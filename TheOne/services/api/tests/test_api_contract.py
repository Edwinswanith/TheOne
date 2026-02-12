from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from services.api.app.main import app, store


@pytest.fixture(autouse=True)
def reset_store():
    store.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _create_project(client: TestClient) -> tuple[str, str]:
    response = client.post(
        "/projects",
        json={
            "project_name": "GTMGraph QA Project",
            "idea": {
                "name": "PulsePilot",
                "one_liner": "AI assistant that turns customer calls into actionable follow-ups",
                "problem": "Teams forget follow-ups and lose deals",
                "target_region": "UK",
                "category": "b2b_saas",
            },
            "constraints": {
                "team_size": 2,
                "timeline_weeks": 8,
                "budget_usd_monthly": 500,
                "compliance_level": "none",
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    return payload["project"]["id"], payload["scenario"]["id"]


def _submit_required_intake(client: TestClient, scenario_id: str) -> None:
    response = client.post(
        f"/scenarios/{scenario_id}/intake",
        json={
            "answers": [
                {
                    "question_id": "buyer_role",
                    "answer_type": "mcq",
                    "value": "Head of Sales",
                    "is_recommended": True,
                },
                {
                    "question_id": "company_type",
                    "answer_type": "text",
                    "value": "B2B SaaS",
                },
                {
                    "question_id": "trigger_event",
                    "answer_type": "text",
                    "value": "Hiring new sales reps",
                },
                {
                    "question_id": "current_workaround",
                    "answer_type": "text",
                    "value": "Spreadsheets",
                },
                {
                    "question_id": "measurable_outcome",
                    "answer_type": "text",
                    "value": "Reduce lead leakage",
                },
            ]
        },
    )
    assert response.status_code == 200


def _start_run(client: TestClient, scenario_id: str, payload: dict | None = None) -> dict:
    response = client.post(f"/scenarios/{scenario_id}/runs", json=payload or {})
    assert response.status_code == 200
    return response.json()


def _scenario_state(client: TestClient, scenario_id: str) -> dict:
    response = client.get(f"/scenarios/{scenario_id}")
    assert response.status_code == 200
    return response.json()["state"]


def test_create_project_initializes_canonical_state(client: TestClient) -> None:
    _, scenario_id = _create_project(client)
    state = _scenario_state(client, scenario_id)

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
        "artifacts",
    }
    assert state["execution"]["chosen_track"] == "unset"
    assert state["decisions"]["icp"]["selected_option_id"] == ""


def test_run_is_blocked_when_required_intake_is_missing(client: TestClient) -> None:
    _, scenario_id = _create_project(client)

    before_runs = len(store.runs)
    run_resp = client.post(f"/scenarios/{scenario_id}/runs")

    assert run_resp.status_code == 422
    assert len(store.runs) == before_runs
    detail = run_resp.json()["detail"]
    assert "buyer_role" in detail["missing_requirements"]


def test_mcq_recommended_answer_saves_without_justification(client: TestClient) -> None:
    _, scenario_id = _create_project(client)

    response = client.post(
        f"/scenarios/{scenario_id}/intake",
        json={
            "answers": [
                {
                    "question_id": "buyer_role",
                    "answer_type": "mcq",
                    "value": "Head of Sales",
                    "is_recommended": True,
                    "meta": {
                        "source_type": "inference",
                        "confidence": 0.7,
                        "sources": [],
                    },
                }
            ]
        },
    )

    assert response.status_code == 200
    state = _scenario_state(client, scenario_id)
    answer = state["inputs"]["intake_answers"][0]
    assert answer["answer_type"] == "mcq"
    assert answer["value"] == "Head of Sales"
    assert answer.get("justification", "") in {"", None}
    assert answer["meta"]["source_type"] in {"inference", "assumption"}


def test_custom_override_requires_justification(client: TestClient) -> None:
    _, scenario_id = _create_project(client)
    _submit_required_intake(client, scenario_id)
    _start_run(client, scenario_id)

    response = client.post(
        f"/scenarios/{scenario_id}/decisions/pricing/select",
        json={
            "is_custom": True,
            "custom_value": {"metric": "per_deal_closed"},
            "justification": "",
        },
    )
    assert response.status_code == 422
    assert "requires justification" in response.json()["detail"]["message"].lower()


def test_override_impact_warning_generated_and_confidence_reduced(client: TestClient) -> None:
    _, scenario_id = _create_project(client)
    _submit_required_intake(client, scenario_id)
    _start_run(client, scenario_id)

    before_state = _scenario_state(client, scenario_id)
    before_conf = {
        node["id"]: node["confidence"]
        for node in before_state["graph"]["nodes"]
        if node["id"] in {"pricing.metric", "execution.pipeline"}
    }

    response = client.post(
        f"/scenarios/{scenario_id}/decisions/pricing/select",
        json={
            "is_custom": True,
            "custom_value": {"metric": "per_deal_closed"},
            "justification": "Align pricing to revenue impact.",
        },
    )
    assert response.status_code == 200

    after_state = _scenario_state(client, scenario_id)
    assert any(flag["rule_id"] == "OVERRIDE-IMPACT" for flag in after_state["risks"]["high_risk_flags"])

    after_conf = {
        node["id"]: node["confidence"]
        for node in after_state["graph"]["nodes"]
        if node["id"] in before_conf
    }

    assert after_conf["pricing.metric"] < before_conf["pricing.metric"]
    assert after_conf["execution.pipeline"] < before_conf["execution.pipeline"]


def test_channel_focus_guardrail_requires_override_and_normalizes_channels(client: TestClient) -> None:
    _, scenario_id = _create_project(client)

    blocked = client.post(
        f"/scenarios/{scenario_id}/decisions/channels/select",
        json={
            "selected_option_id": "chan_opt_1",
            "primary_channels": ["linkedin", "seo", "events"],
        },
    )
    assert blocked.status_code == 422

    accepted = client.post(
        f"/scenarios/{scenario_id}/decisions/channels/select",
        json={
            "selected_option_id": "chan_opt_1",
            "primary_channels": ["linkedin", "seo", "events"],
            "justification": "Temporary broad test before narrowing.",
        },
    )
    assert accepted.status_code == 200

    state = _scenario_state(client, scenario_id)
    channels = state["decisions"]["channels"]
    assert channels["primary"] == "linkedin"
    assert channels["secondary"] == "seo"
    assert channels["primary_channels"] == ["linkedin", "seo"]


def test_full_run_produces_stable_graph_without_duplicates_on_repeat(client: TestClient) -> None:
    _, scenario_id = _create_project(client)
    _submit_required_intake(client, scenario_id)

    _start_run(client, scenario_id)
    first = _scenario_state(client, scenario_id)
    first_ids = [node["id"] for node in first["graph"]["nodes"]]

    _start_run(client, scenario_id)
    second = _scenario_state(client, scenario_id)
    second_ids = [node["id"] for node in second["graph"]["nodes"]]

    assert len(first_ids) >= 20
    assert len(first_ids) == len(set(first_ids))
    assert len(second_ids) == len(set(second_ids))
    assert len(second_ids) == len(first_ids)


def test_partial_rerun_only_recomputes_dependents_and_skips_unrelated_agents(client: TestClient) -> None:
    _, scenario_id = _create_project(client)
    _submit_required_intake(client, scenario_id)

    _start_run(client, scenario_id)
    before = _scenario_state(client, scenario_id)
    product_node_before = next(node for node in before["graph"]["nodes"] if node["id"] == "product.core_offer")

    rerun = _start_run(client, scenario_id, payload={"changed_decision": "icp"})
    run_id = rerun["run_id"]

    run_status = client.get(f"/runs/{run_id}")
    assert run_status.status_code == 200
    run_payload = run_status.json()
    assert run_payload["status"] in {"completed", "blocked"}

    after = _scenario_state(client, scenario_id)
    product_node_after = next(node for node in after["graph"]["nodes"] if node["id"] == "product.core_offer")
    assert product_node_after["updated_at"] == product_node_before["updated_at"]

    run_record = store.runs[run_id]
    assert "evidence_collector" in run_record.skipped_agents
    assert "icp_agent" in run_record.skipped_agents


def test_run_resume_from_checkpoint_after_failure(client: TestClient) -> None:
    _, scenario_id = _create_project(client)
    _submit_required_intake(client, scenario_id)

    failed_run = _start_run(client, scenario_id, payload={"simulate_failure_at_agent": "pricing_agent"})
    failed_run_id = failed_run["run_id"]
    assert store.runs[failed_run_id].status == "failed"

    resumed = client.post(f"/runs/{failed_run_id}/resume")
    assert resumed.status_code == 200
    resumed_payload = resumed.json()

    resumed_run = store.runs[resumed_payload["run_id"]]
    assert resumed_run.resumed_from_run_id == failed_run_id
    assert resumed_run.status in {"completed", "blocked"}


def test_final_export_blocked_until_execution_track_selected(client: TestClient) -> None:
    _, scenario_id = _create_project(client)

    blocked = client.post(f"/scenarios/{scenario_id}/export", json={"kind": "final", "format": "md"})
    assert blocked.status_code == 422
    blocked_rules = {item["rule_id"] for item in blocked.json()["detail"]["contradictions"]}
    assert "V-EXEC-01" in blocked_rules

    track = client.patch(
        f"/scenarios/{scenario_id}/execution-track",
        json={"chosen_track": "validation_sprint"},
    )
    assert track.status_code == 200

    exported = client.post(f"/scenarios/{scenario_id}/export", json={"kind": "final", "format": "md"})
    assert exported.status_code == 422
    rules_after_track = {item["rule_id"] for item in exported.json()["detail"]["contradictions"]}
    assert "V-EXEC-01" not in rules_after_track


def test_compare_scenarios_returns_decision_diff(client: TestClient) -> None:
    project_id, scenario_a = _create_project(client)
    scenario_b_resp = client.post(f"/projects/{project_id}/scenarios", json={"name": "Scenario B"})
    assert scenario_b_resp.status_code == 200
    scenario_b = scenario_b_resp.json()["id"]

    selected = client.post(
        f"/scenarios/{scenario_b}/decisions/icp/select",
        json={"selected_option_id": "icp_opt_2"},
    )
    assert selected.status_code == 200

    compare = client.post(
        "/scenarios/compare",
        json={"left_scenario_id": scenario_a, "right_scenario_id": scenario_b},
    )
    assert compare.status_code == 200
    payload = compare.json()
    assert "icp" in payload["decision_diff"]
