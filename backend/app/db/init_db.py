from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.db.models import Base
from app.db.session import engine
from sqlalchemy import Engine, inspect, text


def init_db() -> None:
    settings = get_settings()
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    upgrade_sqlite_schema(engine)


def upgrade_sqlite_schema(target_engine: Engine) -> None:
    if not target_engine.url.get_backend_name().startswith("sqlite"):
        return

    inspector = inspect(target_engine)
    table_names = set(inspector.get_table_names())
    migrations = {
        "servers": {
            "last_test_message": "ALTER TABLE servers ADD COLUMN last_test_message TEXT",
        },
        "ai_providers": {
            "last_test_status": "ALTER TABLE ai_providers ADD COLUMN last_test_status VARCHAR(30)",
            "last_test_message": "ALTER TABLE ai_providers ADD COLUMN last_test_message TEXT",
            "last_test_at": "ALTER TABLE ai_providers ADD COLUMN last_test_at DATETIME",
        },
    }

    with target_engine.begin() as connection:
        for table_name, column_sql in migrations.items():
            if table_name not in table_names:
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, sql in column_sql.items():
                if column_name not in existing_columns:
                    connection.execute(text(sql))
