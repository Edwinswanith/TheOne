"""Pillar cluster execution engine."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent
from services.orchestrator.agents.sub_agents.schemas import ReasoningArtifact, SubAgentOutput


@dataclass
class ClusterOutput:
    """Output from executing a full pillar cluster."""

    pillar: str
    artifacts: list[ReasoningArtifact] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)


PublishFn = Callable[[str, dict[str, Any]], Awaitable[None]]


class PillarCluster:
    """Executes a sequence of sub-agents for a single pillar.

    Sub-agents run sequentially within a cluster, building up a shared
    cluster_context dict. When feedback is provided (round 2), only
    affected sub-agents and the synthesizer (last sub-agent) re-execute;
    others reuse their round 1 output.
    """

    def __init__(self, pillar: str, sub_agents: list[BaseSubAgent]) -> None:
        self.pillar = pillar
        self.sub_agents = sub_agents

    async def execute(
        self,
        run_id: str,
        state: dict[str, Any],
        publish: PublishFn,
        changed_decision: str | None = None,
        feedback: Any | None = None,
        previous_context: dict[str, Any] | None = None,
    ) -> ClusterOutput:
        """Execute all sub-agents in sequence, collecting artifacts and outputs.

        Args:
            run_id: Current pipeline run ID.
            state: Canonical state dict.
            publish: Async SSE event publisher.
            changed_decision: If partial rerun, which decision changed.
            feedback: Orchestrator feedback directives (round 2 only).
            previous_context: Round 1 context for selective re-execution.
        """
        cluster_context: dict[str, Any] = dict(previous_context or {})
        artifacts: list[ReasoningArtifact] = []
        outputs: list[dict[str, Any]] = []

        # Determine which sub-agents to run in feedback round
        affected_agents: set[str] | None = None
        if feedback is not None:
            affected_agents = set()
            if isinstance(feedback, list):
                for directive in feedback:
                    if hasattr(directive, "affected_sub_agents"):
                        affected_agents.update(directive.affected_sub_agents)
                    elif isinstance(directive, dict):
                        affected_agents.update(directive.get("affected_sub_agents", []))
            # Always include the synthesizer (last sub-agent)
            if self.sub_agents:
                affected_agents.add(self.sub_agents[-1].name)

        round_num = 1 if feedback is not None else 0

        for sub_agent in self.sub_agents:
            # Skip unaffected agents in feedback round (reuse round 1 output)
            if affected_agents is not None and sub_agent.name not in affected_agents:
                if sub_agent.name in cluster_context:
                    outputs.append(cluster_context[sub_agent.name])
                continue

            await publish("sub_agent_started", {
                "agent": sub_agent.name,
                "pillar": self.pillar,
                "step": sub_agent.step_number,
                "total_steps": sub_agent.total_steps,
                "round": round_num,
            })

            # Run sub-agent in thread pool (BaseAgent._call_llm is synchronous)
            result: SubAgentOutput = await asyncio.to_thread(
                sub_agent.run,
                run_id,
                state,
                changed_decision,
                cluster_context,
                feedback,
                round_num,
            )

            cluster_context[sub_agent.name] = result.agent_output
            artifacts.append(result.artifact)
            outputs.append(result.agent_output)

            await publish("sub_agent_completed", {
                "agent": sub_agent.name,
                "pillar": self.pillar,
                "artifact_id": result.artifact.artifact_id,
                "step": sub_agent.step_number,
                "total_steps": sub_agent.total_steps,
                "round": round_num,
            })

        return ClusterOutput(pillar=self.pillar, artifacts=artifacts, outputs=outputs)
