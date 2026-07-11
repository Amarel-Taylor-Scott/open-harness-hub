#!/usr/bin/env python3
"""capability_retrieval_mcp_server — the "retrieve capabilities not code" MCP transport (stdio, stdlib-only).

The PMF surface: instead of an agent re-writing a solved capability, it RETRIEVES the existing one. This is a
stdlib-only JSON-RPC 2.0 / MCP server over stdin/stdout (no ``mcp`` pip package — matching the repo's no-pip
discipline, mirroring ``aidevobserver_mcp_server.py``). It is ADD-ONLY: it wires existing search, retrieval,
guardrail, and composition capabilities; it builds no parallel engine.

Tools:
  primitive_search {query, limit?}  -> federated search over the multi-million-row SQLite FTS database plus
                                       the resumable working/draft overlay. ``scope=governed`` preserves the
                                       smaller df-capped governed-only index lane.
  primitive_get {primitive_id, ...} -> exact lookup with typed edges, proof status, and an optional full payload.
  find_reuse {message}              -> the reinvention guardrail
                                       (``src.teleon.registry.reinvention_guard.check``): given build-intent
                                       text, FIRES with grounded registry matches when the capability already
                                       exists in the federation, and stays QUIET on genuinely-novel work.
  capability_compose {request, ...} -> the agent-callable COMPOSE surface (the completeness teardown's #2:
                                       the engines previously reached no runtime surface). Wraps
                                       ``scripts.primitive_runtime.compose_solution`` — decompose-by-retrieval
                                       -> pruned search -> edge-type classify/rerank -> route compose (REAL
                                       teleon composer) -> peel-back -> remix gap specs -> executed-proof
                                       cross-check — and returns a COMPACT route view (signatures + edges, not
                                       card bodies: the token-economy onion discipline).
  primitive_corpus_status {}       -> measured search, description, embedding, and goal-loop coverage.
  primitive_description_gaps {...} -> a bounded cursor page of IDs still missing effective descriptions.
  record_reuse_outcome {...}       -> append privacy-minimized accept/reuse/dismiss/ignore ranking feedback.

Every result is a governed CANDIDATE (``serves_truth=false``): a search hit is a POINTER to reuse, and a
reuse notice is advice — neither is served truth. Primitive sources remain read-only. Full-corpus search may
advance its derived local sidecar checkpoint so newly appended source rows become searchable; it never edits or
promotes the source corpus.

Register it with Claude Code:

  claude mcp add capability-retrieval -- python3 \
      /home/username/ai_harness_and_knowledge_facts_and_logic_website_sharing/_repos/shared-backend-components/scripts/capability_retrieval_mcp_server.py

Run the proof (offline: one search + one reuse check):

  python3 _repos/shared-backend-components/scripts/capability_retrieval_mcp_server.py --self-test
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# ── cross-repo bootstrap (task-required: _repo_paths.install()) ──────────────────────────────────────────────
# Put the code roots (repo root + every _repos/*/backend + shared-backend-components) on sys.path through the ONE
# resolver, so BOTH `scripts.build_primitive_search_index` and the MOVED `src.teleon.registry.reinvention_guard`
# resolve regardless of CWD/PYTHONPATH — a stdio server is launched with an arbitrary cwd by its MCP client.
_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:  # so `scripts._repo_paths` imports before install() has run
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install  # noqa: E402

_install()  # prepend all code roots -> `scripts.*` and `src.teleon.*` both importable below

from scripts import _mcp_stdio  # noqa: E402  the ONE newline-delimited (spec) MCP stdio transport, shared by every server
from scripts.build_primitive_search_index import (  # noqa: E402
    DEFAULT_LIMIT,
    PACK_DIR as _SERVED_LEXICAL_INDEX_DIR,  # the built inverted index search actually loads
    search_with_stats,
)
from scripts.primitive_runtime import compose_solution as _compose_solution  # noqa: E402  the ONE runtime pipeline
from scripts.primitive_search_federation import (  # noqa: E402
    PrimitiveSearchFederation,
    cached_federation_stats,
    federation_stats,
)
from scripts.primitive_description_embedding_loop import (  # noqa: E402
    DEFAULT_STATE_DIR as DESCRIPTION_EMBEDDING_STATE_DIR,
    INDEX_FILENAME as DESCRIPTION_EMBEDDING_MANIFEST_FILENAME,
)
from scripts._repo_paths import resource  # noqa: E402
from src.teleon.registry.reinvention_guard import (  # noqa: E402
    py_function_src_teleon_registry_reinvention_guard__check as _reinvention_check,
)

PROTOCOL_VERSION = "2024-11-05"  # MCP protocol revision this server implements (matches the sibling servers)
SERVER_NAME = "capability-retrieval"
SERVER_VERSION = "0.4.0"
REUSE_OUTCOME_PATH = resource("data") / "dev-intel" / "aidevobserver_reuse_outcomes" / "outcomes.jsonl"

# Opt-in ADAPTIVE-LEARNING lane (owner 2026-07-10: the MCP tool "can be more flexible and learn from the
# environment and requests, and database"). OFF (unset) -> every response is bit-for-bit what it was before this
# lane existed. ON ("1") -> primitive_search responses are additionally recorded to the usage/request ledgers,
# annotated with the caller's environment technologies, and NON-DESTRUCTIVELY reranked by learned outcome bias
# (hits reorder, never drop). Mirrors scripts.environment_request_learning.ADAPTIVE_LEARNING_ENVIRONMENT_VARIABLE
# as a literal — a stdio server must not import the learning module at startup; that module's self-test
# drift-checks this mirror.
_ADAPTIVE_LEARNING_ENV = "OH_MCP_ADAPTIVE_LEARNING"

# Public MCP requests are deliberately small control-plane messages.  These bounds prevent a client from turning
# the stdio process into an unbounded parser/search/composition or telemetry sink.  Full primitive bodies remain
# behind primitive_get's explicit include_payload switch and are never accepted as request arguments.
MAX_QUERY_CHARS = 8_192
MAX_PRIMITIVE_ID_CHARS = 512
MAX_POOL_CHARS = 128
MAX_CURSOR_CHARS = 1_024
MAX_SEARCH_LIMIT = 100
MAX_GAP_LIMIT = 1_000
MAX_ROUTE_STEPS = 64
MAX_SESSION_ID_CHARS = 1_024

# JSON-RPC 2.0 error codes — single-sourced from the shared transport (scripts._mcp_stdio). Parse errors are
# owned by _mcp_stdio.serve, so dispatch only references method-not-found + internal.
_METHOD_NOT_FOUND = _mcp_stdio.METHOD_NOT_FOUND
_INTERNAL_ERROR = _mcp_stdio.INTERNAL_ERROR
_INVALID_REQUEST = _mcp_stdio.INVALID_REQUEST
_INVALID_PARAMS = _mcp_stdio.INVALID_PARAMS

# --- tool catalog (name + description + JSON Schema inputSchema) -------------------------------------------------
TOOLS = [
    {
        "name": "primitive_search",
        "description": "Retrieve reusable capability primitives by intent. Default scope=all searches the "
                       "multi-million-row SQLite FTS core plus every registered synthesis, draft, research, "
                       "and compiled-codeblock corpus tier, with "
                       "source-declared labels disclosed but never self-authorizing. evidence=trusted_receipt "
                       "uses the low-latency content-valid hidden-oracle recipe lane. scope=governed preserves the smaller "
                       "df-capped governed-card index. Each hit is a candidate pointer to reuse "
                       "(serves_truth=false), not served truth.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 1, "maxLength": MAX_QUERY_CHARS,
                          "description": "What capability you need (intent / edge / domain words)."},
                "limit": {"type": "integer", "minimum": 1, "maximum": MAX_SEARCH_LIMIT,
                          "default": DEFAULT_LIMIT,
                          "description": f"Max hits to return (default {DEFAULT_LIMIT})."},
                "scope": {"type": "string", "enum": ["all", "governed"], "default": "all",
                          "description": "all = federated full corpus; governed = smaller governed-card index."},
                "sync": {"type": "boolean", "default": False,
                         "description": "Advance append-only overlay checkpoints before searching. The 100M "
                                        "supervisor normally handles this, so ordinary queries stay read-fast."},
                "pool": {"type": "string", "maxLength": MAX_POOL_CHARS,
                         "description": "Optional full-corpus pool filter, e.g. executable, verified_factory, "
                                        "working_primitives, compiled_codeblock_candidates, or "
                                        "continuous_research_candidates."},
                "evidence": {
                    "type": "string",
                    "enum": ["any", "trusted_receipt"],
                    "default": "any",
                    "description": "trusted_receipt returns only content-valid, passing, unrevoked recipe receipts.",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "primitive_get",
        "description": "Retrieve one primitive by immutable id after search. Returns core/overlay metadata, typed "
                       "edges, verification/proof status, and (when requested and available) the full source "
                       "payload or executable body. Retrieval is candidate evidence and never promotion.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "primitive_id": {"type": "string", "minLength": 1, "maxLength": MAX_PRIMITIVE_ID_CHARS,
                                 "description": "Exact primitive id returned by search."},
                "include_payload": {"type": "boolean", "default": False,
                                    "description": "Also resolve the full JSONL payload; may read a large legacy "
                                                   "source file when no direct payload index exists."},
                "sync": {"type": "boolean", "default": False,
                         "description": "Advance append-only overlay checkpoints before lookup."},
            },
            "required": ["primitive_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "find_reuse",
        "description": "Guard against reinventing a solved capability. Given build-intent text (e.g. \"let me "
                       "write a PDF parser from scratch\"), it FIRES with grounded registry-federation matches "
                       "when the capability already exists, and stays QUIET on genuinely-novel or non-build work. "
                       "The fire is advice to reuse/compare before building (serves_truth=false); it decides "
                       "nothing on its own.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "minLength": 1, "maxLength": MAX_QUERY_CHARS,
                            "description": "The build-intent text to screen (what the agent is about to build)."},
            },
            "required": ["message"],
            "additionalProperties": False,
        },
    },
    {
        "name": "capability_compose",
        "description": "Compose a route of existing primitives for a natural-language request instead of "
                       "generating code. Runs the full runtime pipeline (decompose-by-retrieval -> pruned "
                       "search -> edge-type classify + rerank -> route composition via the real composer -> "
                       "peel-back -> deterministic remix of any gap -> executed-proof cross-check) and returns "
                       "a compact route view: endpoints, ordered steps as signature+edge views (never card "
                       "bodies), gap specs for anything missing, and which step took which path. Every part is "
                       "a governed candidate (serves_truth=false) — composition is not promotion.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "request": {"type": "string", "minLength": 1, "maxLength": MAX_QUERY_CHARS,
                            "description": "What you need built/done, in natural language (the capability intent)."},
                "limit": {"type": "integer", "minimum": 1, "maximum": MAX_SEARCH_LIMIT,
                          "default": DEFAULT_LIMIT,
                          "description": f"Max search candidates feeding the composer (default {DEFAULT_LIMIT})."},
                "max_route_steps": {"type": "integer", "minimum": 1, "maximum": MAX_ROUTE_STEPS,
                                    "description": "Route-depth budget (default 12). The composers terminate via "
                                                   "visited pruning regardless — raise for long-chain systems."},
            },
            "required": ["request"],
            "additionalProperties": False,
        },
    },
    {
        "name": "primitive_corpus_status",
        "description": "Read measured corpus coverage: unique searchable IDs, four-field presence, versioned "
                       "source-grounded/usefulness-passing descriptions, embeddings, source cursors, and the "
                       "latest 100M-loop state. Counts remain candidate receipts, never target-derived claims.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "primitive_description_gaps",
        "description": "Return a bounded cursor page of immutable primitive IDs that still lack an effective "
                       "title, blackbox, typed input, or typed output after core/overlay dedupe and accepted "
                       "descriptor revisions. Returns metadata only, never source bodies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cursor": {"type": "string", "maxLength": MAX_CURSOR_CHARS,
                           "description": "Prior next_cursor; omit for the first page."},
                "limit": {"type": "integer", "minimum": 1, "maximum": MAX_GAP_LIMIT, "default": 50},
                "pool": {"type": "string", "maxLength": MAX_POOL_CHARS,
                         "description": "Optional primitive pool filter."},
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "record_reuse_outcome",
        "description": "Record metadata-only feedback that a searched primitive was accepted, actually reused, "
                       "dismissed, or ignored. Raw query/session text is never stored; only SHA-256 digests are "
                       "kept for dedupe and ranking experiments. This candidate telemetry never promotes a row.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "primitive_id": {"type": "string", "minLength": 1, "maxLength": MAX_PRIMITIVE_ID_CHARS},
                "outcome": {"type": "string", "enum": ["accepted", "reused", "dismissed", "ignored"]},
                "query": {"type": "string", "maxLength": MAX_QUERY_CHARS,
                          "description": "Optional query; stored only as a digest."},
                "session_id": {"type": "string", "maxLength": MAX_SESSION_ID_CHARS,
                               "description": "Optional opaque ID; stored only as a digest."},
            },
            "required": ["primitive_id", "outcome"],
            "additionalProperties": False,
        },
    },
]


class ToolError(Exception):
    """A tool-level failure -> surfaced in-band via {isError: true} (so the model sees it), not a JSON-RPC error."""


class _InternalFixtureIndex(dict):
    """Python-only marker for an offline self-test index; ordinary JSON always decodes to plain ``dict``."""


def _schema_error(value: object, schema: dict, path: str = "arguments") -> str | None:
    """Validate the small JSON-Schema subset used by this server, without an optional pip dependency.

    MCP advertises these schemas as an executable contract, so ``additionalProperties: false`` and every bound
    are enforced before a handler runs.  The catalog currently uses only object/string/integer/boolean, enum,
    required, length, and numeric bounds; rejecting an unknown schema type is safer than silently accepting it.
    """

    expected = schema.get("type")
    type_ok = {
        "object": lambda item: isinstance(item, dict),
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
    }.get(expected)
    if type_ok is None:
        return f"{path} uses an unsupported server schema"
    if not type_ok(value):
        return f"{path} must be {expected}"
    if "enum" in schema and value not in schema["enum"]:
        return f"{path} must be one of the declared values"
    if isinstance(value, str):
        if len(value) < int(schema.get("minLength", 0)):
            return f"{path} is too short"
        if "maxLength" in schema and len(value) > int(schema["maxLength"]):
            return f"{path} exceeds its maximum length"
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in schema and value < int(schema["minimum"]):
            return f"{path} is below its minimum"
        if "maximum" in schema and value > int(schema["maximum"]):
            return f"{path} exceeds its maximum"
    if isinstance(value, dict):
        properties = schema.get("properties") or {}
        for required in schema.get("required") or []:
            if required not in value:
                return f"{path} is missing required field {required}"
        if schema.get("additionalProperties") is False:
            undeclared = sorted(str(key) for key in value if key not in properties)
            if undeclared:
                return f"{path} contains undeclared field {undeclared[0]}"
        for key, item in value.items():
            if key in properties:
                error = _schema_error(item, properties[key], f"{path}.{key}")
                if error:
                    return error
    return None


def _tool_schema(name: str) -> dict | None:
    return next((tool["inputSchema"] for tool in TOOLS if tool["name"] == name), None)


def _validated_arguments(name: str, arguments: object) -> dict:
    schema = _tool_schema(name)
    error = _schema_error(arguments, schema or {}) if schema is not None else "tool schema unavailable"
    if error:
        raise ToolError(error)
    return arguments  # type: ignore[return-value]


# --- capability seams (pure: reused engines shaped into a JSON-able result) --------------------------------------
def run_primitive_search(query: str, limit: int = DEFAULT_LIMIT, index: dict | None = None,
                         scope: str = "all", federation: PrimitiveSearchFederation | None = None,
                         sync_overlay: bool = False, pool: str | None = None,
                         evidence: str = "any") -> dict:
    """Search the full federation by default; preserve the injected/governed index as a distinct lane.

    ``index`` is an in-process injection seam (used by --self-test to run fully offline against a synthetic
    index); when None the reused engine loads the persisted default index. The pruning stats are surfaced so a
    caller can SEE the search touched ``candidate_count`` docs, not the whole corpus.
    """
    if scope not in {"all", "governed"}:
        raise ToolError("primitive_search scope must be `all` or `governed`")
    if evidence not in {"any", "trusted_receipt"}:
        raise ToolError("primitive_search evidence must be `any` or `trusted_receipt`")
    if evidence == "trusted_receipt" and scope != "all":
        raise ToolError("primitive_search evidence=trusted_receipt requires scope=all")
    if index is None and scope == "all":
        search_federation = federation or PrimitiveSearchFederation()
        if evidence == "trusted_receipt":
            response = search_federation.search_trusted_recipes(query, limit=limit)
            response.update({
                "limit": limit,
                "scope": "all",
                "evidence": evidence,
                "source_kind": "trusted_recipe_receipt_search",
                "index_sync": {"synced": False, "reason": "receipt lane is content-addressed"},
                "candidate": True,
                "serves_truth": False,
            })
            return response
        response = search_federation.search(query, pool=pool, limit=limit, sync=sync_overlay)
        sync_receipt = response.pop("overlay_sync", None)
        coverage = ((sync_receipt or {}).get("coverage") if sync_receipt is not None else None)
        if coverage is None and isinstance(search_federation, PrimitiveSearchFederation):
            # Search returns progressive-disclosure sketches.  Never add a multi-million-row overlap join to
            # every tool call merely to decorate it with a corpus count: synchronization already persisted an
            # atomic fast/exact coverage receipt, and primitive_corpus_status is the explicit fresh-count surface.
            coverage = cached_federation_stats(overlay_db=search_federation.overlay_db)
        response.update({
            "limit": limit,
            "scope": "all",
            "evidence": evidence,
            "source_kind": "primitive_search_federation",
            "index_sync": {
                "synced": sync_receipt is not None,
                "indexed": (sync_receipt or {}).get("indexed", 0),
                "quality_upgrades": (sync_receipt or {}).get("quality_upgrades", 0),
                "mutations_blocked": (sync_receipt or {}).get("mutations_blocked", 0),
                "unique_searchable_docs": (coverage or {}).get("unique_searchable_docs"),
                "coverage_source": (coverage or {}).get("coverage_source", (
                    "live_sync" if sync_receipt is not None else "unavailable"
                )),
            },
            "candidate": True,
            "serves_truth": False,
        })
        return response

    results, stats = search_with_stats(query, limit, index=index)
    return {
        "query": query,
        "limit": limit,
        "count": len(results),
        "results": results,  # each hit already carries candidate=true / serves_truth=false
        "pruning": {  # proof the index pruned: O(candidates), not O(total_docs)
            "total_docs": stats.get("total_docs"),
            "candidate_count": stats.get("candidate_count"),
            "docs_scored": stats.get("docs_scored"),
            "selective_tokens": stats.get("selective_tokens"),
            "capped": stats.get("capped"),
        },
        "source_kind": "primitive_search_index",
        "scope": "governed",
        "candidate": True,
        "serves_truth": False,
    }


def _coerce_limit(raw: object, *, maximum: int = MAX_SEARCH_LIMIT, default: int = DEFAULT_LIMIT) -> int:
    """Best-effort positive int for `limit`, defaulting to DEFAULT_LIMIT (single source: the reused engine)."""
    try:
        return min(maximum, max(1, int(raw)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _route_step_view(step: dict) -> dict:
    """One composed step as a SIGNATURE view (id + edges + operation) — the onion's L0/L1 read, never the body."""
    return {
        "component_id": step.get("component_id") or step.get("primitive_id"),
        "input_edge": step.get("input_edge"),
        "output_edge": step.get("output_edge"),
        "operation": step.get("operation") or "",
    }


_COMPILED_ROUTES = None  # lazy CompiledRouteCache — the compile-once/execute-many lane for DEFAULT composes


def _compiled_routes():
    global _COMPILED_ROUTES
    if _COMPILED_ROUTES is None:
        from scripts.compiled_route_cache import CompiledRouteCache  # noqa: PLC0415
        _COMPILED_ROUTES = CompiledRouteCache()
    return _COMPILED_ROUTES


def run_capability_compose(request: str, limit: int = DEFAULT_LIMIT, cards: list | None = None,
                           max_route_steps: int | None = None) -> dict:
    """Reuse ``primitive_runtime.compose_solution`` and shape a compact, governed route view.

    ``cards`` is an in-process injection seam (used by --self-test to compose fully offline over a synthetic
    chainable corpus); when None the engine runs over the persisted verified corpus/index. The full solution
    record stays reproducible by re-running the engine — this view keeps the agent-facing read cheap
    (signatures + edges + paths, never card bodies), which is the point of the surface.

    COMPILE-ONCE LANE (side-by-side, default-parameter composes only): an identical repeat request over the
    default corpus is served from the compiled-route cache at artifact-read cost with ZERO recompose — the
    Compiled-AI amortization loop, live on the agent surface. Non-default calls (injected cards / custom
    route budget) bypass the cache and behave exactly as before.
    """
    cacheable = cards is None and max_route_steps is None and limit == DEFAULT_LIMIT
    if cacheable:
        cache = _compiled_routes()
        from scripts.compiled_route_cache import _request_key, corpus_fingerprint  # noqa: PLC0415
        key = _request_key(request)
        if key in cache.entries:
            try:
                hit = cache.execute(request, expected_corpus_fingerprint=corpus_fingerprint())
            except KeyError:
                hit = None  # STALE (corpus drifted since compile) — fall through and recompile below
        else:
            hit = None
        if hit is not None:
            entry = cache.entries[key]
            return {"request": request, "compiled_route_hit": True, "model_calls": 0,
                    "tokens_spent_estimate": hit["tokens_spent"],
                    "route": {"route_found": entry["route_found"], "composer_path": entry["composer_path"],
                              "ordered_route": hit["ordered_route"]},
                    "amortization": {"reuse_count": entry["reuse_count"],
                                     "compile_cost_tokens": entry["compile_cost_tokens"]},
                    "source_kind": "compiled_route_cache", "candidate": True, "serves_truth": False}
    compose_kwargs = {"limit": limit, "candidate_cards": cards}
    if max_route_steps is not None:
        compose_kwargs["max_route_steps"] = max(1, int(max_route_steps))
    sol = _compose_solution(request, **compose_kwargs)
    if cacheable:
        _compiled_routes().compile_once(request, solution=sol)  # seed from THIS compose — never compose twice
    decomposition = sol["decomposition"]
    route = sol["route"]
    remix = sol["remix"]
    prove = sol["prove"]
    return {
        "request": request,
        "decomposition": {
            "path_used": decomposition.get("path_used"),
            "requested_input_type": decomposition.get("requested_input_type"),
            "requested_output_type": decomposition.get("requested_output_type"),
            "retrieved_endpoints": [
                {k: e.get(k) for k in ("primitive_id", "input_type", "output_type", "score")}
                for e in (decomposition.get("retrieved_endpoints") or [])
            ],
        },
        "route": {
            "route_found": route.get("route_found"),
            "composer_path": route.get("composer_path"),
            "edge_chain_strength": route.get("edge_chain_strength"),
            "recomposed_via_peel_back": bool(route.get("recomposed_via_peel_back")),
            "ordered_route": [_route_step_view(s) for s in (route.get("ordered_route") or [])],
        },
        "gaps": {  # what composition could NOT cover — remix bridged it deterministically or specs a model step
            "remix_steps": remix.get("remix_steps") or [],
            "model_steps": remix.get("model_steps") or [],
        },
        "prove": {
            "route_proven": prove.get("route_proven"),
            "proven_leaves": prove.get("proven_leaves") or [],
            "unproven_leaves": prove.get("unproven_leaves") or [],
        },
        "step_log": sol.get("step_log") or [],  # which path each step took (decompose/search/.../prove)
        "fell_back": sol.get("fell_back") or [],  # engines that silently degraded (empty = all REAL)
        "source_kind": "primitive_runtime_solution",
        "candidate": True,
        "serves_truth": False,
    }


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def run_primitive_corpus_status(federation: PrimitiveSearchFederation | None = None) -> dict:
    """Assemble a read-only status receipt from the stores that own each measured count."""

    search_federation = federation or PrimitiveSearchFederation()
    search_manifest_path = search_federation.overlay_db.with_name(
        f"{search_federation.overlay_db.stem}.manifest.json"
    )
    description_manifest_path = search_federation.description_db.with_suffix(".manifest.json")
    coverage = _read_json(search_manifest_path)
    if not coverage:
        coverage = federation_stats(
            core_db=search_federation.core_db,
            overlay_db=search_federation.overlay_db,
            description_db=search_federation.description_db,
            include_description_coverage=True,
        )
    embedding_path = resource("dist") / "primitive-embedding-shards" / "manifest.json"
    description_embedding_path = DESCRIPTION_EMBEDDING_STATE_DIR / DESCRIPTION_EMBEDDING_MANIFEST_FILENAME
    recipe_receipt_path = resource("dist") / "verified_recipe_receipts.manifest.json"
    goal_state_path = (
        resource("data") / "dev-intel" / "aidevobserver_100m_goal_loop" / "state.json"
    )
    embedding = _read_json(embedding_path)
    description_embedding = _read_json(description_embedding_path)
    recipe_receipts = _read_json(recipe_receipt_path)
    goal_state = _read_json(goal_state_path)
    description = {
        **(coverage.get("description_enrichment") or {}),
        **_read_json(description_manifest_path),
    }
    # ── HONEST FUNNEL ─────────────────────────────────────────────────────────────────────────
    # `unique_searchable_docs` (6.4M) is the federation DB INVENTORY across all pools — it is NOT a
    # count of primitives that are richly searchable, embedded, or runnable. Report the funnel from
    # raw inventory down to authorized-to-execute as DISTINCT computed counts so the headline can't be
    # misread (candidate/truth-boundary + no-magic-values laws). Every number below is read from the
    # store that owns it; none is hand-typed.
    _served_index_manifest = _read_json(_SERVED_LEXICAL_INDEX_DIR / "manifest.json")
    reconciled_funnel = {
        "1_federation_db_inventory_rows": coverage.get("unique_searchable_docs", 0),
        "2_field_complete_docs": coverage.get("field_complete_docs", 0),
        "3_descriptor_search_indexed_docs": description.get("search_indexed", 0),
        "4_built_lexical_index_docs_served": _served_index_manifest.get("n_docs", 0),
        "5_embedded_docs": embedding.get("coverage_rows", 0),
        "6_trusted_execution_receipts": recipe_receipts.get("trusted_receipts", 0),
        "7_descriptor_execution_verified_docs": description.get(
            "descriptor_specific_execution_verified", 0
        ),
        "interpretation": (
            "STRICTLY DESCENDING axes, not one number: (1) total known rows in the federation DB across "
            "all pools; (2) rows with nonblank title+blackbox+edges (metadata, not code); (3) rows with "
            "complete descriptors that are actually search-indexed; (4) docs in the built inverted index "
            "that serve-time lexical search loads; (5) docs with a persisted embedding (semantic-search "
            "coverage); (6) primitives with a trusted, unrevoked execution receipt (authorized to RUN); "
            "(7) descriptor-specific execution-verified docs. Inventory is NOT usability: most rows are "
            "edge/contract records with no code body. serves_truth=false at every level."
        ),
    }
    return {
        "record_type": "aidevobserver_primitive_corpus_status",
        "reconciled_funnel": reconciled_funnel,
        "search": {
            "unique_searchable_docs": coverage.get("unique_searchable_docs", 0),
            "core_docs": coverage.get("core_docs", 0),
            "overlay_docs": coverage.get("overlay_docs", 0),
            "overlap_docs": coverage.get("overlap_docs", 0),
            "source_offsets": coverage.get("source_offsets", []),
            "manifest_path": str(search_manifest_path),
            "manifest_mtime": search_manifest_path.stat().st_mtime if search_manifest_path.exists() else None,
        },
        "descriptions": {
            "field_complete_docs": coverage.get("field_complete_docs", 0),
            "effective_field_complete_docs": coverage.get("effective_field_complete_docs", 0),
            "sidecar_gap_closures": description.get("effective_field_gap_closures", 0),
            "field_presence_semantics": "nonblank title+blackbox+input_edge+output_edge only",
            "versioned_current": description.get("current_descriptions", 0),
            "source_grounded": description.get("source_grounded", 0),
            "usefulness_pass": description.get("usefulness_pass", 0),
            "search_indexed": description.get("search_indexed", 0),
            "descriptor_specific_execution_verified": description.get(
                "descriptor_specific_execution_verified", 0
            ),
            "manifest_path": str(description_manifest_path),
            "manifest_mtime": (
                description_manifest_path.stat().st_mtime if description_manifest_path.exists() else None
            ),
        },
        "embeddings": {
            "coverage_rows": embedding.get("coverage_rows", 0),
            "manifest_exists": embedding_path.exists(),
            "manifest_path": str(embedding_path),
            "description_revision_jobs": description_embedding.get("coverage_jobs", 0),
            "description_revisions": sum(
                int(shard.get("description_revisions", 0))
                for shard in description_embedding.get("shards", [])
                if isinstance(shard, dict)
            ),
            "description_profile_counts": description_embedding.get("profile_counts", {}),
            "description_manifest_path": str(description_embedding_path),
        },
        "execution_receipts": {
            "declared_recipes": recipe_receipts.get("declared_recipes", 0),
            "stored_receipts": recipe_receipts.get("stored_receipts", 0),
            "trusted_receipts": recipe_receipts.get("trusted_receipts", 0),
            "revoked_receipts": recipe_receipts.get("revoked_receipts", 0),
            "invalid_or_stale_receipts": recipe_receipts.get("invalid_or_stale_receipts", 0),
            "manifest_exists": recipe_receipt_path.exists(),
            "manifest_path": str(recipe_receipt_path),
        },
        "goal_loop": {
            "state_exists": goal_state_path.exists(),
            "tick": goal_state.get("tick"),
            "last_tick_ok": goal_state.get("last_tick_ok"),
            "last_blocked_by": goal_state.get("last_blocked_by"),
            "last_target_gates": goal_state.get("last_target_gates"),
        },
        "claim_boundary": (
            "searchability, descriptor quality, embeddings, and content-valid unrevoked execution receipts "
            "are independent measured axes; source-declared proof labels do not authorize execution"
        ),
        "candidate": True,
        "serves_truth": False,
    }


def record_reuse_outcome(
    primitive_id: str,
    outcome: str,
    *,
    query: str = "",
    session_id: str = "",
    path: Path = REUSE_OUTCOME_PATH,
) -> dict:
    """Append a privacy-minimized ranking event under an advisory file lock."""

    allowed = {"accepted", "reused", "dismissed", "ignored"}
    primitive_id = str(primitive_id or "").strip()
    outcome = str(outcome or "").strip().lower()
    if not primitive_id:
        raise ToolError("record_reuse_outcome requires a non-empty `primitive_id`")
    if outcome not in allowed:
        raise ToolError(f"record_reuse_outcome outcome must be one of {sorted(allowed)}")

    def digest(value: str) -> str | None:
        value = str(value or "").strip()
        return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else None

    event = {
        "record_type": "primitive_reuse_outcome",
        "primitive_id": primitive_id,
        "outcome": outcome,
        "query_digest": digest(query),
        "session_digest": digest(session_id),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "raw_text_stored": False,
        "candidate": True,
        "serves_truth": False,
    }
    event["event_digest"] = hashlib.sha256(
        json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ToolError("record_reuse_outcome storage is unavailable")
    parent_info = path.parent.stat()
    if not stat.S_ISDIR(parent_info.st_mode) or parent_info.st_uid != os.geteuid():
        raise ToolError("record_reuse_outcome storage is unavailable")
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise ToolError("record_reuse_outcome storage is unavailable") from exc
    with os.fdopen(fd, "a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        file_info = os.fstat(handle.fileno())
        if not stat.S_ISREG(file_info.st_mode) or file_info.st_uid != os.geteuid():
            raise ToolError("record_reuse_outcome storage is unavailable")
        os.fchmod(handle.fileno(), 0o600)
        handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return {
        "recorded": True,
        "event_digest": event["event_digest"],
        "primitive_id": primitive_id,
        "outcome": outcome,
        "raw_text_stored": False,
        "candidate": True,
        "serves_truth": False,
    }


# --- tool handlers (pure: arguments dict -> JSON-able result) ----------------------------------------------------
# ``fixtures`` is a private in-process test dependency channel.  Public JSON-RPC can reach only
# ``handle_tools_call`` below, which never supplies it and validates arguments before dispatch.
def _maybe_adapt_search(query: str, response: dict) -> dict:
    """The opt-in adaptive-learning lane (see _ADAPTIVE_LEARNING_ENV). OFF -> the response object passes through
    untouched. ON -> environment fingerprint + request/usage-ledger recording + NON-DESTRUCTIVE learned rerank
    (delegated to scripts.environment_request_learning, imported lazily so server startup never depends on it).
    Fail-OPEN: a learning failure annotates the response; it never breaks retrieval."""
    if os.environ.get(_ADAPTIVE_LEARNING_ENV) != "1":
        return response
    try:
        from scripts.environment_request_learning import adapt_search_response  # noqa: PLC0415
        return adapt_search_response(query, response, surface=f"mcp:{SERVER_NAME}")
    except Exception as error:  # noqa: BLE001  fail open — the learned lane must never take down search
        response.setdefault("adaptive", {"enabled": True, "error": str(error)[:200],
                                         "candidate": True, "serves_truth": False})
        return response


def _tool_primitive_search(arguments: dict, fixtures: dict | None = None) -> dict:
    fixture = dict(fixtures or {})
    # Backward-compatible *in-process* seam for the unified server's hermetic proof.  JSON decoding can never
    # create this subclass, so a production request carrying an ordinary ``index`` object is rejected below.
    if not fixture and isinstance(arguments, dict) and isinstance(arguments.get("index"), _InternalFixtureIndex):
        arguments = dict(arguments)
        fixture["index"] = arguments.pop("index")
    arguments = _validated_arguments("primitive_search", arguments)
    query = str(arguments.get("query") or "").strip()
    if not query:
        raise ToolError("primitive_search requires a non-empty `query` string")
    index = fixture.get("index")
    return _maybe_adapt_search(query, run_primitive_search(
        query, _coerce_limit(arguments.get("limit")), index=index,
        scope=str(arguments.get("scope") or ("governed" if index else "all")),
        federation=fixture.get("federation"),
        sync_overlay=bool(arguments.get("sync", False)),
        pool=str(arguments.get("pool") or "").strip() or None,
        evidence=str(arguments.get("evidence") or "any")))


def _tool_primitive_get(arguments: dict, fixtures: dict | None = None) -> dict:
    arguments = _validated_arguments("primitive_get", arguments)
    primitive_id = str(arguments.get("primitive_id") or "").strip()
    if not primitive_id:
        raise ToolError("primitive_get requires a non-empty `primitive_id`")
    federation = (fixtures or {}).get("federation") or PrimitiveSearchFederation()
    return federation.get(primitive_id, sync=bool(arguments.get("sync", False)),
                          load_core_payload=bool(arguments.get("include_payload", False)))


def _tool_find_reuse(arguments: dict, fixtures: dict | None = None) -> dict:
    arguments = _validated_arguments("find_reuse", arguments)
    message = str(arguments.get("message") or "").strip()
    if not message:
        raise ToolError("find_reuse requires a non-empty `message` string (the build-intent text to screen)")
    return _reinvention_check(message)  # governed: fires only when GROUNDED in the federation; serves_truth=false


def _tool_capability_compose(arguments: dict, fixtures: dict | None = None) -> dict:
    arguments = _validated_arguments("capability_compose", arguments)
    request = str(arguments.get("request") or "").strip()
    if not request:
        raise ToolError("capability_compose requires a non-empty `request` string (the capability intent)")
    return run_capability_compose(request, _coerce_limit(arguments.get("limit")),
                                  cards=(fixtures or {}).get("cards"),
                                  max_route_steps=arguments.get("max_route_steps"))


def _tool_primitive_corpus_status(arguments: dict, fixtures: dict | None = None) -> dict:
    arguments = _validated_arguments("primitive_corpus_status", arguments)
    fixture = fixtures or {}
    provider = fixture.get("status_provider")
    if callable(provider):
        return provider()
    return run_primitive_corpus_status(fixture.get("federation"))


def _tool_primitive_description_gaps(arguments: dict, fixtures: dict | None = None) -> dict:
    arguments = _validated_arguments("primitive_description_gaps", arguments)
    federation = (fixtures or {}).get("federation") or PrimitiveSearchFederation()
    return federation.description_gaps(
        cursor=str(arguments.get("cursor") or ""),
        limit=_coerce_limit(arguments.get("limit", 50), maximum=MAX_GAP_LIMIT, default=50),
        pool=str(arguments.get("pool") or "").strip() or None,
    )


def _tool_record_reuse_outcome(arguments: dict, fixtures: dict | None = None) -> dict:
    arguments = _validated_arguments("record_reuse_outcome", arguments)
    return record_reuse_outcome(
        str(arguments.get("primitive_id") or ""),
        str(arguments.get("outcome") or ""),
        query=str(arguments.get("query") or ""),
        session_id=str(arguments.get("session_id") or ""),
        path=Path((fixtures or {}).get("outcome_path") or REUSE_OUTCOME_PATH),
    )


def _public_handler(handler):
    """Keep direct-import surfaces (the unified MCP) on the same sanitized failure boundary."""

    def guarded(arguments: dict, fixtures: dict | None = None) -> dict:
        try:
            return handler(arguments, fixtures)
        except ToolError as exc:
            raise ToolError(_public_text(exc)) from None
        except Exception as exc:  # noqa: BLE001 - convert internal details to a fixed public error
            raise ToolError("tool execution failed") from exc

    return guarded


_TOOL_HANDLERS = {
    "primitive_search": _public_handler(_tool_primitive_search),
    "primitive_get": _public_handler(_tool_primitive_get),
    "find_reuse": _public_handler(_tool_find_reuse),
    "capability_compose": _public_handler(_tool_capability_compose),
    "primitive_corpus_status": _public_handler(_tool_primitive_corpus_status),
    "primitive_description_gaps": _public_handler(_tool_primitive_description_gaps),
    "record_reuse_outcome": _public_handler(_tool_record_reuse_outcome),
}


# --- JSON-RPC / MCP method handlers -----------------------------------------------------------------------------
def handle_initialize(params: dict) -> dict:
    # echo the client's protocolVersion when given (compat), else advertise ours
    client_pv = (params or {}).get("protocolVersion")
    if not isinstance(client_pv, str) or not client_pv.isprintable() or len(client_pv) > 64:
        client_pv = None
    return {
        "protocolVersion": client_pv or PROTOCOL_VERSION,
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        "capabilities": {"tools": {}},
    }


def handle_tools_list(params: dict) -> dict:
    return {"tools": TOOLS}


def _public_text(value: object, *, maximum: int = 512) -> str:
    """One-line printable text for public error surfaces; never echo terminal control sequences."""

    raw = str(value)
    printable = "".join(ch if ch.isprintable() else " " for ch in raw)
    return " ".join(printable.split())[:maximum]


def _handle_tools_call(params: object, *, fixtures: dict | None = None) -> dict:
    """Validate and invoke one tool; ``fixtures`` is reachable only by in-process self-tests."""

    if not isinstance(params, dict):
        return {"content": [{"type": "text", "text": "tools/call params must be an object"}], "isError": True}
    name = params.get("name")
    arguments = params.get("arguments", {})
    if not isinstance(name, str) or name not in _TOOL_HANDLERS:
        return {"content": [{"type": "text", "text": "unknown tool"}], "isError": True}
    if arguments is None:
        arguments = {}
    schema = _tool_schema(name)
    schema_failure = _schema_error(arguments, schema or {}) if schema is not None else "tool schema unavailable"
    if schema_failure:
        return {"content": [{"type": "text", "text": _public_text(schema_failure)}], "isError": True}
    handler = _TOOL_HANDLERS.get(name)
    try:
        result = handler(arguments, fixtures)
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}], "isError": False}
    except ToolError as e:
        return {"content": [{"type": "text", "text": _public_text(e)}], "isError": True}
    except Exception:  # noqa: BLE001 — public errors do not leak paths, internals, or attacker controls
        return {"content": [{"type": "text", "text": "tool execution failed"}], "isError": True}


def handle_tools_call(params: object) -> dict:
    """Production MCP entry: advertised schemas enforced, with no injectable fixture dependencies."""

    return _handle_tools_call(params)


def _handle_tools_call_for_test(params: object, **fixtures: object) -> dict:
    """Hermetic self-test entry. Fixtures are Python dependencies, never JSON-RPC arguments."""

    return _handle_tools_call(params, fixtures=fixtures)


def _error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def dispatch(request: dict) -> dict | None:
    """Route one JSON-RPC request -> a response dict, or None for notifications (requests with no `id`)."""
    if not isinstance(request, dict):
        return _error(None, _INVALID_REQUEST, "invalid request")
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    is_notification = "id" not in request

    if not isinstance(method, str):
        return None if is_notification else _error(req_id, _INVALID_REQUEST, "invalid request")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return None if is_notification else _error(req_id, _INVALID_PARAMS, "params must be an object")

    if method == "notifications/initialized":
        return None  # no-op notification (client confirming the handshake)
    try:
        if method == "initialize":
            result = handle_initialize(params)
        elif method == "tools/list":
            result = handle_tools_list(params)
        elif method == "tools/call":
            result = handle_tools_call(params)
        elif method == "ping":
            result = {}
        elif is_notification:
            return None  # unknown notification -> silently ignore (spec-compliant)
        else:
            return _error(req_id, _METHOD_NOT_FOUND, "method not found")
    except Exception:  # noqa: BLE001 — never leak implementation details over the public transport
        return None if is_notification else _error(req_id, _INTERNAL_ERROR, "internal error")
    return None if is_notification else {"jsonrpc": "2.0", "id": req_id, "result": result}


def serve(stdin=None, stdout=None) -> int:
    """The stdio main loop — delegates to the shared newline-delimited (MCP-spec) transport
    (scripts._mcp_stdio.serve): one JSON request per line, dispatch, write+flush non-None responses;
    a malformed line answers a -32700 parse error. Signature preserved for the self-test's stream injection."""
    return _mcp_stdio.serve(dispatch, stream_in=stdin, stream_out=stdout)


# --- proof: one search + one reuse check, OFFLINE, through the real tools/call envelope --------------------------
def _synthetic_search_index() -> dict:
    """A tiny in-memory index (public build_index over synthetic cards) — no persisted index, no network.

    One target card about OFAC sanctions screening + junk cards that share a high-df debris token, so the
    df-cap must prune and only the target carries the selective 'sanctions'/'ofac' tokens.
    """
    from scripts.build_primitive_search_index import build_index  # local import: only needed by the proof

    boundary = {"candidate": True, "serves_truth": False}
    cards = [{
        "primitive_id": "prim:test:target",
        "title": "Screen entity against OFAC sanctions list",
        "input_edge": "EntityRecord",
        "output_edge": "SanctionsScreeningReport",
        "blackbox": "Matches an entity record against the OFAC sanctions watchlist and emits a screening report.",
        "blocking_keys": ["sanctions", "ofac", "screening", "entityrecord"],
        **boundary,
    }]
    for i in range(30):  # junk sharing a high-df token so the index has something selective to prune against
        cards.append({
            "primitive_id": f"prim:test:junk{i:02d}",
            "title": f"Generic widget helper number {i}",
            "input_edge": "WidgetInput",
            "output_edge": "WidgetOutput",
            "blackbox": "A generic widget helper.",
            "blocking_keys": ["widget", "generic", "helper"],
            **boundary,
        })
    return _InternalFixtureIndex(build_index(cards))


def _self_test() -> int:
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    # MCP handshake + tool advertisement
    init = handle_initialize({"protocolVersion": PROTOCOL_VERSION})
    ck("initialize returns a protocolVersion", isinstance(init.get("protocolVersion"), str))
    ck("initialize advertises serverInfo.name", init.get("serverInfo", {}).get("name") == SERVER_NAME)
    ck("initialize advertises a tools capability", "tools" in init.get("capabilities", {}))

    listed = handle_tools_list({})["tools"]
    names = {t["name"] for t in listed}
    ck("tools/list returns the 7 capability-retrieval tools",
       names == {"primitive_search", "primitive_get", "find_reuse", "capability_compose",
                 "primitive_corpus_status", "primitive_description_gaps", "record_reuse_outcome"}, str(names))
    ck("each tool has an object inputSchema", all(t.get("inputSchema", {}).get("type") == "object" for t in listed))
    ck("each tool has a non-empty description", all(t.get("description") for t in listed))
    primitive_search_schema = next(t for t in listed if t["name"] == "primitive_search")["inputSchema"]
    ck(
        "primitive_search advertises the receipt-backed evidence lane",
        primitive_search_schema["properties"]["evidence"]["enum"] == ["any", "trusted_receipt"],
    )

    class _ReceiptFixtureFederation:
        def search_trusted_recipes(self, query: str, *, limit: int) -> dict:
            return {
                "query": query,
                "count": 1,
                "results": [{"primitive_id": "recipe/fixture", "proof_status": "passed",
                             "candidate": True, "serves_truth": False}],
                "recipe_receipt_authorization": {"authorized_candidates": 1,
                                                 "candidate": True, "serves_truth": False},
                "candidate": True,
                "serves_truth": False,
            }

    receipt_lane = run_primitive_search(
        "verified fixture",
        3,
        scope="all",
        federation=_ReceiptFixtureFederation(),  # type: ignore[arg-type]
        evidence="trusted_receipt",
    )
    ck(
        "trusted_receipt evidence uses the bounded receipt lane",
        receipt_lane["source_kind"] == "trusted_recipe_receipt_search"
        and receipt_lane["results"][0]["primitive_id"] == "recipe/fixture",
    )
    ck("each tool explicitly declares its required-input list",
       all(isinstance(t["inputSchema"].get("required"), list) for t in listed))

    # (1) ONE SEARCH — offline, through tools/call, against a synthetic in-memory index (no persisted index/network)
    index = _synthetic_search_index()
    call = _handle_tools_call_for_test({
        "name": "primitive_search",
        "arguments": {"query": "ofac sanctions screening entityrecord", "limit": 5},
    }, index=index)
    ck("primitive_search tools/call is not an error", call.get("isError") is False)
    ck("primitive_search returns text content", call["content"][0]["type"] == "text")
    search = json.loads(call["content"][0]["text"])
    ck("search returns the target primitive as top hit",
       bool(search["results"]) and search["results"][0]["primitive_id"] == "prim:test:target",
       str(search.get("count")))
    ck("search hits are governed candidates (serves_truth=false)",
       bool(search["results"]) and all(r["candidate"] is True and r["serves_truth"] is False for r in search["results"]))
    ck("search PRUNED (candidate_count < total_docs — O(candidates), not O(N))",
       0 < (search["pruning"]["candidate_count"] or 0) < (search["pruning"]["total_docs"] or 0),
       str(search["pruning"]))
    ck("search result itself is stamped serves_truth=false", search.get("serves_truth") is False)

    # ADAPTIVE-LEARNING LANE — OFF by default (bit-for-bit: no annotation), ON = annotated + hits preserved + logged.
    ck("adaptive lane defaults OFF: search response carries no adaptive annotation",
       os.environ.get(_ADAPTIVE_LEARNING_ENV) != "1" and "adaptive" not in search)
    from scripts.environment_request_learning import (  # noqa: PLC0415  self-test only — never a startup import
        LEARNING_DATA_DIR_ENVIRONMENT_VARIABLE,
        WORKSPACE_ROOT_ENVIRONMENT_VARIABLE,
        request_ledger_path,
    )
    _saved_adaptive_env = {name: os.environ.get(name) for name in
                           (_ADAPTIVE_LEARNING_ENV, LEARNING_DATA_DIR_ENVIRONMENT_VARIABLE,
                            WORKSPACE_ROOT_ENVIRONMENT_VARIABLE)}
    try:
        with tempfile.TemporaryDirectory() as adaptive_sandbox:
            os.environ[_ADAPTIVE_LEARNING_ENV] = "1"
            os.environ[LEARNING_DATA_DIR_ENVIRONMENT_VARIABLE] = str(Path(adaptive_sandbox) / "learning")
            os.environ[WORKSPACE_ROOT_ENVIRONMENT_VARIABLE] = adaptive_sandbox
            adaptive_call = _handle_tools_call_for_test({
                "name": "primitive_search",
                "arguments": {"query": "ofac sanctions screening entityrecord", "limit": 5},
            }, index=index)
            adaptive_search = json.loads(adaptive_call["content"][0]["text"])
            ck("adaptive lane ON: response annotated, request recorded, hit set preserved (reorder-only)",
               adaptive_search.get("adaptive", {}).get("enabled") is True
               and {r["primitive_id"] for r in adaptive_search["results"]}
               == {r["primitive_id"] for r in search["results"]}
               and request_ledger_path().exists(),
               str(adaptive_search.get("adaptive")))
    finally:
        for _name, _value in _saved_adaptive_env.items():
            if _value is None:
                os.environ.pop(_name, None)
            else:
                os.environ[_name] = _value

    class _FixtureFederation:
        def get(self, primitive_id, *, sync, load_core_payload):
            return {"primitive_id": primitive_id, "found": True, "sync": sync,
                    "payload": {"code": "def run(x): return x"} if load_core_payload else None,
                    "candidate": True, "serves_truth": False}

        def description_gaps(self, *, cursor, limit, pool):
            return {"cursor": cursor or None, "next_cursor": "prim:test:gap", "limit": limit,
                    "count": 1, "gaps": [{"primitive_id": "prim:test:gap",
                    "missing_fields": ["blackbox"], "candidate": True, "serves_truth": False}],
                    "pool": pool, "candidate": True, "serves_truth": False}

    get_call = _handle_tools_call_for_test({
        "name": "primitive_get",
        "arguments": {"primitive_id": "prim:test:target", "include_payload": True},
    }, federation=_FixtureFederation())
    got = json.loads(get_call["content"][0]["text"])
    ck("primitive_get resolves an exact id through the federation seam",
       get_call.get("isError") is False and got.get("found") is True
       and got.get("payload", {}).get("code", "").startswith("def run"))
    ck("primitive_get preserves candidate/serves_truth=false", got.get("candidate") is True
       and got.get("serves_truth") is False)

    gaps_call = _handle_tools_call_for_test({
        "name": "primitive_description_gaps",
        "arguments": {"limit": 3},
    }, federation=_FixtureFederation())
    gaps = json.loads(gaps_call["content"][0]["text"])
    ck("primitive_description_gaps returns a bounded metadata-only page",
       gaps_call.get("isError") is False and gaps.get("count") == 1
       and gaps["gaps"][0]["missing_fields"] == ["blackbox"])

    status_call = _handle_tools_call_for_test({
        "name": "primitive_corpus_status",
        "arguments": {},
    }, status_provider=lambda: {"search": {"unique_searchable_docs": 7},
                                "candidate": True, "serves_truth": False})
    status = json.loads(status_call["content"][0]["text"])
    ck("primitive_corpus_status is callable through the MCP envelope",
       status_call.get("isError") is False and status["search"]["unique_searchable_docs"] == 7)

    with tempfile.TemporaryDirectory(prefix="reuse_outcome_mcp_") as temp_dir:
        outcome_path = Path(temp_dir) / "outcomes.jsonl"
        outcome_call = _handle_tools_call_for_test({
            "name": "record_reuse_outcome",
            "arguments": {"primitive_id": "prim:test:target", "outcome": "reused",
                          "query": "raw private query", "session_id": "session-private"},
        }, outcome_path=outcome_path)
        outcome = json.loads(outcome_call["content"][0]["text"])
        stored = json.loads(outcome_path.read_text(encoding="utf-8"))
        ck("record_reuse_outcome stores digests but no raw query/session text",
           outcome_call.get("isError") is False and outcome.get("recorded") is True
           and stored.get("query_digest") and stored.get("session_digest")
           and "raw private query" not in outcome_path.read_text(encoding="utf-8")
           and "session-private" not in outcome_path.read_text(encoding="utf-8"))

    # (2) ONE REUSE CHECK — offline, through tools/call (reinvention_guard grounds on LOCAL registries, no network)
    reuse_call = handle_tools_call({
        "name": "find_reuse",
        "arguments": {"message": "Let me write a function to parse a PDF and extract text from scratch"},
    })
    ck("find_reuse tools/call is not an error", reuse_call.get("isError") is False)
    reuse = json.loads(reuse_call["content"][0]["text"])
    ck("find_reuse FIRES on a solved capability", reuse.get("fire") is True, str(reuse))
    ck("the fire is GROUNDED in real registry matches", bool(reuse.get("existing")) and any(reuse["existing"].values()))
    ck("the fire is governed (serves_truth=false)", reuse.get("serves_truth") is False)
    # precision discipline: quiet on genuinely-novel work
    quiet = json.loads(handle_tools_call({
        "name": "find_reuse",
        "arguments": {"message": "Let me build a novel quantum-resistant consensus protocol from scratch"},
    })["content"][0]["text"])
    ck("find_reuse stays QUIET on genuinely-novel work", quiet.get("fire") is False)

    # (3) ONE COMPOSE — offline, through tools/call, over a synthetic CHAINABLE corpus (no persisted index).
    # The exact shape the decompose-by-retrieval wire was proven on: a non-edge NL request the old 3-regex
    # front door nulled out, over a normalize->dedupe chain + distractors.
    boundary = {"candidate": True, "serves_truth": False}
    chainable_cards = [
        {"primitive_id": "p:norm", "title": "Normalize messy records",
         "blackbox": "Normalize and standardize messy raw records into a clean canonical schema.",
         "input_edge": "RawRecord", "output_edge": "NormalizedRecord", **boundary},
        {"primitive_id": "p:dedup", "title": "Deduplicate records",
         "blackbox": "Remove duplicate records by clustering near-identical normalized rows and keeping one canonical row.",
         "input_edge": "NormalizedRecord", "output_edge": "DedupedRecord", **boundary},
        {"primitive_id": "p:resize", "title": "Resize image",
         "blackbox": "Resize an image to target dimensions using bilinear interpolation.",
         "input_edge": "Image", "output_edge": "ResizedImage", **boundary},
    ]
    compose_call = _handle_tools_call_for_test({
        "name": "capability_compose",
        "arguments": {"request": "clean up and remove duplicate messy records"},
    }, cards=chainable_cards)
    ck("capability_compose tools/call is not an error", compose_call.get("isError") is False,
       str(compose_call["content"][0]["text"])[:200])
    composed = json.loads(compose_call["content"][0]["text"])
    ck("compose decomposed by RETRIEVAL (the wire, not the regex fast-path)",
       str(composed["decomposition"]["path_used"]).startswith("decompose_by_retrieval"),
       str(composed["decomposition"]["path_used"]))
    ck("compose found a route over the chainable corpus", composed["route"]["route_found"] is True,
       str(composed["route"]))
    ck("route steps are SIGNATURE views (id + edges), never card bodies",
       bool(composed["route"]["ordered_route"]) and all(
           set(s) == {"component_id", "input_edge", "output_edge", "operation"} and "blackbox" not in s
           for s in composed["route"]["ordered_route"]))
    ck("compose records which path each step took (step_log)",
       {e["step"] for e in composed["step_log"]} >= {"decompose", "search", "compose", "prove"})
    ck("compose result is a governed candidate (serves_truth=false)",
       composed.get("candidate") is True and composed.get("serves_truth") is False)

    # (4) the COMPILE-ONCE lane: a seeded identical request is served from the compiled-route cache with
    # ZERO recompose — hermetic (the hit path returns before any corpus/engine touch).
    from scripts.compiled_route_cache import CompiledRouteCache
    globals()["_COMPILED_ROUTES"] = CompiledRouteCache()
    seeded_request = "clean up and remove duplicate messy records"
    seed_sol = json.loads(compose_call["content"][0]["text"])  # reuse the composed view as the seed solution
    _compiled_routes().compile_once(seeded_request, solution={
        "route": {"route_found": composed["route"]["route_found"],
                  "composer_path": composed["route"]["composer_path"],
                  "ordered_route": composed["route"]["ordered_route"]},
        "decomposition": seed_sol.get("decomposition", {}), "remix": {}, "prove": {}, "step_log": []})
    cached_call = handle_tools_call({"name": "capability_compose", "arguments": {"request": seeded_request}})
    cached = json.loads(cached_call["content"][0]["text"])
    ck("an identical repeat request hits the compiled-route cache (zero recompose)",
       cached.get("compiled_route_hit") is True and cached.get("model_calls") == 0)
    ck("the cache hit carries the amortization ledger and stays a governed candidate",
       cached.get("amortization", {}).get("reuse_count") == 1 and cached.get("serves_truth") is False)
    globals()["_COMPILED_ROUTES"] = None  # reset: later assertions must not see the seeded cache

    # tool-level + JSON-RPC-envelope robustness
    ck("capability_compose with empty request -> in-band error",
       handle_tools_call({"name": "capability_compose", "arguments": {"request": " "}}).get("isError") is True)
    ck("primitive_search with empty query -> in-band error",
       handle_tools_call({"name": "primitive_search", "arguments": {"query": "  "}}).get("isError") is True)
    ck("find_reuse with empty message -> in-band error",
       handle_tools_call({"name": "find_reuse", "arguments": {}}).get("isError") is True)
    ck("primitive_get with empty id -> in-band error",
       handle_tools_call({"name": "primitive_get", "arguments": {}}).get("isError") is True)
    ck("unknown tool sets isError", handle_tools_call({"name": "does_not_exist", "arguments": {}}).get("isError") is True)
    fixture_attacks = {
        "index": ("primitive_search", {"query": "x", "index": {}}),
        "federation": ("primitive_get", {"primitive_id": "p", "federation": {}}),
        "cards": ("capability_compose", {"request": "x", "cards": []}),
        "status_provider": ("primitive_corpus_status", {"status_provider": "callable"}),
        "outcome_path": ("record_reuse_outcome", {
            "primitive_id": "p", "outcome": "reused", "outcome_path": "/tmp/escape",
        }),
    }
    for seam, (tool_name, arguments) in fixture_attacks.items():
        rejected = handle_tools_call({"name": tool_name, "arguments": arguments})
        ck(f"public JSON-RPC rejects undeclared fixture seam {seam}",
           rejected.get("isError") is True and "undeclared field" in rejected["content"][0]["text"])
    ck("public schema rejects oversized search limits",
       handle_tools_call({"name": "primitive_search", "arguments": {
           "query": "x", "limit": MAX_SEARCH_LIMIT + 1,
       }}).get("isError") is True)
    ck("public schema rejects non-object arguments",
       handle_tools_call({"name": "primitive_search", "arguments": []}).get("isError") is True)
    class _FailingFederation:
        def get(self, primitive_id, *, sync, load_core_payload):
            raise RuntimeError("private/path\x1b[31m")

    sanitized_failure = _handle_tools_call_for_test({
        "name": "primitive_get", "arguments": {"primitive_id": "p"},
    }, federation=_FailingFederation())
    ck("unexpected tool failures expose a fixed sanitized public error",
       sanitized_failure.get("isError") is True
       and sanitized_failure["content"][0]["text"] == "tool execution failed")
    resp = dispatch({"jsonrpc": "2.0", "id": 7, "method": "tools/list", "params": {}})
    ck("dispatch wraps a result in the JSON-RPC envelope",
       resp.get("jsonrpc") == "2.0" and resp.get("id") == 7 and "result" in resp)
    ck("notifications/initialized is a no-op (no response)",
       dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None)
    ck("unknown method -> JSON-RPC method-not-found",
       dispatch({"jsonrpc": "2.0", "id": 8, "method": "bogus"})["error"]["code"] == _METHOD_NOT_FOUND)

    if fails:
        print(f"\nFAIL - capability_retrieval_mcp_server: {len(fails)} of {checks} assertions failed")
        return 1
    print(f"PASS - capability_retrieval_mcp_server: stdlib MCP server over stdio (initialize + tools/list[7] + "
          f"tools/call) wiring primitive_search (federated full-corpus default; governed fixture pruned "
          f"{search['pruning']['candidate_count']}/"
          f"{search['pruning']['total_docs']} docs) + find_reuse (grounded reinvention guard) + capability_compose "
          f"(the agent-callable COMPOSE surface: decompose-by-retrieval path "
          f"{composed['decomposition']['path_used']}, route_found={composed['route']['route_found']}, "
          f"signature-view steps); {checks} assertions run OFFLINE; serves_truth=false; source corpus read-only "
          f"(derived search checkpoint may advance).")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    return serve()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
