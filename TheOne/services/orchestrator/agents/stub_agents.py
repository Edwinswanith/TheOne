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
        "sources": [],
        "citations": [],
        "execution_time_ms": 0,
        "token_usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "model": "stub",
        },
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
                "path": "/pillars/positioning_pricing/summary",
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
        "agent": "channel_agent",
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
                "path": "/pillars/product_tech/summary",
                "value": "Prioritize call summarization, follow-up extraction, and CRM sync.",
                "meta": _meta("inference", 0.75),
            },
            {
                "op": "replace",
                "path": "/pillars/product_tech/nodes",
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
        "agent": "tech_feasibility_agent",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/pillars/product_tech/security_plan",
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
                "path": "/pillars/execution/team_plan",
                "value": {"summary": "Keep burn below $10k and hire one SDR only after PMF signal."},
                "meta": _meta("inference", 0.66),
            },
            {
                "op": "replace",
                "path": "/pillars/execution/nodes",
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
    # Extract rich data from canonical state
    icp_profile = state["decisions"]["icp"].get("profile", {})
    pos_frame = state["decisions"]["positioning"].get("frame", {})
    pricing = state["decisions"]["pricing"]
    channels = state["decisions"]["channels"]
    evidence = state.get("evidence", {})
    pillars = state.get("pillars", {})
    execution = state.get("execution", {})
    constraints = state.get("constraints", {})
    competitors = evidence.get("competitors", [])
    pricing_anchors = evidence.get("pricing_anchors", [])
    channel_signals = evidence.get("channel_signals", [])

    buyer_role = icp_profile.get("buyer_role", "")
    company_size = icp_profile.get("company_size", "")
    trigger_event = icp_profile.get("trigger_event", "")
    value_prop = pos_frame.get("value_prop", "")
    category = pos_frame.get("category", "")
    wedge = pos_frame.get("wedge", "")
    pricing_metric = pricing.get("metric", "")
    tiers = pricing.get("tiers", [])
    price_to_test = pricing.get("price_to_test", "")
    primary_channel = channels.get("primary", "")
    secondary_channel = channels.get("secondary", "")
    sales_motion = state["decisions"]["sales_motion"].get("motion", "")

    next_actions = execution.get("next_actions", [])
    experiments = execution.get("experiments", [])
    team_plan = pillars.get("execution", {}).get("team_plan", {})
    product_summary = pillars.get("product_tech", {}).get("summary", "")
    mvp_features = pillars.get("product_tech", {}).get("mvp_features", [])
    roadmap_phases = pillars.get("product_tech", {}).get("roadmap_phases", [])
    pos_summary = pillars.get("positioning_pricing", {}).get("summary", "")
    gtm_summary = pillars.get("go_to_market", {}).get("summary", "")
    security_plan = pillars.get("product_tech", {}).get("security_plan", "")
    compliance_level = constraints.get("compliance_level", "none")

    # Build tier summary text
    tier_names = [f"{t.get('name', '')} (${t.get('price', '')})" for t in tiers] if tiers else []
    tier_summary = f"Tiered pricing: {', '.join(tier_names)}" if tier_names else "No tiers defined"

    # ICP rationale from proposal if available
    icp_opts = state["decisions"]["icp"].get("options", [])
    icp_rationale = ""
    icp_rec_id = state["decisions"]["icp"].get("recommended_option_id", "")
    for opt in icp_opts:
        if opt.get("id") == icp_rec_id:
            icp_rationale = opt.get("description", "")
            break

    template = [
        # Level 1 pillar summary nodes
        ("pillar.market_intelligence", "Market Intelligence", "market_intelligence", "pillar", {}, []),
        ("pillar.customer", "Customer", "customer", "pillar", {}, []),
        ("pillar.positioning_pricing", "Positioning & Pricing", "positioning_pricing", "pillar", {}, []),
        ("pillar.go_to_market", "Go-to-Market", "go_to_market", "pillar", {}, []),
        ("pillar.product_tech", "Product & Tech", "product_tech", "pillar", {}, []),
        ("pillar.execution", "Execution", "execution", "pillar", {}, []),
        # Level 2 detail nodes — enriched content
        (
            "market.icp.summary", "ICP Summary", "customer", "decision",
            {
                "summary": f"Target buyer: {buyer_role} at {company_size} companies, triggered by {trigger_event}." if buyer_role else "ICP not yet defined.",
                "buyer_role": buyer_role,
                "company_size": company_size,
                "budget_owner": icp_profile.get("budget_owner", ""),
                "trigger_event": trigger_event,
                "rationale": icp_rationale or "Best evidence-backed fit from current source set.",
            },
            ["icp"],
        ),
        (
            "market.trigger.event", "Trigger Event", "customer", "evidence",
            {
                "summary": f"Key trigger: {trigger_event}. Signals buyer readiness and urgency to act." if trigger_event else "No trigger event identified.",
                "trigger": trigger_event,
                "why_it_matters": "Trigger events create urgency and budget allocation for new solutions.",
                "competitors_count": len(competitors),
            },
            ["icp"],
        ),
        (
            "positioning.wedge", "Positioning Wedge", "positioning_pricing", "decision",
            {
                "summary": f"Position as '{category}' leading with '{wedge}' — {value_prop}." if wedge else "Positioning not yet defined.",
                "category": category,
                "wedge": wedge,
                "value_prop": value_prop,
                "pillar_summary": pos_summary,
                "rationale": "Aligns with buyer pain from intake and evidence.",
            },
            ["positioning", "icp"],
        ),
        (
            "pricing.metric", "Pricing Metric", "positioning_pricing", "decision",
            {
                "summary": f"Recommended pricing model: {pricing_metric.replace('_', ' ')} at ${price_to_test}/mo test point." if pricing_metric else "Pricing metric not set.",
                "metric": pricing_metric,
                "price_to_test": price_to_test,
                "rationale": "Closest match to evidence anchors and competitor pricing.",
                "anchors": pricing_anchors[:3] if pricing_anchors else [],
            },
            ["pricing", "icp"],
        ),
        (
            "pricing.tiers", "Pricing Tiers", "positioning_pricing", "plan",
            {
                "summary": tier_summary,
                "tiers": tiers,
            },
            ["pricing"],
        ),
        (
            "channel.primary", "Primary Channel", "go_to_market", "decision",
            {
                "summary": f"Primary acquisition channel: {primary_channel.replace('_', ' ')}." if primary_channel else "Primary channel not selected.",
                "channel": primary_channel,
                "channel_signals": channel_signals[:3] if channel_signals else [],
                "rationale": "Strongest signal from channel evidence set.",
            },
            ["channels"],
        ),
        (
            "channel.secondary", "Secondary Channel", "go_to_market", "decision",
            {
                "summary": f"Secondary channel: {secondary_channel.replace('_', ' ')} to diversify acquisition." if secondary_channel else "No secondary channel.",
                "channel": secondary_channel,
                "rationale": "Complements primary channel for broader reach.",
            },
            ["channels"],
        ),
        (
            "sales.motion", "Sales Motion", "go_to_market", "decision",
            {
                "summary": f"Sales approach: {sales_motion.replace('_', ' ')}." if sales_motion != "unset" else "Sales motion not decided.",
                "motion": sales_motion,
                "pillar_summary": gtm_summary,
                "rationale": "Best fit for current ICP/channel combination.",
            },
            ["sales_motion", "channels", "icp"],
        ),
        (
            "product.core_offer", "Core Offer", "product_tech", "plan",
            {
                "summary": product_summary or "Core product offer pending strategy agent.",
                "mvp_features": mvp_features or ["Call summarization", "Follow-up extraction", "CRM sync"],
                "roadmap_phases": roadmap_phases or ["MVP: core automation", "V2: integrations", "V3: analytics"],
            },
            ["positioning"],
        ),
        (
            "product.onboarding", "Onboarding Flow", "product_tech", "plan",
            {
                "summary": "Guided onboarding: import calls, connect CRM, configure automations.",
                "steps": ["Import existing calls or connect live source", "Connect CRM (HubSpot/Salesforce)", "Configure follow-up automation rules", "Send first automated follow-up"],
                "integration_targets": ["HubSpot", "Salesforce"],
            },
            ["product"],
        ),
        (
            "product.integration", "Integration Plan", "product_tech", "plan",
            {
                "summary": "Priority integrations: HubSpot and Salesforce for CRM sync.",
                "targets": ["HubSpot", "Salesforce"],
                "priority": "HubSpot first (larger SMB install base), then Salesforce.",
            },
            ["product"],
        ),
        (
            "product.security_plan", "Security Plan", "product_tech", "risk",
            {
                "summary": f"Security posture: {compliance_level} compliance. {security_plan}" if security_plan else f"Compliance level: {compliance_level}. Security plan pending.",
                "plan": security_plan,
                "compliance_level": compliance_level,
            },
            ["tech"],
        ),
        (
            "execution.validation_sprint", "Validation Sprint", "execution", "checklist",
            {
                "summary": "2-week validation sprint: interview buyers, test messaging, validate willingness to pay.",
                "description": next_actions[0].get("title", "Interview 10 target buyers") if next_actions else "Interview 10 target buyers",
                "owner": next_actions[0].get("owner", "founder") if next_actions else "founder",
                "timeline": "Week 1-2",
                "success_metric": "10+ buyer interviews completed with pain confirmation",
            },
            ["execution"],
        ),
        (
            "execution.outbound_playbook", "Outbound Playbook", "execution", "asset",
            {
                "summary": "Send first 50 outbound messages to validate channel and messaging.",
                "description": next_actions[1].get("title", "Send first 50 outbound messages") if len(next_actions) > 1 else "Send first 50 outbound messages",
                "owner": next_actions[1].get("owner", "founder") if len(next_actions) > 1 else "founder",
                "timeline": "Week 1",
                "success_metric": "5%+ reply rate on cold outbound",
            },
            ["execution", "channels"],
        ),
        (
            "execution.landing_page", "Landing Page Sprint", "execution", "asset",
            {
                "summary": "Launch landing page with waitlist CTA to capture early demand signal.",
                "description": next_actions[2].get("title", "Launch landing page with CTA") if len(next_actions) > 2 else "Launch landing page with CTA",
                "owner": next_actions[2].get("owner", "marketing") if len(next_actions) > 2 else "marketing",
                "timeline": "Week 2",
                "success_metric": "100+ waitlist signups in first 2 weeks",
            },
            ["execution"],
        ),
        (
            "execution.pipeline", "Pipeline Review", "execution", "checklist",
            {
                "summary": "Track pipeline conversion from outbound to demo to trial to close.",
                "description": experiments[0].get("hypothesis", "") if experiments else "Validate buyer willingness to pay.",
                "owner": "founder",
                "timeline": "Ongoing",
                "success_metric": experiments[0].get("metric", "Demo-to-trial conversion") if experiments else "Demo-to-trial conversion",
            },
            ["execution", "pricing", "sales_motion"],
        ),
        (
            "people.team_plan", "Team Plan", "execution", "plan",
            {
                "summary": team_plan.get("summary", "Lean team: founder-led execution, hire after PMF signal."),
                "team_size": constraints.get("team_size", 1),
                "budget": constraints.get("budget_usd_monthly", 0),
                "hiring_trigger": "After first 10 paying customers or $10k MRR",
            },
            ["execution"],
        ),
        (
            "people.runway", "Runway Plan", "execution", "risk",
            {
                "summary": f"Monthly budget: ${constraints.get('budget_usd_monthly', 0):,.0f}. Keep burn minimal until PMF.",
                "budget": constraints.get("budget_usd_monthly", 0),
                "rationale": "Conserve runway until product-market fit is confirmed by conversion metrics.",
            },
            ["pricing", "execution"],
        ),
        (
            "people.hiring", "Hiring Trigger", "execution", "checklist",
            {
                "summary": "Hire first SDR after 10 customers or when founder capacity is saturated.",
                "trigger": "After first 10 customers",
                "rationale": "Premature hiring burns runway without validated demand.",
            },
            ["execution"],
        ),
        (
            "people.ops", "Ops Checklist", "execution", "checklist",
            {
                "summary": "Weekly ops cadence: metrics review, risk assessment, pipeline check.",
                "items": ["Weekly metrics review", "Risk register update", "Pipeline health check", "Customer feedback synthesis"],
            },
            ["execution"],
        ),
    ]

    impacted = impacted_decisions(changed_decision) if changed_decision else set()
    if changed_decision:
        impacted.add(changed_decision)

    # Node-specific assumptions for low-confidence areas
    node_assumptions: dict[str, list[str]] = {
        "pricing.metric": [f"Assumes {buyer_role or 'buyer'} has budget authority for ${price_to_test}/seat"] if price_to_test else [],
        "pricing.tiers": ["Tier pricing assumes clear feature differentiation between plans"],
        "channel.primary": [f"Assumes {primary_channel.replace('_', ' ')} reaches {buyer_role or 'target buyer'} effectively"] if primary_channel else [],
        "sales.motion": ["Sales motion choice depends on ICP validation from buyer interviews"],
        "people.runway": [f"Budget of ${constraints.get('budget_usd_monthly', 0):,.0f}/mo assumes no paid acquisition spend"],
    }

    # Node-specific evidence refs
    node_evidence: dict[str, list[str]] = {
        "market.icp.summary": ["src_comp_1"] if competitors else [],
        "market.trigger.event": ["src_comp_1"] if competitors else [],
        "positioning.wedge": ["src_comp_1", "src_comp_2"] if len(competitors) >= 2 else (["src_comp_1"] if competitors else []),
        "pricing.metric": [a.get("source_id", "src_pricing_1") for a in pricing_anchors[:2]] if pricing_anchors else [],
        "pricing.tiers": [a.get("source_id", "src_pricing_1") for a in pricing_anchors[:1]] if pricing_anchors else [],
        "channel.primary": ["src_comp_1"] if competitors else [],
    }

    nodes = []
    for node_id, title, pillar, node_type, content, dependencies in template:
        # Pillar summary nodes always included
        if node_type == "pillar":
            pass
        elif changed_decision and not any(dep in impacted for dep in dependencies):
            continue
        nodes.append(
            {
                "id": node_id,
                "title": title,
                "pillar": pillar,
                "type": node_type,
                "content": content,
                "assumptions": node_assumptions.get(node_id, []),
                "confidence": 0.74 if "pricing" in node_id or "sales" in node_id else 0.7,
                "evidence_refs": node_evidence.get(node_id, ["src_comp_1"] if pillar == "market_intelligence" else []),
                "dependencies": dependencies,
                "status": "draft",
                "actions": ["edit", "rerun"],
                "updated_at": _now(),
            }
        )
    return nodes


def _graph_groups(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {
        "market_intelligence": [],
        "customer": [],
        "positioning_pricing": [],
        "go_to_market": [],
        "product_tech": [],
        "execution": [],
    }
    for node in nodes:
        pillar = node["pillar"]
        if pillar in grouped:
            grouped[pillar].append(node["id"])

    return [
        {"id": "group.market_intelligence", "title": "Market Intelligence", "node_ids": grouped["market_intelligence"]},
        {"id": "group.customer", "title": "Customer", "node_ids": grouped["customer"]},
        {"id": "group.positioning_pricing", "title": "Positioning & Pricing", "node_ids": grouped["positioning_pricing"]},
        {"id": "group.go_to_market", "title": "Go-to-Market", "node_ids": grouped["go_to_market"]},
        {"id": "group.product_tech", "title": "Product & Tech", "node_ids": grouped["product_tech"]},
        {"id": "group.execution", "title": "Execution", "node_ids": grouped["execution"]},
    ]


def _competitive_teardown_output(run_id: str, state: dict[str, Any], _: str | None) -> dict[str, Any]:
    return {
        "agent": "competitive_teardown_agent",
        "run_id": run_id,
        "produced_at": _now(),
        "patches": [
            {
                "op": "replace",
                "path": "/evidence/competitors",
                "value": [
                    {
                        "name": "Competitor A",
                        "url": "https://example.com/competitor-a",
                        "positioning": "All-in-one platform",
                        "pricing_model": "per_seat",
                        "target_segment": "Mid-market",
                        "strengths": ["Brand recognition", "Feature breadth"],
                        "weaknesses": ["Complex onboarding", "High price"],
                        "category": "direct",
                        "channels": ["direct_sales", "content_marketing"],
                        "market_position": "leader",
                        "threat_level": "high",
                        "pricing_detail": {"base_price": 50, "model": "per_seat", "source_id": "src_comp_1"},
                        "weakness_evidence": [
                            {"claim": "Complex onboarding", "source": "G2 review", "relevance": "Speed-to-value wedge"},
                            {"claim": "High price excludes SMBs", "source": "Reddit thread", "relevance": "Price undercut opportunity"},
                        ],
                        "channel_footprint": {"channels_observed": ["linkedin_ads", "seo_blog", "webinars"], "estimated_primary": "direct_sales"},
                    },
                    {
                        "name": "Competitor B",
                        "url": "https://example.com/competitor-b",
                        "positioning": "Simple and fast",
                        "pricing_model": "flat_rate",
                        "target_segment": "SMB",
                        "strengths": ["Easy setup", "Low cost"],
                        "weaknesses": ["Limited integrations", "No enterprise features"],
                        "category": "direct",
                        "channels": ["product_led", "seo"],
                        "market_position": "niche",
                        "threat_level": "medium",
                        "pricing_detail": {"base_price": 29, "model": "flat_rate", "source_id": "src_comp_2"},
                        "weakness_evidence": [
                            {"claim": "Limited integrations", "source": "Capterra review", "relevance": "Integration gap for mid-market"},
                        ],
                        "channel_footprint": {"channels_observed": ["seo_blog", "product_hunt"], "estimated_primary": "product_led"},
                    },
                ],
                "meta": _meta("evidence", 0.78, ["https://example.com/competitor-a", "https://example.com/competitor-b"]),
            },
            {
                "op": "replace",
                "path": "/evidence/positioning_map",
                "value": [
                    {
                        "axes": {"x": "price_point", "y": "feature_depth"},
                        "placements": [
                            {"name": "Competitor A", "x": 0.7, "y": 0.85},
                            {"name": "Competitor B", "x": 0.3, "y": 0.4},
                        ],
                        "identified_gap": {
                            "x_range": [0.2, 0.5],
                            "y_range": [0.3, 0.6],
                            "description": "Low-price, focused-feature zone is underserved",
                            "confidence": 0.72,
                        },
                    }
                ],
                "meta": _meta("inference", 0.72, ["https://example.com/competitor-a"]),
            },
        ],
        "proposals": [],
        "facts": [
            {
                "claim": "Two direct competitors identified with distinct positioning strategies",
                "confidence": 0.78,
                "sources": ["https://example.com/competitor-a", "https://example.com/competitor-b"],
            }
        ],
        "assumptions": [],
        "risks": [],
        "required_inputs": [],
        "node_updates": [],
    }


AGENT_BUILDERS = {
    "evidence_collector": _evidence_output,
    "competitive_teardown_agent": _competitive_teardown_output,
    "icp_agent": _icp_output,
    "positioning_agent": _positioning_output,
    "pricing_agent": _pricing_output,
    "channel_agent": _channel_output,
    "sales_motion_agent": _sales_output,
    "product_strategy_agent": _product_output,
    "tech_feasibility_agent": _tech_output,
    "people_cash_agent": _people_output,
    "execution_agent": _execution_output,
    "graph_builder": _graph_output,
    "validator_agent": _validator_output,
}
