from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from services.orchestrator.agents.registry import build_agent_output
from services.orchestrator.dependencies import AGENT_SEQUENCE, impacted_agents
from services.orchestrator.state.default_state import utc_now_iso
from services.orchestrator.state.merge import merge_agent_outputs
from services.orchestrator.validators.rules import run_validator

EventPublisher = Callable[[str, dict[str, Any]], Awaitable[None]]
CheckpointCallback = Callable[[dict[str, Any], int, str], Awaitable[None]]

_PATH_TO_AGENT: dict[str, str] = {
    "/decisions/icp": "icp_agent",
    "/decisions/positioning": "positioning_agent",
    "/decisions/pricing": "pricing_agent",
    "/decisions/channels": "channel_agent",
    "/decisions/sales_motion": "sales_motion_agent",
    "/pillars/market_intelligence": "evidence_collector",
    "/pillars/customer": "icp_agent",
    "/pillars/positioning_pricing": "positioning_agent",
    "/pillars/go_to_market": "channel_agent",
    "/pillars/product_tech": "product_strategy_agent",
    "/pillars/execution": "execution_agent",
}


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


def _path_to_responsible_agent(path: str) -> str | None:
    """Map a contradiction path to the responsible agent."""
    for prefix, agent in _PATH_TO_AGENT.items():
        if path.startswith(prefix):
            return agent
    return None


def _auto_recommend(state: dict[str, Any], output: dict[str, Any]) -> None:
    """Auto-select recommended options from this agent's proposals.

    Runtime IS the orchestrator, so setting selected_option_id here
    does not violate merge engine rules.
    """
    for proposal in output.get("proposals", []):
        key = proposal.get("decision_key")
        rec = proposal.get("recommended_option_id")
        if not key or not rec:
            continue
        decision = state["decisions"].get(key)
        if decision is None:
            continue
        if not decision.get("selected_option_id"):
            decision["selected_option_id"] = rec
            decision["selection_mode"] = "auto_recommended"


async def _reconciliation_pass(
    state: dict[str, Any],
    run_id: str,
    publish: EventPublisher,
    checkpoint: CheckpointCallback,
    completed_agents: list[str],
) -> dict[str, Any]:
    """Pass 2: Validator identifies contradictions, triggers targeted agent reruns."""
    validation = run_validator(state)
    contradictions = validation.get("contradictions", [])
    if not contradictions:
        return state

    rerun_set: set[str] = set()
    for c in contradictions:
        for path in c.get("paths", []):
            agent = _path_to_responsible_agent(path)
            if agent and agent in completed_agents:
                rerun_set.add(agent)

    rerun_set -= {"graph_builder", "validator_agent"}

    for agent_name in AGENT_SEQUENCE:
        if agent_name not in rerun_set:
            continue
        await publish("agent_started", {"agent": agent_name, "pass": 2})
        output = build_agent_output(agent_name, run_id, state)
        state, _ = merge_agent_outputs(state, [output])
        _auto_recommend(state, output)
        await checkpoint(state, -1, agent_name)
        await publish("agent_completed", {"agent": agent_name, "pass": 2})

    # Re-run graph builder + validator after reconciliation
    for agent_name in ["graph_builder", "validator_agent"]:
        output = build_agent_output(agent_name, run_id, state)
        state, _ = merge_agent_outputs(state, [output])

    return state


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

        # Accumulate token usage telemetry
        token_usage = output.get("token_usage")
        if token_usage:
            spend = state["telemetry"].setdefault("token_spend", {"total": 0, "by_agent": []})
            agent_tokens = token_usage.get("input_tokens", 0) + token_usage.get("output_tokens", 0)
            spend["total"] = spend.get("total", 0) + agent_tokens
            spend.setdefault("by_agent", []).append({
                "agent": agent,
                "input_tokens": token_usage.get("input_tokens", 0),
                "output_tokens": token_usage.get("output_tokens", 0),
                "model": token_usage.get("model", "unknown"),
                "execution_time_ms": output.get("execution_time_ms", 0),
            })

        # Auto-recommend after each agent's proposals
        _auto_recommend(state, output)

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

    # Reconciliation pass (only on fresh runs, not partial reruns)
    if not changed_decision:
        state = await _reconciliation_pass(state, run_id, publish, checkpoint, completed_agents)

    # Final validation
    validation = run_validator(state)

    # Store unresolved contradictions
    remaining = [c for c in validation.get("contradictions", []) if c["severity"] in {"critical", "high"}]
    state["risks"]["unresolved_contradictions"] = remaining

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
