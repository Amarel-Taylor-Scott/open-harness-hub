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
    a sourceless claim can never be reconciled or promoted by Baltor (``BlackboardObservation.v1``).
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

_REPO = Path(__file__).resolve().parents[3]

#: provider id of the one active, offline, deterministic local blackboard store.
LOCAL_SQLITE_BLACKBOARD_PROVIDER_ID = "blackboard.local_sqlite@v1"
#: default on-disk location (under .agent/, like the durable fleet ledger). The path is INJECTABLE — tests pass a
#: tempfile / ``:memory:`` so the real .agent db is never touched.
DEFAULT_DB_PATH = str(_REPO / ".agent" / "blackboard.local.db")
#: the hash prefix used for the receipt content hashes (tamper-evident; not the raw bytes).
HASH_PREFIX = "sha256:"


def _content_hash(value: Any) -> str:
    """A ``sha256:<hex>`` content hash over the canonical bytes of ``value`` (tamper-evident; deterministic)."""
    return f"{HASH_PREFIX}{sha256_hex(value)}"


class LocalSqliteBlackboard:
    """The offline correctness-invariant blackboard store. APPEND-ONLY, tenant-isolated, source-backed, and
    truth-free (every stored entry's ``serves_truth`` is pinned False). Deterministic when ``now`` is injected.

    ``db_path`` is injectable (default :data:`DEFAULT_DB_PATH` under ``.agent/``); pass a tempfile or
    ``":memory:"`` in tests. The connection is opened once and the schema created on construction.
    """

    provider_id = LOCAL_SQLITE_BLACKBOARD_PROVIDER_ID

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread False so a single in-process store is usable from helper threads; we still serialize
        # through one connection and never share across processes (local-first, offline).
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    # ---- schema --------------------------------------------------------------------------
    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(
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

    def _next_seq(self) -> int:
        """A monotonic per-store insertion counter (deterministic ordering key). Not wall-clock, not RNG."""
        cur = self._conn.cursor()
        cur.execute("INSERT INTO _seq(name, value) VALUES('entry', 1) "
                    "ON CONFLICT(name) DO UPDATE SET value = value + 1")
        cur.execute("SELECT value FROM _seq WHERE name='entry'")
        return int(cur.fetchone()[0])

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
        """Open a new tenant-scoped Blackboard.v1 workspace (status=open, entry_count=0). REQUIRES a tenant_scope
        (else :class:`BlackboardWriteRejected` ``missing_tenant_scope``). The id is content-addressed from
        (task, tenant_scope, now) so the same call is idempotent. Returns the Blackboard.v1-shaped row dict."""
        if not tenant_scope:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.MISSING_TENANT_SCOPE,
                "create_blackboard requires a non-empty tenant_scope (working state is tenant-isolated)",
            )
        blackboard_id = canonical_id("bb", task, tenant_scope, now)
        seq = self._next_seq()
        cur = self._conn.cursor()
        # idempotent create: the same (task, tenant_scope, now) re-uses the existing row (content-addressed id).
        cur.execute(
            "INSERT OR IGNORE INTO blackboards"
            "(blackboard_id, task, tenant_scope, created_at, status, iteration, seq) "
            "VALUES(?,?,?,?,?,?,?)",
            (blackboard_id, task, tenant_scope, now, STATUS_OPEN, 0, seq),
        )
        self._conn.commit()
        return self._blackboard_row(blackboard_id)

    def _blackboard_row(self, blackboard_id: str) -> dict:
        cur = self._conn.cursor()
        row = cur.execute(
            "SELECT blackboard_id, task, tenant_scope, created_at, status, iteration FROM blackboards "
            "WHERE blackboard_id=?",
            (blackboard_id,),
        ).fetchone()
        if row is None:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.UNKNOWN_BLACKBOARD, f"no blackboard {blackboard_id!r}"
            )
        count = cur.execute(
            "SELECT COUNT(*) FROM entries WHERE blackboard_id=?", (blackboard_id,)
        ).fetchone()[0]
        return {
            "blackboard_id": row["blackboard_id"],
            "task": row["task"],
            "tenant_scope": row["tenant_scope"],
            "created_at": row["created_at"],
            "status": row["status"],
            "entry_count": int(count),  # projection of the entry stream (Blackboard.v1)
            "iteration": int(row["iteration"]),
        }

    # ---- append (the governed write) -----------------------------------------------------
    def append_entry(self, blackboard_id: str, entry: dict, *, worker_receipt: dict, now: str) -> dict:
        """APPEND one typed BlackboardEntry under a MANDATORY ``worker_receipt``; return the stored row dict.

        All governance guards raise :class:`BlackboardWriteRejected` and store NOTHING. The stored row's
        ``serves_truth`` is pinned False (the input's ``serves_truth`` is read only to REJECT a truthy value).
        Idempotent on a content-identical re-write of the same ``entry_id``; an append-only violation on a
        content-DIFFERENT re-write. Deterministic when ``now`` is injected.
        """
        bb = self._blackboard_row(blackboard_id)  # raises unknown_blackboard if absent

        # --- guard: mandatory worker receipt ---------------------------------------------
        if not worker_receipt or not worker_receipt.get("worker_id"):
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.MISSING_RECEIPT,
                "append_entry requires a worker_receipt with a worker_id (provenance is mandatory)",
            )

        kind = entry.get("kind")
        if kind not in BLACKBOARD_ENTRY_KINDS:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.INVALID_KIND,
                f"kind {kind!r} not one of {BLACKBOARD_ENTRY_KINDS}",
            )

        # --- guard: serves_truth may NEVER be true ---------------------------------------
        if entry.get("serves_truth") is True:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.SERVES_TRUTH_FORBIDDEN,
                "a blackboard entry is working state, never served truth (serves_truth must be false)",
            )

        # --- guard: tenant scope present AND matches the blackboard ----------------------
        tenant_scope = entry.get("tenant_scope") or ""
        if not tenant_scope:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.MISSING_TENANT_SCOPE,
                "entry requires a non-empty tenant_scope (working state is tenant-isolated)",
            )
        if tenant_scope != bb["tenant_scope"]:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.MISSING_TENANT_SCOPE,
                f"entry tenant_scope {tenant_scope!r} != blackboard tenant_scope {bb['tenant_scope']!r} "
                "(never cross-tenant)",
            )

        # --- guard: an observation must be source-backed (non-empty source_refs) ----------
        source_refs = list(entry.get("source_refs") or [])
        if kind == KIND_OBSERVATION and len(source_refs) == 0:
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.SOURCELESS_OBSERVATION,
                "an observation requires non-empty source_refs (a sourceless claim can never be promoted)",
            )

        iteration = int(entry.get("iteration", bb["iteration"]) or 0)
        author_worker_id = entry.get("author_worker_id") or worker_receipt.get("worker_id")
        body = entry.get("body", {})

        # content-addressed entry_id: stable across retries of the SAME content, distinct for different content.
        entry_id = entry.get("entry_id") or canonical_id(
            "bbe", blackboard_id, kind, author_worker_id, str(iteration),
            json.dumps(body, sort_keys=True, separators=(",", ":")),
            json.dumps(source_refs, sort_keys=True, separators=(",", ":")),
        )

        # canonical hash of the STORED shape (kind + lineage + body + source_refs); the basis of idempotency.
        stored_core = {
            "blackboard_id": blackboard_id,
            "kind": kind,
            "author_worker_id": author_worker_id,
            "iteration": iteration,
            "source_refs": source_refs,
            "tenant_scope": tenant_scope,
            "body": body,
        }
        content_hash = _content_hash(stored_core)

        cur = self._conn.cursor()
        existing = cur.execute(
            "SELECT content_hash FROM entries WHERE entry_id=?", (entry_id,)
        ).fetchone()
        if existing is not None:
            # --- guard: append-only. Identical content => idempotent no-op; different content => REJECT. ---
            if existing["content_hash"] == content_hash:
                return self._entry_row(entry_id)  # idempotent: the same write twice is a no-op
            raise BlackboardWriteRejected(
                BlackboardWriteRejected.APPEND_ONLY_VIOLATION,
                f"entry {entry_id!r} already exists with different content (no update/delete — append-only)",
            )

        # record the mandatory worker receipt (idempotent on its own content-addressed id).
        receipt_id = self._record_receipt(blackboard_id, worker_receipt, entry_ids=[entry_id], now=now)

        seq = self._next_seq()
        cur.execute(
            "INSERT INTO entries"
            "(entry_id, blackboard_id, kind, author_worker_id, iteration, source_refs, serves_truth, "
            " tenant_scope, created_at, body, content_hash, receipt_id, seq) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                entry_id,
                blackboard_id,
                kind,
                author_worker_id,
                iteration,
                json.dumps(source_refs, separators=(",", ":")),
                0,  # serves_truth pinned False on every stored row — THE INVARIANT
                tenant_scope,
                now,
                json.dumps(body, separators=(",", ":")),
                content_hash,
                receipt_id,
                seq,
            ),
        )
        # keep the blackboard.iteration projection monotonic (never rewinds; entry_count is computed on read).
        if iteration > int(bb["iteration"]):
            cur.execute(
                "UPDATE blackboards SET iteration=? WHERE blackboard_id=?", (iteration, blackboard_id)
            )
        self._conn.commit()
        return self._entry_row(entry_id)

    def _record_receipt(self, blackboard_id: str, worker_receipt: dict, *, entry_ids: list[str], now: str) -> str:
        """Persist a BlackboardWorkerReceipt.v1-shaped row and return its content-addressed receipt_id.

        The receipt records WHAT the worker did (worker id/kind, entries written, input/output content hashes,
        start/complete timestamps). It NEVER asserts the entries are true. No raw secrets/keys: any
        ``llm_route_receipt_ref`` is kept verbatim only if it is an env:// / receipt-id handle (the schema's
        pattern); we do not synthesize one. Idempotent on its content-addressed id.
        """
        worker_id = worker_receipt["worker_id"]
        worker_kind = worker_receipt.get("worker_kind", "worker")
        input_hash = worker_receipt.get("input_hash") or _content_hash(
            {"blackboard_id": blackboard_id, "worker_id": worker_id, "entry_ids": entry_ids}
        )
        output_hash = worker_receipt.get("output_hash") or _content_hash({"entry_ids": entry_ids})
        receipt_id = worker_receipt.get("receipt_id") or canonical_id(
            "bbr", blackboard_id, worker_id, worker_kind, output_hash, now
        )
        body = {
            "receipt_id": receipt_id,
            "blackboard_id": blackboard_id,
            "worker_id": worker_id,
            "worker_kind": worker_kind,
            "entries_written": list(entry_ids),
            "input_hash": input_hash,
            "output_hash": output_hash,
            "started_at": worker_receipt.get("started_at", now),
            "completed_at": worker_receipt.get("completed_at", now),
        }
        # optional LLM-route ref — kept ONLY when it is a handle (never a raw key value).
        ref = worker_receipt.get("llm_route_receipt_ref")
        if isinstance(ref, str) and ref.startswith(("env://", "receipt:", "rcpt-", "mir-")):
            body["llm_route_receipt_ref"] = ref

        cur = self._conn.cursor()
        existing = cur.execute("SELECT receipt_id FROM receipts WHERE receipt_id=?", (receipt_id,)).fetchone()
        if existing is None:
            seq = self._next_seq()
            cur.execute(
                "INSERT INTO receipts(receipt_id, blackboard_id, body, seq) VALUES(?,?,?,?)",
                (receipt_id, blackboard_id, json.dumps(body, separators=(",", ":")), seq),
            )
        return receipt_id

    def _entry_row(self, entry_id: str) -> dict:
        cur = self._conn.cursor()
        row = cur.execute(
            "SELECT entry_id, blackboard_id, kind, author_worker_id, iteration, source_refs, serves_truth, "
            "tenant_scope, created_at, body, content_hash, receipt_id FROM entries WHERE entry_id=?",
            (entry_id,),
        ).fetchone()
        return self._row_to_entry(row)

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> dict:
        return {
            "entry_id": row["entry_id"],
            "blackboard_id": row["blackboard_id"],
            "kind": row["kind"],
            "author_worker_id": row["author_worker_id"],
            "iteration": int(row["iteration"]),
            "source_refs": json.loads(row["source_refs"]),
            "serves_truth": bool(row["serves_truth"]),  # always False (stored as 0)
            "tenant_scope": row["tenant_scope"],
            "created_at": row["created_at"],
            "body": json.loads(row["body"]),
            "content_hash": row["content_hash"],
            "receipt_id": row["receipt_id"],
        }

    # ---- query (deterministic read projection) -------------------------------------------
    def query(
        self,
        blackboard_id: str,
        *,
        kind: str | None = None,
        author_worker_id: str | None = None,
        iteration: int | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Return stored entries in a DETERMINISTIC total order: insertion sequence, then entry_id as a
        tie-breaker. Pure projection of the append-only stream — the same (db, filters) always yields the same
        rows in the same order. Nothing here is served truth (every row's ``serves_truth`` is False)."""
        clauses = ["blackboard_id = ?"]
        params: list[Any] = [blackboard_id]
        if kind is not None:
            clauses.append("kind = ?")
            params.append(kind)
        if author_worker_id is not None:
            clauses.append("author_worker_id = ?")
            params.append(author_worker_id)
        if iteration is not None:
            clauses.append("iteration = ?")
            params.append(int(iteration))
        sql = (
            "SELECT entry_id, blackboard_id, kind, author_worker_id, iteration, source_refs, serves_truth, "
            "tenant_scope, created_at, body, content_hash, receipt_id FROM entries WHERE "
            + " AND ".join(clauses)
            + " ORDER BY seq ASC, entry_id ASC"  # total, stable order (insertion then id)
        )
        if limit is not None and limit >= 0:
            sql += " LIMIT ?"
            params.append(int(limit))
        cur = self._conn.cursor()
        return [self._row_to_entry(r) for r in cur.execute(sql, params).fetchall()]

    def get_receipts(self, blackboard_id: str) -> list[dict]:
        """Return the BlackboardWorkerReceipt rows for ``blackboard_id`` in deterministic (insertion) order.
        A receipt records WHAT a worker did; it never asserts the written entries are true."""
        cur = self._conn.cursor()
        rows = cur.execute(
            "SELECT body FROM receipts WHERE blackboard_id=? ORDER BY seq ASC, receipt_id ASC",
            (blackboard_id,),
        ).fetchall()
        return [json.loads(r["body"]) for r in rows]

    def close(self) -> None:
        """Close the underlying connection (tests / short-lived stores)."""
        self._conn.close()


# ---- seed / demo helper -----------------------------------------------------------------
def seed_demo_blackboard(*, db_path: str | None = None, now: str = "2026-01-01T00:00:00Z",
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
    bb = LocalSqliteBlackboard(db_path=db_path)
    board = bb.create_blackboard(
        task="What is the sanction's effective date?", tenant_scope=tenant_scope, now=now
    )
    bid = board["blackboard_id"]

    def receipt(worker_id: str, worker_kind: str) -> dict:
        # a minimal worker receipt (hashes are filled in by the store from the entry lineage); no raw keys.
        return {"worker_id": worker_id, "worker_kind": worker_kind, "started_at": now, "completed_at": now}

    # 1) a signal (procedural; no sources)
    signal = bb.append_entry(
        bid,
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
    source = bb.append_entry(
        bid,
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
    source_handle_id = source["body"]["source_id"]

    # 2b) an observation that CITES the source (non-empty source_refs => passes the source-backed guard)
    observation = bb.append_entry(
        bid,
        {
            "kind": KIND_OBSERVATION,
            "author_worker_id": "worker.observer",
            "iteration": 1,
            "tenant_scope": tenant_scope,
            "source_refs": [source_handle_id],
            "body": {
                "statement": "The sanction took effect on 2026-04-15.",
                "source_refs": [source_handle_id],
                "confidence": 0.9,
            },
        },
        worker_receipt=receipt("worker.observer", "observer"),
        now=now,
    )

    # 3) a gap (a named hole — convergence currency)
    gap = bb.append_entry(
        bid,
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
        "blackboard_id": bid,
        "entries": [signal, source, observation, gap],
    }


__all__ = [
    "LocalSqliteBlackboard",
    "LOCAL_SQLITE_BLACKBOARD_PROVIDER_ID",
    "DEFAULT_DB_PATH",
    "HASH_PREFIX",
    "seed_demo_blackboard",
]
