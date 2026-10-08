import os, sys
# `streamlit run frontend/streamlit.py` only puts frontend/ on the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st

from database.db import save_run
from graph import build_graph, run_pipeline

st.set_page_config(page_title="Multi-Agent Research Assistant", page_icon="🔬", layout="wide")


@st.cache_resource
def get_graph():
    return build_graph()


AGENT_LABELS = {
    "planner":      ("🗂️", "Planner"),
    "web_searcher": ("🌐", "Web Searcher"),
    "synthesizer":  ("🔗", "Synthesizer"),
    "writer":       ("✍️", "Writer"),
    "grader":       ("✅", "Grader"),
}

st.title("🔬 Multi-Agent Research Assistant")
st.caption("Five LangGraph agents plan, search, synthesize, write and grade a research report.")

with st.form("query_form"):
    query = st.text_input(
        "Enter your research question",
        placeholder="e.g. What is the impact of LLMs on software engineering jobs in 2025?",
        max_chars=500,
    )
    run = st.form_submit_button("Research", type="primary")

if run and len(query.strip()) < 3:
    st.warning("Please enter a research question.")
elif run:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Agent Progress")
        slots = {name: st.empty() for name in AGENT_LABELS}
        for name, (_, label) in AGENT_LABELS.items():
            slots[name].markdown(f"⬜ **{label}** — waiting")
        facts_box = st.empty()

    with col2:
        st.subheader("Research Report")
        report_box = st.empty()
        report_box.info("Report will appear here once complete...")

    final = None
    try:
        with st.spinner("Agents at work…"):
            for event, final in run_pipeline(get_graph(), query.strip()):
                icon, label = AGENT_LABELS[event["agent"]]
                slots[event["agent"]].markdown(f"{icon} **{label}** — {event['message']}")

                if event["agent"] == "synthesizer":
                    with facts_box.container():
                        st.markdown("**Extracted Facts**")
                        for fact in event["payload"]:
                            st.markdown(f"- {fact}")
    except Exception as e:
        st.error(f"The research pipeline failed: {e}")
        st.stop()

    save_run(
        query=final["query"],
        report=final["draft"],
        facts=final["synthesized_facts"],
        grade=final["grade"],
        revision=final["revision"],
    )

    report_box.markdown(final["draft"])
    st.success(f"✅ Done — {len(final['synthesized_facts'])} facts · "
               f"{final['revision']} revision(s) · Grade: {final['grade']} ({final['score']}/10)")
    st.download_button("Download report (.md)", final["draft"], file_name="research_report.md")
