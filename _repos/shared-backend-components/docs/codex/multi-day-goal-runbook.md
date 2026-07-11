# Multi-Day /goal Runbook

Use this runbook when running Codex repeatedly or continuously against the million-component goal.

## Daily Start

1. Read `.codex/prompts/goal.md`.
2. Read `AGENTS.md`.
3. Run a quick repository check:

   ```bash
   git status --short
   find catalog -name '*.yaml' | wc -l
   ```

4. Pick one factory area and keep the batch coherent.

## Daily Production Contract

Every goal day should attempt to produce:

- 1,000 to 5,000 database-backed component candidates;
- 5 to 25 preconfigured showcase pipelines;
- a load or audit package proving the generated rows are internally consistent;
- a short note in docs or generated summaries explaining source surfaces used, counts produced, review queues opened, and what remains staged versus committed.

The minimum acceptable daily production run is:

```bash
python3 -m scripts.factory.daily_thousand_component_seeds \
  --output-dir dist/daily-component-batch/YYYY-MM-DD \
  --target-count 1000 \
  --matrix core
```

When healthy, raise `--target-count` to `2500` or `5000`, or run multiple partitions with different matrices. After generating two or more partitions, merge and audit them before treating them as load-ready:

```bash
python3 -m scripts.db.daily_partition_load_audit \
  --partition dist/daily-component-batch/YYYY-MM-DD \
  --partition dist/daily-component-batch/YYYY-MM-DD-extra \
  --output-dir dist/daily-component-batch-load-audit/YYYY-MM-DD \
  --run-id daily-YYYY-MM-DD
```

Showcase pipelines are required because the product is not only a database. They prove how generated components become usable systems. Each daily pipeline set should cover specific use cases, for example cheap social moderation, AML alert review, water-quality public notice review, trades work-order triage, public fact refresh propagation, cyber alert quality, public procurement review, or content creation approval.

When a user supplies a technical theory, postmortem, or architecture critique, extract reusable components instead of storing it only as prose. Identify pre-LLM, LLM-routing, post-LLM, evaluation, cost, deployment, and audit subcomponents, then add a defensive showcase pipeline when the pattern is safety or security related.

## Factory Areas

Rotate through:

- occupation and job-description work atoms;
- procedure/checklist/question components;
- public fact versioning and archive-backed RAG;
- source surface expansion;
- workflow graph imports;
- tools and containerized workers;
- dedupe, entity resolution, and indexing;
- hosting/deployment blueprints;
- rubrics and benchmarks;
- cost/pricing records.

## Roadblock Navigation

Do not stop because one source surface, one dependency, one validation path, or one generation route is slow. Switch to the next useful path while keeping the proof boundary honest.

Use this fallback order:

1. Switch source-surface matrix: `core`, `expanded`, then `combined`.
2. Reduce one large run into multiple smaller partitions and merge them later.
3. Generate showcase pipeline templates while ingestion is blocked.
4. Generate rubrics, benchmark cases, review questions, or deployment blueprints for existing candidates.
5. Run load-audit, dedupe, promotion, CDC, or index-delta planners on existing partitions.
6. If external network or credentialed sources are blocked, use synthetic source-surface seeds and document that live source ingestion is pending.
7. If validation is slow, run focused validation first, then full validation before closeout.

Only stop when there is a real safety, privacy, licensing, or destructive-action concern that cannot be routed to review.

## Batch Contract

Each multi-day batch should add or improve:

- one source surface or architecture doc;
- one normalized schema or data pack;
- one extraction, dedupe, entity, archive, or indexing tool;
- one pipeline that uses it;
- validation and generated docs.

## Checkpoints

After each batch:

```bash
python3 scripts/validate.py <changed component-definition paths>
python3 scripts/build_catalog_pages.py --paths <changed component-definition paths> --update-index
find catalog -name '*.yaml' | wc -l
```

Use `python3 scripts/validate.py --global-ref-check <changed component-definition paths>` when a changed component definition adds or rewires component references and you need selected-path validation with full catalog reference checking.

Keep the component-id cache warm for fast global ref checks:

```bash
python3 scripts/build_component_id_index.py --update <changed catalog yaml paths>
python3 scripts/build_component_id_index.py --check-fresh
```

Run the full forms only for release snapshots, broad schema/vocabulary changes, or when generated catalog state may be stale:

```bash
python3 scripts/validate.py
python3 scripts/build_catalog_pages.py
```

Record:

- public component definition count;
- generated candidate row count;
- staged unique row count after dedupe;
- committed Postgres row count when available;
- showcase pipeline count;
- new factories;
- failed validations fixed;
- next source surfaces;
- any manual review queues.

## Worker Smoke Test

When touching factory-worker code or component definitions, run:

```bash
python3 -m scripts.factory.object_factory_workers --self-test
```

This proves the local no-key baseline still converts HTML/text into Markdown, extracts candidate components, screens sensitive data, and performs deterministic polish/verification. Passing this smoke test does not prove hosted queues, browser containers, PDF/OCR, or external model routing work; those need separate deployment tests.

## Long-Running Discipline

- Do not generate thousands of repository files manually in one turn.
- Prefer one factory that can later generate thousands of JSONL component rows.
- Keep high-volume generated atoms in knowledge-pack data files.
- Add schemas before adding large data.
- Add dedupe before adding bulk ingest.
- Add archive/versioning before volatile facts.
- Add review queues before risky domains.
- Keep docs current as the architecture changes.

## Stop Conditions

Stop and report when:

- validation fails and cannot be fixed quickly;
- a source license is unclear;
- ingestion might include PII, PHI, secrets, or proprietary content;
- a source requires credentials or explicit authorization;
- a factory would create a large, noisy, unreviewed dump.
