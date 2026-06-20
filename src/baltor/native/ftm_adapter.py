#!/usr/bin/env python3
"""src/baltor/native/ftm_adapter — interoperate with the FollowTheMoney (FtM) entity schema at the EDGES, the same
way okf_adapter does for OKF: map a governed Baltor entity record → an FtM EntityProxy ({id, schema, properties}),
WITHOUT making FtM our core object. FtM is a projection (like OKF / PROV-JSON / OpenLineage), not the source of truth.

FtM is the canonical, Aleph-loadable entity schema used across investigative/compliance tooling (OpenSanctions,
ICIJ, Aleph). It is MIT-licensed and — critically — the *schema* is usable without the library (the upstream lib
needs PyICU, which won't build on every box). So we adopt the schema with a pure-Python serializer and let our
assurance (verified source-authority, freshness, receipts, topics promoted only from governed evidence) ride above
it. Imported from the DueCare entity-intelligence reference (2026-06): "we use the schema; lib optional".

Deterministic + offline + stdlib only. id = ``lei-<LEI>`` when a canonical LEI is present (the global join key),
else ``dc-<sha1>`` of the canonical record. Topics are promoted CONSERVATIVELY (only from governed flags), never
guessed. serves_truth is always False — a schema projection never serves truth.
"""
from __future__ import annotations

import hashlib
import json

#: Baltor entity_type -> FtM schema (real FtM schemata). Unknown types fall back to the LegalEntity base.
SCHEMA_FOR_TYPE = {
    "company": "Company", "recruitment_agency": "Company", "employer": "Company", "microfinance": "Company",
    "contractor": "Company", "sponsor": "Company", "vessel_operator": "Company",
    "person": "Person", "representative": "Person", "officer": "Person", "individual": "Person",
    "organization": "Organization", "ngo": "Organization", "support_org": "Organization", "union": "Organization",
    "government_body": "PublicBody", "regulator": "PublicBody", "public_body": "PublicBody",
    "vessel": "Vessel", "ship": "Vessel",
    "legal_entity": "LegalEntity",
}
_DEFAULT_SCHEMA = "LegalEntity"

#: governed Baltor record field -> FtM property name (verified against upstream FtM YAMLs; see the DueCare dump §5).
PROP_MAP = {
    "name": "name", "aliases": "alias", "address": "address", "publisher": "publisher", "source": "publisher",
    "country": "country", "jurisdiction": "jurisdiction", "lei": "leiCode", "license_number": "licenseNumber",
    "registration_number": "registrationNumber", "reg_no": "registrationNumber", "tax_number": "taxNumber",
    "status": "status", "sector": "sector", "industry": "sector",
}
#: governed flag -> FtM topic, mapped CONSERVATIVELY (only these three; never guess a topic from free text).
TOPIC_MAP = {"sanctioned": "sanction", "sanction": "sanction", "debarred": "debarment", "debarment": "debarment",
             "forced_labor": "export.control", "export_control": "export.control"}

SERVES_TRUTH = False


def _sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _as_list(v) -> list:
    if v is None or v == "":
        return []
    return [str(x) for x in v] if isinstance(v, (list, tuple)) else [str(v)]


def schema_for(entity_type: str) -> str:
    return SCHEMA_FOR_TYPE.get((entity_type or "").strip().lower(), _DEFAULT_SCHEMA)


def _topics(record: dict) -> list:
    """Promote topics ONLY from governed flags (record['flags'] / explicit topic keys) — never inferred from text.
    Order-preserving (flags-list order, then boolean topic keys) so the proxy is deterministic."""
    out = []
    ordered = _as_list(record.get("flags")) + [k for k in TOPIC_MAP if record.get(k) is True]
    for f in ordered:
        t = TOPIC_MAP.get(str(f).strip().lower())
        if t and t not in out:
            out.append(t)
    return out


def to_entity_proxy(record: dict, *, entity_type: str | None = None) -> dict:
    """Map a governed entity record → an FtM EntityProxy {id, schema, properties:{prop:[values]}}. Aleph-loadable."""
    etype = entity_type if entity_type is not None else record.get("entity_type", "")
    schema = schema_for(etype)
    props: dict[str, list] = {}
    for field, ftm_prop in PROP_MAP.items():
        vals = _as_list(record.get(field))
        if vals:
            props.setdefault(ftm_prop, [])
            for v in vals:
                if v not in props[ftm_prop]:
                    props[ftm_prop].append(v)
    topics = _topics(record)
    if topics:
        props["topics"] = topics
    lei = (record.get("lei") or "").strip()
    if lei:
        ident = f"lei-{lei}"
    else:
        ident = "dc-" + _sha1(json.dumps({"schema": schema, "props": props}, sort_keys=True))
    return {"id": ident, "schema": schema, "properties": props, "serves_truth": SERVES_TRUTH}


def to_ftm(records: list[dict]) -> list[dict]:
    """Map a list of governed records → FtM EntityProxies (the Aleph bulk-load shape)."""
    return [to_entity_proxy(r) for r in records]
