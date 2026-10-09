import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from database import db
from graph import build_graph, run_pipeline, result_summary
from models.query_class import QueryRequest

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INDEX_HTML = Path(__file__).parent / "index.html"

# Each run costs Groq + Tavily credits, so cap how often one visitor can start one
RATE_LIMIT_RUNS   = int(os.environ.get("RATE_LIMIT_RUNS", "5"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "600"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    if db.is_enabled():
        try:
            db.init_db()
            logger.info("Database ready")
        except Exception:
            # A DATABASE_URL pointing at localhost only works on your own machine
            logger.exception("Database unavailable, reports will not be saved. "
                             "Check that DATABASE_URL points to a reachable, hosted Postgres.")
    else:
        logger.info("DATABASE_URL not set, history disabled")
    yield


app = FastAPI(title="Multi-Agent Research Assistant", lifespan=lifespan)

# Only needed when index.html is hosted on a different domain than the API
allowed_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

graph = build_graph()

_runs_by_client: dict[str, deque] = defaultdict(deque)
_rate_lock = threading.Lock()


def check_rate_limit(request: Request):
    # Render and most hosts sit behind a proxy, so prefer the forwarded client IP
    forwarded = request.headers.get("x-forwarded-for", "")
    client = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    now = time.monotonic()

    with _rate_lock:
        runs = _runs_by_client[client]
        while runs and now - runs[0] > RATE_LIMIT_WINDOW:
            runs.popleft()
        if len(runs) >= RATE_LIMIT_RUNS:
            retry_in = int(RATE_LIMIT_WINDOW - (now - runs[0])) + 1
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit reached. Try again in {retry_in // 60 + 1} min.",
                headers={"Retry-After": str(retry_in)},
            )
        runs.append(now)


def finish(state) -> dict:
    """Stamp the report with its creation date, store it, and build the response."""
    created_at = datetime.now(timezone.utc)
    run_id = db.save_run(
        query=state["query"],
        report=state["draft"],
        facts=state["synthesized_facts"],
        grade=state["grade"],
        revision=state["revision"],
        created_at=created_at,
    )
    return {**result_summary(state), "id": run_id, "created_at": created_at.isoformat(),
            "saved": run_id is not None}


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(INDEX_HTML)


@app.get("/health")
def health():
    status = {"status": "ok", "history_enabled": db.is_enabled(), "database_reachable": False}
    if db.is_enabled():
        try:
            with db.transaction() as cur:
                cur.execute("SELECT 1")
            status["database_reachable"] = True
        except Exception as e:
            status["database_error"] = type(e).__name__
    return status


@app.post("/research")
def research(body: QueryRequest, request: Request):
    """Run the full pipeline and return the final report."""
    check_rate_limit(request)

    final = None
    for _, final in run_pipeline(graph, body.query):
        pass

    return finish(final)


@app.post("/research/stream")
def research_stream(body: QueryRequest, request: Request):
    """Stream agent progress as Server-Sent Events. The last event carries the report."""
    check_rate_limit(request)

    def sse(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    def event_stream():
        final = None
        try:
            for event, final in run_pipeline(graph, body.query):
                yield sse(event)
        except Exception:
            logger.exception("Pipeline failed for query %r", body.query)
            yield sse({"agent": "error", "message": "The research pipeline failed. Please try again.", "payload": []})
            return

        yield sse({"agent": "done", "message": "Report complete", "payload": finish(final)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/history")
def history():
    if not db.is_enabled():
        return []
    try:
        return db.get_history()
    except Exception:
        logger.exception("Could not load history")
        raise HTTPException(status_code=503, detail="History is temporarily unavailable")


@app.get("/history/{run_id}")
def history_item(run_id: int):
    """Reopen a saved report, with its creation date."""
    if not db.is_enabled():
        raise HTTPException(status_code=404, detail="History is disabled")
    try:
        run = db.get_run(run_id)
    except Exception:
        logger.exception("Could not load run %s", run_id)
        raise HTTPException(status_code=503, detail="History is temporarily unavailable")
    if run is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return run
