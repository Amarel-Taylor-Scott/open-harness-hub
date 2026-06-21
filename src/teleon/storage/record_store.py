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

import json
import os
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_POLICY_PATH = _REPO / "architecture" / "storage_tier_policy.json"


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


class PostgresRecordStore(_UnwiredCloudStore):
    backend = "postgres"
    target = "PostgreSQL (+ pgvector) — operational, millions of indexed rows"


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
    return cls()  # cloud backend: raises with its swap contract
