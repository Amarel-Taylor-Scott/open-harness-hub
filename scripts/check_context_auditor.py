#!/usr/bin/env python3
"""scripts.check_context_auditor — PROOF for src/baltor/context_audit (the Context Auditor MVP).

The Context Auditor emits a deterministic, auditable optimization manifest (ContextAuditReport) across ALL
context-source kinds before an LLM call. This proof asserts (a) the module's own self-test passes, and
(b) the load-bearing GOVERNANCE invariants hold on a fresh audit:
  A. the report carries the owner's manifest shape (original_tokens, estimated_optimized_tokens, issues[])
     plus the governed envelope; every issue has type∈ISSUE_TYPES, a known severity, sources, reason, action.
  B. PROPOSES, never disposes — applied is False, and the input sources are byte-identical after the audit
     (LOSSLESS: no mutation/deletion).
  C. a conflict SURFACES both sides and SUPERSEDES (never deletes) the loser; conflict is labelled a
     heuristic, not a truth verdict (output ≠ truth).
  D. single-source / no drift — SOURCE_KINDS is derived from AUTHORITY_RANK; the manifest echoes the
     authority order.
  E. no raw secrets anywhere in the manifest.

Deterministic, offline, stdlib-only. Exit 0/1. `--self-test` runs the gate (also the default body).
"""
from __future__ import annotations

import copy
import json
import re
import sys

from src.baltor.context_audit import AUTHORITY_RANK, ISSUE_TYPES, SOURCE_KINDS, audit
from src.baltor.context_audit.context_auditor import _fixture, _self_test as _module_self_test

_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,})")
_SEVERITIES = {"low", "medium", "high"}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # the module's own self-test (15 contract checks) must pass first
    ck("module self-test passes", _module_self_test() == 0)

    sources = _fixture()
    before = copy.deepcopy(sources)
    rep = audit(sources)

    # A. manifest shape
    for k in ("original_tokens", "estimated_optimized_tokens", "issues", "applied", "method",
              "authority_order", "lossless"):
        ck(f"A: manifest has '{k}'", k in rep)
    ck("A: every issue is well-formed", all(
        it.get("type") in ISSUE_TYPES and it.get("severity") in _SEVERITIES
        and it.get("sources") and it.get("reason") and it.get("action") for it in rep["issues"]),
       str([it.get("type") for it in rep["issues"]]))

    # B. proposes-not-disposes + lossless input
    ck("B: applied is False (PROPOSES, never disposes)", rep["applied"] is False)
    ck("B: LOSSLESS — input sources unchanged after audit", sources == before)

    # C. conflict surfaces both + supersedes (never deletes) + labelled heuristic
    conflicts = [it for it in rep["issues"] if it["type"] == "conflicting_context"]
    ck("C: a conflict was detected", len(conflicts) >= 1)
    if conflicts:
        c = conflicts[0]
        ck("C: conflict references >=2 sources (surfaces both)", len(c["sources"]) >= 2)
        ck("C: conflict supersedes, never deletes (lossless)", "never deleted" in c["action"])
        ck("C: conflict is evidence, not a truth verdict", "NOT a truth verdict" in c["reason"])

    # D. single-source / no drift
    ck("D: SOURCE_KINDS derived from AUTHORITY_RANK (no drift)", SOURCE_KINDS == tuple(AUTHORITY_RANK))
    ck("D: manifest echoes the authority order", rep["authority_order"] == dict(AUTHORITY_RANK))

    # E. no raw secrets
    ck("E: no raw keys in the manifest", not _KEY_RE.search(json.dumps(rep)))

    print("\n" + ("PASS — check_context_auditor: the Context Auditor emits a governed ContextAuditReport "
                  "(duplicate/conflict/bloat/stale across all source kinds), PROPOSES not disposes, is LOSSLESS "
                  "(raw untouched, conflicts surface both sides + supersede not delete), single-sourced authority, "
                  "deterministic + offline." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_context_auditor.py --self-test")
    raise SystemExit(0)
