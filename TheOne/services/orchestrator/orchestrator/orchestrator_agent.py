"""Orchestrator agent — cross-pillar validation and feedback generation."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from services.orchestrator.orchestrator.rules_registry import (
    OrchestratorRule,
    RuleResult,
    load_rules,
)
from services.orchestrator.tools.providers import ProviderClient


@dataclass
class FeedbackDirective:
    """Instruction sent to a cluster for the feedback round."""

    directive_id: str
    rule_id: str
    target_cluster: str
    affected_sub_agents: list[str]
    message: str
    correction_hint: str
    severity: str


@dataclass
class OrchestratorReport:
    """Full report from the orchestrator cross-reference phase."""

    rules_evaluated: int
    failures: list[RuleResult]
    directives: list[FeedbackDirective]
    insights: list[dict[str, Any]] = field(default_factory=list)


def run_orchestrator_check(
    state: dict[str, Any],
    provider: ProviderClient | None = None,
) -> OrchestratorReport:
    """Run all applicable rules and generate feedback directives.

    Three phases:
    1. Deterministic cross-reference — run all loaded rules, collect failures
    2. Feedback directive generation — Gemini call to produce correction hints
    3. Insight distribution — cross-pillar insights (no reruns needed)
    """
    category = state.get("idea", {}).get("category", "b2b_saas")
    rules = load_rules(category, state)

    # Phase 1: Evaluate all rules
    results: list[RuleResult] = []
    failures: list[RuleResult] = []
    for rule in rules:
        result = rule.check(state)
        result.rule_id = rule.rule_id
        results.append(result)
        if not result.passed:
            failures.append(result)

    # Phase 2: Generate feedback directives
    directives: list[FeedbackDirective] = []
    if failures:
        directives = _generate_directives(failures, state, provider)

    # Phase 3: Collect insights (non-actionable observations)
    insights = _extract_insights(results, state)

    return OrchestratorReport(
        rules_evaluated=len(rules),
        failures=failures,
        directives=directives,
        insights=insights,
    )


def _generate_directives(
    failures: list[RuleResult],
    state: dict[str, Any],
    provider: ProviderClient | None = None,
) -> list[FeedbackDirective]:
    """Generate correction directives from rule failures.

    For deterministic/obvious fixes, generates directives directly.
    For ambiguous cases, uses a single Gemini call for arbitration.
    """
    directives: list[FeedbackDirective] = []
    ambiguous: list[RuleResult] = []

    for failure in failures:
        # Simple cases: generate directive directly from rule result
        if failure.affected_sub_agents:
            directives.append(FeedbackDirective(
                directive_id=f"dir_{failure.rule_id}",
                rule_id=failure.rule_id,
                target_cluster=failure.target_pillar,
                affected_sub_agents=failure.affected_sub_agents,
                message=failure.message,
                correction_hint=f"Address {failure.rule_id}: {failure.message}",
                severity=failure.severity,
            ))
        else:
            ambiguous.append(failure)

    # For ambiguous cases, use Gemini to generate correction hints
    if ambiguous and provider:
        try:
            llm_directives = _arbitrate_with_llm(ambiguous, state, provider)
            directives.extend(llm_directives)
        except Exception:
            # Fallback: create generic directives
            for failure in ambiguous:
                directives.append(FeedbackDirective(
                    directive_id=f"dir_{failure.rule_id}",
                    rule_id=failure.rule_id,
                    target_cluster=failure.target_pillar,
                    affected_sub_agents=[],
                    message=failure.message,
                    correction_hint=failure.message,
                    severity=failure.severity,
                ))

    return directives


def _arbitrate_with_llm(
    failures: list[RuleResult],
    state: dict[str, Any],
    provider: ProviderClient,
) -> list[FeedbackDirective]:
    """Use Gemini to generate correction hints for ambiguous conflicts."""
    conflicts_desc = []
    for f in failures:
        conflicts_desc.append({
            "rule_id": f.rule_id,
            "severity": f.severity,
            "message": f.message,
            "source_pillar": f.source_pillar,
            "target_pillar": f.target_pillar,
        })

    prompt = f"""You are a GTM strategy orchestrator. The following cross-pillar conflicts were detected:

{json.dumps(conflicts_desc, indent=2)}

Product context:
Name: {state.get('idea', {}).get('name', '')}
Category: {state.get('idea', {}).get('category', '')}
Team size: {state.get('constraints', {}).get('team_size', '')}

For each conflict, provide a specific correction hint. Return JSON:
{{
  "directives": [
    {{
      "rule_id": "string",
      "target_cluster": "string (pillar name)",
      "affected_sub_agents": ["string"],
      "correction_hint": "string (specific actionable instruction)"
    }}
  ]
}}
"""
    raw = provider._gemini_json(prompt)
    result_directives = []
    for d in raw.get("directives", []):
        result_directives.append(FeedbackDirective(
            directive_id=f"dir_{d.get('rule_id', 'unknown')}",
            rule_id=d.get("rule_id", ""),
            target_cluster=d.get("target_cluster", ""),
            affected_sub_agents=d.get("affected_sub_agents", []),
            message=next((f.message for f in failures if f.rule_id == d.get("rule_id")), ""),
            correction_hint=d.get("correction_hint", ""),
            severity="must_address",
        ))
    return result_directives


def _extract_insights(results: list[RuleResult], state: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract non-actionable cross-pillar insights from rule results."""
    insights = []

    # Count passing and failing by pillar
    pillar_health: dict[str, dict[str, int]] = {}
    for r in results:
        target = r.target_pillar
        pillar_health.setdefault(target, {"pass": 0, "fail": 0})
        if r.passed:
            pillar_health[target]["pass"] += 1
        else:
            pillar_health[target]["fail"] += 1

    for pillar, counts in pillar_health.items():
        total = counts["pass"] + counts["fail"]
        if total > 0:
            health_pct = counts["pass"] / total
            insights.append({
                "pillar": pillar,
                "health_score": round(health_pct, 2),
                "rules_passed": counts["pass"],
                "rules_failed": counts["fail"],
            })

    return insights


def group_directives_by_cluster(
    directives: list[FeedbackDirective],
) -> dict[str, list[FeedbackDirective]]:
    """Group directives by target cluster for dispatch."""
    grouped: dict[str, list[FeedbackDirective]] = {}
    for d in directives:
        grouped.setdefault(d.target_cluster, []).append(d)
    return grouped
