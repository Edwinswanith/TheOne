from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._history: dict[str, list[dict[str, Any]]] = defaultdict(list)

    async def publish(self, run_id: str, scenario_id: str, event_type: str, data: dict[str, Any]) -> None:
        event = {
            "event_id": str(uuid4()),
            "run_id": run_id,
            "scenario_id": scenario_id,
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "data": data,
        }
        self._history[run_id].append(event)
        for queue in self._subscribers.get(run_id, []):
            await queue.put(event)

    async def subscribe(self, run_id: str):
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers[run_id].append(queue)
        try:
            for event in self._history.get(run_id, []):
                yield event
            while True:
                event = await queue.get()
                yield event
        finally:
            self._subscribers[run_id].remove(queue)
