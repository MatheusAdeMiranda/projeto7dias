from __future__ import annotations

import logging
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

logger = logging.getLogger(__name__)


def write_heartbeat() -> None:
    HEARTBEAT_FILE.write_text(datetime.now(UTC).isoformat(), encoding="utf-8")


def _heartbeat_loop() -> None:
    """Thread daemon que renova o heartbeat enquanto o worker esta vivo."""
    while True:
        write_heartbeat()
        time.sleep(HEARTBEAT_INTERVAL)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL)

    logger.info("worker booting")

    conn = redis.from_url(redis_url)

    heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
    heartbeat_thread.start()
    logger.info("heartbeat thread started")

    worker = Worker([CHECK_QUEUE_NAME], connection=conn)
    logger.info("listening on queue '%s'", CHECK_QUEUE_NAME)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
