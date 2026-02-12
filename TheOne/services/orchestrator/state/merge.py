from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from services.orchestrator.state.default_state import utc_now_iso
from services.orchestrator.tools.evidence import dedupe_sources

PATCH_ORDER = ["/evidence", "/decisions", "/pillars", "/graph", "/execution", "/telemetry", "/artifacts"]


@dataclass
class MergeWarning:
    code: str
    message: str
    path: str
    agent: str


def merge_agent_outputs(state: dict[str, Any], outputs: list[dict[str, Any]]) -> tuple[dict[str, Any], list[MergeWarning]]:
    merged = deepcopy(state)
    warnings: list[MergeWarning] = []

    for output in outputs:
        agent = output.get("agent", "unknown")
        _ingest_facts_and_assumptions(merged, output, agent)
        _apply_proposals(merged, output.get("proposals", []), agent)

    all_patches: list[tuple[str, dict[str, Any]]] = []
    for output in outputs:
        agent = output.get("agent", "unknown")
        for patch in output.get("patches", []):
            all_patches.append((agent, patch))

    all_patches.sort(key=lambda pair: _patch_rank(pair[1].get("path", "")))
    seen_updates: dict[str, dict[str, Any]] = {}

    for agent, patch in all_patches:
        path = patch["path"]
        value = patch.get("value")
        meta = dict(patch.get("meta", {}))

        if _is_decision_selection_path(path) and agent != "orchestrator":
            warnings.append(
                MergeWarning(
                    code="decision_ownership_violation",
                    message="Only orchestrator can set selected_option_id",
                    path=path,
                    agent=agent,
                )
            )
            merged["telemetry"]["errors"].append(
                {
                    "component": "merge",
                    "code": "decision_ownership_violation",
                    "path": path,
                    "agent": agent,
                    "message": "Only orchestrator can write decisions.*.selected_option_id",
                }
            )
            continue

        if meta.get("source_type") == "evidence" and not meta.get("sources"):
            meta["source_type"] = "assumption"
            meta["confidence"] = min(float(meta.get("confidence", 0.6)), 0.6)
            merged["telemetry"]["errors"].append(
                {
                    "component": "merge",
                    "code": "evidence_without_sources",
                    "path": path,
                    "agent": agent,
                    "source_type": "assumption",
                    "confidence": meta["confidence"],
                    "message": "Evidence claim without sources converted to assumption.",
                }
            )
            if _is_critical_path(path):
                merged["risks"]["missing_proof"].append(
                    {
                        "rule_id": "V-EVID-FACT-01",
                        "severity": "high",
                        "message": "Critical decision updated without evidence sources.",
                        "paths": [path],
                    }
                )

        if path.startswith("/evidence/sources"):
            existing = merged["evidence"].get("sources", [])
            merged["evidence"]["sources"] = dedupe_sources(existing + _as_list(value))
            seen_updates[path] = {"value": merged["evidence"]["sources"], "meta": meta}
            continue

        if path.startswith("/graph/nodes"):
            existing_nodes = merged["graph"].get("nodes", [])
            incoming_nodes = _as_list(value)
            merged["graph"]["nodes"] = _upsert_graph_nodes(existing_nodes, incoming_nodes)
            seen_updates[path] = {"value": merged["graph"]["nodes"], "meta": meta}
            continue

        if path.startswith("/graph/groups"):
            merged["graph"]["groups"] = _merge_groups(merged["graph"].get("groups", []), _as_list(value))
            seen_updates[path] = {"value": merged["graph"]["groups"], "meta": meta}
            continue

        previous = seen_updates.get(path)
        if previous and previous["value"] != value:
            chosen, conflict = _resolve_conflict(path, previous, {"value": value, "meta": meta})
            value = chosen["value"]
            if conflict:
                merged["risks"]["contradictions"].append(conflict)

        _apply_patch(merged, patch["op"], path, value)
        seen_updates[path] = {"value": value, "meta": meta}

    merged["meta"]["updated_by"] = "orchestrator"
    merged["meta"]["updated_at"] = utc_now_iso()
    return merged, warnings


def _ingest_facts_and_assumptions(state: dict[str, Any], output: dict[str, Any], agent: str) -> None:
    for fact in output.get("facts", []):
        sources = fact.get("supporting_sources", [])
        confidence = float(fact.get("confidence", 0.6))
        if not sources:
            state["telemetry"]["errors"].append(
                {
                    "component": "merge",
                    "code": "fact_without_source",
                    "agent": agent,
                    "claim": fact.get("claim", ""),
                    "source_type": "assumption",
                    "confidence": min(confidence, 0.6),
                }
            )
            state["risks"]["missing_proof"].append(
                {
                    "rule_id": "V-EVID-FACT-01",
                    "severity": "high",
                    "message": "Fact claim without source was downgraded to assumption.",
                    "paths": ["/facts"],
                    "claim": fact.get("claim", ""),
                }
            )

    for assumption in output.get("assumptions", []):
        experiment = {
            "hypothesis": assumption.get("statement", ""),
            "validation": assumption.get("how_to_validate", ""),
            "confidence": float(assumption.get("confidence", 0.5)),
        }
        if experiment not in state["execution"]["experiments"]:
            state["execution"]["experiments"].append(experiment)


def _apply_proposals(state: dict[str, Any], proposals: list[dict[str, Any]], _: str) -> None:
    for proposal in proposals:
        key = proposal["decision_key"]
        if key not in state["decisions"]:
            continue
        state["decisions"][key]["options"] = proposal.get("options", [])
        state["decisions"][key]["recommended_option_id"] = proposal.get("recommended_option_id", "")


def _patch_rank(path: str) -> int:
    for idx, prefix in enumerate(PATCH_ORDER):
        if path.startswith(prefix):
            return idx
    return len(PATCH_ORDER)


def _is_decision_selection_path(path: str) -> bool:
    return path.startswith("/decisions/") and path.endswith("/selected_option_id")


def _split_pointer(path: str) -> list[str]:
    if not path.startswith("/"):
        raise ValueError(f"invalid json pointer path: {path}")
    return [segment.replace("~1", "/").replace("~0", "~") for segment in path[1:].split("/") if segment]


def _ensure_container(parent: Any, token: str) -> Any:
    if isinstance(parent, dict):
        if token not in parent:
            parent[token] = {}
        return parent[token]
    if isinstance(parent, list):
        index = int(token)
        while len(parent) <= index:
            parent.append({})
        return parent[index]
    raise TypeError("unsupported parent type")


def _apply_patch(state: dict[str, Any], op: str, path: str, value: Any) -> None:
    tokens = _split_pointer(path)
    if not tokens:
        raise ValueError("cannot patch root")

    target = state
    for token in tokens[:-1]:
        target = _ensure_container(target, token)

    leaf = tokens[-1]
    if op in {"add", "replace"}:
        if isinstance(target, dict):
            target[leaf] = value
        else:
            index = int(leaf)
            while len(target) <= index:
                target.append(None)
            target[index] = value
        return

    if op == "remove":
        if isinstance(target, dict):
            target.pop(leaf, None)
        else:
            index = int(leaf)
            if 0 <= index < len(target):
                target.pop(index)
        return

    raise ValueError(f"unsupported patch operation: {op}")


def _resolve_conflict(
    path: str,
    first: dict[str, Any],
    second: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    first_meta = first.get("meta", {})
    second_meta = second.get("meta", {})
    first_source = first_meta.get("source_type", "assumption")
    second_source = second_meta.get("source_type", "assumption")

    if first_source == "evidence" and second_source != "evidence":
        return first, None
    if second_source == "evidence" and first_source != "evidence":
        return second, None

    first_conf = float(first_meta.get("confidence", 0))
    second_conf = float(second_meta.get("confidence", 0))

    if first_source == "evidence" and second_source == "evidence":
        chosen = first if first_conf >= second_conf else second
        contradiction = {
            "rule_id": "V-CONFLICT-EVID",
            "severity": "high",
            "message": "Conflicting evidence updates require user validation.",
            "paths": [path],
            "recommended_fix": "Review alternatives and choose one candidate.",
        }
        return chosen, contradiction

    chosen = first if first_conf >= second_conf else second
    chosen["meta"] = dict(chosen.get("meta", {}))
    chosen["meta"]["source_type"] = "assumption"
    chosen["meta"]["confidence"] = min(float(chosen["meta"].get("confidence", 0.6)), 0.6)
    return chosen, None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _upsert_graph_nodes(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {node["id"]: deepcopy(node) for node in existing if isinstance(node, dict) and node.get("id")}
    for node in incoming:
        if not isinstance(node, dict) or "id" not in node:
            continue
        prior = by_id.get(node["id"])
        if prior and _node_signature(prior) == _node_signature(node):
            node = deepcopy(node)
            node["updated_at"] = prior.get("updated_at", node.get("updated_at"))
        by_id[node["id"]] = deepcopy(node)

    merged_nodes = list(by_id.values())
    merged_nodes.sort(key=lambda node: node["id"])
    return merged_nodes


def _merge_groups(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {group["id"]: deepcopy(group) for group in existing if group.get("id")}
    for group in incoming:
        if not isinstance(group, dict) or "id" not in group:
            continue
        node_ids = list(dict.fromkeys(group.get("node_ids", [])))
        merged = deepcopy(group)
        merged["node_ids"] = node_ids
        by_id[group["id"]] = merged

    result = list(by_id.values())
    result.sort(key=lambda group: group["id"])
    return result


def _node_signature(node: dict[str, Any]) -> tuple[Any, ...]:
    return (
        node.get("title"),
        node.get("pillar"),
        node.get("type"),
        node.get("content"),
        tuple(node.get("assumptions", [])),
        tuple(node.get("evidence_refs", [])),
        tuple(node.get("dependencies", [])),
        node.get("status"),
    )


def _is_critical_path(path: str) -> bool:
    critical_prefixes = [
        "/decisions/icp",
        "/decisions/pricing",
        "/decisions/channels",
        "/decisions/sales_motion",
    ]
    return any(path.startswith(prefix) for prefix in critical_prefixes)


def merge_cluster_outputs(
    state: dict[str, Any],
    cluster_output: Any,
) -> tuple[dict[str, Any], list[MergeWarning]]:
    """Merge outputs from a pillar cluster into canonical state.

    Thin wrapper around merge_agent_outputs that also stores reasoning
    artifacts under state["artifacts"][pillar].

    Args:
        state: Current canonical state.
        cluster_output: ClusterOutput with .pillar, .outputs, .artifacts.

    Returns:
        (updated_state, warnings) tuple.
    """
    # Merge all sub-agent outputs through the standard merge engine
    merged, warnings = merge_agent_outputs(state, cluster_output.outputs)

    # Store artifacts under state["artifacts"][pillar]
    if "artifacts" not in merged:
        merged["artifacts"] = {}
    pillar_artifacts = {}
    for artifact in cluster_output.artifacts:
        pillar_artifacts[artifact.agent] = artifact.to_dict()
    merged["artifacts"][cluster_output.pillar] = pillar_artifacts

    # Update pillar status
    if cluster_output.pillar in merged.get("pillars", {}):
        merged["pillars"][cluster_output.pillar]["status"] = "completed"

    return merged, warnings
