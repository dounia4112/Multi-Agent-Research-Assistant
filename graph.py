import os, sys
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from state import ResearchState
from agents.planner import planner
from agents.web_searcher import web_searcher
from agents.synthesizer import synthesizer
from agents.writer import writer
from agents.grader import grader

load_dotenv(override=True)

MAX_REVISIONS = 2

def supervisor_router(state:ResearchState) -> str:
    if state.get("is_done"):
        return "END"
    if not state.get('sub_tasks'):
        return "planner"
    if state.get("current_task_idx", 0) < len(state['sub_tasks']):
        return "web_searcher"
    if not state.get('synthesized_facts'):
        return 'synthesizer'
    if not state.get('draft'):
        return "writer"
    if state.get('grade') != 'pass':
        return "grader"
    return "END"



def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node('planner', planner)
    graph.add_node('web_searcher', web_searcher)
    graph.add_node('synthesizer', synthesizer)
    graph.add_node('writer', writer)
    graph.add_node('grader', grader)

    graph.set_entry_point("planner")

    # After planner → supervisor decides
    graph.add_conditional_edges("planner", supervisor_router, {
        "web_searcher": "web_searcher", 
        "END": END
    })

    # After searcher → keep searching or synthesize
    graph.add_conditional_edges("web_searcher", supervisor_router, {
        "web_searcher": "web_searcher",
        "synthesizer":  "synthesizer",
        "END": END
    })

    # After synthesizer → write
    graph.add_conditional_edges("synthesizer", supervisor_router, {
        "writer": "writer",
        "END": END
    })

    # After writer → grade
    graph.add_conditional_edges("writer", supervisor_router, {
        "grader": "grader",
        "END": END
    })

    # After grader → revise or done
    graph.add_conditional_edges("grader", supervisor_router, {
        "writer": "writer",
        "END":    END
    })

    return graph.compile()



if __name__ == "__main__":
    graph = build_graph()

    initial_state = {
        "query": "What is the impact of LLMs on software engineering jobs in 2025?",
        "sub_tasks": [], "current_task_idx": 0,
        "search_results": [], "raw_sources": [],
        "synthesized_facts": [], "draft": "",
        "revision": 0, "grade": "", "feedback": "",
        "next_agent": "", "is_done": False
    }

    print("🚀 Running multi-agent research graph...\n")
    result = graph.invoke(initial_state)

    print("\n✅ Done!")
    print(f"Revisions: {result['revision']}")
    print(f"Facts found: {len(result['synthesized_facts'])}")
    print("\n--- FINAL REPORT ---")
    print(result["draft"])