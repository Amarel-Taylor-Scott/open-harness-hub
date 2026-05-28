#!/usr/bin/env python3
"""Capability-gap scout — continuously find areas where an LLM needs a knowledge pack.

This is the standing, single-process version of the parallel discovery fleet:
given a domain cluster, it asks a model route (Gemma via Ollama by default) to
propose KNOWLEDGE-PACK opportunities that clear the capability-lift bar, dedups
them against already-discovered candidates and the live catalog, scores each by
a deterministic priority heuristic, and appends survivors to a dated JSONL plus
a review-ticket file. Run it on a loop/cron for 24/7/365 discovery; the heavy
parallel burst (multiple sub-agents) complements it for breadth.

Provider-neutral: uses scripts.model_routes (local now, cloud later by env var).
Degrades gracefully with no model (emits nothing, exits 0) — never fabricates.

Usage:
  python3 -m scripts.factory.capability_gap_scout --cluster "finance/AML" --n 12
  python3 -m scripts.factory.capability_gap_scout --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from scripts.model_routes import resolve_route

ROOT = Path(__file__).resolve().parents[2]
GAPS_DIR = ROOT / "data" / "capability-gaps"
KP_DIR = ROOT / "catalog" / "knowledge-packs"
RETRIEVAL_TYPES = {"rag_vector", "regex", "keyword", "exact_id", "classifier", "graph"}
# Retrieval types that tend to maximize verifiability / not_solved_by_out_of_box_llms.
HIGH_LIFT_RETRIEVAL = {"exact_id", "graph", "regex"}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:64] or "gap"


def existing_pack_names() -> set[str]:
    """Already-discovered candidates + live catalog knowledge-pack slugs (dedup)."""
    names: set[str] = set()
    for f in GAPS_DIR.glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                names.add(_slug(json.loads(line).get("pack_name", "")))
            except json.JSONDecodeError:
                continue
    for f in KP_DIR.rglob("*.yaml"):
        names.add(_slug(f.stem))
    names.discard("")
    return names


def priority(candidate: dict) -> float:
    """Deterministic capability-lift heuristic in [0,1] — favors verifiable,
    identifier/graph-keyed, well-sourced gaps with a concrete failure mode."""
    score = 0.0
    if candidate.get("public_source"):
        score += 0.30
    if candidate.get("retrieval_type") in HIGH_LIFT_RETRIEVAL:
        score += 0.25
    elif candidate.get("retrieval_type") in RETRIEVAL_TYPES:
        score += 0.12
    gap = str(candidate.get("gap", ""))
    if len(gap) >= 60:
        score += 0.20
    if re.search(r"\b(exact|code|id|threshold|version|date|number|table|jurisdiction)\b", gap, re.I):
        score += 0.15
    if str(candidate.get("lift_rationale", "")):
        score += 0.10
    return round(min(1.0, score), 3)


def _parse_array(raw: str) -> list[dict]:
    if not raw:
        return []
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
        return [d for d in data if isinstance(d, dict)]
    except json.JSONDecodeError:
        return []


def propose(cluster: str, n: int, route) -> list[dict]:
    if not route.health():
        return []
    system = (
        "You are the Open Harness Hub capability-gap scout. Propose KNOWLEDGE-PACK "
        "opportunities: domains where an LLM CANNOT answer reliably alone (long-tail / "
        "fast-changing / exact-identifier / jurisdiction-specific facts) and a grounded "
        "pack would fix it. AVOID anything a frontier model already does well zero-shot. "
        f"Return ONLY a JSON array of {n} objects, each: "
        '{"domain","pack_name","gap","public_source","retrieval_type"(rag_vector|regex|'
        'keyword|exact_id|classifier|graph),"lift_rationale","example_query"}.'
    )
    return _parse_array(route.complete(system, f"Domain cluster: {cluster}", max_tokens=4096))


def scout(cluster: str, n: int = 12, route=None) -> dict:
    route = route or resolve_route()
    seen = existing_pack_names()
    fresh = []
    for c in propose(cluster, n, route):
        slug = _slug(c.get("pack_name", ""))
        if not slug or slug in seen or c.get("retrieval_type") not in RETRIEVAL_TYPES:
            continue
        seen.add(slug)
        c["pack_name"] = slug
        c["cluster"] = cluster
        c["priority"] = priority(c)
        c["discovered_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        fresh.append(c)
    fresh.sort(key=lambda c: c["priority"], reverse=True)
    if fresh:
        GAPS_DIR.mkdir(parents=True, exist_ok=True)
        out = GAPS_DIR / f"scouted-{time.strftime('%Y-%m-%d')}.jsonl"
        with out.open("a", encoding="utf-8") as fh:
            for c in fresh:
                fh.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    return {"cluster": cluster, "proposed": len(fresh),
            "high_priority": sum(1 for c in fresh if c["priority"] >= 0.7),
            "candidates": fresh}


def _self_test() -> int:
    # Offline: no model route → no fabrication, clean exit. Scoring is deterministic.
    names = existing_pack_names()
    assert "fda-510k-predicate-device-clearances" in names, "did not load existing candidates"
    hi = priority({"public_source": "X", "retrieval_type": "exact_id",
                   "gap": "exact code thresholds that change by jurisdiction and date " * 2,
                   "lift_rationale": "y"})
    lo = priority({"retrieval_type": "rag_vector", "gap": "short"})
    assert hi >= 0.8 and lo <= 0.5, (hi, lo)
    res = scout("test/offline-cluster", n=5, route=resolve_route())  # likely no LLM here
    print(json.dumps({"ok": True, "existing_known": len(names),
                      "priority_hi": hi, "priority_lo": lo,
                      "offline_proposed": res["proposed"]}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Continuously scout LLM capability gaps -> knowledge-pack candidates.")
    p.add_argument("--cluster", help="Domain cluster to scout, e.g. 'finance/AML' or 'aerospace'.")
    p.add_argument("--n", type=int, default=12)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.cluster:
        p.error("--cluster is required (or use --self-test)")
    print(json.dumps(scout(args.cluster, args.n), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
