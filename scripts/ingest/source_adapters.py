#!/usr/bin/env python3
"""scripts.ingest.source_adapters — governed multi-source ingestion behind ONE SourceAdapterPort.

Every source type (api/structured-record, csv, json/webhook, …) normalizes into the SAME governed artifacts —
source_record → source_field → atomic_fact / narrative_allegation — with per-type source handles, content
hashes, tenant scope, and lineage, so any source flows through the existing decomposition → ledger → vector →
graph → conflict → reconcile → verify → optimize → consumption path. No raw source becomes truth: structured
official fields are promotion-eligible facts; free-text becomes held-out allegations; a source whose parser is
unavailable (e.g. PDF) returns an explicit NON-CONSUMABLE reason + the stored raw artifact, never a fake result.

Deterministic + offline: content hashes are content-addressed; same payload → same artifacts. stdlib only.
"""
from __future__ import annotations

import csv as _csv
import hashlib
import io
import json
from typing import Protocol, runtime_checkable

#: field names whose values are treated as free-text narrative (→ held-out allegations), not structured facts.
NARRATIVE_FIELDS = {"narrative", "consumer_complaint_narrative", "note", "notes", "description", "comment",
                    "comments", "body", "message", "text", "summary", "remarks"}
_NARRATIVE_LEN = 120  # a long string value is treated as narrative even if the field name isn't known


def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def _is_narrative(field: str, value) -> bool:
    return isinstance(value, str) and (field.lower() in NARRATIVE_FIELDS or len(value) > _NARRATIVE_LEN)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in str(text).replace("\n", " ").split(".") if s.strip()]


def _artifact(at: str, *, handle: str, value, tenant_id: str, scope: str, source_id: str, parent: str,
              claim_status: str = "", promotion_eligible: bool = False) -> dict:
    return {"artifact_id": f"{at.split('_')[0]}-" + _hash({"h": handle, "v": value}), "artifact_type": at,
            "claim_status": claim_status, "promotion_eligible": promotion_eligible, "source_handle": handle,
            "content_hash": _hash({"h": handle, "v": value}), "parent_artifact_id": parent,
            "tenant_id": tenant_id, "scope": scope, "source_id": source_id, "value": value,
            "object": str(value), "text": str(value)}


def _base_handle(tenant_id: str, scope: str, source_id: str) -> str:
    return (f"ctx://tenant/{tenant_id}/source/{source_id}" if scope != "global_public"
            else f"ctx://public/source/{source_id}")


def _decompose_field(field: str, value, *, base: str, sep: str, tenant_id: str, scope: str, source_id: str,
                     parent: str, out: list) -> None:
    """One field → a source_field + either an atomic_fact (structured) or N narrative_allegations (free-text)."""
    fh = f"{base}#{sep}{field}"
    out.append(_artifact("source_field", handle=fh, value=value, tenant_id=tenant_id, scope=scope,
                         source_id=source_id, parent=parent))
    if _is_narrative(field, value):
        for i, sent in enumerate(_sentences(value)):
            out.append(_artifact("narrative_allegation", handle=f"{fh}.s{i}", value=sent, tenant_id=tenant_id,
                                 scope=scope, source_id=source_id, parent=fh,
                                 claim_status="unverified_allegation", promotion_eligible=False))
    else:
        out.append(_artifact("atomic_fact", handle=fh, value=value, tenant_id=tenant_id, scope=scope,
                             source_id=source_id, parent=fh, claim_status="fact", promotion_eligible=True))


def _flatten_json(obj, prefix: str = "") -> list[tuple]:
    """Flatten to JSON-pointer (path, scalar_value) pairs. Lists index by position."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += _flatten_json(v, f"{prefix}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += _flatten_json(v, f"{prefix}/{i}")
    else:
        out.append((prefix, obj))
    return out


@runtime_checkable
class SourceAdapter(Protocol):
    source_type: str
    parser_provider: str
    def ingest(self, payload, *, tenant_id: str, source_id: str, scope: str, authority: str) -> dict: ...


def _result(adapter, *, tenant_id, source_id, scope, authority, raw, artifacts) -> dict:
    src = {"artifact_id": "source-" + _hash(raw), "artifact_type": "source_record", "claim_status": "",
           "source_handle": _base_handle(tenant_id, scope, source_id), "content_hash": _hash(raw),
           "parent_artifact_id": "", "tenant_id": tenant_id, "scope": scope, "source_id": source_id,
           "source_type": adapter.source_type, "authority": authority, "is_source_root": True}
    return {"consumable": True, "source_type": adapter.source_type, "parser_provider": adapter.parser_provider,
            "source_id": source_id, "tenant_id": tenant_id, "scope": scope, "authority": authority,
            "content_hash": _hash(raw), "source_artifacts": [src], "artifacts": [src] + artifacts}


class ApiStructuredAdapter:
    source_type = "api"
    parser_provider = "structured_record"

    def ingest(self, payload, *, tenant_id, source_id, scope, authority) -> dict:
        records = payload if isinstance(payload, list) else [payload]
        base = _base_handle(tenant_id, scope, source_id)
        arts: list[dict] = []
        for ridx, rec in enumerate(records):
            rid = str(rec.get("id") or rec.get("complaint_id") or ridx)
            rh = f"{base}/record/{rid}"
            arts.append(_artifact("source_record", handle=rh, value=rid, tenant_id=tenant_id, scope=scope,
                                  source_id=source_id, parent=base))
            for field, value in rec.items():
                _decompose_field(field, value, base=rh, sep="", tenant_id=tenant_id, scope=scope,
                                 source_id=source_id, parent=rh, out=arts)
        return _result(self, tenant_id=tenant_id, source_id=source_id, scope=scope, authority=authority,
                       raw={"records": records}, artifacts=arts)


class CsvAdapter:
    source_type = "csv"
    parser_provider = "csv"

    def ingest(self, payload, *, tenant_id, source_id, scope, authority) -> dict:
        text = payload.decode("utf-8") if isinstance(payload, bytes) else str(payload)
        base = _base_handle(tenant_id, scope, source_id)
        rows = list(_csv.DictReader(io.StringIO(text)))
        arts: list[dict] = []
        for n, row in enumerate(rows):
            rh = f"{base}#row.{n}"
            arts.append(_artifact("source_record", handle=rh, value=n, tenant_id=tenant_id, scope=scope,
                                  source_id=source_id, parent=base))
            for col, value in row.items():
                ch = f"{base}#row.{n}.col.{col}"
                arts.append(_artifact("source_field", handle=ch, value=value, tenant_id=tenant_id, scope=scope,
                                      source_id=source_id, parent=rh))
                if _is_narrative(col, value):
                    for i, sent in enumerate(_sentences(value)):
                        arts.append(_artifact("narrative_allegation", handle=f"{ch}.s{i}", value=sent,
                                              tenant_id=tenant_id, scope=scope, source_id=source_id, parent=ch,
                                              claim_status="unverified_allegation", promotion_eligible=False))
                else:
                    arts.append(_artifact("atomic_fact", handle=ch, value=value, tenant_id=tenant_id, scope=scope,
                                          source_id=source_id, parent=ch, claim_status="fact", promotion_eligible=True))
        return _result(self, tenant_id=tenant_id, source_id=source_id, scope=scope, authority=authority,
                       raw={"csv": text}, artifacts=arts)


class JsonAdapter:
    source_type = "json"
    parser_provider = "json"

    def ingest(self, payload, *, tenant_id, source_id, scope, authority) -> dict:
        obj = json.loads(payload) if isinstance(payload, (str, bytes)) else payload
        base = _base_handle(tenant_id, scope, source_id)
        arts: list[dict] = [_artifact("source_record", handle=f"{base}#/", value="root", tenant_id=tenant_id,
                                      scope=scope, source_id=source_id, parent=base)]
        for pointer, value in _flatten_json(obj):
            fh = f"{base}#{pointer}"
            field = pointer.rsplit("/", 1)[-1]
            arts.append(_artifact("source_field", handle=fh, value=value, tenant_id=tenant_id, scope=scope,
                                  source_id=source_id, parent=f"{base}#/"))
            if _is_narrative(field, value):
                for i, sent in enumerate(_sentences(value)):
                    arts.append(_artifact("narrative_allegation", handle=f"{fh}.s{i}", value=sent, tenant_id=tenant_id,
                                          scope=scope, source_id=source_id, parent=fh,
                                          claim_status="unverified_allegation", promotion_eligible=False))
            elif not isinstance(value, str) or value:
                arts.append(_artifact("atomic_fact", handle=fh, value=value, tenant_id=tenant_id, scope=scope,
                                      source_id=source_id, parent=fh, claim_status="fact", promotion_eligible=True))
        return _result(self, tenant_id=tenant_id, source_id=source_id, scope=scope, authority=authority,
                       raw={"json": obj}, artifacts=arts)


class UnavailableParserAdapter:
    """For source types whose real parser is a cataloged candidate (e.g. PDF Docling). Stores the raw payload as
    a source artifact but returns NON-CONSUMABLE — never a faked parse / extracted claim."""

    def __init__(self, source_type: str, parser_provider: str) -> None:
        self.source_type = source_type
        self.parser_provider = parser_provider

    def ingest(self, payload, *, tenant_id, source_id, scope, authority) -> dict:
        raw = payload.decode("utf-8", "ignore") if isinstance(payload, bytes) else str(payload)
        src = {"artifact_id": "source-" + _hash(raw), "artifact_type": "source_record",
               "source_handle": _base_handle(tenant_id, scope, source_id), "content_hash": _hash(raw),
               "tenant_id": tenant_id, "scope": scope, "source_id": source_id, "source_type": self.source_type,
               "is_source_root": True}
        return {"consumable": False,
                "reason": f"parser_unavailable: {self.parser_provider} is a cataloged candidate (no local extractor); "
                          f"raw {self.source_type} stored as a source artifact, but no claim is extracted or served",
                "source_type": self.source_type, "parser_provider": self.parser_provider, "source_id": source_id,
                "source_artifacts": [src], "artifacts": [src]}


#: the source-adapter registry (source_type → adapter). New source types register here + in contract_registry.json#source_types.
REGISTRY: dict = {a.source_type: a for a in (ApiStructuredAdapter(), CsvAdapter(), JsonAdapter())}
REGISTRY["webhook"] = REGISTRY["json"]
REGISTRY["pdf"] = UnavailableParserAdapter("pdf", "parser.docling@candidate")
REGISTRY["html"] = UnavailableParserAdapter("html", "parser.html@candidate")


def normalize(source_type: str, payload, *, tenant_id: str, source_id: str, scope: str = "global_public",
              authority: str = "unknown") -> dict:
    """Route a source through its adapter (SourceAdapterPort). Unknown type → non-consumable, raw stored only."""
    adapter = REGISTRY.get(source_type)
    if adapter is None:
        raw = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True, default=str)
        return {"consumable": False, "reason": f"unknown source_type {source_type!r}; raw stored, not served",
                "source_type": source_type, "source_id": source_id,
                "source_artifacts": [{"artifact_id": "source-" + _hash(raw), "artifact_type": "source_record",
                                      "content_hash": _hash(raw), "source_id": source_id, "tenant_id": tenant_id,
                                      "scope": scope, "is_source_root": True}], "artifacts": []}
    return adapter.ingest(payload, tenant_id=tenant_id, source_id=source_id, scope=scope, authority=authority)
