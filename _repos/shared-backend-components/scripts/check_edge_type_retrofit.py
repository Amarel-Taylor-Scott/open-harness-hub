#!/usr/bin/env python3
"""scripts.check_edge_type_retrofit — verify the edge-type-retrofit pack is internally consistent + honest.

Validates that the pack emitted by `build_edge_type_retrofit.py` (1) recomputes to its recorded `content_sha256`
and row_counts, (2) every `edge_type_map` row's `canonical_type_id` is the value `canonicalize_edge` returns for its
raw string AND is a defined `canonical_types` row, (3) source/sink flags agree with producer/consumer counts,
(4) majority-coverage recomputes to the manifest number and exceeds 0.5, (5) the candidate/serves_truth boundary
holds on every row. Reuses the builder's pure functions so the check and the build share ONE source of truth.

Offline + deterministic. `--self-test` validates the checker logic on an in-memory fixture pack (no disk needed);
plain run validates the on-disk pack (fails cleanly if it was never written). Prints PASS/FAIL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts import build_edge_type_retrofit as builder  # noqa: E402

PACK_DIR = builder.PACK_DIR


def _content_sha(pack: dict[str, list[dict[str, Any]]]) -> str:
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False)
                          for n in sorted(pack) for r in pack[n])
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_pack(pack: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Return a list of failure strings (empty == valid). Pure; used by both the self-test and the disk check."""
    problems: list[str] = []
    map_rows = pack.get("edge_type_map.jsonl", [])
    type_rows = pack.get("canonical_types.jsonl", [])
    if not map_rows or not type_rows:
        return ["pack is missing edge_type_map.jsonl or canonical_types.jsonl rows"]

    by_id = {r["type_id"]: r for r in type_rows}

    # (1) every map row canonicalizes consistently with the importable function AND targets a defined type
    for r in map_rows:
        raw = r["raw_edge_string"]
        expected = builder.canonicalize_edge(raw)
        if r["canonical_type_id"] != expected:
            problems.append(f"map row {raw!r}: stored {r['canonical_type_id']!r} != canonicalize_edge {expected!r}")
            break
        if r["canonical_type_id"] not in by_id:
            problems.append(f"map row {raw!r}: canonical type {r['canonical_type_id']!r} not in canonical_types")
            break

    # (2) canonical_types aggregates must equal the aggregation of the map rows
    agg_occ: dict[str, int] = {}
    agg_prod: dict[str, int] = {}
    agg_cons: dict[str, int] = {}
    agg_members: dict[str, int] = {}
    for r in map_rows:
        c = r["canonical_type_id"]
        agg_occ[c] = agg_occ.get(c, 0) + r["occurrence_count"]
        agg_prod[c] = agg_prod.get(c, 0) + r["as_output_count"]
        agg_cons[c] = agg_cons.get(c, 0) + r["as_input_count"]
        agg_members[c] = agg_members.get(c, 0) + 1
    for c, tr in by_id.items():
        if tr["occurrence_count"] != agg_occ.get(c):
            problems.append(f"type {c!r}: occurrence_count {tr['occurrence_count']} != map sum {agg_occ.get(c)}")
            break
        if tr["member_raw_strings_count"] != agg_members.get(c):
            problems.append(f"type {c!r}: member count mismatch")
            break
        # (3) source/sink flags must agree with producer/consumer counts
        exp_source = agg_prod.get(c, 0) == 0 and agg_cons.get(c, 0) > 0
        exp_sink = agg_cons.get(c, 0) == 0 and agg_prod.get(c, 0) > 0
        if tr["is_source"] != exp_source or tr["is_sink"] != exp_sink:
            problems.append(f"type {c!r}: source/sink flags disagree with producer/consumer counts")
            break

    # (4) majority-coverage recomputes and exceeds 0.5
    cov, _total = builder.majority_coverage(type_rows)
    if not cov > 0.5:
        problems.append(f"majority-coverage {cov:.4f} is not > 0.5")

    # (5) boundary held
    if not all(r.get("candidate") is True and r.get("serves_truth") is False
               for rows in pack.values() for r in rows):
        problems.append("candidate/serves_truth boundary violated on some row")

    return problems


def _load_disk_pack() -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    pack: dict[str, list[dict[str, Any]]] = {}
    for name in ("edge_type_map.jsonl", "canonical_types.jsonl"):
        path = PACK_DIR / name
        pack[name] = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest = json.loads((PACK_DIR / "manifest.json").read_text(encoding="utf-8"))
    return pack, manifest


def check_disk() -> int:
    if not (PACK_DIR / "manifest.json").exists():
        print(f"FAIL - edge_type_retrofit pack not found at {PACK_DIR} "
              f"(run: python3 scripts/build_edge_type_retrofit.py --write)")
        return 1
    pack, manifest = _load_disk_pack()
    problems = validate_pack(pack)

    # manifest agreement
    row_counts = {n: len(r) for n, r in pack.items()}
    if manifest.get("row_counts") != row_counts:
        problems.append(f"manifest row_counts {manifest.get('row_counts')} != actual {row_counts}")
    if manifest.get("content_sha256") != _content_sha(pack):
        problems.append("manifest content_sha256 does not recompute from pack rows")
    cov, total = builder.majority_coverage(pack["canonical_types.jsonl"])
    if round(cov, 6) != manifest.get("majority_coverage"):
        problems.append(f"manifest majority_coverage {manifest.get('majority_coverage')} != recomputed {round(cov, 6)}")
    if manifest.get("canonical_type_count") != len(pack["canonical_types.jsonl"]):
        problems.append("manifest canonical_type_count mismatch")

    if problems:
        print("FAIL - edge_type_retrofit (disk):\n  " + "\n  ".join(problems))
        return 1
    print(f"PASS - edge_type_retrofit (disk): {manifest['distinct_raw_edge_strings']} raw edge strings -> "
          f"{manifest['canonical_type_count']} canonical types, majority-coverage={cov:.3f} over {total} "
          f"occurrences; sha256 + row_counts + source/sink flags + boundary all verified.")
    return 0


def self_test() -> int:
    # in-memory fixture pack (no disk): build from the builder's frozen sample and validate the CHECKER logic
    inc = {r: i for r, i, _o in builder.FROZEN_SAMPLE}
    outc = {r: o for r, _i, o in builder.FROZEN_SAMPLE}
    good = builder.build_pack_from_counts(inc, outc)
    checks: list[tuple[str, bool]] = [("valid pack passes validate_pack", not validate_pack(good))]

    # a tampered canonical_type_id must be caught
    import copy
    bad = copy.deepcopy(good)
    bad["edge_type_map.jsonl"][0]["canonical_type_id"] = "WrongType"
    checks.append(("tampered canonical_type_id is caught", bool(validate_pack(bad))))

    # a flipped boundary must be caught
    bad2 = copy.deepcopy(good)
    bad2["canonical_types.jsonl"][0]["serves_truth"] = True
    checks.append(("flipped serves_truth is caught", bool(validate_pack(bad2))))

    # a corrupted source/sink flag must be caught
    bad3 = copy.deepcopy(good)
    bad3["canonical_types.jsonl"][0]["is_sink"] = not bad3["canonical_types.jsonl"][0]["is_sink"]
    checks.append(("corrupted source/sink flag is caught", bool(validate_pack(bad3))))

    # sha recomputation is stable
    checks.append(("content_sha stable", _content_sha(good) == _content_sha(good)))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - check_edge_type_retrofit self-test:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - check_edge_type_retrofit self-test: validate_pack accepts a good pack and rejects tampered "
          "canonical ids, flipped boundaries, and corrupted source/sink flags.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    return check_disk()


if __name__ == "__main__":
    raise SystemExit(main())
