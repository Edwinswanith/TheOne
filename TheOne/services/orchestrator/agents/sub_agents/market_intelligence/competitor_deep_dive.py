"""CompetitorDeepDive — second sub-agent in the Market Intelligence cluster.

For each competitor discovered by MarketScanner (or already present in state),
fetches detailed profiles and user reviews via Perplexity, then asks Gemini
to produce positioning teardowns, pricing breakdowns, and differentiation gaps.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class CompetitorDeepDive(BaseSubAgent):
    """Produces detailed competitive profiles with pricing teardowns."""

    name = "competitor_deep_dive"
    pillar = "market_intelligence"
    step_number = 2
    total_steps = 4
    uses_external_search = True

    # ------------------------------------------------------------------
    # External search
    # ------------------------------------------------------------------

    def _run_searches(
        self,
        state: dict[str, Any],
        cluster_context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Fetch details + reviews for each competitor (max 5)."""
        # Gather competitor names from state evidence or market_scanner output
        competitor_names: list[str] = []

        evidence = state.get("evidence", {})
        for comp in evidence.get("competitors", []):
            name = comp.get("name", "")
            if name and name not in competitor_names:
                competitor_names.append(name)

        # Also pull from market_scanner's key_players if available
        if cluster_context:
            scanner_output = cluster_context.get("market_scanner", {})
            scanner_patches = scanner_output.get("patches", [])
            for patch in scanner_patches:
                if patch.get("path") == "/evidence/sources":
                    for src in patch.get("value", []):
                        n = src.get("title", "")
                        if n and n not in competitor_names:
                            competitor_names.append(n)

        competitor_names = competitor_names[:5]
        if not competitor_names:
            return None

        details: dict[str, Any] = {}
        for name in competitor_names:
            details[name] = self.provider.search_competitor_details(name)

        reviews = self.provider.search_competitor_reviews(competitor_names)

        return {
            "competitor_details": details,
            "competitor_reviews": reviews,
            "competitor_names": competitor_names,
        }

    def _enrich_prompt_with_search(
        self, prompt: str, search_data: dict[str, Any]
    ) -> str:
        details = search_data.get("competitor_details", {})
        reviews = search_data.get("competitor_reviews", {})
        block = "\n\n--- Competitor Research Data ---\n"
        block += f"Details:\n{json.dumps(details, indent=2)}\n"
        block += f"\nReviews/Sentiment:\n{json.dumps(reviews, indent=2)}\n"
        return prompt + block

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
        evidence = state.get("evidence", {})
        existing_competitors = evidence.get("competitors", [])

        # Include market_scanner context if available
        scanner_summary = ""
        if cluster_context:
            scanner_output = cluster_context.get("market_scanner", {})
            scanner_facts = scanner_output.get("facts", [])
            if scanner_facts:
                scanner_summary = "\n".join(f"- {f.get('claim', '')}" for f in scanner_facts)

        prompt = f"""You are a competitive intelligence analyst. Perform a deep dive on each competitor.

Product context:
Name: {idea.get("name", "")}
One-liner: {idea.get("one_liner", "")}
Problem: {idea.get("problem", "")}
Category: {idea.get("category", "")}

Market Scanner findings:
{scanner_summary or "No prior market scan available."}

Known competitors:
{json.dumps(existing_competitors[:5], indent=2) if existing_competitors else "None yet — use research data below."}

For each competitor, provide detailed analysis. Return JSON:
{{
  "teardowns": [
    {{
      "name": "string",
      "url": "string",
      "positioning": "string (their core positioning statement)",
      "value_proposition": "string",
      "pricing_model": "string (freemium | subscription | usage | enterprise)",
      "pricing_details": {{
        "entry_price": "string",
        "mid_tier": "string",
        "enterprise": "string",
        "free_tier": "boolean or description"
      }},
      "target_segment": "string",
      "go_to_market": "string (PLG | sales-led | hybrid | community)",
      "strengths": ["string"],
      "weaknesses": ["string"],
      "user_sentiment": "positive | mixed | negative",
      "key_complaints": ["string"],
      "differentiation_gaps": ["string (areas where they fall short)"]
    }}
  ],
  "overall_competitive_intensity": "high | medium | low",
  "biggest_opportunity": "string"
}}"""

        if feedback:
            prompt += f"\n\nOrchestrator feedback:\n{json.dumps(feedback) if not isinstance(feedback, str) else feedback}"

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

        teardowns = raw.get("teardowns", [])
        intensity = raw.get("overall_competitive_intensity", "medium")
        opportunity = raw.get("biggest_opportunity", "")

        if teardowns:
            urls = [t.get("url", "") for t in teardowns if t.get("url")]

            # Patch enriched competitor data
            patches.append({
                "op": "replace",
                "path": "/evidence/competitors",
                "value": teardowns,
                "meta": self.meta("evidence", 0.85, urls),
            })

            # Patch teardown analysis
            patches.append({
                "op": "add",
                "path": "/evidence/teardowns",
                "value": {
                    "competitors": teardowns,
                    "competitive_intensity": intensity,
                    "biggest_opportunity": opportunity,
                },
                "meta": self.meta("evidence", 0.8, urls),
            })

            facts.append({
                "claim": (
                    f"Deep-dived {len(teardowns)} competitors; "
                    f"competitive intensity: {intensity}"
                ),
                "confidence": 0.85,
                "sources": urls,
            })

            if opportunity:
                facts.append({
                    "claim": f"Biggest competitive opportunity: {opportunity}",
                    "confidence": 0.75,
                    "sources": [],
                })

            # Flag negative sentiment competitors as risks
            negative = [t for t in teardowns if t.get("user_sentiment") == "negative"]
            for comp in negative:
                complaints = comp.get("key_complaints", [])
                reasoning_steps.append({
                    "action": "risk_identification",
                    "thought": (
                        f"Competitor {comp.get('name', '')} has negative user sentiment. "
                        f"Top complaints: {', '.join(complaints[:3])}"
                    ),
                    "confidence": 0.7,
                })

            # High competitive intensity is a risk
            if intensity == "high":
                risks.append({
                    "id": "risk_competitive_intensity",
                    "severity": "high",
                    "description": "Market has high competitive intensity",
                    "mitigation": opportunity or "Identify niche positioning",
                })

            reasoning_steps.append({
                "action": "competitive_analysis",
                "thought": (
                    f"Analyzed {len(teardowns)} competitors across positioning, pricing, "
                    f"and sentiment dimensions"
                ),
                "confidence": 0.85,
                "source_ids": urls,
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
            "_confidence": 0.85 if teardowns else 0.4,
            "_summary": (
                f"Competitor deep dive: {len(teardowns)} teardowns, "
                f"intensity={intensity}"
            ),
        }
