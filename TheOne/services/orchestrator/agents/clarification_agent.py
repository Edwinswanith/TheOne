"""Clarification agent — generates MCQ questions for pre-pipeline intake."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent


class ClarificationAgent(BaseAgent):
    """Generates MCQ questions to surface and confirm AI assumptions before pipeline runs."""

    name = "clarification_agent"
    pillar = ""  # Pre-pipeline, not pillar-specific

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Build clarification questions prompt."""
        idea = state.get("idea", {})
        constraints = state.get("constraints", {})

        return (
            "You are a GTM strategy expert. Based on the product idea below, "
            "generate 8-12 multiple-choice clarification questions. "
            "5 required fields (buyer_role, company_type, trigger_event, current_workaround, measurable_outcome) "
            "plus 3-7 contextual questions. Each question has 3-4 options with one marked recommended. "
            "Include a 'why' explanation per question. "
            "Return JSON with key 'questions' containing array of question objects. "
            f"Idea: name={idea.get('name','')}, one_liner={idea.get('one_liner','')}, "
            f"problem={idea.get('problem','')}, category={idea.get('category','')}. "
            f"Constraints: team_size={constraints.get('team_size','')}, "
            f"timeline_weeks={constraints.get('timeline_weeks','')}."
        )

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse clarification questions from LLM response."""
        return {
            "questions": raw.get("questions", []),
            "patches": [],
            "proposals": [],
            "facts": [],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": [],
        }

    def run(
        self, run_id: str, state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Generate clarification questions using provider."""
        result = self.provider.generate_clarification_questions(state)
        return result
