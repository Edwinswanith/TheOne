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
        # Load .env for API keys (safe: won't override existing env vars)
        try:
            from dotenv import load_dotenv
            _env_path = Path(__file__).resolve().parents[3] / ".env"
            if _env_path.exists():
                load_dotenv(_env_path, override=False)
        except ImportError:
            pass

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
        # Always use real Gemini for context extraction (user-facing interaction)
        if not self.config.google_api_key:
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
        idea = state.get("idea", {})
        constraints = state.get("constraints", {})
        raw_context = state.get("inputs", {}).get("raw_context", "")
        existing_answers = state.get("inputs", {}).get("intake_answers", [])

        # Always use real Gemini for clarification questions (user-facing interaction)
        if not self.config.google_api_key:
            return self._fixture_json("gemini/clarification_questions.json")

        # Build context about what's already known
        already_collected = {}
        for ans in existing_answers:
            already_collected[ans["question_id"]] = ans.get("value", "")

        already_known_text = ""
        if already_collected:
            items = [f"  - {k}: {v}" for k, v in already_collected.items()]
            already_known_text = (
                "\n\nFields already inferred from the user's description "
                "(DO NOT re-ask these, but you may ask follow-up questions that go deeper):\n"
                + "\n".join(items)
            )

        # Determine which required fields still need to be asked
        required_fields = [
            "buyer_role", "company_type", "trigger_event",
            "current_workaround", "measurable_outcome",
        ]
        missing_fields = [f for f in required_fields if f not in already_collected]

        prompt = (
            "You are a GTM strategy expert. Based on the product idea and context below, "
            "generate contextual multiple-choice clarification questions.\n\n"
            f"Product idea: {idea.get('name', '')} — {idea.get('one_liner', '')}\n"
            f"Problem: {idea.get('problem', '')}\n"
            f"Category: {idea.get('category', '')}\n"
            f"Constraints: team_size={constraints.get('team_size', '')}, "
            f"timeline_weeks={constraints.get('timeline_weeks', '')}, "
            f"budget=${constraints.get('budget_usd_monthly', '')}/mo\n"
        )

        if raw_context:
            prompt += f"\nUser's original description:\n\"{raw_context}\"\n"

        prompt += already_known_text

        if missing_fields:
            prompt += (
                f"\n\nYou MUST include questions for these missing required fields: "
                f"{', '.join(missing_fields)}.\n"
            )
        else:
            prompt += (
                "\n\nAll 5 required fields are already collected. "
                "Generate 4-6 contextual follow-up questions to deepen understanding.\n"
            )

        prompt += (
            "\nAdditionally, generate 3-5 contextual follow-up questions that are SPECIFIC "
            "to this particular product idea (not generic). Questions should help refine the "
            "GTM strategy based on the user's specific domain, market, and situation.\n\n"
            "Return JSON with key 'questions' containing an array of question objects. "
            "Each question object must have:\n"
            '- "id": string (use field name for required fields, descriptive id for others)\n'
            '- "question": string\n'
            '- "why": string (brief explanation why this matters)\n'
            '- "category": one of "customer", "market", "value", "product", "execution"\n'
            '- "required": boolean (true only for the 5 required fields)\n'
            '- "allow_custom": true\n'
            '- "custom_placeholder": string\n'
            '- "options": array of 3-4 objects, each with:\n'
            '  - "id": string\n'
            '  - "label": string (concise label)\n'
            '  - "detail": string (1-sentence explanation)\n'
            '  - "recommended": boolean (exactly one true per question)\n'
            '  - "reasoning": string (optional, why this is recommended)\n'
            "\nMake options SPECIFIC to this product idea, not generic."
        )
        return self._gemini_json(prompt)

    def search_market(self, queries: list[str]) -> list[dict[str, Any]]:
        """Run sequential market research queries via Perplexity."""
        if not self.config.use_real_providers:
            return self._fixture_json("perplexity/market_scan.json").get("results", [])

        results = []
        for query in queries[:5]:  # Cap at 5 queries
            result = self._perplexity_json(query)
            results.append(result)
            time.sleep(0.5)  # Rate limit delay
        return results

    def search_competitor_details(self, name: str) -> dict[str, Any]:
        """Search for detailed competitor info via Perplexity."""
        if not self.config.use_real_providers:
            return self._fixture_json("perplexity/competitor_details.json")

        prompt = (
            f"Provide detailed analysis of {name} as a software product. "
            "Return JSON with: positioning, pricing_model, pricing_details, "
            "target_segment, go_to_market, strengths, weaknesses, market_share, "
            "founding_year, funding, key_features."
        )
        return self._perplexity_json(prompt)

    def search_buyer_journey(self, buyer_role: str, company_type: str, domain: str) -> dict[str, Any]:
        """Search for buyer journey patterns via Perplexity."""
        if not self.config.use_real_providers:
            return self._fixture_json("perplexity/buyer_journey.json")

        import datetime
        year = datetime.date.today().year
        prompt = (
            f"How do {buyer_role} at {company_type} evaluate and purchase "
            f"{domain} software in {year}? "
            "Return JSON with: evaluation_stages, key_criteria, typical_timeline, "
            "stakeholders_involved, common_objections, preferred_channels."
        )
        return self._perplexity_json(prompt)

    def search_industry_channels(self, domain: str, category: str) -> dict[str, Any]:
        """Search for industry-specific channel patterns via Perplexity."""
        if not self.config.use_real_providers:
            return self._fixture_json("perplexity/industry_channels.json")

        import datetime
        year = datetime.date.today().year
        prompt = (
            f"How do {domain} companies evaluate and purchase software tools in {year}? "
            f"Category: {category}. "
            "Return JSON with: primary_channels, industry_events, "
            "common_discovery_methods, trust_signals, community_platforms."
        )
        return self._perplexity_json(prompt)

    def search_domain_data_requirements(self, domain: str) -> dict[str, Any]:
        """Search for domain-specific data sources and API requirements via Perplexity."""
        if not self.config.use_real_providers:
            return self._fixture_json("perplexity/domain_data_requirements.json")

        prompt = (
            f"{domain} software required data sources APIs integrations. "
            "Return JSON with: required_data_sources, common_apis, "
            "integration_requirements, data_format_standards."
        )
        return self._perplexity_json(prompt)

    def search_competitor_reviews(self, competitor_names: list[str]) -> dict[str, Any]:
        """Search for competitor reviews and user sentiment via Perplexity."""
        if not self.config.use_real_providers:
            return self._fixture_json("perplexity/competitor_reviews.json")

        names_str = ", ".join(competitor_names[:5])
        prompt = (
            f"Find user reviews, complaints, and sentiment for these software tools: {names_str}. "
            "Return JSON with key 'reviews' mapping each name to "
            '{"sentiment": "positive|mixed|negative", "key_complaints": ["string"], '
            '"key_praises": ["string"], "review_sources": ["string"]}.'
        )
        return self._perplexity_json(prompt)

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
    # Strip markdown code fences
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()

    # Use JSONDecoder.raw_decode for robust single-object extraction
    decoder = json.JSONDecoder()
    start = stripped.find("{")
    if start == -1:
        raise ValueError("No JSON object found in provider response")
    try:
        obj, _ = decoder.raw_decode(stripped, start)
        if isinstance(obj, dict):
            return obj
        raise ValueError("Decoded value is not a JSON object")
    except json.JSONDecodeError:
        # Fallback: try the simple bracket-matching approach
        end = stripped.rfind("}")
        if end == -1:
            raise ValueError("No JSON object found in provider response")
        return json.loads(stripped[start : end + 1])
