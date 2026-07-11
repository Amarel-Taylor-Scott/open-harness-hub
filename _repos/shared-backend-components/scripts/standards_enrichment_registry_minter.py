#!/usr/bin/env python3
"""scripts.standards_enrichment_registry_minter — the owner platform spec's STANDARDS, ENRICHMENT PROVIDERS,
and TOP-50 priority primitives minted as candidates (2026-07-07): every standard (ISO 3166/4217/8601/8000/
19160/19112, UCUM, QUDT, Schema.org, JSON Schema, SHACL, FHIR, GTIN, NAICS, SOC, GEOID, IANA tz) becomes a
reference-system primitive + a conformity-validator candidate; every provider (Census Geocoder/Data API,
TIGER, OSM/Overpass, GeoNames, OurAirports, RUCA/RUCC, ADI, NLCD, EPQS, NOAA normals, GLEIF, O*NET) becomes
an enrichment-provider candidate carrying the provider-metadata shape (coverage/cost/license/refresh); the
spec's 50 priority primitives mint with their rank. All lookups/enrichment are candidate infrastructure —
live calls are governed enrichment requests, never ad-hoc. candidate=true, serves_truth=false.

    python3 scripts/standards_enrichment_registry_minter.py --self-test
    python3 scripts/standards_enrichment_registry_minter.py --run
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"standards_enrichment_registry_minter requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-stdreg"

#: (standard, standardizes, key primitives)
STANDARDS: tuple[tuple[str, str, str], ...] = (
    ("iso_3166", "country and subdivision codes", "country_code subdivision_code country_alias jurisdiction"),
    ("iso_4217", "currency codes", "currency_code numeric_currency_code minor_units money_parsing"),
    ("iso_8601", "dates and times", "date datetime interval duration timezone_aware_timestamp"),
    ("iso_8000", "data quality frameworks", "data_quality_rule master_data_quality conformity_evidence"),
    ("iso_19160", "postal address components", "postal_address_component address_template delivery_line"),
    ("iso_19112", "spatial referencing by geographic identifiers", "place_identifier gazetteer_entry"),
    ("ucum", "unambiguous machine units", "unit_code quantity dimensional_equivalence"),
    ("qudt", "semantic quantities/units/dimensions", "quantity_kind unit dimension_vector"),
    ("schema_org", "web-scale entity vocabulary", "person organization place postal_address product event"),
    ("json_schema", "JSON structural validation", "field_type constraint enum pattern required_property"),
    ("shacl", "RDF shape validation", "graph_constraint ontology_validation semantic_quality"),
    ("fhir", "healthcare exchange resources", "patient observation practitioner encounter"),
    ("gs1_gtin", "trade item identification", "product_identifier package_identifier barcode_key"),
    ("naics", "industry classification", "industry_code sector business_classification"),
    ("soc", "occupational classification", "occupation_code job_classification"),
    ("census_geoid", "census geographic identifiers", "tract block_group county place state"),
    ("iana_tz", "time zone identifiers and rules", "timezone_id offset_history dst_rule"),
)
#: (provider, input, output, coverage, cost_model, license)
PROVIDERS: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("census_geocoder", "address or lat/lon", "coordinates + tract/block/county/state", "US", "free", "public_data"),
    ("census_data_api", "GEOID + variables", "demographics housing economics", "US", "free_keyed", "public_data"),
    ("tiger_line", "geometry or GEOID", "boundaries + geographic codes", "US", "free", "public_data"),
    ("osm_overpass", "bbox/point/tags", "POIs roads landuse amenities", "global", "free_rate_limited", "ODbL"),
    ("geonames", "place/postal/lat-lon", "gazetteer features postal places", "global", "free_keyed", "CC-BY"),
    ("ourairports", "lat/lon or airport code", "airport metadata nearest airport", "global", "free", "public_domain"),
    ("usda_ruca", "census tract", "rural/urban classification", "US", "free", "public_data"),
    ("usda_rucc", "county", "metro/nonmetro classification", "US", "free", "public_data"),
    ("neighborhood_atlas_adi", "block group", "deprivation percentile", "US", "free_registered", "restricted_use"),
    ("usgs_nlcd", "point/polygon", "land cover imperviousness canopy", "US", "free", "public_data"),
    ("usgs_epqs", "lat/lon", "elevation", "US", "free", "public_data"),
    ("noaa_climate_normals", "station/location", "30-year climate averages", "US", "free", "public_data"),
    ("iana_tz_db", "location/tz id", "timezone rules", "global", "free", "public_domain"),
    ("gs1", "product code", "trade item identity", "global", "licensed", "membership"),
    ("gleif_lei", "entity name/LEI", "legal entity identity", "global", "free", "CC0"),
    ("onet_soc", "job title/description", "occupation classification", "US", "free", "public_data"),
    ("overture_maps", "bbox/theme", "places buildings transportation", "global", "free", "ODbL_CDLA"),
)
TOP_50_PRIORITY: tuple[str, ...] = (
    "raw_observation", "standardized_value", "parsed_component", "type_candidate", "quality_issue",
    "transformation_trace", "reference_code", "reference_dataset", "canonical_entity", "entity_alias",
    "entity_relationship", "match_candidate", "comparison_vector", "match_decision", "review_task",
    "enrichment_request", "enrichment_response", "enrichment_feature", "provider_registry", "unit_alias",
    "currency_alias", "country_alias", "address_component", "geocode_result", "geometry", "geoid",
    "h3_cell", "nearest_feature", "distance_feature", "area_overlay_feature", "money_value",
    "quantity_value", "date_value", "identifier_value", "email_value", "phone_value", "url_value",
    "organization_name", "person_name", "trust_name", "estate_name", "product_identifier",
    "industry_classification", "occupation_classification", "land_cover_class", "rurality_class",
    "deprivation_index", "schema_conformity_result", "confidence_score", "provenance_record")
#: implemented-already links (reuse-first accounting)
_IMPLEMENTED = {"unit_alias": "quantity_money_primitives.lookup_unit_alias",
                "currency_alias": "quantity_money_primitives.parse_money",
                "money_value": "quantity_money_primitives.parse_money",
                "quantity_value": "quantity_money_primitives.parse_quantity",
                "schema_conformity_result": "quantity_money_primitives.conformity_check",
                "organization_name": "string_standardization_primitives.standardize_company_name",
                "person_name": "string_standardization_primitives.standardize_person_name",
                "trust_name": "party_name_primitives.classify_party_type",
                "estate_name": "party_name_primitives.classify_party_type",
                "match_candidate": "party_name_primitives (expansion + keys)",
                "transformation_trace": "quantity_money_primitives (trace in every parse)",
                "review_task": "dummy_data_detection_primitives.rate_dummy_likelihood (routes to review)"}


def mint_rows() -> list[dict[str, Any]]:
    rows = []
    for std, what, prims in STANDARDS:
        rows.append({"primitive_id": canonical_id(CARD_PREFIX, "standard", std), "kind": "primitive_group",
                     "record_type": "reference_standard_candidate", "title": f"Reference system: {std}",
                     "standard": std, "standardizes": what, "member_primitives": prims.split(),
                     "blackbox": f"Reference/code system {std}: standardizes {what}. Members become lookup "
                                 f"tables, validators, and conformity checks. Input: RawFieldValue. "
                                 f"Output: {std.title().replace('_', '')}ConformityResult.",
                     "input_edge": "RawFieldValue", "output_edge": "ReferenceConformityResult",
                     "tags": f"standard:{std}", **BOUNDARY})
    for prov, inp, outp, coverage, cost, license_ in PROVIDERS:
        rows.append({"primitive_id": canonical_id(CARD_PREFIX, "provider", prov), "kind": "primitive_group",
                     "record_type": "enrichment_provider_candidate", "title": f"Enrichment provider: {prov}",
                     "provider": prov, "provider_metadata": {"input": inp, "output": outp,
                                                             "coverage": coverage, "cost_model": cost,
                                                             "license": license_},
                     "blackbox": f"Enrichment provider {prov}: {inp} -> {outp} ({coverage}; {cost}; "
                                 f"{license_}). Calls are governed enrichment_request/response records with "
                                 f"cache keys, TTLs, dataset versions, and provenance — never ad-hoc.",
                     "input_edge": "EnrichmentRequest", "output_edge": "EnrichmentResponse",
                     "tags": f"provider:{prov} coverage:{coverage}", **BOUNDARY})
    for rank, prim in enumerate(TOP_50_PRIORITY, start=1):
        impl = _IMPLEMENTED.get(prim, "")
        rows.append({"primitive_id": canonical_id(CARD_PREFIX, "priority", prim), "kind": "primitive",
                     "record_type": "platform_priority_primitive_candidate",
                     "title": f"Platform primitive #{rank}: {prim.replace('_', ' ')}",
                     "priority_rank": rank, "impl_name": prim, "implemented_by": impl,
                     "status": "already_executable" if impl else "to_build",
                     "blackbox": f"Owner-ranked platform primitive (#{rank}/50): {prim.replace('_', ' ')}. "
                                 f"{'Implemented by ' + impl if impl else 'Minting-queue item.'} "
                                 f"Input: PlatformDataInput. Output: PlatformDataStructure.",
                     "input_edge": "PlatformDataInput", "output_edge": "PlatformDataStructure",
                     "tags": f"priority:{rank}", **BOUNDARY})
    return rows


def run_minter() -> dict[str, Any]:
    rows = mint_rows()
    out_dir = resource("data") / "dev-intel" / "standards_enrichment_registry"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "standards_enrichment_candidates.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    rec = {"record_type": "standards_enrichment_registry_receipt", "standards": len(STANDARDS),
           "providers": len(PROVIDERS), "priority_primitives": len(TOP_50_PRIORITY),
           "already_executable": sum(1 for r in rows if r.get("status") == "already_executable"),
           "total": len(rows), "staged_path": str(out_dir / "standards_enrichment_candidates.jsonl"),
           **BOUNDARY}
    (out_dir / "standards_enrichment_registry_receipt.json").write_text(
        json.dumps(rec, indent=2, sort_keys=True))
    return rec


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    rows = mint_rows()
    checks.append(("mints 17 standards + 17 providers + 50 ranked priority primitives",
                   len(rows) == len(STANDARDS) + len(PROVIDERS) + 50
                   and sum(1 for r in rows if r["record_type"] == "reference_standard_candidate") == 17))
    checks.append(("provider rows carry the provider-metadata shape (coverage/cost/license)",
                   all({"coverage", "cost_model", "license"} <= set(r["provider_metadata"])
                       for r in rows if r["record_type"] == "enrichment_provider_candidate")))
    checks.append(("REUSE-FIRST: >=10 of the top-50 already map to executable pack primitives",
                   sum(1 for r in rows if r.get("status") == "already_executable") >= 10))
    checks.append(("priority ranks preserved 1..50; ids unique; deterministic",
                   [r["priority_rank"] for r in rows if "priority_rank" in r] == list(range(1, 51))
                   and len({r["primitive_id"] for r in rows}) == len(rows)
                   and json.dumps(mint_rows(), sort_keys=True) == json.dumps(rows, sort_keys=True)))
    checks.append(("boundary", all(r.get("serves_truth") is False for r in rows)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - standards_enrichment_registry_minter: standards -> conformity systems, providers -> "
          "governed enrichment candidates, top-50 ranked with reuse-first links. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        print(json.dumps(run_minter(), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
