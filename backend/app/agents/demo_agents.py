from .base import AgentContext, AgentResult


class DemoAgent:
    def __init__(self, name: str, category: str, summary: str, actions: list[str]):
        self.name = name
        self.category = category
        self.summary = summary
        self.actions = actions

    async def run(self, context: AgentContext) -> AgentResult:
        findings = []
        if context.error:
            findings.append(f"Erro recebido para análise: {context.error}")
        if context.function_name:
            findings.append(f"Função analisada: {context.function_name}")

        return AgentResult(
            agent=self.name,
            status="completed",
            summary=self.summary,
            findings=findings,
            actions=self.actions,
            score=90,
        )


AGENTS = {
    "agente_requisitos": DemoAgent(
        "agente_requisitos", "planning", "Requisitos transformados em critérios verificáveis.",
        ["Separar objetivo em tarefas pequenas", "Definir critérios de aceite"],
    ),
    "agente_system_design": DemoAgent(
        "agente_system_design", "architecture", "Fluxo, limites de contexto e dependências avaliados.",
        ["Definir componentes", "Documentar fluxo de dados", "Avaliar escalabilidade"],
    ),
    "agente_clean_architecture": DemoAgent(
        "agente_clean_architecture", "architecture", "Dependências devem apontar para o domínio.",
        ["Separar domínio, aplicação, infraestrutura e entrada", "Reduzir acoplamento"],
    ),
    "agente_backend": DemoAgent(
        "agente_backend", "development", "Proposta de implementação para o serviço backend.",
        ["Aplicar validação de entrada", "Adicionar tratamento de exceções", "Manter regra no caso de uso"],
    ),
    "agente_frontend": DemoAgent(
        "agente_frontend", "development", "Interface e estados de erro considerados.",
        ["Adicionar estado de carregamento", "Tratar erro da API", "Validar acessibilidade"],
    ),
    "agente_testes_unitarios": DemoAgent(
        "agente_testes_unitarios", "testing", "Casos unitários básicos foram planejados.",
        ["Cobrir caminho feliz", "Cobrir entradas inválidas", "Cobrir exceções"],
    ),
    "agente_testes_integracao": DemoAgent(
        "agente_testes_integracao", "testing", "Integrações críticas foram mapeadas.",
        ["Testar banco isolado", "Testar contrato HTTP", "Validar transação"],
    ),
    "agente_testes_carga": DemoAgent(
        "agente_testes_carga", "testing", "Cenário controlado de carga foi definido.",
        ["Definir usuários virtuais", "Medir latência p95", "Impor limite de segurança"],
    ),
    "agente_testes_concorrencia": DemoAgent(
        "agente_testes_concorrencia", "testing", "Riscos de corrida e idempotência foram avaliados.",
        ["Simular requisições simultâneas", "Verificar locks", "Validar idempotência"],
    ),
    "agente_security_review": DemoAgent(
        "agente_security_review", "security", "Revisão de segurança baseada em riscos foi preparada.",
        ["Revisar autenticação e autorização", "Verificar exposição de dados", "Registrar evidências"],
    ),
    "agente_pentest": DemoAgent(
        "agente_pentest", "security", "Plano de teste autorizado para homologação foi preparado.",
        ["Confirmar escopo autorizado", "Executar somente contra ambiente controlado", "Gerar relatório OWASP"],
    ),
    "agente_revisor_final": DemoAgent(
        "agente_revisor_final", "delivery", "Alterações prontas para revisão humana.",
        ["Conferir diff", "Verificar testes", "Bloquear deploy sem aprovação"],
    ),
}
