import os, sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from agents.planner import planner
from agents.web_searcher import web_searcher
from agents.synthesizer import synthesizer
import logging

logger = logging.getLogger(__name__)

fake_state = {
    "query": "What is the impact of LLMs on software engineering jobs in 2025?",
    "sub_tasks": [],
    "current_task_idx": 0,
    "search_results": [],
    "raw_sources": [],
    "synthesized_facts": [],
    "draft": "",
    "revision": 0,
    "grade": "",
    "feedback": "",
    "next_agent": "",
    "is_done": False
}

fake_state.update(planner(fake_state))

# Run searcher once per sub-task
for i in range(len(fake_state["sub_tasks"])):
    fake_state.update(web_searcher(fake_state))
    print(f"✓ Searcher: task {i+1} done, {len(fake_state['search_results'])} results total")


print('result', synthesizer(fake_state))
fake_state.update(synthesizer(fake_state))
print(f"✓ Synthesizer: {len(fake_state['synthesized_facts'])} facts extracted")
for fact in fake_state["synthesized_facts"][:3]:
    print(f"  — {fact}")


# print("\n\n ###### RESULT ######", result)