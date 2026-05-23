#!/usr/bin/env python3
"""End-to-end demo: run pipeline/contract-clause-review against 3
synthetic contract samples.

Third proof point that the architecture is industry-agnostic — same
6-step chain handles ESG (CSDDD) + healthcare (RADS / Fleischner) +
legal (contract clauses).

Usage:
  python scripts/demo_contract_pipeline.py
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
        "contract_text":             sample,
        "contract_type":             sample.get("contract_type"),
        "jurisdiction":              sample.get("jurisdiction"),
        "lead_company_playbook_ref": "knowledge-pack/contract-law-clauses",
    }
    result = run_pipeline(pipeline, inputs, simulate=False)

    print(f"\n{'=' * 76}")
    print(f"  {sample_path.name}")
    print(f"  type: {sample.get('contract_type')}  •  jurisdiction: {sample.get('jurisdiction')}")
    print(f"  parties: {', '.join(sample.get('parties') or [])}")
    print(f"{'=' * 76}")
    print(f"  steps: {len(result['trace'])}  •  total ms: {sum(s['ms'] for s in result['trace']):.1f}")

    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for step in result["trace"]:
        if step["kind"] == "rule_pack":
            for h in step["output"].get("fired", []):
                summary[h["severity"]] = summary.get(h["severity"], 0) + 1

    print(f"  red-flag findings: C:{summary['critical']:>2}  H:{summary['high']:>2}  M:{summary['medium']:>2}  L:{summary['low']:>2}")

    for step in result["trace"]:
        if step["kind"] != "rule_pack":
            continue
        fired = step["output"].get("fired", [])
        if not fired:
            continue
        print(f"\n  {step['ref']}:")
        for h in fired:
            print(f"    [{h['severity']:9s}] {h['rule_id']:32s} {h['category']}")


def main() -> int:
    catalog = load_catalog()
    pipeline = catalog.get("pipeline/contract-clause-review")
    if pipeline is None:
        print("pipeline/contract-clause-review not found", file=sys.stderr)
        return 1

    samples = sorted(Path("data/contract-samples").glob("*.json"))
    if not samples:
        print("no contract samples found", file=sys.stderr)
        return 1

    for path in samples:
        run_one(path, pipeline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
