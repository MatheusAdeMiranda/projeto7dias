from __future__ import annotations

import os
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import redis
from rq import Worker

DEFAULT_REDIS_URL = "redis://redis:6379/0"
CHECK_QUEUE_NAME = "checks"
HEARTBEAT_FILE = Path("/tmp/worker-heartbeat")
HEARTBEAT_INTERVAL = 10


def write_heartbeat() -> None:
    HEARTBEAT_FILE.write_text(datetime.now(UTC).isoformat(), encoding="utf-8")


def _heartbeat_loop() -> None:
    """Thread daemon que renova o heartbeat enquanto o worker esta vivo."""
    while True:
        write_heartbeat()
        time.sleep(HEARTBEAT_INTERVAL)


def main() -> None:
    redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL)

    print("[worker] booting", flush=True)

    conn = redis.from_url(redis_url)

    heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
    heartbeat_thread.start()
    print("[worker] heartbeat thread started", flush=True)

    worker = Worker([CHECK_QUEUE_NAME], connection=conn)
    print(f"[worker] listening on queue '{CHECK_QUEUE_NAME}'", flush=True)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
