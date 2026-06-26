#!/usr/bin/env python3
"""scripts.api_{{area}}_handler — projection-safe HTTP handler for {{title}} ({{route_path}}).

GENERATED STUB (standard.api_projection). Pure request handler (method, path, body) -> (status, json) so
the contract is testable WITHOUT a socket; the admin server delegates to it (MAIN wires the server). It NEVER
fabricates truth: it calls the proven engine and returns its {{returns_contract}}; it is projection-only
(computes no truth, bypasses no gate) and emits NO secret markers.

TODO(stub): wire `serve` to the real engine call and return its {{returns_contract}}.
"""
from __future__ import annotations

#: routes this handler owns (MAIN registers in architecture/contract_registry.json#api_routes).
ROUTES = ("{{route_path}}",)
RETURNS_CONTRACT = "{{returns_contract}}"

#: fields/markers that must NEVER appear in a response (projection-only, no secret leakage).
_SECRET_MARKERS = ("OH_SHOWCASE_TOKEN", "sk-", "api_key", "Authorization", "MEMORY.md", ".agent/")


def _has_secret_marker(obj) -> bool:
    return any(m in repr(obj) for m in _SECRET_MARKERS)


def serve(body: dict) -> tuple:
    """Projection only: call the proven engine and RETURN its {{returns_contract}}. Compute no truth here."""
    # TODO(stub): from scripts.runtime.<engine> import <run_fn>; resp = <run_fn>(...); return 200, resp
    raise NotImplementedError(
        "api_{{area}}_handler.serve is a generated stub — call the proven engine and return {{returns_contract}}"
    )


def handle(method: str, path: str, body: dict) -> tuple:
    """(method, path, body) -> (status, json). Socket-free contract surface."""
    if path == "{{route_path}}":
        status, payload = serve(body or {})
        if _has_secret_marker(payload):  # defense-in-depth: never emit a secret marker
            return 500, {"error": "projection guard: secret marker in response"}
        return status, payload
    return 404, {"error": f"no route {path!r} on api_{{area}}_handler"}
