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
py_var_src_teleon_runtime_key_holder___HEADER_STYLE = {
    "github": lambda py_arg_src_teleon_runtime_key_holder__v: {"Authorization": f"Bearer {py_arg_src_teleon_runtime_key_holder__v}", "Accept": "application/vnd.github+json"},
    "gitlab": lambda py_arg_src_teleon_runtime_key_holder__v: {"PRIVATE-TOKEN": py_arg_src_teleon_runtime_key_holder__v},
    "rapidapi": lambda py_arg_src_teleon_runtime_key_holder__v: {"X-RapidAPI-Key": py_arg_src_teleon_runtime_key_holder__v},
    "apify": lambda py_arg_src_teleon_runtime_key_holder__v: {"Authorization": f"Bearer {py_arg_src_teleon_runtime_key_holder__v}"},
    "anthropic": lambda py_arg_src_teleon_runtime_key_holder__v: {"x-api-key": py_arg_src_teleon_runtime_key_holder__v, "anthropic-version": "2023-06-01"},
    "fly": lambda py_arg_src_teleon_runtime_key_holder__v: {"Authorization": f"Bearer {py_arg_src_teleon_runtime_key_holder__v}"},
}


class py_class_src_teleon_runtime_key_holder__KeyHolder:
    """Holds + resolves developer/platform keys for the pipeline. No values are stored on the instance; each call reads
    fresh from the environment via credentials.env_value."""

    def held(self, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_held__env: dict | None = None, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_held__tenant_keys: set | None = None) -> set[str]:
        """Service ids whose key is currently available (a developer added it, or it's keyless/platform-within-limits)."""
        return {s["id"] for s in C.py_function_src_teleon_runtime_credentials___services() if C.py_function_src_teleon_runtime_credentials__key_mode(s["id"], py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_held__env, byo=py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_held__tenant_keys) is not None}

    def resolve(self, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_resolve__service_id: str, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_resolve__env: dict | None = None, *, tenant_keys: set | None = None, principal=None) -> str | None:
        """The secret VALUE for a reachable service (its first env var), or None. NEVER log the return value. When a
        `principal` is given, the key is ALSO gated by the access policy: a free user can't use a platform key, but can
        use their own BYO key (entitlement on top of mere reachability)."""
        if C.py_function_src_teleon_runtime_credentials__key_mode(py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_resolve__service_id, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_resolve__env, byo=tenant_keys) is None:
            return None
        if principal is not None:
            from src.teleon.runtime import entitlements as E
            if not E.py_function_src_teleon_runtime_entitlements__entitled_key(principal, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_resolve__service_id):
                return None                        # reachable but NOT entitled -> denied (no value leaves)
        py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_resolve__svc = C.py_function_src_teleon_runtime_credentials___svc(py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_resolve__service_id)
        if not py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_resolve__svc or not py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_resolve__svc.get("env_vars"):
            return None
        return C.py_function_src_teleon_runtime_credentials__env_value(py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_resolve__svc["env_vars"][0], py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_resolve__env) or None

    def auth_headers(self, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_auth_headers__service_id: str, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_auth_headers__env: dict | None = None, *, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_auth_headers__tenant_keys: set | None = None) -> dict:
        """Ready-to-use auth header(s) for the service ({} if no key is held) — so callers never touch the raw value."""
        py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_auth_headers__v = self.resolve(py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_auth_headers__service_id, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_auth_headers__env, tenant_keys=py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_auth_headers__tenant_keys)
        if not py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_auth_headers__v:
            return {}
        return py_var_src_teleon_runtime_key_holder___HEADER_STYLE.get(py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_auth_headers__service_id, lambda py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_auth_headers__x: {"Authorization": f"Bearer {py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_auth_headers__x}"})(py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_auth_headers__v)

    def missing(self, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_missing__service_id: str, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_missing__env: dict | None = None) -> list[str]:
        """The env var(s) a developer must set to enable this service ([] if held). For honest 'needs X' messages."""
        return C.py_function_src_teleon_runtime_credentials__missing_for(py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_missing__service_id, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_missing__env)

    def status(self, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__env: dict | None = None, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__tenant_keys: set | None = None, *, principal=None) -> dict:
        """REDACTED snapshot for display: which services are held vs missing, the mode (byo/platform), limits, and — when
        a `principal` is given — whether THEY are entitled to use it (held != entitled). NO values, ever."""
        py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__held = self.held(py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__env, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__tenant_keys)
        py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__ent = None
        if principal is not None:
            from src.teleon.runtime import entitlements as E
            py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__ent = {py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__s["id"] for py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__s in C.py_function_src_teleon_runtime_credentials___services() if E.py_function_src_teleon_runtime_entitlements__entitled_key(principal, py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__s["id"])}
        py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__rows = []
        for py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__s in C.py_function_src_teleon_runtime_credentials___services():
            py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__sid = py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__s["id"]
            py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__row = {"service": py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__sid, "held": py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__sid in py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__held, "mode": C.py_function_src_teleon_runtime_credentials__key_mode(py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__sid, py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__env, byo=py_arg_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__tenant_keys),
                   "ownership": C.py_function_src_teleon_runtime_credentials__key_ownership(py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__sid), "needs": ([] if py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__sid in py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__held else py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__s["env_vars"]),
                   "platform_limits": C.py_function_src_teleon_runtime_credentials__platform_limits(py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__sid)}
            if py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__ent is not None:
                py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__row["entitled"] = py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__sid in py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__ent
                py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__row["usable"] = (py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__sid in py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__held) and (py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__sid in py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__ent)
            py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__rows.append(py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__row)
        return {"held": sorted(py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__held), "services": py_local_src_teleon_runtime_key_holder__py_class_src_teleon_runtime_key_holder__KeyHolder_status__rows, "serves_truth": False}


py_const_src_teleon_runtime_key_holder__HOLDER = py_class_src_teleon_runtime_key_holder__KeyHolder()
