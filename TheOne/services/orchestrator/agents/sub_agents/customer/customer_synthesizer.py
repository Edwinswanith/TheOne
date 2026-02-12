"""CustomerSynthesizer — fourth and final sub-agent in the Customer cluster.

Synthesizes outputs from ICPResearcher, BuyerJourneyMapper, and
ObjectionAnalyst into a cohesive customer intelligence summary and
produces graph node updates for the Customer pillar.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class CustomerSynthesizer(BaseSubAgent):
    """Produces the unified Customer pillar summary and graph nodes."""

    name = "customer_synthesizer"
    pillar = "customer"
    step_number = 4
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
        ctx = cluster_context or {}

        # Collect all prior sub-agent outputs
        icp_output = ctx.get("icp_researcher", {})
        journey_output = ctx.get("buyer_journey_mapper", {})
        objection_output = ctx.get("objection_analyst", {})

        # Extract key facts and findings
        icp_facts = icp_output.get("facts", [])
        icp_risks = icp_output.get("risks", [])
        journey_facts = journey_output.get("facts", [])
        journey_risks = journey_output.get("risks", [])
        objection_facts = objection_output.get("facts", [])
        objection_risks = objection_output.get("risks", [])

        all_facts = icp_facts + journey_facts + objection_facts
        all_risks = icp_risks + journey_risks + objection_risks

        # Extract ICP profile
        icp_profile: dict[str, Any] = {}
        for patch in icp_output.get("patches", []):
            if patch.get("path") == "/decisions/icp/profile":
                icp_profile = patch.get("value", {})
                break

        # Extract objection severity
        objection_severity = "medium"
        for patch in objection_output.get("patches", []):
            if patch.get("path") == "/pillars/customer/objection_map":
                objection_severity = patch.get("value", {}).get(
                    "overall_severity", "medium"
                )
                break

        prompt = f"""You are a senior customer strategy consultant. Synthesize the following
customer research into a cohesive Customer Intelligence brief.

Product context:
Name: {idea.get("name", "")}
One-liner: {idea.get("one_liner", "")}
Problem: {idea.get("problem", "")}
Category: {idea.get("category", "")}

Recommended ICP:
{json.dumps(icp_profile, indent=2) if icp_profile else "Not available."}

All collected facts ({len(all_facts)} total):
{json.dumps(all_facts, indent=2)}

All identified risks ({len(all_risks)} total):
{json.dumps(all_risks, indent=2)}

Objection severity: {objection_severity}

Return JSON:
{{
  "executive_summary": "string (2-3 paragraphs synthesizing the full customer picture)",
  "customer_readiness": "high | medium | low",
  "customer_readiness_rationale": "string",
  "key_insights": [
    {{
      "insight": "string",
      "implication_for_gtm": "string",
      "confidence": 0.8,
      "source_type": "evidence | inference | assumption"
    }}
  ],
  "recommended_engagement_model": {{
    "model": "string (PLG | sales-led | hybrid | community-led)",
    "rationale": "string",
    "first_touch_strategy": "string",
    "nurture_strategy": "string"
  }},
  "top_risks": [
    {{
      "risk": "string",
      "severity": "high | medium | low",
      "mitigation": "string"
    }}
  ],
  "graph_nodes": [
    {{
      "node_id": "customer.icp.summary",
      "title": "string",
      "body": "string (2-3 sentences)"
    }},
    {{
      "node_id": "customer.journey",
      "title": "string",
      "body": "string"
    }},
    {{
      "node_id": "customer.objections",
      "title": "string",
      "body": "string"
    }},
    {{
      "node_id": "customer.engagement",
      "title": "string",
      "body": "string"
    }}
  ]
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
        node_updates: list[dict[str, Any]] = []
        reasoning_steps: list[dict[str, Any]] = []

        executive_summary = raw.get("executive_summary", "")
        readiness = raw.get("customer_readiness", "medium")
        readiness_rationale = raw.get("customer_readiness_rationale", "")
        key_insights = raw.get("key_insights", [])
        engagement_model = raw.get("recommended_engagement_model", {})
        top_risks = raw.get("top_risks", [])
        graph_nodes = raw.get("graph_nodes", [])

        # --- Pillar summary ---
        if executive_summary:
            patches.append({
                "op": "replace",
                "path": "/pillars/customer/summary",
                "value": executive_summary,
                "meta": self.meta("inference", 0.75),
            })

        # --- Customer readiness ---
        patches.append({
            "op": "add",
            "path": "/pillars/customer/readiness",
            "value": {
                "rating": readiness,
                "rationale": readiness_rationale,
            },
            "meta": self.meta("inference", 0.7),
        })

        # --- Engagement model ---
        if engagement_model:
            patches.append({
                "op": "add",
                "path": "/pillars/customer/engagement_model",
                "value": engagement_model,
                "meta": self.meta("inference", 0.7),
            })
            reasoning_steps.append({
                "action": "engagement_recommendation",
                "thought": (
                    f"Recommending {engagement_model.get('model', 'unknown')} engagement model: "
                    f"{engagement_model.get('rationale', '')}"
                ),
                "confidence": 0.7,
            })

        # --- Key insights as facts or assumptions ---
        for insight in key_insights:
            src_type = insight.get("source_type", "inference")
            conf = insight.get("confidence", 0.7)
            entry = {
                "claim": (
                    f"{insight.get('insight', '')} "
                    f"-> GTM implication: {insight.get('implication_for_gtm', '')}"
                ),
                "confidence": conf,
                "sources": [],
            }
            if src_type == "assumption" or conf < 0.6:
                assumptions.append(entry)
            else:
                facts.append(entry)

        # --- Risks ---
        for risk_entry in top_risks:
            risk_id = (
                f"risk_cust_{risk_entry.get('risk', 'unknown')[:30].replace(' ', '_').lower()}"
            )
            risks.append({
                "id": risk_id,
                "severity": risk_entry.get("severity", "medium"),
                "description": risk_entry.get("risk", ""),
                "mitigation": risk_entry.get("mitigation", ""),
            })

        # --- Graph node updates ---
        for gn in graph_nodes:
            node_id = gn.get("node_id", "")
            if node_id:
                node_updates.append({
                    "node_id": node_id,
                    "title": gn.get("title", ""),
                    "body": gn.get("body", ""),
                    "pillar": "customer",
                })

        # Ensure standard graph nodes exist
        existing_ids = {n.get("node_id") for n in node_updates}
        default_nodes = {
            "customer.icp.summary": (
                "Ideal Customer Profile",
                executive_summary[:200] if executive_summary else "",
            ),
            "customer.journey": ("Buyer Journey", ""),
            "customer.objections": ("Key Objections", ""),
            "customer.engagement": ("Engagement Model", ""),
        }
        for nid, (title, body) in default_nodes.items():
            if nid not in existing_ids and body:
                node_updates.append({
                    "node_id": nid,
                    "title": title,
                    "body": body,
                    "pillar": "customer",
                })

        reasoning_steps.append({
            "action": "synthesis",
            "thought": (
                f"Synthesized customer intelligence: readiness={readiness}, "
                f"{len(key_insights)} insights, {len(top_risks)} risks, "
                f"{len(node_updates)} graph nodes"
            ),
            "confidence": 0.75,
        })

        # Overall confidence
        confidence_map = {"high": 0.8, "medium": 0.7, "low": 0.6}
        overall_confidence = confidence_map.get(readiness, 0.7)

        return {
            "patches": patches,
            "proposals": [],
            "facts": facts,
            "assumptions": assumptions,
            "risks": risks,
            "required_inputs": [],
            "node_updates": node_updates,
            "reasoning_steps": reasoning_steps,
            "_confidence": overall_confidence,
            "_summary": (
                f"Customer synthesis complete: readiness={readiness}, "
                f"{len(key_insights)} insights, {len(node_updates)} graph nodes"
            ),
        }
