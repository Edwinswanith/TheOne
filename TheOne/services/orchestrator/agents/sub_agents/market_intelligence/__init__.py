"""Market Intelligence cluster sub-agents."""
from services.orchestrator.agents.sub_agents.market_intelligence.market_scanner import MarketScanner
from services.orchestrator.agents.sub_agents.market_intelligence.competitor_deep_dive import CompetitorDeepDive
from services.orchestrator.agents.sub_agents.market_intelligence.weakness_miner import WeaknessMiner
from services.orchestrator.agents.sub_agents.market_intelligence.mi_synthesizer import MISynthesizer
from services.orchestrator.clusters.engine import PillarCluster
from services.orchestrator.tools.providers import ProviderClient


def build_mi_cluster(provider: ProviderClient | None = None) -> PillarCluster:
    p = provider or ProviderClient()
    return PillarCluster("market_intelligence", [
        MarketScanner(p),
        CompetitorDeepDive(p),
        WeaknessMiner(p),
        MISynthesizer(p),
    ])
