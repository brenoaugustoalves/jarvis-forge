"""Run a Jarvis workflow locally through the authenticated Codex CLI.

This is intentionally separate from the Railway worker: the Codex session and
its ChatGPT/Codex plan limits remain on the user's computer.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_WORKFLOW = {
    "name": "Revisão local com Codex",
    "nodes": [
        {"id": "requirements", "agent": "agente_requisitos", "role": "Planejamento"},
    ],
    "edges": [],
}


def ordered_nodes(workflow: dict) -> list[dict]:
    nodes = workflow.get("nodes", [])
    by_id = {node.get("id"): node for node in nodes}
    dependencies = {node.get("id"): set() for node in nodes}
    for edge in workflow.get("edges", []):
        if edge.get("to") in dependencies and edge.get("from") in by_id:
            dependencies[edge["to"]].add(edge["from"])
    result, pending = [], set(by_id)
    while pending:
        ready = [node_id for node_id in pending if not dependencies[node_id] & pending]
        if not ready:
            raise ValueError("Workflow inválido: ciclo detectado")
        result.extend(by_id[node_id] for node_id in ready)
        pending -= set(ready)
    return result


def run_agent(node: dict, goal: str, workspace: Path, model: str | None, writable: bool) -> str:
    prompt = f"""Você é o agente {node.get('agent', 'agente de engenharia')} do Jarvis Forge.
Objetivo: {goal}
Papel: {node.get('role', 'engenharia de software')}
Prompt específico: {node.get('prompt', 'Analise o objetivo e produza uma recomendação técnica.')}
Ferramentas permitidas: {node.get('tools', 'leitura do projeto e análise')}
Responda em português, com resumo, descobertas, ações e riscos. Não faça deploy nem altere arquivos sem aprovação humana."""
    command = ["codex", "exec", "--ephemeral", "--color", "never", "--sandbox", "workspace-write" if writable else "read-only", "-C", str(workspace)]
    if model:
        command.extend(["--model", model])
    command.append(prompt)
    process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    if process.returncode:
        raise RuntimeError(process.stderr.strip() or f"Codex encerrou com código {process.returncode}")
    return process.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Executa o Jarvis Forge usando a cota local do Codex")
    parser.add_argument("goal", help="Objetivo do workflow")
    parser.add_argument("--workflow", type=Path, help="JSON exportado do Canvas")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Pasta do projeto analisado")
    parser.add_argument("--model", help="Modelo aceito pela sua instalação do Codex")
    parser.add_argument("--writable", action="store_true", help="Permite alterações no workspace; read-only é o padrão")
    parser.add_argument("--output", type=Path, default=Path("jarvis-local-run.json"))
    args = parser.parse_args()
    workflow = json.loads(args.workflow.read_text(encoding="utf-8")) if args.workflow else DEFAULT_WORKFLOW
    results = []
    for node in ordered_nodes(workflow):
        print(f"Executando {node.get('agent')}...", flush=True)
        results.append({"agent": node.get("agent"), "status": "completed", "output": run_agent(node, args.goal, args.workspace.resolve(), args.model, args.writable)})
    report = {"status": "awaiting_approval", "goal": args.goal, "workflow": workflow, "agents": results, "created_at": datetime.now(timezone.utc).isoformat()}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Relatório salvo em {args.output.resolve()}")


if __name__ == "__main__":
    main()
