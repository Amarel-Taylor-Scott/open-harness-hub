"""src.teleon.endpoints — interchangeable PROVIDER ENDPOINTS per capability, selected by the objective layer.

When a capability unit needs an external call (WHOIS, geocoding, a stock quote), many providers can serve it.
This package registers those endpoints and picks the best one for the tenant's priority (fastest / cheapest /
most reliable) via src.teleon.objectives — the same selection used for runners and placement — with an org
guardrail policy able to forbid endpoints (license/domain/egress) before selection, and a RunLedger refining the
choice from observed calls. Teleon-layer — never imports src.baltor."""
from src.teleon.endpoints.registry import (
    EndpointError,
    ProviderEndpoint,
    endpoints_for,
    registered_capabilities,
    select_endpoint,
)

__all__ = ["ProviderEndpoint", "EndpointError", "endpoints_for", "registered_capabilities", "select_endpoint"]
