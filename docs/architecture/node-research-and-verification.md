# Node Research and Verification

Detected graph nodes need a separate research layer. A node mention is not a
verified fact; it is a prompt to look for evidence. The implemented contract is:

```text
detected node
-> node.research.plan
-> configured public-record / OSINT / registry / search tools
-> evidence records
-> proposed edges
-> evidence scoring and verification tier
```

## Policy

The worker policy is intentionally split:

- Public business records, company websites, business addresses, official
  registries, public filings, DOI metadata, institution records, domain
  registration/DNS data, archived web pages, and public fact-check records can be
  planned and enriched when the relevant service/API is configured.
- Person, email, phone, username, and private-person enrichment requires
  `authorized=true` in the payload or `NODE_RESEARCH_AUTHORIZED=true`.
- Active reconnaissance tools require `active_recon_authorized=true` or
  `ACTIVE_RECON_AUTHORIZED=true`.
- Enrichment creates candidate evidence, not verified graph facts. Verification
  requires corroboration, primary sources, or analyst approval.

## Implemented Workers

| Worker | Purpose |
|---|---|
| `node.research.catalog` | Reports configured node-enrichment tools, supported node types, and authorization requirements. |
| `node.research.plan` | Creates research tasks for detected nodes and routes them by node type. |
| `node.research.enrich` | Runs configured tools for one node and returns evidence records plus proposed `ENRICHED_BY` edges. |
| `node.evidence.score` | Scores evidence into verification tiers without auto-merging candidates into facts. |

These are registered by `scripts/context_workers/workers/node_research.py`.

`node.research.plan` creates queued `node.research.enrich` task envelopes from
detected nodes. The deterministic context pipeline emits those envelopes through
`TaskResult.enqueue`, so Redis/K8s workers can process enrichment asynchronously
after the first pass completes.

```text
context.pipeline.pass
-> node.research.plan
-> TaskResult.enqueue[node.research.enrich]
-> Redis list ohh:context:jobs
-> node.research.enrich
-> Redis stream ohh:context:events
-> ledger/artifact records
```

## Verification Tiers

| Tier | Label | Meaning |
|---:|---|---|
| 0 | `detected` | Mentioned in uploaded content or extracted graph. |
| 1 | `enriched` | One configured tool produced candidate evidence. |
| 2 | `resolved` | Matched to a stable identifier. |
| 3 | `corroborated` | Supported by at least two independent useful sources. |
| 4 | `verified` | Supported by a primary/official source or analyst-approved evidence. |
| 5 | `contradicted` | Credible evidence conflicts. |
| 6 | `stale` | Evidence is too old for the fact type. |

## Tool Surface

The catalog covers OpenOSINT-style enrichment plus public-record and LLM-friendly
research tools:

- General OSINT/link analysis: OpenOSINT, SpiderFoot, OSINTBuddy, Maltego,
  Recon-ng, Aleph/OpenAleph.
- Company and public-record enrichment: OpenSanctions/yente,
  FollowTheMoney-compatible evidence, OpenCorporates, GLEIF, Companies House,
  SEC EDGAR, OpenOwnership BODS, ICIJ Offshore Leaks.
- Scholarly identifiers: OpenAlex, Crossref, ORCID, ROR.
- Username/email/phone enrichment: Sherlock, Maigret, Social Analyzer, Holehe,
  PhoneInfoga. These are authorization-gated.
- Domain/IP/cyber enrichment: Shodan, Censys, VirusTotal, AbuseIPDB,
  SecurityTrails, OpenCTI, MISP, MITRE ATT&CK STIX. Active CLI recon tools are
  separately gated.
- Location/media: Nominatim, GeoNames, Overpass, Mapillary, ExifTool,
  InVID-WeVerify.
- Claims and evidence preservation: Google Fact Check Tools, ClaimReview, Media
  Cloud, Hoaxy, ArchiveBox, Wayback, Hunchly.
- LLM-friendly research: Tavily, Exa, Firecrawl, Crawl4AI.
- Reconciliation: OpenRefine reconciliation, Wikidata, dedupe, Splink.

The worker reports `not_configured` for tools that need a missing URL, API key,
CLI, or module. This is intentional: the pipeline can compare readiness without
pretending every external system is installed.

## Example Task

```json
{
  "task": "node.research.plan",
  "run_id": "demo",
  "payload": {
    "nodes": [
      {"id": "n1", "label": "Acme Holdings Ltd.", "node_type": "company"},
      {"id": "n2", "label": "acme.example", "node_type": "domain"}
    ]
  }
}
```

For person/email/phone/username nodes:

```json
{
  "task": "node.research.enrich",
  "run_id": "authorized-demo",
  "payload": {
    "authorized": true,
    "node": {"node_id": "n9", "label": "example_user", "node_type": "username"}
  }
}
```

For active recon:

```json
{
  "task": "node.research.enrich",
  "run_id": "owned-domain-demo",
  "payload": {
    "active_recon_authorized": true,
    "node": {"node_id": "n10", "label": "example.com", "node_type": "domain"},
    "candidate_tools": ["amass", "subfinder", "dnsx"]
  }
}
```

## Graph Edge Policy

Use weak edges until evidence is strong:

- `MENTIONED`
- `POSSIBLY_SAME_AS`
- `ENRICHED_BY`
- `RESOLVED_AS`
- `CORROBORATED_BY`
- `CONTRADICTED_BY`
- `VERIFIED_BY_ANALYST`

Do not create `SAME_PERSON`, `OFFICER_OF`, `CONTROLS`, or similar high-impact
edges from a single OSINT hit. Store the evidence, score it, and require a
primary source, corroboration, or review before promotion.
