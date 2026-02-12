"""GTMSynthesizer — synthesizes all Go-to-Market cluster outputs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from services.orchestrator.agents.sub_agents.base_sub_agent import BaseSubAgent


class GTMSynthesizer(BaseSubAgent):
    """Synthesizes outputs from ChannelResearcher, MotionDesigner, and
    MessageCrafter into a cohesive pillar summary and graph nodes.

    This is the final sub-agent in the Go-to-Market cluster (step 4/4).
    It always runs, even in feedback rounds.
    """

    name = "gtm_synthesizer"
    pillar = "go_to_market"
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
        constraints = state.get("constraints", {})
        ctx = cluster_context or {}

        channel_output = ctx.get("channel_researcher", {})
        motion_output = ctx.get("motion_designer", {})
        message_output = ctx.get("message_crafter", {})

        prompt = f"""You are a GTM strategist synthesizing the Go-to-Market \
analysis for a product. Combine the outputs from three prior analyses into \
a unified pillar summary and graph node specifications.

## Product
Name: {idea.get('name', '')}
One-liner: {idea.get('one_liner', '')}
Category: {idea.get('category', '')}

## Constraints
Team size: {constraints.get('team_size', '')}
Budget: ${constraints.get('budget_usd_monthly', '')} monthly
Timeline: {constraints.get('timeline_weeks', '')} weeks

## ChannelResearcher Output
Proposals: {json.dumps(channel_output.get('proposals', []), default=str)}
Facts: {json.dumps(channel_output.get('facts', []), default=str)}
Risks: {json.dumps(channel_output.get('risks', []), default=str)}

## MotionDesigner Output
Proposals: {json.dumps(motion_output.get('proposals', []), default=str)}
Facts: {json.dumps(motion_output.get('facts', []), default=str)}
Risks: {json.dumps(motion_output.get('risks', []), default=str)}

## MessageCrafter Output
Facts: {json.dumps(message_output.get('facts', []), default=str)}
Patches: {json.dumps(message_output.get('patches', [])[:3], default=str)}

## Instructions
Synthesize all three outputs into:
1. A concise pillar summary (2-3 sentences) capturing the channel \
strategy, sales motion, and messaging approach
2. Graph nodes representing the key GTM artifacts
3. Identify any internal contradictions (e.g., outbound motion + no \
outbound channels, PLG motion + high-touch pricing)
4. Flag if team/budget constraints conflict with the recommended strategy
5. Generate edges connecting GTM nodes to upstream dependencies

Use stable node IDs from this set:
- gtm.channels — Channel strategy summary
- gtm.motion — Sales motion design
- gtm.messaging — Messaging framework
- gtm.playbook — Tactical GTM playbook
- gtm.summary — Overall GTM synthesis

{f"ORCHESTRATOR FEEDBACK: {feedback}" if feedback else ""}

Return JSON:
{{
  "pillar_summary": "string (2-3 sentence synthesis)",
  "nodes": [
    {{
      "id": "gtm.channels",
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
      "source": "gtm.channels",
      "target": "gtm.motion",
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
  "constraint_conflicts": [
    {{
      "constraint": "string (e.g., 'team_size=2')",
      "conflict": "string (what strategy element conflicts)",
      "severity": "low | medium | high",
      "workaround": "string"
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
        constraint_conflicts = raw.get("constraint_conflicts", [])
        unresolved = raw.get("unresolved_assumptions", [])

        now = datetime.now(timezone.utc).isoformat()

        # Patch pillar summary
        if pillar_summary:
            patches.append({
                "op": "replace",
                "path": "/pillars/go_to_market/summary",
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
                "pillar": "go_to_market",
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
                "path": "/pillars/go_to_market/nodes",
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
                    f"GTM contradiction between {c.get('between', [])}: "
                    f"{c.get('issue', '')}"
                ),
            })

        # Register constraint conflicts as risks
        for cc in constraint_conflicts:
            severity = cc.get("severity", "medium")
            risks.append({
                "type": "constraint_conflict",
                "severity": severity,
                "description": (
                    f"Constraint {cc.get('constraint', '')} conflicts with "
                    f"GTM strategy: {cc.get('conflict', '')}. "
                    f"Workaround: {cc.get('workaround', 'none proposed')}"
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
                f"Go-to-Market synthesis complete: {len(nodes)} graph nodes, "
                f"{len(edges)} edges, {len(contradictions)} contradictions, "
                f"{len(constraint_conflicts)} constraint conflicts"
            ),
            "confidence": 0.8,
            "sources": [],
        })

        reasoning_steps = [
            {
                "action": "synthesis",
                "thought": (
                    f"Synthesized GTM cluster: {len(nodes)} nodes, "
                    f"{len(contradictions)} contradictions, "
                    f"{len(constraint_conflicts)} constraint conflicts"
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
                f"GTM synthesis complete: {pillar_summary[:80]}..."
                if len(pillar_summary) > 80
                else f"GTM synthesis complete: {pillar_summary}"
            ),
        }
