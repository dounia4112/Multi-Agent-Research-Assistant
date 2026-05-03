import os, sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from state import ResearchState
from tavily import TavilyClient
from dotenv import load_dotenv


load_dotenv(override=True)
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]

def web_searcher(state: ResearchState) -> ResearchState:
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

    idx = state['current_task_idx']
    current_sub_task = state['sub_tasks'][idx]

    result = tavily_client.search(current_sub_task, max_results=5)

    filtered_results = [
        {
            "url": item.get("url"),
            "title": item.get("title"),
            "content": item.get("content")
        }
        for item in result.get("results", [])
    ]

    existing = state.get("search_results", [])
    

    state['search_results'] = existing + filtered_results
    state['current_task_idx'] = idx +1
    return state