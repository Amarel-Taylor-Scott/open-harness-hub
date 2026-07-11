#!/usr/bin/env python3
"""scripts.domain_fmt_domain_messages — WORKABLE (proven + TYPED) deterministic SHAPE leaves for domain-message formats.

ADD-ONLY parallel path (its OWN shard file). It IMPORTS the shared machinery, never edits it:
  * `run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt` from `scripts.mutator_registry` — the proof-runner EXECUTES
    each pure mutator against a synthetic fixture and flips serves_truth false->true ONLY on a PASSING executed proof;
  * `canonicalize_edge` from `scripts.build_edge_type_retrofit` — folds each leaf's logical edge labels to canonical
    type_ids so every proven leaf is also TYPED (input_edge_type_id + output_edge_type_id) and can chain.

Covers parse / extract / validate / emit / checksum SHAPES (SYNTHETIC fixtures, NO real PII/PAN/SSN/secrets) for:
  EDI X12 segment · HL7 v2 segment (healthcare ADMIN: PID demographics/MSH only — never clinical-risk, never insurance)
  · FHIR resource field (ADMIN: resourceType/id/identifier shapes) · FIX tag · ISO 20022 XML element · syslog line
  (RFC3164 PRI + RFC5424 header) · Common Log Format · W3C extended log. All validators operate on the SHAPE only.

DOMAIN LAWS honored: NO insurance primitives (any domain); healthcare = ADMIN only (demographic/identifier shapes, no
clinical or risk fields); synthetic/public shapes only. NETWORK/EFFECTFUL capabilities (FHIR server GET, HL7 MLLP send,
X12 trading-partner submit, remote syslog forward, LLM field extraction) are NEVER run through the proof runner and
NEVER serve_truth — they are declared as GATED EFFECT candidates (candidate=true, serves_truth=false, effect,
proof_obligation) in a SEPARATE section of the shard, with SEPARATE honest counts.

Deterministic + offline: no network, no LLM, no wall-clock, no RNG (fixed literal manifest timestamp; stable string
seeds only). CLI: --self-test | --write.

Register tuple for the shared proof suite (REPORT ONLY — this module does NOT self-register):
    ("_repos/shared-backend-components/scripts/domain_fmt_domain_messages.py", "domain_fmt_domain_messages")
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY / flexible-multi-path).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

DOMAIN = "fmt_domain_messages"
_FIXED_UTC = "2026-07-03"  # fixed literal timestamp — NO wall-clock (repo law: deterministic + offline)

OUT_DIR = _resource("data") / "dev-intel" / "domain_primitives"
OUT_JSONL = OUT_DIR / "domain_fmt_domain_messages.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_fmt_domain_messages.json"


# ── PURE deterministic mutators, contract (payload, **kwargs) -> (output, receipt). Domain-prefixed (`fdm_`) so they
#    never collide with existing registry entries; registered via setdefault (idempotent, never overwrites). ──

# EDI X12 segment (elements separated by '*', first element is the segment id) — synthetic NM1 name/id shape.
def fdm_x12_segment_parse(seg: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    parts = seg.split("*")
    out = {"segment_id": parts[0], "elements": parts[1:]}
    return out, _receipt("fdm_x12_segment_parse", before=seg, after=out, lossless=True, note="X12 segment -> {segment_id, elements}; fdm_x12_segment_emit restores")


def fdm_x12_segment_emit(parsed: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "*".join([parsed["segment_id"], *parsed["elements"]])
    return out, _receipt("fdm_x12_segment_emit", before=parsed, after=out, lossless=True, note="{segment_id, elements} -> X12 segment string")


def fdm_x12_segment_id(seg: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = seg.split("*")[0]
    return out, _receipt("fdm_x12_segment_id", before=seg, after=out, lossless=False, note="extract X12 segment id (head element)")


def fdm_x12_element_at(seg: str, idx: int = 0, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = seg.split("*")[1:][idx]
    return out, _receipt("fdm_x12_element_at", before=seg, after=out, lossless=False, note=f"X12 data element at index {idx} (id excluded)")


def fdm_x12_element_count(seg: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = len(seg.split("*")) - 1
    return out, _receipt("fdm_x12_element_count", before=seg, after=out, lossless=False, note="count of X12 data elements (id excluded)")


# HL7 v2 segment (fields separated by '|', first field is the segment name) — healthcare ADMIN: PID demographics only.
def fdm_hl7_segment_parse(seg: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    parts = seg.split("|")
    out = {"segment": parts[0], "fields": parts[1:]}
    return out, _receipt("fdm_hl7_segment_parse", before=seg, after=out, lossless=True, note="HL7 v2 segment -> {segment, fields}; fdm_hl7_segment_emit restores")


def fdm_hl7_segment_emit(parsed: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "|".join([parsed["segment"], *parsed["fields"]])
    return out, _receipt("fdm_hl7_segment_emit", before=parsed, after=out, lossless=True, note="{segment, fields} -> HL7 v2 segment string")


def fdm_hl7_segment_name(seg: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = seg.split("|")[0]
    return out, _receipt("fdm_hl7_segment_name", before=seg, after=out, lossless=False, note="extract HL7 segment name (head field)")


def fdm_hl7_field_at(seg: str, idx: int = 0, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = seg.split("|")[1:][idx]
    return out, _receipt("fdm_hl7_field_at", before=seg, after=out, lossless=False, note=f"HL7 field at index {idx} (name excluded)")


def fdm_hl7_component_split(field: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = field.split("^")
    return out, _receipt("fdm_hl7_component_split", before=field, after=out, lossless=True, note="HL7 field -> component list (split '^')")


# FHIR resource field (ADMIN shapes only: resourceType / id / identifier).
def fdm_fhir_resource_type(resource_json: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.loads(resource_json).get("resourceType", "")
    return out, _receipt("fdm_fhir_resource_type", before=resource_json, after=out, lossless=False, note="extract FHIR resourceType (admin)")


def fdm_fhir_field_extract(resource_json: str, field: str = "id", **_kw: Any) -> tuple[Any, dict[str, Any]]:
    out = json.loads(resource_json).get(field)
    return out, _receipt("fdm_fhir_field_extract", before=resource_json, after=out, lossless=False, note=f"extract FHIR admin field {field!r}")


def fdm_fhir_identifier_first_value(resource_json: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    ids = json.loads(resource_json).get("identifier", [])
    out = ids[0].get("value", "") if ids else ""
    return out, _receipt("fdm_fhir_identifier_first_value", before=resource_json, after=out, lossless=False, note="first FHIR identifier.value (admin shape)")


def fdm_fhir_validate_shape(resource_json: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    obj = json.loads(resource_json)
    rt = obj.get("resourceType")
    valid = isinstance(rt, str) and bool(rt)
    out = {"valid": valid, "resource_type": rt if valid else None}
    return out, _receipt("fdm_fhir_validate_shape", before=resource_json, after=out, lossless=False, note="validate FHIR shape: resourceType is a non-empty string")


# FIX (tag=value pairs; SOH shown as '|' in synthetic fixtures).
def fdm_fix_parse(msg: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {}
    for pair in msg.split("|"):
        if pair:
            k, v = pair.split("=", 1)
            out[k] = v
    return out, _receipt("fdm_fix_parse", before=msg, after=out, lossless=True, note="FIX message -> ordered {tag:value}; fdm_fix_emit restores")


def fdm_fix_emit(tags: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "|".join(f"{k}={v}" for k, v in tags.items())
    return out, _receipt("fdm_fix_emit", before=tags, after=out, lossless=True, note="{tag:value} -> FIX message string")


def fdm_fix_tag_value(msg: str, tag: str = "35", **_kw: Any) -> tuple[str, dict[str, Any]]:
    val = ""
    for pair in msg.split("|"):
        if pair and pair.split("=", 1)[0] == tag:
            val = pair.split("=", 1)[1]
            break
    return val, _receipt("fdm_fix_tag_value", before=msg, after=val, lossless=False, note=f"extract FIX tag {tag}")


def fdm_fix_msg_type(msg: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    val, _ = fdm_fix_tag_value(msg, tag="35")
    return val, _receipt("fdm_fix_msg_type", before=msg, after=val, lossless=False, note="extract FIX MsgType (tag 35)")


def fdm_fix_checksum(body: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    total = sum(ord(c) for c in body) % 256
    out = f"{total:03d}"
    return out, _receipt("fdm_fix_checksum", before=body, after=out, lossless=False, note="FIX checksum: sum(bytes) mod 256 as 3 digits (deterministic)")


# ISO 20022 XML element (single-attribute synthetic shape) — payment amount/currency shape, NOT insurance.
_ISO_RE = re.compile(r'^<(?P<tag>[A-Za-z][\w.-]*)(?P<attrs>(?:\s+[\w.:-]+="[^"]*")*)\s*>(?P<text>.*)</(?P=tag)>$')
_ATTR_RE = re.compile(r'(?P<k>[\w.:-]+)="(?P<v>[^"]*)"')


def fdm_iso20022_element_parse(elem: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    m = _ISO_RE.match(elem.strip())
    if not m:
        raise ValueError("unparseable ISO 20022 element")
    attrs = {a.group("k"): a.group("v") for a in _ATTR_RE.finditer(m.group("attrs"))}
    out = {"tag": m.group("tag"), "attrs": attrs, "text": m.group("text")}
    return out, _receipt("fdm_iso20022_element_parse", before=elem, after=out, lossless=True, note="ISO 20022 element -> {tag, attrs, text}; fdm_iso20022_element_emit restores")


def fdm_iso20022_element_emit(parsed: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    attrstr = "".join(f' {k}="{v}"' for k, v in parsed["attrs"].items())
    out = f'<{parsed["tag"]}{attrstr}>{parsed["text"]}</{parsed["tag"]}>'
    return out, _receipt("fdm_iso20022_element_emit", before=parsed, after=out, lossless=True, note="{tag, attrs, text} -> ISO 20022 element string")


def fdm_iso20022_element_tag(elem: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    m = _ISO_RE.match(elem.strip())
    out = m.group("tag") if m else ""
    return out, _receipt("fdm_iso20022_element_tag", before=elem, after=out, lossless=False, note="extract ISO 20022 element tag")


def fdm_iso20022_attr_value(elem: str, attr: str = "Ccy", **_kw: Any) -> tuple[str, dict[str, Any]]:
    m = _ISO_RE.match(elem.strip())
    attrs = {a.group("k"): a.group("v") for a in _ATTR_RE.finditer(m.group("attrs"))} if m else {}
    out = attrs.get(attr, "")
    return out, _receipt("fdm_iso20022_attr_value", before=elem, after=out, lossless=False, note=f"extract ISO 20022 attribute {attr!r}")


# syslog — RFC 3164 PRI decomposition (facility*8 + severity) + RFC 5424 header parse.
def fdm_syslog_pri_parse(pri: str, **_kw: Any) -> tuple[dict[str, int], dict[str, Any]]:
    n = int(pri.strip().lstrip("<").rstrip(">"))
    out = {"pri": n, "facility": n // 8, "severity": n % 8}
    return out, _receipt("fdm_syslog_pri_parse", before=pri, after=out, lossless=True, note="syslog PRI -> {pri, facility, severity}")


def fdm_syslog_facility(pri: int, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = int(pri) // 8
    return out, _receipt("fdm_syslog_facility", before=pri, after=out, lossless=False, note="syslog facility = PRI // 8")


def fdm_syslog_severity(pri: int, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = int(pri) % 8
    return out, _receipt("fdm_syslog_severity", before=pri, after=out, lossless=False, note="syslog severity = PRI mod 8")


_SYSLOG5424_RE = re.compile(
    r"^<(?P<pri>\d{1,3})>(?P<version>\d+) (?P<timestamp>\S+) (?P<host>\S+) (?P<app>\S+) (?P<procid>\S+) (?P<msgid>\S+)")


def fdm_syslog5424_header_parse(line: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    m = _SYSLOG5424_RE.match(line)
    if not m:
        raise ValueError("unparseable RFC5424 header")
    out = m.groupdict()
    return out, _receipt("fdm_syslog5424_header_parse", before=line, after=out, lossless=False, note="RFC5424 syslog header -> {pri,version,timestamp,host,app,procid,msgid}")


# Common Log Format (Apache NCSA).
_CLF_RE = re.compile(r'^(?P<host>\S+) (?P<ident>\S+) (?P<authuser>\S+) \[(?P<timestamp>[^\]]+)\] "(?P<request>[^"]*)" (?P<status>\S+) (?P<bytes>\S+)$')


def fdm_clf_parse(line: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    m = _CLF_RE.match(line)
    if not m:
        raise ValueError("unparseable CLF line")
    out = m.groupdict()
    return out, _receipt("fdm_clf_parse", before=line, after=out, lossless=False, note="Common Log Format line -> record fields")


def fdm_clf_status(line: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    m = _CLF_RE.match(line)
    out = m.group("status") if m else ""
    return out, _receipt("fdm_clf_status", before=line, after=out, lossless=False, note="extract CLF HTTP status code")


def fdm_clf_request_method(line: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    m = _CLF_RE.match(line)
    req = m.group("request") if m else ""
    out = req.split(" ")[0] if req else ""
    return out, _receipt("fdm_clf_request_method", before=line, after=out, lossless=False, note="extract CLF HTTP request method")


def fdm_clf_bytes(line: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    m = _CLF_RE.match(line)
    out = m.group("bytes") if m else ""
    return out, _receipt("fdm_clf_bytes", before=line, after=out, lossless=False, note="extract CLF response byte count")


# W3C extended log (directive '#Fields:' header + space-separated rows).
def fdm_w3c_fields_parse(directive: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = directive.split(":", 1)[1].split()
    return out, _receipt("fdm_w3c_fields_parse", before=directive, after=out, lossless=True, note="W3C '#Fields:' directive -> ordered field-name list")


def fdm_w3c_row_zip(row: str, fields: list[str] | None = None, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    fields = fields or []
    out = dict(zip(fields, row.split(" ")))
    return out, _receipt("fdm_w3c_row_zip", before=row, after=out, lossless=False, note="zip a W3C log row against a field-name list -> record")


def fdm_w3c_field_count(directive: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = len(directive.split(":", 1)[1].split())
    return out, _receipt("fdm_w3c_field_count", before=directive, after=out, lossless=False, note="count W3C declared fields")


#: new pure mutators to plug into the shared registry (idempotent setdefault — never overwrites an existing entry)
_NEW_MUTATORS = {
    "fdm_x12_segment_parse": fdm_x12_segment_parse, "fdm_x12_segment_emit": fdm_x12_segment_emit,
    "fdm_x12_segment_id": fdm_x12_segment_id, "fdm_x12_element_at": fdm_x12_element_at,
    "fdm_x12_element_count": fdm_x12_element_count,
    "fdm_hl7_segment_parse": fdm_hl7_segment_parse, "fdm_hl7_segment_emit": fdm_hl7_segment_emit,
    "fdm_hl7_segment_name": fdm_hl7_segment_name, "fdm_hl7_field_at": fdm_hl7_field_at,
    "fdm_hl7_component_split": fdm_hl7_component_split,
    "fdm_fhir_resource_type": fdm_fhir_resource_type, "fdm_fhir_field_extract": fdm_fhir_field_extract,
    "fdm_fhir_identifier_first_value": fdm_fhir_identifier_first_value, "fdm_fhir_validate_shape": fdm_fhir_validate_shape,
    "fdm_fix_parse": fdm_fix_parse, "fdm_fix_emit": fdm_fix_emit, "fdm_fix_tag_value": fdm_fix_tag_value,
    "fdm_fix_msg_type": fdm_fix_msg_type, "fdm_fix_checksum": fdm_fix_checksum,
    "fdm_iso20022_element_parse": fdm_iso20022_element_parse, "fdm_iso20022_element_emit": fdm_iso20022_element_emit,
    "fdm_iso20022_element_tag": fdm_iso20022_element_tag, "fdm_iso20022_attr_value": fdm_iso20022_attr_value,
    "fdm_syslog_pri_parse": fdm_syslog_pri_parse, "fdm_syslog_facility": fdm_syslog_facility,
    "fdm_syslog_severity": fdm_syslog_severity, "fdm_syslog5424_header_parse": fdm_syslog5424_header_parse,
    "fdm_clf_parse": fdm_clf_parse, "fdm_clf_status": fdm_clf_status,
    "fdm_clf_request_method": fdm_clf_request_method, "fdm_clf_bytes": fdm_clf_bytes,
    "fdm_w3c_fields_parse": fdm_w3c_fields_parse, "fdm_w3c_row_zip": fdm_w3c_row_zip,
    "fdm_w3c_field_count": fdm_w3c_field_count,
}


def register_new_mutators() -> None:
    """Plug the domain's pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── proven-deterministic leaves: each a REAL SHAPE capability with a synthetic fixture + expected (+ inverse where a
#    roundtrip holds). spec fields: id, mutator, fixture, expected, args?, inverse?, format, input_edge, output_edge ──
LEAF_SPECS: list[dict[str, Any]] = [
    # EDI X12 segment
    {"id": "prim:leaf:fdm_x12_segment_parse", "mutator": "fdm_x12_segment_parse", "format": "edi_x12_segment",
     "fixture": "NM1*IL*1*DOE*JOHN", "expected": {"segment_id": "NM1", "elements": ["IL", "1", "DOE", "JOHN"]},
     "inverse": "fdm_x12_segment_emit", "input_edge": "X12Segment", "output_edge": "X12ParsedSegment"},
    {"id": "prim:leaf:fdm_x12_segment_emit", "mutator": "fdm_x12_segment_emit", "format": "edi_x12_segment",
     "fixture": {"segment_id": "NM1", "elements": ["IL", "1"]}, "expected": "NM1*IL*1",
     "inverse": "fdm_x12_segment_parse", "input_edge": "X12ParsedSegment", "output_edge": "X12Segment"},
    {"id": "prim:leaf:fdm_x12_segment_id", "mutator": "fdm_x12_segment_id", "format": "edi_x12_segment",
     "fixture": "NM1*IL*1*DOE", "expected": "NM1", "input_edge": "X12Segment", "output_edge": "SegmentId"},
    {"id": "prim:leaf:fdm_x12_element_at", "mutator": "fdm_x12_element_at", "format": "edi_x12_segment",
     "fixture": "NM1*IL*1*DOE", "expected": "1", "args": {"idx": 1}, "input_edge": "X12Segment", "output_edge": "ElementValue"},
    {"id": "prim:leaf:fdm_x12_element_count", "mutator": "fdm_x12_element_count", "format": "edi_x12_segment",
     "fixture": "NM1*IL*1*DOE", "expected": 3, "input_edge": "X12Segment", "output_edge": "Count"},

    # HL7 v2 segment (healthcare ADMIN — PID demographics/identifier shape)
    {"id": "prim:leaf:fdm_hl7_segment_parse", "mutator": "fdm_hl7_segment_parse", "format": "hl7v2_segment",
     "fixture": "PID|1||MRN00123||DOE^JOHN", "expected": {"segment": "PID", "fields": ["1", "", "MRN00123", "", "DOE^JOHN"]},
     "inverse": "fdm_hl7_segment_emit", "input_edge": "Hl7Segment", "output_edge": "Hl7ParsedSegment"},
    {"id": "prim:leaf:fdm_hl7_segment_emit", "mutator": "fdm_hl7_segment_emit", "format": "hl7v2_segment",
     "fixture": {"segment": "PID", "fields": ["1", "", "MRN00123"]}, "expected": "PID|1||MRN00123",
     "inverse": "fdm_hl7_segment_parse", "input_edge": "Hl7ParsedSegment", "output_edge": "Hl7Segment"},
    {"id": "prim:leaf:fdm_hl7_segment_name", "mutator": "fdm_hl7_segment_name", "format": "hl7v2_segment",
     "fixture": "PID|1||MRN00123", "expected": "PID", "input_edge": "Hl7Segment", "output_edge": "SegmentName"},
    {"id": "prim:leaf:fdm_hl7_field_at", "mutator": "fdm_hl7_field_at", "format": "hl7v2_segment",
     "fixture": "PID|1||MRN00123", "expected": "MRN00123", "args": {"idx": 2}, "input_edge": "Hl7Segment", "output_edge": "FieldValue"},
    {"id": "prim:leaf:fdm_hl7_component_split", "mutator": "fdm_hl7_component_split", "format": "hl7v2_segment",
     "fixture": "DOE^JOHN^A", "expected": ["DOE", "JOHN", "A"], "input_edge": "Hl7Field", "output_edge": "ComponentList"},

    # FHIR resource field (ADMIN shapes)
    {"id": "prim:leaf:fdm_fhir_resource_type", "mutator": "fdm_fhir_resource_type", "format": "fhir_resource_field",
     "fixture": '{"resourceType": "Patient", "id": "p1"}', "expected": "Patient",
     "input_edge": "FhirResourceJson", "output_edge": "ResourceType"},
    {"id": "prim:leaf:fdm_fhir_field_extract", "mutator": "fdm_fhir_field_extract", "format": "fhir_resource_field",
     "fixture": '{"resourceType": "Practitioner", "id": "pr7"}', "expected": "pr7", "args": {"field": "id"},
     "input_edge": "FhirResourceJson", "output_edge": "FieldValue"},
    {"id": "prim:leaf:fdm_fhir_identifier_first_value", "mutator": "fdm_fhir_identifier_first_value", "format": "fhir_resource_field",
     "fixture": '{"resourceType": "Organization", "identifier": [{"system": "urn:oid:2.16.840.1.113883.4.6", "value": "1234567893"}]}',
     "expected": "1234567893", "input_edge": "FhirResourceJson", "output_edge": "IdentifierValue"},
    {"id": "prim:leaf:fdm_fhir_validate_shape", "mutator": "fdm_fhir_validate_shape", "format": "fhir_resource_field",
     "fixture": '{"resourceType": "Location", "id": "loc9"}', "expected": {"valid": True, "resource_type": "Location"},
     "input_edge": "FhirResourceJson", "output_edge": "ValidationResult"},

    # FIX tag
    {"id": "prim:leaf:fdm_fix_parse", "mutator": "fdm_fix_parse", "format": "fix_tag",
     "fixture": "8=FIX.4.2|9=65|35=A", "expected": {"8": "FIX.4.2", "9": "65", "35": "A"},
     "inverse": "fdm_fix_emit", "input_edge": "FixMessage", "output_edge": "FixTagMap"},
    {"id": "prim:leaf:fdm_fix_emit", "mutator": "fdm_fix_emit", "format": "fix_tag",
     "fixture": {"8": "FIX.4.2", "35": "D"}, "expected": "8=FIX.4.2|35=D",
     "inverse": "fdm_fix_parse", "input_edge": "FixTagMap", "output_edge": "FixMessage"},
    {"id": "prim:leaf:fdm_fix_tag_value", "mutator": "fdm_fix_tag_value", "format": "fix_tag",
     "fixture": "8=FIX.4.4|35=D|49=SENDER", "expected": "SENDER", "args": {"tag": "49"},
     "input_edge": "FixMessage", "output_edge": "TagValue"},
    {"id": "prim:leaf:fdm_fix_msg_type", "mutator": "fdm_fix_msg_type", "format": "fix_tag",
     "fixture": "8=FIX.4.4|35=8|150=0", "expected": "8", "input_edge": "FixMessage", "output_edge": "MsgType"},
    {"id": "prim:leaf:fdm_fix_checksum", "mutator": "fdm_fix_checksum", "format": "fix_tag",
     "fixture": "8=FIX.4.2|9=5|35=0|", "expected": f"{sum(ord(c) for c in '8=FIX.4.2|9=5|35=0|') % 256:03d}",
     "input_edge": "FixMessage", "output_edge": "Checksum"},

    # ISO 20022 element
    {"id": "prim:leaf:fdm_iso20022_element_parse", "mutator": "fdm_iso20022_element_parse", "format": "iso20022_element",
     "fixture": '<Amt Ccy="USD">100.00</Amt>', "expected": {"tag": "Amt", "attrs": {"Ccy": "USD"}, "text": "100.00"},
     "inverse": "fdm_iso20022_element_emit", "input_edge": "Iso20022Element", "output_edge": "Iso20022ParsedElement"},
    {"id": "prim:leaf:fdm_iso20022_element_emit", "mutator": "fdm_iso20022_element_emit", "format": "iso20022_element",
     "fixture": {"tag": "Amt", "attrs": {"Ccy": "EUR"}, "text": "42.50"}, "expected": '<Amt Ccy="EUR">42.50</Amt>',
     "inverse": "fdm_iso20022_element_parse", "input_edge": "Iso20022ParsedElement", "output_edge": "Iso20022Element"},
    {"id": "prim:leaf:fdm_iso20022_element_tag", "mutator": "fdm_iso20022_element_tag", "format": "iso20022_element",
     "fixture": '<InstdAmt Ccy="GBP">10</InstdAmt>', "expected": "InstdAmt", "input_edge": "Iso20022Element", "output_edge": "ElementTag"},
    {"id": "prim:leaf:fdm_iso20022_attr_value", "mutator": "fdm_iso20022_attr_value", "format": "iso20022_element",
     "fixture": '<Amt Ccy="JPY">500</Amt>', "expected": "JPY", "args": {"attr": "Ccy"},
     "input_edge": "Iso20022Element", "output_edge": "AttrValue"},

    # syslog
    {"id": "prim:leaf:fdm_syslog_pri_parse", "mutator": "fdm_syslog_pri_parse", "format": "syslog_line",
     "fixture": "<34>", "expected": {"pri": 34, "facility": 4, "severity": 2},
     "input_edge": "SyslogPri", "output_edge": "SyslogPriParts"},
    {"id": "prim:leaf:fdm_syslog_facility", "mutator": "fdm_syslog_facility", "format": "syslog_line",
     "fixture": 165, "expected": 20, "input_edge": "SyslogPriValue", "output_edge": "FacilityCode"},
    {"id": "prim:leaf:fdm_syslog_severity", "mutator": "fdm_syslog_severity", "format": "syslog_line",
     "fixture": 165, "expected": 5, "input_edge": "SyslogPriValue", "output_edge": "SeverityCode"},
    {"id": "prim:leaf:fdm_syslog5424_header_parse", "mutator": "fdm_syslog5424_header_parse", "format": "syslog_line",
     "fixture": "<165>1 2003-10-11T22:14:15Z host01 evntslog 8710 ID47 msg",
     "expected": {"pri": "165", "version": "1", "timestamp": "2003-10-11T22:14:15Z", "host": "host01",
                  "app": "evntslog", "procid": "8710", "msgid": "ID47"},
     "input_edge": "Syslog5424Line", "output_edge": "Syslog5424Header"},

    # Common Log Format
    {"id": "prim:leaf:fdm_clf_parse", "mutator": "fdm_clf_parse", "format": "common_log_format",
     "fixture": '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326',
     "expected": {"host": "127.0.0.1", "ident": "-", "authuser": "frank", "timestamp": "10/Oct/2000:13:55:36 -0700",
                  "request": "GET /apache_pb.gif HTTP/1.0", "status": "200", "bytes": "2326"},
     "input_edge": "CommonLogLine", "output_edge": "CommonLogRecord"},
    {"id": "prim:leaf:fdm_clf_status", "mutator": "fdm_clf_status", "format": "common_log_format",
     "fixture": '10.0.0.1 - - [10/Oct/2000:13:55:36 -0700] "GET / HTTP/1.1" 404 512', "expected": "404",
     "input_edge": "CommonLogLine", "output_edge": "StatusCode"},
    {"id": "prim:leaf:fdm_clf_request_method", "mutator": "fdm_clf_request_method", "format": "common_log_format",
     "fixture": '10.0.0.1 - - [10/Oct/2000:13:55:36 -0700] "POST /submit HTTP/1.1" 200 0', "expected": "POST",
     "input_edge": "CommonLogLine", "output_edge": "HttpMethod"},
    {"id": "prim:leaf:fdm_clf_bytes", "mutator": "fdm_clf_bytes", "format": "common_log_format",
     "fixture": '10.0.0.1 - - [10/Oct/2000:13:55:36 -0700] "GET /x HTTP/1.1" 200 8188', "expected": "8188",
     "input_edge": "CommonLogLine", "output_edge": "ByteCount"},

    # W3C extended log
    {"id": "prim:leaf:fdm_w3c_fields_parse", "mutator": "fdm_w3c_fields_parse", "format": "w3c_extended_log",
     "fixture": "#Fields: date time cs-method sc-status", "expected": ["date", "time", "cs-method", "sc-status"],
     "input_edge": "W3cFieldsDirective", "output_edge": "FieldNameList"},
    {"id": "prim:leaf:fdm_w3c_row_zip", "mutator": "fdm_w3c_row_zip", "format": "w3c_extended_log",
     "fixture": "2000-10-10 13:55:36 GET 200", "args": {"fields": ["date", "time", "cs-method", "sc-status"]},
     "expected": {"date": "2000-10-10", "time": "13:55:36", "cs-method": "GET", "sc-status": "200"},
     "input_edge": "W3cLogLine", "output_edge": "W3cRecord"},
    {"id": "prim:leaf:fdm_w3c_field_count", "mutator": "fdm_w3c_field_count", "format": "w3c_extended_log",
     "fixture": "#Fields: date time cs-method sc-status cs-uri-stem", "expected": 5,
     "input_edge": "W3cFieldsDirective", "output_edge": "Count"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven-deterministic)
NEGATIVE_SPEC: dict[str, Any] = {
    "id": "prim:leaf:fdm_WRONG_expected", "mutator": "fdm_x12_segment_id", "format": "edi_x12_segment",
    "fixture": "NM1*IL*1", "expected": "WRONG", "input_edge": "X12Segment", "output_edge": "SegmentId"}


# ── GATED-EFFECT candidates: NETWORK / EFFECTFUL capabilities. NEVER run through the proof runner, NEVER serve_truth.
#    Each declares effect + proof_obligation (a live integration test with a credential) + typed edges. ──
GATED_EFFECT_SPECS: list[dict[str, Any]] = [
    {"id": "prim:gated:fdm_fhir_server_read", "capability": "FHIR RESTful read (GET /Patient/{id}) from a FHIR server",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox FHIR endpoint with a bearer credential",
     "input_edge": "FhirResourceRequest", "output_edge": "FhirResourceJson", "format": "fhir_resource_field"},
    {"id": "prim:gated:fdm_hl7_mllp_send", "capability": "send an HL7 v2 message over MLLP to an interface engine",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox MLLP listener with host/port credential",
     "input_edge": "Hl7Segment", "output_edge": "MllpAck", "format": "hl7v2_segment"},
    {"id": "prim:gated:fdm_x12_partner_submit", "capability": "submit an X12 interchange to a trading-partner AS2/API endpoint",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox trading-partner endpoint with a credential",
     "input_edge": "X12Segment", "output_edge": "PartnerAck", "format": "edi_x12_segment"},
    {"id": "prim:gated:fdm_syslog_remote_forward", "capability": "forward a syslog line to a remote collector (UDP/TCP)",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox syslog collector with host/port credential",
     "input_edge": "Syslog5424Line", "output_edge": "ForwardAck", "format": "syslog_line"},
    {"id": "prim:gated:fdm_llm_field_extract", "capability": "LLM-based free-text field extraction from an unstructured message",
     "effect": "model_call", "proof_obligation": "live model call with an API credential; output is candidate advice, never truth",
     "input_edge": "RawMessageText", "output_edge": "ExtractedFields", "format": "fmt_domain_messages"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    return run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )


def prove_all() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Run every declared deterministic leaf through the imported executed-proof runner. Returns [(spec, receipt), ...]."""
    return [(s, _prove_one(s)) for s in LEAF_SPECS]


def build_proven_rows() -> list[dict[str, Any]]:
    """Persist-ready rows for leaves whose executed proof PASSED — TYPED via canonicalize_edge (workable == typed)."""
    rows: list[dict[str, Any]] = []
    for spec, receipt in prove_all():
        if receipt["serves_truth"] is not True:
            continue  # a failing / wrong-expected leaf stays candidate and is NOT persisted (the gate is the point)
        rows.append({
            "primitive_id": receipt["primitive_id"],
            "mutator": receipt["mutator"],
            "domain": DOMAIN,
            "format": spec["format"],
            "row_section": "proven_deterministic",
            "candidate": False,
            "serves_truth": True,
            "verification_level": "L7_executed_proof",
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
            "has_inverse": spec.get("inverse"),
            "proofs": [p["name"] for p in receipt["proofs"] if p["passed"]],
        })
    return rows


def build_gated_rows() -> list[dict[str, Any]]:
    """Gated-effect candidate rows — NEVER proven, NEVER serves_truth; typed so they still declare their edges."""
    rows: list[dict[str, Any]] = []
    for spec in GATED_EFFECT_SPECS:
        rows.append({
            "primitive_id": spec["id"],
            "domain": DOMAIN,
            "format": spec["format"],
            "row_section": "gated_effect_candidate",
            "capability": spec["capability"],
            "candidate": True,
            "serves_truth": False,
            "effect": spec["effect"],
            "proof_obligation": spec["proof_obligation"],
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
        })
    return rows


def build_manifest(proven: list[dict[str, Any]], gated: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "domain_primitive_shard_manifest",
        "domain": DOMAIN,
        "generator": "scripts/domain_fmt_domain_messages.py",
        "generated_utc": _FIXED_UTC,
        "formats_covered": sorted({s["format"] for s in LEAF_SPECS}),
        # SEPARATE, honest counts (proven-deterministic vs gated-effect candidate).
        "defined_deterministic_count": len(LEAF_SPECS),
        "proven_deterministic": len(proven),
        "typed": len(typed),
        "gated_effect_candidates": len(gated),
        "gated_effect_by_effect": {e: sum(1 for r in gated if r["effect"] == e)
                                   for e in sorted({r["effect"] for r in gated})},
        "verification_level": "L7_executed_proof",
        "proven_primitive_ids": sorted(r["primitive_id"] for r in proven),
        "gated_effect_primitive_ids": sorted(r["primitive_id"] for r in gated),
        "note": "proven_deterministic rows: serves_truth=true set ONLY by an executed passing proof (run_primitive_proof, "
                "imported from scripts/mutator_registry.py); every row TYPED via canonicalize_edge (imported from "
                "scripts/build_edge_type_retrofit.py). gated_effect_candidate rows: network/effectful capabilities are "
                "NEVER proven and stay candidate/serves_truth=false with an effect + proof_obligation. Synthetic/public "
                "shapes only; NO insurance; healthcare = ADMIN only. Counts are separate and honest.",
    }


def write_shard() -> dict[str, Any]:
    proven = build_proven_rows()
    gated = build_gated_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Both sections written to the SAME shard, each row self-labels via row_section.
    all_rows = proven + gated
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in all_rows), encoding="utf-8")
    manifest = build_manifest(proven, gated)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    proven = prove_all()
    rows = build_proven_rows()
    gated = build_gated_rows()
    ids = [r["primitive_id"] for r in rows]
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_by_id = {r["primitive_id"]: r for (s, r) in proven}

    # deliberately-wrong leaf must stay candidate (proof gate is real) — and never enter the proven section
    wrong = _prove_one(NEGATIVE_SPEC)
    # a second wrong path: an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:fdm_EXEC_ERROR", "fdm_fix_parse", object(), "irrelevant")

    manifest = build_manifest(rows, gated)
    valid_effects = {"network_read", "network_write", "model_call", "file_write"}

    checks: list[tuple[str, bool]] = [
        (">=25 deterministic leaves declared", len(LEAF_SPECS) >= 25),
        ("unique proven primitive ids", len(set(ids)) == len(ids)),
        (">=25 leaves PROVE serves_truth=true via an executed proof", len(rows) >= 25),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for (_s, r) in proven if r["serves_truth"] is True)),
        ("EVERY proven row carries non-null input+output edge type ids", len(typed) == len(rows)),
        ("manifest typed == proven_deterministic", manifest["typed"] == manifest["proven_deterministic"]),
        ("all 8 target formats are covered", set(manifest["formats_covered"]) == {
            "edi_x12_segment", "hl7v2_segment", "fhir_resource_field", "fix_tag", "iso20022_element",
            "syslog_line", "common_log_format", "w3c_extended_log"}),
        ("roundtrip-inverse pairs actually ran + PASSED a roundtrip proof", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in proven_by_id[s["id"]]["proofs"])
            for s in roundtrip_specs)),
        ("domain stamped on every proven row", all(r["domain"] == DOMAIN for r in rows)),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in build_proven_rows()] == [json.dumps(r, sort_keys=True) for r in rows]),
        # gated-effect law: EVERY gated row is candidate / serves_truth=false with a valid effect + proof_obligation
        (">=1 gated-effect candidate declared", len(gated) >= 1),
        ("EVERY gated-effect row is candidate + serves_truth=false",
         all(r["candidate"] is True and r["serves_truth"] is False for r in gated)),
        ("EVERY gated-effect row has a valid effect + non-empty proof_obligation",
         all(r["effect"] in valid_effects and isinstance(r["proof_obligation"], str) and r["proof_obligation"]
             for r in gated)),
        ("EVERY gated-effect row is TYPED (input+output edge type ids)",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in gated)),
        ("no gated-effect id leaked into the proven section", not (set(r["primitive_id"] for r in gated) & set(ids))),
        # the proof gate is real
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT persisted as proven", NEGATIVE_SPEC["id"] not in set(ids)),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - domain_fmt_domain_messages:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - domain_fmt_domain_messages: {len(rows)} WORKABLE (proven + TYPED) deterministic SHAPE leaves for "
          f"'{DOMAIN}' (serves_truth=true, L7_executed_proof; typed=={len(rows)}) across 8 message formats; "
          f"{len(roundtrip_specs)} inverse pairs proven reversible via roundtrip; {len(gated)} network/effectful "
          "capabilities declared as GATED-EFFECT candidates (serves_truth=false, effect + proof_obligation). "
          "A deliberately-wrong leaf and an un-runnable fixture correctly stay candidate. Synthetic shapes; no insurance.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        manifest = write_shard()
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
