import logging
from typing import Literal

from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from agents.models import SMART_MODEL
from state import ResearchState

logger = logging.getLogger(__name__)

GRADER_PROMPT = """
You are a research quality reviewer. Grade this research report.

Check all of the following:
1. Does it directly answer the query: "{query}"?
2. Does it have an Executive Summary section?
3. Does it have a Key Findings section?
4. Does it have an Analysis section?
5. Is the analysis meaningful (not just repeated bullet points)?

Report to grade:
{draft}
"""

MAX_REVISIONS = 2


class Grade(BaseModel):
    grade: Literal["pass", "needs_revision"]
    feedback: str = Field(default="", description="Specific issues to fix; empty if pass")
    score: int = Field(default=0, ge=0, le=10, description="Overall quality from 1 to 10")


def grader(state: ResearchState) -> dict:
    llm = ChatGroq(model=SMART_MODEL, temperature=0)

    try:
        result = llm.with_structured_output(Grade, method="json_schema").invoke(GRADER_PROMPT.format(
            query=state["query"],
            draft=state["draft"][:5000],
        ))
    except Exception:
        logger.exception("Grader failed, accepting the current draft")
        result = Grade(grade="pass", feedback="", score=0)

    # Stop revising once the writer has had its maximum number of passes
    if result.grade == "needs_revision" and state.get("revision", 0) >= MAX_REVISIONS:
        logger.info("Max revisions reached, accepting the current draft")
        result.grade = "pass"

    logger.info("Grader: %s (score %s/10)", result.grade, result.score)

    return {
        "grade":    result.grade,
        "feedback": result.feedback if result.grade == "needs_revision" else "",
        "score":    result.score,
        "is_done":  result.grade == "pass",
    }
