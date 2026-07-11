#!/usr/bin/env python3
"""Global primitive source lifecycle packager.

This script packages source-foundry output into the artifacts needed for the
global primitive creation loop used by AIDevObserver, Teleon, OpenHubForAI,
Baltor, AI Done Right, and future surfaces:

source candidates + primitive opportunities/drafts + rankings
  -> selected primitive digests
  -> implementation backlog rows
  -> compact search cards
  -> deterministic vector rows
  -> manifest + Markdown summary

It does not fetch public source, download package code, implement primitives, or
promote anything. It makes the status of each primitive explicit:

* `existing_source_ref_candidate` means the row points to reviewed first-party
  source evidence but still needs proof/promotion.
* `implementation_backlog` means the row is a real opportunity/request that
  needs implementation and proof before it can become a usable primitive.

Every emitted row remains `serves_truth=false`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.registry.enrich import (  # noqa: E402
    py_function_src_teleon_registry_enrich__embedding as embed_record,
    py_function_src_teleon_registry_enrich__keywords as keywords_for_record,
    py_var_src_teleon_registry_enrich___EMBED_DIM as EMBED_DIM,
)

DEFAULT_FOUNDRY_DIR = _resource("data") / "dev-intel" / "aidevobserver_context_foundry"
DEFAULT_OUT_DIR = _resource("data") / "dev-intel" / "primitive_source_lifecycle"
DEFAULT_EDGE_FOUNDRY_PATH = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "primitive_edge_cards.jsonl"
DEFAULT_EDGE_FOUNDRY_LIMIT = 5000
DEFAULT_EDGE_FOUNDRY_MIN_QUALITY = 70

EDGE_FOUNDRY_LIFECYCLE_KINDS = {
    "alert.rule",
    "api.endpoint",
    "auth.middleware",
    "artifact.capability_blueprint",
    "artifact.capability_slot",
    "artifact.capability_template_route",
    "artifact.ci_workflow",
    "artifact.command_target",
    "artifact.json_schema",
    "artifact.k8s_manifest",
    "artifact.markdown_executable_snippet",
    "artifact.microsurface_blueprint",
    "artifact.notebook_code_cell",
    "artifact.openapi_operation",
    "artifact.package_script",
    "artifact.primitive_group",
    "artifact.shell_command",
    "artifact.shell_function",
    "artifact.sql_artifact",
    "artifact.workflow_definition",
    "artifact.workflow_step",
    "cli.command",
    "container.job",
    "cron.job",
    "dashboard",
    "data.quality.rule",
    "db.migration",
    "elt.model",
    "etl.pipeline",
    "event.handler",
    "github.action",
    "graphql.resolver",
    "grpc.method",
    "integration.connector",
    "llm.tool",
    "mock.server",
    "policy.rule",
    "rate.limit.middleware",
    "runbook",
    "security.compliance.workflow",
    "shell.script",
    "sql.proc",
    "sql.view",
    "terraform.module",
    "test.fixture",
    "ui.component",
    "ui.route",
    "vector.indexer",
    "dashboard",
    "grpc.method",
    "js.fn",
    "js.test_case",
    "kubernetes.controller",
    "kubernetes.job",
    "llm.tool",
    "queue.consumer",
    "queue.producer",
    "py.fn",
    "py.method",
    "py.proof_fn",
    "py.test_fn",
    "sdk.client",
    "service.group",
    "webhook.handler",
    "workflow.group",
    "workflow.step",
}

SOURCE_CANDIDATES_FILE = "source_candidates.jsonl"
PRIMITIVE_DRAFTS_FILE = "primitive_drafts.jsonl"
SYNTHETIC_SESSION_SPECS_FILE = "synthetic_session_specs.jsonl"
CANDIDATE_RANKINGS_FILE = "candidate_rankings.jsonl"


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(value: str | bytes, *, n: int = 24) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:n]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL in {path} line {i}: {exc}") from exc
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def _read_optional_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    return _read_jsonl(path)


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(_canon(row) + "\n")
            count += 1
    return count


def _source_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for key in ("candidate_id", "source_candidate", "source_surface_id"):
        value = row.get(key)
        if value:
            keys.add(str(value))
    if row.get("source_surface_id"):
        keys.add(f"source:{row['source_surface_id']}")
    source_ref = row.get("source_ref")
    if isinstance(source_ref, dict):
        for key in ("candidate_id", "source_candidate", "source_surface_id"):
            value = source_ref.get(key)
            if value:
                keys.add(str(value))
    return keys


def _by_candidate_id(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("candidate_id")): row for row in rows if row.get("candidate_id")}


def _rankings_by_source(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row.get("source_candidate_id")
        if key:
            out[str(key)] = row
    return out


def _best_ranking(row: dict[str, Any], ranking_by_source: dict[str, dict[str, Any]]) -> dict[str, Any]:
    for key in _source_keys(row):
        if key in ranking_by_source:
            return ranking_by_source[key]
    return {}


def _best_source(row: dict[str, Any], source_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    for key in _source_keys(row):
        if key in source_by_id:
            return source_by_id[key]
    return {}


def _row_id(row: dict[str, Any]) -> str:
    return str(row.get("primitive_id") or row.get("id") or f"row:{_sha(_canon(row))}")


def _label(row: dict[str, Any]) -> str:
    return str(row.get("slug") or row.get("title") or _row_id(row))


def _blackbox_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("does") or value.get("summary") or value)
    return str(value or "")


def _edge_quality(row: dict[str, Any]) -> int:
    try:
        return int(row.get("quality_score") or 0)
    except (TypeError, ValueError):
        return 0


def _edge_foundry_visible_for_lifecycle(row: dict[str, Any], *, include_private: bool) -> bool:
    visibility = str(row.get("surface_visibility") or "public_demo_safe_candidate")
    return include_private or visibility == "public_demo_safe_candidate"


def _edge_foundry_kind_allowed(row: dict[str, Any], *, include_jsonl_records: bool) -> bool:
    kind = str(row.get("kind") or "")
    return kind in EDGE_FOUNDRY_LIFECYCLE_KINDS or (include_jsonl_records and kind == "artifact.jsonl_record")


def _edge_foundry_candidate_allowed(
    row: dict[str, Any],
    *,
    min_quality: int,
    include_private: bool,
    include_jsonl_records: bool,
) -> bool:
    return (
        row.get("candidate") is True
        and row.get("serves_truth") is False
        and row.get("source_evidence_status") == "source_backed"
        and _edge_quality(row) >= min_quality
        and _edge_foundry_visible_for_lifecycle(row, include_private=include_private)
        and _edge_foundry_kind_allowed(row, include_jsonl_records=include_jsonl_records)
    )


def _edge_proof_requirements(row: dict[str, Any]) -> list[str]:
    effects = {str(effect) for effect in row.get("effects") or []}
    requirements = [
        "source_ref_exists",
        "contract_review_passes",
        "import_or_parse_smoke_passes",
        "reuse_card_benchmark_passes",
    ]
    if row.get("mutations"):
        requirements.append("deterministic_mutator_preconditions_pass")
    if any(effect.startswith("net.") or effect == "net.read" for effect in effects):
        requirements.extend(["network_effect_policy_review", "recorded_receipt_or_ttl_policy"])
    if any("write" in effect for effect in effects):
        requirements.extend(["idempotency_or_compensation_policy", "side_effect_ordering_gate"])
    if "subprocess" in effects:
        requirements.append("sandbox_runtime_required")
    return sorted(dict.fromkeys(requirements))


def _edge_promotion_blockers(row: dict[str, Any]) -> list[str]:
    blockers = ["proof_bundle_required", "promotion_review_required"]
    if row.get("surface_visibility") != "public_demo_safe_candidate":
        blockers.append("private_visibility_review_required")
    if "Any" in str(row.get("contract") or ""):
        blockers.append("contract_specificity_review_required")
    if _edge_quality(row) < 80:
        blockers.append("quality_threshold_review_required")
    return sorted(dict.fromkeys(blockers))


def _edge_foundry_to_primitive_row(row: dict[str, Any]) -> dict[str, Any]:
    primitive_id = str(row.get("primitive_id") or f"prim:edge-foundry:{_sha(_canon(row))}")
    source_digest = str(row.get("source_digest") or _sha(_canon(row), n=24))
    contract = row.get("contract") if isinstance(row.get("contract"), dict) else {
        "input": row.get("input_edge"),
        "output": row.get("output_edge"),
    }
    return {
        "record_type": "primitive_draft",
        "candidate_stage": "edge_foundry_source_backed_candidate",
        "primitive_id": primitive_id,
        "slug": str(row.get("slug") or primitive_id),
        "title": str(row.get("title") or row.get("label") or row.get("slug") or primitive_id),
        "source_candidate": f"source:edge-foundry:{source_digest}",
        "source_surface_id": "edge-foundry",
        "source_kind": "edge_foundry_source_backed_edge_card",
        "source_family": row.get("source_family"),
        "source_ref": row.get("source_ref"),
        "source_digest": source_digest,
        "source_evidence_status": "source_backed",
        "surface_visibility": row.get("surface_visibility"),
        "kind": row.get("kind"),
        "contract": contract,
        "input_edge": row.get("input_edge") or contract.get("input"),
        "output_edge": row.get("output_edge") or contract.get("output"),
        "blackbox": _blackbox_text(row.get("blackbox")),
        "effects": row.get("effects") or [],
        "memory": row.get("memory"),
        "cache": row.get("cache"),
        "runtime_targets": row.get("runtime_targets") or [],
        "blocking_keys": row.get("blocking_keys") or [],
        "capability_tags": row.get("capability_tags") or row.get("domains") or [],
        "mutations": row.get("mutations") or [],
        "quality_score": _edge_quality(row),
        "readiness": row.get("readiness"),
        "trust": row.get("trust") or "candidate",
        "proof_requirements": _edge_proof_requirements(row),
        "promotion_blockers": _edge_promotion_blockers(row),
        "candidate": True,
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _select_edge_foundry_rows(
    rows: list[dict[str, Any]],
    *,
    limit: int,
    min_quality: int,
    include_private: bool,
    include_jsonl_records: bool,
) -> list[dict[str, Any]]:
    candidates = [
        _edge_foundry_to_primitive_row(row)
        for row in rows
        if _edge_foundry_candidate_allowed(
            row,
            min_quality=min_quality,
            include_private=include_private,
            include_jsonl_records=include_jsonl_records,
        )
    ]
    candidates.sort(key=lambda row: (
        -int(row.get("quality_score") or 0),
        0 if row.get("kind") in {"artifact.capability_template_route", "artifact.capability_blueprint", "artifact.microsurface_blueprint"} else 1,
        str(row.get("source_family") or ""),
        str(row.get("primitive_id") or ""),
    ))
    return candidates[:limit] if limit else candidates


def _digest_text(row: dict[str, Any], source: dict[str, Any], ranking: dict[str, Any]) -> str:
    contract = row.get("contract") or {
        "input": row.get("input_contract"),
        "output": row.get("output_contract"),
    }
    return " ".join(
        str(part)
        for part in (
            _row_id(row),
            _label(row),
            row.get("record_type"),
            row.get("candidate_stage"),
            contract,
            row.get("effects"),
            row.get("memory"),
            row.get("cache"),
            row.get("proof_requirements"),
            row.get("promotion_blockers"),
            row.get("source_evidence_status"),
            row.get("source_family"),
            row.get("source_ref"),
            row.get("blackbox"),
            row.get("input_edge"),
            row.get("output_edge"),
            row.get("blocking_keys"),
            row.get("capability_tags"),
            row.get("mutations"),
            row.get("runtime_targets"),
            row.get("quality_score"),
            source.get("title"),
            source.get("source_kind") or source.get("source_type"),
            ranking.get("recommended_next_action"),
        )
        if part
    )


def _implementation_state(row: dict[str, Any], source: dict[str, Any]) -> str:
    if row.get("source_evidence_status") == "source_backed":
        return "existing_source_ref_candidate"
    if source.get("source_evidence_status") == "source_backed":
        return "existing_source_ref_candidate"
    if row.get("record_type") == "primitive_draft":
        return "source_backed_candidate_needs_proof"
    return "implementation_backlog"


def _next_action(row: dict[str, Any], source: dict[str, Any], ranking: dict[str, Any]) -> str:
    if ranking.get("recommended_next_action"):
        return str(ranking["recommended_next_action"])
    if _implementation_state(row, source) == "existing_source_ref_candidate":
        return "run_contract_proof_and_reuse_card_benchmark"
    return "find_or_build_source_backed_implementation_then_prove"


def _digest_row(row: dict[str, Any], source: dict[str, Any], ranking: dict[str, Any]) -> dict[str, Any]:
    text = _digest_text(row, source, ranking)
    contract = row.get("contract") or {
        "input": row.get("input_contract"),
        "output": row.get("output_contract"),
    }
    return {
        "record_type": "primitive_lifecycle_digest",
        "primitive_id": _row_id(row),
        "label": _label(row),
        "candidate_record_type": row.get("record_type"),
        "candidate_stage": row.get("candidate_stage") or row.get("record_type"),
        "source_candidate": row.get("source_candidate") or source.get("candidate_id"),
        "source_surface_id": row.get("source_surface_id") or source.get("source_surface_id"),
        "source_kind": row.get("source_kind") or source.get("source_kind") or source.get("source_type"),
        "source_family": row.get("source_family"),
        "source_ref": row.get("source_ref"),
        "contract": contract,
        "input_edge": row.get("input_edge") or contract.get("input"),
        "output_edge": row.get("output_edge") or contract.get("output"),
        "blackbox": row.get("blackbox"),
        "effects": row.get("effects") or [],
        "memory": row.get("memory"),
        "cache": row.get("cache"),
        "runtime_targets": row.get("runtime_targets") or [],
        "blocking_keys": row.get("blocking_keys") or [],
        "capability_tags": row.get("capability_tags") or [],
        "mutations": row.get("mutations") or [],
        "quality_score": row.get("quality_score", 0),
        "surface_visibility": row.get("surface_visibility"),
        "readiness": row.get("readiness"),
        "trust": row.get("trust"),
        "source_evidence_status": row.get("source_evidence_status") or source.get("source_evidence_status") or "needs_source_evidence",
        "implementation_state": _implementation_state(row, source),
        "next_action": _next_action(row, source, ranking),
        "rank_score": ranking.get("rank_score", 0),
        "priority": ranking.get("priority", "P3"),
        "estimated_token_savings_proxy": ranking.get("estimated_token_savings_proxy", 0),
        "proof_requirements": row.get("proof_requirements") or [],
        "promotion_blockers": row.get("promotion_blockers") or [],
        "digest": f"sha256:{_sha(text, n=32)}",
        "digest_text_chars": len(text),
        "keywords": keywords_for_record({"text": text}),
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _backlog_row(digest: dict[str, Any]) -> dict[str, Any]:
    state = str(digest.get("implementation_state") or "")
    return {
        "record_type": "primitive_implementation_backlog",
        "backlog_id": f"backlog:{_sha(str(digest['primitive_id']), n=24)}",
        "primitive_id": digest["primitive_id"],
        "label": digest["label"],
        "priority": digest.get("priority"),
        "rank_score": digest.get("rank_score"),
        "implementation_state": state,
        "required_action": "prove_existing_source_ref" if state.startswith("existing") else "build_or_find_deterministic_implementation",
        "acceptance_criteria": [
            "license_and_attribution_gate_passes",
            "contract_review_passes",
            "reuse_card_benchmark_passes",
            "deterministic_replay_or_fixture_proof_passes",
            "promotion_candidate_remains_serves_truth_false_until_approved",
        ],
        "proof_requirements": digest.get("proof_requirements") or [],
        "promotion_blockers": digest.get("promotion_blockers") or [],
        "serves_truth": False,
        "created_at": _utc(),
    }


def _search_card(digest: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "primitive_search_card",
        "primitive_id": digest["primitive_id"],
        "label": digest["label"],
        "contract": digest.get("contract"),
        "input_edge": digest.get("input_edge"),
        "output_edge": digest.get("output_edge"),
        "blackbox": digest.get("blackbox"),
        "effects": digest.get("effects") or [],
        "memory": digest.get("memory"),
        "cache": digest.get("cache"),
        "runtime_targets": digest.get("runtime_targets") or [],
        "blocking_keys": digest.get("blocking_keys") or [],
        "capability_tags": digest.get("capability_tags") or [],
        "mutations": digest.get("mutations") or [],
        "quality_score": digest.get("quality_score", 0),
        "keywords": digest.get("keywords") or [],
        "priority": digest.get("priority"),
        "implementation_state": digest.get("implementation_state"),
        "source_surface_id": digest.get("source_surface_id"),
        "source_kind": digest.get("source_kind"),
        "source_family": digest.get("source_family"),
        "source_ref": digest.get("source_ref"),
        "source_evidence_status": digest.get("source_evidence_status"),
        "surface_visibility": digest.get("surface_visibility"),
        "candidate": True,
        "serves_truth": False,
    }


def _vector_row(digest: dict[str, Any]) -> dict[str, Any]:
    text = _canon({
        "primitive_id": digest.get("primitive_id"),
        "label": digest.get("label"),
        "contract": digest.get("contract"),
        "effects": digest.get("effects"),
        "keywords": digest.get("keywords"),
        "source_surface_id": digest.get("source_surface_id"),
        "source_kind": digest.get("source_kind"),
        "source_family": digest.get("source_family"),
        "input_edge": digest.get("input_edge"),
        "output_edge": digest.get("output_edge"),
        "blackbox": digest.get("blackbox"),
        "blocking_keys": digest.get("blocking_keys"),
        "capability_tags": digest.get("capability_tags"),
        "runtime_targets": digest.get("runtime_targets"),
        "mutators": [
            mutation.get("mutator")
            for mutation in digest.get("mutations") or []
            if isinstance(mutation, dict) and mutation.get("mutator")
        ],
        "quality_score": digest.get("quality_score"),
        "implementation_state": digest.get("implementation_state"),
    })
    return {
        "record_type": "primitive_lifecycle_vector",
        "primitive_id": digest["primitive_id"],
        "embedding": embed_record({"text": text}),
        "embedding_dim": EMBED_DIM,
        "embedding_model": "deterministic-lexical-hash-v1",
        "embedding_status": "staging_not_promotion_ready",
        "text_digest": f"sha256:{_sha(text, n=32)}",
        "metadata": {
            "label": digest["label"],
            "priority": digest.get("priority"),
            "implementation_state": digest.get("implementation_state"),
            "candidate": True,
            "serves_truth": False,
        },
        "serves_truth": False,
    }


def _is_private_local_session_row(row: dict[str, Any]) -> bool:
    return (
        row.get("source_surface_id") == "local-claude-code"
        or str(row.get("source_candidate") or "").startswith("source:local-claude:")
    )


def _select_primitive_rows(rows: list[dict[str, Any]], *, limit: int, include_private_local_sessions: bool) -> list[dict[str, Any]]:
    candidates = [
        row
        for row in rows
        if row.get("record_type") in {"primitive_opportunity", "primitive_draft"}
        and row.get("serves_truth") is False
        and (include_private_local_sessions or not _is_private_local_session_row(row))
    ]
    candidates.sort(key=lambda row: (
        0 if row.get("source_evidence_status") == "source_backed" else 1,
        str(row.get("source_surface_id") or ""),
        str(row.get("primitive_id") or ""),
    ))
    return candidates[:limit] if limit else candidates


def build_lifecycle(
    foundry_dir: Path,
    out_dir: Path,
    *,
    limit: int,
    include_private_local_sessions: bool = False,
    edge_foundry_path: Path | None = None,
    edge_foundry_limit: int = DEFAULT_EDGE_FOUNDRY_LIMIT,
    edge_foundry_min_quality: int = DEFAULT_EDGE_FOUNDRY_MIN_QUALITY,
    include_private_edge_foundry: bool = False,
    include_edge_jsonl_records: bool = False,
    write: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    sources = _read_jsonl(foundry_dir / SOURCE_CANDIDATES_FILE)
    primitives = _read_jsonl(foundry_dir / PRIMITIVE_DRAFTS_FILE)
    sessions = _read_jsonl(foundry_dir / SYNTHETIC_SESSION_SPECS_FILE)
    rankings = _read_jsonl(foundry_dir / CANDIDATE_RANKINGS_FILE)
    edge_foundry_rows = _read_optional_jsonl(edge_foundry_path)

    source_by_id = _by_candidate_id(sources)
    ranking_by_source = _rankings_by_source(rankings)
    selected_context = _select_primitive_rows(
        primitives,
        limit=limit,
        include_private_local_sessions=include_private_local_sessions,
    )
    selected_edge_foundry = _select_edge_foundry_rows(
        edge_foundry_rows,
        limit=edge_foundry_limit,
        min_quality=edge_foundry_min_quality,
        include_private=include_private_edge_foundry,
        include_jsonl_records=include_edge_jsonl_records,
    )
    selected = [*selected_context, *selected_edge_foundry]
    digests = [
        _digest_row(row, _best_source(row, source_by_id), _best_ranking(row, ranking_by_source))
        for row in selected
    ]
    digests.sort(key=lambda row: (-int(row.get("rank_score") or 0), str(row.get("priority") or ""), str(row["label"])))

    backlog = [_backlog_row(row) for row in digests]
    search_cards = [_search_card(row) for row in digests]
    vectors = [_vector_row(row) for row in digests]
    by_state = Counter(str(row.get("implementation_state") or "unknown") for row in digests)
    by_surface = Counter(str(row.get("source_surface_id") or "unknown") for row in digests)
    manifest = {
        "record_type": "primitive_lifecycle_manifest",
        "created_at": _utc(),
        "foundry_dir": str(foundry_dir),
        "out_dir": str(out_dir),
        "source_candidates": len(sources),
        "source_sessions": len(sessions),
        "context_primitive_rows_available": len(primitives),
        "context_primitive_rows_selected": len(selected_context),
        "edge_foundry_path": str(edge_foundry_path) if edge_foundry_path else None,
        "edge_foundry_rows_available": len(edge_foundry_rows),
        "edge_foundry_rows_selected": len(selected_edge_foundry),
        "edge_foundry_min_quality": edge_foundry_min_quality,
        "edge_foundry_limit": edge_foundry_limit,
        "include_private_edge_foundry": include_private_edge_foundry,
        "include_edge_jsonl_records": include_edge_jsonl_records,
        "primitive_rows_available": len(primitives) + len(selected_edge_foundry),
        "primitive_rows_selected": len(digests),
        "include_private_local_sessions": include_private_local_sessions,
        "implementation_backlog_rows": len(backlog),
        "search_cards": len(search_cards),
        "vector_rows": len(vectors),
        "embedding_dim": EMBED_DIM,
        "embedding_model": "deterministic-lexical-hash-v1",
        "implementation_state_counts": dict(sorted(by_state.items())),
        "source_surface_counts": dict(sorted(by_surface.items())),
        "artifacts": {
            "digests": str(out_dir / "primitive_lifecycle_digests.jsonl"),
            "implementation_backlog": str(out_dir / "primitive_implementation_backlog.jsonl"),
            "search_cards": str(out_dir / "primitive_search_cards.jsonl"),
            "vectors": str(out_dir / "primitive_vector_export.jsonl"),
            "summary": str(out_dir / "summary.md"),
            "manifest": str(out_dir / "manifest.json"),
        },
        "candidate": True,
        "serves_truth": False,
    }

    if write:
        out_dir.mkdir(parents=True, exist_ok=True)
        _write_jsonl(out_dir / "primitive_lifecycle_digests.jsonl", digests)
        _write_jsonl(out_dir / "primitive_implementation_backlog.jsonl", backlog)
        _write_jsonl(out_dir / "primitive_search_cards.jsonl", search_cards)
        _write_jsonl(out_dir / "primitive_vector_export.jsonl", vectors)
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        _write_summary(out_dir / "summary.md", manifest, digests)
    return manifest, digests, backlog, search_cards, vectors


def _write_summary(path: Path, manifest: dict[str, Any], digests: list[dict[str, Any]]) -> None:
    top = digests[:12]
    lines = [
        "# Primitive Source Lifecycle",
        "",
        f"- Updated: `{manifest['created_at']}`",
        f"- Source candidates: `{manifest['source_candidates']}`",
        f"- Context primitive rows available: `{manifest.get('context_primitive_rows_available', 0)}`",
        f"- Context primitive rows selected: `{manifest.get('context_primitive_rows_selected', 0)}`",
        f"- Edge-foundry rows available: `{manifest.get('edge_foundry_rows_available', 0)}`",
        f"- Edge-foundry rows selected: `{manifest.get('edge_foundry_rows_selected', 0)}`",
        f"- Edge-foundry min quality: `{manifest.get('edge_foundry_min_quality')}`",
        f"- Primitive rows available: `{manifest['primitive_rows_available']}`",
        f"- Primitive rows selected: `{manifest['primitive_rows_selected']}`",
        f"- Implementation backlog rows: `{manifest['implementation_backlog_rows']}`",
        f"- Vector rows: `{manifest['vector_rows']}`",
        f"- Embedding: `{manifest['embedding_model']}` dim `{manifest['embedding_dim']}`",
        f"- Serves truth: `{manifest['serves_truth']}`",
        "",
        "## Implementation State Counts",
        "",
        "```json",
        json.dumps(manifest["implementation_state_counts"], indent=2, sort_keys=True),
        "```",
        "",
        "## Top Candidate Rows",
        "",
    ]
    for row in top:
        lines.extend([
            f"- `{row['primitive_id']}`",
            f"  - label: `{row['label']}`",
            f"  - priority: `{row.get('priority')}` score `{row.get('rank_score')}`",
            f"  - state: `{row.get('implementation_state')}`",
            f"  - source: `{row.get('source_surface_id')}`",
            f"  - next: `{row.get('next_action')}`",
        ])
    lines.extend([
        "",
        "## Boundary",
        "",
        "These lifecycle artifacts are planning and search artifacts only. They do not promote primitives, do not claim implementation truth, and do not make vector search production-ready.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_fixture_foundry(root: Path) -> Path:
    foundry = root / "foundry"
    foundry.mkdir(parents=True)
    source = {
        "record_type": "source_candidate",
        "candidate_id": "source:surface-deterministicbuilds-leaderboard",
        "source_surface_id": "surface-deterministicbuilds-leaderboard",
        "source_kind": "deterministic_build_demand_signal",
        "title": "DeterministicBuilds.io requests and proof leaderboard",
        "primitive_opportunities": ["deterministic_build_request"],
        "license_status": "needs_review",
        "serves_truth": False,
    }
    primitive = {
        "record_type": "primitive_opportunity",
        "candidate_stage": "primitive_opportunity",
        "primitive_id": "prim:candidate:surface-deterministicbuilds-leaderboard:deterministic-build-request",
        "slug": "deterministicbuilds-leaderboard.deterministic-build-request",
        "source_candidate": source["candidate_id"],
        "source_surface_id": source["source_surface_id"],
        "contract": {"input": "SourceEvidence", "output": "PrimitiveRecordDraft"},
        "effects": ["net.read"],
        "memory": "inline",
        "cache": "content_hash",
        "trust": "candidate",
        "readiness": "R2_surface_known",
        "source_evidence_status": "needs_source_evidence",
        "proof_requirements": ["license_gate", "contract_review"],
        "promotion_blockers": ["source_evidence_required"],
        "serves_truth": False,
    }
    ranking = {
        "record_type": "candidate_ranking",
        "source_candidate_id": source["candidate_id"],
        "rank_score": 175,
        "priority": "P0",
        "recommended_next_action": "review_source_surface_and_generate_high_value_session_specs",
        "estimated_token_savings_proxy": 18900,
        "serves_truth": False,
    }
    session = {
        "record_type": "synthetic_session_spec",
        "source_candidate": source["candidate_id"],
        "session_spec_id": "synth:deterministicbuilds",
        "serves_truth": False,
    }
    _write_jsonl(foundry / SOURCE_CANDIDATES_FILE, [source])
    _write_jsonl(foundry / PRIMITIVE_DRAFTS_FILE, [primitive])
    _write_jsonl(foundry / CANDIDATE_RANKINGS_FILE, [ranking])
    _write_jsonl(foundry / SYNTHETIC_SESSION_SPECS_FILE, [session])
    return foundry


def _write_fixture_edge_foundry(root: Path) -> Path:
    edge_path = root / "edge_foundry" / "primitive_edge_cards.jsonl"
    edge_row = {
        "primitive_id": "prim:edge:read-uploaded-csv",
        "slug": "fixture.csv.read_uploaded_rows",
        "title": "read_uploaded_rows",
        "kind": "py.fn",
        "candidate": True,
        "serves_truth": False,
        "source_evidence_status": "source_backed",
        "surface_visibility": "public_demo_safe_candidate",
        "source_family": "python_source",
        "source_digest": "fixture-source-digest",
        "source_ref": {"path": "src/demo/csv.py", "line": 7, "name": "read_uploaded_rows", "language": "python"},
        "contract": {"input": "Path", "output": "list[CsvRow]"},
        "input_edge": "Path",
        "output_edge": "list[CsvRow]",
        "blackbox": {"does": "Reads uploaded CSV rows into normalized dictionaries."},
        "effects": ["fs.read"],
        "memory": "inline",
        "cache": "content_hash",
        "runtime_targets": ["local.python"],
        "blocking_keys": ["csv", "uploaded", "rows"],
        "capability_tags": ["data_engineering"],
        "mutations": [
            {
                "mutator": "map_sequence",
                "mutator_agent_id": "mut:deterministic:map_sequence@1",
                "effect_delta": "preserve",
                "serves_truth": False,
                "candidate": True,
            }
        ],
        "quality_score": 86,
        "readiness": "R3_contract_known",
        "trust": "candidate",
    }
    _write_jsonl(edge_path, [edge_row])
    return edge_path


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        foundry = _write_fixture_foundry(root)
        edge_foundry = _write_fixture_edge_foundry(root)
        out_dir = root / "out"
        manifest, digests, backlog, search_cards, vectors = build_lifecycle(
            foundry,
            out_dir,
            limit=10,
            edge_foundry_path=edge_foundry,
            edge_foundry_limit=10,
            edge_foundry_min_quality=70,
            write=True,
        )
        assert manifest["serves_truth"] is False
        assert manifest["context_primitive_rows_selected"] == 1
        assert manifest["edge_foundry_rows_available"] == 1
        assert manifest["edge_foundry_rows_selected"] == 1
        assert manifest["primitive_rows_selected"] == 2
        assert manifest["implementation_backlog_rows"] == 2
        assert manifest["vector_rows"] == 2
        assert (out_dir / "summary.md").exists()
        assert all(row["serves_truth"] is False for row in digests + backlog + search_cards + vectors)
        assert any(row["implementation_state"] == "implementation_backlog" for row in digests)
        edge_digest = next(row for row in digests if row["primitive_id"] == "prim:edge:read-uploaded-csv")
        assert edge_digest["implementation_state"] == "existing_source_ref_candidate"
        assert edge_digest["input_edge"] == "Path"
        assert edge_digest["output_edge"] == "list[CsvRow]"
        edge_card = next(row for row in search_cards if row["primitive_id"] == "prim:edge:read-uploaded-csv")
        assert edge_card["source_ref"]["path"] == "src/demo/csv.py"
        assert edge_card["mutations"][0]["mutator"] == "map_sequence"
        assert all(row["embedding_dim"] == EMBED_DIM for row in vectors)
        assert all(len(row["embedding"]) == EMBED_DIM for row in vectors)
        assert all(row["embedding_status"] == "staging_not_promotion_ready" for row in vectors)
    print("PASS - primitive source lifecycle: foundry rows -> digests, implementation backlog, search cards, vectors, summary; candidate-only.")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--foundry-dir", default=str(DEFAULT_FOUNDRY_DIR))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--edge-foundry-path", default=str(DEFAULT_EDGE_FOUNDRY_PATH))
    parser.add_argument(
        "--edge-foundry-limit",
        type=int,
        default=DEFAULT_EDGE_FOUNDRY_LIMIT,
        help="Max source-backed edge-foundry cards to include; 0 means all eligible cards.",
    )
    parser.add_argument("--edge-foundry-min-quality", type=int, default=DEFAULT_EDGE_FOUNDRY_MIN_QUALITY)
    parser.add_argument("--skip-edge-foundry", action="store_true")
    parser.add_argument("--include-private-edge-foundry", action="store_true")
    parser.add_argument(
        "--include-edge-jsonl-records",
        action="store_true",
        help="Also include generic JSONL record materialization cards; disabled by default to reduce low-signal rows.",
    )
    parser.add_argument(
        "--include-private-local-sessions",
        action="store_true",
        help="Include private local Claude/Codex session-derived rows. Default excludes them from the global lifecycle output.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    manifest, _, _, _, _ = build_lifecycle(
        Path(args.foundry_dir),
        Path(args.out_dir),
        limit=args.limit,
        include_private_local_sessions=args.include_private_local_sessions,
        edge_foundry_path=None if args.skip_edge_foundry else Path(args.edge_foundry_path),
        edge_foundry_limit=args.edge_foundry_limit,
        edge_foundry_min_quality=args.edge_foundry_min_quality,
        include_private_edge_foundry=args.include_private_edge_foundry,
        include_edge_jsonl_records=args.include_edge_jsonl_records,
        write=True,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
