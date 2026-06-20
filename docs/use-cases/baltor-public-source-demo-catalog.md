# Baltor Public Source Demo Catalog

Date: 2026-06-04

This catalog gives Baltor a broader demo surface than a single dataset. It
identifies public sources that can show different parts of the full context
pipeline:

```text
source records
-> normalized context objects
-> CodeGraph / DocGraph / OrgGraph links
-> safe claims and blocked claims
-> policy caveats
-> context packs
-> context receipts
```

The catalog lives at:

```text
data/baltor-demo-source-catalog.json
```

The builder is:

```bash
python3 scripts/demo_public_source_catalog.py
```

Output goes to:

```text
site/baltor-demos/public-source-catalog/
```

Emitted files:

```text
source-records.json
context-objects.json
demo-matrix.json
context-pack.json
context-receipt.json
README.md
```

## Current Sources

| Source | Shows | Best Pack |
|---|---|---|
| CFPB Consumer Complaint Database | Public complaint metadata, aggregate-only claims, narrative caveats, receipts | `customer_pack` |
| SEC EDGAR Submissions and XBRL APIs | Financial filings, DocGraph claims, filing freshness | `financial_risk_pack` |
| NIST National Vulnerability Database | CVE metadata, security claims, CodeGraph/asset joins | `security_triage_pack` |
| CISA Known Exploited Vulnerabilities Catalog | Known-exploited priority, patch urgency, security receipts | `security_triage_pack` |
| openFDA APIs and Downloads | Health public data, aggregate claims, clinical caveats | `clinical_summary_pack` |
| Data.gov Catalog API | Source discovery, metadata registry, dataset prioritization | `custom` |
| EPA ECHO | Facility/compliance public data, policy caveats | `compliance_pack` |
| GitHub Public Repository Contents API | RepoDirectory, CodeGraph, commit-scoped code pointers | `implementation_pack` |

## Why These Sources

The set intentionally spans different source shapes:

- public official datasets
- public APIs
- downloadable JSON feeds
- metadata catalogs
- public repositories
- high-caveat allegation/report sources
- security records that must be joined with local asset evidence

That makes it useful for demonstrating that Baltor is not a vector database or a
generic scraper. Baltor has to decide what kind of claims are safe, what claims
are blocked, what gets source handles, and what a context receipt must disclose.

## Demo Progression

Recommended sequence:

1. **CFPB**: demonstrate public corpus ingestion, aggregate-only claims, and
   narrative caveats.
2. **GitHub repo**: demonstrate CodeGraph, repo pointers, commit scoping, and
   implementation packs.
3. **NVD + CISA KEV**: demonstrate security verification, source precedence,
   and local asset joins.
4. **SEC EDGAR**: demonstrate DocGraph extraction from filings and freshness.
5. **openFDA**: demonstrate high-stakes caveats where reports do not prove
   causality.
6. **Data.gov**: demonstrate source discovery and source-prioritization.
7. **EPA ECHO**: demonstrate compliance packs with official-source caveats.

## Policy Rule

Every source entry carries:

```text
safe_claims
blocked_claims
caveats
pipeline_fit
demo_pack_type
```

This keeps demo generation tied to Baltor's context CI/CD model. A source is not
just fetched. It is normalized, scoped, policy-labeled, and released with a
receipt.

## Live Fetching

This catalog does not fetch live corpuses. That is deliberate. Live fetching
belongs in source-specific adapters with:

```text
pagination limits
response-size caps
rate-limit handling
terms review
content hashes
CDC/freshness checks
source-specific caveats
```

The catalog is the planning layer. Each source-specific adapter can later
graduate into a real Context Wizard once it has tests and receipts.
