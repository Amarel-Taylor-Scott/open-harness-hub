#!/usr/bin/env python3
"""scripts.context_memory_block — deterministic anti-drift "Memory Block" (reconcile a decision log).

Pattern adapted from `nidhinjs/prompt-master`'s "Memory Block" (see
`research/external-repos-brief-2026-06-04.md`) and expressed in Baltor's own terms: given a
time-ordered DECISION LOG, deterministically (NO LLM) reconcile to the CURRENT pinned state — later
supersedes earlier on the same key — and emit a compact "Memory Block" to prepend to a long session
so the model cannot contradict earlier decisions. This IS Baltor's reconcile/anti-fragile motion plus
the lineage invariant: **DIGESTIBLE FRONT** (the pinned current decisions) / **EXPANDABLE BACK**
(each entry carries the full chain of superseded decisions it replaced).

Deterministic + offline: input order IS the decision sequence (no wall-clock). Reuses
`scrapers.content_hash` for a stable identity (No-Magic-Values). Optional `bus=` emits onto the live
event bus (component.started → relationship.created per supersession edge → context_pack.created →
component.finished), byte-identical / non-breaking when omitted — the same contract as the other
connected engines.

CLI:
    python3 _repos/shared-backend-components/scripts/context_memory_block.py --self-test
"""
from __future__ import annotations

import argparse
import json
from typing import Any, Iterable, Mapping

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.foundry.scrapers import content_hash

#: Every decision record must carry at least these (single source for the contract).
REQUIRED_FIELDS = ("decision_id", "key")


def _canon(value: Any) -> str:
    """Canonical, order-stable serialization for comparison + hashing (handles dict/list values)."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _render_value(v: Any) -> str:
    return _canon(v) if isinstance(v, (dict, list)) else str(v)


def build_memory_block(decisions: Iterable[Mapping[str, Any]], *, bus=None) -> dict[str, Any]:
    """Reconcile a time-ordered decision log into a pinned Memory Block (current state + lineage).

    Each decision is a mapping: ``decision_id`` + ``key`` (required), optional ``value``,
    ``rationale``, ``source_handle``, and ``supersedes`` (a decision_id or list). The CURRENT decision
    for a key is the highest-sequence (latest) one; earlier decisions on that key become its
    expandable-back ``history``. Returns a dict with the digestible-front ``pinned`` map, ordered
    ``entries`` (each w/ history), ``superseded`` ids, ``revisions`` (value changes), a prependable
    ``block_text``, and a deterministic ``content_hash``.
    """
    decs = list(decisions)
    norm: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for i, d in enumerate(decs):
        if not isinstance(d, Mapping):
            raise ValueError(f"decision #{i} is not a mapping: {d!r}")
        for f in REQUIRED_FIELDS:
            if not d.get(f):
                raise ValueError(f"decision #{i} missing required field {f!r}")
        did = str(d["decision_id"])
        if did in seen_ids:
            raise ValueError(f"duplicate decision_id {did!r}")
        seen_ids.add(did)
        sup = d.get("supersedes") or []
        if isinstance(sup, str):
            sup = [sup]
        norm.append({
            "seq": i,
            "decision_id": did,
            "key": str(d["key"]),
            "value": d.get("value"),
            "rationale": d.get("rationale"),
            "source_handle": d.get("source_handle"),
            "supersedes": [str(s) for s in sup],
        })

    by_key: dict[str, list[dict]] = {}
    for n in norm:
        by_key.setdefault(n["key"], []).append(n)  # preserves seq order
    explicit_superseded = {s for n in norm for s in n["supersedes"]}

    entries: list[dict[str, Any]] = []
    pinned: dict[str, Any] = {}
    superseded_ids: list[str] = []
    revisions: list[dict[str, Any]] = []
    for key in sorted(by_key):
        chain = by_key[key]
        current = chain[-1]          # latest wins
        history = chain[:-1]         # expandable-back lineage
        pinned[key] = current["value"]
        for h in history:
            superseded_ids.append(h["decision_id"])
            if _canon(h["value"]) != _canon(current["value"]):
                revisions.append({"key": key, "from": h["value"], "to": current["value"],
                                  "from_id": h["decision_id"], "to_id": current["decision_id"]})
        entries.append({
            "key": key,
            "value": current["value"],
            "decision_id": current["decision_id"],
            "rationale": current["rationale"],
            "source_handle": current["source_handle"],
            "supersedes": current["supersedes"],
            "history": [h["decision_id"] for h in history],
        })
    # cross-key explicit supersessions not already captured by same-key chaining
    for s in sorted(explicit_superseded):
        if s in seen_ids and s not in superseded_ids:
            superseded_ids.append(s)
    superseded_ids = sorted(set(superseded_ids))

    block_lines = [f"## Pinned decisions (reconciled — {len(entries)} current, {len(superseded_ids)} superseded)"]
    for e in entries:
        sup = f" · supersedes {', '.join(e['history'])}" if e["history"] else ""
        block_lines.append(f"- {e['key']}: {_render_value(e['value'])}  [{e['decision_id']}{sup}]")
    block_text = "\n".join(block_lines)

    identity = "|".join(f"{e['key']}={_canon(e['value'])}@{e['decision_id']}" for e in entries)
    chash = content_hash(identity)

    result = {
        "pinned": pinned,
        "entries": entries,
        "superseded": superseded_ids,
        "revisions": revisions,
        "block_text": block_text,
        "content_hash": chash,
        "stats": {"decisions": len(norm), "current": len(entries),
                  "superseded": len(superseded_ids), "revisions": len(revisions)},
    }

    if bus is not None:  # live-bus emit — pure side-effect; byte-identical return when bus=None
        cid = "memblock-" + chash[:8]
        bus.publish("component.started", component="context_memory_block", stage="Reconciliation",
                    correlation_id=cid, payload={"decisions": len(norm)})
        for e in entries:
            for prior in e["history"]:
                bus.publish("relationship.created", component="context_memory_block", stage="Reconciliation",
                            correlation_id=cid, object_ref=e["decision_id"],
                            payload={"predicate": "supersedes", "object": prior, "key": e["key"]})
        bus.publish("context_pack.created", component="context_memory_block", stage="Consumption",
                    correlation_id=cid, object_ref=cid,
                    payload={"current": len(entries), "superseded": len(superseded_ids),
                             "content_hash": chash[:12]})
        bus.publish("component.finished", component="context_memory_block", stage="Reconciliation",
                    correlation_id=cid, payload={"current": len(entries)})
    return result


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    decisions = [
        {"decision_id": "d1", "key": "max_retries", "value": 3, "source_handle": "ctx://runbook#retry"},
        {"decision_id": "d2", "key": "owner", "value": "billing-team"},
        {"decision_id": "d3", "key": "max_retries", "value": 5, "supersedes": "d1",
         "rationale": "ADR-014 raised the ceiling", "source_handle": "ctx://adr-014#decision"},
    ]
    mb = build_memory_block(decisions)

    check("pinned reflects the LATEST decision (max_retries=5)", mb["pinned"]["max_retries"] == 5)
    check("unrelated decision retained (owner=billing-team)", mb["pinned"]["owner"] == "billing-team")
    check("superseded decision d1 recorded", "d1" in mb["superseded"])
    mr = next(e for e in mb["entries"] if e["key"] == "max_retries")
    check("entry carries expandable-back history [d1]", mr["history"] == ["d1"])
    check("current entry keeps its source_handle (lineage)", mr["source_handle"] == "ctx://adr-014#decision")
    check("revision recorded 3→5", any(r["from"] == 3 and r["to"] == 5 for r in mb["revisions"]))
    check("block_text pins 5, not 3", "max_retries: 5" in mb["block_text"] and "max_retries: 3" not in mb["block_text"])

    mb2 = build_memory_block(decisions)
    check("deterministic content_hash (sha256)", mb["content_hash"] == mb2["content_hash"] and len(mb["content_hash"]) == 64)
    check("byte-identical re-run", mb == mb2)

    # validation contract
    for bad, why in [([{"key": "k"}], "missing decision_id"),
                     ([{"decision_id": "x"}], "missing key"),
                     ([{"decision_id": "a", "key": "k"}, {"decision_id": "a", "key": "k2"}], "duplicate decision_id"),
                     (["not-a-map"], "non-mapping decision")]:
        try:
            build_memory_block(bad)
            ok = False
        except ValueError:
            ok = True
        check(f"rejects {why}", ok)

    # bus emit (optional, non-breaking)
    from scripts.context_events import EventBus
    bus = EventBus()
    seen: list[dict] = []
    bus.subscribe(seen.append)
    mb_bus = build_memory_block(decisions, bus=bus)
    kinds = [e["kind"] for e in seen]
    check("bus: first started, last finished", bool(kinds) and kinds[0] == "component.started" and kinds[-1] == "component.finished")
    check("bus: supersession edge emitted (d3 supersedes d1)",
          any(e["kind"] == "relationship.created" and e["object_ref"] == "d3"
              and e["payload"].get("object") == "d1" and e["payload"].get("predicate") == "supersedes" for e in seen))
    check("bus: context_pack.created (the memory block)", "context_pack.created" in kinds)
    check("bus vs no-bus return is IDENTICAL (events are side-effects only)", mb_bus == mb)

    print(f"\n{'all context_memory_block self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Deterministic anti-drift Memory Block (reconcile a decision log).")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
