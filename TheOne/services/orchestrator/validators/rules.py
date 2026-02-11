from __future__ import annotations

from typing import Any


def run_validator(
    state: dict[str, Any],
    export_final: bool = False,
    finalize: bool = False,
    mark_complete: bool = False,
) -> dict[str, Any]:
    contradictions: list[dict[str, Any]] = []
    missing_proof: list[dict[str, Any]] = []
    high_risk_flags: list[dict[str, Any]] = [
        item
        for item in state["risks"].get("high_risk_flags", [])
        if str(item.get("rule_id", "")).startswith("OVERRIDE-")
    ]
    blocking = False

    decisions = state["decisions"]
    pricing = decisions["pricing"]
    channels = decisions["channels"]
    icp = decisions["icp"]
    positioning = decisions["positioning"]
    sales_motion = decisions["sales_motion"]

    def add_contradiction(item: dict[str, Any]) -> None:
        nonlocal blocking
        contradictions.append(item)
        if item["severity"] in {"critical", "high"}:
            blocking = True

    if finalize and not icp.get("selected_option_id", ""):
        add_contradiction(
            _contradiction(
                "V-ICP-01",
                "critical",
                "ICP selection is required before finalization.",
                ["/decisions/icp/selected_option_id"],
            )
        )

    value_prop = positioning.get("frame", {}).get("value_prop", "")
    if finalize and not value_prop:
        add_contradiction(
            _contradiction(
                "V-PROD-01",
                "critical",
                "Value proposition is missing.",
                ["/decisions/positioning/frame/value_prop"],
            )
        )

    pricing_metric = pricing.get("metric", "")
    pricing_tiers = pricing.get("tiers", [])
    if not pricing_metric and (pricing_tiers or finalize or mark_complete):
        add_contradiction(
            _contradiction(
                "V-PRICE-01",
                "critical",
                "Pricing metric is required before completion/export.",
                ["/decisions/pricing/metric", "/decisions/pricing/tiers"],
            )
        )

    primary_channels = channels.get("primary_channels", [])
    category = state["idea"].get("category", "")
    if category in {"b2b_saas", "b2b_services"} and len(primary_channels) > 2:
        high_risk_flags.append(
            {
                "rule_id": "V-CHAN-01",
                "severity": "high",
                "message": "Focus failure: keep at most one primary plus one secondary channel.",
                "paths": ["/decisions/channels/primary_channels"],
                "recommended_fix": "Reduce to one primary and one backup channel.",
            }
        )

    icp_profile = icp.get("profile", {})
    motion = sales_motion.get("motion", "unset")
    if motion == "plg" and (
        icp_profile.get("company_size") in {"enterprise", "500+"}
        or icp_profile.get("budget_owner") == "procurement"
    ):
        add_contradiction(
            _contradiction(
                "V-SALES-01",
                "high",
                "PLG-only motion conflicts with enterprise/procurement ICP.",
                [
                    "/decisions/sales_motion/motion",
                    "/decisions/icp/profile/company_size",
                    "/decisions/icp/profile/budget_owner",
                ],
                "Switch motion or add enterprise sales support plan.",
            )
        )

    price_to_test = float(pricing.get("price_to_test", 0) or 0)
    company_size = str(icp_profile.get("company_size", ""))
    if motion == "outbound_led" and company_size in {"1-10", "1-20"} and price_to_test <= 99:
        contradictions.append(
            _contradiction(
                "V-SALES-02",
                "medium",
                "Outbound motion with low price on very small ICP may have poor unit economics.",
                ["/decisions/sales_motion/motion", "/decisions/pricing/price_to_test"],
            )
        )

    has_wtp_proof = bool(state["evidence"].get("pricing_anchors"))
    if price_to_test >= 500 and not has_wtp_proof:
        missing_proof.append(
            {
                "rule_id": "V-PRICE-02",
                "severity": "high",
                "message": "Price-to-test is high without willingness-to-pay proof.",
                "paths": ["/decisions/pricing/price_to_test", "/evidence/pricing_anchors"],
                "recommended_fix": "Run WTP interviews or collect paid pilot signals.",
            }
        )

    if state["constraints"].get("compliance_level") == "high":
        has_security_node = any(node.get("id") == "product.security_plan" for node in state["graph"].get("nodes", []))
        has_security_summary = bool(state["pillars"]["execution"].get("security_plan", ""))
        if finalize and not (has_security_node or has_security_summary):
            add_contradiction(
                _contradiction(
                    "V-TECH-01",
                    "critical",
                    "High compliance requires a security/data handling plan.",
                    ["/constraints/compliance_level", "/pillars/execution/security_plan"],
                )
            )

    category_is_novel = state["idea"].get("category") == "b2c"
    if not category_is_novel and not state["evidence"].get("competitors"):
        missing_proof.append(
            {
                "rule_id": "V-EVID-01",
                "severity": "high",
                "message": "Competitor evidence is missing for non-novel category.",
                "paths": ["/evidence/competitors"],
                "recommended_fix": "Rerun evidence collection or confirm greenfield market.",
            }
        )

    if pricing_metric and not state["evidence"].get("pricing_anchors"):
        missing_proof.append(
            {
                "rule_id": "V-EVID-02",
                "severity": "high",
                "message": "Pricing is decided without pricing anchors evidence.",
                "paths": ["/evidence/pricing_anchors", "/decisions/pricing/metric"],
                "recommended_fix": "Collect competitor pricing anchors or run WTP experiment.",
            }
        )

    if export_final and state["execution"].get("chosen_track") == "unset":
        add_contradiction(
            _contradiction(
                "V-EXEC-01",
                "high",
                "Execution track must be selected before final export.",
                ["/execution/chosen_track"],
                "Select a track or use draft export.",
            )
        )

    execution_empty = not state["execution"].get("next_actions")
    if mark_complete and execution_empty:
        add_contradiction(
            _contradiction(
                "V-OPS-01",
                "high",
                "Execution pillar is empty; scenario cannot be marked complete.",
                ["/execution/next_actions", "/pillars/execution"],
            )
        )

    people_empty = not state["pillars"]["people_and_cash"].get("summary")
    if pricing_metric and people_empty:
        contradictions.append(
            _contradiction(
                "V-PEOPLE-01",
                "medium",
                "People and cash pillar is under-defined relative to pricing decision.",
                ["/pillars/people_and_cash", "/decisions/pricing"],
            )
        )

    for key in ["icp", "positioning", "pricing", "channels", "sales_motion"]:
        override = decisions[key].get("override", {})
        if override.get("is_custom") and not override.get("justification", "").strip():
            add_contradiction(
                _contradiction(
                    "V-CONT-01",
                    "high",
                    f"Custom override on {key} requires justification.",
                    [f"/decisions/{key}/override/justification"],
                )
            )

    state["risks"]["contradictions"] = contradictions
    state["risks"]["missing_proof"] = missing_proof
    state["risks"]["high_risk_flags"] = high_risk_flags

    return {
        "blocking": blocking,
        "contradictions": contradictions,
        "missing_proof": missing_proof,
        "high_risk_flags": high_risk_flags,
    }


def _contradiction(
    rule_id: str,
    severity: str,
    message: str,
    paths: list[str],
    recommended_fix: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
        "paths": paths,
    }
    if recommended_fix:
        item["recommended_fix"] = recommended_fix
    return item
