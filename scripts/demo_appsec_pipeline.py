#!/usr/bin/env python3
"""End-to-end AppSec demo: run pipeline/code-security-review against 3
synthetic code bundles."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_pipeline import run_pipeline, load_catalog


def run_one(sample_path: Path, pipeline: dict) -> None:
    sample = json.loads(sample_path.read_text())
    inputs = {
        "code_bundle": sample,
        "language":    sample.get("language"),
        "framework":   sample.get("framework"),
    }
    result = run_pipeline(pipeline, inputs, simulate=False)

    print(f"\n{'=' * 76}")
    print(f"  {sample_path.name}")
    print(f"  language: {sample.get('language')}  •  framework: {sample.get('framework')}")
    print(f"  description: {sample.get('description', '')[:90]}")
    print(f"{'=' * 76}")
    print(f"  steps: {len(result['trace'])}  •  total ms: {sum(s['ms'] for s in result['trace']):.1f}")

    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for step in result["trace"]:
        if step["kind"] == "rule_pack":
            for h in step["output"].get("fired", []):
                summary[h["severity"]] = summary.get(h["severity"], 0) + 1

    print(f"  vuln findings: C:{summary['critical']:>2}  H:{summary['high']:>2}  M:{summary['medium']:>2}  L:{summary['low']:>2}")

    for step in result["trace"]:
        if step["kind"] != "rule_pack":
            continue
        fired = step["output"].get("fired", [])
        if not fired:
            continue
        print(f"\n  {step['ref']}:")
        for h in fired:
            print(f"    [{h['severity']:9s}] {h['rule_id']:38s} {h['category']}")

    print(f"\n  success_criteria:")
    for c in result.get("success_criteria") or []:
        icon = "✅" if c["pass"] else "❌"
        print(f"    {icon} {c['kind']:14s} {c.get('label', '')[:55]}")
    print(f"  aggregate_pass: {result.get('success_aggregate')}")


def main() -> int:
    catalog = load_catalog()
    pipeline = catalog.get("pipeline/code-security-review")
    if pipeline is None:
        print("pipeline/code-security-review not found", file=sys.stderr)
        return 1

    samples = sorted(Path("data/code-review-samples").glob("*.json"))
    for path in samples:
        run_one(path, pipeline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
