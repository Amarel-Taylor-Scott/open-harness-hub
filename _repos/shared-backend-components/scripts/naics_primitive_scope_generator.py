#!/usr/bin/env python3
"""Generate candidate-only primitive search scopes from NAICS CSV rows.

The input CSV must have at least:

    level,code,name,notes

Rows are emitted in the same JSONL shape consumed by
``_repos/shared-backend-components/scripts/aidevobserver_context_foundry_loop.py`` as multilingual search
scopes. This script does not fetch the web, copy source bodies, or promote
anything. It creates metadata/search scaffolding so the foundry can search
public sources for each industry code and turn evidence into primitive
opportunities.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import csv
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = _resource("catalog") / "knowledge-packs" / "data" / "aidevobserver-naics-primitive-scopes"
DEFAULT_SCOPE_FILE = DEFAULT_OUT_DIR / "scopes.jsonl"
DEFAULT_SUMMARY_FILE = DEFAULT_OUT_DIR / "summary.md"
DEFAULT_MIN_LEVEL = 2
DEFAULT_MAX_LEVEL = 6

PROVIDERS = (
    "github_code",
    "github_repositories",
    "kaggle",
    "data_portals",
    "documentation_search",
    "rss_news",
    "forum_search",
)

LANGUAGE_QUERY_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "lang": "en",
        "language": "English",
        "templates": (
            "NAICS {code} {name} workflow data schema API compliance software",
            "NAICS {code} {name} open data dataset benchmark Kaggle",
            "{name} SaaS workflow forms dashboard automation import export",
        ),
    },
    {
        "lang": "es",
        "language": "Spanish",
        "templates": (
            "NAICS {code} {name} flujo de trabajo datos esquema API cumplimiento software",
            "NAICS {code} {name} datos abiertos dataset benchmark Kaggle",
        ),
    },
    {
        "lang": "pt",
        "language": "Portuguese",
        "templates": (
            "NAICS {code} {name} fluxo de trabalho dados esquema API conformidade software",
            "NAICS {code} {name} dados abertos dataset benchmark Kaggle",
        ),
    },
    {
        "lang": "fr",
        "language": "French",
        "templates": (
            "NAICS {code} {name} workflow donnees schema API conformite logiciel",
            "NAICS {code} {name} donnees ouvertes dataset benchmark Kaggle",
        ),
    },
    {
        "lang": "de",
        "language": "German",
        "templates": (
            "NAICS {code} {name} workflow daten schema API compliance software",
            "NAICS {code} {name} offene daten dataset benchmark Kaggle",
        ),
    },
    {
        "lang": "zh",
        "language": "Chinese",
        "templates": (
            "NAICS {code} {name} 工作流 数据 schema API 合规 软件",
            "NAICS {code} {name} 开放 数据集 benchmark Kaggle",
        ),
    },
    {
        "lang": "ja",
        "language": "Japanese",
        "templates": (
            "NAICS {code} {name} ワークフロー データ スキーマ API コンプライアンス ソフトウェア",
            "NAICS {code} {name} オープンデータ データセット benchmark Kaggle",
        ),
    },
)

SECTOR_TOPIC_FAMILIES = {
    "11": "naics_agriculture_forestry_fishing_hunting",
    "21": "naics_mining_quarrying_oil_gas",
    "22": "naics_utilities",
    "23": "naics_construction",
    "31": "naics_manufacturing",
    "32": "naics_manufacturing",
    "33": "naics_manufacturing",
    "41": "naics_wholesale_trade",
    "42": "naics_wholesale_trade",
    "44": "naics_retail_trade",
    "45": "naics_retail_trade",
    "48": "naics_transportation_warehousing",
    "49": "naics_transportation_warehousing",
    "51": "naics_information",
    "52": "naics_finance_insurance",
    "53": "naics_real_estate_rental_leasing",
    "54": "naics_professional_scientific_technical_services",
    "55": "naics_management_companies_enterprises",
    "56": "naics_admin_support_waste_remediation",
    "61": "naics_educational_services",
    "62": "naics_healthcare_social_assistance",
    "71": "naics_arts_entertainment_recreation",
    "72": "naics_accommodation_food_services",
    "81": "naics_other_services",
    "91": "naics_public_administration",
    "92": "naics_public_administration",
}

COMMON_OUTPUTS = (
    "industry_source_discovery_query",
    "industry_entity_schema",
    "industry_workflow_template",
    "industry_dataset_loader",
    "industry_compliance_checklist",
    "industry_eval_fixture",
)

SECTOR_OUTPUTS = {
    "naics_finance_insurance": (
        "market_data_ingest_template",
        "portfolio_risk_policy_gate",
        "brokerage_compliance_checklist",
    ),
    "naics_admin_support_waste_remediation": (
        "employment_agency_candidate_intake_template",
        "job_order_matching_schema",
        "temp_staffing_compliance_checklist",
    ),
    "naics_professional_scientific_technical_services": (
        "professional_services_project_intake_template",
        "client_deliverable_quality_gate",
        "consulting_research_workflow_fixture",
    ),
    "naics_healthcare_social_assistance": (
        "patient_intake_schema",
        "clinical_document_extraction_template",
        "healthcare_privacy_gate",
    ),
    "naics_retail_trade": (
        "retail_catalog_ingest_template",
        "return_authorization_policy_gate",
        "store_operations_dashboard_schema",
    ),
    "naics_manufacturing": (
        "quality_inspection_template",
        "production_lot_traceability_schema",
        "supplier_quality_gate",
    ),
}


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: Any, *, n: int = 16) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()[:n]


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO))
    except ValueError:
        return str(resolved)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:90] or "naics"


def _topic_family(code: str) -> str:
    return SECTOR_TOPIC_FAMILIES.get(code[:2], "naics_other_industries")


def _candidate_outputs(topic_family: str) -> list[str]:
    return sorted(set((*COMMON_OUTPUTS, *SECTOR_OUTPUTS.get(topic_family, ()))))


def _read_naics_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"level", "code", "name"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"NAICS CSV is missing required columns: {sorted(missing)}")
        for row in reader:
            code = str(row.get("code") or "").strip()
            name = " ".join(str(row.get("name") or "").split())
            if not code or not name:
                continue
            try:
                level = int(str(row.get("level") or "").strip())
            except ValueError:
                continue
            rows.append({
                "level": level,
                "code": code,
                "name": name,
                "notes": " ".join(str(row.get("notes") or "").split()),
            })
    return rows


def _scope_from_naics(row: dict[str, Any]) -> dict[str, Any]:
    code = str(row["code"])
    name = str(row["name"])
    topic_family = _topic_family(code)
    queries = []
    for language in LANGUAGE_QUERY_TEMPLATES:
        terms = [
            template.format(code=code, name=name)
            for template in language["templates"]
        ]
        queries.append({
            "lang": language["lang"],
            "language": language["language"],
            "terms": terms,
        })
    return {
        "id": f"naics-{code}-{_slug(name)}",
        "surface_id": "surface-naics-industry-taxonomy",
        "title": f"NAICS {code} — {name}",
        "topic_family": topic_family,
        "naics": {
            "level": row["level"],
            "code": code,
            "name": name,
            "notes": row.get("notes") or "",
        },
        "providers": list(PROVIDERS),
        "queries": queries,
        "candidate_outputs": _candidate_outputs(topic_family),
        "source_policy": "metadata_and_official_naics_refs_first_no_private_business_data",
        "raw_source_republish_allowed": False,
        "public_export_allowed": False,
        "serves_truth": False,
    }


def generate_scopes(
    csv_path: Path,
    *,
    min_level: int = DEFAULT_MIN_LEVEL,
    max_level: int = DEFAULT_MAX_LEVEL,
    limit: int = 0,
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in _read_naics_rows(csv_path)
        if min_level <= int(row["level"]) <= max_level
    ]
    rows.sort(key=lambda row: (int(row["level"]), str(row["code"]), str(row["name"])))
    if limit > 0:
        rows = rows[:limit]
    return [_scope_from_naics(row) for row in rows]


def write_outputs(scopes: Iterable[dict[str, Any]], *, scope_file: Path, summary_file: Path) -> dict[str, Any]:
    scope_rows = list(scopes)
    scope_file.parent.mkdir(parents=True, exist_ok=True)
    scope_file.write_text("".join(_canon(row) + "\n" for row in scope_rows), encoding="utf-8")

    family_counts: dict[str, int] = {}
    levels: dict[str, int] = {}
    for row in scope_rows:
        family = str(row.get("topic_family") or "unknown")
        family_counts[family] = family_counts.get(family, 0) + 1
        level = str((row.get("naics") or {}).get("level") or "unknown")
        levels[level] = levels.get(level, 0) + 1

    summary = {
        "record_type": "naics_primitive_scope_generation",
        "scope_rows": len(scope_rows),
        "scope_file": _display_path(scope_file),
        "summary_file": _display_path(summary_file),
        "topic_family_counts": dict(sorted(family_counts.items())),
        "level_counts": dict(sorted(levels.items())),
        "serves_truth": False,
        "digest": f"sha256:{_sha(scope_rows, n=24)}",
    }
    lines = [
        "# NAICS Primitive Search Scopes",
        "",
        "Candidate-only multilingual source-discovery scopes generated from NAICS rows.",
        "",
        f"- Scope rows: {summary['scope_rows']}",
        f"- Serves truth: {str(summary['serves_truth']).lower()}",
        f"- Digest: {summary['digest']}",
        "",
        "## Topic Families",
    ]
    for family, count in summary["topic_family_counts"].items():
        lines.append(f"- `{family}`: {count}")
    lines.append("")
    summary_file.write_text("\n".join(lines), encoding="utf-8")
    return summary


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        csv_path = root / "naics.csv"
        csv_path.write_text(
            "\n".join([
                "level,code,name,notes",
                "2,52,Finance and Insurance,",
                "6,523120,Securities Brokerage,US",
                "6,561310,Employment Placement Agencies and Executive Search Services,",
            ]),
            encoding="utf-8",
        )
        scopes = generate_scopes(csv_path, min_level=2, max_level=6)
        out = root / "scopes.jsonl"
        summary = root / "summary.md"
        report = write_outputs(scopes, scope_file=out, summary_file=summary)
        summary_exists = out.exists() and summary.exists()

    check("generated one scope per NAICS row", len(scopes) == 3, str(len(scopes)))
    check("all generated scopes are candidate-only", all(row.get("serves_truth") is False for row in scopes))
    check("stock trading/brokerage row gets finance outputs", any("market_data_ingest_template" in row.get("candidate_outputs", []) for row in scopes if row["naics"]["code"] == "523120"))
    check("employment agency row gets employment outputs", any("job_order_matching_schema" in row.get("candidate_outputs", []) for row in scopes if row["naics"]["code"] == "561310"))
    check("multilingual queries include zh", any(any(q.get("lang") == "zh" for q in row.get("queries", [])) for row in scopes))
    check("summary written", report.get("scope_rows") == 3 and summary_exists)

    print("\n" + ("PASS - naics primitive scope generator" if not failures else f"{len(failures)} FAILURES: {failures}"))
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate candidate-only AIDevObserver primitive search scopes from NAICS CSV rows.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--csv", default="", help="CSV path with level,code,name,notes columns")
    parser.add_argument("--out", default=str(DEFAULT_SCOPE_FILE))
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY_FILE))
    parser.add_argument("--min-level", type=int, default=DEFAULT_MIN_LEVEL)
    parser.add_argument("--max-level", type=int, default=DEFAULT_MAX_LEVEL)
    parser.add_argument("--limit", type=int, default=0, help="0 means all rows in the selected level range")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.csv:
        parser.error("--csv is required unless --self-test is used")
    scopes = generate_scopes(
        Path(args.csv),
        min_level=args.min_level,
        max_level=args.max_level,
        limit=args.limit,
    )
    report = write_outputs(scopes, scope_file=Path(args.out), summary_file=Path(args.summary))
    print(_canon(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
