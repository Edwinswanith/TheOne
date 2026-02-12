"""PlaybookBuilder — first sub-agent in the Execution cluster.

Replaces execution_agent. Creates a phased execution playbook with milestones,
kill criteria, and detailed first-90-days planning. Consumes all upstream
decisions (ICP, pricing, channels, sales motion) plus constraints.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class PlaybookBuilder(BaseSubAgent):
    """Creates the execution playbook, kill criteria, and next actions."""

    name = "playbook_builder"
    pillar = "execution"
    step_number = 1
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
        constraints = state.get("constraints", {})
        decisions = state.get("decisions", {})
        pillars = state.get("pillars", {})

        # Gather all upstream decisions
        icp_decision = decisions.get("icp", {})
        pricing_decision = decisions.get("pricing", {})
        channel_decision = decisions.get("channels", {})
        sales_motion_decision = decisions.get("sales_motion", {})
        positioning_decision = decisions.get("positioning", {})

        # Product & tech context
        pt_pillar = pillars.get("product_tech", {})
        mvp_features = pt_pillar.get("mvp_features", [])
        feasibility_flags = pt_pillar.get("feasibility_flags", {})

        prompt = f"""You are an execution strategist specializing in go-to-market launch \
planning. Create a phased execution playbook with the first 90 days in detail.

Product context:
Name: {idea.get("name", "")}
One-liner: {idea.get("one_liner", "")}
Category: {idea.get("category", "")}

Decisions:
ICP: {json.dumps(icp_decision) if icp_decision else "Not yet decided"}
Pricing: {json.dumps(pricing_decision) if pricing_decision else "Not yet decided"}
Channels: {json.dumps(channel_decision) if channel_decision else "Not yet decided"}
Sales motion: {json.dumps(sales_motion_decision) if sales_motion_decision else "Not yet decided"}
Positioning: {json.dumps(positioning_decision) if positioning_decision else "Not yet decided"}

Product scope:
MVP features: {len(mvp_features)} features defined
Feasibility: {json.dumps(feasibility_flags) if feasibility_flags else "Not assessed"}

Constraints:
- Team size: {constraints.get("team_size", "")}
- Timeline: {constraints.get("timeline_weeks", "")} weeks
- Budget: ${constraints.get("budget_usd_monthly", "")} monthly

{"Changed decision: " + changed_decision if changed_decision else "Initial plan"}

Create a phased execution plan. The first 90 days should be detailed with \
week-by-week milestones. Include kill criteria — specific metrics that, if not \
met, signal the team should pivot or stop.

Return a JSON object with these keys:
{{
  "playbook": {{
    "chosen_track": "validation_sprint | outbound_sprint | landing_waitlist | pilot_onboarding",
    "phases": [
      {{
        "phase": "string (e.g. Phase 1: Validate)",
        "duration": "string (e.g. Weeks 1-4)",
        "objectives": ["string"],
        "milestones": [
          {{
            "milestone": "string",
            "target_week": 0,
            "success_metric": "string",
            "owner": "string"
          }}
        ],
        "key_activities": ["string"]
      }}
    ],
    "first_90_days": [
      {{
        "week": 0,
        "focus": "string",
        "deliverables": ["string"],
        "decisions_needed": ["string"]
      }}
    ]
  }},
  "kill_criteria": [
    {{
      "metric": "string",
      "threshold": "string",
      "evaluation_point": "string (e.g. Week 4)",
      "action_if_breached": "pivot | pause | adjust"
    }}
  ],
  "next_actions": [
    {{
      "id": "string",
      "title": "string",
      "description": "string",
      "owner": "string",
      "due_weeks": 0,
      "dependencies": ["string"],
      "priority": "p0 | p1 | p2"
    }}
  ],
  "experiments": [
    {{
      "id": "string",
      "hypothesis": "string",
      "test_method": "string",
      "success_criteria": "string",
      "duration_weeks": 0,
      "cost_estimate": 0
    }}
  ]
}}"""

        if feedback:
            prompt += (
                "\n\nOrchestrator feedback for this round:\n"
                + (json.dumps(feedback) if not isinstance(feedback, str) else feedback)
            )

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

        playbook = raw.get("playbook", {})
        kill_criteria = raw.get("kill_criteria", [])
        next_actions = raw.get("next_actions", [])
        experiments = raw.get("experiments", [])

        # --- Playbook ---
        if playbook:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/playbook",
                "value": playbook,
                "meta": self.meta("inference", 0.75),
            })

            phases = playbook.get("phases", [])
            chosen_track = playbook.get("chosen_track", "")

            if chosen_track:
                patches.append({
                    "op": "replace",
                    "path": "/execution/chosen_track",
                    "value": chosen_track,
                    "meta": self.meta("inference", 0.75),
                })

            total_milestones = sum(
                len(p.get("milestones", [])) for p in phases
            )
            facts.append({
                "claim": (
                    f"Created {len(phases)}-phase playbook ({chosen_track}) "
                    f"with {total_milestones} milestones"
                ),
                "confidence": 0.75,
                "sources": [],
            })

            first_90 = playbook.get("first_90_days", [])
            if first_90:
                reasoning_steps.append({
                    "action": "detailed_planning",
                    "thought": (
                        f"Detailed first 90 days: {len(first_90)} weekly plans"
                    ),
                    "confidence": 0.75,
                })

        # --- Kill criteria ---
        if kill_criteria:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/kill_criteria",
                "value": kill_criteria,
                "meta": self.meta("inference", 0.7),
            })

            facts.append({
                "claim": (
                    f"Defined {len(kill_criteria)} kill criteria for "
                    "go/no-go decisions"
                ),
                "confidence": 0.7,
                "sources": [],
            })

            reasoning_steps.append({
                "action": "kill_criteria",
                "thought": (
                    f"Established {len(kill_criteria)} kill criteria: "
                    + ", ".join(
                        kc.get("metric", "") for kc in kill_criteria[:3]
                    )
                ),
                "confidence": 0.7,
            })

        # --- Next actions ---
        # Add revalidation action if decision changed
        if changed_decision:
            next_actions.insert(0, {
                "id": f"revalidate_{changed_decision}",
                "title": f"Revalidate {changed_decision} decision",
                "description": (
                    f"Review and validate the impact of changing "
                    f"{changed_decision} on the execution plan"
                ),
                "owner": "team_lead",
                "due_weeks": 1,
                "dependencies": [],
                "priority": "p0",
            })

        if next_actions:
            patches.append({
                "op": "replace",
                "path": "/execution/next_actions",
                "value": next_actions,
                "meta": self.meta("inference", 0.75),
            })

            p0_count = len(
                [a for a in next_actions if a.get("priority") == "p0"]
            )
            facts.append({
                "claim": (
                    f"Defined {len(next_actions)} actions with "
                    f"{p0_count} P0 priorities"
                ),
                "confidence": 0.75,
                "sources": [],
            })

        # --- Experiments ---
        if experiments:
            patches.append({
                "op": "replace",
                "path": "/execution/experiments",
                "value": experiments,
                "meta": self.meta("inference", 0.7),
            })

            assumptions.append({
                "claim": (
                    f"{len(experiments)} validation experiments proposed; "
                    "outcomes are hypothetical until executed"
                ),
                "confidence": 0.5,
                "sources": [],
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
            "_confidence": 0.75,
            "_summary": (
                f"Playbook complete: {len(playbook.get('phases', []))} phases, "
                f"{len(kill_criteria)} kill criteria, "
                f"{len(next_actions)} actions"
            ),
        }
