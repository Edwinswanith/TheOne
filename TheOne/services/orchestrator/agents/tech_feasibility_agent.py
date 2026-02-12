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

        prompt = f"""You are a technical feasibility analyst. Assess technical feasibility, build-vs-buy decisions, and compliance requirements.

Product:
Name: {idea.get('name', '')}
Domain: {idea.get('domain', '')}
Category: {idea.get('category', '')}

Constraints:
Team size: {constraints.get('team_size', '')}
Compliance level: {compliance_level}

IMPORTANT: Do NOT recommend specific technology stacks. Focus on feasibility assessment, build-vs-buy analysis, and compliance requirements.

Return JSON:
{{
  "summary": "string (feasibility assessment summary)",
  "feasibility_flags": {{
    "is_feasible": true,
    "complexity": "low | medium | high",
    "estimated_build_months": 0,
    "key_risks": ["string"],
    "blockers": ["string"]
  }},
  "build_vs_buy": [
    {{
      "component": "string",
      "recommendation": "build | buy | open_source",
      "rationale": "string",
      "cost_estimate": "string"
    }}
  ],
  "compliance_assessment": {{
    "required_certifications": ["string"],
    "data_handling_requirements": ["string"],
    "regulatory_considerations": ["string"],
    "compliance_timeline_weeks": 0
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
        feasibility_flags = raw.get("feasibility_flags", {})
        build_vs_buy = raw.get("build_vs_buy", [])
        compliance_assessment = raw.get("compliance_assessment", {})
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

        if feasibility_flags:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/feasibility_flags",
                "value": feasibility_flags,
                "meta": self.meta("inference", 0.7, [])
            })
            if not feasibility_flags.get("is_feasible", True):
                risks.append({
                    "type": "technical",
                    "severity": "critical",
                    "description": "Product deemed not feasible with current constraints",
                    "mitigation": "; ".join(feasibility_flags.get("blockers", []))
                })

        if build_vs_buy:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/build_vs_buy",
                "value": build_vs_buy,
                "meta": self.meta("inference", 0.7, [])
            })

        if compliance_assessment:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/compliance_assessment",
                "value": compliance_assessment,
                "meta": self.meta("inference", 0.75, [])
            })
            cert_count = len(compliance_assessment.get("required_certifications", []))
            if cert_count > 0:
                facts.append({
                    "claim": f"Identified {cert_count} required certifications for compliance",
                    "confidence": 0.75,
                    "sources": []
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
