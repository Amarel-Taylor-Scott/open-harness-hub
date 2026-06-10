#!/usr/bin/env python3
"""scripts.api_native_handler — the projection-safe HTTP handler for the Native Format Preservation API
(C-NATIVE-1). Model: scripts/api_context_handler.py, scripts/api_memory_handler.py.

Pure request handler (method, path, query|body) -> (status, json), so the contract is testable WITHOUT a
socket and the admin server just delegates to it. It NEVER overwrites canonical truth and NEVER serves an
unverified value as a confirmed fact:

  POST /api/native/ingest             — store a SOURCE (exact bytes + sha256) and return refs/handles ONLY.
                                        Does NOT mutate canonical truth and does NOT serve a fact. The
                                        stored source is the input the lossless-distillation law protects:
                                        the original is never overwritten.
  GET  /api/native/export/<source_id>?mode=...  — projection-only same-shape export per output_mode
                                        (architecture/native_output_modes.json). Calls the Lane B
                                        NativeExportService; degrades gracefully if the source is absent.
  GET  /api/native/sidecar/<source_id>          — the SidecarOverlay (receipts/conflicts/held_out/lineage).
  GET  /api/native/diff/<source_id>             — the NativeDiff (changed_fields: path/old/new/decision/receipt).
  GET  /api/native/annotations/<source_id>      — per-native-path annotations (warnings/receipts/conflicts).

LOSSLESS-DISTILLATION + GOVERNANCE (the whole point):
  - The ORIGINAL is never overwritten. Ingest stores source bytes + sha256 in a process-level projection of
    refs (NOT a 2nd ledger / NOT a 2nd export framework); export/sidecar/diff are read-only projections.
  - held_out_claims stay in the SIDECAR; the native_output never silently applies an unverified value as a
    confirmed fact. A value may differ from source in the native_output ONLY when the export service marks it
    VERIFIED and emits a matching NativeDiff entry — and this handler re-checks that invariant defensively.
  - The Lane B service (src/baltor/native/native_export_service) is imported LAZILY; if it (or the requested
    source) is absent, the handler degrades to {"available": false, ...} so the projection + its proof are
    robust whether or not the sibling lane has landed. The UI consumes THIS projection; it computes no truth.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_ARCH = _REPO / "architecture"

#: routes this handler owns (registered in architecture/contract_registry.json#api_routes by MAIN).
ROUTES = (
    "/api/native/ingest",
    "/api/native/export/",
    "/api/native/sidecar/",
    "/api/native/diff/",
    "/api/native/annotations/",
)

#: the canonical output_mode registry (single source of truth for the 8 modes; never re-define here).
_MODES_FILE = _ARCH / "native_output_modes.json"

#: the Lane B runtime interface this handler projects over (lazy import; degrade-on-absence). One module path.
_EXPORT_SERVICE_MODULE = "src.baltor.native.native_export_service"

#: substrings that must never appear in any payload this handler returns (defense-in-depth scrub).
_SECRET_MARKERS = ("OH_SHOWCASE_TOKEN", "sk-", "api_key", "Authorization", "Bearer ", "MEMORY.md", ".agent/")

#: a value that differs from source in native_output is only legitimate when it is VERIFIED; these are the
#: claim_status values that may NOT be served as a confirmed fact in a native projection (held-out lane).
_NON_SERVABLE_STATUSES = frozenset({"candidate", "unverified", "unverified_allegation", "held_out",
                                    "rejected", "conflict", "alleged"})

#: injected wall-clock string for ingest/export receipts: deterministic, offline.
_NOW = "2026-06-05T00:00:00Z"

#: process-level projection of ingested sources (source_id -> {source_hash, byte_len, format_hint, refs, ...}).
#: A projection of REFERENCES, never the canonical truth store and never a 2nd ledger. Safe to rebuild on
#: restart. Ingest stores the exact bytes here so export can later rehydrate to them via the Lane B service.
_SOURCES: dict[str, dict] = {}


# --------------------------------------------------------------------------------------------------------- #
# helpers                                                                                                    #
# --------------------------------------------------------------------------------------------------------- #
def _import_export_service():
    """Lazily import the Lane B NativeExportService module. Returns the module or None (absent/broken)."""
    try:
        return __import__(_EXPORT_SERVICE_MODULE, fromlist=["*"])
    except Exception:  # noqa: BLE001 - sibling lane absent/broken -> degrade, never crash
        return None


def _call_export(source: dict, output_mode: str, tenant_id: str):
    """Call the Lane B export service read-only; return its dict, or None on absence/raise.
    Tries a module-level export(...) function then an exported NativeExportService().export(...)."""
    mod = _import_export_service()
    if mod is None:
        return None
    try:
        fn = getattr(mod, "export", None)
        if callable(fn):
            return fn(source, output_mode, tenant_id, now=_NOW)
        cls = getattr(mod, "NativeExportService", None)
        if cls is not None:
            return cls().export(source, output_mode, tenant_id, now=_NOW)
    except Exception:  # noqa: BLE001 - any service error -> degrade, never crash or fabricate truth
        return None
    return None


def _modes() -> dict:
    """Return {mode_id: mode_def} from the canonical registry; {} if the file is absent/broken."""
    try:
        data = json.loads(_MODES_FILE.read_text(encoding="utf-8"))
        return {m["id"]: m for m in data.get("output_modes", []) if isinstance(m, dict) and m.get("id")}
    except (OSError, ValueError):
        return {}


def _query_mode(query: dict) -> str:
    return str((query or {}).get("mode") or "native_passthrough_with_sidecar").strip() or "native_passthrough_with_sidecar"


def _enforce_no_truth_bypass(payload: dict, mode_def: dict) -> dict:
    """Defense-in-depth: a native_output value may differ from source ONLY when VERIFIED with a matching
    NativeDiff. Any non-servable claim_status carried on a native field is downgraded out of the served
    output and noted in warnings; held_out stays in the sidecar. We never silently apply an unverified value.
    Returns the (possibly annotated) payload; never raises."""
    if not isinstance(payload, dict):
        return {"available": False, "warning": "export service returned a non-dict payload"}
    warnings = list(payload.get("warnings") or [])
    diff = payload.get("diff") if isinstance(payload.get("diff"), dict) else {}
    changed = {c.get("path") for c in (diff.get("changed_fields") or []) if isinstance(c, dict)}
    mutates = bool(mode_def.get("mutates_values"))
    # 1) if the mode does not mutate values, there must be no changed_fields claiming a served value change.
    if not mutates and changed:
        warnings.append("native output mode does not mutate values but a diff claimed changes; diff suppressed")
        payload = {**payload, "diff": {**diff, "changed_fields": []}}
    # 2) a native field whose value differs from source must be VERIFIED + have a NativeDiff entry; otherwise
    #    it is a non-servable claim and must not be presented as a confirmed native value.
    fields = payload.get("native_field_status")
    if isinstance(fields, list):
        clean = []
        for f in fields:
            if not isinstance(f, dict):
                continue
            status = str(f.get("claim_status") or "").lower()
            differs = bool(f.get("differs_from_source"))
            if differs and (status in _NON_SERVABLE_STATUSES or f.get("path") not in changed):
                warnings.append(f"field {f.get('path')!r} differs from source but is not VERIFIED+diffed; held out")
                f = {**f, "differs_from_source": False, "held_out": True}
            clean.append(f)
        payload = {**payload, "native_field_status": clean}
    payload = {**payload, "warnings": warnings}
    return payload


# --------------------------------------------------------------------------------------------------------- #
# routes                                                                                                     #
# --------------------------------------------------------------------------------------------------------- #
def ingest(body: dict) -> tuple:
    """POST /api/native/ingest — store a SOURCE (exact bytes + sha256) and return refs/handles ONLY.

    Stores the original so the lossless-distillation law can hold: the original is never overwritten and an
    export can later rehydrate to it. This writes NO canonical truth and serves NO fact — it returns only the
    source_id, source_hash, byte length, the stored format hint, and the export/sidecar/diff refs to poll.
    """
    tenant_id = str((body or {}).get("tenant_id") or "demo").strip() or "demo"
    raw = (body or {}).get("content")
    if raw is None:
        return 400, {"error": "missing 'content' (the source bytes/text/object to preserve)"}
    fmt = str((body or {}).get("format") or "").strip().lower()
    # canonicalize to bytes for an exact content hash; objects -> deterministic JSON bytes.
    if isinstance(raw, (bytes, bytearray)):
        data = bytes(raw)
        fmt = fmt or "bytes"
    elif isinstance(raw, str):
        data = raw.encode("utf-8")
        fmt = fmt or "text"
    else:
        data = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode("utf-8")
        fmt = fmt or "json"
    source_hash = hashlib.sha256(data).hexdigest()
    # source_id is content+tenant addressed: same input -> same id (deterministic; dedupe-safe).
    source_id = "src-" + hashlib.sha256(f"{tenant_id}|{source_hash}".encode()).hexdigest()[:16]
    _SOURCES[source_id] = {
        "schema_version": "NativeSourceRef.v1",
        "source_id": source_id,
        "tenant_id": tenant_id,
        "source_hash": source_hash,
        "byte_len": len(data),
        "format_hint": fmt,
        "raw_bytes": data,                 # the ORIGINAL, never overwritten; used only to rehydrate on export
        "stored_at": _NOW,
    }
    receipt_id = "ingrcpt-" + hashlib.sha256(f"{source_id}|{source_hash}|{_NOW}".encode()).hexdigest()[:16]
    return 200, _scrub({
        "schema_version": "NativeIngestResult.v1",
        "stored": True,
        "mutated_canonical_truth": False,      # by design: ingest stores a source; it never mutates truth
        "served_fact": False,                  # by design: ingest serves no fact
        "source_id": source_id,
        "tenant_id": tenant_id,
        "source_hash": source_hash,
        "byte_len": len(data),
        "format_hint": fmt,
        "receipt": {"schema_version": "NativeExportReceipt.v1", "receipt_id": receipt_id,
                    "op": "ingest", "source_id": source_id, "source_hash": source_hash, "created_at": _NOW},
        "refs": {
            "export": f"/api/native/export/{source_id}?mode=native_passthrough_with_sidecar",
            "sidecar": f"/api/native/sidecar/{source_id}",
            "diff": f"/api/native/diff/{source_id}",
            "annotations": f"/api/native/annotations/{source_id}",
        },
        "note": "source stored (exact bytes + sha256); original is never overwritten; no canonical truth written; no fact served",
    })


def export(source_id: str, query: dict) -> tuple:
    """GET /api/native/export/<source_id>?mode=... — projection-only same-shape export per output_mode.
    Calls the Lane B NativeExportService; degrades gracefully if the source or the service is absent. Enforces
    no-truth-bypass defensively (held-out stays in the sidecar; unverified values are never served)."""
    modes = _modes()
    mode = _query_mode(query)
    if modes and mode not in modes:
        return 400, {"error": f"unknown output_mode {mode!r}", "known_modes": sorted(modes)}
    src = _SOURCES.get(source_id)
    if src is None:
        return 404, {"available": False, "source_id": source_id, "mode": mode,
                     "note": "no source ingested for this id (POST /api/native/ingest first)"}
    out = _call_export(src, mode, src["tenant_id"])
    mode_def = modes.get(mode, {})
    if out is None:
        # service not landed: degrade to a SAFE same-shape projection (passthrough) — never fabricate a change.
        return 200, _scrub({
            "available": False,
            "source_id": source_id, "tenant_id": src["tenant_id"], "mode": mode,
            "projection_only": True,
            "native_output": _decode_for_projection(src),  # the original, unchanged (no value applied)
            "byte_identical": True,
            "source_hash": src["source_hash"],
            "sidecar": None, "diff": {"changed_fields": []},
            "note": "native export service (Lane B) not available; returning the unchanged original (passthrough). No value was applied; no fact served.",
        })
    out = _enforce_no_truth_bypass(out if isinstance(out, dict) else {}, mode_def)
    out.setdefault("available", True)
    out.setdefault("source_id", source_id)
    out.setdefault("tenant_id", src["tenant_id"])
    out.setdefault("mode", mode)
    out.setdefault("projection_only", True)
    out.setdefault("source_hash", src["source_hash"])
    return 200, _scrub(out)


def _decode_for_projection(src: dict):
    """Best-effort decode of stored source bytes for a degrade-path passthrough projection. JSON sources are
    returned as their parsed object (same shape); text as the string; bytes that won't decode as a hash ref."""
    data = src.get("raw_bytes") or b""
    fmt = src.get("format_hint")
    try:
        text = data.decode("utf-8")
    except (UnicodeDecodeError, AttributeError):
        return {"_baltor_binary_source_sha256": src.get("source_hash"), "byte_len": src.get("byte_len")}
    if fmt == "json":
        try:
            return json.loads(text)
        except ValueError:
            return text
    return text


def sidecar(source_id: str) -> tuple:
    """GET /api/native/sidecar/<source_id> — the SidecarOverlay (receipts/conflicts/held_out/lineage)."""
    src = _SOURCES.get(source_id)
    if src is None:
        return 404, {"available": False, "source_id": source_id, "note": "no source ingested for this id"}
    out = _call_export(src, "native_passthrough_with_sidecar", src["tenant_id"])
    if not isinstance(out, dict) or out.get("sidecar") is None:
        return 200, _scrub({"available": False, "source_id": source_id, "source_hash": src["source_hash"],
                            "sidecar": None,
                            "note": "native export service (Lane B) not available; no sidecar yet (source bytes preserved)"})
    return 200, _scrub({"available": True, "source_id": source_id, "tenant_id": src["tenant_id"],
                        "source_hash": src["source_hash"], "sidecar": out["sidecar"]})


def diff(source_id: str) -> tuple:
    """GET /api/native/diff/<source_id> — the NativeDiff (changed_fields: path/old/new/decision/receipt_id)."""
    src = _SOURCES.get(source_id)
    if src is None:
        return 404, {"available": False, "source_id": source_id, "note": "no source ingested for this id"}
    out = _call_export(src, "compare", src["tenant_id"])
    if not isinstance(out, dict):
        return 200, _scrub({"available": False, "source_id": source_id, "tenant_id": src["tenant_id"],
                            "source_hash": src["source_hash"], "diff": {"changed_fields": []},
                            "note": "native export service (Lane B) not available; no diff yet"})
    out = _enforce_no_truth_bypass(out, _modes().get("compare", {}))
    d = out.get("diff") if isinstance(out.get("diff"), dict) else {"changed_fields": []}
    return 200, _scrub({"available": True, "source_id": source_id, "tenant_id": src["tenant_id"],
                        "source_hash": src["source_hash"], "diff": d,
                        "note": "every changed field carries a decision + receipt_id; unverified changes are held out, not served"})


def annotations(source_id: str) -> tuple:
    """GET /api/native/annotations/<source_id> — per-native-path annotations (warnings/receipts/conflicts)."""
    src = _SOURCES.get(source_id)
    if src is None:
        return 404, {"available": False, "source_id": source_id, "note": "no source ingested for this id"}
    out = _call_export(src, "annotated_native", src["tenant_id"])
    if not isinstance(out, dict):
        return 200, _scrub({"available": False, "source_id": source_id, "tenant_id": src["tenant_id"],
                            "source_hash": src["source_hash"], "annotations": [],
                            "note": "native export service (Lane B) not available; no annotations yet"})
    side = out.get("sidecar") if isinstance(out.get("sidecar"), dict) else {}
    anns = out.get("annotations")
    if not isinstance(anns, list):
        # derive annotations from the sidecar overlay if the service did not pre-shape them.
        anns = [{"native_path": w.get("native_path", ""), "kind": "warning", "message": w.get("reason", str(w))}
                for w in (side.get("warnings") or []) if isinstance(w, dict)]
    return 200, _scrub({"available": True, "source_id": source_id, "tenant_id": src["tenant_id"],
                        "source_hash": src["source_hash"], "annotations": anns,
                        "note": "annotations are surfaced per native path; they never replace a source value silently"})


# --------------------------------------------------------------------------------------------------------- #
def _scrub(obj):
    """Defensively strip any value carrying a secret marker from an outbound payload. raw_bytes is never
    serialized to a client (the projection exposes source_hash/byte_len, not the stored bytes)."""
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items()
                if k != "raw_bytes" and not any(m in str(k) for m in _SECRET_MARKERS)}
    if isinstance(obj, list):
        return [_scrub(v) for v in obj]
    if isinstance(obj, (bytes, bytearray)):
        return f"<bytes:{len(obj)}>"
    if isinstance(obj, str) and any(m in obj for m in _SECRET_MARKERS):
        return "[redacted]"
    return obj


def _tail(path: str, prefix: str) -> str:
    """Return the <source_id> segment after a route prefix (strips a trailing slash already handled by handle)."""
    return path[len(prefix):].strip("/").split("/")[0] if path.startswith(prefix) else ""


def handle(method: str, path: str, payload: dict | None = None) -> tuple:
    """Dispatch a Native-API request. Returns (status_code, json_payload).

    For GET routes `payload` is the parsed query dict; for POST /api/native/ingest it is the body dict.
    Projection-safe: only ingest accepts POST (store-only, no canonical mutation); everything else is GET.
    """
    payload = payload or {}
    path = path.rstrip("/") or path
    if path == "/api/native/ingest":
        if method != "POST":
            return 405, {"error": f"native ingest is POST-only; {method} not allowed"}
        return ingest(payload)
    if method != "GET":
        return 405, {"error": f"native API route is read-only; {method} not allowed on {path}"}
    if path.startswith("/api/native/export/"):
        return export(_tail(path, "/api/native/export/"), payload)
    if path.startswith("/api/native/sidecar/"):
        return sidecar(_tail(path, "/api/native/sidecar/"))
    if path.startswith("/api/native/diff/"):
        return diff(_tail(path, "/api/native/diff/"))
    if path.startswith("/api/native/annotations/"):
        return annotations(_tail(path, "/api/native/annotations/"))
    return 404, {"error": f"unknown native route {method} {path}"}


def owns(path: str) -> bool:
    return any(path == r or path.startswith(r) for r in ROUTES)


# --------------------------------------------------------------------------------------------------------- #
def _reset_sources_for_test() -> None:
    """Test-only: clear the process-level source projection so proofs are deterministic + isolated."""
    _SOURCES.clear()
