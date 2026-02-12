"""WedgeBuilder — builds competitive wedge (unique market entry point)."""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class WedgeBuilder(BaseSubAgent):
    """Builds a competitive wedge: the unique entry point into the market.

    Consumes CategoryFramer output from cluster_context. If Market Intelligence
    artifacts contain red-flag gap_types ("attempted_and_failed" or
    "well_funded_incumbent"), the wedge must explicitly address how the product
    overcomes those barriers.
    """

    name = "wedge_builder"
    pillar = "positioning_pricing"
    step_number = 2
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

        competitors = evidence.get("competitors", [])
        weakness_map = evidence.get("weakness_map", [])

        # Extract category_framer output from cluster context
        ctx = cluster_context or {}
        framer_output = ctx.get("category_framer", {})
        framer_proposals = framer_output.get("proposals", [])
        framer_patches = framer_output.get("patches", [])

        # Check for MI red flags in artifacts
        mi_data = artifacts.get("market_intelligence", {})
        gap_type = mi_data.get("gap_type", "")
        red_flags = gap_type in ("attempted_and_failed", "well_funded_incumbent")

        red_flag_section = ""
        if red_flags:
            red_flag_section = f"""
## CRITICAL: Market Red Flag Detected
Gap type: {gap_type}
{"Previous attempts in this space have failed. Your wedge MUST explicitly address why this attempt will succeed where others failed. Include specific differentiators or changed market conditions." if gap_type == "attempted_and_failed" else ""}
{"A well-funded incumbent dominates this market. Your wedge MUST explicitly address how to enter without triggering a competitive response, or how to survive one." if gap_type == "well_funded_incumbent" else ""}
You MUST include a 'barrier_response' field in your output that directly \
addresses how the product overcomes this specific barrier.
"""

        prompt = f"""You are a competitive strategy expert specializing in \
market entry wedges. A "wedge" is the narrow, defensible entry point that \
lets a new product gain initial traction in a market.

## Product
Name: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Problem: {idea.get('problem', '')}
Category: {idea.get('category', '')}
Domain: {idea.get('domain', '')}

## Selected ICP: {selected_icp_id}

## Category Framer Output
Proposals: {json.dumps(framer_proposals, default=str)}
Key patches: {json.dumps(framer_patches[:3], default=str)}

## Competitive Landscape
Competitors: {json.dumps(competitors[:5], default=str)}
Weakness Map: {json.dumps(weakness_map[:5], default=str)}
{red_flag_section}

## Instructions
Build a competitive wedge strategy. The wedge must:
1. Identify a specific, narrow use case where the product wins decisively
2. Exploit competitor weaknesses identified in the weakness map
3. Align with the selected positioning framework from CategoryFramer
4. Be defensible against competitive response
5. Define the "land" strategy (initial foothold) and "expand" path

{f"NOTE: Decision '{changed_decision}' changed. Re-evaluate wedge accordingly." if changed_decision else ""}
{f"ORCHESTRATOR FEEDBACK: {feedback}" if feedback else ""}

Return JSON:
{{
  "wedge": {{
    "entry_point": "string (the specific narrow use case)",
    "target_pain": "string (the acute pain point being solved)",
    "why_us": "string (why this product wins here specifically)",
    "competitor_blind_spot": "string (what incumbents miss or ignore)",
    "land_strategy": "string (how to get first 10 customers)",
    "expand_path": "string (how first customers become many)",
    "defensibility": "string (why competitors can't easily copy)",
    "confidence": 0.8
  }},
  {"'barrier_response': 'string (REQUIRED: how the product overcomes the detected market barrier)'," if red_flags else ""}
  "positioning_alignment": {{
    "selected_framework_id": "string",
    "alignment_score": 0.9,
    "adjustments_needed": ["string"]
  }},
  "risks": [
    {{
      "risk": "string",
      "severity": "low | medium | high",
      "mitigation": "string"
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

        wedge = raw.get("wedge", {})
        barrier_response = raw.get("barrier_response", "")
        positioning_alignment = raw.get("positioning_alignment", {})
        raw_risks = raw.get("risks", [])

        wedge_confidence = wedge.get("confidence", 0.7)

        if wedge:
            # Patch the positioning wedge data into the pillar
            patches.append({
                "op": "replace",
                "path": "/pillars/positioning_pricing/wedge",
                "value": wedge,
                "meta": self.meta("inference", wedge_confidence),
            })

            # Store in artifacts for downstream sub-agents
            patches.append({
                "op": "replace",
                "path": "/artifacts/positioning_pricing/wedge",
                "value": {
                    **wedge,
                    "barrier_response": barrier_response,
                    "positioning_alignment": positioning_alignment,
                },
                "meta": self.meta("inference", wedge_confidence),
            })

            facts.append({
                "claim": (
                    f"Competitive wedge identified: {wedge.get('entry_point', '')}. "
                    f"Exploits blind spot: {wedge.get('competitor_blind_spot', '')}"
                ),
                "confidence": wedge_confidence,
                "sources": [],
            })

            if wedge.get("land_strategy"):
                facts.append({
                    "claim": (
                        f"Land strategy defined: {wedge.get('land_strategy', '')}"
                    ),
                    "confidence": wedge_confidence * 0.9,
                    "sources": [],
                })

        if barrier_response:
            facts.append({
                "claim": (
                    f"Market barrier response: {barrier_response}"
                ),
                "confidence": 0.65,
                "sources": [],
            })

        # Check MI red-flag alignment
        artifacts = state.get("artifacts", {})
        mi_data = artifacts.get("market_intelligence", {})
        gap_type = mi_data.get("gap_type", "")
        if gap_type in ("attempted_and_failed", "well_funded_incumbent"):
            if not barrier_response:
                risks.append({
                    "type": "unaddressed_barrier",
                    "severity": "critical",
                    "description": (
                        f"Market barrier ({gap_type}) detected but wedge "
                        "does not include an explicit barrier response."
                    ),
                })
                assumptions.append({
                    "claim": (
                        "Wedge strategy may not adequately address "
                        f"market barrier: {gap_type}"
                    ),
                    "confidence": 0.4,
                })

        for r in raw_risks:
            risks.append({
                "type": "wedge_risk",
                "severity": r.get("severity", "medium"),
                "description": (
                    f"{r.get('risk', '')} | "
                    f"Mitigation: {r.get('mitigation', '')}"
                ),
            })

        alignment_score = positioning_alignment.get("alignment_score", 0)
        if alignment_score < 0.7:
            assumptions.append({
                "claim": (
                    f"Wedge alignment with positioning framework is "
                    f"low ({alignment_score}); may need framework adjustment"
                ),
                "confidence": 0.6,
            })

        reasoning_steps = [
            {
                "action": "wedge_analysis",
                "thought": (
                    f"Built competitive wedge targeting "
                    f"'{wedge.get('entry_point', 'unknown')}' with "
                    f"confidence {wedge_confidence}"
                ),
                "confidence": wedge_confidence,
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
            "_confidence": wedge_confidence,
            "_summary": (
                f"Wedge built: {wedge.get('entry_point', 'N/A')} "
                f"(confidence: {wedge_confidence})"
            ),
        }
