#!/usr/bin/env python3
"""scripts._jsonl_store — a SQLite-WAL-backed append-log behind the JSONL durability contract.

The three shared local services (identity, registry, events) keep per-account / per-realm state in
append-only ``*.jsonl`` files. Those files are the externally CONTRACTED on-disk record: several
proofs that this module does NOT own read them back by name as UTF-8 text (``audit-events.jsonl``,
``events.jsonl``, ``review_queue.jsonl`` …) and three of those proofs ``glob('**/*')`` + ``read_text``
EVERY file under a service's state dir for disk-hygiene. A binary SQLite file (and its ``-wal`` /
``-shm`` sidecars, which are NOT valid UTF-8) dropped into those dirs would crash that scan. So this
store does the thing that satisfies BOTH the prompt's goal (a SQLite WAL engine — crash-safe, no
torn-tail corruption, O(1)-attach rehydration instead of an O(n) per-start full re-parse, the exact
append/iter/count shape that swaps to Postgres) AND every standing invariant:

  * the SQLite table is the CRASH-SAFE primary record (one ACID transaction per append; ``WAL`` so a
    committed row survives a kill mid-write — a torn line can never wedge it);
  * the ``*.jsonl`` text file stays an APPEND-ONLY MIRROR, written from the committed row inside the
    same lock, so the durability contract + every external reader keep working unchanged;
  * the SQLite database lives OUTSIDE the service state dir (under ``.agent/state-index/`` — off the
    hygiene-scanned tree, never committed). It is a REBUILDABLE index: on a cold start with no db it
    re-imports from the ``*.jsonl`` (so even on a host where ``.agent/`` is ephemeral — e.g. a Fly
    machine whose only volume is the state dir — the JSONL on the volume remains the source of truth
    and the index is rebuilt for free).

LOSSLESS (docs/codex/lossless-distillation.md): migrating a pre-existing legacy ``*.jsonl`` into the
db is distillation, never replacement — every line is imported, the legacy file is LEFT IN PLACE and
additionally snapshotted to ``<name>.migrated`` (a rollback target), and rotation renames a full
generation to ``.1`` (one kept), never truncating in place.

SINGLE-MACHINE LAW (unchanged): one service process owns one state dir on one node. WAL is
single-writer-node; ``busy_timeout`` makes a concurrent reader/writer WAIT rather than error, and
``check_same_thread=False`` + an ``RLock`` make it safe under each service's ThreadingHTTPServer
(every request a thread). This module REMOVES the per-start re-parse and the corruption-on-crash
risk and is the seam where a Postgres backend drops in later — it does NOT license ``scale count>1``.

stdlib ``sqlite3`` only; offline. Run ``python3 scripts/_jsonl_store.py --self-test``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Callable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]

# -- where the rebuildable SQLite index lives (NOT under any service state dir) -----------------
# Off every disk-hygiene scan (those glob the service state dir) and gitignored (.agent/). A db here
# being absent is non-fatal: the store re-imports from the durable *.jsonl on the volume. One dir,
# many logs; each log's db file is named from a hash of its absolute jsonl path so two services (or
# two temp dirs in a proof) never collide on the same db.
STATE_INDEX_DIR = REPO_ROOT / ".agent" / "state-index"
_DB_PATH_HASH_CHARS = 16          # blake2b hex chars of the absolute jsonl path → a collision-safe,
#                                   filesystem-safe db filename (the human stem is kept for triage)

# -- SQLite pragmas (the house durability profile; see scripts/durable_store.py) ----------------
_PRAGMA_JOURNAL_MODE = "WAL"      # crash-safe: a committed append survives a process kill mid-write
_PRAGMA_SYNCHRONOUS = "NORMAL"    # WAL + NORMAL = durable across app crash, fsync only at checkpoint
_PRAGMA_BUSY_TIMEOUT_MS = 5000    # multi-reader/writer: WAIT on a held lock rather than raise (5s)

# -- on-disk layout constants (single source; the services import these, never re-type them) ----
ROTATED_SUFFIX = ".1"             # the single kept previous generation of a rotated jsonl (lossless)
MIGRATED_SUFFIX = ".migrated"     # snapshot of a legacy jsonl taken at first import (rollback target)
GENERATION_START = 1              # first live generation number; ++ on every rotate()


def _db_path_for(jsonl_path: Path) -> Path:
    """Deterministic db path for a given durable jsonl. Keyed by the ABSOLUTE jsonl path so distinct
    state dirs (incl. per-proof temp dirs) get distinct dbs; the stem is kept only for human triage."""
    absolute = str(jsonl_path.resolve())
    digest = hashlib.blake2b(absolute.encode(), digest_size=_DB_PATH_HASH_CHARS // 2).hexdigest()
    return STATE_INDEX_DIR / f"{jsonl_path.stem}.{digest}.db"


class AppendLog:
    """A single append-only log: SQLite-WAL primary + an append-only ``*.jsonl`` mirror.

    Records are JSON objects (dicts). ``append`` is one ACID transaction; ``iter`` streams the live
    generation oldest→newest (optionally filtered); ``count`` is the live-generation row count;
    ``rotate`` closes the current generation losslessly (jsonl → ``.1``; the db's rows are tagged with
    a new generation so counters describe the live generation only, exactly like the services do today).

    The ``*.jsonl`` mirror is what the durability contract and external readers see; the db is what
    makes a restart O(attach) instead of O(n re-parse) and what a torn tail line can never corrupt.
    """

    def __init__(self, jsonl_path: Path, *, db_path: Path | None = None) -> None:
        self.jsonl_path = Path(jsonl_path)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path) if db_path is not None else _db_path_for(self.jsonl_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        # check_same_thread=False + the RLock = safe under ThreadingHTTPServer / worker threads.
        self.conn = sqlite3.connect(str(self.db_path), isolation_level=None, check_same_thread=False)
        self.conn.execute(f"PRAGMA journal_mode={_PRAGMA_JOURNAL_MODE}")
        self.conn.execute(f"PRAGMA synchronous={_PRAGMA_SYNCHRONOUS}")
        self.conn.execute(f"PRAGMA busy_timeout={_PRAGMA_BUSY_TIMEOUT_MS}")
        self._init_schema()
        self._generation = self._current_generation()
        self._reconcile_with_jsonl()

    # -- schema + generation bookkeeping --------------------------------------------------------
    def _init_schema(self) -> None:
        with self._lock:
            c = self.conn
            # body_json: the exact record. generation: which live era the row belongs to (rotation
            # bumps it). seq AUTOINCREMENT gives a stable oldest→newest order that survives restart.
            c.execute("""CREATE TABLE IF NOT EXISTS records(
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                generation INTEGER NOT NULL,
                body_json TEXT NOT NULL)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_records_gen ON records(generation, seq)")
            c.execute("CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT)")

    def _current_generation(self) -> int:
        with self._lock:
            row = self.conn.execute("SELECT value FROM meta WHERE key='generation'").fetchone()
        return int(row[0]) if row else GENERATION_START

    def _set_generation(self, generation: int) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT INTO meta(key,value) VALUES('generation',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(generation),))
        self._generation = generation

    # -- migration + reconciliation (LOSSLESS) --------------------------------------------------
    def _reconcile_with_jsonl(self) -> None:
        """Make the db and the live jsonl mirror agree, losslessly, at startup:

        * FIRST START WITH A LEGACY FILE (db empty, jsonl has lines) → import every line into the db,
          leave the jsonl in place, and snapshot it to ``<name>.migrated`` (a rollback target). This
          is the prompt's required migration: never drop the legacy file.
        * DB AHEAD OF A TORN MIRROR (db has the rows, the jsonl tail was torn by a crash mid-append) →
          the db is authoritative; rewrite the mirror from the db so external readers see every
          committed row. The pre-repair mirror is snapshotted to ``<name>.migrated`` once, so nothing
          is destroyed.
        * ALREADY IN AGREEMENT → no-op.

        Counts compare the LIVE generation only (a rotated ``.1`` is separate, preserved evidence).

        HOT-PATH COST: the steady-state restart (db present, mirror intact) does an O(1) indexed
        ``COUNT(*)`` and an O(bytes) newline scan — NO per-record ``json.loads`` on either side. Only
        the two RARE branches parse: a one-time legacy import (must read the legacy lines once) and a
        torn-mirror repair (must materialize the db rows once). This is what makes the restart cheaper
        than the old whole-file re-parse rather than 2× more expensive.
        """
        with self._lock:
            db_count = self._live_count_locked()
            jsonl_count = self._count_jsonl_lines(self.jsonl_path)
            if db_count == jsonl_count:
                return                                  # in agreement — the common case, no parsing
            if db_count == 0 and jsonl_count > 0:
                # legacy import: every line → the db, in file order, under the current generation.
                self._snapshot_jsonl_once(self.jsonl_path)
                self.conn.execute("BEGIN IMMEDIATE")
                try:
                    for rec in self._read_jsonl_lines(self.jsonl_path):
                        self.conn.execute(
                            "INSERT INTO records(generation, body_json) VALUES(?,?)",
                            (self._generation, self._canon(rec)))
                    self.conn.execute("COMMIT")
                except Exception:
                    self.conn.execute("ROLLBACK")
                    raise
            else:
                # the db is the crash-safe truth; repair the mirror to match (torn or partial tail).
                self._snapshot_jsonl_once(self.jsonl_path)
                self._rewrite_mirror_locked(self._live_bodies_locked())

    def _snapshot_jsonl_once(self, path: Path) -> None:
        """Preserve the legacy/pre-repair jsonl as ``<name>.migrated`` exactly once (rollback target).
        Never overwrites an existing snapshot — the FIRST observed legacy state is the one we keep."""
        if not path.exists():
            return
        snapshot = path.with_name(path.name + MIGRATED_SUFFIX)
        if not snapshot.exists():
            snapshot.write_bytes(path.read_bytes())

    def _rewrite_mirror_locked(self, bodies: list[dict]) -> None:
        """Rewrite the live jsonl mirror atomically from db rows (caller holds the lock). Used only to
        REPAIR a torn mirror from the authoritative db; the prior mirror is already snapshotted."""
        tmp = self.jsonl_path.with_suffix(self.jsonl_path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            for body in bodies:
                fh.write(self._canon(body) + "\n")
        os.replace(tmp, self.jsonl_path)

    # -- the append-log API ---------------------------------------------------------------------
    def append(self, record: dict) -> int:
        """Append one record. The db INSERT is the crash-safe commit; the jsonl mirror line is written
        from the same canonical bytes under the same lock. Returns the db ``seq`` (a stable id)."""
        if not isinstance(record, dict):
            raise TypeError("AppendLog records must be JSON objects (dict)")
        body = self._canon(record)
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO records(generation, body_json) VALUES(?,?)", (self._generation, body))
            seq = int(cur.lastrowid)
            # mirror AFTER the committed insert (isolation_level=None autocommits the INSERT): the db
            # is the source of truth, so a crash between the two leaves the db right and the mirror is
            # repaired from it on the next start (never the reverse — no mirror line without a db row).
            with self.jsonl_path.open("a", encoding="utf-8") as fh:
                fh.write(body + "\n")
            return seq

    def iter(self, predicate: Callable[[dict], bool] | None = None) -> Iterator[dict]:
        """Yield live-generation records oldest→newest, optionally filtered. Snapshots the rows under
        the lock first (cheap) so iteration is safe while another thread appends."""
        for body in self._live_bodies():
            rec = json.loads(body) if isinstance(body, str) else body
            if predicate is None or predicate(rec):
                yield rec

    def all(self, predicate: Callable[[dict], bool] | None = None) -> list[dict]:
        """``iter`` materialized — the common case (the services build lists/replays)."""
        return list(self.iter(predicate))

    def count(self) -> int:
        """Number of records in the LIVE generation (a rotated ``.1`` is excluded, by design)."""
        with self._lock:
            row = self.conn.execute(
                "SELECT COUNT(*) FROM records WHERE generation=?", (self._generation,)).fetchone()
        return int(row[0])

    def rotate(self) -> int:
        """Close the current generation LOSSLESSLY and start a fresh one. Mirrors the services' size
        rotation: the live jsonl is renamed to ``<name>.1`` (exactly one kept; a later rotation
        replaces it), and the db's generation counter is bumped so ``count``/``iter`` describe only the
        new live generation — the prior generation's rows STAY in the db (preserved evidence, queryable
        via ``iter_generation``), they are simply no longer "live". Returns the new generation number.
        """
        with self._lock:
            if self.jsonl_path.exists():
                os.replace(self.jsonl_path, self.jsonl_path.with_name(self.jsonl_path.name + ROTATED_SUFFIX))
            self._set_generation(self._generation + 1)
            return self._generation

    def iter_generation(self, generation: int) -> Iterator[dict]:
        """Records of a SPECIFIC (e.g. rotated-out) generation — the lossless rehydration path."""
        with self._lock:
            rows = self.conn.execute(
                "SELECT body_json FROM records WHERE generation=? ORDER BY seq", (generation,)).fetchall()
        for (body,) in rows:
            yield json.loads(body)

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    # -- internals ------------------------------------------------------------------------------
    @staticmethod
    def _canon(record: dict) -> str:
        """Canonical one-line JSON for a record — ``sort_keys`` so the mirror bytes are stable and
        match what the services already write (``json.dumps(rec, sort_keys=True)``)."""
        return json.dumps(record, sort_keys=True)

    def _live_count_locked(self) -> int:
        """O(1) live-generation row count (indexed). The cheap side of the startup reconcile."""
        return int(self.conn.execute(
            "SELECT COUNT(*) FROM records WHERE generation=?", (self._generation,)).fetchone()[0])

    @staticmethod
    def _count_jsonl_lines(path: Path) -> int:
        """Count non-blank lines in the mirror WITHOUT parsing JSON — the cheap side of the startup
        reconcile (parsing every line was the cost that made the old restart O(n·parse); a steady-state
        mirror is one canonical dict per line so this count equals the db row count exactly). Blank
        trailing lines are ignored so a stray newline never forces a spurious repair."""
        if not path.exists():
            return 0
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())

    def _live_bodies_locked(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT body_json FROM records WHERE generation=? ORDER BY seq", (self._generation,)).fetchall()
        return [json.loads(b) for (b,) in rows]

    def _live_bodies(self) -> list[str]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT body_json FROM records WHERE generation=? ORDER BY seq",
                (self._generation,)).fetchall()
        return [b for (b,) in rows]

    @staticmethod
    def _read_jsonl_lines(path: Path) -> list[dict]:
        """Parse a jsonl into dicts, skipping unparseable lines (a torn tail after a crash must never
        wedge startup) — exactly the tolerance the services' own loaders already apply."""
        if not path.exists():
            return []
        out: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict):
                out.append(rec)
        return out


def open_log(jsonl_path: Path | str, *, db_path: Path | None = None) -> AppendLog:
    """Convenience constructor mirroring the repo's ``open(...)``-style factories."""
    return AppendLog(Path(jsonl_path), db_path=db_path)


# --------------------------------------------------------------------------------------------------
# self-test — concurrency (threads), WAL, restart reopen, migration-from-jsonl, lossless rotation
# --------------------------------------------------------------------------------------------------
def _self_test() -> int:
    """Offline proof of the append-log contract: a legacy jsonl migrates losslessly (every line
    imported, the legacy file preserved as .migrated), reads serve from the db, N threads append with
    no loss/dup under WAL, a restart reopens with EQUAL state (O(attach), not a re-parse), rotation
    renames the live generation to .1 (preserved) while the db keeps the rotated rows, and a torn
    mirror is repaired from the crash-safe db. Temp dirs, stdlib-only. Exit 0/1."""
    import shutil
    import tempfile

    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = Path(tempfile.mkdtemp(prefix="jsonl-store-selftest-"))
    try:
        state = tmp / "state"
        state.mkdir(parents=True)
        idx = tmp / "index"          # the db lives OUTSIDE the state dir (as in production)
        jsonl = state / "log.jsonl"

        # ── 1) MIGRATION FROM A PRE-SEEDED LEGACY JSONL (lossless) ──────────────
        legacy = [{"i": i, "kind": "legacy", "v": f"row-{i}"} for i in range(1000)]
        with jsonl.open("w", encoding="utf-8") as fh:
            for rec in legacy:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
        legacy_bytes = jsonl.read_bytes()
        log = AppendLog(jsonl, db_path=idx / "log.db")
        ck("migration imported every legacy line into the db", log.count() == 1000, str(log.count()))
        ck("migration preserved order + content (db == legacy)",
           log.all() == legacy)
        migrated = jsonl.with_name(jsonl.name + MIGRATED_SUFFIX)
        ck("legacy jsonl LEFT IN PLACE (never dropped)", jsonl.exists()
           and len(jsonl.read_text(encoding="utf-8").splitlines()) == 1000)
        ck("legacy jsonl additionally snapshotted to .migrated (rollback target, byte-identical)",
           migrated.exists() and migrated.read_bytes() == legacy_bytes)
        ck("the db lives OUTSIDE the state dir (no binary file would poison a hygiene scan)",
           not any(p.suffix in (".db", ".db-wal", ".db-shm") for p in state.glob("**/*")))

        # ── 2) reads serve from the db; a new append mirrors to the jsonl ───────
        new_seq = log.append({"i": 1000, "kind": "fresh", "v": "row-1000"})
        ck("append returns a monotonic db seq", new_seq == 1001, str(new_seq))
        ck("count reflects the append immediately (db-served)", log.count() == 1001)
        ck("the jsonl mirror grew by exactly one line (durability contract intact)",
           len(jsonl.read_text(encoding="utf-8").splitlines()) == 1001)
        ck("filtered iter works", [r["i"] for r in log.iter(lambda r: r["kind"] == "fresh")] == [1000])

        # reads are db-served: blanking the mirror does NOT change live reads (the db is the engine);
        # the mirror is the DURABLE artifact for restart — restored + proven right below.
        saved_mirror = jsonl.read_bytes()
        jsonl.write_text("", encoding="utf-8")
        ck("reads are db-served, not a per-call jsonl re-parse", log.count() == 1001)
        jsonl.write_bytes(saved_mirror)

        # ── 3) WAL CONCURRENCY: N threads append, no loss / no dup ──────────────
        threads_n, per_thread = 8, 50
        base = log.count()
        barrier = threading.Barrier(threads_n)

        def _worker(t: int) -> None:
            barrier.wait()
            for k in range(per_thread):
                log.append({"thread": t, "k": k, "kind": "concurrent"})

        workers = [threading.Thread(target=_worker, args=(t,)) for t in range(threads_n)]
        for w in workers:
            w.start()
        for w in workers:
            w.join()
        added = log.all(lambda r: r.get("kind") == "concurrent")
        seen = {(r["thread"], r["k"]) for r in added}
        ck("N threads appended every record (no loss)", len(added) == threads_n * per_thread,
           str(len(added)))
        ck("no duplicates under concurrent WAL appends", len(seen) == threads_n * per_thread,
           f"{len(seen)} unique of {len(added)}")
        ck("count == db rows == mirror lines after concurrency",
           log.count() == base + threads_n * per_thread
           == len(jsonl.read_text(encoding="utf-8").splitlines()), str(log.count()))

        # ── 4) RESTART REOPEN: equal state, O(attach) not a re-parse ────────────
        expected_after = log.all()
        log.close()
        log2 = AppendLog(jsonl, db_path=idx / "log.db")
        ck("restart rehydrates the SAME count", log2.count() == base + threads_n * per_thread)
        ck("restart rehydrates EQUAL records (order + content)", log2.all() == expected_after)
        # a restart with the db already present must NOT re-snapshot or mutate the mirror
        ck("restart did not re-import (mirror unchanged)",
           len(jsonl.read_text(encoding="utf-8").splitlines()) == log2.count())

        # ── 5) ROTATION preserves a generation losslessly ──────────────────────
        pre_rotate = log2.all()
        live_before = log2.count()
        gen = log2.rotate()
        ck("rotate bumped the generation", gen == GENERATION_START + 1, str(gen))
        ck("rotated jsonl renamed to .1 (preserved, full generation)",
           jsonl.with_name(jsonl.name + ROTATED_SUFFIX).exists()
           and len(jsonl.with_name(jsonl.name + ROTATED_SUFFIX).read_text(encoding="utf-8").splitlines())
           == live_before)
        ck("the live generation is empty after rotation", log2.count() == 0)
        log2.append({"i": 0, "kind": "post-rotate"})
        ck("a fresh append lands in the new live generation only", log2.count() == 1)
        ck("the rotated-out generation is STILL in the db (lossless, queryable)",
           list(log2.iter_generation(GENERATION_START)) == pre_rotate)
        # rotation survives a restart: counters describe the live generation only
        log2.close()
        log3 = AppendLog(jsonl, db_path=idx / "log.db")
        ck("restart after rotation rehydrates the live generation only (count==1)", log3.count() == 1)
        ck("restart after rotation still exposes the rotated generation in the db",
           list(log3.iter_generation(GENERATION_START)) == pre_rotate)
        log3.close()

        # ── 6) TORN-MIRROR REPAIR: the crash-safe db fixes a torn jsonl tail ────
        torn_state = tmp / "torn"
        torn_state.mkdir()
        tj = torn_state / "torn.jsonl"
        tlog = AppendLog(tj, db_path=tmp / "torn-index" / "torn.db")
        for i in range(20):
            tlog.append({"i": i})
        tlog.close()
        # simulate a crash mid-append: the db has 20 committed rows; the mirror's tail is torn
        # (a truncated final line + a half-written extra) — exactly the corruption WAL prevents.
        good = tj.read_text(encoding="utf-8").splitlines()
        tj.write_text("\n".join(good[:18]) + "\n" + '{"i": 18, "par', encoding="utf-8")  # torn tail
        repaired = AppendLog(tj, db_path=tmp / "torn-index" / "torn.db")
        ck("a torn mirror is detected and repaired from the crash-safe db",
           repaired.count() == 20
           and len(tj.read_text(encoding="utf-8").splitlines()) == 20
           and [r["i"] for r in repaired.all()] == list(range(20)))
        ck("the pre-repair (torn) mirror was snapshotted, not destroyed (lossless)",
           tj.with_name(tj.name + MIGRATED_SUFFIX).exists())
        repaired.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + ("PASS — _jsonl_store --self-test: SQLite-WAL append-log behind the JSONL contract — "
                  "legacy jsonl migrates losslessly (every line imported, original preserved + "
                  ".migrated snapshot), reads served from the db, N-thread WAL appends with no "
                  "loss/dup, restart reopens with EQUAL state (O(attach), not a re-parse), rotation "
                  "renames a full generation to .1 while the db keeps the rotated rows (queryable), "
                  "and a torn mirror is repaired from the crash-safe db."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true",
                        help="offline append-log proof (concurrency, WAL, restart, migration, rotation)")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
