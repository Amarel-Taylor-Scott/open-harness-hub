#!/usr/bin/env python3
"""Live popularity-weighted Kaggle acquisition -> primitive candidates.

This is an acquisition and experiment plane, not a verification plane.  It
collects real competition, dataset, and notebook metadata through the official
Kaggle CLI, ranks sources by observable demand, optionally pulls a bounded set
of public notebook sources into an ephemeral directory, extracts structural
metadata, and writes candidate-only primitive ideas.

Popularity routes scarce review/execution capacity.  It never proves that a
primitive is correct.  Competition-specific labels, predictions, tuned values,
and notebook source bodies are never copied into emitted rows.  Raw notebook
files are deleted with the temporary directory after structural extraction.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import math
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable, Optional


HERE = Path(__file__).resolve()
SBC = next((p for p in HERE.parents if (p / "scripts" / "_repo_paths.py").exists()), HERE.parents[1])
if str(SBC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SBC))

from scripts._repo_paths import resource  # noqa: E402
from scripts.check_generated_artifact_security import screen_prompt_injection  # noqa: E402


BOUNDARY = {"candidate": True, "serves_truth": False}
SCHEMA_VERSION = "kaggle-popularity-primitive-loop/v1"
DEFAULT_OUT = resource("data") / "dev-intel" / "kaggle_popularity_primitive_loop"
MAX_SOURCE_ROWS = 600
MAX_PULL_NOTEBOOKS = 50
MAX_NOTEBOOK_BYTES = 8_000_000
MAX_SYMBOLS = 200
MAX_IMPORTS = 100
MAX_CALLS = 200
SAFE_TEXT_CHARS = 500


def sha(value: str | bytes) -> str:
    raw = value if isinstance(value, bytes) else value.encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_text(value: Any) -> str:
    text = " ".join(str(value or "").replace("\x00", " ").split())
    return text[:SAFE_TEXT_CHARS]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        for row in materialized:
            handle.write(canonical(row) + "\n")
        handle.flush()
        __import__("os").fsync(handle.fileno())
    temp.replace(path)
    return len(materialized)


def run_cli(command: list[str], *, timeout: int = 120) -> str:
    completed = subprocess.run(
        command,
        cwd=SBC,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode:
        error = safe_text(completed.stderr) or f"exit_{completed.returncode}"
        raise RuntimeError(f"Kaggle CLI failed: {error}")
    return completed.stdout


def json_cli(command: list[str], runner: Callable[[list[str]], str] = run_cli) -> list[dict[str, Any]]:
    try:
        value = json.loads(runner(command))
    except (json.JSONDecodeError, RecursionError) as exc:
        raise RuntimeError("Kaggle CLI did not return a JSON array") from exc
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise RuntimeError("Kaggle CLI JSON has the wrong shape")
    return value


def collect_live_metadata(
    *, pages: int = 1, page_size: int = 100,
    runner: Callable[[list[str]], str] = run_cli,
) -> list[dict[str, Any]]:
    pages = max(1, min(10, pages))
    page_size = max(1, min(200, page_size))
    rows: list[dict[str, Any]] = []
    for page in range(1, pages + 1):
        competitions = json_cli(
            ["kaggle", "competitions", "list", "--sort-by", "numberOfTeams", "-p", str(page),
             "--page-size", str(page_size), "--format", "json"], runner
        )
        datasets = json_cli(
            ["kaggle", "datasets", "list", "--sort-by", "votes", "-p", str(page), "--format", "json"],
            runner,
        )
        notebooks = json_cli(
            ["kaggle", "kernels", "list", "--sort-by", "voteCount", "-p", str(page),
             "--page-size", str(page_size), "--format", "json"], runner
        )
        rows.extend(normalize_metadata("competition", row) for row in competitions)
        rows.extend(normalize_metadata("dataset", row) for row in datasets)
        rows.extend(normalize_metadata("notebook", row) for row in notebooks)
        if len(rows) >= MAX_SOURCE_ROWS:
            break
    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows[:MAX_SOURCE_ROWS]:
        deduped[(row["source_kind"], row["source_ref"])] = row
    return sorted(deduped.values(), key=lambda row: (-row["popularity_score"], row["source_kind"], row["source_ref"]))


def normalize_metadata(source_kind: str, raw: dict[str, Any]) -> dict[str, Any]:
    ref = safe_text(raw.get("ref"))
    title = safe_text(raw.get("title") or ref.rsplit("/", 1)[-1].replace("-", " "))
    if screen_prompt_injection(title).get("flagged"):
        title = "[quarantined untrusted title]"
    metrics: dict[str, float] = {}
    if source_kind == "competition":
        metrics["team_count"] = float(raw.get("teamCount") or 0)
    elif source_kind == "dataset":
        metrics["download_count"] = float(raw.get("downloadCount") or 0)
        metrics["vote_count"] = float(raw.get("voteCount") or 0)
        metrics["usability_rating"] = float(raw.get("usabilityRating") or 0)
    else:
        metrics["vote_count"] = float(raw.get("totalVotes") or raw.get("voteCount") or 0)
    score = popularity_score(source_kind, metrics)
    projection = {
        "source_kind": source_kind,
        "source_ref": ref,
        "title": title,
        "author": safe_text(raw.get("author")),
        "category": safe_text(raw.get("category")),
        "deadline": safe_text(raw.get("deadline")),
        "last_updated": safe_text(raw.get("lastUpdated") or raw.get("lastRunTime")),
        "metrics": metrics,
    }
    return {
        "record_type": "kaggle_popularity_source_metadata",
        "schema_version": SCHEMA_VERSION,
        "source_id": sha(canonical(projection)),
        **projection,
        "popularity_score": score,
        "popularity_is_verification": False,
        "license_status": "unknown_requires_join",
        "rules_status": "unknown_requires_join" if source_kind == "competition" else "not_applicable",
        "llm_egress_allowed": False,
        "raw_body_stored": False,
        **BOUNDARY,
    }


def popularity_score(source_kind: str, metrics: dict[str, float]) -> float:
    if source_kind == "competition":
        return round(math.log1p(metrics.get("team_count", 0)) / 12.0, 6)
    if source_kind == "dataset":
        value = (
            math.log1p(metrics.get("download_count", 0))
            + 1.8 * math.log1p(metrics.get("vote_count", 0))
            + 2.0 * metrics.get("usability_rating", 0)
        )
        return round(value / 30.0, 6)
    return round(math.log1p(metrics.get("vote_count", 0)) / 15.0, 6)


def notebook_structure(path: Path) -> dict[str, Any]:
    """Return structure/digests only; never the raw body."""
    if path.stat().st_size > MAX_NOTEBOOK_BYTES:
        return {"parse_status": "too_large", "source_digest": sha(path.read_bytes()), "source_bytes": path.stat().st_size}
    raw = path.read_bytes()
    digest = sha(raw)
    texts: list[str] = []
    try:
        if path.suffix == ".ipynb":
            notebook = json.loads(raw.decode("utf-8"))
            for cell in notebook.get("cells", []) if isinstance(notebook, dict) else []:
                if isinstance(cell, dict) and cell.get("cell_type") == "code":
                    source = cell.get("source") or []
                    texts.append("".join(source) if isinstance(source, list) else str(source))
        elif path.suffix == ".py":
            texts.append(raw.decode("utf-8"))
        else:
            return {"parse_status": "unsupported_extension", "source_digest": digest, "source_bytes": len(raw)}
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return {"parse_status": "decode_error", "source_digest": digest, "source_bytes": len(raw)}
    source = "\n".join(texts)
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError):
        return {"parse_status": "python_parse_error", "source_digest": digest, "source_bytes": len(raw)}
    symbols: list[dict[str, Any]] = []
    imports: set[str] = set()
    calls: Counter[str] = Counter()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and len(symbols) < MAX_SYMBOLS:
            args = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [arg.arg for arg in node.args.args[:20] if re.fullmatch(r"[A-Za-z_]\w*", arg.arg)]
            symbols.append({"kind": type(node).__name__, "name": node.name, "args": args})
        elif isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            name = call_name(node.func)
            if name:
                calls[name] += 1
    return {
        "parse_status": "parsed",
        "source_digest": digest,
        "source_bytes": len(raw),
        "code_cells": len(texts),
        "symbols": symbols[:MAX_SYMBOLS],
        "imports": sorted(imports)[:MAX_IMPORTS],
        "frequent_calls": [{"name": name, "count": count} for name, count in calls.most_common(MAX_CALLS)],
    }


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id if re.fullmatch(r"[A-Za-z_]\w*", node.id) else ""
    if isinstance(node, ast.Attribute):
        parts = []
        current: ast.AST = node
        while isinstance(current, ast.Attribute) and len(parts) < 4:
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        value = ".".join(reversed(parts))
        return value if re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*){0,3}", value) else ""
    return ""


def pull_notebook_structures(
    metadata: list[dict[str, Any]], *, limit: int,
    runner: Callable[[list[str]], str] = run_cli,
) -> list[dict[str, Any]]:
    selected = [row for row in metadata if row["source_kind"] == "notebook"][: max(0, min(MAX_PULL_NOTEBOOKS, limit))]
    receipts: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="aidevobserver-kaggle-") as td:
        root = Path(td)
        for index, row in enumerate(selected):
            dest = root / f"notebook-{index:04d}"
            dest.mkdir()
            try:
                runner(["kaggle", "kernels", "pull", row["source_ref"], "-p", str(dest), "-m"])
                files = sorted(path for path in dest.iterdir() if path.suffix in {".ipynb", ".py"})
                structure = notebook_structure(files[0]) if files else {"parse_status": "no_source_file"}
                status = "captured" if files else "empty"
            except Exception as exc:  # receipt only; error text is classed, never raw provider output
                structure = {"parse_status": "pull_error", "error_class": type(exc).__name__}
                status = "error"
            receipts.append(
                {
                    "record_type": "kaggle_notebook_structure_receipt",
                    "schema_version": SCHEMA_VERSION,
                    "source_id": row["source_id"],
                    "source_ref": row["source_ref"],
                    "status": status,
                    "structure": structure,
                    "raw_body_stored": False,
                    "llm_egress_allowed": False,
                    "license_status": "unknown_requires_join",
                    **BOUNDARY,
                }
            )
    return receipts


GENERIC_FAMILIES: dict[str, tuple[tuple[str, str, str], ...]] = {
    "competition": (
        ("competition_rules_gate", "CompetitionMetadata", "EligibleExperimentPolicy"),
        ("metric_and_submission_contract_inference", "CompetitionMetadata", "EvaluationContract"),
        ("leakage_resistant_holdout_builder", "DatasetProfile", "HiddenHoldoutPlan"),
    ),
    "dataset": (
        ("dataset_license_and_schema_gate", "DatasetMetadata", "EligibleDatasetContract"),
        ("dataset_profile_and_role_inference", "TabularOrModalDataset", "DatasetProfile"),
        ("dataset_quality_and_leakage_probe", "DatasetProfile", "QualityRiskReport"),
    ),
    "notebook": (
        ("notebook_workflow_decomposer", "NotebookStructure", "CapabilityGraphCandidate"),
        ("experiment_step_extractor", "NotebookStructure", "ExperimentRecipeCandidate"),
        ("notebook_near_duplicate_blocker", "NotebookFingerprint", "DeduplicationDecision"),
    ),
}

CALL_CAPABILITIES: tuple[tuple[re.Pattern[str], str, str, str], ...] = (
    (re.compile(r"(?:^|\.)read_(?:csv|parquet|json|excel)$"), "load_tabular_artifact", "DatasetLocator", "TabularDataset"),
    (re.compile(r"(?:^|\.)(?:fillna|dropna|SimpleImputer\.fit_transform)$"), "missing_value_transform", "NullableFeatureMatrix", "ImputedFeatureMatrix"),
    (re.compile(r"(?:^|\.)(?:merge|join|concat)$"), "tabular_relation_join", "TabularRelations", "JoinedTable"),
    (re.compile(r"(?:^|\.)(?:groupby|pivot_table|agg)$"), "group_aggregate_features", "TabularDataset", "AggregateFeatureMatrix"),
    (re.compile(r"(?:^|\.)(?:train_test_split|KFold|StratifiedKFold|GroupKFold|TimeSeriesSplit)$"), "validation_split_builder", "LabeledDataset", "ValidationFolds"),
    (re.compile(r"(?:^|\.)(?:fit|fit_transform)$"), "estimator_fit_step", "TrainingFold", "FittedEstimator"),
    (re.compile(r"(?:^|\.)(?:predict|predict_proba|transform)$"), "estimator_inference_step", "FittedEstimatorAndFeatures", "Predictions"),
    (re.compile(r"(?:^|\.)(?:accuracy_score|roc_auc_score|log_loss|mean_squared_error|mean_absolute_error)$"), "evaluation_metric_step", "PredictionsAndLabels", "MetricScore"),
    (re.compile(r"(?:^|\.)(?:plot|scatter|hist|imshow|lineplot|heatmap)$"), "diagnostic_visualization_step", "AnalysisArtifact", "Visualization"),
    (re.compile(r"(?:^|\.)(?:to_csv|to_parquet|dump|save)$"), "artifact_materialization_step", "ComputedArtifact", "ArtifactLocator"),
)


def primitive_ideas(metadata: list[dict[str, Any]], structures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    structure_by_source = {row["source_id"]: row for row in structures}
    ideas: list[dict[str, Any]] = []
    for source in metadata:
        for family, input_edge, output_edge in GENERIC_FAMILIES[source["source_kind"]]:
            identity = {
                "source_id": source["source_id"], "family": family,
                "input_edge": input_edge, "output_edge": output_edge,
            }
            structure = structure_by_source.get(source["source_id"])
            ideas.append(
                {
                    "record_type": "kaggle_popularity_primitive_idea",
                    "schema_version": SCHEMA_VERSION,
                    "primitive_id": "candidate/kaggle/" + sha(canonical(identity))[7:31],
                    "family": family,
                    "input_edge": input_edge,
                    "output_edge": output_edge,
                    "source_id": source["source_id"],
                    "source_kind": source["source_kind"],
                    "source_ref": source["source_ref"],
                    "source_popularity_score": source["popularity_score"],
                    "source_structure_digest": sha(canonical(structure)) if structure else None,
                    "evidence_level": "structural_metadata_candidate" if structure else "popularity_metadata_candidate",
                    "verification_required": [
                        "license_and_rules_join", "independent_contract_test", "negative_near_miss_test",
                    ],
                    "popularity_is_verification": False,
                    "execution_authorized": False,
                    **BOUNDARY,
                }
            )
        if source["source_kind"] != "notebook" or not structure:
            continue
        structure_value = structure.get("structure") if isinstance(structure.get("structure"), dict) else {}
        if structure_value.get("parse_status") != "parsed":
            continue
        structure_digest = sha(canonical(structure))
        for symbol in structure_value.get("symbols") or []:
            if not isinstance(symbol, dict):
                continue
            symbol_name = str(symbol.get("name") or "")
            if not re.fullmatch(r"[A-Za-z_]\w*", symbol_name):
                continue
            signature = {
                "kind": symbol.get("kind"), "name": symbol_name,
                "args": [str(arg) for arg in symbol.get("args") or []],
            }
            identity = {"source_id": source["source_id"], "symbol": signature}
            ideas.append(
                {
                    "record_type": "kaggle_notebook_symbol_primitive_candidate",
                    "schema_version": SCHEMA_VERSION,
                    "primitive_id": "candidate/kaggle-symbol/" + sha(canonical(identity))[7:31],
                    "family": "notebook_symbol_behavior",
                    "symbol_name": symbol_name,
                    "symbol_kind": signature["kind"],
                    "argument_names": signature["args"],
                    "input_edge": "NotebookSymbolInput",
                    "output_edge": "NotebookSymbolOutput",
                    "source_id": source["source_id"],
                    "source_ref": source["source_ref"],
                    "source_structure_digest": structure_digest,
                    "source_symbol_signature_digest": sha(canonical(signature)),
                    "evidence_level": "ast_structure_candidate",
                    "verification_required": ["license_join", "body_local_only", "fixture_generation", "execution_oracle"],
                    "execution_authorized": False,
                    "popularity_is_verification": False,
                    **BOUNDARY,
                }
            )
        for call in structure_value.get("frequent_calls") or []:
            if not isinstance(call, dict):
                continue
            call_value = str(call.get("name") or "")
            for pattern, family, input_edge, output_edge in CALL_CAPABILITIES:
                if not pattern.search(call_value):
                    continue
                identity = {"source_id": source["source_id"], "call": call_value, "family": family}
                ideas.append(
                    {
                        "record_type": "kaggle_notebook_call_primitive_candidate",
                        "schema_version": SCHEMA_VERSION,
                        "primitive_id": "candidate/kaggle-call/" + sha(canonical(identity))[7:31],
                        "family": family,
                        "observed_call": call_value,
                        "observed_count": int(call.get("count") or 0),
                        "input_edge": input_edge,
                        "output_edge": output_edge,
                        "source_id": source["source_id"],
                        "source_ref": source["source_ref"],
                        "source_structure_digest": structure_digest,
                        "evidence_level": "ast_call_candidate",
                        "verification_required": ["license_join", "type_inference", "fixture_generation", "execution_oracle"],
                        "execution_authorized": False,
                        "popularity_is_verification": False,
                        **BOUNDARY,
                    }
                )
                break
    deduped = {str(row["primitive_id"]): row for row in ideas}
    return [deduped[key] for key in sorted(deduped)]


def run_live(out_dir: Path, *, pages: int, page_size: int, pull_notebooks: int) -> dict[str, Any]:
    metadata = collect_live_metadata(pages=pages, page_size=page_size)
    structures = pull_notebook_structures(metadata, limit=pull_notebooks) if pull_notebooks else []
    ideas = primitive_ideas(metadata, structures)
    write_jsonl(out_dir / "source_metadata.jsonl", metadata)
    write_jsonl(out_dir / "notebook_structure_receipts.jsonl", structures)
    write_jsonl(out_dir / "primitive_ideas.jsonl", ideas)
    result = {
        "record_type": "kaggle_popularity_primitive_loop_receipt",
        "schema_version": SCHEMA_VERSION,
        "source_rows": len(metadata),
        "source_kinds": dict(sorted(Counter(row["source_kind"] for row in metadata).items())),
        "notebooks_pulled": len(structures),
        "notebooks_parsed": sum(row.get("structure", {}).get("parse_status") == "parsed" for row in structures),
        "primitive_ideas": len(ideas),
        "unique_primitive_ideas": len({row["primitive_id"] for row in ideas}),
        "raw_body_rows": 0,
        "llm_calls": 0,
        "popularity_is_verification": False,
        "created_at": utc_now(),
        "module_digest": sha(HERE.read_bytes()),
        **BOUNDARY,
    }
    (out_dir / "latest_receipt.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def self_test() -> int:
    fixtures = {
        "competitions": [{"ref": "https://www.kaggle.com/competitions/unit", "teamCount": 1000}],
        "datasets": [{"ref": "owner/data", "title": "Unit data", "downloadCount": 5000, "voteCount": 300,
                      "usabilityRating": 1.0}],
        "notebooks": [{"ref": "owner/unit-notebook", "title": "Unit notebook", "totalVotes": 250}],
    }
    def fixture_runner(command: list[str]) -> str:
        if command[:3] == ["kaggle", "competitions", "list"]:
            return json.dumps(fixtures["competitions"])
        if command[:3] == ["kaggle", "datasets", "list"]:
            return json.dumps(fixtures["datasets"])
        if command[:3] == ["kaggle", "kernels", "list"]:
            return json.dumps(fixtures["notebooks"])
        raise AssertionError(command)
    metadata = collect_live_metadata(pages=1, page_size=3, runner=fixture_runner)
    ideas = primitive_ideas(metadata, [])
    checks = [
        ("three live-source shapes normalize", len(metadata) == 3),
        ("all rows are candidate-only", all(r["candidate"] and not r["serves_truth"] for r in metadata + ideas)),
        ("popularity never becomes verification", all(not r["popularity_is_verification"] for r in metadata + ideas)),
        ("nine deterministic generic ideas emitted", len(ideas) == 9 and len({r["primitive_id"] for r in ideas}) == 9),
        ("no raw body field emitted", "source_code" not in canonical(metadata + ideas)
         and "notebook_body" not in canonical(metadata + ideas)
         and all(row.get("raw_body_stored") is False for row in metadata)),
    ]
    with tempfile.TemporaryDirectory() as td:
        py = Path(td) / "unit.py"
        py.write_text("import pandas as pd\ndef build_features(frame):\n    return frame.fillna(0)\n", encoding="utf-8")
        structure = notebook_structure(py)
        checks.append(("real AST structure extracts digest, import, symbol, and calls without body",
                       structure["parse_status"] == "parsed" and structure["symbols"][0]["name"] == "build_features"
                       and "pandas" in structure["imports"] and "return frame" not in canonical(structure)))
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    failed = [name for name, ok in checks if not ok]
    if failed:
        print(f"FAIL: {failed}")
        return 1
    print("PASS - live Kaggle metadata/pull loop is popularity-routed, structure-only, candidate-only, and proof-gated.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--live", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--pull-notebooks", type=int, default=0)
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if not 1 <= args.pages <= 10 or not 1 <= args.page_size <= 200:
        parser.error("pages must be 1..10 and page-size must be 1..200")
    if not 0 <= args.pull_notebooks <= MAX_PULL_NOTEBOOKS:
        parser.error(f"pull-notebooks must be 0..{MAX_PULL_NOTEBOOKS}")
    print(json.dumps(run_live(
        args.out_dir, pages=args.pages, page_size=args.page_size, pull_notebooks=args.pull_notebooks,
    ), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
