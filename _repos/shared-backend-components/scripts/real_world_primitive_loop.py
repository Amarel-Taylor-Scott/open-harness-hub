#!/usr/bin/env python3
"""Real-world primitive generation loop.

One operator command should be able to:

1. inventory repo files without storing raw contents;
2. add real-world source surfaces such as Kaggle notebooks, LeetCode tasks,
   competitive-programming problems, apps, papers, websites, and discussions;
3. decompose each source into components;
4. build "how would we rebuild this?" plans;
5. emit primitive and variation candidates;
6. record benchmarkable receipts and gaps.

This script is the runnable loop behind `/loop`. It is offline by default and
candidate-only. Live web/GitHub/Kaggle collectors should feed JSONL descriptors
into `source_to_primitive_foundry.py` or this script; generated rows do not serve
truth until promotion gates prove them.
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
from collections import Counter
from typing import Any, Iterable

from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts.source_to_primitive_foundry import (  # noqa: E402
    DEFAULT_COMPONENTS_PER_SOURCE,
    DEFAULT_MAX_SOURCES_PER_PARTITION,
    DEFAULT_OUT_DIR,
    run_foundry,
)


RECORD_TYPE = "real_world_primitive_loop"
DEFAULT_REPO_ROOT = _resource(".")
DEFAULT_FILE_LIMIT = 0
DEFAULT_EXTERNAL_SEED_COUNT = 240
DEFAULT_MAX_FILE_BYTES = 50 * 1024 * 1024
CONSUMPTION_BENCHMARK_DIR = _resource("data") / "dev-intel" / "primitive_consumption_benchmark"
DEFAULT_EXCLUDED_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)
DEFAULT_BINARY_SUFFIXES = frozenset(
    {
        ".7z",
        ".bin",
        ".bmp",
        ".db",
        ".gif",
        ".ico",
        ".jpeg",
        ".jpg",
        ".mp3",
        ".mp4",
        ".o",
        ".pdf",
        ".png",
        ".pyc",
        ".sqlite",
        ".tar",
        ".webp",
        ".zip",
    }
)


SUFFIX_SUMMARIES: dict[str, str] = {
    ".css": "Stylesheet surface: layout, visual tokens, responsive behavior, selectors, and reusable UI patterns.",
    ".html": "HTML surface: page structure, forms, navigation, semantic sections, and embedded interactions.",
    ".ipynb": "Notebook surface: cells, dataset loading, transformations, model/evaluation steps, and outputs.",
    ".js": "JavaScript module: runtime logic, UI behavior, data transforms, imports, and tests.",
    ".json": "JSON artifact: schema-like object, configuration, catalog row, fixture, or machine-readable receipt.",
    ".jsonl": "JSONL stream: append-only candidate rows, receipts, source descriptors, or benchmark events.",
    ".md": "Markdown document: product spec, command, standard, design note, benchmark plan, or source explanation.",
    ".py": "Python source file: functions, classes, CLIs, tests, deterministic processors, and registry tooling.",
    ".sh": "Shell command surface: local workflow, orchestration, setup, validation, or deployment wrapper.",
    ".ts": "TypeScript module: typed frontend/backend logic, contracts, imports, and tests.",
    ".tsx": "TypeScript UI component: component props, state, rendering, interactions, and visual primitives.",
    ".yaml": "YAML component/config manifest: catalog definition, workflow, schema fixture, or policy row.",
    ".yml": "YAML component/config manifest: catalog definition, workflow, schema fixture, or policy row.",
}


REAL_WORLD_SURFACE_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "source_kind": "kaggle_project",
        "title": "Kaggle tabular competition notebook",
        "summary": "Dataset loading, null handling, feature engineering, cross-validation, model training, metric scoring, leakage checks, and submission writing.",
        "tags": ["kaggle", "dataset_loader", "feature_engineering", "training_loop", "metric_scorer", "submission_writer"],
    },
    {
        "source_kind": "kaggle_project",
        "title": "Kaggle computer-vision baseline",
        "summary": "Image dataset manifest, augmentation policy, train/validation split, model loop, metric scorer, error analysis, and submission artifact.",
        "tags": ["kaggle", "dataset_loader", "training_loop", "metric_scorer", "submission_writer"],
    },
    {
        "source_kind": "leetcode_problem",
        "title": "LeetCode dynamic-programming task",
        "summary": "Problem statement, constraints, examples, state definition, recurrence, base cases, edge cases, complexity target, and solution template.",
        "tags": ["leetcode", "constraints_model", "algorithm_pattern", "edge_case_catalog", "test_case_generator", "solution_template"],
    },
    {
        "source_kind": "leetcode_problem",
        "title": "LeetCode graph traversal task",
        "summary": "Graph input parser, visited-state model, traversal strategy, edge cases, correctness proof, tests, and implementation template.",
        "tags": ["leetcode", "problem_parser", "constraints_model", "algorithm_pattern", "edge_case_catalog", "solution_template"],
    },
    {
        "source_kind": "competitive_problem",
        "title": "Competitive-programming combinatorics problem",
        "summary": "Statement parser, constraints, combinatorial invariant, proof sketch, modular arithmetic edge cases, brute-force checker, and optimized solution.",
        "tags": ["competitive", "statement_parser", "constraints_model", "algorithm_pattern", "proof_sketch", "stress_tester"],
    },
    {
        "source_kind": "repo",
        "title": "SWE-bench style repository bugfix",
        "summary": "Repo inventory, failing test, issue reproduction, minimal patch, regression test, dependency boundary, and CI proof.",
        "tags": ["repo", "repo_inventory", "test_harness", "ci_workflow", "schema_validator"],
    },
    {
        "source_kind": "website",
        "title": "SaaS onboarding website",
        "summary": "Navigation, landing sections, signup form, pricing cards, docs links, analytics events, responsive states, and support flows.",
        "tags": ["website", "navigation_map", "page_template", "form_flow", "content_card", "analytics_event"],
    },
    {
        "source_kind": "app",
        "title": "Operations approval workflow app",
        "summary": "Role-gated workflow states, approval steps, notification rules, export surface, audit events, and integration targets.",
        "tags": ["app", "state_model", "workflow_step", "permission_gate", "notification_rule", "export_surface"],
    },
    {
        "source_kind": "paper",
        "title": "ML systems paper",
        "summary": "Claims, method decomposition, benchmark table, ablations, replication protocol, limitations, and citation graph.",
        "tags": ["paper", "claim_extract", "method_decompose", "benchmark_table", "replication_protocol", "citation_graph"],
    },
    {
        "source_kind": "discussion",
        "title": "Developer issue discussion",
        "summary": "Question cluster, pain points, accepted answer pattern, workaround, evidence strength, unresolved gaps, and consensus signal.",
        "tags": ["discussion", "question_cluster", "answer_pattern", "pain_point", "workaround", "consensus_signal"],
    },
    {
        "source_kind": "web_page",
        "title": "API documentation page",
        "summary": "Page fetch, content extraction, endpoint table normalization, citation capture, examples, rate-limit notes, and change detection.",
        "tags": ["web_page", "page_fetch", "content_extract", "table_normalize", "citation_capture", "change_detect"],
    },
)


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_stable_json(row) + "\n")


def _write_json(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_stable_json(row) + "\n")
            count += 1
    return count


def _slug(value: str, *, limit: int = 80) -> str:
    chars: list[str] = []
    for char in str(value).lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")[:limit] or "item"


def _file_digest(path: Path) -> str:
    stat = path.stat()
    payload = {
        "path": str(path),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }
    return "sha256:" + hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def _should_skip(path: Path, repo_root: Path, *, include_generated: bool) -> bool:
    try:
        parts = set(path.relative_to(repo_root).parts)
    except ValueError:
        parts = set(path.parts)
    if parts & DEFAULT_EXCLUDED_DIRS:
        return True
    if not include_generated and ({"dist", "build", "tmp"} & parts):
        return True
    return False


def _file_tags(relative: Path) -> list[str]:
    tags = ["repo_file"]
    suffix = relative.suffix.lower()
    if suffix:
        tags.append(suffix.lstrip("."))
    tags.extend(part for part in relative.parts[:4] if part and part not in {".", "_repos"})
    if "test" in relative.name.lower() or "tests" in relative.parts:
        tags.append("test_harness")
    if "schema" in relative.parts or suffix in {".json", ".jsonl", ".yaml", ".yml"}:
        tags.append("schema_validator")
    if suffix in {".py", ".js", ".ts", ".tsx", ".sh"}:
        tags.append("repo_inventory")
    return sorted(dict.fromkeys(tags))[:16]


def _descriptor_for_file(path: Path, repo_root: Path) -> dict[str, Any] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    if stat.st_size > DEFAULT_MAX_FILE_BYTES:
        size_note = f"Large file metadata only ({stat.st_size} bytes)."
    else:
        size_note = f"File metadata only ({stat.st_size} bytes)."
    relative = path.relative_to(repo_root)
    suffix = relative.suffix.lower()
    relative_id_hash = hashlib.sha256(str(relative).encode("utf-8")).hexdigest()[:12]
    summary = SUFFIX_SUMMARIES.get(
        suffix,
        "Repository artifact: file path, extension, folder context, metadata digest, and reuse opportunities.",
    )
    return {
        "source_kind": "repo",
        "source_id": f"src/repo-file/{_slug(str(relative), limit=80)}-{relative_id_hash}",
        "title": str(relative),
        "locator": f"file://{relative}",
        "summary": f"{summary} {size_note} Raw file contents are intentionally not stored by this loop.",
        "tags": _file_tags(relative),
        "license_status": "first_party_metadata_only",
        "file_digest": _file_digest(path),
    }


def repo_file_descriptors(repo_root: Path, *, file_limit: int, include_generated: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(repo_root.rglob("*")):
        if _should_skip(path, repo_root, include_generated=include_generated):
            if path.is_dir():
                continue
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() in DEFAULT_BINARY_SUFFIXES:
            continue
        row = _descriptor_for_file(path, repo_root)
        if row:
            rows.append(row)
        if file_limit and len(rows) >= file_limit:
            break
    return rows


def real_world_seed_descriptors(count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(1, count + 1):
        template = REAL_WORLD_SURFACE_TEMPLATES[(index - 1) % len(REAL_WORLD_SURFACE_TEMPLATES)]
        source_kind = template["source_kind"]
        title = f"{template['title']} {index}"
        rows.append(
            {
                "source_kind": source_kind,
                "title": title,
                "locator": f"seed://real-world/{source_kind}/{index}",
                "summary": template["summary"],
                "tags": list(template["tags"]) + [f"seed_{index % 13}"],
                "license_status": "curated_synthetic_real_world_seed_needs_live_source",
            }
        )
    return rows


def _source_mix(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("source_kind", "unknown")) for row in rows).items()))


def _read_latest_consumption_aggregate() -> dict[str, Any]:
    if not CONSUMPTION_BENCHMARK_DIR.exists():
        return {}
    aggregates = sorted(CONSUMPTION_BENCHMARK_DIR.glob("*_aggregate.json"))
    if not aggregates:
        return {}
    for path in reversed(aggregates):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            value["_source_path"] = str(path)
            return value
    return {}


def _gap_source_kind(gap: dict[str, Any]) -> str:
    task_id = str(gap.get("task_id", "")).lower()
    domain = str(gap.get("domain", "")).lower()
    if task_id.startswith("lc_") or domain == "algorithm":
        return "leetcode_problem"
    if task_id.startswith("cp_") or domain == "competitive":
        return "competitive_problem"
    if "kaggle" in task_id or domain == "ml":
        return "kaggle_project"
    if domain == "swe" or "repo" in task_id:
        return "repo"
    if domain == "agentic" or task_id in {"webarena_browser", "osworld"}:
        return "app"
    return "web_page"


def _gap_tags(gap: dict[str, Any], *, hard: bool) -> list[str]:
    task_id = str(gap.get("task_id", "unknown"))
    domain = str(gap.get("domain", "unknown"))
    tags = ["benchmark_gap", domain, task_id]
    if hard:
        tags.append("hard_gap_no_solver_route")
    else:
        tags.append("soft_gap_thin_stringability")
    if task_id.startswith("lc_"):
        tags.extend(["leetcode", "algorithm_pattern", "edge_case_catalog", "solution_template"])
    elif task_id.startswith("cp_"):
        tags.extend(["competitive", "constraints_model", "proof_sketch", "stress_tester"])
    elif domain == "ml":
        tags.extend(["kaggle", "dataset_loader", "training_loop", "metric_scorer"])
    elif domain == "swe":
        tags.extend(["repo_inventory", "test_harness", "ci_workflow"])
    elif domain == "agentic":
        tags.extend(["workflow_step", "permission_gate", "state_model"])
    return sorted(dict.fromkeys(tags))[:16]


def benchmark_gap_descriptors() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    aggregate = _read_latest_consumption_aggregate()
    if not aggregate:
        return [], [], {}
    gap_queue: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    hard_gaps = aggregate.get("capability_gaps") or []
    soft_gaps = aggregate.get("thin_coverage_soft_gaps") or []
    for hard, gaps in ((True, hard_gaps), (False, soft_gaps)):
        for gap in gaps:
            if not isinstance(gap, dict):
                continue
            task_id = str(gap.get("task_id") or "unknown")
            source_kind = _gap_source_kind(gap)
            priority = "p0_hard_gap" if hard else "p1_thin_coverage"
            reason = str(gap.get("reason") or ("thin stringable route coverage" if not hard else "no solver route"))
            queue_row = {
                "record_type": "real_world_primitive_gap_queue_item",
                "task_id": task_id,
                "domain": str(gap.get("domain") or "unknown"),
                "priority": priority,
                "recommended_source_kind": source_kind,
                "reason": reason,
                "source": aggregate.get("_source_path", ""),
                "candidate": True,
                "serves_truth": False,
            }
            gap_queue.append(queue_row)
            source_rows.append(
                {
                    "source_kind": source_kind,
                    "title": f"Benchmark gap source target: {task_id}",
                    "locator": f"gap://primitive-consumption/{task_id}",
                    "summary": (
                        f"Registry benchmark gap for {task_id}: {reason}. Mine real-world examples, "
                        "not prose, then generate components, rebuild plans, primitive candidates, "
                        "variation candidates, and executable proof requirements."
                    ),
                    "tags": _gap_tags(gap, hard=hard),
                    "license_status": "gap_target_requires_live_source_before_promotion",
                }
            )
    return gap_queue, source_rows, aggregate


def run_loop(
    *,
    repo_root: Path,
    output_dir: Path,
    file_limit: int = DEFAULT_FILE_LIMIT,
    external_seed_count: int = DEFAULT_EXTERNAL_SEED_COUNT,
    include_generated: bool = False,
    max_components: int = DEFAULT_COMPONENTS_PER_SOURCE,
    max_sources_per_partition: int = DEFAULT_MAX_SOURCES_PER_PARTITION,
) -> dict[str, Any]:
    started = time.time()
    repo_sources = repo_file_descriptors(repo_root, file_limit=file_limit, include_generated=include_generated)
    seed_sources = real_world_seed_descriptors(external_seed_count)
    gap_queue, gap_sources, gap_aggregate = benchmark_gap_descriptors()
    all_sources = repo_sources + seed_sources + gap_sources
    run_id = f"real-world-primitive-loop-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    foundry_out = output_dir / "foundry_store"
    receipt = run_foundry(
        source_rows=all_sources,
        output_dir=foundry_out,
        max_components=max_components,
        max_sources_per_partition=max_sources_per_partition,
        run_id=run_id,
    )
    summary = {
        "record_type": RECORD_TYPE,
        "run_id": run_id,
        "created_at": _utc(),
        "seconds": round(time.time() - started, 3),
        "repo_root": str(repo_root),
        "repo_files_analyzed": len(repo_sources),
        "external_seed_sources": len(seed_sources),
        "benchmark_gap_sources": len(gap_sources),
        "gap_queue_items": len(gap_queue),
        "total_sources": len(all_sources),
        "source_kind_counts": _source_mix(all_sources),
        "repo_file_suffix_counts": dict(
            sorted(Counter(Path(row["title"]).suffix.lower() or "[none]" for row in repo_sources).items())
        ),
        "gap_queue_source": gap_aggregate.get("_source_path", ""),
        "foundry_receipt": receipt,
        "next_live_connectors": [
            "GitHub repository/API metadata descriptors",
            "Kaggle competition/dataset/kernel metadata descriptors",
            "LeetCode/problem-list or coding-benchmark descriptor import",
            "web sitemap/page descriptors",
            "paper metadata/PDF snapshot descriptors",
            "discussion/issue/forum descriptors",
        ],
        "outputs": {
            "latest_status": "latest_status.json",
            "loop_ledger": "loop_ledger.jsonl",
            "gap_queue": "gap_queue.jsonl",
            "foundry_store": "foundry_store/",
        },
        "candidate": True,
        "serves_truth": False,
    }
    _write_json(output_dir / "latest_status.json", summary)
    _write_jsonl(output_dir / "gap_queue.jsonl", gap_queue)
    _append_jsonl(output_dir / "loop_ledger.jsonl", summary)
    return summary


def _self_test() -> int:
    global CONSUMPTION_BENCHMARK_DIR
    original_consumption_benchmark_dir = CONSUMPTION_BENCHMARK_DIR
    with tempfile.TemporaryDirectory(prefix="real-world-primitive-loop-test-") as temp:
        CONSUMPTION_BENCHMARK_DIR = Path(temp) / "missing-consumption-benchmark"
        root = Path(temp) / "repo"
        root.mkdir()
        (root / "app.py").write_text("def handler(event): return {'ok': True}\n", encoding="utf-8")
        (root / "README.md").write_text("# Demo\n\nA small app with API route and tests.\n", encoding="utf-8")
        (root / "tests").mkdir()
        (root / "tests" / "test_app.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
        out = Path(temp) / "out"
        summary = run_loop(
            repo_root=root,
            output_dir=out,
            file_limit=0,
            external_seed_count=12,
            max_components=3,
            max_sources_per_partition=5,
        )
        assert summary["repo_files_analyzed"] == 3
        assert summary["external_seed_sources"] == 12
        assert summary["total_sources"] == 15
        assert summary["source_kind_counts"].get("kaggle_project", 0) >= 1
        assert summary["source_kind_counts"].get("leetcode_problem", 0) >= 1
        assert summary["foundry_receipt"]["primitive_candidates"] >= 10
        assert summary["foundry_receipt"]["source_id_collision_count"] == 0
        assert summary["foundry_receipt"]["coverage"]["full_rebuild_plan_rate"] == 1.0
        assert summary["foundry_receipt"]["coverage"]["avg_primitives_per_rebuild_plan"] <= 3.0
        assert (out / "latest_status.json").exists()
        assert (out / "gap_queue.jsonl").exists()
        assert (out / "foundry_store" / "primitive_candidates.jsonl").exists()
        bench_dir = Path(temp) / "bench"
        bench_dir.mkdir()
        (bench_dir / "2026-07-07_aggregate.json").write_text(
            json.dumps(
                {
                    "capability_gaps": [
                        {"task_id": "lc_matrix", "domain": "algorithm", "reason": "no plausible match surfaced at all"},
                        {"task_id": "cp_game_theory", "domain": "competitive", "reason": "no plausible match surfaced at all"},
                    ],
                    "thin_coverage_soft_gaps": [
                        {"task_id": "swe_repo_bugfix", "domain": "swe", "stringable_edges": 1},
                    ],
                    "candidate": True,
                    "serves_truth": False,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        CONSUMPTION_BENCHMARK_DIR = bench_dir
        gap_summary = run_loop(
            repo_root=root,
            output_dir=Path(temp) / "out-with-gaps",
            file_limit=1,
            external_seed_count=1,
            max_components=2,
            max_sources_per_partition=5,
        )
        assert gap_summary["gap_queue_items"] == 3
        assert gap_summary["benchmark_gap_sources"] == 3
        assert gap_summary["source_kind_counts"].get("leetcode_problem", 0) >= 1
        assert gap_summary["source_kind_counts"].get("competitive_problem", 0) >= 1
        assert (Path(temp) / "out-with-gaps" / "gap_queue.jsonl").read_text(encoding="utf-8").count("\n") == 3
    CONSUMPTION_BENCHMARK_DIR = original_consumption_benchmark_dir
    print(
        "PASS - real_world_primitive_loop: inventories repo files, adds Kaggle/LeetCode/"
        "competitive/app/paper/web/discussion seeds, emits component breakdowns, rebuild plans, "
        "primitive candidates, and receipts; candidate-only/serves_truth=false."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the real-world primitive generation loop.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--once", action="store_true", help="Run one loop pass.")
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR / "real_world_loop"))
    parser.add_argument("--file-limit", type=int, default=DEFAULT_FILE_LIMIT, help="0 means all eligible files.")
    parser.add_argument("--external-seed-count", type=int, default=DEFAULT_EXTERNAL_SEED_COUNT)
    parser.add_argument("--include-generated", action="store_true", help="Include generated dist/build/tmp files.")
    parser.add_argument("--max-components", type=int, default=DEFAULT_COMPONENTS_PER_SOURCE)
    parser.add_argument("--max-sources-per-partition", type=int, default=DEFAULT_MAX_SOURCES_PER_PARTITION)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.once:
        parser.error("pass --once or --self-test")
    summary = run_loop(
        repo_root=Path(args.repo_root).resolve(),
        output_dir=Path(args.out_dir),
        file_limit=args.file_limit,
        external_seed_count=args.external_seed_count,
        include_generated=args.include_generated,
        max_components=args.max_components,
        max_sources_per_partition=args.max_sources_per_partition,
    )
    print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True))
    print(f"written: {Path(args.out_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
