import json
import logging
import os

import psycopg2

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS research_runs (
      id          SERIAL PRIMARY KEY,
      query       TEXT NOT NULL,
      report      TEXT,
      facts       JSONB,
      grade       VARCHAR(20),
      revision    INT,
      created_at  TIMESTAMP DEFAULT NOW()
    );
"""


def is_enabled() -> bool:
    """History is optional — the app works without a database."""
    return bool(os.environ.get("DATABASE_URL"))


def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=5)


def init_db():
    """Create the table if it doesn't exist. Safe to run on every startup."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)


def save_run(query, report, facts, grade, revision) -> bool:
    """Store a finished run. Never raises: a DB outage must not lose the user's report."""
    if not is_enabled():
        return False
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO research_runs (query, report, facts, grade, revision)
                    VALUES (%s, %s, %s, %s, %s)
                """, (query, report, json.dumps(facts), grade, revision))
        return True
    except Exception:
        logger.exception("Could not save research run")
        return False


def get_history(limit: int = 20) -> list[dict]:
    if not is_enabled():
        return []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, query, grade, created_at FROM research_runs "
                "ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            return [
                {"id": r[0], "query": r[1], "grade": r[2], "created_at": r[3].isoformat()}
                for r in cur.fetchall()
            ]
