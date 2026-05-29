# Measured-lift head-to-head — the protocol that proves OHH's #1 differentiator

Status: methodology + reproducible harness spec, written 2026-05-29. **No live numbers yet** —
the model route is network-blocked in this environment. This doc defines the experiment so it
runs the moment a route is live, and so the result is *defensible* rather than self-flattering.

This is the direct response to the single honest gap the Contextual competitive verdict flagged:
OHH's differentiation **is** measured lift + verified corpora, and the **evidence for the lift half
is currently thin** (`docs/strategy/competitor-contextual-ai.md` — "OHH's measured-lift EVIDENCE
is thin (credibility-critical, must not overclaim)", and concrete next step #2: "Publish a
measured-lift head-to-head on a shared domain … **Do this for real or not at all** —
overclaiming here is the one self-inflicted risk that would cost more than the win"). The lift
*mechanism* and the *durability taxonomy* are real and implemented; what is missing is a single
**paired, separately-judged, held-out** number on a shared domain task, published next to a
competitor demo. This doc is the recipe for that number.

It does **not** restate the engine-rigor requirements — those live in
`docs/strategy/evaluation-methodology-and-rigor.md` (the six diligence-fatal gaps: self-grading,
open-book contamination, the unimplemented fidelity check, n=6/no-CI, the mis-named published
`lift` field, unverifiable arXiv citations) and are the *preconditions* this protocol depends on.
This doc adds what that one does not: the **three-arm comparison design** (what we run against
what), the **shared-domain choice**, the **held-out construction**, and the **publish-or-don't
gate** specific to a *head-to-head against Contextual*. Where the two overlap, the rigor doc is
authoritative; cite it, do not fork it.

---

## 1. What we are proving — and the trap we are avoiding

**The claim under test (one sentence):** *On a shared regulated/technical QA task over a governed
corpus, the OHH governed pipeline lifts a bare model's task accuracy by a measured margin, that
margin is produced by a **separate** evaluator on **held-out** items, and the lift is **structural**
(it will not close when the next base model ships) — a number neither a bare model nor a
Contextual-style agent-over-public-docs reports.*

Two halves, both load-bearing:

1. **Lift exists and is measured** — `pipeline_score − bare_model_score > 0`, computed by
   `scripts/foundry/measure.py` (`MeasurementStage`), not asserted by a metadata heuristic.
2. **The lift is durable** — tagged with a `lift_reason` → `durability_class` from
   `scripts/eval/reason_codes.py` (the single source), so we report *whether the next model erases
   it*, the axis Contextual has no analog for.

**The trap (state it before designing the experiment, so the design forecloses it).** The
Contextual verdict's own warning and `evaluation-methodology-and-rigor.md` together name exactly
how a head-to-head goes wrong, and each failure mode produces a *precise, impressive, meaningless*
number:

| Failure mode | What it fakes | How this protocol forecloses it |
|---|---|---|
| **Self-grading** | The model that answers also grades → self-preference inflates the pipeline arm and depresses the bare arm. `scripts/foundry/model_route.py::wire` today assigns the **same** route to bare, pipeline, *and* judge (verified — `RouteBareModel`, `RoutePipelineRunner`, `RouteJudge` all built from one `route`). | **§5 — independent evaluator.** Judge model family ≠ pipeline/bare family; `judge_independent: true` is a publish precondition (rigor-doc gap 1). |
| **Open-book echo** | The pipeline is handed the gold answer verbatim as "grounding"; the bare model answers closed-book. This measures *reading comprehension*, not *capability the model lacks*. | **§4 — held-out construction + contamination guard.** Gold is derivable independently of the grounding the pipeline sees; `answer_in_grounding` items are excluded from the headline (rigor-doc gap 2). |
| **n=6, no CI, floor 0.0** | A six-item mean with a CI wide enough to include zero, promoted on the point estimate. | **§6 — minimum n, bootstrap/Wilson CI, promote on the lower bound** (rigor-doc gap 4). |
| **Heuristic dressed as lift** | Quoting `dist/reports/capability-lift-gate.json`'s `lift` field, which is a metadata score with **no model and no task**. | **§7 — only a `measurement_kind: measured` record may be cited** (rigor-doc gap 5). |
| **Grounding == lift confusion** | Reporting that the pipeline's answers are *grounded/cited* (which Contextual already does at SOTA) and calling that "lift". | The whole design: lift is **Δ task accuracy vs the same bare model**, never a grounding/faithfulness score. `grounding != lift` (Contextual verdict, next step #3). |

The honest posture, restated as a rule: **a head-to-head that overclaims is worse than no
head-to-head.** A buyer who catches one inflated arm discounts every other OHH number, including
the verified-corpus and governance claims that are solid. The point of this protocol is to make
the lift number survive an adversarial technical reviewer, not to win a slide.

---

## 2. The three arms (the comparison design)

This is the part `evaluation-methodology-and-rigor.md` does not specify: it hardens the *engine*
(bare vs pipeline, internally); this doc adds the **third, competitive arm** and pins all three to
one shared task so the result is a *head-to-head*, not a self-report.

Every arm answers the **same held-out item set** (§3) under the **same separate judge** (§5). The
only thing that varies is what the model is allowed to use.

| Arm | What it is | What it may use | What it represents | Run by |
|---|---|---|---|---|
| **A — Bare model** | The frontier base model, closed-book. | The question only. No retrieval, no grounding, no tools. | The "do we even need a pipeline?" floor. | `RouteBareModel` (`model_route.py`) / `task['bare_answer']` |
| **B — OHH governed pipeline** | The seven-primitive pipeline over the **governed** corpus: Knowledge-Corpus retrieval → deterministic extract-before-model pre-pass (`processor/faithful-extract-before-model`) → grounded generation → an **If-Statement that abstains/routes when the corpus does not support an answer** (never infers). | The governed corpus (verified source-registry provenance), retrieval, the deterministic pre-pass, the abstain/route discipline. | OHH's actual product. | `RoutePipelineRunner` / `scripts/run_pipeline.py` |
| **C — Contextual-style agent over public docs** | A clean-RAG agent over the **same domain corpus ingested as raw public docs** (no provenance, no abstain gate) — the *shape* of a Contextual Agent-Composer demo, reproduced honestly. | The same documents, but ingested-public (no signed-publisher provenance, no freshness/CDC), answer-by-default. | The competitor's surface, so the delta is a *head-to-head*. | A second pipeline config: same retriever, **no** governance layer, **no** abstain gate |

**Why arm C, and how to keep it honest.** The Contextual verdict establishes we should **wrap, not
out-build** Contextual's engines, and that their domain demos are *showcases over ingested public
docs with "no comparison baseline or capability lift analysis"* — i.e. they publish **grounding**,
never **paired lift**. Arm C exists to make that distinction *measurable on one screen*: same
documents, same questions, same judge — the only differences are (a) governance/provenance on the
corpus and (b) the abstain/route discipline. So the B−C delta isolates **exactly OHH's two moat
ingredients** (governed content + abstain-don't-infer), holding the RAG engine constant.

- **Do not strawman arm C.** It must use a *competent* retriever (the same one arm B uses) so the
  comparison is not rigged. If a strong public-docs RAG agent already answers a held-out item
  correctly, that item is in Contextual's addressable space (tiers 1–3) and **arm C should win or
  tie** — that is the honest result, and §3 deliberately includes such items.
- **Where arm B is expected to separate from C is the negative space** (tiers 4–5): items where the
  authoritative source is un-ingestible, volatile, embodiment-/license-gated, or where answering by
  default is *wrong* and abstaining is *correct* (see §3, the held-out item families). There, arm C
  will confidently answer and be wrong (clean RAG "will answer even when it shouldn't" — Contextual
  verdict); arm B abstains-and-routes and is scored correct for the abstention.
- **Optionally a fourth arm, B′ — OHH wrapping a Contextual engine.** Same as arm B but with
  Contextual's Rerank/Generate/Parse wrapped as the engine under the governed layer (the planned
  `contextual-ai` adapter family). This tests the wrap thesis directly: if B′ ≥ B, the governance
  layer carries value *on top of* a SOTA engine, which is the cleanest possible statement of "the
  moat is the governance, not the engine." Mark B′ explicitly `planned` until the adapter exists.

---

## 3. The shared domain task and the held-out item set

**Domain choice — be honest about what exists.** The Contextual verdict and their docs make
**materials-science QA** (their "7,500+ arXiv papers" Material Science Agent) and **3GPP spec QA**
(their "`download_3gpp` CLI" Spec Explorer) the two natural shared domains — both public, both
replicable, both already demoed by Contextual *without* a lift baseline. Either is a candidate.

> **Honest status:** OHH's `data/source-registry.jsonl` today carries **38 verified sources** (35
> gov/standards; regulation 20 / standard 7 / dataset 6 / guidance 5 — counts read live from the
> file, not typed) — and **materials-science / arXiv / 3GPP are not among them** (grep-clean).
> Choosing materials-science means **first registering that corpus** with the same provenance
> discipline (source URL, license, `verified_fetch`, `source_kind`) the registry already enforces.
> That registration is a prerequisite of running this protocol on that domain — do not claim the
> head-to-head is "ready to run on materials-science" until the corpus is registered. **The
> head-to-head IS runnable today on a domain OHH already governs** (the building-/occupational-
> safety PH corpus, below), which is the recommended first instance precisely because it sits in
> the negative space Contextual's clean-RAG cannot reach.

**Recommended first instance — the domain where OHH's wedge is sharpest.** The building-/
occupational-safety PH worked example (`docs/strategy/building-safety-dev-countries-worked-example.md`
+ the five runnable pipelines in `catalog/pipelines/building-occupational-safety-ph/`) is "a
governed domain pipeline over a corpus **exactly** like Contextual's Material-Science agent — but
deliberately built in the NEGATIVE SPACE Contextual's clean-RAG architecturally cannot reach"
(durability 5.0/5.0 via `reason_codes.py`). Running the three arms here is the strongest possible
head-to-head: it is the case where arm C *structurally* cannot win, and the corpus is **already
governed** so no new registration is needed. Materials-science is the *second* instance — the one
that meets Contextual on their own demo turf — and is worth doing once the arXiv corpus is
registered, because winning on *their* domain is more persuasive than winning on ours.

**The task** is **closed-form, citation-backed QA**: each item has a question whose correct answer
is a specific, checkable fact, clause, code, or — critically — **"unanswerable from the available
sources; route to <authority>"**.

**Held-out item families (the design that prevents open-book echo and tests durability):**

1. **Answerable-from-corpus (the lift core).** The answer exists in the governed corpus but is the
   kind a bare model gets wrong: long-tail clause numbers, esoteric coefficients, coded vocabulary.
   *Held-out construction:* the gold is drawn from a **held-out portion of the source the pipeline
   is NOT given as grounding** (per rigor-doc gap 2, fix 2), or the question is **reformulated to
   require combining facts** rather than echoing one span. Each item carries `answer_in_grounding:
   bool`; items where the answer is verbatim in the grounding are scored separately as
   *extraction-fidelity*, not lift (rigor-doc gap 2, fix 1 + 3).
2. **Volatile / freshness items.** The correct answer changed recently (a renumbered IRR clause, a
   superseded coefficient). A bare model's parametric snapshot is stale; the governed corpus is
   CDC-fresh. Tagged `lift_reason: volatile_fact` → structural.
3. **Negative-space / abstain-correct items (where arm C breaks).** The authoritative source is
   un-ingestible, embodiment-required, or license-gated (counter-only permit records, as-built
   floor count, PRC-licensed sign-off). The **correct response is to abstain and route to the named
   authority with citations** — *not* to answer. Arm B (with the abstain If-Statement) is scored
   correct for abstaining; arm C (answer-by-default clean RAG) will hallucinate a confident wrong
   answer. Tagged `lift_reason ∈ {no_addressable_source, embodiment_required,
   accountability_or_license}` → structural. **This family is where `grounding != lift` becomes a
   number:** Contextual's grounded answer is *faithful to a doc that does not contain the answer*,
   and still wrong.
4. **Control / addressable items (honesty ballast).** Plain tier-1–3 facts a competent public-docs
   RAG agent *should* get right. Arm C should win or tie here. Including these prevents the result
   from looking cherry-picked and gives an honest read on where OHH does *not* add lift (a clean
   negative on these items is a feature — it shows the bar is real).

**Held-out discipline (non-negotiable):** items are authored/sealed **before** any arm is run, by
someone other than whoever tunes the pipelines; no arm's outputs feed back into item selection; the
gold answers and the grounding the pipeline receives are **separated at authoring time** so the
contamination guard (§4) can run. Provenance for every item's gold (which source, which clause)
is recorded so a reviewer can re-derive it. Persist as a JSONL the harness already understands:
the per-item shape is the `eval_tasks` row `measure.py` consumes —
`{"prompt", "correct_answer", "bare_answer"?, "pipeline_answer"?, "answer_in_grounding", "item_family", "lift_reason", "gold_source"}`.

---

## 4. Open-book contamination guard (before any arm runs)

This is rigor-doc gap 2 applied to the head-to-head specifically; it runs as a **gate**, not a
post-hoc filter.

1. For every item, compute lexical/n-gram overlap between `correct_answer` and the exact grounding
   text arm B (and arm C) will receive. If the answer is **verbatim present**, set
   `answer_in_grounding: true` and **exclude the item from the headline lift delta** — it tests
   copying, not capability. (It is retained as an *extraction-fidelity* metric, which is what the
   CEaaS `verify.compression_fidelity` check actually wants — see rigor-doc gap 3.)
2. The **bare arm faces the question with no grounding** (it already does). The **gold must be
   derivable independently** of the grounding the pipeline sees (held-out span or fact-combination —
   §3, family 1).
3. **Distinguish the two metrics in the report.** "Did governance let the model answer/abstain
   correctly on an item it otherwise got wrong?" (**lift**) is reported separately from "did the
   compressed tier preserve the answer?" (**fidelity**). This protocol measures the former; it does
   not silently blend them.

A head-to-head where >X% of headline items are `answer_in_grounding: true` is **not a lift
measurement** and must not be published as one (it is an extraction benchmark). Record the
excluded-fraction in the run metadata so the headline's denominator is auditable.

---

## 5. The separate evaluator (no self-grading)

The judge is the part most likely to be quietly wrong, so it is the part this protocol pins hardest.

- **Independence is a precondition, not an option.** The judge route must be a **different model
  family** (ideally a different vendor) from the arm-A/B/C answer model. A run with
  `judge_model_family == answer_model_family` is stamped `judge_independent: false` and is
  **ineligible for external quotation** — routed to review exactly like `unmeasured` (rigor-doc gap
  1). Record `bare_model`, `pipeline_model`, and `judge_model` as distinct provenance fields on the
  `lift` record so independence is auditable per row.
- **Today's wiring violates this and must be changed before publishing.** `model_route.py::wire`
  currently sets `foundry.measure`, `foundry.gaps.prober = RouteBareModel(route)`, and
  `foundry.gaps.judge = RouteJudge(route)` all from **one** `route` (verified). The fix is the
  rigor-doc's gap-1 item (a separate judge route); this protocol *depends* on that fix and should
  not be run for a publishable number until it lands.
- **The judge is OHH's existing eval seam — and this is where Contextual's LMUnit gets wrapped.**
  The judge primitive is `processor/eval/llm-judge` (`process_kind: eval.rubric_llm_judge`,
  `deterministic: false`), whose `model_targets` already declare a `frontier_judge`
  (Anthropic/OpenAI/Gemini) and a `local_judge`. **LMUnit — Contextual's open-sourced
  (arXiv:2412.13091) NL-unit-test judge — is a selectable judge model behind this seam**, exactly
  the highest-value wrap the Contextual verdict identifies (next step #1: "LMUnit is the
  highest-value wrap … make it a selectable judge model behind `processor/eval/llm-judge`"). Using
  LMUnit (or any frontier model from a *different* family than the answer model) as the judge is
  *stronger* than self-grading and turns a competitor asset into OHH's measurement instrument.
  **Note the honest layering:** wrapping LMUnit as the judge satisfies the *independence* and
  *judge-quality* requirements; it does **not** by itself satisfy held-out construction (§4),
  minimum-n/CI (§6), or judge↔human calibration (§5, below) — those are separate gates. A SOTA judge
  on a contaminated item set still produces a meaningless delta.
- **Deterministic where possible.** Where an item has a checkable gold (a clause number, a code, an
  abstain-decision), score it with the deterministic checker (`measure.py::DeterministicChecker`,
  token-F1 / exact match) and reserve the LLM-judge for items with no deterministic ground truth.
  An abstain-correct item (§3, family 3) is *deterministically* scorable: did the arm abstain-and-
  route, yes/no — no LLM judge needed, and no self-grading possible.
- **Judge↔human calibration is the error bar on every delta.** On a small labelled subset, measure
  judge↔human agreement (Cohen's κ / correlation) and **publish it next to the lift number**
  (rigor-doc roadmap step 5). An uncalibrated judge is an unquantified error bar; "the judge said
  0.83" only becomes "0.83 ± …, judge agrees with humans at κ=…" after this step.

---

## 6. The statistic — paired delta with an interval, promoted on the lower bound

`measure.py` today computes a plain mean delta and records `n`, but **no interval** — that is
rigor-doc gap 4, and it is a precondition for *publishing* (not for the engine working).

- **Per item, paired:** record `bare_i` (arm A), `pipe_i` (arm B), and `comp_i` (arm C) on the same
  item, so the differences are paired by item (lower variance than unpaired means). Keep the
  **per-item scores** on the run record so the interval is reproducible (rigor-doc gap 4, fix 4).
- **Headline statistics:**
  - **B−A** = OHH lift over the bare model (the admission-gate number, `pipeline_score −
    bare_model_score`).
  - **B−C** = OHH governed pipeline over a Contextual-style clean-RAG agent (the **head-to-head**
    number — the one Contextual's demos do not publish).
  - **C−A** = how much a *plain public-docs RAG agent* already lifts the bare model (honesty
    context: on addressable items this can be large, and that is fine — it shows where OHH does *not*
    differentiate, isolating the moat to the negative-space items where B−C separates).
- **Interval, not point.** Report `delta_ci_low` / `delta_ci_high` from a **bootstrap** over the
  per-item paired differences; for the binary abstain-correct / answer-correct items, use a **Wilson
  score interval** on the pass-rate difference (the honest small-sample interval). **Promote/publish
  on the lower bound:** `delta_ci_low > lift_floor`, i.e. "we are confident the lift is real," not
  "the average looked positive" (rigor-doc gap 4, fix 3). A point estimate above the floor with a CI
  straddling it → **more items / review**, not a headline.
- **Minimum n.** Below `MIN_EVAL_TASKS` (a named constant with rationale — rigor-doc gap 4, fix 1)
  the result is `unmeasured`, not published. `measure.py`'s offline self-test uses n=2; that is a
  *development* minimum, never a publication minimum.
- **Report per item-family.** A single blended delta hides the mechanism. Report B−A and B−C
  **broken out by the four item-families of §3**, so a reader sees *where* the lift comes from
  (negative-space + volatile items, not the addressable controls). This is also the honest defense
  against "you cherry-picked": the controls are in the denominator and reported.

---

## 7. Durability — the axis Contextual structurally lacks

A measured delta is necessary but not sufficient for an OHH admission claim. The second axis is
**will it survive the next model**, and it is what makes the head-to-head a *moat* statement rather
than a benchmark snapshot.

- Tag every item / item-family with a `lift_reason` from `scripts/eval/reason_codes.py` (the single
  source — never re-defined here). The harness derives `durability_class` (transient | structural |
  mixed) and the `gap_durability_score` (0..5) via `classify_gap` in
  `scripts/eval/durable_gap_harness.py`.
- **The headline lift must be paired with its durability class.** A `+0.30` on
  `lift_reason: long_tail_fact` is **transient** — honest revenue today, *not* a defensibility
  claim (the data flywheel closes it; keep its traces governed). A `+0.30` on
  `no_addressable_source` / `embodiment_required` / `accountability_or_license` is **structural** —
  the moat. Report the delta and the class **together, always.** The Contextual verdict's whole
  point: "Contextual measures answer quality; it has **no** will-it-survive axis."
- **The negative-space item-family (§3, family 3) is structural by construction**, which is why the
  building-safety instance scores durability 5.0/5.0 — and why arm C's confident-wrong answers there
  are not a transient engine deficiency Contextual will patch, but a *structural* consequence of
  clean-RAG-over-ingestible-sources answering when it should abstain.

---

## 8. The single publish-or-don't gate (the rule this doc enforces)

Reuse the rigor-doc's enforceable rule verbatim — this protocol does not invent a looser one. A
head-to-head lift/fidelity number may be quoted **externally** (a pitch, a `dist/` artifact, a
comparison slide vs Contextual) **only if** its `lift` record carries **all** of:

- `measurement_kind: measured` (a real `pipeline_score − bare_model_score`, **not** the metadata
  heuristic in `dist/reports/capability-lift-gate.json` — rigor-doc gap 5);
- `judge_independent: true` (judge family ≠ answer family — §5, rigor-doc gap 1);
- `answer_in_grounding: false` on the headline items (or an explicit extraction-fidelity caveat —
  §4, rigor-doc gap 2);
- `n ≥ MIN_EVAL_TASKS` (§6, rigor-doc gap 4);
- `delta_ci_low > lift_floor` (promote on the lower bound — §6);
- a recorded **judge↔human calibration** (§5, rigor-doc roadmap step 5);
- a `durability_class` paired with the number (§7).

**Anything missing one qualifier is a development signal, labelled as such, and stays internal.**
Encode the gate as a validate/CI check on any artifact bound for `dist/` or a pitch (the same
drift-guard `no-magic-values` mandates), so the discipline cannot silently regress. This is the
mechanical form of the Contextual verdict's "**do this for real or not at all**."

---

## 9. Honest status — what is real, what is spec, what is blocked

Stated plainly, per the change-verification contract's honesty requirement (no filler, no invented
metrics, real-vs-spec-vs-aspirational):

- **REAL and implemented:** the lift *mechanism* (`scripts/foundry/measure.py::MeasurementStage`
  computes a paired delta over recorded/generated answers and **leaves `lift = None` → review when
  unmeasured**, never fabricating a number); the durability taxonomy
  (`scripts/eval/reason_codes.py` — 13 lift_reasons, 3 durability classes, the 0..5 score) and its
  sorter (`scripts/eval/durable_gap_harness.py`); the judge seam (`processor/eval/llm-judge`, with
  `model_targets` ready to host LMUnit); the model route + wire (`scripts/foundry/model_route.py`);
  the building-safety governed corpus and its five runnable pipelines (the recommended first
  instance, already governed); the source registry (38 verified sources). The compression
  processors this lane builds on (`scripts/processors/compression/structural_compress.py`,
  `scripts/processors/verify/compression_fidelity_check.py`) are real.
- **SPEC-level (this doc + the rigor doc specify; engine items not yet landed):** the **separate
  judge route** (today `wire` shares one route across bare/pipeline/judge — must be fixed before a
  publishable number — rigor-doc gap 1); the **bootstrap/Wilson CI + `MIN_EVAL_TASKS`**
  (`measure.py` reports a mean + `n` only — rigor-doc gap 4); the **open-book contamination guard +
  `answer_in_grounding` flag** (rigor-doc gap 2); the **`measurement_kind` stamp + renamed
  published `lift` field** (rigor-doc gap 5); the **publish-or-don't CI gate** (§8); the
  **`contextual-ai` adapter family** for arm B′ (Contextual verdict next step #1). The
  materials-science corpus is **not registered** (grep-clean) — registering it is a prerequisite of
  running this protocol on that domain.
- **BLOCKED here, by design:** **no live model route in this environment** (network-blocked), so
  there are **no real numbers in this doc and there must not be.** This is the *harness/methodology*
  — it is written so that the moment a route is wired (a key + the gap-1 separate-judge fix), the
  experiment runs end-to-end and emits a `lift` record that either clears the §8 gate (publishable)
  or routes to review (internal). **Honesty rule, restated:** claim the lift *mechanism* and the
  *durability taxonomy* as real; claim the *head-to-head number* only once it exists, is
  separately-judged, held-out, CI-bounded, and durability-classed — never before.

---

## 10. Run recipe (the moment a route is live)

1. **Pick the instance.** First: building-/occupational-safety PH (already governed; negative-space;
   arm C structurally cannot win). Second, for a head-to-head on Contextual's own turf: register the
   materials-science arXiv corpus in `data/source-registry.jsonl` with full provenance, *then* run.
2. **Author the held-out item set** (§3) — sealed before any arm runs, gold separated from
   grounding, four item-families, persisted as `eval_tasks` JSONL.
3. **Run the contamination guard** (§4) — drop/relabel `answer_in_grounding` items from the headline.
4. **Wire two model families** — one for the answer arms (A/B/C), a **different** one for the judge
   (§5; LMUnit is a valid judge). Apply the gap-1 separate-judge fix first.
5. **Run the three arms** on the same items under the same judge (`measure.py` paired; the
   abstain-correct items scored deterministically).
6. **Compute B−A, B−C, C−A with intervals** (§6), broken out by item-family, paired with the
   `durability_class` (§7).
7. **Apply the §8 publish gate.** Clears all qualifiers → publish the head-to-head next to
   Contextual's baseline-free Material-Science demo. Misses one → label development-signal, keep
   internal, fix the missing qualifier.

---

## Related (referenced, not duplicated)

- `docs/strategy/competitor-contextual-ai.md` — the verdict this actions; `grounding != lift`,
  `ingested-public != governed`, "do this for real or not at all," and the thin-evidence flag.
- `docs/strategy/evaluation-methodology-and-rigor.md` — the six diligence-fatal gaps and the
  enforceable publish rule; the **engine preconditions** this protocol depends on (authoritative
  where the two overlap).
- `scripts/eval/reason_codes.py` · `scripts/eval/durable_gap_harness.py` — the durability axis
  (single source) and its sorter.
- `scripts/foundry/measure.py` · `scripts/foundry/model_route.py` — the lift engine and the
  (currently shared-route) model wiring the §5 fix targets.
- `catalog/processors/eval/llm-judge.yaml` — the judge seam LMUnit wraps into.
- `docs/strategy/building-safety-dev-countries-worked-example.md` +
  `catalog/pipelines/building-occupational-safety-ph/` — the recommended first instance (negative
  space, durability 5.0/5.0).
- `docs/codex/change-verification-contract.md` · `docs/codex/no-magic-values.md` — the honesty
  warrant and the drift-guard the §8 CI gate applies.
