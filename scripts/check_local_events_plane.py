#!/usr/bin/env python3
"""scripts.check_local_events_plane — PROOF for scripts/events_local_service.py (the native
events/A-B plane; EVENTS.md contract recreated in repo patterns — reference Node core stays
reference). Asserts: Cloud-Run-like endpoints answer; single + batch ingest; summary counts by
site/type/experiment:variant with conversion_rate; PII/key-shaped events REJECTED and never
stored; restart-safe persistence; the service's port comes from the local service registry
(drift gate); the plane declares itself non-truth. Offline, stdlib-only. Exit 0/1."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.events_local_service import SERVICE_ID, _registry_port, start_service  # noqa: E402


def _call(port, method, path, body=None):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = json.loads((REPO_ROOT / "architecture" / "local_service_registry.json").read_text())
    entry = next(s for s in reg["services"] if s["service_id"] == SERVICE_ID)
    ck("A: service port single-sourced from the registry", _registry_port() == entry["port"])

    state = Path(tempfile.mkdtemp(prefix="events-proof-"))
    server, thread, port = start_service(port=0, state_dir=state)
    try:
        ck("B: healthz answers", _call(port, "GET", "/healthz")[1].get("ok") is True)
        ck("B: readyz/version/status answer",
           _call(port, "GET", "/readyz")[0] == 200 and _call(port, "GET", "/version")[0] == 200
           and _call(port, "GET", "/api/status")[1].get("truth_authority") is False)
        st, out = _call(port, "POST", "/api/events",
                        {"site": "baltor", "event": "page", "name": "landing", "anon": "a_1f"})
        ck("C: single event accepted (202)", st == 202 and out["accepted"] == 1)
        st, out = _call(port, "POST", "/api/events", {"events": [
            {"site": "baltor", "event": "exposure", "name": "hero", "experiment": "hero_copy",
             "variant": "B", "anon": "a_1f"},
            {"site": "baltor", "event": "conversion", "name": "cta", "experiment": "hero_copy",
             "variant": "B", "anon": "a_1f"}]})
        ck("C: batch exposure+conversion accepted", st == 202 and out["accepted"] == 2)
        st, summary = _call(port, "GET", "/api/events/summary")
        exp = summary["experiments"].get("hero_copy:B", {})
        ck("C: summary counts by site/type/variant with conversion_rate",
           summary["total"] == 3 and summary["by_site"].get("baltor") == 3
           and exp.get("exposure") == 1 and exp.get("conversion") == 1
           and exp.get("conversion_rate") == 1.0, json.dumps(summary)[:160])
        st, out = _call(port, "POST", "/api/events",
                        {"site": "baltor", "event": "page", "name": "x", "anon": "ada@example.com"})
        ck("D: email-shaped anon REJECTED (400, PII guard)", st == 400)
        ck("D: rejected event never stored",
           "ada@example.com" not in (state / "events.jsonl").read_text(encoding="utf-8"))
        server.shutdown(); thread.join(timeout=5)
        server, thread, port = start_service(port=0, state_dir=state)
        ck("E: counters rebuild from JSONL after restart",
           _call(port, "GET", "/api/events/summary")[1]["total"] == 3)
    finally:
        server.shutdown(); thread.join(timeout=5)
        shutil.rmtree(state, ignore_errors=True)

    print("\n" + ("PASS — check_local_events_plane: registry-ported native events/A-B plane — ingest "
                  "(single/batch), per-variant summary with conversion_rate, PII-guarded (rejected events "
                  "never stored), restart-safe, non-truth by declaration."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_local_events_plane.py --self-test")
    raise SystemExit(0)
