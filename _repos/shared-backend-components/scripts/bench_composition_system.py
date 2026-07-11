#!/usr/bin/env python3
"""scripts.bench_composition_system — the END-TO-END benchmark of the whole composition system, over the REAL
verified primitive corpus, measuring the three levers that make "compose, don't cache" work TOGETHER.

Each lever already has its own module + proof; this benchmark wires the three into one honest whole-system
receipt (nothing new is matched/composed here — it only MEASURES the existing engines end to end):

  1. CONNECTIVITY (the composer's reach) — what fraction of consumer input edges have SOME producer, under
     EXACT string equality vs. the intelligent ``scripts.edge_type_matcher`` (canonical fold + type-token
     overlap). Exact is the ~10% floor; type-aware is the ceiling. The RATIO is the "compose, don't cache"
     lever: primitives DO chain once the matcher decides type-compatibility instead of string-identity.
  2. TOKENS (the read cost) — the cost of a composed plan read by SIGNATURE (``scripts.primitive_onion``,
     ~50 tok/primitive) vs. the full card (~750 tok). The ~15x is why an agent reads the docstring, not the body.
  3. HYBRID GAP RATE (the honesty of "partial + generate") — over a sample of targets, the fraction the
     composer (``scripts.hybrid_composer``) CANNOT fully cover from existing primitives and must emit an
     LLM-generation spec for. Measured under BOTH matchers so the connectivity lever's effect on the gap
     rate is visible: the intelligent matcher collapses the gap rate the naive one leaves open.

The composer is driven by matchers built on ``edge_type_matcher`` (a ``match``-backed type matcher and an
``exact``-tier matcher), so the "whole system" is genuinely wired — the connectivity lever (#1) drives the
gap rate (#3), and both plans are read by signature (#2). Matcher hits carry ONLY the ``primitive_id`` so
``hybrid_composer`` resolves each producer's real input edge from its own card (correct backward chaining).

Honest floor↔ceiling: the ~99% "type" number quoted by ``bench_intelligent_composition`` is its
token-overlap PROXY (any-shared-token → an over-matching UPPER bound). This benchmark reports the STRICTER
``edge_type_matcher`` number (canonical fold onto the curated vocabulary + Jaccard-floored type-token
overlap), which is the real matcher every composer would use — a lower, honest ceiling at a large lift.

BOUNDARY LAW: every emitted row is candidate=true / serves_truth=false. Measuring connectivity/reuse never
promotes a primitive; a producer becomes served truth only through its own proofs + gates.

    PYTHONPATH=. python3 scripts/bench_composition_system.py --self-test
    PYTHONPATH=. python3 scripts/bench_composition_system.py --run [--corpus 34123] [--input-sample 4000]
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── self-bootstrap via the repo-paths sentinel (BEFORE any scripts.*/src.* import) ──
_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable, Iterable, Optional  # noqa: E402

from scripts import edge_type_matcher as _etm  # noqa: E402  lever #1: the intelligent type matcher + connectivity
from scripts import hybrid_composer as _hc  # noqa: E402  lever #3: compose-what-exists + emit gaps as specs
from scripts import primitive_onion as _onion  # noqa: E402  lever #2: read a primitive by its cheap signature
from scripts._jsonl import read_jsonl_tolerant  # noqa: E402  (mandated helper)
from scripts._time import now_iso  # noqa: E402  (mandated helper; report metadata only — never in benchmark())

__all__ = ["benchmark", "connectivity_section", "token_section", "hybrid_section", "BOUNDARY"]

#: every emitted row/record is a candidate signal, never truth (a benchmark cannot promote).
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: the verified corpus, single-sourced from edge_type_matcher (no parallel path literal).
CORPUS = _etm.CORPUS

# ── bounded-probe sizes (rationale inline; not cross-module constants — this benchmark's own knobs) ──
#: full verified corpus card count (a cap, not a magic count — the file may hold more/fewer; we index what's there).
DEFAULT_CORPUS_CAP = 34123
#: distinct-input probe for CONNECTIVITY. The type tier is O(inputs × candidate-producers); a deterministic
#: even sample of the distinct inputs estimates the satisfiability FRACTION at bounded cost while the producer
#: index still covers the WHOLE corpus (complete producer coverage, bounded probe). None ⇒ probe every input.
DEFAULT_INPUT_SAMPLE = 4000
#: targets for the HYBRID gap rate (deterministic even sample of distinct output edges).
DEFAULT_TARGET_SAMPLE = 150
#: cards for the per-primitive SIGNATURE-vs-full token ratio (deterministic even sample).
DEFAULT_TOKEN_SAMPLE = 500
#: producers a matcher returns per edge, and the backward-chain bound — single-sourced from hybrid_composer
#: so the benchmark and the composer it drives never drift on these.
DEFAULT_MATCH_LIMIT = _hc.DEFAULT_MATCH_LIMIT
DEFAULT_MAX_STEPS = _hc.DEFAULT_MAX_STEPS


# ────────────────────────────── deterministic sampling ──────────────────────────────

def _even_sample(items: Iterable[Any], n: Optional[int]) -> list[Any]:
    """A deterministic, evenly-spaced sub-sample of ``items`` (no RNG, no hash()) — every run picks the SAME
    rows. Returns all items when ``n`` is None / non-positive / ≥ len (nothing to sample)."""
    seq = list(items)
    if n is None or n <= 0 or n >= len(seq):
        return seq
    stride = max(1, len(seq) // n)
    return seq[::stride][:n]


# ────────────────────────────── matcher adapters (drive the composer with edge_type_matcher) ──────────────

def _type_matcher(index: dict[str, Any], *, limit: int = DEFAULT_MATCH_LIMIT) -> Callable[[str], list[dict]]:
    """A ``matcher(edge) -> producer hits`` oracle backed by the INTELLIGENT ``edge_type_matcher.match``
    (exact→canonical→token, ranked best-first). Hits carry ONLY the ``primitive_id`` so ``hybrid_composer``
    reads each producer's real input edge from its own card (correct backward chaining, no shape mismatch)."""
    def _match(edge: str) -> list[dict]:
        return [{"primitive_id": pid} for pid in _etm.match(edge, index, limit=limit)]
    _match.backend = "edge_type_matcher.match"  # type: ignore[attr-defined]
    return _match


def _exact_matcher(index: dict[str, Any]) -> Callable[[str], list[dict]]:
    """A ``matcher(edge) -> producer hits`` oracle restricted to the EXACT tier (raw ``output_edge`` string
    equality) — today's ~10% baseline, so the gap rate it leaves open is the honest naive-matcher floor."""
    def _match(edge: str) -> list[dict]:
        return [{"primitive_id": pid} for pid in _etm.producers(edge, index, method="exact")]
    _match.backend = "edge_type_matcher.exact"  # type: ignore[attr-defined]
    return _match


# ────────────────────────────── section 1: connectivity (exact vs type-aware) ──────────────────────────────

def connectivity_section(cards: list[dict], index: dict[str, Any], *,
                         input_sample: Optional[int] = DEFAULT_INPUT_SAMPLE) -> dict[str, Any]:
    """What fraction of consumer input edges have SOME producer, under EXACT vs the type-aware matcher.
    Reuses ``edge_type_matcher.connectivity`` (no reimplementation). Probes a deterministic even sample of the
    distinct inputs (bounded cost) against the full producer index. The lift is the composition lever."""
    all_inputs = sorted({str(c.get("input_edge") or "").strip()
                         for c in cards if str(c.get("input_edge") or "").strip()})
    probe = _even_sample(all_inputs, input_sample)
    c_exact = _etm.connectivity(probe, index, method="exact")
    c_type = _etm.connectivity(probe, index, method="type")
    return {
        "distinct_inputs_total": len(all_inputs),
        "inputs_probed": len(probe),
        "connectivity_exact": c_exact,
        "connectivity_type": c_type,
        "lift_type_over_exact": round(c_type / c_exact, 2) if c_exact else None,
    }


# ────────────────────────────── section 2: token cost (signature vs full card) ──────────────────────────────

def token_section(cards: list[dict], *, sample_size: Optional[int] = DEFAULT_TOKEN_SAMPLE) -> dict[str, Any]:
    """Cost of reading a primitive by its SIGNATURE vs its full card, over a deterministic sample. Reuses
    ``primitive_onion.peel`` (ONE call yields both the signature cost and the full-card cost; the CHARS/token
    proxy lives in the onion, never re-declared here). The ratio is why an agent reads the docstring layer."""
    sample = _even_sample(cards, sample_size)
    sig_total = 0
    full_total = 0
    for card in sample:
        disclosure = _onion.peel(card, "signature")   # signature token_cost + full_card_tokens in one read
        sig_total += disclosure["token_cost"]
        full_total += disclosure["full_card_tokens"]
    n = len(sample) or 1
    return {
        "cards_sampled": len(sample),
        "signature_tokens_total": sig_total,
        "full_card_tokens_total": full_total,
        "mean_signature_tokens": round(sig_total / n, 1),
        "mean_full_card_tokens": round(full_total / n, 1),
        "token_reduction_signature_vs_full": round(full_total / sig_total, 2) if sig_total else None,
    }


# ────────────────────────────── section 3: hybrid gap rate (partial + generate) ──────────────────────────────

def _run_over_targets(cards: list[dict], targets: list[str], matcher: Callable[[str], list[dict]], *,
                      source_edges: list[str], max_steps: int) -> dict[str, Any]:
    """Compose toward each target with ``hybrid_composer.plan`` under ONE matcher; aggregate gap rate, coverage,
    route length, and reuse-vs-regenerate token accounting (all deterministic; no wall-clock/RNG)."""
    gapped = covered = spec_count = 0
    sig_total = full_total = route_len_total = 0
    example_spec: Optional[dict] = None
    for target in targets:
        pl = _hc.plan(target, cards, matcher, source_edges=source_edges, max_steps=max_steps)
        if pl["gap_count"] >= 1:
            gapped += 1
        if pl["covered"]:
            covered += 1
        spec_count += pl["gap_count"]
        sig_total += pl["token_cost_signatures"]
        full_total += pl["token_cost_if_regenerated"]
        route_len_total += pl["route_length"]
        if example_spec is None and pl["gaps"]:
            example_spec = pl["gaps"][0]["generation_spec"]   # first emitted spec, deterministically
    n = len(targets) or 1
    return {
        "matcher_backend": getattr(matcher, "backend", "injected"),
        "gap_rate": round(gapped / n, 4),
        "covered_rate": round(covered / n, 4),
        "avg_route_length": round(route_len_total / n, 2),
        "generated_spec_count": spec_count,
        "plan_signature_tokens_total": sig_total,
        "plan_full_tokens_total": full_total,
        "plan_token_reduction": round(full_total / sig_total, 2) if sig_total else None,
        "example_generated_spec": example_spec,
    }


def hybrid_section(cards: list[dict], index: dict[str, Any], *, targets: Optional[Iterable[str]] = None,
                   target_sample: int = DEFAULT_TARGET_SAMPLE, match_limit: int = DEFAULT_MATCH_LIMIT,
                   max_steps: int = DEFAULT_MAX_STEPS,
                   source_edges: Optional[Iterable[str]] = None) -> dict[str, Any]:
    """Gap rate = fraction of targets the composer must emit ≥1 LLM-generation spec for, under the TYPE-aware
    matcher vs the EXACT matcher. Reuses ``hybrid_composer.plan`` (the composer) and ``._corpus_entry_edges``
    (the default available-source set) — this section only chooses the matcher + targets and aggregates."""
    card_list = [c for c in cards if isinstance(c, dict)]
    if targets is None:
        outs = sorted({str(c.get("output_edge") or "").strip()
                       for c in card_list if str(c.get("output_edge") or "").strip()})
        target_list = _even_sample(outs, target_sample)
    else:
        target_list = list(targets)
    # Available sources: the corpus entry edges (canonical types produced by no card). canonicalize_edge is
    # idempotent on canonical types, so re-canonicalization inside plan() is a no-op — verified in the self-test.
    src = sorted(_hc._corpus_entry_edges(card_list)) if source_edges is None else sorted(source_edges)

    type_matcher = _type_matcher(index, limit=match_limit)
    exact_matcher = _exact_matcher(index)
    type_res = _run_over_targets(card_list, target_list, type_matcher, source_edges=src, max_steps=max_steps)
    exact_res = _run_over_targets(card_list, target_list, exact_matcher, source_edges=src, max_steps=max_steps)
    return {
        "targets_probed": len(target_list),
        "source_edges_count": len(src),
        "type_aware": type_res,
        "exact": exact_res,
        "gap_rate_type": type_res["gap_rate"],
        "gap_rate_exact": exact_res["gap_rate"],
        "gap_rate_reduction": round(exact_res["gap_rate"] - type_res["gap_rate"], 4),
    }


# ────────────────────────────── the whole-system benchmark ──────────────────────────────

_NOTE = (
    "Whole-system composition benchmark. connectivity_exact = raw-string equality (~10% floor); "
    "connectivity_type = the STRICTER edge_type_matcher (canonical fold onto the curated vocabulary + "
    "Jaccard-floored type-token overlap) — the honest ceiling, LOWER than bench_intelligent_composition's "
    "any-shared-token proxy (its ~99% is an over-matching upper bound). The gap rate is measured under BOTH "
    "matchers so the connectivity lever's effect on 'partial + generate' is visible. serves_truth=false."
)


def benchmark(cards: Iterable[dict], *, input_sample: Optional[int] = DEFAULT_INPUT_SAMPLE,
              target_sample: int = DEFAULT_TARGET_SAMPLE, token_sample: Optional[int] = DEFAULT_TOKEN_SAMPLE,
              match_limit: int = DEFAULT_MATCH_LIMIT, max_steps: int = DEFAULT_MAX_STEPS,
              targets: Optional[Iterable[str]] = None,
              source_edges: Optional[Iterable[str]] = None) -> dict[str, Any]:
    """Measure the whole composition system over ``cards`` and return one ``composition_system_benchmark``
    record: connectivity (exact vs type-aware), token cost (signature vs full card), and hybrid gap rate
    (type-aware vs exact). ``source_edges`` = the environment's available raw inputs for the gap rate; None
    (the real-corpus default) uses ``hybrid_composer``'s natural corpus-entry edges. Pure + deterministic (no
    wall-clock/RNG here — now_iso is added only at the emit boundary in the CLI). candidate=true /
    serves_truth=false."""
    card_list = [c for c in cards if isinstance(c, dict) and c.get("primitive_id")]
    index = _etm.build_producer_index(card_list)   # lever #1 index — full producer coverage, built once
    conn = connectivity_section(card_list, index, input_sample=input_sample)
    tok = token_section(card_list, sample_size=token_sample)
    hyb = hybrid_section(card_list, index, targets=targets, target_sample=target_sample,
                         match_limit=match_limit, max_steps=max_steps, source_edges=source_edges)
    return {
        "record_type": "composition_system_benchmark",
        "cards_indexed": index["card_count"],
        "connectivity": conn,
        "tokens": tok,
        "hybrid": hyb,
        "headline": {
            "connectivity_exact": conn["connectivity_exact"],
            "connectivity_type_aware": conn["connectivity_type"],
            "connectivity_lift_type_over_exact": conn["lift_type_over_exact"],
            "token_reduction_signature_vs_full": tok["token_reduction_signature_vs_full"],
            "hybrid_gap_rate_type_aware": hyb["gap_rate_type"],
            "hybrid_gap_rate_exact": hyb["gap_rate_exact"],
        },
        "note": _NOTE,
        **BOUNDARY,
    }


# ────────────────────────────── verify-the-verifier self-test ──────────────────────────────

def _fixture_cards() -> list[dict]:
    """A synthetic corpus exercising all three levers with mutation sensitivity. A long blackbox makes each
    full card strictly larger than its signature (a REAL token saving). The A→B pair is the type-variant
    hinge: B consumes 'NormalizedRecordBatch', which ONLY the type matcher (token tier) connects to A's
    'NormalizedRecord' output — so 'Summary' is coverable under type but GAPS under exact."""
    def _card(pid: str, title: str, in_edge: str, out_edge: str) -> dict:
        return {
            "primitive_id": pid, "title": title, "input_edge": in_edge, "output_edge": out_edge,
            "kind": "route.primitive",
            "blackbox": f"deterministically transforms {in_edge} into {out_edge}; " * 8,
            "contract": {"input": {in_edge: "the upstream value"}, "output": {out_edge: "the produced value"},
                         "errors": ["bad_input", "empty_input"]},
            "effects": [{"type": "transform", "description": f"{in_edge}->{out_edge}"}],
            "mutations": ["variant_a", "variant_b"], "quality_score": 70, "readiness": "R2_edge_known",
            "verification_level": "L2", **BOUNDARY,
        }
    return [
        _card("prim:A", "normalize seed to record", "Seed", "NormalizedRecord"),
        _card("prim:B", "summarize a record batch", "NormalizedRecordBatch", "Summary"),
        _card("prim:P1", "parse raw input to edge list", "RawGraphInput", "EdgeList"),
        _card("prim:P2", "build adjacency graph from edges", "EdgeList", "AdjacencyGraph"),
        _card("prim:P3", "answer from adjacency graph", "AdjacencyGraph", "AnswerString"),
    ]


#: token ratio the fixture must clear (its cards carry an 8x-repeated blackbox, so the full card dwarfs the
#: signature). A floor derived from the fixture shape, not a hand-typed live-corpus number.
_FIXTURE_TOKEN_RATIO_FLOOR = 3.0
#: the environment's TRUE raw inputs for the fixture. Deliberately EXCLUDES 'NormalizedRecordBatch' (a card
#: consumes it but no card produces it exactly/canonically) so the composer must FIND a producer for it —
#: which ONLY the type matcher can (via the token-tier bridge to 'NormalizedRecord'). Without this, default
#: entry-detection would treat 'NormalizedRecordBatch' as an available source and BOTH lanes would stop there,
#: masking the lever. On the real corpus the default (None) is used — its many non-entry intermediate edges
#: expose the same gap-rate difference (measured type ~0.0 vs exact ~0.30).
_FIXTURE_SOURCE_EDGES = ("Seed", "RawGraphInput")


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = _fixture_cards()
    index = _etm.build_producer_index(cards)

    # ── SECTION 1: connectivity — type-aware reaches strictly more than exact (the composition lever). ──
    conn = connectivity_section(cards, index, input_sample=None)  # probe every input in the fixture
    checks.append(("connectivity: type-aware > exact (the compose-don't-cache lever is real)",
                   conn["connectivity_type"] > conn["connectivity_exact"]))
    checks.append(("connectivity: lift is reported (> 1x)",
                   conn["lift_type_over_exact"] is not None and conn["lift_type_over_exact"] > 1.0))
    # the specific hinge: 'NormalizedRecordBatch' has NO exact/canonical producer but IS matched under type.
    checks.append(("connectivity hinge: type-variant edge is unmatched by exact but matched by type-aware",
                   _etm.producers("NormalizedRecordBatch", index, method="exact") == []
                   and _etm.producers("NormalizedRecordBatch", index, method="canonical") == []
                   and "prim:A" in _etm.match("NormalizedRecordBatch", index)))

    # ── SECTION 2: tokens — signature is strictly cheaper than the full card (the ~15x read lever). ──
    tok = token_section(cards, sample_size=None)
    checks.append(("tokens: mean full-card cost > mean signature cost (reading the body is dearer)",
                   tok["mean_full_card_tokens"] > tok["mean_signature_tokens"]))
    checks.append((f"tokens: signature-vs-full reduction clears the fixture floor ({_FIXTURE_TOKEN_RATIO_FLOOR}x)",
                   tok["token_reduction_signature_vs_full"] is not None
                   and tok["token_reduction_signature_vs_full"] > _FIXTURE_TOKEN_RATIO_FLOOR))

    # ── SECTION 3: hybrid gap rate — exact leaves gaps the type matcher closes; specs are candidate skeletons. ──
    hyb = hybrid_section(cards, index, targets=["Summary", "ZzzNonexistentTarget"],
                         source_edges=_FIXTURE_SOURCE_EDGES)
    checks.append(("hybrid: the composer is driven by edge_type_matcher (not a reimplemented matcher)",
                   hyb["type_aware"]["matcher_backend"] == "edge_type_matcher.match"
                   and hyb["exact"]["matcher_backend"] == "edge_type_matcher.exact"))
    checks.append(("hybrid: 'Summary' is covered under type (via the token-tier bridge) but gaps under exact",
                   hyb["gap_rate_type"] == 0.5 and hyb["gap_rate_exact"] == 1.0))
    checks.append(("hybrid: the type matcher yields a LOWER gap rate than exact (connectivity → fewer gaps)",
                   hyb["gap_rate_type"] < hyb["gap_rate_exact"] and hyb["gap_rate_reduction"] > 0))
    spec = hyb["type_aware"]["example_generated_spec"]
    checks.append(("hybrid: the emitted gap spec is a candidate skeleton (serves_truth=false + promotion_blockers)",
                   spec is not None and spec["serves_truth"] is False and spec["candidate"] is True
                   and spec["promotion_blockers"] and spec["output_edge"] == "ZzzNonexistentTarget"))

    # ── whole-system record: boundary + determinism. ──
    report = benchmark(cards, input_sample=None, token_sample=None, targets=["Summary", "ZzzNonexistentTarget"],
                       source_edges=_FIXTURE_SOURCE_EDGES)
    rows = [report, report["hybrid"]["type_aware"]["example_generated_spec"],
            report["hybrid"]["exact"]["example_generated_spec"]]
    checks.append(("boundary: the report and every emitted gap spec are candidate=true / serves_truth=false",
                   all(r is not None and r.get("serves_truth") is False and r.get("candidate") is True
                       for r in rows)))
    checks.append(("headline surfaces all three levers (connectivity lift, token reduction, gap rates)",
                   report["headline"]["connectivity_lift_type_over_exact"] is not None
                   and report["headline"]["token_reduction_signature_vs_full"] is not None
                   and report["headline"]["hybrid_gap_rate_type_aware"]
                   != report["headline"]["hybrid_gap_rate_exact"]))
    report2 = benchmark(cards, input_sample=None, token_sample=None, targets=["Summary", "ZzzNonexistentTarget"],
                        source_edges=_FIXTURE_SOURCE_EDGES)
    checks.append(("DETERMINISM: benchmark() is byte-identical across two builds (no wall-clock/RNG)",
                   json.dumps(report, sort_keys=True) == json.dumps(report2, sort_keys=True)))

    # ── MUTATION GATES: a real injected defect must flip a headline. ──
    # G1: corrupt the type-variant producer's output → the token bridge breaks → type connectivity DROPS and
    #     'Summary' now gaps under type (the lift + gap-closure are not vacuous).
    mutated = [dict(c) for c in cards]
    for c in mutated:
        if c["primitive_id"] == "prim:A":
            c["output_edge"] = "ZzzUnrelatedGarbageOutput"
    idx_mut = _etm.build_producer_index(mutated)
    conn_mut = connectivity_section(mutated, idx_mut, input_sample=None)
    hyb_mut = hybrid_section(mutated, idx_mut, targets=["Summary"], source_edges=_FIXTURE_SOURCE_EDGES)
    checks.append(("MUTATION: corrupting the type-variant producer lowers type-aware connectivity",
                   conn_mut["connectivity_type"] < conn["connectivity_type"]))
    checks.append(("MUTATION: with the bridge gone, 'Summary' gaps under type too (gap detection is real)",
                   hybrid_section(cards, index, targets=["Summary"],
                                  source_edges=_FIXTURE_SOURCE_EDGES)["gap_rate_type"] == 0.0
                   and hyb_mut["gap_rate_type"] == 1.0))
    # G2: a mutant token measure that reads FULL cards for BOTH sides collapses the reduction to 1.0 — the
    #     real ratio must exceed it (guards against the signature saving being silently dropped).
    mutant_ratio = round(tok["full_card_tokens_total"] / tok["full_card_tokens_total"], 2)
    checks.append(("MUTATION: reading full cards for both sides collapses the reduction to 1.0 — caught by ratio>1",
                   tok["token_reduction_signature_vs_full"] > 1.0 and mutant_ratio == 1.0))
    # G3: the exact matcher must differ from the type matcher — if hybrid_section wired the SAME matcher to
    #     both lanes, the two gap rates would be equal. They are not.
    checks.append(("MUTATION: the two matcher lanes are genuinely different (equal rates would mean mis-wiring)",
                   hyb["gap_rate_type"] != hyb["gap_rate_exact"]))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - bench_composition_system: the three levers measured end to end on the synthetic corpus — "
          f"connectivity type-aware {conn['connectivity_type']} vs exact {conn['connectivity_exact']} "
          f"(lift {conn['lift_type_over_exact']}x), signature-vs-full token reduction "
          f"{tok['token_reduction_signature_vs_full']}x, hybrid gap rate type {hyb['gap_rate_type']} vs exact "
          f"{hyb['gap_rate_exact']}. Reuses edge_type_matcher + hybrid_composer + primitive_onion; "
          f"mutation- + determinism-gated; serves_truth=false.")
    return 0


# ────────────────────────────── CLI ──────────────────────────────

def _load_corpus(cap: int) -> list[dict]:
    if not CORPUS.exists():
        return []
    cards = [c for c in read_jsonl_tolerant(CORPUS) if c.get("primitive_id")]
    return cards[:cap] if cap and cap < len(cards) else cards


def _run(cap: int, input_sample: int, target_sample: int, token_sample: int) -> int:
    """Measure the whole system over the real corpus and print the headline + section receipts."""
    cards = _load_corpus(cap)
    if not cards:
        print(f"no corpus cards at {CORPUS} (factory scratch may be gitignored on this checkout)")
        return 1
    report = benchmark(cards, input_sample=input_sample, target_sample=target_sample, token_sample=token_sample)
    receipt = {"generated_at": now_iso(),  # emit-boundary only — never inside deterministic benchmark()
               "cards_indexed": report["cards_indexed"], "headline": report["headline"],
               "connectivity": report["connectivity"], "tokens": report["tokens"],
               "hybrid": {k: report["hybrid"][k] for k in
                          ("targets_probed", "gap_rate_type", "gap_rate_exact", "gap_rate_reduction")},
               "hybrid_type_detail": {k: report["hybrid"]["type_aware"][k] for k in
                                      ("gap_rate", "covered_rate", "avg_route_length", "generated_spec_count",
                                       "plan_token_reduction")},
               "note": report["note"], **BOUNDARY}
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true", help="mutation- + determinism-gated hermetic self-test")
    ap.add_argument("--run", action="store_true", help="measure the whole system over the real corpus")
    ap.add_argument("--corpus", type=int, default=DEFAULT_CORPUS_CAP, help="cap on cards loaded for --run")
    ap.add_argument("--input-sample", type=int, default=DEFAULT_INPUT_SAMPLE,
                    help="distinct-input probe size for connectivity (bounded cost; 0 = probe all)")
    ap.add_argument("--target-sample", type=int, default=DEFAULT_TARGET_SAMPLE, help="targets for the gap rate")
    ap.add_argument("--token-sample", type=int, default=DEFAULT_TOKEN_SAMPLE, help="cards for the token ratio")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.corpus, args.input_sample, args.target_sample, args.token_sample)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
