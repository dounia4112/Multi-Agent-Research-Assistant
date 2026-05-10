import streamlit as st
import requests
import json

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 Multi-Agent Research Assistant")

query = st.text_input(
    "Enter your research question",
    placeholder="e.g. What is the impact of LLMs on software engineering jobs in 2025?"
)

run = st.button("Research", type="primary", disabled=not query)

if run and query:

    # ── Layout ───────────────────────────────────────────
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Agent Progress")
        status = {
            "planner":     st.empty(),
            "web_searcher": st.empty(),
            "synthesizer": st.empty(),
            "writer":      st.empty(),
            "grader":      st.empty(),
        }
        # Set all to waiting
        for name, slot in status.items():
            slot.markdown(f"⬜ **{name.replace('_', ' ').title()}** — waiting")

        facts_box  = st.empty()

    with col2:
        st.subheader("Research Report")
        report_box = st.empty()
        report_box.info("Report will appear here once complete...")

    # ── Stream ───────────────────────────────────────────
    agent_icons = {
        "planner":      "🗂️",
        "web_searcher": "🌐",
        "synthesizer":  "🔗",
        "writer":       "✍️",
        "grader":       "✅",
    }

    try:
        with requests.post(
            f"{API_URL}/research/stream",
            json={"query": query},
            stream=True,
            timeout=300
        ) as response:

            for line in response.iter_lines():
                if not line:
                    continue

                # Strip "data: " prefix
                if line.startswith(b"data: "):
                    raw = line[6:]
                else:
                    continue

                data = json.loads(raw)
                agent = data.get("agent")
                message = data.get("message", "")
                payload = data.get("payload", [])

                # Update agent status card
                if agent in status:
                    icon = agent_icons.get(agent, "🔄")
                    status[agent].markdown(
                        f"{icon} **{agent.replace('_', ' ').title()}** — {message}"
                    )

                # Show facts when synthesizer finishes
                if agent == "synthesizer" and payload:
                    with facts_box.container():
                        st.markdown("**Extracted Facts**")
                        for fact in payload:
                            st.markdown(f"- {fact}")

                # Stream is done — fetch full report
                if agent == "done":
                    final = requests.post(
                        f"{API_URL}/research",
                        json={"query": query}
                    ).json()

                    report_box.markdown(final["draft"])

                    st.success(
                        f"✅ Done — {len(final['facts'])} facts · "
                        f"{final['revision']} revision(s) · "
                        f"Grade: {final['grade']}"
                    )

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the FastAPI server is running: uvicorn main:app --reload")
    except Exception as e:
        st.error(f"Something went wrong: {e}")