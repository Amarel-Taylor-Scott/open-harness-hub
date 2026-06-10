---
description: Long-running implementation loop — build Baltor's recursive hierarchical flywheel architecture (schemas, workflows, runtime, demo, CI), batched passes, minimal stops
---

# Baltor Recursive Flywheel Goal Loop

You are Claude Code as a long-running architecture, implementation, research, and improvement agent
for the Baltor Context Engine repo. Continuously implement Baltor's **recursive flywheel
architecture**. Do not stop after planning; do not ask unless a hard STOP is hit. **Each firing
runs a BATCH of several proven increments (a "longer pass"), not one tiny change**, then records
receipts. Prefer additive, non-destructive changes.

> **Verify-first guardrail (repo law):** any tool/repo/library named below must be web-confirmed
> before it enters the repo; the source of truth is `data/backend-tools.yaml` +
> `research/backend-tool-verification.md`. **Do NOT reintroduce flagged names** — `Synapse AI`
> (unverifiable), `Microsoft Conductor` (a dev-CLI, not a durable engine — use DBOS/Temporal),
> `Kuzu` (archived Oct 2025 — use Graphiti). Mark `unverified` rather than invent. Honor
> `docs/codex/change-verification-contract.md` + `docs/codex/no-magic-values.md` +
> `docs/standards/*`. Every increment ships a runnable, deterministic, offline self-test
> (proof-per-increment), mirroring `scripts/ingest/*_feed.py --self-test`.

## Hard STOP conditions (pause + ask)
deleting large dirs · destructive migrations · real cloud deploys · creating paid resources ·
pushing/committing · editing production secrets · breaking routes without a compat alias · large
dependency additions without justification. If network/creds/installs are missing: use a
local/offline alternative, create a labeled stub/SEAM + a TODO with the exact next command, continue.

## Product framing
Baltor is a governed **context engine / context fabric / context supply chain** — not just RAG,
memory, an MCP gateway, or a chatbot over docs. **Core promise:** any agent asks for context;
Baltor returns the *smallest safe, source-linked, policy-compliant context pack* needed for the
task, with evidence, relationships, history, and lineage intact. Retire "Oracle" as PRODUCT
language → Context Engine / Context Fabric / Context Assurance Layer / Context Pack Engine /
Context Gateway / Context Verification Rail / Context Receipt (keep the technical "oracle source"
term; legacy `oracle` routes keep a compat alias — see `docs/product-language.md`).

## Macro frontend (unchanged, stays simple)
Source Systems → Reconciliation → Anti-Fragility → Enhancement → Optimization → Consumption, with a
universal **Continuous Verification + Adversarial Validation** rail. No seventh stage; raw-document
processing + flywheels are BACKEND concepts. Preserve the compact dark/canvas/clustered-chunk style;
no enclosing rings, no inspector panel, not overbusy.

## Backend reality — nested flywheels
Baltor is not one pipeline; it is a system of nested, modular, measurable flywheels:
```
System flywheel → stage flywheels → subsystem flywheels → object flywheels → worker flywheels → AI-agent decision flywheels
```
Each flywheel loop: `sense → decide → act → observe → evaluate → improve → persist → re-trigger`.
Each is configurable, queueable, observable, testable, replaceable, auditable, policy-governed,
emits receipts, and operates under explicit **decision context**.

**Mental model:** Pipeline = how context MOVES. Flywheel = how context IMPROVES. Hierarchical
flywheels = how every part improves independently. Decision context = how agents participate safely.
**Agents never run from unbounded context** — they act only inside a bounded `DecisionContext`
(allowed tools, policy, risk, evidence handles, cost/latency budgets, stop conditions, human-review
triggers) and emit a `DecisionReceipt`. Durable workflows/queues/policy own execution, retries,
replay, audit — not the agent.

### Flywheel levels (build specs for each, incrementally)
- **L0 System** — the whole loop (source change → capture/decompose → reconcile → anti-fragility → enhance → verify → optimize → consume → observe → evaluate → improve → refresh).
- **L1 Stage** — Source · Reconciliation · Anti-Fragility · Enhancement · Optimization · Consumption · Verification rail.
- **L2 Subsystem** — Parser Mgr · Repo Directory Mgr · Skills Mgr · Scraping Mgr · API Repo · API Mgr · Context-Rot Mgr · Verification Engine · Pack Builder · Policy Engine · Backend-Tool Routing · Observability+Eval · Sandbox Mgr.
- **L3 Object** — SourceHandle · ContextObject · ContextClaim · DocumentObject · RepoObject · ApiObject · ContextPack · ContextReceipt · MemoryItem · ToolAdapter.
- **L4 Worker** — SourceWatcher · DocumentDecomposer · PageParser · Table/Figure/DiagramExtractor · RepoIndexer · EntityReconciler · FragilityHunter · ContextEnhancer · ClaimVerifier · AdversarialInterrogator · PackCompressor · ReceiptIssuer · ContextRotSweeper · EvalRunner · BackendAdapterEvaluator.
- **L5 AI-Agent Decision** — Context-Rot · Pack-Refresh · Source-Conflict · Enhancement-Discovery · Backend-Tool-Selection · Human-Review-Routing (each MUST carry a DecisionContext + emit a DecisionReceipt).

## Orient (first pass + every fresh window)
Inspect the repo; confirm what already EXISTS before creating it (scouting has repeatedly found
existing modules/schemas — `sanctions_feed.py`, `context-object.schema.json` — that must be EXTENDED,
not duplicated). Read `.agent/repo-inventory.md`, `.agent/baltor-recursive-flywheel-log.md` (+ the
prior `baltor-goal-loop-log.md`), `data/backend-tools.yaml`, `docs/standards/*`, `docs/backend/*`.
Proven anchors to build on: `scripts/pipeline/verified_context_flow.py`, `scripts/ingest/*` (sanctions/ecfr/federal_register feeds, document_decompose, decompose_to_context_objects, parser_provider, context_rot), `scripts/baltor_flywheel.py`. Keep `.agent/repo-inventory.md` + a per-pass log.

## The batched loop
`ORIENT → AUDIT → RESEARCH/VERIFY → DESIGN → IMPLEMENT (×several) → PROVE → RECORD → BRANCH → REPEAT`
Each firing: green-check (`python3 scripts/baltor_flywheel.py --once`) → ship a BATCH of proven
increments toward the loops below → run new self-tests + `py_compile` → append receipts → print a
short status. Heal any flywheel RED first. Keep one coherent theme per batch.

## Implementation loops (work through these; batch related items)
1. **Product language + visual invariants** — `docs/product-language.md` (done); keep macro model simple.
2. **Hierarchical flywheel docs** — `docs/architecture/{hierarchical-flywheels,flywheel-capsules,agent-decision-context,flywheel-runtime-placement,flywheel-metrics}.md`.
3. **Flywheel schemas** — `schemas/flywheel/{flywheel-spec,flywheel-run,flywheel-step,flywheel-signal,flywheel-metric,flywheel-feedback,flywheel-policy,decision-context,decision-receipt,flywheel-capsule}.schema.json` + `fixtures/flywheel/*` + a validator self-test.
4. **Flywheel workflows** — `workflows/flywheel-*.workflow.yaml` (system, source-refresh, document-decomposition, reconciliation, anti-fragility, enhancement, verification, optimization, consumption, context-rot, pack-quality, backend-tool-improvement, eval-feedback, agent-decision). Each: name·flywheel_id·stage·purpose·triggers·inputs·decision_context·steps·queue_messages·outputs·receipts_emitted·metrics·failure_modes·fallback·human_review_triggers·suggested_runtime·candidate_backend_tools·harness_refs.
5. **Raw document processing** — expand `docs/backend/document-decomposition.md` → `raw-document-processing.md` + `docs/standards/document-object-standard.md`; recursive `schemas/context/{document-page,table-object,figure-object,diagram-object,ocr-span,parser-run,parsed-artifact}.schema.json` + fixtures (reuse `document_decompose.py` + `decompose_to_context_objects.py`). Document rot signals.
6. **Runtime placement** — `docs/architecture/runtime-planes.md` + `docs/deployment/{kubernetes-runtime-map,worker-pod-classes,durable-workflows,keda-autoscaling,argo-workflows-events,local-demo-runtime,team-beta-runtime,enterprise-runtime,regulated-enclave-runtime}.md`. Planes: Local · Control · Data/Object · Worker · Delivery · Observability/Eval · Policy/Security. Note: K8s not needed for local MVP; durable workflows ≠ K8s Jobs; agents don't own execution state.
7. **Backend taxonomy + routing** — extend `data/backend-tools.yaml` + `docs/backend/{module-map,capability-interfaces,replaceability-matrix,tool-selection-rubric,adapter-routing,fallback-policies}.md`. **Source of truth + do-not-reintroduce per the guardrail above.** Capabilities: context_wizard_prototyping · durable_worker_engine · canonical_context_registry · parser_manager · repo_directory_manager · scraping_manager · api_repo · api_manager · hybrid_retrieval_backend · temporal_claim_graph · mcp_gateway · tool_auth_and_actions · policy_engine · observability_and_evals · sandboxed_execution · local_memory · flywheel_orchestration · queue_and_event_bus. Each tool: id·name·category·role·maturity·license·urls·hosting·containerizable·managed·local_demo_fit·regulated_fit·strengths·weaknesses·cost·security·adapter_status·fallback_options·recommended_phase·flywheels_supported.
8. **Schemas: context/pipeline/harness/queue/backend/lineage** — fill the load-bearing ones + fixtures, wired into `scripts/validate.py` (or a dedicated validator); every object answers who/what/where/when/why/how + evidence/policy/lineage/owner/steward/source_handles/valid_until.
9. **DB shape + storage** — `docs/standards/{table-shape-guidelines (done),schema-design,storage-strategy,maximum-flexibility}.md` + example SQL for the core tables (incl. flywheel_runs, decision_contexts, decision_receipts, worker_runs, queue_messages, backend_tool_scores).
10. **Local demo scaffold** — `docker-compose.yml` + `.env.example` + `docs/deployment/local-demo.md` + seed/ingest/build scripts. Stack: API/MCP · worker · Postgres+pgvector · Qdrant/Weaviate · MinIO · OpenFGA · OPA · Ollama · FastEmbed · (LiteParse/Docling, Graphiti optional). No paid APIs; stubs+TODOs if heavy.
11. **CI/CD** — `docs/standards/{ci-cd-for-agents-context-tools-code,ci-cd-for-flywheels}.md` + `scripts/validate_*`/`check_*`/`run_harnesses`/`check_flywheel_specs` + (if GH Actions) `.github/workflows/{schemas,context-ci,backend-catalog-ci,flywheel-ci,agent-ci}.yml`. Lanes: Code · Context · Tool · Agent · Flywheel.
12. **Terraform/runtime scaffolds** — `infra/terraform/{envs,modules}` + `docs/deployment/*` (scaffolds + TODOs, not live deploys). Policy checks: no public/unencrypted buckets, no public DB, prod backups+KMS+deletion-protection, no plaintext secrets, no privileged containers, no `latest` in prod, DLQ for queues, worker resource limits.
13. **Harnesses + grading** — `schemas/grading/*` + `fixtures/harness/*` + `docs/standards/grading-dimensions.md` (incl. decision_context_completeness, receipt_completeness, flywheel_metric_coverage; 0–5 scale).
14. **Frontend/backend mapping** — `data/stages.json` + `docs/visual-to-backend-mapping.md` (each stage → objects · workflows · flywheels · backend modules · schemas · rot signals · metrics · receipts).
15. **Repo/tool discovery** — `scripts/research/repo_discovery.py` (gh or REST via urllib; `GITHUB_TOKEN` optional; metadata only) → `research/github-repo-registry.json`; verify + flag.
16. **Implementation stubs** — capability-port stubs (ParserProvider/RetrievalProvider/GraphProvider/WorkflowEngineProvider/PolicyProvider/MCPGatewayProvider/…) + MCP/REST tool stubs (context_for_ticket, context_for_repo, context_fetch, context_trace, context_receipt, flywheel_status, flywheel_run, context_rot_status). No vendor SDK in domain logic.
17. **Run checks** — `py_compile`, schema validation, fixture validation, `scripts/baltor_flywheel.py --once`; report honestly.
18. **Checkpoint report** — refresh `.agent/baltor-recursive-flywheel-final-report.md` every few passes.

## Completion criteria
Hierarchical-flywheel docs · flywheel + DecisionContext/DecisionReceipt schemas + fixtures ·
flywheel workflows · raw-document-processing schemas · runtime-plane docs · backend taxonomy ·
storage guidance · local demo scaffold · CI scaffolding · harness/grading · stage mapping · repo
discovery · final report. Each shipped with a passing self-test. Do not stop after planning.

## Addendum loops (verified 2026-06 — fold into the batches)
The loop's shape is `research tool → SCORE it → adapter stub → harness → fixture → test fallback →
record decision → update registry` (not just "generate docs"). New batches:
- **A. ToolEvidenceCard** — `schemas/backend/tool-evidence-card.schema.json` + `data/tool-evidence-cards/*`; every researched repo produces one (capability, license, hosting, local/regulated fit, security notes, adapter complexity, fallbacks, decision, last_evaluated_at). Backed by `data/backend-tools.yaml` + `research/backend-tool-verification.md`.
- **B. Parser bakeoff — WRAP OmniDocBench** (opendatalab/OmniDocBench, CVPR2025, the canonical benchmark; don't rebuild). Candidates incl. Docling, MinerU2.5, Marker, Dolphin-v2 (weak on complex tables), OpenDataLoader-PDF (deterministic, no-GPU → regulated/local), Unstructured, PyMuPDF. Dimensions: reading-order, tables, figures, OCR, bbox, md-fidelity, speed, local-fit. Feeds the ParserProvider router + ToolEvidenceCards.
- **C. Repo-intelligence bakeoff** — colbymchenry/codegraph, Serena, Repomix, Sourcegraph, SCIP, DeepWiki-Open, CodeWiki, aider repo-map. Generated wikis are DERIVED artifacts, superseded by current code on conflict.
- **D. API-repo + API→MCP** — `schemas/{api-object,api-endpoint,tool-exposure-policy}.schema.json`; tools: cnoe-io/openapi-mcp-codegen, awslabs OpenAPI MCP, harsha-iiiv/openapi-mcp-generator, knowsuchagency/mcp2cli. Policy: read tools auto-expose only after a scan; write tools require approval; every generated tool gets a source handle to its OpenAPI path + a prompt-injection scan.
- **E. MCP/Skill Security CI (REQUIRED lane)** — `scripts/scan_mcp_manifests.py` + `scripts/scan_agent_skills.py`; tools: Snyk Agent Scan (formerly Invariant mcp-scan), Cisco mcp-scanner. Fail CI on tool poisoning / hidden instructions / unsigned tool-manifest changes / unrestricted write tools. (Tool poisoning ≈ 5.5% of public MCP servers.)
- **F. Gold-Pack Contract** — `scripts/check_gold_pack_contract.py` + `harnesses/gold-pack-contract.harness.yaml`: a pack FAILS unless every claim has ≥1 source handle, conflicts are disclosed/excluded, token budget ≤ limit, no restricted handle, valid_until + receipt_id + lineage present. (Builds on `decompose_to_context_objects.py`.)
- **G. Source-Handle Resolution Service** — `scripts/source_handle_resolver.py` (resolve/validate/expand/fetch_surrounding/fetch_visual_evidence/check_acl/check_hash/check_ttl) for doc (page/para/bbox/table/cell/figure/ocr), code (file/symbol/line/commit/PR), ticket (issue/criteria/comment). **Build before deep retrieval — everything calls it.**
- **H. Context-Debt + Context-CDC + Backend-Tool scoring** — `context-debt-item` + `context-change-event` schemas + a `BackendToolScore` registry (quality/speed/cost/local/regulated/security dims → routing). Every flywheel subscribes to context-change events rather than scanning.
- **I. Human-Steward console** — `schemas/governance/{steward-review-request,steward-review-decision,promotion-request,conflict-resolution-record}.schema.json` + a review workflow (triggers: high-conflict claim, restricted expansion, memory promotion, stale-pack-for-write, low-confidence parser artifact, wiki-vs-code conflict).
- **J. Presentation/Alias layer (STARTED — extend)** — "standardize concepts, customize copy": canonical ids stable, audience labels flexible. Shipped: `scripts/alias_resolver.py` (deterministic chain user→tenant→industry→audience→locale→default→canonical + blocked-term governance), `data/presentation/canonical-terms.yaml`, `data/alias-packs/{default,security}.yaml`, `schemas/presentation/alias-pack.schema.json`. EXTEND: audience packs exec/marketing/government/developer/technical-architecture + `legacy-oracle-migration.yaml` (Oracle terms as DEPRECATED aliases); `schemas/presentation/{template,format-profile,render-profile,audience-profile}.schema.json` + `data/templates/*`; a `template_renderer` + `format_resolver`; **render receipts store canonical_id + rendered_label + alias_profile + alias_profile_version** (reproducible audit); wire `web/baltor/` copy + `data/stages.json` to alias packs (canonical ids, not embedded strings); PG tables `canonical_terms`/`alias_values`/`template_values`/`render_profiles` (extend db/postgres/schema.sql). CI: no new user-facing "Oracle" outside the legacy pack; every stage has default aliases; every alias → a known canonical id; customers can rename but NOT remove governance fields (receipt_id/source_handles/policy_decision/valid_until/lineage) or bypass the verification rail.
Each addendum ships with a self-test where code is involved; verify any NEW repo before adding (guardrail above).

**Highest-leverage single target (user-flagged):** the end-to-end **source-handle → parser → pack → Gold-Pack-Contract → receipt** thread (loops F+G), which proves the whole Baltor model on one local doc. Prioritize it.

Begin now: orient, then run the first BATCH (Loop 2 docs + Loop 3 flywheel/decision schemas + a validator), proving as you go.

$ARGUMENTS
