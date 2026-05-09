import os, sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from dotenv import load_dotenv
from state import ResearchState
from langchain_groq import ChatGroq

load_dotenv(override=True)

WRITER_PROMPT = """
Write a well-structured research report in Markdown about: "{query}"

Use these verified facts:
{facts}

{revision_instruction}

Your report must follow this exact structure:
## Executive Summary
2-3 sentences summarizing the key finding.

## Key Findings
Bullet points covering the most important facts.

## Analysis
2-3 paragraphs with deeper interpretation.

## References
List the sources mentioned in the facts.

Write the full report now. No preamble, start directly with ## Executive Summary.
"""

def writer(state: ResearchState) -> dict:
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.3
    )

    revision_instruction = ""
    if state.get("feedback"):
        revision_instruction = (
            f"IMPORTANT — This is revision #{state['revision'] + 1}. "
            f"The previous draft was rejected. Fix these issues: {state['feedback']}"
        )

    facts_text = "\n".join([f"- {f}" for f in state["synthesized_facts"]])  # fixed typo

    response = llm.invoke(WRITER_PROMPT.format(
        query=state["query"],
        facts=facts_text,
        revision_instruction=revision_instruction
    ))


    return {
        "draft":    response.content.strip(),
        "revision": state.get("revision", 0) + 1,
        "grade":    "",
        "feedback": ""
    }
