#!/usr/bin/env python3
"""scripts.context_diff — deterministic change-report for a rewrite (the diff/provenance layer).

The L18 layer of `research/text-transformation-systems-map.md`, expressed in Baltor's terms: when any
stage REWRITES text (compress, simplify, style-transfer, paraphrase), governance requires showing
**what changed** — especially whether a figure, date, or protected entity was silently dropped, changed,
or fabricated. This produces that change-report deterministically (NO LLM): word/sentence diffs +
entity preservation + risk flags + a readability before/after proxy.

Why it matters for the compliance beachhead: a rewrite that drops a sanctioned entity or alters a figure
is a correctness failure, not a style nit. This catches it before serving.

Deterministic + offline (difflib + regex; stdlib only). Reuses `scrapers.content_hash` (No-Magic-Values).
Optional `bus=` emits onto the live bus (component.started → component.progressed per risk →
context_pack.created → component.finished), byte-identical/non-breaking when omitted.

CLI:
    python3 scripts/context_diff.py --self-test
"""
from __future__ import annotations

import argparse
import difflib
import re
from typing import Any, Iterable

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.foundry.scrapers import content_hash

# ── extraction patterns (single source; No-Magic-Values) ─────────────────────
NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b")
WORD_RE = re.compile(r"[A-Za-z0-9']+")
SENT_RE = re.compile(r"[^.!?]+[.!?]?")
_VOWEL_GROUP_RE = re.compile(r"[aeiouy]+")

#: risk severities (worst-first ordering of the report's flags)
SEV_HIGH = "high"
SEV_MED = "medium"


def _words(text: str) -> list[str]:
    return WORD_RE.findall(text or "")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in SENT_RE.findall(text or "") if s.strip()]


def _numbers(text: str) -> set[str]:
    # strip dates first so a date's components (2026, 05, 28) aren't counted as standalone numbers
    return set(NUMBER_RE.findall(DATE_RE.sub(" ", text or "")))


def _dates(text: str) -> set[str]:
    return set(DATE_RE.findall(text or ""))


def _syllables(word: str) -> int:
    n = len(_VOWEL_GROUP_RE.findall(word.lower()))
    return max(1, n)


def _readability(text: str) -> dict[str, Any]:
    """Deterministic readability proxy: counts + a Flesch-Kincaid grade estimate (heuristic syllables)."""
    words = _words(text)
    sents = _sentences(text) or [text] if text else []
    nw, ns = len(words), max(1, len(sents))
    syll = sum(_syllables(w) for w in words) or 1
    avg_spw = nw / ns
    avg_syll = syll / max(1, nw)
    # Flesch-Kincaid grade level (standard coefficients); rounded for stable output.
    fk = round(0.39 * avg_spw + 11.8 * avg_syll - 15.59, 2) if nw else 0.0
    return {"words": nw, "sentences": len(sents),
            "avg_sentence_len": round(avg_spw, 2), "fk_grade": fk}


def diff_text(original: str, rewrite: str, *, protect: Iterable[str] | None = None, bus=None) -> dict[str, Any]:
    """Produce a deterministic change-report between ``original`` and ``rewrite``.

    ``protect`` is an explicit list of must-keep terms (e.g. entity names the rewrite must not drop).
    Returns word/sentence diffs, per-category entity preservation, risk_flags (worst-first), a
    readability before/after proxy, and a deterministic ``content_hash``.
    """
    protect = [str(p) for p in (protect or [])]

    ow, rw = _words(original), _words(rewrite)
    sm = difflib.SequenceMatcher(a=[w.lower() for w in ow], b=[w.lower() for w in rw], autojunk=False)
    added_w: list[str] = []
    removed_w: list[str] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete"):
            removed_w.extend(ow[i1:i2])
        if tag in ("replace", "insert"):
            added_w.extend(rw[j1:j2])

    os_, rs_ = _sentences(original), _sentences(rewrite)
    os_set, rs_set = set(os_), set(rs_)
    removed_claims = [s for s in os_ if s not in rs_set]
    added_claims = [s for s in rs_ if s not in os_set]

    # entity preservation per category (numbers/dates = governance-critical; protected = explicit)
    on, rn = _numbers(original), _numbers(rewrite)
    od, rd = _dates(original), _dates(rewrite)
    low_orig, low_rw = (original or "").lower(), (rewrite or "").lower()
    prot_dropped = [p for p in protect if p.lower() in low_orig and p.lower() not in low_rw]

    entities = {
        "numbers": {"preserved": sorted(on & rn), "dropped": sorted(on - rn), "added": sorted(rn - on)},
        "dates": {"preserved": sorted(od & rd), "dropped": sorted(od - rd), "added": sorted(rd - od)},
        "protected": {"preserved": sorted([p for p in protect if p.lower() in low_orig and p.lower() in low_rw]),
                      "dropped": sorted(prot_dropped)},
    }

    risk_flags: list[dict[str, Any]] = []
    for p in prot_dropped:
        risk_flags.append({"flag": "protected_term_dropped", "severity": SEV_HIGH, "detail": p})
    for n in sorted(on - rn):
        risk_flags.append({"flag": "number_dropped_or_changed", "severity": SEV_HIGH, "detail": n})
    for n in sorted(rn - on):
        risk_flags.append({"flag": "number_introduced", "severity": SEV_MED, "detail": n})
    for d in sorted(od - rd):
        risk_flags.append({"flag": "date_dropped_or_changed", "severity": SEV_HIGH, "detail": d})
    # worst-first
    risk_flags.sort(key=lambda f: (f["severity"] != SEV_HIGH, f["flag"], f["detail"]))

    rb, ra = _readability(original), _readability(rewrite)
    report = {
        "original": original,
        "rewrite": rewrite,
        "changed_terms": {"added": added_w, "removed": removed_w},
        "added_claims": added_claims,
        "removed_claims": removed_claims,
        "entities": entities,
        "risk_flags": risk_flags,
        "readability_before": rb,
        "readability_after": ra,
        "stats": {"risks": len(risk_flags),
                  "high_risks": sum(1 for f in risk_flags if f["severity"] == SEV_HIGH),
                  "words_before": rb["words"], "words_after": ra["words"],
                  "claims_added": len(added_claims), "claims_removed": len(removed_claims)},
    }
    report["content_hash"] = content_hash(
        f"{content_hash(original)}|{content_hash(rewrite)}|{'/'.join(sorted(protect))}")

    if bus is not None:  # live-bus emit — pure side-effect; byte-identical return when bus=None
        cid = "diff-" + report["content_hash"][:8]
        bus.publish("component.started", component="context_diff", stage="Verification rail",
                    correlation_id=cid, payload={"words_before": rb["words"], "words_after": ra["words"]})
        for f in risk_flags:
            bus.publish("component.progressed", component="context_diff", stage="Verification rail",
                        correlation_id=cid, payload={"risk_flag": f["flag"], "severity": f["severity"], "detail": f["detail"]})
        bus.publish("context_pack.created", component="context_diff", stage="Consumption",
                    correlation_id=cid, object_ref=cid,
                    payload={"risks": len(risk_flags), "high_risks": report["stats"]["high_risks"],
                             "content_hash": report["content_hash"][:12]})
        bus.publish("component.finished", component="context_diff", stage="Verification rail",
                    correlation_id=cid, payload={"risks": len(risk_flags)})
    return report


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # A rewrite that drops a figure + a protected entity, changes a date, adds a fabricated number.
    original = ("Northwind Trading LLC is LISTED as of 2026-05-28; block all 5 pending transactions.")
    rewrite = ("The company is listed as of 2026-05-01; block the pending transactions and add 9 checks.")
    rep = diff_text(original, rewrite, protect=["Northwind Trading LLC"])

    flags = {f["flag"] for f in rep["risk_flags"]}
    check("flags protected_term_dropped (Northwind…)", "protected_term_dropped" in flags)
    check("flags number_dropped_or_changed (the 5)", any(f["flag"] == "number_dropped_or_changed" and f["detail"] == "5" for f in rep["risk_flags"]))
    check("flags number_introduced (the fabricated 9)", any(f["flag"] == "number_introduced" and f["detail"] == "9" for f in rep["risk_flags"]))
    check("flags date_dropped_or_changed (2026-05-28)", any(f["flag"] == "date_dropped_or_changed" and f["detail"] == "2026-05-28" for f in rep["risk_flags"]))
    check("risk_flags worst-first (high before medium)", rep["risk_flags"][0]["severity"] == SEV_HIGH)
    check("entities.numbers dropped=[5], added=[9]", rep["entities"]["numbers"]["dropped"] == ["5"] and rep["entities"]["numbers"]["added"] == ["9"])
    check("protected entity reported dropped", rep["entities"]["protected"]["dropped"] == ["Northwind Trading LLC"])
    check("word-level diff captured a removed + added term", rep["changed_terms"]["removed"] and rep["changed_terms"]["added"])
    check("claims added + removed (sentence diff)", rep["stats"]["claims_added"] >= 1 and rep["stats"]["claims_removed"] >= 1)
    check("readability before/after computed", rep["readability_before"]["words"] > 0 and isinstance(rep["readability_after"]["fk_grade"], float))

    # a clean, faithful rewrite (paraphrase that keeps every figure/date/entity) → ZERO high risks
    clean = diff_text("Block all 5 transactions on 2026-05-28 for Acme Corp.",
                      "On 2026-05-28, block all 5 transactions for Acme Corp.", protect=["Acme Corp"])
    check("faithful reorder → no high-severity risk flags", clean["stats"]["high_risks"] == 0, str(clean["risk_flags"]))

    # determinism + non-breaking bus
    rep2 = diff_text(original, rewrite, protect=["Northwind Trading LLC"])
    check("deterministic content_hash (sha256)", rep["content_hash"] == rep2["content_hash"] and len(rep["content_hash"]) == 64)
    check("byte-identical re-run", rep == rep2)

    from scripts.context_events import EventBus
    bus = EventBus()
    seen: list[dict] = []
    bus.subscribe(seen.append)
    rep_bus = diff_text(original, rewrite, protect=["Northwind Trading LLC"], bus=bus)
    kinds = [e["kind"] for e in seen]
    check("bus: started…finished", bool(kinds) and kinds[0] == "component.started" and kinds[-1] == "component.finished")
    check("bus: a risk emitted as component.progressed", any(e["kind"] == "component.progressed" and e["payload"].get("risk_flag") for e in seen))
    check("bus: context_pack.created (the change-report)", "context_pack.created" in kinds)
    check("bus vs no-bus return IDENTICAL", rep_bus == rep2)

    print(f"\n{'all context_diff self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Deterministic change-report for a rewrite (diff/provenance).")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
