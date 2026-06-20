"""src.teleon.ingest.bulk_registry — bulk-ingest machine-readable capability REGISTRY DUMPS into candidate rows
WITHOUT an LLM. The path from thousands to hundreds of thousands.

Per-item LLM research (the discovery agents) maps WHICH registries exist; this PULLS them at scale: each registry
FORMAT has a deterministic field-mapping adapter, so a 10k-entry dump becomes 10k CapabilityCandidate rows in one
free pass. gap/lift/determinism are HEURISTIC priors (Stage-1 of screen-before-confirm — a deterministic category
keyword classifier + a kind->determinism table); the gap/lift screen and a later Stage-2 confirm refine them. The
rows are written as a discovered-feed JSON that the existing runner ingests + dedups.

Offline-first: ingests a provided dump (the owner exports a registry index). Live registry FETCH is an
off-by-default governed seam (same posture as every other live-fetch here). Pure + deterministic; reads/writes
shared DATA only; Teleon-layer — never imports src.baltor; everything stays a candidate, nothing serves truth.
"""
from __future__ import annotations

import json
from pathlib import Path

#: the registry formats we can map deterministically. Each maps that dump's field names -> a common entry shape.
REGISTRY_FORMATS = ("generic_catalog", "mcp_registry", "airbyte_registry", "npm_pypi_search", "openapi_directory")

#: format -> the source_kind every row from that registry gets (must be in capability_seeder.SOURCE_KINDS).
_FORMAT_SOURCE_KIND = {"generic_catalog": "github_tools_repo", "mcp_registry": "mcp_server",
                       "airbyte_registry": "github_tools_repo", "npm_pypi_search": "github_tools_repo",
                       "openapi_directory": "github_tools_repo"}

#: heuristic determinism prior by inferred kind — refined later by the gap screen + Stage-2 confirm.
_KIND_DETERMINISM = {"library": 1.0, "connector": 0.95, "api": 0.95, "mcp_server": 0.9, "tool": 0.9,
                     "data": 0.95, "workflow": 0.6, "agent": 0.3, "model": 0.35, "unknown": 0.7}

#: deterministic category classifier — ordered (category, keywords); first match wins, else 'other'. The "metadata"
#: layer the corpus needs at bulk scale; never an LLM call.
_CATEGORY_KEYWORDS = (
    ("healthcare", ("fhir", "hl7", "clinical", "patient", "icd", "snomed", "loinc", "dicom", "medical", "drug", "rxnorm")),
    ("financial-data", ("stripe", "payment", "invoice", "ledger", "accounting", "quickbooks", "bank", "sec ", "edgar", "tax")),
    ("market-data", ("stock", "ticker", "crypto", "forex", "market data", "quote", "exchange rate", "trading")),
    ("legal-statute", ("statute", "case law", "court", "legal", "litigation", "contract clause")),
    ("regulation", ("regulation", "compliance", "cfr", "sanction", "ofac", "regulatory", "gdpr")),
    ("federal-register", ("federal register", "rulemaking", "executive order")),
    ("scraping", ("scrape", "crawl", "browser", "playwright", "puppeteer", "spider")),
    ("document", ("pdf", "docx", "spreadsheet", "ocr", "parse document", "word document", "powerpoint")),
    ("database", ("sql", "postgres", "mysql", "mongodb", "redis", "bigquery", "snowflake", "clickhouse", "database")),
    ("devtools", ("github", "gitlab", "ci/cd", "kubernetes", "terraform", "docker", "deploy", "lint")),
    ("cloud-infra", ("aws", "gcp", "azure", "lambda", "s3 bucket", "cloud run", "serverless")),
    ("email", ("email", "smtp", "imap", "mailbox", "gmail", "outlook")),
    ("messaging", ("slack", "discord", "telegram", "sms", "whatsapp", "teams", "chat message")),
    ("geo-weather", ("geocod", "weather", "map", "location", "gis", "satellite", "timezone", "routing")),
    ("scientific-data", ("arxiv", "pubmed", "genom", "protein", "dataset", "scientific", "research paper")),
    ("identity-compliance", ("kyc", "aml", "whois", "verification", "identity", "address validation", "sanctions")),
    ("media", ("image", "video", "audio", "transcription", "speech", "tts", "text-to-image")),
    ("scraping", ("extract data", "data extraction")),
    ("code", ("code", "repository", "ast", "parse code", "linter", "sdk")),
    ("research", ("search", "research", "retrieval", "rag", "knowledge")),
    ("productivity", ("calendar", "notion", "task", "crm", "spreadsheet", "schedule")),
    ("data-extraction", ("connector", "etl", "ingest", "tap", "extract", "replicate")),
)


def _infer_category(text: str) -> str:
    t = (text or "").lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(k in t for k in keywords):
            return category
    return "other"


def _slug(name: str) -> str:
    out = "".join(c if c.isalnum() else "-" for c in (name or "").lower()).strip("-")
    while "--" in out:
        out = out.replace("--", "-")
    return out or "capability"


def _common_entry(raw: dict, fmt: str) -> dict:
    """Pull a common (name, description, url, kind, license) from a format-specific dump entry — deterministic."""
    g = lambda *keys: next((raw[k] for k in keys if isinstance(raw, dict) and raw.get(k)), "")
    if fmt == "mcp_registry":
        return {"name": g("name", "qualifiedName", "id"), "description": g("description", "summary"),
                "url": g("repository", "homepage", "url", "sourceUrl"), "kind": "mcp_server", "license": g("license")}
    if fmt == "airbyte_registry":
        return {"name": g("name", "name_oss", "connectorName"), "description": g("description", "documentationUrl"),
                "url": g("documentationUrl", "githubUrl", "url"), "kind": "connector", "license": g("license", "license_type")}
    if fmt == "npm_pypi_search":
        return {"name": g("name", "package"), "description": g("description", "summary"),
                "url": g("repository", "homepage", "package_url", "url"), "kind": "library", "license": g("license")}
    if fmt == "openapi_directory":
        return {"name": g("name", "title", "api"), "description": g("description", "info"),
                "url": g("url", "swaggerUrl", "openapiUrl"), "kind": "api", "license": g("license")}
    # generic_catalog
    return {"name": g("name", "title", "id"), "description": g("description", "summary", "desc"),
            "url": g("url", "repository", "homepage", "link"), "kind": g("kind", "type") or "unknown",
            "license": g("license", "spdx")}


def map_entry(raw: dict, fmt: str) -> dict | None:
    """Map ONE registry entry to a CapabilityCandidate-shaped row (no LLM). None if it has no usable name."""
    e = _common_entry(raw, fmt)
    if not e["name"]:
        return None
    desc = str(e["description"]) or f"{e['name']} capability"
    kind = (e["kind"] or "unknown").lower()
    determinism = _KIND_DETERMINISM.get(kind, _KIND_DETERMINISM["unknown"])
    category = _infer_category(f"{e['name']} {desc}")
    return {
        "capability_slot": _slug(e["name"]),
        "intent": " ".join(str(desc).split())[:160] or f"use {e['name']}",
        "input_contract": "structured request", "output_contract": "structured result",
        "category": category, "source_kind": _FORMAT_SOURCE_KIND.get(fmt, "github_tools_repo"),
        "source_name": str(e["name"]), "source_url": str(e["url"]), "license": str(e["license"]) or "unknown",
        "gap_hypothesis": (f"a bare model cannot run this {kind} or access its source live, and would guess "
                           "instead of returning the real, current result"),
        "lift_hypothesis": f"adds the real {kind} call/operation for '{e['name']}' that the model lacks",
        "determinism_ceiling": determinism,
        "deterministic_coverage_estimate": round(max(0.3, determinism - 0.05), 4),
        "verify_note": "BULK-INGESTED (heuristic category/determinism from registry metadata) — confirm before promotion",
    }


def ingest_dump(dump, *, registry_format: str) -> list[dict]:
    """Map a whole registry dump (a list of entries, or a dict with an entries/connectors/servers/data list) into
    candidate rows. Deterministic; no LLM; scales to however many entries the dump holds."""
    if registry_format not in REGISTRY_FORMATS:
        raise ValueError(f"unknown registry_format {registry_format!r}; known: {REGISTRY_FORMATS}")
    if isinstance(dump, dict):
        entries = next((dump[k] for k in ("entries", "connectors", "servers", "data", "results", "candidates")
                        if isinstance(dump.get(k), list)), [])
    else:
        entries = dump if isinstance(dump, list) else []
    rows, seen = [], set()
    for raw in entries:
        row = map_entry(raw, registry_format)
        if row is None or row["capability_slot"] in seen:
            continue
        seen.add(row["capability_slot"])
        rows.append(row)
    return rows


def ingest_to_feed(dump_path: str | Path, *, registry_format: str, out_path: str | Path) -> dict:
    """Read a registry dump file, map it, and write a discovered-feed JSON the runner ingests. Returns a summary."""
    dump = json.loads(Path(dump_path).read_text(encoding="utf-8"))
    rows = ingest_dump(dump, registry_format=registry_format)
    feed = {"feed_version": "DiscoveredCapabilityFeed.v1", "discovered_at": "bulk",
            "discovery_method": f"bulk_registry_ingest({registry_format}) — deterministic field mapping, no LLM",
            "governance": "CANDIDATES ONLY — discovery is not trust; bulk-ingested heuristics, Stage-2 confirm pending.",
            "candidates": rows}
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(feed, ensure_ascii=False), encoding="utf-8")
    return {"registry_format": registry_format, "candidates": len(rows), "out_path": str(out), "serves_truth": False}
