from fastapi.testclient import TestClient


def test_create_service_returns_201_and_defaults(client: TestClient) -> None:
    response = client.post(
        "/services",
        json={
            "name": "OpenAI",
            "url": "https://openai.com",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "OpenAI",
        "url": "https://openai.com/",
        "expected_status": 200,
        "timeout_seconds": 5,
        "active": True,
    }


def test_list_services_returns_created_service(client: TestClient) -> None:
    client.post(
        "/services",
        json={
            "name": "API principal",
            "url": "https://example.com/api",
            "expected_status": 204,
            "timeout_seconds": 3,
            "active": False,
        },
    )

    response = client.get("/services")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "API principal",
            "url": "https://example.com/api",
            "expected_status": 204,
            "timeout_seconds": 3,
            "active": False,
        }
    ]


def test_get_service_returns_created_service_by_id(client: TestClient) -> None:
    created_response = client.post(
        "/services",
        json={
            "name": "OpenAI status page",
            "url": "https://status.openai.com",
        },
    )

    response = client.get(f"/services/{created_response.json()['id']}")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "OpenAI status page",
        "url": "https://status.openai.com/",
        "expected_status": 200,
        "timeout_seconds": 5,
        "active": True,
    }


def test_get_service_returns_404_when_id_does_not_exist(client: TestClient) -> None:
    response = client.get("/services/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Service 999 not found"}


def test_create_service_returns_422_for_invalid_payload(
    client: TestClient,
) -> None:
    response = client.post(
        "/services",
        json={
            "name": "",
            "url": "not-a-url",
            "expected_status": 99,
            "timeout_seconds": 0,
        },
    )

    assert response.status_code == 422
