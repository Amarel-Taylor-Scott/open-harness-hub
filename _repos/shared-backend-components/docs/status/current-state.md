# Current State (summary)

See [baltor-current-state-and-opportunities.md](baltor-current-state-and-opportunities.md).

Reference M10: 31/31 · proofs green: 1058 · candidates: unstructured_document_decomposition.

| Section | Status | Reference | Proof | Docs |
|---|---|---|---|---|
| api_runtime | ✅ M10 | yes | `check_consumption_api.py` | _repos/baltor/context/api/context-api.md |
| architecture_guardrails | ✅ M10 | yes | `check_project_spine_folders.py` | _repos/_shared/architecture/architecture-drift-guardrails.md |
| artifact_ledger | ✅ M10 | yes | `check_cfpb_artifact_ledger.py` | _repos/baltor/context/architecture/cfpb-artifact-graph-demo.md |
| conflict_detection | ✅ M10 | yes | `check_cfpb_conflict_detection.py` | _repos/baltor/context/section-cards/conflict-detection.md |
| consumption_readiness | ✅ M10 | yes | `check_optimization_suite.py` | _repos/baltor/context/architecture/optimization-harness.md |
| consumption_service | ✅ M10 | yes | `check_consumption_service.py` | _repos/baltor/context/architecture/consumption-runtime.md |
| context_object_decomposition | ✅ M10 | yes | `ingest/decompose_to_context_objects.py` | _repos/baltor/context/backend/document-decomposition.md |
| context_provider_catalog | m6_proof | no | `check_context_provider_catalog.py` | _repos/baltor/context/research/context-layer-landscape.md |
| context_response | ✅ M10 | yes | `check_cfpb_to_consumption_end_to_end.py` | _repos/baltor/context/architecture/consumption-runtime.md |
| contextops | m6_proof | no | `check_contextops_contracts.py` | _repos/baltor/context/baltor-contextops-verification-foundry.md |
| current_state_reporting | m10_complete | no | `report_current_state.py` | _repos/baltor/context/status/baltor-current-state-and-opportunities.md |
| determinism_factory | m6_proof | no | `check_determinism_contracts.py` | _repos/baltor/context/determinism/overview.md |
| determinism_ui | m8_ui | no | `check_determinism_api.py` | docs/ui/context-surfaces.md |
| docs | ✅ M10 | yes | `check_architecture_adr_coverage.py` | docs/adr |
| durable_queue | ✅ M10 | yes | `durable_store.py` | _repos/baltor/context/architecture/durable-runtime-plan.md |
| encryption_metadata | ✅ M10 | yes | `check_artifact_security_metadata.py` | _repos/baltor/context/security/tenant-isolation-and-encryption.md |
| enhancement | ✅ M10 | yes | `context_compress.py` | _repos/baltor/context/section-cards/enhancement.md |
| event_bus | ✅ M10 | yes | `context_events.py` | _repos/baltor/context/section-cards/event-bus.md |
| fleet_driven_pipeline | m8_ui | no | `fleet_pipeline.py` | _repos/shared-backend-components/context/workers/operating-model-always-on-vs-scale-to-zero.md |
| flywheel_supervisor_scaling | m8_ui | no | `check_flywheel_supervisor_leader_lease.py` | _repos/shared-backend-components/context/workers/flywheel-supervisor-scaling.md |
| fragile_fact_watchtower | m6_proof | no | `check_watchtower_minimum_freshness.py` | _repos/baltor/context/runtime/fragile-fact-watchtower.md |
| graph_builder | ✅ M10 | yes | `check_cfpb_deterministic_graph.py` | _repos/baltor/context/section-cards/graph-builder.md |
| ingestion | ✅ M10 | yes | `ingest/tenant_ingest.py` | _repos/baltor/context/architecture/consumption-runtime.md |
| ingestion_contracts | m6_proof | no | `check_ingestion_contracts.py` | _repos/shared-backend-components/context/ingestion/ingestion-contracts.md |
| llm_gateway | ✅ M10 | yes | `check_llm_gateway_stub.py` | _repos/shared-backend-components/context/architecture/llm-gateway.md |
| local_folder_batch | m8_ui | no | `check_ingest_folder_batch.py` | _repos/shared-backend-components/context/ingestion/folder-batch.md |
| lossless_distillation | m6_proof | no | `check_lossless_distillation_contracts.py` | docs/codex/lossless-distillation.md |
| markdown_folder | m8_ui | no | `check_ingest_markdown_folder.py` | _repos/shared-backend-components/context/ingestion/markdown-folder.md |
| memory_provider | m6_proof | no | `check_memory_provider_contract.py` | _repos/baltor/context/research/supermemory.md |
| memory_ui | m8_ui | no | `check_memory_page_projection_only.py` | _repos/baltor/context/research/supermemory.md |
| multi_source_consumption | m6_proof | no | `check_source_to_consumption_generic.py` | _repos/baltor/context/runtime/source-consumption.md |
| multi_source_ingestion | m10_complete | no | `check_multi_source_ingestion.py` | _repos/shared-backend-components/context/ingestion/multi-source-ingestion.md |
| native_format_preservation | m6_proof | no | `check_native_shape_contract.py` | _repos/baltor/context/native/overview.md |
| native_ui | m8_ui | no | `check_native_ui.py` | docs/ui/context-surfaces.md |
| object_store | m6_proof | no | `check_object_store_payload_ref.py` | _repos/shared-backend-components/context/artifact-graph/object-store.md |
| observability | ✅ M10 | yes | `check_structured_runtime_logging.py` | _repos/baltor/context/section-cards/observability.md |
| observability_provider_seam | m6_proof | no | `check_observability_provider_seam.py` | _repos/baltor/context/observability/provider-seam-and-standards.md |
| opportunity_mapping | m10_complete | no | `check_opportunity_map.py` | docs/status/opportunities.md |
| optimization_suite | ✅ M10 | yes | `check_optimization_harness.py` | _repos/baltor/context/architecture/optimization-harness.md |
| parser_provider | ✅ M10 | yes | `ingest/parser_provider.py` | _repos/baltor/context/backend/document-decomposition.md |
| pattern_standards_factory | m6_proof | no | `check_pattern_registry.py` | docs/standards/pattern-system.md |
| pipeline_pages | m8_ui | no | `check_pipeline_api.py` | _repos/shared-backend-components/context/ui/pipeline-pages.md |
| proof_registry | ✅ M10 | yes | `baltor_acceptance.py` | _repos/shared-backend-components/context/section-cards/proof-registry.md |
| provider_catalog | ✅ M10 | yes | `check_external_capability_catalog.py` | _repos/shared-backend-components/context/architecture/external-capability-catalog.md |
| reconciliation | ✅ M10 | yes | `check_cfpb_reconciliation.py` | _repos/baltor/context/section-cards/reconciliation.md |
| review_pack | ✅ M10 | yes | `make_review_pack.py` | _repos/baltor/context/section-cards/review-pack.md |
| security_tenant_isolation | ✅ M10 | yes | `check_tenant_isolation_policy.py` | _repos/baltor/context/security/tenant-isolation-and-encryption.md |
| source_adapters | ✅ M10 | yes | `ingest/sanctions_feed_live.py` | _repos/baltor/context/backend/architecture-overview.md |
| source_artifact_graph | ✅ M10 | yes | `check_cfpb_source_graph_diff.py` | _repos/baltor/context/section-cards/source-artifact-graph.md |
| standards_api | m8_ui | no | `check_standards_api.py` | _repos/_shared/standards/standards-api.md |
| standards_linter | m6_proof | no | `check_new_code_uses_standards.py` | _repos/_shared/standards/standards-linter.md |
| standards_ui | m8_ui | no | `check_standards_ui.py` | _repos/_shared/standards/standards-api.md |
| structured_atomic_decomposition | ✅ M10 | yes | `ingest/decompose_structured.py` | _repos/baltor/context/decomposition/cfpb-multi-grain-artifacts.md |
| temporal_fact_graph | m8_ui | no | `check_temporal_graph_contracts.py` | docs/graph/temporal-fact-graph.md |
| ui_pages | ✅ M10 | yes | `check_consumption_ui.py` | _repos/baltor/context/ui/consume-page.md |
| unstructured_document_decomposition | candidate | no | `check_pipeline_unstructured.py` | _repos/baltor/context/backend/document-decomposition.md |
| vectorization | ✅ M10 | yes | `check_cfpb_vectorization.py` | _repos/baltor/context/section-cards/vectorization.md |
| verification_gate | ✅ M10 | yes | `check_verification_gate.py` | _repos/baltor/context/architecture/verification-gate.md |
| worker_fleet_supervisor | m6_proof | no | `check_worker_fleet_schema.py` | _repos/shared-backend-components/context/workers/capability-fleet-supervisor.md |
| worker_lifecycle_telemetry | m6_proof | no | `check_worker_lifecycle_policy_details.py` | _repos/shared-backend-components/context/workers/k8s-keda-worker-mapping.md |
| worker_taxonomy | m6_proof | no | `check_worker_bucket_registry.py` | _repos/shared-backend-components/context/workers/worker-taxonomy.md |
| workers | ✅ M10 | yes | `check_durable_worker_parallel.py` | _repos/shared-backend-components/context/workers/durable-worker-runtime.md |
