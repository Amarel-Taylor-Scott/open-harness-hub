"""src.teleon.monitoring.flywheel — cross-surface heartbeats + the monitoring/resolution flywheel.

The loop: PING every surface → classify each (healthy / transient blip / persistent break, by
CONSECUTIVE failures across ticks) → PROPOSE a governed resolution (retry / restart / reheal /
escalate) → record → next tick. Resolutions are PROPOSED + recorded, never auto-executed for
destructive actions — the same discipline as self_healing (propose) and the exploration ladder
(escalate, don't auto-dispatch). A persistent SOURCE break routes to self_healing.reheal; a
persistent SERVICE break proposes a restart; an unresolvable one escalates to a human.

Pure + deterministic given an injected pinger + now (a real urllib pinger is provided for live use).
Heartbeats + proposals are governed records (governed_record: schema_version + is_truth + provenance
+ OTel trace). stdlib only; src/teleon only.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))  # direct-file run → repo importable
from src.teleon.io.governed_record import mint_record  # noqa: E402
SERVICE_REGISTRY = REPO / "architecture" / "local_service_registry.json"

STATUS_HEALTHY = "healthy"
STATUS_TRANSIENT = "transient"      # down for < PERSISTENT_AFTER consecutive ticks → a blip, retry/watch
STATUS_PERSISTENT = "persistent"    # down for >= PERSISTENT_AFTER → a real break, act

ACTION_NONE = "none"
ACTION_RETRY = "retry"              # transient → just re-check next tick
ACTION_RESTART = "propose_restart"  # a persistent SERVICE → propose a restart (recorded, not auto-run)
ACTION_REHEAL = "propose_reheal"    # a persistent SOURCE-backed capability → route to self_healing.reheal
ACTION_ESCALATE = "escalate_human"  # unresolvable / exhausted → a human (never auto-dispatched)

PERSISTENT_AFTER = 3                # consecutive failed heartbeats before a blip becomes a real break
ESCALATE_AFTER = 6                  # consecutive failures before even a restart-class break escalates
LATENCY_WARN_MS = 2000             # a heartbeat slower than this is degraded-but-up (recorded)

#: surface ids whose failure means a SOURCE/capability break → reheal, not a service restart.
_SOURCE_BACKED = ("teleon_local_runtime", "baltor_admin_demo_server")


@dataclass
class HeartbeatResult:
    surface: str
    up: bool
    latency_ms: float | None
    at: str
    detail: str = ""


@dataclass
class ResolutionProposal:
    surface: str
    status: str                     # healthy | transient | persistent
    consecutive_failures: int
    action: str                     # none | retry | propose_restart | propose_reheal | escalate_human
    auto_executed: bool = False     # ALWAYS False for destructive actions (proposed + recorded only)
    rationale: str = ""


def _surfaces(registry_path: Path = SERVICE_REGISTRY) -> list[dict]:
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    return [s for s in data["services"]
            if s.get("status") == "active_local" and s.get("health_url")]


def urllib_pinger(timeout: float = 3.0) -> Callable[[dict], HeartbeatResult]:
    """A REAL pinger: GET the surface's health_url, measure latency. Used live; the self-test injects
    a deterministic fake instead. (No clock dependency in the returned record — caller passes `now`.)"""
    def ping(surface: dict, *, now: str) -> HeartbeatResult:
        url = surface["health_url"]
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                ms = (time.monotonic() - t0) * 1000.0
                up = 200 <= resp.status < 400
                return HeartbeatResult(surface["service_id"], up, round(ms, 1), now,
                                       detail=f"HTTP {resp.status}")
        except Exception as exc:  # noqa: BLE001
            return HeartbeatResult(surface["service_id"], False, None, now, detail=f"{type(exc).__name__}")
    return ping


def classify_failure(consecutive_failures: int, surface_id: str) -> tuple[str, str, str]:
    """(status, action, rationale) from the consecutive-failure count — the resolution policy. Named
    thresholds; a SOURCE-backed surface routes to reheal, a service to a restart, exhaustion to human."""
    if consecutive_failures == 0:
        return STATUS_HEALTHY, ACTION_NONE, "up"
    if consecutive_failures < PERSISTENT_AFTER:
        return STATUS_TRANSIENT, ACTION_RETRY, f"down {consecutive_failures}x (< {PERSISTENT_AFTER}) — a blip, re-check"
    if consecutive_failures >= ESCALATE_AFTER:
        return STATUS_PERSISTENT, ACTION_ESCALATE, f"down {consecutive_failures}x (>= {ESCALATE_AFTER}) — exhausted, escalate to a human"
    if surface_id in _SOURCE_BACKED:
        return STATUS_PERSISTENT, ACTION_REHEAL, f"down {consecutive_failures}x — a source-backed capability break, route to self-heal"
    return STATUS_PERSISTENT, ACTION_RESTART, f"down {consecutive_failures}x — a persistent service break, propose a restart"


class Flywheel:
    """Holds per-surface consecutive-failure state across ticks; each tick() monitors + proposes."""

    def __init__(self, surfaces: list[dict] | None = None):
        self._surfaces = surfaces if surfaces is not None else _surfaces()
        self._consecutive: dict[str, int] = {}

    def tick(self, pinger: Callable[..., HeartbeatResult], *, now: str) -> dict:
        """One monitor→classify→propose pass. Returns {heartbeats, proposals, summary} as governed
        records — never executes a destructive action (proposes + records only)."""
        heartbeats, proposals = [], []
        for surface in self._surfaces:
            hb = pinger(surface, now=now)
            sid = hb.surface
            if hb.up:
                self._consecutive[sid] = 0
            else:
                self._consecutive[sid] = self._consecutive.get(sid, 0) + 1
            cf = self._consecutive[sid]
            status, action, rationale = classify_failure(cf, sid)
            # a degraded-but-up surface is recorded healthy with a latency note (not a failure)
            degraded = hb.up and hb.latency_ms is not None and hb.latency_ms > LATENCY_WARN_MS
            heartbeats.append(mint_record("SurfaceHeartbeat",
                {"surface": sid, "up": hb.up, "latency_ms": hb.latency_ms,
                 "degraded": degraded, "detail": hb.detail},
                produced_by="teleon.monitoring", created_at=now))
            if action != ACTION_NONE:
                proposals.append(mint_record("ResolutionProposal",
                    {"surface": sid, "status": status, "consecutive_failures": cf,
                     "action": action, "auto_executed": False, "rationale": rationale},
                    produced_by="teleon.monitoring", created_at=now))
        summary = {"surfaces": len(self._surfaces),
                   "up": sum(1 for h in heartbeats if h["up"]),
                   "proposals": len(proposals),
                   "escalations": sum(1 for p in proposals if p["action"] == ACTION_ESCALATE)}
        return {"heartbeats": heartbeats, "proposals": proposals, "summary": summary}


# ---------------------------------------------------------------- self-test (offline, deterministic)

def _self_test() -> int:
    checks = []

    def ck(n, ok):
        checks.append((n, ok))

    # _SOURCE_BACKED ids must exist as ACTIVE services in the registry — a rename there must fail
    # loudly here, not silently misroute a source/capability break to a generic restart.
    import json as _json
    _active = {s["service_id"] for s in _json.loads(SERVICE_REGISTRY.read_text())["services"]
               if str(s.get("status", "")).startswith("active")}
    ck("every _SOURCE_BACKED id is an active registry service (rename fails loudly)",
       all(sid in _active for sid in _SOURCE_BACKED))

    surfaces = [{"service_id": "identity", "health_url": "x"},
                {"service_id": "registry", "health_url": "x"},
                {"service_id": "teleon_local_runtime", "health_url": "x"},   # source-backed → reheal
                {"service_id": "events", "health_url": "x"}]

    # scripted world: identity always up; registry flaps then recovers; teleon persistently down;
    # events down long enough to exhaust → escalate
    plan = {
        "identity": [True, True, True, True, True, True, True],
        "registry": [False, False, True, True, True, True, True],   # 2 down (transient) → recovers
        "teleon_local_runtime": [False] * 7,                        # persistent → reheal (source-backed)
        "events": [False] * 7,                                      # persistent → restart → escalate
    }

    def fake_pinger_at(tick_i):
        def ping(surface, *, now):
            up = plan[surface["service_id"]][tick_i]
            return HeartbeatResult(surface["service_id"], up, 5.0 if up else None, now)
        return ping

    fw = Flywheel(surfaces)
    ticks = [fw.tick(fake_pinger_at(i), now=f"epoch:{i}") for i in range(7)]

    # tick 0: registry/teleon/events down (1x) → all transient/retry; identity healthy
    t0 = {p["surface"]: p for p in ticks[0]["proposals"]}
    ck("a single-tick failure is TRANSIENT (retry), not yet acted on",
       t0["registry"]["status"] == STATUS_TRANSIENT and t0["registry"]["action"] == ACTION_RETRY)
    ck("a healthy surface yields no proposal", "identity" not in t0)
    ck("every heartbeat + proposal is a governed record (schema_version + is_truth:false + provenance)",
       all(h["envelope"] == "GovernedRecord" and h["is_truth"] is False for h in ticks[0]["heartbeats"])
       and all(p["is_truth"] is False for p in ticks[0]["proposals"]))

    # tick 2: registry recovered (its 3rd ping is up) → no proposal; teleon now persistent (3x)
    t2 = {p["surface"]: p for p in ticks[2]["proposals"]}
    ck("a recovered surface clears (no proposal once it pings up)", "registry" not in t2)
    ck("a source-backed surface down >= PERSISTENT_AFTER → PROPOSE REHEAL (route to self-heal)",
       t2["teleon_local_runtime"]["status"] == STATUS_PERSISTENT
       and t2["teleon_local_runtime"]["action"] == ACTION_REHEAL)
    ck("a persistent SERVICE (not source-backed) → PROPOSE RESTART",
       t2["events"]["action"] == ACTION_RESTART)

    # tick 6: events down 7x (>= ESCALATE_AFTER=6) → escalate to a human
    t6 = {p["surface"]: p for p in ticks[6]["proposals"]}
    ck("an EXHAUSTED persistent failure (>= ESCALATE_AFTER) → ESCALATE to a human",
       t6["events"]["action"] == ACTION_ESCALATE)
    ck("NO resolution is ever auto-executed (proposed + recorded only — the destructive-action law)",
       all(p["auto_executed"] is False for tk in ticks for p in tk["proposals"]))
    ck("the tick summary counts up/proposals/escalations",
       ticks[6]["summary"]["up"] == 2 and ticks[6]["summary"]["escalations"] >= 1)

    # determinism
    fw2 = Flywheel(surfaces)
    ticks2 = [fw2.tick(fake_pinger_at(i), now=f"epoch:{i}") for i in range(7)]
    ck("deterministic: same world → same proposals",
       [p["action"] for p in ticks[6]["proposals"]] == [p["action"] for p in ticks2[6]["proposals"]])

    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    print(("PASS — " if not failed else "FAIL — ")
          + f"monitoring.flywheel: {len(checks) - len(failed)}/{len(checks)} — cross-surface heartbeats "
            "classify transient vs persistent failures and PROPOSE governed resolutions (retry/restart/"
            "reheal/escalate), never auto-executing a destructive action.")
    return 1 if failed else 0


def _live(now: str) -> int:
    """One REAL monitoring tick against the running plane (the registry's active surfaces). Prints
    heartbeats + any resolution proposals. Read-only — proposes, never acts."""
    fw = Flywheel()
    out = fw.tick(urllib_pinger(), now=now)
    for h in out["heartbeats"]:
        mark = "UP " if h["up"] else "DOWN"
        lat = f"{h['latency_ms']}ms" if h["latency_ms"] is not None else "-"
        deg = " (DEGRADED)" if h.get("degraded") else ""
        print(f"  [{mark}] {h['surface']:<32} {lat:>8}{deg}  {h['detail']}")
    for p in out["proposals"]:
        print(f"  → PROPOSE {p['action']} for {p['surface']} ({p['rationale']})")
    s = out["summary"]
    print(f"\n{s['up']}/{s['surfaces']} surfaces up · {s['proposals']} resolution proposal(s) · "
          f"{s['escalations']} escalation(s) — proposed only, nothing auto-executed")
    return 0


if __name__ == "__main__":
    if "--live" in sys.argv:
        # a fixed timestamp keeps the record deterministic; real wall-clock isn't needed for a heartbeat
        raise SystemExit(_live(now="live"))
    raise SystemExit(_self_test())
