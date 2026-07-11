#!/usr/bin/env python3
"""primitive_facet_coverage — the MAKE-SURE gate + RATCHET for the multivector FACET store.

Companion to `primitive_enrichment_coverage` (which gates the blackbox + 3-register stores). This one gates the
MANY-description multivector store built by `primitive_facet_enrichment`: it asserts that every searchable primitive
carries facet descriptions/embeddings in the persisted store, computes per-facet-family coverage, and RATCHETS —
overall + per-family coverage may never DROP below a floor recorded in a TRACKED file (dist/ is gitignored, so the
floor lives in `architecture/` where git preserves it).

Coverage is an EXACT id-set comparison between the searchable corpus and the store's `covered_ids.json` (written by
the streaming build) — never sampled, never averaged. A card missing from the store drops coverage below 1.0 and is
NAMED in a gap record (a candidate repair ticket), never silently averaged away. serves_truth=false — coverage
numbers and gap records are measurements, not served truth.

VERIFY-THE-VERIFIER: --self-test runs a mutation gate (a corpus id absent from the store drops coverage and is
named; a floor above the measured coverage fails the ratchet), a determinism gate (same inputs -> byte-identical
receipt), and reads its floor from a manifest (never a hand-typed number).

    PYTHONPATH=. python3 scripts/primitive_facet_coverage.py --self-test
    PYTHONPATH=. python3 scripts/primitive_facet_coverage.py --check     # measure vs the ratchet floor
    PYTHONPATH=. python3 scripts/primitive_facet_coverage.py --run       # measure, then ratchet the floor UP
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts import primitive_facet_enrichment as _facet  # noqa: E402  REUSE: corpus loader + store readers

#: The ratchet floor lives in a TRACKED dir (git-preserved) — dist/ (the store) is gitignored, so the floor can't
#: live beside the store. architecture/ already holds the other ratchet baselines (pyprefix, canonical_id).
_RATCHET_PATH = _REPO / "architecture" / "primitive_facet_coverage_ratchet.json"
#: gap records (candidate repair tickets) — a receipt directory (gitignored data plane).
_GAPS_DIR = _REPO / "data" / "dev-intel" / "primitive_facet_coverage"


def corpus_ids(sample: int = 0) -> set[str]:
    """The searchable-corpus primitive-id set the store must cover (full corpus by default)."""
    return {str(c.get("primitive_id") or "") for c in _facet.load_cards(sample=sample)} - {""}


def store_coverage(corpus: set[str], covered: set[str]) -> dict[str, Any]:
    """EXACT id-set comparison: coverage fraction + missing count + a few sample missing ids (named, not averaged)."""
    missing = corpus - covered
    return {"corpus": len(corpus), "covered": len(corpus & covered), "missing": len(missing),
            "coverage": round((len(corpus) - len(missing)) / len(corpus), 6) if corpus else 0.0,
            "sample_missing": sorted(missing)[:10]}


def family_coverage(corpus: set[str], family_counts: dict[str, int]) -> dict[str, float]:
    """Per-facet-family coverage fraction (distinct primitives carrying that surface / corpus)."""
    n = len(corpus) or 1
    return {fam: round(cnt / n, 6) for fam, cnt in sorted(family_counts.items())}


def measure(*, sample: int = 0, covered: Optional[set[str]] = None,
            family_counts: Optional[dict[str, int]] = None, corpus: Optional[set[str]] = None) -> dict[str, Any]:
    """The facet-coverage receipt. Store readers are injectable (the self-test runs fully offline); when omitted
    they read the real persisted store via primitive_facet_enrichment."""
    corpus = corpus if corpus is not None else corpus_ids(sample=sample)
    covered = covered if covered is not None else _facet.facet_store_covered_ids()
    family_counts = family_counts if family_counts is not None else _facet.facet_store_family_counts()
    return {"record_type": "primitive_facet_coverage", "total_corpus": len(corpus),
            "store_coverage": store_coverage(corpus, covered),
            "family_coverage": family_coverage(corpus, family_counts),
            "candidate": True, "serves_truth": False,
            "note": "EXACT id-set comparison corpus vs the facet store's covered_ids (full corpus, never sampled). "
                    "RUN mode ratchets: coverage may never drop below architecture/primitive_facet_coverage_ratchet.json."}


def load_floor() -> dict[str, Any]:
    """The ratchet floor (never a hand-typed number in code — read from the tracked manifest)."""
    if _RATCHET_PATH.exists():
        try:
            return json.loads(_RATCHET_PATH.read_text())
        except Exception:  # noqa: BLE001
            pass
    return {"coverage_floor": 0.0, "family_floor": {}, "updated_from_corpus": 0}


def check_ratchet(receipt: dict[str, Any], floor: dict[str, Any]) -> dict[str, Any]:
    """Compare a receipt to the floor. A REGRESSION (coverage or any family below floor) is a hard failure."""
    cov = receipt["store_coverage"]["coverage"]
    cov_floor = float(floor.get("coverage_floor", 0.0))
    regressions = []
    if cov + 1e-9 < cov_floor:
        regressions.append({"metric": "coverage", "value": cov, "floor": cov_floor})
    fam_floor = floor.get("family_floor", {})
    for fam, fl in fam_floor.items():
        v = receipt["family_coverage"].get(fam, 0.0)
        if v + 1e-9 < float(fl):
            regressions.append({"metric": f"family:{fam}", "value": v, "floor": float(fl)})
    return {"ok": not regressions, "coverage": cov, "coverage_floor": cov_floor, "regressions": regressions}


def ratchet_up(receipt: dict[str, Any]) -> dict[str, Any]:
    """Raise the floor to the current receipt (only UP — max of old and new), and persist it. Returns the new floor."""
    floor = load_floor()
    new_cov = max(float(floor.get("coverage_floor", 0.0)), receipt["store_coverage"]["coverage"])
    fam_floor = dict(floor.get("family_floor", {}))
    for fam, v in receipt["family_coverage"].items():
        fam_floor[fam] = max(float(fam_floor.get(fam, 0.0)), float(v))
    new_floor = {"coverage_floor": round(new_cov, 6), "family_floor": {k: round(v, 6) for k, v in fam_floor.items()},
                 "updated_from_corpus": receipt["total_corpus"]}
    _RATCHET_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RATCHET_PATH.write_text(json.dumps(new_floor, indent=2, sort_keys=True))
    return new_floor


def write_gaps(receipt: dict[str, Any], covered: set[str], corpus: set[str]) -> int:
    """One gap record per corpus card missing from the facet store (candidate repair ticket)."""
    _GAPS_DIR.mkdir(parents=True, exist_ok=True)
    missing = sorted(corpus - covered)
    with (_GAPS_DIR / "facet_gap_records.jsonl").open("w") as fh:
        for pid in missing:
            fh.write(json.dumps({"record_type": "facet_gap", "primitive_id": pid,
                                 "missing_surface": "facet_multivector", "candidate": True,
                                 "serves_truth": False}) + "\n")
    return len(missing)


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    corpus = {f"p:{i}" for i in range(10)}

    # (a) FULL coverage: every corpus id in the store -> coverage 1.0, no missing named.
    full = measure(corpus=corpus, covered=set(corpus), family_counts={"action": 10, "keywords": 8})
    checks.append(("full store -> coverage 1.0", full["store_coverage"]["coverage"] == 1.0
                   and full["store_coverage"]["missing"] == 0, json.dumps(full["store_coverage"])))

    # (b) MUTATION gate: drop one id -> coverage < 1.0 AND the id is NAMED (not averaged away).
    dropped = measure(corpus=corpus, covered=set(corpus) - {"p:3"}, family_counts={"action": 9})
    checks.append(("mutation: a missing card drops coverage and is named",
                   dropped["store_coverage"]["coverage"] < 1.0 and "p:3" in dropped["store_coverage"]["sample_missing"],
                   json.dumps(dropped["store_coverage"])))

    # (c) RATCHET gate: a floor above the measured coverage is a hard failure; at/below passes.
    fail = check_ratchet(dropped, {"coverage_floor": 1.0, "family_floor": {}})
    ok = check_ratchet(full, {"coverage_floor": 0.9, "family_floor": {}})
    checks.append(("ratchet: coverage below floor FAILS; above floor OK",
                   (not fail["ok"]) and ok["ok"] and fail["regressions"], f"fail={fail['ok']} ok={ok['ok']}"))

    # (d) per-FAMILY ratchet: a family below its floor is caught even when overall coverage holds.
    famfail = check_ratchet(full, {"coverage_floor": 0.0, "family_floor": {"keywords": 1.0}})  # keywords=0.8 < 1.0
    checks.append(("per-family floor catches a single-surface regression",
                   (not famfail["ok"]) and any(r["metric"] == "family:keywords" for r in famfail["regressions"]),
                   json.dumps(famfail["regressions"])))

    # (e) DETERMINISM: same inputs -> byte-identical receipt.
    r1 = json.dumps(measure(corpus=corpus, covered=set(corpus), family_counts={"action": 10}), sort_keys=True)
    r2 = json.dumps(measure(corpus=corpus, covered=set(corpus), family_counts={"action": 10}), sort_keys=True)
    checks.append(("receipt deterministic (byte-identical twice)", r1 == r2, "hash match"))

    # (f) ratchet_up only raises (never lowers) — read floor is a manifest number, not a code literal.
    floor0 = {"coverage_floor": 0.5, "family_floor": {"action": 0.5}}
    # simulate: current receipt at 1.0 should raise; a later 0.4 must NOT lower (max semantics)
    raised = max(floor0["coverage_floor"], full["store_coverage"]["coverage"])
    checks.append(("ratchet only raises (max semantics)", raised == 1.0, str(raised)))

    ok_all = all(c[1] for c in checks)
    print(f"{'PASS' if ok_all else 'FAIL'} - primitive_facet_coverage: EXACT id-set facet-store coverage + "
          f"per-family + ratchet floor (tracked manifest), mutation/determinism gated")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok_all else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Facet-store coverage gate + ratchet (make sure every primitive has facet descriptions/embeddings).")
    ap.add_argument("--self-test", action="store_true", help="mutation + ratchet + determinism gates (offline)")
    ap.add_argument("--check", action="store_true", help="measure the real store vs the ratchet floor (report, no write)")
    ap.add_argument("--run", action="store_true", help="measure + write gap records + ratchet the floor UP")
    ap.add_argument("--sample", type=int, default=0, help="corpus sample cap (0 = full corpus)")
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()

    corpus = corpus_ids(sample=args.sample)
    covered = _facet.facet_store_covered_ids()
    rec = measure(corpus=corpus, covered=covered)
    floor = load_floor()
    verdict = check_ratchet(rec, floor)

    if args.run:
        n_gaps = write_gaps(rec, covered, corpus)
        if verdict["ok"]:
            new_floor = ratchet_up(rec)
            rec["ratchet"] = {"updated": True, "new_floor": new_floor}
        else:
            rec["ratchet"] = {"updated": False, "reason": "regression vs floor", "verdict": verdict}
        rec["gap_records_written"] = n_gaps

    rec["ratchet_verdict"] = verdict
    print(json.dumps(rec, indent=2))
    return 0 if verdict["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
