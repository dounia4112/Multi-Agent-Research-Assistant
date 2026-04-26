import os, sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

# from agents.planner import planner
from agents.web_searcher import planner
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


result = planner(fake_state)


print("\n\n ###### RESULT ######", result)