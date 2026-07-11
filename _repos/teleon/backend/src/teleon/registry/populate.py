"""registry.populate — the DOGFOOD population pipeline: discovered signals -> governed registry RECORDS.

Turns signals (repo slugs from the harvester / FB miner / search hits) into candidate RECORDS, ENRICHES them
(via registry.enrich — embedding/description/keywords/labels/use_cases), and returns them staged as CANDIDATES
(discovery != trust; license-checked before adoption). This is HOW registries grow records — dogfooding the
menu + the enrichment worker. Honest-OFFLINE: a record is built deterministically from the slug + any provided
metadata; an optional live GitHub fetch (tools.web_fetch) can add stars/license/description when reachable.
serves_truth=false.
"""
from __future__ import annotations

import json

from ..tools.web_fetch import fetch
from .enrich import py_function_src_teleon_registry_enrich__enrich_record

py_var_src_teleon_registry_populate___GITHUB_API = "https://api.github.com/repos/"


def py_function_src_teleon_registry_populate__repo_to_record(py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__repo_to_record__slug: str, *, source: str = "harvest", desc: str = "",
                   stars: int | None = None, license_id: str | None = None) -> dict:
    """A GitHub repo slug ('owner/name') -> a candidate component record (no network)."""
    py_local_src_teleon_registry_populate__repo_to_record__owner, py_local_src_teleon_registry_populate__repo_to_record___, py_local_src_teleon_registry_populate__repo_to_record__name = py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__repo_to_record__slug.partition("/")
    return {
        "id": py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__repo_to_record__slug.replace("/", "__"), "name": py_local_src_teleon_registry_populate__repo_to_record__name, "repo": py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__repo_to_record__slug,
        "url": f"https://github.com/{py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__repo_to_record__slug}", "owner": py_local_src_teleon_registry_populate__repo_to_record__owner, "source": source,
        "description": desc, "stars": stars, "license": license_id,
        "candidate": True, "serves_truth": False,
    }


def py_function_src_teleon_registry_populate__fetch_repo_meta(py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__fetch_repo_meta__slug: str) -> dict:
    """OPTIONAL live enrichment via the GitHub API (keyless, honest-offline). Returns {} on any failure."""
    py_local_src_teleon_registry_populate__fetch_repo_meta__r = fetch(f"{py_var_src_teleon_registry_populate___GITHUB_API}{py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__fetch_repo_meta__slug}")
    if py_local_src_teleon_registry_populate__fetch_repo_meta__r.get("error") or not py_local_src_teleon_registry_populate__fetch_repo_meta__r.get("text"):
        return {}
    try:
        py_local_src_teleon_registry_populate__fetch_repo_meta__d = json.loads(py_local_src_teleon_registry_populate__fetch_repo_meta__r["text"])
    except (ValueError, TypeError):
        return {}
    return {"desc": py_local_src_teleon_registry_populate__fetch_repo_meta__d.get("description") or "", "stars": py_local_src_teleon_registry_populate__fetch_repo_meta__d.get("stargazers_count"),
            "license_id": (py_local_src_teleon_registry_populate__fetch_repo_meta__d.get("license") or {}).get("spdx_id")}


def py_function_src_teleon_registry_populate__populate(py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__populate__slugs: list[str], *, py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__populate__source: str = "harvest", py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__populate__live: bool = False) -> list[dict]:
    """Repo slugs -> ENRICHED candidate records for the component/tool registry.

    live=False (default) is deterministic + offline. live=True adds GitHub metadata when reachable (honest-fail).
    """
    py_local_src_teleon_registry_populate__populate__out = []
    for py_local_src_teleon_registry_populate__populate__s in py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__populate__slugs:
        py_local_src_teleon_registry_populate__populate__meta = py_function_src_teleon_registry_populate__fetch_repo_meta(py_local_src_teleon_registry_populate__populate__s) if py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__populate__live else {}
        py_local_src_teleon_registry_populate__populate__rec = py_function_src_teleon_registry_populate__repo_to_record(py_local_src_teleon_registry_populate__populate__s, source=py_arg_src_teleon_registry_populate__py_function_src_teleon_registry_populate__populate__source, desc=py_local_src_teleon_registry_populate__populate__meta.get("desc", ""),
                             stars=py_local_src_teleon_registry_populate__populate__meta.get("stars"), license_id=py_local_src_teleon_registry_populate__populate__meta.get("license_id"))
        py_local_src_teleon_registry_populate__populate__out.append(py_function_src_teleon_registry_enrich__enrich_record(py_local_src_teleon_registry_populate__populate__rec))
    return py_local_src_teleon_registry_populate__populate__out
