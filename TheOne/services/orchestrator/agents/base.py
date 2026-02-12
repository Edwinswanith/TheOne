"""Base agent class for all real (LLM-powered) agents."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from services.orchestrator.tools.providers import ProviderClient


class BaseAgent(ABC):
    """Abstract base for LLM-powered agents.

    Subclasses implement `build_prompt()` and `parse_response()`.
    The base class provides `run()` which orchestrates prompt → LLM → parse → AgentOutput.
    """

    name: str = ""
    version: str = "1.0.0"
    pillar: str = ""

    def __init__(self, provider: ProviderClient | None = None) -> None:
        self.provider = provider or ProviderClient()
        self._input_tokens = 0
        self._output_tokens = 0

    @abstractmethod
    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Return the prompt string to send to the LLM."""

    @abstractmethod
    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Parse LLM JSON response into an AgentOutput dict."""

    def run(
        self, run_id: str, state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Execute the agent: build prompt → call LLM → parse → wrap output."""
        timer = time.perf_counter()
        self._input_tokens = 0
        self._output_tokens = 0
        prompt = self.build_prompt(state, changed_decision)
        raw = self._call_llm(prompt)
        parsed = self.parse_response(raw, state, changed_decision)
        elapsed = int((time.perf_counter() - timer) * 1000)
        return self._wrap_output(run_id, parsed, execution_time_ms=elapsed)

    def _call_llm(self, prompt: str, retries: int = 3) -> dict[str, Any]:
        """Call Gemini with retry and backoff."""
        last_err: Exception | None = None
        for attempt in range(retries):
            try:
                result = self.provider._gemini_json(prompt)
                # Rough token estimate: ~4 chars per token
                self._input_tokens += len(prompt) // 4
                self._output_tokens += len(str(result)) // 4
                return result
            except Exception as exc:
                last_err = exc
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # 1s, 2s, 4s
        raise RuntimeError(f"LLM call failed after {retries} retries: {last_err}") from last_err

    def _call_perplexity(self, prompt: str, retries: int = 3) -> dict[str, Any]:
        """Call Perplexity with retry and backoff."""
        last_err: Exception | None = None
        for attempt in range(retries):
            try:
                result = self.provider._perplexity_json(prompt)
                self._input_tokens += len(prompt) // 4
                self._output_tokens += len(str(result)) // 4
                return result
            except Exception as exc:
                last_err = exc
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"Perplexity call failed after {retries} retries: {last_err}") from last_err

    def _wrap_output(
        self, run_id: str, parsed: dict[str, Any], execution_time_ms: int = 0
    ) -> dict[str, Any]:
        """Wrap parsed result into the standard AgentOutput schema."""
        return {
            "agent": self.name,
            "agent_version": self.version,
            "pillar": self.pillar,
            "run_id": run_id,
            "produced_at": datetime.now(timezone.utc).isoformat(),
            "patches": parsed.get("patches", []),
            "proposals": parsed.get("proposals", []),
            "facts": parsed.get("facts", []),
            "assumptions": parsed.get("assumptions", []),
            "risks": parsed.get("risks", []),
            "required_inputs": parsed.get("required_inputs", []),
            "node_updates": parsed.get("node_updates", []),
            "sources": parsed.get("sources", []),
            "citations": parsed.get("citations", []),
            "execution_time_ms": execution_time_ms,
            "token_usage": {
                "input_tokens": self._input_tokens,
                "output_tokens": self._output_tokens,
                "model": "gemini-2.0-flash",
            },
        }

    @staticmethod
    def meta(
        source_type: str = "inference",
        confidence: float = 0.7,
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """Helper to create patch metadata."""
        return {
            "source_type": source_type,
            "confidence": confidence,
            "sources": sources or [],
        }
