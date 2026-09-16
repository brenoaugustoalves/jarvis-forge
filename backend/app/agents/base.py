from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class AgentContext:
    project_name: str
    goal: str
    function_name: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    agent: str
    status: str
    summary: str
    findings: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    score: int = 0


class Agent(Protocol):
    name: str
    category: str

    async def run(self, context: AgentContext) -> AgentResult:
        ...
