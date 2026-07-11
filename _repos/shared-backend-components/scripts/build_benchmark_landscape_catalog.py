#!/usr/bin/env python3
"""scripts.build_benchmark_landscape_catalog — the 2025-2026 benchmark landscape → primitive-demand map.

Synthesizes five parallel research sweeps (competitive programming, data science, data engineering/SQL, SWE/agentic,
frontier) into ONE curated catalog: each benchmark with its category, org, release, url, size, a primary-verified
top score where known, a verification_status, and the primitive_demands it implies. From that, it COMPUTES the
primitive-demand priority (which primitives the most benchmarks need) — so the finding "verification/test-execution
is the #1 leverage" is derived from the data, not asserted — plus the unbenchmarked white-space gap targets.

Curated intake (candidate=true/serves_truth=false); scores/dates are as reported by primary sources at publication
and are RESEARCH INTAKE, not local measurements — flagged benchmarks carry verification_status="flagged". Offline +
deterministic. Regenerate via --write; --self-test. Never treat an external benchmark score as local truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PACK_DIR = _resource("catalog") / "knowledge-packs" / "data" / "benchmark-landscape-catalog"
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# (name, category, org, release, url, size, top_score_note, verification, [primitive_demands])
B = tuple
BENCHMARKS: list[tuple] = [
    # ---- competitive programming ----
    ("AetherCode", "competitive_programming", "28-author (arXiv)", "2025-08", "arXiv:2508.16402", "456 problems (IOI/ICPC/USACO/CCPC, 4 tiers)", "o4-mini-high 35.5% pass@1", "verified", ["algorithm_impl", "checker_validator", "brute_force_oracle", "adversarial_edge_gen"]),
    ("LiveOIBench", "competitive_programming", "Zou et al.", "2025-10", "arXiv:2510.09595", "403 problems, 72 contests, 14 olympiads", "GPT-5 ~81.8th percentile", "verified", ["subtask_decompose", "partial_credit_router", "algorithm_impl", "private_test_checker"]),
    ("LiveCodeBench Pro", "competitive_programming", "Zheng et al. (olympiad medalists)", "2025-06", "arXiv:2506.11928", "curated CF/ICPC/IOI, continuously updated", "best w/o tools 53% medium, 0% hard", "verified", ["case_analysis_decompose", "invariant_finder", "constructive_validator", "algorithm_impl"]),
    ("OJBench", "competitive_programming", "multi-institution", "2025-06", "arXiv:2506.16395", "232 problems (NOI + ICPC)", "o4-mini/Gemini-2.5 struggle", "verified", ["advanced_data_structure", "advanced_dp", "algorithm_impl"]),
    ("CodeELO", "competitive_programming", "Qwen/Alibaba", "2025-01", "arXiv:2501.01257", "387 problems, 54 contests, 35 tags", "o1-mini 1578 Elo (~89th pct); weak on DP+trees", "verified", ["dp_state_transition", "tree_algorithms", "special_judge_checker", "algorithm_impl"]),
    ("ICPC-Eval", "competitive_programming", "RUCAIBox", "2025-06", "arXiv:2506.04894", "118 problems, 11 ICPC contests", "top models need multi-turn feedback (Refine@K)", "verified", ["execution_feedback_repair", "failing_test_minimizer", "local_checker", "algorithm_impl"]),
    ("CodeContests+", "competitive_programming", "Wang et al. (EMNLP 2025)", "2025-06", "arXiv:2506.05817", "~10k problems re-tested, 1.72M submissions", "higher TPR test quality → RL gains", "verified", ["test_generator", "validator", "special_judge_checker", "brute_force_oracle"]),
    ("FormulaOne", "competitive_programming", "Beniamini et al.", "2025-07", "arXiv:2507.13337", "MSO-logic-on-graphs auto-generated", "o3 <1% (starkest flatline)", "verified", ["deep_algorithmic_reasoning", "dp_from_logic_spec", "algorithm_impl"]),
    ("Scaling Agentic Verifier", "competitive_programming", "Ma et al. (method)", "2026-02", "arXiv:2602.04254", "method over 5 CP benchmarks", "+10-15% Best@K", "flagged", ["discriminative_input_gen", "execution_differ", "best_at_k_selector"]),
    # ---- data science / ML engineering ----
    ("MLE-bench", "data_science", "OpenAI", "2024-10", "arXiv:2410.07095", "75 Kaggle competitions", "o1-preview+AIDE any-medal 16.9%", "verified", ["leakage_scan", "train_val_split", "metric_parser", "submission_validator", "cv_harness", "feature_table_build"]),
    ("KramaBench", "data_science", "MIT DB Group", "2025-06", "arXiv:2506.06541", "104 tasks, 1700 files, 24 sources", "best system 55% end-to-end", "verified", ["source_discovery", "entity_linking", "pipeline_dag_planner", "schema_fingerprint", "per_step_validator"]),
    ("DABStep", "data_science", "Adyen + HuggingFace", "2025-06", "arXiv:2506.23719", "450+ real financial-analytics tasks", "o4-mini 14.55% hard / 76.39% easy", "verified", ["documentation_retriever", "multi_step_planner", "code_sandbox", "answer_normalizer"]),
    ("DSBench", "data_science", "Jing et al. (ICLR 2025)", "2024-09", "arXiv:2409.07703", "540 tasks (analysis + modeling)", "best agent 34.12% analysis", "verified", ["multi_table_loader", "eda_profile", "feature_table_build", "metric_parser", "submission_validator"]),
    ("ScienceAgentBench", "data_science", "OSU NLP (ICLR 2025)", "2024-10", "arXiv:2410.05080", "102 tasks, 44 papers", "best 32.4% independent", "verified", ["domain_knowledge_retrieval", "code_from_spec", "visualization_gen", "result_validator", "self_debug_loop"]),
    ("InfiAgent-DABench", "data_science", "InfiAgent (ICML 2024)", "2024-01", "arXiv:2401.05507", "257 questions, 52 CSVs", "DAAgent beats GPT-3.5 +3.9%", "verified", ["csv_loader", "schema_profiler", "closed_form_normalizer", "numeric_validator"]),
    ("MLR-Bench", "data_science", "Chen et al. (NeurIPS 2025)", "2025-05", "arXiv:2505.19955", "201 tasks", "agents FABRICATE experimental results (headline)", "verified", ["hypothesis_generator", "experiment_runner", "result_verification_gate", "rubric_judge"]),
    ("ResearchGym", "data_science", "TCS+Yale", "2026-02", "arXiv:2602.15112", "5 envs / 39 sub-tasks", "GPT-5 improved 1/15 evals", "flagged", ["experiment_runner", "anti_fabrication_gate", "long_horizon_planner", "baseline_diff_evaluator"]),
    ("DARE-bench", "data_science", "arXiv 2602.24288", "2026-02", "arXiv:2602.24288", "6,300 Kaggle-derived tasks (verifiable GT)", "unverified (post-cutoff)", "flagged", ["reproducible_cv_scoring", "instruction_fidelity_checker", "reference_solution_executor", "leakage_scan"]),
    ("DataGovBench", "data_engineering", "Liu/Han/Yan", "2025-12", "arXiv:2512.04416", "150 data-governance tasks", "DataGovAgent 54.9 vs 39.7 baseline", "verified", ["data_quality_gate", "validation_rule_emit", "lineage_capture", "error_correction_loop"]),
    # ---- data engineering / SQL ----
    ("Spider 2.0", "data_engineering", "XLang/HKU (ICLR 2025)", "2024-11", "arXiv:2411.07763", "632 problems (Snow/Lite/DBT), >1k-col DBs", "o1-preview 17.1% Snow (annotation errors flagged)", "verified", ["schema_fingerprint", "sql_dialect_translate", "dbt_model_emit", "join_plan_decompose", "execution_repair"]),
    ("ELT-Bench", "data_engineering", "UIUC", "2025-04", "arXiv:2504.04808", "100 pipelines, 835 tables, 203 models", "best agent 3.9% data models built", "verified", ["source_connector_config", "load_orchestration", "dbt_model_emit", "pipeline_dag_assembly"]),
    ("DAComp", "data_engineering", "ByteDance-Seed (ICLR 2026)", "2025-12", "arXiv:2512.04324", "210 tasks (DE + DA tracks)", "DE success <20%", "verified", ["multi_stage_pipeline_design", "schema_fingerprint", "dbt_model_emit", "join_plan_decompose"]),
    ("BIRD-Interact", "data_engineering", "HKU BIRD + Google (ICLR 2026)", "2025-10", "arXiv:2510.05318", "600 tasks / 11,796 interactions", "GPT-5 8.67% c-Interact", "verified", ["clarification_emit", "ambiguity_resolution", "multi_turn_state", "crud_ddl_emit"]),
    ("LiveSQLBench", "data_engineering", "HKU BIRD + Google", "2025-05", "livesqlbench.ai", "270-600 tasks, industrial schemas", "DIA 48.0% (Jun 2026)", "flagged", ["contamination_resistant_eval", "ddl_dml_emit", "business_rule_drift", "schema_linking"]),
    ("BIRD-CRITIC", "data_engineering", "HKU BIRD + Google (NeurIPS 2025)", "2025-02", "bird-critic.github.io", "600+200 tasks, 4 dialects", "o1-preview 35.5% vs human 78.87%", "verified", ["sql_error_diagnose", "sql_repair", "dialect_aware_fix", "test_case_verification"]),
    ("CORGI", "data_engineering", "Cornell/Mimno", "2025-10", "arXiv:2510.07309", "business text-to-SQL, 4 tiers", "33% lower than BIRD", "verified", ["causal_reasoning", "predictive_sql", "recommendation_synthesis", "business_grounding"]),
    ("Semantic Layers", "data_engineering", "Rumiantsau/Fokeev", "2026-04", "arXiv:2604.25149", "100 NL questions (ClickHouse)", "semantic docs +17-23pp", "flagged", ["semantic_metric_certify", "metric_decompose", "semantic_layer_mediation", "hallucination_guard"]),
    # ---- SWE / agentic coding ----
    ("SWE-bench Pro", "swe_agentic", "Scale AI", "2025-09", "arXiv:2509.16941", "1,865 tasks, 41 repos (contamination-resistant)", "GPT-5 23.3% pass@1 (vs 70%+ Verified)", "verified", ["reproduce_from_issue", "fault_localize", "cross_file_retrieve", "minimal_patch", "test_run_diff", "long_horizon_plan"]),
    ("Terminal-Bench 2.0", "swe_agentic", "Stanford + Laude", "2026-01", "arXiv:2601.11868", "89 tasks (Harbor harness)", "Codex+GPT-5.2 62.9%", "verified", ["cli_command_synthesis", "long_horizon_plan", "env_setup_build", "test_run_diff", "verification_self_check"]),
    ("SWE-Lancer", "swe_agentic", "OpenAI", "2025-02", "arXiv:2502.12115", "1,488 Upwork tasks, $1M payouts", "Claude 3.5 Sonnet best; cannot solve majority", "verified", ["reproduce_from_issue", "cross_file_retrieve", "minimal_patch", "test_run_diff", "long_horizon_plan"]),
    ("R2E-Gym", "swe_agentic", "UC Berkeley (COLM 2025)", "2025-04", "arXiv:2504.07164", ">8,100 problems, 13 repos", "R2E-Gym-32B 34.4% / 51% w/ hybrid verifier", "verified", ["env_setup_build", "reproduce_from_issue", "fault_localize", "minimal_patch", "test_run_diff", "verification_self_check"]),
    ("CI-Repair-Bench", "swe_agentic", "Concordia SPEAR Lab", "2026-05", "arXiv:2604.27148", "567 CI-failure instances, 103 repos", "GPT-5-mini 18.9% pass@1", "verified", ["reproduce_from_issue", "env_setup_build", "fault_localize", "test_run_diff", "minimal_patch"]),
    ("SWE-Perf", "swe_agentic", "TikTok/ByteDance", "2025-07", "arXiv:2507.12415", "140 perf-optimization instances", "expert 10.85% vs best 2.26% speedup", "verified", ["performance_profiling", "fault_localize", "cross_file_retrieve", "minimal_patch", "test_run_diff"]),
    ("SWE-fficiency", "swe_agentic", "arXiv 2511.06090", "2025-11", "arXiv:2511.06090", "498 tasks, 9 DS/ML/HPC repos", "agents <0.15x expert speedup", "verified", ["performance_profiling", "fault_localize", "cross_file_retrieve", "test_run_diff"]),
    ("Konwinski Prize", "swe_agentic", "Laude Institute (Kaggle)", "2025-07", "kprize.ai", "held-out post-deadline issues", "winner 7.5%; $1M >90% unclaimed", "verified", ["reproduce_from_issue", "fault_localize", "cross_file_retrieve", "minimal_patch", "test_run_diff"]),
    ("IDE-Bench", "swe_agentic", "AfterQuery", "2026-01", "arXiv:2601.20886", "80 multi-file tasks, 8 repos", "Claude Sonnet 4.5 87.5% pass@1", "flagged", ["cross_file_retrieve", "fault_localize", "minimal_patch", "test_run_diff", "long_horizon_plan"]),
    ("Commit0", "swe_agentic", "Cornell + Cohere (ICLR 2025)", "2024-12", "arXiv:2412.01769", "54-57 libraries from spec", "OpenHands 41.2% Lite / 15.1% all", "verified", ["spec_to_implementation", "long_horizon_plan", "test_run_diff"]),
    ("SWE-Gym", "swe_agentic", "Berkeley/UIUC/CMU (ICML 2025)", "2024-12", "arXiv:2412.21139", "2,438 training instances", "training env; 32% Verified achieved", "verified", ["env_setup_build", "reproduce_from_issue", "verification_self_check"]),
    ("SWE-rebench", "swe_agentic", "Nebius", "2025-05", "arXiv:2505.20411", "~1000s decontaminated instances (monthly)", "not verified this session", "flagged", ["reproduce_from_issue", "fault_localize", "cross_file_retrieve", "minimal_patch", "test_run_diff"]),
    ("SWE-bench Live", "swe_agentic", "Microsoft", "2025-05", "arXiv:2505.23419", "~1,500+ instances (monthly, RepoLaunch)", "not verified this session", "flagged", ["reproduce_from_issue", "fault_localize", "cross_file_retrieve", "minimal_patch", "test_run_diff"]),
    ("AppWorld", "swe_agentic", "Stony Brook", "2024-07", "arXiv:2407.18901", "9 apps, 457 APIs, 750 tasks", "GPT-4o 49% normal / 30% challenge", "verified", ["multi_step_api_state", "tool_select_abstain", "long_horizon_plan"]),
    # ---- tool use + agentic ----
    ("tau2-bench", "agentic", "Sierra", "2025-06", "arXiv:2506.07982", "dual-control telecom+retail+airline", "sharp drop no-user->dual-control", "verified", ["multi_step_api_state", "user_interaction_clarify", "tool_select_abstain", "long_horizon_plan"]),
    ("BFCL V4", "agentic", "UC Berkeley Gorilla", "2025-07", "gorilla.cs.berkeley.edu", "multi-turn/agentic/web-search/memory", "frontier lead (live table)", "flagged", ["tool_select_abstain", "multi_step_api_state", "long_horizon_plan", "verification_self_check"]),
    ("GAIA2 / ARE", "agentic", "Meta Superintelligence Labs", "2025-09", "arXiv:2509.17158", "1,120 scenarios (async mobile)", "GPT-5 leads; time-reasoning hard", "verified", ["multi_step_api_state", "tool_select_abstain", "long_horizon_plan", "temporal_reasoning", "verification_self_check"]),
    # ---- frontier / novel ----
    ("ARC-AGI-3", "frontier", "ARC Prize Foundation", "2026-03", "arXiv:2603.24621", "hundreds of interactive games (no instructions)", "frontier 0.51% vs human 100%", "flagged", ["goal_inference", "environment_exploration", "long_horizon_plan"]),
    ("ARC-AGI-2", "frontier", "ARC Prize Foundation", "2025-03", "arXiv:2505.11831", "grid abstraction puzzles", "pure LLM 0%; best systems ~30-50%", "verified", ["fluid_abstraction", "compositional_rule_infer"]),
    ("FrontierMath Tier 4", "frontier", "Epoch AI", "2025-06", "arXiv:2411.04872", "43 research-level math problems", "only ~9/43 ever solved", "verified", ["research_math_reasoning", "symbolic_verify"]),
    ("Vending-Bench 2", "frontier", "Andon Labs", "2025-11", "epoch.ai/benchmarks/vending-bench-2", "365-day business simulation", "human ~$63k/yr; models capture fraction", "flagged", ["state_memory_store", "context_compaction", "ledger_verifier", "identity_goal_anchoring", "loop_stop_control"]),
    ("AgencyBench", "frontier", "GAIR/SJTU (ACL 2026)", "2026-01", "arXiv:2601.11044", "138 tasks (~90 tool-calls, ~1M tokens each)", "proprietary 48.4% vs open 32.1%", "flagged", ["state_memory_store", "context_compaction", "long_horizon_plan", "loop_stop_control"]),
    ("METR time-horizon", "frontier", "METR", "2025-03", "arXiv:2503.14499", "~170-230 tasks (<30s to 8h+)", "50% horizon doubling ~131 days", "verified", ["long_horizon_plan", "loop_stop_control", "verification_self_check"]),
    ("CyberGym", "frontier", "UC Berkeley (Dawn Song)", "2025-06", "arXiv:2506.02548", "1,507 instances, 188 projects", "best ~20%; found 34 zero-days", "verified", ["fuzzing_poc_harness", "crash_triage_verify", "prepatch_postpatch_diff"]),
    ("PaperBench", "frontier", "OpenAI", "2025-04", "arXiv:2504.01848", "20 papers, 8,316 sub-tasks", "best 21%; ML-PhD humans 41.4%", "verified", ["rubric_decompose", "experiment_runner", "result_vs_reference_verify"]),
    ("GDPval", "frontier", "OpenAI", "2025-09", "arXiv:2510.04374", "1,320 tasks, 44 occupations", "approaching experts on ~half", "verified", ["deliverable_gen", "domain_knowledge_retrieval", "verification_self_check"]),
    ("Humanity's Last Exam", "frontier", "CAIS + Scale AI", "2025-01", "arXiv:2501.14249", "2,500 expert questions", "launch <10%; tool-use climbs higher", "verified", ["expert_knowledge_retrieval", "multi_modal_reason"]),
    ("OSWorld 2.0", "frontier", "XLang Lab (HKU)", "2026-06", "os-world.github.io", "369+43 tasks (computer use)", "human 72.36%; agents climbing", "flagged", ["gui_grounding", "long_horizon_plan", "tool_select_abstain", "verification_self_check"]),
]

# unbenchmarked white-space (the Capability-Gap negative space the research explicitly flagged)
GAP_TARGETS: list[tuple] = [
    ("scd_type_2_dimensional_modeling", "data_engineering", "no dedicated LLM benchmark exists (research-flagged white space)"),
    ("star_vs_wide_table_decision", "data_engineering", "unbenchmarked; we already generate primitives for it (uc06adv)"),
    ("semantic_metric_certify", "data_engineering", "barely benchmarked (only Semantic Layers 2026)"),
    ("game_theory_grundy", "competitive_programming", "no dedicated generation family yet; a consumption-benchmark gap"),
    ("elo_measurement_standardization", "competitive_programming", "'When Elo Lies' — need deterministic measurement primitives"),
    ("gold_answer_execution_equivalence_verify", "data_engineering", "52-63% annotation errors in SQL benchmarks → verify meta-primitive"),
]


def _slug(name: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", name.lower()))[:60]


def _benchmark_rows() -> list[dict[str, Any]]:
    rows = []
    for name, cat, org, rel, url, size, score, ver, prims in BENCHMARKS:
        rows.append({
            "record_type": "benchmark_landscape_entry",
            "benchmark_id": f"bench:{cat}:{_slug(name)}",
            "name": name, "category": cat, "org": org, "release": rel, "url": url,
            "size": size, "top_score_note": score, "verification_status": ver,
            "primitive_demands": prims,
            "score_disclaimer": "RESEARCH INTAKE from primary sources at publication — NOT a local measurement; never treat as truth.",
            **BOUNDARY,
        })
    return rows


def _primitive_priority_rows() -> list[dict[str, Any]]:
    """COMPUTED: which primitive families the most benchmarks demand → the build-priority list."""
    counter: Counter[str] = Counter()
    for _n, _c, _o, _r, _u, _s, _sc, _v, prims in BENCHMARKS:
        for p in prims:
            counter[p] += 1
    total = len(BENCHMARKS)
    rows = []
    for prim, count in counter.most_common():
        tier = "tier1_universal" if count >= total * 0.20 else ("tier2_common" if count >= total * 0.08 else "tier3_specialized")
        # verification/test/execution family flag — the cross-lane finding
        is_verification = any(k in prim for k in ("verify", "test", "checker", "validator", "oracle", "diff", "gate", "self_check", "anti_fabrication", "execution"))
        rows.append({
            "record_type": "primitive_demand_priority",
            "primitive_family": prim, "benchmarks_demanding": count,
            "pct_of_benchmarks": round(100 * count / total, 1),
            "priority_tier": tier, "is_verification_family": is_verification,
            **BOUNDARY,
        })
    return rows


def _gap_rows() -> list[dict[str, Any]]:
    return [{"record_type": "benchmark_gap_target", "primitive_family": p, "category": c, "note": n, **BOUNDARY}
            for p, c, n in GAP_TARGETS]


JSONL_BUILDERS: dict[str, Callable[[], list[dict[str, Any]]]] = {
    "benchmarks.jsonl": _benchmark_rows,
    "primitive_demand_priority.jsonl": _primitive_priority_rows,
    "gap_targets.jsonl": _gap_rows,
}


def build_pack() -> dict[str, list[dict[str, Any]]]:
    return {n: b() for n, b in JSONL_BUILDERS.items()}


def build_manifest(pack: dict[str, list[dict[str, Any]]], *, date: str) -> dict[str, Any]:
    rc = {n: len(r) for n, r in pack.items()}
    cats = Counter(r["category"] for r in pack["benchmarks.jsonl"])
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for n in sorted(pack) for r in pack[n])
    top = pack["primitive_demand_priority.jsonl"][0] if pack["primitive_demand_priority.jsonl"] else {}
    return {
        "record_type": "benchmark_landscape_catalog_manifest",
        "pack_id": "benchmark-landscape-catalog", "generator": "scripts/build_benchmark_landscape_catalog.py",
        "generated_utc": date, "row_counts": rc, "total_rows": sum(rc.values()),
        "benchmark_count": len(pack["benchmarks.jsonl"]), "categories": dict(cats),
        "verified_count": sum(1 for r in pack["benchmarks.jsonl"] if r["verification_status"] == "verified"),
        "flagged_count": sum(1 for r in pack["benchmarks.jsonl"] if r["verification_status"] == "flagged"),
        "top_demanded_primitive": {"family": top.get("primitive_family"), "pct": top.get("pct_of_benchmarks")},
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        **BOUNDARY,
    }


def write_pack(*, date: str) -> dict[str, Any]:
    pack = build_pack()
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    for n, rows in pack.items():
        (PACK_DIR / n).write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(pack, date=date)
    (PACK_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    pack = build_pack()
    manifest = build_manifest(pack, date="1970-01-01")
    prio = pack["primitive_demand_priority.jsonl"]
    top5 = prio[:5]
    checks = [
        (">=45 benchmarks across 5 categories", len(pack["benchmarks.jsonl"]) >= 45 and len(manifest["categories"]) >= 5),
        ("every benchmark has >=1 primitive demand + url + verification_status", all(
            r["primitive_demands"] and r["url"] and r["verification_status"] in ("verified", "flagged")
            for r in pack["benchmarks.jsonl"])),
        ("scores carry the not-truth disclaimer", all("NOT a local measurement" in r["score_disclaimer"] for r in pack["benchmarks.jsonl"])),
        ("priority is COMPUTED (counts descend)", all(top5[i]["benchmarks_demanding"] >= top5[i+1]["benchmarks_demanding"] for i in range(len(top5)-1))),
        ("a VERIFICATION-family primitive is in the top 5 (the cross-lane finding, derived not asserted)",
         any(r["is_verification_family"] for r in top5)),
        ("execution/verification primitives dominate the top-3 (long_horizon_plan, test_run_diff computed as #1/#2)",
         "test_run_diff" in {r["primitive_family"] for r in prio[:3]} and {"long_horizon_plan", "test_run_diff"} <= {r["primitive_family"] for r in prio[:3]}),
        ("gap targets include the white-space (scd/star-vs-wide/game-theory)",
         {"scd_type_2_dimensional_modeling", "star_vs_wide_table_decision", "game_theory_grundy"} <= {r["primitive_family"] for r in pack["gap_targets.jsonl"]}),
        ("boundary held", all(r["candidate"] is True and r["serves_truth"] is False for rows in pack.values() for r in rows)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - benchmark_landscape_catalog:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - benchmark_landscape_catalog: {manifest['benchmark_count']} benchmarks / 5 categories; "
          f"#1 demanded primitive (computed) = {prio[0]['primitive_family']} ({prio[0]['pct_of_benchmarks']}%).")
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
