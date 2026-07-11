"""src.teleon.runtime.entitlements — bridge the registries to the access policy: build resource dicts + filter by principal.

access_policy.classify() is pure (takes a resource dict); THIS assembles that dict for a real tool / credential / DAG rung
from the registries (its plane, whether a credential key unlocks it, the rung's governance) so the key holder + the descent
can ask `can_access(principal, ...)`. A principal only ever resolves keys + selects tools they're ENTITLED to. serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from functools import lru_cache
from pathlib import Path

from src.teleon.runtime import access_policy as AP
from src.teleon.runtime import credentials as C

py_var_src_teleon_runtime_entitlements___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
#: stealth/undetected browser ids (governed evasion) — selecting one is restricted even though it's not a tool_registry row
py_var_src_teleon_runtime_entitlements___EVASION_TOOLS = {"undetected_chromedriver", "nodriver", "patchright", "seleniumbase", "botasaurus"}


@lru_cache(maxsize=1)
def py_function_src_teleon_runtime_entitlements___tool_planes() -> dict:
    return {t["id"]: t.get("plane") for t in json.loads((_resource("architecture") / "tool_registry.json").read_text())["tools"]}


def py_function_src_teleon_runtime_entitlements__tool_resource(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__tool_id: str, *, plane: str | None = None, governance: str | None = None) -> dict:
    """A resource dict for a tool: its plane, the governance in force (the rung's, or evasion/social inferred), and the
    credential key that unlocks it (if any) -> so access_policy can tier it."""
    plane = plane or py_function_src_teleon_runtime_entitlements___tool_planes().get(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__tool_id)
    py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__svcs = C.py_function_src_teleon_runtime_credentials__services_for_tool(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__tool_id)
    py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__own = C.py_function_src_teleon_runtime_credentials__key_ownership(py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__svcs[0]) if py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__svcs else None
    py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__gov = governance or ("evasion_restricted" if py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__tool_id in py_var_src_teleon_runtime_entitlements___EVASION_TOOLS else ("social" if plane == "social_scrape" else None))
    return {"id": py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__tool_id, "plane": plane, "governance": py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__gov, "key_ownership": py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__own,
            "key_service": (py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__svcs[0] if py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__svcs else None), "keyless": not py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__tool_resource__svcs, "deterministic": True}


def py_function_src_teleon_runtime_entitlements__credential_resource(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__credential_resource__service_id: str) -> dict:
    py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__credential_resource__svc = C.py_function_src_teleon_runtime_credentials___svc(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__credential_resource__service_id) or {}
    return {"id": py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__credential_resource__service_id, "key_ownership": py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__credential_resource__svc.get("key_ownership", "byo"), "key_service": py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__credential_resource__service_id,
            "keyless": bool(py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__credential_resource__svc.get("keyless"))}      # a keyless service (e.g. github unauth) is public — usable by anyone


def py_function_src_teleon_runtime_entitlements__entitled_key(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__entitled_key__principal, py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__entitled_key__service_id: str) -> bool:
    return AP.py_function_src_teleon_runtime_access_policy__can_access(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__entitled_key__principal, py_function_src_teleon_runtime_entitlements__credential_resource(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__entitled_key__service_id))[0]


def py_function_src_teleon_runtime_entitlements__entitled_tools(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__entitled_tools__principal, py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__entitled_tools__tool_ids, *, plane: str | None = None, governance: str | None = None) -> list[str]:
    """The subset of tool ids the principal may use (plane/governance carry the rung's context)."""
    return [t for t in py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__entitled_tools__tool_ids if AP.py_function_src_teleon_runtime_access_policy__can_access(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__entitled_tools__principal, py_function_src_teleon_runtime_entitlements__tool_resource(t, plane=plane, governance=governance))[0]]


def py_function_src_teleon_runtime_entitlements__gate_options(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__principal, py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__options, *, plane=None, governance=None) -> list[str]:
    """Filter a DAG node's options to the entitled ones; if NONE are entitled, return an HONEST blocked sentinel naming
    why (so the synthesis tree records a real dead-end rather than silently dropping the node)."""
    if py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__principal is None:
        return list(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__options)
    py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__allowed = py_function_src_teleon_runtime_entitlements__entitled_tools(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__principal, py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__options, plane=plane, governance=governance)
    if py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__allowed:
        return py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__allowed
    # nothing entitled -> name the tier/grant needed (from the first option's classification)
    py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__req = AP.py_function_src_teleon_runtime_access_policy__classify(py_function_src_teleon_runtime_entitlements__tool_resource(py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__options[0], plane=plane, governance=governance)) if py_arg_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__options else {"tier": "?"}
    py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__need = py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__req.get("grant") or py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__req.get("tier")
    return [f"blocked:needs-{py_local_src_teleon_runtime_entitlements__py_function_src_teleon_runtime_entitlements__gate_options__need}"]
