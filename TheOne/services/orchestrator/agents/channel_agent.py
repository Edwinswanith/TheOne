"""Channel agent — recommends go-to-market channels."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent


class ChannelAgent(BaseAgent):
    """Generates channel strategy options based on ICP and evidence signals."""

    name = "channel_agent"
    pillar = "go_to_market"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Build channel strategy prompt."""
        idea = state.get("idea", {})
        decisions = state.get("decisions", {})
        icp_decision = decisions.get("icp", {})
        evidence = state.get("evidence", {})
        channel_signals = evidence.get("channel_signals", [])

        prompt = f"""You are a channel strategy expert. Generate 2-3 channel strategy options.

Product:
Name: {idea.get('name', '')}
Category: {idea.get('category', '')}

Selected ICP: {icp_decision.get('selected_option_id', '')}

Channel signals from market:
{channel_signals}

Return JSON:
{{
  "options": [
    {{
      "id": "chan_1",
      "title": "string (e.g., 'Content + Community')",
      "primary": "string (main channel)",
      "secondary": "string (supporting channel)",
      "primary_channels": ["string"],
      "tactics": ["string"],
      "confidence": 0.8,
      "rationale": "string"
    }}
  ],
  "recommended_id": "chan_1"
}}
"""
        return prompt

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse channel strategy into patches and proposals."""
        patches = []
        proposals = []
        facts = []

        options = raw.get("options", [])
        recommended_id = raw.get("recommended_id", options[0].get("id") if options else "") if options else ""

        if options:
            decision_options = []
            for opt in options:
                decision_options.append({
                    "id": opt.get("id"),
                    "label": opt.get("title"),
                    "description": opt.get("rationale"),
                    "confidence": opt.get("confidence", 0.7),
                    "data": opt
                })

            proposals.append({
                "decision_key": "channels",
                "options": decision_options,
                "recommended_option_id": recommended_id,
                "rationale": "Channel strategy based on ICP behavior and competitor signals"
            })

            selected_option = options[0]
            patches.append({
                "op": "replace",
                "path": "/decisions/channels/primary",
                "value": selected_option.get("primary", ""),
                "meta": self.meta("inference", 0.7, [])
            })

            patches.append({
                "op": "replace",
                "path": "/decisions/channels/secondary",
                "value": selected_option.get("secondary", ""),
                "meta": self.meta("inference", 0.7, [])
            })

            patches.append({
                "op": "replace",
                "path": "/decisions/channels/primary_channels",
                "value": selected_option.get("primary_channels", []),
                "meta": self.meta("inference", 0.7, [])
            })

            facts.append({
                "claim": f"Identified {len(selected_option.get('primary_channels', []))} priority channels",
                "confidence": 0.7,
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
