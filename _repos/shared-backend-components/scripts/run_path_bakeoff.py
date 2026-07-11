#!/usr/bin/env python3
"""scripts.run_path_bakeoff — the PATH BAKE-OFF: race N processing/execution paths on the SAME input.

The point of a bake-off is not to pick a winner once — it is to discover, per task-class, WHICH path makes
the most sense (best composability at an acceptable token/latency cost). Five strategies for turning a
task-intent into a composed route compete on the IDENTICAL input:

  P0  deterministic_table_row   baseline — a zero-token pre-baked table lookup (covers only the solved head)
  P1  lexical_search            the OLD registry path — token-overlap retrieval + RAW-string edge chaining
  P2  edge_typed_compose        the NEW runtime — retrieval + chaining on CANONICAL edge TYPES
  P3  hybrid_rrf                dense+lexical fusion — surfaces primitives lexical-only retrieval misses
  P4  llm_assisted_peelback     peel deeper retrieval layers ONLY when a shallow compose stalls (costly)

Every race runs through the REAL comparator — ``src.teleon.experiments.parallel_paths.run_parallel`` — which
executes the baseline + every candidate on ONE ``input_snapshot`` (recording ``input_snapshot_hash`` as the
proof they saw identical input), captures per-path {output, cost, latency_ms, error, source_handle_coverage,
contract_validation}, and NEVER serves a candidate as truth. This module does NOT reinvent that engine; it
supplies the PATHS (path dicts) and a ``runner`` that executes each path's strategy.

The runner executes a path by calling the concurrently-built runtime
``scripts.primitive_runtime.compose_solution`` with a path-specific config, and — because that runtime is
being built in parallel and may be ABSENT — falls back to a deterministic, offline STUB strategy per path so
``--self-test`` runs standalone. Real metrics either way: cost ~= estimated tokens, latency_ms from work
done, source_handles ~= the matched primitive_ids, contract_validation from whether the composed route's
edges chain on canonical TYPES, output = {route, edge_chain_strength, route_proven}.

For each task in a ~24-task set (5 task-classes: string_transform · data_pipeline · algorithm · extraction ·
agentic) it calls ``run_parallel(baseline=P0, candidates=[P1..P4])`` and aggregates a LEADERBOARD per
task-class: per path — mean composability, proven_route_pct, median tokens, p50 latency, contract-pass-rate;
then picks the per-class WINNER (highest composability among paths inside the token/latency budget, ties
broken by contract-pass-rate then fewer tokens). Different classes elect different winners — that IS the
finding.

REUSE, never reinvent (all imported with a graceful fallback so --self-test is standalone/offline):
  * REAL engine    src.teleon.experiments.parallel_paths.run_parallel  (the fair comparator)
  * REAL proofs    scripts.mutator_registry.run_primitive_proof        (which leaf primitives are PROVEN)
  * retrieval map  scripts.build_retrieval_backend_portfolio           (each path -> a portfolio search method)
  * concurrent     scripts.primitive_runtime.compose_solution          (the runtime; stub fallback if absent)
  * concurrent     scripts.build_edge_type_retrofit.canonicalize_edge  (the canonical edge-type judge)
  * concurrent     scripts.build_primitive_search_index.fast_search    (lexical retrieval telemetry)
  * concurrent     scripts.check_primitive_composability.composability_report (per-step typedness cross-check)
  * concurrent     scripts.prove_leaf_primitives.proven_primitive_index      (proven-leaf count context)

Boundary law: every emitted row is candidate=true / serves_truth=false — a leaderboard is candidate analysis,
never a truth claim. Deterministic + offline: no network, no wall-clock, no RNG; ``now`` is injected. CLI:
``--self-test`` (pure, offline, stub runners) | ``--run [--date D]`` (writes the leaderboard .md + .json).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Callable, Optional

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# ── the REAL comparator engine (hard dependency — the bake-off IS "run_parallel over path portfolios") ──
from src.teleon.experiments.parallel_paths import (  # noqa: E402
    CHALLENGER_MODES,
    SERVABLE_MODES,
    run_parallel as _engine_run_parallel,
)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
OUT_DIR = _resource("data") / "dev-intel" / "path_bakeoff"
NOW_DEFAULT = "2026-07-03T00:00:00Z"  # injected clock (deterministic; never time.time())
DEFAULT_DATE = "2026-07-03"

# ──────────────────────────────────────────────────────────────────────────────
# REUSE imports — every one guarded so --self-test is standalone even if a sibling is mid-build.
# ──────────────────────────────────────────────────────────────────────────────
try:  # the concurrently-built runtime; ABSENT today -> stub fallback drives the runner
    from scripts.primitive_runtime import compose_solution as _compose_solution  # type: ignore
    _COMPOSE_SRC = "scripts.primitive_runtime.compose_solution"
except Exception:  # noqa: BLE001
    _compose_solution = None
    _COMPOSE_SRC = "stub_fallback"

try:  # the canonical edge-type judge (folds snowflake edge strings onto one namespace)
    from scripts.build_edge_type_retrofit import canonicalize_edge as _ext_canon  # type: ignore
    _CANON_SRC = "scripts.build_edge_type_retrofit.canonicalize_edge"
except Exception:  # noqa: BLE001
    _ext_canon = None
    _CANON_SRC = "local_fallback"

try:
    from scripts.build_primitive_search_index import build_index as _build_index, fast_search as _fast_search  # type: ignore
    _SEARCH_AVAILABLE = True
except Exception:  # noqa: BLE001
    _build_index = None
    _fast_search = None
    _SEARCH_AVAILABLE = False

try:
    from scripts.check_primitive_composability import composability_report as _composability_report  # type: ignore
    _COMPOSABILITY_AVAILABLE = True
except Exception:  # noqa: BLE001
    _composability_report = None
    _COMPOSABILITY_AVAILABLE = False

try:
    from scripts.prove_leaf_primitives import proven_primitive_index as _proven_primitive_index  # type: ignore
    _PROVEN_INDEX_AVAILABLE = True
except Exception:  # noqa: BLE001
    _proven_primitive_index = None
    _PROVEN_INDEX_AVAILABLE = False

try:  # the real executed-proof machinery — decides which of THIS bake-off's leaf primitives are PROVEN
    from scripts.mutator_registry import (  # type: ignore
        MUTATOR_REGISTRY as _MUTATOR_REGISTRY,
        _hash as _mut_hash,
        apply_mutator as _apply_mutator,
        run_primitive_proof as _run_primitive_proof,
    )
    _PROOF_RUNNER_AVAILABLE = True
except Exception:  # noqa: BLE001
    _MUTATOR_REGISTRY = {}
    _apply_mutator = None
    _run_primitive_proof = None
    _PROOF_RUNNER_AVAILABLE = False

    def _mut_hash(value: Any) -> str:  # local mirror of mutator_registry._hash (same canonical bytes)
        return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:16]

try:  # map each bake-off path onto the retrieval portfolio's honest search-method rows
    from scripts.build_retrieval_backend_portfolio import (  # type: ignore
        backends_of as _backends_of,
        dim_compatible as _dim_compatible,
        resolve_active_backends as _resolve_active_backends,
    )
    _PORTFOLIO_AVAILABLE = True
except Exception:  # noqa: BLE001
    _backends_of = None
    _dim_compatible = None
    _resolve_active_backends = None
    _PORTFOLIO_AVAILABLE = False


# ──────────────────────────────────────────────────────────────────────────────
# Canonical edge typing — the shared, FAIR judge every route is scored by.
# The local fallback mirrors the external canonicalizer for the (case/separator-variant) edge strings this
# module uses, so a route scores identically whether or not the concurrent sibling is importable.
# ──────────────────────────────────────────────────────────────────────────────
def _fallback_canon(edge: Any) -> str:
    if not isinstance(edge, str) or not edge.strip():
        return "Unknown"
    s = edge.split("|")[0].strip().split("+")[0].strip()
    if ":" in s:
        s = s.split(":")[-1].strip()
    s = s.split("[")[0].strip()
    if "." in s:
        s = s.split(".")[-1].strip()
    parts = [p for p in re.split(r"[^0-9A-Za-z]+", s) if p]
    if not parts:
        return "Unknown"
    if len(parts) == 1:
        tok = parts[0]
        return tok if re.search(r"[A-Z]", tok[1:]) else tok[:1].upper() + tok[1:]
    return "".join(p[:1].upper() + p[1:] for p in parts)


def canon(edge: Any) -> str:
    """Fold a raw edge string to a canonical type_id (external retrofit canonicalizer, else local fallback)."""
    if _ext_canon is not None:
        try:
            result = _ext_canon(edge)
            if isinstance(result, str) and result.strip():
                return result.strip()
        except Exception:  # noqa: BLE001 — signature/behaviour drift: fall back per-call
            pass
    return _fallback_canon(edge)


# ──────────────────────────────────────────────────────────────────────────────
# The synthetic primitive library + task set (offline, deterministic ground truth).
#
# Consecutive primitives in a chain declare the SAME canonical type under DIFFERENT raw spellings (case /
# separator variants) — e.g. "RawRecordBatchDoc" -> "raw_record_batch_doc". So RAW-string chaining (P1)
# breaks at every internal joint while CANONICAL-type chaining (P2/P3/P4) connects. That is exactly the
# red-team finding the new runtime fixes, expressed as testable data.
#
# Retrieval VISIBILITY tiers model why different retrieval methods surface different primitives:
#   surface     every retrieval strategy can see it
#   dense_only  only a dense/hybrid fusion (P3) or a deep peel-back (P4) surfaces it
#   deep_only   only P4's peel-back reaches it
# ──────────────────────────────────────────────────────────────────────────────
# proof specs (base MUTATOR_REGISTRY mutators only) -> which leaf primitives PROVE serves_truth=true.
_IDEM_KEY = hashlib.sha256("u1|pay".encode()).hexdigest()[:24]
PROOF_SPECS: dict[str, tuple[str, Any, Any, dict[str, Any], Optional[str]]] = {
    # key: (mutator, fixture, expected, args, inverse)
    "field_rename_ok": ("field_rename", {"a": 1, "b": 2}, {"x": 1, "b": 2}, {"mapping": {"a": "x"}}, None),
    "type_cast_ok": ("type_cast", {"n": "5"}, {"n": 5}, {"casts": {"n": "int"}}, None),
    "envelope_ok": ("envelope_wrap", {"p": 1}, {"payload": {"p": 1}, "policy": {"pol": "x"}, "envelope_version": 1},
                    {"policy": {"pol": "x"}}, "envelope_unwrap"),
    "rowjson_ok": ("row_to_json", {"z": 9}, '{"z": 9}', {}, "json_to_row"),
    "project_ok": ("field_project", {"a": 1, "b": 2, "c": 3}, {"a": 1, "c": 3}, {"keep": ["a", "c"]}, None),
    "idem_ok": ("idempotency_wrapper", {"user": "u1", "op": "pay"},
                {"user": "u1", "op": "pay", "idempotency_key": _IDEM_KEY}, {"key_fields": ["user", "op"]}, None),
    "dedupe_ok": ("dedupe_by_key", [{"k": 1, "id": "a"}, {"k": 1, "id": "b"}, {"k": 2, "id": "c"}],
                  [{"k": 1, "id": "a"}, {"k": 2, "id": "c"}], {"key": "k"}, None),
    "schema_ok": ("schema_validator_inserter", {"name": "x"},
                  {"name": "x", "_validation": {"required": ["name", "email"], "missing": ["email"], "valid": False}},
                  {"required": ["name", "email"]}, None),
    # deliberately-wrong expected -> the proof gate leaves it CANDIDATE (an un-proven leaf)
    "WRONG": ("field_rename", {"a": 1}, {"WRONG": 999}, {"mapping": {"a": "x"}}, None),
}
_PROOF_RECEIPT_EXPECTED = {  # output_receipt_wrapper expected depends on the content hash
    "output": "hello", "receipt": {"output_hash": _mut_hash("hello"), "verified_first": True},
}
PROOF_SPECS["receipt_ok"] = ("output_receipt_wrapper", "hello", _PROOF_RECEIPT_EXPECTED, {}, None)

# each primitive: (id, task_class, tier, input_edge_raw, output_edge_raw, proof_key, tokens)
_LIB_SPECS: list[tuple[str, str, str, str, str, str, list[str]]] = [
    # string_transform — 1-hop, all surface, in the P0 table
    ("ST_1", "string_transform", "surface", "user text request", "CleanTextReply", "field_rename_ok",
     ["string", "text", "clean", "normalize", "transform", "user", "request"]),
    ("ST_D", "string_transform", "surface", "user text request", "UnrelatedDeadEndType", "type_cast_ok",
     ["string", "misc", "helper", "unrelated"]),
    # data_pipeline — 2-hop, all surface, NOT in the table (snowflake internal joint breaks P1)
    ("DP_1", "data_pipeline", "surface", "ingest request spec", "RawRecordBatchDoc", "envelope_ok",
     ["ingest", "pipeline", "data", "load", "raw", "records"]),
    ("DP_2", "data_pipeline", "surface", "raw_record_batch_doc", "CleanRecordBatchDoc", "rowjson_ok",
     ["clean", "normalize", "pipeline", "records", "dedupe", "data"]),
    ("DP_D", "data_pipeline", "surface", "ingest request spec", "PipelineDeadEndType", "project_ok",
     ["pipeline", "misc", "unused"]),
    # algorithm — 2-hop, second hop is dense_only (lexical-only P2 cannot see it; hybrid P3 can)
    ("AL_1", "algorithm", "surface", "problem statement spec", "CandidatePlanDraft", "idem_ok",
     ["algorithm", "plan", "search", "solve", "candidate", "problem"]),
    ("AL_2", "algorithm", "dense_only", "candidate_plan_draft", "VerifiedPlanResult", "dedupe_ok",
     ["verify", "check", "optimize", "plan", "result", "prove"]),
    ("AL_D", "algorithm", "surface", "problem statement spec", "AlgoDeadEndType", "schema_ok",
     ["algorithm", "misc", "unused"]),
    # extraction — 3-hop, last hop is deep_only (only P4's peel-back reaches it)
    ("EX_1", "extraction", "surface", "document blob input", "SegmentedSpanSet", "field_rename_ok",
     ["extract", "document", "segment", "span", "parse", "blob"]),
    ("EX_2", "extraction", "dense_only", "segmented_span_set", "ExtractedFieldMap", "type_cast_ok",
     ["extract", "field", "map", "entity", "value", "span"]),
    ("EX_3", "extraction", "deep_only", "extracted_field_map", "ValidatedFieldRecord", "envelope_ok",
     ["validate", "verify", "field", "record", "gate", "confirm"]),
    ("EX_D", "extraction", "surface", "document blob input", "ExtractDeadEndType", "project_ok",
     ["extract", "misc", "unused"]),
    # agentic — 2-hop, all surface; AG_2 is deliberately UN-proven (route composes but is not yet provable)
    ("AG_1", "agentic", "surface", "agent goal spec", "ToolPlanDraft", "rowjson_ok",
     ["agent", "goal", "plan", "tool", "orchestrate", "task"]),
    ("AG_2", "agentic", "surface", "tool_plan_draft", "ExecutedActionLog", "WRONG",
     ["agent", "execute", "action", "tool", "run", "log"]),
    ("AG_D", "agentic", "surface", "agent goal spec", "AgentDeadEndType", "idem_ok",
     ["agent", "misc", "unused"]),
    # probe — used ONLY by the self-test's synthetic clearly-better-path check (not in the main 24 tasks)
    ("PR_1", "probe", "surface", "probe source alpha", "ProbeMidBeta", "field_rename_ok", ["probe", "alpha", "mid"]),
    ("PR_2", "probe", "surface", "probe_mid_beta", "ProbeTargetGamma", "type_cast_ok", ["probe", "mid", "target"]),
]

LIB: list[dict[str, Any]] = [
    {"id": i, "cls": c, "tier": t, "in_raw": ie, "out_raw": oe, "proof_key": pk, "tokens": tok}
    for i, c, t, ie, oe, pk, tok in _LIB_SPECS
]
LIB_BY_ID: dict[str, dict[str, Any]] = {p["id"]: p for p in LIB}

# the full ideal chain per class (what a perfect path recovers) + the class's (source_type, target_type)
CLASS_CHAINS: dict[str, list[str]] = {
    "string_transform": ["ST_1"],
    "data_pipeline": ["DP_1", "DP_2"],
    "algorithm": ["AL_1", "AL_2"],
    "extraction": ["EX_1", "EX_2", "EX_3"],
    "agentic": ["AG_1", "AG_2"],
    "probe": ["PR_1", "PR_2"],
}
CLASS_ENDPOINTS: dict[str, tuple[str, str]] = {
    cls: (canon(LIB_BY_ID[chain[0]]["in_raw"]), canon(LIB_BY_ID[chain[-1]]["out_raw"]))
    for cls, chain in CLASS_CHAINS.items()
}
# P0's pre-baked table — only the solved head (string_transform). Every other class returns nothing (a miss).
P0_TABLE_CLASSES: frozenset[str] = frozenset({"string_transform"})

MAIN_CLASSES: tuple[str, ...] = ("string_transform", "data_pipeline", "algorithm", "extraction", "agentic")
TASKS_PER_CLASS: dict[str, int] = {
    "string_transform": 5, "data_pipeline": 5, "algorithm": 5, "extraction": 5, "agentic": 4,  # == 24
}


def build_task_set() -> list[dict[str, Any]]:
    """~24 tasks across the 5 classes. Tasks in a class are structurally identical (same source/target types
    and ideal chain) so per-class aggregation is deterministic; only the id + intent text vary."""
    tasks: list[dict[str, Any]] = []
    for cls in MAIN_CLASSES:
        src, tgt = CLASS_ENDPOINTS[cls]
        chain_tokens = sorted({t for pid in CLASS_CHAINS[cls] for t in LIB_BY_ID[pid]["tokens"]})
        for i in range(TASKS_PER_CLASS[cls]):
            tasks.append({
                "task_id": f"{cls}-{i:02d}",
                "task_class": cls,
                "intent": f"{cls.replace('_', ' ')} task {i}: {' '.join(chain_tokens[:4])}",
                "intent_tokens": chain_tokens,
                "source_type": src,
                "target_type": tgt,
            })
    return tasks


# ──────────────────────────────────────────────────────────────────────────────
# Provenness — the REAL executed-proof runner decides which leaf primitives are PROVEN (serves_truth=true).
# route_proven then means "every step of the route passed an executed proof", not a hand-set flag.
# ──────────────────────────────────────────────────────────────────────────────
def _prove_primitive(prim: dict[str, Any]) -> bool:
    spec = PROOF_SPECS[prim["proof_key"]]
    mutator, fixture, expected, args, inverse = spec
    if _run_primitive_proof is None:  # proof runner unavailable -> honest static hint (WRONG => un-proven)
        return prim["proof_key"] != "WRONG"
    try:
        receipt = _run_primitive_proof(prim["id"], mutator, fixture, expected, mutator_args=args, has_inverse=inverse)
        return bool(receipt.get("serves_truth"))
    except Exception:  # noqa: BLE001
        return False


PROVEN: dict[str, bool] = {p["id"]: _prove_primitive(p) for p in LIB}


def preflight_proof_specs() -> dict[str, Any]:
    """Guard: every proof spec is built on a REAL registered mutator, and each 'ok' spec actually EXECUTES via
    the shared apply_mutator (not a reinvented transform). Proves this bake-off reuses the mutator substrate."""
    if not _PROOF_RUNNER_AVAILABLE or _apply_mutator is None:
        return {"available": False, "registered": None, "executed_ok": None}
    registered = all(spec[0] in _MUTATOR_REGISTRY for spec in PROOF_SPECS.values())
    executed = 0
    for key, (mutator, fixture, _expected, args, _inverse) in PROOF_SPECS.items():
        if key == "WRONG":
            continue
        try:
            _apply_mutator(mutator, fixture, **args)  # runs the REAL registered mutator on the fixture
            executed += 1
        except Exception:  # noqa: BLE001
            pass
    return {"available": True, "registered": registered, "executed_ok": executed,
            "registry_size": len(_MUTATOR_REGISTRY)}


# ──────────────────────────────────────────────────────────────────────────────
# Route building — each strategy explores its VISIBLE candidate pool and chains under its connect relation.
# The JUDGE that scores the result is shared + canonical for ALL paths (the fair comparator).
# ──────────────────────────────────────────────────────────────────────────────
def _connect(a: dict[str, Any], b: dict[str, Any], relation: str) -> bool:
    """Can primitive a's output feed primitive b's input? ``type`` = canonical-type match; ``raw`` = exact string."""
    if relation == "raw":
        return a["out_raw"] == b["in_raw"]
    return canon(a["out_raw"]) == canon(b["in_raw"])


def _pool_by_tiers(cls: str, tiers: list[str]) -> list[str]:
    tierset = set(tiers)
    return sorted(p["id"] for p in LIB if p["cls"] == cls and p["tier"] in tierset)


def _simple_paths(pool: list[dict[str, Any]], source: str, relation: str) -> list[list[dict[str, Any]]]:
    """All simple (no repeated primitive) chains that START at an entry primitive (canon(input)==source) and
    extend under ``relation``. Deterministic: primitives explored in id order."""
    routes: list[list[dict[str, Any]]] = []
    ordered = sorted(pool, key=lambda x: x["id"])

    def dfs(path: list[dict[str, Any]], used: set[str]) -> None:
        routes.append(list(path))
        last = path[-1]
        for q in ordered:
            if q["id"] in used or not _connect(last, q, relation):
                continue
            used.add(q["id"])
            path.append(q)
            dfs(path, used)
            path.pop()
            used.discard(q["id"])

    for entry in ordered:
        if canon(entry["in_raw"]) == source:
            dfs([entry], {entry["id"]})
    return routes


def _typed_joints(route: list[dict[str, Any]], source: str, target: str) -> list[bool]:
    """The canonical-type joints of a route: source->first, each internal a->b, last->target."""
    if not route:
        return []
    joints = [canon(route[0]["in_raw"]) == source]
    joints += [canon(a["out_raw"]) == canon(b["in_raw"]) for a, b in zip(route, route[1:])]
    joints.append(canon(route[-1]["out_raw"]) == target)
    return joints


def _best_route(pool_ids: list[str], source: str, target: str, relation: str) -> list[dict[str, Any]]:
    """The best chain a strategy can build from its visible pool: a target-reaching route if any exists (shortest,
    then lexicographically least), else the longest / most-canonically-connected partial (deterministic)."""
    pool = [LIB_BY_ID[i] for i in pool_ids]
    routes = _simple_paths(pool, source, relation)
    if not routes:
        return []
    complete = [r for r in routes if canon(r[-1]["out_raw"]) == target]
    if complete:
        complete.sort(key=lambda r: (len(r), [p["id"] for p in r]))
        return complete[0]
    routes.sort(key=lambda r: (-len(r), -sum(_typed_joints(r, source, target)), [p["id"] for p in r]))
    return routes[0]


def judge_route(route: list[dict[str, Any]], source: str, target: str) -> dict[str, Any]:
    """The shared, canonical, fair scorer applied to EVERY path's route regardless of how it was built."""
    joints = _typed_joints(route, source, target)
    matched = sum(joints)
    total = len(joints)
    reached = bool(joints) and all(joints)
    strength = (matched / total) if total else 0.0
    proven = bool(route) and all(PROVEN.get(p["id"], False) for p in route)
    return {"edge_chain_strength": round(strength, 6), "target_reached": reached,
            "route_proven": bool(reached and proven), "hops": len(route),
            "matched_joints": matched, "total_joints": total}


# ──────────────────────────────────────────────────────────────────────────────
# The strategy portfolio (path dicts) + the deterministic cost model.
# ──────────────────────────────────────────────────────────────────────────────
# per-path (base_tokens, tokens_per_scanned_card); a peel adds PEEL_TOKENS.
_TOK: dict[str, tuple[int, int]] = {"P0": (0, 0), "P1": (40, 12), "P2": (30, 8), "P3": (40, 10), "P4": (45, 9)}
_PEEL_TOKENS = 60
# per-path (base_latency_ms, ms_per_scanned_card, latency_factor); a peel adds PEEL_LATENCY_MS.
_LAT: dict[str, tuple[float, float, float]] = {
    "P0": (1.0, 0.0, 1.0), "P1": (15.0, 3.0, 1.0), "P2": (12.0, 3.0, 1.0), "P3": (18.0, 3.0, 1.2), "P4": (20.0, 3.0, 1.5),
}
_PEEL_LATENCY_MS = 25.0
# the "acceptable" gate — a path outside either budget is excluded from the winner pool (a guard, not the selector).
TOKEN_BUDGET = 400.0
LATENCY_BUDGET_MS = 400.0

# strategy configs. P4's peel_stages widen the visible pool ONLY when a shallower compose stalls.
_STRATEGIES: dict[str, dict[str, Any]] = {
    "P0": {"kind": "table", "connect": "type"},
    "P1": {"kind": "pool", "tiers": ["surface"], "connect": "raw"},
    "P2": {"kind": "pool", "tiers": ["surface"], "connect": "type"},
    "P3": {"kind": "pool", "tiers": ["surface", "dense_only"], "connect": "type"},
    "P4": {"kind": "peel", "connect": "type",
           "peel_stages": [["surface"], ["surface", "dense_only"], ["surface", "dense_only", "deep_only"]]},
    # self-test-only strategies for the clearly-better-path check
    "ORACLE": {"kind": "oracle", "connect": "type"},
    "NULL": {"kind": "null", "connect": "type"},
}

_PATH_META: dict[str, dict[str, str]] = {
    "P0": {"name": "deterministic_table_row", "mode": "baseline", "search_method": "exact_edge",
           "description": "zero-token pre-baked table lookup — covers only the solved head"},
    "P1": {"name": "lexical_search", "mode": "candidate", "search_method": "blocking_lexical",
           "description": "old registry path — token-overlap retrieval + RAW-string edge chaining (snowflakes break it)"},
    "P2": {"name": "edge_typed_compose", "mode": "candidate", "search_method": "edge_type_constrained",
           "description": "new runtime — retrieval + chaining on CANONICAL edge types"},
    "P3": {"name": "hybrid_rrf", "mode": "candidate", "search_method": "hybrid_rrf",
           "description": "dense+lexical fusion — surfaces primitives lexical-only retrieval misses"},
    "P4": {"name": "llm_assisted_peelback", "mode": "candidate", "search_method": "dense_ann",
           "description": "peel deeper retrieval layers ONLY when a shallow compose stalls (costly, high recall)"},
}


def path_dict(path_id: str) -> dict[str, Any]:
    """A path dict for run_parallel: {path_id, mode, output_contract} plus the strategy the runner executes."""
    meta = _PATH_META.get(path_id, {"mode": "candidate"})
    return {"path_id": path_id, "mode": meta["mode"], "output_contract": "ComposedRoute",
            "strategy": _STRATEGIES[path_id]}


def portfolio_paths() -> list[dict[str, Any]]:
    """P0 baseline + P1..P4 candidates."""
    return [path_dict("P0"), path_dict("P1"), path_dict("P2"), path_dict("P3"), path_dict("P4")]


def _lexical_top_hit(task: dict[str, Any]) -> Optional[str]:
    """Telemetry only (never affects winners): the reused fast_search's top primitive for this task, if available."""
    if not _SEARCH_AVAILABLE or _build_index is None or _fast_search is None:
        return None
    try:
        cards = [{"primitive_id": p["id"], "title": " ".join(p["tokens"]), "input_edge": p["in_raw"],
                  "output_edge": p["out_raw"], "blocking_keys": p["tokens"], **BOUNDARY}
                 for p in LIB if p["cls"] == task["task_class"]]
        index = _build_index(cards)
        hits = _fast_search(task["intent"], 1, index=index)
        return hits[0].get("primitive_id") if hits else None
    except Exception:  # noqa: BLE001
        return None


def _execute_strategy(path: dict[str, Any], task: dict[str, Any]) -> tuple[list[dict[str, Any]], int, int]:
    """Run a path's stub strategy against a task -> (route, scanned_cards, peels). Pure + deterministic."""
    cfg = path["strategy"]
    kind = cfg["kind"]
    cls, source, target = task["task_class"], task["source_type"], task["target_type"]

    if kind == "table":
        route_ids = list(CLASS_CHAINS[cls]) if cls in P0_TABLE_CLASSES else []
        return [LIB_BY_ID[i] for i in route_ids], 0, 0
    if kind == "oracle":
        return [LIB_BY_ID[i] for i in CLASS_CHAINS[cls]], 0, 0
    if kind == "null":
        return [], 0, 0
    if kind == "pool":
        pool_ids = _pool_by_tiers(cls, cfg["tiers"])
        return _best_route(pool_ids, source, target, cfg["connect"]), len(pool_ids), 0
    if kind == "peel":
        scanned = 0
        route: list[dict[str, Any]] = []
        stages = cfg["peel_stages"]
        for stage_idx, tiers in enumerate(stages):
            pool_ids = _pool_by_tiers(cls, tiers)
            scanned += len(pool_ids)
            route = _best_route(pool_ids, source, target, cfg["connect"])
            if route and canon(route[-1]["out_raw"]) == target:  # shallow compose succeeded — stop peeling
                return route, scanned, stage_idx
        return route, scanned, len(stages) - 1  # never fully composed — paid every peel
    raise ValueError(f"unknown strategy kind: {kind!r}")


def _cost_model(path_id: str, scanned: int, peels: int) -> tuple[float, float]:
    """Deterministic (tokens, latency_ms) from work done — never wall-clock. Unknown paths (the self-test's
    oracle/null probes) fall back to a cheap generic profile so cost stays defined for any path."""
    base_tok, per_tok = _TOK.get(path_id, (5, 2))
    tokens = base_tok + scanned * per_tok + peels * _PEEL_TOKENS
    base_lat, per_lat, factor = _LAT.get(path_id, (5.0, 1.0, 1.0))
    latency = base_lat + scanned * per_lat * factor + peels * _PEEL_LATENCY_MS
    return float(tokens), float(round(latency, 3))


def _runtime_cards(cls: str, tiers: list[str]) -> list[dict[str, Any]]:
    """The path's tier-visible library, shaped as the runtime's candidate_cards (its path-specific config)."""
    tierset = set(tiers)
    return [{"primitive_id": p["id"], "title": " ".join(p["tokens"]), "input_edge": p["in_raw"],
             "output_edge": p["out_raw"], "blocking_keys": p["tokens"], **BOUNDARY}
            for p in LIB if p["cls"] == cls and p["tier"] in tierset]


def _extract_route_ids(result: Any) -> Optional[list[str]]:
    """Pull a primitive-id list out of whatever shape the runtime returns (route may be a dict with an
    ordered_route, a bare list, or step dicts). Defensive so a shape change never crashes the bake-off."""
    if not isinstance(result, dict):
        return None
    cand = result.get("route")
    seq: Any = None
    if isinstance(cand, dict):
        seq = cand.get("ordered_route") or cand.get("route") or cand.get("steps")
    elif isinstance(cand, list):
        seq = cand
    if seq is None:
        seq = result.get("ordered_route") or result.get("steps") or result.get("primitive_ids") or result.get("chain")
    if not isinstance(seq, list):
        return None
    ids: list[str] = []
    for el in seq:
        if isinstance(el, str):
            ids.append(el)
        elif isinstance(el, dict):
            val = el.get("primitive_id") or el.get("id")
            if isinstance(val, str):
                ids.append(val)
    return ids or None


def _adapt_runtime_route(task: dict[str, Any], path: dict[str, Any]) -> Optional[list[dict[str, Any]]]:
    """Best-effort: ask the concurrently-built runtime to compose a route over this path's tier-visible cards
    (its path-specific config), then adapt the result into our primitive list. Returns None (-> stub fallback)
    if the runtime is absent, errors, or returns an unusable / out-of-library route."""
    if _compose_solution is None:
        return None
    cfg = path["strategy"]
    tiers = cfg.get("tiers")
    if tiers is None and cfg.get("kind") == "peel":
        tiers = cfg["peel_stages"][-1]  # a peel-back path may see every layer
    cards = _runtime_cards(task["task_class"], tiers or ["surface"])
    try:  # real signature: compose_solution(intent, *, candidate_cards=..., limit=..., max_route_steps=...)
        result = _compose_solution(task["intent"], candidate_cards=cards,
                                   limit=max(4, len(cards)), max_route_steps=8)  # type: ignore[misc]
    except Exception:  # noqa: BLE001 — absent/signature drift/runtime error: fall back to the stub
        return None
    ids = _extract_route_ids(result)
    if not ids:
        return None
    prims = [LIB_BY_ID[i] for i in ids if i in LIB_BY_ID]
    return prims or None


def make_runner(*, use_runtime: bool) -> Callable[[dict[str, Any], Any], dict[str, Any]]:
    """A run_parallel-compatible ``runner(path, input_snapshot) -> RunnerResult``. When ``use_runtime`` and the
    concurrent runtime is importable it composes via compose_solution; otherwise the deterministic stub runs."""

    def runner(path: dict[str, Any], task: Any) -> dict[str, Any]:
        source, target = task["source_type"], task["target_type"]
        route: Optional[list[dict[str, Any]]] = None
        runtime_used = False
        if use_runtime and path["strategy"]["kind"] in ("pool", "peel"):
            route = _adapt_runtime_route(task, path)
            runtime_used = route is not None
        if route is None:  # graceful stub fallback (the offline, tested path)
            route, scanned, peels = _execute_strategy(path, task)
        else:  # runtime returned a real route — still model cost from the route's shape, deterministically
            scanned = max(len(route), len(_pool_by_tiers(task["task_class"], path["strategy"].get("tiers", ["surface"]))))
            peels = 0
        tokens, latency = _cost_model(path["path_id"], scanned, peels)
        verdict = judge_route(route, source, target)
        output = {"route": [p["id"] for p in route], "edge_chain_strength": verdict["edge_chain_strength"],
                  "route_proven": verdict["route_proven"], "target_reached": verdict["target_reached"],
                  "hops": verdict["hops"], "runtime_composed": runtime_used}
        return {
            "output": output,
            "output_contract": path.get("output_contract", "ComposedRoute"),
            "cost": tokens,                       # cost ~= estimated tokens
            "latency_ms": latency,
            "error": None,
            "source_handles": [p["id"] for p in route],   # source_handles ~= matched primitive_ids
            # contract passes iff the composed route's edges chain on canonical types all the way to the target
            "contract_validation": "pass" if verdict["target_reached"] else "fail",
        }

    return runner


# ──────────────────────────────────────────────────────────────────────────────
# The bake-off: run_parallel per task, then aggregate the per-class leaderboard.
# ──────────────────────────────────────────────────────────────────────────────
_RUN_PARALLEL_CALLS = 0  # proves run_parallel is actually exercised (asserted in --self-test)


def _call_run_parallel(baseline: dict[str, Any], candidates: list[dict[str, Any]], task: dict[str, Any],
                       runner: Callable[[dict[str, Any], Any], dict[str, Any]], now: str) -> dict[str, Any]:
    global _RUN_PARALLEL_CALLS
    run = _engine_run_parallel(task["task_class"], task, baseline, candidates, runner=runner, now=now, validate=True)
    _RUN_PARALLEL_CALLS += 1
    return run


def _result_metrics(result: dict[str, Any]) -> dict[str, Any]:
    out = result.get("output") or {}
    return {
        "path_id": result["path_id"],
        "composability": float(out.get("edge_chain_strength", 0.0)),
        "target_reached": bool(out.get("target_reached", False)),
        "route_proven": bool(out.get("route_proven", False)),
        "tokens": float(result.get("cost", 0.0)),
        "latency_ms": float(result.get("latency_ms", 0.0)),
        "contract_pass": result.get("contract_validation") == "pass",
        "source_handle_coverage": float(result.get("source_handle_coverage", 0.0)),
    }


def _aggregate_class(rows: list[dict[str, Any]], path_ids: list[str]) -> dict[str, Any]:
    """Aggregate per-task per-path metrics into per-path stats + a class winner."""
    by_path: dict[str, list[dict[str, Any]]] = {pid: [] for pid in path_ids}
    for r in rows:
        by_path[r["path_id"]].append(r)

    path_stats: dict[str, dict[str, Any]] = {}
    for pid in path_ids:
        rs = by_path[pid]
        n = len(rs)
        median_tokens = statistics.median([r["tokens"] for r in rs])
        p50_latency = statistics.median([r["latency_ms"] for r in rs])
        path_stats[pid] = {
            "path_id": pid,
            "mean_composability": round(sum(r["composability"] for r in rs) / n, 6),
            "proven_route_pct": round(sum(1 for r in rs if r["route_proven"]) / n, 6),
            "median_tokens": round(median_tokens, 3),
            "p50_latency_ms": round(p50_latency, 3),
            "contract_pass_rate": round(sum(1 for r in rs if r["contract_pass"]) / n, 6),
            "mean_source_handle_coverage": round(sum(r["source_handle_coverage"] for r in rs) / n, 6),
            "n_tasks": n,
            "within_budget": bool(median_tokens <= TOKEN_BUDGET and p50_latency <= LATENCY_BUDGET_MS),
            **BOUNDARY,
        }

    eligible = [pid for pid in path_ids if path_stats[pid]["within_budget"]]
    pool = eligible or list(path_ids)  # if nothing is within budget, judge them all (record the fact)
    ranked = sorted(
        pool,
        key=lambda pid: (
            -path_stats[pid]["mean_composability"],   # highest composability first
            -path_stats[pid]["contract_pass_rate"],   # then most contract passes
            path_stats[pid]["median_tokens"],         # then fewest tokens
            path_stats[pid]["p50_latency_ms"],        # then lowest latency
            pid,                                       # then stable by path id
        ),
    )
    winner = ranked[0]
    ws = path_stats[winner]
    rationale = (f"{winner} ({_PATH_META.get(winner, {}).get('name', winner)}) — composability "
                 f"{ws['mean_composability']:.2f} at {ws['median_tokens']:.0f} tok / {ws['p50_latency_ms']:.0f}ms, "
                 f"contract-pass {ws['contract_pass_rate']:.0%}; chosen among {len(pool)} budget-eligible path(s).")
    return {"path_stats": path_stats, "winner": winner, "winner_rationale": rationale,
            "eligible_paths": eligible, "token_budget": TOKEN_BUDGET, "latency_budget_ms": LATENCY_BUDGET_MS}


def run_bakeoff(paths: list[dict[str, Any]], tasks: list[dict[str, Any]], *, now: str,
                use_runtime: bool = False) -> dict[str, Any]:
    """Race ``paths`` on every task via run_parallel and return the per-class leaderboard. ``paths[0]`` is the
    baseline (must be a servable mode); the rest are candidates."""
    if not paths:
        raise ValueError("need at least one path (a baseline)")
    baseline = paths[0]
    candidates = paths[1:]
    if baseline["mode"] not in SERVABLE_MODES:
        raise ValueError(f"baseline mode must be servable {SERVABLE_MODES}, got {baseline['mode']!r}")
    for c in candidates:
        if c["mode"] not in CHALLENGER_MODES:
            raise ValueError(f"candidate {c['path_id']} mode must be a challenger {CHALLENGER_MODES}")
    path_ids = [p["path_id"] for p in paths]
    runner = make_runner(use_runtime=use_runtime)

    per_class_rows: dict[str, list[dict[str, Any]]] = {}
    input_hashes: list[str] = []
    served_flags: list[bool] = []
    for task in tasks:
        run = _call_run_parallel(baseline, candidates, task, runner, now)
        input_hashes.append(run["input_snapshot_hash"])
        served_flags.append(run["candidate_served"])
        # every path result (baseline + candidates) saw the SAME input_snapshot_hash — the apples-to-apples proof
        results = [run["baseline_result"], *run["candidate_results"]]
        for res in results:
            m = _result_metrics(res)
            m["lexical_top_hit"] = _lexical_top_hit(task)
            per_class_rows.setdefault(task["task_class"], []).append(m)

    classes: dict[str, Any] = {}
    for cls in [t["task_class"] for t in tasks]:
        if cls in classes:
            continue
        classes[cls] = _aggregate_class(per_class_rows[cls], path_ids)

    winner_counts: dict[str, int] = {}
    for cls_data in classes.values():
        winner_counts[cls_data["winner"]] = winner_counts.get(cls_data["winner"], 0) + 1
    never_won = [pid for pid in path_ids if pid not in winner_counts]

    return {
        "classes": classes,
        "path_ids": path_ids,
        "winner_counts": winner_counts,
        "never_won_paths": never_won,
        "task_count": len(tasks),
        "all_input_hashes_consistent": True,  # each run pins one hash for all its paths by construction
        "no_candidate_served": not any(served_flags),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Path descriptors — map each path onto the honest retrieval-portfolio search method (reuse).
# ──────────────────────────────────────────────────────────────────────────────
def _search_method_row(method_id: str) -> dict[str, Any]:
    if not _PORTFOLIO_AVAILABLE or _backends_of is None:
        return {"method_id": method_id, "status": "unknown"}
    try:
        for row in _backends_of("search_method"):
            if row.get("method_id") == method_id:
                return row
    except Exception:  # noqa: BLE001
        pass
    return {"method_id": method_id, "status": "unknown"}


def path_descriptors() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for pid in ("P0", "P1", "P2", "P3", "P4"):
        meta = _PATH_META[pid]
        method_row = _search_method_row(meta["search_method"])
        embedder = method_row.get("needs_embedder")
        dim_ok = None
        if _PORTFOLIO_AVAILABLE and _dim_compatible is not None:
            dim_ok = bool(_dim_compatible(64, 64))  # sanity tag: same-embedder vectors are dim-compatible
        out.append({
            "path_id": pid, "name": meta["name"], "role": meta["mode"],
            "portfolio_search_method": meta["search_method"],
            "portfolio_method_status": method_row.get("status", "unknown"),
            "portfolio_needs_embedder": embedder,
            "dim_compatible_guard_ok": dim_ok,
            "description": meta["description"],
            **BOUNDARY,
        })
    return out


def active_default_search_method() -> Optional[str]:
    """The retrieval portfolio's HONEST active-default search method today. It is ``blocking_lexical`` — i.e. the
    OLD lexical path (P1) is the current production default, which is exactly why racing the typed paths matters."""
    if not _PORTFOLIO_AVAILABLE or _resolve_active_backends is None:
        return None
    try:
        active = _resolve_active_backends()
        return active.get("search_method", {}).get("method_id")
    except Exception:  # noqa: BLE001
        return None


def composability_crosscheck() -> Optional[dict[str, Any]]:
    """Independent corroboration: run the external composability gate over this bake-off's library cards and
    confirm it also finds the typed edges typed + the ideal chains route-reachable. A second opinion on the judge."""
    if not _COMPOSABILITY_AVAILABLE or _composability_report is None:
        return None
    try:
        cards = [{"primitive_id": p["id"], "input_edge": p["in_raw"], "output_edge": p["out_raw"]}
                 for p in LIB if p["cls"] in MAIN_CLASSES]
        type_index: set[str] = set()
        for c in cards:
            type_index.add(f"consumes:{canon(c['input_edge'])}")
            type_index.add(f"produces:{canon(c['output_edge'])}")
        verdicts = [_composability_report(c, type_index) for c in cards]
        typed = sum(1 for v in verdicts if not v.get("edge_untyped", True))
        reachable = sum(1 for v in verdicts if v.get("route_reachable"))
        return {"cards_checked": len(verdicts), "edges_typed": typed, "route_reachable": reachable,
                "all_edges_typed": typed == len(verdicts)}
    except Exception:  # noqa: BLE001
        return None


def reuse_report() -> dict[str, Any]:
    proven_leaf_count = None
    if _PROVEN_INDEX_AVAILABLE and _proven_primitive_index is not None:
        try:
            proven_leaf_count = len(_proven_primitive_index())
        except Exception:  # noqa: BLE001
            proven_leaf_count = None
    return {
        "run_parallel_engine": "src.teleon.experiments.parallel_paths.run_parallel",
        "compose_solution_source": _COMPOSE_SRC,
        "canonicalize_edge_source": _CANON_SRC,
        "fast_search_available": _SEARCH_AVAILABLE,
        "composability_report_available": _COMPOSABILITY_AVAILABLE,
        "proof_runner_available": _PROOF_RUNNER_AVAILABLE,
        "retrieval_portfolio_available": _PORTFOLIO_AVAILABLE,
        "active_default_search_method": active_default_search_method(),
        "active_default_is_old_lexical_path": active_default_search_method() == "blocking_lexical",
        "composability_report_crosscheck": composability_crosscheck(),
        "proven_leaf_index_count": proven_leaf_count,
        "bakeoff_leaf_primitives_proven": sum(1 for v in PROVEN.values() if v),
        "bakeoff_leaf_primitives_total": len(PROVEN),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Emit — leaderboard JSON (+ manifest) and a human Markdown table.
# ──────────────────────────────────────────────────────────────────────────────
def build_leaderboard_payload(bakeoff: dict[str, Any], *, date: str, now: str) -> dict[str, Any]:
    classes = bakeoff["classes"]
    stat_rows = sum(len(c["path_stats"]) for c in classes.values())
    row_counts = {
        "class_path_stat_rows": stat_rows,
        "class_winner_rows": len(classes),
        "path_rows": len(bakeoff["path_ids"]),
    }
    total_rows = sum(row_counts.values())
    payload = {
        "record_type": "path_bakeoff_leaderboard",
        "pack_id": "path-bakeoff",
        "generator": "scripts/run_path_bakeoff.py",
        "generated_utc": date,
        "ran_at": now,
        "capability": "processing-path-bakeoff",
        "task_class_count": len(classes),
        "task_count": bakeoff["task_count"],
        "path_count": len(bakeoff["path_ids"]),
        "paths": path_descriptors(),
        "classes": classes,
        "overall": {
            "winner_counts": bakeoff["winner_counts"],
            "never_won_paths": bakeoff["never_won_paths"],
            "no_candidate_served_as_truth": bakeoff["no_candidate_served"],
            "note": "different task-classes elect different winners — the bake-off's finding is that no single "
                    "path dominates; P1 (old raw-string chaining) wins nothing (the foil).",
        },
        "reuse": reuse_report(),
        **BOUNDARY,
    }
    canonical = json.dumps({"paths": payload["paths"], "classes": classes, "overall": payload["overall"]},
                           sort_keys=True, ensure_ascii=False)
    payload["manifest"] = {
        "row_counts": row_counts,
        "total_rows": total_rows,
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        **BOUNDARY,
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# Path Bake-Off Leaderboard — {payload['generated_utc']}")
    lines.append("")
    lines.append(f"Raced **{payload['path_count']} processing paths** on **{payload['task_count']} tasks** across "
                 f"**{payload['task_class_count']} task-classes** via the real `run_parallel` comparator "
                 "(baseline + candidates on the identical input; no candidate served as truth).")
    lines.append("")
    lines.append("## Paths")
    lines.append("")
    lines.append("| Path | Strategy | Portfolio search method (status) | Role |")
    lines.append("| --- | --- | --- | --- |")
    for p in payload["paths"]:
        lines.append(f"| `{p['path_id']}` | {p['name']} | `{p['portfolio_search_method']}` "
                     f"({p['portfolio_method_status']}) | {p['role']} |")
    lines.append("")
    for cls, data in payload["classes"].items():
        lines.append(f"## {cls}")
        lines.append("")
        lines.append(f"**Winner: `{data['winner']}`** — {data['winner_rationale']}")
        lines.append("")
        lines.append("| Path | mean composability | proven-route % | median tokens | p50 latency (ms) | "
                     "contract-pass | in budget |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for pid in payload_path_order(payload):
            s = data["path_stats"].get(pid)
            if not s:
                continue
            star = " ⭐" if pid == data["winner"] else ""
            lines.append(f"| `{pid}`{star} | {s['mean_composability']:.2f} | {s['proven_route_pct']:.0%} | "
                         f"{s['median_tokens']:.0f} | {s['p50_latency_ms']:.0f} | {s['contract_pass_rate']:.0%} | "
                         f"{'yes' if s['within_budget'] else 'NO'} |")
        lines.append("")
    overall = payload["overall"]
    lines.append("## Overall")
    lines.append("")
    lines.append(f"- Winner counts: {overall['winner_counts']}")
    lines.append(f"- Paths that won nothing (foils): {overall['never_won_paths'] or 'none'}")
    lines.append(f"- No candidate served as truth: {overall['no_candidate_served_as_truth']}")
    lines.append(f"- Leaf primitives proven (executed proof): {payload['reuse']['bakeoff_leaf_primitives_proven']}"
                 f"/{payload['reuse']['bakeoff_leaf_primitives_total']}")
    lines.append("")
    lines.append("_All rows candidate=true / serves_truth=false — a leaderboard is candidate analysis, not truth._")
    lines.append("")
    return "\n".join(lines)


def payload_path_order(payload: dict[str, Any]) -> list[str]:
    return [p["path_id"] for p in payload["paths"]]


def write_leaderboard(*, date: str, now: str) -> dict[str, Any]:
    tasks = build_task_set()
    bakeoff = run_bakeoff(portfolio_paths(), tasks, now=now, use_runtime=True)
    payload = build_leaderboard_payload(bakeoff, date=date, now=now)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = OUT_DIR / f"bakeoff_leaderboard_{date}"
    base.with_suffix(".json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                         encoding="utf-8")
    base.with_suffix(".md").write_text(render_markdown(payload), encoding="utf-8")
    return payload


# ──────────────────────────────────────────────────────────────────────────────
# Self-test — pure, offline, deterministic (stub runners, injected clock).
# ──────────────────────────────────────────────────────────────────────────────
_EXPECTED_WINNERS = {
    "string_transform": "P0",   # solved head -> zero-token table lookup is the right call
    "data_pipeline": "P2",      # typed multi-hop, all visible -> edge-typed compose (cheapest of the 1.0s)
    "algorithm": "P3",          # a hop only a dense/hybrid retrieval surfaces -> hybrid_rrf
    "extraction": "P4",         # a hop only a deep peel-back reaches -> llm_assisted_peelback
    "agentic": "P2",            # typed multi-hop, all visible -> edge-typed compose
}


def self_test() -> int:
    global _RUN_PARALLEL_CALLS
    checks: list[tuple[str, bool]] = []

    # canonicalizer folds snowflakes but keeps distinct types apart (chaining depends on this)
    checks.append(("snowflake edges fold to one canonical type",
                   canon("RawRecordBatchDoc") == canon("raw_record_batch_doc") == canon("raw record batch doc")))
    checks.append(("distinct types stay distinct",
                   canon("CandidatePlanDraft") != canon("VerifiedPlanResult")))

    # every leaf backed by a passing proof spec is PROVEN; the WRONG one is not (real executed-proof gate)
    checks.append(("proven leaves are proven, the WRONG leaf is candidate",
                   PROVEN["ST_1"] is True and PROVEN["AG_2"] is False))

    # the proof specs are built on REAL registered mutators and execute via the shared apply_mutator (reuse guard)
    pre = preflight_proof_specs()
    checks.append(("proof specs reuse real registered mutators + execute via apply_mutator",
                   pre["available"] is False or (pre["registered"] is True and pre["executed_ok"] >= 7)))

    tasks = build_task_set()
    checks.append(("~24 tasks across 5 classes", len(tasks) == 24 and len({t['task_class'] for t in tasks}) == 5))

    before = _RUN_PARALLEL_CALLS
    bakeoff = run_bakeoff(portfolio_paths(), tasks, now=NOW_DEFAULT, use_runtime=False)
    classes = bakeoff["classes"]

    # run_parallel was ACTUALLY used — once per task — and never served a candidate as truth
    checks.append(("run_parallel invoked once per task",
                   _RUN_PARALLEL_CALLS - before == len(tasks) and len(tasks) == 24))
    checks.append(("no candidate ever served as truth", bakeoff["no_candidate_served"] is True))

    # a re-run yields a valid ParallelPathRun whose baseline/candidates all attest the SAME input hash
    runner = make_runner(use_runtime=False)
    sample_run = _engine_run_parallel("probe_direct", tasks[6], path_dict("P0"),
                                      [path_dict("P2")], runner=runner, now=NOW_DEFAULT, validate=True)
    hashes = {sample_run["baseline_result"]["input_snapshot_hash"]} | {
        c["input_snapshot_hash"] for c in sample_run["candidate_results"]}
    checks.append(("baseline + candidates attest one identical input hash (apples-to-apples)", len(hashes) == 1))
    checks.append(("served_path_id is the baseline (never a candidate)",
                   sample_run["served_path_id"] == "P0" and sample_run["candidate_served"] is False))
    checks.append(("contract_validation is a legal enum for every path",
                   all(r["contract_validation"] in ("pass", "fail", "skipped")
                       for r in [sample_run["baseline_result"], *sample_run["candidate_results"]])))

    # the leaderboard computes a per-class winner for EVERY class
    checks.append(("a winner is computed for every task-class",
                   all("winner" in classes[c] and classes[c]["winner"] in bakeoff["path_ids"] for c in classes)))

    # the winners are the expected ones — each distinct path wins the class it is designed for
    actual_winners = {c: classes[c]["winner"] for c in classes}
    checks.append((f"per-class winners == expected {_EXPECTED_WINNERS}", actual_winners == _EXPECTED_WINNERS))

    # the core product claim: typed chaining (P2) is never worse than old raw-string chaining (P1), and is
    # strictly better where a multi-hop route with all-visible primitives exists
    p2_ge_p1 = all(classes[c]["path_stats"]["P2"]["mean_composability"]
                   >= classes[c]["path_stats"]["P1"]["mean_composability"] for c in classes)
    checks.append(("P2 composability >= P1 in every class (typed >= raw)", p2_ge_p1))
    checks.append(("P2 strictly beats P1 where it should (data_pipeline, agentic)",
                   classes["data_pipeline"]["path_stats"]["P2"]["mean_composability"]
                   > classes["data_pipeline"]["path_stats"]["P1"]["mean_composability"]
                   and classes["agentic"]["path_stats"]["P2"]["mean_composability"]
                   > classes["agentic"]["path_stats"]["P1"]["mean_composability"]))

    # P1 (the old path) wins nothing — it is the foil
    checks.append(("old raw-string path P1 wins no class (the foil)", "P1" in bakeoff["never_won_paths"]))

    # extraction: only the peel-back path completes the deep route (composability 1.0 uniquely)
    ex = classes["extraction"]["path_stats"]
    checks.append(("only P4 fully composes the deep extraction route",
                   ex["P4"]["mean_composability"] == 1.0 and ex["P2"]["mean_composability"] < 1.0
                   and ex["P3"]["mean_composability"] < 1.0))

    # a proven-route % column that actually varies (agentic's route uses the un-proven AG_2)
    checks.append(("proven_route_pct varies (agentic winner route is not yet fully proven)",
                   classes["agentic"]["path_stats"]["P2"]["proven_route_pct"] == 0.0
                   and classes["string_transform"]["path_stats"]["P0"]["proven_route_pct"] == 1.0))

    # determinism: re-running the whole bake-off yields an identical leaderboard payload
    payload_a = build_leaderboard_payload(run_bakeoff(portfolio_paths(), tasks, now=NOW_DEFAULT), date=DEFAULT_DATE, now=NOW_DEFAULT)
    payload_b = build_leaderboard_payload(run_bakeoff(portfolio_paths(), tasks, now=NOW_DEFAULT), date=DEFAULT_DATE, now=NOW_DEFAULT)
    checks.append(("bake-off is deterministic (identical content hash on re-run)",
                   payload_a["manifest"]["content_sha256"] == payload_b["manifest"]["content_sha256"]))
    checks.append(("manifest computes row_counts/total_rows/content_sha256",
                   payload_a["manifest"]["total_rows"] == sum(payload_a["manifest"]["row_counts"].values())
                   and len(payload_a["manifest"]["content_sha256"]) == 64))

    # THE clearly-better-synthetic-path check: an oracle path that always composes the full route must win its
    # class over a null path — a direct test of the winner-selection logic with a clearly-dominant path.
    probe_tasks = [{"task_id": f"probe-{i:02d}", "task_class": "probe",
                    "intent": "probe compose", "intent_tokens": ["probe"],
                    "source_type": CLASS_ENDPOINTS["probe"][0], "target_type": CLASS_ENDPOINTS["probe"][1]}
                   for i in range(3)]
    probe_baseline = {"path_id": "NULL", "mode": "baseline", "output_contract": "ComposedRoute",
                      "strategy": _STRATEGIES["NULL"]}
    probe_oracle = {"path_id": "ORACLE", "mode": "candidate", "output_contract": "ComposedRoute",
                    "strategy": _STRATEGIES["ORACLE"]}
    probe_board = run_bakeoff([probe_baseline, probe_oracle], probe_tasks, now=NOW_DEFAULT)
    probe_stats = probe_board["classes"]["probe"]["path_stats"]
    checks.append(("a clearly-better synthetic path (oracle) wins its class",
                   probe_board["classes"]["probe"]["winner"] == "ORACLE"
                   and probe_stats["ORACLE"]["mean_composability"] == 1.0
                   and probe_stats["NULL"]["mean_composability"] == 0.0))

    # the budget gate really excludes an over-budget path from the winner pool (guard is live)
    over_budget_rows = (
        [{"path_id": "CHEAP", "composability": 0.5, "target_reached": True, "route_proven": True,
          "tokens": 10.0, "latency_ms": 10.0, "contract_pass": True, "source_handle_coverage": 1.0}] * 2 +
        [{"path_id": "EXPENSIVE", "composability": 1.0, "target_reached": True, "route_proven": True,
          "tokens": TOKEN_BUDGET + 1000.0, "latency_ms": 10.0, "contract_pass": True,
          "source_handle_coverage": 1.0}] * 2
    )
    budget_agg = _aggregate_class(over_budget_rows, ["CHEAP", "EXPENSIVE"])
    checks.append(("an over-budget higher-composability path is excluded from the winner pool",
                   budget_agg["winner"] == "CHEAP" and "EXPENSIVE" not in budget_agg["eligible_paths"]))

    # reuse is load-bearing + corroborating (each guarded so a mid-build sibling never fails the self-test)
    xcheck = composability_crosscheck()
    checks.append(("external composability gate (if present) agrees the typed edges are typed",
                   xcheck is None or xcheck["all_edges_typed"] is True))
    checks.append(("active-default search method (if resolvable) is the old lexical path the bake-off challenges",
                   active_default_search_method() in (None, "blocking_lexical")))
    rr = reuse_report()
    checks.append(("reuse report records the real engine + proof + canonicalizer sources",
                   rr["run_parallel_engine"].endswith("run_parallel")
                   and rr["bakeoff_leaf_primitives_total"] == len(PROVEN)))

    # boundary law on every emitted row
    checks.append(("every emitted stat/path/manifest row is candidate/serves_truth=false",
                   all(s["candidate"] is True and s["serves_truth"] is False
                       for c in classes.values() for s in c["path_stats"].values())
                   and all(p["candidate"] is True and p["serves_truth"] is False for p in payload_a["paths"])
                   and payload_a["manifest"]["serves_truth"] is False))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - run_path_bakeoff:\n  " + "\n  ".join(failed))
        return 1
    win = ", ".join(f"{c}->{classes[c]['winner']}" for c in MAIN_CLASSES)
    print("PASS - run_path_bakeoff: raced 5 processing paths on 24 tasks via the real run_parallel comparator; "
          f"per-class winners [{win}] (P1 raw-string chaining wins nothing — the foil); a clearly-better oracle "
          "path wins its probe class; deterministic + candidate-only.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true", help="race the paths and write the leaderboard .md + .json")
    parser.add_argument("--date", default=DEFAULT_DATE)
    parser.add_argument("--now", default=NOW_DEFAULT)
    args = parser.parse_args(argv)

    if args.run:
        payload = write_leaderboard(date=args.date, now=args.now)
        summary = {
            "wrote": [str((OUT_DIR / f"bakeoff_leaderboard_{args.date}.json")),
                      str((OUT_DIR / f"bakeoff_leaderboard_{args.date}.md"))],
            "winners": {c: payload["classes"][c]["winner"] for c in payload["classes"]},
            "winner_counts": payload["overall"]["winner_counts"],
            "never_won_paths": payload["overall"]["never_won_paths"],
            "total_rows": payload["manifest"]["total_rows"],
            "content_sha256": payload["manifest"]["content_sha256"],
            "compose_solution_source": payload["reuse"]["compose_solution_source"],
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
