from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-agent-ssh"}


def test_command_check_blocks_dangerous_command() -> None:
    response = client.post("/api/commands/check", json={"command": "rm -rf /"})

    assert response.status_code == 200
    body = response.json()
    assert body["allowed"] is False
    assert "rm -rf" in body["reason"]


def test_validate_plan_returns_normalized_plan() -> None:
    response = client.post(
        "/api/deployments/validate-plan",
        json={
            "summary": "Deploy service",
            "risk_level": "medium",
            "requires_sudo": False,
            "steps": [
                {
                    "name": "Build",
                    "command": "npm run build",
                    "working_directory": "/opt/apps/demo",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["plan"]["steps"][0]["name"] == "Build"


def test_validate_plan_rejects_dangerous_step() -> None:
    response = client.post(
        "/api/deployments/validate-plan",
        json={
            "summary": "Bad plan",
            "risk_level": "high",
            "requires_sudo": True,
            "steps": [
                {
                    "name": "Delete",
                    "command": "rm -rf /",
                    "working_directory": "/",
                }
            ],
        },
    )

    assert response.status_code == 422
