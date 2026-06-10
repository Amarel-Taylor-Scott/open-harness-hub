#!/usr/bin/env python3
"""scripts.context_debt — aggregate context-debt items into a deterministic context_debt_score.

Context debt = known gaps that degrade the governed context over time (unverified claims, stale
packs, missing source handles, unresolved conflicts, unowned objects, unbenchmarked tools, missing
harnesses, policy exceptions). This scores a LIST of context-debt-item records (validated against
schemas/context-debt-item.schema.json) into a weighted total + breakdowns — the admin/triage signal
(docs/architecture/context-debt.md). Pure/offline; the live scan that PRODUCES debt items from real
state is the seam (it would query the registries + run the gold-pack contract / scanners).

CLI:
    python3 scripts/context_debt.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
DEBT_SCHEMA = _REPO / "schemas" / "context-debt-item.schema.json"

#: Severity → weight (rationale: critical context debt is ~15x a low one; tune as evidence accrues).
SEVERITY_WEIGHTS = {"low": 1, "medium": 3, "high": 7, "critical": 15}


def context_debt_score(items: list[dict]) -> dict:
    """Weighted total + breakdowns. Deterministic pure function of the items."""
    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    score = 0
    for it in items:
        w = SEVERITY_WEIGHTS.get(it.get("severity", "low"), 1)
        score += w
        by_type[it.get("debt_type", "unknown")] = by_type.get(it.get("debt_type", "unknown"), 0) + 1
        by_severity[it.get("severity", "low")] = by_severity.get(it.get("severity", "low"), 0) + 1
    return {"context_debt_score": score, "count": len(items),
            "by_type": dict(sorted(by_type.items())), "by_severity": dict(sorted(by_severity.items()))}


def _validator():
    from jsonschema import Draft202012Validator
    return Draft202012Validator(json.loads(DEBT_SCHEMA.read_text(encoding="utf-8")))


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    v = _validator()
    fixture = json.loads((_REPO / "fixtures/context-debt-item.example.json").read_text(encoding="utf-8"))
    check("debt-item fixture is schema-valid", not list(v.iter_errors(fixture)))

    items = [
        fixture,
        {"kind": "baltor.context-debt-item.v1", "id": "d2", "debt_type": "stale_pack", "severity": "critical", "subject": "pack:x", "detected_at": "t"},
        {"kind": "baltor.context-debt-item.v1", "id": "d3", "debt_type": "unbenchmarked_tool", "severity": "low", "subject": "tool:y", "detected_at": "t"},
    ]
    for it in items:
        check(f"item {it['id']} valid", not list(v.iter_errors(it)))
    rep = context_debt_score(items)
    check("score is weighted sum (high7 + critical15 + low1 = 23)", rep["context_debt_score"] == 23, str(rep["context_debt_score"]))
    check("breakdowns present", rep["count"] == 3 and rep["by_severity"]["critical"] == 1)
    check("critical outweighs low (severity matters)", SEVERITY_WEIGHTS["critical"] > SEVERITY_WEIGHTS["low"])
    check("score is deterministic", context_debt_score(items) == context_debt_score(items))
    check("empty debt → score 0", context_debt_score([])["context_debt_score"] == 0)

    # NEGATIVE: a bad debt_type is rejected by the schema (enforcement)
    bad = dict(fixture); bad["debt_type"] = "not_a_debt_type"
    check("bad debt_type rejected", bool(list(v.iter_errors(bad))))

    print(f"\n{'all context_debt self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Aggregate context-debt items into a context_debt_score.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
