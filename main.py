from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from graph import build_graph
import json

load_dotenv(override=True)

app = FastAPI(title="Multi-Agent Research Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Serve the frontend folder as static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

graph = build_graph()

class QueryRequest(BaseModel):
    query: str

initial_state_template = {
    "sub_tasks": [], "current_task_idx": 0,
    "search_results": [], "raw_sources": [],
    "synthesized_facts": [], "draft": "",
    "revision": 0, "grade": "", "feedback": "",
    "next_agent": "", "is_done": False
}

# Serve the HTML at root
@app.get("/", response_class=FileResponse)
def index():
    return FileResponse("index.html")

@app.post("/research")
async def research(request: QueryRequest):
    state = {"query": request.query, **initial_state_template}
    result = graph.invoke(state)
    return {
        "query":    request.query,
        "draft":    result["draft"],
        "facts":    result["synthesized_facts"],
        "revision": result["revision"],
        "grade":    result["grade"]
    }

@app.post("/research/stream")
async def research_stream(request: QueryRequest):
    from fastapi.responses import StreamingResponse
    state = {"query": request.query, **initial_state_template}

    async def event_stream():
        async for chunk in graph.astream(state):
            agent_name  = list(chunk.keys())[0]
            agent_state = chunk[agent_name]

            if agent_name == "planner":
                data = {"agent": "planner", "message": f"Created {len(agent_state.get('sub_tasks', []))} sub-tasks", "payload": agent_state.get("sub_tasks", [])}
            elif agent_name == "web_searcher":
                data = {"agent": "web_searcher", "message": f"Found {len(agent_state.get('search_results', []))} results so far", "payload": []}
            elif agent_name == "synthesizer":
                data = {"agent": "synthesizer", "message": f"Extracted {len(agent_state.get('synthesized_facts', []))} facts", "payload": agent_state.get("synthesized_facts", [])}
            elif agent_name == "writer":
                data = {"agent": "writer", "message": f"Draft revision {agent_state.get('revision', 1)} written", "payload": []}
            elif agent_name == "grader":
                data = {"agent": "grader", "message": f"Grade: {agent_state.get('grade', '')}", "payload": agent_state.get("feedback", "")}
            else:
                data = {"agent": agent_name, "message": "", "payload": []}

            yield f"data: {json.dumps(data)}\n\n"

        yield f"data: {json.dumps({'agent': 'done', 'message': 'Report complete', 'payload': []})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")