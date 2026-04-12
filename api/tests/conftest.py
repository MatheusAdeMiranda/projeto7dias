from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db import create_db_engine, get_session
from app.main import app
from app.models import Base


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    database_path = tmp_path / "test.db"
    engine = create_db_engine(f"sqlite:///{database_path}")
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_session():
        with testing_session_local() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
