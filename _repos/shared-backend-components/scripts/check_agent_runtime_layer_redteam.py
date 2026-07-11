"""check_agent_runtime_layer_redteam — adversarial proof for the shared AI-AGENT RUNTIME layer (Teleon).

A shared `find_violations(catalog, outcomes, *, module_src, generic)` validator is reused by BOTH a CONTROL
(the REAL agent_runtime_catalog + REAL dispatch_agent_request outcomes + the REAL module source → MUST be clean)
AND attack fixtures, each of which mutates ONE thing and MUST be caught:

  A1 candidate runtime card claims serves_truth=true        A6 dispatch crashed instead of structured-unavailable
  A2 candidate claims imported/executed=true                A7 unknown runtime not degraded to Unavailable
  A3 candidate runtime_ref is a raw key (not env://)         A8 the module imports src.baltor (dependency law)
  A4 an agent result claims serves_truth=true (output→truth) A9 a second active runtime (only local_emulator may be active)
  A5 open-ended agent provisioned onto a generic cloud function without an allow_generic proof

Deterministic, offline, stdlib only. Mirrors the fragile-atlas redteam shape (control + attacks via one validator).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import copy
import json
import re
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.agents.agent_runtime_provider import (  # noqa: E402
    py_const_src_teleon_agents_agent_runtime_provider__LOCAL_EMULATOR_RUNTIME_ID, py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeRequest, py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeUnavailableResult, py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request, py_function_src_teleon_agents_agent_runtime_provider__load_catalog,
)
from src.teleon.runtime.execution_backend_selector import py_function_src_teleon_runtime_execution_backend_selector__generic_functions  # noqa: E402

NOW = "2026-06-08T00:00:00Z"
#: a FAKE leaked key for attack A3 — ASSEMBLED from fragments so the literal never appears in tracked source
#: (otherwise check_llm_secret_hygiene correctly flags it); it still matches _KEY_RE at runtime.
_FAKE_LEAKED_KEY = "sk-" + "live" + "deadbeef1234"
#: buckets the selector hard-guards off generic cloud functions (mirror execution_backend_selector).
_GUARDED = {"open_ended_agent", "browser", "model_inference", "cpu_gpu_compute", "control_plane"}
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,}|xai-[A-Za-z0-9]{8,})")


def find_violations(catalog: dict, outcomes: list[dict], *, module_src: str, generic: set) -> list[str]:
    """The single governance gate. Returns a list of violation codes (empty = clean). Used by the control + every attack."""
    v: list[str] = []
    runtimes = catalog.get("runtimes", [])

    # exactly one ACTIVE runtime, and it must be the local emulator (the offline correctness invariant).
    active = [r for r in runtimes if r.get("status") == "active"]
    if not (len(active) == 1 and active[0].get("runtime_id") == py_const_src_teleon_agents_agent_runtime_provider__LOCAL_EMULATOR_RUNTIME_ID):
        v.append("active_runtime_invariant")

    for r in runtimes:
        rid = r.get("runtime_id", "?")
        if r.get("serves_truth") is not False:                      # an agent runtime NEVER serves truth
            v.append(f"serves_truth_true:{rid}")
        if _KEY_RE.search(json.dumps(r)):                           # no raw key anywhere in a card
            v.append(f"raw_key:{rid}")
        if r.get("status") == "candidate":
            if r.get("imported") or r.get("executed"):              # candidates are catalog-only
                v.append(f"candidate_imported_or_executed:{rid}")
            if not str(r.get("runtime_ref", "")).startswith("env://"):  # candidates name an env:// ref, never a value
                v.append(f"candidate_runtime_ref_not_env:{rid}")

    for o in outcomes:
        rid = o.get("runtime_id", "?")
        if o.get("result_serves_truth") is True:                    # agent OUTPUT never becomes truth
            v.append(f"agent_output_as_truth:{rid}")
        if o.get("backend") in generic and o.get("worker_bucket") in _GUARDED and not o.get("allow_generic_proof"):
            v.append(f"open_ended_agent_on_generic_function:{rid}")  # hard guard: no open-ended agent on a generic fn
        if o.get("crashed"):                                        # a missing runtime degrades, never crashes
            v.append(f"crashed_not_structured:{rid}")
        if o.get("runtime_status") in ("unknown", "unavailable") and not o.get("result_is_unavailable"):
            v.append(f"not_degraded:{rid}")                         # candidate/unknown must return Unavailable

    if "src.baltor" in module_src or "import baltor" in module_src:  # dependency law: Teleon never imports Baltor
        v.append("baltor_import")
    return v


def _outcome(env: dict, *, worker_bucket: str, allow_generic_proof: bool = False, crashed: bool = False) -> dict:
    res = env["result"]
    return {"runtime_id": env["runtime_id"], "runtime_status": env["runtime_status"],
            "worker_bucket": worker_bucket, "backend": env["backend_decision"].get("backend"),
            "allow_generic_proof": allow_generic_proof,
            "result_serves_truth": getattr(res, "serves_truth", False),
            "result_kind": type(res).__name__,
            "result_is_unavailable": isinstance(res, py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeUnavailableResult),
            "crashed": crashed}


def main() -> int:
    gen = py_function_src_teleon_runtime_execution_backend_selector__generic_functions()
    cat = py_function_src_teleon_agents_agent_runtime_provider__load_catalog()
    module_src = (_resource("src/teleon/agents/agent_runtime_provider.py")).read_text()

    # ── CONTROL: real catalog + real dispatch outcomes + real module source → MUST be clean ──
    e_local = py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request(
        py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeRequest(task_id="T1", tenant_id="acme", runtime_id=py_const_src_teleon_agents_agent_runtime_provider__LOCAL_EMULATOR_RUNTIME_ID, intent="triage"), now=NOW)
    e_hermes = py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request(
        py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeRequest(task_id="T2", tenant_id="acme", runtime_id="hermes@candidate", intent="browse+act"), now=NOW)
    e_unknown = py_function_src_teleon_agents_agent_runtime_provider__dispatch_agent_request(
        py_class_src_teleon_agents_agent_runtime_provider__AgentRuntimeRequest(task_id="T3", tenant_id="acme", runtime_id="nope@x", intent="x"), now=NOW)
    control = [_outcome(e_local, worker_bucket="open_ended_agent"),
               _outcome(e_hermes, worker_bucket="open_ended_agent"),
               _outcome(e_unknown, worker_bucket="open_ended_agent")]

    fails: list[str] = []
    base = find_violations(cat, control, module_src=module_src, generic=gen)
    if base:
        fails.append(f"CONTROL must be clean, got {base}")

    # ── ATTACKS: each mutates ONE thing; the expected violation code MUST appear ──
    def attack(name: str, *, catalog=None, outcomes=None, src=None, expect: str) -> None:
        viol = find_violations(catalog if catalog is not None else cat,
                               outcomes if outcomes is not None else control,
                               module_src=src if src is not None else module_src, generic=gen)
        if not any(x.startswith(expect) for x in viol):
            fails.append(f"attack '{name}' NOT caught (expected {expect!r}, got {viol})")

    def cat_mut(fn):
        c = copy.deepcopy(cat)
        fn(c)
        return c

    def first_candidate(c):
        return next(r for r in c["runtimes"] if r.get("status") == "candidate")

    attack("A1 candidate serves_truth=true", catalog=cat_mut(lambda c: first_candidate(c).__setitem__("serves_truth", True)),
           expect="serves_truth_true")
    attack("A2 candidate imported=true", catalog=cat_mut(lambda c: first_candidate(c).__setitem__("imported", True)),
           expect="candidate_imported_or_executed")
    attack("A3 candidate runtime_ref raw key", catalog=cat_mut(lambda c: first_candidate(c).__setitem__("runtime_ref", _FAKE_LEAKED_KEY)),
           expect="raw_key")
    attack("A4 agent output as truth",
           outcomes=[{**control[0], "result_serves_truth": True}], expect="agent_output_as_truth")
    attack("A5 open-ended agent on generic function",
           outcomes=[{**control[0], "backend": next(iter(gen)), "worker_bucket": "open_ended_agent", "allow_generic_proof": False}],
           expect="open_ended_agent_on_generic_function")
    attack("A6 crashed not structured",
           outcomes=[{**control[2], "crashed": True}], expect="crashed_not_structured")
    attack("A7 unknown not degraded",
           outcomes=[{**control[2], "result_kind": "AgentRuntimeResult", "result_is_unavailable": False}], expect="not_degraded")
    attack("A8 baltor import", src="from src.baltor.experiments import parallel_paths\n", expect="baltor_import")
    attack("A9 second active runtime",
           catalog=cat_mut(lambda c: c["runtimes"].append({"runtime_id": "rogue@v1", "status": "active",
                                                            "imported": True, "executed": True, "serves_truth": False})),
           expect="active_runtime_invariant")

    # sanity: allow_generic_proof=True (owner asserted a proof) is NOT a violation for a generic-fn backend.
    ok_proof = find_violations(cat, [{**control[0], "backend": next(iter(gen)), "worker_bucket": "open_ended_agent",
                                      "allow_generic_proof": True}], module_src=module_src, generic=gen)
    if any(x.startswith("open_ended_agent_on_generic_function") for x in ok_proof):
        fails.append("allow_generic_proof=True must NOT be flagged (an owner-proven override is allowed)")

    if fails:
        print("check_agent_runtime_layer_redteam: FAILURES")
        for f in fails:
            print("  -", f)
        return 1
    print("PASS — check_agent_runtime_layer_redteam: control clean; 9 attacks caught (candidate serves_truth / "
          "imported / raw-key / agent-output-as-truth / open-ended-on-generic-fn / crash-not-degraded / "
          "unknown-not-degraded / baltor-import / second-active-runtime); owner-proven generic override allowed.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    raise SystemExit(main())
