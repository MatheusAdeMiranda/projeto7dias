from __future__ import annotations

import os
import socket
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import DEFAULT_DATABASE_URL, get_session
from app.models import ServiceModel
from app.schemas import ServiceCreate, ServiceRead

DEFAULT_REDIS_URL = "redis://redis:6379/0"
DEFAULT_PORTS = {
    "postgresql": 5432,
    "postgresql+psycopg": 5432,
    "redis": 6379,
}

app = FastAPI(
    title="uptime-tracker API",
    version="0.2.0",
    description=(
        "API minima dos Dias 2, 3 e 4 para praticar Docker Compose, desenho "
        "REST e persistencia."
    ),
)


def find_service_or_404(service_id: int, session: Session) -> ServiceModel:
    service = session.get(ServiceModel, service_id)
    if service is not None:
        return service

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Service {service_id} not found",
    )


def resolve_host_port(connection_url: str) -> tuple[str, int]:
    parsed = urlparse(connection_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or DEFAULT_PORTS.get(parsed.scheme, 0)
    return host, port


def probe_tcp(connection_url: str, timeout: float = 1.0) -> dict[str, object]:
    host, port = resolve_host_port(connection_url)

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"reachable": True, "host": host, "port": port}
    except OSError as exc:
        return {
            "reachable": False,
            "host": host,
            "port": port,
            "error": str(exc),
        }


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "uptime-tracker-api",
        "message": "API inicial dos Dias 2, 3 e 4",
        "docs": "/docs",
        "health": "/health",
        "services": "/services",
    }


@app.post("/services", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
def create_service(
    payload: ServiceCreate,
    session: Session = Depends(get_session),
) -> ServiceModel:
    service = ServiceModel(**payload.model_dump(mode="json"))
    session.add(service)
    session.commit()
    session.refresh(service)
    return service


@app.get("/services", response_model=list[ServiceRead])
def list_services(session: Session = Depends(get_session)) -> list[ServiceModel]:
    return list(session.scalars(select(ServiceModel).order_by(ServiceModel.id)))


@app.get("/services/{service_id}", response_model=ServiceRead)
def get_service(
    service_id: int,
    session: Session = Depends(get_session),
) -> ServiceModel:
    return find_service_or_404(service_id, session)


@app.get("/health")
def read_health() -> JSONResponse:
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL)

    dependencies = {
        "postgres": probe_tcp(database_url),
        "redis": probe_tcp(redis_url),
    }
    all_dependencies_ready = all(
        dependency["reachable"] for dependency in dependencies.values()
    )

    payload = {
        "status": "ok" if all_dependencies_ready else "degraded",
        "app_env": os.getenv("APP_ENV", "development"),
        "bind": {
            "host": os.getenv("API_HOST", "0.0.0.0"),
            "port": int(os.getenv("API_PORT", "8000")),
        },
        "dependencies": dependencies,
        "network_note": (
            "Dentro do container, postgres e redis sao acessados pelos nomes "
            "de servico do Docker Compose."
        ),
    }

    return JSONResponse(
        status_code=(
            status.HTTP_200_OK
            if all_dependencies_ready
            else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content=payload,
    )
