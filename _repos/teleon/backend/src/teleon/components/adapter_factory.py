"""adapter_factory — the component-agnostic seam's force-multiplier. Don't onboard components one at a time; write
FACTORIES that turn whole ecosystems into components. from_openapi(spec) emits one typed component per endpoint, with I/O
types inferred from the schema — collapsing the N×M integration problem to N+M (ToolRegistry/MCP's thesis). The HTTP
invoke is network-gated + honest offline (never a fabricated response). serves_truth=false.
"""
from __future__ import annotations

py_var_src_teleon_components_adapter_factory___VERBS = ("get", "post", "put", "delete", "patch")


def py_function_src_teleon_components_adapter_factory___infer_in_types(py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__infer_in_types__op: dict) -> list:
    """Request → our type vocabulary: a body object is a `record`; query/path params alone are a `query`."""
    py_local_src_teleon_components_adapter_factory__infer_in_types__types = []
    if py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__infer_in_types__op.get("requestBody"):
        py_local_src_teleon_components_adapter_factory__infer_in_types__types.append("record")
    py_local_src_teleon_components_adapter_factory__infer_in_types__params = py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__infer_in_types__op.get("parameters") or []
    if py_local_src_teleon_components_adapter_factory__infer_in_types__params and "record" not in py_local_src_teleon_components_adapter_factory__infer_in_types__types:
        py_local_src_teleon_components_adapter_factory__infer_in_types__types.append("query")
    return py_local_src_teleon_components_adapter_factory__infer_in_types__types


def py_function_src_teleon_components_adapter_factory___infer_out_types(py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__infer_out_types__op: dict) -> list:
    """Response → our type vocabulary: JSON object/array is a `record`; a bare string is `text`; default `record`."""
    py_local_src_teleon_components_adapter_factory__infer_out_types__resp = (py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__infer_out_types__op.get("responses") or {})
    for py_local_src_teleon_components_adapter_factory__infer_out_types__code in ("200", "201", "default"):
        py_local_src_teleon_components_adapter_factory__infer_out_types__content = (py_local_src_teleon_components_adapter_factory__infer_out_types__resp.get(py_local_src_teleon_components_adapter_factory__infer_out_types__code) or {}).get("content") or {}
        py_local_src_teleon_components_adapter_factory__infer_out_types__sch = (py_local_src_teleon_components_adapter_factory__infer_out_types__content.get("application/json") or {}).get("schema") or {}
        py_local_src_teleon_components_adapter_factory__infer_out_types__t = py_local_src_teleon_components_adapter_factory__infer_out_types__sch.get("type")
        if py_local_src_teleon_components_adapter_factory__infer_out_types__t == "string":
            return ["text"]
        if py_local_src_teleon_components_adapter_factory__infer_out_types__t in ("object", "array") or py_local_src_teleon_components_adapter_factory__infer_out_types__sch:
            return ["record"]
    return ["record"]


def py_function_src_teleon_components_adapter_factory___op_id(py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__op_id__method: str, py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__op_id__path: str, py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__op_id__op: dict) -> str:
    if py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__op_id__op.get("operationId"):
        return py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__op_id__op["operationId"]
    py_local_src_teleon_components_adapter_factory__op_id__slug = py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__op_id__path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
    return f"{py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__op_id__method.lower()}_{py_local_src_teleon_components_adapter_factory__op_id__slug or 'root'}"


def py_function_src_teleon_components_adapter_factory__from_openapi(py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__from_openapi__spec: dict, *, py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__from_openapi__default_plane: str = "external_api") -> list:
    """One typed component descriptor per operation in an OpenAPI spec. Each: {component_id, plane, method, path,
    base_url, consumes, produces, deterministic, source}. A whole API becomes components in ONE call."""
    py_local_src_teleon_components_adapter_factory__from_openapi__base = ((py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__from_openapi__spec.get("servers") or [{}])[0] or {}).get("url", "")
    py_local_src_teleon_components_adapter_factory__from_openapi__comps = []
    for py_local_src_teleon_components_adapter_factory__from_openapi__path, py_local_src_teleon_components_adapter_factory__from_openapi__methods in (py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__from_openapi__spec.get("paths") or {}).items():
        for py_local_src_teleon_components_adapter_factory__from_openapi__method, py_local_src_teleon_components_adapter_factory__from_openapi__op in (py_local_src_teleon_components_adapter_factory__from_openapi__methods or {}).items():
            if py_local_src_teleon_components_adapter_factory__from_openapi__method.lower() not in py_var_src_teleon_components_adapter_factory___VERBS or not isinstance(py_local_src_teleon_components_adapter_factory__from_openapi__op, dict):
                continue
            py_local_src_teleon_components_adapter_factory__from_openapi__comps.append({"component_id": py_function_src_teleon_components_adapter_factory___op_id(py_local_src_teleon_components_adapter_factory__from_openapi__method, py_local_src_teleon_components_adapter_factory__from_openapi__path, py_local_src_teleon_components_adapter_factory__from_openapi__op), "plane": py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__from_openapi__default_plane, "method": py_local_src_teleon_components_adapter_factory__from_openapi__method.upper(),
                          "path": py_local_src_teleon_components_adapter_factory__from_openapi__path, "base_url": py_local_src_teleon_components_adapter_factory__from_openapi__base, "consumes": py_function_src_teleon_components_adapter_factory___infer_in_types(py_local_src_teleon_components_adapter_factory__from_openapi__op), "produces": py_function_src_teleon_components_adapter_factory___infer_out_types(py_local_src_teleon_components_adapter_factory__from_openapi__op),
                          "deterministic": False, "source": "openapi", "serves_truth": False})
    return py_local_src_teleon_components_adapter_factory__from_openapi__comps


def py_function_src_teleon_components_adapter_factory__http_invoke(py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__http_invoke__descriptor: dict, py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__http_invoke__inputs: dict, *, network_allowed=None, py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__http_invoke__timeout: int = 20) -> dict:
    """Invoke an OpenAPI-derived component (the live path). Network-gated + honest: offline it returns an honest
    'unavailable' — never a fabricated response."""
    if network_allowed is None:
        from src.teleon.dag.real_steps import network_allowed as _net
        network_allowed = _net()
    if not network_allowed:
        return {"available": False, "reason": "needs network (honest offline) — no fabricated API response",
                "component": py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__http_invoke__descriptor.get("component_id"), "serves_truth": False}
    import json
    import urllib.request
    py_local_src_teleon_components_adapter_factory__http_invoke__url = (py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__http_invoke__descriptor.get("base_url", "") or "") + py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__http_invoke__descriptor.get("path", "")
    py_local_src_teleon_components_adapter_factory__http_invoke__body = json.dumps(py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__http_invoke__inputs).encode() if py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__http_invoke__inputs and py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__http_invoke__descriptor.get("method") in ("POST", "PUT", "PATCH") else None
    py_local_src_teleon_components_adapter_factory__http_invoke__req = urllib.request.Request(py_local_src_teleon_components_adapter_factory__http_invoke__url, data=py_local_src_teleon_components_adapter_factory__http_invoke__body, method=py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__http_invoke__descriptor.get("method", "GET"),
                                 headers={"Content-Type": "application/json"} if py_local_src_teleon_components_adapter_factory__http_invoke__body else {})
    try:
        with urllib.request.urlopen(py_local_src_teleon_components_adapter_factory__http_invoke__req, timeout=py_arg_src_teleon_components_adapter_factory__py_function_src_teleon_components_adapter_factory__http_invoke__timeout) as py_local_src_teleon_components_adapter_factory__http_invoke__r:
            return {"available": True, "record": json.loads(py_local_src_teleon_components_adapter_factory__http_invoke__r.read().decode()), "serves_truth": False}
    except Exception as py_local_src_teleon_components_adapter_factory__http_invoke__e:  # noqa: BLE001
        return {"available": True, "error": f"{type(py_local_src_teleon_components_adapter_factory__http_invoke__e).__name__}: {py_local_src_teleon_components_adapter_factory__http_invoke__e}", "serves_truth": False}
