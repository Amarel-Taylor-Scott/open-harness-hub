#!/usr/bin/env python3
"""scripts.build_step_path_portfolio_pack — the machine-readable "unlimited paths per step" registry.

The repo already has the canonical path spine — the Parallel-Path Engine
(``src.teleon.experiments.parallel_paths.run_parallel`` with servable/challenger modes) and the append-only
tracking ledger (``src.teleon.evolution.descent_attempt_store.DescentAttempt`` — every attempt with losers +
rollback preserved). What was missing is a SINGLE extensible catalog of WHICH paths each pipeline STEP can take, so
scrapers, builders, testers, benchmarks, generators, search, verify, compile, deploy, and the registry bridge all
declare their portfolio the same way and every path is trackable. This builder emits that catalog.

"Unlimited paths per step" is literal: adding a path is appending a row here; the engine already runs any number of
``candidate_paths``. Every path row references a REAL engine mode (imported from parallel_paths, never retyped),
declares when it wins, how it fails, its escalation order, and the receipt fields the tracking ledger records — so a
step never silently commits to one path and every choice is a receipt. All rows candidate=true / serves_truth=false.

Offline + deterministic (no network/RNG/wall-clock in rows; manifest date from --date). Regenerate via --write;
never hand-edit the pack. CLI: --self-test | --write [--date YYYY-MM-DD].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# single-source the engine modes so the catalog can NEVER drift from the real engine.
from src.teleon.experiments.parallel_paths import CHALLENGER_MODES, SERVABLE_MODES  # noqa: E402

PACK_DIR = _resource("catalog") / "knowledge-packs" / "data" / "step-path-portfolios"
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
ENGINE_REF = "src.teleon.experiments.parallel_paths.run_parallel"
LEDGER_REF = "src.teleon.evolution.descent_attempt_store.DescentAttempt"
ALL_MODES = tuple(dict.fromkeys(SERVABLE_MODES + CHALLENGER_MODES))  # baseline, fallback, candidate, shadow, canary

#: receipt fields every path execution records into the tracking ledger (superset; a step records what applies).
STANDARD_RECEIPT_FIELDS = [
    "step", "path_id", "engine_mode", "input_hash", "output_hash", "outcome",
    "cost", "latency_ms", "tokens_in", "tokens_out", "source_read_depth",
    "proof_status", "winner_reason", "losers", "rollback_target", "negative_memory_ref",
]

# ── The step portfolios. Each step lists an ORDERED escalation ladder of paths (cheapest/most-deterministic first);
#    the engine runs them as baseline + candidates and the ledger records which won. Extend by appending paths. ──
STEPS: dict[str, dict[str, Any]] = {
    "scrape": {
        "intent": "acquire source content from an external surface",
        "paths": [
            ("cached_snapshot", "baseline", "a fresh cached snapshot exists", "stale/missing snapshot", ["cache_hit_rate"]),
            ("structured_api", "candidate", "the surface exposes a machine-readable API/spec (OpenAPI/CKAN/Socrata/registry)", "no API, auth wall, rate limit", ["source_authority", "rows_yielded"]),
            ("html_fetch_parse", "candidate", "static HTML with stable selectors", "JS-rendered, selector drift", ["parse_success_rate"]),
            ("headless_browser", "candidate", "content requires JS render / interaction", "bot-detection, slow, fragile", ["render_success", "latency_ms"]),
            ("stealth_browser", "candidate", "site actively blocks automation", "captcha, IP ban", ["block_rate"]),
            ("vision_extraction", "fallback", "layout is visual/PDF/image only", "highest cost, OCR error", ["ocr_confidence"]),
            ("human_review", "fallback", "high-risk or repeatedly-blocked source", "slowest, human cost", ["human_review_rate"]),
        ],
        "escalation_note": "escalate ONLY when the cheaper path fails its receipt gate (escalate-before-unavailable law); "
                           "record honest-unavailable only after the ladder is exhausted.",
    },
    "build": {
        "intent": "produce candidate primitive rows / code / artifacts",
        "paths": [
            ("deterministic_table_row", "baseline", "source is already structured (MD table, catalog, schema)", "unstructured source", ["rows_per_token", "reject_rate"]),
            ("schema_driven_codegen", "candidate", "a JSON/OpenAPI/protobuf schema defines the shape", "no schema", ["contract_conformance"]),
            ("template_slot_fill", "candidate", "a primitive template + overlays cover the family", "no matching template", ["template_coverage"]),
            ("deterministic_remix", "candidate", "a near-match primitive exists (contract diff + mutators)", "no near match", ["mutator_success"]),
            ("model_bounded_generation", "candidate", "the missing edge needs semantic generation", "token cost, truncation, drift", ["tokens_to_pass", "reject_rate"]),
            ("source_fallback_codegen", "fallback", "no primitive/template/near-match exists", "highest source-read depth", ["source_read_depth"]),
        ],
        "escalation_note": "generate ONLY the missing edge; prefer deterministic paths (0 model tokens) and let the "
                           "reject/dup rate + saturation tracker decide when to escalate.",
    },
    "test": {
        "intent": "verify a candidate meets its contract before promotion",
        "paths": [
            ("schema_gate", "baseline", "every candidate — the L3 verifier shape/source/proof/dedupe gate", "shape-valid but semantically wrong", ["gate_pass_rate"]),
            ("deterministic_fixture", "candidate", "behavior is mechanical (roundtrip/idempotency/row-count)", "semantic fields need judgment", ["fixture_pass_rate"]),
            ("contract_test", "candidate", "the edge has a formal spec (OpenAPI/group-contract/AST)", "no formal spec", ["contract_pass_rate"]),
            ("skill_behavior_test", "candidate", "semantics need a bounded model in a compiled harness (Code-Factory pattern)", "model cost, non-determinism", ["behavior_pass_rate"]),
            ("differential_test", "shadow", "an alternate implementation exists to diff against", "no oracle", ["diff_agreement"]),
            ("human_review", "fallback", "high-risk domain (health-admin/legal/finance/cloud-mutation)", "slowest", ["human_review_rate"]),
        ],
        "escalation_note": "match rigor to risk; a zero-side-effect formatter needs the schema gate, a cloud-mutation "
                           "route needs contract + human review. Deeper proof promotes toward truth.",
    },
    "benchmark": {
        "intent": "score a route against baselines to decide promotion",
        "paths": [
            ("paired_arm_run", "baseline", "same task/fixtures/gates across arms A0..A8 (benchmark-lab-adapter-catalog)", "unverified track names", ["task_success", "tokens_to_pass", "depth_to_solution"]),
            ("offline_replay", "candidate", "a recorded task set exists to replay deterministically", "no recording", ["replay_agreement"]),
            ("shadow_production", "shadow", "compare a challenger against the live champion without serving it", "traffic needed", ["shadow_win_rate"]),
            ("canary_slice", "canary", "route is proof-backed; test on a small live slice", "risk of live regression", ["canary_regression_rate"]),
            ("uplift_matrix", "candidate", "SLM-vs-SOTA: model tier x harness arm x task family (uplift_ratio)", "compute-bound", ["uplift_ratio", "cost_per_success"]),
        ],
        "escalation_note": "no benchmark claim is truth without adapter receipts; external paper numbers stay prior art. "
                           "Track names are unverified intake until an adapter runs them.",
    },
    "search": {
        "intent": "retrieve a CandidateBundle of reusable primitives for an intent",
        "paths": [
            ("exact_edge", "baseline", "the input/output edge matches a promoted route", "no exact match", ["recall_at_k"]),
            ("blocking_lexical", "candidate", "keyword/label/contract-signature overlap (primitive_match lanes)", "vocabulary mismatch", ["recall_at_k", "false_match_rate"]),
            ("dense_vector", "candidate", "semantic similarity (nomic-embed-text 768)", "embedding drift, dim mixing", ["recall_at_k"]),
            ("hybrid_rrf", "candidate", "fuse lexical + dense (RRF_K=60)", "fusion tuning", ["recall_at_k"]),
            ("graph_route", "candidate", "multi-step compatible path through typed edges", "sparse graph", ["route_recall_at_k"]),
            ("negative_memory_suppress", "candidate", "a known-failure class should be demoted", "over-suppression", ["false_block_rate"]),
            ("source_fallback", "fallback", "the registry has a real gap → read source", "highest source-read depth", ["source_read_depth"]),
        ],
        "escalation_note": "search returns a BUNDLE not one answer; record which path found the winner (composition_affinity boost-only).",
    },
    "verify_bridge": {
        "intent": "make verified rows usable (searchable by the product)",
        "paths": [
            ("registry_bridge_load", "baseline", "verified rows exist to map into the searchable registry", "unmapped/malformed rows", ["cards_out", "registry_count_delta"]),
            ("operational_load", "candidate", "a Postgres/pgvector operational load is warranted", "load env unavailable", ["load_rows"]),
            ("dedupe_collapse", "candidate", "cross-lane duplicates should collapse before load", "over-collapse", ["collapsed_duplicates"]),
        ],
        "escalation_note": "a primitive is NOT made until it is searchable; registry-visible count is the real metric, "
                           "not the verified_candidates/ silo count.",
    },
    "compile": {
        "intent": "lower a chosen route into an executable artifact (PlanLock/code/config)",
        "paths": [
            ("deterministic_template_fill", "baseline", "the route maps to a validated template", "novel shape", ["compile_success"]),
            ("typed_graph_lowering", "candidate", "contracts are well-typed", "type gaps", ["compile_success"]),
            ("grammar_constrained_gen", "candidate", "output is a formal language (JSON/SQL/code)", "grammar coverage", ["syntax_error_rate"]),
            ("model_bounded_function", "candidate", "a small function body must be generated", "hallucination", ["compile_success", "tokens_to_pass"]),
            ("manual_approval_lock", "fallback", "high-side-effect or regulated route", "human cost", ["human_review_rate"]),
        ],
        "escalation_note": "execute the compiled PlanLock, never free-form model text; regeneration is driven by validation errors only.",
    },
    "deploy_package": {
        "intent": "package a proven route for a runtime/marketplace (PDU layer)",
        "paths": [
            ("dry_run_plan", "baseline", "always first — emit the plan/receipt before any mutation", "n/a (mandatory)", ["dry_run_receipt"]),
            ("oci_image_build", "candidate", "container runtime target", "base-image drift, CVE", ["sbom_receipt", "scan_receipt"]),
            ("iac_module_emit", "candidate", "terraform/pulumi/cdk/bicep target", "provider drift", ["plan_receipt"]),
            ("helm_operator_emit", "candidate", "kubernetes target", "cluster policy", ["install_test_receipt"]),
            ("marketplace_listing", "candidate", "distribution surface (AWS/Azure/GCP/ArtifactHub)", "submission checklist", ["submission_receipt"]),
            ("human_approval_publish", "fallback", "outward-facing publish", "irreversible without approval", ["approval_receipt"]),
        ],
        "escalation_note": "receipts-first; every outward-facing publish is approval-gated; base images are tracked "
                           "surfaces (digest pin + CVE/EOL rebuild triggers).",
    },
    "repair": {
        "intent": "recover a failed compile/execution without restarting from scratch",
        "paths": [
            ("read_failure_receipt", "baseline", "always first — classify the failure layer", "n/a", ["failure_class"]),
            ("negative_memory_lookup", "candidate", "a known failure class matches", "novel failure", ["suppression_hit"]),
            ("deterministic_mutator", "candidate", "the fix is mechanical (field/schema/wrapper)", "semantic gap", ["mutator_success"]),
            ("alternate_route", "candidate", "another candidate in the bundle fits", "bundle exhausted", ["alt_route_success"]),
            ("context_ladder_escalate", "candidate", "one level deeper context resolves it (L1→L7)", "cost", ["depth_to_solution"]),
            ("model_micro_repair", "fallback", "a bounded model patch is needed", "over-generation", ["repair_success", "tokens"]),
            ("gap_queue_new_primitive", "fallback", "the registry has a real gap", "new demand", ["gap_record_created"]),
        ],
        "escalation_note": "model retries are targeted by validation errors, never open-ended; still-failing → write negative memory.",
    },
}


def _step_rows() -> list[dict[str, Any]]:
    rows = []
    for step, spec in STEPS.items():
        paths = []
        for order, (pid, mode, when_wins, how_fails, extra_receipts) in enumerate(spec["paths"]):
            paths.append({
                "path_id": pid,
                "engine_mode": mode,
                "escalation_order": order,
                "when_wins": when_wins,
                "how_fails": how_fails,
                "receipt_fields": sorted(set(STANDARD_RECEIPT_FIELDS) | set(extra_receipts)),
            })
        rows.append({
            "record_type": "step_path_portfolio",
            "step": step,
            "intent": spec["intent"],
            "path_count": len(paths),
            "paths": paths,
            "escalation_note": spec["escalation_note"],
            "engine_ref": ENGINE_REF,
            "tracking_ledger_ref": LEDGER_REF,
            "extensible": "append a path to STEPS['%s'] in the builder; the engine runs any number of candidate_paths" % step,
            **BOUNDARY,
        })
    return rows


def _mode_rows() -> list[dict[str, Any]]:
    doc = {
        "baseline": "the current champion path; always run; the rollback_target for every promotion.",
        "candidate": "a challenger competing to be served; promoted ONLY via a passing promotion decision.",
        "shadow": "runs but never affects output; gathers evidence with zero user risk.",
        "canary": "serves a small slice after proof; watched for live regression.",
        "fallback": "the escalation path when servable paths fail their receipt gate.",
    }
    return [{
        "record_type": "engine_mode",
        "mode": mode,
        "servable": mode in SERVABLE_MODES,
        "challenger": mode in CHALLENGER_MODES,
        "meaning": doc.get(mode, ""),
        **BOUNDARY,
    } for mode in ALL_MODES]


def _receipt_schema_rows() -> list[dict[str, Any]]:
    units = {
        "step": "which pipeline step ran", "path_id": "which path in the step portfolio",
        "engine_mode": "baseline|candidate|shadow|canary|fallback", "input_hash": "sha256 of the input snapshot",
        "output_hash": "sha256 of the produced output", "outcome": "improved|no_change|regressed|failed",
        "cost": "relative or usd cost", "latency_ms": "wall-clock ms", "tokens_in": "prompt tokens",
        "tokens_out": "completion tokens", "source_read_depth": "L1..L7 context depth reached",
        "proof_status": "which proofs passed", "winner_reason": "why this path won the run",
        "losers": "paths that lost (preserved as training negatives)", "rollback_target": "the baseline to revert to",
        "negative_memory_ref": "id of any negative-memory record written on failure",
    }
    return [{"record_type": "path_receipt_field", "field": f, "meaning": units.get(f, ""), **BOUNDARY}
            for f in STANDARD_RECEIPT_FIELDS]


JSONL_BUILDERS: dict[str, Callable[[], list[dict[str, Any]]]] = {
    "step_path_portfolios.jsonl": _step_rows,
    "engine_modes.jsonl": _mode_rows,
    "path_receipt_fields.jsonl": _receipt_schema_rows,
}


def build_pack() -> dict[str, list[dict[str, Any]]]:
    return {name: builder() for name, builder in JSONL_BUILDERS.items()}


def build_manifest(pack: dict[str, list[dict[str, Any]]], *, date: str) -> dict[str, Any]:
    row_counts = {name: len(rows) for name, rows in pack.items()}
    total_paths = sum(r["path_count"] for r in pack["step_path_portfolios.jsonl"])
    canonical = "\n".join(
        json.dumps(row, sort_keys=True, ensure_ascii=False)
        for name in sorted(pack) for row in pack[name]
    )
    return {
        "record_type": "step_path_portfolio_pack_manifest",
        "pack_id": "step-path-portfolios",
        "generator": "scripts/build_step_path_portfolio_pack.py",
        "generated_utc": date,
        "row_counts": row_counts,
        "total_rows": sum(row_counts.values()),
        "step_count": len(pack["step_path_portfolios.jsonl"]),
        "total_paths_across_steps": total_paths,
        "engine_ref": ENGINE_REF,
        "tracking_ledger_ref": LEDGER_REF,
        "engine_modes": list(ALL_MODES),
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        **BOUNDARY,
    }


def write_pack(*, date: str) -> dict[str, Any]:
    pack = build_pack()
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in pack.items():
        (PACK_DIR / name).write_text(
            "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(pack, date=date)
    (PACK_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    pack = build_pack()
    manifest = build_manifest(pack, date="1970-01-01")
    checks = [
        ("every step has >=3 paths (portfolio, never single)", all(r["path_count"] >= 3 for r in pack["step_path_portfolios.jsonl"])),
        ("scrape/build/test/benchmark all present", {"scrape", "build", "test", "benchmark"} <= {r["step"] for r in pack["step_path_portfolios.jsonl"]}),
        ("every path mode is a REAL engine mode", all(
            p["engine_mode"] in ALL_MODES
            for r in pack["step_path_portfolios.jsonl"] for p in r["paths"])),
        ("every step has exactly one baseline", all(
            sum(1 for p in r["paths"] if p["engine_mode"] == "baseline") == 1
            for r in pack["step_path_portfolios.jsonl"])),
        ("escalation orders are 0..n-1 contiguous", all(
            [p["escalation_order"] for p in r["paths"]] == list(range(r["path_count"]))
            for r in pack["step_path_portfolios.jsonl"])),
        ("every path carries receipt fields", all(
            p["receipt_fields"] for r in pack["step_path_portfolios.jsonl"] for p in r["paths"])),
        ("boundary held on every row", all(
            row.get("candidate") is True and row.get("serves_truth") is False
            for rows in pack.values() for row in rows)),
        ("manifest counts computed", manifest["total_paths_across_steps"] > 30 and manifest["step_count"] >= 8),
    ]
    failed = [name for name, ok in checks if not ok]
    if failed:
        print("FAIL - step_path_portfolio_pack:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - step_path_portfolio_pack: {manifest['step_count']} steps, "
          f"{manifest['total_paths_across_steps']} tracked paths, modes single-sourced from the engine.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    manifest = write_pack(date=date)
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
