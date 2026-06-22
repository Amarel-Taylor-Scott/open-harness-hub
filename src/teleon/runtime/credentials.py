"""src.teleon.runtime.credentials — the credential PLANE: which external services are reachable given the present keys.

Single source = architecture/credential_registry.json (env-var NAMES only, never values). The descent calls
reachable()/missing_for() to pick the cheapest tool that meets the bar AND is reachable, and to say honestly WHICH key
would unlock a blocked path ("needs OH_LIBRARIESIO_KEY") instead of fabricating a result. Reads os.environ first, then a
local .env. Complements SecretRef.v1 (resolves a name to a value at runtime) + the service-auth model. serves_truth=false;
Teleon layer — never imports src.baltor.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_REGISTRY = _REPO / "architecture" / "credential_registry.json"


@lru_cache(maxsize=1)
def _services() -> list[dict]:
    return json.loads(_REGISTRY.read_text(encoding="utf-8"))["services"]


def _dotenv() -> dict[str, str]:
    f = _REPO / ".env"
    out: dict[str, str] = {}
    if f.exists():
        for ln in f.read_text(encoding="utf-8").splitlines():
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _env_value(name: str, env: dict | None) -> str:
    if env is not None:
        return str(env.get(name, "")).strip()
    return (os.environ.get(name) or _dotenv().get(name) or "").strip()


def is_present(service_id: str, env: dict | None = None) -> bool:
    """A service is PRESENT when all of its env vars are set (keyless services are present even with none set)."""
    svc = next((s for s in _services() if s["id"] == service_id), None)
    if not svc:
        return False
    if svc.get("keyless"):
        return True
    return bool(svc["env_vars"]) and all(_env_value(v, env) for v in svc["env_vars"])


def reachable(env: dict | None = None) -> set[str]:
    """Service ids reachable right now (keyless OR all env vars present)."""
    return {s["id"] for s in _services() if is_present(s["id"], env)}


def reachable_planes(env: dict | None = None) -> set[str]:
    """Tool-planes unlocked by the present credentials (a plane is reachable if any service that unlocks it is present)."""
    out: set[str] = set()
    for s in _services():
        if is_present(s["id"], env):
            out.update(s.get("unlocks", {}).get("planes", []))
    return out


def missing_for(service_id: str, env: dict | None = None) -> list[str]:
    """The env vars still needed to reach a service ([] if reachable). For honest 'needs X' messages."""
    svc = next((s for s in _services() if s["id"] == service_id), None)
    if not svc or is_present(service_id, env):
        return []
    return [v for v in svc["env_vars"] if not _env_value(v, env)]


def services_for_tool(tool_id: str) -> list[str]:
    """Which credential service(s) unlock a given tool_registry/ocr tool (for the descent's reachability check)."""
    return [s["id"] for s in _services() if tool_id in s.get("unlocks", {}).get("tools", [])]


def status(env: dict | None = None) -> dict:
    """A governed snapshot: reachable services, unlocked planes, and the keyless-vs-keyed split (no secret values)."""
    svcs = _services()
    reach = reachable(env)
    return {
        "reachable": sorted(reach),
        "blocked": sorted(s["id"] for s in svcs if s["id"] not in reach),
        "planes_unlocked": sorted(reachable_planes(env)),
        "keyless": sorted(s["id"] for s in svcs if s.get("keyless")),
        "serves_truth": False,
    }
