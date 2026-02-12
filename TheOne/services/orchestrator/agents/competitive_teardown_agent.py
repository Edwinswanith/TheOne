"""Competitive teardown agent — deep analysis of competitors."""
from __future__ import annotations

import json
import time
from typing import Any

from services.orchestrator.agents.base import BaseAgent


class CompetitiveTeardownAgent(BaseAgent):
    """Analyzes competitors in detail from collected evidence.

    Uses Perplexity to gather competitor reviews, then Gemini to synthesize
    a detailed competitive teardown.
    """

    name = "competitive_teardown_agent"
    pillar = "market_intelligence"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Build competitor analysis prompt."""
        idea = state.get("idea", {})
        evidence = state.get("evidence", {})
        competitors = evidence.get("competitors", [])

        prompt = f"""You are a competitive intelligence analyst. Perform a detailed teardown of competitors.

Product context:
Name: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Problem: {idea.get('problem', '')}

Existing competitor data:
{competitors}

For each competitor, provide a detailed analysis. Return JSON:
{{
  "competitors": [
    {{
      "name": "string",
      "url": "string",
      "positioning": "string",
      "value_proposition": "string",
      "pricing_model": "string",
      "pricing_details": "string",
      "target_segment": "string",
      "go_to_market": "string",
      "strengths": ["string"],
      "weaknesses": ["string"],
      "differentiation_opportunity": "string"
    }}
  ]
}}
"""
        return prompt

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse competitive analysis into patches and facts."""
        patches = []
        facts = []

        competitors = raw.get("competitors", [])
        if competitors:
            patches.append({
                "op": "replace",
                "path": "/evidence/competitors",
                "value": competitors,
                "meta": self.meta("evidence", 0.85, [c.get("url", "") for c in competitors if c.get("url")])
            })

            facts.append({
                "claim": f"Analyzed {len(competitors)} competitors with detailed positioning and pricing",
                "confidence": 0.85,
                "sources": [c.get("url", "") for c in competitors if c.get("url")]
            })

            # Extract differentiation insights
            opportunities = [c.get("differentiation_opportunity", "") for c in competitors if c.get("differentiation_opportunity")]
            if opportunities:
                facts.append({
                    "claim": "Identified key differentiation opportunities based on competitor weaknesses",
                    "confidence": 0.75,
                    "sources": []
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

    def run(
        self, run_id: str, state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Override run to gather competitor reviews via Perplexity before Gemini synthesis."""
        timer = time.perf_counter()
        self._input_tokens = 0
        self._output_tokens = 0

        # Gather competitor review data from Perplexity
        evidence = state.get("evidence", {})
        competitors = evidence.get("competitors", [])
        competitor_names = [c.get("name", "") for c in competitors if c.get("name")]

        reviews = {}
        if competitor_names:
            reviews = self.provider.search_competitor_reviews(competitor_names)

        # Synthesize with Gemini, enriched with review data
        prompt = self.build_prompt(state, changed_decision)
        if reviews:
            prompt += f"\n\nAdditional competitor review data:\n{json.dumps(reviews, indent=2)}"

        raw = self._call_llm(prompt)
        parsed = self.parse_response(raw, state, changed_decision)
        elapsed = int((time.perf_counter() - timer) * 1000)
        return self._wrap_output(run_id, parsed, execution_time_ms=elapsed)
