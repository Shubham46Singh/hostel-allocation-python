
import os
import time

import psycopg
import redis


deadline = time.monotonic() + 90

while time.monotonic() < deadline:
    try:
        with psycopg.connect(
            os.environ["DATABASE_URL"], connect_timeout=3
        ) as conn:
            conn.execute("SELECT 1")

        redis.Redis.from_url(
            os.environ["REDIS_URL"],
            socket_connect_timeout=3,
        ).ping()

        print("PostgreSQL and Redis are ready.")
        break
    except Exception as exc:
        print(f"Waiting for services: {exc}")
        time.sleep(2)
else:
    raise RuntimeError("PostgreSQL or Redis did not become ready.")
