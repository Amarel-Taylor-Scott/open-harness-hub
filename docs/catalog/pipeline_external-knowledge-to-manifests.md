# External knowledge tree → OHH draft manifests (factory pipeline)

*pipeline* · `pipeline/external-knowledge-to-manifests` · v0.1.0 · experimental

The factory pipeline. Walks an external knowledge tree (Wikipedia
category, US Code title, APQC PCF category, NIST framework
chapter, regulatory corpus, paper-list, etc.), proposes draft
catalog manifests per node, validates them, and writes
curator-ready drafts to `catalog/_inbox/`.

This pipeline implements the "iteratively build a massive index"
idea: point it at a knowledge tree and it produces draft
manifests at scale, each one schema-validated, each one
attribution-preserving, each one held back for curator review
per `catalog/_inbox/` convention (AGENTS.md hard rule).

Use cases:
 - Wikipedia: bulk-ingest a category subtree (e.g., "Category:Money
   laundering typologies" → knowledge-pack + classifier rules)
 - US Code: ingest a title (e.g., Title 31 — Money & Finance →
   N knowledge-pack entries + N GREP rule-packs for detection)
 - APQC PCF: ingest a category (e.g., Category 8 — Manage Information
   Technology → N harnesses + N pipelines for BPO → AI-assisted)
 - NIST publications: ingest 800-series (e.g., NIST SP 800-53 controls
   → N knowledge-pack entries + N rubrics + N rule-packs)
 - Regulatory corpora: EU directives, FDA guidance, OECD frameworks
 - Academic paper-lists: arXiv categories, ICLR / NeurIPS proceedings
   → N pattern manifests
 - Product Hunt: top-N launches per period → N dataset entries

Pipeline shape:
 1. WALK external source (yields nodes)
 2. PARALLEL: per node, DRAFT manifests (model_targets-bound)
 3. VALIDATE each draft against its schema
 4. SELF-REVISE on validation failure (max N attempts)
 5. WRITE successful drafts to `catalog/_inbox/{type}/{slug}.yaml`
 6. AUDIT trace + walk-stats + draft-quality distribution

Output:
 - drafts_emitted: list of (path, type, slug, rubric_score)
 - drafts_failed: list of (node, errors, attempts)
 - vocab_change_requests: aggregated VOCAB-CHANGE-NEEDED flags
 - walk_stats: nodes_walked, nodes_drafted, drafts_per_node_mean
 - audit_trace

| axis | value |
|---|---|
| industry | software, software.docs, ai, cross_industry |
| capability | generation, extraction, verification, classification, reasoning |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given an external knowledge source (walker_kind + walker_inputs),
walk it, propose OHH draft manifests per node, validate, self-
revise on failure, and write curator-ready drafts to
`catalog/_inbox/`.

**pipeline_kind:** `ingest`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `walk` | processor | `processor/wikipedia-category-walker` | - |
| 2 | `rag_manifest_shapes` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 3 | `draft` | harness | `harness/draft-manifest-author` | - |
| 4 | `emit_drafts` | processor | `processor/draft-manifest-yaml-emitter` | - |
| 5 | `grade` | processor | `processor/llm-judge` | - |
| 6 | `audit` | processor | `processor/audit-trace-emitter` | - |

