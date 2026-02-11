from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import request


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class ProviderConfig:
    use_real_providers: bool
    fixture_root: Path
    google_api_key: str | None
    perplexity_api_key: str | None


class ProviderClient:
    """Provider client with fixture-backed fallback mode for tests/CI.

    Modes:
    - Fixture mode (default): reads deterministic JSON from fixtures.
    - Real mode (`GTMGRAPH_USE_REAL_PROVIDERS=true`): calls Perplexity + Gemini APIs.
    """

    def __init__(self, config: ProviderConfig | None = None) -> None:
        self.config = config or ProviderConfig(
            use_real_providers=_env_bool("GTMGRAPH_USE_REAL_PROVIDERS", default=False),
            fixture_root=Path(
                os.getenv(
                    "GTMGRAPH_PROVIDER_FIXTURE_ROOT",
                    str(Path(__file__).resolve().parents[1] / "fixtures"),
                )
            ),
            google_api_key=os.getenv("Google_API_Key"),
            perplexity_api_key=os.getenv("perplexity_api_key"),
        )

    def fetch_evidence_bundle(self, state: dict[str, Any]) -> dict[str, Any]:
        if not self.config.use_real_providers:
            return self._fixture_json("perplexity/evidence_bundle.json")

        idea = state.get("idea", {})
        prompt = (
            "Return JSON with keys: sources, competitors, pricing_anchors, messaging_patterns, channel_signals. "
            f"Idea={idea.get('name','')} one_liner={idea.get('one_liner','')} region={idea.get('target_region','')}"
        )
        return self._perplexity_json(prompt)

    def synthesize_evidence(self, evidence_bundle: dict[str, Any]) -> dict[str, Any]:
        if not self.config.use_real_providers:
            return self._fixture_json("gemini/evidence_synthesis.json")

        prompt = (
            "Given evidence JSON, return JSON with keys summary, facts, assumptions."
            f" Evidence={json.dumps(evidence_bundle)}"
        )
        return self._gemini_json(prompt)

    def decision_template(self, decision_key: str) -> dict[str, Any]:
        templates = self._fixture_json("gemini/decision_templates.json")
        return templates.get(decision_key, {})

    def _fixture_json(self, relative_path: str) -> dict[str, Any]:
        path = self.config.fixture_root / relative_path
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _perplexity_json(self, prompt: str) -> dict[str, Any]:
        if not self.config.perplexity_api_key:
            raise RuntimeError("perplexity_api_key is required in real provider mode")

        payload = {
            "model": "sonar-pro",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        response = self._http_post_json(
            "https://api.perplexity.ai/chat/completions",
            payload,
            headers={"Authorization": f"Bearer {self.config.perplexity_api_key}"},
        )
        content = response["choices"][0]["message"]["content"]
        return _extract_json_block(content)

    def _gemini_json(self, prompt: str) -> dict[str, Any]:
        if not self.config.google_api_key:
            raise RuntimeError("Google_API_Key is required in real provider mode")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            f"?key={self.config.google_api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        response = self._http_post_json(url, payload)
        text = response["candidates"][0]["content"]["parts"][0]["text"]
        return _extract_json_block(text)

    def _http_post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
        raw = json.dumps(payload).encode("utf-8")
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        req = request.Request(url, data=raw, headers=req_headers, method="POST")
        with request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
        return json.loads(body)


def _extract_json_block(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in provider response")
    return json.loads(stripped[start : end + 1])
