#!/usr/bin/env python3
"""scripts.enrichment_primitive_catalog — the reference-data / ENRICHMENT primitive catalog (2026-07-08):
authoritative lookups & public-dataset joins (address→GEOID, point→tract→demographics, point→weather/flood/
land/rurality, company→LEI/SAM/filings, product→VIN/NDC/chemical, date→timezone/holiday) as TYPED, VERSIONED,
PERMISSIONED primitives — not ad-hoc API calls. Each is an EXTERNAL-TOOL primitive (execution_model=
external_tool, determinism_level=D2_bounded_external, permission_class="network egress", risk_tier="review
required"): it flows through the SAME formal-package/security/lifecycle governance as pure primitives, proving
the supply chain handles the tool-wrapper class. Carries the owner's enrichment schema — input/output schema,
provider, coverage, cost/license/PII, cache_policy, provenance_required, failure_modes, fallback_sources.

Data seam (no magic values): a new enrichment source = one ENRICHMENT_SOURCES row, no code. External-tool
primitives DECLARE their permission manifest (they ARE the network boundary — not scanned like pure code).
Owner correction encoded: the Census Geocoder is GEOID/geography enrichment, NOT USPS deliverability — they are
distinct sources with distinct outputs. Sanctions/OFAC emits candidate/review, NEVER a final adverse decision.
candidate; serves_truth=false (external D2 may serve truth only later, with dated provenance + review).

    python3 scripts/enrichment_primitive_catalog.py --self-test
    python3 scripts/enrichment_primitive_catalog.py --cards
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
    raise SystemExit(f"enrichment_primitive_catalog requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-enrich"
CATALOG_VERSION = "enrichment-catalog-v1"
#: provenance fields EVERY enrichment call must persist (owner §2/§13) — the cache/version/audit key
PROVENANCE_REQUIRED = ("provider", "dataset_or_benchmark", "data_version", "retrieved_at", "request_hash",
                       "response_hash", "confidence")


def _s(pid: str, name: str, obj_in: str, obj_out: str, provider: str, standard: str, coverage: str,
       cost: str, license_: str, pii: str, inp: dict[str, str], out: dict[str, str],
       fails: list[str], fallbacks: list[str]) -> dict[str, Any]:
    return {"id": pid, "name": name, "object_in": obj_in, "object_out": obj_out, "provider": provider,
            "standard": standard, "coverage": coverage, "cost_model": cost, "license": license_,
            "pii_risk": pii, "input_schema": inp, "output_schema": out, "failure_modes": fails,
            "fallback_sources": fallbacks}


# ── the versioned enrichment source table (data seam: add a row, no code). Representative high-value set
#    across the owner's object types; the full 50 extend by appending rows. ──────────────────────────────────
ENRICHMENT_SOURCES: tuple[dict[str, Any], ...] = (
    # address / geocoding
    _s("enrich.usps.validate_address", "USPS Address Validation", "postal_address", "deliverability",
       "USPS", "USPS Addresses 3.0", "US", "tiered_fee", "usps_terms", "address",
       {"street": "string", "city": "string", "state": "string", "postal_code": "string"},
       {"standardized_address": "string", "zip4": "string", "deliverable": "boolean",
        "secondary_unit_status": "enum[confirmed,missing,unknown]", "dpv_indicator": "string"},
       ["no_match", "secondary_unit_missing", "vacant", "provider_error"],
       ["google_address_validation", "smarty", "melissa"]),
    _s("enrich.census.geocode_to_geographies", "Census Geocoder Address→Geographies", "postal_address",
       "geography_enrichment", "US Census Bureau", "MAF/TIGER", "US, PR, Island Areas", "free_public",
       "public_domain", "address",
       {"street": "string", "city": "string", "state": "string", "postal_code": "string",
        "benchmark": "string", "vintage": "string"},
       {"matched_address": "string", "latitude": "number", "longitude": "number", "state_geoid": "string",
        "county_geoid": "string", "tract_geoid": "string", "block_geoid": "string",
        "match_type": "enum[exact,non_exact,tie]"},
       ["no_match", "tie_match", "interpolated_coordinate", "outdated_address_range"],
       ["geocodio", "google_geocoding", "nominatim"]),
    _s("enrich.google.validate_address", "Google Address Validation", "postal_address", "deliverability",
       "Google", "CASS (US/PR)", "global", "per_call", "google_terms", "address",
       {"address_lines": "array<string>", "region_code": "string"},
       {"verdict": "object", "standardized_address": "string", "geocode": "lat_lon",
        "missing_component_types": "array<string>", "has_unconfirmed_components": "boolean"},
       ["unconfirmed_components", "no_geocode", "quota_exceeded"], ["usps", "smarty"]),
    _s("enrich.hud.zip_to_tract", "HUD-USPS ZIP↔Tract Crosswalk", "postal_code", "geography_crosswalk",
       "HUD", "HUD-USPS Crosswalk", "US", "free_public", "public_domain", "low",
       {"zip": "string", "quarter": "string"},
       {"tract_geoid": "string", "res_ratio": "number", "bus_ratio": "number", "tot_ratio": "number"},
       ["zip_not_found", "stale_quarter"], ["census_geocoder"]),
    # census / demographics context (join by GEOID)
    _s("enrich.census.acs_by_geoid", "Census ACS 5-Year by GEOID", "geoid", "demographics",
       "US Census Bureau", "ACS 5-Year", "US", "free_public_keyed", "public_domain", "low",
       {"geoid": "string", "variables": "array<string>", "year": "string"},
       {"population": "integer", "median_household_income": "integer", "poverty_rate": "number",
        "education_attainment": "object", "vehicle_access": "object", "margin_of_error": "object"},
       ["variable_not_in_vintage", "suppressed_small_geo", "key_required"], []),
    _s("enrich.usda.rucc_ruca", "USDA Rurality (RUCC/RUCA)", "geoid", "rurality_context",
       "USDA ERS", "RUCC 2023 / RUCA", "US", "free_public", "public_domain", "none",
       {"county_fips": "string", "tract_geoid": "string"},
       {"rucc_code": "integer", "ruca_primary": "number", "ruca_secondary": "number",
        "metro_nonmetro": "enum[metro,nonmetro]"},
       ["geo_not_classified", "version_mismatch"], []),
    _s("enrich.cdc.svi_adi", "Deprivation/Vulnerability (SVI/ADI)", "geoid", "deprivation_context",
       "CDC/ATSDR + Neighborhood Atlas", "SVI / ADI", "US", "free_public", "cite_required", "none",
       {"tract_geoid": "string", "block_group_geoid": "string", "year": "string"},
       {"svi_overall_percentile": "number", "svi_themes": "object", "adi_national": "integer",
        "adi_state": "integer"},
       ["version_not_comparable_across_years", "geo_not_covered"], []),
    # places / POI / infrastructure
    _s("enrich.osm.nearest_feature", "OSM/Overpass Nearest Feature", "lat_lon", "poi_context",
       "OpenStreetMap", "Overpass QL", "global", "free_fair_use", "odbl", "none",
       {"latitude": "number", "longitude": "number", "amenity": "string", "radius_m": "integer"},
       {"nearest_feature": "object", "distance_m": "number", "count_within_radius": "integer"},
       ["no_feature_in_radius", "rate_limited", "tag_ambiguous"], ["overture_places", "geonames"]),
    _s("enrich.ourairports.nearest_airport", "OurAirports Nearest Airport", "lat_lon", "airport_context",
       "OurAirports", "OurAirports CSV", "global", "free_public", "public_domain", "none",
       {"latitude": "number", "longitude": "number", "major_only": "boolean"},
       {"iata": "string", "icao": "string", "airport_name": "string", "airport_type": "string",
        "distance_m": "number"},
       ["no_airport", "stale_local_table"], ["openflights"]),
    # weather / hazard / land
    _s("enrich.nws.forecast_alerts", "NWS Forecast & Alerts", "lat_lon", "weather_context",
       "NWS", "NWS API (JSON-LD)", "US", "free_public", "public_domain", "none",
       {"latitude": "number", "longitude": "number"},
       {"forecast_periods": "array<object>", "active_alerts": "array<object>",
        "observation": "object"},
       ["point_outside_us", "grid_unavailable", "rate_limited"], ["open_meteo", "noaa_cdo"]),
    _s("enrich.usgs.elevation", "USGS Point Elevation (EPQS)", "lat_lon", "elevation_context",
       "USGS", "EPQS", "US", "free_public", "public_domain", "none",
       {"latitude": "number", "longitude": "number", "units": "enum[Meters,Feet]"},
       {"elevation": "number", "units": "string"},
       ["point_outside_coverage", "service_unavailable"], []),
    _s("enrich.fema.flood_zone", "FEMA Flood Zone (NFHL)", "lat_lon", "hazard_context",
       "FEMA", "NFHL", "US", "free_public", "public_domain", "low",
       {"latitude": "number", "longitude": "number"},
       {"flood_zone": "string", "sfha": "boolean", "base_flood_elevation": "number",
        "firm_panel": "string"},
       ["point_not_mapped", "preliminary_data_only"], []),
    # time / date
    _s("enrich.iana.timezone_from_point", "Timezone from Point (IANA/tz boundary)", "lat_lon",
       "temporal_context", "IANA + tz boundary", "IANA TZ DB", "global", "free_public", "public_domain",
       "none",
       {"latitude": "number", "longitude": "number", "at_instant": "string"},
       {"timezone_id": "string", "utc_offset": "string", "is_dst": "boolean"},
       ["ocean_point_no_zone", "boundary_ambiguous"], ["geonames_timezone"]),
    _s("enrich.nager.public_holidays", "Public Holidays (Nager.Date)", "date", "temporal_context",
       "Nager.Date", "Nager API", "150+ countries", "free_public", "open", "none",
       {"country_code": "string", "year": "string"},
       {"holidays": "array<object>", "is_public_holiday": "boolean", "is_business_day": "boolean"},
       ["country_not_supported", "regional_holiday_variance"], ["timeanddate"]),
    # organization / legal entity
    _s("enrich.gleif.lei", "GLEIF LEI Lookup / Fuzzy Match", "organization", "legal_entity_identity",
       "GLEIF", "ISO 17442 LEI", "global", "free_public", "cc0", "low",
       {"lei": "string", "legal_name": "string", "address": "string"},
       {"lei": "string", "legal_name": "string", "registration_status": "string",
        "parent_lei": "string", "match_confidence": "number"},
       ["no_match", "ambiguous_name", "lapsed_registration"], ["companies_house", "sec_edgar"]),
    _s("enrich.cms.npi", "NPPES NPI Lookup / Validate", "provider", "provider_identity",
       "CMS NPPES", "NPI", "US", "free_public", "public_domain", "low",
       {"npi": "string", "first_name": "string", "last_name": "string", "taxonomy": "string",
        "state": "string"},
       {"npi": "string", "entity_type": "enum[individual,organization]", "taxonomy": "string",
        "practice_address": "object", "status": "string"},
       ["no_match", "deactivated_npi", "multiple_candidates"], []),
    _s("enrich.sam.entity_exclusions", "SAM.gov Entity & Exclusions", "organization", "vendor_status",
       "GSA SAM.gov", "SAM Entity API", "US federal", "free_public_keyed", "us_gov_terms", "low",
       {"uei": "string", "cage": "string", "legal_name": "string"},
       {"registration_status": "string", "exclusions": "array<object>", "has_active_exclusion": "boolean"},
       ["no_match", "sensitivity_tier_restricted", "key_required"], []),
    _s("enrich.ofac.screen_name", "OFAC Sanctions Pre-Screen (candidate/review ONLY)", "party",
       "sanctions_prescreen", "US Treasury OFAC", "OFAC SDN/Consolidated", "global", "free_public",
       "public_domain", "medium",
       {"name": "string", "identifiers": "object", "threshold": "number"},
       {"match_status": "enum[candidate_match,no_candidate_match,insufficient_identifiers,"
        "ambiguous_requires_review,list_version_mismatch]", "candidates": "array<object>",
        "list_version": "string", "list_hash": "string", "human_review_required": "boolean"},
       ["ambiguous_match", "list_version_mismatch", "insufficient_identifiers"], ["commercial_watchlist"]),
    # products / things
    _s("enrich.nhtsa.decode_vin", "NHTSA vPIC VIN Decode", "vin", "vehicle_attributes",
       "NHTSA", "vPIC", "US market", "free_public", "public_domain", "none",
       {"vin": "string", "model_year": "string"},
       {"make": "string", "model": "string", "year": "integer", "body_class": "string",
        "manufacturer": "string"},
       ["invalid_vin", "incomplete_decode", "pre_1981_vin"], []),
    _s("enrich.openfda.ndc", "openFDA NDC / Drug Lookup", "ndc", "drug_identity",
       "openFDA", "FDA NDC", "US", "free_public", "public_domain", "none",
       {"ndc": "string", "brand_name": "string"},
       {"product_type": "string", "labeler": "string", "dosage_form": "string",
        "active_ingredients": "array<object>"},
       ["ndc_not_found", "obsolete_listing"], ["rxnorm"]),
    _s("enrich.rxnorm.normalize_drug", "RxNorm/RxNav Normalize Drug", "drug_name", "drug_concept",
       "NLM RxNorm", "RxNorm", "US", "free_public", "public_domain", "none",
       {"drug_name": "string", "rxcui": "string"},
       {"rxcui": "string", "normalized_name": "string", "ingredients": "array<string>",
        "dose_form": "string"},
       ["no_concept", "ambiguous_name"], ["openfda_ndc"]),
    _s("enrich.pubchem.compound", "PubChem Compound Lookup", "chemical", "compound_identity",
       "PubChem", "PubChem PUG", "global", "free_public", "open", "none",
       {"name": "string", "cid": "string", "formula": "string"},
       {"cid": "string", "iupac_name": "string", "molecular_formula": "string", "synonyms": "array<string>"},
       ["no_compound", "structure_ambiguous"], []),
)


def _enrichment_card(src: dict[str, Any]) -> dict[str, Any]:
    """Build a FORMAL external-tool enrichment primitive card. Permission manifest is DECLARED (a network
    tool is the boundary — not body-scanned); flows the same governance fields as pure primitives."""
    sanctions = "sanctions" in src["object_out"] or "prescreen" in src["object_out"]
    return {
        "primitive_id": canonical_id(CARD_PREFIX, src["id"], src["name"]),
        "impl_name": src["id"], "record_type": "enrichment_primitive", "kind": "api_tool",
        "title": src["name"], "language": "rest",
        "input_edge": f"{src['object_in']}", "output_edge": f"{src['object_out']}",
        "provider": src["provider"], "standard": src["standard"], "coverage": src["coverage"],
        "access_method": "rest_api", "cost_model": src["cost_model"], "license": src["license"],
        "pii_risk": src["pii_risk"], "input_schema": src["input_schema"], "output_schema": src["output_schema"],
        "cache_policy": "cache keyed by provider + data_version + request_hash; TTL per update cadence",
        "provenance_required": list(PROVENANCE_REQUIRED),
        "failure_modes": src["failure_modes"], "fallback_sources": src["fallback_sources"],
        # formal-package governance fields — external tool, DECLARED network boundary
        "execution_model": "external_tool", "determinism_level": "D2_bounded_external",
        "permission_manifest": {"permission_class": "network egress", "side_effect_free": False,
                                "network_access": True, "filesystem_write": False, "subprocess": False,
                                "secret_access": src["cost_model"].endswith("keyed"),
                                "security_flags": ["network"]},
        "risk_tier": "review required", "runtime_target": "rest api / python client",
        "compatible_runtimes": ["python", "typescript"], "compatible_models": [],
        "lifecycle_stage": "candidate", "verifier_id": "enrichment_primitive_catalog::_self_test",
        "verifier_kind": "schema + fixture",
        "marginal_utility_evidence": {"status": "unmeasured", "lift": None},
        "promotion_receipts": {}, "artifact_hash": canonical_id("artifact", src["id"], src["standard"]),
        "provenance": {"contract_version": CATALOG_VERSION, "provider": src["provider"],
                       "standard": src["standard"]},
        "retrieval_tags": sorted({"external_tool", "enrichment", "D2_bounded_external", "network egress",
                                  "review required", "candidate", src["object_in"], src["object_out"],
                                  f"provider:{src['provider']}"}),
        "blackbox": f"Enrichment tool: {src['name']} ({src['provider']}, {src['standard']}). "
                    f"{src['object_in']} -> {src['object_out']} over {src['coverage']}. Governed call: "
                    f"cache-by-version + provenance {list(PROVENANCE_REQUIRED)}; failure modes "
                    f"{src['failure_modes']}; fallbacks {src['fallback_sources']}."
                    + (" SANCTIONS: emits candidate/review status ONLY, never a final adverse decision."
                       if sanctions else ""),
        "never_final_adverse_decision": sanctions, "tier": "enrichment", **BOUNDARY}


def all_cards() -> list[dict[str, Any]]:
    return [_enrichment_card(s) for s in ENRICHMENT_SOURCES]


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = all_cards()
    by_id = {c["impl_name"]: c for c in cards}
    checks.append((f"catalog has {len(cards)} enrichment sources across object types (address/census/context/"
                   "places/weather/time/entity/product)",
                   len(cards) >= 20
                   and {c["output_edge"] for c in cards} >= {"geography_enrichment", "demographics",
                                                             "weather_context", "legal_entity_identity",
                                                             "vehicle_attributes", "temporal_context"}))
    checks.append(("every card is external_tool / D2_bounded_external / network-egress / review-required / "
                   "candidate, serves_truth=false",
                   all(c["execution_model"] == "external_tool" and c["determinism_level"] == "D2_bounded_external"
                       and c["permission_manifest"]["permission_class"] == "network egress"
                       and c["risk_tier"] == "review required" and c["serves_truth"] is False
                       for c in cards)))
    checks.append(("every card carries input_schema + output_schema (dicts) + provenance_required + "
                   "failure_modes + fallback_sources",
                   all(isinstance(c["input_schema"], dict) and c["input_schema"]
                       and isinstance(c["output_schema"], dict) and c["output_schema"]
                       and "provider" in c["provenance_required"] and "retrieved_at" in c["provenance_required"]
                       and c["failure_modes"] for c in cards)))
    # owner correction: Census Geocoder is GEOID/geography, NOT USPS deliverability — distinct sources
    census = by_id["enrich.census.geocode_to_geographies"]
    usps = by_id["enrich.usps.validate_address"]
    checks.append(("Census Geocoder = geography enrichment (tract/block GEOID); USPS = deliverability — "
                   "distinct sources, distinct outputs (owner correction encoded)",
                   "tract_geoid" in census["output_schema"] and "deliverable" not in census["output_schema"]
                   and "deliverable" in usps["output_schema"] and "tract_geoid" not in usps["output_schema"]))
    # sanctions safety: candidate/review only, never final adverse
    ofac = by_id["enrich.ofac.screen_name"]
    checks.append(("OFAC pre-screen emits candidate/review status ONLY, never final adverse decision; "
                   "carries list_version + list_hash + human_review flag",
                   ofac["never_final_adverse_decision"] is True
                   and "candidate_match" in ofac["output_schema"]["match_status"]
                   and "list_hash" in ofac["output_schema"] and "human_review_required" in ofac["output_schema"]))
    checks.append(("data seam: sources are a data table (a new source = a row); ids canonical + unique",
                   len({c["primitive_id"] for c in cards}) == len(cards)
                   and all(c["primitive_id"].startswith(CARD_PREFIX) for c in cards)))
    checks.append(("keyed providers declare secret_access; free providers do not",
                   by_id["enrich.sam.entity_exclusions"]["permission_manifest"]["secret_access"] is True
                   and by_id["enrich.usgs.elevation"]["permission_manifest"]["secret_access"] is False))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - enrichment_primitive_catalog: {len(cards)} typed/versioned/permissioned enrichment "
          f"primitives (external_tool, D2_bounded_external, network-egress, review-required). Input/output "
          f"schema + provenance + failure modes + fallbacks. Census!=USPS; OFAC=candidate/review only. "
          f"serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cards", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.cards:
        for c in all_cards():
            print(json.dumps(c, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
