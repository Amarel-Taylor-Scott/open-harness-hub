#!/usr/bin/env python3
"""scripts.api_determinism_handler — the read/projection-safe HTTP handler for the Determinism API.

Pure request handler (method, path, query) -> (status, json), so the contract is testable WITHOUT a socket and
the admin server just delegates to it (model: scripts/api_context_handler.py, scripts/api_memory_handler.py).
It PROJECTS the whole Determinism Factory motion built by ``src.baltor.determinism.demo.build_demo`` — LLM
proposals + multi-model consensus recorded as EVIDENCE, the EXISTING authority's VERIFIED traces, the mined
PatternCandidate, the proposed RuleCandidate, the replay + shadow reports, the promotion gate receipt (and the
tenant_private→global BLOCK), and the deterministic-first serving + recorded fallback.

It NEVER mutates durable truth: it reads ``build_demo()`` (an in-memory, deterministic, offline run of the real
engine) and returns its artifacts read-only. The build is cached per process (a coherent projection across the
nine routes in one page load; rebuilt on restart — a projection cache, never a durable truth store). It serves
NO secret. The UI/dashboard consume THIS projection; they compute no truth.

  GET /api/determinism/overview     — stage counts + the REFERENCE assertion (Reg E "10 business days" wins)
  GET /api/determinism/traces       — every trace (llm + consensus + verified + tenant_private), verified flag
  GET /api/determinism/consensus    — the ConsensusRun (EVIDENCE; can_serve_fact permanently False)
  GET /api/determinism/patterns     — mined PatternCandidate(s) (verified-only; lossless support_trace_ids)
  GET /api/determinism/rules        — proposed RuleCandidate(s) (active=False; lossless distilled_from_trace_ids)
  GET /api/determinism/replay       — the RuleReplayReport (precision, unsafe_count, tenant_leak_count)
  GET /api/determinism/shadow       — the ShadowRunReport (live stayed authoritative; unsafe mismatch count)
  GET /api/determinism/promotions   — the RulePromotionReceipt + the BLOCKED tenant_private→global counter-case
  GET /api/determinism/fallback     — RoutingEvents (rule-served deterministically + OOD fallback; never fabricated)
"""
from __future__ import annotations

import json

#: routes this handler owns (registered in architecture/contract_registry.json#api_routes by MAIN).
ROUTES = (
    "/api/determinism/overview",
    "/api/determinism/traces",
    "/api/determinism/consensus",
    "/api/determinism/patterns",
    "/api/determinism/rules",
    "/api/determinism/replay",
    "/api/determinism/shadow",
    "/api/determinism/promotions",
    "/api/determinism/fallback",
)

#: the injected, deterministic wall-clock for the projected demo (offline; no clock read).
_NOW = "2026-06-05T00:00:00Z"

#: substrings that must never appear in any payload this handler returns.
from scripts.security.response_redaction import SECRET_MARKERS as _SECRET_MARKERS  # single source — no per-handler drift

#: deterministic per-process projection cache. The demo is pure + offline + deterministic, so caching it makes
#: the nine routes coherent within a page load. It is a projection cache (rebuilt on restart), never durable truth.
_CACHE: dict = {"demo": None}


def _build():
    """Return the cached projection dict (build it once per process). Degrades to None if the engine is absent."""
    if _CACHE["demo"] is None:
        try:
            from src.baltor.determinism.demo import build_demo
        except Exception:  # noqa: BLE001 - engine absent/broken -> degrade, never crash
            return None
        try:
            _CACHE["demo"] = build_demo(now=_NOW)
        except Exception:  # noqa: BLE001 - any engine error -> degrade gracefully
            return None
    return _CACHE["demo"]


def _scrub(obj):
    """Defensively strip any value carrying a secret marker from an outbound payload."""
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items() if not any(m in str(k) for m in _SECRET_MARKERS)}
    if isinstance(obj, list):
        return [_scrub(v) for v in obj]
    if isinstance(obj, str) and any(m in obj for m in _SECRET_MARKERS):
        return "[redacted]"
    return obj


def _degraded(section: str) -> tuple:
    """A graceful-degrade payload when the engine could not produce the projection (still 200, never a crash)."""
    return 200, {"available": False, "section": section,
                 "note": "determinism engine not available; projection degraded (no truth computed)"}


def _project(section: str) -> tuple:
    """Project one section of the demo read-only. Returns (200, scrubbed_payload) or a graceful-degrade payload."""
    demo = _build()
    if not isinstance(demo, dict) or section not in demo:
        return _degraded(section)
    payload = demo[section]
    out = _scrub(payload if isinstance(payload, dict) else {"value": payload})
    if isinstance(out, dict):
        out.setdefault("available", True)
    return 200, out


def handle(method: str, path: str, query: dict | None = None) -> tuple:
    """Dispatch a Determinism-API request. Returns (status_code, json_payload). Projection-only; GET-only."""
    _ = query  # all sections are deterministic projections; no query parameter changes the served truth
    path = path.rstrip("/") or path
    if method != "GET":
        return 405, {"error": f"determinism API is read-only; {method} not allowed on {path}"}
    if not owns(path):
        return 404, {"error": f"unknown determinism route {method} {path}"}
    section = path.rsplit("/", 1)[-1]   # the trailing path segment is the section key
    return _project(section)


def owns(path: str) -> bool:
    return any(path == r or path.startswith(r) for r in ROUTES)


if __name__ == "__main__":  # tiny manual smoke (not the proof — see scripts/check_determinism_api.py)
    for r in ROUTES:
        code, body = handle("GET", r)
        print(code, r, sorted(body)[:6])
    json.dumps(handle("GET", "/api/determinism/overview")[1])  # ensure JSON-serializable
