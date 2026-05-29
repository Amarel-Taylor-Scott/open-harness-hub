#!/usr/bin/env python3
"""Backs `processor/compression-fidelity-check` (process_kind ``verify.compression_fidelity``).

CEaaS lives or dies on **measured fidelity per tier**: compress too aggressively
and you destroy the model's ability to reason. Every ``raw -> compressed ->
hyper-efficient`` artifact must ship a *published quality delta* — "did this tier
preserve enough?" — and that score must come from a **SEPARATE evaluator, never
self-graded** (see ``docs/strategy/context-enrichment-service.md`` §"Measured
fidelity per tier"). This module is that separate evaluator. It looks only at the
``raw`` and the ``tier`` content; it has no link to whatever produced the tier, so
a compressor can never grade its own homework.

What it measures
----------------
``run(raw, tier, ...)`` scores how much of the RAW's information the tier
preserved, using **deterministic, defensible retention signals** — the load-bearing,
hard-to-paraphrase tokens that carry meaning and that aggressive compression tends
to drop first:

  * ``identifier``  — code identifiers / API symbols / snake_case / CamelCase / dotted
    paths (``foo.bar.run``), the things a structural compressor is *supposed* to keep;
  * ``signature``  — call-signature / def-line shapes (``def f(...)``, ``class C(...)``,
    ``f(a, b)``) — the explicit promise of the structural tier ("strip bodies, keep
    signatures");
  * ``number``      — numerics, versions, quantities, percentages (``3.14``, ``v2.0``,
    ``70%``) — facts that cannot be re-derived if dropped;
  * ``heading``     — section/heading lines (markdown ``#``, ``Foo:``, ALL-CAPS lines) —
    the document's skeleton;
  * ``entity``      — cited proper-noun entities / acronyms (``CSDDD``, ``OpenAI``,
    ``Tree-sitter``) — the "who/what" a summary must not lose.

For each class we compute *recall of the raw's high-signal tokens into the tier*
(weighted by how load-bearing the class is), combine into a single ``fidelity`` in
``[0, 1]``, and emit ``token_reduction`` plus the concrete ``retained_signals`` /
``dropped_signals`` so the score is auditable, not a black box.

Honest scope (the seam)
-----------------------
This is a **deterministic proxy pending an LLM-judge upgrade**. It measures
*surface-form retention of high-signal tokens*, which is a strong, cheap, and
fully reproducible correlate of preserved information — but it cannot judge
whether the tier preserved *reasoning* or *meaning* the way a separate LLM judge
will. The manifest is therefore ``deterministic: false`` for the
``verify.compression_fidelity`` capability as a whole (the eventual judge is
non-deterministic); this proxy implementation, by contrast, is itself fully
deterministic and self-consistent (same inputs -> same score), which is exactly
what makes it a trustworthy floor and a clean A/B baseline for the judge. The
LLM-judge upgrade is the seam: it plugs in behind the same ``run(...)`` contract
and the same output keys.

Interface
---------
    from scripts.processors.verify.compression_fidelity_check import run
    res = run(raw, tier)
    # -> {"fidelity": 0.0..1.0, "token_reduction": float, "retained_signals": {...},
    #     "dropped_signals": {...}, "verdict": "high|adequate|degraded|gutted",
    #     "per_class": {...}, "tokens": {...}, "method": "deterministic_signal_recall_proxy"}

``raw`` and ``tier`` may each be a plain ``str`` OR a dict wrapper as emitted by the
sibling compressors (``compress.structural`` / ``summarize.llmlingua`` emit
``{"compressed": "..."}``); the text is pulled from the first of
``compressed / content / text / body / raw`` present, else ``str(obj)``.

CLI / self-test:
    python3 scripts/processors/verify/compression_fidelity_check.py
    python3 -m scripts.processors.verify.compression_fidelity_check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

# ─── Tunable constants (single source; unit/rationale inline) ────────────────

# How load-bearing each signal class is for "did the tier preserve information?".
# Identifiers + signatures carry the most reasoning-relevant content for the
# code/structural tier; numbers + entities are unrecoverable facts; headings are
# the skeleton. Weights are relative (normalized per-run over whichever classes
# the raw actually contains), so an entity-free code blob is judged only on the
# classes it has — never penalized for a class it never had.
SIGNAL_WEIGHTS: dict[str, float] = {
    "signature": 3.0,   # explicit promise of the structural tier
    "identifier": 2.5,  # API symbols / names — the thing compression must keep
    "number": 2.0,      # facts that cannot be re-derived if dropped
    "entity": 1.5,      # cited proper nouns / acronyms (the "who/what")
    "heading": 1.0,     # document skeleton
}

# Verdict bands over the final fidelity score. Calibrated against what *correct*
# compression actually scores under surface-recall: a structurally-faithful code
# tier ("strip bodies, keep signatures + declared constants + structure") still
# sheds body-only literals (return placeholders, comment numbers, in-body attr
# accesses), so a *perfect* structural compression lands ~0.75-0.80, not 1.0 —
# Repomix bills itself "structure-lossless", not literal-lossless. Prose/summary
# tiers that keep every cited entity/number/heading land ~1.0. So "high" begins at
# 0.75; a gutted tier (signatures + constants destroyed) lands ~0 and reads
# "degraded"/"gutted". The LLM-judge upgrade (the seam) will recalibrate these.
VERDICT_BANDS: tuple[tuple[float, str], ...] = (
    (0.75, "high"),       # structure + signatures + facts preserved; ship it
    (0.55, "adequate"),   # minor loss; publishable with the delta shown
    (0.35, "degraded"),   # meaningful loss — reasoning likely impaired
    (0.0, "gutted"),      # high-signal content destroyed; do not ship this tier
)

# Min number of high-signal tokens in raw before per-class recall is trustworthy.
# Below this for ALL classes, raw is too small to score; we say so explicitly.
_MIN_SIGNAL_TOKENS = 1


# ─── Text extraction (accept str OR compressor dict wrapper) ─────────────────

_WRAPPER_TEXT_KEYS = ("compressed", "content", "text", "body", "raw")


def _as_text(obj: Any) -> str:
    """Pull the textual payload from a str or a compressor's dict wrapper.

    The sibling ``compress.*`` / ``summarize.*`` processors emit
    ``{"compressed": "..."}``; a raw record may carry ``{"content": "..."}``.
    We look for the first known text key, else fall back to ``str(obj)`` so the
    evaluator never silently scores an empty string for an unexpected shape.
    """
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        for k in _WRAPPER_TEXT_KEYS:
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v
        # Nested single-text dict (e.g. {"tier": {"compressed": ...}}): recurse once.
        for v in obj.values():
            if isinstance(v, dict):
                inner = _as_text(v)
                if inner:
                    return inner
        return ""
    if isinstance(obj, (list, tuple)):
        return "\n".join(_as_text(x) for x in obj)
    return str(obj)


# ─── Signal extraction (deterministic, defensible) ───────────────────────────

# A "word token" for the crude token-reduction ratio (whitespace/punct split).
_WORD_RE = re.compile(r"\S+")

# Code-ish identifiers / API symbols: dotted paths, snake_case, CamelCase, and
# plain >=3-char alnum words. Captured lowercased for case-insensitive recall,
# but dotted/cased shape is what makes them "high-signal" vs. ordinary prose.
_DOTTED_RE = re.compile(r"\b[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)+\b")
_SNAKE_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
_CAMEL_RE = re.compile(r"\b[A-Za-z]+[a-z0-9]+[A-Z][A-Za-z0-9]*\b")
_WORD_IDENT_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9]{2,}\b")

# Call / def signatures: ``def f(...)``, ``class C(...)``, ``func name(...)``,
# or a bare ``name(args)`` call. Normalized to ``name(...)`` so reformatting of
# the *argument list* doesn't count as lost signal — the NAME + arity-of-shape
# is the promise, not the exact whitespace.
_DEF_RE = re.compile(
    r"\b(?:def|class|func|function|fn|sub|method|public|private|static)\s+"
    r"([A-Za-z_]\w*)\s*\(([^)]*)\)"
)
_CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(([^)]*)\)")

# Numerics: ints/floats/versions/percentages/hex. Keep the literal form (``v2.0``,
# ``70%``, ``0x1f``) since the exact value is the fact. ``%`` binds to the trailing
# digit (there is no word boundary between ``0`` and ``%``), so it is matched
# explicitly rather than relying on a closing ``\b``.
_NUMBER_RE = re.compile(r"\b(?:0x[0-9a-fA-F]+|v?\d+(?:\.\d+)*)%?")

# Cited entities: ALL-CAPS acronyms (>=2), TitleCase-with-internal-cap or
# Hyphenated-Proper nouns (``Tree-sitter``, ``OpenAI``, ``LLMLingua``). Common
# leading English stopwords (sentence-initial "The", "A", ...) are excluded.
_ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,}\b")
_PROPER_RE = re.compile(r"\b[A-Z][a-z]+(?:[-/][A-Z][A-Za-z]+|[A-Z][A-Za-z]*)+\b")
_STOPWORD_PROPER = frozenset({"The", "A", "An", "This", "That", "These", "Those", "It", "Its"})


def _signature_tokens(text: str) -> set[str]:
    out: set[str] = set()
    for m in _DEF_RE.finditer(text):
        out.add(f"{m.group(1).lower()}()")
    for m in _CALL_RE.finditer(text):
        name = m.group(1)
        # Skip language keywords that look like calls (e.g. ``if (...)``).
        if name.lower() in {"if", "for", "while", "switch", "return", "with", "def",
                             "class", "func", "function", "fn", "and", "or", "not",
                             "in", "is", "print"}:
            continue
        out.add(f"{name.lower()}()")
    return out


def _identifier_tokens(text: str) -> set[str]:
    out: set[str] = set()
    for rx in (_DOTTED_RE, _SNAKE_RE, _CAMEL_RE):
        for m in rx.finditer(text):
            out.add(m.group(0).lower())
    return out


def _number_tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _NUMBER_RE.finditer(text)}


def _heading_tokens(text: str) -> set[str]:
    """Headings: markdown ``#`` lines, ``Label:`` lines, and short ALL-CAPS lines.

    Keyed by the lowercased heading TEXT (sans markers) so a tier that keeps the
    section but drops the ``#`` still counts as retaining the heading.
    """
    out: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        h: str | None = None
        if line.startswith("#"):
            # Markdown ATX heading only — a leading ``#`` followed by a SPACE.
            # A code/inline comment (``# ... 40 lines ...``, ``#!/usr/bin``) is
            # body content, not a heading, so it must not count as skeleton.
            if re.match(r"#{1,6}\s+\S", line):
                h = line.lstrip("#").strip()
        elif re.fullmatch(r"[A-Za-z][\w ./-]{0,60}:", line):
            h = line[:-1].strip()
        elif len(line) <= 60 and re.fullmatch(r"[A-Z0-9][A-Z0-9 _./-]+", line) and " " in line:
            h = line
        # Reject "headings" that are pure punctuation/ellipsis (``... foo ...``).
        if h and re.search(r"[A-Za-z0-9]", h) and not h.startswith("..."):
            out.add(h.lower())
    return out


def _entity_tokens(text: str) -> set[str]:
    out: set[str] = set()
    for m in _ACRONYM_RE.finditer(text):
        out.add(m.group(0).lower())
    for m in _PROPER_RE.finditer(text):
        if m.group(0) not in _STOPWORD_PROPER:
            out.add(m.group(0).lower())
    return out


_EXTRACTORS = {
    "signature": _signature_tokens,
    "identifier": _identifier_tokens,
    "number": _number_tokens,
    "heading": _heading_tokens,
    "entity": _entity_tokens,
}


def extract_signals(text: str) -> dict[str, set[str]]:
    """All high-signal token sets for a piece of text, keyed by signal class.

    Pure function of ``text``; this is what makes the score reproducible.
    """
    return {cls: extractor(text) for cls, extractor in _EXTRACTORS.items()}


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _name_segments(token: str) -> set[str]:
    """Symbol forms a token can be recognized by: itself, its dotted segments,
    and (for ``foo()``) the bare name.

    This makes recall *symbol-level*, not literal-string-level — the correct
    granularity for code. A structural compressor keeps ``def _bm25(...)`` but
    strips the body where ``self._bm25(...)`` is *called*; the symbol ``_bm25``
    survives, so the raw identifier ``self._bm25`` must count as retained. Both
    ``self._bm25`` (its terminal segment ``_bm25``) and ``_bm25()`` (its bare
    name ``_bm25``) reduce to the shared form ``_bm25``.
    """
    base = token[:-2] if token.endswith("()") else token
    segs = {base}
    if "." in base:
        segs.update(p for p in base.split(".") if p)
    return {s for s in segs if s}


def _tier_symbol_vocab(tier_signals: dict[str, set[str]]) -> set[str]:
    """Every symbol form present anywhere in the tier (identifiers + signature
    names + entities), flattened to bare segments for member-name matching."""
    vocab: set[str] = set()
    for cls in ("identifier", "signature", "entity"):
        for tok in tier_signals.get(cls, set()):
            vocab |= _name_segments(tok)
    return vocab


def _split_retained(
    cls: str,
    raw_set: set[str],
    tier_set: set[str],
    tier_symbol_vocab: set[str],
) -> tuple[set[str], set[str]]:
    """Partition ``raw_set`` into (retained, dropped) for one signal class.

    For ``identifier`` / ``signature`` (code symbols), a raw token is retained if
    its literal form is in the tier OR any of its symbol segments survives in the
    tier's flattened symbol vocabulary — crediting member-name preservation as
    described in ``_name_segments``. For ``number`` / ``heading`` / ``entity`` the
    match is the exact (lowercased) form, since the *value* is the fact and a
    partial match would be misleading.
    """
    if cls in ("identifier", "signature"):
        retained = {
            tok for tok in raw_set
            if tok in tier_set or (_name_segments(tok) & tier_symbol_vocab)
        }
    else:
        retained = raw_set & tier_set
    return retained, raw_set - retained


# ─── Scoring ──────────────────────────────────────────────────────────────────


def run(raw: Any, tier: Any, *, return_examples: int = 12) -> dict[str, Any]:
    """Score how much of ``raw``'s information ``tier`` preserved (separate-evaluator).

    Args:
        raw:  the full-fidelity source. ``str`` or a dict wrapper (``content`` etc.).
        tier: the compressed/distilled artifact to grade. ``str`` or a dict
              wrapper (``compressed`` etc., as the sibling compressors emit).
        return_examples: cap on how many concrete dropped/retained token examples
              to include per class in the result (auditability without bloat).

    Returns:
        {
          "fidelity": float,          # 0..1 — weighted recall of raw's high-signal tokens
          "token_reduction": float,   # 0..1 — 1 - tier_words/raw_words (clamped >= 0)
          "verdict": str,             # high | adequate | degraded | gutted | empty_tier | no_signal
          "retained_signals": {cls: [examples...]},  # raw signals found in tier
          "dropped_signals":  {cls: [examples...]},  # raw signals MISSING from tier
          "per_class": {cls: {"raw": n, "retained": n, "recall": f, "weight": w}},
          "tokens": {"raw_words": n, "tier_words": n,
                     "raw_signal_tokens": n, "retained_signal_tokens": n},
          "method": "deterministic_signal_recall_proxy",
          "note": "<honest scope / seam note>",
        }

    Raises:
        TypeError: if ``raw`` or ``tier`` is not str/dict/list/None (``on_error: raise``).
    """
    for label, obj in (("raw", raw), ("tier", tier)):
        if obj is not None and not isinstance(obj, (str, dict, list, tuple)):
            raise TypeError(
                f"compression_fidelity_check: {label!r} must be str/dict/list/None, "
                f"got {type(obj).__name__}"
            )

    raw_text = _as_text(raw)
    tier_text = _as_text(tier)

    raw_words = _word_count(raw_text)
    tier_words = _word_count(tier_text)
    token_reduction = 0.0 if raw_words == 0 else max(0.0, 1.0 - (tier_words / raw_words))

    raw_signals = extract_signals(raw_text)
    tier_signals = extract_signals(tier_text)
    tier_symbol_vocab = _tier_symbol_vocab(tier_signals)

    note = (
        "Deterministic proxy: weighted recall of high-signal tokens "
        "(signatures/identifiers/numbers/headings/entities) from raw into the "
        "tier. Measures surface-form retention, a reproducible correlate of "
        "preserved information. Pending an LLM-judge upgrade (the seam) that "
        "plugs in behind this same run(...) contract to judge preserved meaning."
    )

    per_class: dict[str, dict[str, Any]] = {}
    retained_signals: dict[str, list[str]] = {}
    dropped_signals: dict[str, list[str]] = {}

    total_raw_signal_tokens = 0
    total_retained_signal_tokens = 0

    weighted_recall_num = 0.0
    weighted_recall_den = 0.0

    for cls in _EXTRACTORS:
        raw_set = raw_signals[cls]
        tier_set = tier_signals[cls]
        n_raw = len(raw_set)
        if n_raw == 0:
            # Class absent from raw: do not score it (no penalty for a missing class).
            continue
        retained, dropped = _split_retained(cls, raw_set, tier_set, tier_symbol_vocab)
        recall = len(retained) / n_raw
        weight = SIGNAL_WEIGHTS[cls]

        per_class[cls] = {
            "raw": n_raw,
            "retained": len(retained),
            "recall": round(recall, 4),
            "weight": weight,
        }
        retained_signals[cls] = sorted(retained)[:return_examples]
        dropped_signals[cls] = sorted(dropped)[:return_examples]

        total_raw_signal_tokens += n_raw
        total_retained_signal_tokens += len(retained)
        weighted_recall_num += weight * recall
        weighted_recall_den += weight

    if total_raw_signal_tokens < _MIN_SIGNAL_TOKENS:
        # Raw had no high-signal tokens at all — can't measure fidelity this way.
        return {
            "fidelity": 1.0 if tier_words > 0 else 0.0,
            "token_reduction": round(token_reduction, 4),
            "verdict": "no_signal",
            "retained_signals": {},
            "dropped_signals": {},
            "per_class": {},
            "tokens": {
                "raw_words": raw_words,
                "tier_words": tier_words,
                "raw_signal_tokens": 0,
                "retained_signal_tokens": 0,
            },
            "method": "deterministic_signal_recall_proxy",
            "note": note + " (raw carried no high-signal tokens; fidelity not measurable by recall)",
        }

    if tier_words == 0:
        # Tier is empty but raw had signal → fully gutted.
        return {
            "fidelity": 0.0,
            "token_reduction": 1.0,
            "verdict": "empty_tier",
            "retained_signals": {c: [] for c in per_class},
            "dropped_signals": {c: dropped_signals[c] for c in per_class},
            "per_class": per_class,
            "tokens": {
                "raw_words": raw_words,
                "tier_words": 0,
                "raw_signal_tokens": total_raw_signal_tokens,
                "retained_signal_tokens": 0,
            },
            "method": "deterministic_signal_recall_proxy",
            "note": note,
        }

    fidelity = weighted_recall_num / weighted_recall_den if weighted_recall_den else 0.0
    fidelity = max(0.0, min(1.0, fidelity))

    verdict = next(label for thresh, label in VERDICT_BANDS if fidelity >= thresh)

    return {
        "fidelity": round(fidelity, 4),
        "token_reduction": round(token_reduction, 4),
        "verdict": verdict,
        "retained_signals": retained_signals,
        "dropped_signals": dropped_signals,
        "per_class": per_class,
        "tokens": {
            "raw_words": raw_words,
            "tier_words": tier_words,
            "raw_signal_tokens": total_raw_signal_tokens,
            "retained_signal_tokens": total_retained_signal_tokens,
        },
        "method": "deterministic_signal_recall_proxy",
        "note": note,
    }


# ─── Self-test (offline; proves the logic on a real example) ─────────────────


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if (detail and not ok) else ''}")
        if not ok:
            failures.append(name)

    # ── A real example: a Python module (raw) vs. two compressions of it. ──
    raw_code = '''\
# retrieval/hybrid_search.py
"""Hybrid lexical + vector retrieval over the governed corpus."""

import math
from typing import Any

BM25_K1 = 1.5
BM25_B = 0.75
DEFAULT_TOP_K = 20

class HybridRetriever:
    """Combine BM25 and pgvector cosine into one ranked list."""

    def __init__(self, alpha: float = 0.5, top_k: int = DEFAULT_TOP_K):
        self.alpha = alpha
        self.top_k = top_k

    def search(self, query: str, corpus: list[dict]) -> list[dict]:
        lexical = self._bm25(query, corpus)
        vector = self._cosine(query, corpus)
        return self._reciprocal_rank_fusion(lexical, vector)

    def _bm25(self, query: str, corpus: list[dict]) -> list[float]:
        # ... 40 lines of scoring ...
        return [0.0 for _ in corpus]

    def _cosine(self, query: str, corpus: list[dict]) -> list[float]:
        # ... embedding lookup + dot product ...
        return [0.0 for _ in corpus]

    def _reciprocal_rank_fusion(self, a, b):
        return sorted(range(len(a)), key=lambda i: a[i] + b[i])
'''

    # GOOD structural compression: bodies stripped, signatures + identifiers +
    # constants + headings kept (exactly what compress.structural promises).
    good_structural = '''\
# retrieval/hybrid_search.py
"""Hybrid lexical + vector retrieval over the governed corpus."""

BM25_K1 = 1.5
BM25_B = 0.75
DEFAULT_TOP_K = 20

class HybridRetriever:
    def __init__(self, alpha: float = 0.5, top_k: int = DEFAULT_TOP_K): ...
    def search(self, query: str, corpus: list[dict]) -> list[dict]: ...
    def _bm25(self, query: str, corpus: list[dict]) -> list[float]: ...
    def _cosine(self, query: str, corpus: list[dict]) -> list[float]: ...
    def _reciprocal_rank_fusion(self, a, b): ...
'''

    # GUTTED compression: prose blurb, signatures + identifiers + constants gone.
    gutted = "This file does some searching over documents and returns results."

    print("[self-test] real example: hybrid_search.py — good structural vs gutted")
    good = run(raw_code, good_structural)
    bad = run(raw_code, gutted)

    print(f"    good: fidelity={good['fidelity']} verdict={good['verdict']} "
          f"reduction={good['token_reduction']}")
    print(f"    bad:  fidelity={bad['fidelity']} verdict={bad['verdict']} "
          f"reduction={bad['token_reduction']}")

    # Core assertions the spec demands.
    # "high" bar (0.75) is calibrated to what a structurally-FAITHFUL code tier
    # actually scores under surface-recall — it still sheds body-only literals
    # (return placeholders, comment numbers, in-body attribute access), so a
    # perfect structural compression lands ~0.78, not 1.0 (see VERDICT_BANDS).
    check("good structural fidelity is HIGH (>=0.75)", good["fidelity"] >= 0.75,
          f"got {good['fidelity']}")
    check("gutted fidelity is LOW (<0.35)", bad["fidelity"] < 0.35,
          f"got {bad['fidelity']}")
    # The gap between a faithful tier and a gutted one is the whole product.
    check("faithful-vs-gutted gap is large (>=0.5)",
          good["fidelity"] - bad["fidelity"] >= 0.5,
          f"gap={good['fidelity'] - bad['fidelity']:.3f}")
    check("good fidelity strictly > gutted fidelity",
          good["fidelity"] > bad["fidelity"],
          f"{good['fidelity']} !> {bad['fidelity']}")
    check("good verdict in {high, adequate}", good["verdict"] in {"high", "adequate"},
          good["verdict"])
    check("gutted verdict in {degraded, gutted}", bad["verdict"] in {"degraded", "gutted"},
          bad["verdict"])
    check("good preserves the def signatures",
          "search()" in good["retained_signals"].get("signature", []),
          str(good["retained_signals"].get("signature")))
    check("good preserves the API identifiers",
          "hybridretriever" in good["retained_signals"].get("identifier", [])
          or "default_top_k" in good["retained_signals"].get("identifier", []),
          str(good["retained_signals"].get("identifier")))
    check("gutted drops the signatures (search() reported dropped)",
          "search()" in bad["dropped_signals"].get("signature", []),
          str(bad["dropped_signals"].get("signature")))
    check("gutted drops the numeric constants (1.5 / 0.75 dropped)",
          "1.5" in bad["dropped_signals"].get("number", [])
          and "0.75" in bad["dropped_signals"].get("number", []),
          str(bad["dropped_signals"].get("number")))

    # Token reduction must be a real, sane ratio in both cases.
    check("good token_reduction in (0,1)", 0.0 < good["token_reduction"] < 1.0,
          str(good["token_reduction"]))
    check("gutted token_reduction higher than good (more was thrown away)",
          bad["token_reduction"] > good["token_reduction"],
          f"{bad['token_reduction']} !> {good['token_reduction']}")

    # ── Determinism: same inputs -> identical score (the proxy's guarantee). ──
    print("[self-test] determinism: identical inputs -> identical result")
    again = run(raw_code, good_structural)
    check("run is deterministic", again == good)

    # ── Monotonicity: a middle tier sits between good and gutted. ──
    print("[self-test] monotonicity: partial compression sits between")
    partial = '''\
class HybridRetriever:
    def search(self, query, corpus): ...
    def _bm25(self, query, corpus): ...
'''  # keeps some signatures/identifiers, drops constants + other defs
    mid = run(raw_code, partial)
    print(f"    mid:  fidelity={mid['fidelity']} verdict={mid['verdict']}")
    check("partial fidelity between gutted and good",
          bad["fidelity"] < mid["fidelity"] < good["fidelity"],
          f"{bad['fidelity']} < {mid['fidelity']} < {good['fidelity']}")

    # ── Dict-wrapper inputs (as the sibling compressors emit). ──
    print("[self-test] accepts compressor dict wrappers ({'compressed': ...})")
    wrapped = run({"content": raw_code}, {"compressed": good_structural})
    check("dict-wrapped inputs match str inputs", wrapped == good,
          "wrapper extraction diverged from str path")

    # ── A prose / markdown doc example (entities + headings + numbers). ──
    print("[self-test] prose example: spec doc with entities, headings, numbers")
    raw_doc = (
        "# Measured fidelity per tier\n"
        "CEaaS scores every tier with verify.compression_fidelity, never self-graded.\n"
        "Repomix achieves ~70% token reduction using Tree-sitter on code.\n"
        "LLMLingua-2 reaches 2-5x compression. OpenAI prompt cache cuts ~90% of input.\n"
        "## The seam\n"
        "An LLM judge upgrades this proxy behind the same contract.\n"
    )
    good_doc = (
        "# Measured fidelity per tier\n"
        "CEaaS scores tiers with verify.compression_fidelity, never self-graded.\n"
        "Repomix: ~70% reduction via Tree-sitter. LLMLingua-2: 2-5x. OpenAI cache ~90%.\n"
        "## The seam\n"
        "An LLM judge upgrades the proxy.\n"
    )
    gutted_doc = "Some notes about making text shorter for models."
    gdoc = run(raw_doc, good_doc)
    bdoc = run(raw_doc, gutted_doc)
    print(f"    good_doc: fidelity={gdoc['fidelity']} verdict={gdoc['verdict']}")
    print(f"    bad_doc:  fidelity={bdoc['fidelity']} verdict={bdoc['verdict']}")
    check("good doc keeps entities high", gdoc["fidelity"] >= 0.80, str(gdoc["fidelity"]))
    check("gutted doc fidelity low", bdoc["fidelity"] < 0.40, str(bdoc["fidelity"]))
    check("good doc retains CSDDD-style entities (repomix/llmlingua-2/openai)",
          any(e in gdoc["retained_signals"].get("entity", [])
              for e in ("repomix", "llmlingua-2", "openai", "tree-sitter")),
          str(gdoc["retained_signals"].get("entity")))
    check("good doc retains the 70% / 90% numbers",
          "70%" in gdoc["retained_signals"].get("number", [])
          and "90%" in gdoc["retained_signals"].get("number", []),
          str(gdoc["retained_signals"].get("number")))

    # ── Edge cases. ──
    print("[self-test] edge cases: empty tier, no-signal raw, bad type")
    empty = run(raw_code, "")
    check("empty tier -> fidelity 0.0, verdict empty_tier",
          empty["fidelity"] == 0.0 and empty["verdict"] == "empty_tier", str(empty["verdict"]))
    nosig = run("the cat sat on the mat and was warm", "a cat on a mat")
    check("no-signal raw -> verdict no_signal", nosig["verdict"] == "no_signal", str(nosig["verdict"]))
    raised = False
    try:
        run(123, "x")  # type: ignore[arg-type]
    except TypeError:
        raised = True
    check("bad input type raises TypeError (on_error: raise)", raised)

    # ── Output contract: every documented key present, fidelity in range. ──
    print("[self-test] output contract / key presence")
    for key in ("fidelity", "token_reduction", "retained_signals", "dropped_signals",
                "verdict", "per_class", "tokens", "method"):
        check(f"result has key {key!r}", key in good)
    check("fidelity in [0,1]", 0.0 <= good["fidelity"] <= 1.0)
    check("result is JSON-serializable", _is_json_safe(good))

    if failures:
        print(f"\nFAIL — {len(failures)} self-test assertion(s) failed: {failures}")
        return 1
    print("\nPASS — compression-fidelity proxy proven: signatures kept -> high "
          "fidelity, gutted -> low, deterministic, monotone, wrappers + prose + "
          "edge cases all green.")
    return 0


def _is_json_safe(obj: Any) -> bool:
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


# ─── CLI ──────────────────────────────────────────────────────────────────────


def _read(path_or_dash: str) -> str:
    if path_or_dash == "-":
        return sys.stdin.read()
    with open(path_or_dash, encoding="utf-8") as fh:
        return fh.read()


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=("Compression-fidelity check (verify.compression_fidelity): score "
                     "how much of RAW a compressed TIER preserved. Deterministic proxy.")
    )
    p.add_argument("--raw", help="Path to raw text ('-' for stdin)")
    p.add_argument("--tier", help="Path to compressed/tier text ('-' for stdin)")
    p.add_argument("--self-test", action="store_true", help="Run the offline self-test and exit")
    args = p.parse_args(argv)

    if args.self_test or (not args.raw and not args.tier):
        return _self_test()
    if not (args.raw and args.tier):
        p.error("provide BOTH --raw and --tier, or --self-test")

    res = run(_read(args.raw), _read(args.tier))
    print(json.dumps(res, indent=2, ensure_ascii=False))
    # Exit non-zero on a gutted/empty tier so the CLI is usable as a gate.
    return 0 if res["verdict"] in {"high", "adequate", "no_signal"} else 1


if __name__ == "__main__":
    sys.exit(_main())
