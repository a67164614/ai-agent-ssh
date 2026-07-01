import pytest
from pydantic import ValidationError

from app.schemas.deployment import DeploymentPlan


def test_accepts_valid_deployment_plan() -> None:
    plan = DeploymentPlan.model_validate(
        {
            "summary": "Deploy a Node.js service",
            "risk_level": "medium",
            "requires_sudo": False,
            "steps": [
                {
                    "name": "Install dependencies",
                    "command": "npm install",
                    "working_directory": "/opt/apps/demo",
                },
                {
                    "name": "Start service",
                    "command": "npm run start",
                    "working_directory": "/opt/apps/demo",
                },
            ],
        }
    )

    assert plan.steps[0].command == "npm install"
    assert plan.has_blocked_steps is False


def test_rejects_dangerous_deployment_step() -> None:
    with pytest.raises(ValidationError) as exc_info:
        DeploymentPlan.model_validate(
            {
                "summary": "Bad plan",
                "risk_level": "high",
                "requires_sudo": True,
                "steps": [
                    {
                        "name": "Destroy host",
                        "command": "rm -rf /",
                        "working_directory": "/",
                    }
                ],
            }
        )

    assert "dangerous command" in str(exc_info.value)


def test_rejects_empty_steps() -> None:
    with pytest.raises(ValidationError):
        DeploymentPlan.model_validate(
            {
                "summary": "No-op",
                "risk_level": "low",
                "requires_sudo": False,
                "steps": [],
            }
        )
