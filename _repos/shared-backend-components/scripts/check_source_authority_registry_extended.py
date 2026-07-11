#!/usr/bin/env python3
"""Proof that the source-authority registry covers the YC beachhead publishers.

B3 extends the EARNED authority registry with FDA/BIS sources and state corporate
registry publishers used by the M&A / ownership demos. This check stays offline:
it verifies that classification is registry-derived, longest-match specific, and
still downgrades unsigned top-tier claims.
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.artifact_graph.source_authority import classify


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    fda_label = classify(source_uri="https://labels.fda.gov/synthetic-label", signed=True)
    fda_access = classify(source_uri="https://www.accessdata.fda.gov/drugsatfda_docs/label/synthetic.pdf", signed=True)
    bis_new = classify(source_uri="https://www.bis.gov/regulations/export-administration-regulations-ear", signed=True)
    bis_legacy = classify(source_uri="https://www.bis.doc.gov/index.php/policy-guidance/lists-of-parties-of-concern/entity-list", signed=True)
    de = classify(source_uri="https://icis.corp.delaware.gov/ecorp/entitysearch/name-search", signed=True)
    ca = classify(source_uri="https://bizfileonline.sos.ca.gov/search/business", signed=True)
    fl = classify(source_uri="https://search.sunbiz.org/Inquiry/CorporationSearch/ByName", signed=True)
    tx = classify(source_uri="https://direct.sos.state.tx.us/acct/acct-login.asp", signed=True)
    dmw_online = classify(source_uri="https://onlineservices.dmw.gov.ph/OnlineServices/POEAOnline.aspx", signed=True)
    dmw = classify(source_uri="https://dmw.gov.ph/", signed=True)
    dole = classify(source_uri="https://www.dole.gov.ph/advisories/example", signed=True)
    vendor = classify(source_uri="https://screenfast-db.example.com/entity-list", signed=False)
    unsigned_fda = classify(source_uri="https://labels.fda.gov/synthetic-label", signed=False)

    for label, result in (
        ("FDA labels.fda.gov", fda_label),
        ("FDA AccessData", fda_access),
        ("BIS bis.gov", bis_new),
        ("BIS bis.doc.gov legacy redirect", bis_legacy),
        ("Delaware Division of Corporations", de),
        ("California BizFile", ca),
        ("Florida Sunbiz", fl),
        ("Texas SOSDirect", tx),
        ("Philippines DMW online services", dmw_online),
        ("Philippines DMW", dmw),
        ("Philippines DOLE", dole),
    ):
        check(f"{label} earns official_agency authority",
              result["tier"] == "official_agency" and result["rank"] == 90, str(result))

    check("longest FDA match wins over bare fda.gov",
          fda_label["matched_by"] == "labels.fda.gov", str(fda_label))
    check("longest Delaware match wins over corp.delaware.gov",
          de["matched_by"] == "icis.corp.delaware.gov", str(de))
    check("longest DMW online-services match wins over bare dmw.gov.ph",
          dmw_online["matched_by"] == "onlineservices.dmw.gov.ph", str(dmw_online))
    check("unlisted screening vendor earns no authority",
          vendor["tier"] == "unverified" and vendor["rank"] == 10, str(vendor))
    check("unsigned claim to a registered FDA source is downgraded",
          unsigned_fda["tier"] == "official_guidance" and unsigned_fda["downgraded"] is True, str(unsigned_fda))

    print("\n" + ("PASS - check_source_authority_registry_extended: FDA, BIS, and state corporate "
                  "registry publishers plus Philippine DMW/DOLE classify as earned official_agency sources; unlisted vendors "
                  "stay unverified; unsigned top-tier claims downgrade." if not failures
                  else f"{len(failures)} FAILURES: {failures}"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
