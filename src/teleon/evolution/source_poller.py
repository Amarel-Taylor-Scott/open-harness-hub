"""src.teleon.evolution.source_poller — poll a REAL authoritative source, detect change, emit a genuine CDC event.

Closes the "live source fetch + CDC freshness" seam: today freshness uses PASSED-IN 'changed' events; this DETECTS change
from a live poll. poll_source() fetches the source (via an injected fetcher — real_federal_register_fetcher hits the live,
keyless US Federal Register), content-hashes it, compares to the last-seen hash recorded in the append-only cdc_events
stream (record_store, history tier), and appends a real {kind:'new'|'changed', source, content_hash, prior_hash,
fetched_at} event — the exact shape src.teleon.self_healing.reheal + freshness_runtime.on_source_change consume (a
'changed' event holds the prior answer out as stale until re-synced). Deterministic given the fetcher; network-gated +
honest offline. serves_truth=false (the source carries provenance); Teleon layer.
"""
from __future__ import annotations

import hashlib

from src.teleon.storage import record_store as RS

_STREAM = "cdc_events"


def content_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()[:16]


def _last_hash(source_id: str) -> str | None:
    st = RS.open_record_store(_STREAM)
    try:
        evs = [e for e in st.all() if e.get("source") == source_id]
        return evs[-1]["content_hash"] if evs else None
    finally:
        st.close()


def poll_source(source_id: str, fetcher, *, now: str) -> dict:
    """Fetch -> hash -> compare to the last recorded hash -> emit a real CDC event. Returns the event (kind: new |
    changed | unchanged). 'changed'/'new' are appended to cdc_events; 'unchanged' is not (no spurious events)."""
    text = fetcher()
    h = content_hash(text)
    prior = _last_hash(source_id)
    if prior == h:
        return {"kind": "unchanged", "source": source_id, "content_hash": h, "fetched_at": now}
    ev = {"event_hash": content_hash(f"{source_id}|{h}|{now}"), "kind": "new" if prior is None else "changed",
          "source": source_id, "content_hash": h, "prior_hash": prior, "fetched_at": now, "event_date": now[:10],
          "serves_truth": False}
    st = RS.open_record_store(_STREAM)
    try:
        st.append(ev, idem_key=ev["event_hash"])
    finally:
        st.close()
    return ev


def reheal_from_event(capability, event: dict, *, now: str) -> dict:
    """Feed a 'changed'/'new' CDC event into a freshness-tracked capability: hold the stale answer out until re-sync."""
    if event.get("kind") in ("changed", "new"):
        return capability.on_source_change({"kind": event["kind"], "source": event["source"]}, now=now)
    return {"held_out": False, "reason": "unchanged"}


def real_federal_register_fetcher(query: str = "consumer financial protection", *, limit: int = 3):
    """A live, keyless authoritative source (US Federal Register). Returns a stable text blob to hash. Network-gated."""
    from src.teleon.dag.real_steps import network_allowed, real_federal_register
    if not network_allowed():
        raise RuntimeError("network not allowed (OH_INFERENCE_ALLOW_NETWORK) — offline; pass a fetcher")
    docs = real_federal_register(query, limit=limit)
    return " | ".join(f"{d.get('title', '')}#{d.get('document_number', d.get('url', ''))}" for d in docs)
