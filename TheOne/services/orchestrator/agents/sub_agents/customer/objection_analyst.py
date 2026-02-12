"""ObjectionAnalyst — third sub-agent in the Customer cluster.

Analyzes ICP profiles and buyer journey data to identify the top objections
buyers will raise and generates evidence-backed counter-strategies.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class ObjectionAnalyst(BaseSubAgent):
    """Identifies top buyer objections and counter-strategies."""

    name = "objection_analyst"
    pillar = "customer"
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
        ctx = cluster_context or {}

        # Extract ICP profile from icp_researcher
        icp_output = ctx.get("icp_researcher", {})
        icp_profile: dict[str, Any] = {}
        for patch in icp_output.get("patches", []):
            if patch.get("path") == "/decisions/icp/profile":
                icp_profile = patch.get("value", {})
                break

        # Extract buyer journey from buyer_journey_mapper
        journey_output = ctx.get("buyer_journey_mapper", {})
        journey_stages: list[dict[str, Any]] = []
        eval_criteria: list[dict[str, Any]] = []
        stakeholders: list[dict[str, Any]] = []
        stage_objections: list[dict[str, Any]] = []

        for patch in journey_output.get("patches", []):
            path = patch.get("path", "")
            if path == "/pillars/customer/buyer_journey":
                journey_stages = patch.get("value", {}).get("stages", [])
            elif path == "/pillars/customer/evaluation_criteria":
                eval_criteria = patch.get("value", [])
            elif path == "/pillars/customer/stakeholders":
                stakeholders = patch.get("value", [])
            elif path == "/pillars/customer/stage_objections":
                stage_objections = patch.get("value", [])

        # Competitor weaknesses (from state evidence)
        evidence = state.get("evidence", {})
        competitor_weaknesses: list[str] = []
        for comp in evidence.get("competitors", []):
            for w in comp.get("weaknesses", []):
                competitor_weaknesses.append(f"{comp.get('name', '')}: {w}")

        prompt = f"""You are a sales objection strategist specializing in B2B software.

Product context:
Name: {idea.get("name", "")}
One-liner: {idea.get("one_liner", "")}
Problem: {idea.get("problem", "")}
Category: {idea.get("category", "")}

Constraints:
- Team size: {constraints.get("team_size", "")}
- Timeline: {constraints.get("timeline_weeks", "")} weeks
- Budget: ${constraints.get("budget_usd_monthly", "")} monthly

Target ICP:
{json.dumps(icp_profile, indent=2) if icp_profile else "No ICP profile available."}

Buyer journey stages:
{json.dumps(journey_stages, indent=2) if journey_stages else "No journey data."}

Evaluation criteria:
{json.dumps(eval_criteria, indent=2) if eval_criteria else "No criteria data."}

Key stakeholders:
{json.dumps(stakeholders, indent=2) if stakeholders else "No stakeholder data."}

Known stage-specific objections:
{json.dumps(stage_objections, indent=2) if stage_objections else "None identified yet."}

Competitor weaknesses we can exploit:
{json.dumps(competitor_weaknesses[:10], indent=2) if competitor_weaknesses else "None available."}

Identify ALL objections a buyer will raise and provide counter-strategies.
Prioritize by likelihood and deal-killing potential.

Return JSON:
{{
  "objections": [
    {{
      "id": "obj_1",
      "objection": "string (what the buyer says)",
      "category": "price | risk | timing | competition | trust | technical | organizational",
      "likelihood": "high | medium | low",
      "deal_killer": true,
      "buyer_stage": "string (at which journey stage this typically appears)",
      "stakeholder_source": "string (which stakeholder role raises this)",
      "root_cause": "string (the real concern behind the objection)",
      "counter_strategy": {{
        "approach": "string (reframe | evidence | social_proof | concession | education)",
        "talk_track": "string (what to say)",
        "proof_points": ["string (evidence that supports the counter)"],
        "avoid": "string (what NOT to say)"
      }},
      "competitive_angle": "string or null (how competitor weaknesses help counter this)"
    }}
  ],
  "objection_heat_map": {{
    "price": 0,
    "risk": 0,
    "timing": 0,
    "competition": 0,
    "trust": 0,
    "technical": 0,
    "organizational": 0
  }},
  "top_deal_killers": ["string (objection IDs)"],
  "overall_objection_severity": "high | medium | low"
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

        objections = raw.get("objections", [])
        heat_map = raw.get("objection_heat_map", {})
        deal_killers = raw.get("top_deal_killers", [])
        severity = raw.get("overall_objection_severity", "medium")

        if objections:
            # Patch objection map
            patches.append({
                "op": "add",
                "path": "/pillars/customer/objection_map",
                "value": {
                    "objections": objections,
                    "heat_map": heat_map,
                    "deal_killers": deal_killers,
                    "overall_severity": severity,
                },
                "meta": self.meta("inference", 0.7),
            })

            facts.append({
                "claim": (
                    f"Identified {len(objections)} buyer objections; "
                    f"{len(deal_killers)} are potential deal killers"
                ),
                "confidence": 0.7,
                "sources": [],
            })

            # Categorize reasoning
            high_likelihood = [o for o in objections if o.get("likelihood") == "high"]
            dk_objs = [o for o in objections if o.get("deal_killer")]

            reasoning_steps.append({
                "action": "objection_analysis",
                "thought": (
                    f"Analyzed {len(objections)} objections: "
                    f"{len(high_likelihood)} high-likelihood, "
                    f"{len(dk_objs)} deal-killers"
                ),
                "confidence": 0.7,
            })

            # Heat map analysis
            if heat_map:
                hottest = max(heat_map, key=lambda k: heat_map.get(k, 0)) if heat_map else None
                if hottest:
                    reasoning_steps.append({
                        "action": "heat_map_analysis",
                        "thought": (
                            f"Objection heat map hottest category: '{hottest}' "
                            f"({heat_map.get(hottest, 0)} objections)"
                        ),
                        "confidence": 0.7,
                    })

            # Deal killers as risks
            for dk_id in deal_killers:
                dk_obj = next(
                    (o for o in objections if o.get("id") == dk_id), None
                )
                if dk_obj:
                    risks.append({
                        "id": f"risk_objection_{dk_id}",
                        "severity": "high",
                        "description": (
                            f"Deal-killing objection: '{dk_obj.get('objection', '')}' "
                            f"(category: {dk_obj.get('category', 'unknown')})"
                        ),
                        "mitigation": (
                            dk_obj.get("counter_strategy", {}).get("talk_track", "")
                            or "Develop counter-strategy"
                        ),
                    })

            # If overall severity is high, add an assumption about deal difficulty
            if severity == "high":
                assumptions.append({
                    "claim": (
                        "High overall objection severity suggests longer sales cycles "
                        "and possible need for enterprise-grade trust signals"
                    ),
                    "confidence": 0.6,
                    "sources": [],
                })

        overall_confidence = 0.7 if objections else 0.4

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
                f"Objection analysis: {len(objections)} objections, "
                f"{len(deal_killers)} deal-killers, severity={severity}"
            ),
        }
