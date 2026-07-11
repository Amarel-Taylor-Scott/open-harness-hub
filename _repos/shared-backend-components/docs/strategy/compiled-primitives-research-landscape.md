# Compiled-Primitives Research & Competitive Landscape

> **Status:** canonical reference (2026-07-08). Memorializes the external research that validates and
> pressure-tests the primitive-registry thesis, names the competitors, and lists the concrete practices we
> should adopt and the honest gaps we still carry. Ground truth for "who else is doing this, what do they
> prove, and where are we behind." Warrant: user-intent — *"we need to research, memorialize and include
> some of this research in my claude md files and memory system … understand gaps, competitors."*
> Single source; CLAUDE.md points here rather than restating.

## 0. TL;DR — one paragraph

The academic literature has converged on our exact thesis — **spend LLM tokens at build/compile time, run
deterministic artifacts at runtime, and reuse curated + evaluated skills instead of regenerating** — across
at least six independent 2026 works. **None of them ship what we ship** (a searchable, governed registry of
millions of pre-verified, typed, composable primitives with a retrieval graph). The closest commercial
effort, **XY.AI / "Compiled AI,"** open-sourced a *benchmark harness*, not a primitive library, and is
monetizing **vertically** (healthcare RCM), which is exactly the go-to-market the roadblock analysis says
wins. Our tech position is strong and largely ahead; our **honest gaps are a security gate on generated
code, a rigorous published benchmark taxonomy, formal provenance/supply-chain (SLSA-style) signing, standard
observability (OpenTelemetry), and a 5-stage promotion lifecycle** — all of which the papers/frameworks below
hand us as ready blueprints.

## 1. The reference set (what each proves, our state, the action)

| Work (arXiv/site) | Core claim | What it teaches us | Our current state | Gap → action |
|---|---|---|---|---|
| **Compiled AI** — XY.AI, 2604.05150 | LLM generates bounded code once from a YAML spec → 4-stage validation → deterministic zero-runtime-token exec. 96% completion, **break-even N≈17**, 57× tokens at 1K. | Compile-time > runtime; every generated artifact needs a validation gate before promotion; **break-even is the honest unit economic**. | We have the orchestrated/planned lanes (LLM plans A→B→C, deterministic builders compose) + `real_buildout_ab_harness.py`. We do NOT compute break-even N* or semantic entropy. | Add **break-even N\*** + the 7-metric taxonomy (§3.1) to our harness. Their repo is a benchmark, not a library — **we are the layer they don't ship**. |
| **SkillsBench** — 2602.12670 | Curated skills lifted pass-rate 33.9% → 50.5%; **self-generated skills are not automatically valuable**. | Curation + evaluation + negative tests + regression tracking is the moat, not raw generation. Smaller focused modules beat huge doc bundles. | We generate at scale but gate with per-pack oracles + `flywheel_proof_modules.py`. Candidate/truth boundary already enforces "generation ≠ promotion." | Strengthen **negative tests + regression floors** on every primitive (VERIFY-THE-VERIFIER already mandates mutation/determinism/ratchet — extend to a *benchmark-lift* floor). |
| **SkVM** — 2604.03088 | Analyzed 118K skills; decomposed skills into primitive capabilities; treated skills as **compilable artifacts across model/harness pairs**. Up to 40% token cut. | **Separate abstract primitive definition from concrete runtime binding**; track portability across model/harness/runtime/API/permissions/env. | Our cards are one body; portability (which model/harness/runtime a primitive is valid on) is **not** a first-class field. | Add **`compatible_models` / `compatible_harnesses` / `compatible_runtimes` / `capability_requirements`** to the card schema; this is the 50M-variant axis (§4). |
| **Agent Primitives** — 2602.03695 | Reusable latent building blocks (review/vote/plan/execute) give 12–16.5% accuracy + **3–4× token/latency** vs text multi-agent. | The reusable set is a *verb library*: review, critique, validate, vote, rank, select, plan, execute, route, decompose, synthesize, extract, transform, reconcile, repair, escalate. Prefer typed I/O over NL. | Our packs cover extract/transform/validate/reconcile/route well; **review/critique/vote/rank/select/plan/escalate as first-class agentic primitives are thin.** | Mint an **agentic-computation-pattern pack** (the 16 verbs) with typed I/O — directly composes with the retrieval graph. |
| **SkillMigrator / transferable web skills** — 2606.17645 | Web/UI skills transfer by **structure + grounding**, not semantic similarity. −8–10% actions at matched success. | For browser/UI/API/CLI/workflow primitives, separate **intent · preconditions · structural pattern · grounding · runtime bindings · success verifier · failure recovery**. | `ui_design_primitives.py` exists; the 7-part interaction contract is not modeled. | When we add action/browser primitives, use the **7-part contract** as the schema (not one blob). |
| **Harbor** — harborframework.com | Framework for **specifying sandboxed agent tasks** for eval + optimization. | Sandboxed deterministic verifiers are the production benchmark substrate. | We sandbox exec in `real_buildout_ab_harness.execute_lane` (py_compile + pytest). | Adopt Harbor-style **task specs** (task.yaml + fixtures + verifier + resource limits) for the published benchmark (§3.2). |
| **OWASP LLM Top-10 · SLSA · OpenTelemetry** | Prod baselines: injection/insecure-output/supply-chain/excessive-agency; artifact integrity + tamper-resistance; standard traces/metrics/logs. | Security + provenance + observability are **day-one**, not later. | We have candidate/truth boundary + lossless ledgers + run_proofs. We have **no security scan on generated code, no artifact signing/SBOM, no OTel**. | Three named gaps below (§3.3, §3.4, §3.5). |

## 2. Competitor verdict — XY.AI / CompiledAI (github.com/XY-Corp/CompiledAI, MIT, ~3★)

- **Published:** yes — arXiv 2604.05150, authors from XY.AI Labs + Stanford (Thickstun) + Harvard Medical
  (Alterovitz) + Walter A. De Brouwer. A real, credentialed paper.
- **What the repo actually is:** a **benchmark suite + eval framework** — a code factory (Templates:
  Simple/Streaming/Validator/Batch; Modules: Database/HTTP/Notif; Prompt Blocks: HIPAA/PCI/SOC2), a 4-stage
  validation pipeline (Security→Syntax→Execution→Accuracy), baselines (Direct LLM/LangChain/Multi-Agent/Human),
  7 metric categories, datasets BFCL v3 (400) + DocILE (5,680 invoices). **It regenerates code per spec; it
  does NOT ship a searchable registry of reusable primitives.** That registry is our layer.
- **Deterministic primitives vs LLMs:** their "primitives" are per-spec *templates/modules/prompt-blocks*
  the LLM assembles once — not thousands of pre-verified reusable functions. Their DocILE result shows pure
  deterministic extraction is weak (20.3% KILE) and the strong variant still uses bounded LLM calls → **hybrid
  is unavoidable for messy inputs** (we agree: micro-repair + LLM fallback on tiny error radius).
- **Commercialization:** vertical **healthcare RCM** (xy.ai "Code Factory Manifesto"), no public revenue.
- **Takeaway:** they validate the *paradigm* and the *vertical GTM*; they are not a substrate competitor.
  We should **adopt their benchmark rigor** and stay the registry/retrieval layer.

## 3. Practices to ADOPT (mapped to our files)

### 3.1 The 7-metric benchmark taxonomy → `real_buildout_ab_harness.py` + `run_realistic_session_benchmarks.py`
We currently measure tokens avoided + runtime pass + cross-test agreement. Add: **compression ratio &
break-even N\*** (gen_cost / per-exec savings — our reuse=0-token is the extreme case, amortized across ALL
consumers not one workflow), **semantic entropy / exact-match rate** (consistency; deterministic lanes should
be entropy 0), **TTFT/TPOT/P50/P99/jitter** (latency), **Determinism Advantage DA>1** (cost), **first-pass
validation rate + regen attempts**. This makes our receipts publishable and directly comparable to their paper.

### 3.2 The 4-stage validation pipeline → extend `execute_lane`
Their order is **Security → Syntax → Execution → Accuracy**. We do syntax (py_compile) + execution (pytest);
we should add a **Security stage** (§3.3) *before* execution and a formal **Accuracy-vs-golden stage** (we
have per-pack golden oracles — wire a generic accuracy gate that scores a candidate primitive against its
golden set, not just "tests pass").

### 3.3 A SECURITY GATE on generated code (real gap; roadblock #5) → new `scripts/primitive_security_gate.py`
Generated/minted primitive bodies are executable code = a new attack surface, and we have **no scan today**.
Adopt their 3-gate shape: **INPUT** (prompt-injection + PII on the spec), **CODE** (Bandit/Semgrep/banned-
imports/secrets on the generated body), **OUTPUT** (canary / leakage). Gate promotion on it. This closes the
single most concrete production gap the roadblock analysis names.

### 3.4 Provenance / supply-chain (SLSA-style) → extend the card + `canonical_id`
We content-address by `canonical_id` already. Add **artifact hash + generated_by + reviewed_by + immutable
version + supersession edges** to every card, and an SBOM-style dependency record for packs that import
libraries. This is the "artifact integrity" the papers assume and our LOSSLESS-DISTILLATION law already leans
toward.

### 3.5 OpenTelemetry-compatible observability → serving path
When primitives serve, emit standard traces/metrics/logs keyed by `primitive_id · version · run_id ·
input/output schema hash · token/runtime/compile cost · cache hit/miss · fallback reason · verifier result`.
Not built; recommended for the serving layer.

### 3.6 A 5-stage promotion LIFECYCLE (we have 2)
Today: `candidate → promoted`. Adopt **candidate → validated → certified → production** (+ `deprecated /
superseded`), matching SkillsBench's "evaluated before valuable." Each transition has a named gate (schema
valid · tests · deterministic verifier · security scan · sandbox · benchmark lift · no leakage · provenance).

## 4. What "50 million primitives" must mean (not a pile of prompts)

A validated primitive **graph** with typed variants + deltas, hierarchically:
- **L0 atomic capabilities** (~5K): parse date, normalize currency, match invoice line, redact secret… (our
  scalar/string/quantity packs live here).
- **L1 typed primitives** (~100K): `extract_invoice_header`, `reconcile_stripe_payout`, `validate_edi_835`,
  `route_denial_by_carc_rarc`… (our verified-factory + edge cards trend here).
- **L2 composite primitives** (~1M): `auto_post_remittance`, `assemble_prior_auth_packet`… (our
  primitives-of-primitives / recipes).
- **L3 vertical workflows** (~5M): `specialty_clinic_denial_workqueue`, `stripe_to_erp_month_end_close`…
- **L4 generated variants** (~50M): tenant/schema/jurisdiction/vendor/payer/**model·harness·runtime·API-
  version** specific — **inherit from a canonical L0–L3 primitive and store only the DELTA** (this is the SkVM
  portability axis made concrete). 50M is L4 variants, not 50M hand-written bodies.

Scaling substrate we already have or stubbed: multi-column index (semantic + LSH + exact + per-term),
`object_embedding` pgvector (HNSW stubbed), JSONL→Postgres staging, dedupe (MinHash-LSH), candidate/truth
boundary. Missing for L4: the **delta-inheritance** record + the **compatibility index** (model/harness/runtime).

## 5. Roadblocks scorecard — "have we solved these?" (honest)

**Tech roadblocks — substantially addressed:** workflow-spec (plan dialect + infer-first intake),
golden datasets (per-pack oracles), input variability (deterministic + micro-repair + LLM fallback), drift
(temporal_cdc + stale-context roadmap), weak horizontal moat (governance + registry + reuse economics),
ops burden (candidate/truth boundary + lossless ledgers + run_proofs).

**Partially addressed (named gaps above):** security gate (§3.3 — NOT built), formal verification (oracles,
not proofs), provenance/SLSA (§3.4), observability/OTel (§3.5), 5-stage lifecycle (§3.6), maintenance/staleness
(roadmap only).

**NOT "solved" by code — because they are BUSINESS, and the analysis is right that they are the real work:**
vertical customer discovery, integration cost (EHR/ERP/payer connectors), compliance evidence + liability,
incumbent distribution, buyer perception, sales. **Our strategy already commits to the recommended shape** —
depth-before-breadth on one revenue vertical (**OFAC/sanctions first `serves_truth=true`, then
healthcare-provider-directory ADMIN**; insurance is explicitly OFF the table per repo law), with AIDevObserver
as the GTM wedge. So: **the tech is mostly solved or blueprinted; the business roadblocks are the roadmap, not
a contradiction.**

## 6. Methodology this landscape endorses

**Audit first → schema second → generate third → benchmark fourth.** Never generate large primitive volumes
before the schema, verifier, and benchmark exist to gate them (SkillsBench's core lesson). The full 11-phase
production plan (repo audit → primitive architecture → machine-readable schemas → candidate mining →
safe factory → productionized benchmark → 50M roadmap → security/provenance → observability → safe scaffolding)
is the sequenced backlog; execute it additively, one gated phase at a time.

## 7. The richer 2026 "skills-as-an-OS" cluster (added 2026-07-08)

A second, deeper wave of papers converges on the same architecture — **package → lint → index → retrieve →
compile → execute → verify → revise → govern** — and hands us specific mechanisms + warnings:

- **Mixed signal / marginal-utility LAW (the most important correction).** SkillsBench (2602.12670): curated
  skills 33.9%→50.5%, but **focused ≤3-module skills beat exhaustive bundles**. SWE-Skills-Bench (2603.15401):
  **39 of 49 real skills gave ZERO lift, avg +1.2%, some +451% tokens, some *degraded* performance.** →
  **Every primitive must A/B prove marginal lift (pass-rate / cost / latency / safety) or be DEPRECATED, not
  accumulated.** This is the counterweight to "generate millions." (Reinforces our usefulness-gate-as-router.)
- **Quality/bloat is measurable.** SkillReducer (2603.29919, 55,315 skills): 26.4% missing routing, >60% body
  non-actionable; two-stage debloat −48% description / −39% body while +2.8% quality. SKILL.md-smells study
  (2607.01456): **>99% of real skills carry ≥1 smell.** → a smell **linter** + a **debloater** are mandatory
  (linter shipped: `scripts/lint_primitives.py`).
- **Retrieval-at-scale is the real problem, not generation.** SkillRet (2605.05726, 17,810 skills): off-the-
  shelf retrievers fail; fine-tuning +13–17 NDCG@10. SkillRouter (2603.22455, ~80K skills): **hiding the body
  drops routing 31–44pts**; a 1.2B retrieve-and-rerank hits 74% Hit@1, 5.8× faster. Graph-of-Skills
  (2604.05333) + SkillDAG (2606.03056): **typed skill graph** (depends_on / specializes / conflicts_with /
  duplicates / composes_with / supersedes) → dependency-aware bounded bundles, −37.8% tokens, +43.6% reward.
  SkillRAE (2605.10114): **compile retrieved evidence into minimal grounded context**, not raw dumps (+11.7%).
  → need **four indexes (full-text · embedding · schema/IO · typed-graph) + a context compiler**, not top-k.
- **Compilation cousins validate the deterministic thesis.** PlanCompiler (2604.13092): typed node registry +
  static validation → 278/300 vs 202/187 for free-form codegen. FlowCompile (2605.13647): compile-time config
  search, up to 6.4×. Agentic Compilation (2604.09718): O(M×N)→amortized O(1). **Formal Skill (2605.19604):
  plain Markdown is too informal — use JSON metadata + action schemas + deterministic Python executors +
  lifecycle hooks + local state + routing metadata + policy gates + observability; its runtime used ~48%
  fewer tokens.** → move from card→**formal primitive PACKAGE**.
- **Verifier-driven evolution, not one-shot.** SkillRevise (2606.01139): 36%→61.6% over 3 trace-conditioned
  revision rounds. MIND-Skill (2605.08670): induction+deduction closed loop beats one-shot. SkillClaw
  (2604.08377) / SkillSmith (2606.01314): co-evolve skills **and tools** from cross-user traces. → our
  micro-repair + save-as-primitive is the seed; formalize **generate→execute→verify→revise→promote**.
- **Security: skill marketplaces are already dangerous.** Skill-Inject (2602.20156): up to **80% attack
  success**; SkillProbe (2603.21019): **>90% of popular skills fail audit** (popularity ≠ safety); Snyk on
  3,984 ClawHub skills: **1,467 with issues, 534 critical, 76 confirmed malicious payloads.** → community/
  generated primitives start **quarantined**, never auto-promoted; the security gate (task #13) is now a
  hard requirement, not a nicety.
- **Benchmark suites to plug into (wrap, don't rebuild):** Harbor (sandboxed task specs; Terminal-Bench 2.0
  ships in Harbor format), AppWorld (9 apps / 457 APIs / 750 tasks), BFCL V4 (function calling), TUA-Bench
  (120 terminal tasks, execution-scored). → the published benchmark is a **primitive promotion gate**, not a
  leaderboard.

## 8. Primitive-OS pipeline — node-by-node status (have / partial / gap)

| Node | Our asset | Status |
|---|---|---|
| Package | executable-pack cards (routing+IO+body+boundary) | **partial** — need the formal-package fields (§9) |
| **Lint** | `scripts/lint_primitives.py` (8 smells + bloat + schema-gap audit) | **have (new)** |
| Index | multi-index (semantic + small/large LSH + exact + per-term, 61 cols) | **have** (full-text + embedding + schema/IO) |
| Typed graph | primitive `input_edge`/`output_edge` + compose zoo | **partial** — edges exist; typed depends/conflicts/supersedes graph NOT built |
| Retrieve | `intent_query` stored-matrix lane + path graph + RRF fusion | **have** |
| Compile context | compose zoo / `route_compose` (edge-valid routes, 0-token) | **have** |
| Compile targets | plan dialect → deterministic builders (py) | **partial** — one target; TS/SQL/MCP/DAG not yet |
| Execute | `real_buildout_ab_harness.execute_lane` (py_compile + pytest sandbox) | **have** |
| Verify | per-pack oracles + `run_proofs` (mutation/determinism/ratchet) | **have** |
| Marginal-utility A/B | bare vs orchestrated vs planned lanes | **partial** — no per-primitive lift gate yet |
| Revise | micro-repair (±6 lines) + save-as-primitive | **partial** — not a formal trace→revise→promote loop |
| Security gate | — | **GAP** (task #13) |
| Govern / lifecycle | candidate/truth boundary (2 stages) | **partial** — need candidate→validated→certified→production |
| Observability | — | **GAP** (OTel) |

## 10. The supply-chain build (SHIPPED 2026-07-08) + the quarry/benchmark-factory backlog

**Shipped (the deterministic-primitive supply-chain spine, all run_proofs-registered, advanced 73-column
search preserved):** ① formal-primitive-package contract (`primitive_package_contract.py` — 16 formal fields,
code-safety scan → permission manifest, D0..D4 determinism budget, risk tier, SLSA provenance, governance
facets feeding the index); ② security gate (`primitive_security_gate.py` + `security/primitive_code_policy.
yaml` — INPUT+CODE, pass/fail/quarantine, all 141 cards pass after a verify-the-verifier false-positive fix);
③ 5-stage lifecycle + truth-serving policy (`primitive_lifecycle.py` — receipt-gated promotion, security-
quarantine fail-safe, pool clean); ④ 7-metric benchmark taxonomy (`primitive_benchmark_taxonomy.py` +
`schemas/benchmark_result.schema.json` — measured determinism, estimated economics labelled honestly, scalar
kernel receipt: entropy 0 / 1200×).

**Backlog (owner-fed research directions, sequenced; each additive + quarantine-first):**
- **Primitive telemetry** (OTel-shaped events, joinable by run_id) — task #19.
- **Contract tests + behavior signatures + adversarial scalar fixtures** — task #20.
- **OFAC pre-screen (narrow candidate/review, never final adverse decision) + stateful/fitted ML schema
  (PurePrimitive vs FittedPrimitiveRecipe vs FittedPrimitiveInstance + 25 ML backbone record types)** — #21.
- **Primitive QUARRY + research-source ledger** (Kaggle notebooks/benchmarks, GitHub/GitLab/Sourcegraph,
  Hugging Face, MCP Registry, PyPI/npm/Docker, papers, LinkedIn weak signals) — mine tests/fixtures/schemas
  into **quarantined** external candidates; NEVER import external code as trusted. New DS benchmarks name the
  missing primitives: LongDS-Bench (state snapshot/diff/rollback), Ambig-DS (ambiguity detector / objective
  resolver — agents silently commit instead of surfacing underspecification), MLE-Dojo (200+ Kaggle
  challenges). Kaggle `kaggle-benchmarks` SDK is the public benchmark-factory venue.
- **Retrieval SAFETY** (SkillResolve risky-siblings: right capability family, wrong sibling; least-privilege
  routing — SkillRouter body-matters 31-44pt) + **behavior-COVERAGE** metric (Skill Coverage: task pass ≠
  behavior-constraint coverage; existing benches covered only ~40%) → add `behavior_constraint` +
  `coverage_report` to the card + a coverage-aware retriever over the 73-column index.
- **API-enrichment tool-wrapper catalog** (owner starter pack, ~20 highest-value): USPS Addresses 3.0,
  Census Geocoder (address→geo, coord→geo), Census ACS by GEOID, HUD ZIP crosswalk, TIGERweb point-in-polygon,
  FCC block, Google/Mapbox/Nominatim geocoding, Overpass nearby-feature, Google Routes drive-time, OurAirports
  nearest-airport, USGS elevation, FEMA flood-zone, NWS/NOAA weather, GLEIF LEI, NPPES NPI, SAM.gov entity/
  exclusions, email/phone validation. These are **tool wrappers** (execution_model=external_tool, permission
  manifest = network egress, D2_bounded_external) — extend `standards_enrichment_registry_minter.py` (already
  17 providers); each becomes a structured primitive with input/output schema + cache-with-source-version +
  provenance fields (request_url_hash, response_timestamp) + quality checks, never a hardcoded host.

## 11. Primitive-OS architecture invariants (owner brief, 2026-07-08 — the scaling frame)

"20 million primitives" is a **primitive operating system**, not a vector DB of skill text. Load-bearing
invariants to hold as we scale:
- **Three layers, store deltas not blobs:** canonical primitive (50k–500k) → typed/domain **variant**
  (1M–5M) → compiled **artifact** per runtime/tenant/policy (20M+). Most storage is deltas + hashes +
  lineage + benchmark receipts, never repeated full bodies. Tenant variants = base + policy delta + schema/
  runtime binding + artifact hash, not a fresh body each.
- **The catalog is the source of truth; every index (vector, lexical, graph) is a REPLACEABLE projection.**
  Rebuilding an index must never lose identity/provenance/benchmark history/lifecycle. (We already honor
  this: JSONL cards + `canonical_id` are truth; the 73-column multi-index is a projection.)
- **Behavior signature = identity** (shipped ba65cf588): names lie, embeddings drift, source hashes churn.
- **Retrieval in stages, not top-k vibes:** query-understanding → hard filters (lifecycle/security/license/
  runtime/permission/tenant) → multi-signal candidates (BM25 + dense + sparse + schema + behavior-sig +
  graph-neighborhood) → rerank by EVIDENCE (benchmark lift, success rate, trust, cost) → graph closure
  (deps/validators/conflicts/superseded) → context compilation (smallest bundle; call by ID, never paste
  bodies). Answer = "safest executable primitive that fits this TYPED workflow, and why."
- **Typed graph edges early:** depends_on/requires_validator/composes_with/conflicts_with/duplicates/
  specializes/supersedes/unsafe_with/verified_on/failed_on/wraps_tool/derived_from_*.
- **Keep NEGATIVE evidence as first-class:** known_bad_inputs, counterexamples, failed_benchmarks,
  unsafe_compositions, reverts, human-review disagreements → "do NOT retrieve X for messy-OCR / intl-names /
  truth-serving." Most skill libraries collect instructions, not evidence.
- **Compile targets are plural:** python/typescript/WASM/SQL/dbt/JSON-Schema/OpenAPI-MCP/Temporal/policy-
  bundle. Author in Python/TS; serve in WASM/SQL/native where it pays. Temporal rule: deterministic workflow
  layer (schema/select/transform/score/route, replayable) vs external activity (LLM/network/DB-write/human/
  browser). **MCP is the plug (export), the registry is the breaker box (trust).**
- **Provenance like a package manager:** primitive.lock + provenance + SBOM (CycloneDX) + security + benchmark
  + signature (Sigstore/SLSA). Compiled workflows pin exact artifact hashes, never "latest".
- **The 15 traps** (doc-worthy): flat vector DB of 20M blobs · SKILL.md as the artifact · similarity without
  schema compatibility · trusting public code/MCP directly · 20M full duplicates vs canonical+delta · no
  negative fixtures · no supersession · no security gate · no benchmark receipts · no behavior signatures ·
  no tenant policy in retrieval · full bodies in agent context · "latest" in prod · ignoring license/
  provenance · truth-serving without production gates.

## 9. The lint finding (our own cards, `lint_primitives.py --report`, 2026-07-08)

**141 live cards score mean 99.55 / 100 on basic hygiene** (140 in 90-100; the only per-card smell is token
bloat — `infer_scalar_type` at 85 from its self-containment preamble, 8 warns). Our cards already carry
routing, typed IO edges, titles, plans, and the candidate boundary — so on the SkillReducer/SKILL.md-smell
axes we are *clean*, which is rare. **The real gap is corpus-wide and structural: 0 of 141 cards carry ANY
of `verifier_id · failure_modes · permission_manifest · marginal_utility_evidence · compatible_models ·
compatible_runtimes`** — the formal-primitive-package fields (Formal Skill / SkVM / SWE-Skills-Bench). That
is the schema-extension backlog, and it is the honest next move before scaling card count.
