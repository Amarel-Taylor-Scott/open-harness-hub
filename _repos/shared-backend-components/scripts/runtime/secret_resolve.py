#!/usr/bin/env python3
"""scripts.runtime.secret_resolve — the ONE secret-resolution CHOKEPOINT.

`resolve(name)` is the single seam every script funnels a secret through, so the resolution
BACKEND can be swapped in ONE place instead of at the ~27 direct `os.environ`/`getenv` call sites
the key-depth audit found under `scripts/`. Today the backend is `env` (os.environ then a local
.env) — resolved through the SAME read the runtime key holder uses
(`src.teleon.runtime.credentials.env_value`, which `src.teleon.runtime.key_holder.KeyHolder`
funnels through) — so adopting this chokepoint changes NO behavior. NOTE: the SOPS+age vault
(scripts/deploy/sops_fallback_cipher.py, .sops.yaml) is DECRYPT-TO-ENV at deploy time — it populates
os.environ, which the `env` backend then reads; it does NOT register a chokepoint backend. Registering
a `sops`/`age`, `rotating`, or `per-tenant` backend here (so resolution is programmatic, not restart-
scoped) is the future extension point; no such backend is wired yet.

Design contract:
  * `resolve(name)` returns the secret VALUE or None; it NEVER logs the value (redaction-safe).
  * The active backend is config-swappable via `OH_SECRET_BACKEND` (default "env"); new backends
    register through `register_backend(name, backend)` — a portfolio behind one selector
    (MULTI-PATH-DEVELOPMENT), never a rewrite of the callers.
  * `resolve_service(service_id, ...)` delegates to the existing key-holder seam so service-level
    resolution (byo/platform ownership + entitlement gating) stays single-sourced there.
  * serves_truth=false — this resolves a POINTER to a secret, never truth.

The ratchet gate `scripts/check_secret_chokepoint.py` inventories the direct reads that still
bypass this seam and FAILS on a NEW one, so the audit's sites migrate here safely over time.

  PYTHONPATH=. python3 scripts/runtime/secret_resolve.py --self-test
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Self-bootstrap: a chokepoint must resolve `scripts.*` and the moved `src.<x>` backend roots
# regardless of the caller's CWD/PYTHONPATH (so it never false-fails just because PYTHONPATH= was
# forgotten). Single source of the path list: scripts/_repo_paths.py.
_REPO = next((p for p in Path(__file__).resolve().parents
              if (p / "scripts" / "_repo_paths.py").exists()), Path(__file__).resolve().parents[2])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

#: env-var name selecting the active backend; env today, config-swappable later (no caller change).
BACKEND_SELECTOR_ENV = "OH_SECRET_BACKEND"
DEFAULT_BACKEND = "env"


class EnvSecretBackend:
    """The default backend: resolves a name to its value through the SAME read the runtime key holder
    uses (`credentials.env_value` — os.environ, then a local .env). Wrapping the key-holder seam here
    means the chokepoint is behaviour-identical to the code it replaces. Never logs a value."""

    name = "env"

    def get(self, secret_name: str, env: dict | None = None) -> str | None:
        # Lazy import so the module loads even if the teleon backend root is momentarily unavailable;
        # falls back to a raw os.environ/.env read (still name-parametrised, never a hardcoded secret).
        try:
            from src.teleon.runtime import credentials as _credentials  # noqa: PLC0415
            value = _credentials.py_function_src_teleon_runtime_credentials__env_value(secret_name, env)
        except Exception:  # noqa: BLE001 — resolution must never crash a caller; treat as unset
            if env is not None:
                value = str(env.get(secret_name, "")).strip()
            else:
                value = (os.environ.get(secret_name) or "").strip()
        return value or None


#: The backend portfolio behind one selector (MULTI-PATH-DEVELOPMENT). `env` is the only path today;
#: `sops`/`age`, `rotating`, `per-tenant` register here later and every caller inherits them.
_BACKENDS: dict[str, object] = {EnvSecretBackend.name: EnvSecretBackend()}


def register_backend(name: str, backend: object) -> None:
    """Register a resolution backend (must expose `.get(secret_name, env=None) -> str | None`). This is
    how SOPS/age, rotating, or per-tenant resolution is added WITHOUT touching a single caller."""
    if not hasattr(backend, "get"):
        raise TypeError(f"secret backend {name!r} must expose .get(secret_name, env=None)")
    _BACKENDS[name] = backend


def active_backend_name(env: dict | None = None) -> str:
    """The selected backend id (`OH_SECRET_BACKEND`, default `env`), falling back to `env` if unknown."""
    selected = (env or os.environ).get(BACKEND_SELECTOR_ENV) or DEFAULT_BACKEND
    return selected if selected in _BACKENDS else DEFAULT_BACKEND


def active_backend(env: dict | None = None):
    """The active backend instance."""
    return _BACKENDS[active_backend_name(env)]


def resolve(secret_name: str, *, env: dict | None = None, default: str | None = None) -> str | None:
    """THE chokepoint: resolve a secret NAME to its value through the active backend, or `default`
    (None) if unset. NEVER log the return value. `env` injects a hermetic mapping for tests."""
    value = active_backend(env).get(secret_name, env)
    return value if value else default


def resolve_required(secret_name: str, *, env: dict | None = None) -> str:
    """Like `resolve` but raises `KeyError` (naming the missing var, never a value) when unset — for
    callers that cannot proceed without the secret."""
    value = resolve(secret_name, env=env)
    if not value:
        raise KeyError(f"secret {secret_name!r} is not set (backend={active_backend_name(env)!r})")
    return value


def is_set(secret_name: str, *, env: dict | None = None) -> bool:
    """Whether a secret is resolvable — a redaction-safe presence check (returns a bool, never a value)."""
    return resolve(secret_name, env=env) is not None


def resolve_service(service_id: str, *, env: dict | None = None, tenant_keys: set | None = None,
                    principal=None) -> str | None:
    """Service-level resolution — delegates to the runtime KEY HOLDER seam so byo/platform ownership +
    entitlement gating stay single-sourced there. Prefer this over `resolve` when you have a
    credential-registry service id (github, anthropic, …) rather than a bare env-var name."""
    from src.teleon.runtime import key_holder as _key_holder  # noqa: PLC0415
    return _key_holder.py_const_src_teleon_runtime_key_holder__HOLDER.resolve(
        service_id, env, tenant_keys=tenant_keys, principal=principal)


def _self_test() -> int:
    results: list[tuple[str, bool, str]] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))

    # A. resolve() reads a value from an injected (hermetic) env, and returns None when unset.
    ck("resolve returns the injected value",
       resolve("OH_LLM_API_KEY", env={"OH_LLM_API_KEY": "secret-x"}) == "secret-x", "")
    ck("resolve returns None when unset", resolve("OH_LLM_API_KEY", env={}) is None, "")
    ck("resolve honours default when unset",
       resolve("OH_LLM_API_KEY", env={}, default="fallback") == "fallback", "")
    ck("is_set is a redaction-safe bool",
       is_set("OH_LLM_API_KEY", env={"OH_LLM_API_KEY": "x"}) is True and is_set("X_MISSING", env={}) is False, "")

    # B. resolve_required raises (naming the var, never a value) when unset.
    try:
        resolve_required("OH_LLM_API_KEY", env={})
        ck("resolve_required raises on unset", False, "did not raise")
    except KeyError as exc:
        ck("resolve_required raises on unset (names var, not value)",
           "OH_LLM_API_KEY" in str(exc) and "secret-x" not in str(exc), "")

    # C. The backend is swappable behind the selector (the SOPS/age/rotating extension point).
    class _StubBackend:
        name = "stub"

        def get(self, secret_name: str, env: dict | None = None) -> str | None:
            return f"stub::{secret_name}"

    register_backend("stub", _StubBackend())
    ck("active_backend_name follows OH_SECRET_BACKEND",
       active_backend_name({BACKEND_SELECTOR_ENV: "stub"}) == "stub"
       and active_backend_name({}) == DEFAULT_BACKEND, "")
    ck("a registered backend is used by resolve",
       resolve("OH_LLM_API_KEY", env={BACKEND_SELECTOR_ENV: "stub"}) == "stub::OH_LLM_API_KEY", "")
    ck("unknown backend falls back to env (never crashes)",
       active_backend_name({BACKEND_SELECTOR_ENV: "does-not-exist"}) == DEFAULT_BACKEND, "")
    try:
        register_backend("bad", object())
        ck("register_backend rejects a backend without .get", False, "accepted bad backend")
    except TypeError:
        ck("register_backend rejects a backend without .get", True, "")

    # D. resolve_service funnels through the existing key-holder seam (keyless github resolves; a keyed
    #    service with no key resolves to None) — proving the chokepoint wraps key_holder, not a new path.
    try:
        gh = resolve_service("github", env={})           # keyless -> present, but has no value to hand back
        lib = resolve_service("libraries_io", env={})    # keyed, unset -> None
        ck("resolve_service delegates to key_holder (keyed+unset -> None)", lib is None, f"github={gh!r}")
    except Exception as exc:  # noqa: BLE001
        ck("resolve_service delegates to key_holder (keyed+unset -> None)", False, repr(exc))

    failures = [n for n, ok, _ in results if not ok]
    for name, ok, detail in results:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
    if failures:
        print(f"\n{len(failures)} FAILURES: {failures}")
        return 1
    print("\nPASS - secret_resolve: ONE resolve(name) chokepoint over a swappable backend "
          "(env now; SOPS/age/rotating/per-tenant later), wrapping the key-holder seam.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
