import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv(override=True)

from agents.planner import planner
from agents.web_searcher import web_searcher
from agents.synthesizer import synthesizer
from agents.writer import writer
from agents.grader import grader

state = {
    "query": "What is the impact of LLMs on software engineering jobs in 2025?",
    "sub_tasks": [], "current_task_idx": 0,
    "search_results": [], "raw_sources": [],
    "synthesized_facts": [], "draft": "",
    "revision": 0, "grade": "", "feedback": "",
    "next_agent": "", "is_done": False
}

# Planner
state.update(planner(state))
print(f"✓ Planner: {len(state['sub_tasks'])} sub-tasks")

# Searcher — once per sub-task
for i in range(len(state["sub_tasks"])):
    state.update(web_searcher(state))
    print(f"✓ Searcher: task {i+1} done, {len(state['search_results'])} results total")

# Synthesizer
state.update(synthesizer(state))
print(f"✓ Synthesizer: {len(state['synthesized_facts'])} facts")

# Writer + Grader loop (max 2 revisions)
while not state["is_done"]:
    state.update(writer(state))
    print(f"✓ Writer: revision {state['revision']} — {len(state['draft'])} chars")

    state.update(grader(state))
    print(f"✓ Grader: {state['grade']}")

print("\n✅ Pipeline complete!")
print("\n--- FINAL REPORT ---")
print(state["draft"])