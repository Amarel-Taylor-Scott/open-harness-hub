#!/usr/bin/env python3
"""Demo: GxP + climate + threat-intel pipelines (verticals 5/6/7).

Runs the new vertical pipelines against synthetic samples.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_pipeline import run_pipeline, load_catalog


def run_one(sample_path: Path, pipeline_id: str, pipeline: dict, input_key: str, extra: dict | None = None) -> None:
    sample = json.loads(sample_path.read_text())
    inputs = {input_key: sample, **(extra or {})}
    result = run_pipeline(pipeline, inputs, simulate=False)
    by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for step in result["trace"]:
        if step["kind"] == "rule_pack":
            for h in step["output"].get("fired") or []:
                by_sev[h["severity"]] = by_sev.get(h["severity"], 0) + 1
    print(f"\n  {sample_path.name[:55]:55s}  C:{by_sev['critical']:>2}  H:{by_sev['high']:>2}  M:{by_sev['medium']:>2}  L:{by_sev['low']:>2}  total {sum(by_sev.values())}")
    for step in result["trace"]:
        if step["kind"] != "rule_pack":
            continue
        fired = step["output"].get("fired") or []
        for h in fired:
            print(f"      [{h['severity']:9s}] {h['rule_id']:36s} {h['category']}")


def main() -> int:
    catalog = load_catalog()
    print("\n=== GxP Validation Review ===")
    pipeline = catalog["pipeline/gxp-validation-review"]
    for p in sorted(Path("data/gxp-samples").glob("*.json")):
        run_one(p, "pipeline/gxp-validation-review", pipeline, "validation_packet", {"system_class": "GxP"})

    print("\n=== Climate Disclosure Review ===")
    pipeline = catalog["pipeline/climate-disclosure-review"]
    for p in sorted(Path("data/climate-samples").glob("*.json")):
        run_one(p, "pipeline/climate-disclosure-review", pipeline, "disclosure",
                {"company_sector": "manufacturing", "fiscal_year": "2025"})

    print("\n=== Threat-Intel IOC + TTP Review ===")
    pipeline = catalog["pipeline/threat-intel-ioc-review"]
    for p in sorted(Path("data/threat-intel-samples").glob("*.json")):
        run_one(p, "pipeline/threat-intel-ioc-review", pipeline, "report_text",
                {"incident_class": "ransomware_intrusion"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
