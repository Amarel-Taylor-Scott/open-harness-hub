# Ingestion contracts, ports, and the connector catalog

This is the ingestion boundary of the Baltor Context Engine: the **only** place a raw upstream source becomes a
governed object. It does not add a second runtime, bus, worker, artifact ledger, LLM gateway, parser framework,
or consumption service — it formalizes the contracts and ports around the existing `SourceAdapter` seam
(`scripts/ingest/source_adapters.py` + `normalize()`).

## The one rule

**No raw source becomes truth.** Every fetched object is turned into a **SourceArtifact** carrying its full
governance metadata (`tenant_id`, `source_id`, `source_version`, `source_handle`, `content_hash`, `scope`,
`authority`, `lineage`, `security`) and **nothing served**. Promotion to served facts happens downstream
(decomposition → ledger → verification gate), never inside a connector. Three invariants:

1. **Every connector writes only SourceArtifacts**, through the artifact store — no connector writes final served facts.
2. **No connector bypasses the artifact store.**
3. **`tenant_private` never updates `global_public`.** A tenant's private source can never advance or write a public source's state/artifacts.

Every ingest is **idempotent**: a re-ingest of identical content (same `idempotency_key` + `content_hash`) returns
an `IngestionReceipt` with `decision="duplicate"` and writes nothing new. Connectors are **deterministic** —
time is injected (`now`), ids are content-addressed via `hashlib`, no RNG.

## Contracts (`schemas/ingestion/*.v1.schema.json`)

| Schema | Role |
|---|---|
| `SourceArtifact` | The governed record of one fetched object. **Requires** `tenant_id`, `source_id`, `source_version`, `source_handle`, `content_hash`, `scope`, `authority`, `artifact_type`, `created_at` (+ `lineage`, `security`). |
| `IngestionReceipt` | Idempotent proof one ingest happened; `decision ∈ ingested\|duplicate\|non_consumable\|rejected`. |
| `SyncState` | Durable per-(tenant, source) sync state: active cursor, last run, mode. |
| `SyncCursor` | A single point-in-stream marker the planner emits/applies idempotently. |
| `SourceHandle` | The parsed, scope-aware form of the `ctx://` handle every artifact carries home. |
| `IngestionRun` | One connector execution: plan, cursor window, counts, terminal status. |
| `IngestionError` | A structured, non-fatal failure record; never produces a served fact. |

All schemas use **stdlib-validator keywords only** (`type`/`required`/`properties`/`enum`/`additionalProperties`/
`items`), validated by `scripts/runtime/schema_validator.py`. Each ships a valid + invalid example under
`schemas/ingestion/examples/`.

## Ports (`src/baltor/ports/`)

| Port | Methods |
|---|---|
| `SourceAdapterPort` (`source_adapter.py`) | `describe` · `plan` · `scan` · `fetch` · `normalize` · `health` |
| `SyncPlannerPort` (`sync_planner.py`) | `plan_full_sync` · `plan_incremental_sync` · `plan_backfill` · `apply_cursor` |
| `SourceArtifactStorePort` (`source_artifact_store.py`) | `write_source_artifacts` · `read_source_artifact` · `query_source_artifacts` · `diff_source_artifacts` |

These are `Protocol`s (runtime-checkable). The current working implementation still lives under `scripts/`
(see the ports layer README + `architecture/migration_plan.json`); these are the typed reusable homes.

## Connector catalog + maturity (`architecture/`)

`ingestion_connector_catalog.json` has one entry per connector (existing + planned). `ingestion_maturity_matrix.json`
records an honest M0..M10/candidate rung per `source_class`:

- **`cfpb_structured` / `json_document` / `csv_table` / `webhook_json` → m8_ui** — proven end-to-end by
  `scripts/check_multi_source_ingestion.py`.
- **`html_page` / `pdf_document` → candidate** — the real cleaner/extractor is a cataloged candidate
  (`scraping_manager` / `parser_manager` slots); until then `UnavailableParserAdapter` stores the raw object as a
  **non-consumable** SourceArtifact and returns an explicit reason — never a faked parse.
- **`markdown_folder` / `local_folder_batch` → m4** — contract-ready with on-disk fixtures; lane B is building the
  implementation + proof this batch (the main agent bumps the rung after it lands).
- **`obsidian_vault` / `customer_database` → candidate** — fixture-contract only. The vault note-link graph is
  **lineage/provenance**, never served truth. Verified session candidates `boxpositron/markdown-vault` (vault API)
  and `benmaster82/Kwipu` (graph-RAG) are catalogued as **candidate-only** replacement notes behind the same
  port — never pip-installed/executed in this lane.

A connector that loses its upstream falls back to a **deterministic local fixture behind the same port**, marks
itself a candidate, and proves the fixture contract — it never fakes truth.

## Proofs

```bash
python3 -m scripts.check_ingestion_contracts --self-test          # schemas exist + validate; SourceArtifact governance fields required
python3 -m scripts.check_ingestion_ports --self-test              # the 3 ports exist with the required method surface
python3 -m scripts.check_ingestion_connector_catalog --self-test  # catalog + maturity matrix complete + honest
```

(The flywheel runs these the same way it runs every registered proof — with the repo root on `PYTHONPATH`,
identical to `scripts/check_multi_source_ingestion.py`.)
