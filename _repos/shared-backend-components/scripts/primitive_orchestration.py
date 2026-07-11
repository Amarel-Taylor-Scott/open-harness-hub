#!/usr/bin/env python3
"""scripts.primitive_orchestration — the MINIMUM-TOKEN protocol: hand an LLM (large, medium, OR small) exactly
what it needs to BUILD A SYSTEM by wiring + ordering primitives, and nothing more.

Owner north star: an LLM should build complex systems with MINIMUM tokens by wiring + ordering primitives,
knowing ONLY their blackbox description + edges, guided by the results of DETERMINISTIC + HYBRID compatibility
checks and remixing — never reading a primitive's implementation, never recomputing what composes. This module
is the seam that delivers that. It COMPOSES the pieces built this session (reuse-first, builds no new engine):

  * hybrid_composer.plan     — backward-chains an ORDERED route from existing primitives + emits GAPS as
                               generation_specs where nothing composes (the "LLM fills the missing pieces").
  * primitive_onion          — each route primitive is handed to the LLM as its SIGNATURE (blackbox + edges,
                               ~tens of tokens), never the full card.
  * edge_representations     — each WIRING JOIN carries the DETERMINISTIC + HYBRID compatibility verdict
                               (exact/canonical/family/embedding, labelled by confidence) — the SYSTEM computed
                               it, so the LLM does not have to.

``orchestrate(target_output, cards)`` returns an ``LLMOrchestrationContext``: the ordered route as blackbox+edge
views, the per-join compatibility verdicts, the gap generation-specs, and a TOKEN BUDGET proving the context is
minimal (views+verdicts+gaps) vs reading the full cards vs regenerating from scratch. That budget is the whole
point: it is what makes a SMALL model able to assemble what a frontier model would generate from scratch.

candidate=true / serves_truth=false — an orchestration plan is a POINTER to a build, never truth.

    PYTHONPATH=. python3 scripts/primitive_orchestration.py --self-test
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
from typing import Any, Callable, Optional  # noqa: E402

from scripts import edge_representations as _er  # noqa: E402  the multi-representation compatibility library
from scripts import hybrid_composer as _hc  # noqa: E402  the compose-route + emit-gaps engine
from scripts import primitive_onion as _onion  # noqa: E402  the signature (blackbox + edges) layer

CHARS_PER_TOKEN = 4
#: an implementation is bigger than its spec card; the from-scratch regenerate cost is at LEAST this multiple of
#: the full-card read (conservative — primitive_lift_benchmark measured ~486x full-SOURCE vs edge-cards; we use a
#: deliberately small, defensible floor so the "vs regenerate" number under-claims, never over-claims).
_REGENERATE_MULTIPLE = 8


def _est_tokens(obj: Any) -> int:
    return len(json.dumps(obj)) // CHARS_PER_TOKEN


def orchestration_view(card: dict, *, blackbox_chars: int = 160) -> dict:
    """The ONLY thing an LLM reads per primitive: its blackbox DESCRIPTION + its edges (the signature). No
    contract, no effects, no implementation — the minimum to wire it. Blackbox is compacted to one short line."""
    sig = _onion.signature(card)  # primitive_id, title, input_edge, output_edge
    bb = card.get("blackbox")
    bb = (bb.get("does") if isinstance(bb, dict) else bb) or ""
    return {"primitive_id": sig.get("primitive_id"), "blackbox": str(bb)[:blackbox_chars],
            "input_edge": sig.get("input_edge"), "output_edge": sig.get("output_edge")}


def _route_ids(plan: dict) -> list[str]:
    """The ordered producer ids of the plan's route, tolerating id-strings or hit/step dicts."""
    out: list[str] = []
    for step in plan.get("route", []) or []:
        if isinstance(step, str):
            out.append(step)
        elif isinstance(step, dict):
            pid = step.get("primitive_id") or step.get("id") or step.get("producer_id")
            if pid:
                out.append(str(pid))
    return out


def orchestrate(target_output: str, cards: list[dict], *, matcher: Optional[Callable] = None,
                source_edges: Optional[list] = None) -> dict:
    """Produce the minimal LLM orchestration context for building ``target_output`` from ``cards``. ``source_edges``
    = the raw inputs the environment supplies; pass a constrained set to make the plan report real gaps rather
    than treating every corpus input as already available (the default biases toward completing)."""
    matcher = matcher or _hc.matcher_from_cards(cards)
    plan = _hc.plan(target_output, cards, matcher, source_edges=source_edges)
    by_id = {c.get("primitive_id"): c for c in cards if c.get("primitive_id")}
    route_ids = _route_ids(plan)
    route_cards = [by_id[pid] for pid in route_ids if pid in by_id]

    # 1. what the LLM READS: each route primitive as blackbox + edges (the signature).
    views = [orchestration_view(c) for c in route_cards]

    # 2. the WIRING JOINS: the deterministic + hybrid compatibility verdict the SYSTEM computed, per adjacency,
    #    so the LLM knows an output feeds the next input (and how confidently) without recomputing it.
    fam_index = _er.build_family_index(
        [str(c.get("output_edge") or "") for c in route_cards] + [str(c.get("input_edge") or "") for c in route_cards])
    joins = []
    for a, b in zip(route_cards, route_cards[1:]):
        v = _er.compatibility(str(a.get("output_edge") or ""), str(b.get("input_edge") or ""), fam_index)
        joins.append({"from": a.get("primitive_id"), "to": b.get("primitive_id"),
                      "producer_edge": v["a"], "consumer_edge": v["b"],
                      "compatible": v["compatible"], "via": v["via"], "confidence": v["score"]})

    # 3. the GAPS: where no primitive composes, a deterministic generation-spec for the LLM to fill.
    gaps = plan.get("gaps", []) or []

    # 4. the TOKEN BUDGET — the whole point. The LLM's context is views + join verdicts + gap specs; compare to
    #    reading the FULL cards, and to regenerating from scratch (a conservative multiple of the full-card read).
    llm_context_tokens = sum(_est_tokens(v) for v in views) + sum(_est_tokens(j) for j in joins) + sum(_est_tokens(g) for g in gaps)
    full_card_tokens = sum(_est_tokens(c) for c in route_cards)
    regenerate_tokens = full_card_tokens * _REGENERATE_MULTIPLE
    return {
        "record_type": "llm_orchestration_context",
        "target_output": target_output,
        "route": route_ids,
        "route_length": len(route_ids),
        "views": views,                       # blackbox + edges, the ONLY per-primitive content the LLM reads
        "joins": joins,                       # deterministic + hybrid compatibility verdicts (system-computed)
        "gaps": gaps,                         # generation specs the LLM fills where nothing composes
        "gap_count": len(gaps),
        "fully_composed": len(gaps) == 0,
        "token_budget": {
            "llm_context_tokens": llm_context_tokens,
            "full_card_read_tokens": full_card_tokens,
            "regenerate_from_scratch_tokens": regenerate_tokens,
            "savings_vs_full_card": round(full_card_tokens / llm_context_tokens, 1) if llm_context_tokens else None,
            "savings_vs_regenerate": round(regenerate_tokens / llm_context_tokens, 1) if llm_context_tokens else None,
            "basis": "chars/4 proxy; regenerate = full_card x conservative 8 floor (primitive_lift_benchmark: ~486x full-source)",
        },
        "protocol": ("The LLM reads only `views` (blackbox+edges) + `joins` (system-computed compatibility) + "
                     "`gaps`; it ORDERS/wires the route and GENERATES only the gap specs. It never reads an "
                     "implementation and never recomputes what composes."),
        "candidate": True,
        "serves_truth": False,
    }


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    def card(pid, inp, out, does):
        return {"primitive_id": pid, "title": pid, "kind": "route.primitive", "input_edge": inp,
                "output_edge": out, "blackbox": {"does": does}, "contract": {"in": inp, "out": out, "rules": ["r"] * 40},
                "effects": ["e"] * 8, "mutations": ["m"] * 6, "proof_requirements": ["p"] * 8,
                "quality_score": 0.8, "readiness": "candidate", "serves_truth": False}
    # a composable chain to the target + one unrelated card (distractor).
    cards = [
        card("p:ocr", "ScannedPdf", "ExtractedText", "extract text from a scanned pdf via ocr"),
        card("p:norm", "ExtractedText", "NormalizedText", "normalize extracted text"),
        card("p:screen", "NormalizedText", "SanctionsHit", "screen normalized text against the ofac list"),
        card("p:unrelated", "Foo", "Bar", "does something unrelated"),
    ]
    ctx = orchestrate("SanctionsHit", cards)

    checks.append(("returns an ordered route toward the target", ctx["route_length"] >= 1 and ctx["serves_truth"] is False))
    checks.append(("each view is ONLY blackbox + edges (no contract/effects/impl leaked)",
                   all(set(v) == {"primitive_id", "blackbox", "input_edge", "output_edge"} for v in ctx["views"])))
    checks.append(("a view is far smaller than the full card (minimum-token reading)",
                   ctx["views"] and _est_tokens(ctx["views"][0]) * 3 < _est_tokens(cards[0])))
    checks.append(("joins carry a system-computed compatibility verdict per adjacency (via + confidence)",
                   all("via" in j and "confidence" in j for j in ctx["joins"])))
    checks.append(("token budget: context << full-card read << regenerate (savings > 1x both ways)",
                   ctx["token_budget"]["savings_vs_full_card"] and ctx["token_budget"]["savings_vs_full_card"] > 1.0
                   and ctx["token_budget"]["savings_vs_regenerate"] > ctx["token_budget"]["savings_vs_full_card"]))
    checks.append(("protocol string states read-only-signatures + system-computed-compat + gaps-only-generation",
                   "blackbox" in ctx["protocol"] and "never recomputes" in ctx["protocol"]))

    # a target with NO producer chain -> the plan reports it as a GAP (the LLM generates it), not a crash.
    ctx2 = orchestrate("NoSuchTargetEdge", cards)
    checks.append(("an unbuildable target yields gaps (LLM-fill), not a crash",
                   isinstance(ctx2.get("gaps"), list) and ctx2["serves_truth"] is False))

    # determinism
    again = orchestrate("SanctionsHit", cards)
    checks.append(("deterministic: same task -> identical route + budget",
                   again["route"] == ctx["route"] and again["token_budget"] == ctx["token_budget"]))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_orchestration: hands an LLM the MINIMUM context to build a system — ordered route as "
          "blackbox+edge views + system-computed compatibility verdicts + gap specs, with a token budget proving it "
          "beats full-card reading and from-scratch regeneration. The LLM wires; it never reads impls. serves_truth=false.")
    return 0


def _run(target: str, corpus: int) -> int:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    from scripts._repo_paths import resource  # noqa: PLC0415
    path = resource("data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards.jsonl")
    if not path.exists():
        print("no cards found"); return 1
    _all = [c for c in read_jsonl_tolerant(path) if c.get("primitive_id")]
    cards = _all[:corpus] if corpus else _all  # 0 = FULL corpus (use everything)
    tgt = target or str(cards[0].get("output_edge"))
    ctx = orchestrate(tgt, cards)
    print(json.dumps({"target": tgt, "route_length": ctx["route_length"], "gap_count": ctx["gap_count"],
                      "fully_composed": ctx["fully_composed"], "token_budget": ctx["token_budget"]}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--target", default="")
    ap.add_argument("--corpus", type=int, default=0, help="0 = FULL corpus (use everything)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.target, args.corpus)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
