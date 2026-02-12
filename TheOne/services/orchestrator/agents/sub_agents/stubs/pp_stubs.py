"""Positioning & Pricing stub sub-agents for testing."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent
from services.orchestrator.agents.sub_agents.schemas import (
    ReasoningArtifact,
    ReasoningStep,
    SubAgentOutput,
)
from services.orchestrator.clusters.engine import PillarCluster


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _meta(
    source_type: str = "inference",
    confidence: float = 0.7,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    return {"source_type": source_type, "confidence": confidence, "sources": sources or []}


def _stub_artifact(agent_name: str, run_id: str, round_num: int, step: ReasoningStep) -> ReasoningArtifact:
    return ReasoningArtifact(
        artifact_id=f"{agent_name}_{run_id}_{round_num}",
        agent=agent_name,
        pillar="positioning_pricing",
        round=round_num,
        reasoning_chain=[step],
        output_summary=f"{agent_name} stub completed",
        execution_meta={
            "llm_calls": 0,
            "external_searches": 0,
            "total_tokens": 0,
            "execution_time_ms": 5,
            "model": "stub",
        },
    )


class StubCategoryFramer(BaseSubAgent):
    """Stub that returns fixture positioning category and decision proposals."""

    name = "category_framer"
    pillar = "positioning_pricing"
    step_number = 1
    total_steps = 4

    def build_prompt(
        self,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
    ) -> str:
        return ""

    def parse_response(
        self,
        raw: dict[str, Any],
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {}

    def run(
        self,
        run_id: str,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
        round_num: int = 0,
    ) -> SubAgentOutput:
        artifact = _stub_artifact(
            self.name, run_id, round_num,
            ReasoningStep(step=1, action="analysis", thought="Framing market category (stub)", confidence=0.76),
        )
        agent_output = {
            "agent": self.name,
            "agent_version": self.version,
            "pillar": self.pillar,
            "run_id": run_id,
            "produced_at": _now(),
            "patches": [
                {
                    "op": "replace",
                    "path": "/decisions/positioning/frame",
                    "value": {
                        "category": "Revenue operations assistant",
                        "wedge": "Call-to-follow-up automation",
                        "value_prop": "Reduce lead leakage by 30%",
                    },
                    "meta": _meta("inference", 0.76),
                },
            ],
            "proposals": [
                {
                    "decision_key": "positioning",
                    "options": [
                        {
                            "id": "pos_opt_1",
                            "label": "Revenue Operations Assistant",
                            "description": "Position as a RevOps tool that automates follow-up workflows",
                            "reasoning": "Aligns with buyer's operational pain and budget category",
                        },
                        {
                            "id": "pos_opt_2",
                            "label": "AI Sales Copilot",
                            "description": "Position as an AI assistant that augments sales reps",
                            "reasoning": "Taps into AI hype but risks crowded positioning",
                        },
                    ],
                    "recommended_option_id": "pos_opt_1",
                    "rationale": "RevOps framing aligns with buyer pain from intake and evidence.",
                    "meta": _meta("inference", 0.76),
                },
            ],
            "facts": [
                {
                    "claim": "Revenue operations is a growing category with clear budget ownership",
                    "confidence": 0.76,
                    "sources": ["https://example.com/revops-report"],
                },
            ],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": [],
            "sources": ["https://example.com/revops-report"],
            "citations": [],
            "execution_time_ms": 5,
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "model": "stub"},
        }
        return SubAgentOutput(artifact=artifact, agent_output=agent_output)


class StubWedgeBuilder(BaseSubAgent):
    """Stub that returns fixture positioning wedge data."""

    name = "wedge_builder"
    pillar = "positioning_pricing"
    step_number = 2
    total_steps = 4

    def build_prompt(
        self,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
    ) -> str:
        return ""

    def parse_response(
        self,
        raw: dict[str, Any],
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {}

    def run(
        self,
        run_id: str,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
        round_num: int = 0,
    ) -> SubAgentOutput:
        artifact = _stub_artifact(
            self.name, run_id, round_num,
            ReasoningStep(step=1, action="analysis", thought="Building positioning wedge (stub)", confidence=0.74),
        )
        agent_output = {
            "agent": self.name,
            "agent_version": self.version,
            "pillar": self.pillar,
            "run_id": run_id,
            "produced_at": _now(),
            "patches": [
                {
                    "op": "replace",
                    "path": "/pillars/positioning_pricing/wedge_detail",
                    "value": {
                        "primary_wedge": "Call-to-follow-up automation",
                        "wedge_narrative": (
                            "Every missed follow-up is a leaked deal. Our tool automatically "
                            "captures action items from sales calls and triggers personalized "
                            "follow-ups within minutes — not days."
                        ),
                        "competitive_differentiation": "Only solution that automates the full call-to-follow-up workflow",
                        "proof_points": [
                            "Competitor Alpha requires manual follow-up tracking",
                            "Competitor Beta has no call integration",
                        ],
                    },
                    "meta": _meta("inference", 0.74),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [
                {
                    "claim": "Speed-to-follow-up is a top-3 buying criterion for sales leaders",
                    "confidence": 0.58,
                    "sources": [],
                },
            ],
            "risks": [],
            "required_inputs": [],
            "node_updates": [],
            "sources": [],
            "citations": [],
            "execution_time_ms": 5,
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "model": "stub"},
        }
        return SubAgentOutput(artifact=artifact, agent_output=agent_output)


class StubPriceModeler(BaseSubAgent):
    """Stub that returns fixture pricing model with metric, tiers, and decision proposals."""

    name = "price_modeler"
    pillar = "positioning_pricing"
    step_number = 3
    total_steps = 4

    def build_prompt(
        self,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
    ) -> str:
        return ""

    def parse_response(
        self,
        raw: dict[str, Any],
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {}

    def run(
        self,
        run_id: str,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
        round_num: int = 0,
    ) -> SubAgentOutput:
        artifact = _stub_artifact(
            self.name, run_id, round_num,
            ReasoningStep(step=1, action="analysis", thought="Modeling pricing structure (stub)", confidence=0.72),
        )
        agent_output = {
            "agent": self.name,
            "agent_version": self.version,
            "pillar": self.pillar,
            "run_id": run_id,
            "produced_at": _now(),
            "patches": [
                {
                    "op": "replace",
                    "path": "/decisions/pricing/metric",
                    "value": "per_seat",
                    "meta": _meta("inference", 0.72),
                },
                {
                    "op": "replace",
                    "path": "/decisions/pricing/tiers",
                    "value": [
                        {"name": "Starter", "price": 49, "features": ["5 users", "Basic follow-up", "Email only"]},
                        {"name": "Growth", "price": 149, "features": ["25 users", "Advanced follow-up", "CRM sync"]},
                        {"name": "Scale", "price": 349, "features": ["Unlimited users", "Custom workflows", "API access"]},
                    ],
                    "meta": _meta("inference", 0.68),
                },
                {
                    "op": "replace",
                    "path": "/decisions/pricing/price_to_test",
                    "value": 99,
                    "meta": _meta("inference", 0.66),
                },
            ],
            "proposals": [
                {
                    "decision_key": "pricing",
                    "options": [
                        {
                            "id": "price_opt_1",
                            "label": "Per-seat tiered",
                            "description": "Per-seat pricing with Starter ($49), Growth ($149), Scale ($349) tiers",
                            "reasoning": "Matches competitor pricing models and scales with team size",
                        },
                        {
                            "id": "price_opt_2",
                            "label": "Flat rate",
                            "description": "Flat monthly fee of $99 regardless of team size",
                            "reasoning": "Simpler to sell but may leave money on the table with larger teams",
                        },
                    ],
                    "recommended_option_id": "price_opt_1",
                    "rationale": "Per-seat tiered pricing closest to evidence anchors and competitive norms.",
                    "meta": _meta("inference", 0.72),
                },
            ],
            "facts": [
                {
                    "claim": "Competitor Alpha charges $75/seat; Competitor Beta charges $25 flat rate",
                    "confidence": 0.78,
                    "sources": ["https://example.com/competitor-alpha"],
                },
            ],
            "assumptions": [
                {
                    "claim": "Buyers will accept per-seat pricing over flat rate",
                    "confidence": 0.58,
                    "sources": [],
                },
            ],
            "risks": [],
            "required_inputs": [],
            "node_updates": [],
            "sources": ["https://example.com/competitor-alpha"],
            "citations": [],
            "execution_time_ms": 5,
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "model": "stub"},
        }
        return SubAgentOutput(artifact=artifact, agent_output=agent_output)


class StubPPSynthesizer(BaseSubAgent):
    """Stub that returns fixture positioning & pricing summary."""

    name = "pp_synthesizer"
    pillar = "positioning_pricing"
    step_number = 4
    total_steps = 4

    def build_prompt(
        self,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
    ) -> str:
        return ""

    def parse_response(
        self,
        raw: dict[str, Any],
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {}

    def run(
        self,
        run_id: str,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
        round_num: int = 0,
    ) -> SubAgentOutput:
        artifact = _stub_artifact(
            self.name, run_id, round_num,
            ReasoningStep(step=1, action="synthesis", thought="Synthesizing positioning and pricing (stub)", confidence=0.74),
        )
        agent_output = {
            "agent": self.name,
            "agent_version": self.version,
            "pillar": self.pillar,
            "run_id": run_id,
            "produced_at": _now(),
            "patches": [
                {
                    "op": "replace",
                    "path": "/pillars/positioning_pricing/summary",
                    "value": (
                        "Position as a Revenue Operations Assistant leading with call-to-follow-up automation. "
                        "Per-seat tiered pricing: Starter ($49), Growth ($149), Scale ($349). "
                        "Test price point: $99/seat. Key wedge: only solution automating full call-to-follow-up workflow."
                    ),
                    "meta": _meta("inference", 0.74, ["https://example.com/revops-report"]),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": [
                {
                    "node_id": "pillar.positioning_pricing",
                    "updates": {
                        "summary": "RevOps positioning with per-seat tiered pricing; test at $99/seat.",
                        "status": "complete",
                    },
                },
            ],
            "sources": [],
            "citations": [],
            "execution_time_ms": 5,
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "model": "stub"},
        }
        return SubAgentOutput(artifact=artifact, agent_output=agent_output)


def build_pp_stub_cluster() -> PillarCluster:
    """Create a PillarCluster with all Positioning & Pricing stub sub-agents."""
    return PillarCluster(
        pillar="positioning_pricing",
        sub_agents=[
            StubCategoryFramer(),
            StubWedgeBuilder(),
            StubPriceModeler(),
            StubPPSynthesizer(),
        ],
    )
