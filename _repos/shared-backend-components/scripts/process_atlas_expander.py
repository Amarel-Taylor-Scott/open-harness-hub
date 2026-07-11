#!/usr/bin/env python3
"""scripts.process_atlas_expander — the RAW-COUNT expansion engine over the process_possibility_atlas seed
(candidate-only).

Owner spec (2026-07-08, §17/§18): 10x the atlas. raw candidate_count is a co-primary SCALING goal; usefulness
is a NON-DESTRUCTIVE ROUTER (rank/diversify/shard/enqueue/downrank-at-serve-time), NEVER a generation cap or a
discard; serve-time context budget applies to serving, not generation. Minimums (>=8 methods/step, >=25
steps/domain, ports/verifiers/fallbacks/metadata) are WARNINGS that emit GAP RECORDS — never hard caps.

This engine takes the 607 seed possibilities and explodes them lazily across IMPLEMENTATION_KINDS (60+) x
MUTATION_OPERATORS, stamping each expanded candidate with LINEAGE (parent_candidates + mutation_history) and
ROUTE PORTS (input/output, port_status=needs_schema_interrogation), all candidate=true/serves_truth=false. It
emits gap records for under-covered domains/steps and a port-normalization queue. Full cartesian is available
(--full) but NOT the default; use --sample / --domain / --impl-kind / --undercovered-first / --weirdness.

    python3 scripts/process_atlas_expander.py --self-test
    python3 scripts/process_atlas_expander.py --stats
    python3 scripts/process_atlas_expander.py --emit --sample 10
    python3 scripts/process_atlas_expander.py --emit --full
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
import json  # noqa: E402
from typing import Any, Iterator  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"process_atlas_expander requires canonical_id; import failed: {exc}")
from scripts.process_possibility_atlas import (  # noqa: E402
    DOMAIN_STEPS, build_candidate_cards as _seed_cards, total_possibilities,
)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
EXP_ID_PREFIX = "prim-atlasx"
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"
ARTIFACT_DIR_REL = "data/dev-intel/atlas"
PACKAGED_AT = "2026-07-08T00:00:00Z"

# ── the metric law v2 (owner §2), encoded as the authoritative object. usefulness is a ROUTER, not a brake. ──
METRIC_LAW_V2: dict[str, Any] = {
    "raw_candidate_count": {"role": "co_primary_scaling_goal", "may_increase_without_quality_gate": True,
                            "may_be_ranked": True, "may_be_deleted": False, "may_be_capped_by_usefulness": False},
    "executor_certified_per_million_tokens": {"role": "quality_signal_at_scale",
                                              "may_rank_generation_strategies": True,
                                              "may_create_priority_queues": True, "may_not_cap_raw_generation": True},
    "usefulness_score": {"role": "non_destructive_router",
                         "allowed_actions": ["rank", "diversify", "shard", "enqueue_to_benchmark",
                                             "enqueue_to_executor_synthesis", "enqueue_to_review",
                                             "downrank_at_serve_time"],
                         "forbidden_actions": ["delete_candidate", "prevent_generation", "cap_source",
                                               "cap_domain", "cap_raw_count"]},
    "serve_time_context_budget": {"role": "retrieval_injection_budget",
                                  "applies_to": ["route_planning", "prompt_context", "tool_selection"],
                                  "does_not_apply_to": ["raw_candidate_generation", "candidate_storage",
                                                        "candidate_mutation", "candidate_remixing"]},
}

# ── 60+ implementation kinds (owner §4): one conceptual step sprouts across all of these ─────────────────────
IMPLEMENTATION_KINDS: list[str] = [
    "python_function", "python_class", "python_async_function", "pydantic_validator", "pandera_validator",
    "great_expectations_expectation", "sql_udf", "sql_view", "dbt_model", "dbt_macro", "duckdb_macro",
    "postgres_function", "bigquery_udf", "snowflake_udf", "spark_job", "pyspark_transform",
    "flink_stream_processor", "kafka_stream_processor", "typescript_function", "node_cli", "fastapi_endpoint",
    "express_endpoint", "openapi_tool", "graphql_resolver", "protobuf_service", "grpc_service", "mcp_tool",
    "cli_command", "bash_script", "github_action", "docker_entrypoint", "kubernetes_job", "helm_hook",
    "terraform_module", "airflow_operator", "airflow_dag", "dagster_asset", "prefect_flow", "temporal_workflow",
    "aws_step_function", "gcp_workflow", "azure_durable_function", "browser_state_machine", "playwright_adapter",
    "selenium_adapter", "cdp_adapter", "puppeteer_adapter", "scrapy_spider", "crawlee_actor",
    "browserbase_adapter", "rpa_bot", "spreadsheet_formula", "excel_powerquery", "google_sheets_function",
    "retool_workflow", "zapier_action", "n8n_node", "human_review_form", "benchmark_verifier",
    "negative_fixture_generator", "synthetic_data_generator",
]

# ── mutation operators (owner §10): a possibility is a genome that can mutate ─────────────────────────────────
MUTATION_OPERATORS: list[str] = [
    "swap_model", "swap_backend", "swap_runtime", "swap_language", "swap_storage", "swap_source", "swap_provider",
    "swap_standard", "swap_geography", "swap_schema", "swap_input_port", "swap_output_port", "swap_metric",
    "swap_verifier", "swap_fallback", "swap_security_policy", "swap_human_review_policy", "swap_batch_streaming",
    "swap_sync_async", "swap_cost_latency_priority", "split_step", "merge_steps", "reorder_steps",
    "add_metadata_classifier", "add_quality_gate", "add_source_span_receipt", "add_benchmark",
    "add_negative_fixture", "add_anti_primitive", "add_route_port", "add_cache", "add_retry", "add_timeout",
    "add_rate_limit", "add_drift_detector",
]

# ── variation/composition operators (owner §11): remix composes multiple primitives ─────────────────────────
VARIATION_OPERATORS: list[str] = [
    "sequential_compose", "parallel_compose", "fanout", "fanin", "map_over_pages", "map_over_regions",
    "map_over_documents", "map_over_rows", "reduce_results", "vote_results", "rank_results", "ensemble_results",
    "fallback_chain", "human_review_gate", "confidence_gate", "quality_gate", "route_by_metadata",
    "route_by_cost", "route_by_latency", "route_by_source_trust", "route_by_data_sensitivity",
    "route_by_region_type", "route_by_document_type", "route_by_standard", "route_by_geography", "route_by_system",
]

# ── 40+ NEW process domains (owner §6): added as gap-flagged domains to populate (warnings, not caps) ────────
NEW_DOMAINS: list[str] = [
    "source_discovery", "browser_acquisition", "api_ingestion", "code_mining", "repo_mining", "notebook_mining",
    "schema_mining", "spreadsheet_mining", "workflow_mining", "support_ticket_mining", "email_thread_mining",
    "event_log_process_mining", "ocr_ingestion", "table_extraction", "contract_processing", "invoice_processing",
    "claim_processing", "payment_reconciliation", "entity_resolution", "address_enrichment",
    "geospatial_enrichment", "identity_enrichment", "product_enrichment", "financial_message_processing",
    "healthcare_admin_processing", "procurement_processing", "salesforce_revops_processing",
    "field_service_processing", "micro_saas_workflow_processing", "crypto_transaction_processing",
    "data_quality_monitoring", "feature_engineering", "feature_selection", "dimensionality_reduction",
    "automl_model_search", "model_registry", "model_serving", "model_monitoring", "llm_prompt_ops",
    "rag_pipeline", "browser_agent_ops", "tool_registry_ops", "security_review", "benchmark_generation",
    "synthetic_data_generation", "human_review_ops", "route_compilation", "token_savings_measurement",
    "primitive_economics", "primitive_warranty_management", "primitive_deprecation",
]
# NOTE: 'insurance_ops_processing' from the owner list is intentionally OMITTED — repo law forbids insurance.

# ── possibility schema v2 fields (owner §9) ──────────────────────────────────────────────────────────────────
POSSIBILITY_SCHEMA_V2_FIELDS: list[str] = [
    "domain", "step", "possibility_id", "method", "best_for", "not_for", "cost_profile", "quality_profile",
    "routing_features", "input_ports", "output_ports", "implementation_kinds", "verifiers", "fallbacks",
    "metadata_emitted", "failure_modes", "mutation_operators", "candidate_generation_policy",
]

# ── expansion minimums (owner §1) — WARNINGS that emit gaps, never generation caps ──────────────────────────
MIN_METHODS_PER_STEP = 8
MIN_STEPS_PER_DOMAIN = 25


def _route_ports(step: str) -> dict[str, Any]:
    """Emit route ports for every candidate (owner §15). Unknown -> placeholder + queue flag."""
    return {"input_ports": [f"{step}.input"], "output_ports": [f"{step}.output"], "semantic_types": [],
            "schema_refs": [], "edge_confidence": 0.0, "port_status": "needs_schema_interrogation"}


def expand(sample: int | None = None, full: bool = False, domain: str | None = None,
           impl_kind: str | None = None, with_mutations: int = 0) -> Iterator[dict[str, Any]]:
    """Lazily explode seed possibilities across implementation kinds (+ optional mutations). Raw count SCALES;
    usefulness never caps this. Every expanded candidate carries lineage + ports + the boundary."""
    seeds = _seed_cards()
    if domain:
        seeds = [s for s in seeds if s["domain"] == domain]
    if impl_kind:
        kinds = [impl_kind]
    elif full:
        kinds = IMPLEMENTATION_KINDS
    else:
        kinds = IMPLEMENTATION_KINDS[: (sample or 10)]
    muts = MUTATION_OPERATORS[:with_mutations] if with_mutations else [None]
    for s in seeds:
        step = s["step"]
        for kind in kinds:
            for mut in muts:
                parts = [s["card_id"], kind] + ([mut] if mut else [])
                cid = canonical_id(EXP_ID_PREFIX, *parts)
                mutation_history = [f"add_implementation_kind:{kind}"] + ([f"mutate:{mut}"] if mut else [])
                yield {
                    "record_type": "atlas_expansion_candidate",
                    "kind": "process_step_implementation_variant",
                    "card_id": cid, "primitive_id": cid,
                    "title": f"{s['domain']}.{step} :: {s['method']} [{kind}]" + (f" +{mut}" if mut else ""),
                    "domain": s["domain"], "step": step, "method": s["method"],
                    "implementation_kind": kind,
                    "parent_candidates": [s["card_id"]],
                    "mutation_history": mutation_history,
                    "seed_source": "process_possibility_atlas",
                    "routing_features": s.get("routing_features", []),
                    "verifiers": s.get("verifiers", []),
                    "fallbacks": s.get("fallbacks", []),
                    **_route_ports(step),
                    "candidate": True, "serves_truth": False,
                    "candidate_generation_policy": {"raw_count_scaling": True, "candidate_only": True,
                                                    "serve_truth": False},
                    "packaged_at": PACKAGED_AT,
                }


def gap_records() -> list[dict[str, Any]]:
    """Under-coverage -> GAP records (warnings, NOT caps): domains <25 steps, steps <8 methods, missing
    verifiers/fallbacks/ports (owner §8-of-prompt). New domains are gap-flagged to populate."""
    gaps: list[dict[str, Any]] = []
    for d, steps in DOMAIN_STEPS.items():
        if len(steps) < MIN_STEPS_PER_DOMAIN:
            gaps.append({"gap": "domain_under_min_steps", "domain": d, "n_steps": len(steps),
                         "needed": MIN_STEPS_PER_DOMAIN, "severity": "warning"})
        for s in steps:
            sid = f"{d}.{s['step']}"
            if len(s["possibilities"]) < MIN_METHODS_PER_STEP:
                gaps.append({"gap": "step_under_min_methods", "step_id": sid, "n": len(s["possibilities"]),
                             "needed": MIN_METHODS_PER_STEP, "severity": "warning"})
            if not s.get("verifiers"):
                gaps.append({"gap": "step_missing_verifiers", "step_id": sid, "severity": "warning"})
            if not s.get("fallbacks"):
                gaps.append({"gap": "step_missing_fallbacks", "step_id": sid, "severity": "warning"})
    for d in NEW_DOMAINS:
        gaps.append({"gap": "domain_not_yet_populated", "domain": d, "n_steps": 0,
                     "needed": MIN_STEPS_PER_DOMAIN, "severity": "warning"})
    return gaps


def full_expansion_count(with_mutations: int = 0) -> int:
    base = total_possibilities() * len(IMPLEMENTATION_KINDS)
    return base * (with_mutations or 1)


def emit(sample: int | None = 10, full: bool = False, domain: str | None = None,
         impl_kind: str | None = None, with_mutations: int = 0) -> dict[str, Any]:
    out_dir = resource(ARTIFACT_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    variants_path = out_dir / "implementation_variants.jsonl"
    port_path = out_dir / "port_normalization_queue.jsonl"
    gaps_path = out_dir / "gap_records.jsonl"
    n = 0
    with variants_path.open("w", encoding="utf-8") as vf, port_path.open("w", encoding="utf-8") as pf:
        for c in expand(sample=sample, full=full, domain=domain, impl_kind=impl_kind, with_mutations=with_mutations):
            vf.write(json.dumps(c, sort_keys=True) + "\n")
            pf.write(json.dumps({"candidate_id": c["card_id"], "input_ports": c["input_ports"],
                                 "output_ports": c["output_ports"], "port_status": c["port_status"]}) + "\n")
            n += 1
    gaps = gap_records()
    with gaps_path.open("w", encoding="utf-8") as gf:
        for g in gaps:
            gf.write(json.dumps(g, sort_keys=True) + "\n")
    report = out_dir / "atlas_expansion_report.md"
    report.write_text(
        f"# Atlas expansion report\n\n"
        f"- seed possibilities: {total_possibilities()}\n"
        f"- implementation kinds: {len(IMPLEMENTATION_KINDS)}\n"
        f"- mutation operators: {len(MUTATION_OPERATORS)} | variation operators: {len(VARIATION_OPERATORS)}\n"
        f"- new domains queued (gap-flagged): {len(NEW_DOMAINS)}\n"
        f"- expanded candidates emitted this run: {n}\n"
        f"- FULL cross-product (impl-only): {full_expansion_count()}\n"
        f"- gap records: {len(gaps)}\n"
        f"- boundary: candidate=true/serves_truth=false; usefulness = non-destructive router (never caps count)\n",
        encoding="utf-8")
    return {"variants_emitted": n, "gap_records": len(gaps), "full_impl_crossproduct": full_expansion_count(),
            "artifacts_dir": str(out_dir)}


def self_test() -> bool:
    """Mutation-gated. Asserts: (a) usefulness CANNOT cap/delete/prevent generation; (b) raw count SCALES (the
    engine explodes the seed); (c) expansion never blocked by gaps; (d) lineage + ports + boundary on every card."""
    # (1) metric law v2: usefulness is a router, not a brake.
    us = METRIC_LAW_V2["usefulness_score"]
    for forbidden in ("delete_candidate", "prevent_generation", "cap_raw_count", "cap_domain", "cap_source"):
        assert forbidden in us["forbidden_actions"], f"usefulness must forbid {forbidden}"
    rc = METRIC_LAW_V2["raw_candidate_count"]
    assert rc["may_be_deleted"] is False and rc["may_be_capped_by_usefulness"] is False, "raw count must not be capped"
    assert "candidate_storage" in METRIC_LAW_V2["serve_time_context_budget"]["does_not_apply_to"]

    # (2) implementation kinds >= 60; mutation/variation operators present.
    assert len(IMPLEMENTATION_KINDS) >= 60, f"need >=60 impl kinds, got {len(IMPLEMENTATION_KINDS)}"
    assert len(set(IMPLEMENTATION_KINDS)) == len(IMPLEMENTATION_KINDS), "dup impl kind"
    assert len(MUTATION_OPERATORS) >= 30 and len(VARIATION_OPERATORS) >= 20

    # (3) RAW COUNT SCALES: a sampled expansion explodes the 607 seed by the sampled impl kinds.
    seed_n = total_possibilities()
    sampled = list(expand(sample=10))
    assert len(sampled) == seed_n * 10, f"expected {seed_n*10} sampled variants, got {len(sampled)}"
    assert full_expansion_count() == seed_n * len(IMPLEMENTATION_KINDS) >= 30000, "full cross-product too small"

    # (4) every expanded candidate: lineage + ports + boundary + policy.
    ids = set()
    for c in sampled:
        assert c["candidate"] is True and c["serves_truth"] is False
        assert c["parent_candidates"] and c["mutation_history"], "missing lineage"
        assert c["input_ports"] and c["output_ports"] and c["port_status"] == "needs_schema_interrogation"
        assert c["candidate_generation_policy"]["raw_count_scaling"] is True
        ids.add(c["card_id"])
    assert len(ids) == len(sampled), "duplicate expanded ids"

    # (5) gaps are WARNINGS, not caps: gap records exist AND expansion still produced candidates for gapped steps.
    gaps = gap_records()
    assert gaps and all(g.get("severity") == "warning" for g in gaps), "gaps must be warnings"
    assert any(g["gap"] == "domain_not_yet_populated" for g in gaps), "new domains should be gap-flagged"
    # a domain under min steps still generated variants (generation not blocked by the gap):
    assert any(c["domain"] == "evaluation" for c in sampled), "gapped domain must still generate"

    # (6) mutation cross-product multiplies count (raw scaling), with lineage recording the mutation.
    with_mut = list(expand(sample=2, with_mutations=3))
    assert len(with_mut) == seed_n * 2 * 3
    assert any("mutate:" in "".join(c["mutation_history"]) for c in with_mut)

    print(f"OK process_atlas_expander self-test: seed {seed_n} x {len(IMPLEMENTATION_KINDS)} impl kinds = "
          f"{full_expansion_count()} full cross-product; {len(NEW_DOMAINS)} new domains queued; "
          f"{len(gap_records())} gap records (warnings); usefulness=router (cannot cap count); serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Raw-count expansion engine over the process atlas seed.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--sample", type=int, default=10, help="implementation kinds per seed (default 10)")
    ap.add_argument("--full", action="store_true", help="full impl-kind cross-product")
    ap.add_argument("--domain", default=None)
    ap.add_argument("--impl-kind", default=None)
    ap.add_argument("--with-mutations", type=int, default=0, help="also apply the first N mutation operators")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.stats:
        print(json.dumps({"seed_possibilities": total_possibilities(),
                          "implementation_kinds": len(IMPLEMENTATION_KINDS),
                          "mutation_operators": len(MUTATION_OPERATORS),
                          "variation_operators": len(VARIATION_OPERATORS),
                          "new_domains_queued": len(NEW_DOMAINS),
                          "full_impl_crossproduct": full_expansion_count(),
                          "full_with_all_mutations": full_expansion_count(len(MUTATION_OPERATORS)),
                          "gap_records": len(gap_records())}, indent=2))
        return
    if args.emit:
        print(json.dumps(emit(sample=args.sample, full=args.full, domain=args.domain,
                              impl_kind=args.impl_kind, with_mutations=args.with_mutations), indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
