#!/usr/bin/env python3
"""scripts.primitive_build_loop — the END-TO-END build loop that closes the minimum-token orchestration:
COMPOSE from existing primitives → REMIX a near-match to fill a gap (before ever asking the LLM to generate)
→ INGEST the fills as candidates → RE-COMPOSE. The remaining gaps are the TRUE gaps an LLM must generate.

Owner north star (this module makes it a closed loop): an LLM builds a system by wiring primitives with
minimum tokens. Two levers cut the LLM's work to near-zero and make it COMPOUND:

  * REMIX-BEFORE-GENERATE — a gap is a needed edge nothing produces. Before spending LLM tokens to GENERATE a
    new primitive, find a near-match whose output is type-COMPATIBLE (edge_representations family/embedding)
    and REMIX its edge (primitive_onion.remix_edges) to the needed edge — a deterministic, lineage-preserving
    CANDIDATE fill (serves_truth=false). The LLM then only VERIFIES a remix instead of writing from scratch.
  * GAP → INGEST — every fill is ingested into the working corpus as a candidate, so RE-composition finds it,
    routes extend, and gaps shrink. Run it and the per-build gap count monotonically falls: the more the
    system is used, the less the LLM has to do.

``build_system(target, cards)`` returns the final orchestration plan, the fill history, and the TRUE gaps
(the only things left for an LLM to generate) — plus the token budget from primitive_orchestration.

Every ingested fill is candidate=true / serves_truth=false — a remix is a HYPOTHESIS the LLM/proof confirms,
never promoted truth. This does not call an LLM; it prepares the minimum for one to.

    PYTHONPATH=. python3 scripts/primitive_build_loop.py --self-test
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
from typing import Any, Optional  # noqa: E402

from scripts import edge_representations as _er  # noqa: E402
from scripts import primitive_onion as _onion  # noqa: E402
from scripts import primitive_orchestration as _orch  # noqa: E402

#: remix-fill EVERY gap by default (None = unbounded — use everything we have; not an arbitrary cap). An
#: explicit integer only exists for a caller that wants to bound one round's work; the loop itself converges.
DEFAULT_MAX_FILLS = None


def _gap_needed_edge(gap: dict) -> str:
    """The edge a gap needs a producer for, tolerating the generation_spec's field names."""
    for k in ("needed_edge", "output_edge", "produces", "target_edge", "input_edge"):
        v = gap.get(k)
        if v:
            return str(v)
    return ""


def remix_fill_candidate(needed_edge: str, cards: list[dict], family_index: dict) -> Optional[dict]:
    """Find a near-match primitive whose OUTPUT is type-compatible with ``needed_edge`` (family/embedding, not
    exact — an exact match would not be a gap) and REMIX its output edge to ``needed_edge``. Returns a candidate
    remixed primitive (serves_truth=false, lineage kept) that PROPOSES to produce ``needed_edge``, or None when
    no near-match exists (a TRUE gap the LLM must generate). Deterministic: the best-quality near-match wins."""
    best = None
    best_key = None
    for c in cards:
        out = str(c.get("output_edge") or "")
        if not out or out == needed_edge:
            continue
        v = _er.compatibility(out, needed_edge, family_index)
        # a REMIX fill only makes sense for a near-match (family/embedding), not exact (that's not a gap) — and
        # never a raw token coincidence: require the principled family/canonical/embedding representations.
        if v["compatible"] and v["via"] in ("canonical", "family", "embedding"):
            key = (v["score"], float(c.get("quality_score") or 0), str(c.get("primitive_id")))
            if best_key is None or key > best_key:
                best, best_key = c, key
    if best is None:
        return None
    fill = _onion.remix_edges(best, output_edge=needed_edge)   # deterministic, lineage-preserving candidate
    fill["fills_gap_edge"] = needed_edge
    fill["fill_via"] = best_key and "near-match-remix"
    fill["fill_confidence"] = _er.compatibility(str(best.get("output_edge") or ""), needed_edge, family_index)["via"]
    return fill


def build_system(target_output: str, cards: list[dict], *, rounds: Optional[int] = None,
                 max_fills: Optional[int] = DEFAULT_MAX_FILLS, source_edges: Optional[list] = None) -> dict:
    """Compose → remix-fill EVERY gap → ingest → re-compose until it CONVERGES (a fixed point: a round that
    adds no new fill), using the WHOLE corpus. ``rounds=None`` (default) converges — it is not a cap; a safety
    bound (1 + corpus size) only prevents a pathological runaway. ``max_fills=None`` fills every gap in a round.
    ``source_edges`` = the raw inputs the environment supplies (passed through to plan) — constrain it to make
    the composition report real gaps rather than treating every corpus input as already available.
    Returns the final plan, the per-round fill history, and the TRUE gaps left for the LLM to generate."""
    working = list(cards)
    history: list[dict] = []
    initial = _orch.orchestrate(target_output, working, source_edges=source_edges)
    bound = rounds if rounds is not None else 1 + len(cards)      # converge; the bound is a runaway backstop
    for r in range(bound):
        ctx = _orch.orchestrate(target_output, working, source_edges=source_edges)
        gaps = ctx.get("gaps", []) or []
        if not gaps:
            history.append({"round": r + 1, "gaps": 0, "remix_filled": 0, "note": "fully composed"})
            break
        fam = _er.build_family_index([str(c.get("output_edge") or "") for c in working]
                                     + [_gap_needed_edge(g) for g in gaps])
        fills = []
        for gap in (gaps if max_fills is None else gaps[:max_fills]):
            cand = remix_fill_candidate(_gap_needed_edge(gap), working, fam)
            if cand:
                fills.append(cand)
        history.append({"round": r + 1, "gaps": len(gaps), "remix_filled": len(fills),
                        "route_length": ctx["route_length"]})
        if not fills:
            break                       # remaining gaps are TRUE gaps — only an LLM can generate these
        working = working + fills       # INGEST the candidate fills; re-compose next round finds them

    final = _orch.orchestrate(target_output, working, source_edges=source_edges)
    return {
        "record_type": "primitive_build_loop_result",
        "target_output": target_output,
        "rounds_run": len(history),
        "history": history,
        "initial_gaps": initial.get("gap_count", 0),
        "initial_route_length": initial.get("route_length", 0),
        "final_gaps": final.get("gap_count", 0),
        "final_route_length": final.get("route_length", 0),
        "remix_fills_total": sum(h.get("remix_filled", 0) for h in history),
        "true_gaps_for_llm": final.get("gaps", []),            # the ONLY things an LLM must generate
        "true_gap_count": final.get("gap_count", 0),
        "token_budget": final.get("token_budget", {}),
        "protocol": ("REMIX-before-GENERATE + GAP->INGEST: compose from existing primitives, fill gaps by "
                     "remixing near-matches (deterministic, candidate), ingest the fills, re-compose. The LLM "
                     "only VERIFIES remixes and GENERATES the true gaps — which shrink as the corpus grows."),
        "candidate": True,
        "serves_truth": False,
    }


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    def card(pid, inp, out, does="does x"):
        return {"primitive_id": pid, "title": pid, "kind": "route.primitive", "input_edge": inp,
                "output_edge": out, "blackbox": {"does": does}, "contract": {"in": inp, "out": out, "rules": ["r"] * 20},
                "effects": ["e"] * 6, "quality_score": 0.8, "readiness": "candidate", "serves_truth": False}

    # A realistically-sized corpus so the family df-window fires (a token must be in >=3 edges but <20% of them):
    # 22 distinct-domain fillers + a 'widget' FAMILY of 5 producers + a consumer that needs 'WidgetBatch' (which
    # NOTHING produces exactly). remix-fill should close the WidgetBatch gap from a widget near-match, no generation.
    cards = [card(f"p:f{i}", f"In{i}Edge", f"Out{i}Edge") for i in range(22)]
    cards += [card("p:wa", "AlphaEdge", "WidgetParsed"), card("p:wb", "BetaEdge", "WidgetNormalized"),
              card("p:wc", "GammaEdge", "WidgetScored"), card("p:wd", "DeltaEdge", "WidgetValidated"),
              card("p:we", "EpsilonEdge", "WidgetIndexed")]
    cards += [card("p:consume", "WidgetBatch", "FinalReport", "consume a widget batch")]
    fam = _er.build_family_index([c["output_edge"] for c in cards] + [c["input_edge"] for c in cards])
    fill = remix_fill_candidate("WidgetBatch", cards, fam)
    checks.append(("remix-fill finds a near-match + remixes it to produce the needed edge (candidate)",
                   fill is not None and fill["output_edge"] == "WidgetBatch"
                   and str(fill["remixed_from"]).startswith("p:w") and fill["serves_truth"] is False))
    checks.append(("a needed edge with NO near-match is a TRUE gap (remix-fill returns None)",
                   remix_fill_candidate("ZzqCompletelyUnrelatedXyz", cards, fam) is None))

    res = build_system("FinalReport", cards, rounds=3)
    checks.append(("build_system runs the loop + reports history/true-gaps + serves_truth=false",
                   res["rounds_run"] >= 1 and isinstance(res["true_gaps_for_llm"], list) and res["serves_truth"] is False))
    checks.append(("gap→ingest shrinks gaps: final gaps <= initial gaps",
                   res["final_gaps"] <= res["initial_gaps"]))
    checks.append(("remix-before-generate did fills OR the target was already composable",
                   res["remix_fills_total"] > 0 or res["initial_gaps"] == 0))
    checks.append(("token budget carried from orchestration", "llm_context_tokens" in (res["token_budget"] or {})))

    # determinism
    again = build_system("FinalReport", cards, rounds=3)
    checks.append(("deterministic: same task -> identical fills + final gaps",
                   again["remix_fills_total"] == res["remix_fills_total"] and again["final_gaps"] == res["final_gaps"]))

    # honesty: an ingested fill is candidate, never promoted; and it carries lineage
    if fill:
        checks.append(("an ingested fill is a lineage-carrying candidate, never truth",
                       fill.get("candidate") and not fill.get("serves_truth") and fill.get("remixed_from")))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_build_loop: closes the loop — compose, REMIX a near-match to fill a gap before "
          "generating, INGEST the candidate fill, re-compose; gaps shrink as the corpus grows; the LLM only "
          "verifies remixes + generates the true gaps; deterministic; serves_truth=false.")
    return 0


def _run(target: str, corpus: int, rounds: int) -> int:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    from scripts._repo_paths import resource  # noqa: PLC0415
    path = resource("data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards.jsonl")
    if not path.exists():
        print("no cards found"); return 1
    _all = [c for c in read_jsonl_tolerant(path) if c.get("primitive_id")]
    cards = _all[:corpus] if corpus else _all  # 0 = FULL corpus (use everything)
    # pick a target that is NOT trivially produced, so the loop has work to do
    tgt = target or next((str(c.get("input_edge")) for c in cards if c.get("input_edge")), str(cards[0].get("output_edge")))
    res = build_system(tgt, cards, rounds=(rounds or None))  # 0 -> None -> converge
    print(json.dumps({k: res[k] for k in ("target_output", "rounds_run", "initial_gaps", "final_gaps",
                     "initial_route_length", "final_route_length", "remix_fills_total", "true_gap_count",
                     "token_budget")}, indent=2, default=str))
    print(f"  history: {res['history']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--target", default="")
    ap.add_argument("--corpus", type=int, default=0, help="0 = FULL corpus (use everything)")
    ap.add_argument("--rounds", type=int, default=0, help="0 = converge (no round cap)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.target, args.corpus, args.rounds)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
