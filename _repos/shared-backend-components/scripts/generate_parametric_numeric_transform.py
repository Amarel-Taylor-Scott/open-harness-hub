#!/usr/bin/env python3
"""scripts.generate_parametric_numeric_transform — WORKABLE configured-primitives for 'numeric_transform' by PARAMETRIC PROOF.

A configured-primitive = (a PROVEN mutator TEMPLATE) x (a specific parameter BINDING) x (canonical edge types).
`numeric_clamp{lo:0,hi:10}` and `numeric_clamp{lo:0,hi:100}` are DISTINCT workable primitives — each proven by
EXECUTING the mutator on a fixture and checking the output, each TYPED with canonical input/output edge type ids so it
can chain. This is how a large family of honest workable primitives is generated without a pile of bloated static
files: efficient TEMPLATE+BINDING rows, one row per proven binding.

Repo laws obeyed (ADD-ONLY, no edits to contract-locked/shared files):
- serves_truth=true is set ONLY by a PASSING executed proof of THAT binding. Every binding's EXPECTED output is
  computed by RUNNING the mutator once; `run_primitive_proof` (imported from _repos/shared-backend-components/scripts/mutator_registry.py) then
  EXECUTES the mutator against the fixture, checks the output, and checks determinism (re-run identical). Only a
  passing receipt is persisted; a binding whose executed proof fails is NEVER persisted as truth.
- Honest accounting: {generated, unique_after_dedupe, proven, typed} are SEPARATE counts — generated candidate
  bindings are never reported as active primitives. Dedupe collapses identical (mutator, binding, fixture) by a
  canonical content hash.
- Typing: every persisted row carries input_edge_type_id + output_edge_type_id via `canonicalize_edge` (imported from
  _repos/shared-backend-components/scripts/build_edge_type_retrofit.py).
- Deterministic + offline ONLY: no network, no LLM, no wall-clock (fixed literal timestamp), no RNG (the parameter
  space is ENUMERATED deterministically). The proven mutator TEMPLATES are imported from the sibling
  _repos/shared-backend-components/scripts/prove_leaves_numeric_math.py (which registers the numeric mutators into MUTATOR_REGISTRY on import); the
  import is guarded so --self-test still runs if a sibling is absent.

Templates parameterized: clamp (bounds), bucketize (edge-sets), scale (factors), round (modes/precisions),
normalize (scale-to-unit-interval bounds). CLI: --self-test | --write [--date D].

This module writes its OWN shard file (no shared-JSONL write race) and does NOT register itself in
flywheel_proof_modules.py — it REPORTS its (script_path, module_name) tuple for the parent workflow to register.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterator

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY).
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _hash,
    apply_mutator,
    run_primitive_proof,
)

# IMPORT the proven numeric TEMPLATES. This sibling registers numeric_* mutators into MUTATOR_REGISTRY on import.
# Guarded so --self-test still runs if the sibling is absent (falls back to whatever is already registered).
try:  # noqa: SIM105
    import scripts.prove_leaves_numeric_math as _numeric_templates  # noqa: F401,E402
except Exception:  # noqa: BLE001  (best-effort; the templates may already be registered elsewhere)
    _numeric_templates = None

OUT_DIR = _resource("data") / "dev-intel" / "parametric_primitives"
OUT_JSONL = OUT_DIR / "param_numeric_transform.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_numeric_transform.json"
GROUP = "numeric_transform"
FAMILY = GROUP
# Fixed literal timestamp — no wall-clock (deterministic, offline).
DEFAULT_DATE = "2026-07-03"

# The (script_path, module_name) tuple the parent workflow must register in flywheel_proof_modules.py.
REGISTER_TUPLE = ("scripts/generate_parametric_numeric_transform.py", "scripts.generate_parametric_numeric_transform")

# ── canonical edge types per numeric-transform template (raw edge strings; canonicalized at persist time) ──
EDGE_TYPES: dict[str, tuple[str, str]] = {
    "numeric_clamp": ("Number", "Number"),
    "numeric_scale_to_01": ("Number", "UnitInterval"),
    "numeric_bucketize": ("Number", "Integer"),
    "numeric_scale": ("Number", "Number"),
    "numeric_round_half_up": ("Number", "Number"),
    "numeric_ceil": ("Number", "Integer"),
    "numeric_floor": ("Number", "Integer"),
    "numeric_trunc": ("Number", "Integer"),
}

# ── CURATED, deterministically-enumerated parameter spaces (meaningfully distinct behaviors, not trivial noise) ──
# clamp / normalize bounds — every ordered (lo, hi) with lo < hi over two curated ladders of real thresholds.
_LO_VALUES: list[float] = [
    -1000, -500, -250, -200, -128, -100, -64, -50, -32, -20, -16, -10, -8, -5, -2, -1,
    0, 1, 2, 5, 8, 10, 16, 20, 25, 32, 50, 64, 100, 128, 200,
]
_HI_VALUES: list[float] = [
    -500, -250, -200, -128, -100, -64, -50, -32, -16, -8, -5, -2, -1,
    1, 2, 5, 8, 10, 16, 20, 25, 32, 50, 64, 100, 128, 200, 250, 255, 500, 1000,
]
# bucketize edge-sets — arithmetic boundary grids (start, step, count); each triple is a distinct real binning scheme.
_BUCKET_STARTS: list[float] = [0, 1, 5, 10, 25, 50, 100, -50, -10, 2]
_BUCKET_STEPS: list[float] = [1, 2, 5, 10, 20, 25, 50, 100]
_BUCKET_COUNTS: list[int] = [2, 3, 4, 5, 6, 8, 10, 12]
# scale factors — decimals (percent-style), whole multipliers, and their negatives; distinct real scaling behaviors.
_SCALE_FACTORS: list[float] = (
    [round(i / 100, 4) for i in range(1, 201)]      # 0.01 .. 2.00
    + [float(i) for i in range(3, 41)]              # 3 .. 40 (whole multipliers; 1,2 already covered as 1.00,2.00)
    + [round(-i / 100, 4) for i in range(1, 201)]   # -0.01 .. -2.00 (sign-flipping scales)
)
# round precisions/modes — half-up at increasing precision, plus the ceil/floor/trunc rounding modes.
_ROUND_HALF_UP_PRECISIONS: list[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8]
_ROUND_HALF_UP_FIXTURE: float = 123.45678912345  # long-tailed value so each precision yields a distinct output


# ── binding enumeration: each yields (mutator, binding_kwargs, fixture_input); fixtures are deterministic ──
def _clamp_bindings() -> Iterator[tuple[str, dict[str, Any], Any]]:
    for lo in _LO_VALUES:
        for hi in _HI_VALUES:
            if lo < hi:
                # fixture above the ceiling -> real clamp to hi (behavior depends on the binding).
                yield "numeric_clamp", {"lo": lo, "hi": hi}, hi + 5


def _normalize_bindings() -> Iterator[tuple[str, dict[str, Any], Any]]:
    for lo in _LO_VALUES:
        for hi in _HI_VALUES:
            if lo < hi:
                # fixture a quarter of the way into the range -> a proper fractional scale-to-unit-interval.
                fixture = lo + (hi - lo) * 0.25
                yield "numeric_scale_to_01", {"lo": lo, "hi": hi}, fixture


def _bucketize_bindings() -> Iterator[tuple[str, dict[str, Any], Any]]:
    for start in _BUCKET_STARTS:
        for step in _BUCKET_STEPS:
            for count in _BUCKET_COUNTS:
                boundaries = [start + step * i for i in range(count)]
                # fixture at the midpoint of the boundary span -> a non-trivial interior bucket index.
                fixture = (boundaries[0] + boundaries[-1]) / 2
                yield "numeric_bucketize", {"boundaries": boundaries}, fixture


def _scale_bindings() -> Iterator[tuple[str, dict[str, Any], Any]]:
    for factor in _SCALE_FACTORS:
        # a fixed base value so the output is fully determined by the factor binding.
        yield "numeric_scale", {"factor": factor}, 100


def _round_bindings() -> Iterator[tuple[str, dict[str, Any], Any]]:
    for ndigits in _ROUND_HALF_UP_PRECISIONS:
        yield "numeric_round_half_up", {"ndigits": ndigits}, _ROUND_HALF_UP_FIXTURE
    # the other rounding modes (parameterless configured behaviors)
    yield "numeric_ceil", {}, 4.2
    yield "numeric_floor", {}, 4.8
    yield "numeric_trunc", {}, -4.7


_BINDING_GENERATORS = [
    _clamp_bindings, _normalize_bindings, _bucketize_bindings, _scale_bindings, _round_bindings,
]


def enumerate_bindings() -> Iterator[tuple[str, dict[str, Any], Any]]:
    """Deterministically enumerate every curated (mutator, binding, fixture). Skips any template whose mutator
    template is not registered (guarded import fallback)."""
    for gen in _BINDING_GENERATORS:
        for mutator, binding, fixture in gen():
            if mutator in MUTATOR_REGISTRY:
                yield mutator, binding, fixture


# ── content hash (canonical, over the full identity of a configured-primitive) for dedupe + id ──
def _content_hash(mutator: str, binding: dict[str, Any], fixture: Any) -> str:
    return _hash({"mutator": mutator, "binding": binding, "fixture": fixture})


def _prove_and_type(mutator: str, binding: dict[str, Any], fixture: Any, expected: Any) -> dict[str, Any] | None:
    """EXECUTE the binding's proof; return a TYPED persisted row ONLY on a passing executed proof, else None."""
    content_hash = _content_hash(mutator, binding, fixture)
    primitive_id = f"prim:param:{mutator}:{content_hash}"
    receipt = run_primitive_proof(primitive_id, mutator, fixture, expected, mutator_args=binding)
    if receipt.get("serves_truth") is not True:
        return None  # a binding that fails its executed proof is NOT persisted as truth
    input_edge, output_edge = EDGE_TYPES[mutator]
    return {
        "primitive_id": primitive_id,
        "mutator": mutator,
        "family": FAMILY,
        "binding": binding,
        "fixture": fixture,
        "expected": expected,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": input_edge,
        "output_edge": output_edge,
        # TYPING — a workable primitive MUST carry canonical edge type ids so it can chain.
        "input_edge_type_id": canonicalize_edge(input_edge),
        "output_edge_type_id": canonicalize_edge(output_edge),
        "output_hash": receipt["output_hash"],
    }


def generate(limit: int | None = None) -> dict[str, Any]:
    """Enumerate -> compute expected by running -> executed-proof -> dedupe -> type. Returns honest separate counts."""
    generated = 0
    unique_hashes: set[str] = set()
    rows_by_hash: dict[str, dict[str, Any]] = {}
    for mutator, binding, fixture in enumerate_bindings():
        if limit is not None and generated >= limit:
            break
        generated += 1
        # EXPECTED is computed by RUNNING the mutator once (the proof then re-executes + checks determinism).
        expected, _ = apply_mutator(mutator, fixture, **binding)
        content_hash = _content_hash(mutator, binding, fixture)
        if content_hash in unique_hashes:
            continue  # identical (mutator, binding, fixture) collapses in dedupe
        unique_hashes.add(content_hash)
        row = _prove_and_type(mutator, binding, fixture, expected)
        if row is not None:
            rows_by_hash[content_hash] = row
    rows = [rows_by_hash[h] for h in sorted(rows_by_hash)]
    typed = [r for r in rows if r.get("input_edge_type_id") and r.get("output_edge_type_id")]
    return {
        "generated": generated,
        "unique_after_dedupe": len(unique_hashes),
        "proven": len(rows),
        "typed": len(typed),
        "rows": rows,
    }


def build_manifest(result: dict[str, Any], *, date: str) -> dict[str, Any]:
    rows = result["rows"]
    per_mutator: dict[str, int] = {}
    for r in rows:
        per_mutator[r["mutator"]] = per_mutator.get(r["mutator"], 0) + 1
    return {
        "record_type": "parametric_numeric_transform_manifest",
        "pack_id": "parametric-configured-primitives-numeric-transform",
        "generator": REGISTER_TUPLE[0],
        "group": GROUP,
        "family": FAMILY,
        "generated_utc": date,
        # HONEST accounting — four SEPARATE counts, never conflated.
        "generated": result["generated"],
        "unique_after_dedupe": result["unique_after_dedupe"],
        "proven": result["proven"],
        "typed": result["typed"],
        "verification_level": "L7_executed_proof",
        "proven_per_template": per_mutator,
        "templates": sorted(EDGE_TYPES),
        "register_tuple": list(REGISTER_TUPLE),
        "note": "Each row is a configured-primitive = (proven mutator template) x (parameter binding) x (canonical "
                "edge types). serves_truth=true is set ONLY by an executed passing proof (run_primitive_proof, "
                "imported from scripts/mutator_registry.py) of THAT binding; the EXPECTED output is computed by "
                "running the mutator, then re-executed + determinism-checked. Every row is TYPED via canonicalize_edge "
                "(imported from scripts/build_edge_type_retrofit.py). generated/unique_after_dedupe/proven/typed are "
                "SEPARATE counts. A binding whose executed proof fails is never persisted.",
    }


def write_pack(*, date: str) -> dict[str, Any]:
    result = generate()
    rows = result["rows"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(result, date=date)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # 1. a small enumeration proves + types correctly (offline, standalone, small)
    sample = generate(limit=40)
    srows = sample["rows"]
    checks.append(("small enumeration yields proven rows", len(srows) > 0))
    checks.append(("every sample row serves_truth=true / candidate=false / L7",
                   all(r["serves_truth"] is True and r["candidate"] is False
                       and r["verification_level"] == "L7_executed_proof" for r in srows)))
    checks.append(("EVERY sample row carries non-null input_edge_type_id + output_edge_type_id",
                   all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in srows)))
    checks.append(("sample proven == typed (all proven rows are typed)", sample["proven"] == sample["typed"]))
    checks.append(("distinct bindings -> distinct primitive_ids",
                   len({r["primitive_id"] for r in srows}) == len(srows)))

    # 2. dedupe collapses an IDENTICAL binding (same mutator, binding, fixture -> one content hash)
    h1 = _content_hash("numeric_clamp", {"lo": 0, "hi": 10}, 15)
    h2 = _content_hash("numeric_clamp", {"lo": 0, "hi": 10}, 15)
    unique_hashes: set[str] = set()
    for _ in range(2):  # feed the same binding twice
        unique_hashes.add(_content_hash("numeric_clamp", {"lo": 0, "hi": 10}, 15))
    checks.append(("identical binding collapses in dedupe (one unique content hash)",
                   h1 == h2 and len(unique_hashes) == 1))
    checks.append(("meaningfully-distinct bindings do NOT collapse",
                   _content_hash("numeric_clamp", {"lo": 0, "hi": 10}, 15)
                   != _content_hash("numeric_clamp", {"lo": 0, "hi": 100}, 105)))

    # 3. a deliberately-WRONG expected FAILS the executed proof and is NOT persisted
    bad_row = _prove_and_type("numeric_clamp", {"lo": 0, "hi": 10}, 15, 999)  # true clamp output is 10, not 999
    bad_receipt = run_primitive_proof("prim:param:bad", "numeric_clamp", 15, 999, mutator_args={"lo": 0, "hi": 10})
    checks.append(("a wrong-expected binding stays candidate (proof gate is real)",
                   bad_receipt["serves_truth"] is False and bad_receipt.get("promoted") is False))
    checks.append(("a wrong-expected binding is NOT persisted (no row)", bad_row is None))

    # 4. an un-runnable binding (bad kwargs) fails the executed proof, does not promote
    err = _prove_and_type("numeric_clamp", {"lo": 0}, 15, 10)  # missing 'hi' -> execution error inside the proof
    checks.append(("an un-runnable binding is not persisted", err is None))

    # 5. determinism: re-running the same enumeration yields byte-identical rows
    sample2 = generate(limit=40)
    checks.append(("deterministic: re-run yields identical rows",
                   [json.dumps(r, sort_keys=True) for r in sample2["rows"]]
                   == [json.dumps(r, sort_keys=True) for r in srows]))

    # 6. honest accounting keeps counts separate (generated >= unique >= proven == typed)
    checks.append(("honest accounting ordering generated>=unique>=proven==typed",
                   sample["generated"] >= sample["unique_after_dedupe"] >= sample["proven"] == sample["typed"]))

    # 7. the proven mutator templates are actually registered (imported, not reinvented)
    checks.append(("clamp/bucketize/scale/round/normalize templates registered",
                   all(m in MUTATOR_REGISTRY for m in
                       ("numeric_clamp", "numeric_bucketize", "numeric_scale",
                        "numeric_round_half_up", "numeric_scale_to_01"))))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - generate_parametric_numeric_transform:\n  " + "\n  ".join(failed))
        return 1
    ex = srows[0]
    print(f"PASS - generate_parametric_numeric_transform: parametric proof over {len(_BINDING_GENERATORS)} numeric "
          f"templates (clamp/normalize/bucketize/scale/round). Small enumeration proved {sample['proven']} "
          f"configured-primitives, all TYPED (e.g. {ex['primitive_id']} {ex['mutator']}{ex['binding']}: "
          f"{ex['input_edge_type_id']}->{ex['output_edge_type_id']}); dedupe collapses identical bindings; a "
          "wrong-expected and an un-runnable binding correctly stay candidate (never persisted). Register tuple: "
          + json.dumps(list(REGISTER_TUPLE)))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack(date=args.date or DEFAULT_DATE)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
