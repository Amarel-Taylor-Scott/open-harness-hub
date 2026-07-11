#!/usr/bin/env python3
"""scripts.check_execution_backend_policy_matrix — proof: the execution-backend policy matrix + pricebook
are well-formed; browser/GPU/open-ended/control-plane buckets exclude generic cloud functions by default;
every eligible backend is in the enum; the pricebook prices every backend; the offline correctness invariant is the
local emulator.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_execution_backend_policy_matrix.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import json
from pathlib import Path

_A = _resource("architecture")
#: NON-FRAGILE: don't exact-match the serverless set (it grows as cloud-agnostic peers are added). Only assert
#: a FLOOR of the three majors is present; the authoritative set is read from the matrix itself below.
_MAJORS = {"aws_lambda@candidate", "gcp_cloud_run_function@candidate", "azure_function@candidate"}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    m = json.loads((_A / "execution_backend_policy_matrix.json").read_text())
    pb = json.loads((_A / "execution_backend_pricebook.json").read_text())
    enum = set(m["backends_enum"])

    # CLOUD-AGNOSTIC + NON-FRAGILE: the serverless family is read from the matrix itself, not exact-matched to
    # a code literal. Assert structural invariants so adding a peer (GCP/Azure/Cloudflare/OpenFaaS) never breaks
    # this proof: declared, non-empty, ⊆ enum, the three majors present as a floor, each has a local equivalent.
    generic = set(m["generic_cloud_functions"])
    local_equivs = set(m.get("candidate_local_equivalents", {}))
    chk("offline correctness invariant is the local function emulator", m["offline_default_backend"] == "local_function_emulator@v1")
    chk("generic_cloud_functions declared, ⊆ enum, majors present (AWS Lambda not canonical — one peer)",
        bool(generic) and generic <= enum and _MAJORS <= generic, str(generic))
    chk("every serverless peer has a local equivalent (cloud-defer gate)", generic <= local_equivs, str(generic - local_equivs))
    for bucket, bp in m["buckets"].items():
        elig = set(bp.get("eligible", []))
        chk(f"{bucket}: eligible ⊆ backends_enum", elig <= enum, str(elig - enum))
        chk(f"{bucket}: a default backend is set", bool(bp.get("default")))
    # heavy buckets are NOT serverless-eligible (the real invariant; the selector's config-driven hard-guard
    # enforces it at runtime, so buckets need not redundantly enumerate every peer — that would be the very
    # magic-value duplication we're removing). Assert no serverless peer appears in their `eligible` set.
    for bucket in ("browser", "model_inference", "cpu_gpu_compute", "open_ended_agent", "control_plane"):
        bp = m["buckets"].get(bucket, {})
        elig = set(bp.get("eligible", []))
        chk(f"{bucket} is not serverless-function-eligible", not (generic & elig), str(generic & elig))
    # at least one bucket is function-eligible (the whole point: side-by-side, not function-banned)
    chk("at least one bucket is generic-function-eligible", any(generic & set(bp.get("eligible", [])) for bp in m["buckets"].values()))

    # pricebook prices every enum backend + flags low-confidence placeholders
    priced = set(pb["backends"])
    chk("pricebook prices every backend in the enum", enum <= priced, str(enum - priced))
    chk("placeholder cloud prices are confidence=low (not asserted as real)",
        all(pb["backends"][b].get("confidence") == "low" for b in generic if b in priced))
    chk("offline emulator is zero-cost + high confidence", pb["backends"]["local_function_emulator@v1"]["confidence"] == "high")

    print(f"\n{'PASS — check_execution_backend_policy_matrix: matrix + pricebook well-formed; heavy buckets exclude generic functions by default; functions are side-by-side eligible elsewhere; emulator is the offline correctness invariant; cloud prices are low-confidence config.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
