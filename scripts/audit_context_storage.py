#!/usr/bin/env python3
"""Audit file-heavy context, hard-coded settings, and archive candidates.

This script is intentionally non-destructive. It helps long-running agents
identify work that should move from YAML/prose/hard-coded literals into database
rows, registries, schemas, or generated exports.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._config import (
    BACKEND_FAMILY_TERMS,
    DEFAULT_EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_PROFILES,
    EMBEDDING_MODELS,
    LOAD_PLAN_TERMS,
    MODEL_RUNTIME_PROFILES,
    REGISTERED_BACKEND_INFRA_IDENTIFIERS,
    REGISTERED_COMPONENT_REF_IDS,
    REGISTERED_EXAMPLE_MODEL_VALUES,
    REGISTERED_MODEL_CLASS_VALUES,
    REGISTERED_MODEL_FAMILY_TAGS,
    REGISTERED_TOOL_TAGS,
    VECTOR_INDEX_PROFILES,
    VECTOR_STORAGE_BACKENDS,
)
from scripts.db.catalog_row_source import read_jsonl


CATALOG = ROOT / "catalog"
DOCS = ROOT / "docs"
SCRIPTS = ROOT / "scripts"
PROMPTS = ROOT / ".codex" / "prompts"
CONFIG_REGISTRY_PATH = SCRIPTS / "_config.py"
MANIFEST_IMPORT_RECORDS_PATH = ROOT / "db" / "seeds" / "manifest-import" / "manifest_import_record.jsonl"
APPROVED_RUNTIME_SETTING_RESOLVER_PATHS = {
    "scripts/_config.py",
    "scripts/db/runtime_settings.py",
    "scripts/db/settings_registry_export.py",
    "scripts/audit_context_storage.py",
}

TEXT_SUFFIXES = {".md", ".py", ".sql", ".yaml", ".yml", ".json", ".toml"}
DEFAULT_EXCLUDED_PARTS = {
    ".claude",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "_reference",
    "__pycache__",
    "data",
    "dist",
    "node_modules",
    "site",
}
DEFAULT_EXCLUDED_PREFIXES = {
    "scale",
    "scale10k",
    "scale100k",
    "scale100000",
    "scale1m",
}

MODEL_LITERAL_RE = re.compile(
    r"(?P<quote>['\"])(?P<value>"
    r"(?:all-MiniLM-L6-v2|text-embedding-[^'\"]+|gemma\d?:[^'\"]+|"
    r"claude-[^'\"]+|gpt-[^'\"]+|qwen[^'\"]+|mistral[^'\"]+|"
    r"deepseek[^'\"]+|llama[^'\"]+|minimax[^'\"]+)"
    r")(?P=quote)",
    re.IGNORECASE,
)
BACKEND_LITERAL_RE = re.compile(
    r"(?P<quote>['\"])(?P<value>"
    r"(?:jsonl_pgvector_ready|postgres_pgvector|local_docker_pgvector|"
    r"postgres_pgvector_[^'\"]+|[^'\"]*pgvector[^'\"]*|"
    r"opensearch|elasticsearch|qdrant|weaviate|pinecone|chroma|lancedb)"
    r")(?P=quote)",
    re.IGNORECASE,
)
VECTOR_DIMENSION_RE = re.compile(r"\bvector\((?P<dimension>\d+)\)|\bDEFAULT_[A-Z_]*DIMENSIONS\s*=\s*(?P<constant>\d+)")
VERSION_IN_NAME_RE = re.compile(r"(^|[-_])(v\d+|\d+\.\d+\.\d+)([-_]|$)", re.IGNORECASE)
PRODUCT_MARKET_FIT_ACRONYM_RE = re.compile(r"\bPMF\b")
PRIVATE_RUNTIME_SETTING_RESOLVER_RE = re.compile(
    r"os\.environ\.get\([^)]*setting\[[\"']env[\"']\][^)]*setting\[[\"']default[\"']\]"
    r"|[A-Z_]*(?:RUNTIME_)?SETTINGS\[[^\]]+\]\[[\"']default[\"']\]"
)
APPROVED_RUNTIME_SETTING_WRAPPER_RE = re.compile(r"\breturn\s+runtime_setting\(")

# A quoted token that ends in a documentation/source file extension is a
# filename, never a model id, even when it matches a model-family prefix such as
# `claude-` (e.g. the handoff doc "CLAUDE-CODE.md"). Skipping these removes a
# false positive without weakening real model-literal detection.
NON_MODEL_FILE_SUFFIXES = (".md", ".py", ".txt", ".json", ".yaml", ".yml", ".toml", ".sql", ".html")

REGISTERED_MODEL_VALUES = {
    *EMBEDDING_MODELS.keys(),
    *EMBEDDING_MODEL_PROFILES.keys(),
    *MODEL_RUNTIME_PROFILES.keys(),
    *REGISTERED_EXAMPLE_MODEL_VALUES.keys(),
    *(str(profile.get("model")) for profile in EMBEDDING_MODEL_PROFILES.values() if profile.get("model")),
    *(str(profile.get("model")) for profile in MODEL_RUNTIME_PROFILES.values() if profile.get("model")),
}
REGISTERED_TOOL_TAG_VALUES = set(REGISTERED_TOOL_TAGS.keys())
REGISTERED_MODEL_FAMILY_TAG_VALUES = set(REGISTERED_MODEL_FAMILY_TAGS.keys())
REGISTERED_MODEL_CLASS_LITERAL_VALUES = set(REGISTERED_MODEL_CLASS_VALUES.keys())
REGISTERED_BACKEND_VALUES = set(VECTOR_STORAGE_BACKENDS.keys()) | set(
    REGISTERED_BACKEND_INFRA_IDENTIFIERS.keys()
)
REGISTERED_BACKEND_FAMILY_VALUES = set(BACKEND_FAMILY_TERMS.keys())
REGISTERED_TERMINOLOGY_VALUES = set(LOAD_PLAN_TERMS.keys())
REGISTERED_COMPONENT_REF_VALUES = set(REGISTERED_COMPONENT_REF_IDS.keys())
REGISTERED_VECTOR_DIMENSIONS = {
    str(DEFAULT_EMBEDDING_DIMENSIONS),
    *(str(dimensions) for dimensions in EMBEDDING_MODELS.values()),
    *(str(profile.get("dimensions")) for profile in VECTOR_INDEX_PROFILES.values() if profile.get("dimensions")),
}

ARCHIVE_REVIEW_STATES = {
    "candidate": "Needs curator review; no file move has been approved.",
    "keep_active": "Keep in active docs and update references if needed.",
    "supersede": "Add a supersession note and canonical replacement pointer.",
    "archive_ready": "Ready for an approved archive move after references are checked.",
}

ARCHIVE_REASON_SEVERITY = {
    "uses product-market-fit acronym; prefer product-market fit": 1,
    "contains version-like prose or filename; check freshness": 1,
    "contains TODO/FIXME": 2,
    "self-identifies as superseded/deprecated": 3,
    "likely old broad-platform framing; compare against current Baltor wedge docs": 2,
    "operational current-state file; review timestamps before reusing as durable context": 2,
}

CANONICAL_REPLACEMENT_HINTS = (
    (
        re.compile(r"product[-_ ]market[-_ ]fit|wedge|gtm|buyer|market", re.IGNORECASE),
        "docs/architecture/baltor-product-market-fit-and-wedge-strategy.md",
    ),
    (
        re.compile(r"context[-_ ]object|context[-_ ]fabric|object[-_ ]graph", re.IGNORECASE),
        "docs/architecture/baltor-context-object-standards.md",
    ),
    (
        re.compile(r"mcp|gateway", re.IGNORECASE),
        "docs/architecture/baltor-mcp-context-gateway.md",
    ),
    (
        re.compile(r"model[-_ ]routing|rerank|lora", re.IGNORECASE),
        "docs/architecture/baltor-model-routing-ladder.md",
    ),
    (
        re.compile(r"local[-_ ]encrypted|memory|sync", re.IGNORECASE),
        "docs/architecture/baltor-local-encrypted-memory-sync.md",
    ),
    (
        re.compile(r"admin[-_ ]demo|context[-_ ]control|current[-_ ]state", re.IGNORECASE),
        "docs/codex/baltor-context-control-current-state.md",
    ),
)

ROTTED_CONTEXT_BASES = (
    DOCS / "architecture",
    DOCS / "codex",
    DOCS / "strategy",
    DOCS / "research",
    DOCS / "spec",
    DOCS / "concepts",
    DOCS / "howto",
    PROMPTS,
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    if parts & DEFAULT_EXCLUDED_PARTS:
        return True
    rel_parts = path.relative_to(ROOT).parts if path.is_relative_to(ROOT) else path.parts
    return any(part in DEFAULT_EXCLUDED_PREFIXES for part in rel_parts)


def iter_files(base: Path, suffixes: set[str]) -> list[Path]:
    if not base.exists():
        return []
    return [
        path
        for path in base.rglob("*")
        if path.is_file()
        and path.suffix in suffixes
        and not is_excluded(path)
    ]


def audit_yaml_manifests() -> dict[str, Any]:
    by_type: Counter[str] = Counter()
    with_version_in_slug: list[str] = []
    rubric_dimension_counts: dict[str, int] = {}

    manifest_records = read_jsonl(MANIFEST_IMPORT_RECORDS_PATH)
    for record in manifest_records:
        manifest_path = str(record.get("manifest_path") or "")
        component_type = str(record.get("component_type") or "")
        if not manifest_path or not component_type:
            continue
        by_type[component_type] += 1
        slug = Path(manifest_path).stem
        if VERSION_IN_NAME_RE.search(slug):
            with_version_in_slug.append(manifest_path)
        if component_type == "rubric":
            row_counts = record.get("row_counts")
            if isinstance(row_counts, dict) and isinstance(row_counts.get("rubric_dimensions"), int):
                rubric_dimension_counts[manifest_path] = int(row_counts["rubric_dimensions"])

    largest_rubrics = sorted(
        rubric_dimension_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:20]

    return {
        "manifest_count": len(manifest_records),
        "by_type": dict(sorted(by_type.items())),
        "version_like_slugs": with_version_in_slug[:100],
        "version_like_slug_count": len(with_version_in_slug),
        "largest_rubrics": largest_rubrics,
        "source": {
            "kind": "manifest_import_record",
            "path": rel(MANIFEST_IMPORT_RECORDS_PATH),
        },
        "database_migration_hint": (
            "Keep YAML as seed/export manifests; expand component, version, "
            "rubric_dimension, context object, mask, and transformer rows in Postgres."
        ),
    }


def audit_hardcoded_settings() -> dict[str, Any]:
    model_literals: dict[str, list[dict[str, Any]]] = defaultdict(list)
    tool_tag_literals: dict[str, list[dict[str, Any]]] = defaultdict(list)
    model_family_tag_literals: dict[str, list[dict[str, Any]]] = defaultdict(list)
    model_class_literals: dict[str, list[dict[str, Any]]] = defaultdict(list)
    backend_literals: dict[str, list[dict[str, Any]]] = defaultdict(list)
    terminology_literals: dict[str, list[dict[str, Any]]] = defaultdict(list)
    component_ref_literals: dict[str, list[dict[str, Any]]] = defaultdict(list)
    vector_dimensions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    registered_vector_dimensions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    private_runtime_setting_resolvers: list[dict[str, Any]] = []
    approved_runtime_setting_wrappers: list[dict[str, Any]] = []

    for path in iter_files(ROOT, TEXT_SUFFIXES):
        if path.parts and path.parts[0] == ".git":
            continue
        is_config_registry = path == CONFIG_REGISTRY_PATH
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            relative_path = rel(path)
            if (
                path.suffix == ".py"
                and relative_path not in APPROVED_RUNTIME_SETTING_RESOLVER_PATHS
                and APPROVED_RUNTIME_SETTING_WRAPPER_RE.search(line)
            ):
                approved_runtime_setting_wrappers.append({
                    "path": relative_path,
                    "line": line_number,
                    "snippet": line.strip()[:160],
                })
            if (
                path.suffix == ".py"
                and relative_path not in APPROVED_RUNTIME_SETTING_RESOLVER_PATHS
                and PRIVATE_RUNTIME_SETTING_RESOLVER_RE.search(line)
            ):
                private_runtime_setting_resolvers.append({
                    "path": relative_path,
                    "line": line_number,
                    "snippet": line.strip()[:160],
                    "recommended_owner": "scripts.db.runtime_settings.runtime_setting",
                })
            for match in MODEL_LITERAL_RE.finditer(line):
                if is_config_registry:
                    continue
                value = match.group("value")
                if value.isupper() and "_" in value:
                    continue
                if value.lower().endswith(NON_MODEL_FILE_SUFFIXES):
                    continue  # filename matched a model prefix (e.g. CLAUDE-CODE.md)
                location = {"path": rel(path), "line": line_number}
                if value in REGISTERED_TOOL_TAG_VALUES:
                    tool_tag_literals[value].append(location)
                elif value in REGISTERED_MODEL_FAMILY_TAG_VALUES:
                    model_family_tag_literals[value].append(location)
                elif value in REGISTERED_MODEL_CLASS_LITERAL_VALUES:
                    model_class_literals[value].append(location)
                else:
                    model_literals[value].append(location)
            for match in BACKEND_LITERAL_RE.finditer(line):
                if is_config_registry:
                    continue
                value = match.group("value")
                if "{" in value and "}" in value:
                    continue
                if any(char.isspace() for char in value) and value not in REGISTERED_TERMINOLOGY_VALUES:
                    continue
                if value in REGISTERED_COMPONENT_REF_VALUES:
                    component_ref_literals[value].append({"path": rel(path), "line": line_number})
                elif value in REGISTERED_TERMINOLOGY_VALUES or value in REGISTERED_BACKEND_FAMILY_VALUES:
                    terminology_literals[value].append({"path": rel(path), "line": line_number})
                else:
                    backend_literals[value].append({"path": rel(path), "line": line_number})
            for match in VECTOR_DIMENSION_RE.finditer(line):
                if is_config_registry:
                    continue
                dimension = match.group("dimension") or match.group("constant")
                if dimension:
                    location = {"path": rel(path), "line": line_number}
                    if dimension in REGISTERED_VECTOR_DIMENSIONS:
                        registered_vector_dimensions[dimension].append(location)
                    else:
                        vector_dimensions[dimension].append(location)

    repeated_model_literals = {
        key: value
        for key, value in sorted(model_literals.items())
        if len(value) > 1
    }
    repeated_vector_dimensions = {
        key: value
        for key, value in sorted(vector_dimensions.items())
        if len(value) > 1
    }
    repeated_tool_tag_literals = {
        key: value
        for key, value in sorted(tool_tag_literals.items())
        if len(value) > 1
    }
    repeated_model_family_tag_literals = {
        key: value
        for key, value in sorted(model_family_tag_literals.items())
        if len(value) > 1
    }
    repeated_model_class_literals = {
        key: value
        for key, value in sorted(model_class_literals.items())
        if len(value) > 1
    }
    repeated_registered_vector_dimensions = {
        key: value
        for key, value in sorted(registered_vector_dimensions.items())
        if len(value) > 1
    }
    repeated_backend_literals = {
        key: value
        for key, value in sorted(backend_literals.items())
        if len(value) > 1
    }
    repeated_terminology_literals = {
        key: value
        for key, value in sorted(terminology_literals.items())
        if len(value) > 1
    }
    repeated_component_ref_literals = {
        key: value
        for key, value in sorted(component_ref_literals.items())
        if len(value) > 1
    }
    unregistered_model_literals = {
        key: value
        for key, value in repeated_model_literals.items()
        if key not in REGISTERED_MODEL_VALUES
    }
    unregistered_backend_literals = {
        key: value
        for key, value in repeated_backend_literals.items()
        if key not in REGISTERED_BACKEND_VALUES
    }

    migration_candidates = []
    for value, locations in unregistered_model_literals.items():
        migration_candidates.append({
            "kind": "model_literal",
            "value": value,
            "occurrences": len(locations),
            "first_locations": locations[:5],
            "recommended_owner": "scripts._config model registry or database setting_profile row",
        })
    for value, locations in unregistered_backend_literals.items():
        migration_candidates.append({
            "kind": "backend_literal",
            "value": value,
            "occurrences": len(locations),
            "first_locations": locations[:5],
            "recommended_owner": "scripts._config backend registry or database setting_profile row",
        })
    for value, locations in repeated_vector_dimensions.items():
        migration_candidates.append({
            "kind": "vector_dimension",
            "value": value,
            "occurrences": len(locations),
            "first_locations": locations[:5],
            "recommended_owner": "scripts._config DEFAULT_EMBEDDING_DIMENSIONS or database vector_index_profile row",
        })
    migration_candidates.sort(key=lambda item: (-int(item["occurrences"]), str(item["kind"]), str(item["value"])))

    return {
        "repeated_model_literal_count": len(repeated_model_literals),
        "repeated_model_literals": repeated_model_literals,
        "unregistered_repeated_model_literal_count": len(unregistered_model_literals),
        "unregistered_repeated_model_literals": unregistered_model_literals,
        "registered_repeated_tool_tag_literal_count": len(repeated_tool_tag_literals),
        "registered_repeated_tool_tag_literals": repeated_tool_tag_literals,
        "registered_repeated_model_family_tag_literal_count": len(repeated_model_family_tag_literals),
        "registered_repeated_model_family_tag_literals": repeated_model_family_tag_literals,
        "registered_repeated_model_class_literal_count": len(repeated_model_class_literals),
        "registered_repeated_model_class_literals": repeated_model_class_literals,
        "repeated_backend_literal_count": len(repeated_backend_literals),
        "repeated_backend_literals": repeated_backend_literals,
        "unregistered_repeated_backend_literal_count": len(unregistered_backend_literals),
        "unregistered_repeated_backend_literals": unregistered_backend_literals,
        "registered_repeated_terminology_literal_count": len(repeated_terminology_literals),
        "registered_repeated_terminology_literals": repeated_terminology_literals,
        "registered_repeated_component_ref_literal_count": len(repeated_component_ref_literals),
        "registered_repeated_component_ref_literals": repeated_component_ref_literals,
        "registered_repeated_vector_dimension_count": len(repeated_registered_vector_dimensions),
        "registered_repeated_vector_dimensions": repeated_registered_vector_dimensions,
        "repeated_vector_dimension_count": len(repeated_vector_dimensions),
        "repeated_vector_dimensions": repeated_vector_dimensions,
        "private_runtime_setting_resolver_bypass_count": len(private_runtime_setting_resolvers),
        "private_runtime_setting_resolver_bypasses": private_runtime_setting_resolvers[:100],
        "approved_runtime_setting_wrapper_count": len(approved_runtime_setting_wrappers),
        "approved_runtime_setting_wrappers": approved_runtime_setting_wrappers[:100],
        "migration_candidates": migration_candidates[:50],
        "database_migration_hint": (
            "Move model IDs, embedding dimensions, thresholds, route names, "
            "and backend choices into a settings registry or database-backed "
            "profile tables before duplicating them in code/docs."
        ),
    }


def infer_canonical_replacement(path: Path, text: str) -> str | None:
    haystack = f"{rel(path)}\n{text[:5000]}"
    for pattern, replacement in CANONICAL_REPLACEMENT_HINTS:
        if pattern.search(haystack) and replacement != rel(path):
            return replacement
    return None


def build_archive_candidate(path: Path, reasons: list[str], text: str) -> dict[str, Any]:
    severity_score = sum(ARCHIVE_REASON_SEVERITY.get(reason, 1) for reason in reasons)
    if "self-identifies as superseded/deprecated" in reasons:
        suggested_action = "supersede"
    elif severity_score >= 4:
        suggested_action = "supersede"
    else:
        suggested_action = "candidate"

    return {
        "path": rel(path),
        "status": "candidate",
        "suggested_action": suggested_action,
        "severity_score": severity_score,
        "confidence": "medium" if severity_score >= 3 else "low",
        "canonical_replacement_hint": infer_canonical_replacement(path, text),
        "reasons": reasons,
        "required_next_checks": [
            "confirm the file is not a canonical spec, schema, active prompt, or current operating runbook",
            "check references from docs, catalog manifests, scripts, prompts, and generated site pages",
            "add a supersession note or redirect pointer before any approved move",
            "run validation after the approved move",
        ],
    }


def audit_rotted_context_candidates() -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    duplicate_titles: dict[str, list[str]] = defaultdict(list)

    candidate_paths: list[Path] = []
    for base in ROTTED_CONTEXT_BASES:
        candidate_paths.extend(iter_files(base, {".md"}))

    for path in sorted(set(candidate_paths)):
        text = path.read_text(encoding="utf-8", errors="ignore")
        first_heading = None
        for line in text.splitlines():
            if line.startswith("# "):
                first_heading = line[2:].strip()
                break
        if first_heading:
            duplicate_titles[first_heading.lower()].append(rel(path))

        reasons: list[str] = []
        if PRODUCT_MARKET_FIT_ACRONYM_RE.search(text):
            reasons.append("uses product-market-fit acronym; prefer product-market fit")
        if "v0." in text or "v1" in path.stem:
            reasons.append("contains version-like prose or filename; check freshness")
        if "TODO" in text or "FIXME" in text:
            reasons.append("contains TODO/FIXME")
        if "superseded" in text.lower() or "deprecated" in text.lower():
            reasons.append("self-identifies as superseded/deprecated")
        if (
            path.parent == DOCS / "architecture"
            and any(term in path.stem for term in ("component", "factory", "hundred-million", "daily"))
        ):
            reasons.append("likely old broad-platform framing; compare against current Baltor wedge docs")
        if path.name.endswith("current-state.md") or path.name.endswith("session-ledger.md"):
            reasons.append("operational current-state file; review timestamps before reusing as durable context")

        if reasons:
            candidates.append(build_archive_candidate(path, reasons, text))

    duplicate_heading_candidates = [
        {"heading": heading, "paths": paths}
        for heading, paths in sorted(duplicate_titles.items())
        if len(paths) > 1
    ][:100]

    return {
        "candidate_count": len(candidates),
        "candidate_review_states": ARCHIVE_REVIEW_STATES,
        "candidates": sorted(
            candidates,
            key=lambda candidate: (
                -candidate["severity_score"],
                candidate["path"],
            ),
        )[:200],
        "duplicate_heading_candidates": duplicate_heading_candidates,
        "archive_policy": (
            "Do not move candidates automatically. Verify references, create "
            "an archive note or alias, move to docs/archive only with approval, "
            "and validate afterwards."
        ),
    }


def build_report(rotted_only: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {
        "repo": rel(ROOT),
        "rotted_context_candidates": audit_rotted_context_candidates(),
    }
    if rotted_only:
        return report

    report["yaml_manifests"] = audit_yaml_manifests()
    report["hardcoded_settings"] = audit_hardcoded_settings()
    return report


def print_markdown(report: dict[str, Any]) -> None:
    print("# Context Storage Audit")
    print()
    manifests = report.get("yaml_manifests")
    if manifests:
        print("## YAML Manifests")
        print()
        print(f"- Manifest count: {manifests['manifest_count']}")
        print(f"- Version-like slug count: {manifests['version_like_slug_count']}")
        print("- By type:")
        for key, value in manifests["by_type"].items():
            print(f"  - {key}: {value}")
        print()

    hardcoded = report.get("hardcoded_settings")
    if hardcoded:
        print("## Hard-Coded Settings")
        print()
        print(f"- Repeated model literal groups: {hardcoded['repeated_model_literal_count']}")
        print(f"- Unregistered repeated model literal groups: {hardcoded['unregistered_repeated_model_literal_count']}")
        print(f"- Registered repeated tool/source tag groups: {hardcoded['registered_repeated_tool_tag_literal_count']}")
        print(f"- Registered repeated model-family tag groups: {hardcoded['registered_repeated_model_family_tag_literal_count']}")
        print(f"- Registered repeated model-class groups: {hardcoded['registered_repeated_model_class_literal_count']}")
        print(f"- Repeated backend literal groups: {hardcoded['repeated_backend_literal_count']}")
        print(f"- Unregistered repeated backend literal groups: {hardcoded['unregistered_repeated_backend_literal_count']}")
        print(f"- Registered repeated terminology groups: {hardcoded['registered_repeated_terminology_literal_count']}")
        print(f"- Registered repeated component-ref groups: {hardcoded['registered_repeated_component_ref_literal_count']}")
        print(f"- Registered repeated vector dimension groups: {hardcoded['registered_repeated_vector_dimension_count']}")
        print(f"- Repeated vector dimension groups: {hardcoded['repeated_vector_dimension_count']}")
        print(f"- Private runtime setting resolver bypasses: {hardcoded['private_runtime_setting_resolver_bypass_count']}")
        print(f"- Approved runtime setting resolver wrappers: {hardcoded['approved_runtime_setting_wrapper_count']}")
        print("- Top migration candidates:")
        for candidate in hardcoded["migration_candidates"][:10]:
            first = candidate["first_locations"][0] if candidate["first_locations"] else {}
            location = f"{first.get('path')}:{first.get('line')}" if first else "unknown"
            print(
                f"  - {candidate['kind']} {candidate['value']!r}: "
                f"{candidate['occurrences']} occurrences; first {location}"
            )
        print()
    print("## Rotted Context Candidates")
    print()
    rotted = report["rotted_context_candidates"]
    print(f"- Candidate count: {rotted['candidate_count']}")
    for candidate in rotted["candidates"][:25]:
        reasons = "; ".join(candidate["reasons"])
        replacement = candidate.get("canonical_replacement_hint") or "none inferred"
        print(
            "  - "
            f"{candidate['path']}: severity={candidate['severity_score']}; "
            f"action={candidate['suggested_action']}; replacement={replacement}; "
            f"{reasons}"
        )


def print_archive_ledger(report: dict[str, Any]) -> None:
    rotted = report["rotted_context_candidates"]
    print("# Archive Candidate Ledger")
    print()
    print("Generated by `python3 scripts/audit_context_storage.py --archive-ledger`.")
    print("This ledger is advisory and non-destructive; it does not approve moves.")
    print()
    print("## Review States")
    print()
    for state, description in rotted["candidate_review_states"].items():
        print(f"- `{state}`: {description}")
    print()
    print("## Candidates")
    print()
    print("| Severity | Status | Suggested action | Path | Canonical replacement hint | Reasons |")
    print("|---:|---|---|---|---|---|")
    for candidate in rotted["candidates"]:
        reasons = "; ".join(candidate["reasons"])
        replacement = candidate.get("canonical_replacement_hint") or ""
        print(
            "| "
            f"{candidate['severity_score']} | "
            f"{candidate['status']} | "
            f"{candidate['suggested_action']} | "
            f"`{candidate['path']}` | "
            f"`{replacement}` | "
            f"{reasons} |"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", action="store_true", help="print a compact Markdown report")
    parser.add_argument(
        "--archive-ledger",
        action="store_true",
        help="print a reviewable Markdown ledger of archive candidates",
    )
    parser.add_argument(
        "--rotted-only",
        action="store_true",
        help="skip manifest and hard-coded setting scans",
    )
    args = parser.parse_args()

    report = build_report(rotted_only=args.rotted_only or args.archive_ledger)
    if args.archive_ledger:
        print_archive_ledger(report)
    elif args.markdown:
        print_markdown(report)
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
