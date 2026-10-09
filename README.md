# 🔬 Multi-Agent Research Assistant

---

## 📸 Live Demo

| Version | Link | Hosting |
|---|---|---|
| 🌐 **Web app** (custom UI + live agent progress) | [dounia4112.github.io/Multi-Agent-Research-Assistant](https://dounia4112.github.io/Multi-Agent-Research-Assistant/) | GitHub Pages → API on Render |
| ⚡ **Web app + REST API** | [multi-agent-research-assistant-7biy.onrender.com](https://multi-agent-research-assistant-7biy.onrender.com/) · [API docs](https://multi-agent-research-assistant-7biy.onrender.com/docs) | Render |
| 📊 **Streamlit version** | [Open the Streamlit app](https://multi-agent-research-assistant-bnmn7379dpzcaq8fdi5d3q.streamlit.app/) | Streamlit Community Cloud |

Every report is stored with its creation date in a Postgres database hosted on [Neon](https://neon.tech).

> Hosted on free tiers: the first request after a period of inactivity can take up to a minute while the server wakes up.


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
git clone https://github.com/dounia4112/Multi-Agent-Research-Assistant.git
cd Multi-Agent-Research-Assistant
pip install -r requirements.txt
```

### 2. Add your API keys

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | ✅ | LLM calls ([console.groq.com](https://console.groq.com)) |
| `TAVILY_API_KEY` | ✅ | Web search ([tavily.com](https://tavily.com)) |
| `DATABASE_URL` | optional | Postgres URL to keep a history of reports (query, report, facts, grade and creation date); the table is created automatically. A `localhost` URL only works on your own machine — deployed apps need a hosted database |
| `GROQ_FAST_MODEL` / `GROQ_SMART_MODEL` | optional | Override the Groq models (defaults: `openai/gpt-oss-20b` / `openai/gpt-oss-120b`) |
| `ALLOWED_ORIGINS` | optional | Sites allowed to call the API from another domain (comma-separated). Defaults to `https://dounia4112.github.io` |
| `RATE_LIMIT_RUNS` / `RATE_LIMIT_WINDOW_SECONDS` | optional | Per-visitor rate limit (default 5 runs / 10 min) |

### 3. Run

**Web app (FastAPI + custom UI):**
```bash
uvicorn main:app --reload
```
Interface at `http://127.0.0.1:8000` · Interactive API docs at `http://127.0.0.1:8000/docs`

**Streamlit:**
```bash
streamlit run frontend/streamlit.py
```

### 4. Test

The tests replace Groq and Tavily with fakes, so they need no API keys:
```bash
pip install -r requirements-dev.txt
pytest
```

---

## 🔌 API

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Web interface |
| `POST` | `/research` | Run the pipeline, return the final report as JSON |
| `POST` | `/research/stream` | Server-Sent Events: one event per agent step; the final `done` event carries the report |
| `GET` | `/history` | Last 20 saved reports with their dates (when `DATABASE_URL` is set) |
| `GET` | `/history/{id}` | One saved report, with its creation date |
| `GET` | `/health` | Health check, including whether the database is reachable |

---

## ☁️ Deployment

**Web app on Render** — `render.yaml` is a ready-made blueprint:
1. On Render, choose **New → Blueprint** and select this repository.
2. Set `GROQ_API_KEY`, `TAVILY_API_KEY` and (optionally) `DATABASE_URL` when prompted. A free Postgres from [Neon](https://neon.tech) or [Supabase](https://supabase.com) works.
3. Render runs `uvicorn main:app --host 0.0.0.0 --port $PORT`; the API serves the web page itself, so there is nothing else to deploy.
   If you create the service manually instead of from the blueprint, use exactly this start command: the port must be `$PORT`, the variable Render provides.

**Web page on GitHub Pages** (optional) — in the repository's **Settings → Pages**, deploy from the `main` branch root. When opened from `*.github.io`, `index.html` calls the Render API automatically; that site's origin must be listed in `ALLOWED_ORIGINS` (the default already allows `https://dounia4112.github.io`).

**Streamlit Community Cloud:**
1. New app → this repository → main file `frontend/streamlit.py`.
2. Under **Advanced settings → Secrets**, add the same keys:
   ```toml
   GROQ_API_KEY = "..."
   TAVILY_API_KEY = "..."
   DATABASE_URL = "..."   # optional
   ```
