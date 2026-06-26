# Inference-Time Capability Watch — two 2026 results vs. the lift+governance thesis

> **Purpose.** A skeptical, precise read of two results the owner flagged in 2026,
> mapped onto OpenHubForAI's two load-bearing axes: **capability lift over a
> bare model** ([master-goal.md](../codex/master-goal.md)) and **durable +
> governed** lift ([capability-valleys.md](../concepts/capability-valleys.md),
> [`scripts/eval/reason_codes.py`](../../scripts/eval/reason_codes.py)).
>
> **Stance.** Treat every number below as a *vendor/author claim* until an
> independent party reproduces it on a held-out set. Both results are reported as
> *training-free* ways to buy capability at inference time — which is exactly the
> kind of news that *could* be a threat ("you don't need our components, just run
> the model harder"). The finding of this watch is the opposite: each is most
> naturally a **new component family we host, measure, and govern**, not a
> substitute for the registry. The discipline that makes that true is our own —
> we admit neither on the strength of its press release; we admit each only after
> a *measured* lift on a *governed* task (the same bar SkillsBench publishes:
> [skillsbench-alignment.md](skillsbench-alignment.md)).

This is a watch document, not a roadmap commitment. It tells a future session how
to think about these two results and, if they hold up, how to ingest them as
components under the existing gates — without re-deriving strategy and without
swallowing the marketing.

---

## Why this is in `strategy/` and not `concepts/`

Both results sit on the **`weak_reasoning_at_scale`** lift-reason — the one our
own taxonomy labels **transient** (`reason_codes.py`: "A reasoning/format slip
scratchpads or larger models paper over"). A naive reading says: *transient =
discount = ignore.* That is the wrong lesson here, for a reason worth stating
once and carrying forward:

> A *technique* that cheaply harvests a transient gap is not itself a component
> with durable lift — but it can become a **substrate that other, durable
> components run on**, and the **governance around it** (whose support data?
> which base model? reproducible config? safety re-test?) is exactly the moat we
> already sell. We host the technique as an Action/harness; the *durability* lives
> in the corpus and the gates wrapped around it, not in the trick.

So the question for each result is not "is the trick durable?" (it is not — labs
will absorb both). The question is the two we always ask: **(1)** does it
*measurably lift* a base model on a real task, and **(2)** can we *govern* it
(provenance of inputs, reproducible config, safety re-test, decay watch) better
than a user running it raw? If yes to both, it is a **component**, and a
defensible one — because what we sell is never the trick, it is the *measured,
governed, composable* form of it.

---

## RESULT A — Hassana Labs, "closed-form controllers" (activation gates)

### (a) What it actually is, in plain terms

A claim about a **shortcut for fine-tuning**. Normally you adapt a model by
running SGD — compute a gradient on some support data and nudge the *weights*.
The claim has three linked parts:

1. **The math claim.** The *effect on the model's logits* of a single SGD step
   has a **closed-form dual** via the **neural tangent kernel (NTK)** — i.e. you
   can write down what one training step would do to the outputs without running
   the optimizer.
2. **The architecture claim.** That dual reduces to a **forward-pass elementwise
   multiply on activations** — a per-feature scale vector ("gate") applied during
   the normal forward pass. No weights change.
3. **The product claim.** You **fit such a gate on support data** (cheap), ship
   it as a tiny file, and **compose multiple gates by addition** — stack two
   skills without retraining and (they say) without the interference LoRA
   composition suffers.

In OHH terms: a **fitted, attachable activation-gate** that turns a *base* model
into a *task-specialized* one at load time, carried as a ~78 KB file instead of a
full fine-tune or a multi-MB LoRA adapter. It is an **adapter format**, adjacent
to LoRA but (claimed) cheaper to fit, smaller to ship, and additively composable.

### (b) The specific claims + numbers

All figures are **as reported by the lab**; none independently confirmed here.

| Claim | Reported number | What it would mean |
|---|---|---|
| Cost to fit one gate | **~$2 / ~15 min on one A100** | Adapter creation is near-free vs. RL/SFT runs |
| Artifact size | **78 KB per task** | Orders of magnitude under a LoRA adapter; trivially shippable/versionable |
| GSM8K (Qwen2.5-7B) | base **+ 78 KB → 84%** vs. Instruct **73%** (**+11 pp**) | Beats the *official instruct-tuned* model on grade-school math |
| BFCL (Qwen2.5-1.5B) | base **+ 78 KB → 61%** vs. Instruct **52%** (**+9 pp**; **+35 pp over base**) | Beats Instruct on tool/function-calling at 1.5B |
| Composition | two controllers, **gate cosine 0.017**, **+0.005 NLL drift** | Near-orthogonal gates; "stack without interference" |
| Composition baseline | **LoRA composition degrades ~17%** | The differentiator vs. the incumbent adapter |
| Availability | **code on GitHub** (link in owner's note); **paper "pending on arXiv"** | **Not yet peer-reviewed or archived** |

### (c) Why it matters to OHH

- **It touches our load-bearing comparison directly.** Our entire admission
  metric is `pipeline_score − bare_model_score`, and our reference external proof
  (SkillsBench/Skill Lift) is *with-skill minus without-skill*. Hassana's
  headline is **base + gate vs. Instruct** — a *different* and, for us,
  *better-framed* delta than "vs. base", because it asks whether the cheap
  artifact beats the **expensive** standard adaptation. That is precisely the
  comparison an acquirer cares about.
- **It is an adapter, and adapters are Actions.** Per project vocabulary, "a
  persona/tool/processor/harness/rubric is an Action," and **version lives in
  metadata, never in names/IDs**. A 78 KB gate fitted for a task is a textbook
  **Action**: attach to a base model, get a capability the base lacks. It slots
  into the catalog as an adapter component with a declared base model, declared
  support corpus, and a measured lift — no new primitive required.
- **Tiny + composable = our economics.** 78 KB artifacts that compose by addition
  are *cheap to store, cheap to version, cheap to CDC, and cheap to attach in a
  builder-assembled flow.* That is friendly to the "paste-a-task → costed,
  deployable flow" north star (P3) and to the daily factory (small artifacts,
  deterministic hashes).
- **It speaks to the small-model thesis.** Our product memory says push narrow
  tasks to cheap models behind deterministic harnesses. A **1.5B base beating its
  own Instruct on BFCL by +9 pp** for $2 is, *if true*, a direct subsidy to that
  thesis: small base + governed gate + our wrapper.

### (d) THREAT or COMPLEMENT?

**Mostly COMPLEMENT, with a bounded threat to one component family.**

- **The bounded threat.** If fitting a gate is genuinely $2/15-min/78 KB, then
  *certain* lifts we might have sold as a prompt/persona Action (format
  discipline, a reasoning nudge, a tool-calling style) can instead be bought as a
  gate by anyone with the support data. Those were **transient lifts on the
  `weak_reasoning_at_scale` / `missing_tool` codes anyway** — exactly the rows
  the two-axis gate already tells us *not* to lean on for defensibility. So the
  threat lands on the part of the catalog we already discount.
- **Why it is mainly a complement.** A gate is *an adapter, not a corpus and not
  a governance trail.* It does not supply: provenance of the support data,
  signed/verified domain facts, CDC for volatile facts, deterministic verifiers,
  review queues, or an accountable signer. Every **structural** lift reason in
  `reason_codes.py` (`volatile_fact`, `no_addressable_source`,
  `embodiment_required`, `closed_channel_access`, `accountability_or_license`,
  `deterministic_guarantee`, `tacit_local_knowledge`) is **untouched** by a
  cheaper fine-tune — you cannot fit a gate for "true today, wrong next quarter"
  or "needs a licensed human." The gate makes the *base model* better; it does
  nothing for the gaps that are not text-prediction problems. **It commoditizes
  the adapter layer and thereby raises the relative value of the corpus +
  governance layer — which is precisely the layer we said is the moat.**
- **Second-order complement (the real prize).** A cheap, *composable*, *tiny*
  adapter format is a gift to a **registry**. If gates compose by addition with
  ~zero interference, then "assemble a flow from existing components" can include
  "attach gates G1+G2+G3 to base M" — and the value migrates to *who has the
  measured, governed, non-interfering gate library and the assembler*, i.e. us.
  The cheaper and more composable adapters get, the more the bottleneck becomes
  curation, measurement, and trust — our thesis exactly.

### (e) How OHH incorporates it as a governed COMPONENT

**Component type:** a **"controller" / activation-gate Action** (an adapter
subtype of Action). One row = one fitted gate.

**Seven-primitive mapping** (canonical set per
[component-taxonomy-and-stages.md](../concepts/component-taxonomy-and-stages.md):
Input · Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output —
the conditional primitive, recently being renamed **If Statement → Conditional**
with **Logical Operator** split out as a distinct node subtype; both names refer
to the same primitive below):

- **Input** — the task input the gated model will run on.
- **Knowledge Corpus** — *the support data the gate was fitted on.* This is the
  governance crux (see below): a gate **is a lossy compression of its support
  set**, so the corpus's provenance/license is inherited by the artifact.
- **Action** — *attach the 78 KB gate to the declared base model* (the adapter);
  the forward-pass elementwise multiply is an implementation detail of this
  Action, not a new primitive.
- **Conditional** + **Logical Operator** — model-routing/admission logic: *use
  this gate only with its declared base model + revision*; refuse to attach to a
  different base; AND-compose only gates declared mutually non-interfering.
- **Output** — the gated model's response, carried forward to verification.
- **Loop** / **Stop-End** — optional fit-time loop and a stop on a quality/cost
  ceiling; at *inference* a single gate attach is loop-free.

**Reason-code mapping (be honest about durability).**

- The *technique's own* lift sits on **`weak_reasoning_at_scale`** →
  **`durability_class = transient`**. A gate that only raises GSM8K is a
  **decaying** asset — re-benchmark it against each new base model and set
  `decay_signal` accordingly (`none → watch → decaying` per `DECAY_SIGNALS`).
- A gate becomes **mixed/structural** *only* through what it is fitted on and
  wrapped with: a gate fitted on a **governed, hard-to-reach domain corpus**
  (e.g. a `sparse_data` / `coded_vocabulary` arena, retrievability tier ≥ 3)
  inherits that corpus's durability — the *adapter* is transient, but the *fitted
  artifact + its provenance + the verifier around it* can sit on `esoteric_rule`
  or a structural code. **Tag the gate by what it encodes, not by the method.**
- This is the same move as `skillsbench.py`: a technique is admitted only when it
  yields a *measured* lift on a task with a *verifier* — never on the method's
  reputation.

**The governance the gate does NOT bring (and we must add):**

1. **Provenance of the support data → the artifact inherits it.** A 78 KB gate is
   a *derivative of its support set*. Our provenance gate (supervisor #5) must
   bind `source_url + license + author` of the **support corpus** to the gate
   row, and a content hash of the support set to the gate's
   `component version definition` (ID/hash discipline in `CLAUDE.md`). A gate
   fitted on data we may not redistribute is **staging-only**, never promoted.
   *Risk to flag:* a tiny artifact can still **memorize/leak** support examples —
   treat a fitted gate as potentially carrying its training data for PII/secret
   review.
2. **Reproducibility.** Record base model + revision, support set hash, fit
   config (seed, the ~$2/15-min recipe), and the resulting gate hash, so the same
   inputs reproduce the same artifact and a *formatting* change never mints a
   false version (no-magic-values + hash discipline).
3. **Safety re-test (the ClawsBench analogue).** A gate that lifts GSM8K may also
   move refusal/safety behavior. Run the gated model through `foundry/gate.py`
   before promotion; an unsafe gate scores like an unsafe skill (−1.0) and is
   **not** promoted regardless of its task lift. *"Capability you can't get
   safely is worth less than nothing."*
4. **Composition is a governed claim, not a default.** "Gates compose by
   addition" must be **measured per pair**, not assumed. Store the measured
   `gate cosine` / NLL-drift for each composed pair as a first-class fact; only
   AND-compose (via the Logical Operator node) pairs whose measured interference
   is below a declared threshold. Do **not** import the lab's "~0.017 cosine /
   +0.005 NLL" as a global constant — it is one data point on two gates.

**Measurement contract (the only thing that admits it).** Through
`scripts/foundry/measure.py`: report **both** deltas —
`gated_base − bare_base` (does the gate do *anything*) **and**
`gated_base − instruct` (does it beat the expensive standard, the lab's
headline). Promotion uses the existing six supervisors; the lift floor
(supervisor #4) gates on a *measured, reproduced* delta on a *held-out* split,
never the reported one.

---

## RESULT B — "Reasoning with Sampling" (Karan & Du)

### (a) What it actually is, in plain terms

A **training-free decoding algorithm**. Instead of post-training a model with RL
to make it reason better, you change *how you sample* from the *already-trained
base model*. It is **MCMC-style iterative sampling** against a **sharpened**
version of the model's **own** output distribution — roughly, propose a
continuation, then iteratively resample/refine toward higher-likelihood (under
the model's own probabilities) reasoning, concentrating mass on the model's more
confident chains rather than taking one greedy or one temperature sample.

Crucially it uses **the base model's own likelihoods** — **no training, no
curated data, no external verifier, no reward model.** It is a smarter *search
over the model's own outputs*, run at inference time.

In OHH terms: a **deterministic-by-config inference-time wrapper / decoding
harness** that sits between the prompt and the model and changes the sampling
procedure. It wraps a model; it does not change one.

### (b) The specific claims + numbers

As reported by the authors; not independently confirmed here.

| Claim | Reported result |
|---|---|
| What it matches/beats | **RL post-training**, on **single-shot** eval |
| Benchmarks | **MATH500, HumanEval, GPQA** |
| Cost | **No training, no curated data, no verifier/reward model** |
| Bonus property | **Avoids RL's diversity collapse** (keeps output variety RL training narrows) |
| Mechanism | MCMC-style iterative sampling on the model's **own sharpened** likelihood |

The headline: *you can get much of RL post-training's reasoning gain by sampling
the base model more cleverly, for free, and keep diversity RL would have
crushed.* The unstated cost is **inference compute** — iterative/MCMC sampling
means **more forward passes per answer** than one greedy decode; "free" means *no
training run*, not *no extra inference cost*. **Flag that explicitly when
measuring** (see lift contract below).

### (c) Why it matters to OHH

- **It is a clean, ownable component shape.** A pure inference-time decoding
  wrapper that takes (model, prompt, config) → (better answer) is the *most
  hostable thing imaginable*: no weights, no fine-tune, no data dependency. It is
  a **harness** in our exact sense — an Action that wraps model I/O — and it is
  trivially **composable** with everything else (retrieval, verifiers, gates from
  Result A).
- **It improves the substrate every other component runs on.** If a base model
  reasons better *for free* under this sampler, then the *bare-model baseline
  rises* — which **raises the bar for every component's measured lift.** That is
  not bad news: it means our `pipeline_score − bare_model_score` deltas get
  *harder and therefore more credible*. A component that still lifts over a
  *better-sampled* base is more defensible, not less.
- **Diversity preservation is a feature we can sell.** RL's diversity collapse is
  a known failure (also flagged in our SkillsBench notes: skills a model writes
  for itself net **−1.3 pp**, 18/84 tasks get *worse*). A decoder that lifts
  reasoning *without* collapsing the output distribution is attractive for any
  pipeline that needs candidate diversity (ensembling, self-consistency, search).

### (d) THREAT or COMPLEMENT?

**Almost purely COMPLEMENT.** A faint, generic threat; a strong, specific
complement.

- **The faint threat.** It is one more thing that makes raw base models more
  capable for free, so the *general* "you don't need a pipeline" narrative gets a
  data point. But it raises only **reasoning on benchmark-shaped tasks** —
  MATH500/HumanEval/GPQA are exactly **condition-1/2 tasks** in our taxonomy
  (digitized text, verifiable ground truth, stationary target). It does nothing
  for any **structural** lift reason: better sampling cannot retrieve a
  `volatile_fact`, reach a `no_addressable_source`, satisfy a
  `deterministic_guarantee`, or supply an `accountability_or_license`. It sharpens
  the model's *own* distribution — so by construction it **cannot add information
  the base model never had.** Our negative-space valleys are defined precisely as
  where that information is *absent*.
- **The strong complement.** Because it is a free, model-agnostic, *training-free*
  wrapper, it is the ideal **default decoding layer** under our own components,
  and a **new harness family** in its own right. It is also a near-perfect
  **demonstration object** for the lift methodology: a wrapper that improves a
  base with zero data is the cleanest possible A/B (`bare sampling` vs. `wrapped
  sampling`), and it composes additively with Result A (gate the base, *then*
  sample it well) and with retrieval/verification (sample well, *then* check).

### (e) How OHH incorporates it as a governed COMPONENT

**Component type:** a **"reasoning-sampler" harness** — a deterministic
inference-time wrapper Action. One row = one decoding strategy with a pinned
config.

**Seven-primitive mapping:**

- **Input** — prompt/task.
- **Action** — the sampler harness wraps **model I/O** (the canonical "harness =
  Action" case): it is the decoding procedure around the model call.
- **Loop** — *first-class here.* MCMC/iterative resampling is literally a
  bounded **Loop** primitive (propose → score under own likelihood → refine),
  governed by an iteration/compute budget.
- **Conditional** + **Stop-End** — convergence / budget stop: halt on a
  likelihood-improvement threshold or a max-iterations / max-compute ceiling
  (the cost gate). This makes the wrapper **deterministic by config** — same
  model + same seed + same budget → same procedure.
- **Output** — the selected high-likelihood answer (optionally *with* its
  preserved candidate set, since diversity is retained).
- **Knowledge Corpus** — **not used by the sampler itself** (it adds no external
  facts). This absence is the whole point: it is why the wrapper is a *substrate*,
  not a substitute for grounded components.

**Reason-code mapping (honest durability).**

- The wrapper's lift sits squarely on **`weak_reasoning_at_scale`** →
  **`durability_class = transient`**. Better base sampling is the *definition* of
  a gap "larger models / better training paper over" — and unlike Result A it
  cannot be made structural by what it is fitted on, because **it is fitted on
  nothing.** It is a transient-by-construction technique.
- Therefore its registry value is **not** "a durable component" — it is **(1)** a
  free default that lifts the *baseline* (making other deltas more credible) and
  **(2)** a measured, reproducible *demonstration* of the lift methodology. We
  host it, measure it, and **watch its decay** (`decay_signal`) precisely because
  we expect labs to fold its gains into base decoding. Honest catalog hygiene:
  mark it transient, keep its benchmark traces governed (don't feed the flywheel
  per the `reason_codes` note on transient lifts), and do not claim it as a moat.

**The governance/engineering OHH adds:**

1. **Determinism + reproducibility.** Pin model + revision, seed, sharpening
   temperature, proposal/acceptance rule, iteration budget; record them as the
   component's config so "deterministic inference-time wrapper" is *true*, not
   aspirational, and the same config reproduces the same procedure (no-magic-
   values: every threshold is a named constant with a rationale).
2. **Honest cost accounting (the load-bearing caveat).** "No training" is **not**
   "no cost." MCMC/iterative sampling spends **extra forward passes per answer.**
   The lift contract must report **lift *per unit inference compute*** — a +X-pp
   gain that costs N× the forward passes is a *different* product than a free win,
   and the builder's cost estimator (P3/P4) must price it. Do **not** let "free"
   leak from the press framing into our cost model.
3. **Lift contract.** Via `foundry/measure.py`: `wrapped_sampling − bare_sampling`
   on the *same* base model, on a *held-out* split, **with the compute multiple
   recorded alongside the delta.** Independently reproduce before promotion;
   never import the authors' MATH500/HumanEval/GPQA numbers as our own.
4. **Safety re-test.** A decoder that concentrates probability mass can also
   sharpen *un*desired outputs. Run `foundry/gate.py`; a wrapper that improves
   MATH500 but degrades refusal behavior fails the safety gate (−1.0) and is not
   promoted.
5. **Composition stance.** Default-attachable under other components (sampler ∘
   retrieval ∘ verifier; sampler ∘ Result-A gate). Each composition's lift is its
   own measured fact, not an assumed sum.

---

## What needs INDEPENDENT VERIFICATION before either is admitted

Nothing here clears the lift floor on a press release. Concretely, before promotion:

### Result A (activation gates) — higher verification burden

1. **The paper is "pending on arXiv."** **No archived, citable, peer-reviewed
   source exists yet.** Until it does, Result A is an *unverified vendor claim
   plus a code drop* — admissible to the *watch list* and to *staging
   experiments*, **not** to a promoted component. (Provenance supervisor #5: an
   unresolved source question ⇒ review ticket, not promotion.)
2. **The math claim** — that one SGD step's logit effect has an NTK closed-form
   *and that it reduces to a forward-pass elementwise multiply* — is the load-
   bearing technical assertion and needs a real derivation reviewed, not a blog
   summary. NTK approximations are typically **first-order / lazy-regime** and can
   diverge from real multi-step fine-tuning; verify the regime of validity.
3. **The benchmark deltas** (84% vs 73% GSM8K; 61% vs 52% BFCL) must be
   **reproduced from the public code** on the stated bases, with **decontaminated**
   eval splits — GSM8K contamination is endemic; "+11 pp on GSM8K" is exactly the
   kind of number contamination inflates. Confirm the Instruct baseline is the
   standard checkpoint at standard settings (not a hobbled one).
4. **The composition claim** (cosine 0.017 / +0.005 NLL vs. LoRA ~−17%) is
   **n = one pair**. Re-measure across several gate pairs and several bases before
   treating "additively composable without interference" as a property.
5. **Support-data provenance + leakage** of any gate we would host: what was each
   reported gate fitted on, under what license, and **can a 78 KB artifact leak
   its support examples** (PII/secret review on the artifact itself, not just the
   recipe).
6. **Generality** beyond Qwen2.5 / GSM8K / BFCL: does it hold on other base
   families and on **non-benchmark-shaped, structural** tasks (where we predict it
   helps little)? That negative result is *useful* — it confirms the
   complement-not-threat read.

### Result B (reasoning-with-sampling)

1. **Reproduce `wrapped − bare`** on the stated benchmarks from the authors'
   method, on a held-out split, on at least one base outside their reported set.
2. **Quantify the inference-compute multiple** (forward passes / wall-clock /
   tokens per answer) — the missing denominator in "free." A gain is only a
   product if it is priced.
3. **Confirm the "matches/exceeds RL" claim is like-for-like**: same base, same
   eval protocol, **single-shot** as stated, and the RL baseline is a fair one.
4. **Confirm diversity preservation** with an actual diversity metric, not an
   anecdote — it is a real selling point only if measured.
5. **Peer-review / archival status** of the paper (named authors Karan & Du;
   verify the arXiv/venue record and that the public method matches the claims).

> **Decay watch (both).** Both lifts are on the **transient** code. Schedule a
> re-benchmark against each new base-model release and set `decay_signal`
> accordingly. The day a base model ships these gains natively, the *technique's*
> lift goes to zero — and our value, correctly, will have already moved to the
> **governed corpus, the measured composition library, the safety gate, and the
> assembler**, none of which a better base model provides.

---

## Bottom line

| | Result A — activation gates | Result B — reasoning-sampler |
|---|---|---|
| **What it is** | Cheap, tiny, composable fine-tune *adapter* (claimed NTK dual → activation multiply) | Training-free *decoding wrapper* (MCMC on the model's own sharpened likelihood) |
| **Our component** | A "controller" **Action** (adapter subtype) | A "reasoning-sampler" **harness** (Action wrapping model I/O) |
| **Key primitives** | Action + Knowledge Corpus (support data) + Conditional/Logical-Operator (base-model + compose gating) | Action + **Loop** + Conditional/Stop-End (budget) |
| **Durability code** | `weak_reasoning_at_scale` → **transient**; can inherit **structural** durability *only* from the governed corpus it is fitted on | `weak_reasoning_at_scale` → **transient by construction** (fitted on nothing) |
| **Threat / complement** | Bounded threat to the *transient adapter* layer; **complement** — commoditizes adapters, raises the value of corpus + governance | **Complement**; faint generic threat; raises the *baseline*, making our deltas more credible |
| **Governance we add** | Support-data provenance→artifact, reproducible fit, **per-pair** composition measurement, safety re-test, leakage review | Pinned deterministic config, **cost-per-compute** accounting, reproduce vs. bare, safety re-test |
| **Verify first** | **arXiv pending — not citable**; NTK regime; decontaminated reproduction; composition n>1; license/leakage | Reproduce `wrapped−bare`; **price the compute multiple**; like-for-like vs RL; diversity metric; archival status |

**The through-line.** Both results make *base models* cheaper to improve at
inference time. Under the lift+governance thesis that is **not** an erosion of the
moat — it is a *shift of value toward the moat*. The trick gets commoditized; the
**measured lift, the governed support corpus, the safety gate, the
non-interference composition facts, and the assembler that wires them into a
costed, deployable flow** do not. We admit each as a component the same way we
admit everything else: a *reproduced* delta over the *right* baseline, a clean
provenance + safety trail, and a `decay_signal` that says out loud we expect the
technique itself to fade. That honesty *is* the product.

---

*See also:* [master-goal.md](../codex/master-goal.md) ·
[capability-valleys.md](../concepts/capability-valleys.md) ·
[`scripts/eval/reason_codes.py`](../../scripts/eval/reason_codes.py) ·
[skillsbench-alignment.md](skillsbench-alignment.md) ·
[component-taxonomy-and-stages.md](../concepts/component-taxonomy-and-stages.md)
