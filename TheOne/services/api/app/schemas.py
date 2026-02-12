from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class IdeaInput(BaseModel):
    name: str = Field(min_length=1)
    one_liner: str = Field(min_length=1)
    problem: str = Field(min_length=1)
    target_region: str = Field(min_length=1)
    category: Literal["b2b_saas", "b2b_services", "b2c"] = "b2b_saas"


class ConstraintsInput(BaseModel):
    team_size: int = Field(ge=1)
    timeline_weeks: int = Field(ge=1)
    budget_usd_monthly: float = Field(ge=0)
    compliance_level: Literal["none", "low", "medium", "high"] = "none"


class ProjectCreateRequest(BaseModel):
    project_name: str = Field(min_length=1)
    idea: IdeaInput
    constraints: ConstraintsInput


class ProjectPatchRequest(BaseModel):
    project_name: str | None = None


class ScenarioCreateRequest(BaseModel):
    name: str = Field(min_length=1)


class ScenarioPatchRequest(BaseModel):
    name: str | None = None


class IntakeAnswerInput(BaseModel):
    question_id: str
    answer_type: Literal["mcq", "text", "number", "boolean"]
    value: Any
    justification: str | None = None
    is_recommended: bool = False
    meta: dict[str, Any] = Field(
        default_factory=lambda: {
            "source_type": "inference",
            "confidence": 0.7,
            "sources": [],
        }
    )


class IntakeSubmitRequest(BaseModel):
    answers: list[IntakeAnswerInput]


class RunStartRequest(BaseModel):
    changed_decision: Literal["icp", "positioning", "pricing", "channels", "sales_motion"] | None = None
    simulate_failure_at_agent: str | None = None


class RunResponse(BaseModel):
    run_id: str
    scenario_id: str
    status: str
    stream_url: str


class RunStatusResponse(BaseModel):
    run_id: str
    scenario_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    resumed_from_run_id: str | None = None
    checkpoint_index: int = 0


class DecisionSelectRequest(BaseModel):
    selected_option_id: str | None = None
    is_custom: bool = False
    custom_value: dict[str, Any] | str | None = None
    justification: str | None = None
    primary_channels: list[str] | None = None


class ExecutionTrackRequest(BaseModel):
    chosen_track: Literal["validation_sprint", "outbound_sprint", "landing_waitlist", "pilot_onboarding", "unset"]


class ExportRequest(BaseModel):
    kind: Literal["draft", "final"] = "draft"
    format: Literal["md", "pdf"] = "md"


class ScenarioCompareRequest(BaseModel):
    left_scenario_id: str
    right_scenario_id: str


class ProjectFromContextRequest(BaseModel):
    context: str = Field(min_length=10)
    project_name: str | None = None


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1)
    field_context: str | None = None


class ClarificationOption(BaseModel):
    id: str
    label: str
    detail: str
    recommended: bool = False


class ClarificationQuestion(BaseModel):
    id: str
    question: str
    why: str = ""
    category: str = ""
    required: bool = True
    options: list[ClarificationOption]


class ClarificationSubmitRequest(BaseModel):
    answers: dict[str, Any]  # {question_id: {option_id: str, custom_value?: str}}
