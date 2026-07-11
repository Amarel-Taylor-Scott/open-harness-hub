# Component standards + templates

This is the **single source** for how the Baltor Context Engine builds new components and subcomponents. A
**standard** describes how the repo *actually* builds one of the canonical component patterns; a **template**
is a runnable scaffold that generates a new component already conforming to a standard. Together they turn the
factory's "daily target" of new components into standards-conformant code instead of hand-typed drift.

## The three pieces

| Piece | File | What it is |
|---|---|---|
| Standards | `_repos/shared-backend-components/architecture/standard_catalog.json` | Normative description of each canonical pattern (must-have / must-not-have / naming / location / contract / proof / doc / registry / security / observability rules) with REAL exemplar paths. |
| Templates | `_repos/shared-backend-components/architecture/template_catalog.json` | The catalog of generatable scaffolds; each maps to a standard. 7 are `active` (built under `templates/`); the rest are `candidate` (planned). |
| Generator | `_repos/shared-backend-components/scripts/generate_from_template.py` | Renders a template's `files/` tree (with `{{variable}}` substitution) into a new component + a content-addressed generation receipt + the next required commands. |

## Standard `status_enum`

`draft` -> `active` -> `enforced` -> `deprecated`. `enforced` standards (e.g. `standard.proof_script`,
`standard.tenant_isolation`) are non-negotiable for any new component; `active` ones are expected;
`draft` are emerging; `deprecated` should not be used for new work.

## Generate a component

```bash
# list everything the factory can generate
python3 _repos/shared-backend-components/scripts/generate_from_template.py --list

# generate a new proof (the canonical scaffold) — passes immediately
python3 _repos/shared-backend-components/scripts/generate_from_template.py --template proof.self_test \
  --proof_name corpus_freshness --title "Corpus freshness proof" \
  --owner _repos/shared-backend-components/scripts/runtime/consumption.py --subject_module scripts.runtime.consumption

# generate a new projection API route (a STUB whose proof FAILS until you wire serve())
python3 _repos/shared-backend-components/scripts/generate_from_template.py --template api.projection_route \
  --area corpus --route_path /api/corpus/serve --returns_contract CorpusResponse \
  --title "Corpus serve" --owner scripts/api_corpus_handler.py
```

The generator **refuses** (nonzero exit) on a missing required variable and **refuses to overwrite** an
existing file unless `--force`. Every run writes a receipt to
`.agent/template-generation/<gen-id>-<template-id>.json` (the id is content-addressed — the same inputs always
produce the same id, so a regenerate is detectable and never collapses during dedupe).

## What the generator emits

- **Implementation files** (`.py`, `.html`) start as **stubs with a failing TODO** — the generated proof
  FAILS until you implement the component. That is intentional: a generated-but-unbuilt component never reads
  as done.
- **Proof files** from `proof.self_test` are a complete, **passing** deterministic scaffold (temp dir,
  content-addressing, `--self-test`, exit 0/1) ready to extend with subject assertions.
- **Docs files** carry every required heading (see `template-authoring.md`).

## The 7 built templates

| Template | Standard | Generates |
|---|---|---|
| `ingestion.source_adapter` | `standard.source_adapter` | a governed `SourceAdapter` + proof + docs |
| `worker.command_handler` | `standard.durable_command` | an idempotent durable command handler + proof + docs |
| `api.projection_route` | `standard.api_projection` | a projection-only HTTP handler + proof + docs |
| `ui.projection_page` | `standard.ui_projection` | a projection-only web page + proof + docs |
| `provider.adapter` | `standard.provider_adapter` | a provider adapter behind a port + proof + docs |
| `proof.self_test` | `standard.proof_script` | the canonical deterministic proof scaffold |
| `docs.section_page` | `standard.docs_page` | a section doc page with all required headings |

The remaining `candidate` templates in the catalog (sync loop, claim loop, processor, contract schema,
artifact object, optimization candidate, reconciliation decision, watchtower task, tenant isolation guard,
review pack) are planned scaffolds; build them next (see the lane opportunity).

## Proofs (enforcement)

```bash
python3 _repos/shared-backend-components/scripts/check_standard_catalog.py --self-test     # standards well-formed + grounded in real paths
python3 _repos/shared-backend-components/scripts/check_template_catalog.py --self-test      # templates buildable; active paths exist
python3 _repos/shared-backend-components/scripts/check_template_generation.py --self-test   # the generator actually renders conformant scaffolds
```

These assert the canonical 25 pattern ids, that every standard's `examples` are real repo paths, that every
`active` template's `files/` sources exist, and that the generator refuses missing variables / refuses
overwrite / writes a content-addressed receipt / emits `--self-test` in generated proofs.

## See also

- `_repos/shared-backend-components/context/standards/template-authoring.md` — how to author a new template.
- `_repos/shared-backend-components/architecture/standard_catalog.json` / `_repos/shared-backend-components/architecture/template_catalog.json` — the catalogs themselves.
