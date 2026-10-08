import logging
from typing import Iterator

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()   # before importing the agents, which read their model names from the env

from state import ResearchState, initial_state
from agents.planner import planner
from agents.web_searcher import web_searcher
from agents.synthesizer import synthesizer
from agents.writer import writer
from agents.grader import grader

AGENTS = {
    "planner":      planner,
    "web_searcher": web_searcher,
    "synthesizer":  synthesizer,
    "writer":       writer,
    "grader":       grader,
}


def supervisor_router(state: ResearchState) -> str:
    """Decide which agent acts next, based only on the shared state."""
    if state.get("is_done"):
        return "END"
    if not state.get("sub_tasks"):
        return "planner"
    if state.get("current_task_idx", 0) < len(state["sub_tasks"]):
        return "web_searcher"
    if not state.get("synthesized_facts"):
        return "synthesizer"
    if not state.get("draft") or state.get("grade") == "needs_revision":
        return "writer"          # no draft yet, or the grader rejected it
    if state.get("grade") == "":
        return "grader"          # fresh draft waiting for review
    return "END"


def build_graph():
    graph = StateGraph(ResearchState)

    for name, fn in AGENTS.items():
        graph.add_node(name, fn)

    graph.set_entry_point("planner")

    # Every agent hands control back to the supervisor, which can route anywhere
    routes = {name: name for name in AGENTS} | {"END": END}
    for name in AGENTS:
        graph.add_conditional_edges(name, supervisor_router, routes)

    return graph.compile()


def describe_update(agent: str, state: ResearchState) -> dict:
    """Turn one agent step into a UI-friendly progress event."""
    if agent == "planner":
        message = f"Created {len(state['sub_tasks'])} sub-tasks"
        payload = state["sub_tasks"]
    elif agent == "web_searcher":
        message = (f"Searched {state['current_task_idx']}/{len(state['sub_tasks'])} sub-tasks · "
                   f"{len(state['search_results'])} results")
        payload = []
    elif agent == "synthesizer":
        message = f"Extracted {len(state['synthesized_facts'])} facts"
        payload = state["synthesized_facts"]
    elif agent == "writer":
        message = f"Draft revision {state['revision']} written"
        payload = []
    elif agent == "grader":
        message = f"Grade: {state['grade']} ({state['score']}/10)"
        payload = state["feedback"]
    else:
        message, payload = "", []

    return {"agent": agent, "message": message, "payload": payload,
            "next": supervisor_router(state)}


def run_pipeline(graph, query: str) -> Iterator[tuple[dict, ResearchState]]:
    """Run the graph once, yielding (progress event, accumulated state) per agent step.

    The last yielded state is the final result, so callers never need to run
    the graph a second time to get the report.
    """
    state = initial_state(query)
    for chunk in graph.stream(state):
        for agent, update in chunk.items():
            state = {**state, **update}
            yield describe_update(agent, state), state


def result_summary(state: ResearchState) -> dict:
    return {
        "query":    state["query"],
        "draft":    state["draft"],
        "facts":    state["synthesized_facts"],
        "revision": state["revision"],
        "grade":    state["grade"],
        "score":    state["score"],
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    graph = build_graph()

    print("🚀 Running multi-agent research graph...\n")
    final = None
    for event, final in run_pipeline(graph, "What is the impact of LLMs on software engineering jobs in 2025?"):
        print(f"[{event['agent']}] {event['message']}")

    print("\n✅ Done!")
    print(f"Revisions: {final['revision']}")
    print(f"Facts found: {len(final['synthesized_facts'])}")
    print("\n--- FINAL REPORT ---")
    print(final["draft"])
