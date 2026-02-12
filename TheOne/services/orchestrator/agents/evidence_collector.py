"""Evidence collector agent — retrieves and synthesizes market evidence."""
from __future__ import annotations

import json
import time
from typing import Any

from services.orchestrator.agents.base import BaseAgent


class EvidenceCollectorAgent(BaseAgent):
    """Collects evidence from Perplexity and synthesizes via Gemini."""

    name = "evidence_collector"
    pillar = "market_intelligence"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Build multi-query evidence collection prompt."""
        idea = state.get("idea", {})
        constraints = state.get("constraints", {})

        prompt = f"""You are a market research analyst. Collect evidence for the following product idea:

Product: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Problem: {idea.get('problem', '')}
Target region: {idea.get('target_region', '')}
Category: {idea.get('category', '')}

Constraints:
- Team size: {constraints.get('team_size', '')}
- Timeline: {constraints.get('timeline_weeks', '')} weeks
- Budget: ${constraints.get('budget_usd_monthly', '')} monthly

Return JSON with these keys:
{{
  "competitors": [
    {{
      "name": "string",
      "url": "string",
      "positioning": "string",
      "pricing_model": "string",
      "target_segment": "string",
      "strengths": ["string"],
      "weaknesses": ["string"]
    }}
  ],
  "pricing_anchors": [
    {{
      "company": "string",
      "metric": "string",
      "range": "string",
      "source_url": "string"
    }}
  ],
  "messaging_patterns": [
    {{
      "theme": "string",
      "examples": ["string"],
      "effectiveness": "string"
    }}
  ],
  "channel_signals": [
    {{
      "channel": "string",
      "evidence": "string",
      "competitors_using": ["string"]
    }}
  ]
}}
"""
        return prompt

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse evidence into patches, facts, and assumptions."""
        patches = []
        facts = []
        assumptions = []

        # Extract competitors
        competitors = raw.get("competitors", [])
        if competitors:
            patches.append({
                "op": "add",
                "path": "/evidence/competitors",
                "value": competitors,
                "meta": self.meta("evidence", 0.8, [c.get("url", "") for c in competitors if c.get("url")])
            })
            facts.append({
                "claim": f"Identified {len(competitors)} competitors in the space",
                "confidence": 0.8,
                "sources": [c.get("url", "") for c in competitors if c.get("url")]
            })

        # Extract pricing anchors
        pricing_anchors = raw.get("pricing_anchors", [])
        if pricing_anchors:
            patches.append({
                "op": "add",
                "path": "/evidence/pricing_anchors",
                "value": pricing_anchors,
                "meta": self.meta("evidence", 0.8, [p.get("source_url", "") for p in pricing_anchors if p.get("source_url")])
            })

        # Extract messaging patterns
        messaging_patterns = raw.get("messaging_patterns", [])
        if messaging_patterns:
            patches.append({
                "op": "add",
                "path": "/evidence/messaging_patterns",
                "value": messaging_patterns,
                "meta": self.meta("inference", 0.7)
            })

        # Extract channel signals
        channel_signals = raw.get("channel_signals", [])
        if channel_signals:
            patches.append({
                "op": "add",
                "path": "/evidence/channel_signals",
                "value": channel_signals,
                "meta": self.meta("evidence", 0.75, [])
            })
            facts.append({
                "claim": f"Identified {len(channel_signals)} viable channel strategies",
                "confidence": 0.75,
                "sources": []
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

    def run(
        self, run_id: str, state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Override run to use Perplexity then Gemini."""
        timer = time.perf_counter()
        self._input_tokens = 0
        self._output_tokens = 0

        # First, get evidence from Perplexity
        perplexity_prompt = self.build_prompt(state, changed_decision)
        perplexity_response = self._call_perplexity(perplexity_prompt)

        # Then synthesize with Gemini
        gemini_prompt = f"""Given the following market evidence, synthesize insights:

{json.dumps(perplexity_response, indent=2)}

Return JSON with the same structure but with added analysis and synthesis."""

        gemini_response = self._call_llm(gemini_prompt)

        # Parse the synthesized response
        parsed = self.parse_response(gemini_response, state, changed_decision)
        elapsed = int((time.perf_counter() - timer) * 1000)
        return self._wrap_output(run_id, parsed, execution_time_ms=elapsed)
