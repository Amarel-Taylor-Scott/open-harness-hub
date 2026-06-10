# Cross-Domain Use Case Seed Surfaces

The registry needs broad seed surfaces that can generate many practical
pipelines without binding the taxonomy to one industry. This seed set focuses
on repeatable work where users ask for pipelines around laws, geography,
moderation, creation, research, and competitive analysis.

## Included Surfaces

- banking operations and bank-law monitoring;
- federal, state, local, and geography-specific law tracking;
- content moderation and trust-and-safety review;
- content creation, creative generation, and brainstorming support;
- competition and market comparison;
- geographic analysis for rules, programs, facilities, and local facts.
- trades such as electrical, plumbing, HVAC, construction, field service, and
  permitting workflows;
- oil and gas workflows such as pipeline integrity, lease operations,
  production reporting, safety procedures, and environmental monitoring;
- veterinary and animal hospital workflows such as intake triage, discharge
  instructions, lab review, controlled medication handling, and care-plan
  checklists.

Insurance-related pipelines are intentionally out of scope for this seed set.

## Factory Treatment

Each seed should be normalized into candidate primitives with:

1. source governance and license boundary;
2. task family, jurisdiction, modality, and risk tier labels;
3. entity recognition for agencies, places, laws, platforms, and competitors;
4. fuzzy dedupe against existing primitives;
5. keyword, vector, graph, facet, freshness, and quality index records;
6. review tickets for high-impact, legal, moderation, or public-facing claims.

These seeds become inputs to the larger object factory, not final authority.
Authoritative facts still need verified publishers, grounded sources, signed
knowledge objects, or expert review before deployment into high-risk pipelines.

## Hierarchy Rule

Do not create a new top-level capability or modality every time a new vertical
appears. Use flexible label paths and dimensions for vertical specificity:

- `vertical.trades.*`
- `vertical.energy.oil_gas.*`
- `vertical.veterinary.animal_hospital.*`
- `jurisdiction.*`
- `workflow.*`
- `risk.*`
- `deployment.*`

Core capability and modality values should describe broad behavior; labels and
dimensions describe the domain, jurisdiction, process, and deployment context.
