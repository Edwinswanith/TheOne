"""Cluster dependency graph for phased execution."""
from __future__ import annotations

# Execution phases: clusters within the same phase can run in parallel.
# Phases execute sequentially.
CLUSTER_PHASES: list[list[str]] = [
    ["market_intelligence"],                     # Phase 1: foundation
    ["customer", "positioning_pricing"],          # Phase 2: parallel
    ["go_to_market", "product_tech"],            # Phase 3: parallel
    ["execution"],                               # Phase 4: depends on all
]

# Which clusters each cluster depends on (inputs it reads from state).
PILLAR_INPUT_DEPENDENCIES: dict[str, set[str]] = {
    "market_intelligence": set(),
    "customer": {"market_intelligence"},
    "positioning_pricing": {"market_intelligence", "customer"},
    "go_to_market": {"customer", "positioning_pricing"},
    "product_tech": {"customer", "positioning_pricing"},
    "execution": {"customer", "positioning_pricing", "go_to_market", "product_tech"},
}

# Reverse map: which downstream clusters are affected when a pillar changes.
PILLAR_DOWNSTREAM: dict[str, set[str]] = {}
for _downstream, _deps in PILLAR_INPUT_DEPENDENCIES.items():
    for _dep in _deps:
        PILLAR_DOWNSTREAM.setdefault(_dep, set()).add(_downstream)


def get_downstream_pillars(pillar: str) -> set[str]:
    """Return all pillars that transitively depend on the given pillar."""
    visited: set[str] = set()
    queue = [pillar]
    while queue:
        current = queue.pop(0)
        for downstream in PILLAR_DOWNSTREAM.get(current, set()):
            if downstream not in visited:
                visited.add(downstream)
                queue.append(downstream)
    return visited
