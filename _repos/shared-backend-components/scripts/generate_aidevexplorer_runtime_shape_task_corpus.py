#!/usr/bin/env python3
"""Generate runtime-shape reuse tasks for the AIDevExplorer benchmark.

This corpus tests whether the same visible core primitive/group edge can be
exposed through multiple deployable or callable surfaces without rebuilding the
hidden member logic for each surface.
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

from scripts._config import (  # noqa: E402
    AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_MANIFEST_PATH,
    AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_PATH,
    AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_TARGET_ROWS,
    AIDEVEXPLORER_RUNTIME_SHAPES,
    AIDEVEXPLORER_TASK_AUDIENCES,
    REPO_ROOT,
)
from scripts.generate_aidevexplorer_real_world_task_corpus import (  # noqa: E402
    BUSINESS_CONTEXTS,
    TASK_ARCHETYPES,
)

OUT_PATH = _resource(AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_PATH)
MANIFEST_PATH = _resource(AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_MANIFEST_PATH)

SOURCE_KIND = "curated_public_codegen_use_case"
CORPUS_KIND = "aidevexplorer_runtime_shape_reuse_task"


CORE_EDGE_BY_FAMILY: dict[str, dict[str, Any]] = {
    "crud_api": {
        "input": "DomainMutationRequest+AuthPolicy",
        "output": "PersistedResourceReceipt",
        "hidden": [
            "DomainMutationRequest->ValidatedRequest",
            "ValidatedRequest+AuthPolicy->AuthorizationDecision",
            "AuthorizationDecision->PersistencePlan",
            "PersistencePlan->PersistedResourceReceipt",
        ],
    },
    "webhook_ingestion": {
        "input": "WebhookEventEnvelope+DeliveryPolicy",
        "output": "VerifiedDomainEventReceipt",
        "hidden": [
            "WebhookEventEnvelope->SignatureVerification",
            "SignatureVerification->ValidatedWebhookPayload",
            "ValidatedWebhookPayload->IdempotencyDecision",
            "IdempotencyDecision->DomainEventReceipt",
        ],
    },
    "tenant_settings": {
        "input": "TenantContext+SettingsPatch",
        "output": "EffectiveSettingsReceipt",
        "hidden": [
            "TenantContext->SettingSourceOrder",
            "SettingsPatch->ValidatedSettingsPatch",
            "SettingSourceOrder+ValidatedSettingsPatch->EffectiveSettings",
            "EffectiveSettings->EffectiveSettingsReceipt",
        ],
    },
    "admin_dashboard": {
        "input": "SessionContext+AdminDataRequest",
        "output": "AdminDashboardPageModel",
        "hidden": [
            "SessionContext->PermissionFilteredNavigation",
            "AdminDataRequest->PaginatedDataQuery",
            "PaginatedDataQuery->AdminTableModel",
            "PermissionFilteredNavigation+AdminTableModel->AdminDashboardPageModel",
        ],
    },
    "customer_onboarding_portal": {
        "input": "OnboardingProfile+DocumentSet",
        "output": "OnboardingStatusReceipt",
        "hidden": [
            "OnboardingProfile->ValidatedAccountSetup",
            "DocumentSet->ValidatedUploadSet",
            "ValidatedAccountSetup+ValidatedUploadSet->OnboardingWorkflowState",
            "OnboardingWorkflowState->OnboardingStatusReceipt",
        ],
    },
    "frontend_quality": {
        "input": "FrontendComponentSet+QualityPolicy",
        "output": "FrontendQualityReport",
        "hidden": [
            "FrontendComponentSet->ParsedComponentInventory",
            "ParsedComponentInventory+QualityPolicy->DesignTokenCheck",
            "ParsedComponentInventory+QualityPolicy->AccessibilityCheck",
            "DesignTokenCheck+AccessibilityCheck->FrontendQualityReport",
        ],
    },
    "csv_import_pipeline": {
        "input": "RawCsvArtifact+ImportPolicy",
        "output": "ValidatedImportReceipt",
        "hidden": [
            "RawCsvArtifact->ParsedCsvRows",
            "ParsedCsvRows+ImportPolicy->MappedImportRows",
            "MappedImportRows->DedupedImportRows",
            "DedupedImportRows->ValidatedImportReceipt",
        ],
    },
    "warehouse_elt": {
        "input": "SourceBatchRef+LineagePolicy",
        "output": "WarehouseLoadReceipt",
        "hidden": [
            "SourceBatchRef->LoadedSourceBatch",
            "LoadedSourceBatch->RowCountValidation",
            "LoadedSourceBatch->ModeledWarehouseTable",
            "ModeledWarehouseTable+LineagePolicy->WarehouseLoadReceipt",
        ],
    },
    "data_quality": {
        "input": "DatasetSnapshot+QualityPolicy",
        "output": "QualityIncidentReport",
        "hidden": [
            "DatasetSnapshot->SchemaDriftSignal",
            "DatasetSnapshot->AnomalySignalSet",
            "SchemaDriftSignal+AnomalySignalSet->ImpactAssessment",
            "ImpactAssessment+QualityPolicy->QualityIncidentReport",
        ],
    },
    "docs_rag_search": {
        "input": "UserQuestion+CorpusRef+RetrievalPolicy",
        "output": "CitedAnswerReceipt",
        "hidden": [
            "CorpusRef->ChunkedDocumentSet",
            "ChunkedDocumentSet->VectorIndexRef",
            "UserQuestion+VectorIndexRef->RetrievedEvidenceSet",
            "RetrievedEvidenceSet+RetrievalPolicy->CitedAnswerReceipt",
        ],
    },
    "knowledge_base_migration": {
        "input": "KnowledgeBaseExport+MigrationPolicy",
        "output": "KnowledgeBaseMigrationPlan",
        "hidden": [
            "KnowledgeBaseExport->ArticleInventory",
            "ArticleInventory->DuplicateTopicClusters",
            "DuplicateTopicClusters+MigrationPolicy->RedirectPlan",
            "RedirectPlan->KnowledgeBaseMigrationPlan",
        ],
    },
    "prompt_eval_harness": {
        "input": "EvalCaseSet+RubricPolicy+ModelTarget",
        "output": "PromptEvalReport",
        "hidden": [
            "EvalCaseSet+ModelTarget->CandidateOutputSet",
            "CandidateOutputSet+RubricPolicy->ScoredEvalCaseSet",
            "ScoredEvalCaseSet->AggregateEvalMetrics",
            "AggregateEvalMetrics->PromptEvalReport",
        ],
    },
    "agent_tool_permissioning": {
        "input": "ToolCallRequest+PolicySet",
        "output": "ToolPermissionDecisionReceipt",
        "hidden": [
            "ToolCallRequest->ParsedToolAction",
            "ParsedToolAction+PolicySet->ScopeDecision",
            "ScopeDecision->RedactionPlan",
            "RedactionPlan->ToolPermissionDecisionReceipt",
        ],
    },
    "ci_hardening": {
        "input": "RepoProfile+CiPolicy",
        "output": "CiQualityGateReceipt",
        "hidden": [
            "RepoProfile->PackageManagerDecision",
            "PackageManagerDecision+CiPolicy->TestMatrixPlan",
            "TestMatrixPlan->WorkflowArtifactPlan",
            "WorkflowArtifactPlan->CiQualityGateReceipt",
        ],
    },
    "deployment_readiness": {
        "input": "ServiceSpec+RuntimePolicy",
        "output": "DeploymentReadinessReport",
        "hidden": [
            "ServiceSpec->ConfigValidationReport",
            "ServiceSpec->SecretReferenceReport",
            "RuntimePolicy->RolloutSafetyPlan",
            "ConfigValidationReport+SecretReferenceReport+RolloutSafetyPlan->DeploymentReadinessReport",
        ],
    },
    "devops_cloud": {
        "input": "KubernetesManifestSet+ClusterPolicy",
        "output": "KubernetesReadinessReceipt",
        "hidden": [
            "KubernetesManifestSet->ParsedKubernetesObjects",
            "ParsedKubernetesObjects+ClusterPolicy->ResourcePolicyDecision",
            "ParsedKubernetesObjects->ProbeValidationReport",
            "ResourcePolicyDecision+ProbeValidationReport->KubernetesReadinessReceipt",
        ],
    },
    "security_alert_triage": {
        "input": "SecurityAlertBatch+TriagePolicy",
        "output": "SecurityCaseRoutingReceipt",
        "hidden": [
            "SecurityAlertBatch->NormalizedAlertSet",
            "NormalizedAlertSet->EnrichedIndicatorSet",
            "EnrichedIndicatorSet+TriagePolicy->RiskScoreBatch",
            "RiskScoreBatch->SecurityCaseRoutingReceipt",
        ],
    },
    "dependency_exception_workflow": {
        "input": "DependencyFindingBatch+ExceptionPolicy",
        "output": "DependencyExceptionReceipt",
        "hidden": [
            "DependencyFindingBatch->NormalizedAdvisorySet",
            "NormalizedAdvisorySet+ExceptionPolicy->ExceptionDecisionBatch",
            "ExceptionDecisionBatch->ApprovalRoute",
            "ApprovalRoute->DependencyExceptionReceipt",
        ],
    },
    "invoice_approval_workflow": {
        "input": "InvoiceDocumentSet+ApprovalPolicy",
        "output": "InvoiceApprovalReceipt",
        "hidden": [
            "InvoiceDocumentSet->ExtractedInvoiceLineItems",
            "ExtractedInvoiceLineItems->PurchaseOrderMatchSet",
            "PurchaseOrderMatchSet+ApprovalPolicy->ApprovalDecisionBatch",
            "ApprovalDecisionBatch->InvoiceApprovalReceipt",
        ],
    },
    "contract_obligation_tracking": {
        "input": "ContractDocumentSet+ObligationPolicy",
        "output": "ContractObligationReceipt",
        "hidden": [
            "ContractDocumentSet->ExtractedObligationSet",
            "ExtractedObligationSet->NormalizedDeadlineSet",
            "NormalizedDeadlineSet+ObligationPolicy->OwnerAlertPlan",
            "OwnerAlertPlan->ContractObligationReceipt",
        ],
    },
}

RUNTIME_SHAPE_PROFILES: dict[str, dict[str, Any]] = {
    "py.fn": {
        "primitive_kind": "py.fn",
        "input_template": "{core_input}",
        "output_template": "{core_output}",
        "wrapper_edges": [
            "FunctionArgs[{core_input}]->{core_input}",
            "{core_output}->FunctionReturn[{core_output}]",
        ],
        "mutators": ["input_envelope_wrapper", "output_wrapper"],
        "proofs": ["unit_test", "contract_test", "pure_function_or_effect_receipt_test"],
        "effects": [],
    },
    "api.endpoint": {
        "primitive_kind": "api.endpoint",
        "input_template": "HttpRequest[{core_input}]",
        "output_template": "HttpResponse[{core_output}]",
        "wrapper_edges": [
            "HttpRequest[{core_input}]->AuthenticatedRequest",
            "AuthenticatedRequest->{core_input}",
            "{core_output}->HttpResponse[{core_output}]",
        ],
        "mutators": ["api_endpoint_wrapper", "schema_validator_inserter", "idempotency_wrapper", "output_wrapper"],
        "proofs": ["openapi_contract_test", "authz_test", "schema_validation_test", "idempotency_test"],
        "effects": ["network_read"],
    },
    "microservice": {
        "primitive_kind": "service.group",
        "input_template": "ServiceCommandEnvelope[{core_input}]",
        "output_template": "ServiceReceipt[{core_output}]",
        "wrapper_edges": [
            "ServiceCommandEnvelope[{core_input}]->ServiceCommand",
            "ServiceCommand->{core_input}",
            "{core_output}->ServiceReceipt[{core_output}]",
        ],
        "mutators": ["api_endpoint_wrapper", "retry_wrapper", "idempotency_wrapper", "provenance_wrapper"],
        "proofs": ["service_contract_test", "failure_mode_test", "idempotency_test", "observability_receipt_test"],
        "effects": ["network_read", "database_write", "audit_log_write"],
    },
    "webhook.handler": {
        "primitive_kind": "webhook.handler",
        "input_template": "WebhookEventEnvelope[{core_input}]",
        "output_template": "WebhookReceipt[{core_output}]",
        "wrapper_edges": [
            "WebhookEventEnvelope[{core_input}]->SignatureVerification",
            "SignatureVerification->{core_input}",
            "{core_output}->WebhookReceipt[{core_output}]",
        ],
        "mutators": ["schema_validator_inserter", "idempotency_wrapper", "retry_wrapper"],
        "proofs": ["signature_fixture_test", "event_dedupe_test", "replay_safety_test"],
        "effects": ["network_read", "queue_write", "audit_log_write"],
    },
    "queue.consumer": {
        "primitive_kind": "queue.consumer",
        "input_template": "QueueMessage[{core_input}]",
        "output_template": "JobExecutionReceipt[{core_output}]",
        "wrapper_edges": [
            "QueueMessage[{core_input}]->DecodedJobEnvelope",
            "DecodedJobEnvelope->{core_input}",
            "{core_output}->JobExecutionReceipt[{core_output}]",
        ],
        "mutators": ["input_envelope_wrapper", "retry_wrapper", "idempotency_wrapper"],
        "proofs": ["queue_fixture_test", "retry_policy_test", "dead_letter_test"],
        "effects": ["queue_read", "database_write", "audit_log_write"],
    },
    "cron.job": {
        "primitive_kind": "cron.job",
        "input_template": "ScheduleTick+JobPolicy[{core_input}]",
        "output_template": "ScheduledJobReceipt[{core_output}]",
        "wrapper_edges": [
            "ScheduleTick+JobPolicy[{core_input}]->ScheduledJobInput",
            "ScheduledJobInput->{core_input}",
            "{core_output}->ScheduledJobReceipt[{core_output}]",
        ],
        "mutators": ["k8s_cronjob_wrapper", "idempotency_wrapper", "provenance_wrapper"],
        "proofs": ["schedule_policy_test", "idempotent_rerun_test", "missed_run_recovery_test"],
        "effects": ["time_trigger", "database_write", "audit_log_write"],
    },
    "cli.command": {
        "primitive_kind": "cli.command",
        "input_template": "CommandArgs[{core_input}]",
        "output_template": "CliExecutionReceipt[{core_output}]",
        "wrapper_edges": [
            "CommandArgs[{core_input}]->ParsedCommandInput",
            "ParsedCommandInput->{core_input}",
            "{core_output}->CliExecutionReceipt[{core_output}]",
        ],
        "mutators": ["cli_wrapper", "schema_validator_inserter", "output_wrapper"],
        "proofs": ["argv_contract_test", "exit_code_test", "artifact_output_test"],
        "effects": ["subprocess_optional", "artifact_write"],
    },
    "workflow.automation": {
        "primitive_kind": "workflow.step",
        "input_template": "WorkflowState+StepInput[{core_input}]",
        "output_template": "WorkflowStepReceipt[{core_output}]",
        "wrapper_edges": [
            "WorkflowState+StepInput[{core_input}]->WorkflowStepCommand",
            "WorkflowStepCommand->{core_input}",
            "{core_output}->WorkflowStepReceipt[{core_output}]",
        ],
        "mutators": ["input_envelope_wrapper", "retry_wrapper", "provenance_wrapper"],
        "proofs": ["workflow_replay_test", "state_transition_test", "compensation_test"],
        "effects": ["workflow_state_write", "audit_log_write"],
    },
    "kubernetes.job": {
        "primitive_kind": "kubernetes.job",
        "input_template": "KubernetesJobSpec[{core_input}]",
        "output_template": "KubernetesJobReceipt[{core_output}]",
        "wrapper_edges": [
            "KubernetesJobSpec[{core_input}]->ContainerJobInput",
            "ContainerJobInput->{core_input}",
            "{core_output}->KubernetesJobReceipt[{core_output}]",
        ],
        "mutators": ["k8s_job_wrapper", "artifact_reference", "provenance_wrapper"],
        "proofs": ["manifest_contract_test", "resource_limit_test", "job_completion_test"],
        "effects": ["container_run", "artifact_read", "artifact_write"],
    },
    "dashboard.report": {
        "primitive_kind": "dashboard",
        "input_template": "MetricSources[{core_input}]",
        "output_template": "DashboardArtifact[{core_output}]",
        "wrapper_edges": [
            "MetricSources[{core_input}]->DashboardQuerySet",
            "DashboardQuerySet->{core_input}",
            "{core_output}->DashboardArtifact[{core_output}]",
        ],
        "mutators": ["output_wrapper", "artifact_materialize", "cache_wrapper"],
        "proofs": ["dashboard_smoke_test", "empty_state_test", "access_filter_test"],
        "effects": ["database_read", "artifact_write"],
    },
}


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


def _format(template: str, *, core_input: str, core_output: str) -> str:
    return template.format(core_input=core_input, core_output=core_output)


def _shape_profile(runtime_shape: str) -> dict[str, Any]:
    profile = RUNTIME_SHAPE_PROFILES.get(runtime_shape)
    if not profile:
        raise AssertionError(f"missing runtime shape profile: {runtime_shape}")
    return profile


def _core_profile(archetype: dict[str, Any]) -> dict[str, Any]:
    family = str(archetype["family"])
    profile = CORE_EDGE_BY_FAMILY.get(family)
    if not profile:
        raise AssertionError(f"missing core edge profile for family: {family}")
    return profile


def _audience(index: int) -> str:
    return AIDEVEXPLORER_TASK_AUDIENCES[index % len(AIDEVEXPLORER_TASK_AUDIENCES)]


def _row(index: int, archetype: dict[str, Any], context: dict[str, str], runtime_shape: str) -> dict[str, Any]:
    core = _core_profile(archetype)
    shape = _shape_profile(runtime_shape)
    core_input = str(core["input"])
    core_output = str(core["output"])
    core_group_edge = f"{core_input} -> {core_output}"
    input_edge = _format(str(shape["input_template"]), core_input=core_input, core_output=core_output)
    output_edge = _format(str(shape["output_template"]), core_input=core_input, core_output=core_output)
    wrapper_edges = [
        _format(str(edge), core_input=core_input, core_output=core_output)
        for edge in shape["wrapper_edges"]
    ]
    audience = _audience(index)
    slug_bits = [context["industry"], archetype["family"], runtime_shape, audience]
    row_id = f"aidev-runtime-task-{index + 1:05d}-{_sha(slug_bits, n=8)}"
    business_task = (
        f"{archetype['intent']} Context: {context['industry']} / "
        f"{context['area'].replace('_', ' ')} on {context['platform']}."
    )
    return {
        "id": row_id,
        "slug": _slug(" ".join(slug_bits)),
        "title": f"{archetype['name'].title()} as {runtime_shape}",
        "source_kind": SOURCE_KIND,
        "corpus_kind": CORPUS_KIND,
        "business_task": business_task,
        "task_family": archetype["family"],
        "industry": context["industry"],
        "business_area": context["area"],
        "audience": audience,
        "team_context": {
            "primary_actor": context["actor"],
            "organization_size": context["size"],
            "platform": context["platform"],
            "data_involved": context["data"],
            "delivery_context": "runtime_shape_reuse_matrix",
        },
        "primitive_kind": shape["primitive_kind"],
        "runtime_shape": runtime_shape,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "core_group_edge": core_group_edge,
        "wrapper_edges": wrapper_edges,
        "hidden_member_edges": list(core["hidden"]),
        "likely_primitives": archetype["primitives"],
        "expected_primitive_groups": archetype["groups"],
        "adapter_mutators": shape["mutators"],
        "effects": sorted(dict.fromkeys([*archetype["effects"], *shape["effects"]])),
        "proof_requirements": sorted(dict.fromkeys([*shape["proofs"], "core_group_contract_test", "candidate_boundary_gate"])),
        "common_pitfalls": [
            *archetype["pitfalls"],
            "runtime wrapper rebuilds core logic instead of reusing core_group_edge",
            "wrapper adds side effects without declaring proof requirements",
            "hidden member edges are pasted into prompt instead of drilled down only when needed",
        ],
        "aidevexplorer_eval_hooks": {
            "measurements": [
                "core_group_reused",
                "wrapper_edges_preserved",
                "runtime_shape_selected",
                "prompt_tokens",
                "wall_clock_minutes",
                "proof_requirements_preserved",
                "side_effects_declared",
            ],
            "success_thresholds": {
                "must_reuse_core_group_edge": True,
                "must_preserve_wrapper_edges": True,
                "must_emit_tests_or_proof": True,
                "target_token_reduction_percent": 35,
            },
        },
        "benchmark_tags": [
            "runtime_shape_reuse",
            runtime_shape,
            str(shape["primitive_kind"]),
            archetype["family"],
            context["industry"],
        ],
        "source_urls": [],
        "source_status": "curated_synthetic_runtime_shape_seed_needs_live_source",
        "license_status": "curated_metadata",
        "trust": "candidate",
        "candidate": True,
        "serves_truth": False,
    }


def _base_pairs() -> list[tuple[dict[str, Any], dict[str, str]]]:
    runtime_shape_count = len(AIDEVEXPLORER_RUNTIME_SHAPES)
    if AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_TARGET_ROWS % runtime_shape_count != 0:
        raise AssertionError("runtime-shape target row count must divide evenly by runtime shapes")
    base_target = AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_TARGET_ROWS // runtime_shape_count
    pairs: list[tuple[dict[str, Any], dict[str, str]]] = []
    for context in BUSINESS_CONTEXTS:
        for archetype in TASK_ARCHETYPES:
            pairs.append((archetype, context))
            if len(pairs) == base_target:
                return pairs
    raise AssertionError(f"generator produced only {len(pairs)} base tasks; target is {base_target}")


def generate_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for archetype, context in _base_pairs():
        for runtime_shape in AIDEVEXPLORER_RUNTIME_SHAPES:
            rows.append(_row(len(rows), archetype, context, runtime_shape))
    if len(rows) != AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_TARGET_ROWS:
        raise AssertionError(
            f"generator produced {len(rows)} rows; target is "
            f"{AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_TARGET_ROWS}"
        )
    return rows


def write_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    shape_counts: dict[str, int] = {}
    primitive_kind_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    for row in rows:
        shape_counts[row["runtime_shape"]] = shape_counts.get(row["runtime_shape"], 0) + 1
        primitive_kind_counts[row["primitive_kind"]] = primitive_kind_counts.get(row["primitive_kind"], 0) + 1
        family_counts[row["task_family"]] = family_counts.get(row["task_family"], 0) + 1
    manifest = {
        "record_type": "aidevexplorer_runtime_shape_task_corpus_manifest",
        "path": AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_PATH,
        "row_count": len(rows),
        "target_row_count": AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_TARGET_ROWS,
        "base_business_tasks": len(rows) // len(AIDEVEXPLORER_RUNTIME_SHAPES),
        "runtime_shapes": list(AIDEVEXPLORER_RUNTIME_SHAPES),
        "runtime_shape_counts": dict(sorted(shape_counts.items())),
        "primitive_kind_counts": dict(sorted(primitive_kind_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "source_kind": SOURCE_KIND,
        "corpus_kind": CORPUS_KIND,
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
        "target_row_count": AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_TARGET_ROWS,
        "would_write": AIDEVEXPLORER_RUNTIME_SHAPE_TASK_CORPUS_PATH,
    }
    if not args.check_only:
        manifest = write_rows(rows)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
