#!/usr/bin/env python3
"""corporate_records_scraping_primitive_pack — ≥50 governed corporate-records scraping primitives.

Owner (2026-07-10): "What about primitives for corporate records scraping, we'd have to have at least 50 of
these." This pack covers the PUBLIC-RECORD corporate surfaces (SEC EDGAR, Companies House UK, OpenCorporates,
GLEIF LEI, state Secretary-of-State registries, IRS 990, SAM.gov, UCC liens, court dockets, USPTO assignments,
FinCEN BOI access-modeling, municipal license portals) plus the cross-source spine (policy gates, rate budgets,
CDC watermarks, entity normalize/link/dedupe, provenance receipts, review tickets).

Stance baked into every card: HONOR source policy — official APIs and bulk files first, robots/ToS gates before
any fetch, fee/rate budgets enforced, no evasion of access controls, public-record fields only (officer names as
published by the registry), review tickets instead of silent merges on conflicts. All rows are candidate-only
(`candidate=true, serves_truth=false`) until the promotion gates run.

    PYTHONPATH=. python3 scripts/corporate_records_scraping_primitive_pack.py --self-test
    PYTHONPATH=. python3 scripts/corporate_records_scraping_primitive_pack.py --build
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  the ONE id authority (data plane law)
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"corporate_records_scraping_primitive_pack requires canonical_id; import failed: {exc}")

PACK_DIR = _SBC / "data" / "dev-intel" / "primitive_factory" / "specialized_packs"
CARDS_PATH = PACK_DIR / "corporate_records_scraping_primitive_cards.jsonl"
MANIFEST_PATH = PACK_DIR / "corporate_records_scraping_manifest.json"
ID_PREFIX = "cpc:corporate-records"
MINIMUM_CARDS = 50   # owner floor 2026-07-10 — the self-test RATCHETS on it, never goes below
_PLACEHOLDER_MARKERS = ("todo", "tbd", "lorem", "placeholder", "fixme")

#: (family, title, blackbox, consumes_edge, produces_edge, extra blocking keys, source_policy)
#: Every blackbox names the CONCRETE surface (endpoint/format/policy) — no combinatorial padding.
_ROWS: list[tuple[str, str, str, str, str, list[str], str]] = [
    # ── SEC EDGAR (US federal; free; fair-access ~10 req/s with declared User-Agent) ─────────────────
    ("sec_edgar", "EDGAR daily filing index enumerator",
     "Enumerates SEC EDGAR daily/quarterly index files (form.idx, master.idx under /Archives/edgar/"
     "daily-index/) into typed filing references with CIK, form type, date, and accession number; honors the "
     "fair-access policy (declared User-Agent, ~10 req/s ceiling) and resumes from a date watermark.",
     "EdgarIndexWindowRequest", "EdgarFilingReferenceBatch", ["edgar", "sec", "index", "10-k"],
     "public; SEC fair-access policy; declared User-Agent required"),
    ("sec_edgar", "EDGAR full-text search adapter",
     "Queries the official EDGAR full-text search API (efts.sec.gov/LATEST/search-index?q=) with paged, "
     "rate-budgeted requests and returns scored filing hits with accession numbers and highlight spans — the "
     "sanctioned lane for keyword discovery across filings.",
     "EdgarFullTextQuery", "EdgarSearchHitBatch", ["edgar", "full-text", "search", "sec"],
     "public; official search API; rate budget enforced"),
    ("sec_edgar", "EDGAR XBRL company-facts parser",
     "Fetches api.sec.gov/api/xbrl/companyfacts/CIK##########.json and normalizes XBRL facts (us-gaap/dei "
     "taxonomies) into period-stamped fact rows with units, frames, and accession lineage for a company.",
     "EdgarCompanyFactsRequest", "XbrlFactRowBatch", ["xbrl", "company facts", "us-gaap", "edgar"],
     "public; official JSON API"),
    ("sec_edgar", "EDGAR accession fetch-plan builder",
     "Turns a batch of discovered EDGAR filing references (CIK + accession + form) into a governed, "
     "rate-budgeted accession fetch plan — deduping already-fetched accessions against the content-hash "
     "ledger and ordering by the fair-access budget — so the document fetcher pulls only what changed. The "
     "bridge that makes filing discovery and document retrieval one chain instead of two islands.",
     "EdgarFilingReferenceBatch", "EdgarAccessionFetchPlan", ["edgar", "fetch plan", "accession", "budget"],
     "public; SEC fair-access policy; dedupes against the receipt ledger"),
    ("sec_edgar", "EDGAR filing document fetcher",
     "Retrieves the primary document set for one accession number (10-K, 10-Q, 8-K, S-1 exhibits) from "
     "/Archives/edgar/data/<CIK>/<accession>/ with retry+backoff, content hashing per file, and a source "
     "receipt naming URL, bytes, and SHA-256 — never re-fetches an unchanged document.",
     "EdgarAccessionFetchPlan", "FilingDocumentBundle", ["8-k", "10-q", "accession", "fetch"],
     "public; SEC fair-access policy"),
    ("sec_edgar", "EDGAR filing-bundle officer extractor",
     "Extracts officer and director rows (name as published, title, appointment dates) from a fetched EDGAR "
     "filing document bundle — the form-agnostic extractor that reads whatever primary documents the fetcher "
     "pulled — carrying the accession as provenance and a review flag on conflicts; public-record fields only.",
     "FilingDocumentBundle", "OfficerRowBatch", ["edgar", "officers", "extract", "bundle"],
     "public filing; person fields as-published only; review queue on conflicts"),
    ("sec_edgar", "DEF 14A officer and director extractor",
     "Parses proxy statements (DEF 14A) into officer/director rows — name as published, title, committee "
     "memberships, and compensation-table references — public-record fields only, each row carrying the "
     "filing accession as provenance and a review flag instead of any inferred enrichment.",
     "ProxyStatementDocument", "OfficerDirectorRowBatch", ["def 14a", "proxy", "officers", "directors"],
     "public filing; person fields limited to as-published; review queue on conflicts"),
    ("sec_edgar", "13F institutional holdings parser",
     "Parses 13F-HR information tables (XML) into holdings rows (issuer, CUSIP, shares, value) with the "
     "filer's CIK and period, normalizing share-class suffixes and flagging amended filings for supersede "
     "handling rather than silent overwrite.",
     "ThirteenFFilingDocument", "InstitutionalHoldingRowBatch", ["13f", "holdings", "cusip", "institutional"],
     "public filing"),
    ("sec_edgar", "CIK to ticker crosswalk builder",
     "Builds the CIK↔ticker↔company-name crosswalk from the official company_tickers.json and submissions "
     "API, emitting canonical mapping rows with effective dates so downstream entity linking joins on stable "
     "identifiers instead of names.",
     "CikTickerCrosswalkRequest", "EntityIdentifierMapBatch", ["cik", "ticker", "crosswalk", "mapping"],
     "public; official JSON"),
    ("sec_edgar", "Form D exempt-offering extractor",
     "Extracts Form D filings (Regulation D exempt offerings) into issuer, related-person, and offering-size "
     "rows — a primary discovery surface for private companies that never file 10-Ks.",
     "FormDFilingDocument", "ExemptOfferingRowBatch", ["form d", "reg d", "private", "offering"],
     "public filing"),
    # ── Companies House UK (free API key; 600 req / 5 min) ───────────────────────────────────────────
    ("companies_house_uk", "Companies House company profile fetcher",
     "Fetches api.company-information.service.gov.uk/company/{number} with an API key, normalizing "
     "registered name, status, incorporation date, SIC codes, and registered office into canonical entity "
     "fields; honors the 600-requests-per-5-minutes quota with a token bucket.",
     "CompaniesHouseNumberRequest", "UkCompanyProfileRecord", ["companies house", "uk", "profile", "sic"],
     "free API key; 600/5min quota; Crown copyright attribution"),
    ("companies_house_uk", "Companies House officers list adapter",
     "Pages /company/{number}/officers into officer rows (name as registered, role, appointed/resigned "
     "dates, partial DOB month-year exactly as the register publishes) with pagination cursors and no "
     "enrichment beyond the public record.",
     "UkCompanyOfficersRequest", "UkOfficerRowBatch", ["officers", "appointments", "companies house", "uk"],
     "public register; person fields as-published only"),
    ("companies_house_uk", "Persons-with-significant-control parser",
     "Normalizes /persons-with-significant-control into ownership-nature rows (kinds of control, ceased "
     "markers, statement cases) so beneficial-ownership graphs cite the register verbatim with per-row "
     "provenance.",
     "UkPscRequest", "PscControlRowBatch", ["psc", "significant control", "ownership", "uk"],
     "public register"),
    ("companies_house_uk", "Companies House filing history enumerator",
     "Enumerates /company/{number}/filing-history with category filters (accounts, confirmation-statement, "
     "officers, charges) into filing references with transaction ids and document metadata links.",
     "UkFilingHistoryRequest", "UkFilingReferenceBatch", ["filing history", "accounts", "charges", "uk"],
     "free API key; quota enforced"),
    ("companies_house_uk", "UK insolvency and charges extractor",
     "Reads /company/{number}/insolvency and /charges into structured case and charge rows (practitioners, "
     "charge status, secured amounts where published) with review tickets on ambiguous case states.",
     "UkInsolvencyChargesRequest", "InsolvencyChargeRowBatch", ["insolvency", "charges", "secured", "uk"],
     "public register; review queue on ambiguity"),
    # ── OpenCorporates (licensed aggregator; share-alike terms) ──────────────────────────────────────
    ("opencorporates", "OpenCorporates company search normalizer",
     "Wraps api.opencorporates.com/v0.4/companies/search into jurisdiction-scoped candidate entity rows, "
     "carrying the OpenCorporates URL and retrieved-at timestamp; results are LICENSE-GATED (share-alike) "
     "and marked non-redistributable until the license check passes.",
     "OpenCorporatesSearchQuery", "AggregatorEntityCandidateBatch", ["opencorporates", "search", "aggregator"],
     "API token; ODbL share-alike — license gate BEFORE persistence"),
    ("opencorporates", "Cross-jurisdiction entity resolver",
     "Resolves one legal entity across jurisdiction registries by combining registry numbers, normalized "
     "names, and incorporation dates from aggregator hits, emitting match candidates with per-feature score "
     "breakdowns — never an auto-merge; ambiguous matches become review tickets.",
     "CrossJurisdictionResolveRequest", "EntityMatchCandidateBatch", ["cross-jurisdiction", "resolve", "match"],
     "derived; inherits strictest upstream license"),
    ("opencorporates", "Aggregator license-compliance gate",
     "Blocks persistence of aggregator-sourced rows unless the declared license (ODbL/share-alike/API terms) "
     "is compatible with the target store's policy; emits an allow/deny receipt naming the license clause — "
     "the gate every aggregator ingest must pass first.",
     "AggregatorIngestPlan", "LicenseGateDecisionReceipt", ["license", "odbl", "compliance", "gate"],
     "policy primitive; deny-by-default"),
    # ── GLEIF LEI (free, CC0 golden copy) ────────────────────────────────────────────────────────────
    ("gleif_lei", "GLEIF golden-copy delta ingester",
     "Ingests the GLEIF LEI golden-copy files (Level 1 who-is-who, published CC0) by delta window, emitting "
     "upsert rows keyed by LEI with registration status transitions tracked as CDC events, not overwrites.",
     "GleifGoldenCopyWindow", "LeiRecordUpsertBatch", ["gleif", "lei", "golden copy", "cc0"],
     "public CC0 bulk files"),
    ("gleif_lei", "LEI relationship graph parser",
     "Parses GLEIF Level 2 relationship records (accounting-consolidation parents) into typed ownership "
     "edges between LEIs, preserving exception reasons when a parent is not reported.",
     "GleifRelationshipFile", "LeiOwnershipEdgeBatch", ["level 2", "parent", "ownership", "lei"],
     "public CC0"),
    ("gleif_lei", "Entity legal-form normalizer",
     "Maps registry legal-form strings to the GLEIF Entity Legal Form (ELF) code list so 'GmbH', 'Ltd', "
     "'S.A.' variants normalize to coded forms with jurisdiction context — a shared vocabulary for every "
     "registry ingest in this pack.",
     "LegalFormNormalizeRequest", "ElfCodedFormBatch", ["elf", "legal form", "normalize", "vocabulary"],
     "public code list"),
    # ── US state Secretary-of-State registries ───────────────────────────────────────────────────────
    ("state_sos", "State SoS business-search adapter (policy-tabled)",
     "Adapts per-state Secretary-of-State business searches behind ONE interface driven by a per-state "
     "policy table (official API > bulk download > HTML only where ToS permits; Delaware/California/New York "
     "exemplars included); states whose terms forbid automation are marked blocked with the clause cited.",
     "StateEntitySearchRequest", "StateEntityCandidateBatch", ["secretary of state", "business search", "state"],
     "per-state policy table; ToS-gated; no CAPTCHA/anti-bot evasion"),
    ("state_sos", "Registered-agent extractor",
     "Extracts registered-agent name and service address from state entity detail records into agent rows "
     "linked to the entity, flagging commercial mass-agents (CT Corporation, Registered Agents Inc.) for "
     "cluster analysis instead of treating them as owner signals.",
     "StateEntityDetailRecord", "RegisteredAgentRowBatch", ["registered agent", "service address", "state"],
     "public record"),
    ("state_sos", "Entity status normalizer (good standing)",
     "Normalizes heterogeneous state status strings (active/good standing/forfeited/void/administratively "
     "dissolved) into a coded status vocabulary with per-state mapping provenance and effective dates.",
     "StateStatusNormalizeRequest", "CodedEntityStatusBatch", ["good standing", "dissolved", "status", "state"],
     "public record; mapping table versioned"),
    ("state_sos", "Annual-report metadata collector",
     "Collects annual/biennial report filing metadata (period, filed date, delinquency flags) where the "
     "state exposes it, emitting compliance-timeline rows that make shell-staleness measurable.",
     "StateAnnualReportRequest", "ComplianceTimelineRowBatch", ["annual report", "delinquent", "compliance"],
     "public record where exposed"),
    ("state_sos", "State registry ToS and anti-bot policy gate",
     "Evaluates a state portal's terms, robots.txt, and posted automation rules BEFORE any fetch plan is "
     "runnable; output is an allow/deny/bulk-only decision receipt with the governing clause quoted — "
     "denied states route to bulk-file or manual-request lanes, never evasion.",
     "StatePortalPolicyRequest", "PortalPolicyDecisionReceipt", ["tos", "robots", "policy gate", "state"],
     "policy primitive; deny-by-default"),
    # ── IRS 990 nonprofits ───────────────────────────────────────────────────────────────────────────
    ("irs_990", "IRS 990 e-file index enumerator",
     "Enumerates the public IRS 990 e-file indexes (annual index CSV/JSON of electronically filed 990/990-EZ/"
     "990-PF) into filing references keyed by EIN and object id, windowed by tax period.",
     "Irs990IndexWindow", "NonprofitFilingReferenceBatch", ["990", "irs", "nonprofit", "e-file"],
     "public bulk index"),
    ("irs_990", "990 officer and compensation extractor",
     "Parses 990 Part VII (officers, directors, trustees, key employees) into as-filed rows with reported "
     "compensation figures and hours — public filing fields only, each row carrying EIN + object id "
     "provenance and a review flag on OCR-degraded values.",
     "Irs990FilingDocument", "NonprofitOfficerRowBatch", ["part vii", "compensation", "officers", "990"],
     "public filing; as-filed fields only"),
    ("irs_990", "EIN entity linker",
     "Links EINs to canonical entities using IRS Exempt Organizations BMF extracts plus name/address "
     "blocking, emitting match candidates with score breakdowns and review tickets under threshold.",
     "EinLinkRequest", "EinEntityMatchBatch", ["ein", "bmf", "link", "nonprofit"],
     "public extract"),
    # ── SAM.gov federal registrations ────────────────────────────────────────────────────────────────
    ("sam_gov", "SAM.gov entity registration fetcher",
     "Fetches api.sam.gov/entity-information/v3/entities with an api.data.gov key, normalizing UEI, legal "
     "business name, physical address, and registration status into canonical entity fields under the "
     "posted rate limits.",
     "SamEntityRequest", "FederalRegistrationRecordBatch", ["sam.gov", "uei", "registration", "federal"],
     "api.data.gov key; posted rate limits"),
    ("sam_gov", "Exclusions (debarment) delta watcher",
     "Polls the SAM.gov exclusions extract for newly debarred/reinstated parties, emitting CDC events with "
     "exclusion type, agency, and effective dates — a screening feed that composes with the OFAC lane.",
     "SamExclusionsWindow", "ExclusionCdcEventBatch", ["exclusions", "debarment", "screening", "delta"],
     "public extract"),
    ("sam_gov", "UEI-DUNS crosswalk mapper",
     "Maintains the UEI↔legacy-DUNS crosswalk from SAM extracts with effective-dated mapping rows so "
     "pre-2022 contractor records join to current UEIs without guessing.",
     "UeiDunsCrosswalkRequest", "IdentifierCrosswalkBatch", ["uei", "duns", "crosswalk", "contractor"],
     "public extract"),
    # ── UCC lien filings ─────────────────────────────────────────────────────────────────────────────
    ("ucc_filings", "UCC-1 filing search adapter",
     "Searches state UCC lien indexes (debtor or secured-party name) behind the same per-state policy table "
     "as the SoS adapter, returning filing references with file numbers, lapse dates, and amendment chains.",
     "UccSearchRequest", "UccFilingReferenceBatch", ["ucc", "lien", "ucc-1", "debtor"],
     "per-state policy table; ToS-gated"),
    ("ucc_filings", "Secured-party normalizer",
     "Normalizes secured-party names (bank branches, servicers, assignees) into canonical creditor entities "
     "with lender-family clustering so one bank's fifty branch spellings read as one creditor.",
     "SecuredPartyRowBatch", "CanonicalCreditorBatch", ["secured party", "creditor", "normalize", "ucc"],
     "public filing"),
    ("ucc_filings", "Collateral description parser",
     "Parses UCC collateral text into typed collateral classes (equipment, receivables, all-assets, "
     "specific-serial) with serial-number extraction where present — text kept verbatim alongside the "
     "classification, never replaced by it.",
     "UccCollateralText", "CollateralClassRowBatch", ["collateral", "all assets", "equipment", "parse"],
     "public filing; lossless verbatim retained"),
    # ── Court dockets ────────────────────────────────────────────────────────────────────────────────
    ("court_dockets", "RECAP archive docket searcher",
     "Searches the free RECAP archive (CourtListener API) for federal dockets naming an entity, returning "
     "docket references with court, case number, nature-of-suit, and document availability — the no-fee "
     "lane that runs before any PACER spend.",
     "RecapDocketQuery", "DocketReferenceBatch", ["recap", "courtlistener", "docket", "federal"],
     "free API; attribution"),
    ("court_dockets", "Docket entry normalizer",
     "Normalizes docket entries into typed event rows (complaint, judgment, dismissal, appeal) with dates "
     "and document links, preserving the clerk's verbatim text next to the coded event.",
     "DocketEntryBatch", "CourtEventRowBatch", ["docket entries", "judgment", "dismissal", "events"],
     "public record; lossless verbatim retained"),
    ("court_dockets", "Case-party entity linker",
     "Links case parties to canonical entities with role awareness (plaintiff/defendant/creditor) and "
     "corporate-suffix-tolerant blocking; low-confidence links emit review tickets, never silent joins.",
     "CasePartyRowBatch", "PartyEntityMatchBatch", ["party", "plaintiff", "defendant", "link"],
     "derived; review queue under threshold"),
    ("court_dockets", "PACER fee-budget gate",
     "Enforces a per-run PACER spending budget (page-count estimates × $0.10 capped at document maximums) "
     "and requires an explicit budget receipt before any billable fetch; RECAP-available documents are "
     "always preferred and the gate proves it.",
     "PacerFetchPlan", "FeeBudgetDecisionReceipt", ["pacer", "fees", "budget", "gate"],
     "fee-gated; RECAP-first policy"),
    # ── USPTO assignments ────────────────────────────────────────────────────────────────────────────
    ("uspto", "Patent assignment delta ingester",
     "Ingests USPTO patent assignment daily XML (assignment-application bulk files) into conveyance rows "
     "(assignor, assignee, reel/frame, conveyance type) windowed by recorded date.",
     "UsptoAssignmentWindow", "PatentConveyanceRowBatch", ["uspto", "assignment", "reel frame", "patent"],
     "public bulk XML"),
    ("uspto", "Assignment party normalizer",
     "Normalizes assignor/assignee names to canonical entities with corporate-suffix and merger-alias "
     "handling, emitting IP-transfer edges that expose acquisition activity before press releases do.",
     "AssignmentPartyRowBatch", "IpTransferEdgeBatch", ["assignee", "assignor", "normalize", "transfer"],
     "derived from public record"),
    ("uspto", "TSDR trademark status fetcher",
     "Fetches trademark status via the TSDR API (tsdr.uspto.gov) with key-based quotas, emitting mark "
     "status rows (live/dead, register, owner of record) linked to owning entities.",
     "TsdrStatusRequest", "TrademarkStatusRowBatch", ["tsdr", "trademark", "status", "owner"],
     "API key; posted quotas"),
    # ── FinCEN BOI (access-restricted — modeled, not scraped) ────────────────────────────────────────
    ("fincen_boi", "FinCEN BOI access-policy gate",
     "Models the FinCEN beneficial-ownership register's ACCESS RESTRICTION as a hard deny for scraping: "
     "BOI data is available only to authorized recipients through official channels, so every request plan "
     "is refused with the governing rule cited and routed to the authorized-request lane — this primitive "
     "exists to make 'we do not scrape this' an executable, receipted decision.",
     "BoiAccessRequest", "AccessDenialReceipt", ["fincen", "boi", "beneficial ownership", "restricted"],
     "RESTRICTED; authorized recipients only; scraping denied by design"),
    ("fincen_boi", "Authorized-request audit trail assembler",
     "Assembles the audit record for a lawful BOI request made OUTSIDE scraping (requester authority, "
     "purpose code, request/response hashes, retention clock) so restricted-data handling is provable "
     "end-to-end.",
     "AuthorizedBoiRequestRecord", "RestrictedAccessAuditReceipt", ["authorized", "audit", "retention"],
     "restricted-data governance primitive"),
    # ── Municipal / business licenses (open-data portals) ────────────────────────────────────────────
    ("municipal_licenses", "Socrata business-license dataset enumerator",
     "Enumerates city open-data portals (Socrata SODA API / CKAN) for business-license datasets, emitting "
     "dataset references with update cadence and field schemas — app-token rate etiquette respected.",
     "OpenDataPortalQuery", "LicenseDatasetReferenceBatch", ["socrata", "ckan", "open data", "license"],
     "public open data; app-token etiquette"),
    ("municipal_licenses", "License record normalizer",
     "Normalizes heterogeneous municipal license rows (business name, license type, issue/expiry, address) "
     "into a shared license schema with per-city field-mapping provenance.",
     "RawLicenseRowBatch", "NormalizedLicenseRowBatch", ["license", "expiry", "normalize", "municipal"],
     "public open data"),
    ("municipal_licenses", "Address-to-entity linker",
     "Links license addresses to registered entities via normalized-address blocking (USPS-style "
     "standardization) plus name similarity, exposing operating-location graphs; sub-threshold matches "
     "become review tickets.",
     "LicenseAddressLinkRequest", "AddressEntityMatchBatch", ["address", "link", "location", "match"],
     "derived; review queue under threshold"),
    # ── Cross-source spine (the ops every family composes with) ──────────────────────────────────────
    ("cross_source", "Robots and terms-of-service pre-flight checker",
     "Resolves robots.txt, posted API terms, and rate-limit headers for a target host into a fetch-policy "
     "decision (allowed paths, crawl delay, bulk-preferred, denied) BEFORE any scraping plan compiles; "
     "decisions are receipts, cached with TTL, and deny-by-default on ambiguity.",
     "SourcePolicyProbeRequest", "FetchPolicyDecisionReceipt", ["robots", "tos", "preflight", "policy"],
     "policy primitive; deny-by-default"),
    ("cross_source", "Per-domain rate-budget scheduler",
     "Schedules fetches under per-domain token buckets (requests/second, concurrency, daily caps) shared "
     "across workers via a lease table, so the whole fleet honors one source's budget as one client.",
     "FetchQueueBatch", "RateBudgetedFetchPlan", ["rate limit", "token bucket", "scheduler", "budget"],
     "infrastructure primitive"),
    ("cross_source", "Incremental CDC watermark manager",
     "Tracks per-source high-water marks (date, accession, cursor) with idempotent advance receipts so "
     "re-runs fetch only the delta and a crashed run resumes exactly where it stopped.",
     "CdcWatermarkRequest", "WatermarkAdvanceReceipt", ["cdc", "watermark", "incremental", "resume"],
     "infrastructure primitive"),
    ("cross_source", "Fetch receipt and content-hash recorder",
     "Records every fetch as a receipt (URL, timestamp, status, byte count, SHA-256, policy decision id) "
     "and detects content change by hash so formatting-only churn never creates false versions.",
     "FetchCompletionEvent", "ProvenanceReceiptRow", ["receipt", "sha-256", "provenance", "hash"],
     "infrastructure primitive"),
    ("cross_source", "Canonical corporate-entity normalizer",
     "Normalizes any source's entity fields into the canonical_entity row family (legal name, jurisdiction, "
     "registry id, ELF-coded form, status, addresses) with per-field source attribution — the convergence "
     "point every family in this pack emits into.",
     "SourceEntityRecordBatch", "CanonicalEntityRowBatch", ["canonical entity", "normalize", "jurisdiction"],
     "row-family primitive"),
    ("cross_source", "Officer dedupe clusterer",
     "Clusters officer/agent person rows across sources with blocking (name keys + entity context) and "
     "conservative similarity, producing dedupe_cluster rows whose merges are PROPOSALS with review "
     "tickets — public-record person data is never auto-merged.",
     "OfficerRowBatch", "OfficerDedupeClusterBatch", ["dedupe", "cluster", "blocking", "officers"],
     "review-gated; no auto-merge of person rows"),
    ("cross_source", "Jurisdiction router",
     "Routes an entity-lookup intent to the right registry primitives by jurisdiction (US-DE → SoS adapter; "
     "UK → Companies House; LEI-known → GLEIF-first) with a non-destructive fallback that fans out to ALL "
     "candidate registries on low confidence.",
     "EntityLookupIntent", "RegistryRoutePlan", ["router", "jurisdiction", "fallback", "fan-out"],
     "routing primitive; non-destructive fallback"),
    ("cross_source", "Conflicting-fact review-ticket emitter",
     "Emits review_ticket rows whenever two sources disagree on a load-bearing field (status, officers, "
     "registered address), packaging both claims with provenance side-by-side — disagreement is surfaced, "
     "never resolved by overwrite.",
     "FactConflictEvent", "ReviewTicketRow", ["review ticket", "conflict", "disagreement", "queue"],
     "governance primitive"),
    ("cross_source", "Provenance chain assembler",
     "Assembles the end-to-end lineage for one served fact (fetch receipt → parse → normalize → link → "
     "publish) into a verifiable chain with hashes at every hop, making 'where did this row come from' a "
     "single query.",
     "ServedFactReference", "ProvenanceChainRecord", ["lineage", "chain", "verifiable", "provenance"],
     "governance primitive"),
    ("cross_source", "Registry-change CDC propagator",
     "Propagates detected registry changes (status flips, officer changes, new filings) as signed CDC "
     "events to downstream subscribers with revocation support, so stale copies are correctable — the "
     "volatile-public-facts handling the promotion gates require.",
     "RegistryChangeEventBatch", "SignedCdcEventBatch", ["cdc", "revocation", "signed", "propagate"],
     "governance primitive"),
]


def build_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for family, title, blackbox, consumes, produces, extra_keys, policy in _ROWS:
        card_id = canonical_id(ID_PREFIX, family, title)
        cards.append({
            "card_id": card_id,
            "primitive_id": card_id,
            "title": title,
            "blackbox": blackbox,
            "family": family,
            "pack": "corporate_records_scraping",
            "input_edge": consumes,
            "output_edge": produces,
            "composition_hints": {"consumes_edge": consumes, "produces_edge": produces,
                                  "candidate_only": True},
            "blocking_keys": sorted({*extra_keys, "corporate records", "scraping", family.replace("_", " ")}),
            "source_policy": policy,
            "governance": {"public_records_only": True, "no_access_control_evasion": True,
                           "person_fields_as_published_only": True, "review_queue_on_conflict": True},
            "schema_version": "1",
            "candidate": True,
            "serves_truth": False,
        })
    return cards


def build(write: bool = True) -> dict[str, Any]:
    cards = build_cards()
    lines = "".join(json.dumps(card, sort_keys=True) + "\n" for card in cards)
    manifest = {
        "record_type": "corporate_records_scraping_pack_manifest",
        "card_count": len(cards),                       # computed, never typed
        "families": sorted({card["family"] for card in cards}),
        "minimum_cards_floor": MINIMUM_CARDS,
        "cards_path": str(CARDS_PATH.relative_to(_ROOT)),
        "source_ref": "owner-intent:corporate-records-scraping:2026-07-10",
        "candidate": True,
        "serves_truth": False,
    }
    if write:
        PACK_DIR.mkdir(parents=True, exist_ok=True)
        CARDS_PATH.write_text(lines)
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return {"cards": len(cards), "families": len(manifest["families"]), "written": write,
            "cards_path": str(CARDS_PATH), "manifest_path": str(MANIFEST_PATH),
            "candidate": True, "serves_truth": False}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    cards = build_cards()

    checks.append((f"owner floor: >= {MINIMUM_CARDS} cards (RATCHET — computed count {len(cards)})",
                   len(cards) >= MINIMUM_CARDS, str(len(cards))))
    checks.append(("ids unique + minted by canonical_id (prefix + 16-hex)",
                   len({c["card_id"] for c in cards}) == len(cards)
                   and all(c["card_id"].startswith(f"{ID_PREFIX}-") and
                           len(c["card_id"].rsplit("-", 1)[1]) == 16 for c in cards), ""))
    checks.append(("every card candidate-only with typed edges + >=4 blocking keys + real blackbox (>=120 chars)",
                   all(c["candidate"] is True and c["serves_truth"] is False
                       and c["input_edge"] and c["output_edge"]
                       and len(c["blocking_keys"]) >= 4 and len(c["blackbox"]) >= 120 for c in cards), ""))
    checks.append(("no placeholder text anywhere (todo/tbd/lorem/placeholder/fixme)",
                   all(marker not in json.dumps(c).lower() for c in cards
                       for marker in _PLACEHOLDER_MARKERS), ""))
    checks.append(("governance stance on every card: public-records-only + no access-control evasion + "
                   "as-published person fields + review-on-conflict",
                   all(all(c["governance"].values()) for c in cards), ""))
    boi_cards = [c for c in cards if c["family"] == "fincen_boi"]
    checks.append(("restricted source is modeled as DENY (FinCEN BOI gate present; policy says RESTRICTED and "
                   "the gate blackbox refuses scraping)",
                   bool(boi_cards) and any("RESTRICTED" in c["source_policy"] for c in boi_cards)
                   and any("refused" in c["blackbox"] for c in boi_cards), ""))

    first = build(write=True)
    first_bytes = CARDS_PATH.read_bytes()
    second = build(write=True)
    checks.append(("deterministic: double build byte-identical; manifest count computed",
                   first_bytes == CARDS_PATH.read_bytes() and first["cards"] == second["cards"]
                   and json.loads(MANIFEST_PATH.read_text())["card_count"] == len(cards), ""))

    ok = all(passed for _n, passed, _d in checks)
    families = len({c['family'] for c in cards})
    print(f"{'PASS' if ok else 'FAIL'} - corporate_records_scraping_primitive_pack: {len(cards)} governed "
          f"corporate-records scraping primitives across {families} source families (EDGAR, Companies House, "
          f"OpenCorporates, GLEIF, state SoS, IRS 990, SAM.gov, UCC, dockets, USPTO, BOI-gate, municipal, "
          f"cross-source spine); policy-gated, candidate-only. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the corporate-records scraping primitive pack.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.build:
        print(json.dumps(build(write=True), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
