#!/usr/bin/env python3
"""Sanctions freshness — catch an internal control that LAGS or CONTRADICTS the live list.

This is the SANCTIONS BEACHHEAD: the north-star wedge
(``_repos/_shared/codex/north-star.md``, ``_repos/_shared/strategy/positioning-v2.md`` — *"we verify
your docs are RIGHT against the source of truth, not just current"*) turned into
runnable code on the single domain where being stale is asymmetric and legal.
Sanctions lists (OFAC SDN, BIS Entity List, EU consolidated) change on their own
clock; an internal screening doc that was correct last week can silently become a
would-be VIOLATION the moment a new list version drops. A faithfulness-only RAG
stack retrieves that internal doc *faithfully* and is exactly wrong. The value —
and the moat — is detecting the lag/contradiction against the fresh list, which is
a ``channel_inaccessibility`` / volatile-source **structural** lift in the
``scripts.eval.reason_codes`` taxonomy (the list moved; no model scale fixes that),
not a transient one.

This module is the deterministic engine for that. It is the freshness sibling of
the assurance processors: ``scripts.processors.assurance.multi_source_corroborate``
asks *"is this claim independently corroborated?"*; this asks the orthogonal
question *"is this internal claim still in step with the CURRENT authoritative
list?"* — and answers ``current`` / ``stale`` / ``contradicted`` with provenance,
the same shape of self-evident, auditable verdict.

What is REAL here vs. the SEAM
------------------------------
* **REAL (proven offline):** ``parse_list`` (normalize + index), ``freshness_diff``
  (added/removed/changed across two list versions, with the version delta), and
  ``flag_stale_context`` (verdict + provenance for an internal claim). All three
  are pure, deterministic functions of the records they are HANDED.
* **SYNTHETIC fixture:** ``SYNTHETIC_SDN_V1`` / ``_V2`` are a handful of
  OFAC-SDN-*like* records — **clearly synthetic, NOT real persons or entities**
  (placeholder names like "Northwind Trading LLC", placeholder ids ``SYN-…``).
  They stand in offline for the real feeds so the logic can be PROVEN without a
  network.
* **SEAM (live, not faked):** the real OFAC SDN / BIS / EU consolidated feeds wire
  in through the **connector/ingest layer** — that fetch is a SEPARATE component
  (``side_effects: external_call``, ``trust_boundary: external``), documented in
  ``LIVE_FEED_SEAMS``. Once it hands real records to ``parse_list`` the very same
  diff/flag logic runs unchanged. No network is touched in this module.

Runtime contract (declared as ``RUNTIME`` and asserted in the self-test; field→pool
mapping per ``_repos/shared-backend-components/context/architecture/component-execution-and-runtime-routing.md`` §4):

  * ``process_kind   = verify.sanctions_freshness`` — CPU step.
  * ``deterministic  = true``  — same records + same claim → identical verdict and
    diff. No clocks, RNG, env reads, network, or filesystem access. (Where a list
    omits a date we fall back to its version *string*, ordered deterministically —
    never to ``now()``.)
  * ``idempotent     = true``  — re-running on the same inputs yields the same
    result; ``parse_list`` is a fixed point (parsing an already-parsed index back
    through its records is stable).
  * ``side_effects   = none``  — pure functions; read nothing, write nothing.
  * ``streaming      = false`` — whole list(s) + whole claim in, verdict out.
  * ``trust_boundary = local`` — scores records already handed in; the *fetch* that
    crosses the boundary is the separate connector (see ``LIVE_FEED_SEAMS``).
  * ``on_error       = raise`` — malformed records/claims raise ``TypeError`` /
    ``ValueError``; we never silently pass a control we could not evaluate.

Pure-Python **stdlib only** (``re``, ``argparse``, ``json``, ``sys``). No deps,
no sibling-package imports needed for the core logic.

Public API:
    from scripts.sanctions.sanctions_freshness import (
        parse_list, freshness_diff, flag_stale_context,
        SYNTHETIC_SDN_V1, SYNTHETIC_SDN_V2,
    )
    cur = parse_list(SYNTHETIC_SDN_V2)
    verdict = flag_stale_context(
        {"entity_id": "SYN-0007", "status": "clear",
         "cites_list_version": "OFAC-SDN-SYN-2026.05.01"},
        cur,
    )
    # -> {"verdict": "contradicted"|"stale"|"current", "reason": "...",
    #     "would_be_violation": bool, "provenance": {...}, ...}

CLI / self-test:
    python3 _repos/shared-backend-components/scripts/sanctions/sanctions_freshness.py
    python3 -m scripts.sanctions.sanctions_freshness
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Iterable, Mapping

# ── Vocabulary (single source of truth; No-Magic-Values) ─────────────────────
#
# Defined ONCE and referenced by every function, the result dicts, and the
# self-test so a rename cannot drift across the API surface.

#: process_kind for this component (open vocab per SPEC §16 / routing doc §4).
PROCESS_KIND = "verify.sanctions_freshness"

#: The three freshness verdicts, worst-last. ``current`` = the internal claim is in
#: step with the live list; ``stale`` = the claim cites/relies on an OLDER list
#: version than the current one (it may be right or wrong, but it has not been
#: re-checked against the fresh list — hold it); ``contradicted`` = the current
#: list directly disagrees with the claim (e.g. claim says "clear", list now lists
#: the entity) — the would-be VIOLATION.
VERDICT_CURRENT = "current"
VERDICT_STALE = "stale"
VERDICT_CONTRADICTED = "contradicted"
VERDICTS: tuple[str, ...] = (VERDICT_CURRENT, VERDICT_STALE, VERDICT_CONTRADICTED)

#: An entity's presence on a sanctions list, normalized to two listing states. A
#: claim that an entity is ``clear`` while the list says ``listed`` is the
#: contradiction the beachhead exists to catch.
STATUS_LISTED = "listed"   # the entity IS on the current list (a match / SDN entry)
STATUS_CLEAR = "clear"     # the entity is NOT on the current list
LISTING_STATES: tuple[str, ...] = (STATUS_LISTED, STATUS_CLEAR)

#: The kinds of change ``freshness_diff`` reports between two list versions.
CHANGE_ADDED = "added"       # entity newly appears on the list
CHANGE_REMOVED = "removed"   # entity was de-listed
CHANGE_CHANGED = "changed"   # entity stayed listed but a field (e.g. program) changed
CHANGE_KINDS: tuple[str, ...] = (CHANGE_ADDED, CHANGE_REMOVED, CHANGE_CHANGED)

#: Honest record of the LIVE feeds this synthetic fixture stands in for, and the
#: layer that wires them in. Carried in results so the seam is visible to any
#: consumer, not buried in prose. NONE of these are touched in this module.
LIVE_FEED_SEAMS: tuple[str, ...] = (
    "OFAC SDN — US Treasury Specially Designated Nationals list (SDN.XML / "
    "consolidated CSV); the canonical sanctions feed this fixture mimics.",
    "BIS Entity List — US Commerce denied-parties; different schema, same diff/flag "
    "logic once normalized through parse_list.",
    "EU consolidated list — EEAS financial-sanctions consolidated file; multi-list "
    "reconciliation is the connector's job, not this scorer's.",
)
#: The connector that performs the network fetch is a SEPARATE component with these
#: runtime signals — recorded here so it's never confused with this pure scorer.
LIVE_CONNECTOR_RUNTIME: dict[str, str] = {
    "process_kind": "ingest.sanctions_feed",
    "side_effects": "external_call",
    "trust_boundary": "external",
}

#: Declared runtime-routing manifest for THIS component (the pure scorer). Mirrors
#: the field→pool mapping in the routing doc §4: deterministic + idempotent +
#: side_effects=none + no latency budget + local trust boundary → the cheap **cpu**
#: pool (scale-to-zero eligible). Asserted in the self-test so it can't silently rot.
RUNTIME: dict[str, Any] = {
    "process_kind": PROCESS_KIND,
    "deterministic": True,
    "idempotent": True,
    "side_effects": "none",
    "streaming": False,
    "latency_budget_ms": None,
    "trust_boundary": "local",
    "on_error": "raise",
    "resource_pool": "cpu",  # inferred per routing-doc §4 from the signals above
}


# ── SYNTHETIC fixture (offline stand-in for the live OFAC SDN feed) ───────────
#
# A handful of OFAC-SDN-*like* records. CLEARLY SYNTHETIC — placeholder company
# names and ``SYN-`` ids; NOT real persons or entities. Each record carries the
# fields the real SDN feed carries that matter for freshness: a stable entity id,
# a name, the sanctions program, and the list version + publication date it
# belongs to. V2 is a LATER version that (a) ADDS one entity, (b) REMOVES one
# (de-listed), and (c) CHANGES the program of one — so the diff exercises all three
# change kinds, and the done-bar "stale internal reference" demo has a real target.

#: List version + publication date for the OLDER fixture (synthetic).
SYN_LIST_VERSION_V1 = "OFAC-SDN-SYN-2026.05.01"
SYN_LIST_DATE_V1 = "2026-05-01"
#: List version + publication date for the CURRENT fixture (synthetic).
SYN_LIST_VERSION_V2 = "OFAC-SDN-SYN-2026.05.28"
SYN_LIST_DATE_V2 = "2026-05-28"

#: Older list version (synthetic). Each record: entity_id, name, program, plus the
#: list_version/date it was published under (so a parsed index keeps provenance).
SYNTHETIC_SDN_V1: tuple[dict[str, str], ...] = (
    {"entity_id": "SYN-0001", "name": "Northwind Trading LLC",
     "program": "SYN-RUSSIA-EO",
     "list_version": SYN_LIST_VERSION_V1, "list_date": SYN_LIST_DATE_V1},
    {"entity_id": "SYN-0002", "name": "Aurora Logistics SA",
     "program": "SYN-NARCOTICS",
     "list_version": SYN_LIST_VERSION_V1, "list_date": SYN_LIST_DATE_V1},
    {"entity_id": "SYN-0003", "name": "Granite Shipping Co",
     "program": "SYN-IRAN-EO",
     "list_version": SYN_LIST_VERSION_V1, "list_date": SYN_LIST_DATE_V1},
)

#: CURRENT list version (synthetic). Versus V1:
#:   - SYN-0007 "Meridian Components Inc" is ADDED (new designation),
#:   - SYN-0002 "Aurora Logistics SA" is REMOVED (de-listed),
#:   - SYN-0003 "Granite Shipping Co" CHANGED program (SYN-IRAN-EO -> SYN-RUSSIA-EO).
#: SYN-0001 is unchanged (the control: an unchanged entity must NOT appear in the diff).
SYNTHETIC_SDN_V2: tuple[dict[str, str], ...] = (
    {"entity_id": "SYN-0001", "name": "Northwind Trading LLC",
     "program": "SYN-RUSSIA-EO",
     "list_version": SYN_LIST_VERSION_V2, "list_date": SYN_LIST_DATE_V2},
    {"entity_id": "SYN-0003", "name": "Granite Shipping Co",
     "program": "SYN-RUSSIA-EO",  # changed from SYN-IRAN-EO
     "list_version": SYN_LIST_VERSION_V2, "list_date": SYN_LIST_DATE_V2},
    {"entity_id": "SYN-0007", "name": "Meridian Components Inc",  # ADDED
     "program": "SYN-EXPORT-CONTROL",
     "list_version": SYN_LIST_VERSION_V2, "list_date": SYN_LIST_DATE_V2},
)

#: The subset of per-entity fields whose change makes ``freshness_diff`` report a
#: record as ``changed`` (entity stayed listed, but a material field moved). Defined
#: once so the diff and any consumer agree on what "material" means. ``name`` is
#: included because a re-designation under a corrected legal name is material;
#: ``list_version``/``list_date`` are provenance, NOT material content, so they are
#: deliberately excluded (otherwise *every* entity would look "changed" each
#: version — the canonical no-magic-values trap).
MATERIAL_FIELDS: tuple[str, ...] = ("name", "program")


# ── Normalization helpers (deterministic, stdlib only) ───────────────────────

# Collapse internal whitespace + lowercase for stable name/version comparison. We
# normalize for COMPARISON only; the original surface form is preserved in the
# index value so provenance/output stays human-readable.
_WS_RE = re.compile(r"\s+")


def _norm(text: str) -> str:
    """Case/whitespace-fold a string for stable comparison (deterministic)."""
    return _WS_RE.sub(" ", text.strip()).lower()


def _ensure_str(value: Any, field: str) -> str:
    """Coerce a required string field, raising on the wrong type (on_error=raise)."""
    if not isinstance(value, str):
        raise TypeError(f"{field} must be str, got {type(value).__name__}")
    s = value.strip()
    if not s:
        raise ValueError(f"{field} must be non-empty")
    return s


def _version_key(version: str, date: str | None) -> tuple[str, str]:
    """Deterministic ordering key for a list version.

    Prefer the publication DATE (ISO ``YYYY-MM-DD`` sorts lexically == chronologically);
    fall back to the version STRING when no date is present. Returns a 2-tuple so
    two versions are always comparable WITHOUT a clock — we never call ``now()`` to
    decide which list is newer (that would break determinism). The version string is
    the tie-breaker so identical-date lists still order stably.
    """
    return (date or "", version)


# ── (1) parse_list — records -> normalized index ─────────────────────────────


def parse_list(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Normalize a sanctions feed (real or synthetic) into an indexed, versioned form.

    Args:
      records: an iterable of mappings, each with at least ``entity_id``, ``name``,
        ``program`` and the list ``list_version`` (``list_date`` optional). Extra
        fields are preserved verbatim on the entry (forward-compatible: the real
        SDN feed carries aliases/addresses we don't yet use).

    Returns a dict:
      ``entities``       — ``{entity_id: {…original fields…, "_norm_name": str}}``,
                           the listing index (membership == "this id is on the list").
      ``by_norm_name``   — ``{normalized_name: entity_id}`` so a claim that names an
                           entity textually (no id) can still be resolved.
      ``list_version``   — the single list version (asserted consistent across rows).
      ``list_date``      — the list publication date (or ``None``).
      ``version_key``    — the deterministic ordering key (see ``_version_key``).
      ``count``          — number of listed entities.
      ``provenance``     — ``{"list_version", "list_date", "source": "..."}`` echoed
                           into every downstream verdict so a flag is auditable.

    Raises:
      ValueError: empty input, a duplicate ``entity_id``, or rows that disagree on
        ``list_version`` (a parsed index is ONE list version by construction — the
        connector hands one version at a time; mixing them is a bug we refuse to
        paper over).
      TypeError: a record is not a mapping or a required field is the wrong type.

    Deterministic and idempotent: the index is a pure function of the records;
    re-parsing the same records yields an equal dict.
    """
    entities: dict[str, dict[str, Any]] = {}
    by_norm_name: dict[str, str] = {}
    list_version: str | None = None
    list_date: str | None = None

    seen_any = False
    for raw in records:
        seen_any = True
        if not isinstance(raw, Mapping):
            raise TypeError(f"each record must be a mapping, got {type(raw).__name__}")
        entity_id = _ensure_str(raw.get("entity_id"), "entity_id")
        name = _ensure_str(raw.get("name"), "name")
        program = _ensure_str(raw.get("program"), "program")
        row_version = _ensure_str(raw.get("list_version"), "list_version")
        row_date = raw.get("list_date")
        if row_date is not None and not isinstance(row_date, str):
            raise TypeError(f"list_date must be str or absent, got {type(row_date).__name__}")

        # One parsed index == one list version (see docstring/Raises).
        if list_version is None:
            list_version, list_date = row_version, row_date
        elif row_version != list_version:
            raise ValueError(
                f"records span multiple list versions ({list_version!r} vs {row_version!r}); "
                "parse one list version at a time"
            )

        if entity_id in entities:
            raise ValueError(f"duplicate entity_id in list: {entity_id!r}")

        entry = dict(raw)  # preserve every original field (forward-compatible)
        entry["_norm_name"] = _norm(name)
        entities[entity_id] = entry
        by_norm_name[entry["_norm_name"]] = entity_id

    if not seen_any:
        raise ValueError("cannot parse an empty sanctions list")

    assert list_version is not None  # established by the loop given non-empty input
    return {
        "entities": entities,
        "by_norm_name": by_norm_name,
        "list_version": list_version,
        "list_date": list_date,
        "version_key": _version_key(list_version, list_date),
        "count": len(entities),
        "provenance": {
            "list_version": list_version,
            "list_date": list_date,
            "source": "synthetic-fixture (live OFAC/BIS/EU via ingest.sanctions_feed seam)",
        },
    }


# ── (2) freshness_diff — old vs new list -> added/removed/changed ────────────


def freshness_diff(old_list: Mapping[str, Any], new_list: Mapping[str, Any]) -> dict[str, Any]:
    """Diff two PARSED lists into ``{added, removed, changed}`` with the version delta.

    Args:
      old_list, new_list: results of :func:`parse_list`. The direction is explicit
        (old -> new) and is NOT inferred from dates — the caller states which is
        which. We DO compute a ``direction`` field by comparing ``version_key`` so a
        caller that passes them backwards is told (``"backward"``/``"forward"``/
        ``"same"``), but we still diff exactly as handed (deterministic, no
        reordering).

    Returns a dict:
      ``added``        — ``[entry, …]`` entities in new but not old (new designations).
      ``removed``      — ``[entry, …]`` entities in old but not new (de-listings).
      ``changed``      — ``[{"entity_id", "before", "after", "changed_fields": [...]}]``
                         for entities present in both whose MATERIAL_FIELDS moved.
      ``unchanged_count`` — entities present in both with no material change (the
                         control: proves a no-op diff is genuinely empty, not just
                         unreported).
      ``version_delta`` — ``{"from": {version,date}, "to": {version,date}}``.
      ``direction``    — ``"forward"`` | ``"backward"`` | ``"same"`` (from version_key).
      ``has_changes``  — bool, True iff any of added/removed/changed is non-empty.

    Raises:
      KeyError/TypeError: if either argument is not a ``parse_list`` result.

    Deterministic: entity ids are iterated in sorted order, so the lists are stably
    ordered and a re-run is byte-identical.
    """
    old_entities = old_list["entities"]
    new_entities = new_list["entities"]
    if not isinstance(old_entities, dict) or not isinstance(new_entities, dict):
        raise TypeError("freshness_diff expects parse_list() results (missing 'entities')")

    old_ids = set(old_entities)
    new_ids = set(new_entities)

    # Sorted iteration → deterministic output ordering (No-Magic-Values: no reliance
    # on dict/set insertion order for a reproducible diff).
    added = [new_entities[eid] for eid in sorted(new_ids - old_ids)]
    removed = [old_entities[eid] for eid in sorted(old_ids - new_ids)]

    changed: list[dict[str, Any]] = []
    unchanged_count = 0
    for eid in sorted(old_ids & new_ids):
        before, after = old_entities[eid], new_entities[eid]
        changed_fields = [f for f in MATERIAL_FIELDS if before.get(f) != after.get(f)]
        if changed_fields:
            changed.append(
                {"entity_id": eid, "before": before, "after": after,
                 "changed_fields": changed_fields}
            )
        else:
            unchanged_count += 1

    ok, nk = old_list["version_key"], new_list["version_key"]
    direction = "same" if ok == nk else ("forward" if ok < nk else "backward")

    return {
        CHANGE_ADDED: added,
        CHANGE_REMOVED: removed,
        CHANGE_CHANGED: changed,
        "unchanged_count": unchanged_count,
        "version_delta": {
            "from": {"list_version": old_list["list_version"], "list_date": old_list["list_date"]},
            "to": {"list_version": new_list["list_version"], "list_date": new_list["list_date"]},
        },
        "direction": direction,
        "has_changes": bool(added or removed or changed),
    }


# ── (3) flag_stale_context — verdict + provenance for an internal claim ──────


def _resolve_entity(claim: Mapping[str, Any], current_list: Mapping[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    """Resolve a claim's referenced entity against the current list (by id, then name).

    Returns ``(entity_id, entry)`` where ``entry`` is the current-list record if the
    entity IS currently listed, else ``None``. ``entity_id`` is the id the claim
    referenced (resolved via name if no id was given), or ``None`` if the claim names
    no resolvable entity. Pure lookup — no mutation.
    """
    entities = current_list["entities"]
    by_name = current_list["by_norm_name"]

    cid = claim.get("entity_id")
    if isinstance(cid, str) and cid.strip():
        cid = cid.strip()
        return cid, entities.get(cid)

    cname = claim.get("entity_name")
    if isinstance(cname, str) and cname.strip():
        resolved = by_name.get(_norm(cname))
        if resolved is not None:
            return resolved, entities.get(resolved)
        return None, None  # named an entity that isn't on the list -> not resolvable to an id

    return None, None


def flag_stale_context(
    internal_claim: Mapping[str, Any],
    current_list: Mapping[str, Any],
) -> dict[str, Any]:
    """Flag an internal claim that LAGS or CONTRADICTS the current sanctions list.

    The done-bar of the beachhead: a stale internal sanction reference is flagged as
    a would-be VIOLATION against the fresh list.

    Args:
      internal_claim: a mapping describing what an internal control/doc asserts. Keys
        (all optional individually, but it must reference *something*):
          ``entity_id`` / ``entity_name`` — which entity the claim is about.
          ``status``            — the claim's assertion: ``"clear"`` or ``"listed"``
                                   (per ``LISTING_STATES``). The high-stakes case is
                                   ``"clear"`` while the list says ``listed``.
          ``cites_list_version``— the list version the internal doc was checked
                                   against (its provenance). If this is OLDER than the
                                   current list, the claim is at best ``stale``.
          ``cites_list_date``   — optional ISO date counterpart to the version.
      current_list: a :func:`parse_list` result for the CURRENT (live/fixture) list.

    Returns a dict:
      ``verdict``            — one of ``VERDICTS`` (``current`` / ``stale`` /
                               ``contradicted``).
      ``would_be_violation`` — bool. ``True`` only when the live list directly
                               contradicts the claim in the dangerous direction
                               (claim says ``clear`` but the entity IS listed now) —
                               the case a screening team must block on.
      ``reason``             — a one-line, human-readable explanation.
      ``entity_id``          — the resolved entity id (or ``None``).
      ``listed_now``         — bool: is the entity on the CURRENT list?
      ``claimed_status``     — the claim's normalized status (or ``None``).
      ``cited_version_key`` / ``current_version_key`` — the ordering keys compared.
      ``provenance``         — ``{"checked_against": <current provenance>,
                               "claim_cited": {version,date}}`` so the flag is
                               auditable: WHICH list version, and what the claim
                               relied on.

    Verdict logic (deterministic, in priority order):
      1. **contradicted** — the current list DIRECTLY disagrees with the claim:
         claim says ``clear`` but the entity is listed now, OR claim says ``listed``
         but the entity is not on the current list. (``clear`` vs ``listed`` is the
         would-be violation.) Contradiction is checked FIRST because a wrong answer
         outranks a merely-old one.
      2. **stale** — no outright contradiction on status, but the claim cites an
         OLDER list version than the current one (it has not been re-checked against
         the fresh list, so it cannot be trusted as current).
      3. **current** — the claim agrees with the current list AND (if it cites a
         version) cites the current version.

    Raises:
      TypeError: ``internal_claim``/``current_list`` not mappings, or ``status`` not
        a string.
      ValueError: ``status`` present but not in ``LISTING_STATES``; ``current_list``
        is not a ``parse_list`` result; the claim references no entity at all.

    Deterministic, pure, no side effects.
    """
    if not isinstance(internal_claim, Mapping):
        raise TypeError(f"internal_claim must be a mapping, got {type(internal_claim).__name__}")
    if not isinstance(current_list, Mapping) or "entities" not in current_list:
        raise ValueError("current_list must be a parse_list() result")

    # Normalize the claimed status (if any).
    claimed_status_raw = internal_claim.get("status")
    if claimed_status_raw is None:
        claimed_status: str | None = None
    else:
        if not isinstance(claimed_status_raw, str):
            raise TypeError(f"status must be str or absent, got {type(claimed_status_raw).__name__}")
        claimed_status = _norm(claimed_status_raw)
        if claimed_status not in LISTING_STATES:
            raise ValueError(f"status must be one of {LISTING_STATES}, got {claimed_status_raw!r}")

    entity_id, entry = _resolve_entity(internal_claim, current_list)
    if entity_id is None and not isinstance(internal_claim.get("entity_name"), str):
        raise ValueError("internal_claim must reference an entity (entity_id or entity_name)")
    listed_now = entry is not None

    # Version provenance comparison (deterministic; no clock).
    cited_version = internal_claim.get("cites_list_version")
    cited_date = internal_claim.get("cites_list_date")
    has_cite = isinstance(cited_version, str) and bool(cited_version.strip())
    cited_version = cited_version.strip() if has_cite else None
    cited_key = _version_key(cited_version, cited_date) if has_cite else None
    current_key: tuple[str, str] = tuple(current_list["version_key"])  # type: ignore[assignment]
    current_version = current_list["list_version"]
    # Staleness rule (order matters): a claim that cites the EXACT current version
    # string is current, regardless of whether it restated the publication date —
    # real docs cite the version label, not the date, so the date is only a
    # tie-breaker for DIFFERENT versions. Comparing the version key directly would
    # wrongly mark a date-less but correct citation as older (an empty date sorts
    # before a populated one). So: same version string ⇒ not older; otherwise fall
    # back to the deterministic ordering key.
    if not has_cite:
        is_older = False
    elif cited_version == current_version:
        is_older = False
    else:
        is_older = cited_key < current_key

    # ── Verdict (priority order: contradiction outranks staleness). ──
    if claimed_status == STATUS_CLEAR and listed_now:
        verdict = VERDICT_CONTRADICTED
        would_be_violation = True
        reason = (
            f"Internal doc says entity {entity_id!r} is CLEAR, but the current list "
            f"{current_list['list_version']!r} LISTS it (program "
            f"{entry.get('program', '?')!r}). Would-be sanctions violation."
        )
    elif claimed_status == STATUS_LISTED and not listed_now:
        verdict = VERDICT_CONTRADICTED
        would_be_violation = False  # over-blocking, not a violation — but still wrong vs the list
        reason = (
            f"Internal doc says entity {entity_id!r} is LISTED, but it is NOT on the "
            f"current list {current_list['list_version']!r} (de-listed or never listed)."
        )
    elif is_older:
        verdict = VERDICT_STALE
        would_be_violation = False
        reason = (
            f"Internal claim cites list version {cited_version!r}, older than the "
            f"current {current_list['list_version']!r}; re-check against the fresh list."
        )
    else:
        verdict = VERDICT_CURRENT
        would_be_violation = False
        if claimed_status is not None:
            reason = (
                f"Internal claim ({claimed_status}) agrees with the current list "
                f"{current_list['list_version']!r}."
            )
        else:
            reason = (
                f"Internal claim is in step with the current list "
                f"{current_list['list_version']!r}."
            )

    return {
        "verdict": verdict,
        "would_be_violation": would_be_violation,
        "reason": reason,
        "entity_id": entity_id,
        "listed_now": listed_now,
        "claimed_status": claimed_status,
        "cited_version_key": list(cited_key) if cited_key is not None else None,
        "current_version_key": list(current_key),
        "provenance": {
            "checked_against": dict(current_list["provenance"]),
            "claim_cited": {"list_version": cited_version, "list_date": cited_date},
        },
    }


# ── Self-test (proves the beachhead on the synthetic fixture) ────────────────


def _selftest() -> None:
    v1 = parse_list(SYNTHETIC_SDN_V1)
    v2 = parse_list(SYNTHETIC_SDN_V2)

    # ── parse_list: index shape + provenance + version key. ──
    assert v1["count"] == len(SYNTHETIC_SDN_V1) == 3, "v1 count wrong"
    assert v2["count"] == len(SYNTHETIC_SDN_V2) == 3, "v2 count wrong"
    assert v1["list_version"] == SYN_LIST_VERSION_V1
    assert v2["list_version"] == SYN_LIST_VERSION_V2
    # name-resolution index works (claim-by-name path).
    assert v2["by_norm_name"][_norm("Meridian Components Inc")] == "SYN-0007"
    # provenance is carried for downstream auditability.
    assert v2["provenance"]["list_version"] == SYN_LIST_VERSION_V2

    # parse_list refuses mixed versions and duplicate ids (refuse-to-paper-over).
    for bad, exc in (
        (list(SYNTHETIC_SDN_V1) + list(SYNTHETIC_SDN_V2), ValueError),  # mixed versions
        (list(SYNTHETIC_SDN_V1) + [SYNTHETIC_SDN_V1[0]], ValueError),   # duplicate id
        ([], ValueError),                                               # empty
    ):
        raised = False
        try:
            parse_list(bad)
        except exc:
            raised = True
        assert raised, f"parse_list should have raised {exc.__name__} on {bad!r:.40}"

    # ── freshness_diff: a NO-CHANGE diff is empty (the control). ──
    noop = freshness_diff(v2, v2)
    assert noop["has_changes"] is False, "self-diff must report no changes"
    assert noop[CHANGE_ADDED] == [] and noop[CHANGE_REMOVED] == [] and noop[CHANGE_CHANGED] == []
    assert noop["direction"] == "same"
    assert noop["unchanged_count"] == v2["count"], "every entity should be unchanged in a self-diff"

    # ── freshness_diff: V1 -> V2 detects ADDED, REMOVED, CHANGED exactly. ──
    diff = freshness_diff(v1, v2)
    assert diff["has_changes"] is True
    added_ids = {e["entity_id"] for e in diff[CHANGE_ADDED]}
    removed_ids = {e["entity_id"] for e in diff[CHANGE_REMOVED]}
    changed_ids = {c["entity_id"] for c in diff[CHANGE_CHANGED]}
    assert added_ids == {"SYN-0007"}, f"expected SYN-0007 added, got {added_ids}"
    assert removed_ids == {"SYN-0002"}, f"expected SYN-0002 removed, got {removed_ids}"
    assert changed_ids == {"SYN-0003"}, f"expected SYN-0003 changed, got {changed_ids}"
    # the changed entry names the moved field, and SYN-0001 (unchanged) is NOT in any bucket.
    assert diff[CHANGE_CHANGED][0]["changed_fields"] == ["program"], "should flag the program change"
    assert "SYN-0001" not in (added_ids | removed_ids | changed_ids), "unchanged entity leaked into diff"
    assert diff["unchanged_count"] == 1, "only SYN-0001 is unchanged across the bump"
    assert diff["direction"] == "forward", "V1->V2 must be forward"
    # direction is honest when handed backwards (still diffs as given).
    assert freshness_diff(v2, v1)["direction"] == "backward"
    # diff is deterministic (re-run identical).
    assert freshness_diff(v1, v2) == diff, "freshness_diff is not deterministic"

    # ── DONE-BAR: a stale internal sanction reference flagged as a would-be VIOLATION. ──
    # The added entity SYN-0007 was NOT on V1. An internal doc, checked only against
    # V1, asserts it is "clear" and cites the old version. Against the fresh V2 list
    # this is a would-be sanctions violation — and it must be caught.
    violation_claim = {
        "entity_id": "SYN-0007",
        "status": STATUS_CLEAR,
        "cites_list_version": SYN_LIST_VERSION_V1,
        "cites_list_date": SYN_LIST_DATE_V1,
    }
    v = flag_stale_context(violation_claim, v2)
    assert v["verdict"] == VERDICT_CONTRADICTED, f"stale 'clear' on a newly-listed entity must be contradicted, got {v['verdict']}"
    assert v["would_be_violation"] is True, "this is the would-be sanctions violation — must be flagged"
    assert v["listed_now"] is True
    assert v["provenance"]["checked_against"]["list_version"] == SYN_LIST_VERSION_V2
    assert v["provenance"]["claim_cited"]["list_version"] == SYN_LIST_VERSION_V1

    # ── STALE (not contradicted): claim agrees on status but cites the OLD version. ──
    # SYN-0001 is listed in BOTH versions; a doc that says "listed" but cites V1 is
    # not WRONG, just un-rechecked -> stale, not a violation.
    stale_claim = {
        "entity_id": "SYN-0001",
        "status": STATUS_LISTED,
        "cites_list_version": SYN_LIST_VERSION_V1,
    }
    s = flag_stale_context(stale_claim, v2)
    assert s["verdict"] == VERDICT_STALE, f"old-version citation should be stale, got {s['verdict']}"
    assert s["would_be_violation"] is False, "a correct-but-old claim is not a violation"

    # ── CONTRADICTED (other direction): claim says LISTED but entity was de-listed. ──
    delisted_claim = {"entity_id": "SYN-0002", "status": STATUS_LISTED,
                      "cites_list_version": SYN_LIST_VERSION_V2}
    d = flag_stale_context(delisted_claim, v2)
    assert d["verdict"] == VERDICT_CONTRADICTED, "claiming a de-listed entity is listed contradicts the current list"
    assert d["would_be_violation"] is False, "over-blocking is wrong-vs-list but not a sanctions violation"
    assert d["listed_now"] is False

    # ── CURRENT: claim agrees AND cites the current version (by NAME, no id). ──
    current_claim = {"entity_name": "Northwind Trading LLC", "status": STATUS_LISTED,
                     "cites_list_version": SYN_LIST_VERSION_V2}
    c = flag_stale_context(current_claim, v2)
    assert c["verdict"] == VERDICT_CURRENT, f"agreeing, current-version claim must be current, got {c['verdict']}"
    assert c["entity_id"] == "SYN-0001", "name resolution should map to the id"
    assert c["would_be_violation"] is False
    # the claim above cited the current version WITHOUT a date — must still be
    # current (regression guard: a date-less but correct citation is not "older").

    # ── A claim citing a version NEWER than the current list is NOT stale. ──
    # (Defensive: staleness is one-directional — only OLDER citations are stale.)
    ahead_claim = {"entity_id": "SYN-0001", "status": STATUS_LISTED,
                   "cites_list_version": "OFAC-SDN-SYN-2026.06.01", "cites_list_date": "2026-06-01"}
    a = flag_stale_context(ahead_claim, v2)
    assert a["verdict"] == VERDICT_CURRENT, f"a newer-than-current citation is not stale, got {a['verdict']}"

    # ── A claim with NO version citation at all, agreeing on status, is current. ──
    nover = flag_stale_context({"entity_id": "SYN-0001", "status": STATUS_LISTED}, v2)
    assert nover["verdict"] == VERDICT_CURRENT, "no-citation agreeing claim should be current"

    # ── flag_stale_context is deterministic + idempotent (re-run identical). ──
    assert flag_stale_context(violation_claim, v2) == v, "flag_stale_context is not deterministic"

    # ── on_error=raise: bad status / no entity referenced. ──
    for bad_claim, exc in (
        ({"entity_id": "SYN-0001", "status": "frozen"}, ValueError),  # not a listing state
        ({"status": STATUS_CLEAR}, ValueError),                       # references no entity
        ({"entity_id": "SYN-0001", "status": 123}, TypeError),        # wrong type
    ):
        raised = False
        try:
            flag_stale_context(bad_claim, v2)
        except exc:
            raised = True
        assert raised, f"flag_stale_context should raise {exc.__name__} on {bad_claim!r}"

    # ── Runtime manifest is the declared one + self-consistent with routing §4. ──
    rt = RUNTIME
    assert rt["process_kind"] == PROCESS_KIND
    assert rt["deterministic"] is True and rt["idempotent"] is True
    assert rt["side_effects"] == "none"
    assert rt["streaming"] is False and rt["latency_budget_ms"] is None
    assert rt["trust_boundary"] == "local"
    # deterministic + idempotent + side_effects=none + no latency budget + local
    # trust boundary ⇒ the cheap cpu pool (NOT burst/gpu/sandbox) per routing §4.
    assert rt["resource_pool"] == "cpu", f"routing pool mismatch: {rt['resource_pool']}"
    # the LIVE fetch is a SEPARATE component with an external boundary (the seam).
    assert LIVE_CONNECTOR_RUNTIME["trust_boundary"] == "external"
    assert LIVE_CONNECTOR_RUNTIME["side_effects"] == "external_call"

    print(
        "PASS — sanctions_freshness: "
        f"parse_list indexed v1={v1['count']}/v2={v2['count']} (provenance carried); "
        "no-change diff empty; V1->V2 diff added=SYN-0007 removed=SYN-0002 changed=SYN-0003(program); "
        "DONE-BAR: stale 'clear' on newly-listed SYN-0007 -> CONTRADICTED + would_be_violation=True; "
        "old-version 'listed' -> stale; de-listed 'listed' -> contradicted; "
        "agreeing current-version -> current; deterministic re-run identical; runtime=cpu pool. "
        "(synthetic fixture; live OFAC/BIS/EU via the ingest.sanctions_feed seam — no network here)"
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Sanctions freshness — flag internal claims that lag/contradict the current list."
    )
    p.add_argument(
        "--demo", action="store_true",
        help="Print the V1->V2 freshness diff and the done-bar violation verdict as JSON.",
    )
    return p


def _demo() -> None:
    """Emit the headline diff + the done-bar verdict as JSON (no asserts; for humans)."""
    v1, v2 = parse_list(SYNTHETIC_SDN_V1), parse_list(SYNTHETIC_SDN_V2)
    diff = freshness_diff(v1, v2)
    verdict = flag_stale_context(
        {"entity_id": "SYN-0007", "status": STATUS_CLEAR,
         "cites_list_version": SYN_LIST_VERSION_V1, "cites_list_date": SYN_LIST_DATE_V1},
        v2,
    )
    print(json.dumps({
        "version_delta": diff["version_delta"],
        "added": [e["entity_id"] for e in diff[CHANGE_ADDED]],
        "removed": [e["entity_id"] for e in diff[CHANGE_REMOVED]],
        "changed": [c["entity_id"] for c in diff[CHANGE_CHANGED]],
        "done_bar_verdict": verdict,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()
    if args.demo:
        _demo()
    else:
        _selftest()
