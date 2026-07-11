#!/usr/bin/env python3
"""scripts.matching_scorecard_primitives — the DETERMINISTIC-CORE / TUNABLE-SHELL matching system (owner
spec 2026-07-08): 'do not make the system less deterministic as it becomes smarter — make the learning
produce versioned, testable, reviewable configs.'

  * TERM-FREQUENCY EVIDENCE — matching on 'Kaczmarek' is stronger than matching on 'Smith': corpus token
    weights (idf-style) + frequency-weighted similarity = deterministic frequency-weighted identity
    resolution.
  * FELLEGI-SUNTER WEIGHTS — m/u probabilities counted from labeled pairs (P(agree|match) vs
    P(agree|non-match)) -> log2 evidence weights per field: the probabilistic-linkage core, computed
    deterministically from a label snapshot.
  * SCORECARD EVALUATION — the versioned config shape (hard rules with PRECEDENCE -> weighted features ->
    threshold bands) -> decision + full explanation + rules-fired. Hard rules dominate; conflicts recorded.
  * THRESHOLD SWEEP — cost-based tuning (false merge 1000 >> false non-match 25 >> review 1): sweep
    (auto_match, review_lower) deterministically against a labeled score set, return the cost-minimizing
    policy WITH the full ledger.
  * CALIBRATION — reliability bins + Brier score, so a 0.9 means ~90%.
  * BLOCKING METRICS — reduction ratio + blocking recall from labeled true pairs (the blocking-tuner
    inputs).

Everything is a pure function over snapshots — same inputs, same config out; deployment stays an approved,
versioned artifact. candidate=true, serves_truth=false.

    python3 scripts/matching_scorecard_primitives.py --self-test
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
import math  # noqa: E402
from typing import Any  # noqa: E402

from scripts.string_standardization_primitives import tokenize_alnum  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"matching_scorecard_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-score"
DEFAULT_COSTS = {"false_merge": 1000.0, "false_non_match": 25.0, "manual_review": 1.0}


# ── TERM-FREQUENCY EVIDENCE (frequency-weighted identity resolution) ─────────────────────────────────────────
def term_frequency_weights(corpus_values: list[str]) -> dict[str, float]:
    """Token -> idf-style evidence weight over a value corpus: rare tokens (Kaczmarek) weigh more than
    common ones (Smith). Deterministic from the corpus snapshot."""
    from collections import Counter  # noqa: PLC0415
    df: Counter = Counter()
    for v in corpus_values:
        df.update(set(tokenize_alnum(v)))
    n = max(len(corpus_values), 1)
    return {t: round(math.log((n + 1) / (c + 1)) + 1.0, 6) for t, c in sorted(df.items())}


def frequency_weighted_similarity(a: str, b: str, weights: dict[str, float]) -> dict[str, Any]:
    """Weighted token overlap: shared RARE tokens carry the match; shared common tokens barely move it.
    Two 'John Smith's score below two 'Zyva Kaczmarek's despite identical token overlap."""
    ta, tb = set(tokenize_alnum(a)), set(tokenize_alnum(b))
    if not ta or not tb:
        return {"similarity": 0.0, "shared_evidence": 0.0, **BOUNDARY}
    default_w = min(weights.values()) if weights else 1.0
    shared = sum(weights.get(t, default_w) for t in ta & tb)
    union = sum(weights.get(t, default_w) for t in ta | tb)
    return {"similarity": round(shared / union, 4) if union else 0.0,
            "shared_evidence": round(shared, 4),
            "shared_tokens": sorted(ta & tb), **BOUNDARY}


# ── FELLEGI-SUNTER m/u WEIGHTS ───────────────────────────────────────────────────────────────────────────────
def fellegi_sunter_weights(labeled_pairs: list[dict[str, Any]], fields: list[str]) -> dict[str, dict[str, float]]:
    """Count m = P(field agrees | match) and u = P(field agrees | non-match) from a label snapshot ->
    log2(m/u) agreement weight and log2((1-m)/(1-u)) disagreement weight per field. Laplace-smoothed;
    deterministic from the snapshot."""
    out = {}
    matches = [p for p in labeled_pairs if p.get("label") == "match"]
    nons = [p for p in labeled_pairs if p.get("label") == "non_match"]
    for f in fields:
        m_agree = sum(1 for p in matches if p["agreements"].get(f)) + 1
        u_agree = sum(1 for p in nons if p["agreements"].get(f)) + 1
        m = m_agree / (len(matches) + 2)
        u = u_agree / (len(nons) + 2)
        out[f] = {"m": round(m, 4), "u": round(u, 4),
                  "agreement_weight": round(math.log2(m / u), 4),
                  "disagreement_weight": round(math.log2((1 - m) / (1 - u)), 4)}
    return out


# ── SCORECARD EVALUATION (hard rules dominate; versioned config shape) ───────────────────────────────────────
def evaluate_scorecard(features: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """The spec's config shape executed: hard rules by PRIORITY first (force_match / force_non_match /
    force_review), then the weighted sum, then threshold bands — with full explanation and conflict record."""
    fired, conflict_positive, conflict_negative = [], [], []
    for rule in sorted(config.get("hard_rules", []), key=lambda r: -int(r.get("priority", 0))):
        if features.get(rule["feature"]):
            fired.append(rule["id"])
            (conflict_negative if rule["effect"] == "force_non_match" else conflict_positive).append(rule["id"])
    if fired:
        top = next(r for r in sorted(config.get("hard_rules", []), key=lambda r: -int(r.get("priority", 0)))
                   if r["id"] == fired[0])
        return {"decision": {"force_match": "auto_match", "force_non_match": "auto_non_match",
                             "force_review": "review"}[top["effect"]],
                "score": None, "hard_rules_fired": fired,
                "rule_conflict": bool(conflict_positive and conflict_negative),
                "explanation": [f"hard rule {top['id']} ({top['effect']}) took precedence"],
                "config_id": config.get("config_id", ""), **BOUNDARY}
    score, explanation = 0.0, []
    for name, weight in sorted(config.get("weights", {}).items()):
        v = features.get(name)
        contribution = weight * (1.0 if v is True else float(v) if isinstance(v, (int, float)) else 0.0)
        if contribution:
            explanation.append(f"{name}: {round(contribution, 4)}")
        score += contribution
    th = config.get("thresholds", {})
    decision = ("auto_match" if score >= th.get("auto_match", 0.95)
                else "review" if score >= th.get("manual_review_lower", 0.7) else "auto_non_match")
    return {"decision": decision, "score": round(score, 4), "hard_rules_fired": [],
            "rule_conflict": False, "explanation": explanation,
            "requires_review": decision == "review", "config_id": config.get("config_id", ""), **BOUNDARY}


# ── THRESHOLD SWEEP (cost-based, deterministic, lossless ledger) ─────────────────────────────────────────────
def threshold_sweep(scored_labeled: list[dict[str, Any]], *, costs: dict[str, float] | None = None,
                    grid_step: float = 0.05) -> dict[str, Any]:
    """Sweep (auto_match, review_lower) over a labeled score snapshot; expected cost = 1000*false_merges +
    25*false_non_matches + 1*reviews (defaults). Champion + full ledger; false merges priced catastrophic."""
    c = {**DEFAULT_COSTS, **(costs or {})}
    grid = [round(x * grid_step, 2) for x in range(int(1 / grid_step) + 1)]
    ledger = []
    for auto in grid:
        for review in grid:
            if review > auto:
                continue
            fm = sum(1 for p in scored_labeled if p["score"] >= auto and p["label"] == "non_match")
            fnm = sum(1 for p in scored_labeled if p["score"] < review and p["label"] == "match")
            reviews = sum(1 for p in scored_labeled if review <= p["score"] < auto)
            cost = c["false_merge"] * fm + c["false_non_match"] * fnm + c["manual_review"] * reviews
            ledger.append({"auto_match": auto, "review_lower": review, "false_merges": fm,
                           "false_non_matches": fnm, "reviews": reviews, "expected_cost": round(cost, 2)})
    champion = min(ledger, key=lambda r: (r["expected_cost"], -r["auto_match"], r["review_lower"]))
    return {"champion": champion, "evaluated": len(ledger), "costs": c,
            "ledger_head": sorted(ledger, key=lambda r: r["expected_cost"])[:5], **BOUNDARY}


# ── CALIBRATION + BLOCKING METRICS ───────────────────────────────────────────────────────────────────────────
def reliability_bins(scored_labeled: list[dict[str, Any]], *, n_bins: int = 10) -> list[dict[str, Any]]:
    """Predicted-probability bins vs observed match rate — a calibrated 0.9 bin should observe ~0.9."""
    bins: list[list[dict]] = [[] for _ in range(n_bins)]
    for p in scored_labeled:
        bins[min(int(p["score"] * n_bins), n_bins - 1)].append(p)
    out = []
    for i, members in enumerate(bins):
        if members:
            observed = sum(1 for p in members if p["label"] == "match") / len(members)
            out.append({"bin": f"{i / n_bins:.1f}-{(i + 1) / n_bins:.1f}", "count": len(members),
                        "mean_score": round(sum(p["score"] for p in members) / len(members), 4),
                        "observed_match_rate": round(observed, 4)})
    return out


def brier_score(scored_labeled: list[dict[str, Any]]) -> float:
    """Mean squared error of score vs outcome (0 = perfect; 0.25 = coin-flip on balanced data)."""
    if not scored_labeled:
        return 0.0
    return round(sum((p["score"] - (1.0 if p["label"] == "match" else 0.0)) ** 2
                     for p in scored_labeled) / len(scored_labeled), 6)


def blocking_metrics(candidate_pairs: set[tuple], true_pairs: set[tuple], total_records: int) -> dict[str, Any]:
    """The blocking-tuner inputs: recall (true pairs surviving blocking) + reduction ratio vs all-pairs."""
    total_possible = total_records * (total_records - 1) // 2
    found = len(candidate_pairs & true_pairs)
    return {"blocking_recall": round(found / len(true_pairs), 4) if true_pairs else 1.0,
            "candidate_pair_count": len(candidate_pairs),
            "reduction_ratio": round(1 - len(candidate_pairs) / total_possible, 6) if total_possible else 0.0,
            "true_matches_missed": sorted(true_pairs - candidate_pairs), **BOUNDARY}


_ATOMIC_FNS = (term_frequency_weights, frequency_weighted_similarity, fellegi_sunter_weights,
               threshold_sweep, reliability_bins, brier_score, blocking_metrics)
_COMPOSITE_FNS = (evaluate_scorecard,)
COMPOSITE_PLANS = {"evaluate_scorecard": ["fellegi_sunter_weights", "frequency_weighted_similarity",
                                          "threshold_sweep"]}


def all_cards() -> list[dict[str, Any]]:
    cards = []
    for fn in _ATOMIC_FNS + _COMPOSITE_FNS:
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        composite = fn in _COMPOSITE_FNS
        cards.append({"primitive_id": canonical_id(CARD_PREFIX, title, fn.__name__),
                      "impl_name": fn.__name__, "record_type": "matching_scorecard_primitive",
                      "kind": "primitive_group" if composite else "primitive", "title": title,
                      "executable_body": inspect.getsource(fn), "language": "python",
                      "input_edge": "ComparisonVector", "output_edge": "MatchDecision",
                      "blackbox": f"{'Composite' if composite else 'Atomic'} tunable-matching primitive: "
                                  f"{title} Input: features/labels/scores snapshots. Output: weights/"
                                  f"decisions/policies (versioned configs, never silent).",
                      "plan_steps": COMPOSITE_PLANS.get(fn.__name__, []), "tier": "common", **BOUNDARY})
    return cards


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    corpus = ["John Smith", "Mary Smith", "James Smith", "Ana Smith", "Zyva Kaczmarek", "Li Wei"]
    w = term_frequency_weights(corpus)
    checks.append(("TF EVIDENCE: rare 'kaczmarek' outweighs common 'smith'",
                   w["kaczmarek"] > w["smith"] and w["smith"] < w["zyva"]))
    smiths = frequency_weighted_similarity("John Smith", "Johnny Smith", w)
    rares = frequency_weighted_similarity("Zyva Kaczmarek", "Zyva K Kaczmarek", w)
    checks.append(("FREQUENCY-WEIGHTED IDENTITY: shared rare tokens score higher than shared common ones",
                   rares["similarity"] > smiths["similarity"]
                   and smiths["shared_tokens"] == ["smith"]))
    labeled = ([{"label": "match", "agreements": {"email": True, "name": True}}] * 9
               + [{"label": "match", "agreements": {"email": False, "name": True}}]
               + [{"label": "non_match", "agreements": {"email": False, "name": True}}] * 6
               + [{"label": "non_match", "agreements": {"email": False, "name": False}}] * 14)
    fs = fellegi_sunter_weights(labeled, ["email", "name"])
    checks.append(("FELLEGI-SUNTER: email (agrees in matches, never in non-matches) carries far more "
                   "agreement weight than name",
                   fs["email"]["agreement_weight"] > 3 and fs["email"]["m"] > 0.8
                   and fs["email"]["agreement_weight"] > fs["name"]["agreement_weight"]))
    config = {"config_id": "org_match_test_v1",
              "hard_rules": [{"id": "verified_tax_id_conflict", "feature": "tax_id_conflict",
                              "effect": "force_non_match", "priority": 1000},
                             {"id": "same_verified_lei", "feature": "lei_exact",
                              "effect": "force_match", "priority": 900}],
              "weights": {"name_similarity": 0.4, "domain_exact": 0.35, "country_match": 0.25},
              "thresholds": {"auto_match": 0.9, "manual_review_lower": 0.6}}
    soft = evaluate_scorecard({"name_similarity": 0.95, "domain_exact": True, "country_match": True}, config)
    hard = evaluate_scorecard({"name_similarity": 0.99, "domain_exact": True, "tax_id_conflict": True},
                              config)
    conflict = evaluate_scorecard({"lei_exact": True, "tax_id_conflict": True}, config)
    checks.append(("SCORECARD: weighted path auto-matches with explanation; hard non-match DOMINATES 0.99 "
                   "similarity; simultaneous force rules recorded as CONFLICT with priority winning",
                   soft["decision"] == "auto_match" and soft["explanation"]
                   and hard["decision"] == "auto_non_match"
                   and conflict["rule_conflict"] and conflict["decision"] == "auto_non_match"))
    scored = ([{"score": 0.98, "label": "match"}] * 20 + [{"score": 0.85, "label": "match"}] * 5
              + [{"score": 0.85, "label": "non_match"}] * 2 + [{"score": 0.3, "label": "non_match"}] * 30
              + [{"score": 0.92, "label": "non_match"}])
    sweep = threshold_sweep(scored)
    ch = sweep["champion"]
    checks.append(("THRESHOLD SWEEP: champion pays reviews to avoid 1000-cost false merges (the 0.92 "
                   "non-match lands in review or below, never auto-matched)",
                   ch["false_merges"] == 0 and ch["auto_match"] > 0.92 and ch["expected_cost"] < 100
                   and sweep["evaluated"] > 100))
    bins = reliability_bins(scored)
    checks.append(("CALIBRATION: reliability bins expose the 0.8-0.9 mixed bin; Brier ranks a good scorer "
                   "over a coin flip",
                   any(0 < b["observed_match_rate"] < 1 for b in bins)
                   and brier_score(scored) < brier_score([{"score": 0.5, "label": p["label"]}
                                                          for p in scored])))
    bm = blocking_metrics({(1, 2), (3, 4), (5, 6)}, {(1, 2), (3, 4), (7, 8)}, total_records=100)
    checks.append(("BLOCKING METRICS: recall 2/3 with the missed true pair NAMED; reduction ratio computed",
                   bm["blocking_recall"] == 0.6667 and bm["true_matches_missed"] == [(7, 8)]
                   and bm["reduction_ratio"] > 0.999))
    checks.append(("determinism + boundary + cards",
                   json.dumps(threshold_sweep(scored), sort_keys=True)
                   == json.dumps(sweep, sort_keys=True)
                   and all(c.get("serves_truth") is False for c in all_cards())))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - matching_scorecard_primitives: TF evidence weights, Fellegi-Sunter m/u, hard-rule-"
          "dominant scorecards with explanations, cost-based threshold sweeps, calibration, blocking "
          "metrics — deterministic snapshots in, versioned configs out. serves_truth=false.")
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
