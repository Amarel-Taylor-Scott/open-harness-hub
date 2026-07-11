#!/usr/bin/env python3
"""Federated primitive search over every registered primitive corpus tier.

The core primitive database is intentionally left read-only.  Candidate sources that are not yet represented in
``dist/primitives.db`` are indexed into a separate sidecar database, one complete JSONL line at a time.  Each source
has a durable byte-offset checkpoint, so later calls read only bytes appended since the last committed batch.
The registered overlays include the current synthesis/context/research feeds and the immutable, content-deduped
full-corpus search snapshot.  That snapshot is how the million compiled codeblock/template capabilities remain
searchable without copying their multi-kilobyte code bodies into the sidecar index.

The federation exposes three library operations:

``sync_overlay``
    Incrementally index the configured JSONL sources.  The append-only gate fingerprints the already-consumed
    head and tail ranges and refuses truncation or mutation instead of silently trusting a stale offset.
``federated_search``
    Search the core and overlay FTS5 indexes and deduplicate by immutable primitive id. Source-declared proof
    labels remain disclosed claims and cannot authorize ranking; a separate trusted receipt store must supply
    future proof upgrades.
``get_primitive``
    Exact id lookup.  It returns core metadata, the full overlay payload when present, and a best-effort full core
    JSONL payload by following the core pool's registered source path.

Every response is candidate evidence: ``candidate=true`` and ``serves_truth=false``.  Loading or finding a row
never promotes it.

Commands::

    python3 scripts/primitive_search_federation.py --sync
    python3 scripts/primitive_search_federation.py --search "signed webhook idempotency"
    python3 scripts/primitive_search_federation.py --id synthprim-...
    python3 scripts/primitive_search_federation.py --self-test
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
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import sqlite3  # noqa: E402
import tempfile  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from typing import Any, Iterable, Iterator, Mapping, Sequence  # noqa: E402
from urllib.parse import quote  # noqa: E402


BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
DEFAULT_CORE_DB = resource("dist") / "primitives.db"
DEFAULT_OVERLAY_DB = resource("dist") / "primitive_search_federation_overlay.db"
DEFAULT_DESCRIPTION_DB = resource("dist") / "primitive_description_sidecar.db"
DEFAULT_DESCRIPTION_EMBEDDING_STATE_DIR = resource("dist") / "primitive-description-embedding-shards"
DEFAULT_RECIPE_RECEIPT_DB = resource("dist") / "verified_recipe_receipts.sqlite3"
VERIFIED_RECIPE_CARDS = (
    resource("data") / "dev-intel" / "verified_recipe_receipts" / "recipe_cards.jsonl"
)
FULL_CORPUS_SEARCH_DOCS = (
    resource("catalog")
    / "knowledge-packs"
    / "data"
    / "primitive-search-index-fullcorpus"
    / "search_docs.jsonl"
)
SOURCE_UNION_SEARCHABLE_FEED = (
    resource("data")
    / "dev-intel"
    / "primitive_search_federation"
    / "searchable_source_union.jsonl"
)
COMPILED_CODEBLOCK_ROOT = resource("data") / "dev-intel" / "primitive_codeblocks"
COMPILED_CODEBLOCK_ROWS_PER_SHARD = 10_000
COMPILED_CODEBLOCK_FIRST_TIER_ROWS = 100_000
COMPILED_CODEBLOCK_TOTAL_ROWS = 1_000_000
COMPILED_TEMPLATE_SOURCES: tuple[Path, ...] = (
    resource("data") / "dev-intel" / "domain_token_savings" / "template_minted_producer_cards_v2.jsonl",
    resource("data") / "dev-intel" / "domain_token_savings" / "template_minted_producer_cards.jsonl",
)

SYNC_BATCH_LINES = 1_000
SOURCE_FINGERPRINT_BYTES = 4_096
SEARCH_OVERSAMPLE = 8
SCHEMA_VERSION = "2"

_ID_KEYS = ("primitive_id", "id", "card_id")
_TITLE_KEYS = ("title", "name", "slug")
_VERIFICATION_RANK = {
    "candidate": 0,
    "unverified": 0,
    "structural": 1,
    "verified": 1,
    "source": 2,
    "source_verified": 2,
    "family_template_execution": 1,
    "execution": 3,
    "execution_verified": 3,
}
_PROOF_RANK = {
    "revoked": -2,
    "expired": -2,
    "failed": -1,
    "unverified": 0,
    "required": 1,
    "structural_verified": 2,
    "family_template_execution": 2,
    "source_verified": 3,
    "execution_verified": 4,
    "passed": 5,
}
BLOCKED_PROOF_STATUSES = frozenset({"failed", "revoked", "expired"})
_RECIPE_RECEIPT_MATCH_FIELDS = (
    "identity_digest",
    "declaration_digest",
    "contract_digest",
    "artifact_digest",
    "oracle_digest",
    "protocol_digest",
)


@dataclass(frozen=True, slots=True)
class OverlaySource:
    """One append-only JSONL source and its stable result-pool label."""

    pool: str
    path: Path


DEFAULT_OVERLAY_SOURCES: tuple[OverlaySource, ...] = (
    OverlaySource(
        "working_primitives",
        resource("data") / "dev-intel" / "primitive_synthesis" / "working_primitives.jsonl",
    ),
    OverlaySource(
        "context_foundry_drafts",
        resource("data") / "dev-intel" / "aidevobserver_context_foundry" / "primitive_drafts.jsonl",
    ),
    OverlaySource(
        "continuous_research_candidates",
        resource("data") / "dev-intel" / "continuous_primitive_scrape_loop" / "searchable_candidates.jsonl",
    ),
    # This is an immutable generated snapshot rather than an append target.  The same prefix fingerprint gate
    # deliberately rejects in-place regeneration; rebuild the overlay when the snapshot is replaced.
    OverlaySource("compiled_codeblock_candidates", FULL_CORPUS_SEARCH_DOCS),
    # Generated by ingest_primitive_source_union.py from the smaller primitive-bearing namespaces scattered
    # across run artifacts and specialized packs.  The feed is append-only even when an origin is a rewrite
    # snapshot, so this federation keeps one safe resume contract.
    OverlaySource("registered_source_union", SOURCE_UNION_SEARCHABLE_FEED),
    # Search text and source-declared labels remain candidate metadata.  Operational execution rank is joined
    # only from the separate content-valid, unrevoked hidden-oracle receipt store at query time.
    OverlaySource("verified_recipe_cards", VERIFIED_RECIPE_CARDS),
)


class SourceMutationError(RuntimeError):
    """Raised when a source is no longer an append-only extension of its committed prefix."""


class ConcurrentSyncError(RuntimeError):
    """Raised when another writer advances a source checkpoint during this process's batch."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _first_text(row: Mapping[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _primitive_id(row: Mapping[str, Any]) -> str:
    return _first_text(row, _ID_KEYS)


def _blackbox_text(row: Mapping[str, Any]) -> str:
    blackbox = row.get("blackbox")
    if isinstance(blackbox, str) and blackbox.strip():
        return blackbox.strip()
    if isinstance(blackbox, Mapping):
        for key in ("does", "summary", "description", "mechanism"):
            value = blackbox.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if blackbox:
            return _canonical_json(blackbox)
    for key in ("description", "summary", "source_descriptor", "docstring"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, Mapping) and value:
            return _canonical_json(value)
    descriptions = row.get("descriptions")
    if isinstance(descriptions, Mapping):
        for key in ("purpose", "use_when", "verification", "not_when"):
            value = descriptions.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _tags_text(row: Mapping[str, Any]) -> str:
    values: list[str] = []
    # The compact full-corpus snapshot stores its normalized searchable vocabulary in ``tokens`` and
    # ``edge_tokens`` rather than repeating a blackbox body.  Include those fields so the federation preserves
    # the snapshot's existing search surface.
    for key in (
        "capability_tags",
        "tags",
        "domains",
        "tokens",
        "edge_tokens",
        "blocking_keys",
        "family",
        "record_type",
        "kind",
        "primitive_kind",
        "search_text",
    ):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
        elif isinstance(value, (list, tuple, set)):
            values.extend(str(item).strip() for item in value if str(item).strip())
        elif isinstance(value, Mapping):
            values.extend(str(item).strip() for item in value.values() if str(item).strip())
    return " ".join(dict.fromkeys(values))


def _edge_text(row: Mapping[str, Any], edge_key: str, contract_key: str) -> str:
    value = row.get(edge_key)
    if value not in (None, ""):
        return value.strip() if isinstance(value, str) else _canonical_json(value)
    contract = row.get("contract")
    if isinstance(contract, Mapping):
        value = contract.get(contract_key)
        if value not in (None, ""):
            return value.strip() if isinstance(value, str) else _canonical_json(value)
    edge_contract = row.get("edge_contract")
    if isinstance(edge_contract, Mapping):
        value = edge_contract.get(contract_key) or edge_contract.get(edge_key)
        if value not in (None, ""):
            return value.strip() if isinstance(value, str) else _canonical_json(value)
    typed_edges = row.get("typed_edges")
    if isinstance(typed_edges, Mapping):
        typed_key = "consumes" if contract_key == "input" else "produces"
        value = typed_edges.get(typed_key)
        if value not in (None, ""):
            return value.strip() if isinstance(value, str) else _canonical_json(value)
    return ""


def _normalize_verification(value: Any) -> str:
    text = str(value or "candidate").strip().lower().replace("-", "_").replace(" ", "_")
    if text in _VERIFICATION_RANK:
        return text
    if "execution" in text or "oracle" in text:
        return "execution"
    if "source" in text:
        return "source"
    if "structural" in text or text == "verified":
        return "structural"
    return "candidate"


def _proof_status(row: Mapping[str, Any], verification_level: str) -> str:
    # primitive_synthesis_loop proves one of a small set of generic transform templates. It does NOT run a
    # descriptor-specific hidden oracle for the often much broader title/edge contract, so never label this
    # evidence as full execution verification of the described capability.
    if row.get("record_type") == "synthesized_working_primitive":
        return "family_template_execution"
    explicit = row.get("proof_status")
    if isinstance(explicit, str) and explicit.strip():
        status = explicit.strip().lower().replace("-", "_").replace(" ", "_")
        return status if status in _PROOF_RANK else "unverified"

    for container_key in ("proof", "validation", "verification"):
        container = row.get(container_key)
        if not isinstance(container, Mapping):
            continue
        for key in ("oracle_pass", "passed", "pass"):
            if container.get(key) is True:
                return "passed"
            if container.get(key) is False:
                return "failed"
        status = container.get("status")
        if isinstance(status, str):
            normalized = status.strip().lower().replace("-", "_").replace(" ", "_")
            if normalized in _PROOF_RANK:
                return normalized

    if row.get("working") is True and row.get("valid_syntax") is True:
        return "execution_verified"
    if verification_level in {"execution", "execution_verified"}:
        return "execution_verified"
    if verification_level in {"source", "source_verified"}:
        return "source_verified"
    if verification_level in {"structural", "verified"}:
        return "structural_verified"
    if row.get("proof_requirements"):
        return "required"
    return "unverified"


def _proof_status_from_level(verification_level: str) -> str:
    return _proof_status({}, verification_level)


def _quality_tuple(verification_level: str, proof_status: str) -> tuple[int, int]:
    # A failed/revoked/expired receipt can never become a trust anchor merely because it claims a
    # high verification class.  This also makes the ordering safe if a future trusted receipt store is
    # connected: negative outcomes sort below every eligible candidate.
    if proof_status in BLOCKED_PROOF_STATUSES:
        return (-1, _PROOF_RANK[proof_status])
    return (_VERIFICATION_RANK.get(verification_level, 0), _PROOF_RANK.get(proof_status, 0))


def _untrusted_claim_quality(
    declared_verification_level: Any, declared_proof_status: Any
) -> tuple[str, str, str, str]:
    """Separate source-declared evidence labels from resolver-authorized proof.

    JSONL rows and the current core database are candidate catalogs, not a trusted receipt store.  They may
    describe an upstream verification claim, but they cannot authorize their own ranking.  Until an external
    receipt store validates the primitive identity/contract digest, the operational level remains candidate.
    """

    declared_level = _normalize_verification(declared_verification_level)
    declared_status = _proof_status(
        {"proof_status": declared_proof_status} if declared_proof_status not in (None, "") else {},
        declared_level,
    )
    return "candidate", "unverified", declared_level, declared_status


def _recipe_receipt_claim(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return a compact, self-consistent recipe-card claim; it is still not proof by itself."""

    if payload.get("record_type") != "verified_recipe_card":
        return None
    card_digest = str(payload.get("card_digest") or "")
    unsigned = {key: value for key, value in payload.items() if key != "card_digest"}
    expected_card_digest = "sha256:" + _sha256_json(unsigned)
    if card_digest != expected_card_digest:
        return None
    claim = {
        "receipt_id": str(payload.get("receipt_id") or ""),
        "card_digest": card_digest,
    }
    for key in _RECIPE_RECEIPT_MATCH_FIELDS:
        value = str(payload.get(key) or "")
        if not value:
            return None
        claim[key] = value
    return claim if claim["receipt_id"] else None


def _verification_scope(verification_level: str, proof_status: str) -> str:
    if proof_status == "family_template_execution" or verification_level == "family_template_execution":
        return "generic_transform_template_only_not_full_descriptor_contract"
    if verification_level in {"execution", "execution_verified"}:
        return "descriptor_specific_execution"
    if verification_level in {"source", "source_verified"}:
        return "source_shape_and_provenance_not_execution"
    if verification_level in {"structural", "verified"}:
        return "structural_not_execution"
    return "candidate_unverified"


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(_SBC.resolve()))
    except ValueError:
        return str(path.resolve())


def _normalized_overlay_row(
    row: Mapping[str, Any], source: OverlaySource, *, source_offset: int, source_line: int
) -> dict[str, Any] | None:
    pid = _primitive_id(row)
    if not pid:
        return None
    title = _first_text(row, _TITLE_KEYS) or pid
    blackbox = _blackbox_text(row)
    tags = _tags_text(row)
    input_edge = _edge_text(row, "input_edge", "input")
    output_edge = _edge_text(row, "output_edge", "output")
    declared_verification_level = _normalize_verification(row.get("verification_level"))
    if row.get("record_type") == "synthesized_working_primitive":
        declared_verification_level = "family_template_execution"
    declared_proof_status = _proof_status(row, declared_verification_level)
    verification_level, proof_status, _, _ = _untrusted_claim_quality(
        declared_verification_level, declared_proof_status
    )
    verification_rank, proof_rank = _quality_tuple(verification_level, proof_status)
    identity = {
        "primitive_id": pid,
        "title": title,
        "blackbox": blackbox,
        "input_edge": input_edge,
        "output_edge": output_edge,
    }
    payload = dict(row)
    return {
        "primitive_id": pid,
        "pool": source.pool,
        "title": title,
        "blackbox": blackbox,
        "tags": tags,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "verification_level": verification_level,
        "verification_rank": verification_rank,
        "proof_status": proof_status,
        "verification_scope": _verification_scope(verification_level, proof_status),
        "proof_rank": proof_rank,
        "source_path": str(source.path.resolve()),
        "source_offset": source_offset,
        "source_line": source_line,
        "identity_digest": _sha256_json(identity),
        "payload_digest": _sha256_json(payload),
        "payload_json": _canonical_json(payload),
    }


def _core_uri(path: Path) -> str:
    return f"file:{quote(str(path.resolve()), safe='/:')}?mode=ro"


def _connect_core(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(_core_uri(path), uri=True)
    con.row_factory = sqlite3.Row
    return con


def _connect_overlay(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA busy_timeout=30000")
    _create_overlay_schema(con)
    return con


def _manifest_path(overlay_db: Path) -> Path:
    return overlay_db.with_name(f"{overlay_db.stem}.manifest.json")


def _fast_manifest_path(overlay_db: Path) -> Path:
    return overlay_db.with_name(f"{overlay_db.stem}.fast.manifest.json")


def cached_federation_stats(*, overlay_db: Path = DEFAULT_OVERLAY_DB) -> dict[str, Any]:
    """Return the latest persisted coverage receipt without opening a multi-million-row database.

    Search is a latency-sensitive sketch operation.  Computing the core/overlay overlap join merely to decorate
    each response can cost tens of seconds at the current corpus size, even though synchronization already wrote
    the same measured counts to an atomic manifest.  Prefer the small fast-coverage receipt, fall back to the
    richer exact receipt, and return an empty mapping when neither valid receipt exists.  A caller that explicitly
    needs fresh counts can still run :func:`federation_stats` or ``sync(include_description_coverage=...)``.
    """

    candidates = (
        (_fast_manifest_path(Path(overlay_db)), "cached_fast_manifest"),
        (_manifest_path(Path(overlay_db)), "cached_exact_manifest"),
    )
    for path, source in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("record_type") != "primitive_search_federation_coverage":
            continue
        if payload.get("candidate") is not True or payload.get("serves_truth") is not False:
            continue
        required_counts = ("core_docs", "overlay_docs", "overlap_docs", "unique_searchable_docs")
        if any(type(payload.get(key)) is not int or int(payload[key]) < 0 for key in required_counts):
            continue
        return {
            **payload,
            "coverage_source": source,
            "coverage_manifest_path": _display_path(path),
        }
    return {}


def federation_stats(
    *, core_db: Path = DEFAULT_CORE_DB, overlay_db: Path = DEFAULT_OVERLAY_DB,
    description_db: Path = DEFAULT_DESCRIPTION_DB,
    include_description_coverage: bool = False,
) -> dict[str, Any]:
    """Measured deduplicated search coverage across the core and sidecar stores.

    The overlap join is by immutable primitive id. This is the receipt-safe count: unlike a sum of source-file
    rows, it cannot count a governed card once in JSONL and again in the compiled core database.
    """

    core_docs = core_description_complete = 0
    if core_db.exists():
        core_con = _connect_core(core_db)
        try:
            core_docs = int(core_con.execute("SELECT count(*) FROM primitives").fetchone()[0])
            if include_description_coverage:
                core_description_complete = int(core_con.execute(
                    "SELECT count(*) FROM primitives WHERE trim(coalesce(title,''))<>'' "
                    "AND trim(coalesce(blackbox,''))<>'' AND trim(coalesce(input_edge,''))<>'' "
                    "AND trim(coalesce(output_edge,''))<>''"
                ).fetchone()[0])
        finally:
            core_con.close()
    overlay_docs = overlap_docs = overlay_description_complete = overlap_description_complete = 0
    source_offsets: list[dict[str, Any]] = []
    if overlay_db.exists():
        con = sqlite3.connect(f"file:{overlay_db.resolve()}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        try:
            overlay_docs = int(con.execute("SELECT count(*) FROM overlay_primitives").fetchone()[0])
            if include_description_coverage:
                overlay_description_complete = int(con.execute(
                    "SELECT count(*) FROM overlay_primitives WHERE trim(title)<>'' AND trim(blackbox)<>'' "
                    "AND trim(input_edge)<>'' AND trim(output_edge)<>''"
                ).fetchone()[0])
            source_offsets = [
                {"pool": str(row["pool"]), "byte_offset": int(row["byte_offset"]),
                 "line_number": int(row["line_number"]), "source_path": _display_path(Path(row["source_path"]))}
                for row in con.execute(
                    "SELECT pool, source_path, byte_offset, line_number FROM overlay_sources ORDER BY pool"
                )
            ]
            if core_db.exists():
                con.execute("ATTACH DATABASE ? AS core", (str(core_db.resolve()),))
                overlap_docs = int(con.execute(
                    "SELECT count(*) FROM overlay_primitives o "
                    "JOIN core.primitives p ON p.primitive_id=o.primitive_id"
                ).fetchone()[0])
                if include_description_coverage:
                    overlap_description_complete = int(con.execute(
                        "SELECT count(*) FROM overlay_primitives o JOIN core.primitives p "
                        "ON p.primitive_id=o.primitive_id WHERE "
                        "trim(o.title)<>'' AND trim(o.blackbox)<>'' AND trim(o.input_edge)<>'' "
                        "AND trim(o.output_edge)<>'' AND trim(coalesce(p.title,''))<>'' "
                        "AND trim(coalesce(p.blackbox,''))<>'' AND trim(coalesce(p.input_edge,''))<>'' "
                        "AND trim(coalesce(p.output_edge,''))<>''"
                    ).fetchone()[0])
        finally:
            con.close()
    result = {
        "record_type": "primitive_search_federation_coverage",
        "core_docs": core_docs,
        "overlay_docs": overlay_docs,
        "overlap_docs": overlap_docs,
        "unique_searchable_docs": core_docs + overlay_docs - overlap_docs,
        "source_offsets": source_offsets,
        "core_db": _display_path(core_db),
        "overlay_db": _display_path(overlay_db),
        **BOUNDARY,
    }
    if include_description_coverage:
        # Legacy name retained for existing consumers.  This is strictly a four-field presence metric, not a
        # claim that the prose is useful, source-grounded, or execution-verified.
        field_complete_docs = (
            core_description_complete + overlay_description_complete - overlap_description_complete
        )
        result["field_complete_docs"] = field_complete_docs
        result["description_complete_docs"] = field_complete_docs
        result["description_coverage"] = {
            "required_fields": ["title", "blackbox", "input_edge", "output_edge"],
            "metric_semantics": "nonblank_field_presence_only",
            "core_complete": core_description_complete,
            "overlay_complete": overlay_description_complete,
            "overlap_complete": overlap_description_complete,
        }
        try:
            from scripts.primitive_description_backfill_loop import description_stats  # noqa: PLC0415

            result["description_enrichment"] = description_stats(db_path=description_db)
            sidecar_gap_closures = 0
            if description_db.exists():
                desc_con = sqlite3.connect(f"file:{description_db.resolve()}?mode=ro", uri=True)
                try:
                    if core_db.exists():
                        desc_con.execute("ATTACH DATABASE ? AS core", (str(core_db.resolve()),))
                    if overlay_db.exists():
                        desc_con.execute("ATTACH DATABASE ? AS overlay", (str(overlay_db.resolve()),))
                    core_complete = (
                        "(p.primitive_id IS NOT NULL AND trim(coalesce(p.title,''))<>'' "
                        "AND trim(coalesce(p.blackbox,''))<>'' AND trim(coalesce(p.input_edge,''))<>'' "
                        "AND trim(coalesce(p.output_edge,''))<>'')"
                        if core_db.exists()
                        else "0"
                    )
                    overlay_complete = (
                        "(o.primitive_id IS NOT NULL AND trim(o.title)<>'' AND trim(o.blackbox)<>'' "
                        "AND trim(o.input_edge)<>'' AND trim(o.output_edge)<>'')"
                        if overlay_db.exists()
                        else "0"
                    )
                    joins = (
                        (" LEFT JOIN core.primitives p ON p.primitive_id=d.primitive_id" if core_db.exists() else "")
                        + (" LEFT JOIN overlay.overlay_primitives o ON o.primitive_id=d.primitive_id"
                           if overlay_db.exists() else "")
                    )
                    sidecar_gap_closures = int(
                        desc_con.execute(
                            "SELECT count(*) FROM current_descriptions d" + joins
                            + " WHERE d.quality_verdict='pass' AND NOT ("
                            + core_complete + " OR " + overlay_complete + ")"
                        ).fetchone()[0]
                    )
                finally:
                    desc_con.close()
            result["description_enrichment"]["effective_field_gap_closures"] = sidecar_gap_closures
            result["effective_field_complete_docs"] = min(
                int(result["unique_searchable_docs"]), field_complete_docs + sidecar_gap_closures
            )
        except Exception as exc:  # noqa: BLE001 - stats must stay available when an optional sidecar is corrupt
            result["description_enrichment"] = {
                "current_descriptions": 0,
                "search_indexed": 0,
                "usefulness_pass": 0,
                "error": f"{type(exc).__name__}: {exc}",
                **BOUNDARY,
            }
            result["effective_field_complete_docs"] = field_complete_docs
    return result


def primitive_description_gaps(
    *,
    core_db: Path = DEFAULT_CORE_DB,
    overlay_db: Path = DEFAULT_OVERLAY_DB,
    description_db: Path = DEFAULT_DESCRIPTION_DB,
    cursor: str = "",
    limit: int = 50,
    pool: str | None = None,
) -> dict[str, Any]:
    """Return a bounded, cursor-based batch of unique IDs still lacking an effective useful description.

    A blank compact overlay is not a gap when the same immutable ID has a complete core row.  Likewise, an
    accepted sidecar revision only closes the quality gap when it passed (not merely weakly survived) the
    usefulness gate.  The cursor is an immutable primitive ID and no source bodies are loaded.
    """

    raw_cursor = str(cursor or "")
    if raw_cursor.startswith("core:"):
        cursor_stage, cursor_id = "core", raw_cursor[len("core:"):]
    elif raw_cursor.startswith("overlay:"):
        cursor_stage, cursor_id = "overlay", raw_cursor[len("overlay:"):]
    else:
        cursor_stage, cursor_id = "overlay", raw_cursor
    limit = max(1, min(int(limit), 1_000))
    scan_limit = limit * 8
    candidates: set[str] = set()

    def collect(path: Path, table: str, *, overlay: bool) -> None:
        if not path.exists():
            return
        con = _connect_overlay(path) if overlay else _connect_core(path)
        try:
            sql = (
                f"SELECT primitive_id FROM {table} WHERE primitive_id>? AND "
                "(trim(coalesce(title,''))='' OR trim(coalesce(blackbox,''))='' OR "
                "trim(coalesce(input_edge,''))='' OR trim(coalesce(output_edge,''))='')"
            )
            params: list[Any] = [cursor_id]
            if pool:
                sql += " AND pool=?"
                params.append(pool)
            sql += " ORDER BY primitive_id LIMIT ?"
            params.append(scan_limit)
            candidates.update(str(row["primitive_id"]) for row in con.execute(sql, params))
        finally:
            con.close()

    # Walk one primary-key space per page. Querying both stores with an OR-of-missing-fields forced SQLite to
    # scan millions of otherwise complete core rows on every MCP call. The explicit stage cursor is stable and
    # makes ordinary pages proportional to the small requested batch.
    if cursor_stage == "overlay":
        collect(overlay_db, "overlay_primitives", overlay=True)
    else:
        collect(core_db, "primitives", overlay=False)
    ordered = sorted(candidates)
    inspected = ordered[:scan_limit]

    core_con = _connect_core(core_db) if core_db.exists() else None
    overlay_con = _connect_overlay(overlay_db) if overlay_db.exists() else None
    description_con = None
    if description_db.exists():
        description_con = sqlite3.connect(f"file:{description_db.resolve()}?mode=ro", uri=True)
        description_con.row_factory = sqlite3.Row
    gaps: list[dict[str, Any]] = []
    try:
        for primitive_id in inspected:
            rows: list[Mapping[str, Any]] = []
            for con, table in ((core_con, "primitives"), (overlay_con, "overlay_primitives")):
                if con is None:
                    continue
                row = con.execute(
                    f"SELECT pool,title,blackbox,input_edge,output_edge FROM {table} WHERE primitive_id=?",
                    (primitive_id,),
                ).fetchone()
                if row is not None:
                    rows.append(row)
            if pool and not any(str(row["pool"] or "") == pool for row in rows):
                continue
            enriched = None
            if description_con is not None:
                enriched = description_con.execute(
                    "SELECT quality_verdict FROM current_descriptions WHERE primitive_id=?",
                    (primitive_id,),
                ).fetchone()
            if enriched is not None and str(enriched["quality_verdict"]) == "pass":
                continue
            missing = []
            for field in ("title", "blackbox", "input_edge", "output_edge"):
                if not any(str(row[field] or "").strip() for row in rows):
                    missing.append(field)
            if not missing:
                continue
            gaps.append(
                {
                    "primitive_id": primitive_id,
                    "pools": sorted({str(row["pool"] or "") for row in rows}),
                    "missing_fields": missing,
                    "description_quality_verdict": (
                        str(enriched["quality_verdict"]) if enriched is not None else None
                    ),
                    **BOUNDARY,
                }
            )
            if len(gaps) >= limit:
                break
    finally:
        for con in (core_con, overlay_con, description_con):
            if con is not None:
                con.close()
    if inspected:
        next_cursor = f"{cursor_stage}:{inspected[-1]}"
    elif cursor_stage == "overlay":
        next_cursor = "core:"
    else:
        next_cursor = None
    return {
        "record_type": "primitive_description_gap_page",
        "cursor": raw_cursor or None,
        "cursor_stage": cursor_stage,
        "next_cursor": next_cursor,
        "limit": limit,
        "count": len(gaps),
        "gaps": gaps,
        "page_exhausted": not inspected and cursor_stage == "core",
        "note": "bounded page only; count is not the total corpus gap",
        **BOUNDARY,
    }


def _persist_manifest(
    coverage: Mapping[str, Any], overlay_db: Path, *, fast_coverage: bool = False
) -> Path:
    """Atomically persist the measured coverage used by goal-loop gates and the website."""

    path = (
        _fast_manifest_path(overlay_db)
        if fast_coverage
        else _manifest_path(overlay_db)
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": SCHEMA_VERSION, **dict(coverage)}
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        tmp = Path(handle.name)
    os.replace(tmp, path)
    return path


def _create_overlay_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS overlay_meta(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS overlay_sources(
            source_path TEXT PRIMARY KEY,
            pool TEXT NOT NULL,
            byte_offset INTEGER NOT NULL,
            line_number INTEGER NOT NULL,
            head_span INTEGER NOT NULL,
            head_sha256 TEXT NOT NULL,
            tail_start INTEGER NOT NULL,
            tail_span INTEGER NOT NULL,
            tail_sha256 TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS overlay_primitives(
            primitive_id TEXT PRIMARY KEY,
            pool TEXT NOT NULL,
            title TEXT NOT NULL,
            blackbox TEXT NOT NULL,
            tags TEXT NOT NULL,
            input_edge TEXT NOT NULL,
            output_edge TEXT NOT NULL,
            verification_level TEXT NOT NULL,
            verification_rank INTEGER NOT NULL,
            proof_status TEXT NOT NULL,
            verification_scope TEXT NOT NULL DEFAULT 'candidate_unverified',
            proof_rank INTEGER NOT NULL,
            source_path TEXT NOT NULL,
            source_offset INTEGER NOT NULL,
            source_line INTEGER NOT NULL,
            identity_digest TEXT NOT NULL,
            payload_digest TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS overlay_primitives_fts USING fts5(
            title, blackbox, tags, input_edge, output_edge,
            content='overlay_primitives', content_rowid='rowid', tokenize='unicode61'
        );
        CREATE TRIGGER IF NOT EXISTS overlay_primitives_ai AFTER INSERT ON overlay_primitives BEGIN
            INSERT INTO overlay_primitives_fts(rowid, title, blackbox, tags, input_edge, output_edge)
            VALUES (new.rowid, new.title, new.blackbox, new.tags, new.input_edge, new.output_edge);
        END;
        CREATE TRIGGER IF NOT EXISTS overlay_primitives_ad AFTER DELETE ON overlay_primitives BEGIN
            INSERT INTO overlay_primitives_fts(
                overlay_primitives_fts, rowid, title, blackbox, tags, input_edge, output_edge
            ) VALUES (
                'delete', old.rowid, old.title, old.blackbox, old.tags, old.input_edge, old.output_edge
            );
        END;
        CREATE TRIGGER IF NOT EXISTS overlay_primitives_au AFTER UPDATE ON overlay_primitives BEGIN
            INSERT INTO overlay_primitives_fts(
                overlay_primitives_fts, rowid, title, blackbox, tags, input_edge, output_edge
            ) VALUES (
                'delete', old.rowid, old.title, old.blackbox, old.tags, old.input_edge, old.output_edge
            );
            INSERT INTO overlay_primitives_fts(rowid, title, blackbox, tags, input_edge, output_edge)
            VALUES (new.rowid, new.title, new.blackbox, new.tags, new.input_edge, new.output_edge);
        END;
        """
    )
    columns = {str(row[1]) for row in con.execute("PRAGMA table_info(overlay_primitives)")}
    if "verification_scope" not in columns:
        con.execute(
            "ALTER TABLE overlay_primitives ADD COLUMN verification_scope TEXT NOT NULL "
            "DEFAULT 'candidate_unverified'"
        )
    current = con.execute("SELECT value FROM overlay_meta WHERE key='schema_version'").fetchone()
    if current is not None and current["value"] not in {"1", SCHEMA_VERSION}:
        raise RuntimeError(
            f"overlay schema version {current['value']} is not supported by this module (expected {SCHEMA_VERSION})"
        )
    con.execute("INSERT INTO overlay_meta(key, value) VALUES('schema_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (SCHEMA_VERSION,))
    con.commit()


def _fingerprint_at(handle, byte_offset: int) -> dict[str, Any]:
    """Hash stable head/tail ranges inside the consumed prefix without rereading a multi-GB source."""

    saved = handle.tell()
    head_span = min(byte_offset, SOURCE_FINGERPRINT_BYTES)
    tail_start = max(0, byte_offset - SOURCE_FINGERPRINT_BYTES)
    tail_span = byte_offset - tail_start
    handle.seek(0)
    head = handle.read(head_span)
    handle.seek(tail_start)
    tail = handle.read(tail_span)
    handle.seek(saved)
    return {
        "head_span": head_span,
        "head_sha256": _sha256_bytes(head),
        "tail_start": tail_start,
        "tail_span": tail_span,
        "tail_sha256": _sha256_bytes(tail),
    }


def _source_state(con: sqlite3.Connection, source_path: str) -> sqlite3.Row | None:
    return con.execute("SELECT * FROM overlay_sources WHERE source_path=?", (source_path,)).fetchone()


def _validate_append_only(handle, source: OverlaySource, state: sqlite3.Row | None) -> None:
    if state is None:
        return
    if state["pool"] != source.pool:
        raise SourceMutationError(
            f"source pool changed for {source.path}: {state['pool']!r} -> {source.pool!r}"
        )
    size = os.fstat(handle.fileno()).st_size
    offset = int(state["byte_offset"])
    if size < offset:
        raise SourceMutationError(f"source truncated below committed offset {offset}: {source.path}")

    saved = handle.tell()
    handle.seek(0)
    head = handle.read(int(state["head_span"]))
    handle.seek(int(state["tail_start"]))
    tail = handle.read(int(state["tail_span"]))
    handle.seek(saved)
    if _sha256_bytes(head) != state["head_sha256"] or _sha256_bytes(tail) != state["tail_sha256"]:
        raise SourceMutationError(
            f"committed source prefix mutated; refuse offset resume until the overlay is rebuilt: {source.path}"
        )


_OVERLAY_COLUMNS = (
    "primitive_id",
    "pool",
    "title",
    "blackbox",
    "tags",
    "input_edge",
    "output_edge",
    "verification_level",
    "verification_rank",
    "proof_status",
    "verification_scope",
    "proof_rank",
    "source_path",
    "source_offset",
    "source_line",
    "identity_digest",
    "payload_digest",
    "payload_json",
)


def _ingest_overlay_row(con: sqlite3.Connection, row: Mapping[str, Any], normalized: Mapping[str, Any]) -> str:
    """Insert/update one immutable-id row and return a receipt counter name."""

    if row.get("serves_truth") is True:
        return "boundary_mutations_blocked"
    existing = con.execute(
        "SELECT identity_digest, payload_digest, verification_rank, proof_rank FROM overlay_primitives "
        "WHERE primitive_id=?",
        (normalized["primitive_id"],),
    ).fetchone()
    values = tuple(normalized[column] for column in _OVERLAY_COLUMNS)
    if existing is None:
        placeholders = ",".join("?" for _ in _OVERLAY_COLUMNS)
        con.execute(
            f"INSERT INTO overlay_primitives({','.join(_OVERLAY_COLUMNS)}) VALUES({placeholders})",
            values,
        )
        return "indexed"
    if existing["identity_digest"] != normalized["identity_digest"]:
        return "id_mutations_blocked"
    if existing["payload_digest"] == normalized["payload_digest"]:
        return "duplicates"
    old_quality = (int(existing["verification_rank"]), int(existing["proof_rank"]))
    new_quality = (int(normalized["verification_rank"]), int(normalized["proof_rank"]))
    if new_quality < old_quality:
        return "quality_regressions_blocked"
    if new_quality == old_quality:
        return "duplicates"
    assignments = ",".join(f"{column}=?" for column in _OVERLAY_COLUMNS[1:])
    con.execute(
        f"UPDATE overlay_primitives SET {assignments} WHERE primitive_id=?",
        tuple(normalized[column] for column in _OVERLAY_COLUMNS[1:]) + (normalized["primitive_id"],),
    )
    return "quality_upgrades"


def _commit_source_batch(
    con: sqlite3.Connection,
    source: OverlaySource,
    handle,
    batch: Sequence[tuple[Mapping[str, Any] | None, int, int]],
    *,
    expected_offset: int,
    next_offset: int,
    line_number: int,
) -> dict[str, int]:
    counters = {
        "indexed": 0,
        "quality_upgrades": 0,
        "duplicates": 0,
        "invalid_rows": 0,
        "boundary_mutations_blocked": 0,
        "id_mutations_blocked": 0,
        "quality_regressions_blocked": 0,
    }
    source_path = str(source.path.resolve())
    fingerprint = _fingerprint_at(handle, next_offset)
    con.execute("BEGIN IMMEDIATE")
    try:
        current = _source_state(con, source_path)
        current_offset = int(current["byte_offset"]) if current is not None else 0
        if current_offset != expected_offset:
            raise ConcurrentSyncError(
                f"source checkpoint advanced concurrently: expected {expected_offset}, found {current_offset}"
            )
        for parsed, row_offset, row_line in batch:
            if parsed is None:
                counters["invalid_rows"] += 1
                continue
            normalized = _normalized_overlay_row(
                parsed, source, source_offset=row_offset, source_line=row_line
            )
            if normalized is None:
                counters["invalid_rows"] += 1
                continue
            outcome = _ingest_overlay_row(con, parsed, normalized)
            counters[outcome] += 1
        con.execute(
            """INSERT INTO overlay_sources(
                   source_path, pool, byte_offset, line_number,
                   head_span, head_sha256, tail_start, tail_span, tail_sha256
               ) VALUES(?,?,?,?,?,?,?,?,?)
               ON CONFLICT(source_path) DO UPDATE SET
                   pool=excluded.pool,
                   byte_offset=excluded.byte_offset,
                   line_number=excluded.line_number,
                   head_span=excluded.head_span,
                   head_sha256=excluded.head_sha256,
                   tail_start=excluded.tail_start,
                   tail_span=excluded.tail_span,
                   tail_sha256=excluded.tail_sha256""",
            (
                source_path,
                source.pool,
                next_offset,
                line_number,
                fingerprint["head_span"],
                fingerprint["head_sha256"],
                fingerprint["tail_start"],
                fingerprint["tail_span"],
                fingerprint["tail_sha256"],
            ),
        )
        con.commit()
    except Exception:
        con.rollback()
        raise
    return counters


def sync_source(
    source: OverlaySource,
    *,
    overlay_db: Path = DEFAULT_OVERLAY_DB,
    batch_lines: int = SYNC_BATCH_LINES,
) -> dict[str, Any]:
    """Resume one append-only JSONL source from its last committed complete-line byte offset."""

    if batch_lines < 1:
        raise ValueError("batch_lines must be positive")
    receipt: dict[str, Any] = {
        "pool": source.pool,
        "source_path": _display_path(source.path),
        "status": "missing" if not source.path.exists() else "ok",
        "offset_before": 0,
        "offset_after": 0,
        "lines_seen": 0,
        "indexed": 0,
        "quality_upgrades": 0,
        "duplicates": 0,
        "invalid_rows": 0,
        "boundary_mutations_blocked": 0,
        "id_mutations_blocked": 0,
        "quality_regressions_blocked": 0,
        "partial_tail_deferred": False,
        **BOUNDARY,
    }
    if not source.path.exists():
        return receipt

    con = _connect_overlay(overlay_db)
    source_path = str(source.path.resolve())
    try:
        state = _source_state(con, source_path)
        offset = int(state["byte_offset"]) if state is not None else 0
        line_number = int(state["line_number"]) if state is not None else 0
        receipt["offset_before"] = offset
        receipt["offset_after"] = offset
        with source.path.open("rb") as handle:
            _validate_append_only(handle, source, state)
            handle.seek(offset)
            batch: list[tuple[Mapping[str, Any] | None, int, int]] = []
            batch_start = offset
            while True:
                row_offset = handle.tell()
                raw = handle.readline()
                if not raw:
                    break
                if not raw.endswith(b"\n"):
                    handle.seek(row_offset)
                    receipt["partial_tail_deferred"] = True
                    break
                line_number += 1
                receipt["lines_seen"] += 1
                parsed: Mapping[str, Any] | None
                try:
                    value = json.loads(raw.decode("utf-8", errors="replace"))
                    parsed = value if isinstance(value, dict) else None
                except json.JSONDecodeError:
                    parsed = None
                batch.append((parsed, row_offset, line_number))
                if len(batch) >= batch_lines:
                    next_offset = handle.tell()
                    counters = _commit_source_batch(
                        con,
                        source,
                        handle,
                        batch,
                        expected_offset=batch_start,
                        next_offset=next_offset,
                        line_number=line_number,
                    )
                    for key, value in counters.items():
                        receipt[key] += value
                    batch.clear()
                    batch_start = next_offset
                    receipt["offset_after"] = next_offset
            if batch:
                next_offset = handle.tell()
                counters = _commit_source_batch(
                    con,
                    source,
                    handle,
                    batch,
                    expected_offset=batch_start,
                    next_offset=next_offset,
                    line_number=line_number,
                )
                for key, value in counters.items():
                    receipt[key] += value
                receipt["offset_after"] = next_offset
            elif state is None and receipt["offset_after"] == 0 and not receipt["partial_tail_deferred"]:
                counters = _commit_source_batch(
                    con,
                    source,
                    handle,
                    (),
                    expected_offset=0,
                    next_offset=0,
                    line_number=0,
                )
                for key, value in counters.items():
                    receipt[key] += value
        receipt["bytes_advanced"] = int(receipt["offset_after"]) - int(receipt["offset_before"])
        return receipt
    finally:
        con.close()


def sync_overlay(
    *,
    core_db: Path = DEFAULT_CORE_DB,
    overlay_db: Path = DEFAULT_OVERLAY_DB,
    description_db: Path = DEFAULT_DESCRIPTION_DB,
    sources: Sequence[OverlaySource] = DEFAULT_OVERLAY_SOURCES,
    batch_lines: int = SYNC_BATCH_LINES,
    include_description_coverage: bool = True,
) -> dict[str, Any]:
    """Incrementally synchronize every configured overlay source."""

    receipts = [sync_source(source, overlay_db=overlay_db, batch_lines=batch_lines) for source in sources]
    indexed = sum(int(item["indexed"]) for item in receipts)
    upgrades = sum(int(item["quality_upgrades"]) for item in receipts)
    coverage = federation_stats(
        core_db=core_db,
        overlay_db=overlay_db,
        description_db=description_db,
        include_description_coverage=include_description_coverage,
    )
    manifest_path = _persist_manifest(
        coverage, overlay_db, fast_coverage=not include_description_coverage
    )
    return {
        "record_type": "primitive_search_overlay_sync",
        "sources": receipts,
        "indexed": indexed,
        "quality_upgrades": upgrades,
        "mutations_blocked": sum(
            int(item["boundary_mutations_blocked"])
            + int(item["id_mutations_blocked"])
            + int(item["quality_regressions_blocked"])
            for item in receipts
        ),
        "coverage": coverage,
        "manifest_path": _display_path(manifest_path),
        **BOUNDARY,
    }


def _fts_query(query: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9_]+", str(query))
    return " OR ".join(f'"{token}"' for token in dict.fromkeys(tokens))


def _core_has_column(con: sqlite3.Connection, column: str) -> bool:
    return column in {str(row["name"]) for row in con.execute("PRAGMA table_info(primitives)")}


def _result(
    *,
    primitive_id: str,
    pool: str,
    title: str,
    blackbox: str,
    tags: str,
    input_edge: str,
    output_edge: str,
    verification_level: str,
    proof_status: str,
    declared_verification_level: str | None = None,
    declared_proof_status: str | None = None,
    score: float,
    source: str,
) -> dict[str, Any]:
    verification_rank, proof_rank = _quality_tuple(verification_level, proof_status)
    result = {
        "primitive_id": primitive_id,
        "pool": pool,
        "title": title,
        "blackbox": blackbox,
        "tags": tags,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "verification_level": verification_level,
        "proof_status": proof_status,
        "verification_scope": _verification_scope(verification_level, proof_status),
        "quality_rank": verification_rank,
        "proof_rank": proof_rank,
        "score": round(float(score), 8),
        "source": source,
        **BOUNDARY,
    }
    if declared_verification_level is not None or declared_proof_status is not None:
        result["declared_verification_level"] = declared_verification_level or "candidate"
        result["declared_proof_status"] = declared_proof_status or "unverified"
        result["evidence_authority"] = "source_declared_untrusted"
    return result


def _search_core(core_db: Path, query: str, *, pool: str | None, limit: int) -> list[dict[str, Any]]:
    if not core_db.exists():
        return []
    fts_query = _fts_query(query)
    if not fts_query:
        return []
    con = _connect_core(core_db)
    try:
        verification = (
            "COALESCE(p.verification_level, 'candidate')"
            if _core_has_column(con, "verification_level")
            else "'candidate'"
        )
        sql = f"""SELECT p.primitive_id, p.pool, p.title, p.blackbox, p.tags,
                          p.input_edge, p.output_edge, {verification} AS verification_level,
                          bm25(primitives_fts) AS bm25_score
                   FROM primitives_fts
                   JOIN primitives p ON p.rowid=primitives_fts.rowid
                   WHERE primitives_fts MATCH ?"""
        params: list[Any] = [fts_query]
        if pool:
            sql += " AND p.pool=?"
            params.append(pool)
        sql += " ORDER BY bm25_score LIMIT ?"
        params.append(max(1, limit))
        rows = con.execute(sql, params).fetchall()
        results = []
        for row in rows:
            level, proof_status, declared_level, declared_status = _untrusted_claim_quality(
                row["verification_level"], None
            )
            results.append(
                _result(
                    primitive_id=str(row["primitive_id"]),
                    pool=str(row["pool"] or "core"),
                    title=str(row["title"] or ""),
                    blackbox=str(row["blackbox"] or ""),
                    tags=str(row["tags"] or ""),
                    input_edge=str(row["input_edge"] or ""),
                    output_edge=str(row["output_edge"] or ""),
                    verification_level=level,
                    proof_status=proof_status,
                    declared_verification_level=declared_level,
                    declared_proof_status=declared_status,
                    score=-float(row["bm25_score"] or 0.0),
                    source="core",
                )
            )
        return results
    finally:
        con.close()


def _search_overlay(overlay_db: Path, query: str, *, pool: str | None, limit: int) -> list[dict[str, Any]]:
    if not overlay_db.exists():
        return []
    fts_query = _fts_query(query)
    if not fts_query:
        return []
    con = _connect_overlay(overlay_db)
    try:
        sql = """SELECT p.primitive_id, p.pool, p.title, p.blackbox, p.tags,
                        p.input_edge, p.output_edge, p.verification_level, p.proof_status,
                        p.payload_json,
                        bm25(overlay_primitives_fts) AS bm25_score
                 FROM overlay_primitives_fts
                 JOIN overlay_primitives p ON p.rowid=overlay_primitives_fts.rowid
                 WHERE overlay_primitives_fts MATCH ?"""
        params: list[Any] = [fts_query]
        if pool:
            sql += " AND p.pool=?"
            params.append(pool)
        sql += " ORDER BY bm25_score LIMIT ?"
        params.append(max(1, limit))
        rows = con.execute(sql, params).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            try:
                payload = json.loads(str(row["payload_json"]))
            except (json.JSONDecodeError, TypeError):
                payload = {}
            declared_level = _normalize_verification(
                payload.get("verification_level") if isinstance(payload, Mapping) else None
            )
            if isinstance(payload, Mapping) and payload.get("record_type") == "synthesized_working_primitive":
                declared_level = "family_template_execution"
            declared_status = _proof_status(
                payload if isinstance(payload, Mapping) else {}, declared_level
            )
            result = _result(
                primitive_id=str(row["primitive_id"]),
                pool=str(row["pool"]),
                title=str(row["title"]),
                blackbox=str(row["blackbox"]),
                tags=str(row["tags"]),
                input_edge=str(row["input_edge"]),
                output_edge=str(row["output_edge"]),
                verification_level="candidate",
                proof_status="unverified",
                declared_verification_level=declared_level,
                declared_proof_status=declared_status,
                score=-float(row["bm25_score"] or 0.0),
                source="overlay",
            )
            receipt_claim = _recipe_receipt_claim(payload) if isinstance(payload, Mapping) else None
            if receipt_claim is not None:
                result["recipe_receipt_claim"] = receipt_claim
            results.append(result)
        return results
    finally:
        con.close()


def _search_descriptions(
    description_db: Path, query: str, *, pool: str | None, limit: int
) -> list[dict[str, Any]]:
    """Search versioned descriptor revisions without changing primitive proof rank."""

    try:
        from scripts.primitive_description_backfill_loop import search_descriptions  # noqa: PLC0415

        rows = search_descriptions(query, db_path=description_db, pool=pool, limit=limit)
    except Exception:  # noqa: BLE001 - an optional candidate sidecar must never break base search
        return []
    results: list[dict[str, Any]] = []
    for row in rows:
        level, proof_status, declared_level, declared_status = _untrusted_claim_quality(
            row.get("capability_verification_level"), None
        )
        result = _result(
            primitive_id=str(row["primitive_id"]),
            pool=str(row["pool"]),
            title=str(row["title"]),
            blackbox=str(row["blackbox"]),
            tags=str(row.get("tags") or ""),
            input_edge=str(row["input_edge"]),
            output_edge=str(row["output_edge"]),
            verification_level=level,
            proof_status=proof_status,
            declared_verification_level=declared_level,
            declared_proof_status=declared_status,
            score=float(row.get("score") or 0.0),
            source="description",
        )
        result["description_digest"] = str(row.get("description_digest") or "")
        result["description_quality_verdict"] = str(row.get("quality_verdict") or "")
        result["description_provenance"] = "versioned_source_grounded_sidecar"
        results.append(result)
    return results


def _winner_key(row: Mapping[str, Any]) -> tuple[int, int, float, float, int]:
    return (
        int(row.get("quality_rank") or 0),
        int(row.get("proof_rank") or 0),
        float(row.get("embedding_score") or 0.0),
        float(row.get("score") or 0.0),
        1 if row.get("source") == "core" else 0,
    )


def _rank_results(rows: Iterable[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    all_rows = [
        row
        for row in rows
        if str(row.get("proof_status") or "unverified") not in BLOCKED_PROOF_STATUSES
        and str(row.get("declared_proof_status") or "unverified") not in BLOCKED_PROOF_STATUSES
    ]
    by_id: dict[str, dict[str, Any]] = {}
    sources_by_id: dict[str, set[str]] = {}
    description_by_id: dict[str, dict[str, Any]] = {}
    for row in all_rows:
        pid = str(row["primitive_id"])
        sources_by_id.setdefault(pid, set()).add(str(row["source"]))
        existing = by_id.get(pid)
        if existing is None or _winner_key(row) > _winner_key(existing):
            by_id[pid] = row
        if row.get("source") == "description":
            prior = description_by_id.get(pid)
            if prior is None or float(row.get("score") or 0.0) > float(prior.get("score") or 0.0):
                description_by_id[pid] = row
    quality_ranked = sorted(
        by_id.values(),
        key=lambda row: (
            -int(row.get("quality_rank") or 0),
            -int(row.get("proof_rank") or 0),
            -float(row.get("embedding_score") or 0.0),
            -float(row.get("score") or 0.0),
            str(row["primitive_id"]),
        ),
    )
    # A hard quality-first sort can make a semantically exact candidate invisible whenever enough loosely
    # matching source-verified rows exist. Keep the strongest quality/proof result as the trust anchor, then
    # reserve a bounded fraction for the description channel ordered by its own BM25 relevance. Trust and proof
    # remain explicit on every row; semantic relevance never upgrades either axis.
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    if quality_ranked:
        selected.append(quality_ranked[0])
        selected_ids.add(str(quality_ranked[0]["primitive_id"]))
    description_quota = min(len(description_by_id), max(1, int(limit) // 3)) if limit > 1 else 0
    description_ranked = sorted(
        description_by_id.values(),
        key=lambda row: (
            -float(row.get("embedding_score") or 0.0),
            -float(row.get("score") or 0.0),
            str(row["primitive_id"]),
        ),
    )
    for row in description_ranked:
        if sum(1 for item in selected if item.get("source") == "description") >= description_quota:
            break
        pid = str(row["primitive_id"])
        if pid in selected_ids:
            continue
        selected.append(row)
        selected_ids.add(pid)
    for row in quality_ranked:
        pid = str(row["primitive_id"])
        if pid in selected_ids:
            continue
        selected.append(row)
        selected_ids.add(pid)
        if len(selected) >= max(1, limit):
            break
    ranked = selected[: max(1, limit)]
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
        row["available_from"] = sorted(sources_by_id[str(row["primitive_id"])])
    return ranked


def _attach_embedding_scores(
    query: str,
    rows: Sequence[dict[str, Any]],
    *,
    embedding_state_dir: Path,
) -> dict[str, Any]:
    """Rerank only the bounded hybrid shortlist against materialized description vectors."""

    candidate_ids = list(dict.fromkeys(str(row["primitive_id"]) for row in rows))
    try:
        from scripts.primitive_description_embedding_loop import (  # noqa: PLC0415
            score_materialized_candidates,
        )

        receipt = score_materialized_candidates(
            query,
            candidate_ids,
            state_dir=embedding_state_dir,
            profile="envelope",
            max_candidates=max(1, SEARCH_OVERSAMPLE * 64),
        )
    except Exception:  # noqa: BLE001 - optional candidate reranking must never break exact/lexical search
        return {
            "available": False,
            "materialized_candidates": 0,
            "vector_rows_scored": 0,
            "retrieval_role": "bounded-shortlist-reranker-not-standalone-ann",
            **BOUNDARY,
        }
    scores = receipt.pop("scores", {})
    for row in rows:
        score = scores.get(str(row["primitive_id"]))
        if score is not None:
            row["embedding_score"] = float(score)
            row["embedding_profile"] = "envelope"
            row["embedding_proof_effect"] = "none"
    receipt.pop("query", None)
    receipt["available"] = True
    return receipt


def _apply_trusted_recipe_receipts(
    rows: Sequence[dict[str, Any]], *, receipt_db: Path
) -> dict[str, Any]:
    """Authorize only recipe-card rows whose separate executed receipt matches every bound digest."""

    claimed_ids = [
        str(row["primitive_id"])
        for row in rows
        if isinstance(row.get("recipe_receipt_claim"), Mapping)
    ]
    base = {
        "record_type": "trusted_recipe_receipt_join",
        "claimed_candidates": len(set(claimed_ids)),
        "authorized_candidates": 0,
        "receipt_store": "separate-content-validated-execution-evidence",
        **BOUNDARY,
    }
    if not claimed_ids:
        return {**base, "available": Path(receipt_db).is_file()}
    try:
        from scripts.verified_recipe_receipt_store import trusted_receipts_for  # noqa: PLC0415

        receipts = trusted_receipts_for(claimed_ids, db_path=receipt_db)
    except Exception:  # noqa: BLE001 - a missing/corrupt proof store fails closed without breaking search
        return {**base, "available": False}
    by_id = {str(receipt["primitive_id"]): receipt for receipt in receipts}
    authorized: set[str] = set()
    for row in rows:
        primitive_id = str(row["primitive_id"])
        claim = row.get("recipe_receipt_claim")
        receipt = by_id.get(primitive_id)
        if not isinstance(claim, Mapping) or receipt is None:
            continue
        if str(claim.get("receipt_id") or "") != str(receipt.get("receipt_id") or ""):
            continue
        if any(str(claim.get(key) or "") != str(receipt.get(key) or "") for key in _RECIPE_RECEIPT_MATCH_FIELDS):
            continue
        row["verification_level"] = "execution"
        row["proof_status"] = "passed"
        row["verification_scope"] = "recipe_specific_hidden_oracle_execution"
        row["quality_rank"], row["proof_rank"] = _quality_tuple("execution", "passed")
        row["evidence_authority"] = "trusted_recipe_receipt_store"
        row["trusted_receipt"] = {
            "receipt_id": receipt["receipt_id"],
            "receipt_digest": receipt["receipt_digest"],
            "artifact_digest": receipt["artifact_digest"],
            "oracle_digest": receipt["oracle_digest"],
            "protocol_digest": receipt["protocol_digest"],
            "model_tokens": receipt["model_tokens"],
            "revoked_at": receipt["revoked_at"],
        }
        authorized.add(primitive_id)
    return {**base, "available": True, "authorized_candidates": len(authorized)}


def federated_search(
    query: str,
    *,
    core_db: Path = DEFAULT_CORE_DB,
    overlay_db: Path = DEFAULT_OVERLAY_DB,
    description_db: Path = DEFAULT_DESCRIPTION_DB,
    embedding_state_dir: Path = DEFAULT_DESCRIPTION_EMBEDDING_STATE_DIR,
    recipe_receipt_db: Path = DEFAULT_RECIPE_RECEIPT_DB,
    sources: Sequence[OverlaySource] = DEFAULT_OVERLAY_SOURCES,
    pool: str | None = None,
    limit: int = 10,
    sync: bool = True,
) -> dict[str, Any]:
    """Search core + overlay, quality-rank, and deduplicate by immutable primitive id."""

    if not str(query).strip():
        return {"query": query, "count": 0, "results": [], "overlay_sync": None, **BOUNDARY}
    limit = max(1, int(limit))
    sync_receipt = (
        sync_overlay(
            core_db=core_db,
            overlay_db=overlay_db,
            description_db=description_db,
            sources=sources,
            include_description_coverage=False,
        )
        if sync
        else None
    )
    per_index = limit * SEARCH_OVERSAMPLE
    core_rows = _search_core(core_db, query, pool=pool, limit=per_index)
    overlay_rows = _search_overlay(overlay_db, query, pool=pool, limit=per_index)
    description_rows = _search_descriptions(description_db, query, pool=pool, limit=per_index)
    candidate_rows = [*core_rows, *overlay_rows, *description_rows]
    receipt_authorization = _apply_trusted_recipe_receipts(
        candidate_rows, receipt_db=Path(recipe_receipt_db)
    )
    embedding_rerank = _attach_embedding_scores(
        query, candidate_rows, embedding_state_dir=Path(embedding_state_dir)
    )
    results = _rank_results(candidate_rows, limit)
    return {
        "query": query,
        "pool": pool,
        "count": len(results),
        "core_candidates": len(core_rows),
        "overlay_candidates": len(overlay_rows),
        "description_candidates": len(description_rows),
        "retrieval_policy": (
            "fts_candidate_generation_plus_materialized_embedding_shortlist_rerank; "
            "source-declared-proof-never-authorizes-ranking"
        ),
        "embedding_rerank": embedding_rerank,
        "recipe_receipt_authorization": receipt_authorization,
        "results": results,
        "overlay_sync": sync_receipt,
        **BOUNDARY,
    }


def trusted_recipe_search(
    query: str,
    *,
    recipe_cards_path: Path = VERIFIED_RECIPE_CARDS,
    recipe_receipt_db: Path = DEFAULT_RECIPE_RECEIPT_DB,
    limit: int = 10,
) -> dict[str, Any]:
    """Low-latency auto-reuse lane: tiny recipe-card stream plus the separate receipt join only.

    Hooks call this instead of the full core/description/vector federation so a pre-tool advisory never waits on
    a multi-million-row FTS or embedding writer.  Failed, stale, tampered, or revoked receipts simply disappear.
    """

    bounded_limit = max(1, min(int(limit), 100))
    query_tokens = set(re.findall(r"[a-z0-9]+", str(query).lower()))
    rows: list[dict[str, Any]] = []
    if Path(recipe_cards_path).is_file() and query_tokens:
        for payload in _iter_jsonl_payloads(Path(recipe_cards_path)):
            claim = _recipe_receipt_claim(payload)
            if claim is None:
                continue
            title = _first_text(payload, _TITLE_KEYS) or _primitive_id(payload)
            blackbox = _blackbox_text(payload)
            tags = _tags_text(payload)
            input_edge = _edge_text(payload, "input_edge", "input")
            output_edge = _edge_text(payload, "output_edge", "output")
            searchable = " ".join((title, blackbox, tags, input_edge, output_edge)).lower()
            document_tokens = set(re.findall(r"[a-z0-9]+", searchable))
            overlap = len(query_tokens & document_tokens)
            if overlap == 0:
                continue
            row = _result(
                primitive_id=_primitive_id(payload),
                pool="verified_recipe_cards",
                title=title,
                blackbox=blackbox,
                tags=tags,
                input_edge=input_edge,
                output_edge=output_edge,
                verification_level="candidate",
                proof_status="unverified",
                declared_verification_level="candidate",
                declared_proof_status="unverified",
                score=overlap / max(1, len(query_tokens)),
                source="verified_recipe_cards",
            )
            row["recipe_receipt_claim"] = claim
            rows.append(row)
    authorization = _apply_trusted_recipe_receipts(
        rows, receipt_db=Path(recipe_receipt_db)
    )
    authorized = [
        row for row in rows
        if row.get("evidence_authority") == "trusted_recipe_receipt_store"
        and row.get("proof_status") == "passed"
    ]
    return {
        "query": query,
        "count": min(len(authorized), bounded_limit),
        "results": _rank_results(authorized, bounded_limit),
        "recipe_receipt_authorization": authorization,
        "retrieval_policy": "bounded-recipe-card-stream-plus-content-valid-receipt-join",
        **BOUNDARY,
    }


def _core_lookup(core_db: Path, primitive_id: str) -> dict[str, Any] | None:
    if not core_db.exists():
        return None
    con = _connect_core(core_db)
    try:
        verification = (
            "COALESCE(verification_level, 'candidate')"
            if _core_has_column(con, "verification_level")
            else "'candidate'"
        )
        row = con.execute(
            f"""SELECT primitive_id, pool, title, blackbox, tags, input_edge, output_edge,
                       {verification} AS verification_level
                FROM primitives WHERE primitive_id=?""",
            (primitive_id,),
        ).fetchone()
        if row is None:
            return None
        level, proof_status, declared_level, declared_status = _untrusted_claim_quality(
            row["verification_level"], None
        )
        quality_rank, proof_rank = _quality_tuple(level, proof_status)
        result = {
            "primitive_id": str(row["primitive_id"]),
            "pool": str(row["pool"] or "core"),
            "title": str(row["title"] or ""),
            "blackbox": str(row["blackbox"] or ""),
            "tags": str(row["tags"] or ""),
            "input_edge": str(row["input_edge"] or ""),
            "output_edge": str(row["output_edge"] or ""),
            "verification_level": level,
            "proof_status": proof_status,
            "declared_verification_level": declared_level,
            "declared_proof_status": declared_status,
            "evidence_authority": "source_declared_untrusted",
            "quality_rank": quality_rank,
            "proof_rank": proof_rank,
            "source": "core",
            **BOUNDARY,
        }
        return result
    finally:
        con.close()


def _overlay_lookup(overlay_db: Path, primitive_id: str) -> dict[str, Any] | None:
    if not overlay_db.exists():
        return None
    con = _connect_overlay(overlay_db)
    try:
        row = con.execute("SELECT * FROM overlay_primitives WHERE primitive_id=?", (primitive_id,)).fetchone()
        if row is None:
            return None
        payload = json.loads(row["payload_json"])
        declared_level = _normalize_verification(payload.get("verification_level"))
        if payload.get("record_type") == "synthesized_working_primitive":
            declared_level = "family_template_execution"
        declared_status = _proof_status(payload, declared_level)
        quality_rank, proof_rank = _quality_tuple("candidate", "unverified")
        result = {
            "primitive_id": str(row["primitive_id"]),
            "pool": str(row["pool"]),
            "title": str(row["title"]),
            "input_edge": str(row["input_edge"]),
            "output_edge": str(row["output_edge"]),
            "verification_level": "candidate",
            "proof_status": "unverified",
            "declared_verification_level": declared_level,
            "declared_proof_status": declared_status,
            "evidence_authority": "source_declared_untrusted",
            "verification_scope": "candidate_unverified",
            "quality_rank": quality_rank,
            "proof_rank": proof_rank,
            "source": "overlay",
            "source_path": _display_path(Path(row["source_path"])),
            "source_offset": int(row["source_offset"]),
            "source_line": int(row["source_line"]),
            "payload": payload,
            **BOUNDARY,
        }
        receipt_claim = _recipe_receipt_claim(payload)
        if receipt_claim is not None:
            result["recipe_receipt_claim"] = receipt_claim
        return result
    finally:
        con.close()


def _default_core_pool_sources() -> dict[str, Path]:
    """Reuse primitive_database's pool registry so source-path ownership stays single-sourced."""

    try:
        from scripts.primitive_database import _POOLS  # noqa: PLC0415, SLF001 - registry is the source of truth

        return {pool: (_SBC / rel).resolve() for pool, rel in _POOLS}
    except Exception:  # noqa: BLE001 - source payload is explicitly best-effort
        return {}


def _iter_jsonl_payloads(path: Path) -> Iterator[dict[str, Any]]:
    try:
        with path.open("rb") as handle:
            for raw in handle:
                try:
                    value = json.loads(raw.decode("utf-8", errors="replace"))
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    yield value
    except OSError:
        return


def _find_jsonl_payload(path: Path | None, primitive_id: str) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    for row in _iter_jsonl_payloads(path):
        if _primitive_id(row) == primitive_id:
            return row
    return None


def _compiled_codeblock_location(primitive_id: str) -> tuple[Path, int] | None:
    """Map the canonical million-seed id to its deterministic source shard and one-based line number."""

    match = re.fullmatch(r"(?:prim|grp)_seed_primitive_(\d{7})", primitive_id)
    if match is None:
        return None
    row_number = int(match.group(1))
    if not 0 <= row_number < COMPILED_CODEBLOCK_TOTAL_ROWS:
        return None
    if row_number < COMPILED_CODEBLOCK_FIRST_TIER_ROWS:
        directory = COMPILED_CODEBLOCK_ROOT / "codeblock_compile_100k"
        tier_row = row_number
    else:
        directory = COMPILED_CODEBLOCK_ROOT / "codeblock_compile_900k_remaining"
        tier_row = row_number - COMPILED_CODEBLOCK_FIRST_TIER_ROWS
    shard_number, line_offset = divmod(tier_row, COMPILED_CODEBLOCK_ROWS_PER_SHARD)
    return directory / f"primitive_codeblocks_{shard_number:06d}.jsonl", line_offset + 1


def _read_jsonl_line(path: Path, line_number: int) -> dict[str, Any] | None:
    if line_number < 1 or not path.is_file():
        return None
    try:
        with path.open("rb") as handle:
            for current_line, raw in enumerate(handle, start=1):
                if current_line != line_number:
                    continue
                value = json.loads(raw.decode("utf-8", errors="replace"))
                return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None
    return None


def _compiled_full_payload(primitive_id: str) -> tuple[dict[str, Any] | None, Path | None, int | None]:
    """Resolve the executable codeblock/template body behind a compact full-corpus search document."""

    location = _compiled_codeblock_location(primitive_id)
    if location is not None:
        path, line_number = location
        payload = _read_jsonl_line(path, line_number)
        if payload is not None and _primitive_id(payload) == primitive_id:
            return payload, path, line_number
    if primitive_id.startswith("codefactory-"):
        for path in COMPILED_TEMPLATE_SOURCES:
            payload = _find_jsonl_payload(path, primitive_id)
            if payload is not None:
                return payload, path, None
    return None, None, None


def _origin_full_payload(
    wrapper: Mapping[str, Any], primitive_id: str, *, allowed_root: Path = _SBC
) -> tuple[dict[str, Any] | None, Path | None, int | None]:
    """Resolve a normalized source-union pointer without allowing paths outside this substrate checkout."""

    source_origin = wrapper.get("source_origin") if isinstance(wrapper.get("source_origin"), Mapping) else {}
    raw_path = wrapper.get("origin_source_path") or source_origin.get("path")
    raw_line = wrapper.get("origin_source_line") or source_origin.get("line")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None, None, None
    path = Path(raw_path)
    path = path if path.is_absolute() else allowed_root / path
    try:
        resolved = path.resolve()
        resolved.relative_to(allowed_root.resolve())
        line_number = int(raw_line)
    except (OSError, TypeError, ValueError):
        return None, None, None
    payload = _read_jsonl_line(resolved, line_number)
    identity_row: Mapping[str, Any] | None = payload
    if payload is not None and not _primitive_id(payload):
        for key in ("payload", "candidate_payload", "primitive", "card"):
            nested = payload.get(key)
            if isinstance(nested, Mapping):
                identity_row = nested
                break
    if payload is None or identity_row is None or _primitive_id(identity_row) != primitive_id:
        return None, resolved, line_number
    return payload, resolved, line_number


def get_primitive(
    primitive_id: str,
    *,
    core_db: Path = DEFAULT_CORE_DB,
    overlay_db: Path = DEFAULT_OVERLAY_DB,
    description_db: Path = DEFAULT_DESCRIPTION_DB,
    recipe_receipt_db: Path = DEFAULT_RECIPE_RECEIPT_DB,
    sources: Sequence[OverlaySource] = DEFAULT_OVERLAY_SOURCES,
    core_pool_sources: Mapping[str, Path] | None = None,
    sync: bool = True,
    load_core_payload: bool = True,
) -> dict[str, Any]:
    """Exact id lookup with an explicit progressive-disclosure payload gate.

    ``load_core_payload=False`` is intentionally broader than its legacy name: it returns identity/contract/proof
    metadata plus description enrichment, but no core, overlay, compiled, origin, or selected broad payload.
    ``True`` preserves the exact-expansion behavior for callers that explicitly request implementation material.
    """

    pid = str(primitive_id).strip()
    if not pid:
        return {"primitive_id": pid, "found": False, "error": "primitive_id is required", **BOUNDARY}
    sync_receipt = (
        sync_overlay(
            core_db=core_db,
            overlay_db=overlay_db,
            description_db=description_db,
            sources=sources,
            include_description_coverage=False,
        )
        if sync
        else None
    )
    core = _core_lookup(core_db, pid)
    overlay = _overlay_lookup(overlay_db, pid)
    receipt_authorization = _apply_trusted_recipe_receipts(
        [row for row in (core, overlay) if row is not None],
        receipt_db=Path(recipe_receipt_db),
    )
    try:
        from scripts.primitive_description_backfill_loop import get_current_description  # noqa: PLC0415

        description = get_current_description(pid, db_path=description_db)
    except Exception:  # noqa: BLE001 - optional candidate sidecar cannot break exact source retrieval
        description = None
    pool_sources = dict(core_pool_sources or _default_core_pool_sources())
    core_source = pool_sources.get(str(core.get("pool"))) if core else None
    core_payload = _find_jsonl_payload(core_source, pid) if core and load_core_payload else None
    selected_metadata_source = (
        "core"
        if core is not None and (overlay is None or _winner_key(core) >= _winner_key(overlay))
        else "overlay"
        if overlay is not None
        else None
    )
    compiled_payload = compiled_source = compiled_line = None
    if (
        load_core_payload
        and selected_metadata_source == "overlay"
        and overlay
        and overlay.get("pool") == "compiled_codeblock_candidates"
    ):
        compiled_payload, compiled_source, compiled_line = _compiled_full_payload(pid)
    origin_payload = origin_source = origin_line = None
    if (
        load_core_payload
        and selected_metadata_source == "overlay"
        and overlay
        and overlay.get("pool") == "registered_source_union"
    ):
        origin_payload, origin_source, origin_line = _origin_full_payload(overlay.get("payload") or {}, pid)
    overlay_payload = overlay.get("payload") if overlay and load_core_payload else None
    payload = None
    if load_core_payload:
        payload = (
            core_payload
            if selected_metadata_source == "core"
            else compiled_payload or origin_payload or overlay_payload
        )
    return {
        "primitive_id": pid,
        "found": bool(core or overlay or description),
        "core_metadata": core,
        "overlay_metadata": ({key: value for key, value in overlay.items() if key != "payload"} if overlay else None),
        "overlay_payload": overlay_payload,
        "core_payload": core_payload,
        "compiled_payload": compiled_payload,
        "origin_payload": origin_payload,
        "description_enrichment": description,
        "recipe_receipt_authorization": receipt_authorization,
        "selected_metadata_source": selected_metadata_source,
        "payload": payload,
        "payload_source": (
            None
            if not load_core_payload
            else "compiled_source_jsonl"
            if compiled_payload
            else "origin_source_jsonl"
            if origin_payload
            else "overlay"
            if selected_metadata_source == "overlay" and overlay_payload is not None
            else "core_jsonl"
            if selected_metadata_source == "core" and core_payload is not None
            else None
        ),
        "compiled_source_path": _display_path(compiled_source) if compiled_source else None,
        "compiled_source_line": compiled_line,
        "origin_source_path": _display_path(origin_source) if origin_source else None,
        "origin_source_line": origin_line,
        "core_pool_source_path": _display_path(core_source) if core_source else None,
        "overlay_sync": sync_receipt,
        **BOUNDARY,
    }


class PrimitiveSearchFederation:
    """Configured reusable facade for callers that search and fetch repeatedly."""

    def __init__(
        self,
        *,
        core_db: Path = DEFAULT_CORE_DB,
        overlay_db: Path = DEFAULT_OVERLAY_DB,
        description_db: Path = DEFAULT_DESCRIPTION_DB,
        embedding_state_dir: Path = DEFAULT_DESCRIPTION_EMBEDDING_STATE_DIR,
        recipe_receipt_db: Path = DEFAULT_RECIPE_RECEIPT_DB,
        recipe_cards_path: Path = VERIFIED_RECIPE_CARDS,
        sources: Sequence[OverlaySource] = DEFAULT_OVERLAY_SOURCES,
        core_pool_sources: Mapping[str, Path] | None = None,
    ) -> None:
        self.core_db = Path(core_db)
        self.overlay_db = Path(overlay_db)
        self.description_db = Path(description_db)
        self.embedding_state_dir = Path(embedding_state_dir)
        self.recipe_receipt_db = Path(recipe_receipt_db)
        self.recipe_cards_path = Path(recipe_cards_path)
        self.sources = tuple(sources)
        self.core_pool_sources = dict(core_pool_sources or _default_core_pool_sources())

    def sync(self, *, include_description_coverage: bool = True) -> dict[str, Any]:
        return sync_overlay(
            core_db=self.core_db,
            overlay_db=self.overlay_db,
            description_db=self.description_db,
            sources=self.sources,
            include_description_coverage=include_description_coverage,
        )

    def search(self, query: str, *, pool: str | None = None, limit: int = 10, sync: bool = True) -> dict[str, Any]:
        return federated_search(
            query,
            core_db=self.core_db,
            overlay_db=self.overlay_db,
            description_db=self.description_db,
            embedding_state_dir=self.embedding_state_dir,
            recipe_receipt_db=self.recipe_receipt_db,
            sources=self.sources,
            pool=pool,
            limit=limit,
            sync=sync,
        )

    def get(self, primitive_id: str, *, sync: bool = True, load_core_payload: bool = True) -> dict[str, Any]:
        return get_primitive(
            primitive_id,
            core_db=self.core_db,
            overlay_db=self.overlay_db,
            description_db=self.description_db,
            recipe_receipt_db=self.recipe_receipt_db,
            sources=self.sources,
            core_pool_sources=self.core_pool_sources,
            sync=sync,
            load_core_payload=load_core_payload,
        )

    def search_trusted_recipes(self, query: str, *, limit: int = 10) -> dict[str, Any]:
        return trusted_recipe_search(
            query,
            recipe_cards_path=self.recipe_cards_path,
            recipe_receipt_db=self.recipe_receipt_db,
            limit=limit,
        )

    def description_gaps(
        self, *, cursor: str = "", limit: int = 50, pool: str | None = None
    ) -> dict[str, Any]:
        return primitive_description_gaps(
            core_db=self.core_db,
            overlay_db=self.overlay_db,
            description_db=self.description_db,
            cursor=cursor,
            limit=limit,
            pool=pool,
        )


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(_canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def _append_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_canonical_json(row) + "\n")


def _build_fixture_core(path: Path, rows: Sequence[Sequence[Any]]) -> None:
    con = sqlite3.connect(str(path))
    con.executescript(
        """
        CREATE TABLE primitives(
            primitive_id TEXT PRIMARY KEY, pool TEXT, title TEXT, blackbox TEXT, tags TEXT,
            input_edge TEXT, output_edge TEXT, serves_truth INTEGER DEFAULT 0, verification_level TEXT
        );
        CREATE VIRTUAL TABLE primitives_fts USING fts5(
            title, blackbox, tags, content='primitives', content_rowid='rowid'
        );
        """
    )
    con.executemany("INSERT INTO primitives VALUES(?,?,?,?,?,?,?,?,?)", rows)
    con.execute("INSERT INTO primitives_fts(primitives_fts) VALUES('rebuild')")
    con.commit()
    con.close()


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: Any = "") -> None:
        checks.append((name, bool(ok), str(detail)))

    failed_evidence = _result(
        primitive_id="fixture:failed",
        pool="fixture",
        title="Failed execution",
        blackbox="",
        tags="",
        input_edge="In",
        output_edge="Out",
        verification_level="execution",
        proof_status="failed",
        score=100.0,
        source="trusted_receipt_fixture",
    )
    passed_evidence = _result(
        primitive_id="fixture:passed",
        pool="fixture",
        title="Passed source",
        blackbox="",
        tags="",
        input_edge="In",
        output_edge="Out",
        verification_level="source",
        proof_status="passed",
        score=1.0,
        source="trusted_receipt_fixture",
    )
    safely_ranked = _rank_results([failed_evidence, passed_evidence], 10)
    check(
        "failed evidence is ineligible even when it declares the higher verification class",
        [row["primitive_id"] for row in safely_ranked] == ["fixture:passed"],
        safely_ranked,
    )

    with tempfile.TemporaryDirectory(prefix="primitive_search_federation_") as temp_dir:
        root = Path(temp_dir)
        core_db = root / "core.db"
        overlay_db = root / "overlay.db"
        description_db = root / "descriptions.db"
        working = root / "working.jsonl"
        drafts = root / "drafts.jsonl"
        compiled = root / "compiled.jsonl"
        origin = root / "origin.jsonl"
        core_payloads = root / "core_pool.jsonl"

        core_rows = [
            (
                "core:source",
                "core_pool",
                "CSV source validator",
                "Validate CSV rows against a declared schema.",
                "csv validate",
                "CsvRows",
                "ValidationReceipt",
                0,
                "source",
            ),
            (
                "dup:1",
                "core_pool",
                "CSV duplicate resolver",
                "Deduplicate CSV records by stable key.",
                "csv dedupe",
                "CsvRows",
                "DedupedRows",
                0,
                "source",
            ),
            (
                "core:candidate",
                "core_pool",
                "CSV candidate helper",
                "Candidate CSV helper without proof.",
                "csv",
                "Rows",
                "Rows",
                0,
                "candidate",
            ),
        ]
        _build_fixture_core(core_db, core_rows)
        _write_jsonl(
            core_payloads,
            [
                {
                    "primitive_id": row[0],
                    "title": row[2],
                    "input_edge": row[5],
                    "output_edge": row[6],
                    "fixture_payload": f"payload-for-{row[0]}",
                }
                for row in core_rows
            ],
        )
        _write_jsonl(
            working,
            [
                {
                    "primitive_id": "overlay:execution",
                    "title": "CSV execution parser",
                    "family": "csv",
                    "input_edge": "CsvText",
                    "output_edge": "CsvRows",
                    "verification_level": "execution",
                    "working": True,
                    "valid_syntax": True,
                    "code": "def parse_csv(text): return []",
                    **BOUNDARY,
                },
                {
                    "primitive_id": "dup:1",
                    "title": "CSV overlay duplicate",
                    "input_edge": "CsvRows",
                    "output_edge": "DedupedRows",
                    "verification_level": "candidate",
                    **BOUNDARY,
                },
                {
                    "primitive_id": "mutation:1",
                    "title": "CSV stable contract",
                    "blackbox": "Compile CSV rows into a stable receipt.",
                    "input_edge": "CsvRows",
                    "output_edge": "CsvReceipt",
                    "verification_level": "structural",
                    **BOUNDARY,
                },
                {
                    "primitive_id": "overlay:family-template",
                    "record_type": "synthesized_working_primitive",
                    "title": "CSV family-template helper",
                    "input_edge": "CsvRows",
                    "output_edge": "CsvRows",
                    "verification_level": "execution",
                    "working": True,
                    "valid_syntax": True,
                    **BOUNDARY,
                },
            ],
        )
        _write_jsonl(
            drafts,
            [
                {
                    "primitive_id": "overlay:source",
                    "title": "CSV source-backed normalizer",
                    "contract": {"input": "CsvRows", "output": "NormalizedRows"},
                    "description": "Normalize CSV rows using a source-backed schema.",
                    "verification_level": "source",
                    **BOUNDARY,
                }
            ],
        )
        _write_jsonl(
            compiled,
            [
                {
                    "primitive_id": "overlay:compiled-token-doc",
                    "title": "Opaque adapter",
                    "tokens": ["graphql", "cursor", "pagination"],
                    "edge_tokens": ["graphqlrequest", "paginatedresponse"],
                    "input_edge": "GraphqlRequest",
                    "output_edge": "PaginatedResponse",
                    **BOUNDARY,
                }
            ],
        )
        _write_jsonl(
            origin,
            [
                {
                    "primitive_id": "origin:payload",
                    "title": "Origin payload",
                    "code": "def origin_payload(): return True",
                    **BOUNDARY,
                }
            ],
        )
        sources = (
            OverlaySource("working", working),
            OverlaySource("drafts", drafts),
            OverlaySource("compiled_codeblock_candidates", compiled),
        )
        federation = PrimitiveSearchFederation(
            core_db=core_db,
            overlay_db=overlay_db,
            description_db=description_db,
            embedding_state_dir=root / "embedding-state",
            recipe_receipt_db=root / "recipe-receipts.sqlite3",
            sources=sources,
            core_pool_sources={"core_pool": core_payloads},
        )

        first = federation.sync()
        check("initial overlay sync indexes all sources", first["indexed"] == 6, first)
        check("coverage manifest deduplicates core and overlay ids",
              first["coverage"]["unique_searchable_docs"] == 8
              and json.loads(_manifest_path(overlay_db).read_text())["unique_searchable_docs"] == 8,
              first["coverage"])
        _persist_manifest(
            {**first["coverage"], "fast_fixture_marker": True}, overlay_db, fast_coverage=True
        )
        cached_coverage = cached_federation_stats(overlay_db=overlay_db)
        check(
            "latency-sensitive callers reuse the atomic fast coverage receipt without a database join",
            cached_coverage.get("coverage_source") == "cached_fast_manifest"
            and cached_coverage.get("fast_fixture_marker") is True
            and cached_coverage.get("unique_searchable_docs") == 8,
            cached_coverage,
        )
        check("coverage separately measures complete title/description/edge columns",
              0 < first["coverage"]["description_complete_docs"]
              <= first["coverage"]["unique_searchable_docs"]
              and first["coverage"]["description_coverage"]["required_fields"]
              == ["title", "blackbox", "input_edge", "output_edge"], first["coverage"])
        initial_offsets = {item["pool"]: item["offset_after"] for item in first["sources"]}
        check("initial sync persists non-zero byte offsets", all(initial_offsets.values()), initial_offsets)

        found = federation.search("csv", limit=20, sync=False)
        ids = [row["primitive_id"] for row in found["results"]]
        check("federated search sees core and overlay", "core:source" in ids and "overlay:execution" in ids, ids)
        claimed_execution = next(row for row in found["results"] if row["primitive_id"] == "overlay:execution")
        check(
            "source-declared execution does not self-authorize proof ranking",
            claimed_execution["verification_level"] == "candidate"
            and claimed_execution["proof_status"] == "unverified"
            and claimed_execution["declared_verification_level"] == "execution"
            and claimed_execution["evidence_authority"] == "source_declared_untrusted",
            claimed_execution,
        )
        check("federation deduplicates an id present in core and overlay", ids.count("dup:1") == 1, ids)
        duplicate = next(row for row in found["results"] if row["primitive_id"] == "dup:1")
        check("stable core tie-break wins when neither duplicate has an authorized receipt",
              duplicate["source"] == "core", duplicate)
        template = next(row for row in found["results"] if row["primitive_id"] == "overlay:family-template")
        check("generic family-template claim remains disclosed but operationally unverified",
              template["declared_proof_status"] == "family_template_execution"
              and template["verification_level"] == "candidate"
              and template["proof_status"] == "unverified", template)
        required_result_keys = {
            "pool",
            "input_edge",
            "output_edge",
            "verification_level",
            "proof_status",
            "verification_scope",
            "candidate",
            "serves_truth",
        }
        check(
            "every search row exposes pool, edges, proof status, and candidate boundary",
            all(
                required_result_keys <= set(row) and row["candidate"] and not row["serves_truth"]
                for row in found["results"]
            ),
        )
        compiled_found = federation.search("graphql pagination", limit=10, sync=False)
        check(
            "compact full-corpus token documents remain searchable without a repeated blackbox body",
            [row["primitive_id"] for row in compiled_found["results"]] == ["overlay:compiled-token-doc"],
            compiled_found,
        )
        gap_before = federation.description_gaps(limit=20)
        check(
            "gap pagination reports a compact row that lacks an effective description",
            "overlay:compiled-token-doc" in {row["primitive_id"] for row in gap_before["gaps"]},
            gap_before,
        )
        description_source = root / "description_source.jsonl"
        _write_jsonl(
            description_source,
            [
                {
                    "primitive_id": "overlay:compiled-token-doc",
                    "title": "Verify HMAC signed webhook",
                    "input_edge": "SignedWebhookRequest",
                    "output_edge": "WebhookValidationReceipt",
                    "family": "webhook_validation",
                    "effects": ["crypto_verify"],
                    "proof_requirements": ["hmac_contract_test"],
                    "promotion_blockers": ["descriptor_specific_oracle_missing"],
                    "problem_solution_core": {
                        "problem": "Webhook receivers must reject a tampered raw body before routing an event.",
                        "solution_summary": "Verify an HMAC-SHA256 signature and return a typed validation receipt.",
                        "fit_when": "Use when a webhook carries a shared-secret signature.",
                        "avoid_when": "Do not use for unsigned polling responses.",
                        "failure_modes": "missing_signature; invalid_signature",
                        "preconditions": "The signature scheme and secret identity are declared by policy.",
                        "postconditions": "The receipt records the validation outcome without the secret.",
                        "composition_notes": "Compose before event parsing and routing.",
                    },
                    **BOUNDARY,
                }
            ],
        )
        from scripts.primitive_description_backfill_loop import run_tick as run_description_tick

        description_tick = run_description_tick(
            db_path=description_db,
            audit_jsonl=None,
            source_files=[description_source],
            batch_size=1,
        )
        from scripts.primitive_description_embedding_loop import run_tick as run_embedding_tick

        embedding_tick = run_embedding_tick(
            description_db=description_db,
            state_dir=root / "embedding-state",
            batch_size=4,
        )
        described_found = federation.search("HMAC SHA256 tampered webhook", limit=10, sync=False)
        described_exact = federation.get("overlay:compiled-token-doc", sync=False)
        gap_after = federation.description_gaps(limit=20)
        enriched_stats = federation_stats(
            core_db=core_db,
            overlay_db=overlay_db,
            description_db=description_db,
            include_description_coverage=True,
        )
        check(
            "versioned description sidecar adds semantics without mutating immutable overlay identity",
            description_tick["stats"]["usefulness_pass"] == 1
            and described_found["results"][0]["primitive_id"] == "overlay:compiled-token-doc"
            and described_found["results"][0]["source"] == "description"
            and described_exact["overlay_payload"]["title"] == "Opaque adapter"
            and described_exact["description_enrichment"]["title"] == "Verify HMAC signed webhook",
            {"search": described_found, "exact": described_exact},
        )
        check(
            "materialized description vectors rerank only the retrieved shortlist",
            embedding_tick["embedded_jobs"] == 4
            and described_found["embedding_rerank"]["materialized_candidates"] == 1
            and described_found["embedding_rerank"]["retrieval_role"]
            == "bounded-shortlist-reranker-not-standalone-ann"
            and described_found["results"][0].get("embedding_proof_effect") == "none",
            described_found["embedding_rerank"],
        )
        check(
            "a usefulness-passing descriptor revision closes the effective gap page",
            "overlay:compiled-token-doc" not in {row["primitive_id"] for row in gap_after["gaps"]},
            gap_after,
        )
        check(
            "effective completeness adds only sidecar revisions that close a real deduplicated gap",
            enriched_stats["description_enrichment"]["effective_field_gap_closures"] == 1
            and enriched_stats["effective_field_complete_docs"]
            == enriched_stats["field_complete_docs"] + 1,
            enriched_stats,
        )

        from scripts.verified_recipe_receipt_store import (  # noqa: PLC0415
            _execute_current_recipes,
            revoke_receipt,
            store_bundles,
        )

        recipe_cards = root / "recipe_cards.jsonl"
        recipe_receipts = root / "recipe-receipts.sqlite3"
        recipe_bundles = _execute_current_recipes()
        stored_recipes = store_bundles(
            recipe_bundles, db_path=recipe_receipts, cards_path=recipe_cards
        )
        recipe_federation = PrimitiveSearchFederation(
            core_db=core_db,
            overlay_db=root / "recipe-overlay.db",
            description_db=description_db,
            embedding_state_dir=root / "embedding-state",
            recipe_receipt_db=recipe_receipts,
            recipe_cards_path=recipe_cards,
            sources=(OverlaySource("verified_recipe_cards", recipe_cards),),
            core_pool_sources={"core_pool": core_payloads},
        )
        recipe_found = recipe_federation.search(
            "semantic search registered molecule", limit=20, sync=True
        )
        semantic_recipe = next(
            row for row in recipe_found["results"]
            if row["primitive_id"] == "recipe/semantic-search"
        )
        check(
            "separate content-valid hidden-oracle receipt authorizes a matching recipe card",
            stored_recipes["inserted_receipts"] == 5
            and semantic_recipe["verification_level"] == "execution"
            and semantic_recipe["proof_status"] == "passed"
            and semantic_recipe["evidence_authority"] == "trusted_recipe_receipt_store"
            and recipe_found["recipe_receipt_authorization"]["authorized_candidates"] >= 1,
            semantic_recipe,
        )
        revoke_receipt(
            semantic_recipe["trusted_receipt"]["receipt_id"],
            "fixture revocation proves fail-closed search",
            db_path=recipe_receipts,
        )
        revoked_found = recipe_federation.search(
            "semantic search registered molecule", limit=20, sync=False
        )
        revoked_recipe = next(
            row for row in revoked_found["results"]
            if row["primitive_id"] == "recipe/semantic-search"
        )
        check(
            "revoked recipe receipt immediately removes execution authorization",
            revoked_recipe["verification_level"] == "candidate"
            and revoked_recipe["proof_status"] == "unverified"
            and "trusted_receipt" not in revoked_recipe,
            revoked_recipe,
        )
        first_location = _compiled_codeblock_location("prim_seed_primitive_0000000")
        group_location = _compiled_codeblock_location("grp_seed_primitive_0000005")
        boundary_location = _compiled_codeblock_location("prim_seed_primitive_0100001")
        check(
            "compiled primitive ids map deterministically to the executable source shard and line",
            first_location is not None
            and first_location[0].name == "primitive_codeblocks_000000.jsonl"
            and first_location[1] == 1
            and group_location is not None
            and group_location[0].name == "primitive_codeblocks_000000.jsonl"
            and group_location[1] == 6
            and boundary_location is not None
            and boundary_location[0].parent.name == "codeblock_compile_900k_remaining"
            and boundary_location[0].name == "primitive_codeblocks_000000.jsonl"
            and boundary_location[1] == 2,
            {"first": first_location, "group": group_location, "boundary": boundary_location},
        )
        resolved_origin, resolved_path, resolved_line = _origin_full_payload(
            {"origin_source_path": str(origin), "origin_source_line": 1},
            "origin:payload",
            allowed_root=root,
        )
        escaped_origin, _, _ = _origin_full_payload(
            {"origin_source_path": "/etc/passwd", "origin_source_line": 1},
            "origin:payload",
            allowed_root=root,
        )
        check(
            "source-union payload pointers resolve inside their allowed root and reject path escape",
            resolved_origin is not None
            and resolved_origin.get("code", "").startswith("def origin_payload")
            and resolved_path == origin.resolve()
            and resolved_line == 1
            and escaped_origin is None,
        )

        overlay_compact = federation.get("overlay:execution", sync=False, load_core_payload=False)
        check(
            "compact overlay lookup returns metadata but no payload at any payload key",
            overlay_compact["found"]
            and overlay_compact["overlay_metadata"]["primitive_id"] == "overlay:execution"
            and "payload" not in overlay_compact["overlay_metadata"]
            and all(
                overlay_compact[key] is None
                for key in ("overlay_payload", "core_payload", "compiled_payload", "origin_payload", "payload")
            )
            and overlay_compact["payload_source"] is None,
            overlay_compact,
        )
        overlay_exact = federation.get("overlay:execution", sync=False, load_core_payload=True)
        check(
            "explicit exact overlay expansion returns the full payload",
            overlay_exact["found"]
            and overlay_exact["overlay_payload"]["code"].startswith("def parse_csv")
            and overlay_exact["payload"]["code"].startswith("def parse_csv")
            and overlay_exact["payload_source"] == "overlay"
            and overlay_exact["core_metadata"] is None,
            overlay_exact,
        )
        core_compact = federation.get("core:source", sync=False, load_core_payload=False)
        check(
            "compact core lookup also suppresses every payload field",
            core_compact["found"]
            and core_compact["core_metadata"]["pool"] == "core_pool"
            and all(
                core_compact[key] is None
                for key in ("overlay_payload", "core_payload", "compiled_payload", "origin_payload", "payload")
            )
            and core_compact["payload_source"] is None,
            core_compact,
        )
        core_exact = federation.get("core:source", sync=False, load_core_payload=True)
        check(
            "explicit exact core expansion returns metadata and best-effort full JSONL payload",
            core_exact["found"]
            and core_exact["core_metadata"]["pool"] == "core_pool"
            and core_exact["core_payload"]["fixture_payload"] == "payload-for-core:source",
            core_exact,
        )

        _append_jsonl(
            working,
            [
                {
                    "primitive_id": "overlay:appended",
                    "title": "CSV appended encoder",
                    "input_edge": "CsvRows",
                    "output_edge": "CsvBytes",
                    "verification_level": "source",
                    **BOUNDARY,
                }
            ],
        )
        with working.open("a", encoding="utf-8") as handle:
            handle.write('{"primitive_id":')
        incremental = federation.sync()
        working_receipt = next(item for item in incremental["sources"] if item["pool"] == "working")
        check(
            "incremental sync reads only appended complete rows and defers a partial tail",
            working_receipt["offset_before"] == initial_offsets["working"]
            and working_receipt["indexed"] == 1
            and working_receipt["partial_tail_deferred"] is True
            and working_receipt["bytes_advanced"] < working.stat().st_size - initial_offsets["working"],
            working_receipt,
        )
        with working.open("a", encoding="utf-8") as handle:
            handle.write(
                '"overlay:partial","title":"CSV partial completion",'
                '"input_edge":"CsvRows","output_edge":"CsvText","serves_truth":false}\n'
            )
        completed = federation.sync()
        completed_working = next(item for item in completed["sources"] if item["pool"] == "working")
        check("a completed former partial line is indexed on the next sync", completed_working["indexed"] == 1)

        _append_jsonl(
            working,
            [
                {
                    "primitive_id": "mutation:1",
                    "title": "CSV stable contract",
                    "blackbox": "Compile CSV rows into a stable receipt.",
                    "input_edge": "CsvRows",
                    "output_edge": "CsvReceipt",
                    "verification_level": "execution",
                    "working": True,
                    "valid_syntax": True,
                    **BOUNDARY,
                },
                {
                    "primitive_id": "mutation:1",
                    "title": "CSV stable contract",
                    "blackbox": "Compile CSV rows into a stable receipt.",
                    "input_edge": "CsvRows",
                    "output_edge": "ChangedReceipt",
                    "verification_level": "execution",
                    **BOUNDARY,
                },
                {
                    "primitive_id": "truth:blocked",
                    "title": "CSV illegal truth mutation",
                    "input_edge": "CsvRows",
                    "output_edge": "ClaimedTruth",
                    "verification_level": "execution",
                    "serves_truth": True,
                },
            ],
        )
        gated = federation.sync()
        gated_working = next(item for item in gated["sources"] if item["pool"] == "working")
        upgraded = federation.get("mutation:1", sync=False)
        blocked_truth = federation.get("truth:blocked", sync=False)
        check(
            "same-contract source proof claim cannot upgrade operational quality",
            gated_working["quality_upgrades"] == 0
            and upgraded["overlay_metadata"]["verification_level"] == "candidate"
            and upgraded["overlay_metadata"]["evidence_authority"] == "source_declared_untrusted",
            gated_working,
        )
        check(
            "immutable-id and candidate-boundary mutation gates reject bad appended rows",
            gated_working["id_mutations_blocked"] == 1
            and gated_working["boundary_mutations_blocked"] == 1
            and upgraded["overlay_metadata"]["output_edge"] == "CsvReceipt"
            and blocked_truth["found"] is False,
            gated_working,
        )

        before_mutation = federation.sync()
        before_offset = next(item for item in before_mutation["sources"] if item["pool"] == "working")["offset_after"]
        with working.open("r+b") as handle:
            first_byte = handle.read(1)
            handle.seek(0)
            handle.write(b"[" if first_byte != b"[" else b"{")
        mutation_caught = False
        try:
            sync_source(sources[0], overlay_db=overlay_db)
        except SourceMutationError:
            mutation_caught = True
        con = _connect_overlay(overlay_db)
        try:
            stored_offset = int(_source_state(con, str(working.resolve()))["byte_offset"])
        finally:
            con.close()
        check(
            "append-only source mutation gate catches prefix tampering without advancing the checkpoint",
            mutation_caught and stored_offset == before_offset,
            {"caught": mutation_caught, "before": before_offset, "after": stored_offset},
        )

    failures = [(name, detail) for name, ok, detail in checks if not ok]
    for name, ok, detail in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if not ok and detail else ''}")
    if failures:
        print(f"\nFAIL - primitive_search_federation: {len(failures)} of {len(checks)} checks failed")
        return 1
    print(
        "\nPASS - primitive_search_federation: read-only core FTS + resumable append-offset overlay; "
        "incremental append, partial-tail resume, federated dedupe, untrusted proof-claim isolation, failed-proof "
        "rejection, materialized-vector shortlist reranking, trusted-recipe receipt authorization/revocation, "
        "coherent exact payload selection, immutable-id/boundary gates, and source-prefix mutation "
        f"gate proven hermetically; {len(checks)} checks; candidate=true, serves_truth=false."
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--core-db", type=Path, default=DEFAULT_CORE_DB)
    parser.add_argument("--overlay-db", type=Path, default=DEFAULT_OVERLAY_DB)
    parser.add_argument("--description-db", type=Path, default=DEFAULT_DESCRIPTION_DB)
    parser.add_argument("--sync", action="store_true", help="synchronize append-only overlay sources")
    parser.add_argument(
        "--fast-coverage",
        action="store_true",
        help="with --sync, refresh deduplicated searchable counts without the expensive exact description-gap join",
    )
    parser.add_argument("--stats", action="store_true", help="print deduplicated core + overlay coverage")
    parser.add_argument("--search", metavar="QUERY")
    parser.add_argument("--id", dest="primitive_id", metavar="PRIMITIVE_ID")
    parser.add_argument("--pool", default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--no-sync", action="store_true", help="do not sync overlays before search/lookup")
    parser.add_argument("--no-core-payload", action="store_true", help="skip best-effort core JSONL payload scan")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    federation = PrimitiveSearchFederation(
        core_db=args.core_db,
        overlay_db=args.overlay_db,
        description_db=args.description_db,
    )
    if args.sync:
        print(
            json.dumps(
                federation.sync(include_description_coverage=not args.fast_coverage),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.stats:
        print(json.dumps(federation_stats(core_db=args.core_db, overlay_db=args.overlay_db,
                                          description_db=args.description_db,
                                          include_description_coverage=True),
                         indent=2, sort_keys=True))
        return 0
    if args.search is not None:
        print(
            json.dumps(
                federation.search(args.search, pool=args.pool, limit=args.limit, sync=not args.no_sync),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.primitive_id is not None:
        print(
            json.dumps(
                federation.get(
                    args.primitive_id,
                    sync=not args.no_sync,
                    load_core_payload=not args.no_core_payload,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
