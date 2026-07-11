#!/usr/bin/env python3
"""scripts.run_parametric_coverage_benchmark — a parametric-COVERAGE + composite-EXECUTION benchmark.

Two honest questions about the proven parametric-primitive substrate
(`data/dev-intel/parametric_primitives/param_*.jsonl`, each row a `serves_truth`-bearing configured primitive
minted by `scripts/generate_parametric_*.py` and proven by executing its mutator on a fixture):

  (a) COVERAGE — over a task-space of ~40 common data-op intents (project these fields, cast this type, validate
      this rule, bucket this metric, join on this key, …), what fraction can we satisfy by GRABBING an existing
      PROVEN parametric binding (serves_truth=true) instead of writing+testing new code? An intent is COVERED
      only when a proven row exists whose (family, mutator) matches AND whose observed binding-keys cover the
      intent's required knobs. Everything else is honestly reported as `needs_generation`.

  (b) EXECUTION — for a sample of covered intents we do NOT trust the template: we CHAIN the matched mutators via
      `scripts.mutator_registry.apply_mutator` on a controlled fixture and assert the composite output equals an
      INDEPENDENTLY hand-authored expected value (ground truth computed by hand, not by the registry), plus a
      determinism re-run. That is a real end-to-end proof of the composite route.

Repo laws honored here:
  * serves_truth=true is set ONLY by a PASSING executed proof of THAT route — the mutators are actually run on the
    fixture and the output is checked against an independent expected; a route that raises or mismatches is NOT
    persisted as truth (its serves_truth stays false). Never inferred from a template.
  * Honest accounting — generated vs unique(deduped) vs proven vs typed counts are reported separately; generated
    lines are never reported as active. Coverage and exec-pass are COMPUTED from the corpus, never asserted.
  * ADD-ONLY: this file imports the contract-locked machinery (`scripts.mutator_registry.apply_mutator`) and the
    proven param corpus; it edits nothing. The param mutators live in `scripts/prove_leaves_*.py` and register
    themselves INTO the shared registry on import (idempotent setdefault) — we import them to populate dispatch.
  * Deterministic + offline: no network, no LLM, no wall-clock (fixed literal timestamp), no RNG. The intent
    task-space and routes are enumerated explicitly; tokens_saved is a clearly-LABELED estimate.

CLI:
  --run        compute the benchmark over the REAL corpus, write
               data/dev-intel/parametric_primitives/coverage_benchmark_2026-07-03.{md,json}
  --self-test  offline synthetic check: coverage computes, an execution proof runs, a broken route FAILS.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import glob
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.mutator_registry import apply_mutator  # noqa: E402  (contract-locked; imported, never edited)

# ── fixed literal timestamp (law: no wall-clock) ──
BENCHMARK_DATE = "2026-07-03"
BENCHMARK_TS = "2026-07-03T00:00:00Z"
PARAM_DIR = _resource("data") / "dev-intel" / "parametric_primitives"

#: LABELED estimate — average tokens an agent would spend to write + unit-test one equivalent leaf transform from
#: scratch (implementation + a fixture test + a determinism check). Grabbing a proven parametric binding avoids that.
#: This is an ESTIMATE for sizing only, never a measured/serves_truth number.
EST_TOKENS_PER_REUSE = 850


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# registry population — the param mutators self-register on import of their prover modules (setdefault, idempotent)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def load_param_mutators() -> int:
    """Import every scripts/prove_leaves_*.py so their pure mutators register into the shared MUTATOR_REGISTRY.

    Returns the registry size after loading. Import failures are skipped (a missing prover just means those
    mutators stay unavailable and any route needing them will honestly fail its match/execution — never guessed)."""
    for path in sorted(glob.glob(str(_resource("scripts") / "prove_leaves_*.py"))):
        mod = "scripts." + os.path.basename(path)[:-3]
        try:
            importlib.import_module(mod)
        except Exception:  # noqa: BLE001 — a broken prover must not sink the benchmark; its mutators just stay absent
            continue
    from scripts.mutator_registry import MUTATOR_REGISTRY

    return len(MUTATOR_REGISTRY)


def mutator_available(name: str) -> bool:
    from scripts.mutator_registry import MUTATOR_REGISTRY

    return name in MUTATOR_REGISTRY


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# corpus loading + HONEST accounting (generated vs unique vs proven vs typed)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def load_proven_index(param_dir: Path = PARAM_DIR) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, int]]:
    """Read every param_*.jsonl. Build a proven index keyed by (family, mutator) → {count, binding_keys(set)} over
    ONLY serves_truth=true rows, and return honest split counts alongside.

    Honest accounting split (never conflated):
      generated_lines  — every JSONL line read
      unique_rows      — deduped by primitive_id (falls back to content hash / whole-line)
      proven_rows      — serves_truth is true
      typed_rows       — carries BOTH input_edge_type_id and output_edge_type_id
    """
    index: dict[tuple[str, str], dict[str, Any]] = {}
    counts = {"generated_lines": 0, "unique_rows": 0, "proven_rows": 0, "typed_rows": 0, "files": 0}
    seen_ids: set[str] = set()
    for fp in sorted(param_dir.glob("param_*.jsonl")):
        counts["files"] += 1
        with fp.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                counts["generated_lines"] += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ident = str(row.get("primitive_id") or row.get("content_hash")
                            or row.get("content_sha256_16") or line)
                if ident not in seen_ids:
                    seen_ids.add(ident)
                    counts["unique_rows"] += 1
                if row.get("input_edge_type_id") and row.get("output_edge_type_id"):
                    counts["typed_rows"] += 1
                if row.get("serves_truth") is not True:
                    continue  # LAW: a non-proven row is never counted as a reusable binding
                counts["proven_rows"] += 1
                fam = str(row.get("family", "?"))
                mut = str(row.get("mutator", "?"))
                slot = index.setdefault((fam, mut), {"count": 0, "binding_keys": set()})
                slot["count"] += 1
                binding = row.get("binding")
                if isinstance(binding, dict):
                    slot["binding_keys"].update(binding.keys())
    return index, counts


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# (a) COVERAGE — the ~40-intent task-space and the computed coverage
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def intent(iid: str, desc: str, family: str, mutator: str, needs: list[str] | None = None) -> dict[str, Any]:
    return {"intent_id": iid, "description": desc, "family": family, "mutator": mutator, "needs": needs or []}


def build_task_space() -> list[dict[str, Any]]:
    """~40 common data-op intents an agent routinely writes code for. Most map to a proven parametric family/mutator
    (should be COVERED); a deliberate tail maps to operations not yet in the corpus (honest `needs_generation` gaps,
    so coverage_pct is a real measurement < 100, not a rigged 100)."""
    return [
        # projection / selection
        intent("proj.keep_fields", "keep only these fields of a record", "projection_selection", "field_project"),
        intent("proj.pick", "pick a whitelisted subset of keys", "projection_selection", "dm_pick"),
        intent("proj.omit", "drop a blacklisted subset of keys", "projection_selection", "dm_omit"),
        intent("proj.rename", "rename fields via a mapping", "projection_selection", "field_rename"),
        intent("proj.deep_get", "extract a nested value by dotted path", "projection_selection", "dm_deep_get", ["path"]),
        # type coercion
        intent("cast.record_schema", "coerce a record to a typed schema", "type_coercion", "coerce_record_schema"),
        intent("cast.field_types", "cast named fields to declared types", "type_coercion", "type_cast"),
        intent("cast.to_int", "safely cast a value to int", "type_coercion", "to_int_safe"),
        intent("cast.to_float", "safely cast a value to float", "type_coercion", "to_float_safe"),
        intent("cast.or_none", "cast to a type or None on failure", "type_coercion", "cast_or_none", ["cast"]),
        intent("cast.strip_and_cast", "strip whitespace then cast", "type_coercion", "strip_and_cast"),
        # validation rules
        intent("valid.in_range", "validate a number is within [lo,hi]", "validation_rules", "vp_in_range"),
        intent("valid.required_keys", "validate required keys are present", "validation_rules", "vp_required_keys"),
        intent("valid.length_bound", "validate a length is within bounds", "validation_rules", "vp_length_bound"),
        intent("valid.enum_member", "validate a value is one of an enum", "validation_rules", "vp_enum_member", ["choices"]),
        intent("valid.regex_match", "validate a string matches a pattern", "validation_rules", "vp_regex_match"),
        # numeric transform
        intent("num.scale", "scale a number by a factor", "numeric_transform", "numeric_scale", ["factor"]),
        intent("num.scale_01", "min-max normalize to the unit interval", "numeric_transform", "numeric_scale_to_01", ["lo", "hi"]),
        intent("num.clamp", "clamp a number to [lo,hi]", "numeric_transform", "numeric_clamp"),
        intent("num.bucketize", "bucket a metric by boundaries", "numeric_transform", "numeric_bucketize"),
        intent("num.round_half_up", "round half-up to n places", "numeric_transform", "numeric_round_half_up"),
        # aggregation
        intent("agg.group_count", "count rows grouped by a key", "aggregation", "agg_group_count"),
        intent("agg.mean_field", "mean of a numeric field", "aggregation", "agg_mean_field"),
        intent("agg.sum_field", "sum of a numeric field", "aggregation", "agg_sum_field"),
        intent("agg.histogram", "histogram a field into bins", "aggregation", "agg_histogram_bins"),
        intent("agg.top_k", "top-k rows by a field", "aggregation", "agg_top_k_by"),
        # text ops
        intent("text.replace", "replace a substring in text", "text_ops", "ts_replace"),
        intent("text.slugify", "slugify a string", "text_ops", "ts_slugify"),
        intent("text.center", "center-pad a string to a width", "text_ops", "ts_center", ["width"]),
        intent("text.truncate", "truncate with an ellipsis", "text_ops", "ts_truncate_ellipsis"),
        intent("text.ljust", "left-justify a string", "text_ops", "ts_ljust"),
        # codec / hash
        intent("codec.base64", "base64-encode bytes/text", "codec_hash", "enc_base64_std"),
        intent("codec.hex", "hex-encode bytes/text", "codec_hash", "enc_hex"),
        intent("codec.sha256", "sha256-hash content", "codec_hash", "hc_sha256_hex"),
        intent("codec.url_quote", "url-quote a string", "codec_hash", "url_quote"),
        # relational / structural
        intent("rel.inner_join", "inner-join two row sets on a key", "relational_structural", "sr_inner_join_on_key"),
        intent("rel.group_by", "group rows by a key", "relational_structural", "sr_group_by_key"),
        intent("rel.dedupe_cluster", "dedupe-cluster rows by a key", "relational_structural", "sr_dedupe_cluster_key"),
        intent("rel.nest_by_key", "nest flat rows by a key", "relational_structural", "reshape_nest_by_key"),
        # ── honest GAPS: routine ops NOT yet in the proven corpus → needs_generation (keeps coverage a measurement) ──
        intent("gap.fuzzy_join", "fuzzy-join two row sets by string similarity", "relational_structural", "sr_fuzzy_join_similarity"),
        intent("gap.geocode", "geocode a postal address to lat/lon", "enrichment", "geo_forward_geocode"),
        intent("gap.currency_convert", "convert an amount between currencies", "numeric_transform", "fx_convert_amount"),
        intent("gap.pii_redact", "redact PII spans from free text", "text_ops", "ts_pii_redact"),
        intent("gap.sentiment", "score sentiment of a text", "enrichment", "nlp_sentiment_score"),
    ]


def compute_coverage(intents: list[dict[str, Any]],
                     proven_index: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    """COMPUTE (never assert) what fraction of the task-space a proven binding already covers. An intent is covered
    iff a proven (family, mutator) exists AND every required binding-knob has been observed on some proven row."""
    results: list[dict[str, Any]] = []
    for it in intents:
        slot = proven_index.get((it["family"], it["mutator"]))
        missing_knobs = [k for k in it["needs"] if not (slot and k in slot["binding_keys"])]
        covered = slot is not None and not missing_knobs
        results.append({
            "intent_id": it["intent_id"], "description": it["description"],
            "family": it["family"], "mutator": it["mutator"],
            "covered": covered,
            "proven_binding_count": (slot["count"] if slot else 0),
            "status": "covered" if covered else "needs_generation",
            "missing_knobs": missing_knobs,
        })
    total = len(results)
    covered = sum(1 for r in results if r["covered"])
    return {
        "total_intents": total,
        "covered_intents": covered,
        "needs_generation": total - covered,
        "coverage_pct": round(100.0 * covered / total, 2) if total else 0.0,
        "intents": results,
    }


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# (b) EXECUTION — composite routes proven by CHAINING real mutators against a hand-authored ground truth
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# Each route chains matched proven mutators. `expected` is the INDEPENDENT ground truth (computed by hand at author
# time, NOT by the registry). A route serves_truth ONLY if the executed chain equals `expected` and is deterministic.
def build_routes() -> list[dict[str, Any]]:
    return [
        {
            "route_id": "extract_cast_scale",
            "description": "deep-get a nested numeric string, cast to float, scale by a factor",
            "fixture": {"customer": {"balance": "100"}},
            "steps": [
                ("dm_deep_get", {"path": "customer.balance"}, "projection_selection"),
                ("cast_or_none", {"cast": "float"}, "type_coercion"),
                ("numeric_scale", {"factor": -1.32}, "numeric_transform"),
            ],
            "expected": -132.0,
        },
        {
            "route_id": "normalize_then_bucket",
            "description": "min-max normalize a reading to [0,1] then bucket it by boundaries",
            "fixture": 8.0,
            "steps": [
                ("numeric_scale_to_01", {"lo": -32, "hi": 128}, "numeric_transform"),
                ("numeric_bucketize", {"boundaries": [0.2, 0.5, 0.8]}, "numeric_transform"),
            ],
            "expected": 1,  # 0.25 → falls in (0.2, 0.5] → bin index 1
        },
        {
            "route_id": "cast_then_clamp",
            "description": "cast a text integer then clamp it to an allowed band",
            "fixture": "42",
            "steps": [
                ("cast_or_none", {"cast": "int"}, "type_coercion"),
                ("numeric_clamp", {"lo": 0, "hi": 10}, "numeric_transform"),
            ],
            "expected": 10,
        },
        {
            "route_id": "extract_then_validate_enum",
            "description": "extract a status field then validate it is a permitted enum member",
            "fixture": {"status": "active", "id": 7},
            "steps": [
                ("dm_deep_get", {"path": "status"}, "projection_selection"),
                ("vp_enum_member", {"choices": ["active", "closed"]}, "validation_rules"),
            ],
            "expected": {"check": "enum_member", "valid": True, "value": "active"},
        },
        {
            "route_id": "center_pad_text",
            "description": "center-pad a short code to a fixed width with a fill char",
            "fixture": "hi",
            "steps": [
                ("ts_center", {"width": 8, "fill": "0"}, "text_ops"),
            ],
            "expected": "000hi000",
        },
    ]


def run_route(route: dict[str, Any],
              proven_index: dict[tuple[str, str], dict[str, Any]] | None = None) -> dict[str, Any]:
    """EXECUTE a composite route end-to-end. serves_truth flips true ONLY when the chain runs, the final output
    equals the independent `expected`, AND a full re-run is identical (determinism). A raise or mismatch → false."""
    steps = route["steps"]
    matched = None
    if proven_index is not None:
        matched = all((fam, mut) in proven_index for (mut, _kw, fam) in steps)

    def _chain(start: Any) -> Any:
        value = start
        for (mutator, kwargs, _fam) in steps:
            value, _rec = apply_mutator(mutator, value, **kwargs)
        return value

    proofs: list[dict[str, Any]] = []
    try:
        final = _chain(route["fixture"])
    except Exception as exc:  # noqa: BLE001 — a broken/edge-mismatched route is a FAILED proof, never a crash-truth
        return {"route_id": route["route_id"], "description": route.get("description", ""),
                "steps": [m for (m, _k, _f) in steps], "matched_proven": matched,
                "passed": False, "serves_truth": False, "error": str(exc),
                "proofs": [{"name": "composite_execution", "passed": False, "error": str(exc)}],
                "verification_level": "L4_route_declared_failed"}
    behavior_ok = final == route["expected"]
    proofs.append({"name": "composite_behavior_test", "passed": behavior_ok,
                   "detail": f"final={final!r} expected={route['expected']!r}"})
    final2 = _chain(route["fixture"])
    det_ok = final2 == final
    proofs.append({"name": "determinism_test", "passed": det_ok,
                   "detail": "re-run identical" if det_ok else "non-deterministic!"})
    passed = behavior_ok and det_ok
    return {
        "route_id": route["route_id"], "description": route.get("description", ""),
        "steps": [m for (m, _k, _f) in steps], "matched_proven": matched,
        "passed": passed,
        # THE promotion: an executed passing composite proof is the only thing that flips serves_truth.
        "serves_truth": bool(passed),
        "proofs": proofs,
        "verification_level": "L7_executed_composite_proof" if passed else "L4_route_declared_failed",
        "final_output": final,
    }


def run_execution(routes: list[dict[str, Any]],
                  proven_index: dict[tuple[str, str], dict[str, Any]] | None = None) -> dict[str, Any]:
    results = [run_route(r, proven_index) for r in routes]
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    return {
        "total_routes": total,
        "passed_routes": passed,
        "exec_pass_rate": round(100.0 * passed / total, 2) if total else 0.0,
        "routes": results,
    }


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# report assembly + writers
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def build_report() -> dict[str, Any]:
    registry_size = load_param_mutators()
    proven_index, counts = load_proven_index()
    coverage = compute_coverage(build_task_space(), proven_index)
    execution = run_execution(build_routes(), proven_index)
    tokens_saved = coverage["covered_intents"] * EST_TOKENS_PER_REUSE
    return {
        "benchmark": "parametric_coverage_and_composite_execution",
        "generated_at": BENCHMARK_TS,
        "deterministic_offline": True,
        "registry_mutators_loaded": registry_size,
        "corpus_accounting": counts,
        "coverage": coverage,
        "execution": execution,
        "tokens_saved_estimate": tokens_saved,
        "tokens_saved_estimate_note": (
            f"ESTIMATE only (not measured, not serves_truth): covered_intents({coverage['covered_intents']}) "
            f"x EST_TOKENS_PER_REUSE({EST_TOKENS_PER_REUSE}) tokens an agent avoids by grabbing a proven binding "
            "instead of writing + unit-testing an equivalent leaf."),
        "proven_binding_families": sorted({f for (f, _m) in proven_index}),
    }


def render_markdown(rep: dict[str, Any]) -> str:
    cov, ex, ct = rep["coverage"], rep["execution"], rep["corpus_accounting"]
    lines: list[str] = []
    lines.append("# Parametric Coverage + Composite Execution Benchmark")
    lines.append("")
    lines.append(f"_Generated {rep['generated_at']} · deterministic + offline · no network / LLM / wall-clock / RNG._")
    lines.append("")
    lines.append("## Headline")
    lines.append("")
    lines.append(f"- **Coverage**: {cov['coverage_pct']}% — {cov['covered_intents']}/{cov['total_intents']} "
                 "common data-op intents satisfiable by an existing PROVEN parametric binding "
                 f"({cov['needs_generation']} still need generation).")
    lines.append(f"- **Composite execution**: {ex['exec_pass_rate']}% — {ex['passed_routes']}/{ex['total_routes']} "
                 "sampled routes chained real mutators end-to-end and matched an independent ground truth.")
    lines.append(f"- **Tokens saved (ESTIMATE)**: ~{rep['tokens_saved_estimate']:,} — {rep['tokens_saved_estimate_note']}")
    lines.append("")
    lines.append("## Honest corpus accounting (generated ≠ unique ≠ proven ≠ typed)")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("| --- | ---: |")
    lines.append(f"| param files | {ct['files']} |")
    lines.append(f"| generated lines | {ct['generated_lines']:,} |")
    lines.append(f"| unique rows (deduped) | {ct['unique_rows']:,} |")
    lines.append(f"| proven rows (serves_truth=true) | {ct['proven_rows']:,} |")
    lines.append(f"| typed rows (both edge type ids) | {ct['typed_rows']:,} |")
    lines.append(f"| registry mutators loaded | {rep['registry_mutators_loaded']} |")
    lines.append("")
    lines.append("## Coverage by intent")
    lines.append("")
    lines.append("| intent | family / mutator | status | proven bindings |")
    lines.append("| --- | --- | --- | ---: |")
    for r in cov["intents"]:
        mark = "✅ covered" if r["covered"] else "⬜ needs_generation"
        knob = "" if not r["missing_knobs"] else f" (missing knob: {', '.join(r['missing_knobs'])})"
        lines.append(f"| {r['intent_id']} | {r['family']} / `{r['mutator']}` | {mark}{knob} | {r['proven_binding_count']} |")
    lines.append("")
    lines.append("## Composite execution routes (real end-to-end proofs)")
    lines.append("")
    lines.append("| route | chain | matched proven | executed | serves_truth |")
    lines.append("| --- | --- | :---: | :---: | :---: |")
    for r in ex["routes"]:
        chain = " → ".join(f"`{s}`" for s in r["steps"])
        mp = {True: "yes", False: "no", None: "—"}[r["matched_proven"]]
        lines.append(f"| {r['route_id']} | {chain} | {mp} | {'PASS' if r['passed'] else 'FAIL'} "
                     f"| {'true' if r['serves_truth'] else 'false'} |")
    lines.append("")
    lines.append("> serves_truth is set ONLY by a passing executed proof of that route; a route that raises or "
                 "mismatches its independent expected value stays serves_truth=false (never inferred from a template).")
    lines.append("")
    return "\n".join(lines)


def write_outputs(rep: dict[str, Any], out_dir: Path = PARAM_DIR) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"coverage_benchmark_{BENCHMARK_DATE}.json"
    md_path = out_dir / f"coverage_benchmark_{BENCHMARK_DATE}.md"
    json_path.write_text(json.dumps(rep, indent=2, sort_keys=True, default=str) + "\n")
    md_path.write_text(render_markdown(rep))
    return {"json": str(json_path), "md": str(md_path)}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# --self-test (offline synthetic): coverage computes, an execution proof runs, a broken route FAILS
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def self_test() -> int:
    load_param_mutators()  # populate the real (offline, deterministic) registry so composite proofs can run
    checks: list[tuple[str, bool]] = []

    # 1. COVERAGE computes over a synthetic proven index (2 covered + 1 gap → 2/3).
    synth_index: dict[tuple[str, str], dict[str, Any]] = {
        ("numeric_transform", "numeric_scale"): {"count": 3, "binding_keys": {"factor"}},
        ("type_coercion", "cast_or_none"): {"count": 2, "binding_keys": {"cast"}},
    }
    synth_intents = [
        intent("s.scale", "scale", "numeric_transform", "numeric_scale", ["factor"]),
        intent("s.cast", "cast", "type_coercion", "cast_or_none", ["cast"]),
        intent("s.gap", "absent op", "numeric_transform", "does_not_exist"),
    ]
    cov = compute_coverage(synth_intents, synth_index)
    checks.append(("coverage computes (2/3 covered)",
                   cov["covered_intents"] == 2 and cov["needs_generation"] == 1
                   and abs(cov["coverage_pct"] - 66.67) < 0.01))
    # a required knob the proven rows never carried → NOT covered even though the mutator exists
    cov_knob = compute_coverage([intent("s.knob", "needs lo", "numeric_transform", "numeric_scale", ["lo"])], synth_index)
    checks.append(("missing binding-knob blocks coverage", cov_knob["covered_intents"] == 0))

    # 2. an EXECUTION proof actually RUNS and PASSES on a good route (independent hand-authored expected).
    good = {"route_id": "st_good", "description": "cast then scale", "fixture": "100",
            "steps": [("cast_or_none", {"cast": "float"}, "type_coercion"),
                      ("numeric_scale", {"factor": 2.0}, "numeric_transform")],
            "expected": 200.0}
    gres = run_route(good, synth_index)
    checks.append(("good route executes + is proven true",
                   gres["passed"] is True and gres["serves_truth"] is True
                   and gres["verification_level"] == "L7_executed_composite_proof"
                   and gres["matched_proven"] is True))

    # 3. a BROKEN route FAILS and is NOT promoted — two independent break modes:
    #    (a) edge-type mismatch: feed a dict into a numeric mutator → raises → caught → serves_truth stays false.
    broken_edge = {"route_id": "st_broken_edge", "fixture": {"a": 1},
                   "steps": [("numeric_scale", {"factor": 2.0}, "numeric_transform")], "expected": 999}
    bres = run_route(broken_edge, synth_index)
    checks.append(("broken (edge mismatch) route FAILS, not promoted",
                   bres["passed"] is False and bres["serves_truth"] is False and "error" in bres))
    #    (b) wrong ground truth: chain runs fine but final != expected → not promoted (gate is real, not a rubber stamp).
    broken_expect = {"route_id": "st_broken_expect", "fixture": "5",
                     "steps": [("cast_or_none", {"cast": "int"}, "type_coercion")], "expected": 999}
    wres = run_route(broken_expect, synth_index)
    checks.append(("wrong-expected route FAILS, not promoted",
                   wres["passed"] is False and wres["serves_truth"] is False))

    # 4. end-to-end: the REAL report builds, coverage/exec are computed numbers, accounting is split honestly.
    rep = build_report()
    checks.append(("real report builds with computed coverage + execution",
                   0.0 <= rep["coverage"]["coverage_pct"] <= 100.0
                   and 0.0 <= rep["execution"]["exec_pass_rate"] <= 100.0
                   and rep["corpus_accounting"]["generated_lines"] >= rep["corpus_accounting"]["proven_rows"]))
    checks.append(("markdown renders", "Parametric Coverage" in render_markdown(rep)))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - run_parametric_coverage_benchmark:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - run_parametric_coverage_benchmark: coverage computes ({cov['coverage_pct']}% on synthetic 2/3), "
          "a composite execution proof runs + promotes only on pass, and TWO broken routes (edge-mismatch + "
          "wrong-expected) correctly FAIL and stay serves_truth=false. Real report: "
          f"coverage={rep['coverage']['coverage_pct']}% exec_pass={rep['execution']['exec_pass_rate']}%.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="compute over the real corpus + write dated md/json")
    parser.add_argument("--self-test", action="store_true", help="offline synthetic verification")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.run:
        rep = build_report()
        paths = write_outputs(rep)
        print(json.dumps({
            "coverage_pct": rep["coverage"]["coverage_pct"],
            "covered_intents": rep["coverage"]["covered_intents"],
            "total_intents": rep["coverage"]["total_intents"],
            "exec_pass_rate": rep["execution"]["exec_pass_rate"],
            "passed_routes": rep["execution"]["passed_routes"],
            "total_routes": rep["execution"]["total_routes"],
            "tokens_saved_estimate": rep["tokens_saved_estimate"],
            "proven_rows": rep["corpus_accounting"]["proven_rows"],
            "generated_lines": rep["corpus_accounting"]["generated_lines"],
            "written": paths,
        }, indent=2))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
