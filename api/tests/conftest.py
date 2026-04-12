from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db import create_db_engine, get_session
from app.main import app


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    project_dir = Path(__file__).resolve().parents[1]
    database_path = tmp_path / "test.db"
    database_url = f"sqlite:///{database_path}"
    engine = create_db_engine(database_url)
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    alembic_config = Config(str(project_dir / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(project_dir / "alembic"))
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")

    def override_get_session():
        with testing_session_local() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    engine.dispose()
