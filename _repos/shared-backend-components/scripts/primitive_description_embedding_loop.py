#!/usr/bin/env python3
"""Build immutable, revision-aware embedding shards for primitive descriptions.

The source of record is the ``current_descriptions`` table created by
``primitive_description_backfill_loop.py``.  That table updates a primitive in place when a better
description revision is accepted, so a rowid-only cursor is not sufficient: it would never notice a revised
description.  This worker instead maintains a rebuildable dedupe catalog whose immutable key is::

    (primitive_id, description_digest, embedding_profile, model, dimension)

The full key makes an unchanged description/profile idempotent while a changed ``description_digest`` creates
new work.  Published shards are append-only, so vectors and source mappings for older description revisions
remain auditable after the current sidecar row advances.

Four progressively useful text profiles are embedded independently: ``plain``, ``technical``, ``semantic``,
and ``envelope``.  The default and only execution path is the repository's deterministic offline token
embedder.  It performs no network or model call.  These vectors are retrieval plumbing, not evidence that the
description is semantically correct and not evidence that the described primitive passed an execution oracle.

Commands::

    PYTHONPATH=. python3 scripts/primitive_description_embedding_loop.py --once --batch-size 4096
    PYTHONPATH=. python3 scripts/primitive_description_embedding_loop.py --stats
    PYTHONPATH=. python3 scripts/primitive_description_embedding_loop.py --self-test

Every output remains ``candidate=true`` and ``serves_truth=false``.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_SBC = next((parent for parent in _HERE.parents if (parent / "scripts" / "_repo_paths.py").exists()), _HERE.parents[1])
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import fcntl  # noqa: E402
import hashlib  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import sqlite3  # noqa: E402
import tempfile  # noqa: E402
import zlib  # noqa: E402
import uuid  # noqa: E402
from contextlib import closing, contextmanager  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from typing import Any, Iterable, Iterator, Mapping, Sequence  # noqa: E402

import numpy as np  # noqa: E402

from scripts import capability_embedding as _embedding  # noqa: E402
from scripts.build_primitive_search_index import tokenize as _tokenize  # noqa: E402


BOUNDARY: dict[str, bool] = {"candidate": True, "serves_truth": False}
SCHEMA_VERSION = 1
INDEX_RECORD_TYPE = "primitive_description_embedding_index"
SHARD_RECORD_TYPE = "primitive_description_embedding_shard"
TICK_RECORD_TYPE = "primitive_description_embedding_tick"
STATS_RECORD_TYPE = "primitive_description_embedding_stats"
CATALOG_SCHEMA = "primitive_description_embedding_catalog"
STATE_SCHEMA = "primitive_description_embedding_state"

DEFAULT_DESCRIPTION_DB = resource("dist") / "primitive_description_sidecar.db"
DEFAULT_STATE_DIR = resource("dist") / "primitive-description-embedding-shards"
DEFAULT_BATCH_SIZE = 4_096

SHARDS_DIRNAME = "shards"
INDEX_FILENAME = "manifest.json"
STATE_FILENAME = "state.json"
CATALOG_FILENAME = "embedding_jobs.sqlite"
LOCK_FILENAME = ".writer.lock"
LEDGER_FILENAME = "ledger.jsonl"
SHARD_MANIFEST_FILENAME = "manifest.json"
KEYS_FILENAME = "embedding_keys.jsonl"
SOURCE_ROWS_FILENAME = "source_rows.jsonl"
SOURCE_TEXTS_FILENAME = "source_texts.jsonl"
VECTORS_FILENAME = "embeddings.npy"
COLUMN_MANIFEST_DIRNAME = "columns"

DESCRIPTION_TABLE = "current_descriptions"
DESCRIPTION_META_TABLE = "description_meta"
EMBEDDING_PROFILES: tuple[str, ...] = ("plain", "technical", "semantic", "envelope")
PROFILE_SOURCE_FIELDS: dict[str, str] = {
    "plain": "plain",
    "technical": "technical",
    "semantic": "semantic",
    "envelope": "semantic_envelope_json",
}
PROFILE_DESCRIPTIONS: dict[str, str] = {
    "plain": "Human-oriented problem, solution, use, and avoidance language",
    "technical": "Typed edges, runtime, effects, preconditions, postconditions, and failures",
    "semantic": "Composition, proof, blocker, fit, and near-miss semantics",
    "envelope": "Labelled semantic-envelope facets including use, non-use, failure, and composition",
}

# This fixed label versions the actual deterministic algorithm, not merely the Python function name.  If the
# algorithm changes incompatibly, mint a new label so the five-part immutable key remains meaningful.
OFFLINE_MODEL = "capability_embedding:tokens-crc32-tf:v1"
OFFLINE_MODEL_DESCRIPTION = (
    "Deterministic L2-normalized hashed token-term-frequency vector from "
    "scripts.capability_embedding.embed_tokens; no network or model inference"
)

REQUIRED_SOURCE_COLUMNS: tuple[str, ...] = (
    "primitive_id",
    "description_digest",
    "source_surface_digest",
    "policy_version",
    "pool",
    "title",
    "blackbox",
    "input_edge",
    "output_edge",
    "plain",
    "technical",
    "semantic",
    "semantic_envelope_json",
    "provenance_json",
    "source_path",
    "source_line",
    "created_at",
    "candidate",
    "serves_truth",
)


@dataclass(frozen=True, slots=True)
class EmbedderPort:
    model: str
    description: str
    dimension: int

    def encode_many(self, texts: Sequence[str]) -> np.ndarray:
        # Vectorized storage/normalization avoids allocating one 256-float Python list per surface while
        # preserving capability_embedding.embed_tokens exactly. Token hashing stays row-local and deterministic.
        matrix = np.zeros((len(texts), self.dimension), dtype="float32")
        for row_index, text_value in enumerate(texts):
            for token in _tokenize(str(text_value)):
                matrix[row_index, zlib.crc32(token.encode()) % self.dimension] += 1.0
        expected = (len(texts), self.dimension)
        if matrix.ndim != 2 or tuple(matrix.shape) != expected:
            raise ValueError(f"embedding shape mismatch: got {matrix.shape}, expected {expected}")
        if not np.isfinite(matrix).all():
            raise ValueError("embedding matrix contains non-finite values")
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        matrix /= norms
        return matrix


@dataclass(frozen=True, slots=True)
class EmbeddingJob:
    source_rowid: int
    primitive_id: str
    description_digest: str
    source_surface_digest: str
    policy_version: str
    pool: str
    embedding_profile: str
    text: str
    title: str
    blackbox: str
    input_edge: str
    output_edge: str
    provenance_json: str
    source_path: str
    source_line: int
    description_created_at: str

    def key_record(self, embedder: EmbedderPort) -> dict[str, Any]:
        return {
            "primitive_id": self.primitive_id,
            "description_digest": self.description_digest,
            "embedding_profile": self.embedding_profile,
            "model": embedder.model,
            "dimension": embedder.dimension,
            "text_digest": _sha256_text(self.text),
            **BOUNDARY,
        }

    def source_record(self, description_db: Path) -> dict[str, Any]:
        return {
            "description_db": _relative_or_absolute(description_db),
            "description_table": DESCRIPTION_TABLE,
            "source_rowid": self.source_rowid,
            "primitive_id": self.primitive_id,
            "description_digest": self.description_digest,
            "source_surface_digest": self.source_surface_digest,
            "description_policy_version": self.policy_version,
            "pool": self.pool,
            "embedding_profile": self.embedding_profile,
            "profile_source_field": PROFILE_SOURCE_FIELDS[self.embedding_profile],
            "description_source_path": self.source_path,
            "description_source_line": self.source_line,
            "description_created_at": self.description_created_at,
            **BOUNDARY,
        }

    def text_record(self) -> dict[str, Any]:
        return {
            "primitive_id": self.primitive_id,
            "description_digest": self.description_digest,
            "embedding_profile": self.embedding_profile,
            "text": self.text,
            "text_digest": _sha256_text(self.text),
            **BOUNDARY,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(str(value).encode("utf-8"))


def _digest(value: Any) -> str:
    return _sha256_text(_canonical_json(value))


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _relative_or_absolute(path: Path, base: Path = _SBC) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(base.resolve()))
    except ValueError:
        return str(resolved)


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


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_canonical_json(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            yield row


def _append_ledger(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_canonical_json(payload) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _offline_embedder() -> EmbedderPort:
    dimension = len(_embedding.embed_tokens("offline dimension probe"))
    if dimension < 1:
        raise RuntimeError("deterministic token embedder returned an invalid dimension")
    return EmbedderPort(
        model=OFFLINE_MODEL,
        description=OFFLINE_MODEL_DESCRIPTION,
        dimension=dimension,
    )


def _embedder_implementation_digest() -> str:
    return _sha256_text(inspect.getsource(_embedding.embed_tokens))


def _source_schema(description_db: Path) -> dict[str, Any]:
    path = Path(description_db)
    if not path.is_file():
        raise FileNotFoundError(f"primitive description sidecar does not exist: {path}")
    with closing(sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(f"PRAGMA table_info({DESCRIPTION_TABLE})").fetchall()
        if not rows:
            raise ValueError(f"sidecar has no {DESCRIPTION_TABLE} table: {path}")
        columns = [
            {
                "cid": int(row["cid"]),
                "name": str(row["name"]),
                "type": str(row["type"] or ""),
                "not_null": bool(row["notnull"]),
                "primary_key_position": int(row["pk"]),
            }
            for row in rows
        ]
        names = {column["name"] for column in columns}
        missing = sorted(set(REQUIRED_SOURCE_COLUMNS) - names)
        if missing:
            raise ValueError(f"description sidecar misses required columns {missing}: {path}")
        meta_present = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (DESCRIPTION_META_TABLE,)
        ).fetchone()
        schema_version = None
        if meta_present:
            row = connection.execute(
                f"SELECT value FROM {DESCRIPTION_META_TABLE} WHERE key='schema_version'"
            ).fetchone()
            schema_version = str(row[0]) if row is not None else None
    surface = {
        "table": DESCRIPTION_TABLE,
        "columns": columns,
        "sidecar_schema_version": schema_version,
        "selected_columns": list(REQUIRED_SOURCE_COLUMNS),
    }
    return {**surface, "schema_digest": _digest(surface)}


def _open_catalog(state_dir: Path) -> sqlite3.Connection:
    state_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(state_dir / CATALOG_FILENAME), timeout=60, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.execute("PRAGMA busy_timeout=60000")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS embedding_jobs(
            primitive_id TEXT NOT NULL,
            description_digest TEXT NOT NULL,
            embedding_profile TEXT NOT NULL,
            model TEXT NOT NULL,
            dimension INTEGER NOT NULL,
            shard_id TEXT NOT NULL,
            shard_row INTEGER NOT NULL,
            source_rowid INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            candidate INTEGER NOT NULL CHECK(candidate=1),
            serves_truth INTEGER NOT NULL CHECK(serves_truth=0),
            PRIMARY KEY(primitive_id,description_digest,embedding_profile,model,dimension)
        );
        CREATE INDEX IF NOT EXISTS embedding_jobs_description
            ON embedding_jobs(primitive_id,description_digest);
        CREATE TABLE IF NOT EXISTS catalog_meta(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    current = connection.execute(
        "SELECT value FROM catalog_meta WHERE key='catalog_schema'"
    ).fetchone()
    if current is not None and str(current[0]) != CATALOG_SCHEMA:
        raise RuntimeError(f"unsupported embedding catalog schema {current[0]!r}")
    connection.execute(
        "INSERT OR REPLACE INTO catalog_meta(key,value) VALUES('catalog_schema',?)",
        (CATALOG_SCHEMA,),
    )
    connection.commit()
    return connection


def _empty_index(description_db: Path, embedder: EmbedderPort) -> dict[str, Any]:
    return {
        "record_type": INDEX_RECORD_TYPE,
        "schema_version": SCHEMA_VERSION,
        "description_db": _relative_or_absolute(description_db),
        "source_table": DESCRIPTION_TABLE,
        "embedding_profiles": list(EMBEDDING_PROFILES),
        "geometry": {
            "model": embedder.model,
            "model_description": embedder.description,
            "dimension": embedder.dimension,
            "dtype": "float32",
            "normalization": "L2",
            "network_calls": False,
            "model_inference_calls": False,
            "embedder_implementation_digest": _embedder_implementation_digest(),
        },
        "coverage_jobs": 0,
        "profile_counts": {profile: 0 for profile in EMBEDDING_PROFILES},
        "shards": [],
        "semantic_quality_verified": 0,
        "descriptor_specific_execution_verified": 0,
        "verification_note": (
            "Deterministic vectors are retrieval plumbing only; embedding does not prove description semantics "
            "or primitive execution correctness."
        ),
        **BOUNDARY,
    }


def _validate_index(index: Mapping[str, Any], description_db: Path, embedder: EmbedderPort) -> None:
    if index.get("record_type") != INDEX_RECORD_TYPE:
        raise ValueError(f"unexpected index record type {index.get('record_type')!r}")
    if int(index.get("schema_version", -1)) != SCHEMA_VERSION:
        raise ValueError(f"unsupported index schema {index.get('schema_version')!r}")
    if index.get("candidate") is not True or index.get("serves_truth") is not False:
        raise ValueError("embedding index lost the candidate-only boundary")
    expected_source = _relative_or_absolute(description_db)
    if index.get("description_db") != expected_source:
        raise ValueError(
            f"description source changed: {index.get('description_db')!r} != {expected_source!r}; "
            "use a new --state-dir"
        )
    geometry = index.get("geometry") if isinstance(index.get("geometry"), Mapping) else {}
    if geometry.get("model") != embedder.model or int(geometry.get("dimension", -1)) != embedder.dimension:
        raise ValueError("embedding geometry changed; use a new --state-dir or a newly versioned model label")
    shards = index.get("shards")
    if not isinstance(shards, list):
        raise ValueError("embedding index shards must be a list")
    shard_ids = [str(shard.get("shard_id")) for shard in shards]
    if len(shard_ids) != len(set(shard_ids)):
        raise ValueError("embedding index contains duplicate shard IDs")
    measured_jobs = sum(int(shard.get("embedding_jobs", 0)) for shard in shards)
    if measured_jobs != int(index.get("coverage_jobs", -1)):
        raise ValueError(f"index coverage mismatch: {index.get('coverage_jobs')} != {measured_jobs}")
    measured_profiles = {profile: 0 for profile in EMBEDDING_PROFILES}
    for shard in shards:
        for profile, count in dict(shard.get("profile_counts") or {}).items():
            if profile not in measured_profiles:
                raise ValueError(f"unknown embedding profile in shard summary: {profile}")
            measured_profiles[profile] += int(count)
    if measured_profiles != dict(index.get("profile_counts") or {}):
        raise ValueError("index profile counts do not equal the published shard summaries")


def _load_index(state_dir: Path, description_db: Path, embedder: EmbedderPort) -> dict[str, Any]:
    path = state_dir / INDEX_FILENAME
    index = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else _empty_index(description_db, embedder)
    _validate_index(index, description_db, embedder)
    return index


def _shard_set_digest(index: Mapping[str, Any]) -> str:
    return _digest(
        [
            {
                "shard_id": shard.get("shard_id"),
                "keys_digest": shard.get("keys_digest"),
                "embedding_jobs": shard.get("embedding_jobs"),
            }
            for shard in index.get("shards", [])
        ]
    )


def _sync_catalog(connection: sqlite3.Connection, state_dir: Path, index: Mapping[str, Any]) -> None:
    expected = _shard_set_digest(index)
    current = connection.execute(
        "SELECT value FROM catalog_meta WHERE key='shard_set_digest'"
    ).fetchone()
    if current is not None and str(current[0]) == expected:
        return
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute("DELETE FROM embedding_jobs")
        for shard in index.get("shards", []):
            shard_id = str(shard["shard_id"])
            shard_dir = state_dir / str(shard["directory"])
            for row_index, key in enumerate(_read_jsonl(shard_dir / KEYS_FILENAME)):
                connection.execute(
                    """INSERT INTO embedding_jobs(
                           primitive_id,description_digest,embedding_profile,model,dimension,
                           shard_id,shard_row,source_rowid,created_at,candidate,serves_truth
                       ) VALUES(?,?,?,?,?,?,?,?,?,1,0)""",
                    (
                        str(key["primitive_id"]),
                        str(key["description_digest"]),
                        str(key["embedding_profile"]),
                        str(key["model"]),
                        int(key["dimension"]),
                        shard_id,
                        row_index,
                        int(key["source_rowid"]),
                        str(shard["created_at"]),
                    ),
                )
        connection.execute(
            "INSERT OR REPLACE INTO catalog_meta(key,value) VALUES('shard_set_digest',?)", (expected,)
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _attach_description_db(connection: sqlite3.Connection, description_db: Path) -> None:
    uri = f"file:{Path(description_db).resolve()}?mode=ro"
    connection.execute("ATTACH DATABASE ? AS descriptions", (uri,))


def _detach_description_db(connection: sqlite3.Connection) -> None:
    connection.execute("DETACH DATABASE descriptions")


def _cursor(connection: sqlite3.Connection, lane: str) -> tuple[int, int]:
    if lane not in {"new", "revision"}:
        raise ValueError(f"unknown scan lane {lane!r}")
    values: dict[str, int] = {}
    for suffix, default in (("rowid", 0), ("profile_ordinal", -1)):
        row = connection.execute(
            "SELECT value FROM catalog_meta WHERE key=?", (f"{lane}_{suffix}",)
        ).fetchone()
        values[suffix] = int(row[0]) if row is not None else default
    return values["rowid"], values["profile_ordinal"]


def _write_cursors(connection: sqlite3.Connection, cursors: Mapping[str, tuple[int, int]]) -> None:
    connection.execute("BEGIN IMMEDIATE")
    try:
        for lane, (rowid, profile_ordinal) in cursors.items():
            if lane not in {"new", "revision"}:
                raise ValueError(f"unknown scan lane {lane!r}")
            connection.execute(
                "INSERT OR REPLACE INTO catalog_meta(key,value) VALUES(?,?)",
                (f"{lane}_rowid", str(int(rowid))),
            )
            connection.execute(
                "INSERT OR REPLACE INTO catalog_meta(key,value) VALUES(?,?)",
                (f"{lane}_profile_ordinal", str(int(profile_ordinal))),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def _flatten_envelope(raw_json: str) -> str:
    try:
        value = json.loads(raw_json or "{}")
    except json.JSONDecodeError:
        value = {"unparsed_envelope": str(raw_json or "")}
    if not isinstance(value, Mapping):
        value = {"envelope": value}
    parts: list[str] = []
    preferred = (
        "does",
        "use_when",
        "not_when",
        "fails_when",
        "composes_with",
        "preconditions",
        "postconditions",
        "effects",
        "proof_requirements",
        "promotion_blockers",
        "human_action_core",
    )
    ordered_keys = [key for key in preferred if key in value]
    ordered_keys.extend(sorted(str(key) for key in value if str(key) not in ordered_keys))
    for key in ordered_keys:
        item = value.get(key)
        if item in (None, "", [], {}):
            continue
        if isinstance(item, Mapping):
            rendered = _canonical_json(item)
        elif isinstance(item, (list, tuple, set)):
            rendered = "; ".join(str(part).strip() for part in item if str(part).strip())
        else:
            rendered = str(item).strip()
        if rendered:
            parts.append(f"{key.replace('_', ' ')}: {rendered}")
    return ". ".join(parts).strip()


def _profile_text(row: Mapping[str, Any], profile: str) -> str:
    if profile not in EMBEDDING_PROFILES:
        raise ValueError(f"unknown embedding profile {profile!r}")
    if profile == "envelope":
        value = _flatten_envelope(str(row["semantic_envelope_json"] or "{}"))
    else:
        value = str(row[PROFILE_SOURCE_FIELDS[profile]] or "").strip()
    if value:
        return value
    # Empty optional facets remain searchable without conflating profiles: the labelled fallback makes the
    # substitution explicit in the text itself and is covered by the description digest.
    blackbox = str(row["blackbox"] or "").strip()
    title = str(row["title"] or "").strip()
    return f"{profile} fallback: {blackbox or title}".strip()


def _select_unseen_jobs(
    connection: sqlite3.Connection,
    description_db: Path,
    embedder: EmbedderPort,
    batch_size: int,
) -> tuple[list[EmbeddingJob], dict[str, Any], dict[str, tuple[int, int]]]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    cursors = {"new": _cursor(connection, "new"), "revision": _cursor(connection, "revision")}
    cursor_updates = dict(cursors)
    _attach_description_db(connection, description_db)
    try:
        profile_values = ",".join("(?,?)" for _ in EMBEDDING_PROFILES)
        profile_params: list[Any] = []
        for ordinal, profile in enumerate(EMBEDDING_PROFILES):
            profile_params.extend((profile, ordinal))
        sql = f"""
            WITH profiles(embedding_profile,ordinal) AS (VALUES {profile_values})
            SELECT d.rowid AS source_rowid,d.*,p.embedding_profile,p.ordinal
            FROM descriptions.{DESCRIPTION_TABLE} AS d
            CROSS JOIN profiles AS p
            WHERE (d.rowid>? OR (d.rowid=? AND p.ordinal>?))
              AND d.candidate=1
              AND d.serves_truth=0
            ORDER BY d.rowid,p.ordinal
            LIMIT ?
        """
        new_cursor = cursors["new"]
        rows = connection.execute(
            sql, (*profile_params, new_cursor[0], new_cursor[0], new_cursor[1], int(batch_size))
        ).fetchall()
        lane = "new"
        reset_revision_cycle = False
        if not rows:
            lane = "revision"
            revision_cursor = cursors["revision"]
            rows = connection.execute(
                sql,
                (*profile_params, revision_cursor[0], revision_cursor[0], revision_cursor[1], int(batch_size)),
            ).fetchall()
            if not rows and revision_cursor != (0, -1):
                # A completed revision sweep immediately wraps to the first row.  This bounded cycle catches
                # in-place description updates without repeatedly scanning the already-embedded prefix on every
                # tick, and it avoids an otherwise unavoidable empty tick at the end of every cycle.
                reset_revision_cycle = True
                rows = connection.execute(
                    sql, (*profile_params, 0, 0, -1, int(batch_size))
                ).fetchall()
                cursor_updates["revision"] = (0, -1)
        if rows:
            cursor_updates[lane] = (int(rows[-1]["source_rowid"]), int(rows[-1]["ordinal"]))
        source_max_rowid = int(
            connection.execute(
                f"SELECT coalesce(max(rowid),0) FROM descriptions.{DESCRIPTION_TABLE}"
            ).fetchone()[0]
        )
    finally:
        _detach_description_db(connection)

    candidate_jobs: list[EmbeddingJob] = []
    for row in rows:
        if int(row["candidate"]) != 1 or int(row["serves_truth"]) != 0:
            raise ValueError(f"description row {row['primitive_id']} violates the candidate-only boundary")
        profile = str(row["embedding_profile"])
        candidate_jobs.append(
            EmbeddingJob(
                source_rowid=int(row["source_rowid"]),
                primitive_id=str(row["primitive_id"]),
                description_digest=str(row["description_digest"]),
                source_surface_digest=str(row["source_surface_digest"]),
                policy_version=str(row["policy_version"]),
                pool=str(row["pool"] or ""),
                embedding_profile=profile,
                text=_profile_text(row, profile),
                title=str(row["title"] or ""),
                blackbox=str(row["blackbox"] or ""),
                input_edge=str(row["input_edge"] or ""),
                output_edge=str(row["output_edge"] or ""),
                provenance_json=str(row["provenance_json"] or "{}"),
                source_path=str(row["source_path"] or ""),
                source_line=int(row["source_line"] or 0),
                description_created_at=str(row["created_at"] or ""),
            )
        )
    seen_keys: set[tuple[str, str, str, str, int]] = set()
    # SQLite's default bind limit is commonly 999.  A conservative 100 five-column tuples keeps this portable.
    key_chunk_size = 100
    for start in range(0, len(candidate_jobs), key_chunk_size):
        chunk = candidate_jobs[start : start + key_chunk_size]
        if not chunk:
            continue
        placeholders = ",".join("(?,?,?,?,?)" for _ in chunk)
        params: list[Any] = []
        for job in chunk:
            params.extend(
                (
                    job.primitive_id,
                    job.description_digest,
                    job.embedding_profile,
                    embedder.model,
                    embedder.dimension,
                )
            )
        for seen in connection.execute(
            "SELECT primitive_id,description_digest,embedding_profile,model,dimension "
            f"FROM embedding_jobs WHERE (primitive_id,description_digest,embedding_profile,model,dimension) "
            f"IN ({placeholders})",
            params,
        ):
            seen_keys.add(
                (
                    str(seen["primitive_id"]),
                    str(seen["description_digest"]),
                    str(seen["embedding_profile"]),
                    str(seen["model"]),
                    int(seen["dimension"]),
                )
            )
    jobs = [
        job
        for job in candidate_jobs
        if (
            job.primitive_id,
            job.description_digest,
            job.embedding_profile,
            embedder.model,
            embedder.dimension,
        )
        not in seen_keys
    ]
    keys = [
        (job.primitive_id, job.description_digest, job.embedding_profile, embedder.model, embedder.dimension)
        for job in jobs
    ]
    if len(keys) != len(set(keys)):
        raise ValueError("unseen-job query returned duplicate immutable keys")
    return jobs, {
        "lane": lane,
        "scanned_profile_rows": len(candidate_jobs),
        "already_embedded": len(candidate_jobs) - len(jobs),
        "source_max_rowid": source_max_rowid,
        "selected_jobs": len(jobs),
        "cursor_before": {name: list(value) for name, value in cursors.items()},
        "cursor_after": {name: list(value) for name, value in cursor_updates.items()},
        "revision_cycle_reset": reset_revision_cycle,
    }, cursor_updates


def _column_descriptor(
    *,
    name: str,
    file: str,
    schema: str,
    description: str,
    shape: list[int],
    source_digest: str,
    content_sha256: str,
    model: str = "none",
    dimension: int = 1,
) -> dict[str, Any]:
    return {
        "record_type": "primitive_description_embedding_column_manifest",
        "schema_version": SCHEMA_VERSION,
        "name": name,
        "file": file,
        "schema": schema,
        "description": description,
        "shape": shape,
        "source_digest": source_digest,
        "content_sha256": content_sha256,
        "model": model,
        "dimension": dimension,
        **BOUNDARY,
    }


def _write_shard(
    state_dir: Path,
    description_db: Path,
    source_schema: Mapping[str, Any],
    jobs: Sequence[EmbeddingJob],
    embedder: EmbedderPort,
    sequence: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not jobs:
        raise ValueError("cannot publish an empty embedding shard")
    texts = [job.text for job in jobs]
    vectors = embedder.encode_many(texts)
    key_records = [
        {**job.key_record(embedder), "source_rowid": job.source_rowid} for job in jobs
    ]
    source_records = [job.source_record(description_db) for job in jobs]
    text_records = [job.text_record() for job in jobs]
    keys_digest = _digest(key_records)
    shard_id = f"shard-{sequence:08d}-{keys_digest[:12]}-{uuid.uuid4().hex[:8]}"
    shards_root = state_dir / SHARDS_DIRNAME
    shards_root.mkdir(parents=True, exist_ok=True)
    temporary = shards_root / f".{shard_id}.tmp"
    destination = shards_root / shard_id
    temporary.mkdir()
    try:
        _write_jsonl(temporary / KEYS_FILENAME, key_records)
        _write_jsonl(temporary / SOURCE_ROWS_FILENAME, source_records)
        _write_jsonl(temporary / SOURCE_TEXTS_FILENAME, text_records)
        with (temporary / VECTORS_FILENAME).open("wb") as handle:
            np.save(handle, vectors, allow_pickle=False)
            handle.flush()
            os.fsync(handle.fileno())

        logical_sources = {
            "embedding_key": key_records,
            "source_mapping": source_records,
            "profile_text": text_records,
            "embedding_vector": [
                {
                    "primitive_id": job.primitive_id,
                    "description_digest": job.description_digest,
                    "embedding_profile": job.embedding_profile,
                    "text_digest": _sha256_text(job.text),
                }
                for job in jobs
            ],
        }
        descriptors = [
            _column_descriptor(
                name="embedding_key",
                file=KEYS_FILENAME,
                schema=(
                    "JSONL {primitive_id,description_digest,embedding_profile,model,dimension,text_digest,"
                    "source_rowid,candidate,serves_truth}"
                ),
                description="The exact immutable five-part dedupe key plus aligned source row and text digest",
                shape=[len(jobs)],
                source_digest=_digest(logical_sources["embedding_key"]),
                content_sha256=_file_digest(temporary / KEYS_FILENAME),
                dimension=5,
            ),
            _column_descriptor(
                name="source_mapping",
                file=SOURCE_ROWS_FILENAME,
                schema="JSONL source-sidecar and original-description provenance mapping",
                description="Auditable mapping from every vector row to its sidecar revision and source payload",
                shape=[len(jobs)],
                source_digest=_digest(logical_sources["source_mapping"]),
                content_sha256=_file_digest(temporary / SOURCE_ROWS_FILENAME),
            ),
            _column_descriptor(
                name="profile_text",
                file=SOURCE_TEXTS_FILENAME,
                schema="JSONL {primitive_id,description_digest,embedding_profile,text,text_digest}",
                description="Exact immutable text surface embedded for each description register revision",
                shape=[len(jobs)],
                source_digest=_digest(logical_sources["profile_text"]),
                content_sha256=_file_digest(temporary / SOURCE_TEXTS_FILENAME),
            ),
            _column_descriptor(
                name="embedding_vector",
                file=VECTORS_FILENAME,
                schema="NumPy .npy float32 matrix",
                description=(
                    "Offline deterministic retrieval vector; it is not a semantic-quality or execution-proof score"
                ),
                shape=[len(jobs), embedder.dimension],
                source_digest=_digest(logical_sources["embedding_vector"]),
                content_sha256=_file_digest(temporary / VECTORS_FILENAME),
                model=embedder.model,
                dimension=embedder.dimension,
            ),
        ]
        column_dir = temporary / COLUMN_MANIFEST_DIRNAME
        column_dir.mkdir()
        column_refs: list[dict[str, Any]] = []
        for descriptor in descriptors:
            descriptor_path = column_dir / f"{descriptor['name']}.manifest.json"
            _atomic_json(descriptor_path, descriptor)
            column_refs.append(
                {
                    **descriptor,
                    "manifest_file": str(descriptor_path.relative_to(temporary)),
                    "manifest_sha256": _file_digest(descriptor_path),
                }
            )

        profile_counts = {profile: 0 for profile in EMBEDDING_PROFILES}
        for job in jobs:
            profile_counts[job.embedding_profile] += 1
        created_at = _now()
        manifest = {
            "record_type": SHARD_RECORD_TYPE,
            "schema_version": SCHEMA_VERSION,
            "shard_id": shard_id,
            "created_at": created_at,
            "immutable": True,
            "embedding_jobs": len(jobs),
            "description_revisions": len({(job.primitive_id, job.description_digest) for job in jobs}),
            "keys_digest": keys_digest,
            "profile_counts": profile_counts,
            "profiles": {
                profile: {
                    "source_field": PROFILE_SOURCE_FIELDS[profile],
                    "description": PROFILE_DESCRIPTIONS[profile],
                }
                for profile in EMBEDDING_PROFILES
            },
            "geometry": {
                "model": embedder.model,
                "model_description": embedder.description,
                "dimension": embedder.dimension,
                "dtype": "float32",
                "normalization": "L2",
                "network_calls": False,
                "model_inference_calls": False,
                "embedder_implementation_digest": _embedder_implementation_digest(),
            },
            "source": {
                "description_db": _relative_or_absolute(description_db),
                "description_table": DESCRIPTION_TABLE,
                "description_schema_digest": source_schema["schema_digest"],
                "sidecar_schema_version": source_schema.get("sidecar_schema_version"),
            },
            "columns": column_refs,
            "semantic_quality_verified": 0,
            "descriptor_specific_execution_verified": 0,
            "verification_note": (
                "Deterministic token vectors prove reproducible retrieval plumbing only. They do not prove that "
                "a description is semantically faithful or that a primitive implementation works."
            ),
            **BOUNDARY,
        }
        _atomic_json(temporary / SHARD_MANIFEST_FILENAME, manifest)
        _validate_shard(temporary, manifest)
        os.replace(temporary, destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    summary = {
        "shard_id": shard_id,
        "directory": str(destination.relative_to(state_dir)),
        "manifest": str((destination / SHARD_MANIFEST_FILENAME).relative_to(state_dir)),
        "manifest_sha256": _file_digest(destination / SHARD_MANIFEST_FILENAME),
        "embedding_jobs": len(jobs),
        "description_revisions": manifest["description_revisions"],
        "profile_counts": profile_counts,
        "keys_digest": keys_digest,
        "created_at": created_at,
    }
    return summary, key_records


def _validate_shard(shard_dir: Path, manifest: Mapping[str, Any] | None = None) -> None:
    value = dict(manifest) if manifest is not None else json.loads(
        (shard_dir / SHARD_MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    if value.get("record_type") != SHARD_RECORD_TYPE:
        raise ValueError(f"unexpected shard record type {value.get('record_type')!r}")
    if value.get("candidate") is not True or value.get("serves_truth") is not False:
        raise ValueError("embedding shard lost the candidate-only boundary")
    jobs = int(value.get("embedding_jobs", -1))
    columns = value.get("columns")
    if not isinstance(columns, list) or len(columns) != 4:
        raise ValueError("embedding shard must carry four per-column manifests")
    for column in columns:
        data_path = shard_dir / str(column["file"])
        descriptor_path = shard_dir / str(column["manifest_file"])
        if _file_digest(data_path) != column["content_sha256"]:
            raise ValueError(f"shard data digest mismatch for {column['name']}")
        if _file_digest(descriptor_path) != column["manifest_sha256"]:
            raise ValueError(f"column-manifest digest mismatch for {column['name']}")
        descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
        if descriptor.get("candidate") is not True or descriptor.get("serves_truth") is not False:
            raise ValueError(f"column {column['name']} lost the candidate boundary")
    keys = list(_read_jsonl(shard_dir / KEYS_FILENAME))
    sources = list(_read_jsonl(shard_dir / SOURCE_ROWS_FILENAME))
    texts = list(_read_jsonl(shard_dir / SOURCE_TEXTS_FILENAME))
    if not (len(keys) == len(sources) == len(texts) == jobs):
        raise ValueError("shard JSONL columns are not row-aligned")
    vectors = np.load(shard_dir / VECTORS_FILENAME, mmap_mode="r", allow_pickle=False)
    expected = (jobs, int(value["geometry"]["dimension"]))
    if tuple(vectors.shape) != expected or vectors.dtype != np.dtype("float32"):
        raise ValueError(f"shard vector geometry mismatch: {vectors.shape}/{vectors.dtype} != {expected}/float32")


def _publish_index(
    state_dir: Path,
    index: Mapping[str, Any],
    summary: Mapping[str, Any],
    embedder: EmbedderPort,
    description_db: Path,
) -> dict[str, Any]:
    updated = dict(index)
    updated["shards"] = [*list(index.get("shards", [])), dict(summary)]
    updated["coverage_jobs"] = int(index.get("coverage_jobs", 0)) + int(summary["embedding_jobs"])
    counts = {profile: int(dict(index.get("profile_counts") or {}).get(profile, 0)) for profile in EMBEDDING_PROFILES}
    for profile, count in dict(summary["profile_counts"]).items():
        counts[profile] += int(count)
    updated["profile_counts"] = counts
    updated["updated_at"] = _now()
    _validate_index(updated, description_db, embedder)
    _atomic_json(state_dir / INDEX_FILENAME, updated)
    return updated


def _record_catalog_shard(
    connection: sqlite3.Connection,
    index: Mapping[str, Any],
    summary: Mapping[str, Any],
    key_records: Sequence[Mapping[str, Any]],
) -> None:
    connection.execute("BEGIN IMMEDIATE")
    try:
        for row_index, key in enumerate(key_records):
            connection.execute(
                """INSERT INTO embedding_jobs(
                       primitive_id,description_digest,embedding_profile,model,dimension,
                       shard_id,shard_row,source_rowid,created_at,candidate,serves_truth
                   ) VALUES(?,?,?,?,?,?,?,?,?,1,0)""",
                (
                    str(key["primitive_id"]),
                    str(key["description_digest"]),
                    str(key["embedding_profile"]),
                    str(key["model"]),
                    int(key["dimension"]),
                    str(summary["shard_id"]),
                    row_index,
                    int(key["source_rowid"]),
                    str(summary["created_at"]),
                ),
            )
        connection.execute(
            "INSERT OR REPLACE INTO catalog_meta(key,value) VALUES('shard_set_digest',?)",
            (_shard_set_digest(index),),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise


@contextmanager
def _writer_lock(state_dir: Path) -> Iterator[None]:
    state_dir.mkdir(parents=True, exist_ok=True)
    with (state_dir / LOCK_FILENAME).open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def run_tick(
    *,
    description_db: Path = DEFAULT_DESCRIPTION_DB,
    state_dir: Path = DEFAULT_STATE_DIR,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, Any]:
    """Embed at most ``batch_size`` unseen revision/profile jobs and publish one immutable shard."""

    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    description_db = Path(description_db).resolve()
    state_dir = Path(state_dir).resolve()
    source_schema = _source_schema(description_db)
    embedder = _offline_embedder()
    with _writer_lock(state_dir):
        index = _load_index(state_dir, description_db, embedder)
        with closing(_open_catalog(state_dir)) as catalog:
            _sync_catalog(catalog, state_dir, index)
            jobs, scan, cursor_updates = _select_unseen_jobs(
                catalog, description_db, embedder, batch_size
            )
            summary: dict[str, Any] | None = None
            if jobs:
                summary, key_records = _write_shard(
                    state_dir,
                    description_db,
                    source_schema,
                    jobs,
                    embedder,
                    sequence=len(index["shards"]) + 1,
                )
                index = _publish_index(state_dir, index, summary, embedder, description_db)
                _record_catalog_shard(catalog, index, summary, key_records)
            _write_cursors(catalog, cursor_updates)
            catalog_rows = int(catalog.execute("SELECT count(*) FROM embedding_jobs").fetchone()[0])
            distinct_revisions = int(
                catalog.execute(
                    "SELECT count(*) FROM (SELECT DISTINCT primitive_id,description_digest FROM embedding_jobs)"
                ).fetchone()[0]
            )
            distinct_primitives = int(
                catalog.execute("SELECT count(DISTINCT primitive_id) FROM embedding_jobs").fetchone()[0]
            )

        prior_state_path = state_dir / STATE_FILENAME
        prior_state = json.loads(prior_state_path.read_text(encoding="utf-8")) if prior_state_path.is_file() else {}
        state = {
            "schema": STATE_SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "ticks": int(prior_state.get("ticks", 0)) + 1,
            "coverage_jobs": int(index["coverage_jobs"]),
            "distinct_primitive_revisions": distinct_revisions,
            "distinct_primitives": distinct_primitives,
            "last_selected_jobs": len(jobs),
            "last_shard_id": summary["shard_id"] if summary else None,
            "updated_at": _now(),
            **BOUNDARY,
        }
        _atomic_json(prior_state_path, state)
        receipt = {
            "record_type": TICK_RECORD_TYPE,
            "schema_version": SCHEMA_VERSION,
            "batch_size": int(batch_size),
            "embedded_jobs": len(jobs),
            "deduplicated_by_catalog": int(scan["already_embedded"]),
            "published_shard": summary,
            "scan": scan,
            "stats": {
                "coverage_jobs": int(index["coverage_jobs"]),
                "catalog_rows": catalog_rows,
                "distinct_primitive_revisions": distinct_revisions,
                "distinct_primitives": distinct_primitives,
                "profile_counts": dict(index["profile_counts"]),
                "published_shards": len(index["shards"]),
                "semantic_quality_verified": 0,
                "descriptor_specific_execution_verified": 0,
            },
            "index_manifest": str(state_dir / INDEX_FILENAME),
            "description_db": str(description_db),
            "state_dir": str(state_dir),
            "offline_only": True,
            "verification_note": index["verification_note"],
            **BOUNDARY,
        }
        _append_ledger(state_dir / LEDGER_FILENAME, receipt)
        return receipt


def embedding_stats(
    *,
    description_db: Path = DEFAULT_DESCRIPTION_DB,
    state_dir: Path = DEFAULT_STATE_DIR,
    validate_shards: bool = False,
) -> dict[str, Any]:
    description_db = Path(description_db).resolve()
    state_dir = Path(state_dir).resolve()
    embedder = _offline_embedder()
    if not (state_dir / INDEX_FILENAME).is_file():
        return {
            "record_type": STATS_RECORD_TYPE,
            "coverage_jobs": 0,
            "distinct_primitive_revisions": 0,
            "distinct_primitives": 0,
            "profile_counts": {profile: 0 for profile in EMBEDDING_PROFILES},
            "published_shards": 0,
            "semantic_quality_verified": 0,
            "descriptor_specific_execution_verified": 0,
            "verification_note": _empty_index(description_db, embedder)["verification_note"],
            **BOUNDARY,
        }
    index = _load_index(state_dir, description_db, embedder)
    validated = 0
    if validate_shards:
        for shard in index["shards"]:
            _validate_shard(state_dir / str(shard["directory"]))
            validated += 1
    with closing(_open_catalog(state_dir)) as catalog:
        _sync_catalog(catalog, state_dir, index)
        catalog_rows = int(catalog.execute("SELECT count(*) FROM embedding_jobs").fetchone()[0])
        revisions = int(
            catalog.execute(
                "SELECT count(*) FROM (SELECT DISTINCT primitive_id,description_digest FROM embedding_jobs)"
            ).fetchone()[0]
        )
        primitives = int(catalog.execute("SELECT count(DISTINCT primitive_id) FROM embedding_jobs").fetchone()[0])
    return {
        "record_type": STATS_RECORD_TYPE,
        "coverage_jobs": int(index["coverage_jobs"]),
        "catalog_rows": catalog_rows,
        "distinct_primitive_revisions": revisions,
        "distinct_primitives": primitives,
        "profile_counts": dict(index["profile_counts"]),
        "published_shards": len(index["shards"]),
        "validated_shards": validated if validate_shards else None,
        "model": embedder.model,
        "dimension": embedder.dimension,
        "offline_only": True,
        "semantic_quality_verified": 0,
        "descriptor_specific_execution_verified": 0,
        "verification_note": index["verification_note"],
        "state_dir": str(state_dir),
        "description_db": str(description_db),
        **BOUNDARY,
    }


def score_materialized_candidates(
    query: str,
    primitive_ids: Sequence[str],
    *,
    state_dir: Path = DEFAULT_STATE_DIR,
    profile: str = "envelope",
    max_candidates: int = 512,
) -> dict[str, Any]:
    """Exact-dot rerank a bounded lexical shortlist against materialized description vectors.

    This is deliberately a shortlist reranker, not a claim of a target-scale ANN deployment.  The catalog lookup
    is keyed by primitive id and only touched vector rows are read from memory-mapped immutable shards, so cost
    scales with the candidate set rather than the corpus.  A future DiskANN/HNSW lane can broaden recall without
    changing the immutable embedding key or this evidence boundary.
    """

    if profile not in EMBEDDING_PROFILES:
        raise ValueError(f"unknown embedding profile {profile!r}")
    if max_candidates < 1:
        raise ValueError("max_candidates must be positive")
    ids = list(dict.fromkeys(str(value).strip() for value in primitive_ids if str(value).strip()))
    ids = ids[:max_candidates]
    state_dir = Path(state_dir).resolve()
    index_path = state_dir / INDEX_FILENAME
    catalog_path = state_dir / CATALOG_FILENAME
    empty = {
        "record_type": "primitive_description_embedding_shortlist_rerank",
        "query": str(query),
        "profile": profile,
        "requested_candidates": len(ids),
        "materialized_candidates": 0,
        "vector_rows_scored": 0,
        "scores": {},
        "retrieval_role": "bounded-shortlist-reranker-not-standalone-ann",
        "semantic_quality_verified": 0,
        "descriptor_specific_execution_verified": 0,
        **BOUNDARY,
    }
    if not ids or not str(query).strip() or not index_path.is_file() or not catalog_path.is_file():
        return empty

    index = json.loads(index_path.read_text(encoding="utf-8"))
    shard_dirs = {
        str(shard["shard_id"]): state_dir / str(shard["directory"])
        for shard in index.get("shards", [])
    }
    embedder = _offline_embedder()
    placeholders = ",".join("?" for _ in ids)
    with closing(sqlite3.connect(f"file:{catalog_path}?mode=ro", uri=True)) as catalog:
        catalog.row_factory = sqlite3.Row
        rows = catalog.execute(
            f"""SELECT primitive_id,description_digest,shard_id,shard_row,source_rowid
                FROM embedding_jobs
                WHERE embedding_profile=? AND model=? AND dimension=?
                  AND primitive_id IN ({placeholders})
                ORDER BY primitive_id,source_rowid DESC""",
            (profile, embedder.model, embedder.dimension, *ids),
        ).fetchall()
    latest: dict[str, sqlite3.Row] = {}
    for row in rows:
        latest.setdefault(str(row["primitive_id"]), row)

    query_vector = embedder.encode_many([str(query)])[0]
    by_shard: dict[str, list[sqlite3.Row]] = {}
    for row in latest.values():
        by_shard.setdefault(str(row["shard_id"]), []).append(row)
    scores: dict[str, float] = {}
    vector_rows_scored = 0
    for shard_id, shard_rows in by_shard.items():
        shard_dir = shard_dirs.get(shard_id)
        if shard_dir is None:
            continue
        matrix = np.load(shard_dir / VECTORS_FILENAME, mmap_mode="r", allow_pickle=False)
        indexes = np.asarray([int(row["shard_row"]) for row in shard_rows], dtype=np.int64)
        if indexes.size and (int(indexes.min()) < 0 or int(indexes.max()) >= int(matrix.shape[0])):
            raise ValueError(f"embedding catalog row out of range for {shard_id}")
        shard_vectors = np.asarray(matrix[indexes], dtype="float32")
        similarities = shard_vectors @ query_vector
        vector_rows_scored += len(shard_rows)
        for row, similarity in zip(shard_rows, similarities, strict=True):
            scores[str(row["primitive_id"])] = round(float(similarity), 8)
    return {
        **empty,
        "materialized_candidates": len(scores),
        "vector_rows_scored": vector_rows_scored,
        "scores": scores,
        "model": embedder.model,
        "dimension": embedder.dimension,
    }


def _create_fixture_sidecar(path: Path) -> tuple[str, str, dict[str, Any]]:
    primitive_id = "fixture_webhook_verifier"
    old_surface = {
        "plain": "Verify a signed webhook request before routing it.",
        "technical": "SignedWebhookRequest to WebhookValidationReceipt using HMAC SHA256.",
        "semantic": "Use before parsing; do not use for unsigned polling responses.",
        "envelope": {
            "does": ["Verifies a webhook signature."],
            "use_when": ["A shared-secret signature is present."],
            "not_when": ["The request is unsigned."],
            "fails_when": ["The signature is missing or invalid."],
            "composes_with": ["Event parsing and routing."],
        },
    }
    old_digest = _digest(old_surface)
    connection = sqlite3.connect(str(path))
    connection.executescript(
        """
        CREATE TABLE description_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        INSERT INTO description_meta(key,value) VALUES('schema_version','1');
        CREATE TABLE current_descriptions(
            primitive_id TEXT PRIMARY KEY,
            description_digest TEXT NOT NULL,
            source_surface_digest TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            pool TEXT NOT NULL,
            title TEXT NOT NULL,
            blackbox TEXT NOT NULL,
            input_edge TEXT NOT NULL,
            output_edge TEXT NOT NULL,
            tags TEXT NOT NULL,
            plain TEXT NOT NULL,
            technical TEXT NOT NULL,
            semantic TEXT NOT NULL,
            semantic_envelope_json TEXT NOT NULL,
            provenance_json TEXT NOT NULL,
            quality_verdict TEXT NOT NULL,
            quality_flags_json TEXT NOT NULL,
            capability_verification_level TEXT NOT NULL,
            source_path TEXT NOT NULL,
            source_line INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            candidate INTEGER NOT NULL CHECK(candidate=1),
            serves_truth INTEGER NOT NULL CHECK(serves_truth=0)
        );
        """
    )
    connection.execute(
        """INSERT INTO current_descriptions VALUES(
               ?,?,'source-old','fixture-policy','fixture_pool','verify webhook','Verify an HMAC webhook.',
               'SignedWebhookRequest','WebhookValidationReceipt','webhook hmac',?,?,?,?,
               '{}','pass','[]','candidate','fixture.jsonl',1,?,1,0
           )""",
        (
            primitive_id,
            old_digest,
            old_surface["plain"],
            old_surface["technical"],
            old_surface["semantic"],
            _canonical_json(old_surface["envelope"]),
            _now(),
        ),
    )
    connection.commit()
    connection.close()
    return primitive_id, old_digest, old_surface


def _revise_fixture_sidecar(path: Path, primitive_id: str) -> tuple[str, dict[str, Any]]:
    new_surface = {
        "plain": "Verify a timestamped signed webhook request and reject replay before routing it.",
        "technical": (
            "TimestampedSignedWebhookRequest to WebhookValidationReceipt using HMAC SHA256 and a replay window."
        ),
        "semantic": "Use before parsing; reject stale timestamps and duplicate delivery identifiers.",
        "envelope": {
            "does": ["Verifies signature freshness and replay safety."],
            "use_when": ["A shared-secret signature and delivery timestamp are present."],
            "not_when": ["The integration uses asymmetric signatures."],
            "fails_when": ["The timestamp is stale, replayed, or the signature is invalid."],
            "composes_with": ["Idempotent event parsing and routing."],
        },
    }
    new_digest = _digest(new_surface)
    connection = sqlite3.connect(str(path))
    connection.execute(
        """UPDATE current_descriptions SET
               description_digest=?,source_surface_digest='source-new',plain=?,technical=?,semantic=?,
               semantic_envelope_json=?,blackbox='Verify HMAC freshness and replay safety.',created_at=?
           WHERE primitive_id=?""",
        (
            new_digest,
            new_surface["plain"],
            new_surface["technical"],
            new_surface["semantic"],
            _canonical_json(new_surface["envelope"]),
            _now(),
            primitive_id,
        ),
    )
    connection.commit()
    connection.close()
    return new_digest, new_surface


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, detail: Any = "") -> None:
        checks.append((name, bool(condition), str(detail)))

    parity_texts = ["signed webhook hmac", "", "semantic composition typed edges"]
    vectorized = _offline_embedder().encode_many(parity_texts)
    reference = np.asarray([_embedding.embed_tokens(text) for text in parity_texts], dtype="float32")
    check(
        "vectorized bulk encoder is exactly compatible with the canonical token embedder",
        bool(np.allclose(vectorized, reference, rtol=0.0, atol=1e-7)),
        float(np.max(np.abs(vectorized - reference))),
    )

    with tempfile.TemporaryDirectory(prefix="primitive_description_embedding_") as temp_dir:
        root = Path(temp_dir)
        description_db = root / "descriptions.db"
        state_dir = root / "embedding-state"
        primitive_id, old_digest, old_surface = _create_fixture_sidecar(description_db)

        first = run_tick(description_db=description_db, state_dir=state_dir, batch_size=4)
        check("first revision creates four profile jobs", first["embedded_jobs"] == 4, first)
        check("all requested profiles are present", first["stats"]["profile_counts"] == {p: 1 for p in EMBEDDING_PROFILES}, first)
        check("first tick publishes exactly one immutable shard", first["stats"]["published_shards"] == 1, first)

        duplicate = run_tick(description_db=description_db, state_dir=state_dir, batch_size=4)
        check("unchanged description dedupes", duplicate["embedded_jobs"] == 0, duplicate)
        check("dedupe does not publish a shard", duplicate["stats"]["published_shards"] == 1, duplicate)

        first_index = json.loads((state_dir / INDEX_FILENAME).read_text(encoding="utf-8"))
        old_shard_dir = state_dir / first_index["shards"][0]["directory"]
        old_text_rows = list(_read_jsonl(old_shard_dir / SOURCE_TEXTS_FILENAME))
        check(
            "old shard preserves exact embedded surfaces",
            {row["embedding_profile"] for row in old_text_rows} == set(EMBEDDING_PROFILES)
            and any(row["text"] == old_surface["plain"] for row in old_text_rows),
            old_text_rows,
        )

        new_digest, _new_surface = _revise_fixture_sidecar(description_db, primitive_id)
        revised = run_tick(description_db=description_db, state_dir=state_dir, batch_size=4)
        check("revised description creates four new jobs", revised["embedded_jobs"] == 4, revised)
        check("revision publishes a second immutable shard", revised["stats"]["published_shards"] == 2, revised)
        check("old and new revisions remain counted", revised["stats"]["distinct_primitive_revisions"] == 2, revised)

        revised_duplicate = run_tick(description_db=description_db, state_dir=state_dir, batch_size=4)
        check("revised description also dedupes after first embed", revised_duplicate["embedded_jobs"] == 0, revised_duplicate)
        check("one primitive has eight immutable revision-profile keys", revised_duplicate["stats"]["catalog_rows"] == 8, revised_duplicate)

        catchup = run_until_current(
            description_db=description_db,
            state_dir=state_dir,
            batch_size=4,
            max_ticks=2,
        )
        check(
            "catch-up supervisor exits on the first zero-work tick",
            catchup["caught_up"] and catchup["ticks"] == 1 and catchup["embedded_jobs"] == 0,
            catchup,
        )

        with closing(_open_catalog(state_dir)) as catalog:
            digests = {
                str(row[0])
                for row in catalog.execute(
                    "SELECT DISTINCT description_digest FROM embedding_jobs WHERE primitive_id=?", (primitive_id,)
                )
            }
        check("catalog retains old and new description keys", digests == {old_digest, new_digest}, digests)
        check("old published shard remains readable after revision", old_shard_dir.is_dir(), old_shard_dir)

        reranked = score_materialized_candidates(
            "timestamped signed webhook HMAC replay",
            [primitive_id, "missing-primitive"],
            state_dir=state_dir,
            profile="envelope",
        )
        check(
            "materialized vectors rerank a bounded shortlist without scanning the corpus",
            reranked["materialized_candidates"] == 1
            and reranked["vector_rows_scored"] == 1
            and primitive_id in reranked["scores"]
            and reranked["retrieval_role"] == "bounded-shortlist-reranker-not-standalone-ann",
            reranked,
        )

        stats = embedding_stats(
            description_db=description_db, state_dir=state_dir, validate_shards=True
        )
        check("all shard and per-column manifests validate", stats["validated_shards"] == 2, stats)
        check(
            "embedding never claims semantic or execution proof",
            stats["semantic_quality_verified"] == 0
            and stats["descriptor_specific_execution_verified"] == 0,
            stats,
        )
        check("candidate-only boundary is preserved", stats["candidate"] and not stats["serves_truth"], stats)

    failed = [name for name, ok, _detail in checks if not ok]
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}" + (f": {detail}" if not ok else ""))
    print(json.dumps({"checks": len(checks), "passed": len(checks) - len(failed), "failed": failed}))
    return 1 if failed else 0


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def run_until_current(
    *,
    description_db: Path = DEFAULT_DESCRIPTION_DB,
    state_dir: Path = DEFAULT_STATE_DIR,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_ticks: int | None = None,
) -> dict[str, Any]:
    """Run bounded immutable-shard ticks until one tick finds no unseen revision/profile job."""

    if max_ticks is not None and max_ticks < 1:
        raise ValueError("max_ticks must be positive when provided")
    ticks = 0
    embedded_jobs = 0
    last: dict[str, Any] | None = None
    while max_ticks is None or ticks < max_ticks:
        last = run_tick(
            description_db=description_db,
            state_dir=state_dir,
            batch_size=batch_size,
        )
        ticks += 1
        embedded_jobs += int(last["embedded_jobs"])
        if int(last["embedded_jobs"]) == 0:
            break
    final = embedding_stats(description_db=description_db, state_dir=state_dir)
    return {
        "record_type": "primitive_description_embedding_catchup",
        "ticks": ticks,
        "embedded_jobs": embedded_jobs,
        "caught_up": bool(last is not None and int(last["embedded_jobs"]) == 0),
        "max_ticks": max_ticks,
        "batch_size": batch_size,
        "stats": final,
        "offline_only": True,
        "target_scale_ann_status": "not_implemented; vectors feed a bounded shortlist reranker",
        **BOUNDARY,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--once", action="store_true", help="run one bounded immutable-shard tick")
    action.add_argument(
        "--until-current",
        action="store_true",
        help="repeat bounded ticks until no unseen description revision/profile job remains",
    )
    action.add_argument("--stats", action="store_true", help="report measured immutable embedding coverage")
    action.add_argument("--self-test", action="store_true", help="run a hermetic revision/dedupe test")
    parser.add_argument("--batch-size", type=_positive_int, default=DEFAULT_BATCH_SIZE, help="maximum profile jobs")
    parser.add_argument("--description-db", type=Path, default=DEFAULT_DESCRIPTION_DB)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument(
        "--max-ticks",
        type=_positive_int,
        default=None,
        help="optional safety bound for --until-current",
    )
    parser.add_argument(
        "--validate-shards",
        action="store_true",
        help="with --stats, hash and geometry-check every published shard",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.stats:
        print(
            json.dumps(
                embedding_stats(
                    description_db=args.description_db,
                    state_dir=args.state_dir,
                    validate_shards=args.validate_shards,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.until_current:
        print(
            json.dumps(
                run_until_current(
                    description_db=args.description_db,
                    state_dir=args.state_dir,
                    batch_size=args.batch_size,
                    max_ticks=args.max_ticks,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    print(
        json.dumps(
            run_tick(
                description_db=args.description_db,
                state_dir=args.state_dir,
                batch_size=args.batch_size,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
