#!/usr/bin/env python3
"""robust_lane_router — the scoreboard: what fraction of capability needs route to a ROBUST lane (gap 2.2).

The reconciled savings ledger says only two reuse lanes are model-independent and dependable: DETERMINISTIC
COMPOSITION (chain verified primitives on exact edges — 0 tokens, the model never sees the code) and
PACKAGE IMPORT (a single verified primitive covers the need). Reuse-via-prompt is prompt/model-dependent and
does NOT reliably save tokens. "Route more work onto the robust lanes" has been an UNQUANTIFIED claim — and
this repo's honest-ledger law forbids unquantified savings claims. This module makes it a number.

For each NEED (a target capability, named by the edge it must produce) it classifies the strongest lane:

    deterministic_compose  — a multi-step exact-edge chain reaches the need (>=2 hops). ROBUST, 0-token.
    package_import         — a single verified primitive produces the need from a source entry. ROBUST.
    partial_compose        — a producer exists but its own input is unmet (a chain with one gap). SEMI.
    generate_tail          — nothing produces the need; the model must generate it. NON-ROBUST.

`robust_lane_coverage(needs, cards)` aggregates the per-lane fractions — the honest scoreboard that says how
much of a workload the robust lanes carry TODAY, and that scores every other gap fix (a better aligner or more
bridges shows up here as a rising robust fraction). Pure composition over the shared `producer_edge_index`
(reuse-first — no new matcher/composer); deterministic; candidate-only.

    PYTHONPATH=. python3 scripts/robust_lane_router.py --self-test
    PYTHONPATH=. python3 scripts/robust_lane_router.py --coverage
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: lanes in strength order (strongest robust first). ROBUST_LANES are the model-independent ones.
LANES = ("deterministic_compose", "package_import", "partial_compose", "generate_tail")
ROBUST_LANES = frozenset({"deterministic_compose", "package_import"})
_MAX_CHAIN_DEPTH = 8   # bound the backward walk (a network is never deeper in practice)


def _reachable_depth(edge: str, index: dict[str, Any], seen: frozenset[str], depth: int) -> Optional[int]:
    """Longest EXACT backward chain ending in a producer of `edge`: 0 = produced from a source entry (its
    producer's input is unproduced), >=1 = each hop's input is itself produced. None = no producer at all.
    `seen` breaks cycles; depth bounds the walk."""
    producers = index["producers"].get(edge, [])
    if not producers or depth >= _MAX_CHAIN_DEPTH:
        return None if not producers else 0
    best: Optional[int] = None
    for cid in producers:
        card = index["by_id"].get(cid, {})
        in_edge = card.get("input_edge")
        if not in_edge or in_edge in seen:          # source-dependent entry (or a cycle) — chain ends here
            best = max(best or 0, 0)
            continue
        upstream = _reachable_depth(in_edge, index, seen | {edge}, depth + 1)
        best = max(best if best is not None else 0, (upstream + 1) if upstream is not None else 0)
    return best


def classify_need(need_edge: str, index: dict[str, Any]) -> dict[str, Any]:
    """Classify the strongest reuse lane that serves `need_edge`, with evidence. Uses only the shared index."""
    producers = index["producers"].get(need_edge, [])
    if not producers:
        return {"need": need_edge, "lane": "generate_tail", "robust": False, "n_producers": 0,
                "reason": "no primitive produces this edge — the model must generate it",
                "candidate": True, "serves_truth": False}
    # is any producer reachable through a >=1-hop exact chain (its input is itself produced)?
    depth = _reachable_depth(need_edge, index, frozenset(), 0)
    # is there ALSO a producer whose input is a source entry (fully met from a source)?
    has_source_entry = any(not index["by_id"].get(cid, {}).get("input_edge")
                           or not index["producers"].get(index["by_id"][cid].get("input_edge"), [])
                           for cid in producers)
    if depth and depth >= 1:
        lane = "deterministic_compose"
        reason = f"an exact-edge chain of depth {depth + 1} reaches this need (0-token composition)"
    elif has_source_entry:
        lane = "package_import"
        reason = "a single verified primitive produces this need from a source entry (import it)"
    else:
        # producers exist but every producer's input is itself unproduced -> a chain with a gap
        lane = "partial_compose"
        reason = "a producer exists but its input edge is unmet — a route with one gap (needs a bridge/tail)"
    return {"need": need_edge, "lane": lane, "robust": lane in ROBUST_LANES, "n_producers": len(producers),
            "chain_depth": (depth + 1) if depth else 1, "reason": reason,
            "candidate": True, "serves_truth": False}


def robust_lane_coverage(needs: list[str], cards: list[dict[str, Any]]) -> dict[str, Any]:
    """The scoreboard: classify every need, aggregate per-lane counts + the robust fraction. Deterministic."""
    from scripts.producer_edge_index import build_producer_edge_index  # noqa: PLC0415  the ONE index
    index = build_producer_edge_index(cards)
    verdicts = [classify_need(n, index) for n in needs]
    counts = {lane: sum(1 for v in verdicts if v["lane"] == lane) for lane in LANES}
    total = len(verdicts) or 1
    robust = sum(1 for v in verdicts if v["robust"])
    return {"record_type": "robust_lane_coverage", "n_needs": len(verdicts),
            "per_lane": counts, "per_lane_fraction": {k: round(v / total, 4) for k, v in counts.items()},
            "robust_count": robust, "robust_fraction": round(robust / total, 4),
            "verdicts": verdicts, "note": "robust = deterministic_compose + package_import (model-independent, "
            "0-token); the fraction is the honest scoreboard, not a savings claim", "candidate": True,
            "serves_truth": False}


def _corpus_and_needs() -> tuple[list[dict[str, Any]], list[str]]:
    """The worked workload: the pack + aligned remixes as cards, and every DISTINCT edge as a need (a realistic
    'produce each of these' workload — some are single primitives, some chains, some unmet)."""
    from scripts.corporate_records_scraping_primitive_pack import build_cards  # noqa: PLC0415
    from scripts.primitive_groups_frameworks_and_remixers import build_remixes  # noqa: PLC0415
    cards = build_cards() + build_remixes(build_cards())
    needs = sorted({c["output_edge"] for c in cards if c.get("output_edge")}
                   | {c["input_edge"] for c in cards if c.get("input_edge")})
    return cards, needs


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    cards, needs = _corpus_and_needs()
    coverage = robust_lane_coverage(needs, cards)

    checks.append(("every need classified into a known lane; per-lane counts partition the needs exactly",
                   all(v["lane"] in LANES for v in coverage["verdicts"])
                   and sum(coverage["per_lane"].values()) == coverage["n_needs"] == len(needs),
                   f"lanes={coverage['per_lane']}"))

    # (2) the scoreboard is MEANINGFUL: robust lanes carry a non-trivial fraction AND the workload spans
    #     multiple lanes (not everything trivially one bucket) — the number is informative.
    lanes_used = {lane for lane, n in coverage["per_lane"].items() if n > 0}
    checks.append(("the scoreboard is informative: >=3 lanes populated and a non-zero robust fraction",
                   len(lanes_used) >= 3 and coverage["robust_fraction"] > 0,
                   f"robust_fraction={coverage['robust_fraction']}, lanes_used={sorted(lanes_used)}"))

    # (3) the deep EDGAR chain's goal is deterministic_compose (a real multi-hop robust route), and a pure
    #     source input (EdgarIndexWindowRequest) with no producer is generate_tail.
    from scripts.producer_edge_index import build_producer_edge_index  # noqa: PLC0415
    index = build_producer_edge_index(cards)
    dedupe = classify_need("OfficerDedupeClusterBatch", index)
    raw_input = classify_need("EdgarIndexWindowRequest", index)
    checks.append(("a multi-hop goal routes to deterministic_compose (robust, 0-token); an unproduced source "
                   "input routes to generate_tail (honest: nothing makes it)",
                   dedupe["lane"] == "deterministic_compose" and dedupe["robust"] is True
                   and raw_input["lane"] == "generate_tail" and raw_input["robust"] is False,
                   f"dedupe={dedupe['lane']} (depth {dedupe.get('chain_depth')}), input={raw_input['lane']}"))

    # (4) MUTATION GATE: delete the producers of a chained need's UPSTREAM edge -> the need falls off the
    #     deterministic_compose lane (the scoreboard MOVES when the corpus loses composability).
    thinner = [c for c in cards if c.get("output_edge") != "FilingDocumentBundle"]  # remove the fetcher's output
    thin_index = build_producer_edge_index(thinner)
    dedupe_thin = classify_need("OfficerRowBatch", thin_index)
    dedupe_full = classify_need("OfficerRowBatch", index)
    checks.append(("mutation gate: removing an upstream producer downgrades a need's lane (scoreboard is "
                   "sensitive to real composability, not a constant)",
                   dedupe_full["lane"] == "deterministic_compose"
                   and dedupe_thin["lane"] != "deterministic_compose",
                   f"full={dedupe_full['lane']} -> thinned={dedupe_thin['lane']}"))

    # (5) robust lanes are exactly the model-independent ones; the fraction is labeled a scoreboard, not savings.
    checks.append(("robust lanes = {deterministic_compose, package_import}; the number is a scoreboard, never "
                   "a proven savings claim (honest-ledger law)",
                   ROBUST_LANES == {"deterministic_compose", "package_import"}
                   and "not a savings claim" in coverage["note"]
                   and all(v["robust"] == (v["lane"] in ROBUST_LANES) for v in coverage["verdicts"]), ""))

    # (6) determinism.
    again = robust_lane_coverage(needs, cards)
    checks.append(("deterministic: re-running the scoreboard yields identical per-lane counts",
                   again["per_lane"] == coverage["per_lane"], ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - robust_lane_router: the robust-lane scoreboard (gap 2.2) — classifies "
          f"each capability need into deterministic_compose / package_import (ROBUST, 0-token) / partial_compose "
          f"/ generate_tail, and reports the honest robust fraction over a workload "
          f"({coverage['robust_fraction']:.0%} robust on the pack workload of {coverage['n_needs']} needs); "
          f"pure composition over producer_edge_index; sensitive to real composability. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Robust-lane router + coverage scoreboard for capability needs.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--need", help="classify a single need edge")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.coverage:
        cards, needs = _corpus_and_needs()
        cov = robust_lane_coverage(needs, cards)
        print(json.dumps({k: cov[k] for k in ("n_needs", "per_lane", "per_lane_fraction",
                                              "robust_fraction", "note")}, indent=2, sort_keys=True))
        return 0
    if args.need:
        from scripts.producer_edge_index import build_producer_edge_index  # noqa: PLC0415
        cards, _ = _corpus_and_needs()
        print(json.dumps(classify_need(args.need, build_producer_edge_index(cards)), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
