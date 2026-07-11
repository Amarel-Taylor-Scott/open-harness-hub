#!/usr/bin/env python3
"""scripts.check_multi_set_membership_index — gate the MULTI-SET membership registry.

Asserts: the on-disk pack matches the builder (freshness — hand-edits go red), the MULTI-SET invariant holds (every
cross-cutting member belongs to >=2 sets, so nothing is single-set), universal members reach EVERY set, the three
surfaces reconcile (set member-lists are the exact inverse of the edge list; edge count equals summed membership),
every edge endpoint is a known set/member, and the candidate/serves_truth boundary holds on every row. Offline,
read-only. CLI: --self-test.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.build_multi_set_membership_index import (  # noqa: E402
    PACK_DIR,
    SETS,
    MEMBERS,
    build_manifest,
    build_pack,
    self_test as builder_self_test,
)


def _fail(msg: str) -> None:
    raise AssertionError(msg)


def _load(name: str) -> list[dict]:
    return [json.loads(ln) for ln in (PACK_DIR / name).read_text(encoding="utf-8").splitlines() if ln.strip()]


def self_test() -> dict:
    if builder_self_test() != 0:
        _fail("builder self-test failed")

    # freshness: on-disk manifest must equal a freshly built manifest (hand-edits go red)
    disk_manifest = json.loads((PACK_DIR / "manifest.json").read_text(encoding="utf-8"))
    fresh = build_manifest(build_pack(), date=disk_manifest.get("generated_utc", "1970-01-01"))
    if disk_manifest.get("content_sha256") != fresh["content_sha256"]:
        _fail("pack is stale/hand-edited — regenerate via build_multi_set_membership_index.py --write")

    set_rows = _load("set_records.jsonl")
    member_rows = _load("cross_cutting_members.jsonl")
    edge_rows = _load("membership_edges.jsonl")

    set_names = {r["set"] for r in set_rows}
    member_names = {r["member_family"] for r in member_rows}
    if set_names != set(SETS):
        _fail("set_records.jsonl does not match the builder's SETS")
    if member_names != set(MEMBERS):
        _fail("cross_cutting_members.jsonl does not match the builder's MEMBERS")

    # MULTI-SET invariant on the pack as written: no member is single-set
    for r in member_rows:
        if r["set_count"] < 2 or len(r["member_of_sets"]) < 2:
            _fail(f"member {r['member_family']} is not multi-set (belongs to <2 sets)")
        if set(r["member_of_sets"]) - set_names:
            _fail(f"member {r['member_family']} references an unknown set")
        if r["universal"] and set(r["member_of_sets"]) != set_names:
            _fail(f"universal member {r['member_family']} must reference every set")

    # edges reconcile with the member rows and with the set rows (three surfaces agree)
    expected_edges = sum(r["set_count"] for r in member_rows)
    if len(edge_rows) != expected_edges:
        _fail(f"edge count {len(edge_rows)} != summed membership {expected_edges}")
    for e in edge_rows:
        if e["member_family"] not in member_names or e["set"] not in set_names:
            _fail("edge endpoint is unknown")
        if e.get("relation") != "member_of":
            _fail("edge relation must be member_of")
    edges_by_set: dict[str, set] = {}
    for e in edge_rows:
        edges_by_set.setdefault(e["set"], set()).add(e["member_family"])
    for r in set_rows:
        if set(r["member_families"]) != edges_by_set.get(r["set"], set()):
            _fail(f"set {r['set']} member list is not the inverse of the edges")
        if r["member_count"] < 1:
            _fail(f"set {r['set']} references no members")

    # boundary holds everywhere
    for rows in (set_rows, member_rows, edge_rows):
        for row in rows:
            if row.get("candidate") is not True or row.get("serves_truth") is not False:
                _fail("candidate/serves_truth boundary violated")

    return {
        "check": "multi_set_membership_index",
        "sets": len(set_rows),
        "members": len(member_rows),
        "edges": len(edge_rows),
        "universal_members": disk_manifest["universal_member_count"],
        "max_sets_per_member": disk_manifest["max_sets_per_member"],
        "candidate": True,
        "serves_truth": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.error("expected --self-test")
    print(json.dumps(self_test(), indent=2, sort_keys=True))
    print("PASS - multi_set_membership_index: fresh, every member is authored once and referenced by >=2 sets, "
          "universal members reach every set, the three surfaces reconcile, boundary holds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
