# P2 — Measured-Lift Promotion Bridge

Status: **bridge module landed + verified** (the callable). Wire-in to the two
gates is **documented, not applied** this pass (collision avoidance — see below).

Closes the named gap in `docs/architecture/capability-rubric-and-deep-dive-2026-06-11.md`:
the **P2** item "measured-lift promotion for registry components" and **step 3** of
the backbone program ("tie `scripts/eval/measured_lift_headtohead.py` … into
promotion as the Stage-2 confirm").

## The gap this closes

The repo had **two promotion notions that never touched**:

| | gate | axis | weakness |
|---|---|---|---|
| (a) | Teleon runtime — `scripts/teleon_local_runtime.py` (`_run_to_completion`) | train+holdout pass-rate ≥ `PROMOTE_AT` (0.90) | proves a capability does its job on **its own suite**; **no lift axis, no durability axis** — a capability can clear it while adding nothing a bare model couldn't do, or while its edge is one model generation from evaporating |
| (b) | Measured lift — `scripts/eval/measured_lift_headtohead.py` (`run_headtohead`) | paired / held-out / **separate judge** (raises on self-grading), paired with a `durability_class` | implements the **real** two-axis discipline but **writes promotion nowhere** — produces the number and stops |

The capability-gap framework (`docs/concepts/capability-valleys.md`,
`scripts/eval/reason_codes.py`, `scripts/eval/durable_gap_harness.py`) defines the
admission rule: a component must **LIFT** (`pipeline_score − bare_model_score > 0`)
**AND** that lift must be **structurally durable** (won't close when the next model
ships). Nothing connected the measured number to a promote/cull. **`scripts/eval/promotion_bridge.py` is that wire.**

## The bridge contract

`promotion_decision(measured_lift_result, gate_evidence, *, policy) -> verdict`

- **Pure & deterministic.** No IO, clock, RNG, model, or network. Same inputs →
  byte-identical output (proven; re-run equality is a self-test check).
- **Input — accepts BOTH real result shapes** (normalized to one record):
  1. the rich `run_headtohead` output (`lift`, `durability_class`, `n`,
     `measurement_kind`, `evaluator_independent`, `publish_blockers`, …);
  2. the leaner `scripts.foundry.measure` candidate-`lift` dict (`delta`,
     `durability_class`, `n`, …).
- **`gate_evidence`** (optional) — the **Promotion Boundary** blockers from
  `CLAUDE.md`: `open_review_tickets`, `high_risk_review_required`,
  `placeholder_embeddings`, `unresolved_source`, `unresolved_signature`,
  `volatile_without_cdc` (+ a free `blockers: [...]` list). The bridge does **not**
  re-derive these — it **accepts** them and treats any present one as
  review-forcing.
- **Output — a lossless verdict dict** (never a bare verdict): `decision`
  (`promote`|`candidate`|`reject`), `basis` (machine token for the deciding rule),
  `lift`, `durability_class`, `lift_reason`, `lift_is_positive`, `durability_ok`,
  `n`, `evaluator_independent`, `requires_review`, **`reasons[]`** (the full ordered
  reasoning chain), `gate_blockers`, `source_publish_blockers` (the head-to-head
  seams carried up), `policy` (the thresholds used), and `normalized` (lineage).

### Decision vocabulary (this module's own — kept distinct on purpose)

`promote | candidate | reject` — deliberately **not** the same words as the other
two gates so a reader always knows which gate spoke:
`teleon_local_runtime` = `promoted|candidate|rolled-back`;
`candidate_promotion_scorer` = `promote_candidate|review_before_promotion|hold|reject`.

## How it enforces lift + durability (the decision ladder)

In order; the first matching rule decides, and **every** factor is recorded in
`reasons[]` even when it isn't the decider:

0. **`evaluator_independent` is not `True`** → **reject** (`self_graded`).
   Fail-closed: a self-graded or independence-unproven number can never gate a
   promotion. (The head-to-head *raises* on self-grading, so a well-formed result
   is always independent; a hand-assembled/legacy result that omits the flag is
   refused.)
1. **unmeasured** (`measurement_kind=='unmeasured'` or no delta) → **reject**
   (`unmeasured`) + review. No number ⇒ no lift claim; never a silent pass.
2. **lift not strictly positive** (`≤ min_promote_lift`) → **reject** (`no_lift`).
   Zero/negative delta = the pipeline added no measured capability.
3. **`durability_class == "transient"`** → **candidate** (`transient_durability`).
   Real lift today, but it closes with the next model — not a durable promote.
4. **durability `unknown`** (positive lift, no `lift_reason`) → **candidate**
   (`durability_unclassified`) + review. Can't assert durable without a reason
   (mirrors `durable_gap_harness`'s `review` for untagged gaps).
5. **promotion-boundary blocker present** in `gate_evidence` → **candidate**
   (`review_blocked`) + review. Caps a would-be promote.
6. **thin paired `n`** (`< min_promote_n`) → **candidate** (`thin_n`) + review.
   Real & durable but too few held-out items to promote.
7. otherwise → **promote** (`positive_lift_durable`): positive measured lift +
   non-transient durability + sufficient `n` + no boundary blocker +
   evaluator-independent. Uncleared *publication* seams (e.g. no CI) ride along as
   an **advisory**, never dropped (lossless), but do not block a *registry*
   promote.

## Single-source / no-magic-values

- The durability vocabulary + classifier are **imported** from
  `scripts.eval.reason_codes` (`DURABILITY_CLASSES`, `LIFT_REASONS`,
  `durability_class`) — **never re-defined**. A self-test check asserts object
  identity (not a copy); `grep` confirms no local `def durability_class` / enum
  assignment.
- `NON_TRANSIENT_DURABILITY_CLASSES` (the classes that satisfy a promote) is
  **computed** as `DURABILITY_CLASSES − {transient}` — `{structural, mixed}` today,
  but it follows a taxonomy change automatically; never hand-typed.
- The only literals this module owns are its **own** thresholds, each a named
  constant with a unit/rationale and **echoed in every verdict's `policy`**:
  `DEFAULT_MIN_PROMOTE_LIFT = 1e-6` (positive-lift floor vs float noise),
  `DEFAULT_MIN_PROMOTE_N = 2` (paired-item promote floor — a dev floor; the
  publication n-floor stays the harness's seam), `TREAT_UNMEASURED_AS = reject`.
- `PromotionPolicy` is frozen and validates at construction: refuses a non-positive
  `min_promote_lift` and refuses any policy that lets `transient` durability
  promote.

## Wire-in points (ONE line each — documented, not applied this pass)

Not wired this pass to avoid edit collisions on the two service files; both are
one-line, flag-guarded changes. Full snippets live in the module's `WIRE-IN`
section.

- **(A) Teleon runtime gate** — `scripts/teleon_local_runtime.py`, in
  `Runtime._run_to_completion`, immediately **after** the existing pass-rate
  `decision = (...)` line. Call `promotion_decision(measured_lift_result, …)` and
  downgrade `promoted → candidate` when the lift gate disagrees; attach the verdict
  to the run receipt. (Needs a lift suite per capability gap via `run_headtohead`;
  the runtime has none today — that's the larger task. The bridge is ready now.)
- **(B) Registry submit/review path** — `scripts/registry_local_service.py`, in
  `RegistryStore.decide`, immediately **before** recording an `approve` (the only
  candidate→public-active path, which today consults **no** lift evidence). Gate the
  approve on `promotion_decision(entry["measured_lift"], …)`; block/downgrade +
  surface `reasons` when it isn't `promote`. Makes "discovery ≠ trust" enforced by a
  **measured number**, not only reviewer judgement. Behind a registry flag.

## Tests (PASS)

```
python3 -m py_compile scripts/eval/promotion_bridge.py            # OK
python3 -m scripts.eval.promotion_bridge --self-test             # 35 ok / 0 FAIL (run 3×, identical)
```

PASS line:

> PASS — promotion_bridge: measured lift gates promotion. REAL run_headtohead
> fixture → promote (lift +0.541, durability structural); transient durability
> blocks promote→candidate; no/negative/zero lift→reject; self-graded (or
> independence-unproven)→reject; unmeasured→reject; promotion-boundary blocker
> (open review ticket / placeholder embeddings)→candidate+review; thin
> n→candidate; thresholds from named constants + the promote-durability set
> COMPUTED from reason_codes (taxonomy never re-defined); deterministic re-run
> identical.

The load-bearing check feeds the **actual** `run_headtohead` fixture output into
the bridge (not a hand-faked shape) and a **real** `scripts.foundry.measure` lift
dict for cross-surface compatibility. Upstream self-tests re-run green (unbroken):
`measured_lift_headtohead`, `reason_codes`, `durable_gap_harness`,
`foundry.measure`.

`--explain` (gate as a shell pipeline; exit 0 promote/candidate, 1 reject):

```
python3 -m scripts.eval.promotion_bridge --explain lift.json [--evidence gate.json]
```

## Critique — is this the right gate? What's missing to be THE admission criterion?

This is the **correct deterministic shape** for the gate, and it makes the two
axes (lift + durability) enforceable for the first time. But it is the *disposition*
layer; several things must land before it is the **real** admission criterion, not
a well-formed stub:

1. **No producer is wired yet.** The bridge consumes a measured-lift result, but
   neither the Teleon runtime nor the registry currently **produces** one per
   capability/component. The gate is real; its **input is not yet generated in
   production**. Highest-value next step: a `run_headtohead` lift suite per Teleon
   capability gap (wire-in A's prerequisite) and a `measured_lift` field on
   registry submissions (wire-in B's prerequisite).
2. **The durability class is asserted, not earned.** `durability_class` comes from a
   `lift_reason` a human/upstream tags. The bridge faithfully refuses to promote an
   `unknown` class, but it cannot *detect* a mis-tag (a "structural" label on a
   transient gap promotes). The real criterion needs the **decay signal** loop from
   `reason_codes` (`DECAY_SIGNALS`: re-benchmark each new base model; demote on
   `decaying`) — currently out of scope here and unbuilt.
3. **Object-level ≠ model-level judge independence.** The bridge enforces the
   head-to-head's *object* separation (judge isn't an answer arm) and fail-closes
   when unproven. It does **not** verify the **model-level** independence
   (`judge_model_family != answer_model_family`) — that's the harness's seam,
   carried as a `source_publish_blocker`, not enforced. A promote here is
   *registry-promotable*, **not** a publishable headline number until that seam +
   the CI/n-floor land.
4. **No confidence interval.** Promotion turns on a point estimate of the lift. The
   honest bar (`measured-lift-head-to-head.md` §6) promotes on a **CI lower bound**;
   the bridge promotes on the mean and carries `no_confidence_interval` as an
   advisory. A thin-but-positive lift can promote (subject to `min_promote_n`) that a
   CI would not. Tightening: gate on the harness's per-item paired scores → a
   bootstrap lower bound, once computed.
5. **`min_promote_n = 2` is a development floor.** It lets the gate run on a tiny
   fixture; it is far below any publication n. An outward-facing surface should pass
   a tighter `PromotionPolicy` (and the verdict records it) — but nothing yet
   *forces* the stricter policy on the outward path.
6. **`gate_evidence` is trusted, not validated.** The bridge believes the caller's
   `open_review_tickets: false`. The registry/runtime must supply truthful evidence;
   a lying caller can clear the boundary. The boundary is only as honest as its feed.

Net: the gate is the right deterministic disposition and is honest about its own
seams (it carries them, never hides them). It becomes **the** admission criterion
when (1) a real lift result is produced per component, (3)+(4) the model-level
independence + CI seams close, and (2) the decay loop demotes mis-tagged
durability. Until then it is a correct, ready gate waiting on its producers.
