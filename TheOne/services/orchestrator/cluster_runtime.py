"""Cluster-based pipeline runtime — phased execution with orchestrator feedback loop."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from copy import deepcopy
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from services.orchestrator.agents.registry import build_agent_output
from services.orchestrator.clusters.dependencies import CLUSTER_PHASES, get_downstream_pillars
from services.orchestrator.clusters.registry import get_cluster_registry
from services.orchestrator.orchestrator.orchestrator_agent import (
    FeedbackDirective,
    group_directives_by_cluster,
    run_orchestrator_check,
)
from services.orchestrator.state.default_state import utc_now_iso
from services.orchestrator.state.merge import merge_agent_outputs, merge_cluster_outputs
from services.orchestrator.tools.providers import ProviderClient
from services.orchestrator.validators.rules import run_validator

EventPublisher = Callable[[str, dict[str, Any]], Awaitable[None]]
CheckpointCallback = Callable[[dict[str, Any], int, str], Awaitable[None]]

# Thread pool size for parallel cluster execution
_THREAD_POOL_SIZE = 12


@dataclass
class ClusterPipelineResult:
    """Result of a cluster pipeline run."""

    state: dict[str, Any]
    completed_clusters: list[str] = field(default_factory=list)
    orchestrator_rounds: int = 0
    blocking: bool = False
    pivot_required: bool = False
    pivot_details: dict[str, Any] | None = None


class PipelineFailure(RuntimeError):
    """Raised when a cluster pipeline fails."""

    def __init__(
        self,
        message: str,
        state: dict[str, Any],
        failed_cluster: str,
        completed_clusters: list[str],
    ):
        super().__init__(message)
        self.state = state
        self.failed_cluster = failed_cluster
        self.completed_clusters = completed_clusters


def _auto_recommend(state: dict[str, Any], output: dict[str, Any]) -> None:
    """Auto-select recommended options from agent proposals."""
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


def _compute_change_score(
    previous_state: dict[str, Any],
    current_state: dict[str, Any],
    pillar: str,
) -> float:
    """Compute how much a pillar changed between two states (0.0 to 1.0).

    Compares pillar summary, decisions, and key fields. Returns a normalized
    change score where 0.0 = no change and 1.0 = complete rewrite.
    """
    prev_pillar = previous_state.get("pillars", {}).get(pillar, {})
    curr_pillar = current_state.get("pillars", {}).get(pillar, {})

    changes = 0
    total_fields = 0

    # Compare summary
    total_fields += 1
    if prev_pillar.get("summary", "") != curr_pillar.get("summary", ""):
        changes += 1

    # Compare decisions relevant to this pillar
    pillar_to_decisions = {
        "customer": ["icp"],
        "positioning_pricing": ["positioning", "pricing"],
        "go_to_market": ["channels", "sales_motion"],
    }
    for dk in pillar_to_decisions.get(pillar, []):
        total_fields += 1
        prev_sel = previous_state.get("decisions", {}).get(dk, {}).get("selected_option_id", "")
        curr_sel = current_state.get("decisions", {}).get(dk, {}).get("selected_option_id", "")
        if prev_sel != curr_sel:
            changes += 1

    # Compare node count changes
    total_fields += 1
    prev_nodes = len(prev_pillar.get("nodes", []))
    curr_nodes = len(curr_pillar.get("nodes", []))
    if abs(prev_nodes - curr_nodes) > 2:
        changes += 1

    return changes / max(total_fields, 1)


def _critical_input_changed(
    previous_state: dict[str, Any],
    current_state: dict[str, Any],
    pillar: str,
) -> bool:
    """Check if a critical input (ICP, pricing, channels) changed for this pillar."""
    critical_decisions = {
        "go_to_market": ["icp", "pricing"],
        "product_tech": ["icp"],
        "execution": ["icp", "pricing", "channels", "sales_motion"],
        "positioning_pricing": ["icp"],
        "customer": [],
        "market_intelligence": [],
    }
    for dk in critical_decisions.get(pillar, []):
        prev = previous_state.get("decisions", {}).get(dk, {}).get("selected_option_id", "")
        curr = current_state.get("decisions", {}).get(dk, {}).get("selected_option_id", "")
        if prev != curr:
            return True
    return False


async def run_cluster_pipeline(
    state: dict[str, Any],
    publish: EventPublisher,
    checkpoint: CheckpointCallback,
    changed_decision: str | None = None,
    start_index: int = 0,
    resumed: bool = False,
) -> ClusterPipelineResult:
    """Execute the cluster-based pipeline.

    Phases:
    1. Execute cluster phases (parallel within phases, sequential across phases)
    2. Orchestrator cross-reference (deterministic rules + optional Gemini arbitration)
    3. Feedback round (targeted cluster reruns)
    4. Convergence check (detect pivots, block if needed)
    5. Finalization (graph builder + validator)
    """
    run_id = state["meta"]["run_id"]
    provider = ProviderClient()
    registry = get_cluster_registry(provider)

    if resumed:
        await publish("run_resumed", {"run_id": run_id, "start_index": start_index})
    else:
        await publish("run_started", {"run_id": run_id, "status": "running", "mode": "cluster"})

    completed_clusters: list[str] = []
    pipeline_timer = perf_counter()

    # -----------------------------------------------------------------------
    # Phase 1: Execute cluster phases
    # -----------------------------------------------------------------------
    for phase_idx, phase_clusters in enumerate(CLUSTER_PHASES):
        await publish("cluster_phase_started", {
            "phase": phase_idx,
            "clusters": phase_clusters,
        })

        phase_timer = perf_counter()

        # Execute clusters within this phase in parallel
        tasks = []
        for cluster_name in phase_clusters:
            if cluster_name not in registry:
                continue
            await publish("cluster_started", {
                "cluster": cluster_name,
                "phase": phase_idx,
            })
            tasks.append(
                registry[cluster_name].execute(
                    run_id, state, publish, changed_decision
                )
            )

        try:
            results = await asyncio.gather(*tasks)
        except Exception as exc:
            raise PipelineFailure(
                f"Cluster phase {phase_idx} failed: {exc}",
                state,
                failed_cluster=phase_clusters[0] if phase_clusters else "unknown",
                completed_clusters=completed_clusters,
            ) from exc

        # Merge results deterministically (sorted by pillar name)
        for result in sorted(results, key=lambda r: r.pillar):
            state, warnings = merge_cluster_outputs(state, result)
            # Auto-recommend from each sub-agent's proposals
            for output in result.outputs:
                _auto_recommend(state, output)
            completed_clusters.append(result.pillar)

            await publish("cluster_completed", {
                "cluster": result.pillar,
                "phase": phase_idx,
                "artifact_count": len(result.artifacts),
            })

        # Checkpoint after each phase
        phase_ms = int((perf_counter() - phase_timer) * 1000)
        state["telemetry"]["cluster_timings"].append({
            "phase": phase_idx,
            "clusters": phase_clusters,
            "duration_ms": phase_ms,
        })
        await checkpoint(state, phase_idx, f"phase_{phase_idx}")

    # -----------------------------------------------------------------------
    # Phase 2: Orchestrator cross-reference
    # -----------------------------------------------------------------------
    await publish("orchestrator_started", {"phase": "cross_reference"})

    report = run_orchestrator_check(state, provider)

    state["telemetry"]["orchestrator_rounds"].append({
        "round": 0,
        "rules_evaluated": report.rules_evaluated,
        "failures": len(report.failures),
        "directives": len(report.directives),
    })

    await publish("orchestrator_completed", {
        "conflicts": len(report.failures),
        "directives": len(report.directives),
        "insights": report.insights,
    })

    # -----------------------------------------------------------------------
    # Phase 3: Feedback round (if conflicts detected)
    # -----------------------------------------------------------------------
    directives = report.directives
    previous_state = None

    if directives:
        previous_state = deepcopy(state)
        await publish("feedback_round_started", {
            "directive_count": len(directives),
        })

        grouped = group_directives_by_cluster(directives)
        rerun_tasks = []
        for cluster_name, cluster_directives in grouped.items():
            if cluster_name not in registry:
                continue
            rerun_tasks.append(
                registry[cluster_name].execute(
                    run_id, state, publish,
                    changed_decision=changed_decision,
                    feedback=cluster_directives,
                )
            )

        try:
            rerun_results = await asyncio.gather(*rerun_tasks)
        except Exception:
            # Non-fatal: feedback round failure doesn't block the pipeline
            rerun_results = []

        for result in sorted(rerun_results, key=lambda r: r.pillar):
            state, _ = merge_cluster_outputs(state, result)
            for output in result.outputs:
                _auto_recommend(state, output)

        await publish("feedback_round_completed", {
            "clusters_rerun": list(grouped.keys()),
        })

    # -----------------------------------------------------------------------
    # Phase 4: Convergence check
    # -----------------------------------------------------------------------
    if directives and previous_state:
        await publish("convergence_check", {"phase": "started"})

        rerun_pillars = list({d.target_cluster for d in directives})
        for pillar in rerun_pillars:
            change_score = _compute_change_score(previous_state, state, pillar)
            critical_changed = _critical_input_changed(previous_state, state, pillar)

            if change_score > 0.5 and critical_changed:
                # Pipeline blocks — pivot decision required
                state["pillars"][pillar]["status"] = "pending_user_decision"
                await publish("pivot_decision_required", {
                    "pillar": pillar,
                    "change_score": change_score,
                    "critical_input_changed": True,
                    "message": f"Significant changes in {pillar} require user decision.",
                })
                return ClusterPipelineResult(
                    state=state,
                    completed_clusters=completed_clusters,
                    orchestrator_rounds=1,
                    blocking=True,
                    pivot_required=True,
                    pivot_details={
                        "pillar": pillar,
                        "change_score": change_score,
                        "downstream_affected": list(get_downstream_pillars(pillar)),
                    },
                )
            elif change_score > 0.3:
                state["risks"].setdefault("unresolved_contradictions", []).append({
                    "rule_id": "CONVERGENCE",
                    "severity": "medium",
                    "message": f"Pillar {pillar} changed significantly (score: {change_score:.2f}) but converged.",
                    "paths": [f"/pillars/{pillar}"],
                })

        await publish("convergence_check", {"phase": "completed", "converged": True})

    # -----------------------------------------------------------------------
    # Phase 5: Finalization (graph builder + validator)
    # -----------------------------------------------------------------------
    graph_output = build_agent_output("graph_builder", run_id, state)
    state, _ = merge_agent_outputs(state, [graph_output])

    validation = run_validator(state)
    remaining = [c for c in validation.get("contradictions", []) if c["severity"] in {"critical", "high"}]
    state["risks"]["unresolved_contradictions"] = remaining

    total_ms = int((perf_counter() - pipeline_timer) * 1000)
    state["telemetry"]["cluster_timings"].append({
        "phase": "total",
        "duration_ms": total_ms,
    })

    if validation["blocking"]:
        await publish("run_blocked", {"reasons": validation["contradictions"]})
    else:
        await publish("node_updated", {
            "node_ids": [node["id"] for node in state["graph"]["nodes"]],
        })
        await publish("run_completed", {"status": "completed", "mode": "cluster"})

    return ClusterPipelineResult(
        state=state,
        completed_clusters=completed_clusters,
        orchestrator_rounds=1 if directives else 0,
        blocking=validation["blocking"],
    )
