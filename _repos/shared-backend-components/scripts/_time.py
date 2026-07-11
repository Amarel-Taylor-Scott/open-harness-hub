#!/usr/bin/env python3
"""scripts._time — the ONE UTC timestamp helper. ``now_iso()`` is the single definition of "the current
instant as an ISO-8601 string", so a record's timestamp never silently drifts between LOCAL and UTC
depending on which of the ~36 ad-hoc ``_now()`` / ``iso_now()`` copies a call site happened to inherit.

The bug this prevents (found in the wild): some copies used ``datetime.now()`` / ``strftime`` with **no
timezone** — LOCAL time, no ``Z`` — while others used ``datetime.now(timezone.utc)`` — UTC with ``Z``.
Mixed local/UTC timestamps in one system are unorderable and quietly wrong (a "12:00:00" row written in
one zone sorts against a "12:00:00Z" row written in another). ``now_iso()`` is ALWAYS UTC, always
``Z``-suffixed, so every stamp is comparable.

  now_iso()             -> "2026-07-04T12:34:56Z"           (UTC, second precision, Z)
  now_iso(micros=True)  -> "2026-07-04T12:34:56.789012Z"    (UTC, microsecond precision, Z)
  utc_now()             -> a timezone-AWARE datetime in UTC  (when you need the object, not the string)
  is_iso_z(s)           -> bool                              (redaction-safe shape check)

Stdlib-only, no side effects. serves_truth=false — a timestamp is metadata, never truth.

    PYTHONPATH=. python3 scripts/_time.py --self-test
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone

#: The exact shape now_iso() emits: date T time, optional .microseconds, trailing Z (UTC). Single source
#: of "a valid AIDoneRight timestamp" so a local-time (no-Z) stamp is detectable, not silently accepted.
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")


def utc_now() -> datetime:
    """The current instant as a timezone-AWARE datetime in UTC. Use when you need the datetime object;
    for a string, use now_iso() (never call .strftime()/.isoformat() ad hoc — that is how the drift began)."""
    return datetime.now(timezone.utc)


def now_iso(*, micros: bool = False) -> str:
    """The current instant as an ISO-8601 string in UTC, ALWAYS 'Z'-suffixed (never local time, never a
    naive/ambiguous stamp). Second precision by default; microsecond precision when ``micros=True``."""
    dt = utc_now()
    fmt = "%Y-%m-%dT%H:%M:%S.%f" if micros else "%Y-%m-%dT%H:%M:%S"
    return dt.strftime(fmt) + "Z"


def is_iso_z(value: object) -> bool:
    """Whether ``value`` is an ISO-8601 UTC 'Z' timestamp in the shape now_iso() emits — a redaction-safe
    check (returns a bool). A LOCAL-time stamp (no trailing Z) or an offset stamp (+00:00) returns False."""
    return isinstance(value, str) and bool(_ISO_Z_RE.match(value))


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # A. now_iso() is UTC + Z, second precision by default.
    s = now_iso()
    checks.append(("now_iso() ends with Z", s.endswith("Z")))
    checks.append(("now_iso() matches the ISO-Z shape", is_iso_z(s)))
    checks.append(("now_iso() default has no microseconds", "." not in s))
    checks.append(("now_iso() round-trips via strptime", _parses(s, "%Y-%m-%dT%H:%M:%SZ")))

    # B. micros variant has fractional seconds + still Z + still valid.
    sm = now_iso(micros=True)
    checks.append(("now_iso(micros) has fractional seconds", "." in sm and sm.endswith("Z")))
    checks.append(("now_iso(micros) matches the ISO-Z shape", is_iso_z(sm)))
    checks.append(("now_iso(micros) round-trips via strptime", _parses(sm, "%Y-%m-%dT%H:%M:%S.%fZ")))

    # C. utc_now() is timezone-AWARE and exactly UTC (zero offset) — the property the local-time copies lacked.
    dt = utc_now()
    checks.append(("utc_now() is timezone-aware", dt.tzinfo is not None))
    checks.append(("utc_now() offset is exactly UTC", dt.utcoffset() == timezone.utc.utcoffset(None)))

    # D. is_iso_z REJECTS the exact bug shape (local time, no Z) and an offset stamp and junk.
    checks.append(("is_iso_z rejects a local-time stamp (no Z)", not is_iso_z("2026-07-04T12:34:56")))
    checks.append(("is_iso_z rejects a +00:00 offset stamp", not is_iso_z("2026-07-04T12:34:56+00:00")))
    checks.append(("is_iso_z rejects junk / non-str", not is_iso_z("nope") and not is_iso_z(12345)))

    failed = [n for n, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - _time: now_iso() is the ONE UTC, Z-suffixed timestamp (no local-time drift); "
          "is_iso_z rejects the local/offset shapes; utc_now() is tz-aware UTC.")
    return 0


def _parses(value: str, fmt: str) -> bool:
    try:
        datetime.strptime(value, fmt)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else _self_test())
