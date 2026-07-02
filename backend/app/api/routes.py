from __future__ import annotations

import hashlib
import asyncio
import contextlib
import json
import shutil
import tarfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import asyncssh
from fastapi import APIRouter
from fastapi import Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, decode_access_token, get_current_user, hash_password, verify_password
from app.core.config import get_settings
from app.core.crypto import CredentialCipher
from app.core.security import CommandSafetyResult, check_command_safety
from app.db.models import (
    AiModel,
    AiProvider,
    AppPackage,
    AuditLog,
    CommandLog,
    DeploymentTask,
    ProjectAnalysis,
    Server,
    ServerSnapshot,
    User,
)
from app.db.session import SessionLocal, get_db
from app.schemas.ai_provider import (
    AiModelCreate,
    AiModelResponse,
    AiModelUpdate,
    AiProviderCreate,
    AiProviderResponse,
    AiProviderUpdate,
)
from app.schemas.auth import AuthRequest, AuthResponse, UserResponse
from app.schemas.deployment import DeploymentPlan
from app.schemas.server import ServerCreate, ServerResponse, ServerSnapshotResponse, ServerUpdate
from app.services.ai_gateway import AiGatewayClient, AiGatewayError
from app.services.project_analyzer import analyze_project_directory, build_deployment_plan, result_json_parts
from app.services.server_snapshot import SNAPSHOT_COMMAND, parse_linux_snapshot_output
from app.services.ssh_command import SshCommandError, run_server_command, upload_file_to_server
from app.services.ssh_probe import probe_ssh_connection


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


class CommandExecuteRequest(BaseModel):
    command: str = Field(min_length=1, max_length=4000)
    working_directory: str | None = Field(default=None, max_length=500)
    timeout: int = Field(default=30, ge=1, le=600)


class CommandLogResponse(BaseModel):
    id: int
    task_id: int | None
    server_id: int
    command: str
    working_directory: str | None
    stdout: str | None
    stderr: str | None
    exit_code: int | None
    status: str
    started_at: datetime | None
    finished_at: datetime | None


class DeploymentPlanCreate(BaseModel):
    server_id: int
    package_id: int | None = None
    plan: DeploymentPlan


class DeploymentTaskResponse(BaseModel):
    id: int
    server_id: int
    package_id: int | None
    status: str
    summary: str | None
    plan: DeploymentPlan
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime | None
    logs: list[CommandLogResponse] = []


class AppPackageResponse(BaseModel):
    id: int
    filename: str
    size: int
    sha256: str
    uploaded_at: datetime | None


class ProjectAnalysisResponse(BaseModel):
    id: int
    package_id: int | None
    server_id: int | None
    target_path: str | None
    detected_type: str
    summary: str
    dependencies: list[str]
    start_commands: list[str]
    file_tree: list[str]
    plan: DeploymentPlan
    created_at: datetime | None


class AnalyzePathRequest(BaseModel):
    target_path: str = Field(min_length=1, max_length=1000)


class AssistantProposeCommandRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    current_directory: str | None = Field(default=None, max_length=500)
    recent_output: str | None = Field(default=None, max_length=8000)


class AssistantProposeCommandResponse(BaseModel):
    command: str
    explanation: str
    requires_confirmation: bool
    warnings: list[str]
    source: str


class AssistantSummarizeOutputRequest(BaseModel):
    command: str = Field(min_length=1, max_length=4000)
    stdout: str | None = Field(default=None, max_length=20000)
    stderr: str | None = Field(default=None, max_length=20000)
    exit_code: int | None = None


class AssistantSummarizeOutputResponse(BaseModel):
    status: str
    summary: str


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    current_directory: str | None = Field(default=None, max_length=500)


class AssistantChatResponse(BaseModel):
    answer: str
    suggested_command: str | None = None


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-agent-ssh"}


@router.post("/auth/init", response_model=AuthResponse)
def init_admin(payload: AuthRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing_user = db.scalar(select(User).limit(1))
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="管理员已经初始化。")

    user = User(username=payload.username, password_hash=hash_password(payload.password), role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)
    _audit(db, user, "auth.init", "user", user.id)
    return _auth_response(user)


@router.get("/auth/status")
def auth_status(db: Session = Depends(get_db)) -> dict[str, bool]:
    return {"initialized": db.scalar(select(User).limit(1)) is not None}


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: AuthRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误。")
    _audit(db, user, "auth.login", "user", user.id)
    return _auth_response(user)


@router.post("/auth/logout")
def logout() -> dict[str, bool]:
    return {"ok": True}


@router.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _user_response(current_user)


@router.get("/ai-providers", response_model=list[AiProviderResponse])
def list_ai_providers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AiProviderResponse]:
    _ = current_user
    providers = db.scalars(select(AiProvider).order_by(AiProvider.id)).all()
    return [_ai_provider_response(provider) for provider in providers]


@router.post("/ai-providers", response_model=AiProviderResponse)
def create_ai_provider(
    payload: AiProviderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiProviderResponse:
    _ = current_user
    provider = AiProvider(
        name=payload.name,
        base_url=payload.base_url,
        encrypted_api_key=_cipher().encrypt(payload.api_key) if payload.api_key else None,
        default_model=payload.default_model,
        enabled=payload.enabled,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    _audit(db, current_user, "ai_provider.create", "ai_provider", provider.id)
    return _ai_provider_response(provider)


@router.get("/ai-providers/{provider_id}", response_model=AiProviderResponse)
def get_ai_provider(
    provider_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiProviderResponse:
    _ = current_user
    return _ai_provider_response(_get_provider_or_404(provider_id, db))


@router.put("/ai-providers/{provider_id}", response_model=AiProviderResponse)
def update_ai_provider(
    provider_id: int,
    payload: AiProviderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiProviderResponse:
    _ = current_user
    provider = _get_provider_or_404(provider_id, db)
    provider.name = payload.name
    provider.base_url = payload.base_url
    provider.default_model = payload.default_model
    provider.enabled = payload.enabled
    if payload.api_key:
        provider.encrypted_api_key = _cipher().encrypt(payload.api_key)
    db.commit()
    db.refresh(provider)
    _audit(db, current_user, "ai_provider.update", "ai_provider", provider.id)
    return _ai_provider_response(provider)


@router.delete("/ai-providers/{provider_id}")
def delete_ai_provider(
    provider_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    _ = current_user
    provider = _get_provider_or_404(provider_id, db)
    db.delete(provider)
    db.commit()
    _audit(db, current_user, "ai_provider.delete", "ai_provider", provider_id)
    return {"ok": True}


@router.post("/ai-providers/{provider_id}/set-default", response_model=AiProviderResponse)
def set_default_ai_provider(
    provider_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiProviderResponse:
    _ = current_user
    provider = _get_provider_or_404(provider_id, db)
    for item in db.scalars(select(AiProvider)).all():
        item.enabled = item.id == provider.id
    db.commit()
    db.refresh(provider)
    return _ai_provider_response(provider)


@router.post("/ai-providers/{provider_id}/test", response_model=AiProviderResponse)
def test_ai_provider(
    provider_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiProviderResponse:
    _ = current_user
    provider = _get_provider_or_404(provider_id, db)
    api_key = _cipher().decrypt(provider.encrypted_api_key) if provider.encrypted_api_key else None
    try:
        ok, message = AiGatewayClient().test_connection(
            base_url=provider.base_url,
            api_key=api_key,
            model=provider.default_model,
        )
    except AiGatewayError as exc:
        ok, message = False, str(exc)
    provider.last_test_status = "ok" if ok else "failed"
    provider.last_test_message = message
    provider.last_test_at = datetime.now(UTC)
    db.commit()
    db.refresh(provider)
    return _ai_provider_response(provider)


@router.post("/ai-providers/{provider_id}/fetch-models", response_model=list[AiModelResponse])
def fetch_ai_models(
    provider_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AiModelResponse]:
    _ = current_user
    provider = _get_provider_or_404(provider_id, db)
    api_key = _cipher().decrypt(provider.encrypted_api_key) if provider.encrypted_api_key else None
    try:
        model_ids = AiGatewayClient().fetch_models(base_url=provider.base_url, api_key=api_key)
    except AiGatewayError as exc:
        provider.last_test_status = "failed"
        provider.last_test_message = str(exc)
        provider.last_test_at = datetime.now(UTC)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    existing_models = {
        model.model_id: model
        for model in db.scalars(select(AiModel).where(AiModel.provider_id == provider.id)).all()
    }
    for model_id in model_ids:
        existing = existing_models.get(model_id)
        if existing is None:
            db.add(
                AiModel(
                    provider_id=provider.id,
                    model_id=model_id,
                    display_name=model_id,
                    source="fetched",
                    enabled=True,
                )
            )
        else:
            existing.source = "fetched" if existing.source != "manual" else existing.source
            existing.enabled = True
    provider.last_test_status = "ok"
    provider.last_test_message = f"模型列表拉取成功，共 {len(model_ids)} 个模型。"
    provider.last_test_at = datetime.now(UTC)
    if provider.default_model is None and model_ids:
        provider.default_model = model_ids[0]
    db.commit()
    return list_ai_models(provider_id, current_user, db)


@router.get("/ai-providers/{provider_id}/models", response_model=list[AiModelResponse])
def list_ai_models(
    provider_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AiModelResponse]:
    _ = current_user
    _get_provider_or_404(provider_id, db)
    models = db.scalars(select(AiModel).where(AiModel.provider_id == provider_id).order_by(AiModel.id)).all()
    return [_ai_model_response(model) for model in models]


@router.post("/ai-providers/{provider_id}/models", response_model=AiModelResponse)
def create_ai_model(
    provider_id: int,
    payload: AiModelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiModelResponse:
    _ = current_user
    _get_provider_or_404(provider_id, db)
    model = AiModel(
        provider_id=provider_id,
        model_id=payload.model_id,
        display_name=payload.display_name,
        source="manual",
        enabled=payload.enabled,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return _ai_model_response(model)


@router.put("/ai-providers/{provider_id}/models/{model_id}", response_model=AiModelResponse)
def update_ai_model(
    provider_id: int,
    model_id: str,
    payload: AiModelUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiModelResponse:
    _ = current_user
    model = _get_model_or_404(provider_id, model_id, db)
    model.display_name = payload.display_name
    model.enabled = payload.enabled
    db.commit()
    db.refresh(model)
    return _ai_model_response(model)


@router.delete("/ai-providers/{provider_id}/models/{model_id}")
def delete_ai_model(
    provider_id: int,
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    _ = current_user
    model = _get_model_or_404(provider_id, model_id, db)
    db.delete(model)
    db.commit()
    return {"ok": True}


@router.get("/servers", response_model=list[ServerResponse])
def list_servers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ServerResponse]:
    _ = current_user
    servers = db.scalars(select(Server).order_by(Server.id)).all()
    return [_server_response(server) for server in servers]


@router.post("/servers", response_model=ServerResponse)
def create_server(
    payload: ServerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ServerResponse:
    server = Server(
        name=payload.name,
        host=payload.host,
        port=payload.port,
        username=payload.username,
        auth_type=payload.auth_type,
        encrypted_password=_cipher().encrypt(payload.password) if payload.password else None,
        encrypted_private_key=_cipher().encrypt(payload.private_key) if payload.private_key else None,
        remark=payload.remark,
        connection_mode=payload.connection_mode,
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    _audit(db, current_user, "server.create", "server", server.id)
    return _server_response(server)


@router.get("/servers/{server_id}", response_model=ServerResponse)
def get_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ServerResponse:
    _ = current_user
    return _server_response(_get_server_or_404(server_id, db))


@router.put("/servers/{server_id}", response_model=ServerResponse)
def update_server(
    server_id: int,
    payload: ServerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ServerResponse:
    server = _get_server_or_404(server_id, db)
    server.name = payload.name
    server.host = payload.host
    server.port = payload.port
    server.username = payload.username
    server.auth_type = payload.auth_type
    server.remark = payload.remark
    server.connection_mode = payload.connection_mode
    if payload.password:
        server.encrypted_password = _cipher().encrypt(payload.password)
    if payload.private_key:
        server.encrypted_private_key = _cipher().encrypt(payload.private_key)
    db.commit()
    db.refresh(server)
    _audit(db, current_user, "server.update", "server", server.id)
    return _server_response(server)


@router.delete("/servers/{server_id}")
def delete_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    server = _get_server_or_404(server_id, db)
    db.delete(server)
    db.commit()
    _audit(db, current_user, "server.delete", "server", server_id)
    return {"ok": True}


@router.post("/servers/{server_id}/test", response_model=ServerResponse)
def test_server_connection(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ServerResponse:
    server = _get_server_or_404(server_id, db)
    password = _cipher().decrypt(server.encrypted_password) if server.encrypted_password else None
    private_key = _cipher().decrypt(server.encrypted_private_key) if server.encrypted_private_key else None
    ok, message = async_run_ssh_probe(
        host=server.host,
        port=server.port,
        username=server.username,
        password=password,
        private_key=private_key,
    )
    server.status = "online" if ok else "offline"
    server.last_test_message = message
    server.last_seen_at = datetime.now(UTC) if ok else None
    db.commit()
    db.refresh(server)
    _audit(db, current_user, "server.test", "server", server.id)
    return _server_response(server)


@router.post("/servers/{server_id}/snapshot", response_model=ServerSnapshotResponse)
def create_server_snapshot(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ServerSnapshotResponse:
    server = _get_server_or_404(server_id, db)
    password, private_key = _server_credentials(server)
    try:
        exit_code, stdout, stderr = run_server_command(
            host=server.host,
            port=server.port,
            username=server.username,
            password=password,
            private_key=private_key,
            command=SNAPSHOT_COMMAND,
            timeout=30,
        )
        data = (
            parse_linux_snapshot_output(stdout)
            if exit_code == 0
            else parse_linux_snapshot_output("")
        )
        if exit_code != 0:
            data = data.__class__(status="failed", message=f"服务器资源快照采集失败：{stderr or stdout or '命令执行失败。'}")
    except SshCommandError as exc:
        data = parse_linux_snapshot_output("")
        data = data.__class__(status="failed", message=str(exc))
    snapshot = ServerSnapshot(
        server_id=server.id,
        status=data.status,
        message=data.message,
        cpu_usage=data.cpu_usage,
        cpu_cores=data.cpu_cores,
        memory_usage=data.memory_usage,
        memory_total_mb=data.memory_total_mb,
        memory_used_mb=data.memory_used_mb,
        disk_usage=data.disk_usage,
        disk_total_gb=data.disk_total_gb,
        disk_used_gb=data.disk_used_gb,
        os_info=data.os_info,
        kernel=data.kernel,
        ip_addresses=data.ip_addresses,
    )
    server.status = "online" if data.status == "ok" else "offline"
    server.last_test_message = data.message
    server.last_seen_at = datetime.now(UTC) if data.status == "ok" else server.last_seen_at
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    _audit(db, current_user, "server.snapshot", "server", server.id)
    return _server_snapshot_response(snapshot)


@router.post("/commands/check", response_model=CommandCheckResponse)
def check_command(payload: CommandCheckRequest) -> CommandCheckResponse:
    return CommandCheckResponse.from_result(check_command_safety(payload.command))


@router.post("/servers/{server_id}/assistant/propose-command", response_model=AssistantProposeCommandResponse)
def propose_assistant_command(
    server_id: int,
    payload: AssistantProposeCommandRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssistantProposeCommandResponse:
    server = _get_server_or_404(server_id, db)
    snapshot = max(server.snapshots, key=lambda item: item.id, default=None)
    provider = _default_provider(db)
    command, explanation, source = _fallback_command_for_question(payload.question)
    if provider and provider.default_model:
        api_key = _cipher().decrypt(provider.encrypted_api_key) if provider.encrypted_api_key else None
        try:
            content = AiGatewayClient().chat_completion(
                base_url=provider.base_url,
                api_key=api_key,
                model=provider.default_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是受控 Linux 运维助手，只能输出 JSON。字段：command、explanation。"
                            "command 必须是只读查询或低风险命令，不允许删除、格式化、重启、下载脚本执行。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "问题": payload.question,
                                "当前目录": payload.current_directory,
                                "最近输出": payload.recent_output,
                                "服务器": {"名称": server.name, "主机": server.host, "用户": server.username},
                                "资源快照": _snapshot_prompt(snapshot),
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
                max_tokens=500,
            )
            ai_command, ai_explanation = _parse_ai_command(content)
            command = ai_command or command
            explanation = ai_explanation or explanation
            source = "ai"
        except AiGatewayError as exc:
            explanation = f"{explanation}；AI 中转站暂不可用，已使用内置安全建议：{exc}"

    safety = check_command_safety(command)
    if not safety.allowed:
        command, explanation, source = _fallback_command_for_question(payload.question)
        safety = check_command_safety(command)
    _audit(db, current_user, "assistant.propose_command", "server", server.id)
    return AssistantProposeCommandResponse(
        command=command,
        explanation=explanation,
        requires_confirmation=True if safety.allowed else safety.requires_confirmation,
        warnings=list(safety.warnings),
        source=source,
    )


@router.post("/servers/{server_id}/assistant/summarize-output", response_model=AssistantSummarizeOutputResponse)
def summarize_assistant_output(
    server_id: int,
    payload: AssistantSummarizeOutputRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssistantSummarizeOutputResponse:
    server = _get_server_or_404(server_id, db)
    provider = _default_provider(db)
    status_label = "成功" if payload.exit_code == 0 else "失败"
    fallback = _fallback_output_summary(payload)
    summary = fallback
    if provider and provider.default_model:
        api_key = _cipher().decrypt(provider.encrypted_api_key) if provider.encrypted_api_key else None
        try:
            summary = AiGatewayClient().chat_completion(
                base_url=provider.base_url,
                api_key=api_key,
                model=provider.default_model,
                messages=[
                    {"role": "system", "content": "你是 Linux 运维助手，用中文总结命令输出，指出关键结论和异常。"},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "服务器": server.name,
                                "命令": payload.command,
                                "退出码": payload.exit_code,
                                "stdout": payload.stdout,
                                "stderr": payload.stderr,
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
                max_tokens=500,
            )
        except AiGatewayError as exc:
            summary = f"{fallback} AI 总结失败：{exc}"
    _audit(db, current_user, "assistant.summarize_output", "server", server.id)
    return AssistantSummarizeOutputResponse(status=status_label, summary=summary)


@router.post("/servers/{server_id}/assistant/chat", response_model=AssistantChatResponse)
def assistant_chat(
    server_id: int,
    payload: AssistantChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssistantChatResponse:
    _get_server_or_404(server_id, db)
    command, explanation, _source = _fallback_command_for_question(payload.message)
    _audit(db, current_user, "assistant.chat", "server", server_id)
    return AssistantChatResponse(answer=explanation, suggested_command=command)


@router.post("/servers/{server_id}/commands", response_model=CommandLogResponse)
def execute_server_command(
    server_id: int,
    payload: CommandExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommandLogResponse:
    server = _get_server_or_404(server_id, db)
    safety = check_command_safety(payload.command)
    if not safety.allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"已拦截危险命令：{safety.reason}")

    log = _run_and_log_command(db, server, payload.command, payload.working_directory, payload.timeout)
    _audit(db, current_user, "command.execute", "server", server.id)
    return _command_log_response(log)


@router.get("/servers/{server_id}/command-logs", response_model=list[CommandLogResponse])
def list_server_command_logs(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CommandLogResponse]:
    _ = current_user
    _get_server_or_404(server_id, db)
    logs = db.scalars(select(CommandLog).where(CommandLog.server_id == server_id).order_by(CommandLog.id.desc())).all()
    return [_command_log_response(log) for log in logs]


@router.post("/deployments/validate-plan", response_model=PlanValidationResponse)
def validate_deployment_plan(plan: DeploymentPlan) -> PlanValidationResponse:
    return PlanValidationResponse(valid=True, plan=plan)


@router.post("/packages/upload", response_model=AppPackageResponse)
def upload_package(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppPackageResponse:
    settings = get_settings()
    upload_dir = Path(settings.data_dir) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    original_name = Path(file.filename or "upload.bin").name
    temp_path = upload_dir / f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}-{original_name}"
    hasher = hashlib.sha256()
    size = 0
    with temp_path.open("wb") as target:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            hasher.update(chunk)
            target.write(chunk)
    package = AppPackage(
        filename=original_name,
        storage_path=str(temp_path),
        size=size,
        sha256=hasher.hexdigest(),
        uploaded_by=current_user.id,
    )
    db.add(package)
    db.commit()
    db.refresh(package)
    _audit(db, current_user, "package.upload", "package", package.id)
    return _package_response(package)


@router.get("/packages", response_model=list[AppPackageResponse])
def list_packages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AppPackageResponse]:
    _ = current_user
    packages = db.scalars(select(AppPackage).order_by(AppPackage.id.desc())).all()
    return [_package_response(package) for package in packages]


@router.delete("/packages/{package_id}")
def delete_package(
    package_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    package = db.get(AppPackage, package_id)
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到服务包。")
    try:
        Path(package.storage_path).unlink(missing_ok=True)
    except OSError:
        pass
    db.delete(package)
    db.commit()
    _audit(db, current_user, "package.delete", "package", package_id)
    return {"ok": True}


@router.post("/servers/{server_id}/analyze-upload", response_model=ProjectAnalysisResponse)
def analyze_uploaded_package(
    server_id: int,
    package_id: int = Form(...),
    target_path: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectAnalysisResponse:
    server = _get_server_or_404(server_id, db)
    package = db.get(AppPackage, package_id)
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到服务包。")
    extracted_dir = _extract_package(Path(package.storage_path))
    analysis_data = analyze_project_directory(extracted_dir, target_path=target_path)
    plan = build_deployment_plan(analysis_data)
    analysis = _save_project_analysis(db, analysis_data, plan, server.id, package.id, target_path)
    _audit(db, current_user, "project.analyze_upload", "server", server.id)
    return _project_analysis_response(analysis)


@router.post("/servers/{server_id}/analyze-path", response_model=ProjectAnalysisResponse)
def analyze_remote_path(
    server_id: int,
    payload: AnalyzePathRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectAnalysisResponse:
    server = _get_server_or_404(server_id, db)
    password, private_key = _server_credentials(server)
    command = (
        "find . -maxdepth 2 -type f "
        "\\( -name README.md -o -name package.json -o -name pom.xml -o -name build.gradle "
        "-o -name requirements.txt -o -name pyproject.toml -o -name go.mod -o -name Dockerfile "
        "-o -name docker-compose.yml -o -name compose.yml -o -name application.yml -o -name .env.example "
        "-o -name index.html -o -name main.py -o -name app.py \\) -print"
    )
    exit_code, stdout, stderr = run_server_command(
        host=server.host,
        port=server.port,
        username=server.username,
        password=password,
        private_key=private_key,
        command=command,
        working_directory=payload.target_path,
        timeout=30,
    )
    if exit_code != 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"远程目录分析失败：{stderr or stdout}")
    temp_dir = Path(get_settings().data_dir) / "remote-analysis" / f"{server.id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    for relative_name in [line.strip().lstrip("./") for line in stdout.splitlines() if line.strip()]:
        target_file = temp_dir / relative_name
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("", encoding="utf-8")
    analysis_data = analyze_project_directory(temp_dir, target_path=payload.target_path)
    plan = build_deployment_plan(analysis_data)
    analysis = _save_project_analysis(db, analysis_data, plan, server.id, None, payload.target_path)
    _audit(db, current_user, "project.analyze_path", "server", server.id)
    return _project_analysis_response(analysis)


@router.post("/deployments/plan", response_model=DeploymentTaskResponse)
def create_deployment_plan(
    payload: DeploymentPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeploymentTaskResponse:
    _get_server_or_404(payload.server_id, db)
    if payload.package_id is not None and db.get(AppPackage, payload.package_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到服务包。")
    task = DeploymentTask(
        server_id=payload.server_id,
        package_id=payload.package_id,
        status="pending",
        summary=payload.plan.summary,
        plan_json=payload.plan.model_dump_json(),
        created_by=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    _audit(db, current_user, "deployment.plan", "deployment", task.id)
    return _deployment_task_response(task)


@router.post("/deployments/{deployment_id}/execute", response_model=DeploymentTaskResponse)
def execute_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeploymentTaskResponse:
    task = _get_deployment_or_404(deployment_id, db)
    if task.status == "running":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="部署任务正在执行。")
    server = _get_server_or_404(task.server_id, db)
    plan = DeploymentPlan.model_validate_json(task.plan_json)
    task.status = "running"
    task.started_at = datetime.now(UTC)
    task.error_message = None
    db.commit()

    package = db.get(AppPackage, task.package_id) if task.package_id else None
    if package is not None and plan.steps:
        first_workdir = plan.steps[0].working_directory
        password, private_key = _server_credentials(server)
        upload_started_at = datetime.now(UTC)
        try:
            remote_path = upload_file_to_server(
                host=server.host,
                port=server.port,
                username=server.username,
                password=password,
                private_key=private_key,
                local_path=package.storage_path,
                remote_directory=first_workdir,
                remote_filename=package.filename,
            )
            upload_log = CommandLog(
                task_id=task.id,
                server_id=server.id,
                command=f"上传服务包 {package.filename} 到 {remote_path}",
                working_directory=first_workdir,
                stdout=f"服务包已上传到 {remote_path}",
                stderr="",
                exit_code=0,
                status="success",
                started_at=upload_started_at,
                finished_at=datetime.now(UTC),
            )
            db.add(upload_log)
            db.commit()
        except SshCommandError as exc:
            upload_log = CommandLog(
                task_id=task.id,
                server_id=server.id,
                command=f"上传服务包 {package.filename}",
                working_directory=first_workdir,
                stdout="",
                stderr=str(exc),
                exit_code=1,
                status="failed",
                started_at=upload_started_at,
                finished_at=datetime.now(UTC),
            )
            db.add(upload_log)
            task.status = "failed"
            task.error_message = str(exc)
            task.finished_at = datetime.now(UTC)
            db.commit()
            db.refresh(task)
            return _deployment_task_response(task)

    for step in plan.steps:
        log = _run_and_log_command(db, server, step.command, step.working_directory, 600, task_id=task.id)
        if log.exit_code != 0:
            task.status = "failed"
            task.error_message = f"步骤「{step.name}」执行失败：{log.stderr or log.stdout or '命令退出码非 0。'}"
            task.finished_at = datetime.now(UTC)
            db.commit()
            db.refresh(task)
            return _deployment_task_response(task)

    task.status = "success"
    task.finished_at = datetime.now(UTC)
    db.commit()
    db.refresh(task)
    _audit(db, current_user, "deployment.execute", "deployment", task.id)
    return _deployment_task_response(task)


@router.get("/deployments", response_model=list[DeploymentTaskResponse])
def list_deployments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DeploymentTaskResponse]:
    _ = current_user
    tasks = db.scalars(select(DeploymentTask).order_by(DeploymentTask.id.desc())).all()
    return [_deployment_task_response(task) for task in tasks]


@router.get("/deployments/{deployment_id}", response_model=DeploymentTaskResponse)
def get_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeploymentTaskResponse:
    _ = current_user
    return _deployment_task_response(_get_deployment_or_404(deployment_id, db))


@router.post("/deployments/{deployment_id}/cancel", response_model=DeploymentTaskResponse)
def cancel_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeploymentTaskResponse:
    task = _get_deployment_or_404(deployment_id, db)
    if task.status in {"success", "failed", "cancelled"}:
        return _deployment_task_response(task)
    task.status = "cancelled"
    task.finished_at = datetime.now(UTC)
    db.commit()
    db.refresh(task)
    _audit(db, current_user, "deployment.cancel", "deployment", task.id)
    return _deployment_task_response(task)


async def terminal_websocket(websocket: WebSocket, server_id: int) -> None:
    token = websocket.query_params.get("token", "")
    await websocket.accept()
    db = SessionLocal()
    connection: asyncssh.SSHClientConnection | None = None
    process = None
    try:
        user_id = decode_access_token(token)
        if db.get(User, user_id) is None:
            await websocket.send_text("认证失败：用户不存在，请重新登录。")
            await websocket.close(code=1008)
            return
        server = _get_server_or_404(server_id, db)
        password, private_key = _server_credentials(server)
        client_keys = [asyncssh.import_private_key(private_key)] if private_key else None
        connection = await asyncssh.connect(
            server.host,
            port=server.port,
            username=server.username,
            password=password,
            client_keys=client_keys,
            known_hosts=None,
            login_timeout=8,
        )
        process = await connection.create_process(term_type="xterm", encoding="utf-8")
        await websocket.send_text("SSH 终端已连接。")

        async def forward_output() -> None:
            while True:
                data = await process.stdout.read(4096)
                if not data:
                    break
                await websocket.send_text(str(data))

        output_task = asyncio.create_task(forward_output())
        try:
            while True:
                message = await websocket.receive_text()
                process.stdin.write(message if message.endswith("\n") else f"{message}\n")
        except WebSocketDisconnect:
            pass
        finally:
            output_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await output_task
    except HTTPException as exc:
        await websocket.send_text(str(exc.detail))
        await websocket.close(code=1008)
    except asyncssh.PermissionDenied:
        await websocket.send_text("SSH 认证失败，请检查用户名、密码或私钥。")
        await websocket.close(code=1011)
    except asyncssh.KeyImportError:
        await websocket.send_text("SSH 私钥格式不正确。")
        await websocket.close(code=1011)
    except (OSError, asyncssh.Error, asyncio.TimeoutError) as exc:
        await websocket.send_text(f"终端连接失败：{exc}")
        await websocket.close(code=1011)
    finally:
        if process is not None:
            process.stdin.write_eof()
        if connection is not None:
            connection.close()
            await connection.wait_closed()
        db.close()


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(access_token=create_access_token(user.id, user.username), user=_user_response(user))


def _user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, username=user.username, role=user.role)


def _cipher() -> CredentialCipher:
    return CredentialCipher(get_settings().credential_secret)


def _default_provider(db: Session) -> AiProvider | None:
    provider = db.scalar(select(AiProvider).where(AiProvider.enabled == True).order_by(AiProvider.id))  # noqa: E712
    return provider or db.scalar(select(AiProvider).order_by(AiProvider.id))


def _fallback_command_for_question(question: str) -> tuple[str, str, str]:
    normalized = question.lower()
    if any(keyword in question for keyword in ("配置", "资源", "系统", "CPU", "内存", "磁盘")):
        return "uname -a && lscpu && free -h && df -h /", "查询系统、CPU、内存和根分区磁盘信息。", "builtin"
    if any(keyword in question for keyword in ("端口", "监听", "服务")):
        return "ss -tulpen", "查询当前监听端口和对应进程。", "builtin"
    if any(keyword in question for keyword in ("进程", "占用")) or "process" in normalized:
        return "ps aux --sort=-%mem | head -20", "查询内存占用最高的进程。", "builtin"
    if any(keyword in question for keyword in ("日志", "错误")):
        return "journalctl -n 100 --no-pager", "查看最近 100 行 systemd 日志。", "builtin"
    return "pwd && ls -lah", "查看当前目录和文件列表。", "builtin"


def _parse_ai_command(content: str) -> tuple[str | None, str | None]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return None, content[:500]
    if not isinstance(payload, dict):
        return None, content[:500]
    command = payload.get("command")
    explanation = payload.get("explanation")
    return (
        command if isinstance(command, str) and command.strip() else None,
        explanation if isinstance(explanation, str) and explanation.strip() else None,
    )


def _fallback_output_summary(payload: AssistantSummarizeOutputRequest) -> str:
    output = "\n".join(part for part in (payload.stdout, payload.stderr) if part).strip()
    if payload.exit_code == 0:
        return f"命令执行成功。关键输出：{output[:500] or '无输出。'}"
    return f"命令执行失败，退出码 {payload.exit_code}。关键输出：{output[:500] or '无输出。'}"


def _snapshot_prompt(snapshot: ServerSnapshot | None) -> dict[str, object] | None:
    if snapshot is None:
        return None
    return {
        "status": snapshot.status,
        "cpu_usage": snapshot.cpu_usage,
        "memory_usage": snapshot.memory_usage,
        "disk_usage": snapshot.disk_usage,
        "os_info": snapshot.os_info,
        "kernel": snapshot.kernel,
        "message": snapshot.message,
    }


def _get_provider_or_404(provider_id: int, db: Session) -> AiProvider:
    provider = db.get(AiProvider, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到 AI 中转站。")
    return provider


def _get_model_or_404(provider_id: int, model_id: str, db: Session) -> AiModel:
    model = db.scalar(select(AiModel).where(AiModel.provider_id == provider_id, AiModel.model_id == model_id))
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到 AI 模型。")
    return model


def _get_server_or_404(server_id: int, db: Session) -> Server:
    server = db.get(Server, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到服务器。")
    return server


def _get_deployment_or_404(deployment_id: int, db: Session) -> DeploymentTask:
    task = db.get(DeploymentTask, deployment_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到部署任务。")
    return task


def _server_credentials(server: Server) -> tuple[str | None, str | None]:
    password = _cipher().decrypt(server.encrypted_password) if server.encrypted_password else None
    private_key = _cipher().decrypt(server.encrypted_private_key) if server.encrypted_private_key else None
    return password, private_key


def async_run_ssh_probe(
    *,
    host: str,
    port: int,
    username: str,
    password: str | None,
    private_key: str | None,
) -> tuple[bool, str]:
    import asyncio

    return asyncio.run(
        probe_ssh_connection(
            host=host,
            port=port,
            username=username,
            password=password,
            private_key=private_key,
        )
    )


def _ai_provider_response(provider: AiProvider) -> AiProviderResponse:
    api_key = _cipher().decrypt(provider.encrypted_api_key) if provider.encrypted_api_key else None
    return AiProviderResponse(
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type,
        base_url=provider.base_url,
        default_model=provider.default_model,
        api_mode=provider.api_mode,
        enabled=provider.enabled,
        has_api_key=bool(provider.encrypted_api_key),
        api_key_mask=_cipher().mask(api_key),
        last_test_status=provider.last_test_status,
        last_test_message=provider.last_test_message,
        last_test_at=provider.last_test_at,
    )


def _ai_model_response(model: AiModel) -> AiModelResponse:
    return AiModelResponse(
        id=model.id,
        provider_id=model.provider_id,
        model_id=model.model_id,
        display_name=model.display_name,
        source=model.source,
        enabled=model.enabled,
    )


def _server_response(server: Server) -> ServerResponse:
    latest_snapshot = max(server.snapshots, key=lambda snapshot: snapshot.id, default=None)
    return ServerResponse(
        id=server.id,
        name=server.name,
        host=server.host,
        port=server.port,
        username=server.username,
        auth_type=server.auth_type,
        remark=server.remark,
        status=server.status,
        connection_mode=server.connection_mode,
        has_password=bool(server.encrypted_password),
        has_private_key=bool(server.encrypted_private_key),
        last_seen_at=server.last_seen_at,
        last_test_message=server.last_test_message,
        latest_snapshot=_server_snapshot_response(latest_snapshot) if latest_snapshot else None,
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


def _server_snapshot_response(snapshot: ServerSnapshot) -> ServerSnapshotResponse:
    return ServerSnapshotResponse(
        id=snapshot.id,
        server_id=snapshot.server_id,
        status=snapshot.status,
        cpu_usage=snapshot.cpu_usage,
        cpu_cores=snapshot.cpu_cores,
        memory_usage=snapshot.memory_usage,
        memory_total_mb=snapshot.memory_total_mb,
        memory_used_mb=snapshot.memory_used_mb,
        disk_usage=snapshot.disk_usage,
        disk_total_gb=snapshot.disk_total_gb,
        disk_used_gb=snapshot.disk_used_gb,
        os_info=snapshot.os_info,
        kernel=snapshot.kernel,
        ip_addresses=snapshot.ip_addresses,
        message=snapshot.message,
        created_at=snapshot.created_at,
    )


def _command_log_response(log: CommandLog) -> CommandLogResponse:
    return CommandLogResponse(
        id=log.id,
        task_id=log.task_id,
        server_id=log.server_id,
        command=log.command,
        working_directory=log.working_directory,
        stdout=log.stdout,
        stderr=log.stderr,
        exit_code=log.exit_code,
        status=log.status,
        started_at=log.started_at,
        finished_at=log.finished_at,
    )


def _deployment_task_response(task: DeploymentTask) -> DeploymentTaskResponse:
    return DeploymentTaskResponse(
        id=task.id,
        server_id=task.server_id,
        package_id=task.package_id,
        status=task.status,
        summary=task.summary,
        plan=DeploymentPlan.model_validate_json(task.plan_json),
        error_message=task.error_message,
        started_at=task.started_at,
        finished_at=task.finished_at,
        created_at=task.created_at,
        logs=[_command_log_response(log) for log in task.logs],
    )


def _package_response(package: AppPackage) -> AppPackageResponse:
    return AppPackageResponse(
        id=package.id,
        filename=package.filename,
        size=package.size,
        sha256=package.sha256,
        uploaded_at=package.uploaded_at,
    )


def _project_analysis_response(analysis: ProjectAnalysis) -> ProjectAnalysisResponse:
    return ProjectAnalysisResponse(
        id=analysis.id,
        package_id=analysis.package_id,
        server_id=analysis.server_id,
        target_path=analysis.target_path,
        detected_type=analysis.detected_type,
        summary=analysis.summary,
        dependencies=json.loads(analysis.dependencies_json or "[]"),
        start_commands=json.loads(analysis.start_commands_json or "[]"),
        file_tree=json.loads(analysis.file_tree_json or "[]"),
        plan=DeploymentPlan.model_validate_json(analysis.deploy_plan_json or "{}"),
        created_at=analysis.created_at,
    )


def _run_and_log_command(
    db: Session,
    server: Server,
    command: str,
    working_directory: str | None,
    timeout: int,
    *,
    task_id: int | None = None,
) -> CommandLog:
    password, private_key = _server_credentials(server)
    started_at = datetime.now(UTC)
    exit_code, stdout, stderr = run_server_command(
        host=server.host,
        port=server.port,
        username=server.username,
        password=password,
        private_key=private_key,
        command=command,
        working_directory=working_directory,
        timeout=timeout,
    )
    finished_at = datetime.now(UTC)
    log = CommandLog(
        task_id=task_id,
        server_id=server.id,
        command=command,
        working_directory=working_directory,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        status="success" if exit_code == 0 else "failed",
        started_at=started_at,
        finished_at=finished_at,
    )
    db.add(log)
    server.status = "online" if exit_code != 255 else "offline"
    server.last_seen_at = finished_at if exit_code == 0 else server.last_seen_at
    server.last_test_message = "命令执行成功。" if exit_code == 0 else stderr or "命令执行失败。"
    db.commit()
    db.refresh(log)
    return log


def _extract_package(package_path: Path) -> Path:
    extract_root = Path(get_settings().data_dir) / "extracted" / package_path.stem
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(package_path):
        with zipfile.ZipFile(package_path) as archive:
            _safe_extract_zip(archive, extract_root)
    elif tarfile.is_tarfile(package_path):
        with tarfile.open(package_path) as archive:
            _safe_extract_tar(archive, extract_root)
    else:
        shutil.copy2(package_path, extract_root / package_path.name)
    children = list(extract_root.iterdir())
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return extract_root


def _safe_extract_zip(archive: zipfile.ZipFile, target_dir: Path) -> None:
    target_root = target_dir.resolve()
    for member in archive.infolist():
        destination = (target_root / member.filename).resolve()
        if not destination.is_relative_to(target_root):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="压缩包包含不安全路径，已拒绝解压。")
    archive.extractall(target_root)


def _safe_extract_tar(archive: tarfile.TarFile, target_dir: Path) -> None:
    target_root = target_dir.resolve()
    for member in archive.getmembers():
        destination = (target_root / member.name).resolve()
        if not destination.is_relative_to(target_root):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="压缩包包含不安全路径，已拒绝解压。")
    archive.extractall(target_root)


def _save_project_analysis(
    db: Session,
    analysis_data,
    plan: DeploymentPlan,
    server_id: int | None,
    package_id: int | None,
    target_path: str | None,
) -> ProjectAnalysis:
    payload = result_json_parts(analysis_data, plan)
    analysis = ProjectAnalysis(
        package_id=package_id,
        server_id=server_id,
        target_path=target_path,
        detected_type=analysis_data.detected_type,
        summary=analysis_data.summary,
        **payload,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def _audit(db: Session, user: User, action: str, target_type: str, target_id: int | str) -> None:
    db.add(AuditLog(user_id=user.id, action=action, target_type=target_type, target_id=str(target_id)))
    db.commit()
