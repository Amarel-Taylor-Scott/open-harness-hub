"""src.teleon.runtime.credentials — the credential PLANE: which external services are reachable given the present keys.

Single source = _repos/shared-backend-components/architecture/credential_registry.json (env-var NAMES only, never values). The descent calls
reachable()/missing_for() to pick the cheapest tool that meets the bar AND is reachable, and to say honestly WHICH key
would unlock a blocked path ("needs OH_LIBRARIESIO_KEY") instead of fabricating a result. Reads os.environ first, then a
local .env. Complements SecretRef (resolves a name to a value at runtime) + the service-auth model. serves_truth=false;
Teleon layer — never imports src.baltor.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
from functools import lru_cache
from pathlib import Path

py_var_src_teleon_runtime_credentials___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
py_var_src_teleon_runtime_credentials___REGISTRY = _resource("architecture") / "credential_registry.json"


@lru_cache(maxsize=1)
def py_function_src_teleon_runtime_credentials___services() -> list[dict]:
    return json.loads(py_var_src_teleon_runtime_credentials___REGISTRY.read_text(encoding="utf-8"))["services"]


def py_function_src_teleon_runtime_credentials__services() -> list[dict]:
    """Public, read-only view of the credential registry slots (env-var NAMES + metadata, never values).
    The Global Operations Console reads this to render its API-keys view; callers must NOT resolve values."""
    return py_function_src_teleon_runtime_credentials___services()


def py_function_src_teleon_runtime_credentials___dotenv() -> dict[str, str]:
    py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__f = py_var_src_teleon_runtime_credentials___REPO / ".env"
    py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__out: dict[str, str] = {}
    if py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__f.exists():
        for py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__ln in py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__f.read_text(encoding="utf-8").splitlines():
            if "=" in py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__ln and not py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__ln.lstrip().startswith("#"):
                py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__k, py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__v = py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__ln.split("=", 1)
                py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__out[py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__k.strip()] = py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__v.strip().strip('"').strip("'")
    return py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__dotenv__out


def py_function_src_teleon_runtime_credentials___env_value(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__env_value__name: str, py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__env_value__env: dict | None) -> str:
    if py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__env_value__env is not None:
        return str(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__env_value__env.get(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__env_value__name, "")).strip()
    return (os.environ.get(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__env_value__name) or py_function_src_teleon_runtime_credentials___dotenv().get(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__env_value__name) or "").strip()


def py_function_src_teleon_runtime_credentials__env_value(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__env_value__name: str, py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__env_value__env: dict | None = None) -> str:
    """Resolve a single env-var VALUE (os.environ then .env). Used by the key holder — callers must NOT log the result."""
    return py_function_src_teleon_runtime_credentials___env_value(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__env_value__name, py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__env_value__env)


def py_function_src_teleon_runtime_credentials__is_present(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__is_present__service_id: str, py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__is_present__env: dict | None = None) -> bool:
    """A service is PRESENT when all of its env vars are set (keyless services are present even with none set)."""
    py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__is_present__svc = next((s for s in py_function_src_teleon_runtime_credentials___services() if s["id"] == py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__is_present__service_id), None)
    if not py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__is_present__svc:
        return False
    if py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__is_present__svc.get("keyless"):
        return True
    return bool(py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__is_present__svc["env_vars"]) and all(py_function_src_teleon_runtime_credentials___env_value(v, py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__is_present__env) for v in py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__is_present__svc["env_vars"])


def py_function_src_teleon_runtime_credentials__reachable(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__reachable__env: dict | None = None) -> set[str]:
    """Service ids reachable right now (keyless OR all env vars present)."""
    return {s["id"] for s in py_function_src_teleon_runtime_credentials___services() if py_function_src_teleon_runtime_credentials__is_present(s["id"], py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__reachable__env)}


def py_function_src_teleon_runtime_credentials__reachable_planes(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__reachable_planes__env: dict | None = None) -> set[str]:
    """Tool-planes unlocked by the present credentials (a plane is reachable if any service that unlocks it is present)."""
    py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__reachable_planes__out: set[str] = set()
    for py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__reachable_planes__s in py_function_src_teleon_runtime_credentials___services():
        if py_function_src_teleon_runtime_credentials__is_present(py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__reachable_planes__s["id"], py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__reachable_planes__env):
            py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__reachable_planes__out.update(py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__reachable_planes__s.get("unlocks", {}).get("planes", []))
    return py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__reachable_planes__out


def py_function_src_teleon_runtime_credentials__missing_for(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__missing_for__service_id: str, py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__missing_for__env: dict | None = None) -> list[str]:
    """The env vars still needed to reach a service ([] if reachable). For honest 'needs X' messages."""
    py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__missing_for__svc = next((s for s in py_function_src_teleon_runtime_credentials___services() if s["id"] == py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__missing_for__service_id), None)
    if not py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__missing_for__svc or py_function_src_teleon_runtime_credentials__is_present(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__missing_for__service_id, py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__missing_for__env):
        return []
    return [v for v in py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__missing_for__svc["env_vars"] if not py_function_src_teleon_runtime_credentials___env_value(v, py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__missing_for__env)]


def py_function_src_teleon_runtime_credentials__services_for_tool(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__services_for_tool__tool_id: str) -> list[str]:
    """Which credential service(s) unlock a given tool_registry/ocr tool (for the descent's reachability check)."""
    return [s["id"] for s in py_function_src_teleon_runtime_credentials___services() if py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__services_for_tool__tool_id in s.get("unlocks", {}).get("tools", [])]


def py_function_src_teleon_runtime_credentials___svc(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__svc__service_id: str) -> dict | None:
    return next((s for s in py_function_src_teleon_runtime_credentials___services() if s["id"] == py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__svc__service_id), None)


def py_function_src_teleon_runtime_credentials__credential_kind(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__credential_kind__service_id: str) -> str:
    """The credential KIND (api_key default | git_token | deploy_token | oauth | deploy_key | webhook_secret | signing_key)."""
    py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__credential_kind__s = py_function_src_teleon_runtime_credentials___svc(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__credential_kind__service_id)
    return (py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__credential_kind__s.get("kind", "api_key") if py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__credential_kind__s else "api_key")


def py_function_src_teleon_runtime_credentials__services_by_kind(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__services_by_kind__kind: str) -> list[str]:
    return [s["id"] for s in py_function_src_teleon_runtime_credentials___services() if s.get("kind", "api_key") == py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__services_by_kind__kind]


def py_function_src_teleon_runtime_credentials__key_ownership(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_ownership__service_id: str) -> str:
    """How a service's key may be supplied: 'byo' (tenant pastes their own) | 'platform' (our shared key within limits) |
    'both'. Mirrors compute key-ownership (see byo-compute)."""
    py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_ownership__s = py_function_src_teleon_runtime_credentials___svc(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_ownership__service_id)
    return py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_ownership__s.get("key_ownership", "byo") if py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_ownership__s else "byo"


def py_function_src_teleon_runtime_credentials__platform_limits(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__platform_limits__service_id: str) -> dict | None:
    """The cap when using OUR key (None if byo-only). The runtime meters against this; here we expose it for the descent."""
    py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__platform_limits__s = py_function_src_teleon_runtime_credentials___svc(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__platform_limits__service_id)
    return py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__platform_limits__s.get("platform_limits") if py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__platform_limits__s else None


def py_function_src_teleon_runtime_credentials__key_mode(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_mode__service_id: str, py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_mode__env: dict | None = None, *, byo: set | None = None) -> str | None:
    """Resolve HOW this service is usable right now: 'byo' (the tenant supplied a key — preferred, no platform cap),
    'platform' (our shared key/keyless, used WITHIN platform_limits), or None (blocked: no key + byo-only or not present).
    `byo` = the set of service ids the tenant brought their own key for."""
    py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_mode__own = py_function_src_teleon_runtime_credentials__key_ownership(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_mode__service_id)
    if byo and py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_mode__service_id in byo and py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_mode__own in ("byo", "both"):
        return "byo"
    if py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_mode__own in ("platform", "both") and py_function_src_teleon_runtime_credentials__is_present(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_mode__service_id, py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_mode__env):
        return "platform"
    if py_local_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_mode__own == "byo" and py_function_src_teleon_runtime_credentials__is_present(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_mode__service_id, py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__key_mode__env):
        return "byo"            # the present key IS a byo key in single-tenant/dev
    return None


def py_function_src_teleon_runtime_credentials__status(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__status__env: dict | None = None) -> dict:
    """A governed snapshot: reachable services, unlocked planes, and the keyless-vs-keyed split (no secret values)."""
    py_local_src_teleon_runtime_credentials__status__svcs = py_function_src_teleon_runtime_credentials___services()
    py_local_src_teleon_runtime_credentials__status__reach = py_function_src_teleon_runtime_credentials__reachable(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__status__env)
    return {
        "reachable": sorted(py_local_src_teleon_runtime_credentials__status__reach),
        "blocked": sorted(s["id"] for s in py_local_src_teleon_runtime_credentials__status__svcs if s["id"] not in py_local_src_teleon_runtime_credentials__status__reach),
        "planes_unlocked": sorted(py_function_src_teleon_runtime_credentials__reachable_planes(py_arg_src_teleon_runtime_credentials__py_function_src_teleon_runtime_credentials__status__env)),
        "keyless": sorted(s["id"] for s in py_local_src_teleon_runtime_credentials__status__svcs if s.get("keyless")),
        "byo_only": sorted(s["id"] for s in py_local_src_teleon_runtime_credentials__status__svcs if s.get("key_ownership") == "byo"),
        "platform_capable": sorted(s["id"] for s in py_local_src_teleon_runtime_credentials__status__svcs if s.get("key_ownership") in ("platform", "both")),
        "serves_truth": False,
    }
