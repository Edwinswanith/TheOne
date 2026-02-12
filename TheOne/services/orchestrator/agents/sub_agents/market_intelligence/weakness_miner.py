"""WeaknessMiner — third sub-agent in the Market Intelligence cluster.

Performs a meta-analysis of market gaps by combining MarketScanner and
CompetitorDeepDive outputs. Classifies each gap into one of five types
and flags red-flag categories that reduce overall confidence.
"""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent

# Gap types that indicate higher risk / lower opportunity quality
RED_FLAG_GAP_TYPES = {"attempted_and_failed", "well_funded_incumbent"}


class WeaknessMiner(BaseSubAgent):
    """Identifies and classifies market gaps from prior cluster outputs."""

    name = "weakness_miner"
    pillar = "market_intelligence"
    step_number = 3
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

        # Gather market_scanner output
        scanner_output = ctx.get("market_scanner", {})
        scanner_patches = scanner_output.get("patches", [])
        scanner_facts = scanner_output.get("facts", [])

        # Gather competitor_deep_dive output
        dive_output = ctx.get("competitor_deep_dive", {})
        dive_patches = dive_output.get("patches", [])
        dive_facts = dive_output.get("facts", [])

        # Extract competitor weaknesses and differentiation gaps
        competitor_weaknesses: list[dict[str, Any]] = []
        for patch in dive_patches:
            if patch.get("path") == "/evidence/teardowns":
                teardown_data = patch.get("value", {})
                for comp in teardown_data.get("competitors", []):
                    competitor_weaknesses.append({
                        "name": comp.get("name", ""),
                        "weaknesses": comp.get("weaknesses", []),
                        "differentiation_gaps": comp.get("differentiation_gaps", []),
                        "key_complaints": comp.get("key_complaints", []),
                    })

        # Extract entry barriers
        entry_barriers: list[dict[str, Any]] = []
        for patch in scanner_patches:
            if patch.get("path", "").endswith("/entry_barriers"):
                entry_barriers = patch.get("value", [])

        prompt = f"""You are a market gap analyst specializing in identifying exploitable weaknesses.

Product context:
Name: {idea.get("name", "")}
One-liner: {idea.get("one_liner", "")}
Problem: {idea.get("problem", "")}

Market scan facts:
{json.dumps(scanner_facts, indent=2)}

Competitor weaknesses and differentiation gaps:
{json.dumps(competitor_weaknesses, indent=2)}

Entry barriers:
{json.dumps(entry_barriers, indent=2)}

Your task: Identify ALL market gaps where this product could win. For each gap,
classify it into exactly ONE of these types:
- "true_gap" — No one is adequately serving this need
- "hard_to_build" — Gap exists because the solution is technically very difficult
- "hard_to_monetize" — Gap exists because no one has found a viable business model
- "attempted_and_failed" — Others have tried and failed (RED FLAG)
- "well_funded_incumbent" — A well-funded player already dominates this gap (RED FLAG)

Return JSON:
{{
  "gaps": [
    {{
      "id": "gap_1",
      "description": "string (what the gap is)",
      "gap_type": "true_gap | hard_to_build | hard_to_monetize | attempted_and_failed | well_funded_incumbent",
      "affected_competitors": ["string (competitor names that have this weakness)"],
      "opportunity_size": "high | medium | low",
      "evidence": "string (why we believe this gap exists)",
      "confidence": 0.8,
      "red_flag_detail": "string or null (only if attempted_and_failed or well_funded_incumbent — explain why)"
    }}
  ],
  "summary": "string (1-2 sentence overall gap landscape assessment)",
  "red_flag_count": 0,
  "strongest_gap_id": "gap_1"
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
        reasoning_steps: list[dict[str, Any]] = []

        gaps = raw.get("gaps", [])
        summary = raw.get("summary", "")
        red_flag_count = raw.get("red_flag_count", 0)
        strongest_gap_id = raw.get("strongest_gap_id", "")

        # Classify gaps
        true_gaps = [g for g in gaps if g.get("gap_type") == "true_gap"]
        hard_build = [g for g in gaps if g.get("gap_type") == "hard_to_build"]
        hard_monetize = [g for g in gaps if g.get("gap_type") == "hard_to_monetize"]
        red_flags = [g for g in gaps if g.get("gap_type") in RED_FLAG_GAP_TYPES]

        # Recount red flags from actual data
        actual_red_flag_count = len(red_flags)

        if gaps:
            # Patch weakness map
            patches.append({
                "op": "add",
                "path": "/evidence/weakness_map",
                "value": {
                    "gaps": gaps,
                    "summary": summary,
                    "red_flag_count": actual_red_flag_count,
                    "strongest_gap_id": strongest_gap_id,
                    "gap_type_distribution": {
                        "true_gap": len(true_gaps),
                        "hard_to_build": len(hard_build),
                        "hard_to_monetize": len(hard_monetize),
                        "attempted_and_failed": len(
                            [g for g in gaps if g.get("gap_type") == "attempted_and_failed"]
                        ),
                        "well_funded_incumbent": len(
                            [g for g in gaps if g.get("gap_type") == "well_funded_incumbent"]
                        ),
                    },
                },
                "meta": self.meta(
                    "inference",
                    0.65 if actual_red_flag_count > 0 else 0.75,
                ),
            })

            facts.append({
                "claim": (
                    f"Identified {len(gaps)} market gaps: "
                    f"{len(true_gaps)} true gaps, {actual_red_flag_count} red flags"
                ),
                "confidence": 0.75,
                "sources": [],
            })

            # Log reasoning for each gap type
            if true_gaps:
                reasoning_steps.append({
                    "action": "gap_classification",
                    "thought": (
                        f"Found {len(true_gaps)} true gaps where no one adequately serves "
                        f"the need — strongest opportunity signals"
                    ),
                    "confidence": 0.8,
                })

            if hard_build:
                reasoning_steps.append({
                    "action": "gap_classification",
                    "thought": (
                        f"{len(hard_build)} gaps exist due to technical difficulty — "
                        "could be moat if solvable"
                    ),
                    "confidence": 0.65,
                })

            # Red flag reasoning and risks
            for rf in red_flags:
                detail = rf.get("red_flag_detail", "No detail provided")
                reasoning_steps.append({
                    "action": "red_flag_detection",
                    "thought": (
                        f"RED FLAG — {rf.get('gap_type', '')}: {rf.get('description', '')}. "
                        f"Detail: {detail}"
                    ),
                    "confidence": 0.7,
                })
                risks.append({
                    "id": f"risk_gap_{rf.get('id', 'unknown')}",
                    "severity": "high",
                    "description": (
                        f"Gap '{rf.get('description', '')}' classified as "
                        f"{rf.get('gap_type', '')} — {detail}"
                    ),
                    "mitigation": (
                        "Validate with customer interviews before committing resources"
                    ),
                })

            # If no true gaps but only risky ones, flag as assumption
            if not true_gaps and gaps:
                assumptions.append({
                    "claim": (
                        "No clear true gaps found; all identified opportunities carry "
                        "structural risk"
                    ),
                    "confidence": 0.5,
                    "sources": [],
                })

        # Confidence degrades if red flags present
        overall_confidence = 0.65 if actual_red_flag_count > 0 else 0.75

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
                f"Weakness mining: {len(gaps)} gaps identified, "
                f"{actual_red_flag_count} red flags"
                + (f" — strongest: {strongest_gap_id}" if strongest_gap_id else "")
            ),
        }
