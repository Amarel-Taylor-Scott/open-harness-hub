#!/usr/bin/env python3
"""contextops/extractor_snippets — the DETERMINISTIC extractor primitives (Lane D).

Each primitive reads ONE value out of a source payload and returns a FactAssertion CANDIDATE
(``claim_status="candidate"``) tied to a REQUIRED ``source_handle``. THE INVARIANT, enforced here in code:
an extractor output is ALWAYS a candidate, NEVER served or canonical truth. A candidate that drops its source
handle is rejected (``MissingSourceHandleError``); a request to mint anything but ``claim_status="candidate"``
is rejected (``CanonicalClaimError``). The candidate's ``claim_type`` is pinned to ``atomic_fact`` from the
governed ``CLAIM_SHAPED`` registry so an extractor can never silently emit an allegation/conclusion as a fact.

Primitives (the nine in the ExtractorSnippet contract):
  regex · json_path · html_selector · csv_field · markdown_heading · duration_parser · date_parser ·
  numeric_parser · source_hash_checker.

These are the bodies a bounded codegen agent DRAFTS; they only ever PROPOSE candidates. The
:mod:`src.baltor.contextops.sandbox_gate` runs one in a temp dir behind a proof gate before any use; nothing
here serves, promotes, or registers anything. Deterministic + offline: candidate ids are content-addressed
(hashlib), time is INJECTED (``extracted_at``), no clock, no RNG, no network. stdlib only.
"""
from __future__ import annotations

import csv as _csv
import hashlib
import html.parser as _htmlparser
import io
import json
import re
from dataclasses import dataclass

from src.baltor.contracts.artifacts.fact_assertion import SCOPES

#: the ONLY claim_status an extractor may mint — pinned, matching ExtractorSnippet + the contract layer.
#: Single-sourced from the contracts layer so it can never drift from the ports' CANDIDATE_CLAIM_STATUS.
from src.baltor.contracts.governance import CANDIDATE_CLAIM_STATUS as CANDIDATE_STATUS  # noqa: E402
#: an extractor candidate is always a factual claim shape (never an allegation/conclusion) — from CLAIM_SHAPED.
CANDIDATE_CLAIM_TYPE = "atomic_fact"
#: what an extractor produces — pinned, matching ExtractorSnippet.produces.
PRODUCES = "fact_assertion_candidate"

#: the nine deterministic extraction primitives this lane ships (single source — matches the contract enum).
EXTRACTOR_TYPES = (
    "regex", "json_path", "html_selector", "csv_field", "markdown_heading",
    "duration_parser", "date_parser", "numeric_parser", "source_hash_checker",
)

#: business-day / calendar-day duration words (lowercased), single source for the duration_parser unit map.
_DURATION_UNITS = {
    "business day": "business_days", "business days": "business_days",
    "calendar day": "calendar_days", "calendar days": "calendar_days",
    "day": "days", "days": "days", "week": "weeks", "weeks": "weeks",
    "month": "months", "months": "months", "year": "years", "years": "years",
    "hour": "hours", "hours": "hours", "minute": "minutes", "minutes": "minutes",
}
#: ordered longest-first so "10 business days" matches "business days" before "days" (deterministic).
_DURATION_KEYS = tuple(sorted(_DURATION_UNITS, key=len, reverse=True))
#: a number followed by up to two unit words (so "business days" is captured, not just "business").
_DURATION_RE = re.compile(r"(?P<n>\d+(?:\.\d+)?)\s*(?P<unit>[A-Za-z]+(?:\s+[A-Za-z]+)?)")
#: ISO-8601 date (YYYY-MM-DD) — the one date shape the date_parser certifies as a value.
_ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
#: a signed decimal / integer for the numeric_parser.
_NUMERIC_RE = re.compile(r"-?\d+(?:\.\d+)?")


class ExtractorError(Exception):
    """Base for extractor faults — a fault is an explicit failure, NEVER a silently-faked value."""


class MissingSourceHandleError(ExtractorError):
    """Raised when an extractor is asked to emit a candidate without a source_handle (red-team gate)."""


class CanonicalClaimError(ExtractorError):
    """Raised when an extractor is asked to mint anything but a candidate (red-team: served/canonical)."""


class NoMatchError(ExtractorError):
    """Raised when a primitive finds no value — an explicit miss, never a fabricated default."""


@dataclass(frozen=True)
class FactAssertionCandidate:
    """An extractor's output: a CANDIDATE assertion tied to a source handle. NEVER served/canonical truth.

    Mirrors the served ``FactAssertion`` shape but is *pinned* to ``claim_status='candidate'`` and
    ``produces='fact_assertion_candidate'``; ``promotion_eligible`` is False — only reconciliation/verification
    may promote a candidate, and that happens elsewhere. ``candidate_id`` is content-addressed (deterministic).
    """

    fact_key: str
    extractor_type: str
    value: object               # the extracted value (str/number/bool depending on primitive)
    unit: str                   # "" unless the primitive produces one (duration_parser, numeric_parser)
    source_handle: str          # REQUIRED — an empty handle is rejected at construction
    scope: str                  # one of SCOPES
    extracted_at: int           # injected epoch seconds — never wall-clock
    claim_status: str = CANDIDATE_STATUS
    claim_type: str = CANDIDATE_CLAIM_TYPE
    produces: str = PRODUCES
    promotion_eligible: bool = False
    tenant_id: str = ""

    def __post_init__(self) -> None:
        if not self.source_handle:
            raise MissingSourceHandleError(
                f"extractor {self.extractor_type!r} produced a candidate without a source_handle — rejected")
        if self.claim_status != CANDIDATE_STATUS:
            raise CanonicalClaimError(
                f"extractor candidate claim_status must be {CANDIDATE_STATUS!r}, got {self.claim_status!r}")
        if self.produces != PRODUCES:
            raise CanonicalClaimError(
                f"extractor must produce {PRODUCES!r}, got {self.produces!r} — never served/canonical truth")
        if self.claim_type != CANDIDATE_CLAIM_TYPE:
            raise CanonicalClaimError(
                f"extractor candidate claim_type must be {CANDIDATE_CLAIM_TYPE!r}, got {self.claim_type!r}")
        if self.promotion_eligible:
            raise CanonicalClaimError("an extractor candidate is never promotion_eligible — reconciliation decides")
        if self.scope not in SCOPES:
            raise ExtractorError(f"scope {self.scope!r} not in {SCOPES}")

    @property
    def candidate_id(self) -> str:
        body = {"fk": self.fact_key, "xt": self.extractor_type, "v": str(self.value), "u": self.unit,
                "sh": self.source_handle, "sc": self.scope, "ten": self.tenant_id}
        return "fac-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {"schema_version": "FactAssertionCandidate", "candidate_id": self.candidate_id,
                "fact_key": self.fact_key, "extractor_type": self.extractor_type, "value": self.value,
                "unit": self.unit, "source_handle": self.source_handle, "scope": self.scope,
                "claim_status": self.claim_status, "claim_type": self.claim_type, "produces": self.produces,
                "promotion_eligible": self.promotion_eligible, "tenant_id": self.tenant_id,
                "extracted_at": self.extracted_at}


def _candidate(*, fact_key: str, extractor_type: str, value, unit: str, source_handle: str, scope: str,
               extracted_at: int, tenant_id: str) -> FactAssertionCandidate:
    """The ONE place a candidate is minted — every primitive funnels through it (single source of the pin)."""
    return FactAssertionCandidate(
        fact_key=fact_key, extractor_type=extractor_type, value=value, unit=unit,
        source_handle=source_handle, scope=scope, extracted_at=extracted_at, tenant_id=tenant_id)


# ───────────────────────────── the nine deterministic primitives ─────────────────────────────


def extract_regex(payload: str, *, pattern: str, fact_key: str, source_handle: str, group: int = 0,
                  scope: str = "global_public", extracted_at: int = 0, tenant_id: str = "") -> FactAssertionCandidate:
    """regex — first match of ``pattern`` (group ``group``) → candidate. No match → NoMatchError."""
    m = re.search(pattern, str(payload))
    if not m:
        raise NoMatchError(f"regex {pattern!r} found no match")
    return _candidate(fact_key=fact_key, extractor_type="regex", value=m.group(group), unit="",
                      source_handle=source_handle, scope=scope, extracted_at=extracted_at, tenant_id=tenant_id)


def extract_json_path(payload, *, path: str, fact_key: str, source_handle: str,
                      scope: str = "global_public", extracted_at: int = 0, tenant_id: str = "") -> FactAssertionCandidate:
    """json_path — walk a slash-pointer (e.g. ``/a/b/0``) into a JSON object. Missing key → NoMatchError."""
    obj = json.loads(payload) if isinstance(payload, (str, bytes)) else payload
    cur = obj
    for part in [p for p in path.split("/") if p != ""]:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.lstrip("-").isdigit() and -len(cur) <= int(part) < len(cur):
            cur = cur[int(part)]
        else:
            raise NoMatchError(f"json_path {path!r} missing segment {part!r}")
    return _candidate(fact_key=fact_key, extractor_type="json_path", value=cur, unit="",
                      source_handle=source_handle, scope=scope, extracted_at=extracted_at, tenant_id=tenant_id)


class _TagTextCollector(_htmlparser.HTMLParser):
    """Collects the text inside the FIRST occurrence of ``target`` tag (deterministic, stdlib-only)."""

    def __init__(self, target: str) -> None:
        super().__init__()
        self.target = target.lower()
        self._depth = 0
        self.found = False
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == self.target and not self.found:
            self._depth += 1
        elif self._depth:
            self._depth += 1

    def handle_endtag(self, tag):
        if self._depth:
            self._depth -= 1
            if self._depth == 0:
                self.found = True

    def handle_data(self, data):
        if self._depth and not self.found:
            self.parts.append(data)


def extract_html_selector(payload: str, *, tag: str, fact_key: str, source_handle: str,
                          scope: str = "global_public", extracted_at: int = 0, tenant_id: str = "") -> FactAssertionCandidate:
    """html_selector — text of the first ``tag`` element (stdlib HTMLParser; no external selector lib)."""
    p = _TagTextCollector(tag)
    p.feed(str(payload))
    if not p.found:
        raise NoMatchError(f"html tag {tag!r} not found")
    text = "".join(p.parts).strip()
    return _candidate(fact_key=fact_key, extractor_type="html_selector", value=text, unit="",
                      source_handle=source_handle, scope=scope, extracted_at=extracted_at, tenant_id=tenant_id)


def extract_csv_field(payload: str, *, column: str, fact_key: str, source_handle: str, row: int = 0,
                      scope: str = "global_public", extracted_at: int = 0, tenant_id: str = "") -> FactAssertionCandidate:
    """csv_field — value of ``column`` in row ``row`` of a CSV (stdlib csv). Missing column/row → NoMatchError."""
    text = payload.decode("utf-8") if isinstance(payload, bytes) else str(payload)
    rows = list(_csv.DictReader(io.StringIO(text)))
    if not (0 <= row < len(rows)) or column not in rows[row]:
        raise NoMatchError(f"csv field column={column!r} row={row} not present")
    return _candidate(fact_key=fact_key, extractor_type="csv_field", value=rows[row][column], unit="",
                      source_handle=source_handle, scope=scope, extracted_at=extracted_at, tenant_id=tenant_id)


def extract_markdown_heading(payload: str, *, heading: str, fact_key: str, source_handle: str,
                             scope: str = "global_public", extracted_at: int = 0, tenant_id: str = "") -> FactAssertionCandidate:
    """markdown_heading — the first non-blank body line under a ``# heading`` (deterministic line scan)."""
    target = heading.strip().lower()
    lines = str(payload).splitlines()
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("#") and s.lstrip("#").strip().lower() == target:
            for body in lines[i + 1:]:
                if body.strip() and not body.strip().startswith("#"):
                    return _candidate(fact_key=fact_key, extractor_type="markdown_heading",
                                      value=body.strip(), unit="", source_handle=source_handle, scope=scope,
                                      extracted_at=extracted_at, tenant_id=tenant_id)
    raise NoMatchError(f"markdown heading {heading!r} (with a body line) not found")


def extract_duration(payload: str, *, fact_key: str, source_handle: str, scope: str = "global_public",
                     extracted_at: int = 0, tenant_id: str = "") -> FactAssertionCandidate:
    """duration_parser — "10 business days" → value 10, unit 'business_days'. The CFPB-reference primitive.

    Scans for ``<number> <unit-words>`` and maps the longest matching unit phrase so "business days" wins
    over "days". The candidate carries BOTH the numeric value AND the normalized unit so a downstream
    unit_check can compare 10 business_days against another source deterministically.
    """
    text = str(payload).lower()
    for m in _DURATION_RE.finditer(text):
        tail = m.group("unit").strip()
        # longest-first whole-word match: "business days" beats "days"; "monthly" never matches "month".
        for key in _DURATION_KEYS:
            if tail == key or tail.startswith(key + " "):
                num = m.group("n")
                value = int(num) if num.isdigit() else float(num)
                return _candidate(fact_key=fact_key, extractor_type="duration_parser", value=value,
                                  unit=_DURATION_UNITS[key], source_handle=source_handle, scope=scope,
                                  extracted_at=extracted_at, tenant_id=tenant_id)
    raise NoMatchError("no '<number> <duration-unit>' found")


def extract_date(payload: str, *, fact_key: str, source_handle: str, scope: str = "global_public",
                 extracted_at: int = 0, tenant_id: str = "") -> FactAssertionCandidate:
    """date_parser — first ISO-8601 (YYYY-MM-DD) date, validated for real month/day ranges. → candidate."""
    for m in _ISO_DATE_RE.finditer(str(payload)):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return _candidate(fact_key=fact_key, extractor_type="date_parser",
                              value=f"{y:04d}-{mo:02d}-{d:02d}", unit="iso_date", source_handle=source_handle,
                              scope=scope, extracted_at=extracted_at, tenant_id=tenant_id)
    raise NoMatchError("no valid ISO-8601 date found")


def extract_numeric(payload: str, *, fact_key: str, source_handle: str, unit: str = "",
                    scope: str = "global_public", extracted_at: int = 0, tenant_id: str = "") -> FactAssertionCandidate:
    """numeric_parser — first signed integer/decimal → candidate (int when whole, else float)."""
    m = _NUMERIC_RE.search(str(payload))
    if not m:
        raise NoMatchError("no numeric value found")
    raw = m.group(0)
    value = int(raw) if raw.lstrip("-").isdigit() else float(raw)
    return _candidate(fact_key=fact_key, extractor_type="numeric_parser", value=value, unit=unit,
                      source_handle=source_handle, scope=scope, extracted_at=extracted_at, tenant_id=tenant_id)


def extract_source_hash(payload, *, expected_hash: str, fact_key: str, source_handle: str,
                        scope: str = "global_public", extracted_at: int = 0, tenant_id: str = "") -> FactAssertionCandidate:
    """source_hash_checker — sha256 of the payload; candidate value is True iff it matches ``expected_hash``.

    This is how a VerificationRecipe's ``source_hash_match`` validator pins a verification to an EXACT source
    snapshot: the candidate records whether the source content is the one the recipe was built against. The
    result is still a candidate (a boolean claim "the source still hashes to X"), never served truth.
    """
    raw = payload if isinstance(payload, (bytes, bytearray)) else str(payload).encode("utf-8")
    actual = hashlib.sha256(raw).hexdigest()
    return _candidate(fact_key=fact_key, extractor_type="source_hash_checker", value=(actual == expected_hash),
                      unit=f"sha256:{actual}", source_handle=source_handle, scope=scope,
                      extracted_at=extracted_at, tenant_id=tenant_id)


#: registry of the nine primitives (extractor_type → callable). The sandbox gate dispatches through this.
EXTRACTORS = {
    "regex": extract_regex,
    "json_path": extract_json_path,
    "html_selector": extract_html_selector,
    "csv_field": extract_csv_field,
    "markdown_heading": extract_markdown_heading,
    "duration_parser": extract_duration,
    "date_parser": extract_date,
    "numeric_parser": extract_numeric,
    "source_hash_checker": extract_source_hash,
}


def run_extractor(extractor_type: str, payload, **kwargs) -> FactAssertionCandidate:
    """Dispatch to one of the nine primitives by type. Unknown type → ExtractorError (never a fake result)."""
    fn = EXTRACTORS.get(extractor_type)
    if fn is None:
        raise ExtractorError(f"unknown extractor_type {extractor_type!r}; not one of {EXTRACTOR_TYPES}")
    return fn(payload, **kwargs)
