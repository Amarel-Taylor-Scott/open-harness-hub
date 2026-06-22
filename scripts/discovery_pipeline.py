#!/usr/bin/env python3
"""discovery_pipeline — scrape GitHub + (governed) Facebook for new AI tools/repos -> ideas -> candidate tools/plugins/capabilities.

Composes: the KEY HOLDER (BYO keys, src/teleon/runtime/key_holder), source_search (GitHub), the external-API registry
(Facebook via RapidAPI), and discover_tools.build_candidates (license-classify + dedupe vs our registries). Each hit is
classified to a plane + ideated into TOOL / PLUGIN / CAPABILITY candidates, written to a candidate feed (discovery≠trust;
candidate-only; promotion boundary). Social sources are PUBLIC-only + ToS-honoring + honest-unavailable without a held key.
Dev-plane script (imports product; never the reverse).

  python3 scripts/discovery_pipeline.py "ocr" "reranker" "pdf table extraction"
  python3 scripts/discovery_pipeline.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.discover_tools import build_candidates, existing_ids
from src.teleon.research.source_search import SourceSearchUnavailable, ToolHit, discover
from src.teleon.runtime.key_holder import HOLDER

REPO = Path(__file__).resolve().parents[1]
FEED = REPO / "data" / "dev-intel" / "discovered_pipeline.jsonl"

#: deterministic hint: keyword in a repo/tool description -> the tool-plane it likely serves (first match wins)
_PLANE_HINTS = [
    ("ocr", "ocr"), ("rerank", "reranker"), ("embedding", "embedding"), ("vector", "vector_store"),
    ("speech", "asr"), ("transcri", "asr"), ("text-to-speech", "tts"), ("translat", "mt"),
    ("contradict", "stance_nli"), ("entailment", "stance_nli"), ("nli", "stance_nli"),
    ("fuzzy", "fuzzy_matching"), ("dedupe", "fuzzy_matching"), ("record linkage", "fuzzy_matching"),
    ("classif", "classical_ml"), ("solver", "constraint_solver"), ("constraint", "constraint_solver"),
    ("scrap", "search"), ("crawl", "browser"), ("browser", "browser"), ("playwright", "browser"), ("selenium", "browser"),
    ("pdf", "data_extraction"), ("table", "data_extraction"), ("docx", "data_extraction"), ("parse", "parsing_grammar"),
    ("address", "field_parsing"), ("phone", "field_parsing"), ("date", "field_parsing"),
    ("enrich", "entity_enrichment"), ("ner", "ner"), ("entit", "ner"), ("diff", "diff_compare"),
    ("template", "templating"), ("workflow", "workflow_orchestration"), ("rule", "rules_engine"),
    ("vision", "vision"), ("detect", "vision"), ("image", "image_gen"), ("lint", "static_analysis"),
]


def classify_plane(text: str) -> str | None:
    t = (text or "").lower()
    return next((pl for kw, pl in _PLANE_HINTS if kw in t), None)


def _thin_planes(target: int = 12) -> set[str]:
    from collections import Counter
    per = Counter(t["plane"] for t in json.loads((REPO / "architecture" / "tool_registry.json").read_text())["tools"])
    laddered = {l.get("plane") for l in json.loads((REPO / "architecture" / "capability_ladders.json").read_text())["ladders"]}
    planes = {p["plane"] for p in json.loads((REPO / "architecture" / "tool_planes.json").read_text())["planes"]}
    return {p for p in planes if per.get(p, 0) < target or p not in laddered}


def ideate(cand: dict, thin: set[str]) -> dict:
    """Turn a governed candidate into idea kinds + a rationale (what it could become in our registries)."""
    plane = cand.get("plane")
    kinds = []
    if plane and cand.get("vendorable"):
        kinds.append("tool")                                   # a vendorable component for a real plane
    if cand.get("source") in ("github", "pypi"):
        kinds.append("plugin")                                 # an integratable add-on behind a port
    if plane in thin:
        kinds.append("capability")                             # could seed/strengthen a thin plane or a missing ladder
    why = []
    if "tool" in kinds: why.append(f"vendorable {cand.get('license')} component for the {plane} plane")
    if "capability" in kinds: why.append(f"{plane} is under-covered — could seed a ladder/plane")
    if not cand.get("vendorable"): why.append(f"technique-only ({cand.get('license_class')}) — study/service-lane, don't vendor")
    return {**cand, "idea_kinds": kinds or ["watch"], "idea_rationale": "; ".join(why) or "candidate"}


def discover_sources(query: str, *, limit: int = 8, env: dict | None = None) -> tuple[list, dict]:
    """GitHub (wired) + Facebook (governed, key-holder-gated). Returns (hits, per-source status). Honest, never fabricates."""
    hits, status = [], {}
    try:
        gh = discover(query, source="github", limit=limit)
        hits += gh; status["github"] = f"{len(gh)} hits"
    except SourceSearchUnavailable as e:
        status["github"] = f"unavailable: {e}"
    # Facebook: governed external API, gated by a HELD RapidAPI key (BYO). No key -> honest 'needs RAPIDAPI_KEY'.
    if HOLDER.resolve("rapidapi", env):
        status["facebook"] = "rapidapi key held; FB connector is BYO-wired by the tenant (public-only, ToS) — not invoked here"
    else:
        status["facebook"] = "unavailable: needs RAPIDAPI_KEY (add it to the key holder to enable governed FB intake)"
    return hits, status


def run(queries: list[str], *, limit: int = 8) -> list[dict]:
    thin, existing, out = _thin_planes(), existing_ids(), []
    for q in queries:
        hits, status = discover_sources(q, limit=limit)
        cands = build_candidates(hits, existing, plane=None)
        for c in cands:
            c["plane"] = classify_plane(c.get("name", "") + " " + c.get("description", ""))
            out.append(ideate(c, thin))
        print(f"  '{q}': github={status.get('github')} | facebook={status.get('facebook')} -> {len(cands)} candidates")
    _write(out)
    return out


def _write(cands: list[dict]) -> int:
    if not cands:
        return 0
    FEED.parent.mkdir(parents=True, exist_ok=True)
    have = {json.loads(l)["id"] for l in FEED.read_text().splitlines()} if FEED.exists() else set()
    new = [c for c in cands if c["id"] not in have]
    with FEED.open("a", encoding="utf-8") as f:
        for c in new:
            f.write(json.dumps(c) + "\n")
    return len(new)


def _self_test() -> int:
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    # key holder: redaction + gating (no values leak; FB needs a held key)
    st = HOLDER.status({})
    ck("key holder status exposes NO secret values", all("value" not in r and "secret" not in r for r in st["services"]))
    ck("github is held keyless (developer needs no key for the cheap tier)", "github" in st["held"])
    ck("rapidapi NOT held without a key (BYO gate)", "rapidapi" not in HOLDER.held({}))
    _, status = discover_sources("ocr", env={})
    ck("facebook honest-unavailable without a held RapidAPI key", "needs RAPIDAPI_KEY" in status["facebook"])
    ck("auth_headers empty when no key held", HOLDER.auth_headers("rapidapi", {}) == {})
    ck("auth_headers shaped when key present (X-RapidAPI-Key)",
       HOLDER.auth_headers("rapidapi", {"RAPIDAPI_KEY": "k"}) == {"X-RapidAPI-Key": "k"})
    # classify + ideate (hermetic, injected hits)
    ck("classify maps a repo desc to a plane", classify_plane("a fast reranker for RAG") == "reranker")
    hits = [ToolHit("github", "acme/coolrerank", "u", "a fast reranker library", "MIT", 100),
            ToolHit("github", "acme/agplthing", "u", "ocr engine", "AGPL-3.0", 50)]
    cands = build_candidates(hits, {"faiss"}, plane=None)
    for c in cands:
        c["plane"] = classify_plane(c["name"] + " " + c["description"])
    ideas = [ideate(c, {"reranker"}) for c in cands]
    rer = next(i for i in ideas if i["id"] == "coolrerank")
    ck("vendorable repo -> TOOL + PLUGIN + CAPABILITY (thin plane) idea", set(rer["idea_kinds"]) >= {"tool", "plugin", "capability"})
    agpl = next(i for i in ideas if i["id"] == "agplthing")
    ck("copyleft repo -> NOT a vendorable tool (technique-only rationale)",
       "tool" not in agpl["idea_kinds"] and "technique-only" in agpl["idea_rationale"])
    ck("candidates stay governed (status=candidate, serves_truth=false)",
       all(c["status"] == "candidate" and c["serves_truth"] is False for c in cands))
    print("\n" + ("PASS - discovery_pipeline: key-holder gated (redacted, BYO), classify->ideate->govern, candidate-only."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    qs = [a for a in sys.argv[1:] if not a.startswith("-")] or ["ocr", "reranker"]
    cands = run(qs)
    print(f"\n{len(cands)} candidates -> {FEED.relative_to(REPO)} (candidate-only; promote via the boundary, discovery≠trust)")
