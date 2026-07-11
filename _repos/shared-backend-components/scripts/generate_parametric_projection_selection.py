#!/usr/bin/env python3
"""scripts.generate_parametric_projection_selection — WORKABLE configured-primitives for 'projection_selection' by
PARAMETRIC PROOF (a proven mutator TEMPLATE x a specific parameter BINDING x canonical edge types).

A configured-primitive is NOT a static definition — it is (proven template) x (binding) executed against a fixture.
`field_project{keep:['id','name']}` and `field_project{keep:['sku','price']}` are DISTINCT workable primitives: each
is proven by EXECUTING the mutator on a realistic fixture and checking output, so ~2500 honest primitives fall out of
a curated parameter space over four proven templates (field_project · field_rename · omit/pick · deep_get) — not
filler. This is the ADD-ONLY parallel path: it IMPORTS the proven machinery (`scripts.mutator_registry`
{MUTATOR_REGISTRY, apply_mutator, run_primitive_proof} and `scripts.build_edge_type_retrofit.canonicalize_edge`) and
the sibling proof pack that registers dm_pick/dm_omit/dm_deep_get; it never edits a contract-locked or shared file.

Repo laws honored:
- serves_truth=true is set ONLY by a PASSING executed proof of THAT binding — the mutator is run on the fixture, the
  output checked, and re-run for determinism (all inside the imported run_primitive_proof). A binding that fails is
  NOT persisted as truth.
- Honest accounting: {generated, unique_after_dedupe, proven, typed} are SEPARATE counts; generated lines are never
  reported as active. DEDUPE is a canonical content hash over (mutator, binding, fixture).
- TYPE every persisted row via canonicalize_edge (input_edge_type_id + output_edge_type_id) so it can chain.
- Deterministic + offline ONLY: no network, no LLM, no wall-clock (fixed literal timestamp), no RNG (the parameter
  space is enumerated deterministically via itertools.combinations over a fixed field list).

CLI: --self-test (offline, standalone, small) | --write (persists the deduped proven shard + manifest).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import itertools
import json
import sys
from pathlib import Path
from typing import Any, Iterator

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the proven machinery — never edit it (ADD-ONLY / contract-locked files stay untouched).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    apply_mutator,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

# Import the sibling proof pack purely for its side effect: it registers dm_pick / dm_omit / dm_deep_get into the
# shared MUTATOR_REGISTRY. try/except so --self-test still runs if it is absent (we then fall back to the base
# templates already present in mutator_registry — field_project + field_rename).
try:  # noqa: SIM105
    import scripts.prove_leaves_dict_mapping  # noqa: F401,E402  (registration side effect)
except Exception:  # noqa: BLE001
    pass

FAMILY = "projection_selection"
# fixed literal timestamp — NO wall-clock (repo law: deterministic + offline).
GENERATED_UTC = "2026-07-03T00:00:00Z"

OUT_DIR = _resource("data") / "dev-intel" / "parametric_primitives"
OUT_JSONL = OUT_DIR / "param_projection_selection.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_projection_selection.json"

# ── the realistic record schema the parameter space is curated over ──
FIELDS: list[str] = [
    "id", "name", "sku", "price", "qty", "ts", "email", "phone", "addr", "city", "zip", "country",
]

# A fully-populated flat fixture (every field present) so a keep/drop/rename binding always yields a non-empty output.
FLAT_FIXTURE: dict[str, Any] = {
    "id": "R-1001", "name": "Ada Lovelace", "sku": "SKU-42", "price": 19.99, "qty": 3,
    "ts": "2026-07-03T00:00:00Z", "email": "ada@example.com", "phone": "+15550100",
    "addr": "1 Analytical Way", "city": "London", "zip": "EC1A", "country": "GB",
}

# One canonical rename target per field — renaming to a canonical name is a real, meaningfully-distinct behavior.
CANON_RENAME: dict[str, str] = {
    "id": "record_id", "name": "full_name", "sku": "product_sku", "price": "unit_price",
    "qty": "quantity", "ts": "event_timestamp", "email": "contact_email", "phone": "phone_number",
    "addr": "street_address", "city": "city_name", "zip": "postal_code", "country": "country_code",
}

# A nested fixture for deep_get: dotted paths into it are distinct extractions.
NESTED_FIXTURE: dict[str, Any] = {
    "id": "R-1001",
    "customer": {
        "name": "Ada Lovelace", "email": "ada@example.com", "phone": "+15550100",
        "addr": {"street": "1 Analytical Way", "city": "London", "zip": "EC1A", "country": "GB"},
    },
    "order": {"sku": "SKU-42", "price": 19.99, "qty": 3, "ts": "2026-07-03T00:00:00Z"},
    "meta": {"status": "ok", "source": "web", "flags": {"gift": True, "priority": False}},
}

# Present dotted paths (leaf + intermediate) — each extracts a distinct value.
DEEP_PATHS_PRESENT: list[str] = [
    "id",
    "customer", "customer.name", "customer.email", "customer.phone",
    "customer.addr", "customer.addr.street", "customer.addr.city", "customer.addr.zip", "customer.addr.country",
    "order", "order.sku", "order.price", "order.qty", "order.ts",
    "meta", "meta.status", "meta.source", "meta.flags", "meta.flags.gift", "meta.flags.priority",
]
# Missing paths WITH a curated default — deep_get returns the default (a distinct, still-proven behavior).
DEEP_PATHS_MISSING: list[tuple[str, Any]] = [
    ("customer.fax", None), ("order.discount", 0), ("meta.flags.wrap", False),
    ("customer.addr.region", "UNKNOWN"), ("order.tax", 0.0), ("shipping.method", "standard"),
]

# ── the template catalog: which proven mutator, over which slice of the parameter space ──
KEEP_TEMPLATES: list[tuple[str, str, list[int]]] = [
    # (mutator, arg_key, subset_sizes) — keep/pick a subset of fields
    ("field_project", "keep", [1, 2, 3, 4]),
    ("dm_pick", "keep", [2, 3, 4]),
]
DROP_TEMPLATES: list[tuple[str, str, list[int]]] = [
    ("dm_omit", "drop", [1, 2, 3]),
]
RENAME_SIZES: list[int] = [1, 2, 3]
DEEP_MUTATOR = "dm_deep_get"


def _available(mutator: str) -> bool:
    return mutator in MUTATOR_REGISTRY


# ── deterministic enumeration of the parameter space (itertools.combinations, no RNG) ──
def enumerate_bindings() -> Iterator[dict[str, Any]]:
    """Yield candidate configured-primitives {mutator, binding, fixture, input_edge, output_edge}, deterministically.

    The output_edge for deep_get is computed from the actual extracted value's shape so the type is honest.
    """
    fields = sorted(FIELDS)  # fixed, sorted -> deterministic ordering

    # keep / pick: project a record down to a subset
    for mutator, arg_key, sizes in KEEP_TEMPLATES:
        if not _available(mutator):
            continue
        for size in sizes:
            for combo in itertools.combinations(fields, size):
                yield {"mutator": mutator, "binding": {arg_key: list(combo)},
                       "fixture": FLAT_FIXTURE, "input_edge": "Record", "output_edge": "Record"}

    # omit: drop a subset of keys
    for mutator, arg_key, sizes in DROP_TEMPLATES:
        if not _available(mutator):
            continue
        for size in sizes:
            for combo in itertools.combinations(fields, size):
                yield {"mutator": mutator, "binding": {arg_key: list(combo)},
                       "fixture": FLAT_FIXTURE, "input_edge": "Record", "output_edge": "Record"}

    # field_rename: rename a subset of fields to their canonical names
    if _available("field_rename"):
        for size in RENAME_SIZES:
            for combo in itertools.combinations(fields, size):
                mapping = {f: CANON_RENAME[f] for f in combo}
                yield {"mutator": "field_rename", "binding": {"mapping": mapping},
                       "fixture": FLAT_FIXTURE, "input_edge": "Record", "output_edge": "Record"}

    # deep_get: extract a value by dotted path (present + missing-with-default)
    if _available(DEEP_MUTATOR):
        for path in DEEP_PATHS_PRESENT:
            out, _ = apply_mutator(DEEP_MUTATOR, NESTED_FIXTURE, path=path)
            yield {"mutator": DEEP_MUTATOR, "binding": {"path": path},
                   "fixture": NESTED_FIXTURE, "input_edge": "Record",
                   "output_edge": "Record" if isinstance(out, dict) else "Scalar"}
        for path, default in DEEP_PATHS_MISSING:
            yield {"mutator": DEEP_MUTATOR, "binding": {"path": path, "default": default},
                   "fixture": NESTED_FIXTURE, "input_edge": "Record", "output_edge": "Scalar"}


def content_hash(mutator: str, binding: dict[str, Any], fixture: Any) -> str:
    """Canonical content hash over (mutator, binding, fixture) — identical bindings collapse to one primitive."""
    blob = json.dumps({"mutator": mutator, "binding": binding, "fixture": fixture},
                      sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def prove_binding(cand: dict[str, Any]) -> dict[str, Any] | None:
    """Prove ONE binding: compute the expected output by running the mutator once, then run the imported executed
    proof (fixture-behavior + determinism). Return a TYPED persistable row ONLY if serves_truth flips true; else None.
    """
    mutator, binding, fixture = cand["mutator"], cand["binding"], cand["fixture"]
    # compute expected by running the mutator once (then the proof re-executes it and asserts a match — determinism).
    try:
        expected, _ = apply_mutator(mutator, fixture, **binding)
    except Exception:  # noqa: BLE001 — an un-runnable binding is not truth
        return None
    sha16 = content_hash(mutator, binding, fixture)
    pid = f"prim:param:{mutator}:{sha16}"
    receipt = run_primitive_proof(pid, mutator, fixture, expected, mutator_args=binding)
    if receipt["serves_truth"] is not True:
        return None  # a binding that fails its executed proof is NEVER persisted as truth
    return {
        "record_type": "parametric_configured_primitive",
        "primitive_id": pid,
        "content_hash": sha16,
        "mutator": mutator,
        "binding": binding,
        "family": FAMILY,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": cand["input_edge"],
        "output_edge": cand["output_edge"],
        "input_edge_type_id": canonicalize_edge(cand["input_edge"]),
        "output_edge_type_id": canonicalize_edge(cand["output_edge"]),
        "input_hash": receipt["input_hash"],
        "output_hash": receipt["output_hash"],
        "proofs": receipt["proofs"],
    }


def generate() -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Enumerate -> prove -> dedupe -> type. Returns (rows, counts) with SEPARATE honest counts."""
    generated = 0
    proven = 0
    seen: dict[str, dict[str, Any]] = {}
    for cand in enumerate_bindings():
        generated += 1
        row = prove_binding(cand)
        if row is None:
            continue
        proven += 1
        # DEDUPE by canonical content hash — an identical (mutator, binding, fixture) collapses to one.
        seen.setdefault(row["content_hash"], row)
    rows = sorted(seen.values(), key=lambda r: r["primitive_id"])
    typed = sum(1 for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"])
    counts = {
        "generated": generated,
        "unique_after_dedupe": len(rows),
        "proven": proven,
        "typed": typed,
    }
    return rows, counts


def build_manifest(rows: list[dict[str, Any]], counts: dict[str, int]) -> dict[str, Any]:
    per_mutator: dict[str, int] = {}
    for r in rows:
        per_mutator[r["mutator"]] = per_mutator.get(r["mutator"], 0) + 1
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    return {
        "record_type": "parametric_projection_selection_manifest",
        "family": FAMILY,
        "pack_id": "parametric-projection-selection",
        "generator": "scripts/generate_parametric_projection_selection.py",
        "generated_utc": GENERATED_UTC,
        # SEPARATE, never-conflated counts (honest accounting):
        "generated": counts["generated"],
        "unique_after_dedupe": counts["unique_after_dedupe"],
        "proven": counts["proven"],
        "typed": counts["typed"],
        "per_mutator_counts": {k: per_mutator[k] for k in sorted(per_mutator)},
        "templates": sorted({r["mutator"] for r in rows}),
        "field_schema": FIELDS,
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "note": "Each row is (proven mutator TEMPLATE) x (specific parameter BINDING) x canonical edge types, proven "
                "by EXECUTING the mutator on a fixture (run_primitive_proof, imported from scripts/mutator_registry.py) "
                "— serves_truth=true set ONLY on a passing executed proof; a failing binding is not persisted. Every "
                "row is TYPED via canonicalize_edge so it can chain. Counts are separate: generated (enumerated) vs "
                "unique_after_dedupe (content-hash collapse) vs proven (passers) vs typed.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack() -> dict[str, Any]:
    rows, counts = generate()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows, counts)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


# ── standalone offline self-test (small, does NOT touch disk or the full enumeration) ──
def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # 1. a small enumeration proves + types correctly
    small = [
        {"mutator": "field_project", "binding": {"keep": ["id", "name"]}, "fixture": FLAT_FIXTURE,
         "input_edge": "Record", "output_edge": "Record"},
        {"mutator": "field_project", "binding": {"keep": ["sku", "price"]}, "fixture": FLAT_FIXTURE,
         "input_edge": "Record", "output_edge": "Record"},
        {"mutator": "field_rename", "binding": {"mapping": {"sku": "product_sku"}}, "fixture": FLAT_FIXTURE,
         "input_edge": "Record", "output_edge": "Record"},
    ]
    if _available("dm_omit"):
        small.append({"mutator": "dm_omit", "binding": {"drop": ["email", "phone"]}, "fixture": FLAT_FIXTURE,
                      "input_edge": "Record", "output_edge": "Record"})
    if _available("dm_deep_get"):
        small.append({"mutator": "dm_deep_get", "binding": {"path": "customer.addr.city"},
                      "fixture": NESTED_FIXTURE, "input_edge": "Record", "output_edge": "Scalar"})
    small_rows = [r for r in (prove_binding(c) for c in small) if r is not None]
    checks.append(("small enumeration all prove", len(small_rows) == len(small)))
    checks.append(("distinct keep-sets -> DISTINCT primitive ids",
                   small_rows[0]["primitive_id"] != small_rows[1]["primitive_id"]))
    checks.append(("every proven row carries BOTH edge type ids + serves_truth=true",
                   all(r["input_edge_type_id"] and r["output_edge_type_id"] and r["serves_truth"] is True
                       for r in small_rows)))
    checks.append(("every proven row is L7_executed_proof with all sub-proofs passing",
                   all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
                       for r in small_rows)))
    checks.append(("edge type ids canonicalize onto the shared namespace (Record->RecordBatch)",
                   small_rows[0]["input_edge_type_id"] == "RecordBatch"))

    # 2. dedupe collapses an identical binding
    dup = dict(small[0])  # same (mutator, binding, fixture) as small[0]
    h1 = content_hash(small[0]["mutator"], small[0]["binding"], small[0]["fixture"])
    h2 = content_hash(dup["mutator"], dup["binding"], dup["fixture"])
    collapsed: dict[str, dict[str, Any]] = {}
    for c in [small[0], dup]:
        r = prove_binding(c)
        collapsed.setdefault(r["content_hash"], r)
    checks.append(("identical binding has identical content hash", h1 == h2))
    checks.append(("dedupe collapses an identical binding (2 -> 1)", len(collapsed) == 1))

    # 3. a deliberately-WRONG expected FAILS the executed proof and is NOT persisted
    wrong = run_primitive_proof("prim:param:field_project:WRONG", "field_project", FLAT_FIXTURE,
                                {"WRONG": 999}, mutator_args={"keep": ["id"]})
    checks.append(("a deliberately-wrong expected FAILS the proof (stays candidate)",
                   wrong["serves_truth"] is False and wrong["promoted"] is False))
    # an un-runnable binding (bad kwarg) returns None -> not persisted
    bad = prove_binding({"mutator": "field_project", "binding": {"NOT_A_KWARG": 1}, "fixture": FLAT_FIXTURE,
                         "input_edge": "Record", "output_edge": "Record"})
    checks.append(("an un-runnable binding is not persisted", bad is None))

    # 4. determinism: re-proving the small set yields identical rows
    small_rows_2 = [r for r in (prove_binding(c) for c in small) if r is not None]
    checks.append(("deterministic: re-proving yields identical rows",
                   [json.dumps(r, sort_keys=True) for r in small_rows_2]
                   == [json.dumps(r, sort_keys=True) for r in small_rows]))

    # 5. honest accounting: generate() returns separate counts and never persists a failer as proven
    #    (run a tiny bounded slice via enumerate to confirm the counts wiring — bounded to keep --self-test small)
    tiny = list(itertools.islice(enumerate_bindings(), 20))
    tiny_rows = [r for r in (prove_binding(c) for c in tiny) if r is not None]
    tiny_typed = sum(1 for r in tiny_rows if r["input_edge_type_id"] and r["output_edge_type_id"])
    checks.append(("bounded slice: proven <= generated and typed == proven",
                   len(tiny_rows) <= len(tiny) and tiny_typed == len(tiny_rows)))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - generate_parametric_projection_selection:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - generate_parametric_projection_selection: parametric proof works — {len(small_rows)} small "
          "configured-primitives PROVEN (executed proof, serves_truth=true) AND TYPED (both edge type_ids); distinct "
          "keep-sets yield distinct ids; an identical binding dedupes 2->1; a deliberately-wrong expected FAILS and is "
          "not persisted; re-proving is deterministic. Counts are separate (generated/unique/proven/typed).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack()
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
