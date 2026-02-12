from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = "2.0.0"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_decision() -> dict[str, Any]:
    return {
        "selected_option_id": "",
        "options": [],
        "recommended_option_id": "",
        "override": {"is_custom": False, "justification": ""},
    }


def _base_state() -> dict[str, Any]:
    return {
        "meta": {
            "project_id": "",
            "scenario_id": "",
            "run_id": "unset",
            "schema_version": SCHEMA_VERSION,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "updated_by": "system",
        },
        "idea": {
            "name": "",
            "one_liner": "",
            "problem": "",
            "target_region": "",
            "category": "b2b_saas",
            "domain": "",
        },
        "constraints": {
            "team_size": 1,
            "timeline_weeks": 1,
            "budget_usd_monthly": 0,
            "compliance_level": "none",
        },
        "inputs": {
            "intake_answers": [],
            "open_questions": [],
            "clarification_responses": [],
        },
        "evidence": {
            "sources": [],
            "competitors": [],
            "pricing_anchors": [],
            "messaging_patterns": [],
            "channel_signals": [],
            "teardowns": [],
            "weakness_map": [],
            "positioning_map": [],
        },
        "decisions": {
            "icp": _empty_decision(),
            "positioning": _empty_decision(),
            "pricing": {
                **_empty_decision(),
                "metric": "",
                "tiers": [],
            },
            "channels": {
                **_empty_decision(),
                "primary": "",
                "secondary": "",
                "primary_channels": [],
            },
            "sales_motion": {
                **_empty_decision(),
                "motion": "unset",
            },
        },
        "pillars": {
            "market_intelligence": {"summary": "", "nodes": []},
            "customer": {"summary": "", "nodes": [], "objection_map": []},
            "positioning_pricing": {"summary": "", "nodes": []},
            "go_to_market": {"summary": "", "nodes": [], "messaging_templates": []},
            "product_tech": {"summary": "", "nodes": [], "mvp_features": [], "roadmap_phases": []},
            "execution": {"summary": "", "nodes": [], "team_plan": {}, "budget_allocation": {}, "playbook": [], "kill_criteria": [], "kpi_thresholds": []},
        },
        "graph": {
            "nodes": [],
            "edges": [],
            "groups": [
                {"id": "group.market_intelligence", "title": "Market Intelligence", "node_ids": []},
                {"id": "group.customer", "title": "Customer", "node_ids": []},
                {"id": "group.positioning_pricing", "title": "Positioning & Pricing", "node_ids": []},
                {"id": "group.go_to_market", "title": "Go-to-Market", "node_ids": []},
                {"id": "group.product_tech", "title": "Product & Tech", "node_ids": []},
                {"id": "group.execution", "title": "Execution", "node_ids": []},
            ],
        },
        "risks": {
            "contradictions": [],
            "missing_proof": [],
            "high_risk_flags": [],
            "unresolved_contradictions": [],
        },
        "execution": {
            "chosen_track": "unset",
            "next_actions": [],
            "experiments": [],
            "assets": [],
        },
        "telemetry": {
            "agent_timings": [],
            "token_spend": {"total": 0, "by_agent": []},
            "errors": [],
        },
    }


def create_default_state(
    project_id: str,
    scenario_id: str,
    idea: dict[str, Any],
    constraints: dict[str, Any],
    run_id: str | None = None,
) -> dict[str, Any]:
    state = deepcopy(_base_state())
    now = utc_now_iso()
    state["meta"]["project_id"] = project_id
    state["meta"]["scenario_id"] = scenario_id
    state["meta"]["run_id"] = run_id or "unset"
    state["meta"]["created_at"] = now
    state["meta"]["updated_at"] = now

    state["idea"]["name"] = idea["name"]
    state["idea"]["one_liner"] = idea["one_liner"]
    state["idea"]["problem"] = idea["problem"]
    state["idea"]["target_region"] = idea["target_region"]
    state["idea"]["category"] = idea.get("category", "b2b_saas")

    state["constraints"]["team_size"] = int(constraints["team_size"])
    state["constraints"]["timeline_weeks"] = int(constraints["timeline_weeks"])
    state["constraints"]["budget_usd_monthly"] = float(constraints["budget_usd_monthly"])
    state["constraints"]["compliance_level"] = constraints.get("compliance_level", "none")
    return state


def new_run_id() -> str:
    return f"run_{uuid4().hex}"
