"""Product strategy agent — defines MVP scope and roadmap."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent


class ProductStrategyAgent(BaseAgent):
    """Generates product strategy and MVP definition."""

    name = "product_strategy_agent"
    pillar = "product_tech"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Build product strategy prompt."""
        idea = state.get("idea", {})
        decisions = state.get("decisions", {})
        icp_decision = decisions.get("icp", {})
        positioning_decision = decisions.get("positioning", {})
        constraints = state.get("constraints", {})

        prompt = f"""You are a product strategist. Define MVP scope and product roadmap.

Product:
Name: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Problem: {idea.get('problem', '')}

Selected ICP: {icp_decision.get('selected_option_id', '')}
Positioning: {positioning_decision.get('frame', '')}

Constraints:
Timeline: {constraints.get('timeline_weeks', '')} weeks
Team size: {constraints.get('team_size', '')}

Return JSON:
{{
  "summary": "string (product strategy summary)",
  "nodes": ["string (node IDs like 'product.mvp', 'product.core_features')"],
  "mvp_features": [
    {{
      "id": "string",
      "title": "string",
      "description": "string",
      "priority": "must_have | should_have | nice_to_have",
      "effort_weeks": "number"
    }}
  ],
  "roadmap_phases": [
    {{
      "phase": "string",
      "timeline": "string",
      "goals": ["string"]
    }}
  ]
}}
"""
        return prompt

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse product strategy into patches."""
        patches = []
        facts = []

        summary = raw.get("summary", "")
        nodes = raw.get("nodes", [])
        mvp_features = raw.get("mvp_features", [])
        roadmap_phases = raw.get("roadmap_phases", [])

        if summary:
            patches.append({
                "op": "replace",
                "path": "/pillars/product_tech/summary",
                "value": summary,
                "meta": self.meta("inference", 0.75, [])
            })

        if nodes:
            patches.append({
                "op": "replace",
                "path": "/pillars/product_tech/nodes",
                "value": nodes,
                "meta": self.meta("inference", 0.75, [])
            })

        # Add MVP features to pillar data
        if mvp_features:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/mvp_features",
                "value": mvp_features,
                "meta": self.meta("inference", 0.7, [])
            })

            must_have_count = len([f for f in mvp_features if f.get("priority") == "must_have"])
            facts.append({
                "claim": f"Defined MVP with {must_have_count} must-have features",
                "confidence": 0.7,
                "sources": []
            })

        if roadmap_phases:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/roadmap_phases",
                "value": roadmap_phases,
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
