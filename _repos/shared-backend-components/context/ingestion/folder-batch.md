# Local Folder Batch Ingestion (a mixed-extension folder as ONE source)

**Purpose.** Treat a folder of mixed-extension files (a drag-and-drop upload, an export dump) as ONE source.
The adapter does not parse anything itself — it **classifies** each file by extension and **routes** it to the
correct EXISTING source adapter via the existing `normalize()` port, emits a **folder manifest** source
artifact + the per-file governed artifacts, and allows **partial failure**: a file with no available parser
(or one that raises) is an honest non-consumable/error entry in the manifest — it never aborts the batch and
never produces a faked claim.

**Owner.** `_repos/baltor/backend/src/baltor/adapters/source/folder_batch.py` (`LocalFolderBatchAdapter`, satisfies the existing
`scripts.ingest.source_adapters.SourceAdapter` Protocol). **Routing.**
`scripts.ingest.source_adapters.normalize()` for json/csv/html/pdf; the sibling `MarkdownFolderAdapter` for
markdown. **Registry.** `architecture/contract_registry.json#source_types` (`folder`). **Parser provider.**
`folder_batch_router` (no parser of its own; it delegates).

## Input

Either an in-memory dict `{relpath: bytes|str}` (offline fixture) or a filesystem path (real connector behind
the same port). Files are processed in sorted relpath order for determinism.

## Extension routing

| Extension | Routed to | Result |
|---|---|---|
| `.json` | `normalize("json", …)` | consumable (atomic_fact / narrative_allegation) |
| `.csv` | `normalize("csv", …)` | consumable |
| `.md` / `.markdown` | `MarkdownFolderAdapter` (single-note) | consumable (note prose held out) |
| `.html` / `.htm` | `normalize("html", …)` | **non-consumable** (parser is a cataloged candidate) |
| `.pdf` | `normalize("pdf", …)` | **non-consumable** (Docling parser is a cataloged candidate) |
| `.txt` | (no batch parser) | **non-consumable**, raw stored as a `source_record` |
| anything else | `unknown` | **non-consumable**, raw stored |

## What the batch produces

- **`folder_manifest`** source artifact (handle `…#folder.manifest`): `file_count` + per-file entries, each
  with `relpath`, classified `source_type`, `content_hash`, `idempotency_key`, `file_source_id`, `consumable`,
  and a `reason` for non-consumable/error files.
- **per-file artifacts** produced by each routed adapter, namespaced under `<sid>/file/<relpath>` so handles
  stay disjoint.
- a **batch summary**: `{file_count, consumable, non_consumable, errors}`.

## Governance (enforced)

- **Honest partial failure.** A `.pdf`/`.html`/`.txt`/unknown file is a non-consumable manifest entry with an
  explicit `reason` and the raw payload stored as a `source_record` — never a faked parse. One bad file (even
  one that raises mid-route) becomes an `error` entry; the batch is NOT aborted.
- **The batch is consumable as a SOURCE** (the manifest exists) even when some files are not consumable.
- **Idempotency** per file = `tenant_id + relpath + content_hash`. Re-running the same folder is byte-identical
  (deterministic; content-addressed; time injected via `now=`). Changed file content → a different per-file
  idempotency key (others unchanged), so changes are detectable.
- **Tenant scope preserved.** Routed per-file artifacts carry the batch's scope (`tenant_private` stays
  private; no `global_public` leak).

## Commands

```
PYTHONPATH=. python3 scripts/check_ingest_folder_batch.py --self-test
PYTHONPATH=. python3 -c "from src.baltor.adapters.source.folder_batch import LocalFolderBatchAdapter as A; \
  import json; print(json.dumps(A().ingest('demo-data/folder-batch', tenant_id='acme', source_id='upload1', now=0)['summary'], indent=2))"
```

## Fixture

`demo-data/folder-batch/` — `facts.json`, `rows.csv`, `readme.md` (consumable) plus `scan.pdf` (parser
unavailable) and `notes.txt` (no batch parser) to prove honest non-consumable routing without aborting.

## Boundaries

INGESTION ONLY. It reuses the existing `normalize()` port and the markdown adapter; it introduces no second
runtime/bus/parser-framework, writes no served facts, and does not edit
`scripts/ingest/source_adapters.py`. Registration of the `folder` source type (adapter wiring +
`contract_registry.json#source_types`) is applied by the integrating agent.
