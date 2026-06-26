# Native Format Preservation — Overview

> **Baltor does not force customers into a new format — it wraps their existing formats with governed,
> verified, reconciled, optimized context.** Same native shape for compatibility + a governed sidecar for
> power + advanced endpoints for depth. This is the **[lossless-distillation law](../codex/lossless-distillation.md)
> applied to the output/export layer**: the original is never overwritten, held-out is never erased, every
> value change carries a diff + receipt, and everything rehydrates.

## Purpose

Let a customer adopt Baltor **without replacing their data model, UI, tables, or APIs**. Baltor remains the
source of truth and stores richer governed context in **sidecars** and **advanced endpoints**, while the
*native output* it returns is byte/format/schema-compatible for drop-in use. The original input is never
mutated; richer governance lives alongside it.

## Owner

- API handler (this lane, Lane C): `scripts/api_native_handler.py` (projection-safe; pure `handle()` + `owns()`).
- Output-mode registry (this lane): `architecture/native_output_modes.json` (the canonical 8 modes).
- Runtime (Lane B): `src/baltor/native/native_format_preserver.py`, `native_projection_builder.py`,
  `sidecar_writer.py`, `native_export_service.py`. The API CALLS the export service and degrades gracefully
  when it (or a source) is absent.
- Maturity section: `native_format_preservation` (category `consumption_export`, `critical_path_required: false`).

## Contracts

- `NativeShapeContract` — detected shape (format, schema_hash, field_order, encoding, delimiter, newline, mime_type).
- `NativeProjection` — the same-shape output for the requested `output_mode`.
- `SidecarOverlay` — `{source_hash, artifact_ids, field_facts, field_map, held_out_claims, conflicts,
  reconciliations, verification_receipts, warnings}`.
- `NativeDiff` — `changed_fields: [{path, old, new, decision, receipt_id}]` (every VERIFIED value change).
- `NativeExportReceipt` / `NativeIngestResult` / `NativeSourceRef` — export/ingest receipts + the stored source ref.

These contract names are registered by MAIN in `architecture/contract_registry.json`; this lane only
produces files and proofs (no shared-manifest edits).

## Inputs

- A customer source: JSON object, CSV/text, or Markdown/HTML (bytes or string), with a tenant id.
- An `output_mode` selecting how Baltor projects governed context back (see [output-modes](output-modes.md)).

## Outputs

- `native_output` — the same-shape projection (or the unchanged original in passthrough modes).
- `sidecar` — the `SidecarOverlay` carrying receipts/conflicts/held-out/lineage (when the mode emits one).
- `diff` — the `NativeDiff` of any VERIFIED value changes.
- `context_response?` — the advanced `ContextResponse` (in `baltor_native` / `dual`).
- `receipt` — a `NativeExportReceipt` tying the export back to the source hash.

## Proofs

| Proof | What it asserts |
|---|---|
| `scripts/check_native_output_modes.py` | the registry has all 8 modes; only `schema_preserving`/`schema_preserving_with_sidecar`/`compare` mutate values; `native_passthrough(+_with_sidecar)` is byte-identical |
| `scripts/check_native_sidecar_lineage.py` | every native field maps to a source_handle + a resolvable artifact_id; held-out claims stay in the sidecar yet still resolve |
| `scripts/check_native_export_no_truth_bypass.py` | (negative) an unverified value is never served as fact; held-out stays in the sidecar; smuggled diffs are suppressed |
| `scripts/check_native_export_rehydration.py` | given an export + sidecar you can reach the original source bytes/hash + artifacts; the original is never overwritten |
| `scripts/check_native_api.py` | each route returns the expected dict; ingest writes no canonical truth; export is projection-only; no secrets leak |

## Commands

```bash
python3 -m scripts.check_native_output_modes --self-test
python3 -m scripts.check_native_sidecar_lineage --self-test
python3 -m scripts.check_native_export_no_truth_bypass --self-test
python3 -m scripts.check_native_export_rehydration --self-test
python3 -m scripts.check_native_api --self-test
```

## Limitations

- The Lane B runtime (`native_export_service`) is imported lazily; until it lands, the API degrades to a safe
  **passthrough** projection (the unchanged original, no value applied) and empty sidecar/diff. The
  registry/lineage/no-bypass proofs validate the contract against a deterministic reference so they hold either way.
- Byte-identical output is only achievable via the passthrough modes. Visually-identical PDF is hard and is
  served via sidecar/annotation rather than a pixel-perfect rewrite.
- The ingest source projection (`_SOURCES`) is process-level and rebuilt on restart — it is a projection of
  references, not a second ledger or truth store.

## Next

- Wire the Lane B `native_export_service` so non-passthrough modes return real same-shape projections + sidecars.
- Add a `/native` UI surface (see the `native_format_preservation` opportunity) and a SQL side-table variant
  (`baltor_artifacts` / `baltor_source_handles` / `baltor_conflicts` / `baltor_receipts` + a `*_view`).
