"""src.teleon.stateful_swarms — the local-first STATEFUL-SWARM runner implementations (Teleon-owned).

A stateful swarm runs many BOUNDED workers against ONE shared, append-only, provenance-tracked blackboard so the
workers build persistent typed source-backed STATE instead of re-reading docs at every handoff. The deterministic
OFFLINE :class:`local_swarm.LocalStatefulSwarm` (``swarm.local_stub@v1``) is the correctness invariant + the
local-first golden path for the :class:`~src.teleon.ports.stateful_swarm_provider.StatefulSwarmProviderPort`.
External/hosted swarm runners (e.g. Irys Stateful Swarms) are CANDIDATES behind the same port — never
imported/executed here.

A swarm run produces analytical WORKING STATE, never served truth: every entry + the run envelope carry
``serves_truth=False``; Teleon RUNS the swarm, Baltor GOVERNS what (if anything) becomes truth. Held-out / minority
/ stale items are PRESERVED as warnings, never merged into the served answer. Imports only the stdlib + the Teleon
blackboard provider + Teleon id helpers — never Baltor. Deterministic when ``now`` is injected.
"""
from src.teleon.stateful_swarms.local_swarm import (
    LOCAL_SWARM_PROVIDER_ID,
    LocalStatefulSwarm,
)

__all__ = [
    "LocalStatefulSwarm",
    "LOCAL_SWARM_PROVIDER_ID",
]
