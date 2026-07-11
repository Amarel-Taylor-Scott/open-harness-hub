#!/usr/bin/env python3
"""scripts.domain_fmt_geo_calendar — WORKABLE (proven + TYPED) deterministic leaf primitives for the
'fmt_geo_calendar' domain (geospatial + calendar/contact interchange formats), plus honestly-declared
GATED-EFFECT candidates for the network/cloud CALLS in the same domain.

The domain covers pure, offline, deterministic transforms over public interchange shapes:
  * GeoJSON — parse / validate / emit Point + LineString, geometry bbox
  * WKT (Well-Known Text) — parse / emit Point + LineString, WKT<->GeoJSON conversion
  * Bounding box — from points, contains-test, center, degree-area
  * GTFS — stop record parse/emit, HH:MM:SS<->seconds (handles >24h service time)
  * iCalendar VEVENT — parse / emit, TEXT escape/unescape, DTSTAMP datetime decompose
  * vCard — parse / emit (synthetic public contact SHAPE only — never real PII)
  * GPX — track-point parse / emit (lat/lon/ele)
  * lat/long — longitude wrap-normalize, latitude clamp, coordinate round, DMS<->decimal

Repo law honored EXACTLY: serves_truth=true is set ONLY by a PASSING executed proof (imported
`run_primitive_proof` runs the mutator against a concrete fixture, checks the output, roundtrips any inverse, and
re-runs for determinism — it flips serves_truth false->true ONLY on pass; a deliberately-wrong fixture stays
candidate and is NEVER persisted as proven). A NETWORK/EFFECTFUL primitive (cloud geocode, CalDAV publish, GTFS-RT
fetch, object-storage upload) is NEVER run through the proof runner and NEVER serves_truth=true — it is declared as a
GATED EFFECT candidate: {candidate:true, serves_truth:false, effect, proof_obligation, input_edge_type_id,
output_edge_type_id}. The two families are counted SEPARATELY in the manifest (proven_deterministic vs
gated_effect_candidates); typed = proven rows carrying both canonical edge type_ids.

ADD-ONLY / flexible-multi-path: a NEW standalone shard file. It IMPORTS the shared machinery
(`scripts.mutator_registry.run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt`,
`scripts.build_edge_type_retrofit.canonicalize_edge`) and plugs its pure mutators in with `setdefault` (idempotent).
It edits NONE of the contract-locked/shared files and does NOT register into the flywheel (the caller gets a
register tuple). Domain law honored: NO insurance primitives; healthcare-admin shapes are absent (geo/calendar only);
all fixtures are synthetic/public shapes — no real PII/PAN/SSN/secrets. Offline + deterministic: no network, no LLM,
no wall-clock, no RNG; the write path uses a fixed literal timestamp. CLI: --self-test | --write.
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

# IMPORT the shared machinery — never edit it (ADD-ONLY seam).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

DOMAIN = "fmt_geo_calendar"
OUT_DIR = _resource("data") / "dev-intel" / "domain_primitives"
OUT_JSONL = OUT_DIR / "domain_fmt_geo_calendar.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_fmt_geo_calendar.json"
# Fixed literal timestamp — deterministic, no wall-clock read (repo law: no datetime.now/time.time).
FROZEN_TS = "2026-07-03T00:00:00Z"


# ── formatting helper: stable numeric text, whole floats lose the trailing .0 (WKT/GPX convention) ──
def _num(n: Any) -> str:
    if isinstance(n, float) and n.is_integer():
        return str(int(n))
    return str(n)


# ── PURE deterministic mutators: signature (payload, **kwargs) -> (output, receipt_dict). No I/O. ──

# GeoJSON ----------------------------------------------------------------------------------------------
def _geojson_parse_point(obj: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    coords = obj["coordinates"]
    out = {"lon": coords[0], "lat": coords[1]}
    return out, _receipt("geojson_parse_point", before=obj, after=out, lossless=True, note="GeoJSON Point -> {lon,lat}")


def _geojson_emit_point(obj: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"type": "Point", "coordinates": [obj["lon"], obj["lat"]]}
    return out, _receipt("geojson_emit_point", before=obj, after=out, lossless=True, note="{lon,lat} -> GeoJSON Point")


def _geojson_validate_point(obj: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    coords = obj.get("coordinates") if isinstance(obj, dict) else None
    valid = (
        isinstance(obj, dict) and obj.get("type") == "Point"
        and isinstance(coords, list) and len(coords) == 2
        and all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in coords)
    )
    out = {"valid": valid, "type": obj.get("type") if isinstance(obj, dict) else None}
    return out, _receipt("geojson_validate_point", before=obj, after=out, lossless=True, note="structural validity of a GeoJSON Point")


def _geojson_parse_linestring(obj: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"points": [{"lon": c[0], "lat": c[1]} for c in obj["coordinates"]]}
    return out, _receipt("geojson_parse_linestring", before=obj, after=out, lossless=True, note="GeoJSON LineString -> point list")


def _geojson_bbox(obj: dict[str, Any], **_kw: Any) -> tuple[list[float], dict[str, Any]]:
    coords = obj["coordinates"]
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    out = [min(lons), min(lats), max(lons), max(lats)]
    return out, _receipt("geojson_bbox", before=obj, after=out, lossless=False, note="[minLon,minLat,maxLon,maxLat] over a coordinate list")


# WKT --------------------------------------------------------------------------------------------------
def _wkt_parse_point(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    inner = text[text.index("(") + 1:text.index(")")].strip()
    x, y = inner.split()
    out = {"lon": float(x), "lat": float(y)}
    return out, _receipt("wkt_parse_point", before=text, after=out, lossless=True, note="WKT POINT -> {lon,lat}")


def _wkt_emit_point(obj: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"POINT ({_num(obj['lon'])} {_num(obj['lat'])})"
    return out, _receipt("wkt_emit_point", before=obj, after=out, lossless=True, note="{lon,lat} -> WKT POINT")


def _wkt_parse_linestring(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    inner = text[text.index("(") + 1:text.rindex(")")]
    pairs = [p.strip().split() for p in inner.split(",")]
    out = {"points": [{"lon": float(a), "lat": float(b)} for a, b in pairs]}
    return out, _receipt("wkt_parse_linestring", before=text, after=out, lossless=True, note="WKT LINESTRING -> point list")


def _wkt_point_to_geojson(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    inner = text[text.index("(") + 1:text.index(")")].strip()
    x, y = inner.split()
    out = {"type": "Point", "coordinates": [float(x), float(y)]}
    return out, _receipt("wkt_point_to_geojson", before=text, after=out, lossless=True, note="WKT POINT -> GeoJSON Point")


def _geojson_point_to_wkt(obj: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    x, y = obj["coordinates"]
    out = f"POINT ({_num(x)} {_num(y)})"
    return out, _receipt("geojson_point_to_wkt", before=obj, after=out, lossless=True, note="GeoJSON Point -> WKT POINT")


# Bounding box -----------------------------------------------------------------------------------------
def _bbox_from_points(points: list[dict[str, Any]], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    lons = [p["lon"] for p in points]
    lats = [p["lat"] for p in points]
    out = {"min_lon": min(lons), "min_lat": min(lats), "max_lon": max(lons), "max_lat": max(lats)}
    return out, _receipt("bbox_from_points", before=points, after=out, lossless=False, note="min/max envelope of a point list")


def _bbox_contains(arg: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    b, p = arg["bbox"], arg["point"]
    inside = b["min_lon"] <= p["lon"] <= b["max_lon"] and b["min_lat"] <= p["lat"] <= b["max_lat"]
    out = {"contains": inside}
    return out, _receipt("bbox_contains", before=arg, after=out, lossless=True, note="point-in-bbox test (inclusive)")


def _bbox_center(b: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"lon": (b["min_lon"] + b["max_lon"]) / 2, "lat": (b["min_lat"] + b["max_lat"]) / 2}
    return out, _receipt("bbox_center", before=b, after=out, lossless=False, note="centroid of a bbox")


def _bbox_area_deg(b: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"area_deg2": (b["max_lon"] - b["min_lon"]) * (b["max_lat"] - b["min_lat"])}
    return out, _receipt("bbox_area_deg", before=b, after=out, lossless=False, note="planar degree^2 area of a bbox")


# GTFS -------------------------------------------------------------------------------------------------
def _gtfs_time_to_seconds(text: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    h, m, s = text.split(":")
    out = int(h) * 3600 + int(m) * 60 + int(s)
    return out, _receipt("gtfs_time_to_seconds", before=text, after=out, lossless=True, note="GTFS HH:MM:SS (may exceed 24h) -> seconds")


def _gtfs_seconds_to_time(n: int, **_kw: Any) -> tuple[str, dict[str, Any]]:
    h, m, s = n // 3600, (n % 3600) // 60, n % 60
    out = f"{h:02d}:{m:02d}:{s:02d}"
    return out, _receipt("gtfs_seconds_to_time", before=n, after=out, lossless=True, note="seconds -> GTFS HH:MM:SS")


def _gtfs_stop_parse(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    f = text.split(",")
    out = {"stop_id": f[0], "stop_name": f[1], "stop_lat": float(f[2]), "stop_lon": float(f[3])}
    return out, _receipt("gtfs_stop_parse", before=text, after=out, lossless=True, note="GTFS stops.txt record -> dict")


def _gtfs_stop_emit(obj: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"{obj['stop_id']},{obj['stop_name']},{_num(obj['stop_lat'])},{_num(obj['stop_lon'])}"
    return out, _receipt("gtfs_stop_emit", before=obj, after=out, lossless=True, note="dict -> GTFS stops.txt record")


# iCalendar VEVENT -------------------------------------------------------------------------------------
def _ical_vevent_parse(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    d: dict[str, str] = {}
    for line in text.split("\n"):
        if ":" in line and not line.startswith(("BEGIN", "END")):
            k, v = line.split(":", 1)
            d[k] = v
    out = {"uid": d.get("UID"), "dtstart": d.get("DTSTART"), "dtend": d.get("DTEND"), "summary": d.get("SUMMARY")}
    return out, _receipt("ical_vevent_parse", before=text, after=out, lossless=True, note="VEVENT block -> field dict")


def _ical_vevent_emit(obj: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join([
        "BEGIN:VEVENT", f"UID:{obj['uid']}", f"DTSTART:{obj['dtstart']}",
        f"DTEND:{obj['dtend']}", f"SUMMARY:{obj['summary']}", "END:VEVENT",
    ])
    return out, _receipt("ical_vevent_emit", before=obj, after=out, lossless=True, note="field dict -> VEVENT block")


def _ical_escape_text(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    return out, _receipt("ical_escape_text", before=text, after=out, lossless=True, note="RFC5545 TEXT escape; unescape restores")


def _ical_unescape_text(text: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = text.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")
    return out, _receipt("ical_unescape_text", before=text, after=out, lossless=True, note="RFC5545 TEXT unescape")


def _ical_datetime_parse(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {
        "year": int(text[0:4]), "month": int(text[4:6]), "day": int(text[6:8]),
        "hour": int(text[9:11]), "minute": int(text[11:13]), "second": int(text[13:15]),
        "utc": text.endswith("Z"),
    }
    return out, _receipt("ical_datetime_parse", before=text, after=out, lossless=True, note="iCal basic datetime (YYYYMMDDThhmmssZ) -> parts")


# vCard (synthetic public contact SHAPE only) ----------------------------------------------------------
def _vcard_parse(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    d: dict[str, str] = {}
    for line in text.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            d[k] = v
    out = {"fn": d.get("FN"), "email": d.get("EMAIL"), "tel": d.get("TEL")}
    return out, _receipt("vcard_parse", before=text, after=out, lossless=True, note="vCard block -> {fn,email,tel} (shape only)")


def _vcard_emit(obj: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = "\n".join([
        "BEGIN:VCARD", "VERSION:3.0", f"FN:{obj['fn']}", f"EMAIL:{obj['email']}",
        f"TEL:{obj['tel']}", "END:VCARD",
    ])
    return out, _receipt("vcard_emit", before=obj, after=out, lossless=True, note="{fn,email,tel} -> vCard block (shape only)")


# GPX --------------------------------------------------------------------------------------------------
def _gpx_trackpoint_parse(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    lat = re.search(r'lat="([^"]+)"', text).group(1)
    lon = re.search(r'lon="([^"]+)"', text).group(1)
    ele_m = re.search(r"<ele>([^<]+)</ele>", text)
    out = {"lat": float(lat), "lon": float(lon), "ele": float(ele_m.group(1)) if ele_m else None}
    return out, _receipt("gpx_trackpoint_parse", before=text, after=out, lossless=True, note="GPX <trkpt> -> {lat,lon,ele}")


def _gpx_trackpoint_emit(obj: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f'<trkpt lat="{_num(obj["lat"])}" lon="{_num(obj["lon"])}"><ele>{_num(obj["ele"])}</ele></trkpt>'
    return out, _receipt("gpx_trackpoint_emit", before=obj, after=out, lossless=True, note="{lat,lon,ele} -> GPX <trkpt>")


# lat/long normalize -----------------------------------------------------------------------------------
def _lon_normalize(n: float, **_kw: Any) -> tuple[float, dict[str, Any]]:
    out = ((n + 180.0) % 360.0) - 180.0
    return out, _receipt("lon_normalize", before=n, after=out, lossless=False, note="wrap longitude into [-180,180)")


def _lat_clamp(n: float, **_kw: Any) -> tuple[float, dict[str, Any]]:
    out = max(-90.0, min(90.0, n))
    return out, _receipt("lat_clamp", before=n, after=out, lossless=False, note="clamp latitude into [-90,90]")


def _latlon_round(arg: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"lon": round(arg["lon"], 5), "lat": round(arg["lat"], 5)}
    return out, _receipt("latlon_round", before=arg, after=out, lossless=False, note="round coordinate pair to 5 decimals (~1.1m)")


def _dms_to_decimal(arg: dict[str, Any], **_kw: Any) -> tuple[float, dict[str, Any]]:
    val = arg["deg"] + arg["min"] / 60.0 + arg["sec"] / 3600.0
    if arg["hemi"] in ("S", "W"):
        val = -val
    out = round(val, 6)
    return out, _receipt("dms_to_decimal", before=arg, after=out, lossless=False, note="degrees/minutes/seconds+hemisphere -> signed decimal degrees")


def _decimal_to_dms(arg: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    v, axis = arg["value"], arg["axis"]
    hemi = ("N" if v >= 0 else "S") if axis == "lat" else ("E" if v >= 0 else "W")
    v = abs(v)
    deg = int(v)
    minutes = int((v - deg) * 60)
    sec = round((v - deg - minutes / 60.0) * 3600.0, 2)
    out = {"deg": deg, "min": minutes, "sec": sec, "hemi": hemi}
    return out, _receipt("decimal_to_dms", before=arg, after=out, lossless=False, note="signed decimal degrees -> DMS+hemisphere")


#: new pure mutators to plug into the shared registry (idempotent registration; never overwrites)
_NEW_MUTATORS = {
    "geojson_parse_point": _geojson_parse_point, "geojson_emit_point": _geojson_emit_point,
    "geojson_validate_point": _geojson_validate_point, "geojson_parse_linestring": _geojson_parse_linestring,
    "geojson_bbox": _geojson_bbox,
    "wkt_parse_point": _wkt_parse_point, "wkt_emit_point": _wkt_emit_point,
    "wkt_parse_linestring": _wkt_parse_linestring, "wkt_point_to_geojson": _wkt_point_to_geojson,
    "geojson_point_to_wkt": _geojson_point_to_wkt,
    "bbox_from_points": _bbox_from_points, "bbox_contains": _bbox_contains,
    "bbox_center": _bbox_center, "bbox_area_deg": _bbox_area_deg,
    "gtfs_time_to_seconds": _gtfs_time_to_seconds, "gtfs_seconds_to_time": _gtfs_seconds_to_time,
    "gtfs_stop_parse": _gtfs_stop_parse, "gtfs_stop_emit": _gtfs_stop_emit,
    "ical_vevent_parse": _ical_vevent_parse, "ical_vevent_emit": _ical_vevent_emit,
    "ical_escape_text": _ical_escape_text, "ical_unescape_text": _ical_unescape_text,
    "ical_datetime_parse": _ical_datetime_parse,
    "vcard_parse": _vcard_parse, "vcard_emit": _vcard_emit,
    "gpx_trackpoint_parse": _gpx_trackpoint_parse, "gpx_trackpoint_emit": _gpx_trackpoint_emit,
    "lon_normalize": _lon_normalize, "lat_clamp": _lat_clamp, "latlon_round": _latlon_round,
    "dms_to_decimal": _dms_to_decimal, "decimal_to_dms": _decimal_to_dms,
}


def register_new_mutators() -> None:
    """Plug the geo/calendar mutators into the shared MUTATOR_REGISTRY (setdefault — idempotent, never overwrites)."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── the leaf primitives: each a REAL transform with a concrete fixture + expected (+ inverse where reversible) ──
# spec fields: id, capability, mutator, fixture, expected, inverse?, input_edge, output_edge
LEAF_SPECS: list[dict[str, Any]] = [
    # GeoJSON
    {"id": "prim:geo:geojson_parse_point", "capability": "parse a GeoJSON Point into a lon/lat pair",
     "mutator": "geojson_parse_point", "fixture": {"type": "Point", "coordinates": [30.0, 10.0]},
     "expected": {"lon": 30.0, "lat": 10.0}, "input_edge": "GeoJSONPoint", "output_edge": "LatLonPoint"},
    {"id": "prim:geo:geojson_emit_point", "capability": "emit a GeoJSON Point from a lon/lat pair",
     "mutator": "geojson_emit_point", "fixture": {"lon": 30.0, "lat": 10.0},
     "expected": {"type": "Point", "coordinates": [30.0, 10.0]}, "inverse": "geojson_parse_point",
     "input_edge": "LatLonPoint", "output_edge": "GeoJSONPoint"},
    {"id": "prim:geo:geojson_validate_point", "capability": "structurally validate a GeoJSON Point",
     "mutator": "geojson_validate_point", "fixture": {"type": "Point", "coordinates": [1.0, 2.0]},
     "expected": {"valid": True, "type": "Point"}, "input_edge": "GeoJSONPoint", "output_edge": "ValidationResult"},
    {"id": "prim:geo:geojson_parse_linestring", "capability": "parse a GeoJSON LineString into a point list",
     "mutator": "geojson_parse_linestring",
     "fixture": {"type": "LineString", "coordinates": [[30.0, 10.0], [10.0, 30.0], [40.0, 40.0]]},
     "expected": {"points": [{"lon": 30.0, "lat": 10.0}, {"lon": 10.0, "lat": 30.0}, {"lon": 40.0, "lat": 40.0}]},
     "input_edge": "GeoJSONLineString", "output_edge": "LatLonPointList"},
    {"id": "prim:geo:geojson_bbox", "capability": "compute the bounding box of a GeoJSON coordinate list",
     "mutator": "geojson_bbox",
     "fixture": {"type": "LineString", "coordinates": [[30.0, 10.0], [10.0, 30.0], [40.0, 5.0]]},
     "expected": [10.0, 5.0, 40.0, 30.0], "input_edge": "GeoJSONLineString", "output_edge": "BoundingBoxArray"},
    # WKT
    {"id": "prim:geo:wkt_parse_point", "capability": "parse a WKT POINT into a lon/lat pair",
     "mutator": "wkt_parse_point", "fixture": "POINT (30 10)", "expected": {"lon": 30.0, "lat": 10.0},
     "input_edge": "WKTPoint", "output_edge": "LatLonPoint"},
    {"id": "prim:geo:wkt_emit_point", "capability": "emit a WKT POINT from a lon/lat pair",
     "mutator": "wkt_emit_point", "fixture": {"lon": 30.0, "lat": 10.0}, "expected": "POINT (30 10)",
     "inverse": "wkt_parse_point", "input_edge": "LatLonPoint", "output_edge": "WKTPoint"},
    {"id": "prim:geo:wkt_parse_linestring", "capability": "parse a WKT LINESTRING into a point list",
     "mutator": "wkt_parse_linestring", "fixture": "LINESTRING (30 10, 10 30, 40 40)",
     "expected": {"points": [{"lon": 30.0, "lat": 10.0}, {"lon": 10.0, "lat": 30.0}, {"lon": 40.0, "lat": 40.0}]},
     "input_edge": "WKTLineString", "output_edge": "LatLonPointList"},
    {"id": "prim:geo:wkt_point_to_geojson", "capability": "convert a WKT POINT into a GeoJSON Point",
     "mutator": "wkt_point_to_geojson", "fixture": "POINT (30 10)",
     "expected": {"type": "Point", "coordinates": [30.0, 10.0]},
     "input_edge": "WKTPoint", "output_edge": "GeoJSONPoint"},
    {"id": "prim:geo:geojson_point_to_wkt", "capability": "convert a GeoJSON Point into a WKT POINT",
     "mutator": "geojson_point_to_wkt", "fixture": {"type": "Point", "coordinates": [30.0, 10.0]},
     "expected": "POINT (30 10)", "inverse": "wkt_point_to_geojson",
     "input_edge": "GeoJSONPoint", "output_edge": "WKTPoint"},
    # Bounding box
    {"id": "prim:geo:bbox_from_points", "capability": "compute a bounding box from a lon/lat point list",
     "mutator": "bbox_from_points",
     "fixture": [{"lon": 30.0, "lat": 10.0}, {"lon": 10.0, "lat": 30.0}, {"lon": 40.0, "lat": 5.0}],
     "expected": {"min_lon": 10.0, "min_lat": 5.0, "max_lon": 40.0, "max_lat": 30.0},
     "input_edge": "LatLonPointList", "output_edge": "BoundingBox"},
    {"id": "prim:geo:bbox_contains", "capability": "test whether a point falls inside a bounding box",
     "mutator": "bbox_contains",
     "fixture": {"bbox": {"min_lon": 10.0, "min_lat": 5.0, "max_lon": 40.0, "max_lat": 30.0}, "point": {"lon": 20.0, "lat": 15.0}},
     "expected": {"contains": True}, "input_edge": "BoundingBoxAndPoint", "output_edge": "ContainmentResult"},
    {"id": "prim:geo:bbox_center", "capability": "compute the centroid of a bounding box",
     "mutator": "bbox_center", "fixture": {"min_lon": 10.0, "min_lat": 5.0, "max_lon": 40.0, "max_lat": 30.0},
     "expected": {"lon": 25.0, "lat": 17.5}, "input_edge": "BoundingBox", "output_edge": "LatLonPoint"},
    {"id": "prim:geo:bbox_area_deg", "capability": "compute the planar degree^2 area of a bounding box",
     "mutator": "bbox_area_deg", "fixture": {"min_lon": 10.0, "min_lat": 5.0, "max_lon": 40.0, "max_lat": 30.0},
     "expected": {"area_deg2": 750.0}, "input_edge": "BoundingBox", "output_edge": "AreaDegrees"},
    # GTFS
    {"id": "prim:geo:gtfs_time_to_seconds", "capability": "convert a GTFS HH:MM:SS time (may exceed 24h) to seconds",
     "mutator": "gtfs_time_to_seconds", "fixture": "25:30:00", "expected": 91800,
     "inverse": "gtfs_seconds_to_time", "input_edge": "GTFSTime", "output_edge": "SecondsInt"},
    {"id": "prim:geo:gtfs_seconds_to_time", "capability": "convert seconds to a GTFS HH:MM:SS time string",
     "mutator": "gtfs_seconds_to_time", "fixture": 91800, "expected": "25:30:00",
     "inverse": "gtfs_time_to_seconds", "input_edge": "SecondsInt", "output_edge": "GTFSTime"},
    {"id": "prim:geo:gtfs_stop_parse", "capability": "parse a GTFS stops.txt record into a dict",
     "mutator": "gtfs_stop_parse", "fixture": "S1,Main St,40.5,-74.2",
     "expected": {"stop_id": "S1", "stop_name": "Main St", "stop_lat": 40.5, "stop_lon": -74.2},
     "input_edge": "GTFSStopRecord", "output_edge": "StopDict"},
    {"id": "prim:geo:gtfs_stop_emit", "capability": "emit a GTFS stops.txt record from a dict",
     "mutator": "gtfs_stop_emit", "fixture": {"stop_id": "S1", "stop_name": "Main St", "stop_lat": 40.5, "stop_lon": -74.2},
     "expected": "S1,Main St,40.5,-74.2", "inverse": "gtfs_stop_parse",
     "input_edge": "StopDict", "output_edge": "GTFSStopRecord"},
    # iCalendar VEVENT
    {"id": "prim:cal:ical_vevent_parse", "capability": "parse an iCalendar VEVENT block into a field dict",
     "mutator": "ical_vevent_parse",
     "fixture": "BEGIN:VEVENT\nUID:abc123\nDTSTART:20260703T120000Z\nDTEND:20260703T130000Z\nSUMMARY:Team Sync\nEND:VEVENT",
     "expected": {"uid": "abc123", "dtstart": "20260703T120000Z", "dtend": "20260703T130000Z", "summary": "Team Sync"},
     "input_edge": "ICalVEvent", "output_edge": "EventDict"},
    {"id": "prim:cal:ical_vevent_emit", "capability": "emit an iCalendar VEVENT block from a field dict",
     "mutator": "ical_vevent_emit",
     "fixture": {"uid": "abc123", "dtstart": "20260703T120000Z", "dtend": "20260703T130000Z", "summary": "Team Sync"},
     "expected": "BEGIN:VEVENT\nUID:abc123\nDTSTART:20260703T120000Z\nDTEND:20260703T130000Z\nSUMMARY:Team Sync\nEND:VEVENT",
     "inverse": "ical_vevent_parse", "input_edge": "EventDict", "output_edge": "ICalVEvent"},
    {"id": "prim:cal:ical_escape_text", "capability": "RFC5545-escape an iCalendar TEXT value",
     "mutator": "ical_escape_text", "fixture": "Meeting, room; 5", "expected": "Meeting\\, room\\; 5",
     "inverse": "ical_unescape_text", "input_edge": "PlainText", "output_edge": "ICalEscapedText"},
    {"id": "prim:cal:ical_unescape_text", "capability": "RFC5545-unescape an iCalendar TEXT value",
     "mutator": "ical_unescape_text", "fixture": "Meeting\\, room\\; 5", "expected": "Meeting, room; 5",
     "inverse": "ical_escape_text", "input_edge": "ICalEscapedText", "output_edge": "PlainText"},
    {"id": "prim:cal:ical_datetime_parse", "capability": "decompose an iCal basic datetime into calendar parts",
     "mutator": "ical_datetime_parse", "fixture": "20260703T120000Z",
     "expected": {"year": 2026, "month": 7, "day": 3, "hour": 12, "minute": 0, "second": 0, "utc": True},
     "input_edge": "ICalDateTime", "output_edge": "CalendarParts"},
    # vCard (synthetic public shape only)
    {"id": "prim:cal:vcard_parse", "capability": "parse a vCard block into a contact shape (fn/email/tel)",
     "mutator": "vcard_parse",
     "fixture": "BEGIN:VCARD\nVERSION:3.0\nFN:Jane Doe\nEMAIL:jane@example.com\nTEL:+15550000000\nEND:VCARD",
     "expected": {"fn": "Jane Doe", "email": "jane@example.com", "tel": "+15550000000"},
     "input_edge": "VCardRecord", "output_edge": "ContactDict"},
    {"id": "prim:cal:vcard_emit", "capability": "emit a vCard block from a contact shape (fn/email/tel)",
     "mutator": "vcard_emit", "fixture": {"fn": "Jane Doe", "email": "jane@example.com", "tel": "+15550000000"},
     "expected": "BEGIN:VCARD\nVERSION:3.0\nFN:Jane Doe\nEMAIL:jane@example.com\nTEL:+15550000000\nEND:VCARD",
     "inverse": "vcard_parse", "input_edge": "ContactDict", "output_edge": "VCardRecord"},
    # GPX
    {"id": "prim:geo:gpx_trackpoint_parse", "capability": "parse a GPX <trkpt> into a lat/lon/ele dict",
     "mutator": "gpx_trackpoint_parse", "fixture": '<trkpt lat="40.5" lon="-74.2"><ele>10.0</ele></trkpt>',
     "expected": {"lat": 40.5, "lon": -74.2, "ele": 10.0}, "input_edge": "GPXTrackPoint", "output_edge": "TrackPointDict"},
    {"id": "prim:geo:gpx_trackpoint_emit", "capability": "emit a GPX <trkpt> from a lat/lon/ele dict",
     "mutator": "gpx_trackpoint_emit", "fixture": {"lat": 40.5, "lon": -74.2, "ele": 10.0},
     "expected": '<trkpt lat="40.5" lon="-74.2"><ele>10</ele></trkpt>',
     "input_edge": "TrackPointDict", "output_edge": "GPXTrackPoint"},
    # lat/long normalize
    {"id": "prim:geo:lon_normalize", "capability": "wrap a longitude into the [-180,180) range",
     "mutator": "lon_normalize", "fixture": 190.0, "expected": -170.0,
     "input_edge": "Longitude", "output_edge": "NormalizedLongitude"},
    {"id": "prim:geo:lat_clamp", "capability": "clamp a latitude into the [-90,90] range",
     "mutator": "lat_clamp", "fixture": 95.0, "expected": 90.0,
     "input_edge": "Latitude", "output_edge": "ClampedLatitude"},
    {"id": "prim:geo:latlon_round", "capability": "round a lon/lat pair to 5 decimal places",
     "mutator": "latlon_round", "fixture": {"lon": 30.123456789, "lat": 10.987654321},
     "expected": {"lon": 30.12346, "lat": 10.98765}, "input_edge": "LatLonPoint", "output_edge": "LatLonPoint"},
    {"id": "prim:geo:dms_to_decimal", "capability": "convert DMS + hemisphere to signed decimal degrees",
     "mutator": "dms_to_decimal", "fixture": {"deg": 40, "min": 30, "sec": 0, "hemi": "N"}, "expected": 40.5,
     "input_edge": "DMSCoordinate", "output_edge": "DecimalDegrees"},
    {"id": "prim:geo:decimal_to_dms", "capability": "convert signed decimal degrees to DMS + hemisphere",
     "mutator": "decimal_to_dms", "fixture": {"value": 40.5, "axis": "lat"},
     "expected": {"deg": 40, "min": 30, "sec": 0.0, "hemi": "N"},
     "input_edge": "DecimalDegrees", "output_edge": "DMSCoordinate"},
]

#: deliberately-wrong leaf — the executed proof gate MUST leave it candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:geo:WRONG_wkt_emit_point", "capability": "WKT emit with a wrong expected output",
     "mutator": "wkt_emit_point", "fixture": {"lon": 30.0, "lat": 10.0}, "expected": "POINT (999 999)",
     "input_edge": "LatLonPoint", "output_edge": "WKTPoint"},
]

# ── GATED-EFFECT candidates: network/cloud CALLS. NEVER run through the proof runner, NEVER serves_truth=true. ──
# Each is declared honestly as candidate with an effect + a proof_obligation (live integration test w/ credential).
GATED_EFFECT_SPECS: list[dict[str, Any]] = [
    {"id": "prim:geo:gated:geocode_address_cloud", "capability": "geocode a postal address via a hosted geocoding API",
     "effect": "network_read", "proof_obligation": "live integration test with credential (geocoding API key)",
     "input_edge": "PostalAddress", "output_edge": "LatLonPoint"},
    {"id": "prim:geo:gated:reverse_geocode_cloud", "capability": "reverse-geocode a lat/lon to an address via a hosted API",
     "effect": "network_read", "proof_obligation": "live integration test with credential (geocoding API key)",
     "input_edge": "LatLonPoint", "output_edge": "PostalAddress"},
    {"id": "prim:geo:gated:timezone_by_latlon_api", "capability": "resolve the IANA timezone for a lat/lon via a hosted API",
     "effect": "network_read", "proof_obligation": "live integration test with credential (timezone API key)",
     "input_edge": "LatLonPoint", "output_edge": "IANATimezone"},
    {"id": "prim:geo:gated:distance_matrix_api", "capability": "request a travel-time distance matrix from a routing API",
     "effect": "network_read", "proof_obligation": "live integration test with credential (routing API key)",
     "input_edge": "LatLonPointList", "output_edge": "DistanceMatrix"},
    {"id": "prim:geo:gated:fetch_gtfs_realtime_feed", "capability": "fetch a GTFS-realtime vehicle-position feed over HTTP",
     "effect": "network_read", "proof_obligation": "live integration test with credential (feed URL + token)",
     "input_edge": "FeedURL", "output_edge": "GTFSRealtimeFeed"},
    {"id": "prim:cal:gated:publish_event_to_caldav", "capability": "publish a VEVENT to a CalDAV calendar server",
     "effect": "network_write", "proof_obligation": "live integration test with credential (CalDAV account)",
     "input_edge": "ICalVEvent", "output_edge": "CalDAVPutResult"},
    {"id": "prim:geo:gated:upload_gpx_object_storage", "capability": "upload a GPX track to cloud object storage",
     "effect": "network_write", "proof_obligation": "live integration test with credential (object-storage credentials)",
     "input_edge": "GPXDocument", "output_edge": "ObjectStorageURI"},
    {"id": "prim:geo:gated:write_geojson_file", "capability": "write a GeoJSON FeatureCollection to a local file",
     "effect": "file_write", "proof_obligation": "live integration test on a writable temp path",
     "input_edge": "GeoJSONFeatureCollection", "output_edge": "FilePath"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"], has_inverse=spec.get("inverse"),
    )
    receipt["capability"] = spec["capability"]
    receipt["input_edge"] = spec["input_edge"]
    receipt["output_edge"] = spec["output_edge"]
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared deterministic leaf primitive through the imported executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def _typed_row(receipt: dict[str, Any]) -> dict[str, Any]:
    """A persisted PROVEN-DETERMINISTIC row: proven (serves_truth=true) AND typed (canonical edge type_ids)."""
    return {
        "record_type": "proven_deterministic_primitive",
        "primitive_id": receipt["primitive_id"],
        "mutator": receipt["mutator"],
        "domain": DOMAIN,
        "capability": receipt["capability"],
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": receipt["input_edge"],
        "output_edge": receipt["output_edge"],
        "input_edge_type_id": canonicalize_edge(receipt["input_edge"]),
        "output_edge_type_id": canonicalize_edge(receipt["output_edge"]),
        "has_roundtrip_proof": any(p["name"] == "roundtrip_test" and p["passed"] for p in receipt["proofs"]),
        "output_hash": receipt["output_hash"],
    }


def proven_typed_rows() -> list[dict[str, Any]]:
    """Only leaves whose executed proof PASSED, each TYPED via canonicalize_edge. Sorted for determinism."""
    rows = [_typed_row(r) for r in prove_all() if r["serves_truth"] is True]
    rows.sort(key=lambda r: r["primitive_id"])
    return rows


def gated_effect_rows() -> list[dict[str, Any]]:
    """Network/effectful CALLS declared as candidates: serves_truth=false, carry effect + proof_obligation + types."""
    rows: list[dict[str, Any]] = []
    for spec in GATED_EFFECT_SPECS:
        rows.append({
            "record_type": "gated_effect_candidate",
            "primitive_id": spec["id"],
            "domain": DOMAIN,
            "capability": spec["capability"],
            # LAW: an effectful primitive is NEVER proven-true; it is a gated candidate.
            "candidate": True,
            "serves_truth": False,
            "effect": spec["effect"],
            "proof_obligation": spec["proof_obligation"],
            "verification_level": "L0_gated_effect_unproven",
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
        })
    rows.sort(key=lambda r: r["primitive_id"])
    return rows


def build_manifest(proven: list[dict[str, Any]], gated: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "domain_fmt_geo_calendar_manifest",
        "pack_id": "domain-fmt-geo-calendar-primitives",
        "domain": DOMAIN,
        "generator": "scripts/domain_fmt_geo_calendar.py",
        "generated_utc": FROZEN_TS,
        "declared_leaf_count": len(LEAF_SPECS),
        # SEPARATE, honest counts — never conflated.
        "proven_deterministic": len(proven),
        "typed": len(typed),
        "gated_effect_candidates": len(gated),
        "roundtrip_pair_count": sum(1 for r in proven if r["has_roundtrip_proof"]),
        "verification_level_proven": "L7_executed_proof",
        "gated_effect_by_type": {
            e: sum(1 for r in gated if r["effect"] == e) for e in sorted({r["effect"] for r in gated})
        },
        "proven_primitive_ids": [r["primitive_id"] for r in proven],
        "gated_effect_primitive_ids": [r["primitive_id"] for r in gated],
        "note": "serves_truth=true rows are PROVEN-DETERMINISTIC only — set solely by an executed passing proof "
                "(run_primitive_proof from scripts/mutator_registry.py), each TYPED via canonicalize_edge "
                "(scripts/build_edge_type_retrofit.py). GATED-EFFECT rows are network/cloud/file CALLS: candidate=true, "
                "serves_truth=false, each carrying an effect + a live-integration proof_obligation; they are NEVER run "
                "through the proof runner. A deliberately-wrong deterministic fixture stays candidate and is never "
                "persisted here. Domain law: no insurance; geo/calendar only; synthetic/public shapes (no real PII).",
    }


def write_pack() -> dict[str, Any]:
    proven = proven_typed_rows()
    gated = gated_effect_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Two SEPARATE sections of the shard: a proven-deterministic header row, then proven rows, then a gated header
    # row, then gated rows — so the two families are never conflated when the shard is streamed.
    lines: list[str] = []
    lines.append(json.dumps({"record_type": "section_marker", "section": "proven_deterministic",
                             "domain": DOMAIN, "count": len(proven)}, sort_keys=True))
    lines += [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in proven]
    lines.append(json.dumps({"record_type": "section_marker", "section": "gated_effect_candidates",
                             "domain": DOMAIN, "count": len(gated)}, sort_keys=True))
    lines += [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in gated]
    OUT_JSONL.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = build_manifest(proven, gated)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    receipts = prove_all()
    proven = proven_typed_rows()
    gated = gated_effect_rows()
    ids = [r["primitive_id"] for r in receipts]

    # a deliberately-wrong deterministic fixture must FAIL the executed proof -> stay CANDIDATE
    wrong = run_primitive_proof(
        NEGATIVE_SPECS[0]["id"], NEGATIVE_SPECS[0]["mutator"], NEGATIVE_SPECS[0]["fixture"],
        NEGATIVE_SPECS[0]["expected"], has_inverse=NEGATIVE_SPECS[0].get("inverse"))
    # a second wrong path: an un-runnable fixture (malformed WKT) -> execution error -> not promoted
    err = run_primitive_proof("prim:geo:EXEC_ERROR", "wkt_parse_point", "NOT WKT", "irrelevant")

    inverse_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_ids = {r["primitive_id"] for r in proven}
    all_ids = ids + [s["id"] for s in GATED_EFFECT_SPECS]

    checks: list[tuple[str, bool]] = [
        (">=25 deterministic leaf primitives declared", len(LEAF_SPECS) >= 25),
        ("all primitive ids unique across proven + gated", len(set(all_ids)) == len(all_ids)),
        (">=25 leaves PROVE serves_truth=true via an executed proof", len(proven) >= 25),
        ("EVERY declared leaf proved (all promoted)",
         all(r["serves_truth"] is True and r["promoted"] is True for r in receipts)),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"]) for r in receipts)),
        ("EVERY proven row carries a non-null input_edge_type_id", all(bool(r["input_edge_type_id"]) for r in proven)),
        ("EVERY proven row carries a non-null output_edge_type_id", all(bool(r["output_edge_type_id"]) for r in proven)),
        ("typed == proven_deterministic (every workable leaf is typed)",
         build_manifest(proven, gated)["typed"] == build_manifest(proven, gated)["proven_deterministic"] == len(proven)),
        ("roundtrip-inverse pairs prove reversible (roundtrip_test passed)",
         all(any(p["name"] == "roundtrip_test" and p["passed"] for p in _prove_one(s)["proofs"]) for s in inverse_specs)),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in proven_typed_rows()]
         == [json.dumps(r, sort_keys=True) for r in proven]),
        # gated-effect honesty law
        (">=1 gated-effect candidate declared", len(gated) >= 1),
        ("EVERY gated-effect row is candidate=true AND serves_truth=false",
         all(r["candidate"] is True and r["serves_truth"] is False for r in gated)),
        ("EVERY gated-effect row carries a known effect",
         all(r["effect"] in {"network_read", "network_write", "model_call", "file_write"} for r in gated)),
        ("EVERY gated-effect row carries a non-empty proof_obligation",
         all(isinstance(r["proof_obligation"], str) and r["proof_obligation"] for r in gated)),
        ("EVERY gated-effect row carries both canonical edge type_ids",
         all(bool(r["input_edge_type_id"]) and bool(r["output_edge_type_id"]) for r in gated)),
        ("NO gated-effect id leaked into the proven set", proven_ids.isdisjoint({r["primitive_id"] for r in gated})),
        # the proof gate is real
        ("a deliberately-wrong deterministic fixture FAILS (stays candidate, never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT in the persisted proven rows", NEGATIVE_SPECS[0]["id"] not in proven_ids),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - domain_fmt_geo_calendar:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - domain_fmt_geo_calendar: {len(proven)} PROVEN-DETERMINISTIC + TYPED geo/calendar leaf primitives "
          f"(serves_truth=true via executed proof, L7; all typed via canonical edge ids; "
          f"{sum(1 for r in proven if r['has_roundtrip_proof'])} reversible roundtrip pairs) and "
          f"{len(gated)} honestly-declared GATED-EFFECT candidates (candidate/serves_truth=false, each with an "
          "effect + live-integration proof_obligation). A wrong-expected fixture and an un-runnable fixture correctly "
          "stay candidate. Counts kept SEPARATE.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack()
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
