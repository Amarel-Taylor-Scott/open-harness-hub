#!/usr/bin/env python3
"""Summarize daily production runs and recommend the next run plan."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    next_run = report["next_run_recommendation"]
    lines = [
        "# Daily Production Schedule Report",
        "",
        f"- Runs analyzed: {report['run_count']}",
        f"- Total staged component candidates: {report['totals']['component_candidates']}",
        f"- Total showcase pipelines: {report['totals']['showcase_templates']}",
        f"- Total index records: {report['totals']['index_records']}",
        f"- Total review tickets: {report['totals']['review_tickets']}",
        f"- Average coverage rate: {report['averages']['coverage_rate']:.3f}",
        f"- Average duplicate rate: {report['averages']['duplicate_rate']:.3f}",
        "",
        "## Next Run",
        "",
        f"- Run date: {next_run['run_date']}",
        f"- Target count: {next_run['target_count']}",
        f"- Matrix: {next_run['matrix']}",
        f"- Showcase count: {next_run['showcase_count']}",
        f"- Gap fill: {next_run['include_gap_fill']}",
        f"- Reason: {next_run['reason']}",
        "",
        "```bash",
        next_run["command"],
        "```",
        "",
        "## Runs",
        "",
        "| Date | Candidates | Showcases | Covered | Partial | Missing | Duplicate rate | Preflight |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in report["runs"]:
        lines.append(
            "| {run_date} | {component_candidates} | {showcase_templates} | {covered_steps} | {partial_steps} | {missing_steps} | {duplicate_rate:.3f} | {preflight_ok} |".format(
                **row
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def discover_run_summaries(root: str | Path) -> list[Path]:
    return sorted(Path(root).glob("*/daily-production-run-summary.json"))


def _run_row(path: Path) -> dict[str, Any]:
    summary = _read_json(path)
    generated = summary.get("generated") if isinstance(summary.get("generated"), dict) else {}
    coverage = summary.get("coverage") if isinstance(summary.get("coverage"), dict) else {}
    load_audit = summary.get("load_audit") if isinstance(summary.get("load_audit"), dict) else {}
    preflight = load_audit.get("preflight") if isinstance(load_audit.get("preflight"), dict) else {}
    raw_total = int(load_audit.get("raw_total") or 0)
    duplicate_total = int(load_audit.get("duplicate_total") or 0)
    step_count = int(coverage.get("step_count") or 0)
    covered_steps = int(coverage.get("covered_steps") or 0)
    return {
        "path": str(path),
        "ok": bool(summary.get("ok")),
        "run_date": str(summary.get("run_date") or path.parent.name),
        "target_count": int(summary.get("target_count") or 0),
        "matrix": str(summary.get("matrix") or ""),
        "showcase_count": int(summary.get("showcase_count") or 0),
        "component_candidates": int(generated.get("component_candidates") or 0),
        "gap_component_candidates": int(generated.get("gap_component_candidates") or 0),
        "index_records": int(generated.get("index_records") or 0),
        "embedding_records": int(generated.get("embedding_records") or 0),
        "review_tickets": int(generated.get("review_tickets") or 0),
        "showcase_templates": int(generated.get("showcase_templates") or 0),
        "showcase_template_steps": int(generated.get("showcase_template_steps") or 0),
        "step_count": step_count,
        "covered_steps": covered_steps,
        "partial_steps": int(coverage.get("partial_steps") or 0),
        "missing_steps": int(coverage.get("missing_steps") or 0),
        "missing_request_count": int(coverage.get("missing_request_count") or 0),
        "raw_total": raw_total,
        "unique_total": int(load_audit.get("unique_total") or 0),
        "duplicate_total": duplicate_total,
        "duplicate_rate": (duplicate_total / raw_total) if raw_total else 0.0,
        "coverage_rate": (covered_steps / step_count) if step_count else 0.0,
        "preflight_ok": bool(preflight.get("ok")),
        "preflight_issue_count": int(preflight.get("issue_count") or 0),
        "audit_status": str(load_audit.get("audit_status") or ""),
    }


def _next_date(rows: list[dict[str, Any]], explicit: str | None = None) -> str:
    if explicit:
        return explicit
    dates = [_parse_date(str(row["run_date"])) for row in rows]
    dates = [date for date in dates if date is not None]
    if not dates:
        return dt.date.today().isoformat()
    return (max(dates) + dt.timedelta(days=1)).isoformat()


def _target_ladder(current: int) -> int:
    if current < 1000:
        return 1000
    if current < 2500:
        return 2500
    if current < 5000:
        return 5000
    return current


def _recommend_next(rows: list[dict[str, Any]], next_run_date: str | None, max_target: int) -> dict[str, Any]:
    run_date = _next_date(rows, explicit=next_run_date)
    if not rows:
        target_count = min(max_target, 1000)
        matrix = "core"
        reason = "No prior runs were found, so start with the conservative core matrix."
        showcase_count = 5
        include_gap_fill = True
    else:
        last = rows[-1]
        duplicate_rate = float(last["duplicate_rate"])
        coverage_rate = float(last["coverage_rate"])
        target_count = int(last["target_count"]) or 1000
        matrix = str(last["matrix"] or "combined")
        showcase_count = int(last["showcase_count"] or 10)
        include_gap_fill = int(last["missing_request_count"]) > 0

        if not last["ok"] or not last["preflight_ok"] or int(last["preflight_issue_count"]) > 0:
            target_count = max(1000, min(target_count, max_target))
            matrix = "core"
            showcase_count = max(5, min(showcase_count, 10))
            include_gap_fill = False
            reason = "The last run had validation or preflight issues; hold volume and switch to core until clean."
        elif duplicate_rate > 0.05:
            target_count = max(1000, min(target_count, max_target))
            matrix = "expanded" if matrix == "combined" else "core"
            reason = "The duplicate rate was high; hold volume and rotate matrix to reduce overlap."
        elif coverage_rate < 0.85 or int(last["missing_steps"]) > 0:
            target_count = max(1000, min(target_count, max_target))
            matrix = "combined"
            showcase_count = min(25, max(showcase_count, 10))
            include_gap_fill = True
            reason = "Coverage is below target; keep volume steady and prioritize gap fill."
        else:
            target_count = min(max_target, _target_ladder(target_count))
            matrix = "combined"
            showcase_count = min(25, max(showcase_count, 10))
            include_gap_fill = True
            reason = "The last run was clean enough to scale to the next target tier."

    command = (
        "python3 -m scripts.factory.daily_production_run "
        f"--run-date {run_date} "
        f"--output-dir dist/daily-production-runs/{run_date} "
        f"--target-count {target_count} "
        f"--matrix {matrix} "
        f"--showcase-count {showcase_count}"
    )
    if not include_gap_fill:
        command += " --skip-gap-fill"
    return {
        "run_date": run_date,
        "target_count": target_count,
        "matrix": matrix,
        "showcase_count": showcase_count,
        "include_gap_fill": include_gap_fill,
        "reason": reason,
        "command": command,
    }


def build_daily_schedule_report(
    *,
    runs_root: str | Path = "dist/daily-production-runs",
    output_dir: str | Path,
    next_run_date: str | None = None,
    max_target: int = 5000,
) -> dict[str, Any]:
    paths = discover_run_summaries(runs_root)
    rows = [_run_row(path) for path in paths]
    rows.sort(key=lambda row: row["run_date"])
    totals = {
        "component_candidates": sum(int(row["component_candidates"]) for row in rows),
        "index_records": sum(int(row["index_records"]) for row in rows),
        "embedding_records": sum(int(row["embedding_records"]) for row in rows),
        "review_tickets": sum(int(row["review_tickets"]) for row in rows),
        "showcase_templates": sum(int(row["showcase_templates"]) for row in rows),
        "gap_component_candidates": sum(int(row["gap_component_candidates"]) for row in rows),
        "unique_staged_rows": sum(int(row["unique_total"]) for row in rows),
    }
    run_count = len(rows)
    averages = {
        "coverage_rate": (sum(float(row["coverage_rate"]) for row in rows) / run_count) if run_count else 0.0,
        "duplicate_rate": (sum(float(row["duplicate_rate"]) for row in rows) / run_count) if run_count else 0.0,
        "component_candidates_per_run": (totals["component_candidates"] / run_count) if run_count else 0.0,
        "showcase_templates_per_run": (totals["showcase_templates"] / run_count) if run_count else 0.0,
    }
    report = {
        "ok": True,
        "runs_root": str(runs_root),
        "run_count": run_count,
        "runs": rows,
        "totals": totals,
        "averages": averages,
        "next_run_recommendation": _recommend_next(rows, next_run_date=next_run_date, max_target=max_target),
        "notes": [
            "This report plans the next run; it does not execute generation.",
            "Use the recommended command only after reviewing prior run quality and disk budget.",
            "High-risk candidates and SQL loads remain review-gated.",
        ],
    }
    out = Path(output_dir)
    _write_json(out / "daily-production-schedule-report.json", report)
    _write_markdown(out / "daily-production-schedule-report.md", report)
    return report


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "runs"
        run_dir = root / "2026-05-29"
        _write_json(
            run_dir / "daily-production-run-summary.json",
            {
                "ok": True,
                "run_date": "2026-05-29",
                "target_count": 1000,
                "matrix": "combined",
                "showcase_count": 10,
                "generated": {
                    "component_candidates": 1011,
                    "index_records": 5055,
                    "embedding_records": 1011,
                    "review_tickets": 211,
                    "showcase_templates": 10,
                    "showcase_template_steps": 76,
                    "gap_component_candidates": 11,
                },
                "coverage": {
                    "step_count": 76,
                    "covered_steps": 65,
                    "partial_steps": 11,
                    "missing_steps": 0,
                    "missing_request_count": 11,
                },
                "load_audit": {
                    "raw_total": 59136,
                    "unique_total": 59122,
                    "duplicate_total": 14,
                    "audit_status": "staged_only",
                    "preflight": {"ok": True, "issue_count": 0},
                },
            },
        )
        report = build_daily_schedule_report(runs_root=root, output_dir=Path(tmp) / "report")
        assert report["run_count"] == 1
        assert report["totals"]["component_candidates"] == 1011
        assert report["next_run_recommendation"]["target_count"] == 2500
        assert Path(tmp, "report", "daily-production-schedule-report.md").exists()
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--runs-root", default="dist/daily-production-runs")
    parser.add_argument("--output-dir", default="dist/daily-production-schedule")
    parser.add_argument("--next-run-date")
    parser.add_argument("--max-target", type=int, default=5000)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    result = build_daily_schedule_report(
        runs_root=args.runs_root,
        output_dir=args.output_dir,
        next_run_date=args.next_run_date,
        max_target=args.max_target,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
