# Jarvis Forge

> Uma plataforma visual para criar, orquestrar e auditar workflows de engenharia de software com agentes de IA.

[![Status](https://img.shields.io/badge/status-MVP%20funcional-38bdf8)](https://github.com/brenoaugustoalves/jarvis-forge)
[![Python](https://img.shields.io/badge/Python-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Deploy](https://img.shields.io/badge/deploy-Railway-7c3aed)](https://railway.com/)

## Sobre o projeto

O Jarvis Forge propõe uma “fábrica de software” visual: em vez de executar uma única tarefa de IA em uma conversa, o usuário monta um workflow com agentes especializados e define como eles colaboram.

Cada agente pode representar uma etapa real do ciclo de desenvolvimento — requisitos, arquitetura, backend, frontend, testes, segurança e revisão. O Canvas transforma essa composição em um DAG (grafo acíclico direcionado), permitindo dependências claras e execução paralela de etapas independentes.

O projeto explora, em uma aplicação funcional, os desafios de combinar IA, orquestração, persistência, segurança e observabilidade em engenharia de software.

## O que ele propõe

```text
Canvas visual → Workflow Engine / DAG → Agent Gateway
      → Redis + Worker → PostgreSQL + auditoria
      → Revisão humana e aprovação
```

O objetivo não é substituir a decisão humana. É organizar o trabalho dos agentes, limitar permissões, registrar evidências e tornar cada execução reproduzível e auditável.

## Funcionalidades atuais

### Canvas profissional

- Adição, remoção e arraste individual de agentes.
- Seleção e movimentação de múltiplos nós.
- Zoom, pan, minimapa e ajuste automático do layout.
- Conexões entre nós e execução baseada em DAG.
- Detecção de ciclos no backend.
- Undo/redo, copiar/colar e atalhos de teclado.
- Busca de agentes e templates de workflows.
- Inspetor para prompt, ferramentas, escopo e autorreparo.

### Backend e execução

- API FastAPI com documentação Swagger.
- PostgreSQL na Railway e SQLite para desenvolvimento local.
- Redis para fila de execuções.
- Worker separado para processamento assíncrono.
- Histórico de projetos, workflows, versões e runs.
- Logs de auditoria.
- Status `queued`, `running`, `awaiting_approval` e `failed`.
- Fallback seguro para agentes demonstrativos.

### Modelos de IA

O Agent Gateway possui adaptadores compatíveis com OpenAI, OpenRouter e Ollama. Quando um provedor está configurado, os agentes usam o modelo definido. Se houver falha ou limite de API, o sistema retorna ao modo demo para não quebrar o workflow.

### Segurança por padrão

- API key opcional para proteger endpoints.
- Pentest bloqueado sem escopo autorizado.
- Separação entre API pública e worker interno.
- Segredos configurados por variáveis de ambiente.
- Aprovação humana antes da etapa de entrega.

## Demonstração

Ambiente publicado na Railway:

**https://jarvis-forge-production-bd8c.up.railway.app**

Endpoints úteis:

```text
GET /health              GET /api/agents
GET /api/providers       GET /api/projects
GET /api/workflows       GET /api/runs/{run_id}
GET /api/audit
```

## Stack

| Camada | Tecnologia |
| --- | --- |
| API | Python, FastAPI, Pydantic |
| Persistência | PostgreSQL, SQLite, Alembic |
| Fila | Redis |
| Worker | Python asyncio |
| IA | OpenAI-compatible Gateway, OpenRouter, Ollama |
| Interface | HTML, CSS e JavaScript no Canvas atual |
| Infraestrutura | Docker, Docker Compose, Railway |
| Qualidade | Pytest e validação de workflows |

## Como executar localmente

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000` e a documentação em `http://127.0.0.1:8000/docs`.

Para PostgreSQL e Redis locais:

```bash
docker compose up --build
```

Para executar o worker manualmente:

```bash
cd backend
python worker.py
```

## Executar usando o limite local do ChatGPT/Codex

Quando o Codex CLI estiver instalado e autenticado no computador, use o runner local. Ele não usa `AI_API_KEY`, não envia a sessão para a Railway e mantém a execução dentro da cota da conta local do Codex.

```powershell
cd backend
codex login status
python local_runner.py "Analise a arquitetura deste projeto"
```

Para usar um workflow exportado do Canvas:

```powershell
python local_runner.py "Revise este projeto" --workflow workflow.json --workspace C:\caminho\do\projeto
```

O padrão é `read-only`; use `--writable` somente quando quiser permitir alterações e sempre revise o relatório `jarvis-local-run.json` antes de aplicar qualquer mudança. No Windows, também é possível executar `run-local-windows.bat`.

## Configuração de IA

Crie `.env` a partir de `.env.example`:

```env
AI_PROVIDER=openai
AI_MODEL=gpt-4.1-mini
AI_API_KEY=sua-chave
```

Na Railway, configure as variáveis no serviço da API e no serviço `jarvis-forge-worker`. Nunca publique `.env` ou chaves no GitHub.

## Deploy

O repositório possui `Dockerfile` na raiz e `railway.json`. A arquitetura publicada possui:

```text
jarvis-forge         API pública
jarvis-forge-worker  consumidor da fila Redis
Postgres             banco persistente
Redis                fila de execução
```

## Roadmap

- Migrar o Canvas para React + TypeScript.
- Adicionar WebSocket/SSE para progresso em tempo real.
- Implementar retry, timeout e cancelamento por etapa.
- Criar sandbox Docker com limites de CPU, memória e rede.
- Executar Pytest, Semgrep, Bandit, Trivy e Gitleaks de forma isolada.
- Adicionar autenticação completa, RBAC e organizações.
- Integrar GitHub para branches, diffs e Pull Requests.
- Implementar autorreparo real com patch, testes e aprovação humana.
- Adicionar métricas com OpenTelemetry, Prometheus e Grafana.

## Por que este projeto é relevante

O Jarvis Forge funciona como um laboratório de arquitetura para sistemas multiagentes. Ele demonstra preocupações que vão além de uma interface de chat: composição de workflows, concorrência, persistência, filas, limites de segurança, fallback de provedores e rastreabilidade das decisões.

O projeto continua em evolução, mas já oferece uma base executável para experimentar como agentes de IA podem colaborar dentro de um processo de engenharia controlado.

## Licença

Projeto experimental para fins de estudo e portfólio.
