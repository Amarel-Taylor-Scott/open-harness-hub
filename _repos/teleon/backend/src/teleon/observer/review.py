"""observer.review — the POST-SESSION REVIEWER: the non-invasive Observer mode, now a thin front-end over the ROUTER.

Post-session review is the SAME engine as the live monitor at a different point on the timeline: it is literally
`router.route_session(mode="review_only")` — every typed intervention module run in BATCH over a finished transcript,
zero live interruptions, exhaustive report a human triages. This is the "lead with this" adoption wedge (easy yes,
near-zero false-positive cost). Building review on the router (instead of its own funnel) is the memo's point: you
build the pipeline once. serves_truth=false; governed candidate findings (discovery != trust).

  from teleon.observer import review_session
  report = review_session([{"role": "user", "content": "let me write a pdf parser from scratch"}, ...])

  python3 -m src.teleon.observer.review --self-test
"""
from __future__ import annotations

import argparse
import sys

from .router import route_session
from .settings import ROUTER_SETTINGS

REVIEW_VERSION = "0.2.0"  # 0.2: re-based on the router/taxonomy (was a standalone funnel in 0.1)


def _savings_summary(findings: list[dict]) -> dict:
    """Roll up transparent estimate fields from findings."""
    tokens = 0
    calls = 0
    by_basis: dict[str, int] = {}
    for finding in findings:
        savings = finding.get("savings") if isinstance(finding.get("savings"), dict) else {}
        tokens += int(savings.get("tokens_avoided_estimate") or 0)
        calls += int(savings.get("model_calls_avoided_estimate") or 0)
        basis = str(savings.get("basis") or "").strip()
        if basis:
            by_basis[basis] = by_basis.get(basis, 0) + 1
    return {
        "tokens_avoided_estimate": tokens,
        "model_calls_avoided_estimate": calls,
        "basis_counts": dict(sorted(by_basis.items())),
        "estimate_method": "observer finding estimates; not a billing receipt",
        "serves_truth": False,
    }


def review_session(messages: list[dict]) -> dict:
    """Run the full taxonomy over a finished session in review mode -> a confidence-ranked report. Reshapes the
    router result into the reviewer's report shape (report + summary), keeping serves_truth/governance."""
    r = route_session(messages, mode="review_only")
    savings = _savings_summary(r["report"])
    reinventions = r["summary"]["by_type"].get("reinvention", 0) + r["summary"]["by_type"].get("reinvention_cluster", 0)
    return {
        "version": REVIEW_VERSION,
        "report": r["report"],
        "summary": {
            "messages_reviewed": r["summary"]["messages"],
            "findings": r["summary"]["findings"],
            "reinventions": reinventions,
            "waste_signals": r["summary"]["findings"] - reinventions,
            "by_type": r["summary"]["by_type"],
            "tokens_avoided_estimate": savings["tokens_avoided_estimate"],
            "model_calls_avoided_estimate": savings["model_calls_avoided_estimate"],
        },
        "savings": savings,
        "serves_truth": False,
        "governed": r["governed"],
    }


# --- proof ------------------------------------------------------------------------------------------------------
def _self_test() -> int:
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(name)
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    big = "x " * (ROUTER_SETTINGS.oversized_tokens * ROUTER_SETTINGS.chars_per_token)
    blob = "company financial report 2026 " * 40
    session = [
        {"role": "user", "content": "let me write a pdf parser from scratch"},      # reinvention (pdf, grounded)
        {"role": "user", "content": "I'll implement my own address validation"},     # reinvention (address)
        {"role": "assistant", "content": "ok, genuinely novel research with no solved domain"},  # QUIET
        {"role": "user", "content": big},                                            # oversized
        {"role": "user", "content": blob},                                           # first send
        {"role": "user", "content": blob},                                           # duplicate
    ]
    rep = review_session(session)
    by_type = rep["summary"]["by_type"]

    ck("returns a governed report", rep["serves_truth"] is False and "report" in rep)
    ck("catches >=2 grounded reinventions", by_type.get("reinvention", 0) >= 2, f"got {by_type.get('reinvention', 0)}")
    ck("each reinvention carries grounded existing components", all(
        f["source_ref"].get("existing") for f in rep["report"] if f["type"] == "reinvention"))
    ck("flags the oversized-context turn", by_type.get("oversized_context", 0) >= 1)
    ck("flags the duplicate re-upload", by_type.get("duplicate_context", 0) >= 1)
    ck("stays QUIET on the genuinely-novel message (precision)", all(
        f["message_index"] != 2 for f in rep["report"]))
    ck("every finding is a governed candidate", all(
        f["serves_truth"] is False and f["candidate"] and "confidence" in f and "suggestion" in f
        for f in rep["report"]))
    ck("report ranked by confidence (desc)", all(
        rep["report"][i]["confidence"] >= rep["report"][i + 1]["confidence"] for i in range(len(rep["report"]) - 1)))
    ck("summary counts computed + consistent", rep["summary"]["findings"] == len(rep["report"]))
    ck("summary rolls up token-savings estimates", rep["summary"]["tokens_avoided_estimate"] > 0
       and rep["savings"]["serves_truth"] is False)
    ck("review interrupts nobody (router surfaced=[] in review_only)",
       route_session(session, mode="review_only")["summary"]["would_interrupt"] == 0)
    ck("deterministic (same input -> same report)", review_session(session)["report"] == rep["report"])

    ml_session = [
        {"role": "user", "content": "Build a baseline for a text-classification competition. The metric is macro F1."},
        {"role": "assistant", "content": "I am also copying a few hundred example rows into context to decide preprocessing."},
    ]
    ml_rep = review_session(ml_session)
    ml_refs = "\n".join(str(f.get("source_ref", {})) for f in ml_rep["report"])
    ck("catches ML competition primitive route",
       "text.normalize_for_classification" in ml_refs and "metric.compute_macro_f1" in ml_refs,
       ml_refs)
    ck("catches manual context dump waste",
       any(f["type"] == "wasted_context" and "dataset.sample_summary" in str(f.get("source_ref", {}))
           for f in ml_rep["report"]))

    if fails:
        print(f"\nFAIL - observer.review: {len(fails)} of {checks} assertions failed")
        return 1
    print(f"PASS - observer.review: post-session reviewer over the ROUTER (review == route_session(review_only)) — "
          f"{rep['summary']['reinventions']} reinventions + {rep['summary']['waste_signals']} waste signals on the "
          f"sample; {checks} assertions; serves_truth=false, human-triaged candidates.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return _self_test()
    rep = review_session([
        {"role": "user", "content": "let me write a pdf parser from scratch"},
        {"role": "user", "content": "I'll build my own oauth login from scratch"},
    ])
    print(f"observer.review v{rep['version']}: {rep['summary']['reinventions']} reinventions, "
          f"{rep['summary']['waste_signals']} waste signals over {rep['summary']['messages_reviewed']} messages")
    for f in rep["report"]:
        print(f"  [{f['confidence']:.2f}] {f['type']} @msg#{f['message_index']}: {f['evidence']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
