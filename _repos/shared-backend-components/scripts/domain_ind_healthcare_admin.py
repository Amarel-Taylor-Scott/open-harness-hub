#!/usr/bin/env python3
"""scripts.domain_ind_healthcare_admin — WORKABLE (proven + TYPED) deterministic SHAPE leaves for healthcare ADMIN.

ADD-ONLY parallel path (its OWN shard file). It IMPORTS the shared machinery, never edits it:
  * `run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt` from `scripts.mutator_registry` — the proof-runner EXECUTES
    each pure mutator against a synthetic fixture and flips serves_truth false->true ONLY on a PASSING executed proof;
  * `canonicalize_edge` from `scripts.build_edge_type_retrofit` — folds each leaf's logical edge labels to canonical
    type_ids so every proven leaf is also TYPED (input_edge_type_id + output_edge_type_id) and can chain.

Covers parse / extract / validate / emit / checksum SHAPES for healthcare ADMINISTRATIVE identifiers and messages
(SYNTHETIC fixtures, NO real PII / MRN / SSN / secrets):
  NPI Luhn check-digit + validate · ICD-10-CM code shape (category/subcategory/normalize) · CPT code shape + category
  classify · HCPCS Level-II shape · FHIR administrative field extract (Patient.name / identifier / gender / birthDate)
  + FHIR token roundtrip · HL7 v2 PID segment split/join + XPN name parse · CMS place-of-service code shape.

DOMAIN LAWS honored: NO insurance primitives (any domain — no 270/271 eligibility, no claims/adjudication, no payer
logic); healthcare = ADMIN ONLY (NPI / ICD / CPT / HCPCS / FHIR-admin / HL7-PID shapes) — NEVER clinical-risk,
diagnosis inference, or coverage decisions; SYNTHETIC / public code SHAPES only (MRNs, names, dates are fabricated;
validators operate on SHAPE, never on real PII/PAN/SSN/secrets). NETWORK / EFFECTFUL healthcare-admin capabilities
(NPPES registry lookup, FHIR server read/create/update, HL7 ADT send, terminology-server $validate-code) are NEVER
run through the proof runner and NEVER serve_truth — they are declared as GATED EFFECT candidates (candidate=true,
serves_truth=false, effect, proof_obligation) in a SEPARATE section of the shard, with SEPARATE honest counts.

Deterministic + offline: no network, no LLM, no wall-clock, no RNG (fixed literal manifest timestamp; stable string
seeds only). CLI: --self-test | --write.

Register tuple for the shared proof suite (REPORT ONLY — this module does NOT self-register):
    ("_repos/shared-backend-components/scripts/domain_ind_healthcare_admin.py", "domain_ind_healthcare_admin")
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

DOMAIN = "ind_healthcare_admin"
_FIXED_UTC = "2026-07-03"  # fixed literal timestamp — NO wall-clock (repo law: deterministic + offline)

#: NPI check digit uses the Luhn algorithm over the 9-digit identifier prefixed with the ISO 7812 issuer prefix for
#: NPPES ("80840"). Public algorithm, not a secret. Source: CMS NPI check-digit specification.
_NPI_ISSUER_PREFIX = "80840"

OUT_DIR = _resource("data") / "dev-intel" / "domain_primitives"
OUT_JSONL = OUT_DIR / "domain_ind_healthcare_admin.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_ind_healthcare_admin.json"


# ── shared helpers (pure) ──
def _luhn_check_digit(payload_digits: str) -> int:
    """Standard Luhn check digit for a numeric payload string (double every 2nd digit from the right, sum, mod 10)."""
    total = 0
    for i, ch in enumerate(reversed(payload_digits)):
        d = int(ch)
        if i % 2 == 0:  # rightmost payload digit doubles (check digit will be appended to its right)
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return (10 - total % 10) % 10


# ── PURE deterministic mutators, contract (payload, **kwargs) -> (output, receipt). Domain-prefixed (`hca_`) so they
#    never collide with existing registry entries; registered via setdefault (idempotent, never overwrites). ──

# NPI — National Provider Identifier (10 digits, Luhn over 80840+first9). ADMIN identifier only.
def hca_npi_check_digit(nine_digits: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    if not (len(nine_digits) == 9 and nine_digits.isdigit()):
        raise ValueError("NPI check-digit input must be exactly 9 digits")
    out = str(_luhn_check_digit(_NPI_ISSUER_PREFIX + nine_digits))
    return out, _receipt("hca_npi_check_digit", before=nine_digits, after=out, lossless=False, note="9-digit NPI base -> Luhn check digit (over 80840 issuer prefix)")


def hca_npi_validate(npi10: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = len(npi10) == 10 and npi10.isdigit() and _luhn_check_digit(_NPI_ISSUER_PREFIX + npi10[:9]) == int(npi10[9])
    out = {"valid": bool(valid)}
    return out, _receipt("hca_npi_validate", before=npi10, after=out, lossless=False, note="validate 10-digit NPI SHAPE via Luhn check digit (synthetic)")


def hca_npi_normalize(raw: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = re.sub(r"\D", "", raw)
    return out, _receipt("hca_npi_normalize", before=raw, after=out, lossless=False, note="strip non-digits from a formatted NPI string")


# ICD-10-CM diagnosis code SHAPE (admin coding artifact; no clinical inference performed).
_ICD10_RE = re.compile(r"^[A-TV-Z][0-9][0-9A-Z](\.[0-9A-Z]{1,4})?$")


def hca_icd10_validate_shape(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"valid": _ICD10_RE.match(code) is not None}
    return out, _receipt("hca_icd10_validate_shape", before=code, after=out, lossless=False, note="validate ICD-10-CM code SHAPE (letter, 2 alnum, optional .subcategory) — shape only, no clinical meaning")


def hca_icd10_category(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = code.split(".", 1)[0]
    return out, _receipt("hca_icd10_category", before=code, after=out, lossless=False, note="ICD-10 category = first 3 chars before the decimal")


def hca_icd10_subcategory(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = code.split(".", 1)[1] if "." in code else ""
    return out, _receipt("hca_icd10_subcategory", before=code, after=out, lossless=False, note="ICD-10 subcategory = chars after the decimal (empty if none)")


def hca_icd10_normalize(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = code.strip().upper()
    return out, _receipt("hca_icd10_normalize", before=code, after=out, lossless=False, note="ICD-10 normalize: strip + uppercase")


def hca_icd10_has_decimal(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"has_decimal": "." in code}
    return out, _receipt("hca_icd10_has_decimal", before=code, after=out, lossless=False, note="does the ICD-10 code carry a subcategory decimal?")


# CPT code SHAPE (procedure-coding artifact; admin). Cat I = 5 digits; Cat II = 4 digits + F; Cat III = 4 digits + T.
_CPT_RE = re.compile(r"^(\d{5}|\d{4}[FTU])$")


def hca_cpt_validate_shape(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"valid": _CPT_RE.match(code) is not None}
    return out, _receipt("hca_cpt_validate_shape", before=code, after=out, lossless=False, note="validate CPT code SHAPE (5 digits, or 4 digits + F/T/U) — shape only")


def hca_cpt_category_classify(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    if re.fullmatch(r"\d{5}", code):
        out = "I"
    elif re.fullmatch(r"\d{4}F", code):
        out = "II"
    elif re.fullmatch(r"\d{4}T", code):
        out = "III"
    else:
        out = "unknown"
    return out, _receipt("hca_cpt_category_classify", before=code, after=out, lossless=False, note="classify CPT category from SHAPE: 5-digit=I, 4d+F=II, 4d+T=III")


# HCPCS Level II SHAPE: one letter (A–V) + 4 digits.
_HCPCS_RE = re.compile(r"^[A-V][0-9]{4}$")


def hca_hcpcs_validate_shape(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"valid": _HCPCS_RE.match(code) is not None}
    return out, _receipt("hca_hcpcs_validate_shape", before=code, after=out, lossless=False, note="validate HCPCS Level-II code SHAPE (letter A-V + 4 digits)")


def hca_hcpcs_letter_prefix(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = code[:1]
    return out, _receipt("hca_hcpcs_letter_prefix", before=code, after=out, lossless=False, note="HCPCS Level-II letter prefix (category letter)")


# FHIR administrative field extraction (Patient resource ADMIN fields — name/identifier/gender/birthDate). SYNTHETIC.
def hca_fhir_patient_family_name(patient: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = (patient.get("name") or [{}])[0].get("family", "")
    return out, _receipt("hca_fhir_patient_family_name", before=patient, after=out, lossless=False, note="FHIR Patient.name[0].family (administrative)")


def hca_fhir_patient_given_name(patient: dict[str, Any], **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = list((patient.get("name") or [{}])[0].get("given", []))
    return out, _receipt("hca_fhir_patient_given_name", before=patient, after=out, lossless=False, note="FHIR Patient.name[0].given (administrative)")


def hca_fhir_human_name_format(human_name: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = " ".join(list(human_name.get("given", [])) + ([human_name["family"]] if human_name.get("family") else []))
    return out, _receipt("hca_fhir_human_name_format", before=human_name, after=out, lossless=False, note="FHIR HumanName -> 'given... family' display string")


def hca_fhir_patient_gender(patient: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = patient.get("gender", "")
    return out, _receipt("hca_fhir_patient_gender", before=patient, after=out, lossless=False, note="FHIR Patient.gender (administrative gender code)")


def hca_fhir_patient_birthdate(patient: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = patient.get("birthDate", "")
    return out, _receipt("hca_fhir_patient_birthdate", before=patient, after=out, lossless=False, note="FHIR Patient.birthDate (administrative)")


def hca_fhir_patient_identifier_value(patient: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = (patient.get("identifier") or [{}])[0].get("value", "")
    return out, _receipt("hca_fhir_patient_identifier_value", before=patient, after=out, lossless=False, note="FHIR Patient.identifier[0].value (synthetic MRN)")


def hca_fhir_patient_identifier_system(patient: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = (patient.get("identifier") or [{}])[0].get("system", "")
    return out, _receipt("hca_fhir_patient_identifier_system", before=patient, after=out, lossless=False, note="FHIR Patient.identifier[0].system")


def hca_fhir_identifier_to_token(identifier: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"{identifier.get('system', '')}|{identifier.get('value', '')}"
    return out, _receipt("hca_fhir_identifier_to_token", before=identifier, after=out, lossless=True, note="FHIR Identifier {system,value} -> 'system|value' search token; hca_fhir_identifier_from_token restores")


def hca_fhir_identifier_from_token(token: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    system, _, value = token.partition("|")
    out = {"system": system, "value": value}
    return out, _receipt("hca_fhir_identifier_from_token", before=token, after=out, lossless=True, note="FHIR 'system|value' token -> {system,value} Identifier")


# HL7 v2 PID segment SHAPE (synthetic patient-administration message). Field separator '|', component separator '^'.
def hca_hl7_segment_split(segment: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    out = segment.split("|")
    return out, _receipt("hca_hl7_segment_split", before=segment, after=out, lossless=True, note="HL7 v2 segment string -> list of fields (split '|'); hca_hl7_segment_join restores")


def hca_hl7_segment_join(fields: list[str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "|".join(fields)
    return out, _receipt("hca_hl7_segment_join", before=fields, after=out, lossless=True, note="HL7 v2 field list -> segment string (join '|')")


def hca_hl7_pid_field(segment: str, index: int = 0, **_kw: Any) -> tuple[str, dict[str, Any]]:
    fields = segment.split("|")
    out = fields[index] if 0 <= index < len(fields) else ""
    return out, _receipt("hca_hl7_pid_field", before=segment, after=out, lossless=False, note=f"extract HL7 PID field at index {index}")


def hca_hl7_pid_patient_id(segment: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    fields = segment.split("|")
    out = fields[3].split("^", 1)[0] if len(fields) > 3 else ""
    return out, _receipt("hca_hl7_pid_patient_id", before=segment, after=out, lossless=False, note="HL7 PID-3 first component = patient identifier (synthetic MRN)")


def hca_hl7_pid_patient_name(segment: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    fields = segment.split("|")
    out = fields[5] if len(fields) > 5 else ""
    return out, _receipt("hca_hl7_pid_patient_name", before=segment, after=out, lossless=False, note="HL7 PID-5 = patient name XPN component (synthetic)")


def hca_hl7_xpn_parse(xpn: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    comps = xpn.split("^")
    out = {"family": comps[0] if len(comps) > 0 else "",
           "given": comps[1] if len(comps) > 1 else "",
           "middle": comps[2] if len(comps) > 2 else ""}
    return out, _receipt("hca_hl7_xpn_parse", before=xpn, after=out, lossless=False, note="HL7 XPN 'family^given^middle' -> {family,given,middle}")


def hca_hl7_xpn_family(xpn: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = xpn.split("^", 1)[0]
    return out, _receipt("hca_hl7_xpn_family", before=xpn, after=out, lossless=False, note="HL7 XPN family (surname) component")


# CMS place-of-service (POS) code SHAPE — administrative 2-digit code.
def hca_pos_validate_shape(code: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"valid": len(code) == 2 and code.isdigit()}
    return out, _receipt("hca_pos_validate_shape", before=code, after=out, lossless=False, note="validate CMS place-of-service code SHAPE (2 digits)")


def hca_pos_normalize(code: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = re.sub(r"\D", "", code).zfill(2)[-2:]
    return out, _receipt("hca_pos_normalize", before=code, after=out, lossless=False, note="normalize POS code: strip non-digits, zero-pad to 2")


#: new pure mutators to plug into the shared registry (idempotent setdefault — never overwrites an existing entry)
_NEW_MUTATORS = {
    "hca_npi_check_digit": hca_npi_check_digit, "hca_npi_validate": hca_npi_validate, "hca_npi_normalize": hca_npi_normalize,
    "hca_icd10_validate_shape": hca_icd10_validate_shape, "hca_icd10_category": hca_icd10_category,
    "hca_icd10_subcategory": hca_icd10_subcategory, "hca_icd10_normalize": hca_icd10_normalize,
    "hca_icd10_has_decimal": hca_icd10_has_decimal,
    "hca_cpt_validate_shape": hca_cpt_validate_shape, "hca_cpt_category_classify": hca_cpt_category_classify,
    "hca_hcpcs_validate_shape": hca_hcpcs_validate_shape, "hca_hcpcs_letter_prefix": hca_hcpcs_letter_prefix,
    "hca_fhir_patient_family_name": hca_fhir_patient_family_name, "hca_fhir_patient_given_name": hca_fhir_patient_given_name,
    "hca_fhir_human_name_format": hca_fhir_human_name_format, "hca_fhir_patient_gender": hca_fhir_patient_gender,
    "hca_fhir_patient_birthdate": hca_fhir_patient_birthdate,
    "hca_fhir_patient_identifier_value": hca_fhir_patient_identifier_value,
    "hca_fhir_patient_identifier_system": hca_fhir_patient_identifier_system,
    "hca_fhir_identifier_to_token": hca_fhir_identifier_to_token,
    "hca_fhir_identifier_from_token": hca_fhir_identifier_from_token,
    "hca_hl7_segment_split": hca_hl7_segment_split, "hca_hl7_segment_join": hca_hl7_segment_join,
    "hca_hl7_pid_field": hca_hl7_pid_field, "hca_hl7_pid_patient_id": hca_hl7_pid_patient_id,
    "hca_hl7_pid_patient_name": hca_hl7_pid_patient_name, "hca_hl7_xpn_parse": hca_hl7_xpn_parse,
    "hca_hl7_xpn_family": hca_hl7_xpn_family,
    "hca_pos_validate_shape": hca_pos_validate_shape, "hca_pos_normalize": hca_pos_normalize,
}


def register_new_mutators() -> None:
    """Plug the domain's pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── proven-deterministic leaves: each a REAL SHAPE capability with a synthetic fixture + expected (+ inverse where a
#    roundtrip holds). spec fields: id, mutator, fixture, expected, args?, inverse?, format, input_edge, output_edge ──
LEAF_SPECS: list[dict[str, Any]] = [
    # NPI (National Provider Identifier) — synthetic; 1234567893 is the canonical Luhn-valid test NPI
    {"id": "prim:leaf:hca_npi_check_digit", "mutator": "hca_npi_check_digit", "format": "npi",
     "fixture": "123456789", "expected": "3", "input_edge": "NpiBaseDigits", "output_edge": "NpiCheckDigit"},
    {"id": "prim:leaf:hca_npi_validate", "mutator": "hca_npi_validate", "format": "npi",
     "fixture": "1234567893", "expected": {"valid": True}, "input_edge": "Npi", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:hca_npi_validate_bad", "mutator": "hca_npi_validate", "format": "npi",
     "fixture": "1234567890", "expected": {"valid": False}, "input_edge": "Npi", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:hca_npi_normalize", "mutator": "hca_npi_normalize", "format": "npi",
     "fixture": "1234-567-893", "expected": "1234567893", "input_edge": "NpiFormatted", "output_edge": "Npi"},

    # ICD-10-CM code shape (admin coding artifact)
    {"id": "prim:leaf:hca_icd10_validate_shape", "mutator": "hca_icd10_validate_shape", "format": "icd10_cm",
     "fixture": "E11.9", "expected": {"valid": True}, "input_edge": "Icd10Code", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:hca_icd10_validate_shape_bad", "mutator": "hca_icd10_validate_shape", "format": "icd10_cm",
     "fixture": "119.0", "expected": {"valid": False}, "input_edge": "Icd10Code", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:hca_icd10_category", "mutator": "hca_icd10_category", "format": "icd10_cm",
     "fixture": "E11.9", "expected": "E11", "input_edge": "Icd10Code", "output_edge": "Icd10Category"},
    {"id": "prim:leaf:hca_icd10_subcategory", "mutator": "hca_icd10_subcategory", "format": "icd10_cm",
     "fixture": "S52.501A", "expected": "501A", "input_edge": "Icd10Code", "output_edge": "Icd10Subcategory"},
    {"id": "prim:leaf:hca_icd10_normalize", "mutator": "hca_icd10_normalize", "format": "icd10_cm",
     "fixture": " e11.9 ", "expected": "E11.9", "input_edge": "Icd10CodeRaw", "output_edge": "Icd10Code"},
    {"id": "prim:leaf:hca_icd10_has_decimal", "mutator": "hca_icd10_has_decimal", "format": "icd10_cm",
     "fixture": "A00", "expected": {"has_decimal": False}, "input_edge": "Icd10Code", "output_edge": "BooleanFlag"},

    # CPT code shape
    {"id": "prim:leaf:hca_cpt_validate_shape", "mutator": "hca_cpt_validate_shape", "format": "cpt",
     "fixture": "99213", "expected": {"valid": True}, "input_edge": "CptCode", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:hca_cpt_validate_shape_bad", "mutator": "hca_cpt_validate_shape", "format": "cpt",
     "fixture": "9921", "expected": {"valid": False}, "input_edge": "CptCode", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:hca_cpt_category_classify_i", "mutator": "hca_cpt_category_classify", "format": "cpt",
     "fixture": "99213", "expected": "I", "input_edge": "CptCode", "output_edge": "CptCategory"},
    {"id": "prim:leaf:hca_cpt_category_classify_ii", "mutator": "hca_cpt_category_classify", "format": "cpt",
     "fixture": "0500F", "expected": "II", "input_edge": "CptCode", "output_edge": "CptCategory"},
    {"id": "prim:leaf:hca_cpt_category_classify_iii", "mutator": "hca_cpt_category_classify", "format": "cpt",
     "fixture": "0019T", "expected": "III", "input_edge": "CptCode", "output_edge": "CptCategory"},

    # HCPCS Level II code shape
    {"id": "prim:leaf:hca_hcpcs_validate_shape", "mutator": "hca_hcpcs_validate_shape", "format": "hcpcs",
     "fixture": "J1885", "expected": {"valid": True}, "input_edge": "HcpcsCode", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:hca_hcpcs_validate_shape_bad", "mutator": "hca_hcpcs_validate_shape", "format": "hcpcs",
     "fixture": "Z12", "expected": {"valid": False}, "input_edge": "HcpcsCode", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:hca_hcpcs_letter_prefix", "mutator": "hca_hcpcs_letter_prefix", "format": "hcpcs",
     "fixture": "J1885", "expected": "J", "input_edge": "HcpcsCode", "output_edge": "HcpcsCategoryLetter"},

    # FHIR administrative field extraction (synthetic Patient resource)
    {"id": "prim:leaf:hca_fhir_patient_family_name", "mutator": "hca_fhir_patient_family_name", "format": "fhir_administrative",
     "fixture": {"resourceType": "Patient", "name": [{"use": "official", "family": "Chalmers", "given": ["Peter", "James"]}]},
     "expected": "Chalmers", "input_edge": "FhirPatient", "output_edge": "FamilyName"},
    {"id": "prim:leaf:hca_fhir_patient_given_name", "mutator": "hca_fhir_patient_given_name", "format": "fhir_administrative",
     "fixture": {"resourceType": "Patient", "name": [{"family": "Chalmers", "given": ["Peter", "James"]}]},
     "expected": ["Peter", "James"], "input_edge": "FhirPatient", "output_edge": "GivenNameList"},
    {"id": "prim:leaf:hca_fhir_human_name_format", "mutator": "hca_fhir_human_name_format", "format": "fhir_administrative",
     "fixture": {"family": "Chalmers", "given": ["Peter", "James"]}, "expected": "Peter James Chalmers",
     "input_edge": "FhirHumanName", "output_edge": "DisplayName"},
    {"id": "prim:leaf:hca_fhir_patient_gender", "mutator": "hca_fhir_patient_gender", "format": "fhir_administrative",
     "fixture": {"resourceType": "Patient", "gender": "male"}, "expected": "male",
     "input_edge": "FhirPatient", "output_edge": "AdministrativeGender"},
    {"id": "prim:leaf:hca_fhir_patient_birthdate", "mutator": "hca_fhir_patient_birthdate", "format": "fhir_administrative",
     "fixture": {"resourceType": "Patient", "birthDate": "1974-12-25"}, "expected": "1974-12-25",
     "input_edge": "FhirPatient", "output_edge": "BirthDate"},
    {"id": "prim:leaf:hca_fhir_patient_identifier_value", "mutator": "hca_fhir_patient_identifier_value", "format": "fhir_administrative",
     "fixture": {"resourceType": "Patient", "identifier": [{"system": "urn:oid:1.2.36.146.595.217.0.1", "value": "MRN-000123"}]},
     "expected": "MRN-000123", "input_edge": "FhirPatient", "output_edge": "IdentifierValue"},
    {"id": "prim:leaf:hca_fhir_patient_identifier_system", "mutator": "hca_fhir_patient_identifier_system", "format": "fhir_administrative",
     "fixture": {"resourceType": "Patient", "identifier": [{"system": "urn:oid:1.2.36.146.595.217.0.1", "value": "MRN-000123"}]},
     "expected": "urn:oid:1.2.36.146.595.217.0.1", "input_edge": "FhirPatient", "output_edge": "IdentifierSystem"},
    {"id": "prim:leaf:hca_fhir_identifier_to_token", "mutator": "hca_fhir_identifier_to_token", "format": "fhir_administrative",
     "fixture": {"system": "urn:oid:1.2.36.146.595.217.0.1", "value": "MRN-000123"},
     "expected": "urn:oid:1.2.36.146.595.217.0.1|MRN-000123", "inverse": "hca_fhir_identifier_from_token",
     "input_edge": "FhirIdentifier", "output_edge": "FhirTokenSearch"},
    {"id": "prim:leaf:hca_fhir_identifier_from_token", "mutator": "hca_fhir_identifier_from_token", "format": "fhir_administrative",
     "fixture": "urn:oid:1.2.36.146.595.217.0.1|MRN-000123",
     "expected": {"system": "urn:oid:1.2.36.146.595.217.0.1", "value": "MRN-000123"},
     "inverse": "hca_fhir_identifier_to_token", "input_edge": "FhirTokenSearch", "output_edge": "FhirIdentifier"},

    # HL7 v2 PID segment (synthetic patient-administration message)
    {"id": "prim:leaf:hca_hl7_segment_split", "mutator": "hca_hl7_segment_split", "format": "hl7_pid",
     "fixture": "PID|1||MRN12345^^^HOSP^MR||DOE^JOHN^Q||19741225|M",
     "expected": ["PID", "1", "", "MRN12345^^^HOSP^MR", "", "DOE^JOHN^Q", "", "19741225", "M"],
     "inverse": "hca_hl7_segment_join", "input_edge": "Hl7Segment", "output_edge": "Hl7FieldList"},
    {"id": "prim:leaf:hca_hl7_segment_join", "mutator": "hca_hl7_segment_join", "format": "hl7_pid",
     "fixture": ["PID", "1", "", "MRN12345", "", "DOE^JOHN^Q"],
     "expected": "PID|1||MRN12345||DOE^JOHN^Q", "inverse": "hca_hl7_segment_split",
     "input_edge": "Hl7FieldList", "output_edge": "Hl7Segment"},
    {"id": "prim:leaf:hca_hl7_pid_field", "mutator": "hca_hl7_pid_field", "format": "hl7_pid",
     "fixture": "PID|1||MRN12345^^^HOSP^MR||DOE^JOHN^Q||19741225|M", "args": {"index": 7}, "expected": "19741225",
     "input_edge": "Hl7Segment", "output_edge": "Hl7Field"},
    {"id": "prim:leaf:hca_hl7_pid_patient_id", "mutator": "hca_hl7_pid_patient_id", "format": "hl7_pid",
     "fixture": "PID|1||MRN12345^^^HOSP^MR||DOE^JOHN^Q||19741225|M", "expected": "MRN12345",
     "input_edge": "Hl7Segment", "output_edge": "PatientIdentifier"},
    {"id": "prim:leaf:hca_hl7_pid_patient_name", "mutator": "hca_hl7_pid_patient_name", "format": "hl7_pid",
     "fixture": "PID|1||MRN12345^^^HOSP^MR||DOE^JOHN^Q||19741225|M", "expected": "DOE^JOHN^Q",
     "input_edge": "Hl7Segment", "output_edge": "Hl7XpnName"},
    {"id": "prim:leaf:hca_hl7_xpn_parse", "mutator": "hca_hl7_xpn_parse", "format": "hl7_pid",
     "fixture": "DOE^JOHN^Q", "expected": {"family": "DOE", "given": "JOHN", "middle": "Q"},
     "input_edge": "Hl7XpnName", "output_edge": "XpnNameParts"},
    {"id": "prim:leaf:hca_hl7_xpn_family", "mutator": "hca_hl7_xpn_family", "format": "hl7_pid",
     "fixture": "DOE^JOHN^Q", "expected": "DOE", "input_edge": "Hl7XpnName", "output_edge": "FamilyName"},

    # CMS place-of-service code shape
    {"id": "prim:leaf:hca_pos_validate_shape", "mutator": "hca_pos_validate_shape", "format": "place_of_service",
     "fixture": "11", "expected": {"valid": True}, "input_edge": "PlaceOfServiceCode", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:hca_pos_normalize", "mutator": "hca_pos_normalize", "format": "place_of_service",
     "fixture": "5", "expected": "05", "input_edge": "PlaceOfServiceCodeRaw", "output_edge": "PlaceOfServiceCode"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven-deterministic)
NEGATIVE_SPEC: dict[str, Any] = {
    "id": "prim:leaf:hca_WRONG_expected", "mutator": "hca_npi_validate", "format": "npi",
    "fixture": "1234567893", "expected": {"valid": False}, "input_edge": "Npi", "output_edge": "ValidationResult"}


# ── GATED-EFFECT candidates: NETWORK / EFFECTFUL healthcare-ADMIN capabilities. NEVER run through the proof runner,
#    NEVER serve_truth. Each declares effect + proof_obligation (a live integration test with a credential) + typed
#    edges. ALL are administrative (registry / directory / demographics / message routing) — NONE clinical or payer. ──
GATED_EFFECT_SPECS: list[dict[str, Any]] = [
    {"id": "prim:gated:hca_nppes_npi_lookup", "capability": "NPPES NPI registry lookup — resolve an NPI to public provider directory data",
     "effect": "network_read", "proof_obligation": "live integration test against the public NPPES registry API endpoint",
     "input_edge": "Npi", "output_edge": "ProviderDirectoryRecord", "format": "npi"},
    {"id": "prim:gated:hca_fhir_patient_read", "capability": "FHIR GET Patient/{id} — read an administrative Patient resource from a FHIR server",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox FHIR server with an access token",
     "input_edge": "FhirPatientId", "output_edge": "FhirPatient", "format": "fhir_administrative"},
    {"id": "prim:gated:hca_fhir_patient_create", "capability": "FHIR POST Patient — create an administrative Patient resource on a FHIR server",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox FHIR server with an access token",
     "input_edge": "FhirPatient", "output_edge": "FhirCreateResult", "format": "fhir_administrative"},
    {"id": "prim:gated:hca_fhir_patient_update", "capability": "FHIR PUT Patient/{id} — update an administrative Patient resource on a FHIR server",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox FHIR server with an access token",
     "input_edge": "FhirPatient", "output_edge": "FhirUpdateResult", "format": "fhir_administrative"},
    {"id": "prim:gated:hca_fhir_bundle_transaction_post", "capability": "FHIR POST Bundle (transaction) — submit an administrative resource bundle to a FHIR server",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox FHIR server with an access token",
     "input_edge": "FhirBundle", "output_edge": "FhirTransactionResult", "format": "fhir_administrative"},
    {"id": "prim:gated:hca_hl7_adt_send", "capability": "HL7 v2 ADT send — route an admit/discharge/transfer administrative message to an interface engine",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox HL7 MLLP interface engine endpoint",
     "input_edge": "Hl7Segment", "output_edge": "Hl7AckResult", "format": "hl7_pid"},
    {"id": "prim:gated:hca_terminology_validate_code", "capability": "Terminology server $validate-code — validate an ICD-10/CPT/HCPCS code against a live value set",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox FHIR terminology server with an access token",
     "input_edge": "Icd10Code", "output_edge": "ValidationResult", "format": "icd10_cm"},
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
        "generator": "scripts/domain_ind_healthcare_admin.py",
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
                "scripts/build_edge_type_retrofit.py). gated_effect_candidate rows: network/effectful healthcare-admin "
                "calls (NPPES, FHIR server read/write, HL7 ADT send, terminology $validate-code) are NEVER proven and "
                "stay candidate/serves_truth=false with an effect + proof_obligation. Healthcare ADMIN only (NPI/ICD/CPT/"
                "HCPCS/FHIR-admin/HL7-PID SHAPES) — NO clinical-risk, NO insurance; synthetic/public shapes only, NO real "
                "PII/PAN/SSN/secrets. Counts are separate and honest.",
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
    err = run_primitive_proof("prim:leaf:hca_EXEC_ERROR", "hca_npi_check_digit", object(), "irrelevant")

    manifest = build_manifest(rows, gated)
    valid_effects = {"network_read", "network_write", "model_call", "file_write"}
    expected_formats = {"npi", "icd10_cm", "cpt", "hcpcs", "fhir_administrative", "hl7_pid", "place_of_service"}

    checks: list[tuple[str, bool]] = [
        (">=25 deterministic leaves declared", len(LEAF_SPECS) >= 25),
        ("unique proven primitive ids", len(set(ids)) == len(ids)),
        (">=25 leaves PROVE serves_truth=true via an executed proof", len(rows) >= 25),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for (_s, r) in proven if r["serves_truth"] is True)),
        ("EVERY proven row carries non-null input+output edge type ids", len(typed) == len(rows)),
        ("manifest typed == proven_deterministic", manifest["typed"] == manifest["proven_deterministic"]),
        ("all 7 target ADMIN formats are covered", set(manifest["formats_covered"]) == expected_formats),
        ("roundtrip-inverse pairs actually ran + PASSED a roundtrip proof", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in proven_by_id[s["id"]]["proofs"])
            for s in roundtrip_specs)),
        ("NPI Luhn check digit is correct (1234567893 valid, 1234567890 invalid)",
         proven_by_id["prim:leaf:hca_npi_validate"]["serves_truth"] is True
         and proven_by_id["prim:leaf:hca_npi_validate_bad"]["serves_truth"] is True),
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
        print("FAIL - domain_ind_healthcare_admin:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - domain_ind_healthcare_admin: {len(rows)} WORKABLE (proven + TYPED) deterministic SHAPE leaves for "
          f"'{DOMAIN}' (serves_truth=true, L7_executed_proof; typed=={len(rows)}) across {len(expected_formats)} "
          f"ADMIN formats (NPI/ICD-10/CPT/HCPCS/FHIR-admin/HL7-PID/place-of-service); {len(roundtrip_specs)} inverse "
          f"pairs proven reversible via roundtrip; {len(gated)} network/effectful healthcare-admin capabilities declared "
          "as GATED-EFFECT candidates (serves_truth=false, effect + proof_obligation). A deliberately-wrong leaf and an "
          "un-runnable fixture correctly stay candidate. ADMIN only, NO clinical/insurance; synthetic shapes, no PII.")
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
