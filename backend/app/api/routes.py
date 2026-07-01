from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, get_current_user, hash_password, verify_password
from app.core.config import get_settings
from app.core.crypto import CredentialCipher
from app.core.security import CommandSafetyResult, check_command_safety
from app.db.models import AiModel, AiProvider, AuditLog, Server, ServerSnapshot, User
from app.db.session import get_db
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


@router.post("/auth/init", response_model=AuthResponse)
def init_admin(payload: AuthRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing_user = db.scalar(select(User).limit(1))
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="admin already initialized")

    user = User(username=payload.username, password_hash=hash_password(payload.password), role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)
    _audit(db, user, "auth.init", "user", user.id)
    return _auth_response(user)


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: AuthRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid username or password")
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
    provider.last_test_status = "skipped"
    provider.last_test_message = "AI connection test will call the provider in the next implementation slice."
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
    if provider.default_model:
        existing = db.scalar(
            select(AiModel).where(AiModel.provider_id == provider.id, AiModel.model_id == provider.default_model)
        )
        if existing is None:
            db.add(
                AiModel(
                    provider_id=provider.id,
                    model_id=provider.default_model,
                    display_name=provider.default_model,
                    source="manual",
                    enabled=True,
                )
            )
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
    server.status = "unchecked"
    server.last_test_message = "SSH connection test will run in the executor implementation slice."
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
    snapshot = ServerSnapshot(
        server_id=server.id,
        status="skipped",
        message="Server snapshot requires the real SSH executor implementation slice.",
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    _audit(db, current_user, "server.snapshot", "server", server.id)
    return _server_snapshot_response(snapshot)


@router.post("/commands/check", response_model=CommandCheckResponse)
def check_command(payload: CommandCheckRequest) -> CommandCheckResponse:
    return CommandCheckResponse.from_result(check_command_safety(payload.command))


@router.post("/deployments/validate-plan", response_model=PlanValidationResponse)
def validate_deployment_plan(plan: DeploymentPlan) -> PlanValidationResponse:
    return PlanValidationResponse(valid=True, plan=plan)


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(access_token=create_access_token(user.id, user.username), user=_user_response(user))


def _user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, username=user.username, role=user.role)


def _cipher() -> CredentialCipher:
    return CredentialCipher(get_settings().credential_secret)


def _get_provider_or_404(provider_id: int, db: Session) -> AiProvider:
    provider = db.get(AiProvider, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI provider not found")
    return provider


def _get_model_or_404(provider_id: int, model_id: str, db: Session) -> AiModel:
    model = db.scalar(select(AiModel).where(AiModel.provider_id == provider_id, AiModel.model_id == model_id))
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI model not found")
    return model


def _get_server_or_404(server_id: int, db: Session) -> Server:
    server = db.get(Server, server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return server


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
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


def _server_snapshot_response(snapshot: ServerSnapshot) -> ServerSnapshotResponse:
    return ServerSnapshotResponse(
        id=snapshot.id,
        server_id=snapshot.server_id,
        status=snapshot.status,
        cpu_usage=snapshot.cpu_usage,
        memory_usage=snapshot.memory_usage,
        disk_usage=snapshot.disk_usage,
        os_info=snapshot.os_info,
        message=snapshot.message,
        created_at=snapshot.created_at,
    )


def _audit(db: Session, user: User, action: str, target_type: str, target_id: int | str) -> None:
    db.add(AuditLog(user_id=user.id, action=action, target_type=target_type, target_id=str(target_id)))
    db.commit()
