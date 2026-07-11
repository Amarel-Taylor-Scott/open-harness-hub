#!/usr/bin/env python3
"""scripts.run_runtime_benchmark — the RUNNABLE benchmark that proves the wired runtime composes (closes F9).

The red-team's F9 finding: "coverage" in `run_primitive_consumption_benchmark` is self-graded by the SAME
token-overlap the retriever ranks on — so a card that is merely word-relevant scores as "composable" even though its
edges never chain. There was no real labeled precision/recall harness and no honest composability metric. This is it.

It is ADD-ONLY and a NEW parallel PATH (the flexible-multi-path way): it IMPORTS the already-built machinery and
benchmarks it against the OLD lexical judge — it edits none of the contract-locked seams.

  * NEW arm  — imports `scripts.primitive_runtime.compose_solution` (the wired runtime) and judges composability the
               HONEST way: `route_composable == (route_found AND edge_chain_strength > 0)`, where `edge_chain_strength`
               counts canonical-TYPE joins (output_type_id == next input_type_id), never token overlap.
  * OLD arm  — imports `scripts.run_primitive_consumption_benchmark.score_task` (the old token-overlap judge) and reads
               its `route_covered` as the OLD composability verdict — the exact self-graded metric F9 flagged.

Both arms score the SAME LABELED task set over the SAME retrieved candidate set, so the only variable is the
composability judgment: canonical types (NEW) vs token overlap (OLD). Because the task set carries GROUND-TRUTH labels
(`expected_composable`, authored with a real typed corpus + token-relevant distractors), we compute a real
precision / recall / F1 for each arm and report the DELTA — did wiring the runtime raise REAL composability above the
old token-overlap judge?

Every emitted row is candidate=true / serves_truth=false (a benchmark scorecard is a candidate measurement, never a
truth claim). The token-savings figure is an ESTIMATE (labelled). Offline + deterministic: `compose_solution` runs
over injected `candidate_cards`, so NO live 113k registry and NO network are needed — `--self-test` and `--run` both
execute fully offline. Latency is measured out-of-band and excluded from the deterministic content hash.
CLI: --self-test | --run [--date D] [--k K].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

OUT_DIR = _resource("data") / "dev-intel" / "primitive_consumption_benchmark"
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CHARS_PER_TOKEN = 4  # rough token estimate for measured compact-card text (matches the consumption benchmark)
# one-shot (write-it-from-scratch) output-token baseline by task complexity — what an agent burns with no reuse.
ONE_SHOT_BASELINE_TOKENS = {"low": 900, "medium": 2200, "high": 4500}

# ── the wired runtime under test (NEW arm) ──
from scripts.primitive_runtime import (  # noqa: E402
    compose_solution,
    edge_chain_strength as _edge_chain_strength,
    canonicalize_edge as _canon,
)
# ── the OLD token-overlap judge (baseline arm) — imported, never edited ──
from scripts import run_primitive_consumption_benchmark as _OLD  # noqa: E402

# ── optional provenance seams (honored, graceful if a sibling has not landed) ──
try:
    from scripts.build_retrieval_backend_portfolio import resolve_active_backends as _RESOLVE_BACKENDS, dim_compatible as _DIM_COMPAT
    _HAS_BACKENDS = True
except Exception:  # noqa: BLE001
    _RESOLVE_BACKENDS = None
    _DIM_COMPAT = None
    _HAS_BACKENDS = False
try:
    from scripts.build_canonical_edge_type_vocabulary import _all_types as _VOCAB_TYPES
    _HAS_VOCAB = True
except Exception:  # noqa: BLE001
    _VOCAB_TYPES = None
    _HAS_VOCAB = False


# ══════════════════════════════════════════════════════════════════════════════
# THE LABELED CORPUS — canonical-typed leaf primitives forming a connected type graph.
# Leaf ids that match the executed-proof proven index (scripts.prove_leaf_primitives) are PROVEN; a handful of
# realistic unproven leaves (parse_array_input / extract_fields / tokenize_text / count_tokens) let proven_route_pct
# be an honest fraction, not 100%.
# spec = (leaf_id, input_type, output_type, keywords)
# ══════════════════════════════════════════════════════════════════════════════
_LEAF_SPECS: list[tuple[str, str, str, list[str]]] = [
    # ── data-cleaning chain ──
    ("prim:leaf:json_to_row", "JsonObject", "ParsedRows", ["json", "parse", "object", "row"]),
    ("prim:leaf:schema_validate", "ParsedRows", "ValidatedRows", ["schema", "validate", "rows"]),
    ("prim:leaf:dedupe_by_key", "ValidatedRows", "DedupedRows", ["dedupe", "duplicate", "rows", "key"]),
    ("prim:leaf:field_project", "DedupedRows", "ProjectedRows", ["project", "select", "fields", "columns"]),
    ("prim:leaf:field_rename", "ProjectedRows", "RenamedRows", ["rename", "map", "fields"]),
    ("prim:leaf:strip_none", "RenamedRows", "CleanRows", ["strip", "null", "none", "clean"]),
    ("prim:leaf:row_to_json_roundtrip", "CleanRows", "JsonObject", ["row", "json", "serialize", "roundtrip"]),
    ("prim:leaf:extract_fields", "DecodedBytes", "ParsedRows", ["extract", "fields", "parse", "bytes"]),
    # ── text / nlp chain ──
    ("prim:leaf:normalize_whitespace", "RawText", "NormalizedText", ["normalize", "whitespace", "text", "trim"]),
    ("prim:leaf:casefold_text", "NormalizedText", "CasefoldedText", ["casefold", "lowercase", "text"]),
    ("prim:leaf:content_hash_sha256", "NormalizedText", "HashDigest", ["hash", "sha256", "fingerprint", "content"]),
    ("prim:leaf:tokenize_text", "CasefoldedText", "TokenList", ["tokenize", "tokens", "split", "words"]),
    ("prim:leaf:count_tokens", "TokenList", "TokenCounts", ["count", "frequency", "histogram", "tokens"]),
    # ── key-value chain ──
    ("prim:leaf:kv_parse", "KvString", "KvMap", ["kv", "key", "value", "parse", "config"]),
    ("prim:leaf:kv_roundtrip", "KvMap", "KvString", ["kv", "serialize", "roundtrip", "map"]),
    # ── array chain ──
    ("prim:leaf:parse_array_input", "RawArrayInput", "ParsedArray", ["parse", "array", "input", "raw"]),
    ("prim:leaf:list_unique", "ParsedArray", "UniqueArray", ["unique", "dedupe", "list", "array"]),
    ("prim:leaf:sort_list", "UniqueArray", "SortedArray", ["sort", "order", "array", "list"]),
    # ── encoding chain ──
    ("prim:leaf:base64_decode", "Base64Text", "DecodedBytes", ["base64", "decode", "bytes"]),
    ("prim:leaf:base64_roundtrip", "DecodedBytes", "Base64Text", ["base64", "encode", "roundtrip", "bytes"]),
    # ── typing / field ──
    ("prim:leaf:type_cast", "RawField", "TypedField", ["cast", "type", "coerce", "field"]),
    ("prim:leaf:default_fill", "RawField", "FilledField", ["default", "fill", "missing", "field"]),
    ("prim:leaf:bool_coerce", "RawField", "BoolField", ["bool", "boolean", "coerce", "field"]),
    # ── number chain ──
    ("prim:leaf:round_number", "RawNumber", "RoundedNumber", ["round", "decimal", "number"]),
    ("prim:leaf:clamp", "RoundedNumber", "ClampedNumber", ["clamp", "bound", "range", "number"]),
    ("prim:leaf:zero_pad", "ClampedNumber", "PaddedString", ["pad", "zero", "format", "string", "number"]),
    # ── agentic / envelope / receipt ──
    ("prim:leaf:idempotency_key", "ActionRequest", "IdempotencyKey", ["idempotency", "key", "action", "request"]),
    ("prim:leaf:envelope_unwrap", "Envelope", "UnwrappedPayload", ["envelope", "unwrap", "payload"]),
    ("prim:leaf:envelope_roundtrip", "UnwrappedPayload", "Envelope", ["envelope", "wrap", "payload", "roundtrip"]),
    ("prim:leaf:output_receipt_wrap", "JsonObject", "Receipt", ["receipt", "wrap", "output", "audit"]),
]

# token-relevant but type-ISOLATED distractors (nothing consumes their output) — the trap the OLD token judge
# falls into and the NEW type judge rejects.
_DISTRACTOR_SPECS: list[tuple[str, str, str, list[str]]] = [
    ("prim:distractor:weather", "Location", "Forecast", ["array", "weather", "forecast", "sort", "data"]),
    ("prim:distractor:email", "EmailAddress", "DeliveryStatus", ["validate", "send", "email", "receipt", "rows"]),
    ("prim:distractor:ml", "FeatureMatrix", "ModelScore", ["train", "model", "feature", "validate", "score"]),
]


def _card(leaf_id: str, in_t: str, out_t: str, keywords: list[str]) -> dict[str, Any]:
    blocking = sorted(set([in_t.lower(), out_t.lower()] + [k.lower() for k in keywords]))
    return {
        "primitive_id": leaf_id,
        "title": f"{keywords[0]} {in_t} into {out_t}",
        "input_edge": in_t,
        "output_edge": out_t,
        "blocking_keys": blocking,
        "blackbox": " ".join(keywords),  # plain string: both the new runtime and the OLD judge read it
        **BOUNDARY,
    }


CORPUS: list[dict[str, Any]] = (
    [_card(*s) for s in _LEAF_SPECS] + [_card(*s) for s in _DISTRACTOR_SPECS]
)


# ══════════════════════════════════════════════════════════════════════════════
# THE LABELED TASK SET (qrels) — 40 judgments across coding / data / algorithm / agentic domains.
# spec = dict(id, domain, complexity, words, start, goal, expected_composable, family)
# `family`: positive | negative | remix (a real gap a deterministic wrapper can bridge) | gap (needs a model step)
# ══════════════════════════════════════════════════════════════════════════════
_TASK_SPECS: list[dict[str, Any]] = [
    # ── positives: a genuine canonical-type route start -> goal exists in the corpus ──
    {"id": "csv_validate_dedupe", "domain": "data", "complexity": "high", "words": "validate dedupe customer rows", "start": "ParsedRows", "goal": "DedupedRows", "expected_composable": True, "family": "positive"},
    {"id": "clean_project_rename_strip", "domain": "data", "complexity": "medium", "words": "project rename strip null fields rows", "start": "DedupedRows", "goal": "CleanRows", "expected_composable": True, "family": "positive"},
    {"id": "json_ingest_to_clean", "domain": "data", "complexity": "high", "words": "parse json validate dedupe project rename strip rows", "start": "JsonObject", "goal": "CleanRows", "expected_composable": True, "family": "positive"},
    {"id": "clean_serialize_json", "domain": "data", "complexity": "medium", "words": "project rename strip serialize rows json", "start": "DedupedRows", "goal": "JsonObject", "expected_composable": True, "family": "positive"},
    {"id": "content_fingerprint", "domain": "data", "complexity": "low", "words": "normalize whitespace hash content fingerprint text", "start": "RawText", "goal": "HashDigest", "expected_composable": True, "family": "positive"},
    {"id": "json_to_rows", "domain": "data", "complexity": "low", "words": "parse json rows object", "start": "JsonObject", "goal": "ParsedRows", "expected_composable": True, "family": "positive"},
    {"id": "schema_validate_only", "domain": "data", "complexity": "low", "words": "schema validate rows", "start": "ParsedRows", "goal": "ValidatedRows", "expected_composable": True, "family": "positive"},
    {"id": "kv_parse", "domain": "config", "complexity": "low", "words": "parse key value config", "start": "KvString", "goal": "KvMap", "expected_composable": True, "family": "positive"},
    {"id": "kv_serialize", "domain": "config", "complexity": "low", "words": "serialize key value map roundtrip", "start": "KvMap", "goal": "KvString", "expected_composable": True, "family": "positive"},
    {"id": "unique_sort", "domain": "algorithm", "complexity": "medium", "words": "unique sort order array list", "start": "ParsedArray", "goal": "SortedArray", "expected_composable": True, "family": "positive"},
    {"id": "parse_unique_sort", "domain": "algorithm", "complexity": "medium", "words": "parse unique sort raw array input list", "start": "RawArrayInput", "goal": "SortedArray", "expected_composable": True, "family": "positive"},
    {"id": "dedupe_list", "domain": "algorithm", "complexity": "low", "words": "unique dedupe array list", "start": "ParsedArray", "goal": "UniqueArray", "expected_composable": True, "family": "positive"},
    {"id": "parse_array", "domain": "algorithm", "complexity": "low", "words": "parse raw array input", "start": "RawArrayInput", "goal": "ParsedArray", "expected_composable": True, "family": "positive"},
    {"id": "base64_decode", "domain": "encoding", "complexity": "low", "words": "base64 decode bytes", "start": "Base64Text", "goal": "DecodedBytes", "expected_composable": True, "family": "positive"},
    {"id": "base64_encode", "domain": "encoding", "complexity": "low", "words": "base64 encode roundtrip bytes", "start": "DecodedBytes", "goal": "Base64Text", "expected_composable": True, "family": "positive"},
    {"id": "normalize_casefold", "domain": "text", "complexity": "medium", "words": "normalize whitespace casefold lowercase text", "start": "RawText", "goal": "CasefoldedText", "expected_composable": True, "family": "positive"},
    {"id": "idempotency", "domain": "agentic", "complexity": "low", "words": "idempotency key action request dedupe", "start": "ActionRequest", "goal": "IdempotencyKey", "expected_composable": True, "family": "positive"},
    {"id": "envelope_unwrap", "domain": "agentic", "complexity": "low", "words": "envelope unwrap payload", "start": "Envelope", "goal": "UnwrappedPayload", "expected_composable": True, "family": "positive"},
    {"id": "envelope_wrap", "domain": "agentic", "complexity": "low", "words": "envelope wrap payload roundtrip", "start": "UnwrappedPayload", "goal": "Envelope", "expected_composable": True, "family": "positive"},
    {"id": "wrap_receipt", "domain": "agentic", "complexity": "medium", "words": "wrap output receipt audit json", "start": "JsonObject", "goal": "Receipt", "expected_composable": True, "family": "positive"},
    {"id": "type_cast", "domain": "coding", "complexity": "low", "words": "cast type coerce field", "start": "RawField", "goal": "TypedField", "expected_composable": True, "family": "positive"},
    {"id": "default_fill", "domain": "coding", "complexity": "low", "words": "default fill missing field", "start": "RawField", "goal": "FilledField", "expected_composable": True, "family": "positive"},
    {"id": "bool_coerce", "domain": "coding", "complexity": "low", "words": "boolean coerce bool field", "start": "RawField", "goal": "BoolField", "expected_composable": True, "family": "positive"},
    {"id": "round_clamp_pad", "domain": "number", "complexity": "medium", "words": "round clamp bound pad zero format number", "start": "RawNumber", "goal": "PaddedString", "expected_composable": True, "family": "positive"},
    {"id": "round_number", "domain": "number", "complexity": "low", "words": "round decimal number", "start": "RawNumber", "goal": "RoundedNumber", "expected_composable": True, "family": "positive"},
    {"id": "text_tokenize", "domain": "nlp", "complexity": "medium", "words": "normalize casefold tokenize split words text", "start": "RawText", "goal": "TokenList", "expected_composable": True, "family": "positive"},
    {"id": "rows_full_pipeline", "domain": "data", "complexity": "high", "words": "validate dedupe project rename strip serialize rows json", "start": "ParsedRows", "goal": "JsonObject", "expected_composable": True, "family": "positive"},
    {"id": "decode_to_clean_rows", "domain": "pipeline", "complexity": "high", "words": "base64 decode extract validate dedupe project rename strip rows", "start": "Base64Text", "goal": "CleanRows", "expected_composable": True, "family": "positive"},
    {"id": "pad_number", "domain": "number", "complexity": "low", "words": "pad zero format clamped number string", "start": "ClampedNumber", "goal": "PaddedString", "expected_composable": True, "family": "positive"},
    {"id": "project_fields", "domain": "data", "complexity": "low", "words": "project select fields rows", "start": "DedupedRows", "goal": "ProjectedRows", "expected_composable": True, "family": "positive"},
    # ── negatives: token-relevant distractors retrieve, but NO canonical-type path exists ──
    {"id": "neg_weather_sort", "domain": "data", "complexity": "medium", "words": "sort array data forecast weather", "start": "Location", "goal": "SortedArray", "expected_composable": False, "family": "negative"},
    {"id": "neg_email_receipt", "domain": "auth", "complexity": "medium", "words": "validate send email receipt rows", "start": "EmailAddress", "goal": "ImportReceipt", "expected_composable": False, "family": "remix"},
    {"id": "neg_ml_deploy", "domain": "ml", "complexity": "high", "words": "train model feature validate score deploy", "start": "FeatureMatrix", "goal": "DeployedModel", "expected_composable": False, "family": "negative"},
    {"id": "neg_missing_middle", "domain": "data", "complexity": "medium", "words": "normalize text validate dedupe rows", "start": "RawText", "goal": "DedupedRows", "expected_composable": False, "family": "negative"},
    {"id": "neg_wrong_direction", "domain": "algorithm", "complexity": "low", "words": "sort array parse raw reverse", "start": "SortedArray", "goal": "RawArrayInput", "expected_composable": False, "family": "negative"},
    {"id": "neg_unknown_goal", "domain": "ai", "complexity": "high", "words": "parse json quantum entangle state", "start": "JsonObject", "goal": "QuantumState", "expected_composable": False, "family": "gap"},
    {"id": "neg_untyped_goal", "domain": "data", "complexity": "low", "words": "validate dedupe rows result", "start": "ParsedRows", "goal": "<result>", "expected_composable": False, "family": "negative"},
    {"id": "neg_receipt_remix", "domain": "agentic", "complexity": "medium", "words": "sort array wrap receipt audit", "start": "SortedArray", "goal": "AuditReceipt", "expected_composable": False, "family": "remix"},
    {"id": "neg_absent_capability", "domain": "misc", "complexity": "low", "words": "xyzzy plugh frobnicate widget", "start": "FooBarBaz", "goal": "QuuxCorge", "expected_composable": False, "family": "negative"},
    {"id": "neg_forecast_unique", "domain": "algorithm", "complexity": "medium", "words": "forecast weather unique dedupe array", "start": "Forecast", "goal": "UniqueArray", "expected_composable": False, "family": "negative"},
]


def _task_query(spec: dict[str, Any]) -> str:
    """Build the natural-language query the retriever sees; the `from X to Y` tail is what the runtime decomposes."""
    return f"{spec['words']} from {spec['start']} to {spec['goal']}"


def _old_task(spec: dict[str, Any]) -> dict[str, str]:
    return {"id": spec["id"], "domain": spec["domain"], "complexity": spec["complexity"], "query": _task_query(spec)}


# ══════════════════════════════════════════════════════════════════════════════
# Token-savings estimate (labelled) — measured compact-card cost vs a one-shot baseline.
# ══════════════════════════════════════════════════════════════════════════════
def _card_context_tokens(card: dict[str, Any]) -> int:
    bb = card.get("blackbox")
    bb_text = bb.get("does", "") if isinstance(bb, dict) else str(bb or "")
    compact = " ".join([str(card.get(k, "")) for k in ("title", "input_edge", "output_edge")] + [bb_text])
    return max(1, len(compact) // CHARS_PER_TOKEN)


_CORPUS_BY_ID = {c["primitive_id"]: c for c in CORPUS}


def _estimated_savings_pct(route_leaf_ids: list[str], complexity: str) -> float:
    """ESTIMATE: primitive-first context tokens (the compact leaf cards the agent reads) vs a one-shot from-scratch
    baseline. Clamped [0, 98]. Labelled evidence_class='estimated' by the caller — never a measured end-to-end run."""
    if not route_leaf_ids:
        return 0.0
    pf = sum(_card_context_tokens(_CORPUS_BY_ID[l]) for l in route_leaf_ids if l in _CORPUS_BY_ID)
    baseline = ONE_SHOT_BASELINE_TOKENS.get(complexity, 2000)
    if pf <= 0 or baseline <= 0:
        return 0.0
    return round(max(0.0, min(98.0, 100 * (1 - pf / baseline))), 1)


# ══════════════════════════════════════════════════════════════════════════════
# Per-task scoring — run BOTH arms over the SAME retrieved candidate set.
# ══════════════════════════════════════════════════════════════════════════════
def score_task(spec: dict[str, Any], candidate_cards: list[dict[str, Any]]) -> dict[str, Any]:
    query = _task_query(spec)
    gt = bool(spec["expected_composable"])

    # ── NEW arm: the wired runtime, judged on canonical TYPES ──
    t0 = time.perf_counter()
    sol = compose_solution(query, candidate_cards=candidate_cards, limit=len(candidate_cards))
    latency_ms = round((time.perf_counter() - t0) * 1000, 3)

    route = sol["route"]
    decomp = sol["decomposition"]
    route_leaf_ids = [str(c.get("component_id") or "") for c in route["ordered_route"] if c.get("component_id")]
    ecs = int(route["edge_chain_strength"])
    new_composable = bool(route["route_found"]) and ecs > 0
    # independent recomputation of edge_chain_strength (proves the metric is canonical-TYPE joins, not token overlap)
    ecs_independent = _edge_chain_strength(
        decomp["requested_input_type"], route["ordered_route"], decomp["requested_output_type"])
    endpoints_correct = bool(
        route["ordered_route"]
        and route["ordered_route"][0].get("input_edge") == _canon(spec["start"])
        and route["ordered_route"][-1].get("output_edge") == _canon(spec["goal"]))
    new_route_correct = new_composable and endpoints_correct and gt
    prove = sol["prove"]
    remix = sol["remix"]
    remix_bridged = remix.get("path") == "bridged_with_deterministic_mutator"

    # ── OLD arm: the token-overlap judge (imported, unedited) over the SAME candidates ──
    old = _OLD.score_task(_old_task(spec), candidate_cards)
    old_composable = bool(old["route_covered"])

    return {
        "record_type": "runtime_benchmark_scorecard",
        "task_id": spec["id"], "domain": spec["domain"], "complexity": spec["complexity"],
        "family": spec["family"],
        "expected_composable": gt,
        "requested_input_type": decomp["requested_input_type"],
        "requested_output_type": decomp["requested_output_type"],
        # NEW arm (canonical-type composability)
        "new_route_found": bool(route["route_found"]),
        "new_route_composable": new_composable,
        "new_edge_chain_strength": ecs,
        "new_edge_chain_strength_independent": int(ecs_independent),
        "new_route_length": len(route_leaf_ids),
        "new_route_leaf_ids": route_leaf_ids,
        "new_endpoints_correct": endpoints_correct,
        "new_route_correct": new_route_correct,
        "new_route_proven": bool(prove["route_proven"]),
        "new_proven_leaf_count": len(prove["proven_leaves"]),
        "new_remix_bridged": remix_bridged,
        "new_estimated_savings_pct": _estimated_savings_pct(route_leaf_ids, spec["complexity"]) if new_composable else 0.0,
        "new_savings_evidence_class": "estimated",
        "new_latency_ms": latency_ms,  # measured out-of-band; EXCLUDED from content_sha256
        # OLD arm (token-overlap composability — the F9 self-graded metric)
        "old_route_covered": old_composable,
        "old_stringable_distinct_edges": old["stringable_distinct_edges"],
        "old_estimated_savings_pct": old["estimated_token_savings_pct"],
        # per-arm confusion vs ground truth
        "new_confusion": _confusion(gt, new_composable),
        "old_confusion": _confusion(gt, old_composable),
        **BOUNDARY,
    }


def _confusion(gt: bool, pred: bool) -> str:
    if gt and pred:
        return "tp"
    if gt and not pred:
        return "fn"
    if (not gt) and pred:
        return "fp"
    return "tn"


def _prf(scores: list[dict[str, Any]], key: str) -> dict[str, float]:
    tp = sum(1 for s in scores if s[key] == "tp")
    fp = sum(1 for s in scores if s[key] == "fp")
    fn = sum(1 for s in scores if s[key] == "fn")
    tn = sum(1 for s in scores if s[key] == "tn")
    precision = round(tp / (tp + fp), 4) if (tp + fp) else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) else 0.0
    f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall, "f1": f1}


# ══════════════════════════════════════════════════════════════════════════════
# Aggregate — the scorecard, incl. the OLD-vs-NEW composability DELTA.
# ══════════════════════════════════════════════════════════════════════════════
def aggregate(scores: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(scores)
    composed = [s for s in scores if s["new_route_composable"]]
    new_prf = _prf(scores, "new_confusion")
    old_prf = _prf(scores, "old_confusion")
    savings = [s["new_estimated_savings_pct"] for s in composed if s["new_estimated_savings_pct"] > 0]
    latencies = [s["new_latency_ms"] for s in scores]
    strengths = [s["new_edge_chain_strength"] for s in composed]
    return {
        "record_type": "runtime_benchmark_aggregate",
        "tasks": n,
        "positives": sum(1 for s in scores if s["expected_composable"]),
        "negatives": sum(1 for s in scores if not s["expected_composable"]),
        "domains": sorted({s["domain"] for s in scores}),
        # NEW arm — the HONEST canonical-type composability metric
        "new_composable_pct": round(100 * len(composed) / n, 1) if n else 0.0,
        "new_route_correct_pct": round(100 * sum(1 for s in scores if s["new_route_correct"]) / n, 1) if n else 0.0,
        "new_composability_precision": new_prf["precision"],
        "new_composability_recall": new_prf["recall"],
        "new_composability_f1": new_prf["f1"],
        "new_confusion": {k: new_prf[k] for k in ("tp", "fp", "fn", "tn")},
        "median_edge_chain_strength": round(statistics.median(strengths), 2) if strengths else 0.0,
        "proven_route_pct": round(100 * sum(1 for s in composed if s["new_route_proven"]) / len(composed), 1) if composed else 0.0,
        "proven_routes": sum(1 for s in composed if s["new_route_proven"]),
        "remix_bridged_count": sum(1 for s in scores if s["new_remix_bridged"]),
        "median_estimated_savings_pct": round(statistics.median(savings), 1) if savings else 0.0,
        "savings_evidence_class": "estimated",
        "p50_latency_ms": round(statistics.median(latencies), 3) if latencies else 0.0,
        "p95_latency_ms": round(sorted(latencies)[max(0, int(0.95 * (len(latencies) - 1)))], 3) if latencies else 0.0,
        # OLD arm — the token-overlap self-graded metric (F9)
        "old_composable_pct": round(100 * sum(1 for s in scores if s["old_route_covered"]) / n, 1) if n else 0.0,
        "old_composability_precision": old_prf["precision"],
        "old_composability_recall": old_prf["recall"],
        "old_composability_f1": old_prf["f1"],
        "old_confusion": {k: old_prf[k] for k in ("tp", "fp", "fn", "tn")},
        # THE DELTA — did wiring the runtime raise REAL composability above the old token-overlap judge?
        "delta_composability_precision": round(new_prf["precision"] - old_prf["precision"], 4),
        "delta_composability_recall": round(new_prf["recall"] - old_prf["recall"], 4),
        "delta_composability_f1": round(new_prf["f1"] - old_prf["f1"], 4),
        "headline": (
            "NEW judges composability on canonical TYPES (edge_chain_strength>0); OLD judges on token overlap. "
            "Against ground-truth labels the NEW arm's composability F1 is "
            f"{new_prf['f1']} vs OLD {old_prf['f1']} (delta {round(new_prf['f1'] - old_prf['f1'], 4):+}); "
            f"NEW precision {new_prf['precision']} vs OLD {old_prf['precision']} — the OLD token judge's false "
            f"positives ({old_prf['fp']}) are token-relevant-but-non-composable cards the NEW type judge rejects."),
        "savings_disclaimer": "Token savings are ESTIMATES (measured compact-card size vs a one-shot complexity "
                              "baseline), NOT a runtime-measured paired end-to-end run.",
        "retrieval_backend_provenance": _backend_provenance(),
        **BOUNDARY,
    }


def _backend_provenance() -> dict[str, Any]:
    if not (_HAS_BACKENDS and _RESOLVE_BACKENDS is not None):
        return {"available": False, "note": "retrieval-backend-portfolio not importable in this environment"}
    try:
        active = _RESOLVE_BACKENDS()
        emb = active.get("embedder") or {}
        idx = active.get("index") or {}
        return {"available": True,
                "active_embedder": emb.get("id") if isinstance(emb, dict) else emb,
                "active_embedder_dim": emb.get("dim") if isinstance(emb, dict) else None,
                "active_index": idx.get("id") if isinstance(idx, dict) else idx}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "note": f"resolve_active_backends failed: {exc}"}


# ══════════════════════════════════════════════════════════════════════════════
# Report rendering + content hash (latency excluded from the deterministic body).
# ══════════════════════════════════════════════════════════════════════════════
_HASH_EXCLUDE = ("new_latency_ms",)


def _hashable(scores: list[dict[str, Any]]) -> str:
    stripped = [{k: v for k, v in s.items() if k not in _HASH_EXCLUDE} for s in scores]
    return "\n".join(json.dumps(s, sort_keys=True, ensure_ascii=False) for s in stripped)


def content_sha256(scores: list[dict[str, Any]]) -> str:
    return hashlib.sha256(_hashable(scores).encode("utf-8")).hexdigest()


def render_report(agg: dict[str, Any], scores: list[dict[str, Any]], *, date: str) -> str:
    L = [f"# Runtime Composability Benchmark — {date}", "",
         "> The runnable labeled benchmark that proves the WIRED runtime composes (closes red-team gap F9). Two arms",
         "> score the SAME 40-task labeled set over the SAME candidates; the only variable is the composability",
         "> judgment: **NEW** = canonical-TYPE edge chain (`edge_chain_strength>0`), **OLD** = token overlap",
         "> (`run_primitive_consumption_benchmark.score_task.route_covered`). Ground-truth labels give a real",
         "> precision/recall. All rows candidate=true / serves_truth=false; savings are ESTIMATES.", "",
         "## Headline", "", f"> {agg['headline']}", "",
         "## Aggregate", "",
         f"- Tasks: **{agg['tasks']}** ({agg['positives']} composable, {agg['negatives']} non-composable) across "
         f"**{len(agg['domains'])}** domains: {', '.join(agg['domains'])}",
         "",
         "| metric | NEW (canonical types) | OLD (token overlap) | delta |",
         "| --- | --- | --- | --- |",
         f"| composability precision | **{agg['new_composability_precision']}** | {agg['old_composability_precision']} | {agg['delta_composability_precision']:+} |",
         f"| composability recall | **{agg['new_composability_recall']}** | {agg['old_composability_recall']} | {agg['delta_composability_recall']:+} |",
         f"| composability F1 | **{agg['new_composability_f1']}** | {agg['old_composability_f1']} | {agg['delta_composability_f1']:+} |",
         f"| predicted composable % | {agg['new_composable_pct']}% | {agg['old_composable_pct']}% | — |",
         f"| false positives | {agg['new_confusion']['fp']} | {agg['old_confusion']['fp']} | — |",
         "",
         f"- NEW route-correct (composable AND endpoints match AND truly composable): **{agg['new_route_correct_pct']}%**",
         f"- Median edge_chain_strength (composed routes): **{agg['median_edge_chain_strength']}**",
         f"- Proven-route %: **{agg['proven_route_pct']}%** ({agg['proven_routes']} routes all-leaves executed-proof)",
         f"- Remix-bridged (deterministic wrapper closed the gap): **{agg['remix_bridged_count']}**",
         f"- Median estimated token savings (composed routes): **{agg['median_estimated_savings_pct']}%** "
         f"({agg['savings_evidence_class']})",
         f"- Latency p50 / p95: **{agg['p50_latency_ms']} / {agg['p95_latency_ms']} ms**",
         f"- Retrieval backend: {json.dumps(agg['retrieval_backend_provenance'])}",
         f"- Disclaimer: {agg['savings_disclaimer']}", "",
         "## Per task", "",
         "| task | domain | expect | NEW comp | ecs | len | proven | savings% | NEW conf | OLD comp | OLD conf |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in scores:
        L.append(
            f"| {s['task_id']} | {s['domain']} | {'Y' if s['expected_composable'] else 'N'} | "
            f"{'Y' if s['new_route_composable'] else '-'} | {s['new_edge_chain_strength']} | {s['new_route_length']} | "
            f"{'Y' if s['new_route_proven'] else '-'} | {s['new_estimated_savings_pct']} | {s['new_confusion']} | "
            f"{'Y' if s['old_route_covered'] else '-'} | {s['old_confusion']} |")
    return "\n".join(L) + "\n"


# ══════════════════════════════════════════════════════════════════════════════
# Runners.
# ══════════════════════════════════════════════════════════════════════════════
def run_full(date: str) -> dict[str, Any]:
    scores = [score_task(spec, CORPUS) for spec in _TASK_SPECS]
    agg = aggregate(scores)
    agg["content_sha256"] = content_sha256(scores)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"runtime_benchmark_{date}.jsonl").write_text(
        "".join(json.dumps(s, ensure_ascii=False, sort_keys=True) + "\n" for s in scores), encoding="utf-8")
    (OUT_DIR / f"runtime_benchmark_{date}.json").write_text(
        json.dumps(agg, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT_DIR / f"runtime_benchmark_{date}.md").write_text(
        render_report(agg, scores, date=date), encoding="utf-8")
    return agg


# ══════════════════════════════════════════════════════════════════════════════
# Self-test — offline, synthetic runtime path (no live 113k, no network).
# ══════════════════════════════════════════════════════════════════════════════
def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # a small synthetic slice: one clearly-composable positive + one token-relevant-but-non-composable negative.
    pos = next(s for s in _TASK_SPECS if s["id"] == "unique_sort")
    neg = next(s for s in _TASK_SPECS if s["id"] == "neg_weather_sort")
    sp = score_task(pos, CORPUS)
    sn = score_task(neg, CORPUS)

    checks.append(("scorecard computes with the required NEW+OLD fields",
                   all(k in sp for k in ("new_route_composable", "new_edge_chain_strength",
                                         "old_route_covered", "new_confusion", "old_confusion"))))
    # THE central assertion: the composability metric uses canonical TYPES, not token overlap.
    checks.append(("edge_chain_strength recomputes independently from canonical types (not token overlap)",
                   sp["new_edge_chain_strength"] == sp["new_edge_chain_strength_independent"]
                   and sp["new_edge_chain_strength"] > 0))
    checks.append(("a genuinely composable task is NEW-composable with a real type chain",
                   sp["new_route_composable"] is True and sp["new_route_length"] >= 2
                   and sp["new_endpoints_correct"] is True))
    # the token-overlap trap: OLD judges the weather distractor task 'covered', NEW rejects it on TYPES.
    checks.append(("token-relevant-but-non-composable negative: NEW=False (types) but OLD=True (tokens)",
                   sn["new_route_composable"] is False and sn["old_route_covered"] is True))
    checks.append(("that negative is a NEW true-negative and an OLD false-positive",
                   sn["new_confusion"] == "tn" and sn["old_confusion"] == "fp"))

    # full labeled run (offline over injected cards) — the scorecard + delta must compute and favor NEW on F1.
    scores = [score_task(spec, CORPUS) for spec in _TASK_SPECS]
    agg = aggregate(scores)
    checks.append(("full labeled set is 40 tasks over >=6 domains incl coding/data/algorithm/agentic",
                   agg["tasks"] == 40 and len(agg["domains"]) >= 6
                   and {"data", "algorithm", "agentic", "coding"}.issubset(set(agg["domains"]))))
    checks.append(("NEW composability precision > OLD (the type judge rejects token false-positives)",
                   agg["new_composability_precision"] > agg["old_composability_precision"]))
    checks.append(("NEW composability F1 > OLD F1 (real composability rose)",
                   agg["new_composability_f1"] > agg["old_composability_f1"]
                   and agg["delta_composability_f1"] > 0))
    checks.append(("OLD arm has more false positives than NEW (F9: token overlap over-claims composability)",
                   agg["old_confusion"]["fp"] > agg["new_confusion"]["fp"]))
    checks.append(("median edge_chain_strength over composed routes is >= 1 (real type joins)",
                   agg["median_edge_chain_strength"] >= 1))
    checks.append(("some composed routes are executed-proof proven (proven_route_pct > 0)",
                   agg["proven_route_pct"] > 0.0))
    checks.append(("median estimated savings is positive and labelled estimated",
                   agg["median_estimated_savings_pct"] > 0.0 and agg["savings_evidence_class"] == "estimated"))
    checks.append(("p50 latency computed (>= 0)", agg["p50_latency_ms"] >= 0.0))

    # boundary: every emitted scorecard row is candidate=true / serves_truth=false
    checks.append(("boundary held on every scorecard row",
                   all(s.get("candidate") is True and s.get("serves_truth") is False for s in scores)))

    # determinism: identical inputs -> identical hashable body (latency excluded)
    scores_b = [score_task(spec, CORPUS) for spec in _TASK_SPECS]
    checks.append(("deterministic: two runs -> identical content_sha256 (latency excluded from the body)",
                   content_sha256(scores) == content_sha256(scores_b)))

    # provenance seams honored
    if _HAS_BACKENDS and _DIM_COMPAT is not None:
        checks.append(("dim-compatibility rule imported and honest (equal dims compatible, mismatch not)",
                       _DIM_COMPAT(384, 384) is True and _DIM_COMPAT(64, 384) is False))
    else:
        checks.append(("backend provenance degrades gracefully when portfolio absent",
                       agg["retrieval_backend_provenance"]["available"] is False))
    if _HAS_VOCAB and _VOCAB_TYPES is not None:
        checks.append(("canonical edge-type vocabulary importable (provenance)", isinstance(_VOCAB_TYPES(), dict)))
    else:
        checks.append(("canonical vocabulary optional — absence is non-fatal", True))

    # report renders
    checks.append(("markdown report renders with the delta table",
                   "Runtime Composability Benchmark" in render_report(agg, scores, date="1970-01-01")))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - run_runtime_benchmark:\n  " + "\n  ".join(failed))
        return 1
    print(
        "PASS - run_runtime_benchmark: 40-task LABELED composability harness over the wired runtime "
        "(compose_solution). Composability judged on canonical TYPES (edge_chain_strength recomputes independently), "
        f"NOT token overlap. NEW composability F1={agg['new_composability_f1']} vs OLD (token-overlap) "
        f"F1={agg['old_composability_f1']} (delta {agg['delta_composability_f1']:+}); NEW precision "
        f"{agg['new_composability_precision']} vs OLD {agg['old_composability_precision']} — OLD false-positives="
        f"{agg['old_confusion']['fp']} (token-relevant-but-non-composable), NEW={agg['new_confusion']['fp']}. "
        f"Median edge_chain_strength={agg['median_edge_chain_strength']}, proven_route_pct={agg['proven_route_pct']}%, "
        f"median est. savings={agg['median_estimated_savings_pct']}% (estimated), p50 latency="
        f"{agg['p50_latency_ms']}ms. Offline + deterministic; boundary held.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true",
                        help="execute the full labeled set through compose_solution and write the reports")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    if args.run:
        date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
        agg = run_full(date)
        print(json.dumps({k: v for k, v in agg.items() if k != "retrieval_backend_provenance"},
                         indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
