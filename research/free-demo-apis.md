# Free public API endpoints for the non-commercial Baltor demo

> **Provenance:** verification workflow `wsxzk600t` (web-confirmed), 2026-06-04. These emulate
> Baltor's "Source Systems" with **real authoritative data on free / no-/low-auth endpoints**,
> so a full ingest → verify → freshness → serve demo runs without paid credentials. Wire each
> behind the proven `scripts/ingest/sanctions_feed_live.py` pattern (fetch via `HttpFetcher` →
> parse → lineage with content-hash → `verified_context_flow.run`), with an offline
> `CannedFetcher` self-test + a `--live` flag. **Already wired & proven:** OFAC SDN
> (`sanctions_feed_live.py`).

## Tier 1 — no auth, live now (wire first)

| # | Source | Format | Baltor source role | Gotcha |
|---|---|---|---|---|
| 1 | **UN Security Council Consolidated Sanctions List** | XML | tier-1 sanctions corpus; `dateGenerated` = freshness | Follow the 302 → short-lived Azure SAS URL with `curl -L`; never cache the signed URL. |
| 2 | **GLEIF LEI API v1** | JSON | canonical entity-resolution spine (3.3M+ legal entities, parent/child); CC0-style | URL-encode `page%5Bsize%5D`. This is your `canonical_entity` backbone. |
| 3 | **Federal Register API v1** | JSON | authoritative regulatory documents; `publication_date`/`effective_on` freshness | No key. |
| 4 | **eCFR Versioner API** | JSON | codified CFR w/ per-Title "amended on / up to date as of" | **The ideal freshness/version-check showpiece.** No key. |
| 5 | **WHO GHO OData** | JSON | authoritative international health indicators; clean structured corpus | Substitute for the unverifiable Codex MRL API. |

## Tier 2 — free key, wire second (one `api.data.gov` key covers most)

| # | Source | Auth | Baltor source role | Gotcha |
|---|---|---|---|---|
| 6 | **CSL API (incl. BIS Entity List)** | free Trade.gov key | THE practical free Entity List feed; `fuzzy_name` powers verify/match | — |
| 7 | **SEC EDGAR** | no key | financial filings + CIK entity linking | **Must** send a real `User-Agent` with contact email; ≤10 req/s; zero-pad CIK to 10. |
| 8 | **CourtListener v4** | free token (recommended) | case-law/judicial layer beyond sanctions+regs | — |
| 9 | **GovInfo + Regulations.gov** | one `api.data.gov` key | broad primary-law corpus + docket/comment layer | `DEMO_KEY` ~30 req/hr — register a key. |
| 10 | **UK Companies House** | free key (HTTP Basic, key-as-username) | real free corporate-registry source (OpenCorporates replacement for UK) | — |

## Use the bulk file, not the hosted API

- **OpenSanctions** — hosted API is now paid (401). Use the free **CC-BY-NC bulk JSON/CSV/FtM** at `data.opensanctions.org` for the non-commercial demo (great cross-list, entity-resolved corroboration layer).
- **EU FSF consolidated list** — works with the published public `?token=` param (not a personal secret) + a browser-ish UA.

## Do NOT wire (verified unusable for a free demo)

- **OpenCorporates** — now 401/paid-gated → use UK Companies House + GLEIF instead.
- **FAO/WHO Codex Alimentarius MRL** — no programmatic API (HTML-only) → substitute WHO GHO.
- **data.gov legacy CKAN** — retired 2026 → use the GSA v3 Catalog API (don't hard-code the host).
- **CFPB Consumer Complaints** — usable but rate-limits this environment, and `format=json` **ignores `size`** (returns a ~39MB dump that trips guards). Use the size-respecting ES-shape response (`hits.hits[]._source`) + a browser-like UA, and keep it Tier 3.

## Suggested demo spine

**UN sanctions + CSL/BIS + EU FSF** (sanctions corpus) → **GLEIF + Companies House + EDGAR-CIK**
(entity resolution) → **eCFR Versioner** (the freshness/version-check showpiece). That triad
demonstrates ingest, entity linking, and governed freshness — Baltor's core thesis — entirely
on free, authoritative, no-/low-auth sources.
