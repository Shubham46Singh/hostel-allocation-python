
import os
from pathlib import Path

import psycopg


with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    for path in sorted(Path("migrations").glob("*.sql")):
        print(f"Applying {path}")
        conn.execute(path.read_text(encoding="utf-8"), prepare=False)

print("Migrations and seed data applied.")
