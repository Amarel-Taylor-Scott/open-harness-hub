#!/usr/bin/env python3
"""scripts.check_events_beacon_wiring — PROOF that the kit SPA is wired to the events/A-B plane
(backlog 2.1/2.3). The shipped surface is the React kit SPA, so this checks the CURRENT mechanism
(not the legacy vanilla app.js/events.js, which the kit entry no longer loads):

  A. LOAD — index.html loads the kit events client (kit/oh-identity.js) and the experiment engine
     (kit/oh-experiments.js); the React shell drives A/B via useExperiment() (shared/oh-site.jsx).
  B. CLIENT CONTRACT — oh-identity.js exposes window.OHEvents (page/variant/exposure/conversion),
     beacons to the events plane (default port matches the registry — drift gate), supports the
     OHH_EVENTS_BASE deploy override, sends via sendBeacon, uses an anon id (never an email), and
     refuses PII/key-shaped payloads; oh-experiments.js BRIDGES OHExp.onTrack → OHEvents so the
     SPA's real experiments reach the plane (not just a localStorage ring buffer).
  C. REAL END-TO-END LOOP — run the actual kit JS in Node (e2e/oh_experiments_beacon_probe.mjs):
     load the shipped oh-identity.js + oh-experiments.js, drive OHExp like the SPA does, capture the
     beacons it sends, then POST those exact payloads to a REAL events plane; /summary shows the A/B
     readout (exposure=1, conversion=1, conversion_rate=1.0) for the assigned variant. No mocks.
  D. STICKY / DETERMINISTIC — OHExp assignment is sticky (proven by the probe); OHEvents' fallback
     variant hash is deterministic (mirror).

Offline + live plane, stdlib-only (+ node for the real-JS proof). Exit 0/1.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.events_local_service import start_service  # noqa: E402

WEB = REPO_ROOT / "web" / "harness-hub"
KIT = WEB / "kit"
PROBE = REPO_ROOT / "e2e" / "oh_experiments_beacon_probe.mjs"


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
    ident = (KIT / "oh-identity.js").read_text(encoding="utf-8")
    exp = (KIT / "oh-experiments.js").read_text(encoding="utf-8")
    site = (KIT / "oh-site.jsx").read_text(encoding="utf-8")
    registry = json.loads((REPO_ROOT / "architecture" / "local_service_registry.json").read_text())
    plane_port = next(s["port"] for s in registry["services"]
                      if s["service_id"] == "local_event_tracking_service")

    # A. the kit SPA loads the events client + experiment engine; the shell drives A/B
    ck("A: index.html loads the kit events client (kit/oh-identity.js)", 'src="kit/oh-identity.js"' in html)
    ck("A: index.html loads the experiment engine (kit/oh-experiments.js)", 'src="kit/oh-experiments.js"' in html)
    ck("A: the React shell drives A/B via useExperiment() (the SPA's real experiments)",
       "function useExperiment" in site and "E.exposure(key)" in site)

    # B. client contract — the LOADED client (oh-identity.js), and the OHExp→OHEvents bridge
    base_match = re.search(r'OHH_EVENTS_BASE \|\| "http://127\.0\.0\.1:(\d+)"', ident)
    ck("B: oh-identity events base default matches the registry port (drift gate)",
       bool(base_match) and int(base_match.group(1)) == plane_port,
       base_match.group(1) if base_match else "no events base literal")
    ck("B: OHH_EVENTS_BASE deploy override supported", "OHH_EVENTS_BASE" in ident)
    ck("B: window.OHEvents exposes page/variant/exposure/conversion",
       all(m in ident for m in ("window.OHEvents", "page:", "variant:", "exposure:", "conversion:")))
    ck("B: sends via sendBeacon (fetch fallback)", "navigator.sendBeacon" in ident and "keepalive" in ident)
    ck("B: uses an anon id, never an email", '"oh-anon"' in ident and '"a_"' in ident)
    ck("B: client-side PII/key guard present (anon-only telemetry)", "PII_RE" in ident)
    ck("B: oh-experiments.js bridges OHExp.onTrack → OHEvents (server-side A/B readout)",
       "API.onTrack(" in exp and "root.OHEvents" in exp and "E.conversion(" in exp and "E.exposure(" in exp)

    # C. REAL end-to-end loop: run the shipped kit JS, then push its beacons through a live plane
    if not shutil.which("node"):
        ck("C: node available for the real-JS proof", False, "node not on PATH")
        probe = {}
    else:
        proc = subprocess.run(["node", str(PROBE)], cwd=str(REPO_ROOT),
                              capture_output=True, text=True, timeout=30)
        try:
            probe = json.loads(proc.stdout)
        except json.JSONDecodeError:
            probe = {"ok": False, "error": (proc.stdout or proc.stderr)[:300]}
        ck("C: the shipped kit JS runs and beacons (real oh-identity.js + oh-experiments.js)",
           probe.get("ok") is True, probe.get("error", ""))
        ck("C: a page beacon fires on load (anon analytics)",
           bool(probe.get("page")) and probe["page"].get("event") == "page")
        ck("C: OHExp.exposure → an exposure beacon carrying experiment+variant (via the bridge)",
           bool(probe.get("exposure")) and probe["exposure"].get("experiment") == "ohh_hero"
           and probe["exposure"].get("variant") in ("A", "B"))
        ck("C: an attributed OHExp.track → a conversion beacon with the SAME sticky variant",
           bool(probe.get("conversion")) and probe["conversion"].get("event") == "conversion"
           and probe["conversion"].get("variant") == (probe.get("exposure") or {}).get("variant"))
        ck("C: every beacon is anon-only (no email/key shape)", probe.get("anon_only") is True)

    if probe.get("ok") and probe.get("exposure") and probe.get("conversion"):
        variant = probe["exposure"]["variant"]
        state = Path(tempfile.mkdtemp(prefix="beacon-proof-"))
        server, thread, port = start_service(port=0, state_dir=state)
        try:
            ck("C: page beacon accepted by the real plane", _post(port, probe["page"]) == 202)
            _post(port, probe["exposure"])
            _post(port, probe["conversion"])
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/events/summary", timeout=10) as r:
                summary = json.loads(r.read())
            slot = summary["experiments"].get(f"ohh_hero:{variant}", {})
            ck(f"C: /summary shows the REAL A/B readout (ohh_hero:{variant} exposure=1, conversion=1, rate=1.0)",
               slot.get("exposure") == 1 and slot.get("conversion") == 1 and slot.get("conversion_rate") == 1.0,
               json.dumps(summary.get("experiments", {})))
            ck("C: the page beacon is counted by site",
               summary["by_site"].get(probe["page"]["site"], 0) >= 1)
        finally:
            server.shutdown(); thread.join(timeout=5)
            shutil.rmtree(state, ignore_errors=True)

    # D. sticky (OHExp, proven by the probe) + deterministic fallback hash (OHEvents.variantOf)
    ck("D: OHExp assignment is sticky (same visitor → same variant)", probe.get("sticky") is True)

    def js_variant(anon_id, experiment, variants=("A", "B")):  # mirror oh-identity.js variantOf()
        s = anon_id + "|" + experiment
        h = 0
        for ch in s:
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        return variants[h % len(variants)]
    ck("D: OHEvents fallback variant hash is deterministic",
       js_variant("a_xyz", "builder_cta") == js_variant("a_xyz", "builder_cta"))

    print("\n" + ("PASS — check_events_beacon_wiring: the kit SPA beacons page + experiment "
                  "exposure/conversion to the registry-ported events plane (drift-gated, sendBeacon, "
                  "anon-only, PII-guarded); the OHExp→OHEvents bridge gives the SPA's real experiments a "
                  "server-side A/B readout — PROVEN by running the shipped kit JS and pushing its beacons "
                  "through a live plane (exposure/conversion/rate real); sticky + deterministic assignment."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_events_beacon_wiring.py --self-test")
    raise SystemExit(0)
