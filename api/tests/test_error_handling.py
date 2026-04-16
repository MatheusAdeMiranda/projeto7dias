from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def permissive_client(client: TestClient) -> TestClient:
    """TestClient sem raise_server_exceptions, necessario para inspecionar respostas 500.

    O Starlette ServerErrorMiddleware sempre re-levanta a excecao original apos chamar
    o handler e enviar a resposta. Com raise_server_exceptions=True (default), o
    TestClient re-levanta essa excecao no teste antes de retornar o response, impedindo
    qualquer inspecao. Com False, a excecao e descartada e o response 500 fica acessivel.

    Preservamos o mesmo app (e portanto os dependency_overrides do banco) via client.app.
    """
    return TestClient(client.app, raise_server_exceptions=False)


def test_unhandled_exception_returns_500_without_traceback(
    permissive_client: TestClient,
) -> None:
    """Garante que erros inesperados retornam 500 sem vazar stack trace."""
    with patch("app.main.find_service_or_404", side_effect=RuntimeError("db exploded")):
        response = permissive_client.get("/services/1")

    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}
    # stack trace nao deve aparecer no body da resposta
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text
