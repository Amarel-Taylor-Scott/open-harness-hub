#!/usr/bin/env python3
"""check_teleon_impl_finder — proof for the deterministic-implementation finder.

When a capability is entered, it searches for a MORE-DETERMINISTIC / more-efficient implementation:
  * INTERNAL — matches the corpus by intent (CROSS-category: a deterministic library can implement an LLM task);
    an LLM 'parse dates from text' (ceiling 0.3) finds the deterministic dateparser library (ceiling 1.0) and
    recommends replacing the model with it (the distillation win, grounded in a real impl).
  * ranks candidates by determinism; flags the ones MORE deterministic than the input; an already-deterministic
    capability gets 'no more-deterministic impl needed'; unrelated capabilities are not matched.
  * EXTERNAL search is a governed seam — OFF by default (routes through the discovery pipeline); enabled only with
    allow_external + a configured ExternalImplSearchPort.
  * deterministic; proposes, never disposes; never serves truth.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_impl_finder.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution import ExternalImplSearchPort, find_implementations


def _cap(slot, category, intent, ceiling, cov=0.9):
    return {"capability_slot": slot, "category": category, "intent": intent,
            "determinism_ceiling": ceiling, "deterministic_coverage_estimate": cov}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    corpus = [
        _cap("extract-dates-llm", "research", "parse and extract dates from text", 0.3, 0.4),
        _cap("dateparser-library", "data-extraction", "parse dates from text deterministically", 1.0, 0.95),
        _cap("arrow-datetime-library", "data-extraction", "parse and format dates and times", 1.0, 0.9),
        _cap("geocode-address", "geo-weather", "convert an address to coordinates", 0.95, 0.9),
        _cap("stock-quote", "market-data", "fetch a live stock price quote", 1.0, 1.0),
    ]
    target = corpus[0]  # the LLM date parser — we want to find a deterministic replacement

    res = find_implementations(target, corpus)
    ck("the finder matches same-need capabilities CROSS-category (LLM date-parse -> deterministic date libraries)",
       {m["capability_slot"] for m in res["internal_matches"]} >= {"dateparser-library", "arrow-datetime-library"},
       str([m["capability_slot"] for m in res["internal_matches"]]))
    ck("it flags the MORE-deterministic implementations (the distillation wins)",
       res["more_deterministic_count"] >= 2 and all(m["determinism_ceiling"] > 0.3 for m in res["internal_matches"]))
    ck("the best deterministic implementation is a ceiling-1.0 library, recommended as the replacement",
       res["best_deterministic_impl"]["determinism_ceiling"] == 1.0
       and "replace with the more-deterministic" in res["recommendation"], res["recommendation"])
    ck("unrelated capabilities (geocode, stock) are NOT matched", not any(
       m["capability_slot"] in ("geocode-address", "stock-quote") for m in res["internal_matches"]))
    ck("the finder proposes, never serves truth", res["serves_truth"] is False)

    # an already-deterministic capability needs no more-deterministic implementation.
    det = find_implementations(corpus[1], corpus)  # dateparser-library, ceiling 1.0
    ck("an already-deterministic capability -> 'no more-deterministic impl needed'",
       det["best_deterministic_impl"] is None and "already" in det["recommendation"], det["recommendation"])

    # a capability with no internal match -> route to external search.
    lonely = find_implementations(_cap("translate-klingon", "media", "translate english to klingon", 0.4), corpus)
    ck("a capability with no internal match is routed to external search (the discovery pipeline)",
       lonely["best_deterministic_impl"] is None and "external search" in lonely["recommendation"])

    # EXTERNAL seam: OFF by default; enabled with allow_external + a configured port.
    ck("external search is OFF by default (a governed seam)", res["external"]["searched"] is False)
    ck("allow_external without a configured port stays off (never a silent live call)",
       find_implementations(target, corpus, allow_external=True)["external"]["searched"] is False)

    class _StubExternal:  # stands in for a real registry/web search behind the port
        def search(self, capability):
            return [{"capability_slot": "ext-dateparser-rs", "determinism_ceiling": 1.0, "source": "crates.io"}]
    ck("ExternalImplSearchPort is satisfiable + a configured external search returns candidates (never truth)",
       isinstance(_StubExternal(), ExternalImplSearchPort)
       and find_implementations(target, corpus, allow_external=True, external_search=_StubExternal())["external"]["searched"] is True)

    # deterministic
    ck("the finder is deterministic (same inputs -> same result)", find_implementations(target, corpus) == res)

    print("\n" + ("PASS - check_teleon_impl_finder: on capability entry, the finder searches the corpus (cross-"
                  "category, by intent) for MORE-deterministic implementations — an LLM date-parser finds a "
                  "deterministic library and recommends replacing the model; already-deterministic capabilities "
                  "need none; unmatched ones route to external search (a governed seam, off by default behind "
                  "ExternalImplSearchPort). It proposes, never disposes; deterministic; never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
