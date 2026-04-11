from __future__ import annotations

import os
import socket
from threading import Lock
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/uptime"
DEFAULT_REDIS_URL = "redis://redis:6379/0"
DEFAULT_PORTS = {
    "postgresql": 5432,
    "redis": 6379,
}


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: HttpUrl
    expected_status: int = Field(default=200, ge=100, le=599)
    timeout_seconds: int = Field(default=5, ge=1, le=30)
    active: bool = True


class Service(ServiceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int

app = FastAPI(
    title="uptime-tracker API",
    version="0.1.0",
    description=(
        "API minima dos Dias 2 e 3 para praticar Docker Compose, portas, DNS "
        "e desenho REST."
    ),
)

service_store: list[Service] = []
next_service_id = 1
service_store_lock = Lock()


def reset_service_store() -> None:
    global next_service_id

    with service_store_lock:
        service_store.clear()
        next_service_id = 1


def find_service_or_404(service_id: int) -> Service:
    with service_store_lock:
        for service in service_store:
            if service.id == service_id:
                return service.model_copy()

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
        "message": "API inicial dos Dias 2 e 3",
        "docs": "/docs",
        "health": "/health",
        "services": "/services",
    }


@app.post("/services", response_model=Service, status_code=status.HTTP_201_CREATED)
def create_service(payload: ServiceCreate) -> Service:
    global next_service_id

    with service_store_lock:
        service = Service(id=next_service_id, **payload.model_dump())
        service_store.append(service)
        next_service_id += 1

    return service


@app.get("/services", response_model=list[Service])
def list_services() -> list[Service]:
    with service_store_lock:
        return [service.model_copy() for service in service_store]


@app.get("/services/{service_id}", response_model=Service)
def get_service(service_id: int) -> Service:
    return find_service_or_404(service_id)


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
