"""MISynthesizer — fourth and final sub-agent in the Market Intelligence cluster.

Synthesizes outputs from MarketScanner, CompetitorDeepDive, and WeaknessMiner
into a cohesive market intelligence summary and produces graph node updates.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class MISynthesizer(BaseSubAgent):
    """Produces the unified Market Intelligence pillar summary."""

    name = "mi_synthesizer"
    pillar = "market_intelligence"
    step_number = 4
    total_steps = 4
    uses_external_search = False

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
        ctx = cluster_context or {}

        # Collect all prior sub-agent outputs
        scanner_output = ctx.get("market_scanner", {})
        dive_output = ctx.get("competitor_deep_dive", {})
        miner_output = ctx.get("weakness_miner", {})

        # Extract key facts and findings from each
        scanner_facts = scanner_output.get("facts", [])
        scanner_risks = scanner_output.get("risks", [])
        dive_facts = dive_output.get("facts", [])
        dive_risks = dive_output.get("risks", [])
        miner_facts = miner_output.get("facts", [])
        miner_risks = miner_output.get("risks", [])

        all_facts = scanner_facts + dive_facts + miner_facts
        all_risks = scanner_risks + dive_risks + miner_risks

        # Get weakness map summary
        weakness_summary = ""
        for patch in miner_output.get("patches", []):
            if patch.get("path") == "/evidence/weakness_map":
                wm = patch.get("value", {})
                weakness_summary = wm.get("summary", "")
                break

        prompt = f"""You are a senior market intelligence strategist. Synthesize the following research
into a cohesive Market Intelligence brief for a go-to-market plan.

Product context:
Name: {idea.get("name", "")}
One-liner: {idea.get("one_liner", "")}
Problem: {idea.get("problem", "")}
Category: {idea.get("category", "")}

Collected facts ({len(all_facts)} total):
{json.dumps(all_facts, indent=2)}

Identified risks ({len(all_risks)} total):
{json.dumps(all_risks, indent=2)}

Weakness/gap analysis summary:
{weakness_summary or "Not available."}

Return JSON:
{{
  "executive_summary": "string (2-3 paragraphs synthesizing the full market picture)",
  "market_attractiveness": "high | medium | low",
  "market_attractiveness_rationale": "string",
  "key_insights": [
    {{
      "insight": "string",
      "implication_for_gtm": "string",
      "confidence": 0.8,
      "source_type": "evidence | inference | assumption"
    }}
  ],
  "recommended_positioning_angle": "string (based on gaps and competitive landscape)",
  "top_risks": [
    {{
      "risk": "string",
      "severity": "high | medium | low",
      "mitigation": "string"
    }}
  ],
  "graph_nodes": [
    {{
      "node_id": "market.overview",
      "title": "string",
      "body": "string (2-3 sentences)"
    }},
    {{
      "node_id": "market.competitors",
      "title": "string",
      "body": "string"
    }},
    {{
      "node_id": "market.gaps",
      "title": "string",
      "body": "string"
    }},
    {{
      "node_id": "market.trends",
      "title": "string",
      "body": "string"
    }}
  ]
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
        node_updates: list[dict[str, Any]] = []
        reasoning_steps: list[dict[str, Any]] = []

        executive_summary = raw.get("executive_summary", "")
        attractiveness = raw.get("market_attractiveness", "medium")
        attractiveness_rationale = raw.get("market_attractiveness_rationale", "")
        key_insights = raw.get("key_insights", [])
        positioning_angle = raw.get("recommended_positioning_angle", "")
        top_risks = raw.get("top_risks", [])
        graph_nodes = raw.get("graph_nodes", [])

        # --- Pillar summary patch ---
        if executive_summary:
            patches.append({
                "op": "replace",
                "path": "/pillars/market_intelligence/summary",
                "value": executive_summary,
                "meta": self.meta("inference", 0.75),
            })

        # --- Market attractiveness ---
        patches.append({
            "op": "add",
            "path": "/pillars/market_intelligence/attractiveness",
            "value": {
                "rating": attractiveness,
                "rationale": attractiveness_rationale,
            },
            "meta": self.meta("inference", 0.7),
        })

        # --- Key insights as facts or assumptions ---
        for insight in key_insights:
            src_type = insight.get("source_type", "inference")
            conf = insight.get("confidence", 0.7)
            entry = {
                "claim": (
                    f"{insight.get('insight', '')} "
                    f"→ GTM implication: {insight.get('implication_for_gtm', '')}"
                ),
                "confidence": conf,
                "sources": [],
            }
            if src_type == "assumption" or conf < 0.6:
                assumptions.append(entry)
            else:
                facts.append(entry)

        # --- Recommended positioning angle ---
        if positioning_angle:
            patches.append({
                "op": "add",
                "path": "/pillars/market_intelligence/recommended_positioning_angle",
                "value": positioning_angle,
                "meta": self.meta("inference", 0.7),
            })
            reasoning_steps.append({
                "action": "positioning_recommendation",
                "thought": f"Recommending positioning angle: {positioning_angle}",
                "confidence": 0.7,
            })

        # --- Risks ---
        for risk_entry in top_risks:
            risks.append({
                "id": f"risk_mi_{risk_entry.get('risk', 'unknown')[:30].replace(' ', '_').lower()}",
                "severity": risk_entry.get("severity", "medium"),
                "description": risk_entry.get("risk", ""),
                "mitigation": risk_entry.get("mitigation", ""),
            })

        # --- Graph node updates ---
        for gn in graph_nodes:
            node_id = gn.get("node_id", "")
            if node_id:
                node_updates.append({
                    "node_id": node_id,
                    "title": gn.get("title", ""),
                    "body": gn.get("body", ""),
                    "pillar": "market_intelligence",
                })

        # Ensure standard graph nodes exist even if LLM omits some
        existing_ids = {n.get("node_id") for n in node_updates}
        default_nodes = {
            "market.overview": ("Market Overview", executive_summary[:200] if executive_summary else ""),
            "market.competitors": ("Competitive Landscape", ""),
            "market.gaps": ("Market Gaps", ""),
            "market.trends": ("Market Trends", ""),
        }
        for nid, (title, body) in default_nodes.items():
            if nid not in existing_ids and body:
                node_updates.append({
                    "node_id": nid,
                    "title": title,
                    "body": body,
                    "pillar": "market_intelligence",
                })

        reasoning_steps.append({
            "action": "synthesis",
            "thought": (
                f"Synthesized market intelligence: attractiveness={attractiveness}, "
                f"{len(key_insights)} insights, {len(top_risks)} risks, "
                f"{len(node_updates)} graph nodes"
            ),
            "confidence": 0.75,
        })

        # Overall confidence based on attractiveness assessment
        confidence_map = {"high": 0.8, "medium": 0.7, "low": 0.6}
        overall_confidence = confidence_map.get(attractiveness, 0.7)

        return {
            "patches": patches,
            "proposals": [],
            "facts": facts,
            "assumptions": assumptions,
            "risks": risks,
            "required_inputs": [],
            "node_updates": node_updates,
            "reasoning_steps": reasoning_steps,
            "_confidence": overall_confidence,
            "_summary": (
                f"MI synthesis complete: attractiveness={attractiveness}, "
                f"{len(key_insights)} insights, {len(node_updates)} graph nodes"
            ),
        }
