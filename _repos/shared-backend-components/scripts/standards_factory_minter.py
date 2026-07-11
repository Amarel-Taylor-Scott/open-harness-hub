#!/usr/bin/env python3
"""scripts.standards_factory_minter — "standards ARE primitive factories" (2026-07-08). Each standard yields
the SAME primitive set — parser · schema-validator · code-validator · canonical-mapper · conformance-checker ·
crosswalk-mapper · version-resolver · error-explainer · ack-builder — so one data table of standards ×
op-classes mints hundreds of governed, multi-axis-addressable primitive SPECS (the owner's §5/§11/§17 Pack-1
and the highest-multiplier move in the primitive atlas). Every spec is typed across the atlas axes
(persona × industry × geography × standard × datatype × process-stage), carries input/output edges, a
determinism budget, a permission manifest, provenance, and the atlas retrieval tags that feed the 79-column
multi-index — then flows the SAME formal-package/security/lifecycle governance as every other primitive.

These are candidate SPECS (contract + schema + promotion path), NOT executables yet: `needs_executor=true`,
`lifecycle_stage=candidate`, `serves_truth=false`. A spec becomes validated only after an executor + verifier +
golden fixtures are generated and the gates pass. Deterministic (D0/D1) — standards parsing/validation is pure
code + versioned tables, never network. Sensitive transaction families (e.g. X12 835 denial) are marked
`never_final_adverse_decision` — they route evidence, never make the final adverse call. Data seam: a new
standard = one STANDARDS row; a new op-class = one OP_SETS row.

    python3 scripts/standards_factory_minter.py --self-test
    python3 scripts/standards_factory_minter.py --cards | head
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"standards_factory_minter requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-std"
FACTORY_VERSION = "standards-factory-v1"

# ── the fixed op-set per standard KIND (op_name, process_stage, execution_model, determinism) ────────────────
OP_SETS: dict[str, tuple[tuple[str, str, str, str], ...]] = {
    "transaction": (  # message standards: X12, EDIFACT, ISO 20022, HL7 v2/FHIR, ACORD, NACHA, GS1 EDI
        ("parse", "ingest", "deterministic_transformer", "D0_pure"),
        ("schema_validate", "validate", "pure_function", "D0_pure"),
        ("map_to_canonical", "normalize", "deterministic_transformer", "D0_pure"),
        ("conformance_check", "conformance check", "pure_function", "D1_seeded"),
        ("build_acknowledgement", "route", "deterministic_transformer", "D0_pure"),
        ("resolve_version", "validate", "pure_function", "D1_seeded"),
        ("explain_error", "route", "deterministic_transformer", "D1_seeded")),
    "code_system": (  # code lists: ISO 4217/3166/8601, LOINC, SNOMED, ICD-10, CPT, HCPCS, NAICS, HS, UCUM, GTIN
        ("validate_code", "validate", "pure_function", "D1_seeded"),
        ("normalize_code", "normalize", "deterministic_transformer", "D1_seeded"),
        ("crosswalk_map", "normalize", "deterministic_transformer", "D1_seeded"),
        ("resolve_version", "validate", "pure_function", "D1_seeded"),
        ("resolve_alias", "normalize", "deterministic_transformer", "D1_seeded")),
    "schema_api": (  # data/API contracts: JSON Schema, OpenAPI, GraphQL, Protobuf, Avro, schema.org
        ("validate_instance", "validate", "pure_function", "D0_pure"),
        ("generate_tool_schema", "normalize", "deterministic_transformer", "D0_pure"),
        ("map_entity", "normalize", "deterministic_transformer", "D0_pure"),
        ("diff_version", "audit", "deterministic_transformer", "D0_pure")),
    "geospatial": (  # OGC API Features, ISO 19115, EPSG, GeoJSON
        ("validate_geometry", "validate", "pure_function", "D0_pure"),
        ("normalize_crs", "normalize", "deterministic_transformer", "D1_seeded"),
        ("transform_crs", "normalize", "deterministic_transformer", "D1_seeded"),
        ("generate_metadata", "report", "deterministic_transformer", "D0_pure")),
    "identifier": (  # LEI, NPI, IBAN, BIC, VIN, DUNS, EORI, GEOID, UPRN, PAN, GSTIN, ABN
        ("validate_checksum", "validate", "pure_function", "D0_pure"),
        ("normalize_format", "normalize", "deterministic_transformer", "D0_pure"),
        ("resolve_alias", "normalize", "deterministic_transformer", "D1_seeded")),
}


def _S(sid: str, name: str, kind: str, geo: str, industries: list[str], datatypes: list[str],
       personas: list[str], sensitive: bool = False) -> dict[str, Any]:
    return {"id": sid, "name": name, "kind": kind, "geography": geo, "industries": industries,
            "datatypes": datatypes, "personas": personas, "sensitive": sensitive}


# ── the versioned STANDARDS table (data seam: a new standard = a row). ───────────────────────────────────────
STANDARDS: tuple[dict[str, Any], ...] = (
    # global reference
    _S("iso_8601", "ISO 8601 Date/Time", "code_system", "global", ["all"], ["date value"],
       ["data engineer", "data steward"]),
    _S("iso_3166", "ISO 3166 Country/Subdivision", "code_system", "global", ["all"], ["code value"],
       ["data engineer", "compliance officer"]),
    _S("iso_4217", "ISO 4217 Currency", "code_system", "global", ["banking", "payments", "retail"],
       ["money amount", "code value"], ["cfo", "treasury analyst", "controller"]),
    _S("bcp_47", "BCP 47 Language/Locale", "code_system", "global", ["all"], ["code value"], ["data steward"]),
    _S("ucum", "UCUM Units", "code_system", "global", ["healthcare", "manufacturing", "life sciences"],
       ["quantity with unit"], ["data engineer", "clinical data integration engineer"]),
    # financial / capital markets
    _S("iso_20022", "ISO 20022 Financial Messaging", "transaction", "global",
       ["banking", "payments", "capital markets"], ["event", "money amount"],
       ["treasury analyst", "reconciliation analyst", "payments operations analyst"]),
    _S("nacha_ach", "NACHA ACH", "transaction", "united states", ["banking", "payments"], ["event"],
       ["payments operations analyst", "treasury analyst"]),
    _S("fix_protocol", "FIX Protocol", "transaction", "global", ["capital markets"], ["event"],
       ["reconciliation analyst"]),
    _S("xbrl", "XBRL / Inline XBRL", "transaction", "global", ["capital markets", "banking"], ["free text"],
       ["controller", "auditor"]),
    _S("lei", "LEI (ISO 17442)", "identifier", "global", ["banking", "insurance", "capital markets"],
       ["legal entity", "identifier"], ["compliance officer", "procurement analyst"]),
    _S("iban", "IBAN", "identifier", "european union", ["banking", "payments"], ["identifier"],
       ["treasury analyst"]),
    # healthcare
    _S("hl7_fhir", "HL7 FHIR", "transaction", "united states", ["healthcare"], ["claim", "person"],
       ["clinical data integration engineer", "rcm specialist"]),
    _S("x12_837", "X12 837 Claims", "transaction", "united states", ["healthcare"], ["claim"],
       ["billing specialist", "rcm specialist"]),
    _S("x12_835", "X12 835 Remittance", "transaction", "united states", ["healthcare"],
       ["remittance advice", "claim"], ["billing specialist", "payer ops analyst"], sensitive=True),
    _S("x12_270_271", "X12 270/271 Eligibility", "transaction", "united states", ["healthcare"], ["event"],
       ["billing specialist"]),
    _S("npi", "NPI (NPPES)", "identifier", "united states", ["healthcare"], ["identifier", "person"],
       ["credentialing specialist", "billing specialist"]),
    _S("loinc", "LOINC Observations", "code_system", "global", ["healthcare", "life sciences"], ["code value"],
       ["clinical data integration engineer"]),
    _S("snomed_ct", "SNOMED CT", "code_system", "global", ["healthcare"], ["code value"],
       ["clinical data integration engineer"], sensitive=True),
    _S("icd_10", "ICD-10", "code_system", "united states", ["healthcare"], ["code value"],
       ["billing specialist"], sensitive=True),
    # supply chain / trade
    _S("gs1_gtin", "GS1 GTIN", "identifier", "global", ["retail", "supply chain", "logistics"],
       ["identifier", "asset"], ["catalog manager", "supply chain analyst"]),
    _S("edi_x12_supply", "X12 850/856/810 (PO/ASN/Invoice)", "transaction", "united states",
       ["supply chain", "logistics", "retail"], ["invoice", "shipment"], ["supply chain analyst"]),
    _S("wco_hs", "WCO Harmonized System", "code_system", "global", ["logistics", "supply chain"],
       ["code value"], ["procurement analyst"]),
    _S("gs1_epcis", "GS1 EPCIS", "transaction", "global", ["supply chain", "logistics", "pharma"], ["event"],
       ["supply chain analyst"]),
    # insurance / manufacturing
    _S("acord", "ACORD", "transaction", "global", ["insurance"], ["claim", "contract"],
       ["claims examiner", "underwriting assistant"]),
    _S("isa_95", "ISA-95 / IEC 62264", "schema_api", "global", ["manufacturing"], ["asset", "work order"],
       ["plant manager", "manufacturing engineer"]),
    _S("opc_ua", "OPC UA", "schema_api", "global", ["manufacturing", "energy"], ["event", "asset"],
       ["plant manager"]),
    # e-invoicing / tax
    _S("peppol_en16931", "Peppol BIS / EN 16931", "transaction", "european union", ["all"], ["invoice"],
       ["controller", "compliance officer"]),
    _S("ubl", "UBL", "schema_api", "global", ["logistics", "retail"], ["invoice"], ["controller"]),
    # data / API / geospatial
    _S("json_schema", "JSON Schema", "schema_api", "global", ["all"], ["free text"],
       ["backend engineer", "data engineer"]),
    _S("openapi", "OpenAPI", "schema_api", "global", ["all"], ["free text"],
       ["backend engineer", "integration engineer"]),
    _S("schema_org", "schema.org", "schema_api", "global", ["retail", "media"], ["organization name"],
       ["data steward"]),
    _S("ogc_features", "OGC API Features", "geospatial", "global", ["public sector", "insurance"],
       ["postal address"], ["gis analyst"]),
    _S("epsg_crs", "EPSG CRS", "geospatial", "global", ["public sector", "energy"], ["postal address"],
       ["gis analyst"]),
)


def _card(std: dict[str, Any], op: tuple[str, str, str, str]) -> dict[str, Any]:
    op_name, stage, exec_model, determinism = op
    impl = f"{std['kind']}.{std['id']}.{op_name}"
    obj = std["datatypes"][0]
    out = {"parse": "canonical_object", "map_to_canonical": "canonical_object",
           "map_entity": "canonical_object", "crosswalk_map": "mapped_code",
           "build_acknowledgement": "acknowledgement", "explain_error": "error_explanation",
           "generate_metadata": "metadata_record", "generate_tool_schema": "tool_schema"}.get(
        op_name, "validation_result")
    tags = sorted({"standard_primitive", std["kind"], stage, determinism, "pure", "safe" if not
                   std["sensitive"] else "review required", "candidate", std["geography"], obj,
                   f"standard:{std['id']}", *std["industries"], *std["personas"]})
    return {
        "primitive_id": canonical_id(CARD_PREFIX, impl, std["name"]),
        "impl_name": impl, "record_type": "standard_primitive_spec",
        "kind": "primitive_spec", "title": f"{op_name} — {std['name']}",
        "input_edge": obj if op_name not in ("parse", "build_acknowledgement") else f"{std['id']}_message",
        "output_edge": out, "language": "python",
        # multi-axis atlas addressability (owner §11)
        "persona_scope": std["personas"], "industry_scope": std["industries"],
        "geography_scope": [std["geography"]], "standard": [std["id"]], "datatype_scope": std["datatypes"],
        "process_stage": stage, "operation": op_name,
        # formal-package governance (deterministic, pure — standards parsing is code + versioned tables)
        "execution_model": exec_model, "determinism_level": determinism, "lifecycle_stage": "candidate",
        "needs_executor": True,  # a SPEC — executor+verifier+fixtures generated before validated
        "permission_manifest": {"permission_class": "pure", "side_effect_free": True, "network_access": False,
                                "security_flags": []},
        "risk_tier": "review required" if std["sensitive"] else "safe",
        "verifier_id": "standards_factory_minter::_self_test", "verifier_kind": "spec + golden fixtures",
        "marginal_utility_evidence": {"status": "unmeasured", "lift": None},
        "compatible_runtimes": ["python", "typescript", "sql"], "compatible_models": ["*"],
        "artifact_hash": canonical_id("artifact", impl, FACTORY_VERSION),
        "provenance": {"contract_version": FACTORY_VERSION, "standard": std["id"], "standard_name": std["name"]},
        "promotion_receipts": {}, "retrieval_tags": tags,
        "never_final_adverse_decision": std["sensitive"],
        "blackbox": f"Standard primitive SPEC: {op_name} for {std['name']} ({std['kind']}, {std['geography']}). "
                    f"{std['datatypes']} in {std['industries']}. Deterministic {determinism}; candidate spec "
                    f"awaiting executor+verifier+golden fixtures before validated."
                    + (" SENSITIVE: routes evidence, NEVER a final adverse/clinical/coverage decision."
                       if std["sensitive"] else ""),
        "tier": "standard", **BOUNDARY}


def all_cards() -> list[dict[str, Any]]:
    cards = []
    for std in STANDARDS:
        for op in OP_SETS[std["kind"]]:
            cards.append(_card(std, op))
    return cards


def summary() -> dict[str, Any]:
    cards = all_cards()
    by_kind: dict[str, int] = {}
    for std in STANDARDS:
        by_kind[std["kind"]] = by_kind.get(std["kind"], 0) + 1
    return {"record_type": "standards_factory_summary", "n_standards": len(STANDARDS),
            "n_primitive_specs": len(cards), "standards_by_kind": dict(sorted(by_kind.items())),
            "ops_per_kind": {k: len(v) for k, v in OP_SETS.items()}, **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = all_cards()
    checks.append((f"factory mints {len(cards)} specs from {len(STANDARDS)} standards × op-sets "
                   "(the multiplier)",
                   len(cards) >= 120 and len(STANDARDS) >= 25))
    checks.append(("every spec is multi-axis addressable (persona/industry/geography/standard/datatype/"
                   "process_stage) + input/output edges + candidate/serves_truth=false",
                   all(c["persona_scope"] and c["industry_scope"] and c["geography_scope"] and c["standard"]
                       and c["datatype_scope"] and c["process_stage"] and c["input_edge"] and c["output_edge"]
                       and c["serves_truth"] is False and c["lifecycle_stage"] == "candidate" for c in cards)))
    checks.append(("standards parsing is PURE/deterministic (D0/D1, no network) — spec awaiting executor",
                   all(c["permission_manifest"]["network_access"] is False
                       and c["determinism_level"] in ("D0_pure", "D1_seeded")
                       and c["needs_executor"] is True for c in cards)))
    # transaction standards get parser + ack + conformance; code systems get code_validate + crosswalk
    x12 = [c for c in cards if c["standard"] == ["x12_835"]]
    iso4217 = [c for c in cards if c["standard"] == ["iso_4217"]]
    checks.append(("transaction standard (X12 835) mints parse+ack+conformance; code system (ISO 4217) mints "
                   "validate_code+crosswalk",
                   {c["operation"] for c in x12} >= {"parse", "build_acknowledgement", "conformance_check"}
                   and {c["operation"] for c in iso4217} >= {"validate_code", "crosswalk_map",
                                                             "resolve_version"}))
    checks.append(("sensitive standards (X12 835, ICD-10, SNOMED) mark never_final_adverse + review-required",
                   all(c["never_final_adverse_decision"] and c["risk_tier"] == "review required"
                       for c in cards if c["standard"][0] in ("x12_835", "icd_10", "snomed_ct"))))
    checks.append(("retrieval_tags carry standard + industry + geography + persona (feed the atlas facets)",
                   all(any(t.startswith("standard:") for t in c["retrieval_tags"]) for c in cards)
                   and "banking" in next(c for c in cards if c["standard"] == ["iso_4217"])["retrieval_tags"]))
    checks.append(("data seam: ids canonical + unique; summary computed (not typed)",
                   len({c["primitive_id"] for c in cards}) == len(cards)
                   and summary()["n_primitive_specs"] == len(cards)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    s = summary()
    print(f"\nPASS - standards_factory_minter: {s['n_standards']} standards -> {s['n_primitive_specs']} "
          f"multi-axis primitive SPECS (parse/validate/map/conform/crosswalk/version/ack/error). Deterministic, "
          f"candidate specs awaiting executors; sensitive families never make final adverse decisions. "
          f"serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cards", action="store_true")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.cards:
        for c in all_cards():
            print(json.dumps(c, sort_keys=True))
        return 0
    if args.summary:
        print(json.dumps(summary(), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
