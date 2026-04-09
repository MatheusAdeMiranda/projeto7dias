from __future__ import annotations

import os
import socket
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/uptime"
DEFAULT_REDIS_URL = "redis://redis:6379/0"
DEFAULT_PORTS = {
    "postgresql": 5432,
    "redis": 6379,
}
HEARTBEAT_FILE = Path("/tmp/worker-heartbeat")


def resolve_host_port(connection_url: str) -> tuple[str, int]:
    parsed = urlparse(connection_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or DEFAULT_PORTS.get(parsed.scheme, 0)
    return host, port


def probe_tcp(connection_url: str, timeout: float = 1.0) -> tuple[bool, str]:
    host, port = resolve_host_port(connection_url)

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"{host}:{port} reachable"
    except OSError as exc:
        return False, f"{host}:{port} failed ({exc})"


def write_heartbeat() -> None:
    HEARTBEAT_FILE.write_text(datetime.now(UTC).isoformat(), encoding="utf-8")


def clear_heartbeat() -> None:
    HEARTBEAT_FILE.unlink(missing_ok=True)


def main() -> None:
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
    check_interval = int(os.getenv("WORKER_CHECK_INTERVAL", "10"))

    print("[worker] booting", flush=True)

    while True:
        postgres_ok, postgres_message = probe_tcp(database_url)
        redis_ok, redis_message = probe_tcp(redis_url)
        overall_status = "ok" if postgres_ok and redis_ok else "degraded"

        print(
            f"[worker] status={overall_status} "
            f"postgres='{postgres_message}' redis='{redis_message}'",
            flush=True,
        )
        if overall_status == "ok":
            write_heartbeat()
        else:
            clear_heartbeat()
        time.sleep(check_interval)


if __name__ == "__main__":
    main()
