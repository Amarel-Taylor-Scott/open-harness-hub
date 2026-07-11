#!/usr/bin/env python3
"""Run one daily component-production pass end to end."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from scripts.db.daily_partition_load_audit import build_daily_partition_load_audit
from scripts.factory.daily_showcase_pipeline_templates import generate_showcase_templates
from scripts.factory.daily_thousand_component_seeds import run_daily_batch
from scripts.factory.showcase_candidate_coverage import build_showcase_coverage
from scripts.factory.showcase_gap_component_seeds import generate_gap_component_rows


DEFAULT_SCENARIOS = "catalog/knowledge-packs/data/daily-showcase-pipeline-patterns/showcase-scenarios.jsonl"


def _today() -> str:
    return dt.date.today().isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _row_count(summary: dict[str, Any], family: str) -> int:
    row_counts = summary.get("row_counts")
    if not isinstance(row_counts, dict):
        return 0
    return int(row_counts.get(family, 0) or 0)


def run_daily_production(
    *,
    run_date: str,
    output_dir: str | Path,
    target_count: int = 1000,
    matrix: str = "combined",
    showcase_count: int = 10,
    scenario_path: str | Path = DEFAULT_SCENARIOS,
    include_gap_fill: bool = True,
) -> dict[str, Any]:
    """Generate component candidates, showcase templates, coverage, gaps, and load audit."""
    out = Path(output_dir)
    component_dir = out / "component-batch"
    showcase_dir = out / "showcase-pipelines"
    coverage_dir = out / "showcase-coverage"
    gap_dir = out / "showcase-gap-components"
    load_audit_dir = out / "load-audit"
    run_id = f"daily-production-{run_date}"

    component_summary = run_daily_batch(
        output_dir=component_dir,
        target_count=target_count,
        matrix=matrix,
    )
    showcase_summary = generate_showcase_templates(
        scenario_path=scenario_path,
        output_dir=showcase_dir,
        count=showcase_count,
        run_id=run_id,
    )
    coverage_summary = build_showcase_coverage(
        template_dir=showcase_dir / "templates",
        normalized_objects=component_dir / "rows" / "normalized-objects.jsonl",
        output_dir=coverage_dir,
    )

    partitions: list[str] = [str(component_dir)]
    gap_summary: dict[str, Any] = {
        "ok": True,
        "skipped": True,
        "reason": "gap fill disabled or no coverage gaps",
        "seed_count": 0,
        "row_counts": {},
    }
    missing_request_count = int(coverage_summary.get("missing_request_count", 0) or 0)
    if include_gap_fill and missing_request_count > 0:
        gap_summary = generate_gap_component_rows(
            missing_requests=coverage_dir / "missing-component-requests.jsonl",
            output_dir=gap_dir,
        )
        if int(gap_summary.get("seed_count", 0) or 0) > 0:
            partitions.append(str(gap_dir))

    load_audit_summary = build_daily_partition_load_audit(
        partitions=partitions,
        output_dir=load_audit_dir,
        run_id=run_id,
    )

    generated_candidate_count = _row_count(component_summary, "normalized_object") + _row_count(gap_summary, "normalized_object")
    generated_index_record_count = _row_count(component_summary, "index_record") + _row_count(gap_summary, "index_record")
    generated_embedding_count = _row_count(component_summary, "object_embedding") + _row_count(gap_summary, "object_embedding")
    generated_review_ticket_count = _row_count(component_summary, "review_ticket") + _row_count(gap_summary, "review_ticket")

    summary = {
        "ok": bool(component_summary.get("ok"))
        and bool(showcase_summary.get("ok"))
        and bool(coverage_summary.get("ok"))
        and bool(gap_summary.get("ok"))
        and bool(load_audit_summary.get("ok")),
        "run_date": run_date,
        "run_id": run_id,
        "output_dir": str(out),
        "target_count": target_count,
        "matrix": matrix,
        "showcase_count": showcase_count,
        "generated": {
            "component_candidates": generated_candidate_count,
            "index_records": generated_index_record_count,
            "embedding_records": generated_embedding_count,
            "review_tickets": generated_review_ticket_count,
            "showcase_templates": int(showcase_summary.get("showcase_template_count", 0) or 0),
            "showcase_template_steps": int(showcase_summary.get("template_step_count", 0) or 0),
            "gap_component_candidates": int(gap_summary.get("seed_count", 0) or 0),
        },
        "coverage": {
            "template_count": coverage_summary.get("template_count"),
            "step_count": coverage_summary.get("step_count"),
            "covered_steps": coverage_summary.get("covered_steps"),
            "partial_steps": coverage_summary.get("partial_steps"),
            "missing_steps": coverage_summary.get("missing_steps"),
            "missing_request_count": coverage_summary.get("missing_request_count"),
        },
        "load_audit": {
            "audit_status": load_audit_summary.get("audit_status"),
            "raw_total": load_audit_summary.get("merge_report", {}).get("raw_total"),
            "unique_total": load_audit_summary.get("merge_report", {}).get("unique_total"),
            "duplicate_total": load_audit_summary.get("merge_report", {}).get("duplicate_total"),
            "unique_counts": load_audit_summary.get("merge_report", {}).get("unique_counts"),
            "preflight": load_audit_summary.get("preflight"),
            "load_sql": load_audit_summary.get("bulk_manifest", {}).get("load_sql"),
        },
        "paths": {
            "component_summary": str(component_dir / "daily-thousand-component-batch.json"),
            "showcase_summary": str(showcase_dir / "daily-showcase-pipeline-summary.json"),
            "coverage_summary": str(coverage_dir / "showcase-candidate-coverage-summary.json"),
            "gap_summary": str(gap_dir / "showcase-gap-component-summary.json"),
            "load_audit_summary": str(load_audit_dir / "summary.json"),
        },
        "notes": [
            "This is a staged daily production run; it does not promote candidates or apply SQL.",
            "The load audit is side-effect free until an operator runs the emitted SQL against Postgres.",
            "Gap-derived candidates remain review-gated.",
        ],
    }
    _write_json(out / "daily-production-run-summary.json", summary)
    return summary


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        result = run_daily_production(
            run_date="self-test",
            output_dir=tmp,
            target_count=40,
            matrix="core",
            showcase_count=5,
        )
        assert result["ok"] is True
        assert result["generated"]["component_candidates"] >= 40
        assert result["generated"]["showcase_templates"] == 5
        assert result["load_audit"]["audit_status"] == "staged_only"
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run-date", default=_today())
    parser.add_argument("--output-dir")
    parser.add_argument("--target-count", type=int, default=1000)
    parser.add_argument("--matrix", choices=["core", "expanded", "combined"], default="combined")
    parser.add_argument("--showcase-count", type=int, default=10)
    parser.add_argument("--scenario-path", default=DEFAULT_SCENARIOS)
    parser.add_argument("--skip-gap-fill", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    output_dir = args.output_dir or f"dist/daily-production-runs/{args.run_date}"
    result = run_daily_production(
        run_date=args.run_date,
        output_dir=output_dir,
        target_count=args.target_count,
        matrix=args.matrix,
        showcase_count=args.showcase_count,
        scenario_path=args.scenario_path,
        include_gap_fill=not args.skip_gap_fill,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
