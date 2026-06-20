#!/usr/bin/env python3
"""ingest_entity_intelligence_catalog — stage the DueCare entity-intelligence catalog (imported 2026-06) as a
GOVERNED CANDIDATE FEED for the Teleon/Baltor corpus. Discovery is NOT trust: nothing here is an active capability;
each row is a candidate that must pass the gap/lift screen + human/eval gates before any promotion. serves_truth is
false for everything downstream.

The catalog is held as a single source of truth (_CATALOG, faithfully transcribed from
docs/entity_intelligence_complete_reference.md), and the feed is GENERATED from it (counts computed, never typed).
Each candidate carries: our determinism_ceiling, its license, and a fragility block whose modes are REAL ids from
architecture/fragile_context_taxonomy.json — and `adoptable` is computed by cross-checking the license/package
against the org guardrail's AVOID ledger (architecture/org_guardrail_policies.json), so a copyleft/proprietary/
key-walled dependency is recorded as NON-adoptable rather than silently ingested.

  --build      (re)write the feed JSON
  --self-test  validate the catalog + the generated feed (the registered proof)

CLI: PYTHONPATH=. python3 scripts/ingest_entity_intelligence_catalog.py --build | --self-test
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FEED = _REPO / "data" / "capability-candidates" / "discovered-feed-entity-intelligence-2026-06-20.json"
_PROVENANCE = ("DueCare entity-intelligence reference (2026-06; docs/entity_intelligence_complete_reference.md) — "
               "endpoints/licenses/fragility verified live in that project 2026-06-13..19; re-verify before relying.")

# fragility flag -> default taxonomy modes (overridable per row); every id is real in fragile_context_taxonomy.json.
_FLAG_DEFAULT_MODES = {"green": ("FRESHNESS_FRAGILE",), "amber": ("SOURCE_FRAGILE", "AUTHORITY_FRAGILE"),
                       "red": ("SOURCE_FRAGILE",)}

# (slot, intent, category, source_kind, source_name, source_url, license, det_ceiling, flag, extra_modes, note)
_CATALOG: list[tuple] = [
    # ── connectors as reusable capability libs (CC0 / public-domain / permissive) ──
    ("gleif-lei-resolve", "Resolve a legal entity to its canonical GLEIF LEI (the global join key).",
     "identity-compliance", "rest_api", "GLEIF LEI Records API", "https://api.gleif.org/api/v1/lei-records",
     "CC0", 1.0, "green", ("AUTHORITY_FRAGILE",), "filter[entity.legalName] is EXACT not fuzzy → join on reg-number/LEI"),
    ("gleif-rr-parents", "Resolve GLEIF Level-2 direct/ultimate parent_of edges for an LEI.",
     "identity-compliance", "rest_api", "GLEIF Level-2 RR", "https://api.gleif.org/api/v1/lei-records",
     "CC0", 1.0, "green", (), "most entities report no parent (only group subsidiaries)"),
    ("openownership-bods", "Resolve beneficial-ownership owns_or_controls edges (with % share).",
     "identity-compliance", "rest_api", "OpenOwnership BODS", "https://oo-bodsdata.s3.amazonaws.com",
     "CC0", 0.95, "green", (), "bulk is ~GB; pull a bounded slice"),
    ("ofac-sdn-screen", "Screen a name against the OFAC SDN sanctions list.",
     "identity-compliance", "rest_api", "OFAC SDN", "https://www.treasury.gov/ofac/downloads/sdn.csv",
     "US public domain", 1.0, "green", ("COMPLIANCE_FRAGILE",), "extends our existing check_live_ofac_receipt"),
    ("worldbank-debarred", "Screen against World Bank debarred firms/individuals.",
     "identity-compliance", "rest_api", "World Bank debarred", "https://apigwext.worldbank.org",
     "public", 1.0, "green", ("COMPLIANCE_FRAGILE",), "1,241 entries; JSON"),
    ("doj-press-prosecutions", "Mine DOJ press releases for offense-tagged prosecutions (named defendants, MO).",
     "research", "rest_api", "DOJ press releases", "https://www.justice.gov/api/v1/press_releases.json",
     "US public domain", 0.9, "amber", (), "only title= + sort=date work; charges plain-language, tag on vocabulary not USC"),
    ("dol-whd-violations", "Resolve DOL Wage&Hour enforcement → employer-violation entities (H-2A/H-2B/MSPA).",
     "identity-compliance", "rest_api", "DOL WHD enforcement", "https://api.dol.gov/v4/get/WHD/enforcement/json",
     "US public domain", 0.85, "amber", (), "full data needs free DOL_API_KEY; v4 metadata is keyless for field maps"),
    ("domain-intel-rdap-dns", "Pivot a scam/recruitment domain → registrant + NS/MX edges (cluster siblings).",
     "identity-compliance", "library", "RDAP (whoisit) + DNS (dnspython)", "https://www.iana.org/whois",
     "BSD-3/ISC", 0.8, "amber", ("PRIVACY_FRAGILE",), "post-GDPR most registrant fields DATA REDACTED → skip+flag; registrar+DNS still pivot"),
    ("adverse-media-screen", "Negative-news / sanctions screening (Google News RSS + GDELT + OpenSanctions).",
     "research", "rest_api", "Google News RSS + GDELT", "https://news.google.com/rss/search",
     "mixed", 0.55, "amber", ("CONFLICT_FRAGILE",), "GDELT 429s on complex queries → quote name only, ~5s pace"),
    ("entity-screen-fuzzy", "Screen a name across collected registers → SANCTIONED/FLAGGED/LICENSED/NOT_FOUND.",
     "identity-compliance", "library", "RapidFuzz token_sort_ratio", "https://github.com/rapidfuzz/RapidFuzz",
     "MIT", 1.0, "green", (), "word-order-invariant + Jaccard; difflib fallback"),
    ("entity-link-lei", "Probabilistic record-linkage joining registry entities to GLEIF on the LEI.",
     "identity-compliance", "library", "splink (DuckDB)", "https://github.com/moj-analytical-services/splink",
     "MIT", 0.85, "amber", (), "splink EM degenerates on homogeneous names → used only for the LEI join, not clustering"),
    ("cluster-registries", "Pool tagged-by-source registries → deterministic cross-source clusters (entity on ≥2 lists).",
     "identity-compliance", "library", "deterministic union + RapidFuzz", "https://github.com/rapidfuzz/RapidFuzz",
     "MIT", 0.95, "green", ("CONFLICT_FRAGILE",), "name merges require a shared non-blank jurisdiction (else BLUE LAGOON false-merge)"),
    ("ftm-normalize", "Normalize any governed entity record → FollowTheMoney EntityProxy (Aleph-loadable).",
     "identity-compliance", "spec_or_standard", "FollowTheMoney schema", "https://github.com/alephdata/followthemoney",
     "MIT", 1.0, "green", (), "schema adopted via our src/baltor/native/ftm_adapter (PyICU-free); lib optional"),

    # ── clean deterministic registry SOURCES (server-rendered table / JSON API / file → deterministic spec) ──
    ("ph-gppb-blacklist", "PH GPPB blacklisted suppliers register.", "identity-compliance", "rest_api",
     "PH GPPB blacklist", "https://onlineblacklistingportal.gppb.gov.ph/obp-backend/cbr/cbr_public/",
     "public", 1.0, "green", ("COMPLIANCE_FRAGILE",), "114; flat JSON"),
    ("si-kpk-business-restrictions", "SI KPK business-restriction register.", "identity-compliance", "rest_api",
     "SI KPK restrictions", "https://registri.kpk-rs.si/registri/omejitve_poslovanja/seznam/omejitve.json",
     "public", 1.0, "green", (), "7,927; flat JSON (name=ps_naziv)"),
    ("br-bcb-disqualified", "BR central-bank disqualified administrators.", "financial-data", "rest_api",
     "BR BCB disqualified", "https://olinda.bcb.gov.br/olinda/servico/Gepad_QuadrosGeraisInternet/versao/v1/odata/QuadroGeralInabilitados",
     "public", 1.0, "green", ("PRIVACY_FRAGILE",), "426; OData; CPF masked at source"),
    ("afdb-debarred", "African Development Bank debarred entities.", "identity-compliance", "http_api",
     "AfDB debarred", "https://www.afdb.org/en/projects-operations/debarment-and-sanctions-procedures",
     "public", 1.0, "green", ("COMPLIANCE_FRAGILE",), "1,334; HTML table"),
    ("gb-modern-slavery", "UK Modern Slavery statement registry.", "identity-compliance", "rest_api",
     "UK Modern Slavery registry", "https://downloads.modern-slavery-statement-registry.service.gov.uk/publicdownloads/",
     "OGL", 1.0, "green", (), "11,718; year-templated CSV; group rows put co-number in OrgName"),
    ("us-dhs-uflpa", "US DHS UFLPA forced-labor entity list.", "identity-compliance", "rest_api",
     "US DHS UFLPA", "https://data.opensanctions.org/datasets/latest/us_dhs_uflpa/targets.simple.csv",
     "CC-BY-NC", 1.0, "amber", ("COMPLIANCE_FRAGILE",), "144; gov list public domain, OS export CC-BY-NC"),
    ("ca-tfwp-lmia", "Canada TFWP positive-LMIA employers.", "identity-compliance", "rest_api",
     "Canada TFWP LMIA", "https://open.canada.ca", "OGL-Canada", 1.0, "green", (), "7,476; CSV title-row quirk"),
    ("gb-licensed-sponsors", "UK Register of Licensed Sponsors (Home Office).", "identity-compliance", "rest_api",
     "UK Licensed Sponsors", "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers",
     "OGL", 1.0, "amber", ("FRESHNESS_FRAGILE",), "~141,980; discover-latest CSV link"),

    # ── bulk datasets (resolver-ingestible) ──
    ("opensanctions-consolidated", "Consolidated sanctions/PEP/debarment screening data (OFAC+EU+UN+80 sources).",
     "identity-compliance", "rest_api", "OpenSanctions", "https://data.opensanctions.org/datasets/latest/sanctions/targets.simple.csv",
     "CC-BY-NC", 0.95, "amber", ("COMPLIANCE_FRAGILE",), "hosted API now needs a key; self-host yente keyless"),
    ("icij-offshore-leaks", "ICIJ Offshore Leaks officers/entities graph.", "research", "rest_api",
     "ICIJ Offshore Leaks", "https://offshoreleaks-data.icij.org/offshoreleaks/csv/full-oldb.LATEST.zip",
     "ODbL", 0.9, "amber", (), "graph-CSV; cite ICIJ; share-alike on redistribution"),
    ("un-locode", "UN/LOCODE port/location code join key.", "geo-weather", "rest_api",
     "UN/LOCODE", "https://github.com/datasets/un-locode/raw/main/data/code-list.csv",
     "PDDL", 1.0, "green", (), "port/location join key"),
    ("global-fishing-watch", "GFW vessel identity (forced-labour-at-sea signal).", "identity-compliance", "rest_api",
     "Global Fishing Watch", "https://gateway.api.globalfishingwatch.org",
     "CC-BY-NC-SA", 0.85, "amber", (), "free token; NC"),

    # ── AVOID ledger: recorded as NON-adoptable candidates (discovery includes recording what NOT to adopt) ──
    ("AVOID-searxng", "Meta-search (AVOID — AGPL).", "research", "github_tools_repo", "searxng",
     "https://github.com/searxng/searxng", "AGPL-3.0", 0.6, "red", (), "AGPL → use ddgs (MIT) instead"),
    ("AVOID-theharvester", "OSINT email/subdomain harvester (AVOID — GPL-2.0, CLI-only).", "research",
     "github_tools_repo", "theharvester", "https://github.com/laramies/theHarvester", "GPL-2.0", 0.6, "red", (),
     "GPL-2.0, CLI-only → not importable as a dep"),
    ("AVOID-shodan", "Internet asset search (AVOID — proprietary + paid key).", "research", "library", "shodan",
     "https://github.com/achillean/shodan-python", "proprietary", 0.6, "red", (), "proprietary-ish + paid key"),
]


def _modes_for(flag: str, extra: tuple) -> list:
    return list(dict.fromkeys(list(_FLAG_DEFAULT_MODES.get(flag, ())) + list(extra)))


def _denied() -> tuple[set, set]:
    pol = json.loads((_REPO / "architecture" / "org_guardrail_policies.json").read_text())
    p = pol["policies"]["entity-intelligence-vetted-deps"]
    return {x.lower() for x in p["denied_licenses"]}, {x.lower() for x in p["denied_packages"]}


def _adoptable(license_: str, source_name: str) -> bool:
    dl, dp = _denied()
    return not (license_.strip().lower() in dl or source_name.strip().lower() in dp)


def build_candidates() -> list[dict]:
    out = []
    for (slot, intent, cat, kind, sname, surl, lic, det, flag, extra, note) in _CATALOG:
        out.append({
            "capability_slot": slot, "intent": intent,
            "input_contract": "an entity name / identifier / query",
            "output_contract": "governed candidate entity records (serves_truth=false; FtM-normalizable)",
            "category": cat, "source_kind": kind, "source_name": sname, "source_url": surl, "license": lic,
            "gap_hypothesis": f"base models cannot enumerate or verify '{slot}' from parametric memory; this register is the authority",
            "lift_hypothesis": "a governed register lookup beats the model's guess on coverage + currency + provenance",
            "determinism_ceiling": det, "deterministic_coverage_estimate": det,
            "verify_note": note,
            "fragility": {"flag": flag, "modes": _modes_for(flag, extra), "note": note},
            "adoptable": _adoptable(lic, sname),
            "serves_truth": False,
        })
    return out


def build_feed() -> dict:
    cands = build_candidates()
    return {
        "feed_version": "DiscoveredCapabilityFeed.v1",
        "discovered_at": "2026-06-20",
        "discovery_method": "cross-project import from the DueCare entity-intelligence reference dump (not live re-crawled)",
        "provenance": _PROVENANCE,
        "governance": ("CANDIDATES ONLY — discovery is not trust. No row here is an active capability; each must pass "
                       "the gap/lift screen, then human/eval gates, before any promotion. Fragility modes are real ids "
                       "from fragile_context_taxonomy.json; `adoptable` cross-checks the org guardrail AVOID ledger; "
                       "AVOID-* rows are recorded as NON-adoptable on purpose. serves_truth=false for everything."),
        "candidates": cands,
    }


def write_feed() -> str:
    _FEED.parent.mkdir(parents=True, exist_ok=True)
    _FEED.write_text(json.dumps(build_feed(), indent=2) + "\n")
    return str(_FEED.relative_to(_REPO))


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    feed = build_feed()
    cands = feed["candidates"]
    taxonomy = json.loads((_REPO / "architecture" / "fragile_context_taxonomy.json").read_text())
    valid_modes = {m["id"] for m in taxonomy["fragility_modes"]}

    ck("feed conforms to DiscoveredCapabilityFeed.v1 with provenance + governance",
       feed["feed_version"] == "DiscoveredCapabilityFeed.v1" and bool(feed.get("provenance")) and bool(feed.get("governance")))
    req = {"capability_slot", "intent", "category", "source_kind", "source_name", "source_url", "license",
           "determinism_ceiling", "verify_note", "fragility", "adoptable", "serves_truth"}
    ck("every candidate carries the required candidate keys", all(req <= set(c) for c in cands),
       str([c["capability_slot"] for c in cands if not req <= set(c)]))
    ck("every candidate is propose-only (serves_truth=false)", all(c["serves_truth"] is False for c in cands))
    ck("every fragility mode is a REAL id from the taxonomy (no invented modes)",
       all(set(c["fragility"]["modes"]) <= valid_modes for c in cands),
       str(sorted({m for c in cands for m in c["fragility"]["modes"] if m not in valid_modes})))
    ck("determinism_ceiling is a 0..1 float for every candidate",
       all(isinstance(c["determinism_ceiling"], (int, float)) and 0.0 <= c["determinism_ceiling"] <= 1.0 for c in cands))
    ck("every candidate records a license", all(c["license"] for c in cands))

    # the AVOID ledger cross-check: copyleft/proprietary/denied-package rows are recorded NON-adoptable
    avoid = [c for c in cands if c["capability_slot"].startswith("AVOID-")]
    ck("AVOID-* rows are recorded as NON-adoptable (cross-checked vs the org guardrail)",
       len(avoid) >= 3 and all(c["adoptable"] is False for c in avoid))
    clean = [c for c in cands if not c["capability_slot"].startswith("AVOID-")]
    ck("clean CC0/public-domain/permissive rows are adoptable", all(c["adoptable"] is True for c in clean),
       str([c["capability_slot"] for c in clean if not c["adoptable"]]))
    # at least one row directly extends our existing compliance beachhead (OFAC) + one is our FtM standard
    ck("the feed extends the existing compliance beachhead (OFAC) + wires our FtM standard",
       any(c["capability_slot"] == "ofac-sdn-screen" for c in cands)
       and any(c["capability_slot"] == "ftm-normalize" for c in cands))

    # if already written, the on-disk feed must be fresh (no drift); always: deterministic
    if _FEED.exists():
        ck("the on-disk feed is fresh vs the catalog (regenerate with --build)",
           json.loads(_FEED.read_text()) == feed)
    ck("deterministic", build_feed() == feed)

    n_clean = len(clean)
    print("\n" + (f"PASS - ingest_entity_intelligence_catalog: {len(cands)} governed CANDIDATES ({n_clean} adoptable + "
                  f"{len(avoid)} AVOID-recorded) staged from the DueCare reference; every fragility mode is a real "
                  f"taxonomy id, every row is propose-only (serves_truth=false), and the AVOID ledger is cross-checked "
                  f"against the org guardrail. Discovery is not trust — nothing is promoted."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--build" in argv:
        print("wrote:", write_feed())
        return 0
    if "--self-test" in argv:
        return _self_test()
    print("usage: ingest_entity_intelligence_catalog.py --build | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
