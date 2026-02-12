"""FeasibilityChecker — second sub-agent in the Product & Tech cluster.

Assesses technical feasibility, build-vs-buy decisions, and compliance
requirements. For vertical SaaS products, runs external search to discover
domain-specific data requirements (Issue 6 fix).

IMPORTANT: Always includes compliance assessment regardless of compliance_level.
Cross-references ICP to proactively flag compliance needs for enterprise or
regulated-industry buyers.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class FeasibilityChecker(BaseSubAgent):
    """Assesses feasibility, build-vs-buy, and compliance for the product."""

    name = "feasibility_checker"
    pillar = "product_tech"
    step_number = 2
    total_steps = 3
    uses_external_search = True  # Conditional — only for vertical SaaS

    # ------------------------------------------------------------------
    # External search (conditional)
    # ------------------------------------------------------------------

    def _run_searches(
        self,
        state: dict[str, Any],
        cluster_context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """For vertical SaaS, search domain-specific data requirements."""
        idea = state.get("idea", {})
        category = idea.get("category", "")

        # Only run external search for vertical SaaS / domain-specific products
        is_vertical = category in (
            "b2b_saas", "vertical_saas", "healthtech", "fintech",
            "edtech", "legaltech", "proptech",
        )
        domain = idea.get("domain", "") or idea.get("name", "")

        if not is_vertical or not domain:
            return None

        result = self.provider.search_domain_data_requirements(domain)
        return {"domain_data_requirements": result, "domain": domain}

    def _enrich_prompt_with_search(
        self, prompt: str, search_data: dict[str, Any]
    ) -> str:
        """Append domain data requirements to the prompt."""
        domain = search_data.get("domain", "")
        reqs = search_data.get("domain_data_requirements", {})
        block = f"\n\n--- Domain-Specific Data Requirements ({domain}) ---\n"
        block += json.dumps(reqs, indent=2) + "\n"
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
        constraints = state.get("constraints", {})
        decisions = state.get("decisions", {})
        pillars = state.get("pillars", {})
        inputs_ = state.get("inputs", {})

        compliance_level = constraints.get("compliance_level", "none")
        icp_decision = decisions.get("icp", {})

        # Pull feature scope from prior sub-agent context
        feature_context = {}
        if cluster_context and "feature_scoper" in cluster_context:
            fs_output = cluster_context["feature_scoper"]
            fs_patches = fs_output.get("patches", [])
            for patch in fs_patches:
                if patch.get("path") == "/pillars/product_tech/mvp_features":
                    feature_context["mvp_features"] = patch.get("value", [])
                elif patch.get("path") == "/pillars/product_tech/roadmap_phases":
                    feature_context["roadmap_phases"] = patch.get("value", [])

        # Detect enterprise/regulated ICP for proactive compliance flagging
        icp_selected = icp_decision.get("selected_option_id", "")
        buyer_role = inputs_.get("buyer_role", "")
        company_type = inputs_.get("company_type", "")
        is_enterprise_icp = any(
            kw in str(icp_selected).lower() + str(buyer_role).lower()
            + str(company_type).lower()
            for kw in ("enterprise", "regulated", "healthcare", "financial",
                        "government", "bank", "hospital", "pharma", "insurance")
        )

        prompt = f"""You are a technical feasibility analyst. Assess feasibility, build-vs-buy \
decisions, and compliance requirements.

IMPORTANT: You MUST include a compliance assessment regardless of the stated \
compliance level. If the ICP targets enterprise buyers or regulated industries, \
proactively flag compliance needs even if compliance_level is "none".

Product context:
Name: {idea.get("name", "")}
One-liner: {idea.get("one_liner", "")}
Problem: {idea.get("problem", "")}
Domain: {idea.get("domain", "") or idea.get("name", "")}
Category: {idea.get("category", "")}

ICP decision: {json.dumps(icp_decision) if icp_decision else "Not yet decided"}
Enterprise/regulated ICP detected: {is_enterprise_icp}
Buyer role: {buyer_role}
Company type: {company_type}

Feature scope from prior analysis:
{json.dumps(feature_context, indent=2) if feature_context else "Not yet available"}

Constraints:
- Team size: {constraints.get("team_size", "")}
- Timeline: {constraints.get("timeline_weeks", "")} weeks
- Budget: ${constraints.get("budget_usd_monthly", "")} monthly
- Stated compliance level: {compliance_level}

{"Changed decision: " + changed_decision if changed_decision else "Initial analysis"}

DO NOT recommend specific technology stacks. Focus on feasibility assessment, \
build-vs-buy analysis, and compliance/security requirements.

Return a JSON object with these keys:
{{
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
      "cost_estimate": "string",
      "time_savings_weeks": 0
    }}
  ],
  "compliance_assessment": {{
    "effective_compliance_level": "none | low | medium | high",
    "required_certifications": ["string"],
    "data_handling_requirements": ["string"],
    "regulatory_considerations": ["string"],
    "compliance_timeline_weeks": 0,
    "proactive_flags": ["string (compliance needs inferred from ICP/domain)"]
  }},
  "security_plan": {{
    "compliance_requirements": ["string"],
    "security_controls": ["string"],
    "data_protection": ["string"],
    "certifications_needed": ["string"]
  }},
  "scalability_approach": "string (high-level scalability strategy)",
  "tech_risks": [
    {{
      "risk": "string",
      "severity": "critical | high | medium | low",
      "mitigation": "string"
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

        feasibility_flags = raw.get("feasibility_flags", {})
        build_vs_buy = raw.get("build_vs_buy", [])
        compliance_assessment = raw.get("compliance_assessment", {})
        security_plan = raw.get("security_plan", {})
        scalability_approach = raw.get("scalability_approach", "")
        tech_risks = raw.get("tech_risks", [])

        # --- Feasibility flags ---
        if feasibility_flags:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/feasibility_flags",
                "value": feasibility_flags,
                "meta": self.meta("inference", 0.7),
            })

            complexity = feasibility_flags.get("complexity", "medium")
            is_feasible = feasibility_flags.get("is_feasible", True)
            build_months = feasibility_flags.get("estimated_build_months", 0)

            facts.append({
                "claim": (
                    f"Technical feasibility: {'feasible' if is_feasible else 'NOT feasible'}, "
                    f"complexity={complexity}, estimated {build_months} months to build"
                ),
                "confidence": 0.7,
                "sources": [],
            })

            if not is_feasible:
                risks.append({
                    "id": "risk_not_feasible",
                    "severity": "critical",
                    "description": "Product deemed not feasible with current constraints",
                    "mitigation": "; ".join(
                        feasibility_flags.get("blockers", [])
                    ),
                })

            blockers = feasibility_flags.get("blockers", [])
            if blockers:
                reasoning_steps.append({
                    "action": "feasibility_assessment",
                    "thought": (
                        f"Identified {len(blockers)} blockers: "
                        + "; ".join(blockers[:3])
                    ),
                    "confidence": 0.7,
                })

        # --- Build vs buy ---
        if build_vs_buy:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/build_vs_buy",
                "value": build_vs_buy,
                "meta": self.meta("inference", 0.7),
            })

            buy_count = len(
                [c for c in build_vs_buy if c.get("recommendation") == "buy"]
            )
            build_count = len(
                [c for c in build_vs_buy if c.get("recommendation") == "build"]
            )
            facts.append({
                "claim": (
                    f"Build-vs-buy analysis: {build_count} build, {buy_count} buy, "
                    f"{len(build_vs_buy) - build_count - buy_count} open-source"
                ),
                "confidence": 0.7,
                "sources": [],
            })

            reasoning_steps.append({
                "action": "build_vs_buy_analysis",
                "thought": (
                    f"Evaluated {len(build_vs_buy)} components for build-vs-buy decisions"
                ),
                "confidence": 0.7,
            })

        # --- Compliance assessment (always present) ---
        if compliance_assessment:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/compliance_assessment",
                "value": compliance_assessment,
                "meta": self.meta("inference", 0.75),
            })

            certs = compliance_assessment.get("required_certifications", [])
            proactive_flags = compliance_assessment.get("proactive_flags", [])
            effective_level = compliance_assessment.get(
                "effective_compliance_level", "none"
            )

            if certs:
                facts.append({
                    "claim": (
                        f"Identified {len(certs)} required certifications: "
                        + ", ".join(certs[:5])
                    ),
                    "confidence": 0.75,
                    "sources": [],
                })

            if proactive_flags:
                for flag in proactive_flags:
                    risks.append({
                        "id": f"risk_compliance_{len(risks)}",
                        "severity": "medium",
                        "description": f"Proactive compliance flag: {flag}",
                        "mitigation": "Review with legal/compliance team",
                    })

            # Warn if stated level differs from effective level
            stated_level = state.get("constraints", {}).get(
                "compliance_level", "none"
            )
            if effective_level != stated_level and effective_level != "none":
                risks.append({
                    "id": "risk_compliance_mismatch",
                    "severity": "high",
                    "description": (
                        f"Stated compliance level is '{stated_level}' but ICP/domain "
                        f"analysis suggests '{effective_level}' is needed"
                    ),
                    "mitigation": (
                        "Update compliance_level constraint or review ICP targeting"
                    ),
                })

            reasoning_steps.append({
                "action": "compliance_assessment",
                "thought": (
                    f"Compliance level: effective={effective_level}, "
                    f"{len(certs)} certifications, "
                    f"{len(proactive_flags)} proactive flags"
                ),
                "confidence": 0.75,
            })

        # --- Security plan ---
        if security_plan:
            patches.append({
                "op": "replace",
                "path": "/pillars/product_tech/security_plan",
                "value": security_plan,
                "meta": self.meta("inference", 0.75),
            })

            controls = security_plan.get("security_controls", [])
            if controls:
                facts.append({
                    "claim": f"Defined {len(controls)} security controls",
                    "confidence": 0.75,
                    "sources": [],
                })

        # --- Scalability approach ---
        if scalability_approach:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/scalability_approach",
                "value": scalability_approach,
                "meta": self.meta("inference", 0.7),
            })

        # --- Tech risks ---
        for tech_risk in tech_risks:
            severity = tech_risk.get("severity", "medium")
            risks.append({
                "id": f"risk_tech_{len(risks)}",
                "severity": severity,
                "description": tech_risk.get("risk", ""),
                "mitigation": tech_risk.get("mitigation", ""),
            })

        # --- Overall confidence ---
        has_external = bool(
            cluster_context
            and "feature_scoper" in (cluster_context or {})
        )
        overall_confidence = 0.75 if has_external else 0.65

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
                f"Feasibility check complete: "
                f"{'feasible' if feasibility_flags.get('is_feasible', True) else 'NOT feasible'}, "
                f"{len(build_vs_buy)} build-vs-buy decisions, "
                f"{len(compliance_assessment.get('required_certifications', []))} certifications"
            ),
        }
