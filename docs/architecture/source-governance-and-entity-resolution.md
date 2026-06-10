# Source Governance and Entity Resolution

The million-object platform needs a normalization layer between raw sources and published primitives. Without it, the catalog becomes a pile of duplicate strings, stale facts, mismatched names, and weak provenance.

This layer has four jobs:

1. standardize source records;
2. extract and link entities;
3. deduplicate near-equivalent objects;
4. organize candidates into stable collections, versions, and graph edges.

## Source Tiers

Source surfaces should be classified before ingestion:

- **Verified publisher**: government agency, standards body, package registry, signed organization, or domain-verified publisher.
- **Canonical public dataset**: O*NET, ESCO, BLS ORS, SEC EDGAR, NVD, OpenAlex, PubMed, Federal Register, data.gov, data.europa.eu.
- **Community registry**: GitHub, package registries, MCP registries, workflow repositories, model hubs.
- **Volatile web source**: pages that need archive capture, hash, diff, and freshness checks.
- **User-private source**: tenant files, SOPs, policies, job descriptions, internal procedures.
- **Generated candidate**: model-extracted object pending validation.

Each tier has different trust, license, privacy, refresh, and review requirements.

## Standard Record Types

Every ingest pipeline should normalize into these records before indexing:

- `source_record`: raw or semi-raw source metadata, URL, license, timestamp, hash, publisher, and trust tier.
- `extracted_object`: candidate task, question, fact, tool, checklist, policy, workflow node, or primitive.
- `entity_mention`: named person, org, product, law, dataset, model, tool, role, place, code, registry id, or concept.
- `canonical_entity`: deduplicated entity with aliases, identifiers, provenance, and confidence.
- `dedupe_cluster`: group of near-equivalent records with canonical representative and merge policy.
- `index_record`: keyword, vector, graph, quality, freshness, and cost records derived from a source or object.
- `review_ticket`: reason an object needs curator, domain expert, safety, legal, or publisher review.

## Deduplication Strategy

Use layered dedupe rather than one model call:

1. exact IDs, URLs, hashes, registry identifiers, and canonical slugs;
2. normalized strings, aliases, stemming, acronym expansion, and language tags;
3. fuzzy matching with trigram, token sort ratio, Jaro-Winkler, and edit distance;
4. SimHash or MinHash for near-duplicate text;
5. vector similarity for semantic overlap;
6. entity graph overlap for same subject, source, and dependencies;
7. LLM or human adjudication only for high-value uncertain clusters.

The output should preserve provenance. Dedupe should not erase source history; it should link records and choose a canonical view.

## Entity Recognition

Entity resolution should cover:

- organizations, agencies, standards bodies, publishers, vendors, and projects;
- laws, regulations, advisories, sections, forms, and policy names;
- job titles, occupations, SOC/ISCO/O*NET/ESCO identifiers;
- software packages, APIs, tools, models, runtimes, containers, and cloud services;
- datasets, papers, authors, DOIs, CVEs, CWEs, MITRE techniques, sanctions ids;
- places, jurisdictions, currencies, units, dates, effective periods, and version labels.

Entities become graph nodes that connect otherwise separate objects. For example, “AML analyst,” “O*NET occupation,” “FinCEN advisory,” “transaction monitoring alert,” and “SAR-style narrative draft” should be searchable as linked concepts.

## Organization

Objects should be organized by multiple axes:

- source surface;
- domain and subdomain;
- component type;
- work atom type;
- entity subject;
- jurisdiction;
- trust tier;
- freshness;
- deployment target;
- cost profile;
- quality/eval status;
- popularity and usage.

This supports search modes beyond keyword and vector search: graph traversal, faceted browsing, dependency exploration, source-limited retrieval, date-valid retrieval, and “show me the cheapest deployable version.”

## Minimum Metadata

Every generated object should carry:

- stable `object_id`;
- `source_record_id`;
- `object_type`;
- `canonical_entity_ids`;
- `source_url` and optional archive URL;
- `publisher`;
- `license`;
- `trust_tier`;
- `privacy_boundary`;
- `created_at`, `retrieved_at`, and effective dates when relevant;
- `content_hash`;
- `dedupe_cluster_id`;
- `embedding_model`;
- `quality_status`;
- `review_status`;
- `supersedes` or `superseded_by` when applicable.

## Operational Principle

At small scale, this can run in Postgres with pgvector, JSONB, trigram indexes, and background workers. At larger scale, split keyword search, vector search, graph traversal, and analytics into specialized services, but keep the canonical provenance record in Postgres or another transactional source of truth.
