#!/usr/bin/env python3
"""producer_edge_index — the corpus-scale slot index for composition (open-problems gap 2.4).

Slot computation in `primitive_networks_and_grid_search.build_network` is a linear O(N) scan of the whole card
list per step. That is fine for the 57-card pack; it does not scale to the 112K-card searchable corpus (let
alone 1.17M). This module builds the inverted index the researcher specified — one streaming pass over the
corpus yields:

    producers[edge_key] -> sorted(card_ids that OUTPUT that edge)
    consumers[edge_key] -> sorted(card_ids that CONSUME that edge)

so a slot (produce edge P, consume edge C) is `producers[P] ∩ consumers[C]` — a hash lookup + a sorted-set
intersection, not a full scan. Equivalence with the linear scan is PROVEN in the self-test (same members for
every network on the real pack), so the index is a faster *substitutable path* (multi-path law), never a
behavior change: `build_network(..., index=None)` keeps the exact linear default.

The index also exposes the primitives the alignment (gap 2.1) and robust-lane (gap 2.2) work need: near-miss
edges (produced-but-never-consumed and consumed-but-never-produced) are exactly the composition breaks.

    PYTHONPATH=. python3 scripts/producer_edge_index.py --self-test
    PYTHONPATH=. python3 scripts/producer_edge_index.py --stats
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


def build_producer_edge_index(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """One streaming pass -> inverted producer/consumer maps keyed by edge, plus a card lookup. Deterministic:
    member lists are sorted; the pass order does not matter."""
    producers: dict[str, list[str]] = {}
    consumers: dict[str, list[str]] = {}
    by_id: dict[str, dict[str, Any]] = {}
    for card in cards:
        cid = card.get("card_id") or card.get("primitive_id")
        if not cid:
            continue
        by_id[cid] = card
        out_edge, in_edge = card.get("output_edge"), card.get("input_edge")
        if out_edge:
            producers.setdefault(out_edge, []).append(cid)
        if in_edge:
            consumers.setdefault(in_edge, []).append(cid)
    for table in (producers, consumers):
        for edge in table:
            table[edge] = sorted(set(table[edge]))
    return {"record_type": "producer_edge_index", "producers": producers, "consumers": consumers,
            "by_id": by_id, "n_cards": len(by_id), "n_produced_edges": len(producers),
            "n_consumed_edges": len(consumers), "candidate": True, "serves_truth": False}


def slot_members(index: dict[str, Any], produced_edge: str, consumed_edge: Optional[str]) -> list[str]:
    """Members of a slot: cards producing `produced_edge` AND (if given) consuming `consumed_edge`. O(min set)."""
    produce = index["producers"].get(produced_edge, [])
    if consumed_edge is None:   # step 0: entry is source-dependent, no consume constraint
        return list(produce)
    consume = set(index["consumers"].get(consumed_edge, []))
    return [cid for cid in produce if cid in consume]


def dangling_edges(index: dict[str, Any]) -> dict[str, list[str]]:
    """The composition breaks (feed the aligner/robust-lane work): edges produced-but-never-consumed and
    consumed-but-never-produced — where a chain would need an alignment or a bridge primitive."""
    produced, consumed = set(index["producers"]), set(index["consumers"])
    return {"produced_never_consumed": sorted(produced - consumed),
            "consumed_never_produced": sorted(consumed - produced),
            "chainable_edges": sorted(produced & consumed)}


def _linear_slot_members(cards: list[dict[str, Any]], produced_edge: str,
                         consumed_edge: Optional[str]) -> list[str]:
    """The reference linear scan (what build_network does today) — the equivalence oracle for the index."""
    return sorted(c["card_id"] for c in cards
                  if c.get("output_edge") == produced_edge
                  and (consumed_edge is None or c.get("input_edge") == consumed_edge))


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    from scripts.corporate_records_scraping_primitive_pack import build_cards
    from scripts.primitive_groups_frameworks_and_remixers import build_remixes
    from scripts.primitive_networks_and_grid_search import NETWORK_TABLE
    cards = build_cards() + build_remixes(build_cards())
    index = build_producer_edge_index(cards)

    checks.append(("index builds over the pack+remixes: producer/consumer maps + card lookup, all sorted",
                   index["n_cards"] == len(cards) and index["n_produced_edges"] > 0
                   and all(index["producers"][e] == sorted(index["producers"][e]) for e in index["producers"]),
                   f"{index['n_cards']} cards, {index['n_produced_edges']} produced edges"))

    # (2) EQUIVALENCE: for every network's every step, the index slot == the linear-scan slot. Exactly.
    mismatches = []
    for row in NETWORK_TABLE:
        chain = row["edge_chain"]
        for i, produced in enumerate(chain):
            consumed = None if i == 0 else chain[i - 1]
            idx_members = sorted(slot_members(index, produced, consumed))
            lin_members = _linear_slot_members(cards, produced, consumed)
            if idx_members != lin_members:
                mismatches.append((row["name"], produced, len(idx_members), len(lin_members)))
    checks.append(("EQUIVALENCE: index slot lookup == linear scan for every step of every network (a "
                   "substitutable faster path, never a behavior change)",
                   not mismatches, f"mismatches={mismatches[:3]}"))

    # (3) build_network accepts the index and yields IDENTICAL slots/grid to the no-index default.
    from scripts.primitive_networks_and_grid_search import build_network
    deep = NETWORK_TABLE[-1]
    net_linear = build_network(deep["name"], deep["edge_chain"], cards)
    net_indexed = build_network(deep["name"], deep["edge_chain"], cards, index=index)
    checks.append(("build_network(index=...) returns identical slots + grid_size to the linear default",
                   [s["member_ids"] for s in net_linear["slots"]]
                   == [s["member_ids"] for s in net_indexed["slots"]]
                   and net_linear["grid_size"] == net_indexed["grid_size"], ""))

    # (4) SCALE: build over a large synthetic corpus in one pass; a slot lookup does not scan the corpus.
    # card i: output E(i%500), input E((i+1)%500). So a card producing E7 (i%500==7) consumes E8 -> the
    # non-empty slot for produce-E7 is consume-E8 (120 of the 60k cards).
    big = [{"card_id": f"syn:{i}", "output_edge": f"E{i % 500}", "input_edge": f"E{(i + 1) % 500}"}
           for i in range(60_000)]
    big_index = build_producer_edge_index(big)
    members = slot_members(big_index, "E7", "E8")   # cards producing E7 and consuming E8
    checks.append(("scale: 60,000-card corpus indexed in one pass; a slot is a hash lookup + set intersect "
                   "(not an O(N) scan)",
                   big_index["n_cards"] == 60_000 and len(members) == 120
                   and members == _linear_slot_members(big, "E7", "E8"), f"E7∩E8 -> {len(members)} members"))

    # (5) dangling-edge surface: produced-never-consumed / consumed-never-produced (the aligner's raw material).
    dangling = dangling_edges(index)
    checks.append(("dangling edges surfaced (the composition breaks): produced-never-consumed + "
                   "consumed-never-produced + chainable, partitioning the edge set",
                   set(dangling["produced_never_consumed"]).isdisjoint(dangling["chainable_edges"])
                   and len(dangling["chainable_edges"]) > 0,
                   f"{len(dangling['produced_never_consumed'])} dead-end, "
                   f"{len(dangling['chainable_edges'])} chainable"))

    # (6) determinism: two builds byte-identical (member lists sorted, no RNG).
    a = json.dumps(build_producer_edge_index(cards)["producers"], sort_keys=True)
    b = json.dumps(build_producer_edge_index(cards)["producers"], sort_keys=True)
    checks.append(("deterministic: two index builds are byte-identical", a == b, ""))

    ok = all(passed for _n, passed, _d in checks)
    print(f"{'PASS' if ok else 'FAIL'} - producer_edge_index: corpus-scale slot index (gap 2.4) — one-pass "
          f"inverted producer/consumer maps; slot = hash lookup + set intersect, PROVEN equivalent to the "
          f"linear scan for every network; scales to 60k cards; surfaces dangling edges for the aligner. "
          f"serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail[:200]})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Corpus-scale producer/consumer edge index for composition.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.stats:
        from scripts.corporate_records_scraping_primitive_pack import build_cards
        from scripts.primitive_groups_frameworks_and_remixers import build_remixes
        cards = build_cards() + build_remixes(build_cards())
        index = build_producer_edge_index(cards)
        dangling = dangling_edges(index)
        print(json.dumps({"n_cards": index["n_cards"], "n_produced_edges": index["n_produced_edges"],
                          "n_consumed_edges": index["n_consumed_edges"],
                          "chainable_edges": len(dangling["chainable_edges"]),
                          "produced_never_consumed": len(dangling["produced_never_consumed"]),
                          "consumed_never_produced": len(dangling["consumed_never_produced"])},
                         indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
