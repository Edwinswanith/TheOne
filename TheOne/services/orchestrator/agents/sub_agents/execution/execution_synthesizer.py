"""ExecutionSynthesizer — fourth sub-agent in the Execution cluster.

Synthesizes all execution cluster outputs (playbook, KPIs, resource plan)
into a unified execution summary with graph node updates. Detects cross-cutting
contradictions (e.g., budget overruns vs. team plan, KPIs vs. kill criteria).
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class ExecutionSynthesizer(BaseSubAgent):
    """Synthesizes Execution cluster outputs into a cohesive summary."""

    name = "execution_synthesizer"
    pillar = "execution"
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
        constraints = state.get("constraints", {})
        ctx = cluster_context or {}

        # Collect all prior sub-agent outputs
        playbook_output = ctx.get("playbook_builder", {})
        kpi_output = ctx.get("kpi_definer", {})
        resource_output = ctx.get("resource_planner", {})

        # Extract key data from patches
        playbook_data = self._extract_from_patches(
            playbook_output, "/pillars/execution/playbook"
        )
        kill_criteria = self._extract_from_patches(
            playbook_output, "/pillars/execution/kill_criteria"
        )
        next_actions = self._extract_from_patches(
            playbook_output, "/execution/next_actions"
        )
        kpi_thresholds = self._extract_from_patches(
            kpi_output, "/pillars/execution/kpi_thresholds"
        )
        north_star = self._extract_from_patches(
            kpi_output, "/pillars/execution/north_star_metric"
        )
        team_plan = self._extract_from_patches(
            resource_output, "/pillars/execution/team_plan"
        )
        budget_allocation = self._extract_from_patches(
            resource_output, "/pillars/execution/budget_allocation"
        )
        financial_plan = self._extract_from_patches(
            resource_output, "/pillars/execution/financial_plan"
        )
        funding_needs = self._extract_from_patches(
            resource_output, "/pillars/execution/funding_needs"
        )

        # Collect all risks and assumptions from prior sub-agents
        all_risks = (
            playbook_output.get("risks", [])
            + kpi_output.get("risks", [])
            + resource_output.get("risks", [])
        )
        all_assumptions = (
            playbook_output.get("assumptions", [])
            + kpi_output.get("assumptions", [])
            + resource_output.get("assumptions", [])
        )

        prompt = f"""You are an execution strategy synthesizer. Combine outputs from the \
playbook builder, KPI definer, and resource planner into a unified execution \
strategy.

Product context:
Name: {idea.get("name", "")}
Category: {idea.get("category", "")}

Constraints:
- Team size: {constraints.get("team_size", "")}
- Timeline: {constraints.get("timeline_weeks", "")} weeks
- Budget: ${constraints.get("budget_usd_monthly", "")} monthly

Playbook:
{json.dumps(playbook_data) if playbook_data else "Not available"}

Kill criteria:
{json.dumps(kill_criteria) if kill_criteria else "Not available"}

Next actions:
{json.dumps(next_actions) if next_actions else "Not available"}

KPI thresholds:
{json.dumps(kpi_thresholds) if kpi_thresholds else "Not available"}

North star metric:
{json.dumps(north_star) if north_star else "Not available"}

Team plan:
{json.dumps(team_plan) if team_plan else "Not available"}

Budget allocation:
{json.dumps(budget_allocation) if budget_allocation else "Not available"}

Financial plan:
{json.dumps(financial_plan) if financial_plan else "Not available"}

Funding needs:
{json.dumps(funding_needs) if funding_needs else "Not available"}

Prior risks: {json.dumps(all_risks)}
Prior assumptions: {json.dumps(all_assumptions)}

Synthesize these into a unified execution view. Identify any contradictions \
(e.g., budget plan exceeds constraints, team plan doesn't match execution \
phases, KPIs don't align with kill criteria).

Return a JSON object with these keys:
{{
  "synthesis_summary": "string (2-4 sentence unified execution strategy)",
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
  "execution_readiness": {{
    "score": 0.0,
    "blockers": ["string"],
    "ready_areas": ["string"],
    "needs_attention": ["string"]
  }},
  "graph_nodes": [
    {{
      "id": "string (e.g. execution.playbook.summary)",
      "label": "string",
      "content": "string",
      "pillar": "execution",
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
        execution_readiness = raw.get("execution_readiness", {})
        graph_nodes = raw.get("graph_nodes", [])
        pillar_nodes = raw.get("pillar_nodes", [])

        # --- Synthesis summary ---
        if synthesis_summary:
            patches.append({
                "op": "replace",
                "path": "/pillars/execution/summary",
                "value": synthesis_summary,
                "meta": self.meta("inference", 0.75),
            })

        # --- Key findings ---
        if key_findings:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/key_findings",
                "value": key_findings,
                "meta": self.meta("inference", 0.7),
            })

            strengths = [
                f for f in key_findings if f.get("category") == "strength"
            ]
            risk_findings = [
                f for f in key_findings if f.get("category") == "risk"
            ]
            gaps = [
                f for f in key_findings if f.get("category") == "gap"
            ]

            facts.append({
                "claim": (
                    f"Execution synthesis: {len(strengths)} strengths, "
                    f"{len(risk_findings)} risks, {len(gaps)} gaps"
                ),
                "confidence": 0.7,
                "sources": [],
            })

            # Elevate critical/high findings to risks
            for finding in key_findings:
                if (
                    finding.get("category") == "risk"
                    and finding.get("severity") in ("critical", "high")
                ):
                    risks.append({
                        "id": f"risk_exec_finding_{len(risks)}",
                        "severity": finding["severity"],
                        "description": finding["finding"],
                        "mitigation": "Review in execution strategy",
                    })

        # --- Contradictions ---
        if contradictions:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/contradictions",
                "value": contradictions,
                "meta": self.meta("inference", 0.8),
            })

            for contradiction in contradictions:
                risks.append({
                    "id": f"risk_exec_contradiction_{len(risks)}",
                    "severity": "high",
                    "description": (
                        f"Contradiction between "
                        f"{', '.join(contradiction.get('between', []))}: "
                        + contradiction.get("description", "")
                    ),
                    "mitigation": contradiction.get("resolution", ""),
                })

            reasoning_steps.append({
                "action": "contradiction_detection",
                "thought": (
                    f"Found {len(contradictions)} contradictions within "
                    "Execution cluster"
                ),
                "confidence": 0.8,
            })

        # --- Execution readiness ---
        if execution_readiness:
            patches.append({
                "op": "add",
                "path": "/pillars/execution/readiness",
                "value": execution_readiness,
                "meta": self.meta("inference", 0.7),
            })

            score = execution_readiness.get("score", 0.0)
            blockers = execution_readiness.get("blockers", [])

            facts.append({
                "claim": (
                    f"Execution readiness score: {score:.0%}"
                    + (f" with {len(blockers)} blockers" if blockers else "")
                ),
                "confidence": 0.7,
                "sources": [],
            })

            if score < 0.5:
                risks.append({
                    "id": "risk_low_readiness",
                    "severity": "high",
                    "description": (
                        f"Execution readiness score is low ({score:.0%})"
                    ),
                    "mitigation": (
                        "Address blockers: " + "; ".join(blockers[:3])
                        if blockers else "Review execution plan"
                    ),
                })

            reasoning_steps.append({
                "action": "readiness_assessment",
                "thought": (
                    f"Execution readiness: {score:.0%}, "
                    f"{len(blockers)} blockers, "
                    f"{len(execution_readiness.get('ready_areas', []))} ready areas"
                ),
                "confidence": 0.7,
            })

        # --- Graph nodes ---
        for node in graph_nodes:
            node_updates.append({
                "id": node.get("id", ""),
                "label": node.get("label", ""),
                "content": node.get("content", ""),
                "pillar": "execution",
                "level": node.get("level", 2),
            })

        # --- Pillar nodes ---
        if pillar_nodes:
            patches.append({
                "op": "replace",
                "path": "/pillars/execution/nodes",
                "value": pillar_nodes,
                "meta": self.meta("inference", 0.7),
            })

        reasoning_steps.append({
            "action": "synthesis",
            "thought": (
                f"Synthesized Execution cluster: "
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
                f"Execution synthesis complete: "
                f"readiness {execution_readiness.get('score', 0.0):.0%}, "
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
