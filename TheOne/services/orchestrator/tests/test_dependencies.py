from __future__ import annotations

from services.orchestrator.dependencies import impacted_decisions


def test_icp_change_only_targets_dependent_decisions() -> None:
    impacted = impacted_decisions("icp")
    assert "pricing" in impacted
    assert "channels" in impacted
    assert "sales_motion" in impacted
    assert "positioning" in impacted
    assert "execution" in impacted
