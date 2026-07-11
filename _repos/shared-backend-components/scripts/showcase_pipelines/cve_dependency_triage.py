#!/usr/bin/env python3
"""Showcase: CVE / dependency vulnerability triage (an engineering, non-CFPB example).

Structural gap (durability: freshness + exactness): CVE/KEV feeds change daily and triage is an
EXACT version-range match against YOUR lockfile — a bare model hallucinates CVE ids, misses
post-cutoff advisories, and can't map an advisory to your exact installed versions.

Composition (real `_repos/shared-backend-components/scripts/processors` callables + deterministic version arithmetic):
  1. exact_id_lookup          — the CVE id is a structured identifier → exact advisory hit
  2. _affected_versions       — deterministic semver range check vs the lockfile (the domain step)
  3. source_precedence_select — NVD / KEV (signed, current) governs over a third-party mirror
  4. deliver_report + escalate_human — a confirmed-affected + KEV finding blocks + routes to review

Run:  python3 _repos/shared-backend-components/scripts/showcase_pipelines/cve_dependency_triage.py [--self-test]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.processors.retrieval.exact_id_lookup import run as exact_run
from scripts.processors.retrieval.source_precedence_select import run as precedence_run
from scripts.processors.deliver.deliver_report import run as report_run
from scripts.processors.deliver.escalate_human import run as escalate_run

_VER_RE = re.compile(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?")


def _ver(s: str) -> tuple[int, int, int]:
    m = _VER_RE.search(str(s))
    return (int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0)) if m else (0, 0, 0)


def _affected(installed: str, *, introduced: str, fixed: str | None) -> bool:
    """Deterministic range check: introduced <= installed < fixed (fixed None = still open)."""
    v = _ver(installed)
    if v < _ver(introduced):
        return False
    return fixed is None or v < _ver(fixed)


def run(*, query: str, advisories: list[dict[str, Any]], lockfile: list[dict[str, Any]],
        advisory_sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Triage the CVE in ``query`` against the lockfile + the governing advisory source."""
    trace: list[dict[str, Any]] = []

    # 1. exact CVE-id lookup against the advisory corpus.
    match = exact_run(identifier=query, corpus=advisories)["match"]
    trace.append({"step": "exact_id_lookup", "cve": match["identifier"], "found": match["found"]})
    if not match["found"]:
        return {"affected": False, "answer": "no matching CVE in the governed advisory feed (abstain)",
                "trace": trace, "serves_truth": False}

    advisory = next(a for a in advisories if a["id"] == match["hits"][0]["id"])

    # 2. exact version-range check vs the lockfile (the domain step the model can't do).
    affected_pkgs = []
    for dep in lockfile:
        if dep["name"] == advisory["package"] and _affected(
                dep["version"], introduced=advisory["introduced"], fixed=advisory.get("fixed")):
            affected_pkgs.append({"name": dep["name"], "installed": dep["version"],
                                  "fixed_in": advisory.get("fixed")})
    trace.append({"step": "version_range_check", "affected": affected_pkgs,
                  "range": f">={advisory['introduced']}, <{advisory.get('fixed') or '∞'}"})

    # 3. which advisory source governs.
    prec = precedence_run(candidates=advisory_sources)
    governing = prec["selected"][0]["id"] if prec["selected"] else None
    trace.append({"step": "source_precedence_select", "governing": governing})

    affected = bool(affected_pkgs)
    kev = bool(advisory.get("kev"))  # CISA Known-Exploited-Vulnerabilities → urgent
    queue: list[dict] = []
    ticket = None
    if affected:
        ticket = escalate_run(result={"cve": advisory["id"], "affected": affected_pkgs, "kev": kev,
                                      "governing_source": governing},
                              reason="gate_fired" if kev else "policy_review",
                              enqueue=lambda t: (queue.append(t), {"ref": f"vuln-{len(queue):04d}"})[1])["ticket"]
    result = {"title": f"CVE triage — {advisory['id']}",
              "answer": ("AFFECTED" + (" (KEV — exploited in the wild)" if kev else "")) if affected
                        else "not affected (installed version outside the vulnerable range)",
              "details": {"package": advisory["package"], "affected": affected_pkgs, "kev": kev},
              "citations": [governing, advisory["id"]] if governing else [advisory["id"]]}
    report = report_run(result=result, format="markdown")["document_uri"]
    return {"affected": affected, "kev": kev, "affected_packages": affected_pkgs,
            "escalated": ticket is not None, "ticket": ticket["queue_ref"] if ticket else None,
            "report_markdown": report["rendered_markdown"], "trace": trace, "serves_truth": False}


# SYNTHETIC advisory + lockfile (public-shape data; proves the mechanism).
_ADVISORIES = [
    {"id": "CVE-2024-3094", "package": "liblzma", "introduced": "5.6.0", "fixed": "5.6.2",
     "kev": True, "text": "CVE-2024-3094: backdoor in xz-utils liblzma 5.6.0–5.6.1"},
    {"id": "CVE-2023-0001", "package": "leftpad", "introduced": "1.0.0", "fixed": "1.0.5",
     "kev": False, "text": "CVE-2023-0001: minor issue in leftpad"},
]
_LOCKFILE = [
    {"name": "liblzma", "version": "5.6.1"},   # in range → affected (and KEV)
    {"name": "leftpad", "version": "1.2.0"},   # past the fix → not affected
    {"name": "requests", "version": "2.31.0"},
]
_SOURCES = [
    {"id": "nvd@2026-06-12", "text": "NVD advisory feed (current)", "source_kind": "source_of_law",
     "signed": True, "valid_through": 2_000_000.0, "as_of": 1_000_000.0},
    {"id": "blog-mirror@old", "text": "a security blog's CVE summary", "source_kind": "secondary_report",
     "signed": False, "valid_through": 500_000.0, "as_of": 1_000_000.0},
]


def _self_test() -> int:
    # The in-range KEV CVE flags liblzma 5.6.1 as AFFECTED and escalates urgently.
    out = run(query="is CVE-2024-3094 affecting us?", advisories=_ADVISORIES, lockfile=_LOCKFILE,
              advisory_sources=_SOURCES)
    assert out["affected"] is True and out["kev"] is True, out
    assert out["affected_packages"][0]["name"] == "liblzma" and out["affected_packages"][0]["installed"] == "5.6.1"
    assert out["escalated"] is True and "AFFECTED" in out["report_markdown"] and "KEV" in out["report_markdown"]
    # A CVE whose fix we already have → NOT affected (exact range arithmetic, not vibes).
    safe = run(query="CVE-2023-0001 status", advisories=_ADVISORIES, lockfile=_LOCKFILE, advisory_sources=_SOURCES)
    assert safe["affected"] is False and safe["escalated"] is False
    # An unknown CVE → abstain (never hallucinate an advisory).
    unknown = run(query="CVE-1999-9999 impact", advisories=_ADVISORIES, lockfile=_LOCKFILE, advisory_sources=_SOURCES)
    assert unknown["affected"] is False and "abstain" in unknown["answer"]
    # NVD governs over the blog mirror.
    gov = next(t for t in out["trace"] if t["step"] == "source_precedence_select")["governing"]
    assert gov == "nvd@2026-06-12"
    # Range boundaries: the fixed version itself is NOT affected (introduced <= v < fixed).
    assert _affected("5.6.1", introduced="5.6.0", fixed="5.6.2") and not _affected("5.6.2", introduced="5.6.0", fixed="5.6.2")
    assert out["serves_truth"] is False
    assert json.dumps(run(query="CVE-2024-3094", advisories=_ADVISORIES, lockfile=_LOCKFILE, advisory_sources=_SOURCES),
                      sort_keys=True) == json.dumps(run(query="CVE-2024-3094", advisories=_ADVISORIES,
                      lockfile=_LOCKFILE, advisory_sources=_SOURCES), sort_keys=True)
    print("PASS — cve_dependency_triage: exact CVE-id lookup + deterministic version-range arithmetic "
          "(5.6.1 ∈ [5.6.0, 5.6.2) → AFFECTED+KEV; 5.6.2 not) — flags the real exposure the bare model "
          "guesses at, abstains on an unknown CVE, NVD governs; escalates; deterministic")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CVE/dependency triage showcase.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    print(run(query="CVE-2024-3094", advisories=_ADVISORIES, lockfile=_LOCKFILE, advisory_sources=_SOURCES)["report_markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
