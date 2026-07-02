from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import AppPackage, CommandLog, DeploymentTask


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/auth/init", json={"username": "admin", "password": "strong-password"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_server(client: TestClient, headers: dict[str, str]) -> dict[str, object]:
    return client.post(
        "/api/servers",
        headers=headers,
        json={"name": "prod", "host": "10.0.0.8", "username": "root", "password": "secret"},
    ).json()


def test_executes_safe_command_and_records_log(client: TestClient, db_session: Session, monkeypatch) -> None:
    headers = auth_headers(client)
    server = create_server(client, headers)

    def fake_run_server_command(**kwargs):
        assert kwargs["command"] == "uname -a"
        return 0, "Linux demo", ""

    monkeypatch.setattr("app.api.routes.run_server_command", fake_run_server_command)

    response = client.post(
        f"/api/servers/{server['id']}/commands",
        headers=headers,
        json={"command": "uname -a", "working_directory": "/tmp"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["stdout"] == "Linux demo"
    assert db_session.query(CommandLog).count() == 1

    log_response = client.get(f"/api/servers/{server['id']}/command-logs", headers=headers)
    assert log_response.status_code == 200
    assert log_response.json()[0]["command"] == "uname -a"


def test_blocks_dangerous_command_execution(client: TestClient) -> None:
    headers = auth_headers(client)
    server = create_server(client, headers)

    response = client.post(
        f"/api/servers/{server['id']}/commands",
        headers=headers,
        json={"command": "rm -rf /", "working_directory": "/"},
    )

    assert response.status_code == 400
    assert "已拦截危险命令" in response.json()["detail"]


def test_creates_and_executes_deployment_task(client: TestClient, db_session: Session, monkeypatch) -> None:
    headers = auth_headers(client)
    server = create_server(client, headers)

    calls: list[str] = []

    def fake_run_server_command(**kwargs):
        calls.append(kwargs["command"])
        return 0, f"done {kwargs['command']}", ""

    monkeypatch.setattr("app.api.routes.run_server_command", fake_run_server_command)

    plan = {
        "summary": "部署测试服务",
        "risk_level": "low",
        "requires_sudo": False,
        "steps": [
            {"name": "查看目录", "command": "pwd", "working_directory": "/tmp"},
            {"name": "查看系统", "command": "uname -a", "working_directory": "/tmp"},
        ],
    }

    created = client.post("/api/deployments/plan", headers=headers, json={"server_id": server["id"], "plan": plan})
    assert created.status_code == 200
    executed = client.post(f"/api/deployments/{created.json()['id']}/execute", headers=headers)

    assert executed.status_code == 200
    assert executed.json()["status"] == "success"
    assert calls == ["pwd", "uname -a"]
    assert db_session.query(DeploymentTask).count() == 1
    assert db_session.query(CommandLog).count() == 2


def test_uploads_package_and_analyzes_project(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    headers = auth_headers(client)
    server = create_server(client, headers)
    monkeypatch.setattr(
        "app.api.routes.get_settings",
        lambda: SimpleNamespace(data_dir=tmp_path, credential_secret="change-me"),
    )

    package_bytes = io.BytesIO()
    with zipfile.ZipFile(package_bytes, "w") as archive:
        archive.writestr("package.json", '{"scripts":{"start":"node server.js"}}')
        archive.writestr("README.md", "demo")
    package_bytes.seek(0)

    upload_response = client.post(
        "/api/packages/upload",
        headers=headers,
        files={"file": ("demo.zip", package_bytes.getvalue(), "application/zip")},
    )
    assert upload_response.status_code == 200
    package_id = upload_response.json()["id"]

    analyze_response = client.post(
        f"/api/servers/{server['id']}/analyze-upload",
        headers=headers,
        data={"package_id": str(package_id), "target_path": "/opt/apps/demo"},
    )

    assert analyze_response.status_code == 200
    body = analyze_response.json()
    assert body["detected_type"] == "node"
    assert body["target_path"] == "/opt/apps/demo"
    assert "package.json" in body["file_tree"]
    assert any(step["command"] == "npm run start" for step in body["plan"]["steps"])


def test_rejects_package_archive_path_traversal(
    client: TestClient,
    tmp_path: Path,
    monkeypatch,
) -> None:
    headers = auth_headers(client)
    server = create_server(client, headers)
    monkeypatch.setattr(
        "app.api.routes.get_settings",
        lambda: SimpleNamespace(data_dir=tmp_path, credential_secret="change-me"),
    )

    package_bytes = io.BytesIO()
    with zipfile.ZipFile(package_bytes, "w") as archive:
        archive.writestr("../evil.txt", "bad")
        archive.writestr("package.json", "{}")
    package_bytes.seek(0)

    upload_response = client.post(
        "/api/packages/upload",
        headers=headers,
        files={"file": ("bad.zip", package_bytes.getvalue(), "application/zip")},
    )

    response = client.post(
        f"/api/servers/{server['id']}/analyze-upload",
        headers=headers,
        data={"package_id": str(upload_response.json()["id"]), "target_path": "/opt/apps/demo"},
    )

    assert response.status_code == 400
    assert "压缩包包含不安全路径" in response.json()["detail"]


def test_deployment_uploads_package_before_running_plan(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    headers = auth_headers(client)
    server = create_server(client, headers)
    package_path = tmp_path / "demo.zip"
    package_path.write_bytes(b"demo")
    package = AppPackage(
        filename="demo.zip",
        storage_path=str(package_path),
        size=package_path.stat().st_size,
        sha256=hashlib.sha256(package_path.read_bytes()).hexdigest(),
    )
    db_session.add(package)
    db_session.commit()
    db_session.refresh(package)

    uploads: list[dict[str, object]] = []
    commands: list[str] = []

    def fake_upload_file_to_server(**kwargs: object) -> str:
        uploads.append(kwargs)
        return "/opt/apps/demo/demo.zip"

    def fake_run_server_command(**kwargs: object) -> tuple[int, str, str]:
        commands.append(str(kwargs["command"]))
        return 0, "ok", ""

    monkeypatch.setattr("app.api.routes.upload_file_to_server", fake_upload_file_to_server)
    monkeypatch.setattr("app.api.routes.run_server_command", fake_run_server_command)

    plan = {
        "summary": "部署上传包",
        "risk_level": "low",
        "requires_sudo": False,
        "steps": [{"name": "查看目录", "command": "pwd", "working_directory": "/opt/apps/demo"}],
    }
    created = client.post(
        "/api/deployments/plan",
        headers=headers,
        json={"server_id": server["id"], "package_id": package.id, "plan": plan},
    )
    executed = client.post(f"/api/deployments/{created.json()['id']}/execute", headers=headers)

    assert executed.status_code == 200
    body = executed.json()
    assert body["status"] == "success"
    assert uploads[0]["remote_directory"] == "/opt/apps/demo"
    assert uploads[0]["remote_filename"] == "demo.zip"
    assert commands == ["pwd"]
    assert len(body["logs"]) == 2
    assert body["logs"][0]["command"] == "上传服务包 demo.zip 到 /opt/apps/demo/demo.zip"
