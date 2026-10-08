import logging
import os

from tavily import TavilyClient

from state import ResearchState

logger = logging.getLogger(__name__)

RESULTS_PER_TASK = 2


def web_searcher(state: ResearchState) -> dict:
    idx = state["current_task_idx"]
    current_sub_task = state["sub_tasks"][idx]

    try:
        client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        result = client.search(current_sub_task, max_results=RESULTS_PER_TASK)
    except Exception:
        # One failed search shouldn't kill the whole run
        logger.exception("Search failed for sub-task %r", current_sub_task)
        result = {}

    new_results = [
        {
            "url":     item.get("url"),
            "title":   item.get("title"),
            "content": item.get("content"),
        }
        for item in result.get("results", [])
    ]

    return {
        "search_results":   state.get("search_results", []) + new_results,
        "current_task_idx": idx + 1,       # advance to next sub-task
    }
