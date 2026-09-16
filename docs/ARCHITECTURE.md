# Arquitetura do Jarvis Forge

## Camadas

1. **Canvas** — composição visual dos workflows.
2. **API** — projetos, agentes, funções, workflows e execuções.
3. **Orquestrador** — roteia agentes e controla o estado da execução.
4. **Agentes** — especialistas com contrato de entrada e saída.
5. **Sandbox** — futura execução isolada de código, testes e scanners.
6. **Auditoria** — histórico de prompts, ações, evidências e aprovações.

## Contrato de um agente

Todo agente deve receber contexto limitado e devolver:

```json
{
  "agent": "agente_testes_unitarios",
  "status": "completed",
  "summary": "...",
  "findings": [],
  "actions": [],
  "evidence": [],
  "risk": "low"
}
```

Um agente não deve alterar produção diretamente. Alterações devem ser criadas em branch ou workspace temporário e passar por testes, análise de segurança e aprovação.

## Estado de uma execução

```text
created → analyzing → planning → generating_patch → testing → security_review → awaiting_approval → approved → deployed
                                                                                                  ↘ rejected / rolled_back
```

## Testes e segurança

Os perfis recomendados são:

- unitário: Pytest, JUnit e Mockito;
- integração: Testcontainers e banco isolado;
- API: contratos HTTP e validação de schema;
- carga: k6 ou Locust com limite de usuários virtuais;
- concorrência: idempotência, locks e race conditions controladas;
- SAST: Semgrep, Bandit e Checkstyle;
- dependências: Trivy, pip-audit e OWASP Dependency-Check;
- segredos: Gitleaks;
- DAST: OWASP ZAP em homologação autorizada.

## Princípios

- Clean Code e SOLID;
- Clean Architecture;
- baixo acoplamento e alta coesão;
- contratos claros entre agentes;
- menor privilégio para ferramentas;
- execução idempotente;
- logs estruturados sem segredos;
- revisão humana para produção;
- rollback verificável.
