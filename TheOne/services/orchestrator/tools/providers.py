from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


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
        self._client = httpx.Client(timeout=60.0)

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

    def generate_intake_questions(self, state: dict[str, Any]) -> dict[str, Any]:
        if not self.config.use_real_providers:
            return self._fixture_json("gemini/intake_questions.json")

        idea = state.get("idea", {})
        constraints = state.get("constraints", {})
        prompt = (
            "You are a GTM strategy expert. Based on the product idea and constraints below, "
            "generate 5 multiple-choice intake questions to refine the go-to-market plan. "
            "Return ONLY a JSON object with exactly these keys: "
            "buyer_role, company_type, trigger_event, current_workaround, measurable_outcome. "
            "Each key maps to an object with: "
            '"question" (string), "options" (array of 3 objects each with "id", "label", "detail", "recommended" boolean — exactly one true per question), '
            '"reasoning" (string explaining why these options were chosen). '
            f"Idea: name={idea.get('name','')}, one_liner={idea.get('one_liner','')}, "
            f"problem={idea.get('problem','')}, region={idea.get('target_region','')}, "
            f"category={idea.get('category','')}. "
            f"Constraints: team_size={constraints.get('team_size','')}, "
            f"timeline_weeks={constraints.get('timeline_weeks','')}, "
            f"budget_usd_monthly={constraints.get('budget_usd_monthly','')}."
        )
        return self._gemini_json(prompt)

    def extract_project_from_context(self, context: str) -> dict[str, Any]:
        if not self.config.use_real_providers:
            return self._fixture_json("gemini/context_extraction.json")

        prompt = (
            "You are a GTM strategy expert. A user has described their product idea in free-form text. "
            "Extract structured information from their description.\n\n"
            f"User input:\n\"{context}\"\n\n"
            "Return ONLY a JSON object with these keys:\n"
            '- "idea": object with keys "name" (string), "one_liner" (string, 1 sentence), '
            '"problem" (string), "target_region" (string, default "US"), '
            '"category" (one of: "b2b_saas", "b2b_services", "b2c")\n'
            '- "constraints": object with keys "team_size" (int, default 2), '
            '"timeline_weeks" (int, default 8), "budget_usd_monthly" (number, default 1000), '
            '"compliance_level" (one of: "none", "low", "medium", "high", default "none")\n'
            '- "pre_collected_fields": object where keys are from [buyer_role, company_type, '
            "trigger_event, current_workaround, measurable_outcome] and values are objects with "
            '"value" (string) and "confidence" (float 0-1). Only include fields you can confidently '
            "infer from the user's text.\n"
            '- "project_name": a short project name (2-4 words)\n\n'
            "Infer as much as possible. For fields you can't determine, use sensible defaults."
        )
        return self._gemini_json(prompt)

    def generate_clarification_questions(self, state: dict[str, Any]) -> dict[str, Any]:
        if not self.config.use_real_providers:
            return self._fixture_json("gemini/clarification_questions.json")

        idea = state.get("idea", {})
        constraints = state.get("constraints", {})
        prompt = (
            "You are a GTM strategy expert. Based on the product idea below, "
            "generate 8-12 multiple-choice clarification questions. "
            "5 required fields (buyer_role, company_type, trigger_event, current_workaround, measurable_outcome) "
            "plus 3-7 contextual questions. Each question has 3-4 options with one marked recommended. "
            "Return JSON with key 'questions' containing array of question objects. "
            f"Idea: name={idea.get('name','')}, one_liner={idea.get('one_liner','')}, "
            f"problem={idea.get('problem','')}, category={idea.get('category','')}. "
            f"Constraints: team_size={constraints.get('team_size','')}, "
            f"timeline_weeks={constraints.get('timeline_weeks','')}."
        )
        return self._gemini_json(prompt)

    def decision_template(self, decision_key: str) -> dict[str, Any]:
        templates = self._fixture_json("gemini/decision_templates.json")
        return templates.get(decision_key, {})

    def _fixture_json(self, relative_path: str) -> dict[str, Any]:
        path = self.config.fixture_root / relative_path
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _perplexity_json(self, prompt: str, retries: int = 3) -> dict[str, Any]:
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
            retries=retries,
        )
        content = response["choices"][0]["message"]["content"]
        return _extract_json_block(content)

    def _gemini_json(self, prompt: str, retries: int = 3) -> dict[str, Any]:
        if not self.config.google_api_key:
            raise RuntimeError("Google_API_Key is required in real provider mode")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            f"?key={self.config.google_api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }
        response = self._http_post_json(url, payload, retries=retries)
        text = response["candidates"][0]["content"]["parts"][0]["text"]
        return _extract_json_block(text)

    def _http_post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
        retries: int = 3,
    ) -> dict[str, Any]:
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        last_err: Exception | None = None
        for attempt in range(retries):
            try:
                resp = self._client.post(url, json=payload, headers=req_headers)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_err = exc
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # 1s, 2s, 4s backoff

        raise RuntimeError(f"HTTP POST to {url} failed after {retries} retries: {last_err}") from last_err


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
