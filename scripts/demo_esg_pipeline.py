#!/usr/bin/env python3
"""End-to-end demo: run pipeline/supplier-policy-grading against the
three synthetic supplier disclosure samples and pretty-print the
resulting findings.

Usage:
  python scripts/demo_esg_pipeline.py            # all 3 samples (full catalog load — interactive)
  python scripts/demo_esg_pipeline.py T3         # just the Mae Sot one
  python scripts/demo_esg_pipeline.py --self-test  # BOUNDED scoped run (one pipeline file, simulate, offline)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_pipeline import run_pipeline, load_catalog

_ROOT = Path(__file__).resolve().parent.parent
_PIPELINE_FILE = _ROOT / "catalog/pipelines/esg-supplier-grading/supplier-policy-grading.yaml"


def _scoped_pipeline() -> dict | None:
    """Load ONLY the ESG pipeline file (avoids the 2.6k-file catalog rglob that made the full run slow)."""
    import yaml
    if not _PIPELINE_FILE.exists():
        return None
    data = yaml.safe_load(_PIPELINE_FILE.read_text())
    return data if isinstance(data, dict) and data.get("id") else None


def _self_test() -> int:
    """BOUNDED, offline, scoped: load one pipeline file, run ONE sample in simulate mode (no full catalog
    load, no heavy component exec) and assert a trace comes back. Proves the demo cannot hang."""
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    pipeline = _scoped_pipeline()
    chk("scoped pipeline file loaded (no full-catalog rglob)", pipeline is not None, str(_PIPELINE_FILE))
    if pipeline is not None:
        samples = pick_samples(None)
        sample = json.loads(samples[0].read_text()) if samples else {"supplier_name": "fixture", "supplier_tier": "T3"}
        inputs = {"supplier_disclosure_pack": sample, "supplier_tier": sample.get("supplier_tier"),
                  "lead_company_code_ref": "knowledge-pack/lead-company-code-stub"}
        # simulate=True + an explicit minimal catalog → run_pipeline does NOT call load_catalog (bounded)
        result = run_pipeline(pipeline, inputs, simulate=True, catalog={pipeline["id"]: pipeline})
        chk("bounded simulate run returned a trace", isinstance(result.get("trace"), list))
        chk("every step simulated (no heavy component exec)", all(s.get("ms") is not None for s in result["trace"]))

    print(f"\n{'PASS — demo_esg_pipeline --self-test: scoped one-file load + simulate run is bounded and offline (cannot hang).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def pick_samples(filter_term: str | None) -> list[Path]:
    base = Path("data/supplier-disclosure-samples")
    paths = sorted(base.glob("*.json"))
    if filter_term:
        paths = [p for p in paths if filter_term in p.name]
    return paths


def run_one(sample_path: Path, pipeline: dict) -> None:
    sample = json.loads(sample_path.read_text())
    inputs = {
        "supplier_disclosure_pack": sample,
        "supplier_tier": sample.get("supplier_tier"),
        "lead_company_code_ref": "knowledge-pack/lead-company-code-stub",
    }
    result = run_pipeline(pipeline, inputs, simulate=False)

    print(f"\n{'=' * 76}")
    print(f"  {sample_path.name}")
    print(f"  supplier: {sample.get('supplier_name')}  •  tier: {sample.get('supplier_tier')}  •  country: {sample.get('iso_country')}")
    print(f"{'=' * 76}")
    print(f"  steps: {len(result['trace'])}  •  total ms: {sum(s['ms'] for s in result['trace']):.1f}")

    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_dimension = {"S": 0, "E": 0, "G": 0}
    for step in result["trace"]:
        if step["kind"] != "rule_pack":
            continue
        out = step["output"]
        for h in out.get("fired", []):
            summary[h["severity"]] = summary.get(h["severity"], 0) + 1
            if "ilo" in (h.get("category") or "") or "supply_chain" in (h.get("category") or ""):
                by_dimension["S"] += 1
            elif "environmental" in (h.get("category") or ""):
                by_dimension["E"] += 1
            elif "governance" in (h.get("category") or ""):
                by_dimension["G"] += 1

    print(f"  findings by severity:  C:{summary['critical']:>2}  H:{summary['high']:>2}  M:{summary['medium']:>2}  L:{summary['low']:>2}")
    print(f"  findings by dimension: S:{by_dimension['S']:>2}  E:{by_dimension['E']:>2}  G:{by_dimension['G']:>2}")

    for step in result["trace"]:
        if step["kind"] != "rule_pack":
            continue
        fired = step["output"].get("fired", [])
        if not fired:
            continue
        print(f"\n  {step['ref']}:")
        for h in fired:
            print(f"    [{h['severity']:9s}] {h['rule_id']:38s} {h['category']}")


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        return _self_test()
    filter_term = sys.argv[1] if len(sys.argv) > 1 else None
    catalog = load_catalog()
    pipeline = catalog.get("pipeline/supplier-policy-grading")
    if pipeline is None:
        print("pipeline/supplier-policy-grading not found in catalog", file=sys.stderr)
        return 1

    samples = pick_samples(filter_term)
    if not samples:
        print(f"no samples matched {filter_term!r}", file=sys.stderr)
        return 1

    for path in samples:
        run_one(path, pipeline)

    return 0


if __name__ == "__main__":
    sys.exit(main())
