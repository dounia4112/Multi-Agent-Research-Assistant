import os, sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from state import ResearchState
from tavily import TavilyClient
from dotenv import load_dotenv


load_dotenv(override=True)
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]

def planner(state: ResearchState) -> ResearchState:
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

    result = tavily_client.search(state["query"])

    filtered_results = [
        {
            "url": item.get("url"),
            "title": item.get("title"),
            "content": item.get("content")
        }
        for item in result.get("results", [])
    ]

    state["search_results"] = filtered_results

    return state