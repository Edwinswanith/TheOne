from __future__ import annotations

from typing import Any


def render_markdown_export(state: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# GTMGraph Export: {state['idea']['name']}")
    lines.append("")
    lines.append("## Decisions")
    for key, decision in state["decisions"].items():
        selected = decision.get("selected_option_id", "") or "unset"
        lines.append(f"- **{key}**: `{selected}`")

    lines.append("")
    lines.append("## Risks")
    for contradiction in state["risks"].get("contradictions", []):
        lines.append(f"- [{contradiction['severity']}] {contradiction['rule_id']}: {contradiction['message']}")

    lines.append("")
    lines.append("## Next Actions")
    for action in state["execution"].get("next_actions", []):
        lines.append(f"- {action}")

    if not state["execution"].get("next_actions"):
        lines.append("- No actions generated yet.")

    return "\n".join(lines)


def render_html_export(state: dict[str, Any], markdown: str | None = None) -> str:
    escaped = (markdown or render_markdown_export(state)).replace("&", "&amp;").replace("<", "&lt;")
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>GTMGraph Export</title>
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
    }}
    .wrap {{
      max-width: 920px;
      margin: 0 auto;
      background: #fffaf2;
      border: 1px solid #e5dcc9;
      border-radius: 12px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
      padding: 2rem;
    }}
    pre {{
      white-space: pre-wrap;
      line-height: 1.5;
      color: var(--graphite);
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <pre>{escaped}</pre>
  </div>
</body>
</html>
"""
