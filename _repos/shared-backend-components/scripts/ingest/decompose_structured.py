#!/usr/bin/env python3
"""scripts.ingest.decompose_structured — finer-grain decomposition: structured record → atomic FACTS.

`document_decompose` turns an unstructured artifact into a tree of nodes. This is the sibling for
STRUCTURED records (CFPB complaints, JSON rows, key/value docs): it breaks ONE record into the smallest
useful, independently-addressable components —

  * **atomic facts** — one single-sentence fact per structured field, each with its own
    ``ctx://…#field`` handle (expandable back to the exact field) and ``claim_status='fact'``;
  * **sentence chunks** — free-text fields (a complaint narrative) split into single-sentence chunks,
    each held out as ``claim_status='unverified_allegation'`` (NOT certifiable) — same governance as the
    pack, now at sentence grain.

This is "digestible front, expandable back" at the FACT level: a downstream If-Statement/claim attaches
to one atomic fact, not the whole record. Deterministic + offline (content-hashed ids; stdlib only).
Structured first; the unstructured-PDF path stays `document_decompose` (this complements it).

CLI:
    python3 _repos/shared-backend-components/scripts/ingest/decompose_structured.py --self-test
"""
from __future__ import annotations

import argparse
import re
from typing import Any, Iterable, Mapping

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.foundry.scrapers import content_hash

_SENT_RE = re.compile(r"[^.!?]+[.!?]?")
CLAIM_FACT = "fact"                       # structured field → certifiable atomic fact
CLAIM_ALLEGATION = "unverified_allegation"  # free-text narrative → held out, not certified

#: CFPB complaint field → human label (single source for the sentence templates).
CFPB_LABELS = {
    "product": "product", "sub_product": "sub-product", "issue": "issue", "sub_issue": "sub-issue",
    "company": "company", "state": "state", "company_response": "company response",
    "timely": "timely response", "submitted_via": "submitted via", "consumer_consent": "consumer consent",
}
#: CFPB free-text field(s) that are allegations, not facts.
CFPB_NARRATIVE_FIELDS = ("complaint_what_happened", "narrative", "consumer_complaint_narrative")


def sentence_chunks(text: str) -> list[str]:
    """Split free text into single-sentence chunks (the smallest text component)."""
    return [s.strip() for s in _SENT_RE.findall(text or "") if s.strip()]


def _fact(subject: str, source_handle: str, field: str, value: Any, label: str,
          *, claim_status: str = CLAIM_FACT) -> dict[str, Any]:
    handle = f"{source_handle}#{field}"
    text = f"{subject}: {label} is {value}."
    return {
        "fact_id": "fact-" + content_hash(f"{handle}={value}")[:12],
        "object_type": "fact" if claim_status == CLAIM_FACT else "source_excerpt",
        "text": text,
        "field": field,
        "value": value,
        "source_handle": handle,            # expandable back to the exact field
        "claim_status": claim_status,
        "promotion_eligible": claim_status == CLAIM_FACT,
    }


def decompose_record(record: Mapping[str, Any], *, source_handle: str, subject: str,
                     narrative_fields: Iterable[str] = (), labels: Mapping[str, str] | None = None) -> list[dict[str, Any]]:
    """Decompose ONE structured record into atomic components (facts + narrative sentence chunks).

    Scalar fields → one atomic fact each (claim_status='fact'). Each ``narrative_fields`` value → one
    component per sentence (claim_status='unverified_allegation', not promotion-eligible). Deterministic,
    ordered by field name then sentence index.
    """
    labels = dict(labels or {})
    narrative = set(narrative_fields)
    out: list[dict[str, Any]] = []
    for field in sorted(record):
        value = record[field]
        if field in narrative:
            continue  # handled below as sentence chunks
        if isinstance(value, (dict, list)) or value is None or value == "":
            continue  # only atomic scalars become single-field facts
        out.append(_fact(subject, source_handle, field, value, labels.get(field, field.replace("_", " "))))
    # narrative → sentence chunks (held out)
    for field in sorted(narrative):
        text = record.get(field)
        if not text:
            continue
        for i, sentence in enumerate(sentence_chunks(str(text))):
            handle = f"{source_handle}#{field}.s{i}"
            out.append({
                "fact_id": "alleg-" + content_hash(f"{handle}={sentence}")[:12],
                "object_type": "source_excerpt",
                "text": sentence,
                "field": field,
                "sentence_index": i,
                "source_handle": handle,
                "claim_status": CLAIM_ALLEGATION,
                "promotion_eligible": False,
            })
    return out


def decompose_cfpb_complaint(record: Mapping[str, Any], *, native_id: str,
                             source_handle_prefix: str = "ctx://cfpb/consumer-complaints/complaint") -> dict[str, Any]:
    """CFPB-specific: decompose a complaint record into atomic facts + held-out narrative sentences."""
    handle = f"{source_handle_prefix}/{native_id}"
    components = decompose_record(record, source_handle=handle, subject=f"Complaint {native_id}",
                                  narrative_fields=CFPB_NARRATIVE_FIELDS, labels=CFPB_LABELS)
    facts = [c for c in components if c["claim_status"] == CLAIM_FACT]
    allegations = [c for c in components if c["claim_status"] == CLAIM_ALLEGATION]
    return {
        "native_id": native_id,
        "source_handle": handle,
        "components": components,
        "fact_count": len(facts),
        "allegation_count": len(allegations),
        "content_hash": content_hash("|".join(c["source_handle"] for c in components)),
    }


#: Tiny deterministic sentiment lexicon (no model) — directional signal over a narrative, not a fact.
_NEG = {"not", "never", "no", "wrong", "fail", "failed", "dispute", "disputed", "incorrect", "error",
        "errors", "unauthorized", "fraud", "refused", "ignored", "denied", "unfair", "mistake", "missing"}
_POS = {"resolved", "fixed", "corrected", "approved", "helpful", "satisfied", "thanks", "timely", "clear", "accurate"}
_WORD = re.compile(r"[A-Za-z']+")
_PARA = re.compile(r"\n\s*\n")


def _sentiment(text: str) -> dict[str, Any]:
    toks = [w.lower() for w in _WORD.findall(text or "")]
    neg = sum(1 for w in toks if w in _NEG)
    pos = sum(1 for w in toks if w in _POS)
    score = round((pos - neg) / (pos + neg + 1), 3)
    polarity = "negative" if score < -0.1 else "positive" if score > 0.1 else "neutral"
    direction = "escalating" if neg > pos else "resolving" if pos > neg else "flat"
    return {"polarity": polarity, "score": score, "direction": direction,
            "neg_terms": neg, "pos_terms": pos, "method": "lexicon"}


def decompose_multigrain(record: Mapping[str, Any], *, native_id: str,
                         source_handle_prefix: str = "ctx://cfpb/consumer-complaints/complaint",
                         narrative_fields: Iterable[str] = CFPB_NARRATIVE_FIELDS) -> dict[str, Any]:
    """Decompose a record at MULTIPLE grains: atomic facts + sentences + paragraphs + a derived
    conclusion + a sentiment signal. Each grain is an independently-addressable component with its own
    handle + claim_status + promotion policy. Deterministic; structured facts are promotion-eligible,
    narrative grains are held out, the sentiment is a derived (non-promotable) signal."""
    handle = f"{source_handle_prefix}/{native_id}"
    base = decompose_cfpb_complaint(record, native_id=native_id, source_handle_prefix=source_handle_prefix)
    facts = [c for c in base["components"] if c["claim_status"] == CLAIM_FACT]
    sentences = [c for c in base["components"] if c["claim_status"] == CLAIM_ALLEGATION]  # already per-sentence

    paragraphs: list[dict[str, Any]] = []
    narrative = ""
    for f in narrative_fields:
        if record.get(f):
            narrative = str(record[f])
            for i, para in enumerate(p.strip() for p in _PARA.split(narrative) if p.strip()):
                paragraphs.append({"grain": "paragraph", "text": para,
                                   "source_handle": f"{handle}#{f}.p{i}",
                                   "claim_status": CLAIM_ALLEGATION, "promotion_eligible": False})
            break

    # a derived single-sentence conclusion from STRUCTURED fields (promotion-eligible: it's from facts)
    issue = record.get("issue", "?")
    conclusion_text = (f"Complaint {native_id}: about '{issue}' ({record.get('product','?')}); "
                       f"company response '{record.get('company_response','?')}', timely={record.get('timely','?')}.")
    conclusion = {"grain": "conclusion", "fact_id": "concl-" + content_hash(f"{handle}#conclusion={conclusion_text}")[:12],
                  "text": conclusion_text, "field": "conclusion", "value": conclusion_text,
                  "source_handle": f"{handle}#conclusion", "claim_status": CLAIM_FACT, "promotion_eligible": True,
                  "derived_from": [f["source_handle"] for f in facts]}

    sentiment = {"grain": "sentiment", **_sentiment(narrative), "source_handle": f"{handle}#sentiment",
                 "claim_status": "derived_signal", "promotion_eligible": False}

    for c in facts:
        c["grain"] = "fact"
    for c in sentences:
        c["grain"] = "sentence"
    components = facts + sentences + paragraphs + [conclusion, sentiment]
    grains = {"fact": len(facts), "sentence": len(sentences), "paragraph": len(paragraphs),
              "conclusion": 1, "sentiment": 1}
    return {"native_id": native_id, "source_handle": handle, "components": components,
            "grains": grains, "sentiment": sentiment,
            "content_hash": content_hash("|".join(c["source_handle"] for c in components))}


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    rec = {
        "product": "Credit reporting or other personal consumer reports",
        "issue": "Incorrect information on your report",
        "sub_issue": "Information belongs to someone else",
        "company": "Example Credit Bureau A", "state": "CA",
        "company_response": "Closed with explanation", "timely": "Yes",
        "complaint_what_happened": "They reported an account that is not mine. I disputed it twice. It was not fixed.",
    }
    d = decompose_cfpb_complaint(rec, native_id="demo-1001")

    check("decomposed into atomic facts (one per structured field)", d["fact_count"] == 7, str(d["fact_count"]))
    check("narrative split into 3 single-sentence chunks", d["allegation_count"] == 3, str(d["allegation_count"]))
    prod = next(c for c in d["components"] if c["field"] == "product")
    check("each fact is a single sentence with its value", prod["text"].endswith("consumer reports.") and "product is" in prod["text"])
    check("each fact has an expandable-back field handle", prod["source_handle"] == "ctx://cfpb/consumer-complaints/complaint/demo-1001#product")
    check("structured facts are promotion-eligible (claim_status=fact)", all(c["promotion_eligible"] for c in d["components"] if c["claim_status"] == CLAIM_FACT))
    check("narrative sentences held out (unverified_allegation, NOT promotion-eligible)",
          all((not c["promotion_eligible"]) and c["claim_status"] == CLAIM_ALLEGATION for c in d["components"] if c["object_type"] == "source_excerpt"))
    s0 = next(c for c in d["components"] if c.get("sentence_index") == 0)
    check("narrative chunk handle is per-sentence (#field.sN)", s0["source_handle"].endswith("#complaint_what_happened.s0"))
    check("deterministic content_hash + re-run identical", d == decompose_cfpb_complaint(rec, native_id="demo-1001"))
    # generic (non-CFPB) record also decomposes
    g = decompose_record({"status": "listed", "country": "US", "notes": ""}, source_handle="ctx://x/1", subject="Row 1")
    check("generic record → atomic facts, empty/None fields skipped", len(g) == 2 and {c["field"] for c in g} == {"status", "country"})

    # ── multi-grain decomposition (sentences + paragraphs + conclusion + sentiment) ──
    mrec = dict(rec)
    mrec["complaint_what_happened"] = "They reported an account that is not mine.\n\nI disputed it twice. It was not fixed."
    mg = decompose_multigrain(mrec, native_id="demo-1001")
    check("multigrain yields all grains", set(mg["grains"]) == {"fact", "sentence", "paragraph", "conclusion", "sentiment"} and mg["grains"]["paragraph"] == 2 and mg["grains"]["sentence"] == 3)
    check("conclusion is a derived promotion-eligible fact", any(c["grain"] == "conclusion" and c["promotion_eligible"] for c in mg["components"]))
    check("sentiment is a derived, non-promotable signal (negative/escalating here)",
          mg["sentiment"]["claim_status"] == "derived_signal" and not mg["sentiment"]["promotion_eligible"] and mg["sentiment"]["polarity"] == "negative")
    check("paragraph grains held out (#field.pN handles, not promotable)",
          all((not c["promotion_eligible"]) and ".p" in c["source_handle"] for c in mg["components"] if c["grain"] == "paragraph"))
    check("multigrain deterministic", mg == decompose_multigrain(mrec, native_id="demo-1001"))

    print(f"\n{'all decompose_structured self-tests passed (record → atomic single-sentence facts w/ #field handles; narrative → held-out sentence chunks; deterministic).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Decompose a structured record into atomic facts + sentence chunks.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
