from __future__ import annotations

import httpx
import pytest

from app.services.ai_gateway import AiGatewayClient, AiGatewayError


def test_tests_chat_completion_connection_successfully() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert str(request.url) == "https://relay.example/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer sk-test"
        return httpx.Response(200, json={"choices": [{"message": {"content": "pong"}}]})

    client = AiGatewayClient(http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    ok, message = client.test_connection(
        base_url="https://relay.example/v1",
        api_key="sk-test",
        model="deepseek-chat",
    )

    assert ok is True
    assert message == "AI 中转站连接成功。"
    assert len(requests) == 1


def test_fetches_openai_compatible_models() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://relay.example/v1/models"
        return httpx.Response(
            200,
            json={
                "data": [
                    {"id": "deepseek-chat", "object": "model"},
                    {"id": "gpt-4o-mini", "object": "model"},
                ]
            },
        )

    client = AiGatewayClient(http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    models = client.fetch_models(base_url="https://relay.example/v1", api_key="sk-test")

    assert models == ["deepseek-chat", "gpt-4o-mini"]


def test_reports_ai_gateway_errors_in_chinese() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    client = AiGatewayClient(http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    with pytest.raises(AiGatewayError) as exc_info:
        client.fetch_models(base_url="https://relay.example/v1", api_key="sk-bad")

    assert "AI 中转站请求失败" in str(exc_info.value)
    assert "401" in str(exc_info.value)
