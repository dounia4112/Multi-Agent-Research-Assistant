import logging
from typing import List

from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from agents.models import FAST_MODEL
from state import ResearchState

logger = logging.getLogger(__name__)

PLANNER_PROMPT = """
You are a research planner. Given a research question, decompose it into
3-5 specific, searchable sub-tasks. Each sub-task should be a focused
search query on its own.

Research question: {query}
"""

MAX_SUB_TASKS = 5


class Plan(BaseModel):
    sub_tasks: List[str] = Field(description="3-5 focused web search queries")


def planner(state: ResearchState) -> dict:
    llm = ChatGroq(model=FAST_MODEL, temperature=0)

    try:
        plan = llm.with_structured_output(Plan, method="json_schema").invoke(
            PLANNER_PROMPT.format(query=state["query"])
        )
        sub_tasks = [t.strip() for t in plan.sub_tasks if t.strip()][:MAX_SUB_TASKS]
    except Exception:
        logger.exception("Planner failed, falling back to the raw query")
        sub_tasks = []

    # Always hand the searcher at least one task so the pipeline can continue
    if not sub_tasks:
        sub_tasks = [state["query"]]

    return {"sub_tasks": sub_tasks, "current_task_idx": 0}
