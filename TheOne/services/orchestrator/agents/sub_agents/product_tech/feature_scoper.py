"""FeatureScoper — first sub-agent in the Product & Tech cluster.

Replaces product_strategy_agent. Scopes MVP features and roadmap based on
ICP decision, competitive gaps, and positioning context.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class FeatureScoper(BaseSubAgent):
    """Scopes MVP feature set and multi-phase product roadmap."""

    name = "feature_scoper"
    pillar = "product_tech"
    step_number = 1
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
        constraints = state.get("constraints", {})
        decisions = state.get("decisions", {})
        pillars = state.get("pillars", {})

        # Pull relevant decision context
        icp_decision = decisions.get("icp", {})
        positioning_decision = decisions.get("positioning", {})

        # Pull competitive gaps from market intelligence if available
        mi_pillar = pillars.get("market_intelligence", {})
        competitive_gaps = mi_pillar.get("competitive_gaps", [])
        entry_barriers = mi_pillar.get("entry_barriers", [])

        prompt = f"""You are a product strategist specializing in MVP scoping and roadmap \
planning for early-stage products.

Product context:
Name: {idea.get("name", "")}
One-liner: {idea.get("one_liner", "")}
Problem: {idea.get("problem", "")}
Category: {idea.get("category", "")}
Target region: {idea.get("target_region", "US")}

ICP decision: {json.dumps(icp_decision) if icp_decision else "Not yet decided"}
Positioning: {json.dumps(positioning_decision) if positioning_decision else "Not yet decided"}

Competitive gaps identified: {json.dumps(competitive_gaps) if competitive_gaps else "None available"}
Entry barriers: {json.dumps(entry_barriers) if entry_barriers else "None available"}

Constraints:
- Team size: {constraints.get("team_size", "")}
- Timeline: {constraints.get("timeline_weeks", "")} weeks
- Budget: ${constraints.get("budget_usd_monthly", "")} monthly

{"Changed decision: " + changed_decision if changed_decision else "Initial analysis"}

Based on the ICP, positioning, and competitive landscape, define the MVP feature \
set and product roadmap. Prioritize features that address competitive gaps and \
align with the selected positioning.

Return a JSON object with these keys:
{{
  "mvp_features": [
    {{
      "id": "string (e.g. feat_01)",
      "title": "string",
      "description": "string",
      "priority": "must_have | should_have | nice_to_have",
      "effort_weeks": 0,
      "rationale": "string (why this feature matters for the ICP)",
      "addresses_gap": "string | null (which competitive gap this fills)"
    }}
  ],
  "roadmap_phases": [
    {{
      "phase": "string (e.g. Phase 1: MVP)",
      "timeline": "string (e.g. Weeks 1-4)",
      "goals": ["string"],
      "features": ["string (feature IDs from mvp_features)"],
      "success_criteria": "string"
    }}
  ],
  "build_priorities": {{
    "critical_path": ["string (ordered feature IDs that form the critical path)"],
    "parallelizable": ["string (feature IDs that can be built in parallel)"],
    "deferrable": ["string (feature IDs safe to defer post-MVP)"]
  }},
  "product_summary": "string (2-3 sentence product strategy summary)"
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

        mvp_features = raw.get("mvp_features", [])
        roadmap_phases = raw.get("roadmap_phases", [])
        build_priorities = raw.get("build_priorities", {})
        product_summary = raw.get("product_summary", "")

        # --- MVP features ---
        if mvp_features:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/mvp_features",
                "value": mvp_features,
                "meta": self.meta("inference", 0.7),
            })

            must_have = [f for f in mvp_features if f.get("priority") == "must_have"]
            should_have = [f for f in mvp_features if f.get("priority") == "should_have"]
            total_effort = sum(f.get("effort_weeks", 0) for f in must_have)

            facts.append({
                "claim": (
                    f"Scoped MVP with {len(must_have)} must-have and "
                    f"{len(should_have)} should-have features"
                ),
                "confidence": 0.7,
                "sources": [],
            })

            # Check if total effort exceeds timeline
            timeline_weeks = state.get("constraints", {}).get("timeline_weeks", 0)
            if timeline_weeks and total_effort > timeline_weeks:
                risks.append({
                    "id": "risk_mvp_timeline_overrun",
                    "severity": "high",
                    "description": (
                        f"Must-have features require {total_effort} weeks but "
                        f"timeline is {timeline_weeks} weeks"
                    ),
                    "mitigation": "Reduce scope or extend timeline",
                })

            reasoning_steps.append({
                "action": "feature_scoping",
                "thought": (
                    f"Defined {len(mvp_features)} features: "
                    f"{len(must_have)} must-have ({total_effort}w effort), "
                    f"{len(should_have)} should-have"
                ),
                "confidence": 0.7,
            })

        # --- Roadmap phases ---
        if roadmap_phases:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/roadmap_phases",
                "value": roadmap_phases,
                "meta": self.meta("inference", 0.7),
            })

            reasoning_steps.append({
                "action": "roadmap_planning",
                "thought": f"Created {len(roadmap_phases)}-phase product roadmap",
                "confidence": 0.7,
            })

        # --- Build priorities ---
        if build_priorities:
            patches.append({
                "op": "add",
                "path": "/pillars/product_tech/build_priorities",
                "value": build_priorities,
                "meta": self.meta("inference", 0.65),
            })

            critical_path = build_priorities.get("critical_path", [])
            if critical_path:
                assumptions.append({
                    "claim": (
                        f"Critical path contains {len(critical_path)} features "
                        "that must be built sequentially"
                    ),
                    "confidence": 0.65,
                    "sources": [],
                })

        # --- Product summary ---
        if product_summary:
            patches.append({
                "op": "replace",
                "path": "/pillars/product_tech/summary",
                "value": product_summary,
                "meta": self.meta("inference", 0.7),
            })

        return {
            "patches": patches,
            "proposals": [],
            "facts": facts,
            "assumptions": assumptions,
            "risks": risks,
            "required_inputs": [],
            "node_updates": [],
            "reasoning_steps": reasoning_steps,
            "_confidence": 0.7,
            "_summary": (
                f"Feature scoping complete: {len(mvp_features)} features across "
                f"{len(roadmap_phases)} roadmap phases"
            ),
        }
