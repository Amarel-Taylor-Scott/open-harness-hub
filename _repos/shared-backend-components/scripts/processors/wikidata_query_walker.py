#!/usr/bin/env python3
"""Backs `processor/wikidata-query-walker`.

The leverage walker. Wikidata holds ~140M items, structured as
(subject, property, object) triples, with multilingual labels, free,
under CC0. One SPARQL query against query.wikidata.org returns hundreds
to thousands of structured knowledge nodes — orders of magnitude cheaper
than walking Wikipedia and far more reliable for catalog drafting since
each node is *already* structured.

Examples of valuable SPARQL queries for OHH catalog seeding:

  - All items that are instance-of `Q740445` (legal concept) + subclass-of
    `Q820655` (crime) → ~3,000 nodes → knowledge-pack drafts for legal-
    concept reference packs.

  - All items that are subclass-of `Q83337` (software framework) →
    several thousand → tool / adapter / pattern drafts.

  - All items in a specific subject (e.g., P31=Q15916648 = ISO standard
    or Q1063603 = standard) → comprehensive standards catalog seed.

  - All items with Wikipedia article + EU AI Act risk taxonomy mention
    → narrow high-value AI-governance seeding.

This walker exposes both PRESET queries (commonly useful) and ARBITRARY
SPARQL (advanced). Nodes carry the Wikidata Q-ID, English label,
description, Wikipedia URL, and a small set of structured claims.

CLI:
    python -m scripts.processors.wikidata_query_walker --self-test
    python -m scripts.processors.wikidata_query_walker --smoke-test
    python -m scripts.processors.wikidata_query_walker \\
        --preset legal-concepts --max-nodes 50
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.processors._walker_base import (
    DEFAULT_RATE_LIMIT_PER_SEC,
    RateLimiter,
    WalkStats,
    fetch_post_json,
)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# ─── Preset queries ─────────────────────────────────────────────────────────
#
# These are deliberately small and parameterized by LIMIT. The factory
# orchestrator can chain a preset with a higher LIMIT for a full seed run.

PRESETS: dict[str, str] = {
    # Items that are subclass-of crime (Q83267), with their English labels.
    "crimes": """
        SELECT ?item ?itemLabel ?itemDescription ?wikipediaUrl WHERE {
          ?item wdt:P279* wd:Q83267 .
          OPTIONAL {
            ?wikipediaUrl schema:about ?item ;
                          schema:isPartOf <https://en.wikipedia.org/> .
          }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        LIMIT %(limit)d
    """,
    # Standards (ISO, IETF, IEEE, etc.). Instance-of Q317623 (standard) or subclass.
    "standards": """
        SELECT ?item ?itemLabel ?itemDescription ?wikipediaUrl WHERE {
          ?item wdt:P31/wdt:P279* wd:Q317623 .
          OPTIONAL {
            ?wikipediaUrl schema:about ?item ;
                          schema:isPartOf <https://en.wikipedia.org/> .
          }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        LIMIT %(limit)d
    """,
    # Legal concepts (subclass-of Q740445).
    "legal-concepts": """
        SELECT ?item ?itemLabel ?itemDescription ?wikipediaUrl WHERE {
          ?item wdt:P279* wd:Q740445 .
          OPTIONAL {
            ?wikipediaUrl schema:about ?item ;
                          schema:isPartOf <https://en.wikipedia.org/> .
          }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        LIMIT %(limit)d
    """,
    # Software frameworks (subclass-of Q1130645).
    "software-frameworks": """
        SELECT ?item ?itemLabel ?itemDescription ?wikipediaUrl WHERE {
          ?item wdt:P279* wd:Q1130645 .
          OPTIONAL {
            ?wikipediaUrl schema:about ?item ;
                          schema:isPartOf <https://en.wikipedia.org/> .
          }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        LIMIT %(limit)d
    """,
    # Programming languages (instance-of Q9143).
    "programming-languages": """
        SELECT ?item ?itemLabel ?itemDescription ?wikipediaUrl WHERE {
          ?item wdt:P31 wd:Q9143 .
          OPTIONAL {
            ?wikipediaUrl schema:about ?item ;
                          schema:isPartOf <https://en.wikipedia.org/> .
          }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        LIMIT %(limit)d
    """,
    # Diseases (subclass-of Q12136).
    "diseases": """
        SELECT ?item ?itemLabel ?itemDescription ?wikipediaUrl WHERE {
          ?item wdt:P279* wd:Q12136 .
          OPTIONAL {
            ?wikipediaUrl schema:about ?item ;
                          schema:isPartOf <https://en.wikipedia.org/> .
          }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        LIMIT %(limit)d
    """,
    # International organizations (instance-of Q484652).
    "international-orgs": """
        SELECT ?item ?itemLabel ?itemDescription ?wikipediaUrl WHERE {
          ?item wdt:P31 wd:Q484652 .
          OPTIONAL {
            ?wikipediaUrl schema:about ?item ;
                          schema:isPartOf <https://en.wikipedia.org/> .
          }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        LIMIT %(limit)d
    """,
}

ABSOLUTE_NODE_CEILING = 10000


@dataclass
class WikidataNode:
    qid: str
    label: str
    description: str
    wikidata_url: str
    wikipedia_url: str = ""
    raw_claims: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "qid": self.qid,
            "label": self.label,
            "description": self.description,
            "wikidata_url": self.wikidata_url,
            "wikipedia_url": self.wikipedia_url,
            "raw_claims": dict(self.raw_claims),
        }


# ─── SPARQL ─────────────────────────────────────────────────────────────────


def _sparql(query: str, rate_limiter: RateLimiter, use_cache: bool) -> list[dict[str, Any]]:
    body = "query=" + _percent_encode(query)
    data = fetch_post_json(
        SPARQL_ENDPOINT,
        body,
        rate_limiter,
        cache_kind="wikidata",
        use_cache=use_cache,
        headers={"Accept": "application/sparql-results+json"},
    )
    return (data.get("results") or {}).get("bindings", []) or []


def _percent_encode(s: str) -> str:
    import urllib.parse
    return urllib.parse.quote(s, safe="")


def _parse_qid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1] if uri else ""


# ─── Public entrypoint ──────────────────────────────────────────────────────


def run(
    preset: str | None = None,
    sparql: str | None = None,
    max_nodes: int = 100,
    rate_limit_per_sec: float = DEFAULT_RATE_LIMIT_PER_SEC,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Run a Wikidata SPARQL query (preset or arbitrary) and yield knowledge nodes.

    Exactly one of `preset` or `sparql` must be supplied.
    """
    if max_nodes > ABSOLUTE_NODE_CEILING:
        raise ValueError(f"max_nodes={max_nodes} > ABSOLUTE_NODE_CEILING={ABSOLUTE_NODE_CEILING}")
    if (preset is None) == (sparql is None):
        raise ValueError("supply exactly one of preset / sparql")

    if preset is not None:
        if preset not in PRESETS:
            raise ValueError(f"unknown preset {preset!r}; choices: {sorted(PRESETS)}")
        query = PRESETS[preset] % {"limit": max_nodes}
    else:
        query = sparql

    rate_limiter = RateLimiter(rate_limit_per_sec)
    stats = WalkStats(walker_kind="wikidata")
    stats.extra["preset"] = preset
    stats.extra["sparql_chars"] = len(query)
    start = time.monotonic()

    try:
        bindings = _sparql(query, rate_limiter, use_cache)
    except RuntimeError as e:
        stats.duration_s = time.monotonic() - start
        stats.stopped_reason = "fetch_failed"
        stats.warnings.append(str(e))
        return {"nodes": [], "walk_stats": stats.to_dict()}

    nodes: list[WikidataNode] = []
    seen: set[str] = set()
    for row in bindings:
        if len(nodes) >= max_nodes:
            stats.stopped_reason = "max_nodes"
            break
        item_uri = (row.get("item") or {}).get("value", "")
        qid = _parse_qid(item_uri)
        if not qid.startswith("Q") or qid in seen:
            continue
        seen.add(qid)
        label = (row.get("itemLabel") or {}).get("value", qid)
        description = (row.get("itemDescription") or {}).get("value", "")
        wikipedia_url = (row.get("wikipediaUrl") or {}).get("value", "")
        nodes.append(
            WikidataNode(
                qid=qid,
                label=label,
                description=description,
                wikidata_url=item_uri,
                wikipedia_url=wikipedia_url,
            )
        )
        stats.nodes_emitted += 1

    stats.duration_s = time.monotonic() - start
    return {
        "nodes": [n.to_dict() for n in nodes],
        "walk_stats": stats.to_dict(),
    }


# ─── Self-test / smoke ──────────────────────────────────────────────────────


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    print("[self-test] PRESETS dict structure")
    check("at least 5 presets defined", len(PRESETS) >= 5)
    for name, q in PRESETS.items():
        check(f"preset '{name}' contains SELECT", "SELECT" in q.upper())
        check(f"preset '{name}' contains %(limit)d", "%(limit)d" in q)

    print("[self-test] _parse_qid")
    check("parses standard URI",
          _parse_qid("http://www.wikidata.org/entity/Q42") == "Q42")
    check("empty input yields empty",
          _parse_qid("") == "")

    print("[self-test] run() rejects bad args")
    try:
        run(preset=None, sparql=None)
        check("raises on neither preset nor sparql", False)
    except ValueError:
        check("raises on neither preset nor sparql", True)
    try:
        run(preset="not-a-preset", max_nodes=1)
        check("raises on unknown preset", False)
    except ValueError:
        check("raises on unknown preset", True)

    print(f"\n{'all self-tests passed.' if not failures else f'{len(failures)} failures: {failures}'}")
    return 0 if not failures else 1


def _smoke_test() -> int:
    print("[smoke-test] running preset 'standards' with limit 5")
    result = run(preset="standards", max_nodes=5, rate_limit_per_sec=2.0)
    print(json.dumps(result["walk_stats"], indent=2))
    for n in result["nodes"]:
        print(f"  {n['qid']} — {n['label']}: {n['description'][:80]}")
    return 0 if result["walk_stats"]["nodes_emitted"] > 0 else 1


# ─── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Walk Wikidata via SPARQL.")
    p.add_argument("--preset", choices=sorted(PRESETS.keys()))
    p.add_argument("--sparql", help="Inline SPARQL query (alternative to --preset)")
    p.add_argument("--max-nodes", type=int, default=100)
    p.add_argument("--rate-limit-per-sec", type=float, default=DEFAULT_RATE_LIMIT_PER_SEC)
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--output", default="-")
    p.add_argument("--list-presets", action="store_true")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--smoke-test", action="store_true")
    args = p.parse_args(argv)

    if args.list_presets:
        for k in sorted(PRESETS.keys()):
            print(k)
        return 0
    if args.self_test:
        return _self_test()
    if args.smoke_test:
        return _smoke_test()
    if not args.preset and not args.sparql:
        p.error("--preset or --sparql or --self-test or --smoke-test required")

    result = run(
        preset=args.preset,
        sparql=args.sparql,
        max_nodes=args.max_nodes,
        rate_limit_per_sec=args.rate_limit_per_sec,
        use_cache=not args.no_cache,
    )
    out_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output == "-":
        sys.stdout.write(out_json + "\n")
    else:
        Path(args.output).write_text(out_json, encoding="utf-8")
        sys.stderr.write(f"wrote {len(result['nodes'])} Wikidata nodes to {args.output}\n")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
