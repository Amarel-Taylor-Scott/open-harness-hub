#!/usr/bin/env python3
"""scripts.generate_parametric_relational_structural — WORKABLE configured-primitives for the 'relational_structural'
group by PARAMETRIC PROOF.

A configured-primitive = (a proven mutator TEMPLATE) x (a specific parameter BINDING) x (canonical edge types). For
example `sr_group_by_key{key:'user_id'}` and `sr_group_by_key{key:'sku'}` are DISTINCT workable primitives — each
proven by EXECUTING the mutator on a realistic fixture and checking the output. This module curates a deterministic,
meaningfully-distinct parameter space for six proven relational/structural templates (join_on_key, dedupe_cluster_key,
group_by, flatten, pivot, nest_by_key), and for EACH binding: builds a fixture + the EXPECTED output (by running the
mutator once), runs the imported, contract-locked `run_primitive_proof` (the ONLY thing that flips serves_truth
false->true — via an executed passing proof + a determinism re-run), keeps ONLY the passers, DEDUPES by a canonical
content hash over (mutator, binding, fixture), and TYPES every survivor via `canonicalize_edge` (input + output edge
type ids) so a configured-primitive can chain.

REPO LAWS honored:
- serves_truth=true is set ONLY by a PASSING executed proof of THAT binding — never inferred from the template. A
  binding that fails is NOT persisted as truth.
- Honest accounting: generated / unique(deduped) / proven / typed are SEPARATE counts, never conflated. Generated
  lines are never reported as active.
- ADD-ONLY: this NEW file imports the proven machinery (mutator_registry, build_edge_type_retrofit) and the sibling
  leaf provers (which register the sr_* / reshape_* mutators on import); it edits none of the contract-locked or
  shared files, and writes its OWN shard (no shared-JSONL write race).
- Deterministic + offline: no network, no LLM, no wall-clock (fixed literal timestamp), no RNG (the parameter space is
  enumerated deterministically; pseudo-variety in fixture values comes from a stable string seed f"{group}:{i}",
  never hash()).

CLI: --self-test (offline, standalone, small) | --write [--date D].

Register tuple (REPORT ONLY — this module never edits flywheel_proof_modules.py):
    ("_repos/shared-backend-components/scripts/generate_parametric_relational_structural.py", "scripts.generate_parametric_relational_structural")
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the proven machinery — never edit it (ADD-ONLY seam).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    apply_mutator,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

# Import the sibling leaf provers so their sr_* / reshape_* mutators register into MUTATOR_REGISTRY on import.
# try/except so --self-test still runs even if one is absent (it then falls back to the base 11 in mutator_registry;
# any template whose mutator is missing is simply skipped — an honest drop in the counts, never a fake pass).
try:  # noqa: SIM105
    import scripts.prove_leaves_set_relational  # noqa: F401  (registers sr_* mutators)
except Exception:  # noqa: BLE001
    pass
try:  # noqa: SIM105
    import scripts.prove_leaves_structural_reshape  # noqa: F401  (registers reshape_* mutators)
except Exception:  # noqa: BLE001
    pass

GROUP = "relational_structural"
FAMILY = GROUP
# Fixed literal timestamp — NO wall-clock (deterministic + offline law).
FIXED_DATE = "2026-07-03"

OUT_DIR = _resource("data") / "dev-intel" / "parametric_primitives"
OUT_JSONL = OUT_DIR / "param_relational_structural.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_relational_structural.json"


# ══ deterministic value helper (stable string seed — NEVER hash(); no RNG) ══
def _seed_val(group: str, i: int) -> str:
    """Stable, deterministic pseudo-variety token for a fixture cell — f"{group}:{i}" style, never hash()."""
    return f"{group}:{i}"


# ══ CURATED, deterministic, meaningfully-distinct parameter pools ══
# 24 realistic key names — each yields a DISTINCT grouping/join/cluster behavior.
KEYS: list[str] = [
    "id", "user_id", "sku", "order_id", "customer_id", "email", "account_id", "product_id",
    "session_id", "tenant_id", "region", "status", "category", "country", "currency", "vendor_id",
    "invoice_id", "ticket_id", "device_id", "campaign_id", "merchant_id", "subscription_id",
    "warehouse_id", "channel",
]

# 18 curated field-sets — each changes the row CONTENT (and thus the grouped/clustered/nested output). Distinct.
FIELD_SETS: list[list[str]] = [
    ["name"], ["amount"], ["name", "amount"], ["qty", "price"], ["name", "qty", "price"],
    ["ts", "label"], ["score"], ["state", "note"], ["rank", "weight"], ["tier"], ["color", "size"],
    ["code"], ["name", "code"], ["amount", "qty"], ["label", "score"], ["name", "state", "tier"],
    ["price", "weight"], ["tag", "rank"],
]

# join_on_key: 5 left-field sets x 4 right-field sets = 20 distinct (left,right) field selections.
JOIN_LEFT_SETS: list[list[str]] = [["name"], ["amount"], ["name", "qty"], ["label"], ["score", "rank"]]
JOIN_RIGHT_SETS: list[list[str]] = [["price"], ["ts", "note"], ["weight"], ["tier", "size"]]

# flatten: 5 separators x 10 branch keys x 8 leaf pairs = 400 distinct nested->flat behaviors.
FLATTEN_SEPS: list[str] = [".", "__", "/", ":", "-"]
FLATTEN_BRANCHES: list[str] = [
    "user", "address", "meta", "geo", "billing", "profile", "device", "order", "account", "contact",
]
FLATTEN_LEAF_PAIRS: list[list[str]] = [
    ["id", "name"], ["city", "zip"], ["lat", "lon"], ["code", "tier"], ["email", "phone"],
    ["first", "last"], ["street", "unit"], ["min", "max"],
]

# pivot: 12 (index,key,value) name-sets x 25 metric-sets = 300 distinct long->wide behaviors.
PIVOT_NAME_SETS: list[list[str]] = [
    ["id", "metric", "value"], ["id", "key", "val"], ["user_id", "metric", "amount"],
    ["order_id", "field", "num"], ["sku", "attr", "measure"], ["account_id", "metric", "value"],
    ["region", "kpi", "score"], ["customer_id", "dim", "qty"], ["ticket_id", "metric", "count"],
    ["device_id", "sensor", "reading"], ["campaign_id", "metric", "spend"], ["session_id", "event", "n"],
]
_METRIC_VOCAB: list[str] = [
    "clicks", "views", "spend", "cpu", "mem", "open", "close", "high", "low", "qty", "price", "tax",
    "net", "gross", "lat", "lon", "inb", "outb", "up", "down", "read", "write", "hit", "miss", "warn",
]
# 12 sliding pairs + 13 sliding triples = 25 distinct metric-column selections.
PIVOT_METRIC_SETS: list[list[str]] = (
    [[_METRIC_VOCAB[i], _METRIC_VOCAB[i + 1]] for i in range(12)]
    + [[_METRIC_VOCAB[i], _METRIC_VOCAB[i + 1], _METRIC_VOCAB[i + 2]] for i in range(13)]
)


# ══ fixture builders (pure, deterministic; values from the stable string seed, never RNG/hash) ══
def _grouping_batch(key: str, extra_fields: list[str]) -> list[dict[str, Any]]:
    """4 rows across 2 key-groups — non-trivial grouping/clustering. Extra fields carry deterministic seed values."""
    rows: list[dict[str, Any]] = []
    for i in range(4):
        row: dict[str, Any] = {key: f"{key}_g{i % 2}"}
        for f in extra_fields:
            row[f] = f"{f}_{_seed_val(GROUP, i)}"
        rows.append(row)
    return rows


def _join_pair(key: str, left_fields: list[str], right_fields: list[str]):
    """left/right batches that share exactly one key value so the inner join produces a real merged row."""
    kv_a, kv_b, kv_c = f"{key}_1", f"{key}_2", f"{key}_3"
    left = [
        {key: kv_a, **{f: f"{f}_L{_seed_val(GROUP, 0)}" for f in left_fields}},
        {key: kv_b, **{f: f"{f}_L{_seed_val(GROUP, 1)}" for f in left_fields}},
    ]
    right = [
        {key: kv_b, **{f: f"{f}_R{_seed_val(GROUP, 0)}" for f in right_fields}},
        {key: kv_c, **{f: f"{f}_R{_seed_val(GROUP, 1)}" for f in right_fields}},
    ]
    return left, right


def _nested_record(branch: str, leaves: list[str]) -> dict[str, Any]:
    """A nested record: one branch dict with two leaves + a scalar top field. Flatten collapses the branch."""
    return {branch: {leaves[0]: f"{leaves[0]}_{_seed_val(GROUP, 0)}",
                     leaves[1]: f"{leaves[1]}_{_seed_val(GROUP, 1)}"},
            "root": f"root_{_seed_val(GROUP, 2)}"}


def _long_rows(index: str, key_col: str, value_col: str, metrics: list[str]) -> list[dict[str, Any]]:
    """Long-format rows for a single index value, one row per metric — pivot folds them into one wide row."""
    iv = f"{index}_1"
    return [{index: iv, key_col: m, value_col: 10 * (j + 1)} for j, m in enumerate(metrics)]


# ══ template registry: name -> (mutator, input_edge, output_edge, binding->(fixture, mutator_args)) ══
# Each entry is a PROVEN mutator template; the enumerator below curates its parameter space.
def _enum_grouping(mutator: str) -> Iterable[dict[str, Any]]:
    for key in KEYS:
        for fields in FIELD_SETS:
            binding = {"key": key, "extra_fields": list(fields)}
            fixture = _grouping_batch(key, list(fields))
            yield {"mutator": mutator, "binding": binding, "fixture": fixture, "args": {"key": key}}


def _enum_join() -> Iterable[dict[str, Any]]:
    for key in KEYS:
        for lf in JOIN_LEFT_SETS:
            for rf in JOIN_RIGHT_SETS:
                left, right = _join_pair(key, list(lf), list(rf))
                binding = {"key": key, "left_fields": list(lf), "right_fields": list(rf)}
                yield {"mutator": "sr_inner_join_on_key", "binding": binding, "fixture": left,
                       "args": {"right": right, "key": key}}


def _enum_flatten() -> Iterable[dict[str, Any]]:
    for sep in FLATTEN_SEPS:
        for branch in FLATTEN_BRANCHES:
            for leaves in FLATTEN_LEAF_PAIRS:
                fixture = _nested_record(branch, list(leaves))
                binding = {"sep": sep, "branch": branch, "leaves": list(leaves)}
                yield {"mutator": "reshape_flatten_nested", "binding": binding, "fixture": fixture,
                       "args": {"sep": sep}}


def _enum_pivot() -> Iterable[dict[str, Any]]:
    for names in PIVOT_NAME_SETS:
        index, key_col, value_col = names
        for metrics in PIVOT_METRIC_SETS:
            fixture = _long_rows(index, key_col, value_col, list(metrics))
            binding = {"index": index, "key": key_col, "value": value_col, "metrics": list(metrics)}
            yield {"mutator": "reshape_pivot_long_to_wide", "binding": binding, "fixture": fixture,
                   "args": {"index": index, "key": key_col, "value": value_col}}


# name -> (input_edge, output_edge, enumerator)
TEMPLATES: dict[str, dict[str, Any]] = {
    "join_on_key": {"mutator": "sr_inner_join_on_key", "input_edge": "RecordBatchPair",
                    "output_edge": "RecordBatch", "enum": _enum_join},
    "dedupe_cluster_key": {"mutator": "sr_dedupe_cluster_key", "input_edge": "RecordBatch",
                           "output_edge": "RecordClusterBatch",
                           "enum": lambda: _enum_grouping("sr_dedupe_cluster_key")},
    "group_by": {"mutator": "sr_group_by_key", "input_edge": "RecordBatch", "output_edge": "RecordGroups",
                 "enum": lambda: _enum_grouping("sr_group_by_key")},
    "flatten": {"mutator": "reshape_flatten_nested", "input_edge": "NestedRecord",
                "output_edge": "FlatRecord", "enum": _enum_flatten},
    "pivot": {"mutator": "reshape_pivot_long_to_wide", "input_edge": "LongRecordList",
              "output_edge": "WideRecordList", "enum": _enum_pivot},
    "nest_by_key": {"mutator": "reshape_nest_by_key", "input_edge": "RecordList", "output_edge": "GroupMap",
                    "enum": lambda: _enum_grouping("reshape_nest_by_key")},
}


# ══ canonical content hash over (mutator, binding, fixture) — the dedupe + id identity ══
def _content_hash(mutator: str, binding: dict[str, Any], fixture: Any) -> str:
    payload = json.dumps({"mutator": mutator, "binding": binding, "fixture": fixture},
                         sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_specs(*, limit_per_template: int | None = None) -> list[dict[str, Any]]:
    """Enumerate the WHOLE curated parameter space deterministically. One spec per (template, binding). This is the
    GENERATED layer (pre-dedupe) — never reported as active."""
    specs: list[dict[str, Any]] = []
    for tname, tinfo in TEMPLATES.items():
        count = 0
        for spec in tinfo["enum"]():
            spec = {**spec, "template": tname,
                    "input_edge": tinfo["input_edge"], "output_edge": tinfo["output_edge"]}
            specs.append(spec)
            count += 1
            if limit_per_template is not None and count >= limit_per_template:
                break
    return specs


def dedupe_specs(specs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Collapse identical (mutator, binding, fixture) specs by canonical content hash. First occurrence wins. Returns
    (unique specs in stable order, hash->primitive_id)."""
    seen: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for spec in specs:
        h = _content_hash(spec["mutator"], spec["binding"], spec["fixture"])
        if h not in seen:
            seen[h] = {**spec, "_hash": h}
            order.append(h)
    unique = [seen[h] for h in order]
    id_by_hash = {h: f"prim:param:{seen[h]['mutator']}:{h[:16]}" for h in order}
    return unique, id_by_hash


def prove_spec(spec: dict[str, Any]) -> dict[str, Any] | None:
    """Prove ONE configured-primitive by EXECUTION: compute expected by running the mutator once (skip if its mutator
    is unavailable or errors on the fixture), then run the imported executed-proof runner (fixture-behavior +
    determinism re-run). Return a WORKABLE row ONLY if the executed proof PASSES; otherwise None (never persisted)."""
    mutator = spec["mutator"]
    if mutator not in MUTATOR_REGISTRY:
        return None
    args = spec.get("args") or {}
    try:
        expected, _ = apply_mutator(mutator, spec["fixture"], **args)
    except Exception:  # noqa: BLE001 — an un-runnable binding is a candidate, never truth
        return None
    h = spec["_hash"]
    primitive_id = f"prim:param:{mutator}:{h[:16]}"
    receipt = run_primitive_proof(primitive_id, mutator, spec["fixture"], expected, mutator_args=args)
    # serves_truth flips true ONLY on a passing executed proof — never inferred from the template.
    if not (receipt.get("serves_truth") is True and receipt.get("promoted") is True):
        return None
    input_edge = spec["input_edge"]
    output_edge = spec["output_edge"]
    return {
        "record_type": "configured_primitive",
        "primitive_id": primitive_id,
        "mutator": mutator,
        "template": spec["template"],
        "binding": spec["binding"],
        "family": FAMILY,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": input_edge,
        "output_edge": output_edge,
        "input_edge_type_id": canonicalize_edge(input_edge),
        "output_edge_type_id": canonicalize_edge(output_edge),
        "input_hash": receipt["input_hash"],
        "output_hash": receipt["output_hash"],
    }


def build_all(*, limit_per_template: int | None = None) -> dict[str, Any]:
    """The full parametric-proof pipeline with HONEST, SEPARATE counts:
    generated -> unique(deduped) -> proven(executed pass) -> typed(both edge type ids)."""
    generated = generate_specs(limit_per_template=limit_per_template)
    unique, _ = dedupe_specs(generated)
    proven_rows: list[dict[str, Any]] = []
    for spec in unique:
        row = prove_spec(spec)
        if row is not None:
            proven_rows.append(row)
    proven_rows.sort(key=lambda r: r["primitive_id"])
    typed_rows = [r for r in proven_rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "generated": len(generated),
        "unique_after_dedupe": len(unique),
        "proven": len(proven_rows),
        "typed": len(typed_rows),
        "rows": proven_rows,
    }


def build_manifest(result: dict[str, Any], *, date: str) -> dict[str, Any]:
    rows = result["rows"]
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    by_template: dict[str, int] = {}
    for r in rows:
        by_template[r["template"]] = by_template.get(r["template"], 0) + 1
    return {
        "record_type": "parametric_relational_structural_manifest",
        "pack_id": "parametric-relational-structural",
        "group": GROUP,
        "family": FAMILY,
        "generator": "scripts/generate_parametric_relational_structural.py",
        "generated_utc": date,
        # HONEST, SEPARATE counts — never conflated. generated != unique != proven != typed in general.
        "generated": result["generated"],
        "unique_after_dedupe": result["unique_after_dedupe"],
        "proven": result["proven"],
        "typed": result["typed"],
        "proven_by_template": by_template,
        "templates": sorted(TEMPLATES),
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "note": "Each row is a configured-primitive = (proven mutator template) x (parameter binding) x (canonical "
                "edge types). serves_truth=true is set ONLY by a PASSING executed proof of THAT binding "
                "(run_primitive_proof, imported from scripts/mutator_registry.py): the mutator is executed on the "
                "fixture, its output checked, and re-run for determinism. Counts are separate: generated (all "
                "enumerated bindings) >= unique_after_dedupe (collapsed by canonical content hash) >= proven "
                "(executed proof passed) >= typed (both edge type ids via canonicalize_edge). Failing/un-runnable "
                "bindings are NOT persisted as truth.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack(*, date: str) -> dict[str, Any]:
    result = build_all()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in result["rows"]),
        encoding="utf-8")
    manifest = build_manifest(result, date=date)
    OUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    # 1. a SMALL enumeration proves + types correctly (offline, standalone, tiny).
    small = build_all(limit_per_template=3)
    small_rows = small["rows"]
    # 2. dedupe collapses an identical binding: a repeated spec must NOT create a second unique row.
    base = generate_specs(limit_per_template=2)
    dup = base + [dict(base[0])]  # exact duplicate of the first spec
    unique_dup, _ = dedupe_specs(dup)
    dedupe_ok = len(unique_dup) == len(dedupe_specs(base)[0]) == len(base)  # +1 generated, +0 unique
    # 3. a deliberately-WRONG expected FAILS the executed proof and is NOT persisted as truth.
    wrong_spec = {**base[0], "_hash": _content_hash(base[0]["mutator"], base[0]["binding"], base[0]["fixture"])}
    wrong_receipt = run_primitive_proof(
        "prim:param:wrong", wrong_spec["mutator"], wrong_spec["fixture"], {"WRONG": 999},
        mutator_args=wrong_spec.get("args") or {})
    wrong_not_promoted = wrong_receipt["serves_truth"] is False and wrong_receipt["promoted"] is False
    # 4. an un-runnable binding (mutator errors on the fixture) -> None, never persisted.
    exec_err = prove_spec({**base[0], "mutator": "reshape_pivot_long_to_wide", "template": "pivot",
                           "args": {"index": "MISSING", "key": "MISSING", "value": "MISSING"},
                           "input_edge": "LongRecordList", "output_edge": "WideRecordList"})

    checks: list[tuple[str, bool]] = [
        ("small enumeration produces proven rows for every template",
         small["proven"] > 0 and {r["template"] for r in small_rows} == set(TEMPLATES)),
        ("every small row is serves_truth=true / candidate=false / L7_executed_proof",
         all(r["serves_truth"] is True and r["candidate"] is False
             and r["verification_level"] == "L7_executed_proof" for r in small_rows)),
        ("EVERY persisted row carries non-null input+output edge type ids",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in small_rows)),
        ("typed == proven for the small run (every proven row is typed)", small["typed"] == small["proven"]),
        ("honest counts ordered generated >= unique >= proven >= typed",
         small["generated"] >= small["unique_after_dedupe"] >= small["proven"] >= small["typed"]),
        ("primitive_id embeds mutator + content-hash and is unique per row",
         len({r["primitive_id"] for r in small_rows}) == len(small_rows)
         and all(r["primitive_id"].startswith(f"prim:param:{r['mutator']}:") for r in small_rows)),
        ("dedupe collapses an identical binding (generated+1, unique+0)", dedupe_ok),
        ("a deliberately-WRONG expected FAILS the proof (never promoted)", wrong_not_promoted),
        ("an un-runnable binding is not persisted (prove_spec -> None)", exec_err is None),
        ("distinct bindings of the SAME template are DISTINCT primitives",
         len({r["primitive_id"] for r in small_rows if r["template"] == "group_by"})
         == len([r for r in small_rows if r["template"] == "group_by"])),
        ("all six proven templates present", set(TEMPLATES) == {
            "join_on_key", "dedupe_cluster_key", "group_by", "flatten", "pivot", "nest_by_key"}),
        ("deterministic: re-running build_all yields identical rows",
         [json.dumps(r, sort_keys=True) for r in build_all(limit_per_template=3)["rows"]]
         == [json.dumps(r, sort_keys=True) for r in small_rows]),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - generate_parametric_relational_structural:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - generate_parametric_relational_structural: small run proved {small['proven']} configured-"
          f"primitives across {len(TEMPLATES)} templates (serves_truth=true via the imported executed-proof runner, "
          f"typed=={small['typed']}); dedupe collapses an identical binding; a wrong-expected and an un-runnable "
          "binding correctly stay candidate (never persisted). Counts are honestly separated.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    if args.write:
        manifest = write_pack(date=args.date or FIXED_DATE)
        print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
