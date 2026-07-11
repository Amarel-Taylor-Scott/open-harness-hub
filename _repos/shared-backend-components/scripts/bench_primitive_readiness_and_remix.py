#!/usr/bin/env python3
"""scripts.bench_primitive_readiness_and_remix — does the primitive corpus actually WORK as a composable
system? Scores every primitive against the standard, runs thousands of composition/remix simulations over
the edge graph, and finds the missing primitives (edges nothing produces/consumes = "where primitives don't
exist"). The companion to run_token_savings_experiments (which measures reuse/search); this measures whether
the things being reused are well-formed, compatible, and remixable.

It COMPOSES the existing machinery rather than reinventing it (reuse-first): the factory card shape + the
edge indexes are the substrate; naming follows the canonical_id shape the ID gate enforces; determinism is
the mutator_registry's axis; schema is the capability-card standard. Here we roll all of that up per-card, at
scale, into one readiness scorecard + a remix simulation.

Three questions, measured:
  1. STANDARDS — does each primitive follow the template? well-formed required fields, TYPED edges (a real
     input_edge AND output_edge), canonical id shape, declared quality/readiness, declared determinism, and a
     candidate/truth boundary. → per-dimension conformance rate + the exact primitives that fail each.
  2. REMIXABILITY — build the edge graph (output_edge → whoever consumes that edge) and run N remix
     simulations: from a sampled primitive, how deep can we CHAIN by feeding outputs into compatible inputs?
     → remixability rate + reachable-depth distribution. Exact-edge matching is a CONSERVATIVE floor (only
     identical edge strings compose; semantic matches are not counted), so it under-states composability.
  3. GAPS — the edges DEMANDED (some primitive's input) but PRODUCED by nothing, and edges PRODUCED but
     CONSUMED by nothing. Both are "a primitive that does not exist yet" — ranked by frequency, routed to the
     research queue (the acquisition signal).

Every row is candidate=true / serves_truth=false — a readiness measurement, never a promotion.

  PYTHONPATH=. python3 scripts/bench_primitive_readiness_and_remix.py --self-test
  PYTHONPATH=. python3 scripts/bench_primitive_readiness_and_remix.py --run --n 5000 [--corpus 30000] [--depth 6] [--emit-gaps]
"""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import random  # noqa: E402
import re  # noqa: E402
from collections import defaultdict  # noqa: E402

from scripts._jsonl import read_jsonl_tolerant  # noqa: E402
from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts._time import now_iso  # noqa: E402

#: sources of edge-bearing primitive cards (first that exists wins; tolerant of a torn factory tail).
CARD_SOURCES = (
    "data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards.jsonl",
    "data/dev-intel/primitive_factory/linkable_cards/2026-07-01/linkable_primitive_cards.jsonl",
    "data/dev-intel/aidevobserver_edge_foundry/primitive_edge_cards.jsonl",
)
OUT_DIR = _resource("data") / "dev-intel" / "primitive_readiness_remix"
#: the template a well-formed factory primitive card must carry (the "standard").
STANDARD_REQUIRED = ("primitive_id", "title", "kind", "input_edge", "output_edge", "contract")
#: canonical id shape the ID gate mints — "<prefix>:<hex16+>" or "<prefix>-<sha16>"; the naming standard.
_ID_SHAPE = re.compile(r"^[a-z][a-z0-9_.]*[:\-][A-Za-z0-9_.:-]{6,}$")
#: a typed edge must be more than a trivial token to actually carry a contract.
_MIN_EDGE_LEN = 3


def _nonempty(v: object) -> bool:
    return bool(v) and (not isinstance(v, str) or len(v.strip()) > 0)


def _edge(card: dict, which: str) -> str:
    """Normalized edge string (input_edge/output_edge), tolerating the contract.{input,output} fallback."""
    v = card.get(which)
    if not v:
        contract = card.get("contract") if isinstance(card.get("contract"), dict) else {}
        v = contract.get(which.split("_")[0]) if contract else None
    return str(v).strip() if v else ""


def score_card(card: dict) -> dict:
    """Score one primitive against the standard — each dimension a bool the roll-up counts, plus a per-card
    readiness fraction. No engine calls: this is the checkable-from-the-card standard surface."""
    inp, out = _edge(card, "input_edge"), _edge(card, "output_edge")
    dims = {
        # well-formed: every required template field present + non-empty
        "well_formed": all(_nonempty(card.get(f)) for f in STANDARD_REQUIRED),
        # typed edges: a real input AND output contract (not a stub) — the composability precondition
        "typed_edges": len(inp) >= _MIN_EDGE_LEN and len(out) >= _MIN_EDGE_LEN,
        # canonical id shape (the naming standard the ID gate enforces)
        "named_canonical": bool(_ID_SHAPE.match(str(card.get("primitive_id") or ""))),
        # declared quality + readiness (a card that can't state its readiness can't be promoted)
        "quality_declared": _nonempty(card.get("quality_score")) and _nonempty(card.get("readiness")),
        # declared determinism/behavior (the deterministic-editing axis — effects/mutations/proof present)
        "deterministic_declared": _nonempty(card.get("kind")) and any(
            _nonempty(card.get(f)) for f in ("effects", "mutations", "proof_requirements", "edge_contract")),
        # candidate/truth boundary explicitly stated (governance standard)
        "governed": "serves_truth" in card,
    }
    passed = sum(1 for v in dims.values() if v)
    return {
        "record_type": "primitive_readiness_scorecard",
        "primitive_id": card.get("primitive_id"),
        "input_edge": inp,
        "output_edge": out,
        **{f"std_{k}": v for k, v in dims.items()},
        "readiness_score": round(passed / len(dims), 3),
        "standard_compliant": passed == len(dims),
        "candidate": True,
        "serves_truth": False,
    }


def build_edge_graph(cards: list[dict]) -> tuple[dict, dict]:
    """producers[edge] = card_ids whose OUTPUT is that edge; consumers[edge] = card_ids whose INPUT is that
    edge. This is the exact-edge composition graph the remix sim walks."""
    producers: dict[str, list[str]] = defaultdict(list)
    consumers: dict[str, list[str]] = defaultdict(list)
    for c in cards:
        cid = c.get("primitive_id")
        if not cid:
            continue
        out, inp = _edge(c, "output_edge"), _edge(c, "input_edge")
        if out:
            producers[out].append(cid)
        if inp:
            consumers[inp].append(cid)
    return producers, consumers


def remix_chain(start: dict, by_id: dict, consumers: dict, max_depth: int) -> dict:
    """From ``start``, greedily chain output→input using exact-edge matches, up to ``max_depth``. Returns the
    depth reached and the break edge (the output no primitive consumes = a MISSING consumer primitive)."""
    seen = {start.get("primitive_id")}
    current = start
    depth = 0
    while depth < max_depth:
        out = _edge(current, "output_edge")
        nxt = next((cid for cid in consumers.get(out, []) if cid not in seen), None)
        if nxt is None:
            return {"depth": depth, "break_edge": out or None, "remixable": depth >= 1}
        seen.add(nxt)
        current = by_id.get(nxt, {})
        depth += 1
    return {"depth": depth, "break_edge": None, "remixable": True}


def run_readiness(cards: list[dict], n: int, depth: int, seed: int) -> dict:
    """Score standards over ALL cards; run ``n`` remix simulations; detect gap edges. Returns the full result
    bundle (scorecards summary, remix rows, gap edges) — aggregation happens in ``aggregate``."""
    scorecards = [score_card(c) for c in cards]
    producers, consumers = build_edge_graph(cards)
    by_id = {c.get("primitive_id"): c for c in cards if c.get("primitive_id")}

    rng = random.Random(seed)
    startable = [c for c in cards if _edge(c, "output_edge")]
    sample = startable if n >= len(startable) else rng.sample(startable, n)
    remix = [{"primitive_id": c.get("primitive_id"), **remix_chain(c, by_id, consumers, depth)} for c in sample]

    # GAPS: inputs demanded but never produced, outputs produced but never consumed → missing primitives.
    unmet_inputs = {e: len(cids) for e, cids in consumers.items() if e not in producers}
    dangling_outputs = {e: len(cids) for e, cids in producers.items() if e not in consumers}
    return {"scorecards": scorecards, "remix": remix,
            "unmet_inputs": unmet_inputs, "dangling_outputs": dangling_outputs,
            "n_cards": len(cards), "n_edges_produced": len(producers), "n_edges_consumed": len(consumers)}


def aggregate(bundle: dict) -> dict:
    """Roll up: standards conformance per dimension, remixability rate + depth, and the ranked missing-primitive
    gaps (the acquisition signal)."""
    scorecards = bundle["scorecards"]
    remix = bundle["remix"]
    n = len(scorecards)
    if not n:
        return {"experiments": 0}
    dim_keys = [k for k in scorecards[0] if k.startswith("std_")]
    conformance = {k[4:]: round(sum(1 for s in scorecards if s[k]) / n, 3) for k in dim_keys}
    # the primitives that fail EACH standard (the fix list) — cap per dimension so the summary stays bounded
    failing = {k[4:]: [s["primitive_id"] for s in scorecards if not s[k]][:20] for k in dim_keys}

    m = len(remix) or 1
    remixable = sum(1 for r in remix if r["remixable"])
    avg_depth = round(sum(r["depth"] for r in remix) / m, 2)
    depth_hist: dict[int, int] = defaultdict(int)
    for r in remix:
        depth_hist[r["depth"]] += 1

    top_unmet = sorted(bundle["unmet_inputs"].items(), key=lambda kv: -kv[1])[:25]
    top_dangling = sorted(bundle["dangling_outputs"].items(), key=lambda kv: -kv[1])[:25]
    return {
        "record_type": "primitive_readiness_remix_summary",
        "generated_at": now_iso(),
        "cards_scored": n,
        "fully_standard_compliant_rate": round(sum(1 for s in scorecards if s["standard_compliant"]) / n, 3),
        "standards_conformance": conformance,
        "worst_standard": min(conformance, key=conformance.get) if conformance else None,
        "failing_examples": failing,
        "remix_simulations": len(remix),
        "remixable_rate": round(remixable / m, 3),
        "avg_reachable_depth": avg_depth,
        "reachable_depth_histogram": {str(d): depth_hist[d] for d in sorted(depth_hist)},
        "missing_producer_primitives": [{"edge": e, "demanded_by": c} for e, c in top_unmet],
        "orphan_output_primitives": [{"edge": e, "produced_by": c} for e, c in top_dangling],
        "gap_edge_counts": {"unmet_inputs": len(bundle["unmet_inputs"]),
                            "dangling_outputs": len(bundle["dangling_outputs"])},
        "tokens_basis": "n/a (structural readiness, not token measurement)",
        "serves_truth": False,
    }


def _load_cards(limit: int) -> list[dict]:
    for rel in CARD_SOURCES:
        path = _resource(rel)
        if path.exists():
            cards = [c for c in read_jsonl_tolerant(path) if c.get("primitive_id")]
            return cards[:limit] if limit and limit < len(cards) else cards
    return []


def _emit(bundle: dict, summary: dict, emit_gaps: bool) -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "scorecards.jsonl").write_text(
        "".join(json.dumps(s) + "\n" for s in bundle["scorecards"]), encoding="utf-8")
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    emitted = 0
    if emit_gaps and summary.get("missing_producer_primitives"):
        from scripts.acquisition import research_queue as _rq  # noqa: PLC0415
        queue = getattr(_rq, "DEFAULT_QUEUE", OUT_DIR / "areas.jsonl")
        with open(queue, "a", encoding="utf-8") as fh:
            for gap in summary["missing_producer_primitives"]:
                fh.write(json.dumps({
                    "record_type": "research_area", "area": gap["edge"],
                    "reason": "no primitive produces this demanded edge (remix gap)",
                    "demanded_by": gap["demanded_by"], "source": "bench_primitive_readiness_and_remix",
                    "candidate": True, "serves_truth": False}) + "\n")
                emitted += 1
    return {"scorecards_path": str(OUT_DIR / "scorecards.jsonl"),
            "summary_path": str(OUT_DIR / "summary.json"), "gap_areas_emitted": emitted}


def _run(n: int, depth: int, seed: int, corpus: int, emit_gaps: bool) -> int:
    cards = _load_cards(corpus)
    if not cards:
        print("no real cards found (factory scratch may be gitignored on this checkout); run the factory first")
        return 1
    bundle = run_readiness(cards, n, depth, seed)
    summary = aggregate(bundle)
    paths = _emit(bundle, summary, emit_gaps)
    keys = ("cards_scored", "fully_standard_compliant_rate", "worst_standard", "remix_simulations",
            "remixable_rate", "avg_reachable_depth")
    print(json.dumps({k: summary[k] for k in keys if k in summary}, indent=2))
    print(f"  standards conformance: {summary['standards_conformance']}")
    print(f"  top missing-producer edges (need these primitives): "
          f"{[g['edge'][:40] for g in summary['missing_producer_primitives'][:6]]}")
    print(f"  written: {paths['summary_path']}  |  gap areas emitted: {paths['gap_areas_emitted']}")
    return 0


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    def card(pid, inp, out, **extra):
        base = {"primitive_id": pid, "title": pid, "kind": "route.primitive", "input_edge": inp,
                "output_edge": out, "contract": {"in": inp, "out": out}, "quality_score": 0.8,
                "readiness": "candidate", "effects": ["x"], "serves_truth": False}
        base.update(extra)
        return base

    # A chainable corpus A->B->C plus a well-formed island D and a MALFORMED card E.
    corpus = [
        card("prim:aa1111111111", "Raw", "Parsed"),
        card("prim:bb2222222222", "Parsed", "Normalized"),
        card("prim:cc3333333333", "Normalized", "Scored"),
        card("prim:dd4444444444", "Lonely", "AlsoLonely"),          # island: nothing consumes AlsoLonely
        {"primitive_id": "not-canonical id", "input_edge": "", "output_edge": ""},  # malformed: fails most dims
    ]
    bundle = run_readiness(corpus, n=len(corpus), depth=6, seed=1)
    summ = aggregate(bundle)

    checks.append(("scored every card + candidate/serves_truth=false",
                   summ["cards_scored"] == len(corpus) and all(s["serves_truth"] is False for s in bundle["scorecards"])))
    checks.append(("standards catch the malformed card (not 100% compliant)",
                   summ["fully_standard_compliant_rate"] < 1.0))
    checks.append(("the malformed card fails well_formed + typed_edges + named_canonical", (
        (sc := next(s for s in bundle["scorecards"] if s["primitive_id"] == "not-canonical id"))
        and not sc["std_well_formed"] and not sc["std_typed_edges"] and not sc["std_named_canonical"])))
    checks.append(("a well-formed chainable card is fully standard-compliant",
                   next(s for s in bundle["scorecards"] if s["primitive_id"] == "prim:aa1111111111")["standard_compliant"]))
    # remix: A should chain A->B->C (depth 2); the island D breaks immediately (depth 0).
    remix_by_id = {r["primitive_id"]: r for r in bundle["remix"]}
    checks.append(("remix chains A->B->C (reachable depth 2)", remix_by_id["prim:aa1111111111"]["depth"] == 2))
    checks.append(("the island primitive is NOT remixable (depth 0, break edge recorded)",
                   remix_by_id["prim:dd4444444444"]["depth"] == 0 and remix_by_id["prim:dd4444444444"]["break_edge"] == "AlsoLonely"))
    # gaps: 'Raw' is demanded (A's input) but nothing produces it -> missing-producer gap; 'Scored'/'AlsoLonely'
    # are produced but unconsumed -> dangling.
    checks.append(("gap: a demanded-but-unproduced edge is a missing-producer primitive",
                   any(g["edge"] == "Raw" for g in summ["missing_producer_primitives"])))
    checks.append(("gap: a produced-but-unconsumed edge is an orphan output",
                   any(g["edge"] in ("Scored", "AlsoLonely") for g in summ["orphan_output_primitives"])))
    # MUTATION / determinism: same seed -> identical remixable rate + conformance (VERIFY-THE-VERIFIER).
    again = aggregate(run_readiness(corpus, n=len(corpus), depth=6, seed=1))
    checks.append(("deterministic: same seed -> identical remixable_rate + conformance",
                   again["remixable_rate"] == summ["remixable_rate"] and again["standards_conformance"] == summ["standards_conformance"]))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - bench_primitive_readiness_and_remix: per-primitive standards scorecard (well-formed / typed "
          "edges / canonical id / quality / determinism / governed); remix simulation chains outputs→inputs and "
          "flags islands; missing-producer + orphan-output edges = the gaps; deterministic; serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--n", type=int, default=5000, help="remix simulations to run")
    ap.add_argument("--depth", type=int, default=6, help="max remix chain depth")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--corpus", type=int, default=30000, help="max cards to score + graph")
    ap.add_argument("--emit-gaps", action="store_true", help="append missing-producer edges to the research queue")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.n, args.depth, args.seed, args.corpus, args.emit_gaps)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
