# /workflows /baltor-k8s-cloudfunction-template-factory (STAGED — launch AFTER any in-flight repo-mutating workflow)

> **SEQUENCING (operational):** do NOT run this concurrently with another file-mutating workflow — both touch
> shared files (`contract_registry.json`, `flywheel_proof_modules.py`, `section_maturity_matrix.json`,
> `technical_debt_register.json`) and concurrent writes corrupt registrations. Launch only when the repo is
> quiescent (no other background build running). Build as focused increments (sequential build-to-green agents
> + parallel adversarial verify), per the recorded lesson — not one stalling multi-phase Workflow.

A governed **Cloud/K8s Worker Template Factory**: agents generate new Kubernetes workers, cloud-function
workers, batch jobs, local emulators, and managed-venv workers **only from approved templates** that FORCE
lifecycle, logging, telemetry, resource ownership, key management, partitioning/clustering, graceful shutdown,
and proof — so the system can auto-build workers to meet recognized demand without becoming fragile.

## GOLDEN TEMPLATE FACTORY CLAUSE (carry in the North Star loop)
Agents may generate workers ONLY from registered templates; templates enforce lifecycle · logging · telemetry ·
resource contracts · security · cleanup · proof. **No generated worker becomes active without local emulation +
contract validation + redteam + registry entry.** Kubernetes and cloud functions are **deployment shapes, not
business logic** — the logic lives behind `CapabilityTask` + `WorkerAppContract` + `ExecutionProviderPort`.
Vendor-neutral + local-emulator-first; BigQuery/KMS/etc. are provider FAMILIES with required local equivalents,
never canonical. No second worker framework / execution framework / durable ledger. No generated worker bypasses
FleetLedger, publishes truth, or creates unmanaged cloud resources.

## 0. Preserve the foundation
Offline demo · CFPB invariant · DurableFleetLedger · live supervisor/flywheel · worker buckets ·
execution-backend flexibility (cloud-agnostic, local-emulators-first) · numeric/non-fragile provider selection ·
no-direct-provider-bypass · memory/LLM/agent/browser ≠ truth. No fake M10, no hidden cloud dependency, no
generated worker without proof.

## 1. Template factory
`templates/workers/{base_worker_app,k8s_deployment_worker,k8s_job_worker,k8s_cronjob_worker,
keda_scaledobject_worker,keda_scaledjob_worker,cloud_function_http,cloud_function_queue,cloud_function_scheduled,
cloud_run_job,local_function_emulator,local_job_emulator,local_worker_pool,managed_venv_worker,browser_worker,
gpu_worker,sandbox_worker}/`. Code `_repos/baltor/backend/src/baltor/templates/{template_renderer,template_registry,template_validator,
template_receipts}.py`. Registries `architecture/{worker_template_catalog,worker_template_policy,
generated_worker_registry,generated_worker_promotion_policy}.json`. Each template entry: template_id ·
execution_backend_family · capability_slots_supported · required_contracts · output_files · variables ·
local_emulator_template · required_data_resources · required_secret_refs · required_proofs · required_redteam ·
generated_docs · promotion_policy · status. **No generated worker active unless its template is registered +
proven.** Proof `check_worker_template_catalog`.

## 2. WorkerAppContract
`_repos/shared-backend-components/schemas/workers/{WorkerAppSpec,WorkerLifecycleSpec,WorkerRuntimeConfig,WorkerTelemetrySpec,WorkerLoggingSpec,
WorkerShutdownSpec,WorkerErrorPolicy,WorkerResourceBinding,GeneratedWorkerReceipt}.v1`. `WorkerAppSpec`:
worker_app_id · capability_id · worker_bucket · execution_backend_policy_id · input/output/task_contract ·
local_emulator_provider · runtime_config_id · telemetry/logging/lifecycle_spec_id · resource_bindings ·
secret_refs · ownership · proofs · docs · promotion_status. `WorkerLifecycleSpec` phases: preflight · bootstrap ·
config_load · dependency_check · module_load · resource_bind · task_poll_or_invoke · atomic_claim · execute ·
emit_progress · write_outputs · ack_or_nack · cleanup · graceful_shutdown · ungraceful_recovery. Register in
contract_registry. Proof `check_worker_app_contracts`.

## 3. BaseWorkerApp abstraction (composition-first)
`_repos/baltor/backend/src/baltor/workers/base_worker_app.py`: BaseWorkerApp + LifecycleRunner + mixins (Preflight · Bootstrap ·
ConfigLoader · ModuleLoader · AtomicClaim · JsonStdoutLogger · TelemetryDbLogger · OtelExporterCandidate ·
ErrorEnvelope · GracefulShutdown · UngracefulRecovery · ResourceBinding · SecretRefResolver · Idempotency ·
RetryDlq · ReceiptWriter). Methods: preflight · bootstrap · load_config · load_modules · bind_resources ·
claim_task · execute_task · write_outputs · ack/nack · emit_progress · cleanup · shutdown_gracefully ·
recover_after_crash · run_once · run_loop. Generated workers implement ONLY the capability handler; they don't
own lifecycle, read raw env (use ConfigLoader/SecretRefResolver), write raw tables (use ports), or own truth.
Proof `check_base_worker_app` (claim-before-execute · output-through-port · graceful-shutdown-runs-cleanup ·
crash-recovery-reclaims-lease · JSON logs + telemetry DB records written).

## 4. JSON logging + telemetry DB
`schemas/telemetry/{JsonLogRecord,WorkerTelemetryEvent,WorkerMetricSample,WorkerTraceSpan}.v1`. Code
`_repos/baltor/backend/src/baltor/observability/{json_logger,telemetry_db,otel_exporter_candidate}.py`. JSON stdout fields: timestamp ·
level · event_name · worker_app_id · worker_id · task_id · tenant_id · project_id · capability_id ·
execution_backend · run_id · trace_id · span_id · correlation_id · causation_id · attempt · status · message ·
fields · error. Telemetry DB: same identifiers + lifecycle_phase · start/end · duration_ms · resource_usage ·
retry_count · error_code · result_artifact_ids. stdout = JSON lines; telemetry DB = local/offline default; OTel
export = candidate; **NO secrets in logs**; logs correlate to task ledger + receipts. Proofs
`check_json_stdout_logging` · `check_worker_telemetry_db` · `check_no_secrets_in_worker_logs`.

## 5. Resource contracts (datasets/tables/keys/partitions/clusters)
`_repos/shared-backend-components/schemas/resources/{DataResourceSpec,DatasetSpec,TableSpec,TemporaryResourceSpec,PersistentResourceSpec,
PartitioningSpec,ClusteringSpec,KeyManagementSpec,ResourceOwnershipSpec,ResourceProvisionPlan,
ResourceProvisionReceipt}.v1`. `DataResourceSpec`: resource_id · provider_family(local_sqlite|postgres|bigquery|
snowflake|duckdb|object_store|other) · logical_name · physical_name_template · ownership_mode(external_existing|
managed_persistent|managed_ephemeral|pipeline_temp|tenant_dedicated) · lifecycle(create_if_missing|validate_only|
migrate_if_owned|never_create|drop_after_run|expire_by_policy) · schema_ref · partitioning · clustering ·
encryption_key_ref · retention_policy · data_residency · tenant_scope · cost_center · owner · proof_required.
`PartitioningSpec`: partition_type(time|integer_range|ingestion_time|none) · field · granularity ·
expiration_days · require_partition_filter. `ClusteringSpec`: clustering_fields · max_fields · provider_limits.
`KeyManagementSpec`: key_ref · key_provider(local_stub|gcp_kms|aws_kms|azure_key_vault|external_kms) ·
rotation_policy · access_policy_ref · cmek_required. Rules: generated workers NEVER create tables ad hoc — they
request via ResourceManagerPort; external_existing → validate only; managed_persistent → create/migrate only via
plan; pipeline_temp → TTL/expiration + cleanup; tenant_dedicated → tenant physical name + key ref; **BigQuery is
one family, not canonical; local SQLite/DuckDB are the offline default.** Proof `check_data_resource_contracts`.

## 6. ResourceManagerPort
`_repos/baltor/backend/src/baltor/ports/resource_manager.py` + `_repos/baltor/backend/src/baltor/resources/{resource_manager,local_sqlite_resource_manager,
bigquery_candidate_resource_manager,resource_naming,resource_receipts}.py`. Port: plan · validate · provision ·
migrate · cleanup · health. Providers: resources.local_sqlite@v1 (offline default) · local_duckdb@candidate ·
bigquery@candidate · postgres@candidate · snowflake@candidate · object_store@candidate. Missing BigQuery creds
must NOT block the local equivalent; enforce ownership_mode + partition/cluster/key policy where supported;
unsupported features return structured warning/failure (never silent). Proofs `check_resource_manager_local` ·
`check_bigquery_candidate_resource_contract` · `check_resource_ownership_modes` · `check_temporary_resource_cleanup`
· `check_persistent_resource_validation`.

## 7. Worker configuration object model
`schemas/config/{WorkerConfigBundle,RuntimeConfigProfile,EnvironmentProfile,TenantExecutionProfile,ModuleLoadSpec,
DependencySpec}.v1` + `architecture/{worker_config_profiles,environment_profiles,tenant_execution_profiles}.json`.
Workers receive config OBJECTS — no scattered env lookups, no provider display-string branching, no hard-coded
dataset/table names in handlers; tenant profile can override isolation/keys/table-ownership/backend-eligibility;
config version appears in telemetry + receipts. Proof `check_worker_configuration_objects`.

## 8–10. Lifecycle templates (preflight/bootstrap · module loading · shutdown/recovery)
`_repos/baltor/backend/src/baltor/workers/{preflight,bootstrap,module_loader,shutdown,recovery}.py`. Preflight: config validates ·
contracts registered · schemas available · resource specs validate · required resources exist-or-planned ·
secret REFS resolve (not values) · local emulator exists · provider health ok · tenant allows backend · logging/
telemetry init · shutdown policy installed · timeouts · idempotency key template · retry/DLQ policy. ModuleLoad:
validates handler exists + signature + allowed/forbidden deps (no provider-SDK/admin-server/web import in
handler) + typed output. Graceful shutdown: stop claiming → finish within grace → drain event → ack/nack → flush
telemetry → release temp resources → mark stopped (K8s preStop sets draining, terminationGracePeriodSeconds
allows finish, readiness fails when draining). Ungraceful: heartbeat expiry → lease reclaim → retry → temp
resources cleaned by TTL/reaper → persistent remain → idempotency blocks duplicate side effects. Proofs
`check_worker_preflight_bootstrap` · `check_worker_module_loading` · `check_worker_shutdown_recovery`.

## 11–13. Templates: K8s · cloud function · data resources
**K8s** (`deployment/job/cronjob/keda_scaledobject/keda_scaledjob`): `*.yaml.j2` + `worker_app.py.j2` + RBAC/SA/
configmap/secrets.example + README + proof. Must include liveness/readiness/startup probes · preStop drain ·
terminationGracePeriodSeconds · resource requests/limits · env REFS (no raw secrets) · config profile · telemetry
+ JSON logging · labels (baltor.worker_app_id/capability_id/worker_bucket/execution_backend/config_version) ·
KEDA trigger + queue-depth/oldest-task-age placeholders · uses BaseWorkerApp. Proof `check_k8s_worker_templates`.
**Cloud function** (http/queue/scheduled/cloud_run_job): cloud-AGNOSTIC core (`function_app/handler/requirements/
config/resource_specs/README/proof`) + candidate provider adapters (aws_lambda/gcp_cloud_function/azure_function/
cloudflare_worker/openfaas_knative). Core handler uses BaseWorkerApp; MUST claim a task from FleetLedger before
processing (no raw event-owned truth); local function emulator runs the SAME handler; no provider-specific
business logic in core. Proof `check_cloud_function_templates`. **Data resources** (dataset/table/temp_table/
bigquery_table_candidate/postgres_table_candidate/sqlite_table_local): schema · partition · cluster · key ref ·
retention · TTL · ownership · validate-only · migration plan · provision receipt. Proof `check_data_resource_templates`.

## 14–16. Generator · safety gate · examples
`scripts/generate_worker_from_template.py` (--template/--worker-app-id/--capability-id/--worker-bucket/
--execution-backend/--config-profile → renders into `generated/workers/<id>/`, writes GeneratedWorkerReceipt +
registry patch + proof + docs, refuses overwrite without --force, NEVER activates until proof passes). Proof
`check_generate_worker_from_template`. `_repos/baltor/backend/src/baltor/workers/generated_worker_gate.py` promotion states:
generated_draft → rendered → local_emulated → proof_green → redteam_green → registered_candidate → active_local →
active_external; agent PROPOSES, generator renders, sandbox/emulator proves, redteam passes, human approval for
real cloud/prod; generated worker can't edit its template or write outside its output path. Proof
`check_generated_worker_promotion_gate`. Examples (≥3 local, proven): utility.hash.local_function (cloud_function_
queue + local emulator; proves JSON+telemetry) · monitor.health.k8s_pool_local (k8s_deployment + local pool;
proves graceful drain + telemetry table) · ingestion.fixture.local_job (k8s_job/cloud_run_job + local job
emulator + temp table + cleanup). Optional: warehouse.write_metrics.local_function (local SQLite table +
BigQuery candidate spec; partition/cluster validated). Proof `check_generated_worker_examples`.

## 17–18. API/UI + redteam
API (local-only render/proof/promote-local; no real cloud activation/secrets from UI): `/api/templates/{workers,
resources}` · `/api/generated-workers[/<id>[/proofs|resources|telemetry]]` · POST render/run-local-proof/
promote-local. UI `/templates` (or extend `/fleet`): template catalogs · generated workers · lifecycle phases ·
logging/telemetry · data resources · KMS refs · temp-vs-persistent · K8s + cloud-function rendered preview ·
local emulator run · proof/redteam · promotion gate. Proofs `check_worker_template_{api,ui}`. Redteam
`check_worker_template_redteam` — all FAIL safely: missing preflight/JSON-logging/telemetry · raw secret env read
· ad-hoc table creation · persistent-table-when-policy-temp · temp-table-without-TTL · persistent-without-owner/
retention/key · BigQuery-without-local-equivalent · process-without-atomic-claim · K8s-missing-preStop/grace ·
cloud-handler-with-provider-business-logic · emit CanonicalFact/ContextResponse · bypass WorkerAppContract ·
activate-without-proof/redteam · write-outside-allowed-path.

## 19–20. Docs + registries
Docs `_repos/shared-backend-components/docs/workers/{worker-template-factory,base-worker-app-contract,k8s-worker-templates,cloud-function-templates,
generated-worker-promotion,worker-lifecycle-...,json-logging-and-telemetry}.md` + `docs/resources/{data-resource-
specs,temp-vs-persistent-resources,partitioning-clustering-key-management,bigquery-candidate-resource-manager}.md`
+ `docs/templates/agent-generated-workers.md`. Update registries: worker_template_catalog/policy,
generated_worker_registry/promotion_policy, contract_registry, runtime_ownership, worker_bucket_registry,
execution_backend_policy_matrix, provider_emulation_matrix, tool_replacement_graph, section_maturity_matrix,
technical_debt_register, opportunities, risk_register. Hard rules: no generated worker active without proof +
redteam; no real cloud/K8s active without approval + proof; no data resource without DataResourceSpec; no BigQuery
candidate without a local SQLite equivalent; no UI/API M10 unless surfaces proven.

## 21–22. Proofs + acceptance
Create/run all `check_*` above + `check_worker_template_factory_full_stack`; REGRESS durable_fleet_ledger ·
live_supervisor_full_stack · execution_backend_full_stack · no_direct_provider_bypass · demo_offline_full_baltor ·
check_baltor_full_stack_perfect · `baltor_flywheel.py --once`. Acceptance: template catalog · WorkerAppContract ·
BaseWorkerApp · JSON+telemetry logging · no-secrets · DataResourceSpec · ResourceManagerPort · local SQLite RM ·
BigQuery-as-candidate-with-local-equivalent · ownership modes · temp cleanup · persistent validation · config
objects · preflight/bootstrap · module loading · graceful/ungraceful shutdown · K8s templates render w/ lifecycle+
telemetry+security · cloud-function templates render w/ cloud-agnostic core · data-resource templates · generator
renders · promotion gate blocks unsafe · ≥3 example workers pass local proof · API+UI · redteam fails safely ·
regressions + flywheel GREEN.

*Warrant: clear owner intent (a golden ground-up template/abstraction factory for K8s + cloud functions enforcing
logging/telemetry/resource-governance/lifecycle so agents can safely auto-generate workers to meet demand).
Vendor-neutral, local-emulator-first, BigQuery/KMS as candidate families with local equivalents; deployment shapes
≠ business logic (CapabilityTask + WorkerAppContract + ExecutionProviderPort). Build as focused increments; do NOT
run concurrently with another repo-mutating workflow.*
