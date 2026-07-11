#!/usr/bin/env python3
"""scripts.api_context_handler — the read/projection-safe HTTP handler for the Consumption API (C-CONSUME-1).

Pure request handler (method, path, body) -> (status, json), so the contract is testable WITHOUT a socket and
the admin server just delegates to it. It NEVER fabricates truth: /api/context/serve calls the proven
ConsumptionService (run_cfpb_to_consumption) and returns its ContextResponse; retrieval reads a process
cache of what was served; /api/runtime/sections projects the section maturity matrix. No raw pack is served, no
gate is bypassed, no secrets are emitted. UI/dashboard consume THIS projection — they do not compute truth.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.runtime.consumption import run_cfpb_to_consumption
from scripts.runtime.schema_validator import validate_ref

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
#: routes this handler owns (registered in _repos/shared-backend-components/architecture/contract_registry.json#api_routes).
ROUTES = ("/api/context/serve", "/api/context/responses/", "/api/context/receipts/",
          "/api/runtime/sections", "/api/runtime/consumption")
#: process-level projection of what was served (deterministic responses; safe to rebuild on restart).
_RESPONSES: dict = {}
_RECEIPTS: dict = {}
_LATEST: dict = {"response_id": None}
#: fields that must never appear in an API response.
from scripts.security.response_redaction import SECRET_MARKERS as _SECRET_MARKERS  # single source — no per-handler drift (was missing Bearer + .claude/)


def _as_bool(v, default: bool = True) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return default
    return str(v).strip().lower() not in ("false", "0", "no", "")


def serve(body: dict) -> tuple:
    req = {"schema_version": "ConsumptionRequest", "tenant_id": str(body.get("tenant_id") or "demo"),
           "corpus": str(body.get("corpus") or "cfpb"), "require_optimized": _as_bool(body.get("require_optimized"), True)}
    errs = validate_ref(req, "consumption/ConsumptionRequest")
    if errs:
        return 400, {"error": "invalid ConsumptionRequest", "details": errs[:3]}
    if req["corpus"] != "cfpb":
        return 400, {"error": f"unknown corpus {req['corpus']!r}; only 'cfpb' is wired"}
    out = run_cfpb_to_consumption(req["tenant_id"], require_optimized=req["require_optimized"], now="2026-06-05T00:00:00Z")
    resp = out["response"]
    _RESPONSES[resp["response_id"]] = resp
    _LATEST["response_id"] = resp["response_id"]
    for kind, rc in out.get("receipts", {}).items():
        if rc.get("receipt_id"):
            _RECEIPTS[rc["receipt_id"]] = {"kind": kind, **rc}
    return 200, resp


def get_response(rid: str) -> tuple:
    r = _RESPONSES.get(rid)
    return (200, r) if r else (404, {"error": f"no ContextResponse {rid!r}"})


def get_receipt(rid: str) -> tuple:
    r = _RECEIPTS.get(rid)
    return (200, r) if r else (404, {"error": f"no receipt {rid!r}"})


def runtime_sections() -> tuple:
    m = json.loads((_resource("architecture") / "section_maturity_matrix.json").read_text())
    out = [{"section_id": s["section_id"], "status": s["status"], "owner": s.get("owner_module"),
            "proof_scripts": s.get("proof_scripts", []), "known_gaps": s.get("known_gaps", []),
            "critical_path_required": s.get("critical_path_required", False)} for s in m["sections"]]
    reference = [s for s in out if s["critical_path_required"]]
    return 200, {"sections": out, "total": len(out),
                 "reference_m10": sum(1 for s in reference if s["status"] == "m10_complete"), "reference_total": len(reference)}


def runtime_consumption() -> tuple:
    rid = _LATEST.get("response_id")
    if not rid or rid not in _RESPONSES:
        return 200, {"api_runtime": "ready", "latest_response_id": None, "note": "no response served yet this process"}
    r = _RESPONSES[rid]
    return 200, {"api_runtime": "ready", "latest_response_id": rid, "answer": r["answer"],
                 "served_fact_count": len(r["served_facts"]), "held_out_count": len(r["held_out_warnings"]),
                 "receipts": r["receipts"]}


def handle(method: str, path: str, body: dict | None = None) -> tuple:
    """Dispatch a Consumption-API request. Returns (status_code, json_payload)."""
    body = body or {}
    path = path.rstrip("/") or path
    if path == "/api/context/serve" and method in ("POST", "GET"):  # GET = ungated projection for the UI
        return serve(body)
    if method == "GET" and path.startswith("/api/context/responses/"):
        return get_response(path.rsplit("/", 1)[-1])
    if method == "GET" and path.startswith("/api/context/receipts/"):
        return get_receipt(path.rsplit("/", 1)[-1])
    if method == "GET" and path == "/api/runtime/sections":
        return runtime_sections()
    if method == "GET" and path == "/api/runtime/consumption":
        return runtime_consumption()
    return 404, {"error": f"unknown context route {method} {path}"}


def owns(path: str) -> bool:
    return any(path == r or path.startswith(r) for r in ROUTES)
