"""src.teleon.runtime.entitlements — bridge the registries to the access policy: build resource dicts + filter by principal.

access_policy.classify() is pure (takes a resource dict); THIS assembles that dict for a real tool / credential / DAG rung
from the registries (its plane, whether a credential key unlocks it, the rung's governance) so the key holder + the descent
can ask `can_access(principal, ...)`. A principal only ever resolves keys + selects tools they're ENTITLED to. serves_truth=false.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from src.teleon.runtime import access_policy as AP
from src.teleon.runtime import credentials as C

_REPO = Path(__file__).resolve().parents[3]
#: stealth/undetected browser ids (governed evasion) — selecting one is restricted even though it's not a tool_registry row
_EVASION_TOOLS = {"undetected_chromedriver", "nodriver", "patchright", "seleniumbase", "botasaurus"}


@lru_cache(maxsize=1)
def _tool_planes() -> dict:
    return {t["id"]: t.get("plane") for t in json.loads((_REPO / "architecture" / "tool_registry.json").read_text())["tools"]}


def tool_resource(tool_id: str, *, plane: str | None = None, governance: str | None = None) -> dict:
    """A resource dict for a tool: its plane, the governance in force (the rung's, or evasion/social inferred), and the
    credential key that unlocks it (if any) -> so access_policy can tier it."""
    plane = plane or _tool_planes().get(tool_id)
    svcs = C.services_for_tool(tool_id)
    own = C.key_ownership(svcs[0]) if svcs else None
    gov = governance or ("evasion_restricted" if tool_id in _EVASION_TOOLS else ("social" if plane == "social_scrape" else None))
    return {"id": tool_id, "plane": plane, "governance": gov, "key_ownership": own,
            "key_service": (svcs[0] if svcs else None), "keyless": not svcs, "deterministic": True}


def credential_resource(service_id: str) -> dict:
    svc = C._svc(service_id) or {}
    return {"id": service_id, "key_ownership": svc.get("key_ownership", "byo"), "key_service": service_id,
            "keyless": bool(svc.get("keyless"))}      # a keyless service (e.g. github unauth) is public — usable by anyone


def entitled_key(principal, service_id: str) -> bool:
    return AP.can_access(principal, credential_resource(service_id))[0]


def entitled_tools(principal, tool_ids, *, plane: str | None = None, governance: str | None = None) -> list[str]:
    """The subset of tool ids the principal may use (plane/governance carry the rung's context)."""
    return [t for t in tool_ids if AP.can_access(principal, tool_resource(t, plane=plane, governance=governance))[0]]


def gate_options(principal, options, *, plane=None, governance=None) -> list[str]:
    """Filter a DAG node's options to the entitled ones; if NONE are entitled, return an HONEST blocked sentinel naming
    why (so the synthesis tree records a real dead-end rather than silently dropping the node)."""
    if principal is None:
        return list(options)
    allowed = entitled_tools(principal, options, plane=plane, governance=governance)
    if allowed:
        return allowed
    # nothing entitled -> name the tier/grant needed (from the first option's classification)
    req = AP.classify(tool_resource(options[0], plane=plane, governance=governance)) if options else {"tier": "?"}
    need = req.get("grant") or req.get("tier")
    return [f"blocked:needs-{need}"]
