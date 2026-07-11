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
    ("scripts/security/skill_scanner.py", "skill_scanner"),
    ("scripts/ops_console_service.py", "ops_console"),
    ("scripts/ops_intake.py", "ops_intake"),
    ("scripts/ops_logs.py", "ops_logs"),
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
    ("scripts/check_sops_secrets.py", "check_sops_secrets"),
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
    # multi-substrate primitive store: ONE put_primitive() -> operational DB (pg/pgvector) + git-like store + object bucket, converged via the sync engine (owner: "store all primitive info in all locations")
    ("scripts/runtime/primitive_multistore.py", "primitive_multistore"),
    # go-live readiness: the owner-residual matrix (READY = agent-done, OWNER = you provide), so "get me to just provide keys" is watchable
    ("scripts/deploy/go_live.py", "go_live"),
    # the ONE lightweight JSONL reader (tolerant/strict) — canonical home for the pattern duplicated across the tree
    ("scripts/_jsonl.py", "_jsonl"),
    # the ONE single-document JSON reader (tolerant read_json_or / strict read_json_strict) — sibling of _jsonl;
    # replaces ~80 divergent _read_json/_load_json copies, several of which returned {} on corrupt and HID corruption
    ("scripts/_json.py", "_json"),
    # the ONE UTC, Z-suffixed timestamp (now_iso) — replaces ~36 ad-hoc _now()/iso_now() copies, some of which
    # emitted LOCAL time with no Z (unorderable across zones)
    ("scripts/_time.py", "_time"),
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
    # ── CAPABILITY SEEDS (learn-from-them, clean-room): all 10 reviewed repos implemented as 11 governed seeds in _repos/teleon/backend/src/teleon/seeds — drop-in only for clean licenses, technique-only for copyleft/unstated; each runs real logic + records the lesson + emits a PurposeTask candidate; court-deadline + inference-routing seeds deterministically CORRECT; never serves truth, nothing promoted ──
    ("scripts/check_capability_seeds.py", "check_capability_seeds"),
    # ── PROFESSION-SCALE SEEDER: generalize the DueCare template beyond migrant-worker protection — 15 professions / 11 sectors derive 55 DURABLE governed capability candidates (license-verification · exclusion-screening · compliance-currency + profession-specific) on the O*NET/WORKBank spine; DueCare is ONE instance; never serves truth, nothing promoted ──
    ("scripts/check_profession_capability_seeder.py", "check_profession_capability_seeder"),
    # -- PROFESSION CALCULATORS: the DETERMINISTIC clean-room If-Statement implementations that CLOSE the determinism_ceiling=1.0 candidates the seeder only DECLARES (FMCSA Hours-of-Service: 11h drive / 14h window / 30-min break / 60-70h cycle, with off-duty-consumes-window + sub-30-no-reset + on-duty-satisfies-break + 34h-restart nuances; DEA CSA: schedule I-V lookup + prescribing/refill consequences -- II no refills, III/IV 5-refills/6-months, V NOT capped at that limit); over public regulation (clean-room), lineage-linked to its candidate, and NEVER serves truth (candidate until verified against the live rule) -- how a gap candidate advances toward promotion-readiness --
    ("scripts/check_profession_calculators.py", "check_profession_calculators"),
    # ── REPO_REFERENCE manifest: external repos cloned for offline study are governed + reconstructable (slug+SHA) WITHOUT republishing — vendorable agrees with the license class (copyleft/unstated/private never vendorable), folder gitignored, every reviewed repo + the DueCare template covered, distilled seeds map to real artifacts ──
    ("scripts/check_repo_reference_manifest.py", "check_repo_reference_manifest"),
    # ── FUNDAMENTAL PRIMITIVES taxonomy: ONE canonical map of the system's primitives (data storage/transfer/computation/unit/medium · interop/context/skill standards · k8s/cloud-fn/execution/environment runtime · seven-primitive grammar · the assurance wedge), each mapped to a REAL artifact; all owner-requested families covered; assurance first-class; generated code/file map (no drift); non-destructive index ──
    ("scripts/check_fundamental_primitives_taxonomy.py", "check_fundamental_primitives_taxonomy"),
    # ── CODE GRAPH: deterministic ast-based dependency graph (file→file imports + crossing symbols) over src/scripts/local_emulators; upstream/downstream are exact inverses; impact = transitive blast radius; neighbors by file path → "edit 1 file, see what breaks"; stdlib-only, always available; never serves truth ──
    ("scripts/code_graph.py", "code_graph"),
    # ── SYMBOL GRAPH: AST symbol-level nodes (function/class/method) + WEIGHTED edges (calls/inherits/contains); module-aware confident-only resolution (ambiguous/builtin-shadow calls dropped+counted, no false hubs); weighted load-bearing ranking; stdlib-only; never serves truth ──
    ("scripts/symbol_graph.py", "symbol_graph"),
    # ── CODEGRAPH (unified+weighted): fuses file-import + symbol call/inherit graphs into one strength-ranked model; `--audit <file|module|symbol>` ranks the strong connections (importers/callers by call-sites×confidence + blast radius) to review when changing something; bounded artifact w/ counted overflow; never serves truth ──
    ("scripts/codegraph.py", "codegraph"),
    # ── PYPREFIX (AI-first deterministic identifiers): the CONVENTION-based complement to codegraph — encode kind+file+scope+meaning in every owned Python definition (`py_<kind>_<file>__<scope>__<name>`, no hashes) so grep is an exact resolver + graphs need no LLM; check/map/find/stats/audit/graph/opgraph + compile-verified codemods for package/module/local/safe-arg migrations; stdlib-only; never serves truth ──
    ("scripts/pyprefix.py", "pyprefix"),
    # ── PYPREFIX CONFORMANCE CONTRACT (anti-regression, owner 2026-06-27): every path in _repos/shared-backend-components/architecture/pyprefix_migration.json `migrated` MUST stay 100% conformant to the typed convention (pyprefix check == 0); a renamed package can't silently diverge. Empty manifest passes (migration just started); the gate holds the line as ChatGPT Codex migrates package by package; never serves truth ──
    ("scripts/check_pyprefix_conformance.py", "check_pyprefix_conformance"),
    # ── PYPREFIX METHODOLOGY CONTRACT (repo-wide migration rules): _repos/shared-backend-components/architecture/pyprefix_methodology_rules.json formalizes owned-source scope, package-sized dry-run/apply, proof-gate oracle, dynamic-ref unresolved policy, and coordinated contract renames; checker verifies required rule ids, path exclusions, and every migrated path remains 100% conformant; never serves truth ──
    ("scripts/check_pyprefix_methodology.py", "check_pyprefix_methodology"),
    # ── CANONICAL-ID SINGLE SOURCE (data-object plane of the naming law, hardened 2026-07-01): every generated id in src/** is minted by src.teleon.experiments.ids (canonical_id = "{prefix}-{sha256[:16]}" over canonical_bytes; version in schema_version METADATA, never names/ids). Direct `import hashlib` in src/** is the drift signal; legacy sites are RECORDED in _repos/shared-backend-components/architecture/canonical_id_migration.json and ratchet DOWN — a NEW site fails, a migrated file must leave the baseline same-change; never serves truth ──
    ("scripts/check_canonical_id_single_source.py", "check_canonical_id_single_source"),
    # ── PRIMITIVE-LIFT BENCHMARK (AIDevObserver Benchmark Lab, v0 2026-07-01): A/B harness proving the black-box thesis — Run A rebuilds helpers monolithically reading FULL SOURCE as context; Run B composes the EXISTING primitives (normalize_field_name + canonical digests) through the real DAG runtime reading only EDGE CARDS. Subprocess-isolated resource envelope per arm: tokens_est + context_bytes_read + peak_rss_kb + py_alloc_peak_kb + cpu/wall + model_calls, every estimate basis-labeled; arms must be output-hash EQUIVALENT; receipts L4 candidate-only, never truth ──
    ("scripts/primitive_lift_benchmark.py", "primitive_lift_benchmark"),
    # ── Scaled token-savings experiment platform: thousands of reuse-vs-rebuild experiments over the REAL
    #    retrieval engine → avg tokens saved, areas we DON'T save (by kind|family + primitive size), coverage
    #    gaps we NEED MORE of. net_saved = hit?(rebuild−reuse):(−reuse) so retrieval MISSES cost tokens
    #    (break-even precision reported); all-miss mutation nets negative (not rigged); serves_truth=false. ──
    ("scripts/run_token_savings_experiments.py", "run_token_savings_experiments"),
    # ── Primitive readiness + remix benchmark: scores every primitive against the standard (well-formed /
    #    typed edges / canonical id / quality / determinism / governed — discriminates: 100% on verified,
    #    0% fully-compliant on raw drafts), runs thousands of remix simulations over the edge graph
    #    (remixable_rate + reachable depth — exposes the composability gap), and flags missing-producer +
    #    orphan-output edges = "primitives that don't exist yet". Deterministic; serves_truth=false. ──
    ("scripts/bench_primitive_readiness_and_remix.py", "bench_primitive_readiness_and_remix"),
    # ── Parameter-grid SWEEP: the missing complement to the fixed-strategy path bake-off — sweeps the harness
    #    knobs (intent mode / top-k / remix depth) as a cartesian grid of REAL runs across 3 sub-grids, ranks
    #    each by its primary metric, and keeps the FULL labelled portfolio (winner + losers) per the multi-path
    #    law so a re-run can re-adapt. Deterministic; serves_truth=false. ──
    ("scripts/run_experiment_parameter_grid.py", "run_experiment_parameter_grid"),
    # ── Code held to the PRIMITIVE standard: scores OUR modules by the same readiness+remix+gap lens (named /
    #    reused / composes / remixable / verified over the import graph). Surfaces islands + high-fan-in-
    #    UNVERIFIED modules (concentrated risk). Found: code is 80.6% remixable (vs primitives 25.6%), naming
    #    97.8%, but only 41.8% verified. Deterministic; serves_truth=false. ──
    ("scripts/bench_code_readiness_and_remix.py", "bench_code_readiness_and_remix"),
    # ── The generic MULTI-PATH capability for CODE (strategy_portfolio): register N contract-substitutable
    #    implementations behind one selector (rows, not ifs), run the ACTIVE_DEFAULT (reproduces today), or RACE
    #    them on the same input and KEEP the losers as labelled fallbacks — the reusable analog of a primitive's
    #    variant portfolio, so code gets the same flexibility/path discipline. serves_truth=false. ──
    ("scripts/strategy_portfolio.py", "strategy_portfolio"),
    # ── Read a primitive like an ONION (primitive_onion): signature/docstring (L0, ~tens of tokens) to COMPOSE
    #    cheap, PEEL deeper (blackbox→contract→provenance) only to troubleshoot — either direction — so the LLM
    #    reads only the layer it needs, not the whole card. Plus deterministic edge REMIX (fresh id, lineage
    #    kept, version in metadata, origin preserved). The token-reduction heart of the composition vision. ──
    ("scripts/primitive_onion.py", "primitive_onion"),
    # ── Functional proof of the canonical-id MINTER (closes the top code-verification gap the readiness lens
    #    found: 29 dependents, was unverified): determinism in- AND cross-process under differing PYTHONHASHSEED,
    #    collision-resistance, content-sensitivity, formatting-stability, shape, no-version-in-id. ──
    ("scripts/check_experiments_ids.py", "check_experiments_ids"),
    # ── Solved-problem REUSE economics (LeetCode corpus): the goal is TOKEN REDUCTION on already-solved
    #    problems (reuse, not new capability), so this measures TOKENS SAVED BY REUSE vs WASTED REGENERATING
    #    with an HONEST label-verified match (not a lexical false-positive), and ranks the reuse gaps —
    #    solved solutions worth INDEXING — by regenerate-tokens-at-stake. serves_truth=false. ──
    ("scripts/bench_leetcode_coverage.py", "bench_leetcode_coverage"),
    # ── Intelligent COMPOSITION (compose, don't cache): measures edge connectivity under EXACT vs TYPE-aware
    #    matching. Exact ~10% input-satisfiability (the 8%/25.6%-remix artifact); type-aware ~99% (9.5x lift) —
    #    proving primitives DO compose and the missing piece is the intelligent edge-matcher, not a cache.
    #    TYPE is an honest token-overlap proxy (upper bound). serves_truth=false. ──
    ("scripts/bench_intelligent_composition.py", "bench_intelligent_composition"),
    # ── EDGE-TYPE MATCHER (the composition lever, factored): ONE reusable type-aware matcher every composer/
    #    benchmark can import — build_producer_index(cards) (produces/consumes id-LISTS keyed on canonicalize_edge,
    #    generalizing check_primitive_composability.build_type_index) + match()/producers()/connectivity() over
    #    exact→canonical(curated-vocabulary fold)→token tiers, each hit a ~50-token signature layer. Turns the
    #    ~99% token-overlap PROXY into the honest canonical connectivity number (measured, not asserted). serves_truth=false. ──
    ("scripts/edge_type_matcher.py", "edge_type_matcher"),
    # ── Edge as a MULTI-REPRESENTATION portfolio (edge_representations): one edge expressed raw / canonical /
    #    FAMILY (data-driven dominant-type standardization: folds surface variants, connectivity exact 11% ->
    #    canonical 36% -> family 96%) / token-set / deterministic EMBEDDING / structural; with compatibility
    #    (strongest-representation-wins), search, remix, and a governance BLOCK gate — all across representations.
    #    Confidence-ordered so a match is labelled; serves_truth=false. ──
    ("scripts/edge_representations.py", "edge_representations"),
    # ── The MINIMUM-TOKEN orchestration protocol (primitive_orchestration): hands an LLM (any size) the minimal
    #    context to BUILD a system by wiring primitives — each as its blackbox+edges signature only, plus the
    #    deterministic+hybrid compatibility verdicts the SYSTEM computed, the ordered route, and gap specs to
    #    generate. Token budget proves it (~57 tok vs ~654 full-card = 11.5x, vs ~5232 regenerate = 91.8x). The
    #    LLM wires + fills gaps; it never reads an impl or recomputes compatibility. serves_truth=false. ──
    ("scripts/primitive_orchestration.py", "primitive_orchestration"),
    # ── HYBRID COMPOSER (partial solution + generate the gaps): backward-chains a route toward a target from
    #    EXISTING primitives (read by primitive_onion signature, driven by an injected edge_type_matcher oracle)
    #    and emits every unbridgeable edge as a candidate generation_spec (adapter_plan vocabulary, canonical_id
    #    minted, promotion-blocked) for an LLM to fill LATER — with reuse-vs-regenerate token accounting. Emits
    #    specs deterministically; never calls an LLM; never promotes. serves_truth=false. ──
    ("scripts/hybrid_composer.py", "hybrid_composer"),
    # ── PRIMITIVE BUILD LOOP (the flywheel to a fixed point): compose a route toward a target, deterministically
    #    REMIX a near-match producer's output edge to fill each gap (via edge_representations.compatibility where
    #    the match is canonical/family/embedding), INGEST the remixed variants (fresh canonical_id, lineage kept),
    #    and RE-COMPOSE until no new gap closes (fixed point). Finds real gaps on NOVEL/external targets; corpus
    #    targets are already covered (97.4% family connectivity). No LLM, no RNG; every variant candidate=true /
    #    serves_truth=false; version in metadata. ──
    ("scripts/primitive_build_loop.py", "primitive_build_loop"),
    # ── CAPABILITY EMBEDDING (the SEMANTIC DISCOVERY axis, 2026-07-05): embeds a primitive's BLACKBOX (its
    #    INTENT — what it does), not just its edges, so a paraphrased request finds the right primitive by MEANING
    #    (top-1, no shared keyword). Structured capability key (blackbox intent ⊕ input/output interface),
    #    deterministic O(N) intent retrieval = the decompose-by-RETRIEVAL front-door core, multi-path embedder
    #    (offline token/trigram proxy default; real Ollama nomic-embed-text as a labelled path with graceful
    #    fallback). Mutation- + determinism-gated; candidate/serves_truth=false. ──
    ("scripts/capability_embedding.py", "capability_embedding"),
    # ── PRIMITIVE DESCRIPTOR (multi-facet describe + compare, 2026-07-05): one primitive, MANY comparable facets
    #    on a PRECISION↔RECALL spectrum — engineered SYMBOLIC dimensions (keywords, keyphrases, datatypes,
    #    operations, operation-count, scalar-vs-other impact class) fused with the SEMANTIC blackbox embedding;
    #    a blocking→impact→operation→datatype→phrase→keyword→semantic ladder (strongest tier wins) + a fused
    #    score + selectable search method. Single-source datatype/operation/impact lexicons; mutation- +
    #    determinism-gated; candidate/serves_truth=false. ──
    ("scripts/primitive_descriptor.py", "primitive_descriptor"),
    # ── PRIMITIVE RETRIEVAL BAKEOFF (multi-path law applied to RETRIEVAL, 2026-07-05): a WIDE named feature
    #    factory (≈181k columns over the real corpus: per token/phrase/datatype/operation/impact/edge-shape/
    #    embedding-bucket) + a ZOO of sub-linear candidate strategies (multi-resolution overlapping MinHash-LSH,
    #    SimHash-LSH, hierarchical cascade, multi-type datatype routing, operation/edge-family partitions, greedy
    #    embedding canopies) RACED on a labelled query set by a measured receipt (recall@k / precision@k / mean
    #    candidates scanned = cost). Champion picked, all losers kept as labelled fallbacks — we MEASURE which
    #    representation grabs best+cheapest, never guess. Deterministic (fixed content-derived hash families, no
    #    RNG); candidate/serves_truth=false. ──
    ("scripts/primitive_retrieval_bakeoff.py", "primitive_retrieval_bakeoff"),
    # ── MECHANISM ZOO (the kitchen sink as ONE typed graph): dimension families + candidate generators +
    #    ordering mechanisms + deterministic remix mechanisms catalogued by NAME (counts computed), a typed
    #    composition graph (dim --feeds--> gen --then--> ord --then--> rmx), runnable pipelines composed from
    #    named parts (incl. ORDER-sensitive generator cascades + gap-filling remix), and a TUNER that races the
    #    combination grid by receipt — which combination, in which order, is MEASURED, never assumed. Builds no
    #    new mechanism: pure composition of the proof-gated zoos. candidate/serves_truth=false. ──
    ("scripts/primitive_mechanism_zoo.py", "primitive_mechanism_zoo"),
    # ── DOMAIN TOKEN-SAVINGS BENCH: the owner-named domains (leetcode/algorithms, AI/LLM, DAG/workflow, data
    #    engineering, scraping, browser, agentic, image/media, documents, devops) x two lanes — retrieval
    #    token-savings (REAL experiment engine, labeled probes, verified precision) + full compose-pipeline
    #    DAG-ability — rolled into per-domain savings + ranked NEEDS (more_dags / more_cards / more_flexibility
    #    / more_inputs_outputs with unmet edges NAMED). Receipts append-only (lossless). serves_truth=false. ──
    ("scripts/bench_domain_token_savings.py", "bench_domain_token_savings"),
    # ── COMPILED ROUTE CACHE (the Compiled-AI amortization loop over OUR routes): compile ONCE via
    #    compose_solution, execute MANY at artifact-read cost with ZERO model calls, and emit the paper's
    #    headline receipt — break-even use count + reduction ratio at N. A cached route is a compiled
    #    CANDIDATE (serves_truth=false); a miss raises rather than silently compiling (the cost the receipt
    #    exists to measure must never hide). ──
    ("scripts/compiled_route_cache.py", "compiled_route_cache"),
    # ── CODE FACTORY LANE (the paper's constrained-generation middle rung, side-by-side): a model_step gap
    #    spec renders into a VALIDATED TEMPLATE and runs the four-stage pipeline (render -> compile-check ->
    #    self-test -> security screen) into a candidate card (needs_review:true, serves_truth=false) — the
    #    /ide cliff between 0%-LLM template and 100%-unconstrained harness gains its middle rung. ──
    ("scripts/code_factory_lane.py", "code_factory_lane"),
    # ── COMPILED ROUTE STORE: append-only JSONL persistence for the compile-once cache — delta-only saves,
    #    last-write-wins load, ledger-alone receipt byte-identical to live, torn-tail tolerated (lossless). ──
    ("scripts/compiled_route_store.py", "compiled_route_store"),
    # ── GENERATED-ARTIFACT SECURITY (the paper's measured security headline, ours to match): prompt-injection
    #    screen + AST code-safety screen over labelled fixture suites with accuracy/false-positive RATES in the
    #    PASS line (zero false positives asserted), mutation-gated. ──
    ("scripts/check_generated_artifact_security.py", "check_generated_artifact_security"),
    # ── UNMET-EDGE PRODUCER MINTING: the domain benchmark's NAMED unmet output types become staged producer
    #    candidate cards (append-only, deduped, provenance = the benchmark receipt as demand signal). ──
    ("scripts/mint_unmet_edge_producers.py", "mint_unmet_edge_producers"),
    # ── AIDevObserver checks formerly OUTSIDE the umbrella (alignment-audit gap): all now run BARE (the
    #    missing-bootstrap class was fixed across them) and gate continuously here. The launch-readiness
    #    META-check stays standalone BY DESIGN — it spawns 11 sub-proofs itself; nesting it here would
    #    double-run the suite inside the suite. ──
    ("scripts/check_aidevobserver_session_benchmark.py", "check_aidevobserver_session_benchmark"),
    ("scripts/check_aidevobserver_local_registry_connector.py", "check_aidevobserver_local_registry_connector"),
    ("scripts/check_aidevobserver_operational_primitive_search.py", "check_aidevobserver_operational_primitive_search"),
    ("scripts/check_aidevobserver_implemented_primitives_consumption.py", "check_aidevobserver_implemented_primitives_consumption"),
    # ── QUICKSTART (the SaaS onboarding path): ONE command from checkout to working AIDevObserver — MCP
    #    merge (idempotent), hook via its own registrar, service start-if-down, OUTSIDE-IN verification,
    #    measured wall-clock receipt; dry-run proven mutation-free. Phase-0 exit gate of the SaaS roadmap
    #    (docs/codex/saas-north-star-roadmap.md). ──
    ("scripts/quickstart_aidevobserver.py", "quickstart_aidevobserver"),
    # ── WIRING LANGUAGE (the north-star output contract): the LLM emits a TINY relationship expression
    #    (A >> (B | C) >> D); the deterministic builder resolves identifiers (exact-id -> type-name ->
    #    standardized-language fold), validates joins by canonical edges, flags gaps in the Code-Factory
    #    gap-spec language, and PARTIALLY compiles every maximal working segment. serves_truth=false. ──
    ("scripts/wiring_language.py", "wiring_language"),
    # ── DEV-TASK PROMPT CORPUS (the session-emulation seed): 2,000+ deterministic realistic prompts —
    #    human Claude-Code asks (verb x subject x constraint) + agent loop tasks (Hermes/OpenClaw-style
    #    multi-step templates), persona-tagged, capability tokens per row, content-hash ids, byte-identical
    #    regeneration; --coverage runs the whole corpus through the REAL index for the partial-coverage
    #    receipt (the owner's 50%/80%-still-pays story, measured). ──
    ("scripts/generate_dev_task_prompt_corpus.py", "generate_dev_task_prompt_corpus"),
    # ── MULTI-PATH COVERAGE (the answer to "are vocabulary agents the only tool"): measures prompt coverage
    #    across lexical + semantic-blackbox + technical-register + facet paths and their UNION, at TWO levels
    #    (HIT = any relevant card; COMPLETENESS = fraction of capabilities connected). Every path reuses a
    #    proof-gated engine; union never loses to a single path. serves_truth=false. ──
    ("scripts/multi_path_coverage_bench.py", "multi_path_coverage_bench"),
    # ── COMPOSE + TOKEN BENCH (the answer to "reorder/reuse/piece together primitives WITHOUT token spend"):
    #    races the graph's compose zoo (clause-join baseline vs max-typed-joins edge_chain vs the REAL
    #    route composer) on chain-complete gold tasks — REUSE (pieces wired), REORDER (gold order + typed
    #    joins), TOKENS (0 llm calls; proxy-token bill of naive body-reading vs signatures vs deterministic).
    #    Options are read from the live graph, so a new compose row races automatically. serves_truth=false. ──
    ("scripts/compose_token_bench.py", "compose_token_bench"),
    # ── ENRICHMENT COVERAGE GATE ("make sure ALL primitives have multiple descriptors/keys/features/
    #    descriptions/embeddings"): card fields by full stream count; persisted feature records, blackbox
    #    embeddings and 3-register description embeddings by EXACT id-set comparison against the stores;
    #    derivability by deterministic stride probe. Gap records = candidate repair tickets; RUN mode
    #    ratchets (store coverage may never drop). serves_truth=false. ──
    ("scripts/primitive_enrichment_coverage.py", "primitive_enrichment_coverage"),
    # ── MULTI-FACET ENRICHMENT (the answer to "are primitives richly described enough to learn WHICH
    #    description/keyword/route retrieves best?"): lifts each primitive from 3 registers to DOZENS-TO-HUNDREDS
    #    of descriptions across 13 facet families (action/input/output/transform/problem/solution/keywords/
    #    operation/datatype/signature/use_case/composition_role/negative_contrast) x 3 registers, embeds each as a
    #    MULTIVECTOR store, then RACES the families (precision@k/MRR + efficiency=quality-per-stored-vector). The
    #    race says which surfaces to index at 5M scale (the Pareto frontier), not blind 300x storage. Self-test:
    #    mutation gate (a garbage facet retrieves worse) + determinism (descriptions+vectors byte-identical) +
    #    no-magic (family/register counts computed). candidate-only, serves_truth=false. ──
    ("scripts/primitive_facet_enrichment.py", "primitive_facet_enrichment"),
    # ── FACET COVERAGE RATCHET (make sure EVERY searchable primitive carries facet descriptions/embeddings in the
    #    multivector store): EXACT id-set comparison corpus vs the streaming store's covered_ids (full, never
    #    sampled) + per-facet-family coverage; RUN mode ratchets a floor in architecture/ (dist/ is gitignored) so
    #    overall + per-surface coverage may never drop. Mutation gate (a missing card drops coverage + is named) +
    #    ratchet gate + determinism. serves_truth=false. ──
    ("scripts/primitive_facet_coverage.py", "primitive_facet_coverage"),
    # ── SEMANTIC LINKER — RESOLVE step (capability plan -> verified primitives): parses a compact capability plan
    #    (graph IR), resolves each capability to the best primitive via the facet store, applies HARD blockers
    #    (policy/effect from DECLARED effects + type-fit) — retrieval probabilistic, ACCEPTANCE deterministic — and
    #    emits a lock + explicit RESIDUAL specs for misses + a structural token-savings projection. Self-test: the
    #    create-user plan end-to-end (5/5 bound when covered; network-decoy invalidated; miss->residual; determinism).
    #    Consumes primitive_semantic_abi_registry (Codex data); live tokens = semantic_linker_long_session_benchmark
    #    (Codex). serves_truth=false. ──
    ("scripts/semantic_linker_resolve.py", "semantic_linker_resolve"),
    # ── SEMANTIC LINKER — ASSEMBLE step (graph_apply): consumes a resolve result and deterministically WIRES the
    #    locked primitives by dataflow (picking the edge-matching producer per input), inserts a typed ADAPTER
    #    where declared edges don't chain (never a silent mismatch), emits a MOUNTABLE artifact (verified primitives
    #    mounted verbatim = the 0-token composition win), and carries RESIDUAL holes. Self-test: create-user
    #    (5 mounted / 0 adapter / 0 residual / deterministic_composition), a forced edge-mismatch -> 1 adapter, a
    #    miss -> residual hole, determinism. serves_truth=false. ──
    ("scripts/semantic_linker_assemble.py", "semantic_linker_assemble"),
    # ── SEMANTIC LINKER — MCP control plane: the SEVEN linker meta-tools over stdio (workspace_profile /
    #    primitive_search [Level-0 sketches over the facet store] / primitive_expand [progressive disclosure 1-3] /
    #    graph_solve [resolve] / graph_apply [assemble] / graph_verify [static gates] / candidate_promote
    #    [readiness, never flips serves_truth]). Small fixed tool set (never 10k primitives as 10k tools). Reuses
    #    _mcp_stdio + resolve + assemble; self-test exercises every tool OFFLINE through tools/call. serves_truth=false. ──
    ("scripts/semantic_linker_mcp_server.py", "semantic_linker_mcp_server"),
    # ── SEMANTIC LINKER — TOKEN BENCH (where does the linker REDUCE tokens?): a controlled COVERAGE SWEEP (0->100%)
    #    yields the savings CURVE + BREAK-EVEN (measured: create-user break-even ~40% coverage, 76% saved at full,
    #    deterministic-composition) + a per-task-family run on the real store (auth covered -> saves; web-CRUD not ->
    #    honest none). STRUCTURAL/resolved projection (deterministic floor) — NOT executed-verified reuse (that's the
    #    fabric execute->prove + long-session bench). Self-test: monotonic sweep + break-even + determinism. serves_truth=false. ──
    ("scripts/semantic_linker_token_bench.py", "semantic_linker_token_bench"),
    # ── MINT VERTICAL PACK (close a vertical's coverage gap with REAL primitives): each spec runs ast.parse + exec
    #    + a behavioral ORACLE; a card is minted verification_level='execution' ONLY if the oracle passes (working =
    #    oracle-passing, never a stub — the no-proxy discipline enforced with a mutation gate). Deterministic ids,
    #    candidate-only. Used to take the auth vertical 67%->100% by minting the request->OpenApiDocument parser the
    #    corpus lacked (reuse-first: validator+emitter already existed). serves_truth=false. ──
    ("scripts/mint_vertical_pack.py", "mint_vertical_pack"),
    # ── ML PIPELINE ZOO (Kaggle-thesis scaffold; multi-path law for ML): 9 stages (profile/task_infer/metric/split/
    #    preprocess/model/ensemble/threshold/submit), each a ZOO of interchangeable PATHS with typed task/metric
    #    compatibility + ML blocking variables + availability-gated learners; runs end-to-end on synthetic data via a
    #    deterministic baseline. enumerate_pipelines() = the candidate set to RACE (arms A-F). Add-a-path not a
    #    rewrite. serves_truth=false. ──
    ("scripts/ml_pipeline_zoo.py", "ml_pipeline_zoo"),
    # ── ML-KAGGLE PACK (mint the ML primitive families as REAL oracle-tested primitives): 44 deterministic ML
    #    primitives (metrics/splits/preprocess/encode/eda/ensemble/submission) with numpy bodies + strict oracles,
    #    minted via mint_vertical_pack (working=oracle-passing). Covers the ML domain so a Kaggle plan resolves +
    #    the A-F arms measure real savings. serves_truth=false, candidate-only. ──
    ("scripts/mint_ml_kaggle_pack.py", "mint_ml_kaggle_pack"),
    # ── LINKER SCORING ZOO (multi-method match/link, trainable custom weights, multiple paths): 15 scorers across
    #    11 families (exact/keyword/idf/word-freq/fuzzy/edit-distance/char-ngram/structural-NLP/phonetic/letter-metric/
    #    semantic) fused by a weight profile; 6 named PATHS + coordinate-ascent train_weights. The cheap
    #    model-independent scoring surface over a blocked shortlist (100M -> shortlist -> these + strong-embedder
    #    rerank). Add-a-scorer / add-a-path = one row. serves_truth=false. ──
    ("scripts/linker_scoring_zoo.py", "linker_scoring_zoo"),
    # ── SURFACE EMBEDDINGS (embed CODE + descriptions + components with SPECIALIZED models): 10 surfaces
    #    (code/code-signature/code-portions + title/blackbox/input/output/io-combined/problem/keywords) routed by
    #    KIND to a model portfolio — CODE surfaces to a code encoder (jina-code), TEXT surfaces to strong text
    #    models (BGE-large/EmbeddingGemma/GTE/…). surface x model RACE decides what to serve. Add-a-surface / add-a-
    #    model = one row. serves_truth=false. ──
    ("scripts/primitive_surface_embeddings.py", "primitive_surface_embeddings"),
    # ── USAGE LEDGER (the outcome graph): hash-chained SEARCHED/DOWNLOADED/IMPLEMENTED events capturing the query
    #    text + embedding MODEL + matched SURFACE + input-prompt digest per primitive; rolls up to per-primitive
    #    stats (counts/success-rate/top-queries/models/surfaces) + TRAINING PAIRS (successful implement -> labelled
    #    query->primitive) that train linker_scoring_zoo/the ranker + surface×model race. Tamper-evident. Strong
    #    feedback signal (only successful implements count). serves_truth=false. ──
    ("scripts/primitive_usage_ledger.py", "primitive_usage_ledger"),
    # ── STRONG-MODEL RERANK (handoff step 1): cheap model2vec RECALL over the shortlist -> strong-embedder
    #    (EmbeddingGemma/BGE/jina-code) rerank on the top-K (paid on K items, not the corpus). rerank_bench measures
    #    MRR before (recall order) vs after (reranked) per model. Wired as pipeline_path_graph rerank option
    #    'strong_embedder'. HONEST: no lift when recall is already near-ceiling; value appears on hard/near-duplicate
    #    workloads. Self-test proves it lifts when recall is imperfect. serves_truth=false. ──
    ("scripts/linker_rerank.py", "linker_rerank"),
    # ── MULTI-MODEL STORE LANES (build EVERY embedding model, do not prune): a per-model card-embedding store for
    #    each backend, resumable/tiered, coverage-reported — all models become live retrieval/rerank/RRF lanes,
    #    weighted by real-world usage, not lab-pruned. serves_truth=false. ──
    ("scripts/primitive_multi_model_store.py", "primitive_multi_model_store"),
    # ── MODEL PORTFOLIO (all TYPES, torch-free): dense + SPARSE (SPLADE/BM42/BM25/miniCOIL = term/keyword
    #    importance) + LATE-INTERACTION (ColBERT = connection) + CLASSIFICATION + INTENT (embedding-prototype,
    #    trainable = label importance) + image (CLIP). Every type a lane; fused by real-world-tuned weights. ──
    ("scripts/model_portfolio.py", "model_portfolio"),
    # ── ADAPTIVE VECTORIZATION (the waterfall): not every card gets vectors for everything — L0 (1 cheap vector,
    #    universal) → L1 registers → L2 facets → L3 strong-model → L4 multi-model+ColBERT, PROMOTED only when the
    #    usage ledger justifies it (retrieval/selection/success/ambiguity). Unused stay L0; promoted demote losslessly.
    #    ~99.7% fewer vectors than materializing everyone at max. serves_truth=false. ──
    ("scripts/adaptive_vectorization.py", "adaptive_vectorization"),
    # ── CLOUD PROVISIONING (self-service, key-based): plan/preflight/apply(guarded)/status for the serverless stack
    #    (S3 Vectors + Neon + Modal + Cloud Run + S3), as CLI AND MCP meta-tools. Billing-gated (OH_BILLING_ENABLED +
    #    confirm), presence-only creds (no secret leak), idempotent. The owner drives it after enabling billing. ──
    ("scripts/cloud_provisioning.py", "cloud_provisioning"),
    # ── ENVIRONMENT/REQUEST LEARNING (the MCP tool's flexible lane): any-technology workspace fingerprint +
    #    request ledger + usage-database-derived NON-DESTRUCTIVE rerank (reorder, never drop). Opt-in via
    #    OH_MCP_ADAPTIVE_LEARNING=1; OFF = bit-for-bit identity; failures fail OPEN. serves_truth=false. ──
    ("scripts/environment_request_learning.py", "environment_request_learning"),
    # ── CAPABILITY AGENT TOOL (the deterministic developer/agent tool beside the MCP tool): one allowlisted,
    #    key-gatable, receipt-backed JSON surface over the SAME engines — retrieval/compose/corpus + usage ledger +
    #    vectorization waterfall + billing-gated provisioning + environment profile. serves_truth=false. ──
    ("scripts/capability_agent_tool.py", "capability_agent_tool"),
    # ── PRIMITIVE ATTRIBUTE PLAN (uncapped column space): facets × styles × audiences × embedding-model slots ×
    #    hash/LSH profiles × lexical/NLP matcher families × per-field projections, ALL COMPUTED (extend = add a
    #    row; the 61-column multi-index was a pilot slice, not a ceiling). Floor >=500 attributes+descriptors per
    #    primitive RATCHETED; physical materialization delegated to the adaptive-vectorization waterfall. ──
    ("scripts/primitive_attribute_plan.py", "primitive_attribute_plan"),
    # ── CAPABILITY SAAS GATEWAY (the sellable hosted surface): signup->key via the embedded identity engine
    #    (hashes only), Bearer-authed remote MCP (the 7 retrieval tools over HTTP) + deterministic agent API
    #    (owner-only actions denied), invocation receipts in the billing_ledger shape, plan limits 429,
    #    billing_plane draft invoices (Stripe stays owner-gated). Proven in-container. serves_truth=false. ──
    ("scripts/capability_saas_gateway.py", "capability_saas_gateway"),
    # ── CAPABILITY SAAS BUNDLE (ship it): computed deploy manifest -> self-contained Fly.io bundle (code +
    #    governed corpus + Dockerfile/fly.toml/CI), token-GUARDED deploy + GitHub push with honest dry-runs
    #    (FLY_API_TOKEN / GITHUB_TOKEN absent -> exact plan, nothing faked). serves_truth=false. ──
    ("scripts/build_capability_saas_bundle.py", "build_capability_saas_bundle"),
    # ── TAEDRI REAL-USE EMULATOR (agent-runnable user emulation): API lifecycle journey (signup→session→
    #    dashboard→private primitives→include_mine→logs→usage→upgrade), MCP-protocol journey (initialize/
    #    tools-list/find_reuse FIRES/search — what `claude mcp add` speaks), REAL Chromium browser journey
    #    (Playwright; honest labeled skip when absent). Receipts per run; network faults = failed steps,
    #    never a dead harness. Verified 15/15 against taedri.fly.dev production. serves_truth=false. ──
    ("scripts/taedri_real_use_emulator.py", "taedri_real_use_emulator"),
    # ── TAEDRI EMULATOR IMAGE (the containerized USER MACHINE): stages a tiny deterministic docker context —
    #    version-matched Playwright python base (Chromium/Firefox/WebKit) + the Claude Code CLI (native
    #    installer; the cli journey does a real `claude mcp add/list/get/remove` round trip) + Xvfb/fluxbox/
    #    x11vnc/noVNC so START_VNC=1 gives a WATCHABLE desktop on :6080 with the browser journey HEADED.
    #    One `docker run` = the full real-use emulation against any deployment. serves_truth=false. ──
    ("scripts/build_taedri_emulator_image.py", "build_taedri_emulator_image"),
    # ── CORPORATE-RECORDS SCRAPING PACK (owner floor ≥50, RATCHETED): 55 curated governed primitives across
    #    13 source families — EDGAR (index/full-text/XBRL/DEF-14A/13F/Form-D), Companies House (officers/PSC/
    #    insolvency), OpenCorporates (license-gated), GLEIF LEI, state SoS (policy-tabled, ToS-gated), IRS 990,
    #    SAM.gov exclusions, UCC liens, RECAP/PACER (fee-budget gate), USPTO assignments, FinCEN BOI modeled as
    #    executable DENY, municipal licenses, cross-source spine (robots/ToS preflight, rate budgets, CDC
    #    watermarks, canonical-entity normalize, review-gated officer dedupe, provenance chains, signed CDC).
    #    canonical_id-minted, typed edges, no placeholders, candidate-only. serves_truth=false. ──
    ("scripts/corporate_records_scraping_primitive_pack.py", "corporate_records_scraping_primitive_pack"),
    # ── PRIMITIVE COMPOSITION LAYER (groups · frameworks · remixers · deterministic integrators): computed
    #    typed GROUPS (4 builder rows, by_family partitions losslessly), FRAMEWORK scaffolds (governed-scraping
    #    9-stage + entity-resolution 6-stage, instantiated per family with HONEST coverage gaps), a REMIX zoo
    #    (deterministic subset runnable: edge_vocabulary_align — THE chainability lever — + jurisdiction/cadence
    #    swaps, every variant lineage-carrying {parent, transform} + fresh canonical_id; llm seam declared not
    #    run), and DETERMINISTIC INTEGRATORS reusing primitive_runtime.compose_route (never a second composer):
    #    raw pack REFUSES (receipted — independently-minted edges never chain exactly), edge-aligned corpus
    #    compiles exact 2-step composites. All rows candidate-only. serves_truth=false. ──
    ("scripts/primitive_groups_frameworks_and_remixers.py", "primitive_groups_frameworks_and_remixers"),
    # ── PRIMITIVE NETWORKS + GRID SEARCH (the "grid of potential primitives"): a task = an ordered EDGE-TYPE
    #    chain; each step is a SLOT whose members are COMPUTED from the corpus (cards producing that edge +
    #    consuming the previous — new card joins its slot automatically); the GRID is the cartesian product,
    #    every path valid by construction (exact canonical edges, asserted). Deterministic grid search under a
    #    SCORER ZOO (proxy_context_tokens/blackbox_tokens/declared_cost runnable; execution_efficiency a declared
    #    seam) with coprime-strided sampling past the cap; NON-DESTRUCTIVE receipts (every path scored, per-scorer
    #    winners + Pareto front, losers preserved). Synthetic 12-path fixture proves the search finds the known
    #    winner AND a different scorer crowns a different path (ranking mutation gate). serves_truth=false. ──
    ("scripts/primitive_networks_and_grid_search.py", "primitive_networks_and_grid_search"),
    # ── PRIMITIVE DEPLOYMENT PROFILER (deps · substrate · K8s-vs-cloud-function · resource estimator): maps each
    #    primitive to an operation class → declared pip deps + runtime substrate (io/cpu/mem, gpu, stateful) +
    #    a base vCPU/memory envelope; a use-case rubric (records/day · freshness · latency SLA · concurrency)
    #    DECIDES the deployment medium and SIZES the envelope + a monthly compute cost band (reusing
    #    cloud_provisioning.plan for the full stack); network profiles critical-path the steps. The medium choice
    #    is a mutation gate (same primitive → different medium per use case). candidate-only. serves_truth=false. ──
    ("scripts/primitive_deployment_profiler.py", "primitive_deployment_profiler"),
    # ── PRIMITIVE SCALE + CONTAINMENT (a primitive spans atom→application): a 6-tier granularity ladder
    #    classifies by line+file counts; SMALL primitives inline their body, LARGE ones (module+) are governed
    #    SOURCE-TREE REFERENCES (handle+digest+counts+entrypoints+internal components — NEVER raw bytes, per the
    #    no-raw-bodies law); delivery rungs scale with size (a 100K-line K8s app = reference/deploy only, never
    #    prompt-inline or pip-import); and a large primitive is FRACTAL (external typed edges + internal
    #    sub-primitive decomposition → the composition layer recurses). Grounded on REAL measured monorepo
    #    subtrees (teleon/baltor src). candidate-only. serves_truth=false. ──
    ("scripts/primitive_scale_and_containment.py", "primitive_scale_and_containment"),
    # ── EDGE ALIGNMENT GATE (automates the SOUNDNESS half of gap 2.1 — cross-mint edge chaining): a
    #    deterministic screen (role: payload→payload only, so input-contract/receipt aliases that FABRICATE
    #    chains are rejected · ambiguity: an alias is single-valued · cycle/re-alias · self) + corpus
    #    enable-evidence (new exact chain-edges created, non-destructive). REPRODUCES the hand-verified
    #    4-accept/10-reject decision on this session's 14 proposed alignments (the verify-the-verifier mutation
    #    gate for the aligner), and asserts the SHIPPED alignment table passes its own role gate. Admits are
    #    candidates_for_review (semantic judgment still required), never auto-truth. serves_truth=false. ──
    ("scripts/edge_alignment_gate.py", "edge_alignment_gate"),
    # ── PRODUCER-EDGE INDEX (corpus-scale slot lookup, gap 2.4): one streaming pass → inverted
    #    producers[edge]→card_ids + consumers[edge]→card_ids, so a network slot is a hash lookup + set
    #    intersect instead of an O(N) scan. PROVEN equivalent to the linear scan for every network (a
    #    substitutable faster path; build_network(index=…) is bit-identical to the default); scales to 60k
    #    cards; surfaces the dangling edges (produced-never-consumed / consumed-never-produced) the aligner
    #    feeds on. serves_truth=false. ──
    ("scripts/producer_edge_index.py", "producer_edge_index"),
    # ── PROPOSE EDGE ALIGNMENTS (the PROPOSE half of the aligner, closing gap 2.1): generate candidate
    #    alignments from dangling edges (dead-end output → an edge-with-consumers of the same role + similar
    #    tokens), screen each through the soundness gate + corpus evidence, emit candidate_for_review rows a
    #    human promotes (proposing is NOT promoting). The token lane REDISCOVERS the lexically-similar shipped
    #    alignments (the Officer family) from the raw pack; the lexically-dissimilar entity family is honestly
    #    MISSED (the documented embedding-similarity_fn seam, proven pluggable). serves_truth=false. ──
    ("scripts/propose_edge_alignments.py", "propose_edge_alignments"),
    # ── ROBUST-LANE ROUTER / SCOREBOARD (gap 2.2 keystone): classifies each capability need into the strongest
    #    reuse lane — deterministic_compose (multi-hop exact chain, 0-token, model-independent) / package_import
    #    (single verified primitive) = ROBUST · partial_compose (a chain with one gap) · generate_tail (nothing
    #    produces it) — and reports the honest ROBUST FRACTION over a workload (the number the honest-ledger law
    #    demands before any "route more to robust lanes" claim; ~54% on the pack workload). Pure composition
    #    over producer_edge_index (reuse-first); a mutation gate proves the scoreboard MOVES when the corpus
    #    loses composability. serves_truth=false. ──
    ("scripts/robust_lane_router.py", "robust_lane_router"),
    # ── PRIMITIVE ATTESTATION (trust for the import/vendor lanes, gap 2.6): an in-toto v1 Statement whose
    #    subject digest = sha256(the ACTUAL body) + an SLSA predicate from formalize_card's fields, signed over
    #    a backend zoo (hmac_local default; ed25519/cosign declared seams). verify_attestation RECOMPUTES the
    #    digest from the shipped body (catches a tampered/stale vendored copy), checks signature + revocation +
    #    primitive_warranty freshness (reused). 4 injected defects — flipped body byte, revoked digest, corrupt
    #    signature, expired warranty — each force verified=False. serves_truth=false. ──
    ("scripts/primitive_attestation.py", "primitive_attestation"),
    # ── EXECUTION SCORER (fills the grid-search execution seam, gap 2.5): scores a path by measured EXECUTED
    #    INSTRUCTION COUNT — runs the member bodies on sample inputs under a line tracer. It is a REAL
    #    measurement (a quadratic path executes far more than a linear one) yet DETERMINISTIC (unlike wall-clock,
    #    so it obeys the scorer determinism law); abstains honestly on non-executable governance cards (coverage
    #    disclosed, never a fake 0); a raising body is a None non-measurement. Wired into the networks scorer zoo
    #    as OPT-IN (runnable_scorers(include_execution=True)) so the default 0-token grid stays byte-identical.
    #    serves_truth=false. ──
    ("scripts/execution_scorer.py", "execution_scorer"),
    # ── SUBTREE PARTITIONER (auto-decompose a large primitive, gap 3.3): partitions a large primitive's symbol
    #    graph (codegraph shape — functions/classes + call/import edges) into candidate sub-primitives + each
    #    one's typed CUT-EDGE interface (entry_points = called-from-outside = its API/inputs; external_deps =
    #    calls-out = its outputs). Partitioner zoo: by_module (deterministic O(n) default) + by_connectivity
    #    (union-find components); community-detection is a DECLARED seam (non-deterministic/resolution-limited,
    #    not run). cut_fraction reports decomposition cleanliness. candidate-only. serves_truth=false. ──
    ("scripts/primitive_subtree_partitioner.py", "primitive_subtree_partitioner"),
    # ── MICROSERVICE PACKAGER (deterministic composition → the deploy rung): emits a runnable microservice from
    #    a primitive's declared contract — a valid FastAPI (default) / Flask scaffold with the VERIFIED body
    #    MOUNTED verbatim (0-token composition, not regenerated), a typed POST /invoke (input_edge→output_edge)
    #    + /healthz, a Dockerfile + requirements.txt (deps/resources REUSED from the deployment profiler), and a
    #    service manifest. Spec-only primitives package honestly (body_mounted=false); novel multi-step wiring is
    #    a declared LLM seam. Deterministic (byte-identical). candidate-only. serves_truth=false. ──
    ("scripts/primitive_microservice_packager.py", "primitive_microservice_packager"),
    # ── COMPATIBILITY LATTICE (the contract-algebra first increment; external research §5.3): edge
    #    compatibility is a GRADED, DIRECTIONAL relation — IDENTICAL/FAMILY_COMPATIBLE/SAFE_STRUCTURAL/
    #    VERIFIED_ADAPTER authorize automatic execution, LOSSY_OR_PARTIAL is policy-gated, and the load-bearing
    #    invariant: name/token/embedding similarity caps at CLOSE_CANDIDATE (retrieval only, NEVER authorizes),
    #    an input-contract producer→payload consumer is INCOMPATIBLE, and the relation is NOT symmetric. Reuses
    #    edge_alignment_gate roles + the canonical alignment table (no parallel matcher). serves_truth=false. ──
    ("scripts/compatibility_lattice.py", "compatibility_lattice"),
    # ── PORTCONTRACT + ADAPTER DSL (contract algebra Phase 1; external review §5.1-5.5): compatibility over
    #    STRUCTURE not names — directional WIDTH SUBTYPING (a producer satisfies a consumer iff it guarantees
    #    every required field with a widening-compatible type + matching unit; int→float yes, float→int no; a
    #    unit mismatch is INCOMPATIBLE; a missing required field is NEVER defaulted) + a restricted PROVED
    #    adapter DSL (rename/widen/unit_convert = total_lossless → auto-authorize; project = total_lossy → opt-in;
    #    enum_map = partial_guarded → typed error on an unmapped value, never fabricated). serves_truth=false. ──
    ("scripts/edge_contract_and_adapters.py", "edge_contract_and_adapters"),
    # ── CAPABILITY IMPLEMENTATION ZOO (review §4, the "essential" object-model split): a capability is a
    #    FAMILY holding an IMMUTABLE, append-only set of implementations (never one mutable current-code row).
    #    Ranking is a non-destructive query-time VIEW — Pareto non-dominance keeps incomparable variants (faster
    #    vs leaner) both alive, a diversity archive preserves novel delivery/license/runtime approaches even when
    #    numerically dominated, and revoked != deleted. Optimization changes RANKING, not history. serves_truth=false. ──
    ("scripts/capability_implementation_zoo.py", "capability_implementation_zoo"),
    # ── COMPATIBILITY BENCHMARK (verify-the-verifier for the whole compatibility system, review §6.1): a
    #    labeled ADVERSARIAL held-out set (same-name/different-unit, same-shape/different-type, missing-required,
    #    semantically-related-not-executable, input-contract→payload, optional-vs-required, width-subtype). Proves
    #    the safety invariant — the CONTRACT-AWARE classifier has 0 false auto-authorizes while the NAME-ONLY one
    #    has ≥1 (the same-name/different-unit trap), i.e. names retrieve but cannot authorize — recall 1.0 on the
    #    safe subset. serves_truth=false. ──
    ("scripts/compatibility_benchmark.py", "compatibility_benchmark"),
    # ── OPEN PRIMITIVE FORMAT (OPF v0 — a candidate OPEN standard + a stable extensible query interface): a
    #    portable validated record for a primitive with MULTIPLE weighted DIRECTIONAL ports (consumes[]/
    #    produces[], not one input/output), MULTIPLE tunable embeddings (pluggable model/dim/space descriptors),
    #    multiple search systems, evidence refs, the capability/implementation split, and a named compatibility
    #    authority (an OPF edge RETRIEVES, it does not authorize). PLUS OPFQuery — a query-method ZOO any
    #    extension (Teleon, future systems) calls WITHOUT the internal card shape; adding a method/embedding/
    #    search-system is one row. The substrate is queryable by downstream products (portfolio law). serves_truth=false. ──
    ("scripts/open_primitive_format.py", "open_primitive_format"),
    # ── OPEN ATTRIBUTE MODEL (uncapped, typed, extensible attributes on ANY subject kind): a subject is a KIND
    #    (code_function/docker_image/cloud_function/service/tool/dataset/model/workflow/…) + an UNCAPPED bag of
    #    typed Attributes (number/quantity+unit/rating/categorical/ordinal/tag_set/text/embedding/reference/
    #    temporal/distribution/…). Types + kinds are DATA in extensible registries (add = one row, no migration);
    #    OPEN-WORLD validation (an unknown type is accepted + flagged opaque, register→queryable, never dropped);
    #    500 attributes attach uncapped; arbitrary attributes are queryable via a filter zoo; every attribute
    #    carries provenance + the candidate/truth boundary. "Infinite flexibility" as a registry, not hardcoded
    #    columns. serves_truth=false. ──
    ("scripts/open_attribute_model.py", "open_attribute_model"),
    # ── ADAPTIVE RETRIEVAL STRATEGY (self-tuning distance/blocking PER DATA SHAPE; info + search theory): a
    #    DISTANCE-MEASURE zoo (exact/levenshtein/jaccard/ngram/numeric/prefix) + a BLOCKING-KEY zoo (extend = one
    #    row); a SELF-TUNER races the measures on labeled pairs FROM THE DATA AT HAND and picks the champion
    #    NON-DESTRUCTIVELY — numeric data → numeric distance, typos → edit distance, token sets → Jaccard, all by
    #    measured separation, not a fixed rule. Information theory (normalized entropy + pair-reduction, penalizing
    #    singletons) selects blocking keys so a low-information key is never chosen. "Not all solutions fit every
    #    data shape", executable. serves_truth=false. ──
    ("scripts/adaptive_retrieval_strategy.py", "adaptive_retrieval_strategy"),
    # ── PRIMITIVE DOMAIN PARTITIONER (category/domain/niche shards): deterministic table-driven taxonomy
    #    (extend = one row), LOSSLESS conserving per-domain shards + per-domain indexes (micro-domains fold into
    #    the always-searched general index — df-cap guard), NON-DESTRUCTIVE query router (low confidence -> ALL),
    #    routed-vs-monolith equivalence receipts. Routed lane is CANDIDATE-ONLY until its receipt clears the
    #    recovery floor (real-corpus receipt currently ~0.23 — cross-partition score fusion needs RRF; the
    #    monolithic lane keeps serving meanwhile). serves_truth=false. ──
    ("scripts/primitive_domain_partitioner.py", "primitive_domain_partitioner"),
    # ── ESOTERIC QUERY BENCH: a ZOO of 12 deterministic hash-seeded corruption probes (keyboard typo /
    #    rotation / truncation / verbose padding / code-speak / leet / vowel-drop / stopword-drop / stutter /
    #    sms / noise-char) raced over lexical + stored-dense + fusion on a known-item harness — degradation
    #    attributable per corruption, receipts byte-identical. serves_truth=false. ──
    ("scripts/esoteric_query_bench.py", "esoteric_query_bench"),
    # ── SAAS REQUIREMENTS BENCH: every requirement of building a SaaS as a dev-task query (suite = DATA,
    #    the gold-set seed), VERIFIED hits only (expected concept token in a top-k card), independent
    #    retrieval per path incl. the stored 3-register lane, per-category rates + named corpus-gap misses.
    #    serves_truth=false. ──
    ("scripts/saas_requirements_bench.py", "saas_requirements_bench"),
    # ── PATH ROUTER ZOO (router methodologies): query -> config per QUERY CLASS (the graph's own analyze
    #    stage) — global champion / always-union baseline / type rules / difficulty gate / LEARNED per-class
    #    champion table (trained by the existing racer, persisted, self-healing). Raced end-to-end; routing
    #    must earn its complexity over the single champion. serves_truth=false. ──
    ("scripts/path_router_zoo.py", "path_router_zoo"),
    # ── WORKLOAD TOKEN SIMULATION: a deterministic simulated day of traffic (clean/typo/verbose/truncated/
    #    repeat, esoteric transforms reused) replayed under token-spend POLICIES (deterministic-only /
    #    always-LLM / difficulty-gated / cache-reuse) — the spend-vs-quality frontier as a byte-stable
    #    receipt; the LLM is a metered stub (proxy-tokens, never a billing claim). serves_truth=false. ──
    ("scripts/workload_token_simulation.py", "workload_token_simulation"),
    # ── STARTUP FLEET SIMULATION (the 100-startups question): fleet token spend building SaaS products with
    #    OUR system (measured verified hits cost 0; misses generated ONCE under the flywheel and accreted as
    #    candidates) vs PURE LLM generation (everything regenerated per startup). Grounded by
    #    saas_requirements_bench.measure against the real corpus; generation size is a SWEEP (a band, never
    #    one magic number); exact once-paid accounting proven in the self-test. serves_truth=false. ──
    ("scripts/startup_fleet_simulation.py", "startup_fleet_simulation"),
    # ── REAL GENERATION TOKEN BENCH: actual Ollama prompt_eval_count/eval_count (local daemon or Ollama
    #    Cloud GLM/Kimi via :cloud + OLLAMA_API_KEY) over a deterministic requirement sample — PURE
    #    generation vs OUR system (verified hits cost 0; only corpus-gap misses generate). Hermetic
    #    self-test via injected stub transport; failures recorded, never fabricated. serves_truth=false. ──
    ("scripts/real_generation_token_bench.py", "real_generation_token_bench"),
    # ── BUILD SCENARIO CORPUS (tens of thousands of build-anything asks): a deterministic strided walk of
    #    domains x artifacts x capabilities x stacks x phrasings, each row with specific expected tokens;
    #    verified coverage sweep over the real corpus (fast lanes); misses = gap-mining leads at scale.
    #    serves_truth=false. ──
    ("scripts/build_scenario_corpus.py", "build_scenario_corpus"),
    # ── DEV SESSION SIMULATION (real back-and-forth, not single prompts): session archetypes (ask/refine/
    #    bug/test/REMIX/UI-polish) replayed under the harness-mode zoo — pure-LLM context compounding vs the
    #    harness serving covered turns for 0 via retrieve/compose/cache and escalating compactly; per-turn
    #    tool traces persisted as developer examples; REAL multi-turn Ollama mode with measured growing
    #    prompt_eval_count. serves_truth=false. ──
    ("scripts/dev_session_simulation.py", "dev_session_simulation"),
    # ── MINT GAP PRIMITIVES (the flywheel made runnable): thousands of candidate cards minted from the
    #    capability x artifact axes (canonical-id law; staged file only, verified corpus untouched) with a
    #    MEASURED base-vs-minted coverage lift proof as admission evidence. Generation is not promotion —
    #    the factory funnel governs. serves_truth=false. ──
    ("scripts/mint_gap_primitives.py", "mint_gap_primitives"),
    # ── MINT IDEA PRIMITIVES: deterministic axis-strided idea-primitive candidates across computational-work
    #    x CS-category x SWE-category x knowledge-domain (incl. geography/textbook) x system/index x
    #    problem->solution (full product 35.7M, strided to --target). Canonical ids, CamelCase edges,
    #    substance-validated, candidate/serves_truth=false; write refuses verified corpus files. Every mint is
    #    scored by the usefulness gate as a NON-DESTRUCTIVE routing signal (weak/placeholder route to
    #    enrichment; NOTHING discarded). serves_truth=false. ──
    ("scripts/mint_idea_primitives.py", "mint_idea_primitives"),
    # ── PRIMITIVE GRID REMIXER: the exhaustive combinatorial generator — 1,848 COMPUTED software operations
    #    (verb x object) x data-type x infra-tool x latency x software-tool x hardware x entity-type = a
    #    77.4-BILLION-point grid, strided (coprime full-period walk) to --target. Canonical ids, CamelCase
    #    edges, candidate/serves_truth=false; usefulness gate scores as a NON-DESTRUCTIVE routing signal. ──
    ("scripts/primitive_grid_remixer.py", "primitive_grid_remixer"),
    # ── PERSONA PRIMITIVE EXPLORER: take on every worker's persona (role x industry x personality x company x
    #    country x era = 9.5M personas) and ideate what/why + a primitive PORTFOLIO (primary + ALTERNATIVES +
    #    infra + libraries); the EXPLORE arm ideates NOVEL primitives + CHAINS via our lanes. Reuses the grid's
    #    computed vocab; usefulness gate = NON-DESTRUCTIVE routing. serves_truth=false. ──
    ("scripts/persona_primitive_explorer.py", "persona_primitive_explorer"),
    # ── PRIMITIVE EXPANSION LOOP: grow OUTWARD — send a primitive to an LLM, ask its use cases / inputs /
    #    outputs / industries + NEIGHBOR primitives + ESOTERIC variants; neighbors become the next BFS
    #    frontier; deterministic esoteric seeding of the rare frontier. Cloud lanes only (NEVER local gemma4);
    #    failures recorded, never faked; candidate/serves_truth=false. ──
    ("scripts/primitive_expansion_loop.py", "primitive_expansion_loop"),
    # ── OPENWEBUI CDP BRIDGE: call the hosted Gemma-4 lane THROUGH the logged-in Chrome (CDP + in-page
    #    fetch) to bypass Cloudflare; pure-stdlib websocket client; never local gemma4. serves_truth=false. ──
    ("scripts/openwebui_cdp_bridge.py", "openwebui_cdp_bridge"),
    # ── LAYERED PRIMITIVE EXPANSION: recursive L1(ways)->L2(sub-ways)->L3(code template) fan-out; each leaf
    #    a primitive with a code-template basis; deterministic job-description + lifecycle seeds; projection
    #    reaches 50-100M. Cloud lanes only (never local gemma4). serves_truth=false. ──
    ("scripts/layered_primitive_expansion.py", "layered_primitive_expansion"),
    # ── PRIMITIVE CENSUS: progress toward the 40M-primitive goal — counts every pool, categorizes,
    #    states the gap + the generator capacity (grid 77.4B) that makes the goal minting-time-bounded. ──
    ("scripts/primitive_census.py", "primitive_census"),
    # ── PRIMITIVE DATABASE: load EVERY pool into a queryable SQLite FTS5 database (streamed, deduped,
    #    full-text searchable); scales to tens of millions; Postgres/pgvector swap config-only. serves_truth=false. ──
    ("scripts/primitive_database.py", "primitive_database"),
    # ── PRIMITIVE VERIFICATION PIPELINE: tier every stored primitive (execution/source/structural/candidate)
    #    at deterministic speed -> a MEASURED verified count, scalable to 20M without an LLM per card. ──
    ("scripts/primitive_verification_pipeline.py", "primitive_verification_pipeline"),
    # ── PRIMITIVE SEMANTIC INDEX: model2vec memmap matrix over the DB primitives; chunked-cosine intent
    #    search; scales to tens of millions on disk; pgvector/faiss swap config-only. serves_truth=false. ──
    ("scripts/primitive_semantic_index.py", "primitive_semantic_index"),
    # ── PRIMITIVE MULTI-INDEX: numerous attributes per primitive (purpose/solution/input/output/domain/
    #    tools/...) each with a semantic index + small/large MinHash-LSH blocking keys; block/cluster/search
    #    across every attribute at two granularities. Deterministic, scales to 20M. serves_truth=false. ──
    ("scripts/primitive_multi_index.py", "primitive_multi_index"),
    # ── PRIMITIVE SYSTEM CATALOG RUN: the owner's autonomous catalog-run spec as a DETERMINISTIC generator —
    #    full artifacts/{RUN_ID}/ tree (4 catalogs, 3 matrices, 30 schema objects x 6 formats, tool registry,
    #    20 playbooks, docs, diagrams, code+tests, coverage/gaps/final reports). Byte-identical re-runs,
    #    mutation-gated validation, candidate-only. serves_truth=false. ──
    ("scripts/primitive_system_catalog_run.py", "primitive_system_catalog_run"),
    # ── REAL BUILDOUT A/B HARNESS: same buildout prompt -> BARE vs REGISTRY-ASSISTED on the big cloud lanes
    #    (GLM/Kimi/CDP-Gemma; local gemma4 REFUSED), real usage-token accounting, sandboxed compile+pytest,
    #    CROSS-TESTED implementations (lane A's tests on lane B's code). The runtime-truth complement to the
    #    proxy session benchmark. serves_truth=false. ──
    ("scripts/real_buildout_ab_harness.py", "real_buildout_ab_harness"),
    # ── STRING STANDARDIZATION PRIMITIVES: the owner's data-loading/standardization playbook as 16 atomic
    #    oracle-tested pure functions + 4 COMPOSITES-OF-PRIMITIVES (declared atom plans) — addresses, person
    #    names, company names; raw never overwritten; match keys aggressive, display lossless; dictionaries
    #    versioned data. Feeds the A/B harness exec corpus + the OFAC name-matching wedge. ──
    ("scripts/string_standardization_primitives.py", "string_standardization_primitives"),
    # ── SCHEMA.ORG PRIMITIVE FOUNDRY: every schema.org property ("column") x the owner's 8-aspect question
    #    grid (use case/transformation/validation/comparison/storage/format/display/indexing) + per-type
    #    records systems + per-branch pipeline systems; SHARED typed-edge vocabulary (chainability lever);
    #    executable cross-links to the standardization pack. Deterministic; candidate-only. ──
    ("scripts/schema_org_primitive_foundry.py", "schema_org_primitive_foundry"),
    # ── UI DESIGN PRIMITIVES: the LLM outputs hex codes + labels (<60 tokens); DETERMINISTIC workers build
    #    shade scales, dark theme, type scale, css variables/components/layout grid, preview page, and a
    #    REAL WCAG contrast gate (mutation-gated). The descent shape applied to UI/design. ──
    ("scripts/ui_design_primitives.py", "ui_design_primitives"),
    # ── STRING OPERATIONS CATALOG MINTER: the owner's 1,000-operation catalog (50 categories x 20) minted
    #    REUSE-FIRST into 1,050 candidates — executable links to the standardization/UI packs, repo
    #    capabilities (LSH/embeddings/FTS) marked, typed per-category edges so candidates chain. ──
    ("scripts/string_operations_catalog_minter.py", "string_operations_catalog_minter"),
    # ── PARTY NAME PRIMITIVES: a name field is NEVER assumed to be one human — party classification
    #    (person/group/company/estate/trust/dba/care-of/role/placeholder), name-expression parsing, SAFE
    #    expansion ('James and Jane Doe' -> inferred surname MARKED; spouse names NEVER invented; family
    #    groups/estates/trusts are entities, not people), particle-aware strict+relaxed keys. Golden-set
    #    oracle from the owner spec. ──
    ("scripts/party_name_primitives.py", "party_name_primitives"),
    # ── PRIMITIVE SETTINGS CONTROL PLANE: deterministic customizers (validated settings -> configured
    #    variants), remixers (grid/neighbors), the TEST-FEEDBACK tuner (lossless ledger), the LLM
    #    short-settings lane (clamp/reject), the ratcheting champion MANAGER, and BAKED VARIANTS (hot
    #    settings frozen into named primitives at ~1 plan token — the token-economics counterpoint). ──
    ("scripts/primitive_settings_control_plane.py", "primitive_settings_control_plane"),
    # ── DUMMY DATA DETECTION: fictional/superhero names, placeholder legal names, 555-01xx fictional phones,
    #    repeating/sequential digits, reserved/disposable email domains, gateway test cards (REAL Luhn),
    #    famous dummy SSNs, placeholder dates + the composite likelihood RATER (routes to review, never
    #    deletes). ──
    ("scripts/dummy_data_detection_primitives.py", "dummy_data_detection_primitives"),
    # ── EXECUTABLE PACK POOL SYNC: every pack's cards -> the executable_packs POOL -> the database ->
    #    the multi-index (the owner's 'are these in the database?' wire; a new pack = one registry row). ──
    ("scripts/executable_pack_pool_sync.py", "executable_pack_pool_sync"),
    # ── PRIMITIVE CHAIN CATALOG: 197 basic ops x 12 families (string/text/vector/numeric/temporal/
    #    collection/categorical/graph/hash/geo/type-inference/dirty-numeric) + 27 package-wrap candidates
    #    (integrate-never-rebuild) + 26 canonical CHAINS in the plan dialect for cleansing/matching/
    #    modeling/representation/user-management. ──
    ("scripts/primitive_chain_catalog.py", "primitive_chain_catalog"),
    # ── PRIMITIVE RECIPE TEMPLATES: formulas with typed SLOTS filled by binding-table LOOKUP + params
    #    clamped by schema -> plans -> the deterministic builder -> verified runs (recipe->plan->code, all
    #    deterministic; recipes compose; record formulas map per-column). END-TO-END proven on real pack
    #    primitives at 0 LLM tokens. ──
    ("scripts/primitive_recipe_templates.py", "primitive_recipe_templates"),
    # ── QUANTITY/MONEY PRIMITIVES: the '5 ft' + '$1.2M' problems — unit aliases -> UCUM -> Decimal SI;
    #    imperial compounds (5'10"); ranges/approximations kept as structure; money with currency inference
    #    FLAGGED and no silent FX. Self-contained cards from day one. ──
    ("scripts/quantity_money_primitives.py", "quantity_money_primitives"),
    # ── SCALAR STANDARDIZATION KERNEL: the BASE ABSTRACTION under lists/arrays/matrices — the type ROUTER
    #    (infer_scalar_type, field-hint-driven) + the dirty-scalar parsers that had no home (null-kinds/
    #    boolean/integer-with-identifier-preserve/locale-decimal/percent-kinds) + the one standardized-scalar
    #    ENVELOPE (raw!=cleaned!=canonical!=display!=match, match_key so equal-meaning scalars collide).
    #    Composes the quantity/money/string packs; re-defines no unit/currency table (law §6). ──
    ("scripts/scalar_standardization_primitives.py", "scalar_standardization_primitives"),
    # ── STANDARDS + ENRICHMENT REGISTRY: 17 reference systems (ISO/UCUM/QUDT/NAICS/SOC/GEOID/tz) ->
    #    conformity candidates; 17 governed enrichment providers (Census/OSM/OurAirports/ADI/NLCD/...) with
    #    coverage/cost/license metadata; the owner's TOP-50 platform primitives ranked with reuse-first
    #    links (12 already executable). ──
    ("scripts/standards_enrichment_registry_minter.py", "standards_enrichment_registry_minter"),
    # ── CROSS-TABLE DISCOVERY: explore tables/columns, discover+test keys (uniqueness,
    #    inclusion-dependency FK detection, composite search), rank join candidates, SHAPE keys
    #    for merges (recipe zoo; lift proven 0.0->0.8 on the 007-vs-7 fixture), fan-out warnings. ──
    ("scripts/cross_table_discovery_primitives.py", "cross_table_discovery_primitives"),
    # ── TEMPORAL / RETROACTIVE CDC: snapshot diffs -> reconstructed change events (honest
    #    snapshot-window precision) -> cross-source timelines -> flip-flops, impossible transitions,
    #    timestamp inconsistencies, gaps, cross-source conflicts. Evidence, never autocorrect. ──
    ("scripts/temporal_cdc_primitives.py", "temporal_cdc_primitives"),
    # ── FEATURE + COMPARISON LAYER: shape features, cross-column constructions, the
    #    contradiction table, comparison vectors, hybrid scores (HARD RULES DOMINATE), group/
    #    window stats, robust outliers (IQR/MAD/group-contextual/rare-category). ──
    ("scripts/feature_comparison_primitives.py", "feature_comparison_primitives"),
    # ── SIMILARITY/TYPO ALGORITHMS: literature-oracle edit distances, QWERTY keyboard-distance
    #    typo classification, Dice/Jaccard/SimHash, LSH near-dup buckets, corporate folds. ──
    ("scripts/similarity_typo_primitives.py", "similarity_typo_primitives"),
    # ── MATCHING SCORECARD (deterministic core / tunable shell): TF evidence, Fellegi-Sunter
    #    m/u weights, hard-rule-dominant scorecards, cost-based threshold sweeps, calibration,
    #    blocking metrics — versioned configs, never silent. ──
    ("scripts/matching_scorecard_primitives.py", "matching_scorecard_primitives"),
    # ── FORMAL-PRIMITIVE-PACKAGE CONTRACT: the single source that turns a bare card into a formal package
    #    (verifier link, permission manifest from a deterministic code-safety scan, determinism budget D0..D4,
    #    risk tier, content-addressed provenance, 5-stage lifecycle=candidate, governance retrieval tags that
    #    feed the multi-index). Additive+lossless. Grounded in Formal Skill / SkVM / SWE-Skills-Bench. ──
    ("scripts/primitive_package_contract.py", "primitive_package_contract"),
    # ── SECURITY GATE (generated code is untrusted): INPUT+CODE gate — AST policy (banned imports/calls),
    #    secrets + canary scan, size cap, optional Bandit/Semgrep — pass|fail|quarantine. The hard gate
    #    before a primitive may serve truth. All 141 live cards pass. OWASP LLM Top-10 / Skill-Inject. ──
    ("scripts/primitive_security_gate.py", "primitive_security_gate"),
    # ── PRIMITIVE LIFECYCLE + PROVENANCE + TRUTH-SERVING POLICY: the 5-stage promotion state machine
    #    (candidate->validated->certified->production->deprecated/quarantined), every transition receipt-gated,
    #    security-quarantine fail-safe, SLSA provenance, and the "can serve truth?" policy (production + D0/D1/D2
    #    + security + benchmark + verifier + provenance). Pool audit: 0 truth-serving violations. ──
    ("scripts/primitive_lifecycle.py", "primitive_lifecycle"),
    # ── BENCHMARK TAXONOMY (marginal utility, not skill count): correctness + determinism (semantic entropy,
    #    replay) + amortized economics (break-even N-true incl. validation/security/review, token-reduction,
    #    determinism advantage) + latency + security status. Deterministic side measured; baseline labelled
    #    estimate. Scalar kernel: entropy 0, 1200x. Schema schemas/benchmark_result.schema.json. ──
    ("scripts/primitive_benchmark_taxonomy.py", "primitive_benchmark_taxonomy"),
    # ── BEHAVIOR SIGNATURES + DEDUPE/SHADOW REPORT: behavioral identity (names lie, embeddings drift, source
    #    hashes churn — hash the input->output pairs on canonical fixtures) + source/normalized-AST/io
    #    signatures -> duplicate & shadow clusters (report-only, never deletes). The dedupe substrate before
    #    141 cards becomes millions. 0 exact duplicates today. ──
    ("scripts/primitive_behavior_signature.py", "primitive_behavior_signature"),
    # ── ENRICHMENT PRIMITIVE CATALOG (the external-tool class): reference-data/authoritative-lookup
    #    primitives (USPS/Census-Geocoder/ACS/RUCC/SVI/OSM/NWS/FEMA/GLEIF/NPI/SAM/OFAC/VIN/NDC/RxNorm/PubChem)
    #    as TYPED/VERSIONED/PERMISSIONED external_tool primitives (D2_bounded_external, network-egress, review-
    #    required) with input/output schema + provenance + failure modes + fallbacks. Census!=USPS; OFAC=
    #    candidate/review only. Data seam: a new source = one row. ──
    ("scripts/enrichment_primitive_catalog.py", "enrichment_primitive_catalog"),
    # ── STANDARDS FACTORY ("standards ARE primitive factories"): each standard × a fixed op-set (parse/
    #    validate/map/conform/crosswalk/version-resolve/ack/error) -> multi-axis-addressable primitive SPECS.
    #    33 standards -> 173 specs (candidate, deterministic D0/D1, needs_executor). Multi-axis: persona ×
    #    industry × geography × standard × datatype × process. Sensitive families never make final adverse. ──
    ("scripts/standards_factory_minter.py", "standards_factory_minter"),
    # ── API INTERFACE PRIMITIVES (endpoints are a primitive factory): OFFLINE OpenAPI-spec importer -> one
    #    governed interface primitive + sub-primitive bundle (request-builder/validator/normalizer/error-
    #    mapper/side-effect-gate) per operation. Side effects inferred from HTTP method, retry-safety from
    #    idempotency, money paths high-risk. External_tool/D2/network-egress. Fourth primitive class. ──
    ("scripts/import_openapi_as_api_primitives.py", "import_openapi_as_api_primitives"),
    # ── PROCESS-STAGE FACTORY (the process IS a primitive factory): the standard ~18-stage lifecycle
    #    (research->source->access->ingest->profile->validate->standardize->ETL->label->split->feature->train->
    #    evaluate->package->deploy->monitor->drift->audit; CRISP-DM/TDSP/TFX) as governed ProcessStep primitives
    #    (executor+validator+verifier+receipt+lineage, typed by artifact), + 49 artifact types + 6 templates.
    #    Computed answer: 12/18 stages high/very-high standardizable scaffold; policy/domain = the delta. ──
    ("scripts/process_stage_factory.py", "process_stage_factory"),
    # ── HY3 OVERNIGHT FLYWHEEL (free multi-LLM, STOP-gated): rotates the free OpenRouter lanes (Hy3 first,
    #    then qwen3-coder/qwen3-next/nemotron-3/gpt-oss — all $0) x tasks (spec_executor/primitive_gen/
    #    raw_digest) to draft executors for our candidate SPECS + mint primitives, EACH security-gated +
    #    candidate-only, append-only pool + receipts. Offline self-test (stub LLM); real run verified $0. ──
    ("scripts/hy3_overnight_flywheel.py", "hy3_overnight_flywheel"),
    # ── SPEC->EXECUTOR SYNTHESIZER (task #26, the promotion-loop closer): Hy3 drafts a runnable executor + golden
    #    fixtures for a needs_executor spec -> security gate -> ISOLATED sandbox exec against fixtures -> determinism
    #    check -> promote candidate->validated->certified only on pass (dangerous quarantined). candidate-only. ──
    ("scripts/spec_to_executor_synthesizer.py", "spec_to_executor_synthesizer"),
    # ── WEAK-CAPABILITY closer: 36 concrete deterministic specs for the MEASURED-weakest capabilities (0.0
    #    hit-rate) -> real Hy3 synthesizer -> fixture-proven working primitives. candidate-only. ──
    ("scripts/weak_capability_primitive_closer.py", "weak_capability_primitive_closer"),
    # ── REAL-WORLD/LEGACY situation generator: 11,616-point grid (family x tech-system x non-ideal SITUATION:
    #    legacy-version/vendor-quirk/broken-encoding/malformed/migration/deprecated-api/partial-failure/injection) ->
    #    Hy3 synthesizer -> fixture-proven primitives for messy reality (not just the happy path). candidate-only. ──
    ("scripts/real_world_situation_primitive_specs.py", "real_world_situation_primitive_specs"),
    # ── PRIMITIVE PLACEMENT (the last mile): AST-verified strategy zoo (import_and_call/vendored_module/
    #    direct_insertion/class_method/legacy_codemod) places certified primitives into new/existing/legacy code
    #    -> verified code reused at 0 tokens; diffed, candidate-only, never executed. ──
    ("scripts/primitive_placement.py", "primitive_placement"),
    # ── DOCUMENT-EXTRACTION OCR PACK: registers the open VLM OCR pipeline (pdf->image->layout->crop->GLM-OCR->
    #    assemble) as a 5-node typed primitive GRAPH whose edges chain end-to-end, plus the cited make-it-cheap
    #    descent receipt ($0.04/1000pp, 100-250x cheaper than hosted OCR). candidate-only; the wedge component. ──
    ("scripts/document_extraction_ocr_pack.py", "document_extraction_ocr_pack"),
    # ── ESOTERIC PLATFORM PRIMITIVE PACK: very-specific, platform/technology-bound DETERMINISTIC primitives
    #    (EBCDIC/COMP-3 mainframe, protobuf varint+zigzag, ASN.1 DER length, DICOM tag, HL7 MSH, FIX, RFC5952
    #    IPv6, base32/TOTP, CRC-32, SemVer precedence) with REAL reference impls + oracle fixtures the self-test
    #    runs. Executor body IS inspect.getsource(fn) (single source). Negative-space, candidate-only. ──
    ("scripts/esoteric_platform_primitive_pack.py", "esoteric_platform_primitive_pack"),
    # ── ESOTERIC PLATFORM PRIMITIVE PACK 2: 16 more real oracle-tested platform primitives (IBAN mod-97, ISBN-13,
    #    ABA routing, EAN-13, Luhn-gen, base58/base64url, IPv4/CIDR, Roman, ISO-8601 duration, RFC-6901 JSON
    #    pointer, hex color, VIN, NPI [healthcare-admin], IMEI). 47 oracle fixtures; executor body = getsource. ──
    ("scripts/esoteric_platform_primitive_pack_2.py", "esoteric_platform_primitive_pack_2"),
    # ── DOCUMENT-INGESTION FACTORY SPEC: the durable backbone (layers 0-35) that wraps the OCR pack (layers
    #    7-17) into a source-acquisition->typed-candidate-primitive supply chain — two-stage metadata
    #    classification, 3 provenance receipt schemas, 6 primitive families, and the OCR promotion gates
    #    (no_promotion_from_ocr_alone). OCR output = candidate evidence, never truth. candidate-only. ──
    ("scripts/document_ingestion_factory_spec.py", "document_ingestion_factory_spec"),
    # ── APP-DIGESTION PRIMITIVE-GENERATION PACK: treats app/website cloner tools as a primitive-GENERATION
    #    engine (recon->tokens->component specs->interaction->build understanding->rebuild plan->candidates->QA).
    #    Generates UI/UX families (design-token/component/layout/interaction/a11y/framework/rebuild) + the
    #    digestion prompts as reusable Action primitives; useful-by-construction (two-axis lift screen); the
    #    cross-source generation map; guardrails (no impersonation, serve built-out surfaces). candidate-only. ──
    ("scripts/app_digestion_primitive_generation_pack.py", "app_digestion_primitive_generation_pack"),
    # ── HARNESS BAKEOFF SPEC: the harness is a hidden runtime — benchmark model x harness x runtime x task_family
    #    (3360 cells), unit = executor_certified_per_million_tokens (metric LAW: never raw candidate_count).
    #    HarnessRunReceipt object + skip-reason taxonomy + a REAL availability probe (harness CLIs on PATH, local
    #    runtime ports, provider-key presence) that NEVER runs a local model (dev-PC crash rule) or prints a key. ──
    ("scripts/harness_bakeoff_spec.py", "harness_bakeoff_spec"),
    # ── TASK LAYER-STACK FRAMEWORK: the GENERIC "every task is a layered stack x options-per-layer" pattern
    #    (multi-path law per domain). 28 canonical layer roles + 7 cross-cutting layers + 7 emission types
    #    (metadata/classification/receipt/routing/candidates/quality/feedback); a registry mapping 9 domains
    #    (document_ingestion/app_digestion/harness_bakeoff/esoteric built; api/repo/browser/kaggle/data_pipeline
    #    next) onto the roles. New domain = one row. candidate-only. ──
    ("scripts/task_layer_stack_framework.py", "task_layer_stack_framework"),
    # ── PROCESS POSSIBILITY ATLAS: the reusable step x layer x possibility atlas across 6 process domains
    #    (document_ingestion/document_processing/ai_agent/ml_training/evaluation/serving) — 46 steps, 607
    #    possibilities, EVERY possibility exploded into a candidate primitive (raw count SCALES, owner law).
    #    Possibility schema (method/best_for/cost/quality/failure_modes + routing_features/verifiers/fallbacks);
    #    each step is a zoo (>=2 options, mutation-gated). candidate-only. ──
    ("scripts/process_possibility_atlas.py", "process_possibility_atlas"),
    # ── PROCESS ATLAS EXPANDER: the raw-count explosion engine. Explodes the 607 seed possibilities x 61
    #    IMPLEMENTATION_KINDS (=37,027) x 35 MUTATION_OPERATORS (=1.29M) lazily, with lineage + route ports +
    #    gap records. Encodes METRIC_LAW_V2: usefulness is a NON-DESTRUCTIVE ROUTER (mutation-gated: it can NEVER
    #    cap/delete/prevent generation); raw count scales; serve-budget is serving-only. candidate-only. ──
    ("scripts/process_atlas_expander.py", "process_atlas_expander"),
    # ── PROCESS PATH SEARCH (OmniPath): the Universal Process Path Search Engine. Any task = a typed graph of
    #    steps x primitive-options (the atlas is the ProcessSpace; document_ingestion alone = 1.2e16 theoretical
    #    paths). Sampler (grid/random/stratified/evolutionary, seeded+reproducible) -> deterministic
    #    multi-objective proxy benchmarker -> Pareto frontier -> supervisor (continue/mutate/promote/quarantine)
    #    -> improver (mutate w/ lineage) -> GATED promoter (never 'certified' without a real verifier seam). Encodes
    #    Fable-5 advisor/orchestrator economics. Explore=grid-search, promote=supply-chain, serve=lean. candidate-only. ──
    ("scripts/process_path_search.py", "process_path_search"),
    # ── PIPELINE GENOME GRID: OmniPath applied to the FACTORY PIPELINE ITSELF. A PipelineGenome = 16 stages
    #    (source/acquisition/digest/roles/decomp/generation/filter/dedupe/security/executor/fixture/verifier/
    #    benchmark/retrieval/serving/adoption), each an option catalog -> 3.25e15 theoretical pipeline paths.
    #    Seeded sampling + successive halving + PARETO leaderboards (best PER objective, never one global winner);
    #    structured proxy scorer w/ domain boosts + the owner's path_score formula. Safety-invariant: candidate-only. ──
    ("scripts/pipeline_genome_grid.py", "pipeline_genome_grid"),
    # ── PRIMKIT CORE: the adoption-FORCING framework core. @primitive decorator (typed ports required) + manifest
    #    registry + receipted run_primitive() + @verifier + promotion-gate state machine (never 'certified'
    #    without lint/security/fixtures/benchmark/determinism/verifier/provenance) + prim.toml POLICY + the
    #    DIRECT-CALL LINTER (AST-scan: naked http/llm/browser/subprocess/eval + undecorated parse/extract/…
    #    functions). Encodes the corrected law (raw count primary; usefulness = non-destructive router). ──
    ("scripts/primkit_core.py", "primkit_core"),
    # ── PRIMITIVE TOKEN-SAVINGS A/B: the REAL (non-proxy) demonstration. For each of the 28 oracle-tested
    #    platform primitives: ARM A = live model WRITES the code -> security-scan -> sandbox vs the ORACLE ->
    #    real completion tokens + pass/fail; ARM B = reuse the verified body at ~0 gen tokens, guaranteed correct.
    #    Reports tokens_saved + correctness delta. Offline self-test uses a mock (mutation-gated); --live = real. ──
    ("scripts/primitive_token_savings_ab.py", "primitive_token_savings_ab"),
    # ── NO-PROXY GATE: the RULE that prevents dumb proxies being reported as real. Audits every benchmark/scoring
    #    module, classifies REAL (executes + measures API completion_tokens / sandbox oracle / http) vs PROXY
    #    (chars/4, hash/random, projection); requires a BENCHMARK_KIND declaration; FAILS if a proxy is dressed as
    #    real or a real claim lacks strong backing. Only REAL modules may report headline savings. ──
    ("scripts/no_proxy_gate.py", "no_proxy_gate"),
    # ── REAL SCALE PROMPT TEST: EXECUTES 50,000+ prompts through real deterministic dispatch + real primitive
    #    execution (0 LLM tokens); reports MEASURED dispatch hit-rate + execution correctness + tokens saved
    #    (0-token reuse vs the REAL measured per-primitive A/B cost, not chars/4). BENCHMARK_KIND=real. It exposed
    #    that 47/75 certified primitives were absent from the dispatch index (fixed -> hit-rate 0.36 -> 0.82). ──
    ("scripts/real_scale_prompt_test.py", "real_scale_prompt_test"),
    # ── HY3 PRIMITIVE CERTIFIER: grow the verified set beyond 75 using the REAL Hy3 keys. Hy3 writes a
    #    deterministic function + its own oracle fixtures -> robust parse (last balanced-brace JSON) -> the SAME
    #    real gates as the campaign (security scan -> isolated sandbox oracle -> determinism) -> certified pack,
    #    else rejected+preserved. candidate-until-certified; nothing self-promotes. ──
    ("scripts/hy3_primitive_certifier.py", "hy3_primitive_certifier"),
    # ── PROJECT TASK HARNESS: REAL project-level delivery (not primitive-level). A ProjectTask passes only when
    #    its solution actually BUILDS + RUNS + passes an EXECUTED hidden oracle in an isolated subprocess (per-run
    #    temp workspace, cleanup) — never plausibility. Pure-local cloud_function + ml_pipeline families execute
    #    here; k8s/localstack skip-with-reason. Self-test proves good PASSES + bad/stub FAIL. BENCHMARK_KIND=real_project. ──
    ("scripts/project_task_harness.py", "project_task_harness"),
    # ── PROJECT LIVE-AGENT A/B: a real model actually SOLVES a project task (writes the solution, repairs on
    #    failure) scored by the EXECUTED hidden oracle. Two lanes: harness_alone vs harness_plus_primitives
    #    (relevant certified primitives dispatched + injected; records real reuse). Real completion tokens +
    #    oracle_pass. Pluggable agent backend (API model default; codex/aider/ClawCodex slot in). BENCHMARK_KIND=real_project. ──
    ("scripts/project_live_agent_ab.py", "project_live_agent_ab"),
    # ── SAAS BUILDOUT DECOMPOSER: the reverse arc of the dev-kit loop — take a just-BUILT multi-file project and
    #    decompose ITS code back into primitive candidates (ast, 0-token), then TEST each by EXECUTION (security
    #    scan -> determinism probe run twice in an isolated subprocess -> optional oracle fixtures). Closes
    #    build->decompose->test->reuse: certified candidates render to the exec-card shape the next buildout
    #    imports verbatim. Mutation-gated (nondeterministic candidate FAILS). BENCHMARK_KIND=real_project. ──
    ("scripts/saas_buildout_decomposer.py", "saas_buildout_decomposer"),
    # ── BUILDOUTFORGE (Wave-0 kernel): the TOP-DOWN loop — a real multi-file project is BUILT, BOOTED as a running
    #    service, and verified by a HIDDEN HTTP oracle that drives real endpoints (realism B6). The executed footing
    #    for a real "does reuse save tokens on real software" number. Non-insurance genome. Mutation-gated (boots-but-
    #    wrong FAILS, never-boots FAILS). BENCHMARK_KIND=real_project_buildout. ──
    ("scripts/buildout_forge.py", "buildout_forge"),
    # ── BUILDOUTFORGE ORACLE PATTERNS: two more EXECUTED hidden-oracle genomes — a background order-ingestion
    #    WORKER (worker.process runs on a seeded queue; hidden oracle checks idempotent dedupe + poison->errors)
    #    and a CSV-UPLOAD stdlib-http app (boots; hidden HTTP oracle checks valid rows==N + malformed->400 +
    #    /health). Non-insurance. Mutation-gated (runs-but-wrong FAILS, never-runs FAILS) for BOTH genomes.
    #    BENCHMARK_KIND=real_project_buildout. ──
    ("scripts/buildout_oracle_patterns.py", "buildout_oracle_patterns"),
    # ── BUILDOUT AGENT BACKENDS: the data-driven ZOO of agent/harness backend LANES that DRIVE a buildout —
    #    direct_api (OpenRouter pool) + codex/aider/opencode/clawcodex/qwen_code CLIs + openai_agents_sdk/langgraph
    #    SDKs. REAL availability probe (shutil.which / find_spec / non-empty pool); run_cli_backend invokes an
    #    available CLI non-interactively and NEVER raises on an unavailable lane. Mutation-gated. BENCHMARK_KIND=real. ──
    ("scripts/buildout_agent_backends.py", "buildout_agent_backends"),
    # ── BUILDOUT A/B (both arms EXECUTED): a real model BUILDS a multi-file service twice — bare vs certified
    #    primitives EXTRACTED from a prior build pre-installed — and BOTH must BOOT + pass the hidden HTTP oracle.
    #    Savings = real tokens-to-pass; verdict honest by construction (measured_savings / capability_lift /
    #    treatment_regressed / inconclusive_no_baseline). Offline mocks self-test; --live drives the model. ──
    ("scripts/buildout_forge_ab.py", "buildout_forge_ab"),
    # ── BUILDOUTFORGE LARGE: one big non-insurance genome — an 11-module back-office ops API BUILT + BOOTED + driven
    #    by a hidden HTTP oracle over ~27 real endpoints (auth, RBAC, idempotent writes, pagination/filter/sort,
    #    audit, CSV export, signed webhook). Big surface -> 12 reusable pure primitives. Mutation-gated (boots-but-
    #    wrong FAILS, never-boots FAILS). BENCHMARK_KIND=real_project_buildout. ──
    ("scripts/buildout_forge_large.py", "buildout_forge_large"),
    # ── BUILDOUTFORGE PIPELINE genome: the OTHER real shape — a multi-module DATA PIPELINE / DAG (not an HTTP
    #    service). A ten-module sales ETL DAG (extract->validate->normalize->dedupe->join->aggregate->quality->
    #    load; stdlib + sqlite3 only) is BUILT, RUN as a subprocess, and verified by a HIDDEN pipeline oracle that
    #    opens out.db + reads metrics.json and asserts ~25 named checks incl. an idempotent rerun. Mutation-gated
    #    (runs-but-wrong FAILS, raises-on-import FAILS). BENCHMARK_KIND=real_project_buildout. ──
    ("scripts/buildout_forge_pipeline.py", "buildout_forge_pipeline"),
    # ── PROJECT COVERAGE PRIMITIVE PACK: 15 CERTIFIED pure primitives (http/validation/query/storage/pipeline) that
    #    cover a LARGE fraction of a build's glue, so the A/B injects real coverage — not one 10-line primitive. Each
    #    certifies oracle_correct via the decomposer's executed gate; the pack renders an importable module. ──
    ("scripts/project_coverage_primitive_pack.py", "project_coverage_primitive_pack"),
    # ── LARGE-PROJECT A/B: a real model BUILDS a LARGE multi-module project (11-file ops-API / 10-module ETL DAG)
    #    twice — bare vs the certified coverage pack pre-installed — BOTH must BOOT/RUN + pass the genome's hidden
    #    oracle. Nets input+output tokens; reports a DISTRIBUTION over n runs (never a cherry-picked run). ──
    ("scripts/run_large_project_ab.py", "run_large_project_ab"),
    # ── HTTP SCAFFOLD MACRO-PRIMITIVE: the measured conclusion in a genome — micro primitives never save (they're
    #    ~50 tok of a build); the BULK is HTTP-server boilerplate. Extracts it into a reusable `http_app` MACRO-
    #    primitive so a thin app.py = just handlers+routes; compiled_route provides the scaffold verbatim (0 gen
    #    tokens) and the model writes only the handlers. The genome where reuse CAN save tokens. ──
    ("scripts/http_scaffold_macro.py", "http_scaffold_macro"),
    # ── MACRO CRUD-SERVICE FACTORY: the decisive macro-primitive with an API the model CAN use — make_crud_app()
    #    factory owning the whole HTTP CRUD boilerplate; thin ~8-line app.py = one call. Lane D (compiled_route)
    #    provides it verbatim (0 prompt tokens) -> the model writes only the factory call. Where TOTAL savings can
    #    finally go positive (model writes materially less AND can wire a factory correctly). ──
    ("scripts/macro_crud_service.py", "macro_crud_service"),
    # ── AUTOMATIONDIRECTORYFORGE: mine PUBLIC workflow ecosystems (n8n/Zapier/IFTTT/Make/Pipedream/Activepieces/
    #    Workato/RapidAPI/Postman/APIs.guru/MCP/GitHub) -> decompose each along trigger->conditions->transforms->
    #    actions->error->credentials->side-effects->observability into deterministic primitive candidates + the
    #    make_webhook_worker MOLECULE (large reusable subsystem). Offline/governed (no raw bodies), env-var-only
    #    credentials, candidate-only. The molecule targets buildout_forge_automation's signed-webhook worker genome. ──
    ("scripts/automation_directory_forge.py", "automation_directory_forge"),
    # ── the AUTOMATION integration-worker buildout genome (signed-webhook ingest worker): the LARGE realistic task
    #    the molecule reuses into. compiled_route mounts make_webhook_worker VERBATIM -> the model writes only the thin
    #    app.py (measure the session-token savings of large-subsystem reuse). Hidden signed-HTTP oracle (HMAC/idempotency). ──
    ("scripts/buildout_forge_automation.py", "buildout_forge_automation"),
    # ── MULTI-STEP task A/B + PrimitiveSessionManager: where reuse COMPOUNDS. A verified primitive is mounted ONCE by
    #    the manager (inject-once, registry-seeded + session-built) and reused FREE by every later step, so savings
    #    scale with step count. Structural token-accounting (labeled PROXY over real module sizes) proves the
    #    compounding law (2.62× / strictly-increasing curve); --live gives the executed cumulative-token number. ──
    ("scripts/multi_step_task_ab.py", "multi_step_task_ab"),
    # ── SEARCH/LABELING/RAG PRIMITIVE DATABASE + 3 LARGE project genomes: the WITH/WITHOUT primitive-database A/B on
    #    advanced semantic search (BM25), rule labeling (+confidence gate), and deterministic RAG (chunk/retrieve/cite).
    #    Verified molecules mounted verbatim in compiled_route (~15-30x reuse ratio) or composed at 0 model tokens. ──
    ("scripts/search_rag_primitive_pack.py", "search_rag_primitive_pack"),
    ("scripts/buildout_forge_search_rag.py", "buildout_forge_search_rag"),
    # ── RACE how to build-with-primitives: 6 prompt variants x model zoo x project — never conclude from one cell.
    ("scripts/primitive_reuse_prompt_matrix.py", "primitive_reuse_prompt_matrix"),
    # ── the AGENT-INSTRUCTION COMPILER (candidate product hypothesis): repo guidance -> verified enforced automation.
    ("scripts/agent_instruction_compiler.py", "agent_instruction_compiler"),
    # ── the COMPREHENSIVE reuse experiment grid (built because conclusions were drawn from tiny runs):
    #    4 lanes x model zoo x task families x many repeats; aggregates with sample sizes, MIN_N guard, no single-cell conclusions.
    ("scripts/reuse_experiment_grid.py", "reuse_experiment_grid"),
    # ── PARTIAL COMPOSITION (owner: "solve some portions, expose the edges, let an LLM fill the gap"): DB covers
    #    the hard infra (tokenize/BM25/HTTP) verified + exposes edges; the model writes ONLY the task-specific gap.
    ("scripts/edge_exposed_gapfill.py", "edge_exposed_gapfill"),
    # ── REALISTIC multi-turn agentic SESSION harness (senior-dev scale): tool loop (read/edit/test/repair) over a
    #    multi-file working set, FULL-session token accounting (input re-sent each turn -> input-dominated), WITH/WITHOUT DB.
    ("scripts/realistic_session_harness.py", "realistic_session_harness"),
    # ── INPUT-TOKEN LEVER (ideation #20/#18/#22): quantify how compact capability-cards vs raw re-reads cut the
    #    INPUT tokens that dominate long sessions (compounds with turns x verified fraction). Structural proxy.
    ("scripts/input_token_lever.py", "input_token_lever"),
    # ── LIVE 5M/40M primitive INVENTORY scanner (AIDevObserver milestone 1): status-label ladder computed from disk
    #    (raw->candidate->indexed->searchable->composition_ready->verified->promotion_ready->customer_proof) + gap + focus.
    ("scripts/primitive_inventory.py", "primitive_inventory"),
    # ── REALAPPFORGE: turn REAL public apps (Claude-Code/Polsia-built SaaS) into SOURCE-backed EQUIVALENT buildout
    #    tasks + enforce the evidence ladder — public claims A0-A5 are SOURCE evidence (NEVER a savings headline);
    #    only EXECUTED A6 (equivalent build passes a hidden oracle) / A7 (paired reuse win) count. App genome plugs
    #    into run_large_project_ab; ops-API + ETL DAG are A6-capable. Legally-safe equivalent tasks, never clones. ──
    ("scripts/real_app_forge.py", "real_app_forge"),
    # ── bench.project_to_primitives.v1: MEASURE the primitive YIELD of building a project — decompose each
    #    executable genome's built code -> candidates, count pure targets + matches to the certified registry.
    #    The empirical answer to "does building whole projects discover reusable primitives?". Deterministic. ──
    ("scripts/bench_project_to_primitives.py", "bench_project_to_primitives"),
    # ── SOURCE SURFACE CATALOG: the governed, extensible map of WHERE primitives come from (code hosts, package
    #    registries, Q&A/forums, docs.<domain>, API directories incl. RapidAPI, standards, algorithm/textbook,
    #    papers, real-apps, infra, AI/agent, issues/security, web index) + the SEARCH METHODS (AST/semantic/schema/
    #    test-mining/issue->PR/dedup) + the user-configurable-credential discipline (env-names only, no embed). ──
    ("scripts/source_surface_catalog.py", "source_surface_catalog"),
    # ── INSTRUCTION FILE MINER: public CLAUDE.md/SKILL.md/TOOLS.md/AGENTS.md -> deterministic capability candidates.
    #    Decomposition rule enforced: NL->metadata, command/code patterns->candidates, human-approval->NON-reusable
    #    policy notes; dedup collapses 'npm test' across thousands of files to ONE; license discipline (unlicensed=
    #    evidence_only). Deterministic core offline; GitHub discovery token-gated. ──
    ("scripts/instruction_file_miner.py", "instruction_file_miner"),
    # ── DOCS API FORGE (DocsDomainForge core): OpenAPI/docs -> USER-KEYED interface primitives (request builder +
    #    response validator + auth injector), MOCK-PROVEN offline with NO real key; credentials referenced BY ENV
    #    NAME (user-configurable), never embedded. Provider key audit + missing-key accelerators. ──
    ("scripts/docs_api_forge.py", "docs_api_forge"),
    # ── RESEARCH EVIDENCE PRIMITIVES: certified deterministic gates for evidence-heavy research (legal/FOIA/
    #    standards/regulatory) from the Universal Research spec — source-reliability tiering (== candidate/truth
    #    boundary for sources), quote gate (metadata never quote-ready), adversarial-completeness, overstatement
    #    detection, theory-shift, proof-gap->records. Fixtures ARE the spec's §15 tests; all certify oracle_correct. ──
    ("scripts/research_evidence_primitives.py", "research_evidence_primitives"),
    # ── REAL SAVINGS LEDGER: the honest reporter over every benchmark receipt — headline-eligible ONLY when both
    #    lanes ran the same task, both REAL, both PASSED, no-proxy holds. classify_pair closes the escape hatch
    #    (a regression never claims savings). Writes docs/REAL_SAVINGS_NUMBERS.md. Mutation-gated on the core. ──
    ("scripts/real_savings_report.py", "real_savings_report"),
    # ── MISSING-CAPABILITY AUDITOR: makes the factory self-aware about blockers — probes keys (presence-only, no
    #    secret values), local LLM endpoints, harness tools, runtimes, and coverage; for every MISSING item reports
    #    what it unlocks + how. Emits docs/MISSING_CAPABILITIES_AND_ACCELERATORS.md + accelerator_requests.jsonl. ──
    ("scripts/audit_missing_capabilities.py", "audit_missing_capabilities"),
    # ── SESSION-SCALE EVALUATION: projects primitive-reuse savings across >=50,000 seeded, diverse sessions
    #    (greenfield app / micro-SaaS / product-improvement / warehouse / ML / agent / API / doc / browser),
    #    CALIBRATED on the real executed A/B receipt (per-task bare-write tokens + 50% bare correctness + reuse
    #    cost). Honest addressability model: only primitive-addressable tasks save; glue is equal in both arms ->
    #    session mean ~1.95x (p90 3.76x) + 50pts correctness. Deterministic; labeled projection; candidate-only. ──
    ("scripts/session_scale_evaluation.py", "session_scale_evaluation"),
    # ── DETERMINISTIC PRIMITIVE DISPATCH: map a task (brief and/or a sample INPUT) to a VERIFIED primitive with
    #    ZERO LLM tokens — keyword/edge index + pure input-shape predicates (IBAN string / EBCDIC bytes / FIX
    #    msg / IPv4 / HL7 …). Ambiguous briefs MISS -> LLM fallback (never guesses). The deterministic-search
    #    token-reduction lever: selection cost -> 0 for the verified set. hit-rate 1.0 on 28 primitives. ──
    ("scripts/deterministic_primitive_dispatch.py", "deterministic_primitive_dispatch"),
    # ── DISPATCH ZOO: the multi-path law applied to resolution. Races deterministic layers (keyword / synonym /
    #    trigram / fusion, 0 LLM tokens) on a REALISTIC English query bank that AVOIDS the primitive keywords —
    #    honest numbers: keyword 0.77 -> synonym 0.86 -> fusion 0.89, with a 0.11 LLM-fallback tail. Proves the
    #    zoo beats any single layer + exposes where a semantic-embed layer / LLM is still needed. ──
    ("scripts/deterministic_dispatch_zoo.py", "deterministic_dispatch_zoo"),
    # ── CERTIFICATION CAMPAIGN V1: turn candidate primitives into CERTIFIED (security+oracle-sandbox+determinism
    #    gated) ones, ranked by ADDRESSABILITY LIFT (freq × token-weight × failure-rate × route-value / cost).
    #    5 lanes; Lane-2 high-frequency scalars prioritized (biggest addressability lever). Ran 42/42 certified
    #    (28 protocol + 14 new scalars); rejects broken+dangerous; multi-tier-aware. candidate-until-certified. ──
    ("scripts/certification_campaign.py", "certification_campaign"),
    # ── PROGRAMMING PRIMITIVES PACK: 33 everyday string/list/dict/math/algorithm DEV utilities (camel<->snake,
    #    chunk/flatten/unique/window, deep-merge/flatten-dict, gcd/lcm/prime/fib, binary-search/levenshtein/RLE/
    #    caesar) with 58 oracle fixtures. The highest-FREQUENCY, broadest-addressability lane; executor=getsource. ──
    ("scripts/programming_primitives_pack.py", "programming_primitives_pack"),
    # ── CLOUD_FUNCTION PRIMITIVE PACK: project-relevant primitives (validate_order_event / idempotency_seen /
    #    http_json_error / health_response) that close the certification gap the real project A/B exposed (lane B
    #    had 0 reuse because dispatch returned IBAN/email for an order-handler). Indexed into dispatch + injection
    #    so the cloud_function goal resolves to RELEVANT primitives and we can measure real project-level lift. ──
    ("scripts/cloud_function_primitive_pack.py", "cloud_function_primitive_pack"),
    # ── KAGGLE ITERATIVE OBJECT MINER: grinds Kaggle ONE notebook at a time, resumable crash-safe cursor
    #    (dedup), OFFLINE AST+pattern decompose (no LLM lane) -> typed primitive candidates (handle+digest, no raw
    #    body). Uses the saved KGAT token via the kaggle CLI. candidate-only. ──
    ("scripts/kaggle_iterative_object_miner.py", "kaggle_iterative_object_miner"),
    # ── PROVIDER-AGNOSTIC ROUTER FACTORY: capability registry over existing PROVIDERS + job-type->lane router
    #    (executor_synthesis -> NVIDIA-first, ideation -> Hy3-first, sensitive -> local-only) + compliance-safe
    #    quota manager (kill-switch/budgets/redacting-ledger) + campaign runner + lane bakeoff. candidate-only. ──
    ("scripts/llm_quota_manager.py", "llm_quota_manager"),
    ("scripts/llm_capability_router.py", "llm_capability_router"),
    ("scripts/run_primitive_generation_campaign.py", "run_primitive_generation_campaign"),
    ("scripts/model_lane_bakeoff.py", "model_lane_bakeoff"),
    # ── AUTONOMOUS full-loop factory: headless forever-loop chaining scrape -> deconstruct -> Hy3 manufacture ->
    #    Hy3+omniroute executor-synthesis, crash-isolated subprocess stages, STOP-gated; ZERO human/Claude-Code input. ──
    ("scripts/autonomous_primitive_factory_loop.py", "autonomous_primitive_factory_loop"),
    # ── PRIMITIVE WARRANTIES: shippable EXPIRING warranty (tested_on/not_tested_on/known_failure_modes/expires;
    #    horizon from determinism x risk) + "no warranty, no production" gate. candidate-only. ──
    ("scripts/primitive_warranty.py", "primitive_warranty"),
    # ── ANTI-PRIMITIVE / NEGATIVE-KNOWLEDGE store: aggregate counterexamples + quarantines + lint hard-fails into a
    #    known-bad store; multi-axis matcher STOPS the foundry re-minting known-bad. candidate-only. ──
    ("scripts/anti_primitive_store.py", "anti_primitive_store"),
    # ── PRIMITIVE LINTER (the "lint" gate of the primitive-OS pipeline): scores our own cards for skill
    #    smells (missing routing/IO/verifier, token bloat, undeclared side effects) + reports the corpus
    #    schema-level gaps vs the formal-primitive-package standard (Formal Skill/SkVM/SWE-Skills-Bench).
    #    Grounded in SkillReducer (55K skills) + the SKILL.md-smells study (>99% carry a smell). ──
    ("scripts/lint_primitives.py", "lint_primitives"),
    # ── ML LIFECYCLE PRIMITIVE MINTER: primitives for all 44 ML-lifecycle stages (301 concrete ops x
    #    techniques x task families = 84,280-point grid) — define->data->prepare->model->evaluate->deploy->
    #    serve->monitor->maintain. Canonical ids; NON-DESTRUCTIVE gate. serves_truth=false. ──
    ("scripts/ml_lifecycle_primitive_minter.py", "ml_lifecycle_primitive_minter"),
    # ── ML TEAM-ROLE PRIMITIVE MINTER: primitives for all 23 production-ML team roles x actions x tools
    #    (152 role-actions x 40 tools). Canonical ids; NON-DESTRUCTIVE gate. serves_truth=false. ──
    ("scripts/ml_team_role_primitive_minter.py", "ml_team_role_primitive_minter"),
    # ── BROWSER AUTOMATION PRIMITIVE MINTER: custom browsers/forks/anti-detection/CDP as primitives
    #    (the space that unblocked Gemma behind Cloudflare). serves_truth=false. ──
    ("scripts/browser_automation_primitive_minter.py", "browser_automation_primitive_minter"),
    # ── BROWSER CONTROL HARNESS: read-only browser + TAB control research crawler; a backend ZOO (static+cdp
    #    implemented, nodriver/playwright/browser-use/pinchtab/lightpanda rows) + browser_* primitives + robots/
    #    throttle/secret-redaction safety -> evidence-linked CapturedArtifact rows. serves_truth=false. ──
    ("scripts/primitive_browser_control_harness.py", "primitive_browser_control_harness"),
    # ── GITHUB REPORT INGESTION: offline-fixture repo_inventory/primitive_mining/test_fixture reports over a repo
    #    tree -> candidate primitives/verifiers/benchmarks; the report layer atop github_repo_harvester. candidate-only. ──
    ("scripts/github_repo_report.py", "github_repo_report"),
    # ── BROWSER SESSION/TAB-GRAPH REPORTS: CapturedArtifact rows -> session report + TAB GRAPH (opener/popup/
    #    cross-origin/auth-state) -> browser_primitive_candidate rows (9 types incl safe_submit_gate). candidate-only. ──
    ("scripts/browser_session_report.py", "browser_session_report"),
    ("scripts/browser_report_to_primitive_candidates.py", "browser_report_to_primitive_candidates"),
    # ── BROWSER TOOLING SURVEY: evidence-based 13-category capability matrix (real CDP/Playwright/HTTP/LLM probes,
    #    mutation-gated) + offline stdlib fixture lab. "Playwright is only the baseline." candidate-only. ──
    ("scripts/run_browser_fixture_lab.py", "run_browser_fixture_lab"),
    ("scripts/probe_browser_control_tools.py", "probe_browser_control_tools"),
    # ── BROWSER/INGESTION full survey: 37-tool inventory + 56 primitive candidates + fetch/parser/crawler/
    #    llm-extraction/search adapters (Playwright = 1 of 37); evidence-based, candidate-only. ──
    ("scripts/build_browser_tool_inventory.py", "build_browser_tool_inventory"),
    ("_repos/shared-backend-components/browser_control/ingestion_self_test.py", "browser_control_ingestion"),
    # ── DRIVER-NEUTRAL ADAPTER PACKAGE: browser_control/ wraps the harness (BrowserAdapter over 4 adapters +
    #    FakeAdapter) + safety + 4 schemas + decision framework; every action -> receipt. candidate-only. ──
    ("_repos/shared-backend-components/browser_control/self_test.py", "browser_control"),
    # ── KAGGLE NOTEBOOK PRIMITIVE FOUNDRY (standalone, no-harness): real Kaggle API acquisition -> LLM
    #    decomposition (Ollama/OpenWebUI-Gemma-4/OpenRouter) -> remix -> canonical-id staging; source
    #    handle+digest only (no raw body in cards); resumable/rate-limited/bounded; offline self-test with a
    #    fixture notebook + stub model. Live Kaggle/LLM lanes opt-in. serves_truth=false. ──
    ("scripts/kaggle_notebook_primitive_foundry.py", "kaggle_notebook_primitive_foundry"),
    # ── EXECUTABLE PRIMITIVE LIBRARY: primitives that ACTUALLY RUN — 18 real, correct, oracle-backed
    #    implementations across common/rare/super-rare coding tasks; each mutation-gated (a planted bug goes
    #    red); cards carry the real source as the executable body. Reuse = 0 generation tokens. serves_truth=false. ──
    ("scripts/executable_primitive_library.py", "executable_primitive_library"),
    # ── TOKEN SAVINGS BENCH: proves the executable primitives cut tokens — reuse=0 (structural) vs a measured
    #    per-tier regeneration lower bound that rises with rarity; labelled/swept workload projection; opt-in
    #    real-model arm (actual regen tokens, no model-code exec). serves_truth=false. ──
    ("scripts/token_savings_bench.py", "token_savings_bench"),
    # ── PRIMITIVE BUILDOUT ORCHESTRATOR (standalone): our LLM endpoints (Ollama/Gemma-4/OpenRouter, provider
    #    fallback) GENERATE executable primitives; each must pass an oracle test in an AST-safety-scanned
    #    sandbox subprocess to be staged (wrong->rejected, unsafe->refused, never fabricated); improves the
    #    decomposition question bank additively. serves_truth=false. ──
    ("scripts/primitive_buildout_orchestrator.py", "primitive_buildout_orchestrator"),
    # ── AGENTIC SESSION SAVINGS BENCH: token savings at the SESSION level where they compound — advanced
    #    multi-turn scenarios (multi-file write/edit, agentic debug, feature end-to-end) under pure-LLM vs a
    #    primitive harness (covered steps 0-token, compacted history, span-budgeted retrieval, patch-not-regen).
    #    Assumptions labelled + swept; mechanisms are the real executable + token-opt primitives. serves_truth=false. ──
    ("scripts/agentic_session_savings_bench.py", "agentic_session_savings_bench"),
    # ── PRIMITIVE FLYWHEEL TICK (the scheduled autonomous engine): one cron tick rotates BOUNDED
    #    primitive-building work across our lanes (Ollama-GLM/Kimi, OpenWebUI-Gemma-4, opt-in Codex) and
    #    harnesses (buildout/enrich/mint); STOP-gated, daily-capped, receipt-logged, idempotent. serves_truth=false. ──
    ("scripts/primitive_flywheel_tick.py", "primitive_flywheel_tick"),
    # ── ENRICH MINTED PRIMITIVES: real-generation upgrades (mechanism + tools + steps + payloads) parsed
    #    from the keyed Ollama Cloud lane, nested LOSSLESSLY with token provenance; failures recorded never
    #    fabricated; new staged file only. The anti-placeholder engine. serves_truth=false. ──
    ("scripts/enrich_minted_primitives.py", "enrich_minted_primitives"),
    # ── PRIMITIVE USEFULNESS GATE (the anti-placeholder gate): deterministic pure-function criteria
    #    (scaffold regex, title-restatement, generic edges, no-concrete-token, vague steps, pool-level
    #    template stamping) as extensible ROWS; placeholder-rate receipts per namespace + the
    #    enriched-vs-plain grading of the enrichment engine. Verdicts are funnel signals, never
    #    promotion. serves_truth=false. ──
    ("scripts/primitive_usefulness_gate.py", "primitive_usefulness_gate"),
    # ── PRIMITIVE SCALE PLAN (fleet-built): pool ledger + six admission gates + provenance-stamped assembly
    #    to target counts; evaluation-verified (coverage 0.585 -> 0.9967 on the 600-scenario probe, 0
    #    boundary violations). Searchable-STAGED lane; promotion stays with the funnel. serves_truth=false. ──
    ("scripts/primitive_scale_plan.py", "primitive_scale_plan"),
    # ── PRIMITIVE CONSUMPTION PROOF: prove the enriched primitives are in a position to be CONSUMED (built
    #    into a loadable candidate store, retrievable by their own task query among real distractors) and that
    #    they carry CROSS-SESSION value (session-reach over diverse dev-task prompts — a card unmatched by our
    #    bank is never discarded); + the real scaffold-vs-scratch generation-savings bench (keyed lane) that
    #    replaces the 0.4-0.7 assumption. Nothing discarded. serves_truth=false. ──
    ("scripts/primitive_consumption_proof.py", "primitive_consumption_proof"),
    # ── CONSUMABILITY AUDIT: tier the pool (verified/enriched/template), verify per-tier mechanics (edges +
    #    in-serving-store set math), and RESTATE the savings model honestly per tier with labelled
    #    assumptions — the anti-overclaim gate. serves_truth=false. ──
    ("scripts/primitive_consumability_audit.py", "primitive_consumability_audit"),
    # ── SAVINGS STATISTICS (the consolidated dashboard): tokens/time/cost saved aggregated from every
    #    receipt (real races, real sessions, simulated fleets, coverage sweeps), price assumptions SWEPT and
    #    labelled, absent sources named, plus expansion signals (weak categories/capabilities, minting lift,
    #    escalation rate) telling the loop where to invest next. serves_truth=false. ──
    ("scripts/savings_statistics.py", "savings_statistics"),
    # ── REAL SESSION PROMPT MINING (real-world proof): mine GENUINE developer prompts from this machine's
    #    own Claude Code transcripts (2,800+ files; tool results/acks/stdout/pastes excluded; byte-bounded),
    #    REACH coverage over the corpus with floors, query-class histogram, and facet-named gap clusters
    #    ("we need more primitives HERE"); raw prompt text lives only in gitignored dist/ — the privacy gate
    #    is a self-test check. serves_truth=false. ──
    ("scripts/real_session_prompt_mining.py", "real_session_prompt_mining"),
    # ── CAPABILITY API (the deployable front door): stored dense + register + lexical lanes fused behind
    #    /retrieve, the 0-token edge_chain path behind /compose, receipts on /stats — stdlib HTTP, immutable
    #    mmap'd stores (replica-ready), proven over a real socket round-trip in the self-test.
    #    serves_truth=false on every payload. ──
    ("scripts/serve_capability_api.py", "serve_capability_api"),
    # ── ROBUST QUERY GRAINS (uncontrolled input — typos/terse/mixed-language): a ZOO of 6 matching grains
    #    (char-trigram/token/phrase/operation/embedding/transliterate), each robust to a different noise,
    #    raced by a noise-injection receipt. The UNION ranks the target where the token grain collapses; NO
    #    single grain survives every noise alone. Reuses edge_representations trigrams + descriptor facets. ──
    ("scripts/robust_query_grains.py", "robust_query_grains"),
    # ── HIERARCHICAL SEMANTIC EMBEDDINGS (advanced NLP: typed roles + grouped grains): each primitive embeds
    #    along 4 TYPED ROLES (intent/object/action/outcome — different embedding KINDS) x 4 abstraction GRAINS
    #    (specific→frame→domain→shape). A query matches at every role x grain: object-focused queries land on
    #    the OBJECT axis, vague queries on a COARSE grain (recall fallback), while a weighted rank keeps a
    #    coarse-grain tie from drowning the specific signal. Reuses the shipped embedder + facet/frame
    #    extractors; backend-agnostic (sharpens under a real model). serves_truth=false. ──
    ("scripts/hierarchical_semantic_embeddings.py", "hierarchical_semantic_embeddings"),
    # ── QUERY DECOMPOSER (break a messy dev-task into components): deterministic-first clause split +
    #    constraint stripping + fuzzy-robust facet typing (char-trigram: dedupe->dedup), with an opt-in LLM
    #    ESCALATION lane for compound single clauses (model proposes CUTS only; deterministic re-types; clean
    #    splits never call it; a crash degrades gracefully). Feeds wiring_language. serves_truth=false. ──
    ("scripts/query_decomposer.py", "query_decomposer"),
    # ── QUERY PREPROCESS ZOO (the owner's "full graph of toggleable paths"): 11 preprocessing routes (5
    #    deterministic + 6 LLM) each ON/OFF; LLM routes call the live Ollama lane via an injected seam and
    #    no-op offline (so the zoo self-tests deterministically); run_grid races EVERY route-subset
    #    combination and picks the champion by receipt — with/without preprocessing, with/without each agent.
    #    No single chosen path; the graph is baked in and MEASURED. serves_truth=false. ──
    ("scripts/query_preprocess_zoo.py", "query_preprocess_zoo"),
    # ── UNDERSTAND_QUERY (the serving FRONT DOOR — the fleet's ranked build #1): one deterministic-first
    #    motion chaining preprocess-zoo -> segment (typed components + constraints) -> per-component
    #    multi-grain UNION retrieve (grains + hierarchical roles) -> confidence gate -> candidate wiring
    #    order. Makes this session's standalone engines load-bearing. 0 tokens by default; llm seam feeds the
    #    escalation tail. serves_truth=false. ──
    ("scripts/rank_fusion_zoo.py", "rank_fusion_zoo"),
    # ── PIPELINE PATH GRAPH (the owner's "graph of potential paths"): the solve is 7 ordered STAGES (analyze /
    #    preprocess / secondary / search / fuse / rerank / compose), each a ZOO of interchangeable OPTIONS
    #    (deterministic/heuristic/nlp/frontier-llm/local-llm — 25 options, 3840 full paths). enumerate_paths
    #    gives the graph (kind-filterable), run_path executes one path 0-token by default with an LLM seam per
    #    llm stage. Options reuse the session's zoos; expand a stage = add a row. serves_truth=false. ──
    ("scripts/pipeline_path_graph.py", "pipeline_path_graph"),
    ("scripts/understand_query.py", "understand_query"),
    # ── QUERY EXPANSION ZOO (the 0-token "before retrieve" segment — the IR/NLP survey's #1 genuinely-absent
    #    technique): 5 routes (none / prf_rm3 / rocchio_lite / facet_expand / neighbor_grain). PRF/RM3 harvests
    #    the pseudo-relevant feedback docs' bridging vocabulary (Σ rel·P(t|d)·idf) and RECOVERS a target the raw
    #    query lexically missed; facet_expand maps paraphrase → canonical operation term; neighbor_grain repairs
    #    typos → corpus vocabulary. Every expansion is a strict superset of the original; the race picks by
    #    recall@k then parsimony. Reuses the shipped idf/facets/trigrams. serves_truth=false. ──
    ("scripts/query_expansion_zoo.py", "query_expansion_zoo"),
    # ── PATH GRAPH BENCH (run + benchmark the WHOLE graph): enumerates + executes ALL paths (every zoo
    #    combination) over a real sampled corpus with a shared cache, proving they run error-free; and a QUALITY
    #    bench over a labelled family set scoring each ranking-relevant config by recall@k/MRR/nDCG with
    #    INDEPENDENT retrieval per path (not a rescored lexical pool) on the REAL local embedder (model2vec /
    #    Ollama). Ranks configs, picks a champion, reports the union-vs-lexical lift. serves_truth=false. ──
    ("scripts/path_graph_bench.py", "path_graph_bench"),
    # ── BUILD PRIMITIVE EMBEDDINGS (close the storage audit's #1 gap): batch-embed every primitive (model2vec,
    #    in-process, ~2.3s/112K) + a deterministic feature record, PERSIST to disk (embeddings.npy + ids +
    #    features + content-hashed manifest), and search the STORED matrix by cosine with NO per-query corpus
    #    re-embed — the local precursor to a pgvector/faiss ANN index behind the same load+search. serves_truth=false. ──
    ("scripts/build_primitive_embeddings.py", "build_primitive_embeddings"),
    # ── EMBEDDER ZOO (the model port is a zoo too): several embedder backends behind one interface — crc32
    #    proxy / a from-scratch LSA we TRAIN on our own corpus (TF-IDF+SVD, numpy) / model2vec static pretrained
    #    / Ollama nomic — raced by recall@k/MRR/nDCG on a labelled family set. Adding any of the thousands of
    #    models out there = one new row + a re-run; the choice is a receipt. serves_truth=false. ──
    ("scripts/embedder_zoo.py", "embedder_zoo"),
    # ── REQUEST INTAKE (the front-most preprocessing layer): normalize a raw user/agent prompt into a canonical
    #    REQUEST BRIEF (goal/input/output/integrations/platform/technologies/constraints), each field filled by a
    #    zoo of extractors (facet/lexicon/pattern/constraint-strip/embed-nearest/llm-LoRA seam), deterministic-
    #    first + 0-token; gaps become CLARIFYING QUESTIONS and filled fields become a normalized query. ──
    ("scripts/request_intake.py", "request_intake"),
    # ── SESSION CONTEXT (deterministic, 0-token session-log + memory mining): tails the stored Claude Code
    #    transcripts (~/.claude/projects/<project>/*.jsonl, BYTE-BOUNDED so a 160MB log costs the same as 1KB) +
    #    the memory bank, extracts the request-brief fields (platform/tech/integrations/entities/goals) via the
    #    shared lexicons/facets, and feeds request_intake as auto-assembled context — a terse follow-up carries
    #    the session forward with no LLM call and no clarifying question. serves_truth=false. ──
    ("scripts/session_context.py", "session_context"),
    # ── GRAPH FLEXIBILITY (ENFORCEMENT): a gated conformance test that mutates a SANDBOX of the live graph the
    #    way a real edit would and asserts it adapts — add option, insert stage mid-pipeline, toggle on/off,
    #    computed counts, contract-substitutable options, routability. Red the moment flexibility regresses. ──
    ("scripts/graph_flexibility.py", "graph_flexibility"),
    # ── GRAPH AUTOTUNE (SELF-TUNING): race the ranking configs, pick the champion by nDCG/recall receipt,
    #    PERSIST it as the graph's active config, read it back for serving with a safe fallback (self-heals when
    #    an option is removed). Re-run to re-adapt. serves_truth=false. ──
    ("scripts/graph_autotune.py", "graph_autotune"),
    # ── SESSION REDUNDANCY (AIDevObserver demo): process a GROUP of stored coding-session transcripts and find
    #    redundant behavior DETERMINISTICALLY (0-token) — duplicate commands, repeated reads/edits, redundant
    #    searches, cross-session repeats + a redundancy rate. The reuse thesis applied to AI usage. ──
    ("scripts/session_redundancy.py", "session_redundancy"),
    # ── BENCH COMPOSITION SYSTEM (the whole-system receipt): wires the three levers end-to-end over the real
    #    corpus — connectivity EXACT vs edge_type_matcher (the ~9.5x lift), a composed plan's token cost by
    #    SIGNATURE vs full card (the ~15x, via primitive_onion), and the hybrid GAP RATE (fraction of targets
    #    needing ≥1 generated spec) under type-aware vs exact matchers so the connectivity lever's effect on the
    #    gap rate is visible. Mutation- + determinism-gated; serves_truth=false. ──
    ("scripts/bench_composition_system.py", "bench_composition_system"),
    # ── SURFACE NAMING REGISTRY (owner canonical operating interpretation 2026-07-01): ONE owning source (_repos/shared-backend-components/architecture/surface_naming_registry.json) for the 5 public surfaces + the internal AIDevObserver Benchmark Lab mode; forbidden branded aliases (AIDevExplorer / AI Dev Explorer / …) must not appear in product-facing copy (web/** + README) unless the same line marks them legacy/internal; lowercase `aidevexplorer` paths stay a recorded legacy namespace until deliberate migration; never serves truth ──
    ("scripts/check_surface_naming.py", "check_surface_naming"),
    # ── COMPOSITION AFFINITY (edge-first program W1, 2026-07-01): LEARNED connection strengths between primitive edges — seeded from source-backed group cards' ordered member edges (known-good chains; 770 production pairs), updated from run/triage outcomes (accept/reuse boost, dismiss/wrong-match NEGATIVE memory) with 30-day half-life decay; deterministic (no model calls), pair ids via canonical_id; a ranking BOOST only — never overrides contract compatibility, never serves truth ──
    ("_repos/teleon/backend/src/teleon/registry/composition_affinity.py", "composition_affinity"),
    # ── QUERY FOUNDRY (edge-first program W11, 2026-07-01): deterministic SAMPLED generation of ingestion search queries from the 14-dimension cross-product (person × directed-question × … × publication-medium, all nullable; seed space ~5.7e13 — never enumerated). Reproducible seeds, order-insensitive blocked dedupe, priority = gap-screen alignment, scope law (no insurance) enforced AT GENERATION; every row records that fetching stays behind the governed browsing stack + W10 licensing owner gate; candidate-only, never truth ──
    ("scripts/query_foundry.py", "query_foundry"),
    # ── REPO LINE REVIEW LOOP (resumable whole-repo sweep): walks owned source/text file-by-file and line-by-line in bounded batches, excluding vendored/reference/generated/data/cache paths; emits checkpointed state + findings JSONL for secrets, conflict markers, syntax, pyprefix drift, dynamic refs, entrypoint contracts, and hygiene; never serves truth ──
    ("scripts/repo_line_review_loop.py", "repo_line_review_loop"),
    # ── REPO CODE INVENTORY: exhaustive owned-source inventory for every reviewed file + every owned Python package/module, definition symbol, reference, import, and structural edge; emits durable JSONL artifacts plus manifest/summary as candidate evidence for hybrid review and pyprefix migration; never serves truth ──
    ("scripts/repo_code_inventory.py", "repo_code_inventory"),
    # ── HYBRID REPO REVIEW PIPELINE: deterministic line/AST/graph findings are the authority; optional OpenAI-compatible LLM calls only enrich review packets as candidate explanations/remediation hypotheses (serves_truth=false); emits review-packets + llm-prompts with graph context for poor logic, magic literals, scalar-series, loopability, dynamic refs, and pyprefix drift ──
    ("scripts/hybrid_repo_review_pipeline.py", "hybrid_repo_review_pipeline"),
    # ── TELEON CODEGEN CONTRACTS: Teleon-generated code must be born graphable/scalable — long AI-first pyprefix names, purpose/input/output contracts, scalar_or_sequence normalization, bounded iteration, dispatch tables, arrays over numbered scalars, candidate-only model output, and proof-before-promotion; backed by _repos/teleon/backend/src/teleon/synthesis/primitive_blocks.py ──
    ("scripts/check_teleon_codegen_contracts.py", "check_teleon_codegen_contracts"),
    # ── TELEON PRIMITIVE ASSEMBLY THESIS: user capability + context + guardrails should resolve to a graph of proven primitives/adapters with I/O contracts, structured JSON logs, self-tuned variants, and proof-gated promotion; generated source is minimized to missing adapters/primitives; never serves truth ──
    ("scripts/check_teleon_primitive_assembly_thesis.py", "check_teleon_primitive_assembly_thesis"),
    # ── TELEON PRIMITIVE VARIATIONS: deterministic/cheap mutations of primitives (scalar→sequence, output wrappers, linear graph composition, JSON run logs) plus enterprise laws for CI/CD, BYOK, marketplace primitives, local/API swaps, and control-vs-cost tradeoffs; never serves truth ──
    ("scripts/check_teleon_primitive_variation_contracts.py", "check_teleon_primitive_variation_contracts"),
    # ── TELEON COMPONENT-PLAN COMPILER: RAG retrieves compact ComponentCards; the LLM emits constrained PipelinePlan objects only; deterministic code validates retrieved components, versions, bindings, side-effect gates, topo order, mutation-before-regeneration affordances, and emits a lockfile (executor never runs raw LLM output); never serves truth ──
    ("scripts/check_teleon_component_plan_compiler_contracts.py", "check_teleon_component_plan_compiler_contracts"),
    # ── TELEON PIPELINE TEMPLATE RUNTIME: LLM JSON / generated Python can express a runtime as one primitive step per line; deterministic code resolves primitive ids from an allowed registry, owns task/named-input state passing, artifact refs, bounded retries, and JSON event logs; never serves truth ──
    ("scripts/check_teleon_pipeline_template_runtime.py", "check_teleon_pipeline_template_runtime"),
    # ── TELEON PIPELINE TEMPLATE ADVERSARIAL BENCHMARK: compares verbose JSON, compact IDs, callable lists, primitive handles, object graphs, and opt-in objects on one vendor-invoice workflow; measures token proxy/determinism/flexibility and rejects malformed variants; never serves truth ──
    ("scripts/check_teleon_pipeline_template_adversarial_benchmark.py", "check_teleon_pipeline_template_adversarial_benchmark"),
    # ── COMBINED CODE-INTELLIGENCE SYSTEMS: keeps pyprefix long meaningful names as the source-level semantic layer, then layers Python AST/symtable, tree-sitter-style multi-language parsing, CPG/data-flow, Semgrep/Ruff/mypy/Pyright/LSP-style evidence, and LLM candidate review; external tools are evidence layers, never truth ──
    ("scripts/check_combined_code_intelligence_systems.py", "check_combined_code_intelligence_systems"),
    # ── GRAPHABLE / ENRICHABLE / VERIFIABLE SYSTEM CONTRACT: every review/code-intelligence packet must carry deterministic evidence, graph context, blast-radius hints, verification lanes (deterministic + hybrid + nondeterministic + human/owner where needed), context-maximization and confusion-reduction policy; proofs, not model prose, promote ──
    ("scripts/check_graphable_enrichable_verifiable_system.py", "check_graphable_enrichable_verifiable_system"),
    # ── GEV ADVERSARIAL INTERROGATORIES: reusable corner-case families + interrogatory templates + reviewer skill frames (graph cartographer, contract skeptic, data-shape normalizer, verification prosecutor, adversarial breaker, UX/product mapper) are machine-readable and attached to hybrid review packets by kind; candidate-only, proof-gated ──
    ("scripts/check_gev_adversarial_interrogatories.py", "check_gev_adversarial_interrogatories"),
    # ── NORTH-STAR GAP CLOSURE LOOP: governed command/prompt/docs for the remaining gaps (repo-wide naming, blast-radius graph, disagreement adjudication, primitive derivation, registry vectorization/search, promotion gate); writes resumable .agent state and routes one bounded next_gap at a time; never serves truth ──
    ("scripts/check_north_star_gap_closure_loop.py", "check_north_star_gap_closure_loop"),
    # ── REQUIRED-FUNCTIONALITY GRAPH (owner 2026-06-27): _repos/shared-backend-components/architecture/required_functionality.json declares 'page X requires functionality Y' as nodes with deterministic check-edges to the code; satisfied requirements are REGRESSION-GUARDED (gate fails if their code vanishes / a forbidden anti-pattern returns), gap requirements are the live remediation backlog from the wiring review; resolves every edge by grep over the source, zero LLM; never serves truth ──
    ("scripts/check_required_functionality.py", "check_required_functionality"),
    # ── SUBSTRATE LAYERS: the systems-layer reconciliation map (owner's proposed 'missing layers' vs what ALREADY exists + real gap + the Foundational Law); keeps the 'already exists' claim honest (every cited asset must exist on disk) so we close gaps instead of rebuilding; never serves truth ──
    ("scripts/check_substrate_layers.py", "check_substrate_layers"),
    # ── MODEL INDEX (best+cheapest+effective, FRESHNESS-governed): unified index of model cost + live endpoint + download location + quality; selector picks the cheapest FRESH model within a quality floor; stale model facts are HELD OUT and never selected until re-verified (kept-up-to-date is the wedge); never serves truth ──
    ("scripts/check_model_index.py", "check_model_index"),
    # ── DESCENT METHOD CATALOG: for every improvement dimension (all 17 descent axes) the concrete METHODS to accomplish it (e.g. reduce skill tokens via compression / redundant-text dedupe), each grounded in a VARIETY of researched candidate modules; license class governs vendorability (copyleft/source-available/unstated/unverified = behind-a-port); generated how-to map; discovery≠trust, never serves truth ──
    ("scripts/check_descent_method_catalog.py", "check_descent_method_catalog"),
    # ── SELF-OPTIMIZING capability unit (the flagship): a capability MEASURES itself + auto-applies the best GOVERNED method per dimension (compress tokens / distill to a deterministic rule or cheaper model / bind a fragile fact to its source / route to the cheapest capable model), emitting a real before→after receipt; lossless + within-policy + accuracy-floored; HONEST when a task can't be made deterministic; deterministic + idempotent; never serves truth ──
    ("scripts/check_self_optimizing_unit.py", "check_self_optimizing_unit"),
    # ── PITCH DECK (slides/demo for technical + investors): generated from _repos/shared-backend-components/architecture/teleon_pitch_deck.json with EVERY number computed live (proof count, the actual self-optimizing receipt, method/profession/standards counts); consistent single-source language; no hand-typed metrics; carries the governance + honest-gap language; serves_truth=false ──
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
    # ── FRAMEWORK INTEGRATION (both directions): EXPORT a governed capability as a native tool for MCP/OpenAI/Anthropic/LangGraph/CrewAI/AutoGen (carrying its receipt + serves_truth=false); WRAP a framework agent as a governed CANDIDATE behind a port (sandboxed, never truth); Teleon imports no framework (emits/consumes specs); never serves truth ──
    ("scripts/check_framework_integration.py", "check_framework_integration"),
    # ── MODALITY CAPABILITY CATALOG: AI-startup capabilities across document/image/text/video/audio/multimodal reverse-engineered into input→output pipelines that all share a DETERMINISTIC spine wrapping an irreducible MODEL CORE; each a tunable cascade (run the spine cheap, escalate to cheapest-capable model core); fully deterministic only where there is no model core; discovery≠trust, never serves truth ──
    ("scripts/check_modality_capability_catalog.py", "check_modality_capability_catalog"),
    # ── DEFAULT BRAIN POLICY: the cheap Ollama brain (GLM-5.2 orchestrator/distiller-judge, Kimi-k2.7-code reviewer) is the DEFAULT, verifiably cheaper than its frontier escalation (cross-checked vs the model index), which fires only when a confidence/quality bar fails — the descent applied to the brain itself; auth via OLLAMA_API_KEY env ref (value gitignored); never serves truth ──
    ("scripts/check_default_brain_policy.py", "check_default_brain_policy"),
    # ── DOCUMENT CASCADE DEMO (fully-working local page): write in a capability (schema + doc profile + key) and the REAL document→schema cheapest-that-meets cascade runs (stdlib http.server) — cheapest path, per-step cost, deterministic-vs-LLM, savings vs frontier, missing fields reported honestly; in-process proof (no port); never serves truth ──
    ("scripts/serve_document_cascade_demo.py", "serve_document_cascade_demo"),
    # ── INPUT ACQUIRE (generalize across input types): pdf/office/text/email+attachments/web-page/rss/social/image/audio each normalized by a cheapest-first acquire ladder (deterministic where possible; model only when forced; web/social via LEGITIMATE paths, never scraping) then fed the SAME extraction cascade; combined acquire+extract receipt; never serves truth ──
    ("scripts/check_input_acquire.py", "check_input_acquire"),
    # ── CASCADE MEASUREMENT (cheapest-that-meets is MEASURED, not assumed): each extract method scored vs offline ground-truth fixtures; per field the cascade picks the cheapest method whose MEASURED accuracy clears the confidence floor; the floor is a live A/B (cheap_llm below it, frontier above it, cost rises with the bar); accuracy computed from fixtures (no hidden table); missing fields honest; never serves truth ──
    ("scripts/check_cascade_measurement.py", "check_cascade_measurement"),
    # ── SCHEMA TEMPLATES (extraction is USER-DEFINED; templates are OPTIONAL): any field the user writes runs the real cascade; code/DB showcase templates are a chooser that prefills an editable schema box (employment_agency single-sourced from the cascade, no duplicated field list); one parser grammar; chosen templates round-trip render→parse; never serves truth ──
    ("scripts/check_schema_templates.py", "check_schema_templates"),
    # ── FLYWHEEL PARALLELISM (throughput): the flywheel runs proof self-tests concurrently (FLYWHEEL_WORKERS, default=cores capped 16; ~5x faster ticks) and the shared portfolio-site build writes ATOMICALLY (temp + os.replace), so concurrent builders never expose a half-written file; regression-guards the race the speedup surfaced (14 check_portfolio_* siblings rebuild the same dist files); never serves truth ──
    ("scripts/check_flywheel_parallelism.py", "check_flywheel_parallelism"),
    # ── CONTEXT-ENGINEERING PATTERNS (governed intake of LangChain's MIT deep-agents course): plan/offload/delegate/summarize captured as CANDIDATE techniques mapped to our descent axes + worker buckets — learn-from (runtime is the foil, never vendored/executed), every output candidate≠truth, summarization bound by the lossless law; wedge = we VERIFY the managed context, not just manage it; never serves truth ──
    ("scripts/check_context_engineering_patterns.py", "check_context_engineering_patterns"),
    # ── PARALLEL DEV FLEET (faster cycles, no same-file edits): Claude Code + Ollama agents run in parallel, each in its OWN git worktree (physical isolation) owning a DISJOINT file set; the proof registry + count token are SERIALIZED (owned by no lane, merged one at a time); heterogeneous brains by the unbounded->bounded policy (ollama for narrow/deterministic lanes, claude for design); pure dry-run plan, never serves truth ──
    ("scripts/check_parallel_dev_lanes.py", "check_parallel_dev_lanes"),
    # ── PORTFOLIO CONNECTION MAP (memorialize how everything connects): all 22 Open*Hubs (9 live + 13 private-bench) mapped to the core products (Baltor, Teleon) they FEED (context packs / harnesses / model info / methods / receipts), with the Amazon internal-infra->public-revenue stage per hub; coverage cross-checked against products.js so no surface is omitted; renders a Mermaid diagram; dependency law hub->core never reverse; never serves truth ──
    ("scripts/build_portfolio_connection_map.py", "build_portfolio_connection_map"),
    # ── DESCENT ATTEMPT STORE (the BRAIN: smarter over time): canonical append-only, lossless store of EVERY unbounded->bounded attempt — keeps failures + losers as training NEGATIVES; doubles as the meta-learner memory (best_strategy_for computed from records) and the training corpus (features+label+reward) for a descent-policy model; internal infra now, OpenDistillationHub public-revenue candidate later; never serves truth ──
    ("scripts/check_descent_attempt_store.py", "check_descent_attempt_store"),
    # ── CATALOG DESCENT DEMO (convert skills/tools -> cheaper bounded versions, WIRED TO THE BRAIN): runs the unbounded->bounded descent over all 16 real capability-catalog entries and records EVERY attempt into the DescentAttemptStore — bounding the catalog AND producing the training corpus + meta-learner memory in one run; full caps -> determinism 1.0 (llm_to_rule), partial -> cheap model tier (model_downgrade); idempotent; never serves truth ──
    ("scripts/convert_catalog_demo.py", "convert_catalog_demo"),
    # ── PREFERENCE PROFILE (efficient = the USER's multi-objective trade-off): a user-set PreferenceProfile (weights over cost/latency/token_burn/determinism/freshness + hard constraints) drives which bounded implementation Teleon picks — cost-first->cheapest, latency-first->fastest, determinism-required->deterministic, impossible-constraint->honest no-pick; generalizes the single-objective selector; never serves truth ──
    ("scripts/check_preference_profile.py", "check_preference_profile"),
    # ── REGISTRY DESCENT (converter spans ALL capability-bearing registries -> the brain): runs the unbounded->bounded descent across the modality catalog + the implementation registry + the tunable-task catalog and records every attempt into the DescentAttemptStore, so the brain learns from more than one registry (more training data); model/context/harness/skill registries are the selection substrate, not items to bound; idempotent; never serves truth ──
    ("scripts/check_registry_descent.py", "check_registry_descent"),
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
    # ── PurposeTask: PurposeTaskSpec contract (declared by intent; the provisioned PoC spec is contract-bound) ──
    ("scripts/check_purpose_task_contracts.py", "check_purpose_task_contracts"),
    # ── OCTS CTS-0: PurposeTaskSpec is a conformant Open Capability Task; runtime-class vocabulary well-formed + cloud-defer-safe ──
    ("scripts/check_octs_conformance.py", "check_octs_conformance"),
    # ── PurposeTask dashboard: ONE truth model → staff (full) + customer (allowlist-redacted) views; no staff-only/secret/cross-tenant leak ──
    ("scripts/check_purpose_task_projection_redaction.py", "check_purpose_task_projection_redaction"),
    # ── Adaptation ladder L0-L5: MEANS auto-promote on gates; ENDS/forbidden/unknown never auto (core invariant, deny-by-default) ──
    ("scripts/check_adaptation_ladder.py", "check_adaptation_ladder"),
    # ── pre-seed Teleon with capability-DEFINED units across the full execution-style spectrum (template → deterministic → det+tool → skill → tool → skill+tool → model → open-ended), each a PurposeTaskSpec classified by the real escalation ladder + provisioned by capability, with a non-det → det descent for cost ──
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
    # ── capability seeder: discovered candidates (from public skills/tools/MCP/plugin sources) normalize into governed CapabilityCandidate, pass a cheap gap/lift SCREEN (rejects retained, not dropped), and each is WALKED non-det -> most-det on the evolution-graph engine (a documented deterministic fork covering the estimated fraction, residual routed to the preserved model); discovery != trust — nothing auto-active, nothing serves truth ──
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
    # ── Portfolio dependency LAW: HoldCo owns Teleon (runtime SaaS) + Baltor (applied, tenant of Teleon) + OpenHubForAI (open ecosystem); Baltor→Teleon→OHH only, never reverse; Teleon never imports Baltor; migration debt tracked ──
    ("scripts/check_portfolio_dependency_law.py", "check_portfolio_dependency_law"),
    # ── Company boundary model: HoldCo ContextIsEverything owns no runtime/customer-data; data-separation (Baltor truth owned by Baltor alone, forbidden elsewhere); surfaces+integrations agree with the import law; no shared prod DB/god token; brand risk registered ──
    ("scripts/check_company_portfolio_boundaries.py", "check_company_portfolio_boundaries"),
    # ── Teleon Lift: import existing cloud functions + K8s → ImportedWorkload → PurposeTaskDraft (always human-gated) + legacy=rollback-baseline + read-only-first 6-mode adoption ladder w/ managed gate; secrets stripped; CTS-1-bindable; offline seams; deterministic ──
    ("scripts/check_teleon_lift.py", "check_teleon_lift"),
    # ── Portfolio websites (ContextIsEverything · Teleon · Baltor · OpenHubForAI): rubric-gated static sites built from one source; brand boundaries + quality>=90 + security + customer readiness + reuse + distinct + technical-launch + trycloudflare discipline + honest screenshots + full-stack table ──
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
    # ── Command/work I/O: the durable FleetLedger's records conform to the typed work-I/O contracts (WorkItem=CapabilityTask, idempotent enqueue, atomic WorkerClaim, AckNackReceipt, DeadLetterEntry); projectors in _repos/teleon/backend/src/teleon/io are pure ──
    ("scripts/check_shared_command_work_io.py", "check_shared_command_work_io"),
    # ── Event I/O: internal EventBus events project to CloudEvents 1.0 (EventEnvelope / CloudEventProjection) — type in EVENT_KINDS, correlation_id required, deterministic (source,type,seq) id, secrets redacted; pure projector in _repos/teleon/backend/src/teleon/io ──
    ("scripts/check_shared_event_io.py", "check_shared_event_io"),
    # ── Teleon EGRESS GRAPH: outbound worker fetch/search/tool calls become redacted append-only observations projected into a tenant/query-scoped graph (query->egress->destination plus worker/tool/response digest); searchable by query/worker/destination; output is evidence only, never truth. ──
    ("scripts/check_teleon_egress_graph.py", "check_teleon_egress_graph"),
    # ── Teleon EGRESS ENFORCEMENT: covered workers + live inference route outbound HTTP through EgressClient; raw HTTP isolated to approved transports; route decisions/attempts ledgered; blocked routes don't fall through; evidence remains truth-free. ──
    ("scripts/check_teleon_egress_enforcement.py", "check_teleon_egress_enforcement"),
    # ── Teleon EXECUTION ENVIRONMENT TAXONOMY: every runtime class has pre-autotune defaults, policy preferences, route preferences, resource/lifecycle/SLA refs, local equivalent, and no-truth/autotune boundary locks. ──
    ("scripts/check_teleon_execution_environment_taxonomy.py", "check_teleon_execution_environment_taxonomy"),
    # ── Baltor main UI: the animated Context Engine hero + its canonical six-stage language wired into the SPA (overview + /engine), single-sourced from _repos/baltor/frontend/stages.json; canvas/raf; reduced-motion; offline; no Oracle copy ──
    ("scripts/check_baltor_engine_hero_ui.py", "check_baltor_engine_hero_ui"),
    # ── Baltor SPA implements the canonical Claude-Design branded-house system (dir-d teal scope, Hanken Grotesk + IBM Plex Mono, shared card primitive + scale) while preserving our own additions; design spec persisted in-repo ──
    ("scripts/check_baltor_design_system.py", "check_baltor_design_system"),
    # ── OpenBenchmarkHub is real: contracts + the first first-party benchmark (Baltor CFPB Context Governance, anchored to real demo facts) + CI-derived benchmark opportunities (candidates); a benchmark result is evidence-not-authority (no benchmark gate in the promotion path) ──
    ("scripts/check_openbenchmarkhub_core.py", "check_openbenchmarkhub_core"),
    # ── Benchmark Lab adapter catalog (edge-first W7): the owner's 240-track external benchmark inventory becomes a typed demand registry (5 families, priority-40, A0..A8 comparison arms, L1..L7 disclosure-depth ladder, scorecard metrics incl. memory + token axes). Every track candidate=true/serves_truth=false with adapter_state=unbuilt — names are UNVERIFIED intake until an adapter is built + verified; a benchmark score is evidence, never promotion authority ──
    ("scripts/build_benchmark_lab_adapter_catalog.py", "build_benchmark_lab_adapter_catalog"),
    # ── Primitive saturation + savings tracker (the self-aware generation loop, owner 2026-07-01): charts VERIFIED primitive count per area (primitive_kind) x lane x industry against measured savings (context 486x / tokens / memory / speed from primitive_lift_benchmark) and detects PLATEAU via per-area duplicate pressure — productive/watch/saturated/cold bands -> recommendations (keep_mining / sprout_diversity / move_on / open_new_frontier) that re-weight generation. Report is evidence (candidate=true/serves_truth=false), never promotion authority ──
    ("scripts/track_primitive_saturation_and_savings.py", "track_primitive_saturation_and_savings"),
    # ── Rollout savings extrapolation (owner 2026-07-01): transparent SOURCED estimate (low/central/high bands) of what the primitive-search harness saves across N developers in tokens -> $ -> kWh -> liters water -> kg CO2. Honest model: blended reduction = context_share x reuse-eligible (~45%), NOT the 486x best-case slice compression. candidate=true/serves_truth=false; effective_reduction is the key uncertainty, override from the A/B simulation aggregate ──
    ("scripts/extrapolate_rollout_savings.py", "extrapolate_rollout_savings"),
    # ── Primitive-kind family catalog (edge-first W2/W5/W10): 60 typed primitive KINDS the factory + template extractors draw from — runtime shapes (api/service/webhook/queue/cron/cli/k8s/terraform) + owner 2026-07-01 expansion: algorithm/function families (sort/graph/optimization/fuzzy/near-dup/vector-search/function-chain, source-backed contracts NOT copied code), tools-we-build-and-use (rapidapi/browser-automation/web-scraper/search-provider/query-lattice), and visualization/media (chart/graph-network/image/video processing, pypi scan, seeded-vs-probabilistic genai image/video w/ safety+provenance receipts). Every family candidate=true/serves_truth=false; deterministic vs probabilistic split explicit; all-paths doctrine = multiple runtime_targets + adapter_mutators per family ──
    ("scripts/check_aidevexplorer_primitive_kind_family_catalog.py", "check_aidevexplorer_primitive_kind_family_catalog"),
    # ── Competitive provider mappings: infra/agent companies map to ports as governed candidates (Fireworks = real inference-gateway candidate w/ secret + governed fallback; Crusoe/Nscale execution backends need local-equivalent; Cursor/Cognition sandboxed, output not truth); none active or a direct import ──
    ("scripts/check_competitive_provider_mappings.py", "check_competitive_provider_mappings"),
    # ── Inference Gateway REDTEAM: the shared LLM plane fails safely — fallback recorded (never silent), receipt never 'served'/output never truth, offline local-stub provenance + no raw-key leak, ClawLess!=endpoint, shared-key quarantine, free!=customer-sensitive, secret-refs only, numeric routing ──
    ("scripts/check_inference_gateway_redteam.py", "check_inference_gateway_redteam"),
    # ── Inference Gateway routes on NUMERIC codes + node-ids, not brittle display strings (rename-safe; capability-code change drives eligibility; no display branching in select_provider/_eligible) ──
    ("scripts/check_no_brittle_model_string_logic.py", "check_no_brittle_model_string_logic"),
    # ── Object preference coverage: key object families declare a model preference BY REFERENCE (ObjectShell.model_preference_ref -> InferencePreference), never inline; the ref resolves through the gateway ──
    ("scripts/check_objects_have_inference_preferences.py", "check_objects_have_inference_preferences"),
    # ── /api/inference PROJECTION (api_projection): projection-only read views of the LLM plane (providers/model-graph/free-endpoints/preferences/health/receipts + local resolve); numeric codes, has_secret_ref bool only, NO raw key/secret value, offline-honest health, ErrorEnvelope; every declared route binds to a real callable ──
    ("scripts/check_inference_api.py", "check_inference_api"),
    # ── Generated OpenAPI + AsyncAPI specs (_repos/shared-backend-components/docs/contracts/*.generated.json via _repos/shared-backend-components/scripts/build_contract_specs.py): drift-free machine projection of contract_registry — every registered route covered (incl. /api/inference), every command/event/log channel covered, every $ref resolves, no raw keys, every op projection-only + ErrorEnvelope ──
    ("scripts/check_shared_openapi_asyncapi_specs.py", "check_shared_openapi_asyncapi_specs"),
    # ── Shared LLM Plane SERVED end-to-end: scripts/api_inference_handler answers every /api/inference route (errors=ErrorEnvelope); structured-local output is a CANDIDATE never truth (ModelInvocationReceipt); admin server delegates GET+POST; read-only UI (_repos/baltor/frontend/inference-plane.html) consumes it; no secret-value leak in any response ──
    ("scripts/check_inference_api_handler.py", "check_inference_api_handler"),
    # ── Shared LLM Plane fires INSIDE the connected pipeline: run_full_pipeline emits governed inference.requested → inference.completed (receipt-backed, is_truth=false, Enhancement stage) visible on /dashboard; the DETERMINISTIC answer stays the served truth (LLM candidate never promoted); no secret leak ──
    ("scripts/check_inference_in_pipeline.py", "check_inference_in_pipeline"),
    # ── ADVERSARIAL: every attack on the pipeline inference wiring fails safely — no SDK/raw-key in the governed path, fallback recorded (never silent), output never promoted to truth, run_full_pipeline runs with ZERO network (socket blocked), model output never reaches a served surface, ungoverned event kinds rejected, governance gates still run ──
    ("scripts/check_inference_pipeline_redteam.py", "check_inference_pipeline_redteam"),
    # ── Shared LLM Plane UI projection: _repos/baltor/frontend/inference-plane.html is reachable (/inference-plane, no dead link), consumes /api/inference/*, declares output candidate-not-truth, labels providers local/external w/ key-as-ref (no value), no secret leak; the Live Ops dashboard links it + renders inference.* events as candidate-not-truth (no dashboard truth) ──
    ("scripts/check_inference_ui.py", "check_inference_ui"),
    # ── Baltor Guided Demos index (Claude Design handoff → _repos/baltor/frontend/guided-demos.html, served /guided-demos): branded-house oh-* design; 14 governed data-examples each showing served-answer + held-out-contradiction (never served); ONLY the runnable CFPB demo is labelled live (links to /consume), rest honest previews — no overclaiming, no dead design-page links, not-advice disclaimer, no secret leak ──
    ("scripts/check_baltor_guided_demos.py", "check_baltor_guided_demos"),
    # ── Anti-rot guard for the orientation doc: _repos/shared-backend-components/docs/CURRENT-STATE.md carries NO frozen flywheel proof-count (no-magic-values — reference the live signal), points to baltor_flywheel, and every concrete repo path it cites resolves (no dangling source handles) ──
    ("scripts/check_current_state_freshness.py", "check_current_state_freshness"),
    # ── ADVERSARIAL: every attack on the Shared I/O + Resource Spine fails closed — raw secret/DSN rejected (resource spec) or redacted (event), temp/persistent/cloud guards hold, events need correlation_id + known kind, work needs a lease (nack never silent), inference stores only the input hash, no artifact leaks a secret ──
    ("scripts/check_shared_io_resource_redteam.py", "check_shared_io_resource_redteam"),
    # ── Shared LLM Plane COMPATIBILITY: Ollama (cloud + local) + the free-but-limited tools (Groq/Gemini/OpenRouter/Cerebras/…) are governed CANDIDATE provider-graph nodes — secret-by-ref, candidate-not-active, customer-sensitive disallowed by default, shared-key bypass quarantined; inference degrades to the local stub offline (fallback recorded, output never truth) ──
    ("scripts/check_ollama_free_limited_compatibility.py", "check_ollama_free_limited_compatibility"),
    # ── Provider-adapter ABSTRACTION: one governed base class (InferenceProviderAdapter) with multiple API-method subclasses (deterministic_stub/openai_compatible/ollama_native/anthropic_messages), resolved by CONFIG (node.adapter_style) + swappable with no code change, byte-consistent with the gateway, SDK-free at import, secret-by-ref, degrading to ProviderUnavailableResult offline ──
    ("scripts/check_inference_provider_adapters.py", "check_inference_provider_adapters"),
    # ── ObjectShell conformance migration (LOSSLESS): ContextArtifact migrates to the canonical 14-section shell via the existing compose_object_shell — original preserved verbatim in payload (rehydratable to byte-identity), content_hash + handles carried, migration recorded in lineage, candidate status (no truth); manifest tracks remaining families as honest backlog ──
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
    # ── Inference I/O: InferenceRequest (input hashed, never raw text) + ModelRouteDecision (governed-fallback trail, recorded) project the live OIPS gateway; receipt never 'served'; pure projectors in _repos/teleon/backend/src/teleon/io ──
    ("scripts/check_shared_inference_io.py", "check_shared_inference_io"),
    # ── Eval/promotion I/O: ratified to the existing parallel-path engine (promotion always reversible by contract; engine proofs registered) + the new HumanApprovalReceipt gate so BOUNDARY EXPANSION requires approved human sign-off ──
    ("scripts/check_eval_promotion_io.py", "check_eval_promotion_io"),
    # ── Fragile Context Atlas: governed registry of fragile-context packs by domain x failure-mode (the strategic wedge) — REUSES FragilityMetadata.volatility_class + CanonicalFact.status + vocabularies/industries.yaml + the sales public-claim policy; ACTIVE packs are a bijection with the 14 live guided demos (no overclaim), CANDIDATE packs are honest backlog (never served); no vendor named; every time-fragile pack has a refresh policy ──
    ("scripts/check_fragile_context_atlas.py", "check_fragile_context_atlas"),
    # ── Fragile Context Atlas REDTEAM (negative proof): feeds the SAME validator (find_violations) deliberately-broken copies of the real atlas — vendor accusation, pack-as-truth, missing source-authority/held-out, missing refresh, leaked credential, served contradiction, benchmark/LLM cited as authority, demo overclaim, candidate-as-active — and asserts each guardrail fires; control proves the real atlas is clean ──
    ("scripts/check_fragile_context_atlas_redteam.py", "check_fragile_context_atlas_redteam"),
    # ── OpenContextHub surfaces the atlas: the OpenContextHub site's fragile-context section is GENERATED from _repos/shared-backend-components/architecture/fragile_context_atlas.json via portfolio_lib (cannot drift) — lock-step domain/mode counts + cfpb/sanctions/tariff served+held verbatim, the 'Run a Fragile Context Audit' CTA resolves to the section, reference-not-truth governance, no vendor named, built artifact matches ──
    ("scripts/check_opencontext_fragile_atlas_page.py", "check_opencontext_fragile_atlas_page"),
    # ── Fragile-context audit OFFERS: _repos/shared-backend-components/docs/sales/fragile-context-audit-offers.md is GENERATED from the atlas (one catalogued audit per distinct sales_audit_offer), in lock-step (regenerate-and-compare), producing the existing schemas/sales/* contracts under the public-claim safety gate (draft-only, appears/requires-review, authorized inputs, no named target without legal review); no vendor named; 10-field audit output ──
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
    # ── Agent-runtime layer REDTEAM: one shared find_violations() validator reused by a CONTROL (real catalog + real dispatch outcomes + real module source = clean) AND 9 attacks that MUST be caught — candidate serves_truth=true / candidate imported|executed=true / raw key in a card / agent output→truth / open-ended agent provisioned onto a generic cloud function w/o an allow_generic proof / crash-instead-of-structured-unavailable / unknown-runtime-not-degraded / module imports src.baltor / a second active runtime. Owner-proven generic override is allowed. Hardens _repos/teleon/backend/src/teleon/agents (agents PROPOSE, never serve truth) ──
    ("scripts/check_agent_runtime_layer_redteam.py", "check_agent_runtime_layer_redteam"),
    # ── Environment + Reward Spine RESEARCH REGISTRY (P1): Repo2RLEnv / Harbor / OpenEnv / ORS / RepoLaunch / SWE-bench / Terminal-Bench / R2E-Gym / SWE-smith / SWE-Gym / NeMo Gym cataloged as CANDIDATE|REFERENCE (NEVER active). Enforces: status never active; any Docker/network/LLM/key-gated entry carries a local_equivalent + proof_to_promote ladder; provenance/license tracked; no raw keys; Repo2RLEnv = repo_to_rl_env_generator (not LLM endpoint / coding agent); benchmark result = EVIDENCE, never promotion authority; output != truth. Converts the Repo2RLEnv due-diligence into governed infrastructure ──
    ("scripts/check_agent_environment_research_registry.py", "check_agent_environment_research_registry"),
    # ── Teleon competitive/runtime LANDSCAPE (P9 competitive intel): repos that do SLICES of Teleon (ARK/kagent/AgentScope-Runtime/agent-sandbox/Temporal/DBOS/Dapr/Hatchet/Inngest/Trigger.dev/Ouroboros/agentregistry) cataloged as substrate-adapter-candidate / sandbox-adapter / inspiration / adjacent-registry. Enforces: none IS the Teleon runtime (0 active; Teleon's own reference runtime + CapabilityTask standard stay the stable layer); every durable/execution substrate carries a do_not_adopt_as_primary guard (no second durable ledger/worker framework); Teleon differentiation articulated per competitor; positioning = control plane ABOVE, not another framework. Answers "any repos that do what Teleon does?" as governed infra ──
    ("scripts/check_teleon_runtime_landscape.py", "check_teleon_runtime_landscape"),
    # ── Open*Hubs BACKEND candidate registry (research→governed): which OSS repos power each hub's backend components (MCP registry/vector/hybrid-search/eval-harness/benchmark/compression/skill/tool/registry-service). Key finding: OpenMCPHub wraps the OSS official modelcontextprotocol/registry as a compatible sub-registry (reused across 4 hubs). discovery≠trust; candidate≠active; benchmark=evidence; output≠truth ──
    ("scripts/check_openhubs_backend_registry.py", "check_openhubs_backend_registry"),
    # ── Teleon-adjacent EXTENDED landscape (deep due-diligence): Restate/Prefect/Kestra/Windmill/Flyte/Ray/Modal/Cloudflare-Workflows = safe_to_wrap substrate adapters behind ExecutionProviderPort (do_not_adopt_as_primary); LangGraph-Platform/Cloudflare-Agents/Bedrock-AgentCore/Vertex-Agent-Engine = positioning_threat (differentiate on capability-contract+eval-gated-promotion+rollback+truth-boundary); Temporal+LangGraph 2-layer = thesis_strengthening. None IS the Teleon runtime ──
    ("scripts/check_teleon_adjacent_extended.py", "check_teleon_adjacent_extended"),
    # ── Environment + Reward Spine P0 CONTRACTS: schemas/environments/{EnvironmentRunRequest,EnvironmentRunResult,EnvironmentRunReceipt,RewardSpec,RewardResult,EnvironmentProviderNode,RewardProviderNode} registered in contract_registry; serves_truth/is_truth pinned const false (a run/score is EVIDENCE, never promotable/served truth); provider nodes candidate-first ──
    ("scripts/check_agent_environment_contracts.py", "check_agent_environment_contracts"),
    # ── Environment + Reward Spine P2: local EnvironmentProviderPort + RewardProviderPort + LocalEnvironmentProvider (offline/deterministic, no Docker/key, writes EnvironmentRunReceipt with input/output hashes, serves_truth=False) + deterministic RewardRunner (deterministic_check kinds) ──
    ("scripts/check_local_environment_provider.py", "check_local_environment_provider"),
    # ── Environment + Reward Spine P3: environment.baltor.cfpb_context_governance.local@v1 — a GOOD "10 business days" answer with a source handle passes; a BAD answer leaking the held-out "30 days" FAILS held_out_absent; output never truth; Teleon never imports Baltor ──
    ("scripts/check_baltor_context_environment.py", "check_baltor_context_environment"),
    # ── Agentic-bot plane P1A governed run contracts: schemas/agents/{AgentRunRequest,Result,Receipt,Tool/Skill/Sandbox/MemoryPolicy,ProviderUnavailableResult} — serves_truth/consumable/cross_tenant const false; secret_refs env:// only; agent-created skills const "candidate"+eval-before-active; sandbox deny-by-default. Agents PROPOSE, never truth ──
    ("scripts/check_agentic_bot_contracts.py", "check_agentic_bot_contracts"),
    # ── Capability-binding / IfC landscape (answers "tools that do capability/contract programming abstracting cloud-fn/K8s"): Nitric/Wing/Encore/Klotho(archived)/Score/Radius/Kratix/Crossplane/OAM-KubeVela/Knative/KEDA/Serverless-Framework cataloged as CapabilityTask BINDING TARGETS (Kratix/Radius/Score/Nitric closest). None owns the eval-gated LIFECYCLE → all are binding/execution adapters; Teleon is the control plane ABOVE. 0 active; license_confidence honest (Klotho archived, SF v4+ proprietary) ──
    ("scripts/check_capability_binding_landscape.py", "check_capability_binding_landscape"),
    # ── CapabilityTaskBindingProvider (realizes the binding layer): a CapabilityTask binds to local_function@v1 NOW (delegates backend choice to execution_backend_selector — open-ended agents hard-guarded off generic cloud functions) and to Nitric/Score/Temporal/Knative/KEDA/Kratix LATER by policy; candidate targets return BindingUnavailableResult (never imported/executed, env:// ref, backend_would_be shown); binding output serves_truth=False; Teleon never imports Baltor. Author never writes cloud-fn/K8s code ──
    ("scripts/check_capability_binding_provider.py", "check_capability_binding_provider"),
    # ── Teleon AGENT CAPABILITY GATEWAY P0 contracts (Teleon serves AI agents as customers): schemas/agents/{AgentCapabilityConsumer,Card,RunRequest,RunResult,Receipt,BoundaryExpansionRequest} — RunResult.serves_truth const false; BoundaryExpansionRequest status const "pending_human_approval" + auto_applied const false (agents can't self-expand); Card deterministic_first + llm_fallback_allowed + receipt_required ──
    ("scripts/check_teleon_agent_gateway_contracts.py", "check_teleon_agent_gateway_contracts"),
    # ── Teleon Agent Gateway P1 LOCAL runner: an agent consumer lists + runs DETERMINISTIC capabilities (utility.hash / cfpb.deadline.verify / json.schema.validate / tariff.hs.classify) → compact AgentCapabilityRunResult + receipt (runtime_path="deterministic", tokens_saved_estimate>0, serves_truth=False); deterministic-first token ladder; LLM fallback owner-gated (never in self-test); delegates to bind_capability_task; Teleon never imports Baltor ──
    ("scripts/check_teleon_agent_gateway_local.py", "check_teleon_agent_gateway_local"),
    # ── Teleon Agent Gateway P5 REDTEAM: control clean + 8 attacks caught — raw-secret-read / forbidden-tool / boundary-auto-apply / weakened-success-criteria / llm-fallback-without-policy / output-as-truth / raw-corpus-not-compact-receipt / benchmark-score-as-truth ──
    ("scripts/check_teleon_agent_gateway_redteam.py", "check_teleon_agent_gateway_redteam"),
    # ── Teleon Agent Gateway: runtime AgentBoundaryExpansionRequest reconciled to its schema (capability_id/requested_change/justification; status const pending_human_approval + auto_applied False preserved; legacy aliases accepted) — a runtime boundary-expansion now validates against AgentBoundaryExpansionRequest ──
    ("scripts/check_teleon_agent_gateway_boundary_schema_match.py", "check_teleon_agent_gateway_boundary_schema_match"),
    # ── Teleon Agent Gateway P2 MCP PROJECTION: the gateway projected as EXACTLY 5 stable MCP tools (list/describe/run/get_receipt/request_boundary_expansion); projection-only over AgentCapabilityGateway (no second gateway, no eval/exec, fixed dispatch table); compact cards/results (secret/backend/runtime fields scrubbed); serves_truth False; unknown tool → structured error ──
    ("scripts/check_teleon_agent_gateway_mcp_projection.py", "check_teleon_agent_gateway_mcp_projection"),
    # ── Teleon Agent Gateway P4 Baltor TRUTH BOUNDARY: context.governed_answer.evidence returns EVIDENCE (serves_truth False, status candidate) with held_out kept SEPARATE from the served output + source handles + governance marker {served_truth_owner:baltor, teleon_role:evidence_only}; Teleon never imports Baltor ──
    ("scripts/check_teleon_agent_gateway_baltor_boundary.py", "check_teleon_agent_gateway_baltor_boundary"),
    # ── Stateful Swarms / blackboard RESEARCH catalog (Irys due-diligence → governed infra): stateful_swarm.irys@research_candidate (MIT verified; Harvey-LAB claims unverified-until-reproduced; Python 3.12+/install/keys → never active, no truth authority) + blackboard/agent-memory landscape (graphiti/letta/langgraph-checkpoint/autogen-mem0/seekdb) as candidates behind local_sqlite@v1; benchmark=evidence-not-promotion; blackboard output≠truth ──
    ("scripts/check_stateful_swarm_provider_catalog.py", "check_stateful_swarm_provider_catalog"),
    # ── Governed blackboard P0 contracts (durable typed analytical state; Teleon runs, Baltor governs): schemas/blackboard/{Blackboard,Entry,Signal,Observation,Gap,Calculation,Analysis,Synthesis,SourceRef,WorkerReceipt,ConvergenceReport,CompressionReport,GovernedBlackboardEntry} — serves_truth const false on Entry/Analysis/Synthesis/Governed; Observation source_refs required+non-empty; Synthesis keeps held_out+source_handles; CompressionReport pins source_handles_preserved+held_out_preserved const true ──
    ("scripts/check_blackboard_contracts.py", "check_blackboard_contracts"),
    # ── LOW-COST (paid) LLM endpoint registry — cheaper Chinese/China-adjacent routes (DeepSeek/Qwen/SiliconFlow/Z.AI/MiniMax admit_first; Baidu/Tencent/Volcengine/StepFun/Moonshot probation) as a DISTINCT lane from free/*: cost_class lowcost_usd, candidate≠active, secrets vault:// refs only, output≠truth, and the load-bearing DATA-CLASS/JURISDICTION guard — low-cost/China lanes carry ONLY public+internal_non_sensitive, NEVER customer/regulated/secrets/confidential ──
    ("scripts/check_lowcost_llm_endpoint_registry.py", "check_lowcost_llm_endpoint_registry"),
    # ── SkillClaw → DETERMINISTIC TOOL promotion (Determinism Factory applied to skills): SkillClaw=research_candidate (MIT, WIP, no truth authority); 7-rung ladder observation→draft-skill→verified-skill→tool-candidate→deterministic-tool→certified→retired; deterministic-tool standard (no_llm/no_rng/no_wall_clock + same_output_hash + sandbox + human-approval + sbom/signed); tools never auto-published; skills mined only from public/synthetic/redacted traces; distillation lossless ──
    ("scripts/check_skill_to_tool_promotion.py", "check_skill_to_tool_promotion"),
    # ── TokenTamer → CONTEXT COMPRESSION (Lossless-law governed): tokentamer=research_candidate (MIT, alpha); MITM/SSL-interception mode QUARANTINED (local-dev opt-in only); 50-80% savings UNVERIFIED-until-benchmarked; compression-as-deterministic-tool (no LLM, stable parsers, same-input→same-output) that MUST preserve answer-critical facts + source handles + held-out warnings + rehydration; one active = the local deterministic skeleton invariant ──
    ("scripts/check_context_compression_catalog.py", "check_context_compression_catalog"),
    # ── CANDIDATE Open*Hub.io websites drawn from real modular components (OpenTemplates/Endpoint/Env/Sandbox/Agent/Receipt/State Hub) — PRIVATE-FIRST: all candidate (0 public/active), domains owner-clearance-gated, each with an open-on-competition trigger + a modular_component_source + distinct-from the 9 existing hubs; discovery≠trust; never public without owner trademark clearance ──
    ("scripts/check_candidate_open_hubs.py", "check_candidate_open_hubs"),
    # ── hub_profiles.json = the SYSTEM-FACING map: every Open*Hub as a DIRECTORY the compiler/runtime pulls from (TYPES of rules/context/modules per hub). Anti-drift: every profiled id is a real hub, every real hub (9 live + active candidates + 5 method) is profiled; serves_truth=false ──
    ("scripts/check_hub_profiles.py", "check_hub_profiles"),
    # ── registry_ontology.json = the registry-of-registries (owner federation vision): indexes the load-bearing knowledge registries in a 5-layer model, each mapped to its REAL backing module/file + hub + stage + status live|partial|gap. GROUNDING: every live/partial backing path is existence-checked on disk (anti-hallucination for an architecture map); rigid entry schema + universe/kind partitions enforced; serves_truth=false ──
    ("scripts/check_registry_ontology.py", "check_registry_ontology"),
    # ── audit_magic_numbers = the no-magic-values AUDITOR (backs registry #41): AST scan flagging UNNAMED numeric literals (inline 0.83/1800/256) that carry no provenance, so the no-magic-values discipline has an actual scanner not just a doc ──
    ("scripts/audit_magic_numbers.py", "audit_magic_numbers"),
    # ── lookup_portals.json (backs registry #72): META, POINTER-ONLY catalog of authoritative fact-lookup portals (weather/license/property/tax-address/sanctions/business) — WHERE to look up a fact + how to access, NEVER a data copy; generalizes the healthcare starter vertical's free-registries-first descent; serves_truth=false ──
    ("scripts/check_lookup_portals.py", "check_lookup_portals"),
    # ── provider_arbitrage (backs registry #63): cross-provider price spread for the SAME model from model_index entries (cheapest vs dearest = the savings); complements routing_engine.route_model; honest on single-provider/absent; serves_truth=false ──
    ("scripts/check_provider_arbitrage.py", "check_provider_arbitrage"),
    # ── semantic_field_ontology (backs registry #20, GAP->partial): canonical field -> aliases (invoice_number=bill_number=NPI) so extraction/linking treat one field as one; deterministic normalize+alias-match resolver; UNAMBIGUOUS (no surface maps to 2 canonicals); serves_truth=false ──
    ("scripts/check_semantic_field_ontology.py", "check_semantic_field_ontology"),
    # ── human_expert_sources (backs registry #74, GAP->partial): META pointer-only catalog of EXTERNAL human-labor channels (Upwork/Toptal/MTurk/hackathons/bounties) — the human tier of the descent; NO worker-PII; serves_truth=false ──
    ("scripts/check_human_expert_sources.py", "check_human_expert_sources"),
    # ── observability_providers (backs registry #33, GAP->partial): pointer-only catalog of external observability providers (prometheus/otel/datadog/sentry/langfuse) a compiled workflow can auto-instrument with; serves_truth=false ──
    ("scripts/check_observability_providers.py", "check_observability_providers"),
    # ── geospatial_sources (backs registry #77): pointer-only catalog of public geo data sources (OSM/Census/NaturalEarth/GeoNames/WorldPop) — geocode/boundaries/population/POI/routing/elevation, licensed, exposed via OpenGeoHub; serves_truth=false ──
    ("scripts/check_geospatial_sources.py", "check_geospatial_sources"),
    # ── vulnerability_sources (backs registry #78): pointer-only catalog of public vuln/advisory feeds (CVE/NVD, GHSA, OSV, CWE, CISA KEV, ecosystem advisories) that feed registry #23 security + #47 code_audit; discovered advisory = candidate signal; serves_truth=false ──
    ("scripts/check_vulnerability_sources.py", "check_vulnerability_sources"),
    # ── knowledge_taxonomies (backs registry #81): pointer-only catalog of standard knowledge/subject/NEWS classification systems (Dewey/LCC/Wikidata/MeSH/ACM/JEL/EuroVoc/IPTC/O*NET/Schema.org) — the 'what is this about' map; distinct from #20 (field-name aliases); serves_truth=false ──
    ("scripts/check_knowledge_taxonomies.py", "check_knowledge_taxonomies"),
    # ── registry_port = the universal Registry<T> MENU realized: ONE ordering protocol (list/lookup/search/explain) over the federation's source catalogs, so an agent picks ingredients UNIFORMLY across lookup_portals/observability/geospatial/vulnerability/knowledge_taxonomies/human_expert/semantic; the demand-side buffet made callable; serves_truth=false ──
    ("scripts/check_registry_port.py", "check_registry_port"),
    # ── acquisition_strategies (backs registry #82): the AGENCY layer — cost-ordered ACTIONS an agent takes to GENERATE/acquire missing info (reformulate/decompose/cross-ref/source-escalate/probe/trigger-action/request-access/subscribe/ask-human/estimate); GOVERNED safety rail: high-invasiveness=boundary-approved, estimate=flagged-non-truth; serves_truth=false ──
    ("scripts/check_acquisition_strategies.py", "check_acquisition_strategies"),
    # ── registry_dependency_graph (registry #83, the META-REGISTRY): dependency graph COMPUTED from registry_ontology cross-refs (the #N / 'vs N' mentions) — nodes=registries, edges=references, most-depended-on; the ontology-about-the-ontology; --self-test validates consistency + FRESHNESS (computed-not-typed); serves_truth=false ──
    ("scripts/build_registry_dependency_graph.py", "build_registry_dependency_graph"),
    # ── registry_enrichment (registry #84): the maintenance/ENRICH worker (Baltor Enhance on the registries) — GENERATES deterministic embedding/description/long_description/use_cases/labels/keywords per record via the RegistryPort menu; learned/LLM enricher swaps behind the same port; serves_truth=false ──
    ("scripts/check_registry_enrich.py", "check_registry_enrich"),
    # ── ingest_fb_page_links (#75 community intake): governed harvest of GitHub repos linked from FB feed pages (theaiempire/DeepRepo) — extracts + CLEANS the links (strips fbclid), candidate-only (discovery!=trust); FB direct-scrape is ToS-restricted, governed fetch = owner-paste OR fb_page_scrape (RAPIDAPI_KEY/APIFY_TOKEN, names only); no PII; serves_truth=false ──
    ("scripts/ingest_fb_page_links.py", "ingest_fb_page_links"),
    # ── registry_populate (#90, the DOGFOOD population loop): repo slugs -> candidate RECORDS -> ENRICHED (#84) -> governed candidate (discovery!=trust); tools/web_fetch = the basic governed fetch floor (honest-fail); how registries GROW records; serves_truth=false ──
    ("scripts/check_registry_populate.py", "check_registry_populate"),
    # ── vertical_playbooks (#93): each business vertical's management-workflow SHAPE + the registries that COMPOSE it into a DAG (dental/vet clinic, agency, SaaS-mgmt, group, AP, contract, support) — a vertical 'management tool' = a DAG the federation assembles; check ties each playbook to REAL registries; NO insurance; serves_truth=false ──
    ("scripts/check_vertical_playbooks.py", "check_vertical_playbooks"),
    # ── registry_compose: the PLAYBOOK->DAG compiler ('how registries become a TOOL') — compiles a vertical playbook OR a universal intent into a candidate DAG plan, each stage picking ingredients from the registries via the RegistryPort menu; governed + candidate-only; serves_truth=false ──
    ("scripts/check_registry_compose.py", "check_registry_compose"),
    # ── registry_search: FEDERATED search across ALL registries (how a DAG builder uses the buffet) — search_all + the 3 builder workflows BUILD/TROUBLESHOOT/IMPROVE; on-menu registries queried, off-menu honestly surfaced; serves_truth=false ──
    ("scripts/check_registry_search.py", "check_registry_search"),
    # ── primitive_hybrid_search: Teleon primitive retrieval is BLOCKING+KEYWORD+LABEL+SEMANTIC+CONTRACT+GRAPH matching, not a single vector hit; classifies each primitive as exact_match / deterministic_edit_match / nondeterministic_edit_match / incompatible and names the adapter/mutation lane (scalar→sequence, output wrapper, retry/cache/rate-limit, model downshift, browser→deterministic, local/API swap, generated adapter). Candidate-only; promotion requires proofs/logs/provenance. ──
    ("scripts/check_primitive_hybrid_search.py", "check_primitive_hybrid_search"),
    # ── primitive_registry_builder: repo-code inventory -> real-code primitive CANDIDATE records + search index + vector export; every row carries I/O contracts, purpose, dependencies, license/provenance, execution surface, proof command, logs schema, graph edges, embedding, candidate=true, serves_truth=false; rejects placeholders/unmarked synthetic rows. ──
    ("scripts/check_primitive_registry_builder.py", "check_primitive_registry_builder"),
    # ── primitive_registry_promotion_gate: strict promotion boundary for primitive records — blocks placeholders, synthetic/example rows, LLM-generated truth, unresolved contracts, missing license/proof/review/log/schema/graph metadata; only proven reviewed real-code records become promotion_ready and still do not serve truth by themselves. ──
    ("scripts/check_primitive_registry_promotion_gate.py", "check_primitive_registry_promotion_gate"),
    # ── reinvention_guard: the 'you're reinventing a solved problem' guardrail GROUNDED in the federation (the descent thesis as a product) — tiered cascade (heuristic -> cheap gate -> Tier2 search_all grounding); FIRES with real matches on solved problems, QUIET on genuinely-novel work; serves_truth=false ──
    ("scripts/check_reinvention_guard.py", "check_reinvention_guard"),
    # ── observer.review: the POST-SESSION REVIEWER (the Observer's non-invasive adoption wedge) — runs the guardrail+federation funnel in BATCH over a finished transcript -> confidence-scored reinvention + waste (oversized/duplicate context) report; review == router.route_session(review_only); QUIET on genuinely-novel work; governed human-triaged candidates; serves_truth=false ──
    ("scripts/check_observer_review.py", "check_observer_review"),
    # ── AIDevObserver compiled-AI evaluation contract: benchmark plan + prompt + fixture matrix for real AI-agent programming sessions; validates domains/industries/token economics/security cases and runs smoke transcripts through review_session; candidate-only, serves_truth=false ──
    ("scripts/check_aidevobserver_compiled_ai_evaluation.py", "check_aidevobserver_compiled_ai_evaluation"),
    # ── AIDevObserver replayable example sessions: synthetic upload/download/live-replay fixtures for AI Dev Explorer demos; TXT+JSONL parse, review deterministically, and remain governed candidates with serves_truth=false ──
    ("scripts/check_aidevobserver_example_sessions.py", "check_aidevobserver_example_sessions"),
    # ── observer.router: the Spotter ROUTER over the intervention TAXONOMY — Tier-0 classify -> wake plausible typed MODULES (reinvention[grounded]/footgun[pattern,can block]/adversarial[question-templates]/waste) -> per-type floor + GLOBAL interruption budget + graduated modes (silent->review->advisory->active->enforcing); one engine, review == router in batch; footgun evidence REDACTED; patterns single-sourced from behavioral_heuristics.json; serves_truth=false ──
    ("scripts/check_observer_router.py", "check_observer_router"),
    # ── knowledge_graph: the Global Software Knowledge Graph engines (#91-93, §2/§9) — dependency_graph (transitive 'this whole stack exists') + product_distance (latent-space overlap to existing PRODUCTS) + repo_similarity (semantic equivalents of an intent) + code_genome (architectural-primitive fingerprints -> software similarity); grounded in 4 real registries; embedder plane (lexical floor in proofs); governed candidates; serves_truth=false ──
    ("scripts/check_knowledge_graph.py", "check_knowledge_graph"),
    # ── observer.capture + session_store: the capture SEAM (normalize Claude Code/Codex JSONL transcripts -> one event stream, drops thinking + slash-command noise, summarizes tool_use; PROVEN on the real 2847-line session -> 1368 events/34 findings) + the session model (session/event/intervention) with the accept/reject OUTCOME loop (append-only, latest-wins, lossless -> per-type tuning stats = the moat signal); serves_truth=false, read-only/local-first ──
    ("scripts/check_observer_capture_store.py", "check_observer_capture_store"),
    # ── observer.agentic: AIDevObserver for AUTONOMOUS agent loops — intra-run monitor_step + post-run review_agentic_run over the router engine; deterministic loop-shape signals (thrash/repeated-failure/stall/budget-overrun/goal-drift), recommends (never forces) halt; serves_truth=false, governed candidates ──
    ("scripts/check_observer_agentic.py", "check_observer_agentic"),
    # ── observer.consent: GATE #0 of the consented-session corpus flywheel — default-DENY, granular per purpose+scope, time-bounded, revocable (per-purpose), redaction always required, agents/pipelines first-class; nothing downstream retains a session unless this allows it; serves_truth=false ──
    ("scripts/check_observer_consent.py", "check_observer_consent"),
    # ── observer.corpus: stages 2-4 of the flywheel — consent-gated retain (deny->None) + mandatory redaction, detector-driven mining (reinvention->component candidates, rest->research-queue), governed standardize (candidate-only, provenance, no self-promote; the dev-plane ingest gate scans + the promotion boundary governs); serves_truth=false ──
    ("scripts/check_observer_corpus.py", "check_observer_corpus"),
    # ── observer_corpus_harvest: the dev-plane DRIVER that runs the flywheel end-to-end — consented sessions -> retain+redact -> mine -> research-queue entries + INGEST-security-scanned candidate components (>=high quarantined), candidate-only; wires the product modules to the dev-plane sinks; serves_truth=false ──
    ("scripts/observer_corpus_harvest.py", "observer_corpus_harvest"),
    # ── code_genome_index: DOGFOOD the Code Genome (§9) on _repos/teleon/backend/src/teleon — AST-fingerprint each module, flag high genome overlap as CANDIDATE internal reinvention (worth review, NOT proven duplication); honest sparse genome over abstract framework code; high-volume->DB; serves_truth=false, candidates only ──
    ("scripts/build_code_genome_index.py", "build_code_genome_index"),
    # ── spotter_surface: the demoable face of the Observer/Spotter subsystem -> self-contained dist/spotter/index.html ('coaching not surveillance', the live taxonomy, a reproducible post-session review embedded, the knowledge-graph engines, funnels to Teleon); ALL counts computed from the live router+registries (no-magic-values); serves_truth=false ──
    ("scripts/build_spotter_surface.py", "build_spotter_surface"),
    # ── enrichment_loop: the 3-day WHOLE-SURFACE enrichment loop (./enrich) — a cadence scheduler over the real worker scripts across ALL 5 surfaces (Baltor/Teleon/Hubs/Observer/Discovery) generating records/metadata/embeddings/tools/descriptions/use-cases every ~30min, full-gate every 4th cycle, STOP-aware + resumable; self-test validates rotation/offline/duration wiring (no subprocess); schedules generation+gating, adds no truth; serves_truth=false ──
    ("scripts/enrichment_loop.py", "enrichment_loop"),
    # ── capability_mvp: the MVP SHOWCASE — wires the whole federation end-to-end (guardrail + build-a-capability live over the registries) into a self-contained dist/capability-mvp/index.html that funnels to Teleon/Baltor; counts COMPUTED from registry_ontology; serves_truth=false ──
    ("scripts/build_capability_mvp.py", "build_capability_mvp"),
    # ── registry_records: SCALE — every menu registry wired to >=1000 records (REAL from catalogs + flagged SYNTHETIC candidates), each ENRICHED (embedding/description/metadata), pgvector DDL+search (vector dim single-sourced from EMBED_DIM); honest real-vs-synthetic ledger; high-volume->DB not git; candidate-only; serves_truth=false ──
    ("scripts/build_registry_records.py", "build_registry_records"),
    # ── registry_discover: AUTO-DISCOVERY — scans _repos/shared-backend-components/architecture/*.json + registers every VALIDATED catalog-shaped registry so federated search spans them all (147, was 14 curated); each validated (list + lookup round-trips); resolves the menu-coverage roadblock ──
    ("scripts/check_registry_discover.py", "check_registry_discover"),
    # ── registry_loop: the refresh LOOP body (discover -> dependency-graph -> records -> MVP; + credential-gated population) — run on a cadence to keep the federation current; everything downstream of the registries is computed ──
    ("scripts/registry_loop.py", "registry_loop"),
    # ── local_embedder: semantic embeddings run LOCALLY via Ollama nomic-embed-text — NO API KEY (one fork, not a default); best_embedder = local_first policy over the plane; gate-safe ──
    ("scripts/check_local_embedder.py", "check_local_embedder"),
    # ── plane_selection (FORK/VARIATION law): generic policy-driven selection over a PLANE of candidate adapters (forks) — local_first/keyless_first/cheapest/best_quality policies DIVERGE, fallback chain, extensible; replaces hardcoded best_X() wrappers; see _repos/shared-backend-components/docs/codex/fork-and-variation-rigor.md ──
    ("scripts/check_plane_selection.py", "check_plane_selection"),
    # ── record_variations (FORK/VARIATION law applied to DATA): any registry row -> governed candidate variations across industry/region/scale/approach + the fork questions; discovery!=trust; serves_truth=false ──
    ("scripts/check_record_variations.py", "check_record_variations"),
    # ── million_records: SCALE past 1M via VARIATION MUTATION — real seeds x cartesian product of axes (industry x geography x season x time x scale x approach) = ~89M governed CANDIDATE variations (computed count, streamed to pgvector not git, candidate-only, serves_truth=false; never fabricated as verified fact) ──
    ("scripts/build_million_records.py", "build_million_records"),
    # ── distill_kaggle_kernels (#88 LLM population): distills the mined Kaggle kernels -> candidate registry ENTRIES (deterministic floor maps pattern->registry + frequency/lineage; LLM path Kimi/GLM/Claude via ollama when OH_LLM_API_KEY). LOSSLESS (keeps raw freq + lineage); candidates only; serves_truth=false ──
    ("scripts/distill_kaggle_kernels.py", "distill_kaggle_kernels"),
    # ── formula_registry (#98): named DETERMINISTIC formulas the compiler applies instead of an LLM (compound interest/Ohm's law/Reynolds/z-score/BMI) — the 'deterministic > probabilistic' core; spec-only (expression+variables+units, no eval), self-consistent (variables in expression); serves_truth=false ──
    ("scripts/check_formula_registry.py", "check_formula_registry"),
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
    # ── PARENT brand canonical + lossless: _repos/shared-backend-components/architecture/brand.json is the ONE source of the parent / holding-company identity — company_name/wordmark "AI Done Right" + tagline "AI systems that can do the work, show the work, and prove the work." + domain aidoneright.dev (renamed from "ContextIsEverything Group" / "Context is Everything"; interim "AI is Everything" rejected); the prior name+taglines are PRESERVED as the rollback target (lossless); Baltor + Teleon recorded unchanged; full-words naming (no abbreviation); single-sourced — company_portfolio_map.json's parent display_name mirrors brand.json with no drift; the holding_company slug stays a code identifier ──
    ("scripts/check_brand_canonical.py", "check_brand_canonical"),
    # ── Context Auditor (_repos/baltor/backend/src/baltor/context_audit): deterministic pre-LLM-call ContextAuditReport across all source kinds (system_prompt/CLAUDE.md/AGENTS.md/MCP-schemas/docs/memories/tool-output/code-comments) — flags duplicate (shingle-Jaccard) / conflicting (claim-key) / tool_bloat (schema-count) / stale (ttl); PROPOSES not disposes (applied=False); LOSSLESS (raw untouched, conflicts surface both + supersede≠delete); output≠truth; single-sourced authority order ──
    ("scripts/check_context_auditor.py", "check_context_auditor"),
    # ── Context-engineering TOOL LANDSCAPE catalog (_repos/shared-backend-components/architecture/context_engineering_tool_catalog.json): 20 candidate tools across 5 layers (token-waste obs / compression / tool-output isolation / code-context selection / memory-RAG dedupe+conflict); all candidate≠active + do_not_adopt_as_runtime; dedupe/supersession lossless-governed; the_gap = the Baltor-owned Context Auditor; distinct from context_compression_provider_catalog ──
    ("scripts/check_context_engineering_tool_catalog.py", "check_context_engineering_tool_catalog"),
    # ── Baltor→Teleon migration STEP 4 (FINAL): _repos/baltor/backend/src/baltor/teleon_client — the versioned tenant client Baltor uses to reach Teleon (Baltor→Teleon direction); offline-first local calls + graceful fallback from a remote seam + per-call receipt (served_by/fallback); output is an inspectable receipt, not auto-truth. Completes the fleet→experiments→purpose_tasks→client extraction. ──
    ("scripts/check_teleon_client.py", "check_teleon_client"),
    # ── Context Auditor CONNECTED: _repos/baltor/backend/src/baltor/context_audit/audit_bridge emits one bus event per finding (conflict→contradiction_found, stale→rot.detected, duplicate→context.duplicate_found, tool_bloat→context.tool_bloat) + a context.audited summary; the gateway pre-call path attaches the manifest to inference.requested; lossless + proposes-not-disposes; monotonic seq, no wall-clock. ──
    ("scripts/check_context_audit_bridge.py", "check_context_audit_bridge"),
    # ── Context Auditor LIVE in the connected pipeline: run_full_pipeline audits the assembled context (audit_and_emit) so context.audited + context.duplicate_found + context.tool_bloat fire mid-run on /dashboard, within the pipeline span, applied=False; no regression (core kinds + exactly one inference request); deterministic across runs. ──
    ("scripts/check_context_audit_in_pipeline.py", "check_context_audit_in_pipeline"),
    # ── Context Optimizer (_repos/baltor/backend/src/baltor/context_audit/optimizer): applies a ContextAuditReport → a smaller optimized context view (duplicates dropped, conflict losers superseded + winner annotated contested, bloat/stale flagged) — LOSSLESS: raw + dropped + superseded + lineage preserved + exact rehydrate(); applied=True but supersede≠delete; output is a derived view, not truth. The Auditor→Optimizer layer of the owner's architecture. ──
    ("scripts/check_context_optimizer.py", "check_context_optimizer"),
    # ── Context Auditor over REAL governed context: _repos/baltor/backend/src/baltor/context_audit/context_object_adapter.from_context_objects maps context-graph objects → auditor sources; run over the ACTUAL acme seed graph it flags the genuinely-stale runbook (real freshness metadata) + raises NO false conflict on agreeing structured claims (prose 5-vs-3 deferred to find_contradictions); deterministic, non-mutating, evidence-not-truth. ──
    ("scripts/check_context_object_audit.py", "check_context_object_audit"),
    # ── Auth/identity KIT (_repos/openhubforai/backend/src/openhubforai/auth_kit): owner-authorized 2026-06-09 — completely SEPARATE + INDEPENDENT login/register/onboarding per product (own accounts/sessions/registration, no cross-realm account, no SSO) built from ONE shared kit (make_realm); standard register→onboard→login flow; credentials are one-way refs (no cleartext; real password-hash/OAuth/SSO is a CredentialProviderPort seam); deterministic + injected clock. Open bottom-layer (Baltor+Teleon may import; OHH imports neither). ──
    ("scripts/check_auth_kit_realm_isolation.py", "check_auth_kit_realm_isolation"),
    # ── Local Identity & Access SERVICE (_repos/shared-backend-components/scripts/identity_local_service.py): the auth kit RUNNING as a local backend — registry-driven SEPARATE realms (parent+Baltor+Teleon+every LIVE hub via _repos/shared-backend-components/architecture/identity_realm_registry.json, products.js drift-gated both directions; private bench excluded), register→onboard→login→session + session-gated HASH-ONLY API keys (raw shown once) over HTTP; restart-safe dist/identity persistence; audited with X-AIDR-Request-Id correlation + rejected outcomes; no cleartext secret or raw key on disk. Local dev equivalent of service-auth Phase 1 — real crypto/OAuth/SSO stays an owner-gated CredentialProviderPort seam. ──
    ("scripts/check_identity_local_service_runtime.py", "check_identity_local_service_runtime"),
    # ── Harness-hub auth WIRED to the local identity service (_repos/openhubforai/frontend/identity.js + pages/auth.js): real register→onboard→login→session + /account/keys console against /api/identity/openhubforai/* — registry drift-gated default port, OPENHUBFORAI_IDENTITY_BASE deploy override, X-AIDR-Request-Id, only the opaque session handle in localStorage (passphrase memory-only, raw key shown once never persisted), SSO/Google rendered as DISABLED owner-gated seams, honest service-down message, no hardcoded tunnel URLs; node --check syntax-gates both files when node exists. ──
    ("scripts/check_openhubforai_auth_wiring.py", "check_openhubforai_auth_wiring"),
    # ── Cloud-Run-like LOCAL service plane (Browser E2E + Local Service Emulation Gate, owner add-on 2026-06-09): _repos/shared-backend-components/architecture/local_service_registry.json declares every local service/emulator with honest active_local/held/planned statuses + held reasons; scripts/local_services_lib + start/stop_local_services manage process groups (idempotent health-first start; stop only via service stop_command or exact recorded pid); ports drift-gated against portfolio_lib + the identity realm registry; every active group must start and answer health; dist/local-service-urls.md carries REAL URLs only (tunnel cells only from the recorded launcher manifest). ──
    ("scripts/check_local_services_health.py", "check_local_services_health"),
    # ── Browser E2E review artifacts are REAL and leak-free: e2e/crawl_all_surfaces.mjs (11 running surfaces × video + 1440/1280/390 stills + HTML + console + overflow + dead-link sweep) and e2e/register_login_portal.mjs (10-step register→onboard→activate+login→mint(blur+server-verify)→revoke→logout→re-login→session-restored journey in real Chrome against the real identity service) must leave: GIF videos ≥10KB, the 10 portal stills, both reports — with NO raw API key / credential ref / provider key / passphrase fixture in any text artifact, the ffmpeg-on-ubuntu26.04 limitation HELD honestly (GIF house pattern, not faked webm), and skipped held/planned services listed with reasons. ──
    ("scripts/check_no_raw_secrets_in_e2e_artifacts.py", "check_no_raw_secrets_in_e2e_artifacts"),
    # ── Native events/A-B plane (_repos/shared-backend-components/scripts/events_local_service.py): the handoff's EVENTS.md contract recreated in repo patterns (bundle Node core stays reference-only) — registry-ported (local_service_registry 9420), single/batch ingest, per-variant summary with conversion_rate, PII/key-shaped events REJECTED and never stored, restart-safe JSONL counters, /healthz /readyz /version /api/status, declares truth_authority:false (projection/evidence only — NOT the platform bus). ──
    ("scripts/check_local_events_plane.py", "check_local_events_plane"),
    # ── Service↔service /service/* handshake slice in the identity service (backlog 1.2, contracts/SERVICE-CONNECTIONS.md — makes the Service Connections dev console real): env-keyed service-account handshake (SERVICE_<REALM>_SECRET; 503 when unset, never faked), 8-scope vocabulary (S3) enforced, directional verify (TO realm only), both-realm connection lists projection-only, revoke with receipts, asymmetric grants (Baltor→Teleon ≠ Teleon→Baltor), user-realm isolation intact (a service token is not a user session), no raw token on disk (svtref: only). ──
    ("scripts/check_service_handshake_slice.py", "check_service_handshake_slice"),
    # ── Events/A-B beacon WIRED (backlog 2.1/2.3): _repos/openhubforai/frontend/events.js beacons page/exposure/conversion to the registry-ported events plane (drift-gated default port, OH_EVENTS_BASE override, sendBeacon, anon-only, client-side PII guard); app.js emits a page event per route + the builder_cta landing exposure + CTA conversion; the live /summary A/B readout is real (exposure/conversion/rate from a real loop); sticky deterministic variant assignment. ──
    ("scripts/check_events_beacon_wiring.py", "check_events_beacon_wiring"),
    # ── Ledger-only billing over LLM receipts (BUSINESS-PLANE order 1): _repos/shared-backend-components/scripts/billing_ledger.py — per-key/per-class/month statements from invocation receipts (model CLASS→rate single source, no model names in logic), reconcile() flags drift with receipts as the authority (never overwrites receipts from the provider), unknown class never invents a rate; authors no charge, calls no payment API. ──
    ("scripts/billing_ledger.py", "billing_ledger"),
    # ── Shared empty/loading/error UX kit (UX-BACKLOG P1 #3): _repos/openhubforai/frontend/oh-states.js — three token-only primitives with correct ARIA roles (status/aria-busy/alert), escaped interpolation, loaded in the shell; node-syntax-gated. ──
    ("scripts/check_oh_states_kit.py", "check_oh_states_kit"),
    # ── AI Done Right surface-family roster GATE (was unregistered — codebase-review G14): products.js defines parent + 4 products (Teleon · Baltor · AIDevObserver · OpenHubForAI; consolidated 2026-06-27) + the Open*Hub registry roster now INTERNAL to OpenHubForAI (live + private-bench, count COMPUTED not hand-typed, preserved in OPENHUB_REGISTRIES) + the five-stage method spine; every referenced surface exists; roster drift fails both directions. Now flywheel-gated so adding/removing a hub can't silently drift. ──
    ("scripts/check_ai_done_right_surface_family.py", "check_ai_done_right_surface_family"),
    # ── Claude Design surface-adherence CONTRACT (2026-06-27): every product surface follows the Claude Design designs in the bundle source — design copy/structure PRESENT; A/B variant pickers + experiment panels + legacy positioning + parent Demo/two-layer model ABSENT; parent shows four products; the Operations Console exposes the credential-plane API-keys view. Drift away from the adopted design fails here instead of silently shipping. ──
    ("scripts/check_surfaces_match_claude_design.py", "check_surfaces_match_claude_design"),
    # ── AI Done Right handoff-docs freshness GATE (was unregistered — codebase-review G14): the handoff/transfer docs exist, record CURRENT surface counts, name the five method hubs, link the service-auth + design-family proofs, carry transfer artifacts, and contain no raw secrets. ──
    ("scripts/check_handoff_docs_freshness.py", "check_handoff_docs_freshness"),
    # ── Standardized transactional-email PORT (BUSINESS-PLANE §2; closes the one spec-only cross-cutting component): one send(realm,template,to,props) contract, realm-branded from the identity realm registry; console adapter renders to dist/email-outbox + audit and HONESTLY does not send (Mode Protocol, sent=False); Resend/Postmark are owner-gated seams (NotConfigured without a provider key — never a fake send); secret/template/recipient guards; no secret in the trail. Indexed in _repos/shared-backend-components/docs/architecture/component-standardization-index.md. ──
    ("scripts/email_port.py", "email_port"),
    # ── Metered billing chain (BUSINESS-PLANE §3; takes billing PARTIAL→fuller): _repos/shared-backend-components/scripts/billing_plane.py — receipts → meter → DRAFT invoice (single-sourced plan subscription + metered overage above the included allowance) on the ledger authority; Stripe is an owner-gated seam that raises NotConfigured without STRIPE_API_KEY (a charge is never faked); reconcile keeps receipts authoritative over the provider. Built on scripts/billing_ledger. ──
    ("scripts/billing_plane.py", "billing_plane"),
    # ── ADVERSARIAL auth across EVERY front end's realm (parent + Baltor + Teleon + 9 live hubs, not just openhubforai): each realm survives the happy path (register→verify-email→onboard→login→key→revoke→re-login) AND the attacks — duplicate register rejected, login-before-onboard rejected, wrong-password and unknown-account both 401 (NO account enumeration), mint without session 401, revoke-not-owned 404, injection-shaped identifier handled safely, cross-realm session/identifier isolation (no SSO), no cleartext secret or raw key on the wire or disk. ──
    ("scripts/check_adversarial_auth_all_realms.py", "check_adversarial_auth_all_realms"),
    # ── FULL-DESIGN bundle WIRED to real backends (owner: "bring the full design into the working apps"): dist/sites/aidoneright-design/shared/oh-identity.js — realm-aware identity client (drift-gated port, OPENHUBFORAI_IDENTITY_BASE override, per-realm sessions, passphrase never stored) loaded across the surface HTMLs; the kit's OhAuth (oh-site.jsx) does REAL register/login against the identity service with honest preview fallback (never fakes a session) + Google/GitHub as disabled owner-gated seams; a page_view beacon fires to the events plane. The hundreds-of-hours design is now functional, not mock. ──
    ("scripts/check_bundle_full_design_wiring.py", "check_bundle_full_design_wiring"),
    # ── REGISTRY DATA BACKEND makes the full-design dashboards REAL (owner: "wire the registry data backend so the dashboards are real"): _repos/shared-backend-components/scripts/registry_local_service.py fulfils the declared local_openhubforai_projection_api (:9423) — a PUBLIC catalog seeded by extracting each hub's entries from the design bundle (single source, no retyped catalog) + a PER-ACCOUNT workspace (install/uninstall/publish/summary) replayed from an append-only log. Workspace endpoints are session-gated: the account is resolved by VALIDATING the realm session against the identity service (raw session id never persisted), so install/Installed/Published/Avg-eval/Activity/API-calls·30d on OhDashboard are the account's REAL numbers; publish → review queue (candidate ≠ active); truth_authority=false. shared/oh-registry.js (drift-gated port, OPENHUBFORAI_REGISTRY_BASE override, reuses the identity realm + oh-session-<realm>) is loaded after oh-identity.js across the surfaces; oh-hub.jsx reads it for the dashboard/Installed/add-button with an HONEST fallback to the in-file design seed (never the seed presented as live) — DESIGN-CONTRACT markup preserved. ──
    ("scripts/check_registry_backend.py", "check_registry_backend"),
    # ── Foundry measure-stage Judge scorer ladder (closes the offline measurement cap): _repos/shared-backend-components/scripts/foundry/eval_scorers.py — deterministic ladder (exact-match/token-F1/REFERENCE-FREE faithfulness proxy/context-precision AP@k) scores lift WITHOUT a gold answer; model-backed NJudgeMajority returns None on judge disagreement and raises without a route (never fabricated); Ragas/DeepEval honest seams; LadderJudge drops into MeasurementStage. ──
    ("scripts/foundry/eval_scorers.py", "foundry_eval_scorers"),
    # ── Catalog→runtime processor BRIDGE (5W1H deepest unlock): _repos/shared-backend-components/scripts/runtime/catalog_processor_bridge.py — discovers every process_kind→component-id→callable from the manifests (single source) and resolves/invokes the 97 governed processors by id or unique process_kind; ambiguous kind raises with candidates; ALL discovered callables import. ──
    ("scripts/runtime/catalog_processor_bridge.py", "catalog_processor_bridge"),
    # ── Catalog processors registered INTO the runtime: _repos/shared-backend-components/scripts/runtime/catalog_runtime_adapter.py — wraps each catalog run() as a runtime Processor (handle(command,ctx)), emits a CANDIDATE processor_output artifact (gate promotes, not the adapter), registers the whole fleet into the ProcessorRegistry the runner uses; a run() error fails cleanly (no crash). ──
    ("scripts/runtime/catalog_runtime_adapter.py", "catalog_runtime_adapter"),
    # ── Processor dispatch-index DRIFT gate: _repos/shared-backend-components/scripts/build_processor_dispatch_index.py — the committed _repos/shared-backend-components/architecture/processor_dispatch_index.json (the stdlib-json map the runtime bridge reads, keeping the runtime YAML-free) must match the manifests; this rebuilds in memory and fails if it drifted. Manifests stay authoritative without a runtime YAML dependency. ──
    ("scripts/build_processor_dispatch_index.py", "build_processor_dispatch_index"),
    # ── Cohort compression-policy selector (context-efficiency 'consumer behavior'): _repos/shared-backend-components/scripts/processors/compression/cohort_policy_selector.py — reads a usage_gated_compress prior, classifies the tenant's usage SHAPE (power-user/iterating/fresh/balanced/unknown), and emits the compression curve (budget_fraction + utility/volatility/recency weights); power-user compresses the stable substrate hard, fresh barely compresses, unknown stays conservative; deterministic. ──
    ("scripts/processors/compression/cohort_policy_selector.py", "cohort_policy_selector"),
    # ── Model-provider LANES wired end-to-end (backlog #4): _repos/shared-backend-components/scripts/check_model_provider_lanes.py — Ollama Cloud / Mistral / OpenRouter / Anthropic / OpenAI / local Ollama each have a governed graph node (external nodes carry secret_ref + local_equivalent) AND a verified env→route mapping through model_route.from_env (offline, no network); live smoke runs only with a real key + OH_LANE_SMOKE_LIVE=1. ──
    ("scripts/check_model_provider_lanes.py", "check_model_provider_lanes"),
    # ── Receipt service (#10c; was status:planned): _repos/shared-backend-components/scripts/receipt_local_service.py — fulfils local_receipt_service (:9426); append-only content-addressed receipts for important flows (is_truth=false — the gate promotes, not this); filter by kind/flow, get by id; same content → same id (replay-detectable). ──
    ("scripts/receipt_local_service.py", "receipt_local_service"),
    # ── State service (#10c; was status:planned): _repos/shared-backend-components/scripts/state_local_service.py — fulfils local_state_service (:9427); keyed session/action state replayed from an append-only op-log (set/append/delete), truth_authority=false always; crash-safe history. ──
    ("scripts/state_local_service.py", "state_local_service"),
    # ── Ingest staging→measure→gate PROMOTE job (#7; closes health≠promotion): _repos/shared-backend-components/scripts/ingest/promote_staged.py — fed official-source rows are staging-only until this runs; offline (no model route) every unmeasured candidate routes to REVIEW (boundary held, no fabricated lift); with a route it measures real bare-vs-pipeline lift and PROMOTES the ones clearing the floor with provenance + durability. Composes model_route.measurement_stage + gate.evaluate (no new gate logic). ──
    ("scripts/ingest/promote_staged.py", "ingest_promote_staged"),
    # ── SHOWCASE PIPELINES gated (closes the "self-tested but un-gated" orphan): each _repos/shared-backend-components/scripts/showcase_pipelines/*.py COMPOSES the real processor run() callables end-to-end into a governed flow for a concrete scenario and self-tests the whole composition (the ONE simulated seam is the model call). These were runnable but reachable from no gate; now the flywheel keeps every showcase green so a processor change that breaks a composition is caught. Spread across durability classes (precedence/aggregation/freshness/coded-vocabulary/low-resource) and domains beyond CFPB. ──
    ("scripts/showcase_pipelines/regulated_fact_qa.py", "showcase_regulated_fact_qa"),
    ("scripts/showcase_pipelines/governed_rag.py", "showcase_governed_rag"),
    ("scripts/showcase_pipelines/clinical_support.py", "showcase_clinical_support"),
    ("scripts/showcase_pipelines/low_resource_alert.py", "showcase_low_resource_alert"),
    ("scripts/showcase_pipelines/context_efficiency_loop.py", "showcase_context_efficiency_loop"),
    ("scripts/showcase_pipelines/sanctions_aml_screening.py", "showcase_sanctions_aml_screening"),
    ("scripts/showcase_pipelines/cve_dependency_triage.py", "showcase_cve_dependency_triage"),
    ("scripts/showcase_pipelines/icd10_coding.py", "showcase_icd10_coding"),
    # ── Related-party / shell-network discovery (owner-requested: networks of relationships — employment agencies, shared addresses/phones/officers, M&A): _repos/shared-backend-components/scripts/showcase_pipelines/related_party_network.py — normalize identifiers → shared-identifier graph → UNION-FIND connected components; three "independent" staffing agencies sharing one normalized address+phone+officer collapse into ONE HIGH-risk shell network (escalated), while a DISCLOSED M&A pair stays NORMAL and a standalone stays a singleton. The hidden network a bare model can't compute; signed registry governs over scraped news; serves_truth=false. ──
    ("scripts/showcase_pipelines/related_party_network.py", "showcase_related_party_network"),
    # ── Common-control resolution from M&A NEWS (owner-requested: mergers & acquisitions): _repos/shared-backend-components/scripts/showcase_pipelines/common_control_resolver.py — chain acquisitions by date → each entity's ultimate parent; a 'vendor' and a 'customer' both rolled up to ParentCo over two deals are flagged as a RELATED-PARTY (self-dealing) transaction and escalated — but NOT before the second deal closed (temporal/as-of axis), and not for truly independent parties. The post-cutoff, transitively-chained control a bare model can't track; signed registry governs; serves_truth=false. ──
    ("scripts/showcase_pipelines/common_control_resolver.py", "showcase_common_control_resolver"),
    # ── Beneficial ownership + OFAC 50% rule (owner-requested M&A / evolving ownership hierarchies in merger-heavy industries — staffing/employment agencies, real-estate brokerages): _repos/shared-backend-components/scripts/showcase_pipelines/beneficial_ownership_resolver.py — resolve each entity's AUTHORITATIVE current parent from CONFLICTING ownership claims using the real scripts/artifact_graph/source_authority classifier (an SEC 8-K GOVERNS over a press rumor; flip the publisher → the owner flips), then apply OFAC's 50% rule: a block on an SDN-listed person (Volkov Holdings) PROPAGATES down every ≥50% ownership edge so Apex Staffing is BLOCKED BY INHERITANCE (unlisted) while the 40%-owned Beacon is not. Authority is EARNED not assumed; temporal as-of; serves_truth=false. Showcases the source-authority work end-to-end on the ownership domain. ──
    ("scripts/showcase_pipelines/beneficial_ownership_resolver.py", "showcase_beneficial_ownership_resolver"),
    # ── FDA drug-labeling claim review (regulated-fact vertical on the EARNED source-authority engine): _repos/shared-backend-components/scripts/showcase_pipelines/fda_labeling_claim_review.py — substantiate each promotional claim against the FDA-APPROVED label (fda.gov, official agency, via scripts/artifact_graph/source_authority); a 25-mmHg efficacy overclaim (contradicts the label) and a 40%-heart-attack-risk claim (off-label, no approved topic) are HELD OUT + escalated as FDCA-502 risk; flip the source → the substantiated claim flips. serves_truth=false. ──
    ("scripts/showcase_pipelines/fda_labeling_claim_review.py", "showcase_fda_labeling_claim_review"),
    # ── BIS export-control screening (regulated-fact vertical): _repos/shared-backend-components/scripts/showcase_pipelines/export_control_screening.py — screen each export's end-user against the authoritative BIS Entity List (bis.doc.gov) vs a stale vendor screening DB; the vendor "clear" is HELD OUT and the export to the LISTED end-user REQUIRES A LICENSE (escalated, EAR) while a clean end-user clears; flip the source → the screen flips. Earned authority; serves_truth=false. ──
    ("scripts/showcase_pipelines/export_control_screening.py", "showcase_export_control_screening"),
    # ── Fragile fact-base watchtower (owner-requested: licensed employment agencies in the Philippines): _repos/shared-backend-components/scripts/context_workers/ph_employment_agency_watchtower.py — DMW/POEA + DOLE official evidence governs licensing status, stale customer/vendor context is held out, unavailable official sources create verification tasks, and Teleon deterministic tools stay separated from LLM-assisted candidate evidence. ──
    ("scripts/context_workers/ph_employment_agency_watchtower.py", "ph_employment_agency_watchtower"),
    # ── Procurement collusion / bid-rigging ring (owner-requested relationship-network 'etc'): _repos/shared-backend-components/scripts/showcase_pipelines/procurement_collusion_ring.py — aggregate bids ACROSS tenders → a co-bidding group whose wins ROTATE and whose losing bids are COVER BIDS (just above the winner) is flagged as a bid-rigging ring (RingCo/BidCo/CovCo escalated), while an honest undercutter is excluded and a competitive ledger is not flagged. The ring is a property of the whole bid history — invisible to a per-tender model; signed award notice governs; serves_truth=false. ──
    ("scripts/showcase_pipelines/procurement_collusion_ring.py", "showcase_procurement_collusion_ring"),
    # ── LLM-plane local service ACTIVATED (#service-registry; was status:planned): _repos/shared-backend-components/scripts/llm_plane_local_service.py — fulfils local_llm_plane_emulator (:9425) by PROJECTING the canonical OIPS router (_repos/teleon/backend/src/teleon/inference) over /api/inference/* (providers/models/health/route) — wires that module, never duplicates routing. A route returns the real select_provider decision + a DETERMINISTIC offline stub completion (is_stub, served_truth=false) + a receipt (is_truth=false); network LLMs stay owner-gated (an external node only wins if its secret is actually present, else it falls back to the local equivalent). ──
    ("scripts/llm_plane_local_service.py", "llm_plane_local_service"),
    # ── Governed-examples GALLERY built from REAL pipeline output (the recordable surface for "more videos, more examples"): _repos/shared-backend-components/scripts/build_examples_gallery.py — imports all 8 showcase pipelines, runs each run() on its own synthetic inputs, and renders ONE self-contained on-brand HTML (dist/examples-gallery/index.html) where every card's verdict/trace/report is the pipeline's ACTUAL deterministic output (BLOCKED 54% / AFFECTED+KEV / abstained / SERVED 28% / ESCALATED / SIGN-OFF / savings). No external resources, no JS — recordable offline by e2e/record_examples_gallery.mjs. Single-sources the portfolio CSS (portfolio_lib.SHARED_CSS). ──
    # ── README COUNT-DRIFT gate (no-magic-values; the canonical "172→thousands" bug): _repos/shared-backend-components/scripts/build_readme_stats.py --self-test (== --check) — the generated catalog-stats block AND every inline `<!--N:key-->value<!--/N-->` count in README prose (demo scripts, foundry modules, design patterns, model adapters, code templates) must equal the computed value; a hand-typed count that drifts from reality now FAILS the gate instead of rotting quietly. ──
    ("scripts/build_readme_stats.py", "build_readme_stats_check"),
    ("scripts/build_examples_gallery.py", "build_examples_gallery"),
    # ── ADVERSARIAL gallery-video verifier gated: _repos/shared-backend-components/scripts/check_examples_video_verifier.py — a recorder asserting "the DOM had the verdict" never proves the VIDEO FILE shows anything. e2e/verify_examples_gallery_videos.mjs inspects the bytes (size / duration / 1600x900 / not-blank via luma range / not-black / not-frozen via start-vs-end PSNR) and its --self-test synthesises blank/black/frozen/short/wrong-size videos and proves it REJECTS each on the right check. The recorder runs the verifier on every full run AND strengthens its own in-page checks (chip visible + in-viewport + FULL verdict text + card not half-rendered + no overflow/console errors). Environment-tolerant: runs the discrimination self-test where node+ffmpeg exist, skips honestly otherwise. ──
    ("scripts/check_examples_video_verifier.py", "check_examples_video_verifier"),
    # ── OPEN*HUB AUTOMATION: all 22 hubs auto-populate via THREE channels — DISCOVER (OpenClaw/Hermes + keep_hub_fresh, unbounded→bounded), GENERATE (method_catalog single-source + operator-injected descent_brain), INTAKE (owner OKF/links/text via --ingest). Research itself is a descent-selectable catalog (cheapest component that gets the detail; the LLM-driven browser only for deep_detail). The capability planner turns open-ended text ("scrape the internet for more skills for openskillshub.io") into iterative/scheduled/multi-component plans. ONE standardized template renders all 22 surfaces. The coverage guard means no hub is silently stranded. Registered so CI + the health flywheel GUARD the hub system — it was previously unguarded (a content_kind rename silently broke check_openclaw_hermes; caught + fixed by this registration). serves_truth=false throughout; verify gate applies (discovery≠trust). ──
    ("scripts/check_hub_engines.py", "check_hub_engines"),
    ("scripts/check_openclaw_hermes.py", "check_openclaw_hermes"),
    ("scripts/check_hub_freshness.py", "check_hub_freshness"),
    ("scripts/check_hub_settings.py", "check_hub_settings"),
    ("scripts/check_hub_population_coverage.py", "check_hub_population_coverage"),
    ("scripts/check_research_catalog.py", "check_research_catalog"),
    ("scripts/check_web_browsing_stack_registry.py", "check_web_browsing_stack_registry"),
    ("scripts/check_agnostic_adapters.py", "check_agnostic_adapters"),
    ("scripts/check_adapter_layers.py", "check_adapter_layers"),
    ("scripts/check_ocr_port.py", "check_ocr_port"),
    ("scripts/check_capability_taxonomy.py", "check_capability_taxonomy"),
    ("scripts/check_agentic_loop_catalog.py", "check_agentic_loop_catalog"),
    ("scripts/check_optimization_passes.py", "check_optimization_passes"),
    ("scripts/check_inefficient_pipeline_archetypes.py", "check_inefficient_pipeline_archetypes"),
    ("scripts/check_tool_registry.py", "check_tool_registry"),
    ("scripts/check_worked_examples.py", "check_worked_examples"),
    ("scripts/check_source_search.py", "check_source_search"),
    ("scripts/discover_tools.py", "discover_tools"),
    ("scripts/check_credential_registry.py", "check_credential_registry"),
    ("scripts/runtime/secret_resolve.py", "secret_resolve"),
    ("scripts/check_secret_chokepoint.py", "check_secret_chokepoint"),
    ("scripts/check_browser_escalation_ladder.py", "check_browser_escalation_ladder"),
    ("scripts/check_capability_ladders.py", "check_capability_ladders"),
    ("scripts/check_capability_synthesis.py", "check_capability_synthesis"),
    ("scripts/check_synthesis_discipline.py", "check_synthesis_discipline"),
    ("scripts/check_discovery_pipeline.py", "check_discovery_pipeline"),
    ("scripts/check_access_policy.py", "check_access_policy"),
    ("scripts/check_input_profilers.py", "check_input_profilers"),
    ("scripts/check_entitlements_wiring.py", "check_entitlements_wiring"),
    ("scripts/check_ml_model_registry.py", "check_ml_model_registry"),
    ("scripts/check_registry_layers.py", "check_registry_layers"),
    ("scripts/check_promote_tools.py", "check_promote_tools"),
    ("scripts/check_microsteps.py", "check_microsteps"),
    ("scripts/check_registry_storage_tiers.py", "check_registry_storage_tiers"),
    ("scripts/check_component_search.py", "check_component_search"),
    ("scripts/check_variation_store.py", "check_variation_store"),
    ("scripts/check_source_poller.py", "check_source_poller"),
    ("scripts/check_rule_generator.py", "check_rule_generator"),
    ("scripts/live_eval.py", "live_eval"),
    ("scripts/build_capability_assurance_surface.py", "build_capability_assurance_surface"),
    ("scripts/check_arch_flex.py", "check_arch_flex"),
    ("scripts/check_reranker_port.py", "check_reranker_port"),
    ("scripts/check_embedding_port.py", "check_embedding_port"),
    ("scripts/check_search_port.py", "check_search_port"),
    ("scripts/check_hybrid_retrieval.py", "check_hybrid_retrieval"),
    ("scripts/check_plane_io_contracts.py", "check_plane_io_contracts"),
    ("scripts/check_dag_contract.py", "check_dag_contract"),
    ("scripts/check_type_lattice.py", "check_type_lattice"),
    ("scripts/check_templates.py", "check_templates"),
    ("scripts/check_beam.py", "check_beam"),
    ("scripts/check_passes.py", "check_passes"),
    ("scripts/check_equivalence.py", "check_equivalence"),
    ("scripts/check_cascade.py", "check_cascade"),
    ("scripts/check_component_standardization.py", "check_component_standardization"),
    ("scripts/check_adapter_factory.py", "check_adapter_factory"),
    ("scripts/check_trust_tiers.py", "check_trust_tiers"),
    ("scripts/check_economic_layer.py", "check_economic_layer"),
    ("scripts/check_vertical_proof.py", "check_vertical_proof"),
    ("scripts/check_provider_directory.py", "check_provider_directory"),
    ("scripts/check_provider_sources.py", "check_provider_sources"),
    ("scripts/check_provider_directory_framework.py", "check_provider_directory_framework"),
    ("scripts/check_licensed_directory.py", "check_licensed_directory"),
    ("scripts/check_entity_resolver.py", "check_entity_resolver"),
    ("scripts/check_industry_links.py", "check_industry_links"),
    ("scripts/check_source_registry.py", "check_source_registry"),
    ("scripts/build_hub_browser.py", "build_hub_browser"),
    ("scripts/check_simulator.py", "check_simulator"),
    ("scripts/compile_capability_live.py", "compile_capability_live"),
    ("scripts/harvest_tools.py", "harvest_tools"),
    ("scripts/check_external_api_registry.py", "check_external_api_registry"),
    ("scripts/check_adjacent_verticals.py", "check_adjacent_verticals"),
    ("scripts/build_agentic_loop_viz.py", "build_agentic_loop_viz"),
    ("_repos/teleon/backend/src/teleon/research/llm_browser.py", "llm_browser"),
    ("scripts/check_capability_planner.py", "check_capability_planner"),
    ("scripts/repo_intake_strategize.py", "repo_intake_strategize"),
    ("scripts/build_intro_site.py", "build_intro_site"),
    ("scripts/share_intro_site.py", "share_intro_site"),
    ("scripts/check_repo_emit.py", "check_repo_emit"),
    ("scripts/build_hub_sites.py", "build_hub_sites"),
    ("scripts/scaffold_hub.py", "scaffold_hub"),
    ("scripts/hub_engine_runner.py", "hub_engine_runner"),
    # --- 2026-06-25 session seams: registered for gate coverage (closes the governance hole). The search trio is
    #     slated to consolidate behind retrieval/search_port + synthesis/component_search per the dev contract (#24). ---
    ("scripts/interrogation_engine.py", "interrogation_engine"),
    ("scripts/kickstart.py", "kickstart"),
    ("scripts/seed_ingest.py", "seed_ingest"),
    ("scripts/bot_swarm.py", "bot_swarm"),
    ("scripts/populate_loop.py", "populate_loop"),
    ("scripts/enrich_loop.py", "enrich_loop"),
    ("scripts/codeblock_enrich.py", "codeblock_enrich"),
    ("scripts/bench_token_usage.py", "bench_token_usage"),
    ("scripts/scale_index.py", "scale_index"),
    ("scripts/hybrid_search.py", "hybrid_search"),
    ("scripts/work_queue.py", "work_queue"),
    ("scripts/build_loop.py", "build_loop"),
    ("scripts/worktree_build.py", "worktree_build"),
    ("scripts/flywheel_status.py", "flywheel_status"),
    ("scripts/check_seha_boundary.py", "check_seha_boundary"),
    ("scripts/check_surface_and_dev_contract.py", "check_surface_and_dev_contract"),
    ("scripts/check_surface_server.py", "check_surface_server"),
    ("scripts/landing_server.py", "landing_server"),
    ("scripts/check_northstar_design.py", "check_northstar_design"),
    ("scripts/aidevobserver_demo_server.py", "aidevobserver_demo_server"),
    ("scripts/check_context_freshness.py", "check_context_freshness"),
    ("scripts/check_component_flow_diagram.py", "check_component_flow_diagram"),
    ("_repos/teleon/backend/src/teleon/monitoring/flywheel_queue.py", "flywheel_queue"),
    ("_repos/teleon/backend/src/teleon/demos/byo_key_demo.py", "byo_key_demo"),
    ("scripts/byo_demo_server.py", "byo_demo_server"),
    ("_repos/teleon/backend/src/teleon/tuning/action_ledger.py", "action_ledger"),
    ("_repos/teleon/backend/src/teleon/tuning/tuner.py", "tuner"),
    ("_repos/teleon/backend/src/teleon/storage/git_record_store.py", "git_record_store"),
    # ── OPERATIONAL CLOUD BACKEND WIRED: PostgresRecordStore (same RecordStore port as LocalRecordStore —
    #    content-addressed O(1) idempotency via ON CONFLICT, parameterized SQL) replaces _UnwiredCloudStore
    #    for the operational tier, and PostgresFleetLedger claims with FOR UPDATE SKIP LOCKED + LIMIT 1 so N
    #    workers claim concurrently WITHOUT serializing (the SQLite BEGIN IMMEDIATE path stays the default).
    #    Offline: imports + interface parity + parameterization (injection sentinel stays in params) +
    #    honest refusal without a DSN; live OH_PG_DSN round-trip otherwise skips honestly. serves_truth=false ──
    ("scripts/check_postgres_record_store.py", "check_postgres_record_store"),
    ("_repos/teleon/backend/src/teleon/storage/sync_engine.py", "sync_engine"),
    ("_repos/teleon/backend/src/teleon/infra/scale_ports.py", "scale_ports"),
    ("_repos/teleon/backend/src/teleon/examples/product_pipelines.py", "product_pipelines"),
    ("scripts/check_aidevobserver_vscode_ext.py", "check_aidevobserver_vscode_ext"),
    ("scripts/check_aidevobserver_mcp.py", "check_aidevobserver_mcp"),
    ("scripts/check_observer_local_service.py", "check_observer_local_service"),
    # the LIVE coaching path: a Claude Code PreToolUse hook over the observer router — footguns/reinvention
    # surfaced as non-blocking notes (read-class calls skipped, malformed events fail open, NEVER blocks); serves_truth=false
    ("scripts/aidevobserver_hook.py", "aidevobserver_hook"),
    ("_repos/teleon/backend/src/teleon/retrieval/learned_vectors.py", "learned_vectors"),
    ("_repos/teleon/backend/src/teleon/retrieval/pgvector_index.py", "pgvector_index"),
    ("_repos/teleon/backend/src/teleon/synthesis/codeblock_loop.py", "codeblock_loop"),
    ("_repos/teleon/backend/src/teleon/registry/browse.py", "browse"),
    ("scripts/openhubforai_browse_server.py", "openhubforai_browse_server"),
    ("_repos/teleon/backend/src/teleon/registry/index.py", "registry_index"),
    ("scripts/check_registry_reconciliation.py", "check_registry_reconciliation"),
    ("scripts/registry_api_server.py", "registry_api_server"),
    ("scripts/check_object_wrapper_hygiene.py", "check_object_wrapper_hygiene"),
    # ── Compiled primitive route benchmark seeds (claude-fable-compiled-primitive-routes handoff): the
    #    Compiled-Primitive-AI harness seed pack — benchmark sources/task demands/arms (cross-refs Benchmark Lab
    #    A0..A8 + L1..L7), path portfolios per layer (generate/search/plan/compile/run/prove/repair), PLUS the
    #    adaptive layer: model/LoRA/ranker/micro-agent lanes, trial runs, sprouting w/ held-out promotion,
    #    telemetry feedback loops, co-occurrence, cache policy, champion/challenger. Builder emits; checker
    #    enforces handoff rules + referential integrity + freshness (hand-edits go red). serves_truth=false ──
    ("scripts/build_compiled_primitive_route_benchmark_seeds.py", "build_compiled_primitive_route_benchmark_seeds"),
    ("scripts/check_compiled_primitive_route_benchmark_seeds.py", "check_compiled_primitive_route_benchmark_seeds"),
    # ── The verified→registry BRIDGE: verified factory candidates (verified_candidates/*) mapped into the
    #    edge-foundry card schema AIDevObserver searches, registered in registry_search._edge_foundry_paths().
    #    Closes the silo where generated+verified rows were never consumable. Regenerate the pack via
    #    _repos/shared-backend-components/scripts/load_verified_candidates_into_registry.py --write. ──
    ("scripts/check_verified_candidates_registry_load.py", "check_verified_candidates_registry_load"),
    # ── Step-path portfolio registry: the machine-readable "unlimited paths per step" catalog (scrape/build/test/
    #    benchmark/search/verify_bridge/compile/deploy/repair), every path referencing the REAL engine mode
    #    (parallel_paths) + the tracking ledger (DescentAttempt). Regenerate via
    #    _repos/shared-backend-components/scripts/build_step_path_portfolio_pack.py --write. ──
    ("scripts/check_step_path_portfolio_pack.py", "check_step_path_portfolio_pack"),
    # ── Two-lane raw-corpus intake for generated_primitive_packs/: (1) deterministic table→candidate converter
    #    (MD packs, zero model tokens) → verify → bridge; (2) prompt-queue builder that clusters the million-row
    #    compact seed ZIPs into bounded per-family briefs for the generation lanes. Both --self-test pure. ──
    ("scripts/build_raw_pack_primitive_candidates.py", "build_raw_pack_primitive_candidates"),
    ("scripts/build_prompt_queue_from_seeds.py", "build_prompt_queue_from_seeds"),
    # ── Consumption benchmark: fires 40 real dev + public-coding-benchmark (LeetCode/SWE-bench/HumanEval/
    #    Terminal-Bench/BFCL/AppWorld/MLE-bench/BigCodeBench) task queries at the LIVE registry and scores
    #    solver-route coverage + stringability + measured-vs-baseline token savings; meta-cards excluded so
    #    uncovered = real capability gap. --self-test is offline; --run fires live. ──
    ("scripts/run_primitive_consumption_benchmark.py", "run_primitive_consumption_benchmark"),
    # ── Solver-route composition demonstrator: the SLM-uplift thesis in code — 6 solver meta-primitives
    #    (decompose/select-match/order-compose/emit/verify/repair) + a real edge-chaining route composer that
    #    orders retrieved primitives output_edge->input_edge and accounts tokens vs a one-shot baseline. ──
    ("scripts/demo_solver_route_composition.py", "demo_solver_route_composition"),
    # ── Canonical edge-type vocabulary: the shared intermediate-TYPE system (28 types / 5 domains / 5 worked
    #    chains) that makes primitives COMPOSE — output_edge type_id == next input_edge type_id. The fix for the
    #    solver-demo composability=0 finding; generation lanes reference these ids so edges match. ──
    ("scripts/build_canonical_edge_type_vocabulary.py", "build_canonical_edge_type_vocabulary"),
    # ── Benchmark landscape catalog: 50 public 2025-2026 benchmarks (5 categories) → COMPUTED primitive-demand
    #    priority (verification/test-execution derived as #1). Research intake; scores NOT local truth. ──
    ("scripts/build_benchmark_landscape_catalog.py", "build_benchmark_landscape_catalog"),
    # ── Retrieval backend PORTFOLIO: single-source resolver for embedders/indexes/rerankers/search-methods
    #    (fixes the 4-disjoint-dim mess flexibly — one wired active default per kind + a hard dim-compat rule +
    #    an importable resolve_active_backends(); new backends/dims/methods are rows, not rewrites). ──
    ("scripts/build_retrieval_backend_portfolio.py", "build_retrieval_backend_portfolio"),
    # ── REAL fast inverted index for primitive-card search: closes the F5/storage-F1+F4 red-team gaps
    #    (live search was an O(N) ~13.7s linear scan over 115k cards; blocking keys didn't prune; mutations[]
    #    = 67.6% of bytes re-serialized every query). ADD-ONLY parallel PATH — imports the same card files,
    #    does NOT edit registry_search.py. Builds a df-capped inverted index (drops tokens in >5% of docs +
    #    path-debris stopwords), search docs EXCLUDE mutations/memory/cache, and fast_search prunes to a
    #    <=500 candidate set ranked by idf-weighted overlap — O(candidates), not O(N). ──
    ("scripts/build_primitive_search_index.py", "build_primitive_search_index"),
    # ── FULL-CORPUS search tier: streams ALL ~1.17M records (seed/edge/draft/gap-fill) into the search-doc shape
    #    (no code body) -> SEPARATE persisted tier (curated default untouched); measures reach-lift + precision.
    #    CORRECTED 2026-07-08: a NAIVE union on a SMALL, reach-saturated eval (400 queries, baseline reach already
    #    1.0) dips top-1 slightly — a RANKING/WEIGHTING signal, NOT evidence "more rows hurt" (too small to conclude).
    #    More rows is the substrate; the fix is tier-weighted + diversity rerank (weighted_corpus_search) + a
    #    disable/weight control + a MUCH larger eval — never reject rows (non-destructive-router law). candidate-only. ──
    ("scripts/full_corpus_search_index.py", "full_corpus_search_index"),
    ("scripts/weighted_corpus_search.py", "weighted_corpus_search"),
    # ── "Retrieve capabilities not code" MCP transport (the PMF surface): a stdlib JSON-RPC/MCP server over stdio
    #    exposing primitive_search (fast_search over the df-capped inverted index — O(candidates)) + find_reuse
    #    (reinvention_guard.check, grounded in the federation). ADD-ONLY — wires two existing engines, builds none.
    #    --self-test runs one search + one reuse check OFFLINE through the real tools/call envelope; serves_truth=false. ──
    ("scripts/capability_retrieval_mcp_server.py", "capability_retrieval_mcp_server"),
    # ── MCP stdio transport, single-sourced (scripts/_mcp_stdio.py): the ONE newline-delimited (MCP spec) framing +
    #    read/write/serve loop shared by every MCP server. Extracted after two WIRED gateways (baltor/teleon) were
    #    found speaking Content-Length (LSP framing) — broken against a real client (Claude Code) that writes bare
    #    JSON lines. Self-test proves read/write/serve, -32700 on a malformed line, -32603 on a handler crash. ──
    ("scripts/_mcp_stdio.py", "_mcp_stdio"),
    # ── Teleon + AIDevObserver MCP gateways (OFFLINE dispatch proofs over the shared transport): tools/list + a
    #    tools/call routed through the in-process projection / observer engine; serves_truth=false. These self-tests
    #    existed but were never in the umbrella — registering them closes that gap. (baltor's gateway forwards to a
    #    live HTTP backend, so it is not umbrella-hermetic and stays out.) ──
    ("scripts/teleon_capability_gateway_mcp.py", "teleon_capability_gateway_mcp"),
    ("scripts/aidevobserver_mcp_server.py", "aidevobserver_mcp_server"),
    # ── REAL executable mutators + proof-runner: the fix for "mutators are 2.7M vocabulary strings, 0 proven".
    #    MUTATOR_REGISTRY (name->callable, transforms DATA), run_primitive_proof executes proofs vs fixtures and
    #    promotes serves_truth false->true ONLY on pass — the first proven primitives in repo history. ──
    ("scripts/mutator_registry.py", "mutator_registry"),
    # ── Proven leaf primitives: closes red-team gap F6. Declares >=20 REAL deterministic leaf primitives
    #    (parse/validate/hash/dedupe/normalize/cast/envelope/idempotency/roundtrip/schema/base64/kv/…), runs each
    #    through the IMPORTED run_primitive_proof, and persists the passing ProofReceipts (serves_truth=true,
    #    L7_executed_proof). ADD-ONLY parallel path (imports mutator_registry, registers extra pure mutators into
    #    the shared registry) — moves the proven count from 2 to 26. proven_primitive_index() exposes them. ──
    ("scripts/prove_leaf_primitives.py", "prove_leaf_primitives"),
    # ── Primitive pipeline catalog intake (owner-provided primitive_pipeline_catalog_8000.md): one intake,
    #    four lanes — lossless staged rows, deduped deterministic verifier-shape cards (batch_runs c8kdet),
    #    Ollama shards for GLM/Kimi/Gemma family expansion (daily_shards_catalog8k c8k1), and Fable ultracode
    #    workflow briefs (uc02: catalog decompositions + place/open-data/geospatial, entity-resolution,
    #    similarity/indexing, visual/math, rendering, algorithms, guardrails, company-surface lanes).
    #    All outputs candidate=true / serves_truth=false; verification never promotes truth. ──
    ("scripts/build_primitive_pipeline_catalog_intake.py", "build_primitive_pipeline_catalog_intake"),
    ("scripts/report_multilane_primitive_generation.py", "report_multilane_primitive_generation"),
    # ── Red-team 9-fix foundations (F2 edge-type retrofit + F1 composability gate): the retrofit folds
    #    the ~4.4k free-text edge strings into 636 canonical types (canonicalize_edge), and the additive
    #    composability gate rejects edge_untyped / route-unreachable cards (measured 14.8% corpus pass —
    #    LOW is the finding). check_edge_type_retrofit validates the pack; neither edits a contract-locked file. ──
    ("scripts/build_edge_type_retrofit.py", "build_edge_type_retrofit"),
    ("scripts/check_edge_type_retrofit.py", "check_edge_type_retrofit"),
    ("scripts/check_primitive_composability.py", "check_primitive_composability"),
    # ── Maximum-flexibility layer: every runtime decision point (canonicalizer/search/composer/reranker/
    #    proof-policy) is a portfolio of contract-substitutable paths + tunable parameters behind one selector;
    #    ACTIVE_DEFAULT reproduces current behavior (replaces nothing), every choice emits a DecisionReceipt. ──
    ("scripts/primitive_paths_config.py", "primitive_paths_config"),
    # ── Verify-the-verifier gate #3 (quality ratchet): headline metrics (composability %, proven count,
    #    canonical-type count/coverage, wired-path count) recorded as candidate floors from computed manifests;
    #    a silent regression below a floor is a hard failure; unsupplied externals are gaps, not fake passes. ──
    ("scripts/check_quality_ratchet.py", "check_quality_ratchet"),
    # ── Red-team 9-fix wired runtime (F5 fast search + F7 edge-type rerank + F8 peel-back + executed proof,
    #    2026-07-03): build_primitive_search_index emits an inverted index whose fast_search prunes candidates;
    #    prove_leaf_primitives runs REAL leaf primitives through the imported executed-proof runner (proven count
    #    moved 2 -> 26, serves_truth=true only on an executed L7 proof); primitive_runtime wires the unplugged
    #    machinery into ONE decompose->search->classify->rerank->compose->peel-back->prove path (IMPORTS the
    #    contract-locked machinery, edits nothing); run_runtime_benchmark is the OLD-vs-NEW labeled composability
    #    harness. All offline + deterministic; only executed-proof primitives serve truth.
    #    (build_primitive_search_index + prove_leaf_primitives are already registered above.) ──
    ("scripts/primitive_runtime.py", "primitive_runtime"),
    ("scripts/run_runtime_benchmark.py", "run_runtime_benchmark"),
    # ── Intake + bake-off + benchmark-suite + path-selection (the "add primitives / benchmark / race paths"
    #    layer): add_primitive is the one-call gated intake (normalize->composability->dedupe->proof->store);
    #    run_path_bakeoff races 5 processing paths on the same input via the real run_parallel comparator
    #    (per-class winners; no single path dominates); build_benchmark_suite_registry is the pick-a-backend
    #    portfolio; run_code_execution_benchmark actually executes routes in-process; path_selection_policy
    #    derives the per-class routing table from the live leaderboard. All candidate-only except executed proofs. ──
    ("scripts/add_primitive.py", "add_primitive"),
    ("scripts/run_path_bakeoff.py", "run_path_bakeoff"),
    ("scripts/build_benchmark_suite_registry.py", "build_benchmark_suite_registry"),
    ("scripts/run_code_execution_benchmark.py", "run_code_execution_benchmark"),
    ("scripts/path_selection_policy.py", "path_selection_policy"),
    # ── Publisher front door: API providers publish primitives + common use-cases as governed CANDIDATES —
    #    signed provenance required (no anonymous truth), same gates as everything (composability + executed
    #    proof / gated-effect + dedupe), inline code sandboxed, use-cases type-validated, review-ticketed. ──
    ("scripts/publish_primitive.py", "publish_primitive"),
    # -- Proven leaf families (14): deterministic leaf primitives, executed-proven + typed (serves_truth=true ONLY on a passing proof); moved proven count 26 -> 500+ --
    ("scripts/prove_leaves_aggregation_reduce.py", "prove_leaves_aggregation_reduce"),
    ("scripts/prove_leaves_datetime_deterministic.py", "prove_leaves_datetime_deterministic"),
    ("scripts/prove_leaves_dict_mapping.py", "prove_leaves_dict_mapping"),
    ("scripts/prove_leaves_encoding_codec.py", "prove_leaves_encoding_codec"),
    ("scripts/prove_leaves_hashing_checksum.py", "prove_leaves_hashing_checksum"),
    ("scripts/prove_leaves_json_csv_transform.py", "prove_leaves_json_csv_transform"),
    ("scripts/prove_leaves_list_sequence.py", "prove_leaves_list_sequence"),
    ("scripts/prove_leaves_numeric_math.py", "prove_leaves_numeric_math"),
    ("scripts/prove_leaves_record_normalization.py", "prove_leaves_record_normalization"),
    ("scripts/prove_leaves_set_relational.py", "prove_leaves_set_relational"),
    ("scripts/prove_leaves_structural_reshape.py", "prove_leaves_structural_reshape"),
    ("scripts/prove_leaves_text_string.py", "prove_leaves_text_string"),
    ("scripts/prove_leaves_type_coercion.py", "prove_leaves_type_coercion"),
    ("scripts/prove_leaves_validation_predicate.py", "prove_leaves_validation_predicate"),
    # -- Proven composite routes (4): multi-step canonical-TYPE chains proven end-to-end (edge_chain_strength>1) --
    ("scripts/prove_composite_entity_resolution.py", "prove_composite_entity_resolution"),
    ("scripts/prove_composite_etl_intake.py", "prove_composite_etl_intake"),
    ("scripts/prove_composite_rag_prep.py", "prove_composite_rag_prep"),
    ("scripts/prove_composite_validation_gate.py", "prove_composite_validation_gate"),
    # -- Parametric generators (8): ~19,250 configured-primitives via parametric proof (template x curated binding), each executed-proven + typed + deduped; honest generated/unique/proven/typed counts --
    ("scripts/generate_parametric_aggregation.py", "generate_parametric_aggregation"),
    ("scripts/generate_parametric_codec_hash.py", "generate_parametric_codec_hash"),
    ("scripts/generate_parametric_numeric_transform.py", "generate_parametric_numeric_transform"),
    ("scripts/generate_parametric_projection_selection.py", "generate_parametric_projection_selection"),
    ("scripts/generate_parametric_relational_structural.py", "generate_parametric_relational_structural"),
    ("scripts/generate_parametric_text_ops.py", "generate_parametric_text_ops"),
    ("scripts/generate_parametric_type_coercion.py", "generate_parametric_type_coercion"),
    ("scripts/generate_parametric_validation_rules.py", "generate_parametric_validation_rules"),
    # -- Similarity + dedupe + benchmarks (4): multi-method similarity portfolio (edge_type/lexical/MinHash-LSH/fingerprint), near-dup clustering, similarity-retrieval + parametric-coverage benchmarks --
    ("scripts/primitive_similarity_portfolio.py", "primitive_similarity_portfolio"),
    ("scripts/cluster_primitive_duplicates.py", "cluster_primitive_duplicates"),
    ("scripts/run_similarity_retrieval_benchmark.py", "run_similarity_retrieval_benchmark"),
    ("scripts/run_parametric_coverage_benchmark.py", "run_parametric_coverage_benchmark"),
    # -- Domain-breadth (12): formats/cloud/industry/mediums; deterministic shape/parse/validate work executed-proven+typed, network CALLS as gated-effect candidates (serves_truth=false); no insurance, healthcare-admin only --
    ("scripts/domain_cloud_aws.py", "domain_cloud_aws"),
    ("scripts/domain_cloud_azure_k8s.py", "domain_cloud_azure_k8s"),
    ("scripts/domain_cloud_gcp.py", "domain_cloud_gcp"),
    ("scripts/domain_fmt_columnar_schema.py", "domain_fmt_columnar_schema"),
    ("scripts/domain_fmt_domain_messages.py", "domain_fmt_domain_messages"),
    ("scripts/domain_fmt_geo_calendar.py", "domain_fmt_geo_calendar"),
    ("scripts/domain_fmt_markup_config.py", "domain_fmt_markup_config"),
    ("scripts/domain_ind_finance_adjacent.py", "domain_ind_finance_adjacent"),
    ("scripts/domain_ind_healthcare_admin.py", "domain_ind_healthcare_admin"),
    ("scripts/domain_ind_logistics_retail_telecom.py", "domain_ind_logistics_retail_telecom"),
    ("scripts/domain_med_message_shapes.py", "domain_med_message_shapes"),
    ("scripts/domain_med_more_operations.py", "domain_med_more_operations"),
    # -- Context reorg tooling: deterministic component classifier (plan), lossless git-mv mover with lineage
    #    manifest (execute), and the moved-doc reference rewriter (rewrite). ADD-ONLY; move-never-delete law. --
    ("scripts/plan_context_reorg.py", "plan_context_reorg"),
    ("scripts/execute_context_reorg.py", "execute_context_reorg"),
    ("scripts/rewrite_context_refs.py", "rewrite_context_refs"),
    # -- Migration foundation: cross-repo dependency-law checker (portable, in _repos/dev-rules-context/tools) proven via
    #    its own --self-test here; migration cleanup-candidate finder (report-only, move-never-delete). --
    ("scripts/find_migration_cleanup_candidates.py", "find_migration_cleanup_candidates"),
    # -- Repo-staging migration: mirror the multi-repo layout under _repos/ (stage_repos, directory git-mv +
    #    lineage) and rewrite refs to the new locations (rewrite_repo_stage_refs). Move-never-delete. --
    ("scripts/stage_repos.py", "stage_repos"),
    ("scripts/rewrite_repo_stage_refs.py", "rewrite_repo_stage_refs"),
    # -- Bridge: the edge/graph/interface tools now live in _repos/ (their future repos); this runs their
    #    --self-tests so cross-repo dependency law + edge digests + versioned interface relationships stay green. --
    ("scripts/check_repos_edge_tools.py", "check_repos_edge_tools"),
    # -- Monorepo->multirepo migration plan: two-level surface->project flatten, per-project manifests,
    #    history-preserving git-subtree extraction order, shared devkit. --
    ("scripts/build_migration_plan.py", "build_migration_plan"),
    # -- Deterministic MAINTAINER: one command regenerates edges/graph/interfaces/migration-plan from the
    #    single-source registry + scans context MD for staleness. Keeps the org from drifting as it grows. --
    ("scripts/refresh_all.py", "refresh_all"),
    # -- Verify-the-verifier for the ORG: the drift GATE. Regenerates every derived artifact (edges/graph/
    #    interfaces/migration-plan) from the registry into a temp dir + diffs; fails if anything drifted. --
    ("scripts/check_org_freshness.py", "check_org_freshness"),
    # -- Deterministic ONBOARDING agent: add a new component/repo (surface or project) in ONE command — append
    #    the single-source registry, validate against the reused dependency law, ADD-ONLY folder scaffold from
    #    the shared template (no existing entry clobbered), then defer derived artifacts to refresh_all. --
    ("scripts/scaffold_component.py", "scaffold_component"),
    ("scripts/_repo_paths.py", "_repo_paths"),
    ("scripts/decouple_repo_root.py", "decouple_repo_root"),
    ("scripts/migrate_dir_to_repo.py", "migrate_dir_to_repo"),
    # -- REASONING / CONTROL / PROOF primitives: primitives that are reasoning scaffolds (chain-of-thought,
    #    decomposition), decision GATES, invariant guards, mathematical PROOF-OBLIGATION checkers (graph
    #    k-coloring certificate, natural-deduction inference chain), and GUIDED ROUTES that steer an agent
    #    down one edge-typed path. Unlike opaque code, the gate/proof/invariant checkers are DETERMINISTIC
    #    (they run + pass oracles here), so they are the primitives that can most easily serve truth. Typed
    #    edges → compose through the same compatibility lattice. candidate-only, serves_truth=false. --
    ("scripts/reasoning_control_and_proof_primitives.py", "reasoning_control_and_proof_primitives"),
    # -- BRAIN-INSPIRED (BDH / Dragon Hatchling arXiv:2509.26507) esoteric kernels as deterministic,
    #    oracle-verified primitives: hebbian_update (fire-together-wire-together) · scale-free graph
    #    (preferential attachment) · leaky integrate-and-fire (spiking) · excitatory/inhibitory k-WTA ·
    #    sparse-positive monosemantic code · linear-attention synaptic memory (unbounded context, no KV). --
    ("scripts/brain_inspired_primitives.py", "brain_inspired_primitives"),
    # -- PHYSICS-INFORMED TRACKING kernels mined from the ROGII geosteering decomposition (owner-provided
    #    Kaggle notebook, seed `kaggle-rogii-wellbore-pf-gbm-notebook`): particle-filter tracker · systematic
    #    resample · effective-sample-size · beam-search grid decoding · NCC template match · robust IRLS
    #    polyfit · likelihood-weighted seed ensemble · IDW spatial impute · exponential warm-up blend ·
    #    backtest-gated override · confidence-gated blend · prediction integrity audit. Pure python, seeded
    #    LCG only, every kernel behind a mutation-sensitive executed oracle; cards carry 3-register
    #    descriptions (plain/technical/semantic) + typed edges. candidate-only, serves_truth=false. --
    ("scripts/physics_tracking_primitives.py", "physics_tracking_primitives"),
    # -- MATHEMATICAL-FOUNDATIONS kernels from the owner's 100M alignment layer (seed
    #    `owner-primitive-100m-mathematical-layer-2026-07-11`), reference numbers pinned as oracles:
    #    identity-bits floor (log2 1e8=26.5754) · cascade ordering by c/(1-s) (brute-force-matched) · SPRT
    #    boundaries+decisions · inverse-propensity off-policy estimate · SimHash collision law · LSH banding
    #    S-curve · Bloom sizing (1e8@1% -> 958,505,838 bits/7 hashes) · Count-Min dims (2719x14) ·
    #    exact majority-vote failure · GF(2) parity syndromes · MDL promotion gate. Pure python, no
    #    randomness; 3-register descriptions + typed edges. candidate-only, serves_truth=false. --
    ("scripts/math_foundations_primitives.py", "math_foundations_primitives"),
    # -- ASSOCIATIVE-MEMORY / fast-weight kernels from the owner-forwarded BDH research verdict (seed
    #    `owner-bdh-research-verdict-2026-07-11`), its THEOREMS as oracles: hebbian write/read · exact
    #    crosstalk bill · delta-rule write (exact overwrite, non-expansive) · erase-then-write · decay
    #    norm bound ((1-l)^t*M0 + R/l) · positive-sparse overlap bias s/D (exact enumeration) ·
    #    contraction forgetting rho^k · multi-timescale power-law mixture (log-ratio stability) ·
    #    persistent occupancy 1-(1-p)^T · exact-recall state floor n*log2(V) · linear-memory rank limit
    #    (d exact, d+1 provably impossible). Pure python, no randomness; 3-register descriptions + typed
    #    edges. candidate-only, serves_truth=false. --
    ("scripts/associative_memory_primitives.py", "associative_memory_primitives"),
    # -- VERIFIED-REUSE gate (the wedge): given a primitive with a declared contract AND runnable
    #    behavior, check the behavior CONFORMS to the declaration — typed edges, every declared output
    #    field is produced, the card's own proof_requirement fixture passes, and NO undeclared effects —
    #    then mint a signed conformance attestation (reuses verify_card + primitive_attestation). Answers
    #    the market's ~80% declaration-vs-behavior skill mismatch: a lying card is CAUGHT, never attested;
    #    a no-behavior scaffold is honestly "unverifiable", never falsely verified. candidate-only. --
    ("scripts/declaration_behavior_conformance.py", "declaration_behavior_conformance"),
    # -- EDGE-ONLY PACKAGE PRIMITIVES: searchable description + typed edges + dimensions + a LINK to code
    #    already maintained by others (crates.io/npm/PyPI) — we don't rewrite or host their raw code
    #    (hosts_raw_code=false; policy link-only, cache only if the license permits, else rewrite). Carries
    #    a compact USAGE-RECIPE zoo (import x; y=x(); y.method()) so an LLM INVOKES the package in ~tens of
    #    tokens instead of reading its files. Storage-light (bytes/primitive), candidate-only. --
    ("scripts/edge_only_package_primitives.py", "edge_only_package_primitives"),
    # -- EDGE-ONLY caveat fix: introspect the REAL installed package API (python stdlib corpus), DERIVE
    #    usage recipes from real callables+signatures, and VERIFY every recipe symbol resolves — a recipe
    #    naming a symbol the API doesn't expose is caught (declaration_behavior_conformance for a package
    #    surface). Closes "edge not verified vs API" + "hand-curated not derived". candidate-only. --
    ("scripts/edge_only_package_introspection.py", "edge_only_package_introspection"),
    # -- EDGE-ONLY token savings PROOF (both planes): plane A = ThinkingCap reasoning-token cut ~45.8%
    #    (CITED, BottleCap, matched-Δ%); plane B = MEASURED on the real stdlib — INPUT ~694x less to read
    #    (recipe vs package source), OUTPUT ~134x less to emit (invoke vs introspectable reimpl). Pure-C
    #    modules honestly marked (no fabricated baseline). The planes stack. candidate-only. --
    ("scripts/edge_only_token_savings.py", "edge_only_token_savings"),
    # -- EDGE-ONLY capability-class TEMPLATES: 13 classes (serialize/http_client/validate/parse/…) each with
    #    canonical typed edges + recipe shape + scrapable dims + cross-ecosystem examples (52 use-cases).
    #    Onboard a package = pick a class + fill the handle → valid edge-only skeleton. The format standard. --
    ("scripts/edge_only_capability_templates.py", "edge_only_capability_templates"),
    # -- EDGE-ONLY HARVESTER: scale the corpus from curated cards to a REAL API-verified corpus by
    #    introspecting the installed packages — derive recipes from real callables+signatures (all
    #    symbols resolve), classify by capability class on TOKEN boundaries, pull license/dims from
    #    metadata. ~2.7KB/card, candidate-only; persist is opt-in (--run). --
    ("scripts/edge_only_package_harvester.py", "edge_only_package_harvester"),
    # -- DETERMINISTIC CAPABILITY PLANE (0-token: descriptions · edges · remixing · self-tuning). Where a
    #    thing can be COMPUTED it costs 0 tokens, runs instantly, is byte-identical + verifiable. descriptions:
    #    3 searchable registers from card structure; edges: one canonical type vocabulary so independent
    #    primitives touching the same type join EXACTLY; remix: 0-token exact-typed-join composition with a
    #    correct-by-construction wiring recipe; plane: self-tunes the edge strategy per corpus (canonical beats
    #    raw: 0→>0 exact joins) + rolls up the savings. The honest-ledger robust win, productized. --
    ("scripts/deterministic_description.py", "deterministic_description"),
    ("scripts/deterministic_edge_derivation.py", "deterministic_edge_derivation"),
    ("scripts/deterministic_remix.py", "deterministic_remix"),
    ("scripts/deterministic_plane.py", "deterministic_plane"),
    # -- CAPABILITY LANE: the serve-time lane wiring the edge-only + deterministic capabilities into the
    #    gateway (agent actions capability.search/get/remix/stats + trial-allowed). Loads curated +
    #    API-introspected + a real aligned pipeline backbone, deterministically enriched; remix returns
    #    0-token exact-typed-join chains + wiring, refuses unreachable. candidate-only. --
    ("scripts/capability_lane.py", "capability_lane"),
    # -- CAPABILITY OPS: edge-only add/test + serve-time TELEMETRY (digest-privacy) + ANALYTICS rollup +
    #    ADJUSTABLE weights/ranking + deterministic SEMANTIC summary (class/edge clusters, coverage gaps).
    #    Wired into the agent tool (capability.analytics/reuse/add + telemetry on search/get/remix). --
    ("scripts/capability_ops.py", "capability_ops"),
    # -- CAPABILITY CLASSIFIER: class from name+summary+API SYMBOL-VERBS over 21 classes (dumps->serialize,
    #    connect->database, render->template); reclassify upgrades the persisted harvest in place. --
    ("scripts/capability_classifier.py", "capability_classifier"),
    # -- TAEDRI WEB: serve the Claude Design screens (.dc.html) from the gateway. One DC->production runtime
    #    (interprets sc-if / {{ }} / style-hover / DCLogic) + transform + route map, each screen wired to real
    #    same-origin endpoints. Landing live: renders in a real browser, corpus counter from /v1/stats/domains. --
    ("scripts/taedri_web.py", "taedri_web"),
]
