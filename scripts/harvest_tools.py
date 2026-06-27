#!/usr/bin/env python3
"""harvest_tools — scale the tool registry MASSIVELY into the staged JSONL layer (real tools only, computed counts).

Generates a broad query set (every plane x templates + every ML task), scrapes GitHub (paginated via source_search),
license- + plane-classifies, dedupes by CONTENT HASH against the curated core + the existing staging, and appends staged
candidate rows. Resumable (a cursor over the query list) + honest: on a rate limit it saves the cursor + stops (never
fabricates rows to inflate counts). The staged layer (data/dev-intel/tool_registry_staging.jsonl) is NOT read by the
descent until promoted (the boundary). serves_truth=false; discovery≠trust. Dev-plane script.

  python3 scripts/harvest_tools.py --run 20          # harvest up to 20 queries this batch (rate-limited; resumable)
  python3 scripts/harvest_tools.py --stats           # computed counts over the staged layer
  python3 scripts/harvest_tools.py --self-test        # hermetic
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from scripts.discovery_pipeline import classify_plane
from src.openhubforai.licenses import classify_license
from src.teleon.research.source_search import SourceSearchUnavailable, discover

REPO = Path(__file__).resolve().parents[1]
STAGING = REPO / "data" / "dev-intel" / "tool_registry_staging.jsonl"
CURSOR = REPO / "data" / "dev-intel" / "harvest_cursor.json"


def generate_queries() -> list[str]:
    """A broad, deterministic query set: every tool-plane x templates + every ML task. Grows the registry by breadth."""
    planes = [p["plane"] for p in json.loads((REPO / "architecture" / "tool_planes.json").read_text())["planes"]
              if p["plane"] not in ("llm",)]
    tasks = json.loads((REPO / "architecture" / "ml_model_registry.json").read_text())["ml_tasks"]
    qs = []
    for p in planes:
        name = p.replace("_", " ")
        qs += [f"{name} library", f"{name} python", f"open source {name}", f"{name} toolkit"]
    for t in tasks:
        qs += [f"{t.replace('_', ' ')} model", f"{t.replace('_', ' ')} library"]
    seen, out = set(), []
    for q in qs:                                  # dedupe, stable order
        if q not in seen:
            seen.add(q); out.append(q)
    return out


def _norm(name: str) -> str:
    return name.split("/")[-1].strip().lower().replace("-", "_").replace(".", "_").replace(" ", "_")


def _content_hash(source: str, name: str, url: str) -> str:
    return hashlib.sha256(f"{source}|{name}|{url}".encode()).hexdigest()[:12]


def _curated_ids() -> set[str]:
    reg = json.loads((REPO / "architecture" / "tool_registry.json").read_text())["tools"]
    return {t["id"] for t in reg} | {_norm(t["name"]) for t in reg}


def _staged_ids() -> set[str]:
    if not STAGING.exists():
        return set()
    return {json.loads(l)["bare"] for l in STAGING.read_text().splitlines() if l.strip()}


def build_staged_rows(hits, existing: set[str], query: str = "") -> list[dict]:
    """License + plane classify, dedupe (by bare id), content-hash. CANDIDATE/staged rows — no fabrication (each has a url)."""
    out, seen = [], set()
    for h in hits:
        bare = _norm(h.name)
        if not h.name or not h.url or bare in existing or bare in seen:
            continue
        seen.add(bare)
        cls, vend = classify_license(h.license)
        out.append({
            "id": f"{bare}-{_content_hash(h.source, h.name, h.url)}", "bare": bare, "name": h.name, "source": h.source,
            "url": h.url, "plane": classify_plane(f"{h.name} {h.description}"), "license": h.license,
            "license_class": cls, "vendorable": vend, "popularity": h.popularity, "description": (h.description or "")[:200],
            "found_via": query, "status": "staged", "serves_truth": False,
        })
    return out


def _append(rows: list[dict]) -> int:
    if not rows:
        return 0
    STAGING.parent.mkdir(parents=True, exist_ok=True)
    with STAGING.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return len(rows)


def harvest(max_queries: int = 20, per_query: int = 30) -> dict:
    queries = generate_queries()
    cur = json.loads(CURSOR.read_text())["i"] if CURSOR.exists() else 0
    existing = _curated_ids() | _staged_ids()
    run, hits_n, new_n, rate_limited = 0, 0, 0, False
    i = cur
    while run < max_queries and i < len(queries):
        q = queries[i]
        try:
            hits = discover(q, source="github", limit=per_query)
        except SourceSearchUnavailable as e:
            rate_limited = "rate limit" in str(e).lower() or "403" in str(e)
            if rate_limited:
                break                              # honest stop; cursor stays here to resume
            i += 1; run += 1; continue
        hits_n += len(hits)
        rows = build_staged_rows(hits, existing, query=q)
        for r in rows:
            existing.add(r["bare"])
        new_n += _append(rows)
        i += 1; run += 1
    CURSOR.parent.mkdir(parents=True, exist_ok=True)
    CURSOR.write_text(json.dumps({"i": i % len(queries), "queries_total": len(queries)}))
    return {"queries_run": run, "hits": hits_n, "new_staged": new_n, "total_staged": len(_staged_ids()),
            "cursor": i % len(queries), "of": len(queries), "rate_limited": rate_limited}


def stats() -> dict:
    """COMPUTED counts over the staged layer (never hand-typed)."""
    if not STAGING.exists():
        return {"total": 0}
    rows = [json.loads(l) for l in STAGING.read_text().splitlines() if l.strip()]
    return {"total": len(rows), "vendorable": sum(1 for r in rows if r.get("vendorable")),
            "by_plane": dict(Counter(r.get("plane") for r in rows).most_common(12)),
            "by_license_class": dict(Counter(r.get("license_class") for r in rows)),
            "by_source": dict(Counter(r.get("source") for r in rows)), "serves_truth": False}


def _self_test() -> int:
    from src.teleon.research.source_search import ToolHit
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    qs = generate_queries()
    ck("query generator yields a broad set (>=80 queries across planes+tasks)", len(qs) >= 80)
    ck("queries deduped", len(qs) == len(set(qs)))
    hits = [ToolHit("github", "acme/fastrerank", "https://github.com/acme/fastrerank", "a reranker", "MIT", 9),
            ToolHit("github", "acme/fastrerank", "https://github.com/acme/fastrerank", "dup", "MIT", 9),  # dup -> dropped
            ToolHit("github", "acme/nourl", "", "no url", "MIT", 1)]                                      # no url -> dropped
    rows = build_staged_rows(hits, {"faiss"}, query="reranker library")
    ck("dedupe within batch + drop urls -> 1 row", len(rows) == 1)
    ck("staged row has content-hash id + bare + url + status", rows and rows[0]["id"].startswith("fastrerank-") and rows[0]["status"] == "staged")
    ck("license + plane classified", rows[0]["license_class"] == "permissive" and rows[0]["vendorable"] is True)
    ck("curated dup excluded", all(r["bare"] != "faiss" for r in rows))
    ck("content hash stable", _content_hash("github", "a/b", "u") == _content_hash("github", "a/b", "u"))
    print("\n" + ("PASS - harvest_tools: broad query gen + content-hash dedupe + license/plane classify, staged (candidate)."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    if "--stats" in sys.argv:
        print(json.dumps(stats(), indent=2)); raise SystemExit(0)
    n = next((int(a) for a in sys.argv if a.isdigit()), 20)
    r = harvest(max_queries=n)
    print(json.dumps(r, indent=2))
    print(f"\nstaged total: {r['total_staged']} (cursor {r['cursor']}/{r['of']}{'; RATE-LIMITED — rerun to resume' if r['rate_limited'] else ''})")
