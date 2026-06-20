#!/usr/bin/env python3
"""check_ftm_interop — proof that Baltor maps governed entity records to the FollowTheMoney (FtM) schema at the
EDGE without surrendering the core: entity_type→FtM schema, fields→real FtM properties (list-valued, Aleph-loadable),
id = lei-<LEI> (the global join key) else dc-<sha1>, and topics promoted CONSERVATIVELY only from governed flags
(never inferred from free text). FtM is a projection; the governed record stays the core; nothing serves truth.

Imported as a candidate standard from the DueCare entity-intelligence reference (2026-06) — the same "adopt the
schema, lib optional, govern above" pattern as OKF.

CLI: PYTHONPATH=. python3 scripts/check_ftm_interop.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.baltor.native.ftm_adapter import SERVES_TRUTH, schema_for, to_entity_proxy, to_ftm


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # entity_type -> FtM schema
    ck("entity_type maps to the right FtM schema (company/person/public_body/vessel/unknown->LegalEntity)",
       schema_for("recruitment_agency") == "Company" and schema_for("representative") == "Person"
       and schema_for("regulator") == "PublicBody" and schema_for("ship") == "Vessel"
       and schema_for("something_unknown") == "LegalEntity")

    rec = {"entity_type": "recruitment_agency", "name": "Sunrise Overseas Manpower",
           "aliases": ["Sunrise Overseas", "Sunrise Manpower"], "country": "PH", "jurisdiction": "PH",
           "reg_no": "POEA-12345", "lei": "5493001KJTIIGC8Y1R12", "status": "licensed",
           "source": "PH DMW licensed agencies", "flags": ["debarred"]}
    px = to_entity_proxy(rec)

    ck("schema is Company; Aleph-loadable shape {id, schema, properties}", px["schema"] == "Company"
       and set(px) >= {"id", "schema", "properties"})
    ck("fields map to real FtM properties with LIST values (name/leiCode/registrationNumber/country/status)",
       px["properties"].get("name") == ["Sunrise Overseas Manpower"]
       and px["properties"].get("leiCode") == ["5493001KJTIIGC8Y1R12"]
       and px["properties"].get("registrationNumber") == ["POEA-12345"]
       and px["properties"].get("country") == ["PH"] and px["properties"].get("status") == ["licensed"])
    ck("aliases map to FtM `alias` (multi-valued)", px["properties"].get("alias") == ["Sunrise Overseas", "Sunrise Manpower"])
    ck("id uses the canonical LEI when present (lei-<LEI>, the global join key)", px["id"] == "lei-5493001KJTIIGC8Y1R12")

    # id falls back to dc-<sha1> without an LEI, deterministically
    no_lei = dict(rec); no_lei.pop("lei")
    p2, p2b = to_entity_proxy(no_lei), to_entity_proxy(dict(no_lei))
    ck("id falls back to dc-<sha1> without an LEI, deterministically", p2["id"].startswith("dc-") and p2["id"] == p2b["id"])

    # topics: ONLY from governed flags, conservative set; NOT inferred from free text
    ck("topics promoted from governed flags, conservatively (debarred -> debarment)",
       px["properties"].get("topics") == ["debarment"])
    text_only = {"entity_type": "company", "name": "Acme", "description": "rumored to be sanctioned and debarred"}
    ck("a topic is NEVER inferred from free text (no flags -> no topics)",
       "topics" not in to_entity_proxy(text_only)["properties"])
    sanc = to_entity_proxy({"entity_type": "company", "name": "X", "flags": ["sanctioned", "forced_labor"]})
    ck("governed sanction/forced-labour flags map to FtM topics (sanction, export.control)",
       sanc["properties"]["topics"] == ["sanction", "export.control"])

    # batch + never serves truth + deterministic
    batch = to_ftm([rec, text_only])
    ck("batch maps to a list of proxies (Aleph bulk-load shape)", isinstance(batch, list) and len(batch) == 2)
    ck("no proxy serves truth (a schema projection never serves truth)",
       SERVES_TRUTH is False and all(p["serves_truth"] is False for p in batch))
    ck("deterministic (same record -> identical proxy)", to_entity_proxy(rec) == px)

    print("\n" + ("PASS - check_ftm_interop: governed entity records map to FollowTheMoney EntityProxies "
                  "(entity_type->schema, fields->real list-valued FtM props, id=lei-<LEI> else dc-<sha1>, topics "
                  "promoted conservatively from governed flags only). FtM rides at the edge as a candidate standard; "
                  "the governed record stays the core. Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_ftm_interop.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
