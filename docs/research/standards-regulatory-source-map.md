# Standards and Regulatory Source Map

Standards, regulatory, and public enforcement sources are high-value inputs for the million-object registry because they contain structured procedures, controls, definitions, exceptions, deadlines, forms, evidence requirements, and review questions.

These sources should feed factories that produce:

- versioned facts;
- compliance checklists;
- procedure questions;
- evidence requirements;
- decision gates;
- rubric criteria;
- citation-aware RAG chunks;
- entity records for agencies, laws, standards, sections, controls, forms, and datasets.

## Priority Sources

The first wave should emphasize sources with stable identifiers, public access, strong economic value, and frequent downstream deployment:

- Federal Register and Regulations.gov for rules, proposed rules, notices, dockets, comments, and effective dates;
- NIST CSF, NVD, SP 800-series, and control catalogs for security and compliance primitives;
- openFDA and FDA guidance/enforcement surfaces for drugs, devices, food, recalls, labels, events, and inspections;
- OSHA data for inspections, citations, severe injuries, fatalities, and workplace safety requirements;
- SEC EDGAR for filings, issuer facts, disclosures, risk factors, XBRL facts, and corporate entity records;
- CMS, CDC, NIH, ClinicalTrials.gov, and PubMed for healthcare and public health facts;
- IRS, CFPB, FTC, FINRA, CFTC, and banking regulators for finance, consumer protection, and market conduct workflows;
- EPA, FAA, DOT, NHTSA, FCC, FERC, and PHMSA for infrastructure, transportation, communications, environment, and energy workflows;
- ISO, IEC, W3C, IETF, OWASP, MITRE, CIS, and OASIS for technical standards, controls, schemas, and implementation guidance.

## Extraction Targets

Each source should be normalized into a common extraction target:

- `source_record`: publisher, source URL, license, content hash, archive URL, retrieval time, and trust tier.
- `canonical_entity`: agency, regulation, standard, section, form, dataset, issuer, product, vulnerability, control, or concept.
- `versioned_fact`: fact with effective date, source date, archive date, supersession relation, and citation.
- `procedure_object`: question, checklist item, decision gate, evidence requirement, exception, deadline, or output template.
- `index_record`: keyword, vector, graph, facet, freshness, quality, and cost records.
- `review_ticket`: curator, legal, domain expert, safety, or publisher review queue entry.

## Factory Pattern

```text
source surface
-> source governance router
-> archive/version lookup
-> source-specific parser
-> entity linker
-> procedure/fact extractor
-> fuzzy dedupe clusterer
-> index record emitter
-> review queue
```

## Hosting Notes

Start with scheduled workers and cheap storage:

- Render worker or Cloud Run job for scans;
- Postgres for source records and canonical entities;
- object storage for raw snapshots and downloaded files;
- pgvector for first semantic index;
- BigQuery or ClickHouse later for large source telemetry and ranking jobs.

Do not put raw high-volume snapshots directly in Postgres. Store snapshots in object storage, keep hashes and canonical metadata in the database, and generate compact index records for search.
