#!/usr/bin/env python3
"""scripts.check_capability_binding_provider — proof: a declared CapabilityTask BINDS to an execution target
without its author writing any cloud-function / Kubernetes-worker code. The active local-function binding is
offline + deterministic and records a backend chosen BY POLICY (delegated to select_backend) — so local-now
vs cloud-/K8s-later is a target+policy choice, not a code rewrite. Candidate targets (Nitric/Score/Temporal/
Knative/KEDA/Kratix) degrade gracefully (return, never raise; never imported/executed) while STILL reporting
the backend the policy WOULD pick. An open-ended/guarded CapabilityTask is never bound onto a generic cloud
function by default. Binding output is never truth, and the binding module never imports src.baltor.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_capability_binding_provider.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.ports.capability_binding_provider import (  # noqa: E402
    BINDING_SERVES_TRUTH,
    LOCAL_FUNCTION_TARGET,
    BindingResult,
    BindingUnavailableResult,
    CapabilityTaskBindingProvider,
)
from src.teleon.runtime.capability_binding import (  # noqa: E402
    py_const_src_teleon_runtime_capability_binding__TARGETS,
    py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding,
    py_function_src_teleon_runtime_capability_binding__bind_capability_task,
    py_function_src_teleon_runtime_capability_binding__get_binding,
)
from src.teleon.runtime.execution_backend_selector import py_function_src_teleon_runtime_execution_backend_selector__generic_functions  # noqa: E402

_POLICY = json.loads((_resource("architecture") / "execution_backend_policy_matrix.json").read_text(encoding="utf-8"))
_NOW = "2026-06-08T00:00:00Z"
_BINDING_MODULE = _resource("src/teleon/runtime/capability_binding.py")
# CANDIDATE targets that must NEVER be imported/executed and must degrade gracefully.
_CANDIDATES = ("nitric@candidate", "score@candidate", "temporal@candidate",
               "knative@candidate", "keda@candidate", "kratix@candidate")


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # a short deterministic CapabilityTask (utility bucket) — the golden path.
    util_task = {"capability_id": "normalize.address", "worker_bucket": "utility",
                 "bounds": {"max_steps": 3}, "estimated_runtime_ms": 300}

    # (1) the active binding satisfies the runtime_checkable Protocol.
    binder = py_class_src_teleon_runtime_capability_binding__LocalFunctionBinding()
    chk("LocalFunctionBinding satisfies CapabilityTaskBindingProvider Protocol",
        isinstance(binder, CapabilityTaskBindingProvider))

    # (2) BINDING_SERVES_TRUTH / LOCAL_FUNCTION_TARGET constants are the pinned invariants.
    chk("BINDING_SERVES_TRUTH is False", BINDING_SERVES_TRUTH is False)
    chk("LOCAL_FUNCTION_TARGET is local_function@v1", LOCAL_FUNCTION_TARGET == "local_function@v1")

    # (3) local binding is OFFLINE + DETERMINISTIC: same task + same now → same binding_id.
    r1 = py_function_src_teleon_runtime_capability_binding__bind_capability_task(util_task, target=LOCAL_FUNCTION_TARGET, now=_NOW)
    r2 = py_function_src_teleon_runtime_capability_binding__bind_capability_task(util_task, target=LOCAL_FUNCTION_TARGET, now=_NOW)
    chk("local binding returns a BindingResult", isinstance(r1, BindingResult))
    chk("local binding is bound", getattr(r1, "status", None) == "bound")
    chk("local binding is deterministic (same task+now → same binding_id)",
        isinstance(r1, BindingResult) and isinstance(r2, BindingResult) and r1.binding_id == r2.binding_id,
        f"{getattr(r1, 'binding_id', None)} vs {getattr(r2, 'binding_id', None)}")
    # different now → different binding_id (binding_id is content-addressed, not constant).
    r_other = py_function_src_teleon_runtime_capability_binding__bind_capability_task(util_task, target=LOCAL_FUNCTION_TARGET, now="2026-06-09T00:00:00Z")
    chk("different now → different binding_id (content-addressed)",
        isinstance(r_other, BindingResult) and r_other.binding_id != r1.binding_id)

    # (4) binding output is NEVER truth.
    chk("local binding output serves_truth is False",
        isinstance(r1, BindingResult) and r1.serves_truth is False)

    # (5) the local binding RECORDS a backend chosen via select_backend (policy abstracts cloud/K8s wiring).
    chk("local binding records a backend chosen by policy",
        isinstance(r1, BindingResult) and bool(r1.backend)
        and isinstance(r1.detail.get("backend_decision"), dict)
        and r1.detail["backend_decision"].get("backend") == r1.backend,
        str(getattr(r1, "detail", None)))
    # utility/local task lands on the local function emulator backend by default (no creds → offline invariant).
    chk("utility CapabilityTask binds onto the local function emulator backend by default",
        isinstance(r1, BindingResult) and r1.backend in ("local_function_emulator@v1", "local_subprocess@v1"),
        getattr(r1, "backend", None))

    # (6) SWITCHABLE BY POLICY (no code change): same CapabilityTask, a policy override + creds → k8s backend.
    rk = py_function_src_teleon_runtime_capability_binding__bind_capability_task(util_task, target=LOCAL_FUNCTION_TARGET, now=_NOW,
                              policy_override={"preferred_backends": ["k8s_deployment_worker@candidate"]},
                              available_creds={"k8s_deployment_worker@candidate"})
    chk("same CapabilityTask switches to a K8s backend by POLICY (no code change)",
        isinstance(rk, BindingResult) and rk.backend == "k8s_deployment_worker@candidate",
        getattr(rk, "backend", None))

    # (7) HARD GUARD: an open-ended/guarded CapabilityTask is NOT bound onto a generic cloud function by
    # default — even when every generic-function cred is present.
    generic = py_function_src_teleon_runtime_execution_backend_selector__generic_functions()
    open_task = {"capability_id": "agent.research", "worker_bucket": "open_ended_agent",
                 "estimated_runtime_ms": 9000}
    ro = py_function_src_teleon_runtime_capability_binding__bind_capability_task(open_task, target=LOCAL_FUNCTION_TARGET, now=_NOW,
                              available_creds=set(generic) | {"k8s_job@candidate", "sandbox_worker@candidate"})
    chk("open-ended CapabilityTask is NOT bound onto a generic cloud function (hard guard)",
        isinstance(ro, BindingResult) and ro.backend not in generic, getattr(ro, "backend", None))
    # ...but a policy override WITH PROOF can still allow it (the guard is policy, not hardwired): the override
    # must (a) make a generic function ELIGIBLE and (b) assert allow_generic_functions (the proof flag). Pick a
    # generic function the bucket does NOT exclude-by-default (config-driven, no hardcoded vendor).
    bucket_excluded = set(_POLICY["buckets"]["open_ended_agent"].get("excluded_by_default", []))
    one_fn = sorted(set(generic) - bucket_excluded)[0]
    ro2 = py_function_src_teleon_runtime_capability_binding__bind_capability_task(open_task, target=LOCAL_FUNCTION_TARGET, now=_NOW,
                               available_creds={one_fn},
                               policy_override={"allow_generic_functions": True,
                                                "eligible": [one_fn],
                                                "preferred_backends": [one_fn]})
    chk("policy override WITH PROOF can bind open-ended onto a generic function (guard is policy, not hardwired)",
        isinstance(ro2, BindingResult) and ro2.backend in generic, getattr(ro2, "backend", None))

    # (8) CANDIDATE targets degrade gracefully: return (never raise) a BindingUnavailableResult, never crash,
    # never imported/executed, AND still report backend_would_be.
    for tgt in _CANDIDATES:
        try:
            cr = py_function_src_teleon_runtime_capability_binding__bind_capability_task(open_task, target=tgt, now=_NOW)
        except Exception as exc:  # candidate binding MUST NOT crash
            chk(f"candidate target {tgt} degrades gracefully (no crash)", False, repr(exc))
            continue
        ok = (isinstance(cr, BindingUnavailableResult) and cr.consumable is False
              and cr.serves_truth is False and cr.target == tgt and bool(cr.backend_would_be))
        chk(f"candidate target {tgt} → BindingUnavailableResult with backend_would_be (graceful)", ok,
            str(cr))
        # the env:// ref is named (owner-gated), and it is a REF not a value.
        chk(f"candidate target {tgt} names an env:// ref (never a value)",
            isinstance(cr, BindingUnavailableResult) and isinstance(cr.ref, str) and cr.ref.startswith("env://"),
            str(getattr(cr, "ref", None)))
        # the provider for a candidate must report it is NOT imported/executed.
        prov = py_function_src_teleon_runtime_capability_binding__get_binding(tgt)
        st = prov.status() if prov is not None else {}
        chk(f"candidate target {tgt} provider reports not imported/executed",
            st.get("imported") is False and st.get("executed") is False, str(st))

    # (9) UNKNOWN target → structured BindingUnavailableResult (never crash), still reports backend_would_be.
    try:
        ur = py_function_src_teleon_runtime_capability_binding__bind_capability_task(util_task, target="made_up_target@v9", now=_NOW)
        unknown_ok = (isinstance(ur, BindingUnavailableResult) and ur.consumable is False
                      and ur.serves_truth is False and bool(ur.backend_would_be))
    except Exception as exc:
        unknown_ok = False
        ur = repr(exc)
    chk("unknown target → structured BindingUnavailableResult (never crash)", unknown_ok, str(ur))

    # (10) every BindingResult/BindingUnavailableResult across the registry has serves_truth False
    # (binding output never truth).
    truth_leak = []
    for tgt in py_const_src_teleon_runtime_capability_binding__TARGETS:
        out = py_function_src_teleon_runtime_capability_binding__bind_capability_task(util_task, target=tgt, now=_NOW)
        if getattr(out, "serves_truth", None) is not False:
            truth_leak.append(tgt)
    chk("no binding output serves truth (serves_truth False for every target)", not truth_leak, str(truth_leak))

    # (11) the binding module does NOT import src.baltor (line-anchored regex, not a docstring substring).
    src = _BINDING_MODULE.read_text(encoding="utf-8")
    import_re = re.compile(r"^\s*(?:from|import)\s+src\.baltor\b", re.MULTILINE)
    chk("capability_binding.py does NOT import src.baltor (Teleon !-> Baltor)", import_re.search(src) is None)

    # (12) no raw API key literals in the binding module (refs are env:// only).
    key_re = re.compile(r"(?:sk-[A-Za-z0-9]{8,}|api[_-]?key\s*=\s*['\"][A-Za-z0-9]{12,}['\"])", re.IGNORECASE)
    chk("no raw API key literals in capability_binding.py", key_re.search(src) is None)

    ok_msg = ("PASS — check_capability_binding_provider: a declared CapabilityTask binds to the local function "
              "emulator (active, offline, deterministic) with its execution backend chosen BY POLICY via "
              "select_backend (switchable local<->k8s<->cloud-function, no code change); open-ended/guarded "
              "tasks stay off generic cloud functions by default; candidate targets (Nitric/Score/Temporal/"
              "Knative/KEDA/Kratix) degrade gracefully (return, never raise; never imported/executed; report "
              "backend_would_be); unknown target → structured unavailable; binding output never truth; module "
              "never imports src.baltor.")
    print(f"\n{ok_msg if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
