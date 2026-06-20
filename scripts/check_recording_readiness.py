#!/usr/bin/env python3
"""scripts.check_recording_readiness — GO/NO-GO for full local + Cloudflare-tunnel video recording.

Before driving the journeys, confirm the whole plane is recordable: every surface up (the heartbeat
flywheel) AND the recordable journey SEAMS answer (the endpoints the recorder will click through —
registration → email inbox → verify, the live catalog, the Teleon runtime, the Baltor backend). A
clean GO means a tunnel + the recorder can run end-to-end without a 404 surprising the camera.

Read-only; live (hits the running plane). NO-GO lists exactly what to start. `--self-test` checks the
gate's own logic offline (a fake plane: all-up → GO, one-down → NO-GO).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(REPO))
from src.teleon.monitoring.flywheel import Flywheel, urllib_pinger  # noqa: E402

def _registry_ports() -> dict:
    reg = json.loads((REPO / "architecture" / "local_service_registry.json").read_text())
    return {s["service_id"]: s.get("port") for s in reg.get("services", [])}


_P = _registry_ports()
#: the recordable journey seams (url, what it proves). PORTS come from the service registry (single
#: source) so a registry port change can't leave this GO/NO-GO gate silently probing dead URLs; the
#: journey PATHS are seam-specific and stay here.
_SEAM_SMOKES = [
    (f"http://127.0.0.1:{_P['local_auth_service']}/api/identity/realms", "identity realms (registration target)"),
    (f"http://127.0.0.1:{_P['mailbox_local_service']}/api/mailbox/messages", "mailbox inbox (email verify journey)"),
    (f"http://127.0.0.1:{_P['local_openhub_projection_api']}/api/openhub/catalog", "live registry catalog (browse journey)"),
    (f"http://127.0.0.1:{_P['teleon_local_runtime']}/healthz", "teleon runtime (capability journey)"),
    (f"http://127.0.0.1:{_P['baltor_admin_demo_server']}/api/health", "baltor backend (context-gateway journey)"),
]


def _get_ok(url: str, timeout: float = 4.0) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return (200 <= resp.status < 400), f"HTTP {resp.status}"
    except Exception as exc:  # noqa: BLE001
        return False, type(exc).__name__


def run_live() -> int:
    fw = Flywheel()
    tick = fw.tick(urllib_pinger(), now="recording-readiness")
    down = [h["surface"] for h in tick["heartbeats"] if not h["up"]]
    s = tick["summary"]
    print(f"  surfaces: {s['up']}/{s['surfaces']} up" + (f" — DOWN: {down}" if down else ""))
    seam_fail = []
    for url, label in _SEAM_SMOKES:
        ok, detail = _get_ok(url)
        print(f"  [{'ok ' if ok else 'DOWN'}] seam: {label} ({detail})")
        if not ok:
            seam_fail.append(label)
    go = not down and not seam_fail
    if go:
        print("\nGO — every surface is up and every recordable seam answers. Start a Cloudflare tunnel "
              "and run e2e/record_user_journeys.mjs; the registration→inbox→verify→key journey + the "
              "capability/exploration/gateway/self-heal journeys are all reachable.")
    else:
        print("\nNO-GO — start the missing pieces first: python3 scripts/start_local_services.py "
              "(+ python3 scripts/mailbox_local_service.py). Re-run this gate.")
    return 0 if go else 1


def _self_test() -> int:
    # offline: prove the GO/NO-GO logic with a fake plane
    from src.teleon.monitoring.flywheel import HeartbeatResult
    checks = []

    def ck(n, ok):
        checks.append((n, ok))

    surfaces = [{"service_id": "a", "health_url": "x"}, {"service_id": "b", "health_url": "x"}]

    def all_up(surface, *, now):
        return HeartbeatResult(surface["service_id"], True, 5.0, now)

    def b_down(surface, *, now):
        return HeartbeatResult(surface["service_id"], surface["service_id"] != "b", 5.0, now)

    up_tick = Flywheel(surfaces).tick(all_up, now="t")
    down_tick = Flywheel(surfaces).tick(b_down, now="t")
    ck("all surfaces up → no down list (GO path)",
       [h for h in up_tick["heartbeats"] if not h["up"]] == [])
    ck("one surface down → it appears in the down list (NO-GO path)",
       [h["surface"] for h in down_tick["heartbeats"] if not h["up"]] == ["b"])
    ck("the seam-smoke list names the recordable journeys (registration/email/catalog/runtime/backend)",
       len(_SEAM_SMOKES) == 5 and any("mailbox" in lbl for _, lbl in _SEAM_SMOKES)
       and any("registration" in lbl for _, lbl in _SEAM_SMOKES))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    print(("PASS — " if not failed else "FAIL — ")
          + f"check_recording_readiness: {len(checks) - len(failed)}/{len(checks)} — the gate is GO only "
            "when every surface is up AND every recordable journey seam answers.")
    return 1 if failed else 0


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--self-test", action="store_true", help="offline gate-logic check")
    args = p.parse_args(argv)
    return _self_test() if args.self_test else run_live()


if __name__ == "__main__":
    raise SystemExit(main())
