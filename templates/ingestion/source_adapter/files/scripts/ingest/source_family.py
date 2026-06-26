#!/usr/bin/env python3
"""scripts.ingest.{{source_family}} — governed source adapter for {{title}} behind one SourceAdapterPort.

GENERATED STUB (standard.source_adapter). This normalizes {{source_type}} payloads into the SAME governed
artifact chain (source_record -> source_field -> atomic_fact / narrative_allegation) used by every other
source, so it flows through the existing decompose -> ledger -> vector -> conflict -> reconcile -> verify ->
optimize -> consumption path. No raw source becomes truth; an unavailable parser returns an explicit
NON-CONSUMABLE reason + the stored raw artifact.

Deterministic + offline: content hashes are content-addressed (same payload -> same artifacts); stdlib only.
TODO(stub): implement `ingest` against the real {{source_type}} payload shape, then delete the NotImplemented
guard. Until then `check_{{source_family}}_adapter.py --self-test` FAILS on purpose.
"""
from __future__ import annotations

import hashlib
import json

SOURCE_TYPE = "{{source_type}}"
PARSER_PROVIDER = "{{parser_provider}}"

#: field names treated as free-text narrative (-> held-out allegations), not promotable structured facts.
NARRATIVE_FIELDS = {"narrative", "note", "notes", "description", "comment", "body", "message", "text", "summary"}
_NARRATIVE_LEN = 120  # a long string value is treated as narrative even if the field name is unknown


def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def _is_narrative(field: str, value) -> bool:
    return isinstance(value, str) and (field.lower() in NARRATIVE_FIELDS or len(value) > _NARRATIVE_LEN)


def _artifact(at: str, *, handle: str, value, tenant_id: str, scope: str, source_id: str, parent: str,
              claim_status: str = "", promotion_eligible: bool = False) -> dict:
    h = _hash({"h": handle, "v": value})
    return {"artifact_id": f"{at.split('_')[0]}-{h}", "artifact_type": at, "claim_status": claim_status,
            "promotion_eligible": promotion_eligible, "source_handle": handle, "content_hash": h,
            "parent_artifact_id": parent, "tenant_id": tenant_id, "scope": scope, "source_id": source_id,
            "value": value, "object": str(value)}


class {{source_family}}Adapter:
    """A SourceAdapter (structural): exposes source_type, parser_provider, ingest(...)."""

    source_type = SOURCE_TYPE
    parser_provider = PARSER_PROVIDER

    def ingest(self, payload, *, tenant_id: str, source_id: str, scope: str, authority: str) -> dict:
        # TODO(stub): replace this guard with real {{source_type}} normalization (see source_adapters.py).
        raise NotImplementedError(
            "{{source_family}}Adapter.ingest is a generated stub — implement {{source_type}} normalization"
        )

    def non_consumable(self, *, source_id: str, reason: str, raw) -> dict:
        """Honest boundary: parser unavailable -> NON-CONSUMABLE + stored raw artifact, never a fake result."""
        return {"consumable": False, "reason": reason, "source_id": source_id,
                "raw_artifact": _artifact("source_record", handle=f"raw:{source_id}", value=raw,
                                          tenant_id="", scope="global_public", source_id=source_id, parent="")}
