"""src.teleon.storage.record_store — the ONE backend-swappable, append-only RECORD STORE for the
long-lived streams that grow to billions-to-trillions of rows (the descent BRAIN, CDC, versioning).

Every such stream is append-only and content-addressed, so the storage backend is a CONFIG choice
(architecture/storage_tier_policy.json), not a code rewrite. Callers write through this port; the
volume tier decides the backend:

    tier          local backend (offline, now)     cloud backend (the scale path, config-selected)
    -----------   ------------------------------   ----------------------------------------------
    config        json_file (git IS the store)      json_file  (never a DB — see the policy law)
    operational   sqlite_wal (_jsonl_store)         postgres   (millions, indexed, pgvector)
    history       sqlite_wal (_jsonl_store)         warehouse  (BigQuery/ClickHouse partitioned +
                                                              object-store Parquet cold — trillions)

Idempotency is content-addressed at EVERY tier (the record's stable hash key): a re-append is an O(1)
INDEXED no-op, never an O(n) rescan — the property that lets an append-only stream scale past billions.
LOSSLESS: the durable ``*.jsonl`` mirror is the single on-disk source; the db is a rebuildable index;
nothing (incl. failures/losers) is dropped. The record schema + idempotency key are backend-independent,
so the cloud swap is a config + loader change, never a caller change.

serves_truth=false (a record is evidence, never a truth claim); Teleon-layer — never imports src.baltor.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:                      # so scripts._config resolves regardless of CWD/runner
    sys.path.insert(0, str(_REPO))
_POLICY_PATH = _REPO / "architecture" / "storage_tier_policy.json"

# Single source for the operational Postgres DSN env-var names (No Magic Values, docs/codex/no-magic-values.md).
from scripts._config import LIBPQ_PG_ENV_PREFIX, OH_PG_DSN_ENV, POSTGRES_DSN_ENV_VARS  # noqa: E402


class StorageError(ValueError):
    """Raised on an unknown stream, a config-tier stream used as an append log, or a bad policy."""


# -- the single-source tier policy ----------------------------------------------------------------
def tier_policy() -> dict:
    """The whole storage tier policy (single source: architecture/storage_tier_policy.json)."""
    return json.loads(_POLICY_PATH.read_text(encoding="utf-8"))


def stream_spec(stream: str, *, policy: dict | None = None) -> dict:
    """The policy row for one stream. Raises on an unknown stream — never a silent default."""
    policy = policy if policy is not None else tier_policy()
    for s in policy.get("streams", []):
        if s.get("stream") == stream:
            return s
    raise StorageError(f"unknown stream {stream!r}; declared: {[s['stream'] for s in policy.get('streams', [])]}")


def backend_for(stream: str, *, mode: str | None = None, policy: dict | None = None) -> str:
    """The backend a stream resolves to for the given mode ('local' default, or 'cloud'). Reads the
    tier's backend from the policy — the swap is config, not code."""
    policy = policy if policy is not None else tier_policy()
    spec = stream_spec(stream, policy=policy)
    tier = policy["tiers"][spec["tier"]]
    mode = mode or os.environ.get("OH_STORAGE_MODE", "local")
    return tier["local_backend"] if mode == "local" else tier["cloud_backend"]


# -- the port + backends --------------------------------------------------------------------------
class RecordStore:
    """Append-only record store port. ``append`` is idempotent when given an ``idem_key``; ``all``
    streams the records (optionally filtered); ``count`` is the live count. serves_truth False."""

    backend = "abstract"

    def append(self, record: dict, *, idem_key: str | None = None) -> int:
        raise NotImplementedError

    def all(self, predicate=None) -> list[dict]:
        raise NotImplementedError

    def count(self) -> int:
        raise NotImplementedError

    def close(self) -> None:
        pass


class LocalRecordStore(RecordStore):
    """The local (offline) backend used for both the operational and history tiers on a single node:
    SQLite-WAL primary + durable JSONL mirror (via scripts._jsonl_store) + O(1) content-addressed
    idempotency. The cloud swap (postgres/warehouse) serves the SAME records through the same port."""

    backend = "sqlite_wal"

    def __init__(self, jsonl_path: str | Path, *, db_path: str | Path | None = None):
        from scripts._jsonl_store import open_log  # src -> scripts: the shared local-store substrate
        self.jsonl_path = Path(jsonl_path)
        self._log = open_log(self.jsonl_path, db_path=Path(db_path) if db_path else None)

    def append(self, record: dict, *, idem_key: str | None = None) -> int:
        return self._log.append(record, idem_key=idem_key)

    def all(self, predicate=None) -> list[dict]:
        return self._log.all(predicate)

    def count(self) -> int:
        return self._log.count()

    def close(self) -> None:
        self._log.close()


class _UnwiredCloudStore(RecordStore):
    """A cloud backend that is config-selected but not wired in the offline build. It names its target
    + the swap contract so the trillion-row path is explicit, never a silent fallback."""

    target = "?"

    def __init__(self, *_a, **_k):
        raise NotImplementedError(
            f"the {self.backend!r} backend ({self.target}) is the documented SCALE swap for this tier; "
            f"it is config-selected via OH_STORAGE_MODE=cloud and not wired in the offline build. The "
            f"record schema + idempotency key are backend-independent, so enabling it is a loader/config "
            f"change, never a caller change.")


# -- Postgres operational backend: shared connection plumbing (lazy driver, single source) --------
# A stream+shard becomes a TABLE NAME, which CANNOT be a bound parameter, so it is sanitized to a strict
# [a-z0-9_] identifier here; every DATA value is ALWAYS passed via a %s placeholder (never interpolated).
_PG_TABLE_PREFIX = "teleon_record_"
_PG_IDENT_SUB = re.compile(r"[^a-z0-9_]+")
_PG_CONNECT_TIMEOUT_S = 5            # fail fast instead of hanging when a DSN points at an unreachable host


def _pg_table_name(stream: str, shard: str) -> str:
    """A safe, deterministic Postgres identifier for a stream+shard (one table per stream)."""
    safe = _PG_IDENT_SUB.sub("_", f"{stream}_{shard}".lower()).strip("_")
    return f"{_PG_TABLE_PREFIX}{safe}"


def resolve_postgres_dsn() -> str | None:
    """The operational Postgres DSN from the environment, or None when UNCONFIGURED (single source:
    scripts._config.POSTGRES_DSN_ENV_VARS). An explicit DSN env wins; otherwise, if any libpq PG* var is
    set, return "" so the driver reads PGHOST/PGDATABASE/... itself. None means 'no Postgres configured'
    (the caller then refuses rather than silently writing to the local backend)."""
    for name in POSTGRES_DSN_ENV_VARS:
        val = os.environ.get(name)
        if val:
            return val
    if any(k.startswith(LIBPQ_PG_ENV_PREFIX) and k != "PGDATA" for k in os.environ):
        return ""                   # configured via the libpq PG* environment (empty DSN → driver fills it)
    return None                     # genuinely unconfigured


def psycopg_available() -> bool:
    """Network-free probe: is a Postgres driver (psycopg v3 OR psycopg2) importable? Decides, together
    with a DSN, whether the cloud backend can be engaged — never guesses, never fakes a DB."""
    return (importlib.util.find_spec("psycopg") is not None
            or importlib.util.find_spec("psycopg2") is not None)


def connect_postgres(dsn: str):  # pragma: no cover - needs a live DB; injected/faked in the proofs
    """Open a real Postgres connection. The driver is imported LAZILY (so this module loads with neither
    psycopg nor a DB present); psycopg v3 is preferred, psycopg2 is the fallback; a connect timeout makes
    an unreachable host fail fast rather than hang."""
    try:
        import psycopg
        return psycopg.connect(dsn, connect_timeout=_PG_CONNECT_TIMEOUT_S)
    except ModuleNotFoundError:           # only the driver being ABSENT falls back — a connect error propagates
        import psycopg2
        return psycopg2.connect(dsn, connect_timeout=_PG_CONNECT_TIMEOUT_S)


class PostgresRecordStore(RecordStore):
    """The OPERATIONAL cloud backend: PostgreSQL, the SAME append-only, content-addressed-idempotent port
    as LocalRecordStore, for millions of indexed rows. One table per stream MIRRORS the SQLite layout
    (``seq, generation, body_json, idem_key``) with a UNIQUE index on ``idem_key`` so a re-append is an
    O(1) INDEXED no-op (``ON CONFLICT DO NOTHING``) — never an O(n) rescan. NULL keys are distinct in
    Postgres, so an un-keyed append never collides (matching the SQLite NULL-key behavior).

    Engaged by ``open_record_store`` only in cloud mode; the driver is imported lazily and ``connect`` is
    an injectable seam so the proof exercises the real SQL path offline against a test double. The record
    schema + idempotency key are backend-independent, so the swap from sqlite_wal is config, not a caller
    change. serves_truth=false (a record is evidence, never a truth claim)."""

    backend = "postgres"
    target = "PostgreSQL (+ pgvector) — operational, millions of indexed rows"

    def __init__(self, stream: str, *, shard: str = "000", dsn: str | None = None, connect=None) -> None:
        from scripts._jsonl_store import GENERATION_START  # single source for the live-generation value
        self.stream = stream
        self.table = _pg_table_name(stream, shard)
        self._generation = GENERATION_START
        self.dsn = resolve_postgres_dsn() if dsn is None else dsn
        if connect is None:                            # production path: require a real, reachable backend
            if self.dsn is None:
                raise StorageError(
                    f"the {self.backend!r} backend ({self.target}) is selected (OH_STORAGE_MODE=cloud) but "
                    f"no DSN is configured — set {OH_PG_DSN_ENV} (or one of {POSTGRES_DSN_ENV_VARS}). It "
                    f"REFUSES rather than silently writing to the local backend.")
            if not psycopg_available():
                raise StorageError(
                    f"the {self.backend!r} backend is configured but no Postgres driver (psycopg / psycopg2) "
                    f"is importable; install one to engage the operational tier.")
        self._conn = (connect or connect_postgres)(self.dsn or "")
        self._init_schema()

    def _exec(self, sql: str, params=(), *, fetch: bool = False, fetchone: bool = False):
        """Run one statement on a context-managed cursor (always closed — no leaks)."""
        cur = self._conn.cursor()
        try:
            cur.execute(sql, params)
            if fetchone:
                return cur.fetchone()
            if fetch:
                return cur.fetchall()
            return None
        finally:
            cur.close()

    def _init_schema(self) -> None:
        # one table per stream; mirrors the SQLite ``records`` layout. The UNIQUE index on idem_key gives
        # O(1) content-addressed idempotency (and enables ON CONFLICT); the (generation, seq) index serves
        # the live-generation ordered scan. body_json is JSONB so the operational tier can index into it.
        self._exec(f"CREATE TABLE IF NOT EXISTS {self.table} ("
                   f"seq BIGSERIAL PRIMARY KEY, generation INTEGER NOT NULL, "
                   f"body_json JSONB NOT NULL, idem_key TEXT)")
        self._exec(f"CREATE UNIQUE INDEX IF NOT EXISTS {self.table}_idem_uq ON {self.table} (idem_key)")
        self._exec(f"CREATE INDEX IF NOT EXISTS {self.table}_gen_seq_ix ON {self.table} (generation, seq)")
        self._conn.commit()

    def append(self, record: dict, *, idem_key: str | None = None) -> int:
        """Append one record; idempotent when ``idem_key`` is given (an O(1) INDEXED no-op returning the
        EXISTING seq). Returns the row seq — the SAME shape as ``LocalRecordStore.append``."""
        if not isinstance(record, dict):
            raise StorageError("RecordStore records must be JSON objects (dict)")
        body = json.dumps(record, sort_keys=True)        # canonical bytes — matches the SQLite mirror
        if idem_key is not None:                          # fast path: indexed lookup, no write on a repeat
            existing = self._exec(f"SELECT seq FROM {self.table} WHERE idem_key = %s LIMIT 1",
                                  (idem_key,), fetchone=True)
            if existing is not None:
                return int(existing[0])
        row = self._exec(
            f"INSERT INTO {self.table} (generation, body_json, idem_key) VALUES (%s, %s::jsonb, %s) "
            f"ON CONFLICT (idem_key) DO NOTHING RETURNING seq",
            (self._generation, body, idem_key), fetchone=True)
        if row is None:                                   # lost a concurrent race on the same idem_key
            existing = self._exec(f"SELECT seq FROM {self.table} WHERE idem_key = %s LIMIT 1",
                                  (idem_key,), fetchone=True)
            self._conn.commit()
            return int(existing[0])
        self._conn.commit()
        return int(row[0])

    def all(self, predicate=None) -> list[dict]:
        rows = self._exec(f"SELECT body_json FROM {self.table} WHERE generation = %s ORDER BY seq",
                          (self._generation,), fetch=True) or []
        out = [r[0] if isinstance(r[0], dict) else json.loads(r[0]) for r in rows]
        return [r for r in out if predicate(r)] if predicate else out

    def count(self) -> int:
        row = self._exec(f"SELECT COUNT(*) FROM {self.table} WHERE generation = %s",
                         (self._generation,), fetchone=True) or (0,)
        return int(row[0])

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass


class WarehouseRecordStore(_UnwiredCloudStore):
    backend = "warehouse"
    target = "BigQuery/ClickHouse partitioned + object-store Parquet cold tier — history/CDC, trillions"


_BACKENDS = {
    "sqlite_wal": LocalRecordStore,
    "postgres": PostgresRecordStore,
    "warehouse": WarehouseRecordStore,
}


def open_record_store(stream: str, *, shard: str = "000", mode: str | None = None) -> RecordStore:
    """Open the append-only store for a declared stream, backend chosen by its tier + the mode.
    Raises for a config-tier stream (those are whole-file git-tracked JSON; read them directly)."""
    policy = tier_policy()
    spec = stream_spec(stream, policy=policy)
    if spec["tier"] == "config":
        raise StorageError(
            f"stream {stream!r} is CONFIG-tier (whole-file git-tracked JSON at {spec.get('json')}); "
            f"read it directly, not through the append-only RecordStore.")
    backend = backend_for(stream, mode=mode, policy=policy)
    cls = _BACKENDS[backend]
    if backend == "sqlite_wal":
        jsonl = _REPO / spec["jsonl"].replace("{shard}", shard)
        return cls(jsonl)
    if backend == "postgres":  # operational cloud tier — WIRED (refuses honestly when no DSN is configured)
        return cls(stream, shard=shard)
    return cls()  # warehouse (history tier): the documented, not-yet-wired SCALE swap; raises its contract
