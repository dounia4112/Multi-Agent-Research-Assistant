import os, sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from state import ResearchState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
import json
import logging
from dotenv import load_dotenv


load_dotenv(override=True)

logger = logging.getLogger(__name__)

PLANNER_PROMPT = """
You are a research planner. Given a research question, decompose it into
3-5 specific, searchable sub-tasks. Each sub-task should be a focused
search query on its own.

Return ONLY valid JSON, no explanation, no markdown fences.

Format: {{"sub_tasks": ["task1", "task2", "task3"]}}

Research question: {query}
"""


def planner(state:ResearchState) -> dict:
    llm = ChatGroq(
        model = "llama-3.1-8b-instant",
        temperature = 0
    )

    response = llm.invoke(PLANNER_PROMPT.format(query = state['query']))

    # Strip markdown fences if the model adds them anyway
    content = response.content.strip()

    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith('json'):
            content = content[4:]

    
    parsed = json.loads(content)

    return {
        "sub_tasks": parsed["sub_tasks"],
        "current_task_idx": 0
    }