from __future__ import annotations

import json
import unittest

from src.teleon.primitives import (
    RouteComponent,
    assemble_cited_answer,
    build_dashboard_metric_snapshot,
    build_test_fixture,
    compile_agent_tool_schema_from_openapi,
    compile_asyncapi_event_primitive_cards,
    compile_ci_workflow_primitive_cards,
    compile_compliance_evidence_workflow,
    compile_container_runtime_primitive_cards,
    compile_kubernetes_workload_primitive_cards,
    compile_openapi_endpoint_primitive_cards,
    compile_runbook_plan,
    compile_service_surface_primitive_cards,
    compile_terraform_module_primitive_cards,
    compare_benchmark_route_token_usage,
    collapse_route_to_group_card,
    compile_cli_command_request,
    compile_exact_edge_route,
    compile_integration_sync_plan,
    decompose_benchmark_task_to_primitive_components,
    evaluate_benchmark_trace_pair,
    evaluate_benchmark_route_promotion_candidate,
    evaluate_alert_rule,
    evaluate_citation_coverage,
    evaluate_auth_middleware_request,
    evaluate_data_quality_rule,
    evaluate_deployment_readiness,
    evaluate_dependency_vulnerability_exception,
    evaluate_domain_event_handler,
    evaluate_event_schema_compatibility,
    evaluate_openapi_compatibility,
    evaluate_policy_api_request,
    evaluate_policy_rule,
    evaluate_prompt_model_outputs,
    evaluate_primitive_consumer_readiness,
    evaluate_primitive_registry_expansion_coverage,
    evaluate_rate_limit_request,
    evaluate_secret_scan_findings,
    evaluate_scheduled_job_tick,
    evaluate_vector_index_freshness,
    evaluate_workflow_step_transition,
    extract_asyncapi_operations,
    extract_openapi_operations,
    guarded_replace_file,
    ingest_benchmark_trace_pairs,
    normalize_field_name,
    normalize_cloudevent_envelope,
    plan_access_review_evidence,
    plan_audit_log_policy,
    plan_agent_tool_permission_matrix,
    plan_api_async_job_endpoint,
    plan_api_auth_scope_matrix,
    plan_api_bulk_operation,
    plan_api_contract_test_suite,
    plan_api_deprecation_notice,
    plan_api_endpoint_telemetry,
    plan_api_gateway_route,
    plan_api_key_rotation,
    plan_api_operation_example_coverage,
    plan_api_resource_group,
    plan_api_request_validation,
    plan_api_usage_plan,
    plan_api_versioning_policy,
    plan_benchmark_run_arm,
    plan_batch_checkpoint,
    plan_backup_restore,
    plan_backup_restore_drill,
    plan_blue_green_deployment,
    plan_cache_invalidation,
    plan_canary_release,
    plan_cdc_capture,
    plan_chaos_experiment,
    plan_circuit_breaker,
    plan_concurrency_limit,
    plan_consumer_group_offset,
    plan_connector_auth_binding,
    plan_connector_cursor_checkpoint,
    plan_connector_error_quarantine,
    plan_connector_field_mapping,
    plan_connector_rate_limit_budget,
    plan_cors_security_headers,
    plan_cron_catchup_window,
    plan_dashboard_filter_contract,
    plan_dead_letter_replay,
    plan_dependency_readiness,
    plan_docker_compose_stack,
    plan_dockerfile,
    plan_document_chunking,
    plan_data_deletion_workflow,
    plan_data_lineage_contract,
    plan_data_quarantine_policy,
    plan_data_retention_enforcement,
    plan_environment_promotion,
    plan_elt_model,
    plan_etl_pipeline,
    plan_event_publication,
    plan_execution_audit_trail,
    plan_external_identity_map,
    plan_error_envelope_contract,
    plan_github_action_workflow,
    plan_graceful_shutdown,
    plan_graphql_resolver,
    plan_grpc_method_call,
    plan_health_probe_contract,
    plan_helm_chart,
    plan_idempotency_policy,
    plan_inbox_deduplication,
    plan_incident_triage,
    plan_kubernetes_job,
    plan_kubernetes_controller,
    plan_license_compliance,
    plan_materialized_view_refresh,
    plan_migration_lock,
    plan_microservice_bundle,
    plan_memory_retention_policy,
    plan_mock_server,
    plan_model_routing_policy,
    plan_pagination_contract,
    plan_maintenance_window,
    plan_partition_strategy,
    plan_pii_redaction_policy,
    plan_feature_flag,
    plan_observability_instrumentation,
    plan_oncall_escalation,
    plan_outbox_publication,
    plan_postmortem_action_items,
    plan_pitfall_avoidance_matrix,
    plan_primitive_candidate_intake,
    plan_primitive_graph_runtime,
    plan_primitive_lift_comparison,
    plan_primitive_proof_coverage_matrix,
    plan_primitive_promotion_review,
    plan_primitive_reuse_observation,
    plan_prompt_regression_suite,
    plan_privileged_access_approval,
    plan_queue_ack_policy,
    plan_queue_batch_consumer,
    plan_queue_ordering_policy,
    plan_queue_payload_contract,
    plan_queue_poison_message_policy,
    plan_rbac_policy_matrix,
    plan_queue_visibility_timeout,
    plan_queue_job_execution,
    plan_retrieval_rerank_policy,
    plan_request_signing_policy,
    plan_response_cache_policy,
    plan_registry_publish_manifest,
    plan_retry_backoff_policy,
    plan_route_promotion_evidence_pack,
    plan_runtime_shape_adapter,
    plan_runtime_shape_adapter_matrix,
    plan_run_artifact_manifest,
    plan_stream_watermark,
    plan_sync_conflict_resolution,
    plan_sync_reconciliation_report,
    plan_sbom_generation,
    plan_sdk_package,
    plan_sdk_client_request,
    plan_service_backpressure_policy,
    plan_service_boundary_contract,
    plan_service_data_ownership,
    plan_service_dependency_contract,
    plan_service_discovery_registration,
    plan_service_ownership_runbook,
    plan_service_secret_binding,
    plan_service_startup_order,
    plan_service_surface_inventory,
    plan_tenant_isolation,
    plan_task_lease,
    plan_sql_procedure,
    plan_sql_view,
    plan_shell_script,
    plan_slo_error_budget_policy,
    plan_secret_rotation,
    plan_serverless_function,
    plan_status_page_update,
    plan_tool_invocation,
    plan_terraform_module,
    plan_timeout_budget,
    plan_token_savings_attribution,
    plan_ui_component,
    plan_ui_accessibility_interaction,
    plan_ui_api_binding,
    plan_ui_form_validation,
    plan_ui_route,
    plan_ui_table_state,
    plan_vector_index_build,
    plan_runtime_config_schema,
    plan_schema_drift_gate,
    plan_webhook_delivery_policy,
    plan_webhook_replay_window,
    plan_tenant_data_boundary,
    plan_worker_autoscale_policy,
    plan_worker_heartbeat,
    plan_workflow_compensation,
    plan_workflow_group,
    plan_database_migration,
    prepare_record_import,
    resolve_tenant_settings,
    verify_webhook_event,
)


class TeleonPrimitiveGroupTests(unittest.TestCase):
    def test_prepare_record_import_groups_normalization_validation_dedupe_and_fingerprints(self) -> None:
        rows = [
            {"Vendor ID": "v-2", "CompanyName": "Beta", "Amount": "20"},
            {"Vendor ID": "v-1", "CompanyName": "Alpha", "Amount": "10"},
            {"vendor_id": "v-1", "company name": "Alpha Updated", "Amount": "12"},
            {"Vendor ID": "", "Amount": "5"},
        ]

        result = prepare_record_import(
            rows,
            required_fields=("vendor_id", "company_name"),
            identity_fields=("vendor_id",),
            field_aliases={"company name": "company_name"},
            sort_fields=("vendor_id",),
            keep="last",
        )

        self.assertEqual(result.original_count, 4)
        self.assertEqual(result.prepared_count, 3)
        self.assertEqual(result.duplicate_count, 1)
        self.assertEqual(result.invalid_records[0].row_index, 3)
        self.assertEqual(result.invalid_records[0].missing_fields, ("vendor_id", "company_name"))
        self.assertEqual([record["vendor_id"] for record in result.records], ["", "v-1", "v-2"])
        self.assertEqual(result.records[1]["company_name"], "Alpha Updated")
        self.assertTrue(result.idempotency_key.startswith("record-import:"))
        self.assertEqual(len(result.schema_fingerprint), 16)

    def test_prepare_record_import_preserves_normalized_field_collisions(self) -> None:
        result = prepare_record_import([
            {"First Name": "Ada", "first_name": "A.", "Last Name": "Lovelace"},
        ])

        self.assertEqual(result.records, ({"first_name": "Ada", "first_name_2": "A.", "last_name": "Lovelace"},))
        self.assertEqual(result.collisions[0].target, "first_name")
        self.assertEqual(result.collisions[0].preserved_as, "first_name_2")

    def test_normalize_field_name_is_ascii_snake_case(self) -> None:
        self.assertEqual(normalize_field_name("HTTP Response Code"), "http_response_code")
        self.assertEqual(normalize_field_name("Caf\u00e9Total"), "cafe_total")
        self.assertEqual(normalize_field_name(""), "field")

    def test_compile_exact_edge_route_uses_shortest_deterministic_path(self) -> None:
        plan = compile_exact_edge_route(
            "RawRecordBatch",
            "ApiResponse",
            [
                RouteComponent("slow", "RawRecordBatch", "ValidatedRecords", "validate", cost=5),
                RouteComponent("slow-2", "ValidatedRecords", "ApiResponse", "emit", cost=1),
                RouteComponent("group", "RawRecordBatch", "PreparedRecordImport", "prepare", cost=1),
                RouteComponent("emit", "PreparedRecordImport", "ApiResponse", "emit", cost=1),
            ],
        )

        self.assertTrue(plan.route_found)
        self.assertEqual([component.component_id for component in plan.components], ["group", "emit"])
        self.assertEqual(plan.edge_path, ("RawRecordBatch", "PreparedRecordImport", "ApiResponse"))

    def test_compile_exact_edge_route_reports_missing_route(self) -> None:
        plan = compile_exact_edge_route(
            "RawRecordBatch",
            "ApiResponse",
            [RouteComponent("prepare", "RawRecordBatch", "PreparedRecordImport", "prepare")],
        )

        self.assertFalse(plan.route_found)
        self.assertEqual(plan.skipped_reason, "unreached_goal")
        self.assertEqual(plan.components, ())

    def test_collapse_route_to_group_card_hides_route_behind_visible_edge(self) -> None:
        plan = compile_exact_edge_route(
            "RawRecordBatch",
            "ApiResponse",
            [
                RouteComponent("prepare", "RawRecordBatch", "PreparedRecordImport", "prepare"),
                RouteComponent("emit", "PreparedRecordImport", "ApiResponse", "emit"),
            ],
        )

        card = collapse_route_to_group_card(plan, group_id="grp:test@1", title="Record import API group")

        self.assertEqual(card["primitive_id"], "grp:test@1")
        self.assertEqual(card["input_edge"], "RawRecordBatch")
        self.assertEqual(card["output_edge"], "ApiResponse")
        self.assertEqual(card["blackbox"]["hidden_step_count"], 2)
        self.assertEqual([edge["component_id"] for edge in card["member_edges"]], ["prepare", "emit"])

    def test_plan_primitive_graph_runtime_orders_edge_cards_without_full_code(self) -> None:
        receipt = plan_primitive_graph_runtime(
            {
                "route_id": "csv-import-api",
                "start_edge": "RawCsvArtifact+ImportPolicy",
                "goal_edge": "HttpResponse[ValidatedImportReceipt]",
                "primitive_cards": [
                    {
                        "primitive_id": "grp:teleon.record_import.prepare@1",
                        "kind": "data_import",
                        "input_edge": "RawCsvArtifact+ImportPolicy",
                        "output_edge": "ValidatedImportReceipt",
                        "hidden_member_edges": [
                            "RawCsvArtifact -> ParsedRows",
                            "ParsedRows -> ValidatedRows",
                        ],
                        "adapter_mutators": ["schema_validator_inserter"],
                        "proof_requirements": ["fixture_import_test"],
                        "effects": ["database_write"],
                        "runtime_targets": ["local.python"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "primitive_id": "api:csv.import.response@candidate",
                        "kind": "api.endpoint",
                        "input_edge": "ValidatedImportReceipt",
                        "output_edge": "HttpResponse[ValidatedImportReceipt]",
                        "hidden_member_edges": ["ValidatedImportReceipt -> HttpResponse"],
                        "adapter_mutators": ["api_endpoint_wrapper"],
                        "proof_requirements": ["openapi_contract_test"],
                        "effects": ["network_write"],
                        "runtime_targets": ["api.endpoint"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                ],
                "candidate": True,
                "serves_truth": False,
            },
            {
                "require_candidate_boundary": True,
                "require_hidden_member_edges": True,
                "require_adapter_mutators": True,
                "require_proof_requirements": True,
                "require_runtime_targets": True,
                "required_adapter_mutators": ["api_endpoint_wrapper"],
                "required_proof_requirements": ["openapi_contract_test"],
                "required_runtime_targets": ["api.endpoint"],
                "min_steps": 2,
            },
        )
        blocked = plan_primitive_graph_runtime(
            {
                "route_id": "bad",
                "start_edge": "A",
                "goal_edge": "C",
                "primitive_cards": [
                    {"primitive_id": "a_to_b", "input_edge": "A", "output_edge": "B", "candidate": False, "serves_truth": True},
                ],
            },
            {
                "require_candidate_boundary": True,
                "require_hidden_member_edges": True,
                "require_adapter_mutators": True,
                "require_proof_requirements": True,
                "require_runtime_targets": True,
            },
        )

        self.assertTrue(receipt.ready)
        self.assertEqual(
            receipt.ordered_primitive_ids,
            ("grp:teleon.record_import.prepare@1", "api:csv.import.response@candidate"),
        )
        self.assertEqual(
            receipt.edge_path,
            ("RawCsvArtifact+ImportPolicy", "ValidatedImportReceipt", "HttpResponse[ValidatedImportReceipt]"),
        )
        self.assertIn("api_endpoint_wrapper", receipt.adapter_mutators)
        self.assertIn("openapi_contract_test", receipt.proof_requirements)
        self.assertIn("api_endpoint", receipt.runtime_targets)
        self.assertTrue(receipt.candidate)
        self.assertFalse(receipt.serves_truth)
        self.assertTrue(receipt.plan_hash.startswith("primitive-graph-runtime-plan:"))
        self.assertFalse(blocked.ready)
        self.assertIn("unreached_goal", blocked.blockers)
        self.assertIn("a_to_b:candidate_boundary_not_declared", blocked.blockers)
        self.assertIn("a_to_b:serves_truth_must_be_false", blocked.blockers)
        self.assertIn("missing_hidden_member_edges", blocked.blockers)
        self.assertIn("missing_adapter_mutators", blocked.blockers)
        self.assertIn("missing_proof_requirements", blocked.blockers)
        self.assertIn("missing_runtime_targets", blocked.blockers)

    def test_evaluate_primitive_consumer_readiness_checks_edges_and_tool_consumers(self) -> None:
        receipt = evaluate_primitive_consumer_readiness(
            {
                "primitive_cards": [
                    {
                        "primitive_id": "grp:teleon.record_import.prepare@1",
                        "kind": "artifact.primitive_group",
                        "title": "CSV import preparation group",
                        "input_edge": "RawCsvArtifact+ImportPolicy",
                        "output_edge": "ValidatedImportReceipt",
                        "blackbox": {"does": "Parses, validates, dedupes, and receipts a CSV import batch."},
                        "blocking_keys": ["csv", "import", "dedupe", "receipt"],
                        "hidden_member_edges": [
                            "RawCsvArtifact -> ParsedRows",
                            "ParsedRows -> ValidatedRows",
                            "ValidatedRows -> DedupedRows",
                        ],
                        "adapter_mutators": ["schema_validator_inserter", "idempotency_wrapper"],
                        "proof_requirements": ["fixture_import_test", "idempotency_test"],
                        "runtime_targets": ["local.python", "api.endpoint"],
                        "effects": ["database_write", "audit_log_write"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "primitive_id": "api:record_import.post@candidate",
                        "kind": "api.endpoint",
                        "title": "CSV import HTTP endpoint wrapper",
                        "input_edge": "ValidatedImportReceipt",
                        "output_edge": "HttpResponse[ValidatedImportReceipt]",
                        "blackbox": {"does": "Wraps the import receipt as a typed HTTP response."},
                        "blocking_keys": ["openapi", "endpoint", "http", "response"],
                        "hidden_member_edges": ["ValidatedImportReceipt -> HttpResponse"],
                        "adapter_mutators": ["api_endpoint_wrapper", "output_wrapper"],
                        "proof_requirements": ["openapi_contract_test"],
                        "runtime_targets": ["api.endpoint"],
                        "effects": ["network_write"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                ],
                "candidate": True,
                "serves_truth": False,
            },
            {
                "consumer_surfaces": [
                    "teleon",
                    "aidevobserver",
                    "aidevexplorer",
                    "baltor",
                    "openhubforai",
                    "coding_agent",
                ],
                "development_tools": ["Codex", "Claude Code", "Kimi", "GLM", "Gemma 4"],
                "require_candidate_boundary": True,
                "require_hidden_member_edges": True,
                "require_adapter_mutators": True,
                "require_proof_requirements": True,
                "require_runtime_targets": True,
                "require_effects": True,
                "min_search_terms_per_card": 5,
            },
        )
        blocked = evaluate_primitive_consumer_readiness(
            {
                "primitive_cards": [
                    {
                        "kind": "",
                        "blackbox": "",
                        "candidate": False,
                        "serves_truth": True,
                    }
                ],
                "candidate": False,
                "serves_truth": True,
            },
            {
                "consumer_surfaces": ["teleon", "aidevobserver", "baltor", "openhubforai", "coding_agent"],
                "development_tools": ["Codex"],
                "require_candidate_boundary": True,
                "require_hidden_member_edges": True,
                "require_adapter_mutators": True,
                "require_proof_requirements": True,
                "require_runtime_targets": True,
                "require_effects": True,
                "min_search_terms_per_card": 4,
            },
        )

        self.assertTrue(receipt.ready)
        self.assertEqual(receipt.card_count, 2)
        self.assertEqual(
            receipt.development_tools,
            ("codex", "claude_code", "kimi", "glm", "gemma_4"),
        )
        self.assertIn("teleon", receipt.ready_surfaces)
        self.assertIn("aidevobserver", receipt.ready_surfaces)
        self.assertIn("baltor", receipt.ready_surfaces)
        self.assertIn("codex:edge_card_ready", receipt.consumer_statuses)
        self.assertIn("claude_code:edge_card_ready", receipt.consumer_statuses)
        self.assertIn("gemma_4:edge_card_ready", receipt.consumer_statuses)
        self.assertIn("RawCsvArtifact+ImportPolicy -> ValidatedImportReceipt", receipt.visible_edges)
        self.assertIn("api_endpoint", receipt.runtime_targets)
        self.assertIn("openapi_contract_test", receipt.proof_requirements)
        self.assertIn("csv", receipt.searchable_terms)
        self.assertTrue(receipt.readiness_hash.startswith("primitive-consumer-readiness:"))
        self.assertTrue(receipt.candidate)
        self.assertFalse(receipt.serves_truth)
        self.assertFalse(blocked.ready)
        self.assertIn("candidate_boundary_not_declared", blocked.blockers)
        self.assertIn("serves_truth_must_be_false", blocked.blockers)
        self.assertIn("card_1:missing_primitive_id", blocked.blockers)
        self.assertIn("card_1:missing_input_edge", blocked.blockers)
        self.assertIn("card_1:missing_hidden_member_edges", blocked.blockers)
        self.assertIn("card_1:missing_adapter_mutators", blocked.blockers)
        self.assertIn("card_1:missing_proof_requirements", blocked.blockers)
        self.assertIn("card_1:missing_runtime_targets", blocked.blockers)
        self.assertIn("card_1:missing_effects", blocked.blockers)
        self.assertIn("card_1:insufficient_search_terms", blocked.blockers)
        self.assertIn("codex:blocked", blocked.consumer_statuses)

    def test_evaluate_primitive_registry_expansion_coverage_checks_required_families(self) -> None:
        cards = [
            {
                "primitive_id": "grp:teleon.api_resource_group.plan@1",
                "kind": "api.endpoint",
                "runtime_targets": ["api.endpoint", "local.python"],
                "source_family": "curated_first_party_primitive_group",
                "source_evidence_status": "source_backed",
                "candidate": True,
                "serves_truth": False,
            },
            {
                "primitive_id": "grp:teleon.microservice_bundle.plan@1",
                "kind": "service.group",
                "runtime_targets": ["container.python", "kubernetes.deployment"],
                "source_family": "curated_first_party_primitive_group",
                "source_evidence_status": "source_backed",
                "candidate": True,
                "serves_truth": False,
            },
            {
                "primitive_id": "grp:teleon.webhook_event.verify@1",
                "kind": "webhook.handler",
                "runtime_targets": ["webhook.handler", "api.endpoint"],
                "source_family": "curated_first_party_primitive_group",
                "source_evidence_status": "source_backed",
                "candidate": True,
                "serves_truth": False,
            },
            {
                "primitive_id": "grp:teleon.queue_job.plan@1",
                "kind": "queue.consumer",
                "runtime_targets": ["queue.consumer", "container.python"],
                "source_family": "curated_first_party_primitive_group",
                "source_evidence_status": "source_backed",
                "candidate": True,
                "serves_truth": False,
            },
        ]
        proof_bundles = [
            {"subject_id": card["primitive_id"], "proof_kind": "unit_test", "status": "pass"}
            for card in cards
        ]
        coverage = evaluate_primitive_registry_expansion_coverage(
            {
                "source_backed_cards": cards,
                "proof_bundles": proof_bundles,
                "search_smokes": [
                    {
                        "expected_id": "grp:teleon.api_resource_group.plan@1",
                        "rank": 1,
                    }
                ],
                "candidate": True,
                "serves_truth": False,
            },
            {
                "required_kinds": ["api.endpoint", "service.group", "webhook.handler", "queue.consumer"],
                "required_runtime_targets": ["api.endpoint", "kubernetes.deployment", "queue.consumer"],
                "required_source_families": ["curated_first_party_primitive_group"],
                "required_search_smoke_ids": ["grp:teleon.api_resource_group.plan@1"],
                "require_proof_bundles": True,
                "require_search_smokes": True,
                "require_candidate_boundary": True,
                "min_cards": 4,
                "max_search_rank": 1,
            },
        )
        blocked = evaluate_primitive_registry_expansion_coverage(
            {
                "cards": [
                    {
                        "primitive_id": "grp:teleon.api_resource_group.plan@1",
                        "kind": "api.endpoint",
                        "runtime_targets": ["api.endpoint"],
                        "source_family": "curated_first_party_primitive_group",
                        "source_evidence_status": "source_backed",
                        "candidate": False,
                        "serves_truth": True,
                    }
                ],
                "proof_bundles": [],
                "candidate": False,
                "serves_truth": True,
            },
            {
                "required_kinds": ["api.endpoint", "service.group"],
                "required_runtime_targets": ["api.endpoint", "queue.consumer"],
                "required_source_families": ["curated_first_party_primitive_group"],
                "required_search_smoke_ids": ["grp:teleon.api_resource_group.plan@1"],
                "require_proof_bundles": True,
                "require_search_smokes": True,
                "require_candidate_boundary": True,
                "min_cards": 2,
            },
        )

        self.assertTrue(coverage.ready)
        self.assertEqual(coverage.card_count, 4)
        self.assertIn("api_endpoint", coverage.covered_kinds)
        self.assertIn("service_group", coverage.covered_kinds)
        self.assertIn("kubernetes_deployment", coverage.covered_runtime_targets)
        self.assertIn("curated_first_party_primitive_group", coverage.covered_source_families)
        self.assertEqual(coverage.missing_kinds, ())
        self.assertEqual(coverage.unproofed_primitive_ids, ())
        self.assertEqual(coverage.search_smoke_ids, ("grp:teleon.api_resource_group.plan@1",))
        self.assertTrue(coverage.coverage_hash.startswith("primitive-registry-expansion-coverage:"))
        self.assertTrue(coverage.candidate)
        self.assertFalse(coverage.serves_truth)
        self.assertFalse(blocked.ready)
        self.assertIn("card_count_below_policy", blocked.blockers)
        self.assertIn("candidate_boundary_not_declared", blocked.blockers)
        self.assertIn("serves_truth_must_be_false", blocked.blockers)
        self.assertIn("grp:teleon.api_resource_group.plan@1:candidate_boundary_not_declared", blocked.blockers)
        self.assertIn("grp:teleon.api_resource_group.plan@1:serves_truth_must_be_false", blocked.blockers)
        self.assertIn("required_kinds_missing", blocked.blockers)
        self.assertIn("required_runtime_targets_missing", blocked.blockers)
        self.assertIn("proof_bundle_coverage_missing", blocked.blockers)
        self.assertIn("grp:teleon.api_resource_group.plan@1:missing_search_smoke", blocked.blockers)
        self.assertIn("missing_search_smokes", blocked.blockers)

    def test_guarded_replace_file_archives_previous_content_and_writes_manifest(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            from pathlib import Path

            root = Path(tmp)
            target = root / "app.py"
            archive_dir = root / "archives"
            target.write_text("old", encoding="utf-8")

            receipt = guarded_replace_file(target, "new", archive_dir, reason="unit test")

            self.assertEqual(target.read_text(encoding="utf-8"), "new")
            self.assertIsNotNone(receipt.archive_path)
            self.assertIsNotNone(receipt.previous_digest)
            self.assertIsNotNone(receipt.new_digest)
            self.assertEqual(receipt.manifest_path, str(archive_dir / "manifest.jsonl"))
            self.assertTrue(str(receipt.archive_path).endswith("_app.py"))

            manifest_line = (archive_dir / "manifest.jsonl").read_text(encoding="utf-8").strip()
            manifest = json.loads(manifest_line)
            self.assertEqual(manifest["target_path"], str(target))
            self.assertEqual(manifest["reason"], "unit test")

    def test_policy_api_request_validates_scope_and_idempotency(self) -> None:
        schema = {
            "required": ["company_id", "idempotency_key"],
            "properties": {"company_id": {"type": "string"}},
        }

        allowed = evaluate_policy_api_request(
            {"company_id": "co_1", "idempotency_key": "req-1"},
            schema,
            actor_scopes=("company:write",),
            required_scopes=("company:write",),
        )
        duplicate = evaluate_policy_api_request(
            {"company_id": "co_1", "idempotency_key": "req-1"},
            schema,
            actor_scopes=("company:write",),
            required_scopes=("company:write",),
            idempotency_keys_seen=("req-1",),
        )
        missing_scope = evaluate_policy_api_request(
            {"company_id": "co_1", "idempotency_key": "req-2"},
            schema,
            actor_scopes=(),
            required_scopes=("company:write",),
        )

        self.assertTrue(allowed.allowed)
        self.assertEqual(allowed.status, "allowed")
        self.assertEqual(duplicate.status, "duplicate_request")
        self.assertEqual(missing_scope.status, "missing_scope")
        self.assertTrue(allowed.decision_receipt.startswith("policy-api:"))

    def test_resolve_tenant_settings_redacts_secret_overrides(self) -> None:
        result = resolve_tenant_settings(
            {"region": "us", "api_key": "default-secret", "limit": 10},
            {"region": "eu", "api_key": "tenant-secret"},
            schema={"required": ["region"], "properties": {"limit": {"type": "integer"}}},
            secret_fields=("api_key",),
            version="settings-v1",
        )

        self.assertEqual(result.effective_settings["region"], "eu")
        self.assertEqual(result.redacted_settings["api_key"], "***")
        self.assertEqual({source.key: source.source for source in result.setting_sources}["region"], "tenant_override")
        self.assertEqual(result.validation_errors, ())
        self.assertTrue(result.settings_hash.startswith("settings:"))

    def test_evaluate_deployment_readiness_reports_blockers(self) -> None:
        report = evaluate_deployment_readiness({
            "required_config_keys": ["DATABASE_URL"],
            "config": {},
            "secret_refs": {"API_KEY": "plain-secret"},
            "health_checks": [{"id": "live", "path": "healthz"}],
            "resources": {},
        })

        self.assertFalse(report.ready)
        self.assertIn("required_config", report.blockers)
        self.assertIn("secret_refs", report.blockers)
        self.assertIn("health_checks", report.blockers)
        self.assertIn("resource_limits", report.blockers)
        self.assertTrue(report.receipt_hash.startswith("deploy-ready:"))

    def test_evaluate_prompt_model_outputs_scores_required_terms(self) -> None:
        report = evaluate_prompt_model_outputs(
            [
                {"id": "a", "expected_terms": ["citation", "receipt"]},
                {"id": "b", "expected_terms": ["rollback"]},
            ],
            {"a": "Answer includes citation and receipt.", "b": "No matching term."},
        )

        self.assertEqual(report.total_count, 2)
        self.assertEqual(report.passed_count, 1)
        self.assertEqual(report.failed_case_ids, ("b",))
        self.assertEqual(report.pass_rate, 0.5)
        self.assertTrue(report.report_hash.startswith("prompt-eval:"))

    def test_plan_database_migration_requires_rollback_for_destructive_changes(self) -> None:
        receipt = plan_database_migration(
            {"tables": {"customers": {"columns": ["id", "email"]}}},
            {
                "operations": [
                    {"op": "add_column", "table": "customers", "column": "tier", "type": "text"},
                    {"op": "drop_column", "table": "customers", "column": "legacy_code"},
                ],
            },
        )

        self.assertFalse(receipt.ready_for_dry_run)
        self.assertIn("destructive_change_requires_rollback", receipt.blockers)
        self.assertIn("destructive_change_review", receipt.integrity_checks)
        self.assertEqual(receipt.operations[0].statement_hint, "ALTER TABLE customers ADD COLUMN tier text")
        self.assertTrue(receipt.receipt_hash.startswith("db-migration:"))

    def test_plan_database_migration_accepts_batched_backfill_with_rollback(self) -> None:
        receipt = plan_database_migration(
            {"tables": {"customers": {"columns": ["id", "tier"]}}},
            {
                "operations": [
                    {"op": "backfill", "table": "customers", "column": "tier", "batch_size": 500},
                ],
                "rollback_steps": ["restore tier from backup"],
            },
        )

        self.assertTrue(receipt.ready_for_dry_run)
        self.assertEqual(receipt.blockers, ())
        self.assertIn("row_count_before_after", receipt.integrity_checks)

    def test_compile_integration_sync_plan_maps_fields_and_skips_duplicate_keys(self) -> None:
        receipt = compile_integration_sync_plan(
            [
                {"email": "a@example.com", "company": "Acme"},
                {"email": "a@example.com", "company": "Acme duplicate"},
                {"company": "Missing email"},
            ],
            {
                "target_system": "hubspot",
                "identity_fields": ["email"],
                "field_mapping": {"company": "company_name"},
                "operation": "upsert",
            },
        )

        self.assertEqual(receipt.source_count, 3)
        self.assertEqual(receipt.mutation_count, 1)
        self.assertEqual(receipt.skipped_records, (1, 2))
        self.assertEqual(receipt.mutations[0].payload["company_name"], "Acme")
        self.assertTrue(receipt.idempotency_key.startswith("integration-sync:"))

    def test_assemble_cited_answer_uses_only_matching_evidence(self) -> None:
        receipt = assemble_cited_answer(
            "How do retries preserve idempotency?",
            [
                {"source_id": "doc-1", "span": "p1", "text": "Retries preserve idempotency by reusing the idempotency key."},
                {"source_id": "doc-2", "span": "p2", "text": "Unrelated deployment note."},
            ],
            retrieval_policy={"required_terms": ["idempotency"], "max_citations": 2},
        )

        self.assertTrue(receipt.grounded)
        self.assertEqual(len(receipt.citations), 1)
        self.assertEqual(receipt.citations[0].source_id, "doc-1")
        self.assertIn("idempotency", receipt.answer.lower())
        self.assertTrue(receipt.receipt_hash.startswith("cited-answer:"))

    def test_verify_webhook_event_checks_signature_dedupe_and_required_body(self) -> None:
        receipt = verify_webhook_event(
            {
                "headers": {"X-Signature": "sig-1"},
                "body": {"id": "evt-1", "type": "invoice.paid", "account_id": "acct-1"},
                "source": "stripe",
            },
            {
                "source": "stripe",
                "signature_header": "X-Signature",
                "expected_signature": "sig-1",
                "required_body_fields": ["account_id"],
            },
        )
        duplicate = verify_webhook_event(
            {
                "headers": {"X-Signature": "sig-1"},
                "body": {"id": "evt-1", "type": "invoice.paid", "account_id": "acct-1"},
            },
            {
                "signature_header": "X-Signature",
                "expected_signature": "sig-1",
                "dedupe_event_ids": ["evt-1"],
            },
        )

        self.assertTrue(receipt.verified)
        self.assertEqual(receipt.domain_event["event_type"], "invoice.paid")
        self.assertTrue(receipt.idempotency_key.startswith("webhook:"))
        self.assertEqual(duplicate.status, "duplicate")
        self.assertEqual(duplicate.blockers, ("duplicate_event",))

    def test_plan_queue_job_execution_rejects_duplicates_and_executes_valid_jobs(self) -> None:
        execute = plan_queue_job_execution(
            {"message_id": "msg-1", "job_type": "send_email", "payload": {"to": "a@example.com"}},
            {"allowed_job_types": ["send_email"], "required_payload_fields": ["to"], "max_attempts": 3},
        )
        retry = plan_queue_job_execution(
            {"message_id": "msg-2", "job_type": "send_email", "payload": {}, "attempt": 1},
            {"allowed_job_types": ["send_email"], "required_payload_fields": ["to"], "retry_after_seconds": 30},
        )
        dead_letter = plan_queue_job_execution(
            {"message_id": "msg-3", "job_type": "send_email", "payload": {"to": "a@example.com"}, "attempt": 3},
            {"allowed_job_types": ["send_email"], "required_payload_fields": ["to"], "max_attempts": 3},
        )

        self.assertTrue(execute.accepted)
        self.assertEqual(execute.action, "execute")
        self.assertEqual(retry.action, "retry_later")
        self.assertEqual(retry.retry_after_seconds, 30)
        self.assertEqual(dead_letter.action, "dead_letter")
        self.assertTrue(execute.receipt_hash.startswith("queue-job:"))

    def test_plan_queue_payload_contract_and_ack_policy_enforce_worker_contracts(self) -> None:
        payload_contract = plan_queue_payload_contract(
            {
                "queue_name": "invoice-events",
                "schema_ref": "schema://invoice-event/v1",
                "schema_version": "1.0",
                "payload_schema": {"required": ["tenant_id", "event_id"], "properties": {"tenant_id": {"type": "string"}, "event_id": {"type": "string"}}},
                "headers": {"X-Tenant-Id": "tenant", "X-Event-Id": "event"},
                "sample_message": {"tenant_id": "t-1", "event_id": "evt-1"},
                "contract_receipt": "payload-contract-1",
            },
            {
                "require_schema_ref": True,
                "allowed_schema_versions": ["1.0"],
                "required_fields": ["tenant_id", "event_id"],
                "required_headers": ["X-Tenant-Id", "X-Event-Id"],
                "require_sample_message": True,
                "require_contract_receipt": True,
            },
        )
        bad_payload_contract = plan_queue_payload_contract(
            {
                "schema_version": "2.0",
                "payload_schema": {"required": ["tenant_id"], "properties": {"tenant_id": {"type": "string"}}},
                "headers": {"X-Tenant-Id": "tenant"},
            },
            {
                "require_schema_ref": True,
                "allowed_schema_versions": ["1.0"],
                "required_fields": ["tenant_id", "event_id"],
                "required_headers": ["X-Tenant-Id", "X-Event-Id"],
                "require_sample_message": True,
                "require_contract_receipt": True,
            },
        )
        ack = plan_queue_ack_policy(
            {
                "queue_name": "invoice-events",
                "ack_mode": "after_success",
                "nack_mode": "retry_or_dlq",
                "ack_timeout_seconds": 30,
                "ack_after_success": True,
                "nack_on_failure": True,
                "visibility_extension": "extend-on-progress",
                "ack_receipt": "ack-1",
            },
            {
                "allowed_ack_modes": ["after_success"],
                "allowed_nack_modes": ["retry_or_dlq"],
                "max_ack_timeout_seconds": 60,
                "require_ack_after_success": True,
                "require_nack_on_failure": True,
                "require_visibility_extension": True,
                "require_ack_receipt": True,
            },
        )
        bad_ack = plan_queue_ack_policy(
            {"ack_mode": "auto", "ack_timeout_seconds": 120},
            {
                "allowed_ack_modes": ["after_success"],
                "allowed_nack_modes": ["retry_or_dlq"],
                "max_ack_timeout_seconds": 60,
                "require_ack_after_success": True,
                "require_nack_on_failure": True,
                "require_visibility_extension": True,
                "require_ack_receipt": True,
            },
        )

        self.assertTrue(payload_contract.ready)
        self.assertTrue(payload_contract.contract_hash.startswith("queue-payload-contract:"))
        self.assertFalse(bad_payload_contract.ready)
        self.assertIn("missing_queue_name", bad_payload_contract.blockers)
        self.assertIn("missing_schema_ref", bad_payload_contract.blockers)
        self.assertIn("missing_required_field:event_id", bad_payload_contract.blockers)
        self.assertIn("field_not_in_schema:event_id", bad_payload_contract.blockers)
        self.assertIn("missing_header:X-Event-Id", bad_payload_contract.blockers)
        self.assertIn("schema_version_not_allowed:2.0", bad_payload_contract.blockers)
        self.assertIn("missing_sample_message", bad_payload_contract.blockers)
        self.assertIn("missing_contract_receipt", bad_payload_contract.blockers)
        self.assertTrue(ack.ready)
        self.assertFalse(bad_ack.ready)
        self.assertIn("missing_queue_name", bad_ack.blockers)
        self.assertIn("ack_mode_not_allowed:auto", bad_ack.blockers)
        self.assertIn("missing_nack_mode", bad_ack.blockers)
        self.assertIn("ack_timeout_exceeds_policy", bad_ack.blockers)
        self.assertIn("missing_ack_after_success", bad_ack.blockers)
        self.assertIn("missing_nack_on_failure", bad_ack.blockers)
        self.assertIn("missing_visibility_extension", bad_ack.blockers)
        self.assertIn("missing_ack_receipt", bad_ack.blockers)

    def test_plan_queue_poison_and_batch_consumer_enforce_failure_boundaries(self) -> None:
        poison = plan_queue_poison_message_policy(
            {
                "queue_name": "invoice-events",
                "poison_threshold": 3,
                "quarantine_sink": "invoice-events-poison",
                "classification_rules": ["schema_error", "permanent_auth_error"],
                "alert_topic": "ops-alerts",
                "replay_policy": "manual-after-fix",
                "poison_receipt": "poison-1",
            },
            {
                "max_poison_threshold": 5,
                "require_quarantine_sink": True,
                "require_classification_rules": True,
                "require_alert_topic": True,
                "require_replay_policy": True,
                "require_poison_receipt": True,
            },
        )
        bad_poison = plan_queue_poison_message_policy(
            {"poison_threshold": 10},
            {
                "max_poison_threshold": 5,
                "require_quarantine_sink": True,
                "require_classification_rules": True,
                "require_alert_topic": True,
                "require_replay_policy": True,
                "require_poison_receipt": True,
            },
        )
        batch = plan_queue_batch_consumer(
            {
                "queue_name": "invoice-events",
                "batch_size": 50,
                "max_wait_seconds": 10,
                "partial_failure_mode": "per_item_retry",
                "per_item_receipt": "item-receipt",
                "batch_idempotency_key": "batch_id",
                "checkpoint": "offset-100",
            },
            {
                "max_batch_size": 100,
                "max_wait_seconds": 30,
                "allowed_partial_failure_modes": ["per_item_retry", "atomic"],
                "require_partial_failure_mode": True,
                "require_per_item_receipt": True,
                "require_batch_idempotency_key": True,
                "require_checkpoint": True,
            },
        )
        bad_batch = plan_queue_batch_consumer(
            {"batch_size": 500, "max_wait_seconds": 60, "partial_failure_mode": "drop"},
            {
                "max_batch_size": 100,
                "max_wait_seconds": 30,
                "allowed_partial_failure_modes": ["per_item_retry", "atomic"],
                "require_partial_failure_mode": True,
                "require_per_item_receipt": True,
                "require_batch_idempotency_key": True,
                "require_checkpoint": True,
            },
        )

        self.assertTrue(poison.ready)
        self.assertFalse(bad_poison.ready)
        self.assertIn("missing_queue_name", bad_poison.blockers)
        self.assertIn("poison_threshold_exceeds_policy", bad_poison.blockers)
        self.assertIn("missing_quarantine_sink", bad_poison.blockers)
        self.assertIn("missing_classification_rules", bad_poison.blockers)
        self.assertIn("missing_alert_topic", bad_poison.blockers)
        self.assertIn("missing_replay_policy", bad_poison.blockers)
        self.assertIn("missing_poison_receipt", bad_poison.blockers)
        self.assertTrue(batch.ready)
        self.assertFalse(bad_batch.ready)
        self.assertIn("missing_queue_name", bad_batch.blockers)
        self.assertIn("batch_size_exceeds_policy", bad_batch.blockers)
        self.assertIn("max_wait_exceeds_policy", bad_batch.blockers)
        self.assertIn("partial_failure_mode_not_allowed:drop", bad_batch.blockers)
        self.assertIn("missing_per_item_receipt", bad_batch.blockers)
        self.assertIn("missing_batch_idempotency_key", bad_batch.blockers)
        self.assertIn("missing_checkpoint", bad_batch.blockers)

    def test_plan_queue_ordering_and_worker_autoscale_enforce_runtime_scaling_edges(self) -> None:
        ordering = plan_queue_ordering_policy(
            {
                "queue_name": "invoice-events",
                "ordering_key": "tenant_id",
                "ordering_mode": "partition_fifo",
                "partition_key": "tenant_id",
                "sequence_check": "sequence_number",
                "gap_handling": "pause-partition",
                "reorder_dlq": "invoice-events-reorder-dlq",
                "ordering_receipt": "ordering-1",
            },
            {
                "allowed_ordering_modes": ["partition_fifo", "best_effort"],
                "require_partition_key": True,
                "require_sequence_check": True,
                "require_gap_handling": True,
                "require_reorder_dlq": True,
                "require_ordering_receipt": True,
            },
        )
        bad_ordering = plan_queue_ordering_policy(
            {"ordering_mode": "random"},
            {
                "allowed_ordering_modes": ["partition_fifo"],
                "require_partition_key": True,
                "require_sequence_check": True,
                "require_gap_handling": True,
                "require_reorder_dlq": True,
                "require_ordering_receipt": True,
            },
        )
        autoscale = plan_worker_autoscale_policy(
            {
                "worker_name": "invoice-worker",
                "scale_metric": "queue_depth",
                "min_replicas": 1,
                "max_replicas": 10,
                "target_value": 100,
                "cooldown_seconds": 60,
                "drain_policy": "finish-inflight",
                "scale_to_zero_guard": "business-hours-only",
                "autoscale_receipt": "autoscale-1",
            },
            {
                "allowed_scale_metrics": ["queue_depth", "lag_seconds"],
                "max_replicas": 20,
                "require_cooldown": True,
                "require_drain_policy": True,
                "require_scale_to_zero_guard": True,
                "require_autoscale_receipt": True,
            },
        )
        bad_autoscale = plan_worker_autoscale_policy(
            {"scale_metric": "cpu", "min_replicas": 3, "max_replicas": 1},
            {
                "allowed_scale_metrics": ["queue_depth"],
                "max_replicas": 20,
                "require_cooldown": True,
                "require_drain_policy": True,
                "require_scale_to_zero_guard": True,
                "require_autoscale_receipt": True,
            },
        )

        self.assertTrue(ordering.ready)
        self.assertFalse(bad_ordering.ready)
        self.assertIn("missing_queue_name", bad_ordering.blockers)
        self.assertIn("missing_ordering_key", bad_ordering.blockers)
        self.assertIn("ordering_mode_not_allowed:random", bad_ordering.blockers)
        self.assertIn("missing_partition_key", bad_ordering.blockers)
        self.assertIn("missing_sequence_check", bad_ordering.blockers)
        self.assertIn("missing_gap_handling", bad_ordering.blockers)
        self.assertIn("missing_reorder_dlq", bad_ordering.blockers)
        self.assertIn("missing_ordering_receipt", bad_ordering.blockers)
        self.assertTrue(autoscale.ready)
        self.assertFalse(bad_autoscale.ready)
        self.assertIn("missing_worker_name", bad_autoscale.blockers)
        self.assertIn("scale_metric_not_allowed:cpu", bad_autoscale.blockers)
        self.assertIn("max_replicas_less_than_min", bad_autoscale.blockers)
        self.assertIn("missing_target_value", bad_autoscale.blockers)
        self.assertIn("missing_cooldown_seconds", bad_autoscale.blockers)
        self.assertIn("missing_drain_policy", bad_autoscale.blockers)
        self.assertIn("missing_scale_to_zero_guard", bad_autoscale.blockers)
        self.assertIn("missing_autoscale_receipt", bad_autoscale.blockers)

    def test_evaluate_scheduled_job_tick_declares_lock_and_skip_reasons(self) -> None:
        run = evaluate_scheduled_job_tick(
            {"date": "2026-07-01", "hour": 9, "minute": 0, "weekday": "wednesday"},
            {"job_name": "daily-report", "allowed_hours": [9], "allowed_weekdays": ["wednesday"]},
        )
        skipped = evaluate_scheduled_job_tick(
            {"date": "2026-07-01", "hour": 10, "minute": 0, "weekday": "wednesday"},
            {"job_name": "daily-report", "allowed_hours": [9]},
        )

        self.assertTrue(run.should_run)
        self.assertTrue(run.lock_key.startswith("cron-lock:"))
        self.assertEqual(skipped.skipped_reason, "hour_not_allowed")
        self.assertIn("idempotent_lock_test", run.proof_requirements)

    def test_compile_cli_command_request_normalizes_argv_and_blocks_unknown_flags(self) -> None:
        receipt = compile_cli_command_request(
            {"flags": {"suite": "unit", "verbose": True}, "positional": ["tests/unit"]},
            {
                "command": "pytest",
                "allowed_commands": ["pytest"],
                "allowed_flags": ["suite", "verbose"],
                "required_flags": ["suite"],
            },
        )
        blocked = compile_cli_command_request(
            {"flags": {"unsafe": "x"}},
            {"command": "pytest", "allowed_commands": ["pytest"], "allowed_flags": ["suite"]},
        )

        self.assertTrue(receipt.executable)
        self.assertEqual(receipt.command_argv, ("pytest", "--suite", "unit", "--verbose", "tests/unit"))
        self.assertFalse(blocked.executable)
        self.assertEqual(blocked.blockers, ("flag_not_allowed:unsafe",))
        self.assertTrue(receipt.receipt_hash.startswith("cli-command:"))

    def test_plan_kubernetes_job_blocks_mutable_images_and_missing_limits(self) -> None:
        blocked = plan_kubernetes_job(
            {
                "name": "embed-build",
                "containers": [{"name": "worker", "image": "repo/worker:latest"}],
                "restart_policy": "OnFailure",
            },
            {"require_resource_limits": True, "forbid_latest_tag": True},
        )
        ready = plan_kubernetes_job(
            {
                "name": "embed-build",
                "containers": [{
                    "name": "worker",
                    "image": "repo/worker:2026-07-01",
                    "resources": {"limits": {"cpu": "1", "memory": "1Gi"}},
                }],
                "restart_policy": "Never",
                "service_account": "jobs",
            },
            {"require_resource_limits": True, "require_service_account": True},
        )

        self.assertFalse(blocked.ready)
        self.assertIn("container_1_mutable_image_tag", blocked.blockers)
        self.assertIn("container_1_missing_resource_limits", blocked.blockers)
        self.assertIn("restart_policy_must_be_never", blocked.blockers)
        self.assertTrue(ready.ready)
        self.assertTrue(ready.manifest_hash.startswith("k8s-job:"))

    def test_build_dashboard_metric_snapshot_reports_missing_and_stale_metrics(self) -> None:
        snapshot = build_dashboard_metric_snapshot(
            [
                {"metric": "queue_depth", "value": 3, "epoch": 100, "source_id": "redis"},
                {"metric": "error_rate", "value": 0.02, "epoch": 10, "source_id": "logs"},
            ],
            {
                "required_metrics": ["queue_depth", "error_rate", "p95_latency"],
                "current_epoch": 200,
                "max_age_seconds": 60,
            },
        )

        self.assertFalse(snapshot.ready)
        self.assertEqual(snapshot.missing_metrics, ("p95_latency",))
        self.assertEqual(snapshot.stale_metrics, ("error_rate", "queue_depth"))
        self.assertEqual([tile.metric for tile in snapshot.tiles], ["error_rate", "queue_depth"])
        self.assertTrue(snapshot.snapshot_hash.startswith("dashboard:"))

    def test_evaluate_auth_middleware_request_authorizes_and_reports_missing_scopes(self) -> None:
        allowed = evaluate_auth_middleware_request(
            {"request_id": "req-1", "path": "/admin", "method": "POST"},
            {"subject_id": "user-1", "token": "tok", "scopes": ["admin:write", "admin:read"]},
            {"required_scopes": ["admin:write"], "allowed_subjects": ["user-1"]},
        )
        denied = evaluate_auth_middleware_request(
            {"request_id": "req-2", "path": "/admin", "method": "POST"},
            {"subject_id": "user-2", "token": "tok", "scopes": ["admin:read"]},
            {"required_scopes": ["admin:write"], "allowed_subjects": ["user-1"]},
        )

        self.assertTrue(allowed.authorized)
        self.assertEqual(allowed.authorized_request["subject_id"], "user-1")
        self.assertFalse(denied.authorized)
        self.assertEqual(denied.missing_scopes, ("admin:write",))
        self.assertTrue(denied.receipt_hash.startswith("auth-middleware:"))

    def test_evaluate_rate_limit_request_reports_remaining_quota_and_exhaustion(self) -> None:
        allowed = evaluate_rate_limit_request(
            {"subject_id": "user-1"},
            {"used": 3, "reset_epoch": 1000},
            {"limit": 5},
        )
        exhausted = evaluate_rate_limit_request(
            {"subject_id": "user-1"},
            {"used": 5, "reset_epoch": 1000},
            {"limit": 5},
        )

        self.assertTrue(allowed.allowed)
        self.assertEqual(allowed.remaining, 1)
        self.assertFalse(exhausted.allowed)
        self.assertEqual(exhausted.reason, "quota_exhausted")
        self.assertTrue(allowed.receipt_hash.startswith("rate-limit:"))

    def test_plan_tool_invocation_blocks_forbidden_args_and_missing_scopes(self) -> None:
        allowed = plan_tool_invocation(
            {"tool_name": "search_registry", "args": {"query": "webhook"}, "actor_scopes": ["registry:read"]},
            {"allowed_tools": ["search_registry"], "required_args": ["query"], "required_scopes": ["registry:read"]},
        )
        blocked = plan_tool_invocation(
            {"tool_name": "search_registry", "args": {"query": "x", "raw_secret": "s"}, "actor_scopes": []},
            {
                "allowed_tools": ["search_registry"],
                "required_args": ["query"],
                "required_scopes": ["registry:read"],
                "forbidden_args": ["raw_secret"],
            },
        )

        self.assertTrue(allowed.allowed)
        self.assertTrue(allowed.audit_key.startswith("tool-call:"))
        self.assertFalse(blocked.allowed)
        self.assertIn("forbidden_arg:raw_secret", blocked.blockers)
        self.assertIn("missing_scope:registry:read", blocked.blockers)

    def test_evaluate_workflow_step_transition_emits_event_and_blocks_duplicates(self) -> None:
        transitioned = evaluate_workflow_step_transition(
            {"current_step": "review"},
            {"action": "approve", "approver": "user-1"},
            {
                "transitions": {"review": {"approve": "approved"}},
                "required_input_fields": ["approver"],
            },
        )
        duplicate = evaluate_workflow_step_transition(
            {"current_step": "review", "completed_transition_keys": ["review:approve"]},
            {"action": "approve", "approver": "user-1"},
            {
                "transitions": {"review": {"approve": "approved"}},
                "required_input_fields": ["approver"],
            },
        )

        self.assertTrue(transitioned.transitioned)
        self.assertEqual(transitioned.next_step, "approved")
        self.assertEqual(transitioned.emitted_events[0]["event_type"], "workflow.approved")
        self.assertFalse(duplicate.transitioned)
        self.assertIn("duplicate_transition", duplicate.blockers)
        self.assertTrue(transitioned.receipt_hash.startswith("workflow-step:"))

    def test_plan_event_publication_validates_topic_partition_and_payload(self) -> None:
        receipt = plan_event_publication(
            {"event_type": "invoice.paid", "payload": {"account_id": "acct-1", "amount": 10}},
            {
                "topic": "billing.events",
                "partition_field": "account_id",
                "allowed_event_types": ["invoice.paid"],
                "required_payload_fields": ["account_id"],
            },
        )
        blocked = plan_event_publication(
            {"event_type": "invoice.failed", "payload": {}},
            {"topic": "billing.events", "allowed_event_types": ["invoice.paid"], "required_payload_fields": ["account_id"]},
        )

        self.assertTrue(receipt.publishable)
        self.assertEqual(receipt.partition_key, "acct-1")
        self.assertTrue(receipt.idempotency_key.startswith("publish-event:"))
        self.assertFalse(blocked.publishable)
        self.assertIn("event_type_not_allowed", blocked.blockers)
        self.assertIn("missing_partition_key", blocked.blockers)

    def test_evaluate_domain_event_handler_emits_commands_and_blocks_duplicates(self) -> None:
        receipt = evaluate_domain_event_handler(
            {"event_id": "evt-1", "event_type": "invoice.paid", "payload": {"invoice_id": "inv-1"}},
            {
                "handler_name": "billing_paid",
                "accepted_event_types": ["invoice.paid"],
                "required_payload_fields": ["invoice_id"],
                "command_templates": [{"command_type": "mark_paid", "field_map": {"invoice_id": "invoice_id"}}],
            },
        )
        duplicate = evaluate_domain_event_handler(
            {"event_id": "evt-1", "event_type": "invoice.paid", "payload": {"invoice_id": "inv-1"}},
            {"accepted_event_types": ["invoice.paid"], "handled_event_ids": ["evt-1"]},
        )

        self.assertTrue(receipt.handled)
        self.assertEqual(receipt.emitted_commands[0]["command_type"], "mark_paid")
        self.assertFalse(duplicate.handled)
        self.assertIn("duplicate_event", duplicate.blockers)
        self.assertTrue(receipt.receipt_hash.startswith("event-handler:"))

    def test_plan_sdk_client_request_adds_idempotency_and_blocks_paths(self) -> None:
        receipt = plan_sdk_client_request(
            {"method": "POST", "path": "/v1/customers", "body": {"email": "a@example.com"}},
            {
                "allowed_methods": ["GET", "POST"],
                "allowed_path_prefixes": ["/v1/"],
                "required_body_fields": ["email"],
                "require_idempotency_key": True,
                "retry_policy": {"max_attempts": 2},
            },
        )
        blocked = plan_sdk_client_request(
            {"method": "DELETE", "path": "/internal/secret", "body": {}},
            {"allowed_methods": ["GET", "POST"], "allowed_path_prefixes": ["/v1/"], "required_body_fields": ["email"]},
        )

        self.assertTrue(receipt.ready)
        self.assertIn("Idempotency-Key", receipt.headers)
        self.assertEqual(receipt.retry_policy["max_attempts"], 2)
        self.assertFalse(blocked.ready)
        self.assertIn("method_not_allowed", blocked.blockers)
        self.assertIn("path_not_allowed", blocked.blockers)

    def test_plan_terraform_module_enforces_variables_resource_types_and_tags(self) -> None:
        receipt = plan_terraform_module(
            {
                "module_name": "storage",
                "variables": {"environment": "prod"},
                "resources": [{"type": "aws_s3_bucket", "name": "logs", "tags": {"owner": "platform"}}],
            },
            {"required_variables": ["environment"], "allowed_resource_types": ["aws_s3_bucket"], "require_tags": True},
        )
        blocked = plan_terraform_module(
            {"module_name": "storage", "variables": {}, "resources": [{"type": "aws_iam_user"}]},
            {"required_variables": ["environment"], "allowed_resource_types": ["aws_s3_bucket"], "require_tags": True},
        )

        self.assertTrue(receipt.ready)
        self.assertTrue(receipt.plan_hash.startswith("terraform-module:"))
        self.assertFalse(blocked.ready)
        self.assertIn("missing_variable:environment", blocked.blockers)
        self.assertIn("resource_type_not_allowed:aws_iam_user", blocked.blockers)

    def test_plan_github_action_workflow_checks_triggers_permissions_and_pinned_actions(self) -> None:
        receipt = plan_github_action_workflow(
            {
                "name": "ci",
                "triggers": ["pull_request"],
                "jobs": [{"runs_on": "ubuntu-latest", "permissions": {"contents": "read"}, "steps": [{"uses": "actions/checkout@v4"}]}],
            },
            {"allowed_triggers": ["pull_request"], "require_permissions": True, "forbid_unpinned_actions": True},
        )
        blocked = plan_github_action_workflow(
            {
                "name": "ci",
                "triggers": ["schedule"],
                "jobs": [{"runs_on": "", "steps": [{"uses": "actions/checkout"}]}],
            },
            {"allowed_triggers": ["pull_request"], "require_permissions": True, "forbid_unpinned_actions": True},
        )

        self.assertTrue(receipt.ready)
        self.assertTrue(receipt.workflow_hash.startswith("github-action:"))
        self.assertFalse(blocked.ready)
        self.assertIn("trigger_not_allowed:schedule", blocked.blockers)
        self.assertIn("job_1_step_1_unpinned_action", blocked.blockers)

    def test_evaluate_data_quality_rule_reports_missing_and_duplicate_rows(self) -> None:
        receipt = evaluate_data_quality_rule(
            [
                {"email": "a@example.com", "account_id": "a"},
                {"email": "", "account_id": "b"},
                {"email": "a@example.com", "account_id": "c"},
            ],
            {"rule_name": "customer_email_quality", "required_fields": ["email"], "unique_fields": ["email"]},
        )

        self.assertFalse(receipt.passed)
        self.assertEqual(receipt.failed_rows, (1, 2))
        self.assertEqual(receipt.failure_reason, "duplicate_key")
        self.assertTrue(receipt.receipt_hash.startswith("data-quality:"))

    def test_plan_vector_index_build_counts_chunks_and_blocks_bad_dimensions(self) -> None:
        receipt = plan_vector_index_build(
            [{"id": "doc-1", "text": "a" * 1200}, {"id": "doc-2", "text": "short"}],
            {"embedding_model": "text-embedding-3-small", "dimension": 1536, "chunk_chars": 500, "min_dimension": 128},
        )
        blocked = plan_vector_index_build(
            [{"id": "doc-1", "text": ""}],
            {"embedding_model": "", "dimension": 8, "chunk_chars": 500, "min_dimension": 128},
        )

        self.assertTrue(receipt.ready)
        self.assertEqual(receipt.chunk_count, 4)
        self.assertTrue(receipt.index_hash.startswith("vector-index:"))
        self.assertFalse(blocked.ready)
        self.assertIn("missing_embedding_model", blocked.blockers)
        self.assertIn("embedding_dimension_too_small", blocked.blockers)

    def test_compile_compliance_evidence_workflow_reports_missing_evidence(self) -> None:
        receipt = compile_compliance_evidence_workflow(
            {
                "control_id": "SOC2-CC6.1",
                "evidence": [
                    {"type": "access_review", "ref": "evidence/access-review.json"},
                    {"type": "policy", "ref": "docs/policy.md"},
                ],
            },
            {"required_evidence_types": ["access_review", "policy"], "review_required": True},
        )
        blocked = compile_compliance_evidence_workflow(
            {"control_id": "SOC2-CC6.1", "evidence": [{"type": "policy", "ref": "docs/policy.md"}]},
            {"required_evidence_types": ["access_review", "policy"], "review_required": True},
        )

        self.assertTrue(receipt.ready)
        self.assertEqual(receipt.evidence_refs, ("evidence/access-review.json", "docs/policy.md"))
        self.assertTrue(receipt.review_required)
        self.assertFalse(blocked.ready)
        self.assertEqual(blocked.missing_evidence, ("access_review",))
        self.assertTrue(receipt.receipt_hash.startswith("compliance-evidence:"))

    def test_plan_graphql_resolver_checks_fields_and_scopes(self) -> None:
        receipt = plan_graphql_resolver(
            {"operation_name": "customer", "selected_fields": ["id", "name"], "actor_scopes": ["customer:read"]},
            {
                "resolver_name": "customerResolver",
                "allowed_operations": ["customer"],
                "allowed_fields": ["id", "name"],
                "required_scopes": ["customer:read"],
            },
        )
        blocked = plan_graphql_resolver(
            {"operation_name": "customer", "selected_fields": ["id", "secret"], "actor_scopes": []},
            {
                "allowed_operations": ["customer"],
                "allowed_fields": ["id", "name"],
                "required_scopes": ["customer:read"],
            },
        )

        self.assertTrue(receipt.ready)
        self.assertEqual(receipt.resolver_name, "customerResolver")
        self.assertFalse(blocked.ready)
        self.assertIn("field_not_allowed:secret", blocked.blockers)
        self.assertIn("missing_scope:customer:read", blocked.blockers)

    def test_plan_grpc_method_call_checks_metadata_and_message_fields(self) -> None:
        receipt = plan_grpc_method_call(
            {"service": "BillingService", "method": "Authorize", "message": {"account_id": "acct-1"}, "metadata": {"authorization": "Bearer t"}},
            {"allowed_methods": ["Authorize"], "required_message_fields": ["account_id"], "required_metadata": ["authorization"]},
        )
        blocked = plan_grpc_method_call(
            {"service": "BillingService", "method": "Delete", "message": {}, "metadata": {}},
            {"allowed_methods": ["Authorize"], "required_message_fields": ["account_id"], "required_metadata": ["authorization"]},
        )

        self.assertTrue(receipt.ready)
        self.assertTrue(receipt.receipt_hash.startswith("grpc-method:"))
        self.assertFalse(blocked.ready)
        self.assertIn("method_not_allowed", blocked.blockers)
        self.assertIn("missing_message_field:account_id", blocked.blockers)

    def test_plan_sql_view_and_procedure_block_unsafe_contracts(self) -> None:
        view = plan_sql_view(
            {"view_name": "active_customers", "source_tables": ["customers"], "columns": ["id", "email"], "where": "active = true"},
            {"allowed_source_tables": ["customers"], "forbid_select_star": True},
        )
        bad_view = plan_sql_view(
            {"view_name": "all_customers", "source_tables": ["private_customers"], "columns": ["*"]},
            {"allowed_source_tables": ["customers"], "forbid_select_star": True},
        )
        proc = plan_sql_procedure(
            {"procedure_name": "get_customer", "parameters": ["customer_id"], "statements": ["SELECT * FROM customers WHERE id = customer_id"]},
            {"required_parameters": ["customer_id"], "readonly_only": True},
        )
        bad_proc = plan_sql_procedure(
            {"procedure_name": "delete_customer", "parameters": ["customer_id"], "statements": ["DELETE FROM customers WHERE id = customer_id"]},
            {"required_parameters": ["customer_id"], "readonly_only": True},
        )

        self.assertTrue(view.ready)
        self.assertIn("CREATE VIEW active_customers", view.sql)
        self.assertFalse(bad_view.ready)
        self.assertIn("source_table_not_allowed:private_customers", bad_view.blockers)
        self.assertIn("select_star_forbidden", bad_view.blockers)
        self.assertTrue(proc.ready)
        self.assertFalse(bad_proc.ready)
        self.assertIn("statement_1_mutates_data", bad_proc.blockers)

    def test_plan_etl_pipeline_and_elt_model_require_checkpoints_tests_and_dependencies(self) -> None:
        etl = plan_etl_pipeline(
            {"source": "salesforce", "target": "warehouse.customers", "transforms": ["normalize_email"], "checkpoint_key": "updated_at"},
            {"require_checkpoint": True, "require_transforms": True},
        )
        bad_etl = plan_etl_pipeline({"source": "salesforce", "target": "warehouse.customers"}, {"require_checkpoint": True, "require_transforms": True})
        elt = plan_elt_model(
            {"model_name": "customer_mart", "dependencies": ["stg_customers"], "materialization": "table", "tests": ["not_null:id"]},
            {"allowed_materializations": ["view", "table"], "require_tests": True},
        )
        bad_elt = plan_elt_model({"model_name": "customer_mart", "materialization": "incremental"}, {"allowed_materializations": ["view"], "require_tests": True})

        self.assertTrue(etl.ready)
        self.assertEqual(etl.steps, ("extract", "transform:normalize_email", "load"))
        self.assertFalse(bad_etl.ready)
        self.assertIn("missing_checkpoint_key", bad_etl.blockers)
        self.assertTrue(elt.ready)
        self.assertFalse(bad_elt.ready)
        self.assertIn("missing_dependencies", bad_elt.blockers)
        self.assertIn("materialization_not_allowed", bad_elt.blockers)

    def test_evaluate_alert_rule_and_compile_runbook_plan_require_routes_and_sections(self) -> None:
        alert = evaluate_alert_rule(
            {"metric": "error_rate", "value": 0.12},
            {"alert_name": "High error rate", "metric": "error_rate", "threshold": 0.05, "operator": "gt", "routes": ["pagerduty"], "severity": "critical"},
        )
        bad_alert = evaluate_alert_rule({"metric": "error_rate", "value": 0.12}, {"alert_name": "High error rate", "threshold": 0})
        runbook = compile_runbook_plan(
            {"incident_type": "api_outage"},
            {
                "steps": ["check health", "roll back"],
                "escalation_targets": ["platform-oncall"],
                "rollback": "deploy previous image",
                "verification": "health checks pass",
                "required_sections": ["steps", "escalation_targets", "rollback", "verification"],
            },
        )
        bad_runbook = compile_runbook_plan({"incident_type": "api_outage"}, {"required_sections": ["steps", "rollback"]})

        self.assertTrue(alert.ready)
        self.assertIn("-> True", alert.condition)
        self.assertFalse(bad_alert.ready)
        self.assertIn("missing_threshold", bad_alert.blockers)
        self.assertTrue(runbook.ready)
        self.assertFalse(bad_runbook.ready)
        self.assertEqual(bad_runbook.missing_sections, ("steps", "rollback"))

    def test_plan_incident_triage_escalation_and_status_page_update_gate_incident_response(self) -> None:
        triage = plan_incident_triage(
            {
                "incident_id": "inc-001",
                "summary": "Checkout API error spike",
                "severity": "sev1",
                "affected_services": ["checkout-api"],
                "priority": "p0",
                "customer_impact": "checkout failures",
                "owner": "payments-platform",
                "runbook_ref": "runbook://checkout-api",
                "detection_age_seconds": 120,
            },
            {
                "allowed_severities": ["sev1", "sev2", "sev3"],
                "require_affected_services": True,
                "require_customer_impact": True,
                "require_owner": True,
                "require_runbook_ref": True,
                "max_detection_age_seconds": 300,
            },
        )
        bad_triage = plan_incident_triage(
            {"severity": "sev9", "detection_age_seconds": 900},
            {
                "allowed_severities": ["sev1"],
                "require_affected_services": True,
                "require_customer_impact": True,
                "require_owner": True,
                "require_runbook_ref": True,
                "max_detection_age_seconds": 300,
            },
        )
        escalation = plan_oncall_escalation(
            {
                "incident_id": "inc-001",
                "primary_oncall": "alice",
                "backup_oncall": "bob",
                "escalation_targets": ["payments-manager"],
                "channels": ["pagerduty", "slack"],
                "ack_minutes": 5,
                "pager_receipt": "pd-123",
            },
            {
                "allowed_channels": ["pagerduty", "slack"],
                "require_escalation_targets": True,
                "require_channels": True,
                "require_backup_oncall": True,
                "max_ack_minutes": 10,
                "require_pager_receipt": True,
            },
        )
        bad_escalation = plan_oncall_escalation(
            {"incident_id": "inc-002", "channels": ["sms"], "ack_minutes": 30},
            {
                "allowed_channels": ["pagerduty"],
                "require_escalation_targets": True,
                "require_channels": True,
                "require_backup_oncall": True,
                "max_ack_minutes": 10,
                "require_pager_receipt": True,
            },
        )
        update = plan_status_page_update(
            {
                "incident_id": "inc-001",
                "status": "investigating",
                "components": ["checkout"],
                "audiences": ["customers"],
                "message": "We are investigating elevated checkout errors.",
                "impact_summary": "Some checkout requests fail.",
                "next_update_eta": "2026-07-01T18:30:00Z",
                "approval": "comms-lead",
                "customer_visible": True,
            },
            {
                "allowed_statuses": ["investigating", "identified", "monitoring", "resolved"],
                "require_components": True,
                "require_audience": True,
                "require_message": True,
                "require_impact_summary": True,
                "require_next_update_eta": True,
                "require_approval": True,
                "require_customer_visible": True,
            },
        )
        bad_update = plan_status_page_update(
            {"status": "internal-only", "components": []},
            {
                "allowed_statuses": ["investigating"],
                "require_components": True,
                "require_audience": True,
                "require_message": True,
                "require_impact_summary": True,
                "require_next_update_eta": True,
                "require_approval": True,
                "require_customer_visible": True,
            },
        )

        self.assertTrue(triage.ready)
        self.assertTrue(triage.triage_hash.startswith("incident-triage:"))
        self.assertFalse(bad_triage.ready)
        self.assertIn("missing_incident_id", bad_triage.blockers)
        self.assertIn("missing_summary", bad_triage.blockers)
        self.assertIn("severity_not_allowed:sev9", bad_triage.blockers)
        self.assertIn("missing_affected_services", bad_triage.blockers)
        self.assertIn("missing_customer_impact", bad_triage.blockers)
        self.assertIn("missing_owner", bad_triage.blockers)
        self.assertIn("missing_runbook_ref", bad_triage.blockers)
        self.assertIn("detection_age_exceeds_policy", bad_triage.blockers)
        self.assertTrue(escalation.ready)
        self.assertEqual(escalation.channels, ("pagerduty", "slack"))
        self.assertFalse(bad_escalation.ready)
        self.assertIn("missing_primary_oncall", bad_escalation.blockers)
        self.assertIn("missing_escalation_targets", bad_escalation.blockers)
        self.assertIn("channel_not_allowed:sms", bad_escalation.blockers)
        self.assertIn("missing_backup_oncall", bad_escalation.blockers)
        self.assertIn("ack_minutes_exceeds_policy", bad_escalation.blockers)
        self.assertIn("missing_pager_receipt", bad_escalation.blockers)
        self.assertTrue(update.ready)
        self.assertTrue(update.update_hash.startswith("status-page-update:"))
        self.assertFalse(bad_update.ready)
        self.assertIn("missing_incident_id", bad_update.blockers)
        self.assertIn("status_not_allowed:internal-only", bad_update.blockers)
        self.assertIn("missing_components", bad_update.blockers)
        self.assertIn("missing_audience", bad_update.blockers)
        self.assertIn("missing_message", bad_update.blockers)
        self.assertIn("missing_impact_summary", bad_update.blockers)
        self.assertIn("missing_next_update_eta", bad_update.blockers)
        self.assertIn("missing_approval", bad_update.blockers)
        self.assertIn("missing_customer_visible_flag", bad_update.blockers)

    def test_plan_maintenance_window_and_postmortem_actions_gate_operational_followthrough(self) -> None:
        maintenance = plan_maintenance_window(
            {
                "window_id": "maint-001",
                "affected_services": ["checkout-api"],
                "start_epoch": 1782930000,
                "end_epoch": 1782931800,
                "notification_channels": ["status-page", "email"],
                "rollback_plan": "restore previous image",
                "owner": "payments-platform",
                "change_freeze": True,
                "freeze_exception": "SEC-9",
            },
            {
                "allowed_services": ["checkout-api"],
                "require_affected_services": True,
                "max_duration_seconds": 3600,
                "require_notification_channels": True,
                "require_rollback_plan": True,
                "require_owner": True,
                "require_freeze_exception": True,
            },
        )
        bad_maintenance = plan_maintenance_window(
            {"window_id": "", "affected_services": ["unknown"], "start_epoch": 20, "end_epoch": 10, "change_freeze": True},
            {
                "allowed_services": ["checkout-api"],
                "require_affected_services": True,
                "max_duration_seconds": 5,
                "require_notification_channels": True,
                "require_rollback_plan": True,
                "require_owner": True,
                "require_freeze_exception": True,
            },
        )
        postmortem = plan_postmortem_action_items(
            {
                "incident_id": "inc-001",
                "root_cause": "connection pool exhaustion",
                "timeline": ["18:00 alert", "18:05 rollback"],
                "action_items": [
                    {"action_id": "pm-1", "owner": "alice", "due_date": "2026-07-08", "prevention_type": "capacity", "verification_plan": "load test"},
                    {"action_id": "pm-2", "owner": "bob", "due_date": "2026-07-09", "prevention_type": "alerting", "verification_plan": "alert drill"},
                ],
            },
            {
                "require_root_cause": True,
                "require_timeline": True,
                "max_action_items": 5,
                "require_due_date": True,
                "require_prevention_type": True,
                "require_verification_plan": True,
                "require_owner_diversity": True,
                "min_owners": 2,
            },
        )
        bad_postmortem = plan_postmortem_action_items(
            {"incident_id": "", "action_items": [{"action_id": "pm-1", "owner": "alice"}]},
            {
                "require_root_cause": True,
                "require_timeline": True,
                "max_action_items": 0,
                "require_due_date": True,
                "require_prevention_type": True,
                "require_verification_plan": True,
                "require_owner_diversity": True,
                "min_owners": 2,
            },
        )

        self.assertTrue(maintenance.ready)
        self.assertTrue(maintenance.window_hash.startswith("maintenance-window:"))
        self.assertFalse(bad_maintenance.ready)
        self.assertIn("missing_window_id", bad_maintenance.blockers)
        self.assertIn("invalid_window_range", bad_maintenance.blockers)
        self.assertIn("service_not_allowed:unknown", bad_maintenance.blockers)
        self.assertIn("missing_notification_channels", bad_maintenance.blockers)
        self.assertIn("missing_rollback_plan", bad_maintenance.blockers)
        self.assertIn("missing_owner", bad_maintenance.blockers)
        self.assertIn("missing_freeze_exception", bad_maintenance.blockers)
        self.assertTrue(postmortem.ready)
        self.assertEqual(postmortem.action_ids, ("pm-1", "pm-2"))
        self.assertTrue(postmortem.action_hash.startswith("postmortem-actions:"))
        self.assertFalse(bad_postmortem.ready)
        self.assertIn("missing_incident_id", bad_postmortem.blockers)
        self.assertIn("missing_root_cause", bad_postmortem.blockers)
        self.assertIn("missing_timeline", bad_postmortem.blockers)
        self.assertIn("action_pm-1_missing_due_date", bad_postmortem.blockers)
        self.assertIn("action_pm-1_missing_prevention_type", bad_postmortem.blockers)
        self.assertIn("action_pm-1_missing_verification_plan", bad_postmortem.blockers)
        self.assertIn("owner_diversity_below_policy", bad_postmortem.blockers)

    def test_build_test_fixture_redacts_pii_and_plan_mock_server_checks_routes(self) -> None:
        fixture = build_test_fixture(
            {"fixture_name": "customers", "row_count": 2, "pii_fields": ["email"]},
            {"fields": {"id": "integer", "email": "string", "active": "boolean"}, "required_fields": ["id", "email"]},
        )
        bad_fixture = build_test_fixture({"fixture_name": "bad", "row_count": 1}, {"fields": {"id": "integer"}, "required_fields": ["email"]})
        mock = plan_mock_server(
            {"routes": [{"method": "GET", "path": "/customers", "response": {"status": 200, "body": []}}]},
            {"base_url": "http://127.0.0.1:9000"},
        )
        bad_mock = plan_mock_server({"routes": [{"method": "GET", "path": "customers"}]}, {})

        self.assertTrue(fixture.ready)
        self.assertEqual(fixture.rows[0]["email"], "***redacted***")
        self.assertFalse(bad_fixture.ready)
        self.assertIn("required_field_not_in_schema:email", bad_fixture.blockers)
        self.assertTrue(mock.ready)
        self.assertFalse(bad_mock.ready)
        self.assertIn("route_1_invalid_path", bad_mock.blockers)
        self.assertIn("route_1_missing_response", bad_mock.blockers)

    def test_evaluate_policy_rule_checks_actions_scopes_and_context(self) -> None:
        receipt = evaluate_policy_rule(
            {"subject_id": "user-1", "action": "invoice.approve", "actor_scopes": ["invoice:write"], "tenant_id": "acme"},
            {"allowed_actions": ["invoice.approve"], "required_scopes": ["invoice:write"], "required_context_fields": ["tenant_id"]},
        )
        blocked = evaluate_policy_rule(
            {"subject_id": "user-2", "action": "invoice.delete", "actor_scopes": [], "tenant_id": "suspended"},
            {
                "allowed_actions": ["invoice.approve"],
                "required_scopes": ["invoice:write"],
                "required_context_fields": ["tenant_id"],
                "deny_if": {"tenant_id": "suspended"},
            },
        )

        self.assertTrue(receipt.allowed)
        self.assertEqual(receipt.decision, "allow")
        self.assertFalse(blocked.allowed)
        self.assertIn("action_not_allowed", blocked.reason_codes)
        self.assertIn("missing_scope:invoice:write", blocked.reason_codes)
        self.assertIn("deny_if:tenant_id", blocked.reason_codes)

    def test_plan_shell_script_and_kubernetes_controller_gate_runtime_plans(self) -> None:
        script = plan_shell_script(
            {"argv": ["python3", "scripts/check.py"], "env": {"APP_ENV": "test"}},
            {"allowed_commands": ["python3"], "required_env": ["APP_ENV"], "forbid_shell_metacharacters": True},
        )
        bad_script = plan_shell_script(
            {"argv": ["bash", "deploy.sh;curl"], "env": {}},
            {"allowed_commands": ["python3"], "required_env": ["APP_ENV"], "forbid_shell_metacharacters": True},
        )
        controller = plan_kubernetes_controller(
            {
                "controller_name": "invoice-reconciler",
                "watched_kinds": ["InvoiceImport"],
                "reconcile_steps": ["load desired state", "compare observed", "emit status"],
                "finalizer": "invoices.teleon/finalizer",
                "leader_election": True,
            },
            {"allowed_watched_kinds": ["InvoiceImport"], "require_finalizer": True, "require_leader_election": True},
        )
        bad_controller = plan_kubernetes_controller(
            {"controller_name": "bad", "watched_kinds": ["Pod"], "reconcile_steps": []},
            {"allowed_watched_kinds": ["InvoiceImport"], "require_finalizer": True},
        )

        self.assertTrue(script.ready)
        self.assertFalse(bad_script.ready)
        self.assertIn("command_not_allowed:bash", bad_script.blockers)
        self.assertIn("missing_env:APP_ENV", bad_script.blockers)
        self.assertTrue(controller.ready)
        self.assertFalse(bad_controller.ready)
        self.assertIn("watched_kind_not_allowed:Pod", bad_controller.blockers)
        self.assertIn("missing_reconcile_steps", bad_controller.blockers)

    def test_plan_workflow_group_and_ui_surfaces_require_edges_states_and_boundaries(self) -> None:
        workflow = plan_workflow_group(
            {
                "workflow_name": "invoice-approval",
                "steps": ["submitted", "review", "approved"],
                "edges": [{"from": "submitted", "to": "review"}, {"from": "review", "to": "approved"}],
            },
            {"required_steps": ["submitted", "approved"], "require_edges": True},
        )
        bad_workflow = plan_workflow_group(
            {"workflow_name": "bad", "steps": ["submitted"], "edges": [{"from": "submitted", "to": "approved"}]},
            {"required_steps": ["submitted", "approved"], "require_edges": True},
        )
        component = plan_ui_component(
            {
                "component_name": "InvoiceApprovalPanel",
                "props": ["invoice", "onApprove"],
                "states": ["loading", "empty", "error", "ready"],
                "accessible_name": "Invoice approval",
            },
            {"required_props": ["invoice"], "required_states": ["loading", "empty", "error"], "require_accessible_name": True},
        )
        route = plan_ui_route(
            {
                "path": "/app/invoices/:id",
                "data_dependencies": ["invoiceDetail"],
                "components": ["ErrorBoundary", "InvoiceApprovalPanel"],
            },
            {"allowed_path_prefixes": ["/app"], "require_data_dependencies": True, "required_components": ["InvoiceApprovalPanel"], "require_error_boundary": True},
        )
        bad_component = plan_ui_component({"component_name": "Panel", "props": ["invoice"], "states": ["ready"]}, {"required_states": ["error"], "require_accessible_name": True})
        bad_route = plan_ui_route({"path": "app/invoices", "components": ["InvoiceApprovalPanel"]}, {"allowed_path_prefixes": ["/app"], "require_error_boundary": True})

        self.assertTrue(workflow.ready)
        self.assertFalse(bad_workflow.ready)
        self.assertIn("missing_step:approved", bad_workflow.blockers)
        self.assertIn("edge_1_references_unknown_step", bad_workflow.blockers)
        self.assertTrue(component.ready)
        self.assertTrue(route.ready)
        self.assertFalse(bad_component.ready)
        self.assertIn("missing_accessible_name", bad_component.blockers)
        self.assertFalse(bad_route.ready)
        self.assertIn("route_path_must_start_with_slash", bad_route.blockers)
        self.assertIn("missing_error_boundary", bad_route.blockers)

    def test_plan_ui_api_binding_form_validation_and_table_state_gate_frontend_edges(self) -> None:
        binding = plan_ui_api_binding(
            {
                "component_name": "InvoiceApprovalPanel",
                "api_operations": [
                    {"operation_id": "getInvoice", "method": "GET", "path": "/api/invoices/{id}", "response_schema": {"type": "object"}},
                    {
                        "operation_id": "approveInvoice",
                        "method": "POST",
                        "path": "/api/invoices/{id}/approve",
                        "request_schema": {"type": "object"},
                        "response_schema": {"type": "object"},
                    },
                ],
                "data_dependencies": ["getInvoice", "approveInvoice"],
                "mutation_handlers": ["approveInvoice"],
                "loading_states": ["initial"],
                "error_states": ["inline"],
                "auth_scopes": ["invoice:read", "invoice:write"],
            },
            {
                "allowed_methods": ["GET", "POST"],
                "required_operations": ["getInvoice", "approveInvoice"],
                "require_response_schema": True,
                "require_request_schema_for_mutations": True,
                "require_data_dependency_per_operation": True,
                "require_mutation_handlers": True,
                "require_loading_state": True,
                "require_error_state": True,
                "required_auth_scopes": ["invoice:write"],
            },
        )
        bad_binding = plan_ui_api_binding(
            {"api_operations": [{"method": "POST", "path": "api/invoices"}]},
            {
                "allowed_methods": ["GET", "POST"],
                "required_operations": ["getInvoice"],
                "require_response_schema": True,
                "require_request_schema_for_mutations": True,
                "require_loading_state": True,
                "require_error_state": True,
                "required_auth_scopes": ["invoice:write"],
            },
        )
        form = plan_ui_form_validation(
            {
                "form_name": "InvoiceAdjustmentForm",
                "fields": [
                    {"name": "email", "validators": ["required", "email"], "accessible_label": "Email"},
                    {"name": "amount", "validators": ["required", "number"], "accessible_label": "Amount"},
                ],
                "submit_action": "submitAdjustment",
                "client_validation": True,
                "server_validation": True,
                "error_summary": True,
            },
            {
                "required_fields": ["email", "amount"],
                "required_validators_by_field": {"email": ["required", "email"], "amount": ["required", "number"]},
                "require_submit_action": True,
                "require_client_validation": True,
                "require_server_validation": True,
                "require_error_summary": True,
                "require_accessible_labels": True,
            },
        )
        bad_form = plan_ui_form_validation(
            {"form_name": "InvoiceAdjustmentForm", "fields": [{"name": "email", "validators": ["required"]}]},
            {
                "required_fields": ["email", "amount"],
                "required_validators_by_field": {"email": ["required", "email"]},
                "require_submit_action": True,
                "require_client_validation": True,
                "require_server_validation": True,
                "require_error_summary": True,
                "require_accessible_labels": True,
            },
        )
        table = plan_ui_table_state(
            {
                "table_name": "InvoiceTable",
                "columns": ["id", "email", "status"],
                "row_key": "id",
                "pagination": True,
                "sorting": True,
                "filters": True,
                "loading_state": True,
                "empty_state": True,
                "error_state": True,
                "selection_mode": "multi",
            },
            {
                "required_columns": ["id", "status"],
                "require_row_key": True,
                "require_pagination": True,
                "require_sorting": True,
                "require_filters": True,
                "require_loading_state": True,
                "require_empty_state": True,
                "require_error_state": True,
                "require_selection_mode": True,
            },
        )
        bad_table = plan_ui_table_state(
            {"table_name": "InvoiceTable", "columns": ["id"]},
            {
                "required_columns": ["id", "status"],
                "require_row_key": True,
                "require_pagination": True,
                "require_sorting": True,
                "require_filters": True,
                "require_loading_state": True,
                "require_empty_state": True,
                "require_error_state": True,
                "require_selection_mode": True,
            },
        )

        self.assertTrue(binding.ready)
        self.assertEqual(binding.mutation_operations, ("approveInvoice",))
        self.assertTrue(binding.binding_hash.startswith("ui-api-binding:"))
        self.assertFalse(bad_binding.ready)
        self.assertIn("missing_component_name", bad_binding.blockers)
        self.assertIn("operation_1_missing_operation_id", bad_binding.blockers)
        self.assertIn("operation_1_missing_path", bad_binding.blockers)
        self.assertIn("operation_1_missing_response_schema", bad_binding.blockers)
        self.assertIn("operation_1_missing_request_schema", bad_binding.blockers)
        self.assertIn("missing_required_operation:getInvoice", bad_binding.blockers)
        self.assertIn("missing_loading_state", bad_binding.blockers)
        self.assertIn("missing_error_state", bad_binding.blockers)
        self.assertIn("missing_auth_scope:invoice:write", bad_binding.blockers)
        self.assertTrue(form.ready)
        self.assertEqual(form.field_names, ("email", "amount"))
        self.assertFalse(bad_form.ready)
        self.assertIn("missing_required_field:amount", bad_form.blockers)
        self.assertIn("missing_validator:email:email", bad_form.blockers)
        self.assertIn("missing_submit_action", bad_form.blockers)
        self.assertIn("missing_client_validation", bad_form.blockers)
        self.assertIn("missing_server_validation", bad_form.blockers)
        self.assertIn("missing_error_summary", bad_form.blockers)
        self.assertIn("field_email_missing_accessible_label", bad_form.blockers)
        self.assertTrue(table.ready)
        self.assertIn("pagination", table.state_controls)
        self.assertFalse(bad_table.ready)
        self.assertIn("missing_column:status", bad_table.blockers)
        self.assertIn("missing_row_key", bad_table.blockers)
        self.assertIn("missing_pagination", bad_table.blockers)
        self.assertIn("missing_sorting", bad_table.blockers)
        self.assertIn("missing_filters", bad_table.blockers)
        self.assertIn("missing_loading_state", bad_table.blockers)
        self.assertIn("missing_empty_state", bad_table.blockers)
        self.assertIn("missing_error_state", bad_table.blockers)
        self.assertIn("missing_selection_mode", bad_table.blockers)

    def test_plan_dashboard_filter_contract_and_ui_accessibility_interactions_gate_report_surfaces(self) -> None:
        dashboard = plan_dashboard_filter_contract(
            {
                "dashboard_name": "RevenueOpsDashboard",
                "filters": [
                    {"name": "date_range", "type": "date_range", "default": "last_30d"},
                    {"name": "region", "type": "multi_select", "default": []},
                ],
                "metrics": ["revenue", "churn"],
                "metric_filter_bindings": {"revenue": ["date_range", "region"], "churn": ["date_range"]},
                "reset_action": "clearFilters",
            },
            {
                "allowed_filter_types": ["date_range", "multi_select"],
                "required_filters": ["date_range"],
                "require_default_values": True,
                "require_metric_bindings": True,
                "require_reset_action": True,
            },
        )
        bad_dashboard = plan_dashboard_filter_contract(
            {
                "filters": [{"name": "region", "type": "text"}],
                "metrics": ["revenue"],
                "metric_filter_bindings": {"revenue": ["unknown"]},
            },
            {
                "allowed_filter_types": ["date_range", "multi_select"],
                "required_filters": ["date_range"],
                "require_default_values": True,
                "require_metric_bindings": True,
                "require_reset_action": True,
            },
        )
        accessibility = plan_ui_accessibility_interaction(
            {
                "surface_name": "InvoiceApprovalPanel",
                "interactions": [
                    {
                        "name": "approve_button",
                        "role": "button",
                        "accessible_name": "Approve invoice",
                        "keyboard_shortcut": "Enter",
                        "focus_state": "visible",
                        "touch_target": "44x44",
                    },
                    {
                        "name": "approval_status",
                        "role": "status",
                        "accessible_name": "Approval result",
                        "keyboard_path": "Tab",
                        "focus_state": "announced",
                        "touch_target": "44x44",
                    },
                ],
                "async_updates": True,
                "aria_live_region": "polite",
                "motion": True,
                "reduced_motion_toggle": True,
            },
            {
                "allowed_roles": ["button", "status"],
                "required_roles": ["button", "status"],
                "require_accessible_name": True,
                "require_keyboard_support": True,
                "require_focus_state": True,
                "require_touch_target": True,
                "require_aria_live_for_async": True,
                "require_reduced_motion_toggle": True,
            },
        )
        bad_accessibility = plan_ui_accessibility_interaction(
            {"interactions": [{"name": "animate", "role": "marquee"}], "async_updates": True, "motion": True},
            {
                "allowed_roles": ["button"],
                "required_roles": ["button"],
                "require_accessible_name": True,
                "require_keyboard_support": True,
                "require_focus_state": True,
                "require_touch_target": True,
                "require_aria_live_for_async": True,
                "require_reduced_motion_toggle": True,
            },
        )

        self.assertTrue(dashboard.ready)
        self.assertEqual(dashboard.filters, ("date_range", "region"))
        self.assertTrue(dashboard.contract_hash.startswith("dashboard-filter-contract:"))
        self.assertFalse(bad_dashboard.ready)
        self.assertIn("missing_dashboard_name", bad_dashboard.blockers)
        self.assertIn("filter_type_not_allowed:text", bad_dashboard.blockers)
        self.assertIn("filter_region_missing_default", bad_dashboard.blockers)
        self.assertIn("missing_filter:date_range", bad_dashboard.blockers)
        self.assertIn("metric_binding_unknown_filter:revenue:unknown", bad_dashboard.blockers)
        self.assertIn("missing_reset_action", bad_dashboard.blockers)
        self.assertTrue(accessibility.ready)
        self.assertEqual(accessibility.roles, ("button", "status"))
        self.assertTrue(accessibility.accessibility_hash.startswith("ui-accessibility-interaction:"))
        self.assertFalse(bad_accessibility.ready)
        self.assertIn("missing_surface_name", bad_accessibility.blockers)
        self.assertIn("role_not_allowed:marquee", bad_accessibility.blockers)
        self.assertIn("interaction_animate_missing_accessible_name", bad_accessibility.blockers)
        self.assertIn("interaction_animate_missing_keyboard_support", bad_accessibility.blockers)
        self.assertIn("interaction_animate_missing_focus_state", bad_accessibility.blockers)
        self.assertIn("interaction_animate_missing_touch_target", bad_accessibility.blockers)
        self.assertIn("missing_required_role:button", bad_accessibility.blockers)
        self.assertIn("missing_aria_live_region", bad_accessibility.blockers)
        self.assertIn("missing_reduced_motion_toggle", bad_accessibility.blockers)

    def test_plan_api_resource_group_and_microservice_bundle_gate_contract_surface(self) -> None:
        resource = plan_api_resource_group(
            {
                "resource_name": "invoice",
                "operations": ["list", "create", "read", "update", "archive"],
                "idempotent_operations": ["create", "update", "archive"],
                "auth": {"required": True},
            },
            {
                "required_operations": ["list", "create", "read", "update", "archive"],
                "require_auth": True,
                "require_idempotency_for_mutations": True,
            },
        )
        bad_resource = plan_api_resource_group(
            {"resource_name": "invoice", "operations": ["list", "create"], "auth": None},
            {"required_operations": ["list", "create", "read"], "require_auth": True, "require_idempotency_for_mutations": True},
        )
        service = plan_microservice_bundle(
            {
                "service_name": "billing-reconciliation",
                "endpoints": ["POST /reconcile"],
                "workers": ["payment-import-worker"],
                "data_stores": ["postgres.ledger"],
                "health_check": "/healthz",
                "telemetry": {"traces": True},
                "env": {"DATABASE_URL": "secret://db"},
            },
            {"require_callable_surface": True, "require_data_store": True, "require_health_check": True, "require_telemetry": True, "required_env": ["DATABASE_URL"]},
        )
        bad_service = plan_microservice_bundle(
            {"service_name": "billing-reconciliation", "endpoints": []},
            {"require_callable_surface": True, "require_data_store": True, "require_health_check": True, "require_telemetry": True},
        )

        self.assertTrue(resource.ready)
        self.assertFalse(bad_resource.ready)
        self.assertIn("missing_operation:read", bad_resource.blockers)
        self.assertIn("missing_auth", bad_resource.blockers)
        self.assertIn("missing_idempotency:create", bad_resource.blockers)
        self.assertTrue(service.ready)
        self.assertFalse(bad_service.ready)
        self.assertIn("missing_callable_surface", bad_service.blockers)
        self.assertIn("missing_data_store", bad_service.blockers)
        self.assertIn("missing_health_check", bad_service.blockers)

    def test_plan_service_boundary_and_surface_inventory_enforce_service_group_edges(self) -> None:
        boundary = plan_service_boundary_contract(
            {
                "service_name": "billing-service",
                "bounded_context": "billing",
                "owned_capabilities": ["invoice.write", "payment.reconcile"],
                "external_dependencies": ["customer-service"],
                "dependency_contracts": ["customer-service"],
                "owner_team": "payments-platform",
                "boundary_receipt": "boundary-1",
            },
            {
                "require_bounded_context": True,
                "require_owned_capabilities": True,
                "require_owner_team": True,
                "require_dependency_contracts": True,
                "forbid_shared_store_access": True,
                "require_boundary_receipt": True,
            },
        )
        bad_boundary = plan_service_boundary_contract(
            {"external_dependencies": ["ledger-service"], "shared_store_access": ["ledger_db"]},
            {
                "require_bounded_context": True,
                "require_owned_capabilities": True,
                "require_owner_team": True,
                "require_dependency_contracts": True,
                "forbid_shared_store_access": True,
                "require_boundary_receipt": True,
            },
        )
        inventory = plan_service_surface_inventory(
            {
                "service_name": "billing-service",
                "surfaces": [
                    {"name": "POST /v1/invoices", "kind": "api_endpoint", "visibility": "public", "auth": "oauth2"},
                    {"name": "invoice-paid", "kind": "event_producer", "visibility": "internal"},
                    {"name": "payment-import-worker", "kind": "queue_consumer", "visibility": "internal"},
                ],
                "inventory_receipt": "surface-inventory-1",
            },
            {"required_surface_kinds": ["api_endpoint", "event_producer", "queue_consumer"], "require_auth_for_public": True, "require_inventory_receipt": True},
        )
        bad_inventory = plan_service_surface_inventory(
            {"surfaces": [{"name": "POST /v1/invoices", "visibility": "public"}, {"kind": "event_producer"}]},
            {"required_surface_kinds": ["api_endpoint", "event_producer"], "require_auth_for_public": True, "require_inventory_receipt": True},
        )

        self.assertTrue(boundary.ready)
        self.assertTrue(boundary.boundary_hash.startswith("service-boundary-contract:"))
        self.assertFalse(bad_boundary.ready)
        self.assertIn("missing_service_name", bad_boundary.blockers)
        self.assertIn("missing_bounded_context", bad_boundary.blockers)
        self.assertIn("missing_owned_capabilities", bad_boundary.blockers)
        self.assertIn("missing_owner_team", bad_boundary.blockers)
        self.assertIn("dependency_without_contract:ledger_service", bad_boundary.blockers)
        self.assertIn("forbidden_shared_store_access", bad_boundary.blockers)
        self.assertIn("missing_boundary_receipt", bad_boundary.blockers)
        self.assertTrue(inventory.ready)
        self.assertEqual(inventory.public_surfaces, ("POST /v1/invoices",))
        self.assertFalse(bad_inventory.ready)
        self.assertIn("missing_service_name", bad_inventory.blockers)
        self.assertIn("surface_1_missing_kind", bad_inventory.blockers)
        self.assertIn("public_surface_missing_auth:POST /v1/invoices", bad_inventory.blockers)
        self.assertIn("surface_2_missing_name", bad_inventory.blockers)
        self.assertIn("missing_required_surface_kind:api_endpoint", bad_inventory.blockers)
        self.assertIn("missing_inventory_receipt", bad_inventory.blockers)

    def test_plan_service_data_ownership_and_startup_order_enforce_runtime_boundaries(self) -> None:
        ownership = plan_service_data_ownership(
            {
                "service_name": "billing-service",
                "owned_stores": ["billing-db"],
                "read_only_stores": ["customer-read-model"],
                "migration_owner": "payments-platform",
                "backup_policy": "daily",
                "data_classification": "confidential",
                "retention_policy": "7y",
                "ownership_receipt": "data-owner-1",
            },
            {
                "require_owned_store": True,
                "require_migration_owner": True,
                "require_backup_policy": True,
                "require_data_classification": True,
                "require_retention_policy": True,
                "require_ownership_receipt": True,
            },
        )
        bad_ownership = plan_service_data_ownership(
            {"shared_write_stores": ["shared-ledger-db"]},
            {
                "require_owned_store": True,
                "require_migration_owner": True,
                "require_backup_policy": True,
                "require_data_classification": True,
                "require_retention_policy": True,
                "require_ownership_receipt": True,
            },
        )
        startup = plan_service_startup_order(
            {
                "service_name": "billing-service",
                "startup_steps": ["load_config", "bind_secrets", "run_migrations", "start_http", "ready"],
                "dependency_checks": ["postgres", "customer-service"],
                "migration_gate": "pre-start-lock",
                "readiness_probe": "/readyz",
                "max_startup_seconds": 45,
            },
            {
                "required_steps": ["load_config", "bind_secrets", "run_migrations", "ready"],
                "require_dependency_checks": True,
                "require_migration_gate": True,
                "require_readiness_probe": True,
                "max_startup_seconds": 60,
            },
        )
        bad_startup = plan_service_startup_order(
            {"startup_steps": ["start_http"], "max_startup_seconds": 120},
            {
                "required_steps": ["load_config", "ready"],
                "require_dependency_checks": True,
                "require_migration_gate": True,
                "require_readiness_probe": True,
                "max_startup_seconds": 60,
            },
        )

        self.assertTrue(ownership.ready)
        self.assertFalse(bad_ownership.ready)
        self.assertIn("missing_service_name", bad_ownership.blockers)
        self.assertIn("missing_owned_stores", bad_ownership.blockers)
        self.assertIn("shared_write_store:shared_ledger_db", bad_ownership.blockers)
        self.assertIn("missing_migration_owner", bad_ownership.blockers)
        self.assertIn("missing_backup_policy", bad_ownership.blockers)
        self.assertIn("missing_data_classification", bad_ownership.blockers)
        self.assertIn("missing_retention_policy", bad_ownership.blockers)
        self.assertIn("missing_ownership_receipt", bad_ownership.blockers)
        self.assertTrue(startup.ready)
        self.assertFalse(bad_startup.ready)
        self.assertIn("missing_service_name", bad_startup.blockers)
        self.assertIn("missing_step:load_config", bad_startup.blockers)
        self.assertIn("missing_step:ready", bad_startup.blockers)
        self.assertIn("missing_dependency_checks", bad_startup.blockers)
        self.assertIn("missing_migration_gate", bad_startup.blockers)
        self.assertIn("missing_readiness_probe", bad_startup.blockers)
        self.assertIn("startup_time_exceeds_policy", bad_startup.blockers)

    def test_plan_service_secret_binding_and_backpressure_enforce_runtime_safety(self) -> None:
        secret_binding = plan_service_secret_binding(
            {
                "service_name": "billing-service",
                "secret_bindings": [
                    {"secret_ref": "secret://billing/db", "env_key": "DATABASE_URL", "provider": "vault"},
                    {"secret_ref": "secret://billing/stripe", "env_key": "STRIPE_KEY", "provider": "vault"},
                ],
                "rotation_policy": "90d",
                "runtime_identity": "svc-billing",
                "secret_receipt": "secret-bind-1",
            },
            {"allowed_providers": ["vault"], "require_rotation_policy": True, "require_runtime_identity": True, "require_secret_receipt": True},
        )
        bad_secret_binding = plan_service_secret_binding(
            {"secret_bindings": [{"provider": "env"}, {"secret_ref": "secret://x", "provider": "vault"}]},
            {"allowed_providers": ["vault"], "require_rotation_policy": True, "require_runtime_identity": True, "require_secret_receipt": True},
        )
        backpressure = plan_service_backpressure_policy(
            {
                "service_name": "billing-service",
                "max_inflight": 100,
                "queue_policy": "bounded",
                "overload_strategy": "shed-low-priority",
                "retry_after": "30s",
                "degrade_receipt": "backpressure-1",
            },
            {
                "max_inflight": 200,
                "allowed_queue_policies": ["bounded", "drop"],
                "require_queue_policy": True,
                "require_overload_strategy": True,
                "require_retry_after": True,
                "require_degrade_receipt": True,
            },
        )
        bad_backpressure = plan_service_backpressure_policy(
            {"max_inflight": 500, "queue_policy": "infinite"},
            {
                "max_inflight": 200,
                "allowed_queue_policies": ["bounded", "drop"],
                "require_queue_policy": True,
                "require_overload_strategy": True,
                "require_retry_after": True,
                "require_degrade_receipt": True,
            },
        )

        self.assertTrue(secret_binding.ready)
        self.assertFalse(bad_secret_binding.ready)
        self.assertIn("missing_service_name", bad_secret_binding.blockers)
        self.assertIn("binding_1_missing_secret_ref", bad_secret_binding.blockers)
        self.assertIn("binding_1_missing_env_key", bad_secret_binding.blockers)
        self.assertIn("secret_provider_not_allowed:env", bad_secret_binding.blockers)
        self.assertIn("binding_2_missing_env_key", bad_secret_binding.blockers)
        self.assertIn("missing_rotation_policy", bad_secret_binding.blockers)
        self.assertIn("missing_runtime_identity", bad_secret_binding.blockers)
        self.assertIn("missing_secret_receipt", bad_secret_binding.blockers)
        self.assertTrue(backpressure.ready)
        self.assertFalse(bad_backpressure.ready)
        self.assertIn("missing_service_name", bad_backpressure.blockers)
        self.assertIn("max_inflight_exceeds_policy", bad_backpressure.blockers)
        self.assertIn("queue_policy_not_allowed:infinite", bad_backpressure.blockers)
        self.assertIn("missing_overload_strategy", bad_backpressure.blockers)
        self.assertIn("missing_retry_after", bad_backpressure.blockers)
        self.assertIn("missing_degrade_receipt", bad_backpressure.blockers)

    def test_extract_openapi_and_asyncapi_operations_require_contracts(self) -> None:
        openapi = extract_openapi_operations(
            {
                "paths": {
                    "/invoices": {
                        "post": {
                            "operationId": "createInvoice",
                            "summary": "Create invoice",
                            "requestBody": {"content": {"application/json": {}}},
                            "responses": {"201": {"description": "created"}},
                        }
                    }
                }
            },
            {"require_operation_id": True, "require_success_response": True},
        )
        bad_openapi = extract_openapi_operations(
            {"paths": {"/invoices": {"post": {"responses": {"400": {"description": "bad"}}}}}},
            {"require_operation_id": True, "require_success_response": True},
        )
        asyncapi = extract_asyncapi_operations(
            {
                "channels": {
                    "invoice.created": {
                        "publish": {
                            "operationId": "publishInvoiceCreated",
                            "message": {"name": "InvoiceCreated"},
                        }
                    }
                }
            },
            {"require_message": True},
        )
        bad_asyncapi = extract_asyncapi_operations({"channels": {"invoice.created": {"publish": {}}}}, {"require_message": True})

        self.assertTrue(openapi.ready)
        self.assertEqual(openapi.operations[0]["visible_edge"], "HttpRequest[createInvoice] -> HttpResponse[createInvoiceReceipt]")
        self.assertFalse(bad_openapi.ready)
        self.assertIn("POST /invoices:missing_operation_id", bad_openapi.blockers)
        self.assertIn("POST /invoices:missing_success_response", bad_openapi.blockers)
        self.assertTrue(asyncapi.ready)
        self.assertEqual(asyncapi.operations[0]["message_name"], "InvoiceCreated")
        self.assertFalse(bad_asyncapi.ready)
        self.assertIn("invoice.created:publish:missing_message", bad_asyncapi.blockers)

    def test_normalize_cloudevent_and_plan_serverless_function_enforce_runtime_contracts(self) -> None:
        event = normalize_cloudevent_envelope(
            {"id": "evt-1", "source": "billing", "type": "invoice.created", "data": {"invoice_id": "inv-1"}, "traceparent": "00-abc"},
            {"allowed_specversions": ["1.0"], "required_extensions": ["traceparent"]},
        )
        bad_event = normalize_cloudevent_envelope({"id": "evt-2", "type": "invoice.created"}, {"allowed_specversions": ["1.0"], "required_extensions": ["traceparent"]})
        function = plan_serverless_function(
            {
                "function_name": "invoiceWebhook",
                "runtime": "python3.11",
                "handler": "handler.main",
                "trigger": {"type": "http"},
                "timeout_seconds": 30,
                "memory_mb": 256,
                "env": {"WEBHOOK_SECRET": "secret://stripe"},
            },
            {"allowed_runtimes": ["python3.11"], "allowed_triggers": ["http"], "max_timeout_seconds": 60, "max_memory_mb": 512, "required_env": ["WEBHOOK_SECRET"]},
        )
        bad_function = plan_serverless_function(
            {"function_name": "bad", "runtime": "node99", "trigger": {"type": "timer"}, "timeout_seconds": 120, "memory_mb": 1024},
            {"allowed_runtimes": ["python3.11"], "allowed_triggers": ["http"], "max_timeout_seconds": 60, "max_memory_mb": 512, "required_env": ["WEBHOOK_SECRET"]},
        )

        self.assertTrue(event.valid)
        self.assertEqual(event.envelope["specversion"], "1.0")
        self.assertFalse(bad_event.valid)
        self.assertIn("missing_source", bad_event.blockers)
        self.assertIn("missing_extension:traceparent", bad_event.blockers)
        self.assertTrue(function.ready)
        self.assertFalse(bad_function.ready)
        self.assertIn("runtime_not_allowed:node99", bad_function.blockers)
        self.assertIn("missing_handler", bad_function.blockers)
        self.assertIn("timeout_exceeds_policy", bad_function.blockers)

    def test_plan_observability_and_contract_suite_require_proof_artifacts(self) -> None:
        observability = plan_observability_instrumentation(
            {
                "operation_name": "POST /invoices",
                "spans": ["invoice.create"],
                "metrics": ["invoice_create_total"],
                "logs": ["request_id", "email"],
                "redacted_fields": ["email"],
                "trace_context": True,
            },
            {"require_trace_span": True, "require_metric": True, "require_log": True, "require_trace_context": True, "sensitive_fields": ["email"]},
        )
        bad_observability = plan_observability_instrumentation(
            {"operation_name": "POST /invoices", "logs": ["email"]},
            {"require_trace_span": True, "require_metric": True, "require_log": True, "require_trace_context": True, "sensitive_fields": ["email"]},
        )
        contract_suite = plan_api_contract_test_suite(
            [{"operation_id": "createInvoice", "method": "POST", "path": "/invoices", "response_codes": ["201"], "examples": [{"invoice_id": "inv-1"}]}],
            {"require_examples": True, "require_negative_cases": True},
        )
        bad_contract_suite = plan_api_contract_test_suite(
            [{"operation_id": "createInvoice", "method": "POST", "path": "/invoices", "response_codes": ["400"]}],
            {"require_examples": True, "require_negative_cases": True},
        )

        self.assertTrue(observability.ready)
        self.assertFalse(bad_observability.ready)
        self.assertIn("missing_trace_span", bad_observability.blockers)
        self.assertIn("missing_metric", bad_observability.blockers)
        self.assertIn("sensitive_field_not_redacted:email", bad_observability.blockers)
        self.assertTrue(contract_suite.ready)
        self.assertEqual(len(contract_suite.test_cases), 2)
        self.assertFalse(bad_contract_suite.ready)
        self.assertIn("createInvoice:missing_examples", bad_contract_suite.blockers)
        self.assertIn("createInvoice:missing_success_response", bad_contract_suite.blockers)

    def test_plan_feature_flag_and_secret_rotation_gate_rollout_and_ops(self) -> None:
        flag = plan_feature_flag(
            {"flag_key": "invoice-approval-v2", "strategy": "percentage", "audiences": ["beta"], "owner": "payments", "kill_switch": True, "rollout_percentage": 10},
            {"allowed_strategies": ["off", "percentage"], "require_owner": True, "require_kill_switch": True, "require_audiences": True, "max_rollout_percentage": 25},
        )
        bad_flag = plan_feature_flag(
            {"flag_key": "invoice-approval-v2", "strategy": "global", "rollout_percentage": 100},
            {"allowed_strategies": ["off", "percentage"], "require_owner": True, "require_kill_switch": True, "require_audiences": True, "max_rollout_percentage": 25},
        )
        rotation = plan_secret_rotation(
            {
                "secret_name": "stripe_webhook_secret",
                "provider": "vault",
                "rotation_interval_days": 30,
                "rotation_steps": ["create_new", "dual_write", "promote", "revoke_old"],
                "rollback": "restore old secret",
                "dual_write": True,
            },
            {"max_interval_days": 90, "required_steps": ["create_new", "promote", "revoke_old"], "require_rollback": True, "require_zero_downtime": True},
        )
        bad_rotation = plan_secret_rotation(
            {"secret_name": "stripe_webhook_secret", "provider": "vault", "rotation_interval_days": 180, "rotation_steps": ["create_new"]},
            {"max_interval_days": 90, "required_steps": ["create_new", "promote"], "require_rollback": True, "require_zero_downtime": True},
        )

        self.assertTrue(flag.ready)
        self.assertFalse(bad_flag.ready)
        self.assertIn("strategy_not_allowed:global", bad_flag.blockers)
        self.assertIn("missing_owner", bad_flag.blockers)
        self.assertIn("rollout_percentage_exceeds_policy", bad_flag.blockers)
        self.assertTrue(rotation.ready)
        self.assertFalse(bad_rotation.ready)
        self.assertIn("rotation_interval_exceeds_policy", bad_rotation.blockers)
        self.assertIn("missing_step:promote", bad_rotation.blockers)
        self.assertIn("missing_rollback", bad_rotation.blockers)

    def test_compile_agent_tool_schema_and_plan_sdk_package_enforce_contracts(self) -> None:
        tool = compile_agent_tool_schema_from_openapi(
            {
                "operation_id": "createInvoice",
                "method": "POST",
                "path": "/v1/invoices",
                "request_schema": {"properties": {"customer_id": {"type": "string"}, "amount": {"type": "number"}}},
                "required_scopes": ["invoice:write"],
            },
            {"allowed_methods": ["GET", "POST"], "require_parameters": True, "require_scopes": True, "max_parameters": 8},
        )
        bad_tool = compile_agent_tool_schema_from_openapi(
            {"operation_id": "deleteEverything", "method": "DELETE", "path": "/admin/wipe", "request_schema": {"properties": {}}},
            {"allowed_methods": ["GET", "POST"], "require_parameters": True, "require_scopes": True, "forbidden_path_prefixes": ["/admin"]},
        )
        sdk = plan_sdk_package(
            {
                "package_name": "billing-sdk",
                "operations": [{"operation_id": "createInvoice"}, {"operation_id": "getInvoice"}],
                "auth_strategy": "oauth2",
                "tests": ["contract"],
                "retry_policy": {"max_attempts": 3},
            },
            {"language": "typescript", "allowed_languages": ["typescript", "python"], "require_auth_strategy": True, "require_tests": True, "require_retry_policy": True},
        )
        bad_sdk = plan_sdk_package({"package_name": "billing-sdk", "operations": []}, {"language": "ruby", "allowed_languages": ["typescript"], "require_auth_strategy": True, "require_tests": True})

        self.assertTrue(tool.ready)
        self.assertEqual(tool.tool_name, "create_invoice")
        self.assertEqual(tool.parameters, ("amount", "customer_id"))
        self.assertFalse(bad_tool.ready)
        self.assertIn("method_not_allowed:DELETE", bad_tool.blockers)
        self.assertIn("missing_parameters", bad_tool.blockers)
        self.assertIn("missing_required_scopes", bad_tool.blockers)
        self.assertIn("path_prefix_forbidden", bad_tool.blockers)
        self.assertTrue(sdk.ready)
        self.assertEqual(sdk.language, "typescript")
        self.assertFalse(bad_sdk.ready)
        self.assertIn("language_not_allowed:ruby", bad_sdk.blockers)
        self.assertIn("missing_operations", bad_sdk.blockers)
        self.assertIn("missing_auth_strategy", bad_sdk.blockers)

    def test_plan_dockerfile_and_compose_stack_enforce_runtime_safety(self) -> None:
        dockerfile = plan_dockerfile(
            {
                "base_image": "python:3.11-slim",
                "workdir": "/app",
                "command": ["python", "-m", "service"],
                "exposed_ports": [8080],
                "user": "10001",
                "healthcheck": "curl -f http://localhost:8080/healthz",
            },
            {"require_pinned_base_image": True, "allowed_base_prefixes": ["python:"], "require_non_root_user": True, "require_healthcheck": True, "require_exposed_port": True},
        )
        bad_dockerfile = plan_dockerfile(
            {"base_image": "node:latest", "command": [], "exposed_ports": []},
            {"require_pinned_base_image": True, "allowed_base_prefixes": ["python:"], "require_non_root_user": True, "require_healthcheck": True, "require_exposed_port": True},
        )
        compose = plan_docker_compose_stack(
            {
                "services": {
                    "api": {"image": "billing:1.0", "healthcheck": {"test": "curl /healthz"}, "environment": {"DATABASE_URL": "secret://db"}},
                    "worker": {"build": ".", "healthcheck": {"test": "python -m health"}},
                },
                "networks": ["backend"],
                "volumes": ["pgdata"],
            },
            {"required_services": ["api", "worker"], "require_images": True, "require_healthchecks": True, "require_secret_refs": True},
        )
        bad_compose = plan_docker_compose_stack(
            {"services": {"api": {"environment": {"API_TOKEN": "plain-text"}}}},
            {"required_services": ["api", "worker"], "require_images": True, "require_healthchecks": True, "require_secret_refs": True},
        )

        self.assertTrue(dockerfile.ready)
        self.assertFalse(bad_dockerfile.ready)
        self.assertIn("base_image_not_pinned", bad_dockerfile.blockers)
        self.assertIn("base_image_not_allowed", bad_dockerfile.blockers)
        self.assertIn("missing_non_root_user", bad_dockerfile.blockers)
        self.assertTrue(compose.ready)
        self.assertFalse(bad_compose.ready)
        self.assertIn("api:missing_image_or_build", bad_compose.blockers)
        self.assertIn("api:missing_healthcheck", bad_compose.blockers)
        self.assertIn("api:inline_secret:API_TOKEN", bad_compose.blockers)
        self.assertIn("missing_service:worker", bad_compose.blockers)

    def test_plan_helm_chart_and_rbac_matrix_enforce_deploy_and_access_policy(self) -> None:
        helm = plan_helm_chart(
            {
                "chart_name": "billing-service",
                "templates": ["deployment.yaml", "service.yaml", "hpa.yaml"],
                "values": {
                    "image": {"repository": "billing", "tag": "1.2.3"},
                    "resources": {"requests": {"cpu": "100m"}, "limits": {"cpu": "500m"}},
                    "readinessProbe": {"httpGet": {"path": "/ready"}},
                    "livenessProbe": {"httpGet": {"path": "/live"}},
                },
            },
            {"required_templates": ["deployment.yaml", "service.yaml"], "require_resources": True, "require_probes": True, "forbid_latest_image": True},
        )
        bad_helm = plan_helm_chart(
            {"chart_name": "billing", "templates": ["deployment.yaml"], "values": {"image": {"tag": "latest"}}},
            {"required_templates": ["deployment.yaml", "service.yaml"], "require_resources": True, "require_probes": True, "forbid_latest_image": True},
        )
        rbac = plan_rbac_policy_matrix(
            {
                "roles": ["analyst", "admin"],
                "actions": ["invoice.read", "invoice.approve"],
                "bindings": [{"role": "analyst", "actions": ["invoice.read"], "reason": "review invoices"}],
            },
            {"forbid_wildcards": True, "require_reason": True},
        )
        bad_rbac = plan_rbac_policy_matrix(
            {"roles": ["admin"], "actions": ["invoice.read"], "bindings": [{"role": "admin", "actions": ["*"]}, {"role": "ghost", "actions": ["invoice.delete"], "reason": "bad"}]},
            {"forbid_wildcards": True, "require_reason": True},
        )

        self.assertTrue(helm.ready)
        self.assertFalse(bad_helm.ready)
        self.assertIn("missing_template:service.yaml", bad_helm.blockers)
        self.assertIn("missing_resource_requests_or_limits", bad_helm.blockers)
        self.assertIn("missing_probes", bad_helm.blockers)
        self.assertIn("image_tag_not_pinned", bad_helm.blockers)
        self.assertTrue(rbac.ready)
        self.assertFalse(bad_rbac.ready)
        self.assertIn("admin:wildcard_action_forbidden", bad_rbac.blockers)
        self.assertIn("admin:missing_reason", bad_rbac.blockers)
        self.assertIn("binding_2_unknown_role", bad_rbac.blockers)

    def test_plan_pii_redaction_and_connector_auth_binding_require_security_edges(self) -> None:
        pii = plan_pii_redaction_policy(
            {"fields": {"email": "string", "name": "string", "amount": "number"}},
            {"sensitive_fields": ["email", "name"], "redaction_map": {"email": "hash", "name": "mask"}, "allowed_methods": ["hash", "mask"]},
        )
        bad_pii = plan_pii_redaction_policy(
            {"fields": {"email": "string"}},
            {"sensitive_fields": ["email", "ssn"], "redaction_map": {"email": "raw"}, "allowed_methods": ["hash"]},
        )
        connector = plan_connector_auth_binding(
            {
                "connector_name": "salesforce-to-hubspot",
                "source_system": "salesforce",
                "target_system": "hubspot",
                "auth_bindings": [{"auth_type": "oauth2", "secret_ref": "secret://sf-token", "scopes": ["contacts.read"], "rotation": "30d"}],
            },
            {"allowed_auth_types": ["oauth2"], "required_scopes": ["contacts.read"], "require_secret_refs": True, "require_rotation": True},
        )
        bad_connector = plan_connector_auth_binding(
            {
                "connector_name": "bad",
                "source_system": "salesforce",
                "target_system": "",
                "auth_bindings": [{"auth_type": "api_key", "secret_ref": "plain", "scopes": []}],
            },
            {"allowed_auth_types": ["oauth2"], "required_scopes": ["contacts.read"], "require_secret_refs": True, "require_rotation": True},
        )

        self.assertTrue(pii.ready)
        self.assertFalse(bad_pii.ready)
        self.assertIn("sensitive_field_not_in_schema:ssn", bad_pii.blockers)
        self.assertIn("redaction_method_not_allowed:email", bad_pii.blockers)
        self.assertIn("unprotected_sensitive_fields", bad_pii.blockers)
        self.assertTrue(connector.ready)
        self.assertFalse(bad_connector.ready)
        self.assertIn("missing_target_system", bad_connector.blockers)
        self.assertIn("auth_type_not_allowed:api_key", bad_connector.blockers)
        self.assertIn("binding_1_missing_secret_ref", bad_connector.blockers)
        self.assertIn("binding_1_missing_scope:contacts.read", bad_connector.blockers)
        self.assertIn("binding_1_missing_rotation", bad_connector.blockers)

    def test_plan_idempotency_policy_and_pagination_contract_enforce_api_edges(self) -> None:
        idempotency = plan_idempotency_policy(
            {
                "operation_name": "create-invoice",
                "key_fields": ["tenant_id", "external_invoice_id"],
                "ttl_seconds": 86400,
                "store_name": "redis-idempotency",
                "replay_strategy": "return_original_receipt",
                "conflict_response": {"status": 409},
            },
            {"require_tenant_key": True, "max_ttl_seconds": 172800, "require_replay_strategy": True, "require_conflict_response": True},
        )
        bad_idempotency = plan_idempotency_policy(
            {"operation_name": "create-invoice", "key_fields": ["external_invoice_id"], "ttl_seconds": 999999},
            {"require_tenant_key": True, "max_ttl_seconds": 172800, "require_replay_strategy": True, "require_conflict_response": True},
        )
        pagination = plan_pagination_contract(
            {
                "resource_name": "customer_accounts",
                "mode": "cursor",
                "default_limit": 50,
                "max_limit": 200,
                "sort_fields": ["created_at", "id"],
                "cursor_fields": ["created_at", "id"],
            },
            {"allowed_modes": ["cursor", "offset"], "absolute_max_limit": 500, "require_stable_sort": True, "require_cursor_fields": True},
        )
        bad_pagination = plan_pagination_contract(
            {"resource_name": "customer_accounts", "mode": "cursor", "default_limit": 1000, "max_limit": 900},
            {"allowed_modes": ["cursor"], "absolute_max_limit": 500, "require_stable_sort": True, "require_cursor_fields": True},
        )

        self.assertTrue(idempotency.ready)
        self.assertFalse(bad_idempotency.ready)
        self.assertIn("missing_tenant_key", bad_idempotency.blockers)
        self.assertIn("ttl_exceeds_policy", bad_idempotency.blockers)
        self.assertIn("missing_store_name", bad_idempotency.blockers)
        self.assertIn("missing_replay_strategy", bad_idempotency.blockers)
        self.assertIn("missing_conflict_response", bad_idempotency.blockers)
        self.assertTrue(pagination.ready)
        self.assertFalse(bad_pagination.ready)
        self.assertIn("default_limit_exceeds_max", bad_pagination.blockers)
        self.assertIn("max_limit_exceeds_policy", bad_pagination.blockers)
        self.assertIn("missing_stable_sort", bad_pagination.blockers)
        self.assertIn("missing_cursor_fields", bad_pagination.blockers)

    def test_plan_cors_security_headers_and_audit_log_policy_enforce_surface_safety(self) -> None:
        headers = plan_cors_security_headers(
            {
                "allowed_origins": ["https://app.example.com"],
                "allowed_methods": ["GET", "POST"],
                "security_headers": {
                    "Content-Security-Policy": "default-src 'self'",
                    "X-Content-Type-Options": "nosniff",
                    "Access-Control-Allow-Credentials": "true",
                },
            },
            {
                "forbid_wildcard_origin": True,
                "required_methods": ["GET"],
                "allowed_methods": ["GET", "POST", "OPTIONS"],
                "required_headers": ["Content-Security-Policy", "X-Content-Type-Options"],
                "require_credentials_policy": True,
            },
        )
        bad_headers = plan_cors_security_headers(
            {"allowed_origins": ["*"], "allowed_methods": ["TRACE"], "security_headers": {}},
            {
                "forbid_wildcard_origin": True,
                "required_methods": ["GET"],
                "allowed_methods": ["GET", "POST", "OPTIONS"],
                "required_headers": ["Content-Security-Policy", "X-Content-Type-Options"],
                "require_credentials_policy": True,
            },
        )
        audit = plan_audit_log_policy(
            {
                "event_name": "invoice-approved",
                "emitted_fields": ["actor_id", "action", "resource_id", "timestamp", "reason_code", "trace_id"],
                "retention_days": 365,
                "tamper_evidence": "hash_chain",
            },
            {
                "required_fields": ["actor_id", "action", "resource_id", "timestamp"],
                "min_retention_days": 180,
                "require_reason_code": True,
                "require_tamper_evidence": True,
                "require_trace_id": True,
            },
        )
        bad_audit = plan_audit_log_policy(
            {"event_name": "invoice-approved", "emitted_fields": ["actor_id"], "retention_days": 30},
            {
                "required_fields": ["actor_id", "action", "resource_id", "timestamp"],
                "min_retention_days": 180,
                "require_reason_code": True,
                "require_tamper_evidence": True,
                "require_trace_id": True,
            },
        )

        self.assertTrue(headers.ready)
        self.assertFalse(bad_headers.ready)
        self.assertIn("wildcard_origin_forbidden", bad_headers.blockers)
        self.assertIn("missing_method:GET", bad_headers.blockers)
        self.assertIn("method_not_allowed:TRACE", bad_headers.blockers)
        self.assertIn("missing_header:Content-Security-Policy", bad_headers.blockers)
        self.assertIn("missing_credentials_policy", bad_headers.blockers)
        self.assertTrue(audit.ready)
        self.assertFalse(bad_audit.ready)
        self.assertIn("missing_required_field:action", bad_audit.blockers)
        self.assertIn("retention_below_policy", bad_audit.blockers)
        self.assertIn("missing_reason_code", bad_audit.blockers)
        self.assertIn("missing_tamper_evidence", bad_audit.blockers)
        self.assertIn("missing_trace_id", bad_audit.blockers)

    def test_plan_tenant_isolation_and_event_schema_compatibility_enforce_contract_evolution(self) -> None:
        isolation = plan_tenant_isolation(
            {
                "resource_name": "invoice",
                "tenant_key": "tenant_id",
                "isolation_mode": "row",
                "query_filters": ["tenant_id", "invoice_id"],
                "auth_context": {"tenant_id": "t-1"},
                "storage_scope": "tenant_partition",
                "negative_tests": ["cross_tenant_read_denied"],
            },
            {"allowed_modes": ["row", "database"], "require_auth_context": True, "require_query_filter": True, "require_storage_scope": True, "require_negative_tests": True},
        )
        bad_isolation = plan_tenant_isolation(
            {"resource_name": "invoice", "tenant_key": "tenant_id", "isolation_mode": "shared", "query_filters": []},
            {"allowed_modes": ["row", "database"], "require_auth_context": True, "require_query_filter": True, "require_storage_scope": True, "require_negative_tests": True},
        )
        compatible = evaluate_event_schema_compatibility(
            {"event_type": "invoice.created", "version": "1.0.0", "fields": {"id": "string", "amount": "number"}, "required": ["id"]},
            {"event_type": "invoice.created", "version": "1.1.0", "fields": {"id": "string", "amount": "number", "status": "string"}, "required": ["id"]},
            {"forbid_removed_fields": True, "forbid_changed_fields": True, "forbid_new_required_fields": True, "require_version_bump": True},
        )
        incompatible = evaluate_event_schema_compatibility(
            {"event_type": "invoice.created", "version": "1.0.0", "fields": {"id": "string", "amount": "number"}, "required": ["id"]},
            {"event_type": "invoice.created", "version": "1.0.0", "fields": {"id": "integer", "status": "string"}, "required": ["id", "status"]},
            {"forbid_removed_fields": True, "forbid_changed_fields": True, "forbid_new_required_fields": True, "require_version_bump": True},
        )

        self.assertTrue(isolation.ready)
        self.assertFalse(bad_isolation.ready)
        self.assertIn("isolation_mode_not_allowed:shared", bad_isolation.blockers)
        self.assertIn("missing_auth_context", bad_isolation.blockers)
        self.assertIn("missing_tenant_query_filter", bad_isolation.blockers)
        self.assertIn("missing_storage_scope", bad_isolation.blockers)
        self.assertIn("missing_negative_tests", bad_isolation.blockers)
        self.assertTrue(compatible.compatible)
        self.assertEqual(compatible.added_fields, ("status",))
        self.assertFalse(incompatible.compatible)
        self.assertIn("removed_fields", incompatible.blockers)
        self.assertIn("changed_fields", incompatible.blockers)
        self.assertIn("new_required_fields", incompatible.blockers)
        self.assertIn("missing_version_bump", incompatible.blockers)

    def test_plan_dead_letter_replay_and_cache_invalidation_enforce_operational_guards(self) -> None:
        replay = plan_dead_letter_replay(
            {
                "queue_name": "invoice-events-dlq",
                "replay_batch_size": 50,
                "max_retries": 3,
                "dedupe_key": "event_id",
                "poison_message_quarantine": "s3://quarantine",
                "audit_receipt": True,
                "throttle": "10/s",
            },
            {"max_batch_size": 100, "require_dedupe_key": True, "require_poison_message_quarantine": True, "require_audit_receipt": True, "require_throttle": True},
        )
        bad_replay = plan_dead_letter_replay(
            {"queue_name": "invoice-events-dlq", "replay_batch_size": 500},
            {"max_batch_size": 100, "require_dedupe_key": True, "require_poison_message_quarantine": True, "require_audit_receipt": True, "require_throttle": True},
        )
        cache = plan_cache_invalidation(
            {
                "cache_name": "customer-profile",
                "key_patterns": ["tenant:{tenant_id}:customer:{customer_id}"],
                "triggers": ["customer.updated"],
                "ttl_seconds": 300,
                "namespace": "tenant",
                "stale_read_strategy": "serve_then_revalidate",
                "metrics": ["hit_rate", "invalidation_count"],
            },
            {"max_ttl_seconds": 600, "require_namespace": True, "require_stale_read_strategy": True, "require_observability": True},
        )
        bad_cache = plan_cache_invalidation(
            {"cache_name": "customer-profile", "ttl_seconds": 999},
            {"max_ttl_seconds": 600, "require_namespace": True, "require_stale_read_strategy": True, "require_observability": True},
        )

        self.assertTrue(replay.ready)
        self.assertFalse(bad_replay.ready)
        self.assertIn("replay_batch_size_exceeds_policy", bad_replay.blockers)
        self.assertIn("missing_max_retries", bad_replay.blockers)
        self.assertIn("missing_dedupe_key", bad_replay.blockers)
        self.assertIn("missing_poison_message_quarantine", bad_replay.blockers)
        self.assertIn("missing_audit_receipt", bad_replay.blockers)
        self.assertIn("missing_throttle", bad_replay.blockers)
        self.assertTrue(cache.ready)
        self.assertFalse(bad_cache.ready)
        self.assertIn("missing_key_patterns", bad_cache.blockers)
        self.assertIn("missing_invalidation_triggers", bad_cache.blockers)
        self.assertIn("ttl_exceeds_policy", bad_cache.blockers)
        self.assertIn("missing_namespace", bad_cache.blockers)
        self.assertIn("missing_stale_read_strategy", bad_cache.blockers)
        self.assertIn("missing_cache_metrics", bad_cache.blockers)

    def test_plan_document_chunking_and_retrieval_rerank_policy_enforce_rag_inputs(self) -> None:
        chunks = plan_document_chunking(
            [
                {"id": "doc-1", "text": "a" * 1200, "metadata": {"source": "handbook"}},
                {"id": "doc-2", "text": "b" * 100, "metadata": {"source": "faq"}},
            ],
            {"chunk_chars": 500, "overlap_chars": 50, "max_chunk_chars": 1000, "require_document_id": True, "require_metadata": True},
        )
        bad_chunks = plan_document_chunking(
            [{"text": "", "metadata": {}}, {"text": "body"}],
            {"chunk_chars": 100, "overlap_chars": 100, "max_chunk_chars": 80, "require_document_id": True, "require_metadata": True},
        )
        retrieval = plan_retrieval_rerank_policy(
            {
                "retrievers": [{"name": "vector", "source": "kb"}, {"name": "keyword", "source": "tickets"}],
                "top_k": 8,
                "reranker_model": "bge-reranker",
            },
            {"max_top_k": 20, "require_reranker": True, "allowed_rerankers": ["bge-reranker"], "require_source_diversity": True, "min_sources": 2},
        )
        bad_retrieval = plan_retrieval_rerank_policy(
            {"retrievers": [{"name": "vector", "source": "kb"}], "top_k": 100, "reranker_model": "unknown"},
            {"max_top_k": 20, "require_reranker": True, "allowed_rerankers": ["bge-reranker"], "require_source_diversity": True, "min_sources": 2},
        )

        self.assertTrue(chunks.ready)
        self.assertEqual(chunks.chunk_count, 4)
        self.assertFalse(bad_chunks.ready)
        self.assertIn("overlap_exceeds_chunk", bad_chunks.blockers)
        self.assertIn("chunk_chars_exceeds_policy", bad_chunks.blockers)
        self.assertIn("document_1_missing_text", bad_chunks.blockers)
        self.assertIn("document_2_missing_id", bad_chunks.blockers)
        self.assertIn("document_2_missing_metadata", bad_chunks.blockers)
        self.assertTrue(retrieval.ready)
        self.assertFalse(bad_retrieval.ready)
        self.assertIn("top_k_exceeds_policy", bad_retrieval.blockers)
        self.assertIn("reranker_not_allowed:unknown", bad_retrieval.blockers)
        self.assertIn("insufficient_source_diversity", bad_retrieval.blockers)

    def test_evaluate_citation_coverage_and_tool_permission_matrix_guard_agent_outputs(self) -> None:
        coverage = evaluate_citation_coverage(
            {
                "claims": [{"id": "c1", "text": "Invoices are reconciled nightly"}, {"id": "c2", "text": "Retries are idempotent"}],
                "citations": [{"source_id": "runbook", "claim_ids": ["c1", "c2"]}],
            },
            {"min_citations": 1, "require_source_ids": True},
        )
        bad_coverage = evaluate_citation_coverage(
            {
                "claims": [{"id": "c1"}, {"id": "c2"}],
                "citations": [{"claim_ids": ["c1"]}],
            },
            {"min_citations": 2, "require_source_ids": True},
        )
        permissions = plan_agent_tool_permission_matrix(
            {
                "tools": [{"name": "send_email", "effects": ["network_write"]}, {"name": "search_docs", "effects": ["network_read"]}],
                "roles": ["support_agent", "admin"],
                "bindings": [{"role": "support_agent", "tool": "send_email", "scopes": ["email.send"], "reason": "customer reply", "approval_required": True}],
            },
            {"require_scopes": True, "require_reason": True, "forbid_wildcards": True, "require_approval_for_effects": True},
        )
        bad_permissions = plan_agent_tool_permission_matrix(
            {
                "tools": [{"name": "send_email", "effects": ["network_write"]}],
                "roles": ["support_agent"],
                "bindings": [{"role": "support_agent", "tool": "*"}, {"role": "ghost", "tool": "delete_user", "scopes": []}],
            },
            {"require_scopes": True, "require_reason": True, "forbid_wildcards": True, "require_approval_for_effects": True},
        )

        self.assertTrue(coverage.grounded)
        self.assertFalse(bad_coverage.grounded)
        self.assertEqual(bad_coverage.uncovered_claims, ("c2",))
        self.assertIn("uncovered_claims", bad_coverage.blockers)
        self.assertIn("citation_count_below_policy", bad_coverage.blockers)
        self.assertIn("citation_1_missing_source_id", bad_coverage.blockers)
        self.assertTrue(permissions.ready)
        self.assertFalse(bad_permissions.ready)
        self.assertIn("support_agent:wildcard_tool_forbidden", bad_permissions.blockers)
        self.assertIn("support_agent:*:missing_scopes", bad_permissions.blockers)
        self.assertIn("support_agent:*:missing_reason", bad_permissions.blockers)
        self.assertIn("binding_2_unknown_role", bad_permissions.blockers)
        self.assertIn("ghost:unknown_tool:delete_user", bad_permissions.blockers)

    def test_plan_model_routing_and_prompt_regression_suite_enforce_eval_readiness(self) -> None:
        routing = plan_model_routing_policy(
            {
                "default_model": "gpt-4.1-mini",
                "fallback_models": ["gpt-4.1"],
                "routes": [
                    {"name": "public_docs", "model": "gpt-4.1-mini", "max_cost_usd": 0.02, "data_classes": ["public"]},
                    {"name": "pii_review", "model": "local-redactor", "max_cost_usd": 0.01, "data_classes": ["pii"], "local_only": True},
                ],
            },
            {"allowed_models": ["gpt-4.1-mini", "gpt-4.1", "local-redactor"], "require_fallback": True, "max_cost_usd": 0.05, "restricted_data_classes": ["pii"]},
        )
        bad_routing = plan_model_routing_policy(
            {
                "default_model": "unknown",
                "routes": [{"name": "pii_review", "model": "gpt-4.1", "max_cost_usd": 0.5, "data_classes": ["pii"]}],
            },
            {"allowed_models": ["gpt-4.1-mini", "gpt-4.1"], "require_fallback": True, "max_cost_usd": 0.05, "restricted_data_classes": ["pii"]},
        )
        suite = plan_prompt_regression_suite(
            {
                "cases": [{"id": "case-1", "prompt": "Summarize", "expected_terms": ["receipt"]}, {"id": "case-2", "prompt": "Cite", "expected_output": "with citation"}],
                "metrics": ["grounding", "format"],
                "thresholds": {"grounding": 0.9, "format": 1.0},
            },
            {"min_cases": 2, "require_expected_outputs": True},
        )
        bad_suite = plan_prompt_regression_suite(
            {"cases": [{"id": "case-1", "prompt": "Summarize"}], "metrics": ["grounding"], "thresholds": {}},
            {"min_cases": 2, "require_expected_outputs": True},
        )

        self.assertTrue(routing.ready)
        self.assertFalse(bad_routing.ready)
        self.assertIn("default_model_not_allowed:unknown", bad_routing.blockers)
        self.assertIn("missing_fallback_models", bad_routing.blockers)
        self.assertIn("pii_review:cost_exceeds_policy", bad_routing.blockers)
        self.assertIn("pii_review:restricted_data_requires_local_route", bad_routing.blockers)
        self.assertTrue(suite.ready)
        self.assertFalse(bad_suite.ready)
        self.assertIn("case_count_below_policy", bad_suite.blockers)
        self.assertIn("missing_threshold:grounding", bad_suite.blockers)
        self.assertIn("case_1_missing_expected_output", bad_suite.blockers)

    def test_plan_memory_retention_and_vector_index_freshness_enforce_lifecycle_gates(self) -> None:
        memory = plan_memory_retention_policy(
            {
                "memory_scope": "support_agent",
                "retention_days": 30,
                "pii_fields": ["email"],
                "redaction_policy": {"email": "hash"},
                "deletion_workflow": "delete_on_request",
                "consent_signal": "user_opt_in",
            },
            {"max_retention_days": 90, "require_deletion_workflow": True, "require_consent": True, "require_pii_redaction": True},
        )
        bad_memory = plan_memory_retention_policy(
            {"memory_scope": "support_agent", "retention_days": 365, "pii_fields": ["email"]},
            {"max_retention_days": 90, "require_deletion_workflow": True, "require_consent": True, "require_pii_redaction": True},
        )
        freshness = evaluate_vector_index_freshness(
            {
                "index_name": "support-kb",
                "age_seconds": 1800,
                "documents": [{"id": "doc-1", "age_seconds": 1000}, {"id": "doc-2", "age_seconds": 1200}],
            },
            {"max_age_seconds": 3600, "max_document_age_seconds": 1800, "require_rebuild_plan": True},
        )
        stale = evaluate_vector_index_freshness(
            {
                "index_name": "support-kb",
                "age_seconds": 9999,
                "documents": [{"id": "doc-1", "age_seconds": 9999}],
            },
            {"max_age_seconds": 3600, "max_document_age_seconds": 1800, "require_rebuild_plan": True},
        )

        self.assertTrue(memory.ready)
        self.assertFalse(bad_memory.ready)
        self.assertIn("retention_exceeds_policy", bad_memory.blockers)
        self.assertIn("missing_deletion_workflow", bad_memory.blockers)
        self.assertIn("missing_consent_signal", bad_memory.blockers)
        self.assertIn("missing_pii_redaction_policy", bad_memory.blockers)
        self.assertTrue(freshness.fresh)
        self.assertFalse(stale.fresh)
        self.assertEqual(stale.stale_documents, ("doc-1",))
        self.assertIn("index_age_exceeds_policy", stale.blockers)
        self.assertIn("stale_documents", stale.blockers)
        self.assertIn("missing_rebuild_plan", stale.blockers)

    def test_plan_canary_release_and_blue_green_deployment_enforce_release_gates(self) -> None:
        canary = plan_canary_release(
            {
                "service_name": "billing-api",
                "image_tag": "2026.07.01",
                "traffic_steps": [5, 25, 50, 100],
                "metrics": ["error_rate", "latency_p95"],
                "health_gate": {"path": "/ready"},
                "rollback_strategy": "restore previous deployment",
            },
            {"require_pinned_image": True, "max_step_percent": 50, "required_metrics": ["error_rate"], "require_metrics": True, "require_health_gate": True, "require_rollback": True},
        )
        bad_canary = plan_canary_release(
            {"service_name": "billing-api", "image_tag": "latest", "traffic_steps": [75], "metrics": []},
            {"require_pinned_image": True, "max_step_percent": 50, "required_metrics": ["error_rate"], "require_metrics": True, "require_health_gate": True, "require_rollback": True},
        )
        blue_green = plan_blue_green_deployment(
            {
                "service_name": "billing-api",
                "active_color": "blue",
                "target_color": "green",
                "switch_strategy": "weighted-dns",
                "smoke_tests": ["GET /ready"],
                "database_compatible": True,
                "rollback_strategy": "switch back to blue",
            },
            {"allowed_colors": ["blue", "green"], "require_switch_strategy": True, "require_smoke_tests": True, "require_db_compatibility": True, "require_rollback": True},
        )
        bad_blue_green = plan_blue_green_deployment(
            {"service_name": "billing-api", "active_color": "blue", "target_color": "blue"},
            {"allowed_colors": ["blue", "green"], "require_switch_strategy": True, "require_smoke_tests": True, "require_db_compatibility": True, "require_rollback": True},
        )

        self.assertTrue(canary.ready)
        self.assertFalse(bad_canary.ready)
        self.assertIn("image_tag_not_pinned", bad_canary.blockers)
        self.assertIn("traffic_steps_must_finish_at_100", bad_canary.blockers)
        self.assertIn("traffic_step_exceeds_policy:75", bad_canary.blockers)
        self.assertIn("missing_metrics", bad_canary.blockers)
        self.assertIn("missing_metric:error_rate", bad_canary.blockers)
        self.assertIn("missing_health_gate", bad_canary.blockers)
        self.assertIn("missing_rollback_strategy", bad_canary.blockers)
        self.assertTrue(blue_green.ready)
        self.assertFalse(bad_blue_green.ready)
        self.assertIn("target_color_matches_active", bad_blue_green.blockers)
        self.assertIn("missing_switch_strategy", bad_blue_green.blockers)
        self.assertIn("missing_smoke_tests", bad_blue_green.blockers)
        self.assertIn("missing_database_compatibility", bad_blue_green.blockers)
        self.assertIn("missing_rollback_strategy", bad_blue_green.blockers)

    def test_plan_slo_and_dependency_vulnerability_exception_enforce_risk_gates(self) -> None:
        slo = plan_slo_error_budget_policy(
            {
                "service_name": "checkout-api",
                "slo_target_percent": 99.9,
                "window_days": 30,
                "error_budget_minutes": 43,
                "alert_windows": ["5m", "1h"],
                "burn_rate_alerts": ["fast", "slow"],
                "runbook_ref": "runbook://checkout-slo",
            },
            {"min_slo_target_percent": 99.0, "require_alert_windows": True, "require_burn_rate_alerts": True, "require_runbook": True},
        )
        bad_slo = plan_slo_error_budget_policy(
            {"service_name": "checkout-api", "slo_target_percent": 95.0, "window_days": 0},
            {"min_slo_target_percent": 99.0, "require_alert_windows": True, "require_burn_rate_alerts": True, "require_runbook": True},
        )
        exception = evaluate_dependency_vulnerability_exception(
            {
                "dependency_name": "urllib3",
                "vulnerability_id": "CVE-2026-0001",
                "severity": "high",
                "expiry_days": 14,
                "owner": "security",
                "compensating_controls": ["egress blocked"],
                "fix_version": "2.3.1",
            },
            {"allowed_severities": ["low", "medium", "high"], "forbid_critical_exceptions": True, "max_expiry_days": 30, "require_owner": True, "require_compensating_controls": True, "require_fix_version": True},
        )
        bad_exception = evaluate_dependency_vulnerability_exception(
            {"dependency_name": "openssl", "vulnerability_id": "CVE-2026-9999", "severity": "critical", "expiry_days": 90},
            {"allowed_severities": ["low", "medium", "high"], "forbid_critical_exceptions": True, "max_expiry_days": 30, "require_owner": True, "require_compensating_controls": True, "require_fix_version": True},
        )

        self.assertTrue(slo.ready)
        self.assertFalse(bad_slo.ready)
        self.assertIn("slo_target_below_policy", bad_slo.blockers)
        self.assertIn("missing_window_days", bad_slo.blockers)
        self.assertIn("missing_error_budget_minutes", bad_slo.blockers)
        self.assertIn("missing_alert_windows", bad_slo.blockers)
        self.assertIn("missing_burn_rate_alerts", bad_slo.blockers)
        self.assertIn("missing_runbook_ref", bad_slo.blockers)
        self.assertTrue(exception.approved)
        self.assertFalse(bad_exception.approved)
        self.assertIn("severity_not_allowed:critical", bad_exception.blockers)
        self.assertIn("critical_exception_forbidden", bad_exception.blockers)
        self.assertIn("expiry_exceeds_policy", bad_exception.blockers)
        self.assertIn("missing_owner", bad_exception.blockers)
        self.assertIn("missing_compensating_controls", bad_exception.blockers)
        self.assertIn("missing_fix_version", bad_exception.blockers)

    def test_evaluate_secret_scan_and_plan_sbom_generation_enforce_supply_chain_evidence(self) -> None:
        scan = evaluate_secret_scan_findings(
            {"scanner_name": "gitleaks", "findings": [{"id": "f1", "confirmed": False, "ignored": True, "ignore_reason": "test fixture"}]},
            {"require_findings_payload": True, "require_remediation_for_confirmed": True, "require_ignore_reasons": True},
        )
        bad_scan = evaluate_secret_scan_findings(
            {"scanner_name": "gitleaks", "findings": [{"id": "f1", "confidence": "high"}, {"id": "f2", "ignored": True}]},
            {"require_findings_payload": True, "require_remediation_for_confirmed": True, "require_ignore_reasons": True},
        )
        sbom = plan_sbom_generation(
            {
                "package_name": "billing-service",
                "components": [{"name": "fastapi", "version": "1.0", "supplier": "pypi"}],
                "formats": ["cyclonedx-json", "spdx-json"],
                "provenance": {"builder": "ci"},
            },
            {"allowed_formats": ["cyclonedx-json", "spdx-json"], "required_formats": ["cyclonedx-json"], "require_provenance": True, "require_supplier": True},
        )
        bad_sbom = plan_sbom_generation(
            {"package_name": "billing-service", "components": [{"name": "fastapi"}], "formats": ["txt"]},
            {"allowed_formats": ["cyclonedx-json"], "required_formats": ["cyclonedx-json"], "require_provenance": True, "require_supplier": True},
        )

        self.assertTrue(scan.clean)
        self.assertFalse(bad_scan.clean)
        self.assertEqual(bad_scan.confirmed_secret_count, 1)
        self.assertIn("confirmed_secret_findings", bad_scan.blockers)
        self.assertIn("finding_1_missing_remediation", bad_scan.blockers)
        self.assertIn("finding_2_missing_ignore_reason", bad_scan.blockers)
        self.assertTrue(sbom.ready)
        self.assertFalse(bad_sbom.ready)
        self.assertIn("format_not_allowed:txt", bad_sbom.blockers)
        self.assertIn("missing_format:cyclonedx-json", bad_sbom.blockers)
        self.assertIn("missing_provenance", bad_sbom.blockers)
        self.assertIn("component_missing_supplier", bad_sbom.blockers)

    def test_plan_license_compliance_and_backup_restore_enforce_operational_evidence(self) -> None:
        license_plan = plan_license_compliance(
            {"packages": [{"name": "fastapi", "license": "MIT", "attribution": "FastAPI authors"}, {"name": "pydantic", "license": "MIT", "attribution": "Pydantic authors"}]},
            {"restricted_licenses": ["GPL-3.0"], "require_attribution": True, "require_license_ids": True},
        )
        bad_license = plan_license_compliance(
            {"packages": [{"name": "copyleft-lib", "license": "GPL-3.0"}, {"name": "unknown"}]},
            {"restricted_licenses": ["GPL-3.0"], "require_attribution": True, "require_license_ids": True},
        )
        backup = plan_backup_restore(
            {
                "resource_name": "customer-db",
                "backup_frequency": "hourly",
                "restore_objective_minutes": 30,
                "recovery_point_minutes": 15,
                "encryption": "kms",
                "restore_test": "2026-07-01",
                "offsite_copy": "s3://backup-copy",
            },
            {"max_restore_objective_minutes": 60, "max_recovery_point_minutes": 30, "require_encryption": True, "require_restore_test": True, "require_offsite_copy": True},
        )
        bad_backup = plan_backup_restore(
            {"resource_name": "customer-db", "backup_frequency": "", "restore_objective_minutes": 120, "recovery_point_minutes": 90},
            {"max_restore_objective_minutes": 60, "max_recovery_point_minutes": 30, "require_encryption": True, "require_restore_test": True, "require_offsite_copy": True},
        )

        self.assertTrue(license_plan.compliant)
        self.assertFalse(bad_license.compliant)
        self.assertEqual(bad_license.restricted_licenses, ("GPL-3.0",))
        self.assertIn("restricted_licenses_present", bad_license.blockers)
        self.assertIn("package_1_missing_attribution", bad_license.blockers)
        self.assertIn("package_2_missing_license", bad_license.blockers)
        self.assertTrue(backup.ready)
        self.assertFalse(bad_backup.ready)
        self.assertIn("missing_backup_frequency", bad_backup.blockers)
        self.assertIn("restore_objective_exceeds_policy", bad_backup.blockers)
        self.assertIn("recovery_point_exceeds_policy", bad_backup.blockers)
        self.assertIn("missing_encryption", bad_backup.blockers)
        self.assertIn("missing_restore_test", bad_backup.blockers)
        self.assertIn("missing_offsite_copy", bad_backup.blockers)

    def test_plan_circuit_breaker_and_retry_backoff_enforce_resilience_gates(self) -> None:
        circuit = plan_circuit_breaker(
            {
                "service_name": "payments-api",
                "failure_threshold": 5,
                "reset_timeout_seconds": 30,
                "fallback": "cached-status",
                "metrics": ["error_rate", "open_circuit_count"],
            },
            {"max_failure_threshold": 10, "require_fallback": True, "require_metrics": True, "required_metrics": ["error_rate"]},
        )
        bad_circuit = plan_circuit_breaker(
            {"failure_threshold": 20},
            {"max_failure_threshold": 10, "require_fallback": True, "require_metrics": True, "required_metrics": ["error_rate"]},
        )
        retry = plan_retry_backoff_policy(
            {"operation_name": "sync invoice", "max_attempts": 3, "base_delay_ms": 100, "jitter": True, "backoff_strategy": "exponential", "idempotent": True},
            {"max_attempts": 3, "require_jitter": True, "forbid_non_idempotent_retries": True},
        )
        bad_retry = plan_retry_backoff_policy(
            {"max_attempts": 6, "base_delay_ms": 0, "jitter": False, "idempotent": False},
            {"max_attempts": 3, "require_jitter": True, "forbid_non_idempotent_retries": True},
        )

        self.assertTrue(circuit.ready)
        self.assertFalse(bad_circuit.ready)
        self.assertIn("missing_service_name", bad_circuit.blockers)
        self.assertIn("failure_threshold_exceeds_policy", bad_circuit.blockers)
        self.assertIn("missing_reset_timeout_seconds", bad_circuit.blockers)
        self.assertIn("missing_fallback", bad_circuit.blockers)
        self.assertIn("missing_metrics", bad_circuit.blockers)
        self.assertIn("missing_metric:error_rate", bad_circuit.blockers)
        self.assertTrue(retry.ready)
        self.assertFalse(bad_retry.ready)
        self.assertIn("missing_operation_name", bad_retry.blockers)
        self.assertIn("max_attempts_exceeds_policy", bad_retry.blockers)
        self.assertIn("missing_base_delay_ms", bad_retry.blockers)
        self.assertIn("missing_backoff_strategy", bad_retry.blockers)
        self.assertIn("missing_jitter", bad_retry.blockers)
        self.assertIn("non_idempotent_retry_forbidden", bad_retry.blockers)

    def test_plan_timeout_budget_and_concurrency_limit_enforce_resource_guards(self) -> None:
        timeout = plan_timeout_budget(
            {"operation_name": "search request", "total_timeout_ms": 900, "phase_budgets": {"connect": 100, "read": 500, "write": 100}},
            {"max_total_timeout_ms": 1000, "required_phases": ["connect", "read", "write"]},
        )
        bad_timeout = plan_timeout_budget(
            {"total_timeout_ms": 1000, "phase_budgets": {"connect": 800, "read": 400}},
            {"max_total_timeout_ms": 500, "required_phases": ["connect", "read", "write"]},
        )
        concurrency = plan_concurrency_limit(
            {"resource_name": "image worker", "max_concurrency": 20, "queue_limit": 200, "overflow_policy": "reject", "metrics": ["active_requests", "rejected_requests"]},
            {"max_concurrency": 50, "require_queue_limit": True, "require_overflow_policy": True, "required_metrics": ["active_requests", "rejected_requests"]},
        )
        bad_concurrency = plan_concurrency_limit(
            {"max_concurrency": 200, "metrics": ["active_requests"]},
            {"max_concurrency": 50, "require_queue_limit": True, "require_overflow_policy": True, "required_metrics": ["active_requests", "rejected_requests"]},
        )

        self.assertTrue(timeout.ready)
        self.assertFalse(bad_timeout.ready)
        self.assertIn("missing_operation_name", bad_timeout.blockers)
        self.assertIn("timeout_exceeds_policy", bad_timeout.blockers)
        self.assertIn("phase_budgets_exceed_total", bad_timeout.blockers)
        self.assertIn("missing_required_phase:write", bad_timeout.blockers)
        self.assertTrue(concurrency.ready)
        self.assertFalse(bad_concurrency.ready)
        self.assertIn("missing_resource_name", bad_concurrency.blockers)
        self.assertIn("max_concurrency_exceeds_policy", bad_concurrency.blockers)
        self.assertIn("missing_queue_limit", bad_concurrency.blockers)
        self.assertIn("missing_overflow_policy", bad_concurrency.blockers)
        self.assertIn("missing_metric:rejected_requests", bad_concurrency.blockers)

    def test_plan_health_probe_and_dependency_readiness_enforce_service_readiness(self) -> None:
        probes = plan_health_probe_contract(
            {
                "service_name": "orders-api",
                "readiness_path": "/ready",
                "liveness_path": "/live",
                "startup_probe": "/startup",
                "probe_timeout_ms": 500,
                "dependency_checks": ["postgres", "redis"],
            },
            {"require_startup_probe": True, "require_timeout": True, "max_probe_timeout_ms": 1000, "require_dependency_checks": True},
        )
        bad_probes = plan_health_probe_contract(
            {"probe_timeout_ms": 5000},
            {"require_startup_probe": True, "require_timeout": True, "max_probe_timeout_ms": 1000, "require_dependency_checks": True},
        )
        readiness = plan_dependency_readiness(
            {
                "service_name": "orders-api",
                "dependencies": [
                    {"name": "postgres", "critical": True, "healthcheck": "/ready", "timeout_ms": 500, "fallback": "read-only"},
                    {"name": "redis", "healthcheck": "PING"},
                ],
            },
            {"require_timeout_for_critical": True, "require_fallback_for_critical": True},
        )
        bad_readiness = plan_dependency_readiness(
            {"dependencies": [{"name": "postgres", "critical": True}, {"name": "cache", "healthcheck": ""}]},
            {"require_timeout_for_critical": True, "require_fallback_for_critical": True},
        )

        self.assertTrue(probes.ready)
        self.assertFalse(bad_probes.ready)
        self.assertIn("missing_service_name", bad_probes.blockers)
        self.assertIn("missing_readiness_path", bad_probes.blockers)
        self.assertIn("missing_liveness_path", bad_probes.blockers)
        self.assertIn("missing_startup_probe", bad_probes.blockers)
        self.assertIn("probe_timeout_exceeds_policy", bad_probes.blockers)
        self.assertIn("missing_dependency_checks", bad_probes.blockers)
        self.assertTrue(readiness.ready)
        self.assertFalse(bad_readiness.ready)
        self.assertIn("missing_service_name", bad_readiness.blockers)
        self.assertIn("postgres:missing_healthcheck", bad_readiness.blockers)
        self.assertIn("postgres:critical_dependency_without_timeout", bad_readiness.blockers)
        self.assertIn("postgres:missing_fallback", bad_readiness.blockers)
        self.assertIn("cache:missing_healthcheck", bad_readiness.blockers)

    def test_plan_graceful_shutdown_and_chaos_experiment_enforce_runtime_safety(self) -> None:
        shutdown = plan_graceful_shutdown(
            {"service_name": "orders-api", "drain_timeout_seconds": 20, "hooks": ["pre_stop", "flush_traces"], "signal_handler": True, "inflight_request_drain": True},
            {"max_drain_timeout_seconds": 30, "required_hooks": ["pre_stop", "flush_traces"], "require_signal_handler": True, "require_inflight_request_drain": True},
        )
        bad_shutdown = plan_graceful_shutdown(
            {"drain_timeout_seconds": 120, "hooks": ["pre_stop"]},
            {"max_drain_timeout_seconds": 30, "required_hooks": ["pre_stop", "flush_traces"], "require_signal_handler": True, "require_inflight_request_drain": True},
        )
        chaos = plan_chaos_experiment(
            {
                "experiment_name": "kill one pod",
                "target_service": "orders-api",
                "blast_radius": "pod",
                "hypothesis": "traffic retries without user-visible errors",
                "abort_condition": "error rate above threshold",
                "observability": ["latency", "error_rate"],
                "rollback": "restart deployment",
            },
            {"allowed_blast_radius": ["pod", "container"], "require_hypothesis": True, "require_abort_condition": True, "require_observability": True, "require_rollback": True},
        )
        bad_chaos = plan_chaos_experiment(
            {"blast_radius": "region"},
            {"allowed_blast_radius": ["pod", "container"], "require_hypothesis": True, "require_abort_condition": True, "require_observability": True, "require_rollback": True},
        )

        self.assertTrue(shutdown.ready)
        self.assertFalse(bad_shutdown.ready)
        self.assertIn("missing_service_name", bad_shutdown.blockers)
        self.assertIn("drain_timeout_exceeds_policy", bad_shutdown.blockers)
        self.assertIn("missing_hook:flush_traces", bad_shutdown.blockers)
        self.assertIn("missing_signal_handler", bad_shutdown.blockers)
        self.assertIn("missing_inflight_request_drain", bad_shutdown.blockers)
        self.assertTrue(chaos.ready)
        self.assertFalse(bad_chaos.ready)
        self.assertIn("missing_experiment_name", bad_chaos.blockers)
        self.assertIn("missing_target_service", bad_chaos.blockers)
        self.assertIn("blast_radius_not_allowed:region", bad_chaos.blockers)
        self.assertIn("missing_hypothesis", bad_chaos.blockers)
        self.assertIn("missing_abort_condition", bad_chaos.blockers)
        self.assertIn("missing_observability", bad_chaos.blockers)
        self.assertIn("missing_rollback", bad_chaos.blockers)

    def test_evaluate_openapi_compatibility_and_api_versioning_enforce_api_evolution_gates(self) -> None:
        compatible = evaluate_openapi_compatibility(
            {"version": "1.0.0", "paths": {"/customers": {"get": {"responses": {"200": {"schema": "CustomerPage"}}}}}},
            {"version": "1.1.0", "migration_notes": "Added optional create operation.", "paths": {"/customers": {"get": {"responses": {"200": {"schema": "CustomerPage"}}}, "post": {"responses": {"201": {"schema": "Customer"}}}}}},
            {"forbid_removed_paths": True, "forbid_removed_operations": True, "forbid_changed_operations": True, "require_version_bump": True, "require_migration_notes": True},
        )
        incompatible = evaluate_openapi_compatibility(
            {
                "version": "1.0.0",
                "paths": {
                    "/customers": {"get": {"responses": {"200": {"schema": "CustomerPage"}}}, "post": {"responses": {"201": {"schema": "Customer"}}}},
                    "/orders": {"get": {"responses": {"200": {"schema": "OrderPage"}}}},
                },
            },
            {"version": "1.0.0", "paths": {"/customers": {"get": {"responses": {"200": {"schema": "ChangedCustomerPage"}}}}}},
            {"forbid_removed_paths": True, "forbid_removed_operations": True, "forbid_changed_operations": True, "require_version_bump": True, "require_migration_notes": True},
        )
        versioning = plan_api_versioning_policy(
            {"api_name": "billing-api", "current_version": "1.2.0", "next_version": "2.0.0", "migration_plan": "v2 adapter", "changelog": "breaking auth scope", "compatibility_report": "openapi diff clean with migration"},
            {"require_migration_plan_for_major": True, "require_changelog": True, "require_compatibility_report": True},
        )
        bad_versioning = plan_api_versioning_policy(
            {"current_version": "2.0.0", "next_version": "1.9.0"},
            {"require_migration_plan_for_major": True, "require_changelog": True, "require_compatibility_report": True},
        )

        self.assertTrue(compatible.compatible)
        self.assertFalse(incompatible.compatible)
        self.assertEqual(incompatible.removed_paths, ("/orders",))
        self.assertIn("POST /customers", incompatible.removed_operations)
        self.assertIn("GET /customers", incompatible.changed_operations)
        self.assertIn("removed_paths", incompatible.blockers)
        self.assertIn("removed_operations", incompatible.blockers)
        self.assertIn("changed_operations", incompatible.blockers)
        self.assertIn("missing_version_bump", incompatible.blockers)
        self.assertIn("missing_migration_notes", incompatible.blockers)
        self.assertTrue(versioning.ready)
        self.assertFalse(bad_versioning.ready)
        self.assertIn("missing_api_name", bad_versioning.blockers)
        self.assertIn("version_not_incremented", bad_versioning.blockers)
        self.assertIn("missing_changelog", bad_versioning.blockers)
        self.assertIn("missing_compatibility_report", bad_versioning.blockers)

    def test_plan_api_deprecation_and_error_envelope_enforce_endpoint_contract_gates(self) -> None:
        deprecation = plan_api_deprecation_notice(
            {"endpoint_id": "POST /v1/invoices", "sunset_days": 180, "replacement_endpoint": "POST /v2/invoices", "docs_url": "https://docs.example.test/invoices-v2", "sunset_header": True},
            {"min_sunset_days": 90, "require_replacement": True, "require_docs_url": True, "require_sunset_header": True},
        )
        bad_deprecation = plan_api_deprecation_notice(
            {"sunset_days": 30},
            {"min_sunset_days": 90, "require_replacement": True, "require_docs_url": True, "require_sunset_header": True},
        )
        envelope = plan_error_envelope_contract(
            {"endpoint_id": "POST /v1/invoices", "error_schema": {"error_code": "string", "message": "string", "correlation_id": "string", "details": "object"}, "error_codes": ["invoice.invalid"]},
            {"required_fields": ["error_code", "message", "correlation_id"], "require_error_codes": True, "require_correlation_id": True},
        )
        bad_envelope = plan_error_envelope_contract(
            {"error_schema": {"error_code": "string"}},
            {"required_fields": ["error_code", "message", "correlation_id"], "require_error_codes": True, "require_correlation_id": True},
        )

        self.assertTrue(deprecation.ready)
        self.assertFalse(bad_deprecation.ready)
        self.assertIn("missing_endpoint_id", bad_deprecation.blockers)
        self.assertIn("sunset_window_too_short", bad_deprecation.blockers)
        self.assertIn("missing_replacement", bad_deprecation.blockers)
        self.assertIn("missing_docs_url", bad_deprecation.blockers)
        self.assertIn("missing_sunset_header", bad_deprecation.blockers)
        self.assertTrue(envelope.ready)
        self.assertFalse(bad_envelope.ready)
        self.assertIn("missing_endpoint_id", bad_envelope.blockers)
        self.assertIn("missing_required_field:message", bad_envelope.blockers)
        self.assertIn("missing_required_field:correlation_id", bad_envelope.blockers)
        self.assertIn("missing_error_codes", bad_envelope.blockers)
        self.assertIn("missing_correlation_id", bad_envelope.blockers)

    def test_plan_request_signing_and_api_usage_plan_enforce_consumer_safety_gates(self) -> None:
        signing = plan_request_signing_policy(
            {
                "endpoint_id": "POST /v1/webhooks/provider",
                "algorithm": "hmac-sha256",
                "required_headers": ["X-Signature", "X-Timestamp", "X-Nonce", "X-Client-Id"],
                "key_rotation": "30d",
                "replay_window_seconds": 300,
            },
            {
                "allowed_algorithms": ["hmac-sha256"],
                "required_headers": ["X-Signature", "X-Client-Id"],
                "require_timestamp": True,
                "timestamp_header": "X-Timestamp",
                "require_nonce": True,
                "nonce_header": "X-Nonce",
                "require_key_rotation": True,
                "max_replay_window_seconds": 300,
            },
        )
        bad_signing = plan_request_signing_policy(
            {"algorithm": "md5", "required_headers": ["X-Signature"], "replay_window_seconds": 600},
            {
                "allowed_algorithms": ["hmac-sha256"],
                "required_headers": ["X-Signature", "X-Client-Id"],
                "require_timestamp": True,
                "timestamp_header": "X-Timestamp",
                "require_nonce": True,
                "nonce_header": "X-Nonce",
                "require_key_rotation": True,
                "max_replay_window_seconds": 300,
            },
        )
        usage = plan_api_usage_plan(
            {"consumer_name": "partner-crm", "quota_limit": 5000, "period": "monthly", "burst_limit": 100, "scopes": ["invoice:read"], "alert_threshold_percent": 80},
            {"max_quota_limit": 10000, "allowed_periods": ["daily", "monthly"], "require_burst_limit": True, "require_scope": True, "require_alert_threshold": True},
        )
        bad_usage = plan_api_usage_plan(
            {"quota_limit": 20000, "period": "year"},
            {"max_quota_limit": 10000, "allowed_periods": ["daily", "monthly"], "require_burst_limit": True, "require_scope": True, "require_alert_threshold": True},
        )

        self.assertTrue(signing.ready)
        self.assertFalse(bad_signing.ready)
        self.assertIn("missing_endpoint_id", bad_signing.blockers)
        self.assertIn("algorithm_not_allowed:md5", bad_signing.blockers)
        self.assertIn("missing_header:X-Client-Id", bad_signing.blockers)
        self.assertIn("missing_timestamp_header", bad_signing.blockers)
        self.assertIn("missing_nonce_header", bad_signing.blockers)
        self.assertIn("missing_key_rotation", bad_signing.blockers)
        self.assertIn("replay_window_exceeds_policy", bad_signing.blockers)
        self.assertTrue(usage.ready)
        self.assertFalse(bad_usage.ready)
        self.assertIn("missing_consumer_name", bad_usage.blockers)
        self.assertIn("quota_exceeds_policy", bad_usage.blockers)
        self.assertIn("period_not_allowed:year", bad_usage.blockers)
        self.assertIn("missing_burst_limit", bad_usage.blockers)
        self.assertIn("missing_scope", bad_usage.blockers)
        self.assertIn("missing_alert_threshold", bad_usage.blockers)

    def test_plan_api_key_rotation_and_response_cache_enforce_runtime_policy_gates(self) -> None:
        rotation = plan_api_key_rotation(
            {"key_name": "partner-crm-key", "secret_ref": "secret://partner-crm", "rotation_days": 30, "overlap_window_days": 7, "revocation_plan": "revoke old key after overlap", "owner": "platform"},
            {"max_rotation_days": 90, "require_overlap_window": True, "max_overlap_window_days": 14, "require_revocation_plan": True, "require_owner": True},
        )
        bad_rotation = plan_api_key_rotation(
            {"rotation_days": 120, "overlap_window_days": 30},
            {"max_rotation_days": 90, "require_overlap_window": True, "max_overlap_window_days": 14, "require_revocation_plan": True, "require_owner": True},
        )
        cache = plan_response_cache_policy(
            {"endpoint_id": "GET /v1/invoices", "cache_ttl_seconds": 300, "vary_headers": ["Authorization", "Accept-Language"], "cache_scope": "private", "auth_context_key": "tenant_id", "invalidation_strategy": "invoice mutation topic"},
            {"max_cache_ttl_seconds": 600, "required_vary_headers": ["Authorization"], "require_invalidation_strategy": True, "require_auth_context_for_private": True},
        )
        bad_cache = plan_response_cache_policy(
            {"cache_ttl_seconds": 3600, "cache_scope": "private"},
            {"max_cache_ttl_seconds": 600, "required_vary_headers": ["Authorization"], "require_invalidation_strategy": True, "require_auth_context_for_private": True},
        )

        self.assertTrue(rotation.ready)
        self.assertFalse(bad_rotation.ready)
        self.assertIn("missing_key_name", bad_rotation.blockers)
        self.assertIn("missing_secret_ref", bad_rotation.blockers)
        self.assertIn("rotation_days_exceeds_policy", bad_rotation.blockers)
        self.assertIn("overlap_window_exceeds_policy", bad_rotation.blockers)
        self.assertIn("missing_revocation_plan", bad_rotation.blockers)
        self.assertIn("missing_owner", bad_rotation.blockers)
        self.assertTrue(cache.ready)
        self.assertFalse(bad_cache.ready)
        self.assertIn("missing_endpoint_id", bad_cache.blockers)
        self.assertIn("ttl_exceeds_policy", bad_cache.blockers)
        self.assertIn("missing_vary_header:Authorization", bad_cache.blockers)
        self.assertIn("missing_invalidation_strategy", bad_cache.blockers)
        self.assertIn("private_cache_missing_auth_context", bad_cache.blockers)

    def test_plan_api_request_validation_and_auth_scope_matrix_enforce_endpoint_gates(self) -> None:
        validation = plan_api_request_validation(
            {
                "endpoint_id": "POST /v1/invoices",
                "method": "POST",
                "content_types": ["application/json"],
                "request_schema": {"required": ["customer_id", "amount"], "properties": {"customer_id": {"type": "string"}, "amount": {"type": "number"}}},
                "unknown_field_policy": "reject",
                "max_body_bytes": 65536,
                "validation_receipt": "validation-receipt",
            },
            {
                "allowed_methods": ["POST"],
                "allowed_content_types": ["application/json"],
                "required_fields": ["customer_id", "amount"],
                "require_unknown_field_policy": True,
                "require_max_body_bytes": True,
                "max_body_bytes": 131072,
                "require_validation_receipt": True,
            },
        )
        bad_validation = plan_api_request_validation(
            {
                "method": "PUT",
                "content_types": ["text/plain"],
                "request_schema": {"required": ["customer_id"], "properties": {"customer_id": {"type": "string"}}},
                "max_body_bytes": 262144,
            },
            {
                "allowed_methods": ["POST"],
                "allowed_content_types": ["application/json"],
                "required_fields": ["customer_id", "amount"],
                "require_unknown_field_policy": True,
                "require_max_body_bytes": True,
                "max_body_bytes": 131072,
                "require_validation_receipt": True,
            },
        )
        scope_matrix = plan_api_auth_scope_matrix(
            {
                "endpoint_id": "POST /v1/invoices",
                "action": "invoice.create",
                "required_scopes": ["invoice:write"],
                "tenant_claims": ["tenant_id"],
                "role_mapping": {"billing_admin": ["invoice:write"]},
                "denied_case_examples": [{"role": "viewer", "status": 403}],
            },
            {
                "allowed_scopes": ["invoice:write", "invoice:read"],
                "required_tenant_claims": ["tenant_id"],
                "require_role_mapping": True,
                "require_denied_case_examples": True,
            },
        )
        bad_scope_matrix = plan_api_auth_scope_matrix(
            {"required_scopes": ["admin:wipe"], "tenant_claims": ["account_id"]},
            {
                "allowed_scopes": ["invoice:write"],
                "required_tenant_claims": ["tenant_id"],
                "require_role_mapping": True,
                "require_denied_case_examples": True,
            },
        )

        self.assertTrue(validation.ready)
        self.assertTrue(validation.validation_hash.startswith("api-request-validation:"))
        self.assertFalse(bad_validation.ready)
        self.assertIn("missing_endpoint_id", bad_validation.blockers)
        self.assertIn("method_not_allowed:PUT", bad_validation.blockers)
        self.assertIn("content_type_not_allowed:text/plain", bad_validation.blockers)
        self.assertIn("missing_required_field:amount", bad_validation.blockers)
        self.assertIn("field_not_in_schema:amount", bad_validation.blockers)
        self.assertIn("missing_unknown_field_policy", bad_validation.blockers)
        self.assertIn("max_body_exceeds_policy", bad_validation.blockers)
        self.assertIn("missing_validation_receipt", bad_validation.blockers)
        self.assertTrue(scope_matrix.ready)
        self.assertFalse(bad_scope_matrix.ready)
        self.assertIn("missing_endpoint_id", bad_scope_matrix.blockers)
        self.assertIn("missing_action", bad_scope_matrix.blockers)
        self.assertIn("scope_not_allowed:admin:wipe", bad_scope_matrix.blockers)
        self.assertIn("missing_tenant_claim:tenant_id", bad_scope_matrix.blockers)
        self.assertIn("missing_role_mapping", bad_scope_matrix.blockers)
        self.assertIn("missing_denied_case_examples", bad_scope_matrix.blockers)

    def test_plan_api_async_bulk_examples_and_telemetry_enforce_runtime_contracts(self) -> None:
        async_endpoint = plan_api_async_job_endpoint(
            {
                "endpoint_id": "POST /v1/report-runs",
                "job_id_field": "job_id",
                "status_endpoint": "GET /v1/report-runs/{job_id}",
                "completion_states": ["succeeded", "failed", "cancelled"],
                "cancel_endpoint": "DELETE /v1/report-runs/{job_id}",
                "result_ttl_seconds": 86400,
                "polling_guidance": "exponential backoff",
                "job_receipt": "job-receipt",
            },
            {
                "required_completion_states": ["succeeded", "failed"],
                "require_cancel_endpoint": True,
                "require_result_ttl": True,
                "max_result_ttl_seconds": 172800,
                "require_polling_guidance": True,
                "require_job_receipt": True,
            },
        )
        bad_async_endpoint = plan_api_async_job_endpoint(
            {"result_ttl_seconds": 604800, "completion_states": ["done"]},
            {
                "required_completion_states": ["succeeded", "failed"],
                "require_cancel_endpoint": True,
                "require_result_ttl": True,
                "max_result_ttl_seconds": 172800,
                "require_polling_guidance": True,
                "require_job_receipt": True,
            },
        )
        bulk = plan_api_bulk_operation(
            {
                "endpoint_id": "POST /v1/invoices/bulk",
                "max_batch_size": 500,
                "partial_failure_mode": "per_item",
                "idempotency_key_field": "request_id",
                "result_item_schema": {"invoice_id": "string", "status": "string"},
                "per_item_error_schema": {"error_code": "string", "row_index": "integer"},
                "atomicity_policy": "per-item",
            },
            {
                "max_batch_size": 1000,
                "allowed_partial_failure_modes": ["per_item", "atomic"],
                "require_idempotency_key_field": True,
                "require_result_item_schema": True,
                "require_per_item_error_schema": True,
                "require_atomicity_policy": True,
            },
        )
        bad_bulk = plan_api_bulk_operation(
            {"max_batch_size": 5000, "partial_failure_mode": "silent_drop"},
            {
                "max_batch_size": 1000,
                "allowed_partial_failure_modes": ["per_item", "atomic"],
                "require_idempotency_key_field": True,
                "require_result_item_schema": True,
                "require_per_item_error_schema": True,
                "require_atomicity_policy": True,
            },
        )
        examples = plan_api_operation_example_coverage(
            {
                "endpoint_id": "POST /v1/invoices",
                "examples": [
                    {"status_code": "201", "type": "success", "request": {"amount": 10}, "response": {"invoice_id": "inv-1"}},
                    {"status_code": "400", "type": "validation_error", "request": {}, "response": {"error_code": "invoice.invalid"}},
                    {"status_code": "401", "type": "auth_error", "response": {"error_code": "auth.required"}},
                ],
            },
            {
                "required_status_codes": ["201", "400", "401"],
                "required_example_types": ["success", "validation_error", "auth_error"],
                "require_request_example": True,
                "require_response_example": True,
            },
        )
        bad_examples = plan_api_operation_example_coverage(
            {"examples": [{"status_code": "201", "type": "success", "request": {"amount": 10}}]},
            {
                "required_status_codes": ["201", "400"],
                "required_example_types": ["success", "validation_error"],
                "require_request_example": True,
                "require_response_example": True,
            },
        )
        telemetry = plan_api_endpoint_telemetry(
            {
                "endpoint_id": "POST /v1/invoices",
                "span_name": "api.invoice.create",
                "metrics": ["http.server.duration", "http.server.request.count"],
                "trace_context": True,
                "latency_bucket_policy": "standard-http",
                "log_fields": ["request_id", "email"],
                "attribute_fields": ["tenant_id"],
                "redacted_fields": ["email"],
            },
            {
                "require_span_name": True,
                "required_metrics": ["http.server.duration", "http.server.request.count"],
                "require_trace_context": True,
                "require_latency_buckets": True,
                "sensitive_fields": ["email", "ssn"],
            },
        )
        bad_telemetry = plan_api_endpoint_telemetry(
            {"endpoint_id": "POST /v1/invoices", "metrics": ["http.server.request.count"], "log_fields": ["email"]},
            {
                "require_span_name": True,
                "required_metrics": ["http.server.duration", "http.server.request.count"],
                "require_trace_context": True,
                "require_latency_buckets": True,
                "sensitive_fields": ["email"],
            },
        )

        self.assertTrue(async_endpoint.ready)
        self.assertFalse(bad_async_endpoint.ready)
        self.assertIn("missing_endpoint_id", bad_async_endpoint.blockers)
        self.assertIn("missing_job_id_field", bad_async_endpoint.blockers)
        self.assertIn("missing_status_endpoint", bad_async_endpoint.blockers)
        self.assertIn("missing_completion_state:succeeded", bad_async_endpoint.blockers)
        self.assertIn("missing_completion_state:failed", bad_async_endpoint.blockers)
        self.assertIn("missing_cancel_endpoint", bad_async_endpoint.blockers)
        self.assertIn("result_ttl_exceeds_policy", bad_async_endpoint.blockers)
        self.assertIn("missing_polling_guidance", bad_async_endpoint.blockers)
        self.assertIn("missing_job_receipt", bad_async_endpoint.blockers)
        self.assertTrue(bulk.ready)
        self.assertFalse(bad_bulk.ready)
        self.assertIn("missing_endpoint_id", bad_bulk.blockers)
        self.assertIn("max_batch_size_exceeds_policy", bad_bulk.blockers)
        self.assertIn("partial_failure_mode_not_allowed:silent_drop", bad_bulk.blockers)
        self.assertIn("missing_idempotency_key_field", bad_bulk.blockers)
        self.assertIn("missing_result_item_schema", bad_bulk.blockers)
        self.assertIn("missing_per_item_error_schema", bad_bulk.blockers)
        self.assertIn("missing_atomicity_policy", bad_bulk.blockers)
        self.assertTrue(examples.ready)
        self.assertEqual(examples.covered_status_codes, ("201", "400", "401"))
        self.assertFalse(bad_examples.ready)
        self.assertIn("missing_endpoint_id", bad_examples.blockers)
        self.assertIn("missing_status_example:400", bad_examples.blockers)
        self.assertIn("missing_example_type:validation_error", bad_examples.blockers)
        self.assertIn("missing_response_example", bad_examples.blockers)
        self.assertTrue(telemetry.ready)
        self.assertFalse(bad_telemetry.ready)
        self.assertIn("missing_span_name", bad_telemetry.blockers)
        self.assertIn("missing_metric:http.server.duration", bad_telemetry.blockers)
        self.assertIn("missing_trace_context", bad_telemetry.blockers)
        self.assertIn("missing_latency_bucket_policy", bad_telemetry.blockers)
        self.assertIn("missing_redaction_for_field:email", bad_telemetry.blockers)

    def test_plan_cdc_capture_and_stream_watermark_enforce_streaming_guards(self) -> None:
        cdc = plan_cdc_capture(
            {
                "source_name": "orders-db",
                "cursor_field": "updated_at",
                "primary_key_fields": ["tenant_id", "order_id"],
                "observed_lag_seconds": 30,
                "initial_snapshot": "snapshot-001",
                "checkpoint": "lsn:123",
                "schema_registry": "registry://orders",
            },
            {"max_lag_seconds": 60, "require_initial_snapshot": True, "require_checkpoint": True, "require_schema_registry": True},
        )
        bad_cdc = plan_cdc_capture(
            {"observed_lag_seconds": 120},
            {"max_lag_seconds": 60, "require_initial_snapshot": True, "require_checkpoint": True, "require_schema_registry": True},
        )
        watermark = plan_stream_watermark(
            {
                "stream_name": "order-events",
                "event_time_field": "occurred_at",
                "watermark_strategy": "bounded_out_of_orderness",
                "allowed_lateness_seconds": 120,
                "late_event_sink": "s3://late-events",
                "clock_skew_policy": "ntp drift under 5s",
            },
            {"max_allowed_lateness_seconds": 300, "require_late_event_sink": True, "require_clock_skew_policy": True},
        )
        bad_watermark = plan_stream_watermark(
            {"allowed_lateness_seconds": 600},
            {"max_allowed_lateness_seconds": 300, "require_late_event_sink": True, "require_clock_skew_policy": True},
        )

        self.assertTrue(cdc.ready)
        self.assertFalse(bad_cdc.ready)
        self.assertIn("missing_source_name", bad_cdc.blockers)
        self.assertIn("missing_cursor_field", bad_cdc.blockers)
        self.assertIn("missing_primary_key_fields", bad_cdc.blockers)
        self.assertIn("lag_exceeds_policy", bad_cdc.blockers)
        self.assertIn("missing_initial_snapshot", bad_cdc.blockers)
        self.assertIn("missing_checkpoint", bad_cdc.blockers)
        self.assertIn("missing_schema_registry", bad_cdc.blockers)
        self.assertTrue(watermark.ready)
        self.assertFalse(bad_watermark.ready)
        self.assertIn("missing_stream_name", bad_watermark.blockers)
        self.assertIn("missing_event_time_field", bad_watermark.blockers)
        self.assertIn("missing_watermark_strategy", bad_watermark.blockers)
        self.assertIn("lateness_exceeds_policy", bad_watermark.blockers)
        self.assertIn("missing_late_event_sink", bad_watermark.blockers)
        self.assertIn("missing_clock_skew_policy", bad_watermark.blockers)

    def test_plan_partition_strategy_and_data_lineage_contract_enforce_dataset_edges(self) -> None:
        partition = plan_partition_strategy(
            {"dataset_name": "order facts", "partition_fields": ["tenant_id", "event_date"], "retention_days": 90, "hot_partition_guard": "hash tenant", "compaction_policy": "daily"},
            {"allowed_partition_fields": ["tenant_id", "event_date"], "require_retention": True, "max_retention_days": 365, "require_hot_partition_guard": True, "require_compaction_policy": True},
        )
        bad_partition = plan_partition_strategy(
            {"partition_fields": ["region"], "retention_days": 730},
            {"allowed_partition_fields": ["tenant_id", "event_date"], "require_retention": True, "max_retention_days": 365, "require_hot_partition_guard": True, "require_compaction_policy": True},
        )
        lineage = plan_data_lineage_contract(
            {
                "dataset_name": "order facts",
                "inputs": ["orders.raw", "customers.dim"],
                "outputs": ["warehouse.order_facts"],
                "owner": "data-platform",
                "column_lineage": {"order_id": "orders.raw.order_id"},
                "run_id": "run-001",
                "source_freshness_ref": "freshness://orders.raw",
            },
            {"require_owner": True, "require_column_lineage": True, "require_run_id": True, "require_source_freshness_ref": True},
        )
        bad_lineage = plan_data_lineage_contract(
            {"inputs": [], "outputs": []},
            {"require_owner": True, "require_column_lineage": True, "require_run_id": True, "require_source_freshness_ref": True},
        )

        self.assertTrue(partition.ready)
        self.assertFalse(bad_partition.ready)
        self.assertIn("missing_dataset_name", bad_partition.blockers)
        self.assertIn("partition_field_not_allowed:region", bad_partition.blockers)
        self.assertIn("retention_exceeds_policy", bad_partition.blockers)
        self.assertIn("missing_hot_partition_guard", bad_partition.blockers)
        self.assertIn("missing_compaction_policy", bad_partition.blockers)
        self.assertTrue(lineage.ready)
        self.assertFalse(bad_lineage.ready)
        self.assertIn("missing_dataset_name", bad_lineage.blockers)
        self.assertIn("missing_inputs", bad_lineage.blockers)
        self.assertIn("missing_outputs", bad_lineage.blockers)
        self.assertIn("missing_owner", bad_lineage.blockers)
        self.assertIn("missing_column_lineage", bad_lineage.blockers)
        self.assertIn("missing_run_id", bad_lineage.blockers)
        self.assertIn("missing_source_freshness_ref", bad_lineage.blockers)

    def test_plan_outbox_publication_and_inbox_deduplication_enforce_event_delivery_guards(self) -> None:
        outbox = plan_outbox_publication(
            {
                "aggregate_name": "invoice",
                "event_topic": "invoice.events",
                "outbox_table": "invoice_outbox",
                "transaction_boundary": "same db transaction",
                "idempotency_key": "event_id",
                "poller_checkpoint": "lsn cursor",
                "publish_receipt": "event receipt",
                "retry_policy": "exponential",
            },
            {"require_transaction_boundary": True, "require_idempotency_key": True, "require_poller_checkpoint": True, "require_publish_receipt": True, "require_retry_policy": True},
        )
        bad_outbox = plan_outbox_publication(
            {"aggregate_name": "", "event_topic": "", "outbox_table": ""},
            {"require_transaction_boundary": True, "require_idempotency_key": True, "require_poller_checkpoint": True, "require_publish_receipt": True, "require_retry_policy": True},
        )
        inbox = plan_inbox_deduplication(
            {"consumer_name": "invoice-ledger", "dedupe_key": "event_id", "ttl_seconds": 86400, "conflict_action": "return_processed_receipt", "processed_receipt": "ledger receipt", "replay_guard": "source offset"},
            {"max_ttl_seconds": 172800, "require_conflict_action": True, "require_processed_receipt": True, "require_replay_guard": True},
        )
        bad_inbox = plan_inbox_deduplication(
            {"ttl_seconds": 999999},
            {"max_ttl_seconds": 172800, "require_conflict_action": True, "require_processed_receipt": True, "require_replay_guard": True},
        )

        self.assertTrue(outbox.ready)
        self.assertFalse(bad_outbox.ready)
        self.assertIn("missing_aggregate_name", bad_outbox.blockers)
        self.assertIn("missing_event_topic", bad_outbox.blockers)
        self.assertIn("missing_outbox_table", bad_outbox.blockers)
        self.assertIn("missing_transaction_boundary", bad_outbox.blockers)
        self.assertIn("missing_idempotency_key", bad_outbox.blockers)
        self.assertIn("missing_poller_checkpoint", bad_outbox.blockers)
        self.assertIn("missing_publish_receipt", bad_outbox.blockers)
        self.assertIn("missing_retry_policy", bad_outbox.blockers)
        self.assertTrue(inbox.ready)
        self.assertFalse(bad_inbox.ready)
        self.assertIn("missing_consumer_name", bad_inbox.blockers)
        self.assertIn("missing_dedupe_key", bad_inbox.blockers)
        self.assertIn("ttl_exceeds_policy", bad_inbox.blockers)
        self.assertIn("missing_conflict_action", bad_inbox.blockers)
        self.assertIn("missing_processed_receipt", bad_inbox.blockers)
        self.assertIn("missing_replay_guard", bad_inbox.blockers)

    def test_plan_materialized_view_refresh_and_data_quarantine_enforce_data_ops_gates(self) -> None:
        refresh = plan_materialized_view_refresh(
            {
                "view_name": "daily_revenue_mv",
                "refresh_strategy": "incremental",
                "max_staleness_seconds": 900,
                "dependency_tables": ["invoice_facts", "payment_facts"],
                "backfill_plan": "range backfill",
                "swap_strategy": "atomic rename",
            },
            {"allowed_refresh_strategies": ["incremental", "full"], "max_staleness_seconds": 1800, "require_dependency_tables": True, "require_backfill_plan": True, "require_swap_strategy": True},
        )
        bad_refresh = plan_materialized_view_refresh(
            {"refresh_strategy": "unsafe", "max_staleness_seconds": 7200},
            {"allowed_refresh_strategies": ["incremental", "full"], "max_staleness_seconds": 1800, "require_dependency_tables": True, "require_backfill_plan": True, "require_swap_strategy": True},
        )
        quarantine = plan_data_quarantine_policy(
            {"dataset_name": "customer_import", "finding_count": 3, "quarantine_sink": "s3://quarantine", "triage_owner": "data-quality", "release_criteria": "all findings remediated", "audit_receipt": "audit-123"},
            {"require_triage_owner": True, "require_release_criteria": True, "require_audit_receipt": True},
        )
        bad_quarantine = plan_data_quarantine_policy(
            {},
            {"require_triage_owner": True, "require_release_criteria": True, "require_audit_receipt": True},
        )

        self.assertTrue(refresh.ready)
        self.assertFalse(bad_refresh.ready)
        self.assertIn("missing_view_name", bad_refresh.blockers)
        self.assertIn("refresh_strategy_not_allowed:unsafe", bad_refresh.blockers)
        self.assertIn("staleness_exceeds_policy", bad_refresh.blockers)
        self.assertIn("missing_dependency_tables", bad_refresh.blockers)
        self.assertIn("missing_backfill_plan", bad_refresh.blockers)
        self.assertIn("missing_swap_strategy", bad_refresh.blockers)
        self.assertTrue(quarantine.ready)
        self.assertFalse(bad_quarantine.ready)
        self.assertIn("missing_dataset_name", bad_quarantine.blockers)
        self.assertIn("missing_findings", bad_quarantine.blockers)
        self.assertIn("missing_quarantine_sink", bad_quarantine.blockers)
        self.assertIn("missing_triage_owner", bad_quarantine.blockers)
        self.assertIn("missing_release_criteria", bad_quarantine.blockers)
        self.assertIn("missing_audit_receipt", bad_quarantine.blockers)

    def test_plan_task_lease_and_worker_heartbeat_enforce_worker_liveness(self) -> None:
        lease = plan_task_lease(
            {"worker_name": "email-worker", "lease_ttl_seconds": 60, "renewal_interval_seconds": 15, "owner_token": "owner-1", "fencing_token": "fence-1"},
            {"max_lease_ttl_seconds": 120, "require_renewal": True, "require_owner_token": True, "require_fencing_token": True},
        )
        bad_lease = plan_task_lease(
            {"lease_ttl_seconds": 300, "renewal_interval_seconds": 300},
            {"max_lease_ttl_seconds": 120, "require_renewal": True, "require_owner_token": True, "require_fencing_token": True},
        )
        heartbeat = plan_worker_heartbeat(
            {"worker_name": "email-worker", "heartbeat_interval_seconds": 10, "stale_after_seconds": 45, "liveness_topic": "workers.heartbeat", "restart_policy": "restart-stale"},
            {"max_heartbeat_interval_seconds": 30, "require_liveness_topic": True, "require_restart_policy": True},
        )
        bad_heartbeat = plan_worker_heartbeat(
            {"heartbeat_interval_seconds": 60, "stale_after_seconds": 30},
            {"max_heartbeat_interval_seconds": 30, "require_liveness_topic": True, "require_restart_policy": True},
        )

        self.assertTrue(lease.ready)
        self.assertFalse(bad_lease.ready)
        self.assertIn("missing_worker_name", bad_lease.blockers)
        self.assertIn("lease_ttl_exceeds_policy", bad_lease.blockers)
        self.assertIn("renewal_interval_not_less_than_ttl", bad_lease.blockers)
        self.assertIn("missing_owner_token", bad_lease.blockers)
        self.assertIn("missing_fencing_token", bad_lease.blockers)
        self.assertTrue(heartbeat.ready)
        self.assertFalse(bad_heartbeat.ready)
        self.assertIn("missing_worker_name", bad_heartbeat.blockers)
        self.assertIn("heartbeat_interval_exceeds_policy", bad_heartbeat.blockers)
        self.assertIn("stale_after_not_greater_than_heartbeat", bad_heartbeat.blockers)
        self.assertIn("missing_liveness_topic", bad_heartbeat.blockers)
        self.assertIn("missing_restart_policy", bad_heartbeat.blockers)

    def test_plan_queue_visibility_and_cron_catchup_enforce_retry_timing(self) -> None:
        visibility = plan_queue_visibility_timeout(
            {"queue_name": "email-jobs", "visibility_timeout_seconds": 120, "max_processing_seconds": 90, "extension_policy": "extend-on-progress", "dead_letter_queue": "email-jobs-dlq"},
            {"max_visibility_timeout_seconds": 300, "require_extension_policy": True, "require_dlq": True},
        )
        bad_visibility = plan_queue_visibility_timeout(
            {"visibility_timeout_seconds": 30, "max_processing_seconds": 90},
            {"max_visibility_timeout_seconds": 300, "require_extension_policy": True, "require_dlq": True},
        )
        catchup = plan_cron_catchup_window(
            {"job_name": "daily-report", "catchup_window_minutes": 120, "max_catchup_runs": 3, "misfire_policy": "run-latest", "idempotency_key": "report-date"},
            {"max_catchup_window_minutes": 240, "max_catchup_runs": 5, "require_misfire_policy": True, "require_idempotency_key": True},
        )
        bad_catchup = plan_cron_catchup_window(
            {"catchup_window_minutes": 500, "max_catchup_runs": 10},
            {"max_catchup_window_minutes": 240, "max_catchup_runs": 5, "require_misfire_policy": True, "require_idempotency_key": True},
        )

        self.assertTrue(visibility.ready)
        self.assertFalse(bad_visibility.ready)
        self.assertIn("missing_queue_name", bad_visibility.blockers)
        self.assertIn("visibility_timeout_less_than_processing_time", bad_visibility.blockers)
        self.assertIn("missing_extension_policy", bad_visibility.blockers)
        self.assertIn("missing_dlq", bad_visibility.blockers)
        self.assertTrue(catchup.ready)
        self.assertFalse(bad_catchup.ready)
        self.assertIn("missing_job_name", bad_catchup.blockers)
        self.assertIn("catchup_window_exceeds_policy", bad_catchup.blockers)
        self.assertIn("max_catchup_runs_exceeds_policy", bad_catchup.blockers)
        self.assertIn("missing_misfire_policy", bad_catchup.blockers)
        self.assertIn("missing_idempotency_key", bad_catchup.blockers)

    def test_plan_workflow_compensation_and_batch_checkpoint_enforce_recoverability(self) -> None:
        compensation = plan_workflow_compensation(
            {
                "workflow_name": "invoice-approval",
                "steps": ["reserve_credit", "create_invoice"],
                "compensating_steps": ["reserve_credit", "create_invoice"],
                "reverse_order": True,
                "compensation_receipt": "receipt://invoice-comp",
                "failure_boundary": "after_each_step",
            },
            {"require_compensation_for_each_step": True, "require_reverse_order": True, "require_compensation_receipt": True, "require_failure_boundary": True},
        )
        bad_compensation = plan_workflow_compensation(
            {"steps": ["reserve_credit", "create_invoice"], "compensating_steps": ["reserve_credit"]},
            {"require_compensation_for_each_step": True, "require_reverse_order": True, "require_compensation_receipt": True, "require_failure_boundary": True},
        )
        checkpoint = plan_batch_checkpoint(
            {"job_name": "invoice-backfill", "checkpoint_interval_records": 1000, "checkpoint_store": "s3://checkpoints", "resume_token": "page-token", "checksum": "sha256:abc", "progress_receipt": "receipt://progress"},
            {"max_checkpoint_interval_records": 5000, "require_resume_token": True, "require_checksum": True, "require_progress_receipt": True},
        )
        bad_checkpoint = plan_batch_checkpoint(
            {"checkpoint_interval_records": 10000},
            {"max_checkpoint_interval_records": 5000, "require_resume_token": True, "require_checksum": True, "require_progress_receipt": True},
        )

        self.assertTrue(compensation.ready)
        self.assertFalse(bad_compensation.ready)
        self.assertIn("missing_workflow_name", bad_compensation.blockers)
        self.assertIn("missing_compensation_for_step:create_invoice", bad_compensation.blockers)
        self.assertIn("missing_reverse_order", bad_compensation.blockers)
        self.assertIn("missing_compensation_receipt", bad_compensation.blockers)
        self.assertIn("missing_failure_boundary", bad_compensation.blockers)
        self.assertTrue(checkpoint.ready)
        self.assertFalse(bad_checkpoint.ready)
        self.assertIn("missing_job_name", bad_checkpoint.blockers)
        self.assertIn("checkpoint_interval_exceeds_policy", bad_checkpoint.blockers)
        self.assertIn("missing_checkpoint_store", bad_checkpoint.blockers)
        self.assertIn("missing_resume_token", bad_checkpoint.blockers)
        self.assertIn("missing_checksum", bad_checkpoint.blockers)
        self.assertIn("missing_progress_receipt", bad_checkpoint.blockers)

    def test_plan_run_artifact_manifest_and_execution_audit_trail_enforce_run_evidence(self) -> None:
        manifest = plan_run_artifact_manifest(
            {
                "run_id": "run-001",
                "artifacts": [{"name": "summary.json", "digest": "sha256:abc", "content_type": "application/json"}],
                "retention_days": 30,
                "owner": "platform",
            },
            {"require_digest": True, "require_content_type": True, "require_retention_days": True, "require_owner": True},
        )
        bad_manifest = plan_run_artifact_manifest(
            {"artifacts": [{"name": "summary.json"}]},
            {"require_digest": True, "require_content_type": True, "require_retention_days": True, "require_owner": True},
        )
        audit = plan_execution_audit_trail(
            {
                "operation_name": "invoice import",
                "audit_events": ["started", "succeeded", "failed"],
                "actor_field": "actor_id",
                "trace_id_field": "trace_id",
                "audit_sink": "audit.log",
                "retention_days": 365,
            },
            {"required_events": ["started", "succeeded", "failed"], "require_actor": True, "require_trace_id": True, "require_audit_sink": True, "require_retention_days": True},
        )
        bad_audit = plan_execution_audit_trail(
            {"audit_events": ["started"]},
            {"required_events": ["started", "succeeded", "failed"], "require_actor": True, "require_trace_id": True, "require_audit_sink": True, "require_retention_days": True},
        )

        self.assertTrue(manifest.ready)
        self.assertFalse(bad_manifest.ready)
        self.assertIn("missing_run_id", bad_manifest.blockers)
        self.assertIn("artifact_1_missing_digest", bad_manifest.blockers)
        self.assertIn("artifact_1_missing_content_type", bad_manifest.blockers)
        self.assertIn("missing_retention_days", bad_manifest.blockers)
        self.assertIn("missing_owner", bad_manifest.blockers)
        self.assertTrue(audit.ready)
        self.assertFalse(bad_audit.ready)
        self.assertIn("missing_operation_name", bad_audit.blockers)
        self.assertIn("missing_event:succeeded", bad_audit.blockers)
        self.assertIn("missing_event:failed", bad_audit.blockers)
        self.assertIn("missing_actor_field", bad_audit.blockers)
        self.assertIn("missing_trace_id_field", bad_audit.blockers)
        self.assertIn("missing_audit_sink", bad_audit.blockers)
        self.assertIn("missing_retention_days", bad_audit.blockers)

    def test_plan_api_gateway_route_and_service_discovery_enforce_surface_routing(self) -> None:
        route = plan_api_gateway_route(
            {
                "route_id": "customer-create",
                "route_path": "/v1/customers",
                "upstream_service": "customer-service",
                "methods": ["POST"],
                "auth_policy": "tenant-jwt",
                "rate_limit_policy": "1000/min",
                "timeout_policy": "2s",
            },
            {"allowed_methods": ["GET", "POST"], "require_auth_policy": True, "require_rate_limit_policy": True, "require_timeout_policy": True},
        )
        bad_route = plan_api_gateway_route(
            {"route_path": "v1/customers", "methods": ["TRACE"]},
            {"allowed_methods": ["GET", "POST"], "require_auth_policy": True, "require_rate_limit_policy": True, "require_timeout_policy": True},
        )
        discovery = plan_service_discovery_registration(
            {"service_name": "customer-service", "endpoints": [{"url": "http://customer:8080"}], "health_check_path": "/healthz", "ttl_seconds": 30, "region": "us-east-1"},
            {"require_health_check_path": True, "require_ttl_seconds": True, "max_ttl_seconds": 60, "require_region": True},
        )
        bad_discovery = plan_service_discovery_registration(
            {"endpoints": [{"name": "customer"}], "ttl_seconds": 120},
            {"require_health_check_path": True, "require_ttl_seconds": True, "max_ttl_seconds": 60, "require_region": True},
        )

        self.assertTrue(route.ready)
        self.assertFalse(bad_route.ready)
        self.assertIn("missing_route_id", bad_route.blockers)
        self.assertIn("route_path_must_start_with_slash", bad_route.blockers)
        self.assertIn("missing_upstream_service", bad_route.blockers)
        self.assertIn("method_not_allowed:TRACE", bad_route.blockers)
        self.assertIn("missing_auth_policy", bad_route.blockers)
        self.assertIn("missing_rate_limit_policy", bad_route.blockers)
        self.assertIn("missing_timeout_policy", bad_route.blockers)
        self.assertTrue(discovery.ready)
        self.assertFalse(bad_discovery.ready)
        self.assertIn("missing_service_name", bad_discovery.blockers)
        self.assertIn("missing_endpoints", bad_discovery.blockers)
        self.assertIn("endpoint_1_missing_url", bad_discovery.blockers)
        self.assertIn("missing_health_check_path", bad_discovery.blockers)
        self.assertIn("ttl_exceeds_policy", bad_discovery.blockers)
        self.assertIn("missing_region", bad_discovery.blockers)

    def test_plan_service_dependency_and_runtime_config_enforce_service_boundaries(self) -> None:
        dependency = plan_service_dependency_contract(
            {
                "service_name": "billing-service",
                "owner": "platform",
                "dependencies": [{"name": "ledger-service", "timeout_ms": 250, "fallback": "queue-command", "circuit_breaker": "ledger-cb"}],
            },
            {"require_timeout": True, "require_fallback": True, "require_circuit_breaker": True, "require_owner": True},
        )
        bad_dependency = plan_service_dependency_contract(
            {"dependencies": [{"service": "ledger-service"}]},
            {"require_timeout": True, "require_fallback": True, "require_circuit_breaker": True, "require_owner": True},
        )
        config = plan_runtime_config_schema(
            {
                "service_name": "billing-service",
                "config": {"database_url": "postgres://db", "api_token": "secret://billing/api-token"},
                "secret_keys": ["api_token"],
                "schema_version": "1.0.0",
                "owner": "platform",
            },
            {"required_keys": ["database_url"], "required_secret_keys": ["api_token"], "forbid_plaintext_secret_values": True, "require_schema_version": True, "require_owner": True},
        )
        bad_config = plan_runtime_config_schema(
            {"config": {"api_token": "plain-token"}, "secret_keys": ["api_token"]},
            {"required_keys": ["database_url"], "required_secret_keys": ["api_token"], "forbid_plaintext_secret_values": True, "require_schema_version": True, "require_owner": True},
        )

        self.assertTrue(dependency.ready)
        self.assertFalse(bad_dependency.ready)
        self.assertIn("missing_service_name", bad_dependency.blockers)
        self.assertIn("dependency_1_missing_timeout", bad_dependency.blockers)
        self.assertIn("missing_fallback_for_dependency:ledger_service", bad_dependency.blockers)
        self.assertIn("missing_circuit_breaker_for_dependency:ledger_service", bad_dependency.blockers)
        self.assertIn("missing_owner", bad_dependency.blockers)
        self.assertTrue(config.ready)
        self.assertFalse(bad_config.ready)
        self.assertIn("missing_service_name", bad_config.blockers)
        self.assertIn("missing_key:database_url", bad_config.blockers)
        self.assertIn("plaintext_secret_key:api_token", bad_config.blockers)
        self.assertIn("missing_schema_version", bad_config.blockers)
        self.assertIn("missing_owner", bad_config.blockers)

    def test_plan_environment_promotion_and_webhook_delivery_enforce_release_edges(self) -> None:
        promotion = plan_environment_promotion(
            {
                "service_name": "billing-service",
                "source_environment": "staging",
                "target_environment": "production",
                "artifact_digest": "sha256:abc",
                "migration_plan": "expand-contract",
                "rollback_plan": "previous image",
                "approval": "change-123",
            },
            {"allowed_pairs": [{"source": "staging", "target": "production"}], "require_artifact_digest": True, "require_migration_plan": True, "require_rollback_plan": True, "require_approval": True},
        )
        bad_promotion = plan_environment_promotion(
            {"source_environment": "dev", "target_environment": "production"},
            {"allowed_pairs": [{"source": "staging", "target": "production"}], "require_artifact_digest": True, "require_migration_plan": True, "require_rollback_plan": True, "require_approval": True},
        )
        delivery = plan_webhook_delivery_policy(
            {
                "webhook_name": "invoice-paid",
                "destination_url": "https://example.test/webhooks/invoice-paid",
                "retry_attempts": 5,
                "signing_secret_ref": "secret://webhooks/invoice-paid",
                "idempotency_key": "event_id",
                "dead_letter_sink": "webhook-dlq",
            },
            {"require_https": True, "require_signing_secret_ref": True, "require_idempotency_key": True, "max_retry_attempts": 8, "require_dead_letter_sink": True},
        )
        bad_delivery = plan_webhook_delivery_policy(
            {"destination_url": "http://example.test/webhooks", "retry_attempts": 12},
            {"require_https": True, "require_signing_secret_ref": True, "require_idempotency_key": True, "max_retry_attempts": 8, "require_dead_letter_sink": True},
        )

        self.assertTrue(promotion.ready)
        self.assertFalse(bad_promotion.ready)
        self.assertIn("missing_service_name", bad_promotion.blockers)
        self.assertIn("promotion_pair_not_allowed", bad_promotion.blockers)
        self.assertIn("missing_artifact_digest", bad_promotion.blockers)
        self.assertIn("missing_migration_plan", bad_promotion.blockers)
        self.assertIn("missing_rollback_plan", bad_promotion.blockers)
        self.assertIn("missing_approval", bad_promotion.blockers)
        self.assertTrue(delivery.ready)
        self.assertFalse(bad_delivery.ready)
        self.assertIn("missing_webhook_name", bad_delivery.blockers)
        self.assertIn("destination_url_must_be_https", bad_delivery.blockers)
        self.assertIn("missing_signing_secret_ref", bad_delivery.blockers)
        self.assertIn("missing_idempotency_key", bad_delivery.blockers)
        self.assertIn("retry_attempts_exceed_policy", bad_delivery.blockers)
        self.assertIn("missing_dead_letter_sink", bad_delivery.blockers)

    def test_plan_consumer_group_offset_and_service_ownership_enforce_ops_evidence(self) -> None:
        offset = plan_consumer_group_offset(
            {
                "consumer_group": "billing-ledger",
                "topic_name": "invoice.events",
                "offset_strategy": "commit_after_receipt",
                "checkpoint_store": "redis://offsets",
                "replay_policy": "bounded-replay",
                "lag_alert_threshold": 1000,
            },
            {"allowed_offset_strategies": ["commit_after_receipt", "manual"], "require_checkpoint_store": True, "require_replay_policy": True, "require_lag_alert_threshold": True, "max_lag_alert_threshold": 5000},
        )
        bad_offset = plan_consumer_group_offset(
            {"offset_strategy": "auto", "lag_alert_threshold": 9000},
            {"allowed_offset_strategies": ["commit_after_receipt", "manual"], "require_checkpoint_store": True, "require_replay_policy": True, "require_lag_alert_threshold": True, "max_lag_alert_threshold": 5000},
        )
        ownership = plan_service_ownership_runbook(
            {
                "service_name": "billing-service",
                "owners": ["platform"],
                "escalation_channels": ["#billing-oncall"],
                "slo": "99.9 availability",
                "runbook_url": "https://docs.example.test/runbooks/billing",
                "dashboard_url": "https://dash.example.test/billing",
                "oncall_rotation": "billing-primary",
            },
            {"require_slo": True, "require_runbook_url": True, "require_dashboard_url": True, "require_oncall_rotation": True},
        )
        bad_ownership = plan_service_ownership_runbook(
            {},
            {"require_slo": True, "require_runbook_url": True, "require_dashboard_url": True, "require_oncall_rotation": True},
        )

        self.assertTrue(offset.ready)
        self.assertFalse(bad_offset.ready)
        self.assertIn("missing_consumer_group", bad_offset.blockers)
        self.assertIn("missing_topic_name", bad_offset.blockers)
        self.assertIn("offset_strategy_not_allowed:auto", bad_offset.blockers)
        self.assertIn("missing_checkpoint_store", bad_offset.blockers)
        self.assertIn("missing_replay_policy", bad_offset.blockers)
        self.assertIn("lag_alert_threshold_exceeds_policy", bad_offset.blockers)
        self.assertTrue(ownership.ready)
        self.assertFalse(bad_ownership.ready)
        self.assertIn("missing_service_name", bad_ownership.blockers)
        self.assertIn("missing_owners", bad_ownership.blockers)
        self.assertIn("missing_escalation_channels", bad_ownership.blockers)
        self.assertIn("missing_slo", bad_ownership.blockers)
        self.assertIn("missing_runbook_url", bad_ownership.blockers)
        self.assertIn("missing_dashboard_url", bad_ownership.blockers)
        self.assertIn("missing_oncall_rotation", bad_ownership.blockers)

    def test_plan_schema_drift_gate_and_migration_lock_enforce_database_change_gates(self) -> None:
        drift = plan_schema_drift_gate(
            {"dataset_name": "customer_accounts", "expected_fields": ["id", "email"], "observed_fields": ["id", "email", "phone"], "owner": "data-platform", "migration_receipt": "migration-123"},
            {"block_removed_fields": True, "block_unapproved_added_fields": True, "allowed_added_fields": ["phone"], "require_owner": True, "require_migration_receipt": True},
        )
        bad_drift = plan_schema_drift_gate(
            {"expected_fields": ["id", "email"], "observed_fields": ["id", "phone"]},
            {"block_removed_fields": True, "block_unapproved_added_fields": True, "allowed_added_fields": ["phone"], "require_owner": True, "require_migration_receipt": True},
        )
        lock = plan_migration_lock(
            {"migration_name": "add-customer-phone", "lock_key": "schema:customer_accounts", "timeout_seconds": 120, "owner": "data-platform", "stale_lock_strategy": "release-after-timeout", "advisory_lock": "pg_advisory_lock", "rollback_receipt": "rollback-123"},
            {"max_timeout_seconds": 300, "require_owner": True, "require_stale_lock_strategy": True, "require_advisory_lock": True, "require_rollback_receipt": True},
        )
        bad_lock = plan_migration_lock(
            {"timeout_seconds": 900},
            {"max_timeout_seconds": 300, "require_owner": True, "require_stale_lock_strategy": True, "require_advisory_lock": True, "require_rollback_receipt": True},
        )

        self.assertTrue(drift.compatible)
        self.assertFalse(bad_drift.compatible)
        self.assertIn("missing_dataset_name", bad_drift.blockers)
        self.assertIn("removed_field:email", bad_drift.blockers)
        self.assertIn("missing_owner", bad_drift.blockers)
        self.assertIn("missing_migration_receipt", bad_drift.blockers)
        self.assertTrue(lock.ready)
        self.assertFalse(bad_lock.ready)
        self.assertIn("missing_migration_name", bad_lock.blockers)
        self.assertIn("missing_lock_key", bad_lock.blockers)
        self.assertIn("timeout_exceeds_policy", bad_lock.blockers)
        self.assertIn("missing_owner", bad_lock.blockers)
        self.assertIn("missing_stale_lock_strategy", bad_lock.blockers)
        self.assertIn("missing_advisory_lock", bad_lock.blockers)
        self.assertIn("missing_rollback_receipt", bad_lock.blockers)

    def test_plan_data_retention_and_tenant_boundary_enforce_privacy_controls(self) -> None:
        retention = plan_data_retention_enforcement(
            {"dataset_name": "audit_logs", "retention_days": 365, "purge_strategy": "tombstone_then_purge", "legal_hold_check": "none", "dry_run_receipt": "dry-run-1", "audit_receipt": "audit-1"},
            {"min_retention_days": 90, "max_retention_days": 730, "allowed_purge_strategies": ["tombstone_then_purge"], "require_legal_hold_check": True, "require_dry_run_receipt": True, "require_audit_receipt": True},
        )
        bad_retention = plan_data_retention_enforcement(
            {"retention_days": 30, "purge_strategy": "drop_table"},
            {"min_retention_days": 90, "max_retention_days": 730, "allowed_purge_strategies": ["tombstone_then_purge"], "require_legal_hold_check": True, "require_dry_run_receipt": True, "require_audit_receipt": True},
        )
        boundary = plan_tenant_data_boundary(
            {"dataset_name": "customer_accounts", "tenant_key": "tenant_id", "boundary_controls": ["rls", "tenant_scoped_index"], "cross_tenant_negative_test": "deny other tenant", "encryption_scope": "tenant", "audit_receipt": "audit-tenant"},
            {"required_controls": ["rls", "tenant_scoped_index"], "require_cross_tenant_negative_test": True, "require_encryption_scope": True, "require_audit_receipt": True},
        )
        bad_boundary = plan_tenant_data_boundary(
            {"boundary_controls": ["rls"]},
            {"required_controls": ["rls", "tenant_scoped_index"], "require_cross_tenant_negative_test": True, "require_encryption_scope": True, "require_audit_receipt": True},
        )

        self.assertTrue(retention.ready)
        self.assertFalse(bad_retention.ready)
        self.assertIn("missing_dataset_name", bad_retention.blockers)
        self.assertIn("retention_below_policy", bad_retention.blockers)
        self.assertIn("purge_strategy_not_allowed:drop_table", bad_retention.blockers)
        self.assertIn("missing_legal_hold_check", bad_retention.blockers)
        self.assertIn("missing_dry_run_receipt", bad_retention.blockers)
        self.assertIn("missing_audit_receipt", bad_retention.blockers)
        self.assertTrue(boundary.ready)
        self.assertFalse(bad_boundary.ready)
        self.assertIn("missing_dataset_name", bad_boundary.blockers)
        self.assertIn("missing_tenant_key", bad_boundary.blockers)
        self.assertIn("missing_control:tenant_scoped_index", bad_boundary.blockers)
        self.assertIn("missing_cross_tenant_negative_test", bad_boundary.blockers)
        self.assertIn("missing_encryption_scope", bad_boundary.blockers)
        self.assertIn("missing_audit_receipt", bad_boundary.blockers)

    def test_plan_backup_restore_drill_and_access_review_enforce_recovery_and_access_evidence(self) -> None:
        drill = plan_backup_restore_drill(
            {"system_name": "billing-db", "backup_artifact": "s3://backups/billing.snap", "restore_target": "restore-lab", "rpo_minutes": 15, "rto_minutes": 45, "checksum_verification": "sha256-ok", "restore_evidence": "restore-report", "owner": "platform"},
            {"max_rpo_minutes": 60, "max_rto_minutes": 120, "require_checksum_verification": True, "require_restore_evidence": True, "require_owner": True},
        )
        bad_drill = plan_backup_restore_drill(
            {"rpo_minutes": 90, "rto_minutes": 300},
            {"max_rpo_minutes": 60, "max_rto_minutes": 120, "require_checksum_verification": True, "require_restore_evidence": True, "require_owner": True},
        )
        review = plan_access_review_evidence(
            {
                "review_name": "q3-admin-access",
                "review_period": "2026-Q3",
                "entries": [
                    {"subject": "alice", "role": "admin", "manager": "maria", "decision": "keep"},
                    {"subject": "bob", "role": "admin", "manager": "maria", "decision": "revoke", "revocation_ticket": "IAM-9"},
                ],
            },
            {"allowed_decisions": ["keep", "revoke"], "require_manager": True, "require_revocation_ticket": True, "require_review_period": True},
        )
        bad_review = plan_access_review_evidence(
            {"entries": [{"subject": "bob", "decision": "unknown"}]},
            {"allowed_decisions": ["keep", "revoke"], "require_manager": True, "require_revocation_ticket": True, "require_review_period": True},
        )

        self.assertTrue(drill.ready)
        self.assertFalse(bad_drill.ready)
        self.assertIn("missing_system_name", bad_drill.blockers)
        self.assertIn("missing_backup_artifact", bad_drill.blockers)
        self.assertIn("missing_restore_target", bad_drill.blockers)
        self.assertIn("rpo_exceeds_policy", bad_drill.blockers)
        self.assertIn("rto_exceeds_policy", bad_drill.blockers)
        self.assertIn("missing_checksum_verification", bad_drill.blockers)
        self.assertIn("missing_restore_evidence", bad_drill.blockers)
        self.assertIn("missing_owner", bad_drill.blockers)
        self.assertTrue(review.ready)
        self.assertFalse(bad_review.ready)
        self.assertIn("missing_review_name", bad_review.blockers)
        self.assertIn("entry_1_missing_role", bad_review.blockers)
        self.assertIn("entry_1_missing_manager", bad_review.blockers)
        self.assertIn("decision_not_allowed:unknown", bad_review.blockers)
        self.assertIn("missing_review_period", bad_review.blockers)

    def test_plan_data_deletion_and_privileged_access_enforce_sensitive_workflows(self) -> None:
        deletion = plan_data_deletion_workflow(
            {"request_id": "dsar-001", "subject_id": "customer-123", "deletion_scopes": ["primary_db", "search_index"], "identity_verification": "verified", "legal_hold_check": "none", "tombstone": "created", "propagation_receipt": "propagated"},
            {"required_scopes": ["primary_db", "search_index"], "require_identity_verification": True, "require_legal_hold_check": True, "require_tombstone": True, "require_propagation_receipt": True},
        )
        bad_deletion = plan_data_deletion_workflow(
            {"deletion_scopes": ["primary_db"]},
            {"required_scopes": ["primary_db", "search_index"], "require_identity_verification": True, "require_legal_hold_check": True, "require_tombstone": True, "require_propagation_receipt": True},
        )
        approval = plan_privileged_access_approval(
            {"request_id": "pam-001", "requester": "alice", "role": "database_admin", "duration_minutes": 30, "approval_ticket": "SEC-1", "justification": "incident repair", "expires_at": "2026-07-01T18:00:00Z", "breakglass": True, "breakglass_reason": "sev1"},
            {"allowed_roles": ["database_admin"], "max_duration_minutes": 60, "require_approval_ticket": True, "require_justification": True, "require_expiry": True, "require_breakglass_reason": True},
        )
        bad_approval = plan_privileged_access_approval(
            {"role": "root", "duration_minutes": 120, "breakglass": True},
            {"allowed_roles": ["database_admin"], "max_duration_minutes": 60, "require_approval_ticket": True, "require_justification": True, "require_expiry": True, "require_breakglass_reason": True},
        )

        self.assertTrue(deletion.ready)
        self.assertFalse(bad_deletion.ready)
        self.assertIn("missing_request_id", bad_deletion.blockers)
        self.assertIn("missing_subject_id", bad_deletion.blockers)
        self.assertIn("missing_scope:search_index", bad_deletion.blockers)
        self.assertIn("missing_identity_verification", bad_deletion.blockers)
        self.assertIn("missing_legal_hold_check", bad_deletion.blockers)
        self.assertIn("missing_tombstone", bad_deletion.blockers)
        self.assertIn("missing_propagation_receipt", bad_deletion.blockers)
        self.assertTrue(approval.ready)
        self.assertFalse(bad_approval.ready)
        self.assertIn("missing_request_id", bad_approval.blockers)
        self.assertIn("missing_requester", bad_approval.blockers)
        self.assertIn("role_not_allowed:root", bad_approval.blockers)
        self.assertIn("duration_exceeds_policy", bad_approval.blockers)
        self.assertIn("missing_approval_ticket", bad_approval.blockers)
        self.assertIn("missing_justification", bad_approval.blockers)
        self.assertIn("missing_expiry", bad_approval.blockers)
        self.assertIn("missing_breakglass_reason", bad_approval.blockers)

    def test_plan_connector_cursor_checkpoint_and_field_mapping_enforce_sync_contracts(self) -> None:
        checkpoint = plan_connector_cursor_checkpoint(
            {"connector_name": "salesforce-hubspot", "cursor_field": "updated_at", "checkpoint_store": "redis://sync-cursors", "checkpoint_interval_records": 500, "monotonic_cursor": "updated_at asc", "resume_token": "cursor-1", "checkpoint_receipt": "receipt-1"},
            {"max_checkpoint_interval_records": 1000, "require_monotonic_cursor": True, "require_resume_token": True, "require_checkpoint_receipt": True},
        )
        bad_checkpoint = plan_connector_cursor_checkpoint(
            {"checkpoint_interval_records": 5000},
            {"max_checkpoint_interval_records": 1000, "require_monotonic_cursor": True, "require_resume_token": True, "require_checkpoint_receipt": True},
        )
        mapping = plan_connector_field_mapping(
            {
                "source_system": "salesforce",
                "target_system": "hubspot",
                "mappings": [
                    {"source_field": "Email", "target_field": "email"},
                    {"source_field": "LifecycleStage", "target_field": "lifecycle_stage", "transform": "enum_map"},
                ],
                "mapping_receipt": "mapping-1",
            },
            {"required_target_fields": ["email", "lifecycle_stage"], "require_transform_for_fields": ["lifecycle_stage"], "require_mapping_receipt": True},
        )
        bad_mapping = plan_connector_field_mapping(
            {"mappings": [{"target_field": "email"}]},
            {"required_target_fields": ["email", "lifecycle_stage"], "require_transform_for_fields": ["email"], "require_mapping_receipt": True},
        )

        self.assertTrue(checkpoint.ready)
        self.assertFalse(bad_checkpoint.ready)
        self.assertIn("missing_connector_name", bad_checkpoint.blockers)
        self.assertIn("missing_cursor_field", bad_checkpoint.blockers)
        self.assertIn("missing_checkpoint_store", bad_checkpoint.blockers)
        self.assertIn("checkpoint_interval_exceeds_policy", bad_checkpoint.blockers)
        self.assertIn("missing_monotonic_cursor", bad_checkpoint.blockers)
        self.assertIn("missing_resume_token", bad_checkpoint.blockers)
        self.assertIn("missing_checkpoint_receipt", bad_checkpoint.blockers)
        self.assertTrue(mapping.ready)
        self.assertFalse(bad_mapping.ready)
        self.assertIn("missing_source_system", bad_mapping.blockers)
        self.assertIn("missing_target_system", bad_mapping.blockers)
        self.assertIn("mapping_1_missing_source_field", bad_mapping.blockers)
        self.assertIn("missing_target_field:lifecycle_stage", bad_mapping.blockers)
        self.assertIn("missing_transform_for_field:email", bad_mapping.blockers)
        self.assertIn("missing_mapping_receipt", bad_mapping.blockers)

    def test_plan_external_identity_map_and_sync_conflict_resolution_enforce_identity_safety(self) -> None:
        identity_map = plan_external_identity_map(
            {"source_system": "shopify", "target_system": "netsuite", "identity_keys": ["external_id", "tenant_id"], "mapping_store": "identity_map", "unique_constraint": "tenant_external_unique", "orphan_policy": "quarantine", "collision_policy": "manual_review"},
            {"required_identity_keys": ["external_id", "tenant_id"], "require_mapping_store": True, "require_unique_constraint": True, "require_orphan_policy": True, "require_collision_policy": True},
        )
        bad_identity_map = plan_external_identity_map(
            {"identity_keys": ["external_id"]},
            {"required_identity_keys": ["external_id", "tenant_id"], "require_mapping_store": True, "require_unique_constraint": True, "require_orphan_policy": True, "require_collision_policy": True},
        )
        conflict = plan_sync_conflict_resolution(
            {"sync_name": "shopify-netsuite-order-sync", "conflict_keys": ["order_id", "updated_at"], "resolution_strategy": "source_priority", "precedence_rule": "netsuite wins after invoice", "manual_review_queue": "sync-conflicts", "conflict_receipt": "conflict-1"},
            {"allowed_resolution_strategies": ["source_priority", "target_priority", "manual_review"], "require_precedence_rule": True, "require_manual_review_queue": True, "require_conflict_receipt": True},
        )
        bad_conflict = plan_sync_conflict_resolution(
            {"resolution_strategy": "overwrite_all"},
            {"allowed_resolution_strategies": ["source_priority", "target_priority", "manual_review"], "require_precedence_rule": True, "require_manual_review_queue": True, "require_conflict_receipt": True},
        )

        self.assertTrue(identity_map.ready)
        self.assertFalse(bad_identity_map.ready)
        self.assertIn("missing_source_system", bad_identity_map.blockers)
        self.assertIn("missing_target_system", bad_identity_map.blockers)
        self.assertIn("missing_identity_key:tenant_id", bad_identity_map.blockers)
        self.assertIn("missing_mapping_store", bad_identity_map.blockers)
        self.assertIn("missing_unique_constraint", bad_identity_map.blockers)
        self.assertIn("missing_orphan_policy", bad_identity_map.blockers)
        self.assertIn("missing_collision_policy", bad_identity_map.blockers)
        self.assertTrue(conflict.ready)
        self.assertFalse(bad_conflict.ready)
        self.assertIn("missing_sync_name", bad_conflict.blockers)
        self.assertIn("missing_conflict_keys", bad_conflict.blockers)
        self.assertIn("resolution_strategy_not_allowed:overwrite_all", bad_conflict.blockers)
        self.assertIn("missing_precedence_rule", bad_conflict.blockers)
        self.assertIn("missing_manual_review_queue", bad_conflict.blockers)
        self.assertIn("missing_conflict_receipt", bad_conflict.blockers)

    def test_plan_connector_rate_limit_and_webhook_replay_enforce_provider_runtime_limits(self) -> None:
        budget = plan_connector_rate_limit_budget(
            {"connector_name": "stripe-sync", "requests_per_window": 80, "window_seconds": 60, "retry_after_handling": "honor-header", "burst_policy": "token-bucket", "budget_alert": "pagerduty"},
            {"max_requests_per_window": 100, "min_window_seconds": 60, "require_retry_after_handling": True, "require_burst_policy": True, "require_budget_alert": True},
        )
        bad_budget = plan_connector_rate_limit_budget(
            {"requests_per_window": 500, "window_seconds": 10},
            {"max_requests_per_window": 100, "min_window_seconds": 60, "require_retry_after_handling": True, "require_burst_policy": True, "require_budget_alert": True},
        )
        replay = plan_webhook_replay_window(
            {"webhook_name": "stripe-invoice-paid", "replay_window_minutes": 120, "dedupe_key": "event_id", "signature_validation": "stripe-sig", "source_event_store": "events.raw", "replay_receipt": "replay-1"},
            {"max_replay_window_minutes": 240, "require_signature_validation": True, "require_source_event_store": True, "require_replay_receipt": True},
        )
        bad_replay = plan_webhook_replay_window(
            {"replay_window_minutes": 1440},
            {"max_replay_window_minutes": 240, "require_signature_validation": True, "require_source_event_store": True, "require_replay_receipt": True},
        )

        self.assertTrue(budget.ready)
        self.assertFalse(bad_budget.ready)
        self.assertIn("missing_connector_name", bad_budget.blockers)
        self.assertIn("requests_per_window_exceeds_policy", bad_budget.blockers)
        self.assertIn("window_below_policy", bad_budget.blockers)
        self.assertIn("missing_retry_after_handling", bad_budget.blockers)
        self.assertIn("missing_burst_policy", bad_budget.blockers)
        self.assertIn("missing_budget_alert", bad_budget.blockers)
        self.assertTrue(replay.ready)
        self.assertFalse(bad_replay.ready)
        self.assertIn("missing_webhook_name", bad_replay.blockers)
        self.assertIn("replay_window_exceeds_policy", bad_replay.blockers)
        self.assertIn("missing_dedupe_key", bad_replay.blockers)
        self.assertIn("missing_signature_validation", bad_replay.blockers)
        self.assertIn("missing_source_event_store", bad_replay.blockers)
        self.assertIn("missing_replay_receipt", bad_replay.blockers)

    def test_plan_connector_error_quarantine_and_sync_reconciliation_enforce_operational_evidence(self) -> None:
        quarantine = plan_connector_error_quarantine(
            {"connector_name": "stripe-sync", "error_classes": ["schema_error", "rate_limit"], "quarantine_sink": "sync.quarantine", "triage_owner": "integrations", "replay_policy": "after-fix", "error_receipt": "error-1"},
            {"required_error_classes": ["schema_error", "rate_limit"], "require_triage_owner": True, "require_replay_policy": True, "require_error_receipt": True},
        )
        bad_quarantine = plan_connector_error_quarantine(
            {"error_classes": ["schema_error"]},
            {"required_error_classes": ["schema_error", "rate_limit"], "require_triage_owner": True, "require_replay_policy": True, "require_error_receipt": True},
        )
        report = plan_sync_reconciliation_report(
            {"sync_name": "stripe-ledger-sync", "source_count_field": "stripe_count", "target_count_field": "ledger_count", "mismatch_threshold": 1, "sample_rows": ["invoice_1"], "reconciliation_owner": "finance-ops", "report_receipt": "report-1"},
            {"max_mismatch_threshold": 5, "require_sample_rows": True, "require_reconciliation_owner": True, "require_report_receipt": True},
        )
        bad_report = plan_sync_reconciliation_report(
            {"mismatch_threshold": 10},
            {"max_mismatch_threshold": 5, "require_sample_rows": True, "require_reconciliation_owner": True, "require_report_receipt": True},
        )

        self.assertTrue(quarantine.ready)
        self.assertFalse(bad_quarantine.ready)
        self.assertIn("missing_connector_name", bad_quarantine.blockers)
        self.assertIn("missing_error_class:rate_limit", bad_quarantine.blockers)
        self.assertIn("missing_quarantine_sink", bad_quarantine.blockers)
        self.assertIn("missing_triage_owner", bad_quarantine.blockers)
        self.assertIn("missing_replay_policy", bad_quarantine.blockers)
        self.assertIn("missing_error_receipt", bad_quarantine.blockers)
        self.assertTrue(report.ready)
        self.assertFalse(bad_report.ready)
        self.assertIn("missing_sync_name", bad_report.blockers)
        self.assertIn("missing_source_count_field", bad_report.blockers)
        self.assertIn("missing_target_count_field", bad_report.blockers)
        self.assertIn("mismatch_threshold_exceeds_policy", bad_report.blockers)
        self.assertIn("missing_sample_rows", bad_report.blockers)
        self.assertIn("missing_reconciliation_owner", bad_report.blockers)
        self.assertIn("missing_report_receipt", bad_report.blockers)

    def test_plan_primitive_candidate_intake_and_reuse_observation_enforce_registry_edges(self) -> None:
        candidate = {
            "primitive_id": "grp:teleon.primitive_candidate_intake.plan@1",
            "kind": "registry.primitive_candidate_intake",
            "input_edge": "PrimitiveCandidateCard+IntakePolicy",
            "output_edge": "PrimitiveCandidateIntakeReceipt",
            "group_contract": {
                "core_group_edge": "PrimitiveCandidateCard+IntakePolicy -> PrimitiveCandidateIntakeReceipt",
                "hidden_member_edges": [
                    "PrimitiveCandidateCard->VisibleEdgeContract",
                    "PrimitiveCandidateCard->HiddenMemberEdgeSet",
                    "IntakePolicy->CandidateBoundaryPolicy",
                ],
            },
            "effects": ["registry_intake_plan"],
            "runtime_targets": ["registry.indexer"],
            "adapter_mutators": ["candidate_intake_gate"],
            "proof_requirements": ["unit_test"],
            "proof_refs": [{"path": "tests/unit/test_teleon_primitive_groups.py"}],
            "source_ref": {"path": "src/teleon/primitives/groups.py", "name": "plan_primitive_candidate_intake"},
            "candidate": True,
            "serves_truth": False,
        }
        intake = plan_primitive_candidate_intake(
            candidate,
            {
                "required_id_prefixes": ["grp:teleon."],
                "allowed_kinds": ["registry.primitive_candidate_intake"],
                "require_core_group_edge": True,
                "min_hidden_member_edges": 2,
                "require_adapter_mutator": True,
                "require_runtime_targets": True,
                "required_effects": ["registry_intake_plan"],
                "require_proof_requirements": True,
                "require_source_ref": True,
                "require_proof_refs": True,
                "require_candidate_boundary": True,
            },
        )
        bad_intake = plan_primitive_candidate_intake(
            {"primitive_id": "bad:id", "kind": "registry.bad", "candidate": False, "serves_truth": True},
            {
                "required_id_prefixes": ["grp:teleon."],
                "allowed_kinds": ["registry.primitive_candidate_intake"],
                "require_core_group_edge": True,
                "min_hidden_member_edges": 1,
                "require_adapter_mutator": True,
                "require_runtime_targets": True,
                "required_effects": ["registry_intake_plan"],
                "require_proof_requirements": True,
                "require_source_ref": True,
                "require_proof_refs": True,
                "require_candidate_boundary": True,
            },
        )
        reuse = plan_primitive_reuse_observation(
            {
                "observations": [
                    {
                        "primitive_id": "grp:teleon.csv_import.api@1",
                        "runtime_shape": "api.endpoint",
                        "core_group_edge": "CsvFile+ImportPolicy -> ImportReceipt",
                        "route_reused": True,
                        "proof_status": "pass",
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "primitive_id": "grp:teleon.csv_import.queue@1",
                        "runtime_shape": "queue.consumer",
                        "core_group_edge": "CsvFile+ImportPolicy -> ImportReceipt",
                        "route_reused": True,
                        "proof_status": "pass",
                        "candidate": True,
                        "serves_truth": False,
                    },
                ]
            },
            {"min_observations": 2, "min_runtime_shapes": 2, "require_single_core_group_edge": True, "require_route_reused": True, "require_proof_status_pass": True, "require_candidate_boundary": True},
        )
        bad_reuse = plan_primitive_reuse_observation(
            {
                "observations": [
                    {"runtime_shape": "api.endpoint", "core_group_edge": "A -> B", "route_reused": False, "proof_status": "fail", "candidate": False, "serves_truth": True},
                    {"runtime_shape": "api.endpoint", "core_group_edge": "C -> D", "route_reused": True, "proof_status": "pass", "candidate": True, "serves_truth": False},
                ]
            },
            {"min_observations": 3, "min_runtime_shapes": 2, "require_single_core_group_edge": True, "require_route_reused": True, "require_proof_status_pass": True, "require_candidate_boundary": True},
        )

        self.assertTrue(intake.ready)
        self.assertEqual(intake.primitive_id, "grp:teleon.primitive_candidate_intake.plan@1")
        self.assertTrue(intake.intake_hash.startswith("primitive-candidate-intake:"))
        self.assertFalse(bad_intake.ready)
        self.assertIn("primitive_id_missing_prefix:grp:teleon.", bad_intake.blockers)
        self.assertIn("kind_not_allowed:registry.bad", bad_intake.blockers)
        self.assertIn("missing_input_edge", bad_intake.blockers)
        self.assertIn("missing_output_edge", bad_intake.blockers)
        self.assertIn("missing_core_group_edge", bad_intake.blockers)
        self.assertIn("hidden_member_edges_below_policy", bad_intake.blockers)
        self.assertIn("missing_adapter_mutators", bad_intake.blockers)
        self.assertIn("missing_runtime_targets", bad_intake.blockers)
        self.assertIn("missing_effect:registry_intake_plan", bad_intake.blockers)
        self.assertIn("missing_proof_requirements", bad_intake.blockers)
        self.assertIn("missing_source_ref", bad_intake.blockers)
        self.assertIn("missing_proof_refs", bad_intake.blockers)
        self.assertIn("candidate_boundary_not_declared", bad_intake.blockers)
        self.assertIn("serves_truth_must_be_false", bad_intake.blockers)
        self.assertTrue(reuse.ready)
        self.assertEqual(reuse.core_group_edge, "CsvFile+ImportPolicy -> ImportReceipt")
        self.assertEqual(reuse.runtime_shapes, ("api.endpoint", "queue.consumer"))
        self.assertFalse(bad_reuse.ready)
        self.assertIn("observation_count_below_policy", bad_reuse.blockers)
        self.assertIn("runtime_shape_count_below_policy", bad_reuse.blockers)
        self.assertIn("multiple_core_group_edges", bad_reuse.blockers)
        self.assertIn("observation_1_route_not_reused", bad_reuse.blockers)
        self.assertIn("observation_1_proof_not_pass", bad_reuse.blockers)
        self.assertIn("observation_1_candidate_boundary_not_declared", bad_reuse.blockers)
        self.assertIn("observation_1_serves_truth_must_be_false", bad_reuse.blockers)

    def test_plan_primitive_proof_promotion_and_registry_publish_enforce_candidate_gates(self) -> None:
        card = {
            "primitive_id": "grp:teleon.primitive_candidate_intake.plan@1",
            "proof_requirements": ["unit_test", "candidate_boundary_gate"],
            "candidate": True,
            "serves_truth": False,
        }
        proofs = [
            {"subject_id": card["primitive_id"], "proof_kind": "unit_test", "status": "pass"},
            {"subject_id": card["primitive_id"], "proof_kind": "candidate_boundary_gate", "status": "pass"},
        ]
        coverage = plan_primitive_proof_coverage_matrix(
            {"candidate_cards": [card], "proof_bundles": proofs},
            {"require_proof_bundles": True, "require_candidate_boundary": True, "required_status": "pass"},
        )
        bad_coverage = plan_primitive_proof_coverage_matrix(
            {"candidate_cards": [{"primitive_id": "grp:teleon.bad.plan@1", "proof_requirements": ["unit_test", "contract_test"], "candidate": False, "serves_truth": True}], "proof_bundles": [{"subject_id": "grp:teleon.bad.plan@1", "proof_kind": "unit_test", "status": "fail"}]},
            {"require_proof_bundles": True, "require_candidate_boundary": True, "required_status": "pass"},
        )
        promotion = plan_primitive_promotion_review(
            {
                "primitive_id": card["primitive_id"],
                "proof_status": "pass",
                "proof_bundle_ref": "proofs/primitive-intake.json",
                "source_ref": {"path": "src/teleon/primitives/groups.py"},
                "owner_review_status": "approved",
                "candidate": True,
                "serves_truth": False,
            },
            {"require_proof_status_pass": True, "require_proof_bundle_ref": True, "require_source_ref": True, "require_owner_review": True, "require_candidate_boundary": True},
        )
        bad_promotion = plan_primitive_promotion_review(
            {"proof_status": "fail", "owner_review_status": "pending", "promotion_blockers": ["missing_contract"], "candidate": False, "serves_truth": True},
            {"require_proof_status_pass": True, "require_proof_bundle_ref": True, "require_source_ref": True, "require_owner_review": True, "require_candidate_boundary": True},
        )
        publish = plan_registry_publish_manifest(
            {
                "registry_name": "aidevobserver-source-backed-groups",
                "cards": [card],
                "proof_bundles": proofs,
                "promotion_gates": [{"subject_id": card["primitive_id"], "promotion_gate_status": "blocked_pending_owner_review"}],
                "search_targets": ["aidevobserver_edge_search", "aidevexplorer_route_search"],
            },
            {"min_cards": 1, "required_search_targets": ["aidevobserver_edge_search"], "require_candidate_boundary": True, "require_proof_bundle": True, "require_promotion_gate": True},
        )
        bad_publish = plan_registry_publish_manifest(
            {"cards": [{"primitive_id": "grp:teleon.bad.plan@1", "candidate": False, "serves_truth": True}], "search_targets": []},
            {"min_cards": 2, "required_search_targets": ["aidevobserver_edge_search"], "require_candidate_boundary": True, "require_proof_bundle": True, "require_promotion_gate": True},
        )

        self.assertTrue(coverage.ready)
        self.assertEqual(coverage.missing_requirements, ())
        self.assertTrue(coverage.coverage_hash.startswith("primitive-proof-coverage:"))
        self.assertFalse(bad_coverage.ready)
        self.assertIn("grp:teleon.bad.plan@1:candidate_boundary_not_declared", bad_coverage.blockers)
        self.assertIn("grp:teleon.bad.plan@1:serves_truth_must_be_false", bad_coverage.blockers)
        self.assertIn("proof_requirements_missing", bad_coverage.blockers)
        self.assertIn("proof_status_not_pass", bad_coverage.blockers)
        self.assertIn("grp:teleon.bad.plan@1:contract_test", bad_coverage.missing_requirements)
        self.assertTrue(promotion.promotion_allowed)
        self.assertEqual(promotion.promotion_gate_status, "approved_for_owner_promotion")
        self.assertFalse(bad_promotion.promotion_allowed)
        self.assertEqual(bad_promotion.promotion_gate_status, "blocked_pending_owner_review")
        self.assertIn("missing_primitive_id", bad_promotion.blockers)
        self.assertIn("proof_status_not_pass", bad_promotion.blockers)
        self.assertIn("missing_proof_bundle_ref", bad_promotion.blockers)
        self.assertIn("missing_source_ref", bad_promotion.blockers)
        self.assertIn("owner_review_required", bad_promotion.blockers)
        self.assertIn("promotion_blocker:missing_contract", bad_promotion.blockers)
        self.assertIn("candidate_boundary_not_declared", bad_promotion.blockers)
        self.assertIn("serves_truth_must_be_false_before_promotion", bad_promotion.blockers)
        self.assertTrue(publish.ready)
        self.assertEqual(publish.registry_name, "aidevobserver_source_backed_groups")
        self.assertEqual(publish.card_count, 1)
        self.assertFalse(bad_publish.ready)
        self.assertIn("missing_registry_name", bad_publish.blockers)
        self.assertIn("card_count_below_policy", bad_publish.blockers)
        self.assertIn("missing_search_target:aidevobserver_edge_search", bad_publish.blockers)
        self.assertIn("grp:teleon.bad.plan@1:candidate_boundary_not_declared", bad_publish.blockers)
        self.assertIn("grp:teleon.bad.plan@1:serves_truth_must_be_false", bad_publish.blockers)
        self.assertIn("grp:teleon.bad.plan@1:missing_proof_bundle", bad_publish.blockers)
        self.assertIn("grp:teleon.bad.plan@1:missing_promotion_gate", bad_publish.blockers)

    def test_plan_benchmark_run_arm_and_token_savings_enforce_scorecard_inputs(self) -> None:
        arm = plan_benchmark_run_arm(
            {
                "arm_name": "aidevexplorer_candidate",
                "task_ids": ["task-1", "task-2"],
                "runner": "codex",
                "metrics": ["wall_clock_minutes", "prompt_tokens", "completion_tokens", "test_pass_rate"],
                "artifact_manifest": "runs/candidate/manifest.json",
                "run_receipt": "receipt://candidate-run",
                "candidate": True,
                "serves_truth": False,
            },
            {
                "allowed_arm_names": ["baseline", "aidevexplorer_candidate"],
                "min_tasks": 2,
                "require_runner": True,
                "required_metrics": ["wall_clock_minutes", "prompt_tokens", "completion_tokens", "test_pass_rate"],
                "require_artifact_manifest": True,
                "require_run_receipt": True,
                "require_candidate_boundary": True,
            },
        )
        bad_arm = plan_benchmark_run_arm(
            {"arm_name": "ad_hoc", "task_ids": ["task-1"], "metrics": ["prompt_tokens"], "candidate": False, "serves_truth": True},
            {
                "allowed_arm_names": ["baseline", "aidevexplorer_candidate"],
                "min_tasks": 2,
                "require_runner": True,
                "required_metrics": ["wall_clock_minutes", "prompt_tokens", "completion_tokens", "test_pass_rate"],
                "require_artifact_manifest": True,
                "require_run_receipt": True,
                "require_candidate_boundary": True,
            },
        )
        savings = plan_token_savings_attribution(
            {
                "baseline_prompt_tokens": 1000,
                "baseline_completion_tokens": 500,
                "candidate_prompt_tokens": 600,
                "candidate_completion_tokens": 300,
                "primitive_ids": ["grp:teleon.csv_import.plan@1"],
                "trace_ref": "runs/candidate/trace.jsonl",
                "candidate": True,
                "serves_truth": False,
            },
            {"min_savings_percent": 30, "require_primitives": True, "require_trace_ref": True, "require_candidate_boundary": True},
        )
        bad_savings = plan_token_savings_attribution(
            {"candidate_prompt_tokens": 1000, "candidate": False, "serves_truth": True},
            {"min_savings_percent": 30, "require_primitives": True, "require_trace_ref": True, "require_candidate_boundary": True},
        )

        self.assertTrue(arm.ready)
        self.assertEqual(arm.task_count, 2)
        self.assertTrue(arm.arm_hash.startswith("benchmark-run-arm:"))
        self.assertFalse(bad_arm.ready)
        self.assertIn("arm_name_not_allowed:ad_hoc", bad_arm.blockers)
        self.assertIn("task_count_below_policy", bad_arm.blockers)
        self.assertIn("missing_runner", bad_arm.blockers)
        self.assertIn("missing_metric:wall_clock_minutes", bad_arm.blockers)
        self.assertIn("missing_metric:completion_tokens", bad_arm.blockers)
        self.assertIn("missing_metric:test_pass_rate", bad_arm.blockers)
        self.assertIn("missing_artifact_manifest", bad_arm.blockers)
        self.assertIn("missing_run_receipt", bad_arm.blockers)
        self.assertIn("candidate_boundary_not_declared", bad_arm.blockers)
        self.assertIn("serves_truth_must_be_false", bad_arm.blockers)
        self.assertTrue(savings.ready)
        self.assertEqual(savings.baseline_tokens, 1500)
        self.assertEqual(savings.candidate_tokens, 900)
        self.assertEqual(savings.savings_percent, 40.0)
        self.assertFalse(bad_savings.ready)
        self.assertIn("missing_baseline_tokens", bad_savings.blockers)
        self.assertIn("missing_primitive_ids", bad_savings.blockers)
        self.assertIn("token_savings_below_policy", bad_savings.blockers)
        self.assertIn("missing_trace_ref", bad_savings.blockers)
        self.assertIn("candidate_boundary_not_declared", bad_savings.blockers)
        self.assertIn("serves_truth_must_be_false", bad_savings.blockers)

    def test_plan_lift_pitfall_and_route_evidence_enforce_experiment_promotion_inputs(self) -> None:
        lift = plan_primitive_lift_comparison(
            {
                "baseline_arm": "baseline",
                "candidate_arm": "aidevexplorer_candidate",
                "baseline_metrics": {"wall_clock_minutes": 20, "prompt_tokens": 1000, "test_pass_rate": 0.7, "pitfalls_avoided": 1},
                "candidate_metrics": {"wall_clock_minutes": 12, "prompt_tokens": 600, "test_pass_rate": 0.9, "pitfalls_avoided": 3},
                "primitive_groups_used": ["grp:teleon.csv_import.plan@1"],
                "candidate": True,
                "serves_truth": False,
            },
            {
                "dimensions": [
                    {"name": "wall_clock_minutes", "direction": "lower_is_better", "min_delta": 1, "required": True},
                    {"name": "prompt_tokens", "direction": "lower_is_better", "min_delta": 100, "required": True},
                    {"name": "test_pass_rate", "direction": "higher_is_better", "min_delta": 0.1, "required": True},
                    {"name": "pitfalls_avoided", "direction": "higher_is_better", "min_delta": 1, "required": True},
                ],
                "min_winning_dimensions": 4,
                "require_primitive_usage": True,
                "require_candidate_boundary": True,
            },
        )
        bad_lift = plan_primitive_lift_comparison(
            {"candidate": False, "serves_truth": True},
            {
                "dimensions": [{"name": "prompt_tokens", "direction": "lower_is_better", "required": True}],
                "min_winning_dimensions": 1,
                "require_primitive_usage": True,
                "require_candidate_boundary": True,
            },
        )
        pitfalls = plan_pitfall_avoidance_matrix(
            {
                "pitfall_ids": ["silent_row_drops", "duplicate_invoices"],
                "evidence": [
                    {"pitfall_id": "silent_row_drops", "avoided": True, "evidence_ref": "proofs/row-count.json"},
                    {"pitfall_id": "duplicate_invoices", "avoided": True, "evidence_ref": "proofs/dedupe.json"},
                ],
                "candidate": True,
                "serves_truth": False,
            },
            {"required_pitfalls": ["silent_row_drops"], "require_all_avoided": True, "require_evidence_ref": True, "min_avoided": 2, "require_candidate_boundary": True},
        )
        bad_pitfalls = plan_pitfall_avoidance_matrix(
            {
                "pitfall_ids": ["silent_row_drops", "duplicate_invoices"],
                "evidence": [{"pitfall_id": "silent_row_drops", "avoided": False}],
                "candidate": False,
                "serves_truth": True,
            },
            {"required_pitfalls": ["non_idempotent_retries"], "require_all_avoided": True, "require_evidence_ref": True, "min_avoided": 2, "require_candidate_boundary": True},
        )
        evidence_pack = plan_route_promotion_evidence_pack(
            {
                "route_id": "csv-import-runtime-reuse",
                "primitive_ids": ["grp:teleon.csv_import.plan@1"],
                "evidence_refs": ["reuse-observation", "lift-comparison"],
                "reuse_observation_ref": "reuse-observation",
                "lift_comparison_ref": "lift-comparison",
                "token_savings_ref": "token-savings",
                "pitfall_matrix_ref": "pitfall-matrix",
                "proof_bundle_ref": "proof-bundle",
                "owner_review_ref": "owner-review",
                "candidate": True,
                "serves_truth": False,
            },
            {
                "required_evidence_refs": ["reuse-observation", "lift-comparison"],
                "require_reuse_observation": True,
                "require_lift_comparison": True,
                "require_token_savings": True,
                "require_pitfall_matrix": True,
                "require_proof_bundle": True,
                "require_owner_review": True,
                "require_candidate_boundary": True,
            },
        )
        bad_evidence_pack = plan_route_promotion_evidence_pack(
            {"candidate": False, "serves_truth": True},
            {
                "required_evidence_refs": ["reuse-observation"],
                "require_reuse_observation": True,
                "require_lift_comparison": True,
                "require_token_savings": True,
                "require_pitfall_matrix": True,
                "require_proof_bundle": True,
                "require_owner_review": True,
                "require_candidate_boundary": True,
            },
        )

        self.assertTrue(lift.ready)
        self.assertEqual(lift.winning_dimensions, ("wall_clock_minutes", "prompt_tokens", "test_pass_rate", "pitfalls_avoided"))
        self.assertTrue(lift.comparison_hash.startswith("primitive-lift-comparison:"))
        self.assertFalse(bad_lift.ready)
        self.assertIn("missing_baseline_metrics", bad_lift.blockers)
        self.assertIn("missing_candidate_metrics", bad_lift.blockers)
        self.assertIn("missing_baseline_metric:prompt_tokens", bad_lift.blockers)
        self.assertIn("winning_dimension_count_below_policy", bad_lift.blockers)
        self.assertIn("missing_primitive_groups_used", bad_lift.blockers)
        self.assertIn("candidate_boundary_not_declared", bad_lift.blockers)
        self.assertIn("serves_truth_must_be_false", bad_lift.blockers)
        self.assertTrue(pitfalls.ready)
        self.assertEqual(pitfalls.avoided_pitfalls, ("silent_row_drops", "duplicate_invoices"))
        self.assertFalse(bad_pitfalls.ready)
        self.assertIn("missing_required_pitfall:non_idempotent_retries", bad_pitfalls.blockers)
        self.assertIn("pitfall_not_avoided:silent_row_drops", bad_pitfalls.blockers)
        self.assertIn("missing_evidence_ref:silent_row_drops", bad_pitfalls.blockers)
        self.assertIn("missing_evidence:duplicate_invoices", bad_pitfalls.blockers)
        self.assertIn("avoided_pitfall_count_below_policy", bad_pitfalls.blockers)
        self.assertIn("candidate_boundary_not_declared", bad_pitfalls.blockers)
        self.assertIn("serves_truth_must_be_false", bad_pitfalls.blockers)
        self.assertTrue(evidence_pack.ready)
        self.assertEqual(evidence_pack.route_id, "csv_import_runtime_reuse")
        self.assertFalse(bad_evidence_pack.ready)
        self.assertIn("missing_route_id", bad_evidence_pack.blockers)
        self.assertIn("missing_primitive_ids", bad_evidence_pack.blockers)
        self.assertIn("missing_evidence_ref:reuse-observation", bad_evidence_pack.blockers)
        self.assertIn("missing_reuse_observation_ref", bad_evidence_pack.blockers)
        self.assertIn("missing_lift_comparison_ref", bad_evidence_pack.blockers)
        self.assertIn("missing_token_savings_ref", bad_evidence_pack.blockers)
        self.assertIn("missing_pitfall_matrix_ref", bad_evidence_pack.blockers)
        self.assertIn("missing_proof_bundle_ref", bad_evidence_pack.blockers)
        self.assertIn("missing_owner_review_ref", bad_evidence_pack.blockers)
        self.assertIn("candidate_boundary_not_declared", bad_evidence_pack.blockers)
        self.assertIn("serves_truth_must_be_false", bad_evidence_pack.blockers)

    def test_plan_runtime_shape_adapters_enforce_wrapper_only_reuse(self) -> None:
        adapter = plan_runtime_shape_adapter(
            {
                "core_group_edge": "CsvFile+ImportPolicy -> ImportReceipt",
                "runtime_shape": "api.endpoint",
                "wrapper_edges": ["HttpRequest -> AuthenticatedRequest", "AuthenticatedRequest -> CoreInput", "CoreOutput -> HttpResponse"],
                "adapter_mutators": ["api_endpoint_wrapper", "schema_validator_inserter"],
                "proof_requirements": ["openapi_contract_test", "authz_test"],
                "effects": ["network_read", "network_write_plan"],
                "candidate": True,
                "serves_truth": False,
            },
            {
                "allowed_runtime_shapes": ["api.endpoint", "queue.consumer"],
                "min_wrapper_edges": 2,
                "required_wrapper_tokens_by_shape": {"api.endpoint": ["HttpRequest", "HttpResponse"]},
                "required_mutators_by_shape": {"api.endpoint": ["api_endpoint_wrapper", "schema_validator_inserter"]},
                "required_proof_by_shape": {"api.endpoint": ["openapi_contract_test", "authz_test"]},
                "required_effects_by_shape": {"api.endpoint": ["network_read"]},
                "require_candidate_boundary": True,
            },
        )
        bad_adapter = plan_runtime_shape_adapter(
            {"runtime_shape": "microservice", "wrapper_edges": ["QueueMessage -> CoreInput"], "candidate": False, "serves_truth": True},
            {
                "allowed_runtime_shapes": ["api.endpoint"],
                "min_wrapper_edges": 2,
                "required_wrapper_tokens_by_shape": {"microservice": ["HttpRequest"]},
                "required_mutators_by_shape": {"microservice": ["microservice_bundle_wrapper"]},
                "required_proof_by_shape": {"microservice": ["contract_test"]},
                "required_effects_by_shape": {"microservice": ["network_read"]},
                "require_candidate_boundary": True,
            },
        )
        matrix = plan_runtime_shape_adapter_matrix(
            {
                "adapters": [
                    {
                        "runtime_shape": "api.endpoint",
                        "core_group_edge": "CsvFile+ImportPolicy -> ImportReceipt",
                        "route_reused": True,
                        "proof_status": "pass",
                        "wrapper_edges": ["HttpRequest -> CoreInput"],
                        "adapter_mutators": ["api_endpoint_wrapper"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "runtime_shape": "queue.consumer",
                        "core_group_edge": "CsvFile+ImportPolicy -> ImportReceipt",
                        "route_reused": True,
                        "proof_status": "pass",
                        "wrapper_edges": ["QueueMessage -> CoreInput"],
                        "adapter_mutators": ["queue_consumer_wrapper"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                ]
            },
            {
                "min_adapters": 2,
                "min_runtime_shapes": 2,
                "required_runtime_shapes": ["api.endpoint", "queue.consumer"],
                "require_single_core_group_edge": True,
                "require_route_reused": True,
                "require_proof_status_pass": True,
                "require_wrapper_edges": True,
                "require_adapter_mutators": True,
                "require_candidate_boundary": True,
            },
        )
        bad_matrix = plan_runtime_shape_adapter_matrix(
            {
                "adapters": [
                    {"runtime_shape": "api.endpoint", "core_group_edge": "A -> B", "route_reused": False, "proof_status": "fail", "candidate": False, "serves_truth": True},
                    {"runtime_shape": "api.endpoint", "core_group_edge": "C -> D", "route_reused": True, "proof_status": "pass", "candidate": True, "serves_truth": False},
                ]
            },
            {
                "min_adapters": 3,
                "min_runtime_shapes": 2,
                "required_runtime_shapes": ["api.endpoint", "queue.consumer"],
                "require_single_core_group_edge": True,
                "require_route_reused": True,
                "require_proof_status_pass": True,
                "require_wrapper_edges": True,
                "require_adapter_mutators": True,
                "require_candidate_boundary": True,
            },
        )

        self.assertTrue(adapter.ready)
        self.assertEqual(adapter.runtime_shape, "api_endpoint")
        self.assertTrue(adapter.adapter_hash.startswith("runtime-shape-adapter:"))
        self.assertFalse(bad_adapter.ready)
        self.assertIn("missing_core_group_edge", bad_adapter.blockers)
        self.assertIn("runtime_shape_not_allowed:microservice", bad_adapter.blockers)
        self.assertIn("wrapper_edges_below_policy", bad_adapter.blockers)
        self.assertIn("missing_adapter_mutator:microservice:microservice_bundle_wrapper", bad_adapter.blockers)
        self.assertIn("missing_proof_requirement:microservice:contract_test", bad_adapter.blockers)
        self.assertIn("missing_effect:microservice:network_read", bad_adapter.blockers)
        self.assertIn("candidate_boundary_not_declared", bad_adapter.blockers)
        self.assertIn("serves_truth_must_be_false", bad_adapter.blockers)
        self.assertTrue(matrix.ready)
        self.assertEqual(matrix.runtime_shapes, ("api_endpoint", "queue_consumer"))
        self.assertFalse(bad_matrix.ready)
        self.assertIn("adapter_count_below_policy", bad_matrix.blockers)
        self.assertIn("runtime_shape_count_below_policy", bad_matrix.blockers)
        self.assertIn("missing_runtime_shape:queue_consumer", bad_matrix.blockers)
        self.assertIn("multiple_core_group_edges", bad_matrix.blockers)
        self.assertIn("adapter_1_route_not_reused", bad_matrix.blockers)
        self.assertIn("adapter_1_proof_not_pass", bad_matrix.blockers)
        self.assertIn("adapter_1_missing_wrapper_edges", bad_matrix.blockers)
        self.assertIn("adapter_1_missing_adapter_mutators", bad_matrix.blockers)
        self.assertIn("adapter_1_candidate_boundary_not_declared", bad_matrix.blockers)
        self.assertIn("adapter_1_serves_truth_must_be_false", bad_matrix.blockers)

    def test_compile_surface_registry_cards_from_api_event_and_service_specs(self) -> None:
        api_cards = compile_openapi_endpoint_primitive_cards(
            {
                "operations": [
                    {
                        "operation_id": "createInvoice",
                        "method": "POST",
                        "path": "/v1/invoices",
                        "response_codes": ["201"],
                        "visible_edge": "HttpRequest[CreateInvoice] -> HttpResponse[InvoiceReceipt]",
                        "security": [{"oauth2": ["invoice.write"]}],
                    }
                ]
            },
            {"primitive_id_prefix": "api:", "require_success_response": True, "require_auth_declared": True, "require_candidate_boundary": True},
        )
        bad_api_cards = compile_openapi_endpoint_primitive_cards(
            {"operations": [{"method": "POST", "path": "/v1/invoices", "response_codes": ["400"]}]},
            {"primitive_id_prefix": "api:", "require_success_response": True, "require_auth_declared": True, "require_candidate_boundary": True},
        )
        event_cards = compile_asyncapi_event_primitive_cards(
            {
                "operations": [
                    {
                        "operation_id": "publishInvoiceCreated",
                        "action": "publish",
                        "channel": "invoice.created",
                        "message_name": "InvoiceCreated",
                        "visible_edge": "AsyncMessage[InvoiceCreated] -> PublishReceipt",
                    }
                ]
            },
            {"primitive_id_prefix": "evt:"},
        )
        bad_event_cards = compile_asyncapi_event_primitive_cards(
            {"operations": [{"operation_id": "publishInvoiceCreated", "action": "publish"}]},
            {"primitive_id_prefix": "evt:", "require_channel": True, "require_message_name": True},
        )
        service_cards = compile_service_surface_primitive_cards(
            {
                "service_name": "billing-service",
                "surfaces": [
                    {"name": "POST /v1/invoices", "kind": "api_endpoint", "visibility": "public", "auth": "oauth2", "visible_edge": "CreateInvoiceRequest -> InvoiceReceipt"},
                    {"name": "payment-import-worker", "kind": "queue_consumer", "visibility": "internal", "visible_edge": "QueueMessage[PaymentImport] -> JobExecutionReceipt"},
                ],
            },
            {"primitive_id_prefix": "svc:", "required_surface_kinds": ["api_endpoint", "queue_consumer"], "require_auth_for_public": True, "min_surfaces": 2},
        )
        bad_service_cards = compile_service_surface_primitive_cards(
            {"surfaces": [{"name": "POST /v1/invoices", "kind": "api_endpoint", "visibility": "public"}]},
            {"required_surface_kinds": ["api_endpoint", "queue_consumer"], "require_auth_for_public": True, "min_surfaces": 2},
        )

        self.assertTrue(api_cards.ready)
        self.assertEqual(api_cards.primitive_ids, ("api:create_invoice@1",))
        self.assertEqual(api_cards.cards[0]["kind"], "api.endpoint")
        self.assertEqual(api_cards.cards[0]["input_edge"], "HttpRequest[CreateInvoice]")
        self.assertIs(api_cards.cards[0]["candidate"], True)
        self.assertIs(api_cards.cards[0]["serves_truth"], False)
        self.assertFalse(bad_api_cards.ready)
        self.assertIn("operation_1_missing_operation_id", bad_api_cards.blockers)
        self.assertIn("post_v1_invoices:missing_success_response", bad_api_cards.blockers)
        self.assertIn("post_v1_invoices:missing_auth", bad_api_cards.blockers)
        self.assertTrue(event_cards.ready)
        self.assertEqual(event_cards.primitive_ids, ("evt:publish_invoice_created@1",))
        self.assertEqual(event_cards.cards[0]["runtime_targets"], ("event.handler", "queue.consumer", "contract.test"))
        self.assertFalse(bad_event_cards.ready)
        self.assertIn("publishInvoiceCreated:missing_channel", bad_event_cards.blockers)
        self.assertIn("publishInvoiceCreated:missing_message_name", bad_event_cards.blockers)
        self.assertTrue(service_cards.ready)
        self.assertEqual(service_cards.primitive_ids, ("svc:billing_service.api_endpoint.post_v1_invoices@1", "svc:billing_service.queue_consumer.payment_import_worker@1"))
        self.assertEqual(service_cards.cards[1]["kind"], "queue.consumer")
        self.assertFalse(bad_service_cards.ready)
        self.assertIn("missing_service_name", bad_service_cards.blockers)
        self.assertIn("public_surface_missing_auth:POST /v1/invoices", bad_service_cards.blockers)
        self.assertIn("missing_required_surface_kind:queue_consumer", bad_service_cards.blockers)
        self.assertIn("surface_count_below_policy", bad_service_cards.blockers)

    def test_decompose_benchmark_task_and_compare_route_token_usage(self) -> None:
        decomposition = decompose_benchmark_task_to_primitive_components(
            {
                "task_id": "task:invoice-import-api",
                "components": [
                    {
                        "component_id": "comp:csv_parse",
                        "kind": "data_import",
                        "input_edge": "CsvBytes",
                        "output_edge": "ParsedRows",
                        "proof_requirements": ["csv_fixture_test"],
                        "estimated_tokens": 300,
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "component_id": "comp:idempotent_endpoint",
                        "kind": "api_endpoint",
                        "input_edge": "HttpRequest[Import]",
                        "output_edge": "HttpResponse[ImportReceipt]",
                        "proof_requirements": ["openapi_contract_test"],
                        "estimated_tokens": 450,
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "component_id": "comp:audit_receipt",
                        "kind": "audit",
                        "core_group_edge": "ImportDecision -> AuditReceipt",
                        "proof_requirements": ["audit_receipt_test"],
                        "estimated_tokens": 200,
                        "candidate": True,
                        "serves_truth": False,
                    },
                ],
            },
            {
                "min_components": 3,
                "required_component_kinds": ["data_import", "api_endpoint", "audit"],
                "require_component_kind": True,
                "require_visible_edges": True,
                "require_proof_requirements": True,
                "max_component_token_estimate": 500,
                "require_candidate_boundary": True,
            },
        )
        bad_decomposition = decompose_benchmark_task_to_primitive_components(
            {
                "components": [
                    {"kind": "api_endpoint", "estimated_tokens": 700, "candidate": False, "serves_truth": True},
                ]
            },
            {
                "min_components": 2,
                "required_component_kinds": ["data_import"],
                "require_component_kind": True,
                "require_visible_edges": True,
                "require_proof_requirements": True,
                "max_component_token_estimate": 500,
                "require_candidate_boundary": True,
            },
        )
        comparison = compare_benchmark_route_token_usage(
            {
                "baseline_task_id": "task:invoice-import-api",
                "primitive_task_id": "task:invoice-import-api",
                "baseline_prompt_tokens": 1800,
                "baseline_completion_tokens": 900,
                "components": [
                    {"component_id": "comp:csv_parse", "tokens": 300},
                    {"component_id": "comp:idempotent_endpoint", "tokens": 450},
                    {"component_id": "comp:audit_receipt", "tokens": 200},
                ],
                "baseline_trace_ref": "runs/baseline/trace.jsonl",
                "primitive_trace_ref": "runs/primitive/trace.jsonl",
                "candidate": True,
                "serves_truth": False,
            },
            {
                "min_savings_percent": 50,
                "require_component_attribution": True,
                "required_component_ids": ["comp:csv_parse", "comp:idempotent_endpoint"],
                "require_baseline_trace_ref": True,
                "require_primitive_trace_ref": True,
                "require_same_task_id": True,
                "require_candidate_boundary": True,
            },
        )
        bad_comparison = compare_benchmark_route_token_usage(
            {
                "baseline_tokens": 100,
                "primitive_route_tokens": 95,
                "baseline_task_id": "task:a",
                "primitive_task_id": "task:b",
                "candidate": False,
                "serves_truth": True,
            },
            {
                "min_savings_percent": 50,
                "require_component_attribution": True,
                "required_component_ids": ["comp:csv_parse"],
                "require_baseline_trace_ref": True,
                "require_primitive_trace_ref": True,
                "require_same_task_id": True,
                "require_candidate_boundary": True,
            },
        )

        self.assertTrue(decomposition.ready)
        self.assertEqual(decomposition.component_ids, ("comp:csv_parse", "comp:idempotent_endpoint", "comp:audit_receipt"))
        self.assertIn("CsvBytes -> ParsedRows", decomposition.core_group_edges)
        self.assertTrue(decomposition.decomposition_hash.startswith("benchmark-primitive-decomposition:"))
        self.assertFalse(bad_decomposition.ready)
        self.assertIn("missing_task_id", bad_decomposition.blockers)
        self.assertIn("component_count_below_policy", bad_decomposition.blockers)
        self.assertIn("component_1_missing_id", bad_decomposition.blockers)
        self.assertIn("component_1:component_token_estimate_exceeds_policy", bad_decomposition.blockers)
        self.assertIn("component_1:missing_visible_edge", bad_decomposition.blockers)
        self.assertIn("component_1:missing_proof_requirements", bad_decomposition.blockers)
        self.assertIn("component_1:candidate_boundary_not_declared", bad_decomposition.blockers)
        self.assertIn("component_1:serves_truth_must_be_false", bad_decomposition.blockers)
        self.assertIn("missing_required_component_kind:data_import", bad_decomposition.blockers)
        self.assertTrue(comparison.ready)
        self.assertEqual(comparison.baseline_tokens, 2700)
        self.assertEqual(comparison.primitive_route_tokens, 950)
        self.assertEqual(comparison.savings_percent, 64.81)
        self.assertFalse(bad_comparison.ready)
        self.assertIn("missing_component_attribution", bad_comparison.blockers)
        self.assertIn("missing_component_id:comp:csv_parse", bad_comparison.blockers)
        self.assertIn("token_savings_below_policy", bad_comparison.blockers)
        self.assertIn("missing_baseline_trace_ref", bad_comparison.blockers)
        self.assertIn("missing_primitive_trace_ref", bad_comparison.blockers)
        self.assertIn("task_id_mismatch", bad_comparison.blockers)
        self.assertIn("candidate_boundary_not_declared", bad_comparison.blockers)
        self.assertIn("serves_truth_must_be_false", bad_comparison.blockers)

    def test_ingest_benchmark_trace_pairs_pairs_run_artifacts_for_evaluation(self) -> None:
        ingestion = ingest_benchmark_trace_pairs(
            {
                "run_artifacts": [
                    {
                        "task_id": "task:csv-api",
                        "arm": "baseline",
                        "trace_ref": "runs/baseline/csv-api.jsonl",
                        "prompt_tokens": 1800,
                        "completion_tokens": 900,
                        "token_source": "actual",
                        "success": True,
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "task_id": "task:csv-api",
                        "arm": "aidevexplorer_candidate",
                        "trace_ref": "runs/primitive/csv-api.jsonl",
                        "prompt_tokens": 650,
                        "completion_tokens": 350,
                        "token_source": "actual",
                        "success": True,
                        "route_reused": True,
                        "runtime_shape": "api.endpoint",
                        "tool_consumer": "Codex",
                        "primitive_ids": ["grp:teleon.benchmark_primitive_decomposition.plan@1"],
                        "component_attribution": [
                            {"component_id": "comp:csv_parse", "tokens": 300},
                            {"component_id": "comp:idempotent_endpoint", "tokens": 450},
                            {"component_id": "comp:audit_receipt", "tokens": 250},
                        ],
                        "proof_refs": ["proofs/csv-api/contract.json"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "task_id": "task:csv-worker",
                        "arm": "baseline",
                        "trace_ref": "runs/baseline/csv-worker.jsonl",
                        "total_tokens": 2400,
                        "token_source": "actual",
                        "success": True,
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "task_id": "task:csv-worker",
                        "arm": "primitive",
                        "trace_ref": "runs/primitive/csv-worker.jsonl",
                        "total_tokens": 900,
                        "token_source": "actual",
                        "success": True,
                        "route_reused": True,
                        "runtime_shape": "queue.consumer",
                        "tool_consumer": "Claude Code",
                        "primitive_ids": ["grp:teleon.runtime_shape_adapter_matrix.plan@1"],
                        "component_attribution": [
                            {"component_id": "comp:csv_parse", "tokens": 300},
                            {"component_id": "comp:queue_wrapper", "tokens": 250},
                        ],
                        "proof_refs": ["proofs/csv-worker/queue.json"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                ]
            },
            {
                "min_pairs": 2,
                "required_task_ids": ["task:csv-api", "task:csv-worker"],
                "baseline_arm_names": ["baseline"],
                "primitive_arm_names": ["primitive", "aidevexplorer_candidate"],
                "require_trace_refs": True,
                "require_actual_tokens": True,
                "require_successful_runs": True,
                "require_route_reused": True,
                "require_primitive_ids": True,
                "require_component_attribution": True,
                "min_component_count": 2,
                "require_proof_refs": True,
                "require_candidate_boundary": True,
            },
        )
        evaluation = evaluate_benchmark_trace_pair(
            ingestion.trace_pairs[0],
            {
                "min_savings_percent": 50,
                "require_same_task_id": True,
                "require_trace_refs": True,
                "require_actual_tokens": True,
                "require_success": True,
                "require_component_attribution": True,
                "min_component_count": 3,
                "required_component_ids": ["comp:csv_parse", "comp:idempotent_endpoint"],
                "require_primitives": True,
                "require_proof_refs": True,
                "require_candidate_boundary": True,
            },
        )
        bad_ingestion = ingest_benchmark_trace_pairs(
            {
                "run_artifacts": [
                    {"arm": "baseline", "candidate": False, "serves_truth": True},
                    {
                        "task_id": "task:bad",
                        "arm": "baseline",
                        "trace_ref": "",
                        "total_tokens": 0,
                        "token_source": "estimate",
                        "success": False,
                        "candidate": False,
                        "serves_truth": True,
                    },
                    {
                        "task_id": "task:bad",
                        "arm": "baseline",
                        "trace_ref": "runs/duplicate.jsonl",
                        "total_tokens": 1000,
                        "token_source": "actual",
                        "success": True,
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "task_id": "task:primitive-only",
                        "arm": "primitive",
                        "trace_ref": "runs/primitive-only.jsonl",
                        "total_tokens": 500,
                        "token_source": "actual",
                        "success": True,
                        "route_reused": False,
                        "candidate": False,
                        "serves_truth": True,
                    },
                    {
                        "task_id": "task:unknown",
                        "arm": "control",
                        "trace_ref": "runs/control.jsonl",
                        "total_tokens": 100,
                        "candidate": True,
                        "serves_truth": False,
                    },
                ]
            },
            {
                "min_pairs": 1,
                "required_task_ids": ["task:bad", "task:missing"],
                "require_trace_refs": True,
                "require_actual_tokens": True,
                "require_successful_runs": True,
                "require_route_reused": True,
                "require_primitive_ids": True,
                "require_component_attribution": True,
                "min_component_count": 1,
                "require_proof_refs": True,
                "require_candidate_boundary": True,
            },
        )

        self.assertTrue(ingestion.ready)
        self.assertEqual(ingestion.pair_count, 2)
        self.assertEqual(ingestion.task_ids, ("task:csv-api", "task:csv-worker"))
        self.assertEqual(ingestion.trace_pairs[0]["baseline_trace"]["total_tokens"], 2700)
        self.assertEqual(ingestion.trace_pairs[0]["primitive_trace"]["tool_consumer"], "codex")
        self.assertTrue(ingestion.ingestion_hash.startswith("benchmark-trace-ingestion:"))
        self.assertTrue(evaluation.ready)
        self.assertEqual(evaluation.task_id, "task:csv-api")
        self.assertEqual(evaluation.savings_percent, 62.96)
        self.assertFalse(bad_ingestion.ready)
        self.assertIn("artifact_1_missing_task_id", bad_ingestion.blockers)
        self.assertIn("task:bad:baseline_missing_trace_ref", bad_ingestion.blockers)
        self.assertIn("task:bad:baseline_tokens_are_estimated", bad_ingestion.blockers)
        self.assertIn("task:bad:baseline_missing_tokens", bad_ingestion.blockers)
        self.assertIn("task:bad:baseline_not_successful", bad_ingestion.blockers)
        self.assertIn("task:bad:baseline_candidate_boundary_not_declared", bad_ingestion.blockers)
        self.assertIn("task:bad:baseline_serves_truth_must_be_false", bad_ingestion.blockers)
        self.assertIn("task:bad:duplicate_baseline_trace", bad_ingestion.blockers)
        self.assertIn("task:primitive-only:primitive_route_not_reused", bad_ingestion.blockers)
        self.assertIn("task:primitive-only:primitive_missing_primitive_ids", bad_ingestion.blockers)
        self.assertIn("task:primitive-only:primitive_missing_component_attribution", bad_ingestion.blockers)
        self.assertIn("task:primitive-only:primitive_component_count_below_policy", bad_ingestion.blockers)
        self.assertIn("task:primitive-only:primitive_missing_proof_refs", bad_ingestion.blockers)
        self.assertIn("task:primitive-only:primitive_candidate_boundary_not_declared", bad_ingestion.blockers)
        self.assertIn("task:primitive-only:primitive_serves_truth_must_be_false", bad_ingestion.blockers)
        self.assertIn("task:unknown:unknown_arm:control", bad_ingestion.blockers)
        self.assertIn("task:bad:missing_primitive_trace", bad_ingestion.blockers)
        self.assertIn("task:primitive-only:missing_baseline_trace", bad_ingestion.blockers)
        self.assertIn("missing_required_trace_pair:task:bad", bad_ingestion.blockers)
        self.assertIn("missing_required_trace_pair:task:missing", bad_ingestion.blockers)
        self.assertIn("trace_pair_count_below_policy", bad_ingestion.blockers)

    def test_evaluate_benchmark_trace_pair_requires_actual_paired_evidence(self) -> None:
        evaluation = evaluate_benchmark_trace_pair(
            {
                "task_id": "task:invoice-import-api",
                "baseline_trace": {
                    "task_id": "task:invoice-import-api",
                    "trace_ref": "runs/2026-07-01/baseline/task.trace.jsonl",
                    "prompt_tokens": 1800,
                    "completion_tokens": 900,
                    "token_source": "actual",
                    "success": True,
                },
                "primitive_trace": {
                    "task_id": "task:invoice-import-api",
                    "trace_ref": "runs/2026-07-01/primitive/task.trace.jsonl",
                    "prompt_tokens": 650,
                    "completion_tokens": 350,
                    "token_source": "actual",
                    "success": True,
                    "primitive_ids": ["grp:teleon.benchmark_primitive_decomposition.plan@1"],
                    "component_attribution": [
                        {"component_id": "comp:csv_parse", "tokens": 300},
                        {"component_id": "comp:idempotent_endpoint", "tokens": 450},
                        {"component_id": "comp:audit_receipt", "tokens": 250},
                    ],
                    "proof_refs": ["proofs/task/unit.xml", "proofs/task/contract.json"],
                },
                "candidate": True,
                "serves_truth": False,
            },
            {
                "min_savings_percent": 50,
                "require_same_task_id": True,
                "require_trace_refs": True,
                "require_actual_tokens": True,
                "require_success": True,
                "require_component_attribution": True,
                "min_component_count": 3,
                "required_component_ids": ["comp:csv_parse", "comp:idempotent_endpoint"],
                "require_primitives": True,
                "require_proof_refs": True,
                "require_candidate_boundary": True,
            },
        )
        bad_evaluation = evaluate_benchmark_trace_pair(
            {
                "task_id": "task:a",
                "baseline_trace": {
                    "task_id": "task:a",
                    "trace_ref": "runs/baseline.trace.jsonl",
                    "total_tokens": 1000,
                    "estimate_only": True,
                    "success": False,
                },
                "primitive_trace": {
                    "task_id": "task:b",
                    "trace_ref": "",
                    "total_tokens": 950,
                    "token_source": "estimate",
                    "success": False,
                },
                "candidate": False,
                "serves_truth": True,
            },
            {
                "min_savings_percent": 30,
                "require_same_task_id": True,
                "require_trace_refs": True,
                "require_actual_tokens": True,
                "require_success": True,
                "require_component_attribution": True,
                "min_component_count": 2,
                "required_component_ids": ["comp:csv_parse"],
                "require_primitives": True,
                "require_proof_refs": True,
                "require_candidate_boundary": True,
            },
        )

        self.assertTrue(evaluation.ready)
        self.assertEqual(evaluation.task_id, "task:invoice-import-api")
        self.assertEqual(evaluation.baseline_tokens, 2700)
        self.assertEqual(evaluation.primitive_tokens, 1000)
        self.assertEqual(evaluation.savings_percent, 62.96)
        self.assertEqual(evaluation.component_ids, ("comp:csv_parse", "comp:idempotent_endpoint", "comp:audit_receipt"))
        self.assertEqual(evaluation.primitive_ids, ("grp:teleon.benchmark_primitive_decomposition.plan@1",))
        self.assertEqual(evaluation.proof_refs, ("proofs/task/unit.xml", "proofs/task/contract.json"))
        self.assertTrue(evaluation.evaluation_hash.startswith("benchmark-trace-pair-evaluation:"))
        self.assertFalse(bad_evaluation.ready)
        self.assertIn("task_id_mismatch", bad_evaluation.blockers)
        self.assertIn("primitive_task_id_mismatch", bad_evaluation.blockers)
        self.assertIn("missing_primitive_trace_ref", bad_evaluation.blockers)
        self.assertIn("baseline_tokens_are_estimated", bad_evaluation.blockers)
        self.assertIn("primitive_tokens_are_estimated", bad_evaluation.blockers)
        self.assertIn("baseline_trace_not_successful", bad_evaluation.blockers)
        self.assertIn("primitive_trace_not_successful", bad_evaluation.blockers)
        self.assertIn("missing_component_attribution", bad_evaluation.blockers)
        self.assertIn("component_count_below_policy", bad_evaluation.blockers)
        self.assertIn("missing_component_id:comp:csv_parse", bad_evaluation.blockers)
        self.assertIn("missing_primitive_ids", bad_evaluation.blockers)
        self.assertIn("missing_proof_refs", bad_evaluation.blockers)
        self.assertIn("token_savings_below_policy", bad_evaluation.blockers)
        self.assertIn("candidate_boundary_not_declared", bad_evaluation.blockers)
        self.assertIn("serves_truth_must_be_false", bad_evaluation.blockers)

    def test_evaluate_benchmark_route_promotion_candidate_aggregates_route_lift(self) -> None:
        candidate = evaluate_benchmark_route_promotion_candidate(
            {
                "route_id": "csv-import-runtime-route",
                "primitive_ids": ["grp:teleon.benchmark_primitive_decomposition.plan@1"],
                "benchmark_runs": [
                    {
                        "task_id": "task:csv-import-api",
                        "runtime_shape": "api.endpoint",
                        "tool_consumer": "Codex",
                        "baseline_tokens": 3000,
                        "primitive_tokens": 1200,
                        "token_source": "actual",
                        "success": True,
                        "route_reused": True,
                        "proof_refs": ["proofs/api-contract.json"],
                        "primitive_ids": ["grp:teleon.runtime_shape_adapter.plan@1"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "task_id": "task:csv-import-worker",
                        "runtime_shape": "queue.consumer",
                        "tool_consumer": "Claude Code",
                        "baseline_tokens": 2600,
                        "primitive_tokens": 1000,
                        "token_source": "actual",
                        "success": True,
                        "route_reused": True,
                        "proof_refs": ["proofs/queue-worker.json"],
                        "primitive_ids": ["grp:teleon.runtime_shape_adapter_matrix.plan@1"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "task_id": "task:csv-import-dashboard",
                        "runtime_shape": "dashboard.report",
                        "tool_consumer": "Gemma 4",
                        "baseline_tokens": 2400,
                        "primitive_tokens": 960,
                        "token_source": "actual",
                        "success": True,
                        "route_reused": True,
                        "proof_refs": ["proofs/dashboard.json"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "task_id": "task:csv-import-workflow",
                        "runtime_shape": "workflow.automation",
                        "tool_consumer": "Kimi",
                        "baseline_tokens": 2200,
                        "primitive_tokens": 880,
                        "token_source": "actual",
                        "success": True,
                        "route_reused": True,
                        "proof_refs": ["proofs/workflow.json"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                    {
                        "task_id": "task:csv-import-service",
                        "runtime_shape": "microservice",
                        "tool_consumer": "GLM",
                        "baseline_tokens": 2500,
                        "primitive_tokens": 1000,
                        "token_source": "actual",
                        "success": True,
                        "route_reused": True,
                        "proof_refs": ["proofs/service.json"],
                        "candidate": True,
                        "serves_truth": False,
                    },
                ],
                "candidate": True,
                "serves_truth": False,
            },
            {
                "min_runs": 5,
                "min_tasks": 5,
                "min_runtime_shapes": 5,
                "min_tool_consumers": 5,
                "required_runtime_shapes": ["api.endpoint", "queue.consumer", "dashboard.report", "workflow.automation", "microservice"],
                "required_tool_consumers": ["Codex", "Claude Code", "Kimi", "GLM", "Gemma 4"],
                "required_primitive_ids": ["grp:teleon.benchmark_primitive_decomposition.plan@1"],
                "min_run_savings_percent": 50,
                "min_average_savings_percent": 55,
                "min_winning_run_percent": 100,
                "require_primitives": True,
                "require_task_id": True,
                "require_actual_tokens": True,
                "require_successful_runs": True,
                "require_route_reused": True,
                "require_proof_refs": True,
                "max_unresolved_pitfalls": 0,
                "require_candidate_boundary": True,
            },
        )
        bad_candidate = evaluate_benchmark_route_promotion_candidate(
            {
                "benchmark_runs": [
                    {
                        "task_id": "task:a",
                        "runtime_shape": "api.endpoint",
                        "tool_consumer": "Codex",
                        "baseline_tokens": 1000,
                        "primitive_tokens": 900,
                        "token_source": "estimate",
                        "success": False,
                        "route_reused": False,
                        "unresolved_pitfalls": ["duplicate_imports"],
                        "candidate": False,
                        "serves_truth": True,
                    }
                ],
                "candidate": False,
                "serves_truth": True,
            },
            {
                "min_runs": 2,
                "min_tasks": 2,
                "min_runtime_shapes": 2,
                "min_tool_consumers": 2,
                "required_runtime_shapes": ["api.endpoint", "queue.consumer"],
                "required_tool_consumers": ["Codex", "Claude Code"],
                "required_primitive_ids": ["grp:teleon.benchmark_primitive_decomposition.plan@1"],
                "min_run_savings_percent": 50,
                "min_average_savings_percent": 50,
                "min_winning_run_percent": 100,
                "require_primitives": True,
                "require_task_id": True,
                "require_actual_tokens": True,
                "require_successful_runs": True,
                "require_route_reused": True,
                "require_proof_refs": True,
                "require_no_unresolved_pitfalls": True,
                "max_unresolved_pitfalls": 0,
                "require_candidate_boundary": True,
            },
        )

        self.assertTrue(candidate.ready)
        self.assertEqual(candidate.route_id, "csv_import_runtime_route")
        self.assertEqual(candidate.run_count, 5)
        self.assertEqual(candidate.task_ids, ("task:csv-import-api", "task:csv-import-dashboard", "task:csv-import-service", "task:csv-import-worker", "task:csv-import-workflow"))
        self.assertEqual(candidate.runtime_shapes, ("api_endpoint", "dashboard_report", "microservice", "queue_consumer", "workflow_automation"))
        self.assertEqual(candidate.tool_consumers, ("claude_code", "codex", "gemma_4", "glm", "kimi"))
        self.assertEqual(candidate.average_savings_percent, 60.31)
        self.assertEqual(candidate.winning_run_percent, 100.0)
        self.assertTrue(candidate.candidate_hash.startswith("benchmark-route-promotion-candidate:"))
        self.assertFalse(bad_candidate.ready)
        self.assertIn("missing_route_id", bad_candidate.blockers)
        self.assertIn("run_1_not_successful", bad_candidate.blockers)
        self.assertIn("run_1_route_not_reused", bad_candidate.blockers)
        self.assertIn("run_1_missing_proof_refs", bad_candidate.blockers)
        self.assertIn("run_1_tokens_are_estimated", bad_candidate.blockers)
        self.assertIn("run_1_candidate_boundary_not_declared", bad_candidate.blockers)
        self.assertIn("run_1_serves_truth_must_be_false", bad_candidate.blockers)
        self.assertIn("run_count_below_policy", bad_candidate.blockers)
        self.assertIn("task_count_below_policy", bad_candidate.blockers)
        self.assertIn("runtime_shape_count_below_policy", bad_candidate.blockers)
        self.assertIn("tool_consumer_count_below_policy", bad_candidate.blockers)
        self.assertIn("missing_primitive_ids", bad_candidate.blockers)
        self.assertIn("missing_primitive_id:grp:teleon.benchmark_primitive_decomposition.plan@1", bad_candidate.blockers)
        self.assertIn("missing_runtime_shape:queue_consumer", bad_candidate.blockers)
        self.assertIn("missing_tool_consumer:claude_code", bad_candidate.blockers)
        self.assertIn("average_token_savings_below_policy", bad_candidate.blockers)
        self.assertIn("winning_run_percent_below_policy", bad_candidate.blockers)
        self.assertIn("unresolved_pitfall_count_above_policy", bad_candidate.blockers)
        self.assertIn("unresolved_pitfalls_present", bad_candidate.blockers)
        self.assertIn("candidate_boundary_not_declared", bad_candidate.blockers)
        self.assertIn("serves_truth_must_be_false", bad_candidate.blockers)

    def test_compile_deployment_surface_registry_cards_from_runtime_artifacts(self) -> None:
        container_cards = compile_container_runtime_primitive_cards(
            {
                "runtime_name": "billing-stack",
                "services": {
                    "api": {"image": "billing-api:1.2.3", "healthcheck": {"test": "curl /healthz"}, "environment": {"DATABASE_URL": "secret://db"}},
                    "worker": {"build": ".", "healthcheck": {"test": "python -m health"}},
                },
            },
            {"primitive_id_prefix": "ctr:", "require_image_or_build": True, "require_healthcheck": True, "require_secret_refs": True, "forbid_latest_image": True, "min_services": 2},
        )
        bad_container_cards = compile_container_runtime_primitive_cards(
            {"services": {"api": {"image": "billing:latest", "environment": {"API_TOKEN": "plain"}}}},
            {"require_image_or_build": True, "require_healthcheck": True, "require_secret_refs": True, "forbid_latest_image": True, "min_services": 2},
        )
        k8s_cards = compile_kubernetes_workload_primitive_cards(
            {
                "workloads": [
                    {"kind": "Deployment", "name": "billing-api", "images": ["billing-api:1.2.3"], "resource_limits": {"cpu": "500m"}, "readiness_probe": "/ready", "liveness_probe": "/live"},
                    {"kind": "Job", "name": "billing-backfill", "images": ["billing-job:1.2.3"], "resource_limits": {"cpu": "1"}},
                ]
            },
            {"primitive_id_prefix": "k8s:", "required_kinds": ["deployment", "job"], "require_images": True, "forbid_latest_image": True, "require_resource_limits": True, "require_probes": True},
        )
        bad_k8s_cards = compile_kubernetes_workload_primitive_cards(
            {"workloads": [{"kind": "Deployment", "name": "api", "images": ["api:latest"]}]},
            {"required_kinds": ["deployment", "job"], "require_images": True, "forbid_latest_image": True, "require_resource_limits": True, "require_probes": True},
        )
        terraform_cards = compile_terraform_module_primitive_cards(
            {
                "module_name": "billing-service",
                "variables": ["region", "image_tag"],
                "outputs": ["service_url"],
                "resources": [{"type": "aws_ecs_service", "name": "api", "tags": {"owner": "platform"}}],
            },
            {"primitive_id_prefix": "tf:", "allowed_resource_types": ["aws_ecs_service"], "require_variables": True, "require_outputs": True, "require_tags": True},
        )
        bad_terraform_cards = compile_terraform_module_primitive_cards(
            {"resources": [{"type": "aws_iam_user", "name": "root"}]},
            {"allowed_resource_types": ["aws_ecs_service"], "require_variables": True, "require_outputs": True, "require_tags": True},
        )
        ci_cards = compile_ci_workflow_primitive_cards(
            {
                "workflows": [
                    {"name": "primitive-registry-ci", "triggers": ["pull_request", "push"], "jobs": ["test", "validate"], "permissions": ["contents:read"], "artifacts": ["proof-bundle"]},
                ]
            },
            {"primitive_id_prefix": "ci:", "required_triggers": ["pull_request"], "require_permissions": True, "require_artifacts": True},
        )
        bad_ci_cards = compile_ci_workflow_primitive_cards(
            {"name": "ci", "triggers": ["push"], "jobs": []},
            {"required_triggers": ["pull_request"], "require_permissions": True, "require_artifacts": True},
        )

        self.assertTrue(container_cards.ready)
        self.assertEqual(container_cards.primitive_ids, ("ctr:billing_stack.api@1", "ctr:billing_stack.worker@1"))
        self.assertFalse(bad_container_cards.ready)
        self.assertIn("api:latest_image_forbidden", bad_container_cards.blockers)
        self.assertIn("api:missing_healthcheck", bad_container_cards.blockers)
        self.assertIn("api:inline_secret:API_TOKEN", bad_container_cards.blockers)
        self.assertIn("service_count_below_policy", bad_container_cards.blockers)
        self.assertTrue(k8s_cards.ready)
        self.assertEqual(k8s_cards.cards[0]["kind"], "kubernetes.deployment")
        self.assertFalse(bad_k8s_cards.ready)
        self.assertIn("api:latest_image_forbidden", bad_k8s_cards.blockers)
        self.assertIn("api:missing_resource_limits", bad_k8s_cards.blockers)
        self.assertIn("api:missing_readiness_or_liveness_probe", bad_k8s_cards.blockers)
        self.assertIn("missing_required_kind:job", bad_k8s_cards.blockers)
        self.assertTrue(terraform_cards.ready)
        self.assertEqual(terraform_cards.primitive_ids, ("tf:billing_service.aws_ecs_service.api@1",))
        self.assertFalse(bad_terraform_cards.ready)
        self.assertIn("missing_module_name", bad_terraform_cards.blockers)
        self.assertIn("missing_variables", bad_terraform_cards.blockers)
        self.assertIn("missing_outputs", bad_terraform_cards.blockers)
        self.assertIn("root:resource_type_not_allowed:aws_iam_user", bad_terraform_cards.blockers)
        self.assertIn("root:missing_tags", bad_terraform_cards.blockers)
        self.assertTrue(ci_cards.ready)
        self.assertEqual(ci_cards.primitive_ids, ("ci:primitive_registry_ci@1",))
        self.assertFalse(bad_ci_cards.ready)
        self.assertIn("ci:missing_trigger:pull_request", bad_ci_cards.blockers)
        self.assertIn("ci:missing_jobs", bad_ci_cards.blockers)
        self.assertIn("ci:missing_permissions", bad_ci_cards.blockers)
        self.assertIn("ci:missing_artifacts", bad_ci_cards.blockers)


if __name__ == "__main__":
    unittest.main()
