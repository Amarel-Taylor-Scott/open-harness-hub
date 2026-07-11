#!/usr/bin/env python3
"""Generate problem-solution detail cards for ranked primitive opportunities."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACK_DIR = _resource("catalog/knowledge-packs/data/high-priority-primitive-opportunity-rankings")
PACK_DIR = _resource("catalog/knowledge-packs/data/primitive-problem-solution-details")
SOURCE_STATUS = "curated_problem_solution_seed_needs_source_ref_resolution"

COMMON_ROW = {
    "candidate": True,
    "serves_truth": False,
    "source_refs": [],
    "source_evidence_status": SOURCE_STATUS,
}

PATTERNS = [
    {
        "solution_pattern_id": "pattern:verify_before_answer",
        "title": "Verify before answer",
        "best_for_modules": ["module:data_verification", "module:citation_span_verification", "module:legal_information_search"],
        "route_steps": ["extract claims", "resolve authoritative sources", "compare evidence", "emit verified disputed or needs-evidence receipt"],
        "primary_receipts": ["VerificationReceipt", "EvidenceSpanReceipt", "NeedsEvidenceReceipt"],
    },
    {
        "solution_pattern_id": "pattern:resolve_enrich_then_receipt",
        "title": "Resolve enrich then receipt",
        "best_for_modules": ["module:entity_resolution", "module:entity_enrichment", "module:related_data_search"],
        "route_steps": ["normalize entity mentions", "resolve identity candidates", "fetch enrichment sources", "emit provenance and conflict receipts"],
        "primary_receipts": ["IdentityResolutionReceipt", "EnrichmentReceipt", "ConflictReceipt"],
    },
    {
        "solution_pattern_id": "pattern:jurisdiction_ladder",
        "title": "Jurisdiction ladder",
        "best_for_modules": ["module:geography_specific_search", "module:jurisdiction_policy_mapping", "module:legal_information_search"],
        "route_steps": ["normalize country and subjurisdiction", "rank official sources", "check effective dates", "route conflicts to review"],
        "primary_receipts": ["JurisdictionReceipt", "EffectiveDateReceipt", "ConflictReceipt"],
    },
    {
        "solution_pattern_id": "pattern:freshness_monitor",
        "title": "Freshness monitor",
        "best_for_modules": ["module:fragile_context_monitoring", "module:temporal_freshness_tracking"],
        "route_steps": ["classify fragile facts", "extract effective dates", "search change signals", "rank refresh queue"],
        "primary_receipts": ["FreshnessReceipt", "NeedsRefreshReceipt", "RefreshPlan"],
    },
    {
        "solution_pattern_id": "pattern:quality_gate_then_quarantine",
        "title": "Quality gate then quarantine",
        "best_for_modules": ["module:data_quality_profiling", "module:schema_mapping_normalization", "module:document_extraction_evidence"],
        "route_steps": ["profile input data", "validate required fields", "quarantine bad rows or fields", "emit quality and rejected-row receipts"],
        "primary_receipts": ["QualityReceipt", "RejectedRowManifest", "MappingGapReceipt"],
    },
    {
        "solution_pattern_id": "pattern:risk_signal_review_packet",
        "title": "Risk signal review packet",
        "best_for_modules": ["module:adverse_media_risk_discovery", "module:sanctions_watchlist_screening", "module:privacy_boundary_classification"],
        "route_steps": ["screen candidate signals", "score evidence quality", "redact sensitive fields", "emit human-review packet"],
        "primary_receipts": ["ScreeningReceipt", "PrivacyReceipt", "HumanReviewReceipt"],
    },
    {
        "solution_pattern_id": "pattern:graph_extract_with_evidence",
        "title": "Graph extract with evidence",
        "best_for_modules": ["module:relationship_graph_extraction"],
        "route_steps": ["resolve entities", "extract relation edges", "attach source spans", "validate graph consistency"],
        "primary_receipts": ["GraphEvidenceReceipt", "SourceSpanReceipt", "GraphConsistencyReceipt"],
    },
    {
        "solution_pattern_id": "pattern:license_terms_gate",
        "title": "License and terms gate",
        "best_for_modules": ["module:license_terms_review", "module:source_ref_resolution"],
        "route_steps": ["resolve source ref", "extract license or terms hints", "score compatibility", "emit use restriction receipt"],
        "primary_receipts": ["LicenseReviewReceipt", "UseRestrictionSet", "SourceRefBundle"],
    },
    {
        "solution_pattern_id": "pattern:proof_receipt_pipeline",
        "title": "Proof receipt pipeline",
        "best_for_modules": ["module:proof_receipt_generation"],
        "route_steps": ["hash trace", "attach source refs", "attach test results", "score promotion gate"],
        "primary_receipts": ["ProofReceipt", "PromotionAdvice", "TraceHashReceipt"],
    },
]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows) + "\n",
        encoding="utf-8",
    )


def _pattern_for(module_id: str) -> dict[str, Any]:
    for pattern in PATTERNS:
        if module_id in pattern["best_for_modules"]:
            return pattern
    return PATTERNS[0]


def _detail_for(opportunity: dict[str, Any]) -> dict[str, Any]:
    pattern = _pattern_for(str(opportunity["module_id"]))
    industry = str(opportunity["industry_title"])
    module = str(opportunity["module_title"])
    variant = str(opportunity["variant_title"])
    source_hints = list(opportunity["source_surface_hints"])
    transformations = list(opportunity["transformations"])
    proof_requirements = list(opportunity["proof_requirements"])
    negative_memory = list(opportunity["negative_memory_queries"])
    opportunity_tail = str(opportunity["opportunity_id"]).split(":", 1)[1]

    return {
        "record_type": "primitive_problem_solution_detail",
        "detail_id": f"detail:{opportunity_tail}",
        "opportunity_id": opportunity["opportunity_id"],
        "rank": opportunity["rank"],
        "priority_score": opportunity["priority_score"],
        "module_id": opportunity["module_id"],
        "industry_id": opportunity["industry_id"],
        "variant_id": opportunity["variant_id"],
        "problem": {
            "statement": f"{industry} teams need {module.lower()} that can be reused across workflows without re-reading all sources or asking a model to improvise the process.",
            "user_triggers": [
                f"user asks for {module.lower()} in a {industry.lower()} workflow",
                "source data is incomplete, stale, ambiguous, or spread across systems",
                "the output needs evidence, review, or a receipt before it can be trusted",
            ],
            "stakes": [
                "wrong matches or stale facts propagate into downstream automation",
                "manual review is slow without source-linked evidence",
                "unverified model output may be mistaken for promoted truth",
            ],
            "non_goals": [
                "do not serve final truth without source refs and proof receipts",
                "do not silently drop conflicts or missing fields",
                "do not copy restricted source implementation code",
            ],
        },
        "solution": {
            "pattern_id": pattern["solution_pattern_id"],
            "summary": f"Use the {pattern['title'].lower()} route for {variant.lower()} delivery: {', '.join(pattern['route_steps'])}.",
            "input_edge": opportunity["input_edge"],
            "output_edge": opportunity["output_edge"],
            "route_steps": pattern["route_steps"],
            "transformations": transformations,
            "runtime_targets": opportunity["runtime_targets"],
            "source_surface_hints": source_hints,
            "primary_receipts": pattern["primary_receipts"],
        },
        "implementation_notes": {
            "base_components": [
                "source_ref_resolver",
                "negative_memory_retrieval",
                "schema_or_policy_validator",
                "receipt_emitter",
            ],
            "deterministic_first_steps": transformations[:2],
            "model_allowed_only_for": [
                "ambiguous extraction after deterministic parsing fails",
                "ranking candidate evidence with source refs attached",
                "drafting review summaries from verified spans",
            ],
            "data_contract": {
                "input_edge": opportunity["input_edge"],
                "output_edge": opportunity["output_edge"],
                "required_receipt": pattern["primary_receipts"][0],
            },
        },
        "acceptance_criteria": [
            "visible input and output edges are validated",
            "at least one source or fixture backs every promoted field",
            "conflicts and gaps emit receipts instead of being hidden",
            "runtime effects and privacy boundaries are declared",
            "proof requirements pass before promotion",
        ],
        "proof_plan": {
            "proof_requirements": proof_requirements,
            "minimum_fixtures": [
                "happy_path_fixture",
                "missing_source_fixture",
                "conflict_or_ambiguous_input_fixture",
            ],
            "promotion_gate": "candidate row can be promoted only after source refs, license review if needed, contract tests, and receipt validation pass",
        },
        "failure_modes": [
            "false positive or false merge",
            "stale or jurisdiction-mismatched source",
            "missing source receipt",
            "schema drift or required-field gap",
            "unsupported model-generated claim",
        ],
        "troubleshooting_hooks": [
            "reproduce failing input",
            "isolate source, schema, policy, or runtime layer",
            "retrieve negative memory",
            "try same-plane deterministic alternative",
            "emit NeedsEvidence or NeedsRefresh when unresolved",
        ],
        "negative_memory_queries": negative_memory,
        "materialization_policy": opportunity["materialization_policy"],
        "example_io": {
            "synthetic_input": f"{opportunity['input_edge']} with {source_hints[0]} evidence and one ambiguous field",
            "expected_output": f"{opportunity['output_edge']} with {pattern['primary_receipts'][0]} and gap receipt when evidence is insufficient",
        },
        **COMMON_ROW,
    }


def main() -> int:
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    opportunities = _read_jsonl(SOURCE_PACK_DIR / "primitive_opportunities_1000.jsonl")
    details = [_detail_for(row) for row in opportunities]
    pattern_rows = [
        {
            "record_type": "primitive_problem_solution_pattern",
            **pattern,
            **COMMON_ROW,
        }
        for pattern in PATTERNS
    ]
    template = {
        "record_type": "primitive_problem_solution_detail_template",
        "required_sections": [
            "problem",
            "solution",
            "implementation_notes",
            "acceptance_criteria",
            "proof_plan",
            "failure_modes",
            "troubleshooting_hooks",
            "negative_memory_queries",
            "example_io",
        ],
        "candidate": True,
        "serves_truth": False,
    }
    manifest = {
        "record_type": "primitive_problem_solution_details_manifest",
        "pack_id": "primitive-problem-solution-details",
        "version": "0.1.0",
        "candidate": True,
        "serves_truth": False,
        "source_status": SOURCE_STATUS,
        "description": "Problem-solution detail cards linked to ranked primitive opportunities. These records hold problem framing, solution route, constraints, failure modes, examples, and proof plans without bloating compact primitive cards.",
        "files": {
            "details": "problem_solution_details_1000.jsonl",
            "solution_patterns": "solution_patterns.jsonl",
            "detail_template": "detail_template.json",
        },
        "detail_count": len(details),
        "solution_pattern_count": len(pattern_rows),
        "source_opportunity_pack": "catalog/knowledge-packs/data/high-priority-primitive-opportunity-rankings/primitive_opportunities_1000.jsonl",
    }
    _write_jsonl(PACK_DIR / "problem_solution_details_1000.jsonl", details)
    _write_jsonl(PACK_DIR / "solution_patterns.jsonl", pattern_rows)
    (PACK_DIR / "detail_template.json").write_text(json.dumps(template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (PACK_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"detail_count": len(details), "solution_pattern_count": len(pattern_rows)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
