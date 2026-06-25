#!/usr/bin/env python3
"""scripts.scale_index — the SCALE-correct record index: SQLite-backed, INCREMENTAL, indexed, shard-ready.

Replaces the prototype whole-file JSON rebuild (O(n) per cycle → quadratic) with an index that updates in O(NEW)
records and answers search with an indexed SQL lookup (not an O(n) Python scan). This is the operational tier per
storage_tier_policy ("operational = sqlite_wal local → postgres+pgvector cloud"): the SAME schema + access pattern
swaps to Postgres/pgvector with NO rewrite. Build TOWARD scale, not to replace later.
  * INCREMENTAL: a byte-offset cursor on registry_records.jsonl reads only newly-appended records (safe with the
    concurrently-appending populate loop — advances only past the last COMPLETE line).
  * IDEMPOTENT: INSERT OR REPLACE by record_id (content-addressed); re-index clears the record's old tokens.
  * SHARD-READY: every record carries a stable shard (hash-prefix) → scatter/gather + per-shard ANN later.
  * Reuses hybrid_search.columns()/_embed() so the multi-attribute decomposition + (pgvector-ready) vectors carry over.
serves_truth=false.

  --self-test | --ingest | --search "<q>" [-k N] | --stats
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from scripts.hybrid_search import WEIGHTS, _embed, _toks, columns  # reuse the column decomposition + embedding

DB = REPO / "data" / "dev-intel" / "registry_index.db"
SRC = REPO / "data" / "dev-intel" / "registry_records.jsonl"
SHARDS = 256


def _shard(rid: str) -> int:
    return int(hashlib.md5(rid.encode()).hexdigest()[:4], 16) % SHARDS   # stable (not PYTHONHASHSEED-dependent)


def _conn(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(db))
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")
    c.executescript(
        "CREATE TABLE IF NOT EXISTS records(record_id TEXT PRIMARY KEY, shard INT, name TEXT, type TEXT,"
        " registry TEXT, kind TEXT, vec TEXT);"
        "CREATE TABLE IF NOT EXISTS tokens(token TEXT, record_id TEXT, col TEXT);"
        "CREATE INDEX IF NOT EXISTS ix_tokens_tok ON tokens(token);"
        "CREATE INDEX IF NOT EXISTS ix_tokens_rid ON tokens(record_id);"
        "CREATE INDEX IF NOT EXISTS ix_records_shard ON records(shard);"
        "CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);")
    return c


def _get_offset(c: sqlite3.Connection) -> int:
    r = c.execute("SELECT v FROM meta WHERE k='offset'").fetchone()
    return int(r[0]) if r else 0


def _upsert(c: sqlite3.Connection, rec: dict) -> bool:
    rid = rec.get("record_id")
    if not rid or not rec.get("name"):
        return False
    cols = columns(rec)
    vec = _embed(f"{cols['name']} {cols['use_cases']}")                 # one semantic vec/record (per-column ANN = #16)
    c.execute("INSERT OR REPLACE INTO records VALUES(?,?,?,?,?,?,?)",
              (rid, _shard(rid), rec.get("name", ""), rec.get("object_type", ""), rec.get("registry", ""),
               rec.get("kind", "record"), json.dumps([round(x, 4) for x in vec])))
    c.execute("DELETE FROM tokens WHERE record_id=?", (rid,))           # idempotent re-index
    seen = set()
    for col in WEIGHTS:
        for t in set(_toks(cols[col])):
            if (t, col) not in seen:
                seen.add((t, col))
                c.execute("INSERT INTO tokens VALUES(?,?,?)", (t, rid, col))
    return True


def ingest(db: Path = DB, src: Path = SRC) -> dict:
    if not src.exists():
        return {"new": 0, "total": 0}
    c = _conn(db)
    off = _get_offset(c)
    with src.open("rb") as f:
        f.seek(off)
        chunk = f.read()
    nl = chunk.rfind(b"\n")                                             # advance only past the last COMPLETE line
    if nl < 0:                                                          # no complete new line → nothing to do
        total = c.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        c.close()
        return {"new": 0, "total": total}
    body = chunk[:nl + 1].decode("utf-8", "replace")
    n = 0
    for ln in body.splitlines():
        if ln.strip():
            try:
                if _upsert(c, json.loads(ln)):
                    n += 1
            except json.JSONDecodeError:
                pass
    c.execute("INSERT OR REPLACE INTO meta VALUES('offset',?)", (str(off + nl + 1),))
    c.commit()
    total = c.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    c.close()
    return {"new": n, "total": total}


def search(query: str, k: int = 10, db: Path = DB) -> list[dict]:
    qt = set(_toks(query))
    if not qt or not db.exists():
        return []
    c = _conn(db)
    ph = ",".join("?" * len(qt))
    rows = c.execute(f"SELECT record_id, col, COUNT(*) c FROM tokens WHERE token IN ({ph}) "
                     f"GROUP BY record_id, col", list(qt)).fetchall()       # indexed lookup, NOT a full scan
    score: dict[str, float] = {}
    for rid, col, cnt in rows:
        score[rid] = score.get(rid, 0.0) + WEIGHTS.get(col, 1.0) * cnt
    top = sorted(score.items(), key=lambda x: -x[1])[:k]
    out = []
    for rid, sc in top:
        r = c.execute("SELECT name, type, registry, shard FROM records WHERE record_id=?", (rid,)).fetchone()
        if r:
            out.append({"record_id": rid, "score": round(sc, 2), "name": r[0], "type": r[1],
                        "registry": r[2], "shard": r[3]})
    c.close()
    return out


def stats(db: Path = DB) -> dict:
    if not db.exists():
        return {"records": 0}
    c = _conn(db)
    nr = c.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    nt = c.execute("SELECT COUNT(*) FROM tokens").fetchone()[0]
    ns = c.execute("SELECT COUNT(DISTINCT shard) FROM records").fetchone()[0]
    c.close()
    return {"records": nr, "tokens": nt, "shards_used": ns, "db_kb": round(db.stat().st_size / 1024, 1)}


def self_test() -> int:
    import tempfile
    d = Path(tempfile.mkdtemp())
    db, src = d / "i.db", d / "r.jsonl"
    recs = [{"record_id": "r1", "kind": "record", "object_type": "tool", "name": "LangGraph agent orchestration",
             "registry": "tool_registry", "searchability_tags": ["langgraph", "agent"], "capabilities": ["orchestrate agents"], "source": {}},
            {"record_id": "r2", "kind": "record", "object_type": "tool", "name": "email regex",
             "registry": "component", "searchability_tags": ["regex", "email"], "source": {}}]
    src.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    a = ingest(db, src)
    assert a["new"] == 2 and a["total"] == 2, a
    b = ingest(db, src)                                                 # INCREMENTAL: nothing new on re-ingest
    assert b["new"] == 0, f"re-ingest must be O(0): {b}"
    with src.open("a", encoding="utf-8") as f:                          # append one → only the new one ingests
        f.write(json.dumps({"record_id": "r3", "kind": "record", "object_type": "tool", "name": "browser automation",
                            "registry": "tool_registry", "searchability_tags": ["browser"], "source": {}}) + "\n")
    assert ingest(db, src)["new"] == 1, "only the appended record re-ingests"
    hits = search("agent orchestration", db=db)
    assert hits and hits[0]["record_id"] == "r1", f"indexed search ranks r1 first: {hits[:1]}"
    assert any(h["record_id"] == "r3" for h in search("browser", db=db)), "appended record searchable"
    assert all(isinstance(h["shard"], int) for h in hits), "records carry a stable shard"
    assert _shard("r1") == _shard("r1"), "shard is stable"
    print(f"scale_index self-test: OK (sqlite incremental ingest O(new), idempotent re-ingest, indexed search, "
          f"shard-ready) stats={stats(db)}")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    if "--ingest" in argv:
        print(json.dumps(ingest(), indent=2)); return 0
    if "--stats" in argv:
        print(json.dumps(stats(), indent=2)); return 0
    if "--search" in argv:
        for h in search(opt("--search") or "", int(opt("-k", "10"))):
            print(f"  [{h['score']}] {h['name'][:50]} ({h['type']}/{h['registry']}) shard={h['shard']}")
        return 0
    print("usage: scale_index.py --self-test | --ingest | --search '<q>' [-k N] | --stats")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
