#!/usr/bin/env python3
"""Backs `processor/simhash-dedupe` (process_kind ``select.dedupe_simhash``).

Near-duplicate removal before context placement (taxonomy step R5): an exact
content-hash pass removes identical chunks, then a 64-bit SimHash over word
shingles catches near-duplicates (small edits, boilerplate variants) whose
fingerprints differ by at most ``threshold`` bits. Duplicates are REPORTED
with the id they duplicate — dropped from the working list, never silently
lost (the lossless law at the selection layer).

Contract: deterministic; side_effects=none; on_error=raise.
Inputs candidates({"id","text"}), threshold(bits) → output deduped.

CLI / self-test: python3 scripts/processors/retrieval/simhash_dedupe.py
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: SimHash width in bits (md5's low 64 bits per feature).
SIMHASH_BITS = 64

#: Hamming-distance ceiling for "near-duplicate". Google's classic web-doc
#: threshold is 3 bits, but RAG chunks have far fewer shingle features, so a
#: one-word edit moves ~5-8 bits (measured in the self-test fixture: 7) while
#: unrelated chunks sit near the 32-bit random expectation (measured: 36).
#: 10 bits separates those regimes with margin on both sides.
DEFAULT_THRESHOLD_BITS = 10

#: Word-shingle width for features: 2-grams balance locality vs. noise.
SHINGLE_WIDTH = 2

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _features(text: str) -> list[str]:
    toks = _TOKEN_RE.findall(text.lower())
    if len(toks) < SHINGLE_WIDTH:
        return [" ".join(toks)] if toks else []
    return [" ".join(toks[i:i + SHINGLE_WIDTH]) for i in range(len(toks) - SHINGLE_WIDTH + 1)]


def simhash(text: str) -> int:
    """64-bit SimHash over word shingles (deterministic, stdlib md5)."""
    weights = [0] * SIMHASH_BITS
    for feat in _features(text):
        h = int.from_bytes(hashlib.md5(feat.encode("utf-8")).digest()[:8], "big")
        for bit in range(SIMHASH_BITS):
            weights[bit] += 1 if (h >> bit) & 1 else -1
    out = 0
    for bit, w in enumerate(weights):
        if w > 0:
            out |= 1 << bit
    return out


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def run(*, candidates: list[dict[str, Any]], threshold: int = DEFAULT_THRESHOLD_BITS) -> dict[str, Any]:
    """Drop exact + near-duplicate candidates (first occurrence wins, input order)."""
    if not isinstance(candidates, list):
        raise TypeError("candidates must be a list of id/text dicts")
    if not isinstance(threshold, int) or not 0 <= threshold <= SIMHASH_BITS:
        raise ValueError(f"threshold must be 0..{SIMHASH_BITS} bits, got {threshold!r}")
    kept: list[dict[str, Any]] = []
    kept_sigs: list[tuple[str, int, str]] = []  # (id, simhash, exact_hash)
    removed: list[dict[str, Any]] = []
    for i, c in enumerate(candidates):
        if not isinstance(c, dict) or "id" not in c or "text" not in c:
            raise ValueError(f"candidates[{i}] needs id and text")
        text = str(c["text"])
        exact = hashlib.sha256(text.encode("utf-8")).hexdigest()
        sig = simhash(text)
        dup_of = None
        method = None
        for kid, ksig, kexact in kept_sigs:
            if exact == kexact:
                dup_of, method = kid, "exact_hash"
                break
            if hamming(sig, ksig) <= threshold:
                dup_of, method = kid, "simhash"
                break
        if dup_of is not None:
            removed.append({"id": str(c["id"]), "duplicate_of": dup_of, "method": method})
        else:
            kept.append(c)
            kept_sigs.append((str(c["id"]), sig, exact))
    return {"deduped": {"kept": kept, "removed": removed,
                        "threshold_bits": threshold, "simhash_bits": SIMHASH_BITS}}


def _selftest() -> None:
    base = ("under regulation e the bank must provide provisional credit within ten "
            "business days of an error notice from the consumer")
    cands = [
        {"id": "k1", "text": base},
        {"id": "k2", "text": base},                                   # exact duplicate
        {"id": "k3", "text": base.replace("ten", "10") + "."},        # near-duplicate
        {"id": "k4", "text": "liability for unauthorized debit transfers is capped at fifty dollars when reported promptly"},
    ]
    out = run(candidates=cands)["deduped"]
    kept_ids = [c["id"] for c in out["kept"]]
    assert kept_ids == ["k1", "k4"]
    # Removals carry full lineage (what they duplicate + how it was caught).
    rm = {r["id"]: r for r in out["removed"]}
    assert rm["k2"]["duplicate_of"] == "k1" and rm["k2"]["method"] == "exact_hash"
    assert rm["k3"]["duplicate_of"] == "k1" and rm["k3"]["method"] == "simhash"
    # Nothing vanished: kept + removed account for every input.
    assert len(out["kept"]) + len(out["removed"]) == len(cands)
    # threshold=0 keeps near-duplicates (only exact collapses).
    strict = run(candidates=cands, threshold=0)["deduped"]
    assert [c["id"] for c in strict["kept"]] == ["k1", "k3", "k4"]
    # Deterministic; inputs untouched; honest empty; on_error=raise.
    snap = json.dumps(cands, sort_keys=True)
    assert json.dumps(run(candidates=cands), sort_keys=True) == json.dumps(run(candidates=cands), sort_keys=True)
    assert json.dumps(cands, sort_keys=True) == snap
    assert run(candidates=[])["deduped"]["kept"] == []
    raised = False
    try:
        run(candidates=cands, threshold=65)
    except ValueError:
        raised = True
    assert raised
    print(f"PASS — simhash_dedupe: exact-hash + {SIMHASH_BITS}-bit shingle SimHash at "
          f"<= {DEFAULT_THRESHOLD_BITS} bits (chunk-scale tuned), removals carry duplicate_of lineage, "
          "first-wins deterministic order verified")


if __name__ == "__main__":
    _selftest()
