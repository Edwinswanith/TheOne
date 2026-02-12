"""Execution cluster sub-agents."""
from services.orchestrator.agents.sub_agents.execution.playbook_builder import PlaybookBuilder
from services.orchestrator.agents.sub_agents.execution.kpi_definer import KPIDefiner
from services.orchestrator.agents.sub_agents.execution.resource_planner import ResourcePlanner
from services.orchestrator.agents.sub_agents.execution.execution_synthesizer import ExecutionSynthesizer
from services.orchestrator.clusters.engine import PillarCluster
from services.orchestrator.tools.providers import ProviderClient


def build_execution_cluster(provider: ProviderClient | None = None) -> PillarCluster:
    p = provider or ProviderClient()
    return PillarCluster("execution", [
        PlaybookBuilder(p),
        KPIDefiner(p),
        ResourcePlanner(p),
        ExecutionSynthesizer(p),
    ])
