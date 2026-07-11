#!/usr/bin/env python3
"""scripts.primitive_census — measure progress toward the 40-MILLION-primitive goal. Counts every
primitive-bearing pool (the searchable corpus + every staged candidate pool + the combinatorial generators'
computed CAPACITY), categorizes them (governed-searchable vs staged-candidate vs synthetic-seed vs generator-
capacity), sums the realized total, states the GAP to 40M, and names the highest-throughput lever to close it.

Realized primitives are on disk today; generator CAPACITY is what the deterministic minters can produce on
demand (grid 77.4B, persona 9.5M, idea 35.7M) — so the 40M goal is supply-bounded only by minting time, not
by ideas. serves_truth=false (a count is not a promotion).

    python3 scripts/primitive_census.py --self-test
    python3 scripts/primitive_census.py --run
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap ─────────────────────────────────────────────────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
GOAL = 40_000_000

# category: governed_searchable | staged_candidate | synthetic_seed
_FOUNDRY = "data/dev-intel/aidevobserver_edge_foundry"
_POOLS: tuple[tuple[str, str, str], ...] = (
    ("verified_factory_cards", f"{_FOUNDRY}/verified_factory_primitive_cards.jsonl", "governed_searchable"),
    ("primitive_edge_cards", f"{_FOUNDRY}/primitive_edge_cards.jsonl", "governed_searchable"),
    ("minted_gap_candidates", f"{_FOUNDRY}/minted_gap_primitive_candidates.jsonl", "staged_candidate"),
    ("grid_candidates", f"{_FOUNDRY}/grid_primitive_candidates.jsonl", "staged_candidate"),
    ("idea_candidates", f"{_FOUNDRY}/idea_primitive_candidates.jsonl", "staged_candidate"),
    ("persona_candidates", f"{_FOUNDRY}/persona_primitive_candidates.jsonl", "staged_candidate"),
    ("expanded_candidates", f"{_FOUNDRY}/expanded_primitive_candidates.jsonl", "staged_candidate"),
    ("executable_candidates", f"{_FOUNDRY}/executable_primitive_candidates.jsonl", "staged_candidate"),
    ("enriched_candidates", f"{_FOUNDRY}/enriched_primitive_candidates.jsonl", "staged_candidate"),
    ("kaggle_candidates", f"{_FOUNDRY}/kaggle_primitive_candidates.jsonl", "staged_candidate"),
)


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open("rb") as fh:
        for _ in fh:
            n += 1
    return n


def _generator_capacity() -> dict[str, int]:
    """The computed on-demand capacity of the deterministic minters (import-light)."""
    caps: dict[str, int] = {}
    try:
        import scripts.primitive_grid_remixer as g  # noqa: PLC0415
        caps["grid_remixer"] = g.grid_size()
    except Exception:  # noqa: BLE001
        pass
    try:
        import scripts.persona_primitive_explorer as p  # noqa: PLC0415
        caps["persona_explorer"] = p.persona_grid_size()
    except Exception:  # noqa: BLE001
        pass
    try:
        import scripts.mint_idea_primitives as m  # noqa: PLC0415
        caps["idea_minter"] = m.full_product_size()
    except Exception:  # noqa: BLE001
        pass
    return caps


def census(pools: Optional[tuple[tuple[str, str, str], ...]] = None, base: Optional[Path] = None,
           goal: int = GOAL, with_capacity: bool = True) -> dict[str, Any]:
    pools = pools or _POOLS
    base = base or _sbc_boot
    per_pool: dict[str, Any] = {}
    by_category: dict[str, int] = {}
    for name, rel, category in pools:
        n = _count_lines(base / rel)
        per_pool[name] = {"count": n, "category": category}
        by_category[category] = by_category.get(category, 0) + n
    realized = sum(by_category.values())
    caps = _generator_capacity() if with_capacity else {}
    max_cap = max(caps.values()) if caps else 0
    return {
        "record_type": "primitive_census", "goal": goal, "realized_total": realized,
        "gap_to_goal": max(0, goal - realized), "pct_of_goal": round(100 * realized / goal, 2),
        "by_category": by_category, "per_pool": per_pool,
        "generator_capacity": caps,
        "goal_is_supply_bounded_by_minting_time_not_ideas": max_cap >= goal,
        "highest_throughput_lever": max(caps, key=caps.get) if caps else None,
        **BOUNDARY,
    }


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        (base / "a.jsonl").write_text("x\ny\nz\n")           # 3
        (base / "b.jsonl").write_text("1\n2\n")               # 2
        fixture = (("pool_a", "a.jsonl", "governed_searchable"), ("pool_b", "b.jsonl", "staged_candidate"),
                   ("missing", "nope.jsonl", "staged_candidate"))
        rec = census(pools=fixture, base=base, goal=10, with_capacity=False)
        checks.append(("counts lines per pool + sums the realized total", rec["realized_total"] == 5
                       and rec["per_pool"]["pool_a"]["count"] == 3 and rec["per_pool"]["missing"]["count"] == 0))
        checks.append(("categorizes and reports the gap + pct of goal",
                       rec["by_category"]["governed_searchable"] == 3 and rec["gap_to_goal"] == 5
                       and rec["pct_of_goal"] == 50.0))
        checks.append(("deterministic (identical twice)",
                       json.dumps(census(pools=fixture, base=base, goal=10, with_capacity=False), sort_keys=True)
                       == json.dumps(census(pools=fixture, base=base, goal=10, with_capacity=False), sort_keys=True)))
    # capacity: the grid can supply 40M (goal is idea-unbounded)
    real = census(with_capacity=True)
    checks.append(("generator capacity shows the 40M goal is supply-bounded by minting time, not ideas",
                   real["goal_is_supply_bounded_by_minting_time_not_ideas"] is True
                   and real["highest_throughput_lever"] is not None))
    checks.append(("receipts carry the boundary", real["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - primitive_census: counts every pool toward the {GOAL:,} goal, categorizes "
          f"(governed/staged/synthetic), states the gap + the generator capacity that makes the goal "
          f"supply-bounded by minting time, not ideas. serves_truth=false.")
    return 0


def _run() -> int:
    rec = census()
    out = resource("data") / "dev-intel" / "session_emulation" / "primitive_census_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({k: rec[k] for k in ("goal", "realized_total", "gap_to_goal", "pct_of_goal",
                                          "by_category", "generator_capacity", "highest_throughput_lever")},
                     indent=2, sort_keys=True))
    print(f"\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
