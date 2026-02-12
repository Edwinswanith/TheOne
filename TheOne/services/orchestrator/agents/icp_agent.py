"""ICP agent — generates buyer profiles and decision options."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent


class ICPAgent(BaseAgent):
    """Generates ideal customer profile options based on evidence and intake."""

    name = "icp_agent"
    pillar = "customer"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Build ICP generation prompt."""
        idea = state.get("idea", {})
        inputs = state.get("inputs", {})
        intake_answers = inputs.get("intake_answers", [])
        evidence = state.get("evidence", {})

        # Extract intake insights
        buyer_role = next((a.get("value") for a in intake_answers if a.get("question_id") == "buyer_role"), "")
        company_type = next((a.get("value") for a in intake_answers if a.get("question_id") == "company_type"), "")

        prompt = f"""You are an ICP strategist. Generate 2-3 ideal customer profile options.

Product:
Name: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Problem: {idea.get('problem', '')}
Category: {idea.get('category', '')}

Intake insights:
Buyer role: {buyer_role}
Company type: {company_type}

Evidence:
Competitors: {len(evidence.get('competitors', []))} analyzed
Channel signals: {len(evidence.get('channel_signals', []))} identified

Return JSON:
{{
  "profiles": [
    {{
      "id": "icp_1",
      "title": "string (e.g., 'Mid-market SaaS VP of Sales')",
      "company_size": "string (e.g., '50-500 employees')",
      "role": "string",
      "pain_points": ["string"],
      "buying_triggers": ["string"],
      "budget_authority": "string",
      "decision_criteria": ["string"],
      "confidence": 0.8,
      "rationale": "string"
    }}
  ],
  "recommended_id": "icp_1"
}}
"""
        return prompt

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse ICP profiles into patches and proposals."""
        patches = []
        proposals = []
        facts = []

        profiles = raw.get("profiles", [])
        recommended_id = raw.get("recommended_id", profiles[0].get("id") if profiles else "")

        if profiles:
            # Create decision options
            options = []
            for profile in profiles:
                options.append({
                    "id": profile.get("id"),
                    "label": profile.get("title"),
                    "description": profile.get("rationale"),
                    "confidence": profile.get("confidence", 0.7),
                    "data": profile
                })

            # Create ICP decision proposal
            proposals.append({
                "decision_key": "icp",
                "options": options,
                "recommended_option_id": recommended_id,
                "rationale": "ICP options generated from evidence and intake data"
            })

            # Patch the profile data
            patches.append({
                "op": "replace",
                "path": "/decisions/icp/profile",
                "value": profiles[0],  # Default to first profile
                "meta": self.meta("inference", 0.75, [])
            })

            facts.append({
                "claim": f"Generated {len(profiles)} validated ICP options",
                "confidence": 0.75,
                "sources": []
            })

        return {
            "patches": patches,
            "proposals": proposals,
            "facts": facts,
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": []
        }
