import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Permite executar também `python app/main.py` sem quebrar por falta de pacote.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.bootstrap import ensure_managed_runtime

ensure_managed_runtime()

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agents.demo_agents import AGENTS
from app.core.orchestrator import InMemoryStore, Orchestrator
from app.core.persistence import PersistentStore
from app.core.queue import RunQueue
import os


app = FastAPI(title="Jarvis Forge", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def optional_api_key(request: Request, call_next):
    expected = os.getenv("JARVIS_API_KEY")
    if expected and request.url.path.startswith("/api/") and request.headers.get("x-api-key") != expected:
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "API key inválida ou ausente"}, status_code=401)
    return await call_next(request)

store = PersistentStore()
orchestrator = Orchestrator(store)
run_queue = RunQueue()
DASHBOARD = Path(__file__).resolve().parents[2] / "dashboard" / "index.html"


class ProjectInput(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str = ""
    stack: str = "python-fastapi"
    architecture: str = "clean-architecture"


class RunInput(BaseModel):
    goal: str = Field(min_length=5)
    function_name: str | None = None
    error: str | None = None
    agent_names: list[str] = []
    workflow: dict = {}


class WorkflowInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    nodes: list[dict] = []
    edges: list[dict] = []


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(DASHBOARD)


@app.get("/health")
def health():
    return {"status": "ok", "service": "jarvis-forge"}


@app.get("/api/agents")
def list_agents():
    return [
        {"name": agent.name, "category": agent.category}
        for agent in AGENTS.values()
    ]


@app.get("/api/providers")
def providers():
    return {"provider": orchestrator.gateway.provider, "model": orchestrator.gateway.model or None, "live_enabled": orchestrator.gateway.enabled, "fallback": "demo"}


@app.get("/api/functions")
def list_functions():
    return orchestrator.functions


@app.get("/api/workflows")
def list_workflows():
    return store.list_workflows()


@app.post("/api/workflows")
def save_workflow(payload: WorkflowInput):
    from uuid import uuid4

    workflow = {"id": str(uuid4()), **payload.model_dump()}
    return store.save_workflow(workflow)


@app.post("/api/projects")
def create_project(payload: ProjectInput):
    return orchestrator.create_project(payload.model_dump())


@app.get("/api/projects")
def list_projects():
    return store.list_projects()


@app.post("/api/projects/{project_id}/runs")
async def create_run(project_id: str, payload: RunInput):
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    if run_queue.enabled:
        from uuid import uuid4
        run_id = str(uuid4())
        queued = {"id": run_id, "project_id": project_id, "status": "queued", "goal": payload.goal, "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "next_action": "Aguardando worker Redis", "workflow": payload.workflow}
        store.save_run(queued)
        await run_queue.enqueue({"run_id": run_id, "project": project, "payload": payload.model_dump()})
        return queued
    try:
        return await orchestrator.execute(project, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Execução não encontrada")
    return run


@app.get("/api/projects/{project_id}/runs")
def list_runs(project_id: str):
    return store.list_runs(project_id)


@app.get("/api/audit")
def audit_log():
    return store.list_audit()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
