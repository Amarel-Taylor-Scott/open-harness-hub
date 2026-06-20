"""src.teleon.purpose_tasks.eval_suite — the EVAL/BENCHMARK as a first-class PurposeTask contract field.

"The benchmark IS the spec": a user hands Teleon the *evaluation system* that defines DONE, not a fixed
capability. This module is the structured, validated `eval_suite` field that closes vision gap D-2
(`docs/strategy/teleon-self-improving-runtime-vision.md`): the declared input the runtime gate + compiler
consume to decide promotion.

An `eval_suite` is EITHER an INLINE example suite (the same shape the live runtime already executes —
`{input, expected, weight?}` rows the deterministic judge scores by exact match, split train/holdout) OR a
`benchmark_ref` to a NAMED registry suite. Exactly one of the two (XOR). It also carries the gate threshold,
the holdout policy, and the judge kind.

No-magic-values: the gate-threshold default and the holdout policy are NOT typed here — they are read from
the ONE canonical source, the live runtime's promotion constants (`scripts.teleon_local_runtime.PROMOTE_AT`
/ `TRAIN_PARITY` / `GATE_BASIS`), so the contract default can never drift from the gate that actually runs.
The import is LAZY (inside the accessor) so importing this module stays cheap and never starts a server.

Honest: `resolve_benchmark_ref` for an unregistered name raises `BenchmarkNotRegisteredError` — it NEVER
fabricates a suite. A `benchmark_ref` is a promise to be resolved against a real registry, not a stand-in for
one. The registry-of-named-suites itself is the documented follow-up (see docs/architecture/eval-as-contract.md);
until a registry is supplied, an inline `examples` suite is the fully-working path.

Lossless: normalization fills DEFAULTS and returns a NEW dict; it never drops a provided field (weights,
extra judge config, a held-out policy override survive round-trip). Pure + deterministic (no I/O, no clock).
"""
from __future__ import annotations

from typing import Any

#: Where the canonical gate constants live (single source of truth — read, never re-typed). Surfaced as a
#: string so error messages / docs can point a reader at the authority without importing it.
EVAL_GATE_SOURCE = "scripts.teleon_local_runtime"

#: Judge kinds — single definition, kept identical to schemas/benchmark.schema.json `judge` enum so the
#: PurposeTask eval_suite judge and the benchmark-manifest judge are the same vocabulary (no parallel list).
JUDGE_KINDS = ("deterministic", "local_model", "frontier_judge", "human")
DEFAULT_JUDGE = "deterministic"  # the runtime's live judge is exact-match deterministic; evidence judges

#: The two carriers of "what DONE means" — an inline suite XOR a named-registry reference. Exactly one.
EVAL_SOURCE_KEYS = ("examples", "benchmark_ref")


class BenchmarkNotRegisteredError(LookupError):
    """A `benchmark_ref` named a suite that is not in the supplied registry. Raised HONESTLY — the resolver
    never invents a suite to fill the gap (that would fabricate the very evidence the gate exists to check)."""

    def __init__(self, ref: str, known: tuple[str, ...] = ()) -> None:
        known_s = ", ".join(sorted(known)) if known else "<none registered>"
        super().__init__(
            f"benchmark_ref {ref!r} is not registered (known suites: {known_s}). "
            "Register the named suite or hand an inline `examples` suite — a benchmark_ref is never "
            "resolved to a fabricated suite.")
        self.ref = ref
        self.known = tuple(known)


def default_gate_threshold() -> float:
    """The default promotion gate threshold, read from the ONE canonical source (the live runtime's
    PROMOTE_AT) — never typed here, so the contract default tracks the gate that actually runs. Lazy import:
    keeps this module cheap to import and free of the runtime's server-side dependencies."""
    from scripts.teleon_local_runtime import PROMOTE_AT  # canonical gate threshold (no-magic-values)
    return float(PROMOTE_AT)


def default_holdout_policy() -> str:
    """The default holdout policy, DERIVED from the runtime's canonical split constants (TRAIN_PARITY +
    the split labels) rather than re-typed — so it can never disagree with how `_example_split` actually
    splits the suite. Returns a stable, parseable policy id, e.g. 'index_parity:even=train,odd=holdout'."""
    from scripts.teleon_local_runtime import TRAIN_PARITY, TRAIN_SPLIT, HOLDOUT_SPLIT  # canonical split
    train_side, holdout_side = ("even", "odd") if TRAIN_PARITY == 0 else ("odd", "even")
    return f"index_parity:{train_side}={TRAIN_SPLIT},{holdout_side}={HOLDOUT_SPLIT}"


def gate_basis() -> str:
    """The basis the runtime gate evaluates the threshold over (e.g. 'train+holdout'). Canonical source:
    the live runtime's GATE_BASIS. Carried onto a normalized suite so a reader knows BOTH splits must clear."""
    from scripts.teleon_local_runtime import GATE_BASIS  # canonical gate basis (no-magic-values)
    return str(GATE_BASIS)


def _is_ref(suite: dict[str, Any]) -> bool:
    return bool(str(suite.get("benchmark_ref", "")).strip())


def validate_eval_suite(suite: Any, *, model_built: bool = False) -> list[str]:
    """Return a list of human-readable errors for an eval_suite (empty list == valid). Enforces the rules the
    JSON-Schema layer can't express portably:

      * the suite is an object with a non-empty `suite_id`;
      * EXACTLY ONE of `examples` / `benchmark_ref` is present (XOR — never both, never neither);
      * for a MODEL-BUILT capability an INLINE suite must have ≥1 example (a model can't be gated on an empty
        suite — that would read as 'cleared' with nothing measured); a benchmark_ref is allowed (the registry
        carries the examples);
      * every inline example is an object with an `input` and an `expected` (the answer key the judge scores
        against); an optional `weight` is a non-negative number;
      * `gate_threshold`, if present, is a number in [0, 1];
      * `judge`, if present, is one of JUDGE_KINDS.

    Pure + deterministic; does no I/O and reads no defaults (so it never needs the runtime)."""
    errs: list[str] = []
    if not isinstance(suite, dict):
        return [f"eval_suite: expected object, got {type(suite).__name__}"]
    if not str(suite.get("suite_id", "")).strip():
        errs.append("eval_suite.suite_id: required non-empty string")

    # XOR over PRESENCE of the carrier keys (so an empty `examples: []` still reads as "inline declared" and
    # reaches the model-built non-empty check below — not as "no carrier at all").
    has_examples, ref = "examples" in suite, _is_ref(suite)
    if has_examples and ref:
        errs.append("eval_suite: declare EITHER `examples` (inline) OR `benchmark_ref` (named) — not both")
    if not has_examples and not ref:
        errs.append("eval_suite: declare one of `examples` (inline) or `benchmark_ref` (named registry suite)")

    if has_examples:
        examples = suite.get("examples")
        if not isinstance(examples, list):
            errs.append("eval_suite.examples: must be an array of {input, expected} rows")
        else:
            if model_built and len(examples) == 0:
                errs.append("eval_suite.examples: a model-built capability needs ≥1 example "
                            "(an empty suite must never read as a cleared gate)")
            for i, ex in enumerate(examples):
                if not isinstance(ex, dict):
                    errs.append(f"eval_suite.examples[{i}]: must be an object with input + expected")
                    continue
                if "input" not in ex:
                    errs.append(f"eval_suite.examples[{i}]: missing `input`")
                if "expected" not in ex:
                    errs.append(f"eval_suite.examples[{i}]: missing `expected` (the answer key the judge scores)")
                if "weight" in ex:
                    w = ex["weight"]
                    if isinstance(w, bool) or not isinstance(w, (int, float)) or w < 0:
                        errs.append(f"eval_suite.examples[{i}].weight: must be a non-negative number")

    if "gate_threshold" in suite:
        gt = suite["gate_threshold"]
        if isinstance(gt, bool) or not isinstance(gt, (int, float)) or not (0.0 <= float(gt) <= 1.0):
            errs.append("eval_suite.gate_threshold: must be a number in [0, 1]")
    if "judge" in suite and suite["judge"] not in JUDGE_KINDS:
        errs.append(f"eval_suite.judge: must be one of {list(JUDGE_KINDS)}")
    return errs


def normalize_eval_suite(suite: Any, *, model_built: bool = False) -> dict[str, Any]:
    """Validate + fill DEFAULTS, returning a NEW normalized eval_suite the runtime gate + compiler consume.

    Fills `gate_threshold` (from the canonical PROMOTE_AT), `holdout_policy` (derived from the canonical split
    constants), `judge` (default deterministic), and stamps `gate_basis` so a reader knows both splits must
    clear. Inline `examples` are normalized to `{input, expected, weight}` rows (weight defaults to 1.0).
    LOSSLESS: any extra keys the caller supplied are preserved verbatim. Raises ValueError listing every
    validation error if the suite is invalid (fail-closed — an unmeasurable 'done' is never normalized)."""
    errs = validate_eval_suite(suite, model_built=model_built)
    if errs:
        raise ValueError("invalid eval_suite: " + "; ".join(errs))

    out = dict(suite)  # lossless: keep every provided field (weights, judge config, policy overrides, ...)
    out.setdefault("gate_threshold", default_gate_threshold())
    out.setdefault("holdout_policy", default_holdout_policy())
    out.setdefault("judge", DEFAULT_JUDGE)
    out["gate_basis"] = gate_basis()  # stamped from the canonical source (informational; both splits gate)
    inline = "examples" in out  # key-presence (consistent with validate): an empty list is still inline
    out["source"] = "inline" if inline else "benchmark_ref"  # which carrier defines DONE

    if inline:
        out["examples"] = [
            {**ex, "weight": float(ex.get("weight", 1.0))} for ex in out["examples"]
        ]
        out["example_count"] = len(out["examples"])
    return out


def eval_pairs(normalized_suite: dict[str, Any]) -> list[tuple[Any, Any]]:
    """Project an inline normalized suite to the runtime's executable shape: a list of (input, expected)
    pairs — EXACTLY what `scripts.teleon_local_runtime`'s `_suite` iterates and the deterministic judge
    scores by exact match. This is the seam the runtime gate reads instead of a hardcoded CAPABILITIES suite.
    Empty for a benchmark_ref suite (resolve the ref first)."""
    return [(ex["input"], ex["expected"]) for ex in normalized_suite.get("examples", [])]


def resolve_benchmark_ref(ref: str, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve a `benchmark_ref` to its inline suite via a supplied registry {suite_id: eval_suite}.

    HONEST FAILURE: if `ref` is not in the registry (or no registry was supplied), raise
    BenchmarkNotRegisteredError — this function NEVER returns a fabricated/placeholder suite. The
    named-suite registry is the documented follow-up; this resolver is the real, honest seam for it (hand it
    a registry and it resolves; hand it nothing and it tells the truth)."""
    reg = registry or {}
    if ref not in reg:
        raise BenchmarkNotRegisteredError(ref, known=tuple(reg.keys()))
    return reg[ref]


__all__ = [
    "EVAL_GATE_SOURCE", "JUDGE_KINDS", "DEFAULT_JUDGE", "EVAL_SOURCE_KEYS",
    "BenchmarkNotRegisteredError",
    "default_gate_threshold", "default_holdout_policy", "gate_basis",
    "validate_eval_suite", "normalize_eval_suite", "eval_pairs", "resolve_benchmark_ref",
]
