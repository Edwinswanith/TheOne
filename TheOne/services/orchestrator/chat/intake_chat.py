"""Conversational intake chat module.

Drives a turn-by-turn chat to collect the 5 required intake fields.
AI asks one question at a time, adapts based on answers, and tracks readiness.
"""
from __future__ import annotations

from typing import Any

REQUIRED_FIELDS = [
    "buyer_role",
    "company_type",
    "trigger_event",
    "current_workaround",
    "measurable_outcome",
]

FIELD_LABELS = {
    "buyer_role": "the target buyer role",
    "company_type": "the type of company you're targeting",
    "trigger_event": "what triggers the purchase decision",
    "current_workaround": "how prospects solve this problem today",
    "measurable_outcome": "the measurable outcome your product delivers",
}


def compute_readiness(collected: set[str]) -> float:
    """Return 0.0-1.0 readiness score based on collected fields."""
    return len(collected.intersection(REQUIRED_FIELDS)) / len(REQUIRED_FIELDS)


def next_field(collected: set[str]) -> str | None:
    """Return the next field to ask about, or None if all collected."""
    for field in REQUIRED_FIELDS:
        if field not in collected:
            return field
    return None


def next_question_prompt(
    idea: dict[str, Any],
    constraints: dict[str, Any],
    history: list[dict[str, str]],
    collected: set[str],
    raw_context: str | None = None,
) -> str:
    """Build the Gemini prompt to generate the next conversational question."""
    field = next_field(collected)
    if not field:
        return ""

    history_text = ""
    for msg in history[-10:]:  # last 10 messages for context
        history_text += f"{msg['role'].upper()}: {msg['content']}\n"

    context_section = ""
    if raw_context:
        context_section = (
            f"\nThe user originally described their idea as:\n\"{raw_context}\"\n"
            "Use this context to ask smarter follow-up questions and skip topics already covered.\n"
        )

    return (
        "You are a friendly GTM strategy expert having a conversation with a founder. "
        "You're helping them define their go-to-market plan. "
        f"Their product: {idea.get('name', '')} — {idea.get('one_liner', '')}. "
        f"Problem it solves: {idea.get('problem', '')}. "
        f"Target region: {idea.get('target_region', '')}. "
        f"Team size: {constraints.get('team_size', 1)}, "
        f"Budget: ${constraints.get('budget_usd_monthly', 0)}/mo.\n\n"
        f"{context_section}"
        f"Conversation so far:\n{history_text}\n"
        f"You need to ask about: {FIELD_LABELS[field]}.\n\n"
        "Return ONLY a JSON object with these keys:\n"
        '- "message": A natural, conversational question (1-2 sentences)\n'
        '- "field": The field being asked about (one of: buyer_role, company_type, trigger_event, current_workaround, measurable_outcome)\n'
        '- "suggestions": An array of 2-3 short suggestion strings the user could click\n\n'
        "Be concise and conversational. Reference what they've already told you."
    )


def extract_field_prompt(user_msg: str, field: str, idea: dict[str, Any]) -> str:
    """Build the Gemini prompt to extract a structured field value from user's free text."""
    return (
        "Extract a concise, structured answer from the user's message.\n\n"
        f"Product: {idea.get('name', '')} — {idea.get('one_liner', '')}\n"
        f"Field to extract: {field} ({FIELD_LABELS.get(field, field)})\n"
        f"User said: \"{user_msg}\"\n\n"
        "Return ONLY a JSON object with:\n"
        '- "value": The extracted answer as a concise string\n'
        '- "confidence": A float 0.0-1.0 for how confident you are in the extraction\n'
        '- "field": The field name\n'
    )


# Fixture responses for deterministic testing
_FIXTURE_RESPONSES: dict[str, dict[str, Any]] = {
    "buyer_role": {
        "message": "Let's start with the buyer. Who would be the primary decision-maker for your product?",
        "field": "buyer_role",
        "suggestions": ["VP of Sales", "Head of Marketing", "CTO / Engineering Lead"],
    },
    "company_type": {
        "message": "Great! What type of company are you targeting?",
        "field": "company_type",
        "suggestions": ["B2B SaaS (50-200 employees)", "Enterprise (500+)", "SMB / Startups"],
    },
    "trigger_event": {
        "message": "What event typically triggers them to look for a solution like yours?",
        "field": "trigger_event",
        "suggestions": ["Missed revenue targets", "Team scaling challenges", "Compliance requirement"],
    },
    "current_workaround": {
        "message": "How are they currently solving this problem without your product?",
        "field": "current_workaround",
        "suggestions": ["Manual spreadsheets", "Cobbled-together tools", "Hiring more people"],
    },
    "measurable_outcome": {
        "message": "What measurable outcome can you promise them?",
        "field": "measurable_outcome",
        "suggestions": ["30% faster time-to-close", "50% reduction in manual work", "2x pipeline coverage"],
    },
}

_FIXTURE_EXTRACTIONS: dict[str, dict[str, Any]] = {
    "buyer_role": {"value": "VP of Sales", "confidence": 0.85, "field": "buyer_role"},
    "company_type": {"value": "B2B SaaS, 50-200 employees", "confidence": 0.9, "field": "company_type"},
    "trigger_event": {"value": "Missed revenue targets", "confidence": 0.8, "field": "trigger_event"},
    "current_workaround": {"value": "Manual CRM notes and spreadsheets", "confidence": 0.85, "field": "current_workaround"},
    "measurable_outcome": {"value": "30% increase in quota attainment", "confidence": 0.88, "field": "measurable_outcome"},
}


def fixture_chat_response(collected: set[str]) -> dict[str, Any] | None:
    """Return deterministic fixture response for the next uncollected field."""
    field = next_field(collected)
    if not field:
        return None
    resp = _FIXTURE_RESPONSES[field].copy()
    readiness = compute_readiness(collected)
    return {
        **resp,
        "readiness": readiness,
        "ready": readiness >= 1.0,
        "collected_fields": sorted(collected),
    }


def fixture_extract(field: str) -> dict[str, Any]:
    """Return deterministic extraction for a field."""
    return _FIXTURE_EXTRACTIONS.get(field, {"value": "User input", "confidence": 0.7, "field": field})
