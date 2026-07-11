#!/usr/bin/env python3
"""Compare catalog search results across seed-row and database-row sources."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.processors.catalog_search import run


DEFAULT_SEED_ROW_DIR = _resource("dist") / "catalog-manifest-bridge"
DEFAULT_DB_ROW_DIR = _resource("dist") / "catalog-db-export-rows-smoke"
DEFAULT_OUTPUT = _resource("dist") / "catalog-db-export-rows-smoke" / "catalog-row-source-compare.json"
DEFAULT_PROMPTS = [
    "I need a pipeline to grade an ESG supplier disclosure against CSDDD",
    "Find a security incident grading pipeline with CTI and AppSec evidence",
    "I need a reranking processor for hybrid retrieval",
    "Show governance rubrics for context objects and fragile information",
]


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _ids(result: dict[str, Any]) -> list[str]:
    return [str(candidate.get("id")) for candidate in result.get("candidates", []) if candidate.get("id")]


def _jaccard(left: list[str], right: list[str]) -> float:
    a = set(left)
    b = set(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def compare_row_sources(
    *,
    seed_row_dir: Path = DEFAULT_SEED_ROW_DIR,
    db_row_dir: Path = DEFAULT_DB_ROW_DIR,
    prompts: list[str] | None = None,
    top_k: int = 10,
    min_overlap: float = 0.4,
    output: Path | None = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    prompts = prompts or DEFAULT_PROMPTS
    comparisons: list[dict[str, Any]] = []
    failures = 0
    for prompt in prompts:
        seed_result = run(prompt, top_k=top_k, row_dir=seed_row_dir)
        db_result = run(prompt, top_k=top_k, row_dir=db_row_dir)
        seed_ids = _ids(seed_result)
        db_ids = _ids(db_result)
        overlap = _jaccard(seed_ids, db_ids)
        top_match = bool(seed_ids and db_ids and seed_ids[0] == db_ids[0])
        ok = top_match or overlap >= min_overlap
        failures += 0 if ok else 1
        comparisons.append({
            "prompt": prompt,
            "ok": ok,
            "top_match": top_match,
            "overlap": round(overlap, 4),
            "seed_top_ids": seed_ids,
            "db_top_ids": db_ids,
            "seed_stats": seed_result.get("stats", {}),
            "db_stats": db_result.get("stats", {}),
        })
    report = {
        "ok": failures == 0,
        "generated_at": _utc_now(),
        "seed_row_dir": str(seed_row_dir),
        "db_row_dir": str(db_row_dir),
        "top_k": top_k,
        "min_overlap": min_overlap,
        "prompt_count": len(prompts),
        "failure_count": failures,
        "comparisons": comparisons,
        "safety_notes": [
            "This comparison reads row sets only; it does not read live catalog YAML.",
            "Top result may differ when database normalization removes duplicate axis rows.",
            "Use this as a regression gate before switching a product consumer to database rows.",
        ],
    }
    if output:
        _write_json(output, report)
    return report


def _self_test() -> int:
    if not DEFAULT_SEED_ROW_DIR.exists() or not DEFAULT_DB_ROW_DIR.exists():
        print(json.dumps({
            "ok": True,
            "self_test": "catalog_row_source_compare",
            "skipped": "default row directories are not present",
        }, indent=2, sort_keys=True))
        return 0
    with tempfile.TemporaryDirectory(prefix="ohh-row-source-compare-") as tmp:
        report = compare_row_sources(
            seed_row_dir=DEFAULT_SEED_ROW_DIR,
            db_row_dir=DEFAULT_DB_ROW_DIR,
            prompts=DEFAULT_PROMPTS[:1],
            output=Path(tmp) / "compare.json",
        )
        assert report["prompt_count"] == 1
        assert report["comparisons"][0]["seed_stats"]["corpus_source"] == "database_rows"
        assert report["comparisons"][0]["db_stats"]["corpus_source"] == "database_rows"
    print(json.dumps({"ok": True, "self_test": "catalog_row_source_compare"}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare catalog search over seed rows and database rows.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--seed-row-dir", type=Path, default=DEFAULT_SEED_ROW_DIR)
    parser.add_argument("--db-row-dir", type=Path, default=DEFAULT_DB_ROW_DIR)
    parser.add_argument("--prompt", action="append", help="Prompt to compare; repeatable")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--min-overlap", type=float, default=0.4)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    report = compare_row_sources(
        seed_row_dir=args.seed_row_dir,
        db_row_dir=args.db_row_dir,
        prompts=args.prompt or DEFAULT_PROMPTS,
        top_k=args.top_k,
        min_overlap=args.min_overlap,
        output=args.output,
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
