# Native Format Preservation (C-NATIVE-1) — Index

> **Baltor does not force customers into a new format — it wraps their existing formats with governed,
> verified, reconciled, optimized context.** Same native shape for compatibility + a governed **sidecar**
> for power + advanced endpoints for depth. This is the
> [lossless-distillation law](../codex/lossless-distillation.md) applied to the **output/export layer**:
> the original is never overwritten, held-out is never erased, every value change carries a diff + receipt,
> and everything rehydrates to its source.

A customer can adopt Baltor **without replacing their data model, UI, tables, or APIs**. Baltor stays the
source of truth (the governed artifacts live in the sidecar + advanced endpoints); the *native output* is
purely for drop-in compatibility. **THE ORIGINAL IS NEVER OVERWRITTEN.**

## Docs

| Doc | What it covers |
|---|---|
| [overview.md](overview.md) | purpose, owners, contracts, inputs/outputs, the full proof set, limitations |
| [output-modes.md](output-modes.md) | the eight `output_mode` values + the three registry invariants (only the value-changing modes mutate; only passthrough is byte-identical) |
| [sidecars.md](sidecars.md) | the `SidecarOverlay.v1` fields + the lineage invariants (every field → handle + resolvable artifact; held-out kept, never served) |

## The eight output modes (single source: `architecture/native_output_modes.json`)

`native_passthrough` · `native_passthrough_with_sidecar` · `schema_preserving` ·
`schema_preserving_with_sidecar` · `annotated_native` · `baltor_native` · `dual` · `compare`.

See [output-modes.md](output-modes.md) for the per-mode table; the registry is the canonical definition
(this index does not re-define it — see [No Magic Values](../codex/no-magic-values.md)).

## Runtime (Lane B — rides the existing runtime; NO 2nd ledger / NO 2nd export framework)

- `src/baltor/native/native_format_preserver.py` — detect shape → `NativeShapeContract`; keep original
  bytes + sha256; **never mutate** the original.
- `src/baltor/native/native_projection_builder.py` — build a same-shape output per `output_mode`; apply
  **only** verified value changes; emit a `NativeDiff` per change.
- `src/baltor/native/sidecar_writer.py` — build the `SidecarOverlay` (`field_facts`, `held_out_claims`,
  `conflicts`, `reconciliations`, `verification_receipts`, `warnings`, `source_hash`, `artifact_ids`,
  `field_map`).
- `src/baltor/native/native_export_service.py` — `export(source, output_mode, tenant_id, *, now)` →
  `{native_output, sidecar, diff, context_response?, receipt}`; deterministic + offline.

## API (Lane C — projection-safe; `scripts/api_native_handler.py`)

`POST /api/native/ingest` (store-only; no canonical mutation; no fact served) ·
`GET /api/native/export/<source_id>?mode=...` (projection-only same-shape export) ·
`GET /api/native/sidecar/<source_id>` · `GET /api/native/diff/<source_id>` ·
`GET /api/native/annotations/<source_id>`.

## Contracts

`schemas/native/*.v1.schema.json` (+ `examples/`): `NativeShapeContract.v1`, `NativeProjection.v1`,
`SidecarOverlay.v1`, `NativeDiff.v1`, `NativeExportReceipt.v1`. Registered by MAIN in
`architecture/contract_registry.json`.

## Proofs (every one is `--self-test`, deterministic + offline)

| Proof | Asserts |
|---|---|
| `scripts/check_native_shape_contract.py` | shape detection (format/schema_hash/field_order/columns/delimiter/newline) is frozen + value-independent |
| `scripts/check_native_json_roundtrip.py` | JSON: passthrough byte-identical; schema_preserving keeps keys+nesting, changes only a verified value (each a `NativeDiff`); unverified change refused |
| `scripts/check_native_csv_roundtrip.py` | CSV: columns/order/delimiter/CRLF preserved; only the verified cell (row,col) changes; sidecar carries facts/held-out/receipts |
| `scripts/check_native_markdown_sidecar.py` | Markdown: default note returned byte-for-byte unchanged + sidecar; annotated mode adds without removing |
| `scripts/check_native_output_modes.py` | the registry has all 8 modes; only `schema_preserving`/`_with_sidecar`/`compare` mutate; only passthrough is byte-identical |
| `scripts/check_native_sidecar_lineage.py` | every native field → source_handle + resolvable artifact_id; held-out kept in the sidecar yet still resolves |
| `scripts/check_native_export_no_truth_bypass.py` | (negative) an unverified value is never served as fact; smuggled diffs suppressed; only mutating modes may change a value |
| `scripts/check_native_export_same_schema.py` | schema_preserving output schema == input schema across modes; a dropped-key output fails (the check has teeth) |
| `scripts/check_native_export_rehydration.py` | given an export + sidecar you reach the original bytes/hash; the original is never overwritten; ingest is content-addressed |
| `scripts/check_native_api.py` | each route returns the expected dict; ingest writes no canonical truth; export is projection-only; no secrets leak |
| **`scripts/check_native_format_full_stack.py`** | **END-TO-END**: drives the real runtime + API across JSON/CSV/Markdown × the key modes; one `FORMAT \| MODE \| ORIG_PRESERVED \| SAME_SCHEMA \| SIDECAR \| HELD_OUT_KEPT \| NO_TRUTH_BYPASS \| REHYDRATE \| STATUS` table |

## Commands

```bash
python3 scripts/check_native_shape_contract.py --self-test
python3 scripts/check_native_json_roundtrip.py --self-test
python3 scripts/check_native_csv_roundtrip.py --self-test
python3 scripts/check_native_markdown_sidecar.py --self-test
python3 scripts/check_native_output_modes.py --self-test
python3 scripts/check_native_sidecar_lineage.py --self-test
python3 scripts/check_native_export_no_truth_bypass.py --self-test
python3 scripts/check_native_export_same_schema.py --self-test
python3 scripts/check_native_export_rehydration.py --self-test
python3 scripts/check_native_api.py --self-test
# the synthesis proof — runs the whole stack end-to-end and prints the matrix:
python3 scripts/check_native_format_full_stack.py --self-test
```

## Acceptance (A–J, from `prompts/baltor-native-format-preservation.md`)

JSON same-structure export · CSV same-columns/order · Markdown unchanged + sidecar · sidecar carries
facts/warnings/conflicts/receipts/lineage · original never overwritten · held-out remains visible · NO
unverified fact served · native export rehydrates to artifacts · section in matrix · flywheel green. The
full-stack proof exercises A–H end-to-end; the section + flywheel registration (I–J) is integrated by MAIN.

## Limitations

- Byte-identical output is achievable **only** via the passthrough modes; visually-identical PDF is hard and
  is served via sidecar/annotation rather than a pixel-perfect rewrite.
- Markdown mutating modes never silently edit the note body — the verified fact rides in the sidecar's
  `field_facts`; the strict-preservation default returns the note byte-for-byte.
- The ingest source projection (`_SOURCES` in the API handler) is process-level and rebuilt on restart — a
  projection of references, not a second ledger or truth store.
