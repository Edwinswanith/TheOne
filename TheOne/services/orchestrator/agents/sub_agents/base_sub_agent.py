"""Base sub-agent class for cluster-based pipeline execution."""
from __future__ import annotations

import time
from typing import Any

from services.orchestrator.agents.base import BaseAgent
from services.orchestrator.agents.sub_agents.schemas import (
    ReasoningArtifact,
    ReasoningStep,
    SubAgentOutput,
)


class BaseSubAgent(BaseAgent):
    """Extended base agent for cluster sub-agents.

    Adds cluster_context (prior sub-agent outputs) and feedback (orchestrator
    directives) to the prompt/parse lifecycle. Produces a ReasoningArtifact
    alongside the standard AgentOutput for transparency.

    Class attributes set by subclasses:
        pillar: str — which pillar cluster this belongs to
        step_number: int — position within the cluster (1-based)
        total_steps: int — total sub-agents in the cluster
        uses_external_search: bool — whether this agent calls Perplexity
    """

    pillar: str = ""
    step_number: int = 0
    total_steps: int = 0
    uses_external_search: bool = False

    def build_prompt(
        self,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
    ) -> str:
        """Build prompt with optional cluster context and orchestrator feedback.

        Subclasses override this instead of the base 2-arg version.
        """
        raise NotImplementedError

    def parse_response(
        self,
        raw: dict[str, Any],
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Parse response with optional cluster context.

        Must return a dict with standard keys (patches, proposals, facts, etc.)
        plus an optional "reasoning_steps" list of dicts for the artifact.
        """
        raise NotImplementedError

    def run(
        self,
        run_id: str,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
        round_num: int = 0,
    ) -> SubAgentOutput:
        """Execute the sub-agent and produce both AgentOutput and ReasoningArtifact."""
        timer = time.perf_counter()
        self._input_tokens = 0
        self._output_tokens = 0
        llm_calls = 0
        external_searches = 0
        reasoning_steps: list[ReasoningStep] = []

        # Step 1: Build prompt
        prompt = self.build_prompt(state, changed_decision, cluster_context, feedback)
        reasoning_steps.append(ReasoningStep(
            step=1,
            action="query_generation",
            thought=f"Building prompt for {self.name} (step {self.step_number}/{self.total_steps})",
            confidence=0.0,
        ))

        # Step 2: External search (if applicable — subclass overrides _run_searches)
        search_data = None
        if self.uses_external_search:
            search_data = self._run_searches(state, cluster_context)
            external_searches += 1
            if search_data:
                prompt = self._enrich_prompt_with_search(prompt, search_data)
                reasoning_steps.append(ReasoningStep(
                    step=2,
                    action="search_execution",
                    thought=f"Retrieved external data for {self.name}",
                    data={"search_result_keys": list(search_data.keys()) if isinstance(search_data, dict) else []},
                    confidence=0.7,
                ))

        # Step 3: LLM call
        raw = self._call_llm(prompt)
        llm_calls += 1
        reasoning_steps.append(ReasoningStep(
            step=len(reasoning_steps) + 1,
            action="analysis",
            thought=f"LLM analysis complete for {self.name}",
            confidence=0.5,
        ))

        # Step 4: Parse response
        parsed = self.parse_response(raw, state, changed_decision, cluster_context)

        # Extract reasoning steps from parsed output if provided
        extra_steps = parsed.pop("reasoning_steps", [])
        for i, step_data in enumerate(extra_steps):
            reasoning_steps.append(ReasoningStep(
                step=len(reasoning_steps) + 1,
                action=step_data.get("action", "synthesis"),
                thought=step_data.get("thought", ""),
                data=step_data.get("data"),
                confidence=step_data.get("confidence", 0.7),
                source_ids=step_data.get("source_ids", []),
            ))

        # Final synthesis step
        elapsed = int((time.perf_counter() - timer) * 1000)
        reasoning_steps.append(ReasoningStep(
            step=len(reasoning_steps) + 1,
            action="synthesis",
            thought=f"Completed {self.name} in {elapsed}ms",
            confidence=parsed.get("_confidence", 0.7),
        ))
        parsed.pop("_confidence", None)

        # Build artifact
        artifact = ReasoningArtifact(
            artifact_id=f"{self.name}_{run_id}_{round_num}",
            agent=self.name,
            pillar=self.pillar,
            round=round_num,
            reasoning_chain=reasoning_steps,
            output_summary=parsed.get("_summary", f"{self.name} completed"),
            execution_meta={
                "llm_calls": llm_calls,
                "external_searches": external_searches,
                "total_tokens": self._input_tokens + self._output_tokens,
                "execution_time_ms": elapsed,
                "model": "gemini-2.0-flash",
            },
        )
        parsed.pop("_summary", None)

        # Build standard agent output
        agent_output = self._wrap_output(run_id, parsed, execution_time_ms=elapsed)

        return SubAgentOutput(artifact=artifact, agent_output=agent_output)

    def _run_searches(
        self,
        state: dict[str, Any],
        cluster_context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Override in subclasses that use external search (Perplexity).

        Returns search results dict, or None if no search needed.
        """
        return None

    def _enrich_prompt_with_search(self, prompt: str, search_data: dict[str, Any]) -> str:
        """Append search results to the prompt. Override for custom formatting."""
        import json
        return prompt + f"\n\nExternal research data:\n{json.dumps(search_data, indent=2)}"
