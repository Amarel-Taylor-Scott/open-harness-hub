#!/usr/bin/env python3
"""Backs `processor/multi-source-corroborate`. The CANONICAL wiring lives in the manifest
``_repos/shared-backend-components/catalog/processors/assurance/multi-source-corroborate.yaml`` — process_kind
``verify.multi_source_corroborate``, side_effects ``none`` (``run()`` is a pure function of the
claim + the sources it is HANDED; it does no fetching itself). This docstring does not re-assert
those values (one source of truth — see ``_repos/shared-backend-components/docs/codex/no-magic-values.md``).

This is the **change-verification-contract** idea turned into a runtime tool. The contract
(``_repos/shared-backend-components/docs/codex/change-verification-contract.md``) admits a change on *corroboration* — **>= 2
independent agreeing sources**; one source, or one agent's assertion, is **not** corroboration.
This processor is the deterministic engine that *counts* that corroboration for an arbitrary claim:
given a claim and a set of already-gathered sources, how many INDEPENDENT publishers support it,
how many contradict it, and therefore is the claim corroborated, single-sourced, contradicted, or
uncorroborated.

Where it sits in the assurance wedge
-------------------------------------
The verified-corpus-commons wedge (``_repos/shared-backend-components/context/strategy/oracle-corpus-and-tooling-map.md``,
``beat-contextual-positioning.md``) is **context assurance**: prove a corpus/claim is still TRUE and
current, not merely *faithfully retrieved* — the job Contextual AI and the data marketplaces
structurally avoid. ``corpus_integrity_check`` is the anti-poisoning half (catch a planted doc that
contradicts/supersedes the authority). This module is the **corroboration** half: a claim that only
ONE publisher asserts is *single-sourced* and must not be treated as established — exactly the bar
the contract sets. "Three copies from one publisher" is one voice, not three; **independence is by
distinct publisher/source id**, so an attacker cannot manufacture agreement by reposting.

What independence buys (the threat it defends against)
------------------------------------------------------
A faithfulness-only retriever that returns three chunks agreeing on "the wire-transfer limit is USD
50,000" looks like strong evidence — but if all three trace to one planted note, it is one
unverified claim wearing three hats (the BadRAG/TrojanRAG corpus-poisoning pattern: a single planted
document cited as authoritative). Counting by **distinct publisher** collapses those three back to
one independent voice, so the verdict is ``single-source`` (hold for a second independent
confirmation), not ``corroborated``. Conversely, if even one independent publisher asserts a
*different* value for the same claim, the verdict is ``contradicted`` — surface the conflict, do not
average it away (that conflict is then the input to ``cross_source_reconcile``).

Deterministic v1 (honest scope — the seam)
------------------------------------------
Support detection is a **deterministic lexical v1**, the cheap reproducible floor, NOT a semantic
oracle. A source SUPPORTS the claim when it shares the claim's KEY TERMS *and* the claim's VALUE; it
CONTRADICTS when it shares the key terms but asserts a DIFFERENT value of the same kind; otherwise it
is SILENT (does not address the claim) and is not counted either way. Value normalization is reused
verbatim from :mod:`scripts.processors.assurance.corpus_integrity_check` (``$50k`` == ``USD
50,000`` != ``$10,000``), so a re-spelled value still corroborates/contradicts and the two modules
cannot drift. Because it is lexical it will MISS a paraphrased restatement ("fifty thousand dollars"
written out, or a synonym for the key term) — under-counting support, never inventing it, which is
the safe direction for a corroboration bar. The **semantic / NLI / LLM-judge upgrade** plugs in
behind this same ``run(...)`` contract and the same output keys, raising recall on paraphrases while
this deterministic floor stays the auditable A/B baseline. The **live-fetch** upgrade (actually
retrieving the independent sources via web-search / browser tools) is a SEPARATE component — those
are external (``side_effects: external_call``, ``trust_boundary: external``); this corroborator only
*scores* the sources it is handed, which is what keeps it pure and deterministic.

Runtime contract (matches the processor manifest + the runtime-routing doc
``_repos/shared-backend-components/context/architecture/component-execution-and-runtime-routing.md``):

  * ``process_kind = verify.multi_source_corroborate`` — CPU pool (matches the manifest).
  * **deterministic**: same inputs -> same output. No clocks, no RNG, no environment reads, no
    network, no filesystem access. Independent-source counting iterates publishers in a
    deterministically sorted order, so ties and verdicts are reproducible.
  * **idempotent**: re-running on the same claim + sources yields the same verdict; scoring has no
    effect on its inputs.
  * **side_effects = none** (manifest): ``run()`` is a pure function of its arguments; it neither
    reads nor writes the world. (Contrast ``corpus_integrity_check``'s ``read``: that component
    reads an authoritative reference; this one is handed everything.)
  * **on_error = raise**: wrong-typed inputs raise ``TypeError``/``ValueError``; we never silently
    score the wrong thing.
  * **streaming = false**: whole claim + full source set in, verdict out.

Pure-Python stdlib only (``re``) + a sibling-module import for shared value normalization. No
third-party deps.

Public API:
    from scripts.processors.assurance.multi_source_corroborate import run
    res = run(claim="The wire-transfer limit is USD 10,000.",
              sources=[{"text": "...", "source_id": "reuters"}, ...],
              min_independent=2)
    # -> {"corroboration": 0.0..1.0, "verdict": "corroborated|single-source|contradicted|
    #     uncorroborated", "agreeing_independent": int, "contradicting_independent": int,
    #     "min_independent": int, "supporting_source_ids": [...], "contradicting_source_ids": [...],
    #     "silent_source_ids": [...], "claim_value": str|None, "claim_terms": [...],
    #     "per_publisher": {...}, "method": METHOD}

CLI / self-test:
    python3 _repos/shared-backend-components/scripts/processors/assurance/multi_source_corroborate.py
    python3 -m scripts.processors.assurance.multi_source_corroborate
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

# Reuse the SAME value normalization + threshold extraction as the integrity checker — one source of
# truth (No-Magic-Values). Importing (not re-implementing) guarantees "$50k" == "USD 50,000" means
# the same thing in BOTH the anti-poisoning gate and the corroborator; they cannot drift apart.
# Tolerant to being run as a bare script (no package parent) OR as a package module.
try:  # package / -m execution
    from scripts.processors.assurance.corpus_integrity_check import (
        _VALUE_RE,
        _extract_thresholds,
        _label_key,
        _normalize_value,
        _same_threshold,
        _ensure_text as _coerce_text,
    )
except Exception:  # pragma: no cover - bare-script fallback
    import os as _os

    sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from corpus_integrity_check import (  # type: ignore[no-redef]
        _VALUE_RE,
        _extract_thresholds,
        _label_key,
        _normalize_value,
        _same_threshold,
        _ensure_text as _coerce_text,
    )

# ─── Tunable constants (single source of truth; No-Magic-Values) ─────────────

METHOD = "deterministic_independent_corroboration_v1"

# Default minimum number of INDEPENDENT agreeing publishers for "corroborated". 2 mirrors the
# change-verification contract's bar verbatim ("≥ 2 independent agreeing sources"). Callers may raise
# it for higher-stakes claims; it is never < 1 (one agreeing source can never be "corroborated").
DEFAULT_MIN_INDEPENDENT = 2

# Minimum share of the claim's KEY TERMS a source must contain before it is judged to ADDRESS the
# claim at all. Below this overlap the source is SILENT (off-topic) — neither support nor
# contradiction. Set so a source mentioning the subject of the claim (its salient nouns) counts as
# on-topic while a source about an unrelated matter does not accidentally "agree". A claim with very
# few key terms (1-2) requires all of them, which this fraction yields for small term sets.
TERM_OVERLAP_FLOOR = 0.6

# Stopwords stripped when extracting a claim's KEY TERMS. Superset of the integrity checker's label
# stopwords plus generic claim/assertion connective words, so "The report says the limit is X"
# keys on the content nouns, not on "the/report/says/is". Kept here (not imported) because this is a
# claim-term set, a different concern from the threshold-LABEL stopwords in the integrity checker.
_TERM_STOPWORDS = frozenset({
    # articles / determiners / conjunctions / prepositions
    "the", "a", "an", "of", "for", "per", "to", "at", "in", "on", "by", "as", "is", "are", "was",
    "were", "be", "been", "being", "and", "or", "but", "with", "from", "that", "this", "these",
    "those", "it", "its", "their", "our", "your", "his", "her", "no", "not", "than", "then",
    # claim / reporting framing verbs + adverbs that carry no subject content
    "say", "says", "said", "state", "states", "stated", "report", "reports", "reported",
    "according", "confirm", "confirms", "confirmed", "note", "notes", "noted", "claim", "claims",
    "claimed", "set", "now", "currently", "hereby", "effective", "immediately", "shall", "will",
    "must", "value", "figure", "amount", "number", "must", "per",
    # generic time/scale words that recur across unrelated claims
    "daily", "monthly", "weekly", "yearly", "annual", "total", "current", "new", "all", "any",
    "each", "single", "applicable", "please", "above", "below",
})

# Currency / unit WORDS belong to the claim's VALUE (scored separately via the shared
# ``_normalize_value``), not to its KEY TERMS — keying on "usd" would let a source agree on the unit
# while disagreeing on the figure, and would penalize a source that writes "$" instead of "USD". So
# these are excluded from key terms. (Mirrors the unit/currency vocabulary the integrity checker uses
# for value parsing; kept as a token-membership set here because that module exposes a span regex,
# not a token set — same vocabulary, different shape.)
_UNIT_TERMS = frozenset({
    "usd", "us", "eur", "gbp", "usdc", "dollar", "dollars", "euro", "euros", "pound", "pounds",
    "cent", "cents", "day", "days", "hour", "hours", "minute", "minutes", "month", "months",
    "year", "years", "week", "weeks", "percent", "pct", "time", "times", "attempt", "attempts",
    "retry", "retries", "thousand", "million", "billion",
})

# A claim-term token must be at least this long to count, so stray 1-2 char fragments ("x", "an")
# never become key terms. (Numbers are handled separately as the VALUE, not as a term.)
_MIN_TERM_LEN = 3


def _ensure_min_independent(value: Any) -> int:
    """Coerce/validate min_independent to an int >= 1, else raise (on_error = raise)."""
    if isinstance(value, bool):  # bool is an int subclass — reject explicitly
        raise TypeError("min_independent must be an int, got bool")
    if not isinstance(value, int):
        raise TypeError(f"min_independent must be an int, got {type(value).__name__}")
    if value < 1:
        raise ValueError(f"min_independent must be >= 1, got {value}")
    return value


def _source_id(src: Any, index: int) -> str:
    """Extract the publisher / source id for INDEPENDENCE keying.

    Independence is by distinct publisher, so the id is what collapses three copies from one
    publisher into one voice. Accepts the common spellings; falls back to a positional id ONLY when a
    source carries no identity at all (so an un-identified source is still its own voice rather than
    silently merging with another).
    """
    if isinstance(src, dict):
        for key in ("source_id", "publisher", "source", "id", "origin", "outlet", "domain"):
            val = src.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip().lower()
            if isinstance(val, dict):
                # nested {"publisher": {"id": "..."}} / source_record-style wrapper
                for inner_key in ("id", "name", "slug", "publisher"):
                    inner = val.get(inner_key)
                    if isinstance(inner, str) and inner.strip():
                        return inner.strip().lower()
    return f"__unidentified_{index}"


def _source_text(src: Any) -> str:
    """Extract the source body text, reusing the integrity checker's tolerant coercion."""
    if isinstance(src, str):
        return src
    if isinstance(src, dict):
        return _coerce_text("source", src)
    raise TypeError(f"each source must be str or dict, got {type(src).__name__}")


def _claim_terms(text: str) -> list[str]:
    """Deterministically extract the claim's KEY TERMS (significant content words).

    Lowercased, de-duplicated (preserving first-seen order for a stable audit trail), stripped of
    stopwords / unit words / short fragments; numbers excluded (the number is the VALUE, scored
    separately). Hyphenated compounds are split into their ATOMIC parts and the compound is NOT also
    kept as a separate term — so "wire-transfer" and "wire transfer" yield the SAME term set
    ({wire, transfer}) and overlap identically. Keeping the compound too would double-count one
    concept (inflating the denominator) and would penalize the un-hyphenated spelling; atomic-only is
    the robust, drift-free choice.
    """
    seen: set[str] = set()
    terms: list[str] = []
    # Tokens are alpha runs allowing internal hyphens (wire-transfer) and apostrophes; pure numbers
    # are not matched here. Split each on hyphen into atomic words.
    for raw in re.findall(r"[A-Za-z][A-Za-z'\-]*", text.lower()):
        for tok in (p for p in raw.split("-") if p):
            if len(tok) < _MIN_TERM_LEN or tok in _TERM_STOPWORDS or tok in _UNIT_TERMS:
                continue
            if tok not in seen:
                seen.add(tok)
                terms.append(tok)
    return terms


def _claim_value(text: str) -> str | None:
    """Extract the claim's asserted VALUE (the thing sources must match to AGREE).

    v1 = the first numeric/threshold value in the claim, normalized via the SHARED
    ``_normalize_value`` so "$50k"/"USD 50,000" compare equal. Prefer a value attached to a NAMED
    threshold (``_extract_thresholds``) when present (more precise), else the first standalone value.
    Returns ``None`` when the claim carries no numeric value — a non-numeric claim still has key
    terms, and a source agrees by sharing those terms with no conflicting value (handled in
    :func:`_classify_text`).
    """
    thresholds = _extract_thresholds(text)
    if thresholds:
        # Deterministic pick: first threshold in source order. _extract_thresholds preserves
        # finditer order within each key; choose the value whose raw span appears earliest in text.
        best_norm: str | None = None
        best_pos = len(text) + 1
        for _key, vals in thresholds.items():
            for norm, span in vals:
                # locate the raw value text within the span to order deterministically
                pos = text.lower().find(span.split("=")[-1].strip().lower())
                if 0 <= pos < best_pos:
                    best_pos, best_norm = pos, norm
        if best_norm is not None:
            return best_norm
    m = _VALUE_RE.search(text)
    if m:
        norm = _normalize_value(m.group(0))
        # A bare unit-less token that normalizes to empty is not a usable value.
        return norm or None
    return None


def _values_in_text(text: str) -> set[str]:
    """All normalized numeric values present in *text* (for detecting a CONTRADICTING value)."""
    out: set[str] = set()
    for m in _VALUE_RE.finditer(text):
        norm = _normalize_value(m.group(0))
        if norm:
            out.add(norm)
    return out


def _term_overlap(claim_terms: list[str], source_text: str) -> float:
    """Fraction of the claim's key terms that appear in *source_text* (0..1)."""
    if not claim_terms:
        return 0.0
    src_terms = set(_claim_terms(source_text))
    hit = sum(1 for t in claim_terms if t in src_terms)
    return hit / len(claim_terms)


# ─── Per-source classification ───────────────────────────────────────────────


def _classify_text(claim_terms: list[str], claim_value: str | None, source_text: str) -> str:
    """Classify ONE source's stance on the claim: 'support' | 'contradict' | 'silent'.

    Deterministic v1:
      * SILENT  — the source does not share enough of the claim's key terms (off-topic).
      * Once on-topic (term overlap >= floor):
          - if the claim has a numeric VALUE:
                SUPPORT    if the source contains that same normalized value;
                CONTRADICT if the source contains a DIFFERENT numeric value of the same kind but
                           not the claim's value (it addresses the subject with a conflicting figure);
                SILENT     if the on-topic source carries NO numeric value at all (it discusses the
                           subject but does not assert a comparable figure — under-count, never invent).
          - if the claim has NO numeric value (qualitative claim):
                SUPPORT    — sharing the key terms is agreement for a v1 qualitative claim.
                (A qualitative *negation* is a documented seam: lexical v1 does not parse "not"
                reliably, so we do not assert a contradiction we cannot defend.)
    """
    if _term_overlap(claim_terms, source_text) < TERM_OVERLAP_FLOOR:
        return "silent"

    if claim_value is None:
        # Qualitative claim, on-topic source: agreement in v1 (negation is a seam).
        return "support"

    src_values = _values_in_text(source_text)
    if claim_value in src_values:
        return "support"
    if src_values:  # on-topic, carries a value, but NOT the claim's value -> conflict
        return "contradict"
    return "silent"  # on-topic but asserts no comparable figure


def _reduce_publisher(stances: list[str]) -> str:
    """Collapse one publisher's (possibly many) copies into ONE independent stance.

    A publisher is ONE voice. If any of its sources CONTRADICT the claim the publisher is counted as
    contradicting (an internally-inconsistent or self-contradicting publisher is treated as a
    conflict, the safe direction — do not let it also count as agreement). Else if any SUPPORT, the
    publisher supports. Else the publisher is silent. This is what stops three copies from one
    publisher counting as three agreeing voices.
    """
    if "contradict" in stances:
        return "contradict"
    if "support" in stances:
        return "support"
    return "silent"


# ─── The corroborator ──────────────────────────────────────────────────────


def run(
    claim: Any,
    sources: Any,
    min_independent: int = DEFAULT_MIN_INDEPENDENT,
) -> dict[str, Any]:
    """Count INDEPENDENT corroboration of *claim* across *sources*. Cheap. Pure. Deterministic.

    Args:
        claim: the claim text (str) or a record dict carrying it (``{"text"|"content"|...}``).
        sources: an iterable of sources. Each source is a str (just text) or a dict carrying the
            text (``text``/``content``/...) and an identity (``source_id``/``publisher``/...). The
            identity is what defines INDEPENDENCE — three sources with the same id are one voice.
        min_independent: minimum number of independent AGREEING publishers required for the
            ``corroborated`` verdict (default :data:`DEFAULT_MIN_INDEPENDENT`, the contract's bar).

    Returns:
        {
          "corroboration": float in [0, 1],   # agreeing independent / max(agreeing+contradicting,
                                               # min_independent) — see note below
          "verdict": "corroborated" | "single-source" | "contradicted" | "uncorroborated",
          "agreeing_independent": int,         # distinct publishers that SUPPORT
          "contradicting_independent": int,    # distinct publishers that CONTRADICT
          "min_independent": int,              # the bar applied
          "supporting_source_ids": [str, ...], # distinct publisher ids that support (sorted)
          "contradicting_source_ids": [str, ...],
          "silent_source_ids": [str, ...],
          "claim_value": str | None,           # the normalized value the claim asserts (if numeric)
          "claim_terms": [str, ...],           # the extracted key terms (audit trail)
          "per_publisher": { id: "support|contradict|silent", ... },
          "method": METHOD,
        }

    Verdict rules:
      * ``contradicted``   — at least one INDEPENDENT publisher asserts a conflicting value. Surfaced
        first because a single credible contradiction means the claim is NOT safely established (it
        is the input to cross-source reconciliation).
      * ``corroborated``   — agreeing independent publishers >= ``min_independent`` AND none
        contradict.
      * ``single-source``  — exactly the situation the contract warns against: 1..(min-1) independent
        publishers agree, none contradict. Real support, but below the bar — hold for a second
        independent confirmation; do NOT treat as established.
      * ``uncorroborated`` — no independent publisher supports the claim (all silent).
    """
    claim_text = _coerce_text("claim", claim)
    min_independent = _ensure_min_independent(min_independent)

    if isinstance(sources, (str, bytes, dict)):
        raise TypeError("sources must be a list/iterable of source records, not a single value")
    try:
        source_list = list(sources)
    except TypeError as exc:  # not iterable
        raise TypeError("sources must be an iterable of source records") from exc

    claim_terms = _claim_terms(claim_text)
    claim_value = _claim_value(claim_text)

    # Group each source's stance by publisher id (independence), preserving determinism.
    per_pub_stances: dict[str, list[str]] = {}
    for idx, src in enumerate(source_list):
        text = _source_text(src)
        sid = _source_id(src, idx)
        stance = _classify_text(claim_terms, claim_value, text)
        per_pub_stances.setdefault(sid, []).append(stance)

    # Collapse to ONE stance per publisher -> independence.
    per_publisher: dict[str, str] = {
        sid: _reduce_publisher(stances) for sid, stances in per_pub_stances.items()
    }

    supporting = sorted(sid for sid, st in per_publisher.items() if st == "support")
    contradicting = sorted(sid for sid, st in per_publisher.items() if st == "contradict")
    silent = sorted(sid for sid, st in per_publisher.items() if st == "silent")

    agreeing = len(supporting)
    against = len(contradicting)

    # Verdict (order matters — contradiction dominates, then the bar, then single-source).
    if against > 0:
        verdict = "contradicted"
    elif agreeing >= min_independent:
        verdict = "corroborated"
    elif agreeing >= 1:
        verdict = "single-source"
    else:
        verdict = "uncorroborated"

    # Corroboration score in [0,1]: agreeing share of the WEIGHED-IN voices, where the denominator is
    # at least min_independent so that "1 agreeing, bar=2, none against" reads as 0.5 (half-way to the
    # bar), not a misleadingly perfect 1.0. With contradictions the denominator is the contested set
    # (agreeing + contradicting), so 2 agree / 1 contradicts -> ~0.67. Deterministic, bounded.
    denom = max(agreeing + against, min_independent, 1)
    corroboration = round(agreeing / denom, 4)

    return {
        "corroboration": corroboration,
        "verdict": verdict,
        "agreeing_independent": agreeing,
        "contradicting_independent": against,
        "min_independent": min_independent,
        "supporting_source_ids": supporting,
        "contradicting_source_ids": contradicting,
        "silent_source_ids": silent,
        "claim_value": claim_value,
        "claim_terms": claim_terms,
        "per_publisher": per_publisher,
        "method": METHOD,
    }


# ─── Self-test (offline) ──────────────────────────────────────────────────────


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    claim = "The daily wire-transfer limit is USD 10,000 per account."

    # 1) Three DISTINCT publishers all asserting USD 10,000 -> CORROBORATED.
    print("[self-test] 3 distinct publishers agreeing -> corroborated")
    three_distinct = [
        {"source_id": "reuters", "text": "Reuters: the daily wire-transfer limit is USD 10,000."},
        {"source_id": "acme-treasury", "text": "Treasury memo confirms the wire-transfer limit is $10,000 per account."},
        {"source_id": "central-bank", "text": "Per the regulator, the wire transfer limit is USD 10,000 daily."},
    ]
    res = run(claim, three_distinct)
    check("3-distinct verdict is corroborated", res["verdict"] == "corroborated", detail=json.dumps(res))
    check("3-distinct agreeing == 3", res["agreeing_independent"] == 3, detail=str(res["agreeing_independent"]))
    check("3-distinct none contradict", res["contradicting_independent"] == 0, detail=str(res))
    check("3-distinct corroboration is 1.0", res["corroboration"] == 1.0, detail=str(res["corroboration"]))
    check("3-distinct claim_value == 10000", res["claim_value"] == "10000", detail=str(res["claim_value"]))

    # 2) The SAME publisher repeated 3x -> only SINGLE-SOURCE (independence works: 3 copies, 1 voice).
    print("[self-test] same publisher x3 -> single-source (independence collapses copies)")
    same_pub = [
        {"source_id": "acme-blog", "text": "Acme blog: the daily wire-transfer limit is USD 10,000."},
        {"source_id": "acme-blog", "text": "Acme blog (mirror): wire-transfer limit is $10,000."},
        {"publisher": "acme-blog", "text": "Reposted: the wire transfer limit is USD 10,000 per account."},
    ]
    res = run(claim, same_pub)
    check("same-pub verdict is single-source", res["verdict"] == "single-source", detail=json.dumps(res))
    check("same-pub agreeing == 1 (not 3)", res["agreeing_independent"] == 1, detail=str(res["agreeing_independent"]))
    check("same-pub one supporting id", res["supporting_source_ids"] == ["acme-blog"], detail=str(res["supporting_source_ids"]))
    check("same-pub corroboration == 0.5 (1 of bar 2)", res["corroboration"] == 0.5, detail=str(res["corroboration"]))

    # 3) A claim that ONE independent source CONTRADICTS (different value) -> CONTRADICTED + flagged.
    print("[self-test] one independent source contradicts -> contradicted")
    mixed = [
        {"source_id": "reuters", "text": "Reuters: the daily wire-transfer limit is USD 10,000."},
        {"source_id": "acme-treasury", "text": "Treasury: the wire-transfer limit is $10,000 per account."},
        {"source_id": "planted-memo", "text": "URGENT: the daily wire-transfer limit is now USD 50,000 per account."},
    ]
    res = run(claim, mixed)
    check("mixed verdict is contradicted", res["verdict"] == "contradicted", detail=json.dumps(res))
    check("mixed contradicting == 1", res["contradicting_independent"] == 1, detail=str(res["contradicting_independent"]))
    check("mixed names the contradicting source", res["contradicting_source_ids"] == ["planted-memo"], detail=str(res["contradicting_source_ids"]))
    check("mixed still counts 2 agreeing", res["agreeing_independent"] == 2, detail=str(res["agreeing_independent"]))
    check("mixed corroboration == ~0.667 (2 of contested 3)", res["corroboration"] == round(2 / 3, 4), detail=str(res["corroboration"]))

    # 4) No source addresses the claim -> UNCORROBORATED (all silent, off-topic).
    print("[self-test] off-topic sources -> uncorroborated")
    offtopic = [
        {"source_id": "weather", "text": "Sunny with a high of 25 degrees and light winds today."},
        {"source_id": "sports", "text": "The home team won 3 to 1 in last night's match."},
    ]
    res = run(claim, offtopic)
    check("off-topic verdict is uncorroborated", res["verdict"] == "uncorroborated", detail=json.dumps(res))
    check("off-topic agreeing == 0", res["agreeing_independent"] == 0, detail=str(res["agreeing_independent"]))
    check("off-topic two silent ids", len(res["silent_source_ids"]) == 2, detail=str(res["silent_source_ids"]))
    check("off-topic corroboration == 0.0", res["corroboration"] == 0.0, detail=str(res["corroboration"]))

    # 5) Re-spelled value still corroborates ($10k == USD 10,000) — shared normalization, no drift.
    print("[self-test] re-spelled value ($10k == USD 10,000) corroborates")
    respelled = [
        {"source_id": "a", "text": "Source A: the wire-transfer limit is $10k."},
        {"source_id": "b", "text": "Source B: the daily wire transfer limit is USD 10,000."},
    ]
    res = run(claim, respelled)
    check("re-spelled verdict is corroborated", res["verdict"] == "corroborated", detail=json.dumps(res))
    check("re-spelled agreeing == 2", res["agreeing_independent"] == 2, detail=str(res["agreeing_independent"]))

    # 6) min_independent raises the bar: 2 distinct agreeing with bar=3 -> single-source, not corroborated.
    print("[self-test] min_independent raises the bar (2 agree, bar=3 -> single-source)")
    two_distinct = [
        {"source_id": "a", "text": "A: the wire-transfer limit is USD 10,000."},
        {"source_id": "b", "text": "B: the wire-transfer limit is $10,000."},
    ]
    res = run(claim, two_distinct, min_independent=3)
    check("bar=3 with 2 agreeing is single-source", res["verdict"] == "single-source", detail=json.dumps(res))
    check("bar=3 echoed in result", res["min_independent"] == 3, detail=str(res["min_independent"]))
    # Same two with the DEFAULT bar (2) IS corroborated — proves the bar is what moved the verdict.
    res2 = run(claim, two_distinct)
    check("same 2 with default bar=2 is corroborated", res2["verdict"] == "corroborated", detail=json.dumps(res2))

    # 7) Qualitative (non-numeric) claim corroborated by shared key terms.
    print("[self-test] qualitative claim corroborated by shared key terms")
    qual_claim = "The merger between Acme and Globex was approved by regulators."
    qual_sources = [
        {"source_id": "ft", "text": "The Acme Globex merger was approved by regulators last week."},
        {"source_id": "bloomberg", "text": "Regulators approved the merger of Acme and Globex."},
    ]
    res = run(qual_claim, qual_sources)
    check("qualitative claim has no numeric value", res["claim_value"] is None, detail=str(res["claim_value"]))
    check("qualitative verdict is corroborated", res["verdict"] == "corroborated", detail=json.dumps(res))
    check("qualitative agreeing == 2", res["agreeing_independent"] == 2, detail=str(res["agreeing_independent"]))

    # 8) On-topic but value-silent source does NOT count as agreement (under-count, never invent).
    print("[self-test] on-topic but no figure -> silent, not support")
    topic_no_value = [
        {"source_id": "vague", "text": "There is a daily wire-transfer limit policy in effect for accounts."},
    ]
    res = run(claim, topic_no_value)
    check("topic-no-value is silent (uncorroborated)", res["verdict"] == "uncorroborated", detail=json.dumps(res))
    check("topic-no-value agreeing == 0", res["agreeing_independent"] == 0, detail=str(res["agreeing_independent"]))

    # 9) Plain-string sources (no dict) each count as their own (unidentified) voice.
    print("[self-test] plain-string sources each count as a distinct voice")
    string_sources = [
        "The daily wire-transfer limit is USD 10,000 per account.",
        "Confirmed: the wire transfer limit is $10,000.",
    ]
    res = run(claim, string_sources)
    check("string-sources verdict is corroborated", res["verdict"] == "corroborated", detail=json.dumps(res))
    check("string-sources agreeing == 2", res["agreeing_independent"] == 2, detail=str(res["agreeing_independent"]))

    # 10) Determinism: identical inputs -> identical output.
    print("[self-test] deterministic")
    a = run(claim, mixed)
    b = run(claim, mixed)
    check("run is deterministic", a == b)

    # 11) Bad inputs raise (on_error = raise), not silently mis-scored.
    print("[self-test] invalid inputs raise")
    raised_sources = False
    try:
        run(claim, "a single string is not a list of sources")  # type: ignore[arg-type]
    except TypeError:
        raised_sources = True
    check("string-instead-of-list sources raises TypeError", raised_sources)

    raised_min = False
    try:
        run(claim, three_distinct, min_independent=0)
    except ValueError:
        raised_min = True
    check("min_independent < 1 raises ValueError", raised_min)

    raised_min_type = False
    try:
        run(claim, three_distinct, min_independent=True)  # type: ignore[arg-type]
    except TypeError:
        raised_min_type = True
    check("min_independent as bool raises TypeError", raised_min_type)

    raised_claim = False
    try:
        run(12345, three_distinct)  # type: ignore[arg-type]
    except TypeError:
        raised_claim = True
    check("non-text claim raises TypeError", raised_claim)

    # ── Aggregate assertion: ALL must pass (the task's "assert all and print PASS"). ──
    assert not failures, f"{len(failures)} self-test assertion(s) failed: {failures}"

    print("\nPASS — all self-tests passed (3 distinct publishers corroborate; the SAME publisher "
          "x3 is only single-source [independence]; one contradicting source flags 'contradicted'; "
          "off-topic is uncorroborated; re-spelled values agree; the bar is configurable).")
    return 0


# ─── CLI ──────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Deterministic multi-source corroborator — count INDEPENDENT publishers that "
                    "support vs contradict a claim (the change-verification ≥2-source bar as a tool).",
    )
    p.add_argument("--claim", help="The claim text to corroborate")
    p.add_argument("--sources", help="Path to a JSON file: a list of source records "
                                     "({\"text\": ..., \"source_id\": ...}) or strings")
    p.add_argument("--min-independent", type=int, default=DEFAULT_MIN_INDEPENDENT,
                   help=f"Minimum independent agreeing publishers for 'corroborated' "
                        f"(default {DEFAULT_MIN_INDEPENDENT})")
    p.add_argument("--self-test", action="store_true", help="Run the offline self-test")
    args = p.parse_args(argv)

    if args.self_test or not args.claim or not args.sources:
        # Default action with no args is the self-test (matches sibling processors).
        return _self_test()

    from pathlib import Path
    sources = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    res = run(args.claim, sources, min_independent=args.min_independent)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    # Exit non-zero when the claim is NOT corroborated — usable as a CI / pipeline gate.
    return 0 if res["verdict"] == "corroborated" else 1


if __name__ == "__main__":
    sys.exit(_main())
