"""MotionDesigner — designs sales motion options (outbound, inbound, PLG, partner-led)."""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class MotionDesigner(BaseSubAgent):
    """Generates 2-3 sales motion options using ICP, pricing, team constraints,
    and channel_researcher context.

    Motion types: outbound_led, inbound_led, plg, partner_led.
    """

    name = "motion_designer"
    pillar = "go_to_market"
    step_number = 2
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
        constraints = state.get("constraints", {})

        icp_decision = decisions.get("icp", {})
        selected_icp_id = icp_decision.get("selected_option_id", "")
        icp_options = icp_decision.get("options", [])
        selected_icp = next(
            (o for o in icp_options if o.get("id") == selected_icp_id), {}
        )

        pricing_decision = decisions.get("pricing", {})
        pricing_metric = pricing_decision.get("metric", "")
        pricing_tiers = pricing_decision.get("tiers", [])

        # Get channel_researcher output from cluster context
        ctx = cluster_context or {}
        channel_output = ctx.get("channel_researcher", {})
        channel_proposals = channel_output.get("proposals", [])
        channel_facts = channel_output.get("facts", [])

        prompt = f"""You are a sales strategy architect. Design 2-3 sales \
motion options for a new product. Each motion must be realistic given the \
team size and budget constraints.

## Product
Name: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Category: {idea.get('category', '')}
Domain: {idea.get('domain', '')}

## Selected ICP
ID: {selected_icp_id}
Details: {json.dumps(selected_icp.get('data', selected_icp), default=str)}

## Pricing Context
Metric: {pricing_metric}
Tiers: {json.dumps(pricing_tiers[:3], default=str)}

## Team Constraints
Team size: {constraints.get('team_size', '')}
Budget: ${constraints.get('budget_usd_monthly', '')} monthly
Timeline: {constraints.get('timeline_weeks', '')} weeks

## Channel Researcher Context
Channel proposals: {json.dumps(channel_proposals, default=str)}
Channel facts: {json.dumps(channel_facts, default=str)}

## Instructions
Design 2-3 sales motion options. For each:
1. Choose a motion type: outbound_led, inbound_led, plg, partner_led
2. Define the sales cycle (weeks), expected deal size, and key activities
3. Specify required team roles and minimum team size
4. Estimate cost-to-acquire and time-to-first-deal
5. Explain how this motion aligns with the selected channels
6. Flag if team size or budget makes this motion infeasible

IMPORTANT: If team_size <= 3, heavily penalize outbound_led (requires \
dedicated SDR). If budget < $2000/month, penalize paid acquisition motions. \
If category is b2c, favor PLG over sales-led motions.

{f"NOTE: Decision '{changed_decision}' changed. Re-evaluate motions." if changed_decision else ""}
{f"ORCHESTRATOR FEEDBACK: {feedback}" if feedback else ""}

Return JSON:
{{
  "options": [
    {{
      "id": "motion_1",
      "motion": "outbound_led | inbound_led | plg | partner_led",
      "title": "string (e.g., 'Product-Led Growth with Community')",
      "description": "string (2-3 sentences)",
      "sales_cycle_weeks": "number",
      "avg_deal_size": "number (USD)",
      "key_activities": ["string (specific activities, not generic)"],
      "required_roles": ["string (e.g., 'growth engineer', 'content marketer')"],
      "min_team_size": "number",
      "estimated_cac": "number (USD)",
      "time_to_first_deal_weeks": "number",
      "channel_alignment": "string (how this uses selected channels)",
      "feasibility_score": "number (1-10, given constraints)",
      "confidence": 0.8,
      "rationale": "string"
    }}
  ],
  "recommended_id": "motion_1",
  "constraint_warnings": [
    {{
      "motion_id": "string",
      "warning": "string (why constraints may block this)"
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

        options = raw.get("options", [])
        recommended_id = raw.get("recommended_id", "")
        if not recommended_id and options:
            recommended_id = options[0].get("id", "")
        constraint_warnings = raw.get("constraint_warnings", [])

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
                "decision_key": "sales_motion",
                "options": decision_options,
                "recommended_option_id": recommended_id,
                "rationale": (
                    "Sales motion options based on ICP, pricing, "
                    "channel strategy, and team constraints"
                ),
            })

            # Patch the motion field from recommended option
            rec_opt = next(
                (o for o in options if o.get("id") == recommended_id),
                options[0],
            )

            patches.append({
                "op": "replace",
                "path": "/decisions/sales_motion/motion",
                "value": rec_opt.get("motion", "unset"),
                "meta": self.meta("inference", 0.75),
            })

            # Store full motion data in artifacts
            patches.append({
                "op": "replace",
                "path": "/artifacts/go_to_market/sales_motion",
                "value": {
                    "options": options,
                    "recommended_id": recommended_id,
                },
                "meta": self.meta("inference", 0.75),
            })

            facts.append({
                "claim": (
                    f"Designed {len(options)} sales motion options; "
                    f"recommended '{rec_opt.get('title', '')}' "
                    f"({rec_opt.get('motion', '')}) with "
                    f"~{rec_opt.get('sales_cycle_weeks', '?')} week cycle"
                ),
                "confidence": 0.75,
                "sources": [],
            })

            # Check feasibility
            for opt in options:
                feasibility = opt.get("feasibility_score", 10)
                if feasibility < 5:
                    risks.append({
                        "type": "motion_feasibility",
                        "severity": "high" if feasibility < 3 else "medium",
                        "description": (
                            f"Motion '{opt.get('title', '')}' has low "
                            f"feasibility score ({feasibility}/10) given "
                            "current constraints"
                        ),
                    })

        # Process constraint warnings
        for warning in constraint_warnings:
            motion_id = warning.get("motion_id", "")
            msg = warning.get("warning", "")
            if motion_id == recommended_id:
                # Warning on the recommended motion is more severe
                risks.append({
                    "type": "constraint_conflict",
                    "severity": "high",
                    "description": (
                        f"Recommended motion '{motion_id}' has constraint "
                        f"warning: {msg}"
                    ),
                })
            else:
                assumptions.append({
                    "claim": (
                        f"Motion '{motion_id}' may face constraint: {msg}"
                    ),
                    "confidence": 0.6,
                })

        reasoning_steps = [
            {
                "action": "motion_design",
                "thought": (
                    f"Designed {len(options)} sales motions; evaluated "
                    "feasibility against team/budget constraints"
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
                f"Motion design complete: {len(options)} options, "
                f"recommended {recommended_id}"
            ),
        }
