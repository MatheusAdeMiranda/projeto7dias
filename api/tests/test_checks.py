from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from app.db import get_session
from app.main import get_queue
from app.models import CheckResultModel
from fastapi.testclient import TestClient


@pytest.fixture()
def mock_queue(client: TestClient):
    """Substitui a Queue real por um mock que nao precisa de Redis."""
    fake_queue = MagicMock()
    fake_queue.enqueue.return_value = MagicMock(id="fake-job-id")
    client.app.dependency_overrides[get_queue] = lambda: fake_queue
    yield fake_queue
    client.app.dependency_overrides.pop(get_queue, None)


def test_trigger_check_returns_202(client: TestClient, mock_queue: MagicMock) -> None:
    client.post("/services", json={"name": "Example", "url": "https://example.com"})

    response = client.post("/services/1/checks")

    assert response.status_code == 202
    assert response.json()["queued"] is True
    assert response.json()["service_id"] == 1


def test_trigger_check_calls_enqueue(client: TestClient, mock_queue: MagicMock) -> None:
    client.post("/services", json={"name": "Example", "url": "https://example.com"})

    client.post("/services/1/checks")

    mock_queue.enqueue.assert_called_once_with("app.jobs.run_check", 1)


def test_trigger_check_returns_404_for_unknown_service(
    client: TestClient, mock_queue: MagicMock
) -> None:
    response = client.post("/services/999/checks")

    assert response.status_code == 404
    mock_queue.enqueue.assert_not_called()


def test_list_checks_returns_empty_before_any_check(
    client: TestClient, mock_queue: MagicMock
) -> None:
    client.post("/services", json={"name": "Example", "url": "https://example.com"})

    response = client.get("/services/1/checks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_checks_returns_404_for_unknown_service(client: TestClient) -> None:
    response = client.get("/services/999/checks")

    assert response.status_code == 404


def test_list_checks_returns_results_in_descending_order_filtered_by_service(
    client: TestClient, mock_queue: MagicMock
) -> None:
    client.post("/services", json={"name": "A", "url": "https://a.example.com"})
    client.post("/services", json={"name": "B", "url": "https://b.example.com"})

    now = datetime.now(UTC)
    session_factory = client.app.dependency_overrides[get_session]
    session = next(session_factory())
    try:
        session.add_all(
            [
                CheckResultModel(
                    service_id=1,
                    status="ok",
                    http_status_code=200,
                    response_time_ms=120,
                    checked_at=now - timedelta(minutes=2),
                    error_message=None,
                ),
                CheckResultModel(
                    service_id=1,
                    status="error",
                    http_status_code=None,
                    response_time_ms=None,
                    checked_at=now,
                    error_message="boom",
                ),
                CheckResultModel(
                    service_id=2,
                    status="ok",
                    http_status_code=200,
                    response_time_ms=80,
                    checked_at=now - timedelta(minutes=1),
                    error_message=None,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    response = client.get("/services/1/checks")

    assert response.status_code == 200
    body = response.json()
    assert [row["status"] for row in body] == ["error", "ok"]
    assert all(row["service_id"] == 1 for row in body)
