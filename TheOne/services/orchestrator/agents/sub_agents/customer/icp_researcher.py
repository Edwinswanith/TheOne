"""ICPResearcher — first sub-agent in the Customer cluster.

Replaces the legacy icp_agent.py with richer output including pain points,
buying triggers, budget authority, and decision criteria for 2-3 ICP profiles.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class ICPResearcher(BaseSubAgent):
    """Generates rich Ideal Customer Profile options."""

    name = "icp_researcher"
    pillar = "customer"
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
        inputs = state.get("inputs", {})
        intake_answers = inputs.get("intake_answers", [])
        evidence = state.get("evidence", {})
        constraints = state.get("constraints", {})

        # Extract intake insights
        buyer_role = next(
            (a.get("value") for a in intake_answers if a.get("question_id") == "buyer_role"),
            "",
        )
        company_type = next(
            (a.get("value") for a in intake_answers if a.get("question_id") == "company_type"),
            "",
        )
        trigger_event = next(
            (a.get("value") for a in intake_answers if a.get("question_id") == "trigger_event"),
            "",
        )
        current_workaround = next(
            (a.get("value") for a in intake_answers if a.get("question_id") == "current_workaround"),
            "",
        )
        measurable_outcome = next(
            (a.get("value") for a in intake_answers if a.get("question_id") == "measurable_outcome"),
            "",
        )

        # Evidence context
        competitors = evidence.get("competitors", [])
        competitor_summary = ""
        if competitors:
            segments = list({c.get("target_segment", "") for c in competitors if c.get("target_segment")})
            competitor_summary = f"Competitor target segments: {', '.join(segments[:5])}"

        # Weakness map context (from MI cluster if available)
        weakness_context = ""
        weakness_map = evidence.get("weakness_map", {})
        if weakness_map:
            true_gaps = [
                g.get("description", "")
                for g in weakness_map.get("gaps", [])
                if g.get("gap_type") == "true_gap"
            ]
            if true_gaps:
                weakness_context = f"True market gaps identified: {'; '.join(true_gaps[:3])}"

        prompt = f"""You are an ICP strategist specializing in B2B customer segmentation.

Product context:
Name: {idea.get("name", "")}
One-liner: {idea.get("one_liner", "")}
Problem: {idea.get("problem", "")}
Category: {idea.get("category", "")}
Target region: {idea.get("target_region", "US")}

Constraints:
- Team size: {constraints.get("team_size", "")}
- Timeline: {constraints.get("timeline_weeks", "")} weeks
- Budget: ${constraints.get("budget_usd_monthly", "")} monthly

Intake answers:
- Buyer role: {buyer_role}
- Company type: {company_type}
- Trigger event: {trigger_event}
- Current workaround: {current_workaround}
- Measurable outcome: {measurable_outcome}

{competitor_summary}
{weakness_context}

Generate 2-3 detailed Ideal Customer Profiles. Each must include deep
behavioral and organizational insights, not just demographics.

Return JSON:
{{
  "profiles": [
    {{
      "id": "icp_1",
      "title": "string (e.g., 'Mid-market SaaS VP of Sales')",
      "company_size": "string (e.g., '50-500 employees')",
      "industry": "string",
      "role": "string (job title)",
      "seniority": "string (C-level | VP | Director | Manager | IC)",
      "pain_points": [
        {{
          "pain": "string",
          "severity": "high | medium | low",
          "current_solution": "string (how they cope today)"
        }}
      ],
      "buying_triggers": [
        {{
          "trigger": "string",
          "urgency": "high | medium | low",
          "frequency": "string (how often this trigger occurs)"
        }}
      ],
      "budget_authority": {{
        "typical_budget_range": "string",
        "approval_process": "string",
        "decision_timeline": "string"
      }},
      "decision_criteria": [
        {{
          "criterion": "string",
          "weight": "high | medium | low",
          "our_strength": "string (how we meet this criterion)"
        }}
      ],
      "channels_they_trust": ["string"],
      "confidence": 0.8,
      "rationale": "string (why this ICP is a good fit)"
    }}
  ],
  "recommended_id": "icp_1",
  "recommendation_rationale": "string"
}}"""

        if changed_decision:
            prompt += f"\n\nNote: The '{changed_decision}' decision has changed. Re-evaluate ICPs accordingly."

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
        proposals: list[dict[str, Any]] = []
        facts: list[dict[str, Any]] = []
        assumptions: list[dict[str, Any]] = []
        reasoning_steps: list[dict[str, Any]] = []

        profiles = raw.get("profiles", [])
        recommended_id = raw.get("recommended_id", "")
        recommendation_rationale = raw.get("recommendation_rationale", "")

        if not recommended_id and profiles:
            recommended_id = profiles[0].get("id", "")

        if profiles:
            # Build decision options
            options = []
            for profile in profiles:
                options.append({
                    "id": profile.get("id"),
                    "label": profile.get("title"),
                    "description": profile.get("rationale"),
                    "confidence": profile.get("confidence", 0.7),
                    "data": profile,
                })

            # ICP decision proposal
            proposals.append({
                "decision_key": "icp",
                "options": options,
                "recommended_option_id": recommended_id,
                "rationale": recommendation_rationale or "ICP options generated from evidence and intake data",
            })

            # Patch the recommended profile as default
            recommended_profile = next(
                (p for p in profiles if p.get("id") == recommended_id),
                profiles[0],
            )

            patches.append({
                "op": "replace",
                "path": "/decisions/icp/profile",
                "value": recommended_profile,
                "meta": self.meta("inference", 0.75),
            })

            # Facts
            facts.append({
                "claim": f"Generated {len(profiles)} validated ICP profiles",
                "confidence": 0.75,
                "sources": [],
            })

            # Track pain point depth as a quality signal
            total_pains = sum(len(p.get("pain_points", [])) for p in profiles)
            total_triggers = sum(len(p.get("buying_triggers", [])) for p in profiles)

            reasoning_steps.append({
                "action": "icp_generation",
                "thought": (
                    f"Generated {len(profiles)} ICPs with {total_pains} pain points "
                    f"and {total_triggers} buying triggers total"
                ),
                "confidence": 0.75,
            })

            # If any profile has low confidence, flag as assumption
            low_conf = [p for p in profiles if p.get("confidence", 0.7) < 0.6]
            for lc in low_conf:
                assumptions.append({
                    "claim": (
                        f"ICP '{lc.get('title', '')}' has low confidence ({lc.get('confidence', 0)}) "
                        "— needs customer validation"
                    ),
                    "confidence": lc.get("confidence", 0.5),
                    "sources": [],
                })

        overall_confidence = 0.75 if profiles else 0.3

        return {
            "patches": patches,
            "proposals": proposals,
            "facts": facts,
            "assumptions": assumptions,
            "risks": [],
            "required_inputs": [],
            "node_updates": [],
            "reasoning_steps": reasoning_steps,
            "_confidence": overall_confidence,
            "_summary": (
                f"ICP research complete: {len(profiles)} profiles generated"
                + (f", recommended: {recommended_id}" if recommended_id else "")
            ),
        }
