import asyncio

from app.core.orchestrator import InMemoryStore, Orchestrator


def test_orchestrator_routes_agents_by_function():
    orchestrator = Orchestrator(InMemoryStore())
    project = orchestrator.create_project({"name": "Projeto teste"})
    run = asyncio.run(orchestrator.execute(project, {
        "goal": "Corrigir processamento concorrente",
        "function_name": "processar_pagamento",
        "error": "Timeout intermitente",
    }))

    names = {agent["agent"] for agent in run["agents"]}
    assert "agente_testes_concorrencia" in names
    assert "agente_testes_carga" in names
    assert run["status"] == "awaiting_approval"
