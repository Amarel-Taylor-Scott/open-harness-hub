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

- API handler (this lane, Lane C): `_repos/shared-backend-components/scripts/api_native_handler.py` (projection-safe; pure `handle()` + `owns()`).
- Output-mode registry (this lane): `_repos/shared-backend-components/architecture/native_output_modes.json` (the canonical 8 modes).
- Runtime (Lane B): `_repos/baltor/backend/src/baltor/native/native_format_preserver.py`, `native_projection_builder.py`,
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

These contract names are registered by MAIN in `_repos/shared-backend-components/architecture/contract_registry.json`; this lane only
produces files and proofs (no shared-manifest edits). The JSON Schemas live at
`_repos/shared-backend-components/schemas/native/*.v1.schema.json` (+ `examples/`): `NativeShapeContract`, `NativeProjection`,
`SidecarOverlay`, `NativeDiff`, `NativeExportReceipt`.

## The eight output modes (single source: `_repos/shared-backend-components/architecture/native_output_modes.json`)

`native_passthrough` · `native_passthrough_with_sidecar` · `schema_preserving` ·
`schema_preserving_with_sidecar` · `annotated_native` · `baltor_native` · `dual` · `compare`.

See [output-modes.md](output-modes.md) for the per-mode table; the registry is the canonical definition
(this doc does not re-define it — see [No Magic Values](../codex/no-magic-values.md)). Only the value-changing
modes (`schema_preserving`, `schema_preserving_with_sidecar`, `compare`) mutate a value; only the passthrough
modes are byte-identical.

## Runtime files (Lane B — rides the existing runtime; NO 2nd ledger / NO 2nd export framework)

- `_repos/baltor/backend/src/baltor/native/native_format_preserver.py` — detect shape → `NativeShapeContract`;
  keep original bytes + sha256; **never mutate** the original.
- `_repos/baltor/backend/src/baltor/native/native_projection_builder.py` — build a same-shape output per
  `output_mode`; apply **only** verified value changes; emit a `NativeDiff` per change.
- `_repos/baltor/backend/src/baltor/native/sidecar_writer.py` — build the `SidecarOverlay` (`field_facts`,
  `held_out_claims`, `conflicts`, `reconciliations`, `verification_receipts`, `warnings`, `source_hash`,
  `artifact_ids`, `field_map`).
- `_repos/baltor/backend/src/baltor/native/native_export_service.py` —
  `export(source, output_mode, tenant_id, *, now)` → `{native_output, sidecar, diff, context_response?, receipt}`;
  deterministic + offline.

## API (Lane C — projection-safe; `_repos/shared-backend-components/scripts/api_native_handler.py`)

`POST /api/native/ingest` (store-only; no canonical mutation; no fact served) ·
`GET /api/native/export/<source_id>?mode=...` (projection-only same-shape export) ·
`GET /api/native/sidecar/<source_id>` · `GET /api/native/diff/<source_id>` ·
`GET /api/native/annotations/<source_id>`.

## Inputs

- A customer source: JSON object, CSV/text, or Markdown/HTML (bytes or string), with a tenant id.
- An `output_mode` selecting how Baltor projects governed context back (see [output-modes](output-modes.md)).

## Outputs

- `native_output` — the same-shape projection (or the unchanged original in passthrough modes).
- `sidecar` — the `SidecarOverlay` carrying receipts/conflicts/held-out/lineage (when the mode emits one).
- `diff` — the `NativeDiff` of any VERIFIED value changes.
- `context_response?` — the advanced `ContextResponse` (in `baltor_native` / `dual`).
- `receipt` — a `NativeExportReceipt` tying the export back to the source hash.

## Proofs (every one is `--self-test`, deterministic + offline)

| Proof | What it asserts |
|---|---|
| `_repos/shared-backend-components/scripts/check_native_shape_contract.py` | shape detection (format/schema_hash/field_order/columns/delimiter/newline) is frozen + value-independent |
| `_repos/shared-backend-components/scripts/check_native_json_roundtrip.py` | JSON: passthrough byte-identical; schema_preserving keeps keys+nesting, changes only a verified value (each a `NativeDiff`); unverified change refused |
| `_repos/shared-backend-components/scripts/check_native_csv_roundtrip.py` | CSV: columns/order/delimiter/CRLF preserved; only the verified cell (row,col) changes; sidecar carries facts/held-out/receipts |
| `_repos/shared-backend-components/scripts/check_native_markdown_sidecar.py` | Markdown: default note returned byte-for-byte unchanged + sidecar; annotated mode adds without removing |
| `_repos/shared-backend-components/scripts/check_native_output_modes.py` | the registry has all 8 modes; only `schema_preserving`/`schema_preserving_with_sidecar`/`compare` mutate values; `native_passthrough(+_with_sidecar)` is byte-identical |
| `_repos/shared-backend-components/scripts/check_native_sidecar_lineage.py` | every native field maps to a source_handle + a resolvable artifact_id; held-out claims stay in the sidecar yet still resolve |
| `_repos/shared-backend-components/scripts/check_native_export_no_truth_bypass.py` | (negative) an unverified value is never served as fact; held-out stays in the sidecar; smuggled diffs are suppressed |
| `_repos/shared-backend-components/scripts/check_native_export_same_schema.py` | schema_preserving output schema == input schema across modes; a dropped-key output fails (the check has teeth) |
| `_repos/shared-backend-components/scripts/check_native_export_rehydration.py` | given an export + sidecar you can reach the original source bytes/hash + artifacts; the original is never overwritten; ingest is content-addressed |
| `_repos/shared-backend-components/scripts/check_native_api.py` | each route returns the expected dict; ingest writes no canonical truth; export is projection-only; no secrets leak |
| **`_repos/shared-backend-components/scripts/check_native_format_full_stack.py`** | **END-TO-END**: drives the real runtime + API across JSON/CSV/Markdown × the key modes; one `FORMAT \| MODE \| ORIG_PRESERVED \| SAME_SCHEMA \| SIDECAR \| HELD_OUT_KEPT \| NO_TRUTH_BYPASS \| REHYDRATE \| STATUS` table |

## Commands

```bash
python3 _repos/shared-backend-components/scripts/check_native_shape_contract.py --self-test
python3 _repos/shared-backend-components/scripts/check_native_json_roundtrip.py --self-test
python3 _repos/shared-backend-components/scripts/check_native_csv_roundtrip.py --self-test
python3 _repos/shared-backend-components/scripts/check_native_markdown_sidecar.py --self-test
python3 _repos/shared-backend-components/scripts/check_native_output_modes.py --self-test
python3 _repos/shared-backend-components/scripts/check_native_sidecar_lineage.py --self-test
python3 _repos/shared-backend-components/scripts/check_native_export_no_truth_bypass.py --self-test
python3 _repos/shared-backend-components/scripts/check_native_export_same_schema.py --self-test
python3 _repos/shared-backend-components/scripts/check_native_export_rehydration.py --self-test
python3 _repos/shared-backend-components/scripts/check_native_api.py --self-test
# the synthesis proof — runs the whole stack end-to-end and prints the matrix:
python3 _repos/shared-backend-components/scripts/check_native_format_full_stack.py --self-test
```

## Acceptance (A–J, from `prompts/baltor-native-format-preservation.md`)

JSON same-structure export · CSV same-columns/order · Markdown unchanged + sidecar · sidecar carries
facts/warnings/conflicts/receipts/lineage · original never overwritten · held-out remains visible · NO
unverified fact served · native export rehydrates to artifacts · section in matrix · flywheel green. The
full-stack proof exercises A–H end-to-end; the section + flywheel registration (I–J) is integrated by MAIN.

## Limitations

- The Lane B runtime (`native_export_service`) is imported lazily; until it lands, the API degrades to a safe
  **passthrough** projection (the unchanged original, no value applied) and empty sidecar/diff. The
  registry/lineage/no-bypass proofs validate the contract against a deterministic reference so they hold either way.
- Byte-identical output is only achievable via the passthrough modes. Visually-identical PDF is hard and is
  served via sidecar/annotation rather than a pixel-perfect rewrite.
- Markdown mutating modes never silently edit the note body — the verified fact rides in the sidecar's
  `field_facts`; the strict-preservation default returns the note byte-for-byte.
- The ingest source projection (`_SOURCES` in the API handler) is process-level and rebuilt on restart — it is
  a projection of references, not a second ledger or truth store.

## Next

- Wire the Lane B `native_export_service` so non-passthrough modes return real same-shape projections + sidecars.
- Add a `/native` UI surface (see the `native_format_preservation` opportunity) and a SQL side-table variant
  (`baltor_artifacts` / `baltor_source_handles` / `baltor_conflicts` / `baltor_receipts` + a `*_view`).
