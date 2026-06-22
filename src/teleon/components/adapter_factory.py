"""adapter_factory — the component-agnostic seam's force-multiplier. Don't onboard components one at a time; write
FACTORIES that turn whole ecosystems into components. from_openapi(spec) emits one typed component per endpoint, with I/O
types inferred from the schema — collapsing the N×M integration problem to N+M (ToolRegistry/MCP's thesis). The HTTP
invoke is network-gated + honest offline (never a fabricated response). serves_truth=false.
"""
from __future__ import annotations

_VERBS = ("get", "post", "put", "delete", "patch")


def _infer_in_types(op: dict) -> list:
    """Request → our type vocabulary: a body object is a `record`; query/path params alone are a `query`."""
    types = []
    if op.get("requestBody"):
        types.append("record")
    params = op.get("parameters") or []
    if params and "record" not in types:
        types.append("query")
    return types


def _infer_out_types(op: dict) -> list:
    """Response → our type vocabulary: JSON object/array is a `record`; a bare string is `text`; default `record`."""
    resp = (op.get("responses") or {})
    for code in ("200", "201", "default"):
        content = (resp.get(code) or {}).get("content") or {}
        sch = (content.get("application/json") or {}).get("schema") or {}
        t = sch.get("type")
        if t == "string":
            return ["text"]
        if t in ("object", "array") or sch:
            return ["record"]
    return ["record"]


def _op_id(method: str, path: str, op: dict) -> str:
    if op.get("operationId"):
        return op["operationId"]
    slug = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
    return f"{method.lower()}_{slug or 'root'}"


def from_openapi(spec: dict, *, default_plane: str = "external_api") -> list:
    """One typed component descriptor per operation in an OpenAPI spec. Each: {component_id, plane, method, path,
    base_url, consumes, produces, deterministic, source}. A whole API becomes components in ONE call."""
    base = ((spec.get("servers") or [{}])[0] or {}).get("url", "")
    comps = []
    for path, methods in (spec.get("paths") or {}).items():
        for method, op in (methods or {}).items():
            if method.lower() not in _VERBS or not isinstance(op, dict):
                continue
            comps.append({"component_id": _op_id(method, path, op), "plane": default_plane, "method": method.upper(),
                          "path": path, "base_url": base, "consumes": _infer_in_types(op), "produces": _infer_out_types(op),
                          "deterministic": False, "source": "openapi", "serves_truth": False})
    return comps


def http_invoke(descriptor: dict, inputs: dict, *, network_allowed=None, timeout: int = 20) -> dict:
    """Invoke an OpenAPI-derived component (the live path). Network-gated + honest: offline it returns an honest
    'unavailable' — never a fabricated response."""
    if network_allowed is None:
        from src.teleon.dag.real_steps import network_allowed as _net
        network_allowed = _net()
    if not network_allowed:
        return {"available": False, "reason": "needs network (honest offline) — no fabricated API response",
                "component": descriptor.get("component_id"), "serves_truth": False}
    import json
    import urllib.request
    url = (descriptor.get("base_url", "") or "") + descriptor.get("path", "")
    body = json.dumps(inputs).encode() if inputs and descriptor.get("method") in ("POST", "PUT", "PATCH") else None
    req = urllib.request.Request(url, data=body, method=descriptor.get("method", "GET"),
                                 headers={"Content-Type": "application/json"} if body else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"available": True, "record": json.loads(r.read().decode()), "serves_truth": False}
    except Exception as e:  # noqa: BLE001
        return {"available": True, "error": f"{type(e).__name__}: {e}", "serves_truth": False}
