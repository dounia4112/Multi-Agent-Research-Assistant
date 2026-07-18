import os, sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from graph import build_graph
from database.db import save_run
import streamlit as st
from dotenv import load_dotenv
load_dotenv(override=True)

st.set_page_config(page_title="Multi-Agent Research Assistant", page_icon="🔬", layout="wide")

st.markdown("""
<style>
  .block-container { padding-top: 2.5rem; }
  div[data-testid="stTextInput"] input {
    border-radius: 8px;
    padding: 12px 14px;
    font-size: 0.95rem;
  }
  div[data-testid="stButton"] button {
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

st.title("🔬 Multi-Agent Research Assistant")

graph = build_graph()

AGENTS = [
    {"key": "planner",      "label": "Planner",      "icon": "🗂️", "sub": "Query decomposition"},
    {"key": "web_searcher", "label": "Web Searcher",  "icon": "🌐", "sub": "Tavily search"},
    {"key": "synthesizer",  "label": "Synthesizer",   "icon": "🔗", "sub": "Fact extraction"},
    {"key": "writer",       "label": "Writer",        "icon": "✍️", "sub": "Report drafting"},
    {"key": "grader",       "label": "Grader",        "icon": "✅", "sub": "Quality review"},
]

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

query = st.text_input("Enter your research question",
    placeholder="e.g. What is the impact of LLMs on software engineering jobs in 2025?")

run = st.button("🚀 Research", type="primary", disabled=not query)

if run and query:
    col1, col2 = st.columns([1, 2])

    with col1:
        progress_bar = st.progress(0)
        slots = {a["key"]: st.empty() for a in AGENTS}
        for a in AGENTS:
            render_agent_card(slots[a["key"]], a)
        facts_box = st.empty()

    with col2:
        st.subheader("Research Report")
        report_box = st.empty()
        report_box.info("Report will appear here once complete...")

    initial_state = {
        "query": query,
        "sub_tasks": [], "current_task_idx": 0,
        "search_results": [], "raw_sources": [],
        "synthesized_facts": [], "draft": "",
        "revision": 0, "grade": "", "feedback": "",
        "next_agent": "", "is_done": False
    }

    full_state = dict(initial_state)
    seen_agents = set()

    try:
        with st.spinner("Agents are researching..."):
            # Stream graph updates directly — the accumulated full_state
            # below already holds the final result, so we don't need a
            # second graph.invoke() call once the stream finishes.
            for chunk in graph.stream(initial_state):
                agent_name  = list(chunk.keys())[0]
                agent_state = chunk[agent_name]
                full_state.update(agent_state)

                agent = next((a for a in AGENTS if a["key"] == agent_name), None)
                if agent:
                    if agent_name == "planner":
                        msg = f"Created {len(agent_state.get('sub_tasks', []))} sub-tasks"
                    elif agent_name == "web_searcher":
                        msg = f"Found {len(agent_state.get('search_results', []))} results so far"
                    elif agent_name == "synthesizer":
                        msg = f"Extracted {len(agent_state.get('synthesized_facts', []))} facts"
                        facts = agent_state.get("synthesized_facts", [])
                        if facts:
                            with facts_box.container():
                                st.markdown("**Extracted Facts**")
                                for f in facts:
                                    st.markdown(f"- {f}")
                    elif agent_name == "writer":
                        msg = f"Revision {agent_state.get('revision', 1)} written"
                    elif agent_name == "grader":
                        msg = f"Grade: {agent_state.get('grade', '')}"
                    else:
                        msg = "done"

                    render_agent_card(slots[agent_name], agent, "done", msg)
                    seen_agents.add(agent_name)
                    progress_bar.progress(min(len(seen_agents) / len(AGENTS), 1.0))

        save_run(
            query    = query.strip(),
            report   = full_state["draft"],
            facts    = full_state["synthesized_facts"],
            grade    = full_state["grade"],
            revision = full_state["revision"]
        )

        report_box.markdown(full_state["draft"])

        m1, m2, m3 = st.columns(3)
        m1.metric("Facts", len(full_state["synthesized_facts"]))
        m2.metric("Revisions", full_state["revision"])
        m3.metric("Grade", full_state["grade"] or "—")

        st.download_button(
            "⬇️ Download report (.md)",
            data=full_state["draft"],
            file_name="research_report.md",
            mime="text/markdown",
        )

    except Exception as e:
        report_box.empty()
        st.error(f"⚠️ Research failed: {e}")



# import streamlit as st
# import os, sys, time
# from datetime import datetime
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from dotenv import load_dotenv
# load_dotenv(override=True)

# from graph import build_graph

# # ── Page config ───────────────────────────────────────────
# st.set_page_config(
#     page_title="Research Assistant",
#     layout="wide",
#     page_icon="🔬",
#     initial_sidebar_state="collapsed"
# )

# # ── Inject fonts + global CSS ─────────────────────────────
# st.markdown("""
# <link rel="preconnect" href="https://fonts.googleapis.com">
# <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">

# <style>
# :root {
#   --bg:      #0a0a08;
#   --surface: #111110;
#   --border:  #1e1e1c;
#   --border2: #5b5b51;
#   --text:    #e8e6e0;
#   --muted:   #9a9787;
#   --accent:  #c8b87a;
#   --accent2: #7a9e8a;
#   --danger:  #c47a6a;
#   --mono:    'JetBrains Mono', monospace;
#   --serif:   'Playfair Display', Georgia, serif;
#   --sans:    'DM Sans', sans-serif;
# }

# /* ── Reset Streamlit chrome ── */
# html, body, [data-testid="stAppViewContainer"],
# [data-testid="stMain"], [data-testid="block-container"] {
#   background: var(--bg) !important;
#   color: var(--text) !important;
#   font-family: var(--sans) !important;
#   padding: 0 !important;
#   margin: 0 !important;
#   max-width: 100% !important;
# }
# [data-testid="stHeader"]          { display: none !important; }
# [data-testid="stSidebar"]         { display: none !important; }
# [data-testid="stToolbar"]         { display: none !important; }
# [data-testid="stDecoration"]      { display: none !important; }
# footer                            { display: none !important; }
# #MainMenu                         { display: none !important; }
# [data-testid="stStatusWidget"]    { display: none !important; }
# [data-testid="collapsedControl"]  { display: none !important; }

# /* ── Scrollbar ── */
# ::-webkit-scrollbar { width: 3px; }
# ::-webkit-scrollbar-track { background: transparent; }
# ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

# /* ── Header ── */
# .ra-header {
#   grid-column: 1 / -1;
#   border-bottom: 1px solid var(--border);
#   padding: 0 32px;
#   display: flex;
#   align-items: center;
#   justify-content: space-between;
#   height: 56px;
#   background: var(--bg);
#   position: sticky;
#   top: 0;
#   z-index: 100;
# }
# .ra-logo {
#   font-family: var(--serif);
#   font-size: 1.15rem;
#   font-weight: 400;
#   color: var(--text);
#   display: flex;
#   align-items: center;
#   gap: 10px;
# }
# .ra-logo-dot {
#   width: 6px; height: 6px;
#   border-radius: 50%;
#   background: var(--accent);
#   box-shadow: 0 0 8px var(--accent);
#   animation: breathe 3s ease-in-out infinite;
#   flex-shrink: 0;
# }
# @keyframes breathe {
#   0%,100% { opacity:1; box-shadow: 0 0 8px var(--accent); }
#   50%      { opacity:.5; box-shadow: 0 0 3px var(--accent); }
# }
# .ra-header-meta {
#   font-family: var(--mono);
#   font-size: 0.65rem;
#   color: var(--muted);
#   letter-spacing: 0.08em;
#   text-transform: uppercase;
#   display: flex;
#   align-items: center;
#   gap: 20px;
# }
# .ra-pill {
#   display: flex;
#   align-items: center;
#   gap: 6px;
#   padding: 3px 10px;
#   border: 1px solid var(--border2);
#   border-radius: 20px;
#   font-size: 0.62rem;
#   letter-spacing: 0.06em;
#   text-transform: uppercase;
#   color: var(--muted);
# }
# .ra-pill.active { border-color: var(--accent2); color: var(--accent2); }
# .ra-pill-dot {
#   width: 5px; height: 5px;
#   border-radius: 50%;
#   background: var(--border2);
# }
# .ra-pill.active .ra-pill-dot { background: var(--accent2); box-shadow: 0 0 6px var(--accent2); }

# /* ── Shell ── */
# .ra-shell {
#   display: grid;
#   grid-template-columns: 260px 1fr;
#   min-height: calc(100vh - 56px);
# }

# /* ── Sidebar ── */
# .ra-aside {
#   border-right: 1px solid var(--border);
#   padding: 24px 0;
#   overflow-y: auto;
# }
# .ra-sidebar-label {
#   font-family: var(--mono);
#   font-size: 0.58rem;
#   letter-spacing: 0.12em;
#   text-transform: uppercase;
#   color: var(--muted);
#   margin-bottom: 12px;
#   padding: 0 20px;
# }
# .ra-sidebar-section { padding: 0; margin-bottom: 28px; }

# /* Progress bar */
# .ra-progress-wrap { padding: 0 20px; margin-bottom: 24px; }
# .ra-progress-track {
#   height: 1px;
#   background: var(--border);
#   border-radius: 1px;
#   overflow: hidden;
#   margin-bottom: 6px;
# }
# .ra-progress-fill {
#   height: 100%;
#   background: linear-gradient(90deg, var(--accent), var(--accent2));
#   border-radius: 1px;
#   transition: width 0.6s ease;
# }
# .ra-progress-label {
#   display: flex;
#   justify-content: space-between;
#   font-family: var(--mono);
#   font-size: 0.58rem;
#   color: var(--muted);
# }

# /* Agent items */
# .ra-agent-list { display: flex; flex-direction: column; gap: 4px; padding: 0 8px; }
# .ra-agent-item {
#   display: flex;
#   align-items: center;
#   gap: 10px;
#   padding: 8px 10px;
#   border-radius: 6px;
#   border: 1px solid transparent;
#   position: relative;
#   overflow: hidden;
# }
# .ra-agent-item::before {
#   content: '';
#   position: absolute;
#   left: 0; top: 0; bottom: 0;
#   width: 2px;
#   background: var(--accent);
#   transform: scaleY(0);
#   transition: transform 0.3s ease;
#   transform-origin: bottom;
# }
# .ra-agent-item.idle   { opacity: 0.4; }
# .ra-agent-item.running {
#   background: rgba(200,184,122,0.04);
#   border-color: rgba(200,184,122,0.15);
# }
# .ra-agent-item.running::before { transform: scaleY(1); }
# .ra-agent-item.done {
#   background: rgba(122,158,138,0.05);
#   border-color: rgba(122,158,138,0.15);
# }
# .ra-agent-item.done::before { background: var(--accent2); transform: scaleY(1); }
# .ra-agent-idx {
#   font-family: var(--mono);
#   font-size: 0.58rem;
#   color: var(--muted);
#   width: 14px;
#   text-align: center;
#   flex-shrink: 0;
# }
# .ra-agent-info { flex: 1; min-width: 0; }
# .ra-agent-name {
#   font-size: 0.75rem;
#   font-weight: 500;
#   letter-spacing: 0.02em;
# }
# .ra-agent-item.idle    .ra-agent-name { color: var(--muted); }
# .ra-agent-item.running .ra-agent-name { color: var(--accent); }
# .ra-agent-item.done    .ra-agent-name { color: var(--accent2); }
# .ra-agent-sub {
#   font-family: var(--mono);
#   font-size: 0.58rem;
#   color: var(--muted);
#   margin-top: 1px;
#   white-space: nowrap;
#   overflow: hidden;
#   text-overflow: ellipsis;
# }
# .ra-spinner {
#   width: 10px; height: 10px;
#   border: 1.5px solid rgba(200,184,122,0.2);
#   border-top-color: var(--accent);
#   border-radius: 50%;
#   animation: spin 0.8s linear infinite;
#   flex-shrink: 0;
# }
# @keyframes spin { to { transform: rotate(360deg); } }
# .ra-check { font-size: 0.65rem; color: var(--accent2); flex-shrink: 0; }

# /* Facts */
# .ra-fact-item {
#   display: flex;
#   gap: 8px;
#   font-size: 0.7rem;
#   color: var(--muted);
#   line-height: 1.5;
#   margin-bottom: 6px;
#   padding: 0 20px;
#   animation: fadeSlide 0.3s ease both;
# }
# .ra-fact-num {
#   font-family: var(--mono);
#   font-size: 0.58rem;
#   color: var(--border2);
#   flex-shrink: 0;
#   margin-top: 2px;
# }
# @keyframes fadeSlide {
#   from { opacity:0; transform: translateX(-6px); }
#   to   { opacity:1; transform: none; }
# }

# /* ── Main ── */
# .ra-main { display: flex; flex-direction: column; overflow: hidden; }

# /* Input */
# .ra-input-area {
#   padding: 28px 36px 24px;
#   border-bottom: 1px solid var(--border);
# }
# .ra-query-label {
#   font-family: var(--mono);
#   font-size: 0.6rem;
#   letter-spacing: 0.1em;
#   text-transform: uppercase;
#   color: var(--muted);
#   margin-bottom: 10px;
# }
# .ra-query-wrap {
#   display: flex;
#   align-items: flex-start;
#   border: 1px solid var(--border2);
#   border-radius: 8px;
#   background: var(--surface);
# }
# .ra-query-prompt {
#   font-family: var(--mono);
#   font-size: 0.7rem;
#   color: var(--accent);
#   padding: 14px 0 14px 16px;
#   flex-shrink: 0;
#   line-height: 1.6;
#   user-select: none;
# }

# /* Output */
# .ra-output { flex: 1; overflow-y: auto; padding: 32px 36px; }

# /* Empty state */
# .ra-empty {
#   display: flex;
#   flex-direction: column;
#   align-items: center;
#   justify-content: center;
#   min-height: 320px;
#   gap: 16px;
#   text-align: center;
#   opacity: 0.4;
# }
# .ra-empty-glyph {
#   font-family: var(--serif);
#   font-size: 4rem;
#   font-style: italic;
#   color: var(--muted);
#   line-height: 1;
# }
# .ra-empty-title {
#   font-family: var(--serif);
#   font-size: 1.1rem;
#   color: var(--muted);
# }
# .ra-empty-sub { font-size: 0.75rem; color: var(--muted); max-width: 280px; line-height: 1.7; }

# /* Log stream */
# .ra-log { font-family: var(--mono); font-size: 0.65rem; color: var(--muted); line-height: 2; margin-bottom: 24px; }
# .ra-log-line { display: flex; gap: 12px; animation: fadeSlide 0.25s ease both; }
# .ra-log-time  { color: var(--border2); flex-shrink: 0; }
# .ra-log-agent { color: var(--accent); width: 100px; flex-shrink: 0; }
# .ra-log-agent.done { color: var(--accent2); }
# .ra-log-msg   { color: var(--muted); }

# /* Report */
# .ra-report-meta {
#   display: flex;
#   align-items: center;
#   gap: 16px;
#   margin-bottom: 28px;
#   padding-bottom: 16px;
#   border-bottom: 1px solid var(--border);
#   flex-wrap: wrap;
# }
# .ra-meta-item {
#   font-family: var(--mono);
#   font-size: 0.6rem;
#   color: var(--muted);
#   letter-spacing: 0.06em;
#   text-transform: uppercase;
#   display: flex;
#   align-items: center;
#   gap: 6px;
# }
# .ra-meta-val { color: var(--accent2); font-weight: 500; }
# .ra-report-body h2 {
#   font-family: var(--serif);
#   font-size: 1.1rem;
#   font-weight: 600;
#   color: var(--text);
#   margin: 28px 0 10px;
#   padding-bottom: 6px;
#   border-bottom: 1px solid var(--border);
# }
# .ra-report-body p  { font-size: 0.875rem; color: #c0bdb6; line-height: 1.85; margin-bottom: 12px; font-weight: 300; }
# .ra-report-body ul { list-style: none; margin: 0 0 12px 0; padding: 0; }
# .ra-report-body li { font-size: 0.875rem; color: #c0bdb6; line-height: 1.75; margin-bottom: 6px; font-weight: 300; padding-left: 4px; }
# .ra-report-body li::before { content: '—'; color: var(--accent); margin-right: 10px; font-family: var(--mono); font-size: 0.7rem; }

# /* Error */
# .ra-error {
#   padding: 12px 16px;
#   border: 1px solid rgba(196,122,106,0.3);
#   background: rgba(196,122,106,0.05);
#   border-radius: 6px;
#   font-family: var(--mono);
#   font-size: 0.68rem;
#   color: var(--danger);
#   line-height: 1.6;
# }

# /* Streamlit widget overrides */
# div[data-testid="stTextArea"] textarea {
#   background: transparent !important;
#   border: none !important;
#   color: var(--text) !important;
#   font-family: var(--sans) !important;
#   font-size: 0.9rem !important;
#   font-weight: 300 !important;
#   outline: none !important;
#   box-shadow: none !important;
#   resize: none !important;
#   padding: 13px 16px !important;
# }
# div[data-testid="stTextArea"] { background: transparent !important; border: none !important; }
# div[data-testid="stTextArea"] > div { background: transparent !important; border: none !important; box-shadow: none !important; }

# div[data-testid="stButton"] button {
#   background: var(--accent) !important;
#   color: var(--bg) !important;
#   border: none !important;
#   border-radius: 5px !important;
#   font-family: var(--mono) !important;
#   font-size: 0.65rem !important;
#   font-weight: 500 !important;
#   letter-spacing: 0.08em !important;
#   text-transform: uppercase !important;
#   padding: 7px 18px !important;
#   cursor: pointer !important;
#   transition: all 0.2s !important;
# }
# div[data-testid="stButton"] button:hover {
#   background: #d4c98a !important;
#   transform: translateY(-1px) !important;
#   box-shadow: 0 4px 12px rgba(200,184,122,0.3) !important;
# }
# div[data-testid="stButton"] button:disabled {
#   background: var(--border2) !important;
#   color: var(--muted) !important;
# }
# </style>
# """, unsafe_allow_html=True)

# # ── State init ────────────────────────────────────────────
# if "graph" not in st.session_state:
#     st.session_state.graph = build_graph()

# if "agent_states" not in st.session_state:
#     st.session_state.agent_states = {}

# if "log_lines" not in st.session_state:
#     st.session_state.log_lines = []

# if "facts" not in st.session_state:
#     st.session_state.facts = []

# if "report" not in st.session_state:
#     st.session_state.report = None

# if "running" not in st.session_state:
#     st.session_state.running = False

# if "status" not in st.session_state:
#     st.session_state.status = ("Idle", False)

# AGENTS = [
#     {"key": "planner",      "label": "Planner",      "sub": "Query decomposition"},
#     {"key": "web_searcher", "label": "Web Searcher",  "sub": "Tavily search"      },
#     {"key": "synthesizer",  "label": "Synthesizer",   "sub": "Fact extraction"    },
#     {"key": "writer",       "label": "Writer",        "sub": "Report drafting"    },
#     {"key": "grader",       "label": "Grader",        "sub": "Quality review"     },
# ]

# # ── Helper renderers ──────────────────────────────────────
# def render_agent_item(a, state, msg):
#     idx = str(AGENTS.index(a) + 1).zfill(2)
#     spinner = '<div class="ra-spinner"></div>' if state == "running" else ""
#     check   = '<div class="ra-check">✓</div>'  if state == "done"    else ""
#     return f"""
#     <div class="ra-agent-item {state}">
#       <span class="ra-agent-idx">{idx}</span>
#       <div class="ra-agent-info">
#         <div class="ra-agent-name">{a['label']}</div>
#         <div class="ra-agent-sub">{msg or a['sub']}</div>
#       </div>
#       {spinner}{check}
#     </div>"""

# def render_progress(done_count):
#     pct = round((done_count / len(AGENTS)) * 100)
#     return f"""
#     <div class="ra-progress-wrap">
#       <div class="ra-progress-track">
#         <div class="ra-progress-fill" style="width:{pct}%"></div>
#       </div>
#       <div class="ra-progress-label">
#         <span>Pipeline</span><span>{pct}%</span>
#       </div>
#     </div>"""

# def render_report_body(draft):
#     html = ""
#     in_list = False

#     for line in draft.split("\n"):

#         if line.startswith("## "):
#             if in_list:
#                 html += "</ul>"
#                 in_list = False
#             html += f"<h2>{line[3:]}</h2>"

#         elif line.startswith("# "):
#             if in_list:
#                 html += "</ul>"
#                 in_list = False
#             html += f"<h2>{line[2:]}</h2>"

#         elif line.startswith("* ") or line.startswith("- "):
#             if not in_list:
#                 html += "<ul>"
#                 in_list = True
#             html += f"<li>{line[2:]}</li>"

#         elif line.strip() == "":
#             if in_list:
#                 html += "</ul>"
#                 in_list = False

#         else:
#             if in_list:
#                 html += "</ul>"
#                 in_list = False
#             html += f"<p>{line}</p>"

#     if in_list:
#         html += "</ul>"

#     return html

# def ts():
#     return datetime.now().strftime("%H:%M:%S")

# # ── Header ────────────────────────────────────────────────
# status_text, status_active = st.session_state.status
# pill_class = "ra-pill active" if status_active else "ra-pill"
# dot_style  = "background:var(--accent2);box-shadow:0 0 6px var(--accent2)" if status_active else ""

# st.markdown(f"""
# <div class="ra-header">
#   <div class="ra-logo">
#     <div class="ra-logo-dot"></div>
#     Research Assistant
#   </div>
#   <div class="ra-header-meta">
#     <span>LangGraph · Groq · Tavily</span>
#     <div class="{pill_class}">
#       <div class="ra-pill-dot" style="{dot_style}"></div>
#       <span>{status_text}</span>
#     </div>
#   </div>
# </div>
# """, unsafe_allow_html=True)

# # ── Shell ─────────────────────────────────────────────────
# # st.markdown('<div class="ra-shell">', unsafe_allow_html=True)

# # ── Sidebar HTML ──────────────────────────────────────────
# done_count   = sum(1 for a in AGENTS if st.session_state.agent_states.get(a["key"]) == "done")
# has_activity = bool(st.session_state.agent_states)

# progress_html = render_progress(done_count) if has_activity else ""

# agents_html = '<div class="ra-agent-list">'
# for a in AGENTS:
#     state = st.session_state.agent_states.get(a["key"], "idle")
#     msg   = st.session_state.agent_states.get(f"{a['key']}_msg", "")
#     agents_html += render_agent_item(a, state, msg)
# agents_html += "</div>"

# facts_html = ""
# if st.session_state.facts:
#     facts_html += '<div class="ra-sidebar-section"><div class="ra-sidebar-label">Extracted facts</div>'
#     for i, f in enumerate(st.session_state.facts):
#         delay = i * 0.05
#         facts_html += f'<div class="ra-fact-item" style="animation-delay:{delay}s"><span class="ra-fact-num">{str(i+1).zfill(2)}</span><span>{f}</span></div>'
#     facts_html += "</div>"

# st.markdown(f"""
# <div class="ra-aside">
#   {progress_html}
#   <div class="ra-sidebar-section">
#     <div class="ra-sidebar-label">Agents</div>
#     {agents_html}
#   </div>
#   {facts_html}
# </div>
# """, unsafe_allow_html=True)

# # ── Main area ─────────────────────────────────────────────

# st.markdown(
#     '<div class="ra-query-label">Research query</div>',
#     unsafe_allow_html=True
# )

# query_container = st.container()

# with query_container:
#     col_input, col_btn = st.columns([10, 1])

#     with col_input:
#         query = st.text_area(
#             "",
#             label_visibility="collapsed",
#             placeholder="What do you want to research? e.g. Impact of LLMs on software engineering jobs in 2025",
#             height=68,
#             key="query_input"
#         )

#     with col_btn:
#         st.write("")
#         run = st.button(
#             "Run ⏎",
#             disabled=st.session_state.running
#         )

# # ── Output area ───────────────────────────────────────────
# st.markdown('<div class="ra-output">', unsafe_allow_html=True)

# if not has_activity and not st.session_state.report:
#     st.markdown("""
#     <div class="ra-empty">
#       <div class="ra-empty-glyph">∂</div>
#       <div class="ra-empty-title">Nothing yet</div>
#       <div class="ra-empty-sub">Enter a research question above and the agents will get to work.</div>
#     </div>
#     """, unsafe_allow_html=True)

# elif st.session_state.report:
#     r = st.session_state.report
#     body_html = render_report_body(r["draft"])
#     st.markdown(f"""
#     <div class="ra-report-meta">
#       <div class="ra-meta-item">Facts <span class="ra-meta-val">{len(r['facts'])}</span></div>
#       <div class="ra-meta-item">Revisions <span class="ra-meta-val">{r['revision']}</span></div>
#       <div class="ra-meta-item">Grade <span class="ra-meta-val">{r['grade']}</span></div>
#       <div class="ra-meta-item">Query <span class="ra-meta-val" style="font-style:italic;text-transform:none;letter-spacing:0">{r['query']}</span></div>
#     </div>
#     <div class="ra-report-body">{body_html}</div>
#     """, unsafe_allow_html=True)
#     st.download_button(
#         label="⎘ Download report",
#         data=r["draft"],
#         file_name="research_report.md",
#         mime="text/markdown"
#     )

# elif has_activity:
#     log_html = '<div class="ra-log">'
#     for line in st.session_state.log_lines:
#         agent_cls = "done" if line["done"] else ""
#         log_html += f"""
#         <div class="ra-log-line">
#           <span class="ra-log-time">{line['time']}</span>
#           <span class="ra-log-agent {agent_cls}">[{line['agent']}]</span>
#           <span class="ra-log-msg">{line['msg']}</span>
#         </div>"""
#     log_html += "</div>"
#     st.markdown(log_html, unsafe_allow_html=True)

# st.markdown("</div>", unsafe_allow_html=True)  # close ra-output
# # st.markdown("</div>", unsafe_allow_html=True)  # close ra-main
# # st.markdown("</div>", unsafe_allow_html=True)  # close ra-shell

# # ── Run pipeline ──────────────────────────────────────────
# if run and query.strip():
#     # Reset
#     st.session_state.agent_states = {}
#     st.session_state.log_lines    = []
#     st.session_state.facts        = []
#     st.session_state.report       = None
#     st.session_state.running      = True
#     st.session_state.status       = ("Running", True)

#     initial_state = {
#         "query": query.strip(),
#         "sub_tasks": [], "current_task_idx": 0,
#         "search_results": [], "raw_sources": [],
#         "synthesized_facts": [], "draft": "",
#         "revision": 0, "grade": "", "feedback": "",
#         "next_agent": "", "is_done": False
#     }

#     st.session_state.log_lines.append({
#         "time": ts(), "agent": "system",
#         "msg": f'Research started — "{query.strip()}"', "done": False
#     })

#     try:
#         for chunk in st.session_state.graph.stream(initial_state):
#             agent_name  = list(chunk.keys())[0]
#             agent_state = chunk[agent_name]

#             if agent_name == "planner":
#                 msg = f"Created {len(agent_state.get('sub_tasks', []))} sub-tasks"
#             elif agent_name == "web_searcher":
#                 msg = f"Found {len(agent_state.get('search_results', []))} results so far"
#             elif agent_name == "synthesizer":
#                 msg  = f"Extracted {len(agent_state.get('synthesized_facts', []))} facts"
#                 st.session_state.facts = agent_state.get("synthesized_facts", [])
#             elif agent_name == "writer":
#                 msg = f"Draft revision {agent_state.get('revision', 1)} written"
#             elif agent_name == "grader":
#                 msg = f"Grade: {agent_state.get('grade', '')}"
#             else:
#                 msg = ""

#             # Mark previous agent done, current done
#             idx = next((i for i, a in enumerate(AGENTS) if a["key"] == agent_name), None)
#             if idx is not None:
#                 st.session_state.agent_states[agent_name]           = "done"
#                 st.session_state.agent_states[f"{agent_name}_msg"]  = msg
#                 # Mark next as running if exists
#                 if idx + 1 < len(AGENTS):
#                     next_key = AGENTS[idx + 1]["key"]
#                     if st.session_state.agent_states.get(next_key) != "done":
#                         st.session_state.agent_states[next_key] = "running"

#             st.session_state.log_lines.append({
#                 "time": ts(), "agent": agent_name, "msg": msg, "done": True
#             })

#         # Get final state
#         final = st.session_state.graph.invoke(initial_state)
#         st.session_state.report = {
#             "draft":    final["draft"],
#             "facts":    final["synthesized_facts"],
#             "revision": final["revision"],
#             "grade":    final["grade"],
#             "query":    query.strip()
#         }
#         st.session_state.status  = ("Done", False)
#         st.session_state.running = False

#     except Exception as e:
#         st.session_state.log_lines.append({
#             "time": ts(), "agent": "error", "msg": str(e), "done": False
#         })
#         st.session_state.status  = ("Error", False)
#         st.session_state.running = False

#     st.rerun()