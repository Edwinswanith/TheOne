"""Validator agent — runs validation rules on canonical state."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent


class ValidatorAgent(BaseAgent):
    """Validates state consistency via rules.py — returns empty output."""

    name = "validator_agent"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Not used - validator uses rules.py."""
        return ""

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Not used - validator uses rules.py."""
        return {}

    def run(
        self, run_id: str, state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Override run to return empty output - validation is done via rules.py."""
        parsed = {
            "patches": [],
            "proposals": [],
            "facts": [],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": []
        }

        return self._wrap_output(run_id, parsed)
