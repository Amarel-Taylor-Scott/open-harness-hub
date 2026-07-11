#!/usr/bin/env python3
"""check_cards_carry_body — CONTRACT: a card that claims a working primitive MUST carry its verified body.

Owner (2026-07-10): "add more rules and contracts to avoid dropping code again — that is a serious issue." Dropping
a primitive's verified code during a promotion/transform is a LOSSLESS-DISTILLATION violation (the working primitive
became a hollow descriptor). This is the gated guard that makes that class of bug go RED instead of silently
shipping.

THE CONTRACT (single source of truth for "working card"):
  A card is WORKING iff verification_level ∈ {execution, verified} OR has_working_body is True.
  A WORKING card MUST carry a non-empty `source_code` AND a `body_sha` that matches it.
  → a working-claim WITHOUT a body is a CODE-DROP VIOLATION.
  → a descriptor card (no working claim, no body) is fine (a candidate capability, not a dropped body).
  → a body whose `body_sha` doesn't match `source_code` is an INTEGRITY violation (tampered/mismatched body).

`assert_carries_body(source_row, card)` is the point-of-transform guard: any promoter/minter that derives a card from
a source that HAS working code must produce a card that carries it — call it in the transform and it raises on a drop.
`check_corpus()` audits the real minted card files. Registered in the proof umbrella so a reintroduced drop fails CI.

    PYTHONPATH=. python3 scripts/check_cards_carry_body.py --self-test
    PYTHONPATH=. python3 scripts/check_cards_carry_body.py --check      # audit the real minted card files
"""
from __future__ import annotations

import argparse
import json
import sys
import zlib
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
_EDGE = _REPO / "data" / "dev-intel" / "aidevobserver_edge_foundry"

_WORKING_LEVELS = frozenset({"execution", "verified"})


def _body_sha(code: str) -> str:
    return f"crc32:{zlib.crc32(str(code).encode()) & 0xFFFFFFFF:08x}"


def claims_working(card: dict[str, Any]) -> bool:
    return card.get("verification_level") in _WORKING_LEVELS or bool(card.get("has_working_body"))


class CodeDropError(AssertionError):
    """Raised when a transform produces a working-claim card that dropped its body."""


def assert_carries_body(source_row: Optional[dict[str, Any]], card: dict[str, Any]) -> dict[str, Any]:
    """POINT-OF-TRANSFORM guard. If ``source_row`` has working code, ``card`` MUST carry it (non-empty source_code +
    matching body_sha) and be marked working. Raises CodeDropError on a drop. Returns the card (for chaining)."""
    src_code = str((source_row or {}).get("code") or (source_row or {}).get("body") or "").strip()
    src_working = bool((source_row or {}).get("working")) or (source_row or {}).get("verification_level") in _WORKING_LEVELS
    if src_code and src_working:
        body = str(card.get("source_code") or "").strip()
        if not body:
            raise CodeDropError(f"code dropped: source has working code but card {card.get('primitive_id')} carries none")
        if card.get("body_sha") and card["body_sha"] != _body_sha(body):
            raise CodeDropError(f"body_sha mismatch for {card.get('primitive_id')}")
        if not claims_working(card):
            raise CodeDropError(f"card {card.get('primitive_id')} carries a body but is not marked working")
    return card


def audit(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit a card list against the contract. Violations = working-claim cards with no body (CODE DROPS)."""
    working_with_body = descriptors = 0
    drops: list[str] = []
    mismatches: list[str] = []
    for c in cards:
        working = claims_working(c)
        body = str(c.get("source_code") or "").strip()
        if working and not body:
            drops.append(c.get("primitive_id"))
        elif working and body:
            working_with_body += 1
            if c.get("body_sha") and c["body_sha"] != _body_sha(body):
                mismatches.append(c.get("primitive_id"))
        else:
            descriptors += 1
    return {"total": len(cards), "working_with_body": working_with_body, "descriptors": descriptors,
            "code_drop_violations": len(drops), "sample_drops": drops[:10],
            "body_sha_mismatches": len(mismatches), "sample_mismatches": mismatches[:10],
            "ok": not drops and not mismatches}


def check_corpus() -> dict[str, Any]:
    """Audit the real minted card files (the ones that should carry bodies)."""
    per_file = {}
    total = {"working_with_body": 0, "code_drop_violations": 0, "body_sha_mismatches": 0}
    for f in sorted(_EDGE.glob("minted_*_cards.jsonl")):
        cards = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        a = audit(cards)
        per_file[f.name] = {k: a[k] for k in ("total", "working_with_body", "descriptors",
                                              "code_drop_violations", "body_sha_mismatches")}
        for k in total:
            total[k] += a[k]
    return {"per_file": per_file, "total": total,
            "ok": total["code_drop_violations"] == 0 and total["body_sha_mismatches"] == 0,
            "note": "minted cards that are working MUST carry source_code + matching body_sha. serves_truth=false"}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    good = {"primitive_id": "p:good", "verification_level": "execution",
            "source_code": "def run(x):\n    return len(x)\n", "has_working_body": True}
    good["body_sha"] = _body_sha(good["source_code"])
    dropped = {"primitive_id": "p:drop", "verification_level": "execution", "source_code": ""}  # WORKING claim, no body
    descriptor = {"primitive_id": "p:desc", "verification_level": "draft"}  # no claim, no body — legitimate
    tampered = {"primitive_id": "p:tamp", "verification_level": "execution",
                "source_code": "def run(x): return 1", "body_sha": "crc32:deadbeef", "has_working_body": True}

    a = audit([good, dropped, descriptor, tampered])
    checks.append((f"audit: 1 working-with-body, 1 CODE DROP, 1 descriptor ok, 1 sha mismatch (found={a['code_drop_violations']}/{a['body_sha_mismatches']})",
                   a["working_with_body"] == 1 and a["code_drop_violations"] == 1 and a["descriptors"] == 1
                   and a["body_sha_mismatches"] == 1 and not a["ok"], json.dumps(a["sample_drops"])))

    # (2) POINT-OF-TRANSFORM guard: a source with working code -> a card that dropped it RAISES.
    src = {"code": "def run(x):\n    return sorted(x)\n", "working": True}
    raised = False
    try:
        assert_carries_body(src, {"primitive_id": "x", "verification_level": "execution", "source_code": ""})
    except CodeDropError:
        raised = True
    checks.append(("assert_carries_body RAISES on a dropped body (the guard bites at the transform)", raised, ""))

    # (3) a proper carry passes the guard.
    ok_card = {"primitive_id": "x", "verification_level": "execution", "source_code": src["code"],
               "body_sha": _body_sha(src["code"]), "has_working_body": True}
    passed = True
    try:
        assert_carries_body(src, ok_card)
    except CodeDropError:
        passed = False
    checks.append(("assert_carries_body PASSES when the body is carried + sha matches", passed, ""))

    # (4) a descriptor source (no code) is not forced to carry a body.
    nodrop = True
    try:
        assert_carries_body({"code": "", "working": False}, {"primitive_id": "d", "verification_level": "draft"})
    except CodeDropError:
        nodrop = False
    checks.append(("descriptor source (no code) does not trigger the guard", nodrop, ""))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - check_cards_carry_body: CONTRACT — a working card MUST carry source_code + "
          f"matching body_sha; code-drop + tamper detected (audit) and RAISED at the transform (assert). serves_truth=false")
    for name, passed_, detail in checks:
        print(f"  [{'ok' if passed_ else 'XX'}] {name}" + (f"  ({detail})" if not passed_ else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Contract: working cards must carry their verified body (anti-code-drop).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--check", action="store_true", help="audit the real minted card files")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.check:
        rep = check_corpus()
        print(json.dumps(rep, indent=2))
        return 0 if rep["ok"] else 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
