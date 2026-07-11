#!/usr/bin/env python3
"""scripts.check_worker_k8s_keda_mapping_docs — proof (C-FLEET-2): the K8s/KEDA mapping doc + the four
manifest templates exist and explain the load-bearing invariants (DB ledger = truth, KEDA = wake-up,
HPA 1->N vs KEDA 0->1, cooldownPeriod = ramp-down, preStop drain, atomic claim). Templates are scaffolds,
not live deploys.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_worker_k8s_keda_mapping_docs.py --self-test
"""
from __future__ import annotations

import argparse
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_DOC = _resource("docs") / "workers" / "k8s-keda-worker-mapping.md"
_TEMPLATES = [
    "infra/k8s/capability-worker-deployment.yaml.template",
    "infra/k8s/capability-worker-scaledobject.yaml.template",
    "infra/k8s/capability-worker-scaledjob.yaml.template",
    "infra/k8s/capability-worker-job.yaml.template",
]
_DOC_CONCEPTS = ["source of truth", "cooldownPeriod", "HPA", "KEDA", "preStop", "SKIP LOCKED", "atomic"]


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    chk("mapping doc exists", _DOC.exists())
    text = _DOC.read_text() if _DOC.exists() else ""
    for c in _DOC_CONCEPTS:
        chk(f"doc explains '{c}'", c.lower() in text.lower())

    for t in _TEMPLATES:
        fp = _resource(t)
        chk(f"template {t} exists", fp.exists())
        if fp.exists():
            body = fp.read_text()
            chk(f"{t} references the DB ledger (truth)", "ledger" in body.lower() or "task_queue" in body.lower())
            chk(f"{t} is a placeholder template (not a live manifest)", "${" in body)

    # the ScaledObject must scale to zero; the Deployment must carry an HPA + drain
    so = (_resource("infra/k8s/capability-worker-scaledobject.yaml.template")).read_text()
    chk("ScaledObject scales to zero (minReplicaCount: 0)", "minReplicaCount: 0" in so)
    chk("ScaledObject sets cooldownPeriod (ramp-down)", "cooldownPeriod" in so)
    dep = (_resource("infra/k8s/capability-worker-deployment.yaml.template")).read_text()
    chk("Deployment has HPA (1->N)", "HorizontalPodAutoscaler" in dep)
    chk("Deployment drains via preStop + grace period", "preStop" in dep and "terminationGracePeriodSeconds" in dep)

    print(f"\n{'PASS — check_worker_k8s_keda_mapping_docs: mapping doc + 4 templates present; invariants documented (ledger=truth, HPA 1->N / KEDA 0->1, cooldownPeriod ramp-down, preStop drain, SKIP LOCKED).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
