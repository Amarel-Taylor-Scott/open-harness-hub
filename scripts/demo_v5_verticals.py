#!/usr/bin/env python3
"""Demo: Construction OSHA + NERC CIP + Maritime IMO + Transfer Pricing (verticals 18-21)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_pipeline import run_pipeline, load_catalog


def run_block(label, pipeline_id, samples_dir, input_key):
    catalog = load_catalog()
    pipeline = catalog[pipeline_id]
    print(f"\n=== {label} ({pipeline_id}) ===")
    for p in sorted(Path(samples_dir).glob("*.json")):
        sample = json.loads(p.read_text())
        result = run_pipeline(pipeline, {input_key: sample}, simulate=False)
        by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for step in result["trace"]:
            if step["kind"] == "rule_pack":
                for h in step["output"].get("fired") or []:
                    by_sev[h["severity"]] = by_sev.get(h["severity"], 0) + 1
        print(f"\n  {p.name[:55]:55s}  C:{by_sev['critical']:>2}  H:{by_sev['high']:>2}  M:{by_sev['medium']:>2}  L:{by_sev['low']:>2}")
        for step in result["trace"]:
            if step["kind"] != "rule_pack":
                continue
            for h in step["output"].get("fired") or []:
                print(f"      [{h['severity']:9s}] {h['rule_id']:38s} {h['category']}")


def main() -> int:
    run_block("Construction Safety (OSHA)", "pipeline/construction-safety-review",    "data/construction-samples", "site_packet")
    run_block("NERC CIP",                    "pipeline/nerc-cip-compliance-review",    "data/energy-samples",       "bes_packet")
    run_block("Maritime Safety (IMO)",       "pipeline/maritime-safety-review",        "data/maritime-samples",     "vessel_packet")
    run_block("Transfer Pricing (OECD)",     "pipeline/transfer-pricing-review",       "data/tax-samples",          "tp_packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
