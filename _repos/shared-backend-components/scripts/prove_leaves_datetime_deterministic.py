#!/usr/bin/env python3
"""scripts.prove_leaves_datetime_deterministic — REAL executed-proof leaf primitives for the datetime_deterministic family.

Vocabulary is not capability. This module declares >=28 REAL *pure deterministic* datetime leaf primitives — every one
computed purely from its INPUT VALUE, never from the wall clock (no datetime.now / time.time / RNG / network in any
body) — runs EVERY ONE through the imported executed-proof runner (`run_primitive_proof` from
`_repos/shared-backend-components/scripts/mutator_registry.py`, which flips serves_truth false->true ONLY on a PASSING executed proof), keeps ONLY the
passers, TYPES each persisted row with canonical edge type ids (`canonicalize_edge`) so a workable primitive can chain,
and --write's them to the family file + a manifest.

ADD-ONLY / flexible-multi-path: this is a NEW parallel path. It IMPORTS the existing machinery (never edits it) and
plugs a handful of extra PURE datetime mutators INTO the shared `MUTATOR_REGISTRY` via `setdefault` (registration, not
a rewrite — exactly the seam that module documents). serves_truth=true here is CORRECT and required: it is set ONLY by
an executed passing proof — a deliberately-wrong-expected leaf stays candidate and is never persisted. Coverage:
iso-parse-to-parts (no now()), parts-to-iso, to-epoch-seconds/days, truncate-to-day/month/hour, add-fixed-delta,
weekday-name, is-leap-year, format-yyyymmdd, and more; true inverse pairs (parse/emit, enc/dec) are proven REVERSIBLE
via a roundtrip proof. CLI: --self-test | --write [--date D]. Offline, deterministic, standalone.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import calendar as _cal
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the existing machinery — never edit it (ADD-ONLY / flexible-multi-path).
from scripts.mutator_registry import (  # noqa: E402
    INVERSE_PAIRS,
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

FAMILY = "datetime_deterministic"
OUT_DIR = _resource("data") / "dev-intel" / "proven_primitives"
OUT_JSONL = OUT_DIR / "proven_datetime_deterministic.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_datetime_deterministic.json"

# ── fixed reference constants (NO wall clock — a literal epoch anchor only) ─────────────────────────────────────────
_EPOCH = _dt.datetime(1970, 1, 1, tzinfo=_dt.timezone.utc)  # the unix epoch as a fixed literal, never "now"
_EPOCH_DATE = _dt.date(1970, 1, 1)
#: deterministic, locale-independent weekday/month names (never rely on strftime %A/%B locale)
_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
_MONTHS = ("", "January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December")
_ISO_FMT = "%Y-%m-%dT%H:%M:%S"


def _r(name: str, *, before: Any, after: Any, lossless: bool, note: str) -> dict[str, Any]:
    return _receipt(name, before=before, after=after, lossless=lossless, note=note)


# ── PURE deterministic datetime mutators — each (payload, **kwargs) -> (output, receipt). No I/O, no clock. ──────────
def dtd_iso_parse_to_parts(iso: str) -> tuple[dict[str, int], dict[str, Any]]:
    d = _dt.datetime.strptime(iso, _ISO_FMT)
    out = {"year": d.year, "month": d.month, "day": d.day, "hour": d.hour, "minute": d.minute, "second": d.second}
    return out, _r("dtd_iso_parse_to_parts", before=iso, after=out, lossless=True, note="ISO->parts; parts_to_iso restores")


def dtd_parts_to_iso(parts: dict[str, int]) -> tuple[str, dict[str, Any]]:
    out = "{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}".format(**parts)
    return out, _r("dtd_parts_to_iso", before=parts, after=out, lossless=True, note="parts->canonical ISO string")


def dtd_date_to_epoch_days(date_str: str) -> tuple[int, dict[str, Any]]:
    out = (_dt.date.fromisoformat(date_str) - _EPOCH_DATE).days
    return out, _r("dtd_date_to_epoch_days", before=date_str, after=out, lossless=True, note="days since 1970-01-01; reversible")


def dtd_epoch_days_to_date(days: int) -> tuple[str, dict[str, Any]]:
    out = (_EPOCH_DATE + _dt.timedelta(days=days)).isoformat()
    return out, _r("dtd_epoch_days_to_date", before=days, after=out, lossless=True, note="epoch-day count -> ISO date")


def dtd_iso_to_epoch_seconds(iso: str) -> tuple[int, dict[str, Any]]:
    d = _dt.datetime.strptime(iso, _ISO_FMT).replace(tzinfo=_dt.timezone.utc)
    out = int((d - _EPOCH).total_seconds())
    return out, _r("dtd_iso_to_epoch_seconds", before=iso, after=out, lossless=True, note="UTC epoch seconds; reversible")


def dtd_epoch_seconds_to_iso(seconds: int) -> tuple[str, dict[str, Any]]:
    out = (_EPOCH + _dt.timedelta(seconds=seconds)).strftime(_ISO_FMT)
    return out, _r("dtd_epoch_seconds_to_iso", before=seconds, after=out, lossless=True, note="epoch seconds -> UTC ISO string")


def dtd_format_yyyymmdd(date_str: str) -> tuple[str, dict[str, Any]]:
    d = _dt.date.fromisoformat(date_str)
    out = "{:04d}{:02d}{:02d}".format(d.year, d.month, d.day)
    return out, _r("dtd_format_yyyymmdd", before=date_str, after=out, lossless=True, note="YYYY-MM-DD -> YYYYMMDD; reversible")


def dtd_parse_yyyymmdd(compact: str) -> tuple[str, dict[str, Any]]:
    out = "{}-{}-{}".format(compact[0:4], compact[4:6], compact[6:8])
    return out, _r("dtd_parse_yyyymmdd", before=compact, after=out, lossless=True, note="YYYYMMDD -> ISO date")


def dtd_time_to_seconds(time_str: str) -> tuple[int, dict[str, Any]]:
    h, m, s = (int(p) for p in time_str.split(":"))
    out = h * 3600 + m * 60 + s
    return out, _r("dtd_time_to_seconds", before=time_str, after=out, lossless=True, note="HH:MM:SS -> seconds-of-day; reversible")


def dtd_seconds_to_time(seconds: int) -> tuple[str, dict[str, Any]]:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    out = "{:02d}:{:02d}:{:02d}".format(h, m, s)
    return out, _r("dtd_seconds_to_time", before=seconds, after=out, lossless=True, note="seconds-of-day -> HH:MM:SS")


def dtd_truncate_to_day(iso: str) -> tuple[str, dict[str, Any]]:
    out = _dt.datetime.strptime(iso, _ISO_FMT).date().isoformat()
    return out, _r("dtd_truncate_to_day", before=iso, after=out, lossless=False, note="drop time-of-day -> ISO date")


def dtd_truncate_to_month(iso: str) -> tuple[str, dict[str, Any]]:
    d = _dt.datetime.strptime(iso, _ISO_FMT)
    out = "{:04d}-{:02d}".format(d.year, d.month)
    return out, _r("dtd_truncate_to_month", before=iso, after=out, lossless=False, note="truncate to YYYY-MM")


def dtd_truncate_to_hour(iso: str) -> tuple[str, dict[str, Any]]:
    d = _dt.datetime.strptime(iso, _ISO_FMT).replace(minute=0, second=0)
    out = d.strftime(_ISO_FMT)
    return out, _r("dtd_truncate_to_hour", before=iso, after=out, lossless=False, note="zero the minute/second")


def dtd_add_days(date_str: str, days: int = 0) -> tuple[str, dict[str, Any]]:
    out = (_dt.date.fromisoformat(date_str) + _dt.timedelta(days=days)).isoformat()
    return out, _r("dtd_add_days", before=date_str, after=out, lossless=False, note=f"shift date by {days} days")


def dtd_add_seconds(iso: str, seconds: int = 0) -> tuple[str, dict[str, Any]]:
    d = _dt.datetime.strptime(iso, _ISO_FMT) + _dt.timedelta(seconds=seconds)
    out = d.strftime(_ISO_FMT)
    return out, _r("dtd_add_seconds", before=iso, after=out, lossless=False, note=f"shift by {seconds} seconds")


def dtd_add_fixed_delta(iso: str, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> tuple[str, dict[str, Any]]:
    d = _dt.datetime.strptime(iso, _ISO_FMT) + _dt.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    out = d.strftime(_ISO_FMT)
    return out, _r("dtd_add_fixed_delta", before=iso, after=out, lossless=False,
                   note=f"shift by +{days}d{hours}h{minutes}m{seconds}s")


def dtd_weekday_name(date_str: str) -> tuple[str, dict[str, Any]]:
    out = _WEEKDAYS[_dt.date.fromisoformat(date_str).weekday()]
    return out, _r("dtd_weekday_name", before=date_str, after=out, lossless=False, note="locale-independent weekday name")


def dtd_weekday_index(date_str: str) -> tuple[int, dict[str, Any]]:
    out = _dt.date.fromisoformat(date_str).weekday()
    return out, _r("dtd_weekday_index", before=date_str, after=out, lossless=False, note="Mon=0 .. Sun=6")


def dtd_iso_weekday(date_str: str) -> tuple[int, dict[str, Any]]:
    out = _dt.date.fromisoformat(date_str).isoweekday()
    return out, _r("dtd_iso_weekday", before=date_str, after=out, lossless=False, note="ISO weekday Mon=1 .. Sun=7")


def dtd_is_leap_year(year: int) -> tuple[bool, dict[str, Any]]:
    out = _cal.isleap(int(year))
    return out, _r("dtd_is_leap_year", before=year, after=out, lossless=False, note="proleptic Gregorian leap-year test")


def dtd_is_leap_year_from_date(date_str: str) -> tuple[bool, dict[str, Any]]:
    out = _cal.isleap(_dt.date.fromisoformat(date_str).year)
    return out, _r("dtd_is_leap_year_from_date", before=date_str, after=out, lossless=False, note="leap test on a date's year")


def dtd_days_in_month(parts: dict[str, int]) -> tuple[int, dict[str, Any]]:
    out = _cal.monthrange(int(parts["year"]), int(parts["month"]))[1]
    return out, _r("dtd_days_in_month", before=parts, after=out, lossless=False, note="days in {year,month}")


def dtd_day_of_year(date_str: str) -> tuple[int, dict[str, Any]]:
    out = _dt.date.fromisoformat(date_str).timetuple().tm_yday
    return out, _r("dtd_day_of_year", before=date_str, after=out, lossless=False, note="ordinal day within the year (1..366)")


def dtd_iso_week_number(date_str: str) -> tuple[int, dict[str, Any]]:
    out = _dt.date.fromisoformat(date_str).isocalendar()[1]
    return out, _r("dtd_iso_week_number", before=date_str, after=out, lossless=False, note="ISO-8601 week number")


def dtd_quarter_of_year(date_str: str) -> tuple[int, dict[str, Any]]:
    out = (_dt.date.fromisoformat(date_str).month - 1) // 3 + 1
    return out, _r("dtd_quarter_of_year", before=date_str, after=out, lossless=False, note="calendar quarter 1..4")


def dtd_month_name(month: int) -> tuple[str, dict[str, Any]]:
    out = _MONTHS[int(month)]
    return out, _r("dtd_month_name", before=month, after=out, lossless=False, note="locale-independent month name")


def dtd_extract_year(iso: str) -> tuple[int, dict[str, Any]]:
    out = _dt.datetime.strptime(iso, _ISO_FMT).year
    return out, _r("dtd_extract_year", before=iso, after=out, lossless=False, note="extract year field")


def dtd_extract_month(iso: str) -> tuple[int, dict[str, Any]]:
    out = _dt.datetime.strptime(iso, _ISO_FMT).month
    return out, _r("dtd_extract_month", before=iso, after=out, lossless=False, note="extract month field")


def dtd_extract_day(iso: str) -> tuple[int, dict[str, Any]]:
    out = _dt.datetime.strptime(iso, _ISO_FMT).day
    return out, _r("dtd_extract_day", before=iso, after=out, lossless=False, note="extract day field")


def dtd_extract_time(iso: str) -> tuple[str, dict[str, Any]]:
    out = _dt.datetime.strptime(iso, _ISO_FMT).strftime("%H:%M:%S")
    return out, _r("dtd_extract_time", before=iso, after=out, lossless=False, note="extract HH:MM:SS")


def dtd_is_weekend(date_str: str) -> tuple[bool, dict[str, Any]]:
    out = _dt.date.fromisoformat(date_str).weekday() >= 5
    return out, _r("dtd_is_weekend", before=date_str, after=out, lossless=False, note="Sat/Sun -> True")


def dtd_end_of_month(date_str: str) -> tuple[str, dict[str, Any]]:
    d = _dt.date.fromisoformat(date_str)
    last = _cal.monthrange(d.year, d.month)[1]
    out = _dt.date(d.year, d.month, last).isoformat()
    return out, _r("dtd_end_of_month", before=date_str, after=out, lossless=False, note="last calendar day of the month")


def dtd_days_between(pair: list[str]) -> tuple[int, dict[str, Any]]:
    a, b = _dt.date.fromisoformat(pair[0]), _dt.date.fromisoformat(pair[1])
    out = (b - a).days
    return out, _r("dtd_days_between", before=pair, after=out, lossless=False, note="whole days from pair[0] to pair[1]")


def dtd_seconds_between(pair: list[str]) -> tuple[int, dict[str, Any]]:
    a = _dt.datetime.strptime(pair[0], _ISO_FMT)
    b = _dt.datetime.strptime(pair[1], _ISO_FMT)
    out = int((b - a).total_seconds())
    return out, _r("dtd_seconds_between", before=pair, after=out, lossless=False, note="whole seconds from pair[0] to pair[1]")


#: new pure datetime mutators to plug into the shared registry (idempotent registration; never overwrites)
_NEW_MUTATORS = {
    "dtd_iso_parse_to_parts": dtd_iso_parse_to_parts, "dtd_parts_to_iso": dtd_parts_to_iso,
    "dtd_date_to_epoch_days": dtd_date_to_epoch_days, "dtd_epoch_days_to_date": dtd_epoch_days_to_date,
    "dtd_iso_to_epoch_seconds": dtd_iso_to_epoch_seconds, "dtd_epoch_seconds_to_iso": dtd_epoch_seconds_to_iso,
    "dtd_format_yyyymmdd": dtd_format_yyyymmdd, "dtd_parse_yyyymmdd": dtd_parse_yyyymmdd,
    "dtd_time_to_seconds": dtd_time_to_seconds, "dtd_seconds_to_time": dtd_seconds_to_time,
    "dtd_truncate_to_day": dtd_truncate_to_day, "dtd_truncate_to_month": dtd_truncate_to_month,
    "dtd_truncate_to_hour": dtd_truncate_to_hour, "dtd_add_days": dtd_add_days, "dtd_add_seconds": dtd_add_seconds,
    "dtd_add_fixed_delta": dtd_add_fixed_delta, "dtd_weekday_name": dtd_weekday_name,
    "dtd_weekday_index": dtd_weekday_index, "dtd_iso_weekday": dtd_iso_weekday, "dtd_is_leap_year": dtd_is_leap_year,
    "dtd_is_leap_year_from_date": dtd_is_leap_year_from_date, "dtd_days_in_month": dtd_days_in_month,
    "dtd_day_of_year": dtd_day_of_year, "dtd_iso_week_number": dtd_iso_week_number,
    "dtd_quarter_of_year": dtd_quarter_of_year, "dtd_month_name": dtd_month_name,
    "dtd_extract_year": dtd_extract_year, "dtd_extract_month": dtd_extract_month, "dtd_extract_day": dtd_extract_day,
    "dtd_extract_time": dtd_extract_time, "dtd_is_weekend": dtd_is_weekend, "dtd_end_of_month": dtd_end_of_month,
    "dtd_days_between": dtd_days_between, "dtd_seconds_between": dtd_seconds_between,
}
_NEW_INVERSE_PAIRS = [
    ("dtd_iso_parse_to_parts", "dtd_parts_to_iso"),
    ("dtd_date_to_epoch_days", "dtd_epoch_days_to_date"),
    ("dtd_iso_to_epoch_seconds", "dtd_epoch_seconds_to_iso"),
    ("dtd_format_yyyymmdd", "dtd_parse_yyyymmdd"),
    ("dtd_time_to_seconds", "dtd_seconds_to_time"),
]


def register_new_mutators() -> None:
    """Plug the extra pure datetime mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)
    for pair in _NEW_INVERSE_PAIRS:
        if pair not in INVERSE_PAIRS:
            INVERSE_PAIRS.append(pair)


register_new_mutators()


# ── the leaf primitives: each a REAL pure-datetime capability with a concrete fixture + expected (+ optional inverse) ──
# spec fields: id, capability, mutator, fixture, expected, args, inverse, input_edge, output_edge
LEAF_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:dtd_iso_parse_to_parts", "capability": "parse an ISO datetime string to its calendar parts",
     "mutator": "dtd_iso_parse_to_parts", "fixture": "2024-02-29T13:45:30",
     "expected": {"year": 2024, "month": 2, "day": 29, "hour": 13, "minute": 45, "second": 30},
     "inverse": "dtd_parts_to_iso", "input_edge": "Text", "output_edge": "DateParts"},
    {"id": "prim:leaf:dtd_parts_to_iso", "capability": "render calendar parts back to a canonical ISO string",
     "mutator": "dtd_parts_to_iso",
     "fixture": {"year": 2024, "month": 2, "day": 29, "hour": 13, "minute": 45, "second": 30},
     "expected": "2024-02-29T13:45:30", "input_edge": "DateParts", "output_edge": "IsoString"},
    {"id": "prim:leaf:dtd_date_to_epoch_days", "capability": "count whole days since the unix epoch date",
     "mutator": "dtd_date_to_epoch_days", "fixture": "2024-02-29", "expected": 19782,
     "inverse": "dtd_epoch_days_to_date", "input_edge": "DateString", "output_edge": "EpochDays"},
    {"id": "prim:leaf:dtd_epoch_days_to_date", "capability": "convert an epoch-day count back to an ISO date",
     "mutator": "dtd_epoch_days_to_date", "fixture": 19782, "expected": "2024-02-29",
     "input_edge": "EpochDays", "output_edge": "DateString"},
    {"id": "prim:leaf:dtd_iso_to_epoch_seconds", "capability": "convert an ISO datetime to UTC epoch seconds",
     "mutator": "dtd_iso_to_epoch_seconds", "fixture": "2024-02-29T13:45:30", "expected": 1709214330,
     "inverse": "dtd_epoch_seconds_to_iso", "input_edge": "IsoString", "output_edge": "Epoch"},
    {"id": "prim:leaf:dtd_epoch_seconds_to_iso", "capability": "convert UTC epoch seconds back to an ISO datetime",
     "mutator": "dtd_epoch_seconds_to_iso", "fixture": 1709214330, "expected": "2024-02-29T13:45:30",
     "input_edge": "Epoch", "output_edge": "IsoString"},
    {"id": "prim:leaf:dtd_format_yyyymmdd", "capability": "format an ISO date as a compact YYYYMMDD token",
     "mutator": "dtd_format_yyyymmdd", "fixture": "2024-02-29", "expected": "20240229",
     "inverse": "dtd_parse_yyyymmdd", "input_edge": "DateString", "output_edge": "YyyyMmdd"},
    {"id": "prim:leaf:dtd_parse_yyyymmdd", "capability": "parse a compact YYYYMMDD token to an ISO date",
     "mutator": "dtd_parse_yyyymmdd", "fixture": "20240229", "expected": "2024-02-29",
     "input_edge": "YyyyMmdd", "output_edge": "DateString"},
    {"id": "prim:leaf:dtd_time_to_seconds", "capability": "convert HH:MM:SS to seconds-of-day",
     "mutator": "dtd_time_to_seconds", "fixture": "13:45:30", "expected": 49530,
     "inverse": "dtd_seconds_to_time", "input_edge": "TimeString", "output_edge": "Integer"},
    {"id": "prim:leaf:dtd_seconds_to_time", "capability": "convert seconds-of-day back to HH:MM:SS",
     "mutator": "dtd_seconds_to_time", "fixture": 49530, "expected": "13:45:30",
     "input_edge": "Integer", "output_edge": "TimeString"},
    {"id": "prim:leaf:dtd_truncate_to_day", "capability": "truncate an ISO datetime to its date",
     "mutator": "dtd_truncate_to_day", "fixture": "2024-02-29T13:45:30", "expected": "2024-02-29",
     "input_edge": "IsoString", "output_edge": "DateString"},
    {"id": "prim:leaf:dtd_truncate_to_month", "capability": "truncate an ISO datetime to YYYY-MM",
     "mutator": "dtd_truncate_to_month", "fixture": "2024-02-29T13:45:30", "expected": "2024-02",
     "input_edge": "IsoString", "output_edge": "Text"},
    {"id": "prim:leaf:dtd_truncate_to_hour", "capability": "truncate an ISO datetime to the hour",
     "mutator": "dtd_truncate_to_hour", "fixture": "2024-02-29T13:45:30", "expected": "2024-02-29T13:00:00",
     "input_edge": "IsoString", "output_edge": "IsoString"},
    {"id": "prim:leaf:dtd_add_days", "capability": "add a fixed number of days to an ISO date",
     "mutator": "dtd_add_days", "fixture": "2024-02-28", "expected": "2024-02-29", "args": {"days": 1},
     "input_edge": "DateString", "output_edge": "DateString"},
    {"id": "prim:leaf:dtd_add_seconds", "capability": "add a fixed number of seconds to an ISO datetime",
     "mutator": "dtd_add_seconds", "fixture": "2024-02-29T13:45:30", "expected": "2024-02-29T13:46:00",
     "args": {"seconds": 30}, "input_edge": "IsoString", "output_edge": "IsoString"},
    {"id": "prim:leaf:dtd_add_fixed_delta", "capability": "add a fixed d/h/m/s delta to an ISO datetime",
     "mutator": "dtd_add_fixed_delta", "fixture": "2024-02-29T13:45:30", "expected": "2024-03-01T14:46:31",
     "args": {"days": 1, "hours": 1, "minutes": 1, "seconds": 1}, "input_edge": "IsoString", "output_edge": "IsoString"},
    {"id": "prim:leaf:dtd_weekday_name", "capability": "name the weekday of an ISO date (locale-independent)",
     "mutator": "dtd_weekday_name", "fixture": "2024-02-29", "expected": "Thursday",
     "input_edge": "DateString", "output_edge": "Weekday"},
    {"id": "prim:leaf:dtd_weekday_index", "capability": "index the weekday of an ISO date (Mon=0)",
     "mutator": "dtd_weekday_index", "fixture": "2024-02-29", "expected": 3,
     "input_edge": "DateString", "output_edge": "WeekdayIndex"},
    {"id": "prim:leaf:dtd_iso_weekday", "capability": "ISO weekday of a date (Mon=1..Sun=7)",
     "mutator": "dtd_iso_weekday", "fixture": "2024-02-29", "expected": 4,
     "input_edge": "DateString", "output_edge": "WeekdayIndex"},
    {"id": "prim:leaf:dtd_is_leap_year", "capability": "test whether a year is a leap year",
     "mutator": "dtd_is_leap_year", "fixture": 2024, "expected": True,
     "input_edge": "Year", "output_edge": "Boolean"},
    {"id": "prim:leaf:dtd_is_leap_year_from_date", "capability": "test whether a date's year is a leap year",
     "mutator": "dtd_is_leap_year_from_date", "fixture": "2024-02-29", "expected": True,
     "input_edge": "DateString", "output_edge": "Boolean"},
    {"id": "prim:leaf:dtd_days_in_month", "capability": "number of days in a {year,month}",
     "mutator": "dtd_days_in_month", "fixture": {"year": 2024, "month": 2}, "expected": 29,
     "input_edge": "DateParts", "output_edge": "Integer"},
    {"id": "prim:leaf:dtd_day_of_year", "capability": "ordinal day-of-year for a date",
     "mutator": "dtd_day_of_year", "fixture": "2024-02-29", "expected": 60,
     "input_edge": "DateString", "output_edge": "Integer"},
    {"id": "prim:leaf:dtd_iso_week_number", "capability": "ISO-8601 week number for a date",
     "mutator": "dtd_iso_week_number", "fixture": "2024-02-29", "expected": 9,
     "input_edge": "DateString", "output_edge": "Integer"},
    {"id": "prim:leaf:dtd_quarter_of_year", "capability": "calendar quarter (1..4) for a date",
     "mutator": "dtd_quarter_of_year", "fixture": "2024-02-29", "expected": 1,
     "input_edge": "DateString", "output_edge": "Quarter"},
    {"id": "prim:leaf:dtd_month_name", "capability": "name a month number (locale-independent)",
     "mutator": "dtd_month_name", "fixture": 2, "expected": "February",
     "input_edge": "Month", "output_edge": "MonthName"},
    {"id": "prim:leaf:dtd_extract_year", "capability": "extract the year field from an ISO datetime",
     "mutator": "dtd_extract_year", "fixture": "2024-02-29T13:45:30", "expected": 2024,
     "input_edge": "IsoString", "output_edge": "Year"},
    {"id": "prim:leaf:dtd_extract_month", "capability": "extract the month field from an ISO datetime",
     "mutator": "dtd_extract_month", "fixture": "2024-02-29T13:45:30", "expected": 2,
     "input_edge": "IsoString", "output_edge": "Month"},
    {"id": "prim:leaf:dtd_extract_day", "capability": "extract the day field from an ISO datetime",
     "mutator": "dtd_extract_day", "fixture": "2024-02-29T13:45:30", "expected": 29,
     "input_edge": "IsoString", "output_edge": "Day"},
    {"id": "prim:leaf:dtd_extract_time", "capability": "extract HH:MM:SS from an ISO datetime",
     "mutator": "dtd_extract_time", "fixture": "2024-02-29T13:45:30", "expected": "13:45:30",
     "input_edge": "IsoString", "output_edge": "TimeString"},
    {"id": "prim:leaf:dtd_is_weekend", "capability": "test whether a date falls on the weekend",
     "mutator": "dtd_is_weekend", "fixture": "2024-03-02", "expected": True,
     "input_edge": "DateString", "output_edge": "Boolean"},
    {"id": "prim:leaf:dtd_end_of_month", "capability": "last calendar day of a date's month",
     "mutator": "dtd_end_of_month", "fixture": "2024-02-15", "expected": "2024-02-29",
     "input_edge": "DateString", "output_edge": "DateString"},
    {"id": "prim:leaf:dtd_days_between", "capability": "whole days between two ISO dates",
     "mutator": "dtd_days_between", "fixture": ["2024-01-01", "2024-03-01"], "expected": 60,
     "input_edge": "DateRange", "output_edge": "Integer"},
    {"id": "prim:leaf:dtd_seconds_between", "capability": "whole seconds between two ISO datetimes",
     "mutator": "dtd_seconds_between", "fixture": ["2024-01-01T00:00:00", "2024-01-01T01:00:00"], "expected": 3600,
     "input_edge": "DateRange", "output_edge": "Integer"},
]

#: deliberately-wrong leaves — the proof gate MUST leave these candidate (never persisted as proven)
NEGATIVE_SPECS: list[dict[str, Any]] = [
    {"id": "prim:leaf:dtd_WRONG_weekday", "capability": "weekday_name with a wrong expected output",
     "mutator": "dtd_weekday_name", "fixture": "2024-02-29", "expected": "Monday",
     "input_edge": "DateString", "output_edge": "Weekday"},
    {"id": "prim:leaf:dtd_WRONG_leap", "capability": "is_leap_year with a wrong expected output",
     "mutator": "dtd_is_leap_year", "fixture": 2023, "expected": True,
     "input_edge": "Year", "output_edge": "Boolean"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    receipt = run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )
    receipt["capability"] = spec["capability"]
    receipt["family"] = FAMILY
    # TYPE the row: canonical edge type ids so a workable primitive can chain (the 'proven but untyped' fix).
    receipt["input_edge"] = spec["input_edge"]
    receipt["output_edge"] = spec["output_edge"]
    receipt["input_edge_type_id"] = canonicalize_edge(spec["input_edge"])
    receipt["output_edge_type_id"] = canonicalize_edge(spec["output_edge"])
    return receipt


def prove_all() -> list[dict[str, Any]]:
    """Run every declared datetime leaf primitive through the imported executed-proof runner."""
    return [_prove_one(s) for s in LEAF_SPECS]


def proven_rows() -> list[dict[str, Any]]:
    """Passing, TYPED rows only (serves_truth=true, both edge type ids non-null), sorted by primitive_id."""
    rows = [
        r for r in prove_all()
        if r["serves_truth"] is True and r.get("input_edge_type_id") and r.get("output_edge_type_id")
    ]
    return sorted(rows, key=lambda r: r["primitive_id"])


def build_manifest(rows: list[dict[str, Any]], *, date: str) -> dict[str, Any]:
    typed = [r for r in rows if r.get("input_edge_type_id") and r.get("output_edge_type_id")]
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    return {
        "record_type": "proven_leaf_primitives_manifest",
        "pack_id": f"proven-leaf-primitives-{FAMILY}",
        "family": FAMILY,
        "generator": "scripts/prove_leaves_datetime_deterministic.py",
        "generated_utc": date,
        "declared_leaf_count": len(LEAF_SPECS),
        "proven_count": len(rows),
        "typed_count": len(typed),
        "proven_primitive_ids": sorted(r["primitive_id"] for r in rows),
        "verification_level": "L7_executed_proof",
        "row_counts": {OUT_JSONL.name: len(rows)},
        "total_rows": len(rows),
        "note": "serves_truth=true here is CORRECT + required — set ONLY by an executed passing proof "
                "(run_primitive_proof, imported from scripts/mutator_registry.py). Every persisted row is TYPED "
                "(input_edge_type_id + output_edge_type_id via canonicalize_edge) so it can chain. A deliberately-"
                "wrong leaf stays candidate and is never persisted here.",
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def _persist_row(r: dict[str, Any]) -> dict[str, Any]:
    """Shape the persisted family row: proven + typed + family-stamped."""
    return {
        "primitive_id": r["primitive_id"],
        "mutator": r["mutator"],
        "capability": r["capability"],
        "family": FAMILY,
        "serves_truth": True,
        "candidate": False,
        "verification_level": "L7_executed_proof",
        "input_edge": r["input_edge"],
        "output_edge": r["output_edge"],
        "input_edge_type_id": r["input_edge_type_id"],
        "output_edge_type_id": r["output_edge_type_id"],
        "input_hash": r.get("input_hash"),
        "output_hash": r.get("output_hash"),
        "proofs": r["proofs"],
    }


def write_pack(*, date: str) -> dict[str, Any]:
    rows = proven_rows()
    persist = [_persist_row(r) for r in rows]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in persist), encoding="utf-8"
    )
    manifest = build_manifest(persist, date=date)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    rows = prove_all()
    proven = proven_rows()
    ids = [r["primitive_id"] for r in rows]
    persisted = [_persist_row(r) for r in proven]

    # a deliberately-wrong-expected leaf must stay candidate (the gate is real, not a rubber stamp)
    wrongs = [run_primitive_proof(s["id"], s["mutator"], s["fixture"], s["expected"],
                                  mutator_args=s.get("args") or {}) for s in NEGATIVE_SPECS]
    # an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:dtd_EXEC_ERROR", "dtd_iso_parse_to_parts", "not-a-date", "irrelevant")
    proven_ids = {r["primitive_id"] for r in proven}

    checks: list[tuple[str, bool]] = [
        (">=28 datetime leaf primitives declared", len(LEAF_SPECS) >= 28),
        ("unique primitive ids", len(set(ids)) == len(ids)),
        (">=28 leaves PROVE serves_truth=true via an executed proof", len(proven) >= 28),
        ("every proven row is promoted + L7_executed_proof with all sub-proofs passing",
         all(r["serves_truth"] is True and r["promoted"] is True and r["verification_level"] == "L7_executed_proof"
             and all(p["passed"] for p in r["proofs"]) for r in proven)),
        ("EVERY persisted row carries non-null input+output edge type ids (typed)",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in persisted)),
        ("typed_count == proven_count (every workable leaf is typed)",
         build_manifest(persisted, date="X")["typed_count"] == build_manifest(persisted, date="X")["proven_count"]),
        ("edge type ids are canonical (canonicalize_edge is idempotent on them)",
         all(canonicalize_edge(r["input_edge_type_id"]) == r["input_edge_type_id"]
             and canonicalize_edge(r["output_edge_type_id"]) == r["output_edge_type_id"] for r in persisted)),
        ("roundtrip-inverse pairs actually proved reversible", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in next(x for x in proven if x["primitive_id"] == s["id"])["proofs"])
            for s in LEAF_SPECS if s.get("inverse"))),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in proven_rows()] == [json.dumps(r, sort_keys=True) for r in proven]),
        ("every deliberately-wrong leaf stays CANDIDATE (never promoted)",
         all(w["serves_truth"] is False and w["promoted"] is False for w in wrongs)),
        ("the wrong leaves are NOT in the proven set", all(s["id"] not in proven_ids for s in NEGATIVE_SPECS)),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
        ("no wall-clock/RNG symbols used in bodies", _no_forbidden_symbols()),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - prove_leaves_datetime_deterministic:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - prove_leaves_datetime_deterministic: {len(proven)} REAL pure-deterministic datetime leaf primitives "
          f"PROVEN end-to-end via the imported executed-proof runner (serves_truth=true, L7_executed_proof), every one "
          f"TYPED with canonical edge type ids; {sum(1 for s in LEAF_SPECS if s.get('inverse'))} inverse pairs proved "
          "reversible; deliberately-wrong leaves + an un-runnable fixture correctly stay candidate. Pure from INPUT, "
          "never the clock.")
    return 0


def _no_forbidden_symbols() -> bool:
    """Guard: the mutator BODIES must not use wall-clock/RNG/network (deterministic + offline law).

    Scans only the source of each registered datetime mutator (never docstrings/comments), so it is precise."""
    import inspect
    forbidden = (".now(", "time.time(", "utcnow(", "random", "requests", "urllib", "socket", "open(", "input(")
    for fn in _NEW_MUTATORS.values():
        body = inspect.getsource(fn)
        if any(tok in body for tok in forbidden):
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default="2026-07-03")  # fixed literal default — no wall-clock read
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack(date=args.date)
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
