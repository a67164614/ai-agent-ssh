from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.db.models import Base
from app.db.session import engine


def init_db() -> None:
    settings = get_settings()
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
