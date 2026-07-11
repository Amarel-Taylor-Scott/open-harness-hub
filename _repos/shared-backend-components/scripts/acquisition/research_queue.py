#!/usr/bin/env python3
"""Research-swarm intake → ranked acquisition queue.

This is where the owner manually feeds "areas of improvement" for the swarm to
research/scrape/conform/spider. Append rows to data/research-queue/areas.jsonl
(see that folder's README), then run:

    python3 -m scripts.acquisition.research_queue

It turns each area into a grid Cell, runs the Stage-1 gap SCREEN
(_repos/shared-backend-components/scripts/acquisition/gap_screen.py) to estimate `expected_lift` WITHOUT collecting
anything, feeds that into the cell value function
(_repos/shared-backend-components/scripts/acquisition/cell_priority.py), and prints the ranked queue. High-likelihood
× high-priority cells are what the swarm should collect first; the rest are named
in the address space but not collected (the negative-space discipline).

No LLM proposes areas or cells here — the owner and external signals do.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.acquisition.cell_priority import (
    Cell,
    CellSignals,
    cell_priority,
    sourceable_from_tier,
)
from scripts.acquisition.gap_screen import GapSignals, screen

ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
from scripts._repo_paths import resource as _resource
DEFAULT_QUEUE = _resource("data") / "research-queue" / "areas.jsonl"

DEFAULT_TIER = "unstructured_addressable"  # neutral tier-3 default when an area omits it
DEFAULT_ACQ_COST = 0.5


def process_area(area: dict[str, Any]) -> dict[str, Any]:
    """Score one fed area: screen for gap-likelihood, then priority. Deterministic."""
    cell = Cell(
        jurisdiction=str(area.get("jurisdiction", "XX")),
        industry=str(area.get("industry", area.get("area", "general"))),
        source_type=str(area.get("source_type", "primary_regulator")),
        time_window=str(area.get("time_window", "all")),
        publisher_type=str(area.get("publisher_type", "government_primary")),
        use_case=str(area.get("use_case", "screening")),
    )
    tier = area.get("tier", DEFAULT_TIER)
    sourceable = sourceable_from_tier(tier)
    velocity = float(area.get("regulatory_velocity", 0.0))
    misses = int(area.get("query_misses", 0))

    gap_signals = GapSignals(
        corpus_density_gap=float(area.get("corpus_density_gap", 0.0)),
        source_tier_gap=round(1.0 - sourceable, 3),       # high tier → high gap (single source: tier)
        regulatory_velocity=velocity,
        query_misses=misses,
        confident_hallucination=float(area.get("confident_hallucination", 0.0)),
        cross_model_disagreement=float(area.get("cross_model_disagreement", 0.0)),
        hedge_rate=float(area.get("hedge_rate", 0.0)),
        recency_gap=float(area.get("recency_gap", 0.0)),
    )
    scr = screen(gap_signals)

    cell_signals = CellSignals(
        expected_lift=scr["gap_likelihood"],   # the screen IS the pre-collection lift estimate
        pays=float(area.get("pays", 0.0)),
        sourceable=sourceable,
        volatility=velocity,
        current_coverage=float(area.get("current_coverage", 0.0)),
        acquisition_cost=float(area.get("acquisition_cost", DEFAULT_ACQ_COST)),
        query_misses=misses,
    )
    return {
        "cell_id": cell.cell_id,
        "area": area.get("area", f"{cell.jurisdiction} × {cell.industry}"),
        "jurisdiction": cell.jurisdiction,
        "industry": cell.industry,
        "tier": tier,
        "gap_likelihood": scr["gap_likelihood"],
        "screen_decision": scr["decision"],
        "model_independent_share": scr["model_independent_share"],
        "priority": cell_priority(cell_signals),
        "status": area.get("status", "queued"),
        "why": area.get("why", ""),
        "source_hints": area.get("source_hints", []),
    }


def load_areas(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        value = json.loads(s)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{n}: expected a JSON object per line")
        rows.append(value)
    return rows


def rank(path: Path = DEFAULT_QUEUE) -> list[dict[str, Any]]:
    scored = [process_area(a) for a in load_areas(path)]
    # collect-first order: confirmed gaps by priority, then skipped (named, not collected)
    return sorted(scored, key=lambda r: (r["screen_decision"] == "confirm", r["priority"]), reverse=True)


def _self_test() -> int:
    areas = [
        {"area": "PH AML thresholds & covered persons", "jurisdiction": "PH", "industry": "financial-crime",
         "tier": "unstructured_addressable", "corpus_density_gap": 0.9, "regulatory_velocity": 0.9,
         "query_misses": 6, "confident_hallucination": 0.9, "pays": 0.95, "current_coverage": 0.1},
        {"area": "PH labor advisories & department orders", "jurisdiction": "PH", "industry": "labor",
         "tier": "structured_no_api", "corpus_density_gap": 0.5, "regulatory_velocity": 0.5,
         "query_misses": 1, "confident_hallucination": 0.4, "pays": 0.5, "current_coverage": 0.2},
        {"area": "France corporate-tax basics", "jurisdiction": "FR", "industry": "tax",
         "tier": "clean_api", "corpus_density_gap": 0.05, "regulatory_velocity": 0.1,
         "query_misses": 0, "confident_hallucination": 0.05, "pays": 0.4, "current_coverage": 0.6},
    ]
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "areas.jsonl"
        p.write_text("\n".join(json.dumps(a) for a in areas) + "\n", encoding="utf-8")
        ranked = rank(p)
        assert ranked[0]["industry"] == "financial-crime", ranked
        assert ranked[0]["screen_decision"] == "confirm", ranked
        assert any(r["industry"] == "tax" and r["screen_decision"] == "skip" for r in ranked), ranked
        for r in ranked:
            print(f"  {r['screen_decision']:7} gl={r['gap_likelihood']:.3f} pri={r['priority']:+.2f} "
                  f"mi={r['model_independent_share']:.2f}  {r['area']}")
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Rank fed research areas into an acquisition queue.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--queue", default=str(DEFAULT_QUEUE))
    p.add_argument("--json", action="store_true", help="emit ranked queue as JSON")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    ranked = rank(Path(args.queue))
    if args.json:
        print(json.dumps(ranked, indent=2))
        return 0
    if not ranked:
        print(f"No areas in {args.queue} — append rows (see data/research-queue/README.md).")
        return 0
    print(f"Acquisition queue ({len(ranked)} areas; collect 'confirm' top-down):\n")
    for r in ranked:
        print(f"  {r['screen_decision']:7} gap={r['gap_likelihood']:.3f} priority={r['priority']:+.2f} "
              f"model-indep={r['model_independent_share']:.2f}  {r['area']}  [{r['cell_id']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
