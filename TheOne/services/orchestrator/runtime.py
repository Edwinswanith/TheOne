from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from services.orchestrator.agents.stub_agents import build_agent_output
from services.orchestrator.dependencies import AGENT_SEQUENCE, impacted_agents
from services.orchestrator.state.default_state import utc_now_iso
from services.orchestrator.state.merge import merge_agent_outputs
from services.orchestrator.validators.rules import run_validator

EventPublisher = Callable[[str, dict[str, Any]], Awaitable[None]]
CheckpointCallback = Callable[[dict[str, Any], int, str], Awaitable[None]]


@dataclass
class PipelineResult:
    state: dict[str, Any]
    completed_agents: list[str]
    skipped_agents: list[str]
    last_agent_index: int
    blocking: bool


class PipelineFailure(RuntimeError):
    def __init__(
        self,
        message: str,
        state: dict[str, Any],
        failed_agent: str,
        failed_index: int,
        completed_agents: list[str],
        skipped_agents: list[str],
    ):
        super().__init__(message)
        self.state = state
        self.failed_agent = failed_agent
        self.failed_index = failed_index
        self.completed_agents = completed_agents
        self.skipped_agents = skipped_agents


async def run_pipeline(
    state: dict[str, Any],
    publish: EventPublisher,
    checkpoint: CheckpointCallback,
    changed_decision: str | None = None,
    start_index: int = 0,
    resumed: bool = False,
    simulate_failure_at_agent: str | None = None,
) -> PipelineResult:
    run_id = state["meta"]["run_id"]
    run_agents = impacted_agents(changed_decision)

    if resumed:
        await publish("run_resumed", {"run_id": run_id, "start_index": start_index})
    else:
        await publish("run_started", {"run_id": run_id, "status": "running"})

    completed_agents: list[str] = []
    skipped_agents: list[str] = []

    for agent_index, agent in enumerate(AGENT_SEQUENCE[start_index:], start=start_index):
        start_at = utc_now_iso()
        timer = perf_counter()

        if agent not in run_agents:
            skipped_agents.append(agent)
            _append_timing(state, agent, start_at, utc_now_iso(), 0, "skipped")
            continue

        await publish("agent_started", {"agent": agent, "index": agent_index})
        await asyncio.sleep(0.03)

        if simulate_failure_at_agent and agent == simulate_failure_at_agent:
            end_at = utc_now_iso()
            duration_ms = int((perf_counter() - timer) * 1000)
            _append_timing(state, agent, start_at, end_at, duration_ms, "failed")
            raise PipelineFailure(
                f"Simulated failure at {agent}",
                state,
                failed_agent=agent,
                failed_index=agent_index,
                completed_agents=completed_agents,
                skipped_agents=skipped_agents,
            )

        output = build_agent_output(agent, run_id, state, changed_decision)
        state, warnings = merge_agent_outputs(state, [output])

        if warnings:
            await publish(
                "validator_warning",
                {
                    "agent": agent,
                    "count": len(warnings),
                    "warnings": [warning.__dict__ for warning in warnings],
                },
            )

        await publish(
            "agent_progress",
            {
                "agent": agent,
                "patch_count": len(output.get("patches", [])),
                "proposal_count": len(output.get("proposals", [])),
            },
        )

        completed_agents.append(agent)
        end_at = utc_now_iso()
        duration_ms = int((perf_counter() - timer) * 1000)
        _append_timing(state, agent, start_at, end_at, duration_ms, "completed")

        await checkpoint(state, agent_index, agent)
        await publish("state_checkpointed", {"agent": agent, "index": agent_index, "updated_at": state["meta"]["updated_at"]})
        await publish("agent_completed", {"agent": agent, "index": agent_index})

    validation = run_validator(state)
    if validation["blocking"]:
        await publish("run_blocked", {"reasons": validation["contradictions"]})
    else:
        await publish("node_updated", {"node_ids": [node["id"] for node in state["graph"]["nodes"]]})
        await publish("run_completed", {"status": "completed"})

    return PipelineResult(
        state=state,
        completed_agents=completed_agents,
        skipped_agents=skipped_agents,
        last_agent_index=(len(AGENT_SEQUENCE) - 1),
        blocking=validation["blocking"],
    )


def _append_timing(
    state: dict[str, Any],
    agent: str,
    started_at: str,
    ended_at: str,
    duration_ms: int,
    status: str,
) -> None:
    state["telemetry"]["agent_timings"].append(
        {
            "agent": agent,
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_ms": duration_ms,
            "status": status,
        }
    )
