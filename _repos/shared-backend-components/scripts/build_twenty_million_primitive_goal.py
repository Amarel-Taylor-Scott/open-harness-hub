#!/usr/bin/env python3
"""Build the 20M primitive goal control plane.

This emits a candidate-only, machine-callable plan for deterministic,
non-deterministic, hybrid, research-oriented, remix, benchmark, proof, and
failure-mode generators. It does not promote generated rows.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

_SBC = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "scripts" / "_repo_paths.py").exists()),
    Path(__file__).resolve().parents[1],
)
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))

from scripts._repo_paths import install as _install  # noqa: E402

_install()

from scripts._repo_paths import repo_root as _repo_root  # noqa: E402
from scripts._repo_paths import resource as _resource  # noqa: E402


RECORD_TYPE = "twenty_million_primitive_goal"
TARGET_WORKING_PRIMITIVES = 20_000_000
DEFAULT_OUT_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "20m_goal"
DEFAULT_ROWS_PER_SHARD = 10_000
DEFAULT_DAILY_WORKING_TARGET = 100_000
DEFAULT_DAILY_CANDIDATE_TARGET = 400_000
DEFAULT_HORIZON_DAYS = 60
MAX_HORIZON_DAYS = 365

MILLION_BUNDLE_MANIFEST = (
    _resource("data")
    / "dev-intel"
    / "primitive_million_seed_bundle"
    / "common-software-primitive-seed-bundle-million"
    / "manifest.json"
)
VERIFIED_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "verified_candidates"
LINKABLE_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "linkable_cards"
MILLION_COMPILER_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "million_seed_compiler_runs"
SUPERVISED_CYCLE_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "20m_goal" / "supervised_cycles"


GENERATOR_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "family_id": "gen:deterministic.seed-bundle-expander",
        "generator_class": "deterministic",
        "target_working_primitives": 2_000_000,
        "implementation_refs": ["scripts/generate_million_primitive_seed_bundle.py"],
        "source_planes": ["dimension_cross_product", "known_runtime_surfaces", "policy_overlays"],
        "output_level": "L1_seed_rows",
    },
    {
        "family_id": "gen:deterministic.route-mutator",
        "generator_class": "deterministic",
        "target_working_primitives": 1_250_000,
        "implementation_refs": ["data/dev-intel/primitive_route_fixtures"],
        "source_planes": ["input_output_edge_mutations", "adapter_mutators", "route_fixtures"],
        "output_level": "L2_candidate_routes",
    },
    {
        "family_id": "gen:deterministic.schema-api-compiler",
        "generator_class": "deterministic",
        "target_working_primitives": 1_250_000,
        "implementation_refs": ["scripts/build_primitive_pipeline_catalog_intake.py"],
        "source_planes": ["openapi", "asyncapi", "graphql", "json_schema", "protobuf"],
        "output_level": "L2_schema_backed_candidates",
    },
    {
        "family_id": "gen:deterministic.repo-symbol-compiler",
        "generator_class": "deterministic",
        "target_working_primitives": 1_000_000,
        "implementation_refs": ["scripts/primitive_quality_promoter.py"],
        "source_planes": ["repo_symbols", "tests", "docs", "module_boundaries"],
        "output_level": "L3_contract_known",
    },
    {
        "family_id": "gen:deterministic.ui-component-miner",
        "generator_class": "deterministic",
        "target_working_primitives": 750_000,
        "implementation_refs": ["scripts/aidevobserver_context_foundry_loop.py"],
        "source_planes": ["frontend_components", "routes", "forms", "state_transitions"],
        "output_level": "L2_surface_candidates",
    },
    {
        "family_id": "gen:deterministic.notebook-dataset-compiler",
        "generator_class": "deterministic",
        "target_working_primitives": 750_000,
        "implementation_refs": ["scripts/aidevobserver_context_foundry_loop.py"],
        "source_planes": ["kaggle_notebooks", "datasets", "feature_pipelines", "metric_cells"],
        "output_level": "L2_data_science_candidates",
    },
    {
        "family_id": "gen:nondeterministic.gemma-long-group-synthesizer",
        "generator_class": "nondeterministic",
        "target_working_primitives": 1_500_000,
        "implementation_refs": ["scripts/run_gemma_long_multistep_primitive_lane.py"],
        "source_planes": ["deconstruction_candidates", "long_multistep_groups", "hidden_member_edges"],
        "output_level": "L3_model_written_group_candidates",
        "model_refs": ["gemma-4-coding"],
    },
    {
        "family_id": "gen:nondeterministic.glm-contract-writer",
        "generator_class": "nondeterministic",
        "target_working_primitives": 1_250_000,
        "implementation_refs": ["scripts/run_primitive_provider_fleet_loop.py"],
        "source_planes": ["contract_review", "schema_repair", "source_ref_repair"],
        "output_level": "L3_reviewed_candidates",
        "model_refs": ["glm-5.2"],
    },
    {
        "family_id": "gen:nondeterministic.kimi-long-expander",
        "generator_class": "nondeterministic",
        "target_working_primitives": 1_250_000,
        "implementation_refs": ["scripts/run_primitive_provider_fleet_loop.py"],
        "source_planes": ["long_expansion", "variant_generation", "edge_description_expansion"],
        "output_level": "L3_expanded_candidates",
        "model_refs": ["kimi-k2.7-code"],
    },
    {
        "family_id": "gen:nondeterministic.codex-gap-closer",
        "generator_class": "nondeterministic",
        "target_working_primitives": 750_000,
        "implementation_refs": ["scripts/run_codex_north_star_gap_loop.sh"],
        "source_planes": ["repo_gaps", "tests", "implementation_todos", "north_star_alignment"],
        "output_level": "L4_repo_backed_working_candidates",
        "model_refs": ["codex"],
    },
    {
        "family_id": "gen:hybrid.seed-model-enricher",
        "generator_class": "hybrid",
        "target_working_primitives": 1_500_000,
        "implementation_refs": ["scripts/run_million_seed_bundle_compiler.py", "scripts/run_primitive_factory_batch_loop.py"],
        "source_planes": ["deterministic_seed", "model_expansion", "deterministic_validation"],
        "output_level": "L3_verified_candidates",
    },
    {
        "family_id": "gen:hybrid.retrieval-augmented-generator",
        "generator_class": "hybrid",
        "target_working_primitives": 1_000_000,
        "implementation_refs": ["scripts/run_token_savings_experiments.py", "scripts/package_linkable_primitive_cards.py"],
        "source_planes": ["retrieved_cards", "source_refs", "compact_context", "reuse_profile"],
        "output_level": "L4_linkable_cards",
    },
    {
        "family_id": "gen:hybrid.agent-primitive-composer",
        "generator_class": "hybrid",
        "target_working_primitives": 750_000,
        "implementation_refs": ["scripts/primitive_deconstruction_plane_pipeline.py"],
        "source_planes": ["review", "voting_selection", "planning_execution", "organizer", "knowledge_pool"],
        "output_level": "L4_composable_agent_primitive_groups",
    },
    {
        "family_id": "gen:research.paper-method-decomposer",
        "generator_class": "research_oriented",
        "target_working_primitives": 1_000_000,
        "implementation_refs": ["scripts/continuous_primitive_scrape_loop.py"],
        "source_planes": ["arxiv", "openreview", "google_scholar_metadata", "benchmarks", "method_sections"],
        "output_level": "L2_research_method_candidates",
    },
    {
        "family_id": "gen:research.repo-app-system-decomposer",
        "generator_class": "research_oriented",
        "target_working_primitives": 1_000_000,
        "implementation_refs": ["scripts/aidevobserver_context_foundry_loop.py"],
        "source_planes": ["github_repos", "apps", "system_designs", "architecture_docs"],
        "output_level": "L3_source_backed_system_primitives",
    },
    {
        "family_id": "gen:research.discussion-pattern-miner",
        "generator_class": "research_oriented",
        "target_working_primitives": 500_000,
        "implementation_refs": ["scripts/continuous_primitive_scrape_loop.py"],
        "source_planes": ["forums", "issue_threads", "engineering_posts", "failure_reports"],
        "output_level": "L2_pattern_candidates",
    },
    {
        "family_id": "gen:remix.graph-composition-generator",
        "generator_class": "remix_composition",
        "target_working_primitives": 1_000_000,
        "implementation_refs": ["scripts/package_linkable_primitive_cards.py"],
        "source_planes": ["edge_route_index", "input_edge_index", "output_edge_index", "mutator_chains"],
        "output_level": "L4_composed_routes",
    },
    {
        "family_id": "gen:proof.fixture-adapter-generator",
        "generator_class": "proof_oriented",
        "target_working_primitives": 750_000,
        "implementation_refs": ["scripts/verify_primitive_candidates.py", "scripts/check_primitive_registry_promotion_gate.py"],
        "source_planes": ["fixtures", "property_tests", "contract_tests", "adapter_receipts"],
        "output_level": "L4_working_with_proofs",
    },
    {
        "family_id": "gen:benchmark.trace-pair-generator",
        "generator_class": "benchmark_oriented",
        "target_working_primitives": 500_000,
        "implementation_refs": ["scripts/run_token_savings_experiments.py"],
        "source_planes": ["developer_sessions", "trace_pairs", "reuse_vs_rebuild", "token_accounting"],
        "output_level": "L4_benchmark_linked_working_candidates",
    },
    {
        "family_id": "gen:negative.failure-mode-memory-generator",
        "generator_class": "negative_memory",
        "target_working_primitives": 250_000,
        "implementation_refs": ["scripts/primitive_quality_promoter.py"],
        "source_planes": ["rejections", "duplicates", "bad_source_refs", "unsafe_effects", "failed_tests"],
        "output_level": "L3_negative_routing_primitives",
    },
)

GENERATION_PLANES = (
    "source_surface", "runtime", "language", "framework", "architecture", "design_system",
    "data_contract", "policy_overlay", "privacy_boundary", "effect_class", "receipt_shape",
    "proof_requirement", "mutator_chain", "input_edge", "output_edge", "hidden_member_edge",
    "failure_mode", "recovery_path", "benchmark_task", "developer_session", "repo_symbol",
    "api_schema", "database_schema", "ui_state", "workflow_state", "agent_role",
    "agent_primitive", "context_budget", "token_savings", "retrieval_model", "reranker",
    "extractor", "composition_graph", "route_template", "adapter_surface", "license_state",
    "source_freshness", "region", "industry", "domain_object", "human_action", "approval_gate",
    "idempotency", "pagination", "batching", "streaming", "caching", "rate_limit",
    "observability", "security", "accessibility", "localization", "simulation", "visualization",
    "data_science", "ml_eval", "paper_method", "notebook_cell", "discussion_pattern",
    "negative_memory", "promotion_blocker", "storage_partition", "search_index",
)

PROMOTION_GATES = (
    ("G0_seed_candidate", "candidate row is shaped, deterministic id attached, serves_truth=false"),
    ("G1_source_backed", "public or governed source ref resolves and license/status is attached"),
    ("G2_contract_complete", "input edge, output edge, errors, effects, and receipt contract are complete"),
    ("G3_verified_candidate", "schema validation, source policy, candidate boundary, and dedupe checks pass"),
    ("G4_linkable_card", "compact card, route indexes, reuse profile, and estimated saved tokens are packaged"),
    ("G5_working_primitive", "fixture/property/adapter proof receipts pass in at least one runtime target"),
    ("G6_benchmark_linked", "reuse-vs-rebuild trace pair or benchmark task validates retrieval and token accounting"),
)


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha(value: Any, *, n: int = 12) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:n]


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_stable_json(row) + "\n")
            count += 1
    return count


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _rel(path: Path) -> str:
    root = _repo_root()
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _latest_manifest(root: Path) -> dict[str, Any]:
    manifests = sorted(root.glob("*/manifest.json"), key=lambda p: p.stat().st_mtime if p.exists() else 0)
    return _read_json(manifests[-1]) if manifests else {}


def _aggregate_verified_manifests() -> dict[str, int]:
    totals = {
        "manifest_count": 0,
        "source_row_count": 0,
        "verified_count": 0,
        "rejected_count": 0,
        "duplicate_count": 0,
    }
    for path in VERIFIED_ROOT.glob("*/manifest.json"):
        data = _read_json(path)
        if data.get("record_type") != "primitive_candidate_verification_manifest":
            continue
        totals["manifest_count"] += 1
        for key in ("source_row_count", "verified_count", "rejected_count", "duplicate_count"):
            try:
                totals[key] += int(data.get(key) or 0)
            except (TypeError, ValueError):
                pass
    return totals


def _aggregate_million_compiler() -> dict[str, Any]:
    by_shard: dict[str, dict[str, int]] = {}
    for path in MILLION_COMPILER_ROOT.glob("**/manifest.json"):
        data = _read_json(path)
        if data.get("record_type") != "million_seed_shard_compile_manifest":
            continue
        shard = str(data.get("shard_path") or path.parent.name)
        current = by_shard.setdefault(shard, {"selected_count": 0, "verified_count": 0, "included_count": 0})
        for key in ("selected_count", "verified_count", "included_count"):
            try:
                current[key] = max(current[key], int(data.get(key) or 0))
            except (TypeError, ValueError):
                pass
    return {
        "compiled_seed_shards": len(by_shard),
        "selected_count": sum(row["selected_count"] for row in by_shard.values()),
        "verified_count": sum(row["verified_count"] for row in by_shard.values()),
        "included_count": sum(row["included_count"] for row in by_shard.values()),
    }


def _aggregate_supervised_cycles() -> dict[str, Any]:
    totals = {
        "cycle_count": 0,
        "raw_generated_seed_rows": 0,
        "raw_compiled_seed_rows": 0,
        "raw_verified_count": 0,
        "raw_linkable_card_count": 0,
        "raw_high_leverage_card_count": 0,
        "raw_estimated_saved_output_tokens_total": 0,
        "generated_seed_rows": 0,
        "compiled_seed_rows": 0,
        "verified_count": 0,
        "linkable_card_count": 0,
        "high_leverage_card_count": 0,
        "estimated_saved_output_tokens_total": 0,
        "duplicate_compiled_seed_rows": 0,
        "duplicate_linkable_card_count": 0,
        "positive_improvement_cycles": 0,
        "unique_shard_windows": 0,
    }
    seen_shards: set[tuple[int, int, int]] = set()
    for path in SUPERVISED_CYCLE_ROOT.glob("*/cycle_manifest.json"):
        data = _read_json(path)
        if data.get("record_type") != "twenty_million_supervised_cycle_manifest":
            continue
        totals["cycle_count"] += 1
        seed_manifest = data.get("seed_manifest") if isinstance(data.get("seed_manifest"), dict) else {}
        compiler_manifest = data.get("compiler_manifest") if isinstance(data.get("compiler_manifest"), dict) else {}
        compiler_totals = compiler_manifest.get("totals") if isinstance(compiler_manifest.get("totals"), dict) else {}
        improvement = data.get("improvement") if isinstance(data.get("improvement"), dict) else {}
        raw_generated = int(seed_manifest.get("total_rows") or 0)
        raw_compiled = int(compiler_totals.get("selected_count") or 0)
        raw_verified = int(compiler_totals.get("verified_count") or 0)
        raw_cards = int(improvement.get("card_count_delta") or 0)
        raw_high = int(improvement.get("high_leverage_card_delta") or 0)
        raw_saved = int(improvement.get("estimated_saved_output_tokens_delta") or 0)
        totals["raw_generated_seed_rows"] += raw_generated
        totals["raw_compiled_seed_rows"] += raw_compiled
        totals["raw_verified_count"] += raw_verified
        totals["raw_linkable_card_count"] += raw_cards
        totals["raw_high_leverage_card_count"] += raw_high
        totals["raw_estimated_saved_output_tokens_total"] += raw_saved
        rows_per_shard = max(1, int(seed_manifest.get("rows_per_shard") or DEFAULT_ROWS_PER_SHARD))
        total_rows = int(seed_manifest.get("total_rows") or 0)
        try:
            start_shard = int(compiler_manifest.get("start_shard") or 0)
            shard_count = int(compiler_manifest.get("shard_count") or 0)
        except (TypeError, ValueError):
            start_shard = 0
            shard_count = 0
        selected_shards = [(total_rows, rows_per_shard, shard) for shard in range(start_shard, start_shard + shard_count)]
        new_shards = [shard for shard in selected_shards if shard not in seen_shards]
        for shard_key in new_shards:
            seen_shards.add(shard_key)
        unique_fraction = (len(new_shards) / len(selected_shards)) if selected_shards else 0.0
        unique_compiled = round(raw_compiled * unique_fraction)
        unique_verified = round(raw_verified * unique_fraction)
        unique_cards = round(raw_cards * unique_fraction)
        unique_high = round(raw_high * unique_fraction)
        unique_saved = round(raw_saved * unique_fraction)
        totals["compiled_seed_rows"] += unique_compiled
        totals["verified_count"] += unique_verified
        totals["linkable_card_count"] += unique_cards
        totals["high_leverage_card_count"] += unique_high
        totals["estimated_saved_output_tokens_total"] += unique_saved
        totals["duplicate_compiled_seed_rows"] += raw_compiled - unique_compiled
        totals["duplicate_linkable_card_count"] += raw_cards - unique_cards
        if improvement.get("positive_improvement") is True:
            totals["positive_improvement_cycles"] += 1
    totals["generated_seed_rows"] = totals["raw_generated_seed_rows"]
    totals["unique_shard_windows"] = len(seen_shards)
    return totals


def observed_state() -> dict[str, Any]:
    million_manifest = _read_json(MILLION_BUNDLE_MANIFEST)
    linkable_manifest = _latest_manifest(LINKABLE_ROOT)
    verified = _aggregate_verified_manifests()
    million_compiler = _aggregate_million_compiler()
    supervised_cycles = _aggregate_supervised_cycles()
    return {
        "record_type": "twenty_million_observed_state",
        "created_at": _utc(),
        "million_seed_bundle": {
            "path": _rel(MILLION_BUNDLE_MANIFEST),
            "exists": MILLION_BUNDLE_MANIFEST.exists(),
            "total_rows": int(million_manifest.get("total_rows") or 0),
            "shard_count": int(million_manifest.get("shard_count") or 0),
            "rows_per_shard": int(million_manifest.get("rows_per_shard") or 0),
        },
        "million_seed_compiler": million_compiler,
        "twenty_million_supervised_cycles": supervised_cycles,
        "verified_candidates": verified,
        "linkable_cards": {
            "card_count": int(linkable_manifest.get("card_count") or 0),
            "card_count_including_20m_supervised": (
                int(linkable_manifest.get("card_count") or 0)
                + int(supervised_cycles.get("linkable_card_count") or 0)
            ),
            "high_leverage_card_count": int(linkable_manifest.get("high_leverage_card_count") or 0),
            "high_leverage_card_count_including_20m_supervised": (
                int(linkable_manifest.get("high_leverage_card_count") or 0)
                + int(supervised_cycles.get("high_leverage_card_count") or 0)
            ),
            "multistep_coding_index_count": int(linkable_manifest.get("multistep_coding_index_count") or 0),
            "estimated_saved_output_tokens_total": int(linkable_manifest.get("estimated_saved_output_tokens_total") or 0),
            "estimated_saved_output_tokens_total_including_20m_supervised": (
                int(linkable_manifest.get("estimated_saved_output_tokens_total") or 0)
                + int(supervised_cycles.get("estimated_saved_output_tokens_total") or 0)
            ),
            "manifest_path": _rel(LINKABLE_ROOT / str(linkable_manifest.get("out_dir", "")).split("/")[-1] / "manifest.json")
            if linkable_manifest.get("out_dir")
            else "",
        },
        "candidate": True,
        "serves_truth": False,
    }


def generator_family_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(GENERATOR_FAMILIES, start=1):
        target = int(row["target_working_primitives"])
        rows.append({
            **row,
            "record_type": "twenty_million_generator_family",
            "family_index": index,
            "target_candidate_rows": target * 4,
            "target_verified_candidates": target * 2,
            "target_linkable_cards": target,
            "target_working_primitives": target,
            "acceptance_gates": [gate[0] for gate in PROMOTION_GATES],
            "dedupe_namespace": _sha({"family_id": row["family_id"], "target": target}),
            "candidate": True,
            "serves_truth": False,
        })
    return rows


def generation_plane_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, plane in enumerate(GENERATION_PLANES, start=1):
        rows.append({
            "record_type": "twenty_million_generation_plane",
            "plane_id": f"plane:{plane}",
            "plane_index": index,
            "description": f"Decompose, generate, remix, and test primitives across the {plane} plane.",
            "applies_to_generator_classes": [
                "deterministic",
                "nondeterministic",
                "hybrid",
                "research_oriented",
                "remix_composition",
            ],
            "question_budget_per_source": 1200,
            "candidate": True,
            "serves_truth": False,
        })
    return rows


def promotion_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "record_type": "twenty_million_promotion_gate",
            "gate_id": gate_id,
            "gate_index": index,
            "requirement": requirement,
            "blocks_truth_claims": True,
            "candidate": True,
            "serves_truth": False,
        }
        for index, (gate_id, requirement) in enumerate(PROMOTION_GATES, start=1)
    ]


def storage_partition_rows(*, target: int, rows_per_shard: int) -> list[dict[str, Any]]:
    partition_count = math.ceil(target / rows_per_shard)
    rows: list[dict[str, Any]] = []
    for index in range(partition_count):
        start = index * rows_per_shard
        end = min(target, start + rows_per_shard)
        rows.append({
            "record_type": "twenty_million_storage_partition",
            "partition_id": f"20m:partition:{index:05d}",
            "partition_index": index,
            "start_index": start,
            "end_index_exclusive": end,
            "row_capacity": end - start,
            "seed_shard_path": f"data/dev-intel/primitive_factory/20m_goal/seed_shards/primitive_seed_shard_{index:05d}.jsonl",
            "candidate_output_dir": f"data/dev-intel/primitive_factory/20m_goal/candidate_runs/shard_{index:05d}",
            "verified_output_dir": f"data/dev-intel/primitive_factory/20m_goal/verified/shard_{index:05d}",
            "card_output_dir": f"data/dev-intel/primitive_factory/20m_goal/linkable_cards/shard_{index:05d}",
            "candidate": True,
            "serves_truth": False,
        })
    return rows


def daily_execution_rows(
    *,
    start_date: dt.date,
    horizon_days: int,
    daily_working_target: int,
    daily_candidate_target: int,
) -> list[dict[str, Any]]:
    families = generator_family_rows()
    total_target = sum(int(row["target_working_primitives"]) for row in families)
    rows: list[dict[str, Any]] = []
    for day_index in range(horizon_days):
        run_date = (start_date + dt.timedelta(days=day_index)).isoformat()
        for family in families:
            share = int(family["target_working_primitives"]) / total_target
            working = max(1, round(daily_working_target * share))
            candidates = max(working, round(daily_candidate_target * share))
            rows.append({
                "record_type": "twenty_million_daily_execution_slice",
                "run_date": run_date,
                "day_index": day_index + 1,
                "family_id": family["family_id"],
                "generator_class": family["generator_class"],
                "candidate_target": candidates,
                "verified_candidate_target": working * 2,
                "linkable_card_target": working,
                "working_primitive_target": working,
                "max_output_tokens": 65_536 if family["generator_class"] in {"nondeterministic", "hybrid", "research_oriented"} else 0,
                "model_refs": family.get("model_refs", []),
                "implementation_refs": family["implementation_refs"],
                "candidate": True,
                "serves_truth": False,
            })
    return rows


def command_lines(*, start_date: dt.date, daily_candidate_target: int) -> list[str]:
    date = start_date.isoformat()
    root = _repo_root()
    return [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"cd {root}",
        "# Deterministic 20M seed geometry. Increase --total-rows by shard plan, not by hand-edited docs.",
        (
            "python3 _repos/shared-backend-components/scripts/generate_million_primitive_seed_bundle.py "
            "--total-rows 20000000 --rows-per-shard 10000 "
            "--bundle-dir _repos/shared-backend-components/data/dev-intel/primitive_factory/20m_goal/seed_bundle "
            "--zip-path _repos/shared-backend-components/data/dev-intel/primitive_factory/20m_goal/seed_bundle.zip"
        ),
        "# Bounded deterministic compiler slice; scheduler should advance --start-shard via ledger leases.",
        (
            "python3 _repos/shared-backend-components/scripts/run_million_seed_bundle_compiler.py "
            "--bundle-root _repos/shared-backend-components/data/dev-intel/primitive_factory/20m_goal/seed_bundle "
            "--out-root _repos/shared-backend-components/data/dev-intel/primitive_factory/20m_goal/compiler_runs "
            "--start-shard 0 --shard-count 1 --verify"
        ),
        "# Model/hybrid fleet over today's 20k shard profile.",
        f"python3 _repos/shared-backend-components/scripts/build_primitive_factory_5k_shards.py --date {date} --target-profile 20k",
        (
            "python3 _repos/shared-backend-components/scripts/run_primitive_provider_fleet_loop.py "
            f"--date {date} --target-profile 20k --max-cycles 1 --scale 1 --max-tokens 65536 "
            "--run-label scheduled-20m-advanced-fleet"
        ),
        "# Research/deconstruction and benchmark loop.",
        (
            "python3 _repos/shared-backend-components/scripts/primitive_loop_json_hook.py --request-json "
            + json.dumps(json.dumps({
                "action": "flywheel.run",
                "request_id": "20m-goal-full-flywheel",
                "args": {
                    "iterations": 1,
                    "mode": "full",
                    "source_limit": 72,
                    "source_question_count": 2400,
                    "deconstruction_question_count": 3000,
                    "deconstruction_overlays_per_primitive": 16,
                    "input_context_tokens": 262144,
                    "output_context_tokens": 65536,
                    "max_token_ceiling": 65536,
                },
            }))
        ),
        f"# Daily candidate target for this plan: {daily_candidate_target}",
    ]


def build_plan(
    *,
    target: int,
    rows_per_shard: int,
    daily_working_target: int,
    daily_candidate_target: int,
    horizon_days: int,
    start_date: dt.date,
) -> dict[str, Any]:
    families = generator_family_rows()
    target_sum = sum(int(row["target_working_primitives"]) for row in families)
    if target_sum != target:
        raise AssertionError(f"generator family targets sum to {target_sum}, expected {target}")
    observed = observed_state()
    linkable_cards = int(observed["linkable_cards"]["card_count_including_20m_supervised"])
    million_verified = int(observed["million_seed_compiler"]["verified_count"])
    verified_candidates = (
        int(observed["verified_candidates"]["verified_count"])
        + int(observed["twenty_million_supervised_cycles"]["verified_count"])
    )
    current_best_working_proxy = max(linkable_cards, 0)
    remaining = max(0, target - current_best_working_proxy)
    return {
        "record_type": RECORD_TYPE,
        "created_at": _utc(),
        "target_working_primitives": target,
        "target_candidate_rows": target * 4,
        "target_verified_candidates": target * 2,
        "target_linkable_cards": target,
        "current_counts": {
            "verified_candidates": verified_candidates,
            "million_seed_verified_candidates": million_verified,
            "linkable_cards": linkable_cards,
            "working_proxy_count": current_best_working_proxy,
        },
        "remaining_working_proxy_gap": remaining,
        "rows_per_shard": rows_per_shard,
        "target_partition_count": math.ceil(target / rows_per_shard),
        "daily_working_target": daily_working_target,
        "daily_candidate_target": daily_candidate_target,
        "days_at_daily_working_target": math.ceil(remaining / daily_working_target) if daily_working_target else 0,
        "horizon_days_materialized": horizon_days,
        "generator_family_count": len(families),
        "generation_plane_count": len(GENERATION_PLANES),
        "promotion_gate_count": len(PROMOTION_GATES),
        "observed_state": observed,
        "candidate": True,
        "serves_truth": False,
    }


def run(
    *,
    out_root: Path,
    target: int,
    rows_per_shard: int,
    daily_working_target: int,
    daily_candidate_target: int,
    horizon_days: int,
    start_date: dt.date,
) -> dict[str, Any]:
    run_id = f"twenty-million-goal-{_stamp()}-{_sha({'target': target, 'start': start_date.isoformat()})}"
    run_dir = out_root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    plan = build_plan(
        target=target,
        rows_per_shard=rows_per_shard,
        daily_working_target=daily_working_target,
        daily_candidate_target=daily_candidate_target,
        horizon_days=horizon_days,
        start_date=start_date,
    )
    plan.update({
        "run_id": run_id,
        "run_dir": str(run_dir),
        "outputs": {
            "system_plan": "system_plan.json",
            "generator_families": "generator_families.jsonl",
            "generation_planes": "generation_planes.jsonl",
            "daily_execution_plan": "daily_execution_plan.jsonl",
            "storage_partitions": "storage_partitions.jsonl",
            "promotion_gates": "promotion_gates.jsonl",
            "commands": "commands.sh",
        },
    })

    _write_json(run_dir / "system_plan.json", plan)
    _write_jsonl(run_dir / "generator_families.jsonl", generator_family_rows())
    _write_jsonl(run_dir / "generation_planes.jsonl", generation_plane_rows())
    _write_jsonl(run_dir / "daily_execution_plan.jsonl", daily_execution_rows(
        start_date=start_date,
        horizon_days=horizon_days,
        daily_working_target=daily_working_target,
        daily_candidate_target=daily_candidate_target,
    ))
    _write_jsonl(run_dir / "storage_partitions.jsonl", storage_partition_rows(target=target, rows_per_shard=rows_per_shard))
    _write_jsonl(run_dir / "promotion_gates.jsonl", promotion_gate_rows())
    commands = "\n".join(command_lines(start_date=start_date, daily_candidate_target=daily_candidate_target)) + "\n"
    (run_dir / "commands.sh").write_text(commands, encoding="utf-8")
    _write_json(out_root / "latest_status.json", plan)
    return plan


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            failures.append(name)

    families = generator_family_rows()
    check("family targets sum to 20M", sum(int(row["target_working_primitives"]) for row in families) == TARGET_WORKING_PRIMITIVES)
    check("all generator classes present", {"deterministic", "nondeterministic", "hybrid", "research_oriented"} <= {str(row["generator_class"]) for row in families})
    check("candidate boundary on all family rows", all(row["candidate"] is True and row["serves_truth"] is False for row in families))
    check("promotion gates include working primitive", any(row["gate_id"] == "G5_working_primitive" for row in promotion_gate_rows()))
    check("storage partitions cover target", sum(row["row_capacity"] for row in storage_partition_rows(target=TARGET_WORKING_PRIMITIVES, rows_per_shard=DEFAULT_ROWS_PER_SHARD)) == TARGET_WORKING_PRIMITIVES)
    if failures:
        print(f"\nFAIL - 20M primitive goal plan: {len(failures)} failure(s)")
        return 1
    print("\nPASS - 20M primitive goal plan is wired.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--target", type=int, default=TARGET_WORKING_PRIMITIVES)
    parser.add_argument("--rows-per-shard", type=int, default=DEFAULT_ROWS_PER_SHARD)
    parser.add_argument("--daily-working-target", type=int, default=DEFAULT_DAILY_WORKING_TARGET)
    parser.add_argument("--daily-candidate-target", type=int, default=DEFAULT_DAILY_CANDIDATE_TARGET)
    parser.add_argument("--horizon-days", type=int, default=DEFAULT_HORIZON_DAYS)
    parser.add_argument("--start-date", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    parser.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.target <= 0:
        print("FAIL: --target must be positive", file=sys.stderr)
        return 1
    if args.rows_per_shard <= 0:
        print("FAIL: --rows-per-shard must be positive", file=sys.stderr)
        return 1
    if args.daily_working_target <= 0 or args.daily_candidate_target <= 0:
        print("FAIL: daily targets must be positive", file=sys.stderr)
        return 1
    horizon_days = max(1, min(MAX_HORIZON_DAYS, int(args.horizon_days)))
    try:
        start_date = dt.date.fromisoformat(args.start_date)
    except ValueError:
        print("FAIL: --start-date must be YYYY-MM-DD", file=sys.stderr)
        return 1
    plan = run(
        out_root=Path(args.out_root),
        target=args.target,
        rows_per_shard=args.rows_per_shard,
        daily_working_target=args.daily_working_target,
        daily_candidate_target=args.daily_candidate_target,
        horizon_days=horizon_days,
        start_date=start_date,
    )
    print(json.dumps(plan, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
