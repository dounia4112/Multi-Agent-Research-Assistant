# 🔬 Multi-Agent Research Assistant

> An autonomous research pipeline powered by **LangGraph**, **Groq (Llama 3)**, and **Tavily Search** — 5 specialized AI agents collaborate to research any topic and produce a structured, cited report.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-ff4b4b?style=flat&logo=streamlit)](https://YOUR-APP-NAME.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-1C3C3C?style=flat)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

---

## 📸 Demo

![Demo GIF](assets/demo.gif)

> **Live demo:** [https://YOUR-APP-NAME.streamlit.app](https://YOUR-APP-NAME.streamlit.app)

---

## 🧠 How It Works

The system uses a **LangGraph StateGraph** where 5 specialist agents share a common state object and are orchestrated by a supervisor router. No agent calls another directly — they all read from and write to the shared state, and the supervisor decides who acts next.

```
User Query
    │
    ▼
┌─────────────┐
│  Supervisor  │  ◄─────────────────────────────┐
│   (router)   │                                 │
└──────┬──────┘                                 │
       │                                         │
   ┌───▼────┐   ┌────────────┐   ┌────────────┐ │
   │Planner │──►│Web Searcher│──►│Synthesizer │ │
   │        │   │(per task)  │   │            │ │
   └────────┘   └────────────┘   └─────┬──────┘ │
                                        │        │
                                   ┌────▼───┐    │
                                   │ Writer │    │
                                   └────┬───┘    │
                                        │        │
                                   ┌────▼───┐    │
                                   │ Grader │────┘
                                   └────┬───┘  (needs revision?)
                                        │
                                   ┌────▼───┐
                                   │ Report │
                                   └────────┘
```

### Agent responsibilities

| Agent | Role | LLM used |
|---|---|---|
| **Planner** | Decomposes the query into 3–5 focused search sub-tasks | Groq Llama 3.3 70B |
| **Web Searcher** | Executes one Tavily search per sub-task, appends results to state | No LLM — API call only |
| **Synthesizer** | Extracts unique, factual claims from all search results | Groq Llama 3.3 70B |
| **Writer** | Drafts a structured Markdown report from synthesized facts | Groq Llama 3.1 8B |
| **Grader** | Quality-checks the draft; sends back for revision or approves | Groq Llama 3.3 70B |

### Shared state

Every agent reads from and writes to a single `ResearchState` TypedDict. LangGraph merges partial updates automatically — agents only return the keys they modified.

```python
class ResearchState(TypedDict):
    query: str
    sub_tasks: List[str]
    current_task_idx: int
    search_results: List[dict]
    synthesized_facts: List[str]
    draft: str
    revision: int
    grade: str          # "pass" | "needs_revision"
    feedback: str
    is_done: bool
```

---

## ⚡ Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/dounia4112/multi-agent-researcher.git
cd multi-agent-researcher
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up API keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

Get your free keys here:
- **Groq** (14,400 req/day free): [console.groq.com](https://console.groq.com)
- **Tavily** (1,000 searches/month free): [app.tavily.com](https://app.tavily.com)

### 4. Run the backend

```bash
uvicorn main:app --reload
```

API is now running at `http://127.0.0.1:8000`
Interactive docs at `http://127.0.0.1:8000/docs`

### 5. Run the frontend

```bash
streamlit run frontend.py
```
Open `http://localhost:8501`

---

## 🔌 API Reference

### `POST /research`

Runs the full pipeline and returns when complete.

**Request:**
```json
{ "query": "What is the impact of LLMs on software engineering jobs in 2025?" }
```

**Response:**
```json
{
  "query":    "What is the impact of LLMs...",
  "draft":    "## Executive Summary\n...",
  "facts":    ["LLMs caused 1.09M tech layoffs...", "..."],
  "revision": 1,
  "grade":    "pass"
}
```

---

### `POST /research/stream`

Streams agent progress as **Server-Sent Events (SSE)**. Each event fires when an agent finishes.

**Request:** same as above

**SSE events (one per agent):**
```
data: {"agent": "planner",      "message": "Created 4 sub-tasks",       "payload": ["task1", ...]}
data: {"agent": "web_searcher", "message": "Found 20 results so far",   "payload": []}
data: {"agent": "synthesizer",  "message": "Extracted 10 facts",        "payload": ["fact1", ...]}
data: {"agent": "writer",       "message": "Draft revision 1 written",  "payload": []}
data: {"agent": "grader",       "message": "Grade: pass",               "payload": ""}
data: {"agent": "done",         "message": "Report complete",           "payload": []}
```

**Consume in Python:**
```python
import requests, json

with requests.post(url, json={"query": q}, stream=True) as r:
    for line in r.iter_lines():
        if line.startswith(b"data: "):
            data = json.loads(line[6:])
            print(data["agent"], "→", data["message"])
```

---

## 📋 Requirements

```
langgraph>=0.2.0
langchain-groq>=0.1.0
langchain-core>=0.2.0
tavily-python>=0.3.0
fastapi>=0.111.0
uvicorn>=0.30.0
python-dotenv>=1.0.0
streamlit>=1.35.0
requests>=2.31.0
```

Install all at once:
```bash
pip install -r requirements.txt
```

## 👩‍💻 Author

**Dounia Toubal** — Data Analyst & AI Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Dounia%20Toubal-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/dounia-toubal)
[![GitHub](https://img.shields.io/badge/GitHub-dounia4112-181717?style=flat&logo=github)](https://github.com/dounia4112)
[![Portfolio](https://img.shields.io/badge/Portfolio-dounia4112.github.io-black?style=flat)](https://dounia4112.github.io/portfolio/)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
