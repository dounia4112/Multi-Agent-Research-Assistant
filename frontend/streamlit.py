import os, sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)
import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(override=True)

from graph import build_graph

st.set_page_config(page_title="Multi-Agent Research Assistant", page_icon="🔬", layout="wide")
st.title("🔬 Multi-Agent Research Assistant")
st.caption("Powered by LangGraph · Groq · Tavily")

graph = build_graph()

query = st.text_input("Enter your research question",
    placeholder="e.g. What is the impact of LLMs on software engineering jobs in 2025?")

run = st.button("Research", type="primary", disabled=not query)

if run and query:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Agent Progress")
        slots = {
            "planner":      st.empty(),
            "web_searcher": st.empty(),
            "synthesizer":  st.empty(),
            "writer":       st.empty(),
            "grader":       st.empty(),
        }
        for name, slot in slots.items():
            slot.markdown(f"⬜ **{name.replace('_', ' ').title()}** — waiting")
        facts_box = st.empty()

    with col2:
        st.subheader("Research Report")
        report_box = st.empty()
        report_box.info("Report will appear here once complete...")

    icons = {
        "planner": "🗂️", "web_searcher": "🌐",
        "synthesizer": "🔗", "writer": "✍️", "grader": "✅"
    }

    initial_state = {
        "query": query,
        "sub_tasks": [], "current_task_idx": 0,
        "search_results": [], "raw_sources": [],
        "synthesized_facts": [], "draft": "",
        "revision": 0, "grade": "", "feedback": "",
        "next_agent": "", "is_done": False
    }

    # Stream graph updates directly
    for chunk in graph.stream(initial_state):
        agent_name  = list(chunk.keys())[0]
        agent_state = chunk[agent_name]

        if agent_name in slots:
            icon = icons.get(agent_name, "🔄")
            label = agent_name.replace("_", " ").title()

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

            slots[agent_name].markdown(f"{icon} **{label}** — {msg}")

    # Show final report
    final_state = graph.invoke(initial_state)
    report_box.markdown(final_state["draft"])
    st.success(f"✅ Done — {len(final_state['synthesized_facts'])} facts · "
            f"{final_state['revision']} revision(s) · Grade: {final_state['grade']}")