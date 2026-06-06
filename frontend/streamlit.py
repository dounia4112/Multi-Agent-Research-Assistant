# import os, sys
# current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_dir, '..'))
# sys.path.append(project_root)
# import streamlit as st

# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# from dotenv import load_dotenv
# load_dotenv(override=True)

# from graph import build_graph

# st.set_page_config(page_title="Multi-Agent Research Assistant", page_icon="🔬", layout="wide")
# st.title("🔬 Multi-Agent Research Assistant")

# graph = build_graph()

# query = st.text_input("Enter your research question",
#     placeholder="e.g. What is the impact of LLMs on software engineering jobs in 2025?")

# run = st.button("Research", type="primary", disabled=not query)

# if run and query:
#     col1, col2 = st.columns([1, 2])

#     with col1:
#         st.subheader("Agent Progress")
#         slots = {
#             "planner":      st.empty(),
#             "web_searcher": st.empty(),
#             "synthesizer":  st.empty(),
#             "writer":       st.empty(),
#             "grader":       st.empty(),
#         }
#         for name, slot in slots.items():
#             slot.markdown(f"⬜ **{name.replace('_', ' ').title()}** — waiting")
#         facts_box = st.empty()

#     with col2:
#         st.subheader("Research Report")
#         report_box = st.empty()
#         report_box.info("Report will appear here once complete...")

#     icons = {
#         "planner": "🗂️", "web_searcher": "🌐",
#         "synthesizer": "🔗", "writer": "✍️", "grader": "✅"
#     }

#     initial_state = {
#         "query": query,
#         "sub_tasks": [], "current_task_idx": 0,
#         "search_results": [], "raw_sources": [],
#         "synthesized_facts": [], "draft": "",
#         "revision": 0, "grade": "", "feedback": "",
#         "next_agent": "", "is_done": False
#     }

#     # Stream graph updates directly
#     for chunk in graph.stream(initial_state):
#         agent_name  = list(chunk.keys())[0]
#         agent_state = chunk[agent_name]

#         if agent_name in slots:
#             icon = icons.get(agent_name, "🔄")
#             label = agent_name.replace("_", " ").title()

#             if agent_name == "planner":
#                 msg = f"Created {len(agent_state.get('sub_tasks', []))} sub-tasks"
#             elif agent_name == "web_searcher":
#                 msg = f"Found {len(agent_state.get('search_results', []))} results so far"
#             elif agent_name == "synthesizer":
#                 msg = f"Extracted {len(agent_state.get('synthesized_facts', []))} facts"
#                 facts = agent_state.get("synthesized_facts", [])
#                 if facts:
#                     with facts_box.container():
#                         st.markdown("**Extracted Facts**")
#                         for f in facts:
#                             st.markdown(f"- {f}")
#             elif agent_name == "writer":
#                 msg = f"Revision {agent_state.get('revision', 1)} written"
#             elif agent_name == "grader":
#                 msg = f"Grade: {agent_state.get('grade', '')}"
#             else:
#                 msg = "done"

#             slots[agent_name].markdown(f"{icon} **{label}** — {msg}")

#     # Show final report
#     final_state = graph.invoke(initial_state)
#     report_box.markdown(final_state["draft"])
#     st.success(f"✅ Done — {len(final_state['synthesized_facts'])} facts · "
#             f"{final_state['revision']} revision(s) · Grade: {final_state['grade']}")


import streamlit as st
import os, sys
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv(override=True)
from graph import build_graph

st.set_page_config(page_title="Research Assistant", layout="wide", page_icon="🔬")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {
  --bg:#0a0a08; --surface:#111110; --border:#1e1e1c; --border2:#5b5b51;
  --text:#e8e6e0; --muted:#9a9787; --accent:#c8b87a; --accent2:#7a9e8a;
  --mono:'JetBrains Mono',monospace; --serif:'Playfair Display',Georgia,serif; --sans:'DM Sans',sans-serif;
}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="block-container"]{
  background:var(--bg) !important; color:var(--text) !important;
  font-family:var(--sans) !important; padding:0 !important; max-width:100% !important;
}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
footer,#MainMenu,[data-testid="stStatusWidget"],[data-testid="collapsedControl"],
[data-testid="stSidebar"] { display:none !important; }

section[data-testid="stMain"] > div { padding: 0 !important; }
div[data-testid="stVerticalBlock"] { gap: 0 !important; }

/* Header */
.ra-header {
  border-bottom:1px solid var(--border); padding:0 32px;
  display:flex; align-items:center; justify-content:space-between;
  height:56px; background:var(--bg);
}
.ra-logo { font-family:var(--serif); font-size:1.1rem; color:var(--text); display:flex; align-items:center; gap:10px; }
.ra-dot { width:6px; height:6px; border-radius:50%; background:var(--accent); box-shadow:0 0 8px var(--accent); animation:breathe 3s ease-in-out infinite; }
@keyframes breathe { 0%,100%{opacity:1;box-shadow:0 0 8px var(--accent)} 50%{opacity:.5;box-shadow:0 0 3px var(--accent)} }
.ra-meta { font-family:var(--mono); font-size:0.62rem; color:var(--muted); letter-spacing:.08em; text-transform:uppercase; display:flex; align-items:center; gap:16px; }
.pill { display:flex; align-items:center; gap:6px; padding:3px 10px; border:1px solid var(--border2); border-radius:20px; font-size:0.6rem; color:var(--muted); }
.pill.on { border-color:var(--accent2); color:var(--accent2); }
.pdot { width:5px; height:5px; border-radius:50%; background:var(--border2); }
.pill.on .pdot { background:var(--accent2); box-shadow:0 0 6px var(--accent2); }

/* Sidebar column styling */
[data-testid="stColumn"]:first-child {
  border-right: 1px solid var(--border) !important;
  padding: 24px 8px !important;
  min-height: calc(100vh - 56px);
}
[data-testid="stColumn"]:last-child {
  padding: 0 !important;
}

/* Agent item */
.agent-item {
  display:flex; align-items:center; gap:10px;
  padding:8px 10px; border-radius:6px; border:1px solid transparent;
  position:relative; overflow:hidden; margin-bottom:4px;
}
.agent-item::before { content:''; position:absolute; left:0; top:0; bottom:0; width:2px; background:var(--accent); transform:scaleY(0); transition:transform .3s ease; transform-origin:bottom; }
.agent-item.idle { opacity:.4; }
.agent-item.running { background:rgba(200,184,122,.04); border-color:rgba(200,184,122,.15); }
.agent-item.running::before { transform:scaleY(1); }
.agent-item.done { background:rgba(122,158,138,.05); border-color:rgba(122,158,138,.15); }
.agent-item.done::before { background:var(--accent2); transform:scaleY(1); }
.aidx { font-family:var(--mono); font-size:.58rem; color:var(--muted); width:14px; text-align:center; flex-shrink:0; }
.ainfo { flex:1; min-width:0; }
.aname { font-size:.75rem; font-weight:500; letter-spacing:.02em; }
.idle .aname { color:var(--muted); }
.running .aname { color:var(--accent); }
.done .aname { color:var(--accent2); }
.asub { font-family:var(--mono); font-size:.58rem; color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-top:1px; }
.spinner { width:10px; height:10px; border:1.5px solid rgba(200,184,122,.2); border-top-color:var(--accent); border-radius:50%; animation:spin .8s linear infinite; flex-shrink:0; }
@keyframes spin { to{transform:rotate(360deg)} }
.acheck { font-size:.65rem; color:var(--accent2); flex-shrink:0; }

/* Progress */
.prog-wrap { margin-bottom:20px; padding:0 10px; }
.prog-track { height:1px; background:var(--border); border-radius:1px; overflow:hidden; margin-bottom:6px; }
.prog-fill { height:100%; background:linear-gradient(90deg,var(--accent),var(--accent2)); border-radius:1px; transition:width .6s ease; }
.prog-lbl { display:flex; justify-content:space-between; font-family:var(--mono); font-size:.58rem; color:var(--muted); }

/* Section label */
.slabel { font-family:var(--mono); font-size:.58rem; letter-spacing:.12em; text-transform:uppercase; color:var(--muted); margin-bottom:12px; padding:0 10px; }

/* Facts */
.fact-item { display:flex; gap:8px; font-size:.7rem; color:var(--muted); line-height:1.5; margin-bottom:6px; padding:0 10px; }
.fnum { font-family:var(--mono); font-size:.58rem; color:var(--border2); flex-shrink:0; margin-top:2px; }

/* Input area */
.input-area { padding:28px 36px 24px; border-bottom:1px solid var(--border); }
.qlabel { font-family:var(--mono); font-size:.6rem; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); margin-bottom:10px; }
.qwrap { display:flex; align-items:center; border:1px solid var(--border2); border-radius:8px; background:var(--surface); padding:0 0 0 8px; }
.qprompt { font-family:var(--mono); font-size:.7rem; color:var(--accent); padding:0 8px; flex-shrink:0; }

div[data-testid="stTextArea"] textarea {
  background:var(--surface) !important; border:none !important;
  color:var(--text) !important; font-family:var(--sans) !important;
  font-size:.9rem !important; font-weight:300 !important;
  outline:none !important; box-shadow:none !important; resize:none !important;
}
div[data-testid="stTextArea"] > div { background:transparent !important; border:none !important; box-shadow:none !important; }

div[data-testid="stButton"] button {
  background:var(--accent) !important; color:var(--bg) !important;
  border:none !important; border-radius:5px !important;
  font-family:var(--mono) !important; font-size:.65rem !important;
  font-weight:500 !important; letter-spacing:.08em !important;
  text-transform:uppercase !important; width:100% !important;
}
div[data-testid="stButton"] button:hover { background:#d4c98a !important; }

/* Output */
.output { padding:32px 36px; min-height:400px; }
.empty { display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:320px; gap:16px; text-align:center; opacity:.4; }
.empty-glyph { font-family:var(--serif); font-size:4rem; font-style:italic; color:var(--muted); }
.empty-title { font-family:var(--serif); font-size:1.1rem; color:var(--muted); }
.empty-sub { font-size:.75rem; color:var(--muted); max-width:280px; line-height:1.7; }

/* Log */
.logwrap { font-family:var(--mono); font-size:.65rem; color:var(--muted); line-height:2; }
.logline { display:flex; gap:12px; }
.ltime { color:var(--border2); flex-shrink:0; }
.lagent { color:var(--accent); width:100px; flex-shrink:0; }
.lagent.done { color:var(--accent2); }
.lmsg { color:var(--muted); }

/* Report */
.rmeta { display:flex; gap:16px; margin-bottom:28px; padding-bottom:16px; border-bottom:1px solid var(--border); flex-wrap:wrap; }
.rmeta-item { font-family:var(--mono); font-size:.6rem; color:var(--muted); letter-spacing:.06em; text-transform:uppercase; display:flex; gap:6px; }
.rmeta-val { color:var(--accent2); font-weight:500; }
.rbody h2 { font-family:var(--serif); font-size:1.1rem; font-weight:600; color:var(--text); margin:28px 0 10px; padding-bottom:6px; border-bottom:1px solid var(--border); }
.rbody p { font-size:.875rem; color:#c0bdb6; line-height:1.85; margin-bottom:12px; font-weight:300; }
.rbody ul { list-style:none; margin:0 0 12px; padding:0; }
.rbody li { font-size:.875rem; color:#c0bdb6; line-height:1.75; margin-bottom:6px; font-weight:300; }
.rbody li::before { content:'—'; color:var(--accent); margin-right:10px; font-family:var(--mono); font-size:.7rem; }

@keyframes fadeSlide { from{opacity:0;transform:translateX(-6px)} to{opacity:1;transform:none} }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────
def init():
    defaults = {
        "graph":         None,
        "agent_states":  {},
        "log_lines":     [],
        "facts":         [],
        "report":        None,
        "running":       False,
        "status":        ("Idle", False),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if st.session_state.graph is None:
        st.session_state.graph = build_graph()

init()

AGENTS = [
    {"key":"planner",      "label":"Planner",      "sub":"Query decomposition"},
    {"key":"web_searcher", "label":"Web Searcher",  "sub":"Tavily search"},
    {"key":"synthesizer",  "label":"Synthesizer",   "sub":"Fact extraction"},
    {"key":"writer",       "label":"Writer",        "sub":"Report drafting"},
    {"key":"grader",       "label":"Grader",        "sub":"Quality review"},
]

def ts(): return datetime.now().strftime("%H:%M:%S")

def agent_html(a, state, msg):
    idx  = str(AGENTS.index(a)+1).zfill(2)
    spin = '<div class="spinner"></div>' if state == "running" else ""
    chk  = '<div class="acheck">✓</div>' if state == "done"    else ""
    return f"""<div class="agent-item {state}">
      <span class="aidx">{idx}</span>
      <div class="ainfo">
        <div class="aname">{a['label']}</div>
        <div class="asub">{msg or a['sub']}</div>
      </div>{spin}{chk}
    </div>"""

def report_body_html(draft):
    html = ""
    for line in draft.split("\n"):
        if   line.startswith("## "): html += f"<h2>{line[3:]}</h2>"
        elif line.startswith("# "):  html += f"<h2>{line[2:]}</h2>"
        elif line.startswith(("* ","- ")): html += f"<ul><li>{line[2:]}</li></ul>"
        elif line.strip(): html += f"<p>{line}</p>"
    return html

# ── Header ────────────────────────────────────────────────
stxt, son = st.session_state.status
st.markdown(f"""
<div class="ra-header">
  <div class="ra-logo"><div class="ra-dot"></div>Research Assistant</div>
  <div class="ra-meta">
    <span>LangGraph · Groq · Tavily</span>
    <div class="pill {'on' if son else ''}">
      <div class="pdot"></div><span>{stxt}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Two-column layout via st.columns ─────────────────────
sidebar_col, main_col = st.columns([1, 3])

# ── Sidebar ───────────────────────────────────────────────
with sidebar_col:
    has_activity = bool(st.session_state.agent_states)
    done_count   = sum(1 for a in AGENTS if st.session_state.agent_states.get(a["key"]) == "done")

    if has_activity:
        pct = round(done_count / len(AGENTS) * 100)
        st.markdown(f"""
        <div class="prog-wrap">
          <div class="prog-track"><div class="prog-fill" style="width:{pct}%"></div></div>
          <div class="prog-lbl"><span>Pipeline</span><span>{pct}%</span></div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="slabel">Agents</div>', unsafe_allow_html=True)
    agents_html = ""
    for a in AGENTS:
        state = st.session_state.agent_states.get(a["key"], "idle")
        msg   = st.session_state.agent_states.get(f"{a['key']}_msg", "")
        agents_html += agent_html(a, state, msg)
    st.markdown(agents_html, unsafe_allow_html=True)

    if st.session_state.facts:
        st.markdown('<br><div class="slabel">Extracted facts</div>', unsafe_allow_html=True)
        facts_html = ""
        for i, f in enumerate(st.session_state.facts):
            facts_html += f'<div class="fact-item"><span class="fnum">{str(i+1).zfill(2)}</span><span>{f}</span></div>'
        st.markdown(facts_html, unsafe_allow_html=True)

# ── Main ──────────────────────────────────────────────────
with main_col:
    # Input
    st.markdown('<div class="input-area"><div class="qlabel">Research query</div>', unsafe_allow_html=True)

    inp_col, btn_col = st.columns([9, 1])
    with inp_col:
        query = st.text_area(
            label="q", label_visibility="collapsed",
            placeholder="What do you want to research? e.g. Impact of LLMs on software engineering jobs in 2025",
            height=80, key="query_input"
        )
    with btn_col:
        st.markdown("<div style='padding-top:20px'></div>", unsafe_allow_html=True)
        run = st.button("Run ⏎", disabled=st.session_state.running)

    st.markdown("</div>", unsafe_allow_html=True)

    # Output
    st.markdown('<div class="output">', unsafe_allow_html=True)

    if st.session_state.report:
        r = st.session_state.report
        st.markdown(f"""
        <div class="rmeta">
          <div class="rmeta-item">Facts <span class="rmeta-val">{len(r['facts'])}</span></div>
          <div class="rmeta-item">Revisions <span class="rmeta-val">{r['revision']}</span></div>
          <div class="rmeta-item">Grade <span class="rmeta-val">{r['grade']}</span></div>
          <div class="rmeta-item">Query <span class="rmeta-val" style="font-style:italic;text-transform:none;letter-spacing:0">{r['query']}</span></div>
        </div>
        <div class="rbody">{report_body_html(r['draft'])}</div>
        """, unsafe_allow_html=True)
        st.download_button("⎘ Download report", data=r["draft"], file_name="report.md", mime="text/markdown")

    elif has_activity:
        log_html = '<div class="logwrap">'
        for l in st.session_state.log_lines:
            cls = "done" if l["done"] else ""
            log_html += f'<div class="logline"><span class="ltime">{l["time"]}</span><span class="lagent {cls}">[{l["agent"]}]</span><span class="lmsg">{l["msg"]}</span></div>'
        log_html += "</div>"
        st.markdown(log_html, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="empty">
          <div class="empty-glyph">∂</div>
          <div class="empty-title">Nothing yet</div>
          <div class="empty-sub">Enter a research question above and the agents will get to work.</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── Run ───────────────────────────────────────────────────
if run and query.strip():
    st.session_state.agent_states = {}
    st.session_state.log_lines    = []
    st.session_state.facts        = []
    st.session_state.report       = None
    st.session_state.running      = True
    st.session_state.status       = ("Running", True)

    initial_state = {
        "query": query.strip(),
        "sub_tasks":[], "current_task_idx":0,
        "search_results":[], "raw_sources":[],
        "synthesized_facts":[], "draft":"",
        "revision":0, "grade":"", "feedback":"",
        "next_agent":"", "is_done":False
    }

    st.session_state.log_lines.append({"time":ts(),"agent":"system","msg":f'Research started — "{query.strip()}"',"done":False})

    try:
        for chunk in st.session_state.graph.stream(initial_state):
            agent_name  = list(chunk.keys())[0]
            agent_state = chunk[agent_name]

            if   agent_name == "planner":      msg = f"Created {len(agent_state.get('sub_tasks',[]))} sub-tasks"
            elif agent_name == "web_searcher": msg = f"Found {len(agent_state.get('search_results',[]))} results so far"
            elif agent_name == "synthesizer":
                msg = f"Extracted {len(agent_state.get('synthesized_facts',[]))} facts"
                st.session_state.facts = agent_state.get("synthesized_facts", [])
            elif agent_name == "writer":  msg = f"Draft revision {agent_state.get('revision',1)} written"
            elif agent_name == "grader":  msg = f"Grade: {agent_state.get('grade','')}"
            else: msg = ""

            idx = next((i for i,a in enumerate(AGENTS) if a["key"]==agent_name), None)
            if idx is not None:
                st.session_state.agent_states[agent_name]          = "done"
                st.session_state.agent_states[f"{agent_name}_msg"] = msg
                if idx+1 < len(AGENTS):
                    nk = AGENTS[idx+1]["key"]
                    if st.session_state.agent_states.get(nk) != "done":
                        st.session_state.agent_states[nk] = "running"

            st.session_state.log_lines.append({"time":ts(),"agent":agent_name,"msg":msg,"done":True})

        final = st.session_state.graph.invoke(initial_state)
        st.session_state.report  = {"draft":final["draft"],"facts":final["synthesized_facts"],"revision":final["revision"],"grade":final["grade"],"query":query.strip()}
        st.session_state.status  = ("Done", False)
        st.session_state.running = False

    except Exception as e:
        st.session_state.log_lines.append({"time":ts(),"agent":"error","msg":str(e),"done":False})
        st.session_state.status  = ("Error", False)
        st.session_state.running = False

    st.rerun()