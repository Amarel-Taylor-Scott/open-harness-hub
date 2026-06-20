#!/usr/bin/env python3
"""src/baltor/native/sidecar_writer — build the governed SidecarOverlay that rides alongside the native output.

"Do not change my tables — give me the context elsewhere." The sidecar is where the governance power lives: it
maps each native field (JSON-pointer / CSV row.col / markdown anchor) back to its source handle + artifact id +
claim status, and carries the verified facts, the HELD-OUT claims (never erased — surfaced separately), the
conflicts, the reconciliations, the verification receipts, and the warnings.

LOSSLESS DISTILLATION: held_out_claims is the proof that "omitted from the native answer" != "deleted". Every
served field_fact carries a source_handle; every change is backed by a receipt. The sidecar always carries the
``source_hash`` of the frozen original so it can be re-attached to / rehydrated from the exact source bytes.

Deterministic + offline + stdlib only: ids are content-addressed; no RNG, no network.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


def _hid(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _handles(a: dict) -> list:
    """Source handle(s) for a governed artifact, tolerating either singular or plural key."""
    hs = a.get("source_handles")
    if hs:
        return list(hs)
    h = a.get("source_handle")
    return [h] if h else []


@dataclass
class SidecarOverlay:
    """The governed overlay for one native source. Pure projection — never holds the second copy of truth."""
    source_hash: str
    output_mode: str
    tenant_id: str
    native_format: str
    artifact_ids: list = field(default_factory=list)
    field_facts: list = field(default_factory=list)          # native_path -> verified fact + source handle
    held_out_claims: list = field(default_factory=list)      # surfaced separately; NEVER erased
    conflicts: list = field(default_factory=list)
    reconciliations: list = field(default_factory=list)
    verification_receipts: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    field_map: list = field(default_factory=list)            # native_path <-> source_handle <-> artifact <-> status
    created_at: str = ""
    sidecar_id: str = ""
    schema_version: str = "SidecarOverlay.v1"

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "sidecar_id": self.sidecar_id, "source_hash": self.source_hash,
                "output_mode": self.output_mode, "tenant_id": self.tenant_id, "native_format": self.native_format,
                "artifact_ids": list(self.artifact_ids), "field_facts": list(self.field_facts),
                "held_out_claims": list(self.held_out_claims), "conflicts": list(self.conflicts),
                "reconciliations": list(self.reconciliations), "verification_receipts": list(self.verification_receipts),
                "warnings": list(self.warnings), "field_map": list(self.field_map), "created_at": self.created_at}


class SidecarWriter:
    """Build a SidecarOverlay from the frozen shape contract + the governed pieces (facts/held-out/receipts)."""

    def build(self, *, contract, output_mode: str, tenant_id: str, field_facts=None, held_out_claims=None,
              conflicts=None, reconciliations=None, verification_receipts=None, warnings=None, field_map=None,
              now: str = "") -> SidecarOverlay:
        field_facts = list(field_facts or [])
        held_out_claims = list(held_out_claims or [])
        field_map = list(field_map or [])
        # the artifact id set is the union of everything the sidecar references (lineage for rehydration)
        artifact_ids = sorted({a["artifact_id"] for a in field_facts + held_out_claims if a.get("artifact_id")}
                              | {m["artifact_id"] for m in field_map if m.get("artifact_id")})
        body = {"sh": contract.source_hash, "mode": output_mode, "t": tenant_id,
                "facts": sorted(f.get("artifact_id", "") for f in field_facts),
                "held": sorted(h.get("artifact_id", "") for h in held_out_claims)}
        sidecar = SidecarOverlay(
            source_hash=contract.source_hash, output_mode=output_mode, tenant_id=tenant_id,
            native_format=contract.format, artifact_ids=artifact_ids, field_facts=field_facts,
            held_out_claims=held_out_claims, conflicts=list(conflicts or []),
            reconciliations=list(reconciliations or []), verification_receipts=list(verification_receipts or []),
            warnings=list(warnings or []), field_map=field_map, created_at=now,
            sidecar_id=_hid("sidecar", body))
        return sidecar

    @staticmethod
    def field_fact(native_path: str, *, artifact, receipt_id: str = "", claim_status: str = "fact") -> dict:
        """A single verified-fact overlay row: which native field, what value, backed by which source handle."""
        hs = _handles(artifact)
        return {"native_path": native_path, "artifact_id": artifact.get("artifact_id", ""),
                "source_handle": hs[0] if hs else "", "source_handles": hs,
                "claim_status": artifact.get("claim_status", claim_status),
                "object": str(artifact.get("object", artifact.get("value", ""))),
                "content_hash": artifact.get("content_hash", ""), "verification_receipt_id": receipt_id}

    @staticmethod
    def held_out(artifact, *, reason: str) -> dict:
        """A held-out claim row — surfaced separately, never erased (lossless)."""
        hs = _handles(artifact)
        return {"artifact_id": artifact.get("artifact_id", ""), "reason": reason,
                "claim_status": artifact.get("claim_status", ""), "source_handle": hs[0] if hs else "",
                "source_handles": hs, "object": str(artifact.get("object", artifact.get("text", "")))}

    @staticmethod
    def map_row(native_path: str, *, source_handle: str, artifact_id: str = "", claim_status: str = "") -> dict:
        """One native_path <-> source_handle <-> artifact <-> claim_status mapping row (the field_map)."""
        return {"native_path": native_path, "source_handle": source_handle, "artifact_id": artifact_id,
                "claim_status": claim_status}
