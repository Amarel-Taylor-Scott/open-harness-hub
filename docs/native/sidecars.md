# Native Sidecars

## Purpose

The **sidecar** is where Baltor keeps the governance *power* when a customer keeps their native shape. It is a
`SidecarOverlay` returned alongside (never instead of) the native output, so a customer can say *"do not
change my tables — give me the context elsewhere"* and still get receipts, conflicts, held-out claims,
reconciliations, and full lineage. This is the lossless-distillation law on the export layer: a value omitted
from the native output is **held out in the sidecar, never erased**.

## Owner

- Builder (Lane B): `src/baltor/native/sidecar_writer.py`.
- Projection (Lane C): `GET /api/native/sidecar/<source_id>` and the `sidecar` field of an export, served by
  `scripts/api_native_handler.py`.

## Contracts

`SidecarOverlay`:

| field | meaning |
|---|---|
| `source_hash` | sha256 of the original source bytes — the pivot back to the original |
| `artifact_ids` | every artifact referenced by the overlay (incl. those referenced only by held-out claims) |
| `field_map` | `native_path` ⇄ `source_handle` ⇄ `artifact_id` ⇄ `claim_status` (+ `differs_from_source`) |
| `field_facts` | per native path, the fact artifact backing it |
| `held_out_claims` | claims kept out of the native output (value + reason + source_handle + artifact_id) |
| `conflicts` | detected conflicts (e.g. deadline mismatch) with winner/held-out |
| `reconciliations` | how each conflict was resolved (decision + winning artifact id) |
| `verification_receipts` | receipt per changed/served fact |
| `warnings` | per native path notes (e.g. "value corrected from source; see diff + receipt") |

## Lineage invariants (proven)

- **Every native output field** has a `field_map` entry that resolves to a `source_handle` **and** a resolvable
  `artifact_id`. There are no orphan native fields.
- **Held-out claims stay in the sidecar** and their values do **not** appear in the native output; yet their
  artifact ids still resolve (omitted ≠ deleted).
- **Every changed native field** (`differs_from_source: true`) has a matching `NativeDiff` entry **and** a
  verification receipt — no silent change.

## Inputs

`GET /api/native/sidecar/<source_id>` (and `field_map`/`held_out_claims` are also embedded in an export with a
`*_with_sidecar` / `dual` / `compare` / `annotated_native` mode).

## Outputs

`{available, source_id, tenant_id, source_hash, sidecar}` — projection-only; degrades to `available: false`
with the source bytes still preserved when the Lane B writer is absent.

## Proofs

- `scripts/check_native_sidecar_lineage.py --self-test` — the lineage invariants above.
- `scripts/check_native_export_rehydration.py --self-test` — export + sidecar pivot back to the original via
  `source_hash`; the original is never overwritten.

## Commands

```bash
python3 -m scripts.check_native_sidecar_lineage --self-test
python3 -m scripts.check_native_export_rehydration --self-test
```

## Limitations

- For SQL customers the same overlay maps to side tables (`baltor_artifacts` / `baltor_source_handles` /
  `baltor_conflicts` / `baltor_reconciliations` / `baltor_receipts` / `baltor_field_annotations` + a `*_view`);
  that variant is a tracked opportunity, not yet built.
- The handler never serializes raw source bytes to a client — the sidecar exposes `source_hash` + `byte_len`,
  not the stored bytes.

## Next

- Land `src/baltor/native/sidecar_writer.py` (Lane B) so real conflicts/reconciliations/receipts flow through
  the projection, and add the SQL side-table emitter.
