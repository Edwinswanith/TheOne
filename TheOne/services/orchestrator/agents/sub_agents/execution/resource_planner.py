"""ResourcePlanner — third sub-agent in the Execution cluster.

Replaces people_cash_agent. Plans team hiring timeline, budget allocation,
financial projections, and funding needs based on constraints, sales motion,
and feature scope from upstream decisions.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class ResourcePlanner(BaseSubAgent):
    """Plans team needs, budget allocation, and financial projections."""

    name = "resource_planner"
    pillar = "execution"
    step_number = 3
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
        ctx = cluster_context or {}

        # Gather upstream context
        sales_motion_decision = decisions.get("sales_motion", {})
        pricing_decision = decisions.get("pricing", {})
        channel_decision = decisions.get("channels", {})

        # Product scope for resourcing
        pt_pillar = pillars.get("product_tech", {})
        mvp_features = pt_pillar.get("mvp_features", [])
        feasibility_flags = pt_pillar.get("feasibility_flags", {})

        # Playbook context for phased resourcing
        playbook_output = ctx.get("playbook_builder", {})
        playbook_data = None
        for patch in playbook_output.get("patches", []):
            if patch.get("path") == "/pillars/execution/playbook":
                playbook_data = patch.get("value", {})

        phases = playbook_data.get("phases", []) if playbook_data else []

        prompt = f"""You are a resource planning and financial strategist for early-stage \
startups. Plan team hiring, budget allocation, and funding needs.

Product context:
Name: {idea.get("name", "")}
Category: {idea.get("category", "")}

Constraints:
- Team size: {constraints.get("team_size", "")}
- Timeline: {constraints.get("timeline_weeks", "")} weeks
- Budget: ${constraints.get("budget_usd_monthly", "")} monthly

Decisions:
Sales motion: {json.dumps(sales_motion_decision) if sales_motion_decision else "Not yet decided"}
Pricing: {json.dumps(pricing_decision) if pricing_decision else "Not yet decided"}
Channels: {json.dumps(channel_decision) if channel_decision else "Not yet decided"}

Product scope:
MVP features: {len(mvp_features)} features
Feasibility: {json.dumps(feasibility_flags) if feasibility_flags else "Not assessed"}
Build complexity: {feasibility_flags.get("complexity", "unknown") if feasibility_flags else "unknown"}

Execution phases: {json.dumps(phases) if phases else "Not available"}

{"Changed decision: " + changed_decision if changed_decision else "Initial plan"}

Plan the team structure aligned to execution phases and sales motion. Budget \
should cover personnel, infrastructure, marketing, and operational costs. \
Include funding needs if current budget is insufficient.

Return a JSON object with these keys:
{{
  "team_plan": [
    {{
      "role": "string",
      "count": 0,
      "priority": "immediate | phase_2 | phase_3",
      "rationale": "string",
      "monthly_cost_estimate": 0,
      "hire_by_week": 0
    }}
  ],
  "budget_allocation": {{
    "monthly_total": 0,
    "breakdown": {{
      "personnel": 0,
      "infrastructure": 0,
      "marketing": 0,
      "tools_services": 0,
      "other": 0
    }},
    "phase_budgets": [
      {{
        "phase": "string",
        "monthly_budget": 0,
        "key_costs": ["string"]
      }}
    ]
  }},
  "financial_plan": {{
    "monthly_burn": 0,
    "runway_months": 0,
    "break_even_month": 0,
    "revenue_assumptions": ["string"],
    "cost_breakdown": {{
      "personnel": 0,
      "infrastructure": 0,
      "marketing": 0,
      "other": 0
    }}
  }},
  "funding_needs": {{
    "required": true,
    "amount": 0,
    "timing": "string",
    "use_of_funds": ["string"],
    "funding_type": "bootstrapped | pre_seed | seed | series_a"
  }}
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

        team_plan = raw.get("team_plan", [])
        budget_allocation = raw.get("budget_allocation", {})
        financial_plan = raw.get("financial_plan", {})
        funding_needs = raw.get("funding_needs", {})

        constraints = state.get("constraints", {})
        stated_team_size = constraints.get("team_size", 0)
        stated_budget = constraints.get("budget_usd_monthly", 0)

        # --- Team plan ---
        if team_plan:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/team_plan",
                "value": team_plan,
                "meta": self.meta("inference", 0.7),
            })

            immediate = [r for r in team_plan if r.get("priority") == "immediate"]
            total_headcount = sum(r.get("count", 0) for r in team_plan)
            immediate_count = sum(r.get("count", 0) for r in immediate)

            facts.append({
                "claim": (
                    f"Team plan: {total_headcount} total roles, "
                    f"{immediate_count} immediate hires needed"
                ),
                "confidence": 0.7,
                "sources": [],
            })

            # Check against stated team size constraint
            if stated_team_size and immediate_count > stated_team_size:
                risks.append({
                    "id": "risk_team_size_exceed",
                    "severity": "high",
                    "description": (
                        f"Immediate hiring need ({immediate_count}) exceeds "
                        f"stated team size constraint ({stated_team_size})"
                    ),
                    "mitigation": (
                        "Prioritize roles or adjust team size constraint"
                    ),
                })

            reasoning_steps.append({
                "action": "team_planning",
                "thought": (
                    f"Planned {len(team_plan)} roles: "
                    + ", ".join(
                        f"{r.get('role', '')} x{r.get('count', 0)}"
                        for r in team_plan[:4]
                    )
                ),
                "confidence": 0.7,
            })

        # --- Budget allocation ---
        if budget_allocation:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/budget_allocation",
                "value": budget_allocation,
                "meta": self.meta("inference", 0.65),
            })

            monthly_total = budget_allocation.get("monthly_total", 0)
            if stated_budget and monthly_total > stated_budget:
                risks.append({
                    "id": "risk_budget_exceed",
                    "severity": "high",
                    "description": (
                        f"Planned monthly budget (${monthly_total:,}) exceeds "
                        f"stated constraint (${stated_budget:,})"
                    ),
                    "mitigation": "Reduce scope or increase budget",
                })

            reasoning_steps.append({
                "action": "budget_allocation",
                "thought": f"Allocated ${monthly_total:,}/month across categories",
                "confidence": 0.65,
            })

        # --- Financial plan ---
        if financial_plan:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/financial_plan",
                "value": financial_plan,
                "meta": self.meta("inference", 0.6),
            })

            runway = financial_plan.get("runway_months", 0)
            burn = financial_plan.get("monthly_burn", 0)

            facts.append({
                "claim": (
                    f"Financial projection: ${burn:,}/month burn, "
                    f"{runway} months runway"
                ),
                "confidence": 0.6,
                "sources": [],
            })

            if runway and runway < 6:
                risks.append({
                    "id": "risk_short_runway",
                    "severity": "critical",
                    "description": (
                        f"Projected runway of {runway} months is under "
                        "6-month safety threshold"
                    ),
                    "mitigation": "Reduce burn rate or secure additional funding",
                })

            # Revenue assumptions are explicitly assumptions
            for assumption_text in financial_plan.get("revenue_assumptions", []):
                assumptions.append({
                    "claim": assumption_text,
                    "confidence": 0.5,
                    "reason": "Revenue projection based on market assumptions",
                })

            reasoning_steps.append({
                "action": "financial_modeling",
                "thought": (
                    f"Projected ${burn:,}/month burn with {runway}mo runway"
                ),
                "confidence": 0.6,
            })

        # --- Funding needs ---
        if funding_needs:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/funding_needs",
                "value": funding_needs,
                "meta": self.meta("inference", 0.6),
            })

            if funding_needs.get("required", False):
                amount = funding_needs.get("amount", 0)
                funding_type = funding_needs.get("funding_type", "unknown")
                facts.append({
                    "claim": (
                        f"Funding required: ${amount:,} ({funding_type}), "
                        f"timing: {funding_needs.get('timing', 'N/A')}"
                    ),
                    "confidence": 0.6,
                    "sources": [],
                })

                assumptions.append({
                    "claim": (
                        f"Assumed ability to raise ${amount:,} in "
                        f"{funding_needs.get('timing', 'specified timeframe')}"
                    ),
                    "confidence": 0.45,
                    "reason": "Fundraising timeline depends on market conditions",
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
            "_confidence": 0.65,
            "_summary": (
                f"Resource plan complete: {len(team_plan)} roles, "
                f"${budget_allocation.get('monthly_total', 0):,}/month budget, "
                f"{financial_plan.get('runway_months', 0)}mo runway"
            ),
        }
