#!/usr/bin/env python3
"""check_capability_ladders — every capability is a cost-ordered, deterministic-first descent ladder (and we cover more).

Owner: "we need ladders for EVERYTHING and every subcomponent." Proves: each ladder is cost-ordered; DETERMINISTIC rungs
come before model rungs (climb cheap->dear, LLM last); every rung's tools/external_apis/planes are real; statuses honest;
ToS/evasion rungs governed; the named capabilities (web_browsing, document_extraction, document_classification,
entity_enrichment, social_media_scraping) are present; and COVERAGE vs the planes is computed + the gap surfaced (the loop
fills it — never a silent claim of completeness). serves_truth=false.

  python3 scripts/check_capability_ladders.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(name):
    return json.loads((REPO / "architecture" / name).read_text(encoding="utf-8"))


def _self_test() -> int:
    lad = _load("capability_ladders.json")
    ladders = lad["ladders"]
    planes = {p["plane"] for p in _load("tool_planes.json")["planes"]}
    ext = {a["id"] for a in _load("external_api_registry.json")["apis"]}
    tools = ({t["id"] for t in _load("tool_registry.json")["tools"]}
             | {p.get("id") for p in _load("ocr_provider_registry.json")["providers"]}
             | {b["id"] for b in _load("web_browsing_stack_registry.json")["browsers"]}
             | {c["id"] for c in _load("web_browsing_stack_registry.json")["driving_components"]})
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"ladders for many capabilities ({len(ladders)})", len(ladders) >= 10)
    named = {"web_browsing", "document_extraction", "document_classification", "entity_enrichment", "social_media_scraping"}
    have = {l["capability"] for l in ladders}
    ck("the owner-named capabilities all have a ladder", named <= have, str(named - have))

    for l in ladders:
        cap, rungs = l["capability"], l["rungs"]
        ranks = [r["cost_rank"] for r in rungs]
        ck(f"[{cap}] >=2 rungs (it climbs)", len(rungs) >= 2)
        ck(f"[{cap}] cost-ordered (non-decreasing)", ranks == sorted(ranks))
        # deterministic-first: ordered by cost, deterministic flags are non-increasing (det rungs precede model rungs)
        det = [bool(r["deterministic"]) for r in sorted(rungs, key=lambda r: r["cost_rank"])]
        ck(f"[{cap}] deterministic rungs precede model rungs (LLM is last resort)", det == sorted(det, reverse=True))
        bad_tool = sorted({t for r in rungs for t in r.get("tools", []) if t not in tools})
        ck(f"[{cap}] rung tools are real", not bad_tool, str(bad_tool))
        bad_ext = sorted({a for r in rungs for a in r.get("external_apis", []) if a not in ext})
        ck(f"[{cap}] external-API rungs are real (external_api_registry)", not bad_ext, str(bad_ext))
        bad_pl = sorted({pl for r in rungs for pl in r.get("planes", []) if pl not in planes})
        ck(f"[{cap}] rung planes are declared", not bad_pl, str(bad_pl))
        ck(f"[{cap}] statuses honest", all(r["status"] in ("wired", "cataloged", "candidate") for r in rungs))
    # ToS-sensitive ladder is governed
    soc = next((l for l in ladders if l["capability"] == "social_media_scraping"), {})
    ck("social_media_scraping ladder is governed + has an honest-stop rung",
       bool(soc.get("governance")) and any(r["tier"] == "honest_stop" for r in soc.get("rungs", [])))
    ck("serves_truth=false", lad.get("serves_truth") is False)

    # COVERAGE (computed, not claimed): which planes still lack a ladder -> the loop fills them
    covered = {l.get("plane") for l in ladders}
    missing = sorted(planes - covered)
    print(f"\n  ladder coverage: {len(covered & planes)}/{len(planes)} planes have a ladder; "
          f"{len(missing)} to add next (e.g. {', '.join(missing[:8])})")

    print("\n" + (f"PASS - check_capability_ladders: {len(ladders)} capability ladders, cost-ordered + deterministic-first, "
                  f"real rungs; {len(missing)} planes still need one (surfaced, not hidden)."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
