from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/uptime"


def _normalize(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def make_session_factory() -> sessionmaker:
    url = _normalize(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
    engine = create_engine(url, future=True, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
