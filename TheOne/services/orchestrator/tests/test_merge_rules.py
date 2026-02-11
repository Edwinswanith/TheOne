from __future__ import annotations

from services.orchestrator.state.default_state import create_default_state
from services.orchestrator.state.merge import merge_agent_outputs


def base_state() -> dict:
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


def patch(path: str, value, source_type: str = "inference", confidence: float = 0.8, sources: list[str] | None = None) -> dict:
    return {
        "op": "replace",
        "path": path,
        "value": value,
        "meta": {
            "source_type": source_type,
            "confidence": confidence,
            "sources": sources or [],
        },
    }


def test_decision_ownership_enforced() -> None:
    state = base_state()
    outputs = [
        {
            "agent": "pricing_agent",
            "patches": [patch("/decisions/icp/selected_option_id", "icp_opt_1")],
            "proposals": [],
        }
    ]
    merged, warnings = merge_agent_outputs(state, outputs)

    assert merged["decisions"]["icp"]["selected_option_id"] == ""
    assert warnings
    assert any(err["code"] == "decision_ownership_violation" for err in merged["telemetry"]["errors"])


def test_evidence_sources_dedupe_by_normalized_url() -> None:
    state = base_state()
    outputs = [
        {
            "agent": "evidence_collector",
            "patches": [
                {
                    "op": "add",
                    "path": "/evidence/sources",
                    "value": [
                        {
                            "id": "src_1",
                            "url": "https://example.com/pricing",
                            "title": "Pricing",
                            "snippets": ["A"],
                            "quality_score": 0.6,
                        },
                        {
                            "id": "src_2",
                            "url": "https://example.com/pricing/",
                            "title": "Pricing Duplicate",
                            "snippets": ["B"],
                            "quality_score": 0.9,
                        },
                    ],
                    "meta": {
                        "source_type": "evidence",
                        "confidence": 0.95,
                        "sources": ["https://example.com/pricing"],
                    },
                }
            ],
            "proposals": [],
        }
    ]

    merged, _ = merge_agent_outputs(state, outputs)
    assert len(merged["evidence"]["sources"]) == 1
    source = merged["evidence"]["sources"][0]
    assert source["quality_score"] == 0.9
    assert set(source["snippets"]) == {"A", "B"}


def test_conflicting_evidence_updates_create_validator_item() -> None:
    state = base_state()
    outputs = [
        {
            "agent": "agent_a",
            "patches": [
                patch(
                    "/pillars/market_to_money/summary",
                    "Evidence-backed summary A",
                    source_type="evidence",
                    confidence=0.7,
                    sources=["https://a.com"],
                )
            ],
            "proposals": [],
        },
        {
            "agent": "agent_b",
            "patches": [
                patch(
                    "/pillars/market_to_money/summary",
                    "Evidence-backed summary B",
                    source_type="evidence",
                    confidence=0.8,
                    sources=["https://b.com"],
                )
            ],
            "proposals": [],
        },
    ]

    merged, _ = merge_agent_outputs(state, outputs)
    contradiction_ids = {item["rule_id"] for item in merged["risks"]["contradictions"]}
    assert "V-CONFLICT-EVID" in contradiction_ids


def test_evidence_without_sources_forced_to_assumption_and_capped_confidence() -> None:
    state = base_state()
    outputs = [
        {
            "agent": "agent_a",
            "patches": [
                patch(
                    "/decisions/pricing/metric",
                    "per_seat",
                    source_type="evidence",
                    confidence=0.95,
                    sources=[],
                )
            ],
            "proposals": [],
            "facts": [
                {
                    "claim": "Pricing will convert at 20%",
                    "supporting_sources": [],
                    "confidence": 0.9,
                }
            ],
        }
    ]

    merged, _ = merge_agent_outputs(state, outputs)
    error_codes = [error["code"] for error in merged["telemetry"]["errors"]]
    assert "evidence_without_sources" in error_codes
    assert "fact_without_source" in error_codes


def test_graph_node_ids_are_upserted_without_duplicates() -> None:
    state = base_state()

    first = {
        "agent": "graph_builder",
        "patches": [
            patch(
                "/graph/nodes",
                [
                    {
                        "id": "pricing.metric",
                        "title": "Pricing",
                        "pillar": "market_to_money",
                        "type": "decision",
                        "content": {"metric": "per_seat"},
                        "assumptions": [],
                        "confidence": 0.7,
                        "evidence_refs": [],
                        "dependencies": ["pricing"],
                        "status": "draft",
                        "actions": ["edit"],
                        "updated_at": "2026-01-01T00:00:00+00:00",
                    }
                ],
                source_type="inference",
            )
        ],
        "proposals": [],
    }

    second = {
        "agent": "graph_builder",
        "patches": [
            patch(
                "/graph/nodes",
                [
                    {
                        "id": "pricing.metric",
                        "title": "Pricing",
                        "pillar": "market_to_money",
                        "type": "decision",
                        "content": {"metric": "per_usage"},
                        "assumptions": [],
                        "confidence": 0.75,
                        "evidence_refs": [],
                        "dependencies": ["pricing"],
                        "status": "draft",
                        "actions": ["edit"],
                        "updated_at": "2026-01-02T00:00:00+00:00",
                    }
                ],
                source_type="inference",
            )
        ],
        "proposals": [],
    }

    merged, _ = merge_agent_outputs(state, [first, second])
    node_ids = [node["id"] for node in merged["graph"]["nodes"]]
    assert node_ids.count("pricing.metric") == 1
    assert merged["graph"]["nodes"][0]["content"]["metric"] == "per_usage"
