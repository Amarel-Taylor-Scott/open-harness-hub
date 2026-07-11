#!/usr/bin/env python3
"""Benchmark and monitor the multi-lane primitive generation day.

Reads the per-lane verification manifests under
``data/dev-intel/primitive_factory/verified_candidates/<date-prefix>*/`` and
compares generation lanes (deterministic catalog intake, Ollama GLM/Kimi/Gemma
writers, Claude Fable ultracode workflow, 20k fleet) on verified / duplicate /
rejected counts. Every number is computed from manifests — never typed.

Emits a Markdown report plus an append-only JSONL receipt. Reporting only:
verified rows remain candidate-only (``serves_truth=false``); this script
promotes nothing.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402

VERIFIED_CANDIDATES_DIR = "data/dev-intel/primitive_factory/verified_candidates"
SATURATION_DIR = "data/dev-intel/primitive_saturation"
TESTING_RECEIPTS_PATH = "data/dev-intel/primitive_factory/ultracode_testing_daemon/testing_receipts.jsonl"
REPORT_DIR = "data/dev-intel/primitive_factory"
RECEIPT_NAME = "multilane_generation_receipts.jsonl"

# Lane classification by run-label suffix; the labels are minted by the intake
# builder (c8kdet/c8k1/ucNN) and the 2M goal loop (gNNNN).
LANE_RULES: tuple[tuple[str, str, str], ...] = (
    (r"-c8kdet$", "deterministic_catalog_intake", "Deterministic parser over primitive_pipeline_catalog_8000.md (zero model tokens)"),
    (r"-c8k1$", "ollama_catalog_expansion", "GLM/Kimi (and Gemma when unpaused) writers over catalog family shards"),
    (r"-uc\d+$", "claude_fable_ultracode", "Claude Fable workflow agents over intake briefs"),
    (r"-g\d+$", "fleet_20k", "2M-goal fleet shards (GLM/Kimi/Gemma)"),
)
OTHER_LANE = "other"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def _lane_for_label(label: str) -> str:
    for pattern, lane, _ in LANE_RULES:
        if re.search(pattern, label):
            return lane
    return OTHER_LANE


def collect_lanes(root: Path, date_prefix: str) -> dict[str, dict[str, Any]]:
    lanes: dict[str, dict[str, Any]] = {}
    for manifest_path in sorted(root.glob(f"{date_prefix}*/manifest.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        label = str(manifest.get("run_date") or manifest_path.parent.name)
        lane_key = _lane_for_label(label)
        lane = lanes.setdefault(
            lane_key,
            {"lane": lane_key, "run_labels": [], "source_rows": 0, "verified": 0, "duplicates": 0, "rejected": 0},
        )
        lane["run_labels"].append(label)
        lane["source_rows"] += int(manifest.get("source_row_count") or 0)
        lane["verified"] += int(manifest.get("verified_count") or 0)
        lane["duplicates"] += int(manifest.get("duplicate_count") or 0)
        lane["rejected"] += int(manifest.get("rejected_count") or 0)
    for lane in lanes.values():
        source_rows = lane["source_rows"]
        lane["verified_rate"] = round(lane["verified"] / source_rows, 4) if source_rows else 0.0
        lane["duplicate_rate"] = round(lane["duplicates"] / source_rows, 4) if source_rows else 0.0
        lane["run_label_count"] = len(lane["run_labels"])
    return lanes


def _last_testing_receipt(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    last: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                last = json.loads(line)
            except json.JSONDecodeError:
                continue
    return last


def render_report(date_prefix: str, lanes: dict[str, dict[str, Any]], testing_receipt: dict[str, Any], saturation_path: Path) -> str:
    lane_order = [key for _, key, _ in ((r, k, d) for r, k, d in LANE_RULES)] + [OTHER_LANE]
    descriptions = {key: desc for _, key, desc in LANE_RULES}
    total_verified = sum(lane["verified"] for lane in lanes.values())
    lines = [
        f"# Multi-Lane Primitive Generation Report — {date_prefix}",
        "",
        f"Generated: {_now()} · candidate-only reporting (`serves_truth=false`); verification never promotes truth.",
        "",
        f"Total verified candidates for `{date_prefix}*`: **{total_verified}** across {sum(lane['run_label_count'] for lane in lanes.values())} run labels.",
        "",
        "| lane | run labels | source rows | verified | verified rate | duplicates | dup rate | rejected |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for key in lane_order:
        lane = lanes.get(key)
        if not lane:
            continue
        lines.append(
            f"| {key} | {lane['run_label_count']} | {lane['source_rows']} | {lane['verified']} "
            f"| {lane['verified_rate']:.1%} | {lane['duplicates']} | {lane['duplicate_rate']:.1%} | {lane['rejected']} |"
        )
    lines += ["", "Lane meanings:", ""]
    for key in lane_order:
        if key in lanes and key in descriptions:
            lines.append(f"- `{key}` — {descriptions[key]}")
    if OTHER_LANE in lanes:
        lines.append(f"- `{OTHER_LANE}` — run labels not minted by the intake builder or the 2M goal loop")
    lines += [
        "",
        "Monitoring hooks:",
        "",
        f"- Saturation/savings: `{saturation_path}`" + (" (present)" if (_resource(saturation_path)).exists() else " (not yet written)"),
        (
            "- Lift regression (testing daemon): "
            + (
                f"`{testing_receipt.get('lift_regression')}` at {testing_receipt.get('ts')} "
                f"(verified_total_today={testing_receipt.get('verified_total_today')})"
                if testing_receipt
                else "no receipts yet"
            )
        ),
        "- Duplicate rate is the saturation signal: rising duplicates in a lane mean the lane is re-generating known edges — sprout or move on.",
        "",
    ]
    return "\n".join(lines)


def run_report(*, date_prefix: str, write: bool) -> dict[str, Any]:
    root = _resource(VERIFIED_CANDIDATES_DIR)
    lanes = collect_lanes(root, date_prefix)
    testing_receipt = _last_testing_receipt(_resource(TESTING_RECEIPTS_PATH))
    saturation_path = Path(SATURATION_DIR) / f"{date_prefix}_saturation.md"
    report = render_report(date_prefix, lanes, testing_receipt, saturation_path)
    receipt = {
        "record_type": "multilane_generation_receipt",
        "created_at": _now(),
        "date_prefix": date_prefix,
        "lanes": {
            key: {field: lane[field] for field in ("run_label_count", "source_rows", "verified", "duplicates", "rejected", "verified_rate")}
            for key, lane in sorted(lanes.items())
        },
        "total_verified": sum(lane["verified"] for lane in lanes.values()),
        "lift_regression": testing_receipt.get("lift_regression"),
        "candidate": True,
        "serves_truth": False,
    }
    if write:
        report_path = _resource(REPORT_DIR) / f"multilane_generation_report_{date_prefix}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report + "\n", encoding="utf-8")
        receipts_path = _resource(REPORT_DIR) / RECEIPT_NAME
        with receipts_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")
        receipt["report_path"] = str(report_path.relative_to(REPO_ROOT))
    return receipt


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fixtures = {
            "2000-01-01-c8kdet": {"source_row_count": 200, "verified_count": 200, "duplicate_count": 0, "rejected_count": 0},
            "2000-01-01-c8k1": {"source_row_count": 100, "verified_count": 80, "duplicate_count": 15, "rejected_count": 5},
            "2000-01-01-uc02": {"source_row_count": 600, "verified_count": 590, "duplicate_count": 10, "rejected_count": 0},
            "2000-01-01-g0001": {"source_row_count": 50, "verified_count": 40, "duplicate_count": 10, "rejected_count": 0},
        }
        for label, payload in fixtures.items():
            manifest_dir = root / label
            manifest_dir.mkdir(parents=True)
            (manifest_dir / "manifest.json").write_text(json.dumps({"run_date": label, **payload}), encoding="utf-8")
        lanes = collect_lanes(root, "2000-01-01")
        assert set(lanes) == {"deterministic_catalog_intake", "ollama_catalog_expansion", "claude_fable_ultracode", "fleet_20k"}
        assert lanes["deterministic_catalog_intake"]["verified_rate"] == 1.0
        assert lanes["ollama_catalog_expansion"]["duplicates"] == 15
        report = render_report("2000-01-01", lanes, {"lift_regression": "PASS", "ts": "2000-01-01T00:00:00Z"}, Path("nowhere.md"))
        assert "deterministic_catalog_intake" in report and "PASS" in report
        assert "910" in report  # total verified = 200+80+590+40
    print("OK: multilane generation report self-test passed (lane classification, rates, render).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date-prefix", default=_today_utc())
    parser.add_argument("--write", action="store_true", help="Write the Markdown report and append a receipt.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    receipt = run_report(date_prefix=args.date_prefix, write=args.write)
    print(json.dumps(receipt, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
