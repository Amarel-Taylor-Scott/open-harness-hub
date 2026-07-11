"""src.teleon.evolution.freshness_runtime — the freshness / anti-fragility axis, END-TO-END on a regulated-fact
capability.

This is the wedge formal-proof systems concede (a proof is only as good as a possibly-stale encoded spec) and
gateways disclaim (no answer freshness). A FreshnessSyncedCapability binds a changing-fact capability to an
authoritative source on a volatility-matched cadence and enforces the rule: SERVE ONLY CURRENT FACTS. On a CDC
'changed' event (the shape src.teleon.self_healing.reheal_on_source_change consumes) the prior answer is marked
STALE and HELD OUT — never served — until the capability re-syncs to the new authoritative value. Composes
distill_robustness (the synced fork) + freshness_policy (cadence) + the fragile-context held-out statuses +
source-authority (which source is authoritative).

Pure + deterministic (timestamps passed in); Teleon-layer — never imports src.baltor; serving is a candidate/
evidence path, never autonomous truth (serves_truth False).
"""
from __future__ import annotations

from src.teleon.evolution.descent_axes import freshness_policy

#: held-out statuses from _repos/shared-backend-components/architecture/fragile_context_taxonomy.json — a stale answer is held out, never served.
STATUS_FRESH = "fresh"
STATUS_HELD_OUT_STALE = "held_out"   # a source change was detected; the prior answer is stale until re-synced
STATUS_UNSYNCED = "unsynced"


class FreshnessSyncedCapability:
    """A capability whose answer must stay current. ``sync`` ingests the current authoritative value; a CDC
    'changed' event holds the prior answer out (stale, never served) until the next ``sync``; ``serve`` returns the
    value ONLY when fresh, always with provenance."""

    def __init__(self, capability_slot: str, *, authoritative_source: str, volatility_class: str) -> None:
        if not capability_slot or not authoritative_source:
            raise ValueError("a freshness-synced capability needs a slot + an authoritative source")
        self.capability_slot = capability_slot
        self.authoritative_source = authoritative_source
        self.policy = freshness_policy(volatility_class)
        self._value = None
        self._version = None
        self._synced_at = None
        self._status = STATUS_UNSYNCED

    def _provenance(self) -> dict:
        return {"authoritative_source": self.authoritative_source, "source_version": self._version,
                "synced_at": self._synced_at, "sync_cadence": self.policy["sync_cadence"]}

    def sync(self, value, *, now: str, source_version: str) -> dict:
        """Ingest the CURRENT authoritative value (initial sync or re-sync after a change). Clears any held-out
        staleness."""
        self._value, self._version, self._synced_at, self._status = value, source_version, now, STATUS_FRESH
        return self.serve(now=now)

    def on_source_change(self, event: dict, *, now: str) -> dict:
        """A freshness CDC event ({kind:'changed'|'new', source:<id>, ...}) for this capability's source -> hold the
        prior answer out as STALE (never served) until re-synced. Mirrors the self_healing CDC trigger."""
        if str(event.get("source")) != self.authoritative_source:
            return {"capability_slot": self.capability_slot, "status": self._status,
                    "note": "event for a different source — ignored", "serves_truth": False}
        self._status = STATUS_HELD_OUT_STALE
        return {"capability_slot": self.capability_slot, "status": STATUS_HELD_OUT_STALE,
                "reason": "authoritative source changed; the prior answer is stale and HELD OUT until re-synced",
                "cdc_reheal": self.policy["cdc_reheal"], "served": None, "serves_truth": False}

    def serve(self, *, now: str) -> dict:
        """Return the value ONLY when fresh; a stale/unsynced capability serves NOTHING (held out) — never a stale
        regulated fact. Always carries provenance."""
        if self._status != STATUS_FRESH:
            return {"capability_slot": self.capability_slot, "status": self._status, "served": None, "value": None,
                    "provenance": self._provenance(), "serves_truth": False}
        return {"capability_slot": self.capability_slot, "status": STATUS_FRESH, "served": self._value,
                "value": self._value, "provenance": self._provenance(), "serves_truth": False}


def demonstrate_freshness_e2e(*, capability_slot: str = "reg-e-error-resolution-deadline",
                              authoritative_source: str = "ecfr://12/1005.11",
                              volatility_class: str = "low") -> dict:
    """Walk the freshness axis end-to-end on a regulated fact: sync the current value -> serve it (fresh) -> the
    rule CHANGES (CDC event) -> the stale answer is held out, never served -> re-sync to the new value -> serve the
    NEW current value. Returns the ordered trace."""
    cap = FreshnessSyncedCapability(capability_slot, authoritative_source=authoritative_source,
                                    volatility_class=volatility_class)
    trace = []
    trace.append(("initial_sync", cap.sync("10 business days", now="t0", source_version="2025-edition")))
    trace.append(("serve_fresh", cap.serve(now="t1")))
    trace.append(("source_changed", cap.on_source_change({"kind": "changed", "source": authoritative_source}, now="t2")))
    trace.append(("serve_while_stale", cap.serve(now="t3")))           # must serve NOTHING (held out)
    trace.append(("resync", cap.sync("12 business days", now="t4", source_version="2026-edition")))
    trace.append(("serve_fresh_again", cap.serve(now="t5")))
    return {"capability_slot": capability_slot, "authoritative_source": authoritative_source,
            "sync_cadence": cap.policy["sync_cadence"], "trace": trace, "serves_truth": False}
