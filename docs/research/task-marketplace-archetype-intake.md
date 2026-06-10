# Task Marketplace Archetype Intake

Hiring and task marketplaces are useful demand sensors because they expose recurring work people already pay humans to complete. The hub should mine them for reusable task archetypes, workflow steps, acceptance criteria, skill bundles, review questions, cost priors, and automation boundaries.

The default intake is metadata-only. Do not store raw listing text, worker or client identities, private messages, contact details, platform secrets, or any content that marketplace terms prohibit reusing.

## Intake Flow

```text
marketplace metadata or user export
-> source governance route
-> privacy and license gate
-> normalized task archetype
-> entity records for skills, sources, concepts
-> fuzzy dedupe cluster
-> keyword/facet/vector-ready index records
-> review tickets for privacy, license, and domain risk
```

## What To Keep

- task family;
- category;
- problem statement rewritten as an archetype;
- skill bundle;
- workflow steps;
- acceptance criteria;
- expected deliverables;
- cost and turnaround ranges when terms allow;
- automation opportunities;
- risk flags and review needs.

## What Not To Keep

- names, contact details, profile URLs, or private messages;
- raw listing text from platforms with restrictive terms;
- proprietary screening questions or internal hiring data;
- worker ratings tied to identifiable people;
- content from private or authenticated pages unless the user owns the export and permits processing.

## Primitive Value

These archetypes are useful because they reveal where out-of-box LLMs need harnesses:

- spreadsheet cleanup needs schema inference, fuzzy dedupe, and exception review;
- quote comparison needs structured extraction, contract-term flags, and privacy gating;
- research assistant tasks need source provenance and citation checks;
- customer support tasks need policy retrieval, escalation, and tone/risk review;
- creative tasks need style constraints, asset safety, and approval gates.

The resulting objects should remain candidates until license, privacy, and quality review are complete.
