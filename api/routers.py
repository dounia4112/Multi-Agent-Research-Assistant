import os, json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from graph import build_graph
from models.query_class import QueryRequest
from database.db import save_run
from dotenv import load_dotenv

load_dotenv(override=True)


router = APIRouter()

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


@router.get('/')
def root():
    return {"status": "running", "message": "Multi-Agent Research Assistant API"}



@router.post('/research')
async def research(request : QueryRequest):
    state = {"query": request, **initial_state_template}
    result = graph.invoke(state)

    save_run(
        query    = request.query.strip(),
        report   = result["draft"],
        facts    = result["synthesized_facts"],
        grade    = result["grade"],
        revision = result["revision"]
    )

    return {
        "query":    request.query,
        "draft":    result["draft"],
        "facts":    result["synthesized_facts"],
        "revision": result["revision"],
        "grade":    result["grade"]
    }



@router.post("/research/stream", description = """Stream agent progress as Server-Sent Events.""")
async def research_stream(request: QueryRequest):
    state = {"query": request.query, **initial_state_template}

    async def event_stream():
        async for chunk in graph.astream(state):
            print('\n chunk', chunk)
            print('\n chunk.keys',chunk.keys())
            agent_name = list(chunk.keys())[0]
            agent_state = chunk[agent_name]
            # Build a meaningful message per agent
            if agent_name == "planner":
                data = {
                    "agent":   "planner",
                    "message": f"Created {len(agent_state.get('sub_tasks', []))} sub-tasks",
                    "payload": agent_state.get("sub_tasks", [])
                }
            elif agent_name == "web_searcher":
                data = {
                    "agent":   "web_searcher",
                    "message": f"Found {len(agent_state.get('search_results', []))} results so far",
                    "payload": []
                }
            elif agent_name == "synthesizer":
                data = {
                    "agent":   "synthesizer",
                    "message": f"Extracted {len(agent_state.get('synthesized_facts', []))} facts",
                    "payload": agent_state.get("synthesized_facts", [])
                }
            elif agent_name == "writer":
                data = {
                    "agent":   "writer",
                    "message": f"Draft revision {agent_state.get('revision', 1)} written",
                    "payload": []
                }
            elif agent_name == "grader":
                data = {
                    "agent":   "grader",
                    "message": f"Grade: {agent_state.get('grade', '')}",
                    "payload": agent_state.get("feedback", "")
                }
            else:
                data = {"agent": agent_name, "message": "", "payload": []}

            yield f"data: {json.dumps(data)}\n\n"

        # Final event with the complete report
        yield f"data: {json.dumps({'agent': 'done', 'message': 'Report complete', 'payload': []})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")