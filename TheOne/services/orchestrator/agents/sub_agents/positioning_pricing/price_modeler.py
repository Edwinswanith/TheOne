"""PriceModeler — generates pricing strategies with metric, tiers, and price_to_test."""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class PriceModeler(BaseSubAgent):
    """Generates 2-3 pricing strategies using ICP data, pricing anchors, and
    CategoryFramer context.

    Creates pricing decision proposals and patches /decisions/pricing/*.
    """

    name = "price_modeler"
    pillar = "positioning_pricing"
    step_number = 3
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
        constraints = state.get("constraints", {})

        icp_decision = decisions.get("icp", {})
        selected_icp_id = icp_decision.get("selected_option_id", "")
        icp_options = icp_decision.get("options", [])
        selected_icp = next(
            (o for o in icp_options if o.get("id") == selected_icp_id), {}
        )

        pricing_anchors = evidence.get("pricing_anchors", [])
        competitors = evidence.get("competitors", [])

        # Get upstream cluster context
        ctx = cluster_context or {}
        framer_output = ctx.get("category_framer", {})
        framer_proposals = framer_output.get("proposals", [])
        wedge_output = ctx.get("wedge_builder", {})
        wedge_patches = wedge_output.get("patches", [])

        prompt = f"""You are an expert pricing strategist. Generate 2-3 \
pricing strategy options for a new product based on competitive pricing \
anchors, ICP budget authority, and positioning context.

## Product
Name: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Category: {idea.get('category', '')}
Domain: {idea.get('domain', '')}

## Selected ICP
ID: {selected_icp_id}
Details: {json.dumps(selected_icp.get('data', selected_icp), default=str)}

## Constraints
Team size: {constraints.get('team_size', '')}
Budget: ${constraints.get('budget_usd_monthly', '')} monthly
Timeline: {constraints.get('timeline_weeks', '')} weeks

## Pricing Anchors (from competitors)
{json.dumps(pricing_anchors[:5], default=str)}

## Competitor Overview
{json.dumps([{{"name": c.get("name", ""), "pricing_model": c.get("pricing_model", ""), "pricing_details": c.get("pricing_details", "")}} for c in competitors[:5]], default=str)}

## Positioning Context
Framework proposals: {json.dumps(framer_proposals, default=str)}
Wedge data: {json.dumps(wedge_patches[:2], default=str)}

## Instructions
Generate 2-3 pricing strategies. Each must:
1. Define a clear value metric (per user/month, per API call, flat rate, etc.)
2. Include 2-3 tiers with specific price points
3. Specify a price_to_test for initial market validation
4. Account for the selected ICP's budget authority and buying process
5. Be defensible against competitive undercut
6. Align with the positioning framework (premium position = premium price)

Consider psychological pricing, competitor anchoring, and willingness-to-pay.

{f"NOTE: Decision '{changed_decision}' changed. Re-evaluate pricing in light of this change." if changed_decision else ""}
{f"ORCHESTRATOR FEEDBACK: {feedback}" if feedback else ""}

Return JSON:
{{
  "metric": "string (primary value metric, e.g., 'per user/month')",
  "options": [
    {{
      "id": "price_1",
      "title": "string (e.g., 'Usage-Based Scaling')",
      "strategy_type": "value_based | competitor_based | cost_plus | freemium | usage_based",
      "metric": "string (value metric for this option)",
      "tiers": [
        {{
          "name": "string (e.g., 'Starter')",
          "price": "number (monthly price in USD)",
          "billing_period": "monthly | annual",
          "features": ["string"],
          "target_segment": "string"
        }}
      ],
      "price_to_test": "number (initial price for market validation)",
      "anchor_rationale": "string (how this relates to competitor pricing)",
      "confidence": 0.8,
      "rationale": "string"
    }}
  ],
  "recommended_id": "price_1",
  "pricing_risks": [
    {{
      "risk": "string",
      "severity": "low | medium | high"
    }}
  ]
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

        metric = raw.get("metric", "")
        options = raw.get("options", [])
        recommended_id = raw.get("recommended_id", "")
        if not recommended_id and options:
            recommended_id = options[0].get("id", "")
        pricing_risks = raw.get("pricing_risks", [])

        # Patch the primary metric
        if metric:
            patches.append({
                "op": "replace",
                "path": "/decisions/pricing/metric",
                "value": metric,
                "meta": self.meta("inference", 0.75),
            })

        if options:
            # Build decision options
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
                "decision_key": "pricing",
                "options": decision_options,
                "recommended_option_id": recommended_id,
                "rationale": (
                    "Pricing options based on competitive anchors, "
                    "ICP budget authority, and positioning alignment"
                ),
            })

            # Patch tiers and price_to_test from recommended option
            rec_opt = next(
                (o for o in options if o.get("id") == recommended_id),
                options[0],
            )

            patches.append({
                "op": "replace",
                "path": "/decisions/pricing/tiers",
                "value": rec_opt.get("tiers", []),
                "meta": self.meta("inference", 0.7),
            })

            patches.append({
                "op": "replace",
                "path": "/decisions/pricing/price_to_test",
                "value": rec_opt.get("price_to_test", 0),
                "meta": self.meta("inference", 0.7),
            })

            # Store full pricing data in artifacts
            patches.append({
                "op": "replace",
                "path": "/artifacts/positioning_pricing/pricing",
                "value": {
                    "metric": metric,
                    "options": options,
                    "recommended_id": recommended_id,
                },
                "meta": self.meta("inference", 0.7),
            })

            facts.append({
                "claim": (
                    f"Generated {len(options)} pricing strategies with "
                    f"'{metric}' as value metric; recommended "
                    f"'{rec_opt.get('title', '')}' at "
                    f"${rec_opt.get('price_to_test', 0)} test price"
                ),
                "confidence": 0.75,
                "sources": [],
            })

            # Check if pricing seems unsupported by anchors
            evidence_anchors = state.get("evidence", {}).get("pricing_anchors", [])
            if not evidence_anchors:
                assumptions.append({
                    "claim": (
                        "Pricing strategy generated without competitive "
                        "pricing anchors. Price points are inference-based."
                    ),
                    "confidence": 0.5,
                })

        for pr in pricing_risks:
            risks.append({
                "type": "pricing_risk",
                "severity": pr.get("severity", "medium"),
                "description": pr.get("risk", ""),
            })

        reasoning_steps = [
            {
                "action": "pricing_analysis",
                "thought": (
                    f"Modeled {len(options)} pricing strategies; "
                    f"primary metric: {metric}"
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
                f"Pricing modeled: {len(options)} strategies, "
                f"metric='{metric}'"
            ),
        }
