# Multi-source regression status

The multi-source regression proves that **every supported source TYPE** walks the same
source→consumption motion and lands at its expected outcome — consumable sources serve a schema-valid
`ContextResponse`, and candidate (parser-unavailable) sources return an honest `non_consumable_reason`
and are **never** served as fact.

- Orchestrator: `scripts/runtime/source_consumption.py` (`run_source_to_consumption`)
- Run matrix: `architecture/multi_source_run_matrix.json`
- Proof: `scripts/check_multi_source_regression.py`
- Reference: [`docs/runtime/source-consumption.md`](../runtime/source-consumption.md)

## Per-source status (reference run, `now=2026-06-05T00:00:00Z`)

| row_id | source_type | scope | expected status | served facts | held-out | result |
|---|---|---|---|---|---|---|
| `cfpb_structured_json` | api | global_public | served | 3 | 2 | ok |
| `generic_json` | json | global_public | served | 2 | 2 | ok |
| `csv_table` | csv | tenant_private | served | 2 | 2 | ok |
| `webhook_json` | webhook | tenant_private | served | 3 | 0 | ok |
| `html_page` | html | global_public | non_consumable | 0 | 0 | ok |
| `pdf_document` | pdf | global_public | non_consumable | 0 | 0 | ok |

(The proof prints this table live; counts above are the deterministic reference run.)

## Invariants enforced

- **Status match** — each row's `consumption_status` equals the matrix's `expected_consumption_status`.
- **Served = real** — consumable rows produce a schema-valid `ContextResponse`; every served fact carries
  a source handle and verification + optimization lineage.
- **Candidate = honest** — `html` / `pdf` return `consumable:false` + a `parser_unavailable` reason, with
  the raw payload stored as a source artifact and **no faked response** (`response is None`).
- **No allegation served as fact** — narrative free-text is held out as a warning, never served.
- **No tenant leak** — a `tenant_private` source never serves a fact under a global/public handle; the
  response stays scoped to its tenant.
- **Deterministic** — a second run of the whole matrix is byte-identical.

## Reproduce

```bash
PYTHONPATH=. python3 scripts/check_source_to_consumption_generic.py --self-test
PYTHONPATH=. python3 scripts/check_multi_source_regression.py --self-test
```

## Adding a new source type

1. Register the adapter in `scripts/ingest/source_adapters.py` (`REGISTRY`) and in
   `architecture/contract_registry.json#source_types` (this is the main agent's job — report it).
2. Add a row to `architecture/multi_source_run_matrix.json` with a payload and an
   `expected_consumption_status`.
3. Re-run `check_multi_source_regression.py --self-test` — the new row must turn `ok`.
