#!/usr/bin/env python3
"""Authority-aware multi-source corroboration for fragile facts.

Text-level corroboration already exists in ``processors.assurance``. This module is
the source-authority layer: it counts agreement only from independent sources that
earn enough authority via ``scripts.artifact_graph.source_authority``. Copies from
one publisher collapse to one voice; unlisted vendors can be held out as context,
but they do not raise confidence.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.artifact_graph.source_authority import classify

DEFAULT_MIN_INDEPENDENT = 2
DEFAULT_MIN_RANK = 90


def _independence_key(source: dict[str, Any], authority: dict[str, Any]) -> str:
    """One publisher/authority family is one voice, even if it appears in many URLs/subdomains.

    Preference order: a caller-declared id, then the registry ``authority_id`` family resolved by
    ``classify`` (so OFAC's sanctionssearch.ofac.treas.gov + ofac.treasury.gov collapse to one voice even
    when the caller threads no id), then the matched rule / domain for un-familied catch-alls so they stay
    distinct rather than merging into a single "government" voice."""
    for key in ("independent_authority_id", "authority_id", "publisher_id"):
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return str(authority.get("authority_id") or authority.get("matched_by")
               or authority.get("domain") or authority.get("label") or "unknown").lower()


def corroborate(
    *,
    claim_key: str,
    claim_value: str,
    sources: list[dict[str, Any]],
    min_independent: int = DEFAULT_MIN_INDEPENDENT,
    min_rank: int = DEFAULT_MIN_RANK,
) -> dict[str, Any]:
    """Count independent authoritative agreement for ``claim_key = claim_value``.

    Each source may provide ``value`` or ``claim_value`` plus provenance fields
    ``publisher``/``source_uri``/``signed``. Only sources whose authority rank is at
    least ``min_rank`` contribute to support/contradiction counts; lower-rank sources
    are preserved as held-out receipt evidence.
    """
    best_per_key: dict[str, dict[str, Any]] = {}
    held_out: list[dict[str, Any]] = []
    basis: list[str] = []

    for i, src in enumerate(sources):
        auth = classify(publisher=str(src.get("publisher", "")),
                        source_uri=str(src.get("source_uri", "")),
                        signed=src.get("signed"))
        key = _independence_key(src, auth)
        value = str(src.get("value", src.get("claim_value", ""))).strip()
        rec = {"source_id": src.get("source_id") or f"source-{i}",
               "independent_authority_id": key,
               "value": value,
               "rank": auth["rank"],
               "tier": auth["tier"],
               "authority_basis": auth["basis"]}
        basis.append(auth["basis"])

        if auth["rank"] < min_rank:
            held_out.append({**rec, "reason_held_out": "below authoritative corroboration rank"})
            continue
        # ONE authority = ONE voice: collapse a family's records to a single survivor (highest rank, then
        # first-seen — callers pass an authority's current/winning record first; the watchtower pre-sorts
        # winner-first). The survivor lands in support XOR contradict below, NEVER both — so an authority's own
        # stale row can no longer manufacture a contradiction against its current position. Losers are preserved.
        incumbent = best_per_key.get(key)
        if incumbent is None:
            best_per_key[key] = rec
        elif rec["rank"] > incumbent["rank"]:
            held_out.append({**incumbent, "reason_held_out": "superseded by a higher-rank record from the same authority"})
            best_per_key[key] = rec
        else:
            held_out.append({**rec, "reason_held_out": "collapsed: another record from the same authority is the voice (one authority = one vote)"})

    support = {k: r for k, r in best_per_key.items() if r["value"] == str(claim_value)}
    contradict = {k: r for k, r in best_per_key.items() if r["value"] != str(claim_value)}
    supporting = sorted(support.values(), key=lambda r: r["independent_authority_id"])
    contradicting = sorted(contradict.values(), key=lambda r: r["independent_authority_id"])
    n_support = len(supporting)
    n_contra = len(contradicting)

    if n_contra:
        verdict = "authoritative_contradicted"
        confidence = 0.0
    elif n_support >= min_independent:
        verdict = "multi_source_authoritative"
        confidence = 0.95
    elif n_support == 1:
        verdict = "single_authoritative"
        confidence = 0.75
    else:
        verdict = "unverified"
        confidence = 0.1

    return {
        "claim_key": claim_key,
        "claim_value": claim_value,
        "verdict": verdict,
        "confidence": confidence,
        "agreeing_independent": n_support,
        "contradicting_independent": n_contra,
        "min_independent": min_independent,
        "min_authority_rank": min_rank,
        "supporting_sources": supporting,
        "contradicting_sources": contradicting,
        "held_out_sources": held_out,
        "authority_basis": basis,
        "serves_truth": False,
    }


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    sources = [
        {"source_id": "dmw-registry", "independent_authority_id": "dmw",
         "publisher": "Department of Migrant Workers", "source_uri": "https://onlineservices.dmw.gov.ph/OnlineServices/POEAOnline.aspx",
         "signed": True, "value": "suspended"},
        {"source_id": "dole-advisory", "independent_authority_id": "dole",
         "publisher": "Department of Labor and Employment", "source_uri": "https://www.dole.gov.ph/advisories/example",
         "signed": True, "value": "suspended"},
        {"source_id": "vendor-cache", "publisher": "RecruiterDB",
         "source_uri": "https://recruiterdb.example.com/agency", "signed": False, "value": "valid"},
    ]
    out = corroborate(claim_key="agency_status:Island Recruiters", claim_value="suspended", sources=sources)
    check("two independent official sources raise confidence",
          out["verdict"] == "multi_source_authoritative" and out["agreeing_independent"] == 2, str(out))
    check("unlisted vendor cache is preserved but held out",
          len(out["held_out_sources"]) == 1 and out["held_out_sources"][0]["value"] == "valid", str(out["held_out_sources"]))

    one = corroborate(claim_key="agency_status:Island Recruiters", claim_value="suspended",
                      sources=[{**sources[0], "source_uri": "https://vendor.example.com/mirror", "signed": False}, sources[1]])
    check("flipping one official source to an unlisted vendor drops to single-authoritative",
          one["verdict"] == "single_authoritative" and one["agreeing_independent"] == 1, str(one))

    contradicted = corroborate(claim_key="agency_status:Island Recruiters", claim_value="suspended",
                               sources=[sources[0], {**sources[1], "value": "valid"}])
    check("independent official contradiction blocks confidence",
          contradicted["verdict"] == "authoritative_contradicted"
          and contradicted["contradicting_independent"] == 1, str(contradicted))

    # one authority via TWO subdomains with NO explicit id threaded → still ONE voice (registry authority_id fallback)
    subdomains = corroborate(claim_key="agency_status:Island Recruiters", claim_value="suspended", sources=[
        {"source_id": "dmw-online", "publisher": "DMW", "source_uri": "https://onlineservices.dmw.gov.ph/x", "signed": True, "value": "suspended"},
        {"source_id": "dmw-main", "publisher": "DMW", "source_uri": "https://dmw.gov.ph/advisory", "signed": True, "value": "suspended"}])
    check("two subdomains of ONE authority (no explicit id) collapse to a single voice",
          subdomains["verdict"] == "single_authoritative" and subdomains["agreeing_independent"] == 1, str(subdomains))

    # an authority's OWN stale row must not self-contradict its current position (current/winner passed first)
    stale = corroborate(claim_key="agency_status:Island Recruiters", claim_value="suspended", sources=[
        {"source_id": "dmw-current", "publisher": "DMW", "source_uri": "https://dmw.gov.ph/new", "signed": True, "value": "suspended"},
        {"source_id": "dmw-stale", "publisher": "DMW", "source_uri": "https://dmw.gov.ph/old", "signed": True, "value": "valid"}])
    check("an authority's own stale row does NOT manufacture a self-contradiction",
          stale["verdict"] == "single_authoritative" and stale["contradicting_independent"] == 0, str(stale))
    check("receipt output is evidence, not served truth", out["serves_truth"] is False)

    print("\n" + ("PASS - authority_corroboration: independent authoritative sources raise confidence; "
                  "vendor mirrors are held out; flipping provenance drops confidence; official contradiction "
                  "blocks promotion." if not failures else f"{len(failures)} FAILURES: {failures}"))
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Authority-aware multi-source corroboration.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    print(json.dumps({"usage": "import corroborate(...) or run --self-test"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
