"""Customer stub sub-agents for testing."""
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
        pillar="customer",
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


class StubICPResearcher(BaseSubAgent):
    """Stub that returns fixture ICP profile and decision proposals."""

    name = "icp_researcher"
    pillar = "customer"
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
            ReasoningStep(step=1, action="analysis", thought="Researching ideal customer profile (stub)", confidence=0.78),
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
                    "path": "/decisions/icp/profile",
                    "value": {
                        "buyer_role": "Head of Sales",
                        "company_size": "50-200",
                        "budget_owner": "sales_lead",
                        "trigger_event": "Hiring new reps",
                    },
                    "meta": _meta("inference", 0.78),
                },
            ],
            "proposals": [
                {
                    "decision_key": "icp",
                    "options": [
                        {
                            "id": "icp_opt_1",
                            "label": "Mid-market Sales Leaders",
                            "description": "Head of Sales at 50-200 employee companies with active hiring",
                            "reasoning": "Strong evidence of pain point alignment and budget authority",
                        },
                        {
                            "id": "icp_opt_2",
                            "label": "SMB Founders",
                            "description": "Founder/CEO at 10-50 employee companies doing their own sales",
                            "reasoning": "High urgency but lower deal value and less predictable budget",
                        },
                    ],
                    "recommended_option_id": "icp_opt_1",
                    "rationale": "Best evidence-backed fit: mid-market sales leaders show highest pain and budget authority.",
                    "meta": _meta("inference", 0.78),
                },
            ],
            "facts": [
                {
                    "claim": "Head of Sales in 50-200 employee companies are most likely to have budget authority",
                    "confidence": 0.78,
                    "sources": ["https://example.com/icp-research"],
                },
            ],
            "assumptions": [
                {
                    "claim": "Hiring new reps is a reliable trigger event for tool purchase",
                    "confidence": 0.55,
                    "sources": [],
                },
            ],
            "risks": [],
            "required_inputs": [],
            "node_updates": [],
            "sources": ["https://example.com/icp-research"],
            "citations": [],
            "execution_time_ms": 5,
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "model": "stub"},
        }
        return SubAgentOutput(artifact=artifact, agent_output=agent_output)


class StubBuyerJourneyMapper(BaseSubAgent):
    """Stub that returns fixture buyer journey mapping data."""

    name = "buyer_journey_mapper"
    pillar = "customer"
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
            ReasoningStep(step=1, action="analysis", thought="Mapping buyer journey stages (stub)", confidence=0.72),
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
                    "path": "/pillars/customer/buyer_journey",
                    "value": {
                        "awareness": {
                            "trigger": "Hiring new sales reps",
                            "channels": ["LinkedIn", "peer recommendations"],
                            "content_needs": "ROI case studies",
                        },
                        "consideration": {
                            "evaluation_criteria": ["Ease of setup", "CRM integration", "Price"],
                            "competitors_evaluated": 2,
                            "timeline_days": 14,
                        },
                        "decision": {
                            "decision_maker": "Head of Sales",
                            "influencers": ["Sales Ops", "RevOps"],
                            "deal_cycle_days": 21,
                        },
                    },
                    "meta": _meta("inference", 0.72),
                },
            ],
            "proposals": [],
            "facts": [
                {
                    "claim": "Average deal cycle for SMB sales tools is 14-21 days",
                    "confidence": 0.72,
                    "sources": ["https://example.com/buyer-journey"],
                },
            ],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": [],
            "sources": ["https://example.com/buyer-journey"],
            "citations": [],
            "execution_time_ms": 5,
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "model": "stub"},
        }
        return SubAgentOutput(artifact=artifact, agent_output=agent_output)


class StubObjectionAnalyst(BaseSubAgent):
    """Stub that returns fixture objection map data."""

    name = "objection_analyst"
    pillar = "customer"
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
            ReasoningStep(step=1, action="analysis", thought="Analyzing buyer objections (stub)", confidence=0.70),
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
                    "path": "/pillars/customer/objection_map",
                    "value": [
                        {
                            "objection": "We already use a CRM for follow-ups",
                            "frequency": "high",
                            "reframe": "CRMs track data but don't automate the actual follow-up — our tool does both.",
                            "evidence_support": "src_mi_1",
                        },
                        {
                            "objection": "Our team is too small to justify another tool",
                            "frequency": "medium",
                            "reframe": "Small teams benefit most — automate what a full-time SDR would do for a fraction of the cost.",
                            "evidence_support": None,
                        },
                        {
                            "objection": "How is this different from Competitor Alpha?",
                            "frequency": "medium",
                            "reframe": "We focus on automated follow-up workflows, which Competitor Alpha lacks entirely.",
                            "evidence_support": "src_mi_1",
                        },
                    ],
                    "meta": _meta("inference", 0.70),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [
                {
                    "claim": "CRM overlap is the most common objection for sales automation tools",
                    "confidence": 0.55,
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


class StubCustomerSynthesizer(BaseSubAgent):
    """Stub that returns fixture customer pillar summary."""

    name = "customer_synthesizer"
    pillar = "customer"
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
            ReasoningStep(step=1, action="synthesis", thought="Synthesizing customer insights (stub)", confidence=0.75),
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
                    "path": "/pillars/customer/summary",
                    "value": (
                        "Target buyer is Head of Sales at 50-200 employee companies, triggered by new rep hiring. "
                        "21-day deal cycle with CRM overlap as the primary objection. Key differentiator: "
                        "automated follow-up workflows that competitors lack."
                    ),
                    "meta": _meta("inference", 0.75),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": [
                {
                    "node_id": "pillar.customer",
                    "updates": {
                        "summary": "Mid-market sales leaders with 21-day deal cycle; automated follow-up is key differentiator.",
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


def build_customer_stub_cluster() -> PillarCluster:
    """Create a PillarCluster with all Customer stub sub-agents."""
    return PillarCluster(
        pillar="customer",
        sub_agents=[
            StubICPResearcher(),
            StubBuyerJourneyMapper(),
            StubObjectionAnalyst(),
            StubCustomerSynthesizer(),
        ],
    )
