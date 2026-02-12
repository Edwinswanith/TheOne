from __future__ import annotations

from services.orchestrator.tools.providers import ProviderClient


def test_clarification_fixture_returns_questions() -> None:
    provider = ProviderClient()
    state = {"idea": {"name": "Test", "one_liner": "test", "problem": "test", "target_region": "US", "category": "b2b_saas"}, "constraints": {"team_size": 2, "timeline_weeks": 8}}
    result = provider.generate_clarification_questions(state)
    assert "questions" in result
    assert len(result["questions"]) >= 5


def test_clarification_covers_required_fields() -> None:
    provider = ProviderClient()
    state = {"idea": {"name": "Test"}, "constraints": {}}
    result = provider.generate_clarification_questions(state)
    question_ids = {q["id"] for q in result["questions"]}
    required = {"buyer_role", "company_type", "trigger_event", "current_workaround", "measurable_outcome"}
    assert required.issubset(question_ids)


def test_clarification_question_has_recommended() -> None:
    provider = ProviderClient()
    state = {"idea": {"name": "Test"}, "constraints": {}}
    result = provider.generate_clarification_questions(state)
    for q in result["questions"]:
        recommended_count = sum(1 for opt in q["options"] if opt.get("recommended"))
        assert recommended_count == 1, f"Question {q['id']} has {recommended_count} recommended options"
