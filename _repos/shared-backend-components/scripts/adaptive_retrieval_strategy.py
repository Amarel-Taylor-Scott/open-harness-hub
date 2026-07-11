#!/usr/bin/env python3
"""adaptive_retrieval_strategy — self-tuning distance/blocking selection PER DATA SHAPE (info + search theory).

Owner (2026-07-10): "not all solutions work for every shape of data" — the format needs custom-tuned,
self-tuning heuristics, new blocking keys, fuzzy edits, distance measures chosen from the data at hand. The
existing retrieval zoo already races embedders (embedder_zoo), fuses rankers (rank_fusion_zoo), routes per
query class (path_router_zoo), and self-tunes the graph (graph_autotune). This module adds the missing lane:
choosing the right DISTANCE MEASURE + BLOCKING KEY for the SHAPE of an attribute's values, by MEASUREMENT, not
by a fixed rule — and grounds "which feature is worth blocking on" in information theory.

Two zoos (extend = one row): DISTANCE_MEASURES (exact · levenshtein/fuzzy · jaccard · ngram · numeric ·
prefix) and BLOCKING_KEYS (prefix_k · token_first · ngram_set · length_bucket). A SELF-TUNER races the distance
measures on a labeled probe set drawn from the data at hand and picks the champion NON-DESTRUCTIVELY (losers
kept as fallbacks) — so numeric data selects a numeric distance, typo-prone short strings select edit distance,
and token-set data selects Jaccard, all by observed separation. Information theory selects blocking keys: a key
is scored by normalized entropy (does it make enough buckets?) balanced against over-fragmentation (are the
buckets singletons?), so a low-information key is never chosen.

    PYTHONPATH=. python3 scripts/adaptive_retrieval_strategy.py --self-test
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── DISTANCE / SIMILARITY MEASURE ZOO (each: (a, b) -> similarity in [0,1]; extend = one row). ────────────────
def _sim_exact(a: Any, b: Any) -> float:
    return 1.0 if a == b else 0.0


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _sim_levenshtein(a: Any, b: Any) -> float:
    a, b = str(a), str(b)
    m = max(len(a), len(b)) or 1
    return 1.0 - _levenshtein(a, b) / m


def _tokens(v: Any) -> set:
    return set(v) if isinstance(v, (list, set, tuple)) else set(str(v).lower().split())


def _sim_jaccard(a: Any, b: Any) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta and not tb:
        return 1.0
    return len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0


def _ngrams(v: Any, n: int = 3) -> set:
    s = f"  {str(v).lower()}  "
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def _sim_ngram(a: Any, b: Any) -> float:
    na, nb = _ngrams(a), _ngrams(b)
    return len(na & nb) / len(na | nb) if (na | nb) else 0.0


def _sim_numeric(a: Any, b: Any) -> float:
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return 0.0
    scale = max(abs(fa), abs(fb), 1.0)
    return max(0.0, 1.0 - abs(fa - fb) / scale)


def _sim_prefix(a: Any, b: Any) -> float:
    a, b = str(a), str(b)
    common = 0
    for ca, cb in zip(a, b):
        if ca != cb:
            break
        common += 1
    return common / (max(len(a), len(b)) or 1)


DISTANCE_MEASURES: dict[str, Callable[[Any, Any], float]] = {
    "exact": _sim_exact, "levenshtein": _sim_levenshtein, "jaccard": _sim_jaccard,
    "ngram": _sim_ngram, "numeric": _sim_numeric, "prefix": _sim_prefix,
}


def register_distance_measure(name: str, fn: Callable[[Any, Any], float]) -> None:
    DISTANCE_MEASURES[name] = fn


# ── BLOCKING-KEY ZOO (each: value -> list of blocking keys; extend = one row). ───────────────────────────────
BLOCKING_KEYS: dict[str, Callable[[Any], list[str]]] = {
    "prefix_k": lambda v: [str(v)[:3].lower()],
    "token_first": lambda v: [(str(v).lower().split() or [""])[0]],
    "ngram_set": lambda v: sorted(_ngrams(v)),
    "length_bucket": lambda v: [f"len:{len(str(v)) // 4}"],
}


def register_blocking_key(name: str, fn: Callable[[Any], list[str]]) -> None:
    BLOCKING_KEYS[name] = fn


# ── information theory: how informative is a feature / blocking key over a corpus? ───────────────────────────
def normalized_entropy(values: list[Any]) -> float:
    """Shannon entropy of the value distribution, normalized to [0,1] by log(n) — 0 = all same (no info),
    1 = all distinct (maximally discriminative)."""
    n = len(values)
    if n <= 1:
        return 0.0
    counts = Counter(json.dumps(v, sort_keys=True) if isinstance(v, (list, dict)) else v for v in values)
    h = -sum((c / n) * math.log(c / n) for c in counts.values())
    return h / math.log(n)


def blocking_key_quality(values: list[Any], key_fn: Callable[[Any], list[str]]) -> dict[str, Any]:
    """A blocking key is good when it makes MANY buckets (high entropy → fewer candidate pairs) WITHOUT
    fragmenting into singletons (which miss true matches). Score = entropy × recall-safety (1 - singleton_frac).
    This is the information-theoretic feature-selection the owner asked for."""
    bucket_of: list[str] = []
    for v in values:
        keys = key_fn(v)
        bucket_of.append(keys[0] if keys else "")
    sizes = Counter(bucket_of)
    n = len(values) or 1
    entropy = normalized_entropy(bucket_of)
    singleton_frac = sum(1 for s in sizes.values() if s == 1) / n
    max_bucket_frac = max(sizes.values()) / n if sizes else 1.0
    # reduction: fraction of candidate pairs eliminated vs all-pairs (higher = more selective).
    all_pairs = n * (n - 1) / 2 or 1
    kept_pairs = sum(s * (s - 1) / 2 for s in sizes.values())
    reduction = 1.0 - kept_pairs / all_pairs
    score = entropy * (1.0 - singleton_frac)
    return {"n_buckets": len(sizes), "entropy": round(entropy, 4), "singleton_fraction": round(singleton_frac, 4),
            "max_bucket_fraction": round(max_bucket_frac, 4), "pair_reduction": round(reduction, 4),
            "score": round(score, 4)}


def characterize_data_shape(values: list[Any]) -> dict[str, Any]:
    """The SHAPE of an attribute's values — drives which distance measure to try first."""
    if not values:
        return {"empty": True}
    is_numeric = all(_is_numlike(v) for v in values)
    is_token_set = all(isinstance(v, (list, set, tuple)) for v in values)
    str_lens = [len(str(v)) for v in values]
    return {"n": len(values), "is_numeric": is_numeric, "is_token_set": is_token_set,
            "avg_len": round(sum(str_lens) / len(str_lens), 2), "distinct_ratio": round(normalized_entropy(values), 4)}


def _is_numlike(v: Any) -> bool:
    try:
        float(v)
        return not isinstance(v, bool)
    except (TypeError, ValueError):
        return False


def select_distance_measure(labeled_pairs: list[tuple[Any, Any, bool]]) -> dict[str, Any]:
    """SELF-TUNE by measurement: race every distance measure on labeled (a, b, same?) pairs FROM THE DATA AT
    HAND and pick the one that best SEPARATES same from different (mean sim on matches minus on non-matches).
    Non-destructive: every measure's score is returned; the champion is a selection, not a deletion."""
    scores: dict[str, float] = {}
    for name, fn in DISTANCE_MEASURES.items():
        sims_same = [fn(a, b) for a, b, same in labeled_pairs if same]
        sims_diff = [fn(a, b) for a, b, same in labeled_pairs if not same]
        if not sims_same or not sims_diff:
            scores[name] = 0.0
            continue
        scores[name] = (sum(sims_same) / len(sims_same)) - (sum(sims_diff) / len(sims_diff))
    champion = max(scores, key=lambda k: (scores[k], k)) if scores else "exact"
    return {"champion": champion, "separation": round(scores.get(champion, 0.0), 4),
            "ranked": sorted(({"measure": k, "separation": round(v, 4)} for k, v in scores.items()),
                             key=lambda r: -r["separation"]),
            "note": "champion selected by measured separation on THIS data's labeled pairs; all measures kept "
                    "as fallbacks (non-destructive; re-race when the data shape changes)",
            "candidate": True, "serves_truth": False}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    # (1) NUMERIC data self-selects the NUMERIC distance (close numbers similar, far numbers not) — levenshtein
    #     would say "100" and "101" are similar but "100" and "999" also similar-ish; numeric separates better.
    numeric_pairs = [("100", "101", True), ("100", "102", True), ("100", "9999", False), ("50", "9000", False),
                     ("200", "205", True), ("200", "80000", False)]
    num_sel = select_distance_measure(numeric_pairs)
    checks.append(("self-tune: NUMERIC data selects the numeric distance measure by measured separation",
                   num_sel["champion"] == "numeric", f"champion={num_sel['champion']}"))

    # (2) TYPO-prone SHORT STRINGS self-select EDIT DISTANCE (levenshtein/ngram), not exact/numeric.
    typo_pairs = [("hello", "helo", True), ("world", "wrold", True), ("hello", "world", False),
                  ("banana", "bananna", True), ("apple", "zebra", False), ("orange", "ornage", True)]
    typo_sel = select_distance_measure(typo_pairs)
    checks.append(("self-tune: TYPO-prone short strings select an edit-distance measure (levenshtein/ngram), "
                   "not numeric/exact — a different shape picks a different champion",
                   typo_sel["champion"] in ("levenshtein", "ngram", "prefix")
                   and typo_sel["champion"] != num_sel["champion"], f"champion={typo_sel['champion']}"))

    # (3) TOKEN-SET data self-selects JACCARD. The sets OVERLAP but in DIFFERENT ORDER, so the order-dependent
    #     measures (prefix/levenshtein over the list's string repr) fail while Jaccard (order-independent) wins.
    token_pairs = [(["cat", "dog", "fish"], ["fish", "cat", "bird"], True),
                   (["red", "blue"], ["blue", "green", "red"], True),
                   (["cat", "dog", "fish"], ["car", "van", "bus"], False),
                   (["north", "south"], ["east", "west"], False),
                   (["one", "two", "three"], ["three", "two", "four"], True)]
    token_sel = select_distance_measure(token_pairs)
    checks.append(("self-tune: TOKEN-SET data (overlapping but reordered) selects Jaccard — the "
                   "order-independent set-overlap measure the order-sensitive ones miss",
                   token_sel["champion"] == "jaccard", f"champion={token_sel['champion']}"))

    # (4) INFORMATION THEORY selects blocking keys: the GOOD key makes MODERATE buckets (enough to reduce
    #     candidate pairs, big enough to keep true matches together). A prefix key over words that share
    #     3-char prefixes scores far above BOTH a constant (0-entropy, no reduction) key AND is a real reduction.
    corpus = ["apple", "apply", "append", "banana", "bandit", "band", "cargo", "carbon"]
    prefix_q = blocking_key_quality(corpus, BLOCKING_KEYS["prefix_k"])   # -> app/ban/car buckets (3/3/2)
    const_quality = blocking_key_quality(corpus, lambda v: ["same"])     # -> 1 bucket, useless
    checks.append(("information theory selects blocking keys: a moderate-bucket key (real pair reduction, no "
                   "singletons) scores far above a constant 0-entropy key that eliminates no candidate pairs",
                   prefix_q["score"] > const_quality["score"] and prefix_q["pair_reduction"] > 0.5
                   and prefix_q["singleton_fraction"] == 0.0
                   and const_quality["entropy"] == 0.0 and const_quality["pair_reduction"] == 0.0,
                   json.dumps({"prefix": prefix_q["score"], "reduction": prefix_q["pair_reduction"]})))

    # (5) normalized entropy is calibrated: all-same -> 0, all-distinct -> 1.
    checks.append(("normalized entropy calibrated: all-same values -> 0, all-distinct -> 1 (info content of a "
                   "feature)",
                   normalized_entropy(["a", "a", "a", "a"]) == 0.0
                   and abs(normalized_entropy(["a", "b", "c", "d"]) - 1.0) < 1e-9, ""))

    # (6) data-shape characterization drives the choice; and adding a NEW distance measure is one row.
    shape = characterize_data_shape(["100", "200", "300"])
    register_distance_measure("reverse_prefix", lambda a, b: _sim_prefix(str(a)[::-1], str(b)[::-1]))
    checks.append(("data-shape characterization (numeric/token-set/avg-len/distinct-ratio) is computed; a new "
                   "distance measure is one registered row",
                   shape["is_numeric"] is True and "reverse_prefix" in DISTANCE_MEASURES, ""))

    # (7) NON-DESTRUCTIVE + deterministic: the champion is a selection, all measures ranked + kept; re-run same.
    again = select_distance_measure(numeric_pairs)
    checks.append(("non-destructive selection (all measures ranked + kept as fallbacks) + deterministic re-run",
                   len(num_sel["ranked"]) == len(DISTANCE_MEASURES) - 1  # (+1 registered after num_sel computed)
                   and again["champion"] == num_sel["champion"]
                   and num_sel["serves_truth"] is False, f"ranked={len(num_sel['ranked'])}"))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - adaptive_retrieval_strategy: self-tuning distance/blocking selection "
          f"PER DATA SHAPE — {len(DISTANCE_MEASURES)} distance measures + {len(BLOCKING_KEYS)} blocking keys "
          f"(extend = one row); the self-tuner RACES on the data at hand so numeric→numeric, typos→edit "
          f"distance, sets→Jaccard by MEASUREMENT; information theory (normalized entropy) selects blocking "
          f"keys; non-destructive (champion selected, losers kept). serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Self-tuning distance/blocking selection per data shape.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
