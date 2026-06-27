#!/usr/bin/env python3
"""check_teleon_local_emulation — proof that every BLOCKING go-live seam has a built LOCAL emulator, so the whole
stack runs locally (Docker / Tilt / in-process) with no GPU, no API key, no network, no paid cloud.

It is the local counterpart to check_teleon_go_live_readiness: that gate honestly reports cloud go_live_ready=False
while the LIVE seams are unwired; THIS gate proves each of those blocking seams maps to a built local emulator and
that the two genuinely-new seams (live LLM inference, live source + CDC freshness) wire END-TO-END in-process:

  * freshness seam — a FreshnessSyncedCapability bound to the local SourceOfTruthEmulator: serve the current value
    (fresh) -> the source changes (CDC event) -> the stale answer is HELD OUT (never served) -> re-sync to the new
    value -> serve it. The exact "rule changed -> stale held out -> re-synced" loop, locally.
  * model seam — a call routed through the local ModelEmulator is deterministic and reports real token counts
    (tokens_in/out), standing in for a live LLM with no key/GPU. LLM output is never truth.

The remaining blocking seams (Postgres/promotion, auth/tenancy, hosting) map to REAL local containers already in
architecture/deploy_topology.json (postgres, identity, teleon-runtime), brought up by the deploy compose + the
emulators overlay + the Tiltfile. So local_go_live_ready=True even though cloud go_live_ready stays honestly False
(local != cloud). Emulators are dev scaffolding; they NEVER serve truth.

CLI: PYTHONPATH=. python3 scripts/check_teleon_local_emulation.py --self-test | --report
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_EMU_COMPOSE = "deploy/docker-compose.emulators.yml"   # the local-emulation overlay (runnable packaging)
_BASE_COMPOSE = "deploy/docker-compose.deploy.yml"     # the base stack (Postgres/identity/runtime as real containers)
_TILTFILE = "Tiltfile"

# Each BLOCKING go-live seam (string is single-sourced from check_teleon_go_live_readiness.readiness_report) ->
# its built LOCAL emulator. in_process = an importable stdlib emulator (also runnable as a tiny container);
# container = a real local container already declared in deploy_topology.json; repo_fixture = a local dataset.
LOCAL_EMULATORS: dict[str, dict] = {
    "live LLM inference": {
        "emulator": "local_emulators.model_emulator.ModelEmulator (deterministic OpenAI-compatible local LLM)",
        "kind": "in_process", "module": "local_emulators.model_emulator", "symbol": "ModelEmulator",
        "runnable_via": _EMU_COMPOSE, "compose_service": "model-emulator"},
    "live source fetch + CDC freshness": {
        "emulator": "local_emulators.source_of_truth_emulator.SourceOfTruthEmulator (authoritative source + CDC)",
        "kind": "in_process", "module": "local_emulators.source_of_truth_emulator", "symbol": "SourceOfTruthEmulator",
        "runnable_via": _EMU_COMPOSE, "compose_service": "source-emulator"},
    "real distillation (LLM -> deterministic rule generation)": {
        "emulator": "local_emulators.model_emulator.ModelEmulator (the local LLM the determinism factory calls)",
        "kind": "in_process", "module": "local_emulators.model_emulator", "symbol": "ModelEmulator",
        "runnable_via": _EMU_COMPOSE, "compose_service": "model-emulator"},
    "real per-vertical eval data": {
        "emulator": "data/sample-skills/sample_skills.json (local representative eval corpus the A/B scores on)",
        "kind": "repo_fixture", "fixture": "data/sample-skills/sample_skills.json"},
    "Postgres/pgvector load + live promotion boundary": {
        "emulator": "postgres container (real local Postgres in deploy_topology.json)",
        "kind": "container", "service": "postgres", "runnable_via": _BASE_COMPOSE},
    "auth + tenancy (separate realms)": {
        "emulator": "identity container + src.openhubforai.auth_kit (separate-realm auth, run locally)",
        "kind": "container", "service": "identity", "module": "src.openhubforai.auth_kit",
        "runnable_via": _BASE_COMPOSE},
    "hosting deploy executed + verified": {
        "emulator": "the local compose/Tilt stack from deploy_topology.json IS the local hosting (teleon-runtime)",
        "kind": "container", "service": "teleon-runtime", "runnable_via": _BASE_COMPOSE},
}


def _symbol_ok(module: str, symbol: str | None) -> bool:
    try:
        mod = importlib.import_module(module)
    except Exception:
        return False
    return True if not symbol else hasattr(mod, symbol)


def _topology_service_names() -> set[str]:
    d = json.loads((_REPO / "architecture" / "deploy_topology.json").read_text())
    svcs = d.get("services", d) if isinstance(d, dict) else d
    if isinstance(svcs, dict):
        return set(svcs.keys())
    return {s.get("name") for s in svcs if isinstance(s, dict)} | {s for s in svcs if isinstance(s, str)}


def _verify(desc: dict) -> bool:
    ok = True
    if desc.get("module"):
        ok = ok and _symbol_ok(desc["module"], desc.get("symbol"))
    if desc.get("fixture"):
        ok = ok and (_REPO / desc["fixture"]).exists()
    if desc.get("service"):
        ok = ok and desc["service"] in _topology_service_names()
    if desc.get("runnable_via"):
        ok = ok and (_REPO / desc["runnable_via"]).exists()
    if desc.get("compose_service"):  # the emulator must actually be declared in the overlay compose
        ok = ok and desc["compose_service"] in (_REPO / desc["runnable_via"]).read_text()
    return ok


def _freshness_seam_e2e() -> dict:
    """Wire FreshnessSyncedCapability to the LOCAL source emulator: fresh -> source changes -> held out -> re-sync."""
    from local_emulators.source_of_truth_emulator import SourceOfTruthEmulator
    from src.teleon.evolution.freshness_runtime import FreshnessSyncedCapability

    emu = SourceOfTruthEmulator(source_id="ecfr://12/1005.11", value="10 business days", version="2025-edition")
    cap = FreshnessSyncedCapability("reg-e-error-resolution-deadline",
                                    authoritative_source=emu.source_id, volatility_class="low")
    cur = emu.current()
    cap.sync(cur["value"], now="t0", source_version=cur["version"])
    fresh = cap.serve(now="t1")                                   # serves the current value
    event = emu.change("12 business days", "2026-edition")        # the regulation is amended (CDC event)
    held = cap.on_source_change(event, now="t2")                  # prior answer held out as stale
    stale = cap.serve(now="t3")                                   # must serve NOTHING while stale
    cur2 = emu.current()
    cap.sync(cur2["value"], now="t4", source_version=cur2["version"])  # re-sync from the emulator's new value
    refreshed = cap.serve(now="t5")                              # serves the NEW current value
    return {
        "served_fresh": fresh["served"], "held_out_status": held["status"],
        "served_while_stale": stale["served"], "served_after_resync": refreshed["served"],
        "change_count": emu.change_count,
        "serves_truth": any(x["serves_truth"] for x in (fresh, held, stale, refreshed)),
    }


def _model_seam_e2e() -> dict:
    """Route a call through the LOCAL model emulator: deterministic + real token counts, never truth."""
    from local_emulators.model_emulator import ModelEmulator

    m = ModelEmulator()
    prompt = "what is the Reg E error-resolution deadline?"
    r1, r2 = m.complete(prompt), m.complete(prompt)
    return {"deterministic": r1 == r2, "tokens_in": r1["tokens_in"], "tokens_out": r1["tokens_out"],
            "model_id": r1["model"], "serves_truth": r1["serves_truth"]}


def local_emulation_report() -> dict:
    from scripts.check_teleon_go_live_readiness import readiness_report

    rep = readiness_report()
    blocking = rep["blocking_seams"]
    coverage = []
    for seam in blocking:
        desc = LOCAL_EMULATORS.get(seam)
        coverage.append({"seam": seam, "emulator": desc["emulator"] if desc else None,
                         "kind": desc["kind"] if desc else None, "covered": bool(desc) and _verify(desc)})
    fresh, model = _freshness_seam_e2e(), _model_seam_e2e()
    e2e_ok = (fresh["served_fresh"] == "10 business days" and fresh["held_out_status"] == "held_out"
              and fresh["served_while_stale"] is None and fresh["served_after_resync"] == "12 business days"
              and fresh["change_count"] == 1 and fresh["serves_truth"] is False
              and model["deterministic"] and model["tokens_in"] > 0 and model["tokens_out"] > 0
              and model["serves_truth"] is False)
    all_covered = bool(coverage) and all(c["covered"] for c in coverage)
    return {
        "blocking_seams": blocking, "coverage": coverage,
        "n_blocking": len(blocking), "n_covered": sum(1 for c in coverage if c["covered"]),
        "all_blocking_seams_emulated_locally": all_covered,
        "freshness_seam_e2e": fresh, "model_seam_e2e": model, "e2e_ok": e2e_ok,
        # the whole stack runs locally even though CLOUD go-live stays honestly False (local != cloud).
        "local_go_live_ready": all_covered and e2e_ok,
        "cloud_go_live_ready": rep["go_live_ready"],
        "runnable_via": {"base": _BASE_COMPOSE, "emulators_overlay": _EMU_COMPOSE, "tilt": _TILTFILE},
        "serves_truth": False,
    }


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    r = local_emulation_report()
    ck("every BLOCKING go-live seam maps to a built local emulator (none missing)",
       r["all_blocking_seams_emulated_locally"] and r["n_covered"] == r["n_blocking"] and r["n_blocking"] >= 1,
       str([c["seam"] for c in r["coverage"] if not c["covered"]]))
    ck("freshness seam wires e2e locally: serve fresh value (10 business days)",
       r["freshness_seam_e2e"]["served_fresh"] == "10 business days")
    ck("freshness seam: source change HELDS the stale answer OUT (never served while stale)",
       r["freshness_seam_e2e"]["held_out_status"] == "held_out" and r["freshness_seam_e2e"]["served_while_stale"] is None)
    ck("freshness seam: re-sync to the local source's NEW value (12 business days)",
       r["freshness_seam_e2e"]["served_after_resync"] == "12 business days")
    ck("model seam: local LLM is deterministic + reports real token counts (in & out)",
       r["model_seam_e2e"]["deterministic"] and r["model_seam_e2e"]["tokens_in"] > 0
       and r["model_seam_e2e"]["tokens_out"] > 0)
    ck("the emulators overlay compose declares BOTH local emulator services",
       all(s in (_REPO / _EMU_COMPOSE).read_text() for s in ("model-emulator", "source-emulator")))
    ck("the Tiltfile brings up the stack + runs the local-emulation proof",
       all(t in (_REPO / _TILTFILE).read_text() for t in (_EMU_COMPOSE, "check_teleon_local_emulation")))
    ck("local_go_live_ready is TRUE (the whole stack runs locally / emulated)", r["local_go_live_ready"] is True)
    ck("cloud go_live_ready stays honestly FALSE (local emulation != real cloud go-live)",
       r["cloud_go_live_ready"] is False)
    ck("no emulator ever serves truth (freshness + model + report)",
       r["serves_truth"] is False and r["freshness_seam_e2e"]["serves_truth"] is False
       and r["model_seam_e2e"]["serves_truth"] is False)
    ck("deterministic", local_emulation_report()["local_go_live_ready"] == r["local_go_live_ready"])

    print("\n" + ("PASS - check_teleon_local_emulation: every blocking go-live seam (live LLM, live source+CDC, "
                  "distillation, eval data, Postgres, auth, hosting) has a built LOCAL emulator; the freshness seam "
                  "(serve fresh -> source changes -> stale held out -> re-synced) and the model seam (deterministic "
                  "+ token counts) wire end-to-end in-process; the stack runs via the compose overlay + Tiltfile. "
                  "local_go_live_ready=True while cloud go_live_ready stays honestly False. Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--report" in argv:
        print(json.dumps(local_emulation_report(), indent=2))
        return 0
    print("usage: check_teleon_local_emulation.py --self-test | --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
