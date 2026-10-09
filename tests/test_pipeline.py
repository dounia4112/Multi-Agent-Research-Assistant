"""Offline tests: the LLM and search clients are replaced with fakes, so no API keys are needed."""
import json
from types import SimpleNamespace

import pytest

import agents.grader as grader_mod
import agents.planner as planner_mod
import agents.synthesizer as synth_mod
import agents.web_searcher as search_mod
import agents.writer as writer_mod
from graph import build_graph, run_pipeline, supervisor_router
from state import initial_state


class FakeLLM:
    """Stands in for ChatGroq. `structured` maps a schema class name to a result (or an Exception)."""

    def __init__(self, structured=None, text="## Executive Summary\nok"):
        self.structured = structured or {}
        self.text = text

    def __call__(self, *args, **kwargs):   # used as the ChatGroq constructor
        return self

    def with_structured_output(self, schema, **kwargs):
        result = self.structured[schema.__name__]
        if callable(result) and not isinstance(result, Exception):
            return SimpleNamespace(invoke=lambda prompt: result())

        def invoke(prompt):
            if isinstance(result, Exception):
                raise result
            return result
        return SimpleNamespace(invoke=invoke)

    def invoke(self, prompt):
        return SimpleNamespace(content=self.text)


class FakeTavily:
    def __init__(self, api_key=None):
        pass

    def search(self, query, max_results=2):
        return {"results": [{"url": f"https://example.com/{query}", "title": query, "content": f"About {query}"}]}


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test")
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setattr(search_mod, "TavilyClient", FakeTavily)

    def install(grades):
        grades = iter(grades)
        monkeypatch.setattr(planner_mod, "ChatGroq", FakeLLM({"Plan": planner_mod.Plan(sub_tasks=["a", "b", "c"])}))
        monkeypatch.setattr(synth_mod, "ChatGroq", FakeLLM({"Facts": synth_mod.Facts(facts=["fact 1", "fact 2"])}))
        monkeypatch.setattr(writer_mod, "ChatGroq", FakeLLM())
        monkeypatch.setattr(grader_mod, "ChatGroq", FakeLLM({"Grade": lambda: next(grades)}))
    return install


# ── Supervisor routing ────────────────────────────────────────────────

def state_with(**overrides):
    return {**initial_state("q"), **overrides}


@pytest.mark.parametrize("overrides, expected", [
    ({}, "planner"),
    ({"sub_tasks": ["a", "b"], "current_task_idx": 1}, "web_searcher"),
    ({"sub_tasks": ["a"], "current_task_idx": 1}, "synthesizer"),
    ({"sub_tasks": ["a"], "current_task_idx": 1, "synthesized_facts": ["f"]}, "writer"),
    ({"sub_tasks": ["a"], "current_task_idx": 1, "synthesized_facts": ["f"], "draft": "d"}, "grader"),
    ({"sub_tasks": ["a"], "current_task_idx": 1, "synthesized_facts": ["f"], "draft": "d",
      "grade": "needs_revision"}, "writer"),
    ({"is_done": True}, "END"),
])
def test_supervisor_router(overrides, expected):
    assert supervisor_router(state_with(**overrides)) == expected


# ── Full graph ────────────────────────────────────────────────────────

def test_pipeline_passes_first_time(offline):
    offline([grader_mod.Grade(grade="pass", score=9)])
    events = list(run_pipeline(build_graph(), "q"))
    agents = [e["agent"] for e, _ in events]
    final = events[-1][1]

    assert agents == ["planner", "web_searcher", "web_searcher", "web_searcher",
                      "synthesizer", "writer", "grader"]
    assert final["grade"] == "pass" and final["revision"] == 1
    assert len(final["search_results"]) == 3
    assert events[-1][0]["next"] == "END"


def test_pipeline_revises_after_rejection(offline):
    offline([grader_mod.Grade(grade="needs_revision", feedback="add analysis", score=4),
             grader_mod.Grade(grade="pass", score=8)])
    events = list(run_pipeline(build_graph(), "q"))
    agents = [e["agent"] for e, _ in events]

    assert agents[-4:] == ["writer", "grader", "writer", "grader"]
    assert events[-1][1]["revision"] == 2


def test_revisions_are_capped(offline):
    offline([grader_mod.Grade(grade="needs_revision", feedback="x", score=3)] * 5)
    final = list(run_pipeline(build_graph(), "q"))[-1][1]

    assert final["revision"] == grader_mod.MAX_REVISIONS
    assert final["grade"] == "pass"


# ── Agent fallbacks ───────────────────────────────────────────────────

def test_planner_falls_back_to_query(monkeypatch):
    monkeypatch.setattr(planner_mod, "ChatGroq", FakeLLM({"Plan": ValueError("bad json")}))
    assert planner_mod.planner(initial_state("my question"))["sub_tasks"] == ["my question"]


def test_synthesizer_falls_back_to_snippets(monkeypatch):
    monkeypatch.setattr(synth_mod, "ChatGroq", FakeLLM({"Facts": ValueError("bad json")}))
    state = state_with(search_results=[{"url": "u", "title": "t", "content": "c"}])
    assert synth_mod.synthesizer(state)["synthesized_facts"] == ["c (u)"]


def test_synthesizer_without_results():
    assert synth_mod.synthesizer(initial_state("q"))["synthesized_facts"] == [synth_mod.NO_RESULTS_FACT]


# ── API ───────────────────────────────────────────────────────────────

def test_stream_endpoint_sends_report_in_done_event(offline, monkeypatch):
    from fastapi.testclient import TestClient
    import main

    main._runs_by_client.clear()
    offline([grader_mod.Grade(grade="pass", score=9)])

    with TestClient(main.app) as client:
        r = client.post("/research/stream", json={"query": "test query"})
        events = [json.loads(line[6:]) for line in r.text.splitlines() if line.startswith("data: ")]

        assert events[-1]["agent"] == "done"
        assert events[-1]["payload"]["draft"].startswith("## Executive Summary")
        assert events[-1]["payload"]["created_at"]          # report is dated even without a DB
        assert events[-1]["payload"]["saved"] is False
        assert client.post("/research/stream", json={"query": "  "}).status_code == 422


def test_rate_limit(offline, monkeypatch):
    from fastapi.testclient import TestClient
    import main

    monkeypatch.setattr(main, "RATE_LIMIT_RUNS", 1)
    main._runs_by_client.clear()
    offline([grader_mod.Grade(grade="pass", score=9)] * 2)

    with TestClient(main.app) as client:
        assert client.post("/research", json={"query": "first"}).status_code == 200
        assert client.post("/research", json={"query": "second"}).status_code == 429


def test_report_is_saved_with_its_date(offline, monkeypatch):
    from datetime import datetime
    from fastapi.testclient import TestClient
    import main

    saved = {}

    def fake_save_run(**kwargs):
        saved.update(kwargs)
        return 42

    monkeypatch.setattr(main.db, "save_run", fake_save_run)
    main._runs_by_client.clear()
    offline([grader_mod.Grade(grade="pass", score=9)])

    with TestClient(main.app) as client:
        body = client.post("/research", json={"query": "dated query"}).json()

    assert body["saved"] is True and body["id"] == 42
    assert saved["query"] == "dated query"
    assert isinstance(saved["created_at"], datetime) and saved["created_at"].tzinfo is not None
    assert body["created_at"] == saved["created_at"].isoformat()
