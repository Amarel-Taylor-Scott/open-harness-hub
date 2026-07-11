# /workflows /baltor-internal-skillgraph-rag  (C-SKILL-2 — CANONICAL skill-intelligence layer)

Build an internal **Skill Intelligence Layer** so Baltor can track available skills, search them (RAG), find
similar/duplicate skills, record **where each came from + why it was ingested**, evaluate/sandbox them, and
promote only through governed gates. **NOT** just a vector index, **NOT** a folder of skills, **NOT** a GitHub
watchlist, **NOT** docs.

```
Skill Registry + Skill RAG + Skill Graph + Skill Provenance Ledger + Similarity/Dedup Engine
+ Intake/Sandbox/Eval Pipeline + Promotion Gate + Skill Context Selector
```

> **Layering (no duplication):** this is the canonical SKILL subsystem — the **registry / RAG / graph /
> provenance / dedup** knowledge layer. `_repos/baltor/context/baltor-path-improvement-and-skill-intake-factory.md` keeps the
> PATH-improvement engine + the **skill-as-parallel-path** bridge and DELEGATES skill registry/intake/eval to
> this file. One skill registry, one skill graph — extend, never fork.
> **Sequencing:** focused increments; NEVER concurrent with another repo-mutating workflow. Reuse the
> sandboxed-execution port + the existing vector/hybrid-retrieval slot (local deterministic first); honors all
> locked principles (numeric-config + wrapped redundancy, measured-lift, no-truth-bypass, candidate-behind-port-
> never-runtime, cloud-defer-only-after-local-equivalent).

## SKILLGRAPH RAG CLAUSE (carry in the North Star loop)
Skills live in a Skill Intelligence Layer: registry + RAG + graph + provenance + similarity/dedup + sandbox/eval
+ promotion gates. Every skill records: where it came from (source + commit + content hash + license), **why it
was ingested**, which capability slots it supports, which contracts it implements, which deps/tools it needs,
which similar/duplicate/alternative skills exist, and whether it passed sandbox/eval/redteam. **RAG recall may
SUGGEST skills; it cannot ACTIVATE them.** Discovery is not trust · similarity is not equivalence · popularity
is not quality · skill output is not truth. A skill becomes active only after contract + sandbox + eval +
redteam + registry + promotion.

## Why RAG alone is not enough
RAG answers "what text looks relevant?"; Baltor must answer: what skills EXIST · where from · WHY ingested ·
which capability · which are duplicates/alternatives/supplements/fallbacks · which passed sandbox/eval/redteam ·
which is cheapest/safest/most-reliable/most-recent/preferred · which to show the agent NOW. → a **RAG-backed
GRAPH registry**, not a bag of documents. (Progressive disclosure like Codex/MCP: load compact metadata first,
full skill on demand.)

## 1. Contracts (`schemas/skills/*.v1`, register in contract_registry)
SkillSource · SkillArtifact · SkillManifest · SkillGraphNode · SkillGraphEdge · SkillRecallRequest ·
SkillRecallBundle · SkillDuplicateReport · SkillSimilarityScore · SkillIntakeDecision · SkillEvaluationReport ·
SkillPromotionDecision · SkillUsageTrace · SkillProvenanceRecord. `SkillArtifact`: skill_id · skill_version ·
display_name · source_type · source_url · source_commit · content_hash · manifest_hash · license · ingested_at ·
ingested_by · **why_ingested** · trigger_artifact_ids · capability_slots · input/output_contracts · dependencies
· required_tools · risk_score · status_code · status_label · sandbox_required · local_emulator_required ·
promotion_status · evaluation_reports · provenance_records. Proof `check_skillgraph_contracts`.

## 2. Numeric codes (`architecture/skill_{status,edge_type}_codes.json`)
**Status:** 100 disabled · 200 discovered · 300 intake_candidate · 400 sandboxed · 500 evaluated · 600
active_local · 700 active_external · 800 deprecated · 900 quarantined. **Edges:** 1000 SUPPORTS_CAPABILITY · 1100
DUPLICATE_OF · 1200 NEAR_DUPLICATE_OF · 1300 ALTERNATIVE_TO · 1400 SUPPLEMENTS · 1500 FALLBACK_FOR · 1600
SUPERSEDES · 1700 CAN_SHADOW · 1800 CAN_CANARY · 1900 REQUIRES_TOOL · 2000 REQUIRES_MODEL · 2100 REQUIRES_SANDBOX
· 2200 DERIVED_FROM_REPO · 2300 DERIVED_FROM_FAILURE · 2400 DERIVED_FROM_RESEARCH · 2500 BLOCKED_BY_POLICY · 2600
BLOCKED_BY_LICENSE · 2700 BLOCKED_BY_SECURITY · 2800 PASSED_EVAL · 2900 FAILED_EVAL. Runtime uses IDs + codes;
labels are UI metadata only; no hard-coded duplicate/fallback/candidate string logic. Proof `check_skillgraph_codes`.

## 3. Registry + graph + provenance
`architecture/{skill_registry,skill_capability_graph,skill_intake_policy,skill_promotion_policy,
skill_source_allowlist,skill_dependency_policy}.json` + `_repos/baltor/backend/src/baltor/skills/{skill_registry,skill_graph,
skill_provenance}.py`. Graph stores nodes: skills · sources · repos · capability-slots · dependencies ·
contracts · eval-reports · redteam-reports · provenance. Proof `check_skill_registry_graph` (registry+graph load;
every skill has source/provenance + why_ingested + ≥1 capability slot; every external skill sandbox_required;
every external candidate has a local emulator or ProviderUnavailableResult).

## 4. RAG index (local deterministic first — no external vector DB required)
`_repos/baltor/backend/src/baltor/skills/{skill_rag,skill_indexer,skill_recall}.py`. Index: manifest · SKILL.md · README · examples ·
scripts · templates · dependency files · eval/redteam reports · provenance + why-ingested notes · usage traces.
Use lexical token index + normalized metadata index + a hashed vector/fingerprint (reuse the hybrid_retrieval
slot if available). Output `SkillRecallBundle` = candidate skills + graph context (status/risk/eval score +
duplicates/alternatives/fallbacks + recommended_next_action). **Recall does NOT activate skills.** Proof
`check_skill_rag_index`.

## 5. Similarity + dedup (`_repos/baltor/backend/src/baltor/skills/{skill_similarity,skill_dedup}.py`)
Layers: (1) exact content hash · (2) manifest hash · (3) capability-slot overlap · (4) input/output contract
match · (5) dependency/tool overlap · (6) README/SKILL.md lexical similarity · (7) semantic fingerprint
(candidate) · (8) **behavioral equivalence via eval fixtures (strongest — same input snapshot → same output +
contract + safety)**. Outputs SkillDuplicateReport + SkillSimilarityScore + edges (DUPLICATE_OF/NEAR_DUPLICATE_OF/
ALTERNATIVE_TO/SUPPLEMENTS/FALLBACK_FOR). Rules: exact-dup deterministic; behavioral-equivalence requires same
snapshot + output contract; semantic = candidate only; near-duplicate ≠ automatic replacement; a duplicate can't
go active without an explicit promotion decision. Proof `check_skill_similarity_dedup`.

## 6. Intake pipeline (`_repos/baltor/backend/src/baltor/skills/{skill_intake,skill_manifest_parser,skill_sandbox,skill_evaluator,skill_promotion}.py`)
discover → SkillSource → content hash → parse/infer manifest → classify capability slots → inspect license/deps/
tools → provenance record → **record why_ingested** → similarity/dedup → sandbox → contract tests → evaluation →
redteam → SkillEvaluationReport → add candidate to graph → promote only by policy. Offline fixture
`fixtures/skills/sample_skill_repos.json`. Proof `check_skill_intake_pipeline`.

## 7. Evaluation dimensions (`architecture/skill_evaluation_dimensions.json`)
capability_fit · contract_validity · task_success_rate · output_fidelity · source_handle_preservation ·
tenant_safety · no_truth_bypass · dependency_safety · license_compatibility · maintainability · runtime_ms ·
estimated_cost · sandbox_safety · determinism · observability · redteam_pass_rate · docs_quality ·
local_emulator_quality. BLOCKERS (block active use): unsafe license · forbidden dependency · no sandbox · no
redteam · output-contract mismatch · source-handle loss (blocks truth use). Proof `check_skill_evaluation_dimensions`.

## 8. Why-ingested ledger (`_repos/baltor/backend/src/baltor/skills/skill_intake_reasons.py`)
Reason codes: owner_requested · failing_proof · repeated_failure_pattern · competitor_research ·
provider_watchlist · workflow_gap · cost_reduction_candidate · latency_reduction_candidate ·
replacement_for_unmaintained_tool · local_emulator_needed · customer_requested_capability · redteam_gap ·
documentation_gap · unknown_rejected. Every skill MUST have why_ingested + trigger_artifact_ids/text + expected
capability + expected evaluation policy + owner + review_deadline. Proof `check_skill_intake_reasons` (no skill
lacks why_ingested; reason validates; trigger captured; **unknown reason blocks promotion** — no junk drawer).

## 9. Skill-as-parallel-path (bridge to the path factory)
SkillArtifact → PathDefinition(candidate) → ParallelPathRun → PathComparisonReport → SkillEvaluationReport →
SkillPromotionDecision. Proof `check_skill_as_parallel_path` (skill maps to candidate path · baseline stays
active · runs shadow · contract validates · comparison written · unsafe rejected · safe-local can go active_local).

## 10. Example skills (offline)
`skill.utility.normalize_duration` ("ten business days"/"10 biz days" → normalized; PASS) ·
`skill.compare.runtime_config_diff` (compare worker policy/config leaves; PASS) · `skill.bad.truth_bypass`
(emits CanonicalFact directly; FAIL redteam) · `skill.duplicate.duration_normalizer_copy` (near/exact dup; MUST
be detected). Proof `check_skillgraph_examples`.

## 11. API/UI
GET `/api/skills[/search|/<id>|/duplicates|/graph|/provenance|/intake-reasons|/evaluations]` + POST intake-local/
recall/evaluate/run-shadow (local-only). UI `/skills`: registry · RAG search · graph · similar/duplicate ·
alternatives/supplements/fallbacks · source provenance · why-ingested · sandbox status · eval scorecard ·
promotion gate · blocked/risky · usage traces. Projection-only except explicit local test endpoints; no live
GitHub/secrets from UI; honest status labels. Proofs `check_skillgraph_api` · `check_skillgraph_ui`.

## 12. Redteam (`check_skillgraph_redteam`) — all FAIL safely
GitHub-discovered skill becomes active immediately · duplicate bypasses eval · near-duplicate marked replacement
without behavior proof · missing why_ingested · missing provenance · reads secrets · runs unsandboxed · writes
outside sandbox · emits CanonicalFact/ContextResponse · bypasses provider wrapper · unsafe dependency ·
incompatible license · semantic similarity promotes truth · external skill without local emulator/unavailable
result · display name controls runtime.

## 13–16. Docs · registries · proofs · acceptance
Docs `docs/skills/{internal-skillgraph-rag,skill-registry,skill-rag,skill-provenance,skill-deduplication,
why-ingested-ledger,skill-intake-pipeline,skill-evaluation,skill-as-parallel-path,skill-redteam}.md`. Update
registries (section_maturity, contract_registry, runtime_ownership, skill_registry/capability_graph,
tool_replacement_graph, provider_selection_graph, technical_debt, opportunities, risk_register). Create/run all
`check_*` + `check_skillgraph_full_stack`; REGRESS demo_offline_full_baltor · check_baltor_full_stack_perfect ·
check_no_direct_provider_bypass · `baltor_flywheel.py --once`. **M10** requires contracts + registry + graph +
RAG index + similarity/dedup + why-ingested ledger + intake pipeline + eval dimensions + skill-as-parallel-path
+ examples + API/UI + redteam + docs + regressions. **Acceptance:** recall returns graph context (not just
text) · similar/duplicate detection works (exact + near + alternative-vs-duplicate) · alternatives/supplements/
fallbacks are graph edges · every skill has provenance + why_ingested · intake pipeline works on offline
fixtures · skill-as-parallel-path works · good skills pass · bad skill fails safely · duplicate detected · API+UI
· redteam fails safely · offline demo + flywheel GREEN. No fake M10.

*Warrant: clear owner intent ("internal RAG/graph to track skills available, find similar/duplicate skills,
track where they came from + why"). Canonical skill-intelligence layer; the path+skill factory delegates the
skill registry/RAG/dedup/provenance here (one registry, one graph). RAG suggests, never activates; discovery ≠
trust; similarity ≠ equivalence; skill output ≠ truth. Build as focused increments; never concurrent with
another repo-mutating workflow.*
