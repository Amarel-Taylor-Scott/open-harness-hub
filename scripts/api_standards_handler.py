#!/usr/bin/env python3
"""scripts.api_standards_handler — the read/projection-safe HTTP handler for the Standards API.

Pure request handler (method, path, body) -> (status, json), so the contract is testable WITHOUT a socket
and the admin server just delegates to it (model: scripts/api_context_handler.py). This layer is a
PROJECTION over the standards-system truth files produced by sibling lanes:

  GET  /api/standards/patterns            <- architecture/pattern_registry.json
  GET  /api/standards/templates           <- architecture/template_catalog.json
  GET  /api/standards/routines            <- architecture/routine_library.json
  GET  /api/standards/waivers             <- architecture/pattern_waivers.json
  GET  /api/standards/maturity            <- architecture/pattern_maturity_matrix.json
  POST /api/standards/generate-preview    -> DRY-RUN plan of what WOULD be generated (NO files written)

It NEVER mutates truth, NEVER writes files, NEVER serves secrets or private memory. The truth files are
produced by other lanes; this handler reads them at call time and degrades gracefully (returns
{"available": false, ...}) when a file is absent — so the projection (and its proof) is robust whether or
not the sibling lanes have landed yet. The UI consumes THIS projection; it computes no truth.
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_ARCH = _REPO / "architecture"

#: routes this handler owns (registered in architecture/contract_registry.json#api_routes by MAIN).
ROUTES = (
    "/api/standards/patterns",
    "/api/standards/templates",
    "/api/standards/routines",
    "/api/standards/waivers",
    "/api/standards/maturity",
    "/api/standards/generate-preview",
)

#: truth files this projection reads (produced by sibling lanes; read at call time, never written here).
_SOURCES = {
    "patterns": _ARCH / "pattern_registry.json",
    "templates": _ARCH / "template_catalog.json",
    "routines": _ARCH / "routine_library.json",
    "waivers": _ARCH / "pattern_waivers.json",
    "maturity": _ARCH / "pattern_maturity_matrix.json",
}

#: a standards generator module a sibling lane MAY land; we import it lazily and degrade if absent.
_GENERATOR_CANDIDATES = ("scripts.standards_generator", "scripts.pattern_generator")

#: substrings that must never appear in any payload this handler returns.
from scripts.security.response_redaction import SECRET_MARKERS as _SECRET_MARKERS  # single source — no per-handler drift (was missing Bearer + .claude/)


def _read_json(path: Path) -> tuple[bool, object, str]:
    """Read+parse a truth file. Returns (available, data, error). Never raises; never writes."""
    if not path.exists():
        return False, None, f"{path.name} not produced yet"
    try:
        return True, json.loads(path.read_text(encoding="utf-8")), ""
    except (OSError, ValueError) as exc:  # malformed / unreadable -> degrade, don't crash
        return False, None, f"{path.name} unreadable: {exc}"


def _as_list(data: object, *keys: str) -> list:
    """Pull a list off a dict under the first matching key, or treat a top-level list as the list itself."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in keys:
            v = data.get(k)
            if isinstance(v, list):
                return v
    return []


def patterns() -> tuple:
    """GET /api/standards/patterns — project the pattern registry (id, name, status, examples count)."""
    available, data, err = _read_json(_SOURCES["patterns"])
    if not available:
        return 200, {"available": False, "patterns": [], "total": 0, "note": err}
    items = _as_list(data, "patterns", "pattern_registry")
    out = []
    for p in items:
        if not isinstance(p, dict):
            continue
        out.append({
            "pattern_id": p.get("pattern_id") or p.get("id"),
            "name": p.get("name") or p.get("title"),
            "status": p.get("status"),
            "category": p.get("category") or p.get("stage"),
            "example_count": len(_as_list(p.get("examples"))) if p.get("examples") is not None else p.get("example_count"),
            "examples": [str(e) for e in _as_list(p.get("examples"))][:25],
        })
    return 200, {"available": True, "patterns": out, "total": len(out)}


def templates() -> tuple:
    """GET /api/standards/templates — project the template catalog."""
    available, data, err = _read_json(_SOURCES["templates"])
    if not available:
        return 200, {"available": False, "templates": [], "total": 0, "note": err}
    items = _as_list(data, "templates", "template_catalog")
    out = []
    for t in items:
        if not isinstance(t, dict):
            continue
        out.append({
            "template_id": t.get("template_id") or t.get("id"),
            "name": t.get("name") or t.get("title"),
            "pattern_id": t.get("pattern_id"),
            "produces": t.get("produces") or t.get("output_kind"),
            "status": t.get("status"),
        })
    return 200, {"available": True, "templates": out, "total": len(out)}


def routines() -> tuple:
    """GET /api/standards/routines — project the routine library."""
    available, data, err = _read_json(_SOURCES["routines"])
    if not available:
        return 200, {"available": False, "routines": [], "total": 0, "note": err}
    items = _as_list(data, "routines", "routine_library")
    out = []
    for r in items:
        if not isinstance(r, dict):
            continue
        out.append({
            "routine_id": r.get("routine_id") or r.get("id"),
            "name": r.get("name") or r.get("title"),
            "steps": _as_list(r.get("steps")),
            "patterns": _as_list(r.get("patterns"), "pattern_ids"),
            "status": r.get("status"),
        })
    return 200, {"available": True, "routines": out, "total": len(out)}


def waivers() -> tuple:
    """GET /api/standards/waivers — project active pattern waivers (why a target is exempted)."""
    available, data, err = _read_json(_SOURCES["waivers"])
    if not available:
        return 200, {"available": False, "waivers": [], "total": 0, "note": err}
    items = _as_list(data, "waivers", "pattern_waivers")
    out = []
    for w in items:
        if not isinstance(w, dict):
            continue
        out.append({
            "waiver_id": w.get("waiver_id") or w.get("id"),
            "pattern_id": w.get("pattern_id"),
            "target": w.get("target") or w.get("path"),
            "reason": w.get("reason") or w.get("rationale"),
            "expires": w.get("expires") or w.get("expiry"),
        })
    return 200, {"available": True, "waivers": out, "total": len(out)}


def maturity() -> tuple:
    """GET /api/standards/maturity — project the pattern maturity matrix."""
    available, data, err = _read_json(_SOURCES["maturity"])
    if not available:
        return 200, {"available": False, "patterns": [], "total": 0, "note": err}
    items = _as_list(data, "patterns", "pattern_maturity", "rows")
    out = []
    for m in items:
        if not isinstance(m, dict):
            continue
        out.append({
            "pattern_id": m.get("pattern_id") or m.get("id"),
            "status": m.get("status") or m.get("maturity"),
            "adoption": m.get("adoption") or m.get("conformance"),
            "example_count": m.get("example_count"),
            "known_gaps": _as_list(m.get("known_gaps")),
        })
    return 200, {"available": True, "patterns": out, "total": len(out)}


def generate_preview(body: dict) -> tuple:
    """POST /api/standards/generate-preview — DRY-RUN: return what WOULD be generated, writing NO files.

    Tries a sibling-lane generator's dry-run first; if none is present, builds a deterministic plan from the
    pattern registry + template catalog. EITHER WAY this is projection-only: it computes a plan and returns
    it. It MUST NOT touch the filesystem, the truth files, or any durable store.
    """
    pattern_id = str((body or {}).get("pattern_id") or "").strip()
    template_id = str((body or {}).get("template_id") or "").strip()
    target = str((body or {}).get("target") or (body or {}).get("name") or "").strip()

    # 1) Prefer a sibling-lane generator's own dry-run, if it has landed. Import lazily; degrade on absence.
    for modname in _GENERATOR_CANDIDATES:
        try:
            mod = __import__(modname, fromlist=["*"])
        except Exception:  # noqa: BLE001 - any import failure (absent / broken) -> fall through to local plan
            continue
        fn = getattr(mod, "generate_preview", None) or getattr(mod, "preview", None) or getattr(mod, "dry_run", None)
        if callable(fn):
            try:
                plan = fn(pattern_id=pattern_id, template_id=template_id, target=target) \
                    if _accepts_kwargs(fn) else fn(body or {})
            except Exception as exc:  # noqa: BLE001 - never let a sibling crash break the projection
                return 200, {"dry_run": True, "available": False, "generator": modname,
                             "note": f"generator raised: {exc}", "would_create": []}
            return 200, {"dry_run": True, "available": True, "generator": modname,
                         "would_create": _scrub(plan)}

    # 2) No generator yet -> build a deterministic local plan from the registry + template catalog (read-only).
    pavail, pdata, _ = _read_json(_SOURCES["patterns"])
    tavail, tdata, _ = _read_json(_SOURCES["templates"])
    if not (pavail and tavail):
        return 200, {"dry_run": True, "available": False, "would_create": [],
                     "note": "pattern_registry.json / template_catalog.json not produced yet"}
    pat = next((p for p in _as_list(pdata, "patterns") if isinstance(p, dict)
                and (p.get("pattern_id") or p.get("id")) == pattern_id), None)
    tmpl = next((t for t in _as_list(tdata, "templates") if isinstance(t, dict)
                 and (t.get("template_id") or t.get("id")) == template_id), None)
    if pat is None or tmpl is None:
        return 400, {"dry_run": True, "error": "unknown pattern_id or template_id",
                     "pattern_id": pattern_id, "template_id": template_id}
    produces = tmpl.get("produces") or tmpl.get("output_kind") or "file"
    safe_target = target or f"<{produces}>"
    would_create = [{
        "path": f"{tmpl.get('target_dir', 'scripts')}/{safe_target}",
        "from_template": template_id,
        "for_pattern": pattern_id,
        "produces": produces,
        "written": False,  # DRY-RUN: nothing is written
    }]
    return 200, {"dry_run": True, "available": True, "generator": "local-plan",
                 "would_create": _scrub(would_create)}


def _accepts_kwargs(fn) -> bool:
    try:
        import inspect
        params = inspect.signature(fn).parameters
        return any(p in params for p in ("pattern_id", "template_id", "target"))
    except (TypeError, ValueError):
        return False


def _scrub(obj):
    """Defensively strip any value carrying a secret marker from an outbound payload."""
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items()
                if not any(m in str(k) for m in _SECRET_MARKERS)}
    if isinstance(obj, list):
        return [_scrub(v) for v in obj]
    if isinstance(obj, str) and any(m in obj for m in _SECRET_MARKERS):
        return "[redacted]"
    return obj


def handle(method: str, path: str, body: dict | None = None) -> tuple:
    """Dispatch a Standards-API request. Returns (status_code, json_payload). Projection-only."""
    body = body or {}
    path = path.rstrip("/") or path
    if method == "GET":
        if path == "/api/standards/patterns":
            return patterns()
        if path == "/api/standards/templates":
            return templates()
        if path == "/api/standards/routines":
            return routines()
        if path == "/api/standards/waivers":
            return waivers()
        if path == "/api/standards/maturity":
            return maturity()
    if method == "POST" and path == "/api/standards/generate-preview":
        return generate_preview(body)
    # GET on the preview path is a convenience read-only projection (UI may want a default plan).
    if method == "GET" and path == "/api/standards/generate-preview":
        return generate_preview(body)
    return 404, {"error": f"unknown standards route {method} {path}"}


def owns(path: str) -> bool:
    return any(path == r or path.startswith(r) for r in ROUTES)
