# Baltor Lossless Distillation + Parallel Runtime — workflow spec

> Owner law (2026-06-05). Canonical principle: `docs/codex/lossless-distillation.md`. This workflow
> makes the [[lossless-distillation-law]] a first-class subsystem with contracts, stores, and proofs.
> Build discipline = same as the other factories: build agents create ONLY isolated new files + run
> ONLY their own proofs; MAIN integrates shared manifests (PROOF_MODULES, section_maturity_matrix,
> contract_registry, opportunities, admin server) serially behind a full-flywheel gate. Determinism in
> every proof (injected time, hashlib ids, no RNG, temp dirs, offline). No commit/push/pip/containers/
> network/secrets. No second runtime/bus/worker/ledger/gateway/optimizer/parser/consumption-service.

## Core invariant
DISTILLATION MUST BE LOSSLESS AT THE SYSTEM LEVEL. A derived artifact may be smaller/cleaner/optimized,
but the system retains raw + normalized + intermediates + all source handles + held-out + rejected +
model/tool traces + transform configs + version hashes + receipts + rollback links. Omitted/held-out/
rejected/superseded ≠ deleted. No destructive overwrite, irreversible compression, hidden replacement,
lossy truth promotion, winner without lineage to losers, or distillation without a rehydration path.

## Promotability test (every derived artifact must answer, else NOT promotable)
which raw/source + source handle backs me · which transform/version/config/model/rule made me · what was
omitted/held-out · which candidates competed · prior active version · how to roll back · which proof says
I'm safe to serve.

## Global rule — DistillationRun on every transform
Fields: run_id, tenant_id, source_scope, input_artifact_ids, input_hashes, output_artifact_ids,
output_hashes, transform_type, transform_purpose, processor_id, processor_version, pipeline_id,
pipeline_version, config_hash, prompt_hash (if LLM), model_id/version (if LLM), provider_id (if provider),
rule_id/version (if deterministic), created_at (injected), lineage, receipts, omitted_artifact_ids,
held_out_artifact_ids, rejected_candidate_ids, monitoring_policy_id, rollback_target_id.

## Parts (each = contract + impl behind a port + proof + docs; build in isolated lanes)
1. **Contracts** `schemas/distillation/*.v1` — DistillationRun, DistillationCandidate, DistillationDelta,
   LineageBundle, ParallelRunGroup, ShadowRun, PromotionRecord, RollbackPlan, RehydrationReport,
   InformationRetentionReport, MonitoringSignal (+valid & invalid examples). Register in
   contract_registry. Proof: check_lossless_distillation_contracts (requires input+output ids,
   config_hash|rule_version, lineage, omitted/held_out/rejected lists even if empty; PromotionRecord
   requires rollback target; RehydrationReport requires reachable source artifacts).
2. **Lossless store** `src/baltor/distillation/{lossless_store,lineage,rehydration,rollback}.py` —
   append-only raw/source/derived; current pointer moves but old versions never disappear; payload_ref to
   content-addressed/object storage; no transform overwrites input payload; deletion needs retention
   policy + tombstone receipt (tombstone keeps lineage); tenant_private never enters global_public lineage.
   Proof: check_lossless_artifact_store.
3. **LineageBundle** for every promoted artifact (source/raw/parent ids, transform_run_ids, versions,
   handles, receipts, held_out/rejected ids, prior_version_ids, rollback_target_ids). Proof:
   check_lineage_bundle_complete (served fact reaches raw/source; optimized pack reaches baseline; rule
   reaches its LLM/human/adjudicated traces; reconciliation reaches winner AND loser; no empty handles).
4. **Rehydration** — rehydrate_artifact / _response / _canonical_fact / _distillation_run(id, tenant).
   Proof: check_distillation_rehydration (atomic fact→source field→raw record; optimized→baseline;
   ContextResponse→served facts + held-out warnings; FAQ-30 held-out → rehydrates to source + reconciliation
   receipt; no cross-tenant rehydration).
5. **InformationRetentionReport** — counts + source_handle_coverage (100% for served) +
   dropped_source_handle_count (0 for promotable) + orphaned in/out (0 / explained) + raw_rehydration_passed
   + lineage_complete + lossy_transform_declared/allowed (false for truth) + safe_to_promote. Proof:
   check_information_retention_report (compression dropping handles fails; dedupe erasing loser lineage
   fails; summary omitting held-out warnings fails; duplicate facts collapse only if both lineages survive).
6. **Side-by-side runs** ParallelRunGroup — baseline + candidates on the same source_snapshot_hash;
   separate outputs; diff report; promotion deletes neither; rollback target recorded. Proof:
   check_side_by_side_runs.
7. **Parallel candidate execution** (durable workers) — ≥3 candidates vs baseline; isolated failures;
   metrics; unpromoted never served; idempotent reruns. Proof: check_parallel_candidate_execution.
8. **Shadow mode** ShadowRun — rule runs alongside live path, recorded, non-authoritative; unsafe
   mismatch blocks promotion. Proof: check_shadow_mode_side_by_side.
9. **Monitoring** MonitoringSignal — handle coverage, held-out-leak, unresolved-conflict-leak,
   stale-served, tenant-leak, rehydration-failure, rollback, disagreement, shadow-mismatch,
   candidate-failure, proof-failure, latency/token/cost/queue-lag. Proof: check_distillation_monitoring
   (red status can trigger rollback or hold-out).
10. **Rollback** RollbackPlan + commands distill.rollback.{plan,execute,verify} — moves active pointer
    only; never deletes candidate; writes receipt; re-runs verification/consumption smoke; tenant-scoped.
    Proof: check_distillation_rollback.
11. **Durable commands** distill.{propose_candidate,run_candidate,run_parallel_group,compare_outputs,
    run_shadow,promote,rollback,monitor,rehydrate,retention_report} — CommandEnvelope, idempotent, events,
    receipts, durable worker path, safe-fail invalid. Proof: check_distillation_worker_commands
    (two workers don't duplicate outputs).
12. **API** (projection-safe; MAIN wires monolith) GET /api/distillation/{runs,runs/<id>,candidates,
    parallel-groups,shadow-runs,promotions,rollback-plans,monitoring}; POST {rehydrate,rollback,
    run-candidate} (mutations via runtime/worker). Proof: check_distillation_api.
13. **UI** /distillation (raw/source/derived, runs, candidates, parallel groups, shadow, retention,
    rehydration viewer, promotions, rollback, monitoring, held-out, rejected, lineage graph; projection-
    only). Proof: check_distillation_ui.
14. **CFPB reference lossless** — raw/source/field/atomic_fact preserved; FAQ-30 + allegations held out but
    rehydratable; Reg-E 10 served; optimized pack has baseline lineage; rejected candidates queryable;
    rollback plan exists; answer stays "10 business days". Proof: check_cfpb_lossless_distillation.
15. **LLM→rule lossless** — LLM traces + consensus + adjudication + rule candidate + replay + shadow +
    promotion receipt all preserved; LLM stays fallback until a retirement proof; rule never overwrites
    trace history; old LLM path re-enablable. Proof: check_llm_to_rule_lossless_distillation. (Ties into
    [[determinism-factory-distill-from-verified]].)
16. **Optimization-as-distillation** — baseline + all/rejected candidates preserved; best promoted with
    receipt; compression can't lose handles; held-out warnings stay visible; unpromoted never served.
    Proof: check_optimization_lossless_distillation.
17. **Ingestion/decomposition lossless** — raw payload + normalized + parse tree + decomposed facts +
    held-out allegations + handles preserved; parser candidates stored side-by-side; parser replacement
    never deletes old parse tree. Proof: check_ingestion_decomposition_lossless.
18. **Red-team** check_lossless_distillation_redteam — all FAIL SAFELY: delete raw after distillation;
    overwrite baseline with optimized; drop handles in compression; hide FAQ-30 instead of holding out;
    delete rejected candidate; promote without rollback; promote rule without shadow; tenant_private→global
    rule; serve candidate directly; make old ContextResponse unreadable; rehydrate across tenant boundary.
19. **Docs** docs/distillation/{overview, lossless-principle, lineage-bundles, rehydration,
    information-retention-reports, parallel-runs, shadow-mode, monitoring, rollback, cfpb-example,
    llm-to-deterministic-rules, optimization-as-distillation, redteam}.md (Purpose/Owner/Contracts/Inputs/
    Outputs/Proofs/Commands/Limitations/Next). Proof: check_lossless_distillation_docs.
20. **Master proof** check_lossless_distillation_full_stack — prints
    TRANSFORM | RAW PRESERVED | LINEAGE | REHYDRATION | SIDE_BY_SIDE | MONITORING | ROLLBACK | PROOF | STATUS;
    every critical-path transform green.

## Regression after build
check_consumption_service, check_optimization_suite, reconciliation CFPB reference, ingestion full stack,
check_durable_worker_parallel, no-consumption-bypass, no-direct-provider-bypass, section_maturity_matrix,
baltor_full_stack_perfect, baltor_flywheel --once.

## Acceptance (A–T)
No transform deletes raw/source; every derived artifact has lineage + rehydration; optimization preserves
baseline + rejected; LLM→rule preserves traces; side-by-side/parallel/shadow/monitoring/rollback work;
CFPB stays "10 business days"; FAQ-30 + allegations held out but rehydratable; handles survive every
transform; compression can't drop handles; reconciliation can't erase loser lineage; tenant-private
lineage can't go global; APIs/UI projection-only; red-team attacks fail safely; flywheel green.

## LOSSLESS DISTILLATION CLAUSE (carry verbatim into every workflow prompt)
Any distillation, decomposition, compression, optimization, reconciliation, promotion, or LLM-to-rule
conversion must be lossless at the system level. Never overwrite or delete raw/source/intermediate
artifacts. Every derived artifact must preserve source handles, lineage, transform config, version,
receipts, held-out items, rejected candidates, and a rollback target. Run side-by-side before promotion,
run shadow mode for new rules, monitor after promotion, and prove rehydration. Omitted means held out or
excluded from a view, never erased.
