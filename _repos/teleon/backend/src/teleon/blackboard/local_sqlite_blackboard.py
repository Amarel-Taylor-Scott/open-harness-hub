"""src.teleon.blackboard.local_sqlite_blackboard — the OFFLINE local SQLite blackboard (the correctness invariant).

:class:`LocalSqliteBlackboard` implements
:class:`~src.teleon.ports.blackboard_provider.BlackboardProviderPort` over an in-process ``sqlite3`` database
(``sqlite3`` is stdlib). It is the durable, typed, tenant-isolated, source-backed analytical STATE substrate for
one stateful-swarm task: bounded workers APPEND typed entries (signals / observations / gaps / calculations /
analyses / synthesis / sources) across iterations instead of re-reading docs every turn.

THE STORE IS APPEND-ONLY AND TRUTH-FREE:

  - **append-only** — entries are written once; there is no UPDATE and no DELETE on the entries table, and any
    attempt to re-write an existing ``entry_id`` with DIFFERENT content raises
    :class:`BlackboardWriteRejected` (``append_only_violation``). Re-writing the SAME content is idempotent
    (the content-addressed id makes a duplicate a no-op), so a worker that retries its turn is safe.
  - **source-backed** — an ``observation`` with empty/missing ``source_refs`` is REJECTED (``sourceless_observation``):
    a sourceless claim can never be reconciled or promoted by Baltor (``BlackboardObservation``).
  - **never truth** — an entry that sets ``serves_truth`` true is REJECTED (``serves_truth_forbidden``); every
    STORED entry's ``serves_truth`` is pinned False (``BLACKBOARD_SERVES_TRUTH``). A blackboard is working
    state; only Baltor's separate governance + verification rail may promote anything derived from it.
  - **tenant-isolated** — an entry (or a create) with no ``tenant_scope`` is REJECTED (``missing_tenant_scope``);
    working state is never cross-tenant.
  - **receipted** — every ``append_entry`` REQUIRES a ``worker_receipt`` (else ``missing_receipt``); the receipt
    is recorded (provenance of WHAT the worker did — it never asserts the entries are true).

Reads are a DETERMINISTIC projection of the append-only stream: :meth:`query` orders by insertion sequence then
``entry_id`` (a total order), so the same (db contents, filters) always returns the same rows in the same order.

Teleon-owned: imports only the stdlib + Teleon id helpers (``canonical_id`` / ``sha256_hex``) — never Baltor.
Deterministic given the same (inputs, ``now``): content-addressed ids, no RNG, no wall-clock (``now`` is injected).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.teleon.experiments.ids import canonical_id, sha256_hex
from src.teleon.ports.blackboard_provider import (
    BLACKBOARD_ENTRY_KINDS,
    BLACKBOARD_SERVES_TRUTH,
    KIND_GAP,
    KIND_OBSERVATION,
    KIND_SIGNAL,
    KIND_SOURCE,
    STATUS_OPEN,
    BlackboardWriteRejected,
)

py_var_src_teleon_blackboard_local_sqlite_blackboard___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])

#: provider id of the one active, offline, deterministic local blackboard store.
py_const_src_teleon_blackboard_local_sqlite_blackboard__LOCAL_SQLITE_BLACKBOARD_PROVIDER_ID = "blackboard.local_sqlite@v1"
#: default on-disk location (under .agent/, like the durable fleet ledger). The path is INJECTABLE — tests pass a
#: tempfile / ``:memory:`` so the real .agent db is never touched.
py_const_src_teleon_blackboard_local_sqlite_blackboard__DEFAULT_DB_PATH = str(py_var_src_teleon_blackboard_local_sqlite_blackboard___REPO / ".agent" / "blackboard.local.db")
#: the hash prefix used for the receipt content hashes (tamper-evident; not the raw bytes).
py_const_src_teleon_blackboard_local_sqlite_blackboard__HASH_PREFIX = "sha256:"


def py_function_src_teleon_blackboard_local_sqlite_blackboard___content_hash(py_arg_src_teleon_blackboard_local_sqlite_blackboard__content_hash__value: Any) -> str:
    """A ``sha256:<hex>`` content hash over the canonical bytes of ``value`` (tamper-evident; deterministic)."""
    return f"{py_const_src_teleon_blackboard_local_sqlite_blackboard__HASH_PREFIX}{sha256_hex(py_arg_src_teleon_blackboard_local_sqlite_blackboard__content_hash__value)}"


class py_class_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard:
    """The offline correctness-invariant blackboard store. APPEND-ONLY, tenant-isolated, source-backed, and
    truth-free (every stored entry's ``serves_truth`` is pinned False). Deterministic when ``now`` is injected.

    ``db_path`` is injectable (default :data:`DEFAULT_DB_PATH` under ``.agent/``); pass a tempfile or
    ``":memory:"`` in tests. The connection is opened once and the schema created on construction.
    """

    provider_id = py_const_src_teleon_blackboard_local_sqlite_blackboard__LOCAL_SQLITE_BLACKBOARD_PROVIDER_ID

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or py_const_src_teleon_blackboard_local_sqlite_blackboard__DEFAULT_DB_PATH
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread False so a single in-process store is usable from helper threads; we still serialize
        # through one connection and never share across processes (local-first, offline).
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    # ---- schema --------------------------------------------------------------------------
    def _init_schema(self) -> None:
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__init_schema__cur = self._conn.cursor()
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__init_schema__cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS blackboards (
                blackboard_id TEXT PRIMARY KEY,
                task          TEXT NOT NULL,
                tenant_scope  TEXT NOT NULL,
                created_at    TEXT NOT NULL,
                status        TEXT NOT NULL,
                iteration     INTEGER NOT NULL,
                seq           INTEGER NOT NULL
            );
            -- APPEND-ONLY entry stream. seq is a monotonic insertion counter giving a total, stable read order.
            -- entry_id is the PRIMARY KEY: a content-addressed re-write of the same id+content is idempotent
            -- (INSERT OR IGNORE), and a re-write with DIFFERENT content is detected and rejected in code.
            CREATE TABLE IF NOT EXISTS entries (
                entry_id        TEXT PRIMARY KEY,
                blackboard_id   TEXT NOT NULL,
                kind            TEXT NOT NULL,
                author_worker_id TEXT NOT NULL,
                iteration       INTEGER NOT NULL,
                source_refs     TEXT NOT NULL,   -- JSON array of BlackboardSourceRef ids
                serves_truth    INTEGER NOT NULL,-- pinned 0 (False) on every stored row
                tenant_scope    TEXT NOT NULL,
                created_at      TEXT NOT NULL,
                body            TEXT NOT NULL,    -- JSON typed body (signal/observation/gap/...)
                content_hash    TEXT NOT NULL,    -- canonical hash of the stored entry (idempotency / tamper-evidence)
                receipt_id      TEXT NOT NULL,    -- the worker receipt backing this append (mandatory)
                seq             INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS receipts (
                receipt_id    TEXT PRIMARY KEY,
                blackboard_id TEXT NOT NULL,
                body          TEXT NOT NULL,       -- JSON BlackboardWorkerReceipt
                seq           INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS _seq (name TEXT PRIMARY KEY, value INTEGER NOT NULL);
            """
        )
        self._conn.commit()

    def _next_seq(self, *, autocommit: bool = True) -> int:
        """A monotonic per-store insertion counter (deterministic ordering key). Not wall-clock, not RNG.

        ``autocommit=False`` is used when the caller is already inside an explicit ``BEGIN`` / ``COMMIT``
        transaction so the increment is not committed prematurely (keeping entry + receipt atomic).
        """
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__next_seq__cur = self._conn.cursor()
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__next_seq__cur.execute("INSERT INTO _seq(name, value) VALUES('entry', 1) "
                    "ON CONFLICT(name) DO UPDATE SET value = value + 1")
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__next_seq__cur.execute("SELECT value FROM _seq WHERE name='entry'")
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__next_seq__seq = int(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__next_seq__cur.fetchone()[0])
        if autocommit:
            self._conn.commit()
        return py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__next_seq__seq

    def _transaction(self):
        """Return the underlying sqlite3 connection as a context manager for one atomic transaction.

        ``sqlite3.Connection`` supports the context-manager protocol starting with a ``BEGIN`` and ending
        with ``COMMIT`` on clean exit or ``ROLLBACK`` on exception. All writes that must be atomic (entry +
        receipt + sequence increments) run inside this context.
        """
        return self._conn

    # ---- describe / status ---------------------------------------------------------------
    def describe(self) -> dict:
        """Local-first golden-path card: append-only, no network, IS its own local_equivalent, never truth."""
        return {
            "provider_id": self.provider_id,
            "name": "local-sqlite-blackboard",
            "status": "active",
            "append_only": True,
            "requires_network": False,
            "local_equivalent": self.provider_id,
            "serves_truth": BLACKBOARD_SERVES_TRUTH,
        }

    def status(self) -> dict:
        """Always available — it needs nothing external (the honest local-first golden path)."""
        return {
            "provider_id": self.provider_id,
            "status": "active",
            "available": True,
            "append_only": True,
            "requires_network": False,
            "db_path": self.db_path,
        }

    # ---- create --------------------------------------------------------------------------
    def create_blackboard(self, task: str, tenant_scope: str, *, now: str) -> dict:
        """Open a new tenant-scoped Blackboard workspace (status=open, entry_count=0). REQUIRES a tenant_scope
        (else :class:`BlackboardWriteRejected` ``missing_tenant_scope``). The id is content-addressed from
        (task, tenant_scope, now) so the same call is idempotent. Returns the Blackboard-shaped row dict."""
        if not tenant_scope:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.MISSING_TENANT_SCOPE,
                "create_blackboard requires a non-empty tenant_scope (working state is tenant-isolated)",
            )
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_create_blackboard__blackboard_id = canonical_id("bb", task, tenant_scope, now)
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_create_blackboard__cur = self._conn.cursor()
        # idempotent create: the same (task, tenant_scope, now) re-uses the existing row (content-addressed id).
        # Wrapped in a transaction so the _seq increment + row write are atomic and never partially visible.
        with self._transaction():
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_create_blackboard__seq = self._next_seq(autocommit=False)
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_create_blackboard__cur.execute(
                "INSERT OR IGNORE INTO blackboards"
                "(blackboard_id, task, tenant_scope, created_at, status, iteration, seq) "
                "VALUES(?,?,?,?,?,?,?)",
                (py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_create_blackboard__blackboard_id, task, tenant_scope, now, STATUS_OPEN, 0, py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_create_blackboard__seq),
            )
        return self._blackboard_row(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_create_blackboard__blackboard_id)

    def _blackboard_row(self, py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__blackboard_id: str) -> dict:
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__cur = self._conn.cursor()
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__row = py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__cur.execute(
            "SELECT blackboard_id, task, tenant_scope, created_at, status, iteration FROM blackboards "
            "WHERE blackboard_id=?",
            (py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__blackboard_id,),
        ).fetchone()
        if py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__row is None:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.UNKNOWN_BLACKBOARD, f"no blackboard {py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__blackboard_id!r}"
            )
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__count = py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__cur.execute(
            "SELECT COUNT(*) FROM entries WHERE blackboard_id=?", (py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__blackboard_id,)
        ).fetchone()[0]
        return {
            "blackboard_id": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__row["blackboard_id"],
            "task": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__row["task"],
            "tenant_scope": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__row["tenant_scope"],
            "created_at": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__row["created_at"],
            "status": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__row["status"],
            "entry_count": int(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__count),  # projection of the entry stream (Blackboard)
            "iteration": int(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__blackboard_row__row["iteration"]),
        }

    # ---- append (the governed write) -----------------------------------------------------
    def append_entry(self, py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__blackboard_id: str, py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry: dict, *, worker_receipt: dict, now: str) -> dict:
        """APPEND one typed BlackboardEntry under a MANDATORY ``worker_receipt``; return the stored row dict.

        All governance guards raise :class:`BlackboardWriteRejected` and store NOTHING. The stored row's
        ``serves_truth`` is pinned False (the input's ``serves_truth`` is read only to REJECT a truthy value).
        Idempotent on a content-identical re-write of the same ``entry_id``; an append-only violation on a
        content-DIFFERENT re-write. Deterministic when ``now`` is injected.

        The entry insert + receipt insert + sequence increments run in a single SQLite transaction so a
        crash mid-write never leaves an entry without a receipt (or vice versa).
        """
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__bb = self._blackboard_row(py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__blackboard_id)  # raises unknown_blackboard if absent

        # --- guard: mandatory worker receipt ---------------------------------------------
        if not worker_receipt or not worker_receipt.get("worker_id"):
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.MISSING_RECEIPT,
                "append_entry requires a worker_receipt with a worker_id (provenance is mandatory)",
            )

        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__kind = py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry.get("kind")
        if py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__kind not in BLACKBOARD_ENTRY_KINDS:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.INVALID_KIND,
                f"kind {py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__kind!r} not one of {BLACKBOARD_ENTRY_KINDS}",
            )

        # --- guard: serves_truth may NEVER be true ---------------------------------------
        if py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry.get("serves_truth") is True:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.SERVES_TRUTH_FORBIDDEN,
                "a blackboard entry is working state, never served truth (serves_truth must be false)",
            )

        # --- guard: tenant scope present AND matches the blackboard ----------------------
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__tenant_scope = py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry.get("tenant_scope") or ""
        if not py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__tenant_scope:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.MISSING_TENANT_SCOPE,
                "entry requires a non-empty tenant_scope (working state is tenant-isolated)",
            )
        if py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__tenant_scope != py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__bb["tenant_scope"]:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.MISSING_TENANT_SCOPE,
                f"entry tenant_scope {py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__tenant_scope!r} != blackboard tenant_scope {py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__bb['tenant_scope']!r} "
                "(never cross-tenant)",
            )

        # --- guard: an observation must be source-backed (non-empty source_refs) ----------
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__source_refs = list(py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry.get("source_refs") or [])
        if py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__kind == KIND_OBSERVATION and len(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__source_refs) == 0:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.SOURCELESS_OBSERVATION,
                "an observation requires non-empty source_refs (a sourceless claim can never be promoted)",
            )

        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__iteration = int(py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry.get("iteration", py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__bb["iteration"]) or 0)
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__author_worker_id = py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry.get("author_worker_id") or worker_receipt.get("worker_id")
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__body = py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry.get("body", {})

        # content-addressed entry_id: stable across retries of the SAME content, distinct for different content.
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry_id = py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry.get("entry_id") or canonical_id(
            "bbe", py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__blackboard_id, py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__kind, py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__author_worker_id, str(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__iteration),
            json.dumps(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__body, sort_keys=True, separators=(",", ":")),
            json.dumps(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__source_refs, sort_keys=True, separators=(",", ":")),
        )

        # canonical hash of the STORED shape (kind + lineage + body + source_refs); the basis of idempotency.
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__stored_core = {
            "blackboard_id": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__blackboard_id,
            "kind": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__kind,
            "author_worker_id": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__author_worker_id,
            "iteration": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__iteration,
            "source_refs": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__source_refs,
            "tenant_scope": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__tenant_scope,
            "body": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__body,
        }
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__content_hash = py_function_src_teleon_blackboard_local_sqlite_blackboard___content_hash(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__stored_core)

        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__cur = self._conn.cursor()
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__existing = py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__cur.execute(
            "SELECT content_hash FROM entries WHERE entry_id=?", (py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry_id,)
        ).fetchone()
        if py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__existing is not None:
            # --- guard: append-only. Identical content => idempotent no-op; different content => REJECT. ---
            if py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__existing["content_hash"] == py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__content_hash:
                return self._entry_row(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry_id)  # idempotent: the same write twice is a no-op
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.APPEND_ONLY_VIOLATION,
                f"entry {py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry_id!r} already exists with different content (no update/delete — append-only)",
            )

        # record the mandatory worker receipt (idempotent on its own content-addressed id).
        # Wrapped in a transaction so entry + receipt + sequence increments are all-or-nothing.
        with self._transaction():
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__receipt_id = self._record_receipt(
                py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__blackboard_id, worker_receipt, entry_ids=[py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry_id], now=now, autocommit=False
            )
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__seq = self._next_seq(autocommit=False)
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__cur.execute(
                "INSERT INTO entries"
                "(entry_id, blackboard_id, kind, author_worker_id, iteration, source_refs, serves_truth, "
                " tenant_scope, created_at, body, content_hash, receipt_id, seq) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry_id,
                    py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__blackboard_id,
                    py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__kind,
                    py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__author_worker_id,
                    py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__iteration,
                    json.dumps(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__source_refs, separators=(",", ":")),
                    0,  # serves_truth pinned False on every stored row — THE INVARIANT
                    py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__tenant_scope,
                    now,
                    json.dumps(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__body, separators=(",", ":")),
                    py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__content_hash,
                    py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__receipt_id,
                    py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__seq,
                ),
            )
            # keep the blackboard.iteration projection monotonic (never rewinds; entry_count is computed on read).
            if py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__iteration > int(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__bb["iteration"]):
                py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__cur.execute(
                    "UPDATE blackboards SET iteration=? WHERE blackboard_id=?", (py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__iteration, py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__blackboard_id)
                )
        return self._entry_row(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_append_entry__entry_id)

    def _record_receipt(
        self,
        py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__blackboard_id: str,
        py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_receipt: dict,
        *,
        entry_ids: list[str],
        now: str,
        autocommit: bool = True,
    ) -> str:
        """Persist a BlackboardWorkerReceipt-shaped row and return its content-addressed receipt_id.

        The receipt records WHAT the worker did (worker id/kind, entries written, input/output content hashes,
        start/complete timestamps). It NEVER asserts the entries are true. No raw secrets/keys: any
        ``llm_route_receipt_ref`` is kept verbatim only if it is an env:// / receipt-id handle (the schema's
        pattern); we do not synthesize one. Idempotent on its content-addressed id.

        ``autocommit=False`` is used when the caller is already inside an explicit transaction so the
        sequence increment + receipt insert are committed together with the entry insert.
        """
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_id = py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_receipt["worker_id"]
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_kind = py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_receipt.get("worker_kind", "worker")
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__input_hash = py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_receipt.get("input_hash") or py_function_src_teleon_blackboard_local_sqlite_blackboard___content_hash(
            {"blackboard_id": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__blackboard_id, "worker_id": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_id, "entry_ids": entry_ids}
        )
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__output_hash = py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_receipt.get("output_hash") or py_function_src_teleon_blackboard_local_sqlite_blackboard___content_hash({"entry_ids": entry_ids})
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__receipt_id = py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_receipt.get("receipt_id") or canonical_id(
            "bbr", py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__blackboard_id, py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_id, py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_kind, py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__output_hash, now
        )
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__body = {
            "receipt_id": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__receipt_id,
            "blackboard_id": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__blackboard_id,
            "worker_id": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_id,
            "worker_kind": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_kind,
            "entries_written": list(entry_ids),
            "input_hash": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__input_hash,
            "output_hash": py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__output_hash,
            "started_at": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_receipt.get("started_at", now),
            "completed_at": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_receipt.get("completed_at", now),
        }
        # optional LLM-route ref — kept ONLY when it is a handle (never a raw key value).
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__ref = py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__worker_receipt.get("llm_route_receipt_ref")
        if isinstance(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__ref, str) and py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__ref.startswith(("env://", "receipt:", "rcpt-", "mir-")):
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__body["llm_route_receipt_ref"] = py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__ref

        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__cur = self._conn.cursor()
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__existing = py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__cur.execute("SELECT receipt_id FROM receipts WHERE receipt_id=?", (py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__receipt_id,)).fetchone()
        if py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__existing is None:
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__seq = self._next_seq(autocommit=autocommit)
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__cur.execute(
                "INSERT INTO receipts(receipt_id, blackboard_id, body, seq) VALUES(?,?,?,?)",
                (py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__receipt_id, py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__blackboard_id, json.dumps(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__body, separators=(",", ":")), py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__seq),
            )
        if autocommit:
            self._conn.commit()
        return py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__record_receipt__receipt_id

    def _entry_row(self, py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__entry_row__entry_id: str) -> dict:
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__entry_row__cur = self._conn.cursor()
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__entry_row__row = py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__entry_row__cur.execute(
            "SELECT entry_id, blackboard_id, kind, author_worker_id, iteration, source_refs, serves_truth, "
            "tenant_scope, created_at, body, content_hash, receipt_id FROM entries WHERE entry_id=?",
            (py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__entry_row__entry_id,),
        ).fetchone()
        return self._row_to_entry(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__entry_row__row)

    @staticmethod
    def _row_to_entry(py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row: sqlite3.Row) -> dict:
        return {
            "entry_id": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row["entry_id"],
            "blackboard_id": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row["blackboard_id"],
            "kind": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row["kind"],
            "author_worker_id": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row["author_worker_id"],
            "iteration": int(py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row["iteration"]),
            "source_refs": json.loads(py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row["source_refs"]),
            "serves_truth": bool(py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row["serves_truth"]),  # always False (stored as 0)
            "tenant_scope": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row["tenant_scope"],
            "created_at": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row["created_at"],
            "body": json.loads(py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row["body"]),
            "content_hash": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row["content_hash"],
            "receipt_id": py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard__row_to_entry__row["receipt_id"],
        }

    # ---- query (deterministic read projection) -------------------------------------------
    def query(
        self,
        py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__blackboard_id: str,
        *,
        kind: str | None = None,
        py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__author_worker_id: str | None = None,
        py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__iteration: int | None = None,
        py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__limit: int | None = None,
    ) -> list[dict]:
        """Return stored entries in a DETERMINISTIC total order: insertion sequence, then entry_id as a
        tie-breaker. Pure projection of the append-only stream — the same (db, filters) always yields the same
        rows in the same order. Nothing here is served truth (every row's ``serves_truth`` is False)."""
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__clauses = ["blackboard_id = ?"]
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__params: list[Any] = [py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__blackboard_id]
        if kind is not None:
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__clauses.append("kind = ?")
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__params.append(kind)
        if py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__author_worker_id is not None:
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__clauses.append("author_worker_id = ?")
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__params.append(py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__author_worker_id)
        if py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__iteration is not None:
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__clauses.append("iteration = ?")
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__params.append(int(py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__iteration))
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__sql = (
            "SELECT entry_id, blackboard_id, kind, author_worker_id, iteration, source_refs, serves_truth, "
            "tenant_scope, created_at, body, content_hash, receipt_id FROM entries WHERE "
            + " AND ".join(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__clauses)
            + " ORDER BY seq ASC, entry_id ASC"  # total, stable order (insertion then id)
        )
        if py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__limit is not None and py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__limit >= 0:
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__sql += " LIMIT ?"
            py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__params.append(int(py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__limit))
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__cur = self._conn.cursor()
        return [self._row_to_entry(r) for r in py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__cur.execute(py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__sql, py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_query__params).fetchall()]

    def get_receipts(self, py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_get_receipts__blackboard_id: str) -> list[dict]:
        """Return the BlackboardWorkerReceipt rows for ``blackboard_id`` in deterministic (insertion) order.
        A receipt records WHAT a worker did; it never asserts the written entries are true."""
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_get_receipts__cur = self._conn.cursor()
        py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_get_receipts__rows = py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_get_receipts__cur.execute(
            "SELECT body FROM receipts WHERE blackboard_id=? ORDER BY seq ASC, receipt_id ASC",
            (py_arg_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_get_receipts__blackboard_id,),
        ).fetchall()
        return [json.loads(r["body"]) for r in py_local_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard_get_receipts__rows]

    def close(self) -> None:
        """Close the underlying connection (tests / short-lived stores)."""
        self._conn.close()


# ---- seed / demo helper -----------------------------------------------------------------
def py_function_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard(*, db_path: str | None = None, now: str = "2026-01-01T00:00:00Z",
                         tenant_scope: str = "tenant-demo") -> dict:
    """Build a deterministic 3-entry demo blackboard and return ``{provider, blackboard_id, entries}``.

    The three entries exercise the typed kinds + the source-backed rule end-to-end, all under worker receipts:

      1. a **signal** — an open question directing the swarm (no source_refs required; procedural);
      2. a **source** then an **observation** that CITES it — the observation's ``source_refs`` is non-empty,
         so it passes the source-backed guard (a sourceless observation would be rejected);
      3. a **gap** — a named hole that blocks the analysis (convergence currency).

    Deterministic given the same (db_path, now, tenant_scope): content-addressed ids; no RNG / no wall-clock.
    Every stored entry carries ``serves_truth=False`` — this is working state, never served truth. Pass a
    tempfile / ``":memory:"`` ``db_path`` so the real ``.agent`` db is never touched.
    """
    bb = py_class_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard(db_path=db_path)
    py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__board = bb.create_blackboard(
        task="What is the sanction's effective date?", tenant_scope=tenant_scope, now=now
    )
    py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__bid = py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__board["blackboard_id"]

    def receipt(py_arg_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard_receipt__worker_id: str, py_arg_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard_receipt__worker_kind: str) -> dict:
        # a minimal worker receipt (hashes are filled in by the store from the entry lineage); no raw keys.
        return {"worker_id": py_arg_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard_receipt__worker_id, "worker_kind": py_arg_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard_receipt__worker_kind, "started_at": now, "completed_at": now}

    # 1) a signal (procedural; no sources)
    py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__signal = bb.append_entry(
        py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__bid,
        {
            "kind": KIND_SIGNAL,
            "author_worker_id": "worker.router",
            "iteration": 0,
            "tenant_scope": tenant_scope,
            "source_refs": [],
            "body": {"question": "What is the sanction's effective date?", "priority": 10},
        },
        worker_receipt=receipt("worker.router", "router"),
        now=now,
    )

    # 2a) post a source reference (a stable provenance handle: doc#section)
    py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__source = bb.append_entry(
        py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__bid,
        {
            "kind": KIND_SOURCE,
            "author_worker_id": "worker.retriever",
            "iteration": 1,
            "tenant_scope": tenant_scope,
            "source_refs": [],
            "body": {
                "source_id": "src.ofac.notice",
                "handle": "doc#ofac-notice-2026-04-15/section-1",
                "authority_rank": 90,
                "retrieved_at": now,
            },
        },
        worker_receipt=receipt("worker.retriever", "retriever"),
        now=now,
    )
    py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__source_handle_id = py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__source["body"]["source_id"]

    # 2b) an observation that CITES the source (non-empty source_refs => passes the source-backed guard)
    py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__observation = bb.append_entry(
        py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__bid,
        {
            "kind": KIND_OBSERVATION,
            "author_worker_id": "worker.observer",
            "iteration": 1,
            "tenant_scope": tenant_scope,
            "source_refs": [py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__source_handle_id],
            "body": {
                "statement": "The sanction took effect on 2026-04-15.",
                "source_refs": [py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__source_handle_id],
                "confidence": 0.9,
            },
        },
        worker_receipt=receipt("worker.observer", "observer"),
        now=now,
    )

    # 3) a gap (a named hole — convergence currency)
    py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__gap = bb.append_entry(
        py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__bid,
        {
            "kind": KIND_GAP,
            "author_worker_id": "worker.observer",
            "iteration": 1,
            "tenant_scope": tenant_scope,
            "source_refs": [],
            "body": {
                "missing": "Whether the effective date applies to pre-existing contracts.",
                "why_it_matters": "Determines if legacy obligations are in scope of the sanction.",
                "status": "open",
            },
        },
        worker_receipt=receipt("worker.observer", "observer"),
        now=now,
    )

    return {
        "provider": bb,
        "blackboard_id": py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__bid,
        "entries": [py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__signal, py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__source, py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__observation, py_local_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard__gap],
    }


__all__ = [
    "py_class_src_teleon_blackboard_local_sqlite_blackboard__LocalSqliteBlackboard",
    "py_const_src_teleon_blackboard_local_sqlite_blackboard__LOCAL_SQLITE_BLACKBOARD_PROVIDER_ID",
    "py_const_src_teleon_blackboard_local_sqlite_blackboard__DEFAULT_DB_PATH",
    "py_const_src_teleon_blackboard_local_sqlite_blackboard__HASH_PREFIX",
    "py_function_src_teleon_blackboard_local_sqlite_blackboard__seed_demo_blackboard",
]
