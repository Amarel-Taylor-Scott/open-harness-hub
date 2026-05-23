#!/usr/bin/env python3
"""End-to-end demo: run pipeline/radiology-report-grading against the
three synthetic radiology report samples.

Demonstrates that the same pipeline runner + the same primitives
(structured-to-prose, redact-pii-text, GREP rule packs, audit
trace) handle a completely different industry vertical with only
the rule pack, knowledge pack, rubric, and persona changing.

Usage:
  python scripts/demo_radiology_pipeline.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_pipeline import run_pipeline, load_catalog


def run_one(sample_path: Path, pipeline: dict) -> None:
    sample = json.loads(sample_path.read_text())
    inputs = {
        "report":             sample,
        "modality":           sample.get("modality"),
        "body_part":          sample.get("body_part"),
        "patient_risk_class": sample.get("patient_risk_class"),
    }
    result = run_pipeline(pipeline, inputs, simulate=False)

    print(f"\n{'=' * 76}")
    print(f"  {sample_path.name}")
    print(f"  modality: {sample.get('modality')}  •  body_part: {sample.get('body_part')}  •  risk: {sample.get('patient_risk_class')}")
    print(f"{'=' * 76}")
    print(f"  steps: {len(result['trace'])}  •  total ms: {sum(s['ms'] for s in result['trace']):.1f}")

    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    pii_count = 0
    for step in result["trace"]:
        if step["kind"] == "rule_pack":
            for h in step["output"].get("fired", []):
                summary[h["severity"]] = summary.get(h["severity"], 0) + 1
        if step["ref"] == "processor/redact-pii-text":
            pii_count = sum(step["output"].get("entity_counts_by_type", {}).values())

    print(f"  PII detected & redacted: {pii_count}")
    print(f"  rule findings by severity:  C:{summary['critical']:>2}  H:{summary['high']:>2}  M:{summary['medium']:>2}  L:{summary['low']:>2}")

    for step in result["trace"]:
        if step["kind"] != "rule_pack":
            continue
        fired = step["output"].get("fired", [])
        if not fired:
            continue
        print(f"\n  {step['ref']}:")
        for h in fired:
            print(f"    [{h['severity']:9s}] {h['rule_id']:42s} {h['category']}")


def main() -> int:
    catalog = load_catalog()
    pipeline = catalog.get("pipeline/radiology-report-grading")
    if pipeline is None:
        print("pipeline/radiology-report-grading not found", file=sys.stderr)
        return 1

    samples = sorted(Path("data/radiology-samples").glob("*.json"))
    if not samples:
        print("no radiology samples found", file=sys.stderr)
        return 1

    for path in samples:
        run_one(path, pipeline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
