"""Larger deterministic primitive groups.

These functions intentionally group common low-level operations behind one
contract. AIDevObserver can expose the compact group edge to a planning model
while keeping the normalizing, deduping, ordering, hashing, and file-safety
details out of the first context packet.
"""
from __future__ import annotations

from src.teleon.experiments.ids import sha256_hex
import json
import re
import shutil
import unicodedata
from collections import deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_FINGERPRINT_CHARS = 16
IDEMPOTENCY_DIGEST_CHARS = 24
FILE_DIGEST_CHARS = 24
RECEIPT_DIGEST_CHARS = 24
MANIFEST_NAME = "manifest.jsonl"
DEFAULT_ROUTE_MAX_STEPS = 12
NO_ROUTE_REASON = "unreached_goal"
KEEP_FIRST = "first"
KEEP_LAST = "last"

_FIRST_CAP_RE = re.compile(r"(.)([A-Z][a-z]+)")
_ALL_CAP_RE = re.compile(r"([a-z0-9])([A-Z])")
_NON_ALNUM_RE = re.compile(r"[^0-9a-zA-Z]+")


JsonRecord = dict[str, Any]


@dataclass(frozen=True, slots=True)
class FieldMapping:
    """How one source field was normalized inside a record import group."""

    source: str
    normalized: str
    target: str


@dataclass(frozen=True, slots=True)
class FieldCollision:
    """A normalized field collision that was preserved under a suffixed name."""

    row_index: int
    target: str
    source: str
    preserved_as: str


@dataclass(frozen=True, slots=True)
class InvalidRecord:
    """A row that is missing one or more required normalized fields."""

    row_index: int
    missing_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DuplicateRecord:
    """A duplicate row found by identity fields."""

    duplicate_index: int
    kept_index: int
    key: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PreparedRecordImport:
    """Normalized, validated, deduped, and fingerprinted record-import packet."""

    records: tuple[JsonRecord, ...]
    field_map: tuple[FieldMapping, ...]
    required_fields: tuple[str, ...]
    identity_fields: tuple[str, ...]
    invalid_records: tuple[InvalidRecord, ...]
    duplicates: tuple[DuplicateRecord, ...]
    collisions: tuple[FieldCollision, ...]
    original_count: int
    prepared_count: int
    duplicate_count: int
    schema_fingerprint: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class RouteComponent:
    """One exact-edge component candidate for a deterministic route."""

    component_id: str
    input_edge: str
    output_edge: str
    operation: str
    import_path: str = ""
    function_name: str = ""
    cost: int = 1


@dataclass(frozen=True, slots=True)
class RoutePlan:
    """Compiled route over component input/output edges."""

    start_edge: str
    goal_edge: str
    components: tuple[RouteComponent, ...]
    edge_path: tuple[str, ...]
    route_found: bool
    skipped_reason: str = ""


@dataclass(frozen=True, slots=True)
class PrimitiveGraphRuntimePlanReceipt:
    """Ordered primitive graph plan assembled from compact edge cards."""

    ready: bool
    route_id: str
    start_edge: str
    goal_edge: str
    ordered_primitive_ids: tuple[str, ...]
    edge_path: tuple[str, ...]
    hidden_member_edges: tuple[str, ...]
    adapter_mutators: tuple[str, ...]
    proof_requirements: tuple[str, ...]
    effects: tuple[str, ...]
    runtime_targets: tuple[str, ...]
    blockers: tuple[str, ...]
    candidate: bool
    serves_truth: bool
    plan_hash: str


@dataclass(frozen=True, slots=True)
class PrimitiveConsumerReadinessReceipt:
    """Cross-surface readiness check for compact primitive edge cards."""

    ready: bool
    card_count: int
    consumer_surfaces: tuple[str, ...]
    ready_surfaces: tuple[str, ...]
    card_ids: tuple[str, ...]
    visible_edges: tuple[str, ...]
    searchable_terms: tuple[str, ...]
    proof_requirements: tuple[str, ...]
    runtime_targets: tuple[str, ...]
    development_tools: tuple[str, ...]
    blockers: tuple[str, ...]
    consumer_statuses: tuple[str, ...]
    candidate: bool
    serves_truth: bool
    readiness_hash: str


@dataclass(frozen=True, slots=True)
class PrimitiveRegistryExpansionCoverageReceipt:
    """Coverage audit for required primitive families and runtime shapes."""

    ready: bool
    card_count: int
    covered_kinds: tuple[str, ...]
    missing_kinds: tuple[str, ...]
    covered_runtime_targets: tuple[str, ...]
    missing_runtime_targets: tuple[str, ...]
    covered_source_families: tuple[str, ...]
    missing_source_families: tuple[str, ...]
    proofed_primitive_ids: tuple[str, ...]
    unproofed_primitive_ids: tuple[str, ...]
    search_smoke_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    candidate: bool
    serves_truth: bool
    coverage_hash: str


@dataclass(frozen=True, slots=True)
class GuardedWriteReceipt:
    """Receipt for a file write that archived the previous content first."""

    target_path: str
    archive_path: str | None
    manifest_path: str
    previous_digest: str | None
    new_digest: str
    reason: str


@dataclass(frozen=True, slots=True)
class ContractViolation:
    """A deterministic contract/schema violation for a grouped primitive."""

    path: str
    message: str


@dataclass(frozen=True, slots=True)
class PolicyApiRequestDecision:
    """Request validation, scope check, idempotency, and receipt in one edge."""

    allowed: bool
    status: str
    validation_errors: tuple[ContractViolation, ...]
    missing_scopes: tuple[str, ...]
    idempotency_key: str
    decision_receipt: str


@dataclass(frozen=True, slots=True)
class SettingSource:
    """Where one effective setting value came from."""

    key: str
    source: str


@dataclass(frozen=True, slots=True)
class TenantSettingsResolution:
    """Merged settings with validation errors, sources, and redacted view."""

    effective_settings: JsonRecord
    redacted_settings: JsonRecord
    setting_sources: tuple[SettingSource, ...]
    validation_errors: tuple[ContractViolation, ...]
    settings_hash: str


@dataclass(frozen=True, slots=True)
class DeploymentReadinessCheck:
    """One deterministic deployment readiness check result."""

    check_id: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class DeploymentReadinessReport:
    """Deployment readiness decision with blockers and receipt hash."""

    ready: bool
    checks: tuple[DeploymentReadinessCheck, ...]
    blockers: tuple[str, ...]
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class PromptEvalCaseResult:
    """One deterministic prompt/model eval case result."""

    case_id: str
    passed: bool
    score: float
    missing_terms: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PromptEvalReport:
    """Aggregate deterministic prompt/model eval report."""

    case_results: tuple[PromptEvalCaseResult, ...]
    passed_count: int
    total_count: int
    pass_rate: float
    failed_case_ids: tuple[str, ...]
    report_hash: str


@dataclass(frozen=True, slots=True)
class DatabaseMigrationOperation:
    """One normalized migration operation with risk annotations."""

    operation_id: str
    operation: str
    table: str
    column: str
    destructive: bool
    statement_hint: str


@dataclass(frozen=True, slots=True)
class DatabaseMigrationReceipt:
    """Migration plan with rollback, integrity checks, blockers, and receipt."""

    operations: tuple[DatabaseMigrationOperation, ...]
    rollback_steps: tuple[str, ...]
    integrity_checks: tuple[str, ...]
    blockers: tuple[str, ...]
    ready_for_dry_run: bool
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class IntegrationMutation:
    """One deterministic target-system mutation derived from source delta."""

    mutation_id: str
    operation: str
    target_system: str
    target_key: str
    payload: JsonRecord


@dataclass(frozen=True, slots=True)
class IntegrationSyncReceipt:
    """Integration sync plan with idempotency and skipped-record accounting."""

    mutations: tuple[IntegrationMutation, ...]
    skipped_records: tuple[int, ...]
    source_count: int
    mutation_count: int
    idempotency_key: str
    proof_requirements: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Citation:
    """Source span used by a cited answer receipt."""

    source_id: str
    span: str
    quote: str
    score: int


@dataclass(frozen=True, slots=True)
class CitedAnswerReceipt:
    """Deterministic cited answer packet assembled from retrieved evidence."""

    answer: str
    citations: tuple[Citation, ...]
    grounded: bool
    missing_terms: tuple[str, ...]
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class WebhookEventReceipt:
    """Verified webhook event mapped to a compact domain-event receipt."""

    verified: bool
    status: str
    event_id: str
    event_type: str
    domain_event: JsonRecord
    blockers: tuple[str, ...]
    idempotency_key: str
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class QueueJobExecutionReceipt:
    """Queue worker decision with retry/dead-letter and idempotency metadata."""

    accepted: bool
    action: str
    job_type: str
    message_id: str
    blockers: tuple[str, ...]
    retry_after_seconds: int
    idempotency_key: str
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class QueuePayloadContractPlanReceipt:
    """Queue payload contract plan with schema, required fields, headers, and fixture gates."""

    ready: bool
    queue_name: str
    schema_ref: str
    required_fields: tuple[str, ...]
    required_headers: tuple[str, ...]
    blockers: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True, slots=True)
class QueueAckPolicyPlanReceipt:
    """Queue ack/nack policy plan with ack mode, failure action, timeout, and receipt gates."""

    ready: bool
    queue_name: str
    ack_mode: str
    nack_mode: str
    blockers: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class QueuePoisonMessagePolicyPlanReceipt:
    """Queue poison-message policy with threshold, quarantine sink, alert, and replay gates."""

    ready: bool
    queue_name: str
    poison_threshold: int
    quarantine_sink: str
    blockers: tuple[str, ...]
    poison_hash: str


@dataclass(frozen=True, slots=True)
class QueueBatchConsumerPlanReceipt:
    """Queue batch-consumer plan with batch size, wait window, partial failure, and per-item gates."""

    ready: bool
    queue_name: str
    batch_size: int
    max_wait_seconds: int
    blockers: tuple[str, ...]
    batch_hash: str


@dataclass(frozen=True, slots=True)
class QueueOrderingPolicyPlanReceipt:
    """Queue ordering policy with ordering key, mode, partitioning, and gap-detection gates."""

    ready: bool
    queue_name: str
    ordering_key: str
    ordering_mode: str
    blockers: tuple[str, ...]
    ordering_hash: str


@dataclass(frozen=True, slots=True)
class ScheduledJobReceipt:
    """Cron/scheduled-job decision with lock key and skip reason."""

    should_run: bool
    job_name: str
    run_key: str
    lock_key: str
    skipped_reason: str
    proof_requirements: tuple[str, ...]
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class CliCommandReceipt:
    """Normalized CLI command plan that avoids shell-string execution."""

    executable: bool
    command_argv: tuple[str, ...]
    normalized_flags: JsonRecord
    blockers: tuple[str, ...]
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class KubernetesJobPlanReceipt:
    """Kubernetes job readiness plan with safety blockers and manifest digest."""

    ready: bool
    job_name: str
    blockers: tuple[str, ...]
    manifest: JsonRecord
    manifest_hash: str
    proof_requirements: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DashboardTile:
    """One deterministic dashboard tile value."""

    metric: str
    value: Any
    status: str
    source_id: str


@dataclass(frozen=True, slots=True)
class DashboardSnapshotReceipt:
    """Dashboard/report snapshot with required-metric and freshness checks."""

    tiles: tuple[DashboardTile, ...]
    missing_metrics: tuple[str, ...]
    stale_metrics: tuple[str, ...]
    ready: bool
    snapshot_hash: str


@dataclass(frozen=True, slots=True)
class AuthMiddlewareReceipt:
    """Authentication/authorization middleware decision receipt."""

    authorized: bool
    status: str
    subject_id: str
    scopes: tuple[str, ...]
    missing_scopes: tuple[str, ...]
    authorized_request: JsonRecord
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class RateLimitDecisionReceipt:
    """Rate-limit middleware decision with remaining quota and reset time."""

    allowed: bool
    subject_id: str
    limit: int
    used: int
    remaining: int
    reset_epoch: int
    reason: str
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class ToolInvocationPlanReceipt:
    """Agent tool-call plan with policy blockers and audit key."""

    allowed: bool
    tool_name: str
    normalized_args: JsonRecord
    blockers: tuple[str, ...]
    audit_key: str
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class WorkflowStepReceipt:
    """Workflow step transition decision and emitted domain events."""

    transitioned: bool
    current_step: str
    next_step: str
    status: str
    emitted_events: tuple[JsonRecord, ...]
    blockers: tuple[str, ...]
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class PublishedEventReceipt:
    """Queue/event producer receipt with topic, partition key, and idempotency."""

    publishable: bool
    topic: str
    event_type: str
    partition_key: str
    payload: JsonRecord
    blockers: tuple[str, ...]
    idempotency_key: str
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class EventHandlerReceipt:
    """Domain event handler decision with emitted follow-up commands."""

    handled: bool
    event_type: str
    handler_name: str
    emitted_commands: tuple[JsonRecord, ...]
    blockers: tuple[str, ...]
    idempotency_key: str
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class SdkRequestPlanReceipt:
    """Typed SDK/API client request plan with idempotency and retry policy."""

    ready: bool
    method: str
    path: str
    request_body: JsonRecord
    headers: JsonRecord
    retry_policy: JsonRecord
    blockers: tuple[str, ...]
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class TerraformModulePlanReceipt:
    """Terraform module plan with variable validation and policy blockers."""

    ready: bool
    module_name: str
    resources: tuple[JsonRecord, ...]
    variables: JsonRecord
    blockers: tuple[str, ...]
    plan_hash: str


@dataclass(frozen=True, slots=True)
class GithubActionWorkflowReceipt:
    """GitHub Actions workflow plan with permissions and trigger checks."""

    ready: bool
    workflow_name: str
    triggers: tuple[str, ...]
    jobs: tuple[JsonRecord, ...]
    blockers: tuple[str, ...]
    workflow_hash: str


@dataclass(frozen=True, slots=True)
class DataQualityRuleReceipt:
    """Deterministic data quality evaluation summary."""

    passed: bool
    total_rows: int
    failed_rows: tuple[int, ...]
    rule_name: str
    failure_reason: str
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class VectorIndexPlanReceipt:
    """Vector index build plan with chunking, embedding, and dimension checks."""

    ready: bool
    document_count: int
    chunk_count: int
    embedding_model: str
    dimension: int
    blockers: tuple[str, ...]
    index_hash: str


@dataclass(frozen=True, slots=True)
class ComplianceEvidenceReceipt:
    """Security/compliance evidence workflow receipt."""

    ready: bool
    control_id: str
    evidence_refs: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    review_required: bool
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class GraphqlResolverReceipt:
    """GraphQL resolver plan with selection and auth decisions."""

    ready: bool
    operation_name: str
    resolver_name: str
    selected_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class GrpcMethodReceipt:
    """gRPC method invocation plan with service/method and metadata checks."""

    ready: bool
    service: str
    method: str
    request_message: JsonRecord
    metadata: JsonRecord
    blockers: tuple[str, ...]
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class SqlViewPlanReceipt:
    """SQL view planning receipt with source tables and policy blockers."""

    ready: bool
    view_name: str
    sql: str
    source_tables: tuple[str, ...]
    blockers: tuple[str, ...]
    sql_hash: str


@dataclass(frozen=True, slots=True)
class SqlProcedurePlanReceipt:
    """Stored procedure plan with parameter and mutation policy checks."""

    ready: bool
    procedure_name: str
    parameters: tuple[str, ...]
    statements: tuple[str, ...]
    blockers: tuple[str, ...]
    procedure_hash: str


@dataclass(frozen=True, slots=True)
class EtlPipelinePlanReceipt:
    """ETL pipeline plan with extract/transform/load and checkpoint checks."""

    ready: bool
    source_name: str
    target_name: str
    steps: tuple[str, ...]
    blockers: tuple[str, ...]
    pipeline_hash: str


@dataclass(frozen=True, slots=True)
class EltModelPlanReceipt:
    """ELT/dbt-style model plan with dependency and test checks."""

    ready: bool
    model_name: str
    dependencies: tuple[str, ...]
    materialization: str
    tests: tuple[str, ...]
    blockers: tuple[str, ...]
    model_hash: str


@dataclass(frozen=True, slots=True)
class AlertRuleReceipt:
    """Monitoring alert rule decision with routing and threshold checks."""

    ready: bool
    alert_name: str
    severity: str
    condition: str
    routes: tuple[str, ...]
    blockers: tuple[str, ...]
    alert_hash: str


@dataclass(frozen=True, slots=True)
class RunbookPlanReceipt:
    """Operational runbook plan with required action/evidence checks."""

    ready: bool
    incident_type: str
    steps: tuple[str, ...]
    escalation_targets: tuple[str, ...]
    missing_sections: tuple[str, ...]
    runbook_hash: str


@dataclass(frozen=True, slots=True)
class IncidentTriagePlanReceipt:
    """Incident triage plan with severity, ownership, and impact gates."""

    ready: bool
    incident_id: str
    severity: str
    affected_services: tuple[str, ...]
    priority: str
    blockers: tuple[str, ...]
    triage_hash: str


@dataclass(frozen=True, slots=True)
class OncallEscalationPlanReceipt:
    """On-call escalation plan with channel, target, and ack checks."""

    ready: bool
    incident_id: str
    primary_oncall: str
    escalation_targets: tuple[str, ...]
    channels: tuple[str, ...]
    blockers: tuple[str, ...]
    escalation_hash: str


@dataclass(frozen=True, slots=True)
class StatusPageUpdatePlanReceipt:
    """Status-page update plan with component, audience, and approval checks."""

    ready: bool
    incident_id: str
    status: str
    components: tuple[str, ...]
    audiences: tuple[str, ...]
    blockers: tuple[str, ...]
    update_hash: str


@dataclass(frozen=True, slots=True)
class MaintenanceWindowPlanReceipt:
    """Maintenance window plan with duration, notification, and rollback checks."""

    ready: bool
    window_id: str
    affected_services: tuple[str, ...]
    start_epoch: int
    end_epoch: int
    blockers: tuple[str, ...]
    window_hash: str


@dataclass(frozen=True, slots=True)
class PostmortemActionPlanReceipt:
    """Postmortem action plan with owned prevention and verification tasks."""

    ready: bool
    incident_id: str
    action_ids: tuple[str, ...]
    owners: tuple[str, ...]
    blockers: tuple[str, ...]
    action_hash: str


@dataclass(frozen=True, slots=True)
class TestFixtureReceipt:
    """Test fixture generation receipt with schema and redaction checks."""

    ready: bool
    fixture_name: str
    rows: tuple[JsonRecord, ...]
    redacted_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    fixture_hash: str


@dataclass(frozen=True, slots=True)
class MockServerPlanReceipt:
    """Mock server plan with route and example-response validation."""

    ready: bool
    routes: tuple[JsonRecord, ...]
    base_url: str
    blockers: tuple[str, ...]
    server_hash: str


@dataclass(frozen=True, slots=True)
class PolicyRuleDecisionReceipt:
    """Policy rule decision with reason codes and required context checks."""

    allowed: bool
    decision: str
    action: str
    subject_id: str
    reason_codes: tuple[str, ...]
    blockers: tuple[str, ...]
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class ShellScriptPlanReceipt:
    """Shell command plan that validates argv without executing it."""

    ready: bool
    command_argv: tuple[str, ...]
    env_keys: tuple[str, ...]
    blockers: tuple[str, ...]
    script_hash: str


@dataclass(frozen=True, slots=True)
class KubernetesControllerPlanReceipt:
    """Kubernetes controller plan with watch and reconcile checks."""

    ready: bool
    controller_name: str
    watched_kinds: tuple[str, ...]
    reconcile_steps: tuple[str, ...]
    blockers: tuple[str, ...]
    plan_hash: str


@dataclass(frozen=True, slots=True)
class WorkflowGroupPlanReceipt:
    """Multi-step workflow group plan with edge and required-step checks."""

    ready: bool
    workflow_name: str
    steps: tuple[str, ...]
    edges: tuple[JsonRecord, ...]
    blockers: tuple[str, ...]
    workflow_hash: str


@dataclass(frozen=True, slots=True)
class UiComponentPlanReceipt:
    """UI component plan with props, state, and accessibility checks."""

    ready: bool
    component_name: str
    props: tuple[str, ...]
    states: tuple[str, ...]
    blockers: tuple[str, ...]
    component_hash: str


@dataclass(frozen=True, slots=True)
class UiRoutePlanReceipt:
    """UI route/page plan with path, data, and component checks."""

    ready: bool
    route_path: str
    data_dependencies: tuple[str, ...]
    components: tuple[str, ...]
    blockers: tuple[str, ...]
    route_hash: str


@dataclass(frozen=True, slots=True)
class UiApiBindingPlanReceipt:
    """UI-to-API binding plan with operation, state, and auth checks."""

    ready: bool
    component_name: str
    operation_ids: tuple[str, ...]
    data_dependencies: tuple[str, ...]
    mutation_operations: tuple[str, ...]
    blockers: tuple[str, ...]
    binding_hash: str


@dataclass(frozen=True, slots=True)
class UiFormValidationPlanReceipt:
    """UI form validation plan with field, validator, and error-state checks."""

    ready: bool
    form_name: str
    field_names: tuple[str, ...]
    submit_action: str
    blockers: tuple[str, ...]
    validation_hash: str


@dataclass(frozen=True, slots=True)
class UiTableStatePlanReceipt:
    """UI table state plan for columns, row identity, and list controls."""

    ready: bool
    table_name: str
    columns: tuple[str, ...]
    state_controls: tuple[str, ...]
    blockers: tuple[str, ...]
    state_hash: str


@dataclass(frozen=True, slots=True)
class DashboardFilterContractPlanReceipt:
    """Dashboard filter contract plan for metric/filter bindings."""

    ready: bool
    dashboard_name: str
    filters: tuple[str, ...]
    metrics: tuple[str, ...]
    blockers: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True, slots=True)
class UiAccessibilityInteractionPlanReceipt:
    """UI accessibility interaction plan with keyboard, focus, and ARIA gates."""

    ready: bool
    surface_name: str
    interactions: tuple[str, ...]
    roles: tuple[str, ...]
    blockers: tuple[str, ...]
    accessibility_hash: str


@dataclass(frozen=True, slots=True)
class ApiResourceGroupPlanReceipt:
    """Resource API group plan across CRUD/search/export operations."""

    ready: bool
    resource_name: str
    operations: tuple[str, ...]
    missing_operations: tuple[str, ...]
    blockers: tuple[str, ...]
    api_hash: str


@dataclass(frozen=True, slots=True)
class MicroserviceBundlePlanReceipt:
    """Microservice bundle plan with callable surfaces and runtime proof gates."""

    ready: bool
    service_name: str
    surfaces: tuple[str, ...]
    data_stores: tuple[str, ...]
    blockers: tuple[str, ...]
    service_hash: str


@dataclass(frozen=True, slots=True)
class ServiceBoundaryContractPlanReceipt:
    """Service boundary contract with bounded context, owned capabilities, and dependency gates."""

    ready: bool
    service_name: str
    bounded_context: str
    owned_capabilities: tuple[str, ...]
    external_dependencies: tuple[str, ...]
    blockers: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True, slots=True)
class ServiceSurfaceInventoryPlanReceipt:
    """Service surface inventory with endpoint, worker, event, and public-auth gates."""

    ready: bool
    service_name: str
    surfaces: tuple[str, ...]
    public_surfaces: tuple[str, ...]
    blockers: tuple[str, ...]
    inventory_hash: str


@dataclass(frozen=True, slots=True)
class ServiceDataOwnershipPlanReceipt:
    """Service data ownership plan with owned stores, read-only dependencies, and lifecycle gates."""

    ready: bool
    service_name: str
    owned_stores: tuple[str, ...]
    read_only_stores: tuple[str, ...]
    blockers: tuple[str, ...]
    ownership_hash: str


@dataclass(frozen=True, slots=True)
class ServiceStartupOrderPlanReceipt:
    """Service startup order plan with dependency checks, migration gate, readiness, and timing gates."""

    ready: bool
    service_name: str
    startup_steps: tuple[str, ...]
    blockers: tuple[str, ...]
    startup_hash: str


@dataclass(frozen=True, slots=True)
class ServiceSecretBindingPlanReceipt:
    """Service secret binding plan with secret refs, providers, rotation, and runtime identity gates."""

    ready: bool
    service_name: str
    secret_refs: tuple[str, ...]
    blockers: tuple[str, ...]
    binding_hash: str


@dataclass(frozen=True, slots=True)
class ServiceBackpressurePolicyPlanReceipt:
    """Service backpressure plan with inflight, queue, overload, and retry/degrade gates."""

    ready: bool
    service_name: str
    max_inflight: int
    queue_policy: str
    blockers: tuple[str, ...]
    backpressure_hash: str


@dataclass(frozen=True, slots=True)
class OpenApiOperationPrimitiveSetReceipt:
    """OpenAPI operation extraction receipt for endpoint primitive candidates."""

    ready: bool
    operations: tuple[JsonRecord, ...]
    blockers: tuple[str, ...]
    extraction_hash: str


@dataclass(frozen=True, slots=True)
class AsyncApiOperationPrimitiveSetReceipt:
    """AsyncAPI operation extraction receipt for event primitive candidates."""

    ready: bool
    operations: tuple[JsonRecord, ...]
    channel_count: int
    blockers: tuple[str, ...]
    extraction_hash: str


@dataclass(frozen=True, slots=True)
class CloudEventEnvelopeReceipt:
    """Normalized CloudEvents-style envelope with idempotency metadata."""

    valid: bool
    event_id: str
    event_type: str
    source: str
    envelope: JsonRecord
    blockers: tuple[str, ...]
    idempotency_key: str
    receipt_hash: str


@dataclass(frozen=True, slots=True)
class ServerlessFunctionPlanReceipt:
    """Serverless/cloud-function plan with trigger and runtime blockers."""

    ready: bool
    function_name: str
    runtime: str
    handler: str
    trigger_type: str
    env_keys: tuple[str, ...]
    blockers: tuple[str, ...]
    plan_hash: str


@dataclass(frozen=True, slots=True)
class ObservabilityInstrumentationReceipt:
    """Telemetry instrumentation plan for traces, metrics, logs, and redaction."""

    ready: bool
    operation_name: str
    spans: tuple[str, ...]
    metrics: tuple[str, ...]
    logs: tuple[str, ...]
    redacted_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    instrumentation_hash: str


@dataclass(frozen=True, slots=True)
class ApiContractTestSuiteReceipt:
    """API contract test-suite plan generated from operations and fixtures."""

    ready: bool
    operation_count: int
    test_cases: tuple[JsonRecord, ...]
    blockers: tuple[str, ...]
    suite_hash: str


@dataclass(frozen=True, slots=True)
class FeatureFlagPlanReceipt:
    """Feature-flag rollout plan with audience, owner, and kill-switch gates."""

    ready: bool
    flag_key: str
    rollout_strategy: str
    audiences: tuple[str, ...]
    blockers: tuple[str, ...]
    flag_hash: str


@dataclass(frozen=True, slots=True)
class SecretRotationPlanReceipt:
    """Secret rotation plan with interval, rollback, and zero-downtime gates."""

    ready: bool
    secret_name: str
    provider: str
    rotation_interval_days: int
    rotation_steps: tuple[str, ...]
    blockers: tuple[str, ...]
    rotation_hash: str


@dataclass(frozen=True, slots=True)
class AgentToolSchemaReceipt:
    """Agent tool schema plan derived from an API operation contract."""

    ready: bool
    tool_name: str
    method: str
    path: str
    parameters: tuple[str, ...]
    required_scopes: tuple[str, ...]
    blockers: tuple[str, ...]
    schema_hash: str


@dataclass(frozen=True, slots=True)
class SdkPackagePlanReceipt:
    """SDK package generation plan with operation and auth coverage gates."""

    ready: bool
    package_name: str
    language: str
    operations: tuple[str, ...]
    auth_strategy: str
    blockers: tuple[str, ...]
    package_hash: str


@dataclass(frozen=True, slots=True)
class DockerfilePlanReceipt:
    """Dockerfile plan with base image, command, port, and safety gates."""

    ready: bool
    base_image: str
    workdir: str
    exposed_ports: tuple[int, ...]
    blockers: tuple[str, ...]
    dockerfile_hash: str


@dataclass(frozen=True, slots=True)
class DockerComposePlanReceipt:
    """Docker Compose stack plan with service, secret, and health gates."""

    ready: bool
    service_names: tuple[str, ...]
    network_names: tuple[str, ...]
    volume_names: tuple[str, ...]
    blockers: tuple[str, ...]
    compose_hash: str


@dataclass(frozen=True, slots=True)
class HelmChartPlanReceipt:
    """Helm chart plan with templates, values, resource, and probe gates."""

    ready: bool
    chart_name: str
    templates: tuple[str, ...]
    values: JsonRecord
    blockers: tuple[str, ...]
    chart_hash: str


@dataclass(frozen=True, slots=True)
class RbacPolicyPlanReceipt:
    """RBAC policy matrix plan with role/action and wildcard checks."""

    ready: bool
    roles: tuple[str, ...]
    actions: tuple[str, ...]
    bindings: tuple[JsonRecord, ...]
    blockers: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class PiiRedactionPlanReceipt:
    """PII redaction policy plan over schema fields and masking methods."""

    ready: bool
    sensitive_fields: tuple[str, ...]
    redaction_map: JsonRecord
    unprotected_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class ConnectorAuthBindingReceipt:
    """Integration connector auth binding with secret refs and scope checks."""

    ready: bool
    connector_name: str
    source_system: str
    target_system: str
    auth_bindings: tuple[JsonRecord, ...]
    blockers: tuple[str, ...]
    binding_hash: str


@dataclass(frozen=True, slots=True)
class IdempotencyPolicyPlanReceipt:
    """Idempotency policy plan with key, store, TTL, and replay gates."""

    ready: bool
    operation_name: str
    key_fields: tuple[str, ...]
    ttl_seconds: int
    store_name: str
    blockers: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class PaginationContractPlanReceipt:
    """API pagination contract plan with cursor, limit, and ordering gates."""

    ready: bool
    resource_name: str
    mode: str
    default_limit: int
    max_limit: int
    blockers: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True, slots=True)
class CorsSecurityHeadersPlanReceipt:
    """CORS and HTTP security headers plan for endpoint surfaces."""

    ready: bool
    allowed_origins: tuple[str, ...]
    allowed_methods: tuple[str, ...]
    security_headers: JsonRecord
    blockers: tuple[str, ...]
    headers_hash: str


@dataclass(frozen=True, slots=True)
class AuditLogPolicyPlanReceipt:
    """Audit logging policy plan with actor, action, resource, and retention gates."""

    ready: bool
    event_name: str
    required_fields: tuple[str, ...]
    retention_days: int
    blockers: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class TenantIsolationPlanReceipt:
    """Tenant isolation policy plan for scoped storage, auth, and query filters."""

    ready: bool
    resource_name: str
    tenant_key: str
    isolation_mode: str
    blockers: tuple[str, ...]
    isolation_hash: str


@dataclass(frozen=True, slots=True)
class EventSchemaCompatibilityReceipt:
    """Event schema compatibility check with breaking-change blockers."""

    compatible: bool
    event_type: str
    added_fields: tuple[str, ...]
    removed_fields: tuple[str, ...]
    changed_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    compatibility_hash: str


@dataclass(frozen=True, slots=True)
class DeadLetterReplayPlanReceipt:
    """Dead-letter replay plan with batch, dedupe, throttle, and audit gates."""

    ready: bool
    queue_name: str
    replay_batch_size: int
    max_retries: int
    blockers: tuple[str, ...]
    replay_hash: str


@dataclass(frozen=True, slots=True)
class CacheInvalidationPlanReceipt:
    """Cache invalidation plan with key pattern, trigger, and TTL gates."""

    ready: bool
    cache_name: str
    key_patterns: tuple[str, ...]
    triggers: tuple[str, ...]
    ttl_seconds: int
    blockers: tuple[str, ...]
    invalidation_hash: str


@dataclass(frozen=True, slots=True)
class DocumentChunkingPlanReceipt:
    """Document chunking plan with size, overlap, and metadata gates."""

    ready: bool
    document_count: int
    chunk_count: int
    chunk_chars: int
    overlap_chars: int
    blockers: tuple[str, ...]
    plan_hash: str


@dataclass(frozen=True, slots=True)
class RetrievalRerankPlanReceipt:
    """Retrieval and rerank plan with top-k, model, and source-diversity gates."""

    ready: bool
    retriever_names: tuple[str, ...]
    top_k: int
    reranker_model: str
    blockers: tuple[str, ...]
    plan_hash: str


@dataclass(frozen=True, slots=True)
class CitationCoverageReceipt:
    """Citation coverage check for generated answers and retrieved evidence."""

    grounded: bool
    claim_count: int
    citation_count: int
    uncovered_claims: tuple[str, ...]
    blockers: tuple[str, ...]
    coverage_hash: str


@dataclass(frozen=True, slots=True)
class AgentToolPermissionMatrixReceipt:
    """Agent tool permission matrix with role, scope, and approval gates."""

    ready: bool
    tool_names: tuple[str, ...]
    roles: tuple[str, ...]
    bindings: tuple[JsonRecord, ...]
    blockers: tuple[str, ...]
    matrix_hash: str


@dataclass(frozen=True, slots=True)
class ModelRoutingPolicyReceipt:
    """Model routing policy with route, fallback, budget, and data-class gates."""

    ready: bool
    route_names: tuple[str, ...]
    default_model: str
    fallback_models: tuple[str, ...]
    blockers: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class PromptRegressionSuitePlanReceipt:
    """Prompt regression suite plan with fixtures, metrics, and threshold gates."""

    ready: bool
    case_count: int
    metrics: tuple[str, ...]
    thresholds: JsonRecord
    blockers: tuple[str, ...]
    suite_hash: str


@dataclass(frozen=True, slots=True)
class MemoryRetentionPolicyPlanReceipt:
    """Agent memory retention plan with scope, TTL, PII, and deletion gates."""

    ready: bool
    memory_scope: str
    retention_days: int
    pii_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class VectorIndexFreshnessReceipt:
    """Vector-index freshness check with stale-document and rebuild gates."""

    fresh: bool
    index_name: str
    age_seconds: int
    max_age_seconds: int
    stale_documents: tuple[str, ...]
    blockers: tuple[str, ...]
    freshness_hash: str


@dataclass(frozen=True, slots=True)
class CanaryReleasePlanReceipt:
    """Canary release plan with traffic, metrics, rollback, and health gates."""

    ready: bool
    service_name: str
    traffic_steps: tuple[int, ...]
    metrics: tuple[str, ...]
    blockers: tuple[str, ...]
    plan_hash: str


@dataclass(frozen=True, slots=True)
class BlueGreenDeploymentPlanReceipt:
    """Blue/green deployment plan with target color, smoke, and switch gates."""

    ready: bool
    service_name: str
    active_color: str
    target_color: str
    blockers: tuple[str, ...]
    deployment_hash: str


@dataclass(frozen=True, slots=True)
class SloErrorBudgetPolicyReceipt:
    """SLO/error-budget policy with target, window, alert, and runbook gates."""

    ready: bool
    service_name: str
    slo_target_percent: float
    window_days: int
    error_budget_minutes: int
    blockers: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class DependencyVulnerabilityExceptionReceipt:
    """Dependency vulnerability exception decision with expiry and control gates."""

    approved: bool
    dependency_name: str
    vulnerability_id: str
    severity: str
    blockers: tuple[str, ...]
    exception_hash: str


@dataclass(frozen=True, slots=True)
class SecretScanFindingReceipt:
    """Secret-scan finding evaluation with confirmed secret blockers."""

    clean: bool
    scanner_name: str
    finding_count: int
    confirmed_secret_count: int
    blockers: tuple[str, ...]
    scan_hash: str


@dataclass(frozen=True, slots=True)
class SbomGenerationPlanReceipt:
    """SBOM generation plan with component, format, and provenance gates."""

    ready: bool
    package_name: str
    component_count: int
    formats: tuple[str, ...]
    blockers: tuple[str, ...]
    sbom_hash: str


@dataclass(frozen=True, slots=True)
class LicenseCompliancePlanReceipt:
    """License compliance check with restricted-license and attribution gates."""

    compliant: bool
    package_count: int
    restricted_licenses: tuple[str, ...]
    blockers: tuple[str, ...]
    compliance_hash: str


@dataclass(frozen=True, slots=True)
class BackupRestorePlanReceipt:
    """Backup/restore plan with frequency, RPO/RTO, restore-test, and encryption gates."""

    ready: bool
    resource_name: str
    backup_frequency: str
    restore_objective_minutes: int
    blockers: tuple[str, ...]
    plan_hash: str


@dataclass(frozen=True, slots=True)
class CircuitBreakerPlanReceipt:
    """Circuit-breaker plan with fallback, threshold, timeout, and metric gates."""

    ready: bool
    service_name: str
    failure_threshold: int
    reset_timeout_seconds: int
    blockers: tuple[str, ...]
    plan_hash: str


@dataclass(frozen=True, slots=True)
class RetryBackoffPolicyReceipt:
    """Retry/backoff policy with attempt, delay, jitter, and idempotency gates."""

    ready: bool
    operation_name: str
    max_attempts: int
    base_delay_ms: int
    jitter: bool
    blockers: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class TimeoutBudgetPlanReceipt:
    """Timeout-budget plan with total and per-phase budget gates."""

    ready: bool
    operation_name: str
    total_timeout_ms: int
    phase_budgets: dict[str, int]
    blockers: tuple[str, ...]
    budget_hash: str


@dataclass(frozen=True, slots=True)
class ConcurrencyLimitPlanReceipt:
    """Concurrency-limit/bulkhead plan with resource, queue, and metric gates."""

    ready: bool
    resource_name: str
    max_concurrency: int
    queue_limit: int
    blockers: tuple[str, ...]
    limit_hash: str


@dataclass(frozen=True, slots=True)
class HealthProbePlanReceipt:
    """Health-probe contract with readiness, liveness, startup, and dependency gates."""

    ready: bool
    service_name: str
    readiness_path: str
    liveness_path: str
    blockers: tuple[str, ...]
    probe_hash: str


@dataclass(frozen=True, slots=True)
class DependencyReadinessPlanReceipt:
    """Dependency-readiness plan with healthcheck, timeout, and fallback gates."""

    ready: bool
    service_name: str
    dependencies: tuple[str, ...]
    blockers: tuple[str, ...]
    readiness_hash: str


@dataclass(frozen=True, slots=True)
class GracefulShutdownPlanReceipt:
    """Graceful-shutdown plan with drain timeout, hooks, signal, and request gates."""

    ready: bool
    service_name: str
    drain_timeout_seconds: int
    hooks: tuple[str, ...]
    blockers: tuple[str, ...]
    shutdown_hash: str


@dataclass(frozen=True, slots=True)
class ChaosExperimentPlanReceipt:
    """Chaos-experiment plan with blast-radius, hypothesis, abort, and rollback gates."""

    ready: bool
    experiment_name: str
    target_service: str
    blast_radius: str
    blockers: tuple[str, ...]
    experiment_hash: str


@dataclass(frozen=True, slots=True)
class OpenApiCompatibilityReceipt:
    """OpenAPI compatibility result with removed and changed operation blockers."""

    compatible: bool
    removed_paths: tuple[str, ...]
    removed_operations: tuple[str, ...]
    changed_operations: tuple[str, ...]
    blockers: tuple[str, ...]
    compatibility_hash: str


@dataclass(frozen=True, slots=True)
class ApiVersioningPlanReceipt:
    """API versioning plan with semver, changelog, migration, and compatibility gates."""

    ready: bool
    api_name: str
    current_version: str
    next_version: str
    blockers: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class ApiDeprecationNoticeReceipt:
    """API deprecation notice plan with sunset, replacement, docs, and header gates."""

    ready: bool
    endpoint_id: str
    sunset_days: int
    blockers: tuple[str, ...]
    notice_hash: str


@dataclass(frozen=True, slots=True)
class ErrorEnvelopeContractReceipt:
    """Error-envelope contract plan with required field and code gates."""

    ready: bool
    endpoint_id: str
    required_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    envelope_hash: str


@dataclass(frozen=True, slots=True)
class RequestSigningPolicyReceipt:
    """Request-signing policy with algorithm, header, replay, and rotation gates."""

    ready: bool
    endpoint_id: str
    algorithm: str
    required_headers: tuple[str, ...]
    blockers: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True, slots=True)
class ApiUsagePlanReceipt:
    """API usage-plan policy with quota, period, burst, scope, and alert gates."""

    ready: bool
    consumer_name: str
    quota_limit: int
    period: str
    blockers: tuple[str, ...]
    plan_hash: str


@dataclass(frozen=True, slots=True)
class ApiKeyRotationPlanReceipt:
    """API key rotation plan with secret reference, overlap, owner, and revoke gates."""

    ready: bool
    key_name: str
    rotation_days: int
    blockers: tuple[str, ...]
    rotation_hash: str


@dataclass(frozen=True, slots=True)
class ResponseCachePolicyReceipt:
    """Response-cache policy with TTL, vary-header, privacy, and invalidation gates."""

    ready: bool
    endpoint_id: str
    cache_ttl_seconds: int
    vary_headers: tuple[str, ...]
    blockers: tuple[str, ...]
    cache_hash: str


@dataclass(frozen=True, slots=True)
class ApiRequestValidationPlanReceipt:
    """API request validation plan with method, schema, body, and receipt gates."""

    ready: bool
    endpoint_id: str
    method: str
    content_types: tuple[str, ...]
    required_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    validation_hash: str


@dataclass(frozen=True, slots=True)
class ApiAuthScopeMatrixPlanReceipt:
    """API authorization scope matrix with action, scope, and tenant-claim gates."""

    ready: bool
    endpoint_id: str
    action: str
    required_scopes: tuple[str, ...]
    tenant_claims: tuple[str, ...]
    blockers: tuple[str, ...]
    matrix_hash: str


@dataclass(frozen=True, slots=True)
class ApiAsyncJobEndpointPlanReceipt:
    """API async-job endpoint plan with job, status, cancel, TTL, and receipt gates."""

    ready: bool
    endpoint_id: str
    status_endpoint: str
    completion_states: tuple[str, ...]
    blockers: tuple[str, ...]
    job_hash: str


@dataclass(frozen=True, slots=True)
class ApiBulkOperationPlanReceipt:
    """API bulk-operation plan with batch, partial-failure, and per-item result gates."""

    ready: bool
    endpoint_id: str
    max_batch_size: int
    partial_failure_mode: str
    blockers: tuple[str, ...]
    bulk_hash: str


@dataclass(frozen=True, slots=True)
class ApiOperationExampleCoverageReceipt:
    """API operation example coverage with required status-code and example-type gates."""

    ready: bool
    endpoint_id: str
    covered_status_codes: tuple[str, ...]
    covered_example_types: tuple[str, ...]
    blockers: tuple[str, ...]
    coverage_hash: str


@dataclass(frozen=True, slots=True)
class ApiEndpointTelemetryPlanReceipt:
    """API endpoint telemetry plan with span, metric, trace-context, and redaction gates."""

    ready: bool
    endpoint_id: str
    span_name: str
    metrics: tuple[str, ...]
    redacted_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    telemetry_hash: str


@dataclass(frozen=True, slots=True)
class CdcCapturePlanReceipt:
    """CDC capture plan with cursor, primary key, snapshot, and checkpoint gates."""

    ready: bool
    source_name: str
    cursor_field: str
    primary_key_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    capture_hash: str


@dataclass(frozen=True, slots=True)
class StreamWatermarkPlanReceipt:
    """Stream watermark plan with event-time, lateness, sink, and skew gates."""

    ready: bool
    stream_name: str
    event_time_field: str
    allowed_lateness_seconds: int
    blockers: tuple[str, ...]
    watermark_hash: str


@dataclass(frozen=True, slots=True)
class PartitionStrategyPlanReceipt:
    """Dataset partition strategy with field, retention, compaction, and skew gates."""

    ready: bool
    dataset_name: str
    partition_fields: tuple[str, ...]
    retention_days: int
    blockers: tuple[str, ...]
    strategy_hash: str


@dataclass(frozen=True, slots=True)
class DataLineageContractReceipt:
    """Data lineage contract with input, output, owner, run, and column lineage gates."""

    ready: bool
    dataset_name: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    blockers: tuple[str, ...]
    lineage_hash: str


@dataclass(frozen=True, slots=True)
class OutboxPublicationPlanReceipt:
    """Transactional outbox publication plan with table, topic, checkpoint, and receipt gates."""

    ready: bool
    aggregate_name: str
    event_topic: str
    outbox_table: str
    blockers: tuple[str, ...]
    publication_hash: str


@dataclass(frozen=True, slots=True)
class InboxDeduplicationPlanReceipt:
    """Inbox deduplication plan with dedupe key, TTL, conflict, and replay gates."""

    ready: bool
    consumer_name: str
    dedupe_key: str
    ttl_seconds: int
    blockers: tuple[str, ...]
    dedupe_hash: str


@dataclass(frozen=True, slots=True)
class MaterializedViewRefreshPlanReceipt:
    """Materialized-view refresh plan with staleness, dependency, backfill, and swap gates."""

    ready: bool
    view_name: str
    refresh_strategy: str
    max_staleness_seconds: int
    blockers: tuple[str, ...]
    refresh_hash: str


@dataclass(frozen=True, slots=True)
class DataQuarantinePlanReceipt:
    """Data quarantine plan with finding, sink, triage, and release gates."""

    ready: bool
    dataset_name: str
    finding_count: int
    quarantine_sink: str
    blockers: tuple[str, ...]
    quarantine_hash: str


@dataclass(frozen=True, slots=True)
class TaskLeasePlanReceipt:
    """Task-lease plan with TTL, renewal, owner-token, and fencing gates."""

    ready: bool
    worker_name: str
    lease_ttl_seconds: int
    renewal_interval_seconds: int
    blockers: tuple[str, ...]
    lease_hash: str


@dataclass(frozen=True, slots=True)
class WorkerHeartbeatPlanReceipt:
    """Worker heartbeat plan with interval, stale threshold, liveness, and restart gates."""

    ready: bool
    worker_name: str
    heartbeat_interval_seconds: int
    stale_after_seconds: int
    blockers: tuple[str, ...]
    heartbeat_hash: str


@dataclass(frozen=True, slots=True)
class WorkerAutoscalePolicyPlanReceipt:
    """Worker autoscale policy with queue metric, replica bounds, cooldown, and drain gates."""

    ready: bool
    worker_name: str
    scale_metric: str
    min_replicas: int
    max_replicas: int
    blockers: tuple[str, ...]
    autoscale_hash: str


@dataclass(frozen=True, slots=True)
class QueueVisibilityTimeoutPlanReceipt:
    """Queue visibility-timeout plan with processing-time, extension, and DLQ gates."""

    ready: bool
    queue_name: str
    visibility_timeout_seconds: int
    max_processing_seconds: int
    blockers: tuple[str, ...]
    timeout_hash: str


@dataclass(frozen=True, slots=True)
class CronCatchupPlanReceipt:
    """Cron catch-up plan with catch-up window, max-run, misfire, and idempotency gates."""

    ready: bool
    job_name: str
    catchup_window_minutes: int
    max_catchup_runs: int
    blockers: tuple[str, ...]
    catchup_hash: str


@dataclass(frozen=True, slots=True)
class WorkflowCompensationPlanReceipt:
    """Workflow compensation plan with compensating steps, ordering, and receipt gates."""

    ready: bool
    workflow_name: str
    compensating_steps: tuple[str, ...]
    blockers: tuple[str, ...]
    compensation_hash: str


@dataclass(frozen=True, slots=True)
class BatchCheckpointPlanReceipt:
    """Batch checkpoint plan with interval, store, resume, and checksum gates."""

    ready: bool
    job_name: str
    checkpoint_interval_records: int
    checkpoint_store: str
    blockers: tuple[str, ...]
    checkpoint_hash: str


@dataclass(frozen=True, slots=True)
class RunArtifactManifestReceipt:
    """Run artifact manifest with artifact, digest, retention, and owner gates."""

    ready: bool
    run_id: str
    artifacts: tuple[str, ...]
    blockers: tuple[str, ...]
    manifest_hash: str


@dataclass(frozen=True, slots=True)
class ExecutionAuditTrailPlanReceipt:
    """Execution audit-trail plan with event, actor, trace, and sink gates."""

    ready: bool
    operation_name: str
    audit_events: tuple[str, ...]
    blockers: tuple[str, ...]
    audit_hash: str


@dataclass(frozen=True, slots=True)
class ApiGatewayRoutePlanReceipt:
    """API gateway route plan with upstream, method, auth, rate, and timeout gates."""

    ready: bool
    route_id: str
    upstream_service: str
    methods: tuple[str, ...]
    blockers: tuple[str, ...]
    route_hash: str


@dataclass(frozen=True, slots=True)
class ServiceDiscoveryRegistrationReceipt:
    """Service discovery registration plan with endpoint, health check, TTL, and region gates."""

    ready: bool
    service_name: str
    endpoints: tuple[str, ...]
    health_check_path: str
    blockers: tuple[str, ...]
    registration_hash: str


@dataclass(frozen=True, slots=True)
class ServiceDependencyContractReceipt:
    """Service dependency contract with timeout, fallback, circuit breaker, and owner gates."""

    ready: bool
    service_name: str
    dependencies: tuple[str, ...]
    blockers: tuple[str, ...]
    contract_hash: str


@dataclass(frozen=True, slots=True)
class RuntimeConfigSchemaPlanReceipt:
    """Runtime config schema plan with key, secret-ref, schema-version, and owner gates."""

    ready: bool
    service_name: str
    config_keys: tuple[str, ...]
    secret_keys: tuple[str, ...]
    blockers: tuple[str, ...]
    schema_hash: str


@dataclass(frozen=True, slots=True)
class EnvironmentPromotionPlanReceipt:
    """Environment promotion plan with source, target, artifact, migration, and rollback gates."""

    ready: bool
    service_name: str
    source_environment: str
    target_environment: str
    blockers: tuple[str, ...]
    promotion_hash: str


@dataclass(frozen=True, slots=True)
class WebhookDeliveryPolicyPlanReceipt:
    """Webhook delivery plan with HTTPS destination, signing, idempotency, retry, and DLQ gates."""

    ready: bool
    webhook_name: str
    destination_url: str
    retry_attempts: int
    blockers: tuple[str, ...]
    delivery_hash: str


@dataclass(frozen=True, slots=True)
class ConsumerGroupOffsetPlanReceipt:
    """Consumer group offset plan with strategy, checkpoint, replay, and lag alert gates."""

    ready: bool
    consumer_group: str
    topic_name: str
    offset_strategy: str
    blockers: tuple[str, ...]
    offset_hash: str


@dataclass(frozen=True, slots=True)
class ServiceOwnershipRunbookPlanReceipt:
    """Service ownership runbook plan with owner, escalation, SLO, dashboard, and on-call gates."""

    ready: bool
    service_name: str
    owners: tuple[str, ...]
    escalation_channels: tuple[str, ...]
    blockers: tuple[str, ...]
    ownership_hash: str


@dataclass(frozen=True, slots=True)
class SchemaDriftGateReceipt:
    """Schema drift gate with expected schema, observed schema, compatibility, and owner gates."""

    compatible: bool
    dataset_name: str
    added_fields: tuple[str, ...]
    removed_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    drift_hash: str


@dataclass(frozen=True, slots=True)
class MigrationLockPlanReceipt:
    """Migration lock plan with lock key, owner, timeout, and stale-lock gates."""

    ready: bool
    migration_name: str
    lock_key: str
    timeout_seconds: int
    blockers: tuple[str, ...]
    lock_hash: str


@dataclass(frozen=True, slots=True)
class DataRetentionEnforcementPlanReceipt:
    """Data retention enforcement plan with dataset, retention window, legal hold, and audit gates."""

    ready: bool
    dataset_name: str
    retention_days: int
    purge_strategy: str
    blockers: tuple[str, ...]
    retention_hash: str


@dataclass(frozen=True, slots=True)
class TenantDataBoundaryPlanReceipt:
    """Tenant data boundary plan with tenant key, RLS, cross-tenant tests, and audit gates."""

    ready: bool
    dataset_name: str
    tenant_key: str
    boundary_controls: tuple[str, ...]
    blockers: tuple[str, ...]
    boundary_hash: str


@dataclass(frozen=True, slots=True)
class BackupRestoreDrillReceipt:
    """Backup restore drill receipt with backup artifact, restore target, RPO/RTO, and checksum gates."""

    ready: bool
    system_name: str
    backup_artifact: str
    restore_target: str
    blockers: tuple[str, ...]
    drill_hash: str


@dataclass(frozen=True, slots=True)
class AccessReviewEvidenceReceipt:
    """Access review evidence plan with actor, role, manager, decision, and revocation gates."""

    ready: bool
    review_name: str
    subjects: tuple[str, ...]
    decisions: tuple[str, ...]
    blockers: tuple[str, ...]
    review_hash: str


@dataclass(frozen=True, slots=True)
class DataDeletionWorkflowPlanReceipt:
    """Data deletion workflow plan with subject, scope, tombstone, propagation, and receipt gates."""

    ready: bool
    request_id: str
    subject_id: str
    deletion_scopes: tuple[str, ...]
    blockers: tuple[str, ...]
    deletion_hash: str


@dataclass(frozen=True, slots=True)
class PrivilegedAccessApprovalPlanReceipt:
    """Privileged access approval plan with requester, role, duration, approval, and breakglass gates."""

    ready: bool
    request_id: str
    requester: str
    role: str
    blockers: tuple[str, ...]
    approval_hash: str


@dataclass(frozen=True, slots=True)
class ConnectorCursorCheckpointPlanReceipt:
    """Connector cursor checkpoint plan with cursor, checkpoint store, resume token, and receipt gates."""

    ready: bool
    connector_name: str
    cursor_field: str
    checkpoint_store: str
    blockers: tuple[str, ...]
    checkpoint_hash: str


@dataclass(frozen=True, slots=True)
class ConnectorFieldMappingPlanReceipt:
    """Connector field mapping plan with source, target, required target fields, and transform gates."""

    ready: bool
    source_system: str
    target_system: str
    target_fields: tuple[str, ...]
    blockers: tuple[str, ...]
    mapping_hash: str


@dataclass(frozen=True, slots=True)
class ExternalIdentityMapPlanReceipt:
    """External identity map plan with source, target, identity keys, mapping store, and collision gates."""

    ready: bool
    source_system: str
    target_system: str
    identity_keys: tuple[str, ...]
    blockers: tuple[str, ...]
    identity_hash: str


@dataclass(frozen=True, slots=True)
class SyncConflictResolutionPlanReceipt:
    """Sync conflict resolution plan with conflict keys, strategy, precedence, and audit gates."""

    ready: bool
    sync_name: str
    conflict_keys: tuple[str, ...]
    resolution_strategy: str
    blockers: tuple[str, ...]
    conflict_hash: str


@dataclass(frozen=True, slots=True)
class ConnectorRateLimitBudgetPlanReceipt:
    """Connector rate-limit budget plan with request window, burst, retry-after, and alert gates."""

    ready: bool
    connector_name: str
    requests_per_window: int
    window_seconds: int
    blockers: tuple[str, ...]
    budget_hash: str


@dataclass(frozen=True, slots=True)
class WebhookReplayWindowPlanReceipt:
    """Webhook replay window plan with replay horizon, dedupe key, signature, and receipt gates."""

    ready: bool
    webhook_name: str
    replay_window_minutes: int
    dedupe_key: str
    blockers: tuple[str, ...]
    replay_hash: str


@dataclass(frozen=True, slots=True)
class ConnectorErrorQuarantinePlanReceipt:
    """Connector error quarantine plan with error classes, sink, triage, and replay gates."""

    ready: bool
    connector_name: str
    error_classes: tuple[str, ...]
    quarantine_sink: str
    blockers: tuple[str, ...]
    quarantine_hash: str


@dataclass(frozen=True, slots=True)
class SyncReconciliationReportPlanReceipt:
    """Sync reconciliation report plan with counts, mismatch threshold, sample, and owner gates."""

    ready: bool
    sync_name: str
    source_count_field: str
    target_count_field: str
    blockers: tuple[str, ...]
    report_hash: str


@dataclass(frozen=True, slots=True)
class PrimitiveCandidateIntakeReceipt:
    """Primitive candidate intake result with visible edge, hidden member, and proof gates."""

    ready: bool
    primitive_id: str
    kind: str
    input_edge: str
    output_edge: str
    blockers: tuple[str, ...]
    intake_hash: str


@dataclass(frozen=True, slots=True)
class PrimitiveReuseObservationReceipt:
    """Primitive reuse observation with core edge, runtime-shape, and route-reuse gates."""

    ready: bool
    core_group_edge: str
    primitive_ids: tuple[str, ...]
    runtime_shapes: tuple[str, ...]
    blockers: tuple[str, ...]
    observation_hash: str


@dataclass(frozen=True, slots=True)
class PrimitiveProofCoverageMatrixReceipt:
    """Primitive proof coverage matrix with per-candidate requirement blockers."""

    ready: bool
    primitive_ids: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    blockers: tuple[str, ...]
    coverage_hash: str


@dataclass(frozen=True, slots=True)
class PrimitivePromotionReviewReceipt:
    """Primitive promotion review result with proof, owner-review, and truth-boundary gates."""

    promotion_allowed: bool
    primitive_id: str
    promotion_gate_status: str
    blockers: tuple[str, ...]
    review_hash: str


@dataclass(frozen=True, slots=True)
class RegistryPublishManifestPlanReceipt:
    """Registry publish manifest plan with card, proof, gate, and search-target coverage."""

    ready: bool
    registry_name: str
    card_count: int
    search_targets: tuple[str, ...]
    blockers: tuple[str, ...]
    manifest_hash: str


@dataclass(frozen=True, slots=True)
class BenchmarkRunArmPlanReceipt:
    """Benchmark run-arm plan with task, runner, metric, and artifact gates."""

    ready: bool
    arm_name: str
    task_count: int
    metrics: tuple[str, ...]
    blockers: tuple[str, ...]
    arm_hash: str


@dataclass(frozen=True, slots=True)
class PrimitiveLiftComparisonReceipt:
    """Baseline-vs-primitive lift comparison with dimension wins and blockers."""

    ready: bool
    baseline_arm: str
    candidate_arm: str
    winning_dimensions: tuple[str, ...]
    blockers: tuple[str, ...]
    comparison_hash: str


@dataclass(frozen=True, slots=True)
class TokenSavingsAttributionReceipt:
    """Token-savings attribution with baseline, candidate, primitive, and trace gates."""

    ready: bool
    baseline_tokens: int
    candidate_tokens: int
    savings_percent: float
    primitive_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    attribution_hash: str


@dataclass(frozen=True, slots=True)
class PitfallAvoidanceMatrixReceipt:
    """Pitfall avoidance matrix with evidence-backed avoided and unresolved pitfalls."""

    ready: bool
    pitfall_ids: tuple[str, ...]
    avoided_pitfalls: tuple[str, ...]
    unresolved_pitfalls: tuple[str, ...]
    blockers: tuple[str, ...]
    matrix_hash: str


@dataclass(frozen=True, slots=True)
class RoutePromotionEvidencePackReceipt:
    """Route promotion evidence pack with reuse, proof, lift, and owner gates."""

    ready: bool
    route_id: str
    primitive_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    blockers: tuple[str, ...]
    evidence_hash: str


@dataclass(frozen=True, slots=True)
class BenchmarkPrimitiveDecompositionReceipt:
    """Benchmark task decomposition into logical primitive components."""

    ready: bool
    task_id: str
    component_ids: tuple[str, ...]
    core_group_edges: tuple[str, ...]
    blockers: tuple[str, ...]
    decomposition_hash: str


@dataclass(frozen=True, slots=True)
class BenchmarkRouteTokenComparisonReceipt:
    """Benchmark route token comparison with component-level attribution."""

    ready: bool
    baseline_tokens: int
    primitive_route_tokens: int
    savings_percent: float
    component_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    comparison_hash: str


@dataclass(frozen=True, slots=True)
class BenchmarkTraceIngestionReceipt:
    """Normalized benchmark run artifacts paired into baseline-vs-primitive traces."""

    ready: bool
    pair_count: int
    task_ids: tuple[str, ...]
    trace_pairs: tuple[JsonRecord, ...]
    blockers: tuple[str, ...]
    ingestion_hash: str


@dataclass(frozen=True, slots=True)
class BenchmarkTracePairEvaluationReceipt:
    """Measured baseline-vs-primitive benchmark trace pair evaluation."""

    ready: bool
    task_id: str
    baseline_trace_ref: str
    primitive_trace_ref: str
    baseline_tokens: int
    primitive_tokens: int
    savings_percent: float
    component_ids: tuple[str, ...]
    primitive_ids: tuple[str, ...]
    proof_refs: tuple[str, ...]
    blockers: tuple[str, ...]
    evaluation_hash: str


@dataclass(frozen=True, slots=True)
class BenchmarkRoutePromotionCandidateReceipt:
    """Aggregated benchmark evidence for a reusable route promotion candidate."""

    ready: bool
    route_id: str
    primitive_ids: tuple[str, ...]
    task_ids: tuple[str, ...]
    runtime_shapes: tuple[str, ...]
    tool_consumers: tuple[str, ...]
    run_count: int
    average_savings_percent: float
    winning_run_percent: float
    blockers: tuple[str, ...]
    candidate_hash: str


@dataclass(frozen=True, slots=True)
class RuntimeShapeAdapterPlanReceipt:
    """Runtime-shape adapter plan preserving one core group edge."""

    ready: bool
    runtime_shape: str
    core_group_edge: str
    wrapper_edges: tuple[str, ...]
    adapter_mutators: tuple[str, ...]
    proof_requirements: tuple[str, ...]
    blockers: tuple[str, ...]
    adapter_hash: str


@dataclass(frozen=True, slots=True)
class RuntimeShapeAdapterMatrixReceipt:
    """Runtime-shape adapter matrix proving wrapper-only reuse across surfaces."""

    ready: bool
    core_group_edge: str
    runtime_shapes: tuple[str, ...]
    adapter_count: int
    blockers: tuple[str, ...]
    matrix_hash: str


@dataclass(frozen=True, slots=True)
class SurfacePrimitiveRegistryCardSetReceipt:
    """Candidate primitive registry cards compiled from API, event, or service surfaces."""

    ready: bool
    primitive_ids: tuple[str, ...]
    cards: tuple[JsonRecord, ...]
    blockers: tuple[str, ...]
    card_set_hash: str


def normalize_field_name(name: object) -> str:
    """Normalize an external field label to snake_case ASCII."""

    text = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode("ascii")
    text = _FIRST_CAP_RE.sub(r"\1_\2", text)
    text = _ALL_CAP_RE.sub(r"\1_\2", text)
    text = _NON_ALNUM_RE.sub("_", text)
    text = "_".join(part for part in text.strip("_").lower().split("_") if part)
    return text or "field"


def prepare_record_import(
    rows: Sequence[Mapping[str, Any]],
    *,
    required_fields: Sequence[str] = (),
    identity_fields: Sequence[str] = (),
    field_aliases: Mapping[str, str] | None = None,
    sort_fields: Sequence[str] = (),
    keep: str = KEEP_FIRST,
) -> PreparedRecordImport:
    """Prepare raw rows for import as one deterministic grouped primitive.

    The group expands to: field normalization, explicit aliases, collision
    preservation, required-field checks, identity dedupe, deterministic sort,
    schema fingerprinting, and idempotency-key generation.
    """

    if keep not in {KEEP_FIRST, KEEP_LAST}:
        raise ValueError("keep must be 'first' or 'last'")

    aliases = {
        normalize_field_name(source): normalize_field_name(target)
        for source, target in (field_aliases or {}).items()
    }
    required = tuple(normalize_field_name(field) for field in required_fields)
    identity = tuple(normalize_field_name(field) for field in identity_fields)
    sort_keys = tuple(normalize_field_name(field) for field in sort_fields)

    mappings: list[FieldMapping] = []
    collisions: list[FieldCollision] = []
    normalized_rows: list[JsonRecord] = []

    for row_index, row in enumerate(rows):
        normalized: JsonRecord = {}
        for source, value in row.items():
            source_text = str(source)
            base = normalize_field_name(source_text)
            target = aliases.get(base, base)
            final_target = target
            if final_target in normalized and normalized[final_target] != value:
                final_target = _next_available_field_name(target, normalized)
                collisions.append(FieldCollision(
                    row_index=row_index,
                    target=target,
                    source=source_text,
                    preserved_as=final_target,
                ))
            normalized[final_target] = value
            mappings.append(FieldMapping(source=source_text, normalized=base, target=final_target))
        normalized_rows.append(normalized)

    invalid_records = tuple(
        InvalidRecord(
            row_index=index,
            missing_fields=tuple(field for field in required if _blank(row.get(field))),
        )
        for index, row in enumerate(normalized_rows)
        if any(_blank(row.get(field)) for field in required)
    )

    deduped, duplicates = _dedupe_rows(normalized_rows, identity, keep=keep)
    if sort_keys:
        deduped = sorted(deduped, key=lambda row: tuple(_sort_value(row.get(field)) for field in sort_keys))

    schema_fields = sorted({field for row in deduped for field in row})
    schema_fingerprint = _digest({"fields": schema_fields}, chars=SCHEMA_FINGERPRINT_CHARS)
    idempotency_key = _digest({
        "identity_fields": identity,
        "prepared_records": deduped,
        "required_fields": required,
        "schema_fingerprint": schema_fingerprint,
    }, chars=IDEMPOTENCY_DIGEST_CHARS)

    return PreparedRecordImport(
        records=tuple(dict(row) for row in deduped),
        field_map=tuple(mappings),
        required_fields=required,
        identity_fields=identity,
        invalid_records=invalid_records,
        duplicates=tuple(duplicates),
        collisions=tuple(collisions),
        original_count=len(rows),
        prepared_count=len(deduped),
        duplicate_count=len(duplicates),
        schema_fingerprint=schema_fingerprint,
        idempotency_key=f"record-import:{idempotency_key}",
    )


def compile_exact_edge_route(
    start_edge: str,
    goal_edge: str,
    components: Sequence[RouteComponent | Mapping[str, Any]],
    *,
    adapter_components: Sequence[RouteComponent | Mapping[str, Any]] = (),
    max_steps: int = DEFAULT_ROUTE_MAX_STEPS,
) -> RoutePlan:
    """Compile the shortest deterministic route across exact input/output edges."""

    start = str(start_edge).strip()
    goal = str(goal_edge).strip()
    if not start or not goal:
        raise ValueError("start_edge and goal_edge are required")
    if max_steps < 1:
        raise ValueError("max_steps must be >= 1")
    if start == goal:
        return RoutePlan(start_edge=start, goal_edge=goal, components=(), edge_path=(start,), route_found=True)

    indexed = _index_components([*components, *adapter_components])
    queue: deque[tuple[str, tuple[RouteComponent, ...], tuple[str, ...]]] = deque([(start, (), (start,))])
    best_seen: dict[str, int] = {start: 0}

    while queue:
        current_edge, route, edge_path = queue.popleft()
        if len(route) >= max_steps:
            continue
        for component in indexed.get(current_edge, ()):
            next_route = (*route, component)
            next_path = (*edge_path, component.output_edge)
            if component.output_edge == goal:
                return RoutePlan(
                    start_edge=start,
                    goal_edge=goal,
                    components=next_route,
                    edge_path=next_path,
                    route_found=True,
                )
            if best_seen.get(component.output_edge, max_steps + 1) <= len(next_route):
                continue
            best_seen[component.output_edge] = len(next_route)
            queue.append((component.output_edge, next_route, next_path))

    return RoutePlan(
        start_edge=start,
        goal_edge=goal,
        components=(),
        edge_path=(start,),
        route_found=False,
        skipped_reason=NO_ROUTE_REASON,
    )


def collapse_route_to_group_card(plan: RoutePlan, *, group_id: str, title: str) -> dict[str, Any]:
    """Collapse a compiled route to one compact candidate card for LLM context."""

    return {
        "kind": "py.primitive_group",
        "primitive_id": group_id,
        "title": title,
        "input_edge": plan.start_edge,
        "output_edge": plan.goal_edge,
        "contract": {"input": plan.start_edge, "output": plan.goal_edge},
        "route_found": plan.route_found,
        "member_edges": [
            {
                "component_id": component.component_id,
                "input_edge": component.input_edge,
                "output_edge": component.output_edge,
                "operation": component.operation,
            }
            for component in plan.components
        ],
        "blackbox": {
            "does": f"Executes {len(plan.components)} hidden deterministic steps from {plan.start_edge} to {plan.goal_edge}.",
            "hidden_step_count": len(plan.components),
            "skipped_reason": plan.skipped_reason,
        },
        "candidate": True,
        "serves_truth": False,
    }


def plan_primitive_graph_runtime(
    route_spec: Mapping[str, Any],
    graph_policy: Mapping[str, Any],
) -> PrimitiveGraphRuntimePlanReceipt:
    """Plan an executable primitive graph from compact edge cards, not source code."""

    raw_route_id = str(route_spec.get("route_id") or route_spec.get("id") or route_spec.get("title") or "").strip()
    route_id = normalize_field_name(raw_route_id) if raw_route_id else ""
    start_edge = str(route_spec.get("start_edge") or route_spec.get("input_edge") or "").strip()
    goal_edge = str(route_spec.get("goal_edge") or route_spec.get("output_edge") or "").strip()
    primitive_cards = tuple(
        dict(item)
        for item in _as_mapping_sequence(
            route_spec.get("primitive_cards")
            or route_spec.get("cards")
            or route_spec.get("components")
        )
    )
    adapter_cards = tuple(
        dict(item)
        for item in _as_mapping_sequence(
            route_spec.get("adapter_cards")
            or route_spec.get("adapter_components")
        )
    )
    blockers: list[str] = []
    if graph_policy.get("require_route_id", True) and not route_id:
        blockers.append("missing_route_id")
    if not start_edge:
        blockers.append("missing_start_edge")
    if not goal_edge:
        blockers.append("missing_goal_edge")
    if not primitive_cards:
        blockers.append("missing_primitive_cards")

    def route_component_from_card(card: Mapping[str, Any], index: int) -> RouteComponent:
        primitive_id = str(card.get("primitive_id") or card.get("component_id") or card.get("id") or f"card_{index + 1}").strip()
        operation = str(card.get("kind") or card.get("operation") or card.get("function_name") or "primitive").strip()
        contract = card.get("contract") if isinstance(card.get("contract"), Mapping) else {}
        input_edge = str(card.get("input_edge") or contract.get("input") or "").strip()
        output_edge = str(card.get("output_edge") or contract.get("output") or "").strip()
        return RouteComponent(
            component_id=primitive_id,
            input_edge=input_edge,
            output_edge=output_edge,
            operation=operation,
            import_path=str(card.get("import_path") or ""),
            function_name=str(card.get("function_name") or ""),
            cost=int(card.get("cost") or 1),
        )

    route_components = [route_component_from_card(card, index) for index, card in enumerate(primitive_cards)]
    adapter_components = [route_component_from_card(card, index) for index, card in enumerate(adapter_cards)]
    all_cards_by_id = {
        str(card.get("primitive_id") or card.get("component_id") or card.get("id") or ""): card
        for card in (*primitive_cards, *adapter_cards)
    }
    for index, card in enumerate((*primitive_cards, *adapter_cards), start=1):
        card_id = str(card.get("primitive_id") or card.get("component_id") or card.get("id") or f"card_{index}").strip()
        if graph_policy.get("require_candidate_boundary"):
            if card.get("candidate") is not True:
                blockers.append(f"{card_id}:candidate_boundary_not_declared")
            if card.get("serves_truth") is not False:
                blockers.append(f"{card_id}:serves_truth_must_be_false")
        contract = card.get("contract") if isinstance(card.get("contract"), Mapping) else {}
        if not str(card.get("input_edge") or contract.get("input") or "").strip():
            blockers.append(f"{card_id}:missing_input_edge")
        if not str(card.get("output_edge") or contract.get("output") or "").strip():
            blockers.append(f"{card_id}:missing_output_edge")
        if graph_policy.get("require_short_blackbox") and _blank((card.get("blackbox") or {}).get("does") if isinstance(card.get("blackbox"), Mapping) else card.get("blackbox")):
            blockers.append(f"{card_id}:missing_blackbox")

    max_steps = int(graph_policy.get("max_steps") or DEFAULT_ROUTE_MAX_STEPS)
    plan = None
    if start_edge and goal_edge:
        plan = compile_exact_edge_route(
            start_edge,
            goal_edge,
            route_components,
            adapter_components=adapter_components,
            max_steps=max_steps,
        )
        if not plan.route_found:
            blockers.append(plan.skipped_reason or NO_ROUTE_REASON)
    ordered_primitive_ids = tuple(component.component_id for component in (plan.components if plan else ()))
    min_steps = int(graph_policy.get("min_steps") or 0)
    if min_steps and len(ordered_primitive_ids) < min_steps:
        blockers.append("route_step_count_below_policy")

    ordered_cards = tuple(all_cards_by_id.get(primitive_id, {}) for primitive_id in ordered_primitive_ids)
    hidden_member_edges: list[str] = []
    adapter_mutators: set[str] = set()
    proof_requirements: set[str] = set()
    effects: set[str] = set()
    runtime_targets: set[str] = set()
    for card in ordered_cards:
        for edge in _as_sequence(card.get("hidden_member_edges")):
            edge_text = str(edge).strip()
            if edge_text:
                hidden_member_edges.append(edge_text)
        for edge in _as_mapping_sequence(card.get("member_edges")):
            input_edge = str(edge.get("input_edge") or "").strip()
            output_edge = str(edge.get("output_edge") or "").strip()
            if input_edge and output_edge:
                hidden_member_edges.append(f"{input_edge} -> {output_edge}")
        adapter_mutators.update(
            normalize_field_name(value)
            for value in _as_sequence(card.get("adapter_mutators") or card.get("mutators"))
            if not _blank(value)
        )
        proof_requirements.update(
            normalize_field_name(value)
            for value in _as_sequence(card.get("proof_requirements"))
            if not _blank(value)
        )
        effects.update(
            normalize_field_name(value)
            for value in _as_sequence(card.get("effects"))
            if not _blank(value)
        )
        runtime_targets.update(
            normalize_field_name(value)
            for value in _as_sequence(card.get("runtime_targets"))
            if not _blank(value)
        )

    if graph_policy.get("require_hidden_member_edges") and not hidden_member_edges:
        blockers.append("missing_hidden_member_edges")
    if graph_policy.get("require_adapter_mutators") and not adapter_mutators:
        blockers.append("missing_adapter_mutators")
    if graph_policy.get("require_proof_requirements") and not proof_requirements:
        blockers.append("missing_proof_requirements")
    if graph_policy.get("require_runtime_targets") and not runtime_targets:
        blockers.append("missing_runtime_targets")
    for required in _as_sequence(graph_policy.get("required_proof_requirements")):
        required_name = normalize_field_name(required)
        if required_name and required_name not in proof_requirements:
            blockers.append(f"missing_proof_requirement:{required_name}")
    for required in _as_sequence(graph_policy.get("required_adapter_mutators")):
        required_name = normalize_field_name(required)
        if required_name and required_name not in adapter_mutators:
            blockers.append(f"missing_adapter_mutator:{required_name}")
    for required in _as_sequence(graph_policy.get("required_runtime_targets")):
        required_name = normalize_field_name(required)
        if required_name and required_name not in runtime_targets:
            blockers.append(f"missing_runtime_target:{required_name}")
    if graph_policy.get("require_candidate_boundary"):
        if route_spec.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if route_spec.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")
    plan_hash = "primitive-graph-runtime-plan:" + _digest(
        {
            "adapter_mutators": sorted(adapter_mutators),
            "blockers": blockers,
            "edge_path": plan.edge_path if plan else (),
            "ordered_primitive_ids": ordered_primitive_ids,
            "proof_requirements": sorted(proof_requirements),
            "route_id": route_id,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PrimitiveGraphRuntimePlanReceipt(
        ready=not blockers,
        route_id=route_id,
        start_edge=start_edge,
        goal_edge=goal_edge,
        ordered_primitive_ids=ordered_primitive_ids,
        edge_path=plan.edge_path if plan else (),
        hidden_member_edges=tuple(dict.fromkeys(hidden_member_edges)),
        adapter_mutators=tuple(sorted(adapter_mutators)),
        proof_requirements=tuple(sorted(proof_requirements)),
        effects=tuple(sorted(effects)),
        runtime_targets=tuple(sorted(runtime_targets)),
        blockers=tuple(blockers),
        candidate=True,
        serves_truth=False,
        plan_hash=plan_hash,
    )


def evaluate_primitive_consumer_readiness(
    card_bundle: Mapping[str, Any],
    readiness_policy: Mapping[str, Any],
) -> PrimitiveConsumerReadinessReceipt:
    """Check that compact primitive cards are consumable across product surfaces and coding tools."""

    primitive_cards = tuple(
        dict(item)
        for item in _as_mapping_sequence(
            card_bundle.get("primitive_cards")
            or card_bundle.get("cards")
            or card_bundle.get("edge_cards")
        )
    )
    consumer_surfaces = tuple(
        dict.fromkeys(
            normalize_field_name(surface)
            for surface in (
                _as_sequence(readiness_policy.get("consumer_surfaces"))
                or (
                    "teleon",
                    "aidevobserver",
                    "aidevexplorer",
                    "baltor",
                    "openhubforai",
                    "coding_agent",
                )
            )
            if not _blank(surface)
        )
    )
    development_tools = tuple(
        dict.fromkeys(
            normalize_field_name(tool)
            for tool in (
                _as_sequence(readiness_policy.get("development_tools"))
                or ("codex", "claude_code", "kimi", "glm", "gemma_4")
            )
            if not _blank(tool)
        )
    )
    blockers: list[str] = []
    if not primitive_cards:
        blockers.append("missing_primitive_cards")
    if readiness_policy.get("require_candidate_boundary", True):
        if card_bundle.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if card_bundle.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")

    max_edge_chars = int(readiness_policy.get("max_edge_chars") or 96)
    max_blackbox_words = int(readiness_policy.get("max_blackbox_words") or 48)
    min_search_terms = int(readiness_policy.get("min_search_terms_per_card") or 4)
    require_hidden_edges = readiness_policy.get("require_hidden_member_edges", True)
    require_mutators = readiness_policy.get("require_adapter_mutators", True)
    require_proofs = readiness_policy.get("require_proof_requirements", True)
    require_runtimes = readiness_policy.get("require_runtime_targets", True)
    require_effects = readiness_policy.get("require_effects", False)

    card_ids: list[str] = []
    visible_edges: list[str] = []
    all_search_terms: set[str] = set()
    all_proof_requirements: set[str] = set()
    all_runtime_targets: set[str] = set()
    surface_blockers: dict[str, list[str]] = {surface: [] for surface in consumer_surfaces}

    def add_surface_blocker(surface: str, blocker: str) -> None:
        if surface in surface_blockers:
            surface_blockers[surface].append(blocker)

    def card_blackbox_text(card: Mapping[str, Any]) -> str:
        blackbox = card.get("blackbox")
        if isinstance(blackbox, Mapping):
            return str(blackbox.get("does") or "").strip()
        return str(blackbox or "").strip()

    def card_hidden_edges(card: Mapping[str, Any]) -> tuple[str, ...]:
        hidden_edges = [str(edge).strip() for edge in _as_sequence(card.get("hidden_member_edges")) if not _blank(edge)]
        group_contract = card.get("group_contract") if isinstance(card.get("group_contract"), Mapping) else {}
        hidden_edges.extend(
            str(edge).strip()
            for edge in _as_sequence(group_contract.get("hidden_member_edges"))
            if not _blank(edge)
        )
        for edge in _as_mapping_sequence(card.get("member_edges")):
            input_edge = str(edge.get("input_edge") or "").strip()
            output_edge = str(edge.get("output_edge") or "").strip()
            if input_edge and output_edge:
                hidden_edges.append(f"{input_edge} -> {output_edge}")
        return tuple(dict.fromkeys(hidden_edges))

    def card_search_terms(card: Mapping[str, Any], input_edge: str, output_edge: str, blackbox_text: str) -> tuple[str, ...]:
        raw_values: list[Any] = [
            card.get("primitive_id"),
            card.get("kind"),
            card.get("title"),
            input_edge,
            output_edge,
            blackbox_text,
        ]
        raw_values.extend(_as_sequence(card.get("blocking_keys")))
        raw_values.extend(_as_sequence(card.get("capability_tags")))
        raw_values.extend(_as_sequence(card.get("domains")))
        terms: set[str] = set()
        for raw_value in raw_values:
            for piece in _NON_ALNUM_RE.split(str(raw_value or "")):
                if len(piece) >= 3:
                    terms.add(normalize_field_name(piece))
        return tuple(sorted(terms))

    for index, card in enumerate(primitive_cards, start=1):
        raw_card_id = str(card.get("primitive_id") or card.get("id") or card.get("component_id") or "").strip()
        card_id = raw_card_id or f"card_{index}"
        card_ids.append(card_id)
        contract = card.get("contract") if isinstance(card.get("contract"), Mapping) else {}
        input_edge = str(card.get("input_edge") or contract.get("input") or "").strip()
        output_edge = str(card.get("output_edge") or contract.get("output") or "").strip()
        blackbox_text = card_blackbox_text(card)
        hidden_edges = card_hidden_edges(card)
        adapter_mutators = tuple(
            normalize_field_name(value)
            for value in _as_sequence(card.get("adapter_mutators") or card.get("mutators"))
            if not _blank(value)
        )
        proof_requirements = tuple(
            normalize_field_name(value)
            for value in _as_sequence(card.get("proof_requirements"))
            if not _blank(value)
        )
        runtime_targets = tuple(
            normalize_field_name(value)
            for value in _as_sequence(card.get("runtime_targets"))
            if not _blank(value)
        )
        effects = tuple(
            normalize_field_name(value)
            for value in _as_sequence(card.get("effects"))
            if not _blank(value)
        )
        search_terms = card_search_terms(card, input_edge, output_edge, blackbox_text)
        all_search_terms.update(search_terms)
        all_proof_requirements.update(proof_requirements)
        all_runtime_targets.update(runtime_targets)
        if input_edge and output_edge:
            visible_edges.append(f"{input_edge} -> {output_edge}")

        if not raw_card_id:
            blockers.append(f"{card_id}:missing_primitive_id")
            add_surface_blocker("openhubforai", f"{card_id}:missing_primitive_id")
        if "@" not in raw_card_id and readiness_policy.get("require_versioned_ids", True):
            blockers.append(f"{card_id}:missing_versioned_id")
            add_surface_blocker("openhubforai", f"{card_id}:missing_versioned_id")
        if _blank(card.get("kind")):
            blockers.append(f"{card_id}:missing_kind")
            add_surface_blocker("openhubforai", f"{card_id}:missing_kind")
        if not input_edge:
            blockers.append(f"{card_id}:missing_input_edge")
            add_surface_blocker("teleon", f"{card_id}:missing_input_edge")
            add_surface_blocker("coding_agent", f"{card_id}:missing_input_edge")
        if not output_edge:
            blockers.append(f"{card_id}:missing_output_edge")
            add_surface_blocker("teleon", f"{card_id}:missing_output_edge")
            add_surface_blocker("coding_agent", f"{card_id}:missing_output_edge")
        if len(input_edge) > max_edge_chars:
            blockers.append(f"{card_id}:input_edge_too_long")
            add_surface_blocker("aidevobserver", f"{card_id}:input_edge_too_long")
            add_surface_blocker("coding_agent", f"{card_id}:input_edge_too_long")
        if len(output_edge) > max_edge_chars:
            blockers.append(f"{card_id}:output_edge_too_long")
            add_surface_blocker("aidevobserver", f"{card_id}:output_edge_too_long")
            add_surface_blocker("coding_agent", f"{card_id}:output_edge_too_long")
        if not blackbox_text:
            blockers.append(f"{card_id}:missing_blackbox")
            add_surface_blocker("aidevobserver", f"{card_id}:missing_blackbox")
            add_surface_blocker("coding_agent", f"{card_id}:missing_blackbox")
        if blackbox_text and len(blackbox_text.split()) > max_blackbox_words:
            blockers.append(f"{card_id}:blackbox_too_long")
            add_surface_blocker("aidevobserver", f"{card_id}:blackbox_too_long")
            add_surface_blocker("coding_agent", f"{card_id}:blackbox_too_long")
        if require_hidden_edges and not hidden_edges:
            blockers.append(f"{card_id}:missing_hidden_member_edges")
            add_surface_blocker("teleon", f"{card_id}:missing_hidden_member_edges")
        if require_mutators and not adapter_mutators:
            blockers.append(f"{card_id}:missing_adapter_mutators")
            add_surface_blocker("teleon", f"{card_id}:missing_adapter_mutators")
            add_surface_blocker("coding_agent", f"{card_id}:missing_adapter_mutators")
        if require_proofs and not proof_requirements:
            blockers.append(f"{card_id}:missing_proof_requirements")
            add_surface_blocker("teleon", f"{card_id}:missing_proof_requirements")
            add_surface_blocker("aidevexplorer", f"{card_id}:missing_proof_requirements")
            add_surface_blocker("coding_agent", f"{card_id}:missing_proof_requirements")
        if require_runtimes and not runtime_targets:
            blockers.append(f"{card_id}:missing_runtime_targets")
            add_surface_blocker("teleon", f"{card_id}:missing_runtime_targets")
            add_surface_blocker("aidevexplorer", f"{card_id}:missing_runtime_targets")
        if require_effects and not effects:
            blockers.append(f"{card_id}:missing_effects")
            add_surface_blocker("teleon", f"{card_id}:missing_effects")
            add_surface_blocker("baltor", f"{card_id}:missing_effects")
        if len(search_terms) < min_search_terms:
            blockers.append(f"{card_id}:insufficient_search_terms")
            add_surface_blocker("aidevobserver", f"{card_id}:insufficient_search_terms")
        if readiness_policy.get("require_candidate_boundary", True):
            if card.get("candidate") is not True:
                blockers.append(f"{card_id}:candidate_boundary_not_declared")
                add_surface_blocker("baltor", f"{card_id}:candidate_boundary_not_declared")
            if card.get("serves_truth") is not False:
                blockers.append(f"{card_id}:serves_truth_must_be_false")
                add_surface_blocker("baltor", f"{card_id}:serves_truth_must_be_false")

    ready_surfaces = tuple(
        surface
        for surface in consumer_surfaces
        if not surface_blockers.get(surface)
    )
    consumer_statuses = tuple(
        f"{surface}:{'ready' if surface in ready_surfaces else 'blocked'}"
        for surface in consumer_surfaces
    ) + tuple(
        f"{tool}:{'edge_card_ready' if not surface_blockers.get('coding_agent') and not blockers else 'blocked'}"
        for tool in development_tools
    )
    readiness_hash = "primitive-consumer-readiness:" + _digest(
        {
            "blockers": blockers,
            "card_ids": card_ids,
            "consumer_surfaces": consumer_surfaces,
            "development_tools": development_tools,
            "visible_edges": visible_edges,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PrimitiveConsumerReadinessReceipt(
        ready=not blockers,
        card_count=len(primitive_cards),
        consumer_surfaces=consumer_surfaces,
        ready_surfaces=ready_surfaces,
        card_ids=tuple(card_ids),
        visible_edges=tuple(dict.fromkeys(visible_edges)),
        searchable_terms=tuple(sorted(all_search_terms)),
        proof_requirements=tuple(sorted(all_proof_requirements)),
        runtime_targets=tuple(sorted(all_runtime_targets)),
        development_tools=development_tools,
        blockers=tuple(blockers),
        consumer_statuses=consumer_statuses,
        candidate=True,
        serves_truth=False,
        readiness_hash=readiness_hash,
    )


def evaluate_primitive_registry_expansion_coverage(
    registry_snapshot: Mapping[str, Any],
    coverage_policy: Mapping[str, Any],
) -> PrimitiveRegistryExpansionCoverageReceipt:
    """Audit whether the candidate primitive registry covers required families and runtimes."""

    card_fields = (
        "cards",
        "candidate_cards",
        "primitive_cards",
        "source_backed_cards",
        "runtime_shape_cards",
        "primitive_kind_cards",
        "benchmark_decomposition_cards",
    )
    candidate_cards: list[dict[str, Any]] = []
    for field in card_fields:
        candidate_cards.extend(dict(item) for item in _as_mapping_sequence(registry_snapshot.get(field)))
    proof_bundles = tuple(
        dict(item)
        for item in _as_mapping_sequence(
            registry_snapshot.get("proof_bundles")
            or registry_snapshot.get("proofs")
        )
    )
    search_smokes = tuple(
        dict(item)
        for item in _as_mapping_sequence(
            registry_snapshot.get("search_smokes")
            or registry_snapshot.get("search_results")
        )
    )
    blockers: list[str] = []
    if not candidate_cards:
        blockers.append("missing_candidate_cards")
    if coverage_policy.get("require_candidate_boundary", True):
        if registry_snapshot.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if registry_snapshot.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")

    required_kinds = tuple(
        dict.fromkeys(
            normalize_field_name(kind)
            for kind in _as_sequence(coverage_policy.get("required_kinds"))
            if not _blank(kind)
        )
    )
    required_runtime_targets = tuple(
        dict.fromkeys(
            normalize_field_name(target)
            for target in _as_sequence(coverage_policy.get("required_runtime_targets"))
            if not _blank(target)
        )
    )
    required_source_families = tuple(
        dict.fromkeys(
            normalize_field_name(source_family)
            for source_family in _as_sequence(coverage_policy.get("required_source_families"))
            if not _blank(source_family)
        )
    )
    required_search_ids = tuple(
        dict.fromkeys(
            str(search_id).strip()
            for search_id in _as_sequence(coverage_policy.get("required_search_smoke_ids"))
            if str(search_id).strip()
        )
    )
    min_cards = int(coverage_policy.get("min_cards") or 0)
    if min_cards and len(candidate_cards) < min_cards:
        blockers.append("card_count_below_policy")

    covered_kinds: set[str] = set()
    covered_runtime_targets: set[str] = set()
    covered_source_families: set[str] = set()
    candidate_ids: list[str] = []
    source_backed_candidate_ids: list[str] = []
    for index, card in enumerate(candidate_cards, start=1):
        primitive_id = str(card.get("primitive_id") or card.get("id") or f"card_{index}").strip()
        candidate_ids.append(primitive_id)
        kind = normalize_field_name(card.get("kind") or "")
        if kind:
            covered_kinds.add(kind)
        for runtime_target in _as_sequence(card.get("runtime_targets")):
            if not _blank(runtime_target):
                covered_runtime_targets.add(normalize_field_name(runtime_target))
        source_family = normalize_field_name(card.get("source_family") or "")
        if source_family:
            covered_source_families.add(source_family)
        if card.get("source_evidence_status") == "source_backed" or source_family in {"curated_first_party_primitive_group", "source_backed"}:
            source_backed_candidate_ids.append(primitive_id)
        if coverage_policy.get("require_candidate_boundary", True):
            if card.get("candidate") is not True:
                blockers.append(f"{primitive_id}:candidate_boundary_not_declared")
            if card.get("serves_truth") is not False:
                blockers.append(f"{primitive_id}:serves_truth_must_be_false")

    missing_kinds = tuple(kind for kind in required_kinds if kind not in covered_kinds)
    missing_runtime_targets = tuple(target for target in required_runtime_targets if target not in covered_runtime_targets)
    missing_source_families = tuple(source_family for source_family in required_source_families if source_family not in covered_source_families)
    if missing_kinds:
        blockers.append("required_kinds_missing")
    if missing_runtime_targets:
        blockers.append("required_runtime_targets_missing")
    if missing_source_families:
        blockers.append("required_source_families_missing")

    required_proof_status = str(coverage_policy.get("required_proof_status") or "pass").strip()
    proofed_primitive_ids = tuple(
        sorted(
            {
                str(proof.get("subject_id") or proof.get("primitive_id") or "").strip()
                for proof in proof_bundles
                if str(proof.get("subject_id") or proof.get("primitive_id") or "").strip()
                and (not required_proof_status or str(proof.get("status") or "").strip() == required_proof_status)
            }
        )
    )
    proof_required_ids = (
        tuple(source_backed_candidate_ids)
        if coverage_policy.get("require_proof_for_source_backed_only", True)
        else tuple(candidate_ids)
    )
    unproofed_primitive_ids = tuple(
        primitive_id
        for primitive_id in dict.fromkeys(proof_required_ids)
        if primitive_id and primitive_id not in proofed_primitive_ids
    )
    if coverage_policy.get("require_proof_bundles", True) and unproofed_primitive_ids:
        blockers.append("proof_bundle_coverage_missing")

    max_search_rank = int(coverage_policy.get("max_search_rank") or 1)
    search_smoke_ids: list[str] = []
    search_smoke_index: dict[str, int] = {}
    for index, smoke in enumerate(search_smokes, start=1):
        smoke_id = str(smoke.get("expected_id") or smoke.get("primitive_id") or smoke.get("id") or f"search_smoke_{index}").strip()
        search_smoke_ids.append(smoke_id)
        try:
            rank = int(smoke.get("rank") or smoke.get("observed_rank") or 0)
        except (TypeError, ValueError):
            rank = 0
        search_smoke_index[smoke_id] = rank
        if coverage_policy.get("require_search_smokes") and (rank < 1 or rank > max_search_rank):
            blockers.append(f"{smoke_id}:search_rank_above_policy")
    for required_id in required_search_ids:
        if required_id not in search_smoke_index:
            blockers.append(f"{required_id}:missing_search_smoke")
    if coverage_policy.get("require_search_smokes") and not search_smokes:
        blockers.append("missing_search_smokes")

    coverage_hash = "primitive-registry-expansion-coverage:" + _digest(
        {
            "blockers": blockers,
            "candidate_ids": candidate_ids,
            "covered_kinds": sorted(covered_kinds),
            "covered_runtime_targets": sorted(covered_runtime_targets),
            "covered_source_families": sorted(covered_source_families),
            "search_smoke_ids": search_smoke_ids,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PrimitiveRegistryExpansionCoverageReceipt(
        ready=not blockers,
        card_count=len(candidate_cards),
        covered_kinds=tuple(sorted(covered_kinds)),
        missing_kinds=missing_kinds,
        covered_runtime_targets=tuple(sorted(covered_runtime_targets)),
        missing_runtime_targets=missing_runtime_targets,
        covered_source_families=tuple(sorted(covered_source_families)),
        missing_source_families=missing_source_families,
        proofed_primitive_ids=proofed_primitive_ids,
        unproofed_primitive_ids=unproofed_primitive_ids,
        search_smoke_ids=tuple(search_smoke_ids),
        blockers=tuple(blockers),
        candidate=True,
        serves_truth=False,
        coverage_hash=coverage_hash,
    )


def guarded_replace_file(target_path: Path, content: str, archive_dir: Path, *, reason: str) -> GuardedWriteReceipt:
    """Archive existing file content before replacing it with new content."""

    target = Path(target_path)
    archive_root = Path(archive_dir)
    archive_root.mkdir(parents=True, exist_ok=True)
    manifest_path = archive_root / MANIFEST_NAME

    archive_path: Path | None = None
    previous_digest: str | None = None
    if target.exists():
        previous_bytes = target.read_bytes()
        previous_digest = _bytes_digest(previous_bytes)
        archive_name = f"{_utc_stamp()}_{previous_digest}_{target.name}"
        archive_path = archive_root / archive_name
        shutil.copy2(target, archive_path)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    new_digest = _bytes_digest(content.encode("utf-8"))

    receipt = GuardedWriteReceipt(
        target_path=str(target),
        archive_path=str(archive_path) if archive_path else None,
        manifest_path=str(manifest_path),
        previous_digest=previous_digest,
        new_digest=new_digest,
        reason=reason,
    )
    _append_manifest_event(manifest_path, {
        "archive_path": receipt.archive_path,
        "new_digest": receipt.new_digest,
        "previous_digest": receipt.previous_digest,
        "reason": reason,
        "target_path": receipt.target_path,
        "written_at": _utc_stamp(),
    })
    return receipt


def evaluate_policy_api_request(
    request_payload: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    actor_scopes: Sequence[str] = (),
    required_scopes: Sequence[str] = (),
    idempotency_keys_seen: Sequence[str] = (),
) -> PolicyApiRequestDecision:
    """Validate an API request, enforce scopes, and emit a decision receipt."""

    validation_errors = tuple(_validate_schema_subset(request_payload, schema))
    required = {str(scope) for scope in required_scopes}
    actor = {str(scope) for scope in actor_scopes}
    missing_scopes = tuple(sorted(required - actor))
    idempotency_key = str(request_payload.get("idempotency_key") or "").strip()
    if not idempotency_key:
        idempotency_key = "request:" + _digest(
            {"payload": dict(request_payload), "required_scopes": sorted(required)},
            chars=RECEIPT_DIGEST_CHARS,
        )
    duplicate = idempotency_key in {str(value) for value in idempotency_keys_seen}

    if validation_errors:
        status = "invalid_request"
    elif missing_scopes:
        status = "missing_scope"
    elif duplicate:
        status = "duplicate_request"
    else:
        status = "allowed"

    decision_receipt = "policy-api:" + _digest(
        {
            "idempotency_key": idempotency_key,
            "missing_scopes": missing_scopes,
            "status": status,
            "validation_errors": [asdict(error) for error in validation_errors],
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PolicyApiRequestDecision(
        allowed=status == "allowed",
        status=status,
        validation_errors=validation_errors,
        missing_scopes=missing_scopes,
        idempotency_key=idempotency_key,
        decision_receipt=decision_receipt,
    )


def resolve_tenant_settings(
    defaults: Mapping[str, Any],
    tenant_overrides: Mapping[str, Any],
    *,
    schema: Mapping[str, Any] | None = None,
    secret_fields: Sequence[str] = (),
    version: str = "",
) -> TenantSettingsResolution:
    """Resolve tenant settings with override precedence, validation, and redaction."""

    secret_names = {normalize_field_name(field) for field in secret_fields}
    keys = sorted({str(key) for key in defaults} | {str(key) for key in tenant_overrides})
    effective: JsonRecord = {}
    redacted: JsonRecord = {}
    sources: list[SettingSource] = []
    for key in keys:
        if key in tenant_overrides and tenant_overrides.get(key) is not None:
            value = tenant_overrides[key]
            source = "tenant_override"
        else:
            value = defaults.get(key)
            source = "default"
        effective[key] = value
        redacted[key] = "***" if normalize_field_name(key) in secret_names and not _blank(value) else value
        sources.append(SettingSource(key=key, source=source))

    validation_errors = tuple(_validate_schema_subset(effective, schema or {}))
    settings_hash = "settings:" + _digest(
        {
            "effective": effective,
            "schema": dict(schema or {}),
            "version": version,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return TenantSettingsResolution(
        effective_settings=effective,
        redacted_settings=redacted,
        setting_sources=tuple(sources),
        validation_errors=validation_errors,
        settings_hash=settings_hash,
    )


def evaluate_deployment_readiness(spec: Mapping[str, Any]) -> DeploymentReadinessReport:
    """Check deployment config, secrets, health probes, rollback, and limits."""

    checks: list[DeploymentReadinessCheck] = []
    config = spec.get("config") if isinstance(spec.get("config"), Mapping) else {}
    required_config = tuple(str(key) for key in _as_sequence(spec.get("required_config_keys")))
    missing_config = tuple(key for key in required_config if _blank(config.get(key)))
    checks.append(DeploymentReadinessCheck(
        check_id="required_config",
        passed=not missing_config,
        detail="missing: " + ",".join(missing_config) if missing_config else "all required config present",
    ))

    secret_refs = spec.get("secret_refs") if isinstance(spec.get("secret_refs"), Mapping) else {}
    inline_secret_keys = tuple(
        str(key)
        for key, value in secret_refs.items()
        if not _valid_secret_ref(value)
    )
    checks.append(DeploymentReadinessCheck(
        check_id="secret_refs",
        passed=not inline_secret_keys,
        detail="inline or invalid refs: " + ",".join(inline_secret_keys) if inline_secret_keys else "secret refs are indirect",
    ))

    health_checks = [item for item in _as_sequence(spec.get("health_checks")) if isinstance(item, Mapping)]
    bad_probe_ids = tuple(
        str(item.get("id") or index)
        for index, item in enumerate(health_checks)
        if not str(item.get("path") or "").startswith("/")
    )
    checks.append(DeploymentReadinessCheck(
        check_id="health_checks",
        passed=bool(health_checks) and not bad_probe_ids,
        detail="bad probe paths: " + ",".join(bad_probe_ids) if bad_probe_ids else "health checks declared",
    ))

    rollback_plan = spec.get("rollback_plan") if isinstance(spec.get("rollback_plan"), Mapping) else {}
    checks.append(DeploymentReadinessCheck(
        check_id="rollback_plan",
        passed=bool(rollback_plan.get("steps") or rollback_plan.get("strategy")),
        detail="rollback plan declared" if rollback_plan else "rollback plan missing",
    ))

    resources = spec.get("resources") if isinstance(spec.get("resources"), Mapping) else {}
    checks.append(DeploymentReadinessCheck(
        check_id="resource_limits",
        passed=bool(resources.get("limits")),
        detail="resource limits declared" if resources.get("limits") else "resource limits missing",
    ))

    blockers = tuple(check.check_id for check in checks if not check.passed)
    receipt_hash = "deploy-ready:" + _digest(
        {"blockers": blockers, "checks": [asdict(check) for check in checks]},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DeploymentReadinessReport(
        ready=not blockers,
        checks=tuple(checks),
        blockers=blockers,
        receipt_hash=receipt_hash,
    )


def evaluate_prompt_model_outputs(
    cases: Sequence[Mapping[str, Any]],
    outputs: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> PromptEvalReport:
    """Score fixed prompt/model outputs with deterministic required-term checks."""

    output_by_id = _outputs_by_case_id(outputs)
    results: list[PromptEvalCaseResult] = []
    for index, case in enumerate(cases):
        case_id = str(case.get("id") or f"case-{index + 1}")
        output_text = str(output_by_id.get(case_id) or "")
        required_terms = tuple(
            str(term).lower()
            for term in _as_sequence(case.get("expected_terms") or case.get("required_terms"))
            if str(term).strip()
        )
        if not required_terms and case.get("expected_substring"):
            required_terms = (str(case["expected_substring"]).lower(),)
        haystack = output_text.lower()
        missing = tuple(term for term in required_terms if term not in haystack)
        passed = not missing and bool(output_text.strip())
        results.append(PromptEvalCaseResult(
            case_id=case_id,
            passed=passed,
            score=1.0 if passed else 0.0,
            missing_terms=missing,
        ))

    total = len(results)
    passed_count = sum(1 for result in results if result.passed)
    pass_rate = round(passed_count / total, 4) if total else 0.0
    failed_case_ids = tuple(result.case_id for result in results if not result.passed)
    report_hash = "prompt-eval:" + _digest(
        {"failed": failed_case_ids, "passed": passed_count, "total": total},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PromptEvalReport(
        case_results=tuple(results),
        passed_count=passed_count,
        total_count=total,
        pass_rate=pass_rate,
        failed_case_ids=failed_case_ids,
        report_hash=report_hash,
    )


def plan_database_migration(
    database_state: Mapping[str, Any],
    migration_spec: Mapping[str, Any],
) -> DatabaseMigrationReceipt:
    """Build a deterministic migration plan with rollback and proof gates."""

    operations: list[DatabaseMigrationOperation] = []
    blockers: list[str] = []
    integrity_checks = {"dry_run_plan", "schema_contract_check", "row_count_before_after"}
    destructive_ops = {"drop_table", "drop_column", "truncate", "delete_rows"}
    op_rows = [
        row
        for row in _as_mapping_sequence(migration_spec.get("operations") or migration_spec.get("steps"))
    ]
    rollback_steps = tuple(str(step) for step in _as_sequence(
        migration_spec.get("rollback_steps") or migration_spec.get("rollback")
    ) if str(step).strip())

    for index, row in enumerate(op_rows):
        operation = normalize_field_name(row.get("op") or row.get("operation") or "unknown")
        table = str(row.get("table") or "").strip()
        column = str(row.get("column") or row.get("name") or "").strip()
        destructive = bool(row.get("destructive")) or operation in destructive_ops
        if not table:
            blockers.append(f"operation_{index + 1}_missing_table")
        if operation == "unknown":
            blockers.append(f"operation_{index + 1}_missing_operation")
        if destructive:
            integrity_checks.add("destructive_change_review")
        if operation in {"backfill", "update_rows"} and not row.get("batch_size"):
            blockers.append(f"operation_{index + 1}_missing_batch_size")
        if operation in {"set_not_null", "add_foreign_key"}:
            integrity_checks.add(f"{operation}_validation")
        statement_hint = _migration_statement_hint(operation=operation, table=table, column=column, row=row)
        operations.append(DatabaseMigrationOperation(
            operation_id=str(row.get("id") or f"op-{index + 1}"),
            operation=operation,
            table=table,
            column=column,
            destructive=destructive,
            statement_hint=statement_hint,
        ))

    if not operations:
        blockers.append("no_migration_operations")
    if any(operation.destructive for operation in operations) and not rollback_steps:
        blockers.append("destructive_change_requires_rollback")
    known_tables = database_state.get("tables") if isinstance(database_state.get("tables"), Mapping) else {}
    missing_tables = tuple(
        operation.table
        for operation in operations
        if operation.table and isinstance(known_tables, Mapping) and known_tables and operation.table not in known_tables
    )
    blockers.extend(f"unknown_table:{table}" for table in sorted(set(missing_tables)))

    receipt_hash = "db-migration:" + _digest(
        {
            "blockers": sorted(set(blockers)),
            "integrity_checks": sorted(integrity_checks),
            "operations": [asdict(operation) for operation in operations],
            "rollback_steps": rollback_steps,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DatabaseMigrationReceipt(
        operations=tuple(operations),
        rollback_steps=rollback_steps,
        integrity_checks=tuple(sorted(integrity_checks)),
        blockers=tuple(sorted(dict.fromkeys(blockers))),
        ready_for_dry_run=bool(operations) and not blockers,
        receipt_hash=receipt_hash,
    )


def compile_integration_sync_plan(
    source_delta: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    sync_policy: Mapping[str, Any],
) -> IntegrationSyncReceipt:
    """Compile source-system deltas into deterministic target mutations."""

    records = _source_delta_records(source_delta)
    field_mapping = sync_policy.get("field_mapping") if isinstance(sync_policy.get("field_mapping"), Mapping) else {}
    id_fields = tuple(str(field) for field in _as_sequence(sync_policy.get("identity_fields") or sync_policy.get("id_fields")) if str(field).strip())
    operation = normalize_field_name(sync_policy.get("operation") or sync_policy.get("mode") or "upsert")
    target_system = str(sync_policy.get("target_system") or "target").strip()
    proof_requirements = (
        "source_fixture_test",
        "target_contract_test",
        "idempotent_sync_test",
        "field_mapping_review",
    )

    mutations: list[IntegrationMutation] = []
    skipped: list[int] = []
    seen_keys: set[str] = set()
    for index, record in enumerate(records):
        key_parts = tuple(str(record.get(field) or "").strip() for field in id_fields) if id_fields else (str(index),)
        if any(not part for part in key_parts):
            skipped.append(index)
            continue
        target_key = "|".join(key_parts)
        if target_key in seen_keys:
            skipped.append(index)
            continue
        seen_keys.add(target_key)
        payload: JsonRecord = {}
        for source_field, value in record.items():
            target_field = str(field_mapping.get(source_field) or field_mapping.get(normalize_field_name(source_field)) or normalize_field_name(source_field))
            payload[target_field] = value
        mutation_id = "mutation:" + _digest(
            {"operation": operation, "payload": payload, "target_key": target_key, "target_system": target_system},
            chars=RECEIPT_DIGEST_CHARS,
        )
        mutations.append(IntegrationMutation(
            mutation_id=mutation_id,
            operation=operation,
            target_system=target_system,
            target_key=target_key,
            payload=payload,
        ))

    idempotency_key = "integration-sync:" + _digest(
        {
            "mutations": [asdict(mutation) for mutation in mutations],
            "skipped": skipped,
            "source_count": len(records),
            "target_system": target_system,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return IntegrationSyncReceipt(
        mutations=tuple(mutations),
        skipped_records=tuple(skipped),
        source_count=len(records),
        mutation_count=len(mutations),
        idempotency_key=idempotency_key,
        proof_requirements=proof_requirements,
    )


def assemble_cited_answer(
    question: str,
    evidence: Sequence[Mapping[str, Any]],
    *,
    retrieval_policy: Mapping[str, Any] | None = None,
) -> CitedAnswerReceipt:
    """Assemble a deterministic answer from retrieved evidence with citations."""

    policy = retrieval_policy or {}
    max_citations = int(policy.get("max_citations") or 3)
    required_terms = tuple(
        str(term).lower()
        for term in _as_sequence(policy.get("required_terms"))
        if str(term).strip()
    )
    question_tokens = {
        normalize_field_name(token)
        for token in re.findall(r"[A-Za-z0-9]+", question.lower())
        if len(token) > 2
    }
    scored: list[Citation] = []
    for index, row in enumerate(evidence):
        text = str(row.get("text") or row.get("snippet") or row.get("quote") or "")
        source_id = str(row.get("source_id") or row.get("doc_id") or f"source-{index + 1}")
        span = str(row.get("span") or row.get("loc") or "")
        text_tokens = {
            normalize_field_name(token)
            for token in re.findall(r"[A-Za-z0-9]+", text.lower())
            if len(token) > 2
        }
        score = len(question_tokens & text_tokens)
        if score <= 0 and question_tokens:
            continue
        quote = text.strip()
        if len(quote) > 220:
            quote = quote[:217].rstrip() + "..."
        scored.append(Citation(source_id=source_id, span=span, quote=quote, score=score))

    citations = tuple(sorted(scored, key=lambda item: (-item.score, item.source_id, item.span))[:max_citations])
    if citations:
        answer = " ".join(citation.quote.rstrip(".") + "." for citation in citations)
    else:
        answer = "No grounded answer could be assembled from the provided evidence."
    haystack = answer.lower()
    missing_terms = tuple(term for term in required_terms if term not in haystack)
    grounded = bool(citations) and not missing_terms
    receipt_hash = "cited-answer:" + _digest(
        {
            "answer": answer,
            "citations": [asdict(citation) for citation in citations],
            "missing_terms": missing_terms,
            "question": question,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return CitedAnswerReceipt(
        answer=answer,
        citations=citations,
        grounded=grounded,
        missing_terms=missing_terms,
        receipt_hash=receipt_hash,
    )


def verify_webhook_event(
    event_envelope: Mapping[str, Any],
    verification_policy: Mapping[str, Any],
) -> WebhookEventReceipt:
    """Verify a webhook envelope, dedupe it, and map a domain event receipt."""

    headers = event_envelope.get("headers") if isinstance(event_envelope.get("headers"), Mapping) else {}
    body = event_envelope.get("body") if isinstance(event_envelope.get("body"), Mapping) else {}
    event_id = str(event_envelope.get("event_id") or body.get("id") or "").strip()
    event_type = str(event_envelope.get("event_type") or body.get("type") or "").strip()
    blockers: list[str] = []

    required_headers = tuple(str(value) for value in _as_sequence(verification_policy.get("required_headers")) if str(value).strip())
    for header in required_headers:
        if _blank(headers.get(header)):
            blockers.append(f"missing_header:{header}")

    signature_header = str(verification_policy.get("signature_header") or "").strip()
    expected_signature = str(verification_policy.get("expected_signature") or "").strip()
    if signature_header or expected_signature:
        actual_signature = str(headers.get(signature_header) or "").strip()
        if not signature_header:
            blockers.append("signature_header_not_declared")
        elif not actual_signature:
            blockers.append(f"missing_signature:{signature_header}")
        elif expected_signature and actual_signature != expected_signature:
            blockers.append("signature_mismatch")

    if not event_id:
        blockers.append("missing_event_id")
    if not event_type:
        blockers.append("missing_event_type")
    seen_ids = {str(value) for value in _as_sequence(verification_policy.get("dedupe_event_ids"))}
    if event_id and event_id in seen_ids:
        blockers.append("duplicate_event")

    required_body_fields = tuple(str(value) for value in _as_sequence(verification_policy.get("required_body_fields")) if str(value).strip())
    for field in required_body_fields:
        if _blank(body.get(field)):
            blockers.append(f"missing_body_field:{field}")

    domain_event = {
        "event_id": event_id,
        "event_type": event_type,
        "payload": dict(body),
        "source": str(verification_policy.get("source") or event_envelope.get("source") or "webhook"),
    }
    status = "verified" if not blockers else ("duplicate" if blockers == ["duplicate_event"] else "rejected")
    idempotency_key = "webhook:" + _digest(
        {"event_id": event_id, "event_type": event_type, "source": domain_event["source"]},
        chars=RECEIPT_DIGEST_CHARS,
    )
    receipt_hash = "webhook-receipt:" + _digest(
        {"blockers": blockers, "domain_event": domain_event, "status": status},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return WebhookEventReceipt(
        verified=status == "verified",
        status=status,
        event_id=event_id,
        event_type=event_type,
        domain_event=domain_event,
        blockers=tuple(blockers),
        idempotency_key=idempotency_key,
        receipt_hash=receipt_hash,
    )


def plan_queue_job_execution(
    message: Mapping[str, Any],
    worker_policy: Mapping[str, Any],
) -> QueueJobExecutionReceipt:
    """Plan queue-worker execution with validation, retry, and dead-letter rules."""

    payload = message.get("payload") if isinstance(message.get("payload"), Mapping) else {}
    message_id = str(message.get("message_id") or message.get("id") or "").strip()
    job_type = str(message.get("job_type") or payload.get("job_type") or "").strip()
    current_attempt = int(message.get("attempt") or message.get("current_attempt") or 0)
    max_attempts = int(worker_policy.get("max_attempts") or 3)
    retry_after_seconds = int(worker_policy.get("retry_after_seconds") or 0)
    blockers: list[str] = []

    allowed_job_types = {str(value) for value in _as_sequence(worker_policy.get("allowed_job_types")) if str(value).strip()}
    if not message_id:
        blockers.append("missing_message_id")
    if not job_type:
        blockers.append("missing_job_type")
    elif allowed_job_types and job_type not in allowed_job_types:
        blockers.append("job_type_not_allowed")

    for field in _as_sequence(worker_policy.get("required_payload_fields")):
        field_name = str(field)
        if field_name and _blank(payload.get(field_name)):
            blockers.append(f"missing_payload_field:{field_name}")

    seen_messages = {str(value) for value in _as_sequence(worker_policy.get("processed_message_ids"))}
    if message_id and message_id in seen_messages:
        blockers.append("duplicate_message")

    if current_attempt >= max_attempts:
        action = "dead_letter"
    elif blockers:
        action = "reject" if "duplicate_message" in blockers or "job_type_not_allowed" in blockers else "retry_later"
    else:
        action = "execute"
    accepted = action == "execute"
    idempotency_key = "queue-job:" + _digest(
        {"job_type": job_type, "message_id": message_id, "payload": dict(payload)},
        chars=RECEIPT_DIGEST_CHARS,
    )
    receipt_hash = "queue-job:" + _digest(
        {"action": action, "blockers": blockers, "idempotency_key": idempotency_key},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return QueueJobExecutionReceipt(
        accepted=accepted,
        action=action,
        job_type=job_type,
        message_id=message_id,
        blockers=tuple(blockers),
        retry_after_seconds=retry_after_seconds if action == "retry_later" else 0,
        idempotency_key=idempotency_key,
        receipt_hash=receipt_hash,
    )


def plan_queue_payload_contract(
    queue_contract: Mapping[str, Any],
    contract_policy: Mapping[str, Any],
) -> QueuePayloadContractPlanReceipt:
    """Plan a queue payload contract with schema, required fields, headers, and fixtures."""

    raw_queue_name = str(queue_contract.get("queue_name") or queue_contract.get("name") or "").strip()
    queue_name = normalize_field_name(raw_queue_name) if raw_queue_name else ""
    schema_ref = str(queue_contract.get("schema_ref") or queue_contract.get("schema") or "").strip()
    payload_schema = queue_contract.get("payload_schema") if isinstance(queue_contract.get("payload_schema"), Mapping) else {}
    schema_required_fields = {
        normalize_field_name(value)
        for value in _as_sequence(payload_schema.get("required"))
        if not _blank(value)
    }
    schema_properties = {
        normalize_field_name(value)
        for value in (payload_schema.get("properties") if isinstance(payload_schema.get("properties"), Mapping) else {}).keys()
        if not _blank(value)
    }
    required_fields = tuple(
        normalize_field_name(value)
        for value in _as_sequence(contract_policy.get("required_fields"))
        if not _blank(value)
    )
    headers = queue_contract.get("headers")
    header_names = (
        {str(key).strip().lower() for key in headers.keys() if str(key).strip()}
        if isinstance(headers, Mapping)
        else {str(value).strip().lower() for value in _as_sequence(headers) if str(value).strip()}
    )
    required_headers = tuple(str(value).strip() for value in _as_sequence(contract_policy.get("required_headers")) if str(value).strip())
    blockers: list[str] = []
    if not queue_name:
        blockers.append("missing_queue_name")
    if contract_policy.get("require_schema_ref") and not schema_ref:
        blockers.append("missing_schema_ref")
    if not payload_schema:
        blockers.append("missing_payload_schema")
    for field in required_fields:
        if field not in schema_required_fields:
            blockers.append(f"missing_required_field:{field}")
        if schema_properties and field not in schema_properties:
            blockers.append(f"field_not_in_schema:{field}")
    for header in required_headers:
        if header.lower() not in header_names:
            blockers.append(f"missing_header:{header}")
    allowed_schema_versions = {str(value).strip() for value in _as_sequence(contract_policy.get("allowed_schema_versions")) if str(value).strip()}
    schema_version = str(queue_contract.get("schema_version") or "").strip()
    if allowed_schema_versions and schema_version not in allowed_schema_versions:
        blockers.append(f"schema_version_not_allowed:{schema_version or 'missing'}")
    if contract_policy.get("require_sample_message") and not isinstance(queue_contract.get("sample_message"), Mapping):
        blockers.append("missing_sample_message")
    if contract_policy.get("require_contract_receipt") and _blank(queue_contract.get("contract_receipt")):
        blockers.append("missing_contract_receipt")
    contract_hash = "queue-payload-contract:" + _digest(
        {
            "blockers": blockers,
            "queue_name": queue_name,
            "required_fields": required_fields,
            "required_headers": required_headers,
            "schema_ref": schema_ref,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return QueuePayloadContractPlanReceipt(
        ready=not blockers,
        queue_name=queue_name,
        schema_ref=schema_ref,
        required_fields=required_fields,
        required_headers=required_headers,
        blockers=tuple(blockers),
        contract_hash=contract_hash,
    )


def plan_queue_ack_policy(
    ack_spec: Mapping[str, Any],
    ack_policy: Mapping[str, Any],
) -> QueueAckPolicyPlanReceipt:
    """Plan queue ack/nack behavior with timeout, failure action, visibility extension, and receipt gates."""

    raw_queue_name = str(ack_spec.get("queue_name") or ack_spec.get("name") or "").strip()
    queue_name = normalize_field_name(raw_queue_name) if raw_queue_name else ""
    ack_mode = normalize_field_name(ack_spec.get("ack_mode") or "")
    nack_mode = normalize_field_name(ack_spec.get("nack_mode") or ack_spec.get("failure_action") or "")
    ack_timeout_seconds = int(ack_spec.get("ack_timeout_seconds") or 0)
    max_ack_timeout_seconds = int(ack_policy.get("max_ack_timeout_seconds") or 0)
    allowed_ack_modes = {normalize_field_name(value) for value in _as_sequence(ack_policy.get("allowed_ack_modes")) if not _blank(value)}
    allowed_nack_modes = {normalize_field_name(value) for value in _as_sequence(ack_policy.get("allowed_nack_modes")) if not _blank(value)}
    blockers: list[str] = []
    if not queue_name:
        blockers.append("missing_queue_name")
    if not ack_mode or ack_mode == "field":
        blockers.append("missing_ack_mode")
    elif allowed_ack_modes and ack_mode not in allowed_ack_modes:
        blockers.append(f"ack_mode_not_allowed:{ack_mode}")
    if not nack_mode or nack_mode == "field":
        blockers.append("missing_nack_mode")
    elif allowed_nack_modes and nack_mode not in allowed_nack_modes:
        blockers.append(f"nack_mode_not_allowed:{nack_mode}")
    if ack_timeout_seconds <= 0:
        blockers.append("missing_ack_timeout_seconds")
    elif max_ack_timeout_seconds and ack_timeout_seconds > max_ack_timeout_seconds:
        blockers.append("ack_timeout_exceeds_policy")
    if ack_policy.get("require_ack_after_success") and not ack_spec.get("ack_after_success"):
        blockers.append("missing_ack_after_success")
    if ack_policy.get("require_nack_on_failure") and not ack_spec.get("nack_on_failure"):
        blockers.append("missing_nack_on_failure")
    if ack_policy.get("require_visibility_extension") and _blank(ack_spec.get("visibility_extension")):
        blockers.append("missing_visibility_extension")
    if ack_policy.get("require_ack_receipt") and _blank(ack_spec.get("ack_receipt")):
        blockers.append("missing_ack_receipt")
    policy_hash = "queue-ack-policy:" + _digest(
        {
            "ack_mode": ack_mode,
            "ack_timeout_seconds": ack_timeout_seconds,
            "blockers": blockers,
            "nack_mode": nack_mode,
            "queue_name": queue_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return QueueAckPolicyPlanReceipt(
        ready=not blockers,
        queue_name=queue_name,
        ack_mode=ack_mode,
        nack_mode=nack_mode,
        blockers=tuple(blockers),
        policy_hash=policy_hash,
    )


def plan_queue_poison_message_policy(
    poison_spec: Mapping[str, Any],
    poison_policy: Mapping[str, Any],
) -> QueuePoisonMessagePolicyPlanReceipt:
    """Plan poison-message handling with threshold, quarantine, alerting, replay, and receipt gates."""

    raw_queue_name = str(poison_spec.get("queue_name") or poison_spec.get("name") or "").strip()
    queue_name = normalize_field_name(raw_queue_name) if raw_queue_name else ""
    poison_threshold = int(poison_spec.get("poison_threshold") or poison_spec.get("max_failures") or 0)
    max_poison_threshold = int(poison_policy.get("max_poison_threshold") or poison_policy.get("max_failures") or 0)
    quarantine_sink = str(poison_spec.get("quarantine_sink") or poison_spec.get("dead_letter_queue") or "").strip()
    blockers: list[str] = []
    if not queue_name:
        blockers.append("missing_queue_name")
    if poison_threshold <= 0:
        blockers.append("missing_poison_threshold")
    elif max_poison_threshold and poison_threshold > max_poison_threshold:
        blockers.append("poison_threshold_exceeds_policy")
    if poison_policy.get("require_quarantine_sink") and not quarantine_sink:
        blockers.append("missing_quarantine_sink")
    if poison_policy.get("require_classification_rules") and not _as_sequence(poison_spec.get("classification_rules")):
        blockers.append("missing_classification_rules")
    if poison_policy.get("require_alert_topic") and _blank(poison_spec.get("alert_topic")):
        blockers.append("missing_alert_topic")
    if poison_policy.get("require_replay_policy") and _blank(poison_spec.get("replay_policy")):
        blockers.append("missing_replay_policy")
    if poison_policy.get("require_poison_receipt") and _blank(poison_spec.get("poison_receipt")):
        blockers.append("missing_poison_receipt")
    poison_hash = "queue-poison-message-policy:" + _digest(
        {
            "blockers": blockers,
            "poison_threshold": poison_threshold,
            "queue_name": queue_name,
            "quarantine_sink": quarantine_sink,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return QueuePoisonMessagePolicyPlanReceipt(
        ready=not blockers,
        queue_name=queue_name,
        poison_threshold=poison_threshold,
        quarantine_sink=quarantine_sink,
        blockers=tuple(blockers),
        poison_hash=poison_hash,
    )


def plan_queue_batch_consumer(
    batch_spec: Mapping[str, Any],
    batch_policy: Mapping[str, Any],
) -> QueueBatchConsumerPlanReceipt:
    """Plan queue batch consumption with batch size, wait window, partial failure, and checkpoint gates."""

    raw_queue_name = str(batch_spec.get("queue_name") or batch_spec.get("name") or "").strip()
    queue_name = normalize_field_name(raw_queue_name) if raw_queue_name else ""
    batch_size = int(batch_spec.get("batch_size") or 0)
    max_batch_size = int(batch_policy.get("max_batch_size") or 0)
    max_wait_seconds = int(batch_spec.get("max_wait_seconds") or batch_spec.get("wait_seconds") or 0)
    policy_max_wait_seconds = int(batch_policy.get("max_wait_seconds") or 0)
    partial_failure_mode = normalize_field_name(batch_spec.get("partial_failure_mode") or "")
    allowed_partial_failure_modes = {normalize_field_name(value) for value in _as_sequence(batch_policy.get("allowed_partial_failure_modes")) if not _blank(value)}
    blockers: list[str] = []
    if not queue_name:
        blockers.append("missing_queue_name")
    if batch_size <= 0:
        blockers.append("missing_batch_size")
    elif max_batch_size and batch_size > max_batch_size:
        blockers.append("batch_size_exceeds_policy")
    if max_wait_seconds <= 0:
        blockers.append("missing_max_wait_seconds")
    elif policy_max_wait_seconds and max_wait_seconds > policy_max_wait_seconds:
        blockers.append("max_wait_exceeds_policy")
    if batch_policy.get("require_partial_failure_mode") and (not partial_failure_mode or partial_failure_mode == "field"):
        blockers.append("missing_partial_failure_mode")
    elif allowed_partial_failure_modes and partial_failure_mode not in allowed_partial_failure_modes:
        blockers.append(f"partial_failure_mode_not_allowed:{partial_failure_mode}")
    if batch_policy.get("require_per_item_receipt") and _blank(batch_spec.get("per_item_receipt")):
        blockers.append("missing_per_item_receipt")
    if batch_policy.get("require_batch_idempotency_key") and _blank(batch_spec.get("batch_idempotency_key")):
        blockers.append("missing_batch_idempotency_key")
    if batch_policy.get("require_checkpoint") and _blank(batch_spec.get("checkpoint")):
        blockers.append("missing_checkpoint")
    batch_hash = "queue-batch-consumer:" + _digest(
        {
            "batch_size": batch_size,
            "blockers": blockers,
            "max_wait_seconds": max_wait_seconds,
            "queue_name": queue_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return QueueBatchConsumerPlanReceipt(
        ready=not blockers,
        queue_name=queue_name,
        batch_size=batch_size,
        max_wait_seconds=max_wait_seconds,
        blockers=tuple(blockers),
        batch_hash=batch_hash,
    )


def plan_queue_ordering_policy(
    ordering_spec: Mapping[str, Any],
    ordering_policy: Mapping[str, Any],
) -> QueueOrderingPolicyPlanReceipt:
    """Plan queue ordering with ordering key, mode, partitioning, sequence checks, and gap handling."""

    raw_queue_name = str(ordering_spec.get("queue_name") or ordering_spec.get("name") or "").strip()
    queue_name = normalize_field_name(raw_queue_name) if raw_queue_name else ""
    ordering_key = normalize_field_name(ordering_spec.get("ordering_key") or "") if not _blank(ordering_spec.get("ordering_key")) else ""
    ordering_mode = normalize_field_name(ordering_spec.get("ordering_mode") or ordering_spec.get("mode") or "")
    allowed_ordering_modes = {normalize_field_name(value) for value in _as_sequence(ordering_policy.get("allowed_ordering_modes")) if not _blank(value)}
    blockers: list[str] = []
    if not queue_name:
        blockers.append("missing_queue_name")
    if not ordering_key:
        blockers.append("missing_ordering_key")
    if not ordering_mode or ordering_mode == "field":
        blockers.append("missing_ordering_mode")
    elif allowed_ordering_modes and ordering_mode not in allowed_ordering_modes:
        blockers.append(f"ordering_mode_not_allowed:{ordering_mode}")
    if ordering_policy.get("require_partition_key") and _blank(ordering_spec.get("partition_key")):
        blockers.append("missing_partition_key")
    if ordering_policy.get("require_sequence_check") and _blank(ordering_spec.get("sequence_check")):
        blockers.append("missing_sequence_check")
    if ordering_policy.get("require_gap_handling") and _blank(ordering_spec.get("gap_handling")):
        blockers.append("missing_gap_handling")
    if ordering_policy.get("require_reorder_dlq") and _blank(ordering_spec.get("reorder_dlq")):
        blockers.append("missing_reorder_dlq")
    if ordering_policy.get("require_ordering_receipt") and _blank(ordering_spec.get("ordering_receipt")):
        blockers.append("missing_ordering_receipt")
    ordering_hash = "queue-ordering-policy:" + _digest(
        {
            "blockers": blockers,
            "ordering_key": ordering_key,
            "ordering_mode": ordering_mode,
            "queue_name": queue_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return QueueOrderingPolicyPlanReceipt(
        ready=not blockers,
        queue_name=queue_name,
        ordering_key=ordering_key,
        ordering_mode=ordering_mode,
        blockers=tuple(blockers),
        ordering_hash=ordering_hash,
    )


def evaluate_scheduled_job_tick(
    schedule_tick: Mapping[str, Any],
    job_policy: Mapping[str, Any],
) -> ScheduledJobReceipt:
    """Evaluate whether a cron/scheduled job should run for one tick."""

    job_name = str(job_policy.get("job_name") or schedule_tick.get("job_name") or "scheduled-job").strip()
    tick_date = str(schedule_tick.get("date") or "").strip()
    tick_hour = int(schedule_tick.get("hour") or 0)
    tick_minute = int(schedule_tick.get("minute") or 0)
    weekday = str(schedule_tick.get("weekday") or "").strip().lower()
    allowed_hours = {int(value) for value in _as_sequence(job_policy.get("allowed_hours")) if str(value).strip()}
    allowed_weekdays = {str(value).lower() for value in _as_sequence(job_policy.get("allowed_weekdays")) if str(value).strip()}
    observed_runs = {str(value) for value in _as_sequence(job_policy.get("observed_run_keys"))}
    max_runs_per_day = int(job_policy.get("max_runs_per_day") or 1)

    skipped_reason = ""
    run_key = f"{job_name}:{tick_date}:{tick_hour:02d}{tick_minute:02d}"
    daily_prefix = f"{job_name}:{tick_date}:"
    daily_runs = sum(1 for value in observed_runs if value.startswith(daily_prefix))
    if allowed_hours and tick_hour not in allowed_hours:
        skipped_reason = "hour_not_allowed"
    elif allowed_weekdays and weekday not in allowed_weekdays:
        skipped_reason = "weekday_not_allowed"
    elif run_key in observed_runs:
        skipped_reason = "already_ran"
    elif daily_runs >= max_runs_per_day:
        skipped_reason = "daily_run_limit_reached"
    elif not tick_date:
        skipped_reason = "missing_tick_date"

    proof_requirements = (
        "schedule_fixture_test",
        "idempotent_lock_test",
        "missed_run_policy_test",
        "candidate_boundary_gate",
    )
    lock_key = "cron-lock:" + _digest({"job_name": job_name, "run_key": run_key}, chars=RECEIPT_DIGEST_CHARS)
    receipt_hash = "scheduled-job:" + _digest(
        {"lock_key": lock_key, "run_key": run_key, "skipped_reason": skipped_reason},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ScheduledJobReceipt(
        should_run=not skipped_reason,
        job_name=job_name,
        run_key=run_key,
        lock_key=lock_key,
        skipped_reason=skipped_reason,
        proof_requirements=proof_requirements,
        receipt_hash=receipt_hash,
    )


def compile_cli_command_request(
    command_args: Mapping[str, Any],
    command_policy: Mapping[str, Any],
) -> CliCommandReceipt:
    """Compile a CLI invocation as argv plus deterministic policy blockers."""

    command = str(command_policy.get("command") or command_args.get("command") or "").strip()
    raw_flags = command_args.get("flags") if isinstance(command_args.get("flags"), Mapping) else {}
    positional = tuple(str(value) for value in _as_sequence(command_args.get("positional")) if str(value).strip())
    blockers: list[str] = []
    if not command:
        blockers.append("missing_command")
    allowed_commands = {str(value) for value in _as_sequence(command_policy.get("allowed_commands")) if str(value).strip()}
    if allowed_commands and command not in allowed_commands:
        blockers.append("command_not_allowed")

    normalized_flags: JsonRecord = {}
    allowed_flags = {str(value) for value in _as_sequence(command_policy.get("allowed_flags")) if str(value).strip()}
    for key, value in raw_flags.items():
        flag = str(key).strip().lstrip("-")
        if allowed_flags and flag not in allowed_flags:
            blockers.append(f"flag_not_allowed:{flag}")
            continue
        normalized_flags[flag] = value

    for required_flag in _as_sequence(command_policy.get("required_flags")):
        flag = str(required_flag).strip().lstrip("-")
        if flag and _blank(normalized_flags.get(flag)):
            blockers.append(f"missing_required_flag:{flag}")

    argv: list[str] = [command] if command else []
    for flag in sorted(normalized_flags):
        value = normalized_flags[flag]
        argv.append(f"--{flag}")
        if value is not True:
            argv.append(str(value))
    argv.extend(positional)
    receipt_hash = "cli-command:" + _digest(
        {"argv": argv, "blockers": blockers, "normalized_flags": normalized_flags},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return CliCommandReceipt(
        executable=not blockers,
        command_argv=tuple(argv),
        normalized_flags=normalized_flags,
        blockers=tuple(blockers),
        receipt_hash=receipt_hash,
    )


def plan_kubernetes_job(
    job_spec: Mapping[str, Any],
    runtime_policy: Mapping[str, Any],
) -> KubernetesJobPlanReceipt:
    """Plan a Kubernetes Job manifest with safety and readiness blockers."""

    job_name = str(job_spec.get("name") or job_spec.get("job_name") or "").strip()
    containers = [item for item in _as_mapping_sequence(job_spec.get("containers"))]
    blockers: list[str] = []
    if not job_name:
        blockers.append("missing_job_name")
    if not containers:
        blockers.append("missing_containers")
    require_limits = bool(runtime_policy.get("require_resource_limits", True))
    forbid_latest = bool(runtime_policy.get("forbid_latest_tag", True))
    for index, container in enumerate(containers):
        image = str(container.get("image") or "").strip()
        resources = container.get("resources") if isinstance(container.get("resources"), Mapping) else {}
        limits = resources.get("limits") if isinstance(resources.get("limits"), Mapping) else {}
        if not image:
            blockers.append(f"container_{index + 1}_missing_image")
        if forbid_latest and (image.endswith(":latest") or ":" not in image):
            blockers.append(f"container_{index + 1}_mutable_image_tag")
        if require_limits and not limits:
            blockers.append(f"container_{index + 1}_missing_resource_limits")

    restart_policy = str(job_spec.get("restart_policy") or job_spec.get("restartPolicy") or "Never")
    if restart_policy != "Never":
        blockers.append("restart_policy_must_be_never")
    service_account = str(job_spec.get("service_account") or job_spec.get("serviceAccountName") or "").strip()
    if runtime_policy.get("require_service_account") and not service_account:
        blockers.append("missing_service_account")

    manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {"name": job_name},
        "spec": {
            "backoffLimit": int(job_spec.get("backoff_limit") or job_spec.get("backoffLimit") or runtime_policy.get("default_backoff_limit") or 1),
            "template": {
                "spec": {
                    "containers": [dict(container) for container in containers],
                    "restartPolicy": restart_policy,
                },
            },
        },
    }
    if service_account:
        manifest["spec"]["template"]["spec"]["serviceAccountName"] = service_account
    if job_spec.get("ttl_seconds_after_finished") or runtime_policy.get("ttl_seconds_after_finished"):
        manifest["spec"]["ttlSecondsAfterFinished"] = int(
            job_spec.get("ttl_seconds_after_finished") or runtime_policy.get("ttl_seconds_after_finished")
        )
    manifest_hash = "k8s-job:" + _digest(
        {"blockers": blockers, "manifest": manifest},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return KubernetesJobPlanReceipt(
        ready=not blockers,
        job_name=job_name,
        blockers=tuple(blockers),
        manifest=manifest,
        manifest_hash=manifest_hash,
        proof_requirements=("manifest_schema_test", "image_policy_test", "resource_limit_test", "candidate_boundary_gate"),
    )


def build_dashboard_metric_snapshot(
    metric_sources: Sequence[Mapping[str, Any]],
    dashboard_policy: Mapping[str, Any],
) -> DashboardSnapshotReceipt:
    """Build a deterministic dashboard/report snapshot from metric sources."""

    max_age_seconds = int(dashboard_policy.get("max_age_seconds") or 3600)
    current_epoch = int(dashboard_policy.get("current_epoch") or 0)
    required_metrics = tuple(str(metric) for metric in _as_sequence(dashboard_policy.get("required_metrics")) if str(metric).strip())
    latest_by_metric: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(metric_sources):
        metric = str(row.get("metric") or row.get("name") or "").strip()
        if not metric:
            continue
        previous = latest_by_metric.get(metric)
        row_epoch = int(row.get("epoch") or 0)
        previous_epoch = int(previous.get("epoch") or 0) if previous else -1
        if previous is None or row_epoch >= previous_epoch:
            latest_by_metric[metric] = {**row, "source_id": row.get("source_id") or f"source-{index + 1}"}

    tiles: list[DashboardTile] = []
    stale_metrics: list[str] = []
    for metric in sorted(latest_by_metric):
        row = latest_by_metric[metric]
        epoch = int(row.get("epoch") or 0)
        stale = bool(current_epoch and epoch and current_epoch - epoch > max_age_seconds)
        status = "stale" if stale else "ok"
        if stale:
            stale_metrics.append(metric)
        tiles.append(DashboardTile(
            metric=metric,
            value=row.get("value"),
            status=status,
            source_id=str(row.get("source_id") or ""),
        ))

    missing_metrics = tuple(metric for metric in required_metrics if metric not in latest_by_metric)
    snapshot_hash = "dashboard:" + _digest(
        {
            "missing_metrics": missing_metrics,
            "stale_metrics": stale_metrics,
            "tiles": [asdict(tile) for tile in tiles],
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DashboardSnapshotReceipt(
        tiles=tuple(tiles),
        missing_metrics=missing_metrics,
        stale_metrics=tuple(stale_metrics),
        ready=not missing_metrics and not stale_metrics,
        snapshot_hash=snapshot_hash,
    )


def evaluate_auth_middleware_request(
    request_context: Mapping[str, Any],
    credentials: Mapping[str, Any],
    auth_policy: Mapping[str, Any],
) -> AuthMiddlewareReceipt:
    """Evaluate an auth middleware boundary without performing side effects."""

    subject_id = str(credentials.get("subject_id") or credentials.get("sub") or "").strip()
    token = str(credentials.get("token") or "").strip()
    scopes = tuple(sorted({str(scope) for scope in _as_sequence(credentials.get("scopes")) if str(scope).strip()}))
    required_scopes = {str(scope) for scope in _as_sequence(auth_policy.get("required_scopes")) if str(scope).strip()}
    allowed_subjects = {str(value) for value in _as_sequence(auth_policy.get("allowed_subjects")) if str(value).strip()}
    missing_scopes = tuple(sorted(required_scopes - set(scopes)))
    blockers: list[str] = []
    if bool(auth_policy.get("require_token", True)) and not token:
        blockers.append("missing_token")
    if not subject_id:
        blockers.append("missing_subject")
    if allowed_subjects and subject_id not in allowed_subjects:
        blockers.append("subject_not_allowed")
    blockers.extend(f"missing_scope:{scope}" for scope in missing_scopes)
    status = "authorized" if not blockers else "forbidden"
    authorized_request = {
        "request_id": request_context.get("request_id"),
        "path": request_context.get("path"),
        "method": request_context.get("method"),
        "subject_id": subject_id,
        "scopes": scopes,
    } if not blockers else {}
    receipt_hash = "auth-middleware:" + _digest(
        {
            "authorized_request": authorized_request,
            "blockers": blockers,
            "subject_id": subject_id,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return AuthMiddlewareReceipt(
        authorized=not blockers,
        status=status,
        subject_id=subject_id,
        scopes=scopes,
        missing_scopes=missing_scopes,
        authorized_request=authorized_request,
        receipt_hash=receipt_hash,
    )


def evaluate_rate_limit_request(
    request_context: Mapping[str, Any],
    usage_window: Mapping[str, Any],
    quota_policy: Mapping[str, Any],
) -> RateLimitDecisionReceipt:
    """Evaluate one rate-limit decision from a usage window and quota policy."""

    subject_id = str(request_context.get("subject_id") or request_context.get("ip") or "anonymous").strip()
    limit = int(quota_policy.get("limit") or quota_policy.get("max_requests") or 0)
    used = int(usage_window.get("used") or usage_window.get("count") or 0)
    reset_epoch = int(usage_window.get("reset_epoch") or quota_policy.get("reset_epoch") or 0)
    if limit <= 0:
        allowed = False
        reason = "quota_limit_not_declared"
        remaining = 0
    elif used >= limit:
        allowed = False
        reason = "quota_exhausted"
        remaining = 0
    else:
        allowed = True
        reason = "allowed"
        remaining = limit - used - 1
    receipt_hash = "rate-limit:" + _digest(
        {
            "allowed": allowed,
            "limit": limit,
            "reason": reason,
            "remaining": remaining,
            "subject_id": subject_id,
            "used": used,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return RateLimitDecisionReceipt(
        allowed=allowed,
        subject_id=subject_id,
        limit=limit,
        used=used,
        remaining=remaining,
        reset_epoch=reset_epoch,
        reason=reason,
        receipt_hash=receipt_hash,
    )


def plan_tool_invocation(
    tool_input: Mapping[str, Any],
    tool_policy: Mapping[str, Any],
) -> ToolInvocationPlanReceipt:
    """Plan an agent tool call with argument, scope, and allow-list gates."""

    tool_name = str(tool_input.get("tool_name") or tool_input.get("name") or "").strip()
    args = tool_input.get("args") if isinstance(tool_input.get("args"), Mapping) else {}
    blockers: list[str] = []
    allowed_tools = {str(value) for value in _as_sequence(tool_policy.get("allowed_tools")) if str(value).strip()}
    if not tool_name:
        blockers.append("missing_tool_name")
    elif allowed_tools and tool_name not in allowed_tools:
        blockers.append("tool_not_allowed")

    normalized_args: JsonRecord = {}
    forbidden_args = {str(value) for value in _as_sequence(tool_policy.get("forbidden_args")) if str(value).strip()}
    for key, value in args.items():
        arg_name = str(key)
        if arg_name in forbidden_args:
            blockers.append(f"forbidden_arg:{arg_name}")
            continue
        normalized_args[arg_name] = value
    for required_arg in _as_sequence(tool_policy.get("required_args")):
        arg_name = str(required_arg)
        if arg_name and _blank(normalized_args.get(arg_name)):
            blockers.append(f"missing_arg:{arg_name}")

    max_arg_chars = int(tool_policy.get("max_arg_chars") or 0)
    if max_arg_chars > 0 and len(_stable_json(normalized_args)) > max_arg_chars:
        blockers.append("args_too_large")
    required_scopes = {str(value) for value in _as_sequence(tool_policy.get("required_scopes")) if str(value).strip()}
    actor_scopes = {str(value) for value in _as_sequence(tool_input.get("actor_scopes")) if str(value).strip()}
    for scope in sorted(required_scopes - actor_scopes):
        blockers.append(f"missing_scope:{scope}")

    audit_key = "tool-call:" + _digest(
        {"args": normalized_args, "tool_name": tool_name},
        chars=RECEIPT_DIGEST_CHARS,
    )
    receipt_hash = "tool-plan:" + _digest(
        {"audit_key": audit_key, "blockers": blockers, "tool_name": tool_name},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ToolInvocationPlanReceipt(
        allowed=not blockers,
        tool_name=tool_name,
        normalized_args=normalized_args,
        blockers=tuple(blockers),
        audit_key=audit_key,
        receipt_hash=receipt_hash,
    )


def evaluate_workflow_step_transition(
    workflow_state: Mapping[str, Any],
    step_input: Mapping[str, Any],
    workflow_policy: Mapping[str, Any],
) -> WorkflowStepReceipt:
    """Evaluate one deterministic workflow transition and emitted events."""

    current_step = str(workflow_state.get("current_step") or "").strip()
    action = str(step_input.get("action") or workflow_policy.get("default_action") or "").strip()
    transition_key = f"{current_step}:{action}"
    transitions = workflow_policy.get("transitions") if isinstance(workflow_policy.get("transitions"), Mapping) else {}
    current_transitions = transitions.get(current_step) if isinstance(transitions.get(current_step), Mapping) else {}
    next_step = str(current_transitions.get(action) or "").strip()
    blockers: list[str] = []
    if not current_step:
        blockers.append("missing_current_step")
    if not action:
        blockers.append("missing_action")
    if not next_step:
        blockers.append("transition_not_allowed")
    for field in _as_sequence(workflow_policy.get("required_input_fields")):
        field_name = str(field)
        if field_name and _blank(step_input.get(field_name)):
            blockers.append(f"missing_input_field:{field_name}")
    seen_transition_keys = {str(value) for value in _as_sequence(workflow_state.get("completed_transition_keys"))}
    if transition_key in seen_transition_keys:
        blockers.append("duplicate_transition")

    emitted_events = ()
    if not blockers:
        emitted_events = ({
            "event_type": f"workflow.{normalize_field_name(next_step)}",
            "from_step": current_step,
            "to_step": next_step,
            "action": action,
        },)
    status = "transitioned" if not blockers else "blocked"
    receipt_hash = "workflow-step:" + _digest(
        {
            "blockers": blockers,
            "current_step": current_step,
            "events": emitted_events,
            "next_step": next_step,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return WorkflowStepReceipt(
        transitioned=not blockers,
        current_step=current_step,
        next_step=next_step,
        status=status,
        emitted_events=emitted_events,
        blockers=tuple(blockers),
        receipt_hash=receipt_hash,
    )


def plan_event_publication(
    domain_event: Mapping[str, Any],
    publish_policy: Mapping[str, Any],
) -> PublishedEventReceipt:
    """Plan a queue/event publication with topic and idempotency checks."""

    event_type = str(domain_event.get("event_type") or domain_event.get("type") or "").strip()
    topic = str(publish_policy.get("topic") or domain_event.get("topic") or "").strip()
    payload = domain_event.get("payload") if isinstance(domain_event.get("payload"), Mapping) else {}
    partition_field = str(publish_policy.get("partition_field") or "id").strip()
    partition_key = str(domain_event.get(partition_field) or payload.get(partition_field) or "").strip()
    blockers: list[str] = []
    allowed_event_types = {str(value) for value in _as_sequence(publish_policy.get("allowed_event_types")) if str(value).strip()}
    if not topic:
        blockers.append("missing_topic")
    if not event_type:
        blockers.append("missing_event_type")
    elif allowed_event_types and event_type not in allowed_event_types:
        blockers.append("event_type_not_allowed")
    if not partition_key:
        blockers.append("missing_partition_key")
    for field in _as_sequence(publish_policy.get("required_payload_fields")):
        field_name = str(field)
        if field_name and _blank(payload.get(field_name)):
            blockers.append(f"missing_payload_field:{field_name}")
    idempotency_key = "publish-event:" + _digest(
        {"event_type": event_type, "partition_key": partition_key, "payload": dict(payload), "topic": topic},
        chars=RECEIPT_DIGEST_CHARS,
    )
    receipt_hash = "publish-event:" + _digest(
        {"blockers": blockers, "idempotency_key": idempotency_key},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PublishedEventReceipt(
        publishable=not blockers,
        topic=topic,
        event_type=event_type,
        partition_key=partition_key,
        payload=dict(payload),
        blockers=tuple(blockers),
        idempotency_key=idempotency_key,
        receipt_hash=receipt_hash,
    )


def evaluate_domain_event_handler(
    domain_event: Mapping[str, Any],
    handler_policy: Mapping[str, Any],
) -> EventHandlerReceipt:
    """Evaluate a domain event handler and emitted command plan."""

    event_type = str(domain_event.get("event_type") or domain_event.get("type") or "").strip()
    handler_name = str(handler_policy.get("handler_name") or f"handle_{normalize_field_name(event_type)}").strip()
    payload = domain_event.get("payload") if isinstance(domain_event.get("payload"), Mapping) else {}
    blockers: list[str] = []
    accepted_events = {str(value) for value in _as_sequence(handler_policy.get("accepted_event_types")) if str(value).strip()}
    if not event_type:
        blockers.append("missing_event_type")
    elif accepted_events and event_type not in accepted_events:
        blockers.append("event_type_not_accepted")
    seen_event_ids = {str(value) for value in _as_sequence(handler_policy.get("handled_event_ids"))}
    event_id = str(domain_event.get("event_id") or payload.get("id") or "").strip()
    if not event_id:
        blockers.append("missing_event_id")
    elif event_id in seen_event_ids:
        blockers.append("duplicate_event")
    for field in _as_sequence(handler_policy.get("required_payload_fields")):
        field_name = str(field)
        if field_name and _blank(payload.get(field_name)):
            blockers.append(f"missing_payload_field:{field_name}")
    command_templates = [
        item for item in _as_mapping_sequence(handler_policy.get("command_templates"))
    ]
    emitted_commands: list[JsonRecord] = []
    if not blockers:
        for index, template in enumerate(command_templates):
            args: JsonRecord = {}
            field_map = template.get("field_map") if isinstance(template.get("field_map"), Mapping) else {}
            for source_field, target_field in field_map.items():
                args[str(target_field)] = payload.get(source_field)
            emitted_commands.append({
                "command_type": str(template.get("command_type") or f"command-{index + 1}"),
                "args": args,
            })
    idempotency_key = "event-handler:" + _digest(
        {"event_id": event_id, "handler_name": handler_name},
        chars=RECEIPT_DIGEST_CHARS,
    )
    receipt_hash = "event-handler:" + _digest(
        {"blockers": blockers, "commands": emitted_commands, "idempotency_key": idempotency_key},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return EventHandlerReceipt(
        handled=not blockers,
        event_type=event_type,
        handler_name=handler_name,
        emitted_commands=tuple(emitted_commands),
        blockers=tuple(blockers),
        idempotency_key=idempotency_key,
        receipt_hash=receipt_hash,
    )


def plan_sdk_client_request(
    request_envelope: Mapping[str, Any],
    client_policy: Mapping[str, Any],
) -> SdkRequestPlanReceipt:
    """Plan a typed SDK/API client request without making the network call."""

    method = str(request_envelope.get("method") or client_policy.get("default_method") or "GET").upper()
    path = str(request_envelope.get("path") or "").strip()
    body = request_envelope.get("body") if isinstance(request_envelope.get("body"), Mapping) else {}
    headers = dict(client_policy.get("default_headers") if isinstance(client_policy.get("default_headers"), Mapping) else {})
    headers.update(request_envelope.get("headers") if isinstance(request_envelope.get("headers"), Mapping) else {})
    blockers: list[str] = []
    allowed_methods = {str(value).upper() for value in _as_sequence(client_policy.get("allowed_methods")) if str(value).strip()}
    if allowed_methods and method not in allowed_methods:
        blockers.append("method_not_allowed")
    allowed_path_prefixes = tuple(str(value) for value in _as_sequence(client_policy.get("allowed_path_prefixes")) if str(value).strip())
    if not path:
        blockers.append("missing_path")
    elif allowed_path_prefixes and not any(path.startswith(prefix) for prefix in allowed_path_prefixes):
        blockers.append("path_not_allowed")
    for field in _as_sequence(client_policy.get("required_body_fields")):
        field_name = str(field)
        if field_name and _blank(body.get(field_name)):
            blockers.append(f"missing_body_field:{field_name}")
    if client_policy.get("require_idempotency_key") and _blank(headers.get("Idempotency-Key")):
        headers["Idempotency-Key"] = "sdk:" + _digest({"body": dict(body), "method": method, "path": path}, chars=RECEIPT_DIGEST_CHARS)
    retry_policy = dict(client_policy.get("retry_policy") if isinstance(client_policy.get("retry_policy"), Mapping) else {"max_attempts": 3})
    receipt_hash = "sdk-request:" + _digest(
        {"blockers": blockers, "body": dict(body), "headers": headers, "method": method, "path": path},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SdkRequestPlanReceipt(
        ready=not blockers,
        method=method,
        path=path,
        request_body=dict(body),
        headers=headers,
        retry_policy=retry_policy,
        blockers=tuple(blockers),
        receipt_hash=receipt_hash,
    )


def plan_terraform_module(
    module_spec: Mapping[str, Any],
    infra_policy: Mapping[str, Any],
) -> TerraformModulePlanReceipt:
    """Plan a Terraform module with required variables and resource policies."""

    module_name = str(module_spec.get("module_name") or module_spec.get("name") or "").strip()
    variables = dict(module_spec.get("variables") if isinstance(module_spec.get("variables"), Mapping) else {})
    resources = [dict(item) for item in _as_mapping_sequence(module_spec.get("resources"))]
    blockers: list[str] = []
    if not module_name:
        blockers.append("missing_module_name")
    for var in _as_sequence(infra_policy.get("required_variables")):
        name = str(var)
        if name and _blank(variables.get(name)):
            blockers.append(f"missing_variable:{name}")
    allowed_resource_types = {str(value) for value in _as_sequence(infra_policy.get("allowed_resource_types")) if str(value).strip()}
    for index, resource in enumerate(resources):
        resource_type = str(resource.get("type") or "").strip()
        if not resource_type:
            blockers.append(f"resource_{index + 1}_missing_type")
        elif allowed_resource_types and resource_type not in allowed_resource_types:
            blockers.append(f"resource_type_not_allowed:{resource_type}")
        if infra_policy.get("require_tags"):
            tags = resource.get("tags") if isinstance(resource.get("tags"), Mapping) else {}
            if not tags:
                blockers.append(f"resource_{index + 1}_missing_tags")
    if not resources:
        blockers.append("missing_resources")
    plan_hash = "terraform-module:" + _digest(
        {"blockers": blockers, "module_name": module_name, "resources": resources, "variables": variables},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return TerraformModulePlanReceipt(
        ready=not blockers,
        module_name=module_name,
        resources=tuple(resources),
        variables=variables,
        blockers=tuple(blockers),
        plan_hash=plan_hash,
    )


def plan_github_action_workflow(
    workflow_spec: Mapping[str, Any],
    workflow_policy: Mapping[str, Any],
) -> GithubActionWorkflowReceipt:
    """Plan a GitHub Actions workflow with trigger, job, and permission checks."""

    workflow_name = str(workflow_spec.get("name") or workflow_spec.get("workflow_name") or "").strip()
    triggers = tuple(str(value) for value in _as_sequence(workflow_spec.get("triggers") or workflow_spec.get("on")) if str(value).strip())
    jobs = tuple(dict(item) for item in _as_mapping_sequence(workflow_spec.get("jobs")))
    blockers: list[str] = []
    if not workflow_name:
        blockers.append("missing_workflow_name")
    allowed_triggers = {str(value) for value in _as_sequence(workflow_policy.get("allowed_triggers")) if str(value).strip()}
    if not triggers:
        blockers.append("missing_triggers")
    for trigger in triggers:
        if allowed_triggers and trigger not in allowed_triggers:
            blockers.append(f"trigger_not_allowed:{trigger}")
    if not jobs:
        blockers.append("missing_jobs")
    for index, job in enumerate(jobs):
        if _blank(job.get("runs_on") or job.get("runs-on")):
            blockers.append(f"job_{index + 1}_missing_runner")
        permissions = job.get("permissions") if isinstance(job.get("permissions"), Mapping) else {}
        if workflow_policy.get("require_permissions") and not permissions:
            blockers.append(f"job_{index + 1}_missing_permissions")
        if workflow_policy.get("forbid_unpinned_actions"):
            for step_index, step in enumerate(_as_mapping_sequence(job.get("steps"))):
                uses = str(step.get("uses") or "")
                if uses and "@" not in uses:
                    blockers.append(f"job_{index + 1}_step_{step_index + 1}_unpinned_action")
    workflow_hash = "github-action:" + _digest(
        {"blockers": blockers, "jobs": jobs, "triggers": triggers, "workflow_name": workflow_name},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return GithubActionWorkflowReceipt(
        ready=not blockers,
        workflow_name=workflow_name,
        triggers=triggers,
        jobs=jobs,
        blockers=tuple(blockers),
        workflow_hash=workflow_hash,
    )


def evaluate_data_quality_rule(
    dataset: Sequence[Mapping[str, Any]],
    quality_rule: Mapping[str, Any],
) -> DataQualityRuleReceipt:
    """Evaluate a deterministic data-quality rule over records."""

    rule_name = str(quality_rule.get("rule_name") or quality_rule.get("name") or "data_quality_rule")
    required_fields = tuple(str(value) for value in _as_sequence(quality_rule.get("required_fields")) if str(value).strip())
    unique_fields = tuple(str(value) for value in _as_sequence(quality_rule.get("unique_fields")) if str(value).strip())
    failed_rows: list[int] = []
    seen_keys: set[tuple[str, ...]] = set()
    failure_reason = ""
    for index, row in enumerate(dataset):
        missing = [field for field in required_fields if _blank(row.get(field))]
        if missing:
            failed_rows.append(index)
            failure_reason = "missing_required_fields"
            continue
        if unique_fields:
            key = tuple(str(row.get(field) or "") for field in unique_fields)
            if key in seen_keys:
                failed_rows.append(index)
                failure_reason = "duplicate_key"
                continue
            seen_keys.add(key)
    receipt_hash = "data-quality:" + _digest(
        {"failed_rows": failed_rows, "rule_name": rule_name, "total_rows": len(dataset)},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DataQualityRuleReceipt(
        passed=not failed_rows,
        total_rows=len(dataset),
        failed_rows=tuple(failed_rows),
        rule_name=rule_name,
        failure_reason=failure_reason,
        receipt_hash=receipt_hash,
    )


def plan_vector_index_build(
    documents: Sequence[Mapping[str, Any]],
    index_policy: Mapping[str, Any],
) -> VectorIndexPlanReceipt:
    """Plan a vector index build with chunking and embedding-dimension checks."""

    embedding_model = str(index_policy.get("embedding_model") or "").strip()
    dimension = int(index_policy.get("dimension") or 0)
    chunk_chars = int(index_policy.get("chunk_chars") or 800)
    min_dimension = int(index_policy.get("min_dimension") or 1)
    blockers: list[str] = []
    if not embedding_model:
        blockers.append("missing_embedding_model")
    if dimension < min_dimension:
        blockers.append("embedding_dimension_too_small")
    chunk_count = 0
    for index, document in enumerate(documents):
        text = str(document.get("text") or document.get("content") or "")
        if not text.strip():
            blockers.append(f"document_{index + 1}_missing_text")
            continue
        chunk_count += max(1, (len(text) + chunk_chars - 1) // chunk_chars)
    if not documents:
        blockers.append("missing_documents")
    index_hash = "vector-index:" + _digest(
        {
            "blockers": blockers,
            "chunk_count": chunk_count,
            "dimension": dimension,
            "document_count": len(documents),
            "embedding_model": embedding_model,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return VectorIndexPlanReceipt(
        ready=not blockers,
        document_count=len(documents),
        chunk_count=chunk_count,
        embedding_model=embedding_model,
        dimension=dimension,
        blockers=tuple(blockers),
        index_hash=index_hash,
    )


def compile_compliance_evidence_workflow(
    control_context: Mapping[str, Any],
    evidence_policy: Mapping[str, Any],
) -> ComplianceEvidenceReceipt:
    """Compile a security/compliance evidence workflow receipt."""

    control_id = str(control_context.get("control_id") or evidence_policy.get("control_id") or "").strip()
    evidence = [item for item in _as_mapping_sequence(control_context.get("evidence"))]
    evidence_by_type = {
        str(item.get("type") or item.get("evidence_type") or ""): item
        for item in evidence
    }
    required_types = tuple(str(value) for value in _as_sequence(evidence_policy.get("required_evidence_types")) if str(value).strip())
    missing_evidence = tuple(value for value in required_types if value not in evidence_by_type)
    evidence_refs = tuple(
        str(item.get("ref") or item.get("path") or item.get("url") or item.get("id") or "")
        for item in evidence
        if str(item.get("ref") or item.get("path") or item.get("url") or item.get("id") or "").strip()
    )
    review_required = bool(evidence_policy.get("review_required", True))
    receipt_hash = "compliance-evidence:" + _digest(
        {
            "control_id": control_id,
            "evidence_refs": evidence_refs,
            "missing_evidence": missing_evidence,
            "review_required": review_required,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ComplianceEvidenceReceipt(
        ready=bool(control_id) and not missing_evidence,
        control_id=control_id,
        evidence_refs=evidence_refs,
        missing_evidence=missing_evidence,
        review_required=review_required,
        receipt_hash=receipt_hash,
    )


def plan_graphql_resolver(
    operation: Mapping[str, Any],
    resolver_policy: Mapping[str, Any],
) -> GraphqlResolverReceipt:
    """Plan a GraphQL resolver call with field and scope checks."""

    operation_name = str(operation.get("operation_name") or operation.get("name") or "").strip()
    resolver_name = str(resolver_policy.get("resolver_name") or operation_name or "").strip()
    selected_fields = tuple(str(field) for field in _as_sequence(operation.get("selected_fields")) if str(field).strip())
    blockers: list[str] = []
    allowed_operations = {str(value) for value in _as_sequence(resolver_policy.get("allowed_operations")) if str(value).strip()}
    allowed_fields = {str(value) for value in _as_sequence(resolver_policy.get("allowed_fields")) if str(value).strip()}
    required_scopes = {str(value) for value in _as_sequence(resolver_policy.get("required_scopes")) if str(value).strip()}
    actor_scopes = {str(value) for value in _as_sequence(operation.get("actor_scopes")) if str(value).strip()}
    if not operation_name:
        blockers.append("missing_operation_name")
    elif allowed_operations and operation_name not in allowed_operations:
        blockers.append("operation_not_allowed")
    if not selected_fields:
        blockers.append("missing_selected_fields")
    for field in selected_fields:
        if allowed_fields and field not in allowed_fields:
            blockers.append(f"field_not_allowed:{field}")
    for scope in sorted(required_scopes - actor_scopes):
        blockers.append(f"missing_scope:{scope}")
    receipt_hash = "graphql-resolver:" + _digest(
        {
            "blockers": blockers,
            "operation_name": operation_name,
            "resolver_name": resolver_name,
            "selected_fields": selected_fields,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return GraphqlResolverReceipt(
        ready=not blockers,
        operation_name=operation_name,
        resolver_name=resolver_name,
        selected_fields=selected_fields,
        blockers=tuple(blockers),
        receipt_hash=receipt_hash,
    )


def plan_grpc_method_call(
    request_envelope: Mapping[str, Any],
    method_policy: Mapping[str, Any],
) -> GrpcMethodReceipt:
    """Plan a gRPC method call with metadata and message checks."""

    service = str(request_envelope.get("service") or method_policy.get("service") or "").strip()
    method = str(request_envelope.get("method") or "").strip()
    request_message = dict(request_envelope.get("message") if isinstance(request_envelope.get("message"), Mapping) else {})
    metadata = dict(request_envelope.get("metadata") if isinstance(request_envelope.get("metadata"), Mapping) else {})
    blockers: list[str] = []
    allowed_methods = {str(value) for value in _as_sequence(method_policy.get("allowed_methods")) if str(value).strip()}
    if not service:
        blockers.append("missing_service")
    if not method:
        blockers.append("missing_method")
    elif allowed_methods and method not in allowed_methods:
        blockers.append("method_not_allowed")
    for field in _as_sequence(method_policy.get("required_message_fields")):
        field_name = str(field)
        if field_name and _blank(request_message.get(field_name)):
            blockers.append(f"missing_message_field:{field_name}")
    for header in _as_sequence(method_policy.get("required_metadata")):
        header_name = str(header)
        if header_name and _blank(metadata.get(header_name)):
            blockers.append(f"missing_metadata:{header_name}")
    receipt_hash = "grpc-method:" + _digest(
        {"blockers": blockers, "message": request_message, "metadata": metadata, "method": method, "service": service},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return GrpcMethodReceipt(
        ready=not blockers,
        service=service,
        method=method,
        request_message=request_message,
        metadata=metadata,
        blockers=tuple(blockers),
        receipt_hash=receipt_hash,
    )


def plan_sql_view(
    view_spec: Mapping[str, Any],
    sql_policy: Mapping[str, Any],
) -> SqlViewPlanReceipt:
    """Plan a SQL view from selected columns and source tables."""

    view_name = str(view_spec.get("view_name") or view_spec.get("name") or "").strip()
    source_tables = tuple(str(value) for value in _as_sequence(view_spec.get("source_tables")) if str(value).strip())
    columns = tuple(str(value) for value in _as_sequence(view_spec.get("columns")) if str(value).strip())
    blockers: list[str] = []
    allowed_tables = {str(value) for value in _as_sequence(sql_policy.get("allowed_source_tables")) if str(value).strip()}
    if not view_name:
        blockers.append("missing_view_name")
    if not source_tables:
        blockers.append("missing_source_tables")
    for table in source_tables:
        if allowed_tables and table not in allowed_tables:
            blockers.append(f"source_table_not_allowed:{table}")
    if not columns:
        blockers.append("missing_columns")
    where_clause = str(view_spec.get("where") or "").strip()
    if sql_policy.get("forbid_select_star") and "*" in columns:
        blockers.append("select_star_forbidden")
    sql = ""
    if view_name and source_tables and columns:
        sql = f"CREATE VIEW {view_name} AS SELECT {', '.join(columns)} FROM {source_tables[0]}"
        if where_clause:
            sql += f" WHERE {where_clause}"
    sql_hash = "sql-view:" + _digest({"blockers": blockers, "sql": sql}, chars=RECEIPT_DIGEST_CHARS)
    return SqlViewPlanReceipt(
        ready=not blockers,
        view_name=view_name,
        sql=sql,
        source_tables=source_tables,
        blockers=tuple(blockers),
        sql_hash=sql_hash,
    )


def plan_sql_procedure(
    procedure_spec: Mapping[str, Any],
    sql_policy: Mapping[str, Any],
) -> SqlProcedurePlanReceipt:
    """Plan a stored procedure with parameter and mutation policy checks."""

    procedure_name = str(procedure_spec.get("procedure_name") or procedure_spec.get("name") or "").strip()
    parameters = tuple(str(value) for value in _as_sequence(procedure_spec.get("parameters")) if str(value).strip())
    statements = tuple(str(value).strip() for value in _as_sequence(procedure_spec.get("statements")) if str(value).strip())
    blockers: list[str] = []
    if not procedure_name:
        blockers.append("missing_procedure_name")
    for required_parameter in _as_sequence(sql_policy.get("required_parameters")):
        parameter = str(required_parameter)
        if parameter and parameter not in parameters:
            blockers.append(f"missing_parameter:{parameter}")
    if not statements:
        blockers.append("missing_statements")
    if sql_policy.get("readonly_only"):
        mutating_terms = ("insert ", "update ", "delete ", "drop ", "truncate ")
        for index, statement in enumerate(statements):
            if any(term in statement.lower() for term in mutating_terms):
                blockers.append(f"statement_{index + 1}_mutates_data")
    procedure_hash = "sql-procedure:" + _digest(
        {"blockers": blockers, "parameters": parameters, "procedure_name": procedure_name, "statements": statements},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SqlProcedurePlanReceipt(
        ready=not blockers,
        procedure_name=procedure_name,
        parameters=parameters,
        statements=statements,
        blockers=tuple(blockers),
        procedure_hash=procedure_hash,
    )


def plan_etl_pipeline(
    pipeline_spec: Mapping[str, Any],
    pipeline_policy: Mapping[str, Any],
) -> EtlPipelinePlanReceipt:
    """Plan an ETL pipeline with extract, transform, load, and checkpoint checks."""

    source_name = str(pipeline_spec.get("source") or pipeline_spec.get("source_name") or "").strip()
    target_name = str(pipeline_spec.get("target") or pipeline_spec.get("target_name") or "").strip()
    transforms = tuple(str(value) for value in _as_sequence(pipeline_spec.get("transforms")) if str(value).strip())
    blockers: list[str] = []
    if not source_name:
        blockers.append("missing_source")
    if not target_name:
        blockers.append("missing_target")
    if pipeline_policy.get("require_checkpoint") and _blank(pipeline_spec.get("checkpoint_key")):
        blockers.append("missing_checkpoint_key")
    if pipeline_policy.get("require_transforms") and not transforms:
        blockers.append("missing_transforms")
    steps = tuple(part for part in ("extract", *(f"transform:{item}" for item in transforms), "load") if part)
    pipeline_hash = "etl-pipeline:" + _digest(
        {"blockers": blockers, "source": source_name, "steps": steps, "target": target_name},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return EtlPipelinePlanReceipt(
        ready=not blockers,
        source_name=source_name,
        target_name=target_name,
        steps=steps,
        blockers=tuple(blockers),
        pipeline_hash=pipeline_hash,
    )


def plan_elt_model(
    model_spec: Mapping[str, Any],
    model_policy: Mapping[str, Any],
) -> EltModelPlanReceipt:
    """Plan an ELT/dbt-style model with dependency and test coverage gates."""

    model_name = str(model_spec.get("model_name") or model_spec.get("name") or "").strip()
    dependencies = tuple(str(value) for value in _as_sequence(model_spec.get("dependencies")) if str(value).strip())
    materialization = str(model_spec.get("materialization") or model_policy.get("default_materialization") or "view").strip()
    tests = tuple(str(value) for value in _as_sequence(model_spec.get("tests")) if str(value).strip())
    blockers: list[str] = []
    allowed_materializations = {str(value) for value in _as_sequence(model_policy.get("allowed_materializations")) if str(value).strip()}
    if not model_name:
        blockers.append("missing_model_name")
    if not dependencies:
        blockers.append("missing_dependencies")
    if allowed_materializations and materialization not in allowed_materializations:
        blockers.append("materialization_not_allowed")
    if model_policy.get("require_tests") and not tests:
        blockers.append("missing_tests")
    model_hash = "elt-model:" + _digest(
        {
            "blockers": blockers,
            "dependencies": dependencies,
            "materialization": materialization,
            "model_name": model_name,
            "tests": tests,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return EltModelPlanReceipt(
        ready=not blockers,
        model_name=model_name,
        dependencies=dependencies,
        materialization=materialization,
        tests=tests,
        blockers=tuple(blockers),
        model_hash=model_hash,
    )


def evaluate_alert_rule(
    metric_window: Mapping[str, Any],
    alert_policy: Mapping[str, Any],
) -> AlertRuleReceipt:
    """Evaluate an alert-rule definition with threshold and routing checks."""

    alert_name = str(alert_policy.get("alert_name") or alert_policy.get("name") or "").strip()
    metric = str(metric_window.get("metric") or alert_policy.get("metric") or "").strip()
    value = float(metric_window.get("value") or 0)
    threshold = float(alert_policy.get("threshold") or 0)
    operator = str(alert_policy.get("operator") or "gt").strip()
    severity = str(alert_policy.get("severity") or "warning").strip()
    routes = tuple(str(value) for value in _as_sequence(alert_policy.get("routes")) if str(value).strip())
    blockers: list[str] = []
    if not alert_name:
        blockers.append("missing_alert_name")
    if not metric:
        blockers.append("missing_metric")
    if threshold <= 0:
        blockers.append("missing_threshold")
    if not routes:
        blockers.append("missing_routes")
    valid_operators = {"gt", "gte", "lt", "lte", "eq"}
    if operator not in valid_operators:
        blockers.append("operator_not_supported")
    condition_met = {
        "gt": value > threshold,
        "gte": value >= threshold,
        "lt": value < threshold,
        "lte": value <= threshold,
        "eq": value == threshold,
    }.get(operator, False)
    condition = f"{metric} {operator} {threshold} -> {condition_met}" if metric else ""
    alert_hash = "alert-rule:" + _digest(
        {"alert_name": alert_name, "blockers": blockers, "condition": condition, "routes": routes},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return AlertRuleReceipt(
        ready=not blockers,
        alert_name=alert_name,
        severity=severity,
        condition=condition,
        routes=routes,
        blockers=tuple(blockers),
        alert_hash=alert_hash,
    )


def compile_runbook_plan(
    incident_context: Mapping[str, Any],
    runbook_policy: Mapping[str, Any],
) -> RunbookPlanReceipt:
    """Compile an operational runbook plan with required sections."""

    incident_type = str(incident_context.get("incident_type") or runbook_policy.get("incident_type") or "").strip()
    steps = tuple(str(value) for value in _as_sequence(runbook_policy.get("steps")) if str(value).strip())
    escalation_targets = tuple(str(value) for value in _as_sequence(runbook_policy.get("escalation_targets")) if str(value).strip())
    required_sections = tuple(str(value) for value in _as_sequence(runbook_policy.get("required_sections")) if str(value).strip())
    section_values = {
        "steps": bool(steps),
        "escalation_targets": bool(escalation_targets),
        "rollback": bool(runbook_policy.get("rollback")),
        "verification": bool(runbook_policy.get("verification")),
    }
    missing_sections = tuple(section for section in required_sections if not section_values.get(section))
    if not incident_type:
        missing_sections = (*missing_sections, "incident_type")
    runbook_hash = "runbook:" + _digest(
        {"incident_type": incident_type, "missing_sections": missing_sections, "steps": steps},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return RunbookPlanReceipt(
        ready=not missing_sections,
        incident_type=incident_type,
        steps=steps,
        escalation_targets=escalation_targets,
        missing_sections=missing_sections,
        runbook_hash=runbook_hash,
    )


def plan_incident_triage(
    incident_signal: Mapping[str, Any],
    triage_policy: Mapping[str, Any],
) -> IncidentTriagePlanReceipt:
    """Plan incident triage with severity, owner, impact, and runbook gates."""

    incident_id = str(incident_signal.get("incident_id") or incident_signal.get("id") or "").strip()
    summary = str(incident_signal.get("summary") or incident_signal.get("title") or "").strip()
    severity = str(incident_signal.get("severity") or triage_policy.get("default_severity") or "").strip()
    affected_services = tuple(str(value) for value in _as_sequence(incident_signal.get("affected_services")) if str(value).strip())
    priority = str(incident_signal.get("priority") or triage_policy.get("default_priority") or severity or "").strip()
    blockers: list[str] = []
    if not incident_id:
        blockers.append("missing_incident_id")
    if not summary:
        blockers.append("missing_summary")
    allowed_severities = {str(value) for value in _as_sequence(triage_policy.get("allowed_severities")) if str(value).strip()}
    if not severity:
        blockers.append("missing_severity")
    elif allowed_severities and severity not in allowed_severities:
        blockers.append(f"severity_not_allowed:{severity}")
    if triage_policy.get("require_affected_services") and not affected_services:
        blockers.append("missing_affected_services")
    if triage_policy.get("require_customer_impact") and _blank(incident_signal.get("customer_impact")):
        blockers.append("missing_customer_impact")
    if triage_policy.get("require_owner") and _blank(incident_signal.get("owner")):
        blockers.append("missing_owner")
    if triage_policy.get("require_runbook_ref") and _blank(incident_signal.get("runbook_ref")):
        blockers.append("missing_runbook_ref")
    max_detection_age_seconds = int(triage_policy.get("max_detection_age_seconds") or 0)
    detection_age_seconds = int(incident_signal.get("detection_age_seconds") or 0)
    if max_detection_age_seconds and detection_age_seconds > max_detection_age_seconds:
        blockers.append("detection_age_exceeds_policy")
    triage_hash = "incident-triage:" + _digest(
        {
            "affected_services": affected_services,
            "blockers": blockers,
            "incident_id": incident_id,
            "priority": priority,
            "severity": severity,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return IncidentTriagePlanReceipt(
        ready=not blockers,
        incident_id=incident_id,
        severity=severity,
        affected_services=affected_services,
        priority=priority,
        blockers=tuple(blockers),
        triage_hash=triage_hash,
    )


def plan_oncall_escalation(
    escalation_spec: Mapping[str, Any],
    escalation_policy: Mapping[str, Any],
) -> OncallEscalationPlanReceipt:
    """Plan on-call escalation with primary, backup, channel, and ack gates."""

    incident_id = str(escalation_spec.get("incident_id") or "").strip()
    primary_oncall = str(escalation_spec.get("primary_oncall") or "").strip()
    escalation_targets = tuple(str(value) for value in _as_sequence(escalation_spec.get("escalation_targets")) if str(value).strip())
    channels = tuple(str(value) for value in _as_sequence(escalation_spec.get("channels")) if str(value).strip())
    blockers: list[str] = []
    if not incident_id:
        blockers.append("missing_incident_id")
    if not primary_oncall:
        blockers.append("missing_primary_oncall")
    if escalation_policy.get("require_escalation_targets") and not escalation_targets:
        blockers.append("missing_escalation_targets")
    if escalation_policy.get("require_channels") and not channels:
        blockers.append("missing_channels")
    allowed_channels = {str(value) for value in _as_sequence(escalation_policy.get("allowed_channels")) if str(value).strip()}
    for channel in channels:
        if allowed_channels and channel not in allowed_channels:
            blockers.append(f"channel_not_allowed:{channel}")
    if escalation_policy.get("require_backup_oncall") and _blank(escalation_spec.get("backup_oncall")):
        blockers.append("missing_backup_oncall")
    max_ack_minutes = int(escalation_policy.get("max_ack_minutes") or 0)
    ack_minutes = int(escalation_spec.get("ack_minutes") or 0)
    if max_ack_minutes and (not ack_minutes or ack_minutes > max_ack_minutes):
        blockers.append("ack_minutes_exceeds_policy")
    if escalation_policy.get("require_pager_receipt") and _blank(escalation_spec.get("pager_receipt")):
        blockers.append("missing_pager_receipt")
    escalation_hash = "oncall-escalation:" + _digest(
        {
            "blockers": blockers,
            "channels": channels,
            "escalation_targets": escalation_targets,
            "incident_id": incident_id,
            "primary_oncall": primary_oncall,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return OncallEscalationPlanReceipt(
        ready=not blockers,
        incident_id=incident_id,
        primary_oncall=primary_oncall,
        escalation_targets=escalation_targets,
        channels=channels,
        blockers=tuple(blockers),
        escalation_hash=escalation_hash,
    )


def plan_status_page_update(
    status_spec: Mapping[str, Any],
    comms_policy: Mapping[str, Any],
) -> StatusPageUpdatePlanReceipt:
    """Plan status-page/customer update with approval and next-update gates."""

    incident_id = str(status_spec.get("incident_id") or "").strip()
    status = str(status_spec.get("status") or "").strip()
    components = tuple(str(value) for value in _as_sequence(status_spec.get("components")) if str(value).strip())
    audiences = tuple(str(value) for value in _as_sequence(status_spec.get("audiences")) if str(value).strip())
    blockers: list[str] = []
    if not incident_id:
        blockers.append("missing_incident_id")
    allowed_statuses = {str(value) for value in _as_sequence(comms_policy.get("allowed_statuses")) if str(value).strip()}
    if not status:
        blockers.append("missing_status")
    elif allowed_statuses and status not in allowed_statuses:
        blockers.append(f"status_not_allowed:{status}")
    if comms_policy.get("require_components") and not components:
        blockers.append("missing_components")
    if comms_policy.get("require_audience") and not audiences:
        blockers.append("missing_audience")
    if comms_policy.get("require_message") and _blank(status_spec.get("message")):
        blockers.append("missing_message")
    if comms_policy.get("require_impact_summary") and _blank(status_spec.get("impact_summary")):
        blockers.append("missing_impact_summary")
    if comms_policy.get("require_next_update_eta") and _blank(status_spec.get("next_update_eta")):
        blockers.append("missing_next_update_eta")
    if comms_policy.get("require_approval") and _blank(status_spec.get("approval")):
        blockers.append("missing_approval")
    if comms_policy.get("require_customer_visible") and status_spec.get("customer_visible") is not True:
        blockers.append("missing_customer_visible_flag")
    update_hash = "status-page-update:" + _digest(
        {
            "audiences": audiences,
            "blockers": blockers,
            "components": components,
            "incident_id": incident_id,
            "status": status,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return StatusPageUpdatePlanReceipt(
        ready=not blockers,
        incident_id=incident_id,
        status=status,
        components=components,
        audiences=audiences,
        blockers=tuple(blockers),
        update_hash=update_hash,
    )


def plan_maintenance_window(
    maintenance_spec: Mapping[str, Any],
    maintenance_policy: Mapping[str, Any],
) -> MaintenanceWindowPlanReceipt:
    """Plan maintenance windows with timing, notification, and rollback gates."""

    window_id = str(maintenance_spec.get("window_id") or maintenance_spec.get("id") or "").strip()
    affected_services = tuple(str(value) for value in _as_sequence(maintenance_spec.get("affected_services")) if str(value).strip())
    start_epoch = int(maintenance_spec.get("start_epoch") or 0)
    end_epoch = int(maintenance_spec.get("end_epoch") or 0)
    blockers: list[str] = []
    if not window_id:
        blockers.append("missing_window_id")
    if maintenance_policy.get("require_affected_services") and not affected_services:
        blockers.append("missing_affected_services")
    if not start_epoch:
        blockers.append("missing_start_epoch")
    if not end_epoch:
        blockers.append("missing_end_epoch")
    if start_epoch and end_epoch and end_epoch <= start_epoch:
        blockers.append("invalid_window_range")
    max_duration_seconds = int(maintenance_policy.get("max_duration_seconds") or 0)
    if max_duration_seconds and start_epoch and end_epoch and (end_epoch - start_epoch) > max_duration_seconds:
        blockers.append("window_duration_exceeds_policy")
    allowed_services = {str(value) for value in _as_sequence(maintenance_policy.get("allowed_services")) if str(value).strip()}
    for service in affected_services:
        if allowed_services and service not in allowed_services:
            blockers.append(f"service_not_allowed:{service}")
    if maintenance_policy.get("require_notification_channels") and not _as_sequence(maintenance_spec.get("notification_channels")):
        blockers.append("missing_notification_channels")
    if maintenance_policy.get("require_rollback_plan") and _blank(maintenance_spec.get("rollback_plan")):
        blockers.append("missing_rollback_plan")
    if maintenance_policy.get("require_owner") and _blank(maintenance_spec.get("owner")):
        blockers.append("missing_owner")
    if maintenance_policy.get("require_freeze_exception") and maintenance_spec.get("change_freeze") and _blank(maintenance_spec.get("freeze_exception")):
        blockers.append("missing_freeze_exception")
    window_hash = "maintenance-window:" + _digest(
        {
            "affected_services": affected_services,
            "blockers": blockers,
            "end_epoch": end_epoch,
            "start_epoch": start_epoch,
            "window_id": window_id,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return MaintenanceWindowPlanReceipt(
        ready=not blockers,
        window_id=window_id,
        affected_services=affected_services,
        start_epoch=start_epoch,
        end_epoch=end_epoch,
        blockers=tuple(blockers),
        window_hash=window_hash,
    )


def plan_postmortem_action_items(
    postmortem_spec: Mapping[str, Any],
    action_policy: Mapping[str, Any],
) -> PostmortemActionPlanReceipt:
    """Plan postmortem action items with owners, due dates, and verification."""

    incident_id = str(postmortem_spec.get("incident_id") or "").strip()
    action_items = tuple(dict(item) for item in _as_mapping_sequence(postmortem_spec.get("action_items")))
    blockers: list[str] = []
    action_ids: list[str] = []
    owners: list[str] = []
    if not incident_id:
        blockers.append("missing_incident_id")
    if action_policy.get("require_root_cause") and _blank(postmortem_spec.get("root_cause")):
        blockers.append("missing_root_cause")
    if action_policy.get("require_timeline") and not _as_sequence(postmortem_spec.get("timeline")):
        blockers.append("missing_timeline")
    if not action_items:
        blockers.append("missing_action_items")
    max_action_items = int(action_policy.get("max_action_items") or 0)
    if max_action_items and len(action_items) > max_action_items:
        blockers.append("action_item_count_exceeds_policy")
    for index, item in enumerate(action_items):
        action_id = str(item.get("action_id") or item.get("id") or "").strip()
        owner = str(item.get("owner") or "").strip()
        if action_id:
            action_ids.append(action_id)
        else:
            blockers.append(f"action_{index + 1}_missing_action_id")
        if owner:
            owners.append(owner)
        else:
            blockers.append(f"action_{action_id or index + 1}_missing_owner")
        if action_policy.get("require_due_date") and _blank(item.get("due_date")):
            blockers.append(f"action_{action_id or index + 1}_missing_due_date")
        if action_policy.get("require_prevention_type") and _blank(item.get("prevention_type")):
            blockers.append(f"action_{action_id or index + 1}_missing_prevention_type")
        if action_policy.get("require_verification_plan") and _blank(item.get("verification_plan")):
            blockers.append(f"action_{action_id or index + 1}_missing_verification_plan")
    if action_policy.get("require_owner_diversity"):
        min_owners = int(action_policy.get("min_owners") or 2)
        if len(set(owners)) < min_owners:
            blockers.append("owner_diversity_below_policy")
    action_hash = "postmortem-actions:" + _digest(
        {"action_ids": action_ids, "blockers": blockers, "incident_id": incident_id, "owners": owners},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PostmortemActionPlanReceipt(
        ready=not blockers,
        incident_id=incident_id,
        action_ids=tuple(action_ids),
        owners=tuple(owners),
        blockers=tuple(blockers),
        action_hash=action_hash,
    )


def build_test_fixture(
    fixture_policy: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> TestFixtureReceipt:
    """Build synthetic test fixture rows with required fields and redaction."""

    fixture_name = str(fixture_policy.get("fixture_name") or fixture_policy.get("name") or "fixture").strip()
    row_count = int(fixture_policy.get("row_count") or 1)
    fields = schema.get("fields") if isinstance(schema.get("fields"), Mapping) else {}
    required_fields = tuple(str(value) for value in _as_sequence(schema.get("required_fields")) if str(value).strip())
    pii_fields = tuple(str(value) for value in _as_sequence(fixture_policy.get("pii_fields")) if str(value).strip())
    blockers: list[str] = []
    if row_count < 1:
        blockers.append("row_count_must_be_positive")
        row_count = 0
    rows: list[JsonRecord] = []
    for index in range(row_count):
        row: JsonRecord = {}
        for field, field_type in fields.items():
            field_name = str(field)
            if field_name in pii_fields:
                row[field_name] = "***redacted***"
            elif field_type == "integer":
                row[field_name] = index + 1
            elif field_type == "number":
                row[field_name] = float(index + 1)
            elif field_type == "boolean":
                row[field_name] = index % 2 == 0
            else:
                row[field_name] = f"{field_name}-{index + 1}"
        rows.append(row)
    for field in required_fields:
        if not fields.get(field):
            blockers.append(f"required_field_not_in_schema:{field}")
    fixture_hash = "test-fixture:" + _digest(
        {"blockers": blockers, "fixture_name": fixture_name, "rows": rows},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return TestFixtureReceipt(
        ready=not blockers,
        fixture_name=fixture_name,
        rows=tuple(rows),
        redacted_fields=pii_fields,
        blockers=tuple(blockers),
        fixture_hash=fixture_hash,
    )


def plan_mock_server(
    api_spec: Mapping[str, Any],
    mock_policy: Mapping[str, Any],
) -> MockServerPlanReceipt:
    """Plan a mock server from route examples without opening sockets."""

    base_url = str(mock_policy.get("base_url") or "http://127.0.0.1:0").strip()
    routes = [dict(item) for item in _as_mapping_sequence(api_spec.get("routes") or api_spec.get("paths"))]
    blockers: list[str] = []
    planned_routes: list[JsonRecord] = []
    if not routes:
        blockers.append("missing_routes")
    for index, route in enumerate(routes):
        method = str(route.get("method") or "GET").upper()
        path = str(route.get("path") or "").strip()
        response = route.get("response") if isinstance(route.get("response"), Mapping) else {}
        if not path.startswith("/"):
            blockers.append(f"route_{index + 1}_invalid_path")
        if not response:
            blockers.append(f"route_{index + 1}_missing_response")
        planned_routes.append({"method": method, "path": path, "response": dict(response)})
    server_hash = "mock-server:" + _digest(
        {"base_url": base_url, "blockers": blockers, "routes": planned_routes},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return MockServerPlanReceipt(
        ready=not blockers,
        routes=tuple(planned_routes),
        base_url=base_url,
        blockers=tuple(blockers),
        server_hash=server_hash,
    )


def evaluate_policy_rule(
    action_context: Mapping[str, Any],
    policy_set: Mapping[str, Any],
) -> PolicyRuleDecisionReceipt:
    """Evaluate a deterministic allow/deny policy rule with reason codes."""

    action = str(action_context.get("action") or "").strip()
    subject_id = str(action_context.get("subject_id") or action_context.get("actor_id") or "").strip()
    blockers: list[str] = []
    reason_codes: list[str] = []
    if not action:
        blockers.append("missing_action")
    if not subject_id:
        blockers.append("missing_subject_id")
    allowed_actions = {str(value) for value in _as_sequence(policy_set.get("allowed_actions")) if str(value).strip()}
    if allowed_actions and action not in allowed_actions:
        reason_codes.append("action_not_allowed")
    required_fields = tuple(str(value) for value in _as_sequence(policy_set.get("required_context_fields")) if str(value).strip())
    for field in required_fields:
        if _blank(action_context.get(field)):
            blockers.append(f"missing_context_field:{field}")
    required_scopes = {str(value) for value in _as_sequence(policy_set.get("required_scopes")) if str(value).strip()}
    actor_scopes = {str(value) for value in _as_sequence(action_context.get("actor_scopes")) if str(value).strip()}
    for scope in sorted(required_scopes - actor_scopes):
        reason_codes.append(f"missing_scope:{scope}")
    deny_if = policy_set.get("deny_if") if isinstance(policy_set.get("deny_if"), Mapping) else {}
    for field, forbidden_value in deny_if.items():
        if action_context.get(field) == forbidden_value:
            reason_codes.append(f"deny_if:{field}")
    allowed = not blockers and not reason_codes
    decision = "allow" if allowed else "deny"
    receipt_hash = "policy-rule:" + _digest(
        {
            "action": action,
            "blockers": blockers,
            "decision": decision,
            "reason_codes": reason_codes,
            "subject_id": subject_id,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PolicyRuleDecisionReceipt(
        allowed=allowed,
        decision=decision,
        action=action,
        subject_id=subject_id,
        reason_codes=tuple(reason_codes),
        blockers=tuple(blockers),
        receipt_hash=receipt_hash,
    )


def plan_shell_script(
    script_spec: Mapping[str, Any],
    script_policy: Mapping[str, Any],
) -> ShellScriptPlanReceipt:
    """Plan a shell/script invocation as argv without executing a shell string."""

    command_argv = tuple(str(value) for value in _as_sequence(script_spec.get("argv")) if str(value).strip())
    if not command_argv:
        command = str(script_spec.get("command") or "").strip()
        command_argv = (command,) if command else ()
    env = script_spec.get("env") if isinstance(script_spec.get("env"), Mapping) else {}
    env_keys = tuple(sorted(str(key) for key in env.keys()))
    blockers: list[str] = []
    if not command_argv:
        blockers.append("missing_argv")
    allowed_commands = {str(value) for value in _as_sequence(script_policy.get("allowed_commands")) if str(value).strip()}
    if command_argv and allowed_commands and command_argv[0] not in allowed_commands:
        blockers.append(f"command_not_allowed:{command_argv[0]}")
    for key in _as_sequence(script_policy.get("required_env")):
        env_key = str(key)
        if env_key and _blank(env.get(env_key)):
            blockers.append(f"missing_env:{env_key}")
    if script_policy.get("forbid_shell_metacharacters"):
        metacharacters = set("|&;<>`$")
        for index, part in enumerate(command_argv):
            if any(char in metacharacters for char in part):
                blockers.append(f"argv_{index}_contains_shell_metacharacter")
    script_hash = "shell-script:" + _digest(
        {"argv": command_argv, "blockers": blockers, "env_keys": env_keys},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ShellScriptPlanReceipt(
        ready=not blockers,
        command_argv=command_argv,
        env_keys=env_keys,
        blockers=tuple(blockers),
        script_hash=script_hash,
    )


def plan_kubernetes_controller(
    controller_spec: Mapping[str, Any],
    controller_policy: Mapping[str, Any],
) -> KubernetesControllerPlanReceipt:
    """Plan a Kubernetes controller reconcile loop without touching a cluster."""

    controller_name = str(controller_spec.get("controller_name") or controller_spec.get("name") or "").strip()
    watched_kinds = tuple(str(value) for value in _as_sequence(controller_spec.get("watched_kinds")) if str(value).strip())
    reconcile_steps = tuple(str(value) for value in _as_sequence(controller_spec.get("reconcile_steps")) if str(value).strip())
    blockers: list[str] = []
    if not controller_name:
        blockers.append("missing_controller_name")
    if not watched_kinds:
        blockers.append("missing_watched_kinds")
    allowed_kinds = {str(value) for value in _as_sequence(controller_policy.get("allowed_watched_kinds")) if str(value).strip()}
    for kind in watched_kinds:
        if allowed_kinds and kind not in allowed_kinds:
            blockers.append(f"watched_kind_not_allowed:{kind}")
    if not reconcile_steps:
        blockers.append("missing_reconcile_steps")
    if controller_policy.get("require_finalizer") and not controller_spec.get("finalizer"):
        blockers.append("missing_finalizer")
    if controller_policy.get("require_leader_election") and not controller_spec.get("leader_election"):
        blockers.append("missing_leader_election")
    plan_hash = "kubernetes-controller:" + _digest(
        {
            "blockers": blockers,
            "controller_name": controller_name,
            "reconcile_steps": reconcile_steps,
            "watched_kinds": watched_kinds,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return KubernetesControllerPlanReceipt(
        ready=not blockers,
        controller_name=controller_name,
        watched_kinds=watched_kinds,
        reconcile_steps=reconcile_steps,
        blockers=tuple(blockers),
        plan_hash=plan_hash,
    )


def plan_workflow_group(
    workflow_spec: Mapping[str, Any],
    workflow_policy: Mapping[str, Any],
) -> WorkflowGroupPlanReceipt:
    """Plan a multi-step workflow group with explicit step-edge validation."""

    workflow_name = str(workflow_spec.get("workflow_name") or workflow_spec.get("name") or "").strip()
    steps = tuple(str(value) for value in _as_sequence(workflow_spec.get("steps")) if str(value).strip())
    edges = tuple(dict(item) for item in _as_mapping_sequence(workflow_spec.get("edges")))
    blockers: list[str] = []
    if not workflow_name:
        blockers.append("missing_workflow_name")
    if not steps:
        blockers.append("missing_steps")
    required_steps = tuple(str(value) for value in _as_sequence(workflow_policy.get("required_steps")) if str(value).strip())
    for step in required_steps:
        if step not in steps:
            blockers.append(f"missing_step:{step}")
    step_set = set(steps)
    for index, edge in enumerate(edges):
        source = str(edge.get("from") or "").strip()
        target = str(edge.get("to") or "").strip()
        if source not in step_set or target not in step_set:
            blockers.append(f"edge_{index + 1}_references_unknown_step")
    if workflow_policy.get("require_edges") and not edges:
        blockers.append("missing_edges")
    workflow_hash = "workflow-group:" + _digest(
        {"blockers": blockers, "edges": edges, "steps": steps, "workflow_name": workflow_name},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return WorkflowGroupPlanReceipt(
        ready=not blockers,
        workflow_name=workflow_name,
        steps=steps,
        edges=edges,
        blockers=tuple(blockers),
        workflow_hash=workflow_hash,
    )


def plan_ui_component(
    component_spec: Mapping[str, Any],
    design_policy: Mapping[str, Any],
) -> UiComponentPlanReceipt:
    """Plan a reusable UI component with props, states, and a11y gates."""

    component_name = str(component_spec.get("component_name") or component_spec.get("name") or "").strip()
    props = tuple(str(value) for value in _as_sequence(component_spec.get("props")) if str(value).strip())
    states = tuple(str(value) for value in _as_sequence(component_spec.get("states")) if str(value).strip())
    blockers: list[str] = []
    if not component_name:
        blockers.append("missing_component_name")
    if not props:
        blockers.append("missing_props")
    for prop in _as_sequence(design_policy.get("required_props")):
        prop_name = str(prop)
        if prop_name and prop_name not in props:
            blockers.append(f"missing_prop:{prop_name}")
    required_states = tuple(str(value) for value in _as_sequence(design_policy.get("required_states")) if str(value).strip())
    for state in required_states:
        if state not in states:
            blockers.append(f"missing_state:{state}")
    if design_policy.get("require_accessible_name") and _blank(component_spec.get("accessible_name")):
        blockers.append("missing_accessible_name")
    component_hash = "ui-component:" + _digest(
        {"blockers": blockers, "component_name": component_name, "props": props, "states": states},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return UiComponentPlanReceipt(
        ready=not blockers,
        component_name=component_name,
        props=props,
        states=states,
        blockers=tuple(blockers),
        component_hash=component_hash,
    )


def plan_ui_route(
    route_spec: Mapping[str, Any],
    route_policy: Mapping[str, Any],
) -> UiRoutePlanReceipt:
    """Plan a UI route/page with data dependencies and expected components."""

    route_path = str(route_spec.get("route_path") or route_spec.get("path") or "").strip()
    data_dependencies = tuple(str(value) for value in _as_sequence(route_spec.get("data_dependencies")) if str(value).strip())
    components = tuple(str(value) for value in _as_sequence(route_spec.get("components")) if str(value).strip())
    blockers: list[str] = []
    if not route_path:
        blockers.append("missing_route_path")
    elif not route_path.startswith("/"):
        blockers.append("route_path_must_start_with_slash")
    allowed_prefixes = tuple(str(value) for value in _as_sequence(route_policy.get("allowed_path_prefixes")) if str(value).strip())
    if route_path and allowed_prefixes and not any(route_path.startswith(prefix) for prefix in allowed_prefixes):
        blockers.append("route_path_not_allowed")
    if route_policy.get("require_data_dependencies") and not data_dependencies:
        blockers.append("missing_data_dependencies")
    if not components:
        blockers.append("missing_components")
    for component in _as_sequence(route_policy.get("required_components")):
        component_name = str(component)
        if component_name and component_name not in components:
            blockers.append(f"missing_component:{component_name}")
    if route_policy.get("require_error_boundary") and "ErrorBoundary" not in components:
        blockers.append("missing_error_boundary")
    route_hash = "ui-route:" + _digest(
        {
            "blockers": blockers,
            "components": components,
            "data_dependencies": data_dependencies,
            "route_path": route_path,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return UiRoutePlanReceipt(
        ready=not blockers,
        route_path=route_path,
        data_dependencies=data_dependencies,
        components=components,
        blockers=tuple(blockers),
        route_hash=route_hash,
    )


def plan_ui_api_binding(
    binding_spec: Mapping[str, Any],
    binding_policy: Mapping[str, Any],
) -> UiApiBindingPlanReceipt:
    """Plan UI bindings to API operations with state, mutation, and auth gates."""

    component_name = str(binding_spec.get("component_name") or binding_spec.get("name") or "").strip()
    operations = tuple(dict(item) for item in _as_mapping_sequence(binding_spec.get("api_operations") or binding_spec.get("operations")))
    data_dependencies = tuple(str(value) for value in _as_sequence(binding_spec.get("data_dependencies")) if str(value).strip())
    loading_states = {str(value) for value in _as_sequence(binding_spec.get("loading_states")) if str(value).strip()}
    error_states = {str(value) for value in _as_sequence(binding_spec.get("error_states")) if str(value).strip()}
    auth_scopes = {str(value) for value in _as_sequence(binding_spec.get("auth_scopes")) if str(value).strip()}
    operation_ids: list[str] = []
    mutation_operations: list[str] = []
    blockers: list[str] = []
    if not component_name:
        blockers.append("missing_component_name")
    if not operations:
        blockers.append("missing_api_operations")
    allowed_methods = {str(value).upper() for value in _as_sequence(binding_policy.get("allowed_methods")) if str(value).strip()}
    mutating_methods = {"POST", "PUT", "PATCH", "DELETE"}
    for index, operation in enumerate(operations):
        operation_id = str(operation.get("operation_id") or operation.get("id") or "").strip()
        method = str(operation.get("method") or "GET").upper()
        path = str(operation.get("path") or "").strip()
        if operation_id:
            operation_ids.append(operation_id)
        else:
            blockers.append(f"operation_{index + 1}_missing_operation_id")
        if allowed_methods and method not in allowed_methods:
            blockers.append(f"operation_{index + 1}_method_not_allowed:{method}")
        if not path.startswith("/"):
            blockers.append(f"operation_{index + 1}_missing_path")
        if binding_policy.get("require_response_schema") and not isinstance(operation.get("response_schema"), Mapping):
            blockers.append(f"operation_{index + 1}_missing_response_schema")
        if method in mutating_methods:
            if operation_id:
                mutation_operations.append(operation_id)
            if binding_policy.get("require_request_schema_for_mutations") and not isinstance(operation.get("request_schema"), Mapping):
                blockers.append(f"operation_{index + 1}_missing_request_schema")
    for operation_id in _as_sequence(binding_policy.get("required_operations")):
        required_operation = str(operation_id)
        if required_operation and required_operation not in operation_ids:
            blockers.append(f"missing_required_operation:{required_operation}")
    if binding_policy.get("require_data_dependency_per_operation"):
        for operation_id in operation_ids:
            if operation_id not in data_dependencies:
                blockers.append(f"missing_data_dependency:{operation_id}")
    if binding_policy.get("require_mutation_handlers"):
        handlers = {str(value) for value in _as_sequence(binding_spec.get("mutation_handlers")) if str(value).strip()}
        for operation_id in mutation_operations:
            if operation_id not in handlers:
                blockers.append(f"missing_mutation_handler:{operation_id}")
    if binding_policy.get("require_loading_state") and not loading_states:
        blockers.append("missing_loading_state")
    if binding_policy.get("require_error_state") and not error_states:
        blockers.append("missing_error_state")
    required_scopes = {str(value) for value in _as_sequence(binding_policy.get("required_auth_scopes")) if str(value).strip()}
    for scope in sorted(required_scopes - auth_scopes):
        blockers.append(f"missing_auth_scope:{scope}")
    binding_hash = "ui-api-binding:" + _digest(
        {
            "blockers": blockers,
            "component_name": component_name,
            "data_dependencies": data_dependencies,
            "mutation_operations": mutation_operations,
            "operation_ids": operation_ids,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return UiApiBindingPlanReceipt(
        ready=not blockers,
        component_name=component_name,
        operation_ids=tuple(operation_ids),
        data_dependencies=data_dependencies,
        mutation_operations=tuple(mutation_operations),
        blockers=tuple(blockers),
        binding_hash=binding_hash,
    )


def plan_ui_form_validation(
    form_spec: Mapping[str, Any],
    validation_policy: Mapping[str, Any],
) -> UiFormValidationPlanReceipt:
    """Plan UI form validation with client/server and accessible-error gates."""

    form_name = str(form_spec.get("form_name") or form_spec.get("name") or "").strip()
    fields = tuple(dict(item) for item in _as_mapping_sequence(form_spec.get("fields")))
    submit_action = str(form_spec.get("submit_action") or "").strip()
    blockers: list[str] = []
    field_names: list[str] = []
    if not form_name:
        blockers.append("missing_form_name")
    if not fields:
        blockers.append("missing_fields")
    for index, field in enumerate(fields):
        field_name = str(field.get("name") or "").strip()
        if field_name:
            field_names.append(field_name)
        else:
            blockers.append(f"field_{index + 1}_missing_name")
            continue
        validators = {str(value) for value in _as_sequence(field.get("validators")) if str(value).strip()}
        for validator in _as_sequence(validation_policy.get("required_validators_by_field", {}).get(field_name) if isinstance(validation_policy.get("required_validators_by_field"), Mapping) else []):
            validator_name = str(validator)
            if validator_name and validator_name not in validators:
                blockers.append(f"missing_validator:{field_name}:{validator_name}")
        if validation_policy.get("require_accessible_labels") and _blank(field.get("accessible_label")):
            blockers.append(f"field_{field_name}_missing_accessible_label")
    for required_field in _as_sequence(validation_policy.get("required_fields")):
        required_name = str(required_field)
        if required_name and required_name not in field_names:
            blockers.append(f"missing_required_field:{required_name}")
    if validation_policy.get("require_submit_action") and not submit_action:
        blockers.append("missing_submit_action")
    if validation_policy.get("require_client_validation") and not form_spec.get("client_validation"):
        blockers.append("missing_client_validation")
    if validation_policy.get("require_server_validation") and not form_spec.get("server_validation"):
        blockers.append("missing_server_validation")
    if validation_policy.get("require_error_summary") and not form_spec.get("error_summary"):
        blockers.append("missing_error_summary")
    validation_hash = "ui-form-validation:" + _digest(
        {"blockers": blockers, "field_names": field_names, "form_name": form_name, "submit_action": submit_action},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return UiFormValidationPlanReceipt(
        ready=not blockers,
        form_name=form_name,
        field_names=tuple(field_names),
        submit_action=submit_action,
        blockers=tuple(blockers),
        validation_hash=validation_hash,
    )


def plan_ui_table_state(
    table_spec: Mapping[str, Any],
    table_policy: Mapping[str, Any],
) -> UiTableStatePlanReceipt:
    """Plan reusable table state for columns, row keys, filters, and states."""

    table_name = str(table_spec.get("table_name") or table_spec.get("name") or "").strip()
    columns = tuple(str(value) for value in _as_sequence(table_spec.get("columns")) if str(value).strip())
    blockers: list[str] = []
    controls: list[str] = []
    if not table_name:
        blockers.append("missing_table_name")
    if not columns:
        blockers.append("missing_columns")
    for column in _as_sequence(table_policy.get("required_columns")):
        column_name = str(column)
        if column_name and column_name not in columns:
            blockers.append(f"missing_column:{column_name}")
    if table_policy.get("require_row_key") and _blank(table_spec.get("row_key")):
        blockers.append("missing_row_key")
    for name, flag in (
        ("pagination", table_policy.get("require_pagination")),
        ("sorting", table_policy.get("require_sorting")),
        ("filters", table_policy.get("require_filters")),
        ("loading_state", table_policy.get("require_loading_state")),
        ("empty_state", table_policy.get("require_empty_state")),
        ("error_state", table_policy.get("require_error_state")),
    ):
        if flag:
            if table_spec.get(name):
                controls.append(name)
            else:
                blockers.append(f"missing_{name}")
    if table_policy.get("require_selection_mode"):
        selection_mode = str(table_spec.get("selection_mode") or "").strip()
        if selection_mode:
            controls.append(f"selection:{selection_mode}")
        else:
            blockers.append("missing_selection_mode")
    table_hash = "ui-table-state:" + _digest(
        {"blockers": blockers, "columns": columns, "controls": controls, "table_name": table_name},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return UiTableStatePlanReceipt(
        ready=not blockers,
        table_name=table_name,
        columns=columns,
        state_controls=tuple(controls),
        blockers=tuple(blockers),
        state_hash=table_hash,
    )


def plan_dashboard_filter_contract(
    dashboard_spec: Mapping[str, Any],
    filter_policy: Mapping[str, Any],
) -> DashboardFilterContractPlanReceipt:
    """Plan dashboard filter contracts with metric bindings and reset behavior."""

    dashboard_name = str(dashboard_spec.get("dashboard_name") or dashboard_spec.get("name") or "").strip()
    filters = tuple(dict(item) for item in _as_mapping_sequence(dashboard_spec.get("filters")))
    metrics = tuple(str(value) for value in _as_sequence(dashboard_spec.get("metrics")) if str(value).strip())
    metric_bindings = dashboard_spec.get("metric_filter_bindings") if isinstance(dashboard_spec.get("metric_filter_bindings"), Mapping) else {}
    filter_names = tuple(str(item.get("name") or "").strip() for item in filters if str(item.get("name") or "").strip())
    blockers: list[str] = []
    if not dashboard_name:
        blockers.append("missing_dashboard_name")
    if not filters:
        blockers.append("missing_filters")
    if not metrics:
        blockers.append("missing_metrics")
    allowed_filter_types = {str(value) for value in _as_sequence(filter_policy.get("allowed_filter_types")) if str(value).strip()}
    for index, item in enumerate(filters):
        name = str(item.get("name") or "").strip()
        filter_type = str(item.get("type") or "").strip()
        if not name:
            blockers.append(f"filter_{index + 1}_missing_name")
        if not filter_type:
            blockers.append(f"filter_{index + 1}_missing_type")
        elif allowed_filter_types and filter_type not in allowed_filter_types:
            blockers.append(f"filter_type_not_allowed:{filter_type}")
        if filter_policy.get("require_default_values") and "default" not in item:
            blockers.append(f"filter_{name or index + 1}_missing_default")
    for required_filter in _as_sequence(filter_policy.get("required_filters")):
        required_name = str(required_filter)
        if required_name and required_name not in filter_names:
            blockers.append(f"missing_filter:{required_name}")
    if filter_policy.get("require_metric_bindings"):
        for metric in metrics:
            bound_filters = {str(value) for value in _as_sequence(metric_bindings.get(metric)) if str(value).strip()}
            if not bound_filters:
                blockers.append(f"missing_metric_binding:{metric}")
            for filter_name in bound_filters:
                if filter_name not in filter_names:
                    blockers.append(f"metric_binding_unknown_filter:{metric}:{filter_name}")
    if filter_policy.get("require_reset_action") and not dashboard_spec.get("reset_action"):
        blockers.append("missing_reset_action")
    contract_hash = "dashboard-filter-contract:" + _digest(
        {"blockers": blockers, "dashboard_name": dashboard_name, "filters": filter_names, "metrics": metrics},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DashboardFilterContractPlanReceipt(
        ready=not blockers,
        dashboard_name=dashboard_name,
        filters=filter_names,
        metrics=metrics,
        blockers=tuple(blockers),
        contract_hash=contract_hash,
    )


def plan_ui_accessibility_interaction(
    interaction_spec: Mapping[str, Any],
    accessibility_policy: Mapping[str, Any],
) -> UiAccessibilityInteractionPlanReceipt:
    """Plan UI interaction accessibility with keyboard, focus, and ARIA checks."""

    surface_name = str(interaction_spec.get("surface_name") or interaction_spec.get("name") or "").strip()
    interactions = tuple(dict(item) for item in _as_mapping_sequence(interaction_spec.get("interactions")))
    blockers: list[str] = []
    interaction_names: list[str] = []
    roles: list[str] = []
    if not surface_name:
        blockers.append("missing_surface_name")
    if not interactions:
        blockers.append("missing_interactions")
    allowed_roles = {str(value) for value in _as_sequence(accessibility_policy.get("allowed_roles")) if str(value).strip()}
    for index, interaction in enumerate(interactions):
        name = str(interaction.get("name") or "").strip()
        role = str(interaction.get("role") or "").strip()
        if name:
            interaction_names.append(name)
        else:
            blockers.append(f"interaction_{index + 1}_missing_name")
        if role:
            roles.append(role)
            if allowed_roles and role not in allowed_roles:
                blockers.append(f"role_not_allowed:{role}")
        else:
            blockers.append(f"interaction_{index + 1}_missing_role")
        if accessibility_policy.get("require_accessible_name") and _blank(interaction.get("accessible_name")):
            blockers.append(f"interaction_{name or index + 1}_missing_accessible_name")
        if accessibility_policy.get("require_keyboard_support") and not (interaction.get("keyboard_shortcut") or interaction.get("keyboard_path")):
            blockers.append(f"interaction_{name or index + 1}_missing_keyboard_support")
        if accessibility_policy.get("require_focus_state") and not interaction.get("focus_state"):
            blockers.append(f"interaction_{name or index + 1}_missing_focus_state")
        if accessibility_policy.get("require_touch_target") and not interaction.get("touch_target"):
            blockers.append(f"interaction_{name or index + 1}_missing_touch_target")
    for required_role in _as_sequence(accessibility_policy.get("required_roles")):
        role_name = str(required_role)
        if role_name and role_name not in roles:
            blockers.append(f"missing_required_role:{role_name}")
    if accessibility_policy.get("require_aria_live_for_async") and interaction_spec.get("async_updates") and not interaction_spec.get("aria_live_region"):
        blockers.append("missing_aria_live_region")
    if accessibility_policy.get("require_reduced_motion_toggle") and interaction_spec.get("motion") and not interaction_spec.get("reduced_motion_toggle"):
        blockers.append("missing_reduced_motion_toggle")
    accessibility_hash = "ui-accessibility-interaction:" + _digest(
        {"blockers": blockers, "interactions": interaction_names, "roles": roles, "surface_name": surface_name},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return UiAccessibilityInteractionPlanReceipt(
        ready=not blockers,
        surface_name=surface_name,
        interactions=tuple(interaction_names),
        roles=tuple(roles),
        blockers=tuple(blockers),
        accessibility_hash=accessibility_hash,
    )


def plan_api_resource_group(
    resource_spec: Mapping[str, Any],
    api_policy: Mapping[str, Any],
) -> ApiResourceGroupPlanReceipt:
    """Plan a resource API group across CRUD/search/export operation contracts."""

    resource_name = str(resource_spec.get("resource_name") or resource_spec.get("name") or "").strip()
    operations = tuple(str(value) for value in _as_sequence(resource_spec.get("operations")) if str(value).strip())
    required_operations = tuple(str(value) for value in _as_sequence(api_policy.get("required_operations")) if str(value).strip())
    blockers: list[str] = []
    if not resource_name:
        blockers.append("missing_resource_name")
    if not operations:
        blockers.append("missing_operations")
    missing_operations = tuple(operation for operation in required_operations if operation not in operations)
    for operation in missing_operations:
        blockers.append(f"missing_operation:{operation}")
    if api_policy.get("require_auth") and not resource_spec.get("auth"):
        blockers.append("missing_auth")
    mutating_operations = {"create", "update", "patch", "delete", "archive", "import"}
    if api_policy.get("require_idempotency_for_mutations"):
        idempotent_operations = {str(value) for value in _as_sequence(resource_spec.get("idempotent_operations")) if str(value).strip()}
        for operation in sorted(set(operations) & mutating_operations):
            if operation not in idempotent_operations:
                blockers.append(f"missing_idempotency:{operation}")
    api_hash = "api-resource-group:" + _digest(
        {
            "blockers": blockers,
            "missing_operations": missing_operations,
            "operations": operations,
            "resource_name": resource_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiResourceGroupPlanReceipt(
        ready=not blockers,
        resource_name=resource_name,
        operations=operations,
        missing_operations=missing_operations,
        blockers=tuple(blockers),
        api_hash=api_hash,
    )


def plan_microservice_bundle(
    service_spec: Mapping[str, Any],
    service_policy: Mapping[str, Any],
) -> MicroserviceBundlePlanReceipt:
    """Plan a microservice bundle with endpoints, workers, storage, and proof gates."""

    service_name = str(service_spec.get("service_name") or service_spec.get("name") or "").strip()
    endpoints = tuple(str(value) for value in _as_sequence(service_spec.get("endpoints")) if str(value).strip())
    workers = tuple(str(value) for value in _as_sequence(service_spec.get("workers")) if str(value).strip())
    events = tuple(str(value) for value in _as_sequence(service_spec.get("events")) if str(value).strip())
    data_stores = tuple(str(value) for value in _as_sequence(service_spec.get("data_stores")) if str(value).strip())
    surfaces = tuple(part for part in (*endpoints, *workers, *events) if part)
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if service_policy.get("require_callable_surface") and not surfaces:
        blockers.append("missing_callable_surface")
    if service_policy.get("require_data_store") and not data_stores:
        blockers.append("missing_data_store")
    if service_policy.get("require_health_check") and not service_spec.get("health_check"):
        blockers.append("missing_health_check")
    if service_policy.get("require_telemetry") and not service_spec.get("telemetry"):
        blockers.append("missing_telemetry")
    for env_key in _as_sequence(service_policy.get("required_env")):
        key = str(env_key)
        env = service_spec.get("env") if isinstance(service_spec.get("env"), Mapping) else {}
        if key and _blank(env.get(key)):
            blockers.append(f"missing_env:{key}")
    service_hash = "microservice-bundle:" + _digest(
        {
            "blockers": blockers,
            "data_stores": data_stores,
            "service_name": service_name,
            "surfaces": surfaces,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return MicroserviceBundlePlanReceipt(
        ready=not blockers,
        service_name=service_name,
        surfaces=surfaces,
        data_stores=data_stores,
        blockers=tuple(blockers),
        service_hash=service_hash,
    )


def plan_service_boundary_contract(
    service_spec: Mapping[str, Any],
    boundary_policy: Mapping[str, Any],
) -> ServiceBoundaryContractPlanReceipt:
    """Plan service boundary ownership with bounded context, capabilities, and dependency contracts."""

    raw_service_name = str(service_spec.get("service_name") or service_spec.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    bounded_context = normalize_field_name(service_spec.get("bounded_context") or "") if not _blank(service_spec.get("bounded_context")) else ""
    owned_capabilities = tuple(normalize_field_name(value) for value in _as_sequence(service_spec.get("owned_capabilities")) if not _blank(value))
    external_dependencies = tuple(normalize_field_name(value) for value in _as_sequence(service_spec.get("external_dependencies")) if not _blank(value))
    dependency_contracts = {normalize_field_name(value) for value in _as_sequence(service_spec.get("dependency_contracts")) if not _blank(value)}
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if boundary_policy.get("require_bounded_context") and not bounded_context:
        blockers.append("missing_bounded_context")
    if boundary_policy.get("require_owned_capabilities") and not owned_capabilities:
        blockers.append("missing_owned_capabilities")
    if boundary_policy.get("require_owner_team") and _blank(service_spec.get("owner_team")):
        blockers.append("missing_owner_team")
    if boundary_policy.get("require_dependency_contracts"):
        for dependency in external_dependencies:
            if dependency not in dependency_contracts:
                blockers.append(f"dependency_without_contract:{dependency}")
    if boundary_policy.get("forbid_shared_store_access") and _as_sequence(service_spec.get("shared_store_access")):
        blockers.append("forbidden_shared_store_access")
    if boundary_policy.get("require_boundary_receipt") and _blank(service_spec.get("boundary_receipt")):
        blockers.append("missing_boundary_receipt")
    boundary_hash = "service-boundary-contract:" + _digest(
        {
            "blockers": blockers,
            "bounded_context": bounded_context,
            "external_dependencies": external_dependencies,
            "owned_capabilities": owned_capabilities,
            "service_name": service_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ServiceBoundaryContractPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        bounded_context=bounded_context,
        owned_capabilities=owned_capabilities,
        external_dependencies=external_dependencies,
        blockers=tuple(blockers),
        boundary_hash=boundary_hash,
    )


def plan_service_surface_inventory(
    surface_spec: Mapping[str, Any],
    inventory_policy: Mapping[str, Any],
) -> ServiceSurfaceInventoryPlanReceipt:
    """Plan service surface inventory with endpoint, worker, event, visibility, and auth gates."""

    raw_service_name = str(surface_spec.get("service_name") or surface_spec.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    surface_rows = tuple(dict(item) for item in _as_mapping_sequence(surface_spec.get("surfaces")))
    surface_names: list[str] = []
    public_surfaces: list[str] = []
    surface_kinds: set[str] = set()
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if not surface_rows:
        blockers.append("missing_surfaces")
    for index, surface in enumerate(surface_rows):
        name = str(surface.get("name") or surface.get("id") or "").strip()
        kind = normalize_field_name(surface.get("kind") or surface.get("type") or "")
        visibility = normalize_field_name(surface.get("visibility") or "")
        if not name:
            blockers.append(f"surface_{index + 1}_missing_name")
        else:
            surface_names.append(name)
        if not kind or kind == "field":
            blockers.append(f"surface_{index + 1}_missing_kind")
        else:
            surface_kinds.add(kind)
        if visibility in {"public", "external"}:
            if name:
                public_surfaces.append(name)
            if inventory_policy.get("require_auth_for_public") and _blank(surface.get("auth")):
                blockers.append(f"public_surface_missing_auth:{name or index + 1}")
    for kind in _as_sequence(inventory_policy.get("required_surface_kinds")):
        kind_name = normalize_field_name(kind)
        if kind_name and kind_name not in surface_kinds:
            blockers.append(f"missing_required_surface_kind:{kind_name}")
    if inventory_policy.get("require_inventory_receipt") and _blank(surface_spec.get("inventory_receipt")):
        blockers.append("missing_inventory_receipt")
    inventory_hash = "service-surface-inventory:" + _digest(
        {
            "blockers": blockers,
            "public_surfaces": tuple(public_surfaces),
            "service_name": service_name,
            "surfaces": tuple(surface_names),
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ServiceSurfaceInventoryPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        surfaces=tuple(surface_names),
        public_surfaces=tuple(public_surfaces),
        blockers=tuple(blockers),
        inventory_hash=inventory_hash,
    )


def plan_service_data_ownership(
    data_spec: Mapping[str, Any],
    ownership_policy: Mapping[str, Any],
) -> ServiceDataOwnershipPlanReceipt:
    """Plan service data ownership with owned stores, read-only dependencies, and lifecycle proof."""

    raw_service_name = str(data_spec.get("service_name") or data_spec.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    owned_stores = tuple(normalize_field_name(value) for value in _as_sequence(data_spec.get("owned_stores")) if not _blank(value))
    read_only_stores = tuple(normalize_field_name(value) for value in _as_sequence(data_spec.get("read_only_stores")) if not _blank(value))
    shared_write_stores = tuple(normalize_field_name(value) for value in _as_sequence(data_spec.get("shared_write_stores")) if not _blank(value))
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if ownership_policy.get("require_owned_store") and not owned_stores:
        blockers.append("missing_owned_stores")
    for store in shared_write_stores:
        blockers.append(f"shared_write_store:{store}")
    if ownership_policy.get("require_migration_owner") and _blank(data_spec.get("migration_owner")):
        blockers.append("missing_migration_owner")
    if ownership_policy.get("require_backup_policy") and _blank(data_spec.get("backup_policy")):
        blockers.append("missing_backup_policy")
    if ownership_policy.get("require_data_classification") and _blank(data_spec.get("data_classification")):
        blockers.append("missing_data_classification")
    if ownership_policy.get("require_retention_policy") and _blank(data_spec.get("retention_policy")):
        blockers.append("missing_retention_policy")
    if ownership_policy.get("require_ownership_receipt") and _blank(data_spec.get("ownership_receipt")):
        blockers.append("missing_ownership_receipt")
    ownership_hash = "service-data-ownership:" + _digest(
        {
            "blockers": blockers,
            "owned_stores": owned_stores,
            "read_only_stores": read_only_stores,
            "service_name": service_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ServiceDataOwnershipPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        owned_stores=owned_stores,
        read_only_stores=read_only_stores,
        blockers=tuple(blockers),
        ownership_hash=ownership_hash,
    )


def plan_service_startup_order(
    startup_spec: Mapping[str, Any],
    startup_policy: Mapping[str, Any],
) -> ServiceStartupOrderPlanReceipt:
    """Plan service startup order with dependency checks, migration gate, readiness, and timing."""

    raw_service_name = str(startup_spec.get("service_name") or startup_spec.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    startup_steps = tuple(normalize_field_name(value) for value in _as_sequence(startup_spec.get("startup_steps")) if not _blank(value))
    max_startup_seconds = int(startup_spec.get("max_startup_seconds") or 0)
    policy_max_startup_seconds = int(startup_policy.get("max_startup_seconds") or 0)
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if not startup_steps:
        blockers.append("missing_startup_steps")
    for step in _as_sequence(startup_policy.get("required_steps")):
        step_name = normalize_field_name(step)
        if step_name and step_name not in startup_steps:
            blockers.append(f"missing_step:{step_name}")
    if startup_policy.get("require_dependency_checks") and not _as_sequence(startup_spec.get("dependency_checks")):
        blockers.append("missing_dependency_checks")
    if startup_policy.get("require_migration_gate") and _blank(startup_spec.get("migration_gate")):
        blockers.append("missing_migration_gate")
    if startup_policy.get("require_readiness_probe") and _blank(startup_spec.get("readiness_probe")):
        blockers.append("missing_readiness_probe")
    if max_startup_seconds <= 0:
        blockers.append("missing_max_startup_seconds")
    elif policy_max_startup_seconds and max_startup_seconds > policy_max_startup_seconds:
        blockers.append("startup_time_exceeds_policy")
    startup_hash = "service-startup-order:" + _digest(
        {
            "blockers": blockers,
            "max_startup_seconds": max_startup_seconds,
            "service_name": service_name,
            "startup_steps": startup_steps,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ServiceStartupOrderPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        startup_steps=startup_steps,
        blockers=tuple(blockers),
        startup_hash=startup_hash,
    )


def plan_service_secret_binding(
    secret_spec: Mapping[str, Any],
    secret_policy: Mapping[str, Any],
) -> ServiceSecretBindingPlanReceipt:
    """Plan service secret bindings with secret refs, providers, rotation policy, and runtime identity."""

    raw_service_name = str(secret_spec.get("service_name") or secret_spec.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    bindings = tuple(dict(item) for item in _as_mapping_sequence(secret_spec.get("secret_bindings") or secret_spec.get("secrets")))
    allowed_providers = {normalize_field_name(value) for value in _as_sequence(secret_policy.get("allowed_providers")) if not _blank(value)}
    secret_refs: list[str] = []
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if not bindings:
        blockers.append("missing_secret_bindings")
    for index, binding in enumerate(bindings):
        secret_ref = str(binding.get("secret_ref") or binding.get("ref") or "").strip()
        env_key = str(binding.get("env_key") or "").strip()
        provider = normalize_field_name(binding.get("provider") or "")
        if not secret_ref:
            blockers.append(f"binding_{index + 1}_missing_secret_ref")
        else:
            secret_refs.append(secret_ref)
        if not env_key:
            blockers.append(f"binding_{index + 1}_missing_env_key")
        if allowed_providers and provider not in allowed_providers:
            blockers.append(f"secret_provider_not_allowed:{provider or 'missing'}")
    if secret_policy.get("require_rotation_policy") and _blank(secret_spec.get("rotation_policy")):
        blockers.append("missing_rotation_policy")
    if secret_policy.get("require_runtime_identity") and _blank(secret_spec.get("runtime_identity")):
        blockers.append("missing_runtime_identity")
    if secret_policy.get("require_secret_receipt") and _blank(secret_spec.get("secret_receipt")):
        blockers.append("missing_secret_receipt")
    binding_hash = "service-secret-binding:" + _digest(
        {
            "blockers": blockers,
            "secret_refs": tuple(secret_refs),
            "service_name": service_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ServiceSecretBindingPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        secret_refs=tuple(secret_refs),
        blockers=tuple(blockers),
        binding_hash=binding_hash,
    )


def plan_service_backpressure_policy(
    backpressure_spec: Mapping[str, Any],
    backpressure_policy: Mapping[str, Any],
) -> ServiceBackpressurePolicyPlanReceipt:
    """Plan service backpressure with inflight, queue policy, overload strategy, and retry/degrade proof."""

    raw_service_name = str(backpressure_spec.get("service_name") or backpressure_spec.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    max_inflight = int(backpressure_spec.get("max_inflight") or backpressure_spec.get("max_concurrency") or 0)
    policy_max_inflight = int(backpressure_policy.get("max_inflight") or backpressure_policy.get("max_concurrency") or 0)
    queue_policy = normalize_field_name(backpressure_spec.get("queue_policy") or "")
    allowed_queue_policies = {normalize_field_name(value) for value in _as_sequence(backpressure_policy.get("allowed_queue_policies")) if not _blank(value)}
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if max_inflight <= 0:
        blockers.append("missing_max_inflight")
    elif policy_max_inflight and max_inflight > policy_max_inflight:
        blockers.append("max_inflight_exceeds_policy")
    if backpressure_policy.get("require_queue_policy") and (not queue_policy or queue_policy == "field"):
        blockers.append("missing_queue_policy")
    elif allowed_queue_policies and queue_policy not in allowed_queue_policies:
        blockers.append(f"queue_policy_not_allowed:{queue_policy}")
    if backpressure_policy.get("require_overload_strategy") and _blank(backpressure_spec.get("overload_strategy")):
        blockers.append("missing_overload_strategy")
    if backpressure_policy.get("require_retry_after") and _blank(backpressure_spec.get("retry_after")):
        blockers.append("missing_retry_after")
    if backpressure_policy.get("require_degrade_receipt") and _blank(backpressure_spec.get("degrade_receipt")):
        blockers.append("missing_degrade_receipt")
    backpressure_hash = "service-backpressure-policy:" + _digest(
        {
            "blockers": blockers,
            "max_inflight": max_inflight,
            "queue_policy": queue_policy,
            "service_name": service_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ServiceBackpressurePolicyPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        max_inflight=max_inflight,
        queue_policy=queue_policy,
        blockers=tuple(blockers),
        backpressure_hash=backpressure_hash,
    )


def extract_openapi_operations(
    openapi_doc: Mapping[str, Any],
    extraction_policy: Mapping[str, Any],
) -> OpenApiOperationPrimitiveSetReceipt:
    """Extract endpoint primitive candidates from a small OpenAPI document."""

    paths = openapi_doc.get("paths") if isinstance(openapi_doc.get("paths"), Mapping) else {}
    allowed_methods = {str(value).lower() for value in _as_sequence(extraction_policy.get("allowed_methods")) if str(value).strip()}
    if not allowed_methods:
        allowed_methods = {"get", "post", "put", "patch", "delete"}
    require_operation_id = bool(extraction_policy.get("require_operation_id", True))
    require_success_response = bool(extraction_policy.get("require_success_response", True))
    blockers: list[str] = []
    operations: list[JsonRecord] = []
    if not paths:
        blockers.append("missing_paths")
    for path, path_item in sorted(paths.items()):
        if not isinstance(path_item, Mapping):
            continue
        path_text = str(path)
        for method, operation in sorted(path_item.items()):
            method_text = str(method).lower()
            if method_text not in allowed_methods or not isinstance(operation, Mapping):
                continue
            operation_id = str(operation.get("operationId") or "").strip()
            if require_operation_id and not operation_id:
                blockers.append(f"{method_text.upper()} {path_text}:missing_operation_id")
                operation_id = normalize_field_name(f"{method_text}_{path_text}")
            responses = operation.get("responses") if isinstance(operation.get("responses"), Mapping) else {}
            response_codes = tuple(sorted(str(code) for code in responses.keys()))
            if require_success_response and not any(code.startswith("2") for code in response_codes):
                blockers.append(f"{method_text.upper()} {path_text}:missing_success_response")
            request_body = operation.get("requestBody") if isinstance(operation.get("requestBody"), Mapping) else {}
            operations.append({
                "operation_id": operation_id,
                "method": method_text.upper(),
                "path": path_text,
                "summary": str(operation.get("summary") or ""),
                "response_codes": response_codes,
                "has_request_body": bool(request_body),
                "visible_edge": f"HttpRequest[{operation_id}] -> HttpResponse[{operation_id}Receipt]",
            })
    if not operations:
        blockers.append("missing_operations")
    extraction_hash = "openapi-ops:" + _digest(
        {"blockers": blockers, "operations": operations},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return OpenApiOperationPrimitiveSetReceipt(
        ready=not blockers,
        operations=tuple(operations),
        blockers=tuple(blockers),
        extraction_hash=extraction_hash,
    )


def extract_asyncapi_operations(
    asyncapi_doc: Mapping[str, Any],
    extraction_policy: Mapping[str, Any],
) -> AsyncApiOperationPrimitiveSetReceipt:
    """Extract event/message primitive candidates from an AsyncAPI document."""

    channels = asyncapi_doc.get("channels") if isinstance(asyncapi_doc.get("channels"), Mapping) else {}
    allowed_actions = {str(value) for value in _as_sequence(extraction_policy.get("allowed_actions")) if str(value).strip()}
    if not allowed_actions:
        allowed_actions = {"publish", "subscribe"}
    require_message = bool(extraction_policy.get("require_message", True))
    blockers: list[str] = []
    operations: list[JsonRecord] = []
    if not channels:
        blockers.append("missing_channels")
    for channel_name, channel_spec in sorted(channels.items()):
        if not isinstance(channel_spec, Mapping):
            continue
        for action in sorted(allowed_actions):
            operation = channel_spec.get(action)
            if not isinstance(operation, Mapping):
                continue
            message = operation.get("message") if isinstance(operation.get("message"), Mapping) else {}
            message_name = str(message.get("name") or message.get("title") or operation.get("operationId") or "").strip()
            if require_message and not message:
                blockers.append(f"{channel_name}:{action}:missing_message")
            if require_message and not message_name:
                blockers.append(f"{channel_name}:{action}:missing_message_name")
            operation_id = str(operation.get("operationId") or normalize_field_name(f"{action}_{channel_name}_{message_name}"))
            operations.append({
                "operation_id": operation_id,
                "action": action,
                "channel": str(channel_name),
                "message_name": message_name,
                "visible_edge": f"AsyncMessage[{message_name or operation_id}] -> {action.title()}Receipt",
            })
    if not operations:
        blockers.append("missing_operations")
    extraction_hash = "asyncapi-ops:" + _digest(
        {"blockers": blockers, "operations": operations},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return AsyncApiOperationPrimitiveSetReceipt(
        ready=not blockers,
        operations=tuple(operations),
        channel_count=len(channels),
        blockers=tuple(blockers),
        extraction_hash=extraction_hash,
    )


def normalize_cloudevent_envelope(
    raw_event: Mapping[str, Any],
    event_policy: Mapping[str, Any],
) -> CloudEventEnvelopeReceipt:
    """Normalize an event payload into a CloudEvents-style envelope."""

    specversion = str(raw_event.get("specversion") or event_policy.get("default_specversion") or "1.0").strip()
    event_id = str(raw_event.get("id") or raw_event.get("event_id") or "").strip()
    event_type = str(raw_event.get("type") or raw_event.get("event_type") or "").strip()
    source = str(raw_event.get("source") or event_policy.get("source") or "").strip()
    data = raw_event.get("data") if "data" in raw_event else raw_event.get("payload")
    allowed_specversions = {str(value) for value in _as_sequence(event_policy.get("allowed_specversions")) if str(value).strip()}
    blockers: list[str] = []
    if not event_id:
        blockers.append("missing_id")
    if not event_type:
        blockers.append("missing_type")
    if not source:
        blockers.append("missing_source")
    if allowed_specversions and specversion not in allowed_specversions:
        blockers.append("specversion_not_allowed")
    envelope: JsonRecord = {
        "specversion": specversion,
        "id": event_id,
        "source": source,
        "type": event_type,
        "data": data,
    }
    if raw_event.get("datacontenttype"):
        envelope["datacontenttype"] = str(raw_event.get("datacontenttype"))
    for extension in _as_sequence(event_policy.get("required_extensions")):
        name = str(extension)
        value = raw_event.get(name)
        if name and _blank(value):
            blockers.append(f"missing_extension:{name}")
        elif name:
            envelope[name] = value
    idempotency_key = "cloudevent:" + _digest(
        {"id": event_id, "source": source, "type": event_type},
        chars=RECEIPT_DIGEST_CHARS,
    )
    receipt_hash = "cloudevent:" + _digest(
        {"blockers": blockers, "envelope": envelope, "idempotency_key": idempotency_key},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return CloudEventEnvelopeReceipt(
        valid=not blockers,
        event_id=event_id,
        event_type=event_type,
        source=source,
        envelope=envelope,
        blockers=tuple(blockers),
        idempotency_key=idempotency_key,
        receipt_hash=receipt_hash,
    )


def plan_serverless_function(
    function_spec: Mapping[str, Any],
    runtime_policy: Mapping[str, Any],
) -> ServerlessFunctionPlanReceipt:
    """Plan a serverless/cloud function with trigger and runtime gates."""

    function_name = str(function_spec.get("function_name") or function_spec.get("name") or "").strip()
    runtime = str(function_spec.get("runtime") or "").strip()
    handler = str(function_spec.get("handler") or "").strip()
    trigger = function_spec.get("trigger") if isinstance(function_spec.get("trigger"), Mapping) else {}
    trigger_type = str(trigger.get("type") or "").strip()
    env = function_spec.get("env") if isinstance(function_spec.get("env"), Mapping) else {}
    env_keys = tuple(sorted(str(key) for key in env.keys()))
    blockers: list[str] = []
    if not function_name:
        blockers.append("missing_function_name")
    if not runtime:
        blockers.append("missing_runtime")
    allowed_runtimes = {str(value) for value in _as_sequence(runtime_policy.get("allowed_runtimes")) if str(value).strip()}
    if runtime and allowed_runtimes and runtime not in allowed_runtimes:
        blockers.append(f"runtime_not_allowed:{runtime}")
    if not handler:
        blockers.append("missing_handler")
    if not trigger_type:
        blockers.append("missing_trigger_type")
    allowed_triggers = {str(value) for value in _as_sequence(runtime_policy.get("allowed_triggers")) if str(value).strip()}
    if trigger_type and allowed_triggers and trigger_type not in allowed_triggers:
        blockers.append(f"trigger_not_allowed:{trigger_type}")
    timeout_seconds = int(function_spec.get("timeout_seconds") or 0)
    max_timeout_seconds = int(runtime_policy.get("max_timeout_seconds") or 0)
    if max_timeout_seconds and timeout_seconds > max_timeout_seconds:
        blockers.append("timeout_exceeds_policy")
    memory_mb = int(function_spec.get("memory_mb") or 0)
    max_memory_mb = int(runtime_policy.get("max_memory_mb") or 0)
    if max_memory_mb and memory_mb > max_memory_mb:
        blockers.append("memory_exceeds_policy")
    for key in _as_sequence(runtime_policy.get("required_env")):
        env_key = str(key)
        if env_key and _blank(env.get(env_key)):
            blockers.append(f"missing_env:{env_key}")
    plan_hash = "serverless-function:" + _digest(
        {
            "blockers": blockers,
            "function_name": function_name,
            "handler": handler,
            "runtime": runtime,
            "trigger_type": trigger_type,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ServerlessFunctionPlanReceipt(
        ready=not blockers,
        function_name=function_name,
        runtime=runtime,
        handler=handler,
        trigger_type=trigger_type,
        env_keys=env_keys,
        blockers=tuple(blockers),
        plan_hash=plan_hash,
    )


def plan_observability_instrumentation(
    operation_contract: Mapping[str, Any],
    telemetry_policy: Mapping[str, Any],
) -> ObservabilityInstrumentationReceipt:
    """Plan trace, metric, log, and redaction instrumentation for an operation."""

    operation_name = str(operation_contract.get("operation_name") or operation_contract.get("name") or "").strip()
    spans = tuple(str(value) for value in _as_sequence(operation_contract.get("spans")) if str(value).strip())
    metrics = tuple(str(value) for value in _as_sequence(operation_contract.get("metrics")) if str(value).strip())
    logs = tuple(str(value) for value in _as_sequence(operation_contract.get("logs")) if str(value).strip())
    redacted_fields = tuple(str(value) for value in _as_sequence(operation_contract.get("redacted_fields")) if str(value).strip())
    blockers: list[str] = []
    if not operation_name:
        blockers.append("missing_operation_name")
    if telemetry_policy.get("require_trace_span") and not spans:
        blockers.append("missing_trace_span")
    if telemetry_policy.get("require_metric") and not metrics:
        blockers.append("missing_metric")
    if telemetry_policy.get("require_log") and not logs:
        blockers.append("missing_log")
    if telemetry_policy.get("require_trace_context") and not operation_contract.get("trace_context"):
        blockers.append("missing_trace_context")
    sensitive_fields = tuple(str(value) for value in _as_sequence(telemetry_policy.get("sensitive_fields")) if str(value).strip())
    for field in sensitive_fields:
        if field in logs and field not in redacted_fields:
            blockers.append(f"sensitive_field_not_redacted:{field}")
    instrumentation_hash = "observability:" + _digest(
        {
            "blockers": blockers,
            "metrics": metrics,
            "operation_name": operation_name,
            "spans": spans,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ObservabilityInstrumentationReceipt(
        ready=not blockers,
        operation_name=operation_name,
        spans=spans,
        metrics=metrics,
        logs=logs,
        redacted_fields=redacted_fields,
        blockers=tuple(blockers),
        instrumentation_hash=instrumentation_hash,
    )


def plan_api_contract_test_suite(
    api_operations: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    fixture_policy: Mapping[str, Any],
) -> ApiContractTestSuiteReceipt:
    """Plan API contract tests from operation contracts and examples."""

    if isinstance(api_operations, Mapping):
        operations = tuple(dict(item) for item in _as_mapping_sequence(api_operations.get("operations")))
    else:
        operations = tuple(dict(item) for item in _as_mapping_sequence(api_operations))
    blockers: list[str] = []
    test_cases: list[JsonRecord] = []
    if not operations:
        blockers.append("missing_operations")
    require_examples = bool(fixture_policy.get("require_examples", True))
    require_negative_cases = bool(fixture_policy.get("require_negative_cases", True))
    for index, operation in enumerate(operations):
        operation_id = str(operation.get("operation_id") or operation.get("operationId") or "").strip()
        method = str(operation.get("method") or "").upper()
        path = str(operation.get("path") or "").strip()
        if not operation_id:
            blockers.append(f"operation_{index + 1}_missing_operation_id")
            operation_id = f"operation_{index + 1}"
        if not method or not path:
            blockers.append(f"{operation_id}:missing_method_or_path")
        examples = tuple(_as_sequence(operation.get("examples")))
        if require_examples and not examples:
            blockers.append(f"{operation_id}:missing_examples")
        response_codes = tuple(str(value) for value in _as_sequence(operation.get("response_codes")) if str(value).strip())
        if not any(code.startswith("2") for code in response_codes):
            blockers.append(f"{operation_id}:missing_success_response")
        test_cases.append({
            "case_id": f"{operation_id}:contract",
            "method": method,
            "path": path,
            "assertions": ("request_schema", "response_schema", "error_envelope"),
        })
        if require_negative_cases:
            test_cases.append({
                "case_id": f"{operation_id}:negative",
                "method": method,
                "path": path,
                "assertions": ("invalid_request_rejected",),
            })
    suite_hash = "api-contract-suite:" + _digest(
        {"blockers": blockers, "test_cases": test_cases},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiContractTestSuiteReceipt(
        ready=not blockers,
        operation_count=len(operations),
        test_cases=tuple(test_cases),
        blockers=tuple(blockers),
        suite_hash=suite_hash,
    )


def plan_feature_flag(
    flag_spec: Mapping[str, Any],
    rollout_policy: Mapping[str, Any],
) -> FeatureFlagPlanReceipt:
    """Plan a feature flag rollout with owner, audience, and kill-switch gates."""

    flag_key = str(flag_spec.get("flag_key") or flag_spec.get("key") or "").strip()
    rollout_strategy = str(flag_spec.get("rollout_strategy") or flag_spec.get("strategy") or "off").strip()
    audiences = tuple(str(value) for value in _as_sequence(flag_spec.get("audiences")) if str(value).strip())
    blockers: list[str] = []
    if not flag_key:
        blockers.append("missing_flag_key")
    allowed_strategies = {str(value) for value in _as_sequence(rollout_policy.get("allowed_strategies")) if str(value).strip()}
    if allowed_strategies and rollout_strategy not in allowed_strategies:
        blockers.append(f"strategy_not_allowed:{rollout_strategy}")
    if rollout_policy.get("require_owner") and _blank(flag_spec.get("owner")):
        blockers.append("missing_owner")
    if rollout_policy.get("require_kill_switch") and not flag_spec.get("kill_switch"):
        blockers.append("missing_kill_switch")
    if rollout_policy.get("require_audiences") and not audiences:
        blockers.append("missing_audiences")
    percentage = float(flag_spec.get("rollout_percentage") or 0)
    max_percentage = float(rollout_policy.get("max_rollout_percentage") or 100)
    if percentage > max_percentage:
        blockers.append("rollout_percentage_exceeds_policy")
    flag_hash = "feature-flag:" + _digest(
        {
            "audiences": audiences,
            "blockers": blockers,
            "flag_key": flag_key,
            "rollout_strategy": rollout_strategy,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return FeatureFlagPlanReceipt(
        ready=not blockers,
        flag_key=flag_key,
        rollout_strategy=rollout_strategy,
        audiences=audiences,
        blockers=tuple(blockers),
        flag_hash=flag_hash,
    )


def plan_secret_rotation(
    secret_spec: Mapping[str, Any],
    rotation_policy: Mapping[str, Any],
) -> SecretRotationPlanReceipt:
    """Plan secret rotation with rollback and zero-downtime checks."""

    secret_name = str(secret_spec.get("secret_name") or secret_spec.get("name") or "").strip()
    provider = str(secret_spec.get("provider") or rotation_policy.get("provider") or "").strip()
    rotation_interval_days = int(secret_spec.get("rotation_interval_days") or rotation_policy.get("default_interval_days") or 0)
    rotation_steps = tuple(str(value) for value in _as_sequence(secret_spec.get("rotation_steps")) if str(value).strip())
    blockers: list[str] = []
    if not secret_name:
        blockers.append("missing_secret_name")
    if not provider:
        blockers.append("missing_provider")
    max_interval_days = int(rotation_policy.get("max_interval_days") or 0)
    if max_interval_days and rotation_interval_days > max_interval_days:
        blockers.append("rotation_interval_exceeds_policy")
    if rotation_interval_days <= 0:
        blockers.append("missing_rotation_interval")
    if not rotation_steps:
        blockers.append("missing_rotation_steps")
    for step in _as_sequence(rotation_policy.get("required_steps")):
        step_name = str(step)
        if step_name and step_name not in rotation_steps:
            blockers.append(f"missing_step:{step_name}")
    if rotation_policy.get("require_rollback") and not secret_spec.get("rollback"):
        blockers.append("missing_rollback")
    if rotation_policy.get("require_zero_downtime") and not secret_spec.get("dual_write"):
        blockers.append("missing_dual_write")
    rotation_hash = "secret-rotation:" + _digest(
        {
            "blockers": blockers,
            "provider": provider,
            "rotation_interval_days": rotation_interval_days,
            "rotation_steps": rotation_steps,
            "secret_name": secret_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SecretRotationPlanReceipt(
        ready=not blockers,
        secret_name=secret_name,
        provider=provider,
        rotation_interval_days=rotation_interval_days,
        rotation_steps=rotation_steps,
        blockers=tuple(blockers),
        rotation_hash=rotation_hash,
    )


def compile_agent_tool_schema_from_openapi(
    operation_contract: Mapping[str, Any],
    tool_policy: Mapping[str, Any],
) -> AgentToolSchemaReceipt:
    """Compile an agent-callable tool schema from an API operation contract."""

    operation_id = str(operation_contract.get("operation_id") or operation_contract.get("operationId") or "").strip()
    method = str(operation_contract.get("method") or "").upper()
    path = str(operation_contract.get("path") or "").strip()
    request_schema = operation_contract.get("request_schema") if isinstance(operation_contract.get("request_schema"), Mapping) else {}
    properties = request_schema.get("properties") if isinstance(request_schema.get("properties"), Mapping) else {}
    parameters = tuple(sorted(str(key) for key in properties.keys()))
    required_scopes = tuple(str(value) for value in _as_sequence(operation_contract.get("required_scopes")) if str(value).strip())
    tool_name = normalize_field_name(tool_policy.get("tool_name") or operation_id)
    blockers: list[str] = []
    if not operation_id:
        blockers.append("missing_operation_id")
    if not method:
        blockers.append("missing_method")
    allowed_methods = {str(value).upper() for value in _as_sequence(tool_policy.get("allowed_methods")) if str(value).strip()}
    if method and allowed_methods and method not in allowed_methods:
        blockers.append(f"method_not_allowed:{method}")
    if not path:
        blockers.append("missing_path")
    if not parameters and tool_policy.get("require_parameters"):
        blockers.append("missing_parameters")
    max_parameters = int(tool_policy.get("max_parameters") or 0)
    if max_parameters and len(parameters) > max_parameters:
        blockers.append("too_many_parameters")
    if tool_policy.get("require_scopes") and not required_scopes:
        blockers.append("missing_required_scopes")
    forbidden_prefixes = tuple(str(value) for value in _as_sequence(tool_policy.get("forbidden_path_prefixes")) if str(value).strip())
    if path and forbidden_prefixes and any(path.startswith(prefix) for prefix in forbidden_prefixes):
        blockers.append("path_prefix_forbidden")
    schema_hash = "agent-tool-schema:" + _digest(
        {
            "blockers": blockers,
            "method": method,
            "parameters": parameters,
            "path": path,
            "required_scopes": required_scopes,
            "tool_name": tool_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return AgentToolSchemaReceipt(
        ready=not blockers,
        tool_name=tool_name,
        method=method,
        path=path,
        parameters=parameters,
        required_scopes=required_scopes,
        blockers=tuple(blockers),
        schema_hash=schema_hash,
    )


def plan_sdk_package(
    api_spec: Mapping[str, Any],
    sdk_policy: Mapping[str, Any],
) -> SdkPackagePlanReceipt:
    """Plan an SDK package from API operations without generating files."""

    package_name = normalize_field_name(api_spec.get("package_name") or api_spec.get("name") or "")
    language = str(sdk_policy.get("language") or api_spec.get("language") or "").strip()
    operations = tuple(
        str(item.get("operation_id") or item.get("operationId") or item.get("name") or "").strip()
        for item in _as_mapping_sequence(api_spec.get("operations"))
        if str(item.get("operation_id") or item.get("operationId") or item.get("name") or "").strip()
    )
    auth_strategy = str(api_spec.get("auth_strategy") or sdk_policy.get("auth_strategy") or "").strip()
    blockers: list[str] = []
    if not package_name:
        blockers.append("missing_package_name")
    if not language:
        blockers.append("missing_language")
    allowed_languages = {str(value) for value in _as_sequence(sdk_policy.get("allowed_languages")) if str(value).strip()}
    if language and allowed_languages and language not in allowed_languages:
        blockers.append(f"language_not_allowed:{language}")
    if not operations:
        blockers.append("missing_operations")
    if sdk_policy.get("require_auth_strategy") and not auth_strategy:
        blockers.append("missing_auth_strategy")
    if sdk_policy.get("require_tests") and not api_spec.get("tests"):
        blockers.append("missing_tests")
    if sdk_policy.get("require_retry_policy") and not api_spec.get("retry_policy"):
        blockers.append("missing_retry_policy")
    package_hash = "sdk-package:" + _digest(
        {
            "auth_strategy": auth_strategy,
            "blockers": blockers,
            "language": language,
            "operations": operations,
            "package_name": package_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SdkPackagePlanReceipt(
        ready=not blockers,
        package_name=package_name,
        language=language,
        operations=operations,
        auth_strategy=auth_strategy,
        blockers=tuple(blockers),
        package_hash=package_hash,
    )


def plan_dockerfile(
    app_spec: Mapping[str, Any],
    container_policy: Mapping[str, Any],
) -> DockerfilePlanReceipt:
    """Plan a Dockerfile with base-image and runtime safety checks."""

    base_image = str(app_spec.get("base_image") or "").strip()
    workdir = str(app_spec.get("workdir") or "/app").strip()
    command = tuple(str(value) for value in _as_sequence(app_spec.get("command")) if str(value).strip())
    exposed_ports = tuple(int(value) for value in _as_sequence(app_spec.get("exposed_ports")) if str(value).strip())
    blockers: list[str] = []
    if not base_image:
        blockers.append("missing_base_image")
    if container_policy.get("require_pinned_base_image") and base_image and (":" not in base_image or base_image.endswith(":latest")):
        blockers.append("base_image_not_pinned")
    allowed_base_prefixes = tuple(str(value) for value in _as_sequence(container_policy.get("allowed_base_prefixes")) if str(value).strip())
    if base_image and allowed_base_prefixes and not any(base_image.startswith(prefix) for prefix in allowed_base_prefixes):
        blockers.append("base_image_not_allowed")
    if not command:
        blockers.append("missing_command")
    if container_policy.get("require_non_root_user") and not app_spec.get("user"):
        blockers.append("missing_non_root_user")
    if container_policy.get("require_healthcheck") and not app_spec.get("healthcheck"):
        blockers.append("missing_healthcheck")
    if container_policy.get("require_exposed_port") and not exposed_ports:
        blockers.append("missing_exposed_port")
    dockerfile_hash = "dockerfile:" + _digest(
        {
            "base_image": base_image,
            "blockers": blockers,
            "command": command,
            "exposed_ports": exposed_ports,
            "workdir": workdir,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DockerfilePlanReceipt(
        ready=not blockers,
        base_image=base_image,
        workdir=workdir,
        exposed_ports=exposed_ports,
        blockers=tuple(blockers),
        dockerfile_hash=dockerfile_hash,
    )


def plan_docker_compose_stack(
    stack_spec: Mapping[str, Any],
    compose_policy: Mapping[str, Any],
) -> DockerComposePlanReceipt:
    """Plan a Docker Compose stack with service and secret gates."""

    services_map = stack_spec.get("services") if isinstance(stack_spec.get("services"), Mapping) else {}
    service_names = tuple(sorted(str(name) for name in services_map.keys()))
    network_names = tuple(sorted(str(value) for value in _as_sequence(stack_spec.get("networks")) if str(value).strip()))
    volume_names = tuple(sorted(str(value) for value in _as_sequence(stack_spec.get("volumes")) if str(value).strip()))
    blockers: list[str] = []
    if not service_names:
        blockers.append("missing_services")
    for service_name, service in sorted(services_map.items()):
        service_map = service if isinstance(service, Mapping) else {}
        if compose_policy.get("require_images") and _blank(service_map.get("image")) and _blank(service_map.get("build")):
            blockers.append(f"{service_name}:missing_image_or_build")
        if compose_policy.get("require_healthchecks") and not service_map.get("healthcheck"):
            blockers.append(f"{service_name}:missing_healthcheck")
        if compose_policy.get("require_secret_refs"):
            env = service_map.get("environment") if isinstance(service_map.get("environment"), Mapping) else {}
            for key, value in env.items():
                if str(key).endswith(("PASSWORD", "TOKEN", "SECRET", "KEY")) and not _valid_secret_ref(value):
                    blockers.append(f"{service_name}:inline_secret:{key}")
    required_services = tuple(str(value) for value in _as_sequence(compose_policy.get("required_services")) if str(value).strip())
    for service in required_services:
        if service not in service_names:
            blockers.append(f"missing_service:{service}")
    compose_hash = "docker-compose:" + _digest(
        {
            "blockers": blockers,
            "networks": network_names,
            "services": service_names,
            "volumes": volume_names,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DockerComposePlanReceipt(
        ready=not blockers,
        service_names=service_names,
        network_names=network_names,
        volume_names=volume_names,
        blockers=tuple(blockers),
        compose_hash=compose_hash,
    )


def plan_helm_chart(
    chart_spec: Mapping[str, Any],
    helm_policy: Mapping[str, Any],
) -> HelmChartPlanReceipt:
    """Plan a Helm chart with template, values, and workload policy checks."""

    chart_name = normalize_field_name(chart_spec.get("chart_name") or chart_spec.get("name") or "")
    templates = tuple(str(value) for value in _as_sequence(chart_spec.get("templates")) if str(value).strip())
    values = dict(chart_spec.get("values") if isinstance(chart_spec.get("values"), Mapping) else {})
    blockers: list[str] = []
    if not chart_name:
        blockers.append("missing_chart_name")
    if not templates:
        blockers.append("missing_templates")
    for template in _as_sequence(helm_policy.get("required_templates")):
        name = str(template)
        if name and name not in templates:
            blockers.append(f"missing_template:{name}")
    if helm_policy.get("require_resources"):
        resources = values.get("resources") if isinstance(values.get("resources"), Mapping) else {}
        if not resources.get("limits") or not resources.get("requests"):
            blockers.append("missing_resource_requests_or_limits")
    if helm_policy.get("require_probes"):
        if not values.get("readinessProbe") or not values.get("livenessProbe"):
            blockers.append("missing_probes")
    if helm_policy.get("forbid_latest_image"):
        image = values.get("image") if isinstance(values.get("image"), Mapping) else {}
        tag = str(image.get("tag") or "")
        if not tag or tag == "latest":
            blockers.append("image_tag_not_pinned")
    chart_hash = "helm-chart:" + _digest(
        {"blockers": blockers, "chart_name": chart_name, "templates": templates, "values": values},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return HelmChartPlanReceipt(
        ready=not blockers,
        chart_name=chart_name,
        templates=templates,
        values=values,
        blockers=tuple(blockers),
        chart_hash=chart_hash,
    )


def plan_rbac_policy_matrix(
    access_matrix: Mapping[str, Any],
    rbac_policy: Mapping[str, Any],
) -> RbacPolicyPlanReceipt:
    """Plan RBAC role/action bindings with least-privilege blockers."""

    roles = tuple(str(value) for value in _as_sequence(access_matrix.get("roles")) if str(value).strip())
    actions = tuple(str(value) for value in _as_sequence(access_matrix.get("actions")) if str(value).strip())
    bindings = tuple(dict(item) for item in _as_mapping_sequence(access_matrix.get("bindings")))
    blockers: list[str] = []
    if not roles:
        blockers.append("missing_roles")
    if not actions:
        blockers.append("missing_actions")
    if not bindings:
        blockers.append("missing_bindings")
    role_set = set(roles)
    action_set = set(actions)
    for index, binding in enumerate(bindings):
        role = str(binding.get("role") or "")
        bound_actions = tuple(str(value) for value in _as_sequence(binding.get("actions")) if str(value).strip())
        if role not in role_set:
            blockers.append(f"binding_{index + 1}_unknown_role")
        for action in bound_actions:
            if action == "*" and rbac_policy.get("forbid_wildcards"):
                blockers.append(f"{role}:wildcard_action_forbidden")
            elif action not in action_set and action != "*":
                blockers.append(f"{role}:unknown_action:{action}")
        if rbac_policy.get("require_reason") and _blank(binding.get("reason")):
            blockers.append(f"{role}:missing_reason")
    policy_hash = "rbac-policy:" + _digest(
        {"actions": actions, "bindings": bindings, "blockers": blockers, "roles": roles},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return RbacPolicyPlanReceipt(
        ready=not blockers,
        roles=roles,
        actions=actions,
        bindings=bindings,
        blockers=tuple(blockers),
        policy_hash=policy_hash,
    )


def plan_pii_redaction_policy(
    data_schema: Mapping[str, Any],
    redaction_policy: Mapping[str, Any],
) -> PiiRedactionPlanReceipt:
    """Plan PII redaction coverage for schema fields."""

    fields = data_schema.get("fields") if isinstance(data_schema.get("fields"), Mapping) else {}
    sensitive_fields = tuple(str(value) for value in _as_sequence(redaction_policy.get("sensitive_fields")) if str(value).strip())
    redaction_map = dict(redaction_policy.get("redaction_map") if isinstance(redaction_policy.get("redaction_map"), Mapping) else {})
    allowed_methods = {str(value) for value in _as_sequence(redaction_policy.get("allowed_methods")) if str(value).strip()}
    blockers: list[str] = []
    if not fields:
        blockers.append("missing_schema_fields")
    if not sensitive_fields:
        blockers.append("missing_sensitive_fields")
    unprotected_fields: list[str] = []
    for field in sensitive_fields:
        if field not in fields:
            blockers.append(f"sensitive_field_not_in_schema:{field}")
        method = str(redaction_map.get(field) or "")
        if not method:
            unprotected_fields.append(field)
        elif allowed_methods and method not in allowed_methods:
            blockers.append(f"redaction_method_not_allowed:{field}")
    if unprotected_fields:
        blockers.append("unprotected_sensitive_fields")
    policy_hash = "pii-redaction:" + _digest(
        {
            "blockers": blockers,
            "redaction_map": redaction_map,
            "sensitive_fields": sensitive_fields,
            "unprotected_fields": unprotected_fields,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PiiRedactionPlanReceipt(
        ready=not blockers,
        sensitive_fields=sensitive_fields,
        redaction_map=redaction_map,
        unprotected_fields=tuple(unprotected_fields),
        blockers=tuple(blockers),
        policy_hash=policy_hash,
    )


def plan_connector_auth_binding(
    connector_spec: Mapping[str, Any],
    auth_policy: Mapping[str, Any],
) -> ConnectorAuthBindingReceipt:
    """Plan auth bindings for an integration connector without reading secrets."""

    connector_name = normalize_field_name(connector_spec.get("connector_name") or connector_spec.get("name") or "")
    source_system = str(connector_spec.get("source_system") or "").strip()
    target_system = str(connector_spec.get("target_system") or "").strip()
    auth_bindings = tuple(dict(item) for item in _as_mapping_sequence(connector_spec.get("auth_bindings")))
    blockers: list[str] = []
    if not connector_name:
        blockers.append("missing_connector_name")
    if not source_system:
        blockers.append("missing_source_system")
    if not target_system:
        blockers.append("missing_target_system")
    if not auth_bindings:
        blockers.append("missing_auth_bindings")
    allowed_auth_types = {str(value) for value in _as_sequence(auth_policy.get("allowed_auth_types")) if str(value).strip()}
    for index, binding in enumerate(auth_bindings):
        auth_type = str(binding.get("auth_type") or "").strip()
        if not auth_type:
            blockers.append(f"binding_{index + 1}_missing_auth_type")
        elif allowed_auth_types and auth_type not in allowed_auth_types:
            blockers.append(f"auth_type_not_allowed:{auth_type}")
        if auth_policy.get("require_secret_refs") and not _valid_secret_ref(binding.get("secret_ref")):
            blockers.append(f"binding_{index + 1}_missing_secret_ref")
        scopes = tuple(str(value) for value in _as_sequence(binding.get("scopes")) if str(value).strip())
        required_scopes = tuple(str(value) for value in _as_sequence(auth_policy.get("required_scopes")) if str(value).strip())
        for scope in required_scopes:
            if scope not in scopes:
                blockers.append(f"binding_{index + 1}_missing_scope:{scope}")
        if auth_policy.get("require_rotation") and not binding.get("rotation"):
            blockers.append(f"binding_{index + 1}_missing_rotation")
    binding_hash = "connector-auth:" + _digest(
        {
            "auth_bindings": auth_bindings,
            "blockers": blockers,
            "connector_name": connector_name,
            "source_system": source_system,
            "target_system": target_system,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ConnectorAuthBindingReceipt(
        ready=not blockers,
        connector_name=connector_name,
        source_system=source_system,
        target_system=target_system,
        auth_bindings=auth_bindings,
        blockers=tuple(blockers),
        binding_hash=binding_hash,
    )


def plan_idempotency_policy(
    operation_contract: Mapping[str, Any],
    idempotency_policy: Mapping[str, Any],
) -> IdempotencyPolicyPlanReceipt:
    """Plan idempotency behavior for an API, worker, or workflow operation."""

    operation_name = normalize_field_name(operation_contract.get("operation_name") or operation_contract.get("operation_id") or "")
    key_fields = tuple(str(value) for value in _as_sequence(operation_contract.get("key_fields")) if str(value).strip())
    ttl_seconds = int(operation_contract.get("ttl_seconds") or idempotency_policy.get("default_ttl_seconds") or 0)
    store_name = str(operation_contract.get("store_name") or idempotency_policy.get("store_name") or "").strip()
    replay_strategy = str(operation_contract.get("replay_strategy") or idempotency_policy.get("replay_strategy") or "").strip()
    blockers: list[str] = []
    if not operation_name:
        blockers.append("missing_operation_name")
    if not key_fields:
        blockers.append("missing_key_fields")
    if idempotency_policy.get("require_tenant_key") and "tenant_id" not in key_fields:
        blockers.append("missing_tenant_key")
    if ttl_seconds <= 0:
        blockers.append("missing_ttl_seconds")
    max_ttl_seconds = int(idempotency_policy.get("max_ttl_seconds") or 0)
    if max_ttl_seconds and ttl_seconds > max_ttl_seconds:
        blockers.append("ttl_exceeds_policy")
    if not store_name:
        blockers.append("missing_store_name")
    if idempotency_policy.get("require_replay_strategy") and not replay_strategy:
        blockers.append("missing_replay_strategy")
    if idempotency_policy.get("require_conflict_response") and not operation_contract.get("conflict_response"):
        blockers.append("missing_conflict_response")
    policy_hash = "idempotency-policy:" + _digest(
        {
            "blockers": blockers,
            "key_fields": key_fields,
            "operation_name": operation_name,
            "replay_strategy": replay_strategy,
            "store_name": store_name,
            "ttl_seconds": ttl_seconds,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return IdempotencyPolicyPlanReceipt(
        ready=not blockers,
        operation_name=operation_name,
        key_fields=key_fields,
        ttl_seconds=ttl_seconds,
        store_name=store_name,
        blockers=tuple(blockers),
        policy_hash=policy_hash,
    )


def plan_pagination_contract(
    resource_contract: Mapping[str, Any],
    pagination_policy: Mapping[str, Any],
) -> PaginationContractPlanReceipt:
    """Plan a list/query pagination contract with stable ordering checks."""

    resource_name = normalize_field_name(resource_contract.get("resource_name") or resource_contract.get("name") or "")
    mode = str(resource_contract.get("mode") or pagination_policy.get("default_mode") or "").strip()
    default_limit = int(resource_contract.get("default_limit") or pagination_policy.get("default_limit") or 0)
    max_limit = int(resource_contract.get("max_limit") or pagination_policy.get("max_limit") or 0)
    sort_fields = tuple(str(value) for value in _as_sequence(resource_contract.get("sort_fields")) if str(value).strip())
    cursor_fields = tuple(str(value) for value in _as_sequence(resource_contract.get("cursor_fields")) if str(value).strip())
    blockers: list[str] = []
    if not resource_name:
        blockers.append("missing_resource_name")
    allowed_modes = {str(value) for value in _as_sequence(pagination_policy.get("allowed_modes")) if str(value).strip()}
    if not mode:
        blockers.append("missing_pagination_mode")
    elif allowed_modes and mode not in allowed_modes:
        blockers.append(f"pagination_mode_not_allowed:{mode}")
    if default_limit <= 0:
        blockers.append("missing_default_limit")
    if max_limit <= 0:
        blockers.append("missing_max_limit")
    if default_limit and max_limit and default_limit > max_limit:
        blockers.append("default_limit_exceeds_max")
    absolute_max_limit = int(pagination_policy.get("absolute_max_limit") or 0)
    if absolute_max_limit and max_limit > absolute_max_limit:
        blockers.append("max_limit_exceeds_policy")
    if pagination_policy.get("require_stable_sort") and not sort_fields:
        blockers.append("missing_stable_sort")
    if mode == "cursor" and pagination_policy.get("require_cursor_fields") and not cursor_fields:
        blockers.append("missing_cursor_fields")
    contract_hash = "pagination-contract:" + _digest(
        {
            "blockers": blockers,
            "cursor_fields": cursor_fields,
            "default_limit": default_limit,
            "max_limit": max_limit,
            "mode": mode,
            "resource_name": resource_name,
            "sort_fields": sort_fields,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PaginationContractPlanReceipt(
        ready=not blockers,
        resource_name=resource_name,
        mode=mode,
        default_limit=default_limit,
        max_limit=max_limit,
        blockers=tuple(blockers),
        contract_hash=contract_hash,
    )


def plan_cors_security_headers(
    endpoint_surface: Mapping[str, Any],
    header_policy: Mapping[str, Any],
) -> CorsSecurityHeadersPlanReceipt:
    """Plan CORS and common HTTP security headers for API endpoints."""

    allowed_origins = tuple(str(value) for value in _as_sequence(endpoint_surface.get("allowed_origins")) if str(value).strip())
    allowed_methods = tuple(str(value).upper() for value in _as_sequence(endpoint_surface.get("allowed_methods")) if str(value).strip())
    security_headers = dict(endpoint_surface.get("security_headers") if isinstance(endpoint_surface.get("security_headers"), Mapping) else {})
    blockers: list[str] = []
    if not allowed_origins:
        blockers.append("missing_allowed_origins")
    if header_policy.get("forbid_wildcard_origin") and "*" in allowed_origins:
        blockers.append("wildcard_origin_forbidden")
    required_methods = tuple(str(value).upper() for value in _as_sequence(header_policy.get("required_methods")) if str(value).strip())
    for method in required_methods:
        if method not in allowed_methods:
            blockers.append(f"missing_method:{method}")
    allowed_method_set = {str(value).upper() for value in _as_sequence(header_policy.get("allowed_methods")) if str(value).strip()}
    for method in allowed_methods:
        if allowed_method_set and method not in allowed_method_set:
            blockers.append(f"method_not_allowed:{method}")
    for header in _as_sequence(header_policy.get("required_headers")):
        header_name = str(header)
        if header_name and header_name not in security_headers:
            blockers.append(f"missing_header:{header_name}")
    if header_policy.get("require_credentials_policy") and "Access-Control-Allow-Credentials" not in security_headers:
        blockers.append("missing_credentials_policy")
    headers_hash = "cors-security-headers:" + _digest(
        {
            "allowed_methods": allowed_methods,
            "allowed_origins": allowed_origins,
            "blockers": blockers,
            "security_headers": security_headers,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return CorsSecurityHeadersPlanReceipt(
        ready=not blockers,
        allowed_origins=allowed_origins,
        allowed_methods=allowed_methods,
        security_headers=security_headers,
        blockers=tuple(blockers),
        headers_hash=headers_hash,
    )


def plan_audit_log_policy(
    event_contract: Mapping[str, Any],
    audit_policy: Mapping[str, Any],
) -> AuditLogPolicyPlanReceipt:
    """Plan audit logging fields, retention, and tamper-evidence requirements."""

    event_name = normalize_field_name(event_contract.get("event_name") or event_contract.get("name") or "")
    emitted_fields = {str(value) for value in _as_sequence(event_contract.get("emitted_fields")) if str(value).strip()}
    required_fields = tuple(str(value) for value in _as_sequence(audit_policy.get("required_fields")) if str(value).strip())
    retention_days = int(event_contract.get("retention_days") or audit_policy.get("default_retention_days") or 0)
    blockers: list[str] = []
    if not event_name:
        blockers.append("missing_event_name")
    if not emitted_fields:
        blockers.append("missing_emitted_fields")
    for field in required_fields:
        if field not in emitted_fields:
            blockers.append(f"missing_required_field:{field}")
    min_retention_days = int(audit_policy.get("min_retention_days") or 0)
    if retention_days <= 0:
        blockers.append("missing_retention_days")
    elif min_retention_days and retention_days < min_retention_days:
        blockers.append("retention_below_policy")
    if audit_policy.get("require_reason_code") and "reason_code" not in emitted_fields:
        blockers.append("missing_reason_code")
    if audit_policy.get("require_tamper_evidence") and not event_contract.get("tamper_evidence"):
        blockers.append("missing_tamper_evidence")
    if audit_policy.get("require_trace_id") and "trace_id" not in emitted_fields:
        blockers.append("missing_trace_id")
    policy_hash = "audit-log-policy:" + _digest(
        {
            "blockers": blockers,
            "emitted_fields": sorted(emitted_fields),
            "event_name": event_name,
            "required_fields": required_fields,
            "retention_days": retention_days,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return AuditLogPolicyPlanReceipt(
        ready=not blockers,
        event_name=event_name,
        required_fields=required_fields,
        retention_days=retention_days,
        blockers=tuple(blockers),
        policy_hash=policy_hash,
    )


def plan_tenant_isolation(
    resource_contract: Mapping[str, Any],
    isolation_policy: Mapping[str, Any],
) -> TenantIsolationPlanReceipt:
    """Plan tenant isolation checks for storage, auth context, and queries."""

    resource_name = normalize_field_name(resource_contract.get("resource_name") or resource_contract.get("name") or "")
    tenant_key = str(resource_contract.get("tenant_key") or isolation_policy.get("tenant_key") or "").strip()
    isolation_mode = str(resource_contract.get("isolation_mode") or isolation_policy.get("default_mode") or "").strip()
    query_filters = tuple(str(value) for value in _as_sequence(resource_contract.get("query_filters")) if str(value).strip())
    blockers: list[str] = []
    if not resource_name:
        blockers.append("missing_resource_name")
    if not tenant_key:
        blockers.append("missing_tenant_key")
    allowed_modes = {str(value) for value in _as_sequence(isolation_policy.get("allowed_modes")) if str(value).strip()}
    if not isolation_mode:
        blockers.append("missing_isolation_mode")
    elif allowed_modes and isolation_mode not in allowed_modes:
        blockers.append(f"isolation_mode_not_allowed:{isolation_mode}")
    if isolation_policy.get("require_auth_context") and not resource_contract.get("auth_context"):
        blockers.append("missing_auth_context")
    if isolation_policy.get("require_query_filter") and tenant_key and tenant_key not in query_filters:
        blockers.append("missing_tenant_query_filter")
    if isolation_policy.get("require_storage_scope") and not resource_contract.get("storage_scope"):
        blockers.append("missing_storage_scope")
    if isolation_policy.get("require_negative_tests") and not resource_contract.get("negative_tests"):
        blockers.append("missing_negative_tests")
    isolation_hash = "tenant-isolation:" + _digest(
        {
            "blockers": blockers,
            "isolation_mode": isolation_mode,
            "query_filters": query_filters,
            "resource_name": resource_name,
            "tenant_key": tenant_key,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return TenantIsolationPlanReceipt(
        ready=not blockers,
        resource_name=resource_name,
        tenant_key=tenant_key,
        isolation_mode=isolation_mode,
        blockers=tuple(blockers),
        isolation_hash=isolation_hash,
    )


def evaluate_event_schema_compatibility(
    previous_schema: Mapping[str, Any],
    next_schema: Mapping[str, Any],
    compatibility_policy: Mapping[str, Any],
) -> EventSchemaCompatibilityReceipt:
    """Evaluate schema compatibility for event evolution."""

    event_type = str(next_schema.get("event_type") or previous_schema.get("event_type") or "").strip()
    previous_fields = previous_schema.get("fields") if isinstance(previous_schema.get("fields"), Mapping) else {}
    next_fields = next_schema.get("fields") if isinstance(next_schema.get("fields"), Mapping) else {}
    previous_required = {str(value) for value in _as_sequence(previous_schema.get("required")) if str(value).strip()}
    next_required = {str(value) for value in _as_sequence(next_schema.get("required")) if str(value).strip()}
    previous_names = set(str(key) for key in previous_fields.keys())
    next_names = set(str(key) for key in next_fields.keys())
    added_fields = tuple(sorted(next_names - previous_names))
    removed_fields = tuple(sorted(previous_names - next_names))
    changed_fields = tuple(sorted(
        field
        for field in previous_names & next_names
        if previous_fields.get(field) != next_fields.get(field)
    ))
    blockers: list[str] = []
    if not event_type:
        blockers.append("missing_event_type")
    if not previous_fields:
        blockers.append("missing_previous_fields")
    if not next_fields:
        blockers.append("missing_next_fields")
    if removed_fields and compatibility_policy.get("forbid_removed_fields", True):
        blockers.append("removed_fields")
    if changed_fields and compatibility_policy.get("forbid_changed_fields", True):
        blockers.append("changed_fields")
    newly_required = tuple(sorted(next_required - previous_required))
    if newly_required and compatibility_policy.get("forbid_new_required_fields", True):
        blockers.append("new_required_fields")
    if compatibility_policy.get("require_version_bump") and previous_schema.get("version") == next_schema.get("version"):
        blockers.append("missing_version_bump")
    compatibility_hash = "event-schema-compatibility:" + _digest(
        {
            "added_fields": added_fields,
            "blockers": blockers,
            "changed_fields": changed_fields,
            "event_type": event_type,
            "newly_required": newly_required,
            "removed_fields": removed_fields,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return EventSchemaCompatibilityReceipt(
        compatible=not blockers,
        event_type=event_type,
        added_fields=added_fields,
        removed_fields=removed_fields,
        changed_fields=changed_fields,
        blockers=tuple(blockers),
        compatibility_hash=compatibility_hash,
    )


def plan_dead_letter_replay(
    dlq_spec: Mapping[str, Any],
    replay_policy: Mapping[str, Any],
) -> DeadLetterReplayPlanReceipt:
    """Plan dead-letter queue replay with dedupe, throttle, and audit checks."""

    queue_name = str(dlq_spec.get("queue_name") or dlq_spec.get("name") or "").strip()
    replay_batch_size = int(dlq_spec.get("replay_batch_size") or replay_policy.get("default_batch_size") or 0)
    max_retries = int(dlq_spec.get("max_retries") or replay_policy.get("max_retries") or 0)
    blockers: list[str] = []
    if not queue_name:
        blockers.append("missing_queue_name")
    if replay_batch_size <= 0:
        blockers.append("missing_replay_batch_size")
    max_batch_size = int(replay_policy.get("max_batch_size") or 0)
    if max_batch_size and replay_batch_size > max_batch_size:
        blockers.append("replay_batch_size_exceeds_policy")
    if max_retries <= 0:
        blockers.append("missing_max_retries")
    if replay_policy.get("require_dedupe_key") and not dlq_spec.get("dedupe_key"):
        blockers.append("missing_dedupe_key")
    if replay_policy.get("require_poison_message_quarantine") and not dlq_spec.get("poison_message_quarantine"):
        blockers.append("missing_poison_message_quarantine")
    if replay_policy.get("require_audit_receipt") and not dlq_spec.get("audit_receipt"):
        blockers.append("missing_audit_receipt")
    if replay_policy.get("require_throttle") and not dlq_spec.get("throttle"):
        blockers.append("missing_throttle")
    replay_hash = "dead-letter-replay:" + _digest(
        {
            "blockers": blockers,
            "max_retries": max_retries,
            "queue_name": queue_name,
            "replay_batch_size": replay_batch_size,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DeadLetterReplayPlanReceipt(
        ready=not blockers,
        queue_name=queue_name,
        replay_batch_size=replay_batch_size,
        max_retries=max_retries,
        blockers=tuple(blockers),
        replay_hash=replay_hash,
    )


def plan_cache_invalidation(
    cache_contract: Mapping[str, Any],
    cache_policy: Mapping[str, Any],
) -> CacheInvalidationPlanReceipt:
    """Plan cache invalidation keys, triggers, TTLs, and stale-read safeguards."""

    cache_name = normalize_field_name(cache_contract.get("cache_name") or cache_contract.get("name") or "")
    key_patterns = tuple(str(value) for value in _as_sequence(cache_contract.get("key_patterns")) if str(value).strip())
    triggers = tuple(str(value) for value in _as_sequence(cache_contract.get("triggers")) if str(value).strip())
    ttl_seconds = int(cache_contract.get("ttl_seconds") or cache_policy.get("default_ttl_seconds") or 0)
    blockers: list[str] = []
    if not cache_name:
        blockers.append("missing_cache_name")
    if not key_patterns:
        blockers.append("missing_key_patterns")
    if not triggers:
        blockers.append("missing_invalidation_triggers")
    if ttl_seconds <= 0:
        blockers.append("missing_ttl_seconds")
    max_ttl_seconds = int(cache_policy.get("max_ttl_seconds") or 0)
    if max_ttl_seconds and ttl_seconds > max_ttl_seconds:
        blockers.append("ttl_exceeds_policy")
    if cache_policy.get("require_namespace") and not cache_contract.get("namespace"):
        blockers.append("missing_namespace")
    if cache_policy.get("require_stale_read_strategy") and not cache_contract.get("stale_read_strategy"):
        blockers.append("missing_stale_read_strategy")
    if cache_policy.get("require_observability") and not cache_contract.get("metrics"):
        blockers.append("missing_cache_metrics")
    invalidation_hash = "cache-invalidation:" + _digest(
        {
            "blockers": blockers,
            "cache_name": cache_name,
            "key_patterns": key_patterns,
            "triggers": triggers,
            "ttl_seconds": ttl_seconds,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return CacheInvalidationPlanReceipt(
        ready=not blockers,
        cache_name=cache_name,
        key_patterns=key_patterns,
        triggers=triggers,
        ttl_seconds=ttl_seconds,
        blockers=tuple(blockers),
        invalidation_hash=invalidation_hash,
    )


def plan_document_chunking(
    document_batch: Sequence[Mapping[str, Any]],
    chunking_policy: Mapping[str, Any],
) -> DocumentChunkingPlanReceipt:
    """Plan deterministic document chunking with size and metadata checks."""

    documents = tuple(dict(item) for item in document_batch)
    chunk_chars = int(chunking_policy.get("chunk_chars") or 0)
    overlap_chars = int(chunking_policy.get("overlap_chars") or 0)
    blockers: list[str] = []
    if not documents:
        blockers.append("missing_documents")
    if chunk_chars <= 0:
        blockers.append("missing_chunk_chars")
    if overlap_chars < 0:
        blockers.append("negative_overlap")
    if chunk_chars > 0 and overlap_chars >= chunk_chars:
        blockers.append("overlap_exceeds_chunk")
    max_chunk_chars = int(chunking_policy.get("max_chunk_chars") or 0)
    if max_chunk_chars and chunk_chars > max_chunk_chars:
        blockers.append("chunk_chars_exceeds_policy")
    chunk_count = 0
    step = max(1, chunk_chars - max(0, overlap_chars)) if chunk_chars > 0 else 1
    for index, document in enumerate(documents):
        text = str(document.get("text") or document.get("content") or "")
        if not text:
            blockers.append(f"document_{index + 1}_missing_text")
            continue
        if chunking_policy.get("require_document_id") and _blank(document.get("id")):
            blockers.append(f"document_{index + 1}_missing_id")
        if chunking_policy.get("require_metadata") and not isinstance(document.get("metadata"), Mapping):
            blockers.append(f"document_{index + 1}_missing_metadata")
        chunk_count += max(1, (max(0, len(text) - overlap_chars) + step - 1) // step)
    plan_hash = "document-chunking:" + _digest(
        {
            "blockers": blockers,
            "chunk_chars": chunk_chars,
            "chunk_count": chunk_count,
            "document_count": len(documents),
            "overlap_chars": overlap_chars,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DocumentChunkingPlanReceipt(
        ready=not blockers,
        document_count=len(documents),
        chunk_count=chunk_count,
        chunk_chars=chunk_chars,
        overlap_chars=overlap_chars,
        blockers=tuple(blockers),
        plan_hash=plan_hash,
    )


def plan_retrieval_rerank_policy(
    retrieval_spec: Mapping[str, Any],
    retrieval_policy: Mapping[str, Any],
) -> RetrievalRerankPlanReceipt:
    """Plan retrieval and reranking with top-k and source-diversity gates."""

    retrievers = tuple(dict(item) for item in _as_mapping_sequence(retrieval_spec.get("retrievers")))
    retriever_names = tuple(str(item.get("name") or item.get("source") or "").strip() for item in retrievers if str(item.get("name") or item.get("source") or "").strip())
    top_k = int(retrieval_spec.get("top_k") or retrieval_policy.get("default_top_k") or 0)
    reranker_model = str(retrieval_spec.get("reranker_model") or retrieval_policy.get("reranker_model") or "").strip()
    blockers: list[str] = []
    if not retriever_names:
        blockers.append("missing_retrievers")
    if top_k <= 0:
        blockers.append("missing_top_k")
    max_top_k = int(retrieval_policy.get("max_top_k") or 0)
    if max_top_k and top_k > max_top_k:
        blockers.append("top_k_exceeds_policy")
    if retrieval_policy.get("require_reranker") and not reranker_model:
        blockers.append("missing_reranker_model")
    allowed_rerankers = {str(value) for value in _as_sequence(retrieval_policy.get("allowed_rerankers")) if str(value).strip()}
    if reranker_model and allowed_rerankers and reranker_model not in allowed_rerankers:
        blockers.append(f"reranker_not_allowed:{reranker_model}")
    if retrieval_policy.get("require_source_diversity"):
        sources = {str(item.get("source") or item.get("name") or "") for item in retrievers if str(item.get("source") or item.get("name") or "").strip()}
        min_sources = int(retrieval_policy.get("min_sources") or 2)
        if len(sources) < min_sources:
            blockers.append("insufficient_source_diversity")
    plan_hash = "retrieval-rerank:" + _digest(
        {
            "blockers": blockers,
            "reranker_model": reranker_model,
            "retriever_names": retriever_names,
            "top_k": top_k,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return RetrievalRerankPlanReceipt(
        ready=not blockers,
        retriever_names=retriever_names,
        top_k=top_k,
        reranker_model=reranker_model,
        blockers=tuple(blockers),
        plan_hash=plan_hash,
    )


def evaluate_citation_coverage(
    answer_contract: Mapping[str, Any],
    coverage_policy: Mapping[str, Any],
) -> CitationCoverageReceipt:
    """Evaluate whether answer claims are covered by citation records."""

    claims = tuple(dict(item) for item in _as_mapping_sequence(answer_contract.get("claims")))
    citations = tuple(dict(item) for item in _as_mapping_sequence(answer_contract.get("citations")))
    claim_ids = tuple(str(item.get("id") or item.get("claim_id") or item.get("text") or "").strip() for item in claims)
    citation_claim_ids: set[str] = set()
    for citation in citations:
        for value in _as_sequence(citation.get("claim_ids") or citation.get("claim_id")):
            text = str(value).strip()
            if text:
                citation_claim_ids.add(text)
    uncovered_claims = tuple(claim_id for claim_id in claim_ids if claim_id and claim_id not in citation_claim_ids)
    blockers: list[str] = []
    if not claims:
        blockers.append("missing_claims")
    if not citations:
        blockers.append("missing_citations")
    if uncovered_claims:
        blockers.append("uncovered_claims")
    min_citations = int(coverage_policy.get("min_citations") or 0)
    if min_citations and len(citations) < min_citations:
        blockers.append("citation_count_below_policy")
    if coverage_policy.get("require_source_ids"):
        for index, citation in enumerate(citations):
            if _blank(citation.get("source_id")):
                blockers.append(f"citation_{index + 1}_missing_source_id")
    coverage_hash = "citation-coverage:" + _digest(
        {
            "blockers": blockers,
            "citation_count": len(citations),
            "claim_count": len(claims),
            "uncovered_claims": uncovered_claims,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return CitationCoverageReceipt(
        grounded=not blockers,
        claim_count=len(claims),
        citation_count=len(citations),
        uncovered_claims=uncovered_claims,
        blockers=tuple(blockers),
        coverage_hash=coverage_hash,
    )


def plan_agent_tool_permission_matrix(
    tool_registry: Mapping[str, Any],
    permission_policy: Mapping[str, Any],
) -> AgentToolPermissionMatrixReceipt:
    """Plan agent tool permissions with role, scope, and approval checks."""

    tools = tuple(dict(item) for item in _as_mapping_sequence(tool_registry.get("tools")))
    roles = tuple(str(value) for value in _as_sequence(tool_registry.get("roles")) if str(value).strip())
    bindings = tuple(dict(item) for item in _as_mapping_sequence(tool_registry.get("bindings")))
    tool_names = tuple(str(item.get("name") or item.get("tool_name") or "").strip() for item in tools if str(item.get("name") or item.get("tool_name") or "").strip())
    blockers: list[str] = []
    if not tool_names:
        blockers.append("missing_tools")
    if not roles:
        blockers.append("missing_roles")
    if not bindings:
        blockers.append("missing_bindings")
    tool_set = set(tool_names)
    role_set = set(roles)
    effect_by_tool = {str(item.get("name") or item.get("tool_name") or ""): tuple(str(value) for value in _as_sequence(item.get("effects")) if str(value).strip()) for item in tools}
    for index, binding in enumerate(bindings):
        role = str(binding.get("role") or "").strip()
        tool_name = str(binding.get("tool") or binding.get("tool_name") or "").strip()
        scopes = tuple(str(value) for value in _as_sequence(binding.get("scopes")) if str(value).strip())
        if role not in role_set:
            blockers.append(f"binding_{index + 1}_unknown_role")
        if tool_name == "*" and permission_policy.get("forbid_wildcards"):
            blockers.append(f"{role}:wildcard_tool_forbidden")
        elif tool_name not in tool_set:
            blockers.append(f"{role}:unknown_tool:{tool_name}")
        if permission_policy.get("require_scopes") and not scopes:
            blockers.append(f"{role}:{tool_name}:missing_scopes")
        if permission_policy.get("require_reason") and _blank(binding.get("reason")):
            blockers.append(f"{role}:{tool_name}:missing_reason")
        high_effects = {"network_write", "database_write", "secret_read", "external_side_effect"}
        if permission_policy.get("require_approval_for_effects") and high_effects.intersection(effect_by_tool.get(tool_name, ())):
            if not binding.get("approval_required"):
                blockers.append(f"{role}:{tool_name}:missing_approval_required")
    matrix_hash = "agent-tool-permissions:" + _digest(
        {
            "bindings": bindings,
            "blockers": blockers,
            "roles": roles,
            "tool_names": tool_names,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return AgentToolPermissionMatrixReceipt(
        ready=not blockers,
        tool_names=tool_names,
        roles=roles,
        bindings=bindings,
        blockers=tuple(blockers),
        matrix_hash=matrix_hash,
    )


def plan_model_routing_policy(
    routing_spec: Mapping[str, Any],
    routing_policy: Mapping[str, Any],
) -> ModelRoutingPolicyReceipt:
    """Plan model routing with fallback, budget, and data-class gates."""

    routes = tuple(dict(item) for item in _as_mapping_sequence(routing_spec.get("routes")))
    route_names = tuple(str(item.get("name") or "").strip() for item in routes if str(item.get("name") or "").strip())
    default_model = str(routing_spec.get("default_model") or routing_policy.get("default_model") or "").strip()
    fallback_models = tuple(str(value) for value in _as_sequence(routing_spec.get("fallback_models")) if str(value).strip())
    allowed_models = {str(value) for value in _as_sequence(routing_policy.get("allowed_models")) if str(value).strip()}
    restricted_data_classes = {str(value) for value in _as_sequence(routing_policy.get("restricted_data_classes")) if str(value).strip()}
    blockers: list[str] = []
    if not routes:
        blockers.append("missing_routes")
    if not default_model:
        blockers.append("missing_default_model")
    elif allowed_models and default_model not in allowed_models:
        blockers.append(f"default_model_not_allowed:{default_model}")
    if routing_policy.get("require_fallback") and not fallback_models:
        blockers.append("missing_fallback_models")
    for model in fallback_models:
        if allowed_models and model not in allowed_models:
            blockers.append(f"fallback_model_not_allowed:{model}")
    max_cost_usd = float(routing_policy.get("max_cost_usd") or 0)
    for route in routes:
        name = str(route.get("name") or "route")
        model = str(route.get("model") or default_model)
        if allowed_models and model not in allowed_models:
            blockers.append(f"{name}:model_not_allowed:{model}")
        cost = float(route.get("max_cost_usd") or 0)
        if max_cost_usd and cost > max_cost_usd:
            blockers.append(f"{name}:cost_exceeds_policy")
        route_data_classes = {str(value) for value in _as_sequence(route.get("data_classes")) if str(value).strip()}
        if restricted_data_classes.intersection(route_data_classes) and not route.get("local_only"):
            blockers.append(f"{name}:restricted_data_requires_local_route")
    policy_hash = "model-routing:" + _digest(
        {
            "blockers": blockers,
            "default_model": default_model,
            "fallback_models": fallback_models,
            "route_names": route_names,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ModelRoutingPolicyReceipt(
        ready=not blockers,
        route_names=route_names,
        default_model=default_model,
        fallback_models=fallback_models,
        blockers=tuple(blockers),
        policy_hash=policy_hash,
    )


def plan_prompt_regression_suite(
    suite_spec: Mapping[str, Any],
    regression_policy: Mapping[str, Any],
) -> PromptRegressionSuitePlanReceipt:
    """Plan prompt regression fixtures, metrics, and thresholds."""

    cases = tuple(dict(item) for item in _as_mapping_sequence(suite_spec.get("cases")))
    metrics = tuple(str(value) for value in _as_sequence(suite_spec.get("metrics") or regression_policy.get("metrics")) if str(value).strip())
    thresholds = dict(suite_spec.get("thresholds") if isinstance(suite_spec.get("thresholds"), Mapping) else {})
    blockers: list[str] = []
    if not cases:
        blockers.append("missing_cases")
    min_cases = int(regression_policy.get("min_cases") or 0)
    if min_cases and len(cases) < min_cases:
        blockers.append("case_count_below_policy")
    if not metrics:
        blockers.append("missing_metrics")
    for metric in metrics:
        if metric not in thresholds:
            blockers.append(f"missing_threshold:{metric}")
    if regression_policy.get("require_expected_outputs"):
        for index, case in enumerate(cases):
            if _blank(case.get("expected_output")) and _blank(case.get("expected_terms")):
                blockers.append(f"case_{index + 1}_missing_expected_output")
    suite_hash = "prompt-regression-suite:" + _digest(
        {
            "blockers": blockers,
            "case_count": len(cases),
            "metrics": metrics,
            "thresholds": thresholds,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PromptRegressionSuitePlanReceipt(
        ready=not blockers,
        case_count=len(cases),
        metrics=metrics,
        thresholds=thresholds,
        blockers=tuple(blockers),
        suite_hash=suite_hash,
    )


def plan_memory_retention_policy(
    memory_spec: Mapping[str, Any],
    retention_policy: Mapping[str, Any],
) -> MemoryRetentionPolicyPlanReceipt:
    """Plan agent memory retention with TTL, consent, and deletion checks."""

    memory_scope = normalize_field_name(memory_spec.get("memory_scope") or memory_spec.get("scope") or "")
    retention_days = int(memory_spec.get("retention_days") or retention_policy.get("default_retention_days") or 0)
    pii_fields = tuple(str(value) for value in _as_sequence(memory_spec.get("pii_fields")) if str(value).strip())
    blockers: list[str] = []
    if not memory_scope:
        blockers.append("missing_memory_scope")
    if retention_days <= 0:
        blockers.append("missing_retention_days")
    max_retention_days = int(retention_policy.get("max_retention_days") or 0)
    if max_retention_days and retention_days > max_retention_days:
        blockers.append("retention_exceeds_policy")
    if retention_policy.get("require_deletion_workflow") and not memory_spec.get("deletion_workflow"):
        blockers.append("missing_deletion_workflow")
    if retention_policy.get("require_consent") and not memory_spec.get("consent_signal"):
        blockers.append("missing_consent_signal")
    if retention_policy.get("require_pii_redaction") and pii_fields and not memory_spec.get("redaction_policy"):
        blockers.append("missing_pii_redaction_policy")
    policy_hash = "memory-retention:" + _digest(
        {
            "blockers": blockers,
            "memory_scope": memory_scope,
            "pii_fields": pii_fields,
            "retention_days": retention_days,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return MemoryRetentionPolicyPlanReceipt(
        ready=not blockers,
        memory_scope=memory_scope,
        retention_days=retention_days,
        pii_fields=pii_fields,
        blockers=tuple(blockers),
        policy_hash=policy_hash,
    )


def evaluate_vector_index_freshness(
    index_status: Mapping[str, Any],
    freshness_policy: Mapping[str, Any],
) -> VectorIndexFreshnessReceipt:
    """Evaluate vector-index freshness and stale-document rebuild gates."""

    index_name = normalize_field_name(index_status.get("index_name") or index_status.get("name") or "")
    age_seconds = int(index_status.get("age_seconds") or 0)
    max_age_seconds = int(freshness_policy.get("max_age_seconds") or 0)
    max_document_age_seconds = int(freshness_policy.get("max_document_age_seconds") or max_age_seconds or 0)
    documents = tuple(dict(item) for item in _as_mapping_sequence(index_status.get("documents")))
    stale_documents = tuple(
        str(document.get("id") or document.get("document_id") or index + 1)
        for index, document in enumerate(documents)
        if max_document_age_seconds and int(document.get("age_seconds") or 0) > max_document_age_seconds
    )
    blockers: list[str] = []
    if not index_name:
        blockers.append("missing_index_name")
    if age_seconds <= 0:
        blockers.append("missing_index_age")
    if max_age_seconds <= 0:
        blockers.append("missing_max_age_seconds")
    if max_age_seconds and age_seconds > max_age_seconds:
        blockers.append("index_age_exceeds_policy")
    if stale_documents:
        blockers.append("stale_documents")
    if freshness_policy.get("require_rebuild_plan") and (stale_documents or (max_age_seconds and age_seconds > max_age_seconds)) and not index_status.get("rebuild_plan"):
        blockers.append("missing_rebuild_plan")
    freshness_hash = "vector-index-freshness:" + _digest(
        {
            "age_seconds": age_seconds,
            "blockers": blockers,
            "index_name": index_name,
            "max_age_seconds": max_age_seconds,
            "stale_documents": stale_documents,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return VectorIndexFreshnessReceipt(
        fresh=not blockers,
        index_name=index_name,
        age_seconds=age_seconds,
        max_age_seconds=max_age_seconds,
        stale_documents=stale_documents,
        blockers=tuple(blockers),
        freshness_hash=freshness_hash,
    )


def plan_canary_release(
    release_spec: Mapping[str, Any],
    release_policy: Mapping[str, Any],
) -> CanaryReleasePlanReceipt:
    """Plan a canary release with traffic, health, metrics, and rollback checks."""

    service_name = normalize_field_name(release_spec.get("service_name") or release_spec.get("service") or "")
    image_tag = str(release_spec.get("image_tag") or release_spec.get("version") or "").strip()
    traffic_steps = tuple(int(value) for value in _as_sequence(release_spec.get("traffic_steps")) if str(value).strip())
    metrics = tuple(str(value) for value in _as_sequence(release_spec.get("metrics")) if str(value).strip())
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if not image_tag:
        blockers.append("missing_image_tag")
    if release_policy.get("require_pinned_image") and image_tag == "latest":
        blockers.append("image_tag_not_pinned")
    if not traffic_steps:
        blockers.append("missing_traffic_steps")
    if traffic_steps and (traffic_steps[0] <= 0 or traffic_steps[-1] != 100):
        blockers.append("traffic_steps_must_finish_at_100")
    max_step_percent = int(release_policy.get("max_step_percent") or 0)
    for step in traffic_steps:
        if step <= 0 or step > 100:
            blockers.append(f"invalid_traffic_step:{step}")
        if max_step_percent and step > max_step_percent and step != 100:
            blockers.append(f"traffic_step_exceeds_policy:{step}")
    if release_policy.get("require_metrics") and not metrics:
        blockers.append("missing_metrics")
    for metric in _as_sequence(release_policy.get("required_metrics")):
        metric_name = str(metric)
        if metric_name and metric_name not in metrics:
            blockers.append(f"missing_metric:{metric_name}")
    if release_policy.get("require_health_gate") and not release_spec.get("health_gate"):
        blockers.append("missing_health_gate")
    if release_policy.get("require_rollback") and not release_spec.get("rollback_strategy"):
        blockers.append("missing_rollback_strategy")
    plan_hash = "canary-release:" + _digest(
        {
            "blockers": blockers,
            "image_tag": image_tag,
            "metrics": metrics,
            "service_name": service_name,
            "traffic_steps": traffic_steps,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return CanaryReleasePlanReceipt(
        ready=not blockers,
        service_name=service_name,
        traffic_steps=traffic_steps,
        metrics=metrics,
        blockers=tuple(blockers),
        plan_hash=plan_hash,
    )


def plan_blue_green_deployment(
    deployment_spec: Mapping[str, Any],
    deployment_policy: Mapping[str, Any],
) -> BlueGreenDeploymentPlanReceipt:
    """Plan a blue/green deployment with switch, smoke, and rollback gates."""

    service_name = normalize_field_name(deployment_spec.get("service_name") or deployment_spec.get("service") or "")
    active_color = str(deployment_spec.get("active_color") or "").strip()
    target_color = str(deployment_spec.get("target_color") or "").strip()
    switch_strategy = str(deployment_spec.get("switch_strategy") or "").strip()
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    allowed_colors = {str(value) for value in _as_sequence(deployment_policy.get("allowed_colors")) if str(value).strip()}
    if not active_color:
        blockers.append("missing_active_color")
    elif allowed_colors and active_color not in allowed_colors:
        blockers.append(f"active_color_not_allowed:{active_color}")
    if not target_color:
        blockers.append("missing_target_color")
    elif allowed_colors and target_color not in allowed_colors:
        blockers.append(f"target_color_not_allowed:{target_color}")
    if active_color and target_color and active_color == target_color:
        blockers.append("target_color_matches_active")
    if deployment_policy.get("require_switch_strategy") and not switch_strategy:
        blockers.append("missing_switch_strategy")
    if deployment_policy.get("require_smoke_tests") and not deployment_spec.get("smoke_tests"):
        blockers.append("missing_smoke_tests")
    if deployment_policy.get("require_db_compatibility") and not deployment_spec.get("database_compatible"):
        blockers.append("missing_database_compatibility")
    if deployment_policy.get("require_rollback") and not deployment_spec.get("rollback_strategy"):
        blockers.append("missing_rollback_strategy")
    deployment_hash = "blue-green-deployment:" + _digest(
        {
            "active_color": active_color,
            "blockers": blockers,
            "service_name": service_name,
            "switch_strategy": switch_strategy,
            "target_color": target_color,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return BlueGreenDeploymentPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        active_color=active_color,
        target_color=target_color,
        blockers=tuple(blockers),
        deployment_hash=deployment_hash,
    )


def plan_slo_error_budget_policy(
    slo_spec: Mapping[str, Any],
    slo_policy: Mapping[str, Any],
) -> SloErrorBudgetPolicyReceipt:
    """Plan SLO and error-budget gates for a service."""

    service_name = normalize_field_name(slo_spec.get("service_name") or slo_spec.get("service") or "")
    slo_target_percent = float(slo_spec.get("slo_target_percent") or slo_spec.get("target_percent") or 0)
    window_days = int(slo_spec.get("window_days") or slo_policy.get("default_window_days") or 0)
    error_budget_minutes = int(slo_spec.get("error_budget_minutes") or 0)
    alert_windows = tuple(str(value) for value in _as_sequence(slo_spec.get("alert_windows")) if str(value).strip())
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if slo_target_percent <= 0 or slo_target_percent >= 100:
        blockers.append("invalid_slo_target")
    min_target = float(slo_policy.get("min_slo_target_percent") or 0)
    if min_target and slo_target_percent < min_target:
        blockers.append("slo_target_below_policy")
    if window_days <= 0:
        blockers.append("missing_window_days")
    if error_budget_minutes <= 0:
        blockers.append("missing_error_budget_minutes")
    if slo_policy.get("require_alert_windows") and not alert_windows:
        blockers.append("missing_alert_windows")
    if slo_policy.get("require_burn_rate_alerts") and not slo_spec.get("burn_rate_alerts"):
        blockers.append("missing_burn_rate_alerts")
    if slo_policy.get("require_runbook") and not slo_spec.get("runbook_ref"):
        blockers.append("missing_runbook_ref")
    policy_hash = "slo-error-budget:" + _digest(
        {
            "alert_windows": alert_windows,
            "blockers": blockers,
            "error_budget_minutes": error_budget_minutes,
            "service_name": service_name,
            "slo_target_percent": slo_target_percent,
            "window_days": window_days,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SloErrorBudgetPolicyReceipt(
        ready=not blockers,
        service_name=service_name,
        slo_target_percent=slo_target_percent,
        window_days=window_days,
        error_budget_minutes=error_budget_minutes,
        blockers=tuple(blockers),
        policy_hash=policy_hash,
    )


def evaluate_dependency_vulnerability_exception(
    exception_request: Mapping[str, Any],
    vulnerability_policy: Mapping[str, Any],
) -> DependencyVulnerabilityExceptionReceipt:
    """Evaluate a dependency vulnerability exception request."""

    dependency_name = str(exception_request.get("dependency_name") or exception_request.get("package") or "").strip()
    vulnerability_id = str(exception_request.get("vulnerability_id") or exception_request.get("cve") or "").strip()
    severity = str(exception_request.get("severity") or "").strip().lower()
    expiry_days = int(exception_request.get("expiry_days") or 0)
    blockers: list[str] = []
    if not dependency_name:
        blockers.append("missing_dependency_name")
    if not vulnerability_id:
        blockers.append("missing_vulnerability_id")
    allowed_severities = {str(value).lower() for value in _as_sequence(vulnerability_policy.get("allowed_severities")) if str(value).strip()}
    if not severity:
        blockers.append("missing_severity")
    elif allowed_severities and severity not in allowed_severities:
        blockers.append(f"severity_not_allowed:{severity}")
    if severity == "critical" and vulnerability_policy.get("forbid_critical_exceptions"):
        blockers.append("critical_exception_forbidden")
    max_expiry_days = int(vulnerability_policy.get("max_expiry_days") or 0)
    if expiry_days <= 0:
        blockers.append("missing_expiry_days")
    elif max_expiry_days and expiry_days > max_expiry_days:
        blockers.append("expiry_exceeds_policy")
    if vulnerability_policy.get("require_owner") and not exception_request.get("owner"):
        blockers.append("missing_owner")
    if vulnerability_policy.get("require_compensating_controls") and not exception_request.get("compensating_controls"):
        blockers.append("missing_compensating_controls")
    if vulnerability_policy.get("require_fix_version") and not exception_request.get("fix_version"):
        blockers.append("missing_fix_version")
    exception_hash = "dependency-vulnerability-exception:" + _digest(
        {
            "blockers": blockers,
            "dependency_name": dependency_name,
            "expiry_days": expiry_days,
            "severity": severity,
            "vulnerability_id": vulnerability_id,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DependencyVulnerabilityExceptionReceipt(
        approved=not blockers,
        dependency_name=dependency_name,
        vulnerability_id=vulnerability_id,
        severity=severity,
        blockers=tuple(blockers),
        exception_hash=exception_hash,
    )


def evaluate_secret_scan_findings(
    scan_result: Mapping[str, Any],
    scan_policy: Mapping[str, Any],
) -> SecretScanFindingReceipt:
    """Evaluate secret-scan findings and remediation requirements."""

    scanner_name = normalize_field_name(scan_result.get("scanner_name") or scan_result.get("scanner") or "")
    findings = tuple(dict(item) for item in _as_mapping_sequence(scan_result.get("findings")))
    confirmed = tuple(finding for finding in findings if finding.get("confirmed") or str(finding.get("confidence") or "").lower() == "high")
    blockers: list[str] = []
    if not scanner_name:
        blockers.append("missing_scanner_name")
    if scan_policy.get("require_findings_payload") and "findings" not in scan_result:
        blockers.append("missing_findings_payload")
    if confirmed:
        blockers.append("confirmed_secret_findings")
    if scan_policy.get("require_remediation_for_confirmed"):
        for index, finding in enumerate(confirmed):
            if not finding.get("remediation"):
                blockers.append(f"finding_{index + 1}_missing_remediation")
    if scan_policy.get("require_ignore_reasons"):
        for index, finding in enumerate(findings):
            if finding.get("ignored") and not finding.get("ignore_reason"):
                blockers.append(f"finding_{index + 1}_missing_ignore_reason")
    scan_hash = "secret-scan:" + _digest(
        {
            "blockers": blockers,
            "confirmed_secret_count": len(confirmed),
            "finding_count": len(findings),
            "scanner_name": scanner_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SecretScanFindingReceipt(
        clean=not blockers,
        scanner_name=scanner_name,
        finding_count=len(findings),
        confirmed_secret_count=len(confirmed),
        blockers=tuple(blockers),
        scan_hash=scan_hash,
    )


def plan_sbom_generation(
    package_spec: Mapping[str, Any],
    sbom_policy: Mapping[str, Any],
) -> SbomGenerationPlanReceipt:
    """Plan SBOM generation with format, component, and provenance checks."""

    package_name = normalize_field_name(package_spec.get("package_name") or package_spec.get("name") or "")
    components = tuple(dict(item) for item in _as_mapping_sequence(package_spec.get("components")))
    formats = tuple(str(value) for value in _as_sequence(package_spec.get("formats") or sbom_policy.get("formats")) if str(value).strip())
    blockers: list[str] = []
    if not package_name:
        blockers.append("missing_package_name")
    if not components:
        blockers.append("missing_components")
    allowed_formats = {str(value) for value in _as_sequence(sbom_policy.get("allowed_formats")) if str(value).strip()}
    if not formats:
        blockers.append("missing_formats")
    for fmt in formats:
        if allowed_formats and fmt not in allowed_formats:
            blockers.append(f"format_not_allowed:{fmt}")
    for fmt in _as_sequence(sbom_policy.get("required_formats")):
        format_name = str(fmt)
        if format_name and format_name not in formats:
            blockers.append(f"missing_format:{format_name}")
    if sbom_policy.get("require_provenance") and not package_spec.get("provenance"):
        blockers.append("missing_provenance")
    if sbom_policy.get("require_supplier") and any(_blank(component.get("supplier")) for component in components):
        blockers.append("component_missing_supplier")
    sbom_hash = "sbom-generation:" + _digest(
        {
            "blockers": blockers,
            "component_count": len(components),
            "formats": formats,
            "package_name": package_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SbomGenerationPlanReceipt(
        ready=not blockers,
        package_name=package_name,
        component_count=len(components),
        formats=formats,
        blockers=tuple(blockers),
        sbom_hash=sbom_hash,
    )


def plan_license_compliance(
    dependency_inventory: Mapping[str, Any],
    license_policy: Mapping[str, Any],
) -> LicenseCompliancePlanReceipt:
    """Plan license compliance with restricted-license and attribution checks."""

    packages = tuple(dict(item) for item in _as_mapping_sequence(dependency_inventory.get("packages")))
    restricted = {str(value) for value in _as_sequence(license_policy.get("restricted_licenses")) if str(value).strip()}
    package_restricted = tuple(sorted(
        str(package.get("license"))
        for package in packages
        if str(package.get("license") or "") in restricted
    ))
    blockers: list[str] = []
    if not packages:
        blockers.append("missing_packages")
    if package_restricted:
        blockers.append("restricted_licenses_present")
    if license_policy.get("require_attribution"):
        for index, package in enumerate(packages):
            if _blank(package.get("attribution")):
                blockers.append(f"package_{index + 1}_missing_attribution")
    if license_policy.get("require_license_ids"):
        for index, package in enumerate(packages):
            if _blank(package.get("license")):
                blockers.append(f"package_{index + 1}_missing_license")
    compliance_hash = "license-compliance:" + _digest(
        {
            "blockers": blockers,
            "package_count": len(packages),
            "restricted_licenses": package_restricted,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return LicenseCompliancePlanReceipt(
        compliant=not blockers,
        package_count=len(packages),
        restricted_licenses=package_restricted,
        blockers=tuple(blockers),
        compliance_hash=compliance_hash,
    )


def plan_backup_restore(
    resource_spec: Mapping[str, Any],
    backup_policy: Mapping[str, Any],
) -> BackupRestorePlanReceipt:
    """Plan backup and restore with RPO/RTO, encryption, and restore-test gates."""

    resource_name = normalize_field_name(resource_spec.get("resource_name") or resource_spec.get("name") or "")
    backup_frequency = str(resource_spec.get("backup_frequency") or "").strip()
    restore_objective_minutes = int(resource_spec.get("restore_objective_minutes") or resource_spec.get("rto_minutes") or 0)
    recovery_point_minutes = int(resource_spec.get("recovery_point_minutes") or resource_spec.get("rpo_minutes") or 0)
    blockers: list[str] = []
    if not resource_name:
        blockers.append("missing_resource_name")
    if not backup_frequency:
        blockers.append("missing_backup_frequency")
    max_rto = int(backup_policy.get("max_restore_objective_minutes") or 0)
    if restore_objective_minutes <= 0:
        blockers.append("missing_restore_objective")
    elif max_rto and restore_objective_minutes > max_rto:
        blockers.append("restore_objective_exceeds_policy")
    max_rpo = int(backup_policy.get("max_recovery_point_minutes") or 0)
    if recovery_point_minutes <= 0:
        blockers.append("missing_recovery_point")
    elif max_rpo and recovery_point_minutes > max_rpo:
        blockers.append("recovery_point_exceeds_policy")
    if backup_policy.get("require_encryption") and not resource_spec.get("encryption"):
        blockers.append("missing_encryption")
    if backup_policy.get("require_restore_test") and not resource_spec.get("restore_test"):
        blockers.append("missing_restore_test")
    if backup_policy.get("require_offsite_copy") and not resource_spec.get("offsite_copy"):
        blockers.append("missing_offsite_copy")
    plan_hash = "backup-restore:" + _digest(
        {
            "backup_frequency": backup_frequency,
            "blockers": blockers,
            "recovery_point_minutes": recovery_point_minutes,
            "resource_name": resource_name,
            "restore_objective_minutes": restore_objective_minutes,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return BackupRestorePlanReceipt(
        ready=not blockers,
        resource_name=resource_name,
        backup_frequency=backup_frequency,
        restore_objective_minutes=restore_objective_minutes,
        blockers=tuple(blockers),
        plan_hash=plan_hash,
    )


def plan_circuit_breaker(
    service_contract: Mapping[str, Any],
    breaker_policy: Mapping[str, Any],
) -> CircuitBreakerPlanReceipt:
    """Plan a circuit breaker with fallback, reset timeout, and metric gates."""

    raw_service_name = str(service_contract.get("service_name") or service_contract.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    failure_threshold = int(service_contract.get("failure_threshold") or 0)
    reset_timeout_seconds = int(service_contract.get("reset_timeout_seconds") or service_contract.get("reset_after_seconds") or 0)
    metrics = {normalize_field_name(metric) for metric in _as_sequence(service_contract.get("metrics")) if not _blank(metric)}
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if failure_threshold <= 0:
        blockers.append("missing_failure_threshold")
    max_failure_threshold = int(breaker_policy.get("max_failure_threshold") or 0)
    if max_failure_threshold and failure_threshold > max_failure_threshold:
        blockers.append("failure_threshold_exceeds_policy")
    if reset_timeout_seconds <= 0:
        blockers.append("missing_reset_timeout_seconds")
    if breaker_policy.get("require_fallback") and _blank(service_contract.get("fallback")):
        blockers.append("missing_fallback")
    if breaker_policy.get("require_metrics") and not metrics:
        blockers.append("missing_metrics")
    for metric in _as_sequence(breaker_policy.get("required_metrics")):
        metric_name = normalize_field_name(metric)
        if metric_name and metric_name not in metrics:
            blockers.append(f"missing_metric:{metric_name}")
    plan_hash = "circuit-breaker:" + _digest(
        {
            "blockers": blockers,
            "failure_threshold": failure_threshold,
            "metrics": sorted(metrics),
            "reset_timeout_seconds": reset_timeout_seconds,
            "service_name": service_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return CircuitBreakerPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        failure_threshold=failure_threshold,
        reset_timeout_seconds=reset_timeout_seconds,
        blockers=tuple(blockers),
        plan_hash=plan_hash,
    )


def plan_retry_backoff_policy(
    operation_contract: Mapping[str, Any],
    retry_policy: Mapping[str, Any],
) -> RetryBackoffPolicyReceipt:
    """Plan retry/backoff behavior with jitter and idempotency gates."""

    raw_operation_name = str(operation_contract.get("operation_name") or operation_contract.get("name") or "").strip()
    operation_name = normalize_field_name(raw_operation_name) if raw_operation_name else ""
    max_attempts = int(operation_contract.get("max_attempts") or operation_contract.get("attempts") or 0)
    base_delay_ms = int(operation_contract.get("base_delay_ms") or 0)
    jitter = bool(operation_contract.get("jitter"))
    backoff_strategy = str(operation_contract.get("backoff_strategy") or "").strip()
    blockers: list[str] = []
    if not operation_name:
        blockers.append("missing_operation_name")
    if max_attempts <= 0:
        blockers.append("missing_max_attempts")
    max_attempt_policy = int(retry_policy.get("max_attempts") or 0)
    if max_attempt_policy and max_attempts > max_attempt_policy:
        blockers.append("max_attempts_exceeds_policy")
    if base_delay_ms <= 0:
        blockers.append("missing_base_delay_ms")
    if not backoff_strategy:
        blockers.append("missing_backoff_strategy")
    if retry_policy.get("require_jitter") and not jitter:
        blockers.append("missing_jitter")
    if retry_policy.get("forbid_non_idempotent_retries") and not operation_contract.get("idempotent"):
        blockers.append("non_idempotent_retry_forbidden")
    policy_hash = "retry-backoff:" + _digest(
        {
            "backoff_strategy": backoff_strategy,
            "base_delay_ms": base_delay_ms,
            "blockers": blockers,
            "jitter": jitter,
            "max_attempts": max_attempts,
            "operation_name": operation_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return RetryBackoffPolicyReceipt(
        ready=not blockers,
        operation_name=operation_name,
        max_attempts=max_attempts,
        base_delay_ms=base_delay_ms,
        jitter=jitter,
        blockers=tuple(blockers),
        policy_hash=policy_hash,
    )


def plan_timeout_budget(
    operation_contract: Mapping[str, Any],
    timeout_policy: Mapping[str, Any],
) -> TimeoutBudgetPlanReceipt:
    """Plan operation timeout budget with phase-level budget gates."""

    raw_operation_name = str(operation_contract.get("operation_name") or operation_contract.get("name") or "").strip()
    operation_name = normalize_field_name(raw_operation_name) if raw_operation_name else ""
    total_timeout_ms = int(operation_contract.get("total_timeout_ms") or operation_contract.get("timeout_ms") or 0)
    raw_phase_budgets = operation_contract.get("phase_budgets")
    phase_budgets: dict[str, int] = {}
    if isinstance(raw_phase_budgets, Mapping):
        for phase, budget in raw_phase_budgets.items():
            phase_name = normalize_field_name(phase)
            phase_budgets[phase_name] = int(budget or 0)
    blockers: list[str] = []
    if not operation_name:
        blockers.append("missing_operation_name")
    if total_timeout_ms <= 0:
        blockers.append("missing_total_timeout_ms")
    max_total_timeout_ms = int(timeout_policy.get("max_total_timeout_ms") or 0)
    if max_total_timeout_ms and total_timeout_ms > max_total_timeout_ms:
        blockers.append("timeout_exceeds_policy")
    if not phase_budgets:
        blockers.append("missing_phase_budgets")
    elif sum(phase_budgets.values()) > total_timeout_ms:
        blockers.append("phase_budgets_exceed_total")
    for phase in _as_sequence(timeout_policy.get("required_phases")):
        phase_name = normalize_field_name(phase)
        if phase_name and phase_name not in phase_budgets:
            blockers.append(f"missing_required_phase:{phase_name}")
    budget_hash = "timeout-budget:" + _digest(
        {
            "blockers": blockers,
            "operation_name": operation_name,
            "phase_budgets": phase_budgets,
            "total_timeout_ms": total_timeout_ms,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return TimeoutBudgetPlanReceipt(
        ready=not blockers,
        operation_name=operation_name,
        total_timeout_ms=total_timeout_ms,
        phase_budgets=phase_budgets,
        blockers=tuple(blockers),
        budget_hash=budget_hash,
    )


def plan_concurrency_limit(
    resource_contract: Mapping[str, Any],
    concurrency_policy: Mapping[str, Any],
) -> ConcurrencyLimitPlanReceipt:
    """Plan concurrency limit/bulkhead behavior with queue and overflow gates."""

    raw_resource_name = str(resource_contract.get("resource_name") or resource_contract.get("name") or "").strip()
    resource_name = normalize_field_name(raw_resource_name) if raw_resource_name else ""
    max_concurrency = int(resource_contract.get("max_concurrency") or resource_contract.get("concurrency") or 0)
    queue_limit = int(resource_contract.get("queue_limit") or 0)
    metrics = {normalize_field_name(metric) for metric in _as_sequence(resource_contract.get("metrics")) if not _blank(metric)}
    blockers: list[str] = []
    if not resource_name:
        blockers.append("missing_resource_name")
    if max_concurrency <= 0:
        blockers.append("missing_max_concurrency")
    max_concurrency_policy = int(concurrency_policy.get("max_concurrency") or 0)
    if max_concurrency_policy and max_concurrency > max_concurrency_policy:
        blockers.append("max_concurrency_exceeds_policy")
    if concurrency_policy.get("require_queue_limit") and queue_limit <= 0:
        blockers.append("missing_queue_limit")
    if concurrency_policy.get("require_overflow_policy") and _blank(resource_contract.get("overflow_policy")):
        blockers.append("missing_overflow_policy")
    for metric in _as_sequence(concurrency_policy.get("required_metrics")):
        metric_name = normalize_field_name(metric)
        if metric_name and metric_name not in metrics:
            blockers.append(f"missing_metric:{metric_name}")
    limit_hash = "concurrency-limit:" + _digest(
        {
            "blockers": blockers,
            "max_concurrency": max_concurrency,
            "metrics": sorted(metrics),
            "queue_limit": queue_limit,
            "resource_name": resource_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ConcurrencyLimitPlanReceipt(
        ready=not blockers,
        resource_name=resource_name,
        max_concurrency=max_concurrency,
        queue_limit=queue_limit,
        blockers=tuple(blockers),
        limit_hash=limit_hash,
    )


def plan_health_probe_contract(
    service_contract: Mapping[str, Any],
    probe_policy: Mapping[str, Any],
) -> HealthProbePlanReceipt:
    """Plan readiness/liveness/startup probe contract checks."""

    raw_service_name = str(service_contract.get("service_name") or service_contract.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    readiness_path = str(service_contract.get("readiness_path") or "").strip()
    liveness_path = str(service_contract.get("liveness_path") or "").strip()
    probe_timeout_ms = int(service_contract.get("probe_timeout_ms") or service_contract.get("timeout_ms") or 0)
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if not readiness_path:
        blockers.append("missing_readiness_path")
    if not liveness_path:
        blockers.append("missing_liveness_path")
    if probe_policy.get("require_startup_probe") and _blank(service_contract.get("startup_probe")):
        blockers.append("missing_startup_probe")
    if probe_policy.get("require_timeout") and probe_timeout_ms <= 0:
        blockers.append("missing_probe_timeout_ms")
    max_probe_timeout_ms = int(probe_policy.get("max_probe_timeout_ms") or 0)
    if max_probe_timeout_ms and probe_timeout_ms > max_probe_timeout_ms:
        blockers.append("probe_timeout_exceeds_policy")
    if probe_policy.get("require_dependency_checks") and not _as_sequence(service_contract.get("dependency_checks")):
        blockers.append("missing_dependency_checks")
    probe_hash = "health-probe:" + _digest(
        {
            "blockers": blockers,
            "liveness_path": liveness_path,
            "probe_timeout_ms": probe_timeout_ms,
            "readiness_path": readiness_path,
            "service_name": service_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return HealthProbePlanReceipt(
        ready=not blockers,
        service_name=service_name,
        readiness_path=readiness_path,
        liveness_path=liveness_path,
        blockers=tuple(blockers),
        probe_hash=probe_hash,
    )


def plan_dependency_readiness(
    service_contract: Mapping[str, Any],
    readiness_policy: Mapping[str, Any],
) -> DependencyReadinessPlanReceipt:
    """Plan dependency readiness checks with timeout and fallback gates."""

    raw_service_name = str(service_contract.get("service_name") or service_contract.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    dependencies = tuple(dict(item) for item in _as_mapping_sequence(service_contract.get("dependencies")))
    dependency_names = tuple(
        normalize_field_name(dependency.get("name") or dependency.get("dependency_name") or f"dependency_{index + 1}")
        for index, dependency in enumerate(dependencies)
    )
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if not dependencies:
        blockers.append("missing_dependencies")
    for dependency, dependency_name in zip(dependencies, dependency_names):
        if _blank(dependency.get("healthcheck")):
            blockers.append(f"{dependency_name}:missing_healthcheck")
        if readiness_policy.get("require_timeout_for_critical") and dependency.get("critical") and int(dependency.get("timeout_ms") or 0) <= 0:
            blockers.append(f"{dependency_name}:critical_dependency_without_timeout")
        if readiness_policy.get("require_fallback_for_critical") and dependency.get("critical") and _blank(dependency.get("fallback")):
            blockers.append(f"{dependency_name}:missing_fallback")
    readiness_hash = "dependency-readiness:" + _digest(
        {
            "blockers": blockers,
            "dependencies": dependency_names,
            "service_name": service_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DependencyReadinessPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        dependencies=dependency_names,
        blockers=tuple(blockers),
        readiness_hash=readiness_hash,
    )


def plan_graceful_shutdown(
    service_contract: Mapping[str, Any],
    shutdown_policy: Mapping[str, Any],
) -> GracefulShutdownPlanReceipt:
    """Plan graceful shutdown with drain timeout, hooks, and signal gates."""

    raw_service_name = str(service_contract.get("service_name") or service_contract.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    drain_timeout_seconds = int(service_contract.get("drain_timeout_seconds") or 0)
    hooks = tuple(normalize_field_name(hook) for hook in _as_sequence(service_contract.get("hooks")) if not _blank(hook))
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if drain_timeout_seconds <= 0:
        blockers.append("missing_drain_timeout_seconds")
    max_drain_timeout_seconds = int(shutdown_policy.get("max_drain_timeout_seconds") or 0)
    if max_drain_timeout_seconds and drain_timeout_seconds > max_drain_timeout_seconds:
        blockers.append("drain_timeout_exceeds_policy")
    for hook in _as_sequence(shutdown_policy.get("required_hooks")):
        hook_name = normalize_field_name(hook)
        if hook_name and hook_name not in hooks:
            blockers.append(f"missing_hook:{hook_name}")
    if shutdown_policy.get("require_signal_handler") and not service_contract.get("signal_handler"):
        blockers.append("missing_signal_handler")
    if shutdown_policy.get("require_inflight_request_drain") and not service_contract.get("inflight_request_drain"):
        blockers.append("missing_inflight_request_drain")
    shutdown_hash = "graceful-shutdown:" + _digest(
        {
            "blockers": blockers,
            "drain_timeout_seconds": drain_timeout_seconds,
            "hooks": hooks,
            "service_name": service_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return GracefulShutdownPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        drain_timeout_seconds=drain_timeout_seconds,
        hooks=hooks,
        blockers=tuple(blockers),
        shutdown_hash=shutdown_hash,
    )


def plan_chaos_experiment(
    experiment_spec: Mapping[str, Any],
    chaos_policy: Mapping[str, Any],
) -> ChaosExperimentPlanReceipt:
    """Plan a chaos experiment with blast-radius, observability, and rollback gates."""

    raw_experiment_name = str(experiment_spec.get("experiment_name") or experiment_spec.get("name") or "").strip()
    experiment_name = normalize_field_name(raw_experiment_name) if raw_experiment_name else ""
    raw_target_service = str(experiment_spec.get("target_service") or "").strip()
    target_service = normalize_field_name(raw_target_service) if raw_target_service else ""
    raw_blast_radius = str(experiment_spec.get("blast_radius") or "").strip()
    blast_radius = normalize_field_name(raw_blast_radius) if raw_blast_radius else ""
    allowed_blast_radius = {
        normalize_field_name(value)
        for value in _as_sequence(chaos_policy.get("allowed_blast_radius"))
        if not _blank(value)
    }
    blockers: list[str] = []
    if not experiment_name:
        blockers.append("missing_experiment_name")
    if not target_service:
        blockers.append("missing_target_service")
    if not blast_radius:
        blockers.append("missing_blast_radius")
    elif allowed_blast_radius and blast_radius not in allowed_blast_radius:
        blockers.append(f"blast_radius_not_allowed:{blast_radius}")
    if chaos_policy.get("require_hypothesis") and _blank(experiment_spec.get("hypothesis")):
        blockers.append("missing_hypothesis")
    if chaos_policy.get("require_abort_condition") and _blank(experiment_spec.get("abort_condition")):
        blockers.append("missing_abort_condition")
    if chaos_policy.get("require_observability") and not _as_sequence(experiment_spec.get("observability")):
        blockers.append("missing_observability")
    if chaos_policy.get("require_rollback") and _blank(experiment_spec.get("rollback")):
        blockers.append("missing_rollback")
    experiment_hash = "chaos-experiment:" + _digest(
        {
            "blast_radius": blast_radius,
            "blockers": blockers,
            "experiment_name": experiment_name,
            "target_service": target_service,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ChaosExperimentPlanReceipt(
        ready=not blockers,
        experiment_name=experiment_name,
        target_service=target_service,
        blast_radius=blast_radius,
        blockers=tuple(blockers),
        experiment_hash=experiment_hash,
    )


def evaluate_openapi_compatibility(
    previous_spec: Mapping[str, Any],
    next_spec: Mapping[str, Any],
    compatibility_policy: Mapping[str, Any],
) -> OpenApiCompatibilityReceipt:
    """Evaluate OpenAPI path and operation compatibility for endpoint evolution."""

    previous_paths = previous_spec.get("paths") if isinstance(previous_spec.get("paths"), Mapping) else {}
    next_paths = next_spec.get("paths") if isinstance(next_spec.get("paths"), Mapping) else {}
    removed_paths = tuple(sorted(path for path in previous_paths if path not in next_paths))
    removed_operations: list[str] = []
    changed_operations: list[str] = []
    for path, previous_path_spec in previous_paths.items():
        if path not in next_paths or not isinstance(previous_path_spec, Mapping):
            continue
        next_path_spec = next_paths.get(path)
        if not isinstance(next_path_spec, Mapping):
            continue
        for method, previous_operation in previous_path_spec.items():
            method_name = str(method).upper()
            if method_name.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            operation_id = f"{method_name} {path}"
            next_operation = next_path_spec.get(method)
            if next_operation is None:
                removed_operations.append(operation_id)
            elif compatibility_policy.get("forbid_changed_operations") and _operation_contract_signature(previous_operation) != _operation_contract_signature(next_operation):
                changed_operations.append(operation_id)
    blockers: list[str] = []
    if removed_paths and compatibility_policy.get("forbid_removed_paths", True):
        blockers.append("removed_paths")
    if removed_operations and compatibility_policy.get("forbid_removed_operations", True):
        blockers.append("removed_operations")
    if changed_operations and compatibility_policy.get("forbid_changed_operations"):
        blockers.append("changed_operations")
    if compatibility_policy.get("require_version_bump") and previous_spec.get("version") == next_spec.get("version"):
        blockers.append("missing_version_bump")
    if blockers and compatibility_policy.get("require_migration_notes") and _blank(next_spec.get("migration_notes")):
        blockers.append("missing_migration_notes")
    compatibility_hash = "openapi-compatibility:" + _digest(
        {
            "blockers": blockers,
            "changed_operations": changed_operations,
            "next_version": next_spec.get("version"),
            "previous_version": previous_spec.get("version"),
            "removed_operations": removed_operations,
            "removed_paths": removed_paths,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return OpenApiCompatibilityReceipt(
        compatible=not blockers,
        removed_paths=removed_paths,
        removed_operations=tuple(sorted(removed_operations)),
        changed_operations=tuple(sorted(changed_operations)),
        blockers=tuple(blockers),
        compatibility_hash=compatibility_hash,
    )


def plan_api_versioning_policy(
    api_contract: Mapping[str, Any],
    version_policy: Mapping[str, Any],
) -> ApiVersioningPlanReceipt:
    """Plan API version movement with changelog, migration, and compatibility gates."""

    raw_api_name = str(api_contract.get("api_name") or api_contract.get("name") or "").strip()
    api_name = normalize_field_name(raw_api_name) if raw_api_name else ""
    current_version = str(api_contract.get("current_version") or "").strip()
    next_version = str(api_contract.get("next_version") or "").strip()
    current_tuple = _parse_semver(current_version)
    next_tuple = _parse_semver(next_version)
    blockers: list[str] = []
    if not api_name:
        blockers.append("missing_api_name")
    if not current_version:
        blockers.append("missing_current_version")
    if not next_version:
        blockers.append("missing_next_version")
    if current_version and next_version and (current_tuple is None or next_tuple is None or next_tuple <= current_tuple):
        blockers.append("version_not_incremented")
    if (
        version_policy.get("require_migration_plan_for_major")
        and current_tuple is not None
        and next_tuple is not None
        and next_tuple[0] > current_tuple[0]
        and _blank(api_contract.get("migration_plan"))
    ):
        blockers.append("major_version_without_migration_plan")
    if version_policy.get("require_changelog") and _blank(api_contract.get("changelog")):
        blockers.append("missing_changelog")
    if version_policy.get("require_compatibility_report") and _blank(api_contract.get("compatibility_report")):
        blockers.append("missing_compatibility_report")
    policy_hash = "api-versioning:" + _digest(
        {
            "api_name": api_name,
            "blockers": blockers,
            "current_version": current_version,
            "next_version": next_version,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiVersioningPlanReceipt(
        ready=not blockers,
        api_name=api_name,
        current_version=current_version,
        next_version=next_version,
        blockers=tuple(blockers),
        policy_hash=policy_hash,
    )


def plan_api_deprecation_notice(
    endpoint_contract: Mapping[str, Any],
    deprecation_policy: Mapping[str, Any],
) -> ApiDeprecationNoticeReceipt:
    """Plan API deprecation notice with sunset and replacement gates."""

    raw_endpoint_id = str(endpoint_contract.get("endpoint_id") or endpoint_contract.get("operation_id") or "").strip()
    endpoint_id = normalize_field_name(raw_endpoint_id) if raw_endpoint_id else ""
    sunset_days = int(endpoint_contract.get("sunset_days") or 0)
    min_sunset_days = int(deprecation_policy.get("min_sunset_days") or 0)
    blockers: list[str] = []
    if not endpoint_id:
        blockers.append("missing_endpoint_id")
    if sunset_days <= 0:
        blockers.append("missing_sunset_days")
    elif min_sunset_days and sunset_days < min_sunset_days:
        blockers.append("sunset_window_too_short")
    if deprecation_policy.get("require_replacement") and _blank(endpoint_contract.get("replacement_endpoint")):
        blockers.append("missing_replacement")
    if deprecation_policy.get("require_docs_url") and _blank(endpoint_contract.get("docs_url")):
        blockers.append("missing_docs_url")
    if deprecation_policy.get("require_sunset_header") and not endpoint_contract.get("sunset_header"):
        blockers.append("missing_sunset_header")
    notice_hash = "api-deprecation:" + _digest(
        {
            "blockers": blockers,
            "endpoint_id": endpoint_id,
            "sunset_days": sunset_days,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiDeprecationNoticeReceipt(
        ready=not blockers,
        endpoint_id=endpoint_id,
        sunset_days=sunset_days,
        blockers=tuple(blockers),
        notice_hash=notice_hash,
    )


def plan_error_envelope_contract(
    endpoint_contract: Mapping[str, Any],
    error_policy: Mapping[str, Any],
) -> ErrorEnvelopeContractReceipt:
    """Plan API error-envelope contract with required fields and code gates."""

    raw_endpoint_id = str(endpoint_contract.get("endpoint_id") or endpoint_contract.get("operation_id") or "").strip()
    endpoint_id = normalize_field_name(raw_endpoint_id) if raw_endpoint_id else ""
    error_schema = endpoint_contract.get("error_schema") if isinstance(endpoint_contract.get("error_schema"), Mapping) else {}
    schema_fields = set(error_schema.keys())
    required_fields = tuple(normalize_field_name(field) for field in _as_sequence(error_policy.get("required_fields")) if not _blank(field))
    blockers: list[str] = []
    if not endpoint_id:
        blockers.append("missing_endpoint_id")
    if not error_schema:
        blockers.append("missing_error_schema")
    for field in required_fields:
        if field not in schema_fields:
            blockers.append(f"missing_required_field:{field}")
    if error_policy.get("require_error_codes") and not _as_sequence(endpoint_contract.get("error_codes")):
        blockers.append("missing_error_codes")
    if error_policy.get("require_correlation_id") and "correlation_id" not in schema_fields:
        blockers.append("missing_correlation_id")
    envelope_hash = "error-envelope:" + _digest(
        {
            "blockers": blockers,
            "endpoint_id": endpoint_id,
            "required_fields": required_fields,
            "schema_fields": sorted(schema_fields),
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ErrorEnvelopeContractReceipt(
        ready=not blockers,
        endpoint_id=endpoint_id,
        required_fields=required_fields,
        blockers=tuple(blockers),
        envelope_hash=envelope_hash,
    )


def plan_request_signing_policy(
    endpoint_contract: Mapping[str, Any],
    signing_policy: Mapping[str, Any],
) -> RequestSigningPolicyReceipt:
    """Plan request signing with algorithm, header, replay, and rotation gates."""

    raw_endpoint_id = str(endpoint_contract.get("endpoint_id") or endpoint_contract.get("operation_id") or "").strip()
    endpoint_id = normalize_field_name(raw_endpoint_id) if raw_endpoint_id else ""
    algorithm = str(endpoint_contract.get("algorithm") or "").strip()
    required_headers = tuple(str(header).strip() for header in _as_sequence(endpoint_contract.get("required_headers")) if str(header).strip())
    normalized_headers = {header.lower() for header in required_headers}
    allowed_algorithms = {str(value).strip() for value in _as_sequence(signing_policy.get("allowed_algorithms")) if str(value).strip()}
    replay_window_seconds = int(endpoint_contract.get("replay_window_seconds") or 0)
    blockers: list[str] = []
    if not endpoint_id:
        blockers.append("missing_endpoint_id")
    if not algorithm:
        blockers.append("missing_algorithm")
    elif allowed_algorithms and algorithm not in allowed_algorithms:
        blockers.append(f"algorithm_not_allowed:{algorithm}")
    for header in _as_sequence(signing_policy.get("required_headers")):
        header_name = str(header).strip()
        if header_name and header_name.lower() not in normalized_headers:
            blockers.append(f"missing_header:{header_name}")
    timestamp_header = str(signing_policy.get("timestamp_header") or "").strip()
    if signing_policy.get("require_timestamp") and (not timestamp_header or timestamp_header.lower() not in normalized_headers):
        blockers.append("missing_timestamp_header")
    nonce_header = str(signing_policy.get("nonce_header") or "").strip()
    if signing_policy.get("require_nonce") and (not nonce_header or nonce_header.lower() not in normalized_headers):
        blockers.append("missing_nonce_header")
    if signing_policy.get("require_key_rotation") and _blank(endpoint_contract.get("key_rotation")):
        blockers.append("missing_key_rotation")
    max_replay_window_seconds = int(signing_policy.get("max_replay_window_seconds") or 0)
    if replay_window_seconds <= 0:
        blockers.append("missing_replay_window_seconds")
    elif max_replay_window_seconds and replay_window_seconds > max_replay_window_seconds:
        blockers.append("replay_window_exceeds_policy")
    policy_hash = "request-signing:" + _digest(
        {
            "algorithm": algorithm,
            "blockers": blockers,
            "endpoint_id": endpoint_id,
            "replay_window_seconds": replay_window_seconds,
            "required_headers": required_headers,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return RequestSigningPolicyReceipt(
        ready=not blockers,
        endpoint_id=endpoint_id,
        algorithm=algorithm,
        required_headers=required_headers,
        blockers=tuple(blockers),
        policy_hash=policy_hash,
    )


def plan_api_usage_plan(
    consumer_contract: Mapping[str, Any],
    usage_policy: Mapping[str, Any],
) -> ApiUsagePlanReceipt:
    """Plan API consumer quota, burst, period, scope, and alert gates."""

    raw_consumer_name = str(consumer_contract.get("consumer_name") or consumer_contract.get("name") or "").strip()
    consumer_name = normalize_field_name(raw_consumer_name) if raw_consumer_name else ""
    quota_limit = int(consumer_contract.get("quota_limit") or consumer_contract.get("limit") or 0)
    period = normalize_field_name(consumer_contract.get("period") or "")
    allowed_periods = {normalize_field_name(value) for value in _as_sequence(usage_policy.get("allowed_periods")) if not _blank(value)}
    blockers: list[str] = []
    if not consumer_name:
        blockers.append("missing_consumer_name")
    if quota_limit <= 0:
        blockers.append("missing_quota_limit")
    max_quota_limit = int(usage_policy.get("max_quota_limit") or 0)
    if max_quota_limit and quota_limit > max_quota_limit:
        blockers.append("quota_exceeds_policy")
    if not period or period == "field":
        blockers.append("missing_period")
    elif allowed_periods and period not in allowed_periods:
        blockers.append(f"period_not_allowed:{period}")
    if usage_policy.get("require_burst_limit") and int(consumer_contract.get("burst_limit") or 0) <= 0:
        blockers.append("missing_burst_limit")
    if usage_policy.get("require_scope") and not _as_sequence(consumer_contract.get("scopes")):
        blockers.append("missing_scope")
    if usage_policy.get("require_alert_threshold") and int(consumer_contract.get("alert_threshold_percent") or 0) <= 0:
        blockers.append("missing_alert_threshold")
    plan_hash = "api-usage-plan:" + _digest(
        {
            "blockers": blockers,
            "consumer_name": consumer_name,
            "period": period,
            "quota_limit": quota_limit,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiUsagePlanReceipt(
        ready=not blockers,
        consumer_name=consumer_name,
        quota_limit=quota_limit,
        period=period,
        blockers=tuple(blockers),
        plan_hash=plan_hash,
    )


def plan_api_key_rotation(
    key_contract: Mapping[str, Any],
    rotation_policy: Mapping[str, Any],
) -> ApiKeyRotationPlanReceipt:
    """Plan API key rotation with secret reference, overlap, owner, and revoke gates."""

    raw_key_name = str(key_contract.get("key_name") or key_contract.get("name") or "").strip()
    key_name = normalize_field_name(raw_key_name) if raw_key_name else ""
    rotation_days = int(key_contract.get("rotation_days") or 0)
    overlap_window_days = int(key_contract.get("overlap_window_days") or 0)
    blockers: list[str] = []
    if not key_name:
        blockers.append("missing_key_name")
    if _blank(key_contract.get("secret_ref")):
        blockers.append("missing_secret_ref")
    if rotation_days <= 0:
        blockers.append("missing_rotation_days")
    max_rotation_days = int(rotation_policy.get("max_rotation_days") or 0)
    if max_rotation_days and rotation_days > max_rotation_days:
        blockers.append("rotation_days_exceeds_policy")
    if rotation_policy.get("require_overlap_window") and overlap_window_days <= 0:
        blockers.append("missing_overlap_window_days")
    max_overlap_window_days = int(rotation_policy.get("max_overlap_window_days") or 0)
    if max_overlap_window_days and overlap_window_days > max_overlap_window_days:
        blockers.append("overlap_window_exceeds_policy")
    if rotation_policy.get("require_revocation_plan") and _blank(key_contract.get("revocation_plan")):
        blockers.append("missing_revocation_plan")
    if rotation_policy.get("require_owner") and _blank(key_contract.get("owner")):
        blockers.append("missing_owner")
    rotation_hash = "api-key-rotation:" + _digest(
        {
            "blockers": blockers,
            "key_name": key_name,
            "overlap_window_days": overlap_window_days,
            "rotation_days": rotation_days,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiKeyRotationPlanReceipt(
        ready=not blockers,
        key_name=key_name,
        rotation_days=rotation_days,
        blockers=tuple(blockers),
        rotation_hash=rotation_hash,
    )


def plan_response_cache_policy(
    endpoint_contract: Mapping[str, Any],
    cache_policy: Mapping[str, Any],
) -> ResponseCachePolicyReceipt:
    """Plan response cache policy with TTL, vary, privacy, and invalidation gates."""

    raw_endpoint_id = str(endpoint_contract.get("endpoint_id") or endpoint_contract.get("operation_id") or "").strip()
    endpoint_id = normalize_field_name(raw_endpoint_id) if raw_endpoint_id else ""
    cache_ttl_seconds = int(endpoint_contract.get("cache_ttl_seconds") or endpoint_contract.get("ttl_seconds") or 0)
    vary_headers = tuple(str(header).strip() for header in _as_sequence(endpoint_contract.get("vary_headers")) if str(header).strip())
    normalized_vary_headers = {header.lower() for header in vary_headers}
    blockers: list[str] = []
    if not endpoint_id:
        blockers.append("missing_endpoint_id")
    if cache_ttl_seconds <= 0:
        blockers.append("missing_cache_ttl_seconds")
    max_cache_ttl_seconds = int(cache_policy.get("max_cache_ttl_seconds") or 0)
    if max_cache_ttl_seconds and cache_ttl_seconds > max_cache_ttl_seconds:
        blockers.append("ttl_exceeds_policy")
    for header in _as_sequence(cache_policy.get("required_vary_headers")):
        header_name = str(header).strip()
        if header_name and header_name.lower() not in normalized_vary_headers:
            blockers.append(f"missing_vary_header:{header_name}")
    if cache_policy.get("require_invalidation_strategy") and _blank(endpoint_contract.get("invalidation_strategy")):
        blockers.append("missing_invalidation_strategy")
    if endpoint_contract.get("cache_scope") == "private" and cache_policy.get("require_auth_context_for_private") and _blank(endpoint_contract.get("auth_context_key")):
        blockers.append("private_cache_missing_auth_context")
    cache_hash = "response-cache:" + _digest(
        {
            "blockers": blockers,
            "cache_ttl_seconds": cache_ttl_seconds,
            "endpoint_id": endpoint_id,
            "vary_headers": vary_headers,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ResponseCachePolicyReceipt(
        ready=not blockers,
        endpoint_id=endpoint_id,
        cache_ttl_seconds=cache_ttl_seconds,
        vary_headers=vary_headers,
        blockers=tuple(blockers),
        cache_hash=cache_hash,
    )


def plan_api_request_validation(
    endpoint_contract: Mapping[str, Any],
    validation_policy: Mapping[str, Any],
) -> ApiRequestValidationPlanReceipt:
    """Plan endpoint request validation with schema, content-type, size, and receipt gates."""

    raw_endpoint_id = str(endpoint_contract.get("endpoint_id") or endpoint_contract.get("operation_id") or "").strip()
    endpoint_id = normalize_field_name(raw_endpoint_id) if raw_endpoint_id else ""
    method = str(endpoint_contract.get("method") or "").strip().upper()
    content_types = tuple(str(value).strip() for value in _as_sequence(endpoint_contract.get("content_types") or endpoint_contract.get("consumes")) if str(value).strip())
    normalized_content_types = {value.lower() for value in content_types}
    request_schema = endpoint_contract.get("request_schema") if isinstance(endpoint_contract.get("request_schema"), Mapping) else {}
    schema_required_fields = {
        normalize_field_name(value)
        for value in _as_sequence(request_schema.get("required")) if not _blank(value)
    }
    schema_properties = {
        normalize_field_name(value)
        for value in (request_schema.get("properties") if isinstance(request_schema.get("properties"), Mapping) else {}).keys()
        if not _blank(value)
    }
    required_fields = tuple(
        normalize_field_name(value)
        for value in _as_sequence(validation_policy.get("required_fields"))
        if not _blank(value)
    )
    allowed_methods = {str(value).strip().upper() for value in _as_sequence(validation_policy.get("allowed_methods")) if str(value).strip()}
    allowed_content_types = {str(value).strip().lower() for value in _as_sequence(validation_policy.get("allowed_content_types")) if str(value).strip()}
    max_body_bytes = int(endpoint_contract.get("max_body_bytes") or endpoint_contract.get("max_request_bytes") or 0)
    policy_max_body_bytes = int(validation_policy.get("max_body_bytes") or validation_policy.get("max_request_bytes") or 0)
    blockers: list[str] = []
    if not endpoint_id:
        blockers.append("missing_endpoint_id")
    if not method:
        blockers.append("missing_method")
    elif allowed_methods and method not in allowed_methods:
        blockers.append(f"method_not_allowed:{method}")
    if not request_schema:
        blockers.append("missing_request_schema")
    if not content_types:
        blockers.append("missing_content_type")
    for content_type in content_types:
        if allowed_content_types and content_type.lower() not in allowed_content_types:
            blockers.append(f"content_type_not_allowed:{content_type}")
    for field in required_fields:
        if field not in schema_required_fields:
            blockers.append(f"missing_required_field:{field}")
        if schema_properties and field not in schema_properties:
            blockers.append(f"field_not_in_schema:{field}")
    if validation_policy.get("require_unknown_field_policy") and _blank(endpoint_contract.get("unknown_field_policy")):
        blockers.append("missing_unknown_field_policy")
    if validation_policy.get("require_max_body_bytes") and max_body_bytes <= 0:
        blockers.append("missing_max_body_bytes")
    elif policy_max_body_bytes and max_body_bytes > policy_max_body_bytes:
        blockers.append("max_body_exceeds_policy")
    if validation_policy.get("require_validation_receipt") and _blank(endpoint_contract.get("validation_receipt")):
        blockers.append("missing_validation_receipt")
    validation_hash = "api-request-validation:" + _digest(
        {
            "blockers": blockers,
            "content_types": content_types,
            "endpoint_id": endpoint_id,
            "method": method,
            "required_fields": required_fields,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiRequestValidationPlanReceipt(
        ready=not blockers,
        endpoint_id=endpoint_id,
        method=method,
        content_types=content_types,
        required_fields=required_fields,
        blockers=tuple(blockers),
        validation_hash=validation_hash,
    )


def plan_api_auth_scope_matrix(
    endpoint_contract: Mapping[str, Any],
    auth_policy: Mapping[str, Any],
) -> ApiAuthScopeMatrixPlanReceipt:
    """Plan endpoint authorization matrix with scopes, tenant claims, roles, and denied examples."""

    raw_endpoint_id = str(endpoint_contract.get("endpoint_id") or endpoint_contract.get("operation_id") or "").strip()
    endpoint_id = normalize_field_name(raw_endpoint_id) if raw_endpoint_id else ""
    action = normalize_field_name(endpoint_contract.get("action") or "")
    required_scopes = tuple(str(value).strip() for value in _as_sequence(endpoint_contract.get("required_scopes") or endpoint_contract.get("scopes")) if str(value).strip())
    tenant_claims = tuple(normalize_field_name(value) for value in _as_sequence(endpoint_contract.get("tenant_claims")) if not _blank(value))
    allowed_scopes = {str(value).strip() for value in _as_sequence(auth_policy.get("allowed_scopes")) if str(value).strip()}
    required_tenant_claims = tuple(normalize_field_name(value) for value in _as_sequence(auth_policy.get("required_tenant_claims")) if not _blank(value))
    blockers: list[str] = []
    if not endpoint_id:
        blockers.append("missing_endpoint_id")
    if not action or action == "field":
        blockers.append("missing_action")
    if not required_scopes:
        blockers.append("missing_required_scopes")
    for scope in required_scopes:
        if allowed_scopes and scope not in allowed_scopes:
            blockers.append(f"scope_not_allowed:{scope}")
    for claim in required_tenant_claims:
        if claim not in tenant_claims:
            blockers.append(f"missing_tenant_claim:{claim}")
    if auth_policy.get("require_role_mapping") and _blank(endpoint_contract.get("role_mapping")):
        blockers.append("missing_role_mapping")
    if auth_policy.get("require_denied_case_examples") and not _as_sequence(endpoint_contract.get("denied_case_examples")):
        blockers.append("missing_denied_case_examples")
    matrix_hash = "api-auth-scope-matrix:" + _digest(
        {
            "action": action,
            "blockers": blockers,
            "endpoint_id": endpoint_id,
            "required_scopes": required_scopes,
            "tenant_claims": tenant_claims,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiAuthScopeMatrixPlanReceipt(
        ready=not blockers,
        endpoint_id=endpoint_id,
        action=action,
        required_scopes=required_scopes,
        tenant_claims=tenant_claims,
        blockers=tuple(blockers),
        matrix_hash=matrix_hash,
    )


def plan_api_async_job_endpoint(
    endpoint_contract: Mapping[str, Any],
    async_policy: Mapping[str, Any],
) -> ApiAsyncJobEndpointPlanReceipt:
    """Plan async endpoint behavior with job id, status route, cancel route, TTL, and receipts."""

    raw_endpoint_id = str(endpoint_contract.get("endpoint_id") or endpoint_contract.get("operation_id") or "").strip()
    endpoint_id = normalize_field_name(raw_endpoint_id) if raw_endpoint_id else ""
    status_endpoint = str(endpoint_contract.get("status_endpoint") or "").strip()
    completion_states = tuple(normalize_field_name(value) for value in _as_sequence(endpoint_contract.get("completion_states")) if not _blank(value))
    result_ttl_seconds = int(endpoint_contract.get("result_ttl_seconds") or 0)
    max_result_ttl_seconds = int(async_policy.get("max_result_ttl_seconds") or 0)
    blockers: list[str] = []
    if not endpoint_id:
        blockers.append("missing_endpoint_id")
    if _blank(endpoint_contract.get("job_id_field")):
        blockers.append("missing_job_id_field")
    if not status_endpoint:
        blockers.append("missing_status_endpoint")
    if not completion_states:
        blockers.append("missing_completion_states")
    for state in _as_sequence(async_policy.get("required_completion_states")):
        state_name = normalize_field_name(state)
        if state_name and state_name not in completion_states:
            blockers.append(f"missing_completion_state:{state_name}")
    if async_policy.get("require_cancel_endpoint") and _blank(endpoint_contract.get("cancel_endpoint")):
        blockers.append("missing_cancel_endpoint")
    if async_policy.get("require_result_ttl") and result_ttl_seconds <= 0:
        blockers.append("missing_result_ttl_seconds")
    elif max_result_ttl_seconds and result_ttl_seconds > max_result_ttl_seconds:
        blockers.append("result_ttl_exceeds_policy")
    if async_policy.get("require_polling_guidance") and _blank(endpoint_contract.get("polling_guidance")):
        blockers.append("missing_polling_guidance")
    if async_policy.get("require_job_receipt") and _blank(endpoint_contract.get("job_receipt")):
        blockers.append("missing_job_receipt")
    job_hash = "api-async-job-endpoint:" + _digest(
        {
            "blockers": blockers,
            "completion_states": completion_states,
            "endpoint_id": endpoint_id,
            "status_endpoint": status_endpoint,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiAsyncJobEndpointPlanReceipt(
        ready=not blockers,
        endpoint_id=endpoint_id,
        status_endpoint=status_endpoint,
        completion_states=completion_states,
        blockers=tuple(blockers),
        job_hash=job_hash,
    )


def plan_api_bulk_operation(
    endpoint_contract: Mapping[str, Any],
    bulk_policy: Mapping[str, Any],
) -> ApiBulkOperationPlanReceipt:
    """Plan bulk endpoint behavior with batch limits, partial failures, idempotency, and item results."""

    raw_endpoint_id = str(endpoint_contract.get("endpoint_id") or endpoint_contract.get("operation_id") or "").strip()
    endpoint_id = normalize_field_name(raw_endpoint_id) if raw_endpoint_id else ""
    max_batch_size = int(endpoint_contract.get("max_batch_size") or endpoint_contract.get("batch_size") or 0)
    policy_max_batch_size = int(bulk_policy.get("max_batch_size") or 0)
    partial_failure_mode = normalize_field_name(endpoint_contract.get("partial_failure_mode") or "")
    allowed_partial_failure_modes = {normalize_field_name(value) for value in _as_sequence(bulk_policy.get("allowed_partial_failure_modes")) if not _blank(value)}
    result_item_schema = endpoint_contract.get("result_item_schema") if isinstance(endpoint_contract.get("result_item_schema"), Mapping) else {}
    per_item_error_schema = endpoint_contract.get("per_item_error_schema") if isinstance(endpoint_contract.get("per_item_error_schema"), Mapping) else {}
    blockers: list[str] = []
    if not endpoint_id:
        blockers.append("missing_endpoint_id")
    if max_batch_size <= 0:
        blockers.append("missing_max_batch_size")
    elif policy_max_batch_size and max_batch_size > policy_max_batch_size:
        blockers.append("max_batch_size_exceeds_policy")
    if not partial_failure_mode or partial_failure_mode == "field":
        blockers.append("missing_partial_failure_mode")
    elif allowed_partial_failure_modes and partial_failure_mode not in allowed_partial_failure_modes:
        blockers.append(f"partial_failure_mode_not_allowed:{partial_failure_mode}")
    if bulk_policy.get("require_idempotency_key_field") and _blank(endpoint_contract.get("idempotency_key_field")):
        blockers.append("missing_idempotency_key_field")
    if bulk_policy.get("require_result_item_schema") and not result_item_schema:
        blockers.append("missing_result_item_schema")
    if bulk_policy.get("require_per_item_error_schema") and not per_item_error_schema:
        blockers.append("missing_per_item_error_schema")
    if bulk_policy.get("require_atomicity_policy") and _blank(endpoint_contract.get("atomicity_policy")):
        blockers.append("missing_atomicity_policy")
    bulk_hash = "api-bulk-operation:" + _digest(
        {
            "blockers": blockers,
            "endpoint_id": endpoint_id,
            "max_batch_size": max_batch_size,
            "partial_failure_mode": partial_failure_mode,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiBulkOperationPlanReceipt(
        ready=not blockers,
        endpoint_id=endpoint_id,
        max_batch_size=max_batch_size,
        partial_failure_mode=partial_failure_mode,
        blockers=tuple(blockers),
        bulk_hash=bulk_hash,
    )


def plan_api_operation_example_coverage(
    endpoint_contract: Mapping[str, Any],
    coverage_policy: Mapping[str, Any],
) -> ApiOperationExampleCoverageReceipt:
    """Plan API example coverage for status codes, request/response examples, and negative cases."""

    raw_endpoint_id = str(endpoint_contract.get("endpoint_id") or endpoint_contract.get("operation_id") or "").strip()
    endpoint_id = normalize_field_name(raw_endpoint_id) if raw_endpoint_id else ""
    examples = tuple(dict(item) for item in _as_mapping_sequence(endpoint_contract.get("examples")))
    covered_status_codes = tuple(
        sorted(
            {
                str(example.get("status_code") or example.get("status") or "").strip()
                for example in examples
                if str(example.get("status_code") or example.get("status") or "").strip()
            }
        )
    )
    covered_example_types = tuple(
        sorted(
            {
                normalize_field_name(example.get("type") or example.get("case_type") or "")
                for example in examples
                if not _blank(example.get("type") or example.get("case_type"))
            }
        )
    )
    blockers: list[str] = []
    if not endpoint_id:
        blockers.append("missing_endpoint_id")
    if not examples:
        blockers.append("missing_examples")
    for status_code in _as_sequence(coverage_policy.get("required_status_codes")):
        code = str(status_code).strip()
        if code and code not in covered_status_codes:
            blockers.append(f"missing_status_example:{code}")
    for example_type in _as_sequence(coverage_policy.get("required_example_types")):
        type_name = normalize_field_name(example_type)
        if type_name and type_name not in covered_example_types:
            blockers.append(f"missing_example_type:{type_name}")
    if coverage_policy.get("require_request_example") and not any("request" in example for example in examples):
        blockers.append("missing_request_example")
    if coverage_policy.get("require_response_example") and not any("response" in example for example in examples):
        blockers.append("missing_response_example")
    coverage_hash = "api-example-coverage:" + _digest(
        {
            "blockers": blockers,
            "covered_example_types": covered_example_types,
            "covered_status_codes": covered_status_codes,
            "endpoint_id": endpoint_id,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiOperationExampleCoverageReceipt(
        ready=not blockers,
        endpoint_id=endpoint_id,
        covered_status_codes=covered_status_codes,
        covered_example_types=covered_example_types,
        blockers=tuple(blockers),
        coverage_hash=coverage_hash,
    )


def plan_api_endpoint_telemetry(
    endpoint_contract: Mapping[str, Any],
    telemetry_policy: Mapping[str, Any],
) -> ApiEndpointTelemetryPlanReceipt:
    """Plan endpoint telemetry with route span, metrics, trace context, and sensitive-field redaction."""

    raw_endpoint_id = str(endpoint_contract.get("endpoint_id") or endpoint_contract.get("operation_id") or "").strip()
    endpoint_id = normalize_field_name(raw_endpoint_id) if raw_endpoint_id else ""
    span_name = str(endpoint_contract.get("span_name") or "").strip()
    metrics = tuple(str(value).strip() for value in _as_sequence(endpoint_contract.get("metrics")) if str(value).strip())
    metric_set = set(metrics)
    redacted_fields = tuple(normalize_field_name(value) for value in _as_sequence(endpoint_contract.get("redacted_fields")) if not _blank(value))
    redacted_field_set = set(redacted_fields)
    log_fields = {normalize_field_name(value) for value in _as_sequence(endpoint_contract.get("log_fields")) if not _blank(value)}
    attribute_fields = {normalize_field_name(value) for value in _as_sequence(endpoint_contract.get("attribute_fields")) if not _blank(value)}
    sensitive_fields = tuple(normalize_field_name(value) for value in _as_sequence(telemetry_policy.get("sensitive_fields")) if not _blank(value))
    blockers: list[str] = []
    if not endpoint_id:
        blockers.append("missing_endpoint_id")
    if telemetry_policy.get("require_span_name") and not span_name:
        blockers.append("missing_span_name")
    for metric in _as_sequence(telemetry_policy.get("required_metrics")):
        metric_name = str(metric).strip()
        if metric_name and metric_name not in metric_set:
            blockers.append(f"missing_metric:{metric_name}")
    if telemetry_policy.get("require_trace_context") and not endpoint_contract.get("trace_context"):
        blockers.append("missing_trace_context")
    if telemetry_policy.get("require_latency_buckets") and _blank(endpoint_contract.get("latency_bucket_policy")):
        blockers.append("missing_latency_bucket_policy")
    exposed_fields = log_fields | attribute_fields
    for field in sensitive_fields:
        if field in exposed_fields and field not in redacted_field_set:
            blockers.append(f"missing_redaction_for_field:{field}")
    telemetry_hash = "api-endpoint-telemetry:" + _digest(
        {
            "blockers": blockers,
            "endpoint_id": endpoint_id,
            "metrics": metrics,
            "span_name": span_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiEndpointTelemetryPlanReceipt(
        ready=not blockers,
        endpoint_id=endpoint_id,
        span_name=span_name,
        metrics=metrics,
        redacted_fields=redacted_fields,
        blockers=tuple(blockers),
        telemetry_hash=telemetry_hash,
    )


def plan_cdc_capture(
    source_spec: Mapping[str, Any],
    capture_policy: Mapping[str, Any],
) -> CdcCapturePlanReceipt:
    """Plan CDC capture with cursor, primary key, snapshot, and checkpoint gates."""

    raw_source_name = str(source_spec.get("source_name") or source_spec.get("name") or "").strip()
    source_name = normalize_field_name(raw_source_name) if raw_source_name else ""
    cursor_field = normalize_field_name(source_spec.get("cursor_field") or "") if not _blank(source_spec.get("cursor_field")) else ""
    primary_key_fields = tuple(normalize_field_name(field) for field in _as_sequence(source_spec.get("primary_key_fields")) if not _blank(field))
    max_lag_seconds = int(capture_policy.get("max_lag_seconds") or 0)
    observed_lag_seconds = int(source_spec.get("observed_lag_seconds") or 0)
    blockers: list[str] = []
    if not source_name:
        blockers.append("missing_source_name")
    if not cursor_field:
        blockers.append("missing_cursor_field")
    if not primary_key_fields:
        blockers.append("missing_primary_key_fields")
    if max_lag_seconds and observed_lag_seconds > max_lag_seconds:
        blockers.append("lag_exceeds_policy")
    if capture_policy.get("require_initial_snapshot") and _blank(source_spec.get("initial_snapshot")):
        blockers.append("missing_initial_snapshot")
    if capture_policy.get("require_checkpoint") and _blank(source_spec.get("checkpoint")):
        blockers.append("missing_checkpoint")
    if capture_policy.get("require_schema_registry") and _blank(source_spec.get("schema_registry")):
        blockers.append("missing_schema_registry")
    capture_hash = "cdc-capture:" + _digest(
        {
            "blockers": blockers,
            "cursor_field": cursor_field,
            "observed_lag_seconds": observed_lag_seconds,
            "primary_key_fields": primary_key_fields,
            "source_name": source_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return CdcCapturePlanReceipt(
        ready=not blockers,
        source_name=source_name,
        cursor_field=cursor_field,
        primary_key_fields=primary_key_fields,
        blockers=tuple(blockers),
        capture_hash=capture_hash,
    )


def plan_stream_watermark(
    stream_spec: Mapping[str, Any],
    watermark_policy: Mapping[str, Any],
) -> StreamWatermarkPlanReceipt:
    """Plan stream watermark behavior with lateness, sink, and skew gates."""

    raw_stream_name = str(stream_spec.get("stream_name") or stream_spec.get("name") or "").strip()
    stream_name = normalize_field_name(raw_stream_name) if raw_stream_name else ""
    event_time_field = normalize_field_name(stream_spec.get("event_time_field") or "") if not _blank(stream_spec.get("event_time_field")) else ""
    allowed_lateness_seconds = int(stream_spec.get("allowed_lateness_seconds") or 0)
    max_allowed_lateness_seconds = int(watermark_policy.get("max_allowed_lateness_seconds") or 0)
    blockers: list[str] = []
    if not stream_name:
        blockers.append("missing_stream_name")
    if not event_time_field:
        blockers.append("missing_event_time_field")
    if _blank(stream_spec.get("watermark_strategy")):
        blockers.append("missing_watermark_strategy")
    if allowed_lateness_seconds <= 0:
        blockers.append("missing_allowed_lateness_seconds")
    elif max_allowed_lateness_seconds and allowed_lateness_seconds > max_allowed_lateness_seconds:
        blockers.append("lateness_exceeds_policy")
    if watermark_policy.get("require_late_event_sink") and _blank(stream_spec.get("late_event_sink")):
        blockers.append("missing_late_event_sink")
    if watermark_policy.get("require_clock_skew_policy") and _blank(stream_spec.get("clock_skew_policy")):
        blockers.append("missing_clock_skew_policy")
    watermark_hash = "stream-watermark:" + _digest(
        {
            "allowed_lateness_seconds": allowed_lateness_seconds,
            "blockers": blockers,
            "event_time_field": event_time_field,
            "stream_name": stream_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return StreamWatermarkPlanReceipt(
        ready=not blockers,
        stream_name=stream_name,
        event_time_field=event_time_field,
        allowed_lateness_seconds=allowed_lateness_seconds,
        blockers=tuple(blockers),
        watermark_hash=watermark_hash,
    )


def plan_partition_strategy(
    dataset_spec: Mapping[str, Any],
    partition_policy: Mapping[str, Any],
) -> PartitionStrategyPlanReceipt:
    """Plan dataset partitioning with retention, compaction, and skew guards."""

    raw_dataset_name = str(dataset_spec.get("dataset_name") or dataset_spec.get("name") or "").strip()
    dataset_name = normalize_field_name(raw_dataset_name) if raw_dataset_name else ""
    partition_fields = tuple(normalize_field_name(field) for field in _as_sequence(dataset_spec.get("partition_fields")) if not _blank(field))
    allowed_partition_fields = {normalize_field_name(field) for field in _as_sequence(partition_policy.get("allowed_partition_fields")) if not _blank(field)}
    retention_days = int(dataset_spec.get("retention_days") or 0)
    blockers: list[str] = []
    if not dataset_name:
        blockers.append("missing_dataset_name")
    if not partition_fields:
        blockers.append("missing_partition_fields")
    for field in partition_fields:
        if allowed_partition_fields and field not in allowed_partition_fields:
            blockers.append(f"partition_field_not_allowed:{field}")
    if partition_policy.get("require_retention") and retention_days <= 0:
        blockers.append("missing_retention_days")
    max_retention_days = int(partition_policy.get("max_retention_days") or 0)
    if max_retention_days and retention_days > max_retention_days:
        blockers.append("retention_exceeds_policy")
    if partition_policy.get("require_hot_partition_guard") and _blank(dataset_spec.get("hot_partition_guard")):
        blockers.append("missing_hot_partition_guard")
    if partition_policy.get("require_compaction_policy") and _blank(dataset_spec.get("compaction_policy")):
        blockers.append("missing_compaction_policy")
    strategy_hash = "partition-strategy:" + _digest(
        {
            "blockers": blockers,
            "dataset_name": dataset_name,
            "partition_fields": partition_fields,
            "retention_days": retention_days,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PartitionStrategyPlanReceipt(
        ready=not blockers,
        dataset_name=dataset_name,
        partition_fields=partition_fields,
        retention_days=retention_days,
        blockers=tuple(blockers),
        strategy_hash=strategy_hash,
    )


def plan_data_lineage_contract(
    lineage_spec: Mapping[str, Any],
    lineage_policy: Mapping[str, Any],
) -> DataLineageContractReceipt:
    """Plan data lineage contract with owner, run, freshness, and column lineage gates."""

    raw_dataset_name = str(lineage_spec.get("dataset_name") or lineage_spec.get("name") or "").strip()
    dataset_name = normalize_field_name(raw_dataset_name) if raw_dataset_name else ""
    inputs = tuple(str(value).strip() for value in _as_sequence(lineage_spec.get("inputs")) if str(value).strip())
    outputs = tuple(str(value).strip() for value in _as_sequence(lineage_spec.get("outputs")) if str(value).strip())
    blockers: list[str] = []
    if not dataset_name:
        blockers.append("missing_dataset_name")
    if not inputs:
        blockers.append("missing_inputs")
    if not outputs:
        blockers.append("missing_outputs")
    if lineage_policy.get("require_owner") and _blank(lineage_spec.get("owner")):
        blockers.append("missing_owner")
    if lineage_policy.get("require_column_lineage") and not isinstance(lineage_spec.get("column_lineage"), Mapping):
        blockers.append("missing_column_lineage")
    if lineage_policy.get("require_run_id") and _blank(lineage_spec.get("run_id")):
        blockers.append("missing_run_id")
    if lineage_policy.get("require_source_freshness_ref") and _blank(lineage_spec.get("source_freshness_ref")):
        blockers.append("missing_source_freshness_ref")
    lineage_hash = "data-lineage:" + _digest(
        {
            "blockers": blockers,
            "dataset_name": dataset_name,
            "inputs": inputs,
            "outputs": outputs,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DataLineageContractReceipt(
        ready=not blockers,
        dataset_name=dataset_name,
        inputs=inputs,
        outputs=outputs,
        blockers=tuple(blockers),
        lineage_hash=lineage_hash,
    )


def plan_outbox_publication(
    outbox_spec: Mapping[str, Any],
    outbox_policy: Mapping[str, Any],
) -> OutboxPublicationPlanReceipt:
    """Plan transactional outbox publication with checkpoint, idempotency, and receipt gates."""

    raw_aggregate_name = str(outbox_spec.get("aggregate_name") or outbox_spec.get("name") or "").strip()
    aggregate_name = normalize_field_name(raw_aggregate_name) if raw_aggregate_name else ""
    event_topic = str(outbox_spec.get("event_topic") or "").strip()
    outbox_table = str(outbox_spec.get("outbox_table") or "").strip()
    blockers: list[str] = []
    if not aggregate_name:
        blockers.append("missing_aggregate_name")
    if not event_topic:
        blockers.append("missing_event_topic")
    if not outbox_table:
        blockers.append("missing_outbox_table")
    if outbox_policy.get("require_transaction_boundary") and _blank(outbox_spec.get("transaction_boundary")):
        blockers.append("missing_transaction_boundary")
    if outbox_policy.get("require_idempotency_key") and _blank(outbox_spec.get("idempotency_key")):
        blockers.append("missing_idempotency_key")
    if outbox_policy.get("require_poller_checkpoint") and _blank(outbox_spec.get("poller_checkpoint")):
        blockers.append("missing_poller_checkpoint")
    if outbox_policy.get("require_publish_receipt") and _blank(outbox_spec.get("publish_receipt")):
        blockers.append("missing_publish_receipt")
    if outbox_policy.get("require_retry_policy") and _blank(outbox_spec.get("retry_policy")):
        blockers.append("missing_retry_policy")
    publication_hash = "outbox-publication:" + _digest(
        {
            "aggregate_name": aggregate_name,
            "blockers": blockers,
            "event_topic": event_topic,
            "outbox_table": outbox_table,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return OutboxPublicationPlanReceipt(
        ready=not blockers,
        aggregate_name=aggregate_name,
        event_topic=event_topic,
        outbox_table=outbox_table,
        blockers=tuple(blockers),
        publication_hash=publication_hash,
    )


def plan_inbox_deduplication(
    inbox_spec: Mapping[str, Any],
    inbox_policy: Mapping[str, Any],
) -> InboxDeduplicationPlanReceipt:
    """Plan inbox deduplication with TTL, conflict, processed receipt, and replay gates."""

    raw_consumer_name = str(inbox_spec.get("consumer_name") or inbox_spec.get("name") or "").strip()
    consumer_name = normalize_field_name(raw_consumer_name) if raw_consumer_name else ""
    dedupe_key = normalize_field_name(inbox_spec.get("dedupe_key") or "") if not _blank(inbox_spec.get("dedupe_key")) else ""
    ttl_seconds = int(inbox_spec.get("ttl_seconds") or 0)
    blockers: list[str] = []
    if not consumer_name:
        blockers.append("missing_consumer_name")
    if not dedupe_key:
        blockers.append("missing_dedupe_key")
    if ttl_seconds <= 0:
        blockers.append("missing_ttl_seconds")
    max_ttl_seconds = int(inbox_policy.get("max_ttl_seconds") or 0)
    if max_ttl_seconds and ttl_seconds > max_ttl_seconds:
        blockers.append("ttl_exceeds_policy")
    if inbox_policy.get("require_conflict_action") and _blank(inbox_spec.get("conflict_action")):
        blockers.append("missing_conflict_action")
    if inbox_policy.get("require_processed_receipt") and _blank(inbox_spec.get("processed_receipt")):
        blockers.append("missing_processed_receipt")
    if inbox_policy.get("require_replay_guard") and _blank(inbox_spec.get("replay_guard")):
        blockers.append("missing_replay_guard")
    dedupe_hash = "inbox-deduplication:" + _digest(
        {
            "blockers": blockers,
            "consumer_name": consumer_name,
            "dedupe_key": dedupe_key,
            "ttl_seconds": ttl_seconds,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return InboxDeduplicationPlanReceipt(
        ready=not blockers,
        consumer_name=consumer_name,
        dedupe_key=dedupe_key,
        ttl_seconds=ttl_seconds,
        blockers=tuple(blockers),
        dedupe_hash=dedupe_hash,
    )


def plan_materialized_view_refresh(
    view_spec: Mapping[str, Any],
    refresh_policy: Mapping[str, Any],
) -> MaterializedViewRefreshPlanReceipt:
    """Plan materialized-view refresh with staleness, dependency, backfill, and swap gates."""

    raw_view_name = str(view_spec.get("view_name") or view_spec.get("name") or "").strip()
    view_name = normalize_field_name(raw_view_name) if raw_view_name else ""
    refresh_strategy = normalize_field_name(view_spec.get("refresh_strategy") or "") if not _blank(view_spec.get("refresh_strategy")) else ""
    max_staleness_seconds = int(view_spec.get("max_staleness_seconds") or 0)
    allowed_refresh_strategies = {normalize_field_name(value) for value in _as_sequence(refresh_policy.get("allowed_refresh_strategies")) if not _blank(value)}
    blockers: list[str] = []
    if not view_name:
        blockers.append("missing_view_name")
    if not refresh_strategy:
        blockers.append("missing_refresh_strategy")
    elif allowed_refresh_strategies and refresh_strategy not in allowed_refresh_strategies:
        blockers.append(f"refresh_strategy_not_allowed:{refresh_strategy}")
    if max_staleness_seconds <= 0:
        blockers.append("missing_max_staleness_seconds")
    policy_max_staleness_seconds = int(refresh_policy.get("max_staleness_seconds") or 0)
    if policy_max_staleness_seconds and max_staleness_seconds > policy_max_staleness_seconds:
        blockers.append("staleness_exceeds_policy")
    if refresh_policy.get("require_dependency_tables") and not _as_sequence(view_spec.get("dependency_tables")):
        blockers.append("missing_dependency_tables")
    if refresh_policy.get("require_backfill_plan") and _blank(view_spec.get("backfill_plan")):
        blockers.append("missing_backfill_plan")
    if refresh_policy.get("require_swap_strategy") and _blank(view_spec.get("swap_strategy")):
        blockers.append("missing_swap_strategy")
    refresh_hash = "materialized-view-refresh:" + _digest(
        {
            "blockers": blockers,
            "max_staleness_seconds": max_staleness_seconds,
            "refresh_strategy": refresh_strategy,
            "view_name": view_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return MaterializedViewRefreshPlanReceipt(
        ready=not blockers,
        view_name=view_name,
        refresh_strategy=refresh_strategy,
        max_staleness_seconds=max_staleness_seconds,
        blockers=tuple(blockers),
        refresh_hash=refresh_hash,
    )


def plan_data_quarantine_policy(
    finding_set: Mapping[str, Any],
    quarantine_policy: Mapping[str, Any],
) -> DataQuarantinePlanReceipt:
    """Plan data quarantine with finding, sink, triage, release, and audit gates."""

    raw_dataset_name = str(finding_set.get("dataset_name") or finding_set.get("name") or "").strip()
    dataset_name = normalize_field_name(raw_dataset_name) if raw_dataset_name else ""
    finding_count = int(finding_set.get("finding_count") or len(_as_mapping_sequence(finding_set.get("findings"))))
    quarantine_sink = str(finding_set.get("quarantine_sink") or "").strip()
    blockers: list[str] = []
    if not dataset_name:
        blockers.append("missing_dataset_name")
    if finding_count <= 0:
        blockers.append("missing_findings")
    if not quarantine_sink:
        blockers.append("missing_quarantine_sink")
    if quarantine_policy.get("require_triage_owner") and _blank(finding_set.get("triage_owner")):
        blockers.append("missing_triage_owner")
    if quarantine_policy.get("require_release_criteria") and _blank(finding_set.get("release_criteria")):
        blockers.append("missing_release_criteria")
    if quarantine_policy.get("require_audit_receipt") and _blank(finding_set.get("audit_receipt")):
        blockers.append("missing_audit_receipt")
    quarantine_hash = "data-quarantine:" + _digest(
        {
            "blockers": blockers,
            "dataset_name": dataset_name,
            "finding_count": finding_count,
            "quarantine_sink": quarantine_sink,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DataQuarantinePlanReceipt(
        ready=not blockers,
        dataset_name=dataset_name,
        finding_count=finding_count,
        quarantine_sink=quarantine_sink,
        blockers=tuple(blockers),
        quarantine_hash=quarantine_hash,
    )


def plan_task_lease(
    lease_spec: Mapping[str, Any],
    lease_policy: Mapping[str, Any],
) -> TaskLeasePlanReceipt:
    """Plan task leasing with TTL, renewal, owner-token, and fencing gates."""

    raw_worker_name = str(lease_spec.get("worker_name") or lease_spec.get("name") or "").strip()
    worker_name = normalize_field_name(raw_worker_name) if raw_worker_name else ""
    lease_ttl_seconds = int(lease_spec.get("lease_ttl_seconds") or 0)
    renewal_interval_seconds = int(lease_spec.get("renewal_interval_seconds") or 0)
    max_lease_ttl_seconds = int(lease_policy.get("max_lease_ttl_seconds") or 0)
    blockers: list[str] = []
    if not worker_name:
        blockers.append("missing_worker_name")
    if lease_ttl_seconds <= 0:
        blockers.append("missing_lease_ttl_seconds")
    elif max_lease_ttl_seconds and lease_ttl_seconds > max_lease_ttl_seconds:
        blockers.append("lease_ttl_exceeds_policy")
    if lease_policy.get("require_renewal") and renewal_interval_seconds <= 0:
        blockers.append("missing_renewal_interval_seconds")
    if renewal_interval_seconds > 0 and lease_ttl_seconds > 0 and renewal_interval_seconds >= lease_ttl_seconds:
        blockers.append("renewal_interval_not_less_than_ttl")
    if lease_policy.get("require_owner_token") and _blank(lease_spec.get("owner_token")):
        blockers.append("missing_owner_token")
    if lease_policy.get("require_fencing_token") and _blank(lease_spec.get("fencing_token")):
        blockers.append("missing_fencing_token")
    lease_hash = "task-lease:" + _digest(
        {
            "blockers": blockers,
            "lease_ttl_seconds": lease_ttl_seconds,
            "renewal_interval_seconds": renewal_interval_seconds,
            "worker_name": worker_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return TaskLeasePlanReceipt(
        ready=not blockers,
        worker_name=worker_name,
        lease_ttl_seconds=lease_ttl_seconds,
        renewal_interval_seconds=renewal_interval_seconds,
        blockers=tuple(blockers),
        lease_hash=lease_hash,
    )


def plan_worker_heartbeat(
    worker_spec: Mapping[str, Any],
    heartbeat_policy: Mapping[str, Any],
) -> WorkerHeartbeatPlanReceipt:
    """Plan worker heartbeat and stale-worker detection behavior."""

    raw_worker_name = str(worker_spec.get("worker_name") or worker_spec.get("name") or "").strip()
    worker_name = normalize_field_name(raw_worker_name) if raw_worker_name else ""
    heartbeat_interval_seconds = int(worker_spec.get("heartbeat_interval_seconds") or 0)
    stale_after_seconds = int(worker_spec.get("stale_after_seconds") or 0)
    max_heartbeat_interval_seconds = int(heartbeat_policy.get("max_heartbeat_interval_seconds") or 0)
    blockers: list[str] = []
    if not worker_name:
        blockers.append("missing_worker_name")
    if heartbeat_interval_seconds <= 0:
        blockers.append("missing_heartbeat_interval_seconds")
    elif max_heartbeat_interval_seconds and heartbeat_interval_seconds > max_heartbeat_interval_seconds:
        blockers.append("heartbeat_interval_exceeds_policy")
    if stale_after_seconds <= 0:
        blockers.append("missing_stale_after_seconds")
    elif heartbeat_interval_seconds > 0 and stale_after_seconds <= heartbeat_interval_seconds:
        blockers.append("stale_after_not_greater_than_heartbeat")
    if heartbeat_policy.get("require_liveness_topic") and _blank(worker_spec.get("liveness_topic")):
        blockers.append("missing_liveness_topic")
    if heartbeat_policy.get("require_restart_policy") and _blank(worker_spec.get("restart_policy")):
        blockers.append("missing_restart_policy")
    heartbeat_hash = "worker-heartbeat:" + _digest(
        {
            "blockers": blockers,
            "heartbeat_interval_seconds": heartbeat_interval_seconds,
            "stale_after_seconds": stale_after_seconds,
            "worker_name": worker_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return WorkerHeartbeatPlanReceipt(
        ready=not blockers,
        worker_name=worker_name,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
        stale_after_seconds=stale_after_seconds,
        blockers=tuple(blockers),
        heartbeat_hash=heartbeat_hash,
    )


def plan_worker_autoscale_policy(
    autoscale_spec: Mapping[str, Any],
    autoscale_policy: Mapping[str, Any],
) -> WorkerAutoscalePolicyPlanReceipt:
    """Plan worker autoscaling with queue metric, replica bounds, cooldown, and drain gates."""

    raw_worker_name = str(autoscale_spec.get("worker_name") or autoscale_spec.get("name") or "").strip()
    worker_name = normalize_field_name(raw_worker_name) if raw_worker_name else ""
    scale_metric = normalize_field_name(autoscale_spec.get("scale_metric") or autoscale_spec.get("metric") or "")
    min_replicas = int(autoscale_spec.get("min_replicas") or 0)
    max_replicas = int(autoscale_spec.get("max_replicas") or 0)
    target_value = int(autoscale_spec.get("target_value") or autoscale_spec.get("target") or 0)
    policy_max_replicas = int(autoscale_policy.get("max_replicas") or 0)
    allowed_scale_metrics = {normalize_field_name(value) for value in _as_sequence(autoscale_policy.get("allowed_scale_metrics")) if not _blank(value)}
    blockers: list[str] = []
    if not worker_name:
        blockers.append("missing_worker_name")
    if not scale_metric or scale_metric == "field":
        blockers.append("missing_scale_metric")
    elif allowed_scale_metrics and scale_metric not in allowed_scale_metrics:
        blockers.append(f"scale_metric_not_allowed:{scale_metric}")
    if min_replicas < 0:
        blockers.append("min_replicas_below_zero")
    if max_replicas <= 0:
        blockers.append("missing_max_replicas")
    elif max_replicas < min_replicas:
        blockers.append("max_replicas_less_than_min")
    elif policy_max_replicas and max_replicas > policy_max_replicas:
        blockers.append("max_replicas_exceeds_policy")
    if target_value <= 0:
        blockers.append("missing_target_value")
    if autoscale_policy.get("require_cooldown") and _blank(autoscale_spec.get("cooldown_seconds")):
        blockers.append("missing_cooldown_seconds")
    if autoscale_policy.get("require_drain_policy") and _blank(autoscale_spec.get("drain_policy")):
        blockers.append("missing_drain_policy")
    if autoscale_policy.get("require_scale_to_zero_guard") and _blank(autoscale_spec.get("scale_to_zero_guard")):
        blockers.append("missing_scale_to_zero_guard")
    if autoscale_policy.get("require_autoscale_receipt") and _blank(autoscale_spec.get("autoscale_receipt")):
        blockers.append("missing_autoscale_receipt")
    autoscale_hash = "worker-autoscale-policy:" + _digest(
        {
            "blockers": blockers,
            "max_replicas": max_replicas,
            "min_replicas": min_replicas,
            "scale_metric": scale_metric,
            "worker_name": worker_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return WorkerAutoscalePolicyPlanReceipt(
        ready=not blockers,
        worker_name=worker_name,
        scale_metric=scale_metric,
        min_replicas=min_replicas,
        max_replicas=max_replicas,
        blockers=tuple(blockers),
        autoscale_hash=autoscale_hash,
    )


def plan_queue_visibility_timeout(
    queue_spec: Mapping[str, Any],
    visibility_policy: Mapping[str, Any],
) -> QueueVisibilityTimeoutPlanReceipt:
    """Plan queue visibility timeout with processing-time, extension, and DLQ gates."""

    raw_queue_name = str(queue_spec.get("queue_name") or queue_spec.get("name") or "").strip()
    queue_name = normalize_field_name(raw_queue_name) if raw_queue_name else ""
    visibility_timeout_seconds = int(queue_spec.get("visibility_timeout_seconds") or 0)
    max_processing_seconds = int(queue_spec.get("max_processing_seconds") or 0)
    max_visibility_timeout_seconds = int(visibility_policy.get("max_visibility_timeout_seconds") or 0)
    blockers: list[str] = []
    if not queue_name:
        blockers.append("missing_queue_name")
    if visibility_timeout_seconds <= 0:
        blockers.append("missing_visibility_timeout_seconds")
    elif max_visibility_timeout_seconds and visibility_timeout_seconds > max_visibility_timeout_seconds:
        blockers.append("visibility_timeout_exceeds_policy")
    if max_processing_seconds <= 0:
        blockers.append("missing_max_processing_seconds")
    elif visibility_timeout_seconds > 0 and visibility_timeout_seconds < max_processing_seconds:
        blockers.append("visibility_timeout_less_than_processing_time")
    if visibility_policy.get("require_extension_policy") and _blank(queue_spec.get("extension_policy")):
        blockers.append("missing_extension_policy")
    if visibility_policy.get("require_dlq") and _blank(queue_spec.get("dead_letter_queue")):
        blockers.append("missing_dlq")
    timeout_hash = "queue-visibility-timeout:" + _digest(
        {
            "blockers": blockers,
            "max_processing_seconds": max_processing_seconds,
            "queue_name": queue_name,
            "visibility_timeout_seconds": visibility_timeout_seconds,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return QueueVisibilityTimeoutPlanReceipt(
        ready=not blockers,
        queue_name=queue_name,
        visibility_timeout_seconds=visibility_timeout_seconds,
        max_processing_seconds=max_processing_seconds,
        blockers=tuple(blockers),
        timeout_hash=timeout_hash,
    )


def plan_cron_catchup_window(
    job_spec: Mapping[str, Any],
    catchup_policy: Mapping[str, Any],
) -> CronCatchupPlanReceipt:
    """Plan cron catch-up behavior with misfire and idempotency gates."""

    raw_job_name = str(job_spec.get("job_name") or job_spec.get("name") or "").strip()
    job_name = normalize_field_name(raw_job_name) if raw_job_name else ""
    catchup_window_minutes = int(job_spec.get("catchup_window_minutes") or 0)
    max_catchup_runs = int(job_spec.get("max_catchup_runs") or 0)
    policy_max_window = int(catchup_policy.get("max_catchup_window_minutes") or 0)
    policy_max_runs = int(catchup_policy.get("max_catchup_runs") or 0)
    blockers: list[str] = []
    if not job_name:
        blockers.append("missing_job_name")
    if catchup_window_minutes <= 0:
        blockers.append("missing_catchup_window_minutes")
    elif policy_max_window and catchup_window_minutes > policy_max_window:
        blockers.append("catchup_window_exceeds_policy")
    if max_catchup_runs <= 0:
        blockers.append("missing_max_catchup_runs")
    elif policy_max_runs and max_catchup_runs > policy_max_runs:
        blockers.append("max_catchup_runs_exceeds_policy")
    if catchup_policy.get("require_misfire_policy") and _blank(job_spec.get("misfire_policy")):
        blockers.append("missing_misfire_policy")
    if catchup_policy.get("require_idempotency_key") and _blank(job_spec.get("idempotency_key")):
        blockers.append("missing_idempotency_key")
    catchup_hash = "cron-catchup:" + _digest(
        {
            "blockers": blockers,
            "catchup_window_minutes": catchup_window_minutes,
            "job_name": job_name,
            "max_catchup_runs": max_catchup_runs,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return CronCatchupPlanReceipt(
        ready=not blockers,
        job_name=job_name,
        catchup_window_minutes=catchup_window_minutes,
        max_catchup_runs=max_catchup_runs,
        blockers=tuple(blockers),
        catchup_hash=catchup_hash,
    )


def plan_workflow_compensation(
    workflow_spec: Mapping[str, Any],
    compensation_policy: Mapping[str, Any],
) -> WorkflowCompensationPlanReceipt:
    """Plan workflow compensation with step coverage, ordering, and receipt gates."""

    raw_workflow_name = str(workflow_spec.get("workflow_name") or workflow_spec.get("name") or "").strip()
    workflow_name = normalize_field_name(raw_workflow_name) if raw_workflow_name else ""
    steps = tuple(normalize_field_name(step) for step in _as_sequence(workflow_spec.get("steps")) if not _blank(step))
    compensating_steps = tuple(normalize_field_name(step) for step in _as_sequence(workflow_spec.get("compensating_steps")) if not _blank(step))
    blocker_steps = set(compensating_steps)
    blockers: list[str] = []
    if not workflow_name:
        blockers.append("missing_workflow_name")
    if not compensating_steps:
        blockers.append("missing_compensating_steps")
    for step in steps:
        if compensation_policy.get("require_compensation_for_each_step") and step not in blocker_steps:
            blockers.append(f"missing_compensation_for_step:{step}")
    if compensation_policy.get("require_reverse_order") and not workflow_spec.get("reverse_order"):
        blockers.append("missing_reverse_order")
    if compensation_policy.get("require_compensation_receipt") and _blank(workflow_spec.get("compensation_receipt")):
        blockers.append("missing_compensation_receipt")
    if compensation_policy.get("require_failure_boundary") and _blank(workflow_spec.get("failure_boundary")):
        blockers.append("missing_failure_boundary")
    compensation_hash = "workflow-compensation:" + _digest(
        {
            "blockers": blockers,
            "compensating_steps": compensating_steps,
            "steps": steps,
            "workflow_name": workflow_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return WorkflowCompensationPlanReceipt(
        ready=not blockers,
        workflow_name=workflow_name,
        compensating_steps=compensating_steps,
        blockers=tuple(blockers),
        compensation_hash=compensation_hash,
    )


def plan_batch_checkpoint(
    batch_spec: Mapping[str, Any],
    checkpoint_policy: Mapping[str, Any],
) -> BatchCheckpointPlanReceipt:
    """Plan batch checkpointing with interval, store, resume, and checksum gates."""

    raw_job_name = str(batch_spec.get("job_name") or batch_spec.get("name") or "").strip()
    job_name = normalize_field_name(raw_job_name) if raw_job_name else ""
    checkpoint_interval_records = int(batch_spec.get("checkpoint_interval_records") or 0)
    checkpoint_store = str(batch_spec.get("checkpoint_store") or "").strip()
    max_checkpoint_interval_records = int(checkpoint_policy.get("max_checkpoint_interval_records") or 0)
    blockers: list[str] = []
    if not job_name:
        blockers.append("missing_job_name")
    if checkpoint_interval_records <= 0:
        blockers.append("missing_checkpoint_interval_records")
    elif max_checkpoint_interval_records and checkpoint_interval_records > max_checkpoint_interval_records:
        blockers.append("checkpoint_interval_exceeds_policy")
    if not checkpoint_store:
        blockers.append("missing_checkpoint_store")
    if checkpoint_policy.get("require_resume_token") and _blank(batch_spec.get("resume_token")):
        blockers.append("missing_resume_token")
    if checkpoint_policy.get("require_checksum") and _blank(batch_spec.get("checksum")):
        blockers.append("missing_checksum")
    if checkpoint_policy.get("require_progress_receipt") and _blank(batch_spec.get("progress_receipt")):
        blockers.append("missing_progress_receipt")
    checkpoint_hash = "batch-checkpoint:" + _digest(
        {
            "blockers": blockers,
            "checkpoint_interval_records": checkpoint_interval_records,
            "checkpoint_store": checkpoint_store,
            "job_name": job_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return BatchCheckpointPlanReceipt(
        ready=not blockers,
        job_name=job_name,
        checkpoint_interval_records=checkpoint_interval_records,
        checkpoint_store=checkpoint_store,
        blockers=tuple(blockers),
        checkpoint_hash=checkpoint_hash,
    )


def plan_run_artifact_manifest(
    run_spec: Mapping[str, Any],
    artifact_policy: Mapping[str, Any],
) -> RunArtifactManifestReceipt:
    """Plan run artifact manifest with artifact, digest, retention, and owner gates."""

    raw_run_id = str(run_spec.get("run_id") or run_spec.get("id") or "").strip()
    run_id = normalize_field_name(raw_run_id) if raw_run_id else ""
    artifacts = tuple(dict(item) for item in _as_mapping_sequence(run_spec.get("artifacts")))
    artifact_names = tuple(str(artifact.get("name") or artifact.get("path") or f"artifact_{index + 1}") for index, artifact in enumerate(artifacts))
    blockers: list[str] = []
    if not run_id:
        blockers.append("missing_run_id")
    if not artifacts:
        blockers.append("missing_artifacts")
    for index, artifact in enumerate(artifacts):
        if artifact_policy.get("require_digest") and _blank(artifact.get("digest")):
            blockers.append(f"artifact_{index + 1}_missing_digest")
        if artifact_policy.get("require_content_type") and _blank(artifact.get("content_type")):
            blockers.append(f"artifact_{index + 1}_missing_content_type")
    if artifact_policy.get("require_retention_days") and int(run_spec.get("retention_days") or 0) <= 0:
        blockers.append("missing_retention_days")
    if artifact_policy.get("require_owner") and _blank(run_spec.get("owner")):
        blockers.append("missing_owner")
    manifest_hash = "run-artifact-manifest:" + _digest(
        {
            "artifacts": artifacts,
            "blockers": blockers,
            "run_id": run_id,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return RunArtifactManifestReceipt(
        ready=not blockers,
        run_id=run_id,
        artifacts=artifact_names,
        blockers=tuple(blockers),
        manifest_hash=manifest_hash,
    )


def plan_execution_audit_trail(
    operation_spec: Mapping[str, Any],
    audit_policy: Mapping[str, Any],
) -> ExecutionAuditTrailPlanReceipt:
    """Plan execution audit trail with event, actor, trace, sink, and retention gates."""

    raw_operation_name = str(operation_spec.get("operation_name") or operation_spec.get("name") or "").strip()
    operation_name = normalize_field_name(raw_operation_name) if raw_operation_name else ""
    audit_events = tuple(normalize_field_name(event) for event in _as_sequence(operation_spec.get("audit_events")) if not _blank(event))
    audit_event_set = set(audit_events)
    blockers: list[str] = []
    if not operation_name:
        blockers.append("missing_operation_name")
    if not audit_events:
        blockers.append("missing_audit_events")
    for event in _as_sequence(audit_policy.get("required_events")):
        event_name = normalize_field_name(event)
        if event_name and event_name not in audit_event_set:
            blockers.append(f"missing_event:{event_name}")
    if audit_policy.get("require_actor") and _blank(operation_spec.get("actor_field")):
        blockers.append("missing_actor_field")
    if audit_policy.get("require_trace_id") and _blank(operation_spec.get("trace_id_field")):
        blockers.append("missing_trace_id_field")
    if audit_policy.get("require_audit_sink") and _blank(operation_spec.get("audit_sink")):
        blockers.append("missing_audit_sink")
    if audit_policy.get("require_retention_days") and int(operation_spec.get("retention_days") or 0) <= 0:
        blockers.append("missing_retention_days")
    audit_hash = "execution-audit-trail:" + _digest(
        {
            "audit_events": audit_events,
            "blockers": blockers,
            "operation_name": operation_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ExecutionAuditTrailPlanReceipt(
        ready=not blockers,
        operation_name=operation_name,
        audit_events=audit_events,
        blockers=tuple(blockers),
        audit_hash=audit_hash,
    )


def plan_api_gateway_route(
    route_spec: Mapping[str, Any],
    gateway_policy: Mapping[str, Any],
) -> ApiGatewayRoutePlanReceipt:
    """Plan an API gateway route with upstream, method, auth, rate, and timeout gates."""

    raw_route_id = str(route_spec.get("route_id") or route_spec.get("name") or "").strip()
    route_id = normalize_field_name(raw_route_id) if raw_route_id else ""
    route_path = str(route_spec.get("route_path") or route_spec.get("path") or "").strip()
    raw_upstream_service = str(route_spec.get("upstream_service") or "").strip()
    upstream_service = normalize_field_name(raw_upstream_service) if raw_upstream_service else ""
    methods = tuple(str(value).upper() for value in _as_sequence(route_spec.get("methods")) if str(value).strip())
    allowed_methods = {str(value).upper() for value in _as_sequence(gateway_policy.get("allowed_methods")) if str(value).strip()}
    blockers: list[str] = []
    if not route_id:
        blockers.append("missing_route_id")
    if not route_path:
        blockers.append("missing_route_path")
    elif not route_path.startswith("/"):
        blockers.append("route_path_must_start_with_slash")
    if not upstream_service:
        blockers.append("missing_upstream_service")
    if not methods:
        blockers.append("missing_methods")
    for method in methods:
        if allowed_methods and method not in allowed_methods:
            blockers.append(f"method_not_allowed:{method}")
    if gateway_policy.get("require_auth_policy") and _blank(route_spec.get("auth_policy")):
        blockers.append("missing_auth_policy")
    if gateway_policy.get("require_rate_limit_policy") and _blank(route_spec.get("rate_limit_policy")):
        blockers.append("missing_rate_limit_policy")
    if gateway_policy.get("require_timeout_policy") and _blank(route_spec.get("timeout_policy")):
        blockers.append("missing_timeout_policy")
    route_hash = "api-gateway-route:" + _digest(
        {
            "blockers": blockers,
            "methods": methods,
            "route_id": route_id,
            "route_path": route_path,
            "upstream_service": upstream_service,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ApiGatewayRoutePlanReceipt(
        ready=not blockers,
        route_id=route_id,
        upstream_service=upstream_service,
        methods=methods,
        blockers=tuple(blockers),
        route_hash=route_hash,
    )


def plan_service_discovery_registration(
    service_spec: Mapping[str, Any],
    discovery_policy: Mapping[str, Any],
) -> ServiceDiscoveryRegistrationReceipt:
    """Plan service discovery registration with endpoint, health check, TTL, and region gates."""

    raw_service_name = str(service_spec.get("service_name") or service_spec.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    endpoint_records = tuple(dict(item) for item in _as_mapping_sequence(service_spec.get("endpoints")))
    endpoint_urls = tuple(
        str(endpoint.get("url") or endpoint.get("address") or "").strip()
        for endpoint in endpoint_records
        if str(endpoint.get("url") or endpoint.get("address") or "").strip()
    )
    if not endpoint_records:
        endpoint_urls = tuple(str(value).strip() for value in _as_sequence(service_spec.get("endpoints")) if str(value).strip())
    health_check_path = str(service_spec.get("health_check_path") or "").strip()
    ttl_seconds = int(service_spec.get("ttl_seconds") or 0)
    max_ttl_seconds = int(discovery_policy.get("max_ttl_seconds") or 0)
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if not endpoint_urls:
        blockers.append("missing_endpoints")
    for index, endpoint in enumerate(endpoint_records):
        if _blank(endpoint.get("url")) and _blank(endpoint.get("address")):
            blockers.append(f"endpoint_{index + 1}_missing_url")
    if discovery_policy.get("require_health_check_path") and not health_check_path:
        blockers.append("missing_health_check_path")
    if discovery_policy.get("require_ttl_seconds") and ttl_seconds <= 0:
        blockers.append("missing_ttl_seconds")
    elif max_ttl_seconds and ttl_seconds > max_ttl_seconds:
        blockers.append("ttl_exceeds_policy")
    if discovery_policy.get("require_region") and _blank(service_spec.get("region")):
        blockers.append("missing_region")
    registration_hash = "service-discovery-registration:" + _digest(
        {
            "blockers": blockers,
            "endpoint_urls": endpoint_urls,
            "health_check_path": health_check_path,
            "service_name": service_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ServiceDiscoveryRegistrationReceipt(
        ready=not blockers,
        service_name=service_name,
        endpoints=endpoint_urls,
        health_check_path=health_check_path,
        blockers=tuple(blockers),
        registration_hash=registration_hash,
    )


def plan_service_dependency_contract(
    service_spec: Mapping[str, Any],
    dependency_policy: Mapping[str, Any],
) -> ServiceDependencyContractReceipt:
    """Plan service dependency contracts with timeout, fallback, circuit breaker, and owner gates."""

    raw_service_name = str(service_spec.get("service_name") or service_spec.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    dependency_records = tuple(dict(item) for item in _as_mapping_sequence(service_spec.get("dependencies")))
    dependency_names = tuple(
        normalize_field_name(dependency.get("name") or dependency.get("service") or "")
        for dependency in dependency_records
        if not _blank(dependency.get("name") or dependency.get("service"))
    )
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if not dependency_records:
        blockers.append("missing_dependencies")
    for index, dependency in enumerate(dependency_records):
        dependency_name = normalize_field_name(dependency.get("name") or dependency.get("service") or "")
        if not dependency_name:
            blockers.append(f"dependency_{index + 1}_missing_name")
        if dependency_policy.get("require_timeout") and int(dependency.get("timeout_ms") or 0) <= 0:
            blockers.append(f"dependency_{index + 1}_missing_timeout")
        if dependency_policy.get("require_fallback") and _blank(dependency.get("fallback")):
            blockers.append(f"missing_fallback_for_dependency:{dependency_name or index + 1}")
        if dependency_policy.get("require_circuit_breaker") and _blank(dependency.get("circuit_breaker")):
            blockers.append(f"missing_circuit_breaker_for_dependency:{dependency_name or index + 1}")
    if dependency_policy.get("require_owner") and _blank(service_spec.get("owner")):
        blockers.append("missing_owner")
    contract_hash = "service-dependency-contract:" + _digest(
        {
            "blockers": blockers,
            "dependencies": dependency_records,
            "service_name": service_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ServiceDependencyContractReceipt(
        ready=not blockers,
        service_name=service_name,
        dependencies=dependency_names,
        blockers=tuple(blockers),
        contract_hash=contract_hash,
    )


def plan_runtime_config_schema(
    config_spec: Mapping[str, Any],
    config_policy: Mapping[str, Any],
) -> RuntimeConfigSchemaPlanReceipt:
    """Plan runtime config schema with required config keys, secret refs, version, and owner gates."""

    raw_service_name = str(config_spec.get("service_name") or config_spec.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    config_mapping = config_spec.get("config") if isinstance(config_spec.get("config"), Mapping) else {}
    config_keys = tuple(sorted(normalize_field_name(key) for key in _as_sequence(config_spec.get("config_keys")) if not _blank(key)))
    if not config_keys and config_mapping:
        config_keys = tuple(sorted(normalize_field_name(key) for key in config_mapping.keys()))
    secret_keys = tuple(sorted(normalize_field_name(key) for key in _as_sequence(config_spec.get("secret_keys")) if not _blank(key)))
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if not config_keys:
        blockers.append("missing_config_keys")
    for key in _as_sequence(config_policy.get("required_keys")):
        key_name = normalize_field_name(key)
        if key_name and key_name not in config_keys:
            blockers.append(f"missing_key:{key_name}")
    for key in _as_sequence(config_policy.get("required_secret_keys")):
        key_name = normalize_field_name(key)
        if key_name and key_name not in secret_keys:
            blockers.append(f"missing_secret_ref:{key_name}")
    if config_policy.get("forbid_plaintext_secret_values"):
        for key in secret_keys:
            raw_value = config_mapping.get(key)
            if raw_value is None:
                raw_value = config_mapping.get(str(key).upper())
            if raw_value is not None and not str(raw_value).startswith(("secret://", "vault://", "arn:")):
                blockers.append(f"plaintext_secret_key:{key}")
    if config_policy.get("require_schema_version") and _blank(config_spec.get("schema_version")):
        blockers.append("missing_schema_version")
    if config_policy.get("require_owner") and _blank(config_spec.get("owner")):
        blockers.append("missing_owner")
    schema_hash = "runtime-config-schema:" + _digest(
        {
            "blockers": blockers,
            "config_keys": config_keys,
            "secret_keys": secret_keys,
            "service_name": service_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return RuntimeConfigSchemaPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        config_keys=config_keys,
        secret_keys=secret_keys,
        blockers=tuple(blockers),
        schema_hash=schema_hash,
    )


def plan_environment_promotion(
    promotion_spec: Mapping[str, Any],
    promotion_policy: Mapping[str, Any],
) -> EnvironmentPromotionPlanReceipt:
    """Plan environment promotion with artifact, migration, rollback, and approval gates."""

    raw_service_name = str(promotion_spec.get("service_name") or promotion_spec.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    source_environment = normalize_field_name(promotion_spec.get("source_environment") or "")
    target_environment = normalize_field_name(promotion_spec.get("target_environment") or "")
    allowed_pairs = {
        (
            normalize_field_name(pair.get("source") or pair.get("from") or ""),
            normalize_field_name(pair.get("target") or pair.get("to") or ""),
        )
        for pair in _as_mapping_sequence(promotion_policy.get("allowed_pairs"))
    }
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if not source_environment:
        blockers.append("missing_source_environment")
    if not target_environment:
        blockers.append("missing_target_environment")
    if source_environment and target_environment and allowed_pairs and (source_environment, target_environment) not in allowed_pairs:
        blockers.append("promotion_pair_not_allowed")
    if promotion_policy.get("require_artifact_digest") and _blank(promotion_spec.get("artifact_digest")):
        blockers.append("missing_artifact_digest")
    if promotion_policy.get("require_migration_plan") and _blank(promotion_spec.get("migration_plan")):
        blockers.append("missing_migration_plan")
    if promotion_policy.get("require_rollback_plan") and _blank(promotion_spec.get("rollback_plan")):
        blockers.append("missing_rollback_plan")
    if promotion_policy.get("require_approval") and _blank(promotion_spec.get("approval")):
        blockers.append("missing_approval")
    promotion_hash = "environment-promotion:" + _digest(
        {
            "blockers": blockers,
            "service_name": service_name,
            "source_environment": source_environment,
            "target_environment": target_environment,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return EnvironmentPromotionPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        source_environment=source_environment,
        target_environment=target_environment,
        blockers=tuple(blockers),
        promotion_hash=promotion_hash,
    )


def plan_webhook_delivery_policy(
    webhook_spec: Mapping[str, Any],
    delivery_policy: Mapping[str, Any],
) -> WebhookDeliveryPolicyPlanReceipt:
    """Plan outbound webhook delivery with signing, idempotency, retry, and DLQ gates."""

    raw_webhook_name = str(webhook_spec.get("webhook_name") or webhook_spec.get("name") or "").strip()
    webhook_name = normalize_field_name(raw_webhook_name) if raw_webhook_name else ""
    destination_url = str(webhook_spec.get("destination_url") or "").strip()
    retry_attempts = int(webhook_spec.get("retry_attempts") or 0)
    max_retry_attempts = int(delivery_policy.get("max_retry_attempts") or 0)
    blockers: list[str] = []
    if not webhook_name:
        blockers.append("missing_webhook_name")
    if not destination_url:
        blockers.append("missing_destination_url")
    elif delivery_policy.get("require_https") and not destination_url.startswith("https://"):
        blockers.append("destination_url_must_be_https")
    if delivery_policy.get("require_signing_secret_ref") and _blank(webhook_spec.get("signing_secret_ref")):
        blockers.append("missing_signing_secret_ref")
    if delivery_policy.get("require_idempotency_key") and _blank(webhook_spec.get("idempotency_key")):
        blockers.append("missing_idempotency_key")
    if retry_attempts <= 0:
        blockers.append("missing_retry_attempts")
    elif max_retry_attempts and retry_attempts > max_retry_attempts:
        blockers.append("retry_attempts_exceed_policy")
    if delivery_policy.get("require_dead_letter_sink") and _blank(webhook_spec.get("dead_letter_sink")):
        blockers.append("missing_dead_letter_sink")
    delivery_hash = "webhook-delivery-policy:" + _digest(
        {
            "blockers": blockers,
            "destination_url": destination_url,
            "retry_attempts": retry_attempts,
            "webhook_name": webhook_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return WebhookDeliveryPolicyPlanReceipt(
        ready=not blockers,
        webhook_name=webhook_name,
        destination_url=destination_url,
        retry_attempts=retry_attempts,
        blockers=tuple(blockers),
        delivery_hash=delivery_hash,
    )


def plan_consumer_group_offset(
    consumer_spec: Mapping[str, Any],
    offset_policy: Mapping[str, Any],
) -> ConsumerGroupOffsetPlanReceipt:
    """Plan consumer group offset handling with checkpoint, replay, and lag alert gates."""

    raw_consumer_group = str(consumer_spec.get("consumer_group") or consumer_spec.get("name") or "").strip()
    consumer_group = normalize_field_name(raw_consumer_group) if raw_consumer_group else ""
    raw_topic_name = str(consumer_spec.get("topic_name") or consumer_spec.get("topic") or "").strip()
    topic_name = normalize_field_name(raw_topic_name) if raw_topic_name else ""
    offset_strategy = normalize_field_name(consumer_spec.get("offset_strategy") or "")
    allowed_strategies = {normalize_field_name(value) for value in _as_sequence(offset_policy.get("allowed_offset_strategies")) if not _blank(value)}
    lag_alert_threshold = int(consumer_spec.get("lag_alert_threshold") or 0)
    max_lag_alert_threshold = int(offset_policy.get("max_lag_alert_threshold") or 0)
    blockers: list[str] = []
    if not consumer_group:
        blockers.append("missing_consumer_group")
    if not topic_name:
        blockers.append("missing_topic_name")
    if not offset_strategy:
        blockers.append("missing_offset_strategy")
    elif allowed_strategies and offset_strategy not in allowed_strategies:
        blockers.append(f"offset_strategy_not_allowed:{offset_strategy}")
    if offset_policy.get("require_checkpoint_store") and _blank(consumer_spec.get("checkpoint_store")):
        blockers.append("missing_checkpoint_store")
    if offset_policy.get("require_replay_policy") and _blank(consumer_spec.get("replay_policy")):
        blockers.append("missing_replay_policy")
    if offset_policy.get("require_lag_alert_threshold") and lag_alert_threshold <= 0:
        blockers.append("missing_lag_alert_threshold")
    elif max_lag_alert_threshold and lag_alert_threshold > max_lag_alert_threshold:
        blockers.append("lag_alert_threshold_exceeds_policy")
    offset_hash = "consumer-group-offset:" + _digest(
        {
            "blockers": blockers,
            "consumer_group": consumer_group,
            "offset_strategy": offset_strategy,
            "topic_name": topic_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ConsumerGroupOffsetPlanReceipt(
        ready=not blockers,
        consumer_group=consumer_group,
        topic_name=topic_name,
        offset_strategy=offset_strategy,
        blockers=tuple(blockers),
        offset_hash=offset_hash,
    )


def plan_service_ownership_runbook(
    service_spec: Mapping[str, Any],
    ownership_policy: Mapping[str, Any],
) -> ServiceOwnershipRunbookPlanReceipt:
    """Plan service ownership/runbook evidence with owner, escalation, SLO, dashboard, and on-call gates."""

    raw_service_name = str(service_spec.get("service_name") or service_spec.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    owners = tuple(str(value).strip() for value in _as_sequence(service_spec.get("owners")) if str(value).strip())
    escalation_channels = tuple(str(value).strip() for value in _as_sequence(service_spec.get("escalation_channels")) if str(value).strip())
    blockers: list[str] = []
    if not service_name:
        blockers.append("missing_service_name")
    if not owners:
        blockers.append("missing_owners")
    if not escalation_channels:
        blockers.append("missing_escalation_channels")
    if ownership_policy.get("require_slo") and _blank(service_spec.get("slo")):
        blockers.append("missing_slo")
    if ownership_policy.get("require_runbook_url") and _blank(service_spec.get("runbook_url")):
        blockers.append("missing_runbook_url")
    if ownership_policy.get("require_dashboard_url") and _blank(service_spec.get("dashboard_url")):
        blockers.append("missing_dashboard_url")
    if ownership_policy.get("require_oncall_rotation") and _blank(service_spec.get("oncall_rotation")):
        blockers.append("missing_oncall_rotation")
    ownership_hash = "service-ownership-runbook:" + _digest(
        {
            "blockers": blockers,
            "escalation_channels": escalation_channels,
            "owners": owners,
            "service_name": service_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ServiceOwnershipRunbookPlanReceipt(
        ready=not blockers,
        service_name=service_name,
        owners=owners,
        escalation_channels=escalation_channels,
        blockers=tuple(blockers),
        ownership_hash=ownership_hash,
    )


def plan_schema_drift_gate(
    schema_observation: Mapping[str, Any],
    drift_policy: Mapping[str, Any],
) -> SchemaDriftGateReceipt:
    """Evaluate schema drift against expected and observed field sets."""

    raw_dataset_name = str(schema_observation.get("dataset_name") or schema_observation.get("name") or "").strip()
    dataset_name = normalize_field_name(raw_dataset_name) if raw_dataset_name else ""
    expected_fields = {normalize_field_name(value) for value in _as_sequence(schema_observation.get("expected_fields")) if not _blank(value)}
    observed_fields = {normalize_field_name(value) for value in _as_sequence(schema_observation.get("observed_fields")) if not _blank(value)}
    added_fields = tuple(sorted(observed_fields - expected_fields))
    removed_fields = tuple(sorted(expected_fields - observed_fields))
    allowed_added_fields = {normalize_field_name(value) for value in _as_sequence(drift_policy.get("allowed_added_fields")) if not _blank(value)}
    blockers: list[str] = []
    if not dataset_name:
        blockers.append("missing_dataset_name")
    if not expected_fields:
        blockers.append("missing_expected_fields")
    if not observed_fields:
        blockers.append("missing_observed_fields")
    if drift_policy.get("block_removed_fields"):
        for field in removed_fields:
            blockers.append(f"removed_field:{field}")
    if drift_policy.get("block_unapproved_added_fields"):
        for field in added_fields:
            if field not in allowed_added_fields:
                blockers.append(f"unapproved_added_field:{field}")
    if drift_policy.get("require_owner") and _blank(schema_observation.get("owner")):
        blockers.append("missing_owner")
    if drift_policy.get("require_migration_receipt") and _blank(schema_observation.get("migration_receipt")):
        blockers.append("missing_migration_receipt")
    drift_hash = "schema-drift-gate:" + _digest(
        {
            "added_fields": added_fields,
            "blockers": blockers,
            "dataset_name": dataset_name,
            "removed_fields": removed_fields,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SchemaDriftGateReceipt(
        compatible=not blockers,
        dataset_name=dataset_name,
        added_fields=added_fields,
        removed_fields=removed_fields,
        blockers=tuple(blockers),
        drift_hash=drift_hash,
    )


def plan_migration_lock(
    migration_spec: Mapping[str, Any],
    lock_policy: Mapping[str, Any],
) -> MigrationLockPlanReceipt:
    """Plan a database migration lock with owner, timeout, stale-lock, and advisory-lock gates."""

    raw_migration_name = str(migration_spec.get("migration_name") or migration_spec.get("name") or "").strip()
    migration_name = normalize_field_name(raw_migration_name) if raw_migration_name else ""
    lock_key = str(migration_spec.get("lock_key") or "").strip()
    timeout_seconds = int(migration_spec.get("timeout_seconds") or 0)
    max_timeout_seconds = int(lock_policy.get("max_timeout_seconds") or 0)
    blockers: list[str] = []
    if not migration_name:
        blockers.append("missing_migration_name")
    if not lock_key:
        blockers.append("missing_lock_key")
    if timeout_seconds <= 0:
        blockers.append("missing_timeout_seconds")
    elif max_timeout_seconds and timeout_seconds > max_timeout_seconds:
        blockers.append("timeout_exceeds_policy")
    if lock_policy.get("require_owner") and _blank(migration_spec.get("owner")):
        blockers.append("missing_owner")
    if lock_policy.get("require_stale_lock_strategy") and _blank(migration_spec.get("stale_lock_strategy")):
        blockers.append("missing_stale_lock_strategy")
    if lock_policy.get("require_advisory_lock") and _blank(migration_spec.get("advisory_lock")):
        blockers.append("missing_advisory_lock")
    if lock_policy.get("require_rollback_receipt") and _blank(migration_spec.get("rollback_receipt")):
        blockers.append("missing_rollback_receipt")
    lock_hash = "migration-lock:" + _digest(
        {
            "blockers": blockers,
            "lock_key": lock_key,
            "migration_name": migration_name,
            "timeout_seconds": timeout_seconds,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return MigrationLockPlanReceipt(
        ready=not blockers,
        migration_name=migration_name,
        lock_key=lock_key,
        timeout_seconds=timeout_seconds,
        blockers=tuple(blockers),
        lock_hash=lock_hash,
    )


def plan_data_retention_enforcement(
    retention_spec: Mapping[str, Any],
    retention_policy: Mapping[str, Any],
) -> DataRetentionEnforcementPlanReceipt:
    """Plan data retention enforcement with purge, legal hold, dry-run, and audit gates."""

    raw_dataset_name = str(retention_spec.get("dataset_name") or retention_spec.get("name") or "").strip()
    dataset_name = normalize_field_name(raw_dataset_name) if raw_dataset_name else ""
    retention_days = int(retention_spec.get("retention_days") or 0)
    purge_strategy = normalize_field_name(retention_spec.get("purge_strategy") or "") if not _blank(retention_spec.get("purge_strategy")) else ""
    min_retention_days = int(retention_policy.get("min_retention_days") or 0)
    max_retention_days = int(retention_policy.get("max_retention_days") or 0)
    allowed_purge_strategies = {normalize_field_name(value) for value in _as_sequence(retention_policy.get("allowed_purge_strategies")) if not _blank(value)}
    blockers: list[str] = []
    if not dataset_name:
        blockers.append("missing_dataset_name")
    if retention_days <= 0:
        blockers.append("missing_retention_days")
    if min_retention_days and retention_days > 0 and retention_days < min_retention_days:
        blockers.append("retention_below_policy")
    if max_retention_days and retention_days > max_retention_days:
        blockers.append("retention_exceeds_policy")
    if not purge_strategy:
        blockers.append("missing_purge_strategy")
    elif allowed_purge_strategies and purge_strategy not in allowed_purge_strategies:
        blockers.append(f"purge_strategy_not_allowed:{purge_strategy}")
    if retention_policy.get("require_legal_hold_check") and _blank(retention_spec.get("legal_hold_check")):
        blockers.append("missing_legal_hold_check")
    if retention_policy.get("require_dry_run_receipt") and _blank(retention_spec.get("dry_run_receipt")):
        blockers.append("missing_dry_run_receipt")
    if retention_policy.get("require_audit_receipt") and _blank(retention_spec.get("audit_receipt")):
        blockers.append("missing_audit_receipt")
    retention_hash = "data-retention-enforcement:" + _digest(
        {
            "blockers": blockers,
            "dataset_name": dataset_name,
            "purge_strategy": purge_strategy,
            "retention_days": retention_days,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DataRetentionEnforcementPlanReceipt(
        ready=not blockers,
        dataset_name=dataset_name,
        retention_days=retention_days,
        purge_strategy=purge_strategy,
        blockers=tuple(blockers),
        retention_hash=retention_hash,
    )


def plan_tenant_data_boundary(
    boundary_spec: Mapping[str, Any],
    boundary_policy: Mapping[str, Any],
) -> TenantDataBoundaryPlanReceipt:
    """Plan tenant data boundary controls with RLS, encryption scope, tests, and audit gates."""

    raw_dataset_name = str(boundary_spec.get("dataset_name") or boundary_spec.get("name") or "").strip()
    dataset_name = normalize_field_name(raw_dataset_name) if raw_dataset_name else ""
    tenant_key = normalize_field_name(boundary_spec.get("tenant_key") or "") if not _blank(boundary_spec.get("tenant_key")) else ""
    boundary_controls = tuple(normalize_field_name(value) for value in _as_sequence(boundary_spec.get("boundary_controls")) if not _blank(value))
    control_set = set(boundary_controls)
    blockers: list[str] = []
    if not dataset_name:
        blockers.append("missing_dataset_name")
    if not tenant_key:
        blockers.append("missing_tenant_key")
    for control in _as_sequence(boundary_policy.get("required_controls")):
        control_name = normalize_field_name(control)
        if control_name and control_name not in control_set:
            blockers.append(f"missing_control:{control_name}")
    if boundary_policy.get("require_cross_tenant_negative_test") and _blank(boundary_spec.get("cross_tenant_negative_test")):
        blockers.append("missing_cross_tenant_negative_test")
    if boundary_policy.get("require_encryption_scope") and _blank(boundary_spec.get("encryption_scope")):
        blockers.append("missing_encryption_scope")
    if boundary_policy.get("require_audit_receipt") and _blank(boundary_spec.get("audit_receipt")):
        blockers.append("missing_audit_receipt")
    boundary_hash = "tenant-data-boundary:" + _digest(
        {
            "blockers": blockers,
            "boundary_controls": boundary_controls,
            "dataset_name": dataset_name,
            "tenant_key": tenant_key,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return TenantDataBoundaryPlanReceipt(
        ready=not blockers,
        dataset_name=dataset_name,
        tenant_key=tenant_key,
        boundary_controls=boundary_controls,
        blockers=tuple(blockers),
        boundary_hash=boundary_hash,
    )


def plan_backup_restore_drill(
    drill_spec: Mapping[str, Any],
    drill_policy: Mapping[str, Any],
) -> BackupRestoreDrillReceipt:
    """Plan a backup restore drill with artifact, target, RPO/RTO, checksum, and evidence gates."""

    raw_system_name = str(drill_spec.get("system_name") or drill_spec.get("name") or "").strip()
    system_name = normalize_field_name(raw_system_name) if raw_system_name else ""
    backup_artifact = str(drill_spec.get("backup_artifact") or "").strip()
    restore_target = str(drill_spec.get("restore_target") or "").strip()
    rpo_minutes = int(drill_spec.get("rpo_minutes") or 0)
    rto_minutes = int(drill_spec.get("rto_minutes") or 0)
    max_rpo_minutes = int(drill_policy.get("max_rpo_minutes") or 0)
    max_rto_minutes = int(drill_policy.get("max_rto_minutes") or 0)
    blockers: list[str] = []
    if not system_name:
        blockers.append("missing_system_name")
    if not backup_artifact:
        blockers.append("missing_backup_artifact")
    if not restore_target:
        blockers.append("missing_restore_target")
    if rpo_minutes <= 0:
        blockers.append("missing_rpo_minutes")
    elif max_rpo_minutes and rpo_minutes > max_rpo_minutes:
        blockers.append("rpo_exceeds_policy")
    if rto_minutes <= 0:
        blockers.append("missing_rto_minutes")
    elif max_rto_minutes and rto_minutes > max_rto_minutes:
        blockers.append("rto_exceeds_policy")
    if drill_policy.get("require_checksum_verification") and _blank(drill_spec.get("checksum_verification")):
        blockers.append("missing_checksum_verification")
    if drill_policy.get("require_restore_evidence") and _blank(drill_spec.get("restore_evidence")):
        blockers.append("missing_restore_evidence")
    if drill_policy.get("require_owner") and _blank(drill_spec.get("owner")):
        blockers.append("missing_owner")
    drill_hash = "backup-restore-drill:" + _digest(
        {
            "backup_artifact": backup_artifact,
            "blockers": blockers,
            "restore_target": restore_target,
            "system_name": system_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return BackupRestoreDrillReceipt(
        ready=not blockers,
        system_name=system_name,
        backup_artifact=backup_artifact,
        restore_target=restore_target,
        blockers=tuple(blockers),
        drill_hash=drill_hash,
    )


def plan_access_review_evidence(
    review_spec: Mapping[str, Any],
    review_policy: Mapping[str, Any],
) -> AccessReviewEvidenceReceipt:
    """Plan access review evidence with subject, role, manager, decision, and revocation gates."""

    raw_review_name = str(review_spec.get("review_name") or review_spec.get("name") or "").strip()
    review_name = normalize_field_name(raw_review_name) if raw_review_name else ""
    entries = tuple(dict(item) for item in _as_mapping_sequence(review_spec.get("entries")))
    subjects = tuple(str(entry.get("subject") or entry.get("user") or "").strip() for entry in entries if str(entry.get("subject") or entry.get("user") or "").strip())
    decisions = tuple(normalize_field_name(entry.get("decision") or "") for entry in entries if not _blank(entry.get("decision")))
    allowed_decisions = {normalize_field_name(value) for value in _as_sequence(review_policy.get("allowed_decisions")) if not _blank(value)}
    blockers: list[str] = []
    if not review_name:
        blockers.append("missing_review_name")
    if not entries:
        blockers.append("missing_entries")
    for index, entry in enumerate(entries):
        subject = str(entry.get("subject") or entry.get("user") or "").strip()
        decision = normalize_field_name(entry.get("decision") or "")
        if not subject:
            blockers.append(f"entry_{index + 1}_missing_subject")
        if _blank(entry.get("role")):
            blockers.append(f"entry_{index + 1}_missing_role")
        if review_policy.get("require_manager") and _blank(entry.get("manager")):
            blockers.append(f"entry_{index + 1}_missing_manager")
        if not decision:
            blockers.append(f"entry_{index + 1}_missing_decision")
        elif allowed_decisions and decision not in allowed_decisions:
            blockers.append(f"decision_not_allowed:{decision}")
        if decision == "revoke" and review_policy.get("require_revocation_ticket") and _blank(entry.get("revocation_ticket")):
            blockers.append(f"entry_{index + 1}_missing_revocation_ticket")
    if review_policy.get("require_review_period") and _blank(review_spec.get("review_period")):
        blockers.append("missing_review_period")
    review_hash = "access-review-evidence:" + _digest(
        {
            "blockers": blockers,
            "decisions": decisions,
            "review_name": review_name,
            "subjects": subjects,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return AccessReviewEvidenceReceipt(
        ready=not blockers,
        review_name=review_name,
        subjects=subjects,
        decisions=decisions,
        blockers=tuple(blockers),
        review_hash=review_hash,
    )


def plan_data_deletion_workflow(
    deletion_spec: Mapping[str, Any],
    deletion_policy: Mapping[str, Any],
) -> DataDeletionWorkflowPlanReceipt:
    """Plan a data deletion workflow with identity proof, scope, tombstone, propagation, and receipt gates."""

    raw_request_id = str(deletion_spec.get("request_id") or deletion_spec.get("id") or "").strip()
    request_id = normalize_field_name(raw_request_id) if raw_request_id else ""
    subject_id = str(deletion_spec.get("subject_id") or "").strip()
    deletion_scopes = tuple(normalize_field_name(value) for value in _as_sequence(deletion_spec.get("deletion_scopes")) if not _blank(value))
    required_scopes = {normalize_field_name(value) for value in _as_sequence(deletion_policy.get("required_scopes")) if not _blank(value)}
    scope_set = set(deletion_scopes)
    blockers: list[str] = []
    if not request_id:
        blockers.append("missing_request_id")
    if not subject_id:
        blockers.append("missing_subject_id")
    if not deletion_scopes:
        blockers.append("missing_deletion_scopes")
    for scope in sorted(required_scopes):
        if scope not in scope_set:
            blockers.append(f"missing_scope:{scope}")
    if deletion_policy.get("require_identity_verification") and _blank(deletion_spec.get("identity_verification")):
        blockers.append("missing_identity_verification")
    if deletion_policy.get("require_legal_hold_check") and _blank(deletion_spec.get("legal_hold_check")):
        blockers.append("missing_legal_hold_check")
    if deletion_policy.get("require_tombstone") and _blank(deletion_spec.get("tombstone")):
        blockers.append("missing_tombstone")
    if deletion_policy.get("require_propagation_receipt") and _blank(deletion_spec.get("propagation_receipt")):
        blockers.append("missing_propagation_receipt")
    deletion_hash = "data-deletion-workflow:" + _digest(
        {
            "blockers": blockers,
            "deletion_scopes": deletion_scopes,
            "request_id": request_id,
            "subject_id": subject_id,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return DataDeletionWorkflowPlanReceipt(
        ready=not blockers,
        request_id=request_id,
        subject_id=subject_id,
        deletion_scopes=deletion_scopes,
        blockers=tuple(blockers),
        deletion_hash=deletion_hash,
    )


def plan_privileged_access_approval(
    access_spec: Mapping[str, Any],
    access_policy: Mapping[str, Any],
) -> PrivilegedAccessApprovalPlanReceipt:
    """Plan privileged access approval with requester, role, duration, approval, and breakglass gates."""

    raw_request_id = str(access_spec.get("request_id") or access_spec.get("id") or "").strip()
    request_id = normalize_field_name(raw_request_id) if raw_request_id else ""
    requester = str(access_spec.get("requester") or "").strip()
    role = normalize_field_name(access_spec.get("role") or "") if not _blank(access_spec.get("role")) else ""
    duration_minutes = int(access_spec.get("duration_minutes") or 0)
    max_duration_minutes = int(access_policy.get("max_duration_minutes") or 0)
    allowed_roles = {normalize_field_name(value) for value in _as_sequence(access_policy.get("allowed_roles")) if not _blank(value)}
    blockers: list[str] = []
    if not request_id:
        blockers.append("missing_request_id")
    if not requester:
        blockers.append("missing_requester")
    if not role:
        blockers.append("missing_role")
    elif allowed_roles and role not in allowed_roles:
        blockers.append(f"role_not_allowed:{role}")
    if duration_minutes <= 0:
        blockers.append("missing_duration_minutes")
    elif max_duration_minutes and duration_minutes > max_duration_minutes:
        blockers.append("duration_exceeds_policy")
    if access_policy.get("require_approval_ticket") and _blank(access_spec.get("approval_ticket")):
        blockers.append("missing_approval_ticket")
    if access_policy.get("require_justification") and _blank(access_spec.get("justification")):
        blockers.append("missing_justification")
    if access_policy.get("require_expiry") and _blank(access_spec.get("expires_at")):
        blockers.append("missing_expiry")
    if access_policy.get("require_breakglass_reason") and access_spec.get("breakglass") and _blank(access_spec.get("breakglass_reason")):
        blockers.append("missing_breakglass_reason")
    approval_hash = "privileged-access-approval:" + _digest(
        {
            "blockers": blockers,
            "duration_minutes": duration_minutes,
            "request_id": request_id,
            "requester": requester,
            "role": role,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PrivilegedAccessApprovalPlanReceipt(
        ready=not blockers,
        request_id=request_id,
        requester=requester,
        role=role,
        blockers=tuple(blockers),
        approval_hash=approval_hash,
    )


def plan_connector_cursor_checkpoint(
    checkpoint_spec: Mapping[str, Any],
    checkpoint_policy: Mapping[str, Any],
) -> ConnectorCursorCheckpointPlanReceipt:
    """Plan connector cursor checkpointing with checkpoint interval, store, resume, and receipt gates."""

    raw_connector_name = str(checkpoint_spec.get("connector_name") or checkpoint_spec.get("name") or "").strip()
    connector_name = normalize_field_name(raw_connector_name) if raw_connector_name else ""
    cursor_field = normalize_field_name(checkpoint_spec.get("cursor_field") or "") if not _blank(checkpoint_spec.get("cursor_field")) else ""
    checkpoint_store = str(checkpoint_spec.get("checkpoint_store") or "").strip()
    checkpoint_interval_records = int(checkpoint_spec.get("checkpoint_interval_records") or 0)
    max_checkpoint_interval_records = int(checkpoint_policy.get("max_checkpoint_interval_records") or 0)
    blockers: list[str] = []
    if not connector_name:
        blockers.append("missing_connector_name")
    if not cursor_field:
        blockers.append("missing_cursor_field")
    if not checkpoint_store:
        blockers.append("missing_checkpoint_store")
    if checkpoint_interval_records <= 0:
        blockers.append("missing_checkpoint_interval_records")
    elif max_checkpoint_interval_records and checkpoint_interval_records > max_checkpoint_interval_records:
        blockers.append("checkpoint_interval_exceeds_policy")
    if checkpoint_policy.get("require_monotonic_cursor") and _blank(checkpoint_spec.get("monotonic_cursor")):
        blockers.append("missing_monotonic_cursor")
    if checkpoint_policy.get("require_resume_token") and _blank(checkpoint_spec.get("resume_token")):
        blockers.append("missing_resume_token")
    if checkpoint_policy.get("require_checkpoint_receipt") and _blank(checkpoint_spec.get("checkpoint_receipt")):
        blockers.append("missing_checkpoint_receipt")
    checkpoint_hash = "connector-cursor-checkpoint:" + _digest(
        {
            "blockers": blockers,
            "checkpoint_store": checkpoint_store,
            "connector_name": connector_name,
            "cursor_field": cursor_field,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ConnectorCursorCheckpointPlanReceipt(
        ready=not blockers,
        connector_name=connector_name,
        cursor_field=cursor_field,
        checkpoint_store=checkpoint_store,
        blockers=tuple(blockers),
        checkpoint_hash=checkpoint_hash,
    )


def plan_connector_field_mapping(
    mapping_spec: Mapping[str, Any],
    mapping_policy: Mapping[str, Any],
) -> ConnectorFieldMappingPlanReceipt:
    """Plan connector field mapping with required target field coverage and transform gates."""

    source_system = normalize_field_name(mapping_spec.get("source_system") or "") if not _blank(mapping_spec.get("source_system")) else ""
    target_system = normalize_field_name(mapping_spec.get("target_system") or "") if not _blank(mapping_spec.get("target_system")) else ""
    mappings = tuple(dict(item) for item in _as_mapping_sequence(mapping_spec.get("mappings")))
    target_fields = tuple(
        normalize_field_name(item.get("target_field") or item.get("target") or "")
        for item in mappings
        if not _blank(item.get("target_field") or item.get("target"))
    )
    target_field_set = set(target_fields)
    blockers: list[str] = []
    if not source_system:
        blockers.append("missing_source_system")
    if not target_system:
        blockers.append("missing_target_system")
    if not mappings:
        blockers.append("missing_mappings")
    for index, item in enumerate(mappings):
        source_field = normalize_field_name(item.get("source_field") or item.get("source") or "") if not _blank(item.get("source_field") or item.get("source")) else ""
        target_field = normalize_field_name(item.get("target_field") or item.get("target") or "") if not _blank(item.get("target_field") or item.get("target")) else ""
        if not source_field:
            blockers.append(f"mapping_{index + 1}_missing_source_field")
        if not target_field:
            blockers.append(f"mapping_{index + 1}_missing_target_field")
    for field in _as_sequence(mapping_policy.get("required_target_fields")):
        field_name = normalize_field_name(field)
        if field_name and field_name not in target_field_set:
            blockers.append(f"missing_target_field:{field_name}")
    for field in _as_sequence(mapping_policy.get("require_transform_for_fields")):
        field_name = normalize_field_name(field)
        if not field_name:
            continue
        matching = [item for item in mappings if normalize_field_name(item.get("target_field") or item.get("target") or "") == field_name]
        if matching and all(_blank(item.get("transform")) for item in matching):
            blockers.append(f"missing_transform_for_field:{field_name}")
    if mapping_policy.get("require_mapping_receipt") and _blank(mapping_spec.get("mapping_receipt")):
        blockers.append("missing_mapping_receipt")
    mapping_hash = "connector-field-mapping:" + _digest(
        {
            "blockers": blockers,
            "mappings": mappings,
            "source_system": source_system,
            "target_system": target_system,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ConnectorFieldMappingPlanReceipt(
        ready=not blockers,
        source_system=source_system,
        target_system=target_system,
        target_fields=target_fields,
        blockers=tuple(blockers),
        mapping_hash=mapping_hash,
    )


def plan_external_identity_map(
    identity_spec: Mapping[str, Any],
    identity_policy: Mapping[str, Any],
) -> ExternalIdentityMapPlanReceipt:
    """Plan external identity mapping with key coverage, mapping store, uniqueness, and collision gates."""

    source_system = normalize_field_name(identity_spec.get("source_system") or "") if not _blank(identity_spec.get("source_system")) else ""
    target_system = normalize_field_name(identity_spec.get("target_system") or "") if not _blank(identity_spec.get("target_system")) else ""
    identity_keys = tuple(normalize_field_name(value) for value in _as_sequence(identity_spec.get("identity_keys")) if not _blank(value))
    key_set = set(identity_keys)
    blockers: list[str] = []
    if not source_system:
        blockers.append("missing_source_system")
    if not target_system:
        blockers.append("missing_target_system")
    if not identity_keys:
        blockers.append("missing_identity_keys")
    for key in _as_sequence(identity_policy.get("required_identity_keys")):
        key_name = normalize_field_name(key)
        if key_name and key_name not in key_set:
            blockers.append(f"missing_identity_key:{key_name}")
    if identity_policy.get("require_mapping_store") and _blank(identity_spec.get("mapping_store")):
        blockers.append("missing_mapping_store")
    if identity_policy.get("require_unique_constraint") and _blank(identity_spec.get("unique_constraint")):
        blockers.append("missing_unique_constraint")
    if identity_policy.get("require_orphan_policy") and _blank(identity_spec.get("orphan_policy")):
        blockers.append("missing_orphan_policy")
    if identity_policy.get("require_collision_policy") and _blank(identity_spec.get("collision_policy")):
        blockers.append("missing_collision_policy")
    identity_hash = "external-identity-map:" + _digest(
        {
            "blockers": blockers,
            "identity_keys": identity_keys,
            "source_system": source_system,
            "target_system": target_system,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ExternalIdentityMapPlanReceipt(
        ready=not blockers,
        source_system=source_system,
        target_system=target_system,
        identity_keys=identity_keys,
        blockers=tuple(blockers),
        identity_hash=identity_hash,
    )


def plan_sync_conflict_resolution(
    conflict_spec: Mapping[str, Any],
    conflict_policy: Mapping[str, Any],
) -> SyncConflictResolutionPlanReceipt:
    """Plan sync conflict resolution with conflict keys, strategy, precedence, and audit gates."""

    raw_sync_name = str(conflict_spec.get("sync_name") or conflict_spec.get("name") or "").strip()
    sync_name = normalize_field_name(raw_sync_name) if raw_sync_name else ""
    conflict_keys = tuple(normalize_field_name(value) for value in _as_sequence(conflict_spec.get("conflict_keys")) if not _blank(value))
    resolution_strategy = normalize_field_name(conflict_spec.get("resolution_strategy") or "") if not _blank(conflict_spec.get("resolution_strategy")) else ""
    allowed_strategies = {normalize_field_name(value) for value in _as_sequence(conflict_policy.get("allowed_resolution_strategies")) if not _blank(value)}
    blockers: list[str] = []
    if not sync_name:
        blockers.append("missing_sync_name")
    if not conflict_keys:
        blockers.append("missing_conflict_keys")
    if not resolution_strategy:
        blockers.append("missing_resolution_strategy")
    elif allowed_strategies and resolution_strategy not in allowed_strategies:
        blockers.append(f"resolution_strategy_not_allowed:{resolution_strategy}")
    if conflict_policy.get("require_precedence_rule") and _blank(conflict_spec.get("precedence_rule")):
        blockers.append("missing_precedence_rule")
    if conflict_policy.get("require_manual_review_queue") and _blank(conflict_spec.get("manual_review_queue")):
        blockers.append("missing_manual_review_queue")
    if conflict_policy.get("require_conflict_receipt") and _blank(conflict_spec.get("conflict_receipt")):
        blockers.append("missing_conflict_receipt")
    conflict_hash = "sync-conflict-resolution:" + _digest(
        {
            "blockers": blockers,
            "conflict_keys": conflict_keys,
            "resolution_strategy": resolution_strategy,
            "sync_name": sync_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SyncConflictResolutionPlanReceipt(
        ready=not blockers,
        sync_name=sync_name,
        conflict_keys=conflict_keys,
        resolution_strategy=resolution_strategy,
        blockers=tuple(blockers),
        conflict_hash=conflict_hash,
    )


def plan_connector_rate_limit_budget(
    budget_spec: Mapping[str, Any],
    budget_policy: Mapping[str, Any],
) -> ConnectorRateLimitBudgetPlanReceipt:
    """Plan connector rate-limit budget with window, burst, retry-after, and alert gates."""

    raw_connector_name = str(budget_spec.get("connector_name") or budget_spec.get("name") or "").strip()
    connector_name = normalize_field_name(raw_connector_name) if raw_connector_name else ""
    requests_per_window = int(budget_spec.get("requests_per_window") or 0)
    window_seconds = int(budget_spec.get("window_seconds") or 0)
    max_requests_per_window = int(budget_policy.get("max_requests_per_window") or 0)
    min_window_seconds = int(budget_policy.get("min_window_seconds") or 0)
    blockers: list[str] = []
    if not connector_name:
        blockers.append("missing_connector_name")
    if requests_per_window <= 0:
        blockers.append("missing_requests_per_window")
    elif max_requests_per_window and requests_per_window > max_requests_per_window:
        blockers.append("requests_per_window_exceeds_policy")
    if window_seconds <= 0:
        blockers.append("missing_window_seconds")
    elif min_window_seconds and window_seconds < min_window_seconds:
        blockers.append("window_below_policy")
    if budget_policy.get("require_retry_after_handling") and _blank(budget_spec.get("retry_after_handling")):
        blockers.append("missing_retry_after_handling")
    if budget_policy.get("require_burst_policy") and _blank(budget_spec.get("burst_policy")):
        blockers.append("missing_burst_policy")
    if budget_policy.get("require_budget_alert") and _blank(budget_spec.get("budget_alert")):
        blockers.append("missing_budget_alert")
    budget_hash = "connector-rate-limit-budget:" + _digest(
        {
            "blockers": blockers,
            "connector_name": connector_name,
            "requests_per_window": requests_per_window,
            "window_seconds": window_seconds,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ConnectorRateLimitBudgetPlanReceipt(
        ready=not blockers,
        connector_name=connector_name,
        requests_per_window=requests_per_window,
        window_seconds=window_seconds,
        blockers=tuple(blockers),
        budget_hash=budget_hash,
    )


def plan_webhook_replay_window(
    replay_spec: Mapping[str, Any],
    replay_policy: Mapping[str, Any],
) -> WebhookReplayWindowPlanReceipt:
    """Plan webhook replay window with dedupe, signature, replay receipt, and source event store gates."""

    raw_webhook_name = str(replay_spec.get("webhook_name") or replay_spec.get("name") or "").strip()
    webhook_name = normalize_field_name(raw_webhook_name) if raw_webhook_name else ""
    replay_window_minutes = int(replay_spec.get("replay_window_minutes") or 0)
    dedupe_key = normalize_field_name(replay_spec.get("dedupe_key") or "") if not _blank(replay_spec.get("dedupe_key")) else ""
    max_replay_window_minutes = int(replay_policy.get("max_replay_window_minutes") or 0)
    blockers: list[str] = []
    if not webhook_name:
        blockers.append("missing_webhook_name")
    if replay_window_minutes <= 0:
        blockers.append("missing_replay_window_minutes")
    elif max_replay_window_minutes and replay_window_minutes > max_replay_window_minutes:
        blockers.append("replay_window_exceeds_policy")
    if not dedupe_key:
        blockers.append("missing_dedupe_key")
    if replay_policy.get("require_signature_validation") and _blank(replay_spec.get("signature_validation")):
        blockers.append("missing_signature_validation")
    if replay_policy.get("require_source_event_store") and _blank(replay_spec.get("source_event_store")):
        blockers.append("missing_source_event_store")
    if replay_policy.get("require_replay_receipt") and _blank(replay_spec.get("replay_receipt")):
        blockers.append("missing_replay_receipt")
    replay_hash = "webhook-replay-window:" + _digest(
        {
            "blockers": blockers,
            "dedupe_key": dedupe_key,
            "replay_window_minutes": replay_window_minutes,
            "webhook_name": webhook_name,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return WebhookReplayWindowPlanReceipt(
        ready=not blockers,
        webhook_name=webhook_name,
        replay_window_minutes=replay_window_minutes,
        dedupe_key=dedupe_key,
        blockers=tuple(blockers),
        replay_hash=replay_hash,
    )


def plan_connector_error_quarantine(
    quarantine_spec: Mapping[str, Any],
    quarantine_policy: Mapping[str, Any],
) -> ConnectorErrorQuarantinePlanReceipt:
    """Plan connector error quarantine with error class routing, sink, triage, and replay gates."""

    raw_connector_name = str(quarantine_spec.get("connector_name") or quarantine_spec.get("name") or "").strip()
    connector_name = normalize_field_name(raw_connector_name) if raw_connector_name else ""
    error_classes = tuple(normalize_field_name(value) for value in _as_sequence(quarantine_spec.get("error_classes")) if not _blank(value))
    quarantine_sink = str(quarantine_spec.get("quarantine_sink") or "").strip()
    required_error_classes = {normalize_field_name(value) for value in _as_sequence(quarantine_policy.get("required_error_classes")) if not _blank(value)}
    error_class_set = set(error_classes)
    blockers: list[str] = []
    if not connector_name:
        blockers.append("missing_connector_name")
    if not error_classes:
        blockers.append("missing_error_classes")
    for error_class in sorted(required_error_classes):
        if error_class not in error_class_set:
            blockers.append(f"missing_error_class:{error_class}")
    if not quarantine_sink:
        blockers.append("missing_quarantine_sink")
    if quarantine_policy.get("require_triage_owner") and _blank(quarantine_spec.get("triage_owner")):
        blockers.append("missing_triage_owner")
    if quarantine_policy.get("require_replay_policy") and _blank(quarantine_spec.get("replay_policy")):
        blockers.append("missing_replay_policy")
    if quarantine_policy.get("require_error_receipt") and _blank(quarantine_spec.get("error_receipt")):
        blockers.append("missing_error_receipt")
    quarantine_hash = "connector-error-quarantine:" + _digest(
        {
            "blockers": blockers,
            "connector_name": connector_name,
            "error_classes": error_classes,
            "quarantine_sink": quarantine_sink,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return ConnectorErrorQuarantinePlanReceipt(
        ready=not blockers,
        connector_name=connector_name,
        error_classes=error_classes,
        quarantine_sink=quarantine_sink,
        blockers=tuple(blockers),
        quarantine_hash=quarantine_hash,
    )


def plan_sync_reconciliation_report(
    report_spec: Mapping[str, Any],
    report_policy: Mapping[str, Any],
) -> SyncReconciliationReportPlanReceipt:
    """Plan sync reconciliation reporting with count fields, mismatch threshold, sample, and owner gates."""

    raw_sync_name = str(report_spec.get("sync_name") or report_spec.get("name") or "").strip()
    sync_name = normalize_field_name(raw_sync_name) if raw_sync_name else ""
    source_count_field = normalize_field_name(report_spec.get("source_count_field") or "") if not _blank(report_spec.get("source_count_field")) else ""
    target_count_field = normalize_field_name(report_spec.get("target_count_field") or "") if not _blank(report_spec.get("target_count_field")) else ""
    mismatch_threshold = int(report_spec.get("mismatch_threshold") or 0)
    max_mismatch_threshold = int(report_policy.get("max_mismatch_threshold") or 0)
    blockers: list[str] = []
    if not sync_name:
        blockers.append("missing_sync_name")
    if not source_count_field:
        blockers.append("missing_source_count_field")
    if not target_count_field:
        blockers.append("missing_target_count_field")
    if mismatch_threshold <= 0:
        blockers.append("missing_mismatch_threshold")
    elif max_mismatch_threshold and mismatch_threshold > max_mismatch_threshold:
        blockers.append("mismatch_threshold_exceeds_policy")
    if report_policy.get("require_sample_rows") and not _as_sequence(report_spec.get("sample_rows")):
        blockers.append("missing_sample_rows")
    if report_policy.get("require_reconciliation_owner") and _blank(report_spec.get("reconciliation_owner")):
        blockers.append("missing_reconciliation_owner")
    if report_policy.get("require_report_receipt") and _blank(report_spec.get("report_receipt")):
        blockers.append("missing_report_receipt")
    report_hash = "sync-reconciliation-report:" + _digest(
        {
            "blockers": blockers,
            "source_count_field": source_count_field,
            "sync_name": sync_name,
            "target_count_field": target_count_field,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SyncReconciliationReportPlanReceipt(
        ready=not blockers,
        sync_name=sync_name,
        source_count_field=source_count_field,
        target_count_field=target_count_field,
        blockers=tuple(blockers),
        report_hash=report_hash,
    )


def plan_primitive_candidate_intake(
    candidate_card: Mapping[str, Any],
    intake_policy: Mapping[str, Any],
) -> PrimitiveCandidateIntakeReceipt:
    """Plan registry intake for a candidate primitive while preserving the candidate boundary."""

    primitive_id = str(candidate_card.get("primitive_id") or candidate_card.get("id") or "").strip()
    kind = str(candidate_card.get("kind") or "").strip()
    group_contract = candidate_card.get("group_contract") if isinstance(candidate_card.get("group_contract"), Mapping) else {}
    input_edge = str(
        candidate_card.get("input_edge")
        or group_contract.get("visible_input_edge")
        or ""
    ).strip()
    output_edge = str(
        candidate_card.get("output_edge")
        or group_contract.get("visible_output_edge")
        or ""
    ).strip()
    core_group_edge = str(candidate_card.get("core_group_edge") or group_contract.get("core_group_edge") or "").strip()
    hidden_member_edges = tuple(
        str(value)
        for value in _as_sequence(candidate_card.get("hidden_member_edges") or group_contract.get("hidden_member_edges"))
        if str(value).strip()
    )
    proof_requirements = tuple(str(value) for value in _as_sequence(candidate_card.get("proof_requirements")) if str(value).strip())
    adapter_mutators = tuple(str(value) for value in _as_sequence(candidate_card.get("adapter_mutators")) if str(value).strip())
    runtime_targets = tuple(str(value) for value in _as_sequence(candidate_card.get("runtime_targets")) if str(value).strip())
    effects = {str(value) for value in _as_sequence(candidate_card.get("effects")) if str(value).strip()}
    blockers: list[str] = []
    if not primitive_id:
        blockers.append("missing_primitive_id")
    for prefix in _as_sequence(intake_policy.get("required_id_prefixes")):
        prefix_text = str(prefix)
        if prefix_text and primitive_id and not primitive_id.startswith(prefix_text):
            blockers.append(f"primitive_id_missing_prefix:{prefix_text}")
    if not kind:
        blockers.append("missing_kind")
    allowed_kinds = {str(value) for value in _as_sequence(intake_policy.get("allowed_kinds")) if str(value).strip()}
    if allowed_kinds and kind and kind not in allowed_kinds:
        blockers.append(f"kind_not_allowed:{kind}")
    if not input_edge:
        blockers.append("missing_input_edge")
    if not output_edge:
        blockers.append("missing_output_edge")
    if intake_policy.get("require_core_group_edge") and not core_group_edge:
        blockers.append("missing_core_group_edge")
    min_hidden_member_edges = int(intake_policy.get("min_hidden_member_edges") or 0)
    if min_hidden_member_edges and len(hidden_member_edges) < min_hidden_member_edges:
        blockers.append("hidden_member_edges_below_policy")
    if intake_policy.get("require_adapter_mutator") and not adapter_mutators:
        blockers.append("missing_adapter_mutators")
    if intake_policy.get("require_runtime_targets") and not runtime_targets:
        blockers.append("missing_runtime_targets")
    for effect in _as_sequence(intake_policy.get("required_effects")):
        effect_text = str(effect)
        if effect_text and effect_text not in effects:
            blockers.append(f"missing_effect:{effect_text}")
    if intake_policy.get("require_proof_requirements") and not proof_requirements:
        blockers.append("missing_proof_requirements")
    if intake_policy.get("require_source_ref") and not isinstance(candidate_card.get("source_ref"), Mapping):
        blockers.append("missing_source_ref")
    if intake_policy.get("require_proof_refs") and not _as_sequence(candidate_card.get("proof_refs")):
        blockers.append("missing_proof_refs")
    if intake_policy.get("require_candidate_boundary"):
        if candidate_card.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if candidate_card.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")
    intake_hash = "primitive-candidate-intake:" + _digest(
        {
            "blockers": blockers,
            "core_group_edge": core_group_edge,
            "hidden_member_edges": hidden_member_edges,
            "input_edge": input_edge,
            "kind": kind,
            "output_edge": output_edge,
            "primitive_id": primitive_id,
            "proof_requirements": proof_requirements,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PrimitiveCandidateIntakeReceipt(
        ready=not blockers,
        primitive_id=primitive_id,
        kind=kind,
        input_edge=input_edge,
        output_edge=output_edge,
        blockers=tuple(blockers),
        intake_hash=intake_hash,
    )


def plan_primitive_reuse_observation(
    observation_spec: Mapping[str, Any],
    reuse_policy: Mapping[str, Any],
) -> PrimitiveReuseObservationReceipt:
    """Plan primitive reuse observations across runtime shapes for one core group edge."""

    observations = tuple(dict(item) for item in _as_mapping_sequence(observation_spec.get("observations")))
    primitive_ids = tuple(
        sorted({str(item.get("primitive_id") or item.get("id") or "").strip() for item in observations if str(item.get("primitive_id") or item.get("id") or "").strip()})
    )
    runtime_shapes = tuple(
        sorted({str(item.get("runtime_shape") or item.get("primitive_kind") or item.get("kind") or "").strip() for item in observations if str(item.get("runtime_shape") or item.get("primitive_kind") or item.get("kind") or "").strip()})
    )
    core_group_edges = tuple(
        sorted({str(item.get("core_group_edge") or observation_spec.get("core_group_edge") or "").strip() for item in observations if str(item.get("core_group_edge") or observation_spec.get("core_group_edge") or "").strip()})
    )
    blockers: list[str] = []
    if not observations:
        blockers.append("missing_observations")
    min_observations = int(reuse_policy.get("min_observations") or 0)
    if min_observations and len(observations) < min_observations:
        blockers.append("observation_count_below_policy")
    min_runtime_shapes = int(reuse_policy.get("min_runtime_shapes") or 0)
    if min_runtime_shapes and len(runtime_shapes) < min_runtime_shapes:
        blockers.append("runtime_shape_count_below_policy")
    if not core_group_edges:
        blockers.append("missing_core_group_edge")
    if reuse_policy.get("require_single_core_group_edge") and len(core_group_edges) > 1:
        blockers.append("multiple_core_group_edges")
    if reuse_policy.get("require_route_reused"):
        for index, observation in enumerate(observations):
            if observation.get("route_reused") is not True:
                blockers.append(f"observation_{index + 1}_route_not_reused")
    if reuse_policy.get("require_proof_status_pass"):
        for index, observation in enumerate(observations):
            if str(observation.get("proof_status") or "") != "pass":
                blockers.append(f"observation_{index + 1}_proof_not_pass")
    if reuse_policy.get("require_candidate_boundary"):
        for index, observation in enumerate(observations):
            if observation.get("candidate") is not True:
                blockers.append(f"observation_{index + 1}_candidate_boundary_not_declared")
            if observation.get("serves_truth") is not False:
                blockers.append(f"observation_{index + 1}_serves_truth_must_be_false")
    core_group_edge = core_group_edges[0] if len(core_group_edges) == 1 else ""
    observation_hash = "primitive-reuse-observation:" + _digest(
        {
            "blockers": blockers,
            "core_group_edges": core_group_edges,
            "primitive_ids": primitive_ids,
            "runtime_shapes": runtime_shapes,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PrimitiveReuseObservationReceipt(
        ready=not blockers,
        core_group_edge=core_group_edge,
        primitive_ids=primitive_ids,
        runtime_shapes=runtime_shapes,
        blockers=tuple(blockers),
        observation_hash=observation_hash,
    )


def plan_primitive_proof_coverage_matrix(
    coverage_spec: Mapping[str, Any],
    coverage_policy: Mapping[str, Any],
) -> PrimitiveProofCoverageMatrixReceipt:
    """Plan proof coverage for candidate primitive cards and proof bundle rows."""

    candidate_cards = tuple(dict(item) for item in _as_mapping_sequence(coverage_spec.get("candidate_cards") or coverage_spec.get("cards")))
    proof_bundles = tuple(dict(item) for item in _as_mapping_sequence(coverage_spec.get("proof_bundles") or coverage_spec.get("proofs")))
    proof_status_required = str(coverage_policy.get("required_status") or "pass")
    blockers: list[str] = []
    missing_requirements: list[str] = []
    if not candidate_cards:
        blockers.append("missing_candidate_cards")
    if coverage_policy.get("require_proof_bundles") and not proof_bundles:
        blockers.append("missing_proof_bundles")
    proof_index: dict[str, set[str]] = {}
    failed_proofs: list[str] = []
    for proof in proof_bundles:
        subject_id = str(proof.get("subject_id") or proof.get("primitive_id") or "").strip()
        proof_kind = str(proof.get("proof_kind") or proof.get("kind") or "").strip()
        if not subject_id or not proof_kind:
            continue
        proof_index.setdefault(subject_id, set()).add(proof_kind)
        if proof_status_required and str(proof.get("status") or "") != proof_status_required:
            failed_proofs.append(f"{subject_id}:{proof_kind}")
    for card in candidate_cards:
        primitive_id = str(card.get("primitive_id") or card.get("id") or "").strip()
        if not primitive_id:
            blockers.append("card_missing_primitive_id")
            continue
        if coverage_policy.get("require_candidate_boundary"):
            if card.get("candidate") is not True:
                blockers.append(f"{primitive_id}:candidate_boundary_not_declared")
            if card.get("serves_truth") is not False:
                blockers.append(f"{primitive_id}:serves_truth_must_be_false")
        for requirement in _as_sequence(card.get("proof_requirements")):
            requirement_text = str(requirement).strip()
            if requirement_text and requirement_text not in proof_index.get(primitive_id, set()):
                missing_requirements.append(f"{primitive_id}:{requirement_text}")
    if missing_requirements:
        blockers.append("proof_requirements_missing")
    if failed_proofs:
        blockers.append("proof_status_not_pass")
    primitive_ids = tuple(
        str(card.get("primitive_id") or card.get("id") or "").strip()
        for card in candidate_cards
        if str(card.get("primitive_id") or card.get("id") or "").strip()
    )
    coverage_hash = "primitive-proof-coverage:" + _digest(
        {
            "blockers": blockers,
            "failed_proofs": failed_proofs,
            "missing_requirements": missing_requirements,
            "primitive_ids": primitive_ids,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PrimitiveProofCoverageMatrixReceipt(
        ready=not blockers,
        primitive_ids=primitive_ids,
        missing_requirements=tuple(missing_requirements),
        blockers=tuple(blockers),
        coverage_hash=coverage_hash,
    )


def plan_primitive_promotion_review(
    review_spec: Mapping[str, Any],
    review_policy: Mapping[str, Any],
) -> PrimitivePromotionReviewReceipt:
    """Plan a primitive promotion review without setting the candidate as truth."""

    primitive_id = str(review_spec.get("primitive_id") or review_spec.get("subject_id") or "").strip()
    proof_status = str(review_spec.get("proof_status") or "").strip()
    owner_review_status = str(review_spec.get("owner_review_status") or review_spec.get("owner_review") or "").strip()
    blockers: list[str] = []
    if not primitive_id:
        blockers.append("missing_primitive_id")
    if review_policy.get("require_proof_status_pass") and proof_status != "pass":
        blockers.append("proof_status_not_pass")
    if review_policy.get("require_proof_bundle_ref") and _blank(review_spec.get("proof_bundle_ref")):
        blockers.append("missing_proof_bundle_ref")
    if review_policy.get("require_source_ref") and not isinstance(review_spec.get("source_ref"), Mapping):
        blockers.append("missing_source_ref")
    approved_owner_statuses = {str(value) for value in _as_sequence(review_policy.get("approved_owner_statuses") or ("approved",)) if str(value).strip()}
    if review_policy.get("require_owner_review") and owner_review_status not in approved_owner_statuses:
        blockers.append("owner_review_required")
    for blocker in _as_sequence(review_spec.get("promotion_blockers")):
        blocker_text = str(blocker)
        if blocker_text:
            blockers.append(f"promotion_blocker:{blocker_text}")
    if review_policy.get("require_candidate_boundary"):
        if review_spec.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if review_spec.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false_before_promotion")
    if "owner_review_required" in blockers:
        gate_status = "blocked_pending_owner_review"
    elif blockers:
        gate_status = "blocked"
    else:
        gate_status = str(review_policy.get("approved_gate_status") or "approved_for_owner_promotion")
    review_hash = "primitive-promotion-review:" + _digest(
        {
            "blockers": blockers,
            "gate_status": gate_status,
            "owner_review_status": owner_review_status,
            "primitive_id": primitive_id,
            "proof_status": proof_status,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PrimitivePromotionReviewReceipt(
        promotion_allowed=not blockers,
        primitive_id=primitive_id,
        promotion_gate_status=gate_status,
        blockers=tuple(blockers),
        review_hash=review_hash,
    )


def plan_registry_publish_manifest(
    registry_spec: Mapping[str, Any],
    publish_policy: Mapping[str, Any],
) -> RegistryPublishManifestPlanReceipt:
    """Plan an AIDevObserver-consumable registry publish manifest with proof and gate coverage."""

    raw_registry_name = str(registry_spec.get("registry_name") or registry_spec.get("name") or "").strip()
    registry_name = normalize_field_name(raw_registry_name) if raw_registry_name else ""
    cards = tuple(dict(item) for item in _as_mapping_sequence(registry_spec.get("cards")))
    proofs = tuple(dict(item) for item in _as_mapping_sequence(registry_spec.get("proof_bundles") or registry_spec.get("proofs")))
    gates = tuple(dict(item) for item in _as_mapping_sequence(registry_spec.get("promotion_gates") or registry_spec.get("gates")))
    search_targets = tuple(str(value) for value in _as_sequence(registry_spec.get("search_targets")) if str(value).strip())
    proof_subjects = {str(item.get("subject_id") or item.get("primitive_id") or "").strip() for item in proofs}
    gate_subjects = {str(item.get("subject_id") or item.get("primitive_id") or "").strip() for item in gates}
    blockers: list[str] = []
    if not registry_name:
        blockers.append("missing_registry_name")
    if not cards:
        blockers.append("missing_cards")
    min_cards = int(publish_policy.get("min_cards") or 0)
    if min_cards and len(cards) < min_cards:
        blockers.append("card_count_below_policy")
    for target in _as_sequence(publish_policy.get("required_search_targets")):
        target_text = str(target)
        if target_text and target_text not in search_targets:
            blockers.append(f"missing_search_target:{target_text}")
    for card in cards:
        primitive_id = str(card.get("primitive_id") or card.get("id") or "").strip()
        if not primitive_id:
            blockers.append("card_missing_primitive_id")
            continue
        if publish_policy.get("require_candidate_boundary"):
            if card.get("candidate") is not True:
                blockers.append(f"{primitive_id}:candidate_boundary_not_declared")
            if card.get("serves_truth") is not False:
                blockers.append(f"{primitive_id}:serves_truth_must_be_false")
        if publish_policy.get("require_proof_bundle") and primitive_id not in proof_subjects:
            blockers.append(f"{primitive_id}:missing_proof_bundle")
        if publish_policy.get("require_promotion_gate") and primitive_id not in gate_subjects:
            blockers.append(f"{primitive_id}:missing_promotion_gate")
    manifest_hash = "registry-publish-manifest:" + _digest(
        {
            "blockers": blockers,
            "card_count": len(cards),
            "registry_name": registry_name,
            "search_targets": search_targets,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return RegistryPublishManifestPlanReceipt(
        ready=not blockers,
        registry_name=registry_name,
        card_count=len(cards),
        search_targets=search_targets,
        blockers=tuple(blockers),
        manifest_hash=manifest_hash,
    )


def plan_benchmark_run_arm(
    run_spec: Mapping[str, Any],
    arm_policy: Mapping[str, Any],
) -> BenchmarkRunArmPlanReceipt:
    """Plan one baseline or primitive-first benchmark arm with metric and artifact gates."""

    raw_arm_name = str(run_spec.get("arm_name") or run_spec.get("name") or "").strip()
    arm_name = normalize_field_name(raw_arm_name) if raw_arm_name else ""
    tasks = tuple(str(value) for value in _as_sequence(run_spec.get("tasks") or run_spec.get("task_ids")) if str(value).strip())
    metrics = tuple(normalize_field_name(value) for value in _as_sequence(run_spec.get("metrics")) if str(value).strip())
    metric_set = set(metrics)
    required_metrics = tuple(normalize_field_name(value) for value in _as_sequence(arm_policy.get("required_metrics")) if str(value).strip())
    allowed_arm_names = {normalize_field_name(value) for value in _as_sequence(arm_policy.get("allowed_arm_names")) if str(value).strip()}
    blockers: list[str] = []
    if not arm_name:
        blockers.append("missing_arm_name")
    elif allowed_arm_names and arm_name not in allowed_arm_names:
        blockers.append(f"arm_name_not_allowed:{arm_name}")
    if not tasks:
        blockers.append("missing_tasks")
    min_tasks = int(arm_policy.get("min_tasks") or 0)
    if min_tasks and len(tasks) < min_tasks:
        blockers.append("task_count_below_policy")
    if arm_policy.get("require_runner") and _blank(run_spec.get("runner")):
        blockers.append("missing_runner")
    for metric in required_metrics:
        if metric not in metric_set:
            blockers.append(f"missing_metric:{metric}")
    if arm_policy.get("require_artifact_manifest") and _blank(run_spec.get("artifact_manifest")):
        blockers.append("missing_artifact_manifest")
    if arm_policy.get("require_run_receipt") and _blank(run_spec.get("run_receipt")):
        blockers.append("missing_run_receipt")
    if arm_policy.get("require_candidate_boundary"):
        if run_spec.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if run_spec.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")
    arm_hash = "benchmark-run-arm:" + _digest(
        {
            "arm_name": arm_name,
            "blockers": blockers,
            "metrics": metrics,
            "task_count": len(tasks),
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return BenchmarkRunArmPlanReceipt(
        ready=not blockers,
        arm_name=arm_name,
        task_count=len(tasks),
        metrics=metrics,
        blockers=tuple(blockers),
        arm_hash=arm_hash,
    )


def plan_primitive_lift_comparison(
    comparison_spec: Mapping[str, Any],
    lift_policy: Mapping[str, Any],
) -> PrimitiveLiftComparisonReceipt:
    """Plan baseline-vs-primitive lift comparison across scored dimensions."""

    baseline_arm = normalize_field_name(comparison_spec.get("baseline_arm") or "baseline")
    candidate_arm = normalize_field_name(comparison_spec.get("candidate_arm") or "candidate")
    baseline_metrics = comparison_spec.get("baseline_metrics") if isinstance(comparison_spec.get("baseline_metrics"), Mapping) else {}
    candidate_metrics = comparison_spec.get("candidate_metrics") if isinstance(comparison_spec.get("candidate_metrics"), Mapping) else {}
    dimensions = tuple(dict(item) for item in _as_mapping_sequence(lift_policy.get("dimensions")))
    blockers: list[str] = []
    winning_dimensions: list[str] = []
    if not baseline_metrics:
        blockers.append("missing_baseline_metrics")
    if not candidate_metrics:
        blockers.append("missing_candidate_metrics")
    if not dimensions:
        blockers.append("missing_dimensions")
    for dimension in dimensions:
        name = normalize_field_name(dimension.get("name") or dimension.get("metric") or "")
        if not name:
            blockers.append("dimension_missing_name")
            continue
        if name not in baseline_metrics:
            blockers.append(f"missing_baseline_metric:{name}")
            continue
        if name not in candidate_metrics:
            blockers.append(f"missing_candidate_metric:{name}")
            continue
        baseline_value = float(baseline_metrics.get(name) or 0)
        candidate_value = float(candidate_metrics.get(name) or 0)
        direction = str(dimension.get("direction") or "higher_is_better")
        min_delta = float(dimension.get("min_delta") or lift_policy.get("min_delta") or 0)
        if direction == "lower_is_better":
            delta = baseline_value - candidate_value
        else:
            delta = candidate_value - baseline_value
        if delta >= min_delta:
            winning_dimensions.append(name)
        elif dimension.get("required"):
            blockers.append(f"dimension_lift_below_policy:{name}")
    min_winning_dimensions = int(lift_policy.get("min_winning_dimensions") or 0)
    if min_winning_dimensions and len(winning_dimensions) < min_winning_dimensions:
        blockers.append("winning_dimension_count_below_policy")
    if lift_policy.get("require_primitive_usage") and not _as_sequence(comparison_spec.get("primitive_groups_used")):
        blockers.append("missing_primitive_groups_used")
    if lift_policy.get("require_candidate_boundary"):
        if comparison_spec.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if comparison_spec.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")
    comparison_hash = "primitive-lift-comparison:" + _digest(
        {
            "baseline_arm": baseline_arm,
            "blockers": blockers,
            "candidate_arm": candidate_arm,
            "winning_dimensions": winning_dimensions,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PrimitiveLiftComparisonReceipt(
        ready=not blockers,
        baseline_arm=baseline_arm,
        candidate_arm=candidate_arm,
        winning_dimensions=tuple(winning_dimensions),
        blockers=tuple(blockers),
        comparison_hash=comparison_hash,
    )


def plan_token_savings_attribution(
    token_trace: Mapping[str, Any],
    token_policy: Mapping[str, Any],
) -> TokenSavingsAttributionReceipt:
    """Plan token-savings attribution for primitive-first benchmark runs."""

    baseline_tokens = int(token_trace.get("baseline_prompt_tokens") or 0) + int(token_trace.get("baseline_completion_tokens") or 0)
    candidate_tokens = int(token_trace.get("candidate_prompt_tokens") or 0) + int(token_trace.get("candidate_completion_tokens") or 0)
    primitive_ids = tuple(str(value) for value in _as_sequence(token_trace.get("primitive_ids") or token_trace.get("primitive_groups_used")) if str(value).strip())
    blockers: list[str] = []
    if baseline_tokens <= 0:
        blockers.append("missing_baseline_tokens")
    if candidate_tokens <= 0:
        blockers.append("missing_candidate_tokens")
    if token_policy.get("require_primitives") and not primitive_ids:
        blockers.append("missing_primitive_ids")
    savings_percent = 0.0
    if baseline_tokens > 0:
        savings_percent = round(((baseline_tokens - candidate_tokens) / baseline_tokens) * 100, 2)
    min_savings_percent = float(token_policy.get("min_savings_percent") or 0)
    if min_savings_percent and savings_percent < min_savings_percent:
        blockers.append("token_savings_below_policy")
    if token_policy.get("require_trace_ref") and _blank(token_trace.get("trace_ref")):
        blockers.append("missing_trace_ref")
    if token_policy.get("require_candidate_boundary"):
        if token_trace.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if token_trace.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")
    attribution_hash = "token-savings-attribution:" + _digest(
        {
            "baseline_tokens": baseline_tokens,
            "blockers": blockers,
            "candidate_tokens": candidate_tokens,
            "primitive_ids": primitive_ids,
            "savings_percent": savings_percent,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return TokenSavingsAttributionReceipt(
        ready=not blockers,
        baseline_tokens=baseline_tokens,
        candidate_tokens=candidate_tokens,
        savings_percent=savings_percent,
        primitive_ids=primitive_ids,
        blockers=tuple(blockers),
        attribution_hash=attribution_hash,
    )


def plan_pitfall_avoidance_matrix(
    pitfall_spec: Mapping[str, Any],
    pitfall_policy: Mapping[str, Any],
) -> PitfallAvoidanceMatrixReceipt:
    """Plan evidence-backed pitfall avoidance scoring for a benchmark run."""

    pitfall_ids = tuple(normalize_field_name(value) for value in _as_sequence(pitfall_spec.get("pitfall_ids") or pitfall_spec.get("pitfalls")) if str(value).strip())
    evidence_rows = tuple(dict(item) for item in _as_mapping_sequence(pitfall_spec.get("evidence") or pitfall_spec.get("pitfall_evidence")))
    evidence_by_pitfall = {
        normalize_field_name(row.get("pitfall_id") or row.get("id") or ""): row
        for row in evidence_rows
        if not _blank(row.get("pitfall_id") or row.get("id"))
    }
    blockers: list[str] = []
    avoided_pitfalls: list[str] = []
    unresolved_pitfalls: list[str] = []
    if not pitfall_ids:
        blockers.append("missing_pitfalls")
    for required in _as_sequence(pitfall_policy.get("required_pitfalls")):
        required_id = normalize_field_name(required)
        if required_id and required_id not in pitfall_ids:
            blockers.append(f"missing_required_pitfall:{required_id}")
    for pitfall_id in pitfall_ids:
        evidence = evidence_by_pitfall.get(pitfall_id)
        if not evidence:
            blockers.append(f"missing_evidence:{pitfall_id}")
            unresolved_pitfalls.append(pitfall_id)
            continue
        if evidence.get("avoided") is True:
            avoided_pitfalls.append(pitfall_id)
        else:
            unresolved_pitfalls.append(pitfall_id)
            if pitfall_policy.get("require_all_avoided"):
                blockers.append(f"pitfall_not_avoided:{pitfall_id}")
        if pitfall_policy.get("require_evidence_ref") and _blank(evidence.get("evidence_ref")):
            blockers.append(f"missing_evidence_ref:{pitfall_id}")
    min_avoided = int(pitfall_policy.get("min_avoided") or 0)
    if min_avoided and len(avoided_pitfalls) < min_avoided:
        blockers.append("avoided_pitfall_count_below_policy")
    if pitfall_policy.get("require_candidate_boundary"):
        if pitfall_spec.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if pitfall_spec.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")
    matrix_hash = "pitfall-avoidance-matrix:" + _digest(
        {
            "avoided": avoided_pitfalls,
            "blockers": blockers,
            "pitfalls": pitfall_ids,
            "unresolved": unresolved_pitfalls,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return PitfallAvoidanceMatrixReceipt(
        ready=not blockers,
        pitfall_ids=pitfall_ids,
        avoided_pitfalls=tuple(avoided_pitfalls),
        unresolved_pitfalls=tuple(unresolved_pitfalls),
        blockers=tuple(blockers),
        matrix_hash=matrix_hash,
    )


def plan_route_promotion_evidence_pack(
    evidence_spec: Mapping[str, Any],
    evidence_policy: Mapping[str, Any],
) -> RoutePromotionEvidencePackReceipt:
    """Plan a route promotion evidence pack from reuse, proof, lift, and owner artifacts."""

    raw_route_id = str(evidence_spec.get("route_id") or evidence_spec.get("id") or "").strip()
    route_id = normalize_field_name(raw_route_id) if raw_route_id else ""
    primitive_ids = tuple(str(value) for value in _as_sequence(evidence_spec.get("primitive_ids") or evidence_spec.get("primitive_groups_used")) if str(value).strip())
    evidence_refs = tuple(str(value) for value in _as_sequence(evidence_spec.get("evidence_refs")) if str(value).strip())
    blockers: list[str] = []
    if not route_id:
        blockers.append("missing_route_id")
    if not primitive_ids:
        blockers.append("missing_primitive_ids")
    for required_ref in _as_sequence(evidence_policy.get("required_evidence_refs")):
        required = str(required_ref)
        if required and required not in evidence_refs:
            blockers.append(f"missing_evidence_ref:{required}")
    if evidence_policy.get("require_reuse_observation") and _blank(evidence_spec.get("reuse_observation_ref")):
        blockers.append("missing_reuse_observation_ref")
    if evidence_policy.get("require_lift_comparison") and _blank(evidence_spec.get("lift_comparison_ref")):
        blockers.append("missing_lift_comparison_ref")
    if evidence_policy.get("require_token_savings") and _blank(evidence_spec.get("token_savings_ref")):
        blockers.append("missing_token_savings_ref")
    if evidence_policy.get("require_pitfall_matrix") and _blank(evidence_spec.get("pitfall_matrix_ref")):
        blockers.append("missing_pitfall_matrix_ref")
    if evidence_policy.get("require_proof_bundle") and _blank(evidence_spec.get("proof_bundle_ref")):
        blockers.append("missing_proof_bundle_ref")
    if evidence_policy.get("require_owner_review") and _blank(evidence_spec.get("owner_review_ref")):
        blockers.append("missing_owner_review_ref")
    if evidence_policy.get("require_candidate_boundary"):
        if evidence_spec.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if evidence_spec.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")
    evidence_hash = "route-promotion-evidence-pack:" + _digest(
        {
            "blockers": blockers,
            "evidence_refs": evidence_refs,
            "primitive_ids": primitive_ids,
            "route_id": route_id,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return RoutePromotionEvidencePackReceipt(
        ready=not blockers,
        route_id=route_id,
        primitive_ids=primitive_ids,
        evidence_refs=evidence_refs,
        blockers=tuple(blockers),
        evidence_hash=evidence_hash,
    )


def decompose_benchmark_task_to_primitive_components(
    task_spec: Mapping[str, Any],
    decomposition_policy: Mapping[str, Any],
) -> BenchmarkPrimitiveDecompositionReceipt:
    """Decompose one benchmark task into reusable primitive component edges."""

    raw_task_id = str(task_spec.get("task_id") or task_spec.get("id") or "").strip()
    task_id = normalize_field_name(raw_task_id) if raw_task_id else ""
    components = tuple(dict(item) for item in _as_mapping_sequence(task_spec.get("components") or task_spec.get("primitive_components")))
    required_kinds = {normalize_field_name(value) for value in _as_sequence(decomposition_policy.get("required_component_kinds")) if not _blank(value)}
    blockers: list[str] = []
    component_ids: list[str] = []
    core_group_edges: list[str] = []
    seen_kinds: set[str] = set()
    if not task_id:
        blockers.append("missing_task_id")
    if not components:
        blockers.append("missing_components")
    min_components = int(decomposition_policy.get("min_components") or 0)
    if min_components and len(components) < min_components:
        blockers.append("component_count_below_policy")
    max_component_token_estimate = int(decomposition_policy.get("max_component_token_estimate") or 0)
    for index, component in enumerate(components):
        component_id = str(component.get("component_id") or component.get("primitive_id") or component.get("id") or "").strip()
        if not component_id:
            component_id = f"component_{index + 1}"
            blockers.append(f"component_{index + 1}_missing_id")
        component_ids.append(component_id)
        component_kind = normalize_field_name(component.get("kind") or component.get("primitive_kind") or "")
        if component_kind:
            seen_kinds.add(component_kind)
        elif decomposition_policy.get("require_component_kind"):
            blockers.append(f"{component_id}:missing_component_kind")
        input_edge = str(component.get("input_edge") or "").strip()
        output_edge = str(component.get("output_edge") or "").strip()
        core_group_edge = str(component.get("core_group_edge") or "").strip()
        if not core_group_edge and input_edge and output_edge:
            core_group_edge = f"{input_edge} -> {output_edge}"
        if core_group_edge:
            core_group_edges.append(core_group_edge)
        elif decomposition_policy.get("require_visible_edges"):
            blockers.append(f"{component_id}:missing_visible_edge")
        if decomposition_policy.get("require_proof_requirements") and not _as_sequence(component.get("proof_requirements")):
            blockers.append(f"{component_id}:missing_proof_requirements")
        estimated_tokens = int(component.get("estimated_tokens") or component.get("token_estimate") or 0)
        if max_component_token_estimate and estimated_tokens > max_component_token_estimate:
            blockers.append(f"{component_id}:component_token_estimate_exceeds_policy")
        if decomposition_policy.get("require_candidate_boundary"):
            if component.get("candidate") is not True:
                blockers.append(f"{component_id}:candidate_boundary_not_declared")
            if component.get("serves_truth") is not False:
                blockers.append(f"{component_id}:serves_truth_must_be_false")
    for required_kind in sorted(required_kinds):
        if required_kind not in seen_kinds:
            blockers.append(f"missing_required_component_kind:{required_kind}")
    decomposition_hash = "benchmark-primitive-decomposition:" + _digest(
        {
            "blockers": blockers,
            "component_ids": component_ids,
            "core_group_edges": core_group_edges,
            "task_id": task_id,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return BenchmarkPrimitiveDecompositionReceipt(
        ready=not blockers,
        task_id=task_id,
        component_ids=tuple(component_ids),
        core_group_edges=tuple(core_group_edges),
        blockers=tuple(blockers),
        decomposition_hash=decomposition_hash,
    )


def compare_benchmark_route_token_usage(
    comparison_spec: Mapping[str, Any],
    token_policy: Mapping[str, Any],
) -> BenchmarkRouteTokenComparisonReceipt:
    """Compare baseline route tokens against primitive-component route tokens."""

    baseline_tokens = int(comparison_spec.get("baseline_tokens") or 0)
    if baseline_tokens <= 0:
        baseline_tokens = int(comparison_spec.get("baseline_prompt_tokens") or 0) + int(comparison_spec.get("baseline_completion_tokens") or 0)
    primitive_route_tokens = int(comparison_spec.get("primitive_route_tokens") or comparison_spec.get("candidate_tokens") or 0)
    components = tuple(dict(item) for item in _as_mapping_sequence(comparison_spec.get("components") or comparison_spec.get("primitive_components")))
    component_ids = tuple(str(item.get("component_id") or item.get("primitive_id") or item.get("id") or "").strip() for item in components if str(item.get("component_id") or item.get("primitive_id") or item.get("id") or "").strip())
    if primitive_route_tokens <= 0:
        primitive_route_tokens = sum(int(item.get("tokens") or item.get("token_usage") or item.get("estimated_tokens") or 0) for item in components)
    blockers: list[str] = []
    if baseline_tokens <= 0:
        blockers.append("missing_baseline_tokens")
    if primitive_route_tokens <= 0:
        blockers.append("missing_primitive_route_tokens")
    if token_policy.get("require_component_attribution") and not component_ids:
        blockers.append("missing_component_attribution")
    for required_component in _as_sequence(token_policy.get("required_component_ids")):
        required_id = str(required_component)
        if required_id and required_id not in component_ids:
            blockers.append(f"missing_component_id:{required_id}")
    savings_percent = 0.0
    if baseline_tokens > 0:
        savings_percent = round(((baseline_tokens - primitive_route_tokens) / baseline_tokens) * 100, 2)
    min_savings_percent = float(token_policy.get("min_savings_percent") or 0)
    if min_savings_percent and savings_percent < min_savings_percent:
        blockers.append("token_savings_below_policy")
    if token_policy.get("require_baseline_trace_ref") and _blank(comparison_spec.get("baseline_trace_ref")):
        blockers.append("missing_baseline_trace_ref")
    if token_policy.get("require_primitive_trace_ref") and _blank(comparison_spec.get("primitive_trace_ref") or comparison_spec.get("candidate_trace_ref")):
        blockers.append("missing_primitive_trace_ref")
    if token_policy.get("require_same_task_id") and comparison_spec.get("baseline_task_id") != comparison_spec.get("primitive_task_id"):
        blockers.append("task_id_mismatch")
    if token_policy.get("require_candidate_boundary"):
        if comparison_spec.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if comparison_spec.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")
    comparison_hash = "benchmark-route-token-comparison:" + _digest(
        {
            "baseline_tokens": baseline_tokens,
            "blockers": blockers,
            "component_ids": component_ids,
            "primitive_route_tokens": primitive_route_tokens,
            "savings_percent": savings_percent,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return BenchmarkRouteTokenComparisonReceipt(
        ready=not blockers,
        baseline_tokens=baseline_tokens,
        primitive_route_tokens=primitive_route_tokens,
        savings_percent=savings_percent,
        component_ids=component_ids,
        blockers=tuple(blockers),
        comparison_hash=comparison_hash,
    )


def _trace_token_total(trace: Mapping[str, Any]) -> int:
    total = int(trace.get("total_tokens") or trace.get("tokens") or 0)
    if total > 0:
        return total
    return int(trace.get("prompt_tokens") or trace.get("input_tokens") or 0) + int(
        trace.get("completion_tokens") or trace.get("output_tokens") or 0
    )


def ingest_benchmark_trace_pairs(
    artifact_spec: Mapping[str, Any],
    ingestion_policy: Mapping[str, Any],
) -> BenchmarkTraceIngestionReceipt:
    """Normalize benchmark run artifacts into paired baseline and primitive traces."""

    artifacts = tuple(
        dict(item)
        for item in _as_mapping_sequence(
            artifact_spec.get("run_artifacts")
            or artifact_spec.get("artifacts")
            or artifact_spec.get("traces")
        )
    )
    baseline_arm_names = {
        normalize_field_name(value)
        for value in _as_sequence(ingestion_policy.get("baseline_arm_names") or ("baseline",))
        if not _blank(value)
    }
    primitive_arm_names = {
        normalize_field_name(value)
        for value in _as_sequence(ingestion_policy.get("primitive_arm_names") or ("primitive", "candidate", "aidevexplorer_candidate"))
        if not _blank(value)
    }
    required_task_ids = tuple(str(value).strip() for value in _as_sequence(ingestion_policy.get("required_task_ids")) if str(value).strip())
    blockers: list[str] = []
    indexed: dict[str, dict[str, JsonRecord]] = {}

    def normalized_trace(row: Mapping[str, Any], task_id: str) -> JsonRecord:
        prompt_tokens = int(row.get("prompt_tokens") or row.get("input_tokens") or 0)
        completion_tokens = int(row.get("completion_tokens") or row.get("output_tokens") or 0)
        total_tokens = int(row.get("total_tokens") or row.get("tokens") or 0)
        if total_tokens <= 0 and (prompt_tokens or completion_tokens):
            total_tokens = prompt_tokens + completion_tokens
        trace_ref = str(row.get("trace_ref") or row.get("artifact_ref") or row.get("path") or "").strip()
        trace: JsonRecord = {
            "task_id": task_id,
            "trace_ref": trace_ref,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "token_source": str(row.get("token_source") or "").strip(),
            "success": row.get("success"),
        }
        if row.get("estimate_only") is not None:
            trace["estimate_only"] = row.get("estimate_only")
        runtime_shape = str(row.get("runtime_shape") or row.get("primitive_kind") or "").strip()
        if runtime_shape:
            trace["runtime_shape"] = normalize_field_name(runtime_shape)
        tool_consumer = str(row.get("tool_consumer") or row.get("development_tool") or row.get("runner") or row.get("agent") or "").strip()
        if tool_consumer:
            trace["tool_consumer"] = normalize_field_name(tool_consumer)
        primitive_ids = tuple(str(value).strip() for value in _as_sequence(row.get("primitive_ids") or row.get("primitive_groups_used")) if str(value).strip())
        if primitive_ids:
            trace["primitive_ids"] = primitive_ids
        components = tuple(dict(item) for item in _as_mapping_sequence(row.get("component_attribution") or row.get("components")))
        if components:
            trace["component_attribution"] = components
        proof_refs = tuple(str(value).strip() for value in _as_sequence(row.get("proof_refs") or row.get("proof_artifacts")) if str(value).strip())
        if proof_refs:
            trace["proof_refs"] = proof_refs
        if row.get("route_reused") is not None:
            trace["route_reused"] = row.get("route_reused")
        return trace

    if not artifacts:
        blockers.append("missing_run_artifacts")

    for index, artifact in enumerate(artifacts, start=1):
        task_id = str(artifact.get("task_id") or artifact.get("benchmark_task_id") or "").strip()
        raw_arm = str(artifact.get("arm") or artifact.get("arm_name") or artifact.get("run_arm") or artifact.get("variant") or "").strip()
        arm_name = normalize_field_name(raw_arm) if raw_arm else ""
        if not task_id:
            blockers.append(f"artifact_{index}_missing_task_id")
            continue
        if not arm_name:
            blockers.append(f"{task_id}:missing_arm")
            continue
        if arm_name in baseline_arm_names:
            arm_kind = "baseline"
        elif arm_name in primitive_arm_names:
            arm_kind = "primitive"
        else:
            blockers.append(f"{task_id}:unknown_arm:{arm_name}")
            continue

        if ingestion_policy.get("require_trace_refs") and _blank(artifact.get("trace_ref") or artifact.get("artifact_ref") or artifact.get("path")):
            blockers.append(f"{task_id}:{arm_kind}_missing_trace_ref")
        if ingestion_policy.get("require_actual_tokens"):
            if artifact.get("estimate_only") is True or str(artifact.get("token_source") or "").lower() == "estimate":
                blockers.append(f"{task_id}:{arm_kind}_tokens_are_estimated")
            if _trace_token_total(artifact) <= 0:
                blockers.append(f"{task_id}:{arm_kind}_missing_tokens")
        if ingestion_policy.get("require_successful_runs") and artifact.get("success") is not True:
            blockers.append(f"{task_id}:{arm_kind}_not_successful")
        if arm_kind == "primitive":
            if ingestion_policy.get("require_route_reused") and artifact.get("route_reused") is not True:
                blockers.append(f"{task_id}:primitive_route_not_reused")
            if ingestion_policy.get("require_primitive_ids") and not _as_sequence(artifact.get("primitive_ids") or artifact.get("primitive_groups_used")):
                blockers.append(f"{task_id}:primitive_missing_primitive_ids")
            components = tuple(_as_mapping_sequence(artifact.get("component_attribution") or artifact.get("components")))
            if ingestion_policy.get("require_component_attribution") and not components:
                blockers.append(f"{task_id}:primitive_missing_component_attribution")
            min_component_count = int(ingestion_policy.get("min_component_count") or 0)
            if min_component_count and len(components) < min_component_count:
                blockers.append(f"{task_id}:primitive_component_count_below_policy")
            if ingestion_policy.get("require_proof_refs") and not _as_sequence(artifact.get("proof_refs") or artifact.get("proof_artifacts")):
                blockers.append(f"{task_id}:primitive_missing_proof_refs")
        if ingestion_policy.get("require_candidate_boundary"):
            if artifact.get("candidate") is not True:
                blockers.append(f"{task_id}:{arm_kind}_candidate_boundary_not_declared")
            if artifact.get("serves_truth") is not False:
                blockers.append(f"{task_id}:{arm_kind}_serves_truth_must_be_false")

        by_task = indexed.setdefault(task_id, {})
        if arm_kind in by_task:
            blockers.append(f"{task_id}:duplicate_{arm_kind}_trace")
        else:
            by_task[arm_kind] = normalized_trace(artifact, task_id)

    trace_pairs: list[JsonRecord] = []
    paired_task_ids: list[str] = []
    for task_id in sorted(indexed):
        arms = indexed[task_id]
        if "baseline" not in arms:
            blockers.append(f"{task_id}:missing_baseline_trace")
            continue
        if "primitive" not in arms:
            blockers.append(f"{task_id}:missing_primitive_trace")
            continue
        paired_task_ids.append(task_id)
        trace_pairs.append(
            {
                "task_id": task_id,
                "baseline_trace": arms["baseline"],
                "primitive_trace": arms["primitive"],
                "candidate": True,
                "serves_truth": False,
            }
        )

    for required_task_id in required_task_ids:
        if required_task_id not in paired_task_ids:
            blockers.append(f"missing_required_trace_pair:{required_task_id}")

    min_pairs = int(ingestion_policy.get("min_pairs") or 0)
    if min_pairs and len(trace_pairs) < min_pairs:
        blockers.append("trace_pair_count_below_policy")

    ingestion_hash = "benchmark-trace-ingestion:" + _digest(
        {
            "blockers": blockers,
            "pair_count": len(trace_pairs),
            "required_task_ids": required_task_ids,
            "task_ids": paired_task_ids,
            "trace_pairs": trace_pairs,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return BenchmarkTraceIngestionReceipt(
        ready=not blockers,
        pair_count=len(trace_pairs),
        task_ids=tuple(paired_task_ids),
        trace_pairs=tuple(trace_pairs),
        blockers=tuple(blockers),
        ingestion_hash=ingestion_hash,
    )


def evaluate_benchmark_trace_pair(
    trace_pair_spec: Mapping[str, Any],
    trace_policy: Mapping[str, Any],
) -> BenchmarkTracePairEvaluationReceipt:
    """Evaluate actual baseline and primitive-route benchmark traces."""

    baseline_trace = trace_pair_spec.get("baseline_trace") if isinstance(trace_pair_spec.get("baseline_trace"), Mapping) else {}
    primitive_trace = trace_pair_spec.get("primitive_trace") if isinstance(trace_pair_spec.get("primitive_trace"), Mapping) else {}
    if not primitive_trace:
        primitive_trace = trace_pair_spec.get("candidate_trace") if isinstance(trace_pair_spec.get("candidate_trace"), Mapping) else {}
    task_id = str(
        trace_pair_spec.get("task_id")
        or baseline_trace.get("task_id")
        or primitive_trace.get("task_id")
        or ""
    ).strip()
    baseline_task_id = str(baseline_trace.get("task_id") or trace_pair_spec.get("baseline_task_id") or "").strip()
    primitive_task_id = str(primitive_trace.get("task_id") or trace_pair_spec.get("primitive_task_id") or "").strip()
    baseline_trace_ref = str(
        baseline_trace.get("trace_ref")
        or trace_pair_spec.get("baseline_trace_ref")
        or ""
    ).strip()
    primitive_trace_ref = str(
        primitive_trace.get("trace_ref")
        or primitive_trace.get("candidate_trace_ref")
        or trace_pair_spec.get("primitive_trace_ref")
        or trace_pair_spec.get("candidate_trace_ref")
        or ""
    ).strip()
    baseline_tokens = _trace_token_total(baseline_trace)
    primitive_tokens = _trace_token_total(primitive_trace)
    component_rows = tuple(
        dict(item)
        for item in _as_mapping_sequence(
            primitive_trace.get("component_attribution")
            or primitive_trace.get("components")
            or trace_pair_spec.get("component_attribution")
            or trace_pair_spec.get("components")
        )
    )
    component_ids = tuple(
        str(item.get("component_id") or item.get("id") or item.get("primitive_id") or "").strip()
        for item in component_rows
        if str(item.get("component_id") or item.get("id") or item.get("primitive_id") or "").strip()
    )
    primitive_ids = tuple(
        str(value)
        for value in _as_sequence(
            primitive_trace.get("primitive_ids")
            or primitive_trace.get("primitive_groups_used")
            or trace_pair_spec.get("primitive_ids")
            or trace_pair_spec.get("primitive_groups_used")
        )
        if str(value).strip()
    )
    proof_refs = tuple(
        str(value)
        for value in _as_sequence(
            primitive_trace.get("proof_refs")
            or primitive_trace.get("proof_artifacts")
            or trace_pair_spec.get("proof_refs")
            or trace_pair_spec.get("proof_artifacts")
        )
        if str(value).strip()
    )
    blockers: list[str] = []
    if not task_id:
        blockers.append("missing_task_id")
    if not baseline_trace:
        blockers.append("missing_baseline_trace")
    if not primitive_trace:
        blockers.append("missing_primitive_trace")
    if trace_policy.get("require_same_task_id"):
        if not baseline_task_id:
            blockers.append("missing_baseline_task_id")
        if not primitive_task_id:
            blockers.append("missing_primitive_task_id")
        if baseline_task_id and primitive_task_id and baseline_task_id != primitive_task_id:
            blockers.append("task_id_mismatch")
        if task_id and baseline_task_id and task_id != baseline_task_id:
            blockers.append("baseline_task_id_mismatch")
        if task_id and primitive_task_id and task_id != primitive_task_id:
            blockers.append("primitive_task_id_mismatch")
    if baseline_tokens <= 0:
        blockers.append("missing_baseline_tokens")
    if primitive_tokens <= 0:
        blockers.append("missing_primitive_tokens")
    if trace_policy.get("require_trace_refs"):
        if not baseline_trace_ref:
            blockers.append("missing_baseline_trace_ref")
        if not primitive_trace_ref:
            blockers.append("missing_primitive_trace_ref")
    if trace_policy.get("require_actual_tokens"):
        for label, trace in (("baseline", baseline_trace), ("primitive", primitive_trace)):
            if trace.get("estimate_only") is True or str(trace.get("token_source") or "").lower() == "estimate":
                blockers.append(f"{label}_tokens_are_estimated")
    if trace_policy.get("require_success"):
        if baseline_trace.get("success") is not True:
            blockers.append("baseline_trace_not_successful")
        if primitive_trace.get("success") is not True:
            blockers.append("primitive_trace_not_successful")
    min_component_count = int(trace_policy.get("min_component_count") or 0)
    if trace_policy.get("require_component_attribution") and not component_ids:
        blockers.append("missing_component_attribution")
    if min_component_count and len(component_ids) < min_component_count:
        blockers.append("component_count_below_policy")
    for required_component in _as_sequence(trace_policy.get("required_component_ids")):
        required_id = str(required_component)
        if required_id and required_id not in component_ids:
            blockers.append(f"missing_component_id:{required_id}")
    if trace_policy.get("require_primitives") and not primitive_ids:
        blockers.append("missing_primitive_ids")
    if trace_policy.get("require_proof_refs") and not proof_refs:
        blockers.append("missing_proof_refs")
    savings_percent = 0.0
    if baseline_tokens > 0:
        savings_percent = round(((baseline_tokens - primitive_tokens) / baseline_tokens) * 100, 2)
    min_savings_percent = float(trace_policy.get("min_savings_percent") or 0)
    if min_savings_percent and savings_percent < min_savings_percent:
        blockers.append("token_savings_below_policy")
    if trace_policy.get("require_candidate_boundary"):
        if trace_pair_spec.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if trace_pair_spec.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")
    evaluation_hash = "benchmark-trace-pair-evaluation:" + _digest(
        {
            "baseline_tokens": baseline_tokens,
            "blockers": blockers,
            "component_ids": component_ids,
            "primitive_ids": primitive_ids,
            "primitive_tokens": primitive_tokens,
            "proof_refs": proof_refs,
            "savings_percent": savings_percent,
            "task_id": task_id,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return BenchmarkTracePairEvaluationReceipt(
        ready=not blockers,
        task_id=task_id,
        baseline_trace_ref=baseline_trace_ref,
        primitive_trace_ref=primitive_trace_ref,
        baseline_tokens=baseline_tokens,
        primitive_tokens=primitive_tokens,
        savings_percent=savings_percent,
        component_ids=component_ids,
        primitive_ids=primitive_ids,
        proof_refs=proof_refs,
        blockers=tuple(blockers),
        evaluation_hash=evaluation_hash,
    )


def evaluate_benchmark_route_promotion_candidate(
    evidence_spec: Mapping[str, Any],
    promotion_policy: Mapping[str, Any],
) -> BenchmarkRoutePromotionCandidateReceipt:
    """Aggregate benchmark runs into a candidate-only route promotion signal."""

    raw_route_id = str(evidence_spec.get("route_id") or evidence_spec.get("id") or "").strip()
    route_id = normalize_field_name(raw_route_id) if raw_route_id else ""
    runs = tuple(
        dict(item)
        for item in _as_mapping_sequence(
            evidence_spec.get("benchmark_runs")
            or evidence_spec.get("trace_evaluations")
            or evidence_spec.get("evaluations")
            or evidence_spec.get("runs")
        )
    )

    def token_int(value: Any) -> int:
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0

    def total_tokens(row: Mapping[str, Any], *names: str) -> int:
        for name in names:
            direct = token_int(row.get(name))
            if direct > 0:
                return direct
        return 0

    primitive_ids = {
        str(value).strip()
        for value in _as_sequence(evidence_spec.get("primitive_ids") or evidence_spec.get("primitive_groups_used"))
        if str(value).strip()
    }
    task_ids: set[str] = set()
    runtime_shapes: set[str] = set()
    tool_consumers: set[str] = set()
    proof_ref_counts: dict[int, int] = {}
    savings_values: list[float] = []
    winning_runs = 0
    unresolved_pitfalls: set[str] = set()
    blockers: list[str] = []

    if not route_id:
        blockers.append("missing_route_id")
    if not runs:
        blockers.append("missing_benchmark_runs")

    min_run_savings_percent = float(
        promotion_policy.get("min_run_savings_percent")
        or promotion_policy.get("min_savings_percent")
        or 0
    )

    for index, run in enumerate(runs, start=1):
        task_id = str(run.get("task_id") or "").strip()
        if task_id:
            task_ids.add(task_id)
        elif promotion_policy.get("require_task_id"):
            blockers.append(f"run_{index}_missing_task_id")

        runtime_shape = normalize_field_name(run.get("runtime_shape") or run.get("primitive_kind") or "") if not _blank(run.get("runtime_shape") or run.get("primitive_kind")) else ""
        if runtime_shape:
            runtime_shapes.add(runtime_shape)

        tool_consumer = normalize_field_name(run.get("tool_consumer") or run.get("development_tool") or run.get("runner") or run.get("agent") or "") if not _blank(run.get("tool_consumer") or run.get("development_tool") or run.get("runner") or run.get("agent")) else ""
        if tool_consumer:
            tool_consumers.add(tool_consumer)

        for primitive_id in _as_sequence(run.get("primitive_ids") or run.get("primitive_groups_used")):
            primitive_text = str(primitive_id).strip()
            if primitive_text:
                primitive_ids.add(primitive_text)

        proof_refs = tuple(str(value) for value in _as_sequence(run.get("proof_refs") or run.get("proof_artifacts")) if str(value).strip())
        proof_ref_counts[index] = len(proof_refs)

        if promotion_policy.get("require_successful_runs") and run.get("success", run.get("ready")) is not True:
            blockers.append(f"run_{index}_not_successful")
        if promotion_policy.get("require_route_reused") and run.get("route_reused") is not True:
            blockers.append(f"run_{index}_route_not_reused")
        if promotion_policy.get("require_proof_refs") and not proof_refs:
            blockers.append(f"run_{index}_missing_proof_refs")
        if promotion_policy.get("require_actual_tokens"):
            if run.get("estimate_only") is True or str(run.get("token_source") or "").lower() == "estimate":
                blockers.append(f"run_{index}_tokens_are_estimated")

        baseline_tokens = total_tokens(run, "baseline_tokens", "baseline_total_tokens")
        if baseline_tokens <= 0:
            baseline_tokens = token_int(run.get("baseline_prompt_tokens")) + token_int(run.get("baseline_completion_tokens"))
        primitive_tokens = total_tokens(run, "primitive_tokens", "candidate_tokens", "primitive_route_tokens")
        if primitive_tokens <= 0:
            primitive_tokens = token_int(run.get("primitive_prompt_tokens") or run.get("candidate_prompt_tokens")) + token_int(run.get("primitive_completion_tokens") or run.get("candidate_completion_tokens"))

        savings_value: float | None
        if not _blank(run.get("savings_percent")):
            savings_value = float(run.get("savings_percent") or 0)
        elif baseline_tokens > 0 and primitive_tokens > 0:
            savings_value = round(((baseline_tokens - primitive_tokens) / baseline_tokens) * 100, 2)
        else:
            savings_value = None
        if savings_value is None:
            if promotion_policy.get("require_actual_tokens") or promotion_policy.get("require_savings_measurement"):
                blockers.append(f"run_{index}_missing_token_savings")
        else:
            savings_values.append(savings_value)
            if savings_value >= min_run_savings_percent:
                winning_runs += 1

        for pitfall in _as_sequence(run.get("unresolved_pitfalls") or run.get("pitfalls_unresolved")):
            pitfall_text = normalize_field_name(pitfall)
            if pitfall_text:
                unresolved_pitfalls.add(pitfall_text)

        if promotion_policy.get("require_candidate_boundary"):
            if run.get("candidate") is not True:
                blockers.append(f"run_{index}_candidate_boundary_not_declared")
            if run.get("serves_truth") is not False:
                blockers.append(f"run_{index}_serves_truth_must_be_false")

    primitive_id_tuple = tuple(sorted(primitive_ids))
    task_id_tuple = tuple(sorted(task_ids))
    runtime_shape_tuple = tuple(sorted(runtime_shapes))
    tool_consumer_tuple = tuple(sorted(tool_consumers))

    min_runs = int(promotion_policy.get("min_runs") or 0)
    if min_runs and len(runs) < min_runs:
        blockers.append("run_count_below_policy")
    min_tasks = int(promotion_policy.get("min_tasks") or 0)
    if min_tasks and len(task_id_tuple) < min_tasks:
        blockers.append("task_count_below_policy")
    min_runtime_shapes = int(promotion_policy.get("min_runtime_shapes") or 0)
    if min_runtime_shapes and len(runtime_shape_tuple) < min_runtime_shapes:
        blockers.append("runtime_shape_count_below_policy")
    min_tool_consumers = int(promotion_policy.get("min_tool_consumers") or 0)
    if min_tool_consumers and len(tool_consumer_tuple) < min_tool_consumers:
        blockers.append("tool_consumer_count_below_policy")
    if promotion_policy.get("require_primitives") and not primitive_id_tuple:
        blockers.append("missing_primitive_ids")

    for required_primitive in _as_sequence(promotion_policy.get("required_primitive_ids")):
        primitive_text = str(required_primitive).strip()
        if primitive_text and primitive_text not in primitive_ids:
            blockers.append(f"missing_primitive_id:{primitive_text}")
    for required_shape in _as_sequence(promotion_policy.get("required_runtime_shapes")):
        shape_name = normalize_field_name(required_shape)
        if shape_name and shape_name not in runtime_shapes:
            blockers.append(f"missing_runtime_shape:{shape_name}")
    for required_tool in _as_sequence(promotion_policy.get("required_tool_consumers")):
        tool_name = normalize_field_name(required_tool)
        if tool_name and tool_name not in tool_consumers:
            blockers.append(f"missing_tool_consumer:{tool_name}")

    average_savings_percent = round(sum(savings_values) / len(savings_values), 2) if savings_values else 0.0
    min_average_savings_percent = float(promotion_policy.get("min_average_savings_percent") or 0)
    if min_average_savings_percent and average_savings_percent < min_average_savings_percent:
        blockers.append("average_token_savings_below_policy")
    winning_run_percent = round((winning_runs / len(runs)) * 100, 2) if runs else 0.0
    min_winning_run_percent = float(promotion_policy.get("min_winning_run_percent") or 0)
    if min_winning_run_percent and winning_run_percent < min_winning_run_percent:
        blockers.append("winning_run_percent_below_policy")

    max_unresolved_pitfalls = promotion_policy.get("max_unresolved_pitfalls")
    if max_unresolved_pitfalls is not None and len(unresolved_pitfalls) > int(max_unresolved_pitfalls):
        blockers.append("unresolved_pitfall_count_above_policy")
    if promotion_policy.get("require_no_unresolved_pitfalls") and unresolved_pitfalls:
        blockers.append("unresolved_pitfalls_present")
    if promotion_policy.get("require_candidate_boundary"):
        if evidence_spec.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if evidence_spec.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")

    candidate_hash = "benchmark-route-promotion-candidate:" + _digest(
        {
            "average_savings_percent": average_savings_percent,
            "blockers": blockers,
            "primitive_ids": primitive_id_tuple,
            "proof_ref_counts": proof_ref_counts,
            "route_id": route_id,
            "run_count": len(runs),
            "runtime_shapes": runtime_shape_tuple,
            "task_ids": task_id_tuple,
            "tool_consumers": tool_consumer_tuple,
            "winning_run_percent": winning_run_percent,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return BenchmarkRoutePromotionCandidateReceipt(
        ready=not blockers,
        route_id=route_id,
        primitive_ids=primitive_id_tuple,
        task_ids=task_id_tuple,
        runtime_shapes=runtime_shape_tuple,
        tool_consumers=tool_consumer_tuple,
        run_count=len(runs),
        average_savings_percent=average_savings_percent,
        winning_run_percent=winning_run_percent,
        blockers=tuple(blockers),
        candidate_hash=candidate_hash,
    )


def _visible_edge_parts(visible_edge: str, fallback_input: str, fallback_output: str) -> tuple[str, str]:
    if "->" not in visible_edge:
        return fallback_input, fallback_output
    left, right = visible_edge.split("->", 1)
    return left.strip() or fallback_input, right.strip() or fallback_output


def _surface_card_primitive_id(prefix: str, *parts: object, version: str = "1") -> str:
    clean_prefix = str(prefix or "surface").strip()
    slug = ".".join(normalize_field_name(part) for part in parts if not _blank(part))
    slug = slug or "unnamed_surface"
    return f"{clean_prefix}{slug}@{version}"


def plan_runtime_shape_adapter(
    route_spec: Mapping[str, Any],
    adapter_policy: Mapping[str, Any],
) -> RuntimeShapeAdapterPlanReceipt:
    """Plan one runtime wrapper around a reusable core group edge."""

    core_group_edge = str(route_spec.get("core_group_edge") or route_spec.get("visible_route") or "").strip()
    runtime_shape = normalize_field_name(route_spec.get("runtime_shape") or route_spec.get("primitive_kind") or "") if not _blank(route_spec.get("runtime_shape") or route_spec.get("primitive_kind")) else ""
    wrapper_edges = tuple(str(value).strip() for value in _as_sequence(route_spec.get("wrapper_edges")) if str(value).strip())
    adapter_mutators = tuple(normalize_field_name(value) for value in _as_sequence(route_spec.get("adapter_mutators") or route_spec.get("mutators")) if not _blank(value))
    proof_requirements = tuple(normalize_field_name(value) for value in _as_sequence(route_spec.get("proof_requirements")) if not _blank(value))
    effects = {normalize_field_name(value) for value in _as_sequence(route_spec.get("effects")) if not _blank(value)}
    allowed_runtime_shapes = {normalize_field_name(value) for value in _as_sequence(adapter_policy.get("allowed_runtime_shapes")) if not _blank(value)}
    required_wrapper_tokens_by_shape = adapter_policy.get("required_wrapper_tokens_by_shape") if isinstance(adapter_policy.get("required_wrapper_tokens_by_shape"), Mapping) else {}
    required_mutators_by_shape = adapter_policy.get("required_mutators_by_shape") if isinstance(adapter_policy.get("required_mutators_by_shape"), Mapping) else {}
    required_proof_by_shape = adapter_policy.get("required_proof_by_shape") if isinstance(adapter_policy.get("required_proof_by_shape"), Mapping) else {}
    required_effects_by_shape = adapter_policy.get("required_effects_by_shape") if isinstance(adapter_policy.get("required_effects_by_shape"), Mapping) else {}
    blockers: list[str] = []
    def shape_policy_values(policy_map: Mapping[str, Any]) -> Sequence[Any]:
        for key, value in policy_map.items():
            if normalize_field_name(key) == runtime_shape:
                return _as_sequence(value)
        return ()

    if adapter_policy.get("require_core_group_edge", True) and not core_group_edge:
        blockers.append("missing_core_group_edge")
    if not runtime_shape:
        blockers.append("missing_runtime_shape")
    elif allowed_runtime_shapes and runtime_shape not in allowed_runtime_shapes:
        blockers.append(f"runtime_shape_not_allowed:{runtime_shape}")
    min_wrapper_edges = int(adapter_policy.get("min_wrapper_edges") or 0)
    if min_wrapper_edges and len(wrapper_edges) < min_wrapper_edges:
        blockers.append("wrapper_edges_below_policy")
    for token in shape_policy_values(required_wrapper_tokens_by_shape):
        token_text = str(token).strip()
        if token_text and not any(token_text in edge for edge in wrapper_edges):
            blockers.append(f"missing_wrapper_edge_token:{runtime_shape}:{token_text}")
    for mutator in shape_policy_values(required_mutators_by_shape):
        mutator_name = normalize_field_name(mutator)
        if mutator_name and mutator_name not in adapter_mutators:
            blockers.append(f"missing_adapter_mutator:{runtime_shape}:{mutator_name}")
    for proof in shape_policy_values(required_proof_by_shape):
        proof_name = normalize_field_name(proof)
        if proof_name and proof_name not in proof_requirements:
            blockers.append(f"missing_proof_requirement:{runtime_shape}:{proof_name}")
    for effect in shape_policy_values(required_effects_by_shape):
        effect_name = normalize_field_name(effect)
        if effect_name and effect_name not in effects:
            blockers.append(f"missing_effect:{runtime_shape}:{effect_name}")
    if adapter_policy.get("require_candidate_boundary"):
        if route_spec.get("candidate") is not True:
            blockers.append("candidate_boundary_not_declared")
        if route_spec.get("serves_truth") is not False:
            blockers.append("serves_truth_must_be_false")
    adapter_hash = "runtime-shape-adapter:" + _digest(
        {
            "adapter_mutators": adapter_mutators,
            "blockers": blockers,
            "core_group_edge": core_group_edge,
            "proof_requirements": proof_requirements,
            "runtime_shape": runtime_shape,
            "wrapper_edges": wrapper_edges,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return RuntimeShapeAdapterPlanReceipt(
        ready=not blockers,
        runtime_shape=runtime_shape,
        core_group_edge=core_group_edge,
        wrapper_edges=wrapper_edges,
        adapter_mutators=adapter_mutators,
        proof_requirements=proof_requirements,
        blockers=tuple(blockers),
        adapter_hash=adapter_hash,
    )


def plan_runtime_shape_adapter_matrix(
    matrix_spec: Mapping[str, Any],
    matrix_policy: Mapping[str, Any],
) -> RuntimeShapeAdapterMatrixReceipt:
    """Plan reuse of one core group edge through multiple runtime-shape wrappers."""

    adapters = tuple(dict(item) for item in _as_mapping_sequence(matrix_spec.get("adapters") or matrix_spec.get("runtime_adapters")))
    runtime_shapes = tuple(
        sorted({normalize_field_name(item.get("runtime_shape") or item.get("primitive_kind") or "") for item in adapters if not _blank(item.get("runtime_shape") or item.get("primitive_kind"))})
    )
    core_group_edges = tuple(
        sorted({str(item.get("core_group_edge") or matrix_spec.get("core_group_edge") or "").strip() for item in adapters if str(item.get("core_group_edge") or matrix_spec.get("core_group_edge") or "").strip()})
    )
    blockers: list[str] = []
    if not adapters:
        blockers.append("missing_adapters")
    min_adapters = int(matrix_policy.get("min_adapters") or 0)
    if min_adapters and len(adapters) < min_adapters:
        blockers.append("adapter_count_below_policy")
    min_runtime_shapes = int(matrix_policy.get("min_runtime_shapes") or 0)
    if min_runtime_shapes and len(runtime_shapes) < min_runtime_shapes:
        blockers.append("runtime_shape_count_below_policy")
    for required_shape in _as_sequence(matrix_policy.get("required_runtime_shapes")):
        shape_name = normalize_field_name(required_shape)
        if shape_name and shape_name not in runtime_shapes:
            blockers.append(f"missing_runtime_shape:{shape_name}")
    if not core_group_edges:
        blockers.append("missing_core_group_edge")
    if matrix_policy.get("require_single_core_group_edge") and len(core_group_edges) > 1:
        blockers.append("multiple_core_group_edges")
    for index, adapter in enumerate(adapters):
        if matrix_policy.get("require_route_reused") and adapter.get("route_reused") is not True:
            blockers.append(f"adapter_{index + 1}_route_not_reused")
        if matrix_policy.get("require_proof_status_pass") and str(adapter.get("proof_status") or "") != "pass":
            blockers.append(f"adapter_{index + 1}_proof_not_pass")
        if matrix_policy.get("require_wrapper_edges") and not _as_sequence(adapter.get("wrapper_edges")):
            blockers.append(f"adapter_{index + 1}_missing_wrapper_edges")
        if matrix_policy.get("require_adapter_mutators") and not _as_sequence(adapter.get("adapter_mutators") or adapter.get("mutators")):
            blockers.append(f"adapter_{index + 1}_missing_adapter_mutators")
        if matrix_policy.get("require_candidate_boundary"):
            if adapter.get("candidate") is not True:
                blockers.append(f"adapter_{index + 1}_candidate_boundary_not_declared")
            if adapter.get("serves_truth") is not False:
                blockers.append(f"adapter_{index + 1}_serves_truth_must_be_false")
    core_group_edge = core_group_edges[0] if len(core_group_edges) == 1 else ""
    matrix_hash = "runtime-shape-adapter-matrix:" + _digest(
        {
            "adapter_count": len(adapters),
            "blockers": blockers,
            "core_group_edges": core_group_edges,
            "runtime_shapes": runtime_shapes,
        },
        chars=RECEIPT_DIGEST_CHARS,
    )
    return RuntimeShapeAdapterMatrixReceipt(
        ready=not blockers,
        core_group_edge=core_group_edge,
        runtime_shapes=runtime_shapes,
        adapter_count=len(adapters),
        blockers=tuple(blockers),
        matrix_hash=matrix_hash,
    )


def compile_openapi_endpoint_primitive_cards(
    operation_spec: Mapping[str, Any],
    card_policy: Mapping[str, Any],
) -> SurfacePrimitiveRegistryCardSetReceipt:
    """Compile extracted OpenAPI operations into candidate endpoint primitive cards."""

    operations = tuple(dict(item) for item in _as_mapping_sequence(operation_spec.get("operations")))
    primitive_prefix = str(card_policy.get("primitive_id_prefix") or "api:").strip()
    version = str(card_policy.get("primitive_version") or "1").strip() or "1"
    default_proofs = tuple(normalize_field_name(value) for value in _as_sequence(card_policy.get("proof_requirements") or ("openapi_contract_test", "request_response_schema_test")) if not _blank(value))
    blockers: list[str] = []
    cards: list[JsonRecord] = []
    if not operations:
        blockers.append("missing_operations")
    for index, operation in enumerate(operations):
        operation_id = str(operation.get("operation_id") or operation.get("operationId") or "").strip()
        method = str(operation.get("method") or "").strip().upper()
        path = str(operation.get("path") or "").strip()
        if not operation_id:
            blockers.append(f"operation_{index + 1}_missing_operation_id")
            operation_id = normalize_field_name(f"{method}_{path}") if method or path else f"operation_{index + 1}"
        visible_edge = str(operation.get("visible_edge") or f"HttpRequest[{operation_id}] -> HttpResponse[{operation_id}Receipt]").strip()
        input_edge, output_edge = _visible_edge_parts(visible_edge, f"HttpRequest[{operation_id}]", f"HttpResponse[{operation_id}Receipt]")
        response_codes = tuple(str(code) for code in _as_sequence(operation.get("response_codes")))
        if card_policy.get("require_success_response", True) and response_codes and not any(code.startswith("2") for code in response_codes):
            blockers.append(f"{operation_id}:missing_success_response")
        if card_policy.get("require_auth_declared") and _blank(operation.get("auth") or operation.get("security")):
            blockers.append(f"{operation_id}:missing_auth")
        effects = ("network_read",) if method == "GET" else ("network_read", "network_write_plan")
        primitive_id = _surface_card_primitive_id(primitive_prefix, operation_id, version=version)
        cards.append({
            "primitive_id": primitive_id,
            "kind": "api.endpoint",
            "input_edge": input_edge,
            "output_edge": output_edge,
            "core_group_edge": visible_edge,
            "hidden_member_edges": (
                "HttpRequest->AuthDecision",
                "HttpRequest->RequestSchemaValidation",
                "AuthDecision+RequestSchemaValidation->CoreOperationInput",
                "CoreOperationOutput->HttpResponse",
            ),
            "runtime_targets": ("api.endpoint", "contract.test", "mock.server"),
            "adapter_mutators": ("api_endpoint_wrapper", "schema_validator_inserter", "error_envelope_wrapper"),
            "proof_requirements": default_proofs,
            "effects": effects,
            "source_ref": {"method": method, "path": path, "operation_id": operation_id},
            "candidate": True,
            "serves_truth": False,
        })
    if card_policy.get("require_candidate_boundary"):
        for card in cards:
            if card.get("candidate") is not True:
                blockers.append(f"{card['primitive_id']}:candidate_boundary_not_declared")
            if card.get("serves_truth") is not False:
                blockers.append(f"{card['primitive_id']}:serves_truth_must_be_false")
    primitive_ids = tuple(card["primitive_id"] for card in cards)
    card_set_hash = "openapi-endpoint-primitive-cards:" + _digest(
        {"blockers": blockers, "primitive_ids": primitive_ids},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SurfacePrimitiveRegistryCardSetReceipt(
        ready=not blockers,
        primitive_ids=primitive_ids,
        cards=tuple(cards),
        blockers=tuple(blockers),
        card_set_hash=card_set_hash,
    )


def compile_asyncapi_event_primitive_cards(
    operation_spec: Mapping[str, Any],
    card_policy: Mapping[str, Any],
) -> SurfacePrimitiveRegistryCardSetReceipt:
    """Compile extracted AsyncAPI operations into candidate event primitive cards."""

    operations = tuple(dict(item) for item in _as_mapping_sequence(operation_spec.get("operations")))
    primitive_prefix = str(card_policy.get("primitive_id_prefix") or "evt:").strip()
    version = str(card_policy.get("primitive_version") or "1").strip() or "1"
    default_proofs = tuple(normalize_field_name(value) for value in _as_sequence(card_policy.get("proof_requirements") or ("asyncapi_contract_test", "message_schema_test", "idempotency_test")) if not _blank(value))
    blockers: list[str] = []
    cards: list[JsonRecord] = []
    if not operations:
        blockers.append("missing_operations")
    for index, operation in enumerate(operations):
        operation_id = str(operation.get("operation_id") or operation.get("operationId") or "").strip()
        channel = str(operation.get("channel") or "").strip()
        action = normalize_field_name(operation.get("action") or "")
        message_name = str(operation.get("message_name") or operation.get("message") or "").strip()
        if not operation_id:
            blockers.append(f"operation_{index + 1}_missing_operation_id")
            operation_id = normalize_field_name(f"{action}_{channel}_{message_name}") if action or channel or message_name else f"operation_{index + 1}"
        if card_policy.get("require_channel", True) and not channel:
            blockers.append(f"{operation_id}:missing_channel")
        if card_policy.get("require_message_name", True) and not message_name:
            blockers.append(f"{operation_id}:missing_message_name")
        visible_edge = str(operation.get("visible_edge") or f"AsyncMessage[{message_name or operation_id}] -> {action.title()}Receipt").strip()
        input_edge, output_edge = _visible_edge_parts(visible_edge, f"AsyncMessage[{message_name or operation_id}]", f"{action.title()}Receipt")
        primitive_id = _surface_card_primitive_id(primitive_prefix, operation_id, version=version)
        cards.append({
            "primitive_id": primitive_id,
            "kind": "event.asyncapi.operation",
            "input_edge": input_edge,
            "output_edge": output_edge,
            "core_group_edge": visible_edge,
            "hidden_member_edges": (
                "AsyncMessage->MessageSchemaValidation",
                "AsyncMessage->IdempotencyDecision",
                "MessageSchemaValidation+IdempotencyDecision->DomainEventEnvelope",
                "DomainEventEnvelope->EventOperationReceipt",
            ),
            "runtime_targets": ("event.handler", "queue.consumer", "contract.test"),
            "adapter_mutators": ("asyncapi_operation_wrapper", "message_schema_validator", "idempotency_wrapper"),
            "proof_requirements": default_proofs,
            "effects": ("message_contract_plan", "idempotency_check"),
            "source_ref": {"channel": channel, "action": action, "operation_id": operation_id},
            "candidate": True,
            "serves_truth": False,
        })
    primitive_ids = tuple(card["primitive_id"] for card in cards)
    card_set_hash = "asyncapi-event-primitive-cards:" + _digest(
        {"blockers": blockers, "primitive_ids": primitive_ids},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SurfacePrimitiveRegistryCardSetReceipt(
        ready=not blockers,
        primitive_ids=primitive_ids,
        cards=tuple(cards),
        blockers=tuple(blockers),
        card_set_hash=card_set_hash,
    )


def compile_service_surface_primitive_cards(
    service_spec: Mapping[str, Any],
    card_policy: Mapping[str, Any],
) -> SurfacePrimitiveRegistryCardSetReceipt:
    """Compile microservice surface inventory into candidate primitive cards."""

    raw_service_name = str(service_spec.get("service_name") or service_spec.get("name") or "").strip()
    service_name = normalize_field_name(raw_service_name) if raw_service_name else ""
    surfaces = tuple(dict(item) for item in _as_mapping_sequence(service_spec.get("surfaces")))
    primitive_prefix = str(card_policy.get("primitive_id_prefix") or "svc:").strip()
    version = str(card_policy.get("primitive_version") or "1").strip() or "1"
    required_surface_kinds = {normalize_field_name(value) for value in _as_sequence(card_policy.get("required_surface_kinds")) if not _blank(value)}
    kind_map = {
        "api_endpoint": "api.endpoint",
        "event_producer": "event.handler",
        "event_consumer": "event.handler",
        "queue_consumer": "queue.consumer",
        "cron_job": "cron.job",
        "dashboard": "dashboard",
        "workflow": "workflow.group",
    }
    runtime_map = {
        "api_endpoint": ("api.endpoint", "microservice", "contract.test"),
        "event_producer": ("event.handler", "microservice", "contract.test"),
        "event_consumer": ("event.handler", "queue.consumer", "microservice"),
        "queue_consumer": ("queue.consumer", "microservice", "contract.test"),
        "cron_job": ("cron.job", "microservice", "contract.test"),
        "dashboard": ("dashboard", "ui.route", "api.endpoint"),
        "workflow": ("workflow.group", "microservice", "queue.consumer"),
    }
    blockers: list[str] = []
    cards: list[JsonRecord] = []
    if not service_name:
        blockers.append("missing_service_name")
    if not surfaces:
        blockers.append("missing_surfaces")
    seen_kinds: set[str] = set()
    for index, surface in enumerate(surfaces):
        surface_name = str(surface.get("name") or "").strip()
        surface_kind = normalize_field_name(surface.get("kind") or "")
        visibility = normalize_field_name(surface.get("visibility") or "internal")
        if not surface_name:
            blockers.append(f"surface_{index + 1}_missing_name")
            surface_name = f"surface_{index + 1}"
        if not surface_kind:
            blockers.append(f"surface_{index + 1}_missing_kind")
            surface_kind = "surface"
        seen_kinds.add(surface_kind)
        if visibility == "public" and card_policy.get("require_auth_for_public") and _blank(surface.get("auth")):
            blockers.append(f"public_surface_missing_auth:{surface_name}")
        visible_edge = str(surface.get("visible_edge") or surface.get("core_group_edge") or f"{service_name.title()}SurfaceRequest[{surface_name}] -> {service_name.title()}SurfaceReceipt").strip()
        input_edge, output_edge = _visible_edge_parts(visible_edge, f"{service_name.title()}SurfaceRequest[{surface_name}]", f"{service_name.title()}SurfaceReceipt")
        primitive_kind = kind_map.get(surface_kind, f"service.surface.{surface_kind}")
        primitive_id = _surface_card_primitive_id(primitive_prefix, service_name, surface_kind, surface_name, version=version)
        cards.append({
            "primitive_id": primitive_id,
            "kind": primitive_kind,
            "input_edge": input_edge,
            "output_edge": output_edge,
            "core_group_edge": visible_edge,
            "hidden_member_edges": (
                "ServiceSurfaceRequest->AuthAndVisibilityDecision",
                "ServiceSurfaceRequest->SurfaceContractValidation",
                "AuthAndVisibilityDecision+SurfaceContractValidation->ServiceCapabilityInvocation",
                "ServiceCapabilityInvocation->ServiceSurfaceReceipt",
            ),
            "runtime_targets": runtime_map.get(surface_kind, ("service.group", "microservice")),
            "adapter_mutators": ("service_surface_wrapper", "contract_validator", "telemetry_wrapper"),
            "proof_requirements": tuple(normalize_field_name(value) for value in _as_sequence(card_policy.get("proof_requirements") or ("surface_contract_test", "auth_visibility_test", "telemetry_smoke_test")) if not _blank(value)),
            "effects": tuple(str(value) for value in _as_sequence(surface.get("effects") or ("service_surface_plan",)) if str(value).strip()),
            "source_ref": {"service_name": service_name, "surface_name": surface_name, "surface_kind": surface_kind},
            "candidate": True,
            "serves_truth": False,
        })
    for required_kind in sorted(required_surface_kinds):
        if required_kind not in seen_kinds:
            blockers.append(f"missing_required_surface_kind:{required_kind}")
    min_surfaces = int(card_policy.get("min_surfaces") or 0)
    if min_surfaces and len(surfaces) < min_surfaces:
        blockers.append("surface_count_below_policy")
    primitive_ids = tuple(card["primitive_id"] for card in cards)
    card_set_hash = "service-surface-primitive-cards:" + _digest(
        {"blockers": blockers, "primitive_ids": primitive_ids, "service_name": service_name},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SurfacePrimitiveRegistryCardSetReceipt(
        ready=not blockers,
        primitive_ids=primitive_ids,
        cards=tuple(cards),
        blockers=tuple(blockers),
        card_set_hash=card_set_hash,
    )


def compile_container_runtime_primitive_cards(
    runtime_spec: Mapping[str, Any],
    card_policy: Mapping[str, Any],
) -> SurfacePrimitiveRegistryCardSetReceipt:
    """Compile Docker/Compose runtime surfaces into candidate primitive cards."""

    raw_runtime_name = str(runtime_spec.get("runtime_name") or runtime_spec.get("name") or "container-runtime").strip()
    runtime_name = normalize_field_name(raw_runtime_name)
    raw_services = runtime_spec.get("services")
    if isinstance(raw_services, Mapping):
        services = tuple({"name": str(name), **(dict(spec) if isinstance(spec, Mapping) else {})} for name, spec in raw_services.items())
    else:
        services = tuple(dict(item) for item in _as_mapping_sequence(raw_services))
    primitive_prefix = str(card_policy.get("primitive_id_prefix") or "ctr:").strip()
    version = str(card_policy.get("primitive_version") or "1").strip() or "1"
    blockers: list[str] = []
    cards: list[JsonRecord] = []
    if not services:
        blockers.append("missing_services")
    for index, service in enumerate(services):
        service_name = normalize_field_name(service.get("name") or f"service_{index + 1}")
        image = str(service.get("image") or "").strip()
        build = str(service.get("build") or "").strip()
        if card_policy.get("require_image_or_build", True) and not image and not build:
            blockers.append(f"{service_name}:missing_image_or_build")
        if image.endswith(":latest") and card_policy.get("forbid_latest_image"):
            blockers.append(f"{service_name}:latest_image_forbidden")
        if card_policy.get("require_healthcheck") and not service.get("healthcheck"):
            blockers.append(f"{service_name}:missing_healthcheck")
        env = service.get("environment") if isinstance(service.get("environment"), Mapping) else {}
        if card_policy.get("require_secret_refs"):
            for key, value in env.items():
                if "SECRET" in str(key).upper() or "TOKEN" in str(key).upper() or "PASSWORD" in str(key).upper():
                    if not str(value).startswith(("secret://", "vault://", "${")):
                        blockers.append(f"{service_name}:inline_secret:{key}")
        visible_edge = str(service.get("visible_edge") or f"ContainerServiceSpec[{service_name}] -> ContainerRuntimeReceipt[{service_name}]").strip()
        input_edge, output_edge = _visible_edge_parts(visible_edge, f"ContainerServiceSpec[{service_name}]", f"ContainerRuntimeReceipt[{service_name}]")
        primitive_id = _surface_card_primitive_id(primitive_prefix, runtime_name, service_name, version=version)
        cards.append({
            "primitive_id": primitive_id,
            "kind": "container.runtime_service",
            "input_edge": input_edge,
            "output_edge": output_edge,
            "core_group_edge": visible_edge,
            "hidden_member_edges": (
                "ContainerServiceSpec->ImageOrBuildDecision",
                "ContainerServiceSpec->HealthcheckDecision",
                "ContainerServiceSpec->SecretReferenceDecision",
                "ImageOrBuildDecision+HealthcheckDecision+SecretReferenceDecision->ContainerRuntimeReceipt",
            ),
            "runtime_targets": ("container.compose", "container.dockerfile", "contract.test"),
            "adapter_mutators": ("container_service_card_emitter", "image_pin_gate", "secret_ref_gate"),
            "proof_requirements": tuple(normalize_field_name(value) for value in _as_sequence(card_policy.get("proof_requirements") or ("container_smoke_test", "healthcheck_test", "secret_ref_test")) if not _blank(value)),
            "effects": ("container_runtime_plan", "secret_boundary_check"),
            "source_ref": {"runtime_name": runtime_name, "service_name": service_name, "image": image},
            "candidate": True,
            "serves_truth": False,
        })
    min_services = int(card_policy.get("min_services") or 0)
    if min_services and len(services) < min_services:
        blockers.append("service_count_below_policy")
    primitive_ids = tuple(card["primitive_id"] for card in cards)
    card_set_hash = "container-runtime-primitive-cards:" + _digest(
        {"blockers": blockers, "primitive_ids": primitive_ids, "runtime_name": runtime_name},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SurfacePrimitiveRegistryCardSetReceipt(
        ready=not blockers,
        primitive_ids=primitive_ids,
        cards=tuple(cards),
        blockers=tuple(blockers),
        card_set_hash=card_set_hash,
    )


def compile_kubernetes_workload_primitive_cards(
    workload_spec: Mapping[str, Any],
    card_policy: Mapping[str, Any],
) -> SurfacePrimitiveRegistryCardSetReceipt:
    """Compile Kubernetes workload manifests into candidate primitive cards."""

    workloads = tuple(dict(item) for item in _as_mapping_sequence(workload_spec.get("workloads") or workload_spec.get("manifests")))
    primitive_prefix = str(card_policy.get("primitive_id_prefix") or "k8s:").strip()
    version = str(card_policy.get("primitive_version") or "1").strip() or "1"
    required_kinds = {normalize_field_name(value) for value in _as_sequence(card_policy.get("required_kinds")) if not _blank(value)}
    kind_map = {
        "deployment": "kubernetes.deployment",
        "job": "kubernetes.job",
        "cronjob": "kubernetes.cronjob",
        "service": "kubernetes.service",
        "ingress": "kubernetes.ingress",
        "configmap": "kubernetes.configmap",
    }
    blockers: list[str] = []
    cards: list[JsonRecord] = []
    seen_kinds: set[str] = set()
    if not workloads:
        blockers.append("missing_workloads")
    for index, workload in enumerate(workloads):
        kind = normalize_field_name(workload.get("kind") or "")
        name = normalize_field_name(workload.get("name") or workload.get("metadata_name") or f"workload_{index + 1}")
        if not kind:
            blockers.append(f"workload_{index + 1}_missing_kind")
            kind = "workload"
        seen_kinds.add(kind)
        images = tuple(str(value).strip() for value in _as_sequence(workload.get("images") or workload.get("container_images")) if str(value).strip())
        if card_policy.get("require_images") and kind in {"deployment", "job", "cronjob"} and not images:
            blockers.append(f"{name}:missing_images")
        if card_policy.get("forbid_latest_image"):
            for image in images:
                if image.endswith(":latest"):
                    blockers.append(f"{name}:latest_image_forbidden")
        if card_policy.get("require_resource_limits") and kind in {"deployment", "job", "cronjob"} and not workload.get("resource_limits"):
            blockers.append(f"{name}:missing_resource_limits")
        if card_policy.get("require_probes") and kind == "deployment" and not (workload.get("readiness_probe") and workload.get("liveness_probe")):
            blockers.append(f"{name}:missing_readiness_or_liveness_probe")
        visible_edge = str(workload.get("visible_edge") or f"KubernetesManifest[{kind}:{name}] -> KubernetesApplyReceipt[{name}]").strip()
        input_edge, output_edge = _visible_edge_parts(visible_edge, f"KubernetesManifest[{kind}:{name}]", f"KubernetesApplyReceipt[{name}]")
        primitive_id = _surface_card_primitive_id(primitive_prefix, kind, name, version=version)
        cards.append({
            "primitive_id": primitive_id,
            "kind": kind_map.get(kind, f"kubernetes.{kind}"),
            "input_edge": input_edge,
            "output_edge": output_edge,
            "core_group_edge": visible_edge,
            "hidden_member_edges": (
                "KubernetesManifest->WorkloadKindDecision",
                "KubernetesManifest->ImagePolicyDecision",
                "KubernetesManifest->ProbeAndResourceDecision",
                "WorkloadKindDecision+ImagePolicyDecision+ProbeAndResourceDecision->KubernetesApplyReceipt",
            ),
            "runtime_targets": ("kubernetes.deployment", "kubernetes.job", "contract.test"),
            "adapter_mutators": ("kubernetes_workload_card_emitter", "image_pin_gate", "probe_resource_gate"),
            "proof_requirements": tuple(normalize_field_name(value) for value in _as_sequence(card_policy.get("proof_requirements") or ("manifest_validation_test", "resource_limit_policy_test", "probe_contract_test")) if not _blank(value)),
            "effects": ("kubernetes_manifest_plan", "runtime_safety_check"),
            "source_ref": {"kind": kind, "name": name, "images": images},
            "candidate": True,
            "serves_truth": False,
        })
    for required_kind in sorted(required_kinds):
        if required_kind not in seen_kinds:
            blockers.append(f"missing_required_kind:{required_kind}")
    primitive_ids = tuple(card["primitive_id"] for card in cards)
    card_set_hash = "kubernetes-workload-primitive-cards:" + _digest(
        {"blockers": blockers, "primitive_ids": primitive_ids, "seen_kinds": sorted(seen_kinds)},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SurfacePrimitiveRegistryCardSetReceipt(
        ready=not blockers,
        primitive_ids=primitive_ids,
        cards=tuple(cards),
        blockers=tuple(blockers),
        card_set_hash=card_set_hash,
    )


def compile_terraform_module_primitive_cards(
    module_spec: Mapping[str, Any],
    card_policy: Mapping[str, Any],
) -> SurfacePrimitiveRegistryCardSetReceipt:
    """Compile Terraform module resources into candidate infrastructure primitive cards."""

    raw_module_name = str(module_spec.get("module_name") or module_spec.get("name") or "").strip()
    module_name = normalize_field_name(raw_module_name) if raw_module_name else ""
    resources = tuple(dict(item) for item in _as_mapping_sequence(module_spec.get("resources")))
    variables = tuple(str(value).strip() for value in _as_sequence(module_spec.get("variables")) if str(value).strip())
    outputs = tuple(str(value).strip() for value in _as_sequence(module_spec.get("outputs")) if str(value).strip())
    allowed_resource_types = {str(value) for value in _as_sequence(card_policy.get("allowed_resource_types")) if str(value).strip()}
    primitive_prefix = str(card_policy.get("primitive_id_prefix") or "tf:").strip()
    version = str(card_policy.get("primitive_version") or "1").strip() or "1"
    blockers: list[str] = []
    cards: list[JsonRecord] = []
    if not module_name:
        blockers.append("missing_module_name")
    if not resources:
        blockers.append("missing_resources")
    if card_policy.get("require_variables") and not variables:
        blockers.append("missing_variables")
    if card_policy.get("require_outputs") and not outputs:
        blockers.append("missing_outputs")
    for index, resource in enumerate(resources):
        resource_type = str(resource.get("type") or resource.get("resource_type") or "").strip()
        resource_name = normalize_field_name(resource.get("name") or f"resource_{index + 1}")
        if not resource_type:
            blockers.append(f"resource_{index + 1}_missing_type")
            resource_type = "unknown_resource"
        if allowed_resource_types and resource_type not in allowed_resource_types:
            blockers.append(f"{resource_name}:resource_type_not_allowed:{resource_type}")
        if card_policy.get("require_tags") and not resource.get("tags"):
            blockers.append(f"{resource_name}:missing_tags")
        visible_edge = str(resource.get("visible_edge") or f"TerraformVariables[{module_name}] -> TerraformResourceReceipt[{resource_name}]").strip()
        input_edge, output_edge = _visible_edge_parts(visible_edge, f"TerraformVariables[{module_name}]", f"TerraformResourceReceipt[{resource_name}]")
        primitive_id = _surface_card_primitive_id(primitive_prefix, module_name, resource_type, resource_name, version=version)
        cards.append({
            "primitive_id": primitive_id,
            "kind": "terraform.resource",
            "input_edge": input_edge,
            "output_edge": output_edge,
            "core_group_edge": visible_edge,
            "hidden_member_edges": (
                "TerraformVariables->VariableContractDecision",
                "TerraformResourceSpec->ResourceTypeDecision",
                "TerraformResourceSpec->TagAndOutputDecision",
                "VariableContractDecision+ResourceTypeDecision+TagAndOutputDecision->TerraformResourceReceipt",
            ),
            "runtime_targets": ("terraform.module", "policy.rule", "contract.test"),
            "adapter_mutators": ("terraform_resource_card_emitter", "variable_output_gate", "tag_policy_gate"),
            "proof_requirements": tuple(normalize_field_name(value) for value in _as_sequence(card_policy.get("proof_requirements") or ("terraform_validate_test", "plan_policy_test", "tag_policy_test")) if not _blank(value)),
            "effects": ("infrastructure_plan", "policy_check"),
            "source_ref": {"module_name": module_name, "resource_type": resource_type, "resource_name": resource_name},
            "candidate": True,
            "serves_truth": False,
        })
    primitive_ids = tuple(card["primitive_id"] for card in cards)
    card_set_hash = "terraform-module-primitive-cards:" + _digest(
        {"blockers": blockers, "module_name": module_name, "primitive_ids": primitive_ids},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SurfacePrimitiveRegistryCardSetReceipt(
        ready=not blockers,
        primitive_ids=primitive_ids,
        cards=tuple(cards),
        blockers=tuple(blockers),
        card_set_hash=card_set_hash,
    )


def compile_ci_workflow_primitive_cards(
    workflow_spec: Mapping[str, Any],
    card_policy: Mapping[str, Any],
) -> SurfacePrimitiveRegistryCardSetReceipt:
    """Compile CI workflow definitions into candidate automation primitive cards."""

    workflows = tuple(dict(item) for item in _as_mapping_sequence(workflow_spec.get("workflows"))) or (dict(workflow_spec),)
    primitive_prefix = str(card_policy.get("primitive_id_prefix") or "ci:").strip()
    version = str(card_policy.get("primitive_version") or "1").strip() or "1"
    required_triggers = {normalize_field_name(value) for value in _as_sequence(card_policy.get("required_triggers")) if not _blank(value)}
    blockers: list[str] = []
    cards: list[JsonRecord] = []
    for index, workflow in enumerate(workflows):
        workflow_name = normalize_field_name(workflow.get("workflow_name") or workflow.get("name") or f"workflow_{index + 1}")
        triggers = tuple(normalize_field_name(value) for value in _as_sequence(workflow.get("triggers") or workflow.get("on")) if not _blank(value))
        jobs = tuple(str(value).strip() for value in _as_sequence(workflow.get("jobs")) if str(value).strip())
        permissions = tuple(str(value).strip() for value in _as_sequence(workflow.get("permissions")) if str(value).strip())
        if not triggers:
            blockers.append(f"{workflow_name}:missing_triggers")
        for trigger in sorted(required_triggers):
            if trigger not in triggers:
                blockers.append(f"{workflow_name}:missing_trigger:{trigger}")
        if not jobs:
            blockers.append(f"{workflow_name}:missing_jobs")
        if card_policy.get("require_permissions") and not permissions:
            blockers.append(f"{workflow_name}:missing_permissions")
        if card_policy.get("require_artifacts") and not _as_sequence(workflow.get("artifacts")):
            blockers.append(f"{workflow_name}:missing_artifacts")
        visible_edge = str(workflow.get("visible_edge") or f"RepoEvent[{workflow_name}] -> CiWorkflowReceipt[{workflow_name}]").strip()
        input_edge, output_edge = _visible_edge_parts(visible_edge, f"RepoEvent[{workflow_name}]", f"CiWorkflowReceipt[{workflow_name}]")
        primitive_id = _surface_card_primitive_id(primitive_prefix, workflow_name, version=version)
        cards.append({
            "primitive_id": primitive_id,
            "kind": "ci.workflow",
            "input_edge": input_edge,
            "output_edge": output_edge,
            "core_group_edge": visible_edge,
            "hidden_member_edges": (
                "RepoEvent->TriggerDecision",
                "WorkflowSpec->JobGraphDecision",
                "WorkflowSpec->PermissionAndArtifactDecision",
                "TriggerDecision+JobGraphDecision+PermissionAndArtifactDecision->CiWorkflowReceipt",
            ),
            "runtime_targets": ("github.action", "ci.workflow", "contract.test"),
            "adapter_mutators": ("ci_workflow_card_emitter", "trigger_gate", "permission_artifact_gate"),
            "proof_requirements": tuple(normalize_field_name(value) for value in _as_sequence(card_policy.get("proof_requirements") or ("workflow_lint_test", "permission_scope_test", "artifact_receipt_test")) if not _blank(value)),
            "effects": ("ci_workflow_plan", "artifact_write_optional"),
            "source_ref": {"workflow_name": workflow_name, "triggers": triggers, "jobs": jobs},
            "candidate": True,
            "serves_truth": False,
        })
    primitive_ids = tuple(card["primitive_id"] for card in cards)
    card_set_hash = "ci-workflow-primitive-cards:" + _digest(
        {"blockers": blockers, "primitive_ids": primitive_ids},
        chars=RECEIPT_DIGEST_CHARS,
    )
    return SurfacePrimitiveRegistryCardSetReceipt(
        ready=not blockers,
        primitive_ids=primitive_ids,
        cards=tuple(cards),
        blockers=tuple(blockers),
        card_set_hash=card_set_hash,
    )


def _next_available_field_name(target: str, row: Mapping[str, Any]) -> str:
    suffix = 2
    while f"{target}_{suffix}" in row:
        suffix += 1
    return f"{target}_{suffix}"


def _dedupe_rows(rows: Sequence[JsonRecord], identity_fields: tuple[str, ...], *, keep: str) -> tuple[list[JsonRecord], list[DuplicateRecord]]:
    if not identity_fields:
        return [dict(row) for row in rows], []

    key_order: list[tuple[str, ...]] = []
    kept: dict[tuple[str, ...], tuple[int, JsonRecord]] = {}
    duplicates: list[DuplicateRecord] = []

    for row_index, row in enumerate(rows):
        key = tuple(str(row.get(field, "")) for field in identity_fields)
        if key not in kept:
            key_order.append(key)
            kept[key] = (row_index, dict(row))
            continue
        kept_index, _kept_row = kept[key]
        duplicates.append(DuplicateRecord(duplicate_index=row_index, kept_index=kept_index, key=key))
        if keep == KEEP_LAST:
            kept[key] = (row_index, dict(row))

    return [kept[key][1] for key in key_order], duplicates


def _index_components(values: Sequence[RouteComponent | Mapping[str, Any]]) -> dict[str, tuple[RouteComponent, ...]]:
    by_input: dict[str, list[RouteComponent]] = {}
    for value in values:
        component = value if isinstance(value, RouteComponent) else RouteComponent(
            component_id=str(value.get("component_id") or value.get("id") or value.get("name") or ""),
            input_edge=str(value.get("input_edge") or ""),
            output_edge=str(value.get("output_edge") or ""),
            operation=str(value.get("operation") or value.get("function_name") or ""),
            import_path=str(value.get("import_path") or ""),
            function_name=str(value.get("function_name") or ""),
            cost=int(value.get("cost") or 1),
        )
        if not component.component_id or not component.input_edge or not component.output_edge:
            continue
        by_input.setdefault(component.input_edge, []).append(component)
    return {
        edge: tuple(sorted(items, key=lambda item: (item.cost, item.component_id, item.output_edge)))
        for edge, items in by_input.items()
    }


def _blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _validate_schema_subset(payload: Mapping[str, Any], schema: Mapping[str, Any]) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    required = schema.get("required") if isinstance(schema.get("required"), Sequence) else ()
    for field in required:
        key = str(field)
        if _blank(payload.get(key)):
            violations.append(ContractViolation(path=key, message="required field missing"))

    properties = schema.get("properties") if isinstance(schema.get("properties"), Mapping) else {}
    for key, spec in properties.items():
        if key not in payload or payload.get(key) is None:
            continue
        expected_type = spec.get("type") if isinstance(spec, Mapping) else None
        if expected_type and not _json_type_matches(payload.get(key), str(expected_type)):
            violations.append(ContractViolation(path=str(key), message=f"expected {expected_type}"))
    return violations


def _json_type_matches(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, Mapping)
    if expected == "array":
        return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
    return True


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return (value,)


def _as_mapping_sequence(value: Any) -> tuple[Mapping[str, Any], ...]:
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(item for item in value if isinstance(item, Mapping))
    return ()


def _operation_contract_signature(operation: Any) -> dict[str, Any]:
    if not isinstance(operation, Mapping):
        return {"operation": operation}
    return {
        "parameters": operation.get("parameters"),
        "requestBody": operation.get("requestBody"),
        "responses": operation.get("responses"),
        "security": operation.get("security"),
    }


def _parse_semver(version: str) -> tuple[int, int, int] | None:
    parts = version.strip().lstrip("v").split(".")
    if not 1 <= len(parts) <= 3:
        return None
    try:
        values = tuple(int(part) for part in parts)
    except ValueError:
        return None
    return values + (0,) * (3 - len(values))


def _source_delta_records(source_delta: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    if isinstance(source_delta, Mapping):
        for key in ("records", "changes", "items", "rows"):
            records = source_delta.get(key)
            if isinstance(records, Sequence) and not isinstance(records, (str, bytes, bytearray)):
                return tuple(item for item in records if isinstance(item, Mapping))
        return (source_delta,)
    return tuple(item for item in source_delta if isinstance(item, Mapping))


def _migration_statement_hint(*, operation: str, table: str, column: str, row: Mapping[str, Any]) -> str:
    value_type = str(row.get("type") or row.get("data_type") or "value")
    if operation == "add_column" and column:
        return f"ALTER TABLE {table} ADD COLUMN {column} {value_type}".strip()
    if operation == "drop_column" and column:
        return f"ALTER TABLE {table} DROP COLUMN {column}".strip()
    if operation == "backfill" and column:
        return f"UPDATE {table} SET {column}=<value> WHERE {column} IS NULL".strip()
    if operation == "create_table":
        return f"CREATE TABLE {table} (...)".strip()
    if operation == "drop_table":
        return f"DROP TABLE {table}".strip()
    if operation == "add_foreign_key" and column:
        return f"ALTER TABLE {table} ADD FOREIGN KEY ({column}) REFERENCES <target>".strip()
    return " ".join(part for part in (operation.upper(), table, column) if part)


def _valid_secret_ref(value: Any) -> bool:
    if isinstance(value, Mapping):
        return bool(value.get("ref") or value.get("env") or value.get("secret_name"))
    text = str(value or "")
    return text.startswith(("secret://", "env:", "vault:", "arn:aws:secretsmanager:"))


def _outputs_by_case_id(outputs: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> dict[str, str]:
    if isinstance(outputs, Mapping):
        return {str(key): str(value) for key, value in outputs.items()}
    result: dict[str, str] = {}
    for index, row in enumerate(outputs):
        if not isinstance(row, Mapping):
            continue
        case_id = str(row.get("id") or row.get("case_id") or f"case-{index + 1}")
        result[case_id] = str(row.get("output") or row.get("text") or "")
    return result


def _sort_value(value: Any) -> tuple[int, str, str]:
    if value is None:
        return (1, "none", "")
    return (0, type(value).__name__, _stable_json(value))


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _digest(value: Any, *, chars: int) -> str:
    return sha256_hex(_stable_json(value))[:chars]


def _bytes_digest(value: bytes) -> str:
    return sha256_hex(value)[:FILE_DIGEST_CHARS]


def _utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _append_manifest_event(path: Path, event: Mapping[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_stable_json(dict(event)) + "\n")
