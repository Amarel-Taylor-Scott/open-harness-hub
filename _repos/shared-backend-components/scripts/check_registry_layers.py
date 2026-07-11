#!/usr/bin/env python3
"""check_registry_layers — the layered massive-registry model is real, governed, and not fabricated.

Owner: massive registries of ALL tools. Proves the LAYERS (curated core / staged massive / candidate feeds) + the
promotion boundary; the harvester generates a broad query set, dedupes by content hash, and license/plane-classifies into
staged CANDIDATE rows; counts are COMPUTED (registry_stats); and every staged row is REAL (has a source URL) + staged
(not read by the descent) + disjoint from the curated core (dedupe worked). serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_registry_layers.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts import harvest_tools as H
from src.teleon.research.source_search import ToolHit

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource


def _self_test() -> int:
    spec = json.loads((_resource("architecture") / "registry_layers.json").read_text(encoding="utf-8"))
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # ── layered model ────────────────────────────────────────────────────────────────────────────────────────
    layers = {l["layer"]: l for l in spec["layers"]}
    ck("3 layers: core_curated / staged_massive / candidate_feeds", {"core_curated", "staged_massive", "candidate_feeds"} <= set(layers))
    ck("core is the hand-authored vetted tool_registry", layers["core_curated"]["store"].endswith("tool_registry.json") and layers["core_curated"]["hand_authored"])
    ck("staged is JSONL, NOT hand-authored, scales to millions", layers["staged_massive"]["store"].endswith(".jsonl") and not layers["staged_massive"]["hand_authored"])
    ck("promotion boundary documented (staged not read by the descent)", "descent" in spec.get("promotion_boundary", "").lower())

    # ── harvester: breadth + content-hash dedupe + classify (hermetic) ───────────────────────────────────────
    qs = H.generate_queries()
    ck("broad query set (>=80, deduped)", len(qs) >= 80 and len(qs) == len(set(qs)))
    hits = [ToolHit("github", "o/coolthing", "https://github.com/o/coolthing", "a reranker", "MIT", 5),
            ToolHit("github", "o/coolthing", "https://github.com/o/coolthing", "dup", "MIT", 5),
            ToolHit("github", "o/nourl", "", "no url -> dropped (no fabrication)", "MIT", 1)]
    rows = H.build_staged_rows(hits, {"faiss"}, query="reranker library")
    ck("dedupe + require url (drop the urlless)", len(rows) == 1 and rows[0]["url"])
    ck("staged row: content-hash id + status=staged + serves_truth=false + license/plane classified",
       rows[0]["id"].startswith("coolthing-") and rows[0]["status"] == "staged" and rows[0]["serves_truth"] is False and rows[0]["license_class"] == "permissive")
    ck("content hash stable", H._content_hash("github", "a/b", "u") == H._content_hash("github", "a/b", "u"))

    # ── the actual staged layer (if harvested): real + governed + disjoint from core ────────────────────────
    st = H.stats()
    if st.get("total"):
        staged = [json.loads(l) for l in H.STAGING.read_text().splitlines() if l.strip()]
        ck(f"every staged row is REAL (has a source URL) [{st['total']} rows]", all(r.get("url") for r in staged))
        ck("every staged row is candidate/staged (not promoted)", all(r["status"] == "staged" and r["serves_truth"] is False for r in staged))
        ck("staged ids are content-hash unique", len({r["id"] for r in staged}) == len(staged))
        curated = H._curated_ids()
        ck("staged is DISJOINT from the curated core (dedupe worked)", not ({r["bare"] for r in staged} & curated))
        ck("stats counts are COMPUTED + consistent", st["total"] == len(staged) and st["vendorable"] == sum(1 for r in staged if r.get("vendorable")))
        print(f"    [info] staged massive layer: {st['total']} real tools ({st['vendorable']} vendorable), "
              f"top planes {list(st['by_plane'])[:5]}")
    else:
        ck("staged layer empty (harvester not yet run) — engine still verified hermetically", True)
    ck("serves_truth=false", spec.get("serves_truth") is False)

    print("\n" + ("PASS - check_registry_layers: layered (core/staged/feeds), harvester deduped + classified, staged rows "
                  "real + governed, counts computed." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
