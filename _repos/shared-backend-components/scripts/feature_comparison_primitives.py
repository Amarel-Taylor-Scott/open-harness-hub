#!/usr/bin/env python3
"""scripts.feature_comparison_primitives — the FEATURE + COMPARISON layer (owner-directed 2026-07-08): the
leap from "clean this column" to a structured feature and comparison layer across ALL columns.

  * SINGLE-COLUMN shape features — lengths, counts (digits/letters/vowels/punctuation/whitespace/upper),
    ratios, entropy (reused from the dummy pack), case-style detection: the bad-string/ML feature basis.
  * CROSS-COLUMN construction + CONSISTENCY — full-name/domain/total constructions; the contradiction
    table: date order, total = price x quantity, boolean/text status conflicts, email-domain vs company,
    age vs birthdate — each a named finding with severity, routed to review.
  * COMPARISON VECTORS — compare two records field-by-field (exact / casefolded / token-set / numeric
    difference / date distance) into the explicit comparison-vector shape.
  * HYBRID SCORE — weighted feature sum + rule bonuses/penalties where HARD RULES DOMINATE (different
    verified tax id -> non_match regardless of name similarity; trust-vs-person -> do_not_merge). Weights
    are SETTINGS (tunable via the control plane's test-feedback loop).
  * GROUP/WINDOW features — group count/mean/median/stddev/MAD/z-score (context-conditioned), rolling
    z-score for streams.
  * OUTLIERS — deterministic robust methods: IQR rule, modified z-score (median/MAD), group-contextual
    z-score, rare-category frequency — each returning the outlier-result shape (score, threshold, reason).

Pure deterministic functions; findings rate and route, never delete. candidate=true, serves_truth=false.

    python3 scripts/feature_comparison_primitives.py --self-test
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
import statistics  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts.dummy_data_detection_primitives import shannon_entropy  # noqa: E402 — reuse, not copy
from scripts.string_standardization_primitives import tokenize_alnum, token_sorted_key  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"feature_comparison_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-featcmp"
_VOWELS = frozenset("aeiou")
#: hybrid-score weights: SETTINGS (control-plane tunable), not constants scattered in logic
HYBRID_WEIGHTS: dict[str, float] = {"name_token_set": 0.35, "exact_identifier": 0.35, "numeric_close": 0.10,
                                    "date_close": 0.10, "country_match": 0.10}
#: hard rules DOMINATE the weighted sum (the spec's rule-override law)
HARD_RULES: tuple[tuple[str, str], ...] = (
    ("different_verified_tax_id", "non_match"),
    ("entity_type_conflict", "do_not_merge"),
    ("same_verified_tax_id", "match"),
)
IQR_MULTIPLIER = 1.5          # Tukey fence (units: IQRs)
MODIFIED_ZSCORE_FLOOR = 3.5   # Iglewicz-Hoaglin recommended threshold


# ── SINGLE-COLUMN shape features ─────────────────────────────────────────────────────────────────────────────
def string_shape_features(value: str) -> dict[str, Any]:
    """The full shape-feature vector for one string: counts, ratios, entropy, case style, run lengths."""
    v = value or ""
    n = len(v)
    letters = sum(c.isalpha() for c in v)
    digits = sum(c.isdigit() for c in v)
    upper = sum(c.isupper() for c in v)
    ws = sum(c.isspace() for c in v)
    punct = sum(not c.isalnum() and not c.isspace() for c in v)
    vowels = sum(c.casefold() in _VOWELS for c in v)
    tokens = v.split()
    max_run = max((len(m.group(0)) for m in re.finditer(r"(.)\1*", v)), default=0)
    case_style = ("snake_case" if re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)+", v) else
                  "kebab_case" if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)+", v) else
                  "camel_case" if re.fullmatch(r"[a-z]+(?:[A-Z][a-z0-9]*)+", v) else
                  "all_upper" if v.isupper() and letters else
                  "all_lower" if v.islower() and letters else
                  "title_case" if v.istitle() else "mixed")
    return {"length": n, "token_count": len(tokens), "letter_count": letters, "digit_count": digits,
            "vowel_count": vowels, "consonant_count": letters - vowels, "uppercase_count": upper,
            "whitespace_count": ws, "punctuation_count": punct,
            "unique_char_count": len(set(v)), "max_repeated_run": max_run,
            "digit_ratio": round(digits / n, 4) if n else 0.0,
            "letter_ratio": round(letters / n, 4) if n else 0.0,
            "uppercase_ratio": round(upper / letters, 4) if letters else 0.0,
            "punctuation_ratio": round(punct / n, 4) if n else 0.0,
            "entropy": shannon_entropy(v), "case_style": case_style,
            "first_letter": next((c.casefold() for c in v if c.isalpha()), ""),
            "last_letter": next((c.casefold() for c in reversed(v) if c.isalpha()), ""),
            "first_token": tokens[0] if tokens else "", "last_token": tokens[-1] if tokens else "",
            **BOUNDARY}


# ── CROSS-COLUMN construction + CONTRADICTIONS ───────────────────────────────────────────────────────────────
def construct_cross_features(record: dict[str, Any]) -> dict[str, Any]:
    """Deterministic cross-column constructions from whichever inputs exist (missing inputs -> absent
    features, never fabricated)."""
    out: dict[str, Any] = {}
    r = record or {}
    if r.get("first_name") and r.get("last_name"):
        out["full_name"] = f"{r['first_name']} {r['last_name']}".strip()
        out["initial_last_key"] = f"{str(r['first_name'])[:1].casefold()} {str(r['last_name']).casefold()}"
    if r.get("email") and "@" in str(r["email"]):
        out["email_domain"] = str(r["email"]).rpartition("@")[2].casefold()
        if r.get("company_name"):
            company_tokens = set(tokenize_alnum(str(r["company_name"])))
            domain_core = out["email_domain"].split(".")[0]
            out["email_domain_matches_company"] = domain_core in company_tokens
    if r.get("price") is not None and r.get("quantity") is not None:
        out["computed_total"] = float(r["price"]) * float(r["quantity"])
        if r.get("total") is not None:
            out["total_delta"] = round(float(r["total"]) - out["computed_total"], 6)
    if r.get("start_date") and r.get("end_date"):
        out["date_order_ok"] = str(r["end_date"]) >= str(r["start_date"])
    return {**out, **BOUNDARY}


def detect_contradictions(record: dict[str, Any]) -> list[dict[str, Any]]:
    """The contradiction table: named cross-field findings with severity; quarantine-or-review, never
    silent correction."""
    findings = []
    x = construct_cross_features(record)
    if x.get("date_order_ok") is False:
        findings.append({"contradiction": "date_order", "fields": ["start_date", "end_date"],
                         "severity": "high", "message": "end date precedes start date"})
    if "total_delta" in x and abs(x["total_delta"]) > 0.01:
        findings.append({"contradiction": "total_amount", "fields": ["price", "quantity", "total"],
                         "severity": "high",
                         "message": f"total differs from price x quantity by {x['total_delta']}"})
    if x.get("email_domain_matches_company") is False:
        findings.append({"contradiction": "email_company_domain", "fields": ["email", "company_name"],
                         "severity": "medium", "message": "email domain does not resemble company name"})
    status = str(record.get("status") or "").casefold()
    if record.get("is_active") is False and status == "active":
        findings.append({"contradiction": "boolean_text_status", "fields": ["is_active", "status"],
                         "severity": "high", "message": "is_active=false but status says active"})
    if record.get("age") is not None and record.get("birth_year") and record.get("as_of_year"):
        implied = int(record["as_of_year"]) - int(record["birth_year"])
        if abs(implied - int(record["age"])) > 1:
            findings.append({"contradiction": "age_birthdate", "fields": ["age", "birth_year"],
                             "severity": "medium",
                             "message": f"age {record['age']} vs implied {implied}"})
    return [{**f, "action": "quarantine_or_review", **BOUNDARY} for f in findings]


# ── COMPARISON VECTORS + HYBRID SCORE ────────────────────────────────────────────────────────────────────────
def compare_field(left: Any, right: Any, method: str) -> Any:
    """One field comparison: exact / casefolded / token_set (Jaccard) / numeric_diff / date_days."""
    if left is None or right is None:
        return None
    if method == "exact":
        return left == right
    if method == "casefolded":
        return str(left).strip().casefold() == str(right).strip().casefold()
    if method == "token_set":
        a, b = set(tokenize_alnum(str(left))), set(tokenize_alnum(str(right)))
        return round(len(a & b) / len(a | b), 4) if a | b else 0.0
    if method == "token_sorted_exact":
        return token_sorted_key(tokenize_alnum(str(left))) == token_sorted_key(tokenize_alnum(str(right)))
    if method == "numeric_diff":
        return round(abs(float(left) - float(right)), 6)
    if method == "date_days":  # ISO date strings: coarse day distance without a clock
        from datetime import date  # noqa: PLC0415
        try:
            da, db = date.fromisoformat(str(left)[:10]), date.fromisoformat(str(right)[:10])
            return abs((da - db).days)
        except ValueError:
            return None
    raise ValueError(f"unknown comparison method {method!r}")


def build_comparison_vector(left: dict[str, Any], right: dict[str, Any],
                            spec: dict[str, str]) -> dict[str, Any]:
    """COMPOSITE: {field: method} spec -> the explicit comparison-vector shape (nulls stay null: absent
    evidence is not disagreement)."""
    features = {f"{field}_{method}": compare_field(left.get(field), right.get(field), method)
                for field, method in sorted(spec.items())}
    return {"features": features, "spec": spec,
            "null_features": sorted(k for k, v in features.items() if v is None), **BOUNDARY}


def hybrid_match_score(features: dict[str, Any], *, weights: Optional[dict[str, float]] = None,
                       rule_flags: Optional[dict[str, bool]] = None) -> dict[str, Any]:
    """Weighted feature sum where HARD RULES DOMINATE: a verified-identifier conflict forces non_match no
    matter how similar the names; entity-type conflicts force do_not_merge. Weights are settings."""
    w = weights or HYBRID_WEIGHTS
    flags = rule_flags or {}
    for flag, verdict in HARD_RULES:
        if flags.get(flag):
            return {"decision": verdict, "dominated_by_rule": flag, "score": None,
                    "requires_review": verdict == "do_not_merge", **BOUNDARY}
    score = 0.0
    components = {}
    for name, weight in sorted(w.items()):
        v = features.get(name)
        contribution = weight * (1.0 if v is True else float(v) if isinstance(v, (int, float)) else 0.0)
        components[name] = round(contribution, 4)
        score += contribution
    decision = ("match" if score >= 0.9 else "possible_match" if score >= 0.6 else "non_match")
    return {"score": round(score, 4), "components": components, "decision": decision,
            "requires_review": decision == "possible_match", "weights_version": "hybrid-weights-v1",
            **BOUNDARY}


# ── GROUP / WINDOW / OUTLIERS ────────────────────────────────────────────────────────────────────────────────
def group_stats(rows: list[dict[str, Any]], group_key: str, field: str) -> dict[Any, dict[str, Any]]:
    """Per-group count/mean/median/stddev/MAD — the context that makes z-scores meaningful."""
    groups: dict[Any, list[float]] = {}
    for r in rows:
        if r.get(field) is not None:
            groups.setdefault(r.get(group_key), []).append(float(r[field]))
    out = {}
    for g, vals in sorted(groups.items(), key=str):
        med = statistics.median(vals)
        out[g] = {"count": len(vals), "mean": round(statistics.fmean(vals), 6), "median": med,
                  "stddev": round(statistics.stdev(vals), 6) if len(vals) > 1 else 0.0,
                  "mad": round(statistics.median(abs(v - med) for v in vals), 6)}
    return out


def modified_zscore_outliers(values: list[float], *, threshold: float = MODIFIED_ZSCORE_FLOOR) -> list[dict[str, Any]]:
    """Iglewicz-Hoaglin robust outliers: 0.6745*(x-median)/MAD, flag |score| >= threshold."""
    if len(values) < 3:
        return []
    med = statistics.median(values)
    mad = statistics.median(abs(v - med) for v in values)
    if mad == 0:
        return [{"value": v, "score": None, "is_outlier": v != med, "method": "mad_zero_exact_diff",
                 **BOUNDARY} for v in values if v != med]
    out = []
    for v in values:
        score = 0.6745 * (v - med) / mad
        if abs(score) >= threshold:
            out.append({"value": v, "score": round(score, 4), "threshold": threshold,
                        "is_outlier": True, "method": "modified_zscore",
                        "reason": f"value is {round(abs(score), 1)} robust deviations from the median",
                        **BOUNDARY})
    return out


def iqr_outliers(values: list[float], *, multiplier: float = IQR_MULTIPLIER) -> list[dict[str, Any]]:
    """Tukey fences: below Q1 - k*IQR or above Q3 + k*IQR."""
    if len(values) < 4:
        return []
    q = statistics.quantiles(sorted(values), n=4)
    q1, q3 = q[0], q[2]
    lo, hi = q1 - multiplier * (q3 - q1), q3 + multiplier * (q3 - q1)
    return [{"value": v, "bounds": [round(lo, 6), round(hi, 6)], "is_outlier": True, "method": "iqr",
             **BOUNDARY} for v in values if v < lo or v > hi]


def group_contextual_outliers(rows: list[dict[str, Any]], group_key: str, field: str,
                              *, threshold: float = MODIFIED_ZSCORE_FLOOR) -> list[dict[str, Any]]:
    """Outliers WITHIN context: a $50K charge is normal for enterprise, wild for starter — the group-
    conditioned robust z-score catches what a global score misses."""
    stats = group_stats(rows, group_key, field)
    out = []
    for r in rows:
        g, v = r.get(group_key), r.get(field)
        if v is None or g not in stats or stats[g]["mad"] == 0 or stats[g]["count"] < 3:
            continue
        score = 0.6745 * (float(v) - stats[g]["median"]) / stats[g]["mad"]
        if abs(score) >= threshold:
            out.append({"record": r, "group": g, "value": float(v), "score": round(score, 4),
                        "group_median": stats[g]["median"], "method": "group_modified_zscore",
                        "is_outlier": True, **BOUNDARY})
    return out


def rare_category_outliers(values: list[str], *, max_share: float = 0.01,
                           min_total: int = 50) -> list[dict[str, Any]]:
    """Frequency outliers: categories rarer than max_share of a sufficiently large sample."""
    from collections import Counter  # noqa: PLC0415
    if len(values) < min_total:
        return []
    counts = Counter(values)
    return [{"category": c, "count": n, "share": round(n / len(values), 5), "method": "rare_category",
             "is_outlier": True, **BOUNDARY}
            for c, n in sorted(counts.items()) if n / len(values) <= max_share]


def record_quality_report(record: dict[str, Any]) -> dict[str, Any]:
    """COMPOSITE: the compact quality vector — nulls + contradictions + a score; review flag when warranted."""
    nulls = sorted(k for k, v in (record or {}).items() if v is None or v == "")
    contradictions = detect_contradictions(record or {})
    score = max(0.0, round(1.0 - 0.1 * len(nulls) - 0.25 * len(contradictions), 4))
    return {"record": record, "null_count": len(nulls), "null_fields": nulls,
            "contradiction_count": len(contradictions),
            "top_issues": [c["contradiction"] for c in contradictions],
            "quality_score": score, "requires_review": bool(contradictions) or score < 0.5, **BOUNDARY}


_ATOMIC_FNS = (string_shape_features, construct_cross_features, detect_contradictions, compare_field,
               group_stats, modified_zscore_outliers, iqr_outliers, group_contextual_outliers,
               rare_category_outliers)
_COMPOSITE_FNS = (build_comparison_vector, hybrid_match_score, record_quality_report)
COMPOSITE_PLANS = {"build_comparison_vector": ["compare_field"],
                   "hybrid_match_score": ["build_comparison_vector"],
                   "record_quality_report": ["construct_cross_features", "detect_contradictions"]}


def all_cards() -> list[dict[str, Any]]:
    cards = []
    for fn in _ATOMIC_FNS + _COMPOSITE_FNS:
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        composite = fn in _COMPOSITE_FNS
        cards.append({"primitive_id": canonical_id(CARD_PREFIX, title, fn.__name__),
                      "impl_name": fn.__name__, "record_type": "feature_comparison_primitive",
                      "kind": "primitive_group" if composite else "primitive", "title": title,
                      "executable_body": inspect.getsource(fn), "language": "python",
                      "input_edge": "TypedRecordPair" if "compar" in fn.__name__ else "TypedRecord",
                      "output_edge": "FeatureVector",
                      "blackbox": f"{'Composite' if composite else 'Atomic'} feature/comparison primitive: "
                                  f"{title} Input: record(s)/values. Output: features / comparison vector /"
                                  f" findings.",
                      "plan_steps": COMPOSITE_PLANS.get(fn.__name__, []), "tier": "common", **BOUNDARY})
    return cards


# ── self-test ─────────────────────────────────────────────────────────────────────────────────────────────────
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    sf = string_shape_features("ACME!!! 123")
    checks.append(("shape features: the spec's worked example (length 11, letters 4, digits 3, punct 3, "
                   "upper ratio 1.0)", sf["length"] == 11 and sf["letter_count"] == 4
                   and sf["digit_count"] == 3 and sf["punctuation_count"] == 3
                   and sf["uppercase_ratio"] == 1.0 and sf["case_style"] == "all_upper"))
    checks.append(("case styles + first/last extraction",
                   string_shape_features("customer_name")["case_style"] == "snake_case"
                   and string_shape_features("customerName")["case_style"] == "camel_case"
                   and string_shape_features("Jane Doe")["first_token"] == "Jane"
                   and string_shape_features("Jane Doe")["last_letter"] == "e"))
    x = construct_cross_features({"first_name": "Jane", "last_name": "Doe", "email": "jane@acme.com",
                                  "company_name": "Acme Logistics LLC", "price": 10, "quantity": 3,
                                  "total": 30})
    checks.append(("cross-column: full name, email-domain-matches-company, total consistency",
                   x["full_name"] == "Jane Doe" and x["email_domain_matches_company"] is True
                   and x["total_delta"] == 0.0))
    bad = {"start_date": "2026-05-01", "end_date": "2026-04-01", "price": 10, "quantity": 3, "total": 35,
           "email": "jane@globex.com", "company_name": "Acme LLC", "is_active": False, "status": "active",
           "age": 30, "birth_year": 1981, "as_of_year": 2026}
    contradictions = detect_contradictions(bad)
    checks.append(("CONTRADICTIONS: date order + total mismatch + email/company + boolean/text status + "
                   "age/birthdate all caught, each named with severity",
                   {c["contradiction"] for c in contradictions}
                   == {"date_order", "total_amount", "email_company_domain", "boolean_text_status",
                       "age_birthdate"}
                   and all(c["action"] == "quarantine_or_review" for c in contradictions)))
    cv = build_comparison_vector({"name": "Acme Logistics LLC", "country": "US", "founded": "2001-05-01"},
                                 {"name": "ACME Logistic, L.L.C.", "country": "US", "founded": "2001-05-03"},
                                 {"name": "token_set", "country": "exact", "founded": "date_days"})
    checks.append(("COMPARISON VECTOR: token-set 0.1667 honest (Logistic!=Logistics unstemmed; L.L.C. "
                   "splits to single-char tokens), country exact, date distance 2 days",
                   cv["features"]["name_token_set"] == 0.1667
                   and cv["features"]["country_exact"] is True and cv["features"]["founded_date_days"] == 2))
    hs = hybrid_match_score({"name_token_set": 0.95, "exact_identifier": True, "country_match": True})
    checks.append(("HYBRID SCORE: weighted components + decision bands",
                   hs["score"] > 0.7 and hs["decision"] in ("match", "possible_match")
                   and "name_token_set" in hs["components"]))
    dominated = hybrid_match_score({"name_token_set": 0.99, "exact_identifier": True},
                                   rule_flags={"different_verified_tax_id": True})
    checks.append(("HARD RULES DOMINATE: different verified tax id -> non_match despite 0.99 name "
                   "similarity", dominated["decision"] == "non_match"
                   and dominated["dominated_by_rule"] == "different_verified_tax_id"))
    rows = ([{"segment": "starter", "amount": a} for a in (400, 450, 500, 520, 480, 50000)]
            + [{"segment": "enterprise", "amount": a} for a in (48000, 52000, 50000, 51000)])
    gs = group_stats(rows, "segment", "amount")
    checks.append(("group stats: median/MAD per context",
                   gs["starter"]["median"] == 490 and gs["enterprise"]["count"] == 4))
    ctx = group_contextual_outliers(rows, "segment", "amount")
    checks.append(("GROUP-CONTEXTUAL OUTLIER: $50K flagged in starter, NOT in enterprise (context is the "
                   "point)", len(ctx) == 1 and ctx[0]["group"] == "starter" and ctx[0]["value"] == 50000))
    mz = modified_zscore_outliers([400.0, 450.0, 500.0, 520.0, 480.0, 50000.0])
    checks.append(("modified z-score (median/MAD) flags exactly the extreme value",
                   len(mz) == 1 and mz[0]["value"] == 50000.0 and mz[0]["score"] > 100))
    iq = iqr_outliers([1.0, 2.0, 2.5, 3.0, 3.5, 4.0, 100.0])
    checks.append(("IQR Tukey fences flag 100 among single digits",
                   len(iq) == 1 and iq[0]["value"] == 100.0))
    rare = rare_category_outliers(["us"] * 60 + ["ca"] * 39 + ["xz"])
    checks.append(("rare-category outlier: 1-in-100 'xz' flagged, majors untouched",
                   len(rare) == 1 and rare[0]["category"] == "xz"))
    q = record_quality_report(bad)
    checks.append(("QUALITY REPORT: compact vector with contradiction count + score + review flag",
                   q["contradiction_count"] == 5 and q["requires_review"] and q["quality_score"] < 0.5))
    checks.append(("determinism + boundary + cards",
                   json.dumps(detect_contradictions(bad), sort_keys=True)
                   == json.dumps(contradictions, sort_keys=True)
                   and all(c.get("serves_truth") is False for c in all_cards())))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - feature_comparison_primitives: shape features -> cross-column constructions -> "
          "contradictions -> comparison vectors -> hybrid scores (hard rules dominate) -> group/window "
          "stats -> robust outliers (IQR/MAD/group-contextual/rare-category). serves_truth=false.")
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
