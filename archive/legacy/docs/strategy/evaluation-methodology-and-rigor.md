# Evaluation methodology and the rigor roadmap

The two-axis admission bar ([[north-stars]], [[two-axis-lift-gate]]) is the whole product thesis: a
component is admitted **only on measured `pipeline_score − bare_model_score`** that is **structural**
([[capability-valleys]]). The engine that computes that delta — `scripts/foundry/measure.py`,
`gate.py`, `benchmark_synth.py`, `model_route.py` — is small, deterministic, and well-tested. The
*math* is clean.

What is **not** yet defensible is the **measurement methodology** behind the number. This doc states,
honestly and in one place, the gaps an acquirer's technical diligence will find, why each one inflates
or fabricates a "+lift" figure, and the concrete fix and calibration plan for each. **It is the
prerequisite for ever quoting a `+lift` number externally.** The math being correct does not make the
measurement valid — a clean function over a contaminated benchmark, self-graded, at n=6, produces a
precise number that means nothing.

The code fixes for these gaps are tracked as separate, disjoint engine items; this doc is purely
additive and edits no code. It references — does not modify — `model_route.py`, `measure.py`,
`benchmark_synth.py`, and `gate.py`.

## TL;DR — the bar, restated honestly

> A measured lift is credible only when an **independent** judge scores a **closed-book** bare baseline
> against an **open-book** pipeline on a **held-out, uncontaminated** benchmark of **sufficient n**,
> reports a **confidence interval**, and is itself **calibrated against human judgment**. Until then the
> number is a *development signal*, not an *external claim*, and must be labelled as such.

We currently satisfy almost none of those qualifiers in the live (model-wired) path. The offline path
is honest by construction (it scores *recorded* answers and refuses to fabricate — `measure.py`
docstring and the `unmeasured → review` routing), but it is not the path that produces a headline.

---

## The six diligence-fatal gaps

Each gap below names: the anti-pattern, the exact code that exhibits it, why it inflates the number,
and the fix.

### 1. One model is pipeline **and** judge **and** baseline (self-grading)

**Code.** `model_route.from_env()` builds a *single* `ModelRoute` from one key. `wire(foundry, route)`
(`model_route.py`, the `wire` function) then assigns **that same route** to every measurement role:

- `foundry.measure` ← `measurement_stage(route)`, whose `RouteBareModel`, `RoutePipelineRunner`, and
  `RouteJudge` are **all** constructed from the one `route`;
- `foundry.gaps.prober` ← `RouteBareModel(route)` and `foundry.gaps.judge` ← `RouteJudge(route)`.

So the model that *answers bare*, the model that *answers with the pipeline*, and the model that
*grades both* are the same weights. `RouteJudge.score` (`model_route.py`) asks that model "score 0..1
how correct the candidate answer is."

**Why it inflates.** A model grading its own grounded output is the precise anti-pattern this repo
disclaims elsewhere — [[context-layer-and-the-desk]] ("measured paired, on the user's data, by a
**separate** evaluator — never self-graded") and [[context-enrichment-service]] ("scored by a SEPARATE
evaluator (never self-graded)"). Self-preference bias (an LLM rating its own/grounded completions
higher) is well documented; it systematically lifts `pipeline_score` and can depress the bare score the
same model produced "without trying." The delta is contaminated in the favourable direction.

**Fix.** Independent-judge requirement: the judge route must be a **different model family** (and
ideally a different vendor) from the pipeline/bare route. Make this a *gate precondition*, not an
option — a lift measured with `judge_model_family == pipeline_model_family` is stamped
`judge_independent: false` and is **not eligible for external quotation** (route to review, same as
`unmeasured`). Record `bare_model`, `pipeline_model`, and `judge_model` as distinct provenance fields
on the `lift` dict so the independence is auditable per row, not assumed.

### 2. Benchmark synthesis derives the answer from the component's own source, then injects that source as grounding (open-book vs closed-book)

**Code.** Real research-queue gaps carry *signals, not tasks* (the `data/research-queue` gaps have no
`eval_tasks`/`correct_answer` — confirmed empty), so the **synthesis path is the live path**, not an
edge case. `benchmark_synth.py` builds each `(prompt, correct_answer)` from the component's own
`_entries`/`rules` (`_source_facts`, `_entry_qa`: the `correct_answer` *is* `entry["text"]` /
`entry["fact"]`). Then `RoutePipelineRunner.run` calls `_grounding_text(candidate)` (`model_route.py`),
which serializes **those same `_entries`/`rules`** into the prompt as grounding.

The pipeline therefore answers **open-book** with the exact text the gold answer was extracted from,
while the bare model answers **closed-book**. The synth docstring's honesty claim ("a fact the model
already knows → delta ≈ 0") holds only for *parametric* facts; for any fact **not** already in the
model, the pipeline is handed the answer verbatim and the bare model is not. That is not a capability
measurement — it is a reading-comprehension / copy test, and it inflates **every** delta on exactly the
fresh/esoteric/long-tail facts we most want to admit.

**Why it inflates.** Open-book-vs-closed-book is the single largest confound in retrieval evaluation.
A delta produced this way conflates "the component supplies knowledge the model lacks" (real lift) with
"the prompt contained the answer" (trivial). The two are indistinguishable in the current numbers.

**Fix — contamination check + held-out construction:**

1. **Lexical-overlap contamination guard.** Before measuring, compute n-gram / token overlap between
   each `correct_answer` and the grounding text the pipeline will receive. If the answer is *verbatim
   present* in the grounding, the task tests copying, not lift — flag it `open_book_trivial` and exclude
   it from the headline delta (it can stay as a separate "extraction-fidelity" metric, which is what
   the Baltor fidelity check actually wants — see gap 3).
2. **Closed-book baseline parity.** The bare baseline must face the *same* question with *no* grounding
   (it already does) — but the **gold** must be derivable independently of the grounding the pipeline
   sees, e.g. answer drawn from a held-out portion of the source the pipeline is **not** given, or a
   reformulated question whose answer requires combining facts rather than echoing one. The synth must
   record `answer_in_grounding: bool` so the gate can separate lift from echo.
3. **Distinguish the two metrics explicitly.** "Did grounding let the model answer a question it
   couldn't?" (lift) is a different measurement from "did the compressed tier preserve the answer?"
   (fidelity). The current synth measures something between the two and labels it lift.

### 3. `verify.compression_fidelity` — the Baltor moat — has zero implementation

**Code.** [[context-enrichment-service]] names `verify.compression_fidelity` "the moat … the same
engine and the same moat as OHH's lift gate," scored by "a *separate* evaluator, never self-graded."
The only thing that exists is a **seed definition** — `scripts/seed/baltor_components.py` emits a
catalog component `("compression-fidelity-check", …, "verify.compression_fidelity", …)`. There is no
`scripts/.../verify/compression_fidelity.py`, no fidelity scorer, no published `fidelity_delta` on any
artifact. (`scripts/seed/baltor_components.py` `Status (honest)` already concedes this; this doc makes
the diligence consequence explicit.)

**Why it matters for diligence.** The measured-fidelity-per-tier guarantee is the *stated* differentiator
of the entire Baltor product ([[two-services-shared-infrastructure]]). An acquirer pricing the
enrichment wedge will ask to see one fidelity number on one tier. Today the answer is "it's a seeded
definition." Worse, gap 1 (self-grading) and gap 2 (open-book) would apply to it *by construction* the
moment it is implemented naively, because it would reuse the same single-route engine.

**Fix.** Implement `verify.compression_fidelity` as a *first-class* measurement that reuses the
hardened lift engine **after** gaps 1–2 are fixed: a separate-evaluator scorer comparing answers
derived from `raw` vs `compressed` vs `hyper-efficient` tiers on a fixed question set, publishing a
`fidelity_delta` per tier with a CI (gap 4) and an honest heuristic-vs-measured label (gap 5). Until
then, the doc and any pitch must say "fidelity guarantee: **planned**," not "the moat."

### 4. Measured lift uses ~6 tasks (n=6) with no variance, CI, or significance test

**Code.** `benchmark_synth._DEFAULT_MAX_TASKS = 6`. `measure.py` aggregates with a plain `_mean` over
the per-task scores and records `"n": len(tasks)` — and nothing else. There is no standard error, no
confidence interval, no significance test. The gate (`gate.py` `evaluate`) then promotes on
`delta > lift_floor` where the **default `lift_floor` is `0.0`** — i.e. *any* positive point estimate,
however noisy, clears the bar in the default configuration.

**Why it inflates.** A delta of "+0.31" computed from a mean of six scored items has a confidence
interval wide enough to plausibly include zero. Promoting on a point estimate at n=6 with floor 0.0 is
indistinguishable from promoting on noise. Token-F1 (`measure.py` `token_f1`) on short answers is also
high-variance per item. Reporting `delta` to four decimals (`round(delta, 4)`) implies a precision the
sample size does not support — itself a diligence red flag.

**Fix — minimum-n + interval + significance:**

- **Minimum n.** Set a `MIN_EVAL_TASKS` floor (single source, no magic literal — a named constant with
  rationale) below which lift is `unmeasured` (→ review), not promoted. Six is a development minimum,
  not a publication minimum.
- **Bootstrap CI on the paired delta.** Report `delta_ci_low` / `delta_ci_high` from a bootstrap over
  the per-task paired differences (`pipe_i − bare_i`), since the data are paired by task. For binary
  pass/fail verifiers, a **Wilson score interval** on the pass-rate difference is the standard, more
  honest small-sample interval than the normal approximation.
- **Promote on the interval, not the point.** The gate condition becomes `delta_ci_low > lift_floor`
  (the *lower* bound clears the floor) — "we are confident the lift is real," not "the average looked
  positive." A point estimate above the floor with a CI straddling it routes to review / more eval
  tasks, not promotion.
- **Keep the per-task scores** on the lift record so the interval is reproducible and auditable, not
  just the summary mean.

### 5. The only **published** "lift" artifact reports a metadata heuristic under the bare word "lift"

**Code.** `dist/reports/capability-lift-gate.json` (4,377 decisions) emits, for **every** component, a
field literally named `"lift"` — e.g. `"lift": 0.3` — whose value is the sum of metadata signals
(`description_substance`, `domain_specificity`, `eval_linked`, `permissive_license`, `provenance`,
`structural_depth`) from `scripts/factory/capability_lift_gate.py` `lift_score`. This is a **structural
quality heuristic over the manifest**, computed with **no model and no task** — it never measures
`pipeline_score − bare_model_score`.

The codebase is internally clear that these are two different things: `gate.py` reuses
`capability_lift_gate.lift_score` only as `heuristic_lift` (a *pre-filter signal*, explicitly "recorded;
NOT the decision"), while the *measured* `delta` is what promotes. But the **published file** drops the
`heuristic_` qualifier and ships the heuristic under the unqualified name `lift`.

**Why it inflates.** This is the most dangerous gap for diligence precisely because it is the one
artifact that is *published*. A reader who sees `"lift": 0.3` in `dist/reports/` and the measured-lift
thesis in the docs will reasonably (and wrongly) believe the 4,377 numbers are measured deltas. They
are metadata scores. Quoting "average lift across the catalog" from this file would be a
misrepresentation, even if unintentional.

**Fix — naming discipline (single source of truth for the word "lift"):**

- **Reserve `lift` / `delta` for the measured `pipeline_score − bare_model_score`.** Everything derived
  from manifest metadata is `heuristic_lift` or, better, renamed away from "lift" entirely
  (`structural_quality_score`) so the word cannot be confused. Rename the published field in
  `capability-lift-gate.json` accordingly.
- **Stamp `measurement_kind` on every lift-shaped number** (`measured` | `heuristic` | `synthetic`) and
  on the artifact that carries it, so no consumer ever sees a bare "lift" whose provenance is ambiguous.
- This is a direct application of [[no-magic-values]]: a value that means two different things in two
  places is a value that *will* be misread; give each meaning one unambiguous name.

### 6. SkillsBench / ClawsBench rest on future-dated, unverifiable arXiv IDs stated as fact

**Code/docs.** [[skillsbench-alignment]] cites, as plain fact, "papers arXiv:2602.12670 SkillsBench,
arXiv:2604.05172 ClawsBench," plus precise headline numbers ("+16.4pp average lift … 18 of those 84
tasks get worse … skills a model writes for itself net −1.3pp," "84 expert tasks," "94 public tasks").
The arXiv IDs decode to **Feb 2026** (`2602`) and **Apr 2026** (`2604`) submissions. They are presented
as a settled external benchmark our thesis is "validated" by.

**Why it matters for diligence.** External validation is only worth citing if it survives a click.
Stating an arXiv ID and a peer-reviewed headline number as fact — when the citation cannot be verified,
or the number cannot be reproduced from the cited source — is the kind of claim that, if a single ID
fails to resolve, **discredits every other number in the diligence pack**, including the ones that are
solid. The risk is asymmetric: the upside of the citation is a nice-to-have "third party agrees"; the
downside of one bad ID is loss of credibility across the whole eval story.

**Fix — citation provenance discipline:**

- **Verify before assert.** Every external citation that backs a claim carries a *checked* status: a
  resolvable URL/DOI and an access date, or it is labelled `unverified` / `claimed` and **not** used as
  load-bearing support. (The [[deep-research]] harness's adversarial-verification discipline is the
  model: a claim isn't a fact until a source is fetched and checked.)
- **Separate the durable argument from the contingent citation.** The SkillsBench *mapping* (lift =
  Δ pass-rate; durability = public→private generalisation; safety gate = governance) is a sound
  conceptual alignment that stands on its own reasoning. State *that* as our framework; cite the
  benchmark as *corroboration if/when verified*, never as the foundation. If the papers are real and
  resolve, attach the verified link and date; if not, the thesis does not depend on them.
- **No precise third-party numbers without a reproducible source.** Drop or hedge specific pp figures
  until they can be traced to a fetchable artifact.

---

## What is already honest (so diligence sees the contrast)

It is worth stating plainly what the engine gets *right*, because the gaps above are fixable precisely
because the scaffolding is disciplined:

- **No fabricated deltas, ever.** Offline with no recorded answers and no wired model, `measure.py`
  leaves `lift = None` and the gate routes to **review** (`unmeasured`), never inventing a number. A
  zero/negative measured delta **culls** ("no capability gain"). A `budget=0` cap yields `unmeasured`,
  not a fabricated lift. (All three are covered by the `measure.py` / `gate.py` self-tests.)
- **The two-axis gate is real.** Durability is sourced from the single enum in
  `scripts/eval/reason_codes.py`; `require_structural` mode routes transient lift to review.
- **Human-in-the-loop for self-certification risk.** LLM-probe-only gaps and knowledge components are
  stamped `pending_human` (`gate.py`) — the repo already encodes "the LLM doesn't know what it doesn't
  know."

The problem is not dishonesty in the offline path. The problem is that the **live, model-wired path** —
the only one that produces a headline `+lift` — silently violates qualifiers (independent judge,
closed-book, sufficient n, CI) that the offline path never had to confront, and the **one published
artifact** uses the word "lift" for something that isn't a measured delta.

---

## The rigor roadmap (ordered)

Fix in this order; each is a separate engine item (this doc only specifies the requirement):

1. **Naming first (gap 5)** — cheapest, highest credibility return. Reserve `lift`/`delta` for measured
   deltas; rename the published heuristic field; stamp `measurement_kind`. Pure renaming + one
   validate/CI drift check. Until this lands, **do not quote any catalog-wide "lift" figure.**
2. **Independent judge (gap 1)** — require `judge_model_family ≠ pipeline_model_family`; stamp
   `judge_independent`; make non-independent lift ineligible for external quotation.
3. **Open-book contamination guard (gap 2)** — lexical-overlap check; `answer_in_grounding` flag;
   separate lift from extraction-fidelity; held-out gold construction in the synth.
4. **Min-n + bootstrap/Wilson CI (gap 4)** — `MIN_EVAL_TASKS` floor; report
   `delta_ci_low`/`delta_ci_high`; promote on the lower bound, not the point estimate; keep per-task
   scores.
5. **Evaluator↔human calibration (cross-cutting)** — on a small labelled sample, measure judge↔human
   agreement (e.g. Cohen's κ / correlation) and publish it alongside any measured lift, so a reader
   knows how much to trust the automated judge. An uncalibrated judge is an unquantified error bar on
   *every* delta. This is the step that converts "the model said 0.83" into "the judge agrees with
   humans at κ=…, so 0.83 ± …".
6. **`verify.compression_fidelity` implementation (gap 3)** — build the Baltor moat *on top of* the
   hardened engine (1–4 done), with separate-evaluator scoring, a published `fidelity_delta` per tier,
   and a CI. Re-label the Baltor pitch "planned" until it ships.

## The single, enforceable rule this doc adds

> A `+lift` or `+fidelity` number may be quoted **externally** only if its `lift` record carries:
> `measurement_kind: measured`, `judge_independent: true`, `answer_in_grounding: false` (or an
> extraction-fidelity caveat), `n ≥ MIN_EVAL_TASKS`, a `delta_ci_low > lift_floor`, and a recorded
> judge↔human calibration. Anything missing one qualifier is a **development signal**, labelled as such,
> and stays internal.

Encode the rule as a validate/CI check on any artifact bound for `dist/` or a pitch, so the discipline
can't silently regress — the same drift-guard pattern [[no-magic-values]] mandates for every value that
must not be mistyped twice.

## Related

- [[north-stars]] · [[two-axis-lift-gate]] — the admission bar this methodology has to make defensible.
- [[capability-valleys]] — durability (the second axis) and `scripts/eval/reason_codes.py` as its single
  source.
- [[skillsbench-alignment]] — the external mapping (gap 6 applies to its citations).
- [[context-enrichment-service]] · [[two-services-shared-infrastructure]] — where the (currently
  unimplemented) compression-fidelity moat is claimed (gap 3).
- [[context-layer-and-the-desk]] — the "separate evaluator, never self-graded" principle gap 1 violates.
- [[no-magic-values]] — the naming/drift-guard discipline gaps 5 and the enforcement rule rest on.
- [[deep-research]] — the citation-verification discipline gap 6 adopts.
