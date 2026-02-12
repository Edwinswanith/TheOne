"""PTSynthesizer — third sub-agent in the Product & Tech cluster.

Synthesizes all product_tech cluster outputs (feature scope, feasibility,
compliance) into a unified product & tech summary with graph node updates.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class PTSynthesizer(BaseSubAgent):
    """Synthesizes Product & Tech cluster outputs into a cohesive summary."""

    name = "pt_synthesizer"
    pillar = "product_tech"
    step_number = 3
    total_steps = 3
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

        # Collect outputs from prior sub-agents
        feature_scoper_output = ctx.get("feature_scoper", {})
        feasibility_output = ctx.get("feasibility_checker", {})

        # Extract key data from patches
        feature_data = self._extract_from_patches(
            feature_scoper_output, "/pillars/product_tech/mvp_features"
        )
        roadmap_data = self._extract_from_patches(
            feature_scoper_output, "/pillars/product_tech/roadmap_phases"
        )
        feasibility_data = self._extract_from_patches(
            feasibility_output, "/pillars/product_tech/feasibility_flags"
        )
        compliance_data = self._extract_from_patches(
            feasibility_output, "/pillars/product_tech/compliance_assessment"
        )
        build_vs_buy_data = self._extract_from_patches(
            feasibility_output, "/pillars/product_tech/build_vs_buy"
        )
        security_data = self._extract_from_patches(
            feasibility_output, "/pillars/product_tech/security_plan"
        )

        prompt = f"""You are a product & technology synthesis expert. Combine the outputs \
from feature scoping and feasibility analysis into a unified product & tech \
strategy summary.

Product context:
Name: {idea.get("name", "")}
One-liner: {idea.get("one_liner", "")}

Feature scoping results:
MVP features: {json.dumps(feature_data) if feature_data else "Not available"}
Roadmap phases: {json.dumps(roadmap_data) if roadmap_data else "Not available"}

Feasibility results:
Feasibility flags: {json.dumps(feasibility_data) if feasibility_data else "Not available"}
Compliance assessment: {json.dumps(compliance_data) if compliance_data else "Not available"}
Build vs buy: {json.dumps(build_vs_buy_data) if build_vs_buy_data else "Not available"}
Security plan: {json.dumps(security_data) if security_data else "Not available"}

Prior sub-agent facts: {json.dumps(feature_scoper_output.get("facts", []) + feasibility_output.get("facts", []))}
Prior sub-agent risks: {json.dumps(feature_scoper_output.get("risks", []) + feasibility_output.get("risks", []))}

Synthesize these into a unified view. Identify any contradictions between \
feature scope and feasibility (e.g., features requiring more effort than \
timeline allows, compliance needs conflicting with build choices).

Return a JSON object with these keys:
{{
  "synthesis_summary": "string (2-4 sentence unified product & tech strategy)",
  "key_findings": [
    {{
      "finding": "string",
      "category": "strength | risk | gap | opportunity",
      "severity": "critical | high | medium | low | null"
    }}
  ],
  "contradictions": [
    {{
      "description": "string",
      "between": ["string (sub-agent names)"],
      "resolution": "string"
    }}
  ],
  "graph_nodes": [
    {{
      "id": "string (e.g. product_tech.mvp.summary)",
      "label": "string",
      "content": "string",
      "pillar": "product_tech",
      "level": 2
    }}
  ],
  "pillar_nodes": ["string (node IDs for the pillar sidebar)"]
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
        node_updates: list[dict[str, Any]] = []
        reasoning_steps: list[dict[str, Any]] = []

        synthesis_summary = raw.get("synthesis_summary", "")
        key_findings = raw.get("key_findings", [])
        contradictions = raw.get("contradictions", [])
        graph_nodes = raw.get("graph_nodes", [])
        pillar_nodes = raw.get("pillar_nodes", [])

        # --- Synthesis summary ---
        if synthesis_summary:
            patches.append({
                "op": "replace",
                "path": "/pillars/product_tech/summary",
                "value": synthesis_summary,
                "meta": self.meta("inference", 0.75),
            })

        # --- Key findings ---
        if key_findings:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/key_findings",
                "value": key_findings,
                "meta": self.meta("inference", 0.7),
            })

            strengths = [f for f in key_findings if f.get("category") == "strength"]
            risk_findings = [f for f in key_findings if f.get("category") == "risk"]

            facts.append({
                "claim": (
                    f"Product & Tech synthesis: {len(strengths)} strengths, "
                    f"{len(risk_findings)} risks identified across cluster"
                ),
                "confidence": 0.7,
                "sources": [],
            })

            # Elevate critical findings to risks
            for finding in key_findings:
                if (
                    finding.get("category") == "risk"
                    and finding.get("severity") in ("critical", "high")
                ):
                    risks.append({
                        "id": f"risk_pt_finding_{len(risks)}",
                        "severity": finding["severity"],
                        "description": finding["finding"],
                        "mitigation": "Review in Product & Tech strategy",
                    })

        # --- Contradictions ---
        if contradictions:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/contradictions",
                "value": contradictions,
                "meta": self.meta("inference", 0.8),
            })

            for contradiction in contradictions:
                risks.append({
                    "id": f"risk_pt_contradiction_{len(risks)}",
                    "severity": "high",
                    "description": (
                        f"Contradiction between {', '.join(contradiction.get('between', []))}: "
                        + contradiction.get("description", "")
                    ),
                    "mitigation": contradiction.get("resolution", ""),
                })

            reasoning_steps.append({
                "action": "contradiction_detection",
                "thought": (
                    f"Found {len(contradictions)} contradictions within "
                    "Product & Tech cluster"
                ),
                "confidence": 0.8,
            })

        # --- Graph nodes ---
        for node in graph_nodes:
            node_updates.append({
                "id": node.get("id", ""),
                "label": node.get("label", ""),
                "content": node.get("content", ""),
                "pillar": "product_tech",
                "level": node.get("level", 2),
            })

        # --- Pillar nodes ---
        if pillar_nodes:
            patches.append({
                "op": "replace",
                "path": "/pillars/product_tech/nodes",
                "value": pillar_nodes,
                "meta": self.meta("inference", 0.7),
            })

        reasoning_steps.append({
            "action": "synthesis",
            "thought": (
                f"Synthesized Product & Tech cluster: "
                f"{len(key_findings)} findings, "
                f"{len(contradictions)} contradictions, "
                f"{len(graph_nodes)} graph nodes"
            ),
            "confidence": 0.75,
        })

        return {
            "patches": patches,
            "proposals": [],
            "facts": facts,
            "assumptions": assumptions,
            "risks": risks,
            "required_inputs": [],
            "node_updates": node_updates,
            "reasoning_steps": reasoning_steps,
            "_confidence": 0.75,
            "_summary": (
                f"Product & Tech synthesis complete: "
                f"{len(key_findings)} findings, "
                f"{len(graph_nodes)} graph nodes"
            ),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_from_patches(
        agent_output: dict[str, Any], path: str
    ) -> Any | None:
        """Extract a value from an agent output's patches by JSON Patch path."""
        for patch in agent_output.get("patches", []):
            if patch.get("path") == path:
                return patch.get("value")
        return None
