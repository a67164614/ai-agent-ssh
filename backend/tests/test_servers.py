from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import CredentialCipher
from app.db.models import AuditLog, Server, ServerSnapshot


def _auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/auth/init", json={"username": "admin", "password": "admin12345"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_creates_server_with_encrypted_password(client: TestClient, db_session: Session) -> None:
    headers = _auth_headers(client)

    response = client.post(
        "/api/servers",
        headers=headers,
        json={
            "name": "prod-app-01",
            "host": "10.0.12.21",
            "port": 22,
            "username": "root",
            "auth_type": "password",
            "password": "secret-password",
            "remark": "生产应用服务器",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "prod-app-01"
    assert body["host"] == "10.0.12.21"
    assert body["auth_type"] == "password"
    assert body["has_password"] is True
    assert body["has_private_key"] is False
    assert "password" not in body

    server = db_session.scalar(select(Server).where(Server.name == "prod-app-01"))
    assert server is not None
    assert server.encrypted_password != "secret-password"
    assert CredentialCipher("change-me").decrypt(server.encrypted_password) == "secret-password"


def test_requires_auth_for_servers(client: TestClient) -> None:
    response = client.get("/api/servers")

    assert response.status_code == 401


def test_lists_updates_and_deletes_server(client: TestClient) -> None:
    headers = _auth_headers(client)
    created = client.post(
        "/api/servers",
        headers=headers,
        json={
            "name": "staging-web",
            "host": "10.0.12.33",
            "username": "deploy",
            "auth_type": "private_key",
            "private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\nabc\n-----END OPENSSH PRIVATE KEY-----",
        },
    ).json()

    list_response = client.get("/api/servers", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()[0]["has_private_key"] is True

    update_response = client.put(
        f"/api/servers/{created['id']}",
        headers=headers,
        json={
            "name": "staging-web-1",
            "host": "10.0.12.34",
            "port": 2222,
            "username": "ubuntu",
            "auth_type": "password",
            "password": "new-password",
            "remark": "更新后的测试服务器",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "staging-web-1"
    assert update_response.json()["has_password"] is True

    delete_response = client.delete(f"/api/servers/{created['id']}", headers=headers)
    assert delete_response.status_code == 200
    assert client.get("/api/servers", headers=headers).json() == []


def test_tests_server_connection_without_real_ssh(client: TestClient) -> None:
    headers = _auth_headers(client)
    server = client.post(
        "/api/servers",
        headers=headers,
        json={"name": "legacy-api", "host": "172.16.4.8", "username": "root", "password": "secret"},
    ).json()

    response = client.post(f"/api/servers/{server['id']}/test", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unchecked"
    assert body["last_test_message"] == "SSH connection test will run in the executor implementation slice."


def test_creates_server_snapshot_and_audit_log(client: TestClient, db_session: Session) -> None:
    headers = _auth_headers(client)
    server = client.post(
        "/api/servers",
        headers=headers,
        json={"name": "snapshot-host", "host": "10.0.0.9", "username": "root", "password": "secret"},
    ).json()

    response = client.post(f"/api/servers/{server['id']}/snapshot", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["server_id"] == server["id"]
    assert body["status"] == "skipped"
    assert body["cpu_usage"] is None
    assert "real SSH executor" in body["message"]
    assert db_session.scalar(select(ServerSnapshot).where(ServerSnapshot.server_id == server["id"])) is not None

    audit_actions = [log.action for log in db_session.scalars(select(AuditLog).order_by(AuditLog.id)).all()]
    assert "server.create" in audit_actions
    assert "server.snapshot" in audit_actions
