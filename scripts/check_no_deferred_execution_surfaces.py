#!/usr/bin/env python3
"""scripts.check_no_deferred_execution_surfaces — redteam (DEFER GATE): the system does not silently
require an unavailable cloud backend, and no execution opportunity defers a LOCAL capability. Missing
cloud creds / Docker return a structured ProviderUnavailableResult (no crash, no truth); the selector
falls back locally; and any 'deferred' execution opportunity names only real cloud/credential/Docker
limits — never a missing local emulator.

CLI: PYTHONPATH=. python3 scripts/check_no_deferred_execution_surfaces.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.baltor.ports.execution_provider import ProviderUnavailableResult
from src.baltor.workers.execution_backend_selector import GENERIC_FUNCTIONS, select_backend
from src.baltor.workers.execution_providers.gcp_cloud_run_function_candidate import GcpCloudRunFunctionCandidate
from src.baltor.workers.execution_providers.provider_unavailable import ProviderUnavailable

_A = Path(__file__).resolve().parents[1] / "architecture"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # missing cloud creds → structured unavailable (no crash, no truth) + selector falls back locally
    r = GcpCloudRunFunctionCandidate().invoke({"task_id": "t", "capability_id": "u"})
    chk("missing cloud creds → ProviderUnavailableResult (no crash)", isinstance(r, ProviderUnavailableResult) and not r.consumable)
    d = select_backend({"capability_id": "u", "worker_bucket": "utility"},
                       policy_override={"preferred_backends": ["gcp_cloud_run_function@candidate"]}, available_creds=set())
    chk("selector falls back LOCALLY when the cloud backend is unavailable",
        d["backend"] in ("local_function_emulator@v1", "local_subprocess@v1"))
    chk("provider_unavailable sentinel never crashes/owns truth",
        isinstance(ProviderUnavailable("x").invoke({}), ProviderUnavailableResult))

    # the matrix gate: every real candidate maps to a BUILT local equivalent (no defer without emulator)
    m = json.loads((_A / "execution_backend_policy_matrix.json").read_text())
    eq, built = m.get("candidate_local_equivalents", {}), set(m.get("local_equivalents_built", []))
    orphans = [c for c, e in eq.items() if e not in built]
    chk("no real candidate maps to an unbuilt emulator", orphans == [], str(orphans))

    # opportunities: no execution opportunity defers a LOCAL capability (only real cloud/creds/Docker)
    opps = json.loads((_A / "opportunities.json").read_text())["opportunities"]
    ex_opps = [o for o in opps if "execution" in o.get("opportunity_id", "").lower() or "execution" in o.get("title", "").lower()]
    bad = []
    for o in ex_opps:
        blob = json.dumps(o).lower()
        defers_local = any(t in blob for t in ("local emulator", "local equivalent", "managed venv", "local function", "local job", "local worker pool"))
        # an execution opportunity may only defer real cloud/k8s/docker/creds — not local emulators
        if defers_local and "deferred" in blob:
            bad.append(o.get("opportunity_id"))
    chk("no execution opportunity defers a local emulator/equivalent", bad == [], str(bad))

    # browser/GPU still guarded off generic functions (defer gate must not weaken the safety guards)
    db = select_backend({"capability_id": "b", "worker_bucket": "browser", "requires_browser": True},
                        available_creds=GENERIC_FUNCTIONS)
    chk("browser still not on a generic function", db["backend"] not in GENERIC_FUNCTIONS)

    print(f"\n{'PASS — check_no_deferred_execution_surfaces: missing cloud degrades to a safe local fallback (no crash/truth); every real candidate has a built local equivalent; no opportunity defers a local capability; safety guards intact.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
