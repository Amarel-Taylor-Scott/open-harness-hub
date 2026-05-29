#!/usr/bin/env python3
"""scripts.ingest.sanctions_feed — the LIVE-feed CONNECTOR for the M2 sanctions beachhead.

This is the missing half of the sanctions wedge. ``scripts.sanctions.sanctions_freshness``
is the pure, deterministic SCORER (``docs/codex/north-star.md`` — *"we verify your docs
are RIGHT against the source of truth, not just current"*): handed two parsed list
versions and an internal claim, it answers ``current`` / ``stale`` / ``contradicted``
with provenance and a ``would_be_violation`` flag. But it scores records it is HANDED —
it deliberately touches no network. The scorer's own docstring names exactly this gap:

    SEAM (live, not faked): the real OFAC SDN / BIS / EU consolidated feeds wire in
    through the connector/ingest layer — that fetch is a SEPARATE component
    (side_effects: external_call, trust_boundary: external) ... Once it hands real
    records to parse_list the very same diff/flag logic runs unchanged.

THIS module is that connector. It produces OFAC-SDN-like records **in the exact shape
``scripts.sanctions.sanctions_freshness.parse_list`` expects** and feeds them in, so the
seam is the only thing left abstract — the wiring on both sides is real and proven.

What is REAL here vs. the SEAM
------------------------------
* **REAL (proven offline):**
  - ``fetch_sanctions_records(...)`` returns records ``parse_list`` accepts (the
    self-test imports ``parse_list`` and parses them — the contract is checked, not
    asserted by hand).
  - ``normalize(raw_row, source=...)`` maps a *raw feed-shaped row* (the column names
    the real OFAC SDN consolidated CSV / BIS / EU file use) onto the parse_list record
    shape. This proves the field MAPPING is genuine even though the fetch is a seam:
    when a real fetch lands, ``normalize`` is the function that converts each row.
  - ``LIVE_SANCTIONS_SOURCES`` records the real feed URLs + formats as governed
    **runtime config**, with the connector runtime signals.
* **SYNTHETIC fixture:** the offline records are derived from
  ``scripts.sanctions.sanctions_freshness.SYNTHETIC_SDN_V2`` (imported, NOT re-typed —
  single source of truth) — clearly synthetic ``SYN-…`` ids / placeholder names, NOT
  real persons or entities.
* **SEAM (live, NOT invoked):** the real OFAC / BIS / EU HTTP fetch + format parsing.
  ``offline_fixture`` is forced ``True`` in this module (NETWORK IS BLOCKED): the live
  path is *described* (URL, format, runtime signals) and **raises** if anyone flips the
  flag here, so the seam can never be silently exercised or faked.

Runtime contract (declared as ``RUNTIME``; asserted in the self-test). This component
is the EXTERNAL-boundary sibling of the pure scorer, and its signals are the ones the
scorer already published for us in ``LIVE_CONNECTOR_RUNTIME`` (imported, not re-typed):

  * ``process_kind   = ingest.sanctions_feed``  — an ingest/connector step.
  * ``deterministic  = false`` LIVE — a real fetch depends on what the feed serves at
    fetch time. **OFFLINE it is deterministic** (``offline_fixture=True`` returns the
    fixed bundled fixture every call), which is what lets the self-test prove it.
  * ``idempotent     = false`` LIVE — re-fetching can return a newer list version
    (that is the whole point of a freshness feed); OFFLINE re-runs are identical.
  * ``side_effects   = external_call`` — the live path crosses the network. (None is
    made offline; the signal describes the component's real nature, honestly.)
  * ``streaming      = false`` — whole list pulled, then normalized row by row.
  * ``trust_boundary = external`` — the bytes come from a third party; the scorer that
    consumes them is ``local``. The boundary is HERE, by design.
  * ``on_error       = raise`` — a malformed raw row (missing a required field, or a
    flipped-flag live attempt offline) raises rather than emitting a junk record.

Pure-Python **stdlib only** (``argparse``, ``json``, ``sys``, ``typing``). The only
imports are sibling project modules (the scorer's shape constants + the synthetic
fixture). No third-party deps, no network client constructed.

Public API:
    from scripts.ingest.sanctions_feed import (
        fetch_sanctions_records, normalize,
        LIVE_SANCTIONS_SOURCES, RUNTIME, DEFAULT_SOURCE,
    )
    records = fetch_sanctions_records("ofac_sdn")          # offline fixture, default
    current = parse_list(records)                          # scorer accepts them as-is

CLI / self-test:
    python3 scripts/ingest/sanctions_feed.py
    python3 -m scripts.ingest.sanctions_feed
    python3 scripts/ingest/sanctions_feed.py --demo   # JSON: fetched records + a mapped row
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Mapping

# Make the repo root importable when run *directly* (the repo has no top-level
# scripts/__init__.py; it is a namespace package run via -m from the root). This
# connector must COMPOSE scripts.sanctions.sanctions_freshness (the scorer it feeds —
# imported below for its record shape + synthetic fixture), so a bare
# ``python3 scripts/ingest/sanctions_feed.py`` would otherwise fail with
# ``ModuleNotFoundError: No module named 'scripts'`` because only this file's directory
# is on sys.path. This file is ``<root>/scripts/ingest/sanctions_feed.py`` → the repo
# root is three parents up. Stdlib only; no-op under ``-m`` (``__package__`` is set, so
# the root is already importable). Must run BEFORE the package-qualified import below.
if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

# Import the scorer's shape so the connector and scorer can never drift (No-Magic-Values):
# the record fields, the synthetic fixture we stand in with, and the connector runtime
# signals the scorer already published for THIS component. We do NOT reimplement any of it.
from scripts.sanctions.sanctions_freshness import (
    LIVE_CONNECTOR_RUNTIME,
    LIVE_FEED_SEAMS,
    SYN_LIST_DATE_V2,
    SYN_LIST_VERSION_V2,
    SYNTHETIC_SDN_V2,
    parse_list,  # imported so the self-test checks the real contract, not a hand copy
)

# ── Vocabulary (single source of truth; No-Magic-Values) ─────────────────────

#: process_kind for this connector — sourced from the scorer's published signal so a
#: rename there propagates here (it is the contract between the two components).
PROCESS_KIND = LIVE_CONNECTOR_RUNTIME["process_kind"]  # "ingest.sanctions_feed"

#: The required fields a record MUST carry for ``parse_list`` to accept it. Derived from
#: the scorer's contract (``parse_list`` calls ``_ensure_str`` on exactly these). Kept
#: here as the connector's output spec; the self-test proves every emitted record has them.
REQUIRED_RECORD_FIELDS: tuple[str, ...] = ("entity_id", "name", "program", "list_version")
#: ``list_date`` is optional on the scorer side, but the connector always emits it
#: (provenance is cheap and the freshness ordering uses it). Named so it isn't a literal.
OPTIONAL_RECORD_FIELDS: tuple[str, ...] = ("list_date",)


def _source(key: str, url: str, fmt: str, raw_columns: Mapping[str, str], note: str) -> dict[str, Any]:
    """Build one governed live-source descriptor (kept uniform; not a magic dict)."""
    return {
        "key": key,
        "url": url,                  # the REAL feed URL — governed runtime config, NOT fetched here
        "format": fmt,
        "raw_columns": dict(raw_columns),  # raw_feed_field -> parse_list record field (the mapping)
        "note": note,
    }


#: The REAL live sanctions feeds this connector targets. These URLs/formats are the
#: governed RUNTIME CONFIG for the live path — recorded here, **not fetched** in this
#: module. ``raw_columns`` is the column→record mapping ``normalize`` applies; it is the
#: concrete, real artifact even while the fetch is a seam. (Prose for each feed lives in
#: the scorer's ``LIVE_FEED_SEAMS``, imported below so we don't duplicate the descriptions.)
LIVE_SANCTIONS_SOURCES: dict[str, dict[str, Any]] = {
    "ofac_sdn": _source(
        key="ofac_sdn",
        # US Treasury OFAC — Specially Designated Nationals consolidated CSV.
        url="https://www.treasury.gov/ofac/downloads/sdn.csv",
        fmt="csv",  # SDN.CSV columns are positional; the consolidated CSV has a header row
        raw_columns={
            "ent_num": "entity_id",     # OFAC's stable record number -> our entity_id
            "SDN_Name": "name",         # the designated party's name
            "Program": "program",       # the sanctions program (e.g. an EO/authority code)
            "_list_version": "list_version",  # publication label (derived per-fetch)
            "_publish_date": "list_date",      # publication date (ISO) for the pulled file
        },
        note="OFAC SDN (SDN.XML / consolidated CSV) — the canonical feed the fixture mimics.",
    ),
    "bis_entity_list": _source(
        key="bis_entity_list",
        # US Commerce / BIS — Entity List (denied parties); supplement to part 744.
        url="https://www.bis.doc.gov/index.php/documents/consolidated-entity-list/1072-el/file",
        fmt="csv",
        raw_columns={
            "EntityNumber": "entity_id",
            "EntityName": "name",
            "FRCitation": "program",    # the Federal Register citation acts as the program
            "_list_version": "list_version",
            "_publish_date": "list_date",
        },
        note="BIS Entity List — different schema, same scorer once normalized.",
    ),
    "eu_consolidated": _source(
        key="eu_consolidated",
        # EU EEAS — consolidated financial-sanctions list.
        url="https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content",
        fmt="csv",
        raw_columns={
            "Entity_LogicalId": "entity_id",
            "NameAlias_WholeName": "name",
            "Regulation_Programme": "program",
            "_list_version": "list_version",
            "_publish_date": "list_date",
        },
        note="EU consolidated list — multi-list reconciliation is the connector's job.",
    ),
}

#: Default feed key (the canonical one the scorer's fixture mimics).
DEFAULT_SOURCE = "ofac_sdn"

#: Declared runtime-routing manifest for THIS connector. The boundary/side-effect/
#: process_kind fields are sourced from the scorer's published ``LIVE_CONNECTOR_RUNTIME``
#: (so the two components agree by construction); the remaining fields describe the
#: connector's LIVE nature honestly (non-deterministic, non-idempotent — a real feed
#: changes), with the offline note that the fixture path IS deterministic. The
#: external trust boundary routes this to an egress-capable pool, NOT the scorer's cpu pool.
RUNTIME: dict[str, Any] = {
    "process_kind": PROCESS_KIND,
    # LIVE values (the component's real nature). Offline, the fixture path is fixed —
    # see ``deterministic_offline`` — which is what the self-test relies on.
    "deterministic": False,
    "idempotent": False,
    "deterministic_offline": True,   # offline_fixture=True returns the same bytes every call
    "side_effects": LIVE_CONNECTOR_RUNTIME["side_effects"],   # "external_call"
    "streaming": False,
    "latency_budget_ms": None,
    "trust_boundary": LIVE_CONNECTOR_RUNTIME["trust_boundary"],  # "external"
    "on_error": "raise",
    "resource_pool": "egress",  # external fetch ⇒ needs network egress, not the cpu pool
}


# ── normalize — raw feed row -> parse_list record shape (REAL mapping) ────────


def normalize(raw_row: Mapping[str, Any], *, source: str = DEFAULT_SOURCE) -> dict[str, str]:
    """Map ONE raw feed-shaped row onto the record shape ``parse_list`` accepts.

    This is the real, load-bearing half of the connector: when a live fetch lands, each
    raw row (whose columns are named the way the real OFAC/BIS/EU file names them) is
    passed through here to become a scorer record. Proving this mapping offline is what
    makes the seam *only* the fetch — the transform is genuine.

    Args:
      raw_row: a mapping using the SOURCE's raw column names (the keys of
        ``LIVE_SANCTIONS_SOURCES[source]["raw_columns"]``), e.g. for ``ofac_sdn``:
        ``{"ent_num": "...", "SDN_Name": "...", "Program": "...",
           "_list_version": "...", "_publish_date": "..."}``. Extra raw columns are
        ignored (the real feed carries aliases/addresses we don't map yet).
      source: which feed's column mapping to apply (default ``ofac_sdn``).

    Returns a record dict with ``entity_id``, ``name``, ``program``, ``list_version``
    and (when present) ``list_date`` — exactly what ``parse_list`` reads. All values are
    coerced to ``str`` so the scorer's ``_ensure_str`` accepts them.

    Raises:
      KeyError:   unknown ``source``.
      ValueError: a required raw column is missing or maps to an empty value (we never
                  emit a junk record — ``on_error=raise``).
      TypeError:  ``raw_row`` is not a mapping.

    Deterministic and pure: same row in → same record out; no clock, RNG, or I/O.
    """
    if source not in LIVE_SANCTIONS_SOURCES:
        raise KeyError(f"unknown sanctions source {source!r}; known: {sorted(LIVE_SANCTIONS_SOURCES)}")
    if not isinstance(raw_row, Mapping):
        raise TypeError(f"raw_row must be a mapping, got {type(raw_row).__name__}")

    columns: Mapping[str, str] = LIVE_SANCTIONS_SOURCES[source]["raw_columns"]
    record: dict[str, str] = {}
    for raw_field, record_field in columns.items():
        if raw_field not in raw_row or raw_row[raw_field] is None:
            # list_date is the only field the scorer treats as optional; everything else
            # is required and a missing value is a malformed row, not a silent skip.
            if record_field in OPTIONAL_RECORD_FIELDS:
                continue
            raise ValueError(
                f"raw row missing required column {raw_field!r} (→ {record_field!r}) for source {source!r}"
            )
        value = str(raw_row[raw_field]).strip()
        if not value:
            if record_field in OPTIONAL_RECORD_FIELDS:
                continue
            raise ValueError(
                f"raw row has empty value for required column {raw_field!r} (→ {record_field!r})"
            )
        record[record_field] = value

    # Defensive: every required record field must be present after mapping (a raw_columns
    # spec that forgot one would otherwise emit a record the scorer rejects downstream).
    missing = [f for f in REQUIRED_RECORD_FIELDS if f not in record]
    if missing:
        raise ValueError(f"normalized record missing required field(s) {missing} for source {source!r}")
    return record


# ── _bundled_fixture — synthetic raw rows derived from the scorer's fixture ───


def _bundled_fixture_raw(source: str) -> list[dict[str, str]]:
    """Build synthetic RAW-shaped rows (source's column names) from the scorer's fixture.

    We reuse ``SYNTHETIC_SDN_V2`` (imported — single source of truth, NOT re-typed) and
    project it back into the *raw* column names the live feed would use, so the offline
    path exercises ``normalize`` end-to-end (raw → record) exactly as the live path will.
    This keeps the fixture clearly synthetic (``SYN-…`` ids) AND proves the mapping.
    """
    columns: Mapping[str, str] = LIVE_SANCTIONS_SOURCES[source]["raw_columns"]
    # invert record_field -> raw_field so we can lay the scorer record back into raw shape.
    record_to_raw = {rec: raw for raw, rec in columns.items()}
    raw_rows: list[dict[str, str]] = []
    for rec in SYNTHETIC_SDN_V2:
        # The scorer's fixture rows carry list_version == SYN_LIST_VERSION_V2 already;
        # use them as-is (assert below) so the offline list version is honest provenance.
        raw_rows.append({
            record_to_raw["entity_id"]: rec["entity_id"],
            record_to_raw["name"]: rec["name"],
            record_to_raw["program"]: rec["program"],
            record_to_raw["list_version"]: rec.get("list_version", SYN_LIST_VERSION_V2),
            record_to_raw["list_date"]: rec.get("list_date", SYN_LIST_DATE_V2),
        })
    return raw_rows


# ── fetch_sanctions_records — the connector entrypoint ───────────────────────


def fetch_sanctions_records(
    source: str = DEFAULT_SOURCE,
    *,
    offline_fixture: bool = True,
) -> list[dict[str, str]]:
    """Return sanctions records in the shape ``parse_list`` expects.

    The single entrypoint of the connector. Offline (the default, and the ONLY supported
    mode in this module — NETWORK IS BLOCKED) it returns the bundled synthetic fixture,
    routed through :func:`normalize` so the raw→record mapping is exercised, not bypassed.

    Args:
      source: which feed to pull (a key of ``LIVE_SANCTIONS_SOURCES``; default
        ``"ofac_sdn"``).
      offline_fixture: must be ``True`` here. The live fetch is a declared SEAM
        (``side_effects=external_call``, ``trust_boundary=external``); flipping this to
        ``False`` in this module raises ``NotImplementedError`` rather than touching the
        network or faking a result. (A deployment that wires the real fetcher would
        implement that branch in a network-permitted environment — the URL/format is in
        ``LIVE_SANCTIONS_SOURCES[source]``.)

    Returns:
      A list of record dicts, each accepted by ``parse_list`` (proven in the self-test).
      Offline this is deterministic: the same fixture, in the same order, every call.

    Raises:
      KeyError:           unknown ``source``.
      NotImplementedError: ``offline_fixture=False`` (the live fetch seam — not invoked here).
    """
    if source not in LIVE_SANCTIONS_SOURCES:
        raise KeyError(f"unknown sanctions source {source!r}; known: {sorted(LIVE_SANCTIONS_SOURCES)}")

    if not offline_fixture:
        # ── THE SEAM (live, not faked). ──
        # We do NOT construct an HTTP client, and we do NOT fabricate records. The real
        # path would: GET LIVE_SANCTIONS_SOURCES[source]["url"], parse its `format`, and
        # map each row via normalize(row, source=source). That crosses the external trust
        # boundary and is a SEPARATE concern from this proven-offline logic.
        src = LIVE_SANCTIONS_SOURCES[source]
        raise NotImplementedError(
            "live sanctions fetch is a SEAM (not invoked here; NETWORK IS BLOCKED). "
            f"source={source!r} url={src['url']!r} format={src['format']!r} "
            f"side_effects={RUNTIME['side_effects']} trust_boundary={RUNTIME['trust_boundary']}. "
            "Pass offline_fixture=True (default) to use the bundled synthetic fixture."
        )

    # ── OFFLINE (proven): synthetic raw rows → normalize() → records parse_list accepts. ──
    raw_rows = _bundled_fixture_raw(source)
    return [normalize(row, source=source) for row in raw_rows]


# ── Self-test (proves the connector against the REAL scorer contract) ─────────


def _selftest() -> None:
    # ── (1) offline fetch returns >=3 well-formed records the SCORER accepts. ──
    # We don't hand-check the shape — we feed it to the imported parse_list and let the
    # real contract validate it (the whole point of importing M2, not copying it).
    records = fetch_sanctions_records(DEFAULT_SOURCE)  # offline_fixture=True by default
    assert isinstance(records, list) and len(records) >= 3, (
        f"offline fetch must return >=3 records, got {len(records)}"
    )
    for rec in records:
        for field in REQUIRED_RECORD_FIELDS:
            assert field in rec and isinstance(rec[field], str) and rec[field], (
                f"record missing/empty required field {field!r}: {rec!r}"
            )
    parsed = parse_list(records)  # the REAL scorer contract — raises if any record is bad
    assert parsed["count"] == len(records), "parse_list did not index every fetched record"
    # The fixture is the synthetic V2 list (clearly synthetic ids), with honest provenance.
    assert parsed["list_version"] == SYN_LIST_VERSION_V2, "offline fixture should carry the synthetic V2 version"
    assert all(r["entity_id"].startswith("SYN-") for r in records), "fixture must be clearly synthetic (SYN- ids)"

    # offline path is deterministic (same bytes, same order, every call).
    assert fetch_sanctions_records(DEFAULT_SOURCE) == records, "offline fetch must be deterministic"

    # every declared source's fixture parses too (all column-mappings are valid).
    for key in LIVE_SANCTIONS_SOURCES:
        recs = fetch_sanctions_records(key)
        assert len(recs) >= 3, f"{key}: expected >=3 fixture records"
        parse_list(recs)  # raises on any bad mapping

    # ── (2) normalize maps a RAW-shaped row onto the record shape correctly. ──
    # Use the real OFAC raw column names; prove each maps to the right record field.
    raw = {
        "ent_num": "SYN-9001",
        "SDN_Name": "  Cobalt Freight Partners  ",   # leading/trailing ws must be stripped
        "Program": "SYN-EXPORT-CONTROL",
        "_list_version": SYN_LIST_VERSION_V2,
        "_publish_date": SYN_LIST_DATE_V2,
        "AltName": "ignored extra column",            # extra raw columns are dropped
    }
    rec = normalize(raw, source="ofac_sdn")
    assert rec == {
        "entity_id": "SYN-9001",
        "name": "Cobalt Freight Partners",           # stripped
        "program": "SYN-EXPORT-CONTROL",
        "list_version": SYN_LIST_VERSION_V2,
        "list_date": SYN_LIST_DATE_V2,
    }, f"normalize produced the wrong record: {rec!r}"
    assert "AltName" not in rec, "extra raw columns must not leak into the record"
    # the normalized row is itself accepted by the scorer (one-row list).
    parse_list([rec])
    # normalize is deterministic.
    assert normalize(raw, source="ofac_sdn") == rec, "normalize must be deterministic"

    # a BIS raw row maps through the BIS column names (proves per-source mapping).
    bis_raw = {"EntityNumber": "SYN-9002", "EntityName": "Harbor Optics GmbH",
               "FRCitation": "84 FR 12345", "_list_version": "BIS-EL-SYN-2026.05.28",
               "_publish_date": "2026-05-28"}
    bis_rec = normalize(bis_raw, source="bis_entity_list")
    assert bis_rec["entity_id"] == "SYN-9002" and bis_rec["program"] == "84 FR 12345", bis_rec
    parse_list([bis_rec])

    # ── normalize / fetch are on_error=raise on bad input. ──
    # missing a required raw column -> ValueError (no junk record emitted).
    raised = False
    try:
        normalize({"ent_num": "SYN-1", "SDN_Name": "X"}, source="ofac_sdn")  # no Program/version
    except ValueError:
        raised = True
    assert raised, "normalize must raise on a missing required column"
    # empty required value -> ValueError.
    raised = False
    try:
        normalize({"ent_num": "SYN-1", "SDN_Name": "   ", "Program": "P",
                   "_list_version": "v", "_publish_date": "d"}, source="ofac_sdn")
    except ValueError:
        raised = True
    assert raised, "normalize must raise on an empty required value"
    # unknown source -> KeyError on both surfaces.
    for fn in (lambda: normalize({}, source="nope"), lambda: fetch_sanctions_records("nope")):
        raised = False
        try:
            fn()
        except KeyError:
            raised = True
        assert raised, "unknown source must raise KeyError"
    # non-mapping raw_row -> TypeError.
    raised = False
    try:
        normalize(["not", "a", "mapping"], source="ofac_sdn")  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, "normalize must raise TypeError on a non-mapping row"

    # ── (3) the LIVE feed is a SEAM: clearly flagged, NOT invoked. ──
    # Flipping offline_fixture=False here must RAISE (never fetch, never fake) — and the
    # raised message must carry the real URL + the external boundary signals so the seam
    # is honest and visible, not buried.
    seam_raised = False
    try:
        fetch_sanctions_records(DEFAULT_SOURCE, offline_fixture=False)
    except NotImplementedError as exc:
        seam_raised = True
        msg = str(exc)
        assert LIVE_SANCTIONS_SOURCES[DEFAULT_SOURCE]["url"] in msg, "seam error must name the real feed URL"
        assert "external" in msg and "external_call" in msg, "seam error must surface the external boundary signals"
    assert seam_raised, "live fetch must be a SEAM that raises, not a silent/faked fetch"

    # the seam is also declared as governed runtime config (real URLs, formats, mappings).
    for key, src in LIVE_SANCTIONS_SOURCES.items():
        assert src["url"].startswith("https://"), f"{key}: live URL must be a real https endpoint"
        assert src["format"] in {"csv", "xml", "json"}, f"{key}: declared a parseable format"
        # every raw_columns mapping covers all required record fields (so normalize can't miss one).
        mapped = set(src["raw_columns"].values())
        assert set(REQUIRED_RECORD_FIELDS) <= mapped, f"{key}: raw_columns must map every required field"
    # the scorer's prose seam descriptions are carried (we import, not duplicate, them).
    assert len(LIVE_FEED_SEAMS) >= 3, "the scorer's live-feed seam descriptions should be available"

    # ── (4) RUNTIME manifest is honest + matches the scorer's published connector signals. ──
    rt = RUNTIME
    assert rt["process_kind"] == PROCESS_KIND == "ingest.sanctions_feed"
    # the external-boundary / side-effect signals are the ones the SCORER published for us.
    assert rt["trust_boundary"] == LIVE_CONNECTOR_RUNTIME["trust_boundary"] == "external"
    assert rt["side_effects"] == LIVE_CONNECTOR_RUNTIME["side_effects"] == "external_call"
    # LIVE nature is honest (a real feed is non-deterministic / non-idempotent)...
    assert rt["deterministic"] is False and rt["idempotent"] is False
    # ...but the OFFLINE path we just proved IS deterministic (declared + demonstrated above).
    assert rt["deterministic_offline"] is True
    assert rt["resource_pool"] == "egress", "an external fetch routes to an egress pool, not cpu"
    assert rt["on_error"] == "raise"

    print(
        "PASS — sanctions_feed connector: "
        f"offline fetch -> {len(records)} synthetic records ACCEPTED by parse_list "
        f"(scorer contract, list_version={parsed['list_version']}, all SYN- ids); "
        "all 3 sources' fixtures parse; normalize maps a raw OFAC row -> record correctly "
        "(strips ws, drops extras, BIS mapping too) and is deterministic; "
        "bad input raises (missing/empty column, unknown source, non-mapping); "
        "LIVE feed is a SEAM (offline_fixture=False RAISES with the real URL + "
        "trust_boundary=external/side_effects=external_call — NOT fetched, NOT faked); "
        "runtime=ingest.sanctions_feed/egress, deterministic_offline=True. "
        "(synthetic fixture derived from the scorer's SYNTHETIC_SDN_V2; real fetch is the seam — no network here)"
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Sanctions live-feed connector — offline fixture in parse_list shape; live fetch is a seam."
    )
    p.add_argument(
        "--demo", action="store_true",
        help="Print the offline fixture records + a normalized raw row + the live seam descriptor as JSON.",
    )
    p.add_argument(
        "--source", default=DEFAULT_SOURCE, choices=sorted(LIVE_SANCTIONS_SOURCES),
        help="Which feed's fixture/mapping to use (default: %(default)s).",
    )
    return p


def _demo(source: str) -> None:
    """Emit the offline records + a mapped raw row + the (uninvoked) live seam, as JSON."""
    records = fetch_sanctions_records(source)
    src = LIVE_SANCTIONS_SOURCES[source]
    # one illustrative raw->record mapping using the source's own column names.
    sample_raw = {raw: f"<{rec}>" for raw, rec in src["raw_columns"].items()}
    print(json.dumps({
        "source": source,
        "offline_records": records,
        "sample_raw_columns": src["raw_columns"],
        "live_seam": {
            "url": src["url"], "format": src["format"],
            "invoked": False,
            "side_effects": RUNTIME["side_effects"],
            "trust_boundary": RUNTIME["trust_boundary"],
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()
    if args.demo:
        _demo(args.source)
    else:
        _selftest()
