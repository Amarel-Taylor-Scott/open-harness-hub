# Edge-First Composition — Public Benchmark Plan

*AIDevObserver Benchmark Lab · v1 plan, 2026-07-01. Companion to
`docs/whitepapers/read-the-edges-not-the-code.md`. Everything this program produces is
`candidate=true / serves_truth=false` promotion EVIDENCE with per-run receipts; a winning scorecard never
promotes anything by itself. (Internal corpora historically live under the legacy `aidevexplorer`
namespace — not a branded surface.)*

## 0. The claims under test

1. **Context claim** — an agent reading only edge contracts completes the task with orders-of-magnitude
   less context than one reading implementations, at output equivalence.
2. **Quality claim** — primitive-first runs avoid known pitfalls (silent row drops, non-idempotent retries,
   missing audit trails) more often than baseline runs, because proofs travel with primitives.
3. **Reuse claim** — the same core route is reused across runtime shapes and sessions instead of rebuilt.
4. **Economics claim** — total resources (tokens, machine memory, CPU/wall, model calls, $) fall, and fall
   further over time as routes harden down the compute-tier ladder.

## 1. Arms

| Arm | Description |
|---|---|
| **A — baseline** | coding agent with normal repo access; no primitive search |
| **B — primitive-first** | same agent; edge-card search + graph ordering + mutation adapters first; source only on named escalation |
| **C — cards + constraints** | edge cards plus a compact plan-delta constraint block (template choice, slot bindings, requested mutations) — no free reading at all |
| **B0 — deterministic floor** | no model calls: template/route match + deterministic assembly only (v0 shipped 2026-07-01) |
| Model tiers | each of A/B/C runs per tier: light (Gemma-4 class) · mid (Kimi/GLM class) · SOTA — plus cross-tier pairs (SOTA plan + light execution) |

## 2. Resource envelope (recorded per run, every estimate basis-labeled)

`context_bytes_read` (edge cards vs implementation bytes; exact from harness) · `tokens` (exact when logs
exist > tokenizer-estimated > deterministic proxy chars/4 — basis on every receipt) · `peak_rss_kb` +
`py_alloc_peak_kb` (subprocess-isolated) · `cpu_ms` / `wall_ms` · `model_calls` per tier · `$ estimate` ·
correctness (canonical output hash vs fixture) · proof completeness (obligations satisfied / required) ·
pitfalls hit (per-task trap list) · reuse events (existing route adopted vs rebuilt) ·
**`source_escalations`** (count + reason distribution over the five legitimate reasons: modify / debug-proof
/ security-audit / missing-metadata / contract-contradiction — the escalation rate is the honest measure of
card quality, and context tier consumed per step: alias · signature · card · evidence · canonical · snippet
· full source).

## 3. Corpora (staged, all fixtures carry expected findings + false-positive traps)

1. **Micro-tasks (P0)** — 100–300 tasks sampled from the 10,000-row real-world build-task corpus
   (100 archetypes × 100 business contexts), each with fixture tests and pitfall traps.
2. **Runtime-shape matrix** — 25 core tasks × 4–10 shapes (py.fn / api.endpoint / queue.consumer / cron.job
   / microservice…): scores whether ONLY the wrapper changes (hidden member edges reused).
3. **Session-review fixtures** — 8 domains × 10 recorded agent sessions with known-missed reuse; primary
   metric: high-confidence `source_ref` precision (developers stop trusting wrong pointers immediately).
4. **Industry packs** — procurement-opportunity ingestion, provider-directory freshness, billing
   reconciliation, document→JSON extraction: auditability-heavy domains where receipts are the buying
   reason. One pack per quarter, each with a domain-expert-reviewed trap list.
5. **Negative controls** — clean sessions (nothing to find), tasks with NO matching primitive (the honest
   agent must say so and fall through to synthesis), and poisoned cards (drift planted deliberately —
   the system must catch the lie, not compose it).
6. **Public-benchmark arms** — run A/B/C on established external suites, chosen honestly by regime:
   composition-dominant suites (workflow/task-automation, data-pipeline builds) are the FAVORABLE case;
   repo-level issue-fix suites (SWE-bench class) are the ADVERSE case — bug-fixing inside unfamiliar
   internals is where source escalation should dominate, and we publish that result with the same
   prominence. Metrics: speed, tokens, cost, solve rate, escalation rate.
7. **Ingestion-quality corpus** — decomposition foundries over projects / websites / process docs /
   textbooks: sampled cards audited for contract truthfulness (does the stated edge match observed
   behavior on fixtures?), blocking effectiveness (candidate-pair reduction ratio at constant recall),
   and template yield per source family.

## 4. Capability phases (each phase gates the next; bounded runs; ledger + manifest per cycle)

**P1 — Search management.** Hybrid retrieval quality over the registry (now 72k+ edge cards): lexical +
typed-edge + vector + graph-adjacency channels, ablated individually. Metrics: recall@k against labeled
matches, wrong-pointer rate, query latency, index freshness lag. Includes registry-scale stress (does
retrieval hold at 500k cards?) and visibility-scope safety (public demos never surface private edges).

**P2 — Ordering / semantic hybrid graphing.** From candidate cards to a valid route: typed-edge chaining,
acyclicity + satisfiability verification, dry-run on synthetic data. Metrics: valid-graph rate,
route-optimality vs known-best (cost-weighted), recovery behavior when no route exists. Hybrid = symbolic
edge types AND embedding similarity AND co-composition graph priors; ablate each.

**P3 — Deterministic adjustment (mutations).** Given near-fit edges, apply registered mutation operators
(scalar→sequence, field rename, output wrapper, schema-validator insert, retry/idempotency/cache wrappers,
runtime-shape wrappers). Metrics: adapter-instead-of-rebuild rate, mutation proof-obligation pass rate,
glue-code lines avoided.

**P4 — Genetic mutation tournaments.** Populations of primitive VARIANTS (mutation stacks, cheaper model
substitutions, batching shapes) compete on fixtures; selection by measured lift + receipts, lineage
preserved losslessly, losers retained as negative memory. Metrics: generations-to-improvement, lift per
generation, regression rate, promotion-review yield. LLM tiers may PROPOSE variants; only evidence selects.

**P5 — Troubleshooting drills.** Inject failures (bad input, contract drift, node crash, poisoned card) into
composed graphs. Metrics: time-to-named-node (receipt quality), drill-down depth needed (member edges vs
source), fix-without-reading-source rate, mean bytes read to diagnose. This phase answers the black-box
trust objection with numbers.

**P6 — Tier-ladder ablations.** Same corpus at deterministic-only / +light / +mid / +SOTA. Metrics: solve
rate per tier, marginal lift per added tier, $ per solved task, descent rate (share of tasks that harden to
a cheaper tier after N successes). The headline economics chart comes from this phase.

**P7 — Longitudinal reuse.** Replayed team-simulation: 100 sessions over a growing registry. Metrics:
rebuild rate over time, tokens/session trend, template-hit rate, negative-memory effectiveness (dismissed
suggestions stop recurring).

## 4b. Hypothesis map (the four falsifiable claims → phases)

| Hypothesis | Tested by | Kill criterion |
|---|---|---|
| **H1** — interface-level context suffices for many tasks | arms A/B/C over P1–P2 corpora | B/C solve-rate materially below A at equal correctness |
| **H2** — deterministic remix replaces most glue code | P3 mismatch suite | mutation pass-rate low or proof obligations routinely unsatisfiable |
| **H3** — session review catches reinvention credibly | corpus #3 fixtures | top-1 `source_ref` precision below the trust bar; false positives on clean sessions |
| **H4** — composite primitives compound savings | P7 longitudinal | tokens/session flat over 100 sessions; template-hit rate stagnant |

## 5. Reporting rules (what makes the numbers publishable)

- Every metric carries its **basis label**; exact > estimated > proxy, never silently mixed.
- Arms must be **output-equivalent** (canonical hash or fixture pass) for a comparison to count.
- Machine-side costs (memory/time) are reported **next to** agent-side wins — the +8 MB / +0.6 s receipt
  tax from v0 stays in the table; we publish trade-offs, not highlights.
- Per-phase manifests + receipts ship with the report; quality levels reported separately
  (L0 raw → L6 preferred route), never one collapsed "primitives generated" number.
- Negative controls and failed claims are published with the same prominence as wins.

## 6. Cadence + first milestones

- **M0 (shipped 2026-07-01):** B0 deterministic floor — 486x context reduction at output equivalence,
  +8 MB RSS runtime tax, receipts in `data/dev-intel/primitive_lift_benchmark/`.
- **M1:** P1+P2 on 100 P0 micro-tasks, light+mid tiers, publish search/ordering quality — PLUS the two
  replications the 2026-07-01 verification pass identified as the evidence base's weakest links:
  (a) **skeleton-vs-full with EXECUTED fixes** on public repos (upgrading the location-only vendor
  preprint), and (b) **cross-scaffold read-share instrumentation** (validating the 67.5–76.1%
  file-read token share beyond a single bash-only scaffold). These two close the citation gaps that
  currently keep the whitepaper at v0.95.
- **M2:** P3+P5 (mutations + troubleshooting) — the trust numbers.
- **M3:** Runtime-shape matrix + P6 ladder ablations — the economics chart.
- **M4:** P4 genetic tournaments + P7 longitudinal — the flywheel numbers; whitepaper v1.0 evidence appendix.

## External benchmark adapter catalog (W7 demand side)

The owner supplied a 240-track inventory of public LLM / agentic coding-and-development benchmarks to
run **with and without** the primitive-first stack. It is single-sourced as a typed registry — 5 families
(coding/repo/SWE/terminal · function-calling/tool-use · web/OS/desktop/mobile/company agents ·
data-science/ML/document/table/RAG/retrieval · cybersecurity/DevSecOps, defensive-only), a 40-track
priority-first set, the **A0..A8 comparison arms** (reference → baseline agent → repo-search agent →
observer-review → template-fill → CandidateBundle+PlanDelta → deterministic-remix → LLM-micro-repair →
source-codegen-fallback), and the **L1..L7 disclosure-depth ladder** (the headline is *how shallow the
agent could stay*, not pass/fail). Scorecard metrics track token axes **and memory/wall-clock**, plus
recall/route/proof/escalation-depth.

- Registry: `catalog/knowledge-packs/data/benchmark-lab-adapter-catalog/benchmarks.jsonl`
  (+ `manifest.json`); generator + self-test: `scripts/build_benchmark_lab_adapter_catalog.py`
  (registered in `scripts/flywheel_proof_modules.py`).
- Boundary: every track is `candidate=true` / `serves_truth=false`, `adapter_state=unbuilt`. Names are
  **unverified intake** — each needs a `BenchmarkSource → BenchmarkTask` adapter built and verified
  runnable before any derived score is trusted. A benchmark score is **evidence, never promotion
  authority** (no benchmark gate in the promotion path).
