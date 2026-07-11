#!/usr/bin/env python3
"""Generate a one-million-row primitive idea seed bundle.

The output is deliberately candidate-only. It is a compact combinatorial
opportunity map for later model/code expansion, not a promoted primitive
registry. Every emitted row keeps candidate=true and serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import collections
import hashlib
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402

TOTAL_ROWS = 1_000_000
ROWS_PER_SHARD = 10_000
BUNDLE_SLUG = "common-software-primitive-seed-bundle-million"
OUTPUT_ROOT = _resource("data") / "dev-intel" / "primitive_million_seed_bundle"
DEFAULT_BUNDLE_DIR = _resource(BUNDLE_SLUG)
DEFAULT_ZIP_PATH = _resource(f"{BUNDLE_SLUG}.zip")
GENERATOR_ID = "scripts.generate_million_primitive_seed_bundle"

KINDS = [
    "primitive",
    "primitive_group",
    "primitive_template",
    "runtime_wrapper",
    "source_adapter",
    "proof_adapter",
    "route_portfolio",
    "negative_memory_seed",
]

FAMILIES = [
    "project_scaffold",
    "environment_config",
    "dependency_bootstrap",
    "healthcheck_endpoint",
    "structured_logging",
    "feature_flag",
    "user_registration",
    "login_session",
    "password_reset",
    "email_verification",
    "mfa_challenge",
    "oauth_oidc_login",
    "api_key_management",
    "service_account",
    "rbac_authorization",
    "abac_authorization",
    "tenant_boundary",
    "csrf_protection",
    "rate_limit",
    "input_validation",
    "output_sanitization",
    "secret_detection",
    "secret_rotation",
    "audit_log",
    "security_header",
    "encryption_at_rest",
    "encryption_in_transit",
    "field_level_encryption",
    "key_management",
    "crud_resource",
    "database_migration",
    "seed_data",
    "soft_delete",
    "search_index",
    "transactional_outbox",
    "cache_layer",
    "file_upload",
    "data_import",
    "data_export",
    "customer_tracker",
    "lead_tracker",
    "support_ticket_tracker",
    "subscription_tracker",
    "order_tracker",
    "inventory_tracker",
    "analytics_tracker",
    "notification_center",
    "landing_page",
    "form_workflow",
    "dashboard",
    "admin_crud_page",
    "settings_page",
    "checkout_flow",
    "onboarding_flow",
    "error_boundary",
    "accessibility_audit",
    "api_gateway",
    "rest_controller",
    "graphql_resolver",
    "grpc_method",
    "webhook_ingest",
    "queue_worker",
    "cron_job",
    "email_service",
    "sms_service",
    "payment_service",
    "ci_workflow",
    "container_build",
    "terraform_deploy",
    "kubernetes_deploy",
    "log_metric_trace",
    "alert_rule",
    "incident_runbook",
    "entity_resolution",
    "entity_enrichment",
    "data_verification",
    "fragile_context_freshness",
    "geography_specific_search",
    "legal_information_search",
    "source_citation",
    "rag_context_filter",
    "tool_call_guardrail",
    "math_visualization",
    "threejs_visualization",
    "web_game_loop",
    "game_engine_system",
    "rendering_pipeline",
    "raytracing_shader",
    "memory_management",
    "algorithmic_transform",
    "distance_similarity",
    "lsh_blocking",
    "leaf_record_processing",
    "bigquery_entity_resolution",
    "splink_entity_resolution",
    "tunable_match_pipeline",
    "inbox_triage",
    "email_check",
    "email_reply",
    "newsletter_send",
    "calendar_schedule",
    "staff_task_queue",
    "approval_workflow",
    "double_check_review",
    "audit_review",
    "complaint_management",
    "refund_management",
    "subscription_management",
    "renewal_management",
    "cancellation_management",
    "customer_success_playbook",
    "support_case_resolution",
    "engineer_oncall_action",
    "code_review_action",
    "incident_response_action",
    "admin_backoffice_action",
    "finance_ops_action",
    "sales_ops_action",
    "hr_ops_action",
    "legal_ops_action",
    "data_merge_review",
    "search_operation",
    "crud_operation",
    "staff_handoff",
    "manager_approval",
    "human_agent_collaboration",
]

ACTIONS = [
    "create",
    "validate",
    "normalize",
    "dedupe",
    "enrich",
    "classify",
    "score",
    "route",
    "sync",
    "reconcile",
    "authorize",
    "redact",
    "encrypt",
    "decrypt",
    "sign",
    "verify",
    "index",
    "search",
    "summarize",
    "extract",
    "transform",
    "load",
    "export",
    "render",
    "simulate",
    "compile",
    "wrap",
    "schedule",
    "retry",
    "rollback",
    "monitor",
    "alert",
    "audit",
    "benchmark",
    "cache",
    "page",
    "paginate",
    "merge",
    "split",
    "rank",
    "cluster",
    "compare",
    "diff",
    "localize",
    "translate",
    "map",
    "project",
    "pivot",
    "join",
    "aggregate",
    "stream",
    "batch",
    "materialize",
    "hydrate",
    "quarantine",
    "approve",
    "escalate",
    "notify",
    "profile",
    "trace",
    "checkpoint",
    "check",
    "read",
    "send",
    "reply",
    "forward",
    "draft",
    "publish",
    "schedule",
    "reschedule",
    "renew",
    "cancel",
    "refund",
    "void",
    "approve",
    "reject",
    "assign",
    "delegate",
    "handoff",
    "follow_up",
    "resolve",
    "close",
    "reopen",
    "double_check",
    "qa_review",
    "audit_review",
    "escalate_to_human",
    "request_info",
    "update_record",
    "delete_record",
    "archive_record",
    "restore_record",
    "create_ticket",
    "merge_records",
    "split_records",
    "search_records",
    "filter_results",
    "export_results",
    "import_records",
    "notify_customer",
    "notify_staff",
    "compose_response",
    "summarize_thread",
    "extract_action_items",
]

OBJECTS = [
    "user",
    "account",
    "session",
    "credential",
    "password_reset_token",
    "mfa_factor",
    "oauth_client",
    "api_key",
    "tenant",
    "role",
    "permission",
    "policy",
    "audit_event",
    "secret",
    "encryption_key",
    "customer",
    "contact",
    "company",
    "lead",
    "opportunity",
    "deal",
    "ticket",
    "invoice",
    "payment",
    "refund",
    "subscription",
    "order",
    "product",
    "sku",
    "inventory_item",
    "shipment",
    "asset",
    "project",
    "task",
    "employee",
    "candidate",
    "vendor",
    "contract",
    "claim",
    "patient",
    "provider",
    "appointment",
    "metric",
    "event",
    "webhook_event",
    "queue_message",
    "notification",
    "email",
    "sms",
    "file",
    "image",
    "document",
    "pdf",
    "csv",
    "jsonl",
    "database_row",
    "table",
    "view",
    "index",
    "search_result",
    "source_ref",
    "citation_span",
    "retrieved_context",
    "tool_call",
    "model_output",
    "prompt",
    "guardrail_decision",
    "receipt",
    "trace_span",
    "metric_window",
    "log_event",
    "incident",
    "deployment",
    "container",
    "kubernetes_job",
    "terraform_module",
    "github_action",
    "api_endpoint",
    "graphql_operation",
    "grpc_method",
    "mcp_tool",
    "browser_page",
    "form_submission",
    "dashboard_widget",
    "chart",
    "map_layer",
    "mesh",
    "shader",
    "texture",
    "game_entity",
    "collision_shape",
    "animation_clip",
    "math_formula",
    "algorithm_trace",
    "similarity_pair",
    "blocking_key",
    "match_cluster",
    "entity_profile",
    "geography_query",
    "legal_query",
    "fragile_fact",
    "email_thread",
    "email_inbox",
    "newsletter",
    "newsletter_campaign",
    "subscriber",
    "unsubscribe_request",
    "reply_draft",
    "calendar_event",
    "meeting_request",
    "staff_task",
    "approval_request",
    "audit_item",
    "review_checklist",
    "double_check_task",
    "complaint",
    "complaint_thread",
    "support_case",
    "issue_report",
    "refund_request",
    "chargeback",
    "cancellation_request",
    "renewal_notice",
    "subscription_plan",
    "subscription_change",
    "crud_record",
    "search_query",
    "search_filter",
    "merge_candidate_pair",
    "merge_review_queue",
    "duplicate_record_cluster",
    "staff_handoff_note",
    "manager_approval",
    "oncall_page",
    "incident_ticket",
    "pull_request",
    "code_review",
    "release_note",
    "runbook_step",
    "customer_message",
    "customer_escalation",
    "billing_adjustment",
    "manual_override",
    "human_review_packet",
]

INDUSTRIES = [
    "horizontal_saas",
    "developer_tools",
    "ecommerce",
    "retail",
    "marketplace",
    "payments",
    "finance_accounting",
    "banking",
    "insurance",
    "healthcare",
    "public_health",
    "clinical_admin",
    "pharma",
    "legal",
    "compliance",
    "government",
    "public_procurement",
    "workforce_development",
    "education",
    "higher_education",
    "real_estate",
    "construction",
    "manufacturing",
    "logistics",
    "transportation",
    "energy",
    "telecom",
    "media",
    "gaming",
    "simulation",
    "geospatial",
    "agriculture",
    "hospitality",
    "travel",
    "nonprofit",
    "research",
    "data_science",
    "ml_platform",
    "cybersecurity",
    "hr_recruiting",
    "customer_support",
    "sales_crm",
    "marketing_growth",
    "product_analytics",
    "iot_edge",
    "warehouse_ops",
    "supply_chain",
    "procurement",
    "enterprise_it",
    "devops_sre",
    "observability",
    "content_ops",
    "creator_tools",
    "math_education",
    "visualization",
    "public_data",
    "local_services",
    "small_business",
    "field_services",
    "security_operations",
]

REGIONS = [
    "global",
    "us",
    "us_state",
    "us_county",
    "us_city",
    "canada",
    "uk",
    "eu",
    "germany",
    "france",
    "spain",
    "italy",
    "netherlands",
    "nordics",
    "india",
    "japan",
    "south_korea",
    "singapore",
    "philippines",
    "australia",
    "new_zealand",
    "brazil",
    "mexico",
    "latin_america",
    "middle_east",
    "africa",
    "timezone_specific",
    "currency_specific",
    "tax_jurisdiction",
    "data_residency_zone",
]

SOURCE_SURFACES = [
    "repo_source",
    "unit_tests",
    "integration_tests",
    "openapi_spec",
    "asyncapi_spec",
    "graphql_schema",
    "protobuf_schema",
    "json_schema",
    "database_schema",
    "dbt_project",
    "terraform_registry",
    "helm_chart",
    "kubernetes_crd",
    "github_actions_marketplace",
    "mcp_registry",
    "pypi_package",
    "npm_package",
    "docker_image",
    "cloud_marketplace",
    "serverless_app",
    "n8n_template",
    "zapier_template",
    "pipedream_component",
    "huggingface_model",
    "model_card",
    "benchmark_task",
    "runtime_trace",
    "otel_trace",
    "browser_trace",
    "api_gateway_log",
    "security_standard",
    "owasp_asvs",
    "nist_guidance",
    "openid_connect_spec",
    "twelve_factor_app",
    "schema_org",
    "fhir_schema",
    "xbrl_taxonomy",
    "gtfs_feed",
    "geojson_dataset",
    "legal_primary_source",
    "government_open_data",
    "vendor_docs",
    "sdk_examples",
]

RUNTIMES = [
    "python_function",
    "typescript_function",
    "fastapi_endpoint",
    "express_endpoint",
    "graphql_resolver",
    "grpc_service",
    "mcp_tool",
    "cli_command",
    "queue_worker",
    "cron_job",
    "webhook_handler",
    "browser_automation",
    "github_action",
    "airflow_task",
    "dagster_asset",
    "prefect_flow",
    "temporal_activity",
    "kubernetes_job",
    "cloud_function",
    "lambda_function",
    "cloud_run_service",
    "container_service",
    "terraform_module",
    "helm_chart",
    "dbt_model",
    "bigquery_sql",
    "postgres_sql",
    "duckdb_script",
    "spark_job",
    "react_component",
    "threejs_scene",
    "game_engine_component",
]

POLICIES = [
    "standard",
    "idempotent",
    "audit_required",
    "tenant_scoped",
    "privacy_preserving",
    "pii_redacted",
    "phi_boundary",
    "pci_boundary",
    "secret_safe",
    "least_privilege",
    "human_review",
    "dual_control",
    "rollback_required",
    "retry_safe",
    "rate_limited",
    "source_cited",
    "freshness_checked",
    "region_locked",
    "license_reviewed",
    "accessibility_required",
    "offline_capable",
    "local_only",
    "cloud_deployable",
    "cost_bounded",
]

PROOFS = [
    "schema_contract_test",
    "unit_test",
    "fixture_test",
    "golden_output_test",
    "property_test",
    "metamorphic_test",
    "differential_test",
    "sandbox_smoke_test",
    "idempotency_test",
    "side_effect_audit",
    "privacy_boundary_test",
    "secret_redaction_test",
    "auth_scope_test",
    "rate_limit_test",
    "rollback_test",
    "source_citation_check",
    "freshness_check",
    "license_gate",
    "security_static_scan",
    "accessibility_check",
    "visual_snapshot_test",
    "performance_benchmark",
    "cost_profile_check",
    "human_review_receipt",
]

MUTATORS = [
    "field_rename",
    "field_project",
    "schema_validator_inserter",
    "type_cast",
    "pagination_expander",
    "retry_wrapper",
    "cache_wrapper",
    "idempotency_wrapper",
    "audit_receipt_wrapper",
    "secret_redactor",
    "policy_gate",
    "source_ref_resolver",
    "runtime_wrapper",
    "artifact_materialize",
    "batch_to_stream",
    "stream_to_batch",
    "route_to_group_card",
    "negative_memory_writer",
]

EFFECTS = [
    "none",
    "file_read",
    "file_write",
    "network_read",
    "network_write",
    "database_read",
    "database_write",
    "secret_read",
    "model_call",
    "browser_action",
    "cloud_resource_create",
    "queue_read",
    "queue_write",
    "audit_log_write",
    "artifact_write",
]

DEVELOPMENT_PATHS = [
    "source_adapter_mining",
    "spec_first_extraction",
    "benchmark_demand_generation",
    "trace_mining",
    "template_slot_fill",
    "deterministic_mutator_chain",
    "plan_delta_to_planlock",
    "compiled_code_artifact",
    "llm_microrepair",
    "human_curated_seed",
    "marketplace_adapter",
    "cooccurrence_grouping",
]

ACTOR_ROLES = [
    "end_user",
    "customer",
    "subscriber",
    "support_agent",
    "customer_success_manager",
    "sales_rep",
    "account_manager",
    "operations_staff",
    "finance_staff",
    "billing_specialist",
    "admin_user",
    "manager",
    "approver",
    "compliance_reviewer",
    "legal_reviewer",
    "data_steward",
    "data_engineer",
    "software_engineer",
    "sre_oncall",
    "security_engineer",
    "qa_reviewer",
    "product_manager",
    "hr_staff",
    "recruiter",
    "procurement_analyst",
    "clinical_admin",
    "claims_adjuster",
    "field_operator",
    "content_editor",
    "newsletter_operator",
    "agentic_worker",
]

WORK_CHANNELS = [
    "web_app",
    "admin_panel",
    "email",
    "newsletter_platform",
    "calendar",
    "chat",
    "slack",
    "sms",
    "phone_call_log",
    "crm",
    "support_desk",
    "billing_portal",
    "subscription_system",
    "erp",
    "warehouse",
    "database_console",
    "spreadsheet",
    "github",
    "gitlab",
    "jira",
    "linear",
    "notion",
    "confluence",
    "incident_tool",
    "siem",
    "cloud_console",
    "kubernetes_dashboard",
    "bi_dashboard",
    "document_system",
    "browser_session",
]

HUMAN_ACTION_GUARDRAILS = [
    "human_approval_required_for_irreversible_actions",
    "draft_before_send",
    "preview_before_mutation",
    "rollback_or_compensation_plan",
    "audit_receipt_required",
    "customer_notice_policy",
    "role_scope_check",
    "tenant_boundary_check",
    "amount_limit_check",
    "rate_limit_and_abuse_check",
    "no_account_enumeration",
    "data_minimization",
]


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")


def _pascal(value: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in _slug(value).split("_") if part)


def _pick(items: list[str], index: int, multiplier: int, salt: int = 0) -> str:
    return items[(index * multiplier + salt) % len(items)]


def _pick_many(items: list[str], index: int, count: int, multiplier: int) -> list[str]:
    return [_pick(items, index, multiplier + offset * 6, salt=offset * 11) for offset in range(count)]


def _priority_score(index: int, family: str, policy: str, proof: str, kind: str) -> int:
    score = 40 + (index % 31)
    if family in {
        "login_session",
        "password_reset",
        "rbac_authorization",
        "tenant_boundary",
        "audit_log",
        "crud_resource",
        "customer_tracker",
        "entity_resolution",
        "data_verification",
        "webhook_ingest",
        "queue_worker",
        "inbox_triage",
        "email_reply",
        "newsletter_send",
        "complaint_management",
        "refund_management",
        "subscription_management",
        "data_merge_review",
        "crud_operation",
        "search_operation",
    }:
        score += 16
    if policy in {"audit_required", "tenant_scoped", "privacy_preserving", "idempotent", "secret_safe"}:
        score += 10
    if proof in {"schema_contract_test", "fixture_test", "idempotency_test", "side_effect_audit"}:
        score += 8
    if kind in {"primitive_group", "route_portfolio", "primitive_template"}:
        score += 6
    return min(score, 100)


def _hidden_edges(action: str, obj: str, family: str, runtime: str) -> list[str]:
    item = _pascal(obj)
    act = _pascal(action)
    fam = _pascal(family)
    return [
        f"{item}Intent -> Validated{item}Envelope",
        f"Validated{item}Envelope -> {fam}{act}Plan",
        f"{fam}{act}Plan+{_pascal(runtime)}Runtime -> {item}Receipt",
    ]


def _row(index: int) -> dict[str, Any]:
    kind = _pick(KINDS, index, 37)
    family = _pick(FAMILIES, index, 7)
    action = _pick(ACTIONS, index, 11)
    obj = _pick(OBJECTS, index, 13)
    industry = _pick(INDUSTRIES, index, 17)
    region = _pick(REGIONS, index, 19)
    source = _pick(SOURCE_SURFACES, index, 23)
    runtime = _pick(RUNTIMES, index, 29)
    policy = _pick(POLICIES, index, 31)
    proof = _pick(PROOFS, index, 41)
    actor_role = _pick(ACTOR_ROLES, index, 59)
    work_channel = _pick(WORK_CHANNELS, index, 61)
    guardrails = _pick_many(HUMAN_ACTION_GUARDRAILS, index, 3, 67)
    mutators = _pick_many(MUTATORS, index, 3, 43)
    effects = _pick_many(EFFECTS, index, 2, 47)
    paths = _pick_many(DEVELOPMENT_PATHS, index, 3, 53)
    obj_name = _pascal(obj)
    family_name = _pascal(family)
    policy_name = _pascal(policy)
    runtime_name = _pascal(runtime)
    source_name = _pascal(source)
    priority = _priority_score(index, family, policy, proof, kind)
    record_basis = (
        f"{kind}|{family}|{action}|{obj}|{industry}|{region}|{source}|{runtime}|"
        f"{policy}|{proof}|{actor_role}|{work_channel}|{index}"
    )
    digest = hashlib.sha256(record_basis.encode("utf-8")).hexdigest()[:16]
    input_edge = f"{obj_name}Intent+{policy_name}Policy+{source_name}Context"
    output_edge = f"{family_name}{obj_name}Receipt+{runtime_name}Artifact"
    return {
        "record_type": "primitive_seed_idea",
        "seed_id": f"seed:primitive:{index:07d}",
        "version": "0.1.0",
        "kind": kind,
        "family": family,
        "title": f"{action.replace('_', ' ')} {obj.replace('_', ' ')} via {family.replace('_', ' ')}",
        "industry": industry,
        "region": region,
        "source_surface": source,
        "runtime_shape": runtime,
        "policy_overlay": policy,
        "actor_role": actor_role,
        "work_channel": work_channel,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "problem_solution_core": {
            "problem": (
                f"{industry.replace('_', ' ')} teams repeatedly need to {action.replace('_', ' ')} "
                f"{obj.replace('_', ' ')} while respecting {policy.replace('_', ' ')} constraints."
            ),
            "solution": (
                f"Use the {family.replace('_', ' ')} route with {runtime.replace('_', ' ')} deployment, "
                f"{source.replace('_', ' ')} evidence, and {proof.replace('_', ' ')} before promotion."
            ),
            "fit_when": f"Use when the request has {obj.replace('_', ' ')} inputs and needs a reusable {family.replace('_', ' ')} building block.",
            "avoid_when": "Avoid promotion until source refs, contract tests, side effects, and receipts are verified.",
            "failure_modes": [
                "schema_drift",
                "missing_auth_or_scope",
                "stale_context",
                "unsafe_side_effect",
            ],
        },
        "human_action_core": {
            "actor_role": actor_role,
            "work_channel": work_channel,
            "action_intent": action,
            "target_object": obj,
            "handoff_boundary": (
                "Agent may draft, validate, route, and prepare receipts; irreversible or externally visible "
                "actions require the row guardrails and policy-specific approval checks."
            ),
            "guardrails": guardrails,
            "receipt_expectation": (
                f"Record who/what initiated the {action.replace('_', ' ')} action, source evidence, "
                "before/after state, approvals, side effects, and rollback or escalation outcome."
            ),
        },
        "group_contract": {
            "visible_input_edge": input_edge,
            "visible_output_edge": output_edge,
            "hidden_member_edges": _hidden_edges(action, obj, family, runtime),
        },
        "building_blocks": [
            family,
            f"{action}_{obj}",
            runtime,
            policy,
        ],
        "mutator_chain": mutators,
        "human_action_guardrails": guardrails,
        "effects": effects,
        "proof_requirements": [proof, "candidate_boundary_check", "source_ref_review"],
        "development_paths": paths,
        "telemetry_signals": [
            "accepted_per_1k_tokens",
            "proof_pass_rate",
            "route_reuse_count",
            "source_read_depth",
            "negative_memory_hits",
        ],
        "rank_features": {
            "priority_score": priority,
            "commonality_score": 50 + index % 50,
            "risk_score": 10 + (index * 3) % 80,
            "cacheability_score": 30 + (index * 5) % 70,
        },
        "iteration_hints": {
            "expand_with_models": ["ollama", "codex", "claude_code", "gemma_4_coding"],
            "checkpoint_group": f"checkpoint:{index // 1000:04d}",
            "recommended_next_step": "expand_contract_then_generate_tests",
            "human_action_expansion": "identify actor, authority, channel, approval threshold, before_after_state, and receipt",
        },
        "evidence_level": "generated_seed",
        "dedupe_key": digest,
        "candidate": True,
        "serves_truth": False,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Primitive seed idea",
        "type": "object",
        "required": [
            "record_type",
            "seed_id",
            "kind",
            "family",
            "input_edge",
            "output_edge",
            "problem_solution_core",
            "proof_requirements",
            "candidate",
            "serves_truth",
        ],
        "properties": {
            "record_type": {"const": "primitive_seed_idea"},
            "seed_id": {"type": "string"},
            "version": {"type": "string"},
            "kind": {"type": "string"},
            "family": {"type": "string"},
            "title": {"type": "string"},
            "industry": {"type": "string"},
            "region": {"type": "string"},
            "source_surface": {"type": "string"},
            "runtime_shape": {"type": "string"},
            "policy_overlay": {"type": "string"},
            "input_edge": {"type": "string"},
            "output_edge": {"type": "string"},
            "problem_solution_core": {"type": "object"},
            "group_contract": {"type": "object"},
            "building_blocks": {"type": "array", "items": {"type": "string"}},
            "mutator_chain": {"type": "array", "items": {"type": "string"}},
            "effects": {"type": "array", "items": {"type": "string"}},
            "proof_requirements": {"type": "array", "items": {"type": "string"}},
            "development_paths": {"type": "array", "items": {"type": "string"}},
            "telemetry_signals": {"type": "array", "items": {"type": "string"}},
            "rank_features": {"type": "object"},
            "iteration_hints": {"type": "object"},
            "evidence_level": {"const": "generated_seed"},
            "dedupe_key": {"type": "string"},
            "candidate": {"const": True},
            "serves_truth": {"const": False},
        },
        "additionalProperties": True,
    }


def _dimensions() -> dict[str, list[str]]:
    return {
        "kinds": KINDS,
        "families": FAMILIES,
        "actions": ACTIONS,
        "objects": OBJECTS,
        "industries": INDUSTRIES,
        "regions": REGIONS,
        "source_surfaces": SOURCE_SURFACES,
        "runtimes": RUNTIMES,
        "policies": POLICIES,
        "proofs": PROOFS,
        "mutators": MUTATORS,
        "effects": EFFECTS,
        "development_paths": DEVELOPMENT_PATHS,
        "actor_roles": ACTOR_ROLES,
        "work_channels": WORK_CHANNELS,
        "human_action_guardrails": HUMAN_ACTION_GUARDRAILS,
    }


def _readme(total_rows: int, shard_count: int) -> str:
    return f"""# Common Software Primitive Seed Bundle

This archive contains {total_rows:,} generated primitive idea seeds split into
{shard_count:,} JSONL shards.

These are not promoted primitives. They are candidate ideas and variation
records for Ollama, Codex, Claude Code, Gemma coding models, and local scripts
to expand, test, rank, checkpoint, reject, or promote later.

Every row keeps:

```text
candidate=true
serves_truth=false
evidence_level=generated_seed
```

## Intended Loop

1. Load one shard at a time.
2. Pick rows by priority_score, family, runtime_shape, policy_overlay, or
   source_surface.
3. Ask a coding model to expand selected rows into full primitive cards,
   primitive templates, primitive groups, route portfolios, wrappers, proof
   adapters, and benchmark demands.
4. Run deterministic validators and proof generators.
5. Write receipts, negative memory, and promotion evidence.
6. Only promote rows after source refs, contracts, effects, tests, privacy, and
   runtime receipts pass.

## Useful Fields

- `problem_solution_core`: problem, solution, fit/avoid conditions, failure modes.
- `human_action_core`: actor, work channel, target action, handoff boundary,
  guardrails, and receipt expectations for user/staff/engineer workflows.
- `group_contract`: visible input/output edges and hidden member edges.
- `building_blocks`: compact components likely to co-occur.
- `mutator_chain`: deterministic adapters likely needed for route compilation.
- `proof_requirements`: checks needed before promotion.
- `rank_features`: cheap initial ranking scores for scheduling.
- `iteration_hints.checkpoint_group`: useful for checkpointed model expansion.

## Archive Layout

```text
manifest.json
schema/primitive_seed_idea.schema.json
dimensions/dimensions.json
samples/sample_100.jsonl
shards/primitive_seed_shard_000.jsonl
...
```

The generator is `{GENERATOR_ID}`.
"""


def generate_bundle(*, bundle_dir: Path, zip_path: Path, total_rows: int, rows_per_shard: int, force: bool) -> dict[str, Any]:
    if total_rows <= 0:
        raise AssertionError("total_rows must be positive")
    if rows_per_shard <= 0:
        raise AssertionError("rows_per_shard must be positive")
    if bundle_dir.exists():
        if not force:
            raise AssertionError(f"{bundle_dir} already exists; pass --force to regenerate")
        shutil.rmtree(bundle_dir)
    if zip_path.exists():
        if not force:
            raise AssertionError(f"{zip_path} already exists; pass --force to regenerate")
        zip_path.unlink()
    started = time.time()
    shards_dir = bundle_dir / "shards"
    samples: list[dict[str, Any]] = []
    family_counts: collections.Counter[str] = collections.Counter()
    kind_counts: collections.Counter[str] = collections.Counter()
    runtime_counts: collections.Counter[str] = collections.Counter()
    shard_count = (total_rows + rows_per_shard - 1) // rows_per_shard

    for shard_index in range(shard_count):
        first = shard_index * rows_per_shard
        last = min(first + rows_per_shard, total_rows)
        shard_path = shards_dir / f"primitive_seed_shard_{shard_index:03d}.jsonl"
        shard_path.parent.mkdir(parents=True, exist_ok=True)
        with shard_path.open("w", encoding="utf-8") as handle:
            for row_index in range(first, last):
                row = _row(row_index)
                family_counts[row["family"]] += 1
                kind_counts[row["kind"]] += 1
                runtime_counts[row["runtime_shape"]] += 1
                if len(samples) < 100:
                    samples.append(row)
                handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")

    _write_json(bundle_dir / "schema" / "primitive_seed_idea.schema.json", _schema())
    _write_json(bundle_dir / "dimensions" / "dimensions.json", _dimensions())
    _write_text(
        bundle_dir / "samples" / "sample_100.jsonl",
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in samples),
    )
    duration = round(time.time() - started, 3)
    manifest = {
        "record_type": "primitive_seed_bundle_manifest",
        "bundle_slug": BUNDLE_SLUG,
        "total_rows": total_rows,
        "rows_per_shard": rows_per_shard,
        "shard_count": shard_count,
        "generator": GENERATOR_ID,
        "version": "0.1.0",
        "candidate": True,
        "serves_truth": False,
        "evidence_level": "generated_seed",
        "family_count": len(FAMILIES),
        "action_count": len(ACTIONS),
        "object_count": len(OBJECTS),
        "industry_count": len(INDUSTRIES),
        "region_count": len(REGIONS),
        "source_surface_count": len(SOURCE_SURFACES),
        "runtime_count": len(RUNTIMES),
        "policy_count": len(POLICIES),
        "proof_count": len(PROOFS),
        "counts_by_kind": dict(sorted(kind_counts.items())),
        "top_family_counts": dict(family_counts.most_common(20)),
        "top_runtime_counts": dict(runtime_counts.most_common(20)),
        "duration_seconds": duration,
        "zip_path": _rel(zip_path),
    }
    _write_json(bundle_dir / "manifest.json", manifest)
    _write_text(bundle_dir / "README.md", _readme(total_rows, shard_count))

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(bundle_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(bundle_dir.parent))
    manifest["zip_size_bytes"] = zip_path.stat().st_size
    _write_json(bundle_dir / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--total-rows", type=int, default=TOTAL_ROWS)
    parser.add_argument("--rows-per-shard", type=int, default=ROWS_PER_SHARD)
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE_DIR)
    parser.add_argument("--zip-path", type=Path, default=DEFAULT_ZIP_PATH)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    manifest = generate_bundle(
        bundle_dir=args.bundle_dir,
        zip_path=args.zip_path,
        total_rows=args.total_rows,
        rows_per_shard=args.rows_per_shard,
        force=args.force,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
