"""Positioning agent — generates positioning framework options."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent


class PositioningAgent(BaseAgent):
    """Generates positioning options based on ICP and competitive landscape."""

    name = "positioning_agent"
    pillar = "positioning_pricing"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Build positioning generation prompt."""
        idea = state.get("idea", {})
        decisions = state.get("decisions", {})
        icp_decision = decisions.get("icp", {})
        selected_icp_id = icp_decision.get("selected_option_id", "")
        evidence = state.get("evidence", {})
        competitors = evidence.get("competitors", [])

        prompt = f"""You are a positioning strategist. Generate 2-3 positioning framework options.

Product:
Name: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Problem: {idea.get('problem', '')}

Selected ICP: {selected_icp_id}

Competitive context:
{competitors[:3]}  # First 3 competitors

Return JSON:
{{
  "options": [
    {{
      "id": "pos_1",
      "title": "string (e.g., 'Category Creator')",
      "frame": "string (the positioning statement)",
      "differentiation": "string",
      "proof_points": ["string"],
      "messaging_pillars": ["string"],
      "confidence": 0.8,
      "rationale": "string"
    }}
  ],
  "recommended_id": "pos_1"
}}
"""
        return prompt

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse positioning into patches and proposals."""
        patches = []
        proposals = []
        facts = []

        options = raw.get("options", [])
        recommended_id = raw.get("recommended_id", options[0].get("id") if options else "")

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

            # Create positioning decision proposal
            proposals.append({
                "decision_key": "positioning",
                "options": decision_options,
                "recommended_option_id": recommended_id,
                "rationale": "Positioning options aligned with ICP and competitive differentiation"
            })

            # Patch the positioning frame
            selected_option = options[0]  # Default to first
            patches.append({
                "op": "replace",
                "path": "/decisions/positioning/frame",
                "value": selected_option.get("frame"),
                "meta": self.meta("inference", 0.75, [])
            })

            # Update market_to_money pillar summary
            patches.append({
                "op": "replace",
                "path": "/pillars/positioning_pricing/summary",
                "value": f"Positioning: {selected_option.get('title')} - {selected_option.get('differentiation')}",
                "meta": self.meta("inference", 0.75, [])
            })

            facts.append({
                "claim": f"Generated {len(options)} positioning frameworks based on competitive analysis",
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
