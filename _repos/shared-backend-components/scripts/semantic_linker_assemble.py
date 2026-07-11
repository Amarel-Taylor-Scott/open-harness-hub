#!/usr/bin/env python3
"""semantic_linker_assemble — the ASSEMBLER (graph_apply) of the semantic linker.

Pipeline (owner vision 2026-07-09; research bundle primitive_registry_50m_*):

    intent -> plan-IR -> [semantic_linker_resolve] resolve to verified primitives + blockers
           -> [THIS MODULE] deterministic ASSEMBLE: wire the locked primitives by dataflow, insert typed ADAPTERS
              where declared edges don't chain, emit a mountable wiring artifact + carry RESIDUAL holes
           -> graph_verify (tests/policy/token ledger).

This is the "deterministic assembler" step. It takes a RESOLVE result (the lock + resolved steps, each with a
primitive and its declared input/output edges) and produces, DETERMINISTICALLY (0 model tokens):
  - a DATAFLOW WIRING: for each step, which prior var feeds it, and whether the producer's output_edge chains to
    the consumer's input_edge (an exact/token match) or needs a typed ADAPTER (from_edge -> to_edge);
  - a mountable ARTIFACT: thin wiring that mounts each verified primitive VERBATIM (our measured 0-token win — the
    LLM never re-emits an implementation; the assembler emits the wiring from declared edges);
  - the LOCK (capability -> primitive_id) + RESIDUAL holes (the novel code the model still authors) carried through.

Discipline: the assembler NEVER re-implements a primitive and NEVER silently drops a broken edge — an unchainable
edge becomes an explicit adapter requirement (a residual-adapter), and an unresolved capability stays a residual.
serves_truth=false: the artifact is a candidate composition (a plan/wiring), not executed, not promoted.

Boundaries (concurrent Codex lane): consumes semantic_linker_resolve (this lane) + the primitive DATA from
primitive_semantic_abi_registry (Codex); the LIVE token number is semantic_linker_long_session_benchmark (Codex).

    PYTHONPATH=. python3 scripts/semantic_linker_assemble.py --self-test
    PYTHONPATH=. python3 scripts/semantic_linker_assemble.py --demo     # resolve+assemble create-user on the real store
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts import semantic_linker_resolve as _resolve  # noqa: E402  REUSE: resolve/blockers/edge helpers


def _fn_name(card: dict[str, Any], capability: str) -> str:
    """A stable snake_case wiring name for a primitive (from its slug/title, else the capability)."""
    base = str(card.get("slug") or card.get("title") or _resolve._capability_words(capability))
    return re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_") or "step"


def _edges_chain(out_edge: object, in_edge: object) -> tuple[bool, str]:
    """Do a producer output_edge and a consumer input_edge chain? Returns (ok, match_kind):
    exact (identical normalized), token (share a significant token), or none (adapter required)."""
    o, i = str(out_edge or "").strip(), str(in_edge or "").strip()
    if not i:
        return True, "unconstrained"          # consumer declares no input edge -> cannot disprove
    if o and o.lower() == i.lower():
        return True, "exact"
    if _resolve._norm_edge(o) & _resolve._norm_edge(i):
        return True, "token"
    return False, "none"


def assemble(resolve_result: dict[str, Any], *, cards: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    """Deterministically assemble a resolve result into a wired artifact + adapter list + carried residuals."""
    idx = _resolve._card_index(cards)
    resolved = resolve_result.get("resolved", [])
    residual = resolve_result.get("residual", [])
    # producers: var -> {primitive_id, output_edge, fn}
    producers: dict[str, dict[str, Any]] = {}
    for step in resolved:
        card = idx.get(str(step.get("primitive_id"))) or {}
        producers[step["var"]] = {"primitive_id": step.get("primitive_id"),
                                  "output_edge": card.get("output_edge"),
                                  "fn": _fn_name(card, step.get("capability", ""))}

    wiring: list[dict[str, Any]] = []
    adapters: list[dict[str, Any]] = []
    _RANK = {"exact": 3, "token": 2, "unconstrained": 1}
    for step in resolved:
        card = idx.get(str(step.get("primitive_id"))) or {}
        in_edge = card.get("input_edge")
        # the primary upstream dependency = the producing input whose output_edge BEST chains with this input_edge
        # (exact > token > unconstrained > none) — so insert(u, d) wires from `d:PasswordDigest`, not `u:ValidatedUser`.
        up_key, best_rank = None, -1
        for v in step.get("inputs", []):
            cand_key = str(v).split(".")[0]
            if cand_key not in producers:
                continue
            ok, kind = _edges_chain(producers[cand_key]["output_edge"], in_edge)
            rank = _RANK.get(kind, 0) if ok else 0
            if rank > best_rank:
                up_key, best_rank = cand_key, rank
        prod = producers.get(up_key) if up_key else None
        if prod:
            ok, kind = _edges_chain(prod["output_edge"], in_edge)
            edge = {"from_var": up_key, "from_edge": prod["output_edge"], "to_var": step["var"],
                    "to_capability": step.get("capability"), "to_edge": in_edge, "match": kind}
            if not ok:
                adapter = {"from_edge": prod["output_edge"], "to_edge": in_edge, "for_step": step["var"],
                           "kind": "typed_adapter", "reason": "declared edges do not chain",
                           "status": "residual_adapter"}
                edge["adapter"] = adapter
                adapters.append(adapter)
            wiring.append(edge)
        else:  # source step (consumes only request/external inputs)
            wiring.append({"from_var": None, "from_edge": None, "to_var": step["var"],
                           "to_capability": step.get("capability"), "to_edge": in_edge, "match": "source"})

    artifact = _emit_artifact(resolve_result.get("plan", "plan"), resolved, producers, residual, adapters, idx)
    # deterministic-composition = the 0-token win: every step resolved AND every edge chains (no residual, no adapter)
    deterministic_composition = (not residual) and (not adapters)
    assembly_valid = not residual  # adapters are allowed (they're declared residual-adapters), unresolved caps are not
    return {"plan": resolve_result.get("plan"), "wiring": wiring, "adapters": adapters, "residual": residual,
            "lock": resolve_result.get("lock", {}), "artifact": artifact,
            "assembly_valid": assembly_valid, "deterministic_composition": deterministic_composition,
            "n_mounted": len(resolved), "n_adapters": len(adapters), "n_residual": len(residual),
            "candidate": True, "serves_truth": False}


def _emit_artifact(plan_name: str, resolved: list[dict[str, Any]], producers: dict[str, Any],
                   residual: list[dict[str, Any]], adapters: list[dict[str, Any]], idx: dict[str, Any]) -> str:
    """Emit the mountable wiring artifact (thin wiring; verified primitives mounted verbatim, NEVER re-implemented).
    This text is what the deterministic assembler would write — the 0-token composition surface."""
    fn = re.sub(r"[^a-z0-9]+", "_", str(plan_name).lower()).strip("_") or "assembled"
    lines = [f"# assembled: {plan_name}  (DETERMINISTIC wiring — verified primitives mounted verbatim; serves_truth=false)",
             f"def {fn}(request):"]
    for step in resolved:
        card = idx.get(str(step.get("primitive_id"))) or {}
        name = _fn_name(card, step.get("capability", ""))
        args = ", ".join(step.get("inputs", []) or ["request"])
        pid, ie, oe = step.get("primitive_id"), card.get("input_edge"), card.get("output_edge")
        note = f"  # {pid}  [{ie} -> {oe}]"
        adapt = next((a for a in adapters if a["for_step"] == step["var"]), None)
        if adapt:
            lines.append(f"    {step['var']}_in = adapt__{re.sub(r'[^a-z0-9]+','_',str(adapt['from_edge']).lower())}"
                         f"__to__{re.sub(r'[^a-z0-9]+','_',str(adapt['to_edge']).lower())}({args})  # RESIDUAL ADAPTER")
            args = f"{step['var']}_in"
        lines.append(f"    {step['var']} = {name}({args}){note}")
    for r in residual:
        lines.append(f"    # RESIDUAL (LLM authors): {r['var']} = <{r['capability']}>({', '.join(r.get('inputs', []))})"
                     f"  reason: {r.get('reason')}")
    last = resolved[-1]["var"] if resolved else "request"
    lines.append(f"    return {last}")
    return "\n".join(lines)


def link_and_assemble(plan: Any, *, cards: Optional[list[dict[str, Any]]] = None, retriever=None,
                      k: int = 8, min_score: float = _resolve.DEFAULT_MIN_SCORE) -> dict[str, Any]:
    """graph_solve + graph_apply: resolve the plan to verified primitives, then deterministically assemble."""
    resolved = _resolve.link(plan, retriever=retriever, cards=cards, k=k, min_score=min_score)
    asm = assemble(resolved, cards=cards)
    asm["token_projection"] = resolved.get("token_projection")
    asm["resolve_coverage"] = resolved.get("coverage")
    return asm


# ================================================================================================================
# Self-test
# ================================================================================================================
def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    cards = _resolve._fixture_cards()
    retr = _resolve._keyword_retriever(cards)

    # (1) FULL ASSEMBLE: create-user resolves 5/5 -> wired end-to-end, deterministic-composition (no residual/adapter).
    asm = link_and_assemble(_resolve._CREATE_USER_PLAN, cards=cards, retriever=retr)
    checks.append((f"assemble create-user: {asm['n_mounted']} mounted, {asm['n_adapters']} adapters, "
                   f"{asm['n_residual']} residual, det_composition={asm['deterministic_composition']}",
                   asm["n_mounted"] == 5 and asm["assembly_valid"] and asm["deterministic_composition"],
                   f"valid={asm['assembly_valid']}"))

    # (2) ARTIFACT: the emitted wiring mounts each LOCKED primitive verbatim (its id appears) and RETURNS the sink.
    art = asm["artifact"]
    lock_ids = set(asm["lock"].values())
    checks.append(("artifact mounts every locked primitive verbatim + returns the sink var",
                   bool(lock_ids) and all(pid in art for pid in lock_ids) and art.strip().endswith("return v"),
                   art.splitlines()[-1]))

    # (3) ADAPTER: when a producer's output_edge does NOT chain to the next input_edge, an explicit typed adapter is
    #     inserted (never a silent mismatch). Build a 2-step plan whose edges deliberately don't meet.
    mism = [
        {"primitive_id": "p:a", "title": "Make Alpha", "blackbox": "produces an alpha token.",
         "input_edge": "Seed", "output_edge": "AlphaToken", "effects": [], "candidate": True, "serves_truth": False},
        {"primitive_id": "p:b", "title": "Need Beta", "blackbox": "consumes a beta widget.",
         "input_edge": "BetaWidget", "output_edge": "Done", "effects": [], "candidate": True, "serves_truth": False},
    ]
    mplan = {"name": "mm", "steps": [{"var": "a", "capability": "make.alpha", "in": ["seed"]},
                                     {"var": "b", "capability": "need.beta", "in": ["a"]}]}
    masm = assemble(_resolve.resolve_plan(mplan, retriever=_resolve._keyword_retriever(mism), cards=mism), cards=mism)
    adapter_edge = next((w for w in masm["wiring"] if w.get("adapter")), None)
    checks.append(("edge mismatch -> explicit typed adapter (AlphaToken -> BetaWidget), not a silent drop",
                   adapter_edge is not None and masm["n_adapters"] == 1
                   and "RESIDUAL ADAPTER" in masm["artifact"], f"adapters={masm['n_adapters']}"))

    # (4) RESIDUAL carried: an unresolved capability stays a residual hole in the artifact (assembly_valid False).
    gap = {**_resolve._CREATE_USER_PLAN, "steps": _resolve._CREATE_USER_PLAN["steps"] + [
        {"var": "z", "capability": "cryptography.elliptic-curve-sign", "in": ["v"]}]}
    gasm = link_and_assemble(gap, cards=cards, retriever=retr)
    checks.append(("unresolved capability stays a RESIDUAL hole (assembly not valid, not faked)",
                   gasm["n_residual"] == 1 and not gasm["assembly_valid"]
                   and "RESIDUAL (LLM authors)" in gasm["artifact"], f"residual={gasm['n_residual']}"))

    # (5) DETERMINISM: same input -> byte-identical assembly (artifact + wiring).
    a1 = json.dumps(assemble(_resolve.link(_resolve._CREATE_USER_PLAN, retriever=retr, cards=cards), cards=cards), sort_keys=True)
    a2 = json.dumps(assemble(_resolve.link(_resolve._CREATE_USER_PLAN, retriever=retr, cards=cards), cards=cards), sort_keys=True)
    checks.append(("assembly deterministic (byte-identical twice)", a1 == a2, "hash match"))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - semantic_linker_assemble: dataflow wiring + typed adapters + mountable "
          f"artifact (verbatim mount = 0-token composition; residuals + adapters explicit)")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Semantic linker ASSEMBLER: resolve result -> deterministic wiring + adapters + artifact.")
    ap.add_argument("--self-test", action="store_true", help="offline end-to-end gate")
    ap.add_argument("--demo", action="store_true", help="resolve+assemble the create-user plan on the REAL facet store")
    ap.add_argument("--plan", default=None, help="path to a JSON plan to resolve+assemble against the real store")
    ap.add_argument("--k", type=int, default=8)
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.demo or args.plan:
        from scripts import primitive_facet_enrichment as _facet  # noqa: PLC0415
        cards = _facet.load_cards(sample=0)
        plan = json.loads(Path(args.plan).read_text()) if args.plan else _resolve._CREATE_USER_PLAN
        asm = link_and_assemble(plan, cards=cards, k=args.k)
        print(json.dumps({k: v for k, v in asm.items() if k != "artifact"}, indent=2))
        print("\n# ---- assembled artifact ----\n" + asm["artifact"])
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
