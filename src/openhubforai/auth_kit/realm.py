"""src.openharnesshub.auth_kit.realm — the SHARED auth/identity kit: separate, INDEPENDENT realms per product.

Owner decision (2026-06-09): "completely separate and independent logins / register / onboarding, but we can
have similar UI / backend elements." This kit is the SHARED building block — ONE set of flow shapes + object
shapes + primitives. Each product (Baltor, Teleon, each Open*Hub) instantiates its OWN realm via make_realm(),
with its OWN accounts + sessions + registration. There is NO cross-realm account and NO single-sign-on across
realms. This mirrors the portfolio law (Baltor / Teleon are identity-SEPARATED) and the branded-house model
(shared kit, per-product instance).

Lives in OpenHarnessHub — the open, bottom layer — so Baltor + Teleon may import it (Baltor→Teleon→OHH); OHH
imports neither. Deterministic, offline, stdlib-only: `now` is an injected logical clock (int), session handles
are deterministic opaque tokens (NOT real JWTs), and CREDENTIALS ARE ONE-WAY REFS — a cleartext password is
NEVER stored or echoed; real password-hash / OAuth / SSO / passkey verification is a documented SEAM
(CredentialProviderPort). The kit is reference infrastructure, not a deployed auth service.
"""
from __future__ import annotations

import hashlib
from typing import Any

#: the standard flow every realm runs (shared shape); the realms that run it are independent.
STANDARD_FLOW = ("register", "onboarding", "login")
ACCOUNT_STATUSES = ("registered", "onboarding", "active", "disabled")
DEFAULT_SESSION_TTL = 30          # logical-clock units (injected `now`); a real clock/TTL is a seam
DEFAULT_ONBOARDING_STEPS = ("verify_identifier", "accept_terms", "set_profile")


def _handle(prefix: str, *parts: str) -> str:
    return prefix + "_" + hashlib.blake2b("|".join(parts).encode(), digest_size=10).hexdigest()


class CredentialProviderPort:
    """SEAM for credential verification. Reference impl: a one-way ref handle via blake2b — NOT production
    crypto. A real provider (argon2/bcrypt password hash, OAuth subject, SSO assertion, passkey) drops in here.
    The kit stores ONLY the ref; the cleartext secret is hashed on the way in and never stored or echoed."""

    def make_ref(self, secret: str) -> str:
        return "credref:" + hashlib.blake2b(("cred|" + secret).encode(), digest_size=16).hexdigest()

    def verify(self, stored_ref: str, secret: str) -> bool:
        return bool(stored_ref) and stored_ref == self.make_ref(secret)


class Realm:
    """One product's INDEPENDENT identity realm: its own accounts + sessions + registration. Realm-scoped — it
    never sees another realm's accounts or sessions (no cross-realm SSO)."""

    def __init__(self, realm_id: str, *, display_name: str, onboarding_steps: tuple[str, ...],
                 session_ttl: int, credentials: CredentialProviderPort) -> None:
        self.realm_id = realm_id
        self.display_name = display_name
        self.onboarding_steps = tuple(onboarding_steps)
        self.session_ttl = session_ttl
        self._cred = credentials
        self.accounts: dict[str, dict[str, Any]] = {}      # OWN store (per-realm; never shared)
        self.sessions: dict[str, dict[str, Any]] = {}       # OWN store
        self._by_identifier: dict[str, str] = {}            # identifier → account_id, WITHIN this realm only

    def register(self, identifier: str, secret: str, *, now: int) -> dict[str, Any]:
        """register flow — create an account in THIS realm. The secret is hashed to a one-way credential_ref;
        the cleartext secret is never stored."""
        if not identifier or not secret:
            raise ValueError("identifier and secret required")
        if identifier in self._by_identifier:
            raise ValueError(f"identifier already registered in realm {self.realm_id!r}")
        aid = _handle("acct", self.realm_id, identifier)
        acct = {
            "account_id": aid, "realm_id": self.realm_id, "identifier": identifier,
            "credential_ref": self._cred.make_ref(secret),   # a REF — never the cleartext secret
            "status": "registered", "onboarding_done": [], "created_at": now,
        }
        self.accounts[aid] = acct
        self._by_identifier[identifier] = aid
        return dict(acct)

    def onboard(self, account_id: str, step: str, *, now: int) -> dict[str, Any]:
        """onboarding flow — advance a step; the account becomes 'active' only when ALL steps are done."""
        acct = self.accounts.get(account_id)
        if not acct:
            raise ValueError(f"no account {account_id!r} in realm {self.realm_id!r}")
        if step not in self.onboarding_steps:
            raise ValueError(f"unknown onboarding step {step!r}")
        if step not in acct["onboarding_done"]:
            acct["onboarding_done"].append(step)
        acct["status"] = "active" if all(s in acct["onboarding_done"] for s in self.onboarding_steps) else "onboarding"
        return dict(acct)

    def login(self, identifier: str, secret: str, *, now: int) -> dict[str, Any]:
        """login flow — realm-SCOPED: the account must exist IN THIS realm, be active, and pass credential
        verification. Mints an opaque, realm-scoped session handle."""
        aid = self._by_identifier.get(identifier)
        if not aid:
            raise ValueError(f"no such account in realm {self.realm_id!r}")   # realm-isolated: not found here
        acct = self.accounts[aid]
        if acct["status"] != "active":
            raise ValueError("account not active — complete onboarding first")
        if not self._cred.verify(acct["credential_ref"], secret):
            raise ValueError("credential verification failed")
        sid = _handle("sess", self.realm_id, aid, str(now))
        sess = {"session_id": sid, "realm_id": self.realm_id, "account_id": aid,
                "issued_at": now, "expires_at": now + self.session_ttl}
        self.sessions[sid] = sess
        return dict(sess)

    def validate_session(self, session_id: str, *, now: int) -> bool:
        """A session is valid only in THIS realm (its own store) and only before it expires."""
        s = self.sessions.get(session_id)
        return bool(s) and now < s["expires_at"]

    def snapshot(self) -> dict[str, Any]:
        """Serializable copy of this realm's OWN stores — for a host service's persistence. Contains
        credential REFS and opaque handles only; a cleartext secret never exists in realm state."""
        return {"accounts": {k: dict(v) for k, v in self.accounts.items()},
                "sessions": {k: dict(v) for k, v in self.sessions.items()},
                "by_identifier": dict(self._by_identifier)}

    def restore(self, state: dict[str, Any]) -> None:
        """Hydrate this realm's stores from a snapshot(). Realm-guarded: a snapshot taken in another
        realm is rejected, so persistence cannot become a cross-realm bridge."""
        for acct in state.get("accounts", {}).values():
            if acct.get("realm_id") != self.realm_id:
                raise ValueError(f"snapshot belongs to realm {acct.get('realm_id')!r}, not {self.realm_id!r}")
        for sess in state.get("sessions", {}).values():
            if sess.get("realm_id") != self.realm_id:
                raise ValueError(f"snapshot session belongs to realm {sess.get('realm_id')!r}, not {self.realm_id!r}")
        self.accounts = {k: dict(v) for k, v in state.get("accounts", {}).items()}
        self.sessions = {k: dict(v) for k, v in state.get("sessions", {}).items()}
        self._by_identifier = dict(state.get("by_identifier", {}))


def make_realm(realm_id: str, *, display_name: str | None = None,
               onboarding_steps: tuple[str, ...] = DEFAULT_ONBOARDING_STEPS,
               session_ttl: int = DEFAULT_SESSION_TTL,
               credentials: CredentialProviderPort | None = None) -> Realm:
    """The SHARED kit factory — build one product's INDEPENDENT realm. Same kit, separate instance: two realms
    built here share NO accounts or sessions."""
    return Realm(realm_id, display_name=display_name or realm_id, onboarding_steps=onboarding_steps,
                 session_ttl=session_ttl, credentials=credentials or CredentialProviderPort())
