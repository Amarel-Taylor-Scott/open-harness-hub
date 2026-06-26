#!/usr/bin/env python3
"""src/baltor/native/native_export_service — the one entry point for native-format export across 8 modes.

``export(source, output_mode, tenant_id, *, now)`` -> {native_output, sidecar, diff, context_response?, receipt}.

This is the customer-facing surface: a customer hands Baltor their own JSON / CSV / Markdown and chooses how they
want it back. Baltor stays the source of truth (the governed artifacts live in the sidecar + advanced endpoints);
the native_output is purely for drop-in compatibility. THE ORIGINAL IS NEVER OVERWRITTEN — the frozen contract
keeps the exact bytes + sha256, and passthrough returns them byte-for-byte.

NO 2nd ledger / NO 2nd export framework: this orchestrates the three Lane-B runtime pieces (preserve -> project ->
sidecar) and emits one NativeExportReceipt that references the existing artifacts/receipts the caller supplies.
It does not stand up a second store, bus, or optimizer.

Output modes (output_mode config):
  native_passthrough              — original returned unchanged (byte-identical).
  native_passthrough_with_sidecar — original unchanged + governed sidecar (safest: legal/audit/immutable).
  schema_preserving               — same schema/keys/columns; only VERIFIED value changes (each emits a NativeDiff).
  schema_preserving_with_sidecar  — same schema + receipts/conflicts/warnings sidecar.
  annotated_native                — same doc format + annotations (markdown comment/frontmatter) — adds, never removes.
  baltor_native                   — the advanced ContextResponse surface (passed through from the caller).
  dual                            — both native output AND baltor_native.
  compare                         — original + updated + diff + sidecar.

Deterministic + offline + stdlib only: ids content-addressed; injected ``now``; no RNG, no network, no secrets.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from src.baltor.native.native_format_preserver import NativeFormatPreserver
from src.baltor.native.native_projection_builder import NativeProjectionBuilder
from src.baltor.native.sidecar_writer import SidecarWriter

EPOCH = "1970-01-01T00:00:00Z"

#: every supported output_mode (the per-request/per-tenant config). Single source of the mode vocabulary.
OUTPUT_MODES = ("native_passthrough", "native_passthrough_with_sidecar", "schema_preserving",
                "schema_preserving_with_sidecar", "annotated_native", "baltor_native", "dual", "compare")

#: modes that return the original bytes UNCHANGED (passthrough family) — never apply a value change here.
_PASSTHROUGH_MODES = ("native_passthrough", "native_passthrough_with_sidecar", "annotated_native",
                      "baltor_native", "dual", "compare")
#: modes that attach a governed sidecar.
_SIDECAR_MODES = ("native_passthrough_with_sidecar", "schema_preserving_with_sidecar", "dual", "compare")
#: modes that may apply VERIFIED value changes into the same shape.
_VALUE_CHANGE_MODES = ("schema_preserving", "schema_preserving_with_sidecar", "compare")
#: modes that surface the advanced ContextResponse alongside.
_CONTEXT_RESPONSE_MODES = ("baltor_native", "dual")


def _hid(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:16]


@dataclass
class NativeExportReceipt:
    """The auditable record of one native export. References existing artifacts/receipts — no second ledger."""
    receipt_id: str
    source_hash: str
    output_mode: str
    tenant_id: str
    native_format: str
    output_hash: str
    sidecar_hash: str
    diff_id: str
    context_response_id: str
    changed_field_count: int
    held_out_count: int
    byte_identical_to_source: bool
    original_overwritten: bool      # ALWAYS False — the invariant, recorded for auditors
    created_at: str
    schema_version: str = "NativeExportReceipt"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "receipt_id": self.receipt_id, "source_hash": self.source_hash,
                "output_mode": self.output_mode, "tenant_id": self.tenant_id, "native_format": self.native_format,
                "output_hash": self.output_hash, "sidecar_hash": self.sidecar_hash, "diff_id": self.diff_id,
                "context_response_id": self.context_response_id, "changed_field_count": self.changed_field_count,
                "held_out_count": self.held_out_count, "byte_identical_to_source": self.byte_identical_to_source,
                "original_overwritten": self.original_overwritten, "created_at": self.created_at}


class NativeExportService:
    """Orchestrate preserve -> project -> sidecar for any output_mode. Deterministic, offline, original-safe."""

    def __init__(self, preserver: NativeFormatPreserver | None = None,
                 projection_builder: NativeProjectionBuilder | None = None,
                 sidecar_writer: SidecarWriter | None = None) -> None:
        self._preserver = preserver or NativeFormatPreserver()
        self._projector = projection_builder or NativeProjectionBuilder()
        self._sidecar = sidecar_writer or SidecarWriter()

    def export(self, source, *, output_mode: str, tenant_id: str = "demo", hint: str = "", mime_type: str = "",
               verified_changes=None, field_facts=None, held_out_claims=None, conflicts=None, reconciliations=None,
               verification_receipts=None, warnings=None, field_map=None, context_response: dict | None = None,
               now: str = EPOCH) -> dict:
        if output_mode not in OUTPUT_MODES:
            raise ValueError(f"unknown output_mode {output_mode!r}; expected one of {OUTPUT_MODES}")

        # 1) freeze the native shape — original bytes + sha256 retained; NEVER mutated.
        contract = self._preserver.preserve(source, hint=hint, mime_type=mime_type)

        # 2) build the same-shape projection. Passthrough family returns original bytes; only the
        #    value-change family applies VERIFIED changes (each emits a NativeDiff entry).
        passthrough = output_mode in _PASSTHROUGH_MODES
        annotate = output_mode == "annotated_native"
        changes = None if passthrough else (verified_changes if output_mode in _VALUE_CHANGE_MODES else None)
        # compare wants the schema-preserving (possibly updated) view; build it as schema_preserving, not passthrough
        projection = self._projector.build(
            contract, output_mode=output_mode, passthrough=(passthrough and output_mode != "compare"),
            verified_changes=(verified_changes if output_mode == "compare" else changes),
            annotate=annotate, sidecar_ref=f".baltor/{contract.source_hash[:12]}.baltor.json", now=now)

        # 3) build the sidecar when the mode asks for it (governance power off to the side).
        sidecar = None
        if output_mode in _SIDECAR_MODES:
            sidecar = self._sidecar.build(
                contract=contract, output_mode=output_mode, tenant_id=tenant_id, field_facts=field_facts,
                held_out_claims=held_out_claims, conflicts=conflicts, reconciliations=reconciliations,
                verification_receipts=verification_receipts, warnings=warnings, field_map=field_map, now=now)

        # 4) advanced surface (ContextResponse) for baltor_native / dual — passed through from the caller.
        ctx_resp = context_response if output_mode in _CONTEXT_RESPONSE_MODES else None

        sidecar_dict = sidecar.to_dict() if sidecar else None
        sidecar_hash = (_hid("scH", sidecar_dict) if sidecar_dict else "")
        ctx_id = (ctx_resp.get("response_id", "") if ctx_resp else "")
        receipt = NativeExportReceipt(
            receipt_id=_hid("nexrcpt", {"sh": contract.source_hash, "mode": output_mode, "t": tenant_id,
                                        "out": projection.output_hash, "sc": sidecar_hash, "ctx": ctx_id}),
            source_hash=contract.source_hash, output_mode=output_mode, tenant_id=tenant_id,
            native_format=contract.format, output_hash=projection.output_hash, sidecar_hash=sidecar_hash,
            diff_id=projection.diff.diff_id, context_response_id=ctx_id,
            changed_field_count=len(projection.diff.changed_fields),
            held_out_count=(len(sidecar.held_out_claims) if sidecar else 0),
            byte_identical_to_source=projection.byte_identical_to_source,
            original_overwritten=False, created_at=now)

        result = {"output_mode": output_mode, "tenant_id": tenant_id,
                  "native_shape_contract": contract.to_dict(),
                  "native_output": {"format": projection.format, "bytes_sha256": projection.output_hash,
                                    "text": projection.output_text(), "byte_identical_to_source":
                                    projection.byte_identical_to_source, "annotations_added": projection.annotations_added},
                  "sidecar": sidecar_dict, "diff": projection.diff.to_dict(),
                  "context_response": ctx_resp, "receipt": receipt.to_dict(),
                  # the rollback target — the exact original, never overwritten.
                  "rollback": {"source_hash": contract.source_hash, "original_byte_size": len(contract.original_bytes)}}
        # compare mode: hand back original + updated side by side for the diff view.
        if output_mode == "compare":
            result["compare"] = {"original_text": contract.original_bytes.decode("utf-8", "replace"),
                                 "updated_text": projection.output_text(),
                                 "changed_fields": projection.diff.changed_fields}
        return result

    def rehydrate_original(self, contract) -> bytes:
        """Prove the source is recoverable: the frozen original bytes are always available unchanged."""
        return contract.original_bytes
