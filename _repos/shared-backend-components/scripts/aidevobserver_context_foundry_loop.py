#!/usr/bin/env python3
"""AIDevObserver context foundry loop.

Continuously turns source surfaces and opt-in local AI coding sessions into
candidate-only context for AIDevObserver examples, long synthetic sessions, and
Teleon primitive candidates.

This loop does not promote anything. It writes append-only JSONL candidate
streams under ``data/dev-intel/aidevobserver_context_foundry/``:

* ``source_candidates.jsonl`` — where useful context may come from.
* ``synthetic_session_specs.jsonl`` — public-safe session specs to generate.
* ``primitive_drafts.jsonl`` — source-backed primitive drafts plus opportunity
  rows for capabilities that still need stronger evidence.
* ``candidate_rankings.jsonl`` — ranked next-work queue derived from candidates.
* ``loop_ledger.jsonl`` — one heartbeat per tick.

Local Claude Code sessions are opt-in via ``--include-local-claude``. By default
the loop stores path/content digests and derived review summaries, not raw
transcript content and not raw local paths. Use ``--include-local-paths`` only
for private local operations where path references are acceptable.

Offline by default. Network/Kaggle/GitHub fetching belongs in future source
connectors behind explicit live flags and license gates.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# REPO_ROOT above stays the MONOREPO root (used for relative_to below). But `from scripts.*`/`from src.*` need the
# SUBSTRATE root on sys.path — resolve it via the scripts/_repo_paths.py sentinel, then install() every code root
# so both import families resolve on a bare `python3 _repos/.../scripts/<f>.py` launch.
_sbc = next((_p for _p in Path(__file__).resolve().parents if (_p / "scripts" / "_repo_paths.py").exists()), Path(__file__).resolve().parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install  # noqa: E402
_install()
from scripts._repo_paths import resource as _resource  # noqa: E402
SOURCE_SURFACE_MAP = _resource("catalog") / "knowledge-packs" / "data" / "primitive-source-surface-map" / "surfaces.jsonl"
PUBLIC_CODEGEN_USE_CASE_SEEDS = (
    _resource("catalog")
    / "knowledge-packs"
    / "data"
    / "aidevobserver-public-codegen-use-cases"
    / "use-cases.jsonl"
)
MICROSURFACE_ATLAS = (
    _resource("catalog")
    / "knowledge-packs"
    / "data"
    / "aidevobserver-microsurface-atlas"
    / "microsurfaces.jsonl"
)
SOURCE_DISCOVERY_SEARCH_SEEDS = (
    _resource("catalog")
    / "knowledge-packs"
    / "data"
    / "aidevobserver-source-discovery-search-seeds"
    / "search-topics.jsonl"
)
RSS_SOURCE_FEEDS = (
    _resource("catalog")
    / "knowledge-packs"
    / "data"
    / "aidevobserver-rss-source-feeds"
    / "feeds.jsonl"
)
MARKDOWN_INDEX_SOURCES = (
    _resource("catalog")
    / "knowledge-packs"
    / "data"
    / "aidevobserver-markdown-index-sources"
    / "indexes.jsonl"
)
MULTILINGUAL_SEARCH_SCOPES = (
    _resource("catalog")
    / "knowledge-packs"
    / "data"
    / "aidevobserver-multilingual-search-scopes"
    / "scopes.jsonl"
)
NAICS_SEARCH_SCOPES = (
    _resource("catalog")
    / "knowledge-packs"
    / "data"
    / "aidevobserver-naics-primitive-scopes"
    / "scopes.jsonl"
)
BUSINESS_OPERATION_SEARCH_SCOPES = (
    _resource("catalog")
    / "knowledge-packs"
    / "data"
    / "aidevobserver-business-operation-scopes"
    / "scopes.jsonl"
)
DEFAULT_OUT_DIR = _resource("data") / "dev-intel" / "aidevobserver_context_foundry"
DEFAULT_INTERVAL_SECONDS = 60 * 60
DEFAULT_MAX_LOCAL_SESSIONS = 25
DEFAULT_MAX_LOCAL_REVIEW_BYTES = 8 * 1024 * 1024
DEFAULT_GITHUB_QUERY_LIMIT = 3
DEFAULT_GITHUB_RESULT_LIMIT = 5
DEFAULT_GITHUB_TIMEOUT_SECONDS = 20
DEFAULT_KAGGLE_TOPIC_LIMIT = 3
DEFAULT_KAGGLE_RESULT_LIMIT = 5
DEFAULT_KAGGLE_TIMEOUT_SECONDS = 60
DEFAULT_RSS_FEED_LIMIT = 5
DEFAULT_RSS_ITEM_LIMIT = 5
DEFAULT_RSS_TIMEOUT_SECONDS = 20
DEFAULT_MARKDOWN_INDEX_LIMIT = 3
DEFAULT_MARKDOWN_LINK_LIMIT = 50
DEFAULT_MARKDOWN_TIMEOUT_SECONDS = 20
DEFAULT_SEARCH_SCOPE_LIMIT = 0
DEFAULT_NAICS_SCOPE_LIMIT = 0
DEFAULT_BUSINESS_OPERATION_SCOPE_LIMIT = 0
DEFAULT_LOCAL_REPO_PRIMITIVE_LIMIT = 80
GITHUB_CODE_SEARCH_API = "https://api.github.com/search/code"
GITHUB_REPOSITORY_SEARCH_API = "https://api.github.com/search/repositories"
GITHUB_API_VERSION = "2022-11-28"
GITHUB_USER_AGENT = "AIDevObserver-Context-Foundry"
GITHUB_DISCOVERY_QUERIES = (
    'path:*.jsonl "role" "assistant" "tool_calls"',
    'path:*.jsonl "\\"role\\":\\"assistant\\"" "tool_call"',
    'path:.aider.chat.history.md',
    '"swe-agent" "trajectory" "patch"',
    '"OpenHands" "trajectory" "SWE-bench"',
    'n8n workflow filename:*.json "nodes" "connections"',
    '"n8n-nodes-base" "workflow" filename:*.json',
    '"nodes" "connections" "n8n" path:workflows',
    '"workflow" "nodes" "credentials" "n8n"',
)
GITHUB_REPOSITORY_DISCOVERY_QUERIES = (
    '"swe-agent" trajectory patch',
    '"OpenHands" "SWE-bench" trajectory',
    '"aider" "chat history"',
    '"Claude Code" transcript',
    '"agent" trajectory "tool_calls"',
    'n8n workflows templates json',
    'n8n automation workflows',
    'workflow templates n8n nodes connections',
)
KAGGLE_DISCOVERY_TOPICS = (
    "tabular",
    "classification",
    "regression",
    "forecasting",
    "computer vision",
    "nlp",
    "fraud detection",
    "churn",
    "house prices",
    "sentiment analysis",
)
KAGGLE_METADATA_KINDS = ("competitions", "datasets", "kernels")

SOURCE_CANDIDATES_FILE = "source_candidates.jsonl"
SYNTHETIC_SESSION_SPECS_FILE = "synthetic_session_specs.jsonl"
PRIMITIVE_DRAFTS_FILE = "primitive_drafts.jsonl"
CANDIDATE_RANKINGS_FILE = "candidate_rankings.jsonl"
LOOP_LEDGER_FILE = "loop_ledger.jsonl"

RANK_WEIGHT_BASE = 12
RANK_WEIGHT_PRIMITIVE_OPPORTUNITY = 7
RANK_WEIGHT_SESSION_SPEC = 9
RANK_WEIGHT_PRIMITIVE_DRAFT = 8
RANK_WEIGHT_REVIEW_FINDING = 10
RANK_WEIGHT_PUBLIC_SOURCE = 8
RANK_WEIGHT_PRIVATE_SOURCE = 4
RANK_WEIGHT_PUBLIC_CODEGEN_SEED = 14
RANK_WEIGHT_MICROSURFACE_SEED = 12
RANK_WEIGHT_LICENSE_NEEDS_REVIEW_PENALTY = 6

TOKEN_PROXY_PER_OPPORTUNITY = 650
TOKEN_PROXY_PER_SESSION_SPEC = 1400
TOKEN_PROXY_PER_PRIMITIVE_DRAFT = 1800
TOKEN_PROXY_PER_REVIEW_FINDING = 1200

PRIORITY_P0_MIN_SCORE = 90
PRIORITY_P1_MIN_SCORE = 60
PRIORITY_P2_MIN_SCORE = 30

TRUE_VALUES = {"1", "true", "yes", "on"}
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"AKIA[0-9A-Z]{12,}"),
    re.compile(r"gsk_[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[^\s]+"),
)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

SOURCE_BACKED_LICENSE_STATUSES = {
    "first_party",
    "first_party_reviewed",
    "license_reviewed",
    "license_reviewed_compatible",
    "reviewed_compatible",
}
SOURCE_BACKED_REDACTION_STATUSES = {
    "redaction_passed",
    "reviewed_safe",
    "public_safe",
}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(text: str | bytes, *, n: int = 16) -> str:
    data = text if isinstance(text, bytes) else text.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:n]


def _file_sha(path: Path, *, n: int = 24) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


def _path_label(path: str | Path) -> str:
    raw = str(path)
    try:
        resolved = Path(raw).resolve()
        return str(resolved.relative_to(REPO_ROOT))
    except Exception:
        return f"path_digest:sha256:{_sha(raw, n=24)}"


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:80] or "candidate"


def _edge_type_name(value: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", str(value).lower())
    if not parts:
        return "Value"
    return "".join(part[:1].upper() + part[1:] for part in parts[:4])


def _redact(text: str) -> str:
    out = str(text)
    for pat in SECRET_PATTERNS:
        out = pat.sub("[REDACTED_SECRET]", out)
    out = EMAIL_RE.sub("[REDACTED_EMAIL]", out)
    return out


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _append_unique(path: Path, records: Iterable[dict[str, Any]], *, key: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = {str(r.get(key)) for r in _read_jsonl(path) if r.get(key)}
    added = 0
    with path.open("a", encoding="utf-8") as fh:
        for rec in records:
            k = str(rec.get(key) or "")
            if not k or k in seen:
                continue
            fh.write(_canon(rec) + "\n")
            seen.add(k)
            added += 1
    return added


def _rewrite_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(_canon(rec) + "\n")
    os.replace(tmp, path)


PATH_LABEL_KEYS = {"out_dir", "surface_map", "public_use_case_seeds", "microsurface_atlas", "markdown_index_file", "multilingual_search_scopes", "rss_feed_file", "search_seed_file", "ranking_file"}
PRIVATE_LOCAL_REPO_DIRS = {".agent", ".agents", ".codex"}
STALE_LOCAL_REPO_DIRS = {"archive", "repo_reference"}


def _current_local_repo_primitive_schema() -> str:
    from src.teleon.observer.local_registry_connector import LOCAL_PRIMITIVE_CANDIDATE_SCHEMA

    return LOCAL_PRIMITIVE_CANDIDATE_SCHEMA


def _scrub_path_labels(obj: Any) -> tuple[Any, int]:
    if isinstance(obj, dict):
        changed = 0
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if key in PATH_LABEL_KEYS and isinstance(value, str) and value.startswith("/"):
                label = _path_label(value)
                out[key] = label
                changed += int(label != value)
                continue
            scrubbed, nested_changed = _scrub_path_labels(value)
            out[key] = scrubbed
            changed += nested_changed
        return out, changed
    if isinstance(obj, list):
        changed = 0
        out_list: list[Any] = []
        for item in obj:
            scrubbed, nested_changed = _scrub_path_labels(item)
            out_list.append(scrubbed)
            changed += nested_changed
        return out_list, changed
    return obj, 0


def _skipped_local_repo_row(row: dict[str, Any]) -> bool:
    if row.get("source_kind") != "first_party_local_repo_record" and row.get("source_surface_id") != "local-repo":
        return False
    source_ref = row.get("source_ref")
    if not isinstance(source_ref, dict):
        return False
    path = str(source_ref.get("path") or "")
    parts = {part for part in path.split("/") if part}
    return bool(parts & (PRIVATE_LOCAL_REPO_DIRS | STALE_LOCAL_REPO_DIRS))


def _stale_local_repo_primitive_row(row: dict[str, Any]) -> bool:
    return (
        row.get("source_surface_id") == "local-repo"
        and row.get("record_type") == "primitive_draft"
        and row.get("candidate_schema") != _current_local_repo_primitive_schema()
    )


def _surface_rows(surface_map: Path, *, limit: int = 0) -> list[dict[str, Any]]:
    rows = _read_jsonl(surface_map)
    if limit > 0:
        return rows[:limit]
    return rows


def _discovery_queries(surface: dict[str, Any]) -> list[str]:
    sid = surface.get("id", "surface")
    tags = surface.get("tags") or []
    title = surface.get("title", sid)
    if sid == "surface-kaggle":
        return [
            "kaggle competitions list",
            "kaggle kernels list --search tabular",
            "kaggle datasets list --search classification",
            "kaggle kernels pull <owner/kernel>",
        ]
    if sid == "surface-github":
        return [
            'GitHub Code Search: path:*.jsonl "role" "assistant" "tool_calls"',
            'GitHub Code Search: path:.aider.chat.history.md',
            'GitHub Code Search: "swe-agent" "trajectory" "patch"',
        ]
    if "api" in str(surface.get("access_method", "")):
        return [f"API scout: {surface.get('url')}"]
    joined = " ".join(str(t) for t in tags)
    return [f"search {title} {joined}".strip()]


def _source_candidate(surface: dict[str, Any]) -> dict[str, Any]:
    sid = str(surface.get("id") or _slug(str(surface.get("title") or "surface")))
    return {
        "record_type": "source_candidate",
        "candidate_id": f"source:{sid}",
        "source_surface_id": sid,
        "title": surface.get("title", sid),
        "url": surface.get("url"),
        "source_type": surface.get("source_type"),
        "access_method": surface.get("access_method"),
        "scan_cadence": surface.get("scan_cadence"),
        "authority": surface.get("authority"),
        "license_note": surface.get("license_note"),
        "license_status": "needs_review",
        "primitive_opportunities": surface.get("primitive_opportunities") or [],
        "discovery_queries": _discovery_queries(surface),
        "tags": surface.get("tags") or [],
        "status": "candidate",
        "trust": "candidate",
        "readiness": "R1_indexed",
        "serves_truth": False,
        "created_at": _utc(),
    }


def _contract_for_opportunity(opportunity: str) -> dict[str, str]:
    o = opportunity.lower()
    if "notebook" in o:
        return {"input": "NotebookArtifact", "output": "SyntheticSessionSpec"}
    if "competition" in o or "benchmark" in o or "eval" in o:
        return {"input": "TaskDescriptor", "output": "BenchmarkTemplate"}
    if "dataset" in o:
        return {"input": "DatasetSource", "output": "DatasetDescriptor"}
    if "schema" in o:
        return {"input": "RawSchemaEvidence", "output": "SchemaContract"}
    if "tool" in o or "connector" in o or "mcp" in o:
        return {"input": "ToolEvidence", "output": "PrimitiveRecordDraft"}
    if "workflow" in o or "pipeline" in o or "template" in o:
        return {"input": "WorkflowEvidence", "output": "PipelineTemplateDraft"}
    if "rule" in o or "policy" in o or "control" in o:
        return {"input": "SourceEvidence", "output": "RulePackDraft"}
    return {"input": "SourceEvidence", "output": "PrimitiveRecordDraft"}


def _has_source_evidence_for_draft(source: dict[str, Any]) -> bool:
    """Return true only when a source row is strong enough for a draft candidate.

    Curated seeds, metadata-only discovery, and synthetic derivatives are useful
    opportunities, but they should not be labeled primitive drafts until license
    and redaction evidence have passed or an upstream connector marks the source
    as explicitly source-backed.
    """

    if source.get("source_evidence_status") == "source_backed":
        return True
    if source.get("source_backed") is True:
        return True
    license_status = str(source.get("license_status") or "")
    redaction_status = str(source.get("redaction_status") or "")
    return (
        license_status in SOURCE_BACKED_LICENSE_STATUSES
        and redaction_status in SOURCE_BACKED_REDACTION_STATUSES
    )


def _candidate_source_ref(source: dict[str, Any], *, fallback_candidate: str | None = None) -> dict[str, Any]:
    ref = {
        "kind": str(source.get("source_kind") or source.get("source_type") or "source_candidate"),
        "candidate_id": str(source.get("candidate_id") or fallback_candidate or ""),
    }
    if source.get("source_surface_id"):
        ref["source_surface_id"] = source.get("source_surface_id")
    if source.get("source_candidate"):
        ref["source_candidate"] = source.get("source_candidate")
    if source.get("url"):
        ref["url"] = source.get("url")
    if source.get("source_url"):
        ref["url"] = source.get("source_url")
    return {k: v for k, v in ref.items() if v}


def _finalize_primitive_candidate(
    candidate: dict[str, Any],
    source: dict[str, Any],
    *,
    fallback_candidate: str | None = None,
) -> dict[str, Any]:
    out = dict(candidate)
    source_ref = out.get("source_ref")
    if not isinstance(source_ref, dict):
        source_ref = _candidate_source_ref(source, fallback_candidate=fallback_candidate)
    out["source_ref"] = source_ref
    out["source_evidence_status"] = "source_backed" if _has_source_evidence_for_draft(source) else "needs_source_evidence"
    out["candidate_stage"] = "primitive_draft" if out["source_evidence_status"] == "source_backed" else "primitive_opportunity"
    out["record_type"] = out["candidate_stage"]
    if out["candidate_stage"] == "primitive_opportunity":
        out.setdefault("promotion_blockers", [
            "source_evidence_required",
            "license_gate",
            "redaction_gate",
            "contract_review",
        ])
    out.setdefault("raw_source_republish_allowed", False)
    out.setdefault("public_export_allowed", False)
    out["serves_truth"] = False
    return out


def _effects_for_surface(surface: dict[str, Any]) -> list[str]:
    method = str(surface.get("access_method") or "")
    if "api" in method or "browser" in method:
        return ["net.read"]
    return []


def _session_spec(surface: dict[str, Any], opportunity: str) -> dict[str, Any]:
    sid = str(surface.get("id") or _slug(str(surface.get("title") or "surface")))
    oid = _slug(opportunity)
    return {
        "record_type": "synthetic_session_spec",
        "session_spec_id": f"synth:{sid}:{oid}",
        "source_surface_id": sid,
        "source_kind": "synthetic_from_source_surface",
        "title": f"{surface.get('title', sid)} — {opportunity}",
        "intent": f"Build or improve a workflow around {opportunity.replace('_', ' ')} using {surface.get('title', sid)} evidence.",
        "expected_long_session_shape": [
            "intent",
            "source_discovery",
            "context_distillation",
            "candidate_route_search",
            "implementation_or_adapter",
            "proof_or_eval",
            "registry_memory_update",
        ],
        "expected_findings": [
            "missed_existing_primitive",
            "wasted_context",
            "candidate_template_route",
        ],
        "source_attribution_required": True,
        "license_status": "needs_review",
        "status": "candidate",
        "serves_truth": False,
        "created_at": _utc(),
    }


def _primitive_draft(surface: dict[str, Any], opportunity: str) -> dict[str, Any]:
    sid = str(surface.get("id") or _slug(str(surface.get("title") or "surface")))
    oid = _slug(opportunity)
    contract = _contract_for_opportunity(opportunity)
    candidate = {
        "record_type": "primitive_draft",
        "primitive_id": f"prim:candidate:{sid}:{oid}",
        "slug": f"{sid.replace('surface-', '')}.{oid}",
        "source_surface_id": sid,
        "source_url": surface.get("url"),
        "title": f"{surface.get('title', sid)} {opportunity.replace('_', ' ')} primitive",
        "contract": contract,
        "effects": _effects_for_surface(surface),
        "memory": "artifact" if "Artifact" in contract["input"] or "Artifact" in contract["output"] else "inline",
        "cache": "content_hash",
        "trust": "candidate",
        "readiness": "R2_surface_known",
        "proof_requirements": [
            "license_gate",
            "source_attribution_gate",
            "redaction_gate",
            "contract_review",
            "example_session_review",
        ],
        "remix_tools": ["map_sequence", "output_wrapper"],
        "serves_truth": False,
        "created_at": _utc(),
    }
    return _finalize_primitive_candidate(
        candidate,
        surface,
        fallback_candidate=f"source:{sid}",
    )


def _surface_derived_records(surface_map: Path, *, surface_limit: int = 0) -> tuple[list[dict], list[dict], list[dict]]:
    sources: list[dict] = []
    sessions: list[dict] = []
    primitives: list[dict] = []
    for surface in _surface_rows(surface_map, limit=surface_limit):
        sources.append(_source_candidate(surface))
        for opp in surface.get("primitive_opportunities") or []:
            sessions.append(_session_spec(surface, str(opp)))
            primitives.append(_primitive_draft(surface, str(opp)))
    return sources, sessions, primitives


def _public_use_case_rows(seed_path: Path, *, limit: int = 0) -> list[dict[str, Any]]:
    rows = _read_jsonl(seed_path)
    rows = [r for r in rows if r.get("source_kind") == "curated_public_codegen_use_case"]
    if limit > 0:
        return rows[:limit]
    return rows


def _public_use_case_source_candidate(row: dict[str, Any]) -> dict[str, Any]:
    use_case_id = _slug(str(row.get("id") or row.get("title") or "use-case"))
    primitive_opportunities = [str(p) for p in row.get("expected_primitives") or []]
    task_family = str(row.get("task_family") or "software")
    industry = str(row.get("industry") or "cross_industry")
    return {
        "record_type": "source_candidate",
        "candidate_id": f"source:public-codegen-use-case:{use_case_id}",
        "source_surface_id": "public-codegen-use-case-seeds",
        "source_use_case_id": use_case_id,
        "source_kind": "curated_public_codegen_use_case",
        "source_type": "likely_llm_codegen_use_case",
        "title": row.get("title") or use_case_id,
        "intent": row.get("intent"),
        "task_family": task_family,
        "industry": industry,
        "expected_template": row.get("expected_template"),
        "primitive_opportunities": primitive_opportunities,
        "observed_reinvention_patterns": row.get("observed_reinvention_patterns") or [],
        "source_urls": row.get("source_urls") or [],
        "source_status": row.get("source_status") or "curated_seed_needs_live_source",
        "license_status": row.get("license_status") or "curated_metadata",
        "discovery_queries": [
            f"GitHub/Kaggle/web search: {task_family} {row.get('title') or use_case_id}",
            f"public project scan: {row.get('intent') or use_case_id}",
        ],
        "tags": ["codegen-use-case", task_family, industry],
        "status": "candidate",
        "trust": row.get("trust") or "candidate",
        "readiness": "R2_surface_known",
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _public_session_shape(row: dict[str, Any]) -> list[str]:
    task_family = str(row.get("task_family") or "")
    if task_family in {"data_science", "computer_vision", "nlp"}:
        return [
            "intent",
            "dataset_or_competition_brief",
            "schema_or_manifest_inspection",
            "baseline_implementation",
            "metric_or_submission_loop",
            "registry_route_detection",
            "proof_or_eval",
            "primitive_candidate_extraction",
        ]
    if task_family in {"web_scraping", "entity_resolution", "workflow_automation"}:
        return [
            "intent",
            "source_discovery",
            "existing_route_search",
            "implementation_or_adapter",
            "validation_gate",
            "artifact_emit",
            "registry_memory_update",
        ]
    return [
        "intent",
        "repo_or_source_inspection",
        "agent_attempt",
        "reinvention_or_context_waste_signal",
        "candidate_route_search",
        "compiler_or_review_gate",
        "proof_or_eval",
        "registry_memory_update",
    ]


def _public_use_case_session_spec(row: dict[str, Any]) -> dict[str, Any]:
    use_case_id = _slug(str(row.get("id") or row.get("title") or "use-case"))
    return {
        "record_type": "synthetic_session_spec",
        "session_spec_id": f"synth:public-codegen-use-case:{use_case_id}",
        "source_kind": "synthetic_from_curated_public_codegen_use_case",
        "source_candidate": f"source:public-codegen-use-case:{use_case_id}",
        "source_surface_id": "public-codegen-use-case-seeds",
        "source_use_case_id": use_case_id,
        "title": f"AIDevObserver demo session — {row.get('title') or use_case_id}",
        "intent": row.get("intent"),
        "expected_template": row.get("expected_template"),
        "expected_primitives": row.get("expected_primitives") or [],
        "observed_reinvention_patterns": row.get("observed_reinvention_patterns") or [],
        "expected_long_session_shape": _public_session_shape(row),
        "expected_findings": [
            "missed_existing_primitive",
            "missed_template_route",
            "wasted_context",
            "candidate_reuse_path",
        ],
        "source_attribution_required": True,
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "license_status": row.get("license_status") or "curated_metadata",
        "status": "candidate",
        "serves_truth": False,
        "created_at": _utc(),
    }


def _contract_for_primitive_name(primitive: str, row: dict[str, Any]) -> dict[str, str]:
    name = primitive.lower()
    if name.startswith("web.discover"):
        return {"input": "QuerySpec", "output": "SourcePageSet"}
    if name.startswith("web.fetch"):
        return {"input": "SourcePageSet", "output": "DocumentSet"}
    if "extract" in name and "document" not in name:
        return {"input": "DocumentSet", "output": "RawRecordSet"}
    if name.startswith("document.parse"):
        return {"input": "DocumentArtifact", "output": "ParsedDocumentArtifact"}
    if name.startswith("document.extract"):
        return {"input": "ParsedDocumentArtifact", "output": "RawSchemaFields"}
    if name.startswith("schema.validate"):
        return {"input": "NormalizedRecord", "output": "ValidatedRecord"}
    if name.startswith("dataset.inspect"):
        return {"input": "DatasetArtifact", "output": "SchemaReport"}
    if name.startswith("dataset.infer"):
        return {"input": "DatasetArtifact", "output": "ColumnRoleMap"}
    if name.startswith("table.train_valid_split"):
        return {"input": "FeatureTableArtifact", "output": "TrainTestSplitArtifact"}
    if name.startswith("table."):
        return {"input": "TableArtifact", "output": "TableArtifact"}
    if name.startswith("model.train") or name.startswith("image.train") or name.startswith("text.train"):
        return {"input": "TrainTestSplitArtifact", "output": "ModelArtifact"}
    if name.startswith("metric.") or "evaluate" in name:
        return {"input": "ModelArtifact+EvalDatasetArtifact", "output": "EvalReport"}
    if name.startswith("submission."):
        return {"input": "PredictionSet", "output": "SubmissionArtifact"}
    if name.startswith("image.read"):
        return {"input": "ImageDatasetArtifact", "output": "ImageManifest"}
    if name.startswith("image.resize") or name.startswith("image.augment"):
        return {"input": "ImageDatasetArtifact", "output": "ImageDatasetArtifact"}
    if name.startswith("text.clean"):
        return {"input": "TextDatasetArtifact", "output": "CleanTextDatasetArtifact"}
    if name.startswith("text.vectorize") or name.startswith("text.embed"):
        return {"input": "CleanTextDatasetArtifact", "output": "FeatureTableArtifact"}
    if name.startswith("api.validate"):
        return {"input": "ApiRequest", "output": "ValidatedApiRequest"}
    if name.startswith("api.emit"):
        return {"input": "PolicyDecision+Receipt", "output": "ApiResponse"}
    if name.startswith("db.persist"):
        return {"input": "PolicyDecision", "output": "Receipt"}
    if name.startswith("output.emit") or name.startswith("answer.emit") or name.endswith(".emit_report"):
        return {"input": "ValidatedRecord", "output": "OutputArtifact"}
    if "validate" in name:
        return {"input": "CandidateRecord", "output": "ValidatedRecord"}
    if "normalize" in name or "clean" in name:
        return {"input": "RawRecord", "output": "NormalizedRecord"}
    if "score" in name or "classify" in name:
        return {"input": "NormalizedRecord", "output": "ScoredRecord"}
    if "route" in name:
        return {"input": "ValidatedRecord", "output": "RouteDecision"}
    if "load" in name or "parse" in name or "read" in name:
        return {"input": "SourceArtifact", "output": "ParsedArtifact"}
    if "write" in name or "publish" in name or "upsert" in name:
        return {"input": "Artifact", "output": "Receipt"}
    task_family = str(row.get("task_family") or "software")
    return {"input": f"{_slug(task_family).title().replace('-', '')}Evidence", "output": "PrimitiveRecordDraft"}


def _effects_for_primitive_name(primitive: str, row: dict[str, Any]) -> list[str]:
    name = primitive.lower()
    if "secret" in name:
        return []
    if any(part in name for part in ("fetch", "discover", "enrich", "health", "search_topk")):
        return ["net.read"]
    if any(part in name for part in ("persist", "upsert")):
        return ["db.write"]
    if any(part in name for part in ("publish", "write", "apply_refactor")):
        return ["fs.write"]
    if any(part in name for part in ("run_", "typecheck", "pytest", "train")):
        return ["subprocess"] if "model.train" not in name else ["cpu"]
    if any(part in name for part in ("embed", "classify_bounded", "extract_schema_bounded", "run_candidate")):
        return ["model.call"]
    return []


def _public_use_case_primitive_drafts(row: dict[str, Any]) -> list[dict[str, Any]]:
    use_case_id = _slug(str(row.get("id") or row.get("title") or "use-case"))
    source_candidate = f"source:public-codegen-use-case:{use_case_id}"
    drafts: list[dict[str, Any]] = []
    for primitive in row.get("expected_primitives") or []:
        primitive_name = str(primitive)
        primitive_slug = _slug(primitive_name)
        contract = _contract_for_primitive_name(primitive_name, row)
        candidate = {
            "record_type": "primitive_draft",
            "primitive_id": f"prim:candidate:public-codegen-use-case:{use_case_id}:{primitive_slug}",
            "slug": primitive_name,
            "source_candidate": source_candidate,
            "source_surface_id": "public-codegen-use-case-seeds",
            "source_use_case_id": use_case_id,
            "title": f"{primitive_name} candidate primitive",
            "contract": contract,
            "expected_template": row.get("expected_template"),
            "task_family": row.get("task_family"),
            "industry": row.get("industry"),
            "effects": _effects_for_primitive_name(primitive_name, row),
            "memory": "artifact" if "Artifact" in contract["input"] or "Artifact" in contract["output"] else "inline",
            "cache": "content_hash",
            "trust": "candidate",
            "readiness": "R2_surface_known",
            "proof_requirements": [
                "live_source_attribution_gate",
                "license_gate",
                "redaction_gate",
                "contract_review",
                "demo_session_review",
                "observer_benchmark_check",
            ],
            "remix_tools": ["map_sequence", "field_rename", "output_wrapper"],
            "raw_source_republish_allowed": False,
            "public_export_allowed": False,
            "serves_truth": False,
            "created_at": _utc(),
        }
        drafts.append(_finalize_primitive_candidate(
            candidate,
            row,
            fallback_candidate=source_candidate,
        ))
    return drafts


def _public_use_case_derived_records(seed_path: Path, *, use_case_limit: int = 0) -> tuple[list[dict], list[dict], list[dict]]:
    sources: list[dict] = []
    sessions: list[dict] = []
    primitives: list[dict] = []
    for row in _public_use_case_rows(seed_path, limit=use_case_limit):
        sources.append(_public_use_case_source_candidate(row))
        sessions.append(_public_use_case_session_spec(row))
        primitives.extend(_public_use_case_primitive_drafts(row))
    return sources, sessions, primitives


def _source_discovery_seed_rows(seed_path: Path, *, limit: int = 0) -> list[dict[str, Any]]:
    rows = _read_jsonl(seed_path)
    rows = [row for row in rows if row.get("serves_truth") is False]
    if limit > 0:
        return rows[:limit]
    return rows


def _source_discovery_seed_source_candidate(row: dict[str, Any]) -> dict[str, Any]:
    seed_id = _slug(str(row.get("id") or row.get("topic_family") or "source-discovery-seed"))
    search_terms = [str(term) for term in row.get("search_terms") or []]
    outputs = [str(output) for output in row.get("candidate_outputs") or []]
    surface_id = str(row.get("surface_id") or "source-discovery-search-seeds")
    return {
        "record_type": "source_candidate",
        "candidate_id": f"source:source-discovery-search-seed:{seed_id}",
        "source_surface_id": surface_id,
        "source_kind": "curated_source_discovery_search_seed",
        "source_type": "source_discovery_search_terms",
        "topic_family": row.get("topic_family"),
        "title": f"Source discovery search seed — {seed_id}",
        "discovery_queries": search_terms,
        "primitive_opportunities": outputs,
        "source_policy": row.get("source_policy") or "metadata_first",
        "license_status": "curated_metadata_needs_downstream_source_review",
        "redaction_status": "search_terms_only_no_raw_source",
        "source_status": "curated_search_terms",
        "tags": ["search-seed", str(row.get("topic_family") or ""), surface_id],
        "trust": "candidate",
        "readiness": "R1_indexed",
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _source_discovery_seed_session_spec(row: dict[str, Any]) -> dict[str, Any]:
    seed_id = _slug(str(row.get("id") or row.get("topic_family") or "source-discovery-seed"))
    outputs = [str(output) for output in row.get("candidate_outputs") or []]
    return {
        "record_type": "synthetic_session_spec",
        "session_spec_id": f"synth:source-discovery-search-seed:{seed_id}",
        "source_kind": "synthetic_from_source_discovery_search_seed",
        "source_candidate": f"source:source-discovery-search-seed:{seed_id}",
        "source_surface_id": row.get("surface_id") or "source-discovery-search-seeds",
        "title": f"AIDevObserver source-discovery session — {seed_id}",
        "intent": "Use curated source-discovery terms to find real public metadata, then produce primitive opportunities and route candidates without republishing raw source.",
        "expected_long_session_shape": [
            "seed_query_review",
            "metadata_source_discovery",
            "license_and_redaction_gate",
            "primitive_opportunity_generation",
            "route_template_gap_update",
            "benchmark_fixture_candidate",
        ],
        "expected_findings": [
            "new_source_surface_candidate",
            "primitive_gap_from_public_demand",
            "candidate_template_route",
            "metadata_only_until_review",
        ],
        "expected_outputs": outputs,
        "source_attribution_required": True,
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "license_status": "curated_metadata_needs_downstream_source_review",
        "status": "candidate",
        "serves_truth": False,
        "created_at": _utc(),
    }


def _source_discovery_seed_primitive_drafts(row: dict[str, Any]) -> list[dict[str, Any]]:
    seed_id = _slug(str(row.get("id") or row.get("topic_family") or "source-discovery-seed"))
    source_candidate = f"source:source-discovery-search-seed:{seed_id}"
    drafts: list[dict[str, Any]] = []
    for output in row.get("candidate_outputs") or []:
        output_name = str(output)
        candidate = {
            "record_type": "primitive_opportunity",
            "candidate_stage": "primitive_opportunity",
            "primitive_id": f"prim:candidate:source-discovery:{seed_id}:{_slug(output_name)}",
            "slug": f"source_discovery.{seed_id}.{_slug(output_name)}",
            "source_candidate": source_candidate,
            "source_surface_id": row.get("surface_id") or "source-discovery-search-seeds",
            "title": f"{output_name} from source-discovery seed `{seed_id}`",
            "contract": {
                "input": "PublicSourceMetadata",
                "output": _edge_type_name(output_name),
            },
            "effects": ["net.read"],
            "memory": "artifact",
            "cache": "content_hash",
            "trust": "candidate",
            "readiness": "R1_indexed",
            "proof_requirements": [
                "downstream_source_license_gate",
                "source_attribution_gate",
                "metadata_contract_review",
                "redaction_gate",
                "observer_reuse_benchmark",
            ],
            "remix_tools": ["map_sequence", "output_wrapper", "provenance_wrapper"],
            "raw_source_republish_allowed": False,
            "public_export_allowed": False,
            "serves_truth": False,
            "created_at": _utc(),
        }
        drafts.append(_finalize_primitive_candidate(candidate, row, fallback_candidate=source_candidate))
    return drafts


def _source_discovery_seed_derived_records(seed_path: Path, *, limit: int = 0) -> tuple[list[dict], list[dict], list[dict]]:
    sources: list[dict] = []
    sessions: list[dict] = []
    primitives: list[dict] = []
    for row in _source_discovery_seed_rows(seed_path, limit=limit):
        sources.append(_source_discovery_seed_source_candidate(row))
        sessions.append(_source_discovery_seed_session_spec(row))
        primitives.extend(_source_discovery_seed_primitive_drafts(row))
    return sources, sessions, primitives


def _search_scope_rows(scope_path: Path, *, limit: int = 0) -> list[dict[str, Any]]:
    rows = _read_jsonl(scope_path)
    rows = [row for row in rows if row.get("serves_truth") is False]
    if limit > 0:
        return rows[:limit]
    return rows


def _search_scope_queries(row: dict[str, Any]) -> list[dict[str, Any]]:
    providers = [str(provider) for provider in row.get("providers") or []]
    queries: list[dict[str, Any]] = []
    for item in row.get("queries") or []:
        if not isinstance(item, dict):
            continue
        lang = str(item.get("lang") or "und")
        language = str(item.get("language") or lang)
        for query in item.get("terms") or []:
            text = " ".join(str(query).split())
            if not text:
                continue
            queries.append({
                "lang": lang,
                "language": language,
                "query": text,
                "providers": providers,
                "query_digest": f"sha256:{_sha(text, n=24)}",
            })
    return queries


def _search_scope_source_candidate(row: dict[str, Any]) -> dict[str, Any]:
    scope_id = _slug(str(row.get("id") or row.get("topic_family") or "search-scope"))
    queries = _search_scope_queries(row)
    providers = [str(provider) for provider in row.get("providers") or []]
    outputs = [str(output) for output in row.get("candidate_outputs") or []]
    languages = sorted({str(item.get("lang") or "und") for item in queries})
    return {
        "record_type": "source_candidate",
        "candidate_id": f"source:multilingual-search-scope:{scope_id}",
        "source_surface_id": row.get("surface_id") or "multilingual-search-scopes",
        "source_kind": "curated_multilingual_search_scope",
        "source_type": "multilingual_multi_provider_search_scope",
        "topic_family": row.get("topic_family"),
        "title": row.get("title") or f"Multilingual search scope — {scope_id}",
        "providers": providers,
        "languages": languages,
        "multilingual_queries": queries,
        "discovery_queries": [str(item["query"]) for item in queries],
        "primitive_opportunities": outputs,
        "source_policy": row.get("source_policy") or "metadata_first_search_scope",
        "license_status": "curated_metadata_needs_downstream_source_review",
        "redaction_status": "search_queries_only_no_raw_source",
        "source_status": "curated_multilingual_search_scope",
        "tags": ["multilingual-search", "search-scope", str(row.get("topic_family") or ""), *providers],
        "trust": "candidate",
        "readiness": "R1_indexed",
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _search_scope_session_spec(row: dict[str, Any]) -> dict[str, Any]:
    scope_id = _slug(str(row.get("id") or row.get("topic_family") or "search-scope"))
    providers = [str(provider) for provider in row.get("providers") or []]
    outputs = [str(output) for output in row.get("candidate_outputs") or []]
    return {
        "record_type": "synthetic_session_spec",
        "session_spec_id": f"synth:multilingual-search-scope:{scope_id}",
        "source_kind": "synthetic_from_multilingual_search_scope",
        "source_candidate": f"source:multilingual-search-scope:{scope_id}",
        "source_surface_id": row.get("surface_id") or "multilingual-search-scopes",
        "title": f"AIDevObserver multilingual search session — {scope_id}",
        "intent": "Run multi-provider, multilingual source discovery for public metadata, then convert high-signal results into primitive opportunities without storing raw source bodies.",
        "providers": providers,
        "expected_outputs": outputs,
        "expected_long_session_shape": [
            "multilingual_query_expansion",
            "provider_specific_search",
            "metadata_result_normalization",
            "license_and_redaction_gate",
            "primitive_opportunity_generation",
            "source_surface_seed_update",
            "benchmark_fixture_candidate",
        ],
        "expected_findings": [
            "non_english_source_gap",
            "provider_specific_result_gap",
            "candidate_template_route",
            "metadata_only_until_review",
        ],
        "source_attribution_required": True,
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "license_status": "curated_metadata_needs_downstream_source_review",
        "status": "candidate",
        "serves_truth": False,
        "created_at": _utc(),
    }


def _search_scope_primitive_drafts(row: dict[str, Any]) -> list[dict[str, Any]]:
    scope_id = _slug(str(row.get("id") or row.get("topic_family") or "search-scope"))
    source_candidate = f"source:multilingual-search-scope:{scope_id}"
    providers = [str(provider) for provider in row.get("providers") or []]
    languages = sorted({str(item.get("lang") or "und") for item in _search_scope_queries(row)})
    drafts: list[dict[str, Any]] = []
    for output in row.get("candidate_outputs") or []:
        output_name = str(output)
        candidate = {
            "record_type": "primitive_opportunity",
            "candidate_stage": "primitive_opportunity",
            "primitive_id": f"prim:candidate:multilingual-search:{scope_id}:{_slug(output_name)}",
            "slug": f"multilingual_search.{scope_id}.{_slug(output_name)}",
            "source_candidate": source_candidate,
            "source_surface_id": row.get("surface_id") or "multilingual-search-scopes",
            "title": f"{output_name} from multilingual search scope `{scope_id}`",
            "contract": {
                "input": "MultilingualSearchScope",
                "output": _edge_type_name(output_name),
            },
            "providers": providers,
            "languages": languages,
            "effects": ["net.read"],
            "memory": "artifact",
            "cache": "content_hash",
            "trust": "candidate",
            "readiness": "R1_indexed",
            "proof_requirements": [
                "search_provider_terms_review",
                "downstream_source_license_gate",
                "source_attribution_gate",
                "metadata_contract_review",
                "redaction_gate",
                "no_raw_result_body_republish",
                "observer_reuse_benchmark",
            ],
            "remix_tools": ["map_sequence", "output_wrapper", "provenance_wrapper", "translation_key_wrapper"],
            "raw_source_republish_allowed": False,
            "public_export_allowed": False,
            "serves_truth": False,
            "created_at": _utc(),
        }
        drafts.append(_finalize_primitive_candidate(candidate, row, fallback_candidate=source_candidate))
    return drafts


def _search_scope_derived_records(scope_path: Path, *, limit: int = 0) -> tuple[list[dict], list[dict], list[dict]]:
    sources: list[dict] = []
    sessions: list[dict] = []
    primitives: list[dict] = []
    for row in _search_scope_rows(scope_path, limit=limit):
        sources.append(_search_scope_source_candidate(row))
        sessions.append(_search_scope_session_spec(row))
        primitives.extend(_search_scope_primitive_drafts(row))
    return sources, sessions, primitives


def _microsurface_rows(seed_path: Path, *, limit: int = 0) -> list[dict[str, Any]]:
    rows = _read_jsonl(seed_path)
    rows = [r for r in rows if r.get("source_status") == "curated_microsurface_seed"]
    if limit > 0:
        return rows[:limit]
    return rows


def _microsurface_source_candidate(row: dict[str, Any]) -> dict[str, Any]:
    microsurface_id = _slug(str(row.get("id") or row.get("title") or "microsurface"))
    primitives = [str(p) for p in row.get("candidate_primitives") or []]
    family = str(row.get("surface_family") or "generic_product_surface")
    return {
        "record_type": "source_candidate",
        "candidate_id": f"source:microsurface:{microsurface_id}",
        "source_surface_id": "microsurface-atlas",
        "source_microsurface_id": microsurface_id,
        "source_kind": "curated_microsurface_seed",
        "source_type": "product_platform_microsurface",
        "surface_family": family,
        "title": row.get("title") or microsurface_id,
        "platform_examples": row.get("platform_examples") or [],
        "common_objects": row.get("common_objects") or [],
        "common_actions": row.get("common_actions") or [],
        "observed_reinvention_patterns": row.get("reinvention_patterns") or [],
        "candidate_templates": row.get("candidate_templates") or [],
        "primitive_opportunities": primitives,
        "industries": row.get("industries") or [],
        "modalities": row.get("modalities") or [],
        "effects": row.get("effects") or [],
        "artifact_policy": row.get("artifact_policy"),
        "source_status": "curated_microsurface_seed",
        "license_status": row.get("license_status") or "curated_metadata",
        "discovery_queries": [
            f"top app microsurface scan: {family} {row.get('title') or microsurface_id}",
            f"workflow/component registry scan: {' '.join(primitives[:4])}",
        ],
        "tags": ["microsurface", family, *(str(i) for i in row.get("industries") or [])],
        "status": "candidate",
        "trust": row.get("trust") or "candidate",
        "readiness": "R2_surface_known",
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _microsurface_session_spec(row: dict[str, Any]) -> dict[str, Any]:
    microsurface_id = _slug(str(row.get("id") or row.get("title") or "microsurface"))
    return {
        "record_type": "synthetic_session_spec",
        "session_spec_id": f"synth:microsurface:{microsurface_id}",
        "source_kind": "synthetic_from_curated_microsurface_seed",
        "source_candidate": f"source:microsurface:{microsurface_id}",
        "source_surface_id": "microsurface-atlas",
        "source_microsurface_id": microsurface_id,
        "title": f"AIDevObserver microsurface session — {row.get('title') or microsurface_id}",
        "intent": f"Build or modify a product microsurface for {row.get('title') or microsurface_id}, while routing repeated objects/actions to existing primitives.",
        "surface_family": row.get("surface_family"),
        "candidate_templates": row.get("candidate_templates") or [],
        "expected_primitives": row.get("candidate_primitives") or [],
        "observed_reinvention_patterns": row.get("reinvention_patterns") or [],
        "expected_long_session_shape": [
            "product_surface_request",
            "object_and_action_discovery",
            "existing_component_or_primitive_search",
            "agent_attempt_or_generation",
            "reinvention_detection",
            "template_route_reuse",
            "proof_or_quality_gate",
            "registry_memory_update",
        ],
        "expected_findings": [
            "missed_existing_component",
            "missed_template_route",
            "wasted_context",
            "candidate_microsurface_primitive_family",
        ],
        "source_attribution_required": False,
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "license_status": row.get("license_status") or "curated_metadata",
        "status": "candidate",
        "serves_truth": False,
        "created_at": _utc(),
    }


def _microsurface_contract_for_primitive(primitive: str, row: dict[str, Any]) -> dict[str, str]:
    name = primitive.lower()
    if any(part in name for part in ("validate", "verify", "check")):
        return {"input": "CandidateSurfaceState", "output": "ValidatedSurfaceState"}
    if any(part in name for part in ("create", "send", "persist", "write", "publish", "upsert", "record")):
        return {"input": "ValidatedSurfaceState", "output": "Receipt"}
    if any(part in name for part in ("render", "emit", "generate", "preview", "export")):
        return {"input": "SurfaceState", "output": "OutputArtifact"}
    if any(part in name for part in ("classify", "score", "rank", "route", "suggest")):
        return {"input": "NormalizedSurfaceState", "output": "DecisionRecord"}
    if any(part in name for part in ("normalize", "parse", "extract", "load", "lookup", "read", "list", "search")):
        return {"input": "RawSurfaceInput", "output": "NormalizedSurfaceState"}
    family = _slug(str(row.get("surface_family") or "microsurface")).title().replace("-", "")
    return {"input": f"{family}Input", "output": f"{family}Record"}


def _microsurface_primitive_drafts(row: dict[str, Any]) -> list[dict[str, Any]]:
    microsurface_id = _slug(str(row.get("id") or row.get("title") or "microsurface"))
    source_candidate = f"source:microsurface:{microsurface_id}"
    drafts: list[dict[str, Any]] = []
    for primitive in row.get("candidate_primitives") or []:
        primitive_name = str(primitive)
        contract = _microsurface_contract_for_primitive(primitive_name, row)
        candidate = {
            "record_type": "primitive_draft",
            "primitive_id": f"prim:candidate:microsurface:{microsurface_id}:{_slug(primitive_name)}",
            "slug": primitive_name,
            "source_candidate": source_candidate,
            "source_surface_id": "microsurface-atlas",
            "source_microsurface_id": microsurface_id,
            "title": f"{primitive_name} microsurface primitive candidate",
            "surface_family": row.get("surface_family"),
            "contract": contract,
            "candidate_templates": row.get("candidate_templates") or [],
            "industries": row.get("industries") or [],
            "modalities": row.get("modalities") or [],
            "effects": row.get("effects") or [],
            "memory": "artifact" if "Artifact" in contract["input"] or "Artifact" in contract["output"] else "inline",
            "cache": "content_hash",
            "trust": "candidate",
            "readiness": "R2_surface_known",
            "proof_requirements": [
                "microsurface_contract_review",
                "representative_app_route_review",
                "privacy_boundary_review",
                "example_session_review",
                "observer_benchmark_check",
            ],
            "remix_tools": ["map_sequence", "field_rename", "output_wrapper", "cache_wrapper"],
            "raw_source_republish_allowed": False,
            "public_export_allowed": False,
            "serves_truth": False,
            "created_at": _utc(),
        }
        drafts.append(_finalize_primitive_candidate(
            candidate,
            row,
            fallback_candidate=source_candidate,
        ))
    return drafts


def _microsurface_derived_records(seed_path: Path, *, microsurface_limit: int = 0) -> tuple[list[dict], list[dict], list[dict]]:
    sources: list[dict] = []
    sessions: list[dict] = []
    primitives: list[dict] = []
    for row in _microsurface_rows(seed_path, limit=microsurface_limit):
        sources.append(_microsurface_source_candidate(row))
        sessions.append(_microsurface_session_spec(row))
        primitives.extend(_microsurface_primitive_drafts(row))
    return sources, sessions, primitives


def _github_search_items(
    query: str,
    *,
    result_limit: int,
    timeout_seconds: int,
    token: str | None,
) -> list[dict[str, Any]]:
    per_page = max(1, min(100, int(result_limit)))
    url = f"{GITHUB_CODE_SEARCH_API}?{urllib.parse.urlencode({'q': query, 'per_page': per_page})}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": GITHUB_USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    items = payload.get("items") if isinstance(payload, dict) else []
    return [item for item in items if isinstance(item, dict)]


def _github_repository_search_items(
    query: str,
    *,
    result_limit: int,
    timeout_seconds: int,
    token: str | None,
) -> list[dict[str, Any]]:
    per_page = max(1, min(100, int(result_limit)))
    url = f"{GITHUB_REPOSITORY_SEARCH_API}?{urllib.parse.urlencode({'q': query, 'per_page': per_page})}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": GITHUB_USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    items = payload.get("items") if isinstance(payload, dict) else []
    return [item for item in items if isinstance(item, dict)]


def _github_source_candidate_from_item(item: dict[str, Any], *, query: str) -> dict[str, Any]:
    repo = item.get("repository") if isinstance(item.get("repository"), dict) else {}
    full_name = str(repo.get("full_name") or "unknown/repo")
    path = str(item.get("path") or item.get("name") or "unknown")
    html_url = str(item.get("html_url") or "")
    digest = _sha(f"{full_name}:{path}:{item.get('sha') or html_url}", n=24)
    workflow_like = _github_item_is_workflow_candidate(item, query=query)
    n8n_like = _github_item_is_n8n_candidate(item, query=query)
    source_kind = "public_github_n8n_workflow_candidate" if n8n_like else (
        "public_github_workflow_candidate" if workflow_like else "public_github_session_candidate"
    )
    opportunities = (
        [
            "n8n_workflow_metadata_normalizer",
            "n8n_workflow_template_miner",
            "n8n_node_to_primitive_edge_cards",
            "workflow_slot_extractor",
            "workflow_fixture_generator",
        ]
        if n8n_like
        else [
            "workflow_template_miner",
            "workflow_step_to_primitive_edge_cards",
            "workflow_fixture_generator",
        ]
        if workflow_like
        else [
            "public_session_transcript_normalizer",
            "agent_trajectory_miner",
            "session_review_benchmark_fixture",
        ]
    )
    tags = (
        ["github", "n8n", "workflow", "template", "automation"]
        if n8n_like
        else ["github", "workflow", "template", "automation"]
        if workflow_like
        else ["github", "public-session-candidate", "ai-coding-session"]
    )
    return {
        "record_type": "source_candidate",
        "candidate_id": f"source:{source_kind.replace('_', '-')}:{digest}",
        "source_surface_id": "surface-github",
        "source_kind": source_kind,
        "source_type": "developer_ecosystem",
        "title": f"GitHub public {'n8n workflow' if n8n_like else 'workflow' if workflow_like else 'session'} candidate — {full_name}:{path}",
        "url": html_url,
        "repo_url": repo.get("html_url"),
        "repo_full_name": full_name,
        "repo_id": repo.get("id"),
        "path": path,
        "file_name": item.get("name"),
        "source_sha": item.get("sha"),
        "search_query_digest": f"sha256:{_sha(query, n=24)}",
        "search_query_label": query,
        "license_status": "needs_review",
        "redaction_status": "not_fetched",
        "source_status": "metadata_discovered_not_downloaded",
        "primitive_opportunities": opportunities,
        "discovery_queries": [query],
        "tags": tags,
        "status": "candidate",
        "trust": "candidate",
        "readiness": "R1_indexed",
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _github_item_is_n8n_candidate(item: dict[str, Any], *, query: str) -> bool:
    text = " ".join(
        str(value)
        for value in (
            query,
            item.get("path"),
            item.get("name"),
            item.get("html_url"),
            (item.get("repository") or {}).get("full_name") if isinstance(item.get("repository"), dict) else "",
            (item.get("repository") or {}).get("description") if isinstance(item.get("repository"), dict) else "",
        )
        if value
    ).lower()
    return "n8n" in text or "n8n-nodes-base" in text


def _github_item_is_workflow_candidate(item: dict[str, Any], *, query: str) -> bool:
    text = " ".join(
        str(value)
        for value in (
            query,
            item.get("path"),
            item.get("name"),
            item.get("html_url"),
            (item.get("repository") or {}).get("full_name") if isinstance(item.get("repository"), dict) else "",
            (item.get("repository") or {}).get("description") if isinstance(item.get("repository"), dict) else "",
        )
        if value
    ).lower()
    return any(token in text for token in ("workflow", "template", "dag", "automation", "nodes", "connections"))


def _github_repository_source_candidate_from_item(item: dict[str, Any], *, query: str) -> dict[str, Any]:
    full_name = str(item.get("full_name") or "unknown/repo")
    html_url = str(item.get("html_url") or "")
    license_obj = item.get("license") if isinstance(item.get("license"), dict) else {}
    digest = _sha(f"{full_name}:{item.get('id')}:{html_url}", n=24)
    n8n_like = _github_item_is_n8n_candidate(item, query=query)
    workflow_like = _github_item_is_workflow_candidate(item, query=query)
    source_kind = "public_github_n8n_repository_candidate" if n8n_like else (
        "public_github_workflow_repository_candidate" if workflow_like else "public_github_repository_candidate"
    )
    opportunities = (
        [
            "n8n_workflow_repository_discovery",
            "n8n_template_pack_miner",
            "workflow_step_template_miner",
            "license_aware_workflow_source_ref",
        ]
        if n8n_like
        else [
            "workflow_template_repository_discovery",
            "workflow_step_template_miner",
            "license_aware_workflow_source_ref",
        ]
        if workflow_like
        else [
            "public_repo_session_artifact_discovery",
            "agent_trajectory_miner",
            "workflow_template_miner",
        ]
    )
    tags = (
        ["github", "n8n", "workflow", "repository", "automation"]
        if n8n_like
        else ["github", "workflow", "repository", "automation"]
        if workflow_like
        else ["github", "public-repository-candidate", "ai-coding-session"]
    )
    return {
        "record_type": "source_candidate",
        "candidate_id": f"source:{source_kind.replace('_', '-')}:{digest}",
        "source_surface_id": "surface-github",
        "source_kind": source_kind,
        "source_type": "developer_ecosystem",
        "title": f"GitHub {'n8n workflow repository' if n8n_like else 'workflow repository' if workflow_like else 'repository'} candidate — {full_name}",
        "url": html_url,
        "repo_url": html_url,
        "repo_full_name": full_name,
        "repo_id": item.get("id"),
        "description": _redact(str(item.get("description") or ""))[:500],
        "reported_license_spdx": license_obj.get("spdx_id"),
        "search_query_digest": f"sha256:{_sha(query, n=24)}",
        "search_query_label": query,
        "license_status": "needs_review",
        "redaction_status": "not_fetched",
        "source_status": "repository_metadata_discovered_not_downloaded",
        "primitive_opportunities": opportunities,
        "discovery_queries": [query],
        "tags": tags,
        "status": "candidate",
        "trust": "candidate",
        "readiness": "R1_indexed",
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _github_session_spec_from_source(source: dict[str, Any]) -> dict[str, Any]:
    cid = str(source.get("candidate_id") or "")
    sid = cid.rsplit(":", 1)[-1] if ":" in cid else _sha(cid, n=24)
    location = str(source.get("repo_full_name") or "unknown/repo")
    if source.get("path"):
        location = f"{location}:{source.get('path')}"
    workflow_like = "workflow" in str(source.get("source_kind") or "") or "n8n" in str(source.get("source_kind") or "")
    return {
        "record_type": "synthetic_session_spec",
        "session_spec_id": f"synth:github-public-session:{sid}",
        "source_kind": "synthetic_from_public_github_workflow_metadata" if workflow_like else "synthetic_from_public_github_metadata",
        "source_candidate": cid,
        "source_surface_id": "surface-github",
        "title": f"Public GitHub session derivative — {location}",
        "intent": (
            "After license and redaction review, distill this public workflow-like artifact into reusable workflow/session fixtures and primitive route candidates."
            if workflow_like
            else "After license and redaction review, distill this public session-like artifact into a synthetic AIDevObserver replay and benchmark fixture."
        ),
        "expected_long_session_shape": [
            "public_metadata_review",
            "license_gate",
            "redaction_gate",
            "transcript_or_trajectory_normalization",
            "action_extraction",
            "registry_route_search",
            "benchmark_fixture_emit",
        ],
        "expected_findings": [
            "missed_existing_primitive",
            "wasted_context",
            "agentic_loop",
            "candidate_template_route",
        ],
        "source_attribution_required": True,
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "license_status": source.get("license_status"),
        "status": "candidate",
        "serves_truth": False,
        "created_at": _utc(),
    }


def _github_primitive_draft_from_source(source: dict[str, Any]) -> dict[str, Any]:
    cid = str(source.get("candidate_id") or "")
    sid = cid.rsplit(":", 1)[-1] if ":" in cid else _sha(cid, n=24)
    source_kind = str(source.get("source_kind") or "")
    is_repo = "repository" in source_kind
    workflow_like = "workflow" in source_kind or "n8n" in source_kind
    candidate = {
        "record_type": "primitive_draft",
        "primitive_id": f"prim:candidate:github-public:{sid}",
        "slug": (
            "github.public_workflow_metadata_to_template_route"
            if workflow_like
            else "github.public_repository_or_session_metadata_to_candidate_route"
            if is_repo
            else "github.public_session_metadata_to_synthetic_session"
        ),
        "source_candidate": cid,
        "source_surface_id": "surface-github",
        "title": (
            "GitHub public workflow metadata to candidate template route"
            if workflow_like
            else "GitHub public repository/session metadata to candidate route"
        ),
        "contract": {
            "input": "PublicGitHubWorkflowMetadata" if workflow_like else "PublicGitHubMetadata",
            "output": "PipelineTemplateDraft" if workflow_like else "SyntheticSessionSpec",
        },
        "effects": ["net.read"],
        "memory": "artifact",
        "cache": "content_hash",
        "trust": "candidate",
        "readiness": "R1_indexed",
        "proof_requirements": [
            "license_gate",
            "source_attribution_gate",
            "redaction_gate",
            "raw_source_fetch_review",
            "synthetic_derivative_review",
        ],
        "remix_tools": ["output_wrapper"],
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }
    return _finalize_primitive_candidate(candidate, source, fallback_candidate=cid)


def _github_derived_records_from_items(items: Iterable[dict[str, Any]], *, query: str) -> tuple[list[dict], list[dict], list[dict]]:
    sources = [_github_source_candidate_from_item(item, query=query) for item in items]
    sessions = [_github_session_spec_from_source(source) for source in sources]
    primitives = [_github_primitive_draft_from_source(source) for source in sources]
    return sources, sessions, primitives


def _github_repository_derived_records_from_items(items: Iterable[dict[str, Any]], *, query: str) -> tuple[list[dict], list[dict], list[dict]]:
    sources = [_github_repository_source_candidate_from_item(item, query=query) for item in items]
    sessions = [_github_session_spec_from_source(source) for source in sources]
    primitives = [_github_primitive_draft_from_source(source) for source in sources]
    return sources, sessions, primitives


def _live_github_derived_records(
    *,
    query_limit: int,
    result_limit: int,
    timeout_seconds: int,
    token: str | None,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    sources: list[dict] = []
    sessions: list[dict] = []
    primitives: list[dict] = []
    errors: list[dict] = []
    queries = GITHUB_DISCOVERY_QUERIES[: max(0, int(query_limit))]
    for query in queries:
        try:
            items = _github_search_items(query, result_limit=result_limit, timeout_seconds=timeout_seconds, token=token)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append({
                "record_type": "live_github_discovery_error",
                "query_digest": f"sha256:{_sha(query, n=24)}",
                "error_type": type(exc).__name__,
                "message": str(exc)[:300],
                "serves_truth": False,
            })
            continue
        gs, gsp, gp = _github_derived_records_from_items(items, query=query)
        sources.extend(gs)
        sessions.extend(gsp)
        primitives.extend(gp)
    repo_queries = GITHUB_REPOSITORY_DISCOVERY_QUERIES[: max(0, int(query_limit))]
    for query in repo_queries:
        try:
            items = _github_repository_search_items(query, result_limit=result_limit, timeout_seconds=timeout_seconds, token=token)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append({
                "record_type": "live_github_repository_discovery_error",
                "query_digest": f"sha256:{_sha(query, n=24)}",
                "error_type": type(exc).__name__,
                "message": str(exc)[:300],
                "serves_truth": False,
            })
            continue
        gs, gsp, gp = _github_repository_derived_records_from_items(items, query=query)
        sources.extend(gs)
        sessions.extend(gsp)
        primitives.extend(gp)
    return sources, sessions, primitives, errors


def _kaggle_available() -> bool:
    return shutil.which("kaggle") is not None


def _kaggle_cmd(kind: str, *, topic: str, result_limit: int, include_page_size: bool = True) -> list[str]:
    page_size = str(max(1, min(100, int(result_limit))))
    if kind == "competitions":
        cmd = ["kaggle", "competitions", "list", "--csv", "--search", topic]
    if kind == "datasets":
        cmd = ["kaggle", "datasets", "list", "--csv", "--search", topic]
    if kind == "kernels":
        cmd = ["kaggle", "kernels", "list", "--csv", "--search", topic]
    if kind not in KAGGLE_METADATA_KINDS:
        raise ValueError(f"Unsupported Kaggle metadata kind: {kind}")
    if include_page_size:
        cmd.extend(["--page-size", page_size])
    return cmd


def _csv_rows(text: str, *, required_headers: Iterable[str] = ()) -> list[dict[str, str]]:
    raw_lines = [line for line in text.splitlines() if line.strip()]
    required = {h.lower() for h in required_headers}
    start = 0
    if required:
        for i, line in enumerate(raw_lines):
            cells = [c.strip().lower() for c in next(csv.reader([line]))]
            if required.intersection(cells):
                start = i
                break
        else:
            return []
    lines = [
        line
        for line in raw_lines[start:]
        if not line.lstrip().startswith(("Warning:", "usage:", "Traceback", "kaggle: error:"))
    ]
    if not lines:
        return []
    reader = csv.DictReader(lines)
    rows = [{str(k): str(v or "") for k, v in row.items() if k is not None} for row in reader]
    if required:
        rows = [row for row in rows if any(str(row.get(h) or "").strip() for h in required)]
    return rows


def _kaggle_cli_rows(kind: str, *, topic: str, result_limit: int, timeout_seconds: int) -> list[dict[str, str]]:
    if not _kaggle_available():
        raise RuntimeError("kaggle CLI not found")
    cmd = _kaggle_cmd(kind, topic=topic, result_limit=result_limit, include_page_size=True)
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout_seconds,
        check=False,
    )
    if proc.returncode != 0:
        if "unrecognized arguments: --page-size" not in proc.stdout:
            raise RuntimeError(proc.stdout.strip()[:500] or f"kaggle {kind} exited {proc.returncode}")
        fallback = _kaggle_cmd(kind, topic=topic, result_limit=result_limit, include_page_size=False)
        proc = subprocess.run(
            fallback,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_seconds,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stdout.strip()[:500] or f"kaggle {kind} exited {proc.returncode}")
    required = {
        "competitions": ("ref", "title"),
        "datasets": ("ref", "title", "subtitle"),
        "kernels": ("ref", "title"),
    }.get(kind, ("ref", "title"))
    return _csv_rows(proc.stdout, required_headers=required)[: max(1, int(result_limit))]


def _row_first(row: dict[str, str], names: Iterable[str]) -> str:
    lower = {str(k).lower(): str(v) for k, v in row.items()}
    for name in names:
        val = lower.get(name.lower())
        if val:
            return val
    return ""


def _kaggle_ref(row: dict[str, str], *, kind: str) -> str:
    return (
        _row_first(row, ("ref", "slug", "id", "competition", "dataset", "kernelRef", "kernel_ref"))
        or _slug(_row_first(row, ("title", "name")) or kind)
    )


def _kaggle_url(ref: str, *, kind: str) -> str:
    if kind == "competitions":
        return f"https://www.kaggle.com/competitions/{ref}"
    if kind == "datasets":
        return f"https://www.kaggle.com/datasets/{ref}"
    if kind == "kernels":
        return f"https://www.kaggle.com/code/{ref}"
    return "https://www.kaggle.com"


def _kaggle_source_candidate_from_row(row: dict[str, str], *, kind: str, topic: str) -> dict[str, Any]:
    ref = _kaggle_ref(row, kind=kind)
    title = _row_first(row, ("title", "name", "competition")) or ref
    digest = _sha(f"{kind}:{topic}:{ref}:{title}", n=24)
    primitive_opportunities = {
        "competitions": ["competition_task_template", "metric_contract", "submission_format_contract"],
        "datasets": ["dataset_schema_descriptor", "dataset_loader", "data_quality_profile"],
        "kernels": ["baseline_notebook_miner", "feature_engineering_miner", "model_eval_template"],
    }.get(kind, ["kaggle_metadata_miner"])
    return {
        "record_type": "source_candidate",
        "candidate_id": f"source:kaggle-{kind}:{digest}",
        "source_surface_id": "surface-kaggle",
        "source_kind": f"kaggle_{kind}_metadata_candidate",
        "source_type": "ml_dataset_competition",
        "title": f"Kaggle {kind[:-1] if kind.endswith('s') else kind} candidate — {title}",
        "url": _kaggle_url(ref, kind=kind),
        "kaggle_ref": ref,
        "kaggle_kind": kind,
        "topic": topic,
        "metadata": {
            key: _redact(value)[:500]
            for key, value in row.items()
            if key and value and key.lower() not in {"token", "password", "secret", "apikey", "api_key"}
        },
        "license_status": "needs_review",
        "redaction_status": "metadata_only_not_downloaded",
        "source_status": "kaggle_metadata_discovered_not_downloaded",
        "primitive_opportunities": primitive_opportunities,
        "discovery_queries": [f"kaggle {kind} list --search {topic}"],
        "tags": ["kaggle", kind, "ml", "public-project-candidate"],
        "status": "candidate",
        "trust": "candidate",
        "readiness": "R1_indexed",
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _kaggle_session_spec_from_source(source: dict[str, Any]) -> dict[str, Any]:
    cid = str(source.get("candidate_id") or "")
    sid = cid.split("source:kaggle-", 1)[-1]
    return {
        "record_type": "synthetic_session_spec",
        "session_spec_id": f"synth:kaggle-metadata:{sid}",
        "source_kind": "synthetic_from_kaggle_metadata",
        "source_candidate": cid,
        "source_surface_id": "surface-kaggle",
        "title": f"Kaggle-derived synthetic session — {source.get('title')}",
        "intent": "After license review, turn this Kaggle metadata candidate into a realistic data-science session and primitive family.",
        "expected_long_session_shape": [
            "competition_or_dataset_brief",
            "schema_or_manifest_inspection",
            "baseline_route_search",
            "feature_or_preprocess_work",
            "model_eval_or_submission_loop",
            "primitive_candidate_extraction",
            "benchmark_fixture_emit",
        ],
        "expected_findings": [
            "missed_existing_ml_primitive",
            "manual_context_dump",
            "candidate_template_route",
            "submission_or_metric_loop",
        ],
        "source_attribution_required": True,
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "license_status": source.get("license_status"),
        "status": "candidate",
        "serves_truth": False,
        "created_at": _utc(),
    }


def _kaggle_primitive_draft_from_source(source: dict[str, Any]) -> dict[str, Any]:
    cid = str(source.get("candidate_id") or "")
    sid = cid.split("source:kaggle-", 1)[-1]
    kind = str(source.get("kaggle_kind") or "metadata")
    contracts = {
        "competitions": {"input": "KaggleCompetitionMetadata", "output": "CompetitionTaskTemplateDraft"},
        "datasets": {"input": "KaggleDatasetMetadata", "output": "DatasetContractDraft"},
        "kernels": {"input": "KaggleKernelMetadata", "output": "SyntheticSessionSpec"},
    }
    candidate = {
        "record_type": "primitive_draft",
        "primitive_id": f"prim:candidate:kaggle-metadata:{sid}",
        "slug": f"kaggle.{kind}.metadata_to_candidate_route",
        "source_candidate": cid,
        "source_surface_id": "surface-kaggle",
        "title": f"Kaggle {kind} metadata to candidate route",
        "contract": contracts.get(kind, {"input": "KaggleMetadata", "output": "PrimitiveRecordDraft"}),
        "effects": ["net.read"],
        "memory": "artifact",
        "cache": "content_hash",
        "trust": "candidate",
        "readiness": "R1_indexed",
        "proof_requirements": [
            "kaggle_license_gate",
            "source_attribution_gate",
            "redaction_gate",
            "raw_artifact_fetch_review",
            "synthetic_derivative_review",
            "metric_or_schema_proof",
        ],
        "remix_tools": ["map_sequence", "output_wrapper"],
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }
    return _finalize_primitive_candidate(candidate, source, fallback_candidate=cid)


def _kaggle_derived_records_from_rows(
    rows: Iterable[dict[str, str]],
    *,
    kind: str,
    topic: str,
) -> tuple[list[dict], list[dict], list[dict]]:
    sources = [_kaggle_source_candidate_from_row(row, kind=kind, topic=topic) for row in rows]
    sessions = [_kaggle_session_spec_from_source(source) for source in sources]
    primitives = [_kaggle_primitive_draft_from_source(source) for source in sources]
    return sources, sessions, primitives


def _live_kaggle_derived_records(
    *,
    topic_limit: int,
    result_limit: int,
    timeout_seconds: int,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    sources: list[dict] = []
    sessions: list[dict] = []
    primitives: list[dict] = []
    errors: list[dict] = []
    topics = KAGGLE_DISCOVERY_TOPICS[: max(0, int(topic_limit))]
    for topic in topics:
        for kind in KAGGLE_METADATA_KINDS:
            try:
                rows = _kaggle_cli_rows(kind, topic=topic, result_limit=result_limit, timeout_seconds=timeout_seconds)
            except (RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
                errors.append({
                    "record_type": "live_kaggle_discovery_error",
                    "kind": kind,
                    "topic": topic,
                    "error_type": type(exc).__name__,
                    "message": str(exc)[:300],
                    "serves_truth": False,
                })
                continue
            ks, ksp, kp = _kaggle_derived_records_from_rows(rows, kind=kind, topic=topic)
            sources.extend(ks)
            sessions.extend(ksp)
            primitives.extend(kp)
    return sources, sessions, primitives, errors


def _rss_feed_rows(feed_path: Path, *, limit: int = 0) -> list[dict[str, Any]]:
    rows = _read_jsonl(feed_path)
    rows = [row for row in rows if row.get("serves_truth") is False and row.get("feed_url")]
    if limit > 0:
        return rows[:limit]
    return rows


def _xml_local_name(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1].lower()


def _child_text(element: ET.Element, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for child in list(element):
        if _xml_local_name(child.tag) in wanted:
            return " ".join(str(child.text or "").split())
    return ""


def _child_attr(element: ET.Element, name: str, attr: str) -> str:
    for child in list(element):
        if _xml_local_name(child.tag) == name.lower():
            return str(child.attrib.get(attr) or "").strip()
    return ""


def _rss_entries_from_xml(text: str, *, item_limit: int) -> list[dict[str, str]]:
    root = ET.fromstring(text)
    entries: list[dict[str, str]] = []
    for element in root.iter():
        local = _xml_local_name(element.tag)
        if local not in {"item", "entry"}:
            continue
        title = _child_text(element, "title")
        link = _child_text(element, "link")
        if not link:
            link = _child_attr(element, "link", "href")
        published = _child_text(element, "pubDate", "published", "updated")
        guid = _child_text(element, "guid", "id")
        if not title and not link:
            continue
        entries.append({
            "title": title[:300],
            "link": link[:500],
            "published": published[:120],
            "guid": guid[:300],
        })
        if len(entries) >= max(1, int(item_limit)):
            break
    return entries


def _rss_fetch_xml(feed_url: str, *, timeout_seconds: int) -> str:
    req = urllib.request.Request(
        feed_url,
        headers={
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.1",
            "User-Agent": GITHUB_USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _rss_source_candidate_from_entry(feed: dict[str, Any], entry: dict[str, str]) -> dict[str, Any]:
    feed_id = _slug(str(feed.get("id") or feed.get("title") or "rss-feed"))
    feed_url = str(feed.get("feed_url") or "")
    link = entry.get("link") or ""
    title = entry.get("title") or link or feed_id
    digest = _sha(f"{feed_id}:{feed_url}:{link}:{title}:{entry.get('guid') or ''}", n=24)
    opportunities = [str(item) for item in feed.get("primitive_opportunities") or []]
    return {
        "record_type": "source_candidate",
        "candidate_id": f"source:rss-feed-item:{digest}",
        "source_surface_id": feed.get("surface_id") or "surface-agentic-worker-forums-news-rss",
        "source_feed_id": feed_id,
        "source_kind": "public_rss_feed_item_metadata_candidate",
        "source_type": feed.get("source_type") or "developer_news_forum_rss_metadata",
        "topic_family": feed.get("topic_family"),
        "title": f"RSS metadata candidate — {title[:180]}",
        "url": link,
        "feed_url": feed_url,
        "feed_title": feed.get("title") or feed_id,
        "published": entry.get("published") or "",
        "metadata": {
            "title": title,
            "link": link,
            "published": entry.get("published") or "",
            "guid_digest": f"sha256:{_sha(entry.get('guid') or link or title, n=24)}",
        },
        "license_status": feed.get("license_status") or "needs_review",
        "redaction_status": "title_link_metadata_only_no_body",
        "source_status": "rss_metadata_discovered_not_body_fetched",
        "source_policy": feed.get("source_policy") or "metadata_only_no_post_body_republish",
        "primitive_opportunities": opportunities,
        "discovery_queries": [feed_url],
        "tags": ["rss", "metadata", str(feed.get("topic_family") or ""), *[str(tag) for tag in feed.get("tags") or []]],
        "status": "candidate",
        "trust": "candidate",
        "readiness": "R1_indexed",
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _rss_session_spec_from_source(source: dict[str, Any]) -> dict[str, Any]:
    cid = str(source.get("candidate_id") or "")
    sid = cid.rsplit(":", 1)[-1] if ":" in cid else _sha(cid, n=24)
    return {
        "record_type": "synthetic_session_spec",
        "session_spec_id": f"synth:rss-feed-item:{sid}",
        "source_kind": "synthetic_from_rss_feed_metadata",
        "source_candidate": cid,
        "source_surface_id": source.get("source_surface_id"),
        "title": f"RSS-derived source-discovery session — {source.get('title')}",
        "intent": "Use public feed metadata to identify developer demand signals and candidate primitive gaps without storing article, forum, or comment bodies.",
        "expected_long_session_shape": [
            "feed_metadata_review",
            "topic_and_demand_signal_classification",
            "license_and_redaction_gate",
            "primitive_gap_generation",
            "source_surface_seed_update",
            "benchmark_fixture_candidate",
        ],
        "expected_findings": [
            "developer_demand_signal",
            "primitive_gap_from_public_discussion",
            "candidate_template_route",
            "metadata_only_until_review",
        ],
        "source_attribution_required": True,
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "license_status": source.get("license_status"),
        "status": "candidate",
        "serves_truth": False,
        "created_at": _utc(),
    }


def _rss_primitive_drafts_from_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    cid = str(source.get("candidate_id") or "")
    sid = cid.rsplit(":", 1)[-1] if ":" in cid else _sha(cid, n=24)
    opportunities = [str(item) for item in source.get("primitive_opportunities") or []]
    drafts: list[dict[str, Any]] = []
    for opportunity in opportunities:
        candidate = {
            "record_type": "primitive_opportunity",
            "candidate_stage": "primitive_opportunity",
            "primitive_id": f"prim:candidate:rss-metadata:{sid}:{_slug(opportunity)}",
            "slug": f"rss_metadata.{_slug(opportunity)}",
            "source_candidate": cid,
            "source_surface_id": source.get("source_surface_id"),
            "source_feed_id": source.get("source_feed_id"),
            "title": f"{opportunity} from RSS metadata",
            "contract": {
                "input": "PublicFeedItemMetadata",
                "output": _edge_type_name(opportunity),
            },
            "effects": ["net.read"],
            "memory": "artifact",
            "cache": "content_hash",
            "trust": "candidate",
            "readiness": "R1_indexed",
            "proof_requirements": [
                "feed_terms_review",
                "source_attribution_gate",
                "metadata_contract_review",
                "redaction_gate",
                "no_body_or_comment_republish",
                "observer_reuse_benchmark",
            ],
            "remix_tools": ["map_sequence", "output_wrapper", "provenance_wrapper"],
            "raw_source_republish_allowed": False,
            "public_export_allowed": False,
            "serves_truth": False,
            "created_at": _utc(),
        }
        drafts.append(_finalize_primitive_candidate(candidate, source, fallback_candidate=cid))
    return drafts


def _rss_derived_records_from_xml(
    feed: dict[str, Any],
    xml_text: str,
    *,
    item_limit: int,
) -> tuple[list[dict], list[dict], list[dict]]:
    sources = [
        _rss_source_candidate_from_entry(feed, entry)
        for entry in _rss_entries_from_xml(xml_text, item_limit=item_limit)
    ]
    sessions = [_rss_session_spec_from_source(source) for source in sources]
    primitives: list[dict] = []
    for source in sources:
        primitives.extend(_rss_primitive_drafts_from_source(source))
    return sources, sessions, primitives


def _live_rss_derived_records(
    *,
    feed_path: Path,
    feed_limit: int,
    item_limit: int,
    timeout_seconds: int,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    sources: list[dict] = []
    sessions: list[dict] = []
    primitives: list[dict] = []
    errors: list[dict] = []
    for feed in _rss_feed_rows(feed_path, limit=feed_limit):
        feed_url = str(feed.get("feed_url") or "")
        try:
            xml_text = _rss_fetch_xml(feed_url, timeout_seconds=timeout_seconds)
            fs, fsp, fp = _rss_derived_records_from_xml(feed, xml_text, item_limit=item_limit)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ET.ParseError, UnicodeError, OSError) as exc:
            errors.append({
                "record_type": "live_rss_discovery_error",
                "feed_id": feed.get("id"),
                "feed_url_digest": f"sha256:{_sha(feed_url, n=24)}",
                "error_type": type(exc).__name__,
                "message": str(exc)[:300],
                "serves_truth": False,
            })
            continue
        sources.extend(fs)
        sessions.extend(fsp)
        primitives.extend(fp)
    return sources, sessions, primitives, errors


def _markdown_index_rows(index_path: Path, *, limit: int = 0) -> list[dict[str, Any]]:
    rows = _read_jsonl(index_path)
    rows = [row for row in rows if row.get("serves_truth") is False and row.get("index_url")]
    if limit > 0:
        return rows[:limit]
    return rows


def _markdown_fetch_text(index_url: str, *, timeout_seconds: int) -> str:
    req = urllib.request.Request(
        index_url,
        headers={
            "Accept": "text/markdown, text/plain;q=0.9, */*;q=0.1",
            "User-Agent": GITHUB_USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        return resp.read().decode("utf-8", errors="replace")


MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^\]\n]{1,220})\]\((https?://[^)\s]+)(?:\s+\"[^\"]*\")?\)")
RST_LINK_RE = re.compile(r"`([^`\n<>]{1,220})\s+<(https?://[^>\s]+)>`_{0,2}")


def _clean_markdown_label(value: str) -> str:
    cleaned = re.sub(r"[`*_~<>]", "", str(value))
    return " ".join(cleaned.split())[:300]


def _markdown_index_entries(markdown_text: str, *, link_limit: int) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current_heading = ""
    previous_text = ""
    seen: set[tuple[str, str]] = set()
    for lineno, line in enumerate(markdown_text.splitlines(), start=1):
        stripped = line.strip()
        if re.match(r"^[=\-~^#*]{3,}$", stripped) and previous_text:
            current_heading = _clean_markdown_label(previous_text)
            previous_text = ""
            continue
        heading_match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if heading_match:
            current_heading = _clean_markdown_label(heading_match.group(1))
            previous_text = ""
            continue
        for link_re in (MARKDOWN_LINK_RE, RST_LINK_RE):
            for match in link_re.finditer(line):
                title = _clean_markdown_label(match.group(1))
                url = match.group(2).strip().rstrip(".,;")
                key = (title.lower(), url)
                if key in seen:
                    continue
                seen.add(key)
                entries.append({
                    "title": title,
                    "url": url[:500],
                    "category": current_heading[:200],
                    "line_no": lineno,
                })
                if len(entries) >= max(1, int(link_limit)):
                    return entries
        previous_text = stripped if stripped and not stripped.startswith((".. ", "-", "*", "+")) else ""
    return entries


def _markdown_index_source_candidate_from_entry(index: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    index_id = _slug(str(index.get("id") or index.get("title") or "markdown-index"))
    index_url = str(index.get("index_url") or "")
    link = str(entry.get("url") or "")
    title = str(entry.get("title") or link or index_id)
    category = str(entry.get("category") or index.get("topic_family") or "")
    digest = _sha(f"{index_id}:{index_url}:{link}:{title}:{category}", n=24)
    opportunities = [str(item) for item in index.get("primitive_opportunities") or []]
    return {
        "record_type": "source_candidate",
        "candidate_id": f"source:markdown-index-link:{digest}",
        "source_surface_id": index.get("surface_id") or "surface-awesome-public-datasets",
        "source_index_id": index_id,
        "source_kind": "public_markdown_index_link_metadata_candidate",
        "source_type": index.get("source_type") or "public_markdown_index_metadata",
        "topic_family": index.get("topic_family"),
        "title": f"Markdown index link candidate — {title[:180]}",
        "url": link,
        "index_url": index_url,
        "index_title": index.get("title") or index_id,
        "category": category,
        "metadata": {
            "title": title,
            "link": link,
            "category": category,
            "line_no": entry.get("line_no"),
            "link_digest": f"sha256:{_sha(link, n=24)}",
        },
        "license_status": index.get("license_status") or "needs_review",
        "redaction_status": "markdown_link_metadata_only_no_body",
        "source_status": "markdown_index_link_metadata_discovered_not_content_fetched",
        "source_policy": index.get("source_policy") or "metadata_and_source_refs_first",
        "primitive_opportunities": opportunities,
        "discovery_queries": [index_url],
        "tags": ["markdown-index", "metadata", str(index.get("topic_family") or ""), *[str(tag) for tag in index.get("tags") or []]],
        "status": "candidate",
        "trust": "candidate",
        "readiness": "R1_indexed",
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _markdown_index_session_spec_from_source(source: dict[str, Any]) -> dict[str, Any]:
    cid = str(source.get("candidate_id") or "")
    sid = cid.rsplit(":", 1)[-1] if ":" in cid else _sha(cid, n=24)
    return {
        "record_type": "synthetic_session_spec",
        "session_spec_id": f"synth:markdown-index-link:{sid}",
        "source_kind": "synthetic_from_markdown_index_metadata",
        "source_candidate": cid,
        "source_surface_id": source.get("source_surface_id"),
        "title": f"Markdown-index-derived session — {source.get('title')}",
        "intent": "Use public Markdown index link metadata to identify dataset/API/tool source candidates and primitive gaps without storing README bodies or linked dataset contents.",
        "expected_long_session_shape": [
            "index_link_metadata_review",
            "domain_category_classification",
            "license_and_attribution_gate",
            "dataset_or_api_contract_candidate",
            "loader_or_etl_primitive_gap",
            "benchmark_fixture_candidate",
        ],
        "expected_findings": [
            "dataset_loader_opportunity",
            "domain_etl_blueprint",
            "data_quality_template",
            "metadata_only_until_review",
        ],
        "source_attribution_required": True,
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "license_status": source.get("license_status"),
        "status": "candidate",
        "serves_truth": False,
        "created_at": _utc(),
    }


def _markdown_index_primitive_drafts_from_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    cid = str(source.get("candidate_id") or "")
    sid = cid.rsplit(":", 1)[-1] if ":" in cid else _sha(cid, n=24)
    drafts: list[dict[str, Any]] = []
    for opportunity in [str(item) for item in source.get("primitive_opportunities") or []]:
        candidate = {
            "record_type": "primitive_opportunity",
            "candidate_stage": "primitive_opportunity",
            "primitive_id": f"prim:candidate:markdown-index:{sid}:{_slug(opportunity)}",
            "slug": f"markdown_index.{_slug(opportunity)}",
            "source_candidate": cid,
            "source_surface_id": source.get("source_surface_id"),
            "source_index_id": source.get("source_index_id"),
            "title": f"{opportunity} from Markdown index metadata",
            "contract": {
                "input": "MarkdownIndexLinkMetadata",
                "output": _edge_type_name(opportunity),
            },
            "effects": ["net.read"],
            "memory": "artifact",
            "cache": "content_hash",
            "trust": "candidate",
            "readiness": "R1_indexed",
            "proof_requirements": [
                "index_license_review",
                "linked_source_license_gate",
                "source_attribution_gate",
                "metadata_contract_review",
                "no_readme_or_dataset_republish",
                "observer_reuse_benchmark",
            ],
            "remix_tools": ["map_sequence", "output_wrapper", "provenance_wrapper"],
            "raw_source_republish_allowed": False,
            "public_export_allowed": False,
            "serves_truth": False,
            "created_at": _utc(),
        }
        drafts.append(_finalize_primitive_candidate(candidate, source, fallback_candidate=cid))
    return drafts


def _markdown_index_derived_records_from_text(
    index: dict[str, Any],
    markdown_text: str,
    *,
    link_limit: int,
) -> tuple[list[dict], list[dict], list[dict]]:
    sources = [
        _markdown_index_source_candidate_from_entry(index, entry)
        for entry in _markdown_index_entries(markdown_text, link_limit=link_limit)
    ]
    sessions = [_markdown_index_session_spec_from_source(source) for source in sources]
    primitives: list[dict] = []
    for source in sources:
        primitives.extend(_markdown_index_primitive_drafts_from_source(source))
    return sources, sessions, primitives


def _live_markdown_index_derived_records(
    *,
    index_path: Path,
    index_limit: int,
    link_limit: int,
    timeout_seconds: int,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    sources: list[dict] = []
    sessions: list[dict] = []
    primitives: list[dict] = []
    errors: list[dict] = []
    for index in _markdown_index_rows(index_path, limit=index_limit):
        index_url = str(index.get("index_url") or "")
        try:
            markdown_text = _markdown_fetch_text(index_url, timeout_seconds=timeout_seconds)
            ms, msp, mp = _markdown_index_derived_records_from_text(index, markdown_text, link_limit=link_limit)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, UnicodeError, OSError) as exc:
            errors.append({
                "record_type": "live_markdown_index_discovery_error",
                "index_id": index.get("id"),
                "index_url_digest": f"sha256:{_sha(index_url, n=24)}",
                "error_type": type(exc).__name__,
                "message": str(exc)[:300],
                "serves_truth": False,
            })
            continue
        sources.extend(ms)
        sessions.extend(msp)
        primitives.extend(mp)
    return sources, sessions, primitives, errors


def _source_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    candidate = row.get("source_candidate")
    if candidate:
        keys.add(str(candidate))
    surface_id = row.get("source_surface_id")
    if surface_id:
        keys.add(str(surface_id))
        keys.add(f"source:{surface_id}")
    return keys


def _counts_by_source(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for key in _source_keys(row):
            counts[key] = counts.get(key, 0) + 1
    return counts


def _review_finding_count(source: dict[str, Any]) -> int:
    review = source.get("review_summary")
    if not isinstance(review, dict):
        return 0
    count = review.get("finding_count")
    return int(count) if isinstance(count, int) and count > 0 else 0


def _priority_band(score: int) -> str:
    if score >= PRIORITY_P0_MIN_SCORE:
        return "P0"
    if score >= PRIORITY_P1_MIN_SCORE:
        return "P1"
    if score >= PRIORITY_P2_MIN_SCORE:
        return "P2"
    return "P3"


def _recommended_next_action(source: dict[str, Any], *, review_findings: int) -> str:
    source_id = str(source.get("source_surface_id") or source.get("candidate_id") or "")
    source_type = str(source.get("source_type") or source.get("source_kind") or "")
    tags = {str(t).lower() for t in source.get("tags") or []}
    if source_type == "likely_llm_codegen_use_case" or source.get("source_kind") == "curated_public_codegen_use_case":
        return "generate_realistic_demo_session_and_contract_primitive_family"
    if source.get("source_kind") in {"public_github_session_candidate", "public_github_repository_candidate"}:
        return "run_license_redaction_gate_then_distill_public_session_candidate"
    if source_type == "first_party_local_claude":
        if review_findings:
            return "derive_public_safe_synthetic_session_from_private_summary"
        return "keep_private_digest_until_review_signals_exist"
    if "kaggle" in source_id or "ml" in tags or "competitions" in tags:
        return "generate_kaggle_synthetic_session_and_ml_primitive_family"
    if "github" in source_id or "repos" in tags or source_type == "developer_ecosystem":
        return "mine_public_developer_sessions_workflows_and_helper_routes"
    if "workflow" in tags or "automation" in tags:
        return "distill_workflows_into_candidate_templates_and_primitives"
    return "review_source_surface_and_generate_high_value_session_specs"


def _ranking_record(
    source: dict[str, Any],
    *,
    session_count: int,
    primitive_count: int,
    generated_opportunity_count: int = 0,
) -> dict[str, Any]:
    opportunities = source.get("primitive_opportunities") or []
    opportunity_count = (len(opportunities) if isinstance(opportunities, list) else 0) + generated_opportunity_count
    review_findings = _review_finding_count(source)
    license_status = str(source.get("license_status") or "")
    source_type = str(source.get("source_type") or source.get("source_kind") or "")
    is_private = source_type.startswith("first_party") or "private" in license_status
    privacy_class = "private_local" if is_private else "public_source_needs_review"
    public_export_allowed = False

    score = (
        RANK_WEIGHT_BASE
        + opportunity_count * RANK_WEIGHT_PRIMITIVE_OPPORTUNITY
        + session_count * RANK_WEIGHT_SESSION_SPEC
        + primitive_count * RANK_WEIGHT_PRIMITIVE_DRAFT
        + review_findings * RANK_WEIGHT_REVIEW_FINDING
        + (RANK_WEIGHT_PRIVATE_SOURCE if is_private else RANK_WEIGHT_PUBLIC_SOURCE)
    )
    if source_type == "likely_llm_codegen_use_case":
        score += RANK_WEIGHT_PUBLIC_CODEGEN_SEED
    if license_status == "needs_review":
        score -= RANK_WEIGHT_LICENSE_NEEDS_REVIEW_PENALTY
    score = max(0, score)

    token_proxy = (
        opportunity_count * TOKEN_PROXY_PER_OPPORTUNITY
        + session_count * TOKEN_PROXY_PER_SESSION_SPEC
        + primitive_count * TOKEN_PROXY_PER_PRIMITIVE_DRAFT
        + review_findings * TOKEN_PROXY_PER_REVIEW_FINDING
    )
    return {
        "record_type": "candidate_ranking",
        "ranking_id": f"rank:{source.get('candidate_id')}",
        "source_candidate_id": source.get("candidate_id"),
        "source_surface_id": source.get("source_surface_id"),
        "title": source.get("title") or source.get("source_kind") or source.get("candidate_id"),
        "rank_score": score,
        "priority": _priority_band(score),
        "session_spec_count": session_count,
        "primitive_draft_count": primitive_count,
        "primitive_opportunity_count": opportunity_count,
        "local_review_finding_count": review_findings,
        "estimated_token_savings_proxy": token_proxy,
        "estimate_basis": "deterministic_proxy_from_candidate_counts_not_billing_truth",
        "recommended_next_action": _recommended_next_action(source, review_findings=review_findings),
        "privacy_class": privacy_class,
        "raw_source_republish_allowed": False,
        "public_export_allowed": public_export_allowed,
        "license_status": source.get("license_status"),
        "trust": "candidate",
        "serves_truth": False,
        "updated_at": _utc(),
    }


def refresh_rankings(out_dir: Path) -> dict[str, Any]:
    sources = _read_jsonl(out_dir / SOURCE_CANDIDATES_FILE)
    sessions = _read_jsonl(out_dir / SYNTHETIC_SESSION_SPECS_FILE)
    primitives = _read_jsonl(out_dir / PRIMITIVE_DRAFTS_FILE)
    session_counts = _counts_by_source(sessions)
    primitive_counts = _counts_by_source(r for r in primitives if r.get("record_type") == "primitive_draft")
    generated_opportunity_counts = _counts_by_source(r for r in primitives if r.get("record_type") == "primitive_opportunity")

    rankings = [
        _ranking_record(
            source,
            session_count=session_counts.get(str(source.get("candidate_id")), 0),
            primitive_count=primitive_counts.get(str(source.get("candidate_id")), 0),
            generated_opportunity_count=generated_opportunity_counts.get(str(source.get("candidate_id")), 0),
        )
        for source in sources
    ]
    rankings.sort(key=lambda r: (-int(r["rank_score"]), str(r.get("title") or ""), str(r.get("source_candidate_id") or "")))
    _rewrite_jsonl(out_dir / CANDIDATE_RANKINGS_FILE, rankings)
    top = rankings[0] if rankings else {}
    return {
        "record_type": "candidate_ranking_refresh",
        "rankings_written": len(rankings),
        "top_source_candidate_id": top.get("source_candidate_id"),
        "top_rank_score": top.get("rank_score"),
        "top_priority": top.get("priority"),
        "ranking_file": _path_label(out_dir / CANDIDATE_RANKINGS_FILE),
        "serves_truth": False,
    }


def _claude_projects_root() -> Path:
    override = os.environ.get("OBSERVER_PROJECTS_DIR")
    return Path(override) if override else Path.home() / ".claude" / "projects"


def _iter_claude_transcripts(*, max_sessions: int) -> list[Path]:
    root = _claude_projects_root()
    if not root.is_dir():
        return []
    paths: list[Path] = []
    for project in root.iterdir():
        if not project.is_dir():
            continue
        paths.extend(p for p in project.glob("*.jsonl") if p.is_file())
    paths.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0.0, reverse=True)
    return paths[:max_sessions]


def _review_local_transcript(path: Path) -> dict[str, Any]:
    try:
        from src.teleon.observer.capture import from_transcript
        from src.teleon.observer.review import review_session
        events = from_transcript(path)
        report = review_session(events)
        findings = report.get("report") or []
        by_type = report.get("summary", {}).get("by_type") or {}
        top_findings = []
        for f in findings[:5]:
            evidence = _redact(str(f.get("evidence", "")))
            top_findings.append({
                "type": f.get("type"),
                "confidence": f.get("confidence"),
                "evidence_digest": f"sha256:{_sha(evidence, n=24)}",
                "evidence_chars": len(evidence),
                "source_ref": f.get("source_ref"),
                "serves_truth": False,
            })
        return {
            "message_count": len(events),
            "finding_count": len(findings),
            "by_type": by_type,
            "top_findings": top_findings,
            "serves_truth": False,
        }
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}", "serves_truth": False}


def _local_session_records(
    *,
    max_sessions: int,
    derive_reviews: bool,
    include_paths: bool,
    max_review_bytes: int,
) -> tuple[list[dict], list[dict], list[dict]]:
    source_records: list[dict] = []
    session_specs: list[dict] = []
    primitive_drafts: list[dict] = []
    for path in _iter_claude_transcripts(max_sessions=max_sessions):
        try:
            stat = path.stat()
            content_digest = _file_sha(path, n=24)
        except OSError:
            continue
        path_digest = _sha(str(path), n=24)
        source_id = f"local-claude:{content_digest}"
        rec: dict[str, Any] = {
            "record_type": "source_candidate",
            "candidate_id": f"source:{source_id}",
            "source_surface_id": "local-claude-code",
            "source_kind": "first_party_local_claude",
            "path_digest": path_digest,
            "content_digest": content_digest,
            "byte_size": stat.st_size,
            "mtime": stat.st_mtime,
            "project_digest": _sha(path.parent.name, n=16),
            "license_status": "private_local_opt_in_required",
            "redaction_status": "derived_summary_only",
            "status": "candidate_private",
            "trust": "candidate",
            "readiness": "R1_indexed",
            "serves_truth": False,
            "created_at": _utc(),
        }
        if include_paths:
            rec["local_path"] = str(path)
        if derive_reviews and (max_review_bytes <= 0 or stat.st_size <= max_review_bytes):
            rec["review_summary"] = _review_local_transcript(path)
        elif derive_reviews:
            rec["review_summary"] = {
                "skipped": True,
                "reason": "transcript_over_review_byte_cap",
                "byte_size": stat.st_size,
                "max_review_bytes": max_review_bytes,
                "serves_truth": False,
            }
        source_records.append(rec)
        session_specs.append({
            "record_type": "synthetic_session_spec",
            "session_spec_id": f"synth:local-claude:{content_digest}",
            "source_kind": "synthetic_from_private_local_session",
            "source_candidate": rec["candidate_id"],
            "title": "Public-safe derivative of local Claude Code session",
            "intent": "Rewrite this private local session into a synthetic public demo that preserves task shape and reinvention signals, not private content.",
            "privacy_boundary": "private_local_source_to_synthetic_public_derivative",
            "raw_transcript_republish_allowed": False,
            "expected_findings": ["reinvention", "wasted_context", "missed_registry_route", "loop_or_thrash"],
            "status": "candidate",
            "serves_truth": False,
            "created_at": _utc(),
        })
        candidate = {
            "record_type": "primitive_draft",
            "primitive_id": f"prim:candidate:local-session-derived:{content_digest}",
            "slug": f"local-session-derived.{content_digest}",
            "source_candidate": rec["candidate_id"],
            "title": "Local session-derived primitive candidate",
            "contract": {"input": "SessionEvidence", "output": "PrimitiveRecordDraft"},
            "effects": [],
            "memory": "artifact",
            "cache": "content_hash",
            "trust": "candidate",
            "readiness": "R1_indexed",
            "proof_requirements": [
                "private_source_consent",
                "redaction_gate",
                "synthetic_derivative_review",
                "contract_review",
            ],
            "serves_truth": False,
            "created_at": _utc(),
        }
        primitive_drafts.append(_finalize_primitive_candidate(
            candidate,
            rec,
            fallback_candidate=rec["candidate_id"],
        ))
    return source_records, session_specs, primitive_drafts


def _local_repo_derived_records(root: Path, *, limit: int) -> tuple[list[dict], list[dict], list[dict]]:
    from src.teleon.observer.local_registry_connector import primitive_candidates_from_local_repo

    primitives = primitive_candidates_from_local_repo(root, limit=limit)
    sources: list[dict[str, Any]] = []
    for primitive in primitives:
        source_ref = dict(primitive.get("source_ref") or {})
        source_id = str(primitive.get("source_candidate") or f"source:local-repo:{_sha(_canon(source_ref), n=20)}")
        sources.append({
            "record_type": "source_candidate",
            "candidate_id": source_id,
            "source_surface_id": "local-repo",
            "source_kind": "first_party_local_repo_record",
            "source_evidence_status": "source_backed",
            "title": f"Local repo source ref: {source_ref.get('kind')} {source_ref.get('name')}",
            "local_repo_root": _path_label(root),
            "source_ref": source_ref,
            "license_status": "first_party_reviewed",
            "redaction_status": "reviewed_safe",
            "raw_source_republish_allowed": False,
            "public_export_allowed": False,
            "trust": "candidate",
            "readiness": "R3_contract_known",
            "serves_truth": False,
            "created_at": _utc(),
        })
        primitive.setdefault("created_at", _utc())
    return sources, [], primitives


def run_once(
    *,
    surface_map: Path,
    public_use_case_seeds: Path,
    microsurface_atlas: Path,
    source_discovery_search_seeds: Path = SOURCE_DISCOVERY_SEARCH_SEEDS,
    rss_source_feeds: Path = RSS_SOURCE_FEEDS,
    markdown_index_sources: Path = MARKDOWN_INDEX_SOURCES,
    multilingual_search_scopes: Path = MULTILINGUAL_SEARCH_SCOPES,
    naics_search_scopes: Path = NAICS_SEARCH_SCOPES,
    business_operation_search_scopes: Path = BUSINESS_OPERATION_SEARCH_SCOPES,
    out_dir: Path,
    surface_limit: int,
    use_case_limit: int,
    microsurface_limit: int,
    source_discovery_seed_limit: int = 0,
    search_scope_limit: int = DEFAULT_SEARCH_SCOPE_LIMIT,
    naics_scope_limit: int = DEFAULT_NAICS_SCOPE_LIMIT,
    business_operation_scope_limit: int = DEFAULT_BUSINESS_OPERATION_SCOPE_LIMIT,
    skip_public_use_case_seeds: bool,
    skip_microsurface_atlas: bool,
    skip_source_discovery_search_seeds: bool = False,
    skip_multilingual_search_scopes: bool = False,
    skip_naics_search_scopes: bool = False,
    skip_business_operation_search_scopes: bool = False,
    live_github: bool,
    github_query_limit: int,
    github_result_limit: int,
    github_timeout_seconds: int,
    github_token: str | None,
    live_kaggle: bool,
    kaggle_topic_limit: int,
    kaggle_result_limit: int,
    kaggle_timeout_seconds: int,
    live_rss_feeds: bool,
    rss_feed_limit: int,
    rss_item_limit: int,
    rss_timeout_seconds: int,
    live_markdown_indexes: bool,
    markdown_index_limit: int,
    markdown_link_limit: int,
    markdown_timeout_seconds: int,
    include_local_claude: bool,
    derive_local_reviews: bool,
    include_local_paths: bool,
    max_local_sessions: int,
    max_local_review_bytes: int,
    local_repo_root: Path | None,
    local_repo_limit: int,
) -> dict[str, Any]:
    sources, sessions, primitives = _surface_derived_records(surface_map, surface_limit=surface_limit)
    live_discovery_errors: list[dict[str, Any]] = []
    if not skip_public_use_case_seeds:
        us, usp, up = _public_use_case_derived_records(public_use_case_seeds, use_case_limit=use_case_limit)
        sources.extend(us)
        sessions.extend(usp)
        primitives.extend(up)
    if not skip_microsurface_atlas:
        ms, msp, mp = _microsurface_derived_records(microsurface_atlas, microsurface_limit=microsurface_limit)
        sources.extend(ms)
        sessions.extend(msp)
        primitives.extend(mp)
    if not skip_source_discovery_search_seeds:
        ss, ssp, sp = _source_discovery_seed_derived_records(
            source_discovery_search_seeds,
            limit=source_discovery_seed_limit,
        )
        sources.extend(ss)
        sessions.extend(ssp)
        primitives.extend(sp)
    if not skip_multilingual_search_scopes:
        qs, qsp, qp = _search_scope_derived_records(
            multilingual_search_scopes,
            limit=search_scope_limit,
        )
        sources.extend(qs)
        sessions.extend(qsp)
        primitives.extend(qp)
    if not skip_naics_search_scopes:
        ns, nsp, np = _search_scope_derived_records(
            naics_search_scopes,
            limit=naics_scope_limit,
        )
        sources.extend(ns)
        sessions.extend(nsp)
        primitives.extend(np)
    if not skip_business_operation_search_scopes:
        bs, bsp, bp = _search_scope_derived_records(
            business_operation_search_scopes,
            limit=business_operation_scope_limit,
        )
        sources.extend(bs)
        sessions.extend(bsp)
        primitives.extend(bp)
    if live_github:
        gs, gsp, gp, ge = _live_github_derived_records(
            query_limit=github_query_limit,
            result_limit=github_result_limit,
            timeout_seconds=github_timeout_seconds,
            token=github_token,
        )
        sources.extend(gs)
        sessions.extend(gsp)
        primitives.extend(gp)
        live_discovery_errors.extend(ge)
    if live_kaggle:
        ks, ksp, kp, ke = _live_kaggle_derived_records(
            topic_limit=kaggle_topic_limit,
            result_limit=kaggle_result_limit,
            timeout_seconds=kaggle_timeout_seconds,
        )
        sources.extend(ks)
        sessions.extend(ksp)
        primitives.extend(kp)
        live_discovery_errors.extend(ke)
    if live_rss_feeds:
        rs, rsp, rp, re = _live_rss_derived_records(
            feed_path=rss_source_feeds,
            feed_limit=rss_feed_limit,
            item_limit=rss_item_limit,
            timeout_seconds=rss_timeout_seconds,
        )
        sources.extend(rs)
        sessions.extend(rsp)
        primitives.extend(rp)
        live_discovery_errors.extend(re)
    if live_markdown_indexes:
        ms, msp, mp, me = _live_markdown_index_derived_records(
            index_path=markdown_index_sources,
            index_limit=markdown_index_limit,
            link_limit=markdown_link_limit,
            timeout_seconds=markdown_timeout_seconds,
        )
        sources.extend(ms)
        sessions.extend(msp)
        primitives.extend(mp)
        live_discovery_errors.extend(me)
    if include_local_claude:
        ls, lsp, lp = _local_session_records(
            max_sessions=max_local_sessions,
            derive_reviews=derive_local_reviews,
            include_paths=include_local_paths,
            max_review_bytes=max_local_review_bytes,
        )
        sources.extend(ls)
        sessions.extend(lsp)
        primitives.extend(lp)
    if local_repo_root is not None:
        rs, rsp, rp = _local_repo_derived_records(local_repo_root, limit=local_repo_limit)
        sources.extend(rs)
        sessions.extend(rsp)
        primitives.extend(rp)

    source_candidates_added = _append_unique(out_dir / SOURCE_CANDIDATES_FILE, sources, key="candidate_id")
    synthetic_session_specs_added = _append_unique(out_dir / SYNTHETIC_SESSION_SPECS_FILE, sessions, key="session_spec_id")
    primitive_candidates_added = _append_unique(out_dir / PRIMITIVE_DRAFTS_FILE, primitives, key="primitive_id")
    counts = {
        "source_candidates_added": source_candidates_added,
        "synthetic_session_specs_added": synthetic_session_specs_added,
        "primitive_candidates_added": primitive_candidates_added,
        "primitive_drafts_added": primitive_candidates_added,
        "primitive_draft_rows_generated": sum(1 for p in primitives if p.get("record_type") == "primitive_draft"),
        "primitive_opportunity_rows_generated": sum(1 for p in primitives if p.get("record_type") == "primitive_opportunity"),
    }
    ranking = refresh_rankings(out_dir)
    ledger = {
        "record_type": "context_foundry_tick",
        "tick_id": f"tick:{_sha(_utc() + _canon(counts), n=20)}",
        "ts": _utc(),
        "surface_map": _path_label(surface_map),
        "public_use_case_seeds": _path_label(public_use_case_seeds),
        "microsurface_atlas": _path_label(microsurface_atlas),
        "source_discovery_search_seeds": _path_label(source_discovery_search_seeds),
        "rss_source_feeds": _path_label(rss_source_feeds),
        "markdown_index_sources": _path_label(markdown_index_sources),
        "multilingual_search_scopes": _path_label(multilingual_search_scopes),
        "skip_public_use_case_seeds": skip_public_use_case_seeds,
        "skip_microsurface_atlas": skip_microsurface_atlas,
        "skip_source_discovery_search_seeds": skip_source_discovery_search_seeds,
        "skip_multilingual_search_scopes": skip_multilingual_search_scopes,
        "source_discovery_seed_limit": source_discovery_seed_limit,
        "search_scope_limit": search_scope_limit,
        "live_github": live_github,
        "github_query_limit": github_query_limit if live_github else 0,
        "github_result_limit": github_result_limit if live_github else 0,
        "live_kaggle": live_kaggle,
        "kaggle_topic_limit": kaggle_topic_limit if live_kaggle else 0,
        "kaggle_result_limit": kaggle_result_limit if live_kaggle else 0,
        "live_rss_feeds": live_rss_feeds,
        "rss_feed_limit": rss_feed_limit if live_rss_feeds else 0,
        "rss_item_limit": rss_item_limit if live_rss_feeds else 0,
        "live_markdown_indexes": live_markdown_indexes,
        "markdown_index_limit": markdown_index_limit if live_markdown_indexes else 0,
        "markdown_link_limit": markdown_link_limit if live_markdown_indexes else 0,
        "live_discovery_errors": live_discovery_errors,
        "out_dir": _path_label(out_dir),
        "include_local_claude": include_local_claude,
        "derive_local_reviews": derive_local_reviews,
        "include_local_paths": include_local_paths,
        "max_local_review_bytes": max_local_review_bytes,
        "counts": counts,
        "ranking": ranking,
        "serves_truth": False,
    }
    _append_unique(out_dir / LOOP_LEDGER_FILE, [ledger], key="tick_id")
    return ledger


def sanitize_existing(out_dir: Path) -> dict[str, Any]:
    """Remove private evidence snippets from existing local-session review summaries.

    Early local candidates may have stored redacted evidence snippets. Even redacted
    snippets are too close to private transcript content, so the durable form keeps
    only evidence digests and lengths. Older primitive candidate rows may also have
    called metadata-only or synthetic-only opportunities ``primitive_draft``; those
    rows are normalized through the source-evidence gate here.
    """
    path = out_dir / SOURCE_CANDIDATES_FILE
    rows = _read_jsonl(path)
    changed = 0
    removed = 0
    removed_skipped_local_repo_rows = 0
    removed_stale_local_repo_primitives = 0
    removed_candidate_ids: set[str] = set()
    kept_rows: list[dict[str, Any]] = []
    for row in rows:
        metadata = row.get("metadata")
        warning_keyed_metadata = isinstance(metadata, dict) and any(str(k).startswith("Warning:") for k in metadata)
        bad_kaggle_ref = (
            str(row.get("source_kind", "")).startswith("kaggle_")
            and str(row.get("kaggle_ref") or "") in {"competitions", "datasets", "kernels"}
        )
        if warning_keyed_metadata or bad_kaggle_ref:
            if row.get("candidate_id"):
                removed_candidate_ids.add(str(row.get("candidate_id")))
            removed += 1
            continue
        if _skipped_local_repo_row(row):
            if row.get("candidate_id"):
                removed_candidate_ids.add(str(row.get("candidate_id")))
            removed_skipped_local_repo_rows += 1
            continue
        review = row.get("review_summary")
        if not isinstance(review, dict):
            kept_rows.append(row)
            continue
        for finding in review.get("top_findings") or []:
            if not isinstance(finding, dict) or "evidence" not in finding:
                continue
            evidence = _redact(str(finding.pop("evidence", "")))
            finding["evidence_digest"] = f"sha256:{_sha(evidence, n=24)}"
            finding["evidence_chars"] = len(evidence)
            changed += 1
        kept_rows.append(row)
    if changed or removed or removed_skipped_local_repo_rows:
        _rewrite_jsonl(path, kept_rows)
    normalized_primitive_candidates = 0
    primitive_path = out_dir / PRIMITIVE_DRAFTS_FILE
    primitive_rows = _read_jsonl(primitive_path)
    if primitive_rows:
        normalized_rows: list[dict[str, Any]] = []
        for row in primitive_rows:
            if _skipped_local_repo_row(row):
                removed_skipped_local_repo_rows += 1
                continue
            if _stale_local_repo_primitive_row(row):
                removed_stale_local_repo_primitives += 1
                continue
            if row.get("record_type") in {"primitive_draft", "primitive_opportunity"}:
                normalized = _finalize_primitive_candidate(
                    row,
                    row,
                    fallback_candidate=str(row.get("source_candidate") or row.get("source_surface_id") or ""),
                )
                if normalized != row:
                    normalized_primitive_candidates += 1
                normalized_rows.append(normalized)
            else:
                normalized_rows.append(row)
        if normalized_primitive_candidates or removed_stale_local_repo_primitives:
            _rewrite_jsonl(primitive_path, normalized_rows)
    scrubbed_path_fields = 0
    ledger_path = out_dir / LOOP_LEDGER_FILE
    ledger_rows = _read_jsonl(ledger_path)
    if ledger_rows:
        scrubbed_rows: list[dict[str, Any]] = []
        for row in ledger_rows:
            scrubbed, changed_count = _scrub_path_labels(row)
            scrubbed_rows.append(scrubbed)
            scrubbed_path_fields += changed_count
        if scrubbed_path_fields:
            _rewrite_jsonl(ledger_path, scrubbed_rows)
    removed_dependents = 0
    if removed_candidate_ids:
        for dep_name in (SYNTHETIC_SESSION_SPECS_FILE, PRIMITIVE_DRAFTS_FILE):
            dep_path = out_dir / dep_name
            dep_rows = _read_jsonl(dep_path)
            filtered = [row for row in dep_rows if str(row.get("source_candidate") or "") not in removed_candidate_ids]
            removed_dependents += len(dep_rows) - len(filtered)
            if len(filtered) != len(dep_rows):
                _rewrite_jsonl(dep_path, filtered)
        refresh_rankings(out_dir)
    elif removed_stale_local_repo_primitives:
        refresh_rankings(out_dir)
    rec = {
        "record_type": "context_foundry_sanitization",
        "tick_id": f"sanitize:{_sha(_utc() + str(changed), n=20)}",
        "ts": _utc(),
        "out_dir": _path_label(out_dir),
        "sanitized_evidence_fields": changed,
        "removed_malformed_public_rows": removed,
        "removed_skipped_local_repo_rows": removed_skipped_local_repo_rows,
        "removed_stale_local_repo_primitives": removed_stale_local_repo_primitives,
        "removed_dependent_rows": removed_dependents,
        "normalized_primitive_candidates": normalized_primitive_candidates,
        "scrubbed_path_fields": scrubbed_path_fields,
        "policy": "local_session_top_findings_store_digest_only",
        "serves_truth": False,
    }
    _append_unique(out_dir / LOOP_LEDGER_FILE, [rec], key="tick_id")
    return rec


def _watch(args: argparse.Namespace) -> int:
    ticks = 0
    while True:
        rec = run_once(
            surface_map=Path(args.surface_map),
            public_use_case_seeds=Path(args.public_use_case_seeds),
            microsurface_atlas=Path(args.microsurface_atlas),
            source_discovery_search_seeds=Path(args.source_discovery_search_seeds),
            rss_source_feeds=Path(args.rss_source_feeds),
            markdown_index_sources=Path(args.markdown_index_sources),
            multilingual_search_scopes=Path(args.multilingual_search_scopes),
            naics_search_scopes=Path(args.naics_search_scopes),
            business_operation_search_scopes=Path(args.business_operation_search_scopes),
            out_dir=Path(args.out_dir),
            surface_limit=args.surface_limit,
            use_case_limit=args.use_case_limit,
            microsurface_limit=args.microsurface_limit,
            source_discovery_seed_limit=args.source_discovery_seed_limit,
            search_scope_limit=args.search_scope_limit,
            naics_scope_limit=args.naics_scope_limit,
            business_operation_scope_limit=args.business_operation_scope_limit,
            skip_public_use_case_seeds=args.skip_public_use_case_seeds,
            skip_microsurface_atlas=args.skip_microsurface_atlas,
            skip_source_discovery_search_seeds=args.skip_source_discovery_search_seeds,
            skip_multilingual_search_scopes=args.skip_multilingual_search_scopes,
            skip_naics_search_scopes=args.skip_naics_search_scopes,
            skip_business_operation_search_scopes=args.skip_business_operation_search_scopes,
            live_github=args.live_github,
            github_query_limit=args.github_query_limit,
            github_result_limit=args.github_result_limit,
            github_timeout_seconds=args.github_timeout_seconds,
            github_token=os.environ.get(args.github_token_env) if args.github_token_env else None,
            live_kaggle=args.live_kaggle,
            kaggle_topic_limit=args.kaggle_topic_limit,
            kaggle_result_limit=args.kaggle_result_limit,
            kaggle_timeout_seconds=args.kaggle_timeout_seconds,
            live_rss_feeds=args.live_rss_feeds,
            rss_feed_limit=args.rss_feed_limit,
            rss_item_limit=args.rss_item_limit,
            rss_timeout_seconds=args.rss_timeout_seconds,
            live_markdown_indexes=args.live_markdown_indexes,
            markdown_index_limit=args.markdown_index_limit,
            markdown_link_limit=args.markdown_link_limit,
            markdown_timeout_seconds=args.markdown_timeout_seconds,
            include_local_claude=args.include_local_claude,
            derive_local_reviews=args.derive_local_reviews,
            include_local_paths=args.include_local_paths,
            max_local_sessions=args.max_local_sessions,
            max_local_review_bytes=args.max_local_review_bytes,
            local_repo_root=Path(args.local_repo_root) if args.local_repo_root else None,
            local_repo_limit=args.local_repo_limit,
        )
        c = rec["counts"]
        print(
            f"[{rec['ts']}] context-foundry tick "
            f"sources+{c['source_candidates_added']} sessions+{c['synthetic_session_specs_added']} "
            f"primitive_candidates+{c['primitive_candidates_added']} "
            f"opportunities_generated={c['primitive_opportunity_rows_generated']} "
            f"rankings={rec['ranking']['rankings_written']} "
            f"top={rec['ranking'].get('top_source_candidate_id') or '-'} "
            f"serves_truth=false",
            flush=True,
        )
        ticks += 1
        if args.max_ticks and ticks >= args.max_ticks:
            return 0
        time.sleep(max(30, int(args.interval)))


def _self_test() -> int:
    import shutil
    from src.teleon.observer.sessions import encode_cwd

    failures: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            failures.append(f"{name}: {detail}" if detail else name)

    tmp = Path(tempfile.mkdtemp(prefix="aidevobserver_context_foundry_"))
    source_map = tmp / "surfaces.jsonl"
    use_case_seeds = tmp / "use-cases.jsonl"
    microsurface_atlas = tmp / "microsurfaces.jsonl"
    source_discovery_search_seeds = tmp / "search-topics.jsonl"
    rss_source_feeds = tmp / "feeds.jsonl"
    markdown_index_sources = tmp / "markdown-indexes.jsonl"
    multilingual_search_scopes = tmp / "search-scopes.jsonl"
    naics_search_scopes = tmp / "naics-search-scopes.jsonl"
    business_operation_search_scopes = tmp / "business-operation-search-scopes.jsonl"
    out_dir = tmp / "out"
    source_map.write_text(
        "\n".join([
            _canon({
                "id": "surface-kaggle",
                "title": "Kaggle datasets and competitions",
                "source_type": "ml_dataset_competition",
                "url": "https://www.kaggle.com",
                "access_method": "api_or_browser",
                "scan_cadence": "weekly",
                "primitive_opportunities": ["dataset_loader", "competition_task_template", "baseline_notebook_miner"],
                "authority": "medium",
                "license_note": "Dataset and competition licenses vary.",
                "tags": ["datasets", "competitions", "ml"],
            }),
            _canon({
                "id": "surface-github",
                "title": "GitHub repositories, topics, issues, and releases",
                "source_type": "developer_ecosystem",
                "url": "https://api.github.com",
                "access_method": "api",
                "scan_cadence": "daily",
                "primitive_opportunities": ["tool_wrapper", "deployment_template"],
                "authority": "medium",
                "license_note": "Repository licenses vary.",
                "tags": ["code", "repos"],
            }),
        ]) + "\n",
        encoding="utf-8",
    )
    use_case_seeds.write_text(
        _canon({
            "id": "tabular-baseline-demo",
            "title": "Tabular competition baseline demo",
            "source_kind": "curated_public_codegen_use_case",
            "task_family": "data_science",
            "industry": "machine_learning",
            "intent": "Build a tabular baseline with schema inspection and submission validation.",
            "observed_reinvention_patterns": ["manual schema paste", "custom split"],
            "expected_template": "template.tabular_competition_baseline",
            "expected_primitives": ["dataset.inspect_schema", "submission.validate_format"],
            "artifact_policy": "datasets_and_submissions_as_artifacts",
            "effects": ["fs.read"],
            "source_urls": [],
            "source_status": "curated_seed_needs_live_source",
            "license_status": "curated_metadata",
            "trust": "candidate",
            "serves_truth": False,
        }) + "\n",
        encoding="utf-8",
    )
    microsurface_atlas.write_text(
        _canon({
            "id": "admin-table-demo",
            "surface_family": "admin_ops",
            "title": "Admin table demo microsurface",
            "platform_examples": ["internal tools"],
            "common_objects": ["data_table", "csv_import"],
            "common_actions": ["list_records", "import_csv"],
            "reinvention_patterns": ["custom table rebuilt", "CSV importer rebuilt"],
            "candidate_templates": ["template.admin_table_crud"],
            "candidate_primitives": ["admin.list_records", "file.read_csv_artifact"],
            "industries": ["software"],
            "modalities": ["web", "data"],
            "effects": ["db.read", "fs.read"],
            "artifact_policy": "imports_exports_as_artifacts",
            "source_status": "curated_microsurface_seed",
            "license_status": "curated_metadata",
            "trust": "candidate",
            "serves_truth": False,
        }) + "\n",
        encoding="utf-8",
    )
    source_discovery_search_seeds.write_text(
        _canon({
            "id": "n8n-template-discovery-demo",
            "surface_id": "surface-n8n-workflow-templates",
            "topic_family": "workflow_automation",
            "search_terms": [
                "n8n workflow templates json nodes connections",
                "n8n automation templates github",
            ],
            "candidate_outputs": ["n8n_template_pack_miner"],
            "source_policy": "metadata_and_source_refs_first_secret_scrub_required",
            "serves_truth": False,
        }) + "\n",
        encoding="utf-8",
    )
    rss_source_feeds.write_text(
        _canon({
            "id": "agentic-worker-feed-demo",
            "surface_id": "surface-agentic-worker-forums-news-rss",
            "title": "Agentic worker feed demo",
            "feed_url": "https://example.invalid/feed.xml",
            "topic_family": "agentic_workers",
            "source_type": "developer_news_forum_rss_metadata",
            "primitive_opportunities": [
                "developer_demand_signal",
                "forum_thread_to_primitive_opportunity",
            ],
            "source_policy": "title_link_metadata_first_no_post_body_republish",
            "tags": ["agentic-workers", "programming"],
            "serves_truth": False,
        }) + "\n",
        encoding="utf-8",
    )
    markdown_index_sources.write_text(
        _canon({
            "id": "dataset-index-demo",
            "surface_id": "surface-awesome-public-datasets",
            "title": "Dataset index demo",
            "index_url": "https://example.invalid/awesome.md",
            "topic_family": "public_dataset_indexes",
            "source_type": "public_dataset_index",
            "primitive_opportunities": [
                "dataset_index_normalizer",
                "dataset_loader_opportunity",
            ],
            "source_policy": "link_heading_metadata_first_no_readme_or_dataset_republish",
            "tags": ["datasets", "open-data"],
            "serves_truth": False,
        }) + "\n",
        encoding="utf-8",
    )
    multilingual_search_scopes.write_text(
        _canon({
            "id": "global-dataset-search-demo",
            "surface_id": "surface-awesome-public-datasets",
            "title": "Global dataset search demo",
            "topic_family": "public_dataset_indexes",
            "providers": ["github_code", "kaggle", "rss_news"],
            "queries": [
                {"lang": "en", "language": "English", "terms": ["public datasets api"]},
                {"lang": "es", "language": "Spanish", "terms": ["conjuntos de datos publicos api"]},
            ],
            "candidate_outputs": ["dataset_index_normalizer", "dataset_loader_opportunity"],
            "source_policy": "metadata_first_multilingual",
            "serves_truth": False,
        }) + "\n",
        encoding="utf-8",
    )
    naics_search_scopes.write_text(
        _canon({
            "id": "naics-561310-employment-placement-agencies-demo",
            "surface_id": "surface-naics-industry-taxonomy",
            "title": "NAICS 561310 employment agencies demo",
            "topic_family": "naics_admin_support_waste_remediation",
            "providers": ["github_code", "kaggle", "documentation_search"],
            "queries": [
                {"lang": "en", "language": "English", "terms": ["NAICS 561310 employment agency applicant intake workflow"]},
                {"lang": "es", "language": "Spanish", "terms": ["NAICS 561310 agencia empleo flujo candidatos"]},
            ],
            "candidate_outputs": [
                "employment_agency_candidate_intake_template",
                "job_order_matching_schema",
            ],
            "source_policy": "metadata_and_official_naics_refs_first_no_private_business_data",
            "serves_truth": False,
        }) + "\n",
        encoding="utf-8",
    )
    business_operation_search_scopes.write_text(
        _canon({
            "id": "business-operation-sales-validate-invoice-demo",
            "surface_id": "surface-business-operation-first-principles",
            "title": "Sales validates invoice through CRM",
            "topic_family": "business_operation_first_principles",
            "providers": ["github_code", "documentation_search"],
            "queries": [
                {"lang": "en", "language": "English", "terms": ["sales manager validate invoice CRM input output workflow controls"]},
                {"lang": "es", "language": "Spanish", "terms": ["ventas gerente validar factura CRM flujo datos controles"]},
            ],
            "candidate_outputs": [
                "business_operation_edge_candidate",
                "validation_rule_pack",
            ],
            "source_policy": "metadata_first_first_principles_questions_no_private_business_data",
            "serves_truth": False,
        }) + "\n",
        encoding="utf-8",
    )

    projects_root = tmp / "claude_projects"
    fake_cwd = "/tmp/foundry-demo"
    proj = projects_root / encode_cwd(fake_cwd)
    proj.mkdir(parents=True)
    transcript = proj / "session-1.jsonl"
    transcript.write_text(
        _canon({"type": "user", "message": {"role": "user", "content": "build a csv parser from scratch and paste the schema"}}) + "\n"
        + _canon({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Write", "input": {"file_path": "importer.py", "content": "def parse_csv(path): pass"}}
        ]}}) + "\n",
        encoding="utf-8",
    )
    local_repo = tmp / "local_repo"
    (local_repo / "utils").mkdir(parents=True)
    (local_repo / "utils" / "csv.py").write_text(
        "\n".join([
            "MAX_ROWS = 5000",
            "",
            "def read_rows(path: str) -> list[dict[str, str]]:",
            "    \"\"\"Read CSV rows with a max-row guard.\"\"\"",
            "    return []",
        ]),
        encoding="utf-8",
    )
    prev = os.environ.get("OBSERVER_PROJECTS_DIR")
    os.environ["OBSERVER_PROJECTS_DIR"] = str(projects_root)
    try:
        rec = run_once(
            surface_map=source_map,
            public_use_case_seeds=use_case_seeds,
            microsurface_atlas=microsurface_atlas,
            source_discovery_search_seeds=source_discovery_search_seeds,
            rss_source_feeds=rss_source_feeds,
            markdown_index_sources=markdown_index_sources,
            multilingual_search_scopes=multilingual_search_scopes,
            naics_search_scopes=naics_search_scopes,
            business_operation_search_scopes=business_operation_search_scopes,
            out_dir=out_dir,
            surface_limit=0,
            use_case_limit=0,
            microsurface_limit=0,
            source_discovery_seed_limit=0,
            search_scope_limit=0,
            naics_scope_limit=0,
            business_operation_scope_limit=0,
            skip_public_use_case_seeds=False,
            skip_microsurface_atlas=False,
            skip_source_discovery_search_seeds=False,
            skip_multilingual_search_scopes=False,
            skip_naics_search_scopes=False,
            skip_business_operation_search_scopes=False,
            live_github=False,
            github_query_limit=DEFAULT_GITHUB_QUERY_LIMIT,
            github_result_limit=DEFAULT_GITHUB_RESULT_LIMIT,
            github_timeout_seconds=DEFAULT_GITHUB_TIMEOUT_SECONDS,
            github_token=None,
            live_kaggle=False,
            kaggle_topic_limit=DEFAULT_KAGGLE_TOPIC_LIMIT,
            kaggle_result_limit=DEFAULT_KAGGLE_RESULT_LIMIT,
            kaggle_timeout_seconds=DEFAULT_KAGGLE_TIMEOUT_SECONDS,
            live_rss_feeds=False,
            rss_feed_limit=DEFAULT_RSS_FEED_LIMIT,
            rss_item_limit=DEFAULT_RSS_ITEM_LIMIT,
            rss_timeout_seconds=DEFAULT_RSS_TIMEOUT_SECONDS,
            live_markdown_indexes=False,
            markdown_index_limit=DEFAULT_MARKDOWN_INDEX_LIMIT,
            markdown_link_limit=DEFAULT_MARKDOWN_LINK_LIMIT,
            markdown_timeout_seconds=DEFAULT_MARKDOWN_TIMEOUT_SECONDS,
            include_local_claude=True,
            derive_local_reviews=True,
            include_local_paths=False,
            max_local_sessions=10,
            max_local_review_bytes=DEFAULT_MAX_LOCAL_REVIEW_BYTES,
            local_repo_root=local_repo,
            local_repo_limit=2,
        )
        source_rows = _read_jsonl(out_dir / SOURCE_CANDIDATES_FILE)
        spec_rows = _read_jsonl(out_dir / SYNTHETIC_SESSION_SPECS_FILE)
        primitive_rows = _read_jsonl(out_dir / PRIMITIVE_DRAFTS_FILE)
        ranking_rows = _read_jsonl(out_dir / CANDIDATE_RANKINGS_FILE)
        ledger_rows = _read_jsonl(out_dir / LOOP_LEDGER_FILE)
        ck("wrote source candidates", len(source_rows) == 11, str(len(source_rows)))
        ck("wrote session specs", len(spec_rows) == 12, str(len(spec_rows)))
        ck("wrote primitive candidate rows", len(primitive_rows) == 19, str(len(primitive_rows)))
        ck("wrote rankings", len(ranking_rows) == 11, str(len(ranking_rows)))
        ck("wrote ledger", len(ledger_rows) == 1, str(len(ledger_rows)))
        ck("ledger omits raw temp paths", not any(str(tmp) in _canon(r) or "/tmp/" in _canon(r) for r in ledger_rows), str(ledger_rows))
        ck("all records candidate-only", all(r.get("serves_truth") is False for r in source_rows + spec_rows + primitive_rows + ranking_rows + ledger_rows))
        draft_rows = [r for r in primitive_rows if r.get("record_type") == "primitive_draft"]
        opportunity_rows = [r for r in primitive_rows if r.get("record_type") == "primitive_opportunity"]
        ck("metadata and synthetic-only rows are opportunities", len(opportunity_rows) == 17, str(primitive_rows[:3]))
        ck("local repo rows are source-backed drafts", len(draft_rows) == 2 and all(r.get("source_evidence_status") == "source_backed" for r in draft_rows), str(draft_rows))
        ck("ledger counts primitive opportunities", rec["counts"]["primitive_opportunity_rows_generated"] == 17, str(rec["counts"]))
        ck("ledger counts source-backed drafts", rec["counts"]["primitive_draft_rows_generated"] == 2, str(rec["counts"]))
        ck("local path omitted by default", not any("local_path" in r for r in source_rows))
        ck("local transcript derived review exists", any(r.get("review_summary") for r in source_rows if r.get("source_kind") == "first_party_local_claude"))
        ck("kaggle opportunity exists", any("kaggle" in r.get("slug", "") for r in primitive_rows))
        ck("public use case source exists", any(r.get("source_kind") == "curated_public_codegen_use_case" for r in source_rows))
        ck("public use case session exists", any(r.get("source_kind") == "synthetic_from_curated_public_codegen_use_case" for r in spec_rows))
        ck("public use case opportunity exists", any(r.get("source_surface_id") == "public-codegen-use-case-seeds" for r in primitive_rows))
        ck("microsurface source exists", any(r.get("source_kind") == "curated_microsurface_seed" for r in source_rows))
        ck("microsurface session exists", any(r.get("source_kind") == "synthetic_from_curated_microsurface_seed" for r in spec_rows))
        ck("microsurface opportunity exists", any(r.get("source_surface_id") == "microsurface-atlas" for r in primitive_rows))
        ck("source discovery seed source exists", any(r.get("source_kind") == "curated_source_discovery_search_seed" for r in source_rows))
        ck("source discovery seed session exists", any(r.get("source_kind") == "synthetic_from_source_discovery_search_seed" for r in spec_rows))
        ck("source discovery seed opportunity exists", any(r.get("source_surface_id") == "surface-n8n-workflow-templates" for r in primitive_rows))
        ck("multilingual search scope source exists", any(r.get("source_kind") == "curated_multilingual_search_scope" for r in source_rows))
        ck("multilingual search scope session exists", any(r.get("source_kind") == "synthetic_from_multilingual_search_scope" for r in spec_rows))
        ck("multilingual search scope opportunity exists", any("multilingual_search" in r.get("slug", "") for r in primitive_rows))
        scope_sources = [r for r in source_rows if r.get("source_kind") == "curated_multilingual_search_scope"]
        ck("multilingual search scope stores languages", bool(scope_sources) and any(q.get("lang") == "es" for q in scope_sources[0].get("multilingual_queries", [])), str(scope_sources[:1]))
        ck("multilingual search scope stores providers", bool(scope_sources) and {"github_code", "kaggle"}.issubset(set(scope_sources[0].get("providers", []))), str(scope_sources[:1]))
        ck("NAICS source scope exists", any(r.get("source_surface_id") == "surface-naics-industry-taxonomy" for r in source_rows))
        ck("NAICS session exists", any(r.get("source_surface_id") == "surface-naics-industry-taxonomy" for r in spec_rows))
        ck("NAICS employment primitive opportunity exists", any("employment_agency_candidate_intake_template" in _canon(r) for r in primitive_rows))
        ck("local repo read_rows draft exists", any(r.get("record_type") == "primitive_draft" and "read_rows" in _canon(r) for r in primitive_rows), str(draft_rows))
        fake_github_item = {
            "name": "trajectory.jsonl",
            "path": "examples/trajectory.jsonl",
            "sha": "abc123",
            "html_url": "https://github.com/example/repo/blob/main/examples/trajectory.jsonl",
            "repository": {
                "id": 123,
                "full_name": "example/repo",
                "html_url": "https://github.com/example/repo",
            },
        }
        github_sources, github_specs, github_primitives = _github_derived_records_from_items(
            [fake_github_item],
            query=GITHUB_DISCOVERY_QUERIES[0],
        )
        ck("github metadata source exists", len(github_sources) == 1, str(github_sources))
        ck("github metadata source candidate-only", github_sources[0].get("serves_truth") is False, str(github_sources[0]))
        ck("github metadata not fetched", github_sources[0].get("redaction_status") == "not_fetched", str(github_sources[0]))
        ck("github raw republish blocked", github_sources[0].get("raw_source_republish_allowed") is False, str(github_sources[0]))
        ck("github source has no raw content", "content" not in github_sources[0] and "raw" not in github_sources[0], str(github_sources[0]))
        ck("github session derivative exists", len(github_specs) == 1 and github_specs[0].get("source_kind") == "synthetic_from_public_github_metadata", str(github_specs))
        ck("github metadata creates opportunity not draft", len(github_primitives) == 1 and github_primitives[0].get("record_type") == "primitive_opportunity", str(github_primitives))
        fake_n8n_item = {
            "name": "customer-onboarding.json",
            "path": "workflows/customer-onboarding.json",
            "sha": "n8n123",
            "html_url": "https://github.com/example/n8n-workflows/blob/main/workflows/customer-onboarding.json",
            "repository": {
                "id": 789,
                "full_name": "example/n8n-workflows",
                "html_url": "https://github.com/example/n8n-workflows",
            },
        }
        n8n_sources, n8n_specs, n8n_primitives = _github_derived_records_from_items(
            [fake_n8n_item],
            query='n8n workflow filename:*.json "nodes" "connections"',
        )
        ck("github n8n metadata source exists", len(n8n_sources) == 1, str(n8n_sources))
        ck("github n8n metadata classified", n8n_sources[0].get("source_kind") == "public_github_n8n_workflow_candidate", str(n8n_sources[0]))
        ck("github n8n metadata candidate-only", n8n_sources[0].get("serves_truth") is False, str(n8n_sources[0]))
        ck("github n8n source has no raw content", "content" not in n8n_sources[0] and "raw" not in n8n_sources[0], str(n8n_sources[0]))
        ck("github n8n derivative is workflow metadata", len(n8n_specs) == 1 and n8n_specs[0].get("source_kind") == "synthetic_from_public_github_workflow_metadata", str(n8n_specs))
        ck("github n8n primitive is template opportunity", len(n8n_primitives) == 1 and n8n_primitives[0].get("contract", {}).get("output") == "PipelineTemplateDraft", str(n8n_primitives))
        fake_repo_item = {
            "id": 456,
            "full_name": "example/session-repo",
            "html_url": "https://github.com/example/session-repo",
            "description": "Synthetic public agent trajectory examples",
            "license": {"spdx_id": "MIT"},
        }
        repo_sources, repo_specs, repo_primitives = _github_repository_derived_records_from_items(
            [fake_repo_item],
            query=GITHUB_REPOSITORY_DISCOVERY_QUERIES[0],
        )
        ck("github repository metadata source exists", len(repo_sources) == 1, str(repo_sources))
        ck("github repository metadata candidate-only", repo_sources[0].get("serves_truth") is False, str(repo_sources[0]))
        ck("github repository metadata not fetched", repo_sources[0].get("redaction_status") == "not_fetched", str(repo_sources[0]))
        ck("github repository raw republish blocked", repo_sources[0].get("raw_source_republish_allowed") is False, str(repo_sources[0]))
        ck("github repository has no raw content", "content" not in repo_sources[0] and "raw" not in repo_sources[0], str(repo_sources[0]))
        ck("github repository session derivative exists", len(repo_specs) == 1 and repo_specs[0].get("source_kind") == "synthetic_from_public_github_metadata", str(repo_specs))
        ck("github repository metadata creates opportunity not draft", len(repo_primitives) == 1 and repo_primitives[0].get("record_type") == "primitive_opportunity", str(repo_primitives))
        fake_n8n_repo_item = {
            "id": 654,
            "full_name": "example/n8n-template-pack",
            "html_url": "https://github.com/example/n8n-template-pack",
            "description": "n8n workflow templates with nodes and connections",
            "license": {"spdx_id": "MIT"},
        }
        n8n_repo_sources, n8n_repo_specs, n8n_repo_primitives = _github_repository_derived_records_from_items(
            [fake_n8n_repo_item],
            query="n8n workflows templates json",
        )
        ck("github n8n repository classified", n8n_repo_sources[0].get("source_kind") == "public_github_n8n_repository_candidate", str(n8n_repo_sources[0]))
        ck("github n8n repository candidate-only", n8n_repo_sources[0].get("serves_truth") is False, str(n8n_repo_sources[0]))
        ck("github n8n repository primitive is template opportunity", n8n_repo_primitives[0].get("contract", {}).get("output") == "PipelineTemplateDraft", str(n8n_repo_primitives))
        fake_kaggle_row = {
            "ref": "playground-series/demo",
            "title": "Demo tabular competition",
            "category": "Featured",
            "reward": "$0",
            "deadline": "2030-01-01",
        }
        kaggle_sources, kaggle_specs, kaggle_primitives = _kaggle_derived_records_from_rows(
            [fake_kaggle_row],
            kind="competitions",
            topic="tabular",
        )
        ck("kaggle metadata source exists", len(kaggle_sources) == 1, str(kaggle_sources))
        ck("kaggle metadata candidate-only", kaggle_sources[0].get("serves_truth") is False, str(kaggle_sources[0]))
        ck("kaggle metadata not downloaded", kaggle_sources[0].get("redaction_status") == "metadata_only_not_downloaded", str(kaggle_sources[0]))
        ck("kaggle raw republish blocked", kaggle_sources[0].get("raw_source_republish_allowed") is False, str(kaggle_sources[0]))
        ck("kaggle source has no raw content", "content" not in kaggle_sources[0] and "raw" not in kaggle_sources[0], str(kaggle_sources[0]))
        ck("kaggle session derivative exists", len(kaggle_specs) == 1 and kaggle_specs[0].get("source_kind") == "synthetic_from_kaggle_metadata", str(kaggle_specs))
        ck("kaggle metadata creates opportunity not draft", len(kaggle_primitives) == 1 and kaggle_primitives[0].get("record_type") == "primitive_opportunity", str(kaggle_primitives))
        rss_xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
          <title>Agentic worker demo</title>
          <item>
            <title>New agentic worker orchestration pattern</title>
            <link>https://example.com/posts/agentic-worker</link>
            <guid>agentic-worker-1</guid>
            <pubDate>Tue, 30 Jun 2026 12:00:00 GMT</pubDate>
            <description>This body must not be stored.</description>
          </item>
        </channel></rss>
        """
        rss_feed = _read_jsonl(rss_source_feeds)[0]
        rss_sources, rss_specs, rss_primitives = _rss_derived_records_from_xml(
            rss_feed,
            rss_xml,
            item_limit=5,
        )
        ck("rss metadata source exists", len(rss_sources) == 1, str(rss_sources))
        ck("rss metadata candidate-only", rss_sources[0].get("serves_truth") is False, str(rss_sources[0]))
        ck("rss metadata stores title/link only", "This body must not be stored" not in _canon(rss_sources[0]), str(rss_sources[0]))
        ck("rss raw republish blocked", rss_sources[0].get("raw_source_republish_allowed") is False, str(rss_sources[0]))
        ck("rss session derivative exists", len(rss_specs) == 1 and rss_specs[0].get("source_kind") == "synthetic_from_rss_feed_metadata", str(rss_specs))
        ck("rss metadata creates opportunities", len(rss_primitives) == 2 and all(r.get("record_type") == "primitive_opportunity" for r in rss_primitives), str(rss_primitives))
        markdown_text = """# Finance datasets
This README prose must not be stored in source candidates.
- [SEC EDGAR](https://www.sec.gov/edgar)

Healthcare
----------
`ClinicalTrials <https://clinicaltrials.gov>`_
More prose that must not be stored.
        """
        markdown_index = _read_jsonl(markdown_index_sources)[0]
        markdown_sources, markdown_specs, markdown_primitives = _markdown_index_derived_records_from_text(
            markdown_index,
            markdown_text,
            link_limit=10,
        )
        ck("markdown index metadata sources exist", len(markdown_sources) == 2, str(markdown_sources))
        ck("markdown index candidates-only", all(r.get("serves_truth") is False for r in markdown_sources), str(markdown_sources))
        ck("markdown index stores no README prose", "This README prose must not be stored" not in _canon(markdown_sources), str(markdown_sources))
        ck("markdown index parses rst link", any(r.get("metadata", {}).get("title") == "ClinicalTrials" for r in markdown_sources), str(markdown_sources))
        ck("markdown index session derivatives exist", len(markdown_specs) == 2 and all(r.get("source_kind") == "synthetic_from_markdown_index_metadata" for r in markdown_specs), str(markdown_specs))
        ck("markdown index creates opportunities", len(markdown_primitives) == 4 and all(r.get("record_type") == "primitive_opportunity" for r in markdown_primitives), str(markdown_primitives))
        backed = _finalize_primitive_candidate(
            {
                "primitive_id": "prim:candidate:verified:helper",
                "slug": "verified.helper",
                "contract": {"input": "VerifiedInput", "output": "VerifiedOutput"},
                "effects": [],
                "trust": "candidate",
                "serves_truth": False,
            },
            {
                "candidate_id": "source:verified-helper",
                "source_kind": "first_party_repo_symbol",
                "source_evidence_status": "source_backed",
            },
        )
        ck("source-backed evidence can create primitive draft", backed.get("record_type") == "primitive_draft", str(backed))
        ck("rankings sorted by score", ranking_rows == sorted(ranking_rows, key=lambda r: (-int(r["rank_score"]), str(r.get("title") or ""), str(r.get("source_candidate_id") or ""))))
        ck("ranking has token proxy", all(isinstance(r.get("estimated_token_savings_proxy"), int) for r in ranking_rows))
        ck("ranking blocks raw republish", all(r.get("raw_source_republish_allowed") is False for r in ranking_rows))
        ck("ranking blocks public export by default", all(r.get("public_export_allowed") is False for r in ranking_rows))
        ck("public use case ranking action", any(r.get("recommended_next_action") == "generate_realistic_demo_session_and_contract_primitive_family" for r in ranking_rows))
        ck("ledger includes ranking summary", rec["ranking"]["rankings_written"] == 11, str(rec.get("ranking")))
        ck("ledger counts match", rec["counts"]["source_candidates_added"] == 11, str(rec["counts"]))
        second = run_once(
            surface_map=source_map,
            public_use_case_seeds=use_case_seeds,
            microsurface_atlas=microsurface_atlas,
            source_discovery_search_seeds=source_discovery_search_seeds,
            rss_source_feeds=rss_source_feeds,
            markdown_index_sources=markdown_index_sources,
            multilingual_search_scopes=multilingual_search_scopes,
            naics_search_scopes=naics_search_scopes,
            business_operation_search_scopes=business_operation_search_scopes,
            out_dir=out_dir,
            surface_limit=0,
            use_case_limit=0,
            microsurface_limit=0,
            source_discovery_seed_limit=0,
            search_scope_limit=0,
            naics_scope_limit=0,
            business_operation_scope_limit=0,
            skip_public_use_case_seeds=False,
            skip_microsurface_atlas=False,
            skip_source_discovery_search_seeds=False,
            skip_multilingual_search_scopes=False,
            skip_naics_search_scopes=False,
            skip_business_operation_search_scopes=False,
            live_github=False,
            github_query_limit=DEFAULT_GITHUB_QUERY_LIMIT,
            github_result_limit=DEFAULT_GITHUB_RESULT_LIMIT,
            github_timeout_seconds=DEFAULT_GITHUB_TIMEOUT_SECONDS,
            github_token=None,
            live_kaggle=False,
            kaggle_topic_limit=DEFAULT_KAGGLE_TOPIC_LIMIT,
            kaggle_result_limit=DEFAULT_KAGGLE_RESULT_LIMIT,
            kaggle_timeout_seconds=DEFAULT_KAGGLE_TIMEOUT_SECONDS,
            live_rss_feeds=False,
            rss_feed_limit=DEFAULT_RSS_FEED_LIMIT,
            rss_item_limit=DEFAULT_RSS_ITEM_LIMIT,
            rss_timeout_seconds=DEFAULT_RSS_TIMEOUT_SECONDS,
            live_markdown_indexes=False,
            markdown_index_limit=DEFAULT_MARKDOWN_INDEX_LIMIT,
            markdown_link_limit=DEFAULT_MARKDOWN_LINK_LIMIT,
            markdown_timeout_seconds=DEFAULT_MARKDOWN_TIMEOUT_SECONDS,
            include_local_claude=True,
            derive_local_reviews=True,
            include_local_paths=False,
            max_local_sessions=10,
            max_local_review_bytes=DEFAULT_MAX_LOCAL_REVIEW_BYTES,
            local_repo_root=local_repo,
            local_repo_limit=2,
        )
        ck("idempotent append for candidate rows", second["counts"]["source_candidates_added"] == 0, str(second["counts"]))
        stale = {
            "record_type": "primitive_draft",
            "primitive_id": "prim:candidate:stale:metadata-only",
            "slug": "stale.metadata_only",
            "source_candidate": "source:stale-metadata",
            "contract": {"input": "MetadataOnly", "output": "PrimitiveRecordDraft"},
            "effects": [],
            "trust": "candidate",
            "serves_truth": False,
        }
        _append_unique(out_dir / PRIMITIVE_DRAFTS_FILE, [stale], key="primitive_id")
        _append_unique(out_dir / LOOP_LEDGER_FILE, [{
            "record_type": "legacy_path_row",
            "tick_id": "legacy:path-row",
            "out_dir": str(tmp / "legacy-out"),
            "ranking": {"ranking_file": str(tmp / "legacy-rankings.jsonl")},
            "serves_truth": False,
        }], key="tick_id")
        sanitize = sanitize_existing(out_dir)
        normalized_rows = _read_jsonl(out_dir / PRIMITIVE_DRAFTS_FILE)
        sanitized_ledger_rows = _read_jsonl(out_dir / LOOP_LEDGER_FILE)
        normalized_stale = next((r for r in normalized_rows if r.get("primitive_id") == stale["primitive_id"]), {})
        ck("sanitize normalizes stale primitive draft to opportunity", normalized_stale.get("record_type") == "primitive_opportunity", str(normalized_stale))
        ck("sanitize reports primitive normalization", sanitize.get("normalized_primitive_candidates", 0) >= 1, str(sanitize))
        ck("sanitize scrubs legacy path labels", sanitize.get("scrubbed_path_fields", 0) >= 2, str(sanitize))
        ck("sanitized ledger omits raw temp paths", not any(str(tmp) in _canon(r) or "/tmp/" in _canon(r) for r in sanitized_ledger_rows), str(sanitized_ledger_rows[-3:]))
    finally:
        if prev is None:
            os.environ.pop("OBSERVER_PROJECTS_DIR", None)
        else:
            os.environ["OBSERVER_PROJECTS_DIR"] = prev
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("FAIL - aidevobserver_context_foundry_loop")
        for f in failures:
            print("  -", f)
        return 1
    print("PASS - aidevobserver_context_foundry_loop: source surfaces + opt-in local Claude sessions -> "
          "candidate source records, synthetic session specs, primitive candidate/opportunity rows, and ledger ticks; "
          "candidate-only, redacted-summary default, idempotent appends.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--once", action="store_true", help="run one tick (default when --watch is not set)")
    ap.add_argument("--watch", action="store_true", help="run continuously until interrupted")
    ap.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS)
    ap.add_argument("--max-ticks", type=int, default=0, help="for watch mode tests; 0 means forever")
    ap.add_argument("--surface-map", default=str(SOURCE_SURFACE_MAP))
    ap.add_argument("--surface-limit", type=int, default=0)
    ap.add_argument("--public-use-case-seeds", default=str(PUBLIC_CODEGEN_USE_CASE_SEEDS))
    ap.add_argument("--use-case-limit", type=int, default=0)
    ap.add_argument("--skip-public-use-case-seeds", action="store_true")
    ap.add_argument("--microsurface-atlas", default=str(MICROSURFACE_ATLAS))
    ap.add_argument("--microsurface-limit", type=int, default=0)
    ap.add_argument("--skip-microsurface-atlas", action="store_true")
    ap.add_argument("--source-discovery-search-seeds", default=str(SOURCE_DISCOVERY_SEARCH_SEEDS))
    ap.add_argument("--source-discovery-seed-limit", type=int, default=0)
    ap.add_argument("--skip-source-discovery-search-seeds", action="store_true")
    ap.add_argument("--multilingual-search-scopes", default=str(MULTILINGUAL_SEARCH_SCOPES))
    ap.add_argument("--search-scope-limit", type=int, default=DEFAULT_SEARCH_SCOPE_LIMIT)
    ap.add_argument("--skip-multilingual-search-scopes", action="store_true")
    ap.add_argument("--naics-search-scopes", default=str(NAICS_SEARCH_SCOPES))
    ap.add_argument("--naics-scope-limit", type=int, default=DEFAULT_NAICS_SCOPE_LIMIT)
    ap.add_argument("--skip-naics-search-scopes", action="store_true")
    ap.add_argument("--business-operation-search-scopes", default=str(BUSINESS_OPERATION_SEARCH_SCOPES))
    ap.add_argument("--business-operation-scope-limit", type=int, default=DEFAULT_BUSINESS_OPERATION_SCOPE_LIMIT)
    ap.add_argument("--skip-business-operation-search-scopes", action="store_true")
    ap.add_argument("--live-github", action="store_true",
                    help="opt in to live GitHub Code Search metadata discovery; stores metadata only")
    ap.add_argument("--github-query-limit", type=int, default=DEFAULT_GITHUB_QUERY_LIMIT)
    ap.add_argument("--github-result-limit", type=int, default=DEFAULT_GITHUB_RESULT_LIMIT)
    ap.add_argument("--github-timeout-seconds", type=int, default=DEFAULT_GITHUB_TIMEOUT_SECONDS)
    ap.add_argument("--github-token-env", default="GITHUB_TOKEN",
                    help="environment variable containing an optional GitHub token; never written to records")
    ap.add_argument("--live-kaggle", action="store_true",
                    help="opt in to live Kaggle CLI metadata discovery; stores metadata only")
    ap.add_argument("--kaggle-topic-limit", type=int, default=DEFAULT_KAGGLE_TOPIC_LIMIT)
    ap.add_argument("--kaggle-result-limit", type=int, default=DEFAULT_KAGGLE_RESULT_LIMIT)
    ap.add_argument("--kaggle-timeout-seconds", type=int, default=DEFAULT_KAGGLE_TIMEOUT_SECONDS)
    ap.add_argument("--rss-source-feeds", default=str(RSS_SOURCE_FEEDS))
    ap.add_argument("--live-rss-feeds", action="store_true",
                    help="opt in to live RSS/Atom metadata discovery; stores title/link metadata only")
    ap.add_argument("--rss-feed-limit", type=int, default=DEFAULT_RSS_FEED_LIMIT)
    ap.add_argument("--rss-item-limit", type=int, default=DEFAULT_RSS_ITEM_LIMIT)
    ap.add_argument("--rss-timeout-seconds", type=int, default=DEFAULT_RSS_TIMEOUT_SECONDS)
    ap.add_argument("--markdown-index-sources", default=str(MARKDOWN_INDEX_SOURCES))
    ap.add_argument("--live-markdown-indexes", action="store_true",
                    help="opt in to live Markdown index metadata discovery; stores link/heading metadata only")
    ap.add_argument("--markdown-index-limit", type=int, default=DEFAULT_MARKDOWN_INDEX_LIMIT)
    ap.add_argument("--markdown-link-limit", type=int, default=DEFAULT_MARKDOWN_LINK_LIMIT)
    ap.add_argument("--markdown-timeout-seconds", type=int, default=DEFAULT_MARKDOWN_TIMEOUT_SECONDS)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--include-local-claude", action="store_true", help="opt in to local ~/.claude/projects scanning")
    ap.add_argument("--derive-local-reviews", action="store_true", help="derive governed summaries from local transcripts")
    ap.add_argument("--include-local-paths", action="store_true", help="store raw local transcript paths; private use only")
    ap.add_argument("--max-local-sessions", type=int, default=DEFAULT_MAX_LOCAL_SESSIONS)
    ap.add_argument("--max-local-review-bytes", type=int, default=DEFAULT_MAX_LOCAL_REVIEW_BYTES,
                    help="skip derived review for local transcripts above this size; 0 means no cap")
    ap.add_argument("--local-repo-root", default="",
                    help="explicit repo root to index into source-backed primitive drafts; disabled when empty")
    ap.add_argument("--local-repo-limit", type=int, default=DEFAULT_LOCAL_REPO_PRIMITIVE_LIMIT)
    ap.add_argument("--sanitize-existing", action="store_true", help="remove private evidence snippets from existing local-session summaries")
    ap.add_argument("--refresh-rankings", action="store_true", help="rewrite candidate_rankings.jsonl from existing candidate rows")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()
    if args.sanitize_existing:
        print(_canon(sanitize_existing(Path(args.out_dir))))
        return 0
    if args.refresh_rankings:
        print(_canon(refresh_rankings(Path(args.out_dir))))
        return 0
    if args.watch:
        return _watch(args)
    rec = run_once(
        surface_map=Path(args.surface_map),
        public_use_case_seeds=Path(args.public_use_case_seeds),
        microsurface_atlas=Path(args.microsurface_atlas),
        source_discovery_search_seeds=Path(args.source_discovery_search_seeds),
        rss_source_feeds=Path(args.rss_source_feeds),
        markdown_index_sources=Path(args.markdown_index_sources),
        multilingual_search_scopes=Path(args.multilingual_search_scopes),
        naics_search_scopes=Path(args.naics_search_scopes),
        business_operation_search_scopes=Path(args.business_operation_search_scopes),
        out_dir=Path(args.out_dir),
        surface_limit=args.surface_limit,
        use_case_limit=args.use_case_limit,
        microsurface_limit=args.microsurface_limit,
        source_discovery_seed_limit=args.source_discovery_seed_limit,
        search_scope_limit=args.search_scope_limit,
        naics_scope_limit=args.naics_scope_limit,
        business_operation_scope_limit=args.business_operation_scope_limit,
        skip_public_use_case_seeds=args.skip_public_use_case_seeds,
        skip_microsurface_atlas=args.skip_microsurface_atlas,
        skip_source_discovery_search_seeds=args.skip_source_discovery_search_seeds,
        skip_multilingual_search_scopes=args.skip_multilingual_search_scopes,
        skip_naics_search_scopes=args.skip_naics_search_scopes,
        skip_business_operation_search_scopes=args.skip_business_operation_search_scopes,
        live_github=args.live_github,
        github_query_limit=args.github_query_limit,
        github_result_limit=args.github_result_limit,
        github_timeout_seconds=args.github_timeout_seconds,
        github_token=os.environ.get(args.github_token_env) if args.github_token_env else None,
        live_kaggle=args.live_kaggle,
        kaggle_topic_limit=args.kaggle_topic_limit,
        kaggle_result_limit=args.kaggle_result_limit,
        kaggle_timeout_seconds=args.kaggle_timeout_seconds,
        live_rss_feeds=args.live_rss_feeds,
        rss_feed_limit=args.rss_feed_limit,
        rss_item_limit=args.rss_item_limit,
        rss_timeout_seconds=args.rss_timeout_seconds,
        live_markdown_indexes=args.live_markdown_indexes,
        markdown_index_limit=args.markdown_index_limit,
        markdown_link_limit=args.markdown_link_limit,
        markdown_timeout_seconds=args.markdown_timeout_seconds,
        include_local_claude=args.include_local_claude,
        derive_local_reviews=args.derive_local_reviews,
        include_local_paths=args.include_local_paths,
        max_local_sessions=args.max_local_sessions,
        max_local_review_bytes=args.max_local_review_bytes,
        local_repo_root=Path(args.local_repo_root) if args.local_repo_root else None,
        local_repo_limit=args.local_repo_limit,
    )
    print(_canon(rec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
