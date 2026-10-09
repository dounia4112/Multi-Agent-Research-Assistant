import os, sys
# `streamlit run frontend/streamlit.py` only puts frontend/ on the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timezone

import streamlit as st

from database import db
from graph import build_graph, run_pipeline

st.set_page_config(page_title="Multi-Agent Research Assistant", page_icon="🔬", layout="wide")

SECRET_KEYS = ["GROQ_API_KEY", "TAVILY_API_KEY", "DATABASE_URL", "GROQ_FAST_MODEL", "GROQ_SMART_MODEL"]


def load_secrets_into_env():
    """The shared code reads os.environ. Streamlit Cloud usually exports top-level secrets
    as env vars, but copy them explicitly so a running app never misses one."""
    try:
        for key in SECRET_KEYS:
            if not os.environ.get(key) and key in st.secrets:
                os.environ[key] = str(st.secrets[key]).strip()
    except Exception:
        pass   # no secrets file (e.g. running locally with a .env)


def short_error(e: Exception) -> str:
    first_line = str(e).strip().splitlines()[0] if str(e).strip() else ""
    return f"{type(e).__name__}: {first_line}" if first_line else type(e).__name__


@st.cache_resource(ttl=600)   # re-check every 10 min, so a temporary outage doesn't stick
def database_status() -> tuple[bool, str]:
    """Create the table on first use (Streamlit doesn't run the API's startup hook)."""
    if not db.is_enabled():
        return False, "DATABASE_URL is not set, so reports are not saved."
    try:
        db.init_db()
        return True, "Reports are saved to the database."
    except Exception as e:
        return False, f"Database unreachable, reports are not saved ({short_error(e)})."


load_secrets_into_env()

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

db_ok, db_message = database_status()
st.caption(("🟢 " if db_ok else "⚪ ") + db_message)

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

    created_at = datetime.now(timezone.utc)
    run_id, save_error = None, None
    db_ok, db_message = database_status()
    if db_ok:
        try:
            run_id = db.insert_run(
                query=final["query"],
                report=final["draft"],
                facts=final["synthesized_facts"],
                grade=final["grade"],
                revision=final["revision"],
                created_at=created_at,
            )
        except Exception as e:
            save_error = short_error(e)

    progress_bar.progress(1.0)
    with report_box.container():
        saved = f" · saved as report #{run_id}" if run_id else ""
        st.caption(f"🗓️ Generated {created_at:%d %b %Y, %H:%M} UTC{saved}")
        if save_error:
            st.warning(f"The report could not be saved to the database ({save_error}).")
        elif not db_ok:
            st.info(db_message)
        st.markdown(final["draft"])

    m1, m2, m3 = st.columns(3)
    m1.metric("Facts", len(final["synthesized_facts"]))
    m2.metric("Revisions", final["revision"])
    m3.metric("Grade", f"{final['grade'] or '—'} ({final['score']}/10)")

    st.download_button(
        "⬇️ Download report (.md)",
        data=final["draft"],
        file_name=f"research_report_{created_at:%Y-%m-%d}.md",
        mime="text/markdown",
    )
