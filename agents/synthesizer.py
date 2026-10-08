import logging
from typing import List

from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from agents.models import SMART_MODEL
from state import ResearchState

logger = logging.getLogger(__name__)

SYNTH_PROMPT = """
You are a research analyst. Given these search results about "{query}",
extract a list of unique, factual claims. Remove duplicates.
Mention the source (title or URL) a claim comes from where possible.

Search results:
{results_text}
"""

NO_RESULTS_FACT = "No web search results were found for this query."


class Facts(BaseModel):
    facts: List[str] = Field(description="Unique factual claims taken from the search results")


def synthesizer(state: ResearchState) -> dict:
    results = state["search_results"]
    if not results:
        return {"synthesized_facts": [NO_RESULTS_FACT]}

    results_text = "\n\n".join(
        f"[{r['title']}] ({r['url']})\n{r['content']}" for r in results
    )

    llm = ChatGroq(model=SMART_MODEL, temperature=0)

    try:
        parsed = llm.with_structured_output(Facts, method="json_schema").invoke(SYNTH_PROMPT.format(
            query=state["query"],
            results_text=results_text[:8000],
        ))
        facts = [f.strip() for f in parsed.facts if f.strip()]
    except Exception:
        logger.exception("Synthesizer failed, falling back to raw snippets")
        facts = []

    # Fall back to the raw snippets so the writer always has material
    if not facts:
        facts = [f"{r['content']} ({r['url']})" for r in results if r.get("content")]

    return {"synthesized_facts": facts or [NO_RESULTS_FACT]}
