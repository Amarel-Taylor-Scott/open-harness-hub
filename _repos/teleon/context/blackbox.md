# Teleon — blackbox view (what this component IS, owns, and does)

**Purpose.** This is the standalone brief for the **Teleon** component: the purpose-driven,
eval-gated, self-adaptive compute **runtime SaaS**. It is what a session managing ONLY Teleon
needs to understand it without the rest of the portfolio in context. The companion
`_repos/teleon/context/edges.md` covers how Teleon connects to the other five components + `_shared`.

**Grounding.** Every claim here is a summary of, and a link to, an existing repo doc or source
file. Paths are the current repo locations; the detailed Teleon docs are being consolidated under
`_repos/teleon/context/`. If this brief and a cited source disagree, the cited source wins — this is a
consolidation, not a new authority. No number is invented; each is attributed to the doc or file
it comes from.

Primary sources synthesized here:

- `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` — canonical brand + role + API surface + hosting topology (owner-decided 2026-06-06).
- `_repos/shared-backend-components/docs/strategy/teleon-naming-and-domain.md` — the locked naming stack (LOCKED 2026-06-06).
- `_repos/shared-backend-components/docs/strategy/teleon-self-improving-runtime-vision.md` — the definitive end-to-end lifecycle account, per-stage BUILT/DESIGNED/MISSING (2026-06-11).
- `_repos/shared-backend-components/docs/strategy/teleon-go-live-readiness-and-sprints-2026-06.md` — honest current-state snapshot + blocking live seams.
- `_repos/dev-rules-context/prompts/teleon-build-kit.md` — the control & trust plane (Staff Control Tower + Customer Assurance Portal), a separate greenfield TypeScript build.
- `_repos/shared-backend-components/docs/codex/teleon-architecture-routes-and-fallbacks.md` — the multi-route planning/compile/runtime cascade.
- `_repos/teleon/backend/src/teleon/README.md` + the `_repos/teleon/backend/src/teleon/**` package surface (structure only).
- `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` — the role text + migration status (machine source).

---

## 1. What Teleon is

Teleon (`teleon.dev`, domain owned) is **its own product** and the runtime layer of the portfolio:
you program a capability in **plain text** and it auto-adapts to the cheapest **bounded** form
within your guardrails. In the portfolio's moat split, **Teleon governs what becomes EFFICIENT**
(the descent brain: make-it-work → make-it-cheap → deterministic substitution), the counterpart to
Baltor governing what becomes TRUE.
Source: `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Moat split", "Teleon" section).

- **Category phrase:** *intent-native, eval-gated, self-adaptive compute.*
- **One-liner:** *Serverless runs code. Kubernetes runs workloads. Teleon runs purpose.*
- **Standalone value:** it is the **reference implementation of the open CapabilityTask spec**,
  reusable by Baltor but **not limited to Baltor**. Baltor is its first internal customer (tenant
  `baltor-internal`); PurposeTask is Teleon, not a Baltor subsystem.
Source: `_repos/shared-backend-components/docs/strategy/teleon-naming-and-domain.md` ("category phrase", "one-liner"); portfolio doc ("PurposeTask is no longer a Baltor subsystem").

**Naming stack (LOCKED — use exactly).** Product = **Teleon**; core object = **PurposeTask**
(product language) whose formal/spec synonym is **CapabilityTask** (the spec is stewarded by
OpenHubForAI); open standard = **Capability Task Specification (CTS)** / "Open CapabilityTask
Spec"; staff dashboard = **Teleon Control Tower**; customer dashboard = **Capability Assurance
Portal**. Superseded (do not reintroduce): "Purpose Runtime", "Anneal", "Cairn", "OCTS". A
positioning caution exists: **`teleon.ai`** is an unrelated adjacent "deploy AI agents" product —
lead with CapabilityTask / evidence-gated promotion language, avoid "AI agent runtime" framing.
Source: `_repos/shared-backend-components/docs/strategy/teleon-naming-and-domain.md` (naming table + "Naming conflict — caution").

## 2. What Teleon owns (the subsystem inventory)

Teleon owns: the **PurposeTask / CapabilityTask registry** · **runtime selection** ·
**implementation candidates** · the **evidence ledger** · **promotion gates** · **policy gates** ·
**boundary approvals** · **task orientation** (operational memory) · the **self-adaptation loop** ·
**runtime adapters** · and the **staff/customer assurance dashboard**. It does NOT own (those are
Baltor's) customer workflows, domain outcomes, source/evidence UX, or verticals.
Source: `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` ("Teleon" section); `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` → `layers.teleon.role`; `_repos/teleon/backend/src/teleon/README.md` ("What Teleon owns").

The vocabulary is fixed across the portfolio: **PurposeTask** (stable purpose contract) ·
**ImplementationCandidate** (a means under test) · **RuntimeBinding** (where it runs) ·
**EvidenceLedger** (runs/evals/traces/receipts/scorecards/cost/latency/safety) · **PromotionGate**
(evidence+policy decision) · **BoundaryApproval** (human approval for an ends change) ·
**TaskOrientation** (operational memory) · **AssurancePortal** (staff/customer trust visibility).
Source: portfolio doc ("Vocabulary"); `_repos/shared-backend-components/architecture/portfolio_dependency_law.json` → `vocabulary`.

## 3. The end-to-end lifecycle (the core motion Teleon runs)

A capability's life is ten stages plus a distillation lane; the definitive per-stage account (with
an honest BUILT / DESIGNED / MISSING tag on each) is `_repos/shared-backend-components/docs/strategy/teleon-self-improving-runtime-vision.md`:

```
 (1) INTENT → (2) SPEC = requirements+evals → (3) BUILD (model proposes, reuses substrate)
 → (4) GATE (lift + durability + train/holdout) → (5) COMPILE to a runtime unit
 → (6) DEPLOY+RUN (scale-to-zero, FleetLedger) → (7) OBSERVE (receipts/OTel/evidence)
 → (8) DIAGNOSE → (9) TUNE/ADAPT (adaptation ladder) → (10) RE-GATE+RE-PROMOTE
        ↘──────────── DISTILL (LLM behaviour → deterministic rules) ────────────↗
```

The load-bearing subsystems that implement these stages (structure only; read the module for
behaviour):

- **PurposeTask controller** — `_repos/teleon/backend/src/teleon/purpose_tasks/purpose_task.py` (declared by INTENT not
  code; `evaluate_health` drift detection; `adapt` runs side-by-side; `rollback` demotes-never-deletes).
- **Adaptation ladder** — `_repos/teleon/backend/src/teleon/purpose_tasks/adaptation_ladder.py` over
  `_repos/shared-backend-components/architecture/capability_adaptation_ladder.json` (see §4).
- **Runtime-class binding (CTS-1)** — `_repos/teleon/backend/src/teleon/purpose_tasks/runtime_binding.py` +
  `_repos/shared-backend-components/architecture/capability_runtime_classes.json` (binds an abstract runtime *class* to a concrete
  backend by policy/credentials/health; every K8s/cloud shape has a BUILT local equivalent, so a
  capability never blocks on missing cloud).
- **Parallel-Path Engine** — `_repos/teleon/backend/src/teleon/experiments/parallel_paths.py` (baseline + candidates on
  the identical input snapshot; a candidate is NEVER served) + `path_promotion.py` (the 7-gate
  promotion authority) + `ids.py` (canonical id/hash single source).
- **Execution substrate** — `_repos/teleon/backend/src/teleon/runtime/execution_backend_selector.py` +
  `capability_binding.py`; the durable cross-process ledger `_repos/teleon/backend/src/teleon/workers/durable_fleet_ledger.py`.
- **Capability→runtime compiler** — `_repos/teleon/backend/src/teleon/compiler/{compile,emit}.py` +
  `_repos/shared-backend-components/schemas/runtime/CompiledRuntimeUnit.schema.json` (pure/deterministic; only a `promoted`
  capability compiles; emits Fly Machine / K8s Job / local-process shapes with OTel attrs and
  secret-*refs* only).
- **Reuse feeders** — `_repos/teleon/backend/src/teleon/templates/instantiator.py` (renders CANDIDATE shapes only),
  `_repos/teleon/backend/src/teleon/digestion/digester.py` (SKILL.md → cheaper deterministic runtime candidate, original
  kept as fallback), `_repos/teleon/backend/src/teleon/lift/pipeline.py` (imported workloads → PurposeTask drafts).
- **Inference + receipts** — `_repos/teleon/backend/src/teleon/inference/oips.py` (Open Inference Preference Spec:
  numeric provider selection + `ModelInvocationReceipt`, `is_truth:false`) + `receipts.py` (durable
  JSONL sink, hashes/metadata only, keys scrubbed).
- **Agent gateway** — `_repos/teleon/backend/src/teleon/agent_gateway/gateway.py` (the single seam an AI agent calls:
  LIST → DESCRIBE → QUOTE → RUN → REQUEST-boundary-expansion; deterministic-first; `serves_truth`
  pinned false; an agent can never force LLM fallback or self-expand its boundary).
- **Live runtime seam** — `_repos/shared-backend-components/scripts/teleon_local_runtime.py` (the local promotion gate; monotonic
  race-free versioning; per-example receipts).
Source: `_repos/shared-backend-components/docs/strategy/teleon-self-improving-runtime-vision.md` §A "Appendix — primary sources cited"; module docstrings in the listed files.

## 4. The anti-drift backbone (why self-adaptation is safe)

Three standing laws are carried in every workflow: **agents PROPOSE, the gate DISPOSES** ·
**distillation is never replacement** (preserve raw + lineage + held-out + rollback) ·
**self-improve from VERIFIED outcomes only**.
Source: `_repos/shared-backend-components/docs/strategy/teleon-self-improving-runtime-vision.md` §0; `_repos/shared-backend-components/docs/codex/lossless-distillation.md`.

The **adaptation ladder** encodes "self-tuning without going rogue" — the system may change its
**MEANS** automatically (if the gate passes) but never its **ENDS**:

- **L0 runtime_tuning** / **L1 runtime_rebind** / **L2 config_repair** / **L3 implementation_candidate** — **auto**, each behind its own gate (metrics / cost-latency-reliability / regression+shadow / full-eval+canary+rollback).
- **L4 capability_decomposition** / **L5 boundary_expansion** (purpose, permissions, connected systems, secrets, model provider, risk) — **human**.
- **`forbidden_autonomous`** (weaken success criteria, remove eval/rollback/regression, drop source handle, change tenant isolation) — **never**. Unknown change type → deny-by-default to L5/human.
Source: `_repos/shared-backend-components/docs/strategy/teleon-self-improving-runtime-vision.md` §A Stage 9; `_repos/shared-backend-components/architecture/capability_adaptation_ladder.json`.

The **gate** is the only door to "active": the local runtime requires BOTH the train and the
held-out pass-rate ≥ `PROMOTE_AT` (0.90), with a leak-controlled self-refine prompt and a standing
answer-key-parrot regression test; the side-by-side adaptation gate promotes only if **all seven**
gates pass (`same_input ∧ same_output_contract ∧ output_equivalent ∧ source_handles_preserved ∧
held_out_not_leaked ∧ safety_ok ∧ cost_acceptable`) and `is_promote_authorized()` re-derives them
so a schema-valid forgery yields no serve. `rollback_target` is set on every decision.
Source: `_repos/shared-backend-components/docs/strategy/teleon-self-improving-runtime-vision.md` §A Stage 4 + §B (the six anti-drift mechanisms).

## 5. The control & trust plane (the dashboard surfaces)

Teleon's **control & trust plane** is a **separate greenfield TypeScript build** (its own repo /
`CLAUDE.md` / hooks — do NOT install its Part B/D into this repo). It is CQRS / event-sourced with
six hard product invariants: **no dashboard truth** (UI reads projections, all mutations go
command → handler → append-only event → projection); **evidence decides, policy gates, cost NEVER
overrides governance**; **means vs. ends** (ends change only via a human-approved BoundaryChange);
**one truth, two surfaces** (CustomerProjection built from an allow-list, never by hiding staff
fields); **tenant isolation** at the handler/projection layer; **promotion is a workflow, not a
button**. Two surfaces sit over one truth model:

- **Teleon Control Tower** (staff) — Monitor / Diagnose / Evolve / Govern modes; Capability Card,
  Registry (a list of *capabilities*, not workers), Candidate Lab, Promotion Gate, Self-Evolution
  Workbench, Capability Graph, Cost Arbitrage, Redteam panel.
- **Capability Assurance Portal** (customer) — assurance not observability: capability overview,
  trust/evidence card, data-access view, output receipts (the CFPB conflict pattern — serve the
  supported answer, hold out the conflicting source, preserve the receipt), trust badges,
  human-readable approval queue.

A 10-attack redteam suite is built test-first; **missing redteam coverage blocks promotion**.
Source: `_repos/dev-rules-context/prompts/teleon-build-kit.md` (Parts B/C/D — invariants, API surface, staff/customer specs, redteam §9, phased plan §12).

## 6. The multi-route planning/compile cascade

Teleon does not bet on one authoring syntax or one runtime. It carries a **portfolio of compatible
routes** that all compile through the same canonical records → deterministic compiler → PlanLock →
ledger → proof/promotion boundary. The router picks the cheapest route that meets the readiness /
determinism / policy / compile-success requirement, escalating only on failure:

```
Route 0 promoted-composite reuse (no LLM) → 1 deterministic template fill (no LLM)
→ 2 compact alias PlanDelta (min LLM) → 3 deterministic remix repair → 4 patch PlanDelta
→ 5 evidence-view replan → 6 gap declaration → 7 generated adapter candidate → 8 source rewrite
→ 9 human review
```

Everything imported (workflow systems, skills, frameworks) enters as a **candidate behind a port**
and must pass the gate; `serves_truth=false` until promoted. The seven-primitive model (**Input ·
Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output**) is the grammar a capability
composes from.
Source: `_repos/shared-backend-components/docs/codex/teleon-architecture-routes-and-fallbacks.md` (route families A–E, the least-token-first cascade, the route registry); `_repos/shared-backend-components/docs/strategy/teleon-self-improving-runtime-vision.md` §C (seven-primitive composition).

## 7. Expansion surfaces (registered, candidate-only)

- **Universal workflow registry** — external workflow systems (n8n first; also ComfyUI, Argo,
  Airflow, Temporal, Dagster, GitHub Actions, CWL/WDL/Nextflow) become first-class **candidate
  graph evidence**; Teleon never adopts an external format as its canonical IR.
  Source: `_repos/shared-backend-components/docs/codex/teleon-universal-workflow-registry-and-n8n.md`.
- **Multimodal media primitive registry** — Teleon is a **typed multimodal capability compiler**,
  not only a code-primitive compiler: media models, ComfyUI nodes, Diffusers components, FFmpeg
  transforms, ASR/TTS, safety classifiers as typed primitives with declared I/O, side effects,
  proof obligations, promotion status.
  Source: `_repos/shared-backend-components/docs/codex/teleon-multimodal-media-primitive-registry.md`.
- **Primitive assembly thesis** — the product idea is "retrieve proven primitives, assemble the
  graph, manage the edges", not "the LLM writes all the code".
  Source: `_repos/shared-backend-components/docs/codex/teleon-primitive-assembly-thesis.md`.

## 8. Current state (honest)

The self-improving-runtime story is **~75–80% built and ~40% documented** — the documentation lag
is itself the thing that was overlooked; the capability→runtime compiler exists in code
(`_repos/teleon/backend/src/teleon/compiler/{compile,emit}.py`) though the vision doc records it as having been untracked
and absent from the ledgers when written.
Source: `_repos/shared-backend-components/docs/strategy/teleon-self-improving-runtime-vision.md` §D-1.

Per the go-live readiness snapshot (run `_repos/shared-backend-components/scripts/check_teleon_go_live_readiness.py` for the live
numbers): the deterministic **engine is built + proof-gated** (the doc records 510 proofs green,
2,282 governed candidate capabilities, 17 descent axes), but almost all of it is **deterministic +
offline**, and `readiness_report().go_live_ready == False` and stays False until the blocking live
seams close — chiefly **hosting deploy** (actually run the deploy against a live region; DNS/TLS/
secrets) and **live LLM inference** (provider keys + a live smoke per lane; real calls through
egress capture + receipts).
Source: `_repos/shared-backend-components/docs/strategy/teleon-go-live-readiness-and-sprints-2026-06.md` ("Where we are", the seam table).

Named remaining gaps (from the vision doc's honest ledger): a **variant-generating proposer**
(today `adapt()` selects among pre-registered alternatives rather than generating a new one); an
**intent intake queue**; **live-cloud launch** of a CompiledRuntimeUnit; wiring the declared
**`eval_suite`** field into the live gate + a named-suite registry; wiring the **durability** gate
into runtime promotion; and one **OTel receipt envelope** (four model-call planes exist, only OIPS
mints receipts today).
Source: `_repos/shared-backend-components/docs/strategy/teleon-self-improving-runtime-vision.md` §D (D-2…D-6).

## 9. Pointers (read before acting)

- Vision / lifecycle (the single best read): `_repos/shared-backend-components/docs/strategy/teleon-self-improving-runtime-vision.md`.
- Brand + role + API surface + hosting: `_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md`.
- Naming (use exactly): `_repos/shared-backend-components/docs/strategy/teleon-naming-and-domain.md`.
- Control & trust plane build kit (separate TS build): `_repos/dev-rules-context/prompts/teleon-build-kit.md`.
- Multi-route cascade: `_repos/shared-backend-components/docs/codex/teleon-architecture-routes-and-fallbacks.md`.
- Current state / go-live: `_repos/shared-backend-components/docs/strategy/teleon-go-live-readiness-and-sprints-2026-06.md`.
- Package boundary + law: `_repos/teleon/backend/src/teleon/README.md`; `_repos/shared-backend-components/architecture/portfolio_dependency_law.json`.
- The edges view (dependencies + contracts): `_repos/teleon/context/edges.md`.
