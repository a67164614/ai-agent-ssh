from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditLog


def test_initializes_first_admin(client: TestClient) -> None:
    response = client.post(
        "/api/auth/init",
        json={"username": "admin", "password": "strong-password"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["username"] == "admin"
    assert body["access_token"]
    assert "password" not in body["user"]


def test_reports_admin_initialization_status(client: TestClient) -> None:
    before_response = client.get("/api/auth/status")
    client.post("/api/auth/init", json={"username": "admin", "password": "strong-password"})
    after_response = client.get("/api/auth/status")

    assert before_response.status_code == 200
    assert before_response.json() == {"initialized": False}
    assert after_response.status_code == 200
    assert after_response.json() == {"initialized": True}


def test_rejects_second_admin_initialization(client: TestClient) -> None:
    client.post("/api/auth/init", json={"username": "admin", "password": "strong-password"})

    response = client.post(
        "/api/auth/init",
        json={"username": "other", "password": "strong-password"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "管理员已经初始化。"


def test_logs_in_and_reads_current_user(client: TestClient) -> None:
    client.post("/api/auth/init", json={"username": "admin", "password": "strong-password"})

    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "strong-password"},
    )
    token = login_response.json()["access_token"]
    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert login_response.status_code == 200
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "admin"


def test_writes_audit_logs_for_admin_init_and_login(client: TestClient, db_session: Session) -> None:
    client.post("/api/auth/init", json={"username": "admin", "password": "strong-password"})
    client.post("/api/auth/login", json={"username": "admin", "password": "strong-password"})

    actions = [log.action for log in db_session.scalars(select(AuditLog).order_by(AuditLog.id)).all()]

    assert actions == ["auth.init", "auth.login"]


def test_rejects_invalid_login(client: TestClient) -> None:
    client.post("/api/auth/init", json={"username": "admin", "password": "strong-password"})

    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "账号或密码错误。"


def test_requires_auth_for_current_user(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "请先登录。"
