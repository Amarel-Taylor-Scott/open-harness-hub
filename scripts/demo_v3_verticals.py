#!/usr/bin/env python3
"""Demo: GDPR DSAR + HR EEOC + Trade compliance (verticals 11/12/13)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_pipeline import run_pipeline, load_catalog


def run_block(label, pipeline_id, samples_dir, input_key, extra=None):
    catalog = load_catalog()
    pipeline = catalog[pipeline_id]
    print(f"\n=== {label} ({pipeline_id}) ===")
    for p in sorted(Path(samples_dir).glob("*.json")):
        sample = json.loads(p.read_text())
        inputs = {input_key: sample, **(extra or {})}
        result = run_pipeline(pipeline, inputs, simulate=False)
        by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for step in result["trace"]:
            if step["kind"] == "rule_pack":
                for h in step["output"].get("fired") or []:
                    by_sev[h["severity"]] = by_sev.get(h["severity"], 0) + 1
        print(f"\n  {p.name[:55]:55s}  C:{by_sev['critical']:>2}  H:{by_sev['high']:>2}  M:{by_sev['medium']:>2}  L:{by_sev['low']:>2}")
        for step in result["trace"]:
            if step["kind"] != "rule_pack":
                continue
            fired = step["output"].get("fired") or []
            for h in fired:
                print(f"      [{h['severity']:9s}] {h['rule_id']:36s} {h['category']}")


def main() -> int:
    run_block("GDPR DSAR Review", "pipeline/gdpr-dsar-review", "data/gdpr-samples", "dsar_packet")
    run_block("HR Hiring Compliance Review", "pipeline/hr-hiring-compliance-review", "data/hr-samples", "posting")
    run_block("Trade Compliance Review", "pipeline/trade-compliance-review", "data/trade-samples", "transaction_packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
