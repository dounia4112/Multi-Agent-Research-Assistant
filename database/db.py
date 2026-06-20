import psycopg2, os, json
from dotenv import load_dotenv


load_dotenv(override=True)

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])



def save_run(query, report, facts, grade, revision):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO research_runs (query, report, facts, grade, revision)
                VALUES (%s, %s, %s, %s, %s)
            """, (query, report, json.dumps(facts), grade, revision))

def get_history():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, query, grade, created_at FROM research_runs ORDER BY created_at DESC LIMIT 20")
            return cur.fetchall()
