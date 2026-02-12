"""PPSynthesizer — synthesizes all Positioning & Pricing cluster outputs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class PPSynthesizer(BaseSubAgent):
    """Synthesizes outputs from CategoryFramer, WedgeBuilder, and PriceModeler
    into a cohesive pillar summary and graph nodes.

    This is the final sub-agent in the Positioning & Pricing cluster (step 4/4).
    It always runs, even in feedback rounds.
    """

    name = "pp_synthesizer"
    pillar = "positioning_pricing"
    step_number = 4
    total_steps = 4
    uses_external_search = False

    def build_prompt(
        self,
        state: dict[str, Any],
        changed_decision: str | None = None,
        cluster_context: dict[str, Any] | None = None,
        feedback: Any | None = None,
    ) -> str:
        idea = state.get("idea", {})
        ctx = cluster_context or {}

        framer_output = ctx.get("category_framer", {})
        wedge_output = ctx.get("wedge_builder", {})
        price_output = ctx.get("price_modeler", {})

        prompt = f"""You are a GTM strategist synthesizing the Positioning & \
Pricing analysis for a product. Combine the outputs from three prior \
analyses into a unified pillar summary and graph node specifications.

## Product
Name: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Category: {idea.get('category', '')}

## CategoryFramer Output
Proposals: {json.dumps(framer_output.get('proposals', []), default=str)}
Facts: {json.dumps(framer_output.get('facts', []), default=str)}
Patches: {json.dumps(framer_output.get('patches', [])[:3], default=str)}

## WedgeBuilder Output
Facts: {json.dumps(wedge_output.get('facts', []), default=str)}
Risks: {json.dumps(wedge_output.get('risks', []), default=str)}
Patches: {json.dumps(wedge_output.get('patches', [])[:3], default=str)}

## PriceModeler Output
Proposals: {json.dumps(price_output.get('proposals', []), default=str)}
Facts: {json.dumps(price_output.get('facts', []), default=str)}
Patches: {json.dumps(price_output.get('patches', [])[:3], default=str)}

## Instructions
Synthesize all three outputs into:
1. A concise pillar summary (2-3 sentences) capturing the positioning \
strategy, competitive wedge, and pricing approach
2. Graph nodes representing the key Positioning & Pricing artifacts
3. Identify any internal contradictions between sub-agent outputs
4. Flag unresolved assumptions that need validation

Use stable node IDs from this set:
- positioning.framework — Category positioning summary
- positioning.wedge — Competitive entry wedge
- pricing.metric — Value metric and strategy
- pricing.tiers — Tier structure
- pp.summary — Overall P&P synthesis

{f"ORCHESTRATOR FEEDBACK: {feedback}" if feedback else ""}

Return JSON:
{{
  "pillar_summary": "string (2-3 sentence synthesis)",
  "nodes": [
    {{
      "id": "positioning.framework",
      "title": "string",
      "content": {{"key": "value pairs with node-specific data"}},
      "assumptions": ["string"],
      "confidence": 0.8,
      "evidence_refs": ["string"],
      "dependencies": ["string (node IDs this depends on)"],
      "actions": ["string (recommended next steps)"]
    }}
  ],
  "edges": [
    {{
      "source": "positioning.framework",
      "target": "pricing.metric",
      "kind": "informs | constrains | validates"
    }}
  ],
  "contradictions": [
    {{
      "between": ["sub_agent_1", "sub_agent_2"],
      "issue": "string",
      "severity": "low | medium | high"
    }}
  ],
  "unresolved_assumptions": ["string"]
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
        facts: list[dict[str, Any]] = []
        assumptions: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []
        node_updates: list[dict[str, Any]] = []

        pillar_summary = raw.get("pillar_summary", "")
        nodes = raw.get("nodes", [])
        edges = raw.get("edges", [])
        contradictions = raw.get("contradictions", [])
        unresolved = raw.get("unresolved_assumptions", [])

        now = datetime.now(timezone.utc).isoformat()

        # Patch pillar summary
        if pillar_summary:
            patches.append({
                "op": "replace",
                "path": "/pillars/positioning_pricing/summary",
                "value": pillar_summary,
                "meta": self.meta("inference", 0.8),
            })

        # Build graph node updates
        node_ids = []
        for node in nodes:
            node_id = node.get("id", "")
            if not node_id:
                continue
            node_ids.append(node_id)

            node_updates.append({
                "id": node_id,
                "title": node.get("title", node_id),
                "pillar": "positioning_pricing",
                "type": "analysis",
                "content": node.get("content", {}),
                "assumptions": node.get("assumptions", []),
                "confidence": node.get("confidence", 0.7),
                "evidence_refs": node.get("evidence_refs", []),
                "dependencies": node.get("dependencies", []),
                "status": "draft",
                "actions": node.get("actions", []),
                "updated_at": now,
            })

        # Patch pillar node list
        if node_ids:
            patches.append({
                "op": "replace",
                "path": "/pillars/positioning_pricing/nodes",
                "value": node_ids,
                "meta": self.meta("inference", 0.8),
            })

        # Add graph edges
        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            if source and target:
                patches.append({
                    "op": "add",
                    "path": "/graph/edges/-",
                    "value": {
                        "id": f"{source}_to_{target}",
                        "source": source,
                        "target": target,
                        "kind": edge.get("kind", "informs"),
                    },
                    "meta": self.meta("inference", 0.8),
                })

        # Register contradictions as risks
        for c in contradictions:
            risks.append({
                "type": "internal_contradiction",
                "severity": c.get("severity", "medium"),
                "description": (
                    f"Contradiction between {c.get('between', [])}: "
                    f"{c.get('issue', '')}"
                ),
            })

        # Register unresolved assumptions
        for ua in unresolved:
            assumptions.append({
                "claim": ua,
                "confidence": 0.5,
            })

        facts.append({
            "claim": (
                f"Positioning & Pricing synthesis complete: "
                f"{len(nodes)} graph nodes, {len(edges)} edges, "
                f"{len(contradictions)} contradictions"
            ),
            "confidence": 0.8,
            "sources": [],
        })

        reasoning_steps = [
            {
                "action": "synthesis",
                "thought": (
                    f"Synthesized P&P cluster: {len(nodes)} nodes, "
                    f"{len(contradictions)} contradictions found"
                ),
                "confidence": 0.8,
            },
        ]

        return {
            "patches": patches,
            "proposals": [],
            "facts": facts,
            "assumptions": assumptions,
            "risks": risks,
            "required_inputs": [],
            "node_updates": node_updates,
            "reasoning_steps": reasoning_steps,
            "_confidence": 0.8,
            "_summary": (
                f"P&P synthesis complete: {pillar_summary[:80]}..."
                if len(pillar_summary) > 80
                else f"P&P synthesis complete: {pillar_summary}"
            ),
        }
