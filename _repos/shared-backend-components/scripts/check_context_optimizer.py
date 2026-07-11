#!/usr/bin/env python3
"""scripts.check_context_optimizer — PROOF for _repos/baltor/backend/src/baltor/context_audit/optimizer (the Context Optimizer).

Applies a ContextAuditReport to produce an optimized context view, and asserts the apply is LOSSLESS:
  A. SMALLER VIEW — the optimized bundle has fewer sources and fewer tokens than the raw bundle.
  B. DUPLICATE DROPPED — a near-duplicate is removed from the view (and recorded in `dropped`).
  C. CONFLICT RESOLVED — the conflict loser is superseded (removed from the view, recorded in `superseded`),
     the winner stays and is annotated `_audit.contested_by` (the contested info survives in the view).
  D. LOSSLESS — `sources` is unmutated; every dropped/superseded id is present in `raw`; rehydrate() returns
     the EXACT original bundle (the apply is reversible).
  E. FLAG-NOT-DROP — tool_bloat + stale sources stay in the view, annotated (not removed).
  F. GOVERNED — applied=True AND lossless=True; output is a derived view, not truth (no is_truth flag);
     deterministic (two applies identical); no raw secrets.

Deterministic, offline, stdlib-only. Exit 0/1. `--self-test` runs the gate (also the default body).
"""
from __future__ import annotations

import copy
import json
import re
import sys

from src.baltor.context_audit import apply_manifest, audit, rehydrate
from src.baltor.context_audit.context_auditor import _fixture

_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,})")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    src = _fixture()
    before = copy.deepcopy(src)
    rep = audit(src)
    opt = apply_manifest(src, rep)
    opt_ids = [s["id"] for s in opt["optimized"]]

    # A. smaller view
    ck("A: optimized has fewer sources than raw", len(opt["optimized"]) < len(src), f'{len(opt["optimized"])} < {len(src)}')
    ck("A: optimized has fewer tokens than raw", opt["optimized_tokens"] < opt["original_tokens"],
       f'{opt["optimized_tokens"]} < {opt["original_tokens"]}')

    # B. duplicate dropped (fixture: rag:chunk_17 vs rag:chunk_22 → newer chunk_17 kept, chunk_22 dropped)
    ck("B: a duplicate was dropped", len(opt["dropped"]) >= 1, str(opt["dropped"]))
    ck("B: dropped 'rag:chunk_22' (older), kept 'rag:chunk_17'",
       any(d["id"] == "rag:chunk_22" and d["kept"] == "rag:chunk_17" for d in opt["dropped"]))
    ck("B: dropped source is gone from the optimized view", "rag:chunk_22" not in opt_ids)

    # C. conflict resolved — loser superseded, winner kept + annotated
    ck("C: conflict loser 'memory:auth_2025_10' superseded", any(s["id"] == "memory:auth_2025_10" for s in opt["superseded"]))
    ck("C: superseded loser removed from the view", "memory:auth_2025_10" not in opt_ids)
    winner = next((s for s in opt["optimized"] if s["id"] == "memory:auth_2026_02"), None)
    ck("C: winner 'memory:auth_2026_02' (RS256) kept", winner is not None)
    ck("C: winner annotated _audit.contested_by", bool(winner) and "memory:auth_2025_10" in (winner.get("_audit", {}).get("contested_by") or []))

    # D. LOSSLESS
    ck("D: input sources unmutated", src == before)
    raw_ids = {s["id"] for s in opt["raw"]}
    ck("D: every dropped/superseded id retained in raw",
       all(d["id"] in raw_ids for d in opt["dropped"]) and all(s["id"] in raw_ids for s in opt["superseded"]))
    ck("D: rehydrate() returns the EXACT original bundle (reversible)", rehydrate(opt) == before)

    # E. flag-not-drop for tool_bloat + stale
    bloat = next((s for s in opt["optimized"] if s["id"] == "mcp:github"), None)
    ck("E: tool_bloat source kept + annotated", bool(bloat) and "tool_bloat" in (bloat.get("_audit") or {}))
    stale = next((s for s in opt["optimized"] if s["id"] == "doc:policy_old"), None)
    ck("E: stale source kept + annotated", bool(stale) and "stale" in (stale.get("_audit") or {}))

    # G. poisoning → QUARANTINED (removed from the optimized view, retained in raw — lossless)
    ck("G: poisoned untrusted source quarantined", any(q["id"] == "tool:web_fetch" for q in opt.get("quarantined", [])))
    ck("G: quarantined source removed from the optimized view", "tool:web_fetch" not in opt_ids)
    ck("G: quarantined source retained in raw (lossless)", "tool:web_fetch" in raw_ids)

    # F. governed
    ck("F: applied=True AND lossless=True", opt["applied"] is True and opt["lossless"] is True)
    ck("F: not labelled truth", '"is_truth": true' not in json.dumps(opt) and "served_fact" not in json.dumps(opt))
    ck("F: deterministic — re-apply is identical", apply_manifest(_fixture(), audit(_fixture())) == opt)
    ck("F: no raw keys", not _KEY_RE.search(json.dumps(opt)))

    print("\n" + ("PASS — check_context_optimizer: applies the audit manifest into a smaller optimized view "
                  "(duplicates dropped, conflict losers superseded + winner annotated, bloat/stale flagged) while "
                  "preserving the raw bundle + lineage and rehydrating EXACTLY — lossless, deterministic, output "
                  "is a derived view not truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_context_optimizer.py --self-test")
    raise SystemExit(0)
