"""Product & Tech cluster sub-agents."""
from services.orchestrator.agents.sub_agents.product_tech.feature_scoper import FeatureScoper
from services.orchestrator.agents.sub_agents.product_tech.feasibility_checker import FeasibilityChecker
from services.orchestrator.agents.sub_agents.product_tech.pt_synthesizer import PTSynthesizer
from services.orchestrator.clusters.engine import PillarCluster
from services.orchestrator.tools.providers import ProviderClient


def build_pt_cluster(provider: ProviderClient | None = None) -> PillarCluster:
    p = provider or ProviderClient()
    return PillarCluster("product_tech", [
        FeatureScoper(p),
        FeasibilityChecker(p),
        PTSynthesizer(p),
    ])
