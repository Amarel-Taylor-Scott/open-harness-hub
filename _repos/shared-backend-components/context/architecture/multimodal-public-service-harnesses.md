# Multimodal Public-Service Harnesses

Disaster assistance, water quality, and food quality are good examples of
pipeline primitives that are not solved by a single out-of-box LLM call.

They combine:

- official-source retrieval;
- forms, images, tables, maps, and time-series data;
- policy and eligibility logic;
- model routing across text, vision, geospatial, and tabular specialists;
- freshness and provenance checks;
- human review for high-impact outcomes.

## Example Harness Families

Disaster assistance intake should reconcile applicant statements, damage
photos, geospatial incident boundaries, eligibility rules, duplicate claims,
and missing evidence.

Water quality triage should combine lab results, sampling plans, chain of
custody, maps, historical trends, advisory thresholds, and public notice text.

Food quality and safety triage should combine product labels, lot codes,
temperature logs, inspection notes, supplier records, complaint narratives, and
recall or hold decisions.

## Why Multi-Model

The useful unit is not "ask a large model." It is a harness that decides:

- which evidence needs OCR, vision, geospatial, tabular, or text handling;
- which facts must come from official or archived sources;
- which claims need deterministic checks;
- which model can perform each step cheaply enough;
- when confidence or impact requires human review.

## Generated Object Opportunity

Each harness run can emit many reusable primitives:

- evidence normalization steps;
- eligibility or threshold question sets;
- source-governed facts;
- review-ticket rules;
- label and dimension assignments;
- dedupe patterns;
- index records;
- cost and model-route traces.

That makes these domains strong sources for the million-object registry.
