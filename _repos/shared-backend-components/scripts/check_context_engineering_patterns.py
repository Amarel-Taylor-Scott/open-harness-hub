#!/usr/bin/env python3
"""check_context_engineering_patterns — proof for the governed intake of LangChain's MIT 'deep agents from scratch'
course (_repos/shared-backend-components/architecture/context_engineering_patterns.json). The four patterns it teaches (plan-tracking, context
offloading, sub-agent delegation, summarization) are LEARNED as candidate techniques mapped to our descent axes +
worker buckets — never vendored, never truth. Asserts the learn-from / foil classification, candidate≠active +
serves_truth=false on every pattern, the verification wedge, and that summarization carries the lossless law.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_context_engineering_patterns.py --self-test
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DOC = os.path.join(_ROOT, "architecture", "context_engineering_patterns.json")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    with open(_DOC, encoding="utf-8") as f:
        doc = json.load(f)

    src = doc.get("source", {})
    ck("source is the MIT educational deep-agents course, classified learn-from + foil-runtime",
       src.get("license") == "MIT" and src.get("kind") == "educational"
       and src.get("intake_mode") == "learn-from-patterns" and src.get("runtime_classification") == "foil")

    pats = doc.get("patterns", [])
    expected = {"todo_plan_tracking", "context_offload_vfs", "subagent_delegation", "summarization_compression"}
    ck("the four taught patterns are captured", {p.get("id") for p in pats} == expected, str({p.get("id") for p in pats}))

    ck("every pattern maps to an existing descent axis or worker bucket",
       all(p.get("maps_to") and ("descent" in p["maps_to"] or "worker bucket" in p["maps_to"]) for p in pats))
    ck("every pattern is a CANDIDATE (never active) and never serves truth (governance holds)",
       all(p.get("candidate") is True and p.get("serves_truth") is False for p in pats))
    ck("every pattern carries a governed note", all(p.get("governed_note") for p in pats))

    # the descent framing + the verification WEDGE are explicit (this is the differentiation, not a clone)
    ck("the principle ties the patterns to the unbounded->bounded descent",
       "unbounded" in doc.get("principle", "") and "descent" in doc.get("principle", ""))
    wedge = doc.get("wedge", "").lower()
    ck("the wedge says we govern whether the managed context is TRUE/provable (not just manage it)",
       "true" in wedge and ("provable" in wedge or "verif" in wedge) and "candidate" in wedge)

    # the compression pattern must carry the lossless law (a summary is not a lossy replacement)
    summ = next((p for p in pats if p["id"] == "summarization_compression"), {})
    ck("summarization carries the LOSSLESS DISTILLATION law (answer-critical facts + source handles survive)",
       "lossless" in summ.get("governed_note", "").lower())

    # explicit non-goals: do not vendor/execute the runtime, do not let outputs serve truth
    ng = " ".join(doc.get("non_goals", [])).lower()
    ck("non-goals forbid vendoring the runtime and forbid pattern output serving truth",
       ("vendor" in ng or "pip-install" in ng) and "truth" in ng)

    ck("deterministic (re-load equals)", json.load(open(_DOC, encoding="utf-8")) == doc)

    print("\n" + ("PASS - check_context_engineering_patterns: LangChain's MIT deep-agents course is govern-ingested as "
                  "4 CANDIDATE context-engineering techniques (plan/offload/delegate/summarize) mapped to our descent "
                  "axes + worker buckets — learn-from, runtime is the foil, every output candidate≠truth, summarization "
                  "bound by the lossless law, wedge = we verify the managed context. Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_context_engineering_patterns.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
