#!/usr/bin/env python3
"""scripts.check_observer_local_service — PROOF that the AIDevObserver backend exists and is WIRED
the way the other surfaces' backends are: a service-plane HTTP service over the EXISTING observer
engine (src/teleon/observer), reached by the showcase through a same-origin seam.

It proves the pieces without binding a socket — it calls the service's own request handlers /
underlying functions directly over a SYNTHETIC transcript, then asserts the cross-cutting wiring
(the showcase seam + the service registry):

  A. ENGINE REUSE — review_report over a synthetic Claude-Code transcript (capture.from_transcript)
     AND inline messages returns the GOVERNED post-session report: serves_truth=false, ≥1 CANDIDATE
     finding, ranked by confidence; a missing transcript fails honestly (400, not a crash).
  B. LIVE — live_report (route_session) returns {surfaced, summary}; serves_truth=false; an unknown
     mode is rejected (400).
  C. SESSIONS — sessions_list tolerates a project with no transcripts → 200 with [].
  D. SEAM — scripts/showcase/server.py maps "/api/observer/" to the observer port (strip="", mirrors
     the teleon_runtime seam), so a same-origin /api/observer/review reaches the service.
  E. REGISTRY — architecture/local_service_registry.json declares observer_runtime on port 9431 with
     the --serve start_command, carries EVERY field the local-services health gate requires (so this
     addition can't break that gate), and is honestly active_local.

Offline, stdlib-only, no network, no socket. Synthetic/public session text only. Exit 0/1.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# the service under test (call its functions directly — no socket) ...
from scripts.observer_local_service import (SERVICE_ID, live_report,  # noqa: E402
                                            review_report, sessions_list)
# ... the showcase seam wiring ...
from scripts.showcase.server import (_local_service_port, _seam_base,  # noqa: E402
                                     _seam_for, _seam_proxies)
# ... and the local-services health gate's contract (single-sourced, not re-typed here)
from scripts.check_local_services_health import REQUIRED_FIELDS, VALID_STATUSES  # noqa: E402

REGISTRY_PATH = REPO_ROOT / "architecture" / "local_service_registry.json"
EXPECTED_PORT = 9431
EXPECTED_START = ["python3", "scripts/observer_local_service.py", "--serve"]
SEAM_PREFIX = "/api/observer/"

# A synthetic Claude-Code JSONL transcript (NO real PII): a grounded reinvention (pdf parser) + a
# destructive-command footgun (force-push) → the engine must surface governed candidate findings.
SYNTHETIC_TRANSCRIPT = [
    {"type": "user", "message": {"role": "user", "content": "let me write my own pdf parser from scratch"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": "ok, getting started"},
        {"type": "tool_use", "name": "Bash", "input": {"command": "git push --force origin main"}}]}},
]
SYNTHETIC_MESSAGES = [
    {"role": "user", "content": "let me write my own pdf parser from scratch"},
    {"role": "assistant", "content": "then run: git push --force origin main"},
]


def _self_test() -> int:
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── A. ENGINE REUSE — governed review over a synthetic transcript + inline messages ──────────
    tmp = Path(tempfile.mkdtemp(prefix="observer-proof-"))
    try:
        tpath = tmp / "session.jsonl"
        tpath.write_text("\n".join(json.dumps(r) for r in SYNTHETIC_TRANSCRIPT) + "\n", encoding="utf-8")

        st, rep = review_report({"transcript_path": str(tpath)})
        report = rep.get("report", [])
        ck("A: review over a synthetic transcript → 200", st == 200)
        ck("A: the report is GOVERNED (serves_truth=false)", rep.get("serves_truth") is False)
        ck("A: it surfaces ≥1 finding from the transcript", len(report) >= 1, f"{len(report)} findings")
        ck("A: every finding is a governed CANDIDATE (serves_truth=false, candidate=true, scored)",
           all(f.get("candidate") is True and f.get("serves_truth") is False
               and "confidence" in f and f.get("type") and "suggestion" in f for f in report))
        ck("A: the report is ranked by confidence (desc)",
           all(report[i]["confidence"] >= report[i + 1]["confidence"] for i in range(len(report) - 1)))
        ck("A: the response is stamped with the service id", rep.get("service") == SERVICE_ID)

        st_inline, rep_inline = review_report({"messages": SYNTHETIC_MESSAGES})
        ck("A: review over inline messages → 200 governed report",
           st_inline == 200 and rep_inline.get("serves_truth") is False
           and len(rep_inline.get("report", [])) >= 1)

        st_miss, body_miss = review_report({"transcript_path": str(tmp / "absent.jsonl")})
        ck("A: a missing transcript fails honestly (400, not a crash)",
           st_miss == 400 and "error" in body_miss and body_miss.get("serves_truth") is False)
        st_empty, _ = review_report({})
        ck("A: a body with neither messages nor transcript → 400", st_empty == 400)

        # ── B. LIVE — route_session → surfaced + summary ────────────────────────────────────────
        st_live, live = live_report({"messages": SYNTHETIC_MESSAGES, "mode": "advisory"})
        ck("B: live → 200 with surfaced + summary (serves_truth=false)",
           st_live == 200 and isinstance(live.get("surfaced"), list)
           and isinstance(live.get("summary"), dict) and live.get("serves_truth") is False)
        ck("B: the live summary carries the engine's finding counts",
           "findings" in live.get("summary", {}) and "by_type" in live.get("summary", {}))
        st_defmode, _ = live_report({"messages": SYNTHETIC_MESSAGES})   # default mode = advisory
        ck("B: live defaults its mode (no mode supplied) → 200", st_defmode == 200)
        st_badmode, _ = live_report({"messages": SYNTHETIC_MESSAGES, "mode": "nope"})
        ck("B: an unknown live mode is rejected (400)", st_badmode == 400)

        # ── C. SESSIONS — tolerates a project with no transcripts ───────────────────────────────
        st_sess, sess = sessions_list("/no/such/project/here")
        ck("C: sessions tolerates none → 200 with [] (serves_truth=false)",
           st_sess == 200 and sess.get("sessions") == [] and sess.get("serves_truth") is False)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    # ── D. SEAM — the showcase maps /api/observer/ to the observer port (mirrors teleon) ─────────
    port = _local_service_port("observer_runtime")
    ck("D: the showcase can resolve the observer port from the registry", port == EXPECTED_PORT,
       str(port))
    seam = [(p, s, b) for (p, s, b) in _seam_proxies() if p == SEAM_PREFIX]
    ck("D: the showcase seam table contains '/api/observer/'", len(seam) == 1)
    ck("D: the seam mirrors teleon_runtime (strip empty, base → the observer plane)",
       bool(seam) and seam[0][1] == "" and seam[0][2] == _seam_base("OH_SEAM_OBSERVER_BASE", port))
    routed = _seam_for(SEAM_PREFIX + "review")
    ck("D: a same-origin /api/observer/review routes through the seam to the service",
       routed is not None and routed[0] == "" and (seam and routed[1] == seam[0][2]))

    # ── E. REGISTRY — observer_runtime declared, full-schema, honest ────────────────────────────
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entry = next((s for s in registry["services"] if s.get("service_id") == "observer_runtime"), None)
    ck("E: the registry declares observer_runtime", entry is not None)
    if entry:
        ck("E: on port 9431 with the --serve start_command",
           entry.get("port") == EXPECTED_PORT and entry.get("start_command") == EXPECTED_START)
        ck("E: it is honestly active_local", entry.get("status") in VALID_STATUSES
           and entry.get("status") == "active_local")
        missing = [f for f in REQUIRED_FIELDS if f not in entry]
        ck("E: it carries EVERY health-gate field (won't break check_local_services_health)",
           not missing, f"missing {missing}")
        ck("E: it declares the task's env + purpose", entry.get("env") == {}
           and "observer" in (entry.get("purpose") or "").lower())
        ck("E: its health_url targets /health on the observer port",
           entry.get("health_url") == f"http://127.0.0.1:{EXPECTED_PORT}/health")

    ok = not fails
    print("\n" + (f"PASS — check_observer_local_service ({checks} assertions): the AIDevObserver "
                  "backend is a service-plane HTTP service over the EXISTING observer engine "
                  "(review_session / route_session / from_transcript / discover_sessions) — review "
                  "returns a governed report (serves_truth=false, candidate findings, ranked) over a "
                  "synthetic transcript, live returns surfaced+summary, sessions tolerates none; the "
                  "showcase seam '/api/observer/' (strip=\"\", mirrors teleon_runtime) reaches it, and "
                  "the registry's observer_runtime entry (port 9431, --serve) is full-schema + honest."
                  if ok else f"{len(fails)} of {checks} assertions FAILED: {fails}"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_observer_local_service.py --self-test")
    raise SystemExit(0)
