from __future__ import annotations

from services.orchestrator.state.default_state import create_default_state
from services.orchestrator.state.validation import StateValidationError, validate_state


def build_state() -> dict:
    return create_default_state(
        project_id="proj_1",
        scenario_id="scn_1",
        run_id="unset",
        idea={
            "name": "PulsePilot",
            "one_liner": "AI assistant that turns customer calls into follow-ups",
            "problem": "Teams forget follow-ups",
            "target_region": "UK",
            "category": "b2b_saas",
        },
        constraints={
            "team_size": 2,
            "timeline_weeks": 8,
            "budget_usd_monthly": 500,
            "compliance_level": "none",
        },
    )


def test_default_state_contains_required_top_keys() -> None:
    state = build_state()
    assert set(state.keys()) == {
        "meta",
        "idea",
        "constraints",
        "inputs",
        "evidence",
        "decisions",
        "pillars",
        "graph",
        "risks",
        "execution",
        "telemetry",
    }
    assert state["meta"]["schema_version"]
    assert state["execution"]["chosen_track"] == "unset"
    assert state["decisions"]["icp"]["selected_option_id"] == ""
    assert isinstance(state["graph"]["nodes"], list)
    assert isinstance(state["graph"]["edges"], list)
    assert isinstance(state["graph"]["groups"], list)


def test_default_state_has_six_pillars() -> None:
    state = build_state()
    expected_pillars = {
        "market_intelligence",
        "customer",
        "positioning_pricing",
        "go_to_market",
        "product_tech",
        "execution",
    }
    assert set(state["pillars"].keys()) == expected_pillars


def test_default_state_has_six_graph_groups() -> None:
    state = build_state()
    group_ids = {g["id"] for g in state["graph"]["groups"]}
    expected_groups = {
        "group.market_intelligence",
        "group.customer",
        "group.positioning_pricing",
        "group.go_to_market",
        "group.product_tech",
        "group.execution",
    }
    assert group_ids == expected_groups


def test_schema_rejects_unknown_root_keys() -> None:
    state = build_state()
    state["randomKey"] = {"drift": True}
    try:
        validate_state(state)
    except StateValidationError as err:
        assert "additional properties" in str(err).lower() or "unknown" in str(err).lower()
    else:
        raise AssertionError("expected validation error")
