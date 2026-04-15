from __future__ import annotations

import os

import redis
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from rq import Queue
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectivity import probe_tcp
from app.db import DEFAULT_DATABASE_URL, get_session
from app.models import CheckResultModel, ServiceModel
from app.schemas import CheckResultRead, ServiceCreate, ServiceRead

DEFAULT_REDIS_URL = "redis://redis:6379/0"
CHECK_QUEUE_NAME = "checks"

app = FastAPI(
    title="uptime-tracker API",
    version="0.3.0",
    description=(
        "API dos Dias 2-5 para praticar Docker Compose, desenho REST, "
        "persistencia e fila assincrona."
    ),
)

_redis_conn: redis.Redis = redis.from_url(
    os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
)


def get_queue() -> Queue:
    return Queue(CHECK_QUEUE_NAME, connection=_redis_conn)


def find_service_or_404(service_id: int, session: Session) -> ServiceModel:
    service = session.get(ServiceModel, service_id)
    if service is not None:
        return service

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Service {service_id} not found",
    )


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "uptime-tracker-api",
        "message": "API de monitoramento de servicos",
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


@app.post(
    "/services/{service_id}/checks",
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_check(
    service_id: int,
    session: Session = Depends(get_session),
    queue: Queue = Depends(get_queue),
) -> dict[str, object]:
    find_service_or_404(service_id, session)
    job = queue.enqueue("app.jobs.run_check", service_id)
    return {"queued": True, "job_id": job.id, "service_id": service_id}


@app.get("/services/{service_id}/checks", response_model=list[CheckResultRead])
def list_checks(
    service_id: int,
    session: Session = Depends(get_session),
) -> list[CheckResultModel]:
    find_service_or_404(service_id, session)
    return list(
        session.scalars(
            select(CheckResultModel)
            .where(CheckResultModel.service_id == service_id)
            .order_by(CheckResultModel.checked_at.desc())
        )
    )


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
