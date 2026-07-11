#!/usr/bin/env python3
"""Continuous source -> LLM -> primitive database feed loop.

This is the governed loop for mining broad real-world surfaces into primitive
candidates:

source queue -> policy snapshot -> hundreds-question decomposition -> primitive
graphs/examples -> candidate database feed -> source_to_primitive_foundry store.

The loop is intentionally safe by default:

* no raw source body is written to disk;
* live fetching is opt-in with robots/ToS checks;
* LLM calls are opt-in and batch the same question bank used by the offline
  decomposer;
* every generated row is candidate-only and `serves_truth=false`.

Run:

    python3 scripts/continuous_primitive_scrape_loop.py --self-test
    python3 scripts/continuous_primitive_scrape_loop.py --once --source-limit 25
    python3 scripts/continuous_primitive_scrape_loop.py --watch --interval 3600 --source-limit 500
"""
from __future__ import annotations

import sys
from pathlib import Path

_SBC = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "scripts" / "_repo_paths.py").exists()),
    Path(__file__).resolve().parents[1],
)
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))

from scripts._repo_paths import install as _install  # noqa: E402

_install()

import argparse
import hashlib
import json
import tempfile
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from scripts._llm_client import DEFAULT_PROVIDER, PROVIDERS, chat, resolve_provider  # noqa: E402
from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts.source_to_primitive_foundry import (  # noqa: E402
    DEFAULT_COMPONENTS_PER_SOURCE,
    DEFAULT_MAX_SOURCES_PER_PARTITION,
    PROFILE_BY_KIND,
    RAW_TEXT_FIELDS,
    run_foundry,
)


RECORD_TYPE = "continuous_primitive_scrape_loop"
DEFAULT_OUT_DIR = _resource("data") / "dev-intel" / "continuous_primitive_scrape_loop"
DEFAULT_SOURCE_LIMIT = 25
DEFAULT_QUESTION_COUNT = 240
DEFAULT_LLM_BATCH_SIZE = 40
DEFAULT_MAX_LLM_CONTEXT_CHARS = 16000
DEFAULT_HTTP_TIMEOUT = 30
USER_AGENT = "OpenHubForAI-primitive-foundry/1.0 (+https://openhubforai.com)"
CHARS_PER_TOKEN = 4
RAW_STORAGE_FIELDS = set(RAW_TEXT_FIELDS) | {
    "article_text",
    "content",
    "content_text",
    "full_text",
    "notebook_json",
    "page_html",
    "pdf_body",
}


@dataclass(frozen=True)
class SourcePolicy:
    source_kind: str
    foundry_source_kind: str
    description: str
    default_locator_template: str
    publisher_class: str
    allowed_capture: tuple[str, ...]
    preferred_connectors: tuple[str, ...]
    robots_required: bool = True
    tos_sensitive: bool = False
    raw_body_default: bool = False
    license_status: str = "metadata_and_citation_first"
    source_risk: str = "medium"


SOURCE_POLICIES: tuple[SourcePolicy, ...] = (
    SourcePolicy(
        "news",
        "web_page",
        "News article, RSS item, or publication page.",
        "seed://news/{index}",
        "news_publisher",
        ("metadata", "rss_item", "citation", "short_excerpt_if_allowed"),
        ("rss", "publisher_api", "sitemap", "licensed_feed"),
        tos_sensitive=True,
        license_status="metadata_citation_and_short_excerpt_only",
        source_risk="high",
    ),
    SourcePolicy(
        "app",
        "app",
        "Application workflow, product surface, SaaS flow, or internal tool.",
        "seed://app/{index}",
        "workflow_app",
        ("metadata", "browser_snapshot", "public_api_schema", "first_party_docs"),
        ("browser_capture", "openapi", "storybook", "first_party_repo"),
        license_status="first_party_or_public_metadata",
    ),
    SourcePolicy(
        "system",
        "repo",
        "Software system, architecture, repository, or production stack.",
        "seed://system/{index}",
        "software_system",
        ("metadata", "repo_inventory", "api_schema", "architecture_notes"),
        ("git_metadata", "github_api", "docs_sitemap", "openapi"),
        license_status="metadata_and_license_review_required",
    ),
    SourcePolicy(
        "kaggle_notebook",
        "kaggle_project",
        "Kaggle notebook, competition kernel, dataset workflow, or ML experiment.",
        "seed://kaggle/{index}",
        "competition_or_kernel",
        ("metadata", "dataset_card", "notebook_outline", "competition_metric"),
        ("kaggle_api", "metadata_snapshot", "notebook_pull_when_allowed"),
        tos_sensitive=True,
        license_status="metadata_first_kernel_license_review_required",
        source_risk="high",
    ),
    SourcePolicy(
        "medium_article",
        "web_page",
        "Medium or blog article where terms and copyright posture need review.",
        "seed://medium/{index}",
        "article_publisher",
        ("metadata", "citation", "short_excerpt_if_allowed"),
        ("rss", "publisher_api", "manual_citation"),
        tos_sensitive=True,
        license_status="metadata_citation_only_until_license_review",
        source_risk="high",
    ),
    SourcePolicy(
        "system_design",
        "app",
        "System-design interview prompt, architecture writeup, or design discussion.",
        "seed://system-design/{index}",
        "system_design_source",
        ("metadata", "diagram_summary", "architecture_notes", "citation"),
        ("public_docs", "repo_inventory", "manual_citation"),
        license_status="metadata_and_citation_first",
    ),
    SourcePolicy(
        "textbook",
        "paper",
        "Textbook or course material; use metadata and citations unless licensed.",
        "seed://textbook/{index}",
        "book_or_course",
        ("metadata", "citation", "table_of_contents", "short_excerpt_if_allowed"),
        ("open_textbook_api", "library_metadata", "manual_citation"),
        tos_sensitive=True,
        license_status="metadata_citation_only_until_license_review",
        source_risk="high",
    ),
    SourcePolicy(
        "google_scholar",
        "paper",
        "Scholar search result or citation cluster; do not scrape search pages by default.",
        "seed://google-scholar/{index}",
        "citation_index",
        ("metadata", "citation", "doi", "public_abstract_if_available"),
        ("scholarly_metadata_api", "doi_crossref", "semantic_scholar", "manual_citation"),
        tos_sensitive=True,
        license_status="metadata_citation_only_no_search_page_scrape",
        source_risk="high",
    ),
    SourcePolicy(
        "paper_publication",
        "paper",
        "Paper publication page, preprint record, DOI page, or technical report.",
        "seed://paper/{index}",
        "paper_publisher",
        ("metadata", "doi", "public_abstract", "citation", "open_license_pdf_when_allowed"),
        ("crossref", "arxiv", "semantic_scholar", "publisher_api"),
        license_status="metadata_abstract_first_pdf_license_review_required",
    ),
    SourcePolicy(
        "repo",
        "repo",
        "Repository, package, codebase, or generated project.",
        "seed://repo/{index}",
        "open_source_or_first_party_repo",
        ("metadata", "repo_inventory", "file_digest", "license_file", "api_schema"),
        ("git_metadata", "github_api", "archive_download", "local_inventory"),
        license_status="license_file_required_before_promotion",
    ),
    SourcePolicy(
        "discussion",
        "discussion",
        "Issue, forum, Q&A thread, social technical discussion, or review thread.",
        "seed://discussion/{index}",
        "forum_or_issue_tracker",
        ("metadata", "citation", "thread_outline", "accepted_answer_if_public"),
        ("forum_api", "issue_api", "rss", "manual_citation"),
        tos_sensitive=True,
        license_status="metadata_citation_first_thread_license_review_required",
        source_risk="high",
    ),
    SourcePolicy(
        "website",
        "website",
        "Website, product page, documentation site, or navigable web surface.",
        "seed://website/{index}",
        "website",
        ("metadata", "sitemap", "browser_snapshot", "public_docs"),
        ("sitemap", "rss", "browser_capture", "publisher_api"),
        license_status="metadata_and_citation_first",
    ),
)

POLICY_BY_KIND = {policy.source_kind: policy for policy in SOURCE_POLICIES}


SOURCE_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "source_kind": "news",
        "title": "AI product release news item",
        "summary": "Publication metadata, claims, timeline, affected users, product changes, pricing signals, and follow-up verification tasks.",
        "tags": ["news", "claim_extract", "change_detect", "citation_capture"],
    },
    {
        "source_kind": "app",
        "title": "Operations approval SaaS workflow",
        "summary": "Role-gated workflow states, approval steps, notification rules, exports, audit events, error states, and integration targets.",
        "tags": ["app", "state_model", "workflow_step", "permission_gate", "notification_rule", "export_surface"],
    },
    {
        "source_kind": "system",
        "title": "Event-driven billing system",
        "summary": "Services, queues, idempotency keys, schema validation, retries, observability, deployment topology, and proof receipts.",
        "tags": ["system", "repo_inventory", "api_route", "job_queue", "schema_validator", "ci_workflow"],
    },
    {
        "source_kind": "kaggle_notebook",
        "title": "Kaggle tabular modeling notebook",
        "summary": "Dataset loading, leakage checks, null handling, feature engineering, cross-validation, model training, metric scoring, and submission writer.",
        "tags": ["kaggle", "dataset_loader", "feature_engineering", "training_loop", "metric_scorer", "submission_writer"],
    },
    {
        "source_kind": "medium_article",
        "title": "Engineering blog architecture article",
        "summary": "Architecture pattern, tradeoffs, implementation outline, failure modes, diagrams, code snippets, and source citations.",
        "tags": ["article", "method_decompose", "page_fetch", "content_extract", "citation_capture"],
    },
    {
        "source_kind": "system_design",
        "title": "Design a global notifications system",
        "summary": "Requirements, APIs, data model, delivery channels, queueing, throttling, fanout, observability, failure handling, and cost tradeoffs.",
        "tags": ["system_design", "api_route", "state_model", "job_queue", "notification_rule", "test_harness"],
    },
    {
        "source_kind": "textbook",
        "title": "Distributed systems chapter",
        "summary": "Definitions, invariants, algorithms, consistency models, failure handling, examples, exercises, and citations.",
        "tags": ["textbook", "claim_extract", "method_decompose", "proof_sketch", "edge_case_catalog"],
    },
    {
        "source_kind": "google_scholar",
        "title": "Citation cluster for retrieval augmented generation",
        "summary": "Paper titles, authors, venues, citations, abstract handles, related work clusters, benchmark families, and replication leads.",
        "tags": ["scholar", "citation_graph", "claim_extract", "benchmark_table", "replication_protocol"],
    },
    {
        "source_kind": "paper_publication",
        "title": "ML systems paper publication page",
        "summary": "Public abstract, method decomposition, benchmark table, ablations, limitations, replication protocol, and citation graph.",
        "tags": ["paper", "claim_extract", "method_decompose", "benchmark_table", "replication_protocol", "citation_graph"],
    },
    {
        "source_kind": "repo",
        "title": "Open-source data pipeline repository",
        "summary": "Repository inventory, API routes, schemas, job queue, tests, CI workflow, deployment manifests, and release notes.",
        "tags": ["repo", "repo_inventory", "api_route", "schema_validator", "job_queue", "test_harness", "ci_workflow"],
    },
    {
        "source_kind": "discussion",
        "title": "Developer issue discussion",
        "summary": "Questions, pain points, workarounds, accepted answer pattern, unresolved gaps, evidence strength, and consensus signal.",
        "tags": ["discussion", "question_cluster", "answer_pattern", "pain_point", "workaround", "consensus_signal"],
    },
    {
        "source_kind": "website",
        "title": "SaaS onboarding website",
        "summary": "Navigation, landing sections, signup form, pricing cards, docs links, analytics events, responsive states, and support flows.",
        "tags": ["website", "navigation_map", "page_template", "form_flow", "content_card", "analytics_event"],
    },
)

QUESTION_DIMENSIONS: tuple[str, ...] = (
    "component_inventory",
    "primitive_boundaries",
    "input_contracts",
    "output_contracts",
    "state_model",
    "data_model",
    "control_flow",
    "algorithmic_strategy",
    "ui_structure",
    "design_system_mapping",
    "language_variants",
    "runtime_variants",
    "architecture_variants",
    "storage_variants",
    "api_surface",
    "workflow_orchestration",
    "error_handling",
    "security_privacy",
    "permissions",
    "observability",
    "testing",
    "benchmarking",
    "cost_latency",
    "failure_modes",
    "reproducibility",
    "license_policy",
    "source_provenance",
    "remix_axes",
    "composition_edges",
    "promotion_gate",
    "example_generation",
    "documentation_shape",
)

QUESTION_PERSPECTIVES: tuple[str, ...] = (
    "python",
    "typescript",
    "sql",
    "rust",
    "frontend",
    "backend",
    "data_pipeline",
    "ml_notebook",
    "agent_workflow",
    "cloud_runtime",
    "edge_runtime",
    "mobile",
    "design_system",
    "security_review",
    "test_harness",
    "ops_runbook",
)

QUESTION_TEMPLATES: tuple[str, ...] = (
    "List the primitives needed to rebuild the {dimension} aspects of this source for a {perspective} implementation.",
    "Which components, contracts, dependencies, and proof checks define the {dimension} layer when targeting {perspective}?",
    "What alternative {perspective} designs could satisfy the same {dimension} requirement, and what primitive variations do they imply?",
    "What gaps would block a primitive-based rebuild of the {dimension} layer in {perspective}, and what new primitive should be generated?",
    "How should the {dimension} layer expose inputs, outputs, side effects, acceptance checks, and examples for {perspective}?",
)


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha(value: Any, *, length: int = 16) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:length]


def _slug(value: str, *, limit: int = 80) -> str:
    chars: list[str] = []
    for char in str(value).lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")[:limit] or "item"


def _token_estimate(value: Any) -> int:
    return max(1, len(_stable_json(value)) // CHARS_PER_TOKEN)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_stable_json(row) + "\n")
            count += 1
    return count


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_stable_json(row) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def _policy_for(source_kind: str) -> SourcePolicy:
    return POLICY_BY_KIND.get(source_kind, POLICY_BY_KIND["website"])


def _source_body(row: dict[str, Any]) -> str:
    for key in RAW_STORAGE_FIELDS:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _sanitize_source_row(row: dict[str, Any], *, index: int) -> dict[str, Any]:
    source_kind = str(row.get("source_kind") or row.get("kind") or "website")
    policy = _policy_for(source_kind)
    title = str(row.get("title") or row.get("name") or f"{policy.description} {index}")
    locator = str(row.get("locator") or row.get("url") or policy.default_locator_template.format(index=index))
    summary = str(row.get("summary") or row.get("description") or row.get("why") or policy.description)[:1200]
    tags = row.get("tags") or row.get("seeds") or []
    sanitized = {
        "record_type": "continuous_source_queue_item",
        "source_kind": policy.source_kind,
        "foundry_source_kind": policy.foundry_source_kind,
        "title": title,
        "locator": locator,
        "summary": summary,
        "tags": [str(tag) for tag in tags if str(tag).strip()][:24],
        "source_queue_ref": str(row.get("id") or ""),
        "fetch_hint": str(row.get("fetch") or ""),
        "publisher_class": str(row.get("publisher_class") or policy.publisher_class),
        "license_status": str(row.get("license_status") or policy.license_status),
        "allowed_capture": list(policy.allowed_capture),
        "preferred_connectors": list(policy.preferred_connectors),
        "tos_sensitive": policy.tos_sensitive,
        "robots_required": policy.robots_required,
        "raw_body_default": policy.raw_body_default,
        "source_risk": policy.source_risk,
        "candidate": True,
        "serves_truth": False,
    }
    body = _source_body(row)
    if body:
        sanitized["input_body_digest"] = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
        sanitized["input_body_available_ephemerally"] = True
    return sanitized


def continuous_seed_descriptors(count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    count = count if count > 0 else DEFAULT_SOURCE_LIMIT
    for index in range(1, count + 1):
        template = SOURCE_TEMPLATES[(index - 1) % len(SOURCE_TEMPLATES)]
        policy = _policy_for(str(template["source_kind"]))
        rows.append(
            {
                "source_kind": policy.source_kind,
                "title": f"{template['title']} {index}",
                "locator": policy.default_locator_template.format(index=index),
                "summary": template["summary"],
                "tags": list(template["tags"]) + [f"seed_{index % 17}"],
                "publisher_class": policy.publisher_class,
                "license_status": policy.license_status,
            }
        )
    return rows


def load_source_queue(path: Path | None, *, source_limit: int) -> list[dict[str, Any]]:
    if path:
        rows = _read_jsonl(path)
        if source_limit > 0:
            rows = rows[:source_limit]
    else:
        rows = continuous_seed_descriptors(source_limit)
    return [_sanitize_source_row(row, index=index) for index, row in enumerate(rows, start=1)]


def generate_question_bank(count: int = DEFAULT_QUESTION_COUNT) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    target = max(count, 1)
    ordinal = 1
    while len(questions) < target:
        dimension = QUESTION_DIMENSIONS[(ordinal - 1) % len(QUESTION_DIMENSIONS)]
        perspective = QUESTION_PERSPECTIVES[((ordinal - 1) // len(QUESTION_DIMENSIONS)) % len(QUESTION_PERSPECTIVES)]
        template = QUESTION_TEMPLATES[(ordinal - 1) % len(QUESTION_TEMPLATES)]
        question_id = f"q/{_slug(dimension, limit=32)}/{_slug(perspective, limit=32)}/{ordinal:04d}"
        questions.append(
            {
                "record_type": "primitive_decomposition_question",
                "question_id": question_id,
                "ordinal": ordinal,
                "dimension": dimension,
                "perspective": perspective,
                "prompt": template.format(dimension=dimension.replace("_", " "), perspective=perspective.replace("_", " ")),
                "expected_answer_contract": {
                    "component_families": "list[str]",
                    "primitive_candidates": "list[PrimitiveCandidate]",
                    "variation_axes": "list[str]",
                    "examples": "list[Example]",
                    "proof_obligations": "list[str]",
                    "gaps": "list[str]",
                },
                "candidate": True,
                "serves_truth": False,
            }
        )
        ordinal += 1
    return questions


def _robots_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))


def robots_allows(url: str, *, user_agent: str = USER_AGENT, timeout: int = DEFAULT_HTTP_TIMEOUT) -> tuple[bool, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return True, "not_http"
    rp = urllib.robotparser.RobotFileParser()
    robots = _robots_url(url)
    try:
        req = urllib.request.Request(robots, headers={"User-Agent": user_agent})
        with urllib.request.urlopen(req, timeout=timeout) as response:  # pragma: no cover - network
            raw = response.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return False, f"robots_unavailable:{type(exc).__name__}"
    rp.parse(raw.splitlines())
    return rp.can_fetch(user_agent, url), "robots_allowed" if rp.can_fetch(user_agent, url) else "robots_blocked"


def fetch_url(url: str, *, user_agent: str = USER_AGENT, timeout: int = DEFAULT_HTTP_TIMEOUT) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:  # pragma: no cover - network
            raw = response.read()
            status = getattr(response, "status", 200)
        text = raw.decode("utf-8", errors="replace")
        return {"ok": True, "status": status, "content": text, "error": "", "fetched_at": _utc()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "status": None, "content": "", "error": f"{type(exc).__name__}: {exc}", "fetched_at": _utc()}


def snapshot_source(
    row: dict[str, Any],
    *,
    index: int,
    live: bool,
    allow_tos_sensitive_live: bool,
    store_short_excerpts: bool,
    max_llm_context_chars: int,
    http_timeout: int,
) -> tuple[dict[str, Any], str]:
    source_kind = str(row.get("source_kind") or "website")
    policy = _policy_for(source_kind)
    title = str(row.get("title") or f"{policy.description} {index}")
    locator = str(row.get("locator") or policy.default_locator_template.format(index=index))
    source_id = str(row.get("source_id") or f"src/continuous/{policy.source_kind}/{_slug(title)}-{_sha(locator, length=10)}")
    body = _source_body(row)
    fetch_note = "not_live"
    fetched_content = ""
    fetched_status: int | None = None
    fetch_error = ""
    if live and urllib.parse.urlparse(locator).scheme in {"http", "https"}:
        if policy.tos_sensitive and not allow_tos_sensitive_live:
            fetch_note = "blocked_tos_sensitive_source"
        else:
            allowed = True
            robots_note = "robots_not_required"
            if policy.robots_required:
                allowed, robots_note = robots_allows(locator, timeout=http_timeout)
            if not allowed:
                fetch_note = robots_note
            else:
                fetched = fetch_url(locator, timeout=http_timeout)
                fetched_content = str(fetched.get("content") or "")
                fetched_status = fetched.get("status") if isinstance(fetched.get("status"), int) else None
                fetch_error = str(fetched.get("error") or "")
                fetch_note = "live_fetch_ok" if fetched.get("ok") else "live_fetch_failed"
    ephemeral_context = ""
    content_basis = ""
    if fetched_content:
        ephemeral_context = fetched_content[:max_llm_context_chars]
        content_basis = "live_http_content"
    elif body and (not policy.tos_sensitive or allow_tos_sensitive_live):
        ephemeral_context = body[:max_llm_context_chars]
        content_basis = "input_payload_ephemeral"
    else:
        compact = {
            "title": title,
            "summary": row.get("summary", ""),
            "tags": row.get("tags", []),
            "locator": locator,
            "source_kind": policy.source_kind,
        }
        ephemeral_context = _stable_json(compact)[:max_llm_context_chars]
        content_basis = "metadata_only"
    content_digest_source = fetched_content or body or ephemeral_context
    snapshot = {
        "record_type": "continuous_source_snapshot",
        "snapshot_id": f"snap/{policy.source_kind}/{_slug(title)}-{_sha({'source': source_id, 'basis': content_basis}, length=12)}",
        "source_id": source_id,
        "source_kind": policy.source_kind,
        "foundry_source_kind": policy.foundry_source_kind,
        "title": title,
        "locator": locator,
        "compact_summary": str(row.get("summary") or policy.description)[:1200],
        "tags": [str(tag) for tag in row.get("tags", []) if str(tag).strip()][:24],
        "publisher_class": str(row.get("publisher_class") or policy.publisher_class),
        "license_status": str(row.get("license_status") or policy.license_status),
        "source_policy": {
            "allowed_capture": list(policy.allowed_capture),
            "preferred_connectors": list(policy.preferred_connectors),
            "robots_required": policy.robots_required,
            "tos_sensitive": policy.tos_sensitive,
            "raw_body_default": policy.raw_body_default,
            "source_risk": policy.source_risk,
        },
        "capture": {
            "live_requested": live,
            "live_fetch_status": fetch_note,
            "http_status": fetched_status,
            "http_error": fetch_error[:240],
            "llm_context_basis": content_basis,
            "llm_context_digest": "sha256:" + hashlib.sha256(ephemeral_context.encode("utf-8")).hexdigest(),
            "source_content_digest": "sha256:" + hashlib.sha256(content_digest_source.encode("utf-8")).hexdigest(),
            "raw_body_stored": False,
            "short_excerpt_stored": bool(store_short_excerpts and "short_excerpt_if_allowed" in policy.allowed_capture),
        },
        "candidate": True,
        "serves_truth": False,
    }
    if snapshot["capture"]["short_excerpt_stored"]:
        snapshot["short_excerpt"] = ephemeral_context[:500]
    return snapshot, ephemeral_context


def _profile_component_families(foundry_source_kind: str) -> tuple[str, ...]:
    profile = PROFILE_BY_KIND.get(foundry_source_kind) or PROFILE_BY_KIND["web_page"]
    return tuple(profile.component_families)


def _profile_variation_axes(foundry_source_kind: str) -> tuple[str, ...]:
    profile = PROFILE_BY_KIND.get(foundry_source_kind) or PROFILE_BY_KIND["web_page"]
    return tuple(profile.variation_axes)


def component_families_for_snapshot(snapshot: dict[str, Any], *, max_components: int) -> list[str]:
    families = list(_profile_component_families(str(snapshot.get("foundry_source_kind") or "web_page")))
    searchable = " ".join(
        [
            str(snapshot.get("title", "")),
            str(snapshot.get("compact_summary", "")),
            " ".join(str(tag) for tag in snapshot.get("tags", [])),
        ]
    ).lower()
    scored: list[tuple[int, str]] = []
    for family in families:
        family_terms = family.replace("_", " ").split()
        score = sum(1 for term in family_terms if term in searchable)
        if family in searchable:
            score += 3
        scored.append((score, family))
    selected = [family for score, family in sorted(scored, key=lambda item: (-item[0], item[1])) if score > 0]
    for family in families:
        if family not in selected:
            selected.append(family)
        if len(selected) >= max_components:
            break
    return selected[:max_components]


def deterministic_decomposition(
    snapshot: dict[str, Any],
    questions: list[dict[str, Any]],
    *,
    max_components: int,
) -> dict[str, Any]:
    foundry_kind = str(snapshot.get("foundry_source_kind") or "web_page")
    families = component_families_for_snapshot(snapshot, max_components=max_components)
    axes = list(_profile_variation_axes(foundry_kind))
    components: list[dict[str, Any]] = []
    primitive_refs: list[str] = []
    for ordinal, family in enumerate(families, start=1):
        primitive_id = f"primitive/{foundry_kind}/{_slug(family, limit=48)}"
        primitive_refs.append(primitive_id)
        components.append(
            {
                "component_id": f"llm-cmp/{foundry_kind}/{_slug(family, limit=48)}-{_sha({'source': snapshot['source_id'], 'family': family}, length=10)}",
                "component_family": family,
                "primitive_id": primitive_id,
                "purpose": f"Reusable {family.replace('_', ' ')} component extracted from {snapshot['source_kind']} source.",
                "input_contract": {"shape": "SourceBackedComponent", "required": ["source_ref", "payload"]},
                "output_contract": {"shape": "PrimitiveCandidatePayload", "required": ["candidate", "proof_obligation"]},
                "variation_axes": axes,
                "proof_obligations": [
                    "source reference retained",
                    "raw body excluded from persisted rows",
                    "candidate boundary preserved",
                    "language/runtime variants require executable examples before promotion",
                ],
                "candidate": True,
                "serves_truth": False,
            }
        )
    return {
        "record_type": "source_question_decomposition_candidate",
        "decomposition_id": f"decomp/{snapshot['source_kind']}/{_slug(snapshot['title'])}-{_sha(snapshot['source_id'], length=10)}",
        "source_id": snapshot["source_id"],
        "snapshot_id": snapshot["snapshot_id"],
        "source_kind": snapshot["source_kind"],
        "foundry_source_kind": foundry_kind,
        "mode": "deterministic_offline",
        "question_count": len(questions),
        "question_bank_digest": "sha256:" + hashlib.sha256(_stable_json([q["question_id"] for q in questions]).encode("utf-8")).hexdigest(),
        "component_candidates": components,
        "primitive_refs": primitive_refs,
        "language_variants": ["python", "typescript", "sql"],
        "architecture_variants": ["modular_cli", "service_endpoint", "batch_pipeline", "agent_tool"],
        "design_system_variants": ["headless_contract", "dashboard_component", "notebook_cell"],
        "gaps": [
            "needs live source connector proof before promotion",
            "needs executable examples per target language",
            "needs benchmark receipt showing token/context savings",
        ],
        "candidate": True,
        "serves_truth": False,
    }


def deterministic_question_answers(
    snapshot: dict[str, Any],
    questions: list[dict[str, Any]],
    decomposition: dict[str, Any],
) -> list[dict[str, Any]]:
    families = [component["component_family"] for component in decomposition.get("component_candidates", [])]
    axes = sorted({axis for component in decomposition.get("component_candidates", []) for axis in component.get("variation_axes", [])})
    rows: list[dict[str, Any]] = []
    for question in questions:
        family = families[(int(question["ordinal"]) - 1) % max(len(families), 1)] if families else "source_component"
        rows.append(
            {
                "record_type": "primitive_question_answer_candidate",
                "answer_id": f"ans/{_sha({'source': snapshot['source_id'], 'question': question['question_id']}, length=16)}",
                "source_id": snapshot["source_id"],
                "question_id": question["question_id"],
                "dimension": question["dimension"],
                "perspective": question["perspective"],
                "answer_mode": decomposition["mode"],
                "answer_summary": (
                    f"Map {question['dimension'].replace('_', ' ')} for {question['perspective'].replace('_', ' ')} "
                    f"through {family.replace('_', ' ')} plus source-backed proof checks."
                ),
                "component_families": families[:6],
                "variation_axes": axes[:8],
                "candidate": True,
                "serves_truth": False,
            }
        )
    return rows


def _chunks(values: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    size = max(size, 1)
    for index in range(0, len(values), size):
        yield values[index:index + size]


def _extract_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        value = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def llm_decomposition_batches(
    snapshot: dict[str, Any],
    source_context: str,
    questions: list[dict[str, Any]],
    *,
    provider_name: str,
    model: str,
    batch_size: int,
    max_tokens: int,
    timeout: int,
) -> list[dict[str, Any]]:
    provider = resolve_provider(provider_name)
    system = (
        "You decompose real-world software and knowledge sources into reusable primitive candidates. "
        "Return candidate analysis only. Never claim truth, never store raw source body, and keep every "
        "generated primitive as candidate=true and serves_truth=false."
    )
    rows: list[dict[str, Any]] = []
    for batch_index, batch in enumerate(_chunks(questions, batch_size), start=1):
        compact_questions = [
            {
                "question_id": question["question_id"],
                "dimension": question["dimension"],
                "perspective": question["perspective"],
                "prompt": question["prompt"],
            }
            for question in batch
        ]
        prompt_payload = {
            "source": {
                "source_id": snapshot["source_id"],
                "source_kind": snapshot["source_kind"],
                "foundry_source_kind": snapshot["foundry_source_kind"],
                "title": snapshot["title"],
                "summary": snapshot["compact_summary"],
                "tags": snapshot.get("tags", []),
                "policy": snapshot.get("source_policy", {}),
            },
            "source_context_ephemeral_not_for_storage": source_context[:DEFAULT_MAX_LLM_CONTEXT_CHARS],
            "questions": compact_questions,
            "return_json_contract": {
                "component_candidates": "list of {component_family, purpose, primitive_id, inputs, outputs, proof_obligations}",
                "primitive_graph_edges": "list of {from, to, relation}",
                "examples": "list of {language, outline, acceptance_check}",
                "gaps": "list[str]",
                "candidate": True,
                "serves_truth": False,
            },
        }
        user = json.dumps(prompt_payload, indent=2, sort_keys=True, ensure_ascii=True)
        result = chat(model, system, user, provider, max_tokens=max_tokens, timeout=timeout)
        parsed = _extract_json_object(str(result.get("text") or ""))
        rows.append(
            {
                "record_type": "llm_decomposition_batch_candidate",
                "batch_id": f"llm-batch/{snapshot['source_id'].replace('/', '-')}/{batch_index:03d}",
                "source_id": snapshot["source_id"],
                "snapshot_id": snapshot["snapshot_id"],
                "batch_index": batch_index,
                "question_ids": [question["question_id"] for question in batch],
                "question_count": len(batch),
                "provider": provider_name,
                "model": model,
                "prompt_digest": "sha256:" + hashlib.sha256(user.encode("utf-8")).hexdigest(),
                "response_digest": "sha256:" + hashlib.sha256(str(result.get("text") or "").encode("utf-8")).hexdigest(),
                "parsed_response": parsed,
                "usage": result.get("usage") or {},
                "finish_reason": result.get("finish_reason"),
                "error": result.get("error"),
                "candidate": True,
                "serves_truth": False,
            }
        )
    return rows


def build_primitive_graph(snapshot: dict[str, Any], decomposition: dict[str, Any]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = [
        {"id": snapshot["source_id"], "kind": "source", "label": snapshot["title"]},
        {"id": decomposition["decomposition_id"], "kind": "decomposition", "label": "question decomposition"},
    ]
    edges: list[dict[str, Any]] = [
        {"from": snapshot["source_id"], "to": decomposition["decomposition_id"], "relation": "decomposed_by"},
    ]
    for component in decomposition.get("component_candidates", []):
        nodes.append({"id": component["component_id"], "kind": "component", "label": component["component_family"]})
        nodes.append({"id": component["primitive_id"], "kind": "primitive_candidate", "label": component["component_family"]})
        edges.append({"from": decomposition["decomposition_id"], "to": component["component_id"], "relation": "contains_component"})
        edges.append({"from": component["component_id"], "to": component["primitive_id"], "relation": "maps_to_primitive"})
        for axis in component.get("variation_axes", [])[:6]:
            variation_id = f"variation/{decomposition['foundry_source_kind']}/{_slug(component['component_family'])}/{_slug(axis)}"
            nodes.append({"id": variation_id, "kind": "variation_candidate", "label": axis})
            edges.append({"from": component["primitive_id"], "to": variation_id, "relation": "has_variation_axis"})
        for proof_index, proof in enumerate(component.get("proof_obligations", [])[:4], start=1):
            proof_id = f"proof/{_sha({'component': component['component_id'], 'proof': proof}, length=12)}"
            nodes.append({"id": proof_id, "kind": "proof_obligation", "label": proof})
            edges.append({"from": component["primitive_id"], "to": proof_id, "relation": "requires_proof"})
            if proof_index == 1:
                edges.append({"from": snapshot["source_id"], "to": proof_id, "relation": "source_supports"})
    unique_nodes: dict[str, dict[str, Any]] = {node["id"]: node for node in nodes}
    unique_edges = [dict(item) for item in {(_stable_json(edge)): edge for edge in edges}.values()]
    return {
        "record_type": "primitive_graph_candidate",
        "graph_id": f"graph/{_slug(snapshot['source_kind'])}/{_sha(snapshot['source_id'], length=12)}",
        "source_id": snapshot["source_id"],
        "snapshot_id": snapshot["snapshot_id"],
        "decomposition_id": decomposition["decomposition_id"],
        "nodes": list(unique_nodes.values()),
        "edges": unique_edges,
        "node_count": len(unique_nodes),
        "edge_count": len(unique_edges),
        "candidate": True,
        "serves_truth": False,
    }


def build_examples(snapshot: dict[str, Any], decomposition: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    languages = ["python", "typescript", "sql"]
    for component in decomposition.get("component_candidates", []):
        for language in languages:
            example_id = f"example/{language}/{_sha({'source': snapshot['source_id'], 'component': component['component_id'], 'language': language}, length=14)}"
            rows.append(
                {
                    "record_type": "primitive_example_candidate",
                    "example_id": example_id,
                    "source_id": snapshot["source_id"],
                    "primitive_id": component["primitive_id"],
                    "component_family": component["component_family"],
                    "language": language,
                    "outline": (
                        f"{language} example outline for {component['component_family'].replace('_', ' ')}: "
                        "load a source reference, validate contracts, emit a candidate receipt, and run proof checks."
                    ),
                    "acceptance_checks": [
                        "inputs and outputs explicit",
                        "side effects declared",
                        "candidate receipt persisted",
                        "raw source body excluded",
                    ],
                    "candidate": True,
                    "serves_truth": False,
                }
            )
    return rows


def build_llm_primitive_candidates(
    snapshots: list[dict[str, Any]],
    decompositions: list[dict[str, Any]],
    graphs: list[dict[str, Any]],
    examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_by_id = {snapshot["source_id"]: snapshot for snapshot in snapshots}
    graph_by_source = {graph["source_id"]: graph for graph in graphs}
    examples_by_primitive: dict[str, list[str]] = defaultdict(list)
    for example in examples:
        examples_by_primitive[example["primitive_id"]].append(example["example_id"])
    grouped: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for decomposition in decompositions:
        snapshot = source_by_id.get(decomposition["source_id"], {})
        for component in decomposition.get("component_candidates", []):
            grouped[component["primitive_id"]].append((decomposition, component))
    rows: list[dict[str, Any]] = []
    for primitive_id, group in sorted(grouped.items()):
        first_decomposition, first_component = group[0]
        source_refs = sorted({decomposition["source_id"] for decomposition, _ in group})
        graph_refs = sorted({graph_by_source[source_id]["graph_id"] for source_id in source_refs if source_id in graph_by_source})
        axes = sorted({axis for _, component in group for axis in component.get("variation_axes", [])})
        rows.append(
            {
                "record_type": "llm_primitive_candidate",
                "primitive_id": primitive_id,
                "primitive_group": f"grp:{first_decomposition['foundry_source_kind']}.{first_component['component_family'].replace('_', '-')}@candidate",
                "name": f"{first_decomposition['foundry_source_kind']}.{first_component['component_family']}",
                "purpose": f"LLM-question-bank extracted primitive for {first_component['component_family'].replace('_', ' ')}.",
                "source_kind": first_decomposition["foundry_source_kind"],
                "component_family": first_component["component_family"],
                "input_contract": first_component["input_contract"],
                "output_contract": first_component["output_contract"],
                "mutation_affordances": axes,
                "language_variants": sorted({lang for decomposition, _ in group for lang in decomposition.get("language_variants", [])}),
                "architecture_variants": sorted({arch for decomposition, _ in group for arch in decomposition.get("architecture_variants", [])}),
                "design_system_variants": sorted({design for decomposition, _ in group for design in decomposition.get("design_system_variants", [])}),
                "source_support_count": len(source_refs),
                "source_refs_sample": source_refs[:25],
                "graph_refs_sample": graph_refs[:25],
                "example_refs_sample": sorted(examples_by_primitive.get(primitive_id, []))[:25],
                "proof_obligation": "promotion requires source/license review plus executable examples and benchmark receipt",
                "license_provenance": {
                    "status": "candidate_requires_license_review",
                    "source_policy": "metadata_and_citation_first",
                },
                "trust": "candidate",
                "candidate": True,
                "serves_truth": False,
            }
        )
    return rows


def _foundry_source_rows(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for snapshot in snapshots:
        rows.append(
            {
                "source_kind": snapshot["foundry_source_kind"],
                "source_id": snapshot["source_id"],
                "title": snapshot["title"],
                "locator": snapshot["locator"],
                "summary": snapshot["compact_summary"],
                "tags": snapshot.get("tags", []),
                "publisher_class": snapshot.get("publisher_class", ""),
                "license_status": snapshot.get("license_status", "metadata_and_citation_first"),
            }
        )
    return rows


def build_database_feed(
    *,
    run_id: str,
    foundry_primitives: list[dict[str, Any]],
    llm_primitives: list[dict[str, Any]],
    examples: list[dict[str, Any]],
    graphs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target, payloads in (
        ("primitive_candidates", foundry_primitives),
        ("primitive_candidates", llm_primitives),
        ("primitive_examples", examples),
        ("primitive_graphs", graphs),
    ):
        for payload in payloads:
            identifier = (
                payload.get("primitive_id")
                or payload.get("example_id")
                or payload.get("graph_id")
                or _sha(payload, length=16)
            )
            rows.append(
                {
                    "record_type": "primitive_database_feed_row",
                    "feed_id": f"feed/{target}/{_slug(str(identifier), limit=60)}-{_sha({'run': run_id, 'id': identifier}, length=10)}",
                    "run_id": run_id,
                    "target_registry": target,
                    "operation": "stage_candidate",
                    "payload_id": identifier,
                    "payload_digest": "sha256:" + hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest(),
                    "payload": payload,
                    "promotion_state": "staged_requires_source_license_proof_and_benchmark",
                    "candidate": True,
                    "serves_truth": False,
                }
            )
    return rows


def run_loop(
    *,
    output_dir: Path,
    source_queue_path: Path | None = None,
    source_limit: int = DEFAULT_SOURCE_LIMIT,
    question_count: int = DEFAULT_QUESTION_COUNT,
    live: bool = False,
    allow_tos_sensitive_live: bool = False,
    store_short_excerpts: bool = False,
    use_llm: bool = False,
    provider_name: str = DEFAULT_PROVIDER,
    model: str = "",
    llm_batch_size: int = DEFAULT_LLM_BATCH_SIZE,
    llm_max_tokens: int = 2048,
    llm_timeout: int = 120,
    max_llm_context_chars: int = DEFAULT_MAX_LLM_CONTEXT_CHARS,
    max_components: int = DEFAULT_COMPONENTS_PER_SOURCE,
    max_sources_per_partition: int = DEFAULT_MAX_SOURCES_PER_PARTITION,
    http_timeout: int = DEFAULT_HTTP_TIMEOUT,
) -> dict[str, Any]:
    started = time.time()
    run_id = f"continuous-primitive-scrape-loop-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    run_dir = output_dir / "runs" / run_id
    source_queue = load_source_queue(source_queue_path, source_limit=source_limit)
    question_bank = generate_question_bank(question_count)
    snapshots: list[dict[str, Any]] = []
    context_by_source: dict[str, str] = {}
    for index, row in enumerate(source_queue, start=1):
        snapshot, context = snapshot_source(
            row,
            index=index,
            live=live,
            allow_tos_sensitive_live=allow_tos_sensitive_live,
            store_short_excerpts=store_short_excerpts,
            max_llm_context_chars=max_llm_context_chars,
            http_timeout=http_timeout,
        )
        snapshots.append(snapshot)
        context_by_source[snapshot["source_id"]] = context
    decompositions: list[dict[str, Any]] = []
    question_answers: list[dict[str, Any]] = []
    llm_batches: list[dict[str, Any]] = []
    if use_llm:
        provider_models = PROVIDERS.get(provider_name, {}).get("models", [])
        model = model or (provider_models[0] if provider_models else "")
    for snapshot in snapshots:
        decomposition = deterministic_decomposition(snapshot, question_bank, max_components=max_components)
        if use_llm and model:
            batch_rows = llm_decomposition_batches(
                snapshot,
                context_by_source.get(snapshot["source_id"], ""),
                question_bank,
                provider_name=provider_name,
                model=model,
                batch_size=llm_batch_size,
                max_tokens=llm_max_tokens,
                timeout=llm_timeout,
            )
            llm_batches.extend(batch_rows)
            decomposition["mode"] = "llm_batched_with_deterministic_structure"
            decomposition["llm_batch_count"] = len(batch_rows)
            decomposition["llm_error_count"] = sum(1 for row in batch_rows if row.get("error"))
            decomposition["llm_response_digests"] = [row["response_digest"] for row in batch_rows]
        decompositions.append(decomposition)
        question_answers.extend(deterministic_question_answers(snapshot, question_bank, decomposition))
    foundry_receipt = run_foundry(
        source_rows=_foundry_source_rows(snapshots),
        output_dir=run_dir / "foundry_store",
        max_components=max_components,
        max_sources_per_partition=max_sources_per_partition,
        run_id=run_id,
    )
    graphs = [build_primitive_graph(snapshot, decomposition) for snapshot, decomposition in zip(snapshots, decompositions)]
    examples: list[dict[str, Any]] = []
    for snapshot, decomposition in zip(snapshots, decompositions):
        examples.extend(build_examples(snapshot, decomposition))
    llm_primitives = build_llm_primitive_candidates(snapshots, decompositions, graphs, examples)
    foundry_primitives = _read_jsonl(run_dir / "foundry_store" / "primitive_candidates.jsonl")
    database_feed = build_database_feed(
        run_id=run_id,
        foundry_primitives=foundry_primitives,
        llm_primitives=llm_primitives,
        examples=examples,
        graphs=graphs,
    )
    source_kind_counts = dict(sorted(Counter(snapshot["source_kind"] for snapshot in snapshots).items()))
    foundry_kind_counts = dict(sorted(Counter(snapshot["foundry_source_kind"] for snapshot in snapshots).items()))
    summary = {
        "record_type": RECORD_TYPE,
        "run_id": run_id,
        "created_at": _utc(),
        "seconds": round(time.time() - started, 3),
        "source_queue_items": len(source_queue),
        "source_snapshots": len(snapshots),
        "source_kind_counts": source_kind_counts,
        "foundry_source_kind_counts": foundry_kind_counts,
        "question_count": len(question_bank),
        "question_answer_rows": len(question_answers),
        "llm_enabled": use_llm,
        "llm_provider": provider_name if use_llm else "",
        "llm_model": model if use_llm else "",
        "llm_batch_rows": len(llm_batches),
        "primitive_graphs": len(graphs),
        "primitive_examples": len(examples),
        "llm_primitive_candidates": len(llm_primitives),
        "primitive_database_feed_rows": len(database_feed),
        "foundry_receipt": foundry_receipt,
        "token_proxy": {
            "question_bank_tokens": _token_estimate(question_bank),
            "snapshot_tokens": _token_estimate(snapshots),
            "database_feed_digest_tokens": _token_estimate(
                [{"payload_id": row["payload_id"], "payload_digest": row["payload_digest"]} for row in database_feed]
            ),
            "database_feed_full_tokens": _token_estimate(database_feed),
        },
        "outputs": {
            "run_dir": str(run_dir),
            "source_queue": "source_queue.jsonl",
            "source_snapshots": "source_snapshots.jsonl",
            "llm_question_bank": "llm_question_bank.jsonl",
            "llm_decompositions": "llm_decompositions.jsonl",
            "llm_decomposition_batches": "llm_decomposition_batches.jsonl",
            "question_answers": "question_answers.jsonl",
            "primitive_graphs": "primitive_graphs.jsonl",
            "primitive_examples": "primitive_examples.jsonl",
            "llm_primitive_candidates": "llm_primitive_candidates.jsonl",
            "primitive_database_feed": "primitive_database_feed.jsonl",
            "foundry_store": "foundry_store/",
            "latest_status": str(output_dir / "latest_status.json"),
            "loop_ledger": str(output_dir / "loop_ledger.jsonl"),
        },
        "governance": {
            "raw_body_stored": False,
            "short_excerpt_storage_requested": bool(store_short_excerpts),
            "raw_body_default": False,
            "live_fetch_opt_in": True,
            "tos_sensitive_live_requires_flag": True,
            "generated_rows_are_candidates": True,
            "serves_truth": False,
            "promotion_required": "source/license/proof review plus primitive registry promotion gate",
        },
        "candidate": True,
        "serves_truth": False,
    }
    _write_jsonl(run_dir / "source_queue.jsonl", source_queue)
    _write_jsonl(run_dir / "source_snapshots.jsonl", snapshots)
    _write_jsonl(run_dir / "llm_question_bank.jsonl", question_bank)
    _write_jsonl(run_dir / "llm_decompositions.jsonl", decompositions)
    _write_jsonl(run_dir / "llm_decomposition_batches.jsonl", llm_batches)
    _write_jsonl(run_dir / "question_answers.jsonl", question_answers)
    _write_jsonl(run_dir / "primitive_graphs.jsonl", graphs)
    _write_jsonl(run_dir / "primitive_examples.jsonl", examples)
    _write_jsonl(run_dir / "llm_primitive_candidates.jsonl", llm_primitives)
    _write_jsonl(run_dir / "primitive_database_feed.jsonl", database_feed)
    _write_json(run_dir / "benchmark_receipt.json", summary)
    _write_json(output_dir / "latest_status.json", summary)
    _append_jsonl(output_dir / "loop_ledger.jsonl", summary)
    return summary


def _assert_no_raw_storage(path: Path) -> None:
    for jsonl_path in path.rglob("*.jsonl"):
        for row in _read_jsonl(jsonl_path):
            for key in RAW_STORAGE_FIELDS:
                if key in row:
                    raise AssertionError(f"{jsonl_path}: raw field leaked: {key}")
            if "source_surface_partitions" in jsonl_path.parts:
                continue
            if row.get("candidate") is not True:
                raise AssertionError(f"{jsonl_path}: row must be candidate")
            if row.get("serves_truth") is not False:
                raise AssertionError(f"{jsonl_path}: row must have serves_truth=false")


def _self_test() -> int:
    sample_rows = [
        {
            "source_kind": "kaggle_notebook",
            "title": "Fraud notebook fixture",
            "notebook_source": "RAW NOTEBOOK MUST NOT BE STORED",
            "summary": "Dataset loading, feature engineering, training loop, metric scorer, and submission writer.",
            "tags": ["dataset_loader", "feature_engineering", "training_loop", "metric_scorer"],
        },
        {
            "source_kind": "paper_publication",
            "title": "Benchmark paper fixture",
            "pdf_text": "RAW PDF MUST NOT BE STORED",
            "summary": "Claim extraction, method decomposition, benchmark table, replication protocol, and citation graph.",
            "tags": ["claim_extract", "method_decompose", "benchmark_table", "replication_protocol"],
        },
        {
            "source_kind": "app",
            "title": "Approval workflow fixture",
            "body": "RAW APP NOTES MUST NOT BE STORED",
            "summary": "State model, workflow step, permission gate, notification rule, and export surface.",
            "tags": ["state_model", "workflow_step", "permission_gate", "notification_rule"],
        },
        {
            "source_kind": "google_scholar",
            "title": "Scholar fixture",
            "content": "RAW SEARCH CONTENT MUST NOT BE STORED",
            "summary": "Citation cluster, public abstract handle, related work, benchmarks, and replication leads.",
            "tags": ["citation_graph", "claim_extract", "benchmark_table"],
        },
    ]
    with tempfile.TemporaryDirectory(prefix="continuous-primitive-scrape-loop-test-") as temp:
        source_path = Path(temp) / "sources.jsonl"
        _write_jsonl(source_path, sample_rows)
        out = Path(temp) / "out"
        summary = run_loop(
            output_dir=out,
            source_queue_path=source_path,
            source_limit=0,
            question_count=220,
            live=False,
            use_llm=False,
            max_components=3,
            max_sources_per_partition=3,
        )
        _assert_no_raw_storage(out)
        assert summary["source_snapshots"] == 4
        assert summary["question_count"] >= 200
        assert summary["question_answer_rows"] == summary["source_snapshots"] * summary["question_count"]
        assert summary["primitive_graphs"] == 4
        assert summary["primitive_examples"] >= 12
        assert summary["llm_primitive_candidates"] >= 8
        assert summary["primitive_database_feed_rows"] >= summary["llm_primitive_candidates"]
        assert summary["foundry_receipt"]["primitive_candidates"] >= 8
        assert summary["foundry_receipt"]["source_id_collision_count"] == 0
        latest = json.loads((out / "latest_status.json").read_text(encoding="utf-8"))
        assert latest["run_id"] == summary["run_id"]
        snapshots = _read_jsonl(Path(summary["outputs"]["run_dir"]) / "source_snapshots.jsonl")
        scholar = [row for row in snapshots if row["source_kind"] == "google_scholar"][0]
        assert scholar["capture"]["llm_context_basis"] == "metadata_only"
        assert scholar["capture"]["raw_body_stored"] is False
    print(
        "PASS - continuous_primitive_scrape_loop: governed source queue, 200+ question bank, "
        "candidate decompositions, primitive graphs/examples, database feed, and source_to_primitive_foundry "
        "store all run offline without raw body persistence."
    )
    return 0


def _run_watch(args: argparse.Namespace) -> int:
    tick = 0
    while True:
        tick += 1
        summary = run_loop(
            output_dir=Path(args.out_dir),
            source_queue_path=Path(args.from_jsonl) if args.from_jsonl else None,
            source_limit=args.source_limit,
            question_count=args.question_count,
            live=args.live,
            allow_tos_sensitive_live=args.allow_tos_sensitive_live,
            store_short_excerpts=args.store_short_excerpts,
            use_llm=args.use_llm,
            provider_name=args.provider,
            model=args.model,
            llm_batch_size=args.llm_batch_size,
            llm_max_tokens=args.llm_max_tokens,
            llm_timeout=args.llm_timeout,
            max_llm_context_chars=args.max_llm_context_chars,
            max_components=args.max_components,
            max_sources_per_partition=args.max_sources_per_partition,
            http_timeout=args.http_timeout,
        )
        print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True))
        print(f"written: {Path(args.out_dir)}")
        if args.max_ticks and tick >= args.max_ticks:
            return 0
        time.sleep(args.interval)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Continuously mine sources into primitive database candidate feeds.")
    parser.add_argument("--self-test", action="store_true", help="Run hermetic offline proof.")
    parser.add_argument("--once", action="store_true", help="Run one scrape/decompose/feed pass.")
    parser.add_argument("--watch", action="store_true", help="Run forever or until --max-ticks.")
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between watch ticks.")
    parser.add_argument("--max-ticks", type=int, default=0, help="0 means no watch limit.")
    parser.add_argument("--from-jsonl", default="", help="Optional source queue JSONL. Raw fields are digested and dropped.")
    parser.add_argument("--source-limit", type=int, default=DEFAULT_SOURCE_LIMIT, help="Source rows per tick. For --from-jsonl, 0 means all rows.")
    parser.add_argument("--question-count", type=int, default=DEFAULT_QUESTION_COUNT, help="Questions to ask/store per source.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--live", action="store_true", help="Fetch direct http(s) locators with robots/ToS controls.")
    parser.add_argument("--allow-tos-sensitive-live", action="store_true", help="Allow live fetch of ToS-sensitive sources after operator review.")
    parser.add_argument("--store-short-excerpts", action="store_true", help="Store <=500 char excerpts only when source policy allows it.")
    parser.add_argument("--use-llm", action="store_true", help="Call the shared OpenAI-compatible LLM client in question batches.")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, choices=sorted(PROVIDERS))
    parser.add_argument("--model", default="", help="Defaults to the first configured model for --provider.")
    parser.add_argument("--llm-batch-size", type=int, default=DEFAULT_LLM_BATCH_SIZE)
    parser.add_argument("--llm-max-tokens", type=int, default=2048)
    parser.add_argument("--llm-timeout", type=int, default=120)
    parser.add_argument("--max-llm-context-chars", type=int, default=DEFAULT_MAX_LLM_CONTEXT_CHARS)
    parser.add_argument("--max-components", type=int, default=DEFAULT_COMPONENTS_PER_SOURCE)
    parser.add_argument("--max-sources-per-partition", type=int, default=DEFAULT_MAX_SOURCES_PER_PARTITION)
    parser.add_argument("--http-timeout", type=int, default=DEFAULT_HTTP_TIMEOUT)
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.watch:
        return _run_watch(args)
    if not args.once:
        parser.error("pass --once, --watch, or --self-test")
    summary = run_loop(
        output_dir=Path(args.out_dir),
        source_queue_path=Path(args.from_jsonl) if args.from_jsonl else None,
        source_limit=args.source_limit,
        question_count=args.question_count,
        live=args.live,
        allow_tos_sensitive_live=args.allow_tos_sensitive_live,
        store_short_excerpts=args.store_short_excerpts,
        use_llm=args.use_llm,
        provider_name=args.provider,
        model=args.model,
        llm_batch_size=args.llm_batch_size,
        llm_max_tokens=args.llm_max_tokens,
        llm_timeout=args.llm_timeout,
        max_llm_context_chars=args.max_llm_context_chars,
        max_components=args.max_components,
        max_sources_per_partition=args.max_sources_per_partition,
        http_timeout=args.http_timeout,
    )
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True))
    print(f"written: {Path(args.out_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
