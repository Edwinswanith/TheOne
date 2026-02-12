from __future__ import annotations

import asyncio
from typing import Any

from services.orchestrator.runtime import _auto_recommend, run_pipeline
from services.orchestrator.state.default_state import create_default_state


def _test_state() -> dict[str, Any]:
    state = create_default_state(
        project_id="proj_1",
        scenario_id="scn_1",
        run_id="run_1",
        idea={"name": "Test", "one_liner": "test", "problem": "test", "target_region": "US", "category": "b2b_saas"},
        constraints={"team_size": 2, "timeline_weeks": 8, "budget_usd_monthly": 500, "compliance_level": "none"},
    )
    return state


def test_auto_recommend_sets_selected_option_id() -> None:
    state = _test_state()
    output = {
        "proposals": [
            {
                "decision_key": "icp",
                "recommended_option_id": "icp_opt_1",
                "options": [{"id": "icp_opt_1", "label": "Test"}],
            }
        ]
    }
    _auto_recommend(state, output)
    assert state["decisions"]["icp"]["selected_option_id"] == "icp_opt_1"
    assert state["decisions"]["icp"]["selection_mode"] == "auto_recommended"


def test_auto_recommend_does_not_override_existing_selection() -> None:
    state = _test_state()
    state["decisions"]["icp"]["selected_option_id"] = "existing_opt"
    output = {
        "proposals": [
            {
                "decision_key": "icp",
                "recommended_option_id": "icp_opt_1",
                "options": [],
            }
        ]
    }
    _auto_recommend(state, output)
    assert state["decisions"]["icp"]["selected_option_id"] == "existing_opt"


def test_reconciliation_only_on_fresh_runs() -> None:
    state = _test_state()
    events: list[tuple[str, dict]] = []

    async def publish(event: str, data: dict) -> None:
        events.append((event, data))

    async def checkpoint(s: dict, idx: int, agent: str) -> None:
        pass

    # Partial rerun — reconciliation should NOT run
    result = asyncio.new_event_loop().run_until_complete(
        run_pipeline(state, publish, checkpoint, changed_decision="icp")
    )
    # Check no pass 2 events
    pass2_events = [e for e in events if e[1].get("pass") == 2]
    assert len(pass2_events) == 0


def test_unresolved_contradictions_stored_in_risks() -> None:
    state = _test_state()

    async def publish(event: str, data: dict) -> None:
        pass

    async def checkpoint(s: dict, idx: int, agent: str) -> None:
        pass

    result = asyncio.new_event_loop().run_until_complete(
        run_pipeline(state, publish, checkpoint)
    )
    # unresolved_contradictions should exist (may be empty if no contradictions)
    assert "unresolved_contradictions" in result.state["risks"]
    assert isinstance(result.state["risks"]["unresolved_contradictions"], list)
