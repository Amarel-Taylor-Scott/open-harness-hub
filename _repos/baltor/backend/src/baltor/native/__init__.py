"""_repos/baltor/backend/src/baltor/native — Native Format Preservation (C-NATIVE-1).

Baltor does NOT force customers into a new format. It wraps their existing formats with governed, verified,
reconciled, optimized context — returning the SAME native shape for compatibility, plus a governed sidecar for
power. THE ORIGINAL IS NEVER OVERWRITTEN. This is the [[lossless-distillation-law]] applied to the output/export
layer: the original bytes + hash are preserved, held-out is never erased, every value change carries a NativeDiff
entry + a verification receipt, and everything rehydrates to its source handles.

Runtime (rides the existing runtime — NO 2nd ledger / NO 2nd export framework):
  NativeFormatPreserver  — detect shape -> NativeShapeContract; keep original bytes + sha256; never mutate.
  NativeProjectionBuilder — build same-shape output per output_mode; apply ONLY verified value changes; emit
                            a NativeDiff per change.
  SidecarWriter          — build the SidecarOverlay (field_facts, held_out_claims, conflicts, reconciliations,
                            verification_receipts, warnings, source_hash, artifact_ids, field_map).
  NativeExportService    — export(source, output_mode, tenant_id, *, now) -> {native_output, sidecar, diff,
                            context_response?, receipt}; deterministic + offline.
"""
from __future__ import annotations

from src.baltor.native.native_export_service import NativeExportService, OUTPUT_MODES
from src.baltor.native.native_format_preserver import NativeFormatPreserver, NativeShapeContract
from src.baltor.native.native_projection_builder import NativeProjectionBuilder
from src.baltor.native.sidecar_writer import SidecarWriter

__all__ = [
    "NativeFormatPreserver",
    "NativeShapeContract",
    "NativeProjectionBuilder",
    "SidecarWriter",
    "NativeExportService",
    "OUTPUT_MODES",
]
