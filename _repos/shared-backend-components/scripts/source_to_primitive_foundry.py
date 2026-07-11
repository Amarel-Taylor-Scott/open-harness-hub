#!/usr/bin/env python3
"""Source-to-primitive foundry benchmark and candidate store.

This is the first concrete bridge from broad source acquisition to reusable
primitive generation:

source descriptors -> component breakdowns -> rebuild plans -> primitive
candidate groups -> variation candidates -> benchmark receipt.

It is intentionally offline and descriptor-driven by default. Live web,
GitHub, Kaggle, paper, and discussion collectors can feed the same JSONL shape
without changing the decomposition/storage contract. Raw source bodies are not
stored; generated outputs are candidate-only and never serve truth.
"""
from __future__ import annotations

# Substrate-root bootstrap for bare `python3 _repos/.../scripts/<file>.py`.
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
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts.factory.source_surface_partition_planner import plan_source_surface_partitions  # noqa: E402


RECORD_TYPE = "source_to_primitive_foundry"
DEFAULT_OUT_DIR = _resource("data") / "dev-intel" / "source_to_primitive_foundry"
DEFAULT_SOURCE_COUNT = 500
DEFAULT_COMPONENTS_PER_SOURCE = 4
DEFAULT_MAX_SOURCES_PER_PARTITION = 25
DEFAULT_MAX_RECORDS_PER_PARTITION = 250
CHARS_PER_TOKEN = 4
RAW_TEXT_FIELDS = {
    "body",
    "html",
    "markdown",
    "notebook_source",
    "pdf_text",
    "raw",
    "raw_body",
    "raw_text",
    "source",
    "text",
    "transcript",
}


@dataclass(frozen=True)
class SourceProfile:
    source_kind: str
    title: str
    access_methods: tuple[str, ...]
    publisher_classes: tuple[str, ...]
    component_families: tuple[str, ...]
    variation_axes: tuple[str, ...]
    locator_template: str
    summary_template: str


SOURCE_PROFILES: tuple[SourceProfile, ...] = (
    SourceProfile(
        "web_page",
        "Public web page",
        ("official_web_page", "sitemap", "rss"),
        ("public_publisher", "docs_site", "product_site"),
        ("page_fetch", "content_extract", "table_normalize", "citation_capture", "change_detect"),
        ("selector_strategy", "content_format", "freshness_policy", "citation_granularity"),
        "https://example.org/docs/{index}",
        "A public documentation page with setup steps, tables, links, release notes, and examples.",
    ),
    SourceProfile(
        "website",
        "Website or product surface",
        ("site_crawl", "sitemap", "browser_snapshot"),
        ("product_site", "marketing_site", "docs_site"),
        ("navigation_map", "page_template", "form_flow", "content_card", "analytics_event"),
        ("responsive_layout", "auth_state", "content_model", "interaction_mode"),
        "https://example.org/product/{index}",
        "A product website with navigation, forms, cards, pricing copy, docs, and analytics events.",
    ),
    SourceProfile(
        "repo",
        "Software repository",
        ("git_clone", "github_api", "archive_download"),
        ("open_source_repo", "first_party_repo"),
        ("repo_inventory", "api_route", "schema_validator", "job_queue", "test_harness", "ci_workflow"),
        ("language_runtime", "framework", "storage_backend", "test_runner", "deployment_target"),
        "https://github.com/example/project-{index}",
        "A repository with API routes, schemas, background jobs, tests, CI, and deployment manifests.",
    ),
    SourceProfile(
        "kaggle_project",
        "Kaggle project",
        ("kaggle_api", "metadata_snapshot", "notebook_pull"),
        ("competition", "dataset", "kernel"),
        ("dataset_loader", "feature_engineering", "training_loop", "metric_scorer", "submission_writer"),
        ("task_type", "metric", "model_family", "feature_store", "submission_format"),
        "https://www.kaggle.com/code/example/notebook-{index}",
        "A Kaggle notebook with dataset loading, feature engineering, model training, metric scoring, and submission output.",
    ),
    SourceProfile(
        "leetcode_problem",
        "LeetCode or coding-interview problem",
        ("problem_statement", "test_case_snapshot", "solution_discussion"),
        ("coding_problem", "benchmark_task", "discussion"),
        ("problem_parser", "constraints_model", "algorithm_pattern", "edge_case_catalog", "test_case_generator", "solution_template"),
        ("data_structure", "algorithm_family", "complexity_target", "language_runtime", "proof_style"),
        "https://leetcode.com/problems/problem-{index}/",
        "A coding problem with statement, constraints, examples, edge cases, algorithm pattern, tests, and solution templates.",
    ),
    SourceProfile(
        "competitive_problem",
        "Competitive-programming problem",
        ("problem_statement", "judge_samples", "editorial", "accepted_solution"),
        ("contest_problem", "online_judge", "editorial"),
        ("statement_parser", "constraints_model", "algorithm_pattern", "proof_sketch", "stress_tester", "solution_template"),
        ("contest_format", "algorithm_family", "complexity_target", "input_shape", "language_runtime"),
        "https://example-judge.org/problem/{index}",
        "A competitive-programming task with constraints, samples, editorial ideas, proof sketch, stress tests, and solution template.",
    ),
    SourceProfile(
        "paper",
        "Paper or technical report",
        ("doi_metadata", "arxiv_metadata", "pdf_snapshot"),
        ("research_paper", "technical_report", "whitepaper"),
        ("claim_extract", "method_decompose", "benchmark_table", "replication_protocol", "citation_graph"),
        ("domain", "evidence_type", "metric", "replication_depth", "citation_policy"),
        "https://arxiv.org/abs/0000.{index:05d}",
        "A technical paper with claims, method steps, benchmark tables, ablations, limitations, and citations.",
    ),
    SourceProfile(
        "discussion",
        "Discussion thread",
        ("forum_api", "rss", "html_snapshot"),
        ("forum", "issue_tracker", "social_discussion"),
        ("question_cluster", "answer_pattern", "pain_point", "workaround", "consensus_signal"),
        ("moderation_policy", "evidence_strength", "persona", "resolution_state"),
        "https://discuss.example.org/t/{index}",
        "A discussion thread with user questions, answers, pain points, workarounds, and consensus signals.",
    ),
    SourceProfile(
        "app",
        "Application workflow",
        ("browser_snapshot", "openapi_spec", "storybook", "repo_inventory"),
        ("saas_app", "internal_tool", "workflow_app"),
        ("state_model", "workflow_step", "permission_gate", "notification_rule", "export_surface"),
        ("role_policy", "state_backend", "event_model", "integration_target"),
        "app://example/workflow/{index}",
        "An application workflow with states, permissions, notifications, integrations, exports, and error states.",
    ),
)

PROFILE_BY_KIND = {profile.source_kind: profile for profile in SOURCE_PROFILES}

COMPONENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "api_route": ("api", "route", "endpoint", "request", "response"),
    "answer_pattern": ("answer", "reply", "solution", "accepted"),
    "analytics_event": ("analytics", "event", "tracking", "conversion"),
    "algorithm_pattern": ("algorithm", "pattern", "dynamic programming", "graph", "greedy", "backtracking"),
    "benchmark_table": ("benchmark", "score", "table", "metric"),
    "change_detect": ("release", "change", "diff", "updated"),
    "ci_workflow": ("ci", "workflow", "build", "publish"),
    "citation_capture": ("citation", "link", "source", "reference"),
    "citation_graph": ("citation", "reference", "paper", "related work"),
    "claim_extract": ("claim", "finding", "result", "conclusion"),
    "consensus_signal": ("consensus", "agreement", "resolved", "accepted"),
    "content_card": ("card", "tile", "summary", "item"),
    "content_extract": ("extract", "content", "html", "markdown"),
    "dataset_loader": ("dataset", "csv", "parquet", "load"),
    "export_surface": ("export", "download", "csv", "report"),
    "edge_case_catalog": ("edge", "case", "corner", "boundary"),
    "feature_engineering": ("feature", "transform", "encode", "normalize"),
    "form_flow": ("form", "submit", "validation", "field"),
    "job_queue": ("queue", "worker", "retry", "background"),
    "metric_scorer": ("metric", "score", "evaluate", "auc"),
    "method_decompose": ("method", "approach", "algorithm", "procedure"),
    "navigation_map": ("navigation", "menu", "route", "breadcrumb"),
    "notification_rule": ("notification", "email", "alert", "webhook"),
    "page_fetch": ("fetch", "crawl", "sitemap", "page"),
    "page_template": ("template", "layout", "section", "component"),
    "pain_point": ("pain", "friction", "problem", "issue"),
    "permission_gate": ("permission", "role", "auth", "access"),
    "problem_parser": ("problem", "statement", "input", "output"),
    "proof_sketch": ("proof", "invariant", "correctness", "why"),
    "question_cluster": ("question", "ask", "topic", "cluster"),
    "repo_inventory": ("repo", "module", "symbol", "import"),
    "replication_protocol": ("replicate", "protocol", "dataset", "code"),
    "schema_validator": ("schema", "validate", "contract", "json"),
    "solution_template": ("solution", "template", "code", "implementation"),
    "state_model": ("state", "transition", "status", "store"),
    "statement_parser": ("statement", "constraints", "samples", "input"),
    "stress_tester": ("stress", "random", "bruteforce", "checker"),
    "submission_writer": ("submission", "output", "csv", "kaggle"),
    "table_normalize": ("table", "normalize", "columns", "rows"),
    "test_harness": ("test", "fixture", "proof", "assert"),
    "training_loop": ("train", "model", "fit", "epoch"),
    "workflow_step": ("workflow", "step", "stage", "task"),
    "workaround": ("workaround", "hack", "manual", "temporary"),
}

PRIMITIVE_TEMPLATES: dict[str, dict[str, Any]] = {
    "ingest": {
        "effects": ("net.read_optional", "fs.read_optional", "artifact.write"),
        "input_shape": "SourceDescriptor",
        "output_shape": "NormalizedSourceObject",
        "proof": "source handle resolves, raw body excluded, digest stable",
    },
    "decompose": {
        "effects": ("cpu", "artifact.write"),
        "input_shape": "NormalizedSourceObject",
        "output_shape": "ComponentBreakdown",
        "proof": "component ids stable, source refs preserved, no raw private data",
    },
    "compose": {
        "effects": ("cpu", "artifact.write"),
        "input_shape": "ComponentBreakdown[]",
        "output_shape": "RebuildPlan",
        "proof": "all plan steps map to candidate primitives or explicit gaps",
    },
    "verify": {
        "effects": ("cpu", "subprocess_optional", "artifact.write"),
        "input_shape": "RebuildPlan",
        "output_shape": "ProofReceipt",
        "proof": "acceptance checks are executable or marked owner-review-required",
    },
}

FAMILY_STAGE_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("fetch", "loader", "inventory"), "ingest"),
    (("extract", "normalize", "validator", "cluster", "decompose", "table"), "decompose"),
    (("workflow", "route", "queue", "flow", "state", "training", "permission", "notification"), "compose"),
    (("metric", "test", "replication", "benchmark", "submission"), "verify"),
)


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha(value: Any, *, length: int = 16) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:length]


def _slug(value: str, *, limit: int = 64) -> str:
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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def _source_text_digest(row: dict[str, Any]) -> str:
    raw_parts = {key: row.get(key) for key in RAW_TEXT_FIELDS if key in row}
    compact_parts = {
        "title": row.get("title", ""),
        "summary": row.get("summary", ""),
        "description": row.get("description", ""),
        "tags": row.get("tags", []),
    }
    return "sha256:" + hashlib.sha256(_stable_json({"raw": raw_parts, "compact": compact_parts}).encode("utf-8")).hexdigest()


def _compact_source(row: dict[str, Any], *, index: int) -> dict[str, Any]:
    source_kind = str(row.get("source_kind") or row.get("kind") or "web_page")
    profile = PROFILE_BY_KIND.get(source_kind, PROFILE_BY_KIND["web_page"])
    title = str(row.get("title") or f"{profile.title} {index}")
    locator = str(row.get("locator") or row.get("url") or profile.locator_template.format(index=index))
    source_id = str(row.get("source_id") or f"src/{source_kind}/{_slug(title)}-{_sha(locator, length=10)}")
    compact_summary = str(row.get("summary") or row.get("description") or profile.summary_template)
    return {
        "record_type": "source_object_descriptor",
        "source_id": source_id,
        "source_kind": source_kind,
        "title": title,
        "locator": locator,
        "compact_summary": compact_summary[:800],
        "tags": [str(tag) for tag in row.get("tags", []) if str(tag).strip()][:16],
        "access_methods": list(row.get("access_methods") or profile.access_methods),
        "publisher_class": str(row.get("publisher_class") or profile.publisher_classes[0]),
        "license_status": str(row.get("license_status") or "metadata_and_citation_first"),
        "source_text_digest": _source_text_digest(row),
        "raw_body_stored": False,
        "candidate": True,
        "serves_truth": False,
    }


def generate_source_descriptors(count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(1, count + 1):
        profile = SOURCE_PROFILES[(index - 1) % len(SOURCE_PROFILES)]
        family_hint = profile.component_families[(index - 1) % len(profile.component_families)]
        rows.append(
            {
                "source_kind": profile.source_kind,
                "title": f"{profile.title} benchmark object {index}",
                "locator": profile.locator_template.format(index=index),
                "summary": f"{profile.summary_template} Focus area: {family_hint.replace('_', ' ')}.",
                "tags": [profile.source_kind, family_hint],
                "license_status": "metadata_and_citation_first",
            }
        )
    return rows


def _stage_for_family(component_family: str) -> str:
    family = component_family.lower()
    for needles, stage in FAMILY_STAGE_HINTS:
        if any(needle in family for needle in needles):
            return stage
    return "decompose"


def _families_for_source(source: dict[str, Any], *, max_components: int) -> list[str]:
    source_kind = str(source.get("source_kind") or "web_page")
    profile = PROFILE_BY_KIND.get(source_kind, PROFILE_BY_KIND["web_page"])
    searchable = " ".join(
        [
            str(source.get("title", "")),
            str(source.get("compact_summary", "")),
            " ".join(str(tag) for tag in source.get("tags", [])),
        ]
    ).lower()
    scored: list[tuple[int, str]] = []
    for family in profile.component_families:
        keywords = COMPONENT_KEYWORDS.get(family, ())
        score = sum(1 for keyword in keywords if keyword in searchable)
        scored.append((score, family))
    selected = [family for score, family in sorted(scored, key=lambda item: (-item[0], item[1])) if score > 0]
    for family in profile.component_families:
        if family not in selected:
            selected.append(family)
        if len(selected) >= max_components:
            break
    return selected[:max_components]


def _component_from_family(source: dict[str, Any], family: str, *, ordinal: int) -> dict[str, Any]:
    source_kind = str(source.get("source_kind") or "web_page")
    profile = PROFILE_BY_KIND.get(source_kind, PROFILE_BY_KIND["web_page"])
    component_id = f"cmp/{source_kind}/{_slug(family)}-{_sha({'source': source['source_id'], 'family': family}, length=12)}"
    primitive_group = f"grp:{source_kind}.{family.replace('_', '-')}@candidate"
    return {
        "record_type": "component_breakdown",
        "component_id": component_id,
        "source_id": source["source_id"],
        "source_kind": source_kind,
        "component_family": family,
        "stage": _stage_for_family(family),
        "title": f"{family.replace('_', ' ').title()} from {source['title']}",
        "ordinal": ordinal,
        "evidence_refs": [
            {
                "source_id": source["source_id"],
                "locator": source["locator"],
                "source_text_digest": source["source_text_digest"],
                "raw_body_stored": False,
            }
        ],
        "variation_axes": list(profile.variation_axes),
        "candidate_primitive_group": primitive_group,
        "acceptance_checks": [
            "input and output contracts explicit",
            "source reference retained",
            "side effects declared",
            "candidate boundary preserved",
        ],
        "candidate": True,
        "serves_truth": False,
    }


def decompose_sources(sources: list[dict[str, Any]], *, max_components: int) -> list[dict[str, Any]]:
    components: list[dict[str, Any]] = []
    for source in sources:
        for ordinal, family in enumerate(_families_for_source(source, max_components=max_components), start=1):
            components.append(_component_from_family(source, family, ordinal=ordinal))
    return components


def _primitive_template(component_family: str) -> dict[str, Any]:
    stage = _stage_for_family(component_family)
    template = PRIMITIVE_TEMPLATES[stage]
    return {
        "stage": stage,
        "effects": list(template["effects"]),
        "input_contract": {"shape": template["input_shape"], "required": ["source_ref", "payload"]},
        "output_contract": {"shape": template["output_shape"], "required": ["receipt", "candidate_output"]},
        "proof_obligation": template["proof"],
    }


def build_primitive_candidates(components: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for component in components:
        grouped[(component["source_kind"], component["component_family"])].append(component)

    primitive_rows: list[dict[str, Any]] = []
    variation_rows: list[dict[str, Any]] = []
    for (source_kind, family), group in sorted(grouped.items()):
        primitive_id = f"primitive/{source_kind}/{_slug(family)}"
        template = _primitive_template(family)
        axes = sorted({axis for component in group for axis in component.get("variation_axes", [])})
        source_refs = sorted({ref["source_id"] for component in group for ref in component.get("evidence_refs", [])})
        row = {
            "record_type": "primitive_candidate",
            "primitive_id": primitive_id,
            "primitive_group": f"grp:{source_kind}.{family.replace('_', '-')}@candidate",
            "name": f"{source_kind}.{family}",
            "purpose": f"Reusable {family.replace('_', ' ')} primitive for {source_kind} sources.",
            "source_kind": source_kind,
            "component_family": family,
            "stage": template["stage"],
            "input_contract": template["input_contract"],
            "output_contract": template["output_contract"],
            "effects": template["effects"],
            "composition": {
                "can_be_used_in_rebuild_plan": True,
                "route_position": template["stage"],
                "compatible_source_kinds": [source_kind],
            },
            "mutation_affordances": axes,
            "source_support_count": len(group),
            "source_refs_sample": source_refs[:20],
            "license_provenance": {
                "status": "candidate_requires_license_review",
                "source_policy": "metadata_and_citation_first",
            },
            "proof_command": "python3 _repos/shared-backend-components/scripts/source_to_primitive_foundry.py --self-test",
            "proof_obligation": template["proof_obligation"],
            "trust": "candidate",
            "candidate": True,
            "serves_truth": False,
        }
        primitive_rows.append(row)
        for axis in axes:
            variation_rows.append(
                {
                    "record_type": "primitive_variation_candidate",
                    "variation_id": f"variation/{source_kind}/{_slug(family)}/{_slug(axis)}",
                    "primitive_id": primitive_id,
                    "axis": axis,
                    "purpose": f"Adapt {family.replace('_', ' ')} across {axis.replace('_', ' ')}.",
                    "requires_proof": True,
                    "candidate": True,
                    "serves_truth": False,
                }
            )
    return primitive_rows, variation_rows


def build_rebuild_plans(sources: list[dict[str, Any]], components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for component in components:
        by_source[component["source_id"]].append(component)

    plans: list[dict[str, Any]] = []
    for source in sources:
        source_components = sorted(by_source[source["source_id"]], key=lambda row: row["ordinal"])
        primitive_ids = [
            f"primitive/{component['source_kind']}/{_slug(component['component_family'])}"
            for component in source_components
        ]
        stage_counts = Counter(component["stage"] for component in source_components)
        plans.append(
            {
                "record_type": "rebuild_plan_candidate",
                "plan_id": f"plan/{source['source_kind']}/{_slug(source['title'])}-{_sha(source['source_id'], length=10)}",
                "source_id": source["source_id"],
                "source_kind": source["source_kind"],
                "title": f"Rebuild plan for {source['title']}",
                "component_ids": [component["component_id"] for component in source_components],
                "primitive_route": primitive_ids,
                "route_stage_counts": dict(sorted(stage_counts.items())),
                "missing_primitives": [],
                "gap_count": 0,
                "rebuild_steps": [
                    {
                        "step": index,
                        "component_family": component["component_family"],
                        "primitive_id": primitive_id,
                        "stage": component["stage"],
                    }
                    for index, (component, primitive_id) in enumerate(zip(source_components, primitive_ids), start=1)
                ],
                "candidate": True,
                "serves_truth": False,
            }
        )
    return plans


def _source_surfaces_for_partitions(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_kind = Counter(source["source_kind"] for source in sources)
    surfaces: list[dict[str, Any]] = []
    for profile in SOURCE_PROFILES:
        if by_kind.get(profile.source_kind, 0) == 0:
            continue
        surfaces.append(
            {
                "id": f"{profile.source_kind}-source-to-primitive-foundry",
                "title": profile.title,
                "vertical": "ai_development.source_to_primitive",
                "publisher_classes": list(profile.publisher_classes),
                "access_methods": list(profile.access_methods),
                "source_patterns": [profile.locator_template],
                "candidate_primitives": list(profile.component_families),
                "priority_score": by_kind[profile.source_kind],
                "risk_tier": "medium",
                "max_records_per_partition": DEFAULT_MAX_RECORDS_PER_PARTITION,
                "license_posture": "metadata_and_citation_first",
                "trust_tier": "public_or_first_party",
            }
        )
    return surfaces


def _coverage_metrics(
    sources: list[dict[str, Any]],
    components: list[dict[str, Any]],
    primitives: list[dict[str, Any]],
    plans: list[dict[str, Any]],
) -> dict[str, Any]:
    source_kinds = Counter(source["source_kind"] for source in sources)
    component_families = Counter(component["component_family"] for component in components)
    stage_counts = Counter(component["stage"] for component in components)
    plan_lengths = [len(plan["primitive_route"]) for plan in plans]
    full_plan_rate = (
        sum(1 for plan in plans if not plan.get("missing_primitives")) / len(plans)
        if plans
        else 0.0
    )
    compact_tokens = sum(_token_estimate(row) for row in primitives)
    source_digest_tokens = sum(_token_estimate({k: source[k] for k in ("source_id", "source_text_digest")}) for source in sources)
    naive_source_tokens = sum(
        _token_estimate(
            {
                "title": source["title"],
                "summary": source["compact_summary"],
                "locator": source["locator"],
                "digest": source["source_text_digest"],
            }
        )
        for source in sources
    )
    return {
        "source_kind_counts": dict(sorted(source_kinds.items())),
        "component_family_counts": dict(sorted(component_families.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "full_rebuild_plan_rate": round(full_plan_rate, 4),
        "avg_components_per_source": round(len(components) / max(len(sources), 1), 3),
        "avg_primitives_per_rebuild_plan": round(sum(plan_lengths) / max(len(plan_lengths), 1), 3),
        "primitive_candidate_count": len(primitives),
        "token_proxy": {
            "naive_source_descriptor_tokens": naive_source_tokens,
            "source_digest_only_tokens": source_digest_tokens,
            "primitive_store_tokens": compact_tokens,
            "primitive_store_vs_repeated_source_descriptors_ratio": round(
                naive_source_tokens / max(compact_tokens, 1),
                4,
            ),
        },
    }


def run_foundry(
    *,
    source_rows: list[dict[str, Any]],
    output_dir: Path,
    max_components: int = DEFAULT_COMPONENTS_PER_SOURCE,
    max_sources_per_partition: int = DEFAULT_MAX_SOURCES_PER_PARTITION,
    run_id: str | None = None,
) -> dict[str, Any]:
    started = time.time()
    run_id = run_id or f"source-to-primitive-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    sources = [_compact_source(row, index=index) for index, row in enumerate(source_rows, start=1)]
    source_id_counts = Counter(source["source_id"] for source in sources)
    source_id_collision_count = sum(count - 1 for count in source_id_counts.values() if count > 1)
    components = decompose_sources(sources, max_components=max_components)
    primitives, variations = build_primitive_candidates(components)
    plans = build_rebuild_plans(sources, components)
    partition_result = plan_source_surface_partitions(
        _source_surfaces_for_partitions(sources),
        output_dir=output_dir / "source_surface_partitions",
        run_id=run_id,
        max_sources_per_partition=max_sources_per_partition,
        max_records_per_partition=DEFAULT_MAX_RECORDS_PER_PARTITION,
    )
    receipt = {
        "record_type": RECORD_TYPE,
        "run_id": run_id,
        "created_at": _utc(),
        "seconds": round(time.time() - started, 3),
        "source_objects": len(sources),
        "source_id_collision_count": source_id_collision_count,
        "component_breakdowns": len(components),
        "primitive_candidates": len(primitives),
        "variation_candidates": len(variations),
        "rebuild_plans": len(plans),
        "partition_count": partition_result["partition_count"],
        "source_surface_count": partition_result["source_surface_count"],
        "coverage": _coverage_metrics(sources, components, primitives, plans),
        "files": {
            "source_objects": "source_objects.jsonl",
            "component_breakdowns": "component_breakdowns.jsonl",
            "rebuild_plans": "rebuild_plans.jsonl",
            "primitive_candidates": "primitive_candidates.jsonl",
            "primitive_variations": "primitive_variations.jsonl",
            "benchmark_receipt": "benchmark_receipt.json",
            "source_surface_partitions": "source_surface_partitions/",
        },
        "governance": {
            "raw_body_stored": False,
            "generated_rows_are_candidates": True,
            "serves_truth": False,
            "promotion_required": "check_primitive_registry_promotion_gate.py plus source/license/proof review",
        },
        "candidate": True,
        "serves_truth": False,
    }

    _write_jsonl(output_dir / "source_objects.jsonl", sources)
    _write_jsonl(output_dir / "component_breakdowns.jsonl", components)
    _write_jsonl(output_dir / "rebuild_plans.jsonl", plans)
    _write_jsonl(output_dir / "primitive_candidates.jsonl", primitives)
    _write_jsonl(output_dir / "primitive_variations.jsonl", variations)
    _write_json(output_dir / "benchmark_receipt.json", receipt)
    return receipt


def _load_sources(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.from_jsonl:
        rows = _read_jsonl(Path(args.from_jsonl))
        if args.sources:
            return rows[: args.sources]
        return rows
    return generate_source_descriptors(args.sources or DEFAULT_SOURCE_COUNT)


def _assert_no_raw_storage(path: Path) -> None:
    for file_name in ("source_objects.jsonl", "component_breakdowns.jsonl", "rebuild_plans.jsonl", "primitive_candidates.jsonl"):
        for row in _read_jsonl(path / file_name):
            for raw_key in RAW_TEXT_FIELDS:
                if raw_key in row:
                    raise AssertionError(f"{file_name}: raw field leaked: {raw_key}")
            if row.get("serves_truth") is not False:
                raise AssertionError(f"{file_name}: row serves_truth must be false")
            if row.get("candidate") is not True:
                raise AssertionError(f"{file_name}: row must be candidate")


def _self_test() -> int:
    sample = [
        {
            "source_kind": "repo",
            "title": "Webhook receiver repo",
            "url": "https://github.com/example/webhooks",
            "body": "SECRET RAW BODY MUST NOT BE STORED",
            "summary": "API endpoint with schema validation, queue retry, tests, and CI workflow.",
            "tags": ["api_route", "schema_validator", "job_queue"],
        },
        {
            "source_kind": "kaggle_project",
            "title": "Fraud model notebook",
            "notebook_source": "RAW NOTEBOOK MUST NOT BE STORED",
            "summary": "Dataset loader, feature engineering, model training, metric scoring, and submission CSV.",
            "tags": ["training_loop", "metric_scorer"],
        },
        {
            "source_kind": "paper",
            "title": "Benchmark paper",
            "pdf_text": "RAW PDF MUST NOT BE STORED",
            "summary": "Claims, method, benchmark table, replication protocol, and citation graph.",
            "tags": ["benchmark_table", "replication_protocol"],
        },
        {
            "source_kind": "discussion",
            "title": "Issue discussion",
            "transcript": "RAW THREAD MUST NOT BE STORED",
            "summary": "Question cluster with pain point, workaround, answer pattern, and consensus signal.",
            "tags": ["question_cluster", "workaround"],
        },
    ]
    with tempfile.TemporaryDirectory(prefix="source-to-primitive-foundry-test-") as temp:
        out_dir = Path(temp)
        receipt = run_foundry(source_rows=sample, output_dir=out_dir, run_id="self-test", max_components=4, max_sources_per_partition=2)
        _assert_no_raw_storage(out_dir)
        primitives = _read_jsonl(out_dir / "primitive_candidates.jsonl")
        plans = _read_jsonl(out_dir / "rebuild_plans.jsonl")
        variations = _read_jsonl(out_dir / "primitive_variations.jsonl")
        assert receipt["source_objects"] == len(sample)
        assert receipt["source_id_collision_count"] == 0
        assert receipt["component_breakdowns"] >= len(sample) * 3
        assert receipt["primitive_candidates"] >= 8
        assert receipt["variation_candidates"] >= receipt["primitive_candidates"]
        assert receipt["coverage"]["full_rebuild_plan_rate"] == 1.0
        assert receipt["coverage"]["avg_primitives_per_rebuild_plan"] <= 4.0
        assert all(row["source_support_count"] >= 1 for row in primitives)
        assert all(plan["primitive_route"] and not plan["missing_primitives"] for plan in plans)
        assert all(row["candidate"] is True and row["serves_truth"] is False for row in variations)
    print(
        "PASS - source_to_primitive_foundry: mixed source descriptors decompose into components, "
        "rebuild plans, primitive candidates, and variation candidates; raw bodies are excluded; "
        "all generated rows remain candidate-only/serves_truth=false."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark source-to-primitive foundry decomposition and storage.")
    parser.add_argument("--self-test", action="store_true", help="Run hermetic proof.")
    parser.add_argument("--run", action="store_true", help="Run the benchmark/store writer.")
    parser.add_argument("--sources", type=int, default=DEFAULT_SOURCE_COUNT, help="Synthetic descriptor count or limit for --from-jsonl.")
    parser.add_argument("--from-jsonl", default="", help="Optional source descriptor JSONL input.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory.")
    parser.add_argument("--max-components", type=int, default=DEFAULT_COMPONENTS_PER_SOURCE)
    parser.add_argument("--max-sources-per-partition", type=int, default=DEFAULT_MAX_SOURCES_PER_PARTITION)
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if not args.run:
        parser.error("pass --run or --self-test")

    out_dir = Path(args.out_dir)
    receipt = run_foundry(
        source_rows=_load_sources(args),
        output_dir=out_dir,
        max_components=args.max_components,
        max_sources_per_partition=args.max_sources_per_partition,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=True))
    print(f"written: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
