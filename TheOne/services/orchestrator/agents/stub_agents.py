from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.orchestrator.dependencies import impacted_decisions
from services.orchestrator.tools.providers import ProviderClient


provider_client = ProviderClient()


def _meta(source_type: str = "inference", confidence: float = 0.7, sources: list[str] | None = None) -> dict[str, Any]:
    return {
        "source_type": source_type,
        "confidence": confidence,
        "sources": sources or [],
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_agent_output(
    agent: str,
    run_id: str,
    state: dict[str, Any],
    changed_decision: str | None = None,
) -> dict[str, Any]:
    builder = AGENT_BUILDERS.get(agent)
    if not builder:
        return _empty_output(agent, run_id)
    return builder(run_id, state, changed_decision)


def _empty_output(agent: str, run_id: str) -> dict[str, Any]:
    return {
        "agent": agent,
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [],
        "proposals": [],
        "facts": [],
        "assumptions": [],
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


def _evidence_output(run_id: str, state: dict[str, Any], _: str | None) -> dict[str, Any]:
    evidence_bundle = provider_client.fetch_evidence_bundle(state)
    synthesis = provider_client.synthesize_evidence(evidence_bundle)

    return {
        "agent": "evidence_collector",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/evidence/sources",
                "value": [
                    {
                        "id": f"src_comp_{idx + 1}",
                        "url": item["url"],
                        "title": item.get("title", ""),
                        "snippets": item.get("snippets", []),
                        "quality_score": item.get("quality_score", 0.6),
                    }
                    for idx, item in enumerate(evidence_bundle.get("sources", []))
                ],
                "meta": _meta("evidence", 0.92, ["https://example.com/pricing"]),
            },
            {
                "op": "replace",
                "path": "/evidence/competitors",
                "value": evidence_bundle.get("competitors", []),
                "meta": _meta("evidence", 0.81, ["https://example.com/pricing"]),
            },
            {
                "op": "replace",
                "path": "/evidence/pricing_anchors",
                "value": evidence_bundle.get("pricing_anchors", []),
                "meta": _meta("evidence", 0.88, ["https://example.com/pricing"]),
            },
            {
                "op": "replace",
                "path": "/evidence/messaging_patterns",
                "value": evidence_bundle.get("messaging_patterns", []),
                "meta": _meta("evidence", 0.73, ["https://example.com/pricing"]),
            },
            {
                "op": "replace",
                "path": "/evidence/channel_signals",
                "value": evidence_bundle.get("channel_signals", []),
                "meta": _meta("evidence", 0.7, ["https://example.com/pricing"]),
            },
        ],
        "proposals": [],
        "facts": synthesis.get("facts", []),
        "assumptions": synthesis.get("assumptions", []),
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


def _icp_output(run_id: str, state: dict[str, Any], _: str | None) -> dict[str, Any]:
    template = provider_client.decision_template("icp")

    return {
        "agent": "icp_agent",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/decisions/icp/profile",
                "value": {
                    "buyer_role": "Head of Sales",
                    "company_size": "50-200",
                    "budget_owner": "sales_lead",
                    "trigger_event": "Hiring new reps",
                },
                "meta": _meta("inference", 0.74),
            }
        ],
        "proposals": [
            {
                "decision_key": "icp",
                "options": template.get("options", []),
                "recommended_option_id": template.get("recommended_option_id", "icp_opt_1"),
                "rationale": template.get("rationale", "Best evidence-backed fit from current source set."),
                "meta": _meta("inference", 0.74),
            }
        ],
        "facts": [],
        "assumptions": [],
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


def _positioning_output(run_id: str, state: dict[str, Any], _: str | None) -> dict[str, Any]:
    template = provider_client.decision_template("positioning")

    return {
        "agent": "positioning_agent",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/decisions/positioning/frame",
                "value": {
                    "category": "Revenue operations assistant",
                    "wedge": "Call-to-follow-up automation",
                    "value_prop": "Reduce lead leakage by 30%",
                },
                "meta": _meta("inference", 0.76),
            },
            {
                "op": "replace",
                "path": "/pillars/market_to_money/summary",
                "value": "Position around faster follow-up and measurable pipeline recovery.",
                "meta": _meta("inference", 0.73),
            },
        ],
        "proposals": [
            {
                "decision_key": "positioning",
                "options": template.get("options", []),
                "recommended_option_id": template.get("recommended_option_id", "pos_opt_1"),
                "rationale": template.get("rationale", "Aligns with buyer pain from intake and evidence."),
                "meta": _meta("inference", 0.76),
            }
        ],
        "facts": [],
        "assumptions": [],
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


def _pricing_output(run_id: str, state: dict[str, Any], _: str | None) -> dict[str, Any]:
    template = provider_client.decision_template("pricing")

    return {
        "agent": "pricing_agent",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/decisions/pricing/metric",
                "value": "per_seat",
                "meta": _meta("inference", 0.72),
            },
            {
                "op": "replace",
                "path": "/decisions/pricing/tiers",
                "value": [
                    {"name": "Starter", "price": 49},
                    {"name": "Growth", "price": 149},
                ],
                "meta": _meta("inference", 0.68),
            },
            {
                "op": "replace",
                "path": "/decisions/pricing/price_to_test",
                "value": 99,
                "meta": _meta("inference", 0.66),
            },
        ],
        "proposals": [
            {
                "decision_key": "pricing",
                "options": template.get("options", []),
                "recommended_option_id": template.get("recommended_option_id", "price_opt_1"),
                "rationale": template.get("rationale", "Closest match to evidence anchors."),
                "meta": _meta("inference", 0.72),
            }
        ],
        "facts": [],
        "assumptions": [],
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


def _channel_output(run_id: str, state: dict[str, Any], _: str | None) -> dict[str, Any]:
    template = provider_client.decision_template("channels")

    return {
        "agent": "channel_strategy_agent",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/decisions/channels/primary",
                "value": "linkedin_outbound",
                "meta": _meta("inference", 0.72),
            },
            {
                "op": "replace",
                "path": "/decisions/channels/secondary",
                "value": "founder_network",
                "meta": _meta("inference", 0.61),
            },
            {
                "op": "replace",
                "path": "/decisions/channels/primary_channels",
                "value": ["linkedin_outbound"],
                "meta": _meta("inference", 0.72),
            },
        ],
        "proposals": [
            {
                "decision_key": "channels",
                "options": template.get("options", []),
                "recommended_option_id": template.get("recommended_option_id", "chan_opt_1"),
                "rationale": template.get("rationale", "Strongest signal from channel evidence set."),
                "meta": _meta("inference", 0.72),
            }
        ],
        "facts": [],
        "assumptions": [],
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


def _sales_output(run_id: str, state: dict[str, Any], _: str | None) -> dict[str, Any]:
    template = provider_client.decision_template("sales_motion")

    return {
        "agent": "sales_motion_agent",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/decisions/sales_motion/motion",
                "value": "outbound_led",
                "meta": _meta("inference", 0.7),
            }
        ],
        "proposals": [
            {
                "decision_key": "sales_motion",
                "options": template.get("options", []),
                "recommended_option_id": template.get("recommended_option_id", "sales_opt_1"),
                "rationale": template.get("rationale", "Best fit for current ICP/channel combination."),
                "meta": _meta("inference", 0.7),
            }
        ],
        "facts": [],
        "assumptions": [],
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


def _product_output(run_id: str, state: dict[str, Any], _: str | None) -> dict[str, Any]:
    return {
        "agent": "product_strategy_agent",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/pillars/product/summary",
                "value": "Prioritize call summarization, follow-up extraction, and CRM sync.",
                "meta": _meta("inference", 0.75),
            },
            {
                "op": "replace",
                "path": "/pillars/product/nodes",
                "value": ["product.core_offer", "product.onboarding", "product.integration", "product.security_plan"],
                "meta": _meta("inference", 0.7),
            },
        ],
        "proposals": [],
        "facts": [],
        "assumptions": [],
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


def _tech_output(run_id: str, state: dict[str, Any], _: str | None) -> dict[str, Any]:
    compliance = state["constraints"].get("compliance_level", "none")
    security_plan = (
        "Data retention policy + encrypted transcript storage"
        if compliance in {"medium", "high"}
        else "Baseline logging and role-based access"
    )
    return {
        "agent": "tech_architecture_agent",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/pillars/execution/security_plan",
                "value": security_plan,
                "meta": _meta("inference", 0.64),
            }
        ],
        "proposals": [],
        "facts": [],
        "assumptions": [],
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


def _people_output(run_id: str, state: dict[str, Any], _: str | None) -> dict[str, Any]:
    return {
        "agent": "people_cash_agent",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/pillars/people_and_cash/summary",
                "value": "Keep burn below $10k and hire one SDR only after PMF signal.",
                "meta": _meta("inference", 0.66),
            },
            {
                "op": "replace",
                "path": "/pillars/people_and_cash/nodes",
                "value": ["people.team_plan", "people.runway", "people.hiring", "people.ops"],
                "meta": _meta("inference", 0.66),
            },
        ],
        "proposals": [],
        "facts": [],
        "assumptions": [],
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


def _execution_output(run_id: str, state: dict[str, Any], changed_decision: str | None) -> dict[str, Any]:
    actions = [
        {"title": "Interview 10 target buyers", "owner": "founder", "week": 1},
        {"title": "Send first 50 outbound messages", "owner": "founder", "week": 1},
        {"title": "Launch landing page with CTA", "owner": "marketing", "week": 2},
    ]
    if changed_decision:
        actions.insert(0, {"title": f"Revalidate after {changed_decision} change", "owner": "founder", "week": 0})

    return {
        "agent": "execution_agent",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/execution/next_actions",
                "value": actions,
                "meta": _meta("inference", 0.7),
            },
            {
                "op": "replace",
                "path": "/execution/experiments",
                "value": [
                    {
                        "hypothesis": "Head of Sales will pay for automated follow-up",
                        "steps": ["Run outreach", "Book demos", "Collect objections"],
                        "metric": "Demo-to-trial conversion",
                    }
                ],
                "meta": _meta("inference", 0.67),
            },
        ],
        "proposals": [],
        "facts": [],
        "assumptions": [],
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


def _graph_output(run_id: str, state: dict[str, Any], changed_decision: str | None) -> dict[str, Any]:
    nodes = _graph_nodes(state, changed_decision)
    return {
        "agent": "graph_builder",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/graph/nodes",
                "value": nodes,
                "meta": _meta("inference", 0.7),
            },
            {
                "op": "replace",
                "path": "/graph/groups",
                "value": _graph_groups(nodes),
                "meta": _meta("inference", 0.7),
            },
        ],
        "proposals": [],
        "facts": [],
        "assumptions": [],
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


def _validator_output(run_id: str, _: dict[str, Any], __: str | None) -> dict[str, Any]:
    return _empty_output("validator_agent", run_id)


def _graph_nodes(state: dict[str, Any], changed_decision: str | None) -> list[dict[str, Any]]:
    pricing_metric = state["decisions"]["pricing"].get("metric", "")
    primary_channel = state["decisions"]["channels"].get("primary", "")
    secondary_channel = state["decisions"]["channels"].get("secondary", "")
    sales_motion = state["decisions"]["sales_motion"].get("motion", "")
    value_prop = state["decisions"]["positioning"].get("frame", {}).get("value_prop", "")

    template = [
        ("market.icp.summary", "ICP Summary", "market_to_money", "decision", {"buyer_role": state["decisions"]["icp"].get("profile", {}).get("buyer_role", "")}, ["icp"]),
        ("market.trigger.event", "Trigger Event", "market_to_money", "evidence", {"trigger": state["decisions"]["icp"].get("profile", {}).get("trigger_event", "")}, ["icp"]),
        ("positioning.wedge", "Positioning Wedge", "market_to_money", "decision", {"value_prop": value_prop}, ["positioning", "icp"]),
        ("pricing.metric", "Pricing Metric", "market_to_money", "decision", {"metric": pricing_metric}, ["pricing", "icp"]),
        ("pricing.tiers", "Pricing Tiers", "market_to_money", "plan", {"tiers": state["decisions"]["pricing"].get("tiers", [])}, ["pricing"]),
        ("channel.primary", "Primary Channel", "market_to_money", "decision", {"primary": primary_channel}, ["channels"]),
        ("channel.secondary", "Secondary Channel", "market_to_money", "decision", {"secondary": secondary_channel}, ["channels"]),
        ("sales.motion", "Sales Motion", "market_to_money", "decision", {"motion": sales_motion}, ["sales_motion", "channels", "icp"]),
        ("product.core_offer", "Core Offer", "product", "plan", {"summary": "Call-to-follow-up automation"}, ["positioning"]),
        ("product.onboarding", "Onboarding Flow", "product", "plan", {"step": "Import calls and connect CRM"}, ["product"]),
        ("product.integration", "Integration Plan", "product", "plan", {"targets": ["HubSpot", "Salesforce"]}, ["product"]),
        ("product.security_plan", "Security Plan", "product", "risk", {"plan": state["pillars"]["execution"].get("security_plan", "")}, ["tech"]),
        ("execution.validation_sprint", "Validation Sprint", "execution", "checklist", {"duration_weeks": 2}, ["execution"]),
        ("execution.outbound_playbook", "Outbound Playbook", "execution", "asset", {"messages": 50}, ["execution", "channels"]),
        ("execution.landing_page", "Landing Page Sprint", "execution", "asset", {"goal": "waitlist"}, ["execution"]),
        ("execution.pipeline", "Pipeline Review", "execution", "checklist", {"kpi": "lead leakage reduction"}, ["execution", "pricing", "sales_motion"]),
        ("people.team_plan", "Team Plan", "people_and_cash", "plan", {"team_size": state["constraints"].get("team_size", 1)}, ["people_and_cash"]),
        ("people.runway", "Runway Plan", "people_and_cash", "risk", {"budget": state["constraints"].get("budget_usd_monthly", 0)}, ["pricing", "people_and_cash"]),
        ("people.hiring", "Hiring Trigger", "people_and_cash", "checklist", {"trigger": "After first 10 customers"}, ["execution"]),
        ("people.ops", "Ops Checklist", "people_and_cash", "checklist", {"items": ["Weekly metrics", "Risk review"]}, ["execution"]),
    ]

    impacted = impacted_decisions(changed_decision) if changed_decision else set()
    if changed_decision:
        impacted.add(changed_decision)

    nodes = []
    for node_id, title, pillar, node_type, content, dependencies in template:
        if changed_decision and not any(dep in impacted for dep in dependencies):
            continue
        nodes.append(
            {
                "id": node_id,
                "title": title,
                "pillar": pillar,
                "type": node_type,
                "content": content,
                "assumptions": [],
                "confidence": 0.74 if "pricing" in node_id or "sales" in node_id else 0.7,
                "evidence_refs": ["src_comp_1"] if pillar == "market_to_money" else [],
                "dependencies": dependencies,
                "status": "draft",
                "actions": ["edit", "rerun"],
                "updated_at": _now(),
            }
        )
    return nodes


def _graph_groups(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {
        "market_to_money": [],
        "product": [],
        "execution": [],
        "people_and_cash": [],
    }
    for node in nodes:
        grouped[node["pillar"]].append(node["id"])

    return [
        {"id": "group.market_to_money", "title": "Market to Money", "node_ids": grouped["market_to_money"]},
        {"id": "group.product", "title": "Product", "node_ids": grouped["product"]},
        {"id": "group.execution", "title": "Execution", "node_ids": grouped["execution"]},
        {"id": "group.people_and_cash", "title": "People and Cash", "node_ids": grouped["people_and_cash"]},
    ]


AGENT_BUILDERS = {
    "evidence_collector": _evidence_output,
    "icp_agent": _icp_output,
    "positioning_agent": _positioning_output,
    "pricing_agent": _pricing_output,
    "channel_strategy_agent": _channel_output,
    "sales_motion_agent": _sales_output,
    "product_strategy_agent": _product_output,
    "tech_architecture_agent": _tech_output,
    "people_cash_agent": _people_output,
    "execution_agent": _execution_output,
    "graph_builder": _graph_output,
    "validator_agent": _validator_output,
}
