from __future__ import annotations

AGENT_SEQUENCE = [
    "evidence_collector",
    "icp_agent",
    "positioning_agent",
    "pricing_agent",
    "channel_strategy_agent",
    "sales_motion_agent",
    "product_strategy_agent",
    "tech_architecture_agent",
    "people_cash_agent",
    "execution_agent",
    "graph_builder",
    "validator_agent",
]

DECISION_DEPENDENCY_GRAPH: dict[str, set[str]] = {
    "icp": {"positioning", "pricing", "channels", "sales_motion"},
    "positioning": {"execution"},
    "pricing": {"execution", "people_and_cash"},
    "channels": {"execution", "sales_motion"},
    "sales_motion": {"execution"},
}

DECISION_TO_AGENTS: dict[str, set[str]] = {
    "icp": {
        "positioning_agent",
        "pricing_agent",
        "channel_strategy_agent",
        "sales_motion_agent",
        "people_cash_agent",
        "execution_agent",
    },
    "positioning": {"execution_agent"},
    "pricing": {"people_cash_agent", "execution_agent"},
    "channels": {"sales_motion_agent", "execution_agent"},
    "sales_motion": {"execution_agent"},
}

ALWAYS_RUN_AGENTS = {"graph_builder", "validator_agent"}


def impacted_decisions(changed_decision: str) -> set[str]:
    if not changed_decision:
        return set()

    impacted = set()
    frontier = [changed_decision]
    while frontier:
        current = frontier.pop()
        for dep in DECISION_DEPENDENCY_GRAPH.get(current, set()):
            if dep not in impacted:
                impacted.add(dep)
                frontier.append(dep)
    return impacted


def impacted_agents(changed_decision: str | None) -> set[str]:
    if not changed_decision:
        return set(AGENT_SEQUENCE)

    impacted = set(DECISION_TO_AGENTS.get(changed_decision, set()))
    for dep in impacted_decisions(changed_decision):
        impacted.update(DECISION_TO_AGENTS.get(dep, set()))
    impacted.update(ALWAYS_RUN_AGENTS)
    return impacted
