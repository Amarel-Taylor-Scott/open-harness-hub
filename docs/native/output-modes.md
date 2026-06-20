# Native Output Modes

## Purpose

Document the eight `output_mode` values that select how Baltor projects governed context back to a customer.
The **single source of truth** is the registry `architecture/native_output_modes.json` — this doc explains
it; it does not re-define it (see [No Magic Values](../codex/no-magic-values.md)).

## Owner

- Registry: `architecture/native_output_modes.json` (Lane C).
- Enforcement: `scripts/api_native_handler.py` reads the registry to validate the requested mode and to gate
  whether a value change is even permitted; Lane B's `native_projection_builder` produces the shape per mode.

## Contracts

Each registry row has: `id`, `description`, `mutates_values: bool`, `emits_sidecar: bool`, `byte_identical:
bool`, `best_for: [..]`. Three invariants are proven by `scripts/check_native_output_modes.py`:

- **Only** `schema_preserving`, `schema_preserving_with_sidecar`, `compare` set `mutates_values: true`.
- **Only** `native_passthrough` and `native_passthrough_with_sidecar` set `byte_identical: true`.
- A byte-identical mode can never mutate values; a mutating mode is never byte-identical.

## The eight modes

| `output_mode` | mutates_values | emits_sidecar | byte_identical | what the customer gets |
|---|:---:|:---:|:---:|---|
| `native_passthrough` | no | no | **yes** | the original, unchanged — pure drop-in |
| `native_passthrough_with_sidecar` | no | yes | **yes** | original unchanged + governance sidecar (safest power mode) |
| `schema_preserving` | **yes** | no | no | same schema/columns; only VERIFIED value changes (each a NativeDiff + receipt) |
| `schema_preserving_with_sidecar` | **yes** | yes | no | same schema + verified changes + receipts/conflicts/warnings sidecar |
| `annotated_native` | no | yes | no | same doc format (MD/HTML/DOCX) + inline annotations/footnotes; no silent value change |
| `baltor_native` | no | no | no | the advanced `ContextResponse.v1` / `ContextPack.v1` surface |
| `dual` | no | yes | no | both the native output AND the baltor-native response (migration path) |
| `compare` | **yes** | yes | no | original + updated + NativeDiff + sidecar (human review before drop-in) |

## "Same format" precision

byte-identical (only via passthrough) · format-identical (yes) · schema-identical (yes) · semantically
equivalent / cleaned (yes) · annotated-native (yes) · visually-identical PDF (hard → sidecar/annotation) ·
API-compatible request/response (very feasible).

## Inputs

`GET /api/native/export/<source_id>?mode=<output_mode>` — an unknown mode returns `400` with `known_modes`.

## Outputs

A projection-only dict: `{native_output, sidecar?, diff, source_hash, mode, projection_only: true, ...}`. A
value in `native_output` may differ from source **only** when the export service marks it VERIFIED and emits a
matching NativeDiff entry; the API re-checks this defensively (see [sidecars](sidecars.md) and the no-bypass proof).

## Proofs

- `scripts/check_native_output_modes.py --self-test` — registry shape + the three invariants above.
- `scripts/check_native_export_no_truth_bypass.py --self-test` — only the three mutating modes may change a
  value; an unverified/undiffed differing value is held out, never served.

## Commands

```bash
python3 -m scripts.check_native_output_modes --self-test
python3 -m scripts.check_native_export_no_truth_bypass --self-test
```

## Limitations

- Adding a new mode means editing the registry **and** the proof's expected sets — that drift is intentional:
  the proof is the guardrail that keeps the registry honest.
- `mutates_values` describes the same-shape **projection**, never the stored source bytes — the original is
  never overwritten in any mode.

## Next

- Surface a mode picker in the planned `/native` UI; default tenants to `native_passthrough_with_sidecar`
  (safest power mode) and let regulated tenants pin `native_passthrough` or `schema_preserving_with_sidecar`.
