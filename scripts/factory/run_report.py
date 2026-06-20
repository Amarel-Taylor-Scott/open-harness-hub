#!/usr/bin/env python3
"""Factory run reporter — writes provenance + cost + quality distribution
for each factory run to `dist/factory-runs/{run_id}/`.

Each run directory carries:
  - run.json         — top-level summary (walker, params, totals, costs)
  - walks/*.json     — raw walker outputs (one per source root)
  - drafts/*.yaml    — emitted drafts (mirrored copies, before _inbox)
  - rejected.json    — drafts that failed the quality gate, with reasons
  - dedup.json       — drafts skipped by semantic dedup, with best matches
  - REPORT.md        — human-readable summary suitable for PR description

This is the audit-trail layer: every draft in `catalog/_inbox/` can be
traced back to a specific run + walker call + source node, enabling
reproducibility and accountability at scale.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DIST_FACTORY_RUNS = ROOT / "dist" / "factory-runs"


@dataclass
class RunReport:
    run_id: str
    started_at: str
    walker_kind: str
    walker_inputs: dict[str, Any]
    nodes_walked: int = 0
    drafts_proposed: int = 0
    drafts_accepted_by_gate: int = 0
    drafts_rejected_by_gate: int = 0
    drafts_deduped: int = 0
    drafts_emitted_to_inbox: int = 0
    drafts_failed_validation: int = 0
    cost_estimate_usd: float = 0.0
    duration_s: float = 0.0
    warnings: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "walker_kind": self.walker_kind,
            "walker_inputs": self.walker_inputs,
            "totals": {
                "nodes_walked": self.nodes_walked,
                "drafts_proposed": self.drafts_proposed,
                "drafts_accepted_by_gate": self.drafts_accepted_by_gate,
                "drafts_rejected_by_gate": self.drafts_rejected_by_gate,
                "drafts_deduped": self.drafts_deduped,
                "drafts_emitted_to_inbox": self.drafts_emitted_to_inbox,
                "drafts_failed_validation": self.drafts_failed_validation,
            },
            "cost_estimate_usd": round(self.cost_estimate_usd, 4),
            "duration_s": round(self.duration_s, 2),
            "warnings": list(self.warnings),
        }
        if self.extra:
            d["extra"] = self.extra
        return d


def make_run_id() -> str:
    """Run IDs are sortable + globally unique: YYYYMMDDHHMMSS-<short-uuid>."""
    return time.strftime("%Y%m%d%H%M%S", time.gmtime()) + "-" + uuid.uuid4().hex[:8]


def make_run_dir(run_id: str) -> Path:
    d = DIST_FACTORY_RUNS / run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "walks").mkdir(exist_ok=True)
    (d / "drafts").mkdir(exist_ok=True)
    return d


def render_markdown_report(report: RunReport, run_dir: Path) -> str:
    rejected_path = run_dir / "rejected.json"
    dedup_path = run_dir / "dedup.json"
    n_rejected_kinds: dict[str, int] = {}
    n_dedup_against: dict[str, int] = {}
    if rejected_path.exists():
        try:
            rejs = json.loads(rejected_path.read_text(encoding="utf-8"))
            for r in rejs:
                for reason in r.get("reasons", []):
                    key = reason.split(":")[0][:60]
                    n_rejected_kinds[key] = n_rejected_kinds.get(key, 0) + 1
        except (json.JSONDecodeError, OSError):
            pass
    if dedup_path.exists():
        try:
            deds = json.loads(dedup_path.read_text(encoding="utf-8"))
            for d in deds:
                bm = d.get("best_match_id") or "<none>"
                n_dedup_against[bm] = n_dedup_against.get(bm, 0) + 1
        except (json.JSONDecodeError, OSError):
            pass

    t = report.to_dict()["totals"]
    lines = [
        f"# Factory run {report.run_id}",
        "",
        f"- **started_at**: {report.started_at}",
        f"- **walker_kind**: {report.walker_kind}",
        f"- **walker_inputs**: `{json.dumps(report.walker_inputs)}`",
        f"- **duration**: {report.duration_s:.1f}s",
        f"- **cost_estimate**: ${report.cost_estimate_usd:.4f} USD",
        "",
        "## Funnel",
        "",
        f"| stage | count |",
        f"|---|---|",
        f"| nodes_walked | {t['nodes_walked']} |",
        f"| drafts_proposed | {t['drafts_proposed']} |",
        f"| accepted by quality gate | {t['drafts_accepted_by_gate']} |",
        f"| rejected by quality gate | {t['drafts_rejected_by_gate']} |",
        f"| deduped against live catalog | {t['drafts_deduped']} |",
        f"| emitted to _inbox | {t['drafts_emitted_to_inbox']} |",
        f"| failed schema validation | {t['drafts_failed_validation']} |",
    ]
    if n_rejected_kinds:
        lines += [
            "",
            "## Quality-gate rejection reasons (top 10)",
            "",
            "| reason | count |",
            "|---|---|",
        ]
        for reason, count in sorted(n_rejected_kinds.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"| {reason} | {count} |")
    if n_dedup_against:
        lines += [
            "",
            "## Dedup hits (top 10)",
            "",
            "| existing component | duplicates suppressed |",
            "|---|---|",
        ]
        for art, count in sorted(n_dedup_against.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"| {art} | {count} |")
    if report.warnings:
        lines += [
            "",
            "## Warnings",
            "",
        ]
        for w in report.warnings:
            lines.append(f"- {w}")
    lines.append("")
    return "\n".join(lines)


def write_run_components(
    report: RunReport,
    *,
    walks: dict[str, dict] | None = None,
    drafts: list[dict] | None = None,
    rejected: list[dict] | None = None,
    deduped: list[dict] | None = None,
) -> Path:
    """Persist a complete factory-run report to dist/factory-runs/{run_id}/."""
    run_dir = make_run_dir(report.run_id)

    (run_dir / "run.json").write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if walks:
        for name, payload in walks.items():
            (run_dir / "walks" / f"{name}.json").write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
    if drafts:
        for i, d in enumerate(drafts):
            slug = (d.get("id") or f"draft-{i}").replace("/", "_").replace(" ", "-")[:80]
            (run_dir / "drafts" / f"{slug}.json").write_text(
                json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8"
            )
    if rejected:
        (run_dir / "rejected.json").write_text(
            json.dumps(rejected, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    if deduped:
        (run_dir / "dedup.json").write_text(
            json.dumps(deduped, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    (run_dir / "REPORT.md").write_text(render_markdown_report(report, run_dir), encoding="utf-8")
    return run_dir


# ─── CLI: list / view past runs ─────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="List or view past factory runs.")
    p.add_argument("--list", action="store_true", help="List all past runs in dist/factory-runs/")
    p.add_argument("--view", help="Print the REPORT.md of a specific run_id")
    args = p.parse_args(argv)

    if args.list:
        if not DIST_FACTORY_RUNS.exists():
            print("(no factory runs yet)")
            return 0
        runs = sorted([d.name for d in DIST_FACTORY_RUNS.iterdir() if d.is_dir()])
        for r in runs:
            run_json = DIST_FACTORY_RUNS / r / "run.json"
            if run_json.exists():
                try:
                    j = json.loads(run_json.read_text(encoding="utf-8"))
                    totals = j.get("totals", {})
                    print(f"  {r}  walker={j.get('walker_kind')}  emitted={totals.get('drafts_emitted_to_inbox')}/{totals.get('drafts_proposed')}")
                except json.JSONDecodeError:
                    print(f"  {r}  (corrupted)")
            else:
                print(f"  {r}  (no run.json)")
        return 0

    if args.view:
        report = DIST_FACTORY_RUNS / args.view / "REPORT.md"
        if not report.exists():
            sys.stderr.write(f"no REPORT.md at {report}\n")
            return 1
        sys.stdout.write(report.read_text(encoding="utf-8"))
        return 0

    p.error("--list or --view RUN_ID required")
    return 2


if __name__ == "__main__":
    sys.exit(_main())
