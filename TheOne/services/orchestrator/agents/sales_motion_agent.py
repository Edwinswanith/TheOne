"""Sales motion agent — determines sales-led vs product-led approach."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent


class SalesMotionAgent(BaseAgent):
    """Generates sales motion options (outbound, inbound, PLG, partner-led)."""

    name = "sales_motion_agent"
    pillar = "go_to_market"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Build sales motion prompt."""
        idea = state.get("idea", {})
        decisions = state.get("decisions", {})
        icp_decision = decisions.get("icp", {})
        pricing_decision = decisions.get("pricing", {})
        constraints = state.get("constraints", {})

        prompt = f"""You are a sales strategy expert. Generate 2-3 sales motion options.

Product:
Name: {idea.get('name', '')}
Category: {idea.get('category', '')}

Selected ICP: {icp_decision.get('selected_option_id', '')}
Pricing metric: {pricing_decision.get('metric', '')}

Constraints:
Team size: {constraints.get('team_size', '')}
Budget: ${constraints.get('budget_usd_monthly', '')} monthly

Return JSON:
{{
  "options": [
    {{
      "id": "motion_1",
      "motion": "outbound_led | inbound_led | plg | partner_led",
      "title": "string (e.g., 'Product-Led Growth')",
      "description": "string",
      "sales_cycle_weeks": "number",
      "avg_deal_size": "number",
      "key_activities": ["string"],
      "confidence": 0.8,
      "rationale": "string"
    }}
  ],
  "recommended_id": "motion_1"
}}
"""
        return prompt

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse sales motion into patches and proposals."""
        patches = []
        proposals = []
        facts = []

        options = raw.get("options", [])
        recommended_id = raw.get("recommended_id", options[0].get("id") if options else "") if options else ""

        if options:
            # Create decision options
            decision_options = []
            for opt in options:
                decision_options.append({
                    "id": opt.get("id"),
                    "label": opt.get("title"),
                    "description": opt.get("rationale"),
                    "confidence": opt.get("confidence", 0.7),
                    "data": opt
                })

            # Create sales_motion decision proposal
            proposals.append({
                "decision_key": "sales_motion",
                "options": decision_options,
                "recommended_option_id": recommended_id,
                "rationale": "Sales motion based on ICP, pricing, and team constraints"
            })

            # Patch the motion field
            selected_option = options[0]  # Default to first
            patches.append({
                "op": "replace",
                "path": "/decisions/sales_motion/motion",
                "value": selected_option.get("motion", "unset"),
                "meta": self.meta("inference", 0.75, [])
            })

            facts.append({
                "claim": f"Recommended {selected_option.get('title')} approach based on team size and pricing",
                "confidence": 0.75,
                "sources": []
            })

        return {
            "patches": patches,
            "proposals": proposals,
            "facts": facts,
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": []
        }
