#!/usr/bin/env python3
"""check_user_journey_tracker — proof: every registered user journey runs against the REAL demo backend and
emits a schema-valid, deterministic, REPLAYABLE UserJourneyTrace — the structured, governed complement to
the recorded demo videos (the video shows a journey; this proves + replays it). Asserts: schema conformance,
deterministic replay (same trace_hash), serves_truth=false, redaction, ordered steps, and — for the Baltor
flagship journey — that the moat (reconcile-by-authority, hold out the loser) and the receipt/lineage refs are
on the trace.

CLI: python3 scripts/check_user_journey_tracker.py --self-test
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from jsonschema import Draft202012Validator

from scripts.track_user_journey import _has_secret, all_journeys, track

_SCHEMA_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "schemas" / "UserJourneyTrace.schema.json"


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    ck("UserJourneyTrace is a valid JSON Schema", True)
    validator = Draft202012Validator(schema)
    registry = all_journeys()
    ck("the flagship Baltor journeys + ALL regulated-fact verticals are registered (>=15)",
       len(registry) >= 15 and sum(1 for j in registry if j.startswith("vertical-")) >= 12, str(len(registry)))

    for jid in sorted(registry):
        t = track(jid)
        ck(f"{jid}: trace conforms to UserJourneyTrace",
           validator.is_valid(t), str([e.message for e in validator.iter_errors(t)][:2]))
        ck(f"{jid}: REPLAYABLE — re-running yields the same trace_hash", track(jid)["trace_hash"] == t["trace_hash"])
        ck(f"{jid}: never serves truth", t["serves_truth"] is False)
        ck(f"{jid}: no secret material on the trace (redacted)", not _has_secret(t))
        ck(f"{jid}: steps are ordered 1..N", [s["step_no"] for s in t["steps"]] == list(range(1, len(t["steps"]) + 1)))

    b = track("baltor-context-assurance")
    ck("the Baltor journey HOLDS OUT a lower-authority claim (the moat, tracked on the journey)",
       any(s["surface"] == "reconciliation" and s["status"] == "held_out" for s in b["steps"]), str(b["steps"]))
    ck("the Baltor journey carries >=2 receipt/lineage evidence refs (provable journey)",
       sum(1 for s in b["steps"] if s.get("evidence_ref")) >= 2)
    ck("the Baltor journey ends on a portable receipt step",
       b["steps"][-1]["surface"] == "receipt" and bool(b["steps"][-1].get("evidence_ref")))

    print("\n" + ("PASS — check_user_journey_tracker: every registered journey runs the REAL demo backend into a "
                  "schema-valid, deterministic, REPLAYABLE UserJourneyTrace (same journey -> same trace_hash); "
                  "the Baltor journey tracks the moat (reconcile-by-authority + hold-out) and ends on a portable "
                  "receipt with lineage; traces are redacted and never serve truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
