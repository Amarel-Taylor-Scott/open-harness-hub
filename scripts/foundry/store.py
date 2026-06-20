#!/usr/bin/env python3
"""Foundry store — the persistence layer that scales local → cloud unchanged.

ONE interface (`Store.write(table, rows)` / `read` / `count`), three backends selected
purely by env (12-factor) so the *same* worker code runs everywhere:

  - **SqliteStore** — a real, embedded DB (stdlib `sqlite3`); local dev runs with zero
    extra services. NOT a placeholder — durable, queryable, upsert-idempotent.
  - **PostgresStore** — the cloud backend (psycopg, JSONB); same DDL/SQL shape, so moving
    up is a `DATABASE_URL` change, not a rewrite.
  - **JsonlStore** — append-only files (CI / inspection / the simplest export).

`from_env()` picks: ``DATABASE_URL=postgres://…`` → Postgres; ``…sqlite``/``sqlite:///…``
→ SQLite; ``OH_STORE=jsonl`` → JSONL; default → a local SQLite file. The foundry's row
families (normalized_object · object_embedding · index_record · knowledge_entry ·
review_ticket · source_record · …) and interaction_record all land here.

Run ``python -m scripts.foundry.store`` for the offline self-test (real SQLite).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable, Protocol, runtime_checkable

_NAME = re.compile(r"[^a-z0-9_]+")
# columns promoted out of the JSON blob for indexed querying (NULL when absent)
_PROMOTED_COLS = ("type", "openness", "delivery", "lift_delta", "approval_status")


def _safe_table(name: str) -> str:
    t = _NAME.sub("_", (name or "").lower()).strip("_")
    return t or "rows"


def _row_id(row: dict) -> str:
    for k in ("object_id", "entry_id", "source_id", "ticket_id", "interaction_id", "id"):
        if row.get(k):
            return str(row[k])
    return "row-" + hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _num(v: Any) -> float | None:
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


@runtime_checkable
class Store(Protocol):
    backend: str
    def write(self, table: str, rows: Iterable[dict]) -> int: ...
    def read(self, table: str, *, limit: int = 1000) -> list[dict]: ...
    def count(self, table: str) -> int: ...


class JsonlStore:
    backend = "jsonl"

    def __init__(self, directory: str | Path) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, table: str) -> Path:
        return self.dir / f"{_safe_table(table)}.jsonl"

    def write(self, table: str, rows: Iterable[dict]) -> int:
        rows = list(rows)
        with self._path(table).open("a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, sort_keys=True, ensure_ascii=True, default=str) + "\n")
        return len(rows)

    def read(self, table: str, *, limit: int = 1000) -> list[dict]:
        p = self._path(table)
        if not p.exists():
            return []
        return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines()[:limit] if ln.strip()]

    def count(self, table: str) -> int:
        p = self._path(table)
        return sum(1 for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()) if p.exists() else 0


class SqliteStore:
    """Real embedded DB — local dev with no services. Upsert by row id (idempotent re-runs)."""

    backend = "sqlite"

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

    def _ensure(self, con: sqlite3.Connection, table: str) -> str:
        t = _safe_table(table)
        cols = ", ".join(f"{c} {'REAL' if c == 'lift_delta' else 'TEXT'}" for c in _PROMOTED_COLS)
        con.execute(f"CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY, {cols}, created TEXT, data TEXT)")
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_{t}_type ON {t}(type)")
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_{t}_openness ON {t}(openness)")
        return t

    def write(self, table: str, rows: Iterable[dict]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        con = sqlite3.connect(self.path)
        try:
            t = self._ensure(con, table)
            cols = ["id", *_PROMOTED_COLS, "created", "data"]
            ph = ",".join("?" * len(cols))
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            con.executemany(
                f"INSERT OR REPLACE INTO {t} ({','.join(cols)}) VALUES ({ph})",
                [(_row_id(r), r.get("type"), r.get("openness"), r.get("delivery"),
                  _num(r.get("lift_delta")), r.get("approval_status"),
                  r.get("created") or now, json.dumps(r, sort_keys=True, default=str)) for r in rows],
            )
            con.commit()
        finally:
            con.close()
        return len(rows)

    def read(self, table: str, *, limit: int = 1000) -> list[dict]:
        con = sqlite3.connect(self.path)
        try:
            t = _safe_table(table)
            try:
                cur = con.execute(f"SELECT data FROM {t} LIMIT ?", (limit,))
            except sqlite3.OperationalError:
                return []
            return [json.loads(row[0]) for row in cur.fetchall()]
        finally:
            con.close()

    def count(self, table: str) -> int:
        con = sqlite3.connect(self.path)
        try:
            try:
                return int(con.execute(f"SELECT COUNT(*) FROM {_safe_table(table)}").fetchone()[0])
            except sqlite3.OperationalError:
                return 0
        finally:
            con.close()


class PostgresStore:
    """Cloud backend — same shape as SqliteStore, JSONB blob. Needs psycopg (`pip install psycopg`)."""

    backend = "postgres"

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        import psycopg  # noqa: F401  (import-time check; raises clearly if absent)

    def _conn(self):  # pragma: no cover - needs a live DB
        import psycopg
        return psycopg.connect(self.dsn)

    def write(self, table: str, rows: Iterable[dict]) -> int:  # pragma: no cover - needs a live DB
        rows = list(rows)
        if not rows:
            return 0
        t = _safe_table(table)
        cols = ", ".join(f"{c} {'DOUBLE PRECISION' if c == 'lift_delta' else 'TEXT'}" for c in _PROMOTED_COLS)
        with self._conn() as con, con.cursor() as cur:
            cur.execute(f"CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY, {cols}, created TIMESTAMPTZ DEFAULT now(), data JSONB)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{t}_type ON {t}(type)")
            colnames = ["id", *_PROMOTED_COLS, "data"]
            ph = ",".join(["%s"] * len(colnames))
            updates = ",".join(f"{c}=EXCLUDED.{c}" for c in colnames if c != "id")
            cur.executemany(
                f"INSERT INTO {t} ({','.join(colnames)}) VALUES ({ph}) "
                f"ON CONFLICT (id) DO UPDATE SET {updates}",
                [(_row_id(r), r.get("type"), r.get("openness"), r.get("delivery"),
                  _num(r.get("lift_delta")), r.get("approval_status"),
                  json.dumps(r, default=str)) for r in rows],
            )
            con.commit()
        return len(rows)

    def read(self, table: str, *, limit: int = 1000) -> list[dict]:  # pragma: no cover
        with self._conn() as con, con.cursor() as cur:
            cur.execute(f"SELECT data FROM {_safe_table(table)} LIMIT %s", (limit,))
            return [r[0] for r in cur.fetchall()]

    def count(self, table: str) -> int:  # pragma: no cover
        with self._conn() as con, con.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {_safe_table(table)}")
            return int(cur.fetchone()[0])


def from_env() -> Store:
    """Pick the backend from env — the ONLY thing that changes local → cloud."""
    if os.environ.get("OH_STORE") == "jsonl":
        return JsonlStore(os.environ.get("OH_STORE_PATH", "dist/foundry-rows"))
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres"):
        return PostgresStore(url)
    if url.startswith("sqlite:///"):
        return SqliteStore(url[len("sqlite:///"):])
    if url.endswith((".db", ".sqlite")):
        return SqliteStore(url)
    return SqliteStore(os.environ.get("OH_STORE_PATH", "dist/foundry-store.sqlite"))


def _self_test() -> int:
    import tempfile

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    rows = [
        {"object_id": "knowledge-pack/x", "type": "knowledge-pack", "openness": "commercial",
         "delivery": "credentialed_data", "lift_delta": 0.41, "approval_status": "pending_human", "name": "X"},
        {"object_id": "rule-pack/y", "type": "rule-pack", "openness": "open",
         "delivery": "frozen_export", "lift_delta": 0.2, "approval_status": "auto", "name": "Y"},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        # SQLite — the real local DB
        st = SqliteStore(Path(tmp) / "s.sqlite")
        n = st.write("index_record", rows)
        check("sqlite write returns count", n == 2)
        check("sqlite count == 2", st.count("index_record") == 2)
        check("sqlite read round-trips data", {r["object_id"] for r in st.read("index_record")} == {"knowledge-pack/x", "rule-pack/y"})
        st.write("index_record", rows)   # same ids again
        check("sqlite upsert is idempotent (no dupes)", st.count("index_record") == 2)
        check("unknown table ⇒ count 0 (no crash)", st.count("nope") == 0 and st.read("nope") == [])
        # promoted columns are queryable
        con = sqlite3.connect(st.path)
        only_open = con.execute("SELECT id FROM index_record WHERE openness='open'").fetchall()
        con.close()
        check("indexed column queryable (openness)", only_open == [("rule-pack/y",)], str(only_open))

        # JSONL backend
        js = JsonlStore(Path(tmp) / "rows")
        check("jsonl write+count", js.write("interaction_record", rows) == 2 and js.count("interaction_record") == 2)

        # from_env selection
        saved = {k: os.environ.pop(k, None) for k in ("DATABASE_URL", "OH_STORE", "OH_STORE_PATH")}
        try:
            os.environ["OH_STORE_PATH"] = str(Path(tmp) / "default.sqlite")
            check("from_env default ⇒ SqliteStore", from_env().backend == "sqlite")
            os.environ["DATABASE_URL"] = "postgres://u:p@h/db"
            check("DATABASE_URL=postgres ⇒ PostgresStore selected", type(_safe_pg_select()).__name__ in ("PostgresStore", "str"))
            os.environ["OH_STORE"] = "jsonl"
            check("OH_STORE=jsonl ⇒ JsonlStore", from_env().backend == "jsonl")
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None)
                if v is not None:
                    os.environ[k] = v

    print(f"\n{'all store self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _safe_pg_select():
    """Helper for the test: from_env() with postgres URL — psycopg may be absent, so
    just confirm the selection branch (constructing PostgresStore raises ImportError if
    psycopg isn't installed, which is the honest 'cloud-only' behavior)."""
    try:
        return from_env()
    except ImportError:
        return "postgres-branch-selected (psycopg not installed locally — expected)"


if __name__ == "__main__":
    raise SystemExit(_self_test())
