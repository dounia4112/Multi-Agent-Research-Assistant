# 🔬 Multi-Agent Research Assistant

---

## 📸 Sreamlit Demo

![Demo GIF](assets/demo.gif)

🔗 **Try it live:** https://multi-agent-research-assistant-bnmn7379dpzcaq8fdi5d3q.streamlit.app/


---

## 🧠 How It Works

The system uses a **LangGraph StateGraph** where 5 specialist agents share a common state object and are orchestrated by a supervisor router. No agent calls another directly, they all read from and write to the shared state, and the supervisor decides who acts next.

---

## 💡 What It Does

You type a research question. The system automatically:

1. **Plans** — breaks your question into focused search tasks
2. **Searches** — retrieves real, up-to-date web results for each task
3. **Synthesizes** — extracts and deduplicates the key facts
4. **Writes** — drafts a structured report with an executive summary, findings, and analysis
5. **Grades** — checks quality and revises if needed

The whole process takes under a minute and produces a clean Markdown report you can copy or export.

---

## 🧠 Architecture

The system is built around a **LangGraph agent graph**, 5 specialist agents share a common state and are orchestrated by a supervisor that decides who acts next. Agents never call each other directly; they only read from and write to the shared state.

```
                   ┌──────────────────────┐
                   │   Supervisor router   │
                   └──────────┬───────────┘
                              │ decides who runs next
       ┌──────────┬───────────┼───────────┬──────────┐
       ▼          ▼           ▼           ▼          ▼
   Planner   Web Searcher  Synthesizer  Writer    Grader
  (plan tasks) (search web) (merge facts)(write)   (QA)
                                                    │
                                        ┌───────────┘
                                        │ needs revision?
                                        ▼
                                     Writer  (revision)
                                        │
                                        ▼
                                  Final Report
```

| Agent | What it does |
|---|---|
| **Planner** | Breaks the query into 3–5 focused search sub-tasks |
| **Web Searcher** | Runs a real web search for each sub-task via Tavily |
| **Synthesizer** | Extracts unique factual claims from all search results |
| **Writer** | Drafts a structured Markdown report from the facts |
| **Grader** | Reviews the draft, approves it or sends it back for revision |

The two frontends connect to this pipeline differently:

- **Streamlit** calls the graph directly in Python, streams agent updates live. Used for the hosted demo on Streamlit Share.
- **FastAPI** exposes the same pipeline as a REST API with a `/research/stream` SSE endpoint, useful if you want to integrate the pipeline into another app or frontend.

---

## 🚀 Getting Started

### 1. Clone and install

```bash
git clone https://github.com/dounia4112/multi-agent-researcher.git
cd multi-agent-researcher
pip install -r requirements.txt
```

### 2. Add your API keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here
```

### 3. Run

**Streamlit (recommended):**
```bash
streamlit run frontend.py
```

**FastAPI (optional):**
```bash
uvicorn main:app --reload
```
Interface at `http://127.0.0.1:8000` · Interactive docs at `http://127.0.0.1:8000/docs`

---

