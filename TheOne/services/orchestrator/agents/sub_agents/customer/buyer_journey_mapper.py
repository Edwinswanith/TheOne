"""BuyerJourneyMapper — second sub-agent in the Customer cluster.

Performs a mandatory Perplexity search for buyer journey patterns, then
synthesizes evaluation stages, criteria, and typical timelines via Gemini.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class BuyerJourneyMapper(BaseSubAgent):
    """Maps the buyer journey using external research and ICP context."""

    name = "buyer_journey_mapper"
    pillar = "customer"
    step_number = 2
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
        """MANDATORY Perplexity call for buyer journey research."""
        inputs = state.get("inputs", {})
        intake_answers = inputs.get("intake_answers", [])
        idea = state.get("idea", {})

        buyer_role = next(
            (a.get("value") for a in intake_answers if a.get("question_id") == "buyer_role"),
            "",
        )
        company_type = next(
            (a.get("value") for a in intake_answers if a.get("question_id") == "company_type"),
            "",
        )

        # Derive domain from idea
        domain = idea.get("category", idea.get("name", "software"))

        # Also try to get buyer role from ICP researcher output
        if not buyer_role and cluster_context:
            icp_output = cluster_context.get("icp_researcher", {})
            for patch in icp_output.get("patches", []):
                if patch.get("path") == "/decisions/icp/profile":
                    profile = patch.get("value", {})
                    buyer_role = buyer_role or profile.get("role", "")
                    break

        # Fallback defaults
        buyer_role = buyer_role or "decision maker"
        company_type = company_type or "technology company"
        domain = domain or "software"

        result = self.provider.search_buyer_journey(buyer_role, company_type, domain)
        return {
            "buyer_journey_research": result,
            "search_params": {
                "buyer_role": buyer_role,
                "company_type": company_type,
                "domain": domain,
            },
        }

    def _enrich_prompt_with_search(
        self, prompt: str, search_data: dict[str, Any]
    ) -> str:
        research = search_data.get("buyer_journey_research", {})
        params = search_data.get("search_params", {})
        block = "\n\n--- External Buyer Journey Research ---\n"
        block += f"Search context: {params.get('buyer_role', '')} at {params.get('company_type', '')}, domain: {params.get('domain', '')}\n"
        block += json.dumps(research, indent=2) + "\n"
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
        ctx = cluster_context or {}

        # Get ICP researcher context
        icp_output = ctx.get("icp_researcher", {})
        icp_facts = icp_output.get("facts", [])

        # Extract recommended ICP profile
        icp_profile: dict[str, Any] = {}
        for patch in icp_output.get("patches", []):
            if patch.get("path") == "/decisions/icp/profile":
                icp_profile = patch.get("value", {})
                break

        prompt = f"""You are a buyer journey analyst specializing in B2B purchase behavior.

Product context:
Name: {idea.get("name", "")}
One-liner: {idea.get("one_liner", "")}
Problem: {idea.get("problem", "")}
Category: {idea.get("category", "")}

Selected ICP profile:
{json.dumps(icp_profile, indent=2) if icp_profile else "No ICP profile available yet."}

ICP research findings:
{json.dumps(icp_facts, indent=2) if icp_facts else "No ICP facts available."}

Using the external buyer journey research data below and the ICP context above,
map the complete buyer journey. Include every stage from initial awareness
through post-purchase, with specific evaluation criteria at each stage.

Return JSON:
{{
  "journey_stages": [
    {{
      "stage": "string (e.g., 'Problem Recognition', 'Research', 'Evaluation', 'Decision', 'Implementation')",
      "description": "string",
      "buyer_actions": ["string"],
      "information_needs": ["string"],
      "touchpoints": ["string (channels where they interact)"],
      "duration": "string (e.g., '1-2 weeks')",
      "drop_off_risk": "high | medium | low",
      "our_strategy": "string (how to engage at this stage)"
    }}
  ],
  "evaluation_criteria": [
    {{
      "criterion": "string",
      "importance": "critical | important | nice_to_have",
      "buyer_perspective": "string (how they evaluate this)",
      "our_positioning": "string (how we should present ourselves)"
    }}
  ],
  "typical_timeline": {{
    "total_duration": "string (e.g., '6-12 weeks')",
    "fastest_path": "string",
    "slowest_path": "string",
    "bottleneck_stage": "string"
  }},
  "stakeholders": [
    {{
      "role": "string",
      "influence": "decision_maker | influencer | blocker | champion",
      "concerns": ["string"],
      "engagement_strategy": "string"
    }}
  ],
  "key_objections_at_each_stage": [
    {{
      "stage": "string",
      "objection": "string",
      "likelihood": "high | medium | low"
    }}
  ]
}}"""

        if changed_decision:
            prompt += f"\n\nNote: The '{changed_decision}' decision has changed. Re-map journey accordingly."

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

        stages = raw.get("journey_stages", [])
        eval_criteria = raw.get("evaluation_criteria", [])
        timeline = raw.get("typical_timeline", {})
        stakeholders = raw.get("stakeholders", [])
        stage_objections = raw.get("key_objections_at_each_stage", [])

        # --- Journey stages ---
        if stages:
            patches.append({
                "op": "add",
                "path": "/pillars/customer/buyer_journey",
                "value": {
                    "stages": stages,
                    "stage_count": len(stages),
                },
                "meta": self.meta("evidence", 0.8),
            })
            facts.append({
                "claim": f"Mapped {len(stages)}-stage buyer journey",
                "confidence": 0.8,
                "sources": [],
            })

            # Flag high drop-off risk stages
            high_risk_stages = [s for s in stages if s.get("drop_off_risk") == "high"]
            for hrs in high_risk_stages:
                risks.append({
                    "id": f"risk_dropoff_{hrs.get('stage', 'unknown').lower().replace(' ', '_')}",
                    "severity": "medium",
                    "description": (
                        f"High drop-off risk at '{hrs.get('stage', '')}' stage"
                    ),
                    "mitigation": hrs.get("our_strategy", "Develop targeted engagement"),
                })

            reasoning_steps.append({
                "action": "journey_mapping",
                "thought": (
                    f"Mapped {len(stages)} stages; "
                    f"{len(high_risk_stages)} have high drop-off risk"
                ),
                "confidence": 0.8,
            })

        # --- Evaluation criteria ---
        if eval_criteria:
            patches.append({
                "op": "add",
                "path": "/pillars/customer/evaluation_criteria",
                "value": eval_criteria,
                "meta": self.meta("evidence", 0.75),
            })
            critical = [c for c in eval_criteria if c.get("importance") == "critical"]
            facts.append({
                "claim": (
                    f"Identified {len(eval_criteria)} evaluation criteria, "
                    f"{len(critical)} critical"
                ),
                "confidence": 0.75,
                "sources": [],
            })

        # --- Timeline ---
        if timeline:
            patches.append({
                "op": "add",
                "path": "/pillars/customer/purchase_timeline",
                "value": timeline,
                "meta": self.meta("evidence", 0.7),
            })
            bottleneck = timeline.get("bottleneck_stage", "")
            if bottleneck:
                reasoning_steps.append({
                    "action": "bottleneck_identification",
                    "thought": (
                        f"Purchase bottleneck at '{bottleneck}' stage; "
                        f"total timeline: {timeline.get('total_duration', 'unknown')}"
                    ),
                    "confidence": 0.7,
                })

        # --- Stakeholders ---
        if stakeholders:
            patches.append({
                "op": "add",
                "path": "/pillars/customer/stakeholders",
                "value": stakeholders,
                "meta": self.meta("evidence", 0.75),
            })
            blockers = [s for s in stakeholders if s.get("influence") == "blocker"]
            if blockers:
                for blk in blockers:
                    risks.append({
                        "id": f"risk_blocker_{blk.get('role', 'unknown').lower().replace(' ', '_')}",
                        "severity": "medium",
                        "description": (
                            f"Stakeholder '{blk.get('role', '')}' identified as potential blocker"
                        ),
                        "mitigation": blk.get("engagement_strategy", "Develop targeted content"),
                    })

        # --- Stage objections (stored for ObjectionAnalyst) ---
        if stage_objections:
            patches.append({
                "op": "add",
                "path": "/pillars/customer/stage_objections",
                "value": stage_objections,
                "meta": self.meta("evidence", 0.7),
            })

        overall_confidence = 0.8 if stages else 0.4

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
                f"Buyer journey mapped: {len(stages)} stages, "
                f"{len(eval_criteria)} criteria, "
                f"{len(stakeholders)} stakeholders"
            ),
        }
