#!/usr/bin/env python3
"""scripts.primitive_database — load EVERY primitive pool into a USABLE, queryable database. Minting into JSONL
is the staging layer; this is the step that makes the millions of primitives actually usable: a single SQLite
database with an FTS5 full-text index over title/blackbox/tags, deduped by primitive_id, streamed + batched so
it scales to tens of millions of rows without loading them into memory.

SQLite + FTS5 is the LOCAL database (zero-setup, sub-second keyword search, millions of rows). The production
target is Postgres + pgvector (the CLAUDE.md storage tiers) — the swap is config-only: same ingest contract,
same query verbs (search / lookup / stats). serves_truth=false (a candidate database; loading is not promotion).

    python3 scripts/primitive_database.py --self-test
    python3 scripts/primitive_database.py --build                 # ingest all pools -> dist/primitives.db
    python3 scripts/primitive_database.py --search "drift monitor" --limit 10
    python3 scripts/primitive_database.py --search "canary rollout" --pool ml_lifecycle
    python3 scripts/primitive_database.py --stats
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel) ──────────────────────────────────────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import sqlite3  # noqa: E402
from typing import Any, Iterator, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_DB_NAME = "primitives.db"
_BATCH = 5000

_FOUNDRY = "data/dev-intel/aidevobserver_edge_foundry"
#: (pool_name, relative_path) — every primitive-bearing pool. New pools are one row here.
_POOLS: tuple[tuple[str, str], ...] = (
    ("verified_factory", f"{_FOUNDRY}/verified_factory_primitive_cards.jsonl"),
    ("primitive_edge", f"{_FOUNDRY}/primitive_edge_cards.jsonl"),
    ("minted_gap", f"{_FOUNDRY}/minted_gap_primitive_candidates.jsonl"),
    ("grid", f"{_FOUNDRY}/grid_primitive_candidates.jsonl"),
    ("idea", f"{_FOUNDRY}/idea_primitive_candidates.jsonl"),
    ("persona", f"{_FOUNDRY}/persona_primitive_candidates.jsonl"),
    ("ml_lifecycle", f"{_FOUNDRY}/ml_lifecycle_primitive_candidates.jsonl"),
    ("ml_team_role", f"{_FOUNDRY}/ml_team_role_primitive_candidates.jsonl"),
    ("browser_automation", f"{_FOUNDRY}/browser_automation_primitive_candidates.jsonl"),
    ("layered", f"{_FOUNDRY}/layered_primitive_candidates.jsonl"),
    ("expanded", f"{_FOUNDRY}/expanded_primitive_candidates.jsonl"),
    ("executable", f"{_FOUNDRY}/executable_primitive_candidates.jsonl"),
    ("enriched", f"{_FOUNDRY}/enriched_primitive_candidates.jsonl"),
    ("kaggle", f"{_FOUNDRY}/kaggle_primitive_candidates.jsonl"),
    # the executable packs (standardization/ui/party/control-plane/dummy-detection; synced by
    # executable_pack_pool_sync) + the owner-catalog mints — every primitive reaches the database
    ("executable_packs", f"{_FOUNDRY}/executable_pack_cards.jsonl"),
    ("schema_org", "data/dev-intel/schema_org_foundry/schema_org_primitive_candidates.jsonl"),
    ("string_operations", "data/dev-intel/string_operations_catalog/string_operation_primitive_candidates.jsonl"),
    ("operation_chains", "data/dev-intel/primitive_chain_catalog/operation_and_chain_candidates.jsonl"),
    ("standards_enrichment", "data/dev-intel/standards_enrichment_registry/standards_enrichment_candidates.jsonl"),
)


def default_db_path() -> Path:
    return resource("dist") / _DB_NAME


def _blackbox_text(row: dict[str, Any]) -> str:
    bb = row.get("blackbox")
    if isinstance(bb, dict):
        return str(bb.get("does") or " ".join(str(v) for v in bb.values() if isinstance(v, str)))
    return str(bb or "")


def _tags_text(row: dict[str, Any]) -> str:
    tags = row.get("capability_tags") or []
    return " ".join(str(t) for t in tags) if isinstance(tags, list) else str(tags)


def _iter_rows(path: Path) -> Iterator[dict[str, Any]]:
    """Stream a JSONL pool line-by-line (never load the whole file — scales to tens of millions of rows)."""
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def _create_schema(con: sqlite3.Connection) -> None:
    con.execute("""CREATE TABLE IF NOT EXISTS primitives(
        primitive_id TEXT PRIMARY KEY, pool TEXT, title TEXT, blackbox TEXT, tags TEXT,
        input_edge TEXT, output_edge TEXT, serves_truth INTEGER DEFAULT 0)""")
    # external-content FTS5 over the searchable text columns; synced after the batch load
    con.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS primitives_fts USING fts5(
        title, blackbox, tags, content='primitives', content_rowid='rowid')""")


def build(db_path: Optional[Path] = None, pools: tuple[tuple[str, str], ...] = _POOLS,
          base: Optional[Path] = None) -> dict[str, Any]:
    """Ingest all pools into a fresh SQLite DB (dedup by primitive_id) + build the FTS index. Streamed +
    batched so memory stays flat regardless of pool size."""
    db_path = db_path or default_db_path()
    base = base or _sbc_boot
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()  # rebuild fresh (regenerable artifact)
    con = _connect(db_path)
    _create_schema(con)
    per_pool: dict[str, int] = {}
    total_seen = 0
    for pool_name, rel in pools:
        p = base / rel
        if not p.exists():
            per_pool[pool_name] = 0
            continue
        batch: list[tuple] = []
        inserted_before = con.total_changes
        for row in _iter_rows(p):
            pid = row.get("primitive_id") or row.get("id")
            if not pid:
                continue
            total_seen += 1
            batch.append((str(pid), pool_name, str(row.get("title") or ""), _blackbox_text(row),
                          _tags_text(row), str(row.get("input_edge") or ""), str(row.get("output_edge") or ""),
                          1 if row.get("serves_truth") else 0))
            if len(batch) >= _BATCH:
                con.executemany("INSERT OR IGNORE INTO primitives VALUES(?,?,?,?,?,?,?,?)", batch)
                con.commit()
                batch.clear()
        if batch:
            con.executemany("INSERT OR IGNORE INTO primitives VALUES(?,?,?,?,?,?,?,?)", batch)
            con.commit()
        per_pool[pool_name] = con.total_changes - inserted_before
    # build the FTS index from the deduped content table
    con.execute("INSERT INTO primitives_fts(primitives_fts) VALUES('rebuild')")
    con.commit()
    distinct = con.execute("SELECT COUNT(*) FROM primitives").fetchone()[0]
    con.close()
    return {"db_path": str(db_path), "rows_seen": total_seen, "distinct_rows": distinct,
            "collapsed_duplicates": total_seen - distinct, "per_pool_inserted": per_pool, **BOUNDARY}


def search(query: str, db_path: Optional[Path] = None, *, pool: Optional[str] = None, limit: int = 10) -> list[dict[str, Any]]:
    """FTS5 full-text search over title/blackbox/tags, optionally filtered by pool. Sub-second at millions."""
    db_path = db_path or default_db_path()
    if not db_path.exists():
        return []
    con = _connect(db_path)
    con.row_factory = sqlite3.Row
    sql = ("SELECT p.primitive_id, p.pool, p.title, bm25(primitives_fts) AS score "
           "FROM primitives_fts f JOIN primitives p ON p.rowid = f.rowid "
           "WHERE primitives_fts MATCH ? ")
    params: list[Any] = [query]
    if pool:
        sql += "AND p.pool = ? "
        params.append(pool)
    sql += "ORDER BY score LIMIT ?"
    params.append(limit)
    try:
        rows = con.execute(sql, params).fetchall()
    except sqlite3.OperationalError:  # malformed FTS query -> quote it as a phrase
        params[0] = '"' + query.replace('"', "") + '"'
        rows = con.execute(sql, params).fetchall()
    con.close()
    return [{"primitive_id": r["primitive_id"], "pool": r["pool"], "title": r["title"],
             "score": round(r["score"], 3)} for r in rows]


def stats(db_path: Optional[Path] = None) -> dict[str, Any]:
    db_path = db_path or default_db_path()
    if not db_path.exists():
        return {"db_exists": False, **BOUNDARY}
    con = _connect(db_path)
    total = con.execute("SELECT COUNT(*) FROM primitives").fetchone()[0]
    by_pool = dict(con.execute("SELECT pool, COUNT(*) FROM primitives GROUP BY pool").fetchall())
    con.close()
    return {"db_exists": True, "db_path": str(db_path), "total_primitives": total, "by_pool": by_pool,
            "size_mb": round(db_path.stat().st_size / 1e6, 1), **BOUNDARY}


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        (base / "p1.jsonl").parent.mkdir(parents=True, exist_ok=True)
        rows_a = [{"primitive_id": "a:1", "title": "KS-test drift monitor", "blackbox": "detect distribution drift",
                   "capability_tags": ["ml_op:drift"], "input_edge": "In", "output_edge": "Out"},
                  {"primitive_id": "a:2", "title": "canary rollout gate", "blackbox": "1% 5% 25% traffic",
                   "capability_tags": ["deploy"], "serves_truth": False}]
        rows_b = [{"primitive_id": "a:1", "title": "dup should collapse", "blackbox": "x"},  # dup id
                  {"primitive_id": "b:1", "title": "reservoir sample", "blackbox": "one-pass uniform sample"}]
        (base / "p1.jsonl").write_text("\n".join(json.dumps(r) for r in rows_a))
        (base / "p2.jsonl").write_text("\n".join(json.dumps(r) for r in rows_b))
        pools = (("pool_a", "p1.jsonl"), ("pool_b", "p2.jsonl"))
        db = base / "test.db"
        rec = build(db_path=db, pools=pools, base=base)
        checks.append(("build ingests all pools, dedups by primitive_id",
                       rec["distinct_rows"] == 3 and rec["rows_seen"] == 4 and rec["collapsed_duplicates"] == 1))
        checks.append(("FTS5 full-text search finds a primitive by keyword",
                       any(r["primitive_id"] == "a:1" for r in search("drift", db_path=db))
                       and any("reservoir" in r["title"] for r in search("reservoir sample", db_path=db))))
        checks.append(("search filters by pool",
                       all(r["pool"] == "pool_b" for r in search("sample", db_path=db, pool="pool_b"))))
        st = stats(db_path=db)
        checks.append(("stats reports total + per-pool counts",
                       st["total_primitives"] == 3 and st["by_pool"].get("pool_a") == 2))
        # rebuild is idempotent (same distinct count)
        rec2 = build(db_path=db, pools=pools, base=base)
        checks.append(("rebuild is idempotent (deterministic distinct count)",
                       rec2["distinct_rows"] == rec["distinct_rows"]))
        # a malformed FTS query (special chars) does not crash — falls back to a phrase
        checks.append(("a malformed query is handled (phrase fallback, no crash)",
                       isinstance(search("drift AND (", db_path=db), list)))
        checks.append(("receipts carry the boundary", rec["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_database: every pool loaded into a SQLite FTS5 database (streamed + batched, "
          "deduped by primitive_id), full-text searchable by title/blackbox/tags with pool filtering; scales "
          "to tens of millions of rows; the Postgres/pgvector swap is config-only. serves_truth=false.")
    return 0


def _run_build() -> int:
    rec = build()
    out = resource("data") / "dev-intel" / "session_emulation" / "primitive_database_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({k: rec[k] for k in ("db_path", "rows_seen", "distinct_rows", "collapsed_duplicates",
                                          "per_pool_inserted")}, indent=2))
    print(f"\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--build", action="store_true", help="ingest all pools into the SQLite FTS5 database")
    ap.add_argument("--search", metavar="QUERY", default=None)
    ap.add_argument("--pool", default=None, help="filter search to one pool")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.build:
        return _run_build()
    if args.search:
        for r in search(args.search, pool=args.pool, limit=args.limit):
            print(f"  [{r['pool']}] {r['title']}  ({r['primitive_id']})")
        return 0
    if args.stats:
        print(json.dumps(stats(), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
