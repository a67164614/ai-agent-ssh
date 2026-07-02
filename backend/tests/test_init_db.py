from sqlalchemy import create_engine, inspect, text

from app.db.init_db import upgrade_sqlite_schema
from app.db.models import Base


def test_upgrades_existing_sqlite_schema_without_dropping_data(tmp_path) -> None:
    db_path = tmp_path / "old.db"
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username VARCHAR(100),
                    password_hash VARCHAR(255),
                    role VARCHAR(50),
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE servers (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(120),
                    host VARCHAR(255),
                    port INTEGER,
                    username VARCHAR(120),
                    auth_type VARCHAR(30),
                    encrypted_password TEXT,
                    encrypted_private_key TEXT,
                    remark TEXT,
                    status VARCHAR(30),
                    connection_mode VARCHAR(30),
                    last_seen_at DATETIME,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE ai_providers (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(120),
                    provider_type VARCHAR(50),
                    base_url VARCHAR(500),
                    encrypted_api_key TEXT,
                    default_model VARCHAR(200),
                    api_mode VARCHAR(50),
                    enabled BOOLEAN,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        connection.execute(text("INSERT INTO users (id, username, password_hash, role) VALUES (1, 'admin', 'hash', 'admin')"))

    Base.metadata.create_all(bind=engine)
    upgrade_sqlite_schema(engine)

    inspector = inspect(engine)
    server_columns = {column["name"] for column in inspector.get_columns("servers")}
    provider_columns = {column["name"] for column in inspector.get_columns("ai_providers")}

    assert "last_test_message" in server_columns
    assert {"last_test_status", "last_test_message", "last_test_at"}.issubset(provider_columns)
    assert "server_snapshots" in inspector.get_table_names()

    with engine.connect() as connection:
        user_count = connection.execute(text("SELECT COUNT(*) FROM users")).scalar_one()
    assert user_count == 1
