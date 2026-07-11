#!/usr/bin/env python3
"""scripts.similarity_typo_primitives — the ALGORITHMS layer (owner-directed 2026-07-08): text comparison,
similarity, typo detection, and TYPO-KEYBOARD-DISTANCE detection, plus the outside-the-box hardcoded folds
companies actually use — all pure-python, oracle-tested against the classic literature values.

  * EDIT DISTANCES — Levenshtein (kitten/sitting=3), Damerau-Levenshtein (teh/the: transposition costs 1,
    not 2), Jaro and Jaro-Winkler (MARTHA/MARHTA = 0.961, the canonical example), longest common substring.
  * KEYBOARD DISTANCE — a QWERTY coordinate map gives PHYSICAL key distance, so a single substitution
    classifies as fat-finger-adjacent ('hane'->'jane': h and j touch) vs distant ('pane'->'jane': probably
    a different word). classify_typo names the edit (adjacent/distant substitution, transposition,
    insertion, deletion, doubled letter); typo_likelihood blends them into a score.
  * SET/SEQUENCE SIMILARITY — bigram Dice (night/nacht = 0.25, the textbook case), n-gram Jaccard,
    SimHash (64-bit char-ngram signature + Hamming) for near-duplicate text.
  * LSH NEAR-DUPLICATES — REUSES the multi-index's proven MinHash/band machinery (337M keys in production)
    at the string-list level: bucket near-duplicates without pairwise explosion.
  * HARDCODED CORPORATE FOLDS — the rules data teams re-write forever: Saint/St., ordinal streets
    (1st/First), Mc Donald -> McDonald, O Brien/OBrien/O'Brien folding, roman-numeral suffix folds
    (II <-> 2), and-variant folding (& / and / + / y / et / und) — each a versioned fold with match-key
    discipline (display untouched).

candidate=true, serves_truth=false.

    python3 scripts/similarity_typo_primitives.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any  # noqa: E402

from scripts.primitive_multi_index import lsh_band_keys, minhash  # noqa: E402 — proven at 337M keys
from scripts.string_standardization_primitives import tokenize_alnum  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"similarity_typo_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-simtypo"
FOLD_RULES_VERSION = "corporate-folds-v1"

#: QWERTY physical coordinates (row, column with stagger offsets) — the keyboard-distance basis
_QWERTY_ROWS = (("qwertyuiop", 0.0), ("asdfghjkl", 0.25), ("zxcvbnm", 0.75))
KEY_COORDS: dict[str, tuple[float, float]] = {
    ch: (float(r), i + offset) for r, (row, offset) in enumerate(_QWERTY_ROWS) for i, ch in enumerate(row)}
ADJACENT_KEY_MAX_DISTANCE = 1.2  # euclidean key-units: touching keys incl. diagonals


# ── EDIT DISTANCES (classic values as oracles) ───────────────────────────────────────────────────────────────
def levenshtein_distance(a: str, b: str) -> int:
    """Insert/delete/substitute edit distance (kitten -> sitting = 3)."""
    a, b = a or "", b or ""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def damerau_levenshtein_distance(a: str, b: str) -> int:
    """Edit distance where a TRANSPOSITION costs 1 ('teh' -> 'the' = 1, not 2) — the typo metric."""
    a, b = a or "", b or ""
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        d[i][0] = i
    for j in range(len(b) + 1):
        d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = a[i - 1] != b[j - 1]
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[len(a)][len(b)]


def jaro_similarity(a: str, b: str) -> float:
    a, b = a or "", b or ""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    window = max(len(a), len(b)) // 2 - 1
    a_flags, b_flags = [False] * len(a), [False] * len(b)
    matches = 0
    for i, ca in enumerate(a):
        for j in range(max(0, i - window), min(len(b), i + window + 1)):
            if not b_flags[j] and b[j] == ca:
                a_flags[i] = b_flags[j] = True
                matches += 1
                break
    if not matches:
        return 0.0
    transpositions = sum(1 for x, y in zip((c for i, c in enumerate(a) if a_flags[i]),
                                           (c for j, c in enumerate(b) if b_flags[j])) if x != y) // 2
    m = matches
    return round((m / len(a) + m / len(b) + (m - transpositions) / m) / 3, 6)


def jaro_winkler_similarity(a: str, b: str, *, prefix_scale: float = 0.1) -> float:
    """Jaro with common-prefix boost — the name-matching standard (MARTHA/MARHTA = 0.961)."""
    j = jaro_similarity(a or "", b or "")
    prefix = 0
    for ca, cb in zip((a or "")[:4], (b or "")[:4]):
        if ca != cb:
            break
        prefix += 1
    return round(j + prefix * prefix_scale * (1 - j), 3)


def longest_common_substring_len(a: str, b: str) -> int:
    a, b = a or "", b or ""
    best = 0
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0]
        for j, cb in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if ca == cb else 0)
            best = max(best, cur[-1])
        prev = cur
    return best


# ── KEYBOARD DISTANCE ─────────────────────────────────────────────────────────────────────────────────────────
def keyboard_key_distance(key_a: str, key_b: str) -> float:
    """Physical QWERTY distance between two keys in key-units (adjacent incl. diagonal <= ~1.2)."""
    pa, pb = KEY_COORDS.get((key_a or "").casefold()), KEY_COORDS.get((key_b or "").casefold())
    if pa is None or pb is None:
        return -1.0
    return round(((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2) ** 0.5, 4)


def classify_typo(a: str, b: str) -> dict[str, Any]:
    """Name the single edit between two strings: substitution_adjacent_key / substitution_distant_key /
    transposition / insertion / deletion / doubled_letter — or not_single_typo."""
    a, b = (a or "").casefold(), (b or "").casefold()
    if a == b:
        return {"classification": "identical", **BOUNDARY}
    if damerau_levenshtein_distance(a, b) != 1:
        return {"classification": "not_single_typo",
                "damerau_levenshtein": damerau_levenshtein_distance(a, b), **BOUNDARY}
    if len(a) == len(b):
        diffs = [(ca, cb) for ca, cb in zip(a, b) if ca != cb]
        if len(diffs) == 2:  # transposition
            return {"classification": "transposition", "keys": [diffs[0][0], diffs[0][1]], **BOUNDARY}
        ka, kb = diffs[0]
        dist = keyboard_key_distance(ka, kb)
        cls = ("substitution_adjacent_key" if 0 <= dist <= ADJACENT_KEY_MAX_DISTANCE
               else "substitution_distant_key")
        return {"classification": cls, "keys": [ka, kb], "key_distance": dist, **BOUNDARY}
    longer, shorter = (a, b) if len(a) > len(b) else (b, a)
    for i in range(len(longer)):
        if longer[:i] + longer[i + 1:] == shorter:
            extra = longer[i]
            doubled = (i > 0 and longer[i - 1] == extra) or (i + 1 < len(longer) and longer[i + 1] == extra)
            return {"classification": "doubled_letter" if doubled
                    else ("insertion" if longer == a else "deletion"), "key": extra, **BOUNDARY}
    return {"classification": "not_single_typo", **BOUNDARY}


def typo_likelihood(a: str, b: str) -> dict[str, Any]:
    """COMPOSITE: blend edit distance + typo class + keyboard adjacency into a likelihood that b is a TYPO
    of a (vs a genuinely different word). Adjacent-key substitutions and transpositions score highest."""
    cls = classify_typo(a, b)
    base = {"identical": 0.0, "transposition": 0.9, "doubled_letter": 0.85,
            "substitution_adjacent_key": 0.9, "substitution_distant_key": 0.45,
            "insertion": 0.7, "deletion": 0.7}.get(cls["classification"])
    if base is None:  # multi-edit: fall back to normalized DL + JW blend
        dl = damerau_levenshtein_distance((a or "").casefold(), (b or "").casefold())
        norm = 1 - min(dl / max(len(a or ""), len(b or ""), 1), 1.0)
        base = round(0.5 * norm + 0.3 * jaro_winkler_similarity(a, b), 4) if dl <= 3 else 0.05
    return {"a": a, "b": b, "typo_likelihood": round(float(base), 4), **cls}


# ── SET/SEQUENCE SIMILARITY + SIMHASH + LSH ──────────────────────────────────────────────────────────────────
def _ngrams(text: str, n: int = 2) -> set[str]:
    t = re.sub(r"\s+", " ", (text or "").casefold()).strip()
    return {t[i:i + n] for i in range(max(len(t) - n + 1, 0))}


def dice_bigram_similarity(a: str, b: str) -> float:
    """Sorensen-Dice over character bigrams (night/nacht = 0.25 — the textbook case)."""
    ba, bb = _ngrams(a, 2), _ngrams(b, 2)
    return round(2 * len(ba & bb) / (len(ba) + len(bb)), 4) if ba and bb else 0.0


def ngram_jaccard_similarity(a: str, b: str, n: int = 3) -> float:
    ga, gb = _ngrams(a, n), _ngrams(b, n)
    return round(len(ga & gb) / len(ga | gb), 4) if ga | gb else 0.0


def simhash64(text: str, n: int = 3) -> int:
    """64-bit SimHash over char n-grams (deterministic blake2b lanes) — near-duplicate text fingerprint."""
    import hashlib  # noqa: PLC0415
    weights = [0] * 64
    for g in _ngrams(text, n):
        h = int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "big")
        for bit in range(64):
            weights[bit] += 1 if (h >> bit) & 1 else -1
    return sum(1 << bit for bit in range(64) if weights[bit] > 0)


def simhash_hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def lsh_near_duplicate_buckets(strings: list[str], *, n_bands: int = 16, rows: int = 2) -> dict[str, list[int]]:
    """REUSE the multi-index MinHash/band machinery at the string-list level: indices sharing any band
    bucket are near-duplicate CANDIDATES (verify with a direct similarity — LSH generates, never decides)."""
    buckets: dict[str, list[int]] = {}
    for i, s in enumerate(strings):
        sig = minhash(tokenize_alnum(s))
        for band_i, key in enumerate(lsh_band_keys(sig, n_bands, rows)):
            buckets.setdefault(f"{band_i}:{key}", []).append(i)
    return {k: v for k, v in sorted(buckets.items()) if len(v) > 1}


# ── HARDCODED CORPORATE FOLDS (match keys only; display untouched) ───────────────────────────────────────────
_ORDINALS = {"first": "1st", "second": "2nd", "third": "3rd", "fourth": "4th", "fifth": "5th",
             "sixth": "6th", "seventh": "7th", "eighth": "8th", "ninth": "9th", "tenth": "10th"}
_ROMAN = {"ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6", "vii": "7", "viii": "8", "ix": "9"}
_AND_VARIANTS = {"&": "and", "+": "and", "et": "and", "und": "and", "y": "and", "en": "and"}


def corporate_fold_for_match(text: str) -> str:
    """The folds data teams rewrite forever, applied to MATCH KEYS only: Saint/St., ordinal streets
    (First->1st), Mc Donald->mcdonald, O Brien/O'Brien->obrien, roman suffixes (II->2), and-variants."""
    t = " " + re.sub(r"\s+", " ", (text or "").casefold().strip()) + " "
    t = re.sub(r" st\.? ", " saint ", t)
    t = re.sub(r" mc ([a-z])", r" mc\1", t)          # Mc Donald -> mcdonald
    t = re.sub(r" o[' ]([a-z])", r" o\1", t)          # O'Brien / O Brien -> obrien
    for word, ordn in _ORDINALS.items():
        t = t.replace(f" {word} ", f" {ordn} ")
    for roman, digit in _ROMAN.items():
        t = re.sub(rf" {roman} ", f" {digit} ", t)
    for variant, canon in _AND_VARIANTS.items():
        t = t.replace(f" {re.escape(variant) if variant == '+' else variant} ", f" {canon} ")
    t = t.replace(" + ", " and ")
    return re.sub(r"[^a-z0-9 ]", "", t).strip()


def best_fuzzy_matches(query: str, candidates: list[str], *, k: int = 5) -> list[dict[str, Any]]:
    """COMPOSITE ranker: corporate-folded exact first, then a blended JW + Dice + keyboard-aware typo score
    — deterministic ties broken lexicographically."""
    fq = corporate_fold_for_match(query)
    scored = []
    for c in candidates:
        fc = corporate_fold_for_match(c)
        if fq and fq == fc:
            scored.append((1.0, c, "corporate_fold_exact"))
            continue
        jw = jaro_winkler_similarity(fq, fc)
        dice = dice_bigram_similarity(fq, fc)
        typo = typo_likelihood(fq, fc)["typo_likelihood"] if abs(len(fq) - len(fc)) <= 2 else 0.0
        scored.append((round(0.45 * jw + 0.35 * dice + 0.2 * typo, 4), c, "blended"))
    ranked = sorted(scored, key=lambda x: (-x[0], x[1]))[:k]
    # NOTE: result key is match_candidate — BOUNDARY carries "candidate": True and must not collide
    return [{"match_candidate": c, "score": s, "method": m, **BOUNDARY} for s, c, m in ranked]


_ATOMIC_FNS = (levenshtein_distance, damerau_levenshtein_distance, jaro_similarity,
               jaro_winkler_similarity, longest_common_substring_len, keyboard_key_distance,
               classify_typo, dice_bigram_similarity, ngram_jaccard_similarity, simhash64,
               simhash_hamming, lsh_near_duplicate_buckets, corporate_fold_for_match)
_COMPOSITE_FNS = (typo_likelihood, best_fuzzy_matches)
COMPOSITE_PLANS = {"typo_likelihood": ["classify_typo", "damerau_levenshtein_distance",
                                       "keyboard_key_distance", "jaro_winkler_similarity"],
                   "best_fuzzy_matches": ["corporate_fold_for_match", "jaro_winkler_similarity",
                                          "dice_bigram_similarity", "typo_likelihood"]}


def all_cards() -> list[dict[str, Any]]:
    cards = []
    for fn in _ATOMIC_FNS + _COMPOSITE_FNS:
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        composite = fn in _COMPOSITE_FNS
        cards.append({"primitive_id": canonical_id(CARD_PREFIX, title, fn.__name__),
                      "impl_name": fn.__name__, "record_type": "similarity_typo_primitive",
                      "kind": "primitive_group" if composite else "primitive", "title": title,
                      "executable_body": inspect.getsource(fn), "language": "python",
                      "input_edge": "StringPairValue", "output_edge": "SimilarityScore",
                      "blackbox": f"{'Composite' if composite else 'Atomic'} similarity/typo primitive: "
                                  f"{title} Input: string(s). Output: distance/similarity/typo verdict.",
                      "plan_steps": COMPOSITE_PLANS.get(fn.__name__, []), "tier": "common", **BOUNDARY})
    return cards


# ── self-test (literature oracles) ───────────────────────────────────────────────────────────────────────────
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    checks.append(("Levenshtein literature oracle: kitten/sitting=3, flaw/lawn=2, x/x=0",
                   levenshtein_distance("kitten", "sitting") == 3
                   and levenshtein_distance("flaw", "lawn") == 2 and levenshtein_distance("x", "x") == 0))
    checks.append(("Damerau: transposition costs 1 ('teh'->'the'), Levenshtein says 2 — the typo delta",
                   damerau_levenshtein_distance("teh", "the") == 1
                   and levenshtein_distance("teh", "the") == 2))
    checks.append(("Jaro-Winkler canonical: MARTHA/MARHTA = 0.961; prefix boost beats plain Jaro",
                   jaro_winkler_similarity("martha", "marhta") == 0.961
                   and jaro_winkler_similarity("martha", "marhta") > jaro_similarity("martha", "marhta")))
    checks.append(("longest common substring: 'standardize'/'standard' = 8",
                   longest_common_substring_len("standardize", "standard") == 8))
    checks.append(("KEYBOARD DISTANCE: h-j adjacent (<=1.2), p-j distant; g-t diagonal adjacent",
                   0 < keyboard_key_distance("h", "j") <= 1.2
                   and keyboard_key_distance("p", "j") > 2
                   and 0 < keyboard_key_distance("g", "t") <= 1.2))
    checks.append(("TYPO CLASSIFICATION: hane/jane = adjacent substitution; pane/jane = distant; "
                   "teh/the = transposition; bookk/book = doubled letter",
                   classify_typo("jane", "hane")["classification"] == "substitution_adjacent_key"
                   and classify_typo("jane", "pane")["classification"] == "substitution_distant_key"
                   and classify_typo("the", "teh")["classification"] == "transposition"
                   and classify_typo("book", "bookk")["classification"] == "doubled_letter"))
    hane, pane = typo_likelihood("jane", "hane"), typo_likelihood("jane", "pane")
    checks.append(("TYPO-KEYBOARD LIKELIHOOD: fat-finger 'hane' scores 2x the distant 'pane' — "
                   "same edit distance, different verdict",
                   hane["typo_likelihood"] == 0.9 and pane["typo_likelihood"] == 0.45))
    checks.append(("Dice bigrams textbook: night/nacht = 0.25; identical = 1.0",
                   dice_bigram_similarity("night", "nacht") == 0.25
                   and dice_bigram_similarity("acme", "acme") == 1.0))
    s1, s2, s3 = (simhash64("the quick brown fox jumps over the lazy dog"),
                  simhash64("the quick brown fox jumped over the lazy dog"),
                  simhash64("completely unrelated legal boilerplate paragraph"))
    checks.append(("SimHash: near-duplicate sentences within 12 Hamming bits; unrelated text far",
                   simhash_hamming(s1, s2) <= 12 and simhash_hamming(s1, s3) > 20))
    strings = ["Acme Logistics LLC", "ACME Logistics L.L.C.", "Globex Corporation",
               "Acme Logistics", "Initech Systems"]
    buckets = lsh_near_duplicate_buckets(strings)
    linked: set[int] = set()
    for members in buckets.values():
        if linked & set(members) or not linked:
            linked |= set(members)
    checks.append(("LSH (reusing the multi-index MinHash): the three Acme variants form one CONNECTED "
                   "candidate cluster (0-3-1, transitivity is the contract); Globex/Initech stay out",
                   {0, 1, 3} <= linked
                   and all(2 not in v and 4 not in v for v in buckets.values())))
    checks.append(("CORPORATE FOLDS: St/Saint, First/1st, Mc Donald, O'Brien variants, roman II, "
                   "and-variants all converge",
                   corporate_fold_for_match("St. Mary's Hospital")
                   == corporate_fold_for_match("Saint Marys Hospital")
                   and corporate_fold_for_match("First Street Bakery")
                   == corporate_fold_for_match("1st Street Bakery")
                   and corporate_fold_for_match("Mc Donald") == corporate_fold_for_match("McDonald")
                   and corporate_fold_for_match("O'Brien & Sons")
                   == corporate_fold_for_match("O Brien and Sons")
                   and corporate_fold_for_match("Acme II") == corporate_fold_for_match("Acme 2")))
    ranked = best_fuzzy_matches("Saint Marys Hospital",
                                ["St. Mary's Hospital", "General Hospital", "Saint Martin Hospital"])
    checks.append(("FUZZY RANKER: corporate-fold exact wins at 1.0; deterministic; result key dodges the "
                   "BOUNDARY 'candidate' collision",
                   ranked[0]["match_candidate"] == "St. Mary's Hospital" and ranked[0]["score"] == 1.0
                   and ranked == best_fuzzy_matches("Saint Marys Hospital",
                                                    ["St. Mary's Hospital", "General Hospital",
                                                     "Saint Martin Hospital"])))
    checks.append(("cards + boundary", all(c.get("serves_truth") is False for c in all_cards())))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - similarity_typo_primitives: literature-oracle edit distances, QWERTY keyboard-distance "
          "typo classification (fat-finger vs different-word), Dice/Jaccard/SimHash, LSH near-dup buckets "
          "(multi-index MinHash reused), corporate folds, blended fuzzy ranker. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cards", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.cards:
        for c in all_cards():
            print(json.dumps(c, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
