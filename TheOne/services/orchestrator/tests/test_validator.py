from __future__ import annotations

from services.orchestrator.state.default_state import create_default_state
from services.orchestrator.validators.rules import run_validator


def state() -> dict:
    return create_default_state(
        project_id="proj_1",
        scenario_id="scn_1",
        run_id="run_1",
        idea={
            "name": "PulsePilot",
            "one_liner": "one liner",
            "problem": "problem",
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


def test_v_price_01_blocks_when_metric_missing() -> None:
    s = state()
    s["decisions"]["pricing"]["metric"] = ""
    s["decisions"]["pricing"]["tiers"] = [{"name": "starter", "price": 49}]

    result = run_validator(s, finalize=True)

    assert result["blocking"] is True
    assert any(item["rule_id"] == "V-PRICE-01" for item in result["contradictions"])


def test_v_sales_01_flags_plg_with_enterprise_icp() -> None:
    s = state()
    s["decisions"]["sales_motion"]["motion"] = "plg"
    s["decisions"]["icp"]["profile"] = {"company_size": "500+", "budget_owner": "procurement"}

    result = run_validator(s)

    assert any(item["rule_id"] == "V-SALES-01" for item in result["contradictions"])


def test_v_chan_01_sets_focus_failure_flag() -> None:
    s = state()
    s["decisions"]["channels"]["primary_channels"] = ["linkedin", "seo", "events"]

    result = run_validator(s)

    assert any(item["rule_id"] == "V-CHAN-01" for item in result["high_risk_flags"])


def test_v_evid_02_adds_missing_proof_when_pricing_decided_without_anchors() -> None:
    s = state()
    s["decisions"]["pricing"]["metric"] = "per_seat"
    s["evidence"]["pricing_anchors"] = []

    result = run_validator(s)

    assert any(item["rule_id"] == "V-EVID-02" for item in result["missing_proof"])


def test_v_exec_01_blocks_final_export_if_track_unset() -> None:
    s = state()
    s["execution"]["chosen_track"] = "unset"

    result = run_validator(s, export_final=True)

    assert result["blocking"] is True
    assert any(item["rule_id"] == "V-EXEC-01" for item in result["contradictions"])


def test_v_cont_01_blocks_custom_override_without_justification() -> None:
    s = state()
    s["decisions"]["pricing"]["override"] = {"is_custom": True, "justification": ""}

    result = run_validator(s)

    assert result["blocking"] is True
    assert any(item["rule_id"] == "V-CONT-01" for item in result["contradictions"])


def test_v_ops_01_blocks_mark_complete_when_execution_empty() -> None:
    s = state()
    s["execution"]["next_actions"] = []

    result = run_validator(s, mark_complete=True, finalize=True)

    assert result["blocking"] is True
    assert any(item["rule_id"] == "V-OPS-01" for item in result["contradictions"])
