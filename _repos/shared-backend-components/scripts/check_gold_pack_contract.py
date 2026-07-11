#!/usr/bin/env python3
"""scripts.check_gold_pack_contract — the Gold-Pack Contract (a context pack's admission test).

A context pack is not accepted for serving unless it passes this contract — STRICTER than
`schemas/context-pack.schema.json` (which is only structural). The contract enforces Baltor's
serving invariants: the agent gets the smallest SAFE, source-linked, governed pack — never a raw
dump or an unsourced claim.

Contract (on top of schema validity):
  * every claim carries >= 1 valid ctx:// source handle (source_handle_resolver.validate)
  * a 'conflicts' disclosure surface is present (conflicts disclosed/excluded, not hidden)
  * token_count <= token_budget (the pack is the SMALLEST sufficient, within budget)
  * every source handle is a valid ctx:// and none is in the restricted set (ACL)
  * policy.acl_filter_applied is true (ACL ran before the model)
  * valid_until + receipt_id + lineage present (freshness bound + audit + provenance)

Composes the shipped modules (source_handle_resolver, the context-pack schema). Deterministic +
offline. Stdlib + jsonschema. CLI:
    python3 _repos/shared-backend-components/scripts/check_gold_pack_contract.py --self-test
    python3 _repos/shared-backend-components/scripts/check_gold_pack_contract.py fixtures/context/gold-pack.example.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.source_handle_resolver import validate as _valid_handle

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
PACK_SCHEMA = _resource("schemas") / "context-pack.schema.json"


def _schema_errors(pack: dict) -> list[str]:
    from jsonschema import Draft202012Validator
    schema = json.loads(PACK_SCHEMA.read_text(encoding="utf-8"))
    return [f"schema: {e.message}" for e in Draft202012Validator(schema).iter_errors(pack)]


def check_gold_pack(pack: dict, *, restricted_handles: tuple[str, ...] = ()) -> list[str]:
    """Return the list of contract violations ([] = pack passes). Deterministic."""
    v: list[str] = []
    v.extend(_schema_errors(pack))

    handles = pack.get("source_handles") or []
    for h in handles:
        if not _valid_handle(h):
            v.append(f"source_handle not a valid ctx:// handle: {h!r}")
        if h in restricted_handles:
            v.append(f"restricted source handle present (ACL): {h!r}")

    claims = pack.get("claims") or []
    for i, c in enumerate(claims):
        chandles = c.get("source_handles") or []
        if not chandles:
            v.append(f"claim[{i}] has no source handle (unsourced claim not allowed)")
        elif not all(_valid_handle(h) for h in chandles):
            v.append(f"claim[{i}] has an invalid ctx:// source handle")

    if "conflicts" not in pack:
        v.append("missing 'conflicts' disclosure surface (conflicts must be disclosed or explicitly excluded)")

    tb, tc = pack.get("token_budget"), pack.get("token_count")
    if isinstance(tb, int) and isinstance(tc, int) and tc > tb:
        v.append(f"token_count {tc} exceeds token_budget {tb} (pack not minimal)")

    if not (pack.get("policy") or {}).get("acl_filter_applied"):
        v.append("policy.acl_filter_applied is not true (ACL must run before the model)")

    for field in ("valid_until", "receipt_id", "lineage"):
        if not pack.get(field):
            v.append(f"missing required governance field: {field}")
    return v


def _load(rel: str) -> dict:
    return json.loads((_resource(rel)).read_text(encoding="utf-8"))


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    good = _load("fixtures/context/gold-pack.example.json")
    bad = _load("fixtures/context/gold-pack.bad.example.json")

    good_v = check_gold_pack(good)
    check("gold-pack.example PASSES the contract", good_v == [], "; ".join(good_v[:3]))

    bad_v = check_gold_pack(bad)
    check("gold-pack.bad.example FAILS the contract", bool(bad_v), "expected violations")
    blob = " ".join(bad_v)
    check("  → unsourced claim caught", "no source handle" in blob)
    check("  → over-budget caught", "exceeds token_budget" in blob)
    check("  → ACL-not-applied caught", "acl_filter_applied" in blob)
    check("  → missing receipt_id/valid_until/lineage caught",
          all(f"governance field: {f}" in blob for f in ("valid_until", "receipt_id", "lineage")))

    # per-rule negatives on the good pack
    g2 = json.loads(json.dumps(good)); g2["claims"][0].pop("source_handles")
    check("removing a claim handle fails", bool(check_gold_pack(g2)))
    check("a restricted handle is rejected", bool(check_gold_pack(good, restricted_handles=("ctx://ofac/sdn",))))

    # determinism
    check("contract is deterministic", check_gold_pack(good) == check_gold_pack(good))

    print(f"\n{'all check_gold_pack_contract self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gold-Pack Contract — admission test for a context pack.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("pack", nargs="?", help="path to a context pack JSON to check")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.pack:
        v = check_gold_pack(json.loads(Path(args.pack).read_text(encoding="utf-8")))
        if v:
            print("FAIL — gold-pack contract violations:")
            print("\n".join(f"  - {x}" for x in v))
            return 1
        print("PASS — pack satisfies the gold-pack contract.")
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
