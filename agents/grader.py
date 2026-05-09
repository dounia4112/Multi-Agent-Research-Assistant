import os, sys, json
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from state import ResearchState

load_dotenv(override=True)

GRADER_PROMPT = """
You are a research quality reviewer. Grade this research report.

Check all of the following:
1. Does it directly answer the query: "{query}"?
2. Does it have an Executive Summary section?
3. Does it have a Key Findings section?
4. Does it have an Analysis section?
5. Is the analysis meaningful (not just repeated bullet points)?

Return ONLY valid JSON, no explanation, no markdown fences.

Format:
{{"grade": "pass" or "needs_revision", "feedback": "specific issues if needs_revision, empty string if pass", "score": 1-10}}

Report to grade:
{draft}
"""

MAX_REVISIONS = 2

def grader(state: ResearchState) -> dict:
    if state.get("revision", 0) >= MAX_REVISIONS:
        print("⚠ Max revisions reached — forcing pass")
        return {"grade": "pass", "feedback": "", "is_done": True}

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

    response = llm.invoke(GRADER_PROMPT.format(
        query=state["query"],
        draft=state["draft"][:5000]
    ))

    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        print("⚠ Grader JSON parse failed — defaulting to pass")
        return {"grade": "pass", "feedback": "", "is_done": True}

    is_done = parsed["grade"] == "pass"

    print(f"✓ Grader: {parsed['grade']} (score: {parsed['score']}/10)")
    if not is_done:
        print(f"  Feedback: {parsed['feedback']}")

    return {
        "grade":    parsed["grade"],
        "feedback": parsed.get("feedback", ""),
        "is_done":  is_done
    }