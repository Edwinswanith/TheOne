from __future__ import annotations

import html
from typing import Any

import markdown as md


def render_markdown_export(state: dict[str, Any]) -> str:
    lines: list[str] = []
    idea = state.get("idea", {})

    lines.append(f"# GTMGraph Export: {idea.get('name', 'Untitled')}")
    lines.append("")
    lines.append(f"> {idea.get('one_liner', '')}")
    lines.append("")
    lines.append(f"**Problem:** {idea.get('problem', '')}")
    lines.append(f"**Region:** {idea.get('target_region', '')} | **Category:** {idea.get('category', '')}")
    lines.append("")

    # Constraints
    constraints = state.get("constraints", {})
    lines.append("## Constraints")
    lines.append(f"- Team size: {constraints.get('team_size', '?')}")
    lines.append(f"- Timeline: {constraints.get('timeline_weeks', '?')} weeks")
    lines.append(f"- Budget: ${constraints.get('budget_usd_monthly', 0):,.0f}/mo")
    lines.append(f"- Compliance: {constraints.get('compliance_level', 'none')}")
    lines.append("")

    # Evidence sources
    sources = state.get("evidence", {}).get("sources", [])
    if sources:
        lines.append("## Evidence Sources")
        for src in sources:
            title = src.get("title", "Untitled")
            url = src.get("url", "")
            quality = src.get("quality_score", 0)
            lines.append(f"- [{title}]({url}) (quality: {quality:.0%})")
            for snippet in src.get("snippets", [])[:2]:
                lines.append(f"  > {snippet}")
        lines.append("")

    # Decisions
    lines.append("## Decisions")
    lines.append("")
    for key, decision in state.get("decisions", {}).items():
        selected = decision.get("selected_option_id", "") or "unset"
        recommended = decision.get("recommended_option_id", "")
        override = decision.get("override", {})

        status = "Recommended" if selected == recommended else ("Override" if override.get("is_custom") else "Selected")
        lines.append(f"### {key.replace('_', ' ').title()}")
        lines.append(f"**Selected:** `{selected}` ({status})")

        if override.get("justification"):
            lines.append(f"**Justification:** {override['justification']}")

        options = decision.get("options", [])
        if options:
            lines.append("")
            lines.append("| Option | Description |")
            lines.append("|--------|-------------|")
            for opt in options:
                marker = " *" if opt.get("id") == recommended else ""
                label = opt.get("label", opt.get("id", ""))
                desc = opt.get("description", "")
                lines.append(f"| {label}{marker} | {desc} |")

        # Decision-specific details
        if key == "pricing":
            metric = decision.get("metric", "")
            tiers = decision.get("tiers", [])
            if metric:
                lines.append(f"\n**Pricing metric:** {metric}")
            if tiers:
                lines.append("**Tiers:** " + ", ".join(f"{t.get('name', '')} (${t.get('price', 0)})" for t in tiers))

        if key == "channels":
            primary = decision.get("primary", "")
            secondary = decision.get("secondary", "")
            if primary:
                lines.append(f"\n**Primary channel:** {primary}")
            if secondary:
                lines.append(f"**Secondary channel:** {secondary}")

        if key == "sales_motion":
            motion = decision.get("motion", "")
            if motion:
                lines.append(f"\n**Motion:** {motion}")

        lines.append("")

    # Pillars
    lines.append("## Pillar Summaries")
    pillar_names = {
        "market_intelligence": "Market Intelligence",
        "customer": "Customer",
        "positioning_pricing": "Positioning & Pricing",
        "go_to_market": "Go-to-Market",
        "product_tech": "Product & Tech",
        "execution": "Execution",
    }
    for key, label in pillar_names.items():
        pillar = state.get("pillars", {}).get(key, {})
        summary = pillar.get("summary", "")
        if summary:
            lines.append(f"### {label}")
            lines.append(summary)
            lines.append("")

    # Graph nodes by pillar
    nodes = state.get("graph", {}).get("nodes", [])
    if nodes:
        lines.append("## Graph Nodes")
        for pillar_key, label in pillar_names.items():
            pillar_nodes = [n for n in nodes if n.get("pillar") == pillar_key]
            if pillar_nodes:
                lines.append(f"\n### {label}")
                for node in pillar_nodes:
                    conf = node.get("confidence", 0)
                    lines.append(f"- **{node.get('title', '')}** ({conf:.0%} confidence) — {node.get('status', 'draft')}")
                    assumptions = node.get("assumptions", [])
                    if assumptions:
                        for a in assumptions:
                            lines.append(f"  - Assumption: {a}")
        lines.append("")

    # Risks
    contradictions = state.get("risks", {}).get("contradictions", [])
    high_risk = state.get("risks", {}).get("high_risk_flags", [])
    if contradictions or high_risk:
        lines.append("## Risks")
        for c in contradictions:
            lines.append(f"- [{c.get('severity', '?')}] {c.get('rule_id', '')}: {c.get('message', '')}")
            if c.get("recommended_fix"):
                lines.append(f"  - Fix: {c['recommended_fix']}")
        for r in high_risk:
            lines.append(f"- [{r.get('severity', '?')}] {r.get('rule_id', '')}: {r.get('message', '')}")
        lines.append("")

    # 30-day playbook
    next_actions = state.get("execution", {}).get("next_actions", [])
    if next_actions:
        lines.append("## 30-Day Playbook")
        for action in next_actions:
            if isinstance(action, dict):
                title = action.get("title", "")
                owner = action.get("owner", "")
                week = action.get("week", "")
                lines.append(f"- **Week {week}:** {title} (owner: {owner})")
            else:
                lines.append(f"- {action}")
        lines.append("")

    # Experiments
    experiments = state.get("execution", {}).get("experiments", [])
    if experiments:
        lines.append("## Experiments")
        for exp in experiments:
            if isinstance(exp, dict):
                lines.append(f"- **Hypothesis:** {exp.get('hypothesis', '')}")
                lines.append(f"  - Metric: {exp.get('metric', '')}")
                steps = exp.get("steps", [])
                if steps:
                    lines.append(f"  - Steps: {', '.join(steps)}")
            else:
                lines.append(f"- {exp}")
        lines.append("")

    # Chosen track
    track = state.get("execution", {}).get("chosen_track", "unset")
    if track and track != "unset":
        lines.append(f"## Execution Track: {track.replace('_', ' ').title()}")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by GTMGraph*")

    return "\n".join(lines)


def render_html_export(state: dict[str, Any], markdown_content: str | None = None) -> str:
    raw_md = markdown_content or render_markdown_export(state)
    rendered_html = md.markdown(raw_md, extensions=["tables", "fenced_code"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GTMGraph Export — {html.escape(state.get('idea', {}).get('name', 'Untitled'))}</title>
  <style>
    :root {{
      --paper: #f7f2e8;
      --ink: #1f2328;
      --graphite: #4b5563;
      --sage: #6d8a73;
      --amber: #d58c2f;
    }}
    body {{
      font-family: "Inter", "Segoe UI", sans-serif;
      background: radial-gradient(circle at top right, #efe5d0, var(--paper));
      color: var(--ink);
      margin: 0;
      padding: 2rem;
      line-height: 1.6;
    }}
    .wrap {{
      max-width: 920px;
      margin: 0 auto;
      background: #fffaf2;
      border: 1px solid #e5dcc9;
      border-radius: 12px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
      padding: 2rem 3rem;
    }}
    h1 {{ font-family: "Source Serif 4", Georgia, serif; font-size: 2rem; margin-top: 0; }}
    h2 {{ font-family: "Source Serif 4", Georgia, serif; font-size: 1.4rem; border-bottom: 1px solid #e5dcc9; padding-bottom: 0.3rem; margin-top: 2rem; }}
    h3 {{ font-size: 1.1rem; color: var(--sage); }}
    blockquote {{ border-left: 3px solid var(--sage); padding-left: 1rem; color: var(--graphite); margin: 1rem 0; font-style: italic; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #e5dcc9; padding: 0.5rem 0.75rem; text-align: left; font-size: 0.9rem; }}
    th {{ background: #f0ebe0; font-weight: 600; }}
    code {{ background: #f0ebe0; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.85rem; }}
    a {{ color: var(--sage); }}
    hr {{ border: none; border-top: 1px solid #e5dcc9; margin: 2rem 0; }}
    ul {{ padding-left: 1.5rem; }}
    li {{ margin-bottom: 0.3rem; }}
  </style>
</head>
<body>
  <div class="wrap">
    {rendered_html}
  </div>
</body>
</html>
"""
