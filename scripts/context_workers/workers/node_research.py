"""Node research, OSINT enrichment, and fact-verification workers.

These workers turn detected graph nodes into evidence-backed research tasks. The
default behavior is planning and preflight only; external tools run only when a
service URL, CLI, or API key is configured and the payload satisfies the
authorization policy for sensitive node types.
"""
from __future__ import annotations

import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

from scripts._config import NODE_RESEARCH_RUNTIME_SETTINGS, REPO_ROOT
from scripts.context_workers.common import compact, stable_hash
from scripts.context_workers.registry import TaskContext, TaskResult, registry
from scripts.db.runtime_settings import runtime_setting
from scripts.db.setting_profile_rows import setting_profile_rows_by_namespace

SENSITIVE_NODE_TYPES = {"person", "email", "phone", "username", "private_person"}
ACTIVE_RECON_TOOLS = {"amass", "theharvester", "subfinder", "dnsx"}

TOOL_CATALOG: dict[str, dict[str, Any]] = {
    "local-evidence": {"kind": "local", "node_types": ["any"], "auth_required": False},
    "openosint": {"kind": "cli", "executable": "openosint", "node_types": ["email", "username", "domain", "ip", "phone"], "auth_required": False},
    "spiderfoot": {"kind": "service", "env": "SPIDERFOOT_URL", "node_types": ["domain", "ip", "email", "username", "phone", "company"], "auth_required": False},
    "osintbuddy": {"kind": "service", "env": "OSINTBUDDY_URL", "node_types": ["any"], "auth_required": False},
    "maltego": {"kind": "service", "env": "MALTEGO_TRANSFORM_URL", "node_types": ["any"], "auth_required": False},
    "recon-ng": {"kind": "cli", "executable": "recon-ng", "node_types": ["domain", "company", "person"], "auth_required": False},
    "aleph": {"kind": "service", "env": "ALEPH_URL", "node_types": ["person", "company", "document", "address"], "auth_required": False},
    "openaleph": {"kind": "service", "env": "OPENALEPH_URL", "node_types": ["person", "company", "document", "address"], "auth_required": False},
    "opensanctions-yente": {"kind": "service", "env": "YENTE_URL", "node_types": ["person", "company", "vessel", "asset"], "auth_required": False},
    "opencorporates": {"kind": "api", "env": "OPENCORPORATES_API_TOKEN", "node_types": ["company"], "auth_required": False},
    "gleif": {"kind": "api", "env": "GLEIF_API_BASE", "node_types": ["company"], "auth_required": False},
    "companies-house": {"kind": "api", "env": "COMPANIES_HOUSE_API_KEY", "node_types": ["company"], "auth_required": False},
    "sec-edgar": {"kind": "api", "env": "SEC_EDGAR_USER_AGENT", "node_types": ["company"], "auth_required": False},
    "openownership-bods": {"kind": "service", "env": "OPENOWNERSHIP_BODS_URL", "node_types": ["company", "person"], "auth_required": False},
    "icij-offshore-leaks": {"kind": "service", "env": "ICIJ_OFFSHORE_LEAKS_URL", "node_types": ["company", "person", "address"], "auth_required": False},
    "openalex": {"kind": "api", "env": "OPENALEX_EMAIL", "node_types": ["work", "author", "institution", "funder"], "auth_required": False},
    "crossref": {"kind": "api", "env": "CROSSREF_MAILTO", "node_types": ["work", "doi", "journal"], "auth_required": False},
    "orcid": {"kind": "api", "env": "ORCID_API_BASE", "node_types": ["person", "author"], "auth_required": False},
    "ror": {"kind": "api", "env": "ROR_API_BASE", "node_types": ["institution", "company"], "auth_required": False},
    "sherlock": {"kind": "cli", "executable": "sherlock", "node_types": ["username"], "auth_required": True},
    "maigret": {"kind": "cli", "executable": "maigret", "node_types": ["username"], "auth_required": True},
    "social-analyzer": {"kind": "cli", "executable": "social-analyzer", "node_types": ["username", "person"], "auth_required": True},
    "holehe": {"kind": "cli", "executable": "holehe", "node_types": ["email"], "auth_required": True},
    "phoneinfoga": {"kind": "cli", "executable": "phoneinfoga", "node_types": ["phone"], "auth_required": True},
    "amass": {"kind": "cli", "executable": "amass", "node_types": ["domain"], "auth_required": True, "auth_scope": "active_recon"},
    "theharvester": {"kind": "cli", "executable": "theHarvester", "node_types": ["domain", "company"], "auth_required": True, "auth_scope": "active_recon"},
    "subfinder": {"kind": "cli", "executable": "subfinder", "node_types": ["domain"], "auth_required": True, "auth_scope": "active_recon"},
    "dnsx": {"kind": "cli", "executable": "dnsx", "node_types": ["domain"], "auth_required": True, "auth_scope": "active_recon"},
    "shodan": {"kind": "api", "env": "SHODAN_API_KEY", "node_types": ["ip", "domain"], "auth_required": False},
    "censys": {"kind": "api", "env": "CENSYS_API_ID", "node_types": ["ip", "domain", "certificate"], "auth_required": False},
    "virustotal": {"kind": "api", "env": "VIRUSTOTAL_API_KEY", "node_types": ["ip", "domain", "hash", "url"], "auth_required": False},
    "abuseipdb": {"kind": "api", "env": "ABUSEIPDB_API_KEY", "node_types": ["ip"], "auth_required": False},
    "securitytrails": {"kind": "api", "env": "SECURITYTRAILS_API_KEY", "node_types": ["domain", "ip"], "auth_required": False},
    "opencti": {"kind": "service", "env": "OPENCTI_URL", "node_types": ["ip", "domain", "hash", "threat_actor", "malware"], "auth_required": False},
    "misp": {"kind": "service", "env": "MISP_URL", "node_types": ["ip", "domain", "hash", "threat_event"], "auth_required": False},
    "mitre-attack-stix": {"kind": "service", "env": "MITRE_ATTACK_STIX_URL", "node_types": ["threat_actor", "malware", "technique"], "auth_required": False},
    "nominatim": {"kind": "service", "env": "NOMINATIM_URL", "node_types": ["address", "location", "place"], "auth_required": False},
    "geonames": {"kind": "api", "env": "GEONAMES_USERNAME", "node_types": ["address", "location", "place"], "auth_required": False},
    "overpass": {"kind": "service", "env": "OVERPASS_URL", "node_types": ["address", "location", "place"], "auth_required": False},
    "mapillary": {"kind": "api", "env": "MAPILLARY_TOKEN", "node_types": ["image", "location", "place"], "auth_required": False},
    "exiftool": {"kind": "cli", "executable": "exiftool", "node_types": ["image", "video", "document"], "auth_required": False},
    "invid-weverify": {"kind": "service", "env": "INVID_URL", "node_types": ["image", "video", "url"], "auth_required": False},
    "google-fact-check": {"kind": "api", "env": "GOOGLE_FACT_CHECK_API_KEY", "node_types": ["claim"], "auth_required": False},
    "claimreview": {"kind": "service", "env": "CLAIMREVIEW_URL", "node_types": ["claim"], "auth_required": False},
    "media-cloud": {"kind": "api", "env": "MEDIA_CLOUD_API_KEY", "node_types": ["claim", "url", "organization"], "auth_required": False},
    "hoaxy": {"kind": "service", "env": "HOAXY_URL", "node_types": ["claim", "url"], "auth_required": False},
    "archivebox": {"kind": "service", "env": "ARCHIVEBOX_URL", "node_types": ["url", "claim", "document"], "auth_required": False},
    "wayback": {"kind": "api", "env": "WAYBACK_API_BASE", "node_types": ["url", "claim", "document"], "auth_required": False},
    "hunchly": {"kind": "service", "env": "HUNCHLY_URL", "node_types": ["url", "claim", "document"], "auth_required": False},
    "tavily": {"kind": "api", "env": "TAVILY_API_KEY", "node_types": ["any"], "auth_required": False},
    "exa": {"kind": "api", "env": "EXA_API_KEY", "node_types": ["any"], "auth_required": False},
    "firecrawl": {"kind": "service", "env": "FIRECRAWL_URL", "node_types": ["url", "claim", "company", "person"], "auth_required": False},
    "crawl4ai": {"kind": "service", "env": "CRAWL4AI_URL", "node_types": ["url", "claim", "company", "person"], "auth_required": False},
    "openrefine-reconcile": {"kind": "service", "env": "OPENREFINE_RECONCILE_URL", "node_types": ["any"], "auth_required": False},
    "wikidata": {"kind": "service", "env": "WIKIDATA_SPARQL_URL", "node_types": ["any"], "auth_required": False},
    "dedupe": {"kind": "module", "module": "dedupe", "node_types": ["any"], "auth_required": False},
    "splink": {"kind": "module", "module": "splink", "node_types": ["any"], "auth_required": False},
}

NODE_ROUTES: dict[str, list[str]] = {
    "company": ["local-evidence", "opencorporates", "gleif", "companies-house", "sec-edgar", "opensanctions-yente", "openownership-bods", "icij-offshore-leaks", "aleph", "tavily", "exa"],
    "organization": ["local-evidence", "opencorporates", "gleif", "opensanctions-yente", "ror", "wikidata", "tavily", "exa"],
    "person": ["local-evidence", "opensanctions-yente", "aleph", "openaleph", "wikidata", "orcid", "tavily", "exa"],
    "username": ["local-evidence", "openosint", "sherlock", "maigret", "social-analyzer"],
    "email": ["local-evidence", "openosint", "holehe", "spiderfoot"],
    "phone": ["local-evidence", "openosint", "phoneinfoga", "spiderfoot"],
    "domain": ["local-evidence", "openosint", "spiderfoot", "amass", "theharvester", "subfinder", "dnsx", "shodan", "censys", "virustotal", "securitytrails", "archivebox"],
    "ip": ["local-evidence", "openosint", "spiderfoot", "shodan", "censys", "virustotal", "abuseipdb", "opencti", "misp"],
    "work": ["local-evidence", "openalex", "crossref", "orcid", "ror", "wikidata"],
    "paper": ["local-evidence", "openalex", "crossref", "orcid", "ror", "wikidata"],
    "doi": ["local-evidence", "crossref", "openalex"],
    "institution": ["local-evidence", "ror", "openalex", "wikidata"],
    "address": ["local-evidence", "nominatim", "geonames", "overpass", "opensanctions-yente"],
    "location": ["local-evidence", "nominatim", "geonames", "overpass", "mapillary"],
    "image": ["local-evidence", "exiftool", "invid-weverify", "mapillary", "archivebox"],
    "video": ["local-evidence", "exiftool", "invid-weverify", "archivebox"],
    "claim": ["local-evidence", "google-fact-check", "claimreview", "media-cloud", "hoaxy", "tavily", "exa", "archivebox", "wayback"],
    "url": ["local-evidence", "firecrawl", "crawl4ai", "archivebox", "wayback", "virustotal", "tavily", "exa"],
}

VERIFICATION_TIERS = {
    0: "detected",
    1: "enriched",
    2: "resolved",
    3: "corroborated",
    4: "verified",
    5: "contradicted",
    6: "stale",
}

NODE_RESEARCH_TOOL_CATALOG_NAMESPACE = "baltor.node_research.tool_catalog"
NODE_RESEARCH_ROUTE_NAMESPACE = "baltor.node_research.route"

# Keep literal registries as static/offline fallbacks. Runtime globals below are
# replaced from setting_profile seed rows when those rows are available.
TOOL_CATALOG_SEED = TOOL_CATALOG
NODE_ROUTES_SEED = NODE_ROUTES
NODE_RESEARCH_RUNTIME_NAMESPACE = "baltor.node_research.runtime"


def _node_research_setting(name: str) -> str:
    return runtime_setting(
        namespace=NODE_RESEARCH_RUNTIME_NAMESPACE,
        definitions=NODE_RESEARCH_RUNTIME_SETTINGS,
        name=name,
    )


def _node_research_env(name: str) -> str:
    return str(NODE_RESEARCH_RUNTIME_SETTINGS[name]["env"])


def _node_research_setting_profile_path() -> Path:
    raw_path = _node_research_setting("setting_profile_path")
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _setting_seed_rows(namespace: str) -> list[dict[str, Any]]:
    try:
        return setting_profile_rows_by_namespace(
            namespace,
            _node_research_setting_profile_path(),
            prefer_database=True,
        )
    except (RuntimeError, ValueError):
        return []


def _tool_catalog_from_setting_rows(fallback: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rows = _setting_seed_rows(NODE_RESEARCH_TOOL_CATALOG_NAMESPACE)
    if not rows:
        return fallback
    catalog: dict[str, dict[str, Any]] = {}
    for row in rows:
        default_value = row.get("default_value")
        if not isinstance(default_value, dict):
            return fallback
        tool = str(default_value.get("tool") or row.get("setting_key") or "")
        kind = str(default_value.get("kind") or "")
        node_types = default_value.get("node_types")
        if not tool or kind not in {"api", "cli", "local", "module", "service"} or not isinstance(node_types, list):
            return fallback
        spec = {key: value for key, value in default_value.items() if key != "tool"}
        spec["node_types"] = [str(item) for item in node_types]
        spec["auth_required"] = bool(spec.get("auth_required"))
        catalog[tool] = spec
    return catalog or fallback


def _node_routes_from_setting_rows(fallback: dict[str, list[str]], catalog: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    rows = _setting_seed_rows(NODE_RESEARCH_ROUTE_NAMESPACE)
    if not rows:
        return fallback
    routes: dict[str, list[str]] = {}
    for row in rows:
        default_value = row.get("default_value")
        if not isinstance(default_value, dict):
            return fallback
        node_type = str(default_value.get("node_type") or row.get("setting_key") or "")
        tools = default_value.get("tools")
        if not node_type or not isinstance(tools, list):
            return fallback
        tool_names = [str(tool) for tool in tools]
        if any(tool not in catalog for tool in tool_names):
            return fallback
        routes[node_type] = tool_names
    return routes or fallback


TOOL_CATALOG = _tool_catalog_from_setting_rows(TOOL_CATALOG_SEED)
NODE_ROUTES = _node_routes_from_setting_rows(NODE_ROUTES_SEED, TOOL_CATALOG)


def _authorized(payload: dict[str, Any]) -> bool:
    return bool(payload.get("authorized")) or _node_research_setting("authorized").lower() in {"1", "true", "yes"}


def _active_recon_authorized(payload: dict[str, Any]) -> bool:
    return (
        _authorized(payload)
        or bool(payload.get("active_recon_authorized"))
        or _node_research_setting("active_recon_authorized").lower() in {"1", "true", "yes"}
    )


def _node_type(node: dict[str, Any]) -> str:
    return compact(str(node.get("node_type") or node.get("type") or node.get("kind") or "unknown")).lower().replace(" ", "_")


def _node_label(node: dict[str, Any]) -> str:
    return compact(str(node.get("label") or node.get("name") or node.get("text") or node.get("value") or ""))


def _tool_ready(tool: str) -> dict[str, Any]:
    spec = TOOL_CATALOG[tool]
    kind = spec["kind"]
    if kind == "local":
        return {"configured": True, "kind": kind}
    if kind == "cli":
        executable = str(spec["executable"])
        path_parts = [Path(part) for part in os.environ.get("PATH", "").split(os.pathsep)]
        return {"configured": any((part / executable).exists() for part in path_parts), "kind": kind, "executable": executable}
    if kind in {"service", "api"}:
        env_var = str(spec["env"])
        return {"configured": bool(os.environ.get(env_var)), "kind": kind, "env": env_var}
    if kind == "module":
        import importlib.util

        module = str(spec["module"])
        return {"configured": importlib.util.find_spec(module) is not None, "kind": kind, "module": module}
    return {"configured": False, "kind": kind}


def _candidate_tools(node_type: str, payload: dict[str, Any]) -> list[str]:
    tools = list(NODE_ROUTES.get(node_type, []))
    if not tools:
        tools = ["local-evidence", "wikidata", "tavily", "exa", "openrefine-reconcile"]
    allow = payload.get("enabled_node_research_tools")
    if isinstance(allow, list):
        allowed = {str(item) for item in allow}
        tools = [tool for tool in tools if tool in allowed]
    disabled = payload.get("disabled_node_research_tools")
    if isinstance(disabled, list):
        blocked = {str(item) for item in disabled}
        tools = [tool for tool in tools if tool not in blocked]
    external_enabled = (
        bool(payload.get("enable_external_node_research"))
        or _node_research_setting("enable_external").lower() in {"1", "true", "yes"}
    )
    if not external_enabled:
        tools = [tool for tool in tools if TOOL_CATALOG.get(tool, {}).get("kind") == "local"]
        if not tools:
            tools = ["local-evidence"]
    return tools


def _needed_facts(node_type: str) -> list[str]:
    return {
        "company": ["legal_name", "jurisdiction", "identifier", "officers", "ownership", "sanctions_screening", "source_urls"],
        "organization": ["legal_name", "identifier", "location", "official_url", "source_urls"],
        "person": ["stable_identifier", "affiliation", "public_roles", "sanctions_screening", "source_urls"],
        "username": ["candidate_profiles", "profile_crosslinks", "confidence_signals"],
        "email": ["authorized_account_presence", "domain", "breach_exposure_if_authorized"],
        "phone": ["country", "carrier_or_line_type", "public_listing_if_authorized"],
        "domain": ["dns_records", "subdomains", "certificates", "ownership_signals", "threat_intel"],
        "ip": ["asn", "geolocation", "open_services", "abuse_reports", "threat_intel"],
        "claim": ["claimant", "source_urls", "fact_checks", "supporting_sources", "contradicting_sources", "archive_snapshots"],
        "url": ["page_title", "canonical_url", "archive_snapshot", "content_hash", "entities"],
        "work": ["doi", "authors", "venue", "publisher", "citations", "license"],
        "paper": ["doi", "authors", "venue", "publisher", "citations", "license"],
        "address": ["normalized_address", "coordinates", "jurisdiction", "source_urls"],
        "location": ["coordinates", "osm_id", "nearby_features", "source_urls"],
    }.get(node_type, ["stable_identifier", "source_urls", "candidate_aliases", "corroborating_sources"])


@registry.register(
    "node.research.catalog",
    lane="research",
    description="Report OpenOSINT-style node-enrichment tools, supported node types, readiness, and authorization requirements.",
    emits=("node_research_catalog",),
    capabilities=("osint_catalog", "node_enrichment", "preflight", "authorization_gate"),
    task_types=("node.research.catalog", "osint.node_research.catalog"),
    image="baltor-worker-research",
    output_contract="node_research_catalog.v1",
)
def node_research_catalog(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    tools = {}
    for name, spec in TOOL_CATALOG.items():
        readiness = _tool_ready(name)
        tools[name] = {
            "kind": spec["kind"],
            "node_types": spec["node_types"],
            "auth_required": bool(spec.get("auth_required")),
            **readiness,
        }
    return TaskResult.success({
        "node_research_catalog": {
            "authorized": _authorized(payload),
            "tools": tools,
            "verification_tiers": VERIFICATION_TIERS,
            "policy": "Public business records, official registries, business websites, and non-personal address/domain facts may be enriched when configured. Person/email/phone/username enrichment and active recon require authorization. Treat all enrichment as evidence-backed candidates until corroborated or reviewed.",
        }
    })


@registry.register(
    "node.research.plan",
    lane="research",
    description="Create lawful research tasks for detected graph nodes, routed by node type and required evidence.",
    emits=("node_research_tasks", "node_research_routes"),
    capabilities=("node_research_planning", "fact_verification", "osint_routing", "evidence_requirements"),
    task_types=("node.research.plan", "osint.node_research.plan"),
    image="baltor-worker-research",
    output_contract="node_research_plan.v1",
)
def node_research_plan(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    raw_nodes = payload.get("nodes") or payload.get("entities") or payload.get("proper_nouns") or []
    if isinstance(payload.get("node"), dict):
        raw_nodes = [payload["node"]]
    if not isinstance(raw_nodes, list):
        return TaskResult.failure("nodes list or node object required")
    tasks = []
    routes = {}
    warnings = []
    for index, node in enumerate(raw_nodes[: int(payload.get("max_nodes") or 100)], 1):
        if not isinstance(node, dict):
            node = {"label": str(node), "type": "unknown"}
        node_type = _node_type(node)
        label = _node_label(node)
        if not label:
            continue
        tools = _candidate_tools(node_type, payload)
        sensitive = node_type in SENSITIVE_NODE_TYPES
        if sensitive and not _authorized(payload):
            warnings.append(f"{label}: sensitive node type {node_type} planned but external enrichment requires authorization")
        if any(tool in ACTIVE_RECON_TOOLS for tool in tools) and not _active_recon_authorized(payload):
            warnings.append(
                f"{label}: active reconnaissance tools planned but require "
                f"active_recon_authorized=true or {_node_research_env('active_recon_authorized')}=true"
            )
        node_id = str(node.get("id") or stable_hash("node", f"{node_type}:{label}", index))
        routes[node_id] = tools
        tasks.append({
            "task_id": stable_hash("node-research-task", f"{ctx.run_id}:{node_id}:{','.join(tools)}", index),
            "task": "node.research.enrich",
            "run_id": ctx.run_id,
            "tenant_id": ctx.tenant_id,
            "state": "queued",
            "lane": "research",
            "payload": {
                "node": {"node_id": node_id, "label": label, "node_type": node_type},
                "candidate_tools": tools,
                "needed_facts": _needed_facts(node_type),
                "authorized": _authorized(payload),
                "active_recon_authorized": _active_recon_authorized(payload),
            },
            "node": {"node_id": node_id, "label": label, "node_type": node_type},
            "needed_facts": _needed_facts(node_type),
            "candidate_tools": tools,
            "requires_authorization": sensitive,
            "requires_active_recon_authorization": any(tool in ACTIVE_RECON_TOOLS for tool in tools),
            "verification_policy": {
                "initial_tier": VERIFICATION_TIERS[0],
                "target_tier": "verified" if node_type in {"company", "claim", "domain", "ip"} else "corroborated",
                "do_not_auto_merge": node_type in {"person", "username", "email", "phone"},
            },
        })
    return TaskResult.success({"node_research_tasks": tasks, "node_research_routes": routes}, warnings=warnings)


def _evidence_record(ctx: TaskContext, node: dict[str, Any], tool: str, status: str, detail: dict[str, Any]) -> dict[str, Any]:
    node_id = str(node.get("node_id") or node.get("id") or stable_hash("node", _node_label(node), 1))
    label = _node_label(node)
    return {
        "evidence_id": stable_hash("evidence", f"{ctx.run_id}:{node_id}:{tool}:{status}:{json.dumps(detail, sort_keys=True, default=str)[:500]}", 1),
        "source_name": tool,
        "source_type": TOOL_CATALOG.get(tool, {}).get("kind", "unknown"),
        "retrieved_at": int(time.time()),
        "supports_node": node_id,
        "claim": f"{tool} returned {status} for {label}",
        "confidence": 0.0 if status in {"not_configured", "missing_dependency", "authorization_required"} else 0.35,
        "detail": detail,
    }


def _run_tool(ctx: TaskContext, node: dict[str, Any], tool: str, payload: dict[str, Any]) -> dict[str, Any]:
    spec = TOOL_CATALOG[tool]
    node_type = _node_type(node)
    if node_type in SENSITIVE_NODE_TYPES and not _authorized(payload):
        return _evidence_record(ctx, node, tool, "authorization_required", {"reason": f"person/email/phone/username enrichment requires authorized=true or {_node_research_env('authorized')}=true"})
    if spec.get("auth_scope") == "active_recon" and not _active_recon_authorized(payload):
        return _evidence_record(ctx, node, tool, "authorization_required", {"reason": f"active reconnaissance requires active_recon_authorized=true or {_node_research_env('active_recon_authorized')}=true"})
    if spec.get("auth_required") and not _authorized(payload):
        return _evidence_record(ctx, node, tool, "authorization_required", {"reason": f"authorized=true or {_node_research_env('authorized')}=true required"})
    if node_type not in spec.get("node_types", []) and "any" not in spec.get("node_types", []):
        return _evidence_record(ctx, node, tool, "not_applicable", {"node_type": node_type})
    ready = _tool_ready(tool)
    if not ready.get("configured"):
        return _evidence_record(ctx, node, tool, "not_configured", ready)
    label = _node_label(node)
    try:
        if spec["kind"] == "local":
            return _evidence_record(
                ctx,
                node,
                tool,
                "ready",
                {
                    "label": label,
                    "node_type": node_type,
                    "source": "local_context_graph",
                    "note": "Local evidence record created from parsed corpus metadata; external enrichment remains opt-in.",
                },
            )
        if spec["kind"] == "cli":
            executable = str(spec["executable"])
            proc = subprocess.run([executable, label], capture_output=True, text=True, timeout=int(payload.get("timeout_s") or 90), check=False)
            return _evidence_record(ctx, node, tool, "ready" if proc.returncode == 0 else "failed", {"returncode": proc.returncode, "stdout": proc.stdout[-12000:], "stderr": proc.stderr[-4000:]})
        if spec["kind"] in {"service", "api"}:
            env_var = str(spec["env"])
            target = os.environ.get(env_var, "").rstrip("/")
            if not target.startswith(("http://", "https://")):
                return _evidence_record(ctx, node, tool, "configured", {"env": env_var, "note": "API key/configuration present; direct endpoint call not implemented for this source"})
            body = json.dumps({"node": node, "query": label, "node_type": node_type, "run_id": ctx.run_id}).encode("utf-8")
            req = urllib.request.Request(target, data=body, headers={"content-type": "application/json"})
            with urllib.request.urlopen(req, timeout=int(payload.get("timeout_s") or 30)) as response:  # noqa: S310 - operator configured endpoint
                raw = response.read().decode("utf-8", errors="replace")
            return _evidence_record(ctx, node, tool, "ready", {"response": raw[:20000]})
        return _evidence_record(ctx, node, tool, "configured", ready)
    except Exception as exc:  # noqa: BLE001
        return _evidence_record(ctx, node, tool, "failed", {"error": repr(exc)})


@registry.register(
    "node.research.enrich",
    lane="research",
    description="Run configured node-enrichment tools and return evidence records without auto-verifying weak OSINT signals.",
    emits=("node_evidence", "proposed_node_edges", "verification_state"),
    capabilities=("node_enrichment", "osint", "evidence_capture", "fact_verification"),
    task_types=("node.research.enrich", "osint.node_research.enrich"),
    image="baltor-worker-research",
    output_contract="node_research_evidence.v1",
)
def node_research_enrich(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    node = payload.get("node") if isinstance(payload.get("node"), dict) else {}
    if not node:
        return TaskResult.failure("node object required")
    node_type = _node_type(node)
    tools = payload.get("candidate_tools") if isinstance(payload.get("candidate_tools"), list) else _candidate_tools(node_type, payload)
    max_tools = int(payload.get("max_tools") or len(tools))
    evidence = [_run_tool(ctx, node, str(tool), payload) for tool in tools[:max_tools] if str(tool) in TOOL_CATALOG]
    configured_hits = [item for item in evidence if item["detail"] and item["confidence"] > 0]
    tier = 1 if configured_hits else 0
    if len(configured_hits) >= 2:
        tier = 3
    proposed_edges = [
        {
            "source": str(node.get("node_id") or node.get("id") or _node_label(node)),
            "type": "ENRICHED_BY",
            "target": item["source_name"],
            "evidence_ids": [item["evidence_id"]],
            "confidence": item["confidence"],
            "requires_human_review": node_type in {"person", "username", "email", "phone"} or item["confidence"] < 0.7,
        }
        for item in evidence
        if item["confidence"] > 0
    ]
    return TaskResult.success({
        "node_evidence": evidence,
        "proposed_node_edges": proposed_edges,
        "verification_state": {
            "node_type": node_type,
            "tier": tier,
            "tier_label": VERIFICATION_TIERS[tier],
            "configured_evidence_count": len(configured_hits),
            "evidence_count": len(evidence),
            "policy": "OSINT enrichment creates candidates; primary-source or analyst verification is required for verified graph facts.",
        },
    })


@registry.register(
    "node.evidence.score",
    lane="verify",
    description="Score evidence records into verification tiers without collapsing candidates into verified facts.",
    emits=("verification_state", "evidence_scores"),
    capabilities=("evidence_scoring", "verification_tiers", "provenance"),
    task_types=("node.evidence.score", "fact.evidence.score"),
    image="baltor-worker-audit",
    output_contract="node_evidence_score.v1",
)
def node_evidence_score(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    evidence = payload.get("node_evidence") if isinstance(payload.get("node_evidence"), list) else payload.get("evidence")
    if not isinstance(evidence, list):
        return TaskResult.failure("node_evidence list required")
    primary_sources = {"opencorporates", "gleif", "companies-house", "sec-edgar", "crossref", "openalex", "ror", "google-fact-check"}
    ready = [item for item in evidence if isinstance(item, dict) and item.get("confidence", 0) > 0]
    primary = [item for item in ready if item.get("source_name") in primary_sources]
    contradicted = [item for item in evidence if isinstance(item, dict) and str(item.get("claim") or "").lower().startswith("contradict")]
    if contradicted:
        tier = 5
    elif primary:
        tier = 4
    elif len(ready) >= 2:
        tier = 3
    elif ready:
        tier = 1
    else:
        tier = 0
    return TaskResult.success({
        "verification_state": {
            "tier": tier,
            "tier_label": VERIFICATION_TIERS[tier],
            "ready_evidence_count": len(ready),
            "primary_evidence_count": len(primary),
            "contradiction_count": len(contradicted),
        },
        "evidence_scores": [
            {
                "evidence_id": item.get("evidence_id"),
                "source_name": item.get("source_name"),
                "confidence": item.get("confidence", 0),
                "source_weight": 1.0 if item.get("source_name") in primary_sources else 0.55,
            }
            for item in evidence
            if isinstance(item, dict)
        ],
    })
