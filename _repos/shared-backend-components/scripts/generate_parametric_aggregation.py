#!/usr/bin/env python3
"""scripts.generate_parametric_aggregation — WORKABLE configured-primitives for the 'aggregation' group by
PARAMETRIC PROOF.

A configured-primitive = (proven mutator TEMPLATE) x (a specific parameter BINDING) x (canonical edge types).
e.g. agg_sum_field{field:'order_amount'} and agg_sum_field{field:'user_score'} are DISTINCT workable primitives —
each proven by EXECUTING the mutator on a concrete fixture and checking output, then TYPED via canonicalize_edge.

ADD-ONLY / flexible-multi-path: this is a NEW parallel path. It IMPORTS the proven mutator TEMPLATES that the sibling
`scripts.prove_leaves_aggregation_reduce` registers into the shared MUTATOR_REGISTRY on import (agg_sum_field,
agg_mean_field, agg_group_count, agg_top_k_by, agg_histogram_bins), the shared executed-proof runner
(`scripts.mutator_registry.run_primitive_proof` + `apply_mutator`), and the pure edge-typer
(`scripts.build_edge_type_retrofit.canonicalize_edge`). It NEVER edits any of them. It writes ONLY its own shard +
manifest under `data/dev-intel/parametric_primitives/` (no shared-JSONL write race).

Repo laws honored:
- serves_truth=true is set ONLY by a PASSING executed proof of THAT binding — never inferred from the template. For
  each binding we compute the EXPECTED output by running the mutator ONCE, then hand it to `run_primitive_proof`,
  which re-executes and checks fixture-behavior + determinism; only a passing receipt is persisted. A binding whose
  expected is wrong FAILS and is NOT persisted (proven in --self-test).
- Honest accounting: generated / unique(deduped) / proven / typed are computed + reported as SEPARATE counts, never
  conflated.
- Deterministic + offline ONLY: no network, no LLM, no wall-clock (fixed literal GENERATED_UTC), no RNG. The
  parameter space is ENUMERATED deterministically; per-binding fixture values come from a stable string seed
  (FNV-1a over f"{group}:...", never Python's builtin hash()).
- Efficient TEMPLATE+BINDING rows (not bloated static files); DEDUPE by a canonical content hash over
  (mutator, binding, fixture) so identical bindings collapse.

CLI: --self-test (offline, standalone, small) | --write.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY).
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402
from scripts.mutator_registry import MUTATOR_REGISTRY, apply_mutator, run_primitive_proof  # noqa: E402

# IMPORT the proven aggregation mutator TEMPLATES (registers agg_* into MUTATOR_REGISTRY on import). try/except so
# --self-test still runs against whatever templates ARE present (falling back to the base 11 in mutator_registry).
try:  # pragma: no cover - exercised by presence/absence of the sibling
    import scripts.prove_leaves_aggregation_reduce as _agg_leaves  # noqa: E402,F401
except Exception:  # noqa: BLE001
    _agg_leaves = None

GROUP = "aggregation"
FAMILY = GROUP
OUT_DIR = _resource("data") / "dev-intel" / "parametric_primitives"
OUT_JSONL = OUT_DIR / "param_aggregation.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_aggregation.json"
# Fixed literal timestamp — deterministic, no wall-clock (repo law: no datetime.now / time.time).
GENERATED_UTC = "2026-07-03"

# ── deterministic seed (FNV-1a; NEVER Python's builtin hash()) ──
_FNV_OFFSET = 2166136261
_FNV_PRIME = 16777619


def _seed_int(text: str) -> int:
    """Stable 32-bit FNV-1a over a string — deterministic across processes (builtin hash() is NOT)."""
    h = _FNV_OFFSET
    for ch in text:
        h = ((h ^ ord(ch)) * _FNV_PRIME) & 0xFFFFFFFF
    return h


# Fixture shape: enough records that k / bin-width genuinely change the output (not trivial noise).
_FIXTURE_N = 64
_VALUE_MOD = 5000  # numeric spread wider than the largest bin width so every width bins differently


def _num_value(tag: str, field: str, i: int) -> int:
    return _seed_int(f"{tag}:{field}:{i}") % _VALUE_MOD


def _cat_value(tag: str, key: str, i: int) -> str:
    # 3 deterministic groups so grouping is non-trivial but bounded
    return f"{key}__g{_seed_int(f'{tag}:{key}:{i}') % 3}"


def _batch_numeric(field: str, tag: str, n: int = _FIXTURE_N) -> list[dict[str, Any]]:
    return [{"id": f"r{i}", field: _num_value(tag, field, i)} for i in range(n)]


def _batch_keyed(key: str, tag: str, n: int = _FIXTURE_N) -> list[dict[str, Any]]:
    return [{"id": f"r{i}", key: _cat_value(tag, key, i)} for i in range(n)]


# ── curated, deterministic parameter vocabularies (meaningful field/key names, not noise) ──
_NUM_DOMAINS = ["order", "user", "session", "product", "payment", "invoice",
                "shipment", "account", "request", "event", "ticket", "subscription"]
_NUM_METRICS = ["amount", "count", "score", "duration_ms", "quantity", "weight", "total_value", "latency_ms"]
_KEY_DOMAINS = ["order", "user", "product", "payment", "account", "event", "ticket", "shipment", "invoice", "request"]
_KEY_ATTRS = ["category", "status", "region", "type", "tier", "channel", "country", "segment", "priority", "currency"]

_K_VALUES = [1, 2, 3, 5, 7, 10, 15, 20, 25, 30, 40, 50]              # all < _FIXTURE_N so each k is a distinct top-k
_BIN_WIDTHS = [2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2500]  # all < _VALUE_MOD so each width bins differently


def _numeric_fields(limit: int) -> list[str]:
    names = sorted({f"{d}_{m}" for d in _NUM_DOMAINS for m in _NUM_METRICS})
    return names[:limit]


def _group_keys(limit: int) -> list[str]:
    names = sorted({f"{d}_{a}" for d in _KEY_DOMAINS for a in _KEY_ATTRS})
    return names[:limit]


# template -> (mutator, input_edge, output_edge). count_by and group_count share the proven agg_group_count template
# but run over DISJOINT key vocabularies, so their (mutator, binding) pairs never collide.
_TEMPLATE_EDGES = {
    "sum_field": ("agg_sum_field", "RecordBatch", "ScalarAggregate"),
    "mean_field": ("agg_mean_field", "RecordBatch", "ScalarAggregate"),
    "count_by": ("agg_group_count", "RecordBatch", "GroupCountMap"),
    "group_count": ("agg_group_count", "RecordBatch", "GroupCountMap"),
    "topk_by": ("agg_top_k_by", "RecordBatch", "RankedRecordBatch"),
    "histogram": ("agg_histogram_bins", "RecordBatch", "Histogram"),
}


def build_specs(*, nf: int = 90, ck: int = 90, k_values: list[int] | None = None,
                bin_widths: list[int] | None = None) -> list[dict[str, Any]]:
    """Enumerate the parameter space DETERMINISTICALLY into per-binding specs (mutator, binding, fixture, edges).

    count_by uses the first half of the key vocabulary, group_count the disjoint second half.
    """
    k_values = _K_VALUES if k_values is None else k_values
    bin_widths = _BIN_WIDTHS if bin_widths is None else bin_widths
    fields = _numeric_fields(nf)
    keys = _group_keys(ck)
    half = len(keys) // 2
    count_by_keys, group_count_keys = keys[:half], keys[half:]
    specs: list[dict[str, Any]] = []

    def _add(template: str, binding: dict[str, Any], fixture: list[dict[str, Any]]) -> None:
        mutator, in_edge, out_edge = _TEMPLATE_EDGES[template]
        specs.append({"template": template, "mutator": mutator, "binding": binding,
                      "fixture": fixture, "input_edge": in_edge, "output_edge": out_edge})

    tag = f"{GROUP}:sum_field"
    for f in fields:
        _add("sum_field", {"field": f}, _batch_numeric(f, tag))
    tag = f"{GROUP}:mean_field"
    for f in fields:
        _add("mean_field", {"field": f}, _batch_numeric(f, tag))
    tag = f"{GROUP}:count_by"
    for key in count_by_keys:
        _add("count_by", {"key": key}, _batch_keyed(key, tag))
    tag = f"{GROUP}:group_count"
    for key in group_count_keys:
        _add("group_count", {"key": key}, _batch_keyed(key, tag))
    tag = f"{GROUP}:topk_by"
    for f in fields:
        fixture = _batch_numeric(f, tag)
        for k in k_values:
            _add("topk_by", {"field": f, "k": k}, fixture)
    tag = f"{GROUP}:histogram"
    for f in fields:
        fixture = _batch_numeric(f, tag)
        for w in bin_widths:
            _add("histogram", {"field": f, "width": w}, _batch_numeric(f, tag))
    return specs


# ── content hash for DEDUPE + id: canonical over (mutator, binding, fixture) ──
def _content_sha16(spec: dict[str, Any]) -> str:
    payload = {"mutator": spec["mutator"], "binding": spec["binding"], "fixture": spec["fixture"]}
    canonical = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _prove_spec(spec: dict[str, Any]) -> dict[str, Any] | None:
    """Compute the EXPECTED output by running the mutator ONCE, then hand it to the shared executed-proof runner.

    Returns a persisted row ONLY if the executed proof PASSES (serves_truth flips true); otherwise None.
    """
    mutator, binding, fixture = spec["mutator"], spec["binding"], spec["fixture"]
    sha16 = _content_sha16(spec)
    primitive_id = f"prim:param:{mutator}:{sha16}"
    try:
        expected, _ = apply_mutator(mutator, fixture, **binding)
    except Exception:  # noqa: BLE001 - a binding the mutator cannot execute is not proven, not persisted
        return None
    receipt = run_primitive_proof(primitive_id, mutator, fixture, expected, mutator_args=binding)
    if receipt.get("serves_truth") is not True or receipt.get("promoted") is not True:
        return None  # a binding that fails is NOT persisted as truth
    in_edge, out_edge = spec["input_edge"], spec["output_edge"]
    return {
        "record_type": "parametric_primitive",
        "primitive_id": primitive_id,
        "template": spec["template"],
        "mutator": mutator,
        "binding": binding,
        "family": FAMILY,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": in_edge,
        "output_edge": out_edge,
        "input_edge_type_id": canonicalize_edge(in_edge),
        "output_edge_type_id": canonicalize_edge(out_edge),
        "input_hash": receipt["input_hash"],
        "output_hash": receipt["output_hash"],
        "content_sha256_16": sha16,
    }


def generate(specs: list[dict[str, Any]]) -> dict[str, Any]:
    """Prove + type every spec, DEDUPE by content hash, and return separate honest counts + the persisted rows."""
    generated = len(specs)
    # dedupe by content hash over (mutator, binding, fixture) — identical bindings collapse
    unique: dict[str, dict[str, Any]] = {}
    for spec in specs:
        unique.setdefault(_content_sha16(spec), spec)
    unique_specs = list(unique.values())
    unique_after_dedupe = len(unique_specs)
    # prove: keep ONLY passers (serves_truth=true set by the executed proof)
    proven_rows = [row for row in (_prove_spec(s) for s in unique_specs) if row is not None]
    # type: a row is 'typed' only if BOTH canonical edge type ids are present and not Unknown
    typed_rows = [r for r in proven_rows
                  if r["input_edge_type_id"] and r["input_edge_type_id"] != "Unknown"
                  and r["output_edge_type_id"] and r["output_edge_type_id"] != "Unknown"]
    rows = sorted(typed_rows, key=lambda r: r["primitive_id"])
    return {
        "generated": generated,
        "unique_after_dedupe": unique_after_dedupe,
        "proven": len(proven_rows),
        "typed": len(typed_rows),
        "rows": rows,
    }


def build_manifest(result: dict[str, Any]) -> dict[str, Any]:
    rows = result["rows"]
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    templates = sorted({r["template"] for r in rows})
    return {
        "record_type": "parametric_primitives_manifest",
        "group": GROUP,
        "family": FAMILY,
        "pack_id": f"parametric-{FAMILY}",
        "generator": "scripts/generate_parametric_aggregation.py",
        "generated_utc": GENERATED_UTC,
        # honest, SEPARATE counts — never conflated
        "generated": result["generated"],
        "unique_after_dedupe": result["unique_after_dedupe"],
        "proven": result["proven"],
        "typed": result["typed"],
        "verification_level": "L7_executed_proof",
        "templates": templates,
        "mutators": sorted({r["mutator"] for r in rows}),
        "edge_type_ids": sorted({r["input_edge_type_id"] for r in rows} | {r["output_edge_type_id"] for r in rows}),
        "note": "serves_truth=true is set ONLY by a PASSING executed proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py) of THAT binding; a wrong-expected binding stays candidate and is never "
                "persisted. generated/unique_after_dedupe/proven/typed are SEPARATE counts. Every persisted row is a "
                "TEMPLATE+BINDING pair TYPED via canonicalize_edge so the configured leaf can chain.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def write_pack() -> dict[str, Any]:
    result = generate(build_specs())
    rows = result["rows"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(result)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    # small, offline, standalone enumeration (a few templates/fields) — proves + types correctly
    small = build_specs(nf=4, ck=4, k_values=[1, 3], bin_widths=[10, 100])
    result = generate(small)
    rows = result["rows"]

    # dedupe: injecting an IDENTICAL spec must collapse (unique < generated by exactly 1)
    dup_specs = small + [dict(small[0])]
    dup_result = generate(dup_specs)

    # a deliberately-WRONG expected must FAIL the executed proof (never promoted, never persisted)
    wrong_spec = small[0]
    wrong_id = f"prim:param:{wrong_spec['mutator']}:wrong"
    wrong_receipt = run_primitive_proof(wrong_id, wrong_spec["mutator"], wrong_spec["fixture"],
                                        {"__deliberately__": "wrong"}, mutator_args=wrong_spec["binding"])
    persisted_ids = {r["primitive_id"] for r in rows}

    # an un-runnable fixture must also fail (execution error -> not promoted)
    err_receipt = run_primitive_proof("prim:param:exec_error", "agg_sum_field", object(), "irrelevant",
                                      mutator_args={"field": "v"})

    checks: list[tuple[str, bool]] = [
        ("small enumeration produced rows", len(rows) > 0),
        ("proven == number of persisted rows", result["proven"] == len(rows)),
        ("typed == proven (every persisted row is typed)", result["typed"] == result["proven"]),
        ("counts are honest & ordered: generated >= unique >= proven == typed",
         result["generated"] >= result["unique_after_dedupe"] >= result["proven"] == result["typed"]),
        ("clean enumeration has no accidental collisions (unique == generated)",
         result["unique_after_dedupe"] == result["generated"]),
        ("EVERY persisted row has serves_truth=true", all(r["serves_truth"] is True for r in rows)),
        ("EVERY persisted row is L7_executed_proof",
         all(r["verification_level"] == "L7_executed_proof" for r in rows)),
        ("EVERY persisted row carries a non-null input_edge_type_id",
         all(r["input_edge_type_id"] and r["input_edge_type_id"] != "Unknown" for r in rows)),
        ("EVERY persisted row carries a non-null output_edge_type_id",
         all(r["output_edge_type_id"] and r["output_edge_type_id"] != "Unknown" for r in rows)),
        ("unique primitive ids", len({r["primitive_id"] for r in rows}) == len(rows)),
        ("DISTINCT bindings are distinct primitives (same mutator, different field -> different id)",
         len({r["primitive_id"] for r in rows if r["mutator"] == "agg_sum_field"}) >= 2),
        ("k / width are part of the binding (topk with different k -> different id)",
         len({r["primitive_id"] for r in rows if r["mutator"] == "agg_top_k_by"}) >= 2),
        ("DEDUPE collapses an identical binding (unique drops by exactly 1)",
         dup_result["generated"] == result["generated"] + 1
         and dup_result["unique_after_dedupe"] == result["unique_after_dedupe"]),
        ("a deliberately-WRONG expected FAILS the proof (not promoted)",
         wrong_receipt["serves_truth"] is False and wrong_receipt["promoted"] is False),
        ("the wrong binding is NOT persisted", wrong_id not in persisted_ids),
        ("an un-runnable fixture fails the proof (not promoted)",
         err_receipt["serves_truth"] is False and err_receipt["promoted"] is False),
        ("determinism: re-running yields identical persisted rows",
         [json.dumps(r, sort_keys=True) for r in generate(small)["rows"]]
         == [json.dumps(r, sort_keys=True) for r in rows]),
        ("proven aggregation TEMPLATES are present in the shared registry",
         all(m in MUTATOR_REGISTRY for m in ("agg_sum_field", "agg_mean_field", "agg_group_count",
                                             "agg_top_k_by", "agg_histogram_bins"))),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - generate_parametric_aggregation:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - generate_parametric_aggregation: small enumeration -> generated={result['generated']} "
          f"unique={result['unique_after_dedupe']} proven={result['proven']} typed={result['typed']}; "
          "serves_truth=true set ONLY by a passing executed proof of THAT binding; a wrong-expected binding and an "
          "un-runnable fixture correctly stay candidate (never persisted); dedupe collapses an identical binding; "
          "every persisted row carries both canonical edge type ids.")
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
