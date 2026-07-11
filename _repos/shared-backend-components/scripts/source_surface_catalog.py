#!/usr/bin/env python3
"""scripts.source_surface_catalog — the governed, extensible map of WHERE primitives come from and HOW to search
each surface. Turns "think of more sources" into a one-row-per-surface registry the discovery lanes consume
(candidate-only). Covers code hosts, package registries, Q&A/forums, docs.* sites, API directories (RapidAPI /
APIs.guru / Postman), standards bodies, algorithm/learning sites, papers, real-app/product surfaces, infra/ops
registries, AI/agent registries, issue/security trackers, and the open web index — plus the SEARCH METHODS
(the "more ways to search them"), and the user-configurable-CREDENTIAL discipline for API-wrapper primitives.

Owner (2026-07-09): more sources / websites / GitHub / Stack Overflow / forums / textbooks; RapidAPI keys for API
endpoints; docs.<domain> docs -> API/usage/example primitives with user-configurable API keys. Every API-wrapper
primitive references credentials BY ENV NAME (never an embedded key) so any user configures their own — the
credential-plane discipline (env-names-only). serves_truth=false; all mined rows stay candidate=true.

    python3 scripts/source_surface_catalog.py --self-test
    python3 scripts/source_surface_catalog.py --catalog          # print the full surface + method catalog
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/buildout_forge.py) ────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CATALOG_REL = "data/dev-intel/source_surface_catalog/catalog.json"

# ── source families -> surfaces. access ∈ {api, dump, crawl, bigquery, git_clone, registry_api}. auth is an ENV
#    NAME (user-configurable) or "" (none). yields = the primitive families this surface is richest in. ─────────
_FAMILIES: list[dict[str, Any]] = [
    {"family": "code_hosting", "surfaces": [
        {"name": "github_code_search", "access": "api", "auth": "GITHUB_TOKEN",
         "yields": ["parser", "validator", "adapter", "workflow", "test_fixture"],
         "search": ["path:<file> filters (Dockerfile/schema.prisma/*.tf/openapi.yaml)", "regex code search",
                    "stars/topic/language ranking", "commit-message + PR 'fix'/'refactor' search"]},
        {"name": "github_archive_bigquery", "access": "bigquery", "auth": "GOOGLE_APPLICATION_CREDENTIALS",
         "yields": ["issue_to_pr_repair", "popular_code"], "search": ["all GH events via BigQuery", "reverse-dep"]},
        {"name": "sourcegraph_universal", "access": "api", "auth": "",
         "yields": ["structural_code"], "search": ["structural/AST search across many repos"]},
        {"name": "software_heritage", "access": "api", "auth": "",
         "yields": ["archived_code"], "search": ["content-addressed archive of all public code"]},
        {"name": "gitlab_bitbucket_codeberg", "access": "api", "auth": "",
         "yields": ["parser", "adapter"], "search": ["repo + code search per host"]}]},
    {"family": "package_registries", "surfaces": [
        {"name": "libraries_io", "access": "api", "auth": "LIBRARIES_IO_KEY",
         "yields": ["reverse_dependency", "popular_module"], "search": ["cross-registry reverse-dep + rank"]},
        {"name": "pypi_npm_crates_maven_go", "access": "registry_api", "auth": "",
         "yields": ["module_primitive", "adapter"], "search": ["download-count rank", "source tarball fetch"]},
        {"name": "docker_hub", "access": "registry_api", "auth": "",
         "yields": ["dockerfile_primitive", "healthcheck"], "search": ["popular images + Dockerfiles"]}]},
    {"family": "qa_forums", "surfaces": [
        {"name": "stackoverflow_stackexchange", "access": "dump", "auth": "",
         "yields": ["how_to_snippet", "error_fix", "validator"],
         "search": ["Stack Exchange API (tag/votes/accepted)", "Data Explorer SQL over the dump",
                    "quarterly data dump"]},
        {"name": "hacker_news", "access": "api", "auth": "",
         "yields": ["show_hn_apps", "launch_evidence"], "search": ["Algolia HN API", "GH-BigQuery HN dataset"]},
        {"name": "reddit_lobsters_devto", "access": "api", "auth": "REDDIT_CLIENT_ID",
         "yields": ["pattern", "tooling"], "search": ["subreddit/tag search", "top/hot ranking"]}]},
    {"family": "docs_sites", "surfaces": [
        {"name": "docs_dot_domain", "access": "crawl", "auth": "",
         "yields": ["api_wrapper", "usage_example", "config_schema", "error_mapper"],
         "search": ["sitemap.xml of docs.<domain>", "Docusaurus/ReadTheDocs/Mintlify/GitBook llms.txt",
                    "API-reference + 'examples'/'quickstart' pages -> endpoint primitives"]},
        {"name": "mdn_devdocs", "access": "crawl", "auth": "",
         "yields": ["web_api_primitive"], "search": ["DevDocs offline index", "MDN compat data"]}]},
    {"family": "api_directories", "surfaces": [
        {"name": "rapidapi_hub", "access": "api", "auth": "RAPIDAPI_KEY",
         "yields": ["api_wrapper", "enrichment_adapter", "search_adapter"],
         "search": ["RapidAPI Hub category browse", "per-endpoint OpenAPI -> typed wrapper primitive + variants"]},
        {"name": "apis_guru_openapi", "access": "api", "auth": "",
         "yields": ["api_wrapper", "response_schema"], "search": ["APIs.guru OpenAPI directory (thousands of specs)"]},
        {"name": "postman_public_network", "access": "api", "auth": "POSTMAN_API_KEY",
         "yields": ["api_wrapper", "contract_test"], "search": ["public collections -> request primitives"]}]},
    {"family": "standards_bodies", "surfaces": [
        {"name": "ietf_w3c_ecma_iso", "access": "crawl", "auth": "",
         "yields": ["parser", "validator", "spec_conformance"], "search": ["RFC/spec index", "ABNF/grammar mining"]},
        {"name": "vertical_standards", "access": "crawl", "auth": "",
         "yields": ["x12_parser", "fhir_validator", "ncpdp", "acord", "iso20022", "hl7", "dicom", "gs1"],
         "search": ["implementation guides -> segment/field validators + typed primitives"]}]},
    {"family": "learning_algorithms", "surfaces": [
        {"name": "algorithm_sites", "access": "crawl", "auth": "",
         "yields": ["algorithm_primitive", "data_structure"], "search": ["Rosetta Code (task x language matrix)",
                    "Project Euler", "LeetCode/Codeforces problem+editorial (respect ToS)"]},
        {"name": "open_textbooks_courseware", "access": "crawl", "auth": "",
         "yields": ["reference_algorithm", "worked_example"], "search": ["OpenStax/MIT OCW/CS50/Berkeley/Stanford"]},
        {"name": "kaggle", "access": "api", "auth": "KAGGLE_KEY",
         "yields": ["ml_primitive", "pipeline_step"], "search": ["Meta-Kaggle + Meta-Kaggle-Code notebooks"]}]},
    {"family": "papers", "surfaces": [
        {"name": "arxiv_paperswithcode_semanticscholar", "access": "api", "auth": "SEMANTIC_SCHOLAR_KEY",
         "yields": ["method_primitive", "algorithm"], "search": ["arXiv API", "Papers With Code repo links",
                    "Semantic Scholar citation graph"]}]},
    {"family": "real_apps_products", "surfaces": [
        {"name": "product_hunt_indiehackers_hn_show", "access": "api", "auth": "PRODUCTHUNT_TOKEN",
         "yields": ["app_genome_seed"], "search": ["launch posts (SOURCE evidence A0-A3 -> RealAppForge)"]},
        {"name": "oss_saas_and_starters", "access": "git_clone", "auth": "GITHUB_TOKEN",
         "yields": ["macro_primitive", "app_scaffold"],
         "search": ["awesome-selfhosted", "create-*-app / boilerplate repos", "OSS SaaS with test suites (A6 seed)"]}]},
    {"family": "infra_ops", "surfaces": [
        {"name": "iac_registries", "access": "registry_api", "auth": "",
         "yields": ["terraform_module", "helm_chart", "ansible_role", "gha_action"],
         "search": ["Terraform Registry", "Artifact Hub (Helm)", "Ansible Galaxy", "GitHub Actions Marketplace"]}]},
    {"family": "ai_agent", "surfaces": [
        {"name": "mcp_and_skill_registries", "access": "git_clone", "auth": "",
         "yields": ["mcp_tool", "skill", "agent_workflow"],
         "search": ["MCP server registries", "SKILL.md/.cursorrules/AGENTS.md", "awesome-claude-code",
                    "LangChain/LlamaIndex integration dirs"]}]},
    {"family": "issues_security", "surfaces": [
        {"name": "issue_pr_bugfix_pairs", "access": "api", "auth": "GITHUB_TOKEN",
         "yields": ["repair_primitive", "regression_test"], "search": ["issue->fixing-PR pairing = repair primitives"]},
        {"name": "cve_ghsa_nvd", "access": "api", "auth": "",
         "yields": ["security_gate", "vuln_pattern"], "search": ["GHSA/NVD advisories -> detection primitives"]}]},
    {"family": "web_index", "surfaces": [
        {"name": "common_crawl", "access": "dump", "auth": "",
         "yields": ["broad_web_docs"], "search": ["Common Crawl WARC/columnar index", "domain-scoped extraction"]},
        {"name": "programmable_search_rss", "access": "api", "auth": "SEARCH_API_KEY",
         "yields": ["targeted_discovery"], "search": ["programmable search engine", "RSS/sitemap monitoring"]}]},
]

# ── the "more ways to search them" — search METHODS applied across surfaces (add a row to extend). ─────────────
_SEARCH_METHODS: list[dict[str, str]] = [
    {"method": "text_search", "what": "keyword/regex over source text"},
    {"method": "code_ast_structural", "what": "tree-sitter / Sourcegraph structural search by code SHAPE, not text"},
    {"method": "semantic_embedding", "what": "embed the corpus + vector search (reuse our retrieval stack)"},
    {"method": "reverse_dependency_rank", "what": "mine the MOST-reused code (Libraries.io / registry rank)"},
    {"method": "popularity_rank", "what": "stars / downloads / votes as a value prior"},
    {"method": "issue_to_pr_pairing", "what": "bug -> fixing PR = a repair primitive + its regression test"},
    {"method": "test_file_mining", "what": "test files ENCODE fixtures + oracles (huge for fixture generation)"},
    {"method": "schema_mining", "what": "OpenAPI/JSON-Schema/Prisma/protobuf/SQL-DDL -> TYPED primitives + variants"},
    {"method": "diff_version_mining", "what": "changes across versions = deltas/variants (store deltas, not copies)"},
    {"method": "data_dump_sql", "what": "SO Data Explorer / BigQuery / GH Archive — query at scale, not scrape"},
    {"method": "web_index_crawl", "what": "Common Crawl / sitemap / llms.txt — bulk docs at scale"},
    {"method": "license_aware_filter", "what": "permissive-only for reuse; copyleft/proprietary = metadata-only"},
    {"method": "cross_source_dedup", "what": "same primitive across many sources = high-value canonical (edge-merge)"},
]

# ── credential discipline: API-wrapper primitives reference an ENV NAME; the user configures their own key. ────
CREDENTIAL_DISCIPLINE: dict[str, Any] = {
    "rule": "an API-wrapper primitive declares credentials by ENV NAME only (user-configurable); NEVER an embedded "
            "key. Keys live in gitignored .agent/<provider>_keys.txt or the user's env. Enforced by the "
            "credential-plane (env-names-only, deny-by-default).",
    "example": {"primitive": "rapidapi.<host>.<endpoint>", "credentials": [
        {"env_name": "RAPIDAPI_KEY", "provider": "rapidapi", "user_configurable": True, "required": True}]},
    "stores": [".agent/openrouter_keys.txt", ".agent/rapidapi_keys.txt", ".agent/github_token.txt (all gitignored)"],
}
# discovery lanes that already consume these surfaces (reuse-first — don't rebuild)
_EXISTING_CONSUMERS = {
    "continuous_primitive_scrape_loop.py": ["docs_sites", "qa_forums", "papers", "code_hosting", "web_index"],
    "real_app_forge.py": ["real_apps_products", "code_hosting"],
    "mine_meta_kaggle": ["learning_algorithms"],
    "api-endpoint-wrappers (repo)": ["api_directories", "docs_sites"],
    "standards factory / atlas": ["standards_bodies"],
}


def catalog() -> dict[str, Any]:
    surfaces = [s for f in _FAMILIES for s in f["surfaces"]]
    return {"record_type": "source_surface_catalog", "n_families": len(_FAMILIES), "n_surfaces": len(surfaces),
            "n_search_methods": len(_SEARCH_METHODS),
            "families": _FAMILIES, "search_methods": _SEARCH_METHODS,
            "credential_discipline": CREDENTIAL_DISCIPLINE, "existing_consumers": _EXISTING_CONSUMERS,
            "auth_env_names": sorted({s["auth"] for f in _FAMILIES for s in f["surfaces"] if s["auth"]}),
            **BOUNDARY}


def emit() -> dict[str, str]:
    out = resource(CATALOG_REL)
    out.parent.mkdir(parents=True, exist_ok=True)
    c = catalog()
    out.write_text(json.dumps(c, indent=2, sort_keys=True), encoding="utf-8")
    return {"catalog": str(out), "n_surfaces": str(c["n_surfaces"]), "n_families": str(c["n_families"])}


def self_test() -> bool:
    """Mutation-gated: the catalog is well-formed (every surface has access+auth+yields+search), covers the owner's
    asks (docs_sites, api_directories/RapidAPI, qa_forums, learning/textbooks, papers), enumerates search methods
    incl. schema/AST/test-mining, and the credential discipline embeds NO literal secret (env NAMES only)."""
    c = catalog()
    assert c["n_families"] >= 12 and c["n_surfaces"] >= 25, f"catalog must be broad: {c['n_surfaces']} surfaces"
    fams = {f["family"] for f in c["families"]}
    for required in ("docs_sites", "api_directories", "qa_forums", "learning_algorithms", "papers",
                     "code_hosting", "standards_bodies", "issues_security"):
        assert required in fams, f"missing source family {required}"
    for f in c["families"]:
        for s in f["surfaces"]:
            assert {"name", "access", "auth", "yields", "search"} <= set(s), f"malformed surface {s.get('name')}"
    methods = {m["method"] for m in c["search_methods"]}
    for required in ("code_ast_structural", "semantic_embedding", "schema_mining", "test_file_mining",
                     "issue_to_pr_pairing", "cross_source_dedup"):
        assert required in methods, f"missing search method {required}"
    # RapidAPI + docs.* present; credentials are ENV NAMES, never embedded keys.
    names = {s["name"] for f in c["families"] for s in f["surfaces"]}
    assert "rapidapi_hub" in names and "docs_dot_domain" in names, "RapidAPI + docs.<domain> must be catalogued"
    assert CREDENTIAL_DISCIPLINE["example"]["credentials"][0]["env_name"] == "RAPIDAPI_KEY"
    blob = json.dumps(c)
    assert "sk-or-v1-" not in blob and "ghp_" not in blob, "catalog must embed NO literal secret"
    assert c["serves_truth"] is False
    print(f"OK source_surface_catalog self-test: {c['n_families']} families / {c['n_surfaces']} surfaces "
          f"(incl. docs.<domain>, RapidAPI, StackOverflow, textbooks, papers, standards, issue->PR repair); "
          f"{c['n_search_methods']} search methods (AST/semantic/schema/test-mining/dedup); credentials are "
          f"ENV NAMES only ({len(c['auth_env_names'])} distinct, user-configurable); no embedded secret; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Governed catalog of primitive SOURCE surfaces + search methods.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--catalog", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.catalog:
        print(json.dumps(emit(), indent=2))
        c = catalog()
        for f in c["families"]:
            print(f"  {f['family']:22} {len(f['surfaces'])} surfaces: {', '.join(s['name'] for s in f['surfaces'])}")
        print(f"  search methods: {', '.join(m['method'] for m in c['search_methods'])}")
        return
    self_test()


if __name__ == "__main__":
    main()
