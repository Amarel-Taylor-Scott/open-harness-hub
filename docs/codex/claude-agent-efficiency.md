# Claude Agent Efficiency Plan

This guide is for using Claude 4.x/4.8/4.7-style coding agents to reorganize OpenHubForAI without falling into slow static-site or one-file-per-row loops.

## The Problem

The repo has two different scales:

- public component definitions: curated YAML files that explain reusable tools, packs, pipelines, schemas, and docs;
- database-backed component candidates: high-volume rows that should live in JSONL staging, Postgres, pgvector, and search indexes.

Agents often waste time by treating every generated component candidate as a public static definition, then running full validation and full page rebuilds after every small change. That path will not reach one million components.

## Operating Mode For Claude

Claude should act as an orchestration and refactoring agent, not only as a file generator.

Preferred work:

- improve factories that emit row families;
- improve ID stability and hash discipline;
- add load audits and promotion readiness checks;
- add reusable source-surface and worker contracts;
- add compact knowledge packs and seed JSONL;
- add docs that prevent future agents from repeating slow paths;
- validate focused changes first.

Avoid:

- broad full rebuilds as the first action;
- thousands of static files for generated candidates;
- vague strategy docs without executable scripts or component definitions;
- reintroducing unclear names for components and subcomponents;
- publishing raw source data, PII, secrets, or `_reference/` content.

## High-Power Batch Shape

When asked to push hard, Claude should choose a bottleneck and close it end to end:

1. identify the row-family or promotion bottleneck;
2. fix the generator, planner, or audit script;
3. regenerate one 1K batch locally if the script is side-effect free;
4. run promotion/readiness checks;
5. update one doc and one component definition or pipeline;
6. run focused validation, component ID index update, selected catalog render, and global ref check;
7. run full validation only when explicitly requested or when changing shared schemas.

The goal is not to produce a pretty diff. The goal is to make the next 1,000 to 5,000 rows faster, safer, and less lossy.

## Current Critical Lessons

The model-ops daily run exposed a concrete scale issue: long generated IDs were truncated and collapsed during merge. The fix is to add stable hash suffixes to generated seed IDs, normalized object IDs, and index record IDs.

This pattern should apply everywhere:

- generated IDs must be deterministic;
- truncation must include hash suffixes;
- merge audits should report duplicates by row family;
- promotion readiness should fail structurally when index rows disappear;
- documentation should name the failure so future agents do not repeat it.

## Fast Validation Contract

For ordinary edits:

```bash
python3 scripts/validate.py <changed catalog paths>
python3 scripts/build_component_id_index.py --update <changed catalog paths>
python3 scripts/build_catalog_pages.py --paths <changed catalog paths> --update-index
python3 scripts/validate.py --global-ref-check <changed pipeline paths>
python3 scripts/build_component_id_index.py --check-fresh
```

For release gates:

```bash
python3 scripts/validate.py
python3 scripts/build_catalog_pages.py
```

If full catalog rendering becomes the slowest step, improve incremental rendering and report selected-page results for daily work.

## What Claude Should Optimize Next

The next best efficiency gains are:

- an index-coverage repair planner that emits missing keyword, vector, graph, facet, and quality index records for structurally incomplete rows;
- a duplicate-collapse report grouped by ID source, hash suffix, and row family;
- a daily closeout command that runs generation, load audit, promotion readiness, selected validation, and selected docs in one command;
- a Postgres smoke command approval flow with cryptographic signatures instead of unsigned local examples;
- a compact dashboard JSON that separates generated, staged, load-ready, promotion-ready, committed, and vector-ready counts.

These are more valuable than adding another batch of static component files.
