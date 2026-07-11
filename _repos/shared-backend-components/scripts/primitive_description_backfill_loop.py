#!/usr/bin/env python3
"""Versioned, source-grounded description backfill for primitive search.

This module deliberately keeps descriptor revisions separate from immutable primitive identity.  It extracts
descriptions from the rich ``problem_solution_core`` already present in the canonical million compiled-codeblock
payloads, quality-gates the result, stores every revision, and exposes only the current accepted revision through
an FTS5 sidecar.  It never promotes a primitive and never upgrades the primitive's execution/proof status.

The source reader is bounded and resumable per JSONL shard.  Committed prefixes are fingerprinted so a rewritten
source cannot silently continue from a stale byte offset.  Description identity includes the source-surface digest
and policy version; embedding workers can therefore key future work by ``(primitive_id, description_digest,
embedding_profile)`` rather than permanently deduplicating on primitive id alone.

Commands::

    PYTHONPATH=. python3 scripts/primitive_description_backfill_loop.py --once --batch-size 20000
    PYTHONPATH=. python3 scripts/primitive_description_backfill_loop.py --stats
    PYTHONPATH=. python3 scripts/primitive_description_backfill_loop.py --watch --batch-size 20000
    PYTHONPATH=. python3 scripts/primitive_description_backfill_loop.py --self-test

All rows are ``candidate=true`` and ``serves_truth=false``.  A useful description is not evidence that the
described implementation passed a descriptor-specific execution oracle.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_SBC = next((p for p in _HERE.parents if (p / "scripts" / "_repo_paths.py").exists()), _HERE.parents[1])
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import fcntl  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import sqlite3  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from contextlib import contextmanager  # noqa: E402
from dataclasses import asdict, dataclass  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from typing import Any, Iterable, Mapping, Sequence  # noqa: E402

from scripts.primitive_usefulness_gate import evaluate_card  # noqa: E402


BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
POLICY_VERSION = "compiled-source-fields-v1"
SCHEMA_VERSION = "2"
DEFAULT_DB = resource("dist") / "primitive_description_sidecar.db"
DEFAULT_MANIFEST = resource("dist") / "primitive_description_sidecar.manifest.json"
DEFAULT_AUDIT_JSONL = (
    resource("data") / "dev-intel" / "primitive_description_backfill" / "description_revisions.jsonl"
)
COMPILED_ROOT = resource("data") / "dev-intel" / "primitive_codeblocks"
SOURCE_TIERS: tuple[str, ...] = ("codeblock_compile_100k", "codeblock_compile_900k_remaining")
SOURCE_GLOB = "primitive_codeblocks_*.jsonl"
ADDITIONAL_SOURCE_PATHS: tuple[Path, ...] = (
    resource("data") / "dev-intel" / "domain_token_savings" / "template_minted_producer_cards.jsonl",
    resource("data") / "dev-intel" / "domain_token_savings" / "template_minted_producer_cards_v2.jsonl",
    resource("data") / "dev-intel" / "aidevobserver_context_foundry" / "primitive_drafts.jsonl",
    resource("data") / "dev-intel" / "primitive_search_federation" / "searchable_source_union.jsonl",
)
SOURCE_FINGERPRINT_BYTES = 4_096
SOURCE_FINGERPRINT_WINDOWS = 9
DEFAULT_BATCH_SIZE = 20_000
DEFAULT_WATCH_INTERVAL_SECONDS = 2.0
DESCRIPTION_POOL = "compiled_codeblock_candidates"
ACCEPTED_VERDICTS = frozenset({"pass", "weak"})


class SourceMutationError(RuntimeError):
    """A consumed source prefix changed or shrank."""


class ConcurrentSourceStateError(RuntimeError):
    """The durable source cursor changed after this writer read it."""


@dataclass(frozen=True, slots=True)
class DescriptionBundle:
    primitive_id: str
    source_surface_digest: str
    policy_version: str
    description_digest: str
    pool: str
    title: str
    blackbox: str
    input_edge: str
    output_edge: str
    tags: str
    plain: str
    technical: str
    semantic: str
    semantic_envelope: dict[str, Any]
    provenance: dict[str, Any]
    quality_verdict: str
    quality_flags: tuple[str, ...]
    capability_verification_level: str
    source_path: str
    source_line: int
    created_at: str
    candidate: bool = True
    serves_truth: bool = False


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any) -> str:
    return str(value or "").strip()


def _items(value: Any) -> list[str]:
    if isinstance(value, str):
        return [part.strip() for part in re.split(r"[;\n]", value) if part.strip()]
    if isinstance(value, (list, tuple, set)):
        return [_text(item) for item in value if _text(item)]
    return []


def _sentence_join(values: Iterable[Any]) -> str:
    result: list[str] = []
    for value in values:
        text = _text(value)
        if not text:
            continue
        if text[-1] not in ".!?":
            text += "."
        result.append(text)
    return " ".join(result)


def canonical_source_files(root: Path = COMPILED_ROOT) -> tuple[Path, ...]:
    """Return canonical million rows followed by deterministic adapters for the remaining major gap pools."""

    paths: list[Path] = []
    for tier in SOURCE_TIERS:
        paths.extend(sorted((root / tier).glob(SOURCE_GLOB)))
    paths.extend(path for path in ADDITIONAL_SOURCE_PATHS if path.is_file())
    return tuple(path.resolve() for path in paths if path.is_file())


def _edge_value(row: Mapping[str, Any], field: str, contract_field: str) -> str:
    value = _text(row.get(field))
    if value:
        return value
    contract = row.get("contract")
    if isinstance(contract, Mapping):
        return _text(contract.get(contract_field))
    gap = row.get("gap_spec")
    if isinstance(gap, Mapping):
        return _text(gap.get("needed_input_type" if contract_field == "input" else "needed_output_type"))
    return ""


def _source_pool(path: Path) -> str:
    text = str(path)
    if "aidevobserver_context_foundry" in text:
        return "context_foundry_drafts"
    if "primitive_search_federation" in text:
        return "registered_source_union"
    return DESCRIPTION_POOL


def _needs_backfill(row: Mapping[str, Any], source_path: Path) -> bool:
    pool = _source_pool(source_path)
    if pool == "context_foundry_drafts":
        return not _text(row.get("blackbox"))
    if pool == "registered_source_union":
        return not (
            _text(row.get("blackbox"))
            and _edge_value(row, "input_edge", "input")
            and _edge_value(row, "output_edge", "output")
        )
    return True


def _read_origin_row(wrapper: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    origin = wrapper.get("source_origin")
    if not isinstance(origin, Mapping):
        return None, None
    raw_path = origin.get("path")
    raw_line = origin.get("line")
    if not isinstance(raw_path, str):
        return None, None
    path = Path(raw_path)
    path = path if path.is_absolute() else _SBC / path
    try:
        path = path.resolve()
        path.relative_to(_SBC.resolve())
        line_number = int(raw_line)
        if line_number < 1:
            return None, None
        with path.open("rb") as handle:
            raw = next((value for number, value in enumerate(handle, start=1) if number == line_number), None)
        if raw is None:
            return None, None
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return None, None
    if not isinstance(value, Mapping):
        return None, None
    for key in ("payload", "candidate_payload", "primitive", "card"):
        nested = value.get(key)
        if isinstance(nested, Mapping):
            value = nested
            break
    return dict(value), _sha256_bytes(raw.rstrip(b"\r\n"))


def _prepare_source_row(row: Mapping[str, Any], source_path: Path) -> dict[str, Any]:
    prepared = dict(row)
    prepared["_description_pool"] = _source_pool(source_path)
    if prepared["_description_pool"] != "registered_source_union":
        return prepared
    origin, origin_digest = _read_origin_row(row)
    if origin is None:
        return prepared
    identity = _text(row.get("primitive_id") or row.get("id"))
    merged = {**origin, **{key: value for key, value in row.items() if value not in (None, "", [], {})}}
    merged["primitive_id"] = identity
    merged["title"] = _text(row.get("title")) or _text(origin.get("title")) or identity
    merged["_description_pool"] = "registered_source_union"
    merged["_origin_payload_digest"] = origin_digest
    return merged


def deterministic_describe(
    row: Mapping[str, Any],
    *,
    raw_line: bytes,
    source_path: Path,
    source_line: int,
    policy_version: str = POLICY_VERSION,
) -> DescriptionBundle:
    """Extract an evidence-linked description without a model call."""

    primitive_id = _text(row.get("primitive_id") or row.get("id"))
    if not primitive_id:
        raise ValueError("source row has no primitive_id")
    if row.get("serves_truth") is True:
        raise ValueError("truth-serving source rows cannot enter the candidate descriptor sidecar")

    core = row.get("problem_solution_core")
    core = dict(core) if isinstance(core, Mapping) else {}
    title = _text(row.get("title")) or primitive_id
    input_edge = _edge_value(row, "input_edge", "input")
    output_edge = _edge_value(row, "output_edge", "output")
    if not input_edge or not output_edge:
        raise ValueError(f"{primitive_id} lacks typed input/output edges")

    explicit_blackbox = _text(row.get("blackbox"))
    if not core:
        source_label = _text(row.get("source_url") or row.get("source_surface_id") or row.get("source_refs"))
        proofs = _items(row.get("proof_requirements"))
        blockers = _items(row.get("promotion_blockers"))
        gap = row.get("gap_spec") if isinstance(row.get("gap_spec"), Mapping) else {}
        core = {
            "problem": _text(gap.get("reason")) or (
                f"The cataloged source {source_label} exposes this candidate capability but its evidence and "
                "contract still require review."
                if source_label
                else "This candidate capability requires explicit contract and evidence review before promotion."
            ),
            "solution_summary": explicit_blackbox or (
                f"Candidate {title} consumes {input_edge} and emits {output_edge}; declared proof requirements "
                f"are {', '.join(proofs) if proofs else 'not yet complete'}."
            ),
            "fit_when": f"Use when a task requires the declared {input_edge} to {output_edge} transformation.",
            "avoid_when": (
                f"Do not treat it as verified while these blockers remain: {', '.join(blockers)}."
                if blockers else "Do not treat this candidate description as execution verification."
            ),
            "failure_modes": blockers,
            "preconditions": f"Input conforms to {input_edge} and workspace policy permits declared effects.",
            "postconditions": f"Output conforms to {output_edge}; candidate and truth boundaries remain explicit.",
            "composition_notes": f"Compose only where an upstream edge emits {input_edge}.",
        }
    input_description = _text(core.get("input_edge_description")) or f"Accepts {input_edge}."
    output_description = _text(core.get("output_edge_description")) or f"Emits {output_edge}."
    blackbox = explicit_blackbox or _sentence_join(
        (core.get("solution_summary"), core.get("problem"),
         f"It consumes {input_edge} and emits {output_edge}", core.get("preconditions"), core.get("postconditions"))
    )
    plain = _sentence_join(
        (
            f"Problem: {_text(core.get('problem'))}" if core.get("problem") else "",
            f"Solution: {_text(core.get('solution_summary'))}" if core.get("solution_summary") else "",
            core.get("fit_when"),
            core.get("avoid_when"),
        )
    )
    effects = _items(row.get("effects"))
    proof_requirements = _items(row.get("proof_requirements"))
    promotion_blockers = _items(row.get("promotion_blockers"))
    failure_modes = _items(core.get("failure_modes"))
    technical = _sentence_join(
        (
            input_description,
            output_description,
            f"Entrypoint: {_text(row.get('entrypoint'))}" if row.get("entrypoint") else "",
            f"Runtime: {_text(row.get('runtime_framework'))}" if row.get("runtime_framework") else "",
            f"Declared effects: {', '.join(effects)}" if effects else "",
            core.get("preconditions"),
            core.get("postconditions"),
            f"Declared failure modes: {', '.join(failure_modes)}" if failure_modes else "",
        )
    )
    semantic = _sentence_join(
        (
            core.get("fit_when"),
            core.get("avoid_when"),
            core.get("composition_notes"),
            f"Promotion remains blocked by: {', '.join(promotion_blockers)}" if promotion_blockers else "",
            f"Required evidence: {', '.join(proof_requirements)}" if proof_requirements else "",
        )
    )
    envelope = {
        "does": [blackbox],
        "use_when": [_text(core.get("fit_when"))] if core.get("fit_when") else [],
        "not_when": [_text(core.get("avoid_when"))] if core.get("avoid_when") else [],
        "fails_when": failure_modes,
        "composes_with": [_text(core.get("composition_notes"))] if core.get("composition_notes") else [],
        "preconditions": [_text(core.get("preconditions"))] if core.get("preconditions") else [],
        "postconditions": [_text(core.get("postconditions"))] if core.get("postconditions") else [],
        "effects": effects,
        "proof_requirements": proof_requirements,
        "promotion_blockers": promotion_blockers,
        "human_action_core": dict(core.get("human_action_core"))
        if isinstance(core.get("human_action_core"), Mapping)
        else {},
    }
    tag_values: list[str] = []
    for key in ("family", "industry", "region", "language", "runtime_framework", "record_type"):
        if _text(row.get(key)):
            tag_values.append(_text(row.get(key)))
    tag_values.extend(_items(row.get("runtime_targets")))
    tags = " ".join(dict.fromkeys(tag_values))

    quality = evaluate_card(
        {
            "primitive_id": primitive_id,
            "title": title,
            "blackbox": blackbox,
            "input_edge": input_edge,
            "output_edge": output_edge,
        }
    )
    source_digest = _sha256_bytes(raw_line.rstrip(b"\r\n"))
    description_surface = {
        "primitive_id": primitive_id,
        "policy_version": policy_version,
        "title": title,
        "blackbox": blackbox,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "plain": plain,
        "technical": technical,
        "semantic": semantic,
        "semantic_envelope": envelope,
    }
    description_digest = _sha256_json(description_surface)
    evidence_fields = [
        "problem_solution_core.problem",
        "problem_solution_core.solution_summary",
        "problem_solution_core.fit_when",
        "problem_solution_core.avoid_when",
        "problem_solution_core.failure_modes",
        "problem_solution_core.preconditions",
        "problem_solution_core.postconditions",
        "input_edge",
        "output_edge",
        "effects",
        "proof_requirements",
        "promotion_blockers",
    ]
    provenance = {
        "derivation_method": "deterministic_source_field_extraction",
        "generator": "primitive_description_backfill_loop",
        "generator_policy_version": policy_version,
        "generator_model": None,
        "source_surface_digest": source_digest,
        "origin_payload_digest": _text(row.get("_origin_payload_digest")) or None,
        "adapter_pool": _text(row.get("_description_pool")) or DESCRIPTION_POOL,
        "source_path": str(source_path.resolve()),
        "source_line": int(source_line),
        "evidence_fields": evidence_fields,
        "register_status": {
            "plain": "derived_from_source_payload",
            "technical": "derived_from_source_payload",
            "semantic": "derived_from_source_payload",
        },
        "claim_boundary": "description evidence only; does not upgrade capability execution verification",
    }
    capability_verification_level = _text(row.get("verification_level")) or "candidate"
    return DescriptionBundle(
        primitive_id=primitive_id,
        source_surface_digest=source_digest,
        policy_version=policy_version,
        description_digest=description_digest,
        pool=_text(row.get("_description_pool")) or DESCRIPTION_POOL,
        title=title,
        blackbox=blackbox,
        input_edge=input_edge,
        output_edge=output_edge,
        tags=tags,
        plain=plain,
        technical=technical,
        semantic=semantic,
        semantic_envelope=envelope,
        provenance=provenance,
        quality_verdict=_text(quality.get("verdict")) or "placeholder",
        quality_flags=tuple(str(item) for item in quality.get("flags") or ()),
        capability_verification_level=capability_verification_level,
        source_path=str(source_path.resolve()),
        source_line=int(source_line),
        created_at=_now(),
    )


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), timeout=60)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA busy_timeout=60000")
    _create_schema(con)
    return con


def _connect_readonly(path: Path) -> sqlite3.Connection:
    """Open an existing sidecar without running schema DDL or changing metadata."""

    resolved = Path(path).resolve()
    con = sqlite3.connect(f"file:{resolved}?mode=ro", uri=True, timeout=60)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    con.execute("PRAGMA busy_timeout=60000")
    return con


def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _create_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS description_meta(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS source_state(
            source_path TEXT PRIMARY KEY,
            byte_offset INTEGER NOT NULL,
            line_number INTEGER NOT NULL,
            head_span INTEGER NOT NULL,
            head_sha256 TEXT NOT NULL,
            tail_start INTEGER NOT NULL,
            tail_span INTEGER NOT NULL,
            tail_sha256 TEXT NOT NULL,
            sample_fingerprints_json TEXT NOT NULL DEFAULT '[]',
            policy_version TEXT NOT NULL DEFAULT '',
            source_size_at_commit INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT '',
            complete INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS source_row_outcomes(
            source_path TEXT NOT NULL,
            source_line INTEGER NOT NULL,
            source_surface_digest TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            status TEXT NOT NULL,
            retryable INTEGER NOT NULL CHECK(retryable IN (0,1)),
            error_class TEXT,
            error_message TEXT,
            attempts INTEGER NOT NULL,
            first_seen_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            candidate INTEGER NOT NULL CHECK(candidate=1),
            serves_truth INTEGER NOT NULL CHECK(serves_truth=0),
            PRIMARY KEY(source_path,source_line,source_surface_digest,policy_version)
        );
        CREATE TABLE IF NOT EXISTS source_events(
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            status TEXT NOT NULL,
            byte_offset INTEGER NOT NULL,
            line_number INTEGER NOT NULL,
            error_class TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL,
            candidate INTEGER NOT NULL CHECK(candidate=1),
            serves_truth INTEGER NOT NULL CHECK(serves_truth=0)
        );
        CREATE TABLE IF NOT EXISTS description_jobs(
            primitive_id TEXT NOT NULL,
            source_surface_digest TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            status TEXT NOT NULL,
            attempts INTEGER NOT NULL,
            last_error TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(primitive_id, source_surface_digest, policy_version)
        );
        CREATE TABLE IF NOT EXISTS description_versions(
            primitive_id TEXT NOT NULL,
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
            serves_truth INTEGER NOT NULL CHECK(serves_truth=0),
            PRIMARY KEY(primitive_id, description_digest)
        );
        CREATE TABLE IF NOT EXISTS current_descriptions(
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
        CREATE VIRTUAL TABLE IF NOT EXISTS current_descriptions_fts USING fts5(
            title, blackbox, tags, input_edge, output_edge, plain, technical, semantic,
            semantic_envelope_json,
            content='current_descriptions', content_rowid='rowid', tokenize='unicode61'
        );
        CREATE TRIGGER IF NOT EXISTS current_descriptions_ai AFTER INSERT ON current_descriptions BEGIN
            INSERT INTO current_descriptions_fts(
                rowid,title,blackbox,tags,input_edge,output_edge,plain,technical,semantic,semantic_envelope_json
            ) VALUES (
                new.rowid,new.title,new.blackbox,new.tags,new.input_edge,new.output_edge,
                new.plain,new.technical,new.semantic,new.semantic_envelope_json
            );
        END;
        CREATE TRIGGER IF NOT EXISTS current_descriptions_ad AFTER DELETE ON current_descriptions BEGIN
            INSERT INTO current_descriptions_fts(
                current_descriptions_fts,rowid,title,blackbox,tags,input_edge,output_edge,
                plain,technical,semantic,semantic_envelope_json
            ) VALUES (
                'delete',old.rowid,old.title,old.blackbox,old.tags,old.input_edge,old.output_edge,
                old.plain,old.technical,old.semantic,old.semantic_envelope_json
            );
        END;
        CREATE TRIGGER IF NOT EXISTS current_descriptions_au AFTER UPDATE ON current_descriptions BEGIN
            INSERT INTO current_descriptions_fts(
                current_descriptions_fts,rowid,title,blackbox,tags,input_edge,output_edge,
                plain,technical,semantic,semantic_envelope_json
            ) VALUES (
                'delete',old.rowid,old.title,old.blackbox,old.tags,old.input_edge,old.output_edge,
                old.plain,old.technical,old.semantic,old.semantic_envelope_json
            );
            INSERT INTO current_descriptions_fts(
                rowid,title,blackbox,tags,input_edge,output_edge,plain,technical,semantic,semantic_envelope_json
            ) VALUES (
                new.rowid,new.title,new.blackbox,new.tags,new.input_edge,new.output_edge,
                new.plain,new.technical,new.semantic,new.semantic_envelope_json
            );
        END;
        """
    )
    # Schema v1 sidecars are migrated in place.  The live legacy process is never touched by this module reload;
    # the migration occurs only when a later invocation opens the database under the single-writer lock.
    source_columns = {str(row[1]) for row in con.execute("PRAGMA table_info(source_state)")}
    migrations = {
        "sample_fingerprints_json": "TEXT NOT NULL DEFAULT '[]'",
        "policy_version": "TEXT NOT NULL DEFAULT ''",
        "source_size_at_commit": "INTEGER NOT NULL DEFAULT 0",
        "updated_at": "TEXT NOT NULL DEFAULT ''",
    }
    for column, declaration in migrations.items():
        if column not in source_columns:
            con.execute(f"ALTER TABLE source_state ADD COLUMN {column} {declaration}")
    current = con.execute("SELECT value FROM description_meta WHERE key='schema_version'").fetchone()
    if current is not None and str(current["value"]) not in {"1", SCHEMA_VERSION}:
        raise RuntimeError(f"unsupported description sidecar schema {current['value']!r}")
    if current is not None and str(current["value"]) == "1":
        # Schema v1 was emitted only by the policy label above.  Preserve its cursor without causing an
        # artificial million-row revision; later real policy-label changes still reset and reprocess it.
        con.execute(
            "UPDATE source_state SET policy_version=?,source_size_at_commit=byte_offset "
            "WHERE policy_version=''",
            (POLICY_VERSION,),
        )
    # A legacy writer that was already in flight during the v1 -> v2 migration can append additional
    # source-state rows after the schema marker changes; SQLite supplies the new columns' defaults for those
    # rows.  Empty policy + zero size + empty update time is therefore an unambiguous legacy-state marker, not
    # a real policy change.  Normalize it on every writer open so resume never reprocesses a same-policy shard.
    con.execute(
        """UPDATE source_state
           SET policy_version=?,source_size_at_commit=byte_offset,updated_at=?
           WHERE policy_version='' AND source_size_at_commit=0 AND updated_at=''""",
        (POLICY_VERSION, _now()),
    )
    con.execute(
        "INSERT INTO description_meta(key,value) VALUES('schema_version',?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (SCHEMA_VERSION,),
    )
    con.commit()


_DESCRIPTION_COLUMNS = (
    "primitive_id",
    "description_digest",
    "source_surface_digest",
    "policy_version",
    "pool",
    "title",
    "blackbox",
    "input_edge",
    "output_edge",
    "tags",
    "plain",
    "technical",
    "semantic",
    "semantic_envelope_json",
    "provenance_json",
    "quality_verdict",
    "quality_flags_json",
    "capability_verification_level",
    "source_path",
    "source_line",
    "created_at",
    "candidate",
    "serves_truth",
)


def _bundle_values(bundle: DescriptionBundle) -> tuple[Any, ...]:
    row = asdict(bundle)
    row["semantic_envelope_json"] = _canonical_json(row.pop("semantic_envelope"))
    row["provenance_json"] = _canonical_json(row.pop("provenance"))
    row["quality_flags_json"] = _canonical_json(row.pop("quality_flags"))
    row["candidate"] = 1
    row["serves_truth"] = 0
    return tuple(row[column] for column in _DESCRIPTION_COLUMNS)


def _commit_bundle(con: sqlite3.Connection, bundle: DescriptionBundle) -> str:
    """Persist a revision and, when accepted, make it the searchable current view."""

    values = _bundle_values(bundle)
    placeholders = ",".join("?" for _ in _DESCRIPTION_COLUMNS)
    inserted = con.execute(
        f"INSERT OR IGNORE INTO description_versions({','.join(_DESCRIPTION_COLUMNS)}) "
        f"VALUES({placeholders})",
        values,
    ).rowcount
    con.execute(
        """INSERT INTO description_jobs(
               primitive_id,source_surface_digest,policy_version,status,attempts,last_error,updated_at
           ) VALUES(?,?,?,?,1,NULL,?)
           ON CONFLICT(primitive_id,source_surface_digest,policy_version) DO UPDATE SET
               status=excluded.status, attempts=description_jobs.attempts+1,
               last_error=NULL, updated_at=excluded.updated_at""",
        (
            bundle.primitive_id,
            bundle.source_surface_digest,
            bundle.policy_version,
            "accepted" if bundle.quality_verdict in ACCEPTED_VERDICTS else "quality_rejected",
            bundle.created_at,
        ),
    )
    if bundle.quality_verdict not in ACCEPTED_VERDICTS:
        return "quality_rejected" if inserted else "duplicate_rejected"

    existing = con.execute(
        "SELECT description_digest FROM current_descriptions WHERE primitive_id=?",
        (bundle.primitive_id,),
    ).fetchone()
    if existing is not None and existing["description_digest"] == bundle.description_digest:
        return "duplicate" if not inserted else "version_inserted"
    assignments = ",".join(
        f"{column}=excluded.{column}" for column in _DESCRIPTION_COLUMNS if column != "primitive_id"
    )
    con.execute(
        f"INSERT INTO current_descriptions({','.join(_DESCRIPTION_COLUMNS)}) VALUES({placeholders}) "
        f"ON CONFLICT(primitive_id) DO UPDATE SET {assignments}",
        values,
    )
    return "indexed" if existing is None else "revised"


def _sample_windows(byte_offset: int) -> list[tuple[int, int]]:
    """Return bounded, stratified windows across a committed prefix.

    Validation remains O(number of windows), not O(total corpus).  This is stronger than only checking the
    first and last 4 KiB while remaining explicit that it is a mutation detector, not a cryptographic proof of
    every unsampled byte.
    """

    if byte_offset <= 0:
        return [(0, 0)]
    span = min(byte_offset, SOURCE_FINGERPRINT_BYTES)
    maximum_start = max(0, byte_offset - span)
    if maximum_start == 0:
        return [(0, span)]
    starts = {
        round(maximum_start * index / (SOURCE_FINGERPRINT_WINDOWS - 1))
        for index in range(SOURCE_FINGERPRINT_WINDOWS)
    }
    return [(int(start), span) for start in sorted(starts)]


def _fingerprint_at(handle, byte_offset: int) -> dict[str, Any]:
    saved = handle.tell()
    head_span = min(byte_offset, SOURCE_FINGERPRINT_BYTES)
    tail_start = max(0, byte_offset - SOURCE_FINGERPRINT_BYTES)
    tail_span = byte_offset - tail_start
    handle.seek(0)
    head = handle.read(head_span)
    handle.seek(tail_start)
    tail = handle.read(tail_span)
    samples: list[dict[str, Any]] = []
    for start, span in _sample_windows(byte_offset):
        handle.seek(start)
        payload = handle.read(span)
        samples.append({"start": start, "span": span, "sha256": _sha256_bytes(payload)})
    handle.seek(saved)
    return {
        "head_span": head_span,
        "head_sha256": _sha256_bytes(head),
        "tail_start": tail_start,
        "tail_span": tail_span,
        "tail_sha256": _sha256_bytes(tail),
        "sample_fingerprints_json": _canonical_json(samples),
    }


def _validate_prefix(handle, source_path: Path, state: sqlite3.Row | None) -> None:
    if state is None:
        return
    offset = int(state["byte_offset"])
    if os.fstat(handle.fileno()).st_size < offset:
        raise SourceMutationError(f"source shrank below committed offset {offset}: {source_path}")
    saved = handle.tell()
    handle.seek(0)
    head = handle.read(int(state["head_span"]))
    handle.seek(int(state["tail_start"]))
    tail = handle.read(int(state["tail_span"]))
    handle.seek(saved)
    if _sha256_bytes(head) != state["head_sha256"] or _sha256_bytes(tail) != state["tail_sha256"]:
        raise SourceMutationError(f"committed source prefix changed: {source_path}")
    raw_samples = state["sample_fingerprints_json"] if "sample_fingerprints_json" in state.keys() else "[]"
    try:
        samples = json.loads(str(raw_samples or "[]"))
    except json.JSONDecodeError as exc:
        raise SourceMutationError(f"invalid durable source fingerprint metadata: {source_path}") from exc
    if not isinstance(samples, list):
        raise SourceMutationError(f"invalid durable source fingerprint shape: {source_path}")
    for sample in samples:
        if not isinstance(sample, Mapping):
            raise SourceMutationError(f"invalid durable source fingerprint entry: {source_path}")
        start = int(sample.get("start", -1))
        span = int(sample.get("span", -1))
        expected = _text(sample.get("sha256"))
        if start < 0 or span < 0 or start + span > offset or not expected:
            raise SourceMutationError(f"invalid durable source fingerprint bounds: {source_path}")
        handle.seek(start)
        payload = handle.read(span)
        if _sha256_bytes(payload) != expected:
            raise SourceMutationError(f"sampled committed source prefix changed at byte {start}: {source_path}")
    handle.seek(saved)


@contextmanager
def _writer_lock(db_path: Path):
    """Serialize cursor readers and writers across processes."""

    lock_path = Path(f"{Path(db_path)}.writer.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _state_identity(state: sqlite3.Row | None) -> tuple[Any, ...] | None:
    if state is None:
        return None
    return (
        int(state["byte_offset"]),
        int(state["line_number"]),
        _text(state["policy_version"]) if "policy_version" in state.keys() else "",
        _text(state["head_sha256"]),
        _text(state["tail_sha256"]),
    )


def _row_outcome(
    *,
    source_path: Path,
    source_line: int,
    raw: bytes,
    policy_version: str,
    status: str,
    retryable: bool,
    error: BaseException | None = None,
) -> dict[str, Any]:
    message = str(error)[:2_000] if error is not None else None
    return {
        "source_path": str(source_path),
        "source_line": int(source_line),
        "source_surface_digest": _sha256_bytes(raw.rstrip(b"\r\n")),
        "policy_version": policy_version,
        "status": status,
        "retryable": int(retryable),
        "error_class": type(error).__name__ if error is not None else None,
        "error_message": message,
        "updated_at": _now(),
    }


def _commit_row_outcome(con: sqlite3.Connection, outcome: Mapping[str, Any]) -> None:
    con.execute(
        """INSERT INTO source_row_outcomes(
               source_path,source_line,source_surface_digest,policy_version,status,retryable,
               error_class,error_message,attempts,first_seen_at,updated_at,candidate,serves_truth
           ) VALUES(?,?,?,?,?,?,?,?,1,?,?,1,0)
           ON CONFLICT(source_path,source_line,source_surface_digest,policy_version) DO UPDATE SET
               status=excluded.status,retryable=excluded.retryable,error_class=excluded.error_class,
               error_message=excluded.error_message,attempts=source_row_outcomes.attempts+1,
               updated_at=excluded.updated_at""",
        (
            outcome["source_path"],
            outcome["source_line"],
            outcome["source_surface_digest"],
            outcome["policy_version"],
            outcome["status"],
            outcome["retryable"],
            outcome["error_class"],
            outcome["error_message"],
            outcome["updated_at"],
            outcome["updated_at"],
        ),
    )


def _record_source_event(
    con: sqlite3.Connection,
    *,
    source_path: Path,
    policy_version: str,
    status: str,
    byte_offset: int,
    line_number: int,
    error: BaseException,
) -> None:
    con.execute(
        """INSERT INTO source_events(
               source_path,policy_version,status,byte_offset,line_number,error_class,error_message,
               created_at,candidate,serves_truth
           ) VALUES(?,?,?,?,?,?,?,?,1,0)""",
        (
            str(source_path),
            policy_version,
            status,
            int(byte_offset),
            int(line_number),
            type(error).__name__,
            str(error)[:2_000],
            _now(),
        ),
    )


def _append_audit(path: Path | None, bundles: Sequence[DescriptionBundle]) -> None:
    if path is None or not bundles:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for bundle in bundles:
            handle.write(_canonical_json({"record_type": "primitive_description_revision", **asdict(bundle)}) + "\n")


def run_tick(
    *,
    db_path: Path = DEFAULT_DB,
    audit_jsonl: Path | None = DEFAULT_AUDIT_JSONL,
    source_files: Sequence[Path] | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    policy_version: str = POLICY_VERSION,
) -> dict[str, Any]:
    """Process at most ``batch_size`` rows and atomically advance each consumed source cursor."""

    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    if not _text(policy_version):
        raise ValueError("policy_version must be non-empty")
    sources = tuple(
        Path(path).resolve()
        for path in (canonical_source_files() if source_files is None else source_files)
    )
    db_path = Path(db_path)
    counters = {
        "source_rows": 0,
        "rows_attempted": 0,
        "indexed": 0,
        "revised": 0,
        "version_inserted": 0,
        "duplicate": 0,
        "quality_rejected": 0,
        "duplicate_rejected": 0,
        "invalid_rows": 0,
        "retryable_errors": 0,
        "source_errors": 0,
        "audit_errors": 0,
        "skipped_already_complete": 0,
        "policy_reprocess_sources": 0,
        "appended_sources_resumed": 0,
    }
    completed_sources = 0
    with _writer_lock(db_path):
        con = _connect(db_path)
        try:
            for source_path in sources:
                if counters["rows_attempted"] >= batch_size:
                    break
                state = con.execute(
                    "SELECT * FROM source_state WHERE source_path=?", (str(source_path),)
                ).fetchone()
                expected_state = _state_identity(state)
                if not source_path.is_file():
                    error = FileNotFoundError(str(source_path))
                    con.execute("BEGIN IMMEDIATE")
                    _record_source_event(
                        con,
                        source_path=source_path,
                        policy_version=policy_version,
                        status="source_error",
                        byte_offset=int(state["byte_offset"]) if state is not None else 0,
                        line_number=int(state["line_number"]) if state is not None else 0,
                        error=error,
                    )
                    con.commit()
                    counters["source_errors"] += 1
                    continue

                with source_path.open("rb") as handle:
                    try:
                        _validate_prefix(handle, source_path, state)
                    except SourceMutationError as exc:
                        con.execute("BEGIN IMMEDIATE")
                        _record_source_event(
                            con,
                            source_path=source_path,
                            policy_version=policy_version,
                            status="source_mutation_rejected",
                            byte_offset=int(state["byte_offset"]) if state is not None else 0,
                            line_number=int(state["line_number"]) if state is not None else 0,
                            error=exc,
                        )
                        con.commit()
                        raise

                    source_size = os.fstat(handle.fileno()).st_size
                    stored_policy = _text(state["policy_version"]) if state is not None else ""
                    policy_changed = state is not None and stored_policy != policy_version
                    prior_offset = int(state["byte_offset"]) if state is not None else 0
                    if policy_changed:
                        counters["policy_reprocess_sources"] += 1
                        offset = 0
                        line_number = 0
                    else:
                        offset = prior_offset
                        line_number = int(state["line_number"]) if state is not None else 0

                    if (
                        state is not None
                        and int(state["complete"])
                        and not policy_changed
                        and source_size == prior_offset
                    ):
                        completed_sources += 1
                        continue
                    if state is not None and int(state["complete"]) and not policy_changed and source_size > prior_offset:
                        counters["appended_sources_resumed"] += 1

                    handle.seek(offset)
                    bundles: list[DescriptionBundle] = []
                    durable_outcomes: list[dict[str, Any]] = []
                    local_attempted = 0
                    invalid = 0
                    retryable = 0
                    skipped = 0
                    committed_offset = offset
                    committed_line = line_number
                    while counters["rows_attempted"] + local_attempted < batch_size:
                        line_start = handle.tell()
                        raw = handle.readline()
                        if not raw:
                            break
                        candidate_line = committed_line + 1
                        local_attempted += 1
                        # A partial final JSONL row is retryable.  Do not advance the cursor until its newline
                        # arrives, otherwise a later append could silently complete a row already discarded.
                        if not raw.endswith((b"\n", b"\r")) and handle.tell() == source_size:
                            error = ValueError("incomplete final JSONL row")
                            durable_outcomes.append(
                                _row_outcome(
                                    source_path=source_path,
                                    source_line=candidate_line,
                                    raw=raw,
                                    policy_version=policy_version,
                                    status="retryable_error",
                                    retryable=True,
                                    error=error,
                                )
                            )
                            retryable += 1
                            handle.seek(line_start)
                            break
                        try:
                            row = json.loads(raw.decode("utf-8", errors="strict"))
                            if not isinstance(row, Mapping):
                                raise TypeError("row is not an object")
                            if not _needs_backfill(row, source_path):
                                skipped += 1
                                durable_outcomes.append(
                                    _row_outcome(
                                        source_path=source_path,
                                        source_line=candidate_line,
                                        raw=raw,
                                        policy_version=policy_version,
                                        status="not_missing_description",
                                        retryable=False,
                                    )
                                )
                            else:
                                prepared = _prepare_source_row(row, source_path)
                                bundles.append(
                                    deterministic_describe(
                                        prepared,
                                        raw_line=raw,
                                        source_path=source_path,
                                        source_line=candidate_line,
                                        policy_version=policy_version,
                                    )
                                )
                        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                            invalid += 1
                            durable_outcomes.append(
                                _row_outcome(
                                    source_path=source_path,
                                    source_line=candidate_line,
                                    raw=raw,
                                    policy_version=policy_version,
                                    status="invalid_or_rejected",
                                    retryable=False,
                                    error=exc,
                                )
                            )
                        except Exception as exc:  # keep unexpected implementation/transient errors retryable
                            durable_outcomes.append(
                                _row_outcome(
                                    source_path=source_path,
                                    source_line=candidate_line,
                                    raw=raw,
                                    policy_version=policy_version,
                                    status="retryable_error",
                                    retryable=True,
                                    error=exc,
                                )
                            )
                            retryable += 1
                            handle.seek(line_start)
                            break
                        committed_offset = handle.tell()
                        committed_line = candidate_line

                    complete = committed_offset >= source_size and retryable == 0
                    fingerprint = _fingerprint_at(handle, committed_offset)

                con.execute("BEGIN IMMEDIATE")
                try:
                    current_state = con.execute(
                        "SELECT * FROM source_state WHERE source_path=?", (str(source_path),)
                    ).fetchone()
                    if _state_identity(current_state) != expected_state:
                        raise ConcurrentSourceStateError(
                            f"source cursor changed during tick; refusing regression: {source_path}"
                        )
                    persisted_outcomes: list[str] = []
                    for bundle in bundles:
                        persisted_outcomes.append(_commit_bundle(con, bundle))
                    for outcome in durable_outcomes:
                        _commit_row_outcome(con, outcome)
                    con.execute(
                        """INSERT INTO source_state(
                               source_path,byte_offset,line_number,head_span,head_sha256,
                               tail_start,tail_span,tail_sha256,sample_fingerprints_json,
                               policy_version,source_size_at_commit,updated_at,complete
                           ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                           ON CONFLICT(source_path) DO UPDATE SET
                               byte_offset=excluded.byte_offset,line_number=excluded.line_number,
                               head_span=excluded.head_span,head_sha256=excluded.head_sha256,
                               tail_start=excluded.tail_start,tail_span=excluded.tail_span,
                               tail_sha256=excluded.tail_sha256,
                               sample_fingerprints_json=excluded.sample_fingerprints_json,
                               policy_version=excluded.policy_version,
                               source_size_at_commit=excluded.source_size_at_commit,
                               updated_at=excluded.updated_at,complete=excluded.complete""",
                        (
                            str(source_path),
                            committed_offset,
                            committed_line,
                            fingerprint["head_span"],
                            fingerprint["head_sha256"],
                            fingerprint["tail_start"],
                            fingerprint["tail_span"],
                            fingerprint["tail_sha256"],
                            fingerprint["sample_fingerprints_json"],
                            policy_version,
                            source_size,
                            _now(),
                            int(complete),
                        ),
                    )
                    con.commit()
                except Exception:
                    con.rollback()
                    raise

                try:
                    _append_audit(Path(audit_jsonl) if audit_jsonl is not None else None, bundles)
                except OSError as exc:
                    con.execute("BEGIN IMMEDIATE")
                    _record_source_event(
                        con,
                        source_path=source_path,
                        policy_version=policy_version,
                        status="audit_error",
                        byte_offset=committed_offset,
                        line_number=committed_line,
                        error=exc,
                    )
                    con.commit()
                    counters["audit_errors"] += 1

                consumed = len(bundles) + invalid + skipped
                counters["source_rows"] += consumed
                counters["rows_attempted"] += local_attempted
                counters["invalid_rows"] += invalid
                counters["retryable_errors"] += retryable
                counters["skipped_already_complete"] += skipped
                for outcome in persisted_outcomes:
                    counters[outcome] += 1
                if complete:
                    completed_sources += 1
            stats = description_stats(db_path=db_path, con=con)
        finally:
            con.close()
        manifest_path = db_path.with_suffix(".manifest.json")
        _write_manifest(manifest_path, stats, policy_version=policy_version)
    return {
        "record_type": "primitive_description_backfill_tick",
        "policy_version": policy_version,
        "batch_size": batch_size,
        "source_files_registered": len(sources),
        "source_files_complete": completed_sources,
        "counters": counters,
        "stats": stats,
        "manifest_path": str(manifest_path),
        "audit_jsonl": str(audit_jsonl) if audit_jsonl is not None else None,
        **BOUNDARY,
    }


def _write_manifest(path: Path, stats: Mapping[str, Any], *, policy_version: str = POLICY_VERSION) -> None:
    """Atomically publish the measured sidecar counts consumed by the goal loop and UI."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": SCHEMA_VERSION, "policy_version": policy_version, **dict(stats)}
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def description_stats(*, db_path: Path = DEFAULT_DB, con: sqlite3.Connection | None = None) -> dict[str, Any]:
    if con is None and not Path(db_path).exists():
        return {
            "record_type": "primitive_description_sidecar_stats",
            "current_descriptions": 0,
            "accepted_current_descriptions": 0,
            "description_versions": 0,
            "quality_verdicts": {},
            "durable_row_outcomes": {},
            "durable_retry_attempts": 0,
            "durable_source_events": {},
            "source_grounded": 0,
            "search_indexed": 0,
            **BOUNDARY,
        }
    owned = con is None
    connection = con or _connect_readonly(Path(db_path))
    try:
        current = int(connection.execute("SELECT count(*) FROM current_descriptions").fetchone()[0])
        versions = int(connection.execute("SELECT count(*) FROM description_versions").fetchone()[0])
        verdicts = {
            str(row["quality_verdict"]): int(row["n"])
            for row in connection.execute(
                "SELECT quality_verdict,count(*) AS n FROM current_descriptions GROUP BY quality_verdict"
            )
        }
        sources = int(connection.execute("SELECT count(*) FROM source_state").fetchone()[0])
        complete_sources = int(
            connection.execute("SELECT count(*) FROM source_state WHERE complete=1").fetchone()[0]
        )
        row_outcomes = (
            {
                str(row["status"]): int(row["n"])
                for row in connection.execute(
                    "SELECT status,count(*) AS n FROM source_row_outcomes GROUP BY status"
                )
            }
            if _table_exists(connection, "source_row_outcomes")
            else {}
        )
        retry_attempts = (
            int(
                connection.execute(
                    "SELECT coalesce(sum(attempts),0) FROM source_row_outcomes WHERE retryable=1"
                ).fetchone()[0]
            )
            if _table_exists(connection, "source_row_outcomes")
            else 0
        )
        source_events = (
            {
                str(row["status"]): int(row["n"])
                for row in connection.execute(
                    "SELECT status,count(*) AS n FROM source_events GROUP BY status"
                )
            }
            if _table_exists(connection, "source_events")
            else {}
        )
        return {
            "record_type": "primitive_description_sidecar_stats",
            "current_descriptions": current,
            # Every current row passed ACCEPTED_VERDICTS; this is the count eligible for coverage gates.
            "accepted_current_descriptions": current,
            "description_versions": versions,
            "quality_verdicts": verdicts,
            "usefulness_pass": verdicts.get("pass", 0),
            "durable_row_outcomes": row_outcomes,
            "durable_retry_attempts": retry_attempts,
            "durable_source_events": source_events,
            "source_grounded": current,
            "derived_registers": current * 3,
            "search_indexed": current,
            "source_files_started": sources,
            "source_files_complete": complete_sources,
            "descriptor_specific_execution_verified": 0,
            "verification_note": "description quality is independent of capability execution verification",
            "db_path": str(Path(db_path)),
            **BOUNDARY,
        }
    finally:
        if owned:
            connection.close()


def _fts_query(query: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9_][A-Za-z0-9_.:+/-]*", str(query))
    return " AND ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens[:32])


def search_descriptions(
    query: str,
    *,
    db_path: Path = DEFAULT_DB,
    pool: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search accepted current description revisions; no source payload bodies are returned."""

    if not Path(db_path).exists() or not _fts_query(query):
        return []
    con = _connect_readonly(Path(db_path))
    try:
        sql = """SELECT d.*,bm25(current_descriptions_fts) AS bm25_score
                 FROM current_descriptions_fts
                 JOIN current_descriptions d ON d.rowid=current_descriptions_fts.rowid
                 WHERE current_descriptions_fts MATCH ?"""
        params: list[Any] = [_fts_query(query)]
        if pool:
            sql += " AND d.pool=?"
            params.append(pool)
        sql += " ORDER BY bm25_score LIMIT ?"
        params.append(max(1, int(limit)))
        return [
            {
                "primitive_id": str(row["primitive_id"]),
                "description_digest": str(row["description_digest"]),
                "pool": str(row["pool"]),
                "title": str(row["title"]),
                "blackbox": str(row["blackbox"]),
                "input_edge": str(row["input_edge"]),
                "output_edge": str(row["output_edge"]),
                "tags": str(row["tags"]),
                "quality_verdict": str(row["quality_verdict"]),
                "capability_verification_level": str(row["capability_verification_level"]),
                "score": -float(row["bm25_score"] or 0.0),
                **BOUNDARY,
            }
            for row in con.execute(sql, params)
        ]
    finally:
        con.close()


def get_current_description(
    primitive_id: str, *, db_path: Path = DEFAULT_DB
) -> dict[str, Any] | None:
    if not Path(db_path).exists():
        return None
    con = _connect_readonly(Path(db_path))
    try:
        row = con.execute("SELECT * FROM current_descriptions WHERE primitive_id=?", (primitive_id,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        for source, target in (
            ("semantic_envelope_json", "semantic_envelope"),
            ("provenance_json", "provenance"),
            ("quality_flags_json", "quality_flags"),
        ):
            result[target] = json.loads(result.pop(source))
        result["candidate"] = bool(result["candidate"])
        result["serves_truth"] = bool(result["serves_truth"])
        return result
    finally:
        con.close()


def _fixture_row(index: int) -> dict[str, Any]:
    return {
        "primitive_id": f"fixture_primitive_{index:04d}",
        "record_type": "primitive_codeblock_candidate",
        "title": f"validate webhook event {index}",
        "input_edge": "SignedWebhookRequest",
        "output_edge": "WebhookValidationReceipt",
        "family": "webhook_validation",
        "industry": "horizontal_saas",
        "language": "python",
        "entrypoint": "run(payload, policy=None, context=None)",
        "runtime_framework": "fixture.runtime",
        "effects": ["crypto_verify", "none"],
        "proof_requirements": ["hmac_contract_test", "replay_test"],
        "promotion_blockers": ["descriptor_specific_oracle_missing"],
        "problem_solution_core": {
            "problem": "Webhook receivers must reject tampered event bodies before routing them.",
            "solution_summary": "Verify an HMAC-SHA256 signature over the raw request body and return a typed receipt.",
            "fit_when": "Use when an HTTP webhook includes a shared-secret signature.",
            "avoid_when": "Do not use for unsigned polling responses.",
            "failure_modes": "missing_signature; invalid_signature; stale_timestamp",
            "input_edge_description": "Accepts the raw signed webhook request.",
            "output_edge_description": "Emits a validation receipt without the shared secret.",
            "preconditions": "The signature scheme and secret identity are declared by policy.",
            "postconditions": "The receipt records validation outcome and source digest.",
            "composition_notes": "Compose before event parsing and routing.",
        },
        **BOUNDARY,
    }


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: Any = "") -> None:
        checks.append((name, bool(ok), str(detail)))

    with tempfile.TemporaryDirectory(prefix="primitive_description_backfill_") as temp_dir:
        root = Path(temp_dir)
        source_root = root / "sources"
        source_dir = source_root / SOURCE_TIERS[0]
        source_dir.mkdir(parents=True)
        source = source_dir / "primitive_codeblocks_000000.jsonl"
        rows = [_fixture_row(index) for index in range(12)]
        source.write_text("".join(_canonical_json(row) + "\n" for row in rows), encoding="utf-8")
        db = root / "descriptions.db"
        audit = root / "revisions.jsonl"

        first = run_tick(db_path=db, audit_jsonl=audit, source_files=[source], batch_size=8)
        check("bounded first tick", first["counters"]["source_rows"] == 8, first)
        check("quality gate passes grounded descriptions", first["stats"]["usefulness_pass"] == 8, first)
        second = run_tick(db_path=db, audit_jsonl=audit, source_files=[source], batch_size=8)
        check("resume processes remainder", second["stats"]["current_descriptions"] == 12, second)
        third = run_tick(db_path=db, audit_jsonl=audit, source_files=[source], batch_size=8)
        check("completed source is idempotent", third["counters"]["source_rows"] == 0, third)

        with source.open("a", encoding="utf-8") as handle:
            handle.write(_canonical_json(_fixture_row(12)) + "\n")
        appended = run_tick(db_path=db, audit_jsonl=audit, source_files=[source], batch_size=8)
        check(
            "completed source resumes when bytes are appended",
            appended["counters"]["appended_sources_resumed"] == 1
            and appended["stats"]["current_descriptions"] == 13,
            appended,
        )

        policy_v2 = "fixture-policy-v2"
        reprocessed = run_tick(
            db_path=db,
            audit_jsonl=audit,
            source_files=[source],
            batch_size=100,
            policy_version=policy_v2,
        )
        reprocessed_exact = get_current_description(rows[0]["primitive_id"], db_path=db)
        check(
            "policy change creates revisions without changing primitive identities",
            reprocessed["counters"]["policy_reprocess_sources"] == 1
            and reprocessed["stats"]["current_descriptions"] == 13
            and reprocessed["stats"]["description_versions"] == 26
            and bool(reprocessed_exact and reprocessed_exact["policy_version"] == policy_v2),
            reprocessed,
        )

        with source.open("ab") as handle:
            handle.write(b"{not-json}\n")
        invalid_tick = run_tick(
            db_path=db,
            audit_jsonl=audit,
            source_files=[source],
            batch_size=8,
            policy_version=policy_v2,
        )
        check(
            "invalid rows are durably accounted while the cursor advances",
            invalid_tick["counters"]["invalid_rows"] == 1
            and invalid_tick["stats"]["durable_row_outcomes"].get("invalid_or_rejected") == 1,
            invalid_tick,
        )

        with source.open("ab") as handle:
            handle.write(b"{")
        retry_a = run_tick(
            db_path=db,
            audit_jsonl=audit,
            source_files=[source],
            batch_size=8,
            policy_version=policy_v2,
        )
        retry_b = run_tick(
            db_path=db,
            audit_jsonl=audit,
            source_files=[source],
            batch_size=8,
            policy_version=policy_v2,
        )
        check(
            "incomplete rows retain the cursor and durable retry attempts",
            retry_a["counters"]["retryable_errors"] == 1
            and retry_b["counters"]["retryable_errors"] == 1
            and retry_b["stats"]["durable_retry_attempts"] >= 2,
            retry_b,
        )
        completed_raw = (_canonical_json(_fixture_row(13)) + "\n").encode()
        with source.open("ab") as handle:
            handle.write(completed_raw[1:])
        completed_retry = run_tick(
            db_path=db,
            audit_jsonl=audit,
            source_files=[source],
            batch_size=8,
            policy_version=policy_v2,
        )
        check(
            "a later append can complete and process the retained partial row",
            completed_retry["stats"]["current_descriptions"] == 14,
            completed_retry,
        )

        hits = search_descriptions("HMAC SHA256 signature", db_path=db, limit=3)
        check("description FTS finds source semantics", bool(hits), hits)
        exact = get_current_description(rows[0]["primitive_id"], db_path=db)
        check("exact description keeps provenance", bool(exact and exact["provenance"]["source_line"] == 1), exact)
        check("truth boundary preserved", bool(exact and exact["candidate"] and not exact["serves_truth"]), exact)
        check(
            "three derived registers are counted",
            second["stats"]["derived_registers"] == second["stats"]["current_descriptions"] * 3,
            second["stats"],
        )
        check(
            "execution verification is not inferred",
            second["stats"]["descriptor_specific_execution_verified"] == 0,
            second["stats"],
        )

        context_path = root / "aidevobserver_context_foundry" / "primitive_drafts.jsonl"
        context_row = {
            "primitive_id": "prim:candidate:fixture-descriptor",
            "title": "Fixture dataset descriptor",
            "contract": {"input": "DatasetSource", "output": "DatasetDescriptor"},
            "source_url": "https://example.invalid/catalog",
            "effects": ["net.read"],
            "proof_requirements": ["license_gate", "contract_review"],
            "promotion_blockers": ["source_evidence_required"],
            **BOUNDARY,
        }
        context_raw = (_canonical_json(context_row) + "\n").encode()
        context_bundle = deterministic_describe(
            _prepare_source_row(context_row, context_path),
            raw_line=context_raw,
            source_path=context_path,
            source_line=1,
        )
        check(
            "context-draft adapter renders source-labelled typed descriptions without a model",
            context_bundle.pool == "context_foundry_drafts"
            and context_bundle.quality_verdict == "pass"
            and "DatasetSource" in context_bundle.blackbox,
            context_bundle,
        )

        explicit_row = {
            "primitive_id": "codefactory-fixture",
            "title": "Typed webhook transform stub",
            "blackbox": "A review-only Python function validates a SignedWebhookRequest envelope and emits a WebhookReceipt envelope.",
            "input_edge": "SignedWebhookRequest",
            "output_edge": "WebhookReceipt",
            "proof_requirements": ["contract_test"],
            **BOUNDARY,
        }
        explicit_bundle = deterministic_describe(
            explicit_row,
            raw_line=(_canonical_json(explicit_row) + "\n").encode(),
            source_path=root / "template_minted_producer_cards_v2.jsonl",
            source_line=1,
        )
        check(
            "explicit source blackbox is preserved rather than regenerated",
            explicit_bundle.blackbox == explicit_row["blackbox"] and explicit_bundle.quality_verdict == "pass",
            explicit_bundle,
        )

        mutated = source.read_bytes()
        occurrences = [match.start() for match in re.finditer(b"HMAC-SHA256", mutated)]
        interior = occurrences[len(occurrences) // 2]
        mutated = mutated[:interior] + b"HMAC-SHA512" + mutated[interior + len(b"HMAC-SHA256"):]
        source.write_bytes(mutated)
        try:
            run_tick(
                db_path=db,
                audit_jsonl=audit,
                source_files=[source],
                batch_size=1,
                policy_version=policy_v2,
            )
        except SourceMutationError:
            mutation_blocked = True
        else:
            mutation_blocked = False
        check("sampled interior committed-prefix mutation is rejected", mutation_blocked)

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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--once", action="store_true", help="run one bounded backfill tick")
    action.add_argument("--watch", action="store_true", help="continue bounded ticks until sources are complete")
    action.add_argument("--stats", action="store_true", help="print current sidecar coverage")
    action.add_argument("--self-test", action="store_true")
    parser.add_argument("--batch-size", type=_positive_int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--audit-jsonl", type=Path, default=DEFAULT_AUDIT_JSONL)
    parser.add_argument("--no-audit-jsonl", action="store_true")
    parser.add_argument("--interval", type=float, default=DEFAULT_WATCH_INTERVAL_SECONDS)
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.stats:
        print(json.dumps(description_stats(db_path=args.db), indent=2, sort_keys=True))
        return 0
    audit = None if args.no_audit_jsonl else args.audit_jsonl
    if args.once:
        print(json.dumps(run_tick(db_path=args.db, audit_jsonl=audit, batch_size=args.batch_size), indent=2))
        return 0
    while True:
        receipt = run_tick(db_path=args.db, audit_jsonl=audit, batch_size=args.batch_size)
        print(json.dumps(receipt, sort_keys=True), flush=True)
        if (
            receipt["source_files_complete"] >= receipt["source_files_registered"]
            and receipt["counters"]["retryable_errors"] == 0
        ):
            return 0
        time.sleep(max(0.0, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
