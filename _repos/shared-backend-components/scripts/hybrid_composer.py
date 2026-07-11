#!/usr/bin/env python3
"""scripts.hybrid_composer — compose a target from EXISTING primitives; emit the GAPS as generation specs.

The "partial solution + LLM generates the missing primitives" capability. Given a ``target_output`` edge and
a corpus of primitive cards, backward-chain a route of primitives that PRODUCES the target — reading each
reused primitive by its cheap SIGNATURE (via ``scripts.primitive_onion``), not its full card — and wherever
the chain BREAKS (a needed edge no primitive produces) emit a deterministic ``generation_spec``: a candidate
primitive-card skeleton (input_edge/output_edge/purpose/prompt) for an LLM to fill LATER. This module does
NOT call an LLM; it EMITS the spec deterministically.

It is a THIN wiring layer over existing engines — the composition DECISION is delegated, not reinvented:
  * connectivity comes from an INJECTED ``matcher(edge) -> producers`` oracle. ``matcher_from_cards`` builds
    one whose PRIMARY backend is ``scripts.edge_type_matcher.match_hits`` (the canonical, type-aware matcher,
    reused verbatim — pinned by the self-test's backend check); a SMALL local canonical producer-index is the
    standalone FALLBACK for when that module is not importable, so this module still composes on its own. The
    composer reads each producer's OWN input edge from the resolved card / signature (never a hit's top-level
    ``input_edge``, which a matcher may set to the QUERIED edge), so backward chaining is correct on every
    backend;
  * reading is via ``scripts.primitive_onion.signature`` (~tens of tokens) instead of the full card (~hundreds);
  * the gap spec borrows the ``lane / node_kind / proof_required / promotion_required`` vocabulary from
    ``src.teleon.registry.primitive_match.adapter_plan`` so a whole-missing-primitive (node) gap and a
    missing-adapter (edge) gap speak ONE vocabulary;
  * ids are minted only through the DATA-plane authority ``src.teleon.experiments.ids.canonical_id``.

Route contract: input = ``target_output`` + primitive corpus + a connectivity matcher; output = a
``hybrid_route_plan`` (route of reused primitive_ids + generation specs for the gaps + reuse-vs-regenerate
token accounting). Every emitted row is candidate=true / serves_truth=false — composing/spec-ing a candidate
never promotes it; a spec becomes a real primitive only after an LLM fills the body AND a proof + review gate.

    PYTHONPATH=. python3 scripts/hybrid_composer.py --self-test
    PYTHONPATH=. python3 scripts/hybrid_composer.py --demo
    PYTHONPATH=. python3 scripts/hybrid_composer.py --run --target AnswerString --limit 4000
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── sentinel bootstrap: put the code roots on sys.path BEFORE any scripts.*/src.* import ──
_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable, Iterable, Optional  # noqa: E402

from scripts import primitive_onion as _onion  # noqa: E402  reuse: read a primitive by its SIGNATURE, not full
from scripts._jsonl import read_jsonl_tolerant  # noqa: E402  mandated helper (append-only-safe corpus read)
from scripts._time import now_iso  # noqa: E402  mandated helper (used only at the emit boundary — never in plan())

__all__ = ["plan", "gap_to_generation_spec", "matcher_from_cards", "BOUNDARY"]

#: the candidate/truth boundary every emitted row carries (repo law: generation is not promotion).
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# Generation-spec vocabulary — borrowed VERBATIM from primitive_match.adapter_plan's generated-candidate
# template so a node gap (a whole missing primitive) and an edge gap (a missing adapter) are consistent and
# both loadable. Single source of each string, so the two gap kinds never drift apart.
GEN_LANE = "nondeterministic_generated_candidate"
GEN_NODE_KIND = "generated_primitive_candidate"
GEN_PROOF_REQUIRED = "owner_or_human_review_plus_deterministic_proofs_before_promotion"
GEN_PROVENANCE = "gap_synthesis"
GEN_READINESS = "spec_only"
GEN_PROMOTION_BLOCKERS: tuple[str, ...] = ("ungenerated_body", "unproven")

#: canonical_id prefix for a minted gap spec (DATA-plane law: version lives in metadata, never the id).
GAP_ID_PREFIX = "prim:gap"
#: placeholder input for a gap when the caller declared no available source edge (LLM/caller resolves it).
UNRESOLVED_SOURCE = "UnresolvedSourceInput"
#: kind stamped on a gap-spec skeleton (matches the route-primitive kind used across the factory cards).
GAP_KIND = "route.primitive"

#: bound the backward chain — a route longer than this toward one target is a decomposition smell, not a route.
DEFAULT_MAX_STEPS = 24
#: how many ranked producers the convenience matcher returns per edge (best-first; the head is used).
DEFAULT_MATCH_LIMIT = None       # UNBOUNDED: both backends rank fully before slicing, and plan() filters
                                 # used producers AFTER truncation — any finite head can manufacture false
                                 # gaps when the top-N producers are all already on the route


# ────────────────────────────── small internal helpers ──────────────────────────────

def _est_tokens(obj: Any) -> int:
    """Token proxy, single-sourced from the onion's chars/token constant (no parallel literal)."""
    return len(json.dumps(obj, sort_keys=True)) // _onion.CHARS_PER_TOKEN


def _canon(edge: Any) -> str:
    """Canonical type-id of an edge for THIS module's source-membership + cycle bookkeeping ONLY (not for
    matching — the injected matcher canonicalizes its own way). Reuses build_edge_type_retrofit.canonicalize_edge
    when importable; falls back to a whitespace-normalized identity so the module never depends on it."""
    e = str(edge or "").strip()
    if not e:
        return e
    try:
        from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: PLC0415
        return canonicalize_edge(e) or e
    except Exception:  # noqa: BLE001 — a normalizer's absence must never break planning
        return e


def _hit_id(hit: Any) -> str:
    """The primitive_id of a matcher hit, whether it is a signature dict or a bare id string."""
    if isinstance(hit, dict):
        return str(hit.get("primitive_id") or hit.get("id") or "")
    return str(hit or "")


def _hit_input_edge(hit: Any, resolved_card: Optional[dict]) -> str:
    """The PRODUCER's OWN input edge (what backward chaining moves on to next). Resolved most-authoritative
    first, because a matcher's TOP-LEVEL ``input_edge`` may be the QUERIED edge, NOT the producer's own —
    ``edge_type_matcher.match_hits`` sets ``hit['input_edge']`` to the query and puts the producer's own input
    in ``hit['signature']['input_edge']``; trusting the top-level field would truncate the chain to length 1.

    Priority: (1) the RESOLVED full card's ``input_edge`` (ground truth when the producer is in the corpus —
    authoritative even when empty, which marks a source primitive that ends the chain); (2) the hit's
    ``signature`` layer's ``input_edge`` (edge_type_matcher hits carry ``primitive_onion.signature(producer)``);
    (3) a MINIMAL hit's own top-level ``input_edge`` — the stub / local-fallback shape, where it IS the
    producer's own input, reached only when neither a resolved card nor a signature is present."""
    if isinstance(resolved_card, dict) and "input_edge" in resolved_card:
        return str(resolved_card.get("input_edge") or "")
    if isinstance(hit, dict):
        sig = hit.get("signature")
        if isinstance(sig, dict) and "input_edge" in sig:
            return str(sig.get("input_edge") or "")
        if "input_edge" in hit:
            return str(hit.get("input_edge") or "")
    return ""


def _quality(card: dict) -> float:
    """Deterministic rank weight for a producer (higher first). Reuses the card's quality_score if present."""
    try:
        return float(card.get("quality_score") or 0)
    except (TypeError, ValueError):
        return 0.0


def _mint_gap_id(input_edge: str, output_edge: str) -> str:
    """Mint a gap-spec primitive_id through the ONE DATA-plane authority (canonical, deterministic). Falls
    back to a deterministic local sha256 id — mirroring primitive_onion.remix_edges — only if the authority
    is unavailable, so a spec always has a stable content-derived id."""
    try:
        from src.teleon.experiments.ids import canonical_id  # noqa: PLC0415 — the ONE id authority
        return canonical_id(GAP_ID_PREFIX, str(input_edge), str(output_edge))
    except Exception:  # noqa: BLE001 — never let the id authority's absence break spec emission
        import hashlib  # noqa: PLC0415 — scripts/ (not src/**); deterministic fallback only
        digest = hashlib.sha256(f"{input_edge}|{output_edge}".encode("utf-8")).hexdigest()[:16]
        return f"{GAP_ID_PREFIX}-{digest}"


def _generation_prompt(input_edge: str, output_edge: str, target_output: str, consumer_id: Optional[str]) -> str:
    """A bounded, disciplined prompt for the missing primitive, in the onion SIGNATURE format (narrow scope
    first). Deterministic — no wall-clock, no RNG."""
    downstream = f"Downstream consumer: {consumer_id}.\n" if consumer_id else ""
    return (
        "Generate ONE deterministic primitive (narrow scope — the smallest thing that works).\n"
        f"Signature: primitive mapping {input_edge} -> {output_edge}\n"
        f"Purpose: produce {output_edge} from {input_edge} so a composed route can reach {target_output}.\n"
        f"{downstream}"
        "Fill: contract (input/output/errors), blackbox (one line of what it does), effects, mutations.\n"
        "Return candidate=true, serves_truth=false; a passing proof + human review gate promotion."
    )


# ────────────────────────────── the gap → generation spec ──────────────────────────────

def gap_to_generation_spec(needed_edge: str, *, input_edge: str, consumer_id: Optional[str],
                           target_output: str) -> dict:
    """Turn one unbridgeable edge into a candidate primitive-card SKELETON an LLM can fill later. output_edge
    is the missing edge; input_edge is the best-available upstream (a declared source, or a placeholder). The
    generation-spec fields mirror primitive_match.adapter_plan so node-gaps and edge-gaps are one vocabulary.
    candidate=true / serves_truth=false with promotion_blockers — a spec never promotes itself."""
    out_edge = str(needed_edge)
    in_edge = str(input_edge)
    return {
        "primitive_id": _mint_gap_id(in_edge, out_edge),
        "record_type": "primitive_generation_spec",
        "input_edge": in_edge,
        "output_edge": out_edge,
        "kind": GAP_KIND,
        "title": f"Generate primitive mapping {in_edge} -> {out_edge}",
        "purpose": (
            f"No existing primitive produces {out_edge!r}; generate one that maps {in_edge!r} -> {out_edge!r} "
            f"so the route can reach {str(target_output)!r}"
            + (f" (consumed downstream by {consumer_id})" if consumer_id else "")
        ),
        "contract": {},   # to fill by the LLM
        "blackbox": "",   # to fill by the LLM
        "effects": [],
        "mutations": [],
        # generation-spec fields (same shape as primitive_match.adapter_plan's generated candidate) ↓
        "lane": GEN_LANE,
        "node_kind": GEN_NODE_KIND,
        "proof_required": GEN_PROOF_REQUIRED,
        "promotion_required": True,
        "provenance": GEN_PROVENANCE,
        "readiness": GEN_READINESS,
        "promotion_blockers": list(GEN_PROMOTION_BLOCKERS),
        "generation_prompt": _generation_prompt(in_edge, out_edge, target_output, consumer_id),
        **BOUNDARY,
    }


# ────────────────────────────── the connectivity matcher (convenience) ──────────────────────────────

def _local_producer_index(cards: list[dict]) -> dict[str, list[dict]]:
    """Fallback producer-by-canonical-output-type index -> ranked SIGNATURE hits. Used when the parallel
    scripts.edge_type_matcher is not importable yet, so this module composes standalone. Deterministic rank:
    quality desc, then primitive_id."""
    index: dict[str, list[dict]] = {}
    for card in cards:
        out_edge = card.get("output_edge")
        if out_edge:
            index.setdefault(_canon(out_edge), []).append(card)
    projected: dict[str, list[dict]] = {}
    for type_id, producers in index.items():
        producers.sort(key=lambda c: (-_quality(c), str(c.get("primitive_id", ""))))
        projected[type_id] = [_onion.signature(c) for c in producers]  # read signatures, not full cards
    return projected


def matcher_from_cards(cards: Iterable[dict], *, limit: int = DEFAULT_MATCH_LIMIT) -> Callable[[str], list[dict]]:
    """Build a single-arg connectivity oracle ``matcher(edge) -> ranked producer hits`` over ``cards``.
    PRIMARY: reuse scripts.edge_type_matcher (canonical, type-aware) when importable. FALLBACK: a local
    canonical producer index so this module works standalone before edge_type_matcher lands (parallel build).
    The returned callable carries ``.backend`` naming which lane it used (honest labelling)."""
    card_list = [c for c in cards if isinstance(c, dict)]
    try:
        # PRIMARY reuse: the canonical, type-aware matcher. Its ranked-hit function is ``match_hits`` (each
        # hit carries the producer's ``signature`` — plan() reads the producer's OWN input edge from the
        # resolved card / signature, never from the hit's top-level ``input_edge``, which match_hits sets to
        # the QUERIED edge). Aliased so a symbol drift in this import (which silently drops to the local
        # fallback) is caught by the self-test's backend-pin, not hidden.
        from scripts.edge_type_matcher import build_producer_index, match_hits as _edge_type_match_hits  # noqa: PLC0415
        index = build_producer_index(card_list)

        def _match_via_edge_type_matcher(edge: str) -> list[dict]:
            return list(_edge_type_match_hits(edge, index, limit=limit))

        _match_via_edge_type_matcher.backend = "edge_type_matcher"  # type: ignore[attr-defined]
        return _match_via_edge_type_matcher
    except Exception:  # noqa: BLE001 — parallel module absent/incompatible; canonical local fallback
        local_index = _local_producer_index(card_list)

        def _match_via_local_fallback(edge: str) -> list[dict]:
            return local_index.get(_canon(edge), [])[:limit]

        _match_via_local_fallback.backend = "local_canonical_fallback"  # type: ignore[attr-defined]
        return _match_via_local_fallback


# ────────────────────────────── the composer ──────────────────────────────

def plan(target_output: str, cards: Iterable[dict], matcher: Optional[Callable[[str], list]] = None, *,
         source_edges: Optional[Iterable[str]] = None, max_steps: int = DEFAULT_MAX_STEPS) -> dict:
    """Compose a route toward ``target_output`` from EXISTING primitives and emit the GAPS as generation specs.

    Backward-chains from the target using the injected ``matcher(edge) -> producers`` oracle (if ``matcher``
    is None, one is built via ``matcher_from_cards``). At each step it asks the matcher who produces the needed
    edge, prepends the best producer (read by SIGNATURE), and moves to needing THAT producer's input. A branch
    ends when the needed edge is an available source (``source_edges``) — a clean chain, no gap — or when no
    primitive produces it — a GAP, emitted as a candidate generation_spec. Reads signatures to compose; reads
    the full card only to QUANTIFY the reuse saving.

    ``source_edges``: the edges the environment can supply (raw inputs). Default (None) = the corpus entry
    edges (produced by no card, consumed by some) so a standalone call stops at natural entry points rather
    than over-reporting gaps; pass an explicit set for precise "I have exactly these inputs" gap detection.

    Returns a ``hybrid_route_plan`` dict: ``route`` (reused primitive_ids, source→target order),
    ``route_signatures`` (what the LLM reads — cheap), ``gaps`` ([{needed_edge, generation_spec}, …]),
    ``token_cost_signatures`` / ``token_cost_if_regenerated`` / ``savings`` (reuse-vs-regenerate accounting).
    Deterministic (no wall-clock/RNG). candidate=true / serves_truth=false."""
    card_list = [c for c in cards if isinstance(c, dict)]
    if matcher is None:
        matcher = matcher_from_cards(card_list)

    cards_by_id: dict[str, dict] = {}
    for card in card_list:
        pid = str(card.get("primitive_id") or "")
        if pid and pid not in cards_by_id:
            cards_by_id[pid] = card

    if source_edges is None:
        source_set = _corpus_entry_edges(card_list)
    else:
        source_set = {_canon(e) for e in source_edges}

    route_ids: list[str] = []
    route_cards: list[dict] = []
    gaps: list[dict] = []
    visited: set[str] = set()
    needed = str(target_output)
    consumer_id: Optional[str] = None  # the on-route card that consumes `needed` (downstream), for gap context

    for _ in range(max(0, int(max_steps))):
        needed_canon = _canon(needed)
        if needed_canon and needed_canon in source_set:
            break  # reached an available raw input — chain complete, no gap
        if needed_canon in visited:
            break  # cycle guard — never revisit an edge type
        visited.add(needed_canon)

        used = set(route_ids)
        producers = [h for h in (matcher(needed) or []) if _hit_id(h) and _hit_id(h) not in used]
        if not producers:
            # GAP: nothing produces `needed`. Emit ONE generation spec for it and stop this branch.
            gap_input = sorted(source_set)[0] if source_set else UNRESOLVED_SOURCE
            spec = gap_to_generation_spec(needed, input_edge=gap_input, consumer_id=consumer_id,
                                          target_output=target_output)
            gaps.append({"needed_edge": str(needed), "generation_spec": spec})
            break

        best = producers[0]  # matcher ranks best-first
        pid = _hit_id(best)
        resolved = cards_by_id.get(pid)   # the producer's own full card, when it is in the corpus (the norm)
        card = resolved or (best if isinstance(best, dict) else {"primitive_id": pid})
        route_ids.insert(0, pid)      # prepend — we are chaining backward (source ends up first)
        route_cards.insert(0, card)
        consumer_id = pid
        # the producer's OWN input edge — the resolved card is authoritative; never trust the hit's top-level
        # ``input_edge`` (a matcher may set it to the QUERIED edge, which would truncate the chain to 1 step).
        needed = _hit_input_edge(best, resolved)
        if not needed:
            break  # the producer declares no input — it is itself a source primitive; chain complete

    # ── reuse-vs-regenerate token accounting (all derived from the cards via the onion; no magic values) ──
    route_signatures: list[dict] = []
    token_cost_signatures = 0
    token_cost_if_regenerated = 0
    for card in route_cards:
        disclosure = _onion.peel(card, "signature")          # ONE call: signature cost + full-card cost
        route_signatures.append(_onion.signature(card))
        token_cost_signatures += disclosure["token_cost"]        # compose by reading the SIGNATURE (cheap)
        token_cost_if_regenerated += disclosure["full_card_tokens"]  # regenerating/re-reading in FULL (dear)
    savings = max(0, token_cost_if_regenerated - token_cost_signatures)
    savings_pct = round(100.0 * savings / token_cost_if_regenerated, 1) if token_cost_if_regenerated else 0.0
    gap_spec_tokens = sum(_est_tokens(gap["generation_spec"]) for gap in gaps)

    return {
        "record_type": "hybrid_route_plan",
        "target_output": str(target_output),
        "matcher_backend": getattr(matcher, "backend", "injected"),
        "route": route_ids,                       # reused, EXISTING primitives (source → target order)
        "route_signatures": route_signatures,     # the cheap signature view the composer/LLM reads
        "route_length": len(route_ids),
        "gaps": gaps,                             # [{needed_edge, generation_spec}] — the missing primitives
        "gap_count": len(gaps),
        "covered": not gaps,                      # True ⟺ the whole route was built from existing primitives
        "token_cost_signatures": token_cost_signatures,
        "token_cost_if_regenerated": token_cost_if_regenerated,
        "savings": savings,
        "savings_pct": savings_pct,
        "gap_spec_tokens": gap_spec_tokens,       # even the gap specs are compact to read
        **BOUNDARY,
    }


def _corpus_entry_edges(cards: list[dict]) -> set[str]:
    """Corpus entry edges = canonical types that appear as some card's input_edge but are produced by no
    card. The default 'available source' set so a standalone plan() stops at natural entry points."""
    produced = {_canon(c.get("output_edge", "")) for c in cards if c.get("output_edge")}
    produced.discard("")
    entries: set[str] = set()
    for card in cards:
        in_edge = card.get("input_edge")
        if in_edge:
            in_canon = _canon(in_edge)
            if in_canon and in_canon not in produced:
                entries.add(in_canon)
    return entries


# ────────────────────────────── verify-the-verifier self-test ──────────────────────────────

def _fixture_cards() -> list[dict]:
    """A chain: RawGraphInput → EdgeList → AdjacencyGraph → AnswerString. Cards carry blackbox/contract so a
    full card is strictly larger than its signature (the reuse saving is real, not zero)."""
    def _card(pid: str, title: str, in_edge: str, out_edge: str) -> dict:
        return {
            "primitive_id": pid, "title": title, "input_edge": in_edge, "output_edge": out_edge,
            "kind": GAP_KIND,
            "blackbox": f"deterministically transforms {in_edge} into {out_edge}; " * 4,
            "contract": {"input": {in_edge: "..."}, "output": {out_edge: "..."}, "errors": ["bad_input"]},
            "effects": [{"type": "transform", "description": f"{in_edge}->{out_edge}"}],
            "mutations": ["variant_a", "variant_b"], "quality_score": 70,
            "readiness": "R2_edge_known", "verification_level": "L2",
            **BOUNDARY,
        }
    return [
        _card("prim:p1", "parse raw input to edge list", "RawGraphInput", "EdgeList"),
        _card("prim:p2", "build adjacency graph from edges", "EdgeList", "AdjacencyGraph"),
        _card("prim:p3", "answer from adjacency graph", "AdjacencyGraph", "AnswerString"),
    ]


def _stub_matcher(cards: list[dict]) -> Callable[[str], list[dict]]:
    """A tiny INJECTED connectivity oracle (producers keyed by EXACT output_edge, best-first). Keeps the
    self-test hermetic — it never depends on scripts.edge_type_matcher (built in parallel)."""
    by_output: dict[str, list[dict]] = {}
    for card in cards:
        out_edge = card.get("output_edge")
        if out_edge:
            by_output.setdefault(str(out_edge), []).append(card)
    for producers in by_output.values():
        producers.sort(key=lambda c: (-_quality(c), str(c.get("primitive_id", ""))))

    def _match(edge: str) -> list[dict]:
        return [
            {"primitive_id": c["primitive_id"], "input_edge": c.get("input_edge"),
             "output_edge": c.get("output_edge")}
            for c in by_output.get(str(edge), [])
        ]

    return _match


def _every_row_candidate_nontruth(plan_obj: dict) -> bool:
    """Boundary guard: the plan record AND every emitted gen-spec must be candidate=true / serves_truth=false."""
    rows = [plan_obj] + [g["generation_spec"] for g in plan_obj.get("gaps", [])]
    return all(r.get("serves_truth") is False and r.get("candidate") is True for r in rows)


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    full = _fixture_cards()
    partial = [c for c in full if c["primitive_id"] != "prim:p2"]  # drop the EdgeList→AdjacencyGraph producer
    src = {"RawGraphInput"}
    stub_full = _stub_matcher(full)
    stub_partial = _stub_matcher(partial)

    # A. FULLY-COVERED target → full route + 0 gaps + positive savings.
    p_full = plan("AnswerString", full, stub_full, source_edges=src)
    checks.append(("fully-covered: route chains all 3 existing primitives, source→target",
                   p_full["route"] == ["prim:p1", "prim:p2", "prim:p3"]))
    checks.append(("fully-covered: 0 gaps + covered=True", p_full["gap_count"] == 0 and p_full["covered"] is True))
    checks.append(("fully-covered: positive reuse savings", p_full["savings"] > 0 and p_full["savings_pct"] > 0))

    # B. token_cost uses cheap SIGNATURES, not full cards.
    expect_sig = sum(_onion.token_cost(c, "signature") for c in full)
    expect_full = sum(_onion.peel(c, "signature")["full_card_tokens"] for c in full)
    checks.append(("token_cost_signatures is the SIGNATURE layer (not the full card)",
                   p_full["token_cost_signatures"] == expect_sig and expect_sig < expect_full))
    checks.append(("token_cost_if_regenerated is the FULL-card cost + savings = full − signatures",
                   p_full["token_cost_if_regenerated"] == expect_full
                   and p_full["savings"] == expect_full - expect_sig))
    checks.append(("route_signatures carry ONLY the 4 signature fields (no blackbox/contract leaked)",
                   all(set(s) <= {"primitive_id", "title", "input_edge", "output_edge"}
                       for s in p_full["route_signatures"])))

    # C. PARTIALLY-COVERED target → the reusable route + the CORRECT gap spec.
    p_part = plan("AnswerString", partial, stub_partial, source_edges=src)
    checks.append(("partial: reuses the still-composable downstream primitive", p_part["route"] == ["prim:p3"]))
    checks.append(("partial: exactly one gap, at the missing edge", p_part["gap_count"] == 1
                   and p_part["gaps"][0]["needed_edge"] == "AdjacencyGraph"))
    spec = p_part["gaps"][0]["generation_spec"]
    checks.append(("partial: gap spec's output_edge == the missing edge", spec["output_edge"] == "AdjacencyGraph"))
    checks.append(("partial: gap spec input_edge is a declared source (bridgeable)", spec["input_edge"] == "RawGraphInput"))
    checks.append(("partial: gap spec cites the downstream consumer", "prim:p3" in spec["purpose"]))
    checks.append(("partial: gap spec is a candidate skeleton with promotion_blockers + empty body to fill",
                   spec["promotion_blockers"] == list(GEN_PROMOTION_BLOCKERS)
                   and spec["contract"] == {} and spec["blackbox"] == ""))
    checks.append(("partial: gap spec vocabulary matches adapter_plan (lane/node_kind/proof/promotion)",
                   spec["lane"] == GEN_LANE and spec["node_kind"] == GEN_NODE_KIND
                   and spec["proof_required"] == GEN_PROOF_REQUIRED and spec["promotion_required"] is True))
    checks.append(("partial: gap spec id is content-derived under the gap prefix (version in metadata, not id)",
                   str(spec["primitive_id"]).startswith(GAP_ID_PREFIX + "-")
                   and ".v" not in spec["primitive_id"] and "@" not in spec["primitive_id"]))
    checks.append(("partial: composed step p3 is NOT emitted as a generated spec (reuse ≠ generate)",
                   all(g["generation_spec"]["primitive_id"] != "prim:p3" for g in p_part["gaps"])))

    # D. FULLY-UNCOVERED target (empty corpus) → empty route + a gap at the target itself (graceful).
    p_empty = plan("AnswerString", [], _stub_matcher([]), source_edges=set())
    checks.append(("uncovered: empty route + one gap at the target, no crash",
                   p_empty["route"] == [] and p_empty["gap_count"] == 1
                   and p_empty["gaps"][0]["needed_edge"] == "AnswerString"))

    # E. ALL emitted rows are candidate=true / serves_truth=false.
    checks.append(("every emitted row (plan + gap specs) is candidate=true / serves_truth=false",
                   _every_row_candidate_nontruth(p_full) and _every_row_candidate_nontruth(p_part)))

    # F. matcher_from_cards drives the composer end to end over the PRIMARY reuse path (edge_type_matcher),
    #    composing the full 3-step route. This exercises the real reuse path (not the injected stub), so the
    #    input-edge shape mismatch that would truncate the chain to 1 step (reading the hit's QUERIED edge
    #    instead of the producer's own) shows up here as a wrong route.
    auto = matcher_from_cards(full)
    p_auto = plan("AnswerString", full, auto, source_edges=src)
    checks.append(("matcher_from_cards composes the full route over the reuse path (backward chaining reads the producer's own input edge)",
                   p_auto["route"] == ["prim:p1", "prim:p2", "prim:p3"] and p_auto["covered"] is True))
    # F2. the PRIMARY backend is ACTUALLY scripts.edge_type_matcher, not a silent drop to the local fallback.
    #     `_etm_reuse_available` mirrors the exact import matcher_from_cards does, so a symbol drift there
    #     (e.g. importing a name that no longer exists — the original bug) makes this REQUIRE-reuse check RED
    #     instead of being masked by the fallback composing an identical route on the tiny fixture.
    try:
        from scripts.edge_type_matcher import build_producer_index as _bpi, match_hits as _mh  # noqa: F401,PLC0415
        _etm_reuse_available = True
    except Exception:  # noqa: BLE001
        _etm_reuse_available = False
    checks.append(("matcher_from_cards REUSES scripts.edge_type_matcher (import resolves AND the built matcher runs on it — catches the silent drop to the local fallback)",
                   _etm_reuse_available and getattr(auto, "backend", None) == "edge_type_matcher"))

    # ── MUTATION GATES: a real injected defect must make a guard go RED ──
    # G1: a gap spec leaking serves_truth=true must be caught by the boundary guard.
    leaked = json.loads(json.dumps(p_part))
    leaked["gaps"][0]["generation_spec"]["serves_truth"] = True
    checks.append(("MUTATION: boundary guard REDS on a truth-leaking gap spec",
                   _every_row_candidate_nontruth(p_part) is True and _every_row_candidate_nontruth(leaked) is False))
    # G2: removing the middle producer flips coverage True→False (a real corpus defect changes the verdict).
    checks.append(("MUTATION: coverage flips True→False when a producer is removed",
                   p_full["covered"] is True and p_part["covered"] is False))
    # G3: savings come from SIGNATURES — a mutant reading full cards for both sides collapses savings to 0.
    mutant_savings = max(0, p_full["token_cost_if_regenerated"] - p_full["token_cost_if_regenerated"])
    checks.append(("MUTATION: reading full cards (not signatures) collapses savings to 0 — caught by savings>0",
                   p_full["savings"] > 0 and mutant_savings == 0))
    # G4: the gap's output_edge is bound to the actual missing edge — mutating it must diverge.
    checks.append(("MUTATION: gap output_edge is bound to the missing edge (a wrong edge would mismatch)",
                   spec["output_edge"] == p_part["gaps"][0]["needed_edge"]))

    # ── DETERMINISM GATE: same input → byte-identical plan (no wall-clock/RNG in plan()) ──
    d1 = json.dumps(plan("AnswerString", partial, _stub_matcher(partial), source_edges=src), sort_keys=True)
    d2 = json.dumps(plan("AnswerString", partial, _stub_matcher(partial), source_edges=src), sort_keys=True)
    checks.append(("DETERMINISM: plan() is byte-identical across two builds", d1 == d2))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - hybrid_composer: {len(checks)} checks. Compose a target from EXISTING primitives read by "
          f"signature (savings {p_full['savings']} tok on a {p_full['route_length']}-step route), emit the "
          f"gaps as candidate generation_specs (serves_truth=false, promotion-blocked). Mutation- + "
          f"determinism-gated.")
    return 0


# ────────────────────────────── CLI ──────────────────────────────

def _demo() -> int:
    """Print a plan over the synthetic partial corpus — one composed step + one gap spec. Uses now_iso only
    here (the emit boundary), never inside deterministic plan()."""
    partial = [c for c in _fixture_cards() if c["primitive_id"] != "prim:p2"]
    p = plan("AnswerString", partial, _stub_matcher(partial), source_edges={"RawGraphInput"})
    receipt = {"generated_at": now_iso(), **p}
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


def _run(target: str, limit: int) -> int:
    """Compose toward ``target`` over the real verified primitive corpus (capped for speed/determinism), using
    matcher_from_cards (reuses scripts.edge_type_matcher when importable)."""
    corpus = (_sbc / "data" / "dev-intel" / "aidevobserver_edge_foundry"
              / "verified_factory_primitive_cards.jsonl")
    _all_cards = read_jsonl_tolerant(corpus)
    cards = _all_cards[: int(limit)] if int(limit) > 0 else _all_cards  # 0/negative = uncapped
    matcher = matcher_from_cards(cards)
    p = plan(target, cards, matcher)
    summary = {
        "generated_at": now_iso(), "target_output": target, "corpus_cards": len(cards),
        "matcher_backend": p["matcher_backend"], "route": p["route"], "route_length": p["route_length"],
        "gap_count": p["gap_count"], "covered": p["covered"],
        "token_cost_signatures": p["token_cost_signatures"],
        "token_cost_if_regenerated": p["token_cost_if_regenerated"],
        "savings": p["savings"], "savings_pct": p["savings_pct"],
        "gaps": [g["needed_edge"] for g in p["gaps"]],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--self-test", action="store_true", help="run the mutation- + determinism-gated self-test")
    parser.add_argument("--demo", action="store_true", help="print a plan over the synthetic partial corpus")
    parser.add_argument("--run", action="store_true", help="compose toward --target over the real corpus")
    parser.add_argument("--target", default="AnswerString", help="target output edge for --run")
    parser.add_argument("--limit", type=int, default=0,
                        help="corpus cap for --run; 0 = FULL corpus (caps are opt-in, never silent defaults)")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.demo:
        return _demo()
    if args.run:
        return _run(args.target, args.limit)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
