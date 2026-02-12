"""Execution stub sub-agents for testing."""
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
        pillar="execution",
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


class StubPlaybookBuilder(BaseSubAgent):
    """Stub that returns fixture playbook, kill criteria, and next actions."""

    name = "playbook_builder"
    pillar = "execution"
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
            ReasoningStep(step=1, action="synthesis", thought="Building execution playbook (stub)", confidence=0.72),
        )

        actions = [
            {"title": "Interview 10 target buyers", "owner": "founder", "week": 1},
            {"title": "Send first 50 outbound messages", "owner": "founder", "week": 1},
            {"title": "Launch landing page with CTA", "owner": "marketing", "week": 2},
            {"title": "Run first demo batch", "owner": "founder", "week": 3},
        ]
        if changed_decision:
            actions.insert(
                0,
                {"title": f"Revalidate after {changed_decision} change", "owner": "founder", "week": 0},
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
                    "path": "/pillars/execution/playbook",
                    "value": {
                        "phases": [
                            {
                                "name": "Validation Sprint",
                                "weeks": "1-2",
                                "goals": ["Validate buyer pain", "Test messaging", "Confirm willingness to pay"],
                                "actions": actions[:2],
                            },
                            {
                                "name": "Demand Generation",
                                "weeks": "3-4",
                                "goals": ["Generate pipeline", "Run demos", "Collect objections"],
                                "actions": actions[2:],
                            },
                        ],
                        "cadence": "Weekly check-in with metrics review",
                    },
                    "meta": _meta("inference", 0.72),
                },
                {
                    "op": "replace",
                    "path": "/pillars/execution/kill_criteria",
                    "value": [
                        {
                            "criterion": "Zero demos after 100 outbound messages",
                            "threshold": "0% demo conversion on 100+ touches",
                            "action": "Pivot ICP or channel strategy",
                            "timeline": "Week 4",
                        },
                        {
                            "criterion": "No willingness to pay after 10 buyer interviews",
                            "threshold": "<10% would pay for the solution",
                            "action": "Reconsider value prop and positioning",
                            "timeline": "Week 2",
                        },
                    ],
                    "meta": _meta("inference", 0.66),
                },
                {
                    "op": "replace",
                    "path": "/execution/next_actions",
                    "value": actions,
                    "meta": _meta("inference", 0.72),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [
                {
                    "claim": "10 buyer interviews are sufficient to validate core pain hypothesis",
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


class StubKPIDefiner(BaseSubAgent):
    """Stub that returns fixture KPI thresholds."""

    name = "kpi_definer"
    pillar = "execution"
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
            ReasoningStep(step=1, action="analysis", thought="Defining KPI thresholds (stub)", confidence=0.70),
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
                    "path": "/pillars/execution/kpi_thresholds",
                    "value": [
                        {
                            "kpi": "Outbound reply rate",
                            "target": 0.05,
                            "minimum": 0.02,
                            "unit": "ratio",
                            "measurement_frequency": "weekly",
                            "owner": "founder",
                        },
                        {
                            "kpi": "Demo-to-trial conversion",
                            "target": 0.30,
                            "minimum": 0.15,
                            "unit": "ratio",
                            "measurement_frequency": "weekly",
                            "owner": "founder",
                        },
                        {
                            "kpi": "Trial-to-paid conversion",
                            "target": 0.20,
                            "minimum": 0.10,
                            "unit": "ratio",
                            "measurement_frequency": "monthly",
                            "owner": "founder",
                        },
                        {
                            "kpi": "Monthly burn rate",
                            "target": 5000,
                            "minimum": None,
                            "unit": "usd",
                            "measurement_frequency": "monthly",
                            "owner": "founder",
                        },
                        {
                            "kpi": "Buyer interviews completed",
                            "target": 10,
                            "minimum": 5,
                            "unit": "count",
                            "measurement_frequency": "biweekly",
                            "owner": "founder",
                        },
                    ],
                    "meta": _meta("inference", 0.70),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [
                {
                    "claim": "5% outbound reply rate is achievable with personalized LinkedIn messaging",
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


class StubResourcePlanner(BaseSubAgent):
    """Stub that returns fixture team plan, budget allocation, financial plan, and funding needs."""

    name = "resource_planner"
    pillar = "execution"
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
        budget = state.get("constraints", {}).get("budget_usd_monthly", 5000)
        team_size = state.get("constraints", {}).get("team_size", 1)

        artifact = _stub_artifact(
            self.name, run_id, round_num,
            ReasoningStep(step=1, action="analysis", thought="Planning resources and budget (stub)", confidence=0.68),
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
                    "path": "/pillars/execution/team_plan",
                    "value": {
                        "summary": f"Keep burn below ${budget:,} and hire one SDR only after PMF signal.",
                        "current_team_size": team_size,
                        "roles": [
                            {"role": "Founder", "focus": "Sales + Product", "allocation": 1.0},
                        ],
                        "hiring_triggers": [
                            {"role": "SDR", "trigger": "After 10 paying customers", "timeline": "Month 3-4"},
                            {"role": "Engineer", "trigger": "After $10k MRR", "timeline": "Month 4-6"},
                        ],
                    },
                    "meta": _meta("inference", 0.68),
                },
                {
                    "op": "replace",
                    "path": "/pillars/execution/budget_allocation",
                    "value": {
                        "total_monthly": budget,
                        "categories": [
                            {"category": "Infrastructure", "amount": int(budget * 0.15), "notes": "Cloud hosting, APIs"},
                            {"category": "Tools", "amount": int(budget * 0.10), "notes": "CRM, analytics, outbound tools"},
                            {"category": "Marketing", "amount": int(budget * 0.20), "notes": "LinkedIn, content, landing page"},
                            {"category": "Reserve", "amount": int(budget * 0.55), "notes": "Runway buffer and contingency"},
                        ],
                    },
                    "meta": _meta("inference", 0.66),
                },
                {
                    "op": "replace",
                    "path": "/pillars/execution/financial_plan",
                    "value": {
                        "monthly_burn": budget,
                        "runway_months": 12,
                        "break_even_target": "Month 8-10 at 20 paying customers",
                        "revenue_milestones": [
                            {"month": 3, "target_mrr": 1000, "customers": 5},
                            {"month": 6, "target_mrr": 5000, "customers": 20},
                            {"month": 12, "target_mrr": 15000, "customers": 50},
                        ],
                    },
                    "meta": _meta("inference", 0.62),
                },
                {
                    "op": "replace",
                    "path": "/pillars/execution/funding_needs",
                    "value": {
                        "current_funding": "bootstrapped",
                        "runway_months_remaining": 12,
                        "next_raise_trigger": "$10k MRR with 30%+ month-over-month growth",
                        "recommended_raise": None,
                        "use_of_funds": "Extend runway, hire first SDR and engineer",
                    },
                    "meta": _meta("inference", 0.58),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [
                {
                    "claim": f"Monthly burn of ${budget:,} is sustainable for 12 months",
                    "confidence": 0.58,
                    "sources": [],
                },
                {
                    "claim": "PMF signal arrives within 3 months of launch",
                    "confidence": 0.45,
                    "sources": [],
                },
            ],
            "risks": [
                {
                    "id": "risk_exec_01",
                    "description": "Runway may be insufficient if sales cycle is longer than expected",
                    "severity": "high",
                    "mitigation": "Set strict kill criteria and pivot fast if metrics don't hit targets",
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


class StubExecutionSynthesizer(BaseSubAgent):
    """Stub that returns fixture execution pillar summary."""

    name = "execution_synthesizer"
    pillar = "execution"
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
            ReasoningStep(step=1, action="synthesis", thought="Synthesizing execution plan (stub)", confidence=0.70),
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
                    "path": "/pillars/execution/summary",
                    "value": (
                        "Two-phase execution: Validation Sprint (weeks 1-2) to confirm buyer pain and messaging, "
                        "then Demand Generation (weeks 3-4) for pipeline building. Key KPIs: 5% outbound reply rate, "
                        "30% demo-to-trial conversion. Kill criteria set at week 4. Bootstrapped with 12-month runway. "
                        "First hire (SDR) after 10 paying customers."
                    ),
                    "meta": _meta("inference", 0.70),
                },
            ],
            "proposals": [],
            "facts": [],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": [
                {
                    "node_id": "pillar.execution",
                    "updates": {
                        "summary": "Two-phase plan: validate then generate demand. 12-month runway, hire after PMF.",
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


def build_execution_stub_cluster() -> PillarCluster:
    """Create a PillarCluster with all Execution stub sub-agents."""
    return PillarCluster(
        pillar="execution",
        sub_agents=[
            StubPlaybookBuilder(),
            StubKPIDefiner(),
            StubResourcePlanner(),
            StubExecutionSynthesizer(),
        ],
    )
