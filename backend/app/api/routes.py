from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.security import CommandSafetyResult, check_command_safety
from app.schemas.deployment import DeploymentPlan


router = APIRouter(prefix="/api")


class CommandCheckRequest(BaseModel):
    command: str = Field(min_length=1, max_length=4000)


class CommandCheckResponse(BaseModel):
    allowed: bool
    reason: str | None
    requires_confirmation: bool
    warnings: list[str]

    @classmethod
    def from_result(cls, result: CommandSafetyResult) -> "CommandCheckResponse":
        return cls(
            allowed=result.allowed,
            reason=result.reason,
            requires_confirmation=result.requires_confirmation,
            warnings=list(result.warnings),
        )


class PlanValidationResponse(BaseModel):
    valid: bool
    plan: DeploymentPlan


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-agent-ssh"}


@router.post("/commands/check", response_model=CommandCheckResponse)
def check_command(payload: CommandCheckRequest) -> CommandCheckResponse:
    return CommandCheckResponse.from_result(check_command_safety(payload.command))


@router.post("/deployments/validate-plan", response_model=PlanValidationResponse)
def validate_deployment_plan(plan: DeploymentPlan) -> PlanValidationResponse:
    return PlanValidationResponse(valid=True, plan=plan)
