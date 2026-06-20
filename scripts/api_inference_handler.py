#!/usr/bin/env python3
"""scripts.api_inference_handler — the read/projection-safe HTTP handler for the Shared LLM Plane (/api/inference/*).

Pure request handler (method, path, body) -> (status, json), so the contract is testable WITHOUT a socket and the
admin server just delegates to it. It is a PROJECTION over src/teleon/inference (the Inference Gateway / OIPS): the
GET routes expose the provider graph, free-endpoint due-diligence, preference coverage, health and recorded receipts;
POST resolve-preference is a pure derivation; POST structured-local executes the deterministic LOCAL STUB and returns
a ModelInvocationReceipt — its model output is a CANDIDATE, never served truth. No raw key/secret is ever emitted;
errors are ErrorEnvelope.v1. UI/dashboard consume THIS projection — they do not compute truth.
"""
from __future__ import annotations

import json
import os
import re

from src.teleon.inference import api_projection as ap
from src.teleon.inference import oips

#: routes this handler owns (registered in architecture/contract_registry.json#api_routes; structured-local is the
#: compute route — registered separately when its live wiring lands, kept honest by the proof).
ROUTES = ("/api/inference/providers", "/api/inference/model-graph", "/api/inference/free-endpoints",
          "/api/inference/preferences", "/api/inference/health", "/api/inference/receipts",
          "/api/inference/resolve-preference", "/api/inference/structured-local")
#: process-level projection of receipts produced by structured-local calls (deterministic; safe to rebuild).
_RECEIPTS: dict = {}
#: deterministic demo clock (the plane never reads wall-clock; callers may override with body["now"]).
_DEMO_NOW = "2026-06-05T00:00:00Z"
#: Secret VALUE / internal-path patterns that must NEVER appear in a response (defense-in-depth over the projection's
#: own redaction). NB: we scan for secret VALUE SHAPES, not descriptive words — a free-endpoint due-diligence report
#: may legitimately say "requires api_key" / "Authorization header"; only a real key/token value is a leak. The
#: projection also legitimately exposes a `has_secret_ref` BOOLEAN — never the ref string itself.
_LEAK = re.compile(r"(sk-[A-Za-z0-9]{8,}|gsk_[A-Za-z0-9]{8,}|secret://[^\"\s]*?:[^\"\s]+|Bearer\s+[A-Za-z0-9._-]{12,}"
                   r"|OH_SHOWCASE_TOKEN=|/\.agent/|MEMORY\.md)")


def _err(error_type: str, message: str, *, retryable: bool = False) -> dict:
    return ap.error_envelope(error_type, message, retryable=retryable, error_id="inf_api_err")


def _guard(payload: dict) -> tuple:
    """Final safety scan: no secret VALUE may leak into a response. Fail closed if one does."""
    if _LEAK.search(json.dumps(payload)):
        return 500, _err("secret_leak_blocked", "response withheld: contained a forbidden secret-value pattern")
    return 200, payload


def _get(path: str) -> tuple:
    if path == "/api/inference/providers":
        return _guard({"providers": ap.providers()})
    if path == "/api/inference/model-graph":
        return _guard(ap.model_graph())
    if path == "/api/inference/free-endpoints":
        return _guard({"free_endpoints": ap.free_endpoints()})
    if path == "/api/inference/preferences":
        return _guard(ap.preferences_coverage())
    if path == "/api/inference/health":
        return _guard({"health": ap.health()})
    if path == "/api/inference/receipts":
        return _guard({"receipts": ap.receipts(list(_RECEIPTS.values()))})
    return 404, _err("not_found", f"no inference route {path!r}")


def _post(path: str, body: dict) -> tuple:
    if path == "/api/inference/resolve-preference":
        layers = body.get("layers") or body.get("preference_layers")
        if not isinstance(layers, list) or not layers:
            return 400, _err("invalid_request", "expected a non-empty 'layers' list of InferencePreference layers")
        return _guard(ap.resolve_preference(layers))
    if path == "/api/inference/structured-local":
        layers = body.get("preference_layers") or body.get("layers")
        if not isinstance(layers, list) or not layers:
            return 400, _err("invalid_request", "expected a non-empty 'preference_layers' list")
        out = oips.infer_local(object_id=str(body.get("object_id") or "demo.object"),
                               preference_layers=layers, input_text=str(body.get("input_text") or ""),
                               now=str(body.get("now") or _DEMO_NOW),
                               # owner-authorized live model execution (.env switch); otherwise the
                               # deterministic stub runs and the receipt says so — never fabricated
                               allow_network=os.environ.get("OH_INFERENCE_ALLOW_NETWORK", "") == "1")
        rc = out["receipt"]
        if rc.get("receipt_id"):
            _RECEIPTS[rc["receipt_id"]] = rc
        # the model output is a CANDIDATE, never served truth — say so explicitly in the projection.
        return _guard({"receipt": rc, "route_decision": out["route_decision"],
                       "candidate_output": out["output"], "is_truth": False,
                       "note": "LOCAL-STUB output is a candidate, never served truth; the ModelInvocationReceipt records what actually executed"})
    return 404, _err("not_found", f"no inference route {path!r}")


def handle(method: str, path: str, body: dict | None = None) -> tuple:
    path = (path or "").rstrip("/") or "/"
    body = body or {}
    try:
        if method == "GET":
            return _get(path)
        if method == "POST":
            return _post(path, body)
        return 405, _err("method_not_allowed", f"{method} not supported on {path!r}")
    except Exception as exc:  # never leak a stack/secret; fail closed with an ErrorEnvelope
        return 500, _err("inference_error", f"{type(exc).__name__}: {str(exc)[:120]}")


__all__ = ["ROUTES", "handle"]
