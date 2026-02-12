"""Agent registry — maps agent names to real BaseAgent instances."""
from __future__ import annotations

from typing import Any

from services.orchestrator.agents.base import BaseAgent
from services.orchestrator.agents.evidence_collector import EvidenceCollectorAgent
from services.orchestrator.agents.competitive_teardown_agent import CompetitiveTeardownAgent
from services.orchestrator.agents.icp_agent import ICPAgent
from services.orchestrator.agents.positioning_agent import PositioningAgent
from services.orchestrator.agents.pricing_agent import PricingAgent
from services.orchestrator.agents.channel_agent import ChannelAgent
from services.orchestrator.agents.sales_motion_agent import SalesMotionAgent
from services.orchestrator.agents.product_strategy_agent import ProductStrategyAgent
from services.orchestrator.agents.tech_feasibility_agent import TechFeasibilityAgent
from services.orchestrator.agents.people_cash_agent import PeopleCashAgent
from services.orchestrator.agents.execution_agent import ExecutionAgent
from services.orchestrator.agents.graph_builder import GraphBuilderAgent
from services.orchestrator.agents.validator_agent import ValidatorAgent
from services.orchestrator.tools.providers import ProviderClient

AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "evidence_collector": EvidenceCollectorAgent,
    "competitive_teardown_agent": CompetitiveTeardownAgent,
    "icp_agent": ICPAgent,
    "positioning_agent": PositioningAgent,
    "pricing_agent": PricingAgent,
    "channel_agent": ChannelAgent,
    "sales_motion_agent": SalesMotionAgent,
    "product_strategy_agent": ProductStrategyAgent,
    "tech_feasibility_agent": TechFeasibilityAgent,
    "people_cash_agent": PeopleCashAgent,
    "execution_agent": ExecutionAgent,
    "graph_builder": GraphBuilderAgent,
    "validator_agent": ValidatorAgent,
}


def get_real_agent(agent_name: str, provider: ProviderClient | None = None) -> BaseAgent | None:
    """Get an instantiated real agent by name, or None if not registered."""
    cls = AGENT_REGISTRY.get(agent_name)
    if cls is None:
        return None
    return cls(provider=provider)


def build_agent_output(
    agent: str,
    run_id: str,
    state: dict[str, Any],
    changed_decision: str | None = None,
) -> dict[str, Any]:
    """Dispatcher: if real providers enabled, use real agents; else use stubs.

    Falls back to stub if real agent call fails.
    """
    from services.orchestrator.tools.providers import ProviderClient, _env_bool

    use_real = _env_bool("GTMGRAPH_USE_REAL_PROVIDERS", default=False)

    if use_real:
        provider = ProviderClient()
        real_agent = get_real_agent(agent, provider)
        if real_agent is not None:
            try:
                return real_agent.run(run_id, state, changed_decision)
            except Exception:
                # Fall back to stub on failure
                pass

    # Fixture / fallback mode: use stubs
    from services.orchestrator.agents.stub_agents import build_agent_output as stub_build
    return stub_build(agent, run_id, state, changed_decision)
