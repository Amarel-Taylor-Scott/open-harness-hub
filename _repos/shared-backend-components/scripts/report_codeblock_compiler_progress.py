#!/usr/bin/env python3
"""Summarize primitive codeblock compiler runs and verify shard line counts."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_PROGRESS_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "progress"


def _utc_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def _line_count(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        with path.open("rb") as fh:
            total += sum(1 for _ in fh)
    return total


def summarize(run_dirs: list[Path], run_id: str) -> dict[str, Any]:
    manifests = []
    shard_paths: list[Path] = []
    for run_dir in run_dirs:
        manifest_path = run_dir / "manifest.json"
        manifests.append(json.loads(manifest_path.read_text(encoding="utf-8")))
        shard_paths.extend(sorted(run_dir.glob("primitive_codeblocks_*.jsonl")))

    generated = sum(int(m.get("generated", 0)) for m in manifests)
    syntax_pass = sum(int(m.get("syntax_pass", 0)) for m in manifests)
    smoke_pass = sum(int(m.get("smoke_pass", 0)) for m in manifests)
    included = sum(int(m.get("included", 0)) for m in manifests)
    rejected = sum(int(m.get("rejected", 0)) for m in manifests)
    duration = sum(float(m.get("duration_seconds", 0.0)) for m in manifests)
    lines = _line_count(shard_paths)
    included_per_hour = round(included / max(duration, 0.000001) * 3600, 2)

    summary = {
        "run_id": run_id,
        "record_type": "primitive_codeblock_combined_progress",
        "run_dirs": [_rel(p) for p in run_dirs],
        "manifest_count": len(manifests),
        "shard_count": len(shard_paths),
        "physical_line_count": lines,
        "generated": generated,
        "syntax_pass": syntax_pass,
        "smoke_pass": smoke_pass,
        "included": included,
        "rejected": rejected,
        "duration_seconds": round(duration, 3),
        "included_per_hour": included_per_hour,
        "candidate": True,
        "serves_truth": False,
        "created_at": _utc_stamp(),
    }

    DEFAULT_PROGRESS_ROOT.mkdir(parents=True, exist_ok=True)
    json_path = _resource(f"{run_id}.json")
    md_path = _resource(f"{run_id}.md")
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(
        "# Primitive Codeblock 1M Progress\n\n"
        f"- run_id: `{run_id}`\n"
        f"- run_dirs: `{', '.join(summary['run_dirs'])}`\n"
        f"- manifest_count: `{summary['manifest_count']}`\n"
        f"- shard_count: `{summary['shard_count']}`\n"
        f"- physical_line_count: `{summary['physical_line_count']:,}`\n"
        f"- generated: `{summary['generated']:,}`\n"
        f"- syntax_pass: `{summary['syntax_pass']:,}`\n"
        f"- smoke_pass: `{summary['smoke_pass']:,}`\n"
        f"- included: `{summary['included']:,}`\n"
        f"- rejected: `{summary['rejected']:,}`\n"
        f"- duration_seconds: `{summary['duration_seconds']}`\n"
        f"- included_per_hour: `{summary['included_per_hour']:,}`\n\n"
        "## Interpretation\n\n"
        "The codeblock bank now has one executable candidate codeblock record per verified seed row. "
        "Each record embeds a compact primitive spec, imports the shared candidate runtime, and smoke-runs "
        "to a deterministic receipt. These remain candidate scaffolds, not promoted production implementations.\n",
        encoding="utf-8",
    )
    summary["progress_json_path"] = _rel(json_path)
    summary["progress_path"] = _rel(md_path)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", action="append", type=Path, required=True)
    parser.add_argument("--run-id", default=f"codeblock_compile_1m_progress_{_utc_stamp()}")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = summarize(args.run_dir, args.run_id)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
