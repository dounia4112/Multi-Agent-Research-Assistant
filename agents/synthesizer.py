import os, sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from state import ResearchState
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import json

load_dotenv(override=True)

SYNTH_PROMPT = """
You are a research analyst. Given these search results about "{query}",
extract a list of unique, factual claims. Remove duplicates.

Return ONLY valid JSON, no explanation, no markdown fences.

Format: {{"facts": ["fact1", "fact2", "fact3", ...]}}

Search results:
{results_text}
"""


def synthesizer(state: ResearchState)-> dict:
    llm = ChatGroq(
        model = "llama-3.3-70b-versatile",
        temperature = 0
    )

    results_text = "\n\n".join([
        f"[{r['title']}] ({r['url']})\n{r['content']}"
        for r in state["search_results"]
    ])

    response = llm.invoke(SYNTH_PROMPT.format(
        query = state['query'],
        results_text =results_text[:8000]
    ))

    content = response.content.strip()

    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith('json'):
            content = content[4:]

    parsed = json.loads(content)


    return {
        "synthesized_facts": parsed["facts"]
    }