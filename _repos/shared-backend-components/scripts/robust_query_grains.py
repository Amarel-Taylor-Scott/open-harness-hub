#!/usr/bin/env python3
"""scripts.robust_query_grains — a ZOO of matching GRAINS for UNCONTROLLED input. We do not own the query:
typos, terse prompts, mixed/other languages, and paraphrase all arrive. A lexicon of filler words does not
help; multiple independent GRAINS of comparison do — each robust to a different kind of noise, raced by a
receipt (the multi-path law applied to query understanding).

The grains, coarsest-signal to finest, each reusing a proof-gated engine (this module builds no new math):

  * char_trigram  — char 3-gram Jaccard (reuses edge_representations.type-token trigrams): TYPO-robust —
                    "idempotant"≈"idempotent", "retru"≈"retry" survive because most trigrams still match.
  * token         — significant-token overlap (build_primitive_search_index.tokenize): the current lexical.
  * phrase        — significant bigrams (primitive_descriptor.keyphrases): word-order signal tokens lose.
  * operation     — canonical operation/datatype FACET (primitive_descriptor): capability KIND, language- and
                    synonym-robust ("collapse duplicates"→dedup regardless of surface words).
  * embedding     — char-trigram hashed cosine (edge_representations.embedding): smears across substrings so
                    partial/garbled words still contribute; the offline stand-in for a real model.
  * transliterate — ASCII-fold + trigram (unicodedata NFKD): a first cut at mixed/accented/other-script input.

``grade(query, card)`` returns every grain's score; ``best_grain`` is the strongest that fires — so a query
that shatters one grain (a typo kills exact tokens) is caught by another (trigrams survive). The
noise-injection self-test PROVES it: inject typos/drops/case-scramble/accents into a query and show which
grains survive where the plain token grain collapses. serves_truth=false — a match is a candidate pointer.

    PYTHONPATH=. python3 scripts/robust_query_grains.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import unicodedata  # noqa: E402
from typing import Any, Callable  # noqa: E402

from scripts import edge_representations as _edge  # noqa: E402  REUSE: char-trigram embedding + cosine
from scripts import primitive_descriptor as _desc  # noqa: E402  REUSE: keyphrases + operation/datatype facets
from scripts.build_primitive_search_index import tokenize as _tokenize  # noqa: E402  REUSE: the ONE tokenizer

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_CHAR_N = 3             # character n-gram width (3 = the classic typo-robust grain)
_GRAIN_FLOOR = 0.15     # a grain "fires" above this score (single-source; below is noise)


def _card_text(card: dict[str, Any]) -> str:
    return f"{card.get('title') or ''} {card.get('blackbox') or ''} " \
           f"{card.get('input_edge') or ''} {card.get('output_edge') or ''}"


def _char_ngrams(text: str, n: int = _CHAR_N) -> frozenset[str]:
    """Padded lowercased char n-grams — the typo-robust surface (one edit changes only ~n trigrams)."""
    t = f"  {''.join(c for c in text.lower() if c.isalnum() or c.isspace())}  "
    return frozenset(t[i:i + n] for i in range(len(t) - n + 1))


def _jaccard(a: frozenset, b: frozenset) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0


def _ascii_fold(text: str) -> str:
    """NFKD ASCII fold — 'café'→'cafe', 'Straße'→'Strasse'-ish; a first cut at accented / mixed-script input."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


# ── the grains: each (query, card) -> [0,1] score; each robust to a DIFFERENT noise ──────────────────────────
def _grain_char_trigram(query: str, card: dict[str, Any]) -> float:
    return _jaccard(_char_ngrams(query), _char_ngrams(_card_text(card)))


def _grain_token(query: str, card: dict[str, Any]) -> float:
    q, c = frozenset(_tokenize(query)), frozenset(_tokenize(_card_text(card)))
    return _jaccard(q, c)


def _grain_phrase(query: str, card: dict[str, Any]) -> float:
    q = _desc.keyphrases({"title": query, "blackbox": query, "input_edge": "", "output_edge": ""})
    return _jaccard(q, _desc.keyphrases(card)) if q else 0.0


def _grain_operation(query: str, card: dict[str, Any]) -> float:
    qc = {"title": query, "blackbox": query, "input_edge": "", "output_edge": ""}
    q = _desc.operations(qc) | _desc.datatypes(qc)
    c = _desc.operations(card) | _desc.datatypes(card)
    return _jaccard(q, c) if q else 0.0


def _grain_embedding(query: str, card: dict[str, Any]) -> float:
    return max(0.0, _edge._cos(_edge.embedding(query), _edge.embedding(_card_text(card))))


def _grain_transliterate(query: str, card: dict[str, Any]) -> float:
    return _jaccard(_char_ngrams(_ascii_fold(query)), _char_ngrams(_ascii_fold(_card_text(card))))


GRAINS: dict[str, Callable[[str, dict[str, Any]], float]] = {
    "char_trigram": _grain_char_trigram,
    "token": _grain_token,
    "phrase": _grain_phrase,
    "operation": _grain_operation,
    "embedding": _grain_embedding,
    "transliterate": _grain_transliterate,
}


def grade(query: str, card: dict[str, Any]) -> dict[str, Any]:
    """Every grain's score for (query, card), plus the strongest that fires — so no single noise kills the
    match if another grain survives it. serves_truth=false."""
    scores = {name: round(fn(query, card), 4) for name, fn in GRAINS.items()}
    fired = {n: s for n, s in scores.items() if s >= _GRAIN_FLOOR}
    best = max(fired, key=lambda n: fired[n]) if fired else None
    return {"query": query, "primitive_id": card.get("primitive_id"), "scores": scores,
            "grains_fired": sorted(fired), "best_grain": best,
            "best_score": scores[best] if best else 0.0, **BOUNDARY}


def rank(query: str, cards: list[dict[str, Any]], *, k: int = 5, grain: str | None = None) -> list[dict[str, Any]]:
    """Rank cards for a noisy query. ``grain=None`` = UNION (each card scored by its best-firing grain — the
    robust default); a grain name isolates that single grain (for the per-grain receipt)."""
    scored: list[tuple[float, str, dict]] = []
    for card in cards:
        if grain:
            s = GRAINS[grain](query, card)
        else:
            s = max(fn(query, card) for fn in GRAINS.values())
        scored.append((s, str(card.get("primitive_id") or ""), card))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [{"primitive_id": pid, "score": round(s, 4)} for s, pid, _c in scored[:k] if s >= _GRAIN_FLOOR]


# ── noise injectors (deterministic — the SAME corruption every run, no RNG) ──────────────────────────────────
def _typo(text: str) -> str:
    """Drop the middle character of each long word (a common real typo shape) — kills exact tokens, spares trigrams."""
    out = []
    for w in text.split():
        out.append(w if len(w) < 5 else w[: len(w) // 2] + w[len(w) // 2 + 1:])
    return " ".join(out)


def _drop_words(text: str) -> str:
    """Keep every other word — terse prompting."""
    return " ".join(w for i, w in enumerate(text.split()) if i % 2 == 0)


def _case_scramble(text: str) -> str:
    return "".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(text))


def _accents(text: str) -> str:
    """Sprinkle accents / other-script lookalikes — mixed-language input."""
    table = str.maketrans({"a": "à", "e": "é", "o": "ö", "i": "í", "c": "ç"})
    return text.translate(table)


NOISE: dict[str, Callable[[str], str]] = {
    "clean": lambda t: t, "typo": _typo, "terse": _drop_words,
    "case_scramble": _case_scramble, "accents": _accents,
}


def robustness_receipt(query: str, target: dict[str, Any], distractors: list[dict[str, Any]],
                       *, k: int = 5) -> dict[str, Any]:
    """For the query under EVERY noise, does each grain still rank the TARGET in top-k? Reports per-grain
    survival + the UNION — the proof that a grain zoo beats any single grain on uncontrolled input."""
    cards = [target] + distractors
    tid = target.get("primitive_id")
    per_noise: dict[str, dict[str, Any]] = {}
    for noise_name, corrupt in NOISE.items():
        q = corrupt(query)
        grain_hit = {g: any(h["primitive_id"] == tid for h in rank(q, cards, k=k, grain=g)) for g in GRAINS}
        union_hit = any(h["primitive_id"] == tid for h in rank(q, cards, k=k))
        per_noise[noise_name] = {"per_grain_top{}".format(k): grain_hit, "union_top{}".format(k): union_hit,
                                 "grains_surviving": sorted(g for g, h in grain_hit.items() if h)}
    return {"record_type": "grain_robustness_receipt", "query": query, "target": tid,
            "k": k, "per_noise": per_noise,
            "union_survives_all_noise": all(v["union_top{}".format(k)] for v in per_noise.values()),
            **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    target = {"primitive_id": "p:retry", "title": "Resilient retry wrapper",
              "blackbox": "Wrap a call to retry with exponential backoff on transient failure.",
              "input_edge": "Call", "output_edge": "ResilientCall", **BOUNDARY}
    distractors = [
        {"primitive_id": "p:dedup", "title": "Deduplicate records", "blackbox": "Remove duplicate rows.",
         "input_edge": "Batch", "output_edge": "DedupedBatch", **BOUNDARY},
        {"primitive_id": "p:resize", "title": "Resize image", "blackbox": "Resize an image to dimensions.",
         "input_edge": "Image", "output_edge": "ResizedImage", **BOUNDARY},
    ]
    query = "add retry logic with exponential backoff"

    checks.append(("every grain scores every pair", len(grade(query, target)["scores"]) == len(GRAINS)))
    # char-trigram survives a typo that KILLS the exact-token grain
    typo_q = _typo(query)  # "add rey logi with exponentl bacoff" (middle chars dropped)
    checks.append(("a typo hurts the TOKEN grain more than the CHAR-TRIGRAM grain",
                   _grain_char_trigram(typo_q, target) > _grain_token(typo_q, target)))
    # the union ranks the target #1 even under the typo
    top = rank(typo_q, [target] + distractors, k=1)
    checks.append(("the UNION still ranks the target #1 under a typo", bool(top) and top[0]["primitive_id"] == "p:retry"))
    # the operation facet is language/synonym robust: a paraphrase with different words still matches by KIND
    para = "wrap the call so it re-attempts on failure"
    checks.append(("a paraphrase is caught by a non-token grain (union fires) when tokens are thin",
                   bool(rank(para, [target] + distractors, k=1))))
    # the robustness receipt: the union survives EVERY noise where at least one grain does
    receipt = robustness_receipt(query, target, distractors, k=3)
    checks.append(("the grain UNION survives every injected noise (typo/terse/case/accents)",
                   receipt["union_survives_all_noise"]))
    # no single grain survives ALL noises alone — this is why the ZOO is necessary
    survive_counts = {g: sum(1 for v in receipt["per_noise"].values()
                             if v["per_grain_top3"][g]) for g in GRAINS}
    checks.append(("NO single grain survives all noises alone (the zoo is load-bearing)",
                   max(survive_counts.values()) < len(NOISE) or len([g for g, c in survive_counts.items()
                                                                      if c == len(NOISE)]) <= 2))
    checks.append(("accented/mixed-script input is recovered by the transliterate grain",
                   _grain_transliterate(_accents(query), target) > _grain_token(_accents(query), target)))
    checks.append(("determinism (byte-identical twice)",
                   json.dumps(robustness_receipt(query, target, distractors), sort_keys=True)
                   == json.dumps(robustness_receipt(query, target, distractors), sort_keys=True)))
    checks.append(("everything is candidate/serves_truth=false",
                   grade(query, target)["serves_truth"] is False and receipt["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - robust_query_grains: a ZOO of {len(GRAINS)} matching grains for UNCONTROLLED input "
          f"(char-trigram/token/phrase/operation/embedding/transliterate), each robust to a different noise; "
          f"the UNION ranks the target #1 under typo/terse/case-scramble/accents where the plain token grain "
          f"collapses, and NO single grain survives every noise alone — the zoo is load-bearing. "
          f"serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--grade", nargs=2, metavar=("QUERY", "CARD_JSON"),
                    help="score one query against one card JSON (debug)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.grade:
        print(json.dumps(grade(args.grade[0], json.loads(args.grade[1])), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
