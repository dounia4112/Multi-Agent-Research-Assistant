from typing import TypedDict, List, Optional

class ResearchState(TypedDict):
    # User input
    query: str

    # Planner output
    sub_tasks: List[str]          # ["Search X", "Find Y", ...]
    current_task_idx: int         # tracks which sub-task is active

    # Searcher output
    search_results: List[dict]    # [{url, title, snippet}, ...]
    raw_sources: List[str]

    # Synthesizer output
    synthesized_facts: List[str]

    # Writer output
    draft: str
    revision: int                 # counts writer passes, cap at 2

    # Grader output
    grade: str                    # "pass" | "needs_revision"
    feedback: str

    # Supervisor control
    next_agent: str
    is_done: bool