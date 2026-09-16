"""Redis-backed execution queue."""
from __future__ import annotations

import json
import os

import redis.asyncio as redis


QUEUE_NAME = "jarvis-forge:runs"


class RunQueue:
    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("REDIS_URL")
        self.client = redis.from_url(self.url, decode_responses=True) if self.url else None

    @property
    def enabled(self) -> bool:
        return self.client is not None

    async def enqueue(self, job: dict):
        if not self.client:
            raise RuntimeError("REDIS_URL não configurada")
        await self.client.rpush(QUEUE_NAME, json.dumps(job, ensure_ascii=False))

    async def next(self, timeout: int = 5) -> dict | None:
        if not self.client:
            raise RuntimeError("REDIS_URL não configurada")
        item = await self.client.blpop(QUEUE_NAME, timeout=timeout)
        return json.loads(item[1]) if item else None

    async def close(self):
        if self.client:
            await self.client.aclose()
