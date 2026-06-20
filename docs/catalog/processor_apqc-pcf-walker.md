# APQC Process Classification Framework (PCF) walker

*processor* · `processor/apqc-pcf-walker` · v0.1.0 · experimental

Walks the APQC Process Classification Framework (Cross-Industry
v7.4.0+, ~1,800 processes across 13 categories) and yields one
structured "knowledge node" per process. Each node carries:

 - pcf_id: e.g., "8.2.1.1.1"
 - category: 1.0 (Vision & Strategy), 2.0 (Develop Products), ...
   up to 13.0 (Manage Enterprise Risk & Compliance)
 - process_name
 - parent_path (full breadcrumb)
 - level (1-5 — category / process group / process / activity / task)
 - description
 - typical_inputs (when documented)
 - typical_outputs (when documented)
 - related_pcf_ids

Designed to feed `harness/draft-manifest-author` so each BPO
process becomes a candidate AI-pipeline manifest (BPO process →
AI-assisted pipeline; e.g., PCF 8.2.1.1.1 "Establish data
governance policies" → harness/data-governance-policy-drafter +
pipeline/data-governance-policy-pipeline).

Source: APQC publishes the PCF under a permissive academic-use
license. For commercial use, an APQC subscription is required to
redistribute the framework text verbatim; this walker preserves
PCF IDs (which are factual) and references back to APQC's source
rather than redistributing verbatim descriptions. Distill +
paraphrase + cite, not republish.

Industry-specific PCF variants (Banking, Pharma, Retail, Utilities,
etc.) follow the same shape; declare which variant at walk time.

| axis | value |
|---|---|
| industry | cross_industry, software |
| capability | retrieval, extraction |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



