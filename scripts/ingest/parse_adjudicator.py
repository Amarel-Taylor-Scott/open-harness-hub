#!/usr/bin/env python3
"""scripts.ingest.parse_adjudicator — multi-engine parse adjudication (LOSSLESS).

For a high-value document you can run N parser engines (Docling / MinerU / Tika / MarkItDown / GROBID / ...),
score each with ``parse_quality``, and SELECT the best — but keep EVERY engine's output as evidence (the
lossless-distillation law: the losers are preserved in ``engine_runs``, never discarded, so a later reviewer can
see what each engine produced and why one won). Emits a ``ParsedDocument.v1`` carrying the WINNER's pages +
quality + the full engine_runs ledger. ``serves_truth`` pinned false (a parse is evidence, never a served fact).
Pure + deterministic: the same candidates always select the same winner. stdlib only.

CLI: python3 scripts/ingest/parse_adjudicator.py --self-test
"""
from __future__ import annotations

import argparse
import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from scripts.ingest.parse_quality import score_parse

PARSED_DOCUMENT_SCHEMA_VERSION = "ParsedDocument.v1"


class AdjudicationError(ValueError):
    """Raised when no candidate parse is supplied — fail loud, never silently emit an empty document."""


def adjudicate(candidates: list[dict]) -> dict:
    """Adjudicate ``candidates`` = ``[{"engine", "engine_version"?, "parsed": {"pages":[...]}}, ...]``.

    Score each candidate with ``parse_quality``, select the highest ``overall`` (ties → lowest index, stable +
    deterministic), and return a ``ParsedDocument.v1`` with the WINNER's pages + quality + an ``engine_runs``
    ledger that PRESERVES every engine (lossless — losers carry their own quality + a reason, never dropped)."""
    if not candidates:
        raise AdjudicationError("adjudicate() needs at least one candidate parse")
    scored = []
    for i, c in enumerate(candidates):
        parsed = c.get("parsed") or {}
        scored.append({"i": i, "engine": c.get("engine", f"engine-{i}"),
                       "engine_version": c.get("engine_version", ""), "parsed": parsed,
                       "quality": score_parse(parsed)})
    best = min(scored, key=lambda s: (-s["quality"]["overall"], s["i"]))  # highest quality, ties → first
    engine_runs = [{"engine": s["engine"], "engine_version": s["engine_version"],
                    "selected": s["i"] == best["i"], "overall_quality": s["quality"]["overall"],
                    "reason": "highest parse quality" if s["i"] == best["i"]
                    else f"preserved as evidence (overall {s['quality']['overall']} < winner {best['quality']['overall']})"}
                   for s in scored]
    return {"schema_version": PARSED_DOCUMENT_SCHEMA_VERSION,
            "document": best["parsed"].get("document", {}),
            "pages": best["parsed"].get("pages", []),
            "quality": best["quality"], "engine_runs": engine_runs, "serves_truth": False}


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    good = {"document": {"title": "Policy"}, "pages": [{"page_no": 1, "blocks": [
        {"kind": "heading", "ordinal": 0, "text": "Retention", "confidence": 0.95},
        {"kind": "paragraph", "ordinal": 1, "text": "365 days.", "confidence": 0.93}]}]}
    scrambled = {"pages": [{"page_no": 1, "blocks": [
        {"kind": "paragraph", "ordinal": 1, "text": "365 days.", "confidence": 0.6},
        {"kind": "heading", "ordinal": 0, "text": "Retention", "confidence": 0.6}]}]}   # reading order broken
    blank = {"pages": [{"page_no": 1, "blocks": []}]}                                    # parsed nothing

    out = adjudicate([{"engine": "docling", "parsed": good},
                      {"engine": "mineru", "parsed": scrambled},
                      {"engine": "tika", "parsed": blank}])
    ck("emits a ParsedDocument.v1 that never serves truth",
       out["schema_version"] == "ParsedDocument.v1" and out["serves_truth"] is False)
    ck("the HIGHEST-quality engine (docling) is selected", out["quality"] == score_parse(good)
       and out["pages"] == good["pages"])
    selected = [r for r in out["engine_runs"] if r["selected"]]
    ck("exactly ONE engine is selected", len(selected) == 1 and selected[0]["engine"] == "docling")
    ck("LOSSLESS: every engine is preserved in engine_runs, with its quality + a reason",
       {r["engine"] for r in out["engine_runs"]} == {"docling", "mineru", "tika"}
       and all("reason" in r and r["overall_quality"] is not None for r in out["engine_runs"]))
    ck("a loser's reason names it as preserved evidence",
       any("preserved as evidence" in r["reason"] for r in out["engine_runs"] if not r["selected"]))
    ck("the winning document metadata is carried through", out["document"].get("title") == "Policy")

    one = adjudicate([{"engine": "docling", "parsed": good}])
    ck("a single candidate adjudicates to itself", one["engine_runs"][0]["selected"] and len(one["engine_runs"]) == 1)
    ck("adjudication is deterministic", adjudicate([{"engine": "a", "parsed": good}, {"engine": "b", "parsed": scrambled}])
       == adjudicate([{"engine": "a", "parsed": good}, {"engine": "b", "parsed": scrambled}]))

    raised = False
    try:
        adjudicate([])
    except AdjudicationError:
        raised = True
    ck("no candidates → fail loud (AdjudicationError), never an empty document", raised)

    print("\n" + ("PASS — parse_adjudicator: N engines are scored, the highest-quality parse is SELECTED, and "
                  "every engine's output is PRESERVED in engine_runs (lossless — losers kept as evidence with a "
                  "reason); deterministic; emits ParsedDocument.v1 that never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Multi-engine parse adjudicator (lossless engine_runs).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
