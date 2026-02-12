"""Tech feasibility agent — defines technical stack and security approach."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent


class TechFeasibilityAgent(BaseAgent):
    """Generates technical architecture and security plan."""

    name = "tech_feasibility_agent"
    pillar = "product_tech"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Build tech feasibility prompt."""
        idea = state.get("idea", {})
        constraints = state.get("constraints", {})
        compliance_level = constraints.get("compliance_level", "none")

        prompt = f"""You are a technical architect. Define technical stack and security approach.

Product:
Name: {idea.get('name', '')}
Domain: {idea.get('domain', '')}
Category: {idea.get('category', '')}

Constraints:
Team size: {constraints.get('team_size', '')}
Compliance level: {compliance_level}

Return JSON:
{{
  "summary": "string (architecture summary)",
  "stack": {{
    "frontend": ["string"],
    "backend": ["string"],
    "database": ["string"],
    "infrastructure": ["string"]
  }},
  "security_plan": {{
    "compliance_requirements": ["string"],
    "security_controls": ["string"],
    "data_protection": ["string"],
    "certifications_needed": ["string"]
  }},
  "scalability_approach": "string",
  "tech_risks": [
    {{
      "risk": "string",
      "mitigation": "string"
    }}
  ]
}}
"""
        return prompt

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse tech feasibility into patches."""
        patches = []
        facts = []
        risks = []

        summary = raw.get("summary", "")
        stack = raw.get("stack", {})
        security_plan = raw.get("security_plan", {})
        scalability_approach = raw.get("scalability_approach", "")
        tech_risks = raw.get("tech_risks", [])

        if summary:
            patches.append({
                "op": "replace",
                "path": "/pillars/product_tech/summary",
                "value": summary,
                "meta": self.meta("inference", 0.7, [])
            })

        if security_plan:
            patches.append({
                "op": "replace",
                "path": "/pillars/product_tech/security_plan",
                "value": security_plan,
                "meta": self.meta("inference", 0.75, [])
            })

            compliance_count = len(security_plan.get("compliance_requirements", []))
            if compliance_count > 0:
                facts.append({
                    "claim": f"Identified {compliance_count} compliance requirements",
                    "confidence": 0.75,
                    "sources": []
                })

        if stack:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/tech_stack",
                "value": stack,
                "meta": self.meta("inference", 0.7, [])
            })

        if scalability_approach:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/scalability_approach",
                "value": scalability_approach,
                "meta": self.meta("inference", 0.7, [])
            })

        for tech_risk in tech_risks:
            risks.append({
                "type": "technical",
                "severity": "medium",
                "description": tech_risk.get("risk", ""),
                "mitigation": tech_risk.get("mitigation", "")
            })

        return {
            "patches": patches,
            "proposals": [],
            "facts": facts,
            "assumptions": [],
            "risks": risks,
            "required_inputs": [],
            "node_updates": []
        }
