#!/usr/bin/env python3
"""scripts.temporal_cdc_primitives — RETROACTIVE CDC (owner-directed 2026-07-08): finding changes and
historical data in environments that never captured them — reconstruct change events from snapshots, build
per-entity timelines, and surface the anomalies/inconsistencies that history reveals.

  * SNAPSHOT DIFF — two versions of a table (rows by key) -> added / removed / changed(field, before,
    after). The atom everything else composes.
  * RETROACTIVE CDC — a SEQUENCE of snapshots -> a change-event stream (create/update/delete with
    before/after per field, snapshot-attributed): the CDC feed the source system never emitted.
  * TIMELINES — merge timestamped rows and reconstructed events from MULTIPLE sources into one ordered
    per-entity history.
  * ANOMALIES the history exposes — FLIP-FLOPS (A -> B -> A reversions), IMPOSSIBLE TRANSITIONS against a
    data-driven allowed-transition map (resolved -> open -> deleted -> active), TIMESTAMP inconsistencies
    (updated < created, future dates), SNAPSHOT GAPS against an expected cadence, and CROSS-SOURCE
    CONFLICTS (same entity key, different values in different tables).

Pure functions over row dicts (DB reads happen upstream via cross_table_discovery_primitives); everything
returns findings that ROUTE TO REVIEW — reconstruction is evidence, never silent correction.
candidate=true, serves_truth=false.

    python3 scripts/temporal_cdc_primitives.py --self-test
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
import inspect  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"temporal_cdc_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-cdc"


def _by_key(rows: list[dict[str, Any]], key: str) -> dict[Any, dict[str, Any]]:
    return {r[key]: r for r in rows if r.get(key) is not None}


# ── ATOMIC primitives ─────────────────────────────────────────────────────────────────────────────────────────
def diff_snapshots(old_rows: list[dict[str, Any]], new_rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    """Two table versions -> added / removed / changed (per-field before/after). Deterministic ordering."""
    old, new = _by_key(old_rows, key), _by_key(new_rows, key)
    added = sorted(k for k in new if k not in old)
    removed = sorted(k for k in old if k not in new)
    changed = []
    for k in sorted(set(old) & set(new), key=str):
        for field in sorted(set(old[k]) | set(new[k])):
            if field == key:
                continue
            b, a = old[k].get(field), new[k].get(field)
            if b != a:
                changed.append({"key": k, "field": field, "before": b, "after": a})
    return {"key_column": key, "added": added, "removed": removed, "changed": changed, **BOUNDARY}


def reconstruct_change_events(snapshots: list[tuple[str, list[dict[str, Any]]]], key: str) -> list[dict[str, Any]]:
    """RETROACTIVE CDC: an ordered snapshot sequence [(label, rows), ...] -> create/update/delete events —
    the change feed the source never emitted. Every event carries its snapshot attribution; precision is
    the snapshot cadence (recorded, not overstated: observed_between, not occurred_at)."""
    events: list[dict[str, Any]] = []
    for (prev_label, prev_rows), (cur_label, cur_rows) in zip(snapshots, snapshots[1:]):
        d = diff_snapshots(prev_rows, cur_rows, key)
        window = {"observed_between": [prev_label, cur_label]}
        cur = _by_key(cur_rows, key)
        for k in d["added"]:
            events.append({"event_type": "create", "key": k, "after": cur[k], **window, **BOUNDARY})
        for k in d["removed"]:
            events.append({"event_type": "delete", "key": k,
                           "before": _by_key(prev_rows, key)[k], **window, **BOUNDARY})
        for ch in d["changed"]:
            events.append({"event_type": "update", "key": ch["key"], "field": ch["field"],
                           "before": ch["before"], "after": ch["after"], **window, **BOUNDARY})
    return events


def build_entity_timeline(entity_key_value: Any, *, events: list[dict[str, Any]],
                          timestamped_rows: Optional[list[dict[str, Any]]] = None,
                          key: str = "key", timestamp_field: str = "occurred_at") -> list[dict[str, Any]]:
    """One entity's ordered history: reconstructed CDC events + natively-timestamped rows from any number
    of sources, merged and sorted (window-end for reconstructed events; sources named)."""
    timeline = []
    for e in events:
        if e.get(key if key in e else "key") == entity_key_value:
            timeline.append({"at": e.get("observed_between", ["", ""])[1], "precision": "snapshot_window",
                             "source": "retroactive_cdc", **{k: v for k, v in e.items()
                                                             if k not in ("candidate", "serves_truth")}})
    for r in timestamped_rows or []:
        if r.get(key) == entity_key_value and r.get(timestamp_field):
            timeline.append({"at": str(r[timestamp_field]), "precision": "recorded_timestamp",
                             "source": r.get("source", "timestamped_row"), "row": r})
    return sorted(timeline, key=lambda t: (str(t["at"]), t.get("source", "")))


def detect_flip_flops(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A -> B -> A reversions per (key, field): the classic sign of dueling processes or bad merges."""
    seq: dict[tuple, list[Any]] = {}
    for e in events:
        if e.get("event_type") == "update":
            seq.setdefault((e["key"], e["field"]), []).append((e["before"], e["after"]))
    out = []
    for (k, field), changes in sorted(seq.items(), key=str):
        values = [changes[0][0]] + [a for _b, a in changes]
        for i in range(len(values) - 2):
            if values[i] == values[i + 2] and values[i] != values[i + 1]:
                out.append({"key": k, "field": field, "pattern": [values[i], values[i + 1], values[i + 2]],
                            "finding": "flip_flop_reversion", **BOUNDARY})
                break
    return out


def detect_impossible_transitions(events: list[dict[str, Any]], *, field: str,
                                  allowed: dict[str, list[str]]) -> list[dict[str, Any]]:
    """State-machine check against a DATA-DRIVEN allowed-transition map: transitions history says happened
    but the domain says cannot (resolved -> open may be allowed; deleted -> active is not)."""
    out = []
    for e in events:
        if e.get("event_type") == "update" and e.get("field") == field:
            frm, to = str(e["before"]), str(e["after"])
            if to not in allowed.get(frm, []):
                out.append({"key": e["key"], "field": field, "from": frm, "to": to,
                            "finding": "impossible_transition",
                            "observed_between": e.get("observed_between"), **BOUNDARY})
    return out


def detect_timestamp_inconsistencies(rows: list[dict[str, Any]], *, created_field: str = "created_at",
                                     updated_field: str = "updated_at",
                                     now_iso: str = "") -> list[dict[str, Any]]:
    """updated < created; future timestamps vs a SUPPLIED now (never a hidden clock read — determinism)."""
    out = []
    for r in rows:
        c, u = str(r.get(created_field) or ""), str(r.get(updated_field) or "")
        if c and u and u < c:
            out.append({"row": r, "finding": "updated_before_created", **BOUNDARY})
        if now_iso:
            for f in (created_field, updated_field):
                v = str(r.get(f) or "")
                if v and v > now_iso:
                    out.append({"row": r, "field": f, "finding": "future_timestamp", **BOUNDARY})
    return out


def detect_snapshot_gaps(labels: list[str], *, expected: list[str]) -> list[dict[str, Any]]:
    """Missing periods against an expected cadence list (expected is DATA — never computed from a clock)."""
    have = set(labels)
    return [{"missing_period": p, "finding": "snapshot_gap", **BOUNDARY} for p in expected if p not in have]


def detect_cross_source_conflicts(sources: dict[str, list[dict[str, Any]]], key: str) -> list[dict[str, Any]]:
    """Same entity key, DIFFERENT values per field across source tables — the inconsistency map that drives
    survivorship decisions (finding routes to review; it never picks a winner itself)."""
    out = []
    keyed = {name: _by_key(rows, key) for name, rows in sources.items()}
    all_keys = sorted({k for m in keyed.values() for k in m}, key=str)
    for k in all_keys:
        present = {name: m[k] for name, m in keyed.items() if k in m}
        if len(present) < 2:
            continue
        fields = sorted({f for r in present.values() for f in r if f != key})
        for f in fields:
            values = {name: r.get(f) for name, r in present.items() if f in r}
            if len({json.dumps(v, sort_keys=True, default=str) for v in values.values()}) > 1:
                out.append({"key": k, "field": f, "values_by_source": values,
                            "finding": "cross_source_conflict",
                            "action": "route_to_survivorship_review", **BOUNDARY})
    return out


# ── COMPOSITE ─────────────────────────────────────────────────────────────────────────────────────────────────
COMPOSITE_PLANS = {"retroactive_cdc_audit": ["diff_snapshots", "reconstruct_change_events",
                                             "detect_flip_flops", "detect_timestamp_inconsistencies",
                                             "detect_snapshot_gaps"]}


def retroactive_cdc_audit(snapshots: list[tuple[str, list[dict[str, Any]]]], key: str, *,
                          status_field: str = "", allowed_transitions: Optional[dict[str, list[str]]] = None,
                          expected_periods: Optional[list[str]] = None) -> dict[str, Any]:
    """COMPOSITE: snapshots -> reconstructed change events + every anomaly family in one receipt. Evidence
    for review, never silent correction."""
    events = reconstruct_change_events(snapshots, key)
    ts_findings = []
    seen_ts: set[str] = set()
    for label, rows in snapshots:  # a retroactive audit scans ALL of history, not just the latest state
        for f in detect_timestamp_inconsistencies(rows):
            fp = json.dumps(f, sort_keys=True, default=str)
            if fp not in seen_ts:
                seen_ts.add(fp)
                ts_findings.append({**f, "first_observed_snapshot": label})
    return {"key_column": key, "n_snapshots": len(snapshots), "events": events,
            "n_events": len(events),
            "by_type": {t: sum(1 for e in events if e["event_type"] == t)
                        for t in ("create", "update", "delete")},
            "flip_flops": detect_flip_flops(events),
            "impossible_transitions": detect_impossible_transitions(
                events, field=status_field, allowed=allowed_transitions or {}) if status_field else [],
            "timestamp_inconsistencies": ts_findings,
            "snapshot_gaps": detect_snapshot_gaps([s[0] for s in snapshots],
                                                  expected=expected_periods or []),
            "action": "findings_route_to_review_never_autocorrect", **BOUNDARY}


_ATOMIC_FNS = (diff_snapshots, reconstruct_change_events, build_entity_timeline, detect_flip_flops,
               detect_impossible_transitions, detect_timestamp_inconsistencies, detect_snapshot_gaps,
               detect_cross_source_conflicts)
_COMPOSITE_FNS = (retroactive_cdc_audit,)


def all_cards() -> list[dict[str, Any]]:
    cards = []
    for fn in _ATOMIC_FNS + _COMPOSITE_FNS:
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        composite = fn in _COMPOSITE_FNS
        cards.append({"primitive_id": canonical_id(CARD_PREFIX, title, fn.__name__),
                      "impl_name": fn.__name__, "record_type": "temporal_cdc_primitive",
                      "kind": "primitive_group" if composite else "primitive", "title": title,
                      "executable_body": inspect.getsource(fn), "language": "python",
                      "input_edge": "TableSnapshotSequence", "output_edge": "ReconstructedChangeEvidence",
                      "blackbox": f"{'Composite' if composite else 'Atomic'} retroactive-CDC primitive: "
                                  f"{title} Input: snapshot/row sequences. Output: change events / "
                                  f"timelines / anomaly findings (evidence, never correction).",
                      "plan_steps": COMPOSITE_PLANS.get(fn.__name__, []), "tier": "common", **BOUNDARY})
    return cards


# ── self-test ─────────────────────────────────────────────────────────────────────────────────────────────────
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    s1 = [{"id": 1, "status": "open", "owner": "a", "created_at": "2026-01-05", "updated_at": "2026-01-05"},
          {"id": 2, "status": "open", "owner": "b", "created_at": "2026-01-06", "updated_at": "2026-01-06"}]
    s2 = [{"id": 1, "status": "resolved", "owner": "a", "created_at": "2026-01-05", "updated_at": "2026-02-01"},
          {"id": 3, "status": "open", "owner": "c", "created_at": "2026-02-02", "updated_at": "2026-02-01"}]
    s3 = [{"id": 1, "status": "open", "owner": "a", "created_at": "2026-01-05", "updated_at": "2026-03-01"},
          {"id": 3, "status": "deleted", "owner": "c", "created_at": "2026-02-02", "updated_at": "2026-03-01"}]
    d = diff_snapshots(s1, s2, "id")
    checks.append(("DIFF: added [3], removed [2], changed status+updated_at for id 1 with before/after",
                   d["added"] == [3] and d["removed"] == [2]
                   and {"key": 1, "field": "status", "before": "open", "after": "resolved"} in d["changed"]))
    snaps = [("2026-01", s1), ("2026-02", s2), ("2026-03", s3)]
    events = reconstruct_change_events(snaps, "id")
    checks.append(("RETROACTIVE CDC: create/update/delete events reconstructed with snapshot attribution "
                   "(observed_between, precision honest)",
                   any(e["event_type"] == "create" and e["key"] == 3
                       and e["observed_between"] == ["2026-01", "2026-02"] for e in events)
                   and any(e["event_type"] == "delete" and e["key"] == 2 for e in events)
                   and sum(1 for e in events if e["event_type"] == "update") >= 3))
    tl = build_entity_timeline(1, events=events,
                               timestamped_rows=[{"id": 1, "occurred_at": "2026-01-20",
                                                  "source": "email_log", "note": "customer replied"}],
                               key="id", timestamp_field="occurred_at")
    checks.append(("TIMELINE: reconstructed events + native timestamped rows from another source merge "
                   "into one ordered history", len(tl) >= 3 and tl == sorted(tl, key=lambda t: str(t["at"]))
                   and any(t["source"] == "email_log" for t in tl)
                   and any(t["precision"] == "snapshot_window" for t in tl)))
    ff = detect_flip_flops(events)
    checks.append(("FLIP-FLOP: id 1 status open -> resolved -> open caught",
                   any(f["key"] == 1 and f["pattern"] == ["open", "resolved", "open"] for f in ff)))
    allowed = {"open": ["resolved"], "resolved": ["closed"], "closed": [], "deleted": []}
    it = detect_impossible_transitions(events, field="status", allowed=allowed)
    checks.append(("IMPOSSIBLE TRANSITIONS against the data-driven map: resolved->open AND open->deleted "
                   "both flagged", {(f["from"], f["to"]) for f in it}
                   >= {("resolved", "open"), ("open", "deleted")}))
    ts = detect_timestamp_inconsistencies(s2, now_iso="2026-02-15")
    checks.append(("TIMESTAMPS: updated_before_created caught (id 3: updated 02-01 < created 02-02); "
                   "now is SUPPLIED, never a hidden clock",
                   any(f["finding"] == "updated_before_created" for f in ts)))
    gaps = detect_snapshot_gaps(["2026-01", "2026-03"], expected=["2026-01", "2026-02", "2026-03"])
    checks.append(("GAPS: missing 2026-02 snapshot detected against expected cadence",
                   gaps == [{"missing_period": "2026-02", "finding": "snapshot_gap", **BOUNDARY}]))
    conflicts = detect_cross_source_conflicts(
        {"crm": [{"id": 1, "email": "a@x.com"}], "billing": [{"id": 1, "email": "a@OLD.com"}]}, "id")
    checks.append(("CROSS-SOURCE CONFLICT: same key, different email across crm/billing -> survivorship "
                   "review (never auto-picks a winner)",
                   len(conflicts) == 1 and conflicts[0]["values_by_source"]
                   == {"crm": "a@x.com", "billing": "a@OLD.com"}
                   and conflicts[0]["action"] == "route_to_survivorship_review"))
    audit = retroactive_cdc_audit(snaps, "id", status_field="status", allowed_transitions=allowed,
                                  expected_periods=["2026-01", "2026-02", "2026-03"])
    checks.append(("COMPOSITE AUDIT: one receipt with events by type + every anomaly family + "
                   "route-to-review action", audit["by_type"]["create"] == 1
                   and audit["by_type"]["delete"] == 1 and audit["flip_flops"]
                   and audit["impossible_transitions"] and audit["timestamp_inconsistencies"]
                   and audit["snapshot_gaps"] == [] and "never_autocorrect" in audit["action"]))
    checks.append(("determinism: identical snapshots -> identical events",
                   json.dumps(reconstruct_change_events(snaps, "id"), sort_keys=True, default=str)
                   == json.dumps(events, sort_keys=True, default=str)))
    checks.append(("cards + boundary", all(c.get("serves_truth") is False for c in all_cards())))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - temporal_cdc_primitives: snapshots -> reconstructed CDC (honest snapshot-window "
          "precision) -> timelines across sources -> flip-flops / impossible transitions / timestamp "
          "inconsistencies / gaps / cross-source conflicts. Evidence for review, never silent correction. "
          "serves_truth=false.")
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
