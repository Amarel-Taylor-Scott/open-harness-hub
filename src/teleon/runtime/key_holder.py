"""src.teleon.runtime.key_holder — the runtime KEY HOLDER (developer-key side of the credential plane).

The credential REGISTRY catalogs which secrets exist + what they unlock; `credentials.py` answers reachability; THIS
resolves a service's secret VALUE for an actual call and hands back ready-to-use auth headers — honoring the byo/platform
key-ownership model + platform_limits. A developer "adds a key" by setting its env var (BYO -> their account/plan); the
holder picks it up. REDACTION-SAFE: it never logs a value and exposes only a redacted status; the raw value goes only to
the caller making the request. Complements SecretRef (the typed ref). serves_truth=false; Teleon layer.
"""
from __future__ import annotations

from src.teleon.runtime import credentials as C

#: per-service auth header SHAPE (how the resolved key is presented to that API). Default = bearer.
_HEADER_STYLE = {
    "github": lambda v: {"Authorization": f"Bearer {v}", "Accept": "application/vnd.github+json"},
    "gitlab": lambda v: {"PRIVATE-TOKEN": v},
    "rapidapi": lambda v: {"X-RapidAPI-Key": v},
    "apify": lambda v: {"Authorization": f"Bearer {v}"},
    "anthropic": lambda v: {"x-api-key": v, "anthropic-version": "2023-06-01"},
    "fly": lambda v: {"Authorization": f"Bearer {v}"},
}


class KeyHolder:
    """Holds + resolves developer/platform keys for the pipeline. No values are stored on the instance; each call reads
    fresh from the environment via credentials.env_value."""

    def held(self, env: dict | None = None, tenant_keys: set | None = None) -> set[str]:
        """Service ids whose key is currently available (a developer added it, or it's keyless/platform-within-limits)."""
        return {s["id"] for s in C._services() if C.key_mode(s["id"], env, byo=tenant_keys) is not None}

    def resolve(self, service_id: str, env: dict | None = None, *, tenant_keys: set | None = None, principal=None) -> str | None:
        """The secret VALUE for a reachable service (its first env var), or None. NEVER log the return value. When a
        `principal` is given, the key is ALSO gated by the access policy: a free user can't use a platform key, but can
        use their own BYO key (entitlement on top of mere reachability)."""
        if C.key_mode(service_id, env, byo=tenant_keys) is None:
            return None
        if principal is not None:
            from src.teleon.runtime import entitlements as E
            if not E.entitled_key(principal, service_id):
                return None                        # reachable but NOT entitled -> denied (no value leaves)
        svc = C._svc(service_id)
        if not svc or not svc.get("env_vars"):
            return None
        return C.env_value(svc["env_vars"][0], env) or None

    def auth_headers(self, service_id: str, env: dict | None = None, *, tenant_keys: set | None = None) -> dict:
        """Ready-to-use auth header(s) for the service ({} if no key is held) — so callers never touch the raw value."""
        v = self.resolve(service_id, env, tenant_keys=tenant_keys)
        if not v:
            return {}
        return _HEADER_STYLE.get(service_id, lambda x: {"Authorization": f"Bearer {x}"})(v)

    def missing(self, service_id: str, env: dict | None = None) -> list[str]:
        """The env var(s) a developer must set to enable this service ([] if held). For honest 'needs X' messages."""
        return C.missing_for(service_id, env)

    def status(self, env: dict | None = None, tenant_keys: set | None = None, *, principal=None) -> dict:
        """REDACTED snapshot for display: which services are held vs missing, the mode (byo/platform), limits, and — when
        a `principal` is given — whether THEY are entitled to use it (held != entitled). NO values, ever."""
        held = self.held(env, tenant_keys)
        ent = None
        if principal is not None:
            from src.teleon.runtime import entitlements as E
            ent = {s["id"] for s in C._services() if E.entitled_key(principal, s["id"])}
        rows = []
        for s in C._services():
            sid = s["id"]
            row = {"service": sid, "held": sid in held, "mode": C.key_mode(sid, env, byo=tenant_keys),
                   "ownership": C.key_ownership(sid), "needs": ([] if sid in held else s["env_vars"]),
                   "platform_limits": C.platform_limits(sid)}
            if ent is not None:
                row["entitled"] = sid in ent
                row["usable"] = (sid in held) and (sid in ent)
            rows.append(row)
        return {"held": sorted(held), "services": rows, "serves_truth": False}


HOLDER = KeyHolder()
