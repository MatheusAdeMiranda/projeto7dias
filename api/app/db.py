from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/uptime"


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url


def create_db_engine(database_url: str) -> Engine:
    normalized_database_url = normalize_database_url(database_url)
    connect_args = (
        {"check_same_thread": False}
        if normalized_database_url.startswith("sqlite")
        else {}
    )

    return create_engine(
        normalized_database_url,
        future=True,
        pool_pre_ping=not normalized_database_url.startswith("sqlite"),
        connect_args=connect_args,
    )


engine = create_db_engine(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
