from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class AiProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_url: str = Field(min_length=1, max_length=500)
    api_key: str | None = Field(default=None, max_length=5000)
    default_model: str | None = Field(default=None, max_length=200)
    enabled: bool = True

    @field_validator("base_url")
    @classmethod
    def base_url_must_not_include_endpoint(cls, value: str) -> str:
        if "/chat/completions" in value:
            raise ValueError("Base URL must end at /v1, not /chat/completions")
        return value.rstrip("/")


class AiProviderUpdate(AiProviderCreate):
    pass


class AiProviderResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    base_url: str
    default_model: str | None
    api_mode: str
    enabled: bool
    has_api_key: bool
    api_key_mask: str
    last_test_status: str | None = None
    last_test_message: str | None = None
    last_test_at: datetime | None = None


class AiModelCreate(BaseModel):
    model_id: str = Field(min_length=1, max_length=200)
    display_name: str | None = Field(default=None, max_length=200)
    enabled: bool = True


class AiModelUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)
    enabled: bool = True


class AiModelResponse(BaseModel):
    id: int
    provider_id: int
    model_id: str
    display_name: str | None
    source: str
    enabled: bool
