"""ChannelResearcher — scores channels using industry channel map from Perplexity."""
from __future__ import annotations

import json
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class ChannelResearcher(BaseSubAgent):
    """Researches and scores go-to-market channels using real industry data.

    This sub-agent uses external search (Perplexity) to build an Industry
    Channel Map BEFORE scoring. Industry-incompatible channels get a score
    ceiling of 3/10; industry-standard channels get a score floor of 7/10.

    Fixes Issue 3: channel scoring without industry context.
    """

    name = "channel_researcher"
    pillar = "go_to_market"
    step_number = 1
    total_steps = 4
    uses_external_search = True

    def _run_searches(
        self,
        state: dict[str, Any],
        cluster_context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """MANDATORY: Build Industry Channel Map via Perplexity before scoring.

        Calls self.provider.search_industry_channels(domain, category) to
        retrieve real industry channel patterns.
        """
        idea = state.get("idea", {})
        domain = idea.get("domain", idea.get("name", "software"))
        category = idea.get("category", "b2b_saas")

        try:
            channel_data = self.provider.search_industry_channels(domain, category)
            return channel_data
        except Exception:
            # Graceful degradation: return None and rely on evidence signals
            return None

    def _enrich_prompt_with_search(
        self, prompt: str, search_data: dict[str, Any]
    ) -> str:
        """Format industry channel data for prompt injection."""
        section = "\n\n## Industry Channel Map (from external research)\n"
        section += f"Primary channels: {json.dumps(search_data.get('primary_channels', []))}\n"
        section += f"Industry events: {json.dumps(search_data.get('industry_events', []))}\n"
        section += f"Discovery methods: {json.dumps(search_data.get('common_discovery_methods', []))}\n"
        section += f"Trust signals: {json.dumps(search_data.get('trust_signals', []))}\n"
        section += f"Community platforms: {json.dumps(search_data.get('community_platforms', []))}\n"
        return prompt + section

    def build_prompt(
        self,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
    ) -> str:
        idea = state.get("idea", {})
        decisions = state.get("decisions", {})
        evidence = state.get("evidence", {})
        constraints = state.get("constraints", {})

        icp_decision = decisions.get("icp", {})
        selected_icp_id = icp_decision.get("selected_option_id", "")
        icp_options = icp_decision.get("options", [])
        selected_icp = next(
            (o for o in icp_options if o.get("id") == selected_icp_id), {}
        )

        channel_signals = evidence.get("channel_signals", [])
        competitors = evidence.get("competitors", [])

        prompt = f"""You are a channel strategy expert with deep knowledge of \
B2B and B2C distribution channels. Score and rank go-to-market channels \
for this product using the Industry Channel Map provided below.

## CRITICAL SCORING RULES
- Channels that are INCOMPATIBLE with this industry get a score CEILING \
of 3/10 (even if generically popular)
- Channels that are STANDARD for this industry get a score FLOOR of 7/10 \
(even if less popular generically)
- The Industry Channel Map from external research MUST be the primary \
factor in scoring, not generic channel popularity

## Product
Name: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Category: {idea.get('category', '')}
Domain: {idea.get('domain', '')}
Region: {idea.get('target_region', '')}

## Selected ICP
ID: {selected_icp_id}
Details: {json.dumps(selected_icp.get('data', selected_icp), default=str)}

## Constraints
Team size: {constraints.get('team_size', '')}
Budget: ${constraints.get('budget_usd_monthly', '')} monthly
Timeline: {constraints.get('timeline_weeks', '')} weeks

## Existing Channel Signals
{json.dumps(channel_signals[:5], default=str)}

## Competitor Channels
{json.dumps([{{"name": c.get("name", ""), "go_to_market": c.get("go_to_market", "")}} for c in competitors[:5]], default=str)}

## Instructions
1. First, classify each potential channel as "industry_standard", \
"industry_compatible", or "industry_incompatible" based on the Industry \
Channel Map
2. Score each channel 1-10 following the ceiling/floor rules above
3. Generate 2-3 channel strategy options (combinations of channels)
4. Each option must include primary channel, secondary channel, and tactics

{f"NOTE: Decision '{changed_decision}' changed. Re-evaluate channels." if changed_decision else ""}
{f"ORCHESTRATOR FEEDBACK: {feedback}" if feedback else ""}

Return JSON:
{{
  "channel_scores": [
    {{
      "channel": "string",
      "score": 8,
      "industry_fit": "industry_standard | industry_compatible | industry_incompatible",
      "rationale": "string",
      "ceiling_applied": false,
      "floor_applied": true
    }}
  ],
  "options": [
    {{
      "id": "chan_1",
      "title": "string (e.g., 'Content + Community')",
      "primary": "string (main channel)",
      "secondary": "string (supporting channel)",
      "primary_channels": ["string"],
      "tactics": ["string (specific actions for each channel)"],
      "estimated_cac": "number (estimated customer acquisition cost)",
      "time_to_traction_weeks": "number",
      "confidence": 0.8,
      "rationale": "string"
    }}
  ],
  "recommended_id": "chan_1",
  "industry_insights": {{
    "dominant_channels": ["string"],
    "emerging_channels": ["string"],
    "declining_channels": ["string"]
  }}
}}"""
        return prompt

    def parse_response(
        self,
        raw: dict[str, Any],
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        patches: list[dict[str, Any]] = []
        proposals: list[dict[str, Any]] = []
        facts: list[dict[str, Any]] = []
        assumptions: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []

        channel_scores = raw.get("channel_scores", [])
        options = raw.get("options", [])
        recommended_id = raw.get("recommended_id", "")
        if not recommended_id and options:
            recommended_id = options[0].get("id", "")
        industry_insights = raw.get("industry_insights", {})

        if options:
            # Build decision options
            decision_options = []
            for opt in options:
                decision_options.append({
                    "id": opt.get("id"),
                    "label": opt.get("title"),
                    "description": opt.get("rationale"),
                    "confidence": opt.get("confidence", 0.7),
                    "data": opt,
                })

            proposals.append({
                "decision_key": "channels",
                "options": decision_options,
                "recommended_option_id": recommended_id,
                "rationale": (
                    "Channel strategy based on industry channel map, "
                    "ICP behavior, and competitor signals"
                ),
            })

            # Patch from recommended option
            rec_opt = next(
                (o for o in options if o.get("id") == recommended_id),
                options[0],
            )

            patches.append({
                "op": "replace",
                "path": "/decisions/channels/primary",
                "value": rec_opt.get("primary", ""),
                "meta": self.meta("evidence", 0.8),
            })

            patches.append({
                "op": "replace",
                "path": "/decisions/channels/secondary",
                "value": rec_opt.get("secondary", ""),
                "meta": self.meta("evidence", 0.75),
            })

            patches.append({
                "op": "replace",
                "path": "/decisions/channels/primary_channels",
                "value": rec_opt.get("primary_channels", []),
                "meta": self.meta("evidence", 0.8),
            })

            facts.append({
                "claim": (
                    f"Identified {len(rec_opt.get('primary_channels', []))} "
                    f"priority channels for {state.get('idea', {}).get('domain', 'this domain')}; "
                    f"primary: {rec_opt.get('primary', '')}"
                ),
                "confidence": 0.8,
                "sources": [],
            })

        # Store channel scores in artifacts for downstream agents
        if channel_scores:
            patches.append({
                "op": "replace",
                "path": "/artifacts/go_to_market/channel_scores",
                "value": channel_scores,
                "meta": self.meta("evidence", 0.8),
            })

            # Validate ceiling/floor rules were applied
            incompatible_high = [
                cs for cs in channel_scores
                if cs.get("industry_fit") == "industry_incompatible"
                and cs.get("score", 0) > 3
            ]
            if incompatible_high:
                risks.append({
                    "type": "channel_scoring_violation",
                    "severity": "medium",
                    "description": (
                        f"Industry-incompatible channels scored above "
                        f"3/10 ceiling: "
                        f"{[c['channel'] for c in incompatible_high]}"
                    ),
                })

        if industry_insights:
            patches.append({
                "op": "replace",
                "path": "/artifacts/go_to_market/industry_insights",
                "value": industry_insights,
                "meta": self.meta("evidence", 0.75),
            })

            dominant = industry_insights.get("dominant_channels", [])
            if dominant:
                facts.append({
                    "claim": (
                        f"Industry-dominant channels identified: "
                        f"{', '.join(dominant[:3])}"
                    ),
                    "confidence": 0.8,
                    "sources": [],
                })

        reasoning_steps = [
            {
                "action": "channel_scoring",
                "thought": (
                    f"Scored {len(channel_scores)} channels using industry "
                    "channel map with ceiling/floor rules"
                ),
                "confidence": 0.8,
            },
            {
                "action": "strategy_generation",
                "thought": (
                    f"Generated {len(options)} channel strategy options"
                ),
                "confidence": 0.75,
            },
        ]

        return {
            "patches": patches,
            "proposals": proposals,
            "facts": facts,
            "assumptions": assumptions,
            "risks": risks,
            "required_inputs": [],
            "node_updates": [],
            "reasoning_steps": reasoning_steps,
            "_confidence": 0.8,
            "_summary": (
                f"Channel research complete: {len(channel_scores)} channels "
                f"scored, {len(options)} strategies proposed"
            ),
        }
