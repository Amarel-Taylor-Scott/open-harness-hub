"""src.baltor.teleon_client — Baltor's TENANT client for the Teleon runtime (migration step 4, FINAL).

Baltor is a tenant of Teleon. Rather than reaching into Teleon's internal module layout, Baltor calls
Teleon through ONE versioned client surface (`TeleonClient`) with a graceful, offline-first LOCAL fallback.
This makes the two **separable** (portfolio law: same region/private network, but a versioned API + graceful
local fallback) while keeping the dependency direction legal: the client lives in Baltor and imports
``src.teleon`` (Baltor → Teleon is allowed; Teleon never imports Baltor).

Every call returns an inspectable envelope (capability · contract_version · served_by · fallback · result) —
a receipt of WHICH backend served it. Capability results are deterministic governance outputs (evidence); the
client never auto-serves model/LLM output as truth.
"""
from __future__ import annotations

from .client import CLIENT_CONTRACT_VERSION, TeleonClient, capabilities

__all__ = ["TeleonClient", "CLIENT_CONTRACT_VERSION", "capabilities"]
