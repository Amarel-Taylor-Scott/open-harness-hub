# Capability Rubric + Service Deep-Dive — 2026-06-11

Owner directive: for every surface, ask the ~30 capability questions (embeddings? LLMs?
best practices? multi-cloud? reinvented wheels? optimized paths? technical/user
requirements?), grade current state (demo → MVP → launch-ready → ideal), verify wiring,
and assess Teleon as the runtime backbone. Method: four adversarial code-verified deep-dive
agents (flows traced LIVE against the running plane) + the owner's rubric questions.

**Structured scores (33 questions × 12 surfaces): `architecture/capability_rubric_assessment.json`**
— single source; this doc is the readable verdict layer. Scale: 0 absent · 1 stub/demo ·
2 MVP · 3 launch-ready · 4 ideal.

## Maturity verdicts (one line each)

| Surface | Verdict | The one thing to know |
|---|---|---|
| deploy layer | **Launch-ready** | one topology → fly/k8s/compose, drift-gated; enforce single-machine for stateful apps |
| web tier (4 apps) | **Launch-ready (demo traffic)** | cold start rebuilds the vector index inside `serve()` — fix before auto-stop bites |
| worker fleet + controller | **Launch-ready / MVP** | controller solid (12/12); rows were ephemeral — DATABASE_URL now wired, needs postgres deployed |
| provisioning CLI | **Launch-ready (owner use)** | 8/8 + live-smoked |
| identity | **MVP** | no login rate-limit/lockout; email verification cosmetic; JSON state = single-machine |
| registry | **MVP** | catalog seed was broken on Fly (FIXED); O(n) JSONL re-parse per request; keyword-only search |
| events | **MVP** | unauth sink + hard 50k cap = fill-to-DoS then permanent 429; A/B path dead |
| baltor event bus | **Launch-ready behind a flag** | durability was opt-in — topology now pins BALTOR_DURABLE_DB into the volume |
| baltor context gateway | **MVP skeleton of THE product** | ctx:// handles die on restart; no tenancy/receipts on fetch; keyword scoring |
| baltor admin-demo | **Demo** | TWO run engines (showcase + monolith), double-processing bug, RUNS never pruned |
| model plane | **MVP, fragmented** | FOUR call planes, four receipt shapes; only OIPS mints receipts |
| teleon runtime | **Demo+** | the gate is GAMEABLE (refine prompt leaks expected outputs; no held-out examples) |
| foundry factory | **MVP machinery, demo throughput** | nothing schedules the queue feeder; volume factory and evidence factory are disconnected |

## What was FIXED during this review (committed today)

1. `.dockerignore` re-includes the design bundle — the registry's public catalog was silently
   EMPTY in any container image (worst wiring bug found).
2. Four missing seam prefixes (`/api/memory|pipeline|determinism|runtime/`) — four shipped
   Baltor page families 404'd through the public origin; now proxied.
3. Baltor persistence pinned into the Fly volume by topology env (`BALTOR_DURABLE_DB`,
   ledger, uploads, queue-health) — previously NOTHING survived a restart by default.
4. Worker `DATABASE_URL` added to the queue-stores secret group — staged rows stop dying
   with the machine once `aidr-postgres` is deployed.
5. Queue-key literal watch added to the generator `--check` (4 stray hand-typed copies found).

## The flagship answer: is Teleon the backbone yet?

Owner question: *"is this setup to take contracts/intents/capabilities and automatically
build out efficient more deterministic K8 runtimes or cloud functions using appropriate
standardization and logging tools?"*

**Answer as of 2026-06-11 (UPDATED — was "NO ~40%"): the compiler CORE now EXISTS; the
backbone is ~75–80% built, the remaining gaps are wiring, not a rebuild.** The four
prerequisites the original answer named as missing have all landed this session:
- **ungameable gate** — train/holdout split, answer-key-parrot regression-proof (`scripts/teleon_local_runtime.py`).
- **single receipted model plane** — ChatRoute is a shim over OIPS; every call mints+persists a `ModelInvocationReceipt` with `executed_base_host` (`scripts/model_routes.py` + `_repos/teleon/backend/src/teleon/inference/receipts.py`).
- **capability→runtime COMPILER** — `_repos/teleon/backend/src/teleon/compiler/` (`compile.py`/`emit.py`): a promoted capability + gate evidence + receipts compiles deterministically (byte-identical ×5) to a K8s Job / Fly Machine / local process, OTel logging attrs on every unit, **only-promoted-compiles enforced in code AND schema** (`schemas/runtime/CompiledRuntimeUnit.schema.json`). 40/40 self-test, drift-gated, dependency-law clean.
- **measured-lift promotion bridge** — `scripts/eval/promotion_bridge.py` gates on lift + durability (reason_codes single-source).

Still substrate-real from before: CapabilityTask/PurposeTask spec, FleetLedger + supervisor,
sandbox/template/inference ports, the deploy topology generator (the pattern the compiler
mirrors). What's left is WIRING (the honest gaps, per `teleon-self-improving-runtime-vision.md`):
a registry of compiled units, rollback CONSUMPTION (the field is carried, not consumed yet),
the **PurposeTask intent-intake queue** (auto-compile on promotion — the "just describe the
capability" front door), the **self-programming variant PROPOSER** (today `adapt()` selects
among pre-built; the open-ended exploration ladder `_repos/teleon/backend/src/teleon/exploration/` is the escalation
path to genuine synthesis), and a first credentialed cloud launch (runner is still the local
runtime; cloud backends are `@candidate` by design). The measured-lift bridge needs its
one-line wire-in into the runtime gate + registry decide.

The backbone program, sequenced (each step is prerequisite to the next):

1. **ONE model plane (M):** reimplement `model_routes.ChatRoute` as a shim over OIPS —
   every model call in the repo gets receipts/policy/fallback; kill the four-plane split.
   Bind `base_url` to provider-graph nodes (closes the receipt node≠endpoint hole); add
   LiteLLM as one more `openai_compatible` node (the standard wheel for fan-out — receipts
   stay ours).
2. **ONE receipt envelope (M):** `ModelInvocationReceipt` + a `suite` extension, carrying
   OTel-compatible `trace_id/span_id` attributes; persist behind the already-registered
   `:9426 local_receipt_service` as a thin projection. This is the "appropriate
   standardization and logging tools" answer: OTel for transport/correlation, the governed
   receipt as the artifact.
3. **UNGAMEABLE gates (S — do first, it's cheap):** hold out half of every suite from the
   refine prompt; never include expected outputs; record gate-vs-holdout split. Then tie
   `scripts/eval/measured_lift_headtohead.py` (already implements paired/held-out/
   separate-judge correctly) into promotion as the Stage-2 confirm.
4. **The capability→runtime COMPILER (L — the actual backbone):** extend the topology
   generator pattern: a PROMOTED capability (spec + gate evidence + receipts) compiles to a
   deployable unit — container command + Fly Machine config or K8s Job manifest — with
   budgets from OIPS policy, logging from step 2, and the FleetLedger recording the deployed
   runtime as a versioned, rollbackable entity. Intent intake = PurposeTask contracts queued
   → build attempts → gate → registry of promoted runtimes. Distillation lane (M0→M8) then
   converts stable LLM behavior into deterministic rules per the lossless law.

Steps 1–3 are days of work and de-risk everything; step 4 is the product and should start
only after 1–3 land (otherwise it compiles ungated, unreceipted capabilities).

## Engineering-quality verdicts (the owner's F-family questions)

- **Best practices:** strong on honesty discipline (degrade-and-record everywhere), security
  defaults (hash-only keys, raw-key-shown-once, fail-closed auth), and self-test culture
  (every new tool ships gated). Weak spots: unlocked concurrent state writes (teleon runtime,
  JSON stores), an unauthenticated events sink, missing rate limits.
- **Flexibility:** env/policy-driven throughout; ports come from registries; the seam-base
  pattern makes the same image run local/k8s/fly/compose unchanged.
- **Multi-cloud:** GOOD by construction — stdlib services + one topology emitting three
  provider targets; the only provider-specific code is the Fly controller, BY DESIGN, with
  KEDA as its portable twin encoding identical numbers. Object storage recommendation is
  S3-compatible (Tigris↔R2↔B2 swappable). The real lock-in risk is none of the clouds —
  it's JSON-file state, which is also the scale constraint; the SQLite→Postgres path fixes
  both.
- **Reinvented wheels:** justified customs all carry recorded rationale (queue adapter vs
  Celery; realms vs SSO — owner law; controller vs dormant fly-autoscaler; typed bus vs raw
  streams). Unjustified and queued for consolidation: 4 routing planes, 2 admin-demo run
  engines, 4 receipt schemas, JSON state engines. Full audit:
  `capability_rubric_assessment.json → wheel_reinvention_audit`.
- **Unoptimized hot paths:** registry O(n) JSONL re-parse per request (worst), web-tier
  index rebuild inside `serve()`, teleon synchronous 8×120s runs, receipts files re-read
  per request. All queued with owners in the priority program.
- **Requirements fit:** technical claims mostly honest (the repo's own captions admit
  demo-grade), with two exceptions called out: "model-BUILT capabilities" overstates (spec
  is hardcoded; refined instruction discarded), and the gate's promote claim is gameable.
  User journeys: 29 narrated videos pass 0-HTTP-error gates — the demo journey is real.

## Priority program (merged from all four reports)

**P0 — before/at first deploy (all S):** events ring-rotation + ingest cap; document+enforce
single-machine for stateful apps (`fly scale count 1`); snapshot-retention settings; teleon
held-out suites (gate de-contamination); schedule `seeds --enqueue` (Fly scheduled machine);
`OH_SHOWCASE_TOKEN` on in cloud; auth on gateway GETs.
**P1 — the consolidation wave (M):** ChatRoute→OIPS shim; one receipt envelope + :9426
projection; SQLite WAL for identity/registry/events; one admin-demo run engine (+ kill
double-processing, prune RUNS); persist ctx:// RUNS in DurableStore + receipts on fetch;
async teleon runs; bake embedding store into image; foundry→db-plans default path bridge;
fix reingest job dispatch; registry semantic search (A1); session cache for validators.
**P2 — the product builds (L):** capability→runtime compiler (backbone step 4); tenanted
customer-grade context gateway (ctxv:// fetch, per-tenant stores); measured-lift promotion
for registry components; Graphiti temporal-graph candidate behind `/api/graph/temporal/`;
monolith split (gateway → run engine → queue/fleet → renderers).

Related: `service-auth-and-consumption-model.md` (the orphaned `/service/*` handshake is its
Phase-1 — wire it instead of building :9422 from scratch), `fly-deploy-runbook.md`,
`hosting-decision-matrix.md`, `yc-context-landscape-2026-06.md`.
