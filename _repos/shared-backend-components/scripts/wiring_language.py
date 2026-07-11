#!/usr/bin/env python3
"""scripts.wiring_language — the RELATIONSHIP CODE contract: an LLM outputs a tiny ordering/integration
expression over primitives, and DETERMINISTIC builders compile it — all of it, or every compilable portion.

The owner's north-star sentence, made a module: "the LLM only needs to output some basic ordering and
integration logic, and then deterministic systems string it together." The language is deliberately tiny —
relationships only, no bodies, no control flow the builder can't verify:

    A >> B >> C            sequence: A's output feeds B, B's output feeds C
    A >> (B | C) >> D      alternates: B and C are interchangeable candidates for the middle step
    A >> loop[ B >> C ] >> D   LOOP block: the body iterates (verified CYCLIC: the body's last output
                           canonical type must equal its first input type so it can feed itself);
                           A runs before the loop, D consumes the loop's exit output — layers of
                           primitives inside a loop with work before and after, per the 7-primitive
                           model where Loop is itself a primitive kind
    branch(X | Y)          typed branch (If Statement primitive): BOTH arms must resolve and agree on
                           the same canonical output type — the join downstream is verifiable either way
    Blocks nest: loop[ B >> loop[ C ] >> E ] compiles recursively, innermost first.

Identifiers resolve deterministically against the corpus, most-specific first: exact ``primitive_id`` →
exact canonical TYPE name (any producer of that type) → corpus-language token fold (the standardized-
language fold from the decompose front door). Every join is validated by canonical edge equality; an
incompatible join becomes a FLAGGED gap, never a crash — and the compiler still emits every maximal
compilable SEGMENT (partial compilation: components that help the agent start and cut token burn even
when the whole wiring can't close). serves_truth=false throughout — a compiled wiring is a candidate plan.

    PYTHONPATH=. python3 scripts/wiring_language.py --self-test
    PYTHONPATH=. python3 scripts/wiring_language.py --compile "RawRecord >> NormalizedRecord >> DedupedRecord"
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts.primitive_runtime import (  # noqa: E402  REUSE: the ONE canonicalizer + standardized-language fold
    _corpus_type_language,
    _fold_to_corpus_language,
    canonicalize_edge,
)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_SEQUENCE_OPERATOR = ">>"        # the ONLY ordering operator (A >> B: A's output feeds B)
_ALTERNATE_OPERATOR = "|"        # interchangeable candidates inside one step: (B | C)
_TOKEN_RE = re.compile(r"[A-Za-z0-9_:+.-]+")


def parse_wiring(text: str) -> list[list[str]]:
    """Relationship code -> ordered steps, each a list of alternate identifiers. Deterministic, no eval:
    split on ``>>``, strip one optional level of parens, split alternates on ``|``. Malformed segments
    (empty steps, stray operators) raise ValueError with the offending segment named."""
    steps: list[list[str]] = []
    for raw_step in str(text).split(_SEQUENCE_OPERATOR):
        segment = raw_step.strip()
        if segment.startswith("(") and segment.endswith(")"):
            segment = segment[1:-1]
        alternates = [a.strip() for a in segment.split(_ALTERNATE_OPERATOR)]
        idents = [a for a in alternates if a]
        if not idents or any(not _TOKEN_RE.fullmatch(i) for i in idents):
            raise ValueError(f"malformed wiring segment: {raw_step.strip()!r}")
        steps.append(idents)
    if len(steps) < 1:
        raise ValueError("empty wiring expression")
    return steps


def _corpus_indexes(cards: list[dict[str, Any]]) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    """(by primitive_id, producers by canonical output type) — computed once per compile."""
    by_id: dict[str, dict] = {}
    producers: dict[str, list[dict]] = {}
    for card in cards:
        pid = str(card.get("primitive_id") or "")
        if pid and pid not in by_id:
            by_id[pid] = card
        out_type = canonicalize_edge(card.get("output_edge"))
        if out_type and out_type.lower() not in ("unknown",):
            producers.setdefault(out_type, []).append(card)
    for hits in producers.values():
        hits.sort(key=lambda c: str(c.get("primitive_id")))  # deterministic pick order
    return by_id, producers


def resolve_identifier(ident: str, by_id: dict[str, dict], producers: dict[str, list[dict]],
                       language: dict[str, frozenset]) -> Optional[dict[str, Any]]:
    """Most-specific-first resolution: exact primitive_id -> exact type name (its first producer) ->
    standardized-language fold of the identifier to a spoken type (its first producer). None = unresolved."""
    if ident in by_id:
        return by_id[ident]
    as_type = canonicalize_edge(ident)
    if as_type in producers:
        return producers[as_type][0]
    folded = _fold_to_corpus_language(as_type, None if " " in ident else ident, language)
    if folded and folded in producers:
        return producers[folded][0]
    return None


_LOOP_OPEN = "loop["          # structured LOOP block opener (body = a nested wiring)
_BRANCH_OPEN = "branch("      # typed branch opener (both arms must agree on output type)


def _split_top_level(text: str, separator: str) -> list[str]:
    """Split on ``separator`` only at bracket depth 0 — the recursive grammar's one primitive."""
    parts, depth, start = [], 0, 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth -= 1
        elif depth == 0 and text.startswith(separator, i):
            parts.append(text[start:i])
            i += len(separator)
            start = i
            continue
        i += 1
    parts.append(text[start:])
    return parts


def parse_wiring_tree(text: str) -> list[dict[str, Any]]:
    """The STRUCTURED grammar: sequence of nodes, each a step / loop-block / branch. Recursive, deterministic,
    no eval; malformed segments raise with the segment named. Nodes:
    {"kind": "step", "alternates": [...]} | {"kind": "loop", "body": [nodes]} | {"kind": "branch", "arms": [...]}"""
    nodes: list[dict[str, Any]] = []
    for raw in _split_top_level(str(text), _SEQUENCE_OPERATOR):
        segment = raw.strip()
        if segment.startswith(_LOOP_OPEN) and segment.endswith("]"):
            nodes.append({"kind": "loop", "body": parse_wiring_tree(segment[len(_LOOP_OPEN):-1].strip())})
            continue
        if segment.startswith(_BRANCH_OPEN) and segment.endswith(")"):
            arms = [a.strip() for a in _split_top_level(segment[len(_BRANCH_OPEN):-1], _ALTERNATE_OPERATOR)]
            if len(arms) < 2 or any(not _TOKEN_RE.fullmatch(a) for a in arms):
                raise ValueError(f"malformed branch: {segment!r}")
            nodes.append({"kind": "branch", "arms": arms})
            continue
        if segment.startswith("(") and segment.endswith(")"):
            segment = segment[1:-1]
        alternates = [a.strip() for a in _split_top_level(segment, _ALTERNATE_OPERATOR)]
        idents = [a for a in alternates if a]
        if not idents or any(not _TOKEN_RE.fullmatch(i) for i in idents):
            raise ValueError(f"malformed wiring segment: {raw.strip()!r}")
        nodes.append({"kind": "step", "alternates": idents})
    if not nodes:
        raise ValueError("empty wiring expression")
    return nodes


def _compile_nodes(nodes: list[dict[str, Any]], by_id: dict, producers: dict, language: dict,
                   cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Recursive builder core: resolve every node to OUTWARD edges (a loop/branch block gets the edges of
    its compiled interior), validate joins at THIS layer, recurse into blocks. Gaps carry the layer path."""
    views: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    edges: list[Optional[tuple[str, str]]] = []  # per node: (input_type, output_type) or None
    for index, node in enumerate(nodes):
        if node["kind"] == "step":
            pick = None
            for ident in node["alternates"]:
                pick = resolve_identifier(ident, by_id, producers, language)
                if pick is not None:
                    break
            if pick is None:
                gaps.append({"kind": "unresolved_step", "step": index, "alternates": node["alternates"],
                             **BOUNDARY})
                edges.append(None)
            else:
                edges.append((canonicalize_edge(pick.get("input_edge")), canonicalize_edge(pick.get("output_edge"))))
            views.append({"step": index, "kind": "step", "alternates": node["alternates"],
                          "resolved_primitive_id": pick.get("primitive_id") if pick else None})
        elif node["kind"] == "branch":
            arm_picks = [resolve_identifier(a, by_id, producers, language) for a in node["arms"]]
            arm_outs = {canonicalize_edge(p.get("output_edge")) for p in arm_picks if p}
            if any(p is None for p in arm_picks):
                gaps.append({"kind": "unresolved_branch_arm", "step": index, "arms": node["arms"], **BOUNDARY})
                edges.append(None)
            elif len(arm_outs) != 1:
                gaps.append({"kind": "branch_arms_type_disagree", "step": index,
                             "arm_output_types": sorted(arm_outs), **BOUNDARY})
                edges.append(None)
            else:  # both arms verified: outward input = first arm's input, output = the agreed type
                edges.append((canonicalize_edge(arm_picks[0].get("input_edge")), arm_outs.pop()))
            views.append({"step": index, "kind": "branch", "arms": node["arms"],
                          "resolved_primitive_ids": [p.get("primitive_id") if p else None for p in arm_picks]})
        else:  # loop block: compile the interior, then verify the CYCLIC contract
            inner = _compile_nodes(node["body"], by_id, producers, language, cards)
            first, last = inner["edges"][0], inner["edges"][-1]
            cyclic = bool(first and last and first[0] == last[1])
            if not inner["fully_compiled"]:
                gaps.extend({**g, "layer": f"loop[{index}].{g.get('layer', 'body')}"} for g in inner["gaps"])
            if not cyclic and first and last:
                gaps.append({"kind": "loop_not_cyclic", "step": index,
                             "body_input_type": first[0], "body_output_type": last[1],
                             "needed_input_type": last[1], "needed_output_type": first[0], **BOUNDARY})
            edges.append((first[0], last[1]) if (first and last) else None)
            views.append({"step": index, "kind": "loop", "cyclic_verified": cyclic, "body": inner["steps"]})
    joins: list[dict[str, Any]] = []
    for index in range(len(nodes) - 1):
        up, down = edges[index], edges[index + 1]
        if up is None or down is None:
            joins.append({"join": index, "compatible": False, "reason": "unresolved endpoint"})
            continue
        compatible = bool(up[1]) and up[1] == down[0]
        joins.append({"join": index, "compatible": compatible, "upstream_output": up[1],
                      "downstream_input": down[0],
                      "reason": "canonical types match" if compatible else "canonical type mismatch"})
        if not compatible:
            gaps.append({"kind": "incompatible_join", "join": index,
                         "needed_input_type": up[1], "needed_output_type": down[0], **BOUNDARY})
    return {"steps": views, "joins": joins, "gaps": gaps, "edges": edges,
            "fully_compiled": not gaps}


def compile_structured_wiring(text: str, cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Compile the STRUCTURED grammar (loops with before/after, nesting, typed branches). Every block is
    verified at its own layer; a compiled loop's outward interface is its body's (input, exit-output) —
    the same shape as a GROUP card, so a verified block can later be minted as one and peeled by the
    composer like any other layered primitive."""
    by_id, producers = _corpus_indexes(cards)
    language = _corpus_type_language(cards)
    result = _compile_nodes(parse_wiring_tree(text), by_id, producers, language, cards)
    return {"record_type": "compiled_wiring", "wiring": text, "grammar": "structured",
            "steps": result["steps"], "joins": result["joins"], "gaps": result["gaps"],
            "fully_compiled": result["fully_compiled"],
            "builders": {"full_route": result["fully_compiled"], "segment_builder": True}, **BOUNDARY}


def compile_wiring(text: str, cards: list[dict[str, Any]]) -> dict[str, Any]:
    """The deterministic builder: relationship code -> validated route (full or PORTIONS). Emits per-step
    resolutions (signature views only), per-join verdicts (canonical edge equality), flagged gaps for
    unresolved identifiers or incompatible joins, and every maximal compilable SEGMENT so partial results
    still hand the agent working components."""
    if _LOOP_OPEN in text or _BRANCH_OPEN in text:  # structured grammar -> the recursive builder
        return compile_structured_wiring(text, cards)
    steps = parse_wiring(text)
    by_id, producers = _corpus_indexes(cards)
    language = _corpus_type_language(cards)
    resolved: list[Optional[dict[str, Any]]] = []
    step_views: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    for index, alternates in enumerate(steps):
        pick = None
        for ident in alternates:  # first resolvable alternate wins (alternates are interchangeable by contract)
            pick = resolve_identifier(ident, by_id, producers, language)
            if pick is not None:
                break
        resolved.append(pick)
        if pick is None:
            gaps.append({"kind": "unresolved_step", "step": index, "alternates": alternates, **BOUNDARY})
        step_views.append({
            "step": index, "alternates": alternates,
            "resolved_primitive_id": pick.get("primitive_id") if pick else None,
            "input_edge": pick.get("input_edge") if pick else None,
            "output_edge": pick.get("output_edge") if pick else None,
        })
    joins: list[dict[str, Any]] = []
    for index in range(len(resolved) - 1):
        upstream, downstream = resolved[index], resolved[index + 1]
        if upstream is None or downstream is None:
            joins.append({"join": index, "compatible": False, "reason": "unresolved endpoint"})
            continue
        out_type = canonicalize_edge(upstream.get("output_edge"))
        in_type = canonicalize_edge(downstream.get("input_edge"))
        compatible = bool(out_type) and out_type == in_type
        joins.append({"join": index, "compatible": compatible,
                      "upstream_output": out_type, "downstream_input": in_type,
                      "reason": "canonical types match" if compatible else "canonical type mismatch"})
        if not compatible:
            gaps.append({"kind": "incompatible_join", "join": index,
                         "needed_input_type": out_type, "needed_output_type": in_type, **BOUNDARY})
    # maximal compilable SEGMENTS: runs of resolved steps whose internal joins are all compatible
    segments: list[dict[str, Any]] = []
    run_start: Optional[int] = None
    for index in range(len(resolved)):
        usable = resolved[index] is not None and (index == 0 or run_start is None or joins[index - 1]["compatible"])
        if resolved[index] is not None and run_start is None:
            run_start = index
        elif run_start is not None and (resolved[index] is None or not joins[index - 1]["compatible"]):
            if index - run_start >= 1:
                segments.append({"from_step": run_start, "to_step": index - 1,
                                 "primitive_ids": [r["primitive_id"] for r in resolved[run_start:index] if r]})
            run_start = index if resolved[index] is not None else None
        _ = usable
    if run_start is not None:
        segments.append({"from_step": run_start, "to_step": len(resolved) - 1,
                         "primitive_ids": [r["primitive_id"] for r in resolved[run_start:] if r]})
    fully_compiled = not gaps
    return {"record_type": "compiled_wiring", "wiring": text, "steps": step_views, "joins": joins,
            "gaps": gaps, "segments": segments, "fully_compiled": fully_compiled,
            "builders": {"full_route": fully_compiled, "segment_builder": bool(segments)}, **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    mk = lambda pid, ie, oe: {"primitive_id": pid, "title": pid, "blackbox": f"{ie} to {oe}",  # noqa: E731
                              "input_edge": ie, "output_edge": oe, **BOUNDARY}
    cards = [mk("p:ingest", "RawRecord", "NormalizedRecord"),
             mk("p:dedup", "NormalizedRecord", "DedupedRecord"),
             mk("p:dedup2", "NormalizedRecord", "DedupedRecord"),
             mk("p:score", "DedupedRecord", "RiskScore"),
             mk("p:island", "Image", "ResizedImage")]
    # (a) grammar: sequence + alternates parse; malformed raises with the segment named
    checks.append(("sequence + alternates parse", parse_wiring("a >> (b | c) >> d") == [["a"], ["b", "c"], ["d"]]))
    try:
        parse_wiring("a >> >> b")
        checks.append(("malformed wiring raises", False))
    except ValueError:
        checks.append(("malformed wiring raises", True))
    # (b) full compile by exact ids AND by type names (the standardized language)
    by_ids = compile_wiring("p:ingest >> p:dedup >> p:score", cards)
    checks.append(("exact-id wiring fully compiles", by_ids["fully_compiled"]
                   and by_ids["builders"]["full_route"] and len(by_ids["segments"]) == 1))
    by_types = compile_wiring("NormalizedRecord >> DedupedRecord >> RiskScore", cards)
    checks.append(("type-name wiring resolves producers and compiles",
                   by_types["fully_compiled"]
                   and by_types["steps"][1]["resolved_primitive_id"] in ("p:dedup", "p:dedup2")))
    # (c) alternates: first resolvable wins deterministically
    alt = compile_wiring("p:ingest >> (p:missing | p:dedup) >> p:score", cards)
    checks.append(("alternates pick the first resolvable candidate",
                   alt["fully_compiled"] and alt["steps"][1]["resolved_primitive_id"] == "p:dedup"))
    # (d) PARTIAL compilation: an incompatible join flags a gap and still emits both segments
    partial = compile_wiring("p:ingest >> p:dedup >> p:island", cards)
    checks.append(("incompatible join is a flagged gap, never a crash",
                   not partial["fully_compiled"]
                   and any(g["kind"] == "incompatible_join" for g in partial["gaps"])))
    checks.append(("partial compile still emits the compilable segments",
                   partial["builders"]["segment_builder"] and len(partial["segments"]) == 2
                   and partial["segments"][0]["primitive_ids"] == ["p:ingest", "p:dedup"]))
    # (e) unresolved identifiers flag, and the gap record speaks the Code-Factory gap-spec language
    unresolved = compile_wiring("p:ingest >> TotallyUnknownThing", cards)
    checks.append(("unresolved identifier is a flagged gap", not unresolved["fully_compiled"]
                   and any(g["kind"] == "unresolved_step" for g in unresolved["gaps"])))
    # (f) STRUCTURED grammar: loops with before/after, nesting, typed branches — all builder-verified
    looped = compile_wiring("p:ingest >> loop[ p:selfcycle ] >> p:dedup", cards + [
        mk("p:selfcycle", "NormalizedRecord", "NormalizedRecord")])
    checks.append(("a CYCLIC loop body verifies and wires with work before AND after",
                   looped["fully_compiled"] and looped["steps"][1]["kind"] == "loop"
                   and looped["steps"][1]["cyclic_verified"]))
    not_cyclic = compile_wiring("p:ingest >> loop[ p:dedup ] >> p:score", cards)
    checks.append(("a NON-cyclic loop body is a flagged gap speaking the gap-spec language",
                   not not_cyclic["fully_compiled"]
                   and any(g["kind"] == "loop_not_cyclic" and g.get("needed_output_type") for g in not_cyclic["gaps"])))
    nested = compile_wiring("loop[ p:selfcycle >> loop[ p:selfcycle ] ]", cards + [
        mk("p:selfcycle", "NormalizedRecord", "NormalizedRecord")])
    checks.append(("loops NEST (recursive compile, innermost first)",
                   nested["fully_compiled"] and nested["steps"][0]["body"][1]["kind"] == "loop"))
    agree = compile_wiring("p:ingest >> branch(p:dedup | p:dedup2) >> p:score", cards)
    checks.append(("a typed branch verifies BOTH arms agree on output type and wires through",
                   agree["fully_compiled"] and agree["steps"][1]["kind"] == "branch"))
    disagree = compile_wiring("p:ingest >> branch(p:dedup | p:island)", cards)
    checks.append(("branch arms with DIFFERENT output types are a flagged gap",
                   not disagree["fully_compiled"]
                   and any(g["kind"] == "branch_arms_type_disagree" for g in disagree["gaps"])))

    # (f2) determinism + governance
    checks.append(("compile is deterministic (byte-identical twice)",
                   json.dumps(compile_wiring("p:ingest >> p:dedup", cards), sort_keys=True)
                   == json.dumps(compile_wiring("p:ingest >> p:dedup", cards), sort_keys=True)))
    checks.append(("everything is candidate/serves_truth=false",
                   by_ids["serves_truth"] is False and all(g["serves_truth"] is False for g in partial["gaps"])))
    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - wiring_language: the LLM's output contract is a TINY relationship expression "
          "(A >> (B | C) >> D) and the deterministic builder compiles it — identifiers resolve exact-id -> "
          "type-name -> standardized-language fold; joins validated by canonical edges; incompatible joins "
          "and unknown names become flagged gaps; PARTIAL compilation emits every maximal working segment. "
          "serves_truth=false.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--compile", metavar="WIRING", default=None, help="compile one wiring over the verified corpus")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.compile:
        from scripts.run_token_savings_experiments import _load_cards  # noqa: PLC0415  the ONE corpus loader
        print(json.dumps(compile_wiring(args.compile, _load_cards(0)), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
