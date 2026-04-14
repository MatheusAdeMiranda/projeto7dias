from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import get_queue


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
