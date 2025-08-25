# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import Optional
# from src.agents import get_agent_executor

# app = FastAPI(title="Insurance Chatbot Backend")

# # Store executors per session_id
# sessions = {}

# class QueryRequest(BaseModel):
#     session_id: str        # required for identifying the session
#     user_input: str
#     schema: Optional[str] = None  # still optional if you want
#     class Config:
#         populate_by_name = True  # allows using both "db_schema" and "schema"


# def get_or_create_executor(session_id: str):
#     if session_id not in sessions:
#         sessions[session_id] = get_agent_executor()
#     return sessions[session_id]


# @app.post("/chat")
# async def chat(request: QueryRequest):
#     executor = get_or_create_executor(request.session_id)
#     try:
#         inputs = {"input": request.user_input}
#         result = executor.invoke(inputs)

#         output = result.get("output") if isinstance(result, dict) else str(result)
#         return {"session_id": request.session_id, "result": output}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from src.agents import get_agent_executor
from src.config import set_db_uri
from src.database import reset_engine, clear_schema_cache
import os

app = FastAPI(title="Insurance Chatbot Backend")

# Enable CORS
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store executors per session
sessions = {}

class QueryRequest(BaseModel):
    session_id: str
    user_input: str
    schema: Optional[str] = None
    class Config:
        populate_by_name = True

class DBUpdateRequest(BaseModel):
    new_db_uri: str

def get_or_create_executor(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = get_agent_executor()
    return sessions[session_id]

# Static files / graph
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app.mount("/static", StaticFiles(directory=backend_root), name="static")
graph_path = os.path.join(backend_root, "graph.png")

# -----------------------
# Endpoints
# -----------------------
@app.post("/set-db-uri")
async def update_db_uri(request: DBUpdateRequest, session_id: Optional[str] = "user123"):
    if not request.new_db_uri:
        raise HTTPException(status_code=400, detail="No DB URI provided")

    # 1️⃣ Update DB URI
    set_db_uri(request.new_db_uri)

    # 2️⃣ Reset engine and schema cache
    reset_engine()
    clear_schema_cache()

    # 3️⃣ Reinitialize only the session specified (or all if None)
    if session_id:
        # Ensure session exists before clearing
        if session_id not in sessions:
            sessions[session_id] = get_agent_executor()
        else:
            sessions[session_id].memory.clear()
            sessions[session_id] = get_agent_executor()
    else:
        # optional: reinit all sessions
        for sid in list(sessions.keys()):
            sessions[sid] = get_agent_executor()

    return {"message": "DB_URI updated successfully", "DB_URI": request.new_db_uri}

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Incoming request: {request.method} {request.url}", flush=True)
    response = await call_next(request)
    return response


@app.get("/graph")
def get_graph():
    if os.path.exists(graph_path):
        return FileResponse(graph_path)
    raise HTTPException(status_code=404, detail="Graph not found")

@app.post("/chat")
async def chat(request: QueryRequest):
    executor = get_or_create_executor(request.session_id)
    try:
        # Normalize input
        user_input = " ".join(request.user_input.strip().split())
        inputs = {"input": user_input}

        result = executor.invoke(inputs)
        output = result.get("output") if isinstance(result, dict) else str(result)
        return {"session_id": request.session_id, "result": output}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
