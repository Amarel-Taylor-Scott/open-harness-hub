#!/usr/bin/env python3
"""Generate ranked high-priority primitive opportunity candidates."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = _resource("catalog/knowledge-packs/data/high-priority-primitive-opportunity-rankings")
SOURCE_STATUS = "curated_priority_seed_needs_source_ref_resolution"

COMMON_ROW = {
    "candidate": True,
    "serves_truth": False,
    "source_refs": [],
    "source_evidence_status": SOURCE_STATUS,
}


MODULE_SPECIALTIES: list[dict[str, Any]] = [
    {
        "module_id": "module:entity_resolution",
        "title": "Entity resolution",
        "base_score": 96,
        "input_edge": "RawEntityMentionSet+IdentityPolicy+SourceContext",
        "output_edge": "ResolvedEntitySet+IdentityResolutionReceipt",
        "transformations": ["normalize_identifiers", "blocking_key_generate", "fuzzy_match", "conflict_receipt_emit"],
        "proof_requirements": ["golden_match_fixture", "false_merge_test", "source_id_preservation_test"],
    },
    {
        "module_id": "module:entity_enrichment",
        "title": "Entity enrichment",
        "base_score": 92,
        "input_edge": "ResolvedEntitySet+EnrichmentPolicy+SourceCatalog",
        "output_edge": "EnrichedEntityProfileSet+EnrichmentReceipt",
        "transformations": ["source_select", "attribute_fetch", "confidence_score", "provenance_attach"],
        "proof_requirements": ["source_ref_resolution", "attribute_fixture_test", "staleness_receipt"],
    },
    {
        "module_id": "module:data_verification",
        "title": "Data verification",
        "base_score": 95,
        "input_edge": "ClaimOrRecordSet+VerificationPolicy+SourceHierarchy",
        "output_edge": "VerifiedOrDisputedRecordSet+VerificationReceipt",
        "transformations": ["source_rank", "cross_check", "conflict_detect", "evidence_span_attach"],
        "proof_requirements": ["source_hierarchy_test", "conflict_fixture_test", "evidence_span_check"],
    },
    {
        "module_id": "module:related_data_search",
        "title": "Related data search",
        "base_score": 88,
        "input_edge": "SeedEntityOrTopic+SearchPolicy+SourceSurfaceSet",
        "output_edge": "RelatedRecordCandidateSet+SearchReceipt",
        "transformations": ["query_expand", "source_route", "dedupe_results", "rank_candidates"],
        "proof_requirements": ["query_fixture_test", "dedupe_test", "ranking_reason_receipt"],
    },
    {
        "module_id": "module:fragile_context_monitoring",
        "title": "Fragile context monitoring",
        "base_score": 94,
        "input_edge": "ContextFactSet+FreshnessPolicy+ChangeSignalSet",
        "output_edge": "FreshnessRiskDigest+RefreshPlan",
        "transformations": ["fragility_classify", "effective_date_extract", "change_signal_search", "refresh_priority_rank"],
        "proof_requirements": ["freshness_fixture_test", "effective_date_check", "NeedsRefresh_receipt"],
    },
    {
        "module_id": "module:geography_specific_search",
        "title": "Geography-specific search",
        "base_score": 90,
        "input_edge": "GeoScope+TaskIntent+SourcePolicy",
        "output_edge": "GeoScopedSourceBundle+JurisdictionReceipt",
        "transformations": ["country_normalize", "subjurisdiction_expand", "local_source_route", "geo_scope_receipt_emit"],
        "proof_requirements": ["country_code_test", "local_source_ref_check", "jurisdiction_scope_receipt"],
    },
    {
        "module_id": "module:legal_information_search",
        "title": "Legal information search",
        "base_score": 91,
        "input_edge": "LegalQuestion+JurisdictionPolicy+SourceHierarchy",
        "output_edge": "LegalSourceCandidateSet+LegalSearchReceipt",
        "transformations": ["jurisdiction_scope", "authority_rank", "effective_date_check", "quote_span_attach"],
        "proof_requirements": ["official_source_check", "effective_date_check", "human_review_trigger_test"],
    },
    {
        "module_id": "module:source_ref_resolution",
        "title": "Source reference resolution",
        "base_score": 93,
        "input_edge": "UrlOrPackageOrDocumentRef+SourcePolicy",
        "output_edge": "ResolvedSourceRefBundle+LicenseReviewObligation",
        "transformations": ["source_normalize", "canonical_url_resolve", "license_hint_extract", "snapshot_receipt_emit"],
        "proof_requirements": ["source_resolves_test", "license_gate_check", "snapshot_receipt_test"],
    },
    {
        "module_id": "module:temporal_freshness_tracking",
        "title": "Temporal freshness tracking",
        "base_score": 87,
        "input_edge": "SourceRecordSet+FreshnessPolicy+Clock",
        "output_edge": "FreshnessReceiptSet+RefreshQueue",
        "transformations": ["captured_at_record", "effective_date_extract", "ttl_apply", "refresh_queue_rank"],
        "proof_requirements": ["ttl_fixture_test", "effective_date_fixture_test", "refresh_queue_test"],
    },
    {
        "module_id": "module:jurisdiction_policy_mapping",
        "title": "Jurisdiction policy mapping",
        "base_score": 89,
        "input_edge": "CountryRegionIndustryScope+PolicyQuestion",
        "output_edge": "JurisdictionPolicyMap+PolicyGapReceipt",
        "transformations": ["jurisdiction_expand", "policy_source_route", "rule_extract", "gap_receipt_emit"],
        "proof_requirements": ["jurisdiction_scope_test", "policy_source_ref_check", "conflict_receipt_test"],
    },
    {
        "module_id": "module:data_quality_profiling",
        "title": "Data quality profiling",
        "base_score": 86,
        "input_edge": "DatasetOrRecordBatch+QualityPolicy",
        "output_edge": "QualityProfileReport+RejectedRowManifest",
        "transformations": ["schema_profile", "null_pattern_detect", "outlier_detect", "quality_rule_score"],
        "proof_requirements": ["profile_fixture_test", "rejected_row_manifest_test", "quality_rule_receipt"],
    },
    {
        "module_id": "module:schema_mapping_normalization",
        "title": "Schema mapping and normalization",
        "base_score": 90,
        "input_edge": "SourceSchema+TargetSchema+MappingPolicy",
        "output_edge": "SchemaMapCandidate+MappingGapReceipt",
        "transformations": ["field_alias_resolve", "type_map", "enum_map", "required_field_gate"],
        "proof_requirements": ["mapping_fixture_test", "enum_gap_test", "roundtrip_test"],
    },
    {
        "module_id": "module:relationship_graph_extraction",
        "title": "Relationship graph extraction",
        "base_score": 84,
        "input_edge": "DocumentOrRecordSet+EntitySet+RelationPolicy",
        "output_edge": "RelationshipGraph+GraphEvidenceReceipt",
        "transformations": ["relation_extract", "edge_confidence_score", "source_span_attach", "graph_dedupe"],
        "proof_requirements": ["relation_fixture_test", "source_span_check", "graph_consistency_test"],
    },
    {
        "module_id": "module:adverse_media_risk_discovery",
        "title": "Adverse media and risk discovery",
        "base_score": 82,
        "input_edge": "ResolvedEntity+RiskSearchPolicy+SourceSurfaceSet",
        "output_edge": "RiskSignalCandidateSet+ReviewPacket",
        "transformations": ["query_expand", "source_screen", "risk_signal_classify", "review_packet_emit"],
        "proof_requirements": ["source_ref_resolution", "false_positive_review", "human_review_receipt"],
    },
    {
        "module_id": "module:sanctions_watchlist_screening",
        "title": "Sanctions and watchlist screening",
        "base_score": 85,
        "input_edge": "ResolvedEntitySet+WatchlistSnapshot+ScreeningPolicy",
        "output_edge": "ScreeningCandidateSet+ScreeningReceipt",
        "transformations": ["name_normalize", "watchlist_match", "score_threshold", "review_queue_route"],
        "proof_requirements": ["watchlist_snapshot_receipt", "match_fixture_test", "false_positive_review"],
    },
    {
        "module_id": "module:document_extraction_evidence",
        "title": "Document extraction with evidence",
        "base_score": 88,
        "input_edge": "DocumentArtifact+ExtractionSchema+EvidencePolicy",
        "output_edge": "ExtractedFieldSet+EvidenceSpanReceipt",
        "transformations": ["layout_parse", "field_extract", "table_extract", "evidence_span_attach"],
        "proof_requirements": ["document_fixture_test", "field_accuracy_check", "evidence_span_check"],
    },
    {
        "module_id": "module:citation_span_verification",
        "title": "Citation span verification",
        "base_score": 89,
        "input_edge": "DraftAnswer+SourceSpanSet+CitationPolicy",
        "output_edge": "CitationValidationReceipt+UnsupportedClaimSet",
        "transformations": ["claim_extract", "span_match", "support_score", "unsupported_claim_emit"],
        "proof_requirements": ["citation_fixture_test", "unsupported_claim_test", "source_span_check"],
    },
    {
        "module_id": "module:license_terms_review",
        "title": "License and terms review",
        "base_score": 80,
        "input_edge": "SourceRefBundle+LicensePolicy+UseCase",
        "output_edge": "LicenseReviewReceipt+UseRestrictionSet",
        "transformations": ["license_extract", "terms_hint_extract", "compatibility_score", "restriction_receipt_emit"],
        "proof_requirements": ["license_source_ref_check", "compatibility_fixture_test", "review_receipt_test"],
    },
    {
        "module_id": "module:privacy_boundary_classification",
        "title": "Privacy boundary classification",
        "base_score": 92,
        "input_edge": "DataArtifact+PrivacyPolicy+TenantContext",
        "output_edge": "PrivacyBoundaryDecision+PrivacyReceipt",
        "transformations": ["data_classify", "tenant_scope_check", "purpose_limit_check", "redaction_plan_emit"],
        "proof_requirements": ["classification_fixture_test", "tenant_boundary_test", "redaction_plan_test"],
    },
    {
        "module_id": "module:proof_receipt_generation",
        "title": "Proof receipt generation",
        "base_score": 91,
        "input_edge": "ExecutionTrace+ProofPolicy+SourceRefBundle",
        "output_edge": "ProofReceipt+PromotionAdvice",
        "transformations": ["trace_hash", "source_ref_attach", "test_result_attach", "promotion_gate_score"],
        "proof_requirements": ["receipt_schema_test", "trace_hash_test", "promotion_gate_fixture"],
    },
]

INDUSTRIES: list[dict[str, Any]] = [
    {"industry_id": "industry:healthcare", "title": "Healthcare", "risk": 9, "demand": 9, "geo_legal": 9, "source_surfaces": ["provider_directories", "clinical_docs", "payer_portals"]},
    {"industry_id": "industry:finance", "title": "Finance", "risk": 9, "demand": 9, "geo_legal": 8, "source_surfaces": ["regulators", "market_data", "bank_exports"]},
    {"industry_id": "industry:insurance", "title": "Insurance", "risk": 8, "demand": 8, "geo_legal": 8, "source_surfaces": ["policy_docs", "claim_exports", "regulators"]},
    {"industry_id": "industry:legal", "title": "Legal", "risk": 9, "demand": 8, "geo_legal": 9, "source_surfaces": ["statutes", "case_law", "contract_repositories"]},
    {"industry_id": "industry:government_procurement", "title": "Government procurement", "risk": 8, "demand": 8, "geo_legal": 9, "source_surfaces": ["solicitation_portals", "award_databases", "agency_docs"]},
    {"industry_id": "industry:education", "title": "Education", "risk": 7, "demand": 7, "geo_legal": 7, "source_surfaces": ["school_catalogs", "student_systems", "program_pages"]},
    {"industry_id": "industry:ecommerce", "title": "Ecommerce", "risk": 6, "demand": 9, "geo_legal": 6, "source_surfaces": ["shop_platforms", "payment_processors", "marketplaces"]},
    {"industry_id": "industry:retail", "title": "Retail", "risk": 6, "demand": 8, "geo_legal": 6, "source_surfaces": ["pos_exports", "catalog_feeds", "inventory_systems"]},
    {"industry_id": "industry:logistics", "title": "Logistics", "risk": 7, "demand": 8, "geo_legal": 8, "source_surfaces": ["tracking_feeds", "route_data", "carrier_portals"]},
    {"industry_id": "industry:manufacturing", "title": "Manufacturing", "risk": 7, "demand": 7, "geo_legal": 6, "source_surfaces": ["erp_exports", "quality_records", "supplier_docs"]},
    {"industry_id": "industry:construction", "title": "Construction", "risk": 7, "demand": 7, "geo_legal": 7, "source_surfaces": ["rfi_logs", "submittals", "permit_docs"]},
    {"industry_id": "industry:real_estate", "title": "Real estate", "risk": 7, "demand": 7, "geo_legal": 9, "source_surfaces": ["property_records", "listings", "zoning_docs"]},
    {"industry_id": "industry:energy", "title": "Energy", "risk": 8, "demand": 6, "geo_legal": 8, "source_surfaces": ["asset_registry", "regulatory_filings", "sensor_feeds"]},
    {"industry_id": "industry:telecom", "title": "Telecom", "risk": 7, "demand": 6, "geo_legal": 7, "source_surfaces": ["network_inventory", "tickets", "coverage_maps"]},
    {"industry_id": "industry:media", "title": "Media", "risk": 6, "demand": 7, "geo_legal": 6, "source_surfaces": ["content_feeds", "rights_docs", "ad_platforms"]},
    {"industry_id": "industry:nonprofit", "title": "Nonprofit", "risk": 6, "demand": 6, "geo_legal": 7, "source_surfaces": ["grant_portals", "donor_exports", "program_reports"]},
    {"industry_id": "industry:agriculture", "title": "Agriculture", "risk": 6, "demand": 6, "geo_legal": 8, "source_surfaces": ["farm_records", "weather_data", "regulatory_docs"]},
    {"industry_id": "industry:hospitality", "title": "Hospitality", "risk": 5, "demand": 7, "geo_legal": 6, "source_surfaces": ["booking_systems", "review_sites", "pos_exports"]},
    {"industry_id": "industry:cybersecurity", "title": "Cybersecurity", "risk": 9, "demand": 9, "geo_legal": 6, "source_surfaces": ["advisories", "sboms", "logs"]},
    {"industry_id": "industry:devtools_saas", "title": "Devtools and SaaS", "risk": 7, "demand": 9, "geo_legal": 5, "source_surfaces": ["repos", "issue_trackers", "telemetry"]},
    {"industry_id": "industry:public_health", "title": "Public health", "risk": 9, "demand": 7, "geo_legal": 9, "source_surfaces": ["health_agency_docs", "surveillance_feeds", "clinic_lists"]},
    {"industry_id": "industry:workforce", "title": "Workforce", "risk": 7, "demand": 8, "geo_legal": 8, "source_surfaces": ["job_boards", "training_catalogs", "labor_rules"]},
    {"industry_id": "industry:transportation", "title": "Transportation", "risk": 7, "demand": 7, "geo_legal": 8, "source_surfaces": ["gtfs_feeds", "road_networks", "agency_alerts"]},
    {"industry_id": "industry:supply_chain", "title": "Supply chain", "risk": 8, "demand": 8, "geo_legal": 8, "source_surfaces": ["supplier_master", "shipment_docs", "trade_data"]},
    {"industry_id": "industry:research_science", "title": "Research and science", "risk": 6, "demand": 7, "geo_legal": 5, "source_surfaces": ["papers", "datasets", "protocols"]},
]

VARIANTS = [
    {"variant_id": "variant:fast_triage", "title": "Fast triage", "score_delta": 0, "runtime_targets": ["api.endpoint", "py.fn", "queue.consumer"], "proof_extra": ["smoke_test"]},
    {"variant_id": "variant:evidence_grade", "title": "Evidence grade", "score_delta": 4, "runtime_targets": ["workflow.step", "queue.consumer", "dashboard.report"], "proof_extra": ["source_ref_resolution", "review_packet_receipt"]},
]


def _slug(value: str) -> str:
    return value.split(":", 1)[1].replace("_", "-")


def _score(module: dict[str, Any], industry: dict[str, Any], variant: dict[str, Any]) -> float:
    score = (
        module["base_score"] * 0.55
        + industry["risk"] * 2.0
        + industry["demand"] * 2.0
        + industry["geo_legal"] * 1.2
        + variant["score_delta"]
    )
    if module["module_id"] in {
        "module:entity_resolution",
        "module:data_verification",
        "module:fragile_context_monitoring",
        "module:source_ref_resolution",
        "module:privacy_boundary_classification",
        "module:proof_receipt_generation",
    }:
        score += 3
    if industry["industry_id"] in {"industry:healthcare", "industry:finance", "industry:cybersecurity", "industry:public_health"}:
        score += 2
    return round(min(score, 100.0), 2)


def _opportunity_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for module in MODULE_SPECIALTIES:
        for industry in INDUSTRIES:
            for variant in VARIANTS:
                score = _score(module, industry, variant)
                row = {
                    "record_type": "high_priority_primitive_opportunity",
                    "opportunity_id": f"opp:{_slug(module['module_id'])}.{_slug(industry['industry_id'])}.{_slug(variant['variant_id'])}",
                    "module_id": module["module_id"],
                    "module_title": module["title"],
                    "industry_id": industry["industry_id"],
                    "industry_title": industry["title"],
                    "variant_id": variant["variant_id"],
                    "variant_title": variant["title"],
                    "priority_score": score,
                    "input_edge": module["input_edge"],
                    "output_edge": module["output_edge"],
                    "transformations": module["transformations"],
                    "runtime_targets": variant["runtime_targets"],
                    "source_surface_hints": industry["source_surfaces"],
                    "proof_requirements": sorted(set(module["proof_requirements"] + variant["proof_extra"])),
                    "ranking_features": {
                        "module_base_score": module["base_score"],
                        "industry_risk": industry["risk"],
                        "industry_demand": industry["demand"],
                        "geo_legal_sensitivity": industry["geo_legal"],
                        "variant_score_delta": variant["score_delta"],
                    },
                    "materialization_policy": "materialize_hot_or_proof_backed",
                    "negative_memory_queries": [
                        f"{module['title'].lower()} false positive",
                        f"{industry['title'].lower()} source stale",
                        "missing source receipt",
                    ],
                    **COMMON_ROW,
                }
                rows.append(row)
    rows.sort(key=lambda item: (-item["priority_score"], item["module_id"], item["industry_id"], item["variant_id"]))
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


def _with_common(row: dict[str, Any], record_type: str) -> dict[str, Any]:
    return {"record_type": record_type, **row, **COMMON_ROW}


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    opportunity_rows = _opportunity_rows()
    module_rows = [_with_common(row, "high_priority_primitive_module_specialty") for row in MODULE_SPECIALTIES]
    industry_rows = [_with_common(row, "high_priority_primitive_industry_priority") for row in INDUSTRIES]
    variant_rows = [_with_common(row, "high_priority_primitive_route_variant") for row in VARIANTS]

    _write_jsonl(PACK_DIR / "primitive_opportunities_1000.jsonl", opportunity_rows)
    _write_jsonl(PACK_DIR / "module_specialty_catalog.jsonl", module_rows)
    _write_jsonl(PACK_DIR / "industry_priority_matrix.jsonl", industry_rows)
    _write_jsonl(PACK_DIR / "route_variants.jsonl", variant_rows)

    scoring_model = {
        "record_type": "high_priority_primitive_scoring_model",
        "candidate": True,
        "serves_truth": False,
        "formula": "module_base_score*0.55 + industry_risk*2 + industry_demand*2 + geo_legal_sensitivity*1.2 + variant_delta + selected bonuses",
        "materialization_policy": "rank candidates, materialize hot or proof-backed combinations only",
        "source_status": SOURCE_STATUS,
    }
    (PACK_DIR / "scoring_model.json").write_text(json.dumps(scoring_model, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "record_type": "high_priority_primitive_opportunity_rankings_manifest",
        "pack_id": "high-priority-primitive-opportunity-rankings",
        "version": "0.1.0",
        "candidate": True,
        "serves_truth": False,
        "source_status": SOURCE_STATUS,
        "description": "Ranked candidate primitive opportunities across high-value module specialties, industries, route variants, input/output edges, transformations, and proof requirements.",
        "files": {
            "primitive_opportunities": "primitive_opportunities_1000.jsonl",
            "module_specialties": "module_specialty_catalog.jsonl",
            "industry_priority_matrix": "industry_priority_matrix.jsonl",
            "route_variants": "route_variants.jsonl",
            "scoring_model": "scoring_model.json",
        },
        "module_specialty_count": len(MODULE_SPECIALTIES),
        "industry_count": len(INDUSTRIES),
        "route_variant_count": len(VARIANTS),
        "opportunity_count": len(opportunity_rows),
        "top_module_families": [
            "entity_resolution",
            "entity_enrichment",
            "data_verification",
            "related_data_search",
            "fragile_context_monitoring",
            "geography_specific_search",
            "legal_information_search",
            "source_ref_resolution",
            "privacy_boundary_classification",
            "proof_receipt_generation",
        ],
    }
    (PACK_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"opportunity_count": len(opportunity_rows), "module_specialty_count": len(MODULE_SPECIALTIES), "industry_count": len(INDUSTRIES)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
