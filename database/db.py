import json
import logging
import os
from contextlib import closing, contextmanager
from datetime import datetime

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
      created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
"""

# Tables created by older versions stored a naive TIMESTAMP, which silently depends on the
# DB server's timezone. Existing values are read in the session timezone they were written in.
MIGRATE_CREATED_AT_SQL = """
    DO $$
    BEGIN
      IF (SELECT data_type FROM information_schema.columns
          WHERE table_name = 'research_runs' AND column_name = 'created_at') = 'timestamp without time zone'
      THEN
        ALTER TABLE research_runs ALTER COLUMN created_at TYPE TIMESTAMPTZ;
        UPDATE research_runs SET created_at = NOW() WHERE created_at IS NULL;
        ALTER TABLE research_runs ALTER COLUMN created_at SET NOT NULL;
      END IF;
    END $$;
"""


def is_enabled() -> bool:
    """History is optional — the app works without a database."""
    return bool(os.environ.get("DATABASE_URL"))


@contextmanager
def transaction():
    """Yield a cursor; commit on success, roll back on error, always close the connection."""
    with closing(psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=5)) as conn:
        with conn:                      # commits / rolls back, but does not close
            with conn.cursor() as cur:
                yield cur


def init_db():
    """Create (or upgrade) the table. Safe to run on every startup."""
    with transaction() as cur:
        cur.execute(CREATE_TABLE_SQL)
        cur.execute(MIGRATE_CREATED_AT_SQL)


def save_run(query, report, facts, grade, revision, created_at: datetime) -> int | None:
    """Store a finished run and return its id.

    Never raises: a DB outage must not lose the user's report.
    """
    if not is_enabled():
        return None
    try:
        with transaction() as cur:
            cur.execute("""
                INSERT INTO research_runs (query, report, facts, grade, revision, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (query, report, json.dumps(facts), grade, revision, created_at))
            return cur.fetchone()[0]
    except Exception:
        logger.exception("Could not save research run")
        return None


def get_history(limit: int = 20) -> list[dict]:
    if not is_enabled():
        return []
    with transaction() as cur:
        cur.execute(
            "SELECT id, query, grade, revision, created_at FROM research_runs "
            "ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        return [
            {"id": r[0], "query": r[1], "grade": r[2], "revision": r[3], "created_at": r[4].isoformat()}
            for r in cur.fetchall()
        ]


def get_run(run_id: int) -> dict | None:
    if not is_enabled():
        return None
    with transaction() as cur:
        cur.execute(
            "SELECT id, query, report, facts, grade, revision, created_at "
            "FROM research_runs WHERE id = %s",
            (run_id,),
        )
        r = cur.fetchone()
    if r is None:
        return None
    return {"id": r[0], "query": r[1], "draft": r[2], "facts": r[3], "grade": r[4],
            "revision": r[5], "created_at": r[6].isoformat()}
