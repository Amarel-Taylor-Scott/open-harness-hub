"""check_agent_runtime_layer — proof for the shared AI-AGENT RUNTIME layer (Teleon-owned).

Asserts: the port contract; the local emulator runs offline + deterministically + ``serves_truth=False``;
candidate runtimes (ClawLess/OpenClaw, Hermes) degrade gracefully (unavailable, env:// ref, never
imported/executed, ``run_agent`` raises); ``dispatch_agent_request`` SELECTS a real Teleon backend via
execution_backend_selector and an open-ended agent is hard-guarded off generic cloud functions but CAN provision
onto a K8s job / sandbox worker when policy + creds allow; agent output is never truth; the layer is Teleon-owned
(no Baltor import) and carries no raw keys; unknown runtimes never crash. Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.agents.agent_runtime_provider import (  # noqa: E402
    AGENT_SERVES_TRUTH, DEFAULT_AGENT_BUCKET, LOCAL_EMULATOR_RUNTIME_ID, AgentRuntimeProviderPort,
    AgentRuntimeRequest, AgentRuntimeResult, AgentRuntimeUnavailable, AgentRuntimeUnavailableResult,
    CandidateAgentRuntime, LocalEmulatorAgentRuntime, dispatch_agent_request, get_runtime, load_catalog,
)
from src.teleon.runtime.execution_backend_selector import generic_functions  # noqa: E402

NOW = "2026-06-08T00:00:00Z"
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,}|xai-[A-Za-z0-9]{8,})")


def _raises(exc, fn, *a, **k) -> bool:
    try:
        fn(*a, **k)
        return False
    except exc:
        return True


def main() -> int:
    cat = load_catalog()
    fails: list[str] = []

    # 1. catalog integrity: exactly one ACTIVE runtime (local emulator); ClawLess/OpenClaw + Hermes candidates.
    runtimes = cat.get("runtimes", [])
    active = [r for r in runtimes if r.get("status") == "active"]
    cands = [r for r in runtimes if r.get("status") == "candidate"]
    if not (len(active) == 1 and active[0]["runtime_id"] == LOCAL_EMULATOR_RUNTIME_ID):
        fails.append("catalog must have exactly one active runtime = local_emulator@v1")
    ids = {r["runtime_id"] for r in cands}
    if not ({"clawless_openclaw@candidate", "hermes@candidate"} <= ids):
        fails.append("catalog must register ClawLess/OpenClaw + Hermes as candidate runtimes")
    for r in cands:
        if not str(r.get("runtime_ref", "")).startswith("env://"):
            fails.append(f"candidate {r['runtime_id']} must name an env:// runtime_ref (never a value)")
        if not r.get("sandbox_profile"):
            fails.append(f"candidate {r['runtime_id']} must declare a sandbox_profile")
        if r.get("serves_truth") is not False:
            fails.append(f"candidate {r['runtime_id']} serves_truth must be false")

    # 2. NO raw keys anywhere in the catalog (env:// refs only).
    if _KEY_RE.search(json.dumps(cat)):
        fails.append("catalog must carry NO raw API keys (env:// refs only)")

    # 3. port contract: the local emulator satisfies the runtime-checkable port.
    emu = LocalEmulatorAgentRuntime()
    if not isinstance(emu, AgentRuntimeProviderPort):
        fails.append("LocalEmulatorAgentRuntime must satisfy AgentRuntimeProviderPort")

    # 4. local emulator runs offline + deterministically + serves_truth False.
    req = AgentRuntimeRequest(task_id="T1", tenant_id="acme", runtime_id=LOCAL_EMULATOR_RUNTIME_ID,
                              intent="summarize ticket BILL-782", bounds={"max_steps": 3})
    r1 = emu.run_agent(req, backend="local_function_emulator@v1", now=NOW)
    r2 = emu.run_agent(req, backend="local_function_emulator@v1", now=NOW)
    if not (isinstance(r1, AgentRuntimeResult) and r1.status == "succeeded"):
        fails.append("local emulator must succeed offline")
    if r1.serves_truth is not False or AGENT_SERVES_TRUTH is not False:
        fails.append("agent output serves_truth must be False (no agent output becomes truth)")
    if r1.result_ids != r2.result_ids:
        fails.append("local emulator must be deterministic when now is injected")

    # 5. candidate runtimes degrade gracefully (unavailable, env:// ref, not imported/executed, run_agent raises).
    for rid in ("clawless_openclaw@candidate", "hermes@candidate"):
        prov = get_runtime(rid, catalog=cat)
        if not isinstance(prov, CandidateAgentRuntime):
            fails.append(f"{rid} must resolve to a CandidateAgentRuntime (catalog entry only)")
            continue
        st = prov.status()
        if st.get("status") != "unavailable" or st.get("imported") or st.get("executed"):
            fails.append(f"{rid} must report unavailable + not imported/executed")
        if not str(st.get("runtime_ref", "")).startswith("env://"):
            fails.append(f"{rid} status must name its env:// runtime_ref")
        if not _raises(AgentRuntimeUnavailable, prov.run_agent, req, backend="k8s_job@candidate", now=NOW):
            fails.append(f"{rid}.run_agent must raise AgentRuntimeUnavailable (never imported/executed)")

    # 6. dispatch on the ACTIVE runtime selects a real backend + runs + never truth.
    env = dispatch_agent_request(
        AgentRuntimeRequest(task_id="T2", tenant_id="acme", runtime_id=LOCAL_EMULATOR_RUNTIME_ID, intent="triage"),
        now=NOW)
    if env["runtime_status"] != "active" or not isinstance(env["result"], AgentRuntimeResult):
        fails.append("dispatch on local emulator must run (active)")
    elif env["result"].serves_truth is not False:
        fails.append("dispatched agent result serves_truth must be False")
    if not env["backend_decision"].get("backend"):
        fails.append("dispatch must select an execution backend via the selector")

    # 7. HARD GUARD: an open-ended agent is NEVER auto-provisioned onto a generic cloud function; a candidate
    #    still reports which backend it WOULD provision (honest degradation).
    gen = generic_functions()
    open_req = AgentRuntimeRequest(task_id="T3", tenant_id="acme", runtime_id="hermes@candidate",
                                   intent="browse + act", worker_bucket=DEFAULT_AGENT_BUCKET)
    env_open = dispatch_agent_request(open_req, now=NOW)
    if env_open["backend_decision"].get("backend") in gen:
        fails.append("open-ended agent must NOT be auto-provisioned onto a generic cloud function (hard guard)")
    if not isinstance(env_open["result"], AgentRuntimeUnavailableResult):
        fails.append("candidate runtime dispatch must return AgentRuntimeUnavailableResult (graceful)")
    elif not env_open["result"].backend_would_be:
        fails.append("candidate dispatch must report backend_would_be (honest degradation)")

    # 8. it CAN provision onto a K8s job when policy + creds allow (the 'set up appropriate K8s' path).
    env_k8s = dispatch_agent_request(
        open_req, now=NOW,
        policy_override={"eligible": ["k8s_job@candidate", "sandbox_worker@candidate", "local_function_emulator@v1"],
                         "preferred_backends": ["k8s_job@candidate"]},
        available_creds={"k8s_job@candidate", "sandbox_worker@candidate"})
    if env_k8s["backend_decision"].get("backend") != "k8s_job@candidate":
        fails.append("with creds+policy, an agent must provision onto a K8s job (the 'set up K8s' path)")

    # 9. unknown runtime_id never crashes (structured unavailable).
    env_unknown = dispatch_agent_request(
        AgentRuntimeRequest(task_id="T4", tenant_id="acme", runtime_id="nope@x", intent="x"), now=NOW)
    if not (env_unknown["runtime_status"] == "unknown"
            and isinstance(env_unknown["result"], AgentRuntimeUnavailableResult)):
        fails.append("unknown runtime_id must return a structured unavailable result, never crash")

    # 10. Teleon-owned: the module must NOT import Baltor (dependency law Baltor→Teleon, never reverse).
    src = (_REPO / "src" / "teleon" / "agents" / "agent_runtime_provider.py").read_text()
    if "src.baltor" in src or "import baltor" in src:
        fails.append("agent runtime layer (Teleon) must NOT import Baltor (dependency law)")

    # 11. positioning preserved in the catalog (agents propose; never truth; rides FleetLedger; Teleon-owned).
    note = (cat.get("note", "") + json.dumps(cat.get("positioning", {}))).lower()
    for token in ("propose", "serves_truth", "fleetledger", "teleon", "open_ended_agent"):
        if token not in note:
            fails.append(f"catalog positioning must state '{token}'")

    if fails:
        print("check_agent_runtime_layer: FAILURES")
        for f in fails:
            print("  -", f)
        return 1
    print(f"PASS — check_agent_runtime_layer: agent-runtime port + {len(active)} active (local emulator) + "
          f"{len(cands)} candidate runtimes (ClawLess/OpenClaw, Hermes); dispatch selects a Teleon backend "
          f"(open-ended agent hard-guarded off generic functions; K8s/sandbox on creds); agent output never "
          f"truth; Teleon-owned; no raw keys.")
    return 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    raise SystemExit(main())
