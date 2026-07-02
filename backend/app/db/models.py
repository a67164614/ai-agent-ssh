from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="admin")


class Server(TimestampMixin, Base):
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    host: Mapped[str] = mapped_column(String(255), index=True)
    port: Mapped[int] = mapped_column(Integer, default=22)
    username: Mapped[str] = mapped_column(String(120))
    auth_type: Mapped[str] = mapped_column(String(30), default="password")
    encrypted_password: Mapped[str | None] = mapped_column(Text, nullable=True)
    encrypted_private_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="unknown")
    connection_mode: Mapped[str] = mapped_column(String(30), default="ssh")
    last_test_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    snapshots: Mapped[list["ServerSnapshot"]] = relationship(back_populates="server", cascade="all, delete-orphan")


class ServerSnapshot(Base):
    __tablename__ = "server_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(30), default="skipped")
    cpu_usage: Mapped[float | None] = mapped_column(nullable=True)
    cpu_cores: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_usage: Mapped[float | None] = mapped_column(nullable=True)
    memory_total_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_used_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disk_usage: Mapped[float | None] = mapped_column(nullable=True)
    disk_total_gb: Mapped[float | None] = mapped_column(nullable=True)
    disk_used_gb: Mapped[float | None] = mapped_column(nullable=True)
    os_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    kernel: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_addresses: Mapped[str | None] = mapped_column(Text, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    server: Mapped[Server] = relationship(back_populates="snapshots")


class AiProvider(TimestampMixin, Base):
    __tablename__ = "ai_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    provider_type: Mapped[str] = mapped_column(String(50), default="openai-compatible")
    base_url: Mapped[str] = mapped_column(String(500))
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    api_mode: Mapped[str] = mapped_column(String(50), default="chat_completions")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_test_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    last_test_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    models: Mapped[list["AiModel"]] = relationship(back_populates="provider", cascade="all, delete-orphan")


class AiModel(TimestampMixin, Base):
    __tablename__ = "ai_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("ai_providers.id", ondelete="CASCADE"))
    model_id: Mapped[str] = mapped_column(String(200))
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source: Mapped[str] = mapped_column(String(30), default="manual")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    provider: Mapped[AiProvider] = relationship(back_populates="models")


class AppPackage(Base):
    __tablename__ = "app_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(1000))
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    uploaded_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    analyses: Mapped[list["ProjectAnalysis"]] = relationship(back_populates="package", cascade="all, delete-orphan")
    deployments: Mapped[list["DeploymentTask"]] = relationship(back_populates="package")


class ProjectAnalysis(Base):
    __tablename__ = "project_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    package_id: Mapped[int | None] = mapped_column(ForeignKey("app_packages.id", ondelete="SET NULL"), nullable=True)
    server_id: Mapped[int | None] = mapped_column(ForeignKey("servers.id", ondelete="SET NULL"), nullable=True)
    target_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    detected_type: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str] = mapped_column(Text)
    dependencies_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_commands_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    deploy_plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_tree_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    package: Mapped[AppPackage | None] = relationship(back_populates="analyses")


class DeploymentTask(Base):
    __tablename__ = "deployment_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"))
    package_id: Mapped[int | None] = mapped_column(ForeignKey("app_packages.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_json: Mapped[str] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    package: Mapped[AppPackage | None] = relationship(back_populates="deployments")
    logs: Mapped[list["CommandLog"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class CommandLog(Base):
    __tablename__ = "command_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("deployment_tasks.id", ondelete="CASCADE"), nullable=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"))
    command: Mapped[str] = mapped_column(Text)
    working_directory: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task: Mapped[DeploymentTask | None] = relationship(back_populates="logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(120))
    target_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
