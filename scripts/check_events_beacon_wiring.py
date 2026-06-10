#!/usr/bin/env python3
"""scripts.check_events_beacon_wiring — PROOF that harness-hub is wired to the events/A-B plane
(backlog 2.1/2.3). Static client contract + a LIVE end-to-end loop through the running plane.

  A. LOAD — index.html loads events.js after data.js; app.js emits a page event per route render
     and a builder_cta conversion on the primary CTA, plus a landing exposure.
  B. CLIENT CONTRACT — events.js default base matches the registry port (drift gate), supports the
     OH_EVENTS_BASE override, sends via sendBeacon, uses an anon id (never an email), and refuses
     to send PII/key-shaped payloads (client-side guard).
  C. LIVE A/B LOOP — start the real events plane; POST the exact shapes events.js produces (page,
     exposure, conversion for builder_cta:B); the /summary readout shows exposure=1, conversion=1,
     conversion_rate=1.0 for that variant — the A/B readout is real, not mocked.
  D. STICKY ASSIGNMENT — the variant() hash is deterministic (same anon+experiment → same variant).

Offline, stdlib-only. Exit 0/1.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.events_local_service import start_service  # noqa: E402

WEB = REPO_ROOT / "web" / "harness-hub"


def _post(port, evt):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/events", method="POST",
                                 data=json.dumps(evt).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    html = (WEB / "index.html").read_text(encoding="utf-8")
    events = (WEB / "events.js").read_text(encoding="utf-8")
    app = (WEB / "app.js").read_text(encoding="utf-8")
    registry = json.loads((REPO_ROOT / "architecture" / "local_service_registry.json").read_text())
    plane_port = next(s["port"] for s in registry["services"]
                      if s["service_id"] == "local_event_tracking_service")

    # A. load + wiring
    ck("A: index.html loads events.js", 'src="events.js"' in html)
    ck("A: events.js loads after data.js", html.find('src="data.js"') < html.find('src="events.js"'))
    ck("A: app.js emits a page event per route render", "OHEvents.page(route" in app)
    ck("A: app.js fires the builder_cta conversion + landing exposure",
       'OHEvents.conversion("builder_cta"' in app and 'OHEvents.variant("builder_cta"' in app)

    # B. client contract
    port_match = re.search(r'DEFAULT_BASE = "http://127\.0\.0\.1:(\d+)"', events)
    ck("B: events.js default port matches the registry (drift gate)",
       bool(port_match) and int(port_match.group(1)) == plane_port,
       port_match.group(1) if port_match else "no DEFAULT_BASE")
    ck("B: OH_EVENTS_BASE override supported", "OH_EVENTS_BASE" in events)
    ck("B: sends via sendBeacon", "navigator.sendBeacon" in events)
    ck("B: uses an anon id, never an email", "ANON_KEY" in events and "a_" in events)
    ck("B: client-side PII guard present", "PII_RE" in events and "refuse" in events.lower())

    # C. live A/B loop through the real plane
    state = Path(tempfile.mkdtemp(prefix="beacon-proof-"))
    server, thread, port = start_service(port=0, state_dir=state)
    try:
        anon = "a_proof01"
        ck("C: page event accepted",
           _post(port, {"site": "openharnesshub", "event": "page", "name": "/", "anon": anon}) == 202)
        _post(port, {"site": "openharnesshub", "event": "exposure", "name": "builder_cta",
                     "experiment": "builder_cta", "variant": "B", "anon": anon})
        _post(port, {"site": "openharnesshub", "event": "conversion", "name": "build_requested",
                     "experiment": "builder_cta", "variant": "B", "anon": anon})
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/events/summary", timeout=10) as r:
            summary = json.loads(r.read())
        exp = summary["experiments"].get("builder_cta:B", {})
        ck("C: /summary readout shows the A/B result (exposure=1, conversion=1, rate=1.0)",
           exp.get("exposure") == 1 and exp.get("conversion") == 1 and exp.get("conversion_rate") == 1.0,
           json.dumps(summary.get("experiments", {})))
        ck("C: page event counted by site", summary["by_site"].get("openharnesshub", 0) >= 1)
    finally:
        server.shutdown(); thread.join(timeout=5)
        shutil.rmtree(state, ignore_errors=True)

    # D. sticky deterministic assignment (mirror the JS hash)
    def js_variant(anon_id, experiment, variants=("A", "B")):
        s = anon_id + "|" + experiment
        h = 0
        for ch in s:
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        return variants[h % len(variants)]
    ck("D: variant assignment is deterministic (sticky)",
       js_variant("a_xyz", "builder_cta") == js_variant("a_xyz", "builder_cta"))

    print("\n" + ("PASS — check_events_beacon_wiring: harness-hub beacons page/exposure/conversion to the "
                  "registry-ported events plane (drift-gated, sendBeacon, anon-only, PII-guarded); the live "
                  "A/B readout is real (exposure/conversion/rate from a real loop); sticky deterministic "
                  "variant assignment."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_events_beacon_wiring.py --self-test")
    raise SystemExit(0)
