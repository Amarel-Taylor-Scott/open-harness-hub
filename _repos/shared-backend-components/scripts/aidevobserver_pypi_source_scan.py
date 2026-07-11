#!/usr/bin/env python3
"""Metadata-only PyPI source scanner for AIDevObserver primitive acquisition.

This scanner is deliberately conservative:

* It reads PyPI JSON metadata for named packages.
* It never downloads package archives, wheels, or source files.
* It emits source candidates and primitive opportunities with `serves_truth=false`.
* It treats package code, README-derived behavior, and examples as blocked until
  package-level license, attribution, redaction, and proof gates pass.

The goal is to turn common package capabilities into compact reuse-card inputs
for AIDevObserver, for example:

  "agent is writing retry helper" -> PyPI metadata says `tenacity` exists
  -> candidate primitive: pypi.package_metadata_to_reuse_card
  -> later proof can promote an internal wrapper/template, not the package text.

Usage:

  python3 _repos/shared-backend-components/scripts/aidevobserver_pypi_source_scan.py --pypi-package requests --pypi-package tenacity --write
  python3 _repos/shared-backend-components/scripts/aidevobserver_pypi_source_scan.py --seed-common-python --write
  python3 _repos/shared-backend-components/scripts/aidevobserver_pypi_source_scan.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
DEFAULT_OUT_DIR = _resource("data") / "dev-intel" / "aidevobserver_context_foundry"
SOURCE_CANDIDATES_FILE = "source_candidates.jsonl"
PRIMITIVE_DRAFTS_FILE = "primitive_drafts.jsonl"
PYPI_JSON_URL = "https://pypi.org/pypi/{name}/json"
USER_AGENT = "AIDevObserver-PyPI-Source-Scan"

COMMON_PYTHON_PACKAGES = (
    "requests",
    "httpx",
    "aiohttp",
    "tenacity",
    "backoff",
    "beautifulsoup4",
    "lxml",
    "selectolax",
    "scrapy",
    "playwright",
    "selenium",
    "pandas",
    "polars",
    "numpy",
    "pyarrow",
    "duckdb",
    "openpyxl",
    "pandera",
    "great-expectations",
    "pydantic",
    "jsonschema",
    "marshmallow",
    "fastapi",
    "starlette",
    "uvicorn",
    "flask",
    "django",
    "typer",
    "click",
    "pytest",
    "ruff",
    "mypy",
    "sqlalchemy",
    "alembic",
    "psycopg2-binary",
    "pymongo",
    "redis",
    "celery",
    "rq",
    "prefect",
    "dagster",
    "apache-airflow",
    "dbt-core",
    "boto3",
    "kubernetes",
    "pypdf",
    "pdfplumber",
    "python-docx",
    "pillow",
    "opencv-python",
    "scikit-learn",
    "xgboost",
    "lightgbm",
    "plotly",
    "matplotlib",
    "seaborn",
    "openai",
    "anthropic",
    "litellm",
    "langchain",
    "llama-index",
    "chromadb",
    "qdrant-client",
    "structlog",
    "loguru",
    "prometheus-client",
    "opentelemetry-api",
)

CAPABILITY_HINTS = {
    "requests": ("http_client", "api_integration", "retry_candidate"),
    "httpx": ("http_client", "async_http_client", "api_integration"),
    "aiohttp": ("async_http_client", "api_integration"),
    "tenacity": ("retry_backoff", "resilience_helper"),
    "backoff": ("retry_backoff", "resilience_helper"),
    "beautifulsoup4": ("html_parse", "web_scraping"),
    "lxml": ("html_xml_parse", "document_parse"),
    "selectolax": ("html_parse", "web_scraping"),
    "scrapy": ("web_scraping", "crawler_pipeline"),
    "playwright": ("browser_automation", "web_testing", "scraping"),
    "selenium": ("browser_automation", "web_testing"),
    "pandas": ("table_transform", "csv_excel_ingestion", "dataframe"),
    "polars": ("table_transform", "dataframe", "fast_csv_parquet"),
    "numpy": ("array_compute", "numerical_transform"),
    "pyarrow": ("parquet_arrow", "columnar_artifact"),
    "duckdb": ("local_sql", "analytics_engine"),
    "openpyxl": ("excel_ingestion", "spreadsheet"),
    "pandera": ("dataframe_schema_validation", "data_quality"),
    "great-expectations": ("data_quality", "expectation_suite"),
    "pydantic": ("schema_validation", "typed_model"),
    "jsonschema": ("json_schema_validation", "contract_validation"),
    "marshmallow": ("schema_validation", "serialization"),
    "fastapi": ("api_route", "openapi_app"),
    "starlette": ("asgi_app", "api_route"),
    "uvicorn": ("asgi_server", "runtime_server"),
    "flask": ("api_route", "web_app"),
    "django": ("web_app", "orm", "admin_surface"),
    "typer": ("cli_app", "command_surface"),
    "click": ("cli_app", "command_surface"),
    "pytest": ("test_runner", "proof_command"),
    "ruff": ("lint", "code_quality"),
    "mypy": ("type_check", "code_quality"),
    "sqlalchemy": ("db_orm", "query_layer"),
    "alembic": ("db_migration", "schema_versioning"),
    "psycopg2-binary": ("postgres_driver", "database_connector"),
    "pymongo": ("mongodb_driver", "database_connector"),
    "redis": ("cache", "queue_backend"),
    "celery": ("task_queue", "worker_runtime"),
    "rq": ("task_queue", "worker_runtime"),
    "prefect": ("workflow_orchestration", "data_pipeline"),
    "dagster": ("asset_orchestration", "data_pipeline"),
    "apache-airflow": ("workflow_orchestration", "dag_pipeline"),
    "dbt-core": ("sql_transform", "analytics_engineering"),
    "boto3": ("aws_client", "cloud_integration"),
    "kubernetes": ("k8s_client", "cluster_api"),
    "pypdf": ("pdf_parse", "document_extraction"),
    "pdfplumber": ("pdf_table_extract", "document_extraction"),
    "python-docx": ("docx_parse", "document_extraction"),
    "pillow": ("image_processing", "media_transform"),
    "opencv-python": ("computer_vision", "image_video_processing"),
    "scikit-learn": ("machine_learning", "classification_regression"),
    "xgboost": ("gradient_boosting", "tabular_ml"),
    "lightgbm": ("gradient_boosting", "tabular_ml"),
    "plotly": ("charting", "dashboard_visualization"),
    "matplotlib": ("charting", "report_visualization"),
    "seaborn": ("statistical_charting", "report_visualization"),
    "openai": ("llm_api_client", "model_integration"),
    "anthropic": ("llm_api_client", "model_integration"),
    "litellm": ("llm_router", "model_gateway"),
    "langchain": ("agent_framework", "tool_orchestration"),
    "llama-index": ("rag_framework", "indexing"),
    "chromadb": ("vector_store", "retrieval"),
    "qdrant-client": ("vector_store", "retrieval"),
    "structlog": ("structured_logging", "observability"),
    "loguru": ("logging", "observability"),
    "prometheus-client": ("metrics", "observability"),
    "opentelemetry-api": ("tracing", "observability"),
}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(value: str | bytes, *, n: int = 24) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:n]


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-")
    while "--" in out:
        out = out.replace("--", "-")
    return out[:80] or "pypi-package"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _append_unique(path: Path, records: list[dict[str, Any]], *, key: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = {str(row.get(key)) for row in _read_jsonl(path) if row.get(key)}
    added = 0
    with path.open("a", encoding="utf-8") as fh:
        for record in records:
            item_key = str(record.get(key) or "")
            if not item_key or item_key in seen:
                continue
            fh.write(_canon(record) + "\n")
            seen.add(item_key)
            added += 1
    return added


def _fetch_pypi_json(package: str, *, timeout: int) -> dict[str, Any]:
    name = urllib.parse.quote(package.strip())
    req = urllib.request.Request(
        PYPI_JSON_URL.format(name=name),
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("PyPI payload was not a JSON object")
    return payload


def _metadata_summary(payload: dict[str, Any]) -> dict[str, Any]:
    info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
    name = str(info.get("name") or "").strip()
    version = str(info.get("version") or "").strip()
    project_urls = info.get("project_urls") if isinstance(info.get("project_urls"), dict) else {}
    requires_dist = info.get("requires_dist") if isinstance(info.get("requires_dist"), list) else []
    classifiers = info.get("classifiers") if isinstance(info.get("classifiers"), list) else []
    return {
        "name": name,
        "version": version,
        "summary": str(info.get("summary") or "")[:500],
        "license": str(info.get("license") or "")[:200],
        "project_urls": {str(k): str(v) for k, v in project_urls.items()},
        "requires_dist_count": len(requires_dist),
        "requires_dist_sample": [str(item)[:180] for item in requires_dist[:12]],
        "classifiers_sample": [str(item)[:180] for item in classifiers[:16]],
    }


def _source_candidate(summary: dict[str, Any], *, package: str) -> dict[str, Any]:
    package_name = summary.get("name") or package
    digest = _sha(_canon({"name": package_name, "version": summary.get("version"), "summary": summary.get("summary")}))
    hints = CAPABILITY_HINTS.get(str(package_name).lower(), ("python_package", "package_reuse_card"))
    return {
        "record_type": "source_candidate",
        "candidate_id": f"source:pypi-package:{digest}",
        "source_surface_id": "surface-pypi-json-api",
        "source_kind": "pypi_package_metadata_candidate",
        "source_type": "python_package_registry",
        "title": f"PyPI package metadata candidate - {package_name}",
        "url": f"https://pypi.org/project/{package_name}/",
        "package_name": package_name,
        "package_version": summary.get("version"),
        "metadata": summary,
        "capability_hints": list(hints),
        "primitive_opportunities": [
            "python_package_metadata_connector",
            "package_to_reuse_card",
            "requires_dist_contract",
            *[f"package_capability.{hint}" for hint in hints],
        ],
        "license_status": "needs_package_license_review",
        "redaction_status": "metadata_only_not_downloaded",
        "source_status": "pypi_metadata_discovered_not_downloaded",
        "discovery_queries": [f"pypi json api: {package_name}"],
        "tags": ["pypi", "python", "package", *hints],
        "trust": "candidate",
        "readiness": "R1_indexed",
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def _primitive_opportunity(source: dict[str, Any]) -> dict[str, Any]:
    package_name = str(source.get("package_name") or "package")
    source_id = str(source.get("candidate_id") or "")
    slug = f"pypi.{_slug(package_name)}.metadata_to_reuse_card"
    return {
        "record_type": "primitive_opportunity",
        "candidate_stage": "primitive_opportunity",
        "primitive_id": f"prim:candidate:{slug}",
        "slug": slug,
        "source_candidate": source_id,
        "source_surface_id": "surface-pypi-json-api",
        "title": f"{package_name} metadata to reuse-card primitive opportunity",
        "contract": {
            "input": "PyPIPackageMetadata",
            "output": "PackageReuseCard",
        },
        "effects": ["net.read"],
        "memory": "inline",
        "cache": "content_hash",
        "trust": "candidate",
        "readiness": "R1_indexed",
        "source_ref": {
            "kind": "pypi_package_metadata_candidate",
            "candidate_id": source_id,
            "url": source.get("url"),
            "package_name": package_name,
        },
        "source_evidence_status": "needs_source_evidence",
        "promotion_blockers": [
            "package_license_gate",
            "source_code_fetch_review",
            "api_contract_review",
            "wrapper_or_usage_proof",
        ],
        "proof_requirements": [
            "package_license_gate",
            "source_attribution_gate",
            "metadata_contract_review",
            "usage_or_wrapper_proof",
            "observer_reuse_card_benchmark",
        ],
        "remix_tools": ["output_wrapper", "map_sequence"],
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
        "created_at": _utc(),
    }


def derive_records_from_payload(payload: dict[str, Any], *, package: str) -> tuple[dict[str, Any], dict[str, Any]]:
    summary = _metadata_summary(payload)
    if not summary.get("name"):
        summary["name"] = package
    source = _source_candidate(summary, package=package)
    primitive = _primitive_opportunity(source)
    return source, primitive


def scan_packages(packages: list[str], *, timeout: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    sources: list[dict[str, Any]] = []
    primitives: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for package in packages:
        name = package.strip()
        if not name:
            continue
        try:
            payload = _fetch_pypi_json(name, timeout=timeout)
            source, primitive = derive_records_from_payload(payload, package=name)
            sources.append(source)
            primitives.append(primitive)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            errors.append({
                "record_type": "pypi_scan_error",
                "package_name": name,
                "error_type": type(exc).__name__,
                "message": str(exc)[:300],
                "serves_truth": False,
            })
    return sources, primitives, errors


def _fixture_payload() -> dict[str, Any]:
    return {
        "info": {
            "name": "tenacity",
            "version": "9.1.2",
            "summary": "Retry code until it succeeds",
            "license": "Apache 2.0",
            "project_urls": {"Homepage": "https://github.com/jd/tenacity"},
            "requires_dist": ["typing_extensions; python_version < '3.11'"],
            "classifiers": ["Programming Language :: Python :: 3"],
        },
        "releases": {},
    }


def self_test() -> int:
    source, primitive = derive_records_from_payload(_fixture_payload(), package="tenacity")
    assert source["source_surface_id"] == "surface-pypi-json-api"
    assert source["source_kind"] == "pypi_package_metadata_candidate"
    assert source["serves_truth"] is False
    assert source["raw_source_republish_allowed"] is False
    assert "package_capability.retry_backoff" in source["primitive_opportunities"]
    assert primitive["record_type"] == "primitive_opportunity"
    assert primitive["contract"] == {"input": "PyPIPackageMetadata", "output": "PackageReuseCard"}
    assert primitive["source_ref"]["package_name"] == "tenacity"
    assert primitive["serves_truth"] is False
    assert "package_license_gate" in primitive["proof_requirements"]
    print("PASS - aidevobserver PyPI source scan: metadata-only PyPI package -> source candidate + primitive opportunity; no package code download; serves_truth=false.")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pypi-package", action="append", default=[], help="Package name to scan via PyPI JSON API.")
    ap.add_argument("--seed-common-python", action="store_true", help="Scan a curated list of common AI-coding packages.")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for JSONL candidate rows.")
    ap.add_argument("--timeout", type=int, default=20, help="HTTP timeout seconds for PyPI JSON API.")
    ap.add_argument("--write", action="store_true", help="Append candidate rows to source_candidates.jsonl and primitive_drafts.jsonl.")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()

    packages = list(args.pypi_package)
    if args.seed_common_python:
        packages.extend(COMMON_PYTHON_PACKAGES)
    packages = sorted({p.strip() for p in packages if p.strip()})
    if not packages:
        print(json.dumps({"error": "provide --pypi-package or --seed-common-python", "serves_truth": False}))
        return 2

    sources, primitives, errors = scan_packages(packages, timeout=args.timeout)
    result = {
        "record_type": "pypi_source_scan_result",
        "packages_requested": packages,
        "sources": len(sources),
        "primitive_opportunities": len(primitives),
        "errors": errors,
        "serves_truth": False,
    }
    if args.write:
        out_dir = Path(args.out_dir)
        result["source_candidates_added"] = _append_unique(out_dir / SOURCE_CANDIDATES_FILE, sources, key="candidate_id")
        result["primitive_drafts_added"] = _append_unique(out_dir / PRIMITIVE_DRAFTS_FILE, primitives, key="primitive_id")
    else:
        result["source_candidates"] = sources
        result["primitive_opportunities_rows"] = primitives
    print(json.dumps(result, sort_keys=True))
    return 0 if sources or errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
