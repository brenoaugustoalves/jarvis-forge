"""OpenAI-compatible model gateway with safe demo fallback."""
from __future__ import annotations

import asyncio
import json
import os
from urllib.request import Request, urlopen

from .base import AgentContext, AgentResult


class AgentGateway:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "demo").lower()
        self.model = os.getenv("AI_MODEL", "")
        self.api_key = os.getenv("AI_API_KEY", "")
        self.timeout = float(os.getenv("AI_TIMEOUT_SECONDS", "60"))

    @property
    def enabled(self) -> bool:
        return bool(self.model and (self.api_key or self.provider == "ollama"))

    def _endpoint(self):
        return {
            "openai": "https://api.openai.com/v1/chat/completions",
            "openrouter": "https://openrouter.ai/api/v1/chat/completions",
            "ollama": os.getenv("OLLAMA_URL", "http://127.0.0.1:11434") + "/v1/chat/completions",
        }.get(self.provider, "")

    def _call(self, agent_name: str, context: AgentContext) -> AgentResult:
        system = f"Você é o agente {agent_name} de uma plataforma de engenharia. Responda em JSON com summary, findings e actions. Seja objetivo e seguro."
        user = json.dumps({"projeto": context.project_name, "objetivo": context.goal, "função": context.function_name, "erro": context.error}, ensure_ascii=False)
        headers = {"Content-Type": "application/json"}
        if self.api_key: headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(self._endpoint(), data=json.dumps({"model": self.model, "temperature": 0.2, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode(), headers=headers, method="POST")
        with urlopen(request, timeout=self.timeout) as response:
            content = json.loads(response.read())['choices'][0]['message']['content']
        try: parsed = json.loads(content)
        except json.JSONDecodeError: parsed = {"summary": content, "findings": [], "actions": []}
        return AgentResult(agent=agent_name, status="completed", summary=parsed.get("summary", content), findings=parsed.get("findings", []), actions=parsed.get("actions", []), score=parsed.get("score", 90))

    async def run(self, agent_name: str, context: AgentContext, fallback) -> AgentResult:
        if not self.enabled: return await fallback.run(context)
        try: return await asyncio.to_thread(self._call, agent_name, context)
        except Exception as error:
            result = await fallback.run(context)
            result.status = "fallback"
            result.findings.append(f"Gateway indisponível; fallback demo ativado: {error}")
            return result
