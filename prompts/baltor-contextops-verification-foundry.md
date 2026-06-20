# Baltor ContextOps Verification Foundry — THE core differentiator

> Owner directive (2026-06-05). The single strongest product thesis: **other systems retrieve context;
> Baltor OPERATIONALIZES it.** Detect context that is fragile / conflicting / stale / unverifiable /
> under-supported / enhancement-worthy → use BOUNDED open-ended agents (Hermes / OpenClaw / Claude Code /
> OpenHands / Open SWE / local) to discover the right sources & methods → convert discoveries into
> DETERMINISTIC source recipes + verifier snippets + durable workers → run on-demand or scheduled →
> drive cost down from unbounded LLM tokens to mostly-deterministic verification. Ties together the
> Watchtower (what needs checking), ContextOps (how to check it), the Determinism Factory (distill
> repeats into rules), Reconciliation (what wins), Consumption (serve only governed context).
> See [[baltor-wedge-wraps-providers]], [[determinism-factory-distill-from-verified]],
> [[lossless-distillation-law]], [[governance-is-the-product]].

## CORE RULE (the invariant)
**Agents discover and propose. Baltor stores, verifies, reconciles, proves, schedules, and consumes.**
Bounded agents may: search sources, compare candidates, suggest selectors/extraction code, draft worker
code + tests, suggest a reliability rubric, explain authority. They may NOT: serve final facts, promote
canonical facts, override reconciliation policy, bypass SourceArtifact storage, write to production worker
queues, use tenant-private data globally, skip verification receipts.

## The cost-reduction ladder (the economic moat — make it visible on the dashboard)
- M0 ask LLM every time (highest cost) → M1 agent researches with tools (records traces+sources) →
  M2 agent creates a SourceRecipe (reusable discovery) → M3 deterministic fetch/extract script (cheap,
  testable) → M4 durable worker (scalable/retriable/schedulable) → M5 watch policy (TTL/source-change/
  on-demand) → M6 canonical fact cache (most queries hit verified fact + receipt) → M7 rule-distilled
  verifier (LLM only for novel/ambiguous). Result: unbounded LLM cost → bounded research ONCE →
  deterministic verification FOREVER.

## The product loop
detect context needing action → commission bounded research agent → discover sources → build SourceRecipe
→ generate VerificationRecipe + deterministic ExtractorSnippet → sandbox + proof gate → durable verifier
worker → WatchPolicy + scheduler → CanonicalFact + reconciliation + receipts → future calls use the
deterministic path first; LLM/agent is the long-tail fallback.

## Triage lanes (ContextTriageClassifier)
needs_reconciliation · needs_verification · needs_enrichment · is_fragile · is_stale · is_low_authority ·
is_under_supported · is_conflict_candidate · is_missing_source · is_customer_private_override ·
is_model_interpretation · is_high_value_reusable_fact. Rules: narrative_allegation can't become verified
fact without a stronger source; model_interpretation requires source support; current/rate/fee/deadline
claims are fragile; FAQ/guidance < source-of-law; tenant_private stays tenant-scoped.

## Contracts (schemas/contextops/*.v1; register in contract_registry)
ContextTriageResult · ResearchTask · ResearchPlan · SourceDiscoveryReport · SourceCandidate ·
SourceReliabilityScore · SourceRecipe · VerificationRecipe · ExtractorSnippet · GeneratedWorkerSpec ·
VerifierProofResult · FactRefreshPlan · FactVerificationRun · FactReliabilityScore.

## Provider ports (catalog candidates; output = candidate, never truth; never import as runtime)
research_agent_provider (research.local_stub@v1 [working], research.{hermes,openclaw,claude_code,openhands,
open_swe}@candidate) · source_discovery_provider · codegen_agent_provider. Research agents → SourceDiscoveryReport
(not facts); codegen agents → ExtractorSnippet/GeneratedWorkerSpec (not active production code); all traced.

## Source / verification recipes
SourceRecipe: authority, access method (http_get/api/file), auth, selectors/extraction hints, rate-limit +
retry policy, parser provider, expected output schema, watch triggers, reliability score. VerificationRecipe:
fact_key, input source recipes, extractor id, validators, success criteria, cross-source confirmation policy,
authority policy, freshness policy, tenant scope.

## Deterministic extractor snippets (sandboxed, tested, never write truth directly → produce FactAssertion candidates + source handles)
regex / json_path / html_selector / csv_field / markdown_heading / duration_parser / date_parser /
numeric_parser / source_hash_checker. Each has unit tests; runs in a sandbox (temp dir, no secrets, no
network unless the recipe allows it) behind a proof gate; no production registration until proof passes;
human-approval hook for high-risk generated code.

## Reliability scoring + cross-source confirmation
SourceReliabilityScore: authority_rank, officialness, freshness, stability, machine_readability,
contradiction_rate, availability, rate_limit_risk, parse_stability, tenant_scope, historical_accuracy.
Confirmation policies: single_official_source_ok · two_independent_sources_required ·
official_source_plus_secondary_confirmation · tenant_private_requires_human_signoff ·
llm_claim_requires_source_artifact · current_value_requires_fresh_source.

## Durable command types (CommandEnvelope, idempotent, retry/DLQ, lineage, no direct consumption)
contextops.{triage,research,discover_sources,build_source_recipe,build_verification_recipe,generate_extractor,
sandbox_extractor,generate_worker,run_verification,score_reliability,confirm_cross_source,publish_fact,schedule_watch}.

## Watch modes (integrate with Watchtower)
on_demand · scheduled · source_change · conflict_triggered · high_value_periodic · tenant_policy_change ·
provider_health.

## Cost tracking metrics (the moat, visible)
llm_calls_avoided, agent_research_runs, deterministic_verifications, cached_fact_hits, source_fetches,
watch_policy_runs, cost_per_verified_fact, cost_reduction_estimate, token_cost_before, token_cost_after.

## API/UI
GET /api/contextops/{triage,research-tasks,source-recipes,verification-recipes,generated-workers,reliability,costs}
+ POST /api/contextops/{research,run-verification}. Page /contextops (fragile/conflicting queue · research
tasks · source candidates · recipes · generated snippets/workers · reliability · cross-source · scheduled
checks · cost reduction · receipts). Projection-safe; MAIN wires the monolith.

## Reference CFPB scenario (end-to-end proof)
FAQ "30 days" vs Reg E "10 business days": triage marks FAQ-30 needs_reconciliation/lower_authority →
research finds an official-regulation source candidate (fixture/free endpoint) → SourceRecipe → VerificationRecipe
extracts "10 business days" → reliability ranks Reg E > FAQ → reconciliation holds out FAQ → a deterministic
worker can REVERIFY → future consumption uses the canonical fact, not open-ended LLM. LLM/agent fallback
stays for novel/ambiguous.

## Red-team (all must fail safely)
research agent publishes a fact directly · generated worker lacks proof · source candidate lacks source handle ·
FAQ outranks regulation · tenant_private source updates global_public fact · source recipe uses unapproved
network · extractor drops source handle · LLM output served as truth · unverified generated code registered
as an active worker.

## Build discipline + scope
No 2nd runtime / LLM gateway / worker framework. Generated workers ride the EXISTING durable worker framework.
Build agents create isolated files + own proofs; MAIN integrates shared manifests + red-teams. Determinism in
proofs (injected time, hashlib ids, temp dirs, offline). No commit/push/pip/containers/network/secrets; carry
the LOSSLESS DISTILLATION CLAUSE. **LEAN CORE first** (triage → research-stub → recipes → sandboxed extractor →
reliability → cross-source → cost ladder → CFPB reference → red-team); DEFER generated-worker EXECUTION + watch
scheduler + full API/UI to OPP-contextops-runtime. C-GRAPH-1 (temporal fact graph) folds UNDER this (feeds
is_fragile/is_stale triage).
