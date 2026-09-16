from datetime import datetime, timezone
from uuid import uuid4

from app.agents.base import AgentContext, AgentResult
from app.agents.demo_agents import AGENTS
from app.agents.gateway import AgentGateway
from app.core.config import load_yaml
from app.core.persistence import utc_now


class InMemoryStore:
    def __init__(self):
        self.projects: dict[str, dict] = {}
        self.runs: dict[str, dict] = {}
        self.workflows: dict[str, dict] = {}

    def create_project(self, project): self.projects[project["id"]] = project; return project
    def save_workflow(self, workflow): self.workflows[workflow["id"]] = workflow; return workflow
    def save_run(self, run): self.runs[run["id"]] = run; return run
    def update_run(self, run): self.runs[run["id"]] = run; return run
    def get_project(self, project_id): return self.projects.get(project_id)
    def get_run(self, run_id): return self.runs.get(run_id)
    def list_projects(self): return list(self.projects.values())
    def list_workflows(self): return list(self.workflows.values())
    def list_runs(self, project_id=None): return list(self.runs.values())


class Orchestrator:
    def __init__(self, store: InMemoryStore, gateway: AgentGateway | None = None):
        self.store = store
        self.gateway = gateway or AgentGateway()
        self.functions = load_yaml("functions.yaml").get("functions", {})
        self.catalog = load_yaml("agents.yaml").get("agents", {})

    def create_project(self, payload: dict) -> dict:
        project = {
            "id": str(uuid4()),
            "name": payload["name"],
            "description": payload.get("description", ""),
            "stack": payload.get("stack", "python-fastapi"),
            "architecture": payload.get("architecture", "clean-architecture"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return self.store.create_project(project)

    async def execute(self, project: dict, payload: dict) -> dict:
        run_id = payload.get("_run_id") or str(uuid4())
        function_name = payload.get("function_name")
        configured = self.functions.get(function_name or "", {})
        workflow_agents = payload.get("agent_names") or []
        agent_names = workflow_agents or configured.get("agents") or [
            "agente_requisitos",
            "agente_system_design",
            "agente_backend",
            "agente_testes_unitarios",
            "agente_security_review",
            "agente_revisor_final",
        ]

        context = AgentContext(
            project_name=project["name"],
            goal=payload["goal"],
            function_name=function_name,
            error=payload.get("error"),
        )
        results: list[AgentResult] = []
        unknown_agents = []

        # A workflow without explicit edges retains the legacy sequential order.
        # With edges, execute ready DAG levels concurrently and reject cycles.
        workflow = payload.get("workflow") or {}
        edges = workflow.get("edges", [])
        for node in workflow.get("nodes", []):
            if node.get("agent") == "agente_pentest" and node.get("scope") not in {"homologação autorizada", "produção com aprovação"}:
                raise ValueError("Pentest bloqueado: informe um escopo autorizado de homologação ou produção com aprovação")
        if edges:
            predecessors = {name: set() for name in agent_names}
            for edge in edges:
                source = edge.get("from") or edge.get("source")
                target = edge.get("to") or edge.get("target")
                nodes = {n.get("id"): n.get("agent") for n in workflow.get("nodes", [])}
                source, target = nodes.get(source, source), nodes.get(target, target)
                if target in predecessors and source in predecessors: predecessors[target].add(source)
            pending = set(agent_names)
            while pending:
                ready = [name for name in pending if not (predecessors[name] & pending)]
                if not ready: raise ValueError("Workflow inválido: ciclo detectado no DAG")
                batch = []
                for agent_name in ready:
                    agent = AGENTS.get(agent_name)
                    if agent: batch.append(self.gateway.run(agent_name, context, agent))
                    else: unknown_agents.append(agent_name)
                results.extend(await __import__("asyncio").gather(*batch))
                pending -= set(ready)
        else:
            for agent_name in agent_names:
                agent = AGENTS.get(agent_name)
                if agent: results.append(await self.gateway.run(agent_name, context, agent))
                else: unknown_agents.append(agent_name)

        test_results = {
            "unit": "planned",
            "integration": "planned",
            "load": "planned",
            "concurrency": "planned",
            "security": "planned",
        }
        run = {
            "id": run_id,
            "project_id": project["id"],
            "status": "awaiting_approval",
            "repair_branch": f"autorepair/{run_id[:8]}",
            "function_name": function_name,
            "goal": payload["goal"],
            "error": payload.get("error"),
            "agents": [result.__dict__ for result in results],
            "unknown_agents": unknown_agents,
            "tests": test_results,
            "next_action": "Revisar diff e aprovar Pull Request antes do deploy.",
            "created_at": utc_now(),
            "workflow": payload.get("workflow", {}),
        }
        return self.store.update_run(run) if payload.get("_run_id") else self.store.save_run(run)
