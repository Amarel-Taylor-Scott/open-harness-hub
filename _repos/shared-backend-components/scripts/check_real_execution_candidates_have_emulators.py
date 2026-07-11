#!/usr/bin/env python3
"""scripts.check_real_execution_candidates_have_emulators — proof (the DEFER GATE): every real cloud/K8s/
Docker execution candidate declares a local_emulator_provider that is actually BUILT, importable, and in
the local_equivalents_built list. Cloud can be candidate; the local equivalent cannot be missing.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_real_execution_candidates_have_emulators.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import importlib
import json
from pathlib import Path

_A = _resource("architecture")
# real cloud/k8s/docker backends that must each have a built local equivalent
_REAL_CANDIDATES = {"aws_lambda@candidate", "gcp_cloud_run_function@candidate", "azure_function@candidate",
                    "cloud_run_job@candidate", "k8s_job@candidate", "k8s_deployment_worker@candidate",
                    "docker_container@candidate"}
# emulator provider id → its module (must import without cloud SDKs)
_EMU_MODULE = {
    "execution.local_function_emulator@v1": "src.baltor.workers.function_emulator",
    "execution.managed_venv@v1": "src.baltor.workers.execution_providers.managed_venv",
    "execution.local_job_emulator@v1": "src.baltor.workers.execution_providers.local_job_emulator",
    "execution.local_cloud_run_job_emulator@v1": "src.baltor.workers.execution_providers.local_job_emulator",
    "execution.local_worker_pool@v1": "src.baltor.workers.execution_providers.local_worker_pool",
    "execution.container_image_emulator@v1": "src.baltor.workers.execution_providers.container_image_emulator",
    "execution.provider_unavailable@v1": "src.baltor.workers.execution_providers.provider_unavailable",
}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    m = json.loads((_A / "execution_backend_policy_matrix.json").read_text())
    eq = m.get("candidate_local_equivalents", {})
    built = set(m.get("local_equivalents_built", []))

    for cand in sorted(_REAL_CANDIDATES):
        emu = eq.get(cand)
        chk(f"{cand} declares a local_emulator_provider", bool(emu), "missing")
        if emu:
            chk(f"{cand} → emulator is in local_equivalents_built", emu in built, emu)
            chk(f"{cand} → emulator module imports (no cloud SDK)", emu in _EMU_MODULE and _import_ok(_EMU_MODULE[emu]))

    # every declared built emulator actually imports
    for emu, mod in _EMU_MODULE.items():
        chk(f"built emulator {emu} importable", _import_ok(mod))

    print(f"\n{'PASS — check_real_execution_candidates_have_emulators: every real cloud/K8s/Docker candidate has a built, importable local equivalent (the defer gate holds).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _import_ok(mod: str) -> bool:
    try:
        importlib.import_module(mod); return True
    except Exception:
        return False


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
