#!/usr/bin/env python3
"""Generate a daily 1k database-backed component-candidate batch."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts._config import POSTGRES_PGVECTOR_DEPLOYMENT_LABEL
from scripts.factory.use_case_seed_rows import export_seed_rows


CORE_INDUSTRY_SURFACES = [
    ("trades.plumbing", "Plumbing contractor procedures", ["permit_requirement", "inspection_check", "code_lookup", "estimate_review", "work_order_triage"]),
    ("trades.hvac", "HVAC installation and service procedures", ["load_calc_check", "commissioning_check", "permit_requirement", "maintenance_triage", "quote_review"]),
    ("trades.electrical", "Electrical contractor procedures", ["safety_gate", "permit_requirement", "inspection_check", "parts_lookup", "change_order_review"]),
    ("automotive.used_cars", "Used car sales and service", ["vehicle_history_check", "pricing_comparison", "warranty_term_extract", "lead_triage", "listing_quality_review"]),
    ("automotive.new_cars", "New car dealership workflows", ["incentive_check", "delivery_checklist", "quote_comparison", "customer_followup", "inventory_match"]),
    ("automotive.brokers", "Auto broker workflows", ["offer_comparison", "fee_disclosure_check", "document_request", "market_scan", "handoff_checklist"]),
    ("energy.oil_gas.offshore", "Offshore oil and gas procedures", ["permit_condition_check", "safety_observation", "maintenance_deferral", "environmental_review", "incident_triage"]),
    ("energy.oil_gas.pipeline", "Oil and gas pipeline operations", ["integrity_check", "anomaly_triage", "right_of_way_review", "maintenance_plan", "regulatory_filing_check"]),
    ("environmental.review", "Environmental review workflows", ["impact_screen", "permit_condition_extract", "public_comment_triage", "mitigation_tracking", "citation_check"]),
    ("animal_hospital", "Animal hospital operations", ["triage_question", "discharge_instruction_check", "inventory_substitution", "followup_scheduler", "procedure_checklist"]),
    ("veterinary.specialty", "Veterinary specialty procedures", ["referral_triage", "diagnostic_evidence_check", "care_plan_review", "client_summary", "handoff_question"]),
    ("woodworking.custom", "Custom woodworking shops", ["quote_scope_extract", "materials_cutlist", "safety_check", "finish_spec_review", "delivery_install_check"]),
    ("construction.residential", "Residential construction workflows", ["change_order_review", "inspection_check", "submittal_extract", "permit_requirement", "punch_list_item"]),
    ("construction.commercial", "Commercial construction workflows", ["rfi_triage", "submittal_review", "pay_app_check", "safety_observation", "schedule_risk"]),
    ("manufacturing.quality", "Manufacturing quality workflows", ["nonconformance_triage", "capa_question", "inspection_plan", "supplier_deviation", "batch_record_check"]),
    ("logistics.last_mile", "Last-mile logistics workflows", ["exception_triage", "route_issue_classify", "delivery_evidence_check", "customer_update", "cost_review"]),
    ("maritime.port", "Port and terminal workflows", ["cargo_exception", "security_check", "berth_schedule_review", "document_match", "incident_triage"]),
    ("aviation.maintenance", "Aircraft maintenance workflows", ["deferral_review", "parts_substitution", "logbook_check", "inspection_interval", "release_gate"]),
    ("finance.aml", "AML analyst workflows", ["alert_question", "entity_link_check", "transaction_pattern", "evidence_packet", "case_narrative_review"]),
    ("banking.complaints", "Bank complaint operations", ["complaint_triage", "policy_match", "evidence_request", "response_quality", "root_cause_label"]),
    ("public_health", "Public health fact workflows", ["source_refresh_check", "fact_version_diff", "guidance_extract", "citation_policy", "review_route"]),
    ("food_quality", "Food quality workflows", ["hold_release_check", "supplier_lot_review", "label_claim_check", "temperature_excursion", "complaint_triage"]),
    ("water_quality", "Water quality workflows", ["sample_plan_check", "lab_result_triage", "public_notice_gate", "source_water_fact", "chain_of_custody_check"]),
    ("social_media.moderation", "Social media moderation workflows", ["policy_label", "appeal_question", "evidence_review", "risk_escalation", "community_rule_match"]),
    ("content_creation", "Content creation workflows", ["brief_extract", "brand_safety_check", "asset_variant_plan", "style_rubric", "publish_gate"]),
]

EXPANDED_INDUSTRY_SURFACES = [
    ("automotive.service", "Automotive service departments", ["repair_order_triage", "diagnostic_evidence_check", "parts_substitution", "estimate_variance_review", "customer_authorization_gate"]),
    ("automotive.fleet", "Fleet maintenance operations", ["telematics_alert_triage", "preventive_maintenance_plan", "driver_defect_report", "downtime_cost_review", "warranty_recovery_check"]),
    ("real_estate.zoning", "Real estate zoning and land use", ["parcel_constraint_extract", "variance_question", "setback_check", "public_hearing_issue", "permit_pathway_review"]),
    ("property.management", "Property management operations", ["work_order_triage", "lease_clause_extract", "vendor_dispatch_check", "resident_notice_gate", "inspection_punch_item"]),
    ("facilities.maintenance", "Facilities maintenance workflows", ["asset_condition_triage", "preventive_task_plan", "vendor_quote_compare", "access_shutdown_notice", "safety_permit_gate"]),
    ("utilities.electric", "Electric utility operations", ["outage_report_triage", "vegetation_risk_review", "interconnection_packet_check", "asset_inspection_extract", "mutual_assist_request"]),
    ("utilities.water", "Water utility operations", ["sample_result_triage", "public_notice_gate", "cross_connection_check", "asset_break_response", "lead_service_line_record"]),
    ("utilities.wastewater", "Wastewater utility operations", ["overflow_event_triage", "permit_limit_check", "lab_chain_of_custody", "maintenance_work_order", "public_report_extract"]),
    ("telecom.field_ops", "Telecom field operations", ["service_ticket_triage", "fiber_splice_record", "permit_path_check", "outage_customer_update", "site_access_gate"]),
    ("cybersecurity.soc", "Security operations center workflows", ["alert_quality_review", "ioc_extract", "ttp_mapping", "false_positive_reason", "escalation_packet"]),
    ("cybersecurity.appsec", "Application security workflows", ["dependency_exception_review", "sast_finding_triage", "threat_model_question", "secret_exposure_gate", "remediation_priority"]),
    ("software.devops", "Software DevOps workflows", ["incident_postmortem_extract", "change_risk_gate", "runbook_step_check", "cost_anomaly_triage", "release_readiness_check"]),
    ("legal.public_law", "Public law and rules workflows", ["citation_resolve", "effective_date_diff", "jurisdiction_label", "public_comment_issue", "rule_change_impact"]),
    ("public_procurement", "Public procurement workflows", ["bid_requirement_extract", "responsiveness_check", "vendor_question", "award_protest_issue", "evaluation_rubric_item"]),
    ("education.special_services", "Education accommodation workflows", ["eligibility_question", "service_plan_check", "meeting_note_extract", "parent_notice_gate", "progress_evidence_request"]),
    ("higher_ed.research_admin", "Higher education research administration", ["irb_intake_check", "grant_compliance_question", "data_management_plan", "conflict_review_gate", "protocol_deviation_triage"]),
    ("healthcare.operations", "Healthcare operations workflows", ["prior_auth_packet_check", "discharge_instruction_review", "critical_result_gate", "coding_evidence_request", "appointment_triage"]),
    ("pharma.quality", "Pharma quality workflows", ["batch_record_exception", "deviation_question", "capa_effectiveness_check", "cold_chain_excursion", "labeling_claim_review"]),
    ("food_service", "Food service operations", ["haccp_check", "temperature_log_review", "allergen_label_gate", "supplier_lot_trace", "complaint_root_cause"]),
    ("agriculture.operations", "Agriculture operations workflows", ["pesticide_use_check", "organic_cert_evidence", "worker_safety_gate", "harvest_record_review", "water_use_record"]),
    ("mining.operations", "Mining operations workflows", ["preshift_exam_check", "incident_triage", "reclamation_obligation_extract", "equipment_defect_gate", "training_record_review"]),
    ("rail.operations", "Rail operations workflows", ["crew_hours_check", "equipment_defect_triage", "hazmat_document_match", "track_work_notice", "incident_evidence_packet"]),
    ("aviation.airport_ops", "Airport operations workflows", ["slot_request_review", "wildlife_hazard_report", "airfield_inspection_item", "tenant_permit_gate", "disruption_response_triage"]),
    ("maritime.shipping", "Maritime shipping workflows", ["cargo_claim_extract", "crew_certification_check", "port_security_gate", "bill_of_lading_match", "schedule_exception_triage"]),
    ("creative.media", "Creative media production workflows", ["brief_to_shotlist", "rights_clearance_check", "brand_safety_rubric", "asset_variant_request", "publish_approval_gate"]),
    ("social_media.community", "Social media community operations", ["group_rule_match", "moderator_queue_triage", "appeal_evidence_check", "spam_pattern_label", "high_risk_escalation"]),
    ("marketplace.seller_ops", "Marketplace seller operations", ["listing_quality_review", "seller_risk_signal", "returns_abuse_triage", "policy_notice_extract", "evidence_request"]),
    ("nonprofit.grants", "Nonprofit grant operations", ["restriction_extract", "reporting_deadline_check", "impact_evidence_request", "budget_variance_review", "donor_notice_gate"]),
    ("government.services", "Government service delivery", ["benefit_eligibility_question", "case_evidence_request", "notice_quality_review", "appeal_issue_label", "accessibility_check"]),
    ("humanitarian.response", "Humanitarian response operations", ["needs_assessment_extract", "resource_gap_label", "site_report_triage", "beneficiary_safeguard_gate", "coordination_update"]),
]

MATRICES = {
    "core": CORE_INDUSTRY_SURFACES,
    "expanded": EXPANDED_INDUSTRY_SURFACES,
    "combined": CORE_INDUSTRY_SURFACES + EXPANDED_INDUSTRY_SURFACES,
}

HIGH_REVIEW_DOMAINS = {
    "finance.aml",
    "public_health",
    "water_quality",
    "food_quality",
    "social_media.moderation",
    "utilities.electric",
    "utilities.water",
    "utilities.wastewater",
    "cybersecurity.soc",
    "cybersecurity.appsec",
    "legal.public_law",
    "public_procurement",
    "education.special_services",
    "higher_ed.research_admin",
    "healthcare.operations",
    "pharma.quality",
    "food_service",
    "agriculture.operations",
    "mining.operations",
    "rail.operations",
    "aviation.airport_ops",
    "maritime.shipping",
    "social_media.community",
    "government.services",
    "humanitarian.response",
}

PIPELINE_STAGES = [
    "source_governance",
    "normalized_object_schema",
    "entity_linking",
    "fuzzy_dedupe",
    "index_record_emission",
    "review_ticket_routing",
]

SOURCE_TYPES = [
    "public_forms",
    "public_guidance",
    "procedure_checklists",
    "standards_indexes",
    "training_materials",
    "workflow_templates",
    "package_registries",
    "government_notices",
]


def _seed_id(domain: str, primitive: str, source_type: str, ordinal: int) -> str:
    return f"daily-{ordinal:04d}-{domain.replace('.', '-')}-{primitive}-{source_type}".replace("_", "-")


def build_daily_seeds(target_count: int = 1000, matrix: str = "core") -> list[dict[str, Any]]:
    if matrix not in MATRICES:
        raise ValueError(f"unknown matrix {matrix!r}; expected one of {', '.join(sorted(MATRICES))}")
    industry_surfaces = MATRICES[matrix]
    seeds: list[dict[str, Any]] = []
    ordinal = 1
    while len(seeds) < target_count:
        for domain, title, primitives in industry_surfaces:
            for primitive in primitives:
                for source_type in SOURCE_TYPES:
                    if len(seeds) >= target_count:
                        break
                    risk_tier = "high" if domain in HIGH_REVIEW_DOMAINS else "medium"
                    seed = {
                        "id": _seed_id(domain, primitive, source_type, ordinal),
                        "title": f"{primitive.replace('_', ' ').title()} from {source_type.replace('_', ' ')} for {title}",
                        "domain": domain.replace(".", "_"),
                        "task": (
                            f"Create a reusable {primitive} component candidate for {title} from {source_type.replace('_', ' ')}. "
                            "Preserve source governance, entity links, dedupe keys, index records, review routing, cost profile, and model-swap metadata."
                        ),
                        "inputs": [source_type, "source_record", "normalized_object"],
                        "outputs": [primitive, "subcomponent", "index_record", "review_ticket", "pipeline_step"],
                        "required_stages": PIPELINE_STAGES,
                        "label_paths": [
                            f"matrix.{matrix}",
                            f"vertical.{domain}",
                            f"primitive.{primitive}",
                            f"source.{source_type}",
                            POSTGRES_PGVECTOR_DEPLOYMENT_LABEL,
                            "customization.pipeline_step",
                        ],
                        "risk_tier": risk_tier,
                        "excluded_scope": ["insurance"],
                    }
                    seeds.append(seed)
                    ordinal += 1
    return seeds


def run_daily_batch(output_dir: str | Path, target_count: int = 1000, matrix: str = "core") -> dict[str, Any]:
    out = Path(output_dir)
    seeds = build_daily_seeds(target_count, matrix=matrix)
    seed_path = out / "daily-component-seeds.jsonl"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text("".join(json.dumps(seed, sort_keys=True, ensure_ascii=True) + "\n" for seed in seeds), encoding="utf-8")
    rows = export_seed_rows(seeds, output_dir=out / "rows", excluded_scopes=["insurance"])
    summary = {
        "ok": True,
        "target_count": target_count,
        "seed_count": len(seeds),
        "seed_path": str(seed_path),
        "matrix": matrix,
        "matrix_surface_count": len(MATRICES[matrix]),
        "row_counts": rows["row_counts"],
        "row_family_paths": rows["row_family_paths"],
        "strategy": "database_backed_component_candidates",
        "notes": [
            "These are database-backed candidate rows, not one YAML file per component.",
            "Use review, dedupe, approval, promotion, and CDC planners before publishing active components.",
            "Wikipedia is optional later; curated source-surface matrices are faster and cleaner for deployable components.",
        ],
    }
    (out / "daily-thousand-component-batch.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _self_test() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        result = run_daily_batch(tmp, target_count=40)
        assert result["seed_count"] == 40
        assert result["matrix"] == "core"
        assert result["row_counts"]["normalized_object"] == 40
        assert result["row_counts"]["index_record"] == 200
        assert result["row_counts"]["object_embedding"] == 40
        expanded = run_daily_batch(Path(tmp) / "expanded", target_count=40, matrix="expanded")
        assert expanded["seed_count"] == 40
        assert expanded["matrix"] == "expanded"
        assert expanded["matrix_surface_count"] == len(EXPANDED_INDUSTRY_SURFACES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="dist/daily-component-batch")
    parser.add_argument("--target-count", type=int, default=1000)
    parser.add_argument("--matrix", choices=sorted(MATRICES), default="core")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print("ok")
        return 0
    print(json.dumps(run_daily_batch(args.output_dir, target_count=args.target_count, matrix=args.matrix), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
