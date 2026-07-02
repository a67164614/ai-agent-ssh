from __future__ import annotations

from collections.abc import Iterable

import httpx


class AiGatewayError(RuntimeError):
    """AI 中转站请求失败时抛出，错误信息可直接展示给管理员。"""


class AiGatewayClient:
    def __init__(self, http_client: httpx.Client | None = None, timeout: float = 20.0) -> None:
        self._client = http_client or httpx.Client(timeout=timeout)

    def test_connection(self, *, base_url: str, api_key: str | None, model: str | None) -> tuple[bool, str]:
        if not model:
            raise AiGatewayError("请先配置默认模型后再测试 AI 中转站。")

        response = self._request(
            "POST",
            _join_base_url(base_url, "chat/completions"),
            api_key=api_key,
            json={
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "temperature": 0,
                "max_tokens": 8,
            },
        )
        payload = _json_response(response)
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise AiGatewayError("AI 中转站返回格式异常：缺少 choices。")
        return True, "AI 中转站连接成功。"

    def fetch_models(self, *, base_url: str, api_key: str | None) -> list[str]:
        response = self._request("GET", _join_base_url(base_url, "models"), api_key=api_key)
        payload = _json_response(response)
        data = payload.get("data")
        if not isinstance(data, list):
            raise AiGatewayError("AI 中转站返回格式异常：缺少模型列表 data。")

        model_ids = [_model_id(item) for item in data]
        return sorted({model_id for model_id in model_ids if model_id})

    def chat_completion(
        self,
        *,
        base_url: str,
        api_key: str | None,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int = 800,
    ) -> str:
        response = self._request(
            "POST",
            _join_base_url(base_url, "chat/completions"),
            api_key=api_key,
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": max_tokens,
            },
        )
        payload = _json_response(response)
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise AiGatewayError("AI 中转站返回格式异常：缺少 choices。")
        first = choices[0]
        if not isinstance(first, dict):
            raise AiGatewayError("AI 中转站返回格式异常：choices 内容不是对象。")
        message = first.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"]
        if isinstance(first.get("text"), str):
            return first["text"]
        raise AiGatewayError("AI 中转站返回格式异常：缺少回复内容。")

    def _request(self, method: str, url: str, *, api_key: str | None, json: dict[str, object] | None = None) -> httpx.Response:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            response = self._client.request(method, url, headers=headers, json=json)
        except httpx.TimeoutException as error:
            raise AiGatewayError("AI 中转站请求超时，请检查 Base URL、网络和中转站状态。") from error
        except httpx.HTTPError as error:
            raise AiGatewayError(f"AI 中转站请求失败：{error}") from error

        if response.status_code >= 400:
            raise AiGatewayError(_format_http_error(response))
        return response


def _join_base_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _json_response(response: httpx.Response) -> dict[str, object]:
    try:
        payload = response.json()
    except ValueError as error:
        raise AiGatewayError("AI 中转站返回格式异常：不是合法 JSON。") from error
    if not isinstance(payload, dict):
        raise AiGatewayError("AI 中转站返回格式异常：根节点不是对象。")
    return payload


def _model_id(item: object) -> str | None:
    if isinstance(item, dict) and isinstance(item.get("id"), str):
        return item["id"]
    if isinstance(item, str):
        return item
    return None


def _format_http_error(response: httpx.Response) -> str:
    message = response.text[:300]
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            message = error["message"]
        elif isinstance(payload.get("message"), str):
            message = payload["message"]
    return f"AI 中转站请求失败：HTTP {response.status_code}，{message}"
