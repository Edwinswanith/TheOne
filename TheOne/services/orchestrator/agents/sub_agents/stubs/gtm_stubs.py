"""Go-to-Market stub sub-agents for testing."""
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
        pillar="go_to_market",
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


class StubChannelResearcher(BaseSubAgent):
    """Stub that returns fixture channel research with decision proposals."""

    name = "channel_researcher"
    pillar = "go_to_market"
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
            ReasoningStep(step=1, action="search_execution", thought="Researching acquisition channels (stub)", confidence=0.74),
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
                    "path": "/decisions/channels/primary",
                    "value": "linkedin_outbound",
                    "meta": _meta("inference", 0.74),
                },
                {
                    "op": "replace",
                    "path": "/decisions/channels/secondary",
                    "value": "founder_network",
                    "meta": _meta("inference", 0.61),
                },
                {
                    "op": "replace",
                    "path": "/decisions/channels/primary_channels",
                    "value": ["linkedin_outbound"],
                    "meta": _meta("inference", 0.74),
                },
            ],
            "proposals": [
                {
                    "decision_key": "channels",
                    "options": [
                        {
                            "id": "chan_opt_1",
                            "label": "LinkedIn Outbound",
                            "description": "Direct outbound via LinkedIn to sales leaders at target companies",
                            "reasoning": "Highest signal density for reaching Head of Sales at 50-200 employee companies",
                        },
                        {
                            "id": "chan_opt_2",
                            "label": "Content + SEO",
                            "description": "Build thought leadership content and organic search presence",
                            "reasoning": "Scalable but slower to generate pipeline; better as secondary play",
                        },
                        {
                            "id": "chan_opt_3",
                            "label": "Product-Led Growth",
                            "description": "Free tier with self-serve upgrade path",
                            "reasoning": "Works well for SMB but requires more product investment upfront",
                        },
                    ],
                    "recommended_option_id": "chan_opt_1",
                    "rationale": "Strongest signal from channel evidence set for reaching target ICP.",
                    "meta": _meta("inference", 0.74),
                },
            ],
            "facts": [
                {
                    "claim": "LinkedIn outbound has the highest response rate for reaching B2B sales leaders",
                    "confidence": 0.74,
                    "sources": ["https://example.com/channel-research"],
                },
            ],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": [],
            "sources": ["https://example.com/channel-research"],
            "citations": [],
            "execution_time_ms": 5,
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "model": "stub"},
        }
        return SubAgentOutput(artifact=artifact, agent_output=agent_output)


class StubMotionDesigner(BaseSubAgent):
    """Stub that returns fixture sales motion design with decision proposals."""

    name = "motion_designer"
    pillar = "go_to_market"
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
            ReasoningStep(step=1, action="analysis", thought="Designing sales motion (stub)", confidence=0.72),
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
                    "path": "/decisions/sales_motion/motion",
                    "value": "outbound_led",
                    "meta": _meta("inference", 0.72),
                },
                {
                    "op": "replace",
                    "path": "/pillars/go_to_market/motion_detail",
                    "value": {
                        "primary_motion": "outbound_led",
                        "playbook_summary": "Founder-led outbound via LinkedIn, transitioning to SDR-led after PMF.",
                        "cadence": {
                            "touchpoints": 5,
                            "duration_days": 14,
                            "channels": ["LinkedIn", "Email", "Phone"],
                        },
                        "conversion_targets": {
                            "connect_rate": 0.25,
                            "reply_rate": 0.08,
                            "demo_rate": 0.03,
                        },
                    },
                    "meta": _meta("inference", 0.72),
                },
            ],
            "proposals": [
                {
                    "decision_key": "sales_motion",
                    "options": [
                        {
                            "id": "sales_opt_1",
                            "label": "Outbound-Led",
                            "description": "Founder-led outbound with structured cadence and personalization",
                            "reasoning": "Best fit for reaching target ICP through LinkedIn channel",
                        },
                        {
                            "id": "sales_opt_2",
                            "label": "Product-Led Sales",
                            "description": "Free tier drives signups; sales assists upgrade to paid",
                            "reasoning": "Lower cost but requires more product maturity",
                        },
                    ],
                    "recommended_option_id": "sales_opt_1",
                    "rationale": "Best fit for current ICP/channel combination.",
                    "meta": _meta("inference", 0.72),
                },
            ],
            "facts": [],
            "assumptions": [
                {
                    "claim": "Founder-led outbound can achieve 3% demo rate on LinkedIn",
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


class StubMessageCrafter(BaseSubAgent):
    """Stub that returns fixture messaging templates."""

    name = "message_crafter"
    pillar = "go_to_market"
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
            ReasoningStep(step=1, action="synthesis", thought="Crafting messaging templates (stub)", confidence=0.70),
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
                    "path": "/pillars/go_to_market/messaging_templates",
                    "value": [
                        {
                            "type": "linkedin_connection",
                            "subject": None,
                            "body": (
                                "Hi {{first_name}}, noticed your team at {{company}} is growing the sales org. "
                                "Curious — how are you handling follow-up on sales calls today?"
                            ),
                            "target_persona": "Head of Sales",
                            "channel": "linkedin",
                        },
                        {
                            "type": "cold_email",
                            "subject": "{{company}}'s follow-up problem",
                            "body": (
                                "{{first_name}},\n\nMost sales teams lose 30% of deals to slow follow-up. "
                                "We built a tool that automatically captures action items from calls and "
                                "triggers follow-ups within minutes.\n\nWorth a quick look?"
                            ),
                            "target_persona": "Head of Sales",
                            "channel": "email",
                        },
                        {
                            "type": "landing_page_headline",
                            "subject": None,
                            "body": "Stop losing deals to slow follow-up. Automate every post-call action.",
                            "target_persona": "All visitors",
                            "channel": "website",
                        },
                    ],
                    "meta": _meta("inference", 0.70),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [
                {
                    "claim": "Personalized LinkedIn outreach achieves 2-3x higher response than generic messages",
                    "confidence": 0.60,
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


class StubGTMSynthesizer(BaseSubAgent):
    """Stub that returns fixture go-to-market pillar summary."""

    name = "gtm_synthesizer"
    pillar = "go_to_market"
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
            ReasoningStep(step=1, action="synthesis", thought="Synthesizing go-to-market strategy (stub)", confidence=0.72),
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
                    "path": "/pillars/go_to_market/summary",
                    "value": (
                        "Outbound-led GTM via LinkedIn targeting sales leaders at 50-200 employee companies. "
                        "Founder-led cadence with 5 touchpoints over 14 days. Secondary channel: founder network. "
                        "Messaging leads with follow-up automation value prop."
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
                    "node_id": "pillar.go_to_market",
                    "updates": {
                        "summary": "Outbound-led via LinkedIn; founder-led cadence targeting sales leaders.",
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


def build_gtm_stub_cluster() -> PillarCluster:
    """Create a PillarCluster with all Go-to-Market stub sub-agents."""
    return PillarCluster(
        pillar="go_to_market",
        sub_agents=[
            StubChannelResearcher(),
            StubMotionDesigner(),
            StubMessageCrafter(),
            StubGTMSynthesizer(),
        ],
    )
