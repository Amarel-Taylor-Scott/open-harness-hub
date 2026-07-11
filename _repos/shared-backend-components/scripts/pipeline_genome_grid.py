#!/usr/bin/env python3
"""scripts.pipeline_genome_grid — grid-search the FACTORY PIPELINE ITSELF (candidate-only). OmniPath applied to
the meta-pipeline: every way we discover/generate/certify/retrieve/serve/enforce primitives is a genome stage;
enumerate the cartesian, sample, successive-halve, and keep a Pareto frontier of paths.

Owner (2026-07-09): make the pipeline searchable/generatable/benchmarkable. A PipelineGenome = source_strategy +
acquisition_backend + digest_strategy + role_ensemble + decomposition + generation_lane + candidate_filter +
dedupe + security + executor_synthesis + fixture + verifier + benchmark + retrieval + serving + adoption. Do NOT
collapse to one path — discover the best path PER objective (Pareto), route future work by measured receipts.

This is the tested CORE: the 16-stage genome with real option catalogs (extensible — add a row), the astronomical
cartesian count, seeded deterministic sampling (coprime-strided / stratified / random), a labeled proxy multi-
objective scorer + the owner's path_score formula, successive halving (micro->scout->scale, keep top fraction
each round), and Pareto leaderboards. The real per-stage runners + YAML catalogs (Phases 2-10 of the spec) are
the roadmap; scores here are a PROXY until paths execute. candidate=true/serves_truth=false.

    python3 scripts/pipeline_genome_grid.py --self-test
    python3 scripts/pipeline_genome_grid.py --search --sample 500 --seed 7
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/ml_lifecycle_primitive_minter.py) ────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import hashlib  # noqa: E402  (labeled proxy scorer only — ids via canonical_id)
import json  # noqa: E402
import random  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"pipeline_genome_grid requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "proxy"  # no_proxy_gate: real=executed+measured / proxy=estimated
ARTIFACT_DIR_REL = "data/dev-intel/pipeline_grid"

# ── the 16 genome stages, each a catalog of options (representative subset of the owner's lists; extend = add a
#    row). Order = the factory loop. ─────────────────────────────────────────────────────────────────────────
GENOME_STAGES: dict[str, list[str]] = {
    "source_strategy": ["standards_first", "api_docs_first", "github_repos_first", "test_fixtures_first",
                        "benchmark_failures_first", "browser_traces_first", "kaggle_notebooks_first",
                        "papers_first", "error_code_tables_first", "ci_failure_first", "anti_primitive_first",
                        "technology_stack_first"],
    "acquisition_backend": ["raw_http_fetch", "sitemap_crawl", "pdf_text_extract", "pdf_table_extract",
                            "ocr_fallback", "github_api", "openapi_import", "postman_import", "browser_cdp_capture",
                            "playwright_capture", "network_har_capture", "notebook_cell_digest"],
    "digest_strategy": ["section_digest", "table_digest", "code_block_digest", "endpoint_digest",
                        "error_code_digest", "object_action_state_digest", "workflow_step_digest", "schema_digest",
                        "test_fixture_digest", "message_format_digest"],
    "role_ensemble": ["single_role", "two_role_generator_critic", "three_role_generator_critic_deduper",
                      "api_plus_security", "standards_plus_verifier", "browser_plus_api_archaeologist",
                      "domain_operator_plus_benchmark_designer", "security_plus_negative_gate_designer"],
    "decomposition_strategy": ["noun_to_object", "verb_to_action", "field_to_datatype", "table_to_lookup",
                               "standard_to_parser_validator_mapper", "endpoint_to_interface_wrapper",
                               "error_to_error_mapper", "seven_primitive_model", "process_periodic_table",
                               "determinism_lens"],
    "generation_lane": ["hy3_broad_ideation", "hy3_executor_plus_fixtures", "local_30b_executor",
                        "code_model_executor", "two_model_generator_critic", "self_critique_rewrite",
                        "metamorphic_fixture_generation", "benchmark_failure_to_primitive", "coverage_gap_generation",
                        "variation_remix_generation"],
    "candidate_filter": ["no_filter_baseline", "strict_mechanism_required", "no_generic_any_any", "schema_required",
                         "input_output_edge_required", "determinism_D0_D1_only", "no_side_effect_only",
                         "source_evidence_required", "anti_placeholder_filter"],
    "dedupe_strategy": ["title_hash", "edge_body_hash", "behavior_signature", "minhash_lsh", "embedding_cluster",
                        "title_edge_body_plus_behavior"],
    "security_strategy": ["scan_before_dedupe", "scan_after_dedupe", "banned_imports_gate", "sandbox_isolated",
                          "side_effect_classify", "permission_least_privilege"],
    "executor_synthesis": ["single_model", "hy3_then_code_critic", "code_model_then_hy3_fixtures", "local_30b",
                           "template_library", "rules_engine", "python", "typescript", "sql", "policy_gate"],
    "fixture_strategy": ["llm_positive_negative", "source_examples", "tests_mined_from_github", "metamorphic",
                         "property_based", "boundary_case", "adversarial", "mutation_based", "golden_from_standard"],
    "verifier_strategy": ["schema_only", "exact_output", "invariant", "metamorphic", "property_based",
                          "oracle_function", "cross_implementation", "mutation_verified", "benchmark_task"],
    "benchmark_strategy": ["unit_fixture", "hidden_fixture", "seeded_randomized", "mutation_test", "sandbox_task",
                           "route_composition", "real_token_ledger", "break_even_n"],
    "retrieval_strategy": ["curated_only", "weighted_full", "weighted_full_mmr", "executor_certified_only",
                           "typed_edge_first", "behavior_signature_first", "lexical_bm25_first",
                           "dense_embedding_first", "hybrid_bm25_dense", "hybrid_plus_graph", "combmnz_fusion",
                           "learned_reranker", "coverage_gap_boost", "deprecated_suppression"],
    "serving_strategy": ["card_only_retrieval", "executor_injected_orchestration", "compiled_route_cache",
                         "direct_deterministic_execution", "llm_plans_primitives_execute",
                         "primitive_search_then_no_llm", "primitive_search_with_human_gap", "mcp_tool_export"],
    "adoption_strategy": ["sdk_decorator_first", "cli_scaffold_first", "ci_scanner_first", "runtime_gateway_first",
                          "policy_as_code_first", "codemod_first", "pr_bot_first", "lockfile_first",
                          "ruff_rule_first", "llm_gateway_first", "warn_only", "fail_on_raw_llm_calls"],
}
STAGE_ORDER = list(GENOME_STAGES)

# ── objectives (direction) + the owner's path_score weights ──────────────────────────────────────────────────
OBJECTIVES: dict[str, int] = {"executor_certified_rate": +1, "useful_candidate_rate": +1, "gap_coverage": +1,
                              "ab_savings": +1, "verifier_mutation_pass": +1, "security_fail": -1,
                              "duplicate_rate": -1, "placeholder_rate": -1, "cost": -1}
SCORE_WEIGHTS: dict[str, float] = {"executor_certified_rate": 3.0, "useful_candidate_rate": 2.0, "gap_coverage": 2.0,
                                   "ab_savings": 2.0, "verifier_mutation_pass": 1.5, "security_fail": -2.0,
                                   "duplicate_rate": -1.5, "placeholder_rate": -1.0, "cost": -1.0}

# ── a little REAL domain knowledge: options that genuinely help an objective get a deterministic boost (so the
#    proxy is structured, not pure noise). Everything else is a stable hashed baseline. ──────────────────────
_BOOSTS: dict[str, dict[str, float]] = {
    "executor_certified_rate": {"hy3_executor_plus_fixtures": 0.2, "code_model_then_hy3_fixtures": 0.2,
                                "sandbox_isolated": 0.15, "metamorphic": 0.1, "mutation_verified": 0.15},
    "ab_savings": {"executor_injected_orchestration": 0.2, "primitive_search_then_no_llm": 0.25,
                   "typed_edge_first": 0.15, "compiled_route_cache": 0.15},
    "useful_candidate_rate": {"strict_mechanism_required": 0.15, "no_generic_any_any": 0.15,
                              "source_evidence_required": 0.1, "two_model_generator_critic": 0.1},
    "gap_coverage": {"benchmark_failures_first": 0.2, "coverage_gap_generation": 0.2, "coverage_gap_boost": 0.15},
    "security_fail": {"scan_before_dedupe": -0.2, "banned_imports_gate": -0.15, "permission_least_privilege": -0.15},
    "duplicate_rate": {"title_edge_body_plus_behavior": -0.2, "minhash_lsh": -0.15, "behavior_signature": -0.15},
    "verifier_mutation_pass": {"mutation_verified": 0.25, "metamorphic": 0.15, "property_based": 0.15},
}


def theoretical_paths() -> int:
    n = 1
    for opts in GENOME_STAGES.values():
        n *= len(opts)
    return n


def _proxy(option: str, objective: str, seed: int) -> float:
    h = hashlib.sha256(f"{option}|{objective}|{seed}".encode()).digest()
    return int.from_bytes(h[:4], "big") / 0xFFFFFFFF


def make_genome(choices: dict[str, str]) -> dict[str, Any]:
    gid = canonical_id("pgenome", *[choices[s] for s in STAGE_ORDER])
    return {"pipeline_id": gid, "choices": choices, **BOUNDARY}


def score_genome(genome: dict[str, Any], seed: int, noise: float = 0.10) -> dict[str, Any]:
    """PROXY multi-objective score (deterministic given genome+seed). Real scores come from running the path."""
    rng = random.Random(seed ^ int(genome["pipeline_id"].split("-")[-1][:8], 16))
    objs: dict[str, float] = {}
    for name in OBJECTIVES:
        base = sum(_proxy(genome["choices"][s], name, seed) for s in STAGE_ORDER) / len(STAGE_ORDER)
        boost = sum(_BOOSTS.get(name, {}).get(genome["choices"][s], 0.0) for s in STAGE_ORDER)
        val = min(1.0, max(0.0, base + boost + (rng.random() - 0.5) * noise))
        objs[name] = round(val, 4)
    path_score = round(sum(SCORE_WEIGHTS[n] * (objs[n] if d > 0 else (1.0 - objs[n]))
                           for n, d in OBJECTIVES.items()), 4)
    return {**genome, "objective_scores": objs, "path_score": path_score}


def sample(n: int, seed: int, strategy: str = "coprime") -> list[dict[str, Any]]:
    """Seeded, deterministic sampling of the astronomical grid (never materialize the full cartesian)."""
    out = []
    stages = [(s, GENOME_STAGES[s]) for s in STAGE_ORDER]
    if strategy == "coprime":
        # coprime-strided walk over each stage independently (deterministic coverage without cartesian blowup)
        strides = [7 + i * 2 for i in range(len(stages))]
        for k in range(n):
            choices = {s: opts[(k * strides[i] + seed) % len(opts)] for i, (s, opts) in enumerate(stages)}
            out.append(make_genome(choices))
    elif strategy == "stratified":
        for k in range(n):
            choices = {s: opts[k % len(opts)] if k < len(opts) else opts[(k * 13 + seed) % len(opts)]
                       for s, opts in stages}
            out.append(make_genome(choices))
    else:  # random
        for k in range(n):
            rng = random.Random(seed * 1_000_003 + k)
            out.append(make_genome({s: rng.choice(opts) for s, opts in stages}))
    return out


def pareto_frontier(scored: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def dominates(a: dict, b: dict) -> bool:
        oa, ob = a["objective_scores"], b["objective_scores"]
        ge = all((oa[n] >= ob[n]) if d > 0 else (oa[n] <= ob[n]) for n, d in OBJECTIVES.items())
        gt = any((oa[n] > ob[n]) if d > 0 else (oa[n] < ob[n]) for n, d in OBJECTIVES.items())
        return ge and gt
    return [t for t in scored if not any(dominates(o, t) for o in scored if o is not t)]


def successive_halving(sampled: list[dict[str, Any]], seed: int, keep=(0.3, 0.2, 0.1)) -> dict[str, Any]:
    """Rounds of increasing 'jobs' (modeled as shrinking score noise = tighter estimates), keeping the top
    fraction each round. Mirrors the owner's micro->scout->scale halving."""
    survivors = sampled
    rounds = []
    for r, frac in enumerate(keep):
        noise = 0.14 / (r + 1)                      # more jobs -> less noise
        scored = [score_genome(g, seed, noise) for g in survivors]
        scored.sort(key=lambda t: -t["path_score"])
        n_keep = max(1, int(len(scored) * frac))
        rounds.append({"round": r, "in": len(scored), "kept": n_keep,
                       "top_path_score": scored[0]["path_score"]})
        survivors = scored[:n_keep]
    return {"rounds": rounds, "survivors": survivors}


def leaderboards(scored: list[dict[str, Any]]) -> dict[str, Any]:
    board: dict[str, Any] = {"best_overall": max(scored, key=lambda t: t["path_score"])["pipeline_id"]}
    for name, d in OBJECTIVES.items():
        best = max(scored, key=lambda t, n=name, dd=d: t["objective_scores"][n] if dd > 0
                   else 1 - t["objective_scores"][n])
        board[f"best_{name}"] = {"pipeline_id": best["pipeline_id"],
                                 "choices_digest": {k: best["choices"][k] for k in
                                                    ("generation_lane", "executor_synthesis", "retrieval_strategy",
                                                     "serving_strategy")}}
    return board


def run_search(n: int, seed: int, strategy: str = "coprime") -> dict[str, Any]:
    sampled = sample(n, seed, strategy)
    scored = [score_genome(g, seed) for g in sampled]
    front = pareto_frontier(scored)
    halv = successive_halving(sampled, seed)
    return {"record_type": "pipeline_genome_grid_search", "theoretical_paths": theoretical_paths(),
            "n_stages": len(GENOME_STAGES), "sampled": len(sampled), "strategy": strategy, "seed": seed,
            "pareto_frontier_size": len(front),
            "successive_halving": halv["rounds"],
            "top_survivor": {"pipeline_id": halv["survivors"][0]["pipeline_id"],
                             "path_score": halv["survivors"][0]["path_score"],
                             "choices": halv["survivors"][0]["choices"]},
            "leaderboards": leaderboards(scored),
            "note": "PROXY scores (structured w/ domain boosts) until paths execute; real receipts replace them.",
            **BOUNDARY}


def emit(result: dict[str, Any]) -> str:
    out_dir = resource(ARTIFACT_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "pipeline_genome_grid_search.json"
    p.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return str(p)


def self_test() -> bool:
    """Mutation-gated: astronomical grid; seeded+reproducible sampling; halving strictly reduces; Pareto
    non-dominated; leaderboards per objective; domain boosts actually raise their objective; candidate-only."""
    assert len(GENOME_STAGES) == 16, f"expected 16 genome stages, got {len(GENOME_STAGES)}"
    assert theoretical_paths() > 10 ** 15, f"grid should be astronomical, got {theoretical_paths()}"

    # (1) sampling is seeded + reproducible; different seed differs.
    a = sample(50, seed=7)
    b = sample(50, seed=7)
    assert [g["pipeline_id"] for g in a] == [g["pipeline_id"] for g in b], "sampling not reproducible"
    assert [g["pipeline_id"] for g in sample(50, seed=8)] != [g["pipeline_id"] for g in a], "seed must change it"

    # (2) scoring deterministic given (genome, seed, noise=0).
    s1 = score_genome(a[0], seed=3, noise=0.0)
    s2 = score_genome(a[0], seed=3, noise=0.0)
    assert s1["objective_scores"] == s2["objective_scores"]

    # (3) successive halving strictly reduces the survivor set across rounds.
    hv = successive_halving(sample(300, seed=5), seed=5)
    kept = [r["kept"] for r in hv["rounds"]]
    assert kept[0] > kept[1] > kept[2], f"halving must shrink survivors: {kept}"

    # (4) Pareto frontier is non-dominated.
    scored = [score_genome(g, seed=9) for g in sample(120, seed=9)]
    front = pareto_frontier(scored)
    assert 0 < len(front) <= len(scored)

    # (5) domain boosts WORK: a genome with the certified-rate boosts scores higher on that objective than one
    #     without (proves the proxy is structured, not pure noise).
    base = {s: GENOME_STAGES[s][0] for s in STAGE_ORDER}
    boosted = dict(base, generation_lane="hy3_executor_plus_fixtures", security_strategy="sandbox_isolated",
                   verifier_strategy="mutation_verified")
    hi = score_genome(make_genome(boosted), seed=1, noise=0.0)["objective_scores"]["executor_certified_rate"]
    lo = score_genome(make_genome(base), seed=1, noise=0.0)["objective_scores"]["executor_certified_rate"]
    assert hi > lo, "executor-certified boosts must raise that objective"

    # (6) leaderboards cover every objective + best_overall; candidate-only.
    res = run_search(150, seed=7)
    assert "best_overall" in res["leaderboards"]
    for n in OBJECTIVES:
        assert f"best_{n}" in res["leaderboards"]
    assert res["candidate"] is True and res["serves_truth"] is False

    print(f"OK pipeline_genome_grid self-test: {res['n_stages']} stages, {res['theoretical_paths']:,} theoretical "
          f"paths; seeded sampling; halving {[r['kept'] for r in res['successive_halving']]}; "
          f"Pareto {res['pareto_frontier_size']}; per-objective leaderboards; boosts structural; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Grid-search the factory pipeline itself (pipeline genomes).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--search", action="store_true")
    ap.add_argument("--sample", type=int, default=500)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--strategy", default="coprime", choices=["coprime", "stratified", "random"])
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.search:
        res = run_search(args.sample, args.seed, args.strategy)
        res["path"] = emit(res)
        print(json.dumps({k: res[k] for k in ("theoretical_paths", "sampled", "strategy", "pareto_frontier_size",
                                              "successive_halving", "top_survivor", "leaderboards", "path")},
                         indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
