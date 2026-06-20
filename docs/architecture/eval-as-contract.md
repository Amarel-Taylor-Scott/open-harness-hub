# eval-as-contract — the benchmark IS the spec (eval_suite as a first-class contract field)

**Date:** 2026-06-11. **Status:** BUILT (inline suites end-to-end real; named-suite registry is the documented
follow-up). **Warrant:** synthesis gap #2 / vision gap **D-2** in
`docs/strategy/teleon-self-improving-runtime-vision.md` — *"There is no `eval_suite` / `benchmark_ref` /
acceptance_criteria field on `PurposeTaskSpec.v1` / `CapabilityTask.v1.schema.json`. Until that exists, a user
cannot actually 'hand it the evaluation system' — they get a fixed capability set."* This change closes that
gap: the **evaluation system that defines DONE is now a declared, validated input on the contract**, not a
suite hardcoded in the runtime.

## What changed

`eval_suite` (a.k.a. the benchmark) is now an **optional but, when present, fully-constrained** field of both
contracts:

- `schemas/purpose_tasks/PurposeTaskSpec.v1.schema.json`
- `schemas/workers/CapabilityTask.v1.schema.json`

A user hands Teleon the benchmark in one of two ways (**exactly one** — XOR):

```jsonc
// (A) INLINE suite — the same {input, expected, weight?} rows the live runtime already executes + scores
"eval_suite": {
  "suite_id": "suite.dates@v1#h7a2",
  "examples": [
    {"input": "Filed 3/14/2026.", "expected": "Filed 2026-03-14."},
    {"input": "No dates here.",   "expected": "No dates here."}
  ],
  "judge": "deterministic"           // optional; default deterministic (exact match)
  // gate_threshold / holdout_policy / gate_basis are FILLED at normalization (see below)
}

// (B) NAMED registry suite — a reference resolved against a real suite registry
"eval_suite": { "suite_id": "suite.legal@v3#h9c1", "benchmark_ref": "registry://acme/legal-cites@v3" }
```

Shape (all keys validated): `suite_id` (required), `examples[]` **XOR** `benchmark_ref`, optional
`gate_threshold` (0–1), `holdout_policy`, `gate_basis`, `judge` (`deterministic | local_model |
frontier_judge | human` — the **same vocabulary** as `schemas/benchmark.schema.json`), and the
normalization-stamped `source` / `example_count`. A model-built capability's **inline** suite must carry
≥1 example (a model can never be gated on an empty suite — that would read as a cleared gate with nothing
measured); a `benchmark_ref` is allowed for a model-built capability because the registry carries the rows.

`PurposeTaskSpec.v1` also gained `build_mode` (`auto | model | deterministic`, mirroring the runtime's run
mode) and `model_built` (boolean) so a task can **declare** it is model-built — which is what makes the
non-empty-examples rule fire. Both are optional and backward compatible.

## The code

- `src/teleon/purpose_tasks/eval_suite.py` — the validated field + helpers (pure, deterministic, no I/O):
  - `validate_eval_suite(suite, *, model_built=False) -> list[str]` — XOR, non-empty-for-model-built, per-row
    `input`/`expected`, weight ≥ 0, threshold range, judge enum.
  - `normalize_eval_suite(suite, *, model_built=False) -> dict` — validates, **fills defaults** (see
    single-sourcing below), stamps `gate_basis`/`source`/`example_count`, normalizes weights. **Lossless**:
    extra fields the caller supplied survive. Fails **closed** (raises `ValueError`) on an invalid suite.
  - `eval_pairs(normalized) -> [(input, expected), ...]` — projects an inline suite to the runtime's
    executable shape (exactly what `_suite` iterates).
  - `resolve_benchmark_ref(ref, registry=None) -> dict` — resolves a named ref, or raises
    `BenchmarkNotRegisteredError` (see honesty below).
- `src/teleon/purpose_tasks/purpose_task.py`:
  - `PurposeTaskSpec` — a thin builder that wraps the spec **dict** (the spec stays a plain dict for
    `provision`/`run`/`adapt`; this never replaces it): `from_dict`/`to_dict` (lossless round-trip),
    `with_eval_suite(suite, *, model_built=None, normalize=True)`, `eval_suite` / `normalized_eval_suite()`.
  - `eval_suite_for(spec) -> dict | None` — **the seam**: the normalized, gate-ready suite for a spec, or
    `None` when the task declares no benchmark (backward compatible).
- `src/teleon/purpose_tasks/projections.py` — the customer view summarizes the eval_suite
  (`eval_contract`: id, example count, threshold, holdout policy, judge) but **never** an example's `expected`
  (the answer key is staff-only — deny-by-default, same class as prompts/candidate code).
- Re-exported through `src/baltor/purpose_tasks/*` shims (lossless Baltor→Teleon seam; Teleon never imports
  Baltor — `scripts/check_portfolio_dependency_law.py` stays green).

## How the runtime gate consumes it (the wire-in)

Today the live gate (`scripts/teleon_local_runtime.py`) iterates a **hardcoded** per-capability suite:
`CAPABILITIES[cap_id]["examples"]` in `Runtime._suite`, splits it by index parity (`_example_split`), and
promotes when **both** the train and holdout pass-rates clear `PROMOTE_AT`.

The documented wire-in (the seam is built; flipping the runtime to read it is the follow-up, and that file is
owned by other work) is a **one-line source swap** in `_run_to_completion` / `_suite`:

```python
# instead of: examples = CAPABILITIES[cap_id]["examples"]
from src.teleon.purpose_tasks import eval_suite_for
from src.teleon.purpose_tasks.eval_suite import eval_pairs
suite = eval_suite_for(spec)                 # spec = the PurposeTask/CapabilityTask for this capability
examples = eval_pairs(suite) if suite else CAPABILITIES[cap_id]["examples"]   # declared benchmark, else fallback
threshold = suite["gate_threshold"] if suite else PROMOTE_AT                  # declared gate, else the default
```

`eval_pairs` returns exactly `[(input, expected), ...]`, so `_suite` is unchanged downstream — same receipts,
same train/holdout split, same deterministic judge. `gate_threshold` defaults to `PROMOTE_AT`, so a suite that
doesn't override it gates **identically** to today. A `benchmark_ref` suite must be resolved first
(`resolve_benchmark_ref`) — until a registry is wired, an inline `examples` suite is the fully-working path.

## How the compiler consumes it

`src/teleon/compiler/` compiles only **promoted** capabilities ("Run the eval gate to promotion first, then
compile"). The eval_suite is the **declared acceptance contract** the gate uses to reach that promoted state;
the compiler reads it (via `eval_suite_for`) for two things: (1) refusing to compile a model-built capability
whose declared suite never cleared its `gate_threshold`, and (2) emitting the OTel `eval_suite` /
`success_criteria.passed` attributes the CTS spec already names
(`docs/standards/open-capability-task-specification.md`). The compiler never bypasses the suite — agents
PROPOSE, the gate (scored against the declared benchmark) DISPOSES.

## Single-sourced thresholds (no-magic-values)

The gate threshold and holdout policy are **not typed** in the new code. They are read from the **one canonical
source** — the live runtime's promotion constants — so the contract default can never drift from the gate that
actually runs:

| normalized field | canonical source (`scripts.teleon_local_runtime`) |
|---|---|
| `gate_threshold` default | `PROMOTE_AT` (read via `default_gate_threshold()`) |
| `holdout_policy` default  | **derived** from `TRAIN_PARITY` + the split labels (`default_holdout_policy()` → e.g. `index_parity:even=train,odd=holdout`) |
| `gate_basis` stamp        | `GATE_BASIS` (`gate_basis()`) — both splits must clear |

The import is **lazy** (inside the accessor) so importing the eval_suite module stays cheap and never starts a
server. `scripts/` is tooling, not a brand layer, so this `src/teleon` → `scripts` read does **not** violate
the portfolio dependency law (proof-confirmed).

## Honest by construction (no fabricated evidence)

`resolve_benchmark_ref` for an unregistered name raises **`BenchmarkNotRegisteredError`** — it **never**
returns a placeholder/fabricated suite. A `benchmark_ref` is a promise to be resolved against a real registry,
not a stand-in for one; fabricating a suite would fabricate the very evidence the gate exists to check. The
error names the known suites and tells the caller to register the suite or hand an inline `examples` suite.

## What is real vs the follow-up

**Real now (proven by `scripts/check_eval_suite_contract.py --self-test`, 38 checks):** the field on both
schemas (valid Draft-2020-12; backward compatible with/without the field; malformed suites rejected); the
`PurposeTaskSpec` round-trip; `eval_suite_for` / `eval_pairs` (the runtime-gate seam); single-sourced
threshold/holdout/basis; the honest `benchmark_ref` resolver; XOR + fail-closed validation; and the
customer-view redaction (answer key never leaks). The inline-suite path is end-to-end usable today.

**Follow-up (named, not faked):**
1. **The registry-of-named-suites.** `resolve_benchmark_ref` is the real, honest seam (hand it a registry and
   it resolves; hand it nothing and it raises). A persistent suite registry (likely keyed off
   `schemas/benchmarks/BenchmarkArtifact.v1` / `BenchmarkResult.v1` and the `benchmark.schema.json` manifest)
   is the next increment so `benchmark_ref` resolves from a store, not just an in-memory dict.
2. **Flipping the live runtime gate** (`scripts/teleon_local_runtime.py`, other-owned) to read
   `eval_suite_for(spec)` instead of `CAPABILITIES[...]["examples"]` per the one-line swap above — the seam is
   built and proven; the swap is mechanical.
3. **Wiring the Stage-2 confirm scorer** (`scripts/eval/measured_lift_headtohead.py`) to the declared
   `judge`/threshold so paired/held-out/separate-judge lift is gated by the same declared benchmark (vision
   gap D-2 / Stage 2 convergence).

## Adaptation-ladder alignment

`eval_suite.remove` is already a **`forbidden_autonomous`** change in
`architecture/capability_adaptation_ladder.json` — a task may never autonomously drop its benchmark. Making the
eval_suite a first-class declared field is what gives that ladder rule a concrete artifact to protect.
