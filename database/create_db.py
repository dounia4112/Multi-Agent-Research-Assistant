import psycopg2, os, json
from dotenv import load_dotenv

sql_query= """
    CREATE TABLE research_runs (
      id          SERIAL PRIMARY KEY,
      query       TEXT NOT NULL,
      report      TEXT,
      facts       JSONB,
      grade       VARCHAR(20),
      revision    INT,
      created_at  TIMESTAMP DEFAULT NOW()
    );
"""

load_dotenv(override=True)

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def init_db():
    """Run once to create the table if it doesn't exist."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_query)
        conn.commit()
    print("✓ Table ready")



if __name__ == "__main__":
    init_db()