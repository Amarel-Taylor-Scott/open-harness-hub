#!/usr/bin/env python3
"""scripts.check_baltor_governed_blackboard_demo — PROOF: ``blackboard.baltor.cfpb_evidence@v1`` serves the
AUTHORITATIVE Reg E answer with a source handle, keeps the stale contradiction HELD OUT (a warning, never served),
and is governed (serves_truth False everywhere; Teleon returns evidence, Baltor governs truth).

The demo runs the OFFLINE local stateful-swarm over the synthetic CFPB Reg E fixture (the planted facts in
``demo-data/cfpb-sample``): signals -> observations (with source handles) -> gaps -> held-out allegations (kept
SEPARATE) -> verified facts -> synthesis (reads the BOARD) -> governed answer -> receipts.

Asserts:
  A. SERVED ANSWER IS AUTHORITATIVE + SOURCED: the served answer CONTAINS "10 business days" AND a source handle
     (a ctx:// / doc# locator); the synthesis carries source_handles.
  B. HELD-OUT STAYS SEPARATE: "30 days" is present in the held-out set / held_out_values but is NOT a substring of
     the served answer (the stale contradiction is preserved as a warning, never served).
  C. SERVES_TRUTH FALSE EVERYWHERE: the run envelope, the governed projection (serves_truth const False;
     promotion_eligible False), and every stored blackboard entry carry serves_truth False.
  D. RECEIPTS PRESENT: the board carries worker receipts (provenance), and the governed entry's receipt_refs are
     non-empty.
  E. DETERMINISTIC: the same now yields the same served answer + blackboard_id.
  F. TELEON MODULE DOESN'T IMPORT src.baltor (line-anchored); no raw API key literals.

Deterministic + offline. stdlib only. Uses an in-memory blackboard, never the real .agent db. Exit 0/1.
_REPO = parents[1]; sys.path.insert. No raw keys/secrets.

CLI: PYTHONPATH=. python3 scripts/check_baltor_governed_blackboard_demo.py --self-test
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.environments.baltor_cfpb_context_governance import (  # noqa: E402
    AUTHORITATIVE_ANSWER,
    HELD_OUT_CONTRADICTION,
)
from src.teleon.stateful_swarms.cfpb_evidence_demo import (  # noqa: E402
    DEMO_ID,
    run_cfpb_evidence_demo,
)

_NOW = "2026-06-08T00:00:00Z"

# the teleon demo module + its swarm/port deps must NOT import src.baltor and carry no raw keys.
_TELEON_FILES = [
    _REPO / "src" / "teleon" / "stateful_swarms" / "cfpb_evidence_demo.py",
    _REPO / "src" / "teleon" / "stateful_swarms" / "local_swarm.py",
    _REPO / "src" / "teleon" / "ports" / "stateful_swarm_provider.py",
]
_KEY_PATTERNS = [
    re.compile(p)
    for p in (r"sk-[A-Za-z0-9]{16,}", r"AKIA[0-9A-Z]{12,}", r"AIza[0-9A-Za-z_\-]{20,}", r"gsk_[A-Za-z0-9]{16,}")
]
_BALTOR_IMPORT = re.compile(r"^\s*(from|import)\s+.*\bbaltor\b", re.MULTILINE)
# a source handle is a ctx:// resource handle or a doc# locator (mirrors BlackboardSourceRef.v1's pattern).
_SOURCE_HANDLE = re.compile(r"(ctx://|doc#)\S+")


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    r = run_cfpb_evidence_demo(now=_NOW)
    check("0 demo_id is blackboard.baltor.cfpb_evidence@v1", r["demo_id"] == DEMO_ID, r["demo_id"])

    served = r["served_answer"]

    # ── A. SERVED ANSWER IS AUTHORITATIVE + SOURCED ─────────────────────────────────────────
    check("A1 served answer contains the authoritative '10 business days'",
          AUTHORITATIVE_ANSWER in served, served)
    check("A2 served answer carries a source handle (ctx:// or doc#)",
          bool(_SOURCE_HANDLE.search(served)), served)
    check("A3 synthesis carries source_handles", len(r["served_source_handles"]) >= 1,
          str(r["served_source_handles"]))

    # ── B. HELD-OUT STAYS SEPARATE ──────────────────────────────────────────────────────────
    check("B1 the stale '30 days' is in held_out_values", HELD_OUT_CONTRADICTION in r["held_out_values"])
    check("B2 the stale '30 days' is NOT a substring of the served answer",
          HELD_OUT_CONTRADICTION not in served, served)
    # the held-out set carries the stale FAQ source handle (preserved lineage to the loser).
    check("B3 held_out set carries the stale handle/entry lineage", len(r["held_out"]) >= 1, str(r["held_out"]))
    # the held-out reason is recorded in the governance verdict (held_out != deleted).
    check("B4 governed entry records a held_out_reason (preserved as a warning)",
          bool(r["governed_entry"].get("held_out_reason")), r["governed_entry"].get("held_out_reason", ""))

    # ── C. SERVES_TRUTH FALSE EVERYWHERE ────────────────────────────────────────────────────
    check("C1 run envelope serves_truth False", r["serves_truth"] is False)
    gov = r["governed_entry"]
    check("C2 governed entry serves_truth const False", gov["serves_truth"] is False)
    check("C3 governed entry promotion_eligible False (open gaps => not promotable)",
          gov["promotion_eligible"] is False)
    check("C4 governed entry claim_status is candidate (born candidate, never auto-served)",
          gov["claim_status"] == "candidate", gov.get("claim_status", ""))
    # every stored entry (signals/observations/gaps/synthesis/analyses) is serves_truth False.
    all_kinds_serves_false = all(
        e["serves_truth"] is False
        for group in (r["signals"], r["observations"], r["gaps"], r["synthesis"])
        for e in group
    )
    check("C5 every stored entry serves_truth False", all_kinds_serves_false)

    # ── D. RECEIPTS PRESENT ─────────────────────────────────────────────────────────────────
    check("D1 board carries worker receipts (provenance)", len(r["receipts"]) >= 1, f"{len(r['receipts'])}")
    check("D2 governed entry receipt_refs non-empty", len(gov["receipt_refs"]) >= 1, str(gov["receipt_refs"]))

    # ── E. DETERMINISTIC ────────────────────────────────────────────────────────────────────
    r2 = run_cfpb_evidence_demo(now=_NOW)
    check("E1 same now -> same served answer", served == r2["served_answer"])
    check("E2 same now -> same blackboard_id", r["blackboard_id"] == r2["blackboard_id"])

    # ── F. NO BALTOR IMPORT / NO RAW KEYS ───────────────────────────────────────────────────
    baltor_hits: list[str] = []
    key_hits: list[str] = []
    for f in _TELEON_FILES:
        src = f.read_text()
        if _BALTOR_IMPORT.search(src):
            baltor_hits.append(f.name)
        for pat in _KEY_PATTERNS:
            if pat.search(src):
                key_hits.append(f.name)
    check("F1 teleon demo + deps do not import src.baltor (line-anchored)", not baltor_hits, str(baltor_hits))
    check("F2 no raw API key literal in the teleon demo + deps", not key_hits, str(key_hits))

    if fails:
        print(f"\ncheck_baltor_governed_blackboard_demo: FAIL ({len(fails)} failed)")
        return 1
    print("\nPASS — check_baltor_governed_blackboard_demo: served answer = '10 business days' + a source handle; the "
          "held-out '30 days' is preserved as a warning but is NOT in the served answer; serves_truth False "
          "everywhere (run/governed/entries); receipts present; Teleon returns evidence + a non-promotable candidate "
          "(Baltor governs truth); deterministic; no src.baltor import; no raw keys.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="offline self-test for the Baltor governed-blackboard CFPB demo")
    ap.add_argument("--self-test", action="store_true", help="run the offline self-test (default)")
    ap.parse_args()
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
