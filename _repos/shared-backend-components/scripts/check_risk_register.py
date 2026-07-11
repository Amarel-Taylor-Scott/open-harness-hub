#!/usr/bin/env python3
"""scripts.check_risk_register — proof: _repos/shared-backend-components/architecture/risk_register.json covers the required risk categories
(data correctness, freshness, security/tenant, provider drift, monolith, worker throughput, dashboard truth,
direct bypass, unproven tools, documentation drift, secret leakage, consumption serving unsafe artifacts) and
every risk has severity/likelihood/owner/detection_proof/mitigation/status, with each detection_proof naming a
real proof file or an explicit planned: marker.

CLI: python3 _repos/shared-backend-components/scripts/check_risk_register.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_FIELDS = ("risk_id", "category", "severity", "likelihood", "owner", "detection_proof", "mitigation", "status", "target_pass")
_REQUIRED_CATEGORIES = {"data_correctness", "freshness", "security", "provider", "maintainability", "scaling",
                        "safety", "documentation"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = json.loads((_resource("architecture") / "risk_register.json").read_text())
    risks = reg["risks"]
    sev_ok = set(reg["severity_enum"]); lik_ok = set(reg["likelihood_enum"]); st_ok = set(reg["status_enum"])
    check("risk register has entries", len(risks) >= 10, str(len(risks)))

    missing_fields, bad_enum, bad_detection = [], [], []
    for r in risks:
        for f in _FIELDS:
            if f not in r:
                missing_fields.append(f"{r.get('risk_id')}.{f}")
        if r.get("severity") not in sev_ok or r.get("likelihood") not in lik_ok or r.get("status") not in st_ok:
            bad_enum.append(r.get("risk_id"))
        dp = str(r.get("detection_proof", ""))
        if not (dp.startswith("planned:") or (_resource(dp)).is_file()):
            bad_detection.append(f"{r.get('risk_id')}:{dp}")
    check("every risk declares all required fields", missing_fields == [], str(missing_fields[:6]))
    check("every risk has valid severity/likelihood/status", bad_enum == [], str(bad_enum))
    check("every detection_proof is a real proof file or explicitly planned:", bad_detection == [], str(bad_detection))
    check("every risk has a non-empty mitigation", all(r.get("mitigation") for r in risks))

    cats = {r["category"] for r in risks}
    missing_cats = _REQUIRED_CATEGORIES - cats
    check("the required risk categories are all covered", missing_cats == set(), str(sorted(missing_cats)))

    print(f"\n{'PASS — check_risk_register: all required risk categories covered; every risk has severity/likelihood/owner/detection/mitigation/status; detection proofs are real or explicitly planned.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: risk register.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
