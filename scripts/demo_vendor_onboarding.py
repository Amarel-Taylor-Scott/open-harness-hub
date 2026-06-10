#!/usr/bin/env python3
"""Vendor onboarding kitchen-sink demo: cross-vertical chained pipeline.

Runs pipeline/full-vendor-due-diligence against synthetic vendor packets.
The pipeline chains ESG + AppSec + Legal grading and rolls up the
verdicts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_pipeline import run_pipeline, load_catalog


def run_one(sample_path: Path, pipeline: dict) -> None:
    sample = json.loads(sample_path.read_text())
    result = run_pipeline(pipeline, {"vendor_packet": sample}, simulate=False)

    print(f"\n{'=' * 78}")
    print(f"  {sample_path.name}")
    print(f"  vendor: {sample.get('vendor_name')}  •  tier: {sample.get('tier')}  •  jurisdiction: {sample.get('jurisdiction')}")
    print(f"{'=' * 78}")

    for step in result["trace"]:
        if step["kind"] != "pipeline":
            continue
        out = step["output"] or {}
        print(f"\n  [{step['step_id']:14s}] {step['ref']:42s}  steps={out.get('sub_step_count')}  findings={out.get('sub_findings_total')}  pass={out.get('sub_aggregate')}")
        for c in out.get("sub_criteria") or []:
            icon = "✅" if c.get("pass") else "❌"
            print(f"      {icon} {c.get('kind','?'):14s} {c.get('label','')[:55]}")

    print(f"\n  AGGREGATE")
    for c in result.get("success_criteria") or []:
        icon = "✅" if c.get("pass") else "❌"
        sev = c.get("severity") or "-"
        print(f"    {icon} [{sev:9s}] {c.get('label', '')[:65]}")
    print(f"\n  overall_pass: {result.get('success_aggregate')}")


def main() -> int:
    catalog = load_catalog()
    pipeline = catalog.get("pipeline/full-vendor-due-diligence")
    if pipeline is None:
        print("pipeline/full-vendor-due-diligence not found", file=sys.stderr)
        return 1
    samples = sorted(Path("data/vendor-onboarding-samples").glob("*.json"))
    if not samples:
        print("no vendor-onboarding samples found", file=sys.stderr)
        return 1
    for path in samples:
        run_one(path, pipeline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
