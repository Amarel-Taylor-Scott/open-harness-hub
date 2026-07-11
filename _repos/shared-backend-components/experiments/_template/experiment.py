#!/usr/bin/env python3
"""Skunkworks experiment TEMPLATE — copy this directory to start a new experiment.

Rules (see ../README.md): experiments may be messy/unproven and may use network; they MUST NOT be
imported by any proven scripts/ module (the flywheel forbids it, enforced by
scripts/check_experiments_isolation.py). They MAY import scripts/* and emit onto the shared event
bus so they show LIVE on /dashboard. Graduate a winner into scripts/ with a --self-test.
"""
from __future__ import annotations

import os
import sys

_RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _RR not in sys.path:  # so experiments can import the core
    sys.path.insert(0, _RR)

from scripts.context_events import EventBus


def run(bus=None) -> dict:
    """Your idea goes here. Emit onto `bus` to show up live on the dashboard."""
    own = bus is None
    bus = bus or EventBus()
    seen: list[dict] = []
    if own:
        bus.subscribe(seen.append)

    bus.publish("component.started", component="experiment:_template", stage="Source Systems",
                payload={"hello": "skunkworks"})
    # ── try the new thing here (call scripts/* engines, fetch data, prototype) ──
    bus.publish("component.progressed", component="experiment:_template", payload={"step": "doing the thing"})
    bus.publish("component.finished", component="experiment:_template", payload={"result": "ok"})

    return {"emitted": [e["kind"] for e in seen] if own else "published to shared bus"}


if __name__ == "__main__":
    print(run())
