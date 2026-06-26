"""src.teleon.purpose_tasks.runtime_binding — CTS-1: bind a PurposeTask's declared RUNTIME CLASS to a CONCRETE
execution backend by policy + available credentials + provider health.

A PurposeTask declares `allowed_runtime_classes` from the OCTS-portable vocabulary
(`architecture/capability_runtime_classes.json`) — the contract names the CLASS (e.g. `cloud-function`,
`kubernetes-job`, `gpu-worker`), never a vendor product. This module BINDS a class to a runnable backend:

  * **Cloud-defer-only-after-local-equivalent.** Every class declares a BUILT local equivalent. A cloud/K8s
    vendor is chosen ONLY when it is credentialed AND healthy; otherwise the binding falls back to the class's
    local equivalent (always available). Capability never blocks on missing cloud.
  * **Class-scoped hard guard, for free.** The binding only ever considers a class's OWN vendors, so a
    browser/GPU class can never bind to a generic cloud function — the class vocabulary already scopes it.
  * **Deny-by-default.** An unknown / unrecognized runtime class binds to the offline default backend.

It COMPOSES with `execution_backend_selector` (which ranks concrete backends by bucket/cost/health) — it does
not replace it: `eligible_backends_for_classes` produces the constraint set the selector ranks within. Pure +
deterministic; branches on the runtime CLASS + numeric policy, never on a vendor display name. All inputs are
injectable for testing.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_A = Path(__file__).resolve().parents[3] / "architecture"
#: provider-namespace local ids carry this prefix in the registry/matrix; the selector + dispatch use the
#: BARE id (no prefix). Stripping it bridges the two namespaces deterministically (one rule, not a per-class map).
_PROVIDER_PREFIX = "execution."
#: vendor entries in the class vocabulary carry an adoption-status suffix (e.g. "@candidate"); a vendor is a
#: real cloud/K8s backend regardless of status. We match credentials/health on the FULL id (matches pricebook).
_DEFAULT_OFFLINE_BACKEND = "local_function_emulator@v1"  # used only if the matrix omits offline_default_backend

_classes_cache: dict | None = None
_matrix_cache: dict | None = None


def _load(name: str) -> dict:
    return json.loads((_A / name).read_text(encoding="utf-8"))


def _runtime_classes(runtime_classes: dict | None = None) -> dict:
    global _classes_cache
    if runtime_classes is not None:
        return runtime_classes
    if _classes_cache is None:
        _classes_cache = _load("capability_runtime_classes.json")
    return _classes_cache


def _matrix(policy_matrix: dict | None = None) -> dict:
    global _matrix_cache
    if policy_matrix is not None:
        return policy_matrix
    if _matrix_cache is None:
        _matrix_cache = _load("execution_backend_policy_matrix.json")
    return _matrix_cache


def _index(runtime_classes: dict | None = None) -> dict[str, dict]:
    return {c["class"]: c for c in _runtime_classes(runtime_classes).get("classes", [])}


def offline_default_backend(policy_matrix: dict | None = None) -> str:
    """The bare-id local backend the platform uses when nothing else is available (deny-by-default target)."""
    return _matrix(policy_matrix).get("offline_default_backend", _DEFAULT_OFFLINE_BACKEND)


def class_record(runtime_class: str, *, runtime_classes: dict | None = None) -> dict | None:
    """The vocabulary record for a runtime class, or None if it is not a known class."""
    return _index(runtime_classes).get(runtime_class)


def is_known_class(runtime_class: str, *, runtime_classes: dict | None = None) -> bool:
    return runtime_class in _index(runtime_classes)


def class_vendor_backends(runtime_class: str, *, runtime_classes: dict | None = None) -> list[str]:
    """The cloud/K8s vendor backends a class may bind to (full ids incl. status suffix). [] for local-only."""
    rec = class_record(runtime_class, runtime_classes=runtime_classes)
    return list(rec.get("vendors", [])) if rec else []


def local_fallback_backend(runtime_class: str, *, runtime_classes: dict | None = None,
                           policy_matrix: dict | None = None) -> str:
    """The bare-id LOCAL backend a class falls back to when no cloud vendor is credentialed+healthy. Derived
    from the class's `local_equivalent` (provider namespace) by stripping the `execution.` prefix so the result
    is a backend the selector/dispatch can route. Unknown class → the platform offline default."""
    rec = class_record(runtime_class, runtime_classes=runtime_classes)
    if rec is None:
        return offline_default_backend(policy_matrix)
    eq = rec.get("local_equivalent") or offline_default_backend(policy_matrix)
    return eq[len(_PROVIDER_PREFIX):] if eq.startswith(_PROVIDER_PREFIX) else eq


def _decision(action: str, runtime_class: str, backend: str, *, is_local_fallback: bool, known_class: bool,
              reason: str, considered: list[str]) -> dict[str, Any]:
    return {"schema_version": "RuntimeClassBinding", "action": action, "runtime_class": runtime_class,
            "backend": backend, "is_local_fallback": is_local_fallback, "known_class": known_class,
            "reason": reason, "considered": considered}


def bind(runtime_class: str, *, available_creds: set | None = None, provider_health: dict | None = None,
         policy_override: dict | None = None, runtime_classes: dict | None = None,
         policy_matrix: dict | None = None) -> dict[str, Any]:
    """Bind ONE runtime class to a concrete backend.

    Prefers a cloud/K8s vendor of the class that is BOTH credentialed (`available_creds`) and healthy
    (`provider_health[v]` not False), honoring `policy_override` {preferred_backends, excluded_backends}.
    Falls back to the class's local equivalent (always available) when no such vendor exists. Unknown class →
    offline default (deny-by-default). Never raises on a missing/unknown input.
    """
    creds = set(available_creds or set())
    health = provider_health or {}
    ov = policy_override or {}
    excluded = set(ov.get("excluded_backends", []))
    preferred = list(ov.get("preferred_backends", []))

    if not is_known_class(runtime_class, runtime_classes=runtime_classes):
        fb = offline_default_backend(policy_matrix)
        return _decision("bind_local_fallback", runtime_class, fb, is_local_fallback=True, known_class=False,
                         reason="unknown runtime class → offline default backend (deny-by-default)", considered=[])

    vendors = [v for v in class_vendor_backends(runtime_class, runtime_classes=runtime_classes) if v not in excluded]
    credentialed = [v for v in vendors if v in creds]
    runnable = [v for v in credentialed if health.get(v, True)]

    if runnable:
        chosen = next((v for v in preferred if v in runnable), None) or runnable[0]
        basis = "policy preferred_backends" if chosen in preferred else "first credentialed+healthy class vendor"
        return _decision("bind_cloud_backend", runtime_class, chosen, is_local_fallback=False, known_class=True,
                         reason=f"bound {runtime_class!r} to cloud/K8s backend by {basis}", considered=vendors)

    # no cloud vendor is runnable → local equivalent (cloud-defer-only-after-local-equivalent)
    fb = local_fallback_backend(runtime_class, runtime_classes=runtime_classes, policy_matrix=policy_matrix)
    if not vendors:
        why = "class has no cloud vendors (local-only class)"
    elif not credentialed:
        why = "no class vendor is credentialed → defer cloud, run local equivalent"
    else:
        why = "credentialed class vendor(s) unhealthy → fall back to local equivalent"
    return _decision("bind_local_fallback", runtime_class, fb, is_local_fallback=True, known_class=True,
                     reason=why, considered=vendors)


def bind_allowed(allowed_runtime_classes: list[str] | None, *, available_creds: set | None = None,
                 provider_health: dict | None = None, policy_override: dict | None = None,
                 runtime_classes: dict | None = None, policy_matrix: dict | None = None) -> dict[str, Any]:
    """Bind a task that allows SEVERAL runtime classes (declared in priority order). Returns the first class
    that yields a runnable CLOUD binding; if none does, the LOCAL equivalent of the first allowed class (or the
    offline default when the list is empty). Always returns a usable binding — capability never blocks."""
    classes = list(allowed_runtime_classes or [])
    if not classes:
        fb = offline_default_backend(policy_matrix)
        return _decision("bind_local_fallback", "(none-declared)", fb, is_local_fallback=True, known_class=False,
                         reason="no allowed_runtime_classes declared → offline default backend", considered=[])
    local_first: dict[str, Any] | None = None
    for rc in classes:
        d = bind(rc, available_creds=available_creds, provider_health=provider_health,
                 policy_override=policy_override, runtime_classes=runtime_classes, policy_matrix=policy_matrix)
        if not d["is_local_fallback"]:
            return d
        if local_first is None:
            local_first = d
    assert local_first is not None  # classes is non-empty so the loop set it
    return local_first


def resolve_for_spec(spec: dict[str, Any], *, available_creds: set | None = None,
                     provider_health: dict | None = None, policy_override: dict | None = None,
                     runtime_classes: dict | None = None, policy_matrix: dict | None = None) -> dict[str, Any]:
    """Bind a PurposeTask SPEC by its declared `allowed_runtime_classes` (CTS-1 connection to PurposeTaskSpec)."""
    return bind_allowed(spec.get("allowed_runtime_classes"), available_creds=available_creds,
                        provider_health=provider_health, policy_override=policy_override,
                        runtime_classes=runtime_classes, policy_matrix=policy_matrix)


def eligible_backends_for_classes(allowed_runtime_classes: list[str] | None, *, runtime_classes: dict | None = None,
                                  policy_matrix: dict | None = None) -> list[str]:
    """The union of concrete backends the allowed classes may bind to (cloud vendors + each class's local
    equivalent), de-duplicated, with at least one local fallback guaranteed. Feed this to the execution selector
    as `policy_override['eligible']` so cost/health ranking happens WITHIN the contract's allowed shapes."""
    out: list[str] = []
    seen: set[str] = set()

    def add(b: str) -> None:
        if b not in seen:
            seen.add(b)
            out.append(b)

    for rc in (allowed_runtime_classes or []):
        for v in class_vendor_backends(rc, runtime_classes=runtime_classes):
            add(v)
        add(local_fallback_backend(rc, runtime_classes=runtime_classes, policy_matrix=policy_matrix))
    if not out:
        add(offline_default_backend(policy_matrix))
    return out


__all__ = ["bind", "bind_allowed", "resolve_for_spec", "eligible_backends_for_classes", "class_record",
           "is_known_class", "class_vendor_backends", "local_fallback_backend", "offline_default_backend"]
