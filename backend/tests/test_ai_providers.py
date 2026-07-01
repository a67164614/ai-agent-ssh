from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.crypto import CredentialCipher
from app.db.models import AiProvider


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/auth/init", json={"username": "admin", "password": "strong-password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_creates_ai_provider_with_masked_key(client: TestClient, db_session: Session) -> None:
    headers = auth_headers(client)

    response = client.post(
        "/api/ai-providers",
        headers=headers,
        json={
            "name": "Relay",
            "base_url": "https://cdn.coderelay.cn/v1",
            "api_key": "sk-1234567890abcdef",
            "default_model": "deepseek-chat",
            "enabled": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Relay"
    assert body["has_api_key"] is True
    assert body["api_key_mask"] == "sk-1********cdef"
    assert "api_key" not in body
    saved = db_session.get(AiProvider, body["id"])
    assert saved is not None
    assert saved.encrypted_api_key != "sk-1234567890abcdef"
    assert CredentialCipher("change-me").decrypt(saved.encrypted_api_key) == "sk-1234567890abcdef"


def test_requires_auth_for_ai_providers(client: TestClient) -> None:
    response = client.get("/api/ai-providers")

    assert response.status_code == 401


def test_lists_updates_and_deletes_ai_provider(client: TestClient) -> None:
    headers = auth_headers(client)
    created = client.post(
        "/api/ai-providers",
        headers=headers,
        json={
            "name": "Relay",
            "base_url": "https://cdn.coderelay.cn/v1",
            "api_key": "sk-initial",
            "default_model": "deepseek-chat",
            "enabled": True,
        },
    ).json()

    update_response = client.put(
        f"/api/ai-providers/{created['id']}",
        headers=headers,
        json={
            "name": "Relay Updated",
            "base_url": "https://relay.example/v1",
            "api_key": "",
            "default_model": "gpt-test",
            "enabled": False,
        },
    )
    list_response = client.get("/api/ai-providers", headers=headers)
    delete_response = client.delete(f"/api/ai-providers/{created['id']}", headers=headers)

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Relay Updated"
    assert update_response.json()["has_api_key"] is True
    assert list_response.status_code == 200
    assert list_response.json()[0]["name"] == "Relay Updated"
    assert delete_response.status_code == 200
    assert client.get("/api/ai-providers", headers=headers).json() == []


def test_rejects_chat_completions_base_url(client: TestClient) -> None:
    headers = auth_headers(client)

    response = client.post(
        "/api/ai-providers",
        headers=headers,
        json={
            "name": "Bad",
            "base_url": "https://relay.example/v1/chat/completions",
            "api_key": "sk-test",
            "default_model": "deepseek-chat",
            "enabled": True,
        },
    )

    assert response.status_code == 422


def test_sets_default_provider(client: TestClient) -> None:
    headers = auth_headers(client)
    first = client.post(
        "/api/ai-providers",
        headers=headers,
        json={"name": "First", "base_url": "https://first.example/v1", "api_key": "sk-1", "enabled": True},
    ).json()
    second = client.post(
        "/api/ai-providers",
        headers=headers,
        json={"name": "Second", "base_url": "https://second.example/v1", "api_key": "sk-2", "enabled": True},
    ).json()

    response = client.post(f"/api/ai-providers/{second['id']}/set-default", headers=headers)
    providers = client.get("/api/ai-providers", headers=headers).json()

    assert response.status_code == 200
    assert {provider["id"]: provider["enabled"] for provider in providers} == {
        first["id"]: False,
        second["id"]: True,
    }


def test_manages_ai_models(client: TestClient) -> None:
    headers = auth_headers(client)
    provider = client.post(
        "/api/ai-providers",
        headers=headers,
        json={"name": "Relay", "base_url": "https://relay.example/v1", "api_key": "sk-test", "enabled": True},
    ).json()

    create_response = client.post(
        f"/api/ai-providers/{provider['id']}/models",
        headers=headers,
        json={"model_id": "deepseek-chat", "display_name": "DeepSeek Chat", "enabled": True},
    )
    update_response = client.put(
        f"/api/ai-providers/{provider['id']}/models/deepseek-chat",
        headers=headers,
        json={"display_name": "DeepSeek", "enabled": False},
    )
    list_response = client.get(f"/api/ai-providers/{provider['id']}/models", headers=headers)
    delete_response = client.delete(
        f"/api/ai-providers/{provider['id']}/models/deepseek-chat",
        headers=headers,
    )

    assert create_response.status_code == 200
    assert update_response.status_code == 200
    assert list_response.json()[0]["display_name"] == "DeepSeek"
    assert list_response.json()[0]["enabled"] is False
    assert delete_response.status_code == 200
    assert client.get(f"/api/ai-providers/{provider['id']}/models", headers=headers).json() == []
