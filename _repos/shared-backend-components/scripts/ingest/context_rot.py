#!/usr/bin/env python3
"""scripts.ingest.context_rot — the context-rot manager (offline, deterministic).

Freshness ≠ correctness, and "the document is stale" is too coarse. This module decides, per
cached context item, whether it is still safe to SERVE or must be REFRESHED / BLOCKED / sent to
HUMAN REVIEW — from five independent signals:

  * **TTL** — has the item aged past its class budget? (raw snapshot / generated artifact /
    pack / external authority / local memory each have their own TTL.)
  * **Source-hash CDC** — did the upstream bytes change since we cached? (reuses
    ``scripts.foundry.scrapers.content_hash`` — the same hash the connectors stamp.)
  * **ACL change** — did the source's permissions change under us? (must re-check before serve.)
  * **Supersession** — has a newer authoritative version replaced this claim?
  * **Resolvability** — does the source handle still resolve at all?

It is the policy sibling of the connectors: ``sanctions_feed_live`` / ``document_decompose``
stamp ``content_hash`` + lineage at ingest; THIS decides, later, whether that cached context has
rotted. It composes — never re-implements — the CDC hash, and reuses the freshness verdict spirit
of ``scripts.sanctions.sanctions_freshness`` (current/stale/contradicted) generalized to TTL+ACL.

**Determinism (the proof discipline):** ``now_s`` is ALWAYS passed in — this module reads no clock,
no RNG, no network, no filesystem. Same inputs → byte-identical assessment, so the self-test is a
real, reproducible proof (mirrors ``document_decompose.py``). The live "what changed upstream"
fetch is the connectors' job (their ``--live``); here the current hash/ACL are HANDED in.

Stdlib only. CLI:
    python3 _repos/shared-backend-components/scripts/ingest/context_rot.py --self-test
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

# Make the repo root importable under direct invocation (mirrors the sibling connectors).
if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

# Reuse the CDC hash the connectors stamp — ONE definition of "content identity" (No-Magic-Values).
from scripts.foundry.scrapers import content_hash

# ── TTL classes (seconds) — each with a unit/rationale; no bare literals (No-Magic-Values) ──
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR

#: A raw fetched snapshot of a volatile authority (sanctions list, regulation): re-verify daily —
#: stale here is a compliance event.
TTL_RAW_SNAPSHOT_S = 1 * SECONDS_PER_DAY
#: A derived/parsed artifact (decomposed doc tree, extracted table): valid until its source moves;
#: a week is a safe re-derive cadence absent a CDC signal.
TTL_GENERATED_ARTIFACT_S = 7 * SECONDS_PER_DAY
#: A served context pack: short — it is a point-in-time assembly the agent caches; force a rebuild
#: so a consumer can't sit on a day-old pack.
TTL_PACK_S = 12 * SECONDS_PER_HOUR
#: An external authoritative fact (gov/standards): re-check daily (same risk class as raw snapshot).
TTL_EXTERNAL_AUTHORITY_S = 1 * SECONDS_PER_DAY
#: Local/private memory: long — it is the user's own context, not a volatile external source.
TTL_LOCAL_MEMORY_S = 30 * SECONDS_PER_DAY

TTL_BY_CLASS: dict[str, int] = {
    "raw_snapshot": TTL_RAW_SNAPSHOT_S,
    "generated_artifact": TTL_GENERATED_ARTIFACT_S,
    "pack": TTL_PACK_S,
    "external_authority": TTL_EXTERNAL_AUTHORITY_S,
    "local_memory": TTL_LOCAL_MEMORY_S,
}

#: Fraction of TTL after which an item is WATCH (aging but not yet expired) — one definition.
WATCH_FRACTION = 0.8

# ── Rot states + serve actions (open vocab; the closed seed) ─────────────────
STATE_FRESH = "fresh"
STATE_WATCH = "watch"
STATE_EXPIRED = "expired"
STATE_SOURCE_HASH_CHANGED = "source_hash_changed"
STATE_PERMISSION_CHANGED = "permission_changed"
STATE_SUPERSEDED = "superseded"
STATE_HANDLE_UNRESOLVABLE = "source_handle_unresolvable"

ACTION_SERVE = "serve"                  # safe to serve as-is
ACTION_WATCH = "serve_flagged"          # serve, but surface the watch
ACTION_REFRESH = "refresh"              # re-ingest/re-derive before serving
ACTION_LIVE_VALIDATE = "live_validate"  # re-verify against the live authority before serving
ACTION_BLOCK = "block"                  # do NOT serve (held out)
ACTION_HUMAN_REVIEW = "human_review"    # route to a steward

#: States that must NOT be served (the promotion-boundary side of context rot).
BLOCKING_STATES = frozenset({STATE_HANDLE_UNRESOLVABLE, STATE_PERMISSION_CHANGED, STATE_SUPERSEDED})


@dataclass(frozen=True)
class CachedItem:
    """A piece of context we cached earlier and now must re-assess for rot.

    ``cached_at_s`` is an absolute epoch second stamped at ingest; ``ttl_class`` selects the TTL.
    ``content_hash`` / ``acl_hash`` are what we recorded then. Pure data — no behavior.
    """
    handle: str
    ttl_class: str
    cached_at_s: int
    content_hash: str
    acl_hash: str | None = None


@dataclass(frozen=True)
class RotAssessment:
    handle: str
    state: str
    action: str
    reason: str
    age_s: int
    ttl_s: int

    @property
    def servable(self) -> bool:
        return self.state not in BLOCKING_STATES and self.state != STATE_EXPIRED

    def as_dict(self) -> dict[str, Any]:
        return {"handle": self.handle, "state": self.state, "action": self.action,
                "reason": self.reason, "age_s": self.age_s, "ttl_s": self.ttl_s,
                "servable": self.servable}


def assess(
    item: CachedItem,
    *,
    now_s: int,
    current_content_hash: str | None = None,
    current_acl_hash: str | None = None,
    resolvable: bool = True,
    superseded: bool = False,
) -> RotAssessment:
    """Decide whether a cached item has rotted. Deterministic pure function of its arguments.

    Priority (worst first — a wrong/forbidden item outranks a merely-old one):
      unresolvable → permission_changed → superseded → source_hash_changed → TTL(expired/watch/fresh).
    The "current_*" values and ``resolvable``/``superseded`` are HANDED in (the live check is the
    connectors' job); when omitted, that signal is simply not evaluated (honest, not assumed-fresh
    for the blocking signals — only TTL is unconditional).

    Raises ``ValueError`` on an unknown ``ttl_class`` (fail closed; never serve an un-budgeted item).
    """
    if item.ttl_class not in TTL_BY_CLASS:
        raise ValueError(f"unknown ttl_class {item.ttl_class!r}; known: {sorted(TTL_BY_CLASS)}")
    ttl_s = TTL_BY_CLASS[item.ttl_class]
    age_s = int(now_s) - int(item.cached_at_s)

    if not resolvable:
        return RotAssessment(item.handle, STATE_HANDLE_UNRESOLVABLE, ACTION_BLOCK,
                             "source handle no longer resolves", age_s, ttl_s)
    if current_acl_hash is not None and item.acl_hash is not None and current_acl_hash != item.acl_hash:
        return RotAssessment(item.handle, STATE_PERMISSION_CHANGED, ACTION_BLOCK,
                             "ACL changed at source since cache — re-check before serving", age_s, ttl_s)
    if superseded:
        return RotAssessment(item.handle, STATE_SUPERSEDED, ACTION_REFRESH,
                             "a newer authoritative version supersedes this item", age_s, ttl_s)
    if current_content_hash is not None and current_content_hash != item.content_hash:
        return RotAssessment(item.handle, STATE_SOURCE_HASH_CHANGED, ACTION_REFRESH,
                             "upstream content hash changed (CDC) — re-ingest before serving", age_s, ttl_s)
    if age_s > ttl_s:
        return RotAssessment(item.handle, STATE_EXPIRED, ACTION_LIVE_VALIDATE,
                             f"age {age_s}s exceeds {item.ttl_class} TTL {ttl_s}s", age_s, ttl_s)
    if age_s > int(ttl_s * WATCH_FRACTION):
        return RotAssessment(item.handle, STATE_WATCH, ACTION_WATCH,
                             f"age {age_s}s past {int(WATCH_FRACTION*100)}% of TTL {ttl_s}s", age_s, ttl_s)
    return RotAssessment(item.handle, STATE_FRESH, ACTION_SERVE, "within TTL; no change/ACL/supersession signal", age_s, ttl_s)


def assess_pack(items: list[tuple[CachedItem, dict]], *, now_s: int) -> dict[str, Any]:
    """Assess every item backing a pack; a pack is servable only if NO item is blocking.

    ``items`` is ``[(CachedItem, signals_kwargs), ...]`` where ``signals_kwargs`` is the per-item
    current_content_hash/current_acl_hash/resolvable/superseded (the live observations handed in).
    Returns a governed decision: per-item assessments + the pack-level serve/hold call.
    """
    assessments = [assess(it, now_s=now_s, **kw) for it, kw in items]
    blocking = [a for a in assessments if not a.servable]
    needs_refresh = [a for a in assessments if a.action in (ACTION_REFRESH, ACTION_LIVE_VALIDATE)]
    return {
        "now_s": now_s,
        "assessments": [a.as_dict() for a in assessments],
        "servable": not blocking,
        "blocking_handles": [a.handle for a in blocking],
        "refresh_handles": [a.handle for a in needs_refresh],
        "headline": (
            f"{len(assessments)} item(s): {len(assessments)-len(blocking)} servable, "
            f"{len(blocking)} blocked, {len(needs_refresh)} need refresh/live-validate"
        ),
    }


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    h_fresh = content_hash("the live OFAC list as of today")
    now = 1_000_000_000  # fixed epoch second (determinism — no clock)

    # ── TTL bands on a raw snapshot (1-day TTL) ──
    fresh = CachedItem("ctx://ofac/sdn", "raw_snapshot", now - 1 * SECONDS_PER_HOUR, h_fresh)
    a = assess(fresh, now_s=now, current_content_hash=h_fresh)
    check("within TTL → fresh/serve", a.state == STATE_FRESH and a.action == ACTION_SERVE and a.servable)
    watch = CachedItem("ctx://ofac/sdn", "raw_snapshot", now - 22 * SECONDS_PER_HOUR, h_fresh)
    a = assess(watch, now_s=now, current_content_hash=h_fresh)
    check("past 80% of TTL → watch (served, flagged)", a.state == STATE_WATCH and a.action == ACTION_WATCH and a.servable)
    old = CachedItem("ctx://ofac/sdn", "raw_snapshot", now - 2 * SECONDS_PER_DAY, h_fresh)
    a = assess(old, now_s=now, current_content_hash=h_fresh)
    check("past TTL → expired/live_validate (not servable)", a.state == STATE_EXPIRED and a.action == ACTION_LIVE_VALIDATE and not a.servable)

    # ── CDC: upstream content hash changed → refresh (outranks TTL freshness) ──
    a = assess(fresh, now_s=now, current_content_hash=content_hash("the OFAC list AFTER a new designation"))
    check("content hash changed → source_hash_changed/refresh", a.state == STATE_SOURCE_HASH_CHANGED and a.action == ACTION_REFRESH)

    # ── ACL change → block (must not serve newly-restricted context) ──
    acl_item = CachedItem("ctx://acme/confluence/doc/1", "generated_artifact", now - SECONDS_PER_HOUR, h_fresh, acl_hash="acl-v1")
    a = assess(acl_item, now_s=now, current_content_hash=h_fresh, current_acl_hash="acl-v2")
    check("ACL changed → permission_changed/block (not servable)", a.state == STATE_PERMISSION_CHANGED and not a.servable)

    # ── supersession + unresolvable ──
    a = assess(fresh, now_s=now, current_content_hash=h_fresh, superseded=True)
    check("superseded → superseded/refresh (not servable)", a.state == STATE_SUPERSEDED and a.action == ACTION_REFRESH and not a.servable)
    a = assess(fresh, now_s=now, resolvable=False)
    check("unresolvable handle → block (not servable)", a.state == STATE_HANDLE_UNRESOLVABLE and not a.servable)

    # ── priority: a blocking signal outranks a TTL-fresh item ──
    a = assess(fresh, now_s=now, resolvable=False, current_content_hash=h_fresh)
    check("blocking signal outranks fresh TTL", a.state == STATE_HANDLE_UNRESOLVABLE)

    # ── unknown ttl_class fails closed ──
    raised = False
    try:
        assess(CachedItem("x", "nope", now, h_fresh), now_s=now)
    except ValueError:
        raised = True
    check("unknown ttl_class raises (fail closed)", raised)

    # ── pack-level: one blocking item holds the whole pack ──
    pack = assess_pack([
        (CachedItem("ctx://a", "pack", now - SECONDS_PER_HOUR, h_fresh), {"current_content_hash": h_fresh}),
        (CachedItem("ctx://b", "raw_snapshot", now - SECONDS_PER_HOUR, h_fresh, acl_hash="v1"),
         {"current_acl_hash": "v2"}),  # ACL changed → blocks
    ], now_s=now)
    check("pack with one blocking item is NOT servable", pack["servable"] is False and pack["blocking_handles"] == ["ctx://b"])

    # ── determinism: same inputs → identical assessment ──
    a1 = assess(watch, now_s=now, current_content_hash=h_fresh).as_dict()
    a2 = assess(watch, now_s=now, current_content_hash=h_fresh).as_dict()
    check("assess is deterministic", a1 == a2)

    print(f"\n{'all context_rot self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Context-rot manager (TTL/CDC/ACL/supersession → serve decision).")
    p.add_argument("--self-test", action="store_true", help="offline, deterministic")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
