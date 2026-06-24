# Current State (summary)

See [baltor-current-state-and-opportunities.md](baltor-current-state-and-opportunities.md).

Reference M10: 31/31 · proofs green: 672 · candidates: unstructured_document_decomposition.

| Section | Status | Reference | Proof | Docs |
|---|---|---|---|---|
| api_runtime | ✅ M10 | yes | `check_consumption_api.py` | docs/api/context-api.md |
| architecture_guardrails | ✅ M10 | yes | `check_project_spine_folders.py` | docs/architecture/architecture-drift-guardrails.md |
| artifact_ledger | ✅ M10 | yes | `check_cfpb_artifact_ledger.py` | docs/architecture/cfpb-artifact-graph-demo.md |
| conflict_detection | ✅ M10 | yes | `check_cfpb_conflict_detection.py` | docs/section-cards/conflict-detection.md |
| consumption_readiness | ✅ M10 | yes | `check_optimization_suite.py` | docs/architecture/optimization-harness.md |
| consumption_service | ✅ M10 | yes | `check_consumption_service.py` | docs/architecture/consumption-runtime.md |
| context_object_decomposition | ✅ M10 | yes | `ingest/decompose_to_context_objects.py` | docs/backend/document-decomposition.md |
| context_provider_catalog | m6_proof | no | `check_context_provider_catalog.py` | docs/research/context-layer-landscape.md |
| context_response | ✅ M10 | yes | `check_cfpb_to_consumption_end_to_end.py` | docs/architecture/consumption-runtime.md |
| contextops | m6_proof | no | `check_contextops_contracts.py` | prompts/baltor-contextops-verification-foundry.md |
| current_state_reporting | m10_complete | no | `report_current_state.py` | docs/status/baltor-current-state-and-opportunities.md |
| determinism_factory | m6_proof | no | `check_determinism_contracts.py` | docs/determinism/overview.md |
| determinism_ui | m8_ui | no | `check_determinism_api.py` | docs/ui/context-surfaces.md |
| docs | ✅ M10 | yes | `check_architecture_adr_coverage.py` | docs/adr |
| durable_queue | ✅ M10 | yes | `durable_store.py` | docs/architecture/durable-runtime-plan.md |
| encryption_metadata | ✅ M10 | yes | `check_artifact_security_metadata.py` | docs/security/tenant-isolation-and-encryption.md |
| enhancement | ✅ M10 | yes | `context_compress.py` | docs/section-cards/enhancement.md |
| event_bus | ✅ M10 | yes | `context_events.py` | docs/section-cards/event-bus.md |
| fleet_driven_pipeline | m8_ui | no | `fleet_pipeline.py` | docs/workers/operating-model-always-on-vs-scale-to-zero.md |
| flywheel_supervisor_scaling | m8_ui | no | `check_flywheel_supervisor_leader_lease.py` | docs/workers/flywheel-supervisor-scaling.md |
| fragile_fact_watchtower | m6_proof | no | `check_watchtower_minimum_freshness.py` | docs/runtime/fragile-fact-watchtower.md |
| graph_builder | ✅ M10 | yes | `check_cfpb_deterministic_graph.py` | docs/section-cards/graph-builder.md |
| ingestion | ✅ M10 | yes | `ingest/tenant_ingest.py` | docs/architecture/consumption-runtime.md |
| ingestion_contracts | m6_proof | no | `check_ingestion_contracts.py` | docs/ingestion/ingestion-contracts.md |
| llm_gateway | ✅ M10 | yes | `check_llm_gateway_stub.py` | docs/architecture/llm-gateway.md |
| local_folder_batch | m8_ui | no | `check_ingest_folder_batch.py` | docs/ingestion/folder-batch.md |
| lossless_distillation | m6_proof | no | `check_lossless_distillation_contracts.py` | docs/codex/lossless-distillation.md |
| markdown_folder | m8_ui | no | `check_ingest_markdown_folder.py` | docs/ingestion/markdown-folder.md |
| memory_provider | m6_proof | no | `check_memory_provider_contract.py` | docs/research/supermemory.md |
| memory_ui | m8_ui | no | `check_memory_page_projection_only.py` | docs/research/supermemory.md |
| multi_source_consumption | m6_proof | no | `check_source_to_consumption_generic.py` | docs/runtime/source-consumption.md |
| multi_source_ingestion | m10_complete | no | `check_multi_source_ingestion.py` | docs/ingestion/multi-source-ingestion.md |
| native_format_preservation | m6_proof | no | `check_native_shape_contract.py` | docs/native/overview.md |
| native_ui | m8_ui | no | `check_native_ui.py` | docs/ui/context-surfaces.md |
| object_store | m6_proof | no | `check_object_store_payload_ref.py` | docs/artifact-graph/object-store.md |
| observability | ✅ M10 | yes | `check_structured_runtime_logging.py` | docs/section-cards/observability.md |
| observability_provider_seam | m6_proof | no | `check_observability_provider_seam.py` | docs/observability/provider-seam-and-standards.md |
| opportunity_mapping | m10_complete | no | `check_opportunity_map.py` | docs/status/opportunities.md |
| optimization_suite | ✅ M10 | yes | `check_optimization_harness.py` | docs/architecture/optimization-harness.md |
| parser_provider | ✅ M10 | yes | `ingest/parser_provider.py` | docs/backend/document-decomposition.md |
| pattern_standards_factory | m6_proof | no | `check_pattern_registry.py` | docs/standards/pattern-system.md |
| pipeline_pages | m8_ui | no | `check_pipeline_api.py` | docs/ui/pipeline-pages.md |
| proof_registry | ✅ M10 | yes | `baltor_acceptance.py` | docs/section-cards/proof-registry.md |
| provider_catalog | ✅ M10 | yes | `check_external_capability_catalog.py` | docs/architecture/external-capability-catalog.md |
| reconciliation | ✅ M10 | yes | `check_cfpb_reconciliation.py` | docs/section-cards/reconciliation.md |
| review_pack | ✅ M10 | yes | `make_review_pack.py` | docs/section-cards/review-pack.md |
| security_tenant_isolation | ✅ M10 | yes | `check_tenant_isolation_policy.py` | docs/security/tenant-isolation-and-encryption.md |
| source_adapters | ✅ M10 | yes | `ingest/sanctions_feed_live.py` | docs/backend/architecture-overview.md |
| source_artifact_graph | ✅ M10 | yes | `check_cfpb_source_graph_diff.py` | docs/section-cards/source-artifact-graph.md |
| standards_api | m8_ui | no | `check_standards_api.py` | docs/standards/standards-api.md |
| standards_linter | m6_proof | no | `check_new_code_uses_standards.py` | docs/standards/standards-linter.md |
| standards_ui | m8_ui | no | `check_standards_ui.py` | docs/standards/standards-api.md |
| structured_atomic_decomposition | ✅ M10 | yes | `ingest/decompose_structured.py` | docs/decomposition/cfpb-multi-grain-artifacts.md |
| temporal_fact_graph | m8_ui | no | `check_temporal_graph_contracts.py` | docs/graph/temporal-fact-graph.md |
| ui_pages | ✅ M10 | yes | `check_consumption_ui.py` | docs/ui/consume-page.md |
| unstructured_document_decomposition | candidate | no | `check_pipeline_unstructured.py` | docs/backend/document-decomposition.md |
| vectorization | ✅ M10 | yes | `check_cfpb_vectorization.py` | docs/section-cards/vectorization.md |
| verification_gate | ✅ M10 | yes | `check_verification_gate.py` | docs/architecture/verification-gate.md |
| worker_fleet_supervisor | m6_proof | no | `check_worker_fleet_schema.py` | docs/workers/capability-fleet-supervisor.md |
| worker_lifecycle_telemetry | m6_proof | no | `check_worker_lifecycle_policy_details.py` | docs/workers/k8s-keda-worker-mapping.md |
| worker_taxonomy | m6_proof | no | `check_worker_bucket_registry.py` | docs/workers/worker-taxonomy.md |
| workers | ✅ M10 | yes | `check_durable_worker_parallel.py` | docs/workers/durable-worker-runtime.md |
