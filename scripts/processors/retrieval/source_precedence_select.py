#!/usr/bin/env python3
"""Backs `processor/source-precedence-select` (process_kind ``select.source_precedence``).

Where governance shows up at READ time (taxonomy step R5): when candidates
disagree, primary / signed / still-valid sources win ties by an explicit
precedence policy — and contradictions are FLAGGED with both sides, never
silently averaged or silently resolved. The selector needs source metadata;
candidates without it sink to the bottom of the precedence order and are
marked, not guessed about.

Contract: deterministic; side_effects=none; on_error=raise.
Inputs candidates({"id","text",source metadata}), policy → selected, conflicts.

CLI / self-test: python3 scripts/processors/retrieval/source_precedence_select.py
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Default precedence policy, highest authority first. A caller's policy
#: (list of source_kind strings) replaces this wholesale — no hidden merge.
DEFAULT_PRECEDENCE: tuple[str, ...] = (
    "source_of_law", "primary_document", "signed_publisher",
    "verified_fact", "secondary_report", "unknown",
)

#: Source kind assigned when a candidate carries no source_kind metadata.
UNKNOWN_KIND = "unknown"

#: Two candidates conflict when they share a topic (>= this many salient
#: terms) but report different numeric values.
CONFLICT_TERM_OVERLAP = 2

STOPWORDS = frozenset({"a", "an", "and", "are", "as", "at", "be", "by", "for",
                       "in", "is", "it", "of", "on", "or", "the", "to", "with"})
_TOKEN_RE = re.compile(r"[a-z0-9%$.]+")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?%?")


def _salient(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS}


def run(*, candidates: list[dict[str, Any]],
        policy: list[str] | None = None) -> dict[str, Any]:
    """Order ``candidates`` by source precedence and surface contradictions.

    Candidate metadata read: ``source_kind`` (policy rank), ``signed`` (bool
    tie-break), ``valid_through`` vs ``as_of`` (expiry — expired entries are
    flagged and sink within their kind). Returns ``{"selected": [...],
    "conflicts": [...]}`` per the manifest outputs.
    """
    if not isinstance(candidates, list):
        raise TypeError("candidates must be a list of dicts")
    order = list(policy) if policy is not None else list(DEFAULT_PRECEDENCE)
    if not order:
        raise ValueError("policy must name at least one source kind")
    if UNKNOWN_KIND not in order:
        order.append(UNKNOWN_KIND)  # unknown always has SOME (lowest given) rank
    rank = {kind: i for i, kind in enumerate(order)}

    rows: list[dict[str, Any]] = []
    for i, c in enumerate(candidates):
        if not isinstance(c, dict) or "id" not in c or "text" not in c:
            raise ValueError(f"candidates[{i}] needs id and text")
        kind = c.get("source_kind", UNKNOWN_KIND)
        if kind not in rank:
            raise ValueError(f"candidates[{i}] source_kind {kind!r} is not in the policy {order}")
        expired = False
        if c.get("valid_through") is not None and c.get("as_of") is not None:
            expired = float(c["as_of"]) > float(c["valid_through"])
        rows.append({"id": str(c["id"]), "text": str(c["text"]), "source_kind": kind,
                     "signed": bool(c.get("signed", False)), "expired": expired,
                     "precedence_rank": rank[kind],
                     "metadata_present": "source_kind" in c})
    # Order: precedence rank, expired sinks within kind, signed wins ties, id stable.
    rows.sort(key=lambda r: (r["precedence_rank"], r["expired"], not r["signed"], r["id"]))

    # Conflicts: same topic, different numbers — flagged with BOTH sides and
    # which one precedence prefers; never silently averaged.
    conflicts: list[dict[str, Any]] = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            shared = _salient(a["text"]) & _salient(b["text"])
            if len(shared) < CONFLICT_TERM_OVERLAP:
                continue
            na, nb = set(_NUMBER_RE.findall(a["text"])), set(_NUMBER_RE.findall(b["text"]))
            if na and nb and na != nb:
                conflicts.append({
                    "ids": [a["id"], b["id"]],
                    "values": [sorted(na), sorted(nb)],
                    "precedence_prefers": a["id"],  # rows are precedence-sorted
                    "resolution": "flagged_not_averaged",
                })
    return {"selected": rows, "conflicts": conflicts}


def _selftest() -> None:
    cands = [
        {"id": "blog", "text": "the usury cap is 6% according to a forum post",
         "source_kind": "secondary_report"},
        {"id": "statute", "text": "the usury cap is 8% per the revised code",
         "source_kind": "source_of_law", "signed": True,
         "valid_through": 2_000.0, "as_of": 1_000.0},
        {"id": "mystery", "text": "some unsourced claim about caps"},
    ]
    out = run(candidates=cands)
    sel = out["selected"]
    # Law outranks a secondary report; metadata-less sinks to the bottom, marked.
    assert [r["id"] for r in sel] == ["statute", "blog", "mystery"]
    assert sel[2]["source_kind"] == UNKNOWN_KIND and sel[2]["metadata_present"] is False
    # The 8% vs 6% contradiction is FLAGGED with both sides + the preferred id.
    assert len(out["conflicts"]) == 1
    c = out["conflicts"][0]
    assert set(c["ids"]) == {"statute", "blog"} and c["precedence_prefers"] == "statute"
    assert c["resolution"] == "flagged_not_averaged"
    # Expiry sinks within kind: an expired statute loses to a current one.
    pair = [
        {"id": "old", "text": "cap is 9%", "source_kind": "source_of_law",
         "valid_through": 500.0, "as_of": 1_000.0},
        {"id": "cur", "text": "cap is 8%", "source_kind": "source_of_law",
         "valid_through": 2_000.0, "as_of": 1_000.0},
    ]
    p = run(candidates=pair)["selected"]
    assert [r["id"] for r in p] == ["cur", "old"] and p[1]["expired"] is True
    # Custom policy replaces the default wholesale.
    custom = run(candidates=cands, policy=["secondary_report", "source_of_law"])["selected"]
    assert custom[0]["id"] == "blog"
    # Deterministic; inputs untouched; on_error=raise on out-of-policy kinds.
    snap = json.dumps(cands, sort_keys=True)
    assert json.dumps(run(candidates=cands), sort_keys=True) == \
           json.dumps(run(candidates=cands), sort_keys=True)
    assert json.dumps(cands, sort_keys=True) == snap
    raised = False
    try:
        run(candidates=[{"id": "x", "text": "t", "source_kind": "vibes"}])
    except ValueError:
        raised = True
    assert raised
    print("PASS — source_precedence_select: law>primary>signed>verified>secondary "
          "ordering, expiry sinks, signed tie-break, contradictions flagged with "
          "both sides (never averaged), unknown-metadata marked verified")


if __name__ == "__main__":
    _selftest()
