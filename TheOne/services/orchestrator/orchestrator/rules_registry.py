"""Orchestrator rules registry — 22 cross-pillar validation rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class RuleResult:
    """Result of evaluating a single orchestrator rule."""

    passed: bool
    severity: str  # "must_address" | "should_address"
    message: str
    source_pillar: str
    target_pillar: str
    affected_sub_agents: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    rule_id: str = ""


@dataclass
class OrchestratorRule:
    """A single cross-pillar validation rule."""

    rule_id: str  # OR-01 through OR-22
    name: str
    severity: str  # "must_address" | "should_address"
    source_pillar: str
    target_pillar: str
    check: Callable[[dict[str, Any]], RuleResult]


# ---------------------------------------------------------------------------
# Helper extractors
# ---------------------------------------------------------------------------

def _get_icp_data(state: dict[str, Any]) -> dict[str, Any]:
    icp = state.get("decisions", {}).get("icp", {})
    selected = icp.get("selected_option_id", "")
    for opt in icp.get("options", []):
        if opt.get("id") == selected:
            return opt.get("data", opt)
    # Fallback to first option
    options = icp.get("options", [])
    return options[0].get("data", options[0]) if options else {}


def _get_pricing_data(state: dict[str, Any]) -> dict[str, Any]:
    pricing = state.get("decisions", {}).get("pricing", {})
    selected = pricing.get("selected_option_id", "")
    for opt in pricing.get("options", []):
        if opt.get("id") == selected:
            return opt.get("data", opt)
    options = pricing.get("options", [])
    return options[0].get("data", options[0]) if options else {}


def _get_channel_data(state: dict[str, Any]) -> dict[str, Any]:
    channels = state.get("decisions", {}).get("channels", {})
    selected = channels.get("selected_option_id", "")
    for opt in channels.get("options", []):
        if opt.get("id") == selected:
            return opt.get("data", opt)
    options = channels.get("options", [])
    return options[0].get("data", options[0]) if options else {}


def _get_motion_data(state: dict[str, Any]) -> dict[str, Any]:
    motion = state.get("decisions", {}).get("sales_motion", {})
    selected = motion.get("selected_option_id", "")
    for opt in motion.get("options", []):
        if opt.get("id") == selected:
            return opt.get("data", opt)
    options = motion.get("options", [])
    return options[0].get("data", options[0]) if options else {}


def _get_gap_type(state: dict[str, Any]) -> str | None:
    artifacts = state.get("artifacts", {})
    mi = artifacts.get("market_intelligence", {})
    for agent_data in mi.values():
        if isinstance(agent_data, dict):
            # Check in reasoning chain or output
            for step in agent_data.get("reasoning_chain", []):
                data = step.get("data", {})
                if data and isinstance(data, dict) and "gap_type" in data:
                    return data["gap_type"]
    # Also check weakness_map in evidence
    for entry in state.get("evidence", {}).get("weakness_map", []):
        if isinstance(entry, dict) and entry.get("gap_type"):
            return entry["gap_type"]
    return None


RED_FLAG_GAPS = {"attempted_and_failed", "well_funded_incumbent"}


# ---------------------------------------------------------------------------
# Base rules (OR-01 to OR-10) — apply to ALL categories
# ---------------------------------------------------------------------------

def _check_icp_channel_alignment(state: dict[str, Any]) -> RuleResult:
    """OR-01: ICP-Channel alignment."""
    icp = _get_icp_data(state)
    channel = _get_channel_data(state)
    if not icp or not channel:
        return RuleResult(True, "must_address", "", "customer", "go_to_market", rule_id="OR-01")

    icp_company_size = str(icp.get("company_size", "")).lower()
    channels = channel.get("primary_channels", [])
    channel_names = [c.lower() if isinstance(c, str) else "" for c in channels]

    # Enterprise ICP shouldn't rely primarily on self-serve channels
    if any(kw in icp_company_size for kw in ["enterprise", "1000+", "500+"]):
        if any(c in channel_names for c in ["product-led", "self-serve", "viral"]):
            return RuleResult(
                False, "must_address",
                "Enterprise ICP paired with self-serve/PLG channels — enterprise buyers expect high-touch sales.",
                "customer", "go_to_market",
                affected_sub_agents=["channel_researcher", "motion_designer"],
                rule_id="OR-01",
            )
    return RuleResult(True, "must_address", "", "customer", "go_to_market", rule_id="OR-01")


def _check_icp_motion_compatibility(state: dict[str, Any]) -> RuleResult:
    """OR-02: ICP-Motion compatibility."""
    icp = _get_icp_data(state)
    motion = _get_motion_data(state)
    if not icp or not motion:
        return RuleResult(True, "must_address", "", "customer", "go_to_market", rule_id="OR-02")

    motion_type = motion.get("motion", "")
    budget = str(icp.get("budget_authority", "")).lower()

    # PLG motion with enterprise buyer who needs executive approval
    if motion_type == "plg" and any(kw in budget for kw in ["executive", "board", "c-suite"]):
        return RuleResult(
            False, "must_address",
            "PLG motion incompatible with ICP that requires executive budget approval.",
            "customer", "go_to_market",
            affected_sub_agents=["motion_designer"],
            rule_id="OR-02",
        )
    return RuleResult(True, "must_address", "", "customer", "go_to_market", rule_id="OR-02")


def _check_pricing_icp_budget(state: dict[str, Any]) -> RuleResult:
    """OR-03: Pricing-ICP budget fit."""
    pricing = _get_pricing_data(state)
    icp = _get_icp_data(state)
    if not pricing or not icp:
        return RuleResult(True, "must_address", "", "positioning_pricing", "customer", rule_id="OR-03")

    price_to_test = pricing.get("price_to_test", 0)
    budget_str = str(icp.get("budget_authority", "")).lower()

    # High price with SMB/startup ICP
    if price_to_test and float(price_to_test) > 500:
        if any(kw in budget_str for kw in ["individual", "team lead", "manager"]):
            return RuleResult(
                False, "must_address",
                f"Price point ${price_to_test}/mo requires budget authority beyond {budget_str}.",
                "positioning_pricing", "customer",
                affected_sub_agents=["price_modeler", "icp_researcher"],
                rule_id="OR-03",
            )
    return RuleResult(True, "must_address", "", "positioning_pricing", "customer", rule_id="OR-03")


def _check_channel_cost_vs_budget(state: dict[str, Any]) -> RuleResult:
    """OR-04: Channel cost vs budget."""
    constraints = state.get("constraints", {})
    budget = constraints.get("budget_usd_monthly", 0)
    channel = _get_channel_data(state)
    if not channel:
        return RuleResult(True, "should_address", "", "go_to_market", "execution", rule_id="OR-04")

    channels = channel.get("primary_channels", [])
    expensive_channels = {"outbound sales", "paid advertising", "trade shows", "events"}
    selected_expensive = [c for c in channels if isinstance(c, str) and c.lower() in expensive_channels]

    if selected_expensive and budget < 2000:
        return RuleResult(
            False, "should_address",
            f"High-cost channels ({', '.join(selected_expensive)}) selected with only ${budget}/mo budget.",
            "go_to_market", "execution",
            affected_sub_agents=["channel_researcher", "resource_planner"],
            rule_id="OR-04",
        )
    return RuleResult(True, "should_address", "", "go_to_market", "execution", rule_id="OR-04")


def _check_mvp_timeline(state: dict[str, Any]) -> RuleResult:
    """OR-05: MVP timeline vs constraint."""
    constraints = state.get("constraints", {})
    timeline = constraints.get("timeline_weeks", 52)
    pt = state.get("pillars", {}).get("product_tech", {})
    feasibility = pt.get("feasibility_flags", {})

    if feasibility:
        estimated_months = feasibility.get("estimated_build_months", 0)
        if estimated_months and estimated_months * 4 > timeline:
            return RuleResult(
                False, "must_address",
                f"Estimated build time ({estimated_months} months) exceeds timeline constraint ({timeline} weeks).",
                "product_tech", "execution",
                affected_sub_agents=["feature_scoper", "playbook_builder"],
                rule_id="OR-05",
            )
    return RuleResult(True, "must_address", "", "product_tech", "execution", rule_id="OR-05")


def _check_revenue_vs_pricing(state: dict[str, Any]) -> RuleResult:
    """OR-06: Revenue target vs pricing math."""
    pricing = _get_pricing_data(state)
    motion = _get_motion_data(state)
    if not pricing or not motion:
        return RuleResult(True, "should_address", "", "positioning_pricing", "execution", rule_id="OR-06")

    price = pricing.get("price_to_test", 0)
    deal_size = motion.get("avg_deal_size", 0)
    # Basic sanity: if price_to_test exists, avg_deal_size should be in same ballpark
    if price and deal_size and abs(float(price) - float(deal_size)) > float(price) * 5:
        return RuleResult(
            False, "should_address",
            f"Pricing (${price}) and average deal size (${deal_size}) are significantly misaligned.",
            "positioning_pricing", "execution",
            affected_sub_agents=["price_modeler", "motion_designer"],
            rule_id="OR-06",
        )
    return RuleResult(True, "should_address", "", "positioning_pricing", "execution", rule_id="OR-06")


def _check_team_capacity(state: dict[str, Any]) -> RuleResult:
    """OR-07: Team capacity vs motion requirements."""
    constraints = state.get("constraints", {})
    team_size = constraints.get("team_size", 1)
    motion = _get_motion_data(state)
    if not motion:
        return RuleResult(True, "must_address", "", "execution", "go_to_market", rule_id="OR-07")

    motion_type = motion.get("motion", "")
    if motion_type == "outbound_led" and team_size < 3:
        return RuleResult(
            False, "must_address",
            f"Outbound-led motion requires dedicated sales resources; team of {team_size} is too small.",
            "execution", "go_to_market",
            affected_sub_agents=["motion_designer", "resource_planner"],
            rule_id="OR-07",
        )
    return RuleResult(True, "must_address", "", "execution", "go_to_market", rule_id="OR-07")


def _check_motion_pricing_tier(state: dict[str, Any]) -> RuleResult:
    """OR-08: Sales motion vs pricing tier."""
    motion = _get_motion_data(state)
    pricing = _get_pricing_data(state)
    if not motion or not pricing:
        return RuleResult(True, "should_address", "", "go_to_market", "positioning_pricing", rule_id="OR-08")

    motion_type = motion.get("motion", "")
    tiers = pricing.get("tiers", [])
    has_free_tier = any(
        t.get("price", 1) == 0 or "free" in str(t.get("name", "")).lower()
        for t in tiers if isinstance(t, dict)
    )

    if motion_type == "plg" and not has_free_tier:
        return RuleResult(
            False, "should_address",
            "PLG motion selected but no free tier in pricing — PLG requires a self-serve entry point.",
            "go_to_market", "positioning_pricing",
            affected_sub_agents=["price_modeler", "motion_designer"],
            rule_id="OR-08",
        )
    return RuleResult(True, "should_address", "", "go_to_market", "positioning_pricing", rule_id="OR-08")


def _check_channel_messaging(state: dict[str, Any]) -> RuleResult:
    """OR-09: Channel-messaging alignment."""
    # Light check: ensure messaging templates exist if channels are defined
    gtm = state.get("pillars", {}).get("go_to_market", {})
    channels = state.get("decisions", {}).get("channels", {}).get("primary_channels", [])
    templates = gtm.get("messaging_templates", [])

    if channels and not templates:
        return RuleResult(
            False, "should_address",
            "Channels defined but no messaging templates created.",
            "go_to_market", "go_to_market",
            affected_sub_agents=["message_crafter"],
            rule_id="OR-09",
        )
    return RuleResult(True, "should_address", "", "go_to_market", "go_to_market", rule_id="OR-09")


def _check_evidence_coverage(state: dict[str, Any]) -> RuleResult:
    """OR-10: Evidence coverage minimum."""
    evidence = state.get("evidence", {})
    sources = evidence.get("sources", [])
    competitors = evidence.get("competitors", [])

    if len(sources) + len(competitors) < 3:
        return RuleResult(
            False, "must_address",
            f"Insufficient evidence: only {len(sources)} sources and {len(competitors)} competitors.",
            "market_intelligence", "market_intelligence",
            affected_sub_agents=["market_scanner", "competitor_deep_dive"],
            rule_id="OR-10",
        )
    return RuleResult(True, "must_address", "", "market_intelligence", "market_intelligence", rule_id="OR-10")


# ---------------------------------------------------------------------------
# Category-specific rules
# ---------------------------------------------------------------------------

def _check_b2c_monetization(state: dict[str, Any]) -> RuleResult:
    """OR-11: B2C monetization viability."""
    pricing = _get_pricing_data(state)
    if not pricing:
        return RuleResult(True, "must_address", "", "positioning_pricing", "execution", rule_id="OR-11")

    price = pricing.get("price_to_test", 0)
    if price and float(price) < 5:
        return RuleResult(
            False, "must_address",
            f"B2C price point ${price} may not sustain customer acquisition costs. Consider freemium with upsell.",
            "positioning_pricing", "execution",
            affected_sub_agents=["price_modeler", "motion_designer"],
            rule_id="OR-11",
        )
    return RuleResult(True, "must_address", "", "positioning_pricing", "execution", rule_id="OR-11")


def _check_b2c_retention(state: dict[str, Any]) -> RuleResult:
    """OR-12: B2C retention risk."""
    motion = _get_motion_data(state)
    if not motion:
        return RuleResult(True, "should_address", "", "go_to_market", "execution", rule_id="OR-12")

    # B2C without retention strategy is risky
    exec_pillars = state.get("pillars", {}).get("execution", {})
    kpis = exec_pillars.get("kpi_thresholds", [])
    has_retention_kpi = any(
        "retention" in str(k).lower() or "churn" in str(k).lower()
        for k in kpis
    )
    if not has_retention_kpi:
        return RuleResult(
            False, "should_address",
            "B2C plan missing retention/churn KPIs — high churn is the primary B2C risk.",
            "go_to_market", "execution",
            affected_sub_agents=["kpi_definer"],
            rule_id="OR-12",
        )
    return RuleResult(True, "should_address", "", "go_to_market", "execution", rule_id="OR-12")


def _check_devtools_moat(state: dict[str, Any]) -> RuleResult:
    """OR-13: Dev tools competitive moat."""
    competitors = state.get("evidence", {}).get("competitors", [])
    open_source = [c for c in competitors if isinstance(c, dict) and "open" in str(c.get("pricing_model", "")).lower()]

    if len(open_source) >= 2:
        return RuleResult(
            False, "must_address",
            f"Found {len(open_source)} open-source competitors — dev tools need strong differentiation moat.",
            "market_intelligence", "positioning_pricing",
            affected_sub_agents=["wedge_builder", "category_framer"],
            rule_id="OR-13",
        )
    return RuleResult(True, "must_address", "", "market_intelligence", "positioning_pricing", rule_id="OR-13")


def _check_devtools_free_tier(state: dict[str, Any]) -> RuleResult:
    """OR-14: Dev tools free tier pressure."""
    pricing = _get_pricing_data(state)
    if not pricing:
        return RuleResult(True, "should_address", "", "positioning_pricing", "go_to_market", rule_id="OR-14")

    tiers = pricing.get("tiers", [])
    has_free = any(t.get("price", 1) == 0 for t in tiers if isinstance(t, dict))
    if not has_free:
        return RuleResult(
            False, "should_address",
            "Dev tools market expects free tier or open-source core. Missing free option may limit adoption.",
            "positioning_pricing", "go_to_market",
            affected_sub_agents=["price_modeler"],
            rule_id="OR-14",
        )
    return RuleResult(True, "should_address", "", "positioning_pricing", "go_to_market", rule_id="OR-14")


def _check_vertical_data_dependency(state: dict[str, Any]) -> RuleResult:
    """OR-15: Vertical SaaS domain data dependency."""
    pt = state.get("pillars", {}).get("product_tech", {})
    build_vs_buy = pt.get("build_vs_buy", [])
    if not build_vs_buy:
        return RuleResult(
            False, "should_address",
            "Vertical SaaS without build-vs-buy analysis for domain data sources.",
            "product_tech", "product_tech",
            affected_sub_agents=["feasibility_checker"],
            rule_id="OR-15",
        )
    return RuleResult(True, "should_address", "", "product_tech", "product_tech", rule_id="OR-15")


def _check_vertical_channel_fit(state: dict[str, Any]) -> RuleResult:
    """OR-16: Vertical SaaS industry channel fit."""
    channel = _get_channel_data(state)
    if not channel:
        return RuleResult(True, "must_address", "", "go_to_market", "go_to_market", rule_id="OR-16")

    channels = channel.get("primary_channels", [])
    industry_channels = {"trade shows", "industry events", "associations", "referral networks"}
    has_industry = any(
        any(ic in c.lower() for ic in industry_channels)
        for c in channels if isinstance(c, str)
    )
    if not has_industry:
        return RuleResult(
            False, "should_address",
            "Vertical SaaS without industry-specific channels (trade shows, associations).",
            "go_to_market", "go_to_market",
            affected_sub_agents=["channel_researcher"],
            rule_id="OR-16",
        )
    return RuleResult(True, "should_address", "", "go_to_market", "go_to_market", rule_id="OR-16")


def _check_trade_show_calendar(state: dict[str, Any]) -> RuleResult:
    """OR-17: Vertical SaaS trade show calendar."""
    exec_pillar = state.get("pillars", {}).get("execution", {})
    playbook = exec_pillar.get("playbook", [])
    has_events = any(
        "event" in str(item).lower() or "trade show" in str(item).lower() or "conference" in str(item).lower()
        for item in playbook
    )
    if not has_events:
        return RuleResult(
            False, "should_address",
            "Vertical SaaS execution plan missing industry event timeline.",
            "execution", "go_to_market",
            affected_sub_agents=["playbook_builder"],
            rule_id="OR-17",
        )
    return RuleResult(True, "should_address", "", "execution", "go_to_market", rule_id="OR-17")


# ---------------------------------------------------------------------------
# Compliance rules (conditional — Issue 6)
# ---------------------------------------------------------------------------

def _check_compliance_timeline(state: dict[str, Any]) -> RuleResult:
    """OR-18: Compliance-timeline mismatch."""
    constraints = state.get("constraints", {})
    timeline = constraints.get("timeline_weeks", 52)
    pt = state.get("pillars", {}).get("product_tech", {})
    compliance = pt.get("compliance_assessment", {})
    compliance_weeks = compliance.get("compliance_timeline_weeks", 0)

    if compliance_weeks and compliance_weeks > timeline:
        return RuleResult(
            False, "must_address",
            f"Compliance timeline ({compliance_weeks} weeks) exceeds project timeline ({timeline} weeks).",
            "product_tech", "execution",
            affected_sub_agents=["feasibility_checker", "playbook_builder"],
            rule_id="OR-18",
        )
    return RuleResult(True, "must_address", "", "product_tech", "execution", rule_id="OR-18")


def _check_compliance_budget(state: dict[str, Any]) -> RuleResult:
    """OR-19: Compliance-budget mismatch."""
    constraints = state.get("constraints", {})
    budget = constraints.get("budget_usd_monthly", 0)
    pt = state.get("pillars", {}).get("product_tech", {})
    compliance = pt.get("compliance_assessment", {})
    certs = compliance.get("required_certifications", [])

    # SOC2 / HIPAA / ISO typically cost $10k+ to obtain
    expensive_certs = [c for c in certs if any(kw in str(c).upper() for kw in ["SOC", "HIPAA", "ISO", "PCI", "GDPR"])]
    if expensive_certs and budget < 5000:
        return RuleResult(
            False, "must_address",
            f"Required certifications ({', '.join(expensive_certs)}) are expensive; ${budget}/mo budget may be insufficient.",
            "product_tech", "execution",
            affected_sub_agents=["resource_planner", "feasibility_checker"],
            rule_id="OR-19",
        )
    return RuleResult(True, "must_address", "", "product_tech", "execution", rule_id="OR-19")


# ---------------------------------------------------------------------------
# Marketplace rule
# ---------------------------------------------------------------------------

def _check_marketplace_chicken_egg(state: dict[str, Any]) -> RuleResult:
    """OR-20: Marketplace chicken-and-egg."""
    idea = state.get("idea", {})
    category = idea.get("category", "")
    problem = idea.get("problem", "").lower()
    one_liner = idea.get("one_liner", "").lower()

    is_marketplace = any(kw in problem + one_liner for kw in ["marketplace", "platform", "two-sided", "supply and demand"])
    if not is_marketplace:
        return RuleResult(True, "must_address", "", "go_to_market", "execution", rule_id="OR-20")

    exec_pillar = state.get("pillars", {}).get("execution", {})
    playbook = exec_pillar.get("playbook", [])
    has_supply_strategy = any("supply" in str(item).lower() or "seed" in str(item).lower() for item in playbook)

    if not has_supply_strategy:
        return RuleResult(
            False, "must_address",
            "Marketplace detected but execution plan missing supply-side seeding strategy.",
            "go_to_market", "execution",
            affected_sub_agents=["playbook_builder", "motion_designer"],
            rule_id="OR-20",
        )
    return RuleResult(True, "must_address", "", "go_to_market", "execution", rule_id="OR-20")


# ---------------------------------------------------------------------------
# Solo founder rule
# ---------------------------------------------------------------------------

def _check_solo_founder(state: dict[str, Any]) -> RuleResult:
    """OR-21: Solo founder feasibility."""
    constraints = state.get("constraints", {})
    team_size = constraints.get("team_size", 1)
    if team_size > 2:
        return RuleResult(True, "should_address", "", "execution", "execution", rule_id="OR-21")

    motion = _get_motion_data(state)
    motion_type = motion.get("motion", "") if motion else ""

    if motion_type == "outbound_led":
        return RuleResult(
            False, "must_address",
            f"Team of {team_size} cannot sustain outbound-led motion. Consider PLG or inbound.",
            "execution", "go_to_market",
            affected_sub_agents=["motion_designer", "resource_planner"],
            rule_id="OR-21",
        )

    pt = state.get("pillars", {}).get("product_tech", {})
    feasibility = pt.get("feasibility_flags", {})
    complexity = feasibility.get("complexity", "low")
    if complexity == "high":
        return RuleResult(
            False, "must_address",
            f"High technical complexity with team of {team_size} — reduce scope or extend timeline.",
            "execution", "product_tech",
            affected_sub_agents=["feature_scoper", "resource_planner"],
            rule_id="OR-21",
        )

    return RuleResult(True, "should_address", "", "execution", "execution", rule_id="OR-21")


# ---------------------------------------------------------------------------
# Gap viability rule (Issue 5 downstream)
# ---------------------------------------------------------------------------

def _check_gap_viability(state: dict[str, Any]) -> RuleResult:
    """OR-22: Gap viability check for red-flag gap types."""
    gap_type = _get_gap_type(state)
    if not gap_type or gap_type not in RED_FLAG_GAPS:
        return RuleResult(True, "must_address", "", "market_intelligence", "positioning_pricing", rule_id="OR-22")

    # Check if wedge/positioning addresses the red flag
    pp = state.get("pillars", {}).get("positioning_pricing", {})
    summary = pp.get("summary", "").lower()

    barrier_keywords = ["overcome", "barrier", "despite", "unlike previous", "different approach"]
    addresses_barrier = any(kw in summary for kw in barrier_keywords)

    if not addresses_barrier:
        msg = {
            "attempted_and_failed": "Market gap classified as 'attempted and failed' — positioning must explain why this attempt is different.",
            "well_funded_incumbent": "Well-funded incumbent in this space — positioning must show a flanking strategy, not a head-on attack.",
        }
        return RuleResult(
            False, "must_address",
            msg.get(gap_type, f"Red-flag gap type '{gap_type}' not addressed in positioning."),
            "market_intelligence", "positioning_pricing",
            affected_sub_agents=["wedge_builder", "category_framer"],
            rule_id="OR-22",
        )
    return RuleResult(True, "must_address", "", "market_intelligence", "positioning_pricing", rule_id="OR-22")


# ---------------------------------------------------------------------------
# Rule collections
# ---------------------------------------------------------------------------

BASE_RULES: list[OrchestratorRule] = [
    OrchestratorRule("OR-01", "ICP-Channel alignment", "must_address", "customer", "go_to_market", _check_icp_channel_alignment),
    OrchestratorRule("OR-02", "ICP-Motion compatibility", "must_address", "customer", "go_to_market", _check_icp_motion_compatibility),
    OrchestratorRule("OR-03", "Pricing-ICP budget fit", "must_address", "positioning_pricing", "customer", _check_pricing_icp_budget),
    OrchestratorRule("OR-04", "Channel cost vs budget", "should_address", "go_to_market", "execution", _check_channel_cost_vs_budget),
    OrchestratorRule("OR-05", "MVP timeline vs constraint", "must_address", "product_tech", "execution", _check_mvp_timeline),
    OrchestratorRule("OR-06", "Revenue target vs pricing math", "should_address", "positioning_pricing", "execution", _check_revenue_vs_pricing),
    OrchestratorRule("OR-07", "Team capacity vs motion", "must_address", "execution", "go_to_market", _check_team_capacity),
    OrchestratorRule("OR-08", "Sales motion vs pricing tier", "should_address", "go_to_market", "positioning_pricing", _check_motion_pricing_tier),
    OrchestratorRule("OR-09", "Channel-messaging alignment", "should_address", "go_to_market", "go_to_market", _check_channel_messaging),
    OrchestratorRule("OR-10", "Evidence coverage minimum", "must_address", "market_intelligence", "market_intelligence", _check_evidence_coverage),
]

CATEGORY_RULES: dict[str, list[OrchestratorRule]] = {
    "b2c": [
        OrchestratorRule("OR-11", "B2C monetization viability", "must_address", "positioning_pricing", "execution", _check_b2c_monetization),
        OrchestratorRule("OR-12", "B2C retention risk", "should_address", "go_to_market", "execution", _check_b2c_retention),
    ],
    "dev_tools": [
        OrchestratorRule("OR-13", "Dev tools competitive moat", "must_address", "market_intelligence", "positioning_pricing", _check_devtools_moat),
        OrchestratorRule("OR-14", "Dev tools free tier pressure", "should_address", "positioning_pricing", "go_to_market", _check_devtools_free_tier),
    ],
    "vertical_saas": [
        OrchestratorRule("OR-15", "Vertical SaaS data dependency", "should_address", "product_tech", "product_tech", _check_vertical_data_dependency),
        OrchestratorRule("OR-16", "Vertical SaaS channel fit", "should_address", "go_to_market", "go_to_market", _check_vertical_channel_fit),
        OrchestratorRule("OR-17", "Vertical SaaS trade show calendar", "should_address", "execution", "go_to_market", _check_trade_show_calendar),
    ],
}

COMPLIANCE_RULES: list[OrchestratorRule] = [
    OrchestratorRule("OR-18", "Compliance-timeline mismatch", "must_address", "product_tech", "execution", _check_compliance_timeline),
    OrchestratorRule("OR-19", "Compliance-budget mismatch", "must_address", "product_tech", "execution", _check_compliance_budget),
]

OR_20 = OrchestratorRule("OR-20", "Marketplace chicken-and-egg", "must_address", "go_to_market", "execution", _check_marketplace_chicken_egg)
OR_21 = OrchestratorRule("OR-21", "Solo founder feasibility", "must_address", "execution", "go_to_market", _check_solo_founder)
OR_22 = OrchestratorRule("OR-22", "Gap viability check", "must_address", "market_intelligence", "positioning_pricing", _check_gap_viability)


# ---------------------------------------------------------------------------
# Rule loader
# ---------------------------------------------------------------------------

def load_rules(category: str, state: dict[str, Any]) -> list[OrchestratorRule]:
    """Load applicable rules based on category, compliance level, and constraints."""
    rules = list(BASE_RULES)

    # Category-specific rules
    rules += CATEGORY_RULES.get(category, [])

    # Compliance rules (conditional)
    compliance = state.get("constraints", {}).get("compliance_level", "none")
    if compliance != "none":
        rules += COMPLIANCE_RULES

    # Marketplace detection
    idea = state.get("idea", {})
    text = (idea.get("problem", "") + idea.get("one_liner", "")).lower()
    if any(kw in text for kw in ["marketplace", "platform", "two-sided"]):
        rules.append(OR_20)

    # Solo founder
    team_size = state.get("constraints", {}).get("team_size", 1)
    if team_size <= 2:
        rules.append(OR_21)

    # Gap viability (red flag detection)
    gap_type = _get_gap_type(state)
    if gap_type and gap_type in RED_FLAG_GAPS:
        rules.append(OR_22)

    return rules
