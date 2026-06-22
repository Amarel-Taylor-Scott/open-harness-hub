#!/usr/bin/env python3
"""discover_tools — use Teleon's OWN source-search components to find more deterministic tools for the registry.

Dogfoods src.teleon.research.source_search (PyPI + GitHub, the descent's cheap deterministic tier) to surface CANDIDATE
tools, then governs them: classify the license from the single source (src/openharnesshub/licenses), dedupe against the
existing tool_registry, and append to a candidate feed. Discovery is NOT trust — nothing lands in tool_registry here; a
human/verify step promotes (the promotion boundary). serves_truth=false. Dev-plane script (imports the product searcher,
never the reverse).

  python3 scripts/discover_tools.py "reranker" github --plane reranker
  python3 scripts/discover_tools.py --sweep                 # one query per under-target plane
  python3 scripts/discover_tools.py --self-test             # hermetic (no network)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.openharnesshub.licenses import classify_license
from src.teleon.research.source_search import SourceSearchUnavailable, ToolHit, discover

REPO = Path(__file__).resolve().parents[1]
FEED = REPO / "data" / "dev-intel" / "discovered_tools.jsonl"
REGISTRY = REPO / "architecture" / "tool_registry.json"

#: a default sweep: plane -> a good search query (the discovery flywheel can grow this). Planes with weak coverage first.
PLANE_QUERIES = {
    "reranker": "reranker", "fuzzy_matching": "fuzzy string matching", "field_parsing": "address parser",
    "classical_ml": "text classification sklearn", "constraint_solver": "constraint solver", "vision": "barcode decoder",
    "asr": "speech to text", "diff_compare": "json diff", "templating": "code generator from schema",
    "data_extraction": "pdf table extraction", "parsing_grammar": "tree-sitter grammar",
}


def _norm(name: str) -> str:
    """Bare comparable id: owner/repo or dist-name -> snake slug (so a hit is deduped against an existing registry id)."""
    return name.split("/")[-1].strip().lower().replace("-", "_").replace(".", "_").replace(" ", "_")


def existing_ids() -> set[str]:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))["tools"]
    return {t["id"] for t in reg} | {_norm(t["name"]) for t in reg}


def build_candidates(hits: list[ToolHit], existing: set[str], *, plane: str | None = None) -> list[dict]:
    """Pure governance step (testable offline): classify license, drop dupes of the registry, build candidate rows."""
    out, seen = [], set()
    for h in hits:
        bare = _norm(h.name)
        if bare in existing or bare in seen:
            continue
        seen.add(bare)
        cls, vendorable = classify_license(h.license)
        out.append({
            "id": bare, "source": h.source, "name": h.name, "url": h.url, "plane": plane or "?",
            "license": h.license, "license_class": cls, "vendorable": vendorable,
            "popularity": h.popularity, "description": h.description[:200],
            "status": "candidate", "discovered": True, "serves_truth": False,
        })
    return out


def _append_feed(cands: list[dict]) -> int:
    if not cands:
        return 0
    FEED.parent.mkdir(parents=True, exist_ok=True)
    have = set()
    if FEED.exists():
        have = {json.loads(ln)["id"] for ln in FEED.read_text(encoding="utf-8").splitlines() if ln.strip()}
    new = [c for c in cands if c["id"] not in have]
    with FEED.open("a", encoding="utf-8") as f:
        for c in new:
            f.write(json.dumps(c) + "\n")
    return len(new)


def run(query: str, *, source: str = "auto", plane: str | None = None, limit: int = 12) -> list[dict]:
    hits = discover(query, source=source, limit=limit)   # may raise SourceSearchUnavailable (honest)
    cands = build_candidates(hits, existing_ids(), plane=plane)
    added = _append_feed(cands)
    vend = sum(1 for c in cands if c["vendorable"])
    print(f"  '{query}' [{source}] -> {len(hits)} hits, {len(cands)} new candidates ({vend} vendorable), {added} appended")
    for c in cands[:10]:
        flag = "vendorable" if c["vendorable"] else f"technique-only({c['license_class']})"
        print(f"    [{c['source']:6s}] {c['name'][:42]:42s} {str(c['license'])[:16]:16s} {flag}")
    return cands


def _self_test() -> int:
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    # hermetic: synthetic hits exercise classify + dedupe (no network)
    existing = {"rapidfuzz", "ortools"}
    hits = [
        ToolHit("github", "owner/RapidFuzz", "u", "dup of registry", "MIT", 9000),       # dup -> dropped
        ToolHit("github", "acme/coolparse", "u", "new permissive", "Apache-2.0", 120),   # new, vendorable
        ToolHit("github", "acme/copyleftthing", "u", "agpl", "AGPL-3.0", 50),            # new, technique-only
        ToolHit("pypi", "coolparse", "u", "same bare name -> dedup within batch", "MIT"),  # dup of acme/coolparse bare
    ]
    cands = build_candidates(hits, existing, plane="parsing_grammar")
    ck("registry dup dropped (RapidFuzz)", all(c["id"] != "rapidfuzz" for c in cands))
    ck("within-batch dup dropped (coolparse once)", sum(c["id"] == "coolparse" for c in cands) == 1)
    ck("permissive -> vendorable", any(c["id"] == "coolparse" and c["vendorable"] for c in cands))
    ck("AGPL -> technique-only (not vendorable)", any(c["id"] == "copyleftthing" and not c["vendorable"] for c in cands))
    ck("plane carried + candidate/serves_truth governed", all(c["plane"] == "parsing_grammar" and c["status"] == "candidate"
                                                              and c["serves_truth"] is False for c in cands))
    # honest-unavailable contract is real (the dataclass + exception exist)
    ck("ToolHit.key normalizes", ToolHit("github", "A/B", "u").key == "github:a/b")
    print("\n" + ("PASS - discover_tools: governance (classify+dedupe+candidate) verified offline; live search via "
                  "source_search (PyPI/GitHub)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    if "--sweep" in sys.argv:
        total = 0
        for pl, q in PLANE_QUERIES.items():
            try:
                total += len(run(q, source="github", plane=pl, limit=8))
            except SourceSearchUnavailable as e:
                print(f"  {pl}: UNAVAILABLE (honest) — {e}")
        print(f"\nsweep complete: {total} candidates across {len(PLANE_QUERIES)} planes -> {FEED.relative_to(REPO)}")
        raise SystemExit(0)
    q = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "reranker"
    src = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "auto"
    pl = sys.argv[sys.argv.index("--plane") + 1] if "--plane" in sys.argv else None
    try:
        run(q, source=src, plane=pl)
    except SourceSearchUnavailable as e:
        print(f"  UNAVAILABLE (honest): {e}")
        raise SystemExit(0)
