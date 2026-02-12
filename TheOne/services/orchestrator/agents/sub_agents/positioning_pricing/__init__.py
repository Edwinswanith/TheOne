"""Positioning & Pricing cluster sub-agents."""
from services.orchestrator.agents.sub_agents.positioning_pricing.category_framer import CategoryFramer
from services.orchestrator.agents.sub_agents.positioning_pricing.wedge_builder import WedgeBuilder
from services.orchestrator.agents.sub_agents.positioning_pricing.price_modeler import PriceModeler
from services.orchestrator.agents.sub_agents.positioning_pricing.pp_synthesizer import PPSynthesizer
from services.orchestrator.clusters.engine import PillarCluster
from services.orchestrator.tools.providers import ProviderClient


def build_pp_cluster(provider: ProviderClient | None = None) -> PillarCluster:
    p = provider or ProviderClient()
    return PillarCluster("positioning_pricing", [
        CategoryFramer(p),
        WedgeBuilder(p),
        PriceModeler(p),
        PPSynthesizer(p),
    ])
