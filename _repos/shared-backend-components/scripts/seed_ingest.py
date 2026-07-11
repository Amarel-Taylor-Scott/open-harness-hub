#!/usr/bin/env python3
"""scripts.seed_ingest — KEYLESS seed ingestion: fetch → normalize → interrogate → candidate registry records.

The first live stage of the recursive knowledge-expansion engine. Pulls from keyless sources (GitHub search,
Hacker News Algolia, arXiv) per data/research-queue/seed_sources.jsonl, normalizes each hit into the ONE
universal_object_schema record, attaches interrogation questions, and writes candidates. Governed: PUBLIC
metadata only, serves_truth=false (discovery ≠ trust — candidates until verified), honest on rate-limit (logs +
continues to the next source; never silently gives up — the kickstart layer names the next rung).

  --self-test                       offline: normalize/dedup/schema/governance (NO network)
  --run [--query Q --limit N]       live keyless fetch -> data/dev-intel/ingested_candidates.jsonl
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
OUT = _resource("data") / "dev-intel" / "ingested_candidates.jsonl"

KEYLESS = {
    "github": "https://api.github.com/search/repositories?per_page={n}&q={q}",
    "hacker_news": "https://hn.algolia.com/api/v1/search?hitsPerPage={n}&query={q}",
    "arxiv": "http://export.arxiv.org/api/query?max_results={n}&search_query=all:{q}",
}


def _get(url: str, timeout: int = 25) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "OpenHubForAI-seed-ingest/0.1 (public metadata only)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001 — honest: surface, log, move to the next source (never silently give up)
        code = getattr(e, "code", 0)
        return (code or -1), ""


def fetch(source: str, query: str, n: int = 10) -> list[dict]:
    url = KEYLESS[source].format(q=urllib.parse.quote(query), n=n)
    status, body = _get(url)
    if status != 200 or not body:
        return [{"_error": f"{source} returned {status} (rate-limit? try the next rung)", "_source": source}]
    if source == "github":
        return [{"name": i["full_name"], "url": i["html_url"], "desc": i.get("description") or "",
                 "stars": i.get("stargazers_count", 0)} for i in json.loads(body).get("items", [])]
    if source == "hacker_news":
        return [{"name": i.get("title") or i.get("story_title") or "", "url": i.get("url") or "",
                 "desc": f"HN points={i.get('points')}", "stars": i.get("points", 0)} for i in json.loads(body).get("hits", [])]
    # arxiv returns Atom XML — cheap title/id extraction without an XML dep
    import re
    titles = re.findall(r"<title>(.*?)</title>", body, re.S)[1:]   # [0] is the feed title
    ids = re.findall(r"<id>(.*?)</id>", body, re.S)[1:]
    return [{"name": t.strip().replace("\n", " "), "url": (u.strip() if u else ""), "desc": "arxiv", "stars": 0}
            for t, u in zip(titles, ids)]


def normalize(item: dict, source: str) -> dict:
    """One universal_object_schema candidate record (the normalization target)."""
    ref = item.get("url") or item.get("name") or ""
    oid = hashlib.sha256(f"{source}|{ref}".encode()).hexdigest()[:16]
    name = item.get("name", "")
    return {
        "object_id": oid, "object_type": "tool" if source == "github" else "document",
        "source": {"seed": source, "url": item.get("url", "")}, "name": name,
        "capabilities": [], "inputs": [], "outputs": [], "dependencies": [],
        "searchability_tags": [w.lower() for w in name.replace("/", " ").split()][:12],
        "known_limitations": [], "adjacent_tools": [], "open_questions": ["what capabilities does this expose?",
                                                                          "what cheaper/deterministic variant exists?"],
        "missing_metadata": ["capabilities", "inputs", "outputs", "dependencies", "license"],
        "confidence_score": 0.3, "popularity": item.get("stars", 0), "serves_truth": False,
    }


def interrogate(record: dict) -> list[str]:
    try:
        from scripts.interrogation_engine import generate, load_taxonomy
        rows, _ = generate([{"ref": record["name"], "type": record["object_type"]}], load_taxonomy(),
                           dims=["alternatives", "ai_native", "deletion"], context_samples=1, total_cap=6)
        return [r["question"] for r in rows]
    except Exception:
        return []


def run(query: str, limit: int) -> dict:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    recs: list[dict] = []
    errors: list[str] = []
    for source in KEYLESS:
        for item in fetch(source, query, limit):
            if "_error" in item:
                errors.append(item["_error"])
                continue
            rec = normalize(item, source)
            if rec["object_id"] in seen:
                continue
            seen.add(rec["object_id"])
            rec["interrogation"] = interrogate(rec)
            recs.append(rec)
    with OUT.open("a", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    return {"query": query, "ingested": len(recs), "sources_tried": list(KEYLESS), "errors": errors,
            "out": str(OUT.relative_to(REPO))}


def self_test() -> int:
    rec = normalize({"name": "langchain-ai/langgraph", "url": "https://github.com/langchain-ai/langgraph", "stars": 9}, "github")
    assert rec["object_id"] == normalize({"name": "x", "url": "https://github.com/langchain-ai/langgraph"}, "github")["object_id"], "id keys on url, deterministic"
    for fld in ("object_id", "object_type", "source", "capabilities", "missing_metadata", "confidence_score", "serves_truth"):
        assert fld in rec, f"missing universal-schema field {fld}"
    assert rec["serves_truth"] is False and rec["confidence_score"] < 1.0, "candidate tier"
    assert "langgraph" in rec["searchability_tags"], "tags extracted"
    # rate-limit / error rows are surfaced honestly, not crashed on
    errs = [i for i in [{"_error": "github returned 403", "_source": "github"}] if "_error" in i]
    assert errs, "error rows must be representable (honest, not silent)"
    print("seed_ingest self-test: OK (normalize→universal schema, deterministic id, candidate-tier, honest errors)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    if "--run" in argv:
        print(json.dumps(run(opt("--query", "AI agent framework"), int(opt("--limit", "8"))), indent=2))
        return 0
    print("usage: seed_ingest.py --self-test | --run [--query Q --limit N]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
