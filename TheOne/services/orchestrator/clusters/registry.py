"""Cluster registry — maps pillar names to PillarCluster instances."""
from __future__ import annotations

import os
from typing import Any

from services.orchestrator.clusters.engine import PillarCluster
from services.orchestrator.tools.providers import ProviderClient


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _build_real_clusters(provider: ProviderClient | None = None) -> dict[str, PillarCluster]:
    """Build cluster instances using real sub-agents."""
    from services.orchestrator.agents.sub_agents.market_intelligence import build_mi_cluster
    from services.orchestrator.agents.sub_agents.customer import build_customer_cluster
    from services.orchestrator.agents.sub_agents.positioning_pricing import build_pp_cluster
    from services.orchestrator.agents.sub_agents.go_to_market import build_gtm_cluster
    from services.orchestrator.agents.sub_agents.product_tech import build_pt_cluster
    from services.orchestrator.agents.sub_agents.execution import build_execution_cluster

    p = provider or ProviderClient()
    return {
        "market_intelligence": build_mi_cluster(p),
        "customer": build_customer_cluster(p),
        "positioning_pricing": build_pp_cluster(p),
        "go_to_market": build_gtm_cluster(p),
        "product_tech": build_pt_cluster(p),
        "execution": build_execution_cluster(p),
    }


def _build_stub_clusters() -> dict[str, PillarCluster]:
    """Build cluster instances using stub sub-agents for testing."""
    from services.orchestrator.agents.sub_agents.stubs.mi_stubs import build_mi_stub_cluster
    from services.orchestrator.agents.sub_agents.stubs.customer_stubs import build_customer_stub_cluster
    from services.orchestrator.agents.sub_agents.stubs.pp_stubs import build_pp_stub_cluster
    from services.orchestrator.agents.sub_agents.stubs.gtm_stubs import build_gtm_stub_cluster
    from services.orchestrator.agents.sub_agents.stubs.pt_stubs import build_pt_stub_cluster
    from services.orchestrator.agents.sub_agents.stubs.execution_stubs import build_execution_stub_cluster

    return {
        "market_intelligence": build_mi_stub_cluster(),
        "customer": build_customer_stub_cluster(),
        "positioning_pricing": build_pp_stub_cluster(),
        "go_to_market": build_gtm_stub_cluster(),
        "product_tech": build_pt_stub_cluster(),
        "execution": build_execution_stub_cluster(),
    }


def get_cluster_registry(provider: ProviderClient | None = None) -> dict[str, PillarCluster]:
    """Get the appropriate cluster registry based on provider mode."""
    if _env_bool("GTMGRAPH_USE_REAL_PROVIDERS"):
        return _build_real_clusters(provider)
    return _build_stub_clusters()
