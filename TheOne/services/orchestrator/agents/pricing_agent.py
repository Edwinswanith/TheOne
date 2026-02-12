"""Pricing agent — generates pricing strategy and tier options."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent


class PricingAgent(BaseAgent):
    """Generates pricing options based on evidence anchors and ICP."""

    name = "pricing_agent"
    pillar = "positioning_pricing"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Build pricing generation prompt."""
        idea = state.get("idea", {})
        decisions = state.get("decisions", {})
        icp_decision = decisions.get("icp", {})
        evidence = state.get("evidence", {})
        pricing_anchors = evidence.get("pricing_anchors", [])

        prompt = f"""You are a pricing strategist. Generate 2-3 pricing strategy options.

Product:
Name: {idea.get('name', '')}
Category: {idea.get('category', '')}

Selected ICP: {icp_decision.get('selected_option_id', '')}

Pricing anchors from competitors:
{pricing_anchors}

Return JSON:
{{
  "metric": "string (e.g., 'per user/month', 'per API call', 'flat rate')",
  "options": [
    {{
      "id": "price_1",
      "title": "string (e.g., 'Usage-based')",
      "tiers": [
        {{
          "name": "string",
          "price": "number",
          "features": ["string"]
        }}
      ],
      "price_to_test": "number",
      "confidence": 0.8,
      "rationale": "string"
    }}
  ],
  "recommended_id": "price_1"
}}
"""
        return prompt

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse pricing into patches and proposals."""
        patches = []
        proposals = []
        facts = []

        metric = raw.get("metric", "")
        options = raw.get("options", [])
        recommended_id = raw.get("recommended_id", options[0].get("id") if options else "") if options else ""

        if metric:
            patches.append({
                "op": "replace",
                "path": "/decisions/pricing/metric",
                "value": metric,
                "meta": self.meta("inference", 0.75, [])
            })

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

            # Create pricing decision proposal
            proposals.append({
                "decision_key": "pricing",
                "options": decision_options,
                "recommended_option_id": recommended_id,
                "rationale": "Pricing options based on competitive anchors and ICP budget authority"
            })

            # Patch tiers and price to test
            selected_option = options[0]  # Default to first
            patches.append({
                "op": "replace",
                "path": "/decisions/pricing/tiers",
                "value": selected_option.get("tiers", []),
                "meta": self.meta("inference", 0.7, [])
            })

            patches.append({
                "op": "replace",
                "path": "/decisions/pricing/price_to_test",
                "value": selected_option.get("price_to_test", 0),
                "meta": self.meta("inference", 0.7, [])
            })

            facts.append({
                "claim": f"Generated {len(options)} pricing strategies with {metric} as value metric",
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
