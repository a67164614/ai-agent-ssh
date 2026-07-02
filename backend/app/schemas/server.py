from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ServerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=22, ge=1, le=65535)
    username: str = Field(min_length=1, max_length=120)
    auth_type: str = Field(default="password", pattern="^(password|private_key)$")
    password: str | None = Field(default=None, max_length=5000)
    private_key: str | None = Field(default=None, max_length=20000)
    remark: str | None = Field(default=None, max_length=2000)
    connection_mode: str = Field(default="ssh", max_length=30)

    @field_validator("host")
    @classmethod
    def host_must_not_include_scheme(cls, value: str) -> str:
        normalized = value.strip()
        if "://" in normalized:
            raise ValueError("服务器主机地址不能包含 URL 协议。")
        return normalized


class ServerUpdate(ServerCreate):
    pass


class ServerResponse(BaseModel):
    id: int
    name: str
    host: str
    port: int
    username: str
    auth_type: str
    remark: str | None
    status: str
    connection_mode: str
    has_password: bool
    has_private_key: bool
    last_seen_at: datetime | None = None
    last_test_message: str | None = None
    latest_snapshot: "ServerSnapshotResponse | None" = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ServerSnapshotResponse(BaseModel):
    id: int
    server_id: int
    status: str
    cpu_usage: float | None
    cpu_cores: int | None = None
    memory_usage: float | None
    memory_total_mb: int | None = None
    memory_used_mb: int | None = None
    disk_usage: float | None
    disk_total_gb: float | None = None
    disk_used_gb: float | None = None
    os_info: str | None
    kernel: str | None = None
    ip_addresses: str | None = None
    message: str | None
    created_at: datetime | None = None
