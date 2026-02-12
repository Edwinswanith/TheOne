"""Reasoning artifact schemas for sub-agent transparency."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReasoningStep:
    """A single step in a sub-agent's reasoning chain."""

    step: int
    action: str  # "query_generation", "search_execution", "analysis", "synthesis"
    thought: str  # Reasoning text shown to users
    data: dict[str, Any] | None = None  # Structured data for this step
    confidence: float = 0.0
    source_ids: list[str] = field(default_factory=list)


@dataclass
class ReasoningArtifact:
    """Full reasoning trace for a sub-agent execution."""

    artifact_id: str  # "{agent_name}_{run_id}_{round}"
    agent: str
    pillar: str
    round: int  # 0 = first pass, 1 = feedback round
    reasoning_chain: list[ReasoningStep] = field(default_factory=list)
    output_summary: str = ""
    execution_meta: dict[str, Any] = field(default_factory=dict)
    # execution_meta keys: llm_calls, external_searches, total_tokens, execution_time_ms, model

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "agent": self.agent,
            "pillar": self.pillar,
            "round": self.round,
            "reasoning_chain": [
                {
                    "step": s.step,
                    "action": s.action,
                    "thought": s.thought,
                    "data": s.data,
                    "confidence": s.confidence,
                    "source_ids": s.source_ids,
                }
                for s in self.reasoning_chain
            ],
            "output_summary": self.output_summary,
            "execution_meta": self.execution_meta,
        }


@dataclass
class SubAgentOutput:
    """Combined output from a sub-agent: reasoning artifact + standard agent output."""

    artifact: ReasoningArtifact
    agent_output: dict[str, Any]  # Standard AgentOutput dict (patches, proposals, facts, etc.)
