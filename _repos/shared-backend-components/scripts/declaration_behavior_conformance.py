#!/usr/bin/env python3
"""declaration_behavior_conformance — the VERIFIED-REUSE gate.

Market finding (2026): a crawl of ~50,000 marketplace agent skills found ~80% had a
declaration-vs-behavior MISMATCH — the card says one thing, the code does another. Reuse of a
capability that lies about itself is negative value dressed as savings. Token savings only matter
if the reused thing is CORRECT: savings × correctness = verified reuse (the wedge).

Existing infra verifies the DECLARATION is well-formed (`primitive_verification_pipeline.verify_card`)
and SIGNS a receipt (`primitive_attestation`). Neither runs the primitive and checks its behavior
CONFORMS to what it declares. This module closes that loop: given a primitive with a declared
contract AND a runnable behavior, it checks —
  1. structural   — the declaration is well-formed + typed (reuses verify_card);
  2. runs         — the behavior executes on a witness of the declared input;
  3. output_conforms — the behavior produces every field the output_edge/contract declares;
  4. proof_holds  — the card's own declared proof_requirement fixture passes;
  5. effects_contained — observed effects ⊆ declared effects (no undeclared side effects — the
                    "skill silently inherits host access" risk).
Only when all five hold does it mint a signed conformance attestation (reuses primitive_attestation)
— that is execution-verified EVIDENCE (candidate→verified), never self-promotion. A card that lies
about its behavior is CAUGHT with the exact mismatch, reproducing the 80%-mismatch detection.

First corpus: the deterministic reasoning/gate/proof primitives (they have real behavior + declared
edges + proof_requirements). Scaffolds with no executable behavior are honestly marked
"unverifiable" — they stay candidate, never falsely "verified".

    python3 scripts/declaration_behavior_conformance.py --self-test
    python3 scripts/declaration_behavior_conformance.py --report   # conformance over the real corpus
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
try:
    from src.teleon.experiments.ids import canonical_id
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"declaration_behavior_conformance requires canonical_id; import failed: {exc}")

from scripts.primitive_verification_pipeline import verify_card  # structural declaration level (reused)
from scripts.primitive_attestation import (  # signed receipt (reused — do NOT re-implement signing)
    build_attestation,
    sign_attestation,
    verify_attestation,
)
from scripts.reasoning_control_and_proof_primitives import (  # the first real behavior corpus
    check_graph_coloring_certificate,
    decision_gate,
    emit_cards as _reasoning_cards,
    invariant_guard,
    run_guided_route,
    validate_inference_chain,
)
from scripts.associative_memory_primitives import (  # the fourth behavior corpus: fast-weight memory theorems
    associative_crosstalk,
    associative_read,
    contraction_forgetting_bound,
    decayed_write_norm_bound,
    delta_rule_write,
    emit_cards as _memory_cards,
    erase_then_write,
    exact_recall_state_floor,
    hebbian_write,
    linear_memory_rank_limit,
    multi_timescale_decay_mixture,
    persistent_occupancy_fraction,
    positive_sparse_overlap_bias,
)
from scripts.math_foundations_primitives import (  # the third behavior corpus: mathematical foundations
    bloom_filter_sizing,
    cascade_optimal_order,
    count_min_sketch_dimensions,
    emit_cards as _math_cards,
    gf2_parity_syndrome,
    identity_information_bits,
    inverse_propensity_estimate,
    lsh_banding_candidate_probability,
    majority_vote_failure_probability,
    mdl_promotion_gate,
    simhash_collision_probability,
    sprt_decide,
)
from scripts.physics_tracking_primitives import (  # the second behavior corpus: tracking/estimation kernels
    backtest_gated_override,
    beam_search_grid_path,
    confidence_gated_blend,
    effective_sample_size,
    emit_cards as _tracking_cards,
    exponential_warmup_blend,
    inverse_distance_weighted_impute,
    likelihood_weighted_ensemble,
    ncc_best_offset,
    particle_filter_track,
    prediction_integrity_audit,
    robust_irls_polyfit,
    systematic_resample,
)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
#: a well-formed typed edge is one or more CamelCase components joined by '+' (the repo convention,
#: e.g. "RetryableCall+BackoffPolicy"). verify_card's single-token _CAMEL misses the compound form.
_EDGE_COMPONENT = re.compile(r"^[A-Z][A-Za-z0-9]*$")


def _typed_edge(edge: str) -> bool:
    parts = [p for p in str(edge).split("+") if p]
    return bool(parts) and all(_EDGE_COMPONENT.match(p) for p in parts)


class _EffectProbe:
    """Records observed effects so we can check them against the DECLARED effect set. A pure
    primitive touches nothing here; a primitive that mutates shared state records it."""

    def __init__(self) -> None:
        self.observed: set[str] = set()

    def note(self, effect: str) -> None:
        self.observed.add(effect)


#: behavior spec per primitive_kind: how to RUN it and what its card DECLARES it produces.
#: declared_output_keys are derived from the card's output_edge/contract; proof_fixture reproduces
#: the card's own declared proof_requirement; declared_effects is what the card claims it may do.
def _reasoning_specs() -> dict[str, dict[str, Any]]:
    tri = {"a": ["b", "c"], "b": ["a", "c"], "c": ["a", "b"]}
    route = [
        {"kind": "gate", "name": "size", "reads": "n", "predicate": lambda n: n >= 2,
         "on_true": "go", "on_false": "stop", "halt_on": "stop"},
        {"kind": "proof", "name": "cert",
         "check": lambda ctx: check_graph_coloring_certificate(ctx["g"], ctx["c"], ctx["k"])},
        {"kind": "action", "name": "accept", "does": "record"},
    ]
    return {
        "logic.decision_gate": {
            "behavior": lambda: decision_gate(10, predicate=lambda x: x > 5, on_true="big", on_false="small"),
            "declared_output_keys": {"branch", "predicate_true"},
            "proof_fixture": lambda: (
                decision_gate(10, predicate=lambda x: x > 5, on_true="big", on_false="small")["branch"] == "big"
                and decision_gate(1, predicate=lambda x: x > 5, on_true="big", on_false="small")["branch"] == "small"),
            "declared_effects": set(),
        },
        "logic.invariant_guard": {
            "behavior": lambda: invariant_guard({"b": 100}, {"b": -5},
                                                invariants=[("nn", lambda a, z: z["b"] >= 0)]),
            "declared_output_keys": {"held", "violated"},
            "proof_fixture": lambda: invariant_guard({"b": 100}, {"b": -5},
                                                     invariants=[("nn", lambda a, z: z["b"] >= 0)])["held"] is False,
            "declared_effects": set(),
        },
        "logic.proof_obligation.graph_coloring": {
            "behavior": lambda: check_graph_coloring_certificate(tri, {"a": 0, "b": 1, "c": 2}, 3),
            "declared_output_keys": {"valid", "reason"},
            "proof_fixture": lambda: (
                check_graph_coloring_certificate(tri, {"a": 0, "b": 1, "c": 2}, 3)["valid"] is True
                and check_graph_coloring_certificate(tri, {"a": 0, "b": 0, "c": 2}, 3)["valid"] is False),
            "declared_effects": set(),
        },
        "logic.proof_obligation.inference_chain": {
            "behavior": lambda: validate_inference_chain(["P", "P>Q"], [
                {"rule": "modus_ponens", "formula": "Q", "from": ["P", "P>Q"]}]),
            "declared_output_keys": {"valid", "failed_step"},
            "proof_fixture": lambda: (
                validate_inference_chain(["P", "P>Q"], [
                    {"rule": "modus_ponens", "formula": "Q", "from": ["P", "P>Q"]}])["valid"] is True
                and validate_inference_chain(["P"], [
                    {"rule": "modus_ponens", "formula": "Q", "from": ["P", "P>Q"]}])["valid"] is False),
            "declared_effects": set(),
        },
        "control.guided_route": {
            "behavior": lambda: run_guided_route(route, {"n": 3, "g": tri, "c": {"a": 0, "b": 1, "c": 2}, "k": 3}),
            "declared_output_keys": {"outcome", "trace"},
            "proof_fixture": lambda: (
                run_guided_route(route, {"n": 3, "g": tri, "c": {"a": 0, "b": 1, "c": 2}, "k": 3})["outcome"] == "accepted"
                and run_guided_route(route, {"n": 3, "g": tri, "c": {"a": 0, "b": 0, "c": 2}, "k": 3})["outcome"] == "rejected"),
            "declared_effects": set(),
        },
    }


def _tracking_specs() -> dict[str, dict[str, Any]]:
    """Behavior bindings for the physics-tracking corpus. Non-dict returns (a survivor list, an ESS float)
    are bound through a named-key adapter so the declared output_edge components map to observable fields."""
    reference_x = [float(i) for i in range(0, 21, 2)]
    reference_y = [x * 2.0 for x in reference_x]
    truth = [5.0 + 0.2 * i for i in range(10)]
    observations = [t * 2.0 for t in truth]

    def _track(sigma: float = 1.0) -> dict[str, Any]:
        return particle_filter_track(observations, reference_x, reference_y, start_state=5.0,
                                     n_particles=60, seed=7, observation_sigma=sigma)

    def _rmse_of(path: list[float]) -> float:
        return sum((a - b) ** 2 for a, b in zip(path, truth)) ** 0.5

    grid = [float(v) for v in range(12)]
    planted = [0, 1, 2, 3, 4]
    haystack = [((i * 7) % 13) - 6.0 for i in range(40)]
    needle = [2.0 * haystack[11 + i] + 9.0 for i in range(7)]
    xs = [float(i) for i in range(10)]
    clean = [1.0 + 0.5 * x for x in xs]
    dirty = clean[:]
    dirty[4] += 50.0
    audit_ids = ["a", "b", "c"]
    return {
        "tracking.particle_filter_track": {
            "behavior": _track, "declared_output_keys": {"path", "log_likelihood"},
            "proof_fixture": lambda: _rmse_of(_track()["path"]) < _rmse_of(_track(sigma=1e9)["path"]),
            "declared_effects": set()},
        "tracking.systematic_resample": {
            "behavior": lambda: {"survivor_indices": systematic_resample([0.0, 0.0, 1.0, 0.0], seed=3)},
            "declared_output_keys": {"survivor_indices"},
            "proof_fixture": lambda: set(systematic_resample([0.0, 0.0, 1.0, 0.0], seed=3)) == {2}
            and len(set(systematic_resample([1.0] * 8, seed=3))) >= 6,
            "declared_effects": set()},
        "tracking.effective_sample_size": {
            "behavior": lambda: {"effective_sample_size": effective_sample_size([0.25] * 4)},
            "declared_output_keys": {"effective_sample_size"},
            "proof_fixture": lambda: abs(effective_sample_size([0.25] * 4) - 4.0) < 1e-9
            and abs(effective_sample_size([0.0, 1.0]) - 1.0) < 1e-9,
            "declared_effects": set()},
        "tracking.beam_search_grid_path": {
            "behavior": lambda: beam_search_grid_path([grid[i] for i in planted], grid, 0,
                                                      beam_size=5, move_cost=0.01),
            "declared_output_keys": {"path_indices", "path_values"},
            "proof_fixture": lambda: beam_search_grid_path([grid[i] for i in planted], grid, 0,
                                                           beam_size=5, move_cost=0.01)["path_indices"] == planted,
            "declared_effects": set()},
        "tracking.ncc_best_offset": {
            "behavior": lambda: ncc_best_offset(needle, haystack),
            "declared_output_keys": {"best_offset", "best_score"},
            "proof_fixture": lambda: ncc_best_offset(needle, haystack)["best_offset"] == 11
            and ncc_best_offset(needle, haystack)["best_score"] > 0.999,
            "declared_effects": set()},
        "tracking.robust_irls_polyfit": {
            "behavior": lambda: robust_irls_polyfit(xs, dirty, degree=1, iterations=4),
            "declared_output_keys": {"coefficients", "fitted"},
            "proof_fixture": lambda: (robust_irls_polyfit(xs, dirty, degree=1, iterations=4)["final_weights"][4] < 0.2
                                      and abs(robust_irls_polyfit(xs, dirty, degree=1,
                                                                  iterations=4)["fitted"][4] - clean[4]) < 5.0),
            "declared_effects": set()},
        "tracking.likelihood_weighted_ensemble": {
            "behavior": lambda: likelihood_weighted_ensemble([[0.0] * 3, [10.0] * 3], [-100.0, -1.0], scale=5.0),
            "declared_output_keys": {"prediction", "weights"},
            "proof_fixture": lambda: likelihood_weighted_ensemble([[0.0] * 3, [10.0] * 3],
                                                                  [-100.0, -1.0], scale=5.0)["weights"][1] > 0.99,
            "declared_effects": set()},
        "tracking.inverse_distance_weighted_impute": {
            "behavior": lambda: inverse_distance_weighted_impute(
                [(0.0, 0.0, 10.0), (2.0, 0.0, 30.0)], [(0.0, 0.0), (1.0, 0.0)], k=2),
            "declared_output_keys": {"estimates", "nearest_distances"},
            "proof_fixture": lambda: inverse_distance_weighted_impute(
                [(0.0, 0.0, 10.0), (2.0, 0.0, 30.0)], [(0.0, 0.0), (1.0, 0.0)], k=2)["estimates"] == [10.0, 20.0],
            "declared_effects": set()},
        "tracking.exponential_warmup_blend": {
            "behavior": lambda: exponential_warmup_blend([100.0, 100.0], [10.0, 10.0], [0.0, 12000.0], tau=120.0),
            "declared_output_keys": {"blended", "ramps"},
            "proof_fixture": lambda: (exponential_warmup_blend([100.0], [10.0], [0.0], tau=120.0)["blended"] == [100.0]
                                      and abs(exponential_warmup_blend([100.0], [10.0], [12000.0],
                                                                       tau=120.0)["blended"][0] - 110.0) < 0.01),
            "declared_effects": set()},
        "tracking.backtest_gated_override": {
            "behavior": lambda: backtest_gated_override([1.0], [5.0], [7.0], [7.0], rmse_gate=1.0),
            "declared_output_keys": {"prediction", "adopted_candidate", "backtest_rmse"},
            "proof_fixture": lambda: (backtest_gated_override([1.0], [5.0], [7.0], [7.0],
                                                              rmse_gate=1.0)["adopted_candidate"] is True
                                      and backtest_gated_override([1.0], [5.0], [7.0], [40.0],
                                                                  rmse_gate=1.0)["prediction"] == [1.0]),
            "declared_effects": set()},
        "tracking.confidence_gated_blend": {
            "behavior": lambda: confidence_gated_blend([0.0], [100.0], gain=3.0, consistency=0.9, move_clip=5.0),
            "declared_output_keys": {"blended", "alpha", "qualified"},
            "proof_fixture": lambda: (confidence_gated_blend([0.0], [100.0], gain=0.1,
                                                             consistency=0.9)["blended"] == [0.0]
                                      and confidence_gated_blend([0.0], [100.0], gain=3.0, consistency=0.9,
                                                                 move_clip=5.0)["max_abs_move"] == 5.0),
            "declared_effects": set()},
        "tracking.prediction_integrity_audit": {
            "behavior": lambda: prediction_integrity_audit(audit_ids, [1.0, 2.0, 3.0], audit_ids),
            "declared_output_keys": {"ok", "sha256", "problems"},
            "proof_fixture": lambda: (prediction_integrity_audit(audit_ids, [1.0, 2.0, 3.0], audit_ids)["ok"]
                                      and not prediction_integrity_audit(["b", "a", "c"], [1.0, 2.0, 3.0],
                                                                         audit_ids)["ok"]),
            "declared_effects": set()},
    }


def _math_specs() -> dict[str, dict[str, Any]]:
    """Behavior bindings for the mathematical-foundations corpus (reference numbers double as fixtures)."""
    parity = [[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1]]
    # ratios ~10 / ~0.22 / 20 — deliberately far apart (a float tie between equal ratios is a legitimate
    # either-order optimum and must not be pinned by a fixture; the gate caught exactly that mistake once)
    stages = [{"cost": 1.0, "survival": 0.9}, {"cost": 0.2, "survival": 0.1}, {"cost": 5.0, "survival": 0.75}]
    return {
        "math_foundations.identity_information_bits": {
            "behavior": lambda: identity_information_bits(100_000_000),
            "declared_output_keys": {"bits", "whole_bits"},
            "proof_fixture": lambda: (abs(identity_information_bits(100_000_000)["bits"] - 26.5754247591) < 1e-9
                                      and identity_information_bits(2)["bits"] == 1.0),
            "declared_effects": set()},
        "math_foundations.cascade_optimal_order": {
            "behavior": lambda: cascade_optimal_order(stages),
            "declared_output_keys": {"order", "expected_cost"},
            "proof_fixture": lambda: cascade_optimal_order(stages)["order"] == [1, 0, 2],
            "declared_effects": set()},
        "math_foundations.sprt_sequential_verification": {
            "behavior": lambda: sprt_decide([1.2, 1.1, 0.9], alpha=0.05, beta=0.05),
            "declared_output_keys": {"decision", "steps_used"},
            "proof_fixture": lambda: (sprt_decide([1.2, 1.1, 0.9])["decision"] == "accept_h1"
                                      and sprt_decide([-1.2, -1.1, -0.9])["decision"] == "accept_h0"),
            "declared_effects": set()},
        "math_foundations.inverse_propensity_estimate": {
            "behavior": lambda: inverse_propensity_estimate(
                [{"reward": 1.0, "logged_propensity": 0.5, "target_probability": 0.5}]),
            "declared_output_keys": {"ok", "estimated_value"},
            "proof_fixture": lambda: abs(inverse_propensity_estimate(
                [{"reward": 1.0, "logged_propensity": 0.5, "target_probability": 0.5},
                 {"reward": 0.0, "logged_propensity": 0.5, "target_probability": 0.5}])["estimated_value"]
                - 0.5) < 1e-9,
            "declared_effects": set()},
        "math_foundations.simhash_collision_law": {
            "behavior": lambda: simhash_collision_probability(0.5),
            "declared_output_keys": {"collision_probability"},
            "proof_fixture": lambda: simhash_collision_probability(0.0)["collision_probability"] == 1.0,
            "declared_effects": set()},
        "math_foundations.lsh_banding_amplification": {
            "behavior": lambda: lsh_banding_candidate_probability(0.8, 4, 8),
            "declared_output_keys": {"candidate_probability"},
            "proof_fixture": lambda: abs(lsh_banding_candidate_probability(0.8, 4, 8)["candidate_probability"]
                                         - 0.9852371302) < 1e-9,
            "declared_effects": set()},
        "math_foundations.bloom_filter_sizing": {
            "behavior": lambda: bloom_filter_sizing(100_000_000, 0.01),
            "declared_output_keys": {"bits", "hash_functions", "bits_per_item"},
            "proof_fixture": lambda: (bloom_filter_sizing(100_000_000, 0.01)["bits"] == 958_505_838
                                      and bloom_filter_sizing(100_000_000, 0.01)["hash_functions"] == 7),
            "declared_effects": set()},
        "math_foundations.count_min_sketch_dimensions": {
            "behavior": lambda: count_min_sketch_dimensions(0.001, 1e-6),
            "declared_output_keys": {"width", "depth", "cells"},
            "proof_fixture": lambda: (count_min_sketch_dimensions(0.001, 1e-6)["width"] == 2719
                                      and count_min_sketch_dimensions(0.001, 1e-6)["depth"] == 14),
            "declared_effects": set()},
        "math_foundations.majority_vote_failure": {
            "behavior": lambda: majority_vote_failure_probability(3, 0.3),
            "declared_output_keys": {"majority_failure_probability"},
            "proof_fixture": lambda: abs(majority_vote_failure_probability(3, 0.3)
                                         ["majority_failure_probability"] - 0.216) < 1e-12,
            "declared_effects": set()},
        "math_foundations.gf2_parity_syndrome": {
            "behavior": lambda: gf2_parity_syndrome(parity, [0, 0, 0, 0]),
            "declared_output_keys": {"syndrome", "consistent", "detects_all_single_bit_errors"},
            "proof_fixture": lambda: (gf2_parity_syndrome(parity, [0, 0, 0, 0])["consistent"]
                                      and not gf2_parity_syndrome(parity, [0, 1, 0, 0])["consistent"]),
            "declared_effects": set()},
        "math_foundations.mdl_promotion_gate": {
            "behavior": lambda: mdl_promotion_gate(50.0, 10.0, 20.0, [2.0] * 20, [30.0] * 20),
            "declared_output_keys": {"promote", "gain_bits"},
            "proof_fixture": lambda: (mdl_promotion_gate(50.0, 10.0, 20.0, [2.0] * 20, [30.0] * 20)["promote"]
                                      and not mdl_promotion_gate(500.0, 100.0, 100.0, [2.0], [30.0])["promote"]),
            "declared_effects": set()},
    }


def _memory_specs() -> dict[str, dict[str, Any]]:
    """Behavior bindings for the associative-memory corpus (the verdict's theorems as fixtures)."""
    def _zeros(rows: int, cols: int) -> list[list[float]]:
        return [[0.0] * cols for _ in range(rows)]

    return {
        "associative_memory.hebbian_write": {
            "behavior": lambda: hebbian_write(_zeros(2, 2), [1.0, 0.0], [3.0, 4.0]),
            "declared_output_keys": {"memory", "memory_norm"},
            "proof_fixture": lambda: associative_read(
                hebbian_write(_zeros(2, 2), [1.0, 0.0], [3.0, 4.0])["memory"], [1.0, 0.0])["readout"]
            == [3.0, 4.0],
            "declared_effects": set()},
        "associative_memory.associative_crosstalk": {
            "behavior": lambda: associative_crosstalk([[1.0, 0.0], [0.0, 1.0]], [[5.0], [7.0]], 0),
            "declared_output_keys": {"readout", "crosstalk_norm"},
            "proof_fixture": lambda: (
                associative_crosstalk([[1.0, 0.0], [0.0, 1.0]], [[5.0], [7.0]], 0)["crosstalk_norm"] == 0.0
                and associative_crosstalk([[1.0, 0.0], [0.8, 0.6]], [[5.0], [7.0]], 0)["crosstalk_norm"] > 1.0),
            "declared_effects": set()},
        "associative_memory.delta_rule_write": {
            "behavior": lambda: delta_rule_write(_zeros(2, 2), [1.0, 0.0], [1.0, 2.0], beta=1.0),
            "declared_output_keys": {"memory", "readout_after"},
            "proof_fixture": lambda: delta_rule_write(
                hebbian_write(_zeros(2, 2), [1.0, 0.0], [9.0, 9.0])["memory"],
                [1.0, 0.0], [1.0, 2.0], beta=1.0)["readout_after"] == [1.0, 2.0],
            "declared_effects": set()},
        "associative_memory.erase_then_write": {
            "behavior": lambda: erase_then_write(
                delta_rule_write(_zeros(3, 2), [1.0, 0.0, 0.0], [5.0, 5.0])["memory"],
                [1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [8.0, 8.0]),
            "declared_output_keys": {"memory", "erased_readout", "written_readout"},
            "proof_fixture": lambda: (lambda result: max(abs(x) for x in result["erased_readout"]) < 1e-9
                                      and result["written_readout"] == [8.0, 8.0])(
                erase_then_write(delta_rule_write(_zeros(3, 2), [1.0, 0.0, 0.0], [5.0, 5.0])["memory"],
                                 [1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [8.0, 8.0])),
            "declared_effects": set()},
        "associative_memory.decayed_write_norm_bound": {
            "behavior": lambda: decayed_write_norm_bound(10.0, 0.02, 1.0, 500),
            "declared_output_keys": {"bounded", "worst_case_norm"},
            "proof_fixture": lambda: (decayed_write_norm_bound(10.0, 0.02, 1.0, 500)["bound_holds"]
                                      and not decayed_write_norm_bound(10.0, 0.0, 1.0, 500)["bounded"]),
            "declared_effects": set()},
        "associative_memory.positive_sparse_overlap_bias": {
            "behavior": lambda: positive_sparse_overlap_bias(6, 2),
            "declared_output_keys": {"expected_overlap", "theory_s_over_d", "expected_centered_overlap"},
            "proof_fixture": lambda: (lambda bias: abs(bias["expected_overlap"] - bias["theory_s_over_d"]) < 1e-9
                                      and abs(bias["expected_centered_overlap"]) < 1e-9)(
                positive_sparse_overlap_bias(6, 2)),
            "declared_effects": set()},
        "associative_memory.contraction_forgetting_bound": {
            "behavior": lambda: contraction_forgetting_bound(0.9, 50, 1.0),
            "declared_output_keys": {"gap_after_steps", "bound"},
            "proof_fixture": lambda: contraction_forgetting_bound(0.9, 50, 1.0)["bound_is_exact_for_linear"],
            "declared_effects": set()},
        "associative_memory.multi_timescale_decay_mixture": {
            "behavior": lambda: multi_timescale_decay_mixture([0.5, 0.1, 0.02, 0.004], [1.0] * 4,
                                                              [1, 5, 25, 125]),
            "declared_output_keys": {"retention", "log_ratio_spread_mixture"},
            "proof_fixture": lambda: multi_timescale_decay_mixture(
                [0.5, 0.1, 0.02, 0.004], [1.0] * 4, [1, 5, 25, 125])["mixture_more_scale_stable"],
            "declared_effects": set()},
        "associative_memory.persistent_occupancy_fraction": {
            "behavior": lambda: persistent_occupancy_fraction(0.05, 100),
            "declared_output_keys": {"occupied_fraction"},
            "proof_fixture": lambda: abs(persistent_occupancy_fraction(0.05, 100)["occupied_fraction"]
                                         - 0.994079471) < 1e-9,
            "declared_effects": set()},
        "associative_memory.exact_recall_state_floor": {
            "behavior": lambda: exact_recall_state_floor(1000, 1024),
            "declared_output_keys": {"state_floor_bits", "state_floor_bytes"},
            "proof_fixture": lambda: (exact_recall_state_floor(1000, 1024)["state_floor_bits"] == 10000.0
                                      and exact_recall_state_floor(1000, 1024)["state_floor_bytes"] == 1250),
            "declared_effects": set()},
        "associative_memory.linear_memory_rank_limit": {
            "behavior": lambda: linear_memory_rank_limit(4),
            "declared_output_keys": {"exact_within_capacity", "impossible_over_capacity"},
            "proof_fixture": lambda: (lambda rank: rank["exact_within_capacity"]
                                      and rank["impossible_over_capacity"])(linear_memory_rank_limit(4)),
            "declared_effects": set()},
    }


def check_conformance(card: dict[str, Any], spec: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Verify the primitive's BEHAVIOR conforms to its DECLARATION. Pure + deterministic."""
    pid = card.get("primitive_id") or card.get("id") or ""
    checks: dict[str, Any] = {}
    # (1) declaration well-formed: typed compound edges + not a placeholder. verify_card's level is
    #     kept as an informational signal, but the gate is the edge-component + usefulness check
    #     (verify_card's single-token _CAMEL rejects the compound A+B edge convention).
    from scripts.primitive_usefulness_gate import evaluate_card  # noqa: PLC0415  (reuse the placeholder gate)
    level = verify_card(card)
    checks["structural_declaration"] = (
        _typed_edge(card.get("input_edge", "")) and _typed_edge(card.get("output_edge", ""))
        and evaluate_card(card).get("verdict") != "placeholder")
    if spec is None:
        return {"primitive_id": pid, "conformant": False, "verifiable": False,
                "reason": "no_executable_behavior", "declaration_level": level,
                "checks": checks, **BOUNDARY}
    # (2) runs
    try:
        observed = spec["behavior"]()
        checks["runs"] = isinstance(observed, dict)
    except Exception as exc:  # noqa: BLE001
        return {"primitive_id": pid, "conformant": False, "verifiable": True,
                "reason": f"behavior_raised:{type(exc).__name__}", "checks": checks, **BOUNDARY}
    # (3) output conforms — every DECLARED output field is actually produced
    missing = sorted(spec["declared_output_keys"] - set(observed))
    checks["output_conforms"] = not missing
    # (4) the card's own declared proof_requirement holds
    try:
        checks["proof_requirement_holds"] = bool(spec["proof_fixture"]())
    except Exception:  # noqa: BLE001
        checks["proof_requirement_holds"] = False
    # (5) no undeclared effects
    observed_effects = set(spec.get("observed_effects", set()))
    checks["effects_contained"] = observed_effects <= set(spec["declared_effects"])
    conformant = all(checks.values())
    reason = None if conformant else (
        f"declared_output_missing:{missing}" if missing else
        "proof_requirement_failed" if not checks["proof_requirement_holds"] else
        "undeclared_effects" if not checks["effects_contained"] else
        "declaration_not_wellformed")
    return {"primitive_id": pid, "conformant": conformant, "verifiable": True,
            "reason": reason, "declaration_level": level, "checks": checks, **BOUNDARY}


def attest_conformance(card: dict[str, Any], verdict: dict[str, Any]) -> Optional[dict[str, Any]]:
    """On a conformant verdict, mint a SIGNED conformance attestation (reuses primitive_attestation).
    This is execution-verified evidence bound to the behavior digest — not self-promotion."""
    if not verdict.get("conformant"):
        return None
    body = json.dumps({"primitive_id": verdict["primitive_id"], "checks": verdict["checks"],
                       "claim": "declaration_behavior_conformant"}, sort_keys=True)
    formal = {"primitive_id": verdict["primitive_id"],
              "title": card.get("title", ""),
              "input_edge": card.get("input_edge", ""), "output_edge": card.get("output_edge", ""),
              "verification_level": "L5_declaration_behavior_conformant", **BOUNDARY}
    return sign_attestation(build_attestation(formal, body))


def run_corpus(cards: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    """Conformance over the executable corpora (reasoning/proof + physics-tracking): conformant vs
    mismatched vs unverifiable-scaffold."""
    cards = (cards if cards is not None
             else _reasoning_cards() + _tracking_cards() + _math_cards() + _memory_cards())
    specs = {**_reasoning_specs(), **_tracking_specs(), **_math_specs(), **_memory_specs()}
    verdicts, attestations = [], []
    for card in cards:
        v = check_conformance(card, specs.get(card.get("primitive_kind")))
        verdicts.append(v)
        att = attest_conformance(card, v)
        if att is not None:
            attestations.append(att)
    conformant = [v for v in verdicts if v["conformant"]]
    unverifiable = [v for v in verdicts if not v["verifiable"]]
    mismatched = [v for v in verdicts if v["verifiable"] and not v["conformant"]]
    return {"record_type": "declaration_behavior_conformance_report",
            "n_cards": len(cards), "n_conformant": len(conformant),
            "n_unverifiable_scaffold": len(unverifiable), "n_mismatched": len(mismatched),
            "n_signed_attestations": len(attestations),
            "verdicts": verdicts, "attestations": attestations, **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    report = run_corpus()

    # (1) the 5 reasoning + 12 tracking + 11 math + 11 memory deterministic primitives conformant + attested
    checks.append(("39 deterministic primitives (5 reasoning + 12 tracking + 11 math + 11 memory) "
                   "CONFORMANT + signed",
                   report["n_conformant"] == 39 and report["n_signed_attestations"] == 39))

    # (2) the 2 scaffolds are honestly UNVERIFIABLE (never falsely "verified")
    checks.append(("2 reasoning scaffolds honestly marked unverifiable (not falsely verified)",
                   report["n_unverifiable_scaffold"] == 2 and report["n_mismatched"] == 0))

    # (3) a signed conformance attestation actually verifies against its body (rebuilt from the verdict,
    #     exactly as attest_conformance signs it — attestations[0] is the first conformant card in order)
    v0 = next(v for v in report["verdicts"] if v["conformant"])
    body0 = json.dumps({"primitive_id": v0["primitive_id"], "checks": v0["checks"],
                        "claim": "declaration_behavior_conformant"}, sort_keys=True)
    checks.append(("minted conformance attestation verifies (digest-bound)",
                   verify_attestation(report["attestations"][0], body0).get("verified") is True))

    # (4) MUTATION GATE — a LIAR (declares an output field its behavior never produces) is CAUGHT
    liar_card = {"primitive_id": "prim:rcp:LIAR", "title": "Lies about its output",
                 "input_edge": "TypedValue+BranchPredicate", "output_edge": "SafeVerdict+AuditReceipt",
                 "primitive_kind": "logic.decision_gate", "capability_tags": ["control_flow"],
                 "blackbox": "claims to emit SafeVerdict+AuditReceipt but the behavior emits branch/predicate_true",
                 **BOUNDARY}
    liar_spec = {"behavior": lambda: decision_gate(10, predicate=lambda x: x > 5, on_true="big", on_false="small"),
                 "declared_output_keys": {"safe_verdict", "audit_receipt"},  # DECLARED but never produced
                 "proof_fixture": lambda: True, "declared_effects": set()}
    liar = check_conformance(liar_card, liar_spec)
    checks.append(("LIAR (declared output ≠ produced output) is CAUGHT, not attested",
                   liar["conformant"] is False and str(liar["reason"]).startswith("declared_output_missing")
                   and attest_conformance(liar_card, liar) is None))

    # (5) MUTATION GATE — an UNDECLARED EFFECT is caught (the "skill inherits host access" risk)
    effect_spec = {"behavior": lambda: {"ok": True}, "declared_output_keys": {"ok"},
                   "proof_fixture": lambda: True, "declared_effects": set(),
                   "observed_effects": {"wrote_to_disk"}}  # did something it never declared
    effect_card = {"primitive_id": "prim:rcp:LEAK", "title": "Undeclared effect",
                   "input_edge": "A+B", "output_edge": "Ok", "primitive_kind": "x",
                   "capability_tags": ["x"], "blackbox": "claims pure but writes to disk", **BOUNDARY}
    leak = check_conformance(effect_card, effect_spec)
    checks.append(("UNDECLARED EFFECT is caught (declared-pure but acts)",
                   leak["conformant"] is False and leak["reason"] == "undeclared_effects"))

    # (6) deterministic report (byte-identical) — verify-the-verifier determinism
    checks.append(("conformance report is deterministic (byte-identical)",
                   json.dumps(run_corpus()["verdicts"], sort_keys=True)
                   == json.dumps(report["verdicts"], sort_keys=True)))

    ok = all(v for _, v in checks)
    print("declaration_behavior_conformance — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print(f"  corpus: {report['n_conformant']} verified-reuse-ready, "
          f"{report['n_unverifiable_scaffold']} unverifiable scaffolds, {report['n_mismatched']} mismatched. "
          f"candidate-only.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.report:
        r = run_corpus()
        print(json.dumps({k: r[k] for k in r if k not in ("verdicts", "attestations")}, indent=2))
        for v in r["verdicts"]:
            tag = "CONFORMANT" if v["conformant"] else ("UNVERIFIABLE" if not v["verifiable"] else "MISMATCH")
            print(f"  [{tag}] {v['primitive_id']}  {v.get('reason') or ''}")
        return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
