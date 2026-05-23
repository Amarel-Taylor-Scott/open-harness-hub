#!/usr/bin/env python3
"""Demo: GO/NO-GO checklist gates — WHO SSC, FAA before-takeoff, MSHA pre-shift, PSM PSSR."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_pipeline import run_pipeline, load_catalog


def run_block(label, pipeline_id, samples, input_key):
    catalog = load_catalog()
    pipeline = catalog[pipeline_id]
    print(f"\n=== {label} ({pipeline_id}) ===")
    for sample_path in samples:
        sample = json.loads(Path(sample_path).read_text())
        result = run_pipeline(pipeline, {input_key: sample}, simulate=False)
        gate = next((s for s in result["trace"] if s.get("ref") == "processor/checklist-evaluator"), None)
        if not gate:
            print(f"  {Path(sample_path).name}: NO GATE STEP")
            continue
        out = gate["output"]
        verdict = out["verdict"]
        unverified = out.get("unverified_count", "?")
        total = out.get("step_count", "?")
        triggers = out.get("nogo_triggers", [])
        verdict_str = f"\033[32m{verdict.upper():5s}\033[0m" if verdict == "go" else f"\033[31m{verdict.upper():5s}\033[0m"
        print(f"  {Path(sample_path).name[:40]:40s} {verdict_str}  verified {total - unverified}/{total}  triggers: {len(triggers)}")
        for t in triggers:
            print(f"      [nogo trigger] {t[:120]}")


def main() -> int:
    run_block("WHO Surgical Safety Checklist",
              "pipeline/who-surgical-safety-gate",
              ["data/checklist-samples/who-ssc-clean.json", "data/checklist-samples/who-ssc-flagged.json"],
              "preinduction_packet")
    run_block("FAA Part 91 Before-Takeoff",
              "pipeline/faa-preflight-gate",
              ["data/checklist-samples/faa-before-takeoff-clean.json", "data/checklist-samples/faa-before-takeoff-flagged.json"],
              "preflight_packet")
    run_block("MSHA Pre-Shift Exam",
              "pipeline/msha-preshift-exam",
              ["data/checklist-samples/msha-preshift-clean.json", "data/checklist-samples/msha-preshift-flagged.json"],
              "preshift_packet")
    run_block("PSM Pre-Startup Safety Review",
              "pipeline/pssr-startup-gate",
              ["data/checklist-samples/pssr-clean.json", "data/checklist-samples/pssr-flagged.json"],
              "pssr_packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
