#!/usr/bin/env python3
"""Validate the compiled primitive route benchmark seed pack.

Enforces the validation rules from
``_repos/shared-backend-components/docs/codex/claude-fable-compiled-primitive-routes-handoff.md`` against the
ON-DISK pack under
``_repos/shared-backend-components/catalog/knowledge-packs/data/compiled-primitive-route-benchmark-seeds/``:

* every row (and manifest, and JSON policies) keeps candidate=true / serves_truth=false;
* every benchmark source declares source_status and adapter_state (all unbuilt —
  no external paper number is local measured evidence);
* every task demand declares separate input_edge and output_edge;
* every comparison arm declares allowed model/runtime behavior and maps into
  the Benchmark Lab A0..A8 arms (single-sourced, never re-typed);
* every scorecard covers token, proof, depth, and reuse metric categories;
* every path record declares when it should win AND how it can fail;
* every route portfolio carries at least three candidate paths with resolvable
  cross-references (generation/search/planner/compiler/runtime/proof/model-slot);
* the adaptive layer holds: model slots keep a >=2-lane portfolio with receipt
  fields, adapters carry lineage + rollback fields, micro-agent envelopes are
  bounded, sprouts stay candidate-isolated with held-out promotion, telemetry
  covers every feedback loop, caches declare invalidation + privacy rules;
* promotion (lifecycle L10) requires adapter receipts for any benchmark claim;
* ids are version-free and unique; manifest counts and content hash match;
* FRESHNESS: the on-disk rows byte-match a regeneration from the builder
  (``_repos/shared-backend-components/scripts/build_compiled_primitive_route_benchmark_seeds.py`` is the single
  source — hand-edits to pack files go red here).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_DIR,
    COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_EVIDENCE_STATUS,
    REPO_ROOT,
)
from scripts.build_compiled_primitive_route_benchmark_seeds import (  # noqa: E402
    BENCHMARK_LAB_ARM_IDS,
    CACHE_INVALIDATION_TRIGGERS,
    DEPTH_LEVELS,
    FEEDBACK_LOOPS,
    JSON_BUILDERS,
    JSONL_BUILDERS,
    MODEL_ROUTE_RECEIPT_FIELDS,
    SERVED_BY_LANES,
    build_manifest,
    build_pack,
)

PACK_DIR = _resource(COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_DIR)
FORBIDDEN_ID_PATTERN = re.compile(
    r"(@|(?:^|[:._-])v\d+(?:$|[:._-])|(?:^|[:._-])latest(?:$|[:._-])|20\d{2}[-_]\d{2})",
    re.IGNORECASE,
)
# Files whose rows are path choices and must declare wins_when + fails_when.
PATH_CHOICE_FILES = [
    "primitive_generation_paths.jsonl",
    "primitive_search_paths.jsonl",
    "route_planning_paths.jsonl",
    "compilation_paths.jsonl",
    "proof_paths.jsonl",
    "runtime_execution_paths.jsonl",
    "repair_ladder.jsonl",
    "comparison_arms.jsonl",
    "model_slot_lanes.jsonl",
    "adapter_lanes.jsonl",
    "micro_agent_envelopes.jsonl",
    "trial_run_policies.jsonl",
    "exploration_policies.jsonl",
    "path_sprout_rules.jsonl",
    "cache_policies.jsonl",
]
ID_FIELD_BY_FILE = {
    "benchmark_sources.jsonl": "source_id",
    "benchmark_task_demands.jsonl": "task_id",
    "primitive_generation_paths.jsonl": "path_id",
    "primitive_search_paths.jsonl": "path_id",
    "route_planning_paths.jsonl": "planner_id",
    "compilation_paths.jsonl": "compiler_id",
    "proof_paths.jsonl": "proof_id",
    "runtime_execution_paths.jsonl": "path_id",
    "repair_ladder.jsonl": "repair_id",
    "comparison_arms.jsonl": "arm_id",
    "scorecard_fields.jsonl": "field_id",
    "route_portfolio_examples.jsonl": "portfolio_id",
    "compiled_route_lifecycle.jsonl": "stage_id",
    "model_slot_lanes.jsonl": "slot_id",
    "adapter_lanes.jsonl": "adapter_id",
    "micro_agent_envelopes.jsonl": "agent_id",
    "trial_run_policies.jsonl": "policy_id",
    "exploration_policies.jsonl": "policy_id",
    "path_sprout_rules.jsonl": "sprout_id",
    "telemetry_signals.jsonl": "signal_id",
    "primitive_cooccurrence_examples.jsonl": "cooc_id",
    "cache_policies.jsonl": "cache_id",
    "strategy_genome_examples.jsonl": "genome_id",
}


def _fail(message: str) -> None:
    raise AssertionError(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"{path}: expected JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            _fail(f"{path}:{line_number}: expected JSON object")
        rows.append(value)
    if not rows:
        _fail(f"{path}: expected rows")
    return rows


def _require_boundary(row: dict[str, Any], row_id: str) -> None:
    if row.get("candidate") is not True:
        _fail(f"{row_id}: must keep candidate=true")
    if row.get("serves_truth") is not False:
        _fail(f"{row_id}: must keep serves_truth=false")


def _load_disk_pack(manifest: dict[str, Any]) -> dict[str, Any]:
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        _fail("manifest must declare files")
    pack: dict[str, Any] = {}
    for name in files.values():
        path = PACK_DIR / str(name)
        if not path.is_file():
            _fail(f"declared pack file missing on disk: {name}")
        pack[str(name)] = _read_jsonl(path) if str(name).endswith(".jsonl") else _read_json(path)
    return pack


def self_test() -> dict[str, Any]:
    manifest = _read_json(PACK_DIR / "manifest.json")
    _require_boundary(manifest, "manifest")
    disk = _load_disk_pack(manifest)

    expected_files = set(JSONL_BUILDERS) | set(JSON_BUILDERS)
    if set(disk) != expected_files:
        _fail(f"pack files diverge from builder registry: {sorted(set(disk) ^ expected_files)}")

    # ── Freshness: disk must byte-match a regeneration from the builder ──
    built = build_pack()
    for name in sorted(expected_files):
        if disk[name] != built[name]:
            _fail(f"{name}: on-disk rows diverge from the builder — regenerate via "
                  "`python3 scripts/build_compiled_primitive_route_benchmark_seeds.py --write`")
    rebuilt_manifest = build_manifest(built)
    for key in ("files", "row_counts", "total_rows", "file_count", "content_sha256",
                "pack_id", "version", "source_status", "evidence_status"):
        if manifest.get(key) != rebuilt_manifest.get(key):
            _fail(f"manifest.{key} is stale versus the builder")

    # ── Boundary + version-free unique ids on every row ──
    for name, value in disk.items():
        rows = value if isinstance(value, list) else [value]
        for row in rows:
            _require_boundary(row, f"{name} row")
        id_field = ID_FIELD_BY_FILE.get(name)
        if id_field:
            ids = [str(row.get(id_field) or "") for row in value]
            if "" in ids or len(ids) != len(set(ids)):
                _fail(f"{name}: {id_field} must be present and unique")
            for row_id in ids:
                if FORBIDDEN_ID_PATTERN.search(row_id):
                    _fail(f"{name}: id must be version-free: {row_id!r}")

    # ── Benchmark sources: status + adapter discipline ──
    for row in disk["benchmark_sources.jsonl"]:
        if not row.get("source_status") or not row.get("adapter_state"):
            _fail(f"{row['source_id']}: must declare source_status and adapter_state")
        if row["adapter_state"] != "unbuilt":
            _fail(f"{row['source_id']}: no source may claim a built adapter in the seed pack")
        if row.get("evidence_status") != COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_EVIDENCE_STATUS:
            _fail(f"{row['source_id']}: evidence_status must disclaim local measurement "
                  f"({COMPILED_PRIMITIVE_ROUTE_BENCHMARK_SEEDS_EVIDENCE_STATUS!r})")

    # ── Task demands: separate edges + resolvable references ──
    source_ids = {row["source_id"] for row in disk["benchmark_sources.jsonl"]}
    arm_ids = {row["arm_id"] for row in disk["comparison_arms.jsonl"]}
    score_rows = disk["scorecard_fields.jsonl"]
    score_ids = {row["field_id"] for row in score_rows}
    for task in disk["benchmark_task_demands.jsonl"]:
        task_id = task["task_id"]
        for field in ("input_edge", "output_edge"):
            edge = str(task.get(field) or "")
            if not edge:
                _fail(f"{task_id}: must declare {field}")
            if "->" in edge:
                _fail(f"{task_id}: {field} must stay a single edge (no '->')")
        if task["source_family"] not in source_ids:
            _fail(f"{task_id}: unknown source_family")
        if not set(task["comparison_arms"]) <= arm_ids:
            _fail(f"{task_id}: unknown comparison arm")
        if not set(task["scorecard_fields"]) <= score_ids:
            _fail(f"{task_id}: unknown scorecard field")
        task_categories = {row["metric_category"] for row in score_rows
                           if row["field_id"] in set(task["scorecard_fields"])}
        if not {"token", "proof", "depth", "reuse"} <= task_categories:
            _fail(f"{task_id}: scorecard must include token, proof, depth, and reuse metrics")
        if task["depth_target"] not in DEPTH_LEVELS:
            _fail(f"{task_id}: depth_target outside the benchmark-lab ladder")

    # ── Comparison arms: allowed behavior + Benchmark Lab cross-reference ──
    for arm in disk["comparison_arms.jsonl"]:
        if not arm.get("allowed_model_use") or not arm.get("allowed_runtime_behavior"):
            _fail(f"{arm['arm_id']}: must declare allowed model AND runtime behavior")
        if not set(arm["benchmark_lab_arm_refs"]) <= set(BENCHMARK_LAB_ARM_IDS):
            _fail(f"{arm['arm_id']}: benchmark_lab_arm_refs must map into A0..A8")

    # ── Every path record declares when it wins and how it fails ──
    for name in PATH_CHOICE_FILES:
        for row in disk[name]:
            wins, fails = row.get("wins_when"), row.get("fails_when")
            if not isinstance(wins, list) or not wins or not isinstance(fails, list) or not fails:
                _fail(f"{name}: every path record needs non-empty wins_when and fails_when")

    # ── Route portfolios: >=3 paths, resolvable members ──
    gen_ids = {r["path_id"] for r in disk["primitive_generation_paths.jsonl"]}
    search_ids = {r["path_id"] for r in disk["primitive_search_paths.jsonl"]}
    planner_ids = {r["planner_id"] for r in disk["route_planning_paths.jsonl"]}
    compiler_ids = {r["compiler_id"] for r in disk["compilation_paths.jsonl"]}
    proof_ids = {r["proof_id"] for r in disk["proof_paths.jsonl"]}
    runtime_ids = {r["path_id"] for r in disk["runtime_execution_paths.jsonl"] if r["kind"] == "runtime"}
    pattern_ids = {r["path_id"] for r in disk["runtime_execution_paths.jsonl"] if r["kind"] == "execution_pattern"}
    slot_ids = {r["slot_id"] for r in disk["model_slot_lanes.jsonl"]}
    task_ids = {r["task_id"] for r in disk["benchmark_task_demands.jsonl"]}
    genome_ids = {r["genome_id"] for r in disk["strategy_genome_examples.jsonl"]}
    trial_ids = {r["policy_id"] for r in disk["trial_run_policies.jsonl"]}
    for portfolio in disk["route_portfolio_examples.jsonl"]:
        pid = portfolio["portfolio_id"]
        paths = portfolio.get("candidate_paths") or []
        if len(paths) < 3:
            _fail(f"{pid}: every route portfolio needs at least three candidate paths")
        if portfolio["task_ref"] not in task_ids:
            _fail(f"{pid}: task_ref does not resolve")
        if portfolio["strategy_genome_ref"] not in genome_ids:
            _fail(f"{pid}: strategy_genome_ref does not resolve")
        if portfolio["trial_policy_ref"] not in trial_ids:
            _fail(f"{pid}: trial_policy_ref does not resolve")
        for path in paths:
            checks = [
                (path["generation_path"], gen_ids), (path["search_path"], search_ids),
                (path["planner"], planner_ids), (path["compiler"], compiler_ids),
                (path["runtime"], runtime_ids),
            ]
            for ref, universe in checks:
                if ref not in universe:
                    _fail(f"{pid}/{path['path_id']}: unresolvable member {ref!r}")
            if not set(path["execution_patterns"]) <= pattern_ids:
                _fail(f"{pid}/{path['path_id']}: unknown execution pattern")
            if not set(path["proof_refs"]) <= proof_ids:
                _fail(f"{pid}/{path['path_id']}: unknown proof ref")
            for slot, lane in path["model_slot_assignments"].items():
                if slot not in slot_ids or lane not in SERVED_BY_LANES:
                    _fail(f"{pid}/{path['path_id']}: bad model slot assignment {slot}->{lane}")
            if not path.get("expected_strength") or not path.get("known_failure"):
                _fail(f"{pid}/{path['path_id']}: paths must declare expected_strength and known_failure")

    # ── Adaptive layer invariants ──
    for slot in disk["model_slot_lanes.jsonl"]:
        if len(slot["served_by"]) < 2 or not set(slot["served_by"]) <= set(SERVED_BY_LANES):
            _fail(f"{slot['slot_id']}: model slots keep a portfolio of >=2 known lanes")
        if slot["receipt_fields"] != MODEL_ROUTE_RECEIPT_FIELDS:
            _fail(f"{slot['slot_id']}: model route receipt fields drifted")
    for adapter in disk["adapter_lanes.jsonl"]:
        if not set(adapter["allowed_slots"]) <= slot_ids:
            _fail(f"{adapter['adapter_id']}: allowed_slots must reference model slots")
        for field in ("training_data_lineage", "rollback_receipts", "promotion_receipts"):
            if field not in adapter["required_record_fields"]:
                _fail(f"{adapter['adapter_id']}: adapter records must require {field}")
        if not adapter.get("lift_criteria"):
            _fail(f"{adapter['adapter_id']}: adapters must declare measurable lift criteria")
    for agent in disk["micro_agent_envelopes.jsonl"]:
        envelope = agent.get("envelope") or {}
        for key in ("max_steps", "max_tokens", "max_wall_time_seconds", "stop_conditions",
                    "human_review_trigger"):
            if not envelope.get(key):
                _fail(f"{agent['agent_id']}: micro-agent envelope missing {key}")
    for sprout in disk["path_sprout_rules.jsonl"]:
        if sprout.get("status") != "candidate":
            _fail(f"{sprout['sprout_id']}: sprouts stay candidate-only")
        if "held-out" not in str(sprout.get("promotion_rule") or ""):
            _fail(f"{sprout['sprout_id']}: promotion must require held-out wins")
        if "never serves production" not in str(sprout.get("isolation_rule") or ""):
            _fail(f"{sprout['sprout_id']}: sprouts must be isolated from production")
    covered = set()
    for signal in disk["telemetry_signals.jsonl"]:
        loops = signal.get("feeds_back_into") or []
        if not loops or not set(loops) <= set(FEEDBACK_LOOPS):
            _fail(f"{signal['signal_id']}: telemetry must feed known feedback loops")
        covered.update(loops)
    if covered != set(FEEDBACK_LOOPS):
        _fail(f"telemetry leaves feedback loops uncovered: {sorted(set(FEEDBACK_LOOPS) - covered)}")
    for cache in disk["cache_policies.jsonl"]:
        triggers = cache.get("invalidation_triggers") or []
        if not triggers or not set(triggers) <= set(CACHE_INVALIDATION_TRIGGERS):
            _fail(f"{cache['cache_id']}: caches must declare known invalidation triggers")
        if "never raw private payloads" not in str(cache.get("privacy_rule") or ""):
            _fail(f"{cache['cache_id']}: caches must carry the privacy rule")

    # ── Lifecycle: benchmark claims need adapter receipts before promotion ──
    lifecycle = disk["compiled_route_lifecycle.jsonl"]
    if [s["stage_index"] for s in lifecycle] != list(range(11)):
        _fail("lifecycle must run L0..L10 contiguously")
    final = lifecycle[-1]
    if "adapter_receipts_for_any_benchmark_claim" not in (final.get("promotion_requires") or []):
        _fail("L10 promotion must require adapter receipts for any benchmark claim")
    benchmark_stage = lifecycle[9]
    if "adapter_receipt" not in benchmark_stage["receipts_required"]:
        _fail("L9 benchmark score recording must require an adapter receipt")

    # ── Policies: training capture + champion/challenger shape ──
    training = disk["route_attempt_training_capture_policy.json"]
    if training.get("every_route_attempt_becomes_training_data") is not True:
        _fail("training capture policy must capture every route attempt")
    if "excluded from production truth" not in str(training["isolation"]["experimental_sprouts"]):
        _fail("training capture policy must isolate experimental sprouts from production truth")
    champion = disk["champion_challenger_policy.json"]
    if len(champion["ranking"]["multi_objective_features"]) < 8:
        _fail("champion/challenger ranking must stay multi-objective (>=8 features)")
    if champion["ranking"].get("contextual") is not True:
        _fail("path ranking must be contextual, never one global winner")
    economics = disk["route_economics_model.json"]
    if economics["route_score"].get("score_is_ranking_aid_not_truth") is not True:
        _fail("route score must be declared a ranking aid, not truth")

    return {
        "pack_id": manifest["pack_id"],
        "files": manifest["file_count"],
        "total_rows": manifest["total_rows"],
        "task_demands": len(disk["benchmark_task_demands.jsonl"]),
        "route_portfolios": len(disk["route_portfolio_examples.jsonl"]),
        "model_slot_lanes": len(disk["model_slot_lanes.jsonl"]),
        "telemetry_signals": len(disk["telemetry_signals.jsonl"]),
        "candidate": True,
        "serves_truth": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run validation checks")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("expected --self-test")
    print(json.dumps(self_test(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
