# Traction & metrics — what is real, what is staged, what is aspirational

> **PRIVATE — internal acquisition prep.** This page's credibility *is* the asset. It states
> only what is **measured or directly computable**, separates that from what is **staged** or
> **aspirational**, and tells you the exact command to recompute every number so nothing here
> can quietly drift out of date. **No number on this page is hand-typed into prose** as a
> standing claim — where a count appears it is labelled with the command that produces it, per
> [[../../codex/no-magic-values.md]]. If a metric isn't computed/known, this page says so.
>
> **Warrant.** *User intent* — the owner asked for acquihire prep with an honest traction +
> metrics page (full docs + dogfood + use cases). *Established principle* — the
> change-verification contract ([[../../codex/change-verification-contract.md]]) and the
> capability-lift bar ([[../../codex/master-goal.md]]): we admit on **measured** lift and never
> present generated/aspirational counts as shipped. *Corroboration* — the external SkillsBench /
> Skill Lift benchmark (arXiv:2602.12670) for the lift-measurement methodology
> ([[../../strategy/skillsbench-alignment.md]]).

## How to read this page (the three-state rule)

Every claim is tagged one of three ways. Conflating them is the exact failure this page exists
to prevent:

- **REAL** — runs, is self-tested green, or is directly computable from the repo right now.
- **STAGED** — exists as a governed definition / candidate row / spec, *not* promoted to a
  tenant-visible, measured, vectorized state. Structurally present; not yet load-bearing.
- **ASPIRATIONAL** — designed and documented; no running implementation yet.

The promotion boundary ([[../../codex/master-goal.md]], `CLAUDE.md`) is the line between STAGED
and REAL for catalog content: a row is not REAL traction until it has measured lift, real
provenance, and a real embedding, with no open high-risk review.

---

## 1. What exists today (REAL)

### 1.1 The catalog (substrate) — computable, not asserted

The catalog is a body of schema-validated component definitions. **Do not quote a frozen
number** — it changes per branch and per generation run, and the README's generated block has
been observed stale on this branch (the drift guard is exactly why we never hand-type it).
Recompute on demand:

```bash
python3 scripts/build_readme_stats.py            # writes the generated README block
python3 scripts/build_readme_stats.py --check     # exits non-zero if the block has drifted
```

What that command reports (and what each line *means* for traction):

- **Schema-validated definitions** — the gross substrate. A large fraction are
  **machine-generated candidates pending review/promotion** (STAGED), not committed, promoted
  components. The generated block splits "committed to git" from "candidates pending
  review/promotion" precisely so the two are never conflated. **Quote the split, never the
  total.**
- **By type** — the distribution across the seven-primitive grammar plus benchmarks/rubrics/
  datasets/adapters.
- **Derived query DB** (`dist/catalog.sqlite`) — a built SQLite index with objects + relationship
  edges and **0 embeddings**. The 0 is honest and load-bearing: see §3.

> **Honest caveat (the number that matters most).** The substrate count is **not** a traction
> metric. Per the daily contract ([[../../codex/master-goal.md]]), traction is **useful-promoted
> components** — gate-cleared, measured, vectorized — *not* generated. A day that generates
> thousands of candidates and promotes none scores **zero**. State the committed/promoted split,
> and §3 for what's still missing before promoted rows are tenant-visible.

### 1.2 The foundry — evidence-driven generation, self-tested green (REAL)

The foundry (`scripts/foundry/`) is the engine that admits a component only on three evidence
pillars — a **measured** bare-model failure (gap), a **real licensed source**, and a **measured
lift** — then standardizes, dedupes (SimHash + LSH + source-key), benchmark-measures, gates, and
human-approves (knowledge always routes to a human; the model can't self-certify its own gaps).
A clone cross-product cannot satisfy that, so filler is impossible *by construction*. This is
REAL and verifiable offline today:

```bash
python -m scripts.foundry.pipeline   --self-test    # full gap→source→…→gate→stage_load, offline
python -m scripts.foundry.measure    --self-test    # the lift-measurement engine
python -m scripts.foundry.skillsbench --self-test    # the SkillsBench Action↔skill bridge
```

Observed on this branch: **all three self-test suites pass (exit 0).** The pipeline self-test
demonstrates the discipline end-to-end — same-source clones dropped, a no-lift candidate culled,
two promoted components each satisfying all three evidence pillars, knowledge held for human
approval, a public-registry rule auto-approved, and an embedding correctly flagged `placeholder`
(staging-only). **Every foundry stage module ships its own self-test** (recompute the module list
with `grep -lE "self_test|--self-test" scripts/foundry/*.py | wc -l`). *Note:* the README prose
that says "19 self-tested modules" is a hand-typed count and runs slightly behind the computed
figure — treat the `grep` as source of truth, not the prose (a no-magic-values cleanup, tracked
to the owning doc).

**What this proves vs. doesn't.** It proves the *engine* enforces the bar correctly on its test
fixtures and the production seam is wired (a `BareModel` + `PipelineRunner` + `Judge` plug in to
generate and score real bare-vs-pipeline answers). It does **not** prove the *shipped catalog* is
populated with measured deltas — see §3.

### 1.3 The two live demos (REAL — running now)

Two distinct products run on the shared backend ([[../../strategy/two-services-shared-infrastructure.md]]),
each as its own showcase server behind its own public token-gated tunnel:

| Product | Port | Live check (observed) | Share URL location |
|---|---|---|---|
| **OpenHubForAI** — bounded build/monitor pipelines | 8000 | `HTTP 200` | `dist/showcase-share-url-harness-hub.txt` |
| **Baltor (Baltor)** — governed context enrichment | 8001 | `HTTP 200` | `dist/showcase-share-url-baltor.txt` |

Recompute liveness any time (don't trust this table blind — it's a point-in-time observation):

```bash
curl -s -o /dev/null -w "8000 HTTP %{http_code}\n" http://localhost:8000/
curl -s -o /dev/null -w "8001 HTTP %{http_code}\n" http://localhost:8001/
pgrep -af cloudflared          # both tunnels (8000 + 8001) should be listed
```

Both showcase processes and both `cloudflared` tunnels were observed running, and both share
URLs carry the same access token. The demos are a **shared-backend demonstration**, not a
metered production deployment — the distinction matters in §3.

**Pre-baked end-to-end runs.** 14 `scripts/demo_*.py` scripts execute full vertical pipelines
offline (ESG/CSDDD, radiology, contract review, AppSec, GxP/climate/threat-intel, and more) —
`ls scripts/demo_*.py | wc -l` to recompute. These are reproducible dogfood runs, not a metered
product.

### 1.4 SkillsBench external validation (REAL — third-party corroboration)

This is the strongest *external* asset on the page, because the metric is **not ours**.
BenchFlow's **SkillsBench / "Skill Lift"** benchmark (Kaggle, May–Jul 2026; arXiv:2602.12670,
ClawsBench arXiv:2604.05172) measures exactly our admission criterion — how much a skill lifts an
agent, **paired with-skill minus without-skill**, with an adversarial safety gate. The mapping is
one-to-one ([[../../strategy/skillsbench-alignment.md]]):

- their **lift** = Δ pass-rate (with − without) ≡ our `pipeline_score − bare_model_score`;
- their **public→private generalisation** ≡ our **durability** axis;
- their **ClawsBench** safety gate (unsafe → score −1.0) ≡ our governance moat.

The published headline numbers are why this product exists, and we cite them **as theirs, not as
our results**: across 84 expert tasks SkillsBench reports **+16.4pp average lift — but 18 of the
84 tasks regress, and skills a model writes for itself net −1.3pp**. That is the empirical case
for measuring lift rather than asserting it, for human approval over model self-authoring, and
for a safety gate. Our bridge (`scripts/foundry/skillsbench.py`, self-tested green) makes the
catalog **submittable to Skill Lift today** (EXPORT: any Action → a `SKILL.md` bundle with a
procedure *derived* from the component's real structure) and imports a task as an evidence triple
(IMPORT), **never fabricating a Δ** — an unmeasured task is held, not promoted.

> **Honest line for the data room:** "An independent, peer-reviewed benchmark operationalises our
> exact admission metric and our exact safety concern. We are interoperable with it and
> submittable to it. We have **not** yet published our own catalog's Skill Lift scores" — that is
> the §3 gap, stated plainly.

---

## 2. Measurement methodology (what makes a number trustworthy)

The credibility of every lift/fidelity number rests on two properties, both enforced in code:

### 2.1 Paired, held-out, deterministic-first

Lift is `pipeline_score − bare_model_score` measured on **held-out** task instances for a task
family, scored by a `Judge` (`scripts/foundry/measure.py`). The default judge is a
**deterministic token-F1** against a known `correct_answer` — used wherever there is ground
truth, so the score is reproducible and not model-opinion. An LLM-judge is used only where no
deterministic ground truth exists. Measurement is **amortized per family** (model calls per task
family, not per row), which is what makes volume affordable.

### 2.2 Separate evaluator — never self-graded

The builder never grades its own work. This holds at two levels:

- **In the foundry**, the `Judge` is a distinct component from the `PipelineRunner`/`BareModel`,
  and offline it scores *recorded* answers — it does not invent them. If no answers and no wired
  model are available, lift stays `None` and the gate routes the candidate to **review**; it
  **never makes up a number** (verified by `measure --self-test`: the "no recorded answers ⇒
  unmeasured (None)" and "budget=0 ⇒ no fabricated delta" cases pass).
- **In the change process**, the change-verification contract requires a *different agent* to
  verify than the one that built ([[../../codex/change-verification-contract.md]], "no agent
  grades its own work").

### 2.3 The same engine measures Baltor fidelity

Baltor's **measured-fidelity-per-tier** guarantee (raw → compressed → hyper-efficient) is the
*same* paired, separately-evaluated engine, extended from "does the pipeline lift?" to "did this
tier preserve enough?" ([[../../strategy/context-enrichment-service.md]]). Same moat, same
honesty rule — and **the same current gap:** the fidelity harness is specified and the components
seeded; per-tier fidelity deltas are not yet published (§3).

---

## 3. The gaps — what is STAGED or ASPIRATIONAL (state these first in any pitch)

These are the honest weaknesses. Leading with them is what makes §1 believable.

| Capability | State | Evidence / why |
|---|---|---|
| **Measured lift on the *shipped catalog*** | **STAGED** | The measurement *engine* is REAL and green, but **0 committed catalog definitions currently carry a recorded `bare_score`/`pipeline_score` delta** (recompute: `grep -rlE "bare_score\|pipeline_score" catalog/ \| wc -l`). Lift today is proven on engine fixtures + the foundry self-test + SkillsBench's *external* numbers — **not** on shipped rows. This is the single most important caveat on the page. |
| **Vector search (embeddings)** | **STAGED → blocked** | `dist/catalog.sqlite` has **0 embeddings** (recompute: query the `embeddings` table). Per the master goal this is gate #6 (❌) and the P1 unblock. Until real embeddings exist (declared model + dim), no row is promotion-ready and hybrid vector search is not live. |
| **Capability-lift *gate*** | **STAGED** | The scorer (`candidate_promotion_scorer.py`) *scores* lift but does not yet hard-**gate** on it (master goal gate #4, ⚠️). The foundry pipeline *does* gate (self-test confirms a no-lift candidate is culled); the standing promotion scorer does not yet. |
| **Baltor as a running service** | **ASPIRATIONAL / seeded** | `services/registry.yaml` lists `enrichment` as `status: planned`; the tier/surface/fidelity **components are seeded** (`scripts/seed/baltor_components.py`, lifecycle experimental) but the tier pipeline, MCP serving endpoint, four emitters, and the token-efficiency/fidelity meter are not built ([[../../strategy/context-enrichment-service.md]]). The Baltor *demo surface* (8001) is REAL; the Baltor *service* is not. |
| **Production telemetry on the demos** | **ASPIRATIONAL on the showcase** | `services/registry.yaml` specifies Prometheus `/metrics` + OpenTelemetry traces, but the live showcase returns `HTTP 404` on `/metrics` (observed). The telemetry plane is designed, not wired on the running demo. |
| **Paying customers / revenue / usage** | **NONE — do not imply otherwise** | There is no metered production deployment, no billing, and **no revenue or paid-usage metric to report.** The monetization model (open-core, freezable-vs-recurring, build-on-demand) is a documented *strategy*, not realized traction. |
| **Scaled daily yield (10k useful/day)** | **ASPIRATIONAL** | Master goal P5. The factory can *generate* at volume (ledger: ~1k candidates ≈ 31s); the *useful-promoted/day* yield metric — the one that counts — is not yet sustained, because promotion is blocked on embeddings + the lift gate above. |

---

## 4. The honest one-paragraph summary (for the data room)

OpenHubForAI is a **real, self-tested engine with a real thesis and real external
validation, not yet a metered product with revenue.** What runs today: an evidence-driven
foundry whose three self-test suites pass green and which enforces a measured-lift-or-reject
discipline by construction; two distinct products live on a shared backend behind public tunnels;
a large schema-validated candidate substrate (recompute, never quote a frozen total); and a
one-to-one bridge to SkillsBench, the independent benchmark that operationalises our exact lift
metric and safety gate (their published +16.4pp-average / 18-of-84-regress result is the
empirical case for our whole design — cited as *theirs*). What is **not** yet real: measured lift
on the *shipped* catalog (0 rows carry a recorded delta), vector embeddings (0 in the derived
DB), Baltor as a running service (seeded + spec'd, `status: planned`), production telemetry on the
demos, and any revenue/usage. The asset being acquired is **the governed measurement engine + the
two-door GTM + the external-validation alignment**, with a clearly-bounded build list to turn
STAGED into REAL — not a finished, monetized platform.

---

## 5. Recompute everything (so this page can't rot)

```bash
# substrate counts (committed vs candidates, by type, embeddings)
python3 scripts/build_readme_stats.py --check

# the engine is green
python -m scripts.foundry.pipeline   --self-test
python -m scripts.foundry.measure    --self-test
python -m scripts.foundry.skillsbench --self-test

# the demos are live
curl -s -o /dev/null -w "8000 %{http_code}\n" http://localhost:8000/
curl -s -o /dev/null -w "8001 %{http_code}\n" http://localhost:8001/

# the central caveat: measured deltas on the shipped catalog (expect 0 until §3 closes)
grep -rlE "bare_score|pipeline_score" catalog/ | wc -l
```

Related: [[../../codex/master-goal.md]] · [[../../codex/change-verification-contract.md]] ·
[[../../codex/no-magic-values.md]] · [[../../strategy/skillsbench-alignment.md]] ·
[[../../strategy/two-services-shared-infrastructure.md]] · [[../../strategy/context-enrichment-service.md]] ·
[[../../design/value-propositions.md]].
