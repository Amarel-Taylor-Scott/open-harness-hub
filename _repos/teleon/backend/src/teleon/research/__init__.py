"""src.teleon.research — Teleon-provided research DRIVERS (the executable side of the research-component catalog).

The OpenHubForAI catalog (_repos/openhubforai/backend/src/openhubforai/research_catalog.py) DECLARES + SELECTS research components; the drivers
that actually run the expensive tiers (the low-cost-LLM-driven browser) live here, on the Teleon side (Teleon may import
the open layer; the open layer imports neither). serves_truth=false.
"""
