"""Execution agent — generates next actions and experiments."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent


class ExecutionAgent(BaseAgent):
    """Generates actionable next steps and validation experiments."""

    name = "execution_agent"
    pillar = "execution"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Build execution plan prompt."""
        idea = state.get("idea", {})
        decisions = state.get("decisions", {})
        constraints = state.get("constraints", {})
        pillars = state.get("pillars", {})

        prompt = f"""You are an execution strategist. Generate prioritized next actions and validation experiments.

Product:
Name: {idea.get('name', '')}

Decisions made:
ICP: {decisions.get('icp', {}).get('selected_option_id', '')}
Positioning: {decisions.get('positioning', {}).get('frame', '')}
Sales motion: {decisions.get('sales_motion', {}).get('motion', '')}

Constraints:
Timeline: {constraints.get('timeline_weeks', '')} weeks
Budget: ${constraints.get('budget_usd_monthly', '')} monthly

{"Changed decision: " + changed_decision if changed_decision else "Initial plan"}

Return JSON:
{{
  "chosen_track": "validation_sprint | outbound_sprint | landing_waitlist | pilot_onboarding",
  "next_actions": [
    {{
      "id": "string",
      "title": "string",
      "description": "string",
      "owner": "string",
      "due_weeks": "number",
      "dependencies": ["string (action IDs)"],
      "priority": "p0 | p1 | p2"
    }}
  ],
  "experiments": [
    {{
      "id": "string",
      "hypothesis": "string",
      "test_method": "string",
      "success_criteria": "string",
      "duration_weeks": "number",
      "cost_estimate": "number"
    }}
  ]
}}
"""
        return prompt

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse execution plan into patches."""
        patches = []
        facts = []

        chosen_track = raw.get("chosen_track", "validation_sprint")
        next_actions = raw.get("next_actions", [])
        experiments = raw.get("experiments", [])

        # Add revalidation action if decision changed
        if changed_decision:
            next_actions.insert(0, {
                "id": f"revalidate_{changed_decision}",
                "title": f"Revalidate {changed_decision} decision",
                "description": f"Review and validate the impact of changing {changed_decision} on downstream decisions",
                "owner": "team_lead",
                "due_weeks": 1,
                "dependencies": [],
                "priority": "p0"
            })

        if chosen_track:
            patches.append({
                "op": "replace",
                "path": "/execution/chosen_track",
                "value": chosen_track,
                "meta": self.meta("inference", 0.75, [])
            })

        if next_actions:
            patches.append({
                "op": "replace",
                "path": "/execution/next_actions",
                "value": next_actions,
                "meta": self.meta("inference", 0.75, [])
            })

            p0_count = len([a for a in next_actions if a.get("priority") == "p0"])
            facts.append({
                "claim": f"Defined {len(next_actions)} actions with {p0_count} P0 priorities",
                "confidence": 0.75,
                "sources": []
            })

        if experiments:
            patches.append({
                "op": "replace",
                "path": "/execution/experiments",
                "value": experiments,
                "meta": self.meta("inference", 0.7, [])
            })

        return {
            "patches": patches,
            "proposals": [],
            "facts": facts,
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": []
        }
