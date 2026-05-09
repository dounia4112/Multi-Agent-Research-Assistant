import os, json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from graph import build_graph
from models.query_class import QueryRequest
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI("Multi-Agent Research Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"]
)

graph = build_graph()

initial_state_template = {
    "sub_tasks": [], 
    "current_task_idx": 0,
    "search_results": [], 
    "raw_sources": [],
    "synthesized_facts": [], 
    "draft": "",
    "revision": 0, 
    "grade": "", 
    "feedback": "",
    "next_agent": "", 
    "is_done": False
}


@app.get('/')
def root():
    return {"status": "running", "message": "Multi-Agent Research Assistant API"}



@app.post('/research')
async def research(request : QueryRequest):
    state = {"query": request, **initial_state_template}
    result = graph.invoke(state)

    return {
        "query":    request.query,
        "draft":    result["draft"],
        "facts":    result["synthesized_facts"],
        "revision": result["revision"],
        "grade":    result["grade"]
    }



@app.post("/research/stream", decription = """Stream agent progress as Server-Sent Events.""")
async def research_stream(request: QueryRequest):
    state = {"query": request.query, **initial_state_template}