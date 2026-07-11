# Baltor Native Format Preservation (C-NATIVE-1) — queued workflow spec

> Owner directive (2026-06-05). Product identity sharpening: **Baltor does not force customers into a
> new format — it wraps their existing formats with governed, verified, reconciled, optimized context.**
> Same native shape for compatibility + a governed sidecar for power + advanced endpoints for depth.
> This is the **[[lossless-distillation-law]] applied to the output/export layer**: the original is never
> overwritten, held-out is never erased, every change carries a diff + receipt, everything rehydrates.

## The strength this leans into
Baltor's edge is context **enhancement, reconciliation, governance, decomposition, deterministic
heuristics** — NOT being another memory/vector/RAG store ([[moat-reframe-data-not-capability-gap]],
[[governance-is-the-product]], [[supermemory-competitor-complement]]). Native preservation lets a
customer adopt Baltor WITHOUT replacing their data model, UI, tables, or APIs.

## Output modes (an explicit per-request/per-tenant config — `output_mode`)
- `native_passthrough` — original returned unchanged.
- `native_passthrough_with_sidecar` — original unchanged + `*.baltor.sidecar.json` (safest; legal/audit/immutable).
- `schema_preserving` — same schema/keys/columns; only VERIFIED value changes (e.g. `"30 days"`→`"10 business days"`).
- `schema_preserving_with_sidecar` — same schema + receipts/conflicts/warnings/diff sidecar.
- `annotated_native` — same doc format (MD/HTML/DOCX) + annotations/comments/footnotes/frontmatter.
- `baltor_native` — `ContextResponse` / `ContextPack` (the advanced surface).
- `dual` — both native output AND baltor-native.
- `compare` — original + updated + diff + sidecar.

## "Same format" precision (set expectations)
byte-identical (only via passthrough) · format-identical (yes) · schema-identical (yes) · semantically
equivalent/cleaned (yes) · annotated-native (yes) · visually-identical PDF (hard → sidecar/annotation) ·
API-compatible request/response (very feasible).

## Contracts (_repos/shared-backend-components/schemas/native/*.v1; register in contract_registry)
NativeShapeContract (format, schema_hash, field_order, encoding, delimiter, newline, mime_type) ·
NativeProjection · SidecarOverlay (field_facts, held_out_claims, conflicts, reconciliations,
verification_receipts, warnings, source_hash, artifact_ids) · NativeDiff (changed_fields: path/old/
new/decision/receipt_id) · NativeExportReceipt.

## Runtime (behind ports; NO 2nd ledger / NO 2nd export framework — rides existing runtime)
NativeFormatPreserver · NativeProjectionBuilder · SidecarWriter · NativeExportService. Pipeline:
raw input → SourceArtifact (exact bytes/hash) → NativeShapeContract → parsed/decomposed artifacts →
reconciliation/verification/optimization → NativeProjection (same shape) + SidecarOverlay → optional
ContextResponse. The native projection fits the customer's system; the sidecar holds the governance power.

## Sidecar storage (side tables — "do not change my tables, give me context elsewhere")
native_shape_contracts · native_field_map (native_path ⇄ source_handle ⇄ artifact_id ⇄ claim_status) ·
native_annotations (warnings/receipts/conflicts per native_path) · native_diffs · native_exports
(output_mode, source_hash, export_hash, sidecar_hash, context_response_id, receipt_id — reproducible/auditable).
For SQL customers: keep their tables; add baltor_artifacts / baltor_source_handles / baltor_conflicts /
baltor_reconciliations / baltor_receipts / baltor_field_annotations + a `*_view`.

## Format support
- JSON: preserve keys + nested structure; JSON-pointer field map; sidecar = artifact lineage.
- CSV: preserve columns/order/delimiter/newlines; row/col field map; sidecar table = facts/warnings/receipts.
- Markdown/Obsidian: DEFAULT original unchanged + `.baltor/<note>.baltor.json` sidecar; optional annotated/
  frontmatter mode (`baltor_status`, `baltor_receipt`); strict preservation → never edit the note.

## API
Native-compatible: POST /api/native/ingest · GET /api/native/export/<source_id>?mode=... ·
GET /api/native/sidecar/<source_id> · GET /api/native/diff/<source_id> · GET /api/native/annotations/<source_id>.
Hybrid: POST /api/context/serve {output_mode} → {native_output, sidecar, context_response, receipts}.

## Maturity / proofs
Section `native_format_preservation` (category consumption_export, critical_path_required:false). Proofs:
check_native_shape_contract · check_native_json_roundtrip · check_native_csv_roundtrip ·
check_native_markdown_sidecar · check_native_sidecar_lineage · check_native_export_no_truth_bypass ·
check_native_export_same_schema · check_native_export_rehydration.

## Acceptance (A–J)
JSON same-structure export · CSV same-columns/order · Markdown unchanged + sidecar · sidecar carries
facts/warnings/conflicts/receipts/lineage · original never overwritten · held-out remains visible ·
NO unverified fact served · native export rehydrates to artifacts · section in matrix · flywheel green.

## Build discipline (same as all factories)
Build agents create ONLY isolated new files + run ONLY their own proofs; MAIN integrates shared manifests
serially behind a full-flywheel gate. Determinism in proofs (injected time, hashlib ids, temp dirs, offline).
No commit/push/pip/containers/network/secrets. Carry the LOSSLESS DISTILLATION CLAUSE.

## LOSSLESS DISTILLATION CLAUSE (verbatim)
Any distillation/decomposition/compression/optimization/reconciliation/promotion/LLM-to-rule conversion
must be lossless at the system level. Never overwrite or delete raw/source/intermediate artifacts. Every
derived artifact preserves source handles, lineage, transform config, version, receipts, held-out items,
rejected candidates, and a rollback target. Run side-by-side before promotion, shadow new rules, monitor
after, prove rehydration. Omitted means held out or excluded from a view, never erased.
