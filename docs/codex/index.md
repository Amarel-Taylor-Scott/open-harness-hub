# Codex Operating Guide

This folder gives Codex sessions a stable operating model for scaling Open Harness Hub toward more than one million reusable AI primitives, procedure objects, facts, tools, and pipeline components.

Start with:

- **[Master goal](master-goal.md) — the single canonical long-horizon program.
  Read this first; it reconciles and supersedes the goal docs below.**
- [Object factory workflow](object-factory-workflow.md)
- [Quality gates](quality-gates.md)
- [Speed guardrails](speed-guardrails.md)
- [Billion component goal](billion-component-goal.md) (tiering + vectorization detail)
- [Million object goal](million-object-goal.md) (superseded; history only)

## Working Principle

Every expansion session should create durable catalog value, not only brainstorm. Prefer small validated batches that add source surfaces, extraction patterns, tools, pipelines, rubrics, and generated docs.

The default output of a Codex expansion turn should be:

1. new or improved documentation;
2. catalog manifests that validate;
3. database-ready JSONL rows, load plans, index deltas, or promotion/vector audits when doing high-volume work;
4. selected catalog pages rebuilt for changed public definitions;
5. a short summary of what changed and what still needs scaling.

Full validation and full catalog page rebuilds are release gates. Use focused validation and selected page rendering for normal daily progress.

## Scale Target

The platform target is at least 1,000,000 indexed objects across:

- tools;
- pipelines;
- harnesses;
- rule packs;
- knowledge packs;
- procedure objects;
- review questions;
- checklist items;
- versioned facts;
- occupation work atoms;
- source surfaces;
- datasets;
- rubrics;
- benchmarks;
- deployment blueprints.

Most objects should be produced by repeatable factories from trusted sources, then deduplicated, scored, embedded, reviewed, versioned, and published.
