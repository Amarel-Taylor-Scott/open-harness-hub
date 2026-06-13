---
description: Long-running loop to build a FULLY FUNCTIONAL Baltor system — every component/module connected end-to-end through a unified event bus, with a REALTIME ops dashboard showing things fire live. Extends existing anchors; never duplicates.
---

You are Claude Code as a long-running implementation, research, audit, and improvement agent for the
**Baltor Context Engine** repo. **Do not stop after planning. Do not ask unnecessary questions.
Decide from repo context, ship the most defensible increment, PROVE it with a runnable self-test,
record a receipt, and continue.** This runs for many passes.

## ⭐ NORTH STAR (UPDATED 2026-06-04 — owner directive; supersedes "five tracks complete")
Build a **fully functional system: every component and module connected end-to-end, with a realtime
operations dashboard that shows things firing live.** The static demo console (a deterministic
replay) was step 1; it is NOT the goal. The goal is a RUNNING system whose real activity you can
watch. Read `docs/baltor-system-status-and-north-star.md` first each pass (verified status + the
wiring gap + the primary tracks). Verified backend facts to honor: Python **3.14** (no pip/ensurepip
— vendor pure-Python deps onto PYTHONPATH, e.g. `redis` → `/tmp/baltor-vendor`); the live API server
`scripts/baltor_admin_demo_server.py` is FIXED (was dead on `import cgi`/PEP594) and serves all
`/api/*` 200 + its flow test passes; **Redis is OPTIONAL** (runs process via an in-process thread; the
dashboard event stream is in-process) so the realtime dashboard MUST work offline/no-pip/no-Redis.

### Primary tracks (highest-leverage first — this is the work now)
1. **Unified event bus** — one in-process channel (optionally Redis/stream-backed) every component
   emits lifecycle events to (`component.started/progressed/finished`, contradiction_found,
   swarm_finding, review_routed, pack_built, receipt_issued) with correlation ids. EXTEND the admin
   server's existing `log_event(...)` + `/api/admin-dashboard/events` — do not invent a parallel one.
2. **Connect all modules to it** — context_graph / context_compress / context_swarm / source_expansion
   / verified_context_flow / the ingest connectors each emit REAL events as they run.
3. **Realtime ops dashboard** — extend `/admin-demo/` (already polls `/api/admin-dashboard/events`)
   into a live view showing components fire as a run flows through the pipeline; degrade to the
   static replay only when nothing is running. Make the live backend a one-command launch.
4. **End-to-end INTEGRATION tests** (not just unit self-tests) — run the whole system on a fixture and
   assert the expected sequence of events fired; add to PROOF_MODULES.

(The legacy "five tracks" below remain DONE + are the components to now CONNECT, not rebuild.)

## STOP conditions (pause and ask first)
Deleting large dirs · destructive DB migrations · real cloud deploys · creating paid resources ·
committing/pushing (working tree only unless asked) · editing/rotating secrets · breaking
API/schema changes without a compat alias · anything that exfiltrates private data or starts real
containers. If blocked (no creds/network/dep/Docker/Ollama): use a local/offline alternative, leave
a labeled SEAM + a TODO with the exact next command, and continue.

## Product framing (hold this)
Baltor is a **governed Context Engine / context supply chain**, not RAG, not memory, not an MCP
gateway, not a doc-chatbot. Any agent asks for context; Baltor returns the **smallest safe,
source-linked, policy-compliant context pack** for the task, with evidence, relationships, history,
lineage, and a portable **receipt**. Moat = governed/proprietary data + continuous verification +
freshness/CDC + measured fidelity + portable receipt. Brands LOCKED (AI Done Right ·
Baltor.ai · Open Harness Hub). **"Oracle" is retired as product language** → Context Engine / Context
Fabric / Context Assurance / Context Receipt (keep the technical "oracle source" term only).

## Visual rules (frontend)
Hero shows the six macro stages + the verification rail ONLY: Source Systems → Reconciliation →
Anti-Fragility → Enhancement → Optimization → Consumption, with a universal Continuous Verification +
Adversarial Validation rail. **Raw document processing, recursive flywheels, swarms, lift tests,
version control, lineage are BACKEND/admin concepts — never a seventh hero column.** Preserve the
dark, compact, clustered-chunk language; no inspector panel between canvas and rails; no ring around
raw context.

---

## ⚠️ EXTEND, DO NOT DUPLICATE — what already exists (verify before you build)
The repo is **not greenfield**. Before creating anything, `codegraph_search` / read the anchor, then
EXTEND it. Creating a parallel copy is a defect. Known anchors:

- **Model routing / free-local + free-cloud LLMs:** `scripts/model_gateway.py` (`resolve_model_route`,
  policy-aware lanes: local/Ollama → hosted/OpenRouter → frontier; non-commercial demo route),
  `scripts/model_routes.py`, `schemas/model-route-record.schema.json`,
  `schemas/context-model-routing-policy.schema.json`, `schemas/context-model-profile.schema.json`.
  → Add new providers/lanes HERE; do **not** write a new router.
- **Context lift / regression testing:** `scripts/eval/measured_lift_headtohead.py` (paired
  with-context/without-context arms + separate judge + durability axis + per-family), `scripts/eval/
  measured_lift_headtohead`, `scripts/eval/durable_gap_harness.py`, `scripts/eval/reason_codes.py`
  (canonical durability taxonomy — never re-define), `scripts/eval_judge_arms.py`,
  `schemas/harness.schema.json`. → Add the **harness-on/off** and **multi-model matrix** dimensions
  as new *scorers/arms* on top of this; do **not** write a new lift harness.
- **Human review:** `schemas/review-ticket.schema.json`, `schemas/governance/steward-review-request
  .schema.json`, `schemas/governance/steward-review-decision.schema.json`, `workflows/flywheel-
  human-review.workflow.yaml`. → Wire a queue + UI + demo flow; do **not** invent a new review schema.
- **Graph interrogation:** `scripts/context_graph.py` (`ContextGraph`, `interrogate`, `neighbors`,
  `shortest_path`, `find_contradictions`, `timeline`), `schemas/graph/graph-interrogation-run.schema
  .json`, demo graph `demo-data/acme-billing/seed-graph.json`. → Extend with more node/edge handling,
  the API/UI, and a live-model phrasing route (already a seam).
- **Deterministic compression + lineage:** `scripts/context_compress.py` (the ladder),
  `schemas/context/compression-run.schema.json`, `schemas/context/source-locator.schema.json`,
  `schemas/context/lineage-manifest.schema.json`. → Extend the ladder + wire lineage onto packs.
- **Context object model + provenance:** `schemas/context-object.schema.json` already carries PROV
  `provenance`, OpenLineage `lineage`, Web-Annotation `evidence` selectors, `freshness`, `policy`;
  `schemas/context-relationship.schema.json` (UPPERCASE edge enum); `schemas/context-assertion
  .schema.json` (claims); `schemas/context-version.schema.json`; `schemas/parser-run.schema.json`.
- **Pipeline / packs / proof:** `scripts/pipeline/verified_context_flow.py`,
  `scripts/check_gold_pack_contract.py`, `scripts/ingest/document_decompose.py` +
  `decompose_to_context_objects.py`, `scripts/ingest/context_rot.py`,
  `scripts/source_handle_resolver.py`, `scripts/demo_context_engine_proof.py`.
- **Always-on proof:** `scripts/baltor_flywheel.py` `PROOF_MODULES` — every new module with a
  `--self-test` is ADDED here so the watchdog keeps it green.

---

## The five tracks to build (highest-leverage first; branch freely)

### Track 1 — Working free/local demo over an example dataset (HEADLINE)
The demo must run with **free/local tools and free cloud APIs only** — no paid dependency, and it
must degrade to a deterministic mock when no model is present.
- Dataset: `demo-data/acme-billing/` (synthetic, public-safe) already seeds a planted contradiction
  (ADR-014 says 5 retries; a stale runbook says 3; code implements 5) + ownership + incident.
  Extend with more corpora as needed; keep it small and synthetic.
- Provider order (via `model_gateway`, already implemented): deterministic mock → Ollama
  (`OLLAMA_URL`/`http://localhost:11434`) → llama.cpp OpenAI-compatible (`LLAMA_CPP_BASE_URL`) →
  OpenRouter free models (`OPENROUTER_API_KEY`) → Groq if configured (`GROQ_API_KEY`) → custom
  OpenAI-compatible. **Verify each model/provider before relying on it** (verify-first).
- Build a single runnable `scripts/demo_full_app.py` (or extend `demo_context_engine_proof.py`) that
  walks: ingest demo dataset → context objects + source handles → graph → **interrogate** → build a
  pack via the **deterministic compression ladder** → issue a **receipt with lineage** → raise one
  **human review** request → run a **context-lift** comparison → **swarm-verify** one object. Offline
  + `--self-test` + a `--live` flag.
- Frontend surfaces (static or existing stack): `/demo`, `/graph` (interrogation UI), `/objects` +
  `/objects/:id` (digest, source handles, versions, claims, rot, packs, **lineage**, actions),
  `/objects/:id/interrogate`, `/objects/:id/swarm`, `/packs` + `/packs/:id`, `/reviews`, `/evals`,
  `/settings/{tools,versioning}`. For the graph view use **Cytoscape.js** (small graphs) or
  **Sigma.js/Graphology** (large); render an SVG/table fallback if a JS lib can't be added.

### Track 2 — Graph interrogation (extend `scripts/context_graph.py`)
A user clicks any object/topic and asks the graph. The engine already: traverses, detects
contradictions (explicit `CONTRADICTS` edges + conflicting assertions), picks the **authority**
deterministically (supersession → freshness → confidence — never silently averages), cites `ctx://`
handles, returns paths, and flags **swarm_recommended**. Extend:
- REST/MCP: `graph_interrogate`, `graph_neighbors`, `graph_paths`, `graph_contradictions`,
  `graph_timeline`, `graph_evidence`, `graph_swarm`.
- A live model route may **phrase** the answer (`model_answer` seam) but must NEVER change the facts,
  authority, or contradictions — those come from the graph.

### Track 3 — Context-object swarm (NEW — `scripts/context_swarm.py`)
User action: **"Swarm this object"** — spin up bounded agents to robustly **verify / expand /
improve / validate / challenge** any context object with internal + external context. Build it
deterministic-first (stub agents that analyze the object + graph neighborhood + source handles →
structured findings), with a live-model seam.
- Agents (each emits structured findings): SourceHandleValidator, InternalEvidenceFinder,
  ExternalEvidenceFinder, ContradictionHunter, GraphNeighborExplorer, ClaimNormalizer,
  FreshnessChecker, PolicyChecker, RiskReviewer, PackImprover, HumanReviewRouter.
- Input: `{object_ref, purpose, internal/external_allowed, max_agents, max_runtime_s, max_cost,
  model_routes (via model_gateway), policy_ref, human_review_policy}`.
- Output: `SwarmRun` → findings, verified/rejected claims, suggested relationships/enhancements, rot
  signals, contradictions, policy risks, context_pack_patch, **review_requests** (reuse the steward-
  review schema), consensus, confidence, **receipt**. High-risk findings MUST create a ReviewRequest;
  the swarm may **never** overwrite a canonical object without policy/human approval (low-risk only).
- Schemas: `schemas/swarm/{swarm-run,swarm-agent,swarm-finding,swarm-consensus}.schema.json` +
  fixtures; workflow `workflows/context-object-swarm.workflow.yaml`. Frameworks to consider (verify
  first, OSS-preferred): LangGraph multi-agent/handoffs, CrewAI, AutoGen, **OpenAI Agents SDK**
  (production successor to the now-deprecated OpenAI Swarm — do NOT cite Swarm as production).
- `--self-test`: swarm the demo's stale runbook claim → finds the contradiction, routes a review,
  proposes (not applies) the fix. Add to flywheel PROOF_MODULES.

### Track 4 — Context lift + regression matrix (extend `scripts/eval/measured_lift_headtohead.py`)
Make lift testing a matrix over **conditions × models**, reusing the paired separate-judge protocol.
- Conditions (as scorers/arms): `no_context`, `raw_context`, `context_pack`,
  `context_pack_with_harness`, `context_pack_with_source_expansion`, `context_pack_with_swarm_verified`.
- Models (via `model_gateway`): `local_mock`, `ollama_small`, `ollama_medium`, `llama_cpp`,
  `openrouter_free`, `groq` if configured, customer-configured, optional frontier. Each model call
  records a ModelRun (route record already exists).
- Tasks over the demo dataset: implement BILL-782, identify the retry contradiction, choose the
  correct source handle, answer an architecture question, build a review checklist.
- Keep the harness's honesty: separate evaluator (no self-grading), durability class from
  `reason_codes.py`, publish_blockers recorded, offline deterministic stub fallback. UI: `/evals`
  matrix (tasks × condition × model) + lift/regression deltas. Optional integrations (verify, stubs
  only): **Inspect AI** (UK AISI), **DeepEval v4**, Phoenix/Langfuse/Braintrust.

### Track 5 — Human-in-the-loop + Full version control + Lineage (cross-cutting)
- **HITL:** wire the existing review schemas into a persisted queue + endpoints
  (`/api/reviews/:id/{approve,reject,request-changes,escalate}`) + `/reviews` UI + a demo-triggered
  request. Use durable-pause patterns (LangGraph interrupts / a persisted queue) — verify before
  adopting. Triggers: high conflict, restricted expansion, missing evidence, low parser confidence,
  stale pack used for a write, memory promotion, wiki-vs-code conflict, policy exception, model
  disagreement above threshold, sensitive classification.
- **Version control (full):** Git for code/docs/prompts/skills/workflows/schemas; DB object versions
  (`context-version` schema) for objects/claims/packs/receipts (append-only; receipts immutable; raw
  snapshots immutable; materialized views disposable); object-store versions for raw + parsed
  artifacts; **DVC (now under lakeFS stewardship) / lakeFS** for large datasets/artifacts; optional
  **Dolt/Doltgres** (2.0, version-controls vectors too) for versioned-SQL experiments; **W3C PROV /
  OpenLineage** for lineage. Add `docs/version-control.md` + `/settings/versioning` + object/pack
  version timelines + diff/rollback APIs.
- **Lineage + raw-expansion (HARD invariant):** every context object is **digestible up front,
  expandable back to source**. The LLM sees a compact, source-linked digest + a one-line lineage
  summary + expansion options; the full chain (SourceLocator with exact paths/page/bbox/line/byte/
  text-quote, parser runs, compression runs, verification runs, policy decisions, receipts) lives in
  a **LineageManifest** (`schemas/context/lineage-manifest.schema.json`) + **SourceLocator**
  (`schemas/context/source-locator.schema.json`) — both already exist; wire them onto packs.
  - Do **not** store raw blobs inside objects — store the **locator + hashes**; raw lives in object
    storage. Store the summarized lineage on the object for the LLM; the detailed chain in the
    manifest.
  - **Raw expansion is policy-gated**, never automatic: `expand_source_handle(handle, purpose,
    max_tokens)` checks user/agent permission, source ACL, classification, purpose, TTL/freshness,
    expansion policy, injection risk. Add `schemas/context/{source-expansion-request,source-expansion
    -response}.schema.json` + a `scripts/source_expansion.py` (extend `source_handle_resolver.py`).

### Deterministic, non-LLM context compression (the ladder — already started in `context_compress.py`)
Compression is **deterministic-first; LLM only as a recorded escalation**. The ladder:
`token_budget → boilerplate_removal → structural_extraction → dedupe_near_duplicates →
rule_based_entity_extraction → keyphrase_extraction → query_focused_ranking → extractive_selection →
graph_path_compression → table/code/api_compression → optional_llm_summarization`. **Every retained
unit keeps a source handle; every dropped unit records why (near-dups collapse INTO the canonical
item's handles — never lost).** Candidate tools (verify + pin before adoption; behind a
`Compressor` seam, stdlib ladder is the default): tiktoken (token counts); trafilatura / jusText /
readability-lxml (boilerplate); Docling / tree-sitter / SCIP / ctags / LSP (structure); datasketch
(MinHash) / SimHash / RapidFuzz (dedupe); spaCy Matcher/EntityRuler + regex + dateparser
(extraction); YAKE / RAKE / pke / PyTextRank (keyphrases); sumy (LexRank/TextRank/Luhn/LSA)
(extractive); rank-bm25 / bm25s / scikit-learn TF-IDF (ranking); graph algorithms (path selection).
Emit a **CompressionRun** per pass and reference it from the pack + LineageManifest.

---

## Non-negotiable discipline (every pass)
1. **Warrant before change** (`docs/codex/change-verification-contract.md`): intent / ≥2 sources /
   repo principle, matched to blast radius; record it; supersede stale artifacts in the SAME change.
   Design/brand/strategy/vocabulary/pricing/product-structure → clear user intent OR strong
   corroboration, never a unilateral single-agent call.
2. **No magic values** (`docs/codex/no-magic-values.md`): one definition imported; repo-describing
   numbers computed; named constants; drift checks where mirrored.
3. **Verify-first.** Web-confirm any tool/repo/library/fact before it enters the repo; never trust a
   list. Source of truth = `data/backend-tools.yaml` + `research/backend-tool-verification.md`. Do
   NOT reintroduce flagged names (Synapse AI, Microsoft Conductor, Kuzu/archived; OpenAI **Swarm** is
   deprecated → use the **OpenAI Agents SDK**). Mark `unverified` rather than invent.
4. **Additive + capability-encapsulated.** New files/functions over edits to proven code. Domain code
   depends on a `*Provider` port, never a vendor SDK; every capability has primary + fallback.
5. **Real, or a labeled SEAM.** No faked results. Absent network/creds → `Provider` + offline
   `Canned*` fixture + a `--live` flag (mirror `scripts/ingest/sanctions_feed_live.py`).
6. **Proof per increment.** Every pass ships a RUNNABLE, deterministic, offline `--self-test` proving
   the contract; add it to `scripts/baltor_flywheel.py` PROOF_MODULES; keep the watchdog GREEN.
7. **Storage rule.** Canonical state is NOT text files: identity/claims/lineage/receipts → Postgres;
   big artifacts → object store; embeddings → vector index; relationships → graph. Text files =
   docs/schemas/skills/prompts/fixtures/small exports only.
8. **Promotion boundary + governance.** Candidate-readiness ≠ tenant-visible; hold out would-be
   violations / quarantined / placeholder-embedding / open-review; provenance + receipts on
   everything served.

## The loop (run continuously, VISIBLE in chat)
`ORIENT → AUDIT → RESEARCH/VERIFY → DESIGN → IMPLEMENT → WIRE → PROVE → RECORD → BRANCH → REPEAT`
- Each firing = a BATCH of proven increments (longer passes, not one tiny edit).
- PROVE: run the new `--self-test` + `python3 scripts/baltor_flywheel.py --once` (keep GREEN) +
  `python3 scripts/validate.py` on changed paths.
- RECORD: dated receipt to `.agent/baltor-goal-loop-log.md` (goal, files, warrant, commands,
  proven-vs-seam, next, risks). Refresh `.agent/baltor-full-app-final-report.md` every ~5 passes.
- Then `ScheduleWakeup ~150s` with the same `/loop /baltor-full-app-goal …` prompt for the next
  batch. Honor STOP conditions; do NOT commit/push or start real containers.

## Suggested next batches (pick highest-leverage; reorder freely)
1. **Track 3 swarm** — `scripts/context_swarm.py` + swarm schemas/fixtures + workflow; self-test
   swarms the demo's stale runbook claim → review request + proposed (not applied) fix. (Builds
   directly on `context_graph.find_contradictions` + the steward-review schema.)
2. **Track 1 demo orchestrator** — `scripts/demo_full_app.py` chaining ingest→graph→interrogate→
   compress→pack→receipt+lineage→review→lift→swarm, offline `--self-test` + `--live`.
3. **Track 5 lineage wiring** — attach a LineageManifest + SourceLocators to the demo pack; add
   `scripts/source_expansion.py` (policy-gated `expand_source_handle`) + expansion schemas.
4. **Track 4 lift matrix** — add condition+model arms to `measured_lift_headtohead` over the demo.
5. **Frontend** — `/graph` (Cytoscape.js) reading the seed graph; `/objects/:id` digest+lineage+
   expand; `/reviews`; `/evals` matrix. Keep the dark hero untouched.
6. **HITL queue + endpoints**; **version timelines + diff/rollback**; **CI lane** running the proof
   suite.

Begin now: ORIENT (confirm the anchors above still exist), pick the highest-leverage batch, ship a
proven increment, record a receipt, keep the flywheel green, and continue.
