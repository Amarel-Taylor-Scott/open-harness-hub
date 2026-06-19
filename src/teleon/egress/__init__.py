"""src.teleon.egress — Teleon-owned outbound-traffic evidence graph.

Workers use this layer to record outbound fetches, searches, and tool calls as
append-only evidence. The graph is searchable by tenant/query/worker/destination,
but it never serves truth; Baltor can later verify or promote facts separately.
"""

from .traffic_graph import (
    DEFAULT_DB_PATH,
    EGRESS_SERVES_TRUTH,
    LocalEgressGraph,
    TeleonEgressGraphRejected,
    make_egress_observation,
)
from .client import EgressBlocked, EgressClient
from .ledger import DEFAULT_LEDGER_DB_PATH, EgressLedgerRejected, LocalEgressLedger
from .policy import DEFAULT_ROUTE_POLICY_ID, EgressPolicyError, decide_route, make_egress_intent
from .transports import EgressTransportError, EgressTransportResponse, UrllibHttpTransport

__all__ = [
    "DEFAULT_DB_PATH",
    "DEFAULT_LEDGER_DB_PATH",
    "DEFAULT_ROUTE_POLICY_ID",
    "EGRESS_SERVES_TRUTH",
    "EgressBlocked",
    "EgressClient",
    "EgressLedgerRejected",
    "EgressPolicyError",
    "EgressTransportError",
    "EgressTransportResponse",
    "LocalEgressGraph",
    "LocalEgressLedger",
    "TeleonEgressGraphRejected",
    "UrllibHttpTransport",
    "decide_route",
    "make_egress_intent",
    "make_egress_observation",
]
