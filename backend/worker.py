"""Railway worker: consume Redis jobs and execute workflows outside HTTP."""
from __future__ import annotations

import asyncio
import traceback

from app.core.orchestrator import Orchestrator
from app.core.persistence import PersistentStore
from app.core.queue import RunQueue


async def main():
    store = PersistentStore()
    queue = RunQueue()
    if not queue.enabled:
        raise RuntimeError("REDIS_URL é obrigatória para iniciar o worker")
    orchestrator = Orchestrator(store)
    print("Jarvis Forge worker aguardando jobs Redis", flush=True)
    try:
        while True:
            job = await queue.next()
            if not job:
                continue
            run = store.get_run(job["run_id"])
            if not run:
                continue
            run["status"] = "running"
            store.update_run(run)
            try:
                payload = {**job["payload"], "_run_id": job["run_id"]}
                result = await orchestrator.execute(job["project"], payload)
                store.update_run(result)
            except Exception as error:
                run["status"] = "failed"
                run["error_detail"] = str(error)
                run["traceback"] = traceback.format_exc()
                store.update_run(run)
                print(f"run {run['id']} falhou: {error}", flush=True)
    finally:
        await queue.close()


if __name__ == "__main__":
    asyncio.run(main())
