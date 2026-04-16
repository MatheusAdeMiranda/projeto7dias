"""Helpers de conectividade TCP usados pelo endpoint /health."""

from __future__ import annotations

import socket
from urllib.parse import urlparse

DEFAULT_PORTS: dict[str, int] = {
    "postgresql": 5432,
    "postgresql+psycopg": 5432,
    "redis": 6379,
}


def resolve_host_port(connection_url: str) -> tuple[str, int]:
    """Extrai (host, port) de uma URL de conexao, caindo em defaults por scheme."""
    parsed = urlparse(connection_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or DEFAULT_PORTS.get(parsed.scheme, 0)
    return host, port


def probe_tcp(connection_url: str, timeout: float = 1.0) -> dict[str, object]:
    """Testa se uma URL TCP esta acessivel. Sempre retorna um dict, nunca lanca."""
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
