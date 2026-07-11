#!/usr/bin/env python3
"""Generate a 10k real-world build-task corpus for AIDevExplorer benchmarking.

Rows are compatible with the existing AIDevObserver public-codegen use-case
ingestion path (`source_kind=curated_public_codegen_use_case`) and include
extra benchmark fields for measuring whether AIDevExplorer saves time, tokens,
and reinvention by composing primitives.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_MANIFEST_PATH,
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH,
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS,
    AIDEVEXPLORER_TASK_AUDIENCES,
    REPO_ROOT,
)

OUT_PATH = _resource(AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH)
MANIFEST_PATH = _resource(AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_MANIFEST_PATH)


def _slug(value: str) -> str:
    out = []
    prev_dash = False
    for char in value.lower():
        if char.isalnum():
            out.append(char)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    return "".join(out).strip("-") or "task"


def _sha(value: Any, *, n: int = 16) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n]


TASK_ARCHETYPES: list[dict[str, Any]] = [
    {"family":"crud_api","name":"authenticated CRUD API","intent":"Build an authenticated CRUD API with validation, authorization checks, persistence, pagination, and audit receipts.","template":"template.api_validate_authorize_persist_emit","primitives":["api.validate_json_schema","auth.check_scope","db.persist_record","api.paginate_results","audit.emit_receipt"],"groups":["grp:backend.policy_api_request@candidate","grp:teleon.route_to_group_card.collapse@1"],"deliverables":["OpenAPI spec","API handlers","database migration","auth policy tests","audit receipt log"],"pitfalls":["validation added after persistence","role checks copied per endpoint","missing idempotency key","pagination contract drift"],"effects":["db.read","db.write","net.read"]},
    {"family":"webhook_ingestion","name":"webhook ingestion endpoint","intent":"Build a webhook receiver that verifies signatures, validates payloads, dedupes events, persists receipts, and retries downstream work.","template":"template.webhook_validate_dedupe_route","primitives":["api.verify_signature","api.validate_json_schema","event.dedupe_by_idempotency_key","queue.enqueue_job","audit.emit_receipt"],"groups":["grp:opportunity.cross_source_dedupe@candidate"],"deliverables":["webhook endpoint","signature fixtures","idempotency table","retry worker","event receipt report"],"pitfalls":["signature bypass in tests","duplicate event handling ignored","raw payload logged","retry storms"],"effects":["db.write","queue.write","net.read"]},
    {"family":"tenant_settings","name":"multi-tenant settings service","intent":"Build a settings service with tenant overrides, validation, change history, rollback, and typed client access.","template":"template.tenant_settings_validate_version","primitives":["tenant.resolve_context","schema.validate_settings","db.versioned_write","settings.compute_effective_value","audit.emit_change_log"],"groups":["grp:backend.settings_resolution@candidate"],"deliverables":["settings schema","admin API","typed client","rollback command","change audit tests"],"pitfalls":["magic defaults duplicated","tenant override precedence unclear","no rollback path","settings logged with secrets"],"effects":["db.read","db.write"]},
    {"family":"admin_dashboard","name":"role-based admin dashboard","intent":"Build a role-based dashboard with filtered navigation, data tables, forms, loading states, and access-aware actions.","template":"template.frontend_admin_dashboard","primitives":["frontend.generate_routes","auth.filter_navigation","table.render_paginated_grid","form.validate_client_schema","frontend.emit_ui_state_tests"],"groups":["grp:frontend.dashboard_shell@candidate"],"deliverables":["dashboard pages","route guards","data table","form flows","visual smoke tests"],"pitfalls":["buttons visible without permission","loading state missing","mobile table overflow","duplicated filter logic"],"effects":["fs.write","net.read_optional"]},
    {"family":"customer_onboarding_portal","name":"customer portal onboarding flow","intent":"Build a customer onboarding flow with account setup, document upload, status tracking, email notifications, and support escalation.","template":"template.portal_onboarding_workflow","primitives":["form.collect_user_profile","file.validate_upload","workflow.update_status","notification.send_email","support.create_escalation_ticket"],"groups":["grp:workflow.onboarding_status@candidate"],"deliverables":["multi-step UI","upload validation","status model","notification templates","support escalation path"],"pitfalls":["PII retained in logs","resume flow missing","upload errors vague","email retries not tracked"],"effects":["fs.write","db.write","net.write"]},
    {"family":"frontend_quality","name":"accessibility and design-system gate","intent":"Add an automated frontend quality gate for accessibility, design tokens, keyboard navigation, and visual regressions.","template":"template.frontend_component_quality_gate","primitives":["frontend.parse_component","frontend.run_typecheck","frontend.check_design_tokens","frontend.run_a11y_rules","frontend.compare_snapshot"],"groups":["grp:frontend.quality_gate@candidate"],"deliverables":["quality report","CI gate","a11y fixtures","snapshot artifacts","failure triage guide"],"pitfalls":["a11y skipped in CI","tokens hard-coded","snapshot artifacts not stored","keyboard path untested"],"effects":["subprocess","fs.read","fs.write"]},
    {"family":"csv_import_pipeline","name":"CSV vendor import pipeline","intent":"Build a vendor CSV import pipeline with schema inference, alias mapping, dedupe, quarantine, and import receipts.","template":"template.data_ingest_validate_transform_publish","primitives":["file.read_csv_artifact","table.infer_schema","table.rename_columns","record.identity_dedupe","output.emit_import_receipt"],"groups":["grp:teleon.record_import.prepare@1"],"deliverables":["import CLI","schema contract","dedupe report","quarantine file","import receipt"],"pitfalls":["manual schema dict","duplicate rows silently dropped","no quarantine path","column aliases drift"],"effects":["fs.read","fs.write"]},
    {"family":"warehouse_elt","name":"warehouse ELT job","intent":"Build an ELT job that loads source data, validates row counts, transforms tables, publishes lineage, and alerts on drift.","template":"template.warehouse_elt_with_lineage","primitives":["warehouse.load_source_batch","data.validate_row_counts","sql.apply_transform","lineage.emit_event","alert.route_quality_failure"],"groups":["grp:dataset.ingest_contract@candidate","grp:opportunity.lineage_receipt_generation@candidate"],"deliverables":["ELT job","dbt-style contract","lineage event","alert policy","run report"],"pitfalls":["row-count checks absent","lineage not emitted","SQL hard-coded per customer","alert noise"],"effects":["db.read","db.write","net.write_optional"]},
    {"family":"data_quality","name":"schema drift incident analyzer","intent":"Build tooling to detect schema drift, null spikes, volume anomalies, downstream impact, and generate an incident report.","template":"template.data_quality_incident_review","primitives":["schema.diff_versions","data.detect_anomalies","lineage.find_downstream_impact","incident.classify_severity","incident.emit_report"],"groups":["grp:dataset.quality_incident@candidate"],"deliverables":["drift detector","impact graph","incident summary","owner routing","regression fixtures"],"pitfalls":["anomalies lack baseline","downstream impact guessed","incident severity subjective","no replay fixture"],"effects":["db.read","artifact_write"]},
    {"family":"docs_rag_search","name":"internal documentation RAG app","intent":"Build a documentation search app that chunks docs, embeds content, retrieves context, answers with citations, and records evals.","template":"template.rag_index_retrieve_answer","primitives":["docs.load_corpus","text.chunk_documents","embedding.embed_chunks","vector.upsert_index","answer.emit_cited_response"],"groups":["grp:rag.docs_search@candidate"],"deliverables":["crawler","chunking policy","vector index","citation answer API","RAG eval report"],"pitfalls":["chunking ad hoc","citations not span-backed","stale docs not reindexed","eval cases missing"],"effects":["model.call","db.write","fs.read"]},
    {"family":"knowledge_base_migration","name":"knowledge-base migration assistant","intent":"Build a migration assistant that inventories old knowledge-base articles, dedupes topics, rewrites metadata, and validates redirects.","template":"template.knowledge_base_migration","primitives":["docs.inventory_articles","text.cluster_duplicates","metadata.normalize_tags","redirect.validate_links","output.emit_migration_plan"],"groups":["grp:docs.kb_migration@candidate"],"deliverables":["article inventory","topic clusters","metadata mapping","redirect table","migration checklist"],"pitfalls":["duplicate articles migrated","redirects untested","tags inconsistent","stale owners not flagged"],"effects":["fs.read","fs.write","net.read_optional"]},
    {"family":"prompt_eval_harness","name":"prompt evaluation harness","intent":"Build a prompt/model evaluation harness with fixed cases, scoring rubrics, aggregate metrics, and artifacted outputs.","template":"template.experiment_eval_harness","primitives":["eval.load_cases","eval.run_candidate","eval.score_outputs","eval.aggregate_metrics","eval.emit_report"],"groups":["grp:eval.prompt_model_harness@candidate"],"deliverables":["eval cases","runner","rubric scorer","metrics report","output artifacts"],"pitfalls":["cases pasted into prompt","rubric not versioned","outputs overwritten","benchmark treated as truth"],"effects":["model.call","fs.write"]},
    {"family":"agent_tool_permissioning","name":"agent tool permissioning layer","intent":"Build a tool permissioning layer that validates requested actions, checks scopes, redacts secrets, and emits approval receipts.","template":"template.agent_tool_permission_gate","primitives":["tool.parse_request","policy.check_scope","secret.redact_values","approval.require_if_risky","audit.emit_tool_receipt"],"groups":["grp:policy.tool_permission_gate@candidate"],"deliverables":["policy schema","tool gate middleware","redaction tests","approval workflow","audit receipts"],"pitfalls":["tool calls bypass policy","secrets in logs","approval state not durable","scope names duplicated"],"effects":["artifact_write","db.write"]},
    {"family":"ci_hardening","name":"CI pipeline hardening","intent":"Create or harden CI workflows for linting, testing, dependency caching, build artifacts, release permissions, and failure summaries.","template":"template.ci_validate_build_publish","primitives":["repo.detect_package_manager","ci.generate_test_matrix","ci.configure_dependency_cache","ci.run_lint_and_tests","ci.publish_artifacts"],"groups":["grp:devops.ci_quality_gate@candidate"],"deliverables":["CI workflow","cache policy","test matrix","artifact upload","failure digest"],"pitfalls":["overbroad release token","cache key unstable","matrix too slow","logs not summarized"],"effects":["subprocess","fs.write"]},
    {"family":"deployment_readiness","name":"deployment readiness checker","intent":"Build a deployment readiness checker for config, secret references, health checks, rollout safety, rollback plan, and evidence report.","template":"template.deployment_readiness_check","primitives":["deploy.parse_spec","deploy.validate_config","secrets.validate_refs","service.check_health","deploy.emit_readiness_report"],"groups":["grp:devops.deployment_readiness@candidate"],"deliverables":["readiness CLI","config validator","health probes","rollback checklist","report artifact"],"pitfalls":["secret values printed","rollback skipped","health probes flaky","environment drift"],"effects":["subprocess","net.read","fs.write"]},
    {"family":"devops_cloud","name":"Kubernetes manifest validator","intent":"Build a Kubernetes manifest validator that checks resources, probes, policies, namespace ownership, and rollout readiness.","template":"template.kubernetes_manifest_readiness","primitives":["k8s.parse_manifest","k8s.validate_resources","k8s.check_probes","policy.evaluate_rule","deploy.emit_readiness_report"],"groups":["grp:opportunity.group_factory_route_collapse@candidate"],"deliverables":["manifest checker","policy fixtures","readiness report","CI integration","remediation hints"],"pitfalls":["resource limits absent","probe paths wrong","namespace assumptions hard-coded","policy violations unclear"],"effects":["fs.read","subprocess_optional"]},
    {"family":"security_alert_triage","name":"security alert triage workflow","intent":"Build an alert triage workflow that normalizes alerts, enriches IOCs, correlates user activity, scores risk, and routes cases.","template":"template.security_alert_triage","primitives":["security.normalize_alert","security.enrich_ioc","security.correlate_user_activity","security.score_risk","security.route_case"],"groups":["grp:security.alert_triage@candidate"],"deliverables":["normalizer","IOC enrichment cache","risk scorer","case packet","routing policy"],"pitfalls":["alert body sent unredacted","uncached enrichment calls","risk score unexplained","case packet lacks evidence"],"effects":["net.read","db.read","artifact_write"]},
    {"family":"dependency_exception_workflow","name":"dependency exception workflow","intent":"Build a dependency vulnerability exception workflow with SBOM ingest, severity policy, expiry, approval, and audit receipts.","template":"template.dependency_exception_review","primitives":["sbom.parse_bom","vuln.lookup_advisory","policy.evaluate_exception","approval.route_reviewer","audit.emit_exception_receipt"],"groups":["grp:opportunity.supply_chain_proof_packet@candidate"],"deliverables":["SBOM parser","exception policy","approval UI/API","expiry alerts","audit report"],"pitfalls":["exceptions never expire","severity source unclear","license mixed with vuln policy","approval not immutable"],"effects":["net.read","db.write","artifact_write"]},
    {"family":"invoice_approval_workflow","name":"invoice extraction and approval workflow","intent":"Build an invoice extraction workflow with line-item parsing, PO matching, validation, approval routing, and export receipts.","template":"template.invoice_extract_validate_approve","primitives":["document.parse_artifact","invoice.extract_line_items","po.match_purchase_order","policy.evaluate_approval","output.emit_export_receipt"],"groups":["grp:document.invoice_approval@candidate"],"deliverables":["parser","schema contract","matching rules","approval queue","export receipt"],"pitfalls":["free-form JSON extraction","source spans missing","rounding rules unclear","approval state not durable"],"effects":["model.call_optional","fs.read","db.write"]},
    {"family":"contract_obligation_tracking","name":"contract obligation tracker","intent":"Build a contract obligation tracker that extracts duties, dates, owners, renewal terms, and alert schedules with source spans.","template":"template.contract_obligation_tracking","primitives":["document.parse_artifact","contract.extract_obligations","date.normalize_deadlines","owner.resolve_party","alert.schedule_obligation"],"groups":["grp:document.contract_obligations@candidate"],"deliverables":["obligation schema","extraction report","deadline calendar","owner mapping","alert jobs"],"pitfalls":["legal claims without review","dates lack timezone","source spans missing","renewal terms ambiguous"],"effects":["model.call_optional","fs.read","db.write"]},
]


BUSINESS_CONTEXTS: list[dict[str, str]] = [
    {"industry":"saas","area":"product_operations","actor":"product manager","platform":"React + FastAPI + Postgres","data":"customer accounts","size":"startup"},
    {"industry":"ecommerce","area":"orders_and_fulfillment","actor":"ops lead","platform":"Next.js + Shopify API","data":"orders and refunds","size":"small business"},
    {"industry":"fintech","area":"risk_and_compliance","actor":"compliance analyst","platform":"Python + Postgres + event queue","data":"risk cases","size":"regulated team"},
    {"industry":"healthcare","area":"clinical_operations","actor":"operations manager","platform":"Django + secure document store","data":"patient-adjacent operational records","size":"mid-market"},
    {"industry":"legal_services","area":"matter_operations","actor":"paralegal team","platform":"Rails + document store","data":"contracts and matter notes","size":"professional services"},
    {"industry":"marketing_agency","area":"campaign_operations","actor":"account manager","platform":"TypeScript + Airtable API","data":"campaign assets","size":"agency"},
    {"industry":"real_estate","area":"property_operations","actor":"leasing coordinator","platform":"Laravel + MySQL","data":"properties and leases","size":"regional business"},
    {"industry":"logistics","area":"fleet_and_dispatch","actor":"dispatch manager","platform":"Node + Postgres + map API","data":"shipments and routes","size":"operations team"},
    {"industry":"education","area":"student_success","actor":"program coordinator","platform":"Python + LMS API","data":"course and learner records","size":"institution"},
    {"industry":"manufacturing","area":"quality_and_maintenance","actor":"plant engineer","platform":"Python + SQL warehouse","data":"work orders and inspections","size":"enterprise unit"},
    {"industry":"nonprofit","area":"grant_and_donor_operations","actor":"program director","platform":"Google Sheets + serverless API","data":"donors and grants","size":"lean team"},
    {"industry":"government_contractor","area":"procurement_and_capture","actor":"capture manager","platform":"Python + public APIs + Postgres","data":"opportunities and awards","size":"proposal team"},
    {"industry":"insurance","area":"claims_operations","actor":"claims supervisor","platform":"Java + document pipeline","data":"claims and evidence","size":"enterprise"},
    {"industry":"banking","area":"audit_and_controls","actor":"internal auditor","platform":"Python + workflow engine","data":"control evidence","size":"regulated enterprise"},
    {"industry":"retail","area":"merchandising","actor":"category manager","platform":"React + warehouse + vendor feeds","data":"products and inventory","size":"multi-location"},
    {"industry":"hospitality","area":"booking_operations","actor":"guest support manager","platform":"Node + CRM API","data":"reservations and tickets","size":"service team"},
    {"industry":"construction","area":"project_controls","actor":"project manager","platform":"Python + document store + SQL","data":"RFIs and change orders","size":"contractor"},
    {"industry":"media","area":"content_operations","actor":"editorial producer","platform":"Next.js + CMS API","data":"articles and assets","size":"content team"},
    {"industry":"energy","area":"asset_operations","actor":"reliability engineer","platform":"Python + time-series database","data":"sensor alerts","size":"industrial team"},
    {"industry":"human_resources","area":"people_operations","actor":"HR operations lead","platform":"TypeScript + HRIS API","data":"employee workflow records","size":"distributed company"},
    {"industry":"sales","area":"revenue_operations","actor":"revops manager","platform":"Python + CRM API","data":"accounts and opportunities","size":"growth team"},
    {"industry":"customer_support","area":"support_operations","actor":"support lead","platform":"Node + helpdesk API","data":"tickets and macros","size":"support team"},
    {"industry":"data_platform","area":"analytics_engineering","actor":"analytics engineer","platform":"dbt + warehouse + Python","data":"modeled business tables","size":"data team"},
    {"industry":"cybersecurity","area":"security_operations","actor":"SOC analyst","platform":"Python + SIEM API","data":"alerts and incidents","size":"security team"},
    {"industry":"developer_tools","area":"platform_engineering","actor":"platform engineer","platform":"Go + Kubernetes + GitHub Actions","data":"service manifests","size":"engineering org"},
    {"industry":"marketplace","area":"trust_and_safety","actor":"trust analyst","platform":"Python + moderation queue","data":"seller and listing signals","size":"marketplace team"},
    {"industry":"research","area":"knowledge_management","actor":"research operations lead","platform":"Python + vector search","data":"papers and notes","size":"research group"},
    {"industry":"finance_ops","area":"accounts_payable","actor":"AP manager","platform":"Python + ERP API","data":"invoices and vendors","size":"finance team"},
    {"industry":"field_service","area":"workforce_scheduling","actor":"scheduler","platform":"JavaScript + scheduling API","data":"technicians and jobs","size":"field ops team"},
    {"industry":"food_service","area":"supply_chain","actor":"procurement manager","platform":"Python + spreadsheet imports","data":"suppliers and purchase orders","size":"regional chain"},
    {"industry":"telecom","area":"network_operations","actor":"NOC engineer","platform":"Python + metrics API","data":"network alarms","size":"operations center"},
    {"industry":"automotive","area":"warranty_operations","actor":"warranty analyst","platform":"Java + claims database","data":"warranty claims","size":"manufacturer"},
    {"industry":"pharma","area":"quality_systems","actor":"quality specialist","platform":"Python + validated document store","data":"batch and deviation records","size":"regulated team"},
    {"industry":"biotech","area":"lab_operations","actor":"lab operations manager","platform":"Python + LIMS API","data":"samples and experiments","size":"lab team"},
    {"industry":"agriculture","area":"farm_operations","actor":"operations analyst","platform":"Python + geospatial API","data":"fields and applications","size":"agtech team"},
    {"industry":"transportation","area":"safety_compliance","actor":"safety manager","platform":"Python + document workflow","data":"driver and vehicle records","size":"fleet operator"},
    {"industry":"travel","area":"disruption_operations","actor":"travel ops lead","platform":"Node + booking API","data":"itineraries and alerts","size":"travel service"},
    {"industry":"utilities","area":"outage_response","actor":"incident commander","platform":"Python + GIS + work order API","data":"outages and crews","size":"utility"},
    {"industry":"public_sector","area":"case_management","actor":"case supervisor","platform":"Django + secure workflow","data":"case records","size":"agency team"},
    {"industry":"professional_services","area":"client_delivery","actor":"delivery manager","platform":"TypeScript + project management API","data":"project tasks and deliverables","size":"consulting team"},
    {"industry":"architecture_firm","area":"document_control","actor":"project architect","platform":"Python + file store","data":"drawings and submittals","size":"design firm"},
    {"industry":"gaming","area":"live_operations","actor":"live ops producer","platform":"Node + analytics events","data":"player events","size":"game studio"},
    {"industry":"creator_economy","area":"creator_operations","actor":"creator manager","platform":"Next.js + payment API","data":"creator payouts","size":"creator platform"},
    {"industry":"communications","area":"pr_operations","actor":"communications lead","platform":"Python + CMS + media database","data":"press assets","size":"communications team"},
    {"industry":"procurement","area":"supplier_management","actor":"supplier risk analyst","platform":"Python + vendor portal","data":"supplier records","size":"procurement team"},
    {"industry":"training","area":"learning_operations","actor":"training coordinator","platform":"LMS API + warehouse","data":"training completions","size":"enablement team"},
    {"industry":"facilities","area":"maintenance_operations","actor":"facilities manager","platform":"Python + CMMS API","data":"work orders and assets","size":"facilities team"},
    {"industry":"environmental","area":"reporting_compliance","actor":"environmental analyst","platform":"Python + spreadsheet imports","data":"emissions and samples","size":"compliance team"},
    {"industry":"fundraising","area":"donor_operations","actor":"development operations lead","platform":"CRM API + warehouse","data":"gifts and pledges","size":"nonprofit team"},
    {"industry":"subscription_business","area":"billing_operations","actor":"billing operations manager","platform":"Stripe API + Postgres","data":"subscriptions and invoices","size":"SaaS finance team"},
    {"industry":"identity","area":"user_lifecycle","actor":"identity architect","platform":"OIDC provider + service APIs","data":"users, groups, and permissions","size":"platform team"},
    {"industry":"mobile_apps","area":"release_operations","actor":"mobile lead","platform":"React Native + CI + app store APIs","data":"builds and releases","size":"mobile team"},
    {"industry":"open_source","area":"maintainer_operations","actor":"project maintainer","platform":"GitHub API + static site","data":"issues, PRs, and releases","size":"OSS project"},
    {"industry":"freelance_services","area":"client_automation","actor":"freelance developer","platform":"serverless + low-code APIs","data":"client spreadsheets and forms","size":"solo business"},
    {"industry":"agency_services","area":"client_reporting","actor":"technical account lead","platform":"Python + BI exports","data":"client KPIs","size":"agency team"},
    {"industry":"enterprise_it","area":"asset_inventory","actor":"IT operations lead","platform":"Python + CMDB API","data":"devices and software","size":"IT department"},
    {"industry":"privacy","area":"data_rights_operations","actor":"privacy operations manager","platform":"workflow engine + data catalog","data":"DSAR requests","size":"privacy team"},
    {"industry":"advertising","area":"ad_review","actor":"ad operations specialist","platform":"Python + ad platform APIs","data":"ads and claims","size":"ad ops team"},
    {"industry":"supply_chain","area":"inventory_planning","actor":"inventory planner","platform":"warehouse + forecasting scripts","data":"stock and demand","size":"supply chain team"},
    {"industry":"call_center","area":"quality_assurance","actor":"QA supervisor","platform":"Python + transcript store","data":"calls and scorecards","size":"contact center"},
    {"industry":"legaltech","area":"ediscovery","actor":"litigation support analyst","platform":"Python + document review API","data":"documents and custodians","size":"litigation team"},
    {"industry":"govtech","area":"permit_operations","actor":"permit operations lead","platform":"Django + GIS","data":"permits and parcels","size":"municipal team"},
    {"industry":"academic","area":"research_admin","actor":"research administrator","platform":"Python + grants database","data":"proposals and compliance records","size":"university office"},
    {"industry":"payments","area":"dispute_operations","actor":"dispute analyst","platform":"Python + payment processor API","data":"disputes and evidence","size":"payments team"},
    {"industry":"fraud","area":"case_investigation","actor":"fraud operations lead","platform":"Python + graph database","data":"transactions and entities","size":"risk team"},
    {"industry":"sre","area":"incident_management","actor":"SRE lead","platform":"Python + observability APIs","data":"alerts, traces, and runbooks","size":"platform team"},
    {"industry":"api_business","area":"developer_experience","actor":"developer advocate","platform":"OpenAPI + docs site","data":"API specs and examples","size":"DX team"},
    {"industry":"content_platform","area":"moderation_operations","actor":"moderation manager","platform":"Python + queue API","data":"content reports","size":"policy team"},
    {"industry":"sports","area":"club_operations","actor":"operations analyst","platform":"Python + scheduling API","data":"games, rosters, and venues","size":"sports org"},
    {"industry":"events","area":"event_operations","actor":"event producer","platform":"Node + ticketing API","data":"attendees and sessions","size":"events team"},
    {"industry":"construction_safety","area":"site_safety","actor":"safety coordinator","platform":"mobile forms + warehouse","data":"observations and incidents","size":"site team"},
    {"industry":"maritime","area":"cargo_operations","actor":"cargo claims analyst","platform":"Python + document store","data":"shipments and claims","size":"logistics team"},
    {"industry":"aviation","area":"maintenance_operations","actor":"maintenance planner","platform":"Java + work order system","data":"aircraft maintenance records","size":"aviation team"},
    {"industry":"mining","area":"safety_operations","actor":"safety engineer","platform":"Python + incident database","data":"safety observations","size":"mine operator"},
    {"industry":"water_utility","area":"sampling_compliance","actor":"water quality analyst","platform":"Python + lab data imports","data":"sample results","size":"utility team"},
    {"industry":"telehealth","area":"care_operations","actor":"care operations lead","platform":"Django + scheduling API","data":"appointments and care notes","size":"care team"},
    {"industry":"publishing","area":"rights_management","actor":"rights manager","platform":"Python + CMS","data":"licenses and manuscripts","size":"publisher"},
    {"industry":"music_business","area":"royalty_operations","actor":"royalty analyst","platform":"Python + royalty files","data":"plays and payouts","size":"label or distributor"},
    {"industry":"museum","area":"collection_operations","actor":"registrar","platform":"Python + collections database","data":"objects and provenance","size":"museum team"},
    {"industry":"library","area":"digitization_operations","actor":"digital archivist","platform":"Python + OCR pipeline","data":"scans and metadata","size":"library team"},
    {"industry":"insurance_brokerage","area":"policy_servicing","actor":"broker operations lead","platform":"CRM + document automation","data":"policies and renewals","size":"brokerage"},
    {"industry":"property_management","area":"tenant_operations","actor":"property manager","platform":"Node + property management API","data":"tenants and maintenance tickets","size":"property team"},
    {"industry":"loan_servicing","area":"servicing_operations","actor":"servicing analyst","platform":"Java + document workflow","data":"loan records and documents","size":"servicing team"},
    {"industry":"crypto_operations","area":"compliance_operations","actor":"compliance engineer","platform":"Python + blockchain indexer","data":"addresses and transactions","size":"crypto compliance team"},
    {"industry":"weather_risk","area":"risk_operations","actor":"risk analyst","platform":"Python + weather APIs","data":"weather alerts and assets","size":"risk team"},
    {"industry":"renewables","area":"asset_monitoring","actor":"asset manager","platform":"Python + time-series database","data":"inverter and turbine telemetry","size":"renewables operator"},
    {"industry":"robotics","area":"fleet_operations","actor":"robotics operations engineer","platform":"Python + telemetry store","data":"robot events","size":"robotics team"},
    {"industry":"semiconductor","area":"yield_operations","actor":"process engineer","platform":"Python + manufacturing data lake","data":"wafer tests","size":"fab team"},
    {"industry":"chemical","area":"sds_compliance","actor":"EHS specialist","platform":"Python + document store","data":"SDS documents","size":"chemical company"},
    {"industry":"food_manufacturing","area":"recall_operations","actor":"quality manager","platform":"Python + ERP API","data":"lots and shipments","size":"food manufacturer"},
    {"industry":"clinical_trials","area":"trial_operations","actor":"clinical operations lead","platform":"Python + EDC API","data":"protocol deviations","size":"trial team"},
    {"industry":"veterinary","area":"clinic_operations","actor":"clinic manager","platform":"Django + scheduling API","data":"appointments and reminders","size":"clinic"},
    {"industry":"fitness","area":"member_operations","actor":"studio manager","platform":"Node + membership API","data":"members and bookings","size":"fitness business"},
    {"industry":"restaurant","area":"restaurant_operations","actor":"operations manager","platform":"Python + POS exports","data":"sales and inventory","size":"restaurant group"},
    {"industry":"wholesale","area":"order_operations","actor":"operations coordinator","platform":"Laravel + ERP API","data":"orders and inventory","size":"wholesale distributor"},
    {"industry":"charter_school","area":"school_operations","actor":"school operations manager","platform":"Python + SIS API","data":"attendance and enrollment","size":"school network"},
    {"industry":"home_services","area":"service_operations","actor":"owner-operator","platform":"serverless + CRM API","data":"jobs and customers","size":"local business"},
    {"industry":"managed_services","area":"client_it_operations","actor":"MSP engineer","platform":"Python + ticketing API","data":"client tickets and devices","size":"MSP"},
    {"industry":"B2B_marketplace","area":"vendor_operations","actor":"marketplace operations lead","platform":"Python + marketplace API","data":"vendors and listings","size":"B2B marketplace"},
]


VARIANTS: list[dict[str, str]] = [
    {"scope":"MVP for internal users","constraint":"ship in one week with minimal new infrastructure","priority":"speed"},
    {"scope":"production hardening","constraint":"preserve existing customer workflows and add regression tests","priority":"reliability"},
    {"scope":"migration from spreadsheet process","constraint":"support messy historical data and review exceptions","priority":"data_quality"},
    {"scope":"multi-tenant SaaS version","constraint":"isolate tenant data and make policy configurable","priority":"tenant_safety"},
    {"scope":"audit-ready regulated version","constraint":"store evidence receipts and reviewer decisions","priority":"governance"},
    {"scope":"self-service operator tool","constraint":"non-developers must use it repeatedly without support","priority":"usability"},
    {"scope":"API-first integration","constraint":"external partners need typed contracts and stable errors","priority":"contract_quality"},
    {"scope":"cost-reduced automation","constraint":"avoid unnecessary model calls and cache deterministic work","priority":"cost"},
    {"scope":"globalized workflow","constraint":"handle locale, timezone, currency, and language variants","priority":"internationalization"},
    {"scope":"incident-response upgrade","constraint":"diagnose failures quickly and preserve replay evidence","priority":"observability"},
]


def _audience(index: int) -> str:
    return AIDEVEXPLORER_TASK_AUDIENCES[index % len(AIDEVEXPLORER_TASK_AUDIENCES)]


def _complexity(archetype_index: int, variant_index: int) -> str:
    score = (archetype_index % 5) + (variant_index % 4)
    if score <= 2:
        return "small"
    if score <= 5:
        return "medium"
    return "large"


def _reinvention_patterns(base: dict[str, Any], variant: dict[str, str]) -> list[str]:
    patterns = list(base["pitfalls"][:3])
    patterns.append("large context pasted into model instead of retrieving reusable route")
    patterns.append(f"{variant['priority']} logic duplicated across files")
    return patterns


def _acceptance_criteria(base: dict[str, Any], variant: dict[str, str]) -> list[str]:
    return [
        "Visible input/output contract is explicit.",
        "At least one reusable primitive or primitive group is selected before custom code.",
        "Proof artifacts are emitted for success and failure cases.",
        "Side effects, secrets, and persistence boundaries are declared.",
        f"The implementation satisfies the {variant['priority']} priority without hiding review blockers.",
    ]


def _eval_hooks(base: dict[str, Any], variant: dict[str, str], context: dict[str, str]) -> dict[str, Any]:
    return {
        "baseline_runner": "generic_ai_coding_agent_without_primitive_search",
        "candidate_runner": "aidevexplorer_with_primitive_search_and_route_assembly",
        "measurements": [
            "wall_clock_minutes",
            "prompt_tokens",
            "completion_tokens",
            "files_touched",
            "custom_code_lines",
            "primitive_hits",
            "primitive_groups_used",
            "test_pass_rate",
            "pitfalls_avoided",
            "rework_loops",
        ],
        "success_thresholds": {
            "must_use_primitive_or_group": True,
            "must_emit_tests_or_proof": True,
            "must_preserve_candidate_boundary_for_generated_primitives": True,
            "target_token_reduction_percent": 30,
            "target_time_reduction_percent": 25,
        },
        "scenario_priority": variant["priority"],
        "context_platform": context["platform"],
    }


def _row(index: int, archetype: dict[str, Any], context: dict[str, str], variant: dict[str, str]) -> dict[str, Any]:
    audience = _audience(index)
    slug_bits = [context["industry"], archetype["family"], archetype["name"], variant["scope"], audience]
    task_slug = _slug(" ".join(slug_bits))
    task_id = f"aidev-task-{index + 1:05d}-{_sha(slug_bits, n=8)}"
    title = f"{archetype['name'].title()} for {context['area'].replace('_', ' ')} ({variant['scope']})"
    intent = (
        f"{archetype['intent']} Context: a {context['size']} in {context['industry']} needs this for "
        f"{context['area'].replace('_', ' ')}. Primary user: {context['actor']}. Platform: "
        f"{context['platform']}. Data involved: {context['data']}. Constraint: {variant['constraint']}."
    )
    return {
        "id": task_id,
        "slug": task_slug,
        "title": title,
        "source_kind": "curated_public_codegen_use_case",
        "corpus_kind": "aidevexplorer_real_world_build_task",
        "task_family": archetype["family"],
        "industry": context["industry"],
        "business_area": context["area"],
        "audience": audience,
        "team_context": {
            "primary_actor": context["actor"],
            "organization_size": context["size"],
            "platform": context["platform"],
            "data_involved": context["data"],
            "scope": variant["scope"],
            "constraint": variant["constraint"],
            "priority": variant["priority"],
            "complexity": _complexity(index, VARIANTS.index(variant)),
        },
        "intent": intent,
        "expected_template": archetype["template"],
        "expected_primitives": archetype["primitives"],
        "expected_primitive_groups": archetype["groups"],
        "expected_deliverables": archetype["deliverables"],
        "acceptance_criteria": _acceptance_criteria(archetype, variant),
        "observed_reinvention_patterns": _reinvention_patterns(archetype, variant),
        "common_pitfalls": archetype["pitfalls"],
        "artifact_policy": "source_inputs_outputs_tests_and_receipts_as_artifacts",
        "effects": archetype["effects"],
        "aidevexplorer_eval_hooks": _eval_hooks(archetype, variant, context),
        "benchmark_tags": [
            "real_world_build_task",
            audience,
            archetype["family"],
            context["industry"],
            variant["priority"],
        ],
        "source_urls": [],
        "source_status": "curated_synthetic_real_world_task_seed_needs_live_source",
        "license_status": "curated_metadata",
        "trust": "candidate",
        "serves_truth": False,
    }


def generate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for variant in VARIANTS:
        for context in BUSINESS_CONTEXTS:
            for archetype in TASK_ARCHETYPES:
                rows.append(_row(index, archetype, context, variant))
                index += 1
                if len(rows) == AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS:
                    return rows
    raise AssertionError(
        f"generator produced only {len(rows)} rows; target is "
        f"{AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS}"
    )


def write_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    family_counts: dict[str, int] = {}
    industry_counts: dict[str, int] = {}
    audience_counts: dict[str, int] = {}
    for row in rows:
        family_counts[row["task_family"]] = family_counts.get(row["task_family"], 0) + 1
        industry_counts[row["industry"]] = industry_counts.get(row["industry"], 0) + 1
        audience_counts[row["audience"]] = audience_counts.get(row["audience"], 0) + 1
    manifest = {
        "record_type": "aidevexplorer_real_world_task_corpus_manifest",
        "path": AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH,
        "row_count": len(rows),
        "target_row_count": AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS,
        "task_archetypes": len(TASK_ARCHETYPES),
        "business_contexts": len(BUSINESS_CONTEXTS),
        "variants": len(VARIANTS),
        "family_counts": dict(sorted(family_counts.items())),
        "industry_count": len(industry_counts),
        "audience_counts": dict(sorted(audience_counts.items())),
        "source_kind": "curated_public_codegen_use_case",
        "corpus_kind": "aidevexplorer_real_world_build_task",
        "candidate": True,
        "serves_truth": False,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        rows = generate_rows()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    manifest = {
        "row_count": len(rows),
        "target_row_count": AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS,
        "would_write": AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH,
    }
    if not args.check_only:
        manifest = write_rows(rows)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
