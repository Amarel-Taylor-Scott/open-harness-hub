#!/usr/bin/env python3
"""Compare seed-derived bridge rows with database-exported rows.

This check answers a different question from search comparison:

* catalog_row_source_compare.py asks whether search behavior is similar;
* catalog_row_roundtrip_parity.py asks whether row families themselves match.

It is read-only and does not connect to Postgres. Use it after loading bridge
rows into a database and exporting them back out with catalog_db_export_plan.py.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
from collections import Counter
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.db.catalog_row_integrity import ROW_FILES, read_jsonl


DEFAULT_SEED_ROW_DIR = _resource("dist") / "catalog-manifest-bridge"
DEFAULT_DB_ROW_DIR = _resource("dist") / "catalog-db-export-rows-smoke"
DEFAULT_OUTPUT = _resource("dist") / "catalog-migration-smoke" / "catalog-row-roundtrip-parity.json"

IGNORE_ROW_FAMILIES = {
    # Import batch IDs are intentionally time/run-specific. Import records are
    # checked separately by integrity and migration gates; exact row equality
    # would make every dry run look different even when component truth matches.
    "manifest_import_batches",
    "manifest_import_records",
}


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def row_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_dir_fingerprint(row_dir: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    for row_family, filename in sorted(ROW_FILES.items()):
        path = row_dir / filename
        file_hash = file_digest(path)
        size = path.stat().st_size if path.exists() else None
        entry = {
            "row_family": row_family,
            "file": filename,
            "exists": path.exists(),
            "size": size,
            "sha256": file_hash,
        }
        files.append(entry)
        digest.update(canonical_json(entry).encode("utf-8"))
    return {
        "row_dir": str(row_dir),
        "sha256": digest.hexdigest(),
        "files": files,
    }


def row_counter(path: Path) -> tuple[Counter[str], list[dict[str, Any]], bool]:
    if not path.exists():
        return Counter(), [], False
    rows = read_jsonl(path)
    return Counter(row_hash(row) for row in rows), rows, True


def sample_missing(left: Counter[str], right: Counter[str], rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    wanted = left - right
    samples: list[dict[str, Any]] = []
    for row in rows:
        digest = row_hash(row)
        if wanted[digest] <= 0:
            continue
        samples.append({
            "hash": digest,
            "id": row.get("id")
                or row.get("component_id")
                or row.get("context_object_id")
                or row.get("rubric_dimension_id")
                or row.get("mask_contract_id")
                or row.get("transformer_contract_id"),
            "row": row,
        })
        wanted[digest] -= 1
        if len(samples) >= limit:
            break
    return samples


def compare_row_dirs(
    *,
    seed_row_dir: Path = DEFAULT_SEED_ROW_DIR,
    db_row_dir: Path = DEFAULT_DB_ROW_DIR,
    output: Path | None = DEFAULT_OUTPUT,
    ignored_row_families: set[str] | None = None,
) -> dict[str, Any]:
    ignored = ignored_row_families if ignored_row_families is not None else IGNORE_ROW_FAMILIES
    row_families: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for row_family, filename in sorted(ROW_FILES.items()):
        seed_path = seed_row_dir / filename
        db_path = db_row_dir / filename
        seed_counter, seed_rows, seed_exists = row_counter(seed_path)
        db_counter, db_rows, db_exists = row_counter(db_path)
        missing_from_db = seed_counter - db_counter
        extra_in_db = db_counter - seed_counter
        status = "ignored" if row_family in ignored else "matched"
        if row_family not in ignored and (missing_from_db or extra_in_db or seed_exists != db_exists):
            status = "mismatched"
            severity = "error"
            if not db_exists and not seed_rows:
                severity = "warning"
            issues.append({
                "severity": severity,
                "code": "row_family_roundtrip_mismatch",
                "row_family": row_family,
                "seed_file_exists": seed_exists,
                "db_file_exists": db_exists,
                "seed_count": len(seed_rows),
                "db_count": len(db_rows),
                "missing_from_db": sum(missing_from_db.values()),
                "extra_in_db": sum(extra_in_db.values()),
                "missing_samples": sample_missing(seed_counter, db_counter, seed_rows),
                "extra_samples": sample_missing(db_counter, seed_counter, db_rows),
            })
        row_families.append({
            "row_family": row_family,
            "status": status,
            "seed_file": str(seed_path),
            "db_file": str(db_path),
            "seed_file_exists": seed_exists,
            "db_file_exists": db_exists,
            "seed_count": len(seed_rows),
            "db_count": len(db_rows),
            "missing_from_db": sum(missing_from_db.values()),
            "extra_in_db": sum(extra_in_db.values()),
        })

    severity_counts = Counter(str(issue.get("severity") or "unknown") for issue in issues)
    report = {
        "ok": int(severity_counts.get("error", 0)) == 0,
        "generated_at": utc_now(),
        "seed_row_dir": str(seed_row_dir),
        "db_row_dir": str(db_row_dir),
        "seed_row_fingerprint": row_dir_fingerprint(seed_row_dir),
        "db_row_fingerprint": row_dir_fingerprint(db_row_dir),
        "row_family_count": len(row_families),
        "ignored_row_families": sorted(ignored),
        "severity_counts": dict(sorted(severity_counts.items())),
        "row_families": row_families,
        "issues": issues,
        "notes": [
            "This verifier compares row files exactly after canonical JSON normalization.",
            "It does not connect to Postgres and does not inspect catalog YAML.",
            "Run it after exporting database rows; stale smoke exports may legitimately fail until refreshed.",
        ],
    }
    if output is not None:
        write_json(output, report)
    return report


def run_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="ohh-row-parity-") as tmp:
        root = Path(tmp)
        seed = root / "seed"
        db = root / "db"
        seed.mkdir()
        db.mkdir()
        for filename in ROW_FILES.values():
            (seed / filename).write_text("", encoding="utf-8")
            (db / filename).write_text("", encoding="utf-8")
        row = {"id": "component/example", "type": "tool"}
        (seed / "components.jsonl").write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
        (db / "components.jsonl").write_text(json.dumps({"type": "tool", "id": "component/example"}, sort_keys=True) + "\n", encoding="utf-8")
        report = compare_row_dirs(seed_row_dir=seed, db_row_dir=db, output=None, ignored_row_families=set())
        if not report["ok"]:
            print(json.dumps(report, indent=2, sort_keys=True))
            return 1
    print("[self-test] catalog row round-trip parity passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare seed bridge rows against database-exported rows.")
    parser.add_argument("--seed-row-dir", type=Path, default=DEFAULT_SEED_ROW_DIR)
    parser.add_argument("--db-row-dir", type=Path, default=DEFAULT_DB_ROW_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    report = compare_row_dirs(seed_row_dir=args.seed_row_dir, db_row_dir=args.db_row_dir, output=args.output)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
