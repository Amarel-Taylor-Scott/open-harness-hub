#!/usr/bin/env python3
"""scripts.check_observer_local_service — PROOF that the AIDevObserver backend exists and is WIRED
the way the other surfaces' backends are: a service-plane HTTP service over the EXISTING observer
engine (_repos/teleon/backend/src/teleon/observer), reached by the showcase through a same-origin seam.

It proves the pieces without binding a socket — it calls the service's own request handlers /
underlying functions directly over a SYNTHETIC transcript, then asserts the cross-cutting wiring
(the showcase seam + the service registry):

  A. ENGINE REUSE — review_report over a synthetic Claude-Code transcript (capture.from_transcript)
     AND inline messages returns the GOVERNED post-session report: serves_truth=false, ≥1 CANDIDATE
     finding, ranked by confidence; a missing transcript fails honestly (400, not a crash).
  B. LIVE — live_report (route_session) returns {surfaced, summary}; serves_truth=false; an unknown
     mode is rejected (400).
  C. SESSIONS — sessions_list tolerates a project with no transcripts → 200 with [].
  D. OUTCOMES — outcome_report appends metadata-only triage memory and outcomes_list folds latest-wins.
  E. LOCAL REGISTRY — registry_search is disabled by default and emits repo-relative candidate source refs when opted in.
  F. SEAM — _repos/shared-backend-components/scripts/showcase/server.py maps "/api/observer/" to the observer port (strip="", mirrors
     the teleon_runtime seam), so a same-origin /api/observer/review reaches the service.
  G. REGISTRY — _repos/shared-backend-components/architecture/local_service_registry.json declares observer_runtime on port 9431 with
     the --serve start_command, carries EVERY field the local-services health gate requires (so this
     addition can't break that gate), and is honestly active_local.

Offline, stdlib-only, no network, no socket. Synthetic/public session text only. Exit 0/1.
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# install() prepends every code root so BOTH `scripts.*` and the MOVED `src.teleon.*` resolve on a bare
# `python3 scripts/<f>.py` launch — not only under run_proofs/pytest (which set the full PYTHONPATH for us).
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_here_boot = _Path(__file__).resolve()
_sbc_boot = next((p for p in _here_boot.parents if (p / "scripts" / "_repo_paths.py").exists()), _here_boot.parents[1])
if str(_sbc_boot) not in _sys.path:
    _sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# the service under test (call its functions directly — no socket) ...
from scripts.observer_local_service import (SERVICE_ID, _LOCAL_REGISTRY_ENV, live_report, outcome_report,  # noqa: E402
                                            outcomes_list, registry_search, review_report, runtime_config,
                                            sessions_list)
# ... the showcase seam wiring ...
from scripts.showcase.server import (_local_service_port, _seam_base,  # noqa: E402
                                     _seam_for, _seam_proxies)
# ... and the local-services health gate's contract (single-sourced, not re-typed here)
from scripts.check_local_services_health import REQUIRED_FIELDS, VALID_STATUSES  # noqa: E402

REGISTRY_PATH = _resource("architecture") / "local_service_registry.json"
EXPECTED_PORT = 9431
# The registry stores the REPO-RELATIVE launcher path (portable — no machine-specific absolute in a
# checked-in JSON); the boot helper (local_services_lib._resolve_cmd) resolves it via _resource at spawn
# time after the _repos/ migration. So assert the relative stored form, matching every other file-form service.
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
    """Hermetic + fast wrapper: skip the heavyweight GLOBAL edge-foundry corpus enrichment (tens of thousands
    of cards, .gitignored on some checkouts) for the duration of this proof. Every assertion below exercises
    the service handlers, the LOCAL (opt-in) registry over a tiny synthetic repo, the showcase seam, and the
    service registry — none reads the global scan (§E's privacy assertion only requires that global-plane hits
    are NOT local_repo, which an empty global result trivially satisfies). Disabling it changes no verdict; it
    makes the proof deterministic regardless of whether the global corpus is present on disk and keeps it well
    under run_proofs' per-proof subprocess timeout (the scan otherwise runs on every review, ~75s). Restored
    afterward."""
    from src.teleon.observer.registry_search import set_global_primitives_enabled  # noqa: PLC0415
    set_global_primitives_enabled(False)
    try:
        return _run_self_test_body()
    finally:
        set_global_primitives_enabled(None)  # restore the default (no override) — hygiene for in-process callers


def _run_self_test_body() -> int:
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

        st_cfg, cfg = runtime_config()
        lane_keys = {lane.get("key") for lane in cfg.get("model_lanes", [])}
        ck("B: runtime config exposes deterministic/Kimi/GLM lanes",
           st_cfg == 200 and {"deterministic", "kimi", "glm"}.issubset(lane_keys)
           and cfg.get("serves_truth") is False)
        ck("B: runtime config exposes intelligence toggles",
           isinstance(cfg.get("toggles"), dict)
           and {"global_primitives", "local_registry", "mcp", "plugins", "token_savings"}.issubset(cfg["toggles"]))

        # ── C. SESSIONS — tolerates a project with no transcripts ───────────────────────────────
        st_sess, sess = sessions_list("/no/such/project/here")
        ck("C: sessions tolerates none → 200 with [] (serves_truth=false)",
           st_sess == 200 and sess.get("sessions") == [] and sess.get("serves_truth") is False)

        # ── D. OUTCOMES — append-only triage memory, metadata only ─────────────────────────────
        sid = "check_observer_local_service_outcome"
        iid = "iv_check_observer_local_service"
        source_ref_payload = {"existing": {"local_repo": [{
            "registry": "local_repo",
            "kind": "python_function",
            "path": "helpers.py",
            "name": "read_rows",
        }]}}
        st_out, out = outcome_report({
            "session_id": sid,
            "intervention_id": iid,
            "outcome": "dismissed",
            "type": "reinvention",
            "source_ref": source_ref_payload,
        })
        st_out2, _ = outcome_report({"session_id": sid, "intervention_id": iid, "outcome": "reused"})
        st_fold, folded = outcomes_list(sid)
        ck("D: outcome append stores metadata only and remains candidate-only",
           st_out == 200 and out.get("stored") == "outcome_metadata_only" and out.get("serves_truth") is False)
        ck("D: outcome append stores source-ref memory keys, not raw source text",
           st_out == 200 and len(out.get("source_ref_keys") or []) == 1 and "helpers.py" not in json.dumps(out))
        ck("D: outcomes latest-wins folds the append-only log",
           st_out2 == 200 and st_fold == 200 and folded.get("outcomes", {}).get(iid) == "reused")
        st_bad_out, _ = outcome_report({"session_id": sid, "intervention_id": iid, "outcome": "truth"})
        ck("D: invalid outcome is rejected", st_bad_out == 400)
        st_bad_sid, _ = outcome_report({"session_id": "../bad", "intervention_id": iid, "outcome": "reused"})
        ck("D: path-like outcome session id is rejected", st_bad_sid == 400)
        from src.teleon.observer import session_store
        session_store._path(sid).unlink(missing_ok=True)

        # ── E. LOCAL REGISTRY — opt-in source-ref search over repo-relative records ─────────────
        # This contract tests the PUBLIC-DEMO posture: default-off comes from the server-side mode
        # env (dev mode defaults ON); the explicit expose env below still overrides it for opt-in.
        from scripts._config import AIDEVOBSERVER_PUBLIC_DEMO_ENV  # noqa: E402
        prev_public_demo = os.environ.get(AIDEVOBSERVER_PUBLIC_DEMO_ENV)
        os.environ[AIDEVOBSERVER_PUBLIC_DEMO_ENV] = "1"
        st_reg_off, reg_off = registry_search("parse csv", str(tmp))
        ck("E: local registry search is disabled by default for public demos",
           st_reg_off == 200
           and reg_off.get("local_registry_enabled") is False
           # the privacy invariant: with local search off, NO hit may come from the local repo —
           # global planes (surfaceable/operational/edge-foundry/runtime-shape/benchmark) are fine.
           and all(
               (hit.get("source_ref") or {}).get("registry") != "local_repo"
               and ((hit.get("reuse_card") or {}).get("source_ref") or {}).get("registry") != "local_repo"
               for hit in reg_off.get("hits", [])
           ))
        st_enrich_off, enrich_off = review_report({
            "messages": [{"role": "user", "content": "I'll write a CSV parser from scratch"}],
            "registry_cwd": str(tmp),
        })
        ck("E: review enrichment is disabled by default for public demos",
           st_enrich_off == 200 and (enrich_off.get("local_registry") or {}).get("enabled") is False)
        repo_dir = tmp / "repo"
        repo_dir.mkdir()
        (repo_dir / "helpers.py").write_text(
            "MAX_ROWS = 250\n\n"
            "def read_rows(path: str) -> list[dict[str, str]]:\n"
            "    \"\"\"Read CSV rows with header handling.\"\"\"\n"
            "    return []\n",
            encoding="utf-8",
        )
        (repo_dir / "bad_helpers.py").write_text(
            "def parse_csv_bad(path: str) -> list[dict[str, str]]:\n"
            "    \"\"\"Old CSV parser candidate that reviewers dismissed.\"\"\"\n"
            "    return []\n",
            encoding="utf-8",
        )
        prev_registry = os.environ.get(_LOCAL_REGISTRY_ENV)
        os.environ[_LOCAL_REGISTRY_ENV] = "1"
        mem_sid = "check_observer_local_service_memory"
        mem_reuse = "iv_memory_reuse"
        mem_dismiss = "iv_memory_dismiss"
        try:
            st_reg, reg = registry_search("agent is creating parse_csv in importer.py", str(repo_dir))
            read_hit = next((h for h in reg.get("hits", []) if (h.get("source_ref") or {}).get("name") == "read_rows"), None)
            bad_hit = next((h for h in reg.get("hits", []) if (h.get("source_ref") or {}).get("name") == "parse_csv_bad"), None)
            if read_hit:
                outcome_report({
                    "session_id": mem_sid,
                    "intervention_id": mem_reuse,
                    "outcome": "reused",
                    "type": "reinvention",
                    "source_ref": {"existing": {"local_repo": [read_hit.get("source_ref")]}},
                })
            if bad_hit:
                outcome_report({
                    "session_id": mem_sid,
                    "intervention_id": mem_dismiss,
                    "outcome": "dismissed",
                    "type": "reinvention",
                    "source_ref": {"existing": {"local_repo": [bad_hit.get("source_ref")]}},
                })
            st_reg_mem, reg_mem = registry_search("agent is creating parse_csv in importer.py", str(repo_dir))
            st_enriched, enriched = review_report({
                "messages": [
                    {"role": "user", "content": "add a CSV import to the importer"},
                    {"role": "assistant", "content": "I'll write a CSV parser. Creating parse_csv() in importer.py"},
                ],
                "registry_cwd": str(repo_dir),
            })
        finally:
            if prev_registry is None:
                os.environ.pop(_LOCAL_REGISTRY_ENV, None)
            else:
                os.environ[_LOCAL_REGISTRY_ENV] = prev_registry
            if prev_public_demo is None:
                os.environ.pop(AIDEVOBSERVER_PUBLIC_DEMO_ENV, None)
            else:
                os.environ[AIDEVOBSERVER_PUBLIC_DEMO_ENV] = prev_public_demo
            session_store._path(mem_sid).unlink(missing_ok=True)
        reg_blob = json.dumps(reg, sort_keys=True)
        reg_mem_blob = json.dumps(reg_mem, sort_keys=True)
        enriched_blob = json.dumps(enriched, sort_keys=True)
        ck("E: opt-in local registry search finds an existing helper",
           st_reg == 200 and "read_rows" in reg_blob)
        ck("E: opt-in local registry search emits no absolute local path",
           str(repo_dir) not in reg_blob and tempfile.gettempdir() not in reg_blob)
        ck("E: local registry hits remain candidate-only",
           reg.get("serves_truth") is False
           and all(h.get("candidate") is True and h.get("serves_truth") is False for h in reg.get("hits", [])))
        ck("E: local registry hits include LLM-readable reuse cards with contracts",
           all(
               (h.get("reuse_card") or {}).get("kind") == "reuse_card"
               and (h.get("reuse_card") or {}).get("serves_truth") is False
               and isinstance((h.get("reuse_card") or {}).get("contract"), dict)
               and (h.get("reuse_card") or {}).get("contract", {}).get("input")
               and (h.get("reuse_card") or {}).get("contract", {}).get("output")
               for h in reg.get("hits", [])
           ),
           reg_blob)
        read_mem_hit = next((h for h in reg_mem.get("hits", []) if (h.get("source_ref") or {}).get("name") == "read_rows"), {})
        bad_mem_hit = next((h for h in reg_mem.get("hits", []) if (h.get("source_ref") or {}).get("name") == "parse_csv_bad"), {})
        ck("E: accepted/reused outcome memory boosts matching local source refs",
           st_reg_mem == 200 and (read_mem_hit.get("outcome_memory") or {}).get("score", 0) > 0,
           reg_mem_blob)
        ck("E: dismissed outcome memory suppresses matching local source refs",
           not bad_mem_hit or (bad_mem_hit.get("outcome_memory") or {}).get("score", 0) < 0,
           reg_mem_blob)
        ck("E: opt-in review enrichment attaches local helper source refs",
           st_enriched == 200 and "local_repo" in enriched_blob and "read_rows" in enriched_blob)
        enriched_cards = [
            card
            for finding in enriched.get("report", [])
            for card in finding.get("reuse_cards", [])
        ]
        enriched_local_cards = [
            card
            for card in enriched_cards
            if (card.get("source_ref") or {}).get("registry") == "local_repo"
        ]
        ck("E: opt-in review enrichment attaches reuse cards with input/output edges",
           bool(enriched_cards)
           and all(
               card.get("kind") == "reuse_card"
               and card.get("candidate") is True
               and card.get("serves_truth") is False
               and (card.get("contract") or {}).get("input")
               and (card.get("contract") or {}).get("output")
               for card in enriched_cards
           ),
           enriched_blob)
        ck("E: opt-in review enrichment still attaches local repo reuse cards",
           bool(enriched_local_cards), enriched_blob)
        ck("E: opt-in review enrichment carries outcome-memory signal when available",
           "outcome_memory" in enriched_blob, enriched_blob)
        ck("E: opt-in review enrichment emits no absolute local path",
           str(repo_dir) not in enriched_blob and tempfile.gettempdir() not in enriched_blob)
        ck("E: opt-in review enrichment stays candidate-only",
           enriched.get("serves_truth") is False and (enriched.get("local_registry") or {}).get("serves_truth") is False)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    # ── F. SEAM — the showcase maps /api/observer/ to the observer port (mirrors teleon) ─────────
    port = _local_service_port("observer_runtime")
    ck("F: the showcase can resolve the observer port from the registry", port == EXPECTED_PORT,
       str(port))
    seam = [(p, s, b) for (p, s, b) in _seam_proxies() if p == SEAM_PREFIX]
    ck("F: the showcase seam table contains '/api/observer/'", len(seam) == 1)
    ck("F: the seam mirrors teleon_runtime (strip empty, base → the observer plane)",
       bool(seam) and seam[0][1] == "" and seam[0][2] == _seam_base("OH_SEAM_OBSERVER_BASE", port))
    routed = _seam_for(SEAM_PREFIX + "review")
    ck("F: a same-origin /api/observer/review routes through the seam to the service",
       routed is not None and routed[0] == "" and (seam and routed[1] == seam[0][2]))

    # ── G. REGISTRY — observer_runtime declared, full-schema, honest ────────────────────────────
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entry = next((s for s in registry["services"] if s.get("service_id") == "observer_runtime"), None)
    ck("G: the registry declares observer_runtime", entry is not None)
    if entry:
        ck("G: on port 9431 with the --serve start_command",
           entry.get("port") == EXPECTED_PORT and entry.get("start_command") == EXPECTED_START)
        ck("G: it is honestly active_local", entry.get("status") in VALID_STATUSES
           and entry.get("status") == "active_local")
        missing = [f for f in REQUIRED_FIELDS if f not in entry]
        ck("G: it carries EVERY health-gate field (won't break check_local_services_health)",
           not missing, f"missing {missing}")
        ck("G: it declares the task's env + purpose", entry.get("env") == {}
           and "observer" in (entry.get("purpose") or "").lower())
        ck("G: its health_url targets /health on the observer port",
           entry.get("health_url") == f"http://127.0.0.1:{EXPECTED_PORT}/health")

    ok = not fails
    print("\n" + (f"PASS — check_observer_local_service ({checks} assertions): the AIDevObserver "
                  "backend is a service-plane HTTP service over the EXISTING observer engine "
                  "(review_session / route_session / from_transcript / discover_sessions) — review "
                  "returns a governed report (serves_truth=false, candidate findings, ranked) over a "
                  "synthetic transcript, live returns surfaced+summary, sessions tolerates none, and "
                  "outcome memory stores metadata only; local registry search is opt-in and emits "
                  "repo-relative candidate source refs; the "
                  "showcase seam '/api/observer/' (strip=\"\", mirrors teleon_runtime) reaches it, and "
                  "the registry's observer_runtime entry (port 9431, --serve) is full-schema + honest."
                  if ok else f"{len(fails)} of {checks} assertions FAILED: {fails}"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_observer_local_service.py --self-test")
    raise SystemExit(0)
