#!/usr/bin/env python3
"""Deduplicate the latest governed scrape/research run into the searchable candidate overlay.

This is a staging bridge, not promotion. It reads the latest continuous-scrape run, normalizes its foundry and
question-bank primitive candidates to the typed search-card surface, and appends each immutable primitive id once.
The source rows must already be ``candidate=true / serves_truth=false``; anything else is rejected.

The append file and its SQLite id catalog are crash-reconciled by output byte size. A crash after append but before
catalog commit therefore rebuilds the catalog from the durable JSONL rather than duplicating or losing the row.

    PYTHONPATH=. python3 scripts/ingest_continuous_scrape_candidates.py --sync
    PYTHONPATH=. python3 scripts/ingest_continuous_scrape_candidates.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_SBC = next((p for p in _HERE.parents if (p / "scripts" / "_repo_paths.py").exists()), _HERE.parents[1])
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import fcntl  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import sqlite3  # noqa: E402
import tempfile  # noqa: E402
from typing import Any, Iterable, Mapping, Sequence  # noqa: E402


BOUNDARY = {"candidate": True, "serves_truth": False}
DEFAULT_STATUS = resource("data") / "dev-intel" / "continuous_primitive_scrape_loop" / "latest_status.json"
DEFAULT_OUTPUT = resource("data") / "dev-intel" / "continuous_primitive_scrape_loop" / "searchable_candidates.jsonl"
DEFAULT_CATALOG = resource("data") / "dev-intel" / "continuous_primitive_scrape_loop" / "searchable_candidates.sqlite"
SOURCE_RELS = ("foundry_store/primitive_candidates.jsonl", "llm_primitive_candidates.jsonl")


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _digest(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _contract_edge(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Mapping):
        shape = str(value.get("shape") or "").strip()
        required = value.get("required") or []
        required_text = "+".join(str(item) for item in required) if isinstance(required, list) else ""
        return "+".join(part for part in (shape, required_text) if part)
    return ""


def normalize(row: Mapping[str, Any], *, run_id: str, source_file: str) -> dict[str, Any] | None:
    """Return one searchable candidate row, or None when the boundary/id contract is missing."""

    if row.get("candidate") is not True or row.get("serves_truth") is not False:
        return None
    primitive_id = str(row.get("primitive_id") or row.get("id") or "").strip()
    if not primitive_id:
        return None
    title = str(row.get("title") or row.get("name") or primitive_id).strip()
    blackbox = row.get("blackbox")
    if isinstance(blackbox, Mapping):
        blackbox = blackbox.get("does") or blackbox.get("description") or _stable_json(blackbox)
    blackbox = str(blackbox or row.get("purpose") or row.get("description") or "").strip()
    input_edge = str(row.get("input_edge") or "").strip() or _contract_edge(row.get("input_contract"))
    output_edge = str(row.get("output_edge") or "").strip() or _contract_edge(row.get("output_contract"))
    tags = [str(value) for value in (
        row.get("source_kind"), row.get("component_family"), row.get("stage"), row.get("record_type")
    ) if value]
    return {
        **dict(row),
        "primitive_id": primitive_id,
        "title": title,
        "blackbox": blackbox,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "capability_tags": sorted(set(tags)),
        "verification_level": "candidate",
        "proof_status": "unverified",
        "search_ingest": {"run_id": run_id, "source_file": source_file},
        **BOUNDARY,
    }


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.is_file():
        return
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield row


def _create_catalog(con: sqlite3.Connection) -> None:
    con.execute("CREATE TABLE IF NOT EXISTS ids(primitive_id TEXT PRIMARY KEY, payload_digest TEXT NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    con.commit()


def _rebuild_catalog(con: sqlite3.Connection, output: Path) -> int:
    con.execute("DELETE FROM ids")
    rows = []
    for row in _iter_jsonl(output):
        primitive_id = str(row.get("primitive_id") or "")
        if primitive_id:
            rows.append((primitive_id, _digest(row)))
    con.executemany("INSERT OR REPLACE INTO ids VALUES(?,?)", rows)
    size = output.stat().st_size if output.exists() else 0
    con.execute("INSERT OR REPLACE INTO meta VALUES('output_size',?)", (str(size),))
    con.commit()
    return len(rows)


def _ensure_catalog(con: sqlite3.Connection, output: Path) -> int:
    _create_catalog(con)
    row = con.execute("SELECT value FROM meta WHERE key='output_size'").fetchone()
    size = output.stat().st_size if output.exists() else 0
    if row is None or int(row[0]) != size:
        return _rebuild_catalog(con, output)
    return int(con.execute("SELECT count(*) FROM ids").fetchone()[0])


def _run_dir(status_path: Path) -> tuple[str, Path]:
    status = json.loads(status_path.read_text(encoding="utf-8"))
    run_id = str(status.get("run_id") or "").strip()
    run_dir = Path((status.get("outputs") or {}).get("run_dir") or "").expanduser()
    if not run_id or not run_dir.is_dir():
        raise ValueError(f"latest scrape status has no valid run: {status_path}")
    return run_id, run_dir


def sync_latest(*, status_path: Path = DEFAULT_STATUS, output: Path = DEFAULT_OUTPUT,
                catalog_path: Path = DEFAULT_CATALOG) -> dict[str, Any]:
    run_id, run_dir = _run_dir(status_path)
    candidates: dict[str, dict[str, Any]] = {}
    scanned = boundary_rejected = 0
    for rel in SOURCE_RELS:
        path = run_dir / rel
        for raw in _iter_jsonl(path):
            scanned += 1
            row = normalize(raw, run_id=run_id, source_file=rel)
            if row is None:
                boundary_rejected += 1
                continue
            primitive_id = row["primitive_id"]
            old = candidates.get(primitive_id)
            # Keep the more descriptive duplicate deterministically.
            score = sum(len(str(row.get(key) or "")) for key in ("title", "blackbox", "input_edge", "output_edge"))
            old_score = sum(len(str(old.get(key) or "")) for key in ("title", "blackbox", "input_edge", "output_edge")) if old else -1
            if score > old_score or (score == old_score and _stable_json(row) < _stable_json(old)):
                candidates[primitive_id] = row

    output.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = output.with_suffix(output.suffix + ".lock")
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        con = sqlite3.connect(catalog_path)
        try:
            existing_before = _ensure_catalog(con, output)
            con.execute("BEGIN IMMEDIATE")
            new_rows: list[dict[str, Any]] = []
            for primitive_id, row in sorted(candidates.items()):
                cursor = con.execute("INSERT OR IGNORE INTO ids VALUES(?,?)", (primitive_id, _digest(row)))
                if cursor.rowcount:
                    new_rows.append(row)
            if new_rows:
                with output.open("a", encoding="utf-8") as handle:
                    for row in new_rows:
                        handle.write(_stable_json(row) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
            output_size = output.stat().st_size if output.exists() else 0
            con.execute("INSERT OR REPLACE INTO meta VALUES('output_size',?)", (str(output_size),))
            con.commit()
            distinct_after = int(con.execute("SELECT count(*) FROM ids").fetchone()[0])
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return {"record_type": "continuous_scrape_search_ingest_receipt", "run_id": run_id,
            "source_rows_scanned": scanned, "unique_candidates_in_run": len(candidates),
            "new_searchable_candidates": len(new_rows), "boundary_rejected": boundary_rejected,
            "distinct_output_rows_before": existing_before, "distinct_output_rows_after": distinct_after,
            "output": str(output), **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory(prefix="scrape_candidate_ingest_") as temp:
        root = Path(temp)
        run = root / "run"; (run / "foundry_store").mkdir(parents=True)
        foundry = [
            {"primitive_id": "p:a", "name": "alpha", "purpose": "Alpha candidate", "input_contract": {"shape": "In"},
             "output_contract": {"shape": "Out"}, **BOUNDARY},
            {"primitive_id": "p:truth", "name": "bad", "candidate": True, "serves_truth": True},
        ]
        llm = [
            {"primitive_id": "p:a", "name": "alpha richer", "purpose": "A richer alpha candidate description",
             "input_contract": {"shape": "In"}, "output_contract": {"shape": "Out"}, **BOUNDARY},
            {"primitive_id": "p:b", "name": "beta", "purpose": "Beta candidate", "input_contract": {"shape": "BIn"},
             "output_contract": {"shape": "BOut"}, **BOUNDARY},
        ]
        for path, rows in ((run / "foundry_store/primitive_candidates.jsonl", foundry),
                           (run / "llm_primitive_candidates.jsonl", llm)):
            path.write_text("".join(_stable_json(row) + "\n" for row in rows), encoding="utf-8")
        status = root / "latest.json"
        status.write_text(json.dumps({"run_id": "run:test", "outputs": {"run_dir": str(run)}}))
        output, catalog = root / "searchable.jsonl", root / "ids.sqlite"
        first = sync_latest(status_path=status, output=output, catalog_path=catalog)
        second = sync_latest(status_path=status, output=output, catalog_path=catalog)
        rows = list(_iter_jsonl(output))
        checks.append(("first sync deduplicates files and rejects serves_truth=true",
                       first["new_searchable_candidates"] == 2 and first["boundary_rejected"] == 1))
        checks.append(("normalized rows have title, blackbox, typed edges, and candidate boundary",
                       all(row["title"] and row["blackbox"] and row["input_edge"] and row["output_edge"]
                           and row["candidate"] is True and row["serves_truth"] is False for row in rows)))
        checks.append(("rerun is idempotent", second["new_searchable_candidates"] == 0 and len(rows) == 2))
        # Simulate a stale/lost catalog; byte-size reconciliation rebuilds it from the durable append file.
        catalog.unlink()
        repaired = sync_latest(status_path=status, output=output, catalog_path=catalog)
        checks.append(("catalog rebuild preserves dedupe after catalog loss",
                       repaired["new_searchable_candidates"] == 0 and repaired["distinct_output_rows_after"] == 2))
    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"FAIL - ingest_continuous_scrape_candidates: {failed}")
        return 1
    print("PASS - ingest_continuous_scrape_candidates: latest research candidates normalize, dedupe, append, "
          "reconcile after catalog loss, and remain candidate=true/serves_truth=false.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sync", action="store_true")
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.sync:
        parser.error("pass --sync or --self-test")
    print(json.dumps(sync_latest(status_path=args.status, output=args.output, catalog_path=args.catalog),
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
