"""Validator agent — runs validation rules on canonical state."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent


class ValidatorAgent(BaseAgent):
    """Validates state consistency via rules.py — returns empty output.

    This agent is a no-op placeholder in the agent pipeline. Actual validation
    is performed by `services.orchestrator.validators.rules.py` which runs
    14 deterministic rules (V-ICP-01 through V-CONT-01) against the canonical
    state. The validator agent exists in the AGENT_SEQUENCE so the runtime can
    trigger the reconciliation pass after all other agents have completed.

    The run() method returns an empty AgentOutput (no patches, proposals, or
    facts) because validation results are written directly to
    `state.risks.contradictions[]` by the rules engine, not through the
    standard merge pipeline.
    """

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
