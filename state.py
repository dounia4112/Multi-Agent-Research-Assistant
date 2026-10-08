from typing import TypedDict, List


class ResearchState(TypedDict):
    # User input
    query: str

    # Planner output
    sub_tasks: List[str]          # ["Search X", "Find Y", ...]
    current_task_idx: int         # tracks which sub-task is active

    # Searcher output
    search_results: List[dict]    # [{url, title, content}, ...]

    # Synthesizer output
    synthesized_facts: List[str]

    # Writer output
    draft: str
    revision: int                 # counts writer passes, capped by the grader

    # Grader output
    grade: str                    # "" (not graded yet) | "pass" | "needs_revision"
    feedback: str
    score: int

    # Supervisor control
    is_done: bool


def initial_state(query: str) -> ResearchState:
    return {
        "query": query,
        "sub_tasks": [], "current_task_idx": 0,
        "search_results": [],
        "synthesized_facts": [],
        "draft": "", "revision": 0,
        "grade": "", "feedback": "", "score": 0,
        "is_done": False,
    }
