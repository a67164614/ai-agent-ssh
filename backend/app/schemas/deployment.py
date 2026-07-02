from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.security import check_command_safety


RiskLevel = Literal["low", "medium", "high"]


class DeploymentStep(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    command: str = Field(min_length=1, max_length=4000)
    working_directory: str = Field(min_length=1, max_length=500)

    @field_validator("command")
    @classmethod
    def command_must_be_safe(cls, value: str) -> str:
        safety = check_command_safety(value)
        if not safety.allowed:
            raise ValueError(f"已拦截危险命令：{safety.reason}")
        return value


class DeploymentPlan(BaseModel):
    summary: str = Field(min_length=1, max_length=2000)
    risk_level: RiskLevel
    requires_sudo: bool
    steps: list[DeploymentStep] = Field(min_length=1)

    @property
    def has_blocked_steps(self) -> bool:
        return False
