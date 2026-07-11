#!/usr/bin/env python3
"""Build the candidate plan for a billion-scale primitive system.

The output is an append-only planning bundle, not a promotion. It defines the
agents, tools, shard geometry, and benchmark gates needed to scale primitive
generation toward billions of candidates while proving token-savings claims with
measured reuse-vs-rebuild experiments.

The 90%+ reduction goal is represented as a target gate until measured. No row
serves truth.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
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

from scripts._repo_paths import resource as _resource  # noqa: E402


RECORD_TYPE = "billion_primitive_system_plan"
DEFAULT_OUT_ROOT = _resource("data") / "dev-intel" / "billion_primitive_system"
TARGET_PRIMITIVE_COUNT = 1_000_000_000
TARGET_SAVINGS_RATIO = 0.90
TARGET_MIN_MEASURED_EXPERIMENTS = 100_000
TARGET_MIN_REAL_SESSION_PAIRS = 10_000
TARGET_MIN_SOURCE_FAMILIES = 10_000
TARGET_MIN_COMPONENT_FAMILIES = 500
TARGET_MIN_EDGE_TEMPLATES = 200
TARGET_MIN_VARIATION_OVERLAYS = 100
TARGET_MIN_RUNTIME_SURFACES = 20


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha(value: Any, *, n: int = 16) -> str:
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


def _agent(
    agent_id: str,
    title: str,
    purpose: str,
    inputs: list[str],
    outputs: list[str],
    tools: list[str],
    gates: list[str],
    scale_role: str,
) -> dict[str, Any]:
    return {
        "record_type": "primitive_scale_agent_candidate",
        "agent_id": agent_id,
        "title": title,
        "purpose": purpose,
        "inputs": inputs,
        "outputs": outputs,
        "tool_refs": tools,
        "proof_gates": gates,
        "scale_role": scale_role,
        "candidate": True,
        "serves_truth": False,
    }


def build_agent_catalog() -> list[dict[str, Any]]:
    return [
        _agent(
            "agent:source-scout",
            "Source Scout",
            "Find source surfaces across papers, repos, notebooks, apps, docs, forums, and benchmark corpora.",
            ["search_surface_scope", "source_policy"],
            ["source_queue_item", "source_policy_snapshot"],
            ["tool:search-surface-expander", "tool:robots-and-license-screener"],
            ["source_policy_gate", "raw_body_exclusion_gate"],
            "acquisition",
        ),
        _agent(
            "agent:browser-runtime-captor",
            "Browser Runtime Captor",
            "Capture public UI/runtime structure into interaction maps without storing raw private session material.",
            ["url", "capture_policy"],
            ["browser_snapshot_descriptor", "interaction_map_seed"],
            ["tool:browser-capture", "tool:interaction-map-normalizer"],
            ["robots_gate", "privacy_boundary_gate"],
            "acquisition",
        ),
        _agent(
            "agent:paper-method-decomposer",
            "Paper Method Decomposer",
            "Turn licensed paper metadata and short source-backed claims into method, benchmark, and primitive seeds.",
            ["paper_metadata", "claim_summary", "license_status"],
            ["method_decomposition_seed", "benchmark_hook_seed"],
            ["tool:paper-claim-extractor", "tool:citation-graph-linker"],
            ["citation_gate", "license_review_gate"],
            "source_to_seed",
        ),
        _agent(
            "agent:question-plane-builder",
            "Question Plane Builder",
            "Expand each source into hundreds of deconstruction questions across product, code, data, cost, and proof planes.",
            ["source_snapshot", "deconstruction_plane_db"],
            ["question_answer_candidates", "gap_queue"],
            ["tool:continuous-question-bank", "tool:primitive-deconstruction-plane"],
            ["candidate_boundary_gate", "question_coverage_gate"],
            "decomposition",
        ),
        _agent(
            "agent:long-group-synthesizer",
            "Long Primitive Group Synthesizer",
            "Use model lanes such as Gemma to write fewer, larger multistep primitive groups with hidden member edges.",
            ["fully_defined_seed", "model_lane_budget"],
            ["primitive_group_candidate", "generation_receipt"],
            ["tool:gemma-long-multistep-lane", "tool:deterministic-candidate-normalizer"],
            ["candidate_boundary_gate", "group_contract_gate", "hidden_member_edge_gate"],
            "generation",
        ),
        _agent(
            "agent:kv-agent-primitive-organizer",
            "KV Agent Primitive Organizer",
            "Represent Review, Voting/Selection, Planning/Execution, Organizer, and Knowledge Pool patterns as reusable primitive groups.",
            ["task_query", "knowledge_pool", "available_primitives"],
            ["primitive_composition_plan", "latent_communication_policy"],
            ["tool:agent-primitives-paper-seed", "tool:composition-plan-emitter"],
            ["source_claim_candidate_gate", "kv_compatibility_gate", "rope_reindexing_gate"],
            "composition",
        ),
        _agent(
            "agent:small-model-context-compressor",
            "Small Model Context Compressor",
            "Use encode, score, and extract primitives to reduce downstream LLM context before expensive generation.",
            ["query", "corpus", "small_model_catalog"],
            ["ranked_context_pack", "small_model_cost_receipt"],
            ["tool:encode-score-extract-route", "tool:context-rot-benchmark"],
            ["retrieval_quality_gate", "token_budget_gate"],
            "compression",
        ),
        _agent(
            "agent:dedupe-canonicalizer",
            "Dedupe Canonicalizer",
            "Cluster near-duplicate primitive candidates by edge contract, source support, and blocking keys.",
            ["primitive_candidate_batch", "blocking_index"],
            ["canonical_candidate_batch", "duplicate_receipt"],
            ["tool:blocking-key-indexer", "tool:semantic-dedupe"],
            ["dedupe_key_gate", "source_preservation_gate"],
            "quality",
        ),
        _agent(
            "agent:token-savings-auditor",
            "Token Savings Auditor",
            "Run reuse-vs-rebuild experiments and report positive and negative savings segments honestly.",
            ["primitive_search_index", "benchmark_task_sample"],
            ["token_savings_summary", "negative_savings_segments", "gap_queue"],
            ["tool:run-token-savings-experiments", "tool:bench-token-usage"],
            ["measured_experiment_gate", "negative_segment_gate", "target_not_claim_gate"],
            "benchmark",
        ),
        _agent(
            "agent:saturation-planner",
            "Saturation Planner",
            "Detect duplicate pressure and plateaued areas, then reweight generation toward undercovered spaces.",
            ["verified_candidate_manifest", "token_savings_summary"],
            ["generation_reweight_plan", "new_frontier_queue"],
            ["tool:track-primitive-saturation", "tool:source-surface-partition-planner"],
            ["sample_size_gate", "plateau_signal_gate"],
            "planning",
        ),
        _agent(
            "agent:promotion-gatekeeper",
            "Promotion Gatekeeper",
            "Prevent candidate, benchmark, or model output rows from becoming truth without source, proof, and human review.",
            ["candidate_feed", "proof_receipts", "source_license_reviews"],
            ["promotion_decision", "promotion_blockers"],
            ["tool:verify-primitive-candidates", "tool:registry-stager"],
            ["candidate_boundary_gate", "source_license_gate", "benchmark_evidence_not_authority_gate"],
            "governance",
        ),
        _agent(
            "agent:fleet-orchestrator",
            "Fleet Orchestrator",
            "Assign disjoint shards to Gemma, Ollama GLM/Kimi, deterministic generators, validators, and benchmark workers.",
            ["scale_plan", "provider_lane_status", "work_queue"],
            ["provider_fleet_plan", "work_lease_receipts"],
            ["tool:primitive-provider-fleet-planner", "tool:gemma-rate-limiter"],
            ["lease_gate", "non_overwrite_gate", "provider_budget_gate"],
            "orchestration",
        ),
    ]


def _tool(
    tool_id: str,
    title: str,
    implementation_ref: str,
    purpose: str,
    input_edge: str,
    output_edge: str,
    agent_refs: list[str],
    proof_gates: list[str],
) -> dict[str, Any]:
    return {
        "record_type": "primitive_scale_tool_candidate",
        "tool_id": tool_id,
        "title": title,
        "implementation_ref": implementation_ref,
        "purpose": purpose,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "agent_refs": agent_refs,
        "proof_gates": proof_gates,
        "candidate": True,
        "serves_truth": False,
    }


def build_tool_catalog() -> list[dict[str, Any]]:
    return [
        _tool(
            "tool:continuous-source-loop",
            "Continuous Source Loop",
            "scripts/continuous_primitive_scrape_loop.py",
            "Scrape or metadata-snapshot sources, ask deconstruction questions, and stage candidate primitive feeds.",
            "SourceQueue+SourcePolicy",
            "SourceSnapshots+QuestionAnswers+PrimitiveDatabaseFeed",
            ["agent:source-scout", "agent:question-plane-builder"],
            ["raw_body_exclusion_gate", "candidate_boundary_gate"],
        ),
        _tool(
            "tool:primitive-deconstruction-plane",
            "Primitive Deconstruction Plane Pipeline",
            "scripts/primitive_deconstruction_plane_pipeline.py",
            "Materialize plane/layer/question databases and fully-defined candidate primitive rows.",
            "ContinuousSourceRun",
            "FullyDefinedPrimitiveCandidates+DeconstructionDatabase",
            ["agent:question-plane-builder"],
            ["plane_coverage_gate", "candidate_boundary_gate"],
        ),
        _tool(
            "tool:gemma-long-multistep-lane",
            "Gemma Long Multistep Primitive Lane",
            "scripts/run_gemma_long_multistep_primitive_lane.py",
            "Generate larger primitive_group candidates with hidden member edges through Open WebUI Gemma.",
            "FullyDefinedPrimitiveSeed+ModelBudget",
            "PrimitiveGroupCandidate+GenerationReceipt",
            ["agent:long-group-synthesizer"],
            ["group_contract_gate", "candidate_boundary_gate", "gemma_rate_limit_gate"],
        ),
        _tool(
            "tool:run-token-savings-experiments",
            "Scaled Token Savings Experiments",
            "scripts/run_token_savings_experiments.py",
            "Run thousands of reuse-vs-rebuild retrieval experiments and report where reuse saves or costs tokens.",
            "PrimitiveSearchIndex+BenchmarkSample",
            "TokenSavingsSummary+GapQueue",
            ["agent:token-savings-auditor"],
            ["measured_experiment_gate", "negative_segment_gate"],
        ),
        _tool(
            "tool:track-primitive-saturation",
            "Primitive Saturation Tracker",
            "scripts/track_primitive_saturation_and_savings.py",
            "Detect duplicate pressure, plateaued spaces, and areas where generation should diversify.",
            "VerifiedCandidateManifests+SavingsSummary",
            "SaturationReport+GenerationReweightPlan",
            ["agent:saturation-planner"],
            ["sample_size_gate", "plateau_signal_gate"],
        ),
        _tool(
            "tool:primitive-provider-fleet-planner",
            "Provider Fleet Planner",
            "scripts/plan_primitive_provider_fleet.py",
            "Plan disjoint provider windows for model and deterministic primitive generation lanes.",
            "ShardPlan+ProviderStatus",
            "DisjointProviderFleetPlan",
            ["agent:fleet-orchestrator"],
            ["non_overlap_gate", "budget_gate"],
        ),
        _tool(
            "tool:build-primitive-search-index",
            "Primitive Search Index Builder",
            "scripts/build_primitive_search_index.py",
            "Build lexical/hybrid primitive retrieval artifacts consumed by AIDevObserver and benchmarks.",
            "PrimitiveCandidateRows",
            "PrimitiveSearchIndex",
            ["agent:token-savings-auditor", "agent:dedupe-canonicalizer"],
            ["index_manifest_gate", "search_smoke_gate"],
        ),
        _tool(
            "tool:verify-primitive-candidates",
            "Primitive Candidate Verifier",
            "scripts/verify_primitive_candidates.py",
            "Reject malformed, duplicate, or promoted-truth candidate rows before registry staging.",
            "PrimitiveCandidateBatch",
            "VerifiedCandidates+RejectedRows",
            ["agent:dedupe-canonicalizer", "agent:promotion-gatekeeper"],
            ["candidate_boundary_gate", "proof_shape_gate"],
        ),
        _tool(
            "tool:agent-primitives-paper-seed",
            "Agent Primitives Paper Seed",
            "data/dev-intel/gemma_primitive_lane/source_runs/agent_primitives_and_sie_20260707",
            "Candidate source seed for Review, Voting/Selection, Planning/Execution, Organizer, Knowledge Pool, and KV-cache communication primitives.",
            "PaperMetadata+ClaimSummary",
            "LatentAgentPrimitiveSeed",
            ["agent:kv-agent-primitive-organizer"],
            ["source_claim_candidate_gate", "citation_gate"],
        ),
        _tool(
            "tool:encode-score-extract-route",
            "Encode Score Extract Route",
            "candidate_route:self_hosted_small_model_inference",
            "Represent self-hosted encode, score, and extract steps as primitives that reduce downstream LLM context.",
            "Query+Corpus+SmallModelCatalog",
            "RankedContextPack+ExtractionReceipt",
            ["agent:small-model-context-compressor"],
            ["retrieval_quality_gate", "cost_model_gate"],
        ),
    ]


def build_shard_geometry() -> dict[str, Any]:
    dimensions = {
        "source_families": TARGET_MIN_SOURCE_FAMILIES,
        "component_families": TARGET_MIN_COMPONENT_FAMILIES,
        "edge_templates": TARGET_MIN_EDGE_TEMPLATES,
        "variation_overlays": TARGET_MIN_VARIATION_OVERLAYS,
        "runtime_surfaces": TARGET_MIN_RUNTIME_SURFACES,
    }
    capacity = 1
    for value in dimensions.values():
        capacity *= value
    return {
        "record_type": "primitive_scale_shard_geometry",
        "target_primitive_count": TARGET_PRIMITIVE_COUNT,
        "candidate_capacity": capacity,
        "capacity_meets_target": capacity >= TARGET_PRIMITIVE_COUNT,
        "dimensions": dimensions,
        "shard_key_order": [
            "source_family",
            "component_family",
            "visible_input_edge",
            "visible_output_edge",
            "variation_overlay",
            "runtime_surface",
        ],
        "append_only_storage_policy": "write run directories and stage feeds; do not overwrite registry truth",
        "candidate": True,
        "serves_truth": False,
    }


def build_workstream_shards() -> list[dict[str, Any]]:
    workstreams = [
        ("source_acquisition", "agent:source-scout", 10_000, "source surfaces"),
        ("deconstruction", "agent:question-plane-builder", 100_000, "source x plane question batches"),
        ("long_group_generation", "agent:long-group-synthesizer", 1_000_000, "large primitive-group seeds"),
        ("kv_agent_primitives", "agent:kv-agent-primitive-organizer", 50_000, "latent agent composition patterns"),
        ("small_model_compression", "agent:small-model-context-compressor", 50_000, "encode/score/extract routes"),
        ("dedupe_and_canonicalization", "agent:dedupe-canonicalizer", 1_000_000, "candidate batches"),
        ("token_savings_benchmark", "agent:token-savings-auditor", TARGET_MIN_MEASURED_EXPERIMENTS, "reuse-vs-rebuild trials"),
        ("real_session_benchmark", "agent:token-savings-auditor", TARGET_MIN_REAL_SESSION_PAIRS, "real developer trace pairs"),
        ("saturation_planning", "agent:saturation-planner", 10_000, "area saturation buckets"),
        ("promotion_review", "agent:promotion-gatekeeper", 100_000, "promotion packets"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (name, agent_id, planned_units, unit_kind) in enumerate(workstreams, start=1):
        rows.append(
            {
                "record_type": "primitive_scale_workstream_shard",
                "workstream_id": f"workstream:{name}",
                "ordinal": index,
                "agent_id": agent_id,
                "planned_units": planned_units,
                "unit_kind": unit_kind,
                "lease_policy": "append_only_idempotent_shards",
                "output_policy": "candidate_only_no_truth_promotion",
                "candidate": True,
                "serves_truth": False,
            }
        )
    return rows


def build_benchmark_gates() -> list[dict[str, Any]]:
    gates = [
        (
            "gate:target-90-not-claimed",
            "90 percent savings remains a target until measured",
            "summary.claimed_savings_ratio is absent unless measured_experiment_count and real_session_pairs pass thresholds",
        ),
        (
            "gate:reuse-vs-rebuild-net-positive",
            "Reuse must beat rebuild after search cost",
            "avg_net_saved_tokens > 0 and negative_savings_segments are reported",
        ),
        (
            "gate:p90-token-reduction-target",
            "P90 eligible tasks should approach the 90 percent reduction target",
            f"p90_measured_savings_ratio >= {TARGET_SAVINGS_RATIO}",
        ),
        (
            "gate:real-session-pair-count",
            "Real developer sessions must be sampled before fleet claims",
            f"real_session_pairs >= {TARGET_MIN_REAL_SESSION_PAIRS}",
        ),
        (
            "gate:experiment-count",
            "Scaled deterministic experiments must precede claims",
            f"measured_experiments >= {TARGET_MIN_MEASURED_EXPERIMENTS}",
        ),
        (
            "gate:accuracy-non-regression",
            "Token reduction cannot degrade task quality",
            "primitive_arm_accuracy >= baseline_accuracy - allowed_delta",
        ),
        (
            "gate:latency-budget",
            "Primitive lookup and composition must not erase savings",
            "lookup_latency + composition_latency is within configured budget",
        ),
        (
            "gate:source-license-proof",
            "Source-backed primitive promotion requires source and license review",
            "all promoted rows have reviewed source_refs and license_status",
        ),
        (
            "gate:candidate-boundary",
            "Generated rows remain candidates until promotion review",
            "candidate is true and serves_truth is false for generated feeds",
        ),
        (
            "gate:benchmark-evidence-not-authority",
            "Benchmarks inform but do not promote",
            "benchmark result cannot flip serves_truth",
        ),
    ]
    return [
        {
            "record_type": "primitive_scale_benchmark_gate",
            "gate_id": gate_id,
            "title": title,
            "condition": condition,
            "candidate": True,
            "serves_truth": False,
        }
        for gate_id, title, condition in gates
    ]


def build_system_plan(run_id: str, run_dir: Path) -> dict[str, Any]:
    agents = build_agent_catalog()
    tools = build_tool_catalog()
    geometry = build_shard_geometry()
    workstreams = build_workstream_shards()
    gates = build_benchmark_gates()
    return {
        "record_type": RECORD_TYPE,
        "run_id": run_id,
        "created_at": _utc(),
        "run_dir": str(run_dir),
        "target_primitive_count": TARGET_PRIMITIVE_COUNT,
        "target_savings_ratio": TARGET_SAVINGS_RATIO,
        "target_savings_is_claim": False,
        "minimum_measured_experiments_before_claim": TARGET_MIN_MEASURED_EXPERIMENTS,
        "minimum_real_session_pairs_before_claim": TARGET_MIN_REAL_SESSION_PAIRS,
        "agent_count": len(agents),
        "tool_count": len(tools),
        "workstream_count": len(workstreams),
        "benchmark_gate_count": len(gates),
        "candidate_capacity": geometry["candidate_capacity"],
        "capacity_meets_target": geometry["capacity_meets_target"],
        "architecture_thesis": {
            "primitive_reuse": "replace repeated long task-specific instructions with compact edge contracts and primitive references",
            "agent_primitives": "represent Review, Voting/Selection, Planning/Execution, Organizer, and Knowledge Pool as composable primitive groups",
            "small_model_context_reduction": "use local encode/score/extract routes to reduce context before expensive LLM calls",
            "measurement": "prove savings through reuse-vs-rebuild experiments and real developer trace pairs",
        },
        "outputs": {
            "agents": "agents.jsonl",
            "tools": "tools.jsonl",
            "shard_geometry": "shard_geometry.json",
            "workstream_shards": "workstream_shards.jsonl",
            "benchmark_gates": "benchmark_gates.jsonl",
            "system_plan": "system_plan.json",
        },
        "candidate": True,
        "serves_truth": False,
    }


def run(output_root: Path) -> dict[str, Any]:
    run_id = f"billion-primitive-system-plan-{_stamp()}-{_sha(_utc(), n=8)}"
    run_dir = output_root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    agents = build_agent_catalog()
    tools = build_tool_catalog()
    geometry = build_shard_geometry()
    workstreams = build_workstream_shards()
    gates = build_benchmark_gates()
    plan = build_system_plan(run_id, run_dir)
    _write_jsonl(run_dir / "agents.jsonl", agents)
    _write_jsonl(run_dir / "tools.jsonl", tools)
    _write_json(run_dir / "shard_geometry.json", geometry)
    _write_jsonl(run_dir / "workstream_shards.jsonl", workstreams)
    _write_jsonl(run_dir / "benchmark_gates.jsonl", gates)
    _write_json(run_dir / "system_plan.json", plan)
    _write_json(output_root / "latest_status.json", plan)
    return plan


def _assert_candidate_rows(path: Path) -> None:
    for jsonl in path.rglob("*.jsonl"):
        for line_no, line in enumerate(jsonl.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("candidate") is not True:
                raise AssertionError(f"{jsonl}:{line_no}: candidate must be true")
            if row.get("serves_truth") is not False:
                raise AssertionError(f"{jsonl}:{line_no}: serves_truth must be false")


def _self_test() -> int:
    agents = build_agent_catalog()
    tools = build_tool_catalog()
    geometry = build_shard_geometry()
    gates = build_benchmark_gates()
    assert geometry["candidate_capacity"] >= TARGET_PRIMITIVE_COUNT
    assert any(agent["agent_id"] == "agent:kv-agent-primitive-organizer" for agent in agents)
    assert any(agent["agent_id"] == "agent:token-savings-auditor" for agent in agents)
    assert any(tool["tool_id"] == "tool:gemma-long-multistep-lane" for tool in tools)
    assert any(tool["tool_id"] == "tool:run-token-savings-experiments" for tool in tools)
    assert any(gate["gate_id"] == "gate:target-90-not-claimed" for gate in gates)
    temp_root = _resource("data") / "dev-intel" / "billion_primitive_system_self_test"
    if temp_root.exists():
        # Leave old append-only runs alone; test only writes a new run.
        pass
    plan = run(temp_root)
    _assert_candidate_rows(Path(plan["run_dir"]))
    assert plan["target_savings_is_claim"] is False
    print("PASS - billion primitive system plan emits candidate-only agents, tools, shard geometry, and benchmark gates.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.run:
        parser.error("pass --run or --self-test")
    plan = run(Path(args.out_root))
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
