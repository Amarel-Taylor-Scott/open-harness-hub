# Baltor Determinism Factory — queued workflow spec

> Owner directive (2026-06-05): convert repeated LLM / multi-LLM / heuristic /
> human-reviewed (non-deterministic) workflow **decisions** into deterministic rules
> over time, on **verified** data. Sibling to the Pattern & Standards Factory:
> - Pattern & Standards Factory → repeated **code/workflow** shapes ("we keep writing the same source adapter").
> - Determinism Factory → repeated **decision** shapes ("the LLM keeps making the same classification and the validator keeps agreeing").

## Core principle
**LLMs propose. Baltor verifies. Repeated *verified* patterns become deterministic.**
Distill from **adjudicated, source-grounded, receipt-backed outcomes — NOT raw LLM output.**
Multi-LLM consensus = evidence / ambiguity signal, **not truth**. The deterministic validator
or authority/policy produces the label.

## Non-negotiable safety reframe (apply during build)
Baltor reconciliation (`scripts/artifact_graph/reconciliation.py` + `conflict_detector.py`),
the consumption gate, and the optimizer **are already deterministic authorities.** The Determinism
Factory is a **META / observe-shadow-promote ledger over them** — it must NOT create a second
reconciliation authority, second optimizer, second rule engine, second LLM gateway, or second
runtime. The CFPB / optimization "distillation" proofs assert the mined rule **reproduces the
existing reference outcome**; they never become a competing source of truth. Reference invariant holds:
answer "10 business days"; FAQ "30 days" held out only.

## The maturity ladder (M0–M8) for every non-deterministic slice
- M0 raw LLM output (risky, no schema)
- M1 LLM output + JSON schema (structured, not trusted)
- M2 multiple LLMs produce candidates (agreement/disagreement recorded)
- M3 candidates checked by deterministic validators (handles, schema, policy, conflict)
- M4 human/policy adjudication → verified label (becomes training/eval data)
- M5 pattern miner proposes a deterministic rule; tested against historical traces
- M6 rule runs in shadow mode (rule result vs LLM/human/reference)
- M7 rule promoted: deterministic first, LLM fallback only for uncertain cases
- M8 LLM retired for this slice: rule + proof + monitoring own the path

## What can become deterministic (with verified data)
Reconciliation (authority ranking — already deterministic; wrap as exemplar) · ingestion/source
classification · structured decomposition · many graph edges · optimization rejection · worker
routing. **Keep LLM + human-gate** for: new doc types, ambiguous legal interpretation, novel policy
conflicts, unclear authority, low-confidence entity resolution, semantic contradictions without a
clear numeric/date mismatch, compliance copy, human signoff.

## Promotion thresholds by rule risk
- Truth-serving rule: near-zero false positives; source handles required; human review for first promotion.
- Routing rule: lower risk; can promote earlier; fallback if misrouted.
- Optimization rule: promote if no safety regression + measurable lift.
- UI/projection rule: promote if schema-compatible + no truth mutation.
- Reconciliation rule: promote only with strong authority/scope/freshness proofs.

## Data rules
Mine ONLY from trusted outcomes (input artifacts, source handles, prompt/model/version, LLM output,
schema+grounding+deterministic validation, human/policy decision, final served outcome, later
corrections, customer impact). NEVER mine from: unverified LLM output, ungrounded summaries,
allegations-as-facts, reversed conflicts, tenant-private data used globally, stale facts, or outputs
without source handles. **Tenant-private traces cannot create global rules** unless anonymized + approved.

---

## Paste-ready workflow prompt

```
/workflows /baltor-determinism-factory
```

PART 1 — Contracts (schemas/determinism/*.v1.schema.json; register in architecture/contract_registry.json):
WorkflowTrace, LLMTrace, ConsensusRun, AdjudicationRecord, PatternCandidate, RuleCandidate,
RuleReplayReport, ShadowRunReport, DeterministicRule, RulePromotionReceipt, FallbackPolicy.
Every trace: tenant_id, source_scope, workflow_id, step_id, input_artifact_ids, output_artifact_ids,
model/provider ids (if LLM), prompt_hash, schema_validation, grounding_validation,
deterministic_validation, final_decision, source_handles, receipt_ids, created_at (injected, not wall-clock).

PART 2 — Trace store (src/baltor/determinism/trace_store.py): append-only; tenant_private cannot train
global rules unless anonymized+approved; private prompts/responses → object store / private tenant store;
no secrets.

PART 3 — Consensus recorder (src/baltor/determinism/consensus.py): record multi-model/multi-run outputs;
compute agreement score; record disagreement clusters; DOES NOT decide truth; emit ConsensusRun.v1;
low agreement → human/review or deterministic validator. Proof: scripts/check_consensus_recorder.py
(multiple outputs recorded; agreement computed; disagreement does not promote truth; consensus alone
cannot serve a fact).

PART 4 — Pattern miner (src/baltor/determinism/pattern_miner.py): find repeated non-deterministic
decisions (same conflict classification, reconciliation outcome, authority classification, routing,
held-out reason, optimization rejection reason, entity normalization, parser/source classification) →
PatternCandidate.v1. Proof: scripts/check_determinism_pattern_miner.py.

PART 5 — Rule candidate generator (src/baltor/determinism/rule_candidate_generator.py): rule types —
decision_table, regex_or_pattern, source_authority_rule, graph_rule, threshold_rule, schema_rule,
routing_rule, conflict_detector_rule, reconciliation_policy_rule, freshness_rule. LLMs may PROPOSE via
LLMGateway; proposed rules are NOT active; each candidate has input fields, output decision, scope,
examples, counterexamples, expected failure modes, fallback policy. Proof:
scripts/check_rule_candidate_generation.py.

PART 6 — Replay engine (src/baltor/determinism/replay_engine.py): run a RuleCandidate against historical
WorkflowTraces; compare to verified final decisions; compute precision, recall, FP, FN, abstention rate,
unsafe-promotion count, tenant-leakage risk → RuleReplayReport.v1. Proof: scripts/check_rule_replay_engine.py.

PART 7 — Shadow mode (src/baltor/determinism/shadow_runner.py): rule runs alongside current LLM/human path;
output recorded but NOT used; compare to final decision → ShadowRunReport.v1. Proof: scripts/check_rule_shadow_mode.py.

PART 8 — Promotion gate (src/baltor/determinism/rule_promotion_gate.py): schema valid; source handles
preserved; precision threshold met; unsafe FP = 0 for truth-serving rules; tenant isolation safe; no
unresolved conflict served; fallback policy exists; docs exist; proof exists; redteam passes. Promote only
after RulePromotionReceipt. Proof: scripts/check_rule_promotion_gate.py.

PART 9 — Fallback router (src/baltor/determinism/fallback_router.py): deterministic rule first if active;
low confidence / unknown / OOD → LLMGateway, human review, or hold-out; fallback recorded; fallback traces
feed future mining. Proof: scripts/check_deterministic_rule_fallback.py.

PART 10 — Apply to CFPB reconciliation (assert-equivalence to existing reference, NOT a new authority):
rule = if conflict_type=deadline_mismatch AND source_a.authority>source_b.authority AND same fact_key/scope
→ winner=higher_authority_source, loser=held_out. Proof: scripts/check_cfpb_reconciliation_rule_distillation.py
(historical LLM/consensus/explanation traces NOT required for truth; deterministic authority rule matches
reference; FAQ-30 stays held out; rule has replay report + promotion receipt; ContextResponse still serves
"10 business days" only).

PART 11 — Apply to source classification (deterministic rules): cfpb.gov/consumerfinance.gov official API
→ official_api/global_public; eCFR → source_of_law/global_public; customer upload → tenant_private; Markdown
vault default → tenant_private unless frontmatter says otherwise; narrative text → narrative_allegation, not
fact. Proof: scripts/check_source_classification_rule_distillation.py.

PART 12 — Apply to optimization rejection (deterministic rules): reject candidate if missing source_handle,
drops answer-critical fact, includes held-out conflict as served fact, promotes narrative allegation, crosses
tenant boundary, or lacks promotion receipt. Proof: scripts/check_optimization_rejection_rule_distillation.py.

PART 13 — API/UI (projection-safe; MAIN wires the monolith): GET /api/determinism/{traces,patterns,rules,
replay-reports,shadow-reports,promotions}; page /determinism with panels (LLM traces, consensus runs,
repeated patterns, rule candidates, replay reports, shadow mode, promoted rules, fallback rate, safety blocks,
tenant-scope warnings). Proofs: scripts/check_determinism_api.py, scripts/check_determinism_ui.py.

PART 14 — Redteam (scripts/check_determinism_redteam.py): all must FAIL SAFELY — promote rule from consensus
only; promote with unsafe FP; promote global rule from tenant_private traces; rule serves FAQ-30 as truth;
rule drops source handle; rule bypasses VerificationGate; rule has no fallback; rule has no replay report.

PART 15 — Docs: docs/determinism/{overview, llm-to-rules, consensus-is-not-truth, replay-engine, shadow-mode,
rule-promotion-gate, fallback-router, examples-cfpb-reconciliation, redteam}.md.

PART 16 — Proofs (all --self-test) + regression: the 13 PART proofs, then
check_reconciliation_cfpb_reference, check_optimization_suite, check_consumption_service,
check_no_consumption_bypass, check_no_direct_provider_bypass, check_section_maturity_matrix,
check_baltor_full_stack_perfect, baltor_flywheel --once.

Acceptance A–P: traces recorded; consensus stored as evidence-not-truth; patterns mined; candidates
generated; replay+shadow work; promotion gate blocks unsafe rules; active rules have fallback; CFPB +
source-classification + optimization-rejection rules deterministic & proven; tenant-private cannot create
global rules; UI/API show the ledger; reference CFPB answer stays "10 business days"; FAQ-30 held out;
flywheel green.

## Build discipline (same as Standards Factory)
Build agents create ONLY isolated new files + run ONLY their own proofs; MAIN integrates shared manifests
(PROOF_MODULES, section_maturity_matrix, contract_registry, opportunities, admin server) serially behind a
full-flywheel gate. Determinism in every proof (injected time, hashlib ids, no RNG, temp dirs, offline).
No commit/push/pip/containers/network/secrets. Run AFTER the Pattern & Standards Factory is integrated
(its repo-wide miner/linter scans would flake against half-written determinism files).
