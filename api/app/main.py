from __future__ import annotations

import os
import socket
from urllib.parse import urlparse

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/uptime"
DEFAULT_REDIS_URL = "redis://redis:6379/0"
DEFAULT_PORTS = {
    "postgresql": 5432,
    "redis": 6379,
}

app = FastAPI(
    title="uptime-tracker API",
    version="0.1.0",
    description="API minima do Dia 2 para praticar Docker Compose, portas e DNS.",
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
        "message": "API inicial do Dia 2",
        "docs": "/docs",
        "health": "/health",
    }


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
