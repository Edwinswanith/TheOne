"""CategoryFramer — defines category positioning from ICP + competitive data."""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class CategoryFramer(BaseSubAgent):
    """Generates 2-3 positioning framework options with differentiation and proof points.

    Uses the selected ICP decision and competitive teardown data from evidence
    to determine how the product should be framed within its category.
    """

    name = "category_framer"
    pillar = "positioning_pricing"
    step_number = 1
    total_steps = 4
    uses_external_search = False

    def build_prompt(
        self,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
    ) -> str:
        idea = state.get("idea", {})
        decisions = state.get("decisions", {})
        evidence = state.get("evidence", {})

        icp_decision = decisions.get("icp", {})
        selected_icp_id = icp_decision.get("selected_option_id", "")
        icp_options = icp_decision.get("options", [])
        selected_icp = next(
            (o for o in icp_options if o.get("id") == selected_icp_id), {}
        )

        competitors = evidence.get("competitors", [])
        teardowns = evidence.get("teardowns", [])
        positioning_map = evidence.get("positioning_map", [])

        prompt = f"""You are an expert positioning strategist specializing in \
go-to-market strategy. Your task is to define category positioning \
frameworks for a new product.

## Product
Name: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Problem: {idea.get('problem', '')}
Category: {idea.get('category', '')}
Domain: {idea.get('domain', '')}
Region: {idea.get('target_region', '')}

## Selected ICP
ID: {selected_icp_id}
Details: {json.dumps(selected_icp.get('data', selected_icp), default=str)}

## Competitive Landscape
Competitors: {json.dumps(competitors[:5], default=str)}
Teardowns: {json.dumps(teardowns[:3], default=str)}
Positioning Map: {json.dumps(positioning_map[:3], default=str)}

## Instructions
Generate 2-3 distinct positioning framework options. Each framework must:
1. Define a clear category framing (e.g., "category creator", "category \
disruptor", "niche dominator")
2. Articulate a unique differentiation angle
3. Provide 2-4 evidence-backed proof points
4. Include 2-3 messaging pillars that support the positioning
5. Explain the competitive moat this positioning creates

Consider which competitors own which positions and find whitespace.

{f"NOTE: A previous decision changed ({changed_decision}). Re-evaluate positioning in light of this change." if changed_decision else ""}
{f"ORCHESTRATOR FEEDBACK: {feedback}" if feedback else ""}

Return JSON:
{{
  "options": [
    {{
      "id": "pos_1",
      "title": "string (e.g., 'Category Creator')",
      "frame": "string (the positioning statement)",
      "category_type": "creator | disruptor | niche_dominator | fast_follower",
      "differentiation": "string (unique angle)",
      "proof_points": ["string (evidence-backed claims)"],
      "messaging_pillars": ["string"],
      "competitive_moat": "string",
      "target_narrative": "string (the story you want buyers to believe)",
      "confidence": 0.8,
      "rationale": "string"
    }}
  ],
  "recommended_id": "pos_1",
  "category_analysis": {{
    "existing_categories": ["string (categories competitors claim)"],
    "whitespace_found": "string (unclaimed positioning territory)",
    "risk_of_head_to_head": "low | medium | high"
  }}
}}"""
        return prompt

    def parse_response(
        self,
        raw: dict[str, Any],
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        patches: list[dict[str, Any]] = []
        proposals: list[dict[str, Any]] = []
        facts: list[dict[str, Any]] = []
        assumptions: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []

        options = raw.get("options", [])
        recommended_id = raw.get("recommended_id", "")
        if not recommended_id and options:
            recommended_id = options[0].get("id", "")

        category_analysis = raw.get("category_analysis", {})

        if options:
            # Build decision options for the positioning decision
            decision_options = []
            for opt in options:
                decision_options.append({
                    "id": opt.get("id"),
                    "label": opt.get("title"),
                    "description": opt.get("rationale"),
                    "confidence": opt.get("confidence", 0.7),
                    "data": opt,
                })

            proposals.append({
                "decision_key": "positioning",
                "options": decision_options,
                "recommended_option_id": recommended_id,
                "rationale": (
                    "Positioning options derived from ICP alignment "
                    "and competitive whitespace analysis"
                ),
            })

            # Patch the positioning frame from recommended option
            rec_opt = next(
                (o for o in options if o.get("id") == recommended_id),
                options[0],
            )
            patches.append({
                "op": "replace",
                "path": "/decisions/positioning/frame",
                "value": rec_opt.get("frame", ""),
                "meta": self.meta("inference", 0.75),
            })

            # Patch pillar summary
            patches.append({
                "op": "replace",
                "path": "/pillars/positioning_pricing/summary",
                "value": (
                    f"Positioning: {rec_opt.get('title', '')} "
                    f"- {rec_opt.get('differentiation', '')}"
                ),
                "meta": self.meta("inference", 0.75),
            })

            facts.append({
                "claim": (
                    f"Generated {len(options)} positioning frameworks; "
                    f"recommended '{rec_opt.get('title', '')}' based on "
                    "competitive whitespace"
                ),
                "confidence": 0.75,
                "sources": [],
            })

        if category_analysis:
            whitespace = category_analysis.get("whitespace_found", "")
            if whitespace:
                facts.append({
                    "claim": f"Identified positioning whitespace: {whitespace}",
                    "confidence": 0.7,
                    "sources": [],
                })

            risk_level = category_analysis.get("risk_of_head_to_head", "")
            if risk_level in ("medium", "high"):
                risks.append({
                    "type": "positioning_collision",
                    "severity": "high" if risk_level == "high" else "medium",
                    "description": (
                        f"Head-to-head competitive risk is {risk_level}. "
                        "Category positioning may overlap with incumbents."
                    ),
                })

        reasoning_steps = [
            {
                "action": "category_analysis",
                "thought": (
                    f"Analyzed {len(raw.get('options', []))} positioning "
                    "frameworks against competitive landscape"
                ),
                "confidence": 0.75,
            },
        ]

        return {
            "patches": patches,
            "proposals": proposals,
            "facts": facts,
            "assumptions": assumptions,
            "risks": risks,
            "required_inputs": [],
            "node_updates": [],
            "reasoning_steps": reasoning_steps,
            "_confidence": 0.75,
            "_summary": (
                f"Category framing complete: {len(options)} positioning "
                "options generated"
            ),
        }
