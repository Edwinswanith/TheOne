"""Product & Tech stub sub-agents for testing."""
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
        pillar="product_tech",
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


class StubFeatureScoper(BaseSubAgent):
    """Stub that returns fixture MVP features and roadmap phases."""

    name = "feature_scoper"
    pillar = "product_tech"
    step_number = 1
    total_steps = 3

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
            ReasoningStep(step=1, action="analysis", thought="Scoping MVP features and roadmap (stub)", confidence=0.75),
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
                    "path": "/pillars/product_tech/mvp_features",
                    "value": [
                        {
                            "feature": "Call summarization",
                            "priority": "P0",
                            "effort_weeks": 3,
                            "description": "Automatically summarize sales calls and extract key points",
                        },
                        {
                            "feature": "Follow-up extraction",
                            "priority": "P0",
                            "effort_weeks": 2,
                            "description": "Identify action items and next steps from call transcripts",
                        },
                        {
                            "feature": "CRM sync",
                            "priority": "P0",
                            "effort_weeks": 4,
                            "description": "Two-way sync with HubSpot and Salesforce",
                        },
                        {
                            "feature": "Automated follow-up triggers",
                            "priority": "P1",
                            "effort_weeks": 3,
                            "description": "Auto-send personalized follow-ups based on call outcomes",
                        },
                    ],
                    "meta": _meta("inference", 0.75),
                },
                {
                    "op": "replace",
                    "path": "/pillars/product_tech/roadmap_phases",
                    "value": [
                        {
                            "phase": "MVP",
                            "duration_weeks": 8,
                            "features": ["Call summarization", "Follow-up extraction", "CRM sync"],
                            "goal": "Core automation loop working end-to-end",
                        },
                        {
                            "phase": "V2",
                            "duration_weeks": 6,
                            "features": ["Automated follow-up triggers", "Analytics dashboard", "Team management"],
                            "goal": "Self-serve product with multi-user support",
                        },
                        {
                            "phase": "V3",
                            "duration_weeks": 8,
                            "features": ["API access", "Custom workflows", "Enterprise SSO"],
                            "goal": "Enterprise readiness and platform extensibility",
                        },
                    ],
                    "meta": _meta("inference", 0.70),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [
                {
                    "claim": "MVP can be delivered in 8 weeks with a team of 2 engineers",
                    "confidence": 0.55,
                    "sources": [],
                },
            ],
            "risks": [
                {
                    "id": "risk_pt_01",
                    "description": "CRM integration may take longer than estimated due to API complexity",
                    "severity": "medium",
                    "mitigation": "Start with HubSpot (simpler API) and defer Salesforce to V2 if needed",
                },
            ],
            "required_inputs": [],
            "node_updates": [],
            "sources": [],
            "citations": [],
            "execution_time_ms": 5,
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "model": "stub"},
        }
        return SubAgentOutput(artifact=artifact, agent_output=agent_output)


class StubFeasibilityChecker(BaseSubAgent):
    """Stub that returns fixture security plan, feasibility flags, and compliance assessment."""

    name = "feasibility_checker"
    pillar = "product_tech"
    step_number = 2
    total_steps = 3

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
        compliance = state.get("constraints", {}).get("compliance_level", "none")
        security_plan = (
            "Data retention policy + encrypted transcript storage"
            if compliance in {"medium", "high"}
            else "Baseline logging and role-based access"
        )

        artifact = _stub_artifact(
            self.name, run_id, round_num,
            ReasoningStep(step=1, action="analysis", thought="Checking technical feasibility (stub)", confidence=0.68),
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
                    "path": "/pillars/product_tech/security_plan",
                    "value": security_plan,
                    "meta": _meta("inference", 0.64),
                },
                {
                    "op": "replace",
                    "path": "/pillars/product_tech/feasibility_flags",
                    "value": {
                        "call_recording_api": {"feasible": True, "risk": "low", "notes": "Multiple proven APIs available (Twilio, Recall.ai)"},
                        "llm_summarization": {"feasible": True, "risk": "low", "notes": "GPT-4 / Gemini proven for call summarization"},
                        "crm_integration": {"feasible": True, "risk": "medium", "notes": "HubSpot API well-documented; Salesforce more complex"},
                        "real_time_processing": {"feasible": True, "risk": "medium", "notes": "Requires async pipeline; latency target <5min"},
                    },
                    "meta": _meta("inference", 0.68),
                },
                {
                    "op": "replace",
                    "path": "/pillars/product_tech/compliance_assessment",
                    "value": {
                        "level": compliance,
                        "requirements": [
                            "Call recording consent (two-party states)",
                            "Data encryption at rest and in transit",
                            "User data deletion on request (GDPR/CCPA)",
                        ] if compliance != "none" else ["Basic data handling best practices"],
                        "gaps": ["No SOC2 certification yet"] if compliance in {"medium", "high"} else [],
                    },
                    "meta": _meta("inference", 0.64),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [
                {
                    "claim": "Call recording APIs handle consent management automatically",
                    "confidence": 0.50,
                    "sources": [],
                },
            ],
            "risks": [
                {
                    "id": "risk_pt_02",
                    "description": "Call recording consent requirements vary by state and may delay launch",
                    "severity": "high" if compliance in {"medium", "high"} else "low",
                    "mitigation": "Use a recording API that handles consent, start in one-party consent states",
                },
            ],
            "required_inputs": [],
            "node_updates": [],
            "sources": [],
            "citations": [],
            "execution_time_ms": 5,
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "model": "stub"},
        }
        return SubAgentOutput(artifact=artifact, agent_output=agent_output)


class StubPTSynthesizer(BaseSubAgent):
    """Stub that returns fixture product & tech summary."""

    name = "pt_synthesizer"
    pillar = "product_tech"
    step_number = 3
    total_steps = 3

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
            ReasoningStep(step=1, action="synthesis", thought="Synthesizing product and tech strategy (stub)", confidence=0.72),
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
                    "path": "/pillars/product_tech/summary",
                    "value": (
                        "MVP in 8 weeks: call summarization, follow-up extraction, CRM sync (HubSpot first). "
                        "All core features are technically feasible with low-medium risk. "
                        "Key risk: CRM integration complexity and call recording consent requirements."
                    ),
                    "meta": _meta("inference", 0.72),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": [
                {
                    "node_id": "pillar.product_tech",
                    "updates": {
                        "summary": "8-week MVP: summarization, follow-ups, CRM sync. All features feasible.",
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


def build_pt_stub_cluster() -> PillarCluster:
    """Create a PillarCluster with all Product & Tech stub sub-agents."""
    return PillarCluster(
        pillar="product_tech",
        sub_agents=[
            StubFeatureScoper(),
            StubFeasibilityChecker(),
            StubPTSynthesizer(),
        ],
    )
