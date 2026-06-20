"""src.teleon.seeds.openapi_deconstructor — deconstruct an API endpoint SPEC (OpenAPI — how RapidAPI and every API
hub describes its endpoints) into a Teleon capability SEED candidate.

This is the governed, offline, deterministic core of "browse an API hub and turn each endpoint into a capability".
Each OpenAPI operation (method + path + params + auth + response schema) becomes a candidate capability seed with
an input/output contract and a high determinism ceiling — because an API call IS a deterministic call (the
distiller's ``direct_api_rule`` strategy: the capability already IS the call, so wrap it). The result feeds the
normal candidate pipeline (gap/lift screen → human/eval gates → promotion); nothing is promoted here.

The LIVE harvest of a hub's catalog (e.g. Playwright driving the owner's authenticated browser session over
RapidAPI) is a real-network + owner-credential seam — OWNER-LAUNCHED and out of scope for this offline module; it
has a built local equivalent in ``local_emulators.rapidapi_hub_emulator`` (the DEFER GATE) so the deconstruct →
seed pipeline is fully testable offline. serves_truth is always False — a deconstructed endpoint is a candidate.
"""
from __future__ import annotations

import re

_HTTP_METHODS = ("get", "post", "put", "delete", "patch")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-") or "endpoint"


def _base_url(doc: dict) -> str:
    servers = doc.get("servers") or []
    if servers and isinstance(servers[0], dict):
        return str(servers[0].get("url", "")).rstrip("/")
    return ""


def _auth_required(doc: dict, op: dict) -> bool:
    return bool(op.get("security") or doc.get("security")
                or (doc.get("components") or {}).get("securitySchemes"))


def _params(op: dict) -> list[str]:
    return [str(p.get("name")) for p in (op.get("parameters") or []) if isinstance(p, dict) and p.get("name")]


def deconstruct_operation(method: str, path: str, op: dict, *, api_name: str, base_url: str,
                          doc: dict, hub: str = "rapidapi") -> dict:
    """One OpenAPI operation → a governed capability-seed candidate (with input/output contract + the endpoint)."""
    op_id = op.get("operationId") or f"{method}-{path}"
    slot = f"{_slug(api_name)}.{_slug(op_id)}"
    resp200 = ((op.get("responses") or {}).get("200") or (op.get("responses") or {}).get("default") or {})
    out_schema = (((resp200.get("content") or {}).get("application/json") or {}).get("schema")) or resp200.get("schema")
    return {
        "capability_slot": slot,
        "intent": op.get("summary") or op.get("description") or f"{method.upper()} {path}",
        "input_contract": {"path_query_params": _params(op), "has_request_body": bool(op.get("requestBody"))},
        "output_contract": {"has_200_schema": out_schema is not None,
                            "schema_type": (out_schema or {}).get("type") if isinstance(out_schema, dict) else None},
        "method": method.upper(), "path": path, "endpoint": (base_url.rstrip("/") + path) if base_url else path,
        "hub": hub, "auth_required": _auth_required(doc, op), "cost_model": "per_call",
        "source_kind": "rest_api", "category": "other",
        # an API call IS a deterministic call → wrap it (distiller STRATEGY_DIRECT_API_RULE); high determinism ceiling.
        "determinism_ceiling": 0.95, "distill_strategy": "direct_api_rule",
        "gap_hypothesis": (f"a base model cannot CALL {api_name} {method.upper()} {path} or return its live data "
                           f"from parametric memory; wrapping the endpoint is the capability"),
        "governed": "candidate", "serves_truth": False,
    }


def deconstruct_api(doc: dict, *, api_name: str | None = None, hub: str = "rapidapi") -> list[dict]:
    """Deconstruct a whole OpenAPI document → one capability-seed candidate per operation. Deterministic + offline."""
    name = api_name or (doc.get("info") or {}).get("title") or "api"
    base = _base_url(doc)
    seeds: list[dict] = []
    for path, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() in _HTTP_METHODS and isinstance(op, dict):
                seeds.append(deconstruct_operation(method.lower(), path, op, api_name=name, base_url=base,
                                                   doc=doc, hub=hub))
    return sorted(seeds, key=lambda s: s["capability_slot"])


def deconstruct_hub(specs: dict, *, hub: str = "rapidapi") -> list[dict]:
    """Deconstruct a hub's worth of OpenAPI docs ({api_name: openapi_doc}) → all capability-seed candidates."""
    out: list[dict] = []
    for api_name in sorted(specs):
        out.extend(deconstruct_api(specs[api_name], api_name=api_name, hub=hub))
    return out
