#!/usr/bin/env python3
"""Resumable, bounded primitive embedding shards over SQLite sources.

``build_primitive_embeddings --limit N`` always rebuilds the first N cards.  This
loop instead advances durable SQLite rowid cursors and commits immutable shards.
It reads ``dist/primitives.db`` first and then the optional primitive-search
federation overlay database. Primitive IDs are deduplicated across both sources through a
rebuildable local catalog.

Each shard carries aligned blackbox, plain, technical, and semantic float32
matrices plus IDs, source-row mappings, and deterministic feature records.  The
shard manifest describes every persisted column with its schema, description,
units, model, dimension, and source digest.  Counts are sums of validated shard
rows only; no declared product target is used as inventory.

Default invocation is a read-only dry run.  Execution is offline and bounded:

    PYTHONPATH=. python3 scripts/primitive_embedding_shard_loop.py
    PYTHONPATH=. python3 scripts/primitive_embedding_shard_loop.py --once --batch-size 4096
    PYTHONPATH=. python3 scripts/primitive_embedding_shard_loop.py --watch --max-ticks 3
    PYTHONPATH=. python3 scripts/primitive_embedding_shard_loop.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next(
    (parent for parent in _here_boot.parents if (parent / "scripts" / "_repo_paths.py").exists()),
    _here_boot.parents[1],
)
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import copy  # noqa: E402
import fcntl  # noqa: E402
import hashlib  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import sqlite3  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
import uuid  # noqa: E402
from contextlib import closing  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence  # noqa: E402

import numpy as np  # noqa: E402

from scripts import capability_embedding as _embedding  # noqa: E402
from scripts.build_primitive_embeddings import _features as _feature_record  # noqa: E402,SLF001


BOUNDARY: dict[str, bool] = {"candidate": True, "serves_truth": False}
SCHEMA_VERSION = 1
STATE_SCHEMA = "primitive_embedding_shard_loop_state"
INDEX_RECORD_TYPE = "primitive_embedding_shard_index"
SHARD_RECORD_TYPE = "primitive_embedding_shard"
TICK_RECORD_TYPE = "primitive_embedding_shard_tick"

DEFAULT_CORE_DB = resource("dist") / "primitives.db"
DEFAULT_OVERLAY_DB = resource("dist") / "primitive_search_federation_overlay.db"
DEFAULT_STATE_DIR = resource("dist") / "primitive-embedding-shards"
DEFAULT_BATCH_SIZE = 4_096
DEFAULT_INTERVAL_SECONDS = 3_600
DEFAULT_MAX_TICKS = 1
DEFAULT_EMBED_PATH = "tokens"
MAX_SQL_VARIABLE_IDS = 800

MANIFEST_FILENAME = "manifest.json"
STATE_FILENAME = "state.json"
LEDGER_FILENAME = "ledger.jsonl"
CATALOG_FILENAME = "embedded_ids.sqlite"
LOCK_FILENAME = ".writer.lock"
SHARDS_DIRNAME = "shards"

SOURCE_COLUMNS: tuple[str, ...] = (
    "primitive_id",
    "pool",
    "title",
    "blackbox",
    "tags",
    "input_edge",
    "output_edge",
)
REGISTER_COLUMNS: tuple[str, ...] = tuple(_embedding.REGISTERS)
VECTOR_COLUMNS: tuple[str, ...] = ("blackbox", *REGISTER_COLUMNS)
OUTPUT_FILES: dict[str, str] = {
    "primitive_id": "ids.json",
    "source_row": "source_rows.jsonl",
    "features": "features.jsonl",
    "blackbox": "embeddings_blackbox.npy",
    "plain": "embeddings_plain.npy",
    "technical": "embeddings_technical.npy",
    "semantic": "embeddings_semantic.npy",
}


FaultInjector = Callable[[Path], None]


@dataclass(frozen=True)
class SourceSpec:
    name: str
    path: Path
    optional: bool = False
    table: str = "primitives"


@dataclass(frozen=True)
class SourceRow:
    source: str
    rowid: int
    primitive_id: str
    pool: str
    title: str
    blackbox: str
    tags: str
    input_edge: str
    output_edge: str

    def card(self) -> dict[str, Any]:
        return {
            "primitive_id": self.primitive_id,
            "pool": self.pool,
            "title": self.title,
            "blackbox": self.blackbox,
            "tags": self.tags,
            "input_edge": self.input_edge,
            "output_edge": self.output_edge,
            **BOUNDARY,
        }

    def source_record(self) -> dict[str, Any]:
        return {"source": self.source, "rowid": self.rowid, "primitive_id": self.primitive_id}

    def digest_record(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "rowid": self.rowid,
            **{column: getattr(self, column) for column in SOURCE_COLUMNS},
        }


@dataclass(frozen=True)
class EmbedderPort:
    model: str
    description: str
    dimension: int
    encode_many: Callable[[Sequence[str]], np.ndarray]


@dataclass(frozen=True)
class LoopConfig:
    state_dir: Path
    core_db: Path
    overlay_db: Optional[Path]
    batch_size: int


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _append_ledger(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative_or_absolute(path: Path, base: Path = _sbc_boot) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(base.resolve()))
    except ValueError:
        return str(resolved)


def _read_only_connection(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _source_schema(source: SourceSpec) -> dict[str, Any]:
    if source.table not in {"primitives", "overlay_primitives"}:
        raise ValueError(f"unsupported primitive source table {source.table!r}")
    with closing(_read_only_connection(source.path)) as connection:
        rows = connection.execute(f"PRAGMA table_info({source.table})").fetchall()
        if not rows:
            raise ValueError(f"{source.name} source has no {source.table} table: {source.path}")
        columns = [
            {
                "cid": int(row["cid"]),
                "name": str(row["name"]),
                "type": str(row["type"] or ""),
                "not_null": bool(row["notnull"]),
                "default": row["dflt_value"],
                "primary_key_position": int(row["pk"]),
            }
            for row in rows
        ]
        names = {column["name"] for column in columns}
        missing = sorted(set(SOURCE_COLUMNS) - names)
        if missing:
            raise ValueError(f"{source.name} source misses required columns {missing}: {source.path}")
        primitive_id_pk = any(
            column["name"] == "primitive_id" and column["primary_key_position"] > 0 for column in columns
        )
        unique_id = primitive_id_pk
        if not unique_id:
            for index in connection.execute("PRAGMA index_list(primitives)").fetchall():
                if not bool(index["unique"]):
                    continue
                index_columns = [
                    str(item["name"])
                    for item in connection.execute(f"PRAGMA index_info('{index['name']}')").fetchall()
                ]
                if index_columns == ["primitive_id"]:
                    unique_id = True
                    break
        if not unique_id:
            raise ValueError(f"{source.name}.primitives must uniquely constrain primitive_id")
        fts_name = "overlay_primitives_fts" if source.table == "overlay_primitives" else "primitives_fts"
        fts_present = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (fts_name,)
        ).fetchone() is not None
    schema = {
        "table": source.table,
        "columns": columns,
        "selected_columns": list(SOURCE_COLUMNS),
        "primitive_id_unique": unique_id,
        "fts_table_present": fts_present,
    }
    return {**schema, "schema_digest": _digest(schema)}


def _make_embedder(path: str) -> EmbedderPort:
    if path == "tokens":
        dimension = len(_embedding.embed_tokens("dimension probe"))

        def encode_many(texts: Sequence[str]) -> np.ndarray:
            return np.asarray([_embedding.embed_tokens(text) for text in texts], dtype="float32")

        return EmbedderPort(
            model="capability_embedding:tokens-crc32-tf",
            description="Deterministic hashed token-term-frequency embedding from capability_embedding.embed_tokens",
            dimension=dimension,
            encode_many=encode_many,
        )
    if path == "model2vec":
        model = _embedding._load_model2vec()  # noqa: SLF001 - canonical single loader
        if model is None:
            raise RuntimeError("model2vec requested but the configured local model is unavailable")
        probe = np.asarray(model.encode(["dimension probe"]), dtype="float32")
        if probe.ndim != 2 or probe.shape[0] != 1:
            raise ValueError(f"model2vec returned invalid probe shape {probe.shape}")

        def encode_many(texts: Sequence[str]) -> np.ndarray:
            return np.asarray(model.encode(list(texts)), dtype="float32")

        return EmbedderPort(
            model=f"model2vec:{_embedding._MODEL2VEC_NAME}",  # noqa: SLF001 - exact configured model name
            description="Local static model loaded by capability_embedding._load_model2vec",
            dimension=int(probe.shape[1]),
            encode_many=encode_many,
        )
    raise ValueError(f"unsupported embed path {path!r}; use tokens or model2vec")


def _normalized_matrix(embedder: EmbedderPort, texts: Sequence[str], column: str) -> np.ndarray:
    matrix = np.asarray(embedder.encode_many(texts), dtype="float32")
    expected = (len(texts), embedder.dimension)
    if matrix.ndim != 2 or tuple(matrix.shape) != expected:
        raise ValueError(f"{column} dimension mismatch: got {matrix.shape}, expected {expected}")
    if not np.isfinite(matrix).all():
        raise ValueError(f"{column} contains non-finite embedding values")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return np.asarray(matrix / norms, dtype="float32")


def _catalog_shard_digest(manifest: Mapping[str, Any]) -> str:
    return _digest(
        [
            {"shard_id": shard["shard_id"], "ids_digest": shard["ids_digest"]}
            for shard in manifest.get("shards", [])
        ]
    )


def _empty_manifest(config: LoopConfig) -> dict[str, Any]:
    return {
        "record_type": INDEX_RECORD_TYPE,
        "schema_version": SCHEMA_VERSION,
        "coverage_rows": 0,
        "source_cursors": {"core": 0, "overlay": 0},
        "sources": {
            "core": _relative_or_absolute(config.core_db),
            "overlay": _relative_or_absolute(config.overlay_db) if config.overlay_db else None,
        },
        "geometry": None,
        "shards": [],
        **BOUNDARY,
    }


def _validate_index_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("record_type") != INDEX_RECORD_TYPE:
        raise ValueError(f"unexpected index manifest type {manifest.get('record_type')!r}")
    shards = manifest.get("shards")
    if not isinstance(shards, list):
        raise ValueError("index manifest shards must be a list")
    shard_ids = [shard.get("shard_id") for shard in shards]
    if len(shard_ids) != len(set(shard_ids)):
        raise ValueError("index manifest contains duplicate shard IDs")
    measured = sum(int(shard.get("rows", 0)) for shard in shards)
    if measured != manifest.get("coverage_rows"):
        raise ValueError(
            f"index coverage mismatch: manifest={manifest.get('coverage_rows')} shard_rows={measured}"
        )
    if manifest.get("candidate") is not True or manifest.get("serves_truth") is not False:
        raise ValueError("index manifest lost the candidate boundary")


def _load_manifest(config: LoopConfig) -> dict[str, Any]:
    path = config.state_dir / MANIFEST_FILENAME
    manifest = _read_json(path) if path.exists() else _empty_manifest(config)
    _validate_index_manifest(manifest)
    expected_sources = _empty_manifest(config)["sources"]
    if manifest.get("sources") != expected_sources:
        raise ValueError(
            f"source configuration changed: {manifest.get('sources')!r} != {expected_sources!r}; "
            "use a new --state-dir"
        )
    return manifest


def _state_from_manifest(config: LoopConfig, manifest: Mapping[str, Any]) -> dict[str, Any]:
    state_path = config.state_dir / STATE_FILENAME
    prior: dict[str, Any] = _read_json(state_path) if state_path.exists() else {}
    if prior and prior.get("schema") != STATE_SCHEMA:
        raise ValueError(f"unexpected state schema {prior.get('schema')!r}")
    created_at = prior.get("created_at") or _utc_now()
    return {
        "schema": STATE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "tick": int(prior.get("tick", 0)),
        "source_cursors": copy.deepcopy(manifest["source_cursors"]),
        "coverage_rows": int(manifest["coverage_rows"]),
        "next_shard_sequence": len(manifest["shards"]) + 1,
        "geometry": copy.deepcopy(manifest.get("geometry")),
        "created_at": created_at,
        "updated_at": prior.get("updated_at") or created_at,
        **BOUNDARY,
    }


def _open_catalog(config: LoopConfig, manifest: Mapping[str, Any]) -> sqlite3.Connection:
    path = config.state_dir / CATALOG_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS embedded_ids("
        "primitive_id TEXT PRIMARY KEY, shard_id TEXT NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS catalog_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    expected = _catalog_shard_digest(manifest)
    row = connection.execute(
        "SELECT value FROM catalog_meta WHERE key='shard_set_digest'"
    ).fetchone()
    if row is None or row[0] != expected:
        connection.execute("DELETE FROM embedded_ids")
        for shard in manifest.get("shards", []):
            shard_dir = config.state_dir / str(shard["directory"])
            ids = _read_json(shard_dir / OUTPUT_FILES["primitive_id"])
            connection.executemany(
                "INSERT INTO embedded_ids(primitive_id, shard_id) VALUES(?, ?)",
                [(str(primitive_id), str(shard["shard_id"])) for primitive_id in ids],
            )
        connection.execute(
            "INSERT OR REPLACE INTO catalog_meta(key, value) VALUES('shard_set_digest', ?)",
            (expected,),
        )
        connection.commit()
    return connection


def _catalog_seen(connection: Optional[sqlite3.Connection], ids: Sequence[str]) -> set[str]:
    if connection is None or not ids:
        return set()
    seen: set[str] = set()
    for start in range(0, len(ids), MAX_SQL_VARIABLE_IDS):
        chunk = ids[start : start + MAX_SQL_VARIABLE_IDS]
        placeholders = ",".join("?" for _ in chunk)
        rows = connection.execute(
            f"SELECT primitive_id FROM embedded_ids WHERE primitive_id IN ({placeholders})", tuple(chunk)
        ).fetchall()
        seen.update(str(row[0]) for row in rows)
    return seen


def _fetch_source_rows(source: SourceSpec, after_rowid: int, limit: int) -> list[SourceRow]:
    columns = ", ".join(SOURCE_COLUMNS)
    if source.table not in {"primitives", "overlay_primitives"}:
        raise ValueError(f"unsupported primitive source table {source.table!r}")
    sql = (f"SELECT rowid AS source_rowid, {columns} FROM {source.table} "
           "WHERE rowid > ? ORDER BY rowid LIMIT ?")
    with closing(_read_only_connection(source.path)) as connection:
        raw_rows = connection.execute(sql, (after_rowid, limit)).fetchall()
    return [
        SourceRow(
            source=source.name,
            rowid=int(row["source_rowid"]),
            primitive_id=str(row["primitive_id"]),
            pool=str(row["pool"] or ""),
            title=str(row["title"] or ""),
            blackbox=str(row["blackbox"] or ""),
            tags=str(row["tags"] or ""),
            input_edge=str(row["input_edge"] or ""),
            output_edge=str(row["output_edge"] or ""),
        )
        for row in raw_rows
    ]


def _unseen_batch(
    source: SourceSpec,
    cursor: int,
    batch_size: int,
    catalog: Optional[sqlite3.Connection],
) -> tuple[list[SourceRow], int, bool, int]:
    selected: list[SourceRow] = []
    selected_ids: set[str] = set()
    scan_cursor = cursor
    scanned = 0
    exhausted = False
    while len(selected) < batch_size:
        rows = _fetch_source_rows(source, scan_cursor, batch_size)
        if not rows:
            exhausted = True
            break
        scanned += len(rows)
        scan_cursor = rows[-1].rowid
        seen = _catalog_seen(catalog, [row.primitive_id for row in rows])
        for row in rows:
            if row.primitive_id in seen or row.primitive_id in selected_ids:
                continue
            selected.append(row)
            selected_ids.add(row.primitive_id)
            if len(selected) == batch_size:
                break
        if len(rows) < batch_size:
            exhausted = True
            break
    return selected, scan_cursor, exhausted, scanned


def _select_batch(
    config: LoopConfig,
    cursors: Mapping[str, int],
    catalog: Optional[sqlite3.Connection],
) -> tuple[Optional[SourceSpec], list[SourceRow], dict[str, int], dict[str, Any]]:
    next_cursors = {"core": int(cursors.get("core", 0)), "overlay": int(cursors.get("overlay", 0))}
    scan_receipt: dict[str, Any] = {}
    core = SourceSpec("core", config.core_db)
    _source_schema(core)
    rows, cursor, exhausted, scanned = _unseen_batch(
        core, next_cursors["core"], config.batch_size, catalog
    )
    next_cursors["core"] = cursor
    scan_receipt["core"] = {"scanned": scanned, "cursor": cursor, "exhausted": exhausted}
    if rows:
        return core, rows, next_cursors, scan_receipt

    overlay_path = config.overlay_db
    if overlay_path and overlay_path.exists():
        overlay = SourceSpec("overlay", overlay_path, optional=True, table="overlay_primitives")
        _source_schema(overlay)
        rows, cursor, exhausted, scanned = _unseen_batch(
            overlay, next_cursors["overlay"], config.batch_size, catalog
        )
        next_cursors["overlay"] = cursor
        scan_receipt["overlay"] = {"scanned": scanned, "cursor": cursor, "exhausted": exhausted}
        if rows:
            return overlay, rows, next_cursors, scan_receipt
    else:
        scan_receipt["overlay"] = {
            "present": False,
            "path": _relative_or_absolute(overlay_path) if overlay_path else None,
        }
    return None, [], next_cursors, scan_receipt


def _surface_digest(ids: Sequence[str], values: Sequence[Any]) -> str:
    return _digest([{"primitive_id": primitive_id, "value": value} for primitive_id, value in zip(ids, values)])


def _implementation_digest(function: Callable[..., Any]) -> str:
    return hashlib.sha256(inspect.getsource(function).encode("utf-8")).hexdigest()


def _build_payload(
    source: SourceSpec,
    rows: Sequence[SourceRow],
    embedder: EmbedderPort,
) -> dict[str, Any]:
    cards = [row.card() for row in rows]
    ids = [row.primitive_id for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("selected batch contains duplicate primitive IDs")
    surfaces: dict[str, list[str]] = {
        "blackbox": [_embedding.card_embed_text(card) for card in cards]
    }
    for register in REGISTER_COLUMNS:
        surfaces[register] = [_embedding.register_text(card, register) for card in cards]
    matrices = {
        column: _normalized_matrix(embedder, surfaces[column], column) for column in VECTOR_COLUMNS
    }
    features = [_feature_record(card) for card in cards]
    source_records = [row.source_record() for row in rows]
    source_schema = _source_schema(source)
    source_digest = _digest(
        {
            "schema_digest": source_schema["schema_digest"],
            "rows": [row.digest_record() for row in rows],
        }
    )
    column_digests = {
        column: _surface_digest(ids, surfaces[column]) for column in VECTOR_COLUMNS
    }
    column_digests.update(
        {
            "primitive_id": _digest(ids),
            "source_row": _digest(source_records),
            "features": _surface_digest(ids, features),
        }
    )
    return {
        "ids": ids,
        "source_records": source_records,
        "features": features,
        "matrices": matrices,
        "surfaces": surfaces,
        "source_schema": source_schema,
        "source_digest": source_digest,
        "column_digests": column_digests,
    }


def _column_schema(payload: Mapping[str, Any], embedder: EmbedderPort, rows: int) -> list[dict[str, Any]]:
    columns = [
        {
            "name": "primitive_id",
            "file": OUTPUT_FILES["primitive_id"],
            "schema": "JSON array of UTF-8 strings",
            "description": "Stable primitive identifier aligned by position with every matrix and feature row",
            "units": "identifier",
            "model": "none",
            "dimension": 1,
            "shape": [rows],
            "source_digest": payload["column_digests"]["primitive_id"],
        },
        {
            "name": "source_row",
            "file": OUTPUT_FILES["source_row"],
            "schema": "JSONL object {source,rowid,primitive_id}",
            "description": "Exact SQLite source-row mapping for each aligned output row",
            "units": "SQLite row reference",
            "model": "none",
            "dimension": 3,
            "shape": [rows],
            "source_digest": payload["column_digests"]["source_row"],
        },
    ]
    descriptions = {
        "blackbox": "Intent embedding of capability_embedding.card_embed_text",
        "plain": "Embedding of capability_embedding.register_text(card, 'plain')",
        "technical": "Embedding of capability_embedding.register_text(card, 'technical')",
        "semantic": "Embedding of capability_embedding.register_text(card, 'semantic')",
    }
    for column in VECTOR_COLUMNS:
        columns.append(
            {
                "name": f"{column}_embedding",
                "file": OUTPUT_FILES[column],
                "schema": "NumPy .npy float32 matrix",
                "description": descriptions[column],
                "units": "L2-normalized embedding coordinates",
                "model": embedder.model,
                "model_description": embedder.description,
                "dimension": embedder.dimension,
                "shape": [rows, embedder.dimension],
                "source_digest": payload["column_digests"][column],
            }
        )
    feature_dimension = len(payload["features"][0]) if payload["features"] else 0
    columns.append(
        {
            "name": "features",
            "file": OUTPUT_FILES["features"],
            "schema": "JSONL deterministic feature object",
            "description": "Operations, datatypes, impact, frame, typed edges, and blocking-key count",
            "units": "feature fields",
            "model": "scripts.build_primitive_embeddings._features",
            "model_digest": _implementation_digest(_feature_record),
            "dimension": feature_dimension,
            "shape": [rows],
            "source_digest": payload["column_digests"]["features"],
        }
    )
    return columns


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _file_metadata(directory: Path, filenames: Iterable[str]) -> dict[str, Any]:
    return {
        filename: {"sha256": _file_digest(directory / filename), "bytes": (directory / filename).stat().st_size}
        for filename in filenames
    }


def _validate_shard(directory: Path) -> dict[str, Any]:
    manifest = _read_json(directory / MANIFEST_FILENAME)
    if manifest.get("record_type") != SHARD_RECORD_TYPE:
        raise ValueError(f"unexpected shard record type in {directory}")
    if manifest.get("candidate") is not True or manifest.get("serves_truth") is not False:
        raise ValueError(f"shard boundary invalid in {directory}")
    rows = int(manifest["rows"])
    dimension = int(manifest["dimension"])
    for filename, metadata in manifest["files"].items():
        path = directory / filename
        if not path.is_file():
            raise ValueError(f"missing shard file {path}")
        if path.stat().st_size != metadata["bytes"] or _file_digest(path) != metadata["sha256"]:
            raise ValueError(f"shard file digest mismatch: {path}")
    ids = _read_json(directory / OUTPUT_FILES["primitive_id"])
    source_rows = [
        json.loads(line)
        for line in (directory / OUTPUT_FILES["source_row"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    features = [
        json.loads(line)
        for line in (directory / OUTPUT_FILES["features"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(ids) != rows or len(set(ids)) != rows or len(source_rows) != rows or len(features) != rows:
        raise ValueError(
            f"shard row alignment failure in {directory}: ids={len(ids)} source={len(source_rows)} "
            f"features={len(features)} manifest={rows}"
        )
    if [row["primitive_id"] for row in source_rows] != ids:
        raise ValueError(f"source rows are not ID-aligned in {directory}")
    for column in VECTOR_COLUMNS:
        matrix = np.load(directory / OUTPUT_FILES[column], mmap_mode="r")
        if matrix.dtype != np.dtype("float32") or tuple(matrix.shape) != (rows, dimension):
            raise ValueError(
                f"{column} matrix mismatch in {directory}: dtype={matrix.dtype} shape={matrix.shape}"
            )
    schema_names = [column["name"] for column in manifest["column_schema"]]
    expected_names = [
        "primitive_id",
        "source_row",
        *(f"{column}_embedding" for column in VECTOR_COLUMNS),
        "features",
    ]
    if schema_names != expected_names:
        raise ValueError(f"column schema mismatch in {directory}: {schema_names}")
    return manifest


def _write_shard(
    config: LoopConfig,
    manifest: Mapping[str, Any],
    source: SourceSpec,
    rows: Sequence[SourceRow],
    scan_end_rowid: int,
    embedder: EmbedderPort,
    *,
    fault_injector: Optional[FaultInjector] = None,
) -> tuple[dict[str, Any], Path]:
    payload = _build_payload(source, rows, embedder)
    sequence = len(manifest["shards"]) + 1
    first_rowid, last_rowid = rows[0].rowid, rows[-1].rowid
    shard_id = (
        f"shard-{sequence:08d}-{source.name}-{first_rowid:012d}-{last_rowid:012d}-"
        f"{payload['source_digest'][:12]}"
    )
    shards_dir = config.state_dir / SHARDS_DIRNAME
    shards_dir.mkdir(parents=True, exist_ok=True)
    partial = shards_dir / f".partial-{uuid.uuid4().hex}"
    final = shards_dir / shard_id
    partial.mkdir()
    try:
        (partial / OUTPUT_FILES["primitive_id"]).write_text(
            json.dumps(payload["ids"], ensure_ascii=False), encoding="utf-8"
        )
        _write_jsonl(partial / OUTPUT_FILES["source_row"], payload["source_records"])
        _write_jsonl(partial / OUTPUT_FILES["features"], payload["features"])
        for column in VECTOR_COLUMNS:
            np.save(partial / OUTPUT_FILES[column], payload["matrices"][column], allow_pickle=False)
        data_files = list(OUTPUT_FILES.values())
        files = _file_metadata(partial, data_files)
        shard_manifest = {
            "record_type": SHARD_RECORD_TYPE,
            "schema_version": SCHEMA_VERSION,
            "shard_id": shard_id,
            "sequence": sequence,
            "source": source.name,
            "source_path": _relative_or_absolute(source.path),
            "source_schema": payload["source_schema"],
            "source_digest": payload["source_digest"],
            "first_rowid": first_rowid,
            "last_rowid": last_rowid,
            "source_scan_end_rowid": scan_end_rowid,
            "rows": len(rows),
            "ids_digest": payload["column_digests"]["primitive_id"],
            "embed_model": embedder.model,
            "dimension": embedder.dimension,
            "column_schema": _column_schema(payload, embedder, len(rows)),
            "files": files,
            **BOUNDARY,
        }
        _atomic_json(partial / MANIFEST_FILENAME, shard_manifest)
        if fault_injector:
            fault_injector(partial)
        validated = _validate_shard(partial)
        if final.exists():
            existing = _validate_shard(final)
            if _digest(existing) != _digest(validated):
                raise FileExistsError(f"immutable shard collision at {final}")
            shutil.rmtree(partial)
        else:
            os.replace(partial, final)
        return validated, final
    except Exception:
        shutil.rmtree(partial, ignore_errors=True)
        raise


def _assert_geometry(manifest: Mapping[str, Any], embedder: EmbedderPort) -> None:
    geometry = manifest.get("geometry")
    if geometry is None:
        return
    if geometry.get("model") != embedder.model:
        raise ValueError(
            f"embedding model mismatch: index={geometry.get('model')!r}, requested={embedder.model!r}"
        )
    if int(geometry.get("dimension", -1)) != embedder.dimension:
        raise ValueError(
            f"embedding dimension mismatch: index={geometry.get('dimension')}, requested={embedder.dimension}"
        )


def _register_catalog_ids(
    connection: sqlite3.Connection,
    ids: Sequence[str],
    shard_id: str,
    manifest: Mapping[str, Any],
) -> None:
    connection.executemany(
        "INSERT INTO embedded_ids(primitive_id, shard_id) VALUES(?, ?)",
        [(primitive_id, shard_id) for primitive_id in ids],
    )
    connection.execute(
        "INSERT OR REPLACE INTO catalog_meta(key, value) VALUES('shard_set_digest', ?)",
        (_catalog_shard_digest(manifest),),
    )
    connection.commit()


def _commit_index(
    config: LoopConfig,
    manifest: Mapping[str, Any],
    cursors: Mapping[str, int],
    embedder: EmbedderPort,
    shard_manifest: Optional[Mapping[str, Any]],
    shard_directory: Optional[Path],
) -> dict[str, Any]:
    updated = copy.deepcopy(dict(manifest))
    updated["source_cursors"] = {"core": int(cursors["core"]), "overlay": int(cursors["overlay"])}
    if shard_manifest is not None and shard_directory is not None:
        entry = {
            "shard_id": shard_manifest["shard_id"],
            "directory": str(shard_directory.relative_to(config.state_dir)),
            "source": shard_manifest["source"],
            "first_rowid": shard_manifest["first_rowid"],
            "last_rowid": shard_manifest["last_rowid"],
            "source_scan_end_rowid": shard_manifest["source_scan_end_rowid"],
            "rows": shard_manifest["rows"],
            "ids_digest": shard_manifest["ids_digest"],
            "source_digest": shard_manifest["source_digest"],
            "manifest_sha256": _file_digest(shard_directory / MANIFEST_FILENAME),
        }
        updated["shards"].append(entry)
        updated["geometry"] = {"model": embedder.model, "dimension": embedder.dimension}
    updated["coverage_rows"] = sum(int(shard["rows"]) for shard in updated["shards"])
    updated["updated_at"] = _utc_now()
    _validate_index_manifest(updated)
    _atomic_json(config.state_dir / MANIFEST_FILENAME, updated)
    return updated


def _execute_tick(
    config: LoopConfig,
    embedder: EmbedderPort,
    *,
    fault_injector: Optional[FaultInjector] = None,
) -> dict[str, Any]:
    config.state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = config.state_dir / LOCK_FILENAME
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        manifest = _load_manifest(config)
        state = _state_from_manifest(config, manifest)
        _assert_geometry(manifest, embedder)
        catalog = _open_catalog(config, manifest)
        try:
            source, rows, cursors, scan_receipt = _select_batch(
                config, state["source_cursors"], catalog
            )
            shard_manifest: Optional[dict[str, Any]] = None
            shard_directory: Optional[Path] = None
            if source is not None and rows:
                shard_manifest, shard_directory = _write_shard(
                    config,
                    manifest,
                    source,
                    rows,
                    cursors[source.name],
                    embedder,
                    fault_injector=fault_injector,
                )
            updated_manifest = _commit_index(
                config,
                manifest,
                cursors,
                embedder,
                shard_manifest,
                shard_directory,
            )
            if shard_manifest is not None:
                _register_catalog_ids(
                    catalog,
                    [row.primitive_id for row in rows],
                    str(shard_manifest["shard_id"]),
                    updated_manifest,
                )
            tick = int(state["tick"]) + 1
            updated_state = {
                **state,
                "tick": tick,
                "source_cursors": copy.deepcopy(updated_manifest["source_cursors"]),
                "coverage_rows": int(updated_manifest["coverage_rows"]),
                "next_shard_sequence": len(updated_manifest["shards"]) + 1,
                "geometry": copy.deepcopy(updated_manifest.get("geometry")),
                "updated_at": _utc_now(),
                **BOUNDARY,
            }
            _atomic_json(config.state_dir / STATE_FILENAME, updated_state)
            receipt = {
                "record_type": TICK_RECORD_TYPE,
                "schema_version": SCHEMA_VERSION,
                "tick": tick,
                "generated_at": _utc_now(),
                "batch_size_bound": config.batch_size,
                "source": source.name if source else None,
                "rows_embedded": len(rows),
                "source_scan": scan_receipt,
                "source_cursors": copy.deepcopy(updated_manifest["source_cursors"]),
                "shard_id": shard_manifest["shard_id"] if shard_manifest else None,
                "coverage_rows": updated_manifest["coverage_rows"],
                "coverage_basis": "sum of rows in validated immutable shard manifests",
                "embed_model": embedder.model,
                "dimension": embedder.dimension,
                "sources_exhausted_for_now": source is None,
                **BOUNDARY,
            }
            _append_ledger(config.state_dir / LEDGER_FILENAME, receipt)
            return receipt
        finally:
            catalog.close()
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _dry_run(config: LoopConfig) -> dict[str, Any]:
    manifest = _load_manifest(config)
    state = _state_from_manifest(config, manifest)
    source, rows, cursors, scan_receipt = _select_batch(
        config, state["source_cursors"], None
    )
    return {
        "record_type": "primitive_embedding_shard_dry_run",
        "schema_version": SCHEMA_VERSION,
        "mode": "dry_run",
        "batch_size_bound": config.batch_size,
        "current_coverage_rows": manifest["coverage_rows"],
        "coverage_basis": "sum of rows in validated immutable shard manifests",
        "current_source_cursors": state["source_cursors"],
        "next_source": source.name if source else None,
        "next_source_rowid": rows[0].rowid if rows else None,
        "projected_cursors_if_executed": cursors,
        "source_scan_probe": scan_receipt,
        "overlay_present": bool(config.overlay_db and config.overlay_db.exists()),
        "writes_performed": False,
        **BOUNDARY,
    }


def _run_ticks(
    config: LoopConfig,
    embedder: EmbedderPort,
    ticks: int,
    interval_seconds: int,
    *,
    sleep: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for index in range(ticks):
        receipts.append(_execute_tick(config, embedder))
        if index + 1 < ticks:
            sleep(float(interval_seconds))
    return receipts


def _fixture_db(path: Path, rows: Sequence[tuple[str, str, str, str, str, str, str]],
                table: str = "primitives") -> None:
    if table not in {"primitives", "overlay_primitives"}:
        raise ValueError(table)
    connection = sqlite3.connect(path)
    connection.execute(
        f"CREATE TABLE {table}("
        "primitive_id TEXT PRIMARY KEY, pool TEXT, title TEXT, blackbox TEXT, tags TEXT, "
        "input_edge TEXT, output_edge TEXT, serves_truth INTEGER DEFAULT 0, verification_level TEXT)"
    )
    connection.executemany(
        f"INSERT INTO {table}(primitive_id,pool,title,blackbox,tags,input_edge,output_edge) "
        "VALUES(?,?,?,?,?,?,?)",
        rows,
    )
    connection.commit()
    connection.close()


def _fixture_embedder(dimension: int, model: Optional[str] = None) -> EmbedderPort:
    def encode(texts: Sequence[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), dimension), dtype="float32")
        for row, text in enumerate(texts):
            raw = hashlib.sha256(text.encode("utf-8")).digest()
            for column in range(dimension):
                matrix[row, column] = (raw[column] + 1) / 256.0
        return matrix

    return EmbedderPort(
        model=model or f"fixture:sha256:{dimension}",
        description="Hermetic deterministic fixture embedder",
        dimension=dimension,
        encode_many=encode,
    )


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    core_rows = [
        ("p:a", "core", "Deduplicate rows", "Remove duplicate records by key.", "data", "Rows", "Rows"),
        ("p:b", "core", "Parse invoice", "Extract invoice fields from PDF.", "document", "Pdf", "Invoice"),
        ("p:c", "core", "Verify signature", "Verify an HMAC request signature.", "security", "Request", "Bool"),
    ]
    overlay_rows = [
        ("p:b", "overlay", "Duplicate parse", "Duplicate ID must be skipped.", "dup", "Pdf", "Invoice"),
        ("p:d", "overlay", "Resize image", "Resize an image to fixed dimensions.", "media", "Image", "Image"),
        ("p:e", "overlay", "Send webhook", "POST a signed webhook with retry.", "http", "Event", "Receipt"),
    ]
    with tempfile.TemporaryDirectory(prefix="primitive-embedding-shard-test-") as tmp:
        root = Path(tmp)
        core = root / "core.db"
        overlay = root / "overlay.db"
        _fixture_db(core, core_rows)
        _fixture_db(overlay, overlay_rows, table="overlay_primitives")
        state_dir = root / "state"
        config = LoopConfig(state_dir=state_dir, core_db=core, overlay_db=overlay, batch_size=2)
        embedder = _fixture_embedder(4)

        dry = _dry_run(config)
        checks.append(
            (
                "default dry run sees the tiny FTS/core DB without writing state",
                dry["next_source"] == "core"
                and dry["next_source_rowid"] == 1
                and dry["writes_performed"] is False
                and not state_dir.exists(),
            )
        )

        first = _execute_tick(config, embedder)
        first_state = _read_json(state_dir / STATE_FILENAME)
        second = _execute_tick(config, embedder)
        second_state = _read_json(state_dir / STATE_FILENAME)
        checks.append(
            (
                "the next tick advances the durable core rowid cursor",
                first["rows_embedded"] == 2
                and first_state["source_cursors"]["core"] == 2
                and second["rows_embedded"] == 1
                and second_state["source_cursors"]["core"] == 3,
            )
        )

        # Geometry is a corpus contract: even a valid matrix with a different
        # dimension may not be appended to the existing shard family.
        before_dimension_failure = _read_json(state_dir / MANIFEST_FILENAME)
        try:
            _execute_tick(config, _fixture_embedder(3, model=embedder.model))
            dimension_failed = False
        except ValueError as exc:
            dimension_failed = "dimension mismatch" in str(exc)
        after_dimension_failure = _read_json(state_dir / MANIFEST_FILENAME)
        checks.append(
            (
                "dimension mismatch fails before committing another shard",
                dimension_failed and before_dimension_failure == after_dimension_failure,
            )
        )

        third = _execute_tick(config, embedder)
        fourth = _execute_tick(config, embedder)
        manifest = _read_json(state_dir / MANIFEST_FILENAME)
        all_ids: list[str] = []
        validated_rows = 0
        for shard in manifest["shards"]:
            shard_dir = state_dir / shard["directory"]
            validated = _validate_shard(shard_dir)
            validated_rows += validated["rows"]
            all_ids.extend(_read_json(shard_dir / OUTPUT_FILES["primitive_id"]))
        checks.append(
            (
                "federated overlay advances after core and duplicate IDs never enter shards",
                third["source"] == "overlay"
                and set(all_ids) == {"p:a", "p:b", "p:c", "p:d", "p:e"}
                and len(all_ids) == len(set(all_ids)) == 5
                and fourth["rows_embedded"] == 0,
            )
        )
        checks.append(
            (
                "coverage count equals the sum of validated manifest rows",
                manifest["coverage_rows"] == validated_rows == len(all_ids) == 5,
            )
        )
        checks.append(
            (
                "each shard declares exact column metadata and candidate boundary",
                all(
                    shard_manifest["candidate"] is True
                    and shard_manifest["serves_truth"] is False
                    and all(
                        {
                            "schema",
                            "description",
                            "units",
                            "model",
                            "dimension",
                            "source_digest",
                        }
                        <= set(column)
                        for column in shard_manifest["column_schema"]
                    )
                    for shard_manifest in (
                        _validate_shard(state_dir / shard["directory"]) for shard in manifest["shards"]
                    )
                ),
            )
        )

        # Mutation gate: corruption after partial writes but before directory
        # publication must fail validation and leave no committed shard/index.
        corrupt_state = root / "corrupt-state"
        corrupt_config = LoopConfig(
            state_dir=corrupt_state, core_db=core, overlay_db=None, batch_size=2
        )

        def corrupt_partial(directory: Path) -> None:
            np.save(directory / OUTPUT_FILES["plain"], np.zeros((1, 2), dtype="float32"))

        try:
            _execute_tick(corrupt_config, embedder, fault_injector=corrupt_partial)
            corruption_failed = False
        except ValueError:
            corruption_failed = True
        committed_dirs = [
            path
            for path in (corrupt_state / SHARDS_DIRNAME).glob("*")
            if path.is_dir() and not path.name.startswith(".partial-")
        ] if (corrupt_state / SHARDS_DIRNAME).exists() else []
        partial_dirs = list((corrupt_state / SHARDS_DIRNAME).glob(".partial-*")) \
            if (corrupt_state / SHARDS_DIRNAME).exists() else []
        checks.append(
            (
                "a corrupt partial shard is rejected and never committed",
                corruption_failed
                and not committed_dirs
                and not partial_dirs
                and not (corrupt_state / MANIFEST_FILENAME).exists()
                and not (corrupt_state / STATE_FILENAME).exists(),
            )
        )

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} failures: {failed}")
        return 1
    print(
        "\nPASS - primitive_embedding_shard_loop: rowid cursors advance across immutable, aligned blackbox + "
        "plain/technical/semantic + feature shards; cross-source IDs dedupe; geometry mismatches and corrupted "
        "partials fail closed; coverage is measured from validated shard rows only. "
        "candidate=true / serves_truth=false."
    )
    return 0


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="embed and commit one bounded shard")
    mode.add_argument("--watch", action="store_true", help="run bounded shard ticks repeatedly")
    parser.add_argument("--self-test", action="store_true", help="run the hermetic mutation-gated proof")
    parser.add_argument("--batch-size", type=_positive_int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--core-db", default=str(DEFAULT_CORE_DB))
    parser.add_argument(
        "--overlay-db",
        default=str(DEFAULT_OVERLAY_DB),
        help="optional primitive-search federation overlay DB; a missing path is skipped",
    )
    parser.add_argument(
        "--no-overlay", action="store_true", help="disable the optional federated overlay source"
    )
    parser.add_argument("--embed-path", choices=("tokens", "model2vec"), default=DEFAULT_EMBED_PATH)
    parser.add_argument("--interval", type=_positive_int, default=DEFAULT_INTERVAL_SECONDS)
    parser.add_argument("--max-ticks", type=_positive_int, default=DEFAULT_MAX_TICKS)
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    config = LoopConfig(
        state_dir=Path(args.state_dir).expanduser().resolve(),
        core_db=Path(args.core_db).expanduser().resolve(),
        overlay_db=None if args.no_overlay else Path(args.overlay_db).expanduser().resolve(),
        batch_size=args.batch_size,
    )
    if not args.once and not args.watch:
        print(json.dumps(_dry_run(config), indent=2, sort_keys=True))
        return 0

    embedder = _make_embedder(args.embed_path)
    ticks = args.max_ticks if args.watch else 1
    try:
        receipts = _run_ticks(config, embedder, ticks, args.interval)
    except (FileNotFoundError, RuntimeError, ValueError, sqlite3.Error) as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}", **BOUNDARY}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "record_type": "primitive_embedding_shard_run_summary",
                "ticks": len(receipts),
                "rows_embedded": sum(receipt["rows_embedded"] for receipt in receipts),
                "coverage_rows": receipts[-1]["coverage_rows"],
                "last_source_cursors": receipts[-1]["source_cursors"],
                "embed_model": embedder.model,
                "dimension": embedder.dimension,
                "manifest": str(config.state_dir / MANIFEST_FILENAME),
                **BOUNDARY,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
