#!/usr/bin/env python3
"""Report one-call/one-primitive generation throughput.

This report intentionally separates three layers:

- model rows: one source row sent to one model call
- included candidates: extracted candidate JSON accepted from model output
- verified candidates: stricter source-backed candidate rows in the main bank

No row is promoted to truth here.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402

SINGLE_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "single_primitive_openwebui"
VERIFIED_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "verified_candidates"
REPORT_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "progress"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _manifest_generated_count(manifest: dict[str, Any]) -> int:
    if "generated_count" in manifest:
        return _safe_int(manifest.get("generated_count"))
    selected = _safe_int(manifest.get("selected_count"))
    errors = _safe_int(manifest.get("error_count"))
    return max(0, selected - errors)


def collect_single_runs(root: Path) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    totals = {
        "run_count": 0,
        "attempted_rows": 0,
        "generated_outputs": 0,
        "tested_rows": 0,
        "included_candidates": 0,
        "rejected_candidates": 0,
        "error_outputs": 0,
        "duration_seconds": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    by_provider: dict[str, dict[str, Any]] = {}
    for manifest_path in sorted(root.glob("*/manifest.json")):
        manifest = _read_json(manifest_path)
        if not manifest:
            continue
        selected = _safe_int(manifest.get("selected_count"))
        generated = _manifest_generated_count(manifest)
        included = _safe_int(manifest.get("included_count") or manifest.get("accepted_count"))
        rejected = _safe_int(manifest.get("rejected_count"))
        errors = _safe_int(manifest.get("error_count"))
        duration = _safe_float(manifest.get("duration_seconds"))
        usage = manifest.get("usage") if isinstance(manifest.get("usage"), dict) else {}
        provider = str(manifest.get("provider") or "unknown")
        model = str(manifest.get("model") or "unknown")
        run = {
            "manifest_path": _rel(manifest_path),
            "provider": provider,
            "model": model,
            "attempted_rows": selected,
            "generated_outputs": generated,
            "tested_rows": selected,
            "included_candidates": included,
            "rejected_candidates": rejected,
            "error_outputs": errors,
            "duration_seconds": duration,
            "included_per_hour": round(included / duration * 3600, 2) if duration > 0 else 0.0,
            "total_tokens": _safe_int(usage.get("total_tokens")),
        }
        runs.append(run)
        totals["run_count"] += 1
        totals["attempted_rows"] += selected
        totals["generated_outputs"] += generated
        totals["tested_rows"] += selected
        totals["included_candidates"] += included
        totals["rejected_candidates"] += rejected
        totals["error_outputs"] += errors
        totals["duration_seconds"] += duration
        totals["prompt_tokens"] += _safe_int(usage.get("prompt_tokens"))
        totals["completion_tokens"] += _safe_int(usage.get("completion_tokens"))
        totals["total_tokens"] += _safe_int(usage.get("total_tokens"))
        lane = by_provider.setdefault(
            f"{provider}:{model}",
            {
                "provider": provider,
                "model": model,
                "run_count": 0,
                "attempted_rows": 0,
                "generated_outputs": 0,
                "included_candidates": 0,
                "error_outputs": 0,
                "duration_seconds": 0.0,
            },
        )
        lane["run_count"] += 1
        lane["attempted_rows"] += selected
        lane["generated_outputs"] += generated
        lane["included_candidates"] += included
        lane["error_outputs"] += errors
        lane["duration_seconds"] += duration
    totals["included_per_hour"] = (
        round(totals["included_candidates"] / totals["duration_seconds"] * 3600, 2)
        if totals["duration_seconds"] > 0
        else 0.0
    )
    for lane in by_provider.values():
        duration = _safe_float(lane.get("duration_seconds"))
        lane["included_per_hour"] = (
            round(_safe_int(lane.get("included_candidates")) / duration * 3600, 2)
            if duration > 0
            else 0.0
        )
    return {
        "totals": totals,
        "by_provider_model": sorted(by_provider.values(), key=lambda row: (row["provider"], row["model"])),
        "runs": runs,
    }


def collect_verified_bank(root: Path) -> dict[str, Any]:
    manifest_count = 0
    verified_sum = 0
    jsonl_lines = 0
    unique: set[str] = set()
    for manifest_path in sorted(root.glob("*/manifest.json")):
        manifest_count += 1
        manifest = _read_json(manifest_path)
        verified_sum += _safe_int(manifest.get("verified_count"))
        verified_path = manifest_path.parent / "verified_candidates.jsonl"
        if not verified_path.exists():
            continue
        for line in verified_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            jsonl_lines += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            unique.add(str(row.get("primitive_id") or row.get("dedupe_key") or row.get("verification_id") or line[:80]))
    return {
        "manifest_count": manifest_count,
        "manifest_verified_sum": verified_sum,
        "jsonl_lines": jsonl_lines,
        "unique_ids_or_dedupe_keys": len(unique),
    }


def render_markdown(report: dict[str, Any]) -> str:
    totals = report["single_primitive_runs"]["totals"]
    verified = report["verified_bank"]
    lines = [
        "# Primitive Generation Progress",
        "",
        f"Generated: {report['created_at']} UTC",
        "",
        "Candidate-only report. `included_candidates` means accepted into extracted candidate JSONL; "
        "`verified_bank` means stricter source-backed candidate verification. Neither serves truth.",
        "",
        "## One-Call / One-Primitive Runs",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| runs | {totals['run_count']} |",
        f"| attempted rows | {totals['attempted_rows']} |",
        f"| generated outputs | {totals['generated_outputs']} |",
        f"| tested rows | {totals['tested_rows']} |",
        f"| included candidates | {totals['included_candidates']} |",
        f"| rejected candidates | {totals['rejected_candidates']} |",
        f"| error outputs | {totals['error_outputs']} |",
        f"| elapsed seconds | {totals['duration_seconds']:.3f} |",
        f"| included candidates / hour | {totals['included_per_hour']:.2f} |",
        f"| prompt tokens | {totals['prompt_tokens']} |",
        f"| completion tokens | {totals['completion_tokens']} |",
        f"| total tokens | {totals['total_tokens']} |",
        "",
        "## Provider / Model Lanes",
        "",
        "| provider:model | runs | attempted | generated | included | errors | seconds | included/hour |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for lane in report["single_primitive_runs"]["by_provider_model"]:
        lines.append(
            f"| {lane['provider']}:{lane['model']} | {lane['run_count']} | {lane['attempted_rows']} | "
            f"{lane['generated_outputs']} | {lane['included_candidates']} | {lane['error_outputs']} | "
            f"{lane['duration_seconds']:.3f} | {lane['included_per_hour']:.2f} |"
        )
    lines += [
        "",
        "## Verified Candidate Bank",
        "",
        "| metric | value |",
        "| --- | ---: |",
        f"| manifests | {verified['manifest_count']} |",
        f"| verified rows from manifests | {verified['manifest_verified_sum']} |",
        f"| verified JSONL lines | {verified['jsonl_lines']} |",
        f"| unique ids / dedupe keys | {verified['unique_ids_or_dedupe_keys']} |",
        "",
    ]
    return "\n".join(lines)


def build_report(*, write: bool) -> dict[str, Any]:
    report = {
        "record_type": "single_primitive_throughput_report",
        "created_at": _now(),
        "single_root": _rel(SINGLE_ROOT),
        "verified_root": _rel(VERIFIED_ROOT),
        "single_primitive_runs": collect_single_runs(SINGLE_ROOT),
        "verified_bank": collect_verified_bank(VERIFIED_ROOT),
        "candidate": True,
        "serves_truth": False,
    }
    if write:
        REPORT_ROOT.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        json_path = _resource(f"single_primitive_throughput_{stamp}.json")
        md_path = _resource(f"single_primitive_throughput_{stamp}.md")
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
        report["report_json_path"] = _rel(json_path)
        report["report_md_path"] = _rel(md_path)
    return report


def _self_test() -> int:
    report = {
        "created_at": "2099-01-01T00:00:00+00:00",
        "single_primitive_runs": {
            "totals": {
                "run_count": 1,
                "attempted_rows": 2,
                "generated_outputs": 1,
                "tested_rows": 2,
                "included_candidates": 1,
                "rejected_candidates": 0,
                "error_outputs": 1,
                "duration_seconds": 10.0,
                "included_per_hour": 360.0,
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
            "by_provider_model": [
                {
                    "provider": "openwebui",
                    "model": "gemma-4-coding",
                    "run_count": 1,
                    "attempted_rows": 2,
                    "generated_outputs": 1,
                    "included_candidates": 1,
                    "error_outputs": 1,
                    "duration_seconds": 10.0,
                    "included_per_hour": 360.0,
                }
            ],
        },
        "verified_bank": {
            "manifest_count": 1,
            "manifest_verified_sum": 3,
            "jsonl_lines": 3,
            "unique_ids_or_dedupe_keys": 3,
        },
    }
    text = render_markdown(report)
    ok = "included candidates / hour" in text and "360.00" in text and "verified JSONL lines" in text
    print("PASS - single primitive throughput report renders computed rates." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    report = build_report(write=args.write)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
