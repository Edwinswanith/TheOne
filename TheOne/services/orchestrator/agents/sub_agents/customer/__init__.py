"""Customer cluster sub-agents."""
from services.orchestrator.agents.sub_agents.customer.icp_researcher import ICPResearcher
from services.orchestrator.agents.sub_agents.customer.buyer_journey_mapper import BuyerJourneyMapper
from services.orchestrator.agents.sub_agents.customer.objection_analyst import ObjectionAnalyst
from services.orchestrator.agents.sub_agents.customer.customer_synthesizer import CustomerSynthesizer
from services.orchestrator.clusters.engine import PillarCluster
from services.orchestrator.tools.providers import ProviderClient


def build_customer_cluster(provider: ProviderClient | None = None) -> PillarCluster:
    p = provider or ProviderClient()
    return PillarCluster("customer", [
        ICPResearcher(p),
        BuyerJourneyMapper(p),
        ObjectionAnalyst(p),
        CustomerSynthesizer(p),
    ])
