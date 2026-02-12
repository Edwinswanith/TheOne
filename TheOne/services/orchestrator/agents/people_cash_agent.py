"""People and cash agent — defines team structure and financial plan."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent


class PeopleCashAgent(BaseAgent):
    """Generates people plan and cash flow projection."""

    name = "people_cash_agent"
    pillar = "execution"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Build people and cash plan prompt."""
        idea = state.get("idea", {})
        constraints = state.get("constraints", {})
        decisions = state.get("decisions", {})
        sales_motion = decisions.get("sales_motion", {}).get("motion", "unset")

        prompt = f"""You are a financial and HR strategist. Define team structure and financial plan.

Product:
Name: {idea.get('name', '')}
Category: {idea.get('category', '')}

Constraints:
Team size: {constraints.get('team_size', '')}
Timeline: {constraints.get('timeline_weeks', '')} weeks
Budget: ${constraints.get('budget_usd_monthly', '')} monthly

Sales motion: {sales_motion}

Return JSON:
{{
  "summary": "string (people and cash summary)",
  "nodes": ["string (node IDs like 'people.team_structure', 'cash.runway')"],
  "team_structure": [
    {{
      "role": "string",
      "count": "number",
      "priority": "immediate | phase_2 | phase_3",
      "rationale": "string"
    }}
  ],
  "financial_plan": {{
    "monthly_burn": "number",
    "runway_months": "number",
    "revenue_assumptions": ["string"],
    "cost_breakdown": {{
      "personnel": "number",
      "infrastructure": "number",
      "marketing": "number",
      "other": "number"
    }}
  }},
  "funding_needs": {{
    "amount": "number",
    "timing": "string",
    "use_of_funds": ["string"]
  }}
}}
"""
        return prompt

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse people and cash plan into patches."""
        patches = []
        facts = []
        assumptions = []

        summary = raw.get("summary", "")
        nodes = raw.get("nodes", [])
        team_structure = raw.get("team_structure", [])
        financial_plan = raw.get("financial_plan", {})
        funding_needs = raw.get("funding_needs", {})

        if summary:
            patches.append({
                "op": "replace",
                "path": "/pillars/execution/summary",
                "value": summary,
                "meta": self.meta("inference", 0.7, [])
            })

        if nodes:
            patches.append({
                "op": "replace",
                "path": "/pillars/execution/nodes",
                "value": nodes,
                "meta": self.meta("inference", 0.7, [])
            })

        if team_structure:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/team_structure",
                "value": team_structure,
                "meta": self.meta("inference", 0.7, [])
            })

            immediate_hires = len([r for r in team_structure if r.get("priority") == "immediate"])
            facts.append({
                "claim": f"Identified {immediate_hires} immediate hiring needs",
                "confidence": 0.7,
                "sources": []
            })

        if financial_plan:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/financial_plan",
                "value": financial_plan,
                "meta": self.meta("inference", 0.65, [])
            })

            # Revenue assumptions are assumptions, not facts
            for assumption_text in financial_plan.get("revenue_assumptions", []):
                assumptions.append({
                    "claim": assumption_text,
                    "confidence": 0.5,
                    "reason": "Revenue projection based on market assumptions"
                })

        if funding_needs:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/funding_needs",
                "value": funding_needs,
                "meta": self.meta("inference", 0.65, [])
            })

        return {
            "patches": patches,
            "proposals": [],
            "facts": facts,
            "assumptions": assumptions,
            "risks": [],
            "required_inputs": [],
            "node_updates": []
        }
