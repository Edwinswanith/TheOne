"""Go-to-Market cluster sub-agents."""
from services.orchestrator.agents.sub_agents.go_to_market.channel_researcher import ChannelResearcher
from services.orchestrator.agents.sub_agents.go_to_market.motion_designer import MotionDesigner
from services.orchestrator.agents.sub_agents.go_to_market.message_crafter import MessageCrafter
from services.orchestrator.agents.sub_agents.go_to_market.gtm_synthesizer import GTMSynthesizer
from services.orchestrator.clusters.engine import PillarCluster
from services.orchestrator.tools.providers import ProviderClient


def build_gtm_cluster(provider: ProviderClient | None = None) -> PillarCluster:
    p = provider or ProviderClient()
    return PillarCluster("go_to_market", [
        ChannelResearcher(p),
        MotionDesigner(p),
        MessageCrafter(p),
        GTMSynthesizer(p),
    ])
