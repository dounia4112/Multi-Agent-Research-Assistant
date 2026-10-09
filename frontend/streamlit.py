import os, sys
# `streamlit run frontend/streamlit.py` only puts frontend/ on the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st

from database.db import save_run
from graph import build_graph, run_pipeline

st.set_page_config(page_title="Multi-Agent Research Assistant", page_icon="🔬", layout="wide")

st.markdown("""
<style>
  .block-container { padding-top: 2.5rem; }
  div[data-testid="stTextInput"] input {
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 0.95rem;
  }
  div[data-testid="stFormSubmitButton"] button {
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.4rem;
  }
  .agent-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    border-radius: 8px;
    border: 1px solid rgba(128,128,128,0.25);
    background: rgba(128,128,128,0.05);
    transition: all 0.25s ease;
  }
  .agent-card.running {
    border-color: #c8b87a;
    background: rgba(200,184,122,0.10);
  }
  .agent-card.done {
    border-color: #7a9e8a;
    background: rgba(122,158,138,0.10);
  }
  .agent-icon { font-size: 1.15rem; flex-shrink: 0; }
  .agent-label { font-weight: 600; font-size: 0.85rem; }
  .agent-msg   { font-size: 0.75rem; opacity: 0.65; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_graph():
    return build_graph()


AGENTS = [
    {"key": "planner",      "label": "Planner",      "icon": "🗂️", "sub": "Query decomposition"},
    {"key": "web_searcher", "label": "Web Searcher",  "icon": "🌐", "sub": "Tavily search"},
    {"key": "synthesizer",  "label": "Synthesizer",   "icon": "🔗", "sub": "Fact extraction"},
    {"key": "writer",       "label": "Writer",        "icon": "✍️", "sub": "Report drafting"},
    {"key": "grader",       "label": "Grader",        "icon": "✅", "sub": "Quality review"},
]
AGENTS_BY_KEY = {a["key"]: a for a in AGENTS}


def render_agent_card(slot, agent, state="idle", msg=None):
    icon = agent["icon"] if state != "idle" else "⬜"
    slot.markdown(
        f'<div class="agent-card {state}">'
        f'<span class="agent-icon">{icon}</span>'
        f'<div><div class="agent-label">{agent["label"]}</div>'
        f'<div class="agent-msg">{msg or agent["sub"]}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


st.title("🔬 Multi-Agent Research Assistant")
st.caption("Five LangGraph agents plan, search, synthesize, write and grade a research report.")

with st.form("query_form"):
    query = st.text_input(
        "Enter your research question",
        placeholder="e.g. What is the impact of LLMs on software engineering jobs in 2025?",
        max_chars=500,
    )
    run = st.form_submit_button("🚀 Research", type="primary")

if run and len(query.strip()) < 3:
    st.warning("Please enter a research question.")
elif run:
    col1, col2 = st.columns([1, 2])

    with col1:
        progress_bar = st.progress(0)
        slots = {a["key"]: st.empty() for a in AGENTS}
        for a in AGENTS:
            render_agent_card(slots[a["key"]], a)
        render_agent_card(slots["planner"], AGENTS_BY_KEY["planner"], "running")
        facts_box = st.empty()

    with col2:
        st.subheader("Research Report")
        report_box = st.empty()
        report_box.info("Report will appear here once complete...")

    final = None
    done_agents = set()

    try:
        with st.spinner("Agents are researching..."):
            for event, final in run_pipeline(get_graph(), query.strip()):
                agent_name, next_agent = event["agent"], event["next"]

                # The supervisor tells us who acts next (the searcher repeats, the writer may revise)
                state = "running" if next_agent == agent_name else "done"
                render_agent_card(slots[agent_name], AGENTS_BY_KEY[agent_name], state, event["message"])
                if state == "done":
                    done_agents.add(agent_name)
                if next_agent in slots and next_agent != agent_name:
                    render_agent_card(slots[next_agent], AGENTS_BY_KEY[next_agent], "running")
                progress_bar.progress(len(done_agents) / len(AGENTS))

                if agent_name == "synthesizer":
                    with facts_box.container():
                        st.markdown("**Extracted Facts**")
                        for fact in event["payload"]:
                            st.markdown(f"- {fact}")
    except Exception as e:
        report_box.empty()
        st.error(f"⚠️ Research failed: {e}")
        st.stop()

    save_run(
        query=final["query"],
        report=final["draft"],
        facts=final["synthesized_facts"],
        grade=final["grade"],
        revision=final["revision"],
    )

    progress_bar.progress(1.0)
    report_box.markdown(final["draft"])

    m1, m2, m3 = st.columns(3)
    m1.metric("Facts", len(final["synthesized_facts"]))
    m2.metric("Revisions", final["revision"])
    m3.metric("Grade", f"{final['grade'] or '—'} ({final['score']}/10)")

    st.download_button(
        "⬇️ Download report (.md)",
        data=final["draft"],
        file_name="research_report.md",
        mime="text/markdown",
    )
