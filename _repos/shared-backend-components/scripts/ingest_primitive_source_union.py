#!/usr/bin/env python3
"""Normalize the canonical primitive source union into one append-only search feed.

The input catalogs have intentionally different schemas and trust claims.  This
bridge keeps them read-only, extracts only a compact search card, and always
downgrades the result to ``candidate=true / serves_truth=false``.  Original
truth/proof claims remain provenance fields; ingestion never promotes them.

Each discovered JSONL file has a durable byte-offset checkpoint.  An unchanged
file is not opened, a valid append resumes at the first new complete line, and
a rewritten/truncated snapshot is safely rescanned.  A processed-prefix digest
distinguishes a true append from an in-place rewrite.  The append feed and its
SQLite id catalog are reconciled by durable output size after a crash.

Commands::

    PYTHONPATH=. python3 scripts/ingest_primitive_source_union.py --sync
    PYTHONPATH=. python3 scripts/ingest_primitive_source_union.py --stats
    PYTHONPATH=. python3 scripts/ingest_primitive_source_union.py --self-test
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
import fnmatch  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import sqlite3  # noqa: E402
import tempfile  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from typing import Any, Iterable, Iterator, Mapping, Sequence  # noqa: E402


BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
DEFAULT_OUTPUT = (
    resource("data") / "dev-intel" / "primitive_search_federation" / "searchable_source_union.jsonl"
)
DEFAULT_CATALOG = (
    resource("data") / "dev-intel" / "primitive_search_federation" / "searchable_source_union.sqlite"
)
DEFAULT_RECEIPT = (
    resource("data") / "dev-intel" / "primitive_search_federation" / "source_union_ingest_receipt.json"
)
SCHEMA_VERSION = "1"
MAX_TEXT = 2_000
MAX_EDGE = 1_000
MAX_TAGS = 64
MAX_TAG_LENGTH = 128


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """A dynamically expanded source family."""

    group: str
    pattern: str
    exclude_patterns: tuple[str, ...] = ()
    require_source_id: bool = False


# These are the canonical missing source families from the all-source audit.
# Keep patterns narrow: supporting ledgers, receipts, rejected candidates, full
# code bodies, and benchmark fixtures do not belong in this compact search feed.
SOURCE_SPECS: tuple[SourceSpec, ...] = (
    SourceSpec(
        "factory_verified_candidates",
        "data/dev-intel/primitive_factory/verified_candidates/**/verified_candidates.jsonl",
    ),
    SourceSpec(
        "factory_extracted_candidates",
        "data/dev-intel/primitive_factory/**/extracted/extracted_candidates.jsonl",
        exclude_patterns=(
            "data/dev-intel/primitive_factory/million_seed_compiler_runs/**",
            "data/dev-intel/primitive_factory/20m_goal/**",
        ),
        require_source_id=True,
    ),
    SourceSpec(
        "factory_linkable_cards",
        "data/dev-intel/primitive_factory/linkable_cards/2026-07-01/linkable_primitive_cards.jsonl",
    ),
    SourceSpec("implementation_variants", "data/dev-intel/atlas/implementation_variants.jsonl"),
    SourceSpec(
        "enterprise_operating_system_atlas",
        "catalog/knowledge-packs/data/enterprise-operating-system-primitive-atlas/primitive_candidates.jsonl",
    ),
    SourceSpec(
        "primitive_source_lifecycle",
        "data/dev-intel/primitive_source_lifecycle/primitive_search_cards.jsonl",
    ),
    SourceSpec("parametric_primitives", "data/dev-intel/parametric_primitives/param_*.jsonl"),
    SourceSpec(
        "hy3_flywheel_candidates",
        "data/dev-intel/hy3_overnight_flywheel/flywheel_primitive_candidates.jsonl",
    ),
    SourceSpec(
        "implemented_code_daily_20260702_2k",
        "data/dev-intel/implemented_code_primitives/daily_20260702_2k/implemented_code_primitives.jsonl",
    ),
    SourceSpec(
        "automation_forge_candidates",
        "data/dev-intel/automation_forge/primitive_candidates.jsonl",
        require_source_id=True,
    ),
    SourceSpec(
        "spec_to_executor_cards",
        "data/dev-intel/spec_to_executor_synthesizer/*receipts.jsonl",
        require_source_id=True,
    ),
    SourceSpec(
        "real_world_situation_cards",
        "data/dev-intel/real_world_situation_primitive_specs/situation_synthesis_receipts.jsonl",
        require_source_id=True,
    ),
    SourceSpec(
        "weak_capability_closer_cards",
        "data/dev-intel/weak_capability_primitive_closer/closed_gap_receipts.jsonl",
        require_source_id=True,
    ),
    SourceSpec(
        "specialized_primitive_packs",
        "data/dev-intel/primitive_factory/specialized_packs/*.jsonl",
    ),
    SourceSpec(
        "string_operations",
        "data/dev-intel/string_operations_catalog/string_operation_primitive_candidates.jsonl",
    ),
    SourceSpec(
        "edge_foundry_groups",
        "data/dev-intel/aidevobserver_edge_foundry/curated_primitive_groups.jsonl",
    ),
    SourceSpec(
        "edge_foundry_runtime_shapes",
        "data/dev-intel/aidevobserver_edge_foundry/runtime_shape_primitive_cards.jsonl",
    ),
    SourceSpec(
        "edge_foundry_benchmark_decomposition",
        "data/dev-intel/aidevobserver_edge_foundry/benchmark_decomposition_cards.jsonl",
    ),
    SourceSpec(
        "edge_foundry_kind_families",
        "data/dev-intel/aidevobserver_edge_foundry/primitive_kind_family_cards.jsonl",
    ),
    SourceSpec(
        "edge_foundry_opportunity_intelligence",
        "data/dev-intel/aidevobserver_edge_foundry/opportunity_intelligence_group_candidates.jsonl",
    ),
    SourceSpec("proven_primitives", "data/dev-intel/proven_primitives/proven_*.jsonl"),
    SourceSpec("domain_primitives", "data/dev-intel/domain_primitives/domain_*.jsonl"),
    SourceSpec(
        "cloud_guardrail_primitives",
        "catalog/knowledge-packs/data/primitive-cloud-guardrail-runtime/guardrail_primitives.jsonl",
    ),
    SourceSpec(
        "primitive_chain_catalog",
        "data/dev-intel/primitive_chain_catalog/operation_and_chain_candidates.jsonl",
    ),
    SourceSpec(
        "edge_foundry_executable_packs",
        "data/dev-intel/aidevobserver_edge_foundry/executable_pack_cards.jsonl",
    ),
    SourceSpec(
        "standards_enrichment",
        "data/dev-intel/standards_enrichment_registry/standards_enrichment_candidates.jsonl",
    ),
    SourceSpec(
        "schema_org_foundry",
        "data/dev-intel/schema_org_foundry/schema_org_primitive_candidates.jsonl",
    ),
    SourceSpec(
        "deconstruction_fully_defined",
        "data/dev-intel/primitive_deconstruction_plane_pipeline/runs/*/fully_defined_primitive_candidates.jsonl",
    ),
    SourceSpec(
        "primitive_system_catalog",
        "data/dev-intel/primitive_system_catalog/artifacts/*/primitive_catalog.jsonl",
    ),
    SourceSpec(
        "primitive_system_transformations",
        "data/dev-intel/primitive_system_catalog/artifacts/*/transformation_catalog.jsonl",
    ),
)


_ID_KEYS = (
    "primitive_id",
    "id",
    "card_id",
    "candidate_id",
    "definition_id",
    "group_id",
    "operation_id",
    "chain_id",
    "variant_id",
    "capability_id",
)
_TITLE_KEYS = (
    "title", "name", "stable_name", "slug", "label", "capability", "mutator", "method", "template",
    "operation", "impl_name", "entry", "kind",
)
_BLACKBOX_KEYS = (
    "purpose",
    "description",
    "definition",
    "summary",
    "intent",
    "does",
    "fit_when",
    "capability",
    "what_it_represents",
    "method",
    "mutator",
    "template",
    "operation",
    "label",
    "source_descriptor",
    "docstring",
)
_TAG_KEYS = (
    "capability_tags",
    "tags",
    "domains",
    "domain",
    "family",
    "component_family",
    "kind",
    "category",
    "record_type",
    "runtime_targets",
    "language",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest_json(value: Any) -> str:
    return _digest_bytes(_canonical_json(value).encode("utf-8"))


def _clip(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _first_text(row: Mapping[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
    return ""


def _effective_row(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    """Unwrap feed envelopes without carrying the full source payload forward."""

    payload = raw.get("payload")
    if isinstance(payload, Mapping):
        return payload
    candidate = raw.get("candidate_payload")
    if isinstance(candidate, Mapping):
        return candidate
    primitive = raw.get("primitive")
    if isinstance(primitive, Mapping):
        return primitive
    card = raw.get("card")
    if isinstance(card, Mapping):
        return card
    return raw


def _mapping_text(value: Mapping[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        item = value.get(key)
        if isinstance(item, str) and item.strip():
            return item.strip()
    return ""


def _blackbox(row: Mapping[str, Any]) -> str:
    value = row.get("blackbox")
    if isinstance(value, str) and value.strip():
        return _clip(value, MAX_TEXT)
    if isinstance(value, Mapping):
        text = _mapping_text(value, ("does", "description", "summary", "mechanism", "purpose"))
        if text:
            return _clip(text, MAX_TEXT)
    return _clip(_first_text(row, _BLACKBOX_KEYS), MAX_TEXT)


def _contract_text(value: Any, *, limit: int) -> str:
    if isinstance(value, str):
        return _clip(value, limit)
    if isinstance(value, (list, tuple)):
        return _clip("+".join(str(item).strip() for item in value if str(item).strip()), limit)
    if not isinstance(value, Mapping):
        return ""
    shape = _first_text(value, ("shape", "type", "name"))
    required = value.get("required")
    if isinstance(required, (list, tuple)):
        required_text = "+".join(_clip(item, 80) for item in required if str(item).strip())
    else:
        required_text = ""
    fields = value.get("fields")
    if not required_text and isinstance(fields, Mapping):
        required_text = "+".join(_clip(item, 80) for item in list(fields)[:16])
    text = "+".join(part for part in (shape, required_text) if part)
    return _clip(text or _canonical_json(value), limit)


def _edge(row: Mapping[str, Any], *, direction: str) -> str:
    edge_key = f"{direction}_edge"
    contract_key = f"{direction}_contract"
    for key in (edge_key, f"{direction}_edge_type_id", f"{direction}_type", f"{direction}_types",
                f"{direction}_ports"):
        value = row.get(key)
        if value not in (None, "", [], {}):
            return _contract_text(value, limit=MAX_EDGE)
    edge_contract = row.get("edge_contract")
    if isinstance(edge_contract, Mapping):
        value = edge_contract.get(f"visible_{edge_key}") or edge_contract.get(edge_key)
        if value not in (None, ""):
            return _contract_text(value, limit=MAX_EDGE)
    contract = row.get("contract")
    if isinstance(contract, Mapping):
        for key in (contract_key, f"{direction}_type", direction):
            if contract.get(key) not in (None, "", [], {}):
                return _contract_text(contract.get(key), limit=MAX_EDGE)
    return _contract_text(row.get(contract_key), limit=MAX_EDGE)


def _flatten_tags(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        if value.strip():
            yield value.strip()
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(item, (str, int, float)) and not isinstance(item, bool):
                yield f"{key}:{item}"
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            if isinstance(item, (str, int, float)) and not isinstance(item, bool) and str(item).strip():
                yield str(item).strip()


def _tags(row: Mapping[str, Any], group: str) -> list[str]:
    values = [group]
    for key in _TAG_KEYS:
        values.extend(_flatten_tags(row.get(key)))
    normalized = sorted({_clip(item, MAX_TAG_LENGTH) for item in values if str(item).strip()})
    return normalized[:MAX_TAGS]


def _source_claim(raw: Mapping[str, Any], row: Mapping[str, Any], key: str) -> Any:
    values = [container.get(key) for container in (raw, row) if key in container]
    if key in {"serves_truth", "candidate"}:
        if any(value is True for value in values):
            return True
        if any(value is False for value in values):
            return False
        return None
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _identity_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "primitive_id": row.get("primitive_id"),
        "title": row.get("title"),
        "blackbox": row.get("blackbox"),
        "input_edge": row.get("input_edge"),
        "output_edge": row.get("output_edge"),
    }


def normalize(
    raw: Mapping[str, Any], *, source_group: str, source_path: str, source_line: int,
    require_source_id: bool = False,
) -> dict[str, Any] | None:
    """Return one slim candidate search card, or ``None`` for non-capability rows."""

    row = _effective_row(raw)
    title = _clip(_first_text(row, _TITLE_KEYS), MAX_TEXT)
    blackbox = _blackbox(row)
    input_edge = _edge(row, direction="input")
    output_edge = _edge(row, direction="output")
    claimed_id = _first_text(row, _ID_KEYS) or _first_text(raw, _ID_KEYS)
    if require_source_id and not claimed_id:
        return None
    if not any((claimed_id, title, blackbox, input_edge, output_edge)):
        return None
    if claimed_id:
        primitive_id = _clip(claimed_id, 512)
        id_source = "source"
    else:
        identity_seed = {
            "group": source_group,
            "title": title,
            "blackbox": blackbox,
            "input_edge": input_edge,
            "output_edge": output_edge,
        }
        primitive_id = f"source-union:{source_group}:{_digest_json(identity_seed)[:24]}"
        id_source = "derived_identity"
    title = title or primitive_id
    description_status = "source_described" if blackbox else "title_fallback"
    source_verification = _source_claim(raw, row, "verification_level")
    if source_verification is None:
        source_verification = _source_claim(raw, row, "verification_status")
    source_proof = _source_claim(raw, row, "proof_status")
    if source_proof is None:
        source_proof = _source_claim(raw, row, "proof")
    normalized: dict[str, Any] = {
        "record_type": "primitive_source_union_search_card",
        "primitive_id": primitive_id,
        "title": title,
        "blackbox": blackbox,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "capability_tags": _tags(row, source_group),
        "verification_level": "candidate",
        "proof_status": "unverified",
        "source_candidate": _source_claim(raw, row, "candidate"),
        "source_serves_truth": _source_claim(raw, row, "serves_truth"),
        "source_verification_level": _clip(source_verification, 256) if source_verification is not None else None,
        "source_proof_status": _clip(source_proof, 512) if source_proof is not None else None,
        "source_group": source_group,
        "source_origin": {"path": source_path, "line": source_line},
        "source_primitive_id": claimed_id or None,
        "primitive_id_source": id_source,
        "source_payload_digest": _digest_json(raw),
        "description_status": description_status,
        **BOUNDARY,
    }
    normalized["identity_digest"] = _digest_json(_identity_fields(normalized))
    return normalized


def discover_sources(
    root: Path = _SBC, specs: Sequence[SourceSpec] = SOURCE_SPECS
) -> list[tuple[SourceSpec, Path]]:
    """Expand all source globs deterministically, assigning a file to its first matching family."""

    discovered: dict[str, tuple[SourceSpec, Path]] = {}
    for spec in specs:
        for path in sorted(root.glob(spec.pattern)):
            if path.is_file():
                relative = _relative(path, root)
                if any(fnmatch.fnmatchcase(relative, pattern) for pattern in spec.exclude_patterns):
                    continue
                key = str(path.resolve())
                discovered.setdefault(key, (spec, path.resolve()))
    return [discovered[key] for key in sorted(discovered)]


def _create_catalog(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS ids(
            primitive_id TEXT PRIMARY KEY,
            identity_digest TEXT NOT NULL,
            payload_digest TEXT NOT NULL,
            origin_path TEXT NOT NULL,
            origin_line INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS source_checkpoints(
            source_path TEXT PRIMARY KEY,
            source_group TEXT NOT NULL,
            offset INTEGER NOT NULL,
            line_no INTEGER NOT NULL,
            observed_size INTEGER NOT NULL,
            observed_mtime_ns INTEGER NOT NULL,
            observed_inode INTEGER NOT NULL,
            prefix_digest TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS identity_conflicts(
            primitive_id TEXT NOT NULL,
            first_identity_digest TEXT NOT NULL,
            observed_identity_digest TEXT NOT NULL,
            origin_path TEXT NOT NULL,
            origin_line INTEGER NOT NULL,
            first_seen_at TEXT NOT NULL,
            PRIMARY KEY(primitive_id, observed_identity_digest)
        );
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """
    )
    con.execute("INSERT OR IGNORE INTO meta VALUES('schema_version', ?)", (SCHEMA_VERSION,))
    con.commit()


def _iter_output(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file():
        return
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield row


def _rebuild_ids(con: sqlite3.Connection, output: Path, *, clear_checkpoints: bool) -> int:
    con.execute("DELETE FROM ids")
    if clear_checkpoints:
        con.execute("DELETE FROM source_checkpoints")
    count = 0
    for row in _iter_output(output):
        primitive_id = str(row.get("primitive_id") or "").strip()
        if not primitive_id:
            continue
        identity_digest = str(row.get("identity_digest") or _digest_json(_identity_fields(row)))
        origin = row.get("source_origin") if isinstance(row.get("source_origin"), Mapping) else {}
        cursor = con.execute(
            "INSERT OR IGNORE INTO ids VALUES(?,?,?,?,?)",
            (
                primitive_id,
                identity_digest,
                _digest_json(row),
                str(origin.get("path") or "reconciled_output"),
                int(origin.get("line") or 0),
            ),
        )
        count += int(cursor.rowcount > 0)
    size = output.stat().st_size if output.exists() else 0
    con.execute("INSERT OR REPLACE INTO meta VALUES('output_size', ?)", (str(size),))
    con.commit()
    return count


def _ensure_catalog(con: sqlite3.Connection, output: Path) -> tuple[int, bool]:
    _create_catalog(con)
    row = con.execute("SELECT value FROM meta WHERE key='output_size'").fetchone()
    actual_size = output.stat().st_size if output.exists() else 0
    if row is None:
        return _rebuild_ids(con, output, clear_checkpoints=False), bool(actual_size)
    recorded_size = int(row[0])
    if recorded_size != actual_size:
        return _rebuild_ids(con, output, clear_checkpoints=actual_size < recorded_size), True
    return int(con.execute("SELECT count(*) FROM ids").fetchone()[0]), False


def _prefix_digest(path: Path, size: int) -> str:
    digest = hashlib.sha256()
    remaining = max(0, size)
    with path.open("rb") as handle:
        while remaining:
            chunk = handle.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            digest.update(chunk)
            remaining -= len(chunk)
    if remaining:
        return ""
    return digest.hexdigest()


def _checkpoint(con: sqlite3.Connection, source_path: str) -> sqlite3.Row | None:
    con.row_factory = sqlite3.Row
    return con.execute("SELECT * FROM source_checkpoints WHERE source_path=?", (source_path,)).fetchone()


def _source_plan(path: Path, checkpoint: sqlite3.Row | None) -> tuple[str, int, int, os.stat_result]:
    stat = path.stat()
    if checkpoint is None:
        return "new", 0, 0, stat
    if (
        int(checkpoint["observed_size"]) == stat.st_size
        and int(checkpoint["observed_mtime_ns"]) == stat.st_mtime_ns
        and int(checkpoint["observed_inode"]) == stat.st_ino
    ):
        return "unchanged", int(checkpoint["offset"]), int(checkpoint["line_no"]), stat
    old_offset = int(checkpoint["offset"])
    prefix_matches = (
        stat.st_size >= old_offset
        and _prefix_digest(path, old_offset) == str(checkpoint["prefix_digest"])
    )
    if prefix_matches:
        return "resume", old_offset, int(checkpoint["line_no"]), stat
    return "rewrite", 0, 0, stat


def _complete_lines(path: Path, *, offset: int, line_no: int, snapshot_size: int) -> Iterator[tuple[int, int, bytes]]:
    """Yield (line number, end byte offset, bytes) only for complete snapshot lines."""

    with path.open("rb") as handle:
        handle.seek(offset)
        position = offset
        current_line = line_no
        while position < snapshot_size:
            line_start = position
            raw = handle.readline(snapshot_size - position)
            if not raw:
                break
            position += len(raw)
            if not raw.endswith(b"\n"):
                # Leave a partial final line uncheckpointed so a later append can complete it.
                position = line_start
                break
            current_line += 1
            yield current_line, position, raw


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _empty_counts() -> dict[str, int]:
    return {
        "sources_scanned": 0,
        "sources_skipped_unchanged": 0,
        "sources_resumed": 0,
        "sources_rewritten": 0,
        "source_rows_scanned": 0,
        "invalid_json_lines": 0,
        "non_object_rows": 0,
        "rows_not_capabilities": 0,
        "rows_normalized": 0,
        "new_searchable_rows": 0,
        "duplicate_ids": 0,
        "identity_conflicts_seen": 0,
        "new_identity_conflicts": 0,
    }


def sync_source_union(
    *,
    root: Path = _SBC,
    output: Path = DEFAULT_OUTPUT,
    catalog_path: Path = DEFAULT_CATALOG,
    receipt_path: Path | None = DEFAULT_RECEIPT,
    specs: Sequence[SourceSpec] = SOURCE_SPECS,
) -> dict[str, Any]:
    """Incrementally normalize every discovered source and return a candidate receipt."""

    root = root.resolve()
    sources = discover_sources(root, specs)
    output.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    counts = _empty_counts()
    group_counts: dict[str, dict[str, int]] = {}
    lock_path = output.with_suffix(output.suffix + ".lock")
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        con = sqlite3.connect(catalog_path)
        con.row_factory = sqlite3.Row
        try:
            distinct_before, reconciled = _ensure_catalog(con, output)
            for spec, source in sources:
                source_rel = _relative(source, root)
                checkpoint = _checkpoint(con, source_rel)
                mode, start_offset, start_line, initial_stat = _source_plan(source, checkpoint)
                group = group_counts.setdefault(spec.group, {"sources": 0, "rows_scanned": 0, "rows_added": 0})
                group["sources"] += 1
                if mode == "unchanged":
                    counts["sources_skipped_unchanged"] += 1
                    continue
                counts["sources_scanned"] += 1
                if mode == "resume":
                    counts["sources_resumed"] += 1
                elif mode == "rewrite":
                    counts["sources_rewritten"] += 1

                con.execute("BEGIN IMMEDIATE")
                end_offset = start_offset
                end_line = start_line
                try:
                    with output.open("a", encoding="utf-8") as out:
                        for source_line, line_end, raw_line in _complete_lines(
                            source,
                            offset=start_offset,
                            line_no=start_line,
                            snapshot_size=initial_stat.st_size,
                        ):
                            end_offset = line_end
                            end_line = source_line
                            counts["source_rows_scanned"] += 1
                            group["rows_scanned"] += 1
                            try:
                                raw = json.loads(raw_line)
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                counts["invalid_json_lines"] += 1
                                continue
                            if not isinstance(raw, Mapping):
                                counts["non_object_rows"] += 1
                                continue
                            row = normalize(
                                raw,
                                source_group=spec.group,
                                source_path=source_rel,
                                source_line=source_line,
                                require_source_id=spec.require_source_id,
                            )
                            if row is None:
                                counts["rows_not_capabilities"] += 1
                                continue
                            counts["rows_normalized"] += 1
                            primitive_id = str(row["primitive_id"])
                            existing = con.execute(
                                "SELECT identity_digest FROM ids WHERE primitive_id=?", (primitive_id,)
                            ).fetchone()
                            if existing is not None:
                                if str(existing["identity_digest"]) == str(row["identity_digest"]):
                                    counts["duplicate_ids"] += 1
                                else:
                                    counts["identity_conflicts_seen"] += 1
                                    cursor = con.execute(
                                        """
                                        INSERT OR IGNORE INTO identity_conflicts
                                        VALUES(?,?,?,?,?,?)
                                        """,
                                        (
                                            primitive_id,
                                            str(existing["identity_digest"]),
                                            str(row["identity_digest"]),
                                            source_rel,
                                            source_line,
                                            _now(),
                                        ),
                                    )
                                    counts["new_identity_conflicts"] += int(cursor.rowcount > 0)
                                continue
                            serialized = _canonical_json(row)
                            con.execute(
                                "INSERT INTO ids VALUES(?,?,?,?,?)",
                                (
                                    primitive_id,
                                    str(row["identity_digest"]),
                                    _digest_bytes(serialized.encode("utf-8")),
                                    source_rel,
                                    source_line,
                                ),
                            )
                            out.write(serialized + "\n")
                            counts["new_searchable_rows"] += 1
                            group["rows_added"] += 1
                        out.flush()
                        os.fsync(out.fileno())

                    final_stat = source.stat()
                    # A replacement/truncation during the scan invalidates the checkpoint.  Appends are okay:
                    # this run intentionally consumed only the initial byte snapshot and resumes next time.
                    if final_stat.st_ino != initial_stat.st_ino or final_stat.st_size < initial_stat.st_size:
                        raise RuntimeError(f"source changed destructively during scan: {source_rel}")
                    prefix_digest = _prefix_digest(source, end_offset)
                    if not prefix_digest:
                        raise RuntimeError(f"could not fingerprint processed prefix: {source_rel}")
                    con.execute(
                        """
                        INSERT OR REPLACE INTO source_checkpoints
                        VALUES(?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            source_rel,
                            spec.group,
                            end_offset,
                            end_line,
                            initial_stat.st_size,
                            initial_stat.st_mtime_ns,
                            initial_stat.st_ino,
                            prefix_digest,
                            _now(),
                        ),
                    )
                    output_size = output.stat().st_size if output.exists() else 0
                    con.execute("INSERT OR REPLACE INTO meta VALUES('output_size', ?)", (str(output_size),))
                    con.commit()
                except Exception:
                    con.rollback()
                    raise

            distinct_after = int(con.execute("SELECT count(*) FROM ids").fetchone()[0])
            durable_conflicts = int(con.execute("SELECT count(*) FROM identity_conflicts").fetchone()[0])
            checkpoint_count = int(con.execute("SELECT count(*) FROM source_checkpoints").fetchone()[0])
        finally:
            con.close()
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    receipt: dict[str, Any] = {
        "record_type": "primitive_source_union_ingest_receipt",
        "generated_at": _now(),
        "source_root": str(root),
        "source_patterns": len(specs),
        "discovered_sources": len(sources),
        "catalog_reconciled_from_output": reconciled,
        "distinct_output_rows_before": distinct_before,
        "distinct_output_rows_after": distinct_after,
        "durable_source_checkpoints": checkpoint_count,
        "durable_identity_conflicts": durable_conflicts,
        "counts": counts,
        "by_source_group": dict(sorted(group_counts.items())),
        "output": str(output),
        "catalog": str(catalog_path),
        "receipt": str(receipt_path) if receipt_path else None,
        "trust_note": "Search ingestion is candidate evidence only; source truth and proof claims are not promoted.",
        **BOUNDARY,
    }
    if receipt_path is not None:
        _atomic_json(receipt_path, receipt)
    return receipt


def source_union_stats(
    *, root: Path = _SBC, output: Path = DEFAULT_OUTPUT, catalog_path: Path = DEFAULT_CATALOG,
    specs: Sequence[SourceSpec] = SOURCE_SPECS,
) -> dict[str, Any]:
    """Read durable feed/catalog counts without scanning any source rows."""

    discovered = discover_sources(root.resolve(), specs)
    result: dict[str, Any] = {
        "record_type": "primitive_source_union_stats",
        "discovered_sources": len(discovered),
        "output_exists": output.is_file(),
        "output_bytes": output.stat().st_size if output.exists() else 0,
        "distinct_searchable_rows": 0,
        "source_checkpoints": 0,
        "identity_conflicts": 0,
        **BOUNDARY,
    }
    if catalog_path.is_file():
        con = sqlite3.connect(f"file:{catalog_path.resolve()}?mode=ro", uri=True)
        try:
            tables = {str(row[0]) for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "ids" in tables:
                result["distinct_searchable_rows"] = int(con.execute("SELECT count(*) FROM ids").fetchone()[0])
            if "source_checkpoints" in tables:
                result["source_checkpoints"] = int(
                    con.execute("SELECT count(*) FROM source_checkpoints").fetchone()[0]
                )
            if "identity_conflicts" in tables:
                result["identity_conflicts"] = int(
                    con.execute("SELECT count(*) FROM identity_conflicts").fetchone()[0]
                )
        finally:
            con.close()
    return result


def _write_jsonl(path: Path, rows: Sequence[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(_canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory(prefix="primitive_source_union_") as temp:
        root = Path(temp)
        source = root / "sources" / "nested" / "cards.jsonl"
        excluded_source = root / "sources" / "precursor" / "cards.jsonl"
        specs = (
            SourceSpec(
                "test_family",
                "sources/**/*.jsonl",
                exclude_patterns=("sources/precursor/**",),
            ),
        )
        output = root / "generated" / "source_union.jsonl"
        catalog = root / "generated" / "source_union.sqlite"
        receipt = root / "generated" / "receipt.json"
        source_rows = [
            {
                "primitive_id": "prim:a",
                "title": "Truth-claiming alpha",
                "description": "Normalize alpha safely",
                "input_contract": {"shape": "AlphaIn", "required": ["value"]},
                "output_contract": {"shape": "AlphaOut", "required": ["normalized"]},
                "tags": ["normalize", "alpha"],
                "code": "SECRET FULL CODE MUST NOT BE COPIED",
                "payload_body": {"large": "source body"},
                "verification_level": "execution_verified",
                "proof_status": "passed",
                "candidate": False,
                "serves_truth": True,
            },
            {
                "name": "No source id card",
                "intent": "Derive a stable identity without copying source payload",
                "input_edge": "Text",
                "output_edge": "StableCard",
            },
        ]
        _write_jsonl(source, source_rows)
        _write_jsonl(excluded_source, [{"primitive_id": "prim:excluded", "title": "Must stay excluded"}])
        first = sync_source_union(
            root=root, output=output, catalog_path=catalog, receipt_path=receipt, specs=specs
        )
        first_rows = list(_iter_output(output))
        checks.append((
            "dynamic nested glob honors exclusions and normalizes both source rows",
            first["discovered_sources"] == 1
            and first["counts"]["new_searchable_rows"] == 2
            and len(first_rows) == 2,
        ))
        alpha = next(row for row in first_rows if row["primitive_id"] == "prim:a")
        checks.append((
            "source truth and proof claims are preserved but always downgraded",
            alpha["source_serves_truth"] is True
            and alpha["source_verification_level"] == "execution_verified"
            and alpha["source_proof_status"] == "passed"
            and alpha["candidate"] is True
            and alpha["serves_truth"] is False
            and alpha["verification_level"] == "candidate"
            and alpha["proof_status"] == "unverified",
        ))
        checks.append((
            "search rows stay slim and omit original payload and code",
            "code" not in alpha
            and "payload" not in alpha
            and "payload_body" not in alpha
            and len(_canonical_json(alpha)) < 5_000,
        ))
        derived_id = next(row["primitive_id"] for row in first_rows if row["primitive_id"] != "prim:a")
        checks.append(("missing source ids receive stable identity ids", derived_id.startswith("source-union:test_family:")))
        nested = normalize(
            {
                "card": {
                    "primitive_id": "prim:nested",
                    "entry": "run_nested",
                    "executable_body": "def run_nested(): return True",
                    "serves_truth": False,
                }
            },
            source_group="nested_receipts",
            source_path="nested.jsonl",
            source_line=1,
            require_source_id=True,
        )
        automation = normalize(
            {"primitive_id": "autoprim:1", "stable_name": "automation__webhook__normalize"},
            source_group="automation",
            source_path="automation.jsonl",
            source_line=1,
            require_source_id=True,
        )
        title_only = normalize(
            {"primitive_id": "prim:title-only", "title": "Title is not a description"},
            source_group="title_only",
            source_path="title.jsonl",
            source_line=1,
        )
        checks.append((
            "nested executable and stable-name cards normalize without fabricating description completeness",
            nested is not None
            and nested["primitive_id"] == "prim:nested"
            and nested["title"] == "run_nested"
            and "executable_body" not in nested
            and automation is not None
            and automation["title"] == "automation__webhook__normalize"
            and title_only is not None
            and title_only["blackbox"] == ""
            and title_only["description_status"] == "title_fallback",
        ))
        rejected_unstable = normalize(
            {"title": "Precursor without immutable id", "description": "Not canonical yet"},
            source_group="stable_id_only",
            source_path="source.jsonl",
            source_line=1,
            require_source_id=True,
        )
        checks.append((
            "broad extracted-source families reject rows without stable source ids",
            rejected_unstable is None,
        ))

        second = sync_source_union(
            root=root, output=output, catalog_path=catalog, receipt_path=receipt, specs=specs
        )
        checks.append((
            "unchanged source is not rescanned",
            second["counts"]["sources_skipped_unchanged"] == 1
            and second["counts"]["source_rows_scanned"] == 0,
        ))

        with source.open("a", encoding="utf-8") as handle:
            handle.write(_canonical_json({
                "primitive_id": "prim:b",
                "title": "Beta",
                "description": "Append-only beta",
                "input_edge": "BIn",
                "output_edge": "BOut",
            }) + "\n")
        appended = sync_source_union(
            root=root, output=output, catalog_path=catalog, receipt_path=receipt, specs=specs
        )
        checks.append((
            "true append resumes at the new line",
            appended["counts"]["sources_resumed"] == 1
            and appended["counts"]["source_rows_scanned"] == 1
            and appended["counts"]["new_searchable_rows"] == 1,
        ))

        # Replace the snapshot: changed prim:a is an immutable-id conflict and
        # prim:c is new.  Prefix mismatch must force a safe full rescan.
        _write_jsonl(source, [
            {
                "primitive_id": "prim:a",
                "title": "Changed alpha identity",
                "description": "Conflicting alpha contract",
                "input_edge": "DifferentIn",
                "output_edge": "DifferentOut",
            },
            {
                "primitive_id": "prim:c",
                "title": "Gamma",
                "description": "New row from rewritten snapshot",
                "input_edge": "CIn",
                "output_edge": "COut",
            },
        ])
        rewritten = sync_source_union(
            root=root, output=output, catalog_path=catalog, receipt_path=receipt, specs=specs
        )
        checks.append((
            "rewritten snapshot rescans, adds only new ids, and records immutable-id conflict",
            rewritten["counts"]["sources_rewritten"] == 1
            and rewritten["counts"]["source_rows_scanned"] == 2
            and rewritten["counts"]["new_searchable_rows"] == 1
            and rewritten["counts"]["identity_conflicts_seen"] == 1
            and rewritten["counts"]["new_identity_conflicts"] == 1,
        ))

        # Simulate append durability winning a race against the SQLite commit.
        orphan = normalize(
            {
                "primitive_id": "prim:orphan",
                "title": "Crash durable row",
                "description": "Already appended before catalog commit",
                "input_edge": "CrashIn",
                "output_edge": "CrashOut",
            },
            source_group="test_family",
            source_path="sources/nested/cards.jsonl",
            source_line=3,
        )
        assert orphan is not None
        with output.open("a", encoding="utf-8") as handle:
            handle.write(_canonical_json(orphan) + "\n")
        with source.open("a", encoding="utf-8") as handle:
            handle.write(_canonical_json({
                "primitive_id": "prim:orphan",
                "title": "Crash durable row",
                "description": "Already appended before catalog commit",
                "input_edge": "CrashIn",
                "output_edge": "CrashOut",
            }) + "\n")
        repaired = sync_source_union(
            root=root, output=output, catalog_path=catalog, receipt_path=receipt, specs=specs
        )
        final_rows = list(_iter_output(output))
        final_ids = [row["primitive_id"] for row in final_rows]
        checks.append((
            "output/catalog crash reconciliation prevents duplicate append",
            repaired["catalog_reconciled_from_output"] is True
            and final_ids.count("prim:orphan") == 1
            and len(final_ids) == len(set(final_ids)),
        ))
        stats = source_union_stats(root=root, output=output, catalog_path=catalog, specs=specs)
        checks.append((
            "stats report durable rows, checkpoints, and conflict counters",
            stats["distinct_searchable_rows"] == len(final_ids)
            and stats["source_checkpoints"] == 1
            and stats["identity_conflicts"] == 1
            and stats["candidate"] is True
            and stats["serves_truth"] is False,
        ))
        saved_receipt = json.loads(receipt.read_text(encoding="utf-8"))
        checks.append((
            "durable receipt is candidate-only and carries count groups",
            saved_receipt["candidate"] is True
            and saved_receipt["serves_truth"] is False
            and "counts" in saved_receipt
            and "by_source_group" in saved_receipt,
        ))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"FAIL - ingest_primitive_source_union: {failed}")
        return 1
    print(
        f"PASS - ingest_primitive_source_union: {len(checks)} checks; dynamic source discovery, slim typed "
        "normalization, truth downgrade, append resume, rewrite rescan, immutable-id conflict accounting, "
        "and crash reconciliation."
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sync", action="store_true")
    mode.add_argument("--stats", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", type=Path, default=_SBC)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.stats:
        value = source_union_stats(
            root=args.root, output=args.output, catalog_path=args.catalog, specs=SOURCE_SPECS
        )
    else:
        value = sync_source_union(
            root=args.root,
            output=args.output,
            catalog_path=args.catalog,
            receipt_path=args.receipt,
            specs=SOURCE_SPECS,
        )
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
