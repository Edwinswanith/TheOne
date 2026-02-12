"""MarketScanner — first sub-agent in the Market Intelligence cluster.

Performs broad market research via Perplexity, then synthesizes market size,
growth trends, key players, segments, and entry barriers through Gemini.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class MarketScanner(BaseSubAgent):
    """Scans external sources for market landscape data."""

    name = "market_scanner"
    pillar = "market_intelligence"
    step_number = 1
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
        """Build 3-5 market research queries from state.idea and run them."""
        idea = state.get("idea", {})
        name = idea.get("name", "")
        one_liner = idea.get("one_liner", "")
        category = idea.get("category", "")
        region = idea.get("target_region", "US")

        queries = [
            f"{name} market size and growth rate {region}",
            f"{category} industry trends and competitive landscape {region}",
            f"Key players in {one_liner} space market share",
        ]

        # Additional queries when we have richer context
        problem = idea.get("problem", "")
        if problem:
            queries.append(f"Companies solving {problem} market analysis")
        if category:
            queries.append(f"{category} market entry barriers and regulations {region}")

        results = self.provider.search_market(queries[:5])
        return {"market_scan_results": results, "queries_used": queries[:5]}

    def _enrich_prompt_with_search(
        self, prompt: str, search_data: dict[str, Any]
    ) -> str:
        """Append market scan results in a structured block."""
        results = search_data.get("market_scan_results", [])
        queries = search_data.get("queries_used", [])
        block = "\n\n--- External Market Research ---\n"
        for i, (q, r) in enumerate(zip(queries, results), 1):
            block += f"\nQuery {i}: {q}\n"
            block += json.dumps(r, indent=2) + "\n"
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
        constraints = state.get("constraints", {})

        prompt = f"""You are a market research analyst specializing in go-to-market intelligence.

Product context:
Name: {idea.get("name", "")}
One-liner: {idea.get("one_liner", "")}
Problem: {idea.get("problem", "")}
Target region: {idea.get("target_region", "US")}
Category: {idea.get("category", "")}

Constraints:
- Team size: {constraints.get("team_size", "")}
- Timeline: {constraints.get("timeline_weeks", "")} weeks
- Budget: ${constraints.get("budget_usd_monthly", "")} monthly

Analyze the market landscape and return a JSON object with these keys:
{{
  "market_size": {{
    "tam_usd": "string (total addressable market estimate)",
    "sam_usd": "string (serviceable addressable market)",
    "som_usd": "string (serviceable obtainable market)",
    "methodology": "string (how estimates were derived)",
    "sources": ["string (URLs or report names)"]
  }},
  "growth_trends": [
    {{
      "trend": "string",
      "impact": "positive | negative | neutral",
      "timeframe": "string",
      "confidence": 0.8,
      "source": "string"
    }}
  ],
  "key_players": [
    {{
      "name": "string",
      "estimated_market_share": "string",
      "positioning": "string",
      "url": "string"
    }}
  ],
  "market_segments": [
    {{
      "segment": "string",
      "size_description": "string",
      "growth_rate": "string",
      "accessibility": "high | medium | low"
    }}
  ],
  "entry_barriers": [
    {{
      "barrier": "string",
      "severity": "high | medium | low",
      "mitigation": "string"
    }}
  ]
}}"""

        if feedback:
            prompt += f"\n\nOrchestrator feedback for this round:\n{json.dumps(feedback) if not isinstance(feedback, str) else feedback}"

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

        # --- Market size ---
        market_size = raw.get("market_size", {})
        sources = market_size.get("sources", [])
        if market_size:
            patches.append({
                "op": "add",
                "path": "/pillars/market_intelligence/market_size",
                "value": market_size,
                "meta": self.meta(
                    "evidence" if sources else "inference",
                    0.75 if sources else 0.55,
                    sources,
                ),
            })
            if sources:
                facts.append({
                    "claim": f"Market size estimated: TAM {market_size.get('tam_usd', 'N/A')}",
                    "confidence": 0.75,
                    "sources": sources,
                })
            else:
                assumptions.append({
                    "claim": f"Market size estimated: TAM {market_size.get('tam_usd', 'N/A')} (no external source)",
                    "confidence": 0.55,
                    "sources": [],
                })
            reasoning_steps.append({
                "action": "market_sizing",
                "thought": f"Derived TAM/SAM/SOM via {market_size.get('methodology', 'LLM estimate')}",
                "confidence": 0.75 if sources else 0.55,
                "source_ids": sources,
            })

        # --- Growth trends ---
        growth_trends = raw.get("growth_trends", [])
        if growth_trends:
            trend_sources = [t.get("source", "") for t in growth_trends if t.get("source")]
            patches.append({
                "op": "add",
                "path": "/pillars/market_intelligence/growth_trends",
                "value": growth_trends,
                "meta": self.meta("evidence", 0.7, trend_sources),
            })
            facts.append({
                "claim": f"Identified {len(growth_trends)} market trends",
                "confidence": 0.7,
                "sources": trend_sources,
            })

        # --- Key players ---
        key_players = raw.get("key_players", [])
        if key_players:
            player_urls = [p.get("url", "") for p in key_players if p.get("url")]
            patches.append({
                "op": "add",
                "path": "/evidence/sources",
                "value": [
                    {
                        "url": p.get("url", ""),
                        "title": p.get("name", ""),
                        "quality_score": 0.7,
                        "type": "competitor",
                    }
                    for p in key_players
                    if p.get("url")
                ],
                "meta": self.meta("evidence", 0.7, player_urls),
            })
            facts.append({
                "claim": f"Identified {len(key_players)} key market players",
                "confidence": 0.7,
                "sources": player_urls,
            })

        # --- Market segments ---
        segments = raw.get("market_segments", [])
        if segments:
            patches.append({
                "op": "add",
                "path": "/pillars/market_intelligence/segments",
                "value": segments,
                "meta": self.meta("inference", 0.65),
            })

        # --- Entry barriers ---
        barriers = raw.get("entry_barriers", [])
        if barriers:
            high_barriers = [b for b in barriers if b.get("severity") == "high"]
            patches.append({
                "op": "add",
                "path": "/pillars/market_intelligence/entry_barriers",
                "value": barriers,
                "meta": self.meta("inference", 0.65),
            })
            if high_barriers:
                risks.append({
                    "id": "risk_market_barriers",
                    "severity": "high",
                    "description": f"{len(high_barriers)} high-severity market entry barriers identified",
                    "mitigation": "; ".join(
                        b.get("mitigation", "") for b in high_barriers
                    ),
                })

        # --- Confidence ---
        has_external = bool(market_size.get("sources"))
        overall_confidence = 0.75 if has_external else 0.55

        return {
            "patches": patches,
            "proposals": [],
            "facts": facts,
            "assumptions": assumptions,
            "risks": risks,
            "required_inputs": [],
            "node_updates": [],
            "reasoning_steps": reasoning_steps,
            "_confidence": overall_confidence,
            "_summary": (
                f"Market scan complete: {len(key_players)} players, "
                f"{len(growth_trends)} trends, {len(barriers)} barriers"
            ),
        }
