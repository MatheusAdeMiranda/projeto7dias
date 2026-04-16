from __future__ import annotations

import logging
import ssl
from datetime import UTC, datetime

import httpx

from app.db import make_session_factory
from app.models import CheckResultModel, ServiceModel

logger = logging.getLogger(__name__)
_SSL_CONTEXT = ssl.create_default_context()


def run_check(service_id: int) -> None:
    """Executa uma checagem HTTP para o servico e grava o resultado no banco."""
    session_factory = make_session_factory()

    with session_factory() as session:
        service = session.get(ServiceModel, service_id)
        if service is None:
            logger.warning("service %d not found, skipping", service_id)
            return

        if not service.active:
            logger.info("service %d is inactive, skipping", service_id)
            return

        result = _do_http_check(str(service.url), service.timeout_seconds)
        result.service_id = service_id
        session.add(result)
        session.commit()

    logger.info(
        "service=%d name=%s status=%s http=%s time=%sms",
        service_id,
        service.name,
        result.status,
        result.http_status_code,
        result.response_time_ms,
    )


def _do_http_check(url: str, timeout_seconds: int) -> CheckResultModel:
    """Faz o request HTTP e devolve um CheckResultModel (sem service_id preenchido)."""
    start = datetime.now(UTC)

    try:
        response = httpx.get(
            url, timeout=timeout_seconds, follow_redirects=True, verify=_SSL_CONTEXT
        )
        elapsed_ms = int((datetime.now(UTC) - start).total_seconds() * 1000)

        return CheckResultModel(
            status="ok",
            http_status_code=response.status_code,
            response_time_ms=elapsed_ms,
            checked_at=start,
            error_message=None,
        )

    except httpx.TimeoutException:
        return CheckResultModel(
            status="timeout",
            http_status_code=None,
            response_time_ms=None,
            checked_at=start,
            error_message="request timed out",
        )

    except httpx.RequestError as exc:
        return CheckResultModel(
            status="error",
            http_status_code=None,
            response_time_ms=None,
            checked_at=start,
            error_message=str(exc)[:500],
        )
