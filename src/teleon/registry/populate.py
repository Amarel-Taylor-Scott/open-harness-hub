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
from .enrich import enrich_record

_GITHUB_API = "https://api.github.com/repos/"


def repo_to_record(slug: str, *, source: str = "harvest", desc: str = "",
                   stars: int | None = None, license_id: str | None = None) -> dict:
    """A GitHub repo slug ('owner/name') -> a candidate component record (no network)."""
    owner, _, name = slug.partition("/")
    return {
        "id": slug.replace("/", "__"), "name": name, "repo": slug,
        "url": f"https://github.com/{slug}", "owner": owner, "source": source,
        "description": desc, "stars": stars, "license": license_id,
        "candidate": True, "serves_truth": False,
    }


def fetch_repo_meta(slug: str) -> dict:
    """OPTIONAL live enrichment via the GitHub API (keyless, honest-offline). Returns {} on any failure."""
    r = fetch(f"{_GITHUB_API}{slug}")
    if r.get("error") or not r.get("text"):
        return {}
    try:
        d = json.loads(r["text"])
    except (ValueError, TypeError):
        return {}
    return {"desc": d.get("description") or "", "stars": d.get("stargazers_count"),
            "license_id": (d.get("license") or {}).get("spdx_id")}


def populate(slugs: list[str], *, source: str = "harvest", live: bool = False) -> list[dict]:
    """Repo slugs -> ENRICHED candidate records for the component/tool registry.

    live=False (default) is deterministic + offline. live=True adds GitHub metadata when reachable (honest-fail).
    """
    out = []
    for s in slugs:
        meta = fetch_repo_meta(s) if live else {}
        rec = repo_to_record(s, source=source, desc=meta.get("desc", ""),
                             stars=meta.get("stars"), license_id=meta.get("license_id"))
        out.append(enrich_record(rec))
    return out
