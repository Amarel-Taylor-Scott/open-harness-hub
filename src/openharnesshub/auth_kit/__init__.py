"""src.openharnesshub.auth_kit — the SHARED auth/identity kit (separate, INDEPENDENT realms per product).

One kit (flow shapes + object shapes + primitives); each product instantiates its OWN realm via make_realm(),
with its own accounts/sessions/registration — no cross-realm account, no single-sign-on. Open bottom-layer
building block: Baltor + Teleon may import it (Baltor→Teleon→OHH); OHH imports neither. See realm.py.
"""
from __future__ import annotations

from .realm import (
    ACCOUNT_STATUSES,
    DEFAULT_ONBOARDING_STEPS,
    DEFAULT_SESSION_TTL,
    STANDARD_FLOW,
    CredentialProviderPort,
    Realm,
    make_realm,
)

__all__ = ["make_realm", "Realm", "CredentialProviderPort", "STANDARD_FLOW", "ACCOUNT_STATUSES",
           "DEFAULT_ONBOARDING_STEPS", "DEFAULT_SESSION_TTL"]
