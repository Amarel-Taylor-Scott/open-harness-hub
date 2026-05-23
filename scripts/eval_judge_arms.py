#!/usr/bin/env python3
"""Evaluation harness — compare LLM judge arms side-by-side.

For each sample in `data/<vertical>-samples/`, runs the vertical's
pipeline under multiple judge arms and reports:
  - deterministic baseline (always works, no model)
  - ollama (if Ollama is reachable on OLLAMA_HOST)
  - anthropic (if ANTHROPIC_API_KEY is set)
  - openai (if OPENAI_API_KEY is set)

Outputs a CSV + a markdown summary so reviewers can see which arm
agrees with which on the same input.

Usage:
  python3 scripts/eval_judge_arms.py
  python3 scripts/eval_judge_arms.py --vertical esg
  python3 scripts/eval_judge_arms.py --max-samples 1

Env vars:
  OLLAMA_HOST, OLLAMA_MODEL
  ANTHROPIC_API_KEY, OH_ANTHROPIC_MODEL
  OPENAI_API_KEY, OH_OPENAI_MODEL
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_pipeline import run_pipeline, load_catalog


PIPELINES = {
    "esg":        ("pipeline/supplier-policy-grading",       "data/supplier-disclosure-samples", "supplier_disclosure_pack", {"supplier_tier":"T3","lead_company_code_ref":"knowledge-pack/lead-company-code-stub"}),
    "radiology":  ("pipeline/radiology-report-grading",      "data/radiology-samples",            "report",                  {"modality":"CT","body_part":"chest","patient_risk_class":"low"}),
    "contract":   ("pipeline/contract-clause-review",        "data/contract-samples",             "contract_text",           {"contract_type":"MSA","jurisdiction":"DE","lead_company_playbook_ref":"knowledge-pack/contract-law-clauses"}),
    "appsec":     ("pipeline/code-security-review",          "data/code-review-samples",          "code_bundle",             {"language":"python","framework":"flask"}),
    "gxp":        ("pipeline/gxp-validation-review",         "data/gxp-samples",                   "validation_packet",      {"system_class":"GxP"}),
    "climate":    ("pipeline/climate-disclosure-review",     "data/climate-samples",              "disclosure",              {"company_sector":"manufacturing","fiscal_year":"2025"}),
}


def detect_arms() -> list[str]:
    arms = ["deterministic"]
    # Try Ollama
    try:
        import urllib.request
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        with urllib.request.urlopen(f"{host}/api/tags", timeout=1) as r:
            if r.status == 200:
                arms.append("ollama")
    except Exception:
        pass
    if os.environ.get("ANTHROPIC_API_KEY"):
        arms.append("anthropic")
    if os.environ.get("OPENAI_API_KEY"):
        arms.append("openai")
    return arms


def run_arm(arm: str, pipeline_id: str, pipeline: dict, inputs: dict) -> dict:
    """Run one pipeline under one judge arm. Return summary dict."""
    saved_arm = os.environ.get("OH_JUDGE_ARM")
    os.environ["OH_JUDGE_ARM"] = arm
    try:
        started = time.monotonic()
        result = run_pipeline(pipeline, inputs, simulate=False)
        elapsed = round(time.monotonic() - started, 2)
        judge_step = next((s for s in result["trace"] if s["ref"] == "processor/llm-judge"), None)
        judge_out = (judge_step or {}).get("output") or {}
        by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for step in result["trace"]:
            if step["kind"] == "rule_pack":
                for h in step["output"].get("fired") or []:
                    by_sev[h["severity"]] = by_sev.get(h["severity"], 0) + 1
        return {
            "arm": arm,
            "elapsed_s": elapsed,
            "judge_score": judge_out.get("score"),
            "judge_method": judge_out.get("method") or judge_out.get("method_label"),
            "rationale_first_200": (judge_out.get("rationale") or "")[:200],
            "deterministic_baseline_score": (judge_out.get("deterministic_baseline") or {}).get("score"),
            "rule_pack_critical": by_sev["critical"],
            "rule_pack_high":     by_sev["high"],
            "rule_pack_medium":   by_sev["medium"],
            "rule_pack_low":      by_sev["low"],
            "success_aggregate":  result.get("success_aggregate"),
        }
    finally:
        if saved_arm is None:
            os.environ.pop("OH_JUDGE_ARM", None)
        else:
            os.environ["OH_JUDGE_ARM"] = saved_arm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vertical", default=None, choices=list(PIPELINES.keys()))
    ap.add_argument("--max-samples", type=int, default=None)
    ap.add_argument("--out-csv",  default="data/judge-arm-comparison.csv")
    ap.add_argument("--out-md",   default="data/judge-arm-comparison.md")
    args = ap.parse_args()

    arms = detect_arms()
    print(f"\nJudge arms detected: {', '.join(arms)}\n")

    catalog = load_catalog()
    verticals = [args.vertical] if args.vertical else list(PIPELINES.keys())

    rows = []
    for v in verticals:
        pipeline_id, samples_dir, input_key, extra = PIPELINES[v]
        pipeline = catalog.get(pipeline_id)
        if pipeline is None:
            print(f"  ⚠ {pipeline_id} not in catalog — skipping {v}")
            continue
        samples = sorted(Path(samples_dir).glob("*.json"))
        if args.max_samples:
            samples = samples[:args.max_samples]
        for sample_path in samples:
            sample = json.loads(sample_path.read_text())
            inputs = {input_key: sample, **extra}
            print(f"  {v}: {sample_path.name}")
            for arm in arms:
                summary = run_arm(arm, pipeline_id, pipeline, inputs)
                summary["vertical"] = v
                summary["sample"]   = sample_path.name
                rows.append(summary)
                print(f"    [{arm:14s}] score={summary['judge_score']}  elapsed={summary['elapsed_s']}s  method={summary['judge_method']}")

    # Write CSV
    if rows:
        fieldnames = ["vertical","sample","arm","judge_score","deterministic_baseline_score","judge_method","elapsed_s","rule_pack_critical","rule_pack_high","rule_pack_medium","rule_pack_low","success_aggregate","rationale_first_200"]
        Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        print(f"\nCSV → {args.out_csv}")

        # Markdown summary
        md = [f"# Judge-arm comparison\n\nArms run: {', '.join(arms)}\n\n"]
        md.append("| vertical | sample | arm | score | baseline | elapsed | C | H | M | L |\n")
        md.append("|---|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            md.append(f"| {r['vertical']} | {r['sample'][:30]} | {r['arm']} | {r['judge_score']} | {r['deterministic_baseline_score']} | {r['elapsed_s']}s | {r['rule_pack_critical']} | {r['rule_pack_high']} | {r['rule_pack_medium']} | {r['rule_pack_low']} |\n")
        Path(args.out_md).write_text("".join(md))
        print(f"MD  → {args.out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
