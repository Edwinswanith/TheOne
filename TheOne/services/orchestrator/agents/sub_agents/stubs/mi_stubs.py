"""Market Intelligence stub sub-agents for testing."""
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
        pillar="market_intelligence",
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


class StubMarketScanner(BaseSubAgent):
    """Stub that returns fixture evidence sources and competitor data."""

    name = "market_scanner"
    pillar = "market_intelligence"
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
            ReasoningStep(step=1, action="search_execution", thought="Scanning market landscape (stub)", confidence=0.85),
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
                    "path": "/evidence/sources",
                    "value": [
                        {
                            "id": "src_mi_1",
                            "url": "https://example.com/market-report",
                            "title": "Market Analysis Report 2025",
                            "snippets": ["The market for AI-powered sales tools is growing at 35% CAGR"],
                            "quality_score": 0.88,
                        },
                        {
                            "id": "src_mi_2",
                            "url": "https://example.com/industry-overview",
                            "title": "Industry Overview: Sales Automation",
                            "snippets": ["Key players include Gong, Chorus, and Outreach"],
                            "quality_score": 0.82,
                        },
                    ],
                    "meta": _meta("evidence", 0.88, ["https://example.com/market-report"]),
                },
                {
                    "op": "replace",
                    "path": "/evidence/competitors",
                    "value": [
                        {
                            "name": "Competitor Alpha",
                            "url": "https://example.com/competitor-alpha",
                            "positioning": "Enterprise-grade sales intelligence",
                            "pricing_model": "per_seat",
                            "target_segment": "Enterprise",
                            "strengths": ["Strong brand", "Deep analytics"],
                            "weaknesses": ["Complex setup", "Expensive"],
                            "category": "direct",
                        },
                        {
                            "name": "Competitor Beta",
                            "url": "https://example.com/competitor-beta",
                            "positioning": "Lightweight CRM add-on",
                            "pricing_model": "flat_rate",
                            "target_segment": "SMB",
                            "strengths": ["Easy onboarding", "Affordable"],
                            "weaknesses": ["Limited features", "No API"],
                            "category": "indirect",
                        },
                    ],
                    "meta": _meta("evidence", 0.81, ["https://example.com/competitor-alpha", "https://example.com/competitor-beta"]),
                },
            ],
            "proposals": [],
            "facts": [
                {
                    "claim": "AI-powered sales tools market growing at 35% CAGR",
                    "confidence": 0.88,
                    "sources": ["https://example.com/market-report"],
                },
            ],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": [],
            "sources": ["https://example.com/market-report", "https://example.com/industry-overview"],
            "citations": [],
            "execution_time_ms": 5,
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "model": "stub"},
        }
        return SubAgentOutput(artifact=artifact, agent_output=agent_output)


class StubCompetitorDeepDive(BaseSubAgent):
    """Stub that returns fixture competitor teardown data."""

    name = "competitor_deep_dive"
    pillar = "market_intelligence"
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
            ReasoningStep(step=1, action="analysis", thought="Deep-diving competitor landscape (stub)", confidence=0.80),
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
                    "path": "/evidence/teardowns",
                    "value": [
                        {
                            "competitor": "Competitor Alpha",
                            "pricing_detail": {"base_price": 75, "model": "per_seat", "source_id": "src_mi_1"},
                            "feature_gaps": ["No automated follow-up", "Manual CRM entry required"],
                            "positioning_weakness": "Over-engineered for SMB use cases",
                            "channel_footprint": {
                                "channels_observed": ["direct_sales", "webinars", "linkedin_ads"],
                                "estimated_primary": "direct_sales",
                            },
                        },
                        {
                            "competitor": "Competitor Beta",
                            "pricing_detail": {"base_price": 25, "model": "flat_rate", "source_id": "src_mi_2"},
                            "feature_gaps": ["No AI summarization", "Limited integrations"],
                            "positioning_weakness": "Too basic for growing teams",
                            "channel_footprint": {
                                "channels_observed": ["seo_blog", "product_hunt"],
                                "estimated_primary": "product_led",
                            },
                        },
                    ],
                    "meta": _meta("evidence", 0.78, ["https://example.com/competitor-alpha"]),
                },
            ],
            "proposals": [],
            "facts": [
                {
                    "claim": "Competitor Alpha charges $75/seat with no automated follow-up feature",
                    "confidence": 0.78,
                    "sources": ["https://example.com/competitor-alpha"],
                },
            ],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": [],
            "sources": ["https://example.com/competitor-alpha", "https://example.com/competitor-beta"],
            "citations": [],
            "execution_time_ms": 5,
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "model": "stub"},
        }
        return SubAgentOutput(artifact=artifact, agent_output=agent_output)


class StubWeaknessMiner(BaseSubAgent):
    """Stub that returns fixture weakness map data with gap analysis."""

    name = "weakness_miner"
    pillar = "market_intelligence"
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
            ReasoningStep(step=1, action="analysis", thought="Mining competitor weaknesses (stub)", confidence=0.76),
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
                    "path": "/evidence/weakness_map",
                    "value": [
                        {
                            "competitor": "Competitor Alpha",
                            "gap_type": "true_gap",
                            "gap_description": "No automated follow-up workflow — users must manually track and send follow-ups",
                            "exploitability": 0.85,
                            "evidence_source": "src_mi_1",
                        },
                        {
                            "competitor": "Competitor Beta",
                            "gap_type": "true_gap",
                            "gap_description": "Limited integrations — no Salesforce or HubSpot sync",
                            "exploitability": 0.72,
                            "evidence_source": "src_mi_2",
                        },
                    ],
                    "meta": _meta("evidence", 0.76, ["https://example.com/competitor-alpha"]),
                },
            ],
            "proposals": [],
            "facts": [
                {
                    "claim": "Both major competitors lack automated follow-up workflows",
                    "confidence": 0.76,
                    "sources": ["https://example.com/competitor-alpha", "https://example.com/competitor-beta"],
                },
            ],
            "assumptions": [
                {
                    "claim": "Gap in automated follow-up is exploitable within 6 months",
                    "confidence": 0.6,
                    "sources": [],
                },
            ],
            "risks": [
                {
                    "id": "risk_mi_01",
                    "description": "Competitor Alpha may ship follow-up automation in next release",
                    "severity": "medium",
                    "mitigation": "Move fast to capture early adopters before gap closes",
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


class StubMISynthesizer(BaseSubAgent):
    """Stub that returns fixture market intelligence summary."""

    name = "mi_synthesizer"
    pillar = "market_intelligence"
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
            ReasoningStep(step=1, action="synthesis", thought="Synthesizing market intelligence findings (stub)", confidence=0.80),
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
                    "path": "/pillars/market_intelligence/summary",
                    "value": (
                        "Growing market (35% CAGR) with two direct competitors. Key exploitable gap: "
                        "no automated follow-up workflows. Recommend positioning around speed-to-follow-up "
                        "and CRM integration depth."
                    ),
                    "meta": _meta("inference", 0.80, ["https://example.com/market-report"]),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": [
                {
                    "node_id": "pillar.market_intelligence",
                    "updates": {
                        "summary": "Growing market with exploitable competitor gaps in follow-up automation.",
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


def build_mi_stub_cluster() -> PillarCluster:
    """Create a PillarCluster with all Market Intelligence stub sub-agents."""
    return PillarCluster(
        pillar="market_intelligence",
        sub_agents=[
            StubMarketScanner(),
            StubCompetitorDeepDive(),
            StubWeaknessMiner(),
            StubMISynthesizer(),
        ],
    )
