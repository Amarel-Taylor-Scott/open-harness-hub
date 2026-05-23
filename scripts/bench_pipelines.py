#!/usr/bin/env python3
"""Auto-benchmark all vertical pipelines: clean must produce 0 critical, flagged ≥1 critical.

Exits non-zero if any pipeline regresses. Designed for CI gating.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_pipeline import run_pipeline, load_catalog


VERTICAL_BENCHES = [
    # (label, pipeline_id, samples_dir, input_key)
    ("Telco",          "pipeline/telco-compliance-review",         "data/telco-samples",          "telco_packet"),
    ("Gaming",         "pipeline/gaming-integrity-review",         "data/gaming-samples",         "gaming_packet"),
    ("Nuclear",        "pipeline/nuclear-safety-review",           "data/nuclear-samples",        "nuclear_packet"),
    ("Agriculture",    "pipeline/agriculture-compliance-review",   "data/agriculture-samples",    "ag_packet"),
    ("Customs",        "pipeline/customs-broker-review",           "data/customs-samples",        "entry_packet"),
    ("Space",          "pipeline/space-launch-review",             "data/space-launch-samples",   "launch_packet"),
    ("Cannabis",       "pipeline/cannabis-compliance-review",      "data/cannabis-samples",       "cannabis_packet"),
    ("Biosecurity",    "pipeline/biosecurity-review",              "data/biosecurity-samples",    "biosec_packet"),
    ("AI Governance",  "pipeline/ai-governance-audit",             "data/ai-governance-samples",  "ai_system_packet"),
    ("RCRA Waste",     "pipeline/rcra-waste-review",               "data/rcra-waste-samples",     "waste_packet"),
]


def count_critical(result: dict) -> int:
    n = 0
    for step in result["trace"]:
        if step.get("kind") == "rule_pack":
            for h in (step["output"].get("fired") or []):
                if h["severity"] == "critical":
                    n += 1
    return n


def main() -> int:
    catalog = load_catalog()
    failures = []
    print(f"{'Vertical':25s}  {'clean_crit':10s}  {'flag_crit':10s}  {'verdict':8s}")
    print("-" * 60)
    for label, pid, samples, key in VERTICAL_BENCHES:
        if pid not in catalog:
            failures.append((label, "pipeline missing"))
            print(f"{label:25s}  --          --          MISSING")
            continue
        pipeline = catalog[pid]
        clean = sorted(Path(samples).glob("*clean*.json"))
        flagged = sorted(Path(samples).glob("*flagged*.json"))
        clean_crit = 0
        for p in clean:
            sample = json.loads(p.read_text())
            res = run_pipeline(pipeline, {key: sample}, simulate=False)
            clean_crit += count_critical(res)
        flag_crit = 0
        for p in flagged:
            sample = json.loads(p.read_text())
            res = run_pipeline(pipeline, {key: sample}, simulate=False)
            flag_crit += count_critical(res)
        verdict = "OK"
        if clean_crit > 0:
            verdict = "FAIL"
            failures.append((label, f"clean sample triggered {clean_crit} critical"))
        if flag_crit == 0 and flagged:
            verdict = "FAIL"
            failures.append((label, "flagged sample produced 0 critical"))
        print(f"{label:25s}  {clean_crit:>10d}  {flag_crit:>10d}  {verdict:8s}")
    print()
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for label, reason in failures:
            print(f"  {label}: {reason}")
        return 1
    print(f"All {len(VERTICAL_BENCHES)} vertical pipelines pass clean=0 + flagged≥1 critical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
