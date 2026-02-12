"""MessageCrafter — creates messaging framework aligned with positioning, ICP, and channels."""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class MessageCrafter(BaseSubAgent):
    """Creates a messaging framework that ties together the positioning wedge,
    ICP persona, and chosen channels into actionable messaging templates.

    Patches /pillars/go_to_market/messaging_templates.
    """

    name = "message_crafter"
    pillar = "go_to_market"
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
        artifacts = state.get("artifacts", {})

        icp_decision = decisions.get("icp", {})
        selected_icp_id = icp_decision.get("selected_option_id", "")
        icp_options = icp_decision.get("options", [])
        selected_icp = next(
            (o for o in icp_options if o.get("id") == selected_icp_id), {}
        )

        positioning_decision = decisions.get("positioning", {})
        messaging_patterns = evidence.get("messaging_patterns", [])

        # Get positioning wedge from artifacts or state
        pp_artifacts = artifacts.get("positioning_pricing", {})
        wedge_data = pp_artifacts.get("wedge", {})

        # Get upstream cluster context
        ctx = cluster_context or {}
        channel_output = ctx.get("channel_researcher", {})
        motion_output = ctx.get("motion_designer", {})

        channel_proposals = channel_output.get("proposals", [])
        motion_proposals = motion_output.get("proposals", [])

        prompt = f"""You are a messaging strategist who creates compelling, \
evidence-backed messaging frameworks. Create messaging templates that align \
the product positioning with the target buyer persona and selected channels.

## Product
Name: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Problem: {idea.get('problem', '')}
Category: {idea.get('category', '')}
Domain: {idea.get('domain', '')}

## Selected ICP
ID: {selected_icp_id}
Details: {json.dumps(selected_icp.get('data', selected_icp), default=str)}

## Positioning Context
Decision: {json.dumps({{"selected": positioning_decision.get("selected_option_id", ""), "frame": positioning_decision.get("frame", "")}}, default=str)}
Wedge: {json.dumps(wedge_data, default=str)}

## Competitor Messaging Patterns
{json.dumps(messaging_patterns[:5], default=str)}

## Channel Strategy (from ChannelResearcher)
{json.dumps(channel_proposals, default=str)}

## Sales Motion (from MotionDesigner)
{json.dumps(motion_proposals, default=str)}

## Instructions
Create a messaging framework with:
1. A core value proposition (one sentence)
2. 3 messaging pillars with headline + supporting copy + proof point
3. Channel-specific message variants (adapt tone/length for each channel)
4. Objection handling scripts (top 3 objections with rebuttals)
5. A competitive differentiation one-liner
6. Email/outreach templates if sales motion is outbound_led

{f"NOTE: Decision '{changed_decision}' changed. Adapt messaging." if changed_decision else ""}
{f"ORCHESTRATOR FEEDBACK: {feedback}" if feedback else ""}

Return JSON:
{{
  "value_proposition": "string (one sentence core value prop)",
  "messaging_pillars": [
    {{
      "pillar": "string (theme name)",
      "headline": "string",
      "supporting_copy": "string (2-3 sentences)",
      "proof_point": "string (evidence-backed)",
      "emotion": "string (what buyer should feel)"
    }}
  ],
  "channel_variants": [
    {{
      "channel": "string (e.g., 'linkedin', 'email', 'landing_page')",
      "tone": "string (e.g., 'professional', 'casual', 'technical')",
      "headline": "string",
      "body": "string (channel-appropriate length)",
      "cta": "string (call to action)"
    }}
  ],
  "objection_handling": [
    {{
      "objection": "string",
      "response": "string",
      "proof_point": "string"
    }}
  ],
  "differentiation_line": "string (one-liner vs competitors)",
  "outreach_templates": [
    {{
      "type": "cold_email | follow_up | linkedin_message",
      "subject": "string",
      "body": "string",
      "personalization_slots": ["string (placeholders like {{{{company_name}}}}"]
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
        facts: list[dict[str, Any]] = []
        assumptions: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []

        value_prop = raw.get("value_proposition", "")
        messaging_pillars = raw.get("messaging_pillars", [])
        channel_variants = raw.get("channel_variants", [])
        objection_handling = raw.get("objection_handling", [])
        differentiation_line = raw.get("differentiation_line", "")
        outreach_templates = raw.get("outreach_templates", [])

        # Build the full messaging templates object
        messaging_templates = {
            "value_proposition": value_prop,
            "messaging_pillars": messaging_pillars,
            "channel_variants": channel_variants,
            "objection_handling": objection_handling,
            "differentiation_line": differentiation_line,
            "outreach_templates": outreach_templates,
        }

        # Patch messaging templates into the pillar
        patches.append({
            "op": "replace",
            "path": "/pillars/go_to_market/messaging_templates",
            "value": messaging_templates,
            "meta": self.meta("inference", 0.75),
        })

        # Store in artifacts for synthesizer
        patches.append({
            "op": "replace",
            "path": "/artifacts/go_to_market/messaging",
            "value": messaging_templates,
            "meta": self.meta("inference", 0.75),
        })

        if value_prop:
            facts.append({
                "claim": f"Core value proposition defined: {value_prop}",
                "confidence": 0.75,
                "sources": [],
            })

        if messaging_pillars:
            facts.append({
                "claim": (
                    f"Created {len(messaging_pillars)} messaging pillars: "
                    f"{', '.join(p.get('pillar', '') for p in messaging_pillars[:3])}"
                ),
                "confidence": 0.7,
                "sources": [],
            })

        if channel_variants:
            channels_covered = [v.get("channel", "") for v in channel_variants]
            facts.append({
                "claim": (
                    f"Channel-specific messaging variants created for: "
                    f"{', '.join(channels_covered)}"
                ),
                "confidence": 0.7,
                "sources": [],
            })

        if objection_handling:
            facts.append({
                "claim": (
                    f"Objection handling prepared for {len(objection_handling)} "
                    "common objections"
                ),
                "confidence": 0.7,
                "sources": [],
            })

        # Check for messaging-positioning alignment
        positioning_decision = state.get("decisions", {}).get("positioning", {})
        if positioning_decision.get("frame") and not value_prop:
            risks.append({
                "type": "messaging_gap",
                "severity": "medium",
                "description": (
                    "Positioning frame exists but value proposition "
                    "was not generated by messaging framework"
                ),
            })

        if not messaging_pillars:
            assumptions.append({
                "claim": (
                    "Messaging framework generated without specific "
                    "pillars; generic messaging may underperform"
                ),
                "confidence": 0.5,
            })

        reasoning_steps = [
            {
                "action": "messaging_synthesis",
                "thought": (
                    f"Crafted messaging framework with {len(messaging_pillars)} "
                    f"pillars, {len(channel_variants)} channel variants, "
                    f"{len(objection_handling)} objection handlers"
                ),
                "confidence": 0.75,
            },
        ]

        return {
            "patches": patches,
            "proposals": [],
            "facts": facts,
            "assumptions": assumptions,
            "risks": risks,
            "required_inputs": [],
            "node_updates": [],
            "reasoning_steps": reasoning_steps,
            "_confidence": 0.75,
            "_summary": (
                f"Messaging framework complete: "
                f"{len(messaging_pillars)} pillars, "
                f"{len(channel_variants)} channel variants"
            ),
        }
