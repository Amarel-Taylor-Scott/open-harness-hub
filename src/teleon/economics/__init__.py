"""src.teleon.economics — the economic / market layer (Systems 20–22): the registry is a MARKET, not a static catalog.

- observation_store : System 20 substrate + the telemetry write-back — LIVE economic+quality facets per resource.
- provider_intel    : System 20 — keep economics live (ingest measured runs + a network-gated provider price crawl).
- economic_graph    : the JOIN — capability/model → providers → endpoints → live economics (one traversable graph).
- cost_model        : System 21 — the ONE multi-objective cost function (reuses the user-weighted PreferenceProfile).
- routing_engine    : System 22 — cheapest viable route, secondary-provider arbitrage, reroute-on-change (BGP for compute).

Import submodules directly (e.g. `from src.teleon.economics import routing_engine`); this package __init__ stays minimal
to avoid import-ordering cycles. serves_truth=false throughout: this layer prices/routes computation; truth is Baltor's.
"""

__all__ = ["observation_store", "provider_intel", "economic_graph", "cost_model", "routing_engine"]
