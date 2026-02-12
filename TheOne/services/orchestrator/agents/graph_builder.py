"""Graph builder agent — constructs graph nodes and groups from state."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.orchestrator.agents.base import BaseAgent


class GraphBuilderAgent(BaseAgent):
    """Builds graph nodes and groups from canonical state without LLM calls."""

    name = "graph_builder"

    def build_prompt(self, state: dict[str, Any], changed_decision: str | None = None) -> str:
        """Not used - graph builder doesn't call LLM."""
        return ""

    def parse_response(
        self, raw: dict[str, Any], state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Not used - graph builder doesn't call LLM."""
        return {}

    @staticmethod
    def _decision_to_pillar(decision_key: str) -> str:
        """Map decision keys to their owning pillar."""
        mapping = {
            "icp": "customer",
            "positioning": "positioning_pricing",
            "pricing": "positioning_pricing",
            "channels": "go_to_market",
            "sales_motion": "go_to_market",
        }
        return mapping.get(decision_key, "market_intelligence")

    def run(
        self, run_id: str, state: dict[str, Any], changed_decision: str | None = None
    ) -> dict[str, Any]:
        """Override run to build graph directly from state without LLM."""
        nodes = []
        groups = []
        edges = []
        patches = []

        decisions = state.get("decisions", {})
        pillars = state.get("pillars", {})
        execution = state.get("execution", {})
        evidence = state.get("evidence", {})
        constraints = state.get("constraints", {})
        competitors = evidence.get("competitors", [])
        pricing_anchors = evidence.get("pricing_anchors", [])
        now = datetime.now(timezone.utc).isoformat()

        # Decision-specific content enrichment
        decision_content: dict[str, dict] = {}
        for decision_key, decision_data in decisions.items():
            selected_option_id = decision_data.get("selected_option_id", "")
            options = decision_data.get("options", [])
            selected_option = next(
                (opt for opt in options if opt.get("id") == selected_option_id), None
            )
            if not selected_option:
                continue

            label = selected_option.get("label", "")
            description = selected_option.get("description", "")
            rationale = selected_option.get("rationale", "")
            confidence = selected_option.get("confidence", 0.7)
            alt_count = len(options) - 1

            content: dict = {
                "summary": f"{label}: {description}" if description else label,
                "selected": label,
                "description": description,
                "rationale": rationale or f"Selected from {alt_count + 1} options based on evidence.",
                "alternatives_count": alt_count,
            }

            # Add decision-specific extra fields
            if decision_key == "icp":
                profile = decision_data.get("profile", {})
                content.update({
                    "buyer_role": profile.get("buyer_role", ""),
                    "company_size": profile.get("company_size", ""),
                    "trigger_event": profile.get("trigger_event", ""),
                })
            elif decision_key == "pricing":
                tiers = decision_data.get("tiers", [])
                content.update({
                    "metric": decision_data.get("metric", ""),
                    "price_to_test": decision_data.get("price_to_test", ""),
                    "tiers": tiers,
                    "anchors": pricing_anchors[:3] if pricing_anchors else [],
                })
            elif decision_key == "positioning":
                frame = decision_data.get("frame", {})
                content.update({
                    "category": frame.get("category", ""),
                    "wedge": frame.get("wedge", ""),
                    "value_prop": frame.get("value_prop", ""),
                })
            elif decision_key == "channels":
                content.update({
                    "channel": decision_data.get("primary", ""),
                    "secondary": decision_data.get("secondary", ""),
                })
            elif decision_key == "sales_motion":
                content.update({
                    "motion": decision_data.get("motion", ""),
                })

            decision_content[decision_key] = content

            node_id = f"decision.{decision_key}"
            evidence_refs = []
            if decision_key in ("icp", "positioning") and competitors:
                evidence_refs = ["src_comp_1"]
            elif decision_key == "pricing" and pricing_anchors:
                evidence_refs = [a.get("source_id", "src_pricing_1") for a in pricing_anchors[:2]]

            nodes.append({
                "id": node_id,
                "title": f"{decision_key.replace('_', ' ').title()} Decision",
                "pillar": self._decision_to_pillar(decision_key),
                "type": "decision",
                "content": content,
                "assumptions": [],
                "confidence": confidence,
                "evidence_refs": evidence_refs,
                "dependencies": [],
                "status": "final",
                "actions": [],
                "updated_at": now,
            })

        # Build nodes from pillars with enriched content
        pillar_map = {
            "market_intelligence": "market_intelligence",
            "customer": "customer",
            "positioning_pricing": "positioning_pricing",
            "go_to_market": "go_to_market",
            "product_tech": "product_tech",
            "execution": "execution",
        }

        for pillar_key, pillar_name in pillar_map.items():
            pillar_data = pillars.get(pillar_key, {})
            pillar_nodes = pillar_data.get("nodes", [])
            pillar_summary = pillar_data.get("summary", "")

            for node_id in pillar_nodes:
                node_title = node_id.split(".")[-1].replace("_", " ").title()
                content = {"summary": pillar_summary}

                # Add pillar-specific enrichments
                if pillar_key == "product_tech":
                    content["mvp_features"] = pillar_data.get("mvp_features", [])
                    content["roadmap_phases"] = pillar_data.get("roadmap_phases", [])
                    if "security" in node_id:
                        content["plan"] = pillar_data.get("security_plan", "")
                        content["compliance_level"] = constraints.get("compliance_level", "none")
                elif pillar_key == "execution":
                    team_plan = pillar_data.get("team_plan", {})
                    if "team" in node_id:
                        content["team_size"] = constraints.get("team_size", 1)
                        content["budget"] = constraints.get("budget_usd_monthly", 0)
                        content["summary"] = team_plan.get("summary", pillar_summary)
                    elif "runway" in node_id or "budget" in node_id:
                        content["budget"] = constraints.get("budget_usd_monthly", 0)

                nodes.append({
                    "id": node_id,
                    "title": node_title,
                    "pillar": pillar_name,
                    "type": "strategy",
                    "content": content,
                    "assumptions": [],
                    "confidence": 0.7,
                    "evidence_refs": [],
                    "dependencies": [],
                    "status": "draft",
                    "actions": [],
                    "updated_at": now,
                })

        # Build nodes from execution with rich content
        next_actions = execution.get("next_actions", [])
        experiments = execution.get("experiments", [])
        for idx, action in enumerate(next_actions[:5]):
            action_id = action.get("id", f"action_{idx}")
            node_id = f"execution.action.{action_id}"
            title = action.get("title", "")
            owner = action.get("owner", "")
            week = action.get("week", "")
            nodes.append({
                "id": node_id,
                "title": title or f"Action {idx + 1}",
                "pillar": "execution",
                "type": "action",
                "content": {
                    "summary": f"{title} — owned by {owner}, week {week}." if title else "",
                    "description": action.get("description", title),
                    "owner": owner,
                    "timeline": f"Week {week}" if week else "",
                    "success_metric": experiments[0].get("metric", "") if experiments else "",
                },
                "assumptions": [],
                "confidence": 0.8,
                "evidence_refs": [],
                "dependencies": action.get("dependencies", []),
                "status": "needs-input",
                "actions": [action_id],
                "updated_at": now,
            })

        # Create groups by pillar
        pillar_groups = {
            "market_intelligence": {"id": "group.market_intelligence", "title": "Market Intelligence", "node_ids": []},
            "customer": {"id": "group.customer", "title": "Customer", "node_ids": []},
            "positioning_pricing": {"id": "group.positioning_pricing", "title": "Positioning & Pricing", "node_ids": []},
            "go_to_market": {"id": "group.go_to_market", "title": "Go-to-Market", "node_ids": []},
            "product_tech": {"id": "group.product_tech", "title": "Product & Tech", "node_ids": []},
            "execution": {"id": "group.execution", "title": "Execution", "node_ids": []},
        }

        for node in nodes:
            pillar = node.get("pillar", "")
            if pillar in pillar_groups:
                pillar_groups[pillar]["node_ids"].append(node["id"])

        groups = [group for group in pillar_groups.values() if group["node_ids"]]

        # Create patches
        patches.append({
            "op": "replace",
            "path": "/graph/nodes",
            "value": nodes,
            "meta": self.meta("inference", 1.0, [])
        })

        patches.append({
            "op": "replace",
            "path": "/graph/groups",
            "value": groups,
            "meta": self.meta("inference", 1.0, [])
        })

        # Edges can be added here based on dependencies
        patches.append({
            "op": "replace",
            "path": "/graph/edges",
            "value": edges,
            "meta": self.meta("inference", 1.0, [])
        })

        parsed = {
            "patches": patches,
            "proposals": [],
            "facts": [{
                "claim": f"Generated {len(nodes)} graph nodes across {len(groups)} pillars",
                "confidence": 1.0,
                "sources": []
            }],
            "assumptions": [],
            "risks": [],
            "required_inputs": [],
            "node_updates": []
        }

        return self._wrap_output(run_id, parsed)
