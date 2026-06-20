"""scripts.flywheel_proof_modules — the shipped proof registry the flywheel keeps green.

Separated from baltor_flywheel.py (registry DATA vs watcher LOGIC) so the watcher stays within its
line budget. Re-exported from baltor_flywheel, so `from scripts.baltor_flywheel import PROOF_MODULES`
still works for existing importers.
"""
from __future__ import annotations

#: The shipped proof self-tests the flywheel keeps green (module path → label).
PROOF_MODULES: list[tuple[str, str]] = [
    ("scripts/ingest/context_rot.py", "context_rot"),
    ("scripts/ingest/document_decompose.py", "document_decompose"),
    ("scripts/source_handle_resolver.py", "source_handle_resolver"),
    ("scripts/parser_router.py", "parser_router"),
    ("scripts/context_debt.py", "context_debt"),
    ("scripts/alias_resolver.py", "alias_resolver"),
    ("scripts/render_receipt.py", "render_receipt"),
    ("scripts/check_no_oracle_copy.py", "check_no_oracle_copy"),
    ("scripts/scan_mcp_manifests.py", "scan_mcp_manifests"),
    ("scripts/scan_agent_skills.py", "scan_agent_skills"),
    ("scripts/validate_stages.py", "validate_stages"),
    ("scripts/validate_tool_evidence_cards.py", "validate_tool_evidence_cards"),
    ("scripts/validate_context_schemas.py", "validate_context_schemas"),
    ("scripts/validate_compose.py", "validate_compose"),
    ("scripts/context_graph.py", "context_graph"),
    ("scripts/context_compress.py", "context_compress"),
    ("scripts/context_swarm.py", "context_swarm"),
    ("scripts/demo_full_app.py", "demo_full_app"),
    ("scripts/source_expansion.py", "source_expansion"),
    ("scripts/eval/context_lift_matrix.py", "context_lift_matrix"),
    ("scripts/demo_run_export.py", "demo_run_export"),
    ("scripts/ci_check.py", "ci_check"),
    ("scripts/check_demo_console_links.py", "check_demo_console_links"),
    ("scripts/check_prelaunch.py", "check_prelaunch"),
    ("scripts/baltor_acceptance.py", "baltor_acceptance"),
    ("scripts/context_events.py", "context_events"),
    ("scripts/check_event_integration.py", "check_event_integration"),
    ("scripts/check_admin_server.py", "check_admin_server"),
    ("scripts/check_live_pipeline.py", "check_live_pipeline"),
    ("scripts/check_experiments_isolation.py", "check_experiments_isolation"),
    ("scripts/ingest/decompose_to_context_objects.py", "decompose_to_context_objects"),
    ("scripts/ingest/parser_provider.py", "parser_provider"),
    ("scripts/ingest/parse_quality.py", "parse_quality"),
    ("scripts/ingest/parse_adjudicator.py", "parse_adjudicator"),
    ("scripts/check_parser_portfolio.py", "check_parser_portfolio"),
    ("scripts/ingest/sanctions_feed_live.py", "sanctions_feed_live"),
    ("scripts/check_live_ofac_receipt.py", "check_live_ofac_receipt"),
    ("scripts/ingest/ecfr_feed.py", "ecfr_feed"),
    ("scripts/ingest/federal_register_feed.py", "federal_register_feed"),
    ("scripts/validate_flywheel_schemas.py", "validate_flywheel_schemas"),
    ("scripts/validate_flywheel_workflows.py", "validate_flywheel_workflows"),
    ("scripts/check_gold_pack_contract.py", "check_gold_pack_contract"),
    ("scripts/demo_context_engine_proof.py", "demo_context_engine_proof"),
    ("scripts/check_design_tokens.py", "check_design_tokens"),
    ("scripts/context_memory_block.py", "context_memory_block"),
    ("scripts/make_review_pack.py", "make_review_pack"),
    ("scripts/check_review_pack_recorders.py", "check_review_pack_recorders"),
    # ── source/pipeline/artifact version ledger + reprocessing planner (v1) ──
    ("scripts/check_artifact_type_registry.py", "check_artifact_type_registry"),
    ("scripts/check_tenant_isolation_policy.py", "check_tenant_isolation_policy"),
    ("scripts/check_artifact_security_metadata.py", "check_artifact_security_metadata"),
    ("scripts/check_cfpb_source_graph_diff.py", "check_cfpb_source_graph_diff"),
    ("scripts/check_cfpb_multi_grain_artifacts.py", "check_cfpb_multi_grain_artifacts"),
    ("scripts/check_reprocess_source_change_scope.py", "check_reprocess_source_change_scope"),
    ("scripts/check_reprocess_pipeline_change_scope.py", "check_reprocess_pipeline_change_scope"),
    ("scripts/check_reprocess_security_policy_change.py", "check_reprocess_security_policy_change"),
    ("scripts/check_pipeline_run_fingerprint.py", "check_pipeline_run_fingerprint"),
    # ── C32 CFPB Artifact Graph Demo v1 (ledger + vectors + graph + conflicts + reconciliation) ──
    ("scripts/check_cfpb_artifact_ledger.py", "check_cfpb_artifact_ledger"),
    ("scripts/check_cfpb_vectorization.py", "check_cfpb_vectorization"),
    ("scripts/check_cfpb_deterministic_graph.py", "check_cfpb_deterministic_graph"),
    ("scripts/check_cfpb_conflict_detection.py", "check_cfpb_conflict_detection"),
    ("scripts/check_cfpb_reconciliation.py", "check_cfpb_reconciliation"),
    ("scripts/check_source_authority.py", "check_source_authority"),
    ("scripts/check_source_authority_registry_extended.py", "check_source_authority_registry_extended"),
    ("scripts/check_authority_rank_core_precedence.py", "check_authority_rank_core_precedence"),
    ("scripts/artifact_graph/authority_corroboration.py", "authority_corroboration"),
    ("scripts/check_cfpb_artifact_graph_demo.py", "check_cfpb_artifact_graph_demo"),
    # ── generalized runtime: hybrid storage + tenant resolver + LLM Gateway v1 ──
    ("scripts/check_storage_model_flexible.py", "check_storage_model_flexible"),
    ("scripts/check_tenant_store_resolver.py", "check_tenant_store_resolver"),
    ("scripts/check_llm_secret_hygiene.py", "check_llm_secret_hygiene"),
    ("scripts/check_llm_gateway_stub.py", "check_llm_gateway_stub"),
    ("scripts/check_llm_gateway_openai_config.py", "check_llm_gateway_openai_config"),
    ("scripts/check_llm_router_policy.py", "check_llm_router_policy"),
    # ── C32 Runtime Contracts & Processor Harness v1 (envelopes/schemas/ports/registry/harness/logging) ──
    ("scripts/check_runtime_envelopes.py", "check_runtime_envelopes"),
    ("scripts/check_runtime_schema_validation.py", "check_runtime_schema_validation"),
    ("scripts/check_processor_registry.py", "check_processor_registry"),
    ("scripts/check_processor_harness.py", "check_processor_harness"),
    ("scripts/check_cfpb_decompose_via_harness.py", "check_cfpb_decompose_via_harness"),
    ("scripts/check_worker_command_envelope.py", "check_worker_command_envelope"),
    ("scripts/check_structured_runtime_logging.py", "check_structured_runtime_logging"),
    ("scripts/check_invalid_command_envelope_safe_failure.py", "check_invalid_command_envelope_safe_failure"),
    # ── C40 Verification Gate v1 (the mandatory blocking gate between Enhancement and Optimization) ──
    ("scripts/check_verification_gate.py", "check_verification_gate"),
    # ── C43 Optimization Harness v1 (governed: wrappable/chainable optimizer suite, lift + regression gate) ──
    ("scripts/check_optimization_harness.py", "check_optimization_harness"),
    # ── C43.1 Optimization SUITE: multi-variant bake-off + consumption-readiness gate + external provider slots ──
    ("scripts/check_optimization_suite.py", "check_optimization_suite"),
    # ── C-CONSUME-1 Consumption Runtime: ingestion→consumption served ContextResponse (the forcing function) ──
    ("scripts/check_cfpb_to_consumption_end_to_end.py", "check_cfpb_to_consumption_end_to_end"),
    ("scripts/check_consumption_service.py", "check_consumption_service"),
    ("scripts/check_consumption_blocks_bad_artifacts.py", "check_consumption_blocks_bad_artifacts"),
    ("scripts/check_no_consumption_bypass.py", "check_no_consumption_bypass"),
    # ── PERFECT-MODE: section maturity matrix (honest inventory) + master full-stack critical-path proof ──
    ("scripts/check_section_maturity_matrix.py", "check_section_maturity_matrix"),
    ("scripts/check_baltor_full_stack_perfect.py", "check_baltor_full_stack_perfect"),
    # ── PERFECT+DOC-MODE: strategic visibility — living current-state report + opportunities + risk register ──
    ("scripts/report_current_state.py", "report_current_state"),
    ("scripts/check_opportunity_map.py", "check_opportunity_map"),
    ("scripts/check_risk_register.py", "check_risk_register"),
    # ── C-CONSUME-1 API Runtime Surface → M10 (POST /api/context/serve + retrieval + /api/runtime/sections) ──
    ("scripts/check_consumption_api.py", "check_consumption_api"),
    ("scripts/check_context_response_retrieval_api.py", "check_context_response_retrieval_api"),
    ("scripts/check_runtime_sections_api.py", "check_runtime_sections_api"),
    ("scripts/check_no_api_consumption_bypass.py", "check_no_api_consumption_bypass"),
    # ── MULTI-SOURCE: governed api/csv/json ingestion behind SourceAdapterPort (pdf/html honest non-consumable) ──
    ("scripts/check_multi_source_ingestion.py", "check_multi_source_ingestion"),
    # ── MULTI-SOURCE GENERIC: source_type-agnostic source→consumption + run-matrix regression + docs coverage ──
    ("scripts/check_source_to_consumption_generic.py", "check_source_to_consumption_generic"),
    ("scripts/check_multi_source_regression.py", "check_multi_source_regression"),
    ("scripts/check_documentation_coverage.py", "check_documentation_coverage"),
    # ── INGESTION SWARM b1: contracts + ports + connector catalog + markdown_folder/folder_batch adapters ──
    ("scripts/check_ingestion_contracts.py", "check_ingestion_contracts"),
    ("scripts/check_ingestion_ports.py", "check_ingestion_ports"),
    ("scripts/check_ingestion_connector_catalog.py", "check_ingestion_connector_catalog"),
    ("scripts/check_ingest_markdown_folder.py", "check_ingest_markdown_folder"),
    ("scripts/check_ingest_folder_batch.py", "check_ingest_folder_batch"),
    # ── PATTERN & STANDARDS FACTORY (workflow w893n66dc): mine repeated shapes → standards/templates → enforce ──
    ("scripts/check_pattern_registry.py", "check_pattern_registry"),
    ("scripts/check_pattern_miner.py", "check_pattern_miner"),
    ("scripts/check_standard_catalog.py", "check_standard_catalog"),
    ("scripts/check_template_catalog.py", "check_template_catalog"),
    ("scripts/check_template_generation.py", "check_template_generation"),
    ("scripts/check_new_code_uses_standards.py", "check_new_code_uses_standards"),
    ("scripts/check_routine_library.py", "check_routine_library"),
    ("scripts/check_configuration_standards.py", "check_configuration_standards"),
    ("scripts/check_pattern_waivers.py", "check_pattern_waivers"),
    ("scripts/check_standards_api.py", "check_standards_api"),
    ("scripts/check_standards_ui.py", "check_standards_ui"),
    ("scripts/check_standardized_examples.py", "check_standardized_examples"),
    ("scripts/check_pattern_standards_full_stack.py", "check_pattern_standards_full_stack"),
    ("scripts/check_standards_review_pack.py", "check_standards_review_pack"),
    # ── C-MEM-1: Supermemory candidate memory provider + /memory page (workflow w0bmivqey) ──
    ("scripts/check_memory_provider_contract.py", "check_memory_provider_contract"),
    ("scripts/check_local_memory_provider.py", "check_local_memory_provider"),
    ("scripts/check_supermemory_emulator.py", "check_supermemory_emulator"),
    ("scripts/check_memory_results_become_artifacts.py", "check_memory_results_become_artifacts"),
    ("scripts/check_memory_tenant_project_scoping.py", "check_memory_tenant_project_scoping"),
    ("scripts/check_memory_api.py", "check_memory_api"),
    ("scripts/check_response_redaction_single_source.py", "check_response_redaction_single_source"),
    ("scripts/check_memory_page_projection_only.py", "check_memory_page_projection_only"),
    ("scripts/check_no_direct_supermemory_imports.py", "check_no_direct_supermemory_imports"),
    ("scripts/check_supermemory_no_truth_bypass.py", "check_supermemory_no_truth_bypass"),
    ("scripts/check_memory_trace_written.py", "check_memory_trace_written"),
    # ── C-MEM-1 synth (late) + PIPELINE VISUALIZATION PAGE SERIES (workflow wsklcqf5s) ──
    ("scripts/check_supermemory_candidate_catalog.py", "check_supermemory_candidate_catalog"),
    ("scripts/check_memory_provider_full_stack.py", "check_memory_provider_full_stack"),
    ("scripts/check_pipeline_api.py", "check_pipeline_api"),
    ("scripts/check_pipeline_upload_ui.py", "check_pipeline_upload_ui"),
    ("scripts/check_pipeline_decomposition_ui.py", "check_pipeline_decomposition_ui"),
    ("scripts/check_pipeline_reconciliation_ui.py", "check_pipeline_reconciliation_ui"),
    ("scripts/check_pipeline_enhancement_ui.py", "check_pipeline_enhancement_ui"),
    ("scripts/check_pipeline_optimization_ui.py", "check_pipeline_optimization_ui"),
    ("scripts/check_pipeline_verification_ui.py", "check_pipeline_verification_ui"),
    ("scripts/check_pipeline_consumption_ui.py", "check_pipeline_consumption_ui"),
    ("scripts/check_pipeline_pages_full_stack.py", "check_pipeline_pages_full_stack"),
    # ── C-NATIVE-1: Native Format Preservation — same-shape-in/out + governed sidecars (workflow wfnzj849b) ──
    ("scripts/check_native_shape_contract.py", "check_native_shape_contract"),
    ("scripts/check_native_json_roundtrip.py", "check_native_json_roundtrip"),
    ("scripts/check_native_csv_roundtrip.py", "check_native_csv_roundtrip"),
    ("scripts/check_native_markdown_sidecar.py", "check_native_markdown_sidecar"),
    ("scripts/check_native_export_same_schema.py", "check_native_export_same_schema"),
    ("scripts/check_native_output_modes.py", "check_native_output_modes"),
    ("scripts/check_native_sidecar_lineage.py", "check_native_sidecar_lineage"),
    ("scripts/check_native_export_no_truth_bypass.py", "check_native_export_no_truth_bypass"),
    ("scripts/check_native_export_rehydration.py", "check_native_export_rehydration"),
    ("scripts/check_native_api.py", "check_native_api"),
    ("scripts/check_native_format_full_stack.py", "check_native_format_full_stack"),
    # ── OKF INTEROP: import/export Google's Open Knowledge Format at the EDGES (markdown+YAML, type-required, reserved index.md/log.md) WITHOUT surrendering the core — our governance (verified/source/freshness/receipt) rides in the frontmatter OKF doesn't mandate + a CDC log.md; round-trip lossless (governance + arbitrary keys survive); OKF is a candidate projection, our object stays the core; never serves truth ──
    ("scripts/check_okf_interop.py", "check_okf_interop"),
    # ── STANDARDS INTEROP MANIFEST (single source of truth): every adopted/declined standard (OKF/PROV/OpenLineage/WebAnnotation/JSON-Patch/JSON-LD/MCP; declined data-gravity moats) with direction+status+module+proof; every built/emitted claim import-verified + proof-gated; the public interop page is GENERATED from the manifest (no hand-typed conformance, fails on drift); never serves truth ──
    ("scripts/check_standards_interop_manifest.py", "check_standards_interop_manifest"),
    # ── OKF + FRESHNESS LIVE E2E (capstone, fully local): ingest OKF → bind the fragile fact to the local source emulator → serve fresh → source changes → stale held out → re-sync → export OKF provably current with the change in log.md; round-trip stays lossless; "OKF carries context, Baltor governs whether it's true+current"; never serves truth ──
    ("scripts/check_okf_freshness_live_e2e.py", "check_okf_freshness_live_e2e"),
    # ── FtM INTEROP: map governed entity records → FollowTheMoney EntityProxy at the edge (entity_type→schema, fields→real list-valued FtM props, id=lei-<LEI> else dc-<sha1>, topics promoted CONSERVATIVELY from governed flags only); FtM is a candidate projection, the governed record stays the core; imported from the DueCare entity-intelligence reference; never serves truth ──
    ("scripts/check_ftm_interop.py", "check_ftm_interop"),
    # ── SKILL.md INTEROP: import/export Anthropic Agent Skills SKILL.md at the edge (name+description required, markdown body), the skill format that won the cross-vendor war; our assurance (verified/measured-lift/source-authority/receipt) rides in the frontmatter SKILL.md doesn't mandate; round-trip lossless (governance + arbitrary keys survive); the governed skill stays the core; an imported skill is a candidate; never serves truth ──
    ("scripts/check_skill_md_interop.py", "check_skill_md_interop"),
    # ── ENTITY-INTELLIGENCE candidate feed (governed cross-project ingestion): stage the DueCare catalog (GLEIF/BODS/OFAC/DOJ/DOL/registries) as CANDIDATES with determinism_ceiling + license + fragility (real taxonomy modes); `adoptable` cross-checks the org-guardrail AVOID ledger (AVOID-* rows recorded NON-adoptable); discovery≠trust, nothing promoted, serves_truth=false ──
    ("scripts/ingest_entity_intelligence_catalog.py", "ingest_entity_intelligence_catalog"),
    # ── GITHUB SIGNAL intake (owner-shared repos, reviewed live): 10 targets staged as governed candidates w/ disposition (ADOPT/CONSIDER/WATCH/AVOID); copyleft/unstated/proprietary can NEVER be adoptable (org-guardrail cross-check); provenance corrections + unscrapeable links recorded honestly; discovery≠trust, serves_truth=false ──
    ("scripts/ingest_github_signal_intake.py", "ingest_github_signal_intake"),
    # ── CAPABILITY SEEDS (learn-from-them, clean-room): all 10 reviewed repos implemented as 11 governed seeds in src/teleon/seeds — drop-in only for clean licenses, technique-only for copyleft/unstated; each runs real logic + records the lesson + emits a PurposeTask candidate; court-deadline + inference-routing seeds deterministically CORRECT; never serves truth, nothing promoted ──
    ("scripts/check_capability_seeds.py", "check_capability_seeds"),
    # ── PROFESSION-SCALE SEEDER: generalize the DueCare template beyond migrant-worker protection — 15 professions / 11 sectors derive 55 DURABLE governed capability candidates (license-verification · exclusion-screening · compliance-currency + profession-specific) on the O*NET/WORKBank spine; DueCare is ONE instance; never serves truth, nothing promoted ──
    ("scripts/check_profession_capability_seeder.py", "check_profession_capability_seeder"),
    # ── REPO_REFERENCE manifest: external repos cloned for offline study are governed + reconstructable (slug+SHA) WITHOUT republishing — vendorable agrees with the license class (copyleft/unstated/private never vendorable), folder gitignored, every reviewed repo + the DueCare template covered, distilled seeds map to real artifacts ──
    ("scripts/check_repo_reference_manifest.py", "check_repo_reference_manifest"),
    # ── FUNDAMENTAL PRIMITIVES taxonomy: ONE canonical map of the system's primitives (data storage/transfer/computation/unit/medium · interop/context/skill standards · k8s/cloud-fn/execution/environment runtime · seven-primitive grammar · the assurance wedge), each mapped to a REAL artifact; all owner-requested families covered; assurance first-class; generated code/file map (no drift); non-destructive index ──
    ("scripts/check_fundamental_primitives_taxonomy.py", "check_fundamental_primitives_taxonomy"),
    # ── CODE GRAPH: deterministic ast-based dependency graph (file→file imports + crossing symbols) over src/scripts/local_emulators; upstream/downstream are exact inverses; impact = transitive blast radius; neighbors by file path → "edit 1 file, see what breaks"; stdlib-only, always available; never serves truth ──
    ("scripts/code_graph.py", "code_graph"),
    # ── MODEL INDEX (best+cheapest+effective, FRESHNESS-governed): unified index of model cost + live endpoint + download location + quality; selector picks the cheapest FRESH model within a quality floor; stale model facts are HELD OUT and never selected until re-verified (kept-up-to-date is the wedge); never serves truth ──
    ("scripts/check_model_index.py", "check_model_index"),
    # ── DESCENT METHOD CATALOG: for every improvement dimension (all 17 descent axes) the concrete METHODS to accomplish it (e.g. reduce skill tokens via compression / redundant-text dedupe), each grounded in a VARIETY of researched candidate modules; license class governs vendorability (copyleft/source-available/unstated/unverified = behind-a-port); generated how-to map; discovery≠trust, never serves truth ──
    ("scripts/check_descent_method_catalog.py", "check_descent_method_catalog"),
    # ── SELF-OPTIMIZING capability unit (the flagship): a capability MEASURES itself + auto-applies the best GOVERNED method per dimension (compress tokens / distill to a deterministic rule or cheaper model / bind a fragile fact to its source / route to the cheapest capable model), emitting a real before→after receipt; lossless + within-policy + accuracy-floored; HONEST when a task can't be made deterministic; deterministic + idempotent; never serves truth ──
    ("scripts/check_self_optimizing_unit.py", "check_self_optimizing_unit"),
    # ── PITCH DECK (slides/demo for technical + investors): generated from architecture/teleon_pitch_deck.json with EVERY number computed live (proof count, the actual self-optimizing receipt, method/profession/standards counts); consistent single-source language; no hand-typed metrics; carries the governance + honest-gap language; serves_truth=false ──
    ("scripts/build_pitch_deck.py", "build_pitch_deck"),
    # ── API-HUB intake + GOVERNED feed-intake (+ repo-batch seeds): the feed-intake REFUSES ToS-violating scraping / anti-bot evasion / bulk-PII-harvest and ingests only via legitimate paths (official API / owner-paste / RSS), logging inaccessible sources honestly; the API-hub intake catalogs governed endpoint candidates (RapidAPI/Nokia CAMARA) behind a port; discovery≠trust, never serves truth ──
    ("scripts/check_api_and_feed_seeds.py", "check_api_and_feed_seeds"),
    # ── OPENAPI DECONSTRUCTOR: deconstruct an API hub's endpoint SPECS (OpenAPI — how RapidAPI describes every endpoint) into governed capability-seed candidates (input/output contract + endpoint + auth + high determinism); a deconstructed endpoint distills to a deterministic capability via direct_api_rule; the live Playwright/owner-session harvest has a built local emulator (DEFER GATE); discovery≠trust, never serves truth ──
    ("scripts/check_openapi_deconstructor.py", "check_openapi_deconstructor"),
    # ── PLUGGABLE GIT BACKEND (the brain-blast: Teleon units abstract git primitives): one GitBackendPort backs a capability unit's storage/versioning/diffs on internal git OR the client's GitHub/GitLab/Gitea (same abstraction); governance rides in a SIDECAR (client code stays clean); a backend never serves truth; live external calls owner-gated with an offline mirror (DEFER GATE) ──
    ("scripts/check_git_backend_port.py", "check_git_backend_port"),
    # ── CAPABILITY IMPLEMENTATION REGISTRY: a capability is facilitated by a VARIETY of implementations (internal repos/libraries/API hubs/models/LLMs); each declares tools/models/API-keys (env-ref names) + cost + determinism; the selector picks the best COMBINATION by available keys + objective (a key unlocks an option); + the owner workspace inventory staged as candidate capabilities; discovery≠trust, never serves truth ──
    ("scripts/check_capability_implementation_registry.py", "check_capability_implementation_registry"),
    # ── DOCUMENT EXTRACTION CASCADE: PDF→schema as a cheapest-that-meets-requirements cascade over a method grid (metadata/OCR/text → regex/keyword/deterministic-NLP → prune/compress → cheapest-capable LLM → frontier); deterministic rules before LLM; compress-only-when-needed; unfillable fields reported MISSING honestly (never fabricated); full cost/path receipt; far cheaper than always-frontier; never serves truth ──
    ("scripts/check_document_extraction_cascade.py", "check_document_extraction_cascade"),
    # ── INTELLIGENCE SOURCE REGISTRY: a constant stream (top repos / AI news / papers / newsletters / search) from FREE LEGITIMATE sources only (RSS + official REST APIs, keyless or free-key env-refs, ToS-clean); keyless news-sweep plan covers every need; pull routes through governed-feed-intake (legitimate paths, refuses scraping); key-gated sources logged unfetchable honestly; never serves truth ──
    ("scripts/check_intelligence_source_registry.py", "check_intelligence_source_registry"),
    # ── TUNABLE TASK CATALOG (generalize the doc-extraction idea): 13 agentic tasks that each fit AUTOMATED SETUP TUNING — tiered method grid (deterministic floor → small model → frontier LLM), cheapest-first, escalate only as far as the requirement forces; the auto-tuner key-gates LLM tiers + lets deterministic-possible tasks finish with no LLM; never serves truth ──
    ("scripts/check_tunable_task_catalog.py", "check_tunable_task_catalog"),
    # ── CAPABILITY PR WORKFLOW (GitHub-familiar bridge): a capability unit is a familiar git repo — branches/PRs/checks/merge — where the eval-LIFT gate IS the CI check (a regressing or out-of-policy fork CANNOT merge); same workflow on internal git OR the client's GitHub/GitLab/Gitea (operation parity map); governance rides in the notes sidecar; familiar UI rendered; never serves truth ──
    ("scripts/check_capability_pr_workflow.py", "check_capability_pr_workflow"),
    # ── LOSSLESS DISTILLATION SUBSYSTEM (core; workflow w2bds1nzd) ──
    ("scripts/check_lossless_distillation_contracts.py", "check_lossless_distillation_contracts"),
    ("scripts/check_lossless_artifact_store.py", "check_lossless_artifact_store"),
    ("scripts/check_lineage_bundle_complete.py", "check_lineage_bundle_complete"),
    ("scripts/check_distillation_rehydration.py", "check_distillation_rehydration"),
    ("scripts/check_distillation_rollback.py", "check_distillation_rollback"),
    ("scripts/check_information_retention_report.py", "check_information_retention_report"),
    ("scripts/check_cfpb_lossless_distillation.py", "check_cfpb_lossless_distillation"),
    ("scripts/check_optimization_lossless_distillation.py", "check_optimization_lossless_distillation"),
    ("scripts/check_ingestion_decomposition_lossless.py", "check_ingestion_decomposition_lossless"),
    ("scripts/check_lossless_distillation_redteam.py", "check_lossless_distillation_redteam"),
    ("scripts/check_lossless_distillation_full_stack.py", "check_lossless_distillation_full_stack"),
    # ── DETERMINISM FACTORY: LLM→deterministic-rule distillation on verified data (workflow wyq9bet01) ──
    ("scripts/check_determinism_contracts.py", "check_determinism_contracts"),
    ("scripts/check_trace_store.py", "check_trace_store"),
    ("scripts/check_consensus_recorder.py", "check_consensus_recorder"),
    ("scripts/check_determinism_pattern_miner.py", "check_determinism_pattern_miner"),
    ("scripts/check_rule_candidate_generation.py", "check_rule_candidate_generation"),
    ("scripts/check_rule_replay_engine.py", "check_rule_replay_engine"),
    ("scripts/check_rule_shadow_mode.py", "check_rule_shadow_mode"),
    ("scripts/check_rule_promotion_gate.py", "check_rule_promotion_gate"),
    ("scripts/check_deterministic_rule_fallback.py", "check_deterministic_rule_fallback"),
    ("scripts/check_cfpb_reconciliation_rule_distillation.py", "check_cfpb_reconciliation_rule_distillation"),
    ("scripts/check_source_classification_rule_distillation.py", "check_source_classification_rule_distillation"),
    ("scripts/check_optimization_rejection_rule_distillation.py", "check_optimization_rejection_rule_distillation"),
    ("scripts/check_determinism_redteam.py", "check_determinism_redteam"),
    ("scripts/check_determinism_full_stack.py", "check_determinism_full_stack"),
    # ── CONTEXT SURFACE UIs: /determinism + /native + surfaces index (workflow w8291sv6k) ──
    ("scripts/check_determinism_api.py", "check_determinism_api"),
    ("scripts/check_determinism_ui.py", "check_determinism_ui"),
    ("scripts/check_native_ui.py", "check_native_ui"),
    ("scripts/check_context_surfaces_index.py", "check_context_surfaces_index"),
    # ── CONTEXTOPS Verification Foundry (core differentiator; build lanes — workflow w6powzr4c) ──
    ("scripts/check_contextops_contracts.py", "check_contextops_contracts"),
    ("scripts/check_contextops_triage.py", "check_contextops_triage"),
    ("scripts/check_contextops_research_agent_provider.py", "check_contextops_research_agent_provider"),
    ("scripts/check_contextops_source_discovery.py", "check_contextops_source_discovery"),
    ("scripts/check_contextops_source_recipe.py", "check_contextops_source_recipe"),
    ("scripts/check_contextops_verification_recipe.py", "check_contextops_verification_recipe"),
    ("scripts/check_contextops_extractor_snippets.py", "check_contextops_extractor_snippets"),
    ("scripts/check_contextops_sandbox_gate.py", "check_contextops_sandbox_gate"),
    ("scripts/check_contextops_reliability_scoring.py", "check_contextops_reliability_scoring"),
    ("scripts/check_contextops_cross_source_confirmation.py", "check_contextops_cross_source_confirmation"),
    # ── CONTEXTOPS synth lane: cost ladder + CFPB reference + redteam + full_stack (built inline) ──
    ("scripts/check_contextops_cost_reduction.py", "check_contextops_cost_reduction"),
    ("scripts/check_contextops_cfpb_reference.py", "check_contextops_cfpb_reference"),
    ("scripts/check_contextops_redteam.py", "check_contextops_redteam"),
    ("scripts/check_contextops_full_stack.py", "check_contextops_full_stack"),
    # ── WORKER TAXONOMY & BUCKETS (governance capstone; built inline) ──
    ("scripts/check_worker_bucket_registry.py", "check_worker_bucket_registry"),
    ("scripts/check_worker_router.py", "check_worker_router"),
    ("scripts/check_worker_taxonomy_full_stack.py", "check_worker_taxonomy_full_stack"),
    # ── C-GRAPH-1 TEMPORAL FACT GRAPH (local-first; Graphiti candidate/emulator; built inline) ──
    ("scripts/check_temporal_graph_contracts.py", "check_temporal_graph_contracts"),
    ("scripts/check_temporal_graph_local_store.py", "check_temporal_graph_local_store"),
    ("scripts/check_temporal_graph_cfpb_reference.py", "check_temporal_graph_cfpb_reference"),
    ("scripts/check_temporal_graph_provider_catalog.py", "check_temporal_graph_provider_catalog"),
    ("scripts/check_temporal_graph_watchtower_bridge.py", "check_temporal_graph_watchtower_bridge"),
    ("scripts/check_temporal_graph_reconciliation_bridge.py", "check_temporal_graph_reconciliation_bridge"),
    ("scripts/check_temporal_graph_consumption.py", "check_temporal_graph_consumption"),
    ("scripts/check_temporal_graph_api.py", "check_temporal_graph_api"),
    ("scripts/check_temporal_graph_ui.py", "check_temporal_graph_ui"),
    ("scripts/check_temporal_graph_redteam.py", "check_temporal_graph_redteam"),
    ("scripts/check_temporal_graph_full_stack.py", "check_temporal_graph_full_stack"),
    # ── C-RESEARCH-1 Context Provider Catalog (mem0/letta/graphiti/langfuse/phoenix/langsmith/openlineage/OWL candidates) ──
    ("scripts/check_context_provider_catalog.py", "check_context_provider_catalog"),
    # ── CAPABILITY-AWARE WORKER FLEET SUPERVISOR (DB ledger=truth; atomic claim; spawn/reuse/batch/drain) ──
    ("scripts/check_worker_fleet_schema.py", "check_worker_fleet_schema"),
    ("scripts/check_worker_atomic_claim.py", "check_worker_atomic_claim"),
    ("scripts/check_worker_fleet_supervisor.py", "check_worker_fleet_supervisor"),
    ("scripts/capability_worker.py", "capability_worker"),
    ("scripts/check_worker_status_progress_tracking.py", "check_worker_status_progress_tracking"),
    ("scripts/check_worker_provider_fallback.py", "check_worker_provider_fallback"),
    ("scripts/check_local_spawn_manager.py", "check_local_spawn_manager"),
    ("scripts/check_worker_fleet_redteam.py", "check_worker_fleet_redteam"),
    ("scripts/check_worker_fleet_supervisor_full_stack.py", "check_worker_fleet_supervisor_full_stack"),
    # ── C-OBS-1: observability/lineage provider seam + PROV/OpenLineage/WebAnnotation/JSONPatch standards ──
    ("scripts/check_observability_provider_seam.py", "check_observability_provider_seam"),
    ("scripts/check_lineage_standards_adapters.py", "check_lineage_standards_adapters"),
    ("scripts/check_observability_governance_redteam.py", "check_observability_governance_redteam"),
    # ── C-FLEET-2: worker lifecycle policies + ramp-up/down + telemetry + circuit breakers + recommender ──
    ("scripts/check_worker_lifecycle_policy_details.py", "check_worker_lifecycle_policy_details"),
    ("scripts/check_worker_spawn_decision_engine.py", "check_worker_spawn_decision_engine"),
    ("scripts/check_worker_batch_windows.py", "check_worker_batch_windows"),
    ("scripts/check_worker_cooldown_drain.py", "check_worker_cooldown_drain"),
    ("scripts/check_worker_provider_circuit_breaker.py", "check_worker_provider_circuit_breaker"),
    ("scripts/check_worker_telemetry_schema.py", "check_worker_telemetry_schema"),
    ("scripts/check_worker_failure_taxonomy.py", "check_worker_failure_taxonomy"),
    ("scripts/check_worker_policy_recommender.py", "check_worker_policy_recommender"),
    ("scripts/check_worker_k8s_keda_mapping_docs.py", "check_worker_k8s_keda_mapping_docs"),
    ("scripts/check_worker_lifecycle_redteam.py", "check_worker_lifecycle_redteam"),
    # ── C-FLEET-3: replicated control-plane supervisor scaling (leader/shard leases, idempotent decisions) ──
    ("scripts/check_flywheel_supervisor_leader_lease.py", "check_flywheel_supervisor_leader_lease"),
    ("scripts/check_flywheel_supervisor_failover.py", "check_flywheel_supervisor_failover"),
    ("scripts/check_flywheel_supervisor_shards.py", "check_flywheel_supervisor_shards"),
    ("scripts/check_flywheel_supervisor_idempotent_decisions.py", "check_flywheel_supervisor_idempotent_decisions"),
    ("scripts/check_flywheel_supervisor_no_duplicate_spawn.py", "check_flywheel_supervisor_no_duplicate_spawn"),
    ("scripts/check_flywheel_supervisor_lag_metrics.py", "check_flywheel_supervisor_lag_metrics"),
    ("scripts/check_flywheel_supervisor_keda_mapping.py", "check_flywheel_supervisor_keda_mapping"),
    ("scripts/check_control_plane_tick.py", "check_control_plane_tick"),  # composed C-FLEET-2+3 control-plane tick
    ("scripts/check_heartbeat_queue_contract.py", "check_heartbeat_queue_contract"),  # G3: offline queue/heartbeat contract parity
    # ── OPP-supervisor-scaling-live: durable leader/shard leases wired into baltor_flywheel.py --watch ──
    ("scripts/check_live_supervisor_schema.py", "check_live_supervisor_schema"),
    ("scripts/check_live_supervisor_leader_lease.py", "check_live_supervisor_leader_lease"),
    ("scripts/check_live_supervisor_shards.py", "check_live_supervisor_shards"),
    ("scripts/check_live_supervisor_idempotent_decisions.py", "check_live_supervisor_idempotent_decisions"),
    ("scripts/check_live_supervisor_persistence.py", "check_live_supervisor_persistence"),
    ("scripts/check_live_supervisor_spawn_decisions.py", "check_live_supervisor_spawn_decisions"),
    ("scripts/check_flywheel_watch_uses_supervisor_leases.py", "check_flywheel_watch_uses_supervisor_leases"),
    ("scripts/check_live_supervisor_two_process.py", "check_live_supervisor_two_process"),
    ("scripts/check_live_supervisor_redteam.py", "check_live_supervisor_redteam"),
    ("scripts/check_live_supervisor_api.py", "check_live_supervisor_api"),
    ("scripts/check_live_supervisor_ui.py", "check_live_supervisor_ui"),
    ("scripts/check_live_supervisor_full_stack.py", "check_live_supervisor_full_stack"),
    # ── G1: the full pipeline run AS fleet work (every stage = a claimed CapabilityTask) ──
    ("scripts/fleet_pipeline.py", "fleet_pipeline"),
    # ── durable FleetLedger (SQLite) on the live dispatch path — cross-process atomic claim ──
    ("scripts/check_durable_fleet_ledger.py", "check_durable_fleet_ledger"),
    # ── G4 live dispatch: --watch --dispatch spawns a real worker that drains the durable queue ──
    ("scripts/check_live_supervisor_dispatch.py", "check_live_supervisor_dispatch"),
    # ── G5: dependency-ordered durable claims + real parallel multi-worker drain across capabilities ──
    ("scripts/check_live_supervisor_parallel_dispatch.py", "check_live_supervisor_parallel_dispatch"),
    # ── C-MEM-2 Phase 0: the ESG demo self-test is bounded + cannot hang the flywheel ──
    ("scripts/check_demo_esg_pipeline_no_hang.py", "check_demo_esg_pipeline_no_hang"),
    # ── C-MEM-2 DELTA: builder memory + durable memory capability tasks (memory is NOT truth) ──
    ("scripts/check_cmem2_delta_inventory.py", "check_cmem2_delta_inventory"),
    ("scripts/check_builder_memory_capture.py", "check_builder_memory_capture"),
    ("scripts/check_memory_worker_commands.py", "check_memory_worker_commands"),
    ("scripts/check_memory_redteam.py", "check_memory_redteam"),
    # ── North Star durable runner contract: continuation survives Claude exiting (resumable from repo) ──
    ("scripts/check_north_star_runner_contract.py", "check_north_star_runner_contract"),
    # ── North Star MANDATORY: the full offline demo runs every core section + the CFPB correctness invariant ──
    ("scripts/check_offline_full_demo.py", "check_offline_full_demo"),
    # ── Execution backend flexibility: K8s + cloud functions + local interchangeable behind a port ──
    ("scripts/check_execution_backend_policy_matrix.py", "check_execution_backend_policy_matrix"),
    ("scripts/check_execution_backend_selector.py", "check_execution_backend_selector"),
    ("scripts/check_local_function_emulator.py", "check_local_function_emulator"),
    ("scripts/check_execution_backend_redteam.py", "check_execution_backend_redteam"),
    # ── cloud-defer-only-after-local-equivalent: local execution providers + the defer gate ──
    ("scripts/check_local_execution_providers.py", "check_local_execution_providers"),
    ("scripts/check_real_execution_candidates_have_emulators.py", "check_real_execution_candidates_have_emulators"),
    ("scripts/check_no_deferred_execution_surfaces.py", "check_no_deferred_execution_surfaces"),
    # ── the selector is WIRED into the live fleet-supervisor dispatch path (governed, local-first, no-block) ──
    ("scripts/check_live_fleet_execution_backend_wiring.py", "check_live_fleet_execution_backend_wiring"),
    # ── execution-backend decisions VISIBLE on /api/fleet/execution + the /fleet page (projection-only) ──
    ("scripts/check_fleet_execution_projection.py", "check_fleet_execution_projection"),
    # ── the flywheel injects repo-root PYTHONPATH into proof subprocesses (no false-RED from a bare launch) ──
    ("scripts/check_flywheel_subprocess_pythonpath.py", "check_flywheel_subprocess_pythonpath"),
    # ── adapter selection is NUMERIC + non-fragile (priority graph, not hard-coded role strings) ──
    ("scripts/check_preference_graph_numeric.py", "check_preference_graph_numeric"),
    # ── cloud execution is provider-AGNOSTIC (AWS Lambda is one peer, not canonical; config-sourced family) ──
    ("scripts/check_cloud_agnostic_execution.py", "check_cloud_agnostic_execution"),

    # ── C-CONSUME-2: durable context.consume command (run ConsumptionService as durable work) ──
    ("scripts/check_consumption_worker_command.py", "check_consumption_worker_command"),
    # ── C-CONSUME-3: /consume UI (projection over /api/context/serve + /api/runtime/sections) ──
    ("scripts/check_consumption_ui.py", "check_consumption_ui"),
    # ── SWARM: fragile_fact_watchtower minimum + object_store payload_ref (built via workflow w4lu4qz3k) ──
    ("scripts/check_watchtower_minimum_freshness.py", "check_watchtower_minimum_freshness"),
    ("scripts/check_object_store_payload_ref.py", "check_object_store_payload_ref"),
    # ── C33 Architecture Drift Guardrails & Project Spine (fitness functions: drift is failing, not vague) ──
    ("scripts/check_project_spine_folders.py", "check_project_spine_folders"),
    ("scripts/check_file_layout_policy.py", "check_file_layout_policy"),
    ("scripts/check_import_boundaries_manifest.py", "check_import_boundaries_manifest"),
    ("scripts/check_runtime_ownership_manifest.py", "check_runtime_ownership_manifest"),
    ("scripts/check_contract_registry_manifest.py", "check_contract_registry_manifest"),
    ("scripts/check_monolith_allowlist.py", "check_monolith_allowlist"),
    ("scripts/check_scripts_are_entrypoints.py", "check_scripts_are_entrypoints"),
    ("scripts/check_no_duplicate_runtime.py", "check_no_duplicate_runtime"),
    ("scripts/check_architecture_dashboard_projection_only.py", "check_architecture_dashboard_projection_only"),
    ("scripts/check_architecture_adr_coverage.py", "check_architecture_adr_coverage"),
    ("scripts/check_no_direct_provider_bypass.py", "check_no_direct_provider_bypass"),
    # ── C35 External Capability Catalog & Repo Replaceability (capability slots + health + replacement matrix) ──
    ("scripts/check_external_capability_catalog.py", "check_external_capability_catalog"),
    ("scripts/check_repo_health_policy.py", "check_repo_health_policy"),
    ("scripts/check_provider_replacement_matrix.py", "check_provider_replacement_matrix"),
    ("scripts/check_no_uncataloged_github_repos.py", "check_no_uncataloged_github_repos"),
    ("scripts/check_no_direct_external_imports.py", "check_no_direct_external_imports"),
    ("scripts/check_capability_contract_examples.py", "check_capability_contract_examples"),
    ("scripts/check_flagged_tools_not_reintroduced.py", "check_flagged_tools_not_reintroduced"),
    ("scripts/dev_status.py", "dev_status"),
    ("scripts/context_diff.py", "context_diff"),
    ("scripts/integrate_cfpb.py", "integrate_cfpb"),
    ("scripts/ingest/decompose_structured.py", "decompose_structured"),
    ("scripts/ingest/tenant_ingest.py", "tenant_ingest"),
    ("scripts/flywheel_worker.py", "flywheel_worker"),
    ("scripts/check_durable_worker_parallel.py", "check_durable_worker_parallel"),
    ("scripts/check_durable_queue_crash_recovery.py", "check_durable_queue_crash_recovery"),
    ("scripts/check_pipeline_runtime.py", "check_pipeline_runtime"),
    ("scripts/check_pipeline_parallel_runs.py", "check_pipeline_parallel_runs"),
    ("scripts/check_pipeline_per_step_queue.py", "check_pipeline_per_step_queue"),
    ("scripts/check_pipeline_tenant_isolation.py", "check_pipeline_tenant_isolation"),
    ("scripts/check_event_envelope.py", "check_event_envelope"),
    ("scripts/check_pipeline_unstructured.py", "check_pipeline_unstructured"),
    ("scripts/check_otel_spans.py", "check_otel_spans"),
    ("scripts/check_pipeline_lineage.py", "check_pipeline_lineage"),
    ("scripts/demo_cfpb_context_pack.py", "demo_cfpb_context_pack"),
    ("scripts/durable_store.py", "durable_store"),
    ("scripts/check_durable_restart_survival.py", "check_durable_restart_survival"),
    ("scripts/check_durable_http_enqueue_drain.py", "check_durable_http_enqueue_drain"),
    # ── Parallel-Path experiment engine — Stage 1 contracts (baseline + candidate paths, compare, promote-only-via-decision) ──
    ("scripts/check_parallel_path_contracts.py", "check_parallel_path_contracts"),
    # ── Parallel-Path experiment engine — Stage 2 runtime BEHAVIOR (same input snapshot, candidate never served, deterministic) ──
    ("scripts/check_parallel_path_implementation.py", "check_parallel_path_implementation"),
    # ── Parallel-Path experiment engine — Stage 3 EXAMPLE C: reconciliation/CFPB promotion GATE blocks unsafe candidate, keeps baseline as rollback ──
    ("scripts/check_parallel_path_promotion_gate.py", "check_parallel_path_promotion_gate"),
    # ── Parallel-Path experiment engine — Stage 3 EXAMPLES: execution-backend drain (A) + reconciliation/CFPB safety (C) drive the engine on real anchors ──
    ("scripts/check_parallel_path_examples.py", "check_parallel_path_examples"),
    # ── Parallel-Path experiment engine — Stage 4 REDTEAM: every attack fails safely (no early serve / promote-without-decision / dropped handle / held-out leak / different-input compare / cheap-non-equivalent / baseline rollback survives) ──
    ("scripts/check_parallel_path_redteam.py", "check_parallel_path_redteam"),
    # ── Parallel-Path experiment engine — Stage 4 FULL STACK: runs/asserts contracts+implementation+promotion_gate+examples+redteam and prints the CAPABILITY|STATUS|PROOF|NOTES table ──
    ("scripts/check_parallel_path_full_stack.py", "check_parallel_path_full_stack"),
    # ── PurposeTask PoC: provisioned BY CAPABILITY (numeric, not code) + governed self-adaptation on the Parallel-Path Engine (drift→side-by-side→promote-if-wins, keep original, never serve candidate early, reject unsafe) ──
    ("scripts/check_purpose_task_poc.py", "check_purpose_task_poc"),
    # ── PurposeTask: PurposeTaskSpec.v1 contract (declared by intent; the provisioned PoC spec is contract-bound) ──
    ("scripts/check_purpose_task_contracts.py", "check_purpose_task_contracts"),
    # ── OCTS CTS-0: PurposeTaskSpec.v1 is a conformant Open Capability Task; runtime-class vocabulary well-formed + cloud-defer-safe ──
    ("scripts/check_octs_conformance.py", "check_octs_conformance"),
    # ── PurposeTask dashboard: ONE truth model → staff (full) + customer (allowlist-redacted) views; no staff-only/secret/cross-tenant leak ──
    ("scripts/check_purpose_task_projection_redaction.py", "check_purpose_task_projection_redaction"),
    # ── Adaptation ladder L0-L5: MEANS auto-promote on gates; ENDS/forbidden/unknown never auto (core invariant, deny-by-default) ──
    ("scripts/check_adaptation_ladder.py", "check_adaptation_ladder"),
    # ── pre-seed Teleon with capability-DEFINED units across the full execution-style spectrum (template → deterministic → det+tool → skill → tool → skill+tool → model → open-ended), each a PurposeTaskSpec.v1 classified by the real escalation ladder + provisioned by capability, with a non-det → det descent for cost ──
    ("scripts/teleon_preseed_capabilities.py", "teleon_preseed_capabilities"),
    # ── capability OBJECTIVE flexibility: measure each impl (cost/latency/llm/determinism/accuracy), prioritize via a CapabilityObjective (preset or weights), select with a deterministic + traceable SelectionTrace; safety beats the objective; the objective DRIVES the descent (cost/llm/determinism -> distilled rule, accuracy -> model) ──
    ("scripts/check_teleon_capability_objectives.py", "check_teleon_capability_objectives"),
    # ── OBSERVED measurement / telemetry: a RunLedger turns real run outcomes into a MetricVector per impl (cost/latency/llm means, accuracy=pass-rate, determinism=output-stability); observed evidence feeds select() and blend() removes the cold-start cliff so a unit improves on what it ACTUALLY did, not a declared claim ──
    ("scripts/check_teleon_run_telemetry.py", "check_teleon_run_telemetry"),
    # ── the objective applied to the REAL seeded units: each unit's allowed runtime classes are scored by a CapabilityObjective on REAL pricebook cost + the REAL SLA latency budget, so minimize_latency picks the tightest-SLA placement and minimize_cost the cheapest — the same units flip placement under different priorities (flexibility made real on the units, never synthetic) ──
    ("scripts/check_teleon_unit_placement.py", "check_teleon_unit_placement"),
    # ── the objective GOVERNS self-improvement: a CapabilityObjective decides whether a unit's non-det -> det descent fires on the real adapt() engine (cost/determinism/llm -> promote the distilled rule, model kept as rollback) or is VETOED (maximize_accuracy holds the descent back when the rule diverges on novel/held-out inputs — the lossless-distillation law, made a tunable priority) ──
    ("scripts/check_teleon_objective_gated_descent.py", "check_teleon_objective_gated_descent"),
    # ── per-tenant objective binding: each tenant resolves (from the shared registry) to the CapabilityObjective matching its priority (preset or explicit weights); unbound -> documented default; malformed -> fails loud; and the tenant's objective FLOWS into placement + the journey so the SAME capability plans differently per tenant ──
    ("scripts/check_teleon_tenant_objective_binding.py", "check_teleon_tenant_objective_binding"),
    # ── the capability EVOLUTION graph (proactive, distinct from reactive self_healing): a capability evolves non-det -> most-det through DOCUMENTED forks (coverage traded for determinism, parent preserved, residual routed to a richer runner — never dropped); lineage/descent_path/most_deterministic_runner; lossless violations fail loud; self-healing writes heal edges into the SAME shared lineage (one capability, one history, two authors) ──
    ("scripts/check_teleon_capability_evolution_graph.py", "check_teleon_capability_evolution_graph"),
    # ── capability seeder: discovered candidates (from public skills/tools/MCP/plugin sources) normalize into governed CapabilityCandidate.v1, pass a cheap gap/lift SCREEN (rejects retained, not dropped), and each is WALKED non-det -> most-det on the evolution-graph engine (a documented deterministic fork covering the estimated fraction, residual routed to the preserved model); discovery != trust — nothing auto-active, nothing serves truth ──
    ("scripts/capability_seeder.py", "capability_seeder"),
    # ── the SIDE RUNNER: a resumable runner that discovers capability candidates (feed-file source; live search/scrape a governed off-by-default seam), seeds + screens them, walks each non-det -> most-det on the evolution-graph engine, stages to JSONL, and remembers processed hashes so re-runs are idempotent; owner-launched loop stops only via .agent/STOP_REQUESTED ──
    ("scripts/context_workers/capability_discovery_runner.py", "capability_discovery_runner"),
    # ── interchangeable PROVIDER ENDPOINTS per capability (WHOIS via RDAP/paid-API/library, geocoding via Census/Google/Mapbox): the objective layer picks the best endpoint per priority (minimize_cost->free, minimize_latency->fastest, maximize_accuracy->most reliable); a policy-forbidden endpoint is excluded before scoring (safety beats objective); observed telemetry deprioritizes a slow endpoint; deterministic, never truth ──
    ("scripts/check_teleon_endpoint_registry.py", "check_teleon_endpoint_registry"),
    # ── ORG guardrail policy: an org's devops/security rules (license/domain/runtime/package allow+deny lists + methodology rules like deterministic_only/no_llm) BOUND a capability — disallowed endpoints excluded before objective selection (safety beats objective; all-banned fails loud), and the AI may self-heal/fork a unit ONLY to a runner within the confines (a model fix is vetoed under a deterministic-only org) ──
    ("scripts/check_teleon_org_guardrail_policy.py", "check_teleon_org_guardrail_policy"),
    # ── OpenAI Codex as a first-class governed inference LANE (openai_compatible node, external + secret + local Ollama fallback; offline -> provider_unavailable, never fabricated): the objective routes among lanes (minimize_cost -> free local, capability priority -> Codex) and the org policy bounds it (air-gapped forbids cloud -> falls back to local Ollama; no-LLM forbids every lane -> escalate) ──
    ("scripts/check_teleon_codex_lane.py", "check_teleon_codex_lane"),
    # ── the DISTILLER + META-LEARNER (the moat): the distiller turns a capability into a deterministic FORK (ceiling-1.0 -> a fully-deterministic ~zero-cost rule, equivalence-verified, lossless, within the org's confines); the meta-learner learns from the records the cheapest-effective distillation STRATEGY per class (overriding the prior with evidence) + the cheapest sufficient LANE, so distilling gets cheaper as it runs ──
    ("scripts/check_teleon_distillation.py", "check_teleon_distillation"),
    # ── the scheduled DISTILLATION RUNNER: a resumable, free+offline (cron-safe) pass that distills the corpus's pure-deterministic capabilities into deterministic forks (193 ceiling-1.0 in one pass), idempotent, lowering the ceiling threshold distills more, meta-learner accumulates across runs; loop stops via .agent/STOP_REQUESTED ──
    ("scripts/context_workers/distillation_runner.py", "distillation_runner"),
    # ── the TRAINING system: the skills DB joins capability features + distillation outcomes into a labeled, splittable, exportable dataset; a FittedPolicy is trained from it that learns the highest-efficiency distillation strategy per class, generalizes (class->band->prior backoff), and beats the cold-start prior on held-out; a real model/LoRA plugs in behind the same port (candidate, never truth) + the harness emits its governed spec ──
    ("scripts/check_teleon_distillation_training.py", "check_teleon_distillation_training"),
    # ── the BULK REGISTRY INGESTER (the hundreds-of-thousands path): maps machine-readable registry dumps (MCP/Airbyte/npm-PyPI/OpenAPI/generic) to governed CapabilityCandidate rows WITHOUT an LLM — per-format adapters + deterministic category/kind priors; scales 1k entries -> 1k rows in one free pass; every row passes the seeder screen + is flagged for Stage-2 confirm; writes a runner-ingestible feed ──
    ("scripts/check_teleon_bulk_registry_ingest.py", "check_teleon_bulk_registry_ingest"),
    # ── the cross-capability NETWORK graph + metadata enrichment: detects alternative_of endpoint sets (same need, different provider), captures composability via category adjacency, and exposes a per-capability profile + network features that EXTEND the skills-DB feature vector — so distillation is learned from STRUCTURE, not just per-item features (complements each capability's per-capability evolution/distillation lineage) ──
    ("scripts/check_teleon_capability_network.py", "check_teleon_capability_network"),
    # ── the deterministic-IMPLEMENTATION FINDER: on capability entry, search the corpus (cross-category, by intent) for a MORE-deterministic / cheaper implementation (an LLM date-parser finds a deterministic library -> replace the model); already-deterministic caps need none; unmatched ones route to external search (a governed seam off by default behind ExternalImplSearchPort). Proposes, never disposes; never truth ──
    ("scripts/check_teleon_impl_finder.py", "check_teleon_impl_finder"),
    # ── DESCENT AXES (canonical: determinism/cost/latency-speed/llm_usage/freshness) + the FRESHNESS (anti-fragility) axis (bind a fragile changing-fact capability to an authoritative source on a volatility-matched sync cadence + CDC re-heal -> always-current deterministic lookup, stale held out) + the cost/speed MEASUREMENT harness (per-call cost saved + per-axis improvement + OBSERVED cost/latency from real runs) ──
    ("scripts/check_teleon_descent_axes.py", "check_teleon_descent_axes"),
    # ── descent is an extensible MENU: 15 canonical axes (efficiency + trust/robustness/openness — verifiability/reliability/locality/specialization/privacy/reproducibility/portability/resilience/energy/safety) with a config-driven strategy registry + a GENERIC descender that builds a valid, lossless, policy-checked, never-truth fork for ANY registered axis; adding an axis is a registry entry, not new code; measured per axis ──
    ("scripts/check_teleon_descent_strategies.py", "check_teleon_descent_strategies"),
    # ── TOKEN consumption (in/out) as tracked axes + SKILL-level token reduction: tokens_in/tokens_out are canonical lower-is-better axes the RunLedger tracks per run; compress_skill token-reduces even a single skill prompt LOSSLESSLY (duplicates/optional boilerplate pruned, answer-critical content + raw preserved); prompt_compression is a registered tokens_in descent strategy ──
    ("scripts/check_teleon_token_reduction.py", "check_teleon_token_reduction"),
    # ── RuleArena (ACL-2025) benchmark: on rule-guided reasoning (airline baggage/tax brackets/overtime/NBA trade/late fees) a distilled DETERMINISTIC rule fork is 100% accurate while a bare model mis-applies rules — the measured accuracy LIFT (the moat, measured, not asserted; the seed of the A/B strategy harness) ──
    ("scripts/eval/rulearena_benchmark.py", "rulearena_benchmark"),
    # ── the A/B STRATEGY HARNESS (the core advantage, MEASURED): scores every descent strategy and picks the cheapest that stays within an accuracy tolerance of the full-model baseline — deterministic wins on rule-guided work, a cheaper model on open-ended work, and a cheap-but-WRONG fork the ceiling-only prior would have shipped is CAUGHT (regression prevented); winners feed the meta-learner so the most-efficient path is learned from measured evidence ──
    ("scripts/check_teleon_ab_harness.py", "check_teleon_ab_harness"),
    # ── ECOSYSTEM COHESION e2e: a REAL discovered capability flows through the whole stack — screen -> network/impl-finder -> A/B descent (org-policy-bounded, clears the accuracy floor) -> meta-learner + cost measurement -> tenant-objective binding — each stage consuming the last, governed throughout (serves_truth=False); the tools/verticals/resource-registries compose, not a pile of modules ──
    ("scripts/check_teleon_assurance_pipeline_e2e.py", "check_teleon_assurance_pipeline_e2e"),
    # ── tunable TENANT PREFERENCES + hard blockers: a tenant tunes soft objective/axis-priorities/accuracy-tolerance + sets HARD blockers (MIT-only license, vetted-only, no external egress); compiles to an OrgGuardrailPolicy (hard blocks) + a CapabilityObjective (soft ranks) + the A/B tolerance; hard blocks, soft ranks, suggestions advise ──
    ("scripts/check_teleon_tenant_preferences.py", "check_teleon_tenant_preferences"),
    # ── per-VERTICAL eval suites feeding the A/B harness: each regulated-fact vertical maps to a rule-guided eval suite; eval_suite_scorer gives the A/B a REAL per-vertical accuracy (deterministic fork 100% vs model mis-applies) so the A/B picks the right strategy per vertical on measured evidence ──
    ("scripts/eval/vertical_eval_suites.py", "vertical_eval_suites"),
    # ── FRESHNESS axis end-to-end on a regulated fact (Reg E / eCFR): bind to the authoritative source on a volatility-matched cadence; serve the current value with provenance; on a rule change HOLD THE STALE ANSWER OUT (never served) until re-synced — the wedge provers concede + gateways disclaim ──
    ("scripts/check_teleon_freshness_e2e.py", "check_teleon_freshness_e2e"),
    # ── runnable DEMO: the real assurance engine on sample seed skills under a tenant's preferences — token-aware A/B descent (deterministic/cheaper-model/compressed-prompt within accuracy confines), freshness for fragile facts (stale held out), cost+token measurement, governed; diverse outcomes; no mocks ──
    ("scripts/demo_assurance_descent.py", "demo_assurance_descent"),
    # ── HONEST go-live readiness gate: verifies the built engine by RUNNING it (A/B/preferences/freshness/500+ proofs/corpus/deploy-config) + enumerates the live-wiring seams (live LLM, live source+CDC, real distillation, Postgres+promotion, auth/tenancy, hosting deploy) with owning sprints; go_live_ready=False until they are wired ──
    ("scripts/check_teleon_go_live_readiness.py", "check_teleon_go_live_readiness"),
    # ── LOCAL emulation: every BLOCKING go-live seam maps to a built local emulator (deterministic OpenAI-compatible model + authoritative-source/CDC server, both stdlib-only; Postgres/identity/runtime as real local containers); freshness seam (serve fresh→source changes→stale held out→re-synced) + model seam (deterministic+token counts) wire e2e in-process; runs via the compose overlay + Tiltfile; local_go_live_ready=True while cloud stays honestly False ──
    ("scripts/check_teleon_local_emulation.py", "check_teleon_local_emulation"),
    # ── CTS-1: bind an OCTS runtime CLASS → concrete backend by policy/creds/health; cloud deferred after a built local equivalent; class-scoped guard; deny-by-default; composes with the execution selector ──
    ("scripts/check_runtime_class_binding.py", "check_runtime_class_binding"),
    ("scripts/check_execution_dispatch_fail_loud.py", "check_execution_dispatch_fail_loud"),
    # ── Portfolio dependency LAW: HoldCo owns Teleon (runtime SaaS) + Baltor (applied, tenant of Teleon) + OpenHarnessHub (open ecosystem); Baltor→Teleon→OHH only, never reverse; Teleon never imports Baltor; migration debt tracked ──
    ("scripts/check_portfolio_dependency_law.py", "check_portfolio_dependency_law"),
    # ── Company boundary model: HoldCo ContextIsEverything owns no runtime/customer-data; data-separation (Baltor truth owned by Baltor alone, forbidden elsewhere); surfaces+integrations agree with the import law; no shared prod DB/god token; brand risk registered ──
    ("scripts/check_company_portfolio_boundaries.py", "check_company_portfolio_boundaries"),
    # ── Teleon Lift: import existing cloud functions + K8s → ImportedWorkload → PurposeTaskDraft (always human-gated) + legacy=rollback-baseline + read-only-first 6-mode adoption ladder w/ managed gate; secrets stripped; CTS-1-bindable; offline seams; deterministic ──
    ("scripts/check_teleon_lift.py", "check_teleon_lift"),
    # ── Portfolio websites (ContextIsEverything · Teleon · Baltor · OpenHarnessHub): rubric-gated static sites built from one source; brand boundaries + quality>=90 + security + customer readiness + reuse + distinct + technical-launch + trycloudflare discipline + honest screenshots + full-stack table ──
    ("scripts/build_portfolio_sites.py", "build_portfolio_sites"),
    ("scripts/check_portfolio_website_discovery.py", "check_portfolio_website_discovery"),
    ("scripts/check_portfolio_reuse_no_reinvention.py", "check_portfolio_reuse_no_reinvention"),
    ("scripts/check_portfolio_sites_static.py", "check_portfolio_sites_static"),
    # ── No dead in-page anchors: every href="#x" on every portfolio site resolves to an id="x" (incl. both CTAs) — caught + fixed the portfolio-wide dead-flagship-CTA bug (section ids = heading first-word never matched hand-set #registry/#capabilitytask/#cfpb-demo anchors) ──
    ("scripts/check_portfolio_no_dead_anchors.py", "check_portfolio_no_dead_anchors"),
    ("scripts/check_portfolio_site_quality_rubric.py", "check_portfolio_site_quality_rubric"),
    ("scripts/check_portfolio_websites_are_distinct.py", "check_portfolio_websites_are_distinct"),
    ("scripts/check_portfolio_brand_boundaries.py", "check_portfolio_brand_boundaries"),
    ("scripts/check_portfolio_technical_launch_rubric.py", "check_portfolio_technical_launch_rubric"),
    ("scripts/check_portfolio_trycloudflare_rubric.py", "check_portfolio_trycloudflare_rubric"),
    ("scripts/check_portfolio_security_privacy_rubric.py", "check_portfolio_security_privacy_rubric"),
    ("scripts/check_portfolio_customer_readiness_rubric.py", "check_portfolio_customer_readiness_rubric"),
    ("scripts/check_portfolio_site_screenshots.py", "check_portfolio_site_screenshots"),
    ("scripts/check_portfolio_launch_full_stack.py", "check_portfolio_launch_full_stack"),
    # ── Open-hubs split: public artifact hubs each own one artifact kind; cross-hub bridge graph; NONE is a truth authority (Baltor governs, Teleon runs) ──
    ("scripts/check_open_hubs_bridge_graph.py", "check_open_hubs_bridge_graph"),
    # ── Shared Inference Gateway + OIPS: object-level LLM preferences resolve via inheritance; numeric provider graph selects preferred-or-governed-fallback; ModelInvocationReceipt records the ACTUAL model + fallback trail; secrets are refs only; LLM output never truth/auto-served ──
    ("scripts/check_inference_gateway.py", "check_inference_gateway"),
    # ── Shared Template Registry: canonical 14-section object shell + 15 mixins compose every object family; numeric codes; TemplateArtifact/SchemaObjectTemplate contracts; safe instantiator renders CANDIDATE (never active/truth) shapes; internal-only (OpenTemplatesHub.io is future) ──
    ("scripts/check_shared_template_registry.py", "check_shared_template_registry"),
    # ── Demo Control Tower: aggregates registered demo/runtime surfaces (portfolio_lib static sites + hub + Baltor CFPB + dashboards + registries) into ONE start-here page + dist/demo-all-urls.*; honest active/candidate/internal status; no fake URLs; CFPB e2e invariant cited; ports single-sourced ──
    ("scripts/check_demo_control_tower.py", "check_demo_control_tower"),
    ("scripts/track_user_journey.py", "track_user_journey"),
    ("scripts/check_user_journey_tracker.py", "check_user_journey_tracker"),
    # ── GitHub Signal Flywheel / Repo Intelligence: top repos → GOVERNED candidates (discovery!=trust, stars!=proof, trend!=fit!=activation); weekly growth from STORED snapshots; classify→hub; never auto-active; bad-license→quarantine ──
    ("scripts/check_github_signal_flywheel.py", "check_github_signal_flywheel"),
    # ── Cloudflare URL handoff: aggregate+verify every TryCloudflare+local URL → shareable MD + one-by-one review checklist + review state + rubric scorecard; no fake URLs; honest candidate/missing + screenshot-unavailable ──
    ("scripts/check_cloudflare_url_handoff.py", "check_cloudflare_url_handoff"),
    # ── Shared Sandbox Gateway: candidates run in a governed local sandbox before promotion (deny-by-default: no network/secrets/host-escape); CubeSandbox/E2B/Daytona/Docker/K8s candidate-only behind the port; sandbox output is NEVER truth ──
    ("scripts/check_sandbox_gateway.py", "check_sandbox_gateway"),
    # ── Skill Digestion Lab: parse skill (parse-only) → extract deterministic substeps → cheaper runtime CANDIDATE (never active) keeping original as fallback; unsafe→quarantine; promotion needs sandbox+eval+redteam; composes the Sandbox Gateway ──
    ("scripts/check_skill_digestion.py", "check_skill_digestion"),
    # ── Digestion → open-hub candidate outputs: a digested skill emits an OpenSkillsHub SkillArtifact candidate (canonical shell) + a Teleon runtime candidate (never active; original kept as fallback); unsafe→no candidate; composes Template Registry + digester ──
    ("scripts/check_digestion_open_hub_outputs.py", "check_digestion_open_hub_outputs"),
    # ── Model-compatibility runner: which models a digested skill works with (local stub=draft_only, credentialed external=production_after_gate, uncredentialed=eval_only) and which it does NOT (specialization mismatch=not_compatible); via the Inference Gateway; output not truth ──
    ("scripts/check_model_compatibility.py", "check_model_compatibility"),
    # ── Free/Limited LLM Endpoint Intelligence: classify endpoints+repos by governance class (ClawLess=browser runtime not endpoint; official=candidate; discovery=metadata; gateway=lab; shared-key/bypass/reverse=quarantine; Together=paid); risk-score + phase-cap; provider-node PROPOSALS only; via the Inference Gateway; output never truth ──
    ("scripts/check_free_limited_endpoint_intel.py", "check_free_limited_endpoint_intel"),
    # ── Shared I/O + Resource Spine: ONE named map ratifying existing typed-I/O contracts (ObjectShell + Command/Event/Error envelopes, no duplicates) + the new resource layer (ResourceRef/Binding/DataResourceSpec/SecretRef/KeyRef/ProvisionReceipt) with guards: no raw secrets/tables, TTL on temp, owner+retention on persistent, local-equivalent for cloud ──
    ("scripts/check_shared_io_resource_spine.py", "check_shared_io_resource_spine"),
    # ── Command/work I/O: the durable FleetLedger's records conform to the typed work-I/O contracts (WorkItem=CapabilityTask.v1, idempotent enqueue, atomic WorkerClaim, AckNackReceipt, DeadLetterEntry); projectors in src/teleon/io are pure ──
    ("scripts/check_shared_command_work_io.py", "check_shared_command_work_io"),
    # ── Event I/O: internal EventBus events project to CloudEvents 1.0 (EventEnvelope.v1 / CloudEventProjection.v1) — type in EVENT_KINDS, correlation_id required, deterministic (source,type,seq) id, secrets redacted; pure projector in src/teleon/io ──
    ("scripts/check_shared_event_io.py", "check_shared_event_io"),
    # ── Teleon EGRESS GRAPH: outbound worker fetch/search/tool calls become redacted append-only observations projected into a tenant/query-scoped graph (query->egress->destination plus worker/tool/response digest); searchable by query/worker/destination; output is evidence only, never truth. ──
    ("scripts/check_teleon_egress_graph.py", "check_teleon_egress_graph"),
    # ── Teleon EGRESS ENFORCEMENT: covered workers + live inference route outbound HTTP through EgressClient; raw HTTP isolated to approved transports; route decisions/attempts ledgered; blocked routes don't fall through; evidence remains truth-free. ──
    ("scripts/check_teleon_egress_enforcement.py", "check_teleon_egress_enforcement"),
    # ── Teleon EXECUTION ENVIRONMENT TAXONOMY: every runtime class has pre-autotune defaults, policy preferences, route preferences, resource/lifecycle/SLA refs, local equivalent, and no-truth/autotune boundary locks. ──
    ("scripts/check_teleon_execution_environment_taxonomy.py", "check_teleon_execution_environment_taxonomy"),
    # ── Baltor main UI: the animated Context Engine hero + its canonical six-stage language wired into the SPA (overview + /engine), single-sourced from web/baltor/stages.json; canvas/raf; reduced-motion; offline; no Oracle copy ──
    ("scripts/check_baltor_engine_hero_ui.py", "check_baltor_engine_hero_ui"),
    # ── Baltor SPA implements the canonical Claude-Design branded-house system (dir-d teal scope, Hanken Grotesk + IBM Plex Mono, shared card primitive + scale) while preserving our own additions; design spec persisted in-repo ──
    ("scripts/check_baltor_design_system.py", "check_baltor_design_system"),
    # ── OpenBenchmarkHub is real: contracts + the first first-party benchmark (Baltor CFPB Context Governance, anchored to real demo facts) + CI-derived benchmark opportunities (candidates); a benchmark result is evidence-not-authority (no benchmark gate in the promotion path) ──
    ("scripts/check_openbenchmarkhub_core.py", "check_openbenchmarkhub_core"),
    # ── Competitive provider mappings: infra/agent companies map to ports as governed candidates (Fireworks = real inference-gateway candidate w/ secret + governed fallback; Crusoe/Nscale execution backends need local-equivalent; Cursor/Cognition sandboxed, output not truth); none active or a direct import ──
    ("scripts/check_competitive_provider_mappings.py", "check_competitive_provider_mappings"),
    # ── Inference Gateway REDTEAM: the shared LLM plane fails safely — fallback recorded (never silent), receipt never 'served'/output never truth, offline local-stub provenance + no raw-key leak, ClawLess!=endpoint, shared-key quarantine, free!=customer-sensitive, secret-refs only, numeric routing ──
    ("scripts/check_inference_gateway_redteam.py", "check_inference_gateway_redteam"),
    # ── Inference Gateway routes on NUMERIC codes + node-ids, not brittle display strings (rename-safe; capability-code change drives eligibility; no display branching in select_provider/_eligible) ──
    ("scripts/check_no_brittle_model_string_logic.py", "check_no_brittle_model_string_logic"),
    # ── Object preference coverage: key object families declare a model preference BY REFERENCE (ObjectShell.model_preference_ref -> InferencePreference.v1), never inline; the ref resolves through the gateway ──
    ("scripts/check_objects_have_inference_preferences.py", "check_objects_have_inference_preferences"),
    # ── /api/inference PROJECTION (api_projection): projection-only read views of the LLM plane (providers/model-graph/free-endpoints/preferences/health/receipts + local resolve); numeric codes, has_secret_ref bool only, NO raw key/secret value, offline-honest health, ErrorEnvelope.v1; every declared route binds to a real callable ──
    ("scripts/check_inference_api.py", "check_inference_api"),
    # ── Generated OpenAPI + AsyncAPI specs (docs/contracts/*.generated.json via scripts/build_contract_specs.py): drift-free machine projection of contract_registry — every registered route covered (incl. /api/inference), every command/event/log channel covered, every $ref resolves, no raw keys, every op projection-only + ErrorEnvelope.v1 ──
    ("scripts/check_shared_openapi_asyncapi_specs.py", "check_shared_openapi_asyncapi_specs"),
    # ── Shared LLM Plane SERVED end-to-end: scripts/api_inference_handler answers every /api/inference route (errors=ErrorEnvelope.v1); structured-local output is a CANDIDATE never truth (ModelInvocationReceipt); admin server delegates GET+POST; read-only UI (web/baltor/inference-plane.html) consumes it; no secret-value leak in any response ──
    ("scripts/check_inference_api_handler.py", "check_inference_api_handler"),
    # ── Shared LLM Plane fires INSIDE the connected pipeline: run_full_pipeline emits governed inference.requested → inference.completed (receipt-backed, is_truth=false, Enhancement stage) visible on /dashboard; the DETERMINISTIC answer stays the served truth (LLM candidate never promoted); no secret leak ──
    ("scripts/check_inference_in_pipeline.py", "check_inference_in_pipeline"),
    # ── ADVERSARIAL: every attack on the pipeline inference wiring fails safely — no SDK/raw-key in the governed path, fallback recorded (never silent), output never promoted to truth, run_full_pipeline runs with ZERO network (socket blocked), model output never reaches a served surface, ungoverned event kinds rejected, governance gates still run ──
    ("scripts/check_inference_pipeline_redteam.py", "check_inference_pipeline_redteam"),
    # ── Shared LLM Plane UI projection: web/baltor/inference-plane.html is reachable (/inference-plane, no dead link), consumes /api/inference/*, declares output candidate-not-truth, labels providers local/external w/ key-as-ref (no value), no secret leak; the Live Ops dashboard links it + renders inference.* events as candidate-not-truth (no dashboard truth) ──
    ("scripts/check_inference_ui.py", "check_inference_ui"),
    # ── Baltor Guided Demos index (Claude Design handoff → web/baltor/guided-demos.html, served /guided-demos): branded-house oh-* design; 14 governed data-examples each showing served-answer + held-out-contradiction (never served); ONLY the runnable CFPB demo is labelled live (links to /consume), rest honest previews — no overclaiming, no dead design-page links, not-advice disclaimer, no secret leak ──
    ("scripts/check_baltor_guided_demos.py", "check_baltor_guided_demos"),
    # ── Anti-rot guard for the orientation doc: docs/CURRENT-STATE.md carries NO frozen flywheel proof-count (no-magic-values — reference the live signal), points to baltor_flywheel, and every concrete repo path it cites resolves (no dangling source handles) ──
    ("scripts/check_current_state_freshness.py", "check_current_state_freshness"),
    # ── ADVERSARIAL: every attack on the Shared I/O + Resource Spine fails closed — raw secret/DSN rejected (resource spec) or redacted (event), temp/persistent/cloud guards hold, events need correlation_id + known kind, work needs a lease (nack never silent), inference stores only the input hash, no artifact leaks a secret ──
    ("scripts/check_shared_io_resource_redteam.py", "check_shared_io_resource_redteam"),
    # ── Shared LLM Plane COMPATIBILITY: Ollama (cloud + local) + the free-but-limited tools (Groq/Gemini/OpenRouter/Cerebras/…) are governed CANDIDATE provider-graph nodes — secret-by-ref, candidate-not-active, customer-sensitive disallowed by default, shared-key bypass quarantined; inference degrades to the local stub offline (fallback recorded, output never truth) ──
    ("scripts/check_ollama_free_limited_compatibility.py", "check_ollama_free_limited_compatibility"),
    # ── Provider-adapter ABSTRACTION: one governed base class (InferenceProviderAdapter) with multiple API-method subclasses (deterministic_stub/openai_compatible/ollama_native/anthropic_messages), resolved by CONFIG (node.adapter_style) + swappable with no code change, byte-consistent with the gateway, SDK-free at import, secret-by-ref, degrading to ProviderUnavailableResult offline ──
    ("scripts/check_inference_provider_adapters.py", "check_inference_provider_adapters"),
    # ── ObjectShell.v1 conformance migration (LOSSLESS): ContextArtifact migrates to the canonical 14-section shell via the existing compose_object_shell — original preserved verbatim in payload (rehydratable to byte-identity), content_hash + handles carried, migration recorded in lineage, candidate status (no truth); manifest tracks remaining families as honest backlog ──
    ("scripts/check_object_shell_conformance_migration.py", "check_object_shell_conformance_migration"),
    # ── Shared I/O + Resource Spine END-TO-END roll-up: one scenario threads resource -> work -> event -> inference -> objectshell with a single correlation_id; specs validate, work is lease-gated, events redact secrets, inference stores the input hash + never truth, artifact wraps losslessly, no raw secret crosses any layer ──
    ("scripts/check_shared_io_resource_full_stack.py", "check_shared_io_resource_full_stack"),
    # ── Inference Gateway DISPATCHES through the adapter layer: oips.infer_local executes via adapters.resolve_adapter (the base class is the LIVE backbone, not a hardcoded stub); stub output delegated not inlined; byte-identical to the adapter; governed fallback to the stub offline; allow_network opt-in ──
    ("scripts/check_inference_dispatch_via_adapters.py", "check_inference_dispatch_via_adapters"),
    ("scripts/check_inference_adapter_styles.py", "check_inference_adapter_styles"),
    # ── Sales/lead-proof SAFETY GATE: claim language stays "appears/requires review" not legal-conclusion; no public accusation vs named real co without review; live third-party probe needs written authorization; outreach draft-only; regulated->legal review; synthetic seeds only ──
    ("scripts/check_sales_guardrails.py", "check_sales_guardrails"),
    # ── Baltor Chatbot Guardrail Audit: mode-aware (configurable engagement modes) audit of a PROVIDED transcript; flags regulated-risk answers in appears/requires-review language; private synthetic evidence pack; live third-party probe gated by mode + written authorization (offline seam) ──
    ("scripts/check_chatbot_guardrail_audit.py", "check_chatbot_guardrail_audit"),
    # ── Inference I/O: InferenceRequest (input hashed, never raw text) + ModelRouteDecision (governed-fallback trail, recorded) project the live OIPS gateway; receipt never 'served'; pure projectors in src/teleon/io ──
    ("scripts/check_shared_inference_io.py", "check_shared_inference_io"),
    # ── Eval/promotion I/O: ratified to the existing parallel-path engine (promotion always reversible by contract; engine proofs registered) + the new HumanApprovalReceipt gate so BOUNDARY EXPANSION requires approved human sign-off ──
    ("scripts/check_eval_promotion_io.py", "check_eval_promotion_io"),
    # ── Fragile Context Atlas: governed registry of fragile-context packs by domain x failure-mode (the strategic wedge) — REUSES FragilityMetadata.volatility_class + CanonicalFact.status + vocabularies/industries.yaml + the sales public-claim policy; ACTIVE packs are a bijection with the 14 live guided demos (no overclaim), CANDIDATE packs are honest backlog (never served); no vendor named; every time-fragile pack has a refresh policy ──
    ("scripts/check_fragile_context_atlas.py", "check_fragile_context_atlas"),
    # ── Fragile Context Atlas REDTEAM (negative proof): feeds the SAME validator (find_violations) deliberately-broken copies of the real atlas — vendor accusation, pack-as-truth, missing source-authority/held-out, missing refresh, leaked credential, served contradiction, benchmark/LLM cited as authority, demo overclaim, candidate-as-active — and asserts each guardrail fires; control proves the real atlas is clean ──
    ("scripts/check_fragile_context_atlas_redteam.py", "check_fragile_context_atlas_redteam"),
    # ── OpenContextHub surfaces the atlas: the OpenContextHub site's fragile-context section is GENERATED from architecture/fragile_context_atlas.json via portfolio_lib (cannot drift) — lock-step domain/mode counts + cfpb/sanctions/tariff served+held verbatim, the 'Run a Fragile Context Audit' CTA resolves to the section, reference-not-truth governance, no vendor named, built artifact matches ──
    ("scripts/check_opencontext_fragile_atlas_page.py", "check_opencontext_fragile_atlas_page"),
    # ── Fragile-context audit OFFERS: docs/sales/fragile-context-audit-offers.md is GENERATED from the atlas (one catalogued audit per distinct sales_audit_offer), in lock-step (regenerate-and-compare), producing the existing schemas/sales/* contracts under the public-claim safety gate (draft-only, appears/requires-review, authorized inputs, no named target without legal review); no vendor named; 10-field audit output ──
    ("scripts/check_fragile_context_audit_offers.py", "check_fragile_context_audit_offers"),
    # ── PurposeTask runtime hardening (P4): promotion is ALWAYS reversible — purpose_task.rollback reverts to the preserved rollback target, demotes the regressed impl into alternatives (LOSSLESS, re-promotable by adapt — a closed promotion<->rollback loop), consumes the pending target, and FAILS CLOSED (never blanks current_impl_id / never invents an impl) when no valid target ──
    ("scripts/check_purpose_task_rollback.py", "check_purpose_task_rollback"),
    # ── PurposeTask runtime hardening (P4): run_current_guarded contains a misbehaving impl — a handler that RAISES (bug/timeout/resource) or returns a non-RunnerResult becomes a structured DRIFT result (output '', error set, crashed=True), NEVER crashes the controller and NEVER fabricates a success; evaluate_health flags it and rollback/adapt self-heal ──
    ("scripts/check_purpose_task_hot_path_guard.py", "check_purpose_task_hot_path_guard"),
    # ── PurposeTask self-heal END-TO-END (P4 capstone): provision-by-capability → guarded hot path → drift → (cost) promote a cheaper EQUIVALENT side-by-side OR (crash) contain + rollback-recover; candidate never served before promotion, no promotion fabricated off a crash, predecessor kept as a reversible/lossless rollback target, registry never loses an impl ──
    ("scripts/check_purpose_task_self_heal_e2e.py", "check_purpose_task_self_heal_e2e"),
    # ── Self-prompting LOOP RUNTIME: builder generates each cycle's /loop prompt FROM .agent/next-action.json; a Stop hook continues the loop in-session (INERT by default, STOP-guarded, iteration-capped, fail-open) with an anti-slop/anti-fake-progress gate; the durable runner runs claude -p across sessions (--check/--dry-run launch nothing). Runs + improves the north-star forever, safely ──
    ("scripts/check_loop_runtime.py", "check_loop_runtime"),
    # ── Shared AI-AGENT RUNTIME layer (Teleon-owned): RECEIVES a bounded agent request → PROVISIONS it onto the appropriate Teleon execution backend (local emulator / K8s job / sandbox worker / cloud function) by delegating to execution_backend_selector → ExecutionProviderPort (rides FleetLedger; never a 2nd worker framework). ClawLess/OpenClaw + Hermes are CANDIDATE catalog entries only (never imported/executed, env:// runtime_ref, graceful AgentRuntimeUnavailable); local_emulator@v1 is the offline correctness invariant. Open-ended agents are hard-guarded off generic cloud functions; agents PROPOSE, Baltor DISPOSES — agent output is NEVER truth ──
    ("scripts/check_agent_runtime_layer.py", "check_agent_runtime_layer"),
    # ── Agent-runtime layer REDTEAM: one shared find_violations() validator reused by a CONTROL (real catalog + real dispatch outcomes + real module source = clean) AND 9 attacks that MUST be caught — candidate serves_truth=true / candidate imported|executed=true / raw key in a card / agent output→truth / open-ended agent provisioned onto a generic cloud function w/o an allow_generic proof / crash-instead-of-structured-unavailable / unknown-runtime-not-degraded / module imports src.baltor / a second active runtime. Owner-proven generic override is allowed. Hardens src/teleon/agents (agents PROPOSE, never serve truth) ──
    ("scripts/check_agent_runtime_layer_redteam.py", "check_agent_runtime_layer_redteam"),
    # ── Environment + Reward Spine RESEARCH REGISTRY (P1): Repo2RLEnv / Harbor / OpenEnv / ORS / RepoLaunch / SWE-bench / Terminal-Bench / R2E-Gym / SWE-smith / SWE-Gym / NeMo Gym cataloged as CANDIDATE|REFERENCE (NEVER active). Enforces: status never active; any Docker/network/LLM/key-gated entry carries a local_equivalent + proof_to_promote ladder; provenance/license tracked; no raw keys; Repo2RLEnv = repo_to_rl_env_generator (not LLM endpoint / coding agent); benchmark result = EVIDENCE, never promotion authority; output != truth. Converts the Repo2RLEnv due-diligence into governed infrastructure ──
    ("scripts/check_agent_environment_research_registry.py", "check_agent_environment_research_registry"),
    # ── Teleon competitive/runtime LANDSCAPE (P9 competitive intel): repos that do SLICES of Teleon (ARK/kagent/AgentScope-Runtime/agent-sandbox/Temporal/DBOS/Dapr/Hatchet/Inngest/Trigger.dev/Ouroboros/agentregistry) cataloged as substrate-adapter-candidate / sandbox-adapter / inspiration / adjacent-registry. Enforces: none IS the Teleon runtime (0 active; Teleon's own reference runtime + CapabilityTask standard stay the stable layer); every durable/execution substrate carries a do_not_adopt_as_primary guard (no second durable ledger/worker framework); Teleon differentiation articulated per competitor; positioning = control plane ABOVE, not another framework. Answers "any repos that do what Teleon does?" as governed infra ──
    ("scripts/check_teleon_runtime_landscape.py", "check_teleon_runtime_landscape"),
    # ── Open*Hubs BACKEND candidate registry (research→governed): which OSS repos power each hub's backend components (MCP registry/vector/hybrid-search/eval-harness/benchmark/compression/skill/tool/registry-service). Key finding: OpenMCPHub wraps the OSS official modelcontextprotocol/registry as a compatible sub-registry (reused across 4 hubs). discovery≠trust; candidate≠active; benchmark=evidence; output≠truth ──
    ("scripts/check_openhubs_backend_registry.py", "check_openhubs_backend_registry"),
    # ── Teleon-adjacent EXTENDED landscape (deep due-diligence): Restate/Prefect/Kestra/Windmill/Flyte/Ray/Modal/Cloudflare-Workflows = safe_to_wrap substrate adapters behind ExecutionProviderPort (do_not_adopt_as_primary); LangGraph-Platform/Cloudflare-Agents/Bedrock-AgentCore/Vertex-Agent-Engine = positioning_threat (differentiate on capability-contract+eval-gated-promotion+rollback+truth-boundary); Temporal+LangGraph 2-layer = thesis_strengthening. None IS the Teleon runtime ──
    ("scripts/check_teleon_adjacent_extended.py", "check_teleon_adjacent_extended"),
    # ── Environment + Reward Spine P0 CONTRACTS: schemas/environments/{EnvironmentRunRequest,EnvironmentRunResult,EnvironmentRunReceipt,RewardSpec,RewardResult,EnvironmentProviderNode,RewardProviderNode}.v1 registered in contract_registry; serves_truth/is_truth pinned const false (a run/score is EVIDENCE, never promotable/served truth); provider nodes candidate-first ──
    ("scripts/check_agent_environment_contracts.py", "check_agent_environment_contracts"),
    # ── Environment + Reward Spine P2: local EnvironmentProviderPort + RewardProviderPort + LocalEnvironmentProvider (offline/deterministic, no Docker/key, writes EnvironmentRunReceipt with input/output hashes, serves_truth=False) + deterministic RewardRunner (deterministic_check kinds) ──
    ("scripts/check_local_environment_provider.py", "check_local_environment_provider"),
    # ── Environment + Reward Spine P3: environment.baltor.cfpb_context_governance.local@v1 — a GOOD "10 business days" answer with a source handle passes; a BAD answer leaking the held-out "30 days" FAILS held_out_absent; output never truth; Teleon never imports Baltor ──
    ("scripts/check_baltor_context_environment.py", "check_baltor_context_environment"),
    # ── Agentic-bot plane P1A governed run contracts: schemas/agents/{AgentRunRequest,Result,Receipt,Tool/Skill/Sandbox/MemoryPolicy,ProviderUnavailableResult}.v1 — serves_truth/consumable/cross_tenant const false; secret_refs env:// only; agent-created skills const "candidate"+eval-before-active; sandbox deny-by-default. Agents PROPOSE, never truth ──
    ("scripts/check_agentic_bot_contracts.py", "check_agentic_bot_contracts"),
    # ── Capability-binding / IfC landscape (answers "tools that do capability/contract programming abstracting cloud-fn/K8s"): Nitric/Wing/Encore/Klotho(archived)/Score/Radius/Kratix/Crossplane/OAM-KubeVela/Knative/KEDA/Serverless-Framework cataloged as CapabilityTask BINDING TARGETS (Kratix/Radius/Score/Nitric closest). None owns the eval-gated LIFECYCLE → all are binding/execution adapters; Teleon is the control plane ABOVE. 0 active; license_confidence honest (Klotho archived, SF v4+ proprietary) ──
    ("scripts/check_capability_binding_landscape.py", "check_capability_binding_landscape"),
    # ── CapabilityTaskBindingProvider (realizes the binding layer): a CapabilityTask binds to local_function@v1 NOW (delegates backend choice to execution_backend_selector — open-ended agents hard-guarded off generic cloud functions) and to Nitric/Score/Temporal/Knative/KEDA/Kratix LATER by policy; candidate targets return BindingUnavailableResult (never imported/executed, env:// ref, backend_would_be shown); binding output serves_truth=False; Teleon never imports Baltor. Author never writes cloud-fn/K8s code ──
    ("scripts/check_capability_binding_provider.py", "check_capability_binding_provider"),
    # ── Teleon AGENT CAPABILITY GATEWAY P0 contracts (Teleon serves AI agents as customers): schemas/agents/{AgentCapabilityConsumer,Card,RunRequest,RunResult,Receipt,BoundaryExpansionRequest}.v1 — RunResult.serves_truth const false; BoundaryExpansionRequest status const "pending_human_approval" + auto_applied const false (agents can't self-expand); Card deterministic_first + llm_fallback_allowed + receipt_required ──
    ("scripts/check_teleon_agent_gateway_contracts.py", "check_teleon_agent_gateway_contracts"),
    # ── Teleon Agent Gateway P1 LOCAL runner: an agent consumer lists + runs DETERMINISTIC capabilities (utility.hash / cfpb.deadline.verify / json.schema.validate / tariff.hs.classify) → compact AgentCapabilityRunResult + receipt (runtime_path="deterministic", tokens_saved_estimate>0, serves_truth=False); deterministic-first token ladder; LLM fallback owner-gated (never in self-test); delegates to bind_capability_task; Teleon never imports Baltor ──
    ("scripts/check_teleon_agent_gateway_local.py", "check_teleon_agent_gateway_local"),
    # ── Teleon Agent Gateway P5 REDTEAM: control clean + 8 attacks caught — raw-secret-read / forbidden-tool / boundary-auto-apply / weakened-success-criteria / llm-fallback-without-policy / output-as-truth / raw-corpus-not-compact-receipt / benchmark-score-as-truth ──
    ("scripts/check_teleon_agent_gateway_redteam.py", "check_teleon_agent_gateway_redteam"),
    # ── Teleon Agent Gateway: runtime AgentBoundaryExpansionRequest reconciled to its schema (capability_id/requested_change/justification; status const pending_human_approval + auto_applied False preserved; legacy aliases accepted) — a runtime boundary-expansion now validates against AgentBoundaryExpansionRequest.v1 ──
    ("scripts/check_teleon_agent_gateway_boundary_schema_match.py", "check_teleon_agent_gateway_boundary_schema_match"),
    # ── Teleon Agent Gateway P2 MCP PROJECTION: the gateway projected as EXACTLY 5 stable MCP tools (list/describe/run/get_receipt/request_boundary_expansion); projection-only over AgentCapabilityGateway (no second gateway, no eval/exec, fixed dispatch table); compact cards/results (secret/backend/runtime fields scrubbed); serves_truth False; unknown tool → structured error ──
    ("scripts/check_teleon_agent_gateway_mcp_projection.py", "check_teleon_agent_gateway_mcp_projection"),
    # ── Teleon Agent Gateway P4 Baltor TRUTH BOUNDARY: context.governed_answer.evidence returns EVIDENCE (serves_truth False, status candidate) with held_out kept SEPARATE from the served output + source handles + governance marker {served_truth_owner:baltor, teleon_role:evidence_only}; Teleon never imports Baltor ──
    ("scripts/check_teleon_agent_gateway_baltor_boundary.py", "check_teleon_agent_gateway_baltor_boundary"),
    # ── Stateful Swarms / blackboard RESEARCH catalog (Irys due-diligence → governed infra): stateful_swarm.irys@research_candidate (MIT verified; Harvey-LAB claims unverified-until-reproduced; Python 3.12+/install/keys → never active, no truth authority) + blackboard/agent-memory landscape (graphiti/letta/langgraph-checkpoint/autogen-mem0/seekdb) as candidates behind local_sqlite@v1; benchmark=evidence-not-promotion; blackboard output≠truth ──
    ("scripts/check_stateful_swarm_provider_catalog.py", "check_stateful_swarm_provider_catalog"),
    # ── Governed blackboard P0 contracts (durable typed analytical state; Teleon runs, Baltor governs): schemas/blackboard/{Blackboard,Entry,Signal,Observation,Gap,Calculation,Analysis,Synthesis,SourceRef,WorkerReceipt,ConvergenceReport,CompressionReport,GovernedBlackboardEntry}.v1 — serves_truth const false on Entry/Analysis/Synthesis/Governed; Observation source_refs required+non-empty; Synthesis keeps held_out+source_handles; CompressionReport pins source_handles_preserved+held_out_preserved const true ──
    ("scripts/check_blackboard_contracts.py", "check_blackboard_contracts"),
    # ── LOW-COST (paid) LLM endpoint registry — cheaper Chinese/China-adjacent routes (DeepSeek/Qwen/SiliconFlow/Z.AI/MiniMax admit_first; Baidu/Tencent/Volcengine/StepFun/Moonshot probation) as a DISTINCT lane from free/*: cost_class lowcost_usd, candidate≠active, secrets vault:// refs only, output≠truth, and the load-bearing DATA-CLASS/JURISDICTION guard — low-cost/China lanes carry ONLY public+internal_non_sensitive, NEVER customer/regulated/secrets/confidential ──
    ("scripts/check_lowcost_llm_endpoint_registry.py", "check_lowcost_llm_endpoint_registry"),
    # ── SkillClaw → DETERMINISTIC TOOL promotion (Determinism Factory applied to skills): SkillClaw=research_candidate (MIT, WIP, no truth authority); 7-rung ladder observation→draft-skill→verified-skill→tool-candidate→deterministic-tool→certified→retired; deterministic-tool standard (no_llm/no_rng/no_wall_clock + same_output_hash + sandbox + human-approval + sbom/signed); tools never auto-published; skills mined only from public/synthetic/redacted traces; distillation lossless ──
    ("scripts/check_skill_to_tool_promotion.py", "check_skill_to_tool_promotion"),
    # ── TokenTamer → CONTEXT COMPRESSION (Lossless-law governed): tokentamer=research_candidate (MIT, alpha); MITM/SSL-interception mode QUARANTINED (local-dev opt-in only); 50-80% savings UNVERIFIED-until-benchmarked; compression-as-deterministic-tool (no LLM, stable parsers, same-input→same-output) that MUST preserve answer-critical facts + source handles + held-out warnings + rehydration; one active = the local deterministic skeleton invariant ──
    ("scripts/check_context_compression_catalog.py", "check_context_compression_catalog"),
    # ── CANDIDATE Open*Hub.io websites drawn from real modular components (OpenTemplates/Endpoint/Env/Sandbox/Agent/Receipt/State Hub) — PRIVATE-FIRST: all candidate (0 public/active), domains owner-clearance-gated, each with an open-on-competition trigger + a modular_component_source + distinct-from the 9 existing hubs; discovery≠trust; never public without owner trademark clearance ──
    ("scripts/check_candidate_open_hubs.py", "check_candidate_open_hubs"),
    # ── Governed blackboard spine P2: blackboard.local_sqlite@v1 (BlackboardProviderPort) — APPEND-ONLY sqlite store; rejects sourceless observations / serves_truth=true / missing-tenant-scope / mutate-existing; every append requires a worker_receipt; deterministic query (seq then entry_id); content-addressed ids; Teleon never imports Baltor; output never truth ──
    ("scripts/check_local_blackboard_provider.py", "check_local_blackboard_provider"),
    # ── Stateful-swarm spine P3: swarm.local_stub@v1 (StatefulSwarmProviderPort) + 6 deterministic workers (seed_planner/observation_extractor/gap_detector/entity_resolver/synthesis/governed_projection) writing typed entries + receipts to the local_sqlite blackboard; synthesis reads the BOARD not raw docs; gaps explicit; no live LLM; output never truth ──
    ("scripts/check_stateful_swarm_local_stub.py", "check_stateful_swarm_local_stub"),
    # ── blackboard.baltor.cfpb_evidence@v1 governed demo: signals→observations(source-handled)→gaps→held-out→verified→synthesis→governed answer; served = "10 business days"+handle, the stale "30 days" stays a held-out WARNING (never in the served answer); serves_truth False; Teleon returns candidate/evidence, Baltor governs truth ──
    ("scripts/check_baltor_governed_blackboard_demo.py", "check_baltor_governed_blackboard_demo"),
    # ── Stateful-swarm/blackboard REDTEAM: shared find_violations() — control clean + 12 attacks caught (observation→CanonicalFact / analysis→served_fact / synthesis-leaks-held-out / missing-source-handles / tenant-private-in-public / benchmark-as-promotion / irys-active-without-proof / live-LLM-in-turn / raw-key-in-receipt / compression-drops-held-out / entity-mismatch-not-a-gap / baltor-import) ──
    ("scripts/check_stateful_swarm_blackboard_redteam.py", "check_stateful_swarm_blackboard_redteam"),
    # ── Stateful-vs-stateless TOKEN ECONOMICS (deterministic ESTIMATE, not a real tokenizer): rereading docs every question vs build-blackboard-once + compact reads — stateful wins past the crossover (N=2 on CFPB+5Q: 1895 vs 4075 tokens, ~53% saved); source-handle coverage preserved, held-out leakage 0; report is_truth=false ──
    ("scripts/check_stateful_vs_stateless_token_economics.py", "check_stateful_vs_stateless_token_economics"),
    # ── PARENT brand canonical + lossless: architecture/brand.json is the ONE source of the parent / holding-company identity — company_name/wordmark "AI Done Right" + tagline "AI systems that can do the work, show the work, and prove the work." + domain aidoneright.dev (renamed from "ContextIsEverything Group" / "Context is Everything"; interim "AI is Everything" rejected); the prior name+taglines are PRESERVED as the rollback target (lossless); Baltor + Teleon recorded unchanged; full-words naming (no abbreviation); single-sourced — company_portfolio_map.json's parent display_name mirrors brand.json with no drift; the holding_company slug stays a code identifier ──
    ("scripts/check_brand_canonical.py", "check_brand_canonical"),
    # ── Context Auditor (src/baltor/context_audit): deterministic pre-LLM-call ContextAuditReport across all source kinds (system_prompt/CLAUDE.md/AGENTS.md/MCP-schemas/docs/memories/tool-output/code-comments) — flags duplicate (shingle-Jaccard) / conflicting (claim-key) / tool_bloat (schema-count) / stale (ttl); PROPOSES not disposes (applied=False); LOSSLESS (raw untouched, conflicts surface both + supersede≠delete); output≠truth; single-sourced authority order ──
    ("scripts/check_context_auditor.py", "check_context_auditor"),
    # ── Context-engineering TOOL LANDSCAPE catalog (architecture/context_engineering_tool_catalog.json): 20 candidate tools across 5 layers (token-waste obs / compression / tool-output isolation / code-context selection / memory-RAG dedupe+conflict); all candidate≠active + do_not_adopt_as_runtime; dedupe/supersession lossless-governed; the_gap = the Baltor-owned Context Auditor; distinct from context_compression_provider_catalog ──
    ("scripts/check_context_engineering_tool_catalog.py", "check_context_engineering_tool_catalog"),
    # ── Baltor→Teleon migration STEP 4 (FINAL): src/baltor/teleon_client — the versioned tenant client Baltor uses to reach Teleon (Baltor→Teleon direction); offline-first local calls + graceful fallback from a remote seam + per-call receipt (served_by/fallback); output is an inspectable receipt, not auto-truth. Completes the fleet→experiments→purpose_tasks→client extraction. ──
    ("scripts/check_teleon_client.py", "check_teleon_client"),
    # ── Context Auditor CONNECTED: src/baltor/context_audit/audit_bridge emits one bus event per finding (conflict→contradiction_found, stale→rot.detected, duplicate→context.duplicate_found, tool_bloat→context.tool_bloat) + a context.audited summary; the gateway pre-call path attaches the manifest to inference.requested; lossless + proposes-not-disposes; monotonic seq, no wall-clock. ──
    ("scripts/check_context_audit_bridge.py", "check_context_audit_bridge"),
    # ── Context Auditor LIVE in the connected pipeline: run_full_pipeline audits the assembled context (audit_and_emit) so context.audited + context.duplicate_found + context.tool_bloat fire mid-run on /dashboard, within the pipeline span, applied=False; no regression (core kinds + exactly one inference request); deterministic across runs. ──
    ("scripts/check_context_audit_in_pipeline.py", "check_context_audit_in_pipeline"),
    # ── Context Optimizer (src/baltor/context_audit/optimizer): applies a ContextAuditReport → a smaller optimized context view (duplicates dropped, conflict losers superseded + winner annotated contested, bloat/stale flagged) — LOSSLESS: raw + dropped + superseded + lineage preserved + exact rehydrate(); applied=True but supersede≠delete; output is a derived view, not truth. The Auditor→Optimizer layer of the owner's architecture. ──
    ("scripts/check_context_optimizer.py", "check_context_optimizer"),
    # ── Context Auditor over REAL governed context: src/baltor/context_audit/context_object_adapter.from_context_objects maps context-graph objects → auditor sources; run over the ACTUAL acme seed graph it flags the genuinely-stale runbook (real freshness metadata) + raises NO false conflict on agreeing structured claims (prose 5-vs-3 deferred to find_contradictions); deterministic, non-mutating, evidence-not-truth. ──
    ("scripts/check_context_object_audit.py", "check_context_object_audit"),
    # ── Auth/identity KIT (src/openharnesshub/auth_kit): owner-authorized 2026-06-09 — completely SEPARATE + INDEPENDENT login/register/onboarding per product (own accounts/sessions/registration, no cross-realm account, no SSO) built from ONE shared kit (make_realm); standard register→onboard→login flow; credentials are one-way refs (no cleartext; real password-hash/OAuth/SSO is a CredentialProviderPort seam); deterministic + injected clock. Open bottom-layer (Baltor+Teleon may import; OHH imports neither). ──
    ("scripts/check_auth_kit_realm_isolation.py", "check_auth_kit_realm_isolation"),
    # ── Local Identity & Access SERVICE (scripts/identity_local_service.py): the auth kit RUNNING as a local backend — registry-driven SEPARATE realms (parent+Baltor+Teleon+every LIVE hub via architecture/identity_realm_registry.json, products.js drift-gated both directions; private bench excluded), register→onboard→login→session + session-gated HASH-ONLY API keys (raw shown once) over HTTP; restart-safe dist/identity persistence; audited with X-AIDR-Request-Id correlation + rejected outcomes; no cleartext secret or raw key on disk. Local dev equivalent of service-auth Phase 1 — real crypto/OAuth/SSO stays an owner-gated CredentialProviderPort seam. ──
    ("scripts/check_identity_local_service_runtime.py", "check_identity_local_service_runtime"),
    # ── Harness-hub auth WIRED to the local identity service (web/harness-hub/identity.js + pages/auth.js): real register→onboard→login→session + /account/keys console against /api/identity/openharnesshub/* — registry drift-gated default port, OHH_IDENTITY_BASE deploy override, X-AIDR-Request-Id, only the opaque session handle in localStorage (passphrase memory-only, raw key shown once never persisted), SSO/Google rendered as DISABLED owner-gated seams, honest service-down message, no hardcoded tunnel URLs; node --check syntax-gates both files when node exists. ──
    ("scripts/check_harness_hub_auth_wiring.py", "check_harness_hub_auth_wiring"),
    # ── Cloud-Run-like LOCAL service plane (Browser E2E + Local Service Emulation Gate, owner add-on 2026-06-09): architecture/local_service_registry.json declares every local service/emulator with honest active_local/held/planned statuses + held reasons; scripts/local_services_lib + start/stop_local_services manage process groups (idempotent health-first start; stop only via service stop_command or exact recorded pid); ports drift-gated against portfolio_lib + the identity realm registry; every active group must start and answer health; dist/local-service-urls.md carries REAL URLs only (tunnel cells only from the recorded launcher manifest). ──
    ("scripts/check_local_services_health.py", "check_local_services_health"),
    # ── Browser E2E review artifacts are REAL and leak-free: e2e/crawl_all_surfaces.mjs (11 running surfaces × video + 1440/1280/390 stills + HTML + console + overflow + dead-link sweep) and e2e/register_login_portal.mjs (10-step register→onboard→activate+login→mint(blur+server-verify)→revoke→logout→re-login→session-restored journey in real Chrome against the real identity service) must leave: GIF videos ≥10KB, the 10 portal stills, both reports — with NO raw API key / credential ref / provider key / passphrase fixture in any text artifact, the ffmpeg-on-ubuntu26.04 limitation HELD honestly (GIF house pattern, not faked webm), and skipped held/planned services listed with reasons. ──
    ("scripts/check_no_raw_secrets_in_e2e_artifacts.py", "check_no_raw_secrets_in_e2e_artifacts"),
    # ── Native events/A-B plane (scripts/events_local_service.py): the handoff's EVENTS.md contract recreated in repo patterns (bundle Node core stays reference-only) — registry-ported (local_service_registry 9420), single/batch ingest, per-variant summary with conversion_rate, PII/key-shaped events REJECTED and never stored, restart-safe JSONL counters, /healthz /readyz /version /api/status, declares truth_authority:false (projection/evidence only — NOT the platform bus). ──
    ("scripts/check_local_events_plane.py", "check_local_events_plane"),
    # ── Service↔service /service/* handshake slice in the identity service (backlog 1.2, contracts/SERVICE-CONNECTIONS.md — makes the Service Connections dev console real): env-keyed service-account handshake (SERVICE_<REALM>_SECRET; 503 when unset, never faked), 8-scope vocabulary (S3) enforced, directional verify (TO realm only), both-realm connection lists projection-only, revoke with receipts, asymmetric grants (Baltor→Teleon ≠ Teleon→Baltor), user-realm isolation intact (a service token is not a user session), no raw token on disk (svtref: only). ──
    ("scripts/check_service_handshake_slice.py", "check_service_handshake_slice"),
    # ── Events/A-B beacon WIRED (backlog 2.1/2.3): web/harness-hub/events.js beacons page/exposure/conversion to the registry-ported events plane (drift-gated default port, OH_EVENTS_BASE override, sendBeacon, anon-only, client-side PII guard); app.js emits a page event per route + the builder_cta landing exposure + CTA conversion; the live /summary A/B readout is real (exposure/conversion/rate from a real loop); sticky deterministic variant assignment. ──
    ("scripts/check_events_beacon_wiring.py", "check_events_beacon_wiring"),
    # ── Ledger-only billing over LLM receipts (BUSINESS-PLANE order 1): scripts/billing_ledger.py — per-key/per-class/month statements from invocation receipts (model CLASS→rate single source, no model names in logic), reconcile() flags drift with receipts as the authority (never overwrites receipts from the provider), unknown class never invents a rate; authors no charge, calls no payment API. ──
    ("scripts/billing_ledger.py", "billing_ledger"),
    # ── Shared empty/loading/error UX kit (UX-BACKLOG P1 #3): web/harness-hub/oh-states.js — three token-only primitives with correct ARIA roles (status/aria-busy/alert), escaped interpolation, loaded in the shell; node-syntax-gated. ──
    ("scripts/check_oh_states_kit.py", "check_oh_states_kit"),
    # ── AI Done Right surface-family roster GATE (was unregistered — codebase-review G14): products.js defines parent + 2 products + the Open*Hub roster (live + private-bench, count COMPUTED not hand-typed) + the five-stage method spine; every referenced prototype HTML exists; roster drift fails both directions. Now flywheel-gated so adding/removing a hub can't silently drift. ──
    ("scripts/check_ai_done_right_surface_family.py", "check_ai_done_right_surface_family"),
    # ── AI Done Right handoff-docs freshness GATE (was unregistered — codebase-review G14): the handoff/transfer docs exist, record CURRENT surface counts, name the five method hubs, link the service-auth + design-family proofs, carry transfer artifacts, and contain no raw secrets. ──
    ("scripts/check_handoff_docs_freshness.py", "check_handoff_docs_freshness"),
    # ── Standardized transactional-email PORT (BUSINESS-PLANE §2; closes the one spec-only cross-cutting component): one send(realm,template,to,props) contract, realm-branded from the identity realm registry; console adapter renders to dist/email-outbox + audit and HONESTLY does not send (Mode Protocol, sent=False); Resend/Postmark are owner-gated seams (NotConfigured without a provider key — never a fake send); secret/template/recipient guards; no secret in the trail. Indexed in docs/architecture/component-standardization-index.md. ──
    ("scripts/email_port.py", "email_port"),
    # ── Metered billing chain (BUSINESS-PLANE §3; takes billing PARTIAL→fuller): scripts/billing_plane.py — receipts → meter → DRAFT invoice (single-sourced plan subscription + metered overage above the included allowance) on the ledger authority; Stripe is an owner-gated seam that raises NotConfigured without STRIPE_API_KEY (a charge is never faked); reconcile keeps receipts authoritative over the provider. Built on scripts/billing_ledger. ──
    ("scripts/billing_plane.py", "billing_plane"),
    # ── ADVERSARIAL auth across EVERY front end's realm (parent + Baltor + Teleon + 9 live hubs, not just harness-hub): each realm survives the happy path (register→verify-email→onboard→login→key→revoke→re-login) AND the attacks — duplicate register rejected, login-before-onboard rejected, wrong-password and unknown-account both 401 (NO account enumeration), mint without session 401, revoke-not-owned 404, injection-shaped identifier handled safely, cross-realm session/identifier isolation (no SSO), no cleartext secret or raw key on the wire or disk. ──
    ("scripts/check_adversarial_auth_all_realms.py", "check_adversarial_auth_all_realms"),
    # ── FULL-DESIGN bundle WIRED to real backends (owner: "bring the full design into the working apps"): dist/sites/openharness-design/shared/oh-identity.js — realm-aware identity client (drift-gated port, OHH_IDENTITY_BASE override, per-realm sessions, passphrase never stored) loaded across the surface HTMLs; the kit's OhAuth (oh-site.jsx) does REAL register/login against the identity service with honest preview fallback (never fakes a session) + Google/GitHub as disabled owner-gated seams; a page_view beacon fires to the events plane. The hundreds-of-hours design is now functional, not mock. ──
    ("scripts/check_bundle_full_design_wiring.py", "check_bundle_full_design_wiring"),
    # ── REGISTRY DATA BACKEND makes the full-design dashboards REAL (owner: "wire the registry data backend so the dashboards are real"): scripts/registry_local_service.py fulfils the declared local_openhub_projection_api (:9423) — a PUBLIC catalog seeded by extracting each hub's entries from the design bundle (single source, no retyped catalog) + a PER-ACCOUNT workspace (install/uninstall/publish/summary) replayed from an append-only log. Workspace endpoints are session-gated: the account is resolved by VALIDATING the realm session against the identity service (raw session id never persisted), so install/Installed/Published/Avg-eval/Activity/API-calls·30d on OhDashboard are the account's REAL numbers; publish → review queue (candidate ≠ active); truth_authority=false. shared/oh-registry.js (drift-gated port, OHH_REGISTRY_BASE override, reuses the identity realm + oh-session-<realm>) is loaded after oh-identity.js across the surfaces; oh-hub.jsx reads it for the dashboard/Installed/add-button with an HONEST fallback to the in-file design seed (never the seed presented as live) — DESIGN-CONTRACT markup preserved. ──
    ("scripts/check_registry_backend.py", "check_registry_backend"),
    # ── Foundry measure-stage Judge scorer ladder (closes the offline measurement cap): scripts/foundry/eval_scorers.py — deterministic ladder (exact-match/token-F1/REFERENCE-FREE faithfulness proxy/context-precision AP@k) scores lift WITHOUT a gold answer; model-backed NJudgeMajority returns None on judge disagreement and raises without a route (never fabricated); Ragas/DeepEval honest seams; LadderJudge drops into MeasurementStage. ──
    ("scripts/foundry/eval_scorers.py", "foundry_eval_scorers"),
    # ── Catalog→runtime processor BRIDGE (5W1H deepest unlock): scripts/runtime/catalog_processor_bridge.py — discovers every process_kind→component-id→callable from the manifests (single source) and resolves/invokes the 97 governed processors by id or unique process_kind; ambiguous kind raises with candidates; ALL discovered callables import. ──
    ("scripts/runtime/catalog_processor_bridge.py", "catalog_processor_bridge"),
    # ── Catalog processors registered INTO the runtime: scripts/runtime/catalog_runtime_adapter.py — wraps each catalog run() as a runtime Processor (handle(command,ctx)), emits a CANDIDATE processor_output artifact (gate promotes, not the adapter), registers the whole fleet into the ProcessorRegistry the runner uses; a run() error fails cleanly (no crash). ──
    ("scripts/runtime/catalog_runtime_adapter.py", "catalog_runtime_adapter"),
    # ── Processor dispatch-index DRIFT gate: scripts/build_processor_dispatch_index.py — the committed architecture/processor_dispatch_index.json (the stdlib-json map the runtime bridge reads, keeping the runtime YAML-free) must match the manifests; this rebuilds in memory and fails if it drifted. Manifests stay authoritative without a runtime YAML dependency. ──
    ("scripts/build_processor_dispatch_index.py", "build_processor_dispatch_index"),
    # ── Cohort compression-policy selector (context-efficiency 'consumer behavior'): scripts/processors/compression/cohort_policy_selector.py — reads a usage_gated_compress prior, classifies the tenant's usage SHAPE (power-user/iterating/fresh/balanced/unknown), and emits the compression curve (budget_fraction + utility/volatility/recency weights); power-user compresses the stable substrate hard, fresh barely compresses, unknown stays conservative; deterministic. ──
    ("scripts/processors/compression/cohort_policy_selector.py", "cohort_policy_selector"),
    # ── Model-provider LANES wired end-to-end (backlog #4): scripts/check_model_provider_lanes.py — Ollama Cloud / Mistral / OpenRouter / Anthropic / OpenAI / local Ollama each have a governed graph node (external nodes carry secret_ref + local_equivalent) AND a verified env→route mapping through model_route.from_env (offline, no network); live smoke runs only with a real key + OH_LANE_SMOKE_LIVE=1. ──
    ("scripts/check_model_provider_lanes.py", "check_model_provider_lanes"),
    # ── Receipt service (#10c; was status:planned): scripts/receipt_local_service.py — fulfils local_receipt_service (:9426); append-only content-addressed receipts for important flows (is_truth=false — the gate promotes, not this); filter by kind/flow, get by id; same content → same id (replay-detectable). ──
    ("scripts/receipt_local_service.py", "receipt_local_service"),
    # ── State service (#10c; was status:planned): scripts/state_local_service.py — fulfils local_state_service (:9427); keyed session/action state replayed from an append-only op-log (set/append/delete), truth_authority=false always; crash-safe history. ──
    ("scripts/state_local_service.py", "state_local_service"),
    # ── Ingest staging→measure→gate PROMOTE job (#7; closes health≠promotion): scripts/ingest/promote_staged.py — fed official-source rows are staging-only until this runs; offline (no model route) every unmeasured candidate routes to REVIEW (boundary held, no fabricated lift); with a route it measures real bare-vs-pipeline lift and PROMOTES the ones clearing the floor with provenance + durability. Composes model_route.measurement_stage + gate.evaluate (no new gate logic). ──
    ("scripts/ingest/promote_staged.py", "ingest_promote_staged"),
    # ── SHOWCASE PIPELINES gated (closes the "self-tested but un-gated" orphan): each scripts/showcase_pipelines/*.py COMPOSES the real processor run() callables end-to-end into a governed flow for a concrete scenario and self-tests the whole composition (the ONE simulated seam is the model call). These were runnable but reachable from no gate; now the flywheel keeps every showcase green so a processor change that breaks a composition is caught. Spread across durability classes (precedence/aggregation/freshness/coded-vocabulary/low-resource) and domains beyond CFPB. ──
    ("scripts/showcase_pipelines/regulated_fact_qa.py", "showcase_regulated_fact_qa"),
    ("scripts/showcase_pipelines/governed_rag.py", "showcase_governed_rag"),
    ("scripts/showcase_pipelines/clinical_support.py", "showcase_clinical_support"),
    ("scripts/showcase_pipelines/low_resource_alert.py", "showcase_low_resource_alert"),
    ("scripts/showcase_pipelines/context_efficiency_loop.py", "showcase_context_efficiency_loop"),
    ("scripts/showcase_pipelines/sanctions_aml_screening.py", "showcase_sanctions_aml_screening"),
    ("scripts/showcase_pipelines/cve_dependency_triage.py", "showcase_cve_dependency_triage"),
    ("scripts/showcase_pipelines/icd10_coding.py", "showcase_icd10_coding"),
    # ── Related-party / shell-network discovery (owner-requested: networks of relationships — employment agencies, shared addresses/phones/officers, M&A): scripts/showcase_pipelines/related_party_network.py — normalize identifiers → shared-identifier graph → UNION-FIND connected components; three "independent" staffing agencies sharing one normalized address+phone+officer collapse into ONE HIGH-risk shell network (escalated), while a DISCLOSED M&A pair stays NORMAL and a standalone stays a singleton. The hidden network a bare model can't compute; signed registry governs over scraped news; serves_truth=false. ──
    ("scripts/showcase_pipelines/related_party_network.py", "showcase_related_party_network"),
    # ── Common-control resolution from M&A NEWS (owner-requested: mergers & acquisitions): scripts/showcase_pipelines/common_control_resolver.py — chain acquisitions by date → each entity's ultimate parent; a 'vendor' and a 'customer' both rolled up to ParentCo over two deals are flagged as a RELATED-PARTY (self-dealing) transaction and escalated — but NOT before the second deal closed (temporal/as-of axis), and not for truly independent parties. The post-cutoff, transitively-chained control a bare model can't track; signed registry governs; serves_truth=false. ──
    ("scripts/showcase_pipelines/common_control_resolver.py", "showcase_common_control_resolver"),
    # ── Beneficial ownership + OFAC 50% rule (owner-requested M&A / evolving ownership hierarchies in merger-heavy industries — staffing/employment agencies, real-estate brokerages): scripts/showcase_pipelines/beneficial_ownership_resolver.py — resolve each entity's AUTHORITATIVE current parent from CONFLICTING ownership claims using the real scripts/artifact_graph/source_authority classifier (an SEC 8-K GOVERNS over a press rumor; flip the publisher → the owner flips), then apply OFAC's 50% rule: a block on an SDN-listed person (Volkov Holdings) PROPAGATES down every ≥50% ownership edge so Apex Staffing is BLOCKED BY INHERITANCE (unlisted) while the 40%-owned Beacon is not. Authority is EARNED not assumed; temporal as-of; serves_truth=false. Showcases the source-authority work end-to-end on the ownership domain. ──
    ("scripts/showcase_pipelines/beneficial_ownership_resolver.py", "showcase_beneficial_ownership_resolver"),
    # ── FDA drug-labeling claim review (regulated-fact vertical on the EARNED source-authority engine): scripts/showcase_pipelines/fda_labeling_claim_review.py — substantiate each promotional claim against the FDA-APPROVED label (fda.gov, official agency, via scripts/artifact_graph/source_authority); a 25-mmHg efficacy overclaim (contradicts the label) and a 40%-heart-attack-risk claim (off-label, no approved topic) are HELD OUT + escalated as FDCA-502 risk; flip the source → the substantiated claim flips. serves_truth=false. ──
    ("scripts/showcase_pipelines/fda_labeling_claim_review.py", "showcase_fda_labeling_claim_review"),
    # ── BIS export-control screening (regulated-fact vertical): scripts/showcase_pipelines/export_control_screening.py — screen each export's end-user against the authoritative BIS Entity List (bis.doc.gov) vs a stale vendor screening DB; the vendor "clear" is HELD OUT and the export to the LISTED end-user REQUIRES A LICENSE (escalated, EAR) while a clean end-user clears; flip the source → the screen flips. Earned authority; serves_truth=false. ──
    ("scripts/showcase_pipelines/export_control_screening.py", "showcase_export_control_screening"),
    # ── Fragile fact-base watchtower (owner-requested: licensed employment agencies in the Philippines): scripts/context_workers/ph_employment_agency_watchtower.py — DMW/POEA + DOLE official evidence governs licensing status, stale customer/vendor context is held out, unavailable official sources create verification tasks, and Teleon deterministic tools stay separated from LLM-assisted candidate evidence. ──
    ("scripts/context_workers/ph_employment_agency_watchtower.py", "ph_employment_agency_watchtower"),
    # ── Procurement collusion / bid-rigging ring (owner-requested relationship-network 'etc'): scripts/showcase_pipelines/procurement_collusion_ring.py — aggregate bids ACROSS tenders → a co-bidding group whose wins ROTATE and whose losing bids are COVER BIDS (just above the winner) is flagged as a bid-rigging ring (RingCo/BidCo/CovCo escalated), while an honest undercutter is excluded and a competitive ledger is not flagged. The ring is a property of the whole bid history — invisible to a per-tender model; signed award notice governs; serves_truth=false. ──
    ("scripts/showcase_pipelines/procurement_collusion_ring.py", "showcase_procurement_collusion_ring"),
    # ── LLM-plane local service ACTIVATED (#service-registry; was status:planned): scripts/llm_plane_local_service.py — fulfils local_llm_plane_emulator (:9425) by PROJECTING the canonical OIPS router (src/teleon/inference) over /api/inference/* (providers/models/health/route) — wires that module, never duplicates routing. A route returns the real select_provider decision + a DETERMINISTIC offline stub completion (is_stub, served_truth=false) + a receipt (is_truth=false); network LLMs stay owner-gated (an external node only wins if its secret is actually present, else it falls back to the local equivalent). ──
    ("scripts/llm_plane_local_service.py", "llm_plane_local_service"),
    # ── Governed-examples GALLERY built from REAL pipeline output (the recordable surface for "more videos, more examples"): scripts/build_examples_gallery.py — imports all 8 showcase pipelines, runs each run() on its own synthetic inputs, and renders ONE self-contained on-brand HTML (dist/examples-gallery/index.html) where every card's verdict/trace/report is the pipeline's ACTUAL deterministic output (BLOCKED 54% / AFFECTED+KEV / abstained / SERVED 28% / ESCALATED / SIGN-OFF / savings). No external resources, no JS — recordable offline by e2e/record_examples_gallery.mjs. Single-sources the portfolio CSS (portfolio_lib.SHARED_CSS). ──
    # ── README COUNT-DRIFT gate (no-magic-values; the canonical "172→thousands" bug): scripts/build_readme_stats.py --self-test (== --check) — the generated catalog-stats block AND every inline `<!--N:key-->value<!--/N-->` count in README prose (demo scripts, foundry modules, design patterns, model adapters, code templates) must equal the computed value; a hand-typed count that drifts from reality now FAILS the gate instead of rotting quietly. ──
    ("scripts/build_readme_stats.py", "build_readme_stats_check"),
    ("scripts/build_examples_gallery.py", "build_examples_gallery"),
    # ── ADVERSARIAL gallery-video verifier gated: scripts/check_examples_video_verifier.py — a recorder asserting "the DOM had the verdict" never proves the VIDEO FILE shows anything. e2e/verify_examples_gallery_videos.mjs inspects the bytes (size / duration / 1600x900 / not-blank via luma range / not-black / not-frozen via start-vs-end PSNR) and its --self-test synthesises blank/black/frozen/short/wrong-size videos and proves it REJECTS each on the right check. The recorder runs the verifier on every full run AND strengthens its own in-page checks (chip visible + in-viewport + FULL verdict text + card not half-rendered + no overflow/console errors). Environment-tolerant: runs the discrimination self-test where node+ffmpeg exist, skips honestly otherwise. ──
    ("scripts/check_examples_video_verifier.py", "check_examples_video_verifier"),
]
