#!/usr/bin/env python3
"""scripts.api_memory_handler — the read/projection-safe HTTP handler for the Memory API (C-MEM-1).

Pure request handler (method, path, body) -> (status, json), so the contract is testable WITHOUT a socket
and the admin server just delegates to it (model: scripts/api_context_handler.py, scripts/api_standards_handler.py).
This layer is a PROJECTION over the governed memory providers behind the MemoryProviderPort (src/baltor/
adapters/memory): the deterministic Supermemory EMULATOR is the offline critical-path impl, the Baltor-local
store is the local provider, and the Supermemory api/mcp adapters are CANDIDATE contract stubs. It NEVER
serves canonical truth and NEVER writes (no `write`/mutation — read-only `search`/`profile`/`status` only).

GOVERNANCE (the whole point):
  - A recall result is a CANDIDATE MemoryArtifact (claim_status="candidate"), NOT a served/canonical fact. A
    MemoryArtifact only becomes a CanonicalFact through Baltor's VerificationGate + Reconciliation +
    ConsumptionGate (the Consumption API). remembered != verified; retrieved != served; profiled != canonical.
  - Every MemoryArtifact carries tenant_id + project/container scope + an external_source_handle (the upstream
    id) + lineage. No cross-tenant leakage (the provider is scope-local; we ALSO post-filter by tenant).
  - Lossless: a projection never deletes/overwrites raw; held_out != deleted. We only PROJECT what the
    provider exposes; we never mutate the provider or write canonical truth.

  GET /api/memory/artifacts     — candidate MemoryArtifacts (claim_status=candidate; source handles; lineage)
  GET /api/memory/profile       — governed profile: provider static/dynamic (CANDIDATE) + promoted (consumption)
  GET /api/memory/search        — read-only recall over the local/emulator provider (?q=&tenant_id=&project=)
  GET /api/memory/connectors    — candidate connector list (GDrive/Gmail/Notion/... behind the SourceAdapterPort)
  GET /api/memory/providers     — MemoryProviderStatus list (emulator / local / supermemory candidate)
  GET /api/memory/traces        — MemoryTraces (every provider call is recorded; offline, deterministic)

The provider modules are produced by sibling lanes; this handler imports them LAZILY and degrades gracefully
(returns {"available": false, ...}) when absent — so the projection (and its proof) is robust whether or not
the sibling lanes have landed, and the CORRECTNESS INVARIANT runs with NO credentials. The UI consumes THIS projection;
it computes no truth.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_ARCH = _REPO / "architecture"

#: routes this handler owns (registered in architecture/contract_registry.json#api_routes by MAIN).
ROUTES = (
    "/api/memory/artifacts",
    "/api/memory/profile",
    "/api/memory/search",
    "/api/memory/connectors",
    "/api/memory/providers",
    "/api/memory/traces",
)

#: the canonical claim_status of anything that comes off a memory provider. NEVER "served"/"fact"/"canonical".
CANDIDATE = "candidate"
#: claim_status values a provider output must NEVER carry (defense-in-depth re-stamp enforces this).
_FORBIDDEN_STATUSES = frozenset({"served", "canonical", "verified", "promoted", "fact"})

#: read-only/working provider classes, tried in order. The deterministic EMULATOR sorts first so the reference
#: path runs offline with NO credentials; the Baltor-local store is next. (provider_module, class_name)
_WORKING_PROVIDERS = (
    ("src.baltor.adapters.memory.supermemory_emulator", "SupermemoryEmulatorProvider"),
    ("src.baltor.adapters.memory.baltor_local", "BaltorLocalMemoryProvider"),
)
#: CANDIDATE provider adapter STUBS (api + mcp) — they raise UnavailableProvider without creds; we never
#: import the real supermemory SDK and never make a network call. Projected via status(), never used to serve.
_CANDIDATE_PROVIDERS = (
    ("src.baltor.adapters.memory.supermemory_api", "SupermemoryApiProvider"),
    ("src.baltor.adapters.memory.supermemory_mcp", "SupermemoryMcpProvider"),
)

#: substrings that must never appear in any payload this handler returns.
from scripts.security.response_redaction import SECRET_MARKERS as _SECRET_MARKERS  # single source — no per-handler drift

#: deterministic process-level projection of every provider call (a MemoryTrace per call). Safe to rebuild on
#: restart — it is a projection, not a durable truth store. No canonical fact is ever recorded here.
_TRACES: list[dict] = []
_NOW = "2026-06-05T00:00:00Z"  # injected wall-clock string for traces: deterministic, offline
_NOW_TS = 1_749_081_600        # injected unix time the providers want for `now=` (deterministic)


# --------------------------------------------------------------------------------------------------------- #
# provider discovery (lazy, degrade-on-absence) — never imports the supermemory SDK, never makes a call out  #
# --------------------------------------------------------------------------------------------------------- #
def _import(modname: str):
    """Import a sibling-lane provider module lazily. Returns the module or None (absent/broken). Never raises."""
    try:
        return __import__(modname, fromlist=["*"])
    except Exception:  # noqa: BLE001 - any import failure (absent / broken) -> degrade, do not crash
        return None


def _instance(modname: str, clsname: str):
    """Instantiate a provider class lazily. Returns (instance, provider_id) or (None, "")."""
    mod = _import(modname)
    cls = getattr(mod, clsname, None) if mod is not None else None
    if cls is None:
        return None, ""
    try:
        inst = cls()
    except Exception:  # noqa: BLE001 - a provider that won't construct offline -> degrade
        return None, ""
    return inst, getattr(inst, "provider_id", modname)


#: one cached working-provider instance per process, so all six routes in a page load project the SAME store
#: (a stable, coherent projection). Rebuilt on restart — it is a projection cache, not a durable truth store.
_WORKING_CACHE: dict = {"inst": None, "pid": "", "tried": False}


def _first_working_provider():
    """Return (instance, provider_id) for the first available WORKING provider (emulator first), or (None,'').
    Cached per process so the projection is coherent across routes; never persists truth."""
    if not _WORKING_CACHE["tried"]:
        _WORKING_CACHE["tried"] = True
        for modname, clsname in _WORKING_PROVIDERS:
            inst, pid = _instance(modname, clsname)
            if inst is not None:
                _WORKING_CACHE["inst"], _WORKING_CACHE["pid"] = inst, pid
                break
    return _WORKING_CACHE["inst"], _WORKING_CACHE["pid"]


def _record_trace(provider_id: str, op: str, tenant_id: str, *, count: int = 0, note: str = "") -> dict:
    """Record a MemoryTrace for a provider call. Deterministic id from (seq, provider, op, tenant)."""
    seq = len(_TRACES)
    trace_id = "mtr-" + hashlib.sha256(f"{seq}|{provider_id}|{op}|{tenant_id}".encode()).hexdigest()[:16]
    trace = {
        "schema_version": "MemoryTrace",
        "trace_id": trace_id,
        "seq": seq,
        "provider_id": provider_id or "(none)",
        "op": op,
        "tenant_id": tenant_id,
        "result_count": int(count),
        "claim_status": CANDIDATE,  # a trace records a CANDIDATE recall, never a served fact
        "recorded_at": _NOW,
        "note": note,
    }
    _TRACES.append(trace)
    return trace


def _scope(body: dict) -> tuple[str, str]:
    tenant_id = str((body or {}).get("tenant_id") or "demo").strip() or "demo"
    project = str((body or {}).get("project") or "default").strip() or "default"
    return tenant_id, project


def _candidate(item: dict, tenant_id: str, pid: str) -> dict:
    """Force every projected memory item to be a CANDIDATE with required governance fields (defense-in-depth:
    even if a provider mis-stamps, we re-stamp candidate). Lossless: we only ADD/normalize projection fields;
    we never drop source handles, lineage, held-out, or version."""
    out = dict(item) if isinstance(item, dict) else {"value": item}
    out["claim_status"] = CANDIDATE  # NEVER served/fact/canonical off a provider (overrides any forbidden value)
    out["served"] = False
    out["canonical"] = False
    out.setdefault("tenant_id", tenant_id)
    out.setdefault("provider_id", pid)
    out.setdefault("project", out.get("scope") or "default")
    out.setdefault("external_source_handle",
                   out.get("source_handle") or out.get("upstream_id") or out.get("artifact_id") or "(unhandled)")
    out.setdefault("lineage", {"provider_id": pid, "retrieved_at": _NOW})
    return out


def _scoped(rows, tenant_id: str, pid: str) -> list:
    """Filter to the requested tenant (no cross-tenant leakage) and re-stamp every row as a candidate."""
    return [_scrub(_candidate(r, tenant_id, pid)) for r in (rows or [])
            if isinstance(r, dict) and str(r.get("tenant_id") or tenant_id) == tenant_id]


# --------------------------------------------------------------------------------------------------------- #
# routes                                                                                                     #
# --------------------------------------------------------------------------------------------------------- #
def artifacts(body: dict) -> tuple:
    """GET /api/memory/artifacts — candidate MemoryArtifacts in scope (claim_status=candidate; handles +
    lineage). Read-only: projects the provider's profile (static ∪ dynamic) — never calls write()."""
    tenant_id, project = _scope(body)
    inst, pid = _first_working_provider()
    if inst is None:
        _record_trace("", "artifacts", tenant_id, note="no provider available")
        return 200, {"available": False, "artifacts": [], "total": 0, "claim_status": CANDIDATE,
                     "note": "no memory provider available yet (emulator/local not landed)"}
    prof = _safe_call(inst, "profile", {"tenant_id": tenant_id, "project": project, "now": _NOW_TS})
    rows = []
    if isinstance(prof, dict):
        seen = set()
        for a in list(prof.get("static", [])) + list(prof.get("dynamic", [])):
            key = a.get("artifact_id") if isinstance(a, dict) else None
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            rows.append(a)
    out = _scoped(rows, tenant_id, pid)
    _record_trace(pid, "artifacts", tenant_id, count=len(out))
    return 200, {"available": True, "provider_id": pid, "tenant_id": tenant_id, "project": project,
                 "artifacts": out, "total": len(out), "claim_status": CANDIDATE,
                 "note": "candidate memory artifacts; NOT served facts — promote via the Consumption API"}


def profile(body: dict) -> tuple:
    """GET /api/memory/profile — governed profile projection.

    static  = the provider's long-term CANDIDATE memories (a provider can NOT mint canonical facts).
    dynamic = the provider's recent CANDIDATE context.
    promoted = facts already PROMOTED to canonical via the governed CONSUMPTION layer (NOT the provider) —
               each carries a response id + receipt lineage. This is the only non-candidate lane.
    """
    tenant_id, project = _scope(body)
    inst, pid = _first_working_provider()
    static: list = []
    dynamic: list = []
    if inst is not None:
        prof = _safe_call(inst, "profile", {"tenant_id": tenant_id, "project": project, "now": _NOW_TS})
        if isinstance(prof, dict):
            static = _scoped(prof.get("static", []), tenant_id, pid)
            dynamic = _scoped(prof.get("dynamic", []), tenant_id, pid)
        _record_trace(pid, "profile", tenant_id, count=len(static) + len(dynamic))
    else:
        _record_trace("", "profile", tenant_id, note="no provider available")
    promoted = _promoted_facts(tenant_id)  # from the governed consumption layer ONLY
    return 200, {"available": inst is not None or bool(promoted), "provider_id": pid, "tenant_id": tenant_id,
                 "project": project,
                 "profile": {
                     "static": static,      # candidate long-term (provider)
                     "dynamic": dynamic,    # candidate recent (provider)
                     "promoted": promoted,  # PROMOTED canonical (consumption layer) — the only non-candidate lane
                 },
                 "note": "static/dynamic = CANDIDATE memory (provider); promoted = canonical from the Consumption API"}


def _promoted_facts(tenant_id: str) -> list:
    """Project PROMOTED/canonical facts from the governed consumption layer (NOT the provider). Degrades to []
    when the consumption layer has not served anything this process. Never fabricates a fact."""
    try:
        from scripts.api_context_handler import runtime_consumption
        code, payload = runtime_consumption()
    except Exception:  # noqa: BLE001 - consumption layer absent/unwired -> degrade
        return []
    if code != 200 or not isinstance(payload, dict) or not payload.get("latest_response_id"):
        return []
    return [_scrub({
        "claim_status": "promoted",
        "tenant_id": tenant_id,
        "response_id": payload.get("latest_response_id"),
        "answer": payload.get("answer"),
        "served_fact_count": payload.get("served_fact_count"),
        "source": "consumption-api",
        "note": "promoted via VerificationGate + Reconciliation + ConsumptionGate",
    })]


def search(body: dict) -> tuple:
    """GET /api/memory/search — read-only recall over the local/emulator provider (?q=&tenant_id=&project=).
    Recall results are CANDIDATES, never served facts. No write side effects; tenant-scoped; no cross-tenant
    leakage (provider is scope-local AND we post-filter by tenant)."""
    tenant_id, project = _scope(body)
    query = str((body or {}).get("q") or (body or {}).get("query") or "").strip()
    inst, pid = _first_working_provider()
    if inst is None:
        _record_trace("", "search", tenant_id, note="no provider available")
        return 200, {"available": False, "query": query, "results": [], "total": 0, "claim_status": CANDIDATE,
                     "note": "no memory provider available yet"}
    res = _safe_call(inst, "search", {"tenant_id": tenant_id, "project": project, "query": query,
                                      "now": _NOW_TS, "search_mode": "hybrid"})
    rows = res.get("results", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
    results = _scoped(rows, tenant_id, pid)
    _record_trace(pid, "search", tenant_id, count=len(results))
    return 200, {"available": True, "provider_id": pid, "tenant_id": tenant_id, "project": project,
                 "query": query, "results": results, "total": len(results), "claim_status": CANDIDATE,
                 "note": "recall results are CANDIDATES — promote via the Consumption API to serve as fact"}


def connectors() -> tuple:
    """GET /api/memory/connectors — candidate connector list (behind the SourceAdapterPort). Reads a catalog
    file if present; otherwise returns the known candidate set. Connectors are CANDIDATES, never live truth."""
    catalog = _ARCH / "memory_connector_catalog.json"
    if catalog.exists():
        try:
            data = json.loads(catalog.read_text(encoding="utf-8"))
            items = data if isinstance(data, list) else data.get("connectors", [])
            out = [_scrub({**c, "status": c.get("status", CANDIDATE)}) for c in items if isinstance(c, dict)]
            return 200, {"available": True, "connectors": out, "total": len(out), "source": catalog.name}
        except (OSError, ValueError):
            pass
    # default candidate set (validates/extends the SourceAdapterPort ingestion roadmap; verify-first, not live)
    defaults = [
        {"connector_id": c, "status": CANDIDATE, "behind_port": "SourceAdapterPort",
         "note": "candidate connector; verify-first, never live until cataloged + gated"}
        for c in ("google-drive", "gmail", "notion", "onedrive", "github", "web-crawler")
    ]
    return 200, {"available": False, "connectors": defaults, "total": len(defaults),
                 "note": "default candidate connector set (no catalog file yet)"}


def providers() -> tuple:
    """GET /api/memory/providers — MemoryProviderStatus list (emulator / local / supermemory candidate).

    Each provider's own status() is the source. The Supermemory candidate stubs report status="unavailable"
    naming their env:// credential ref (we DO NOT import the SDK and DO NOT make a network call); the emulator
    reports "emulated"; the local provider reports "available". No provider is ever the source of truth and the
    correctness invariant uses the emulator/local provider with NO credentials."""
    out: list[dict] = []

    def project_status(inst, pid: str, kind: str, fallback_cred: str | None) -> dict:
        st = _safe_call(inst, "status") if inst is not None else None
        st = st if isinstance(st, dict) else {}
        return _scrub({
            "provider_id": pid or "(absent)",
            "kind": kind,
            "available": bool(inst is not None and st.get("status") in ("available", "emulated")),
            "status": st.get("status") or ("absent" if inst is None else "unknown"),
            "is_source_of_truth": False,  # NEVER the source of truth
            "claim_status": CANDIDATE,
            "requires_credential": st.get("credential_ref") or st.get("emulates_credential_ref") or fallback_cred,
            "detail": st.get("detail") or ("not landed yet" if inst is None else ""),
        })

    for modname, clsname in _WORKING_PROVIDERS:
        inst, pid = _instance(modname, clsname)
        kind = "emulator" if "emulator" in modname else "local"
        out.append(project_status(inst, pid or modname, kind, None))
    for modname, clsname in _CANDIDATE_PROVIDERS:
        inst, pid = _instance(modname, clsname)
        mod = _import(modname)
        cred = getattr(mod, "CREDENTIAL_REF", None) if mod is not None else None
        d = project_status(inst, pid or modname, "candidate", cred or "env://SUPERMEMORY_API_KEY")
        d["available"] = False  # candidate stub: unavailable offline (no creds, no network) — by design
        out.append(d)
    return 200, {"providers": out, "total": len(out),
                 "note": "no provider is the source of truth; recall yields candidates, not served facts"}


def traces(body: dict) -> tuple:
    """GET /api/memory/traces — the MemoryTraces recorded this process (every provider call is traced)."""
    tenant_id = str((body or {}).get("tenant_id") or "").strip()
    rows = _TRACES if not tenant_id else [t for t in _TRACES if t.get("tenant_id") == tenant_id]
    return 200, {"traces": [_scrub(t) for t in rows], "total": len(rows),
                 "note": "every provider call records a MemoryTrace (claim_status=candidate)"}


# --------------------------------------------------------------------------------------------------------- #
def _safe_call(inst, method: str, arg=None):
    """Call inst.method(arg) read-only; return its value, or None on absence/raise (incl. UnavailableProvider)."""
    fn = getattr(inst, method, None)
    if not callable(fn):
        return None
    try:
        return fn(arg) if arg is not None else fn()
    except Exception:  # noqa: BLE001 - UnavailableProvider / any provider error -> degrade, never crash
        return None


def _scrub(obj):
    """Defensively strip any value carrying a secret marker from an outbound payload."""
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items() if not any(m in str(k) for m in _SECRET_MARKERS)}
    if isinstance(obj, list):
        return [_scrub(v) for v in obj]
    if isinstance(obj, str) and any(m in obj for m in _SECRET_MARKERS):
        return "[redacted]"
    return obj


def handle(method: str, path: str, body: dict | None = None) -> tuple:
    """Dispatch a Memory-API request. Returns (status_code, json_payload). Projection-only; GET-only."""
    body = body or {}
    path = path.rstrip("/") or path
    if method != "GET":
        return 405, {"error": f"memory API is read-only; {method} not allowed on {path}"}
    if path == "/api/memory/artifacts":
        return artifacts(body)
    if path == "/api/memory/profile":
        return profile(body)
    if path == "/api/memory/search":
        return search(body)
    if path == "/api/memory/connectors":
        return connectors()
    if path == "/api/memory/providers":
        return providers()
    if path == "/api/memory/traces":
        return traces(body)
    return 404, {"error": f"unknown memory route {method} {path}"}


def owns(path: str) -> bool:
    return any(path == r or path.startswith(r) for r in ROUTES)
