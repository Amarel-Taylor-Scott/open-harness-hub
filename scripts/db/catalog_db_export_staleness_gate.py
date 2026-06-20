#!/usr/bin/env python3
"""Gate stale database-exported catalog row snapshots.

This check is intentionally read-only. It does not connect to Postgres and it
does not inspect live catalog YAML. It uses the row round-trip parity report, or
generates one from row directories, to decide whether a database-exported row
snapshot is fresh enough to treat as an operational row source.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import sys
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.db.catalog_row_roundtrip_parity import compare_row_dirs, row_dir_fingerprint
from scripts.db.catalog_row_integrity import ROW_FILES


DEFAULT_SEED_ROW_DIR = REPO / "dist" / "catalog-manifest-bridge"
DEFAULT_DB_ROW_DIR = REPO / "dist" / "catalog-db-export-rows-smoke"
DEFAULT_PARITY_REPORT = REPO / "dist" / "catalog-migration-smoke" / "catalog-row-roundtrip-parity.json"
DEFAULT_OUTPUT = REPO / "dist" / "catalog-migration-smoke" / "catalog-db-export-staleness-gate.json"


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def mismatched_rows(parity_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = parity_report.get("row_families")
    if not isinstance(rows, list):
        return []
    return [
        row
        for row in rows
        if isinstance(row, dict) and row.get("status") == "mismatched"
    ]


def _fingerprint_matches(parity_report: dict[str, Any], *, seed_row_dir: Path, db_row_dir: Path) -> bool:
    seed_fingerprint = parity_report.get("seed_row_fingerprint")
    db_fingerprint = parity_report.get("db_row_fingerprint")
    if not isinstance(seed_fingerprint, dict) or not isinstance(db_fingerprint, dict):
        return False
    return (
        seed_fingerprint.get("sha256") == row_dir_fingerprint(seed_row_dir).get("sha256")
        and db_fingerprint.get("sha256") == row_dir_fingerprint(db_row_dir).get("sha256")
    )


def build_staleness_gate_report(
    *,
    seed_row_dir: Path = DEFAULT_SEED_ROW_DIR,
    db_row_dir: Path = DEFAULT_DB_ROW_DIR,
    parity_report_path: Path = DEFAULT_PARITY_REPORT,
    output: Path | None = DEFAULT_OUTPUT,
    fail_on_warning: bool = False,
    advisory: bool = False,
) -> dict[str, Any]:
    parity_report = read_json(parity_report_path)
    parity_source = "existing_report"
    if parity_report is None:
        parity_report = compare_row_dirs(
            seed_row_dir=seed_row_dir,
            db_row_dir=db_row_dir,
            output=parity_report_path,
        )
        parity_source = "generated_report"
    elif not _fingerprint_matches(parity_report, seed_row_dir=seed_row_dir, db_row_dir=db_row_dir):
        parity_report = compare_row_dirs(
            seed_row_dir=seed_row_dir,
            db_row_dir=db_row_dir,
            output=parity_report_path,
        )
        parity_source = "regenerated_stale_fingerprint"

    severity_counts_raw = parity_report.get("severity_counts")
    severity_counts = (
        {str(key): int(value) for key, value in severity_counts_raw.items() if isinstance(value, int)}
        if isinstance(severity_counts_raw, dict)
        else {}
    )
    blocked_severities = {"error"}
    if fail_on_warning:
        blocked_severities.add("warning")

    blocking_count = sum(severity_counts.get(severity, 0) for severity in blocked_severities)
    parity_ok = bool(parity_report.get("ok"))
    fresh = parity_ok and blocking_count == 0
    status = "fresh" if fresh else "stale"
    mismatches = mismatched_rows(parity_report)
    mismatch_counts = {
        str(row.get("row_family")): {
            "seed_count": row.get("seed_count"),
            "db_count": row.get("db_count"),
            "missing_from_db": row.get("missing_from_db"),
            "extra_in_db": row.get("extra_in_db"),
        }
        for row in mismatches
    }

    report = {
        "ok": True if advisory else fresh,
        "would_pass": fresh,
        "status": status,
        "generated_at": utc_now(),
        "advisory": advisory,
        "fail_on_warning": fail_on_warning,
        "seed_row_dir": str(seed_row_dir),
        "db_row_dir": str(db_row_dir),
        "parity_report": str(parity_report_path),
        "parity_source": parity_source,
        "parity_fingerprint_matched": parity_source == "existing_report",
        "parity_ok": parity_ok,
        "severity_counts": dict(sorted(Counter(severity_counts).items())),
        "blocked_severities": sorted(blocked_severities),
        "mismatched_row_families": [str(row.get("row_family")) for row in mismatches],
        "mismatch_counts": mismatch_counts,
        "recommended_next_step": (
            "Run scripts/db/catalog_db_export_smoke_refresh_plan.py, reload bridge rows into a local/staging "
            "Postgres database, export fresh database rows, and rerun round-trip parity."
            if not fresh
            else "No refresh required; database-exported rows round-trip the seed bridge rows."
        ),
        "safety_notes": [
            "This gate does not connect to Postgres.",
            "It does not read or mutate catalog YAML files.",
            "Use --advisory inside dry-run smoke; omit --advisory when gating promotion or release jobs.",
        ],
    }
    if output is not None:
        write_json(output, report)
    return report


def run_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="ohh-export-staleness-gate-") as tmp:
        root = Path(tmp)
        seed = root / "seed"
        db = root / "db"
        seed.mkdir()
        db.mkdir()
        for filename in ROW_FILES.values():
            (seed / filename).write_text("", encoding="utf-8")
            (db / filename).write_text("", encoding="utf-8")
        (seed / "context_objects.jsonl").write_text(
            json.dumps({"context_object_id": "ctx://example/one"}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        parity = root / "parity.json"
        parity.write_text(
            json.dumps({
                "ok": False,
                "severity_counts": {"error": 1},
                "row_families": [
                    {
                        "row_family": "context_objects",
                        "status": "mismatched",
                        "seed_count": 2,
                        "db_count": 1,
                        "missing_from_db": 1,
                        "extra_in_db": 0,
                    }
                ],
            }),
            encoding="utf-8",
        )
        hard = build_staleness_gate_report(
            parity_report_path=parity,
            seed_row_dir=seed,
            db_row_dir=db,
            output=None,
        )
        if hard["ok"] or hard["would_pass"] or hard["status"] != "stale":
            print(json.dumps(hard, indent=2, sort_keys=True))
            return 1
        advisory = build_staleness_gate_report(
            parity_report_path=parity,
            seed_row_dir=seed,
            db_row_dir=db,
            output=None,
            advisory=True,
        )
        if not advisory["ok"] or advisory["would_pass"] or advisory["status"] != "stale":
            print(json.dumps(advisory, indent=2, sort_keys=True))
            return 1
    print(json.dumps({"ok": True, "self_test": "catalog_db_export_staleness_gate"}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gate stale database-exported catalog row snapshots.")
    parser.add_argument("--seed-row-dir", type=Path, default=DEFAULT_SEED_ROW_DIR)
    parser.add_argument("--db-row-dir", type=Path, default=DEFAULT_DB_ROW_DIR)
    parser.add_argument("--parity-report", type=Path, default=DEFAULT_PARITY_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--advisory", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    report = build_staleness_gate_report(
        seed_row_dir=args.seed_row_dir,
        db_row_dir=args.db_row_dir,
        parity_report_path=args.parity_report,
        output=args.output,
        fail_on_warning=args.fail_on_warning,
        advisory=args.advisory,
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
