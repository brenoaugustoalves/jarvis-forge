# Jarvis Forge

Plataforma inicial de engenharia de software multiagente. Ela organiza agentes de IA por função, aplica práticas de Clean Code, Clean Architecture, SOLID e System Design, executa uma esteira de validação e prepara correções em fluxo seguro.

> Esta versão é um MVP executável. Os agentes possuem implementações demonstrativas, sem exigir uma chave de IA. O contrato de cada agente já está separado para conectar OpenAI, OpenRouter ou modelos locais.

## O que já existe

- Cadastro de projetos e funções do sistema.
- Registro de agentes por especialidade.
- Orquestração de planejamento, arquitetura, implementação, testes e segurança.
- Execução de uma simulação de autorreparo com tentativas limitadas.
- Relatório de testes unitários, integração, carga, concorrência e segurança.
- Dashboard web simples.
- Canvas visual para montar workflows arrastando e conectando agentes.
- Inspetor visual para editar papel, prompt, ferramentas, escopo e autorreparo de cada agente.
- Templates visuais de API segura, Clean Architecture e QA completo.
- API FastAPI e documentação Swagger.
- Docker Compose para subir a plataforma.
- Persistência durável de projetos, versões de workflow, execuções e auditoria.
- PostgreSQL no Docker Compose e SQLite zero-config para desenvolvimento local.
- Execução de DAG por níveis paralelos, com validação de ciclos.
- Agent Gateway compatível com OpenAI, OpenRouter e Ollama, com fallback demo.
- Proteção opcional da API por `JARVIS_API_KEY` e bloqueio de pentest sem escopo autorizado.

### Persistência e migrations

O modo local usa `DATABASE_URL=sqlite:///./jarvis-forge.db`. Para subir a stack completa:

```bash
docker compose up --build
```

O serviço usa PostgreSQL com volume persistente. A estrutura também possui migrations Alembic em `backend/alembic`; em um ambiente com SQLAlchemy instalado, execute `alembic upgrade head` dentro de `backend`.

Endpoints operacionais adicionados: `GET /api/projects/{project_id}/runs` para histórico de execuções e `GET /api/audit` para a trilha de auditoria.

### Modelos de IA

Configure o gateway pelo ambiente. Sem `AI_API_KEY` (ou com `AI_PROVIDER=ollama` sem modelo), o sistema permanece em modo demo. Com um provedor configurado, os agentes usam o modelo e retornam automaticamente ao agente demo se houver timeout ou falha do provedor:

```env
AI_PROVIDER=openrouter
AI_MODEL=openai/gpt-4o-mini
AI_API_KEY=...
```

O endpoint `GET /api/providers` mostra o provedor ativo sem expor a chave.

## Executar localmente

O inicializador é autorreparável para problemas do ambiente Python: ele cria `.venv`, instala ou atualiza as dependências declaradas e somente depois inicia a API.

### Windows — recomendado

Você pode abrir `start-windows.bat` com duplo clique ou executar:

```powershell
cd C:\caminho\jarvis-forge-final\jarvis-forge\backend
python run.py
```

Também é possível executar diretamente `app/main.py`; o bootstrap tentará preparar o ambiente. Porém, `run.py` é o ponto de entrada preferido porque inicia o Uvicorn corretamente.

### Python

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abra http://127.0.0.1:8000 para acessar o dashboard e http://127.0.0.1:8000/docs para a API.

### Deploy no Railway

O repositório já contém `railway.json` e usa `backend/Dockerfile`. No Railway:

1. Crie um projeto e conecte este repositório.
2. Crie um serviço PostgreSQL e copie a variável `DATABASE_URL` para o serviço da API.
3. Gere um domínio público para a API.
4. Configure `AI_PROVIDER`, `AI_MODEL`, `AI_API_KEY` e, em ambiente compartilhado, `JARVIS_API_KEY`.
5. Faça o deploy. O healthcheck será `GET /health`.

O Railway injeta a variável `PORT`; o Dockerfile já escuta essa porta automaticamente. O Railway recomenda usar bancos gerenciados em vez de imagens PostgreSQL/Redis dentro do Compose. Consulte a [documentação de configuração como código](https://docs.railway.com/config-as-code) e a [documentação de Dockerfiles](https://docs.railway.com/builds/dockerfiles).

## Usar o Canvas

No Canvas, use um template ou adicione agentes pela biblioteca lateral. Arraste os nós, clique em `Conectar nós` para criar o fluxo e selecione qualquer nó para editar seu papel. O workflow fica salvo localmente no navegador até você clicar em `Salvar workflow`; `Executar fluxo` envia a configuração para o orquestrador.

Cada nó pode receber um prompt diferente. Isso permite montar uma esteira como:

```text
Requisitos → System Design → Backend → Testes → Segurança → Revisão
```

Os nós de segurança são marcados separadamente e devem usar somente escopos autorizados. Quando o workflow contém arestas, o backend converte-as em um DAG, executa agentes independentes em paralelo e rejeita ciclos; sem arestas, mantém o comportamento sequencial compatível.

### Docker

```bash
docker compose up --build
```

## Fluxo de autorreparo

1. O projeto envia um objetivo ou erro.
2. O analisador identifica a função afetada.
3. O roteador seleciona os agentes configurados para aquela função.
4. Os agentes geram diagnóstico, proposta e testes.
5. A esteira valida qualidade, segurança, carga e concorrência.
6. Uma correção é preparada para branch isolada.
7. O resultado fica aguardando aprovação antes de produção.

## Configuração por função

Edite `backend/config/functions.yaml`:

```yaml
functions:
  processar_pagamento:
    agents:
      - agente_debug
      - agente_backend
      - agente_testes_concorrencia
      - agente_security_review
```

Os testes de penetração devem ser executados somente em aplicações próprias ou em ambientes para os quais exista autorização explícita. O próximo passo natural é conectar o `RepairEngine` a Git, Docker sandbox e um provedor de IA.

## Próximos módulos

- Persistência em PostgreSQL.
- Redis/Celery para filas de execução.
- Integração GitHub para branches e Pull Requests.
- Execução real de Pytest, JUnit, k6, Locust, Semgrep, Trivy, Gitleaks e OWASP ZAP.
- Autenticação, RBAC, auditoria e aprovação humana.
- Adaptadores para Java/Spring Boot, Python/FastAPI e React/TypeScript.
