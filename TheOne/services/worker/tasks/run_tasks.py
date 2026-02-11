from __future__ import annotations

import asyncio
import os
from typing import Any

from celery import Celery

from services.orchestrator.runtime import run_pipeline

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("gtmgraph_worker", broker=redis_url, backend=redis_url)


@celery_app.task(name="runs.execute_stub")
def execute_stub_run(state: dict[str, Any], changed_decision: str | None = None) -> dict[str, Any]:
    events: list[dict[str, Any]] = []

    async def publisher(event_type: str, data: dict[str, Any]) -> None:
        events.append({"type": event_type, "data": data})

    async def checkpoint(_: dict[str, Any], __: int, ___: str) -> None:
        return None

    result = asyncio.run(
        run_pipeline(
            state=state,
            publish=publisher,
            checkpoint=checkpoint,
            changed_decision=changed_decision,
        )
    )
    return {"state": result.state, "events": events}
