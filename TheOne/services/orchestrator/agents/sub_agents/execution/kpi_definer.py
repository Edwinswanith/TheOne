"""KPIDefiner — second sub-agent in the Execution cluster (NEW).

Defines KPI thresholds for each execution phase based on playbook context,
sales motion, and pricing model. Includes leading and lagging indicators
to enable early detection of execution problems.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class KPIDefiner(BaseSubAgent):
    """Defines phase-specific KPI thresholds with leading/lagging indicators."""

    name = "kpi_definer"
    pillar = "execution"
    step_number = 2
    total_steps = 4
    uses_external_search = False

    # ------------------------------------------------------------------
    # Prompt
    # ------------------------------------------------------------------

    def build_prompt(
        self,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
    ) -> str:
        idea = state.get("idea", {})
        constraints = state.get("constraints", {})
        decisions = state.get("decisions", {})
        ctx = cluster_context or {}

        # Gather decisions
        sales_motion_decision = decisions.get("sales_motion", {})
        pricing_decision = decisions.get("pricing", {})
        channel_decision = decisions.get("channels", {})

        # Pull playbook context from prior sub-agent
        playbook_output = ctx.get("playbook_builder", {})
        playbook_data = None
        kill_criteria = None
        for patch in playbook_output.get("patches", []):
            if patch.get("path") == "/pillars/execution/playbook":
                playbook_data = patch.get("value", {})
            elif patch.get("path") == "/pillars/execution/kill_criteria":
                kill_criteria = patch.get("value", [])

        phases = playbook_data.get("phases", []) if playbook_data else []
        chosen_track = (
            playbook_data.get("chosen_track", "") if playbook_data else ""
        )

        prompt = f"""You are a KPI and metrics specialist for go-to-market execution. \
Define measurable KPI thresholds for each execution phase.

Product context:
Name: {idea.get("name", "")}
Category: {idea.get("category", "")}

Execution context:
Chosen track: {chosen_track}
Phases: {json.dumps(phases) if phases else "Not available"}
Kill criteria: {json.dumps(kill_criteria) if kill_criteria else "Not available"}

Decisions:
Sales motion: {json.dumps(sales_motion_decision) if sales_motion_decision else "Not yet decided"}
Pricing: {json.dumps(pricing_decision) if pricing_decision else "Not yet decided"}
Channels: {json.dumps(channel_decision) if channel_decision else "Not yet decided"}

Constraints:
- Team size: {constraints.get("team_size", "")}
- Timeline: {constraints.get("timeline_weeks", "")} weeks
- Budget: ${constraints.get("budget_usd_monthly", "")} monthly

{"Changed decision: " + changed_decision if changed_decision else "Initial analysis"}

For each phase, define KPI thresholds with both leading indicators (predictive, \
early-warning metrics) and lagging indicators (outcome metrics). KPIs should \
be specific, measurable, and tied to the chosen execution track and sales motion.

Return a JSON object with these keys:
{{
  "kpi_thresholds": [
    {{
      "phase": "string (matching phase name from playbook)",
      "duration": "string",
      "leading_indicators": [
        {{
          "metric": "string",
          "target": "string (specific number or percentage)",
          "measurement_method": "string",
          "frequency": "daily | weekly | biweekly | monthly",
          "warning_threshold": "string (value that triggers review)",
          "rationale": "string"
        }}
      ],
      "lagging_indicators": [
        {{
          "metric": "string",
          "target": "string",
          "measurement_method": "string",
          "frequency": "weekly | monthly | quarterly",
          "minimum_acceptable": "string (below this = fail)",
          "rationale": "string"
        }}
      ],
      "phase_gate_criteria": "string (what must be true to advance to next phase)"
    }}
  ],
  "north_star_metric": {{
    "metric": "string",
    "target_30d": "string",
    "target_60d": "string",
    "target_90d": "string",
    "rationale": "string"
  }},
  "dashboard_recommendations": [
    {{
      "metric_group": "string",
      "metrics": ["string"],
      "update_frequency": "string"
    }}
  ]
}}"""

        if feedback:
            prompt += (
                "\n\nOrchestrator feedback for this round:\n"
                + (json.dumps(feedback) if not isinstance(feedback, str) else feedback)
            )

        return prompt

    # ------------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------------

    def parse_response(
        self,
        raw: dict[str, Any],
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        patches: list[dict[str, Any]] = []
        facts: list[dict[str, Any]] = []
        assumptions: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []
        reasoning_steps: list[dict[str, Any]] = []

        kpi_thresholds = raw.get("kpi_thresholds", [])
        north_star = raw.get("north_star_metric", {})
        dashboard_recs = raw.get("dashboard_recommendations", [])

        # --- KPI thresholds ---
        if kpi_thresholds:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/kpi_thresholds",
                "value": kpi_thresholds,
                "meta": self.meta("inference", 0.7),
            })

            total_leading = sum(
                len(phase.get("leading_indicators", []))
                for phase in kpi_thresholds
            )
            total_lagging = sum(
                len(phase.get("lagging_indicators", []))
                for phase in kpi_thresholds
            )

            facts.append({
                "claim": (
                    f"Defined KPIs across {len(kpi_thresholds)} phases: "
                    f"{total_leading} leading and {total_lagging} lagging indicators"
                ),
                "confidence": 0.7,
                "sources": [],
            })

            # Check for phases without gate criteria
            ungated = [
                p for p in kpi_thresholds
                if not p.get("phase_gate_criteria")
            ]
            if ungated:
                risks.append({
                    "id": "risk_ungated_phases",
                    "severity": "medium",
                    "description": (
                        f"{len(ungated)} execution phases lack phase-gate "
                        "criteria for advancement"
                    ),
                    "mitigation": "Define explicit go/no-go criteria for each phase",
                })

            reasoning_steps.append({
                "action": "kpi_definition",
                "thought": (
                    f"Defined {total_leading} leading + {total_lagging} lagging "
                    f"indicators across {len(kpi_thresholds)} phases"
                ),
                "confidence": 0.7,
            })

        # --- North star metric ---
        if north_star:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/north_star_metric",
                "value": north_star,
                "meta": self.meta("inference", 0.7),
            })

            facts.append({
                "claim": (
                    f"North star metric: {north_star.get('metric', 'undefined')} "
                    f"(30d target: {north_star.get('target_30d', 'N/A')})"
                ),
                "confidence": 0.7,
                "sources": [],
            })

            # North star targets are assumptions until validated
            assumptions.append({
                "claim": (
                    f"North star targets ({north_star.get('target_30d', '')}, "
                    f"{north_star.get('target_60d', '')}, "
                    f"{north_star.get('target_90d', '')}) are based on "
                    "industry benchmarks and team capacity estimates"
                ),
                "confidence": 0.55,
                "sources": [],
            })

            reasoning_steps.append({
                "action": "north_star_selection",
                "thought": (
                    f"Selected north star: {north_star.get('metric', '')} — "
                    f"{north_star.get('rationale', '')}"
                ),
                "confidence": 0.7,
            })

        # --- Dashboard recommendations ---
        if dashboard_recs:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/dashboard_recommendations",
                "value": dashboard_recs,
                "meta": self.meta("inference", 0.65),
            })

        return {
            "patches": patches,
            "proposals": [],
            "facts": facts,
            "assumptions": assumptions,
            "risks": risks,
            "required_inputs": [],
            "node_updates": [],
            "reasoning_steps": reasoning_steps,
            "_confidence": 0.7,
            "_summary": (
                f"KPI definition complete: {len(kpi_thresholds)} phase thresholds, "
                f"north star: {north_star.get('metric', 'N/A')}"
            ),
        }
