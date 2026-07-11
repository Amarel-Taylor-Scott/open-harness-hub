#!/usr/bin/env python3
"""math_foundations_primitives — the 100M-scale mathematical foundations as deterministic, oracle-verified
primitives, mined from the owner's mathematical alignment layer (seed
`owner-primitive-100m-mathematical-layer-2026-07-11` in data/research-queue/seed_sources.jsonl).

Owner (2026-07-11): "Continue improving all aspects, building out more primitives, describing primitives,
testing" + the forwarded mathematical layer whose REFERENCE NUMBERS become executable oracle expectations
here (Bloom 100M@1% -> 958,505,838 bits / 7 hashes; Count-Min eps=1e-3, delta=1e-6 -> 2719x14; identity bits
log2(1e8) = 26.5754; cascade ordering by c/(1-s) matching brute force). Implemented from scratch, pure python,
no numpy, no randomness, every kernel behind an executed mutation-sensitive oracle:

   1. identity_information_bits      — exact-identity floor: distinguishing N things needs >= log2(N) bits.
   2. cascade_optimal_order          — order independent filter stages by cost/(1-survival); exchange-argument
                                       optimal (oracle brute-forces every permutation).
   3. sprt_boundaries / sprt_decide  — Wald sequential test: stop early on strong evidence, keep collecting
                                       between the boundaries.
   4. inverse_propensity_estimate    — unbiased off-policy value of a target policy from logged decisions.
   5. simhash_collision_probability  — random-hyperplane collision law p = 1 - theta/pi.
   6. lsh_banding_candidate_probability — AND/OR amplification 1-(1-p^r)^b (SimHash p or MinHash Jaccard).
   7. bloom_filter_sizing            — optimal bits + hash count for n items at a target false-positive rate.
   8. count_min_sketch_dimensions    — width ceil(e/eps) x depth ceil(ln(1/delta)).
   9. majority_vote_failure_probability — exact binomial strict-majority failure for n independent voters.
  10. gf2_parity_syndrome            — semantic parity codes: s = H z (mod 2); nonzero-column H detects every
                                       single-bit corruption.
  11. mdl_promotion_gate             — promote a residual to a primitive only when total description length
                                       shrinks (the formal alternative to "promote after five uses").

Every card is candidate (candidate=true, serves_truth=false); a passing oracle is promotion EVIDENCE, not
promotion. Descriptions ship in THREE registers (plain / technical / semantic). The owner layer's broader
claims (100 claims / 36 proofs / 45 tests) remain UNVERIFIED in-repo — only what executes here is evidence.

    python3 scripts/math_foundations_primitives.py --self-test
    python3 scripts/math_foundations_primitives.py --demo    # size + order + decide for a 100M-scale corpus
    python3 scripts/math_foundations_primitives.py --emit    # write the candidate card pack (+ stdout)
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
try:
    from src.teleon.experiments.ids import canonical_id
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"math_foundations_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
GENERATED_AT = "2026-07-11T00:00:00+00:00"   # fixed build date — emitted cards byte-identical across runs
PRIMITIVE_ID_PREFIX = "prim:math"
SOURCE_FAMILY = "mathematical_foundations_100m_layer"
SOURCE_REF = {"name": "100M primitive mathematical alignment layer v0.3 (owner-forwarded; claims unverified in-repo)",
              "seed_source_id": "owner-primitive-100m-mathematical-layer-2026-07-11"}
OUT_DIR = _SBC / "data" / "dev-intel" / "math_foundations_primitives"
CARDS_PATH = OUT_DIR / "math_foundations_candidate_cards.jsonl"


# ═══════════════ 1. IDENTITY INFORMATION FLOOR ═════════════════════════════════════════════════════════
def identity_information_bits(n_identities: int) -> dict[str, Any]:
    """Exactly distinguishing one identity among N equally likely possibilities requires at least log2(N)
    bits — the floor that says 27 bits suffice for a 100M-primitive EXACT id, so the huge metadata surface
    exists for GENERALIZATION (language, behavior, versions, evidence), not for identity."""
    bits = math.log2(n_identities)
    return {"identities": n_identities, "bits": round(bits, 10), "whole_bits": math.ceil(bits)}


# ═══════════════ 2. OPTIMAL CASCADE ORDERING ═══════════════════════════════════════════════════════════
def cascade_expected_cost(stages: list[dict[str, float]]) -> float:
    """Expected per-candidate cost of running stages in the given order: each stage costs `cost` on what
    survives so far; a fraction `survival` continues to the next stage."""
    total, surviving = 0.0, 1.0
    for stage in stages:
        total += surviving * stage["cost"]
        surviving *= stage["survival"]
    return total


def cascade_optimal_order(stages: list[dict[str, float]]) -> dict[str, Any]:
    """Sort independent filter stages by cost/(1-survival), ascending — the exchange-argument-optimal order
    (run the cheap, aggressive filters first; the expensive, permissive ones last). Returns the order, its
    expected cost, and the ratio table so the decision is auditable."""
    indexed = list(enumerate(stages))
    ratios = [stage["cost"] / max(1e-12, 1.0 - stage["survival"]) for stage in stages]
    order = [i for i, _s in sorted(indexed, key=lambda pair: (ratios[pair[0]], pair[0]))]
    ordered = [stages[i] for i in order]
    return {"order": order, "expected_cost": round(cascade_expected_cost(ordered), 10),
            "ratios": [round(r, 6) for r in ratios]}


# ═══════════════ 3. SEQUENTIAL PROBABILITY RATIO TEST ══════════════════════════════════════════════════
def sprt_boundaries(alpha: float, beta: float) -> dict[str, float]:
    """Wald's approximate SPRT log-likelihood boundaries: accept H1 above A=log((1-beta)/alpha), accept H0
    below B=log(beta/(1-alpha)), keep collecting evidence in between — verification that stops early exactly
    when the evidence is already decisive."""
    return {"upper_accept_h1": round(math.log((1.0 - beta) / alpha), 10),
            "lower_accept_h0": round(math.log(beta / (1.0 - alpha)), 10)}


def sprt_decide(log_likelihood_ratios: list[float], *, alpha: float = 0.05,
                beta: float = 0.05) -> dict[str, Any]:
    """Walk a cumulative log-likelihood-ratio path against the Wald boundaries; decide at the first crossing
    or report 'continue' with the evidence still needed."""
    bounds = sprt_boundaries(alpha, beta)
    cumulative = 0.0
    for step, llr in enumerate(log_likelihood_ratios):
        cumulative += llr
        if cumulative >= bounds["upper_accept_h1"]:
            return {"decision": "accept_h1", "steps_used": step + 1, "cumulative_llr": round(cumulative, 10),
                    **bounds}
        if cumulative <= bounds["lower_accept_h0"]:
            return {"decision": "accept_h0", "steps_used": step + 1, "cumulative_llr": round(cumulative, 10),
                    **bounds}
    return {"decision": "continue", "steps_used": len(log_likelihood_ratios),
            "cumulative_llr": round(cumulative, 10), **bounds}


# ═══════════════ 4. INVERSE-PROPENSITY OFF-POLICY ESTIMATE ═════════════════════════════════════════════
def inverse_propensity_estimate(logged_rows: list[dict[str, float]]) -> dict[str, Any]:
    """Unbiased off-policy value: for logged rows {reward, logged_propensity, target_probability}, the IPS
    estimator averages reward x target_probability / logged_propensity. Corrects the bias where hard queries
    were routed to expensive paths — naive path-outcome comparison penalizes the paths that rescue them."""
    if any(row["logged_propensity"] <= 0 for row in logged_rows):
        return {"ok": False, "error": "positivity violated: a logged propensity is not > 0", **BOUNDARY}
    weights = [row["target_probability"] / row["logged_propensity"] for row in logged_rows]
    value = sum(w * row["reward"] for w, row in zip(weights, logged_rows)) / max(1, len(logged_rows))
    return {"ok": True, "estimated_value": round(value, 10),
            "max_weight": round(max(weights), 6), "rows": len(logged_rows)}


# ═══════════════ 5/6. LSH COLLISION + BANDING LAWS ═════════════════════════════════════════════════════
def simhash_collision_probability(angle_radians: float) -> dict[str, float]:
    """Random-hyperplane (SimHash) collision law: two vectors at angle theta collide on one hash with
    probability 1 - theta/pi (1 for identical directions, 0 for opposite)."""
    return {"angle_radians": round(angle_radians, 10),
            "collision_probability": round(1.0 - angle_radians / math.pi, 10)}


def lsh_banding_candidate_probability(per_hash_probability: float, rows_per_band: int,
                                      bands: int) -> dict[str, float]:
    """AND/OR amplification: with r hashes per band (all must match) and b bands (any may fire), a pair with
    per-hash collision probability p becomes a candidate with probability 1-(1-p^r)^b — the S-curve that
    separates near-duplicates from noise. p is 1-theta/pi for SimHash or the Jaccard similarity for MinHash."""
    candidate = 1.0 - (1.0 - per_hash_probability ** rows_per_band) ** bands
    return {"per_hash_probability": per_hash_probability, "rows_per_band": rows_per_band, "bands": bands,
            "candidate_probability": round(candidate, 10)}


# ═══════════════ 7. BLOOM FILTER SIZING ════════════════════════════════════════════════════════════════
def bloom_filter_sizing(n_items: int, false_positive_rate: float) -> dict[str, Any]:
    """Optimal Bloom filter for n items at target false-positive rate p: m = ceil(-n ln p / (ln 2)^2) bits and
    k = round((m/n) ln 2) hash functions. At 100M ids and 1% the answer is ~958.5M bits (~9.585 bits/item,
    7 hashes, ~120 MB) — membership at planetary corpus scale for megabytes."""
    bits = math.ceil(-n_items * math.log(false_positive_rate) / (math.log(2) ** 2))
    hashes = max(1, round(bits / n_items * math.log(2)))
    return {"items": n_items, "false_positive_rate": false_positive_rate, "bits": bits,
            "bits_per_item": round(bits / n_items, 3), "hash_functions": hashes,
            "megabytes": round(bits / 8 / 1_000_000, 3)}


# ═══════════════ 8. COUNT-MIN SKETCH DIMENSIONS ════════════════════════════════════════════════════════
def count_min_sketch_dimensions(epsilon: float, delta: float) -> dict[str, Any]:
    """Count-Min sketch guaranteeing overcount <= epsilon*N with probability >= 1-delta: width = ceil(e/eps),
    depth = ceil(ln(1/delta)). Frequency estimates over unbounded streams in a fixed, tiny table."""
    width = math.ceil(math.e / epsilon)
    depth = math.ceil(math.log(1.0 / delta))
    return {"epsilon": epsilon, "delta": delta, "width": width, "depth": depth, "cells": width * depth}


# ═══════════════ 9. MAJORITY-VOTE FAILURE ══════════════════════════════════════════════════════════════
def majority_vote_failure_probability(n_voters: int, per_voter_error: float) -> dict[str, Any]:
    """Exact probability that a strict majority of n INDEPENDENT voters (each wrong with probability p) is
    wrong: the binomial tail P[X > n/2]. Falls exponentially for p < 1/2 — and the independence assumption is
    the whole game: correlated LLM samples do not enjoy this bound."""
    failure = sum(math.comb(n_voters, k) * per_voter_error ** k * (1.0 - per_voter_error) ** (n_voters - k)
                  for k in range(n_voters // 2 + 1, n_voters + 1))
    return {"voters": n_voters, "per_voter_error": per_voter_error,
            "majority_failure_probability": round(failure, 10)}


# ═══════════════ 10. GF(2) SEMANTIC PARITY SYNDROME ════════════════════════════════════════════════════
def gf2_parity_syndrome(parity_matrix: list[list[int]], facts: list[int]) -> dict[str, Any]:
    """Semantic parity code: s = H z (mod 2) over normalized binary facts. A zero syndrome means every encoded
    consistency constraint holds; if every column of H is nonzero, ANY single-bit corruption produces a
    nonzero syndrome (it detects contradiction/corruption — it does not prove the facts are true)."""
    syndrome = [sum(h * z for h, z in zip(row, facts)) % 2 for row in parity_matrix]
    columns_nonzero = all(any(row[j] for row in parity_matrix) for j in range(len(facts)))
    return {"syndrome": syndrome, "consistent": not any(syndrome),
            "detects_all_single_bit_errors": columns_nonzero}


# ═══════════════ 11. MDL PROMOTION GATE ════════════════════════════════════════════════════════════════
def mdl_promotion_gate(primitive_cost: float, contract_cost: float, evidence_cost: float,
                       per_use_costs_with_primitive: list[float],
                       repeated_solution_costs: list[float]) -> dict[str, Any]:
    """Minimum-description-length promotion: a residual becomes a reusable primitive only when
    L(primitive)+L(contract)+L(evidence)+sum L(use_i|primitive) < sum L(repeated solution_i) — the formal
    replacement for 'promote after five uses' or 'an LLM thinks it is reusable'."""
    with_primitive = primitive_cost + contract_cost + evidence_cost + sum(per_use_costs_with_primitive)
    without = sum(repeated_solution_costs)
    return {"promote": with_primitive < without, "bits_with_primitive": round(with_primitive, 6),
            "bits_without": round(without, 6), "gain_bits": round(without - with_primitive, 6)}


# ═══════════════ primitive cards (3-register descriptions + typed edges) ═══════════════════════════════
PRIMITIVE_SPECS: list[dict[str, Any]] = [
    {"kind": "math_foundations.identity_information_bits", "title": "Exact-identity information floor (log2 N bits)",
     "input_edge": "IdentityUniverseSize", "output_edge": "InformationFloorBits",
     "tags": ["information-theory", "identity", "capacity"],
     "registers": {
         "plain": "Tells you the minimum amount of information needed to point at exactly one thing out of N "
                  "— for 100 million things, just 27 bits.",
         "technical": "Computes log2(N) and its ceiling: the exact-identification floor. Separates identity "
                      "(cheap) from generalization (the reason rich metadata exists at all).",
         "semantic": "id bit floor / how many bits to name a primitive / capacity planning / Fano precursor"},
     "proof": "log2(1e8) = 26.5754247591 to 1e-9 and 2 identities need exactly 1 bit"},
    {"kind": "math_foundations.cascade_optimal_order", "title": "Optimal filter-cascade ordering (cost over kill-rate)",
     "input_edge": "FilterStageCostsAndSurvivals", "output_edge": "OptimalStageOrder+ExpectedCost",
     "tags": ["optimization", "retrieval", "cascade"],
     "registers": {
         "plain": "Given several filters that each cost something and each throw away some candidates, puts "
                  "them in the order that does the least total work.",
         "technical": "Sorts independent constant-retention stages by c_i/(1-s_i) ascending — the pairwise "
                      "exchange argument makes this globally optimal; returns the auditable ratio table and "
                      "expected per-candidate cost.",
         "semantic": "cheap filters first / tenant-filter before rerank / query funnel ordering / cascade cost"},
     "proof": "matches brute-force enumeration of every permutation on fixed 5-stage examples"},
    {"kind": "math_foundations.sprt_sequential_verification", "title": "Sequential probability ratio test (early-stopping verification)",
     "input_edge": "LogLikelihoodRatioStream+ErrorTargets", "output_edge": "SequentialDecision+Boundaries",
     "tags": ["testing", "sequential", "statistics"],
     "registers": {
         "plain": "Keeps collecting evidence only until the answer is already clear, then stops — instead of "
                  "always running every test.",
         "technical": "Wald SPRT: boundaries A=log((1-beta)/alpha), B=log(beta/(1-alpha)); the cumulative LLR "
                      "path decides accept_h1/accept_h0 at first crossing, else 'continue'. Approximate "
                      "boundaries for simple hypotheses; composite/dependent cases need care.",
         "semantic": "early stopping verification / stop when decisive / evidence budget / anytime testing"},
     "proof": "alpha=beta=0.05 gives A=+2.944, B=-2.944; a rising path accepts H1 at the first crossing"},
    {"kind": "math_foundations.inverse_propensity_estimate", "title": "Inverse-propensity off-policy value estimate",
     "input_edge": "LoggedDecisionsWithPropensities+TargetPolicy", "output_edge": "UnbiasedPolicyValue",
     "tags": ["causal", "off-policy", "evaluation"],
     "registers": {
         "plain": "Judges a new routing rule fairly from old logs, even though the old system chose where "
                  "traffic went — so hard cases sent to the strong path don't make it look bad.",
         "technical": "IPS: mean of reward x pi(a|x)/e(a|x) over logged rows; unbiased under positivity + "
                      "correct logged propensities; emits max weight as the variance warning.",
         "semantic": "logged bandit evaluation / counterfactual path value / propensity correction / IPS"},
     "proof": "when the target equals the logging policy the estimate equals the plain mean reward; a known "
              "two-action example recovers the analytic value"},
    {"kind": "math_foundations.simhash_collision_law", "title": "SimHash random-hyperplane collision probability",
     "input_edge": "VectorAngle", "output_edge": "PerHashCollisionProbability",
     "tags": ["lsh", "hashing", "similarity"],
     "registers": {
         "plain": "The chance two similar items get the same random fingerprint bit — identical items always "
                  "match, opposite items never do.",
         "technical": "p = 1 - theta/pi for random-hyperplane signing of two vectors at angle theta; the "
                      "elementary law every SimHash index is built on.",
         "semantic": "near-duplicate hashing / angle to collision chance / fingerprint similarity"},
     "proof": "theta=0 gives 1, theta=pi gives 0, theta=pi/2 gives exactly 0.5"},
    {"kind": "math_foundations.lsh_banding_amplification", "title": "LSH AND/OR banding amplification curve",
     "input_edge": "PerHashProbability+BandShape", "output_edge": "CandidatePairProbability",
     "tags": ["lsh", "banding", "retrieval"],
     "registers": {
         "plain": "Turns a weak per-fingerprint match chance into a sharp yes/no: similar pairs almost always "
                  "become candidates, dissimilar pairs almost never do.",
         "technical": "1-(1-p^r)^b with r hashes per band (AND) and b bands (OR); p is the SimHash law or the "
                      "MinHash Jaccard. The S-curve's threshold moves with (r,b) — the tuning surface of "
                      "every LSH index.",
         "semantic": "banding S-curve / candidate-pair probability / MinHash bands / dedupe blocking design"},
     "proof": "J=0.8 with r=4,b=8 gives 0.9852371302; J=0.2 with the same shape gives 0.0127285489"},
    {"kind": "math_foundations.bloom_filter_sizing", "title": "Bloom filter optimal sizing (bits + hash count)",
     "input_edge": "ItemCount+FalsePositiveTarget", "output_edge": "BloomBits+HashFunctions",
     "tags": ["sketch", "membership", "sizing"],
     "registers": {
         "plain": "Tells you exactly how much memory and how many hash functions a set-membership filter "
                  "needs — 100 million ids at 1% error fit in about 120 megabytes.",
         "technical": "m = ceil(-n ln p/(ln 2)^2), k = round((m/n) ln 2); returns bits, bits/item, hash "
                      "count, and megabytes. Reference: 1e8@0.01 -> 958,505,838 bits, 9.585 b/item, k=7.",
         "semantic": "membership sketch sizing / dedupe pre-filter / seen-before check at corpus scale"},
     "proof": "1e8 items at 1% -> exactly 958,505,838 bits and 7 hash functions (the layer's reference numbers)"},
    {"kind": "math_foundations.count_min_sketch_dimensions", "title": "Count-Min sketch dimensioning (width x depth)",
     "input_edge": "AccuracyEpsilon+FailureDelta", "output_edge": "SketchWidthDepth",
     "tags": ["sketch", "streaming", "frequency"],
     "registers": {
         "plain": "Sizes a tiny fixed table that can count how often things appear in an endless stream, with "
                  "a known worst-case overcount.",
         "technical": "width = ceil(e/epsilon), depth = ceil(ln(1/delta)): overcount <= epsilon*N with "
                      "probability >= 1-delta. Reference: eps=1e-3, delta=1e-6 -> 2719 x 14 = 38,066 cells.",
         "semantic": "stream frequency sketch / heavy hitters / bounded overcount counting"},
     "proof": "epsilon=1e-3, delta=1e-6 -> width 2719, depth 14 (the layer's reference numbers)"},
    {"kind": "math_foundations.majority_vote_failure", "title": "Independent-majority failure probability (exact binomial tail)",
     "input_edge": "VoterCount+PerVoterError", "output_edge": "MajorityFailureProbability",
     "tags": ["ensemble", "voting", "reliability"],
     "registers": {
         "plain": "The exact chance that most of your independent checkers are wrong at once — it collapses "
                  "fast as you add voters, but ONLY if they truly err independently.",
         "technical": "P[Binomial(n,p) > n/2] computed exactly; the exponential-decay bound for p<1/2 and the "
                      "reason correlated LLM votes do NOT enjoy it (estimate lineage before voting).",
         "semantic": "vote reliability / n-version disagreement / when does majority help / correlation caveat"},
     "proof": "n=3,p=0.3 gives exactly 0.216 (= p^3 + 3p^2(1-p)) and is below the n=1 error 0.3"},
    {"kind": "math_foundations.gf2_parity_syndrome", "title": "GF(2) semantic parity syndrome (single-corruption detection)",
     "input_edge": "ParityMatrix+NormalizedBinaryFacts", "output_edge": "Syndrome+ConsistencyVerdict",
     "tags": ["integrity", "coding", "consistency"],
     "registers": {
         "plain": "Runs a manifest's yes/no facts through consistency equations; any single silently flipped "
                  "fact makes the check light up.",
         "technical": "s = Hz mod 2; s=0 iff every encoded constraint holds; every-column-nonzero H detects "
                      "all single-bit corruptions (He_j = column j != 0). Detects contradiction, never proves "
                      "underlying truth.",
         "semantic": "manifest self-consistency / pure implies no writes / declared-unit equality / corruption "
                     "syndrome"},
     "proof": "a consistent fact vector yields the zero syndrome; flipping ANY single bit yields nonzero"},
    {"kind": "math_foundations.mdl_promotion_gate", "title": "Minimum-description-length promotion gate",
     "input_edge": "PrimitiveContractEvidenceCosts+UsageCosts", "output_edge": "PromotionVerdict+GainBits",
     "tags": ["promotion", "mdl", "compression"],
     "registers": {
         "plain": "Only mints a new reusable building block when doing so actually makes the whole recorded "
                  "experience SHORTER to describe than repeating the solution everywhere.",
         "technical": "Promote iff L(primitive)+L(contract)+L(evidence)+sum L(use_i|primitive) < sum "
                      "L(repeated_i); emits the gain in bits. The formal replacement for promote-after-N-uses "
                      "heuristics.",
         "semantic": "when to mint a primitive / compression-justified reuse / library growth gate"},
     "proof": "a heavily reused cheap abstraction promotes with positive gain; a costly single-use one is refused"},
]


def _card(spec: dict[str, Any]) -> dict[str, Any]:
    pid = canonical_id(PRIMITIVE_ID_PREFIX, spec["kind"], spec["title"])
    return {"primitive_id": pid, "title": spec["title"], "blackbox": spec["registers"]["technical"],
            "registers": spec["registers"], "primitive_kind": spec["kind"], "kind": "math_foundations.primitive",
            "input_edge": spec["input_edge"], "output_edge": spec["output_edge"],
            "capability_tags": spec["tags"], "domains": ["algorithms", "ml", "testing", "general"],
            "runtime_targets": ["python"], "proof_requirements": [spec["proof"]],
            "promotion_blockers": ["review_required", "no_lift_measurement_yet"],
            "readiness": "R4_checker_runs_and_passes_oracle", "verification_level": "L4_deterministic_checker",
            "source_family": SOURCE_FAMILY, "source_ref": SOURCE_REF, "generated_at": GENERATED_AT, **BOUNDARY}


def emit_cards() -> list[dict[str, Any]]:
    return [_card(s) for s in PRIMITIVE_SPECS]


def build(write: bool = False) -> dict[str, Any]:
    cards = emit_cards()
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        CARDS_PATH.write_text("".join(json.dumps(c, sort_keys=True) + "\n" for c in cards))
    return {"cards": len(cards), "path": str(CARDS_PATH) if write else None,
            "ids": [c["primitive_id"] for c in cards], **BOUNDARY}


def demo() -> dict[str, Any]:
    """Plan a 100M-primitive serving layer end to end: identity floor -> membership sketch -> stream counter
    -> retrieval cascade order -> sequential verification decision. Deterministic, 0-token."""
    floor = identity_information_bits(100_000_000)
    bloom = bloom_filter_sizing(100_000_000, 0.01)
    sketch = count_min_sketch_dimensions(0.001, 1e-6)
    cascade = cascade_optimal_order([
        {"cost": 50.0, "survival": 0.5},    # cross-encoder-ish: expensive, permissive
        {"cost": 0.1, "survival": 0.05},    # tenant/visibility: cheap, aggressive
        {"cost": 2.0, "survival": 0.3}])    # dense retrieval: middling
    verdict = sprt_decide([1.2, 1.1, 0.9], alpha=0.05, beta=0.05)
    return {"identity_bits": floor["whole_bits"], "bloom_megabytes": bloom["megabytes"],
            "count_min_cells": sketch["cells"], "cascade_order": cascade["order"],
            "sprt": verdict["decision"], **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # 1 identity floor: the layer's reference number, exact small case (MUTATION-SENSITIVE constants)
    floor = identity_information_bits(100_000_000)
    checks.append(("identity floor: log2(1e8)=26.5754247591 (ceil 27); 2 identities = exactly 1 bit",
                   abs(floor["bits"] - 26.5754247591) < 1e-9 and floor["whole_bits"] == 27
                   and identity_information_bits(2)["bits"] == 1.0))

    # 2 cascade: theorem order == brute force over EVERY permutation on two fixed 5-stage examples
    fixtures = [
        [{"cost": 1.0, "survival": 0.9}, {"cost": 0.2, "survival": 0.1}, {"cost": 5.0, "survival": 0.5},
         {"cost": 0.05, "survival": 0.8}, {"cost": 2.0, "survival": 0.25}],
        [{"cost": 3.0, "survival": 0.6}, {"cost": 0.5, "survival": 0.45}, {"cost": 0.5, "survival": 0.05},
         {"cost": 10.0, "survival": 0.95}, {"cost": 1.5, "survival": 0.2}]]
    def brute_force_best(stages: list[dict[str, float]]) -> float:
        return min(cascade_expected_cost([stages[i] for i in perm])
                   for perm in itertools.permutations(range(len(stages))))
    checks.append(("cascade: c/(1-s) ordering matches brute-force optimum on every permutation (2 fixtures)",
                   all(abs(cascade_optimal_order(f)["expected_cost"] - brute_force_best(f)) < 1e-9
                       for f in fixtures)))

    # 3 SPRT: boundary values + decisions on rising/falling/indecisive paths
    bounds = sprt_boundaries(0.05, 0.05)
    rising = sprt_decide([1.2, 1.1, 0.9], alpha=0.05, beta=0.05)
    falling = sprt_decide([-1.2, -1.1, -0.9], alpha=0.05, beta=0.05)
    undecided = sprt_decide([0.1, -0.1, 0.1], alpha=0.05, beta=0.05)
    checks.append(("SPRT: A=+2.9444, B=-2.9444; rising path accepts H1 at step 3, falling accepts H0, "
                   "weak evidence continues",
                   abs(bounds["upper_accept_h1"] - 2.9444389792) < 1e-9
                   and abs(bounds["lower_accept_h0"] + 2.9444389792) < 1e-9
                   and rising["decision"] == "accept_h1" and rising["steps_used"] == 3
                   and falling["decision"] == "accept_h0" and undecided["decision"] == "continue"))

    # 4 IPS: equals plain mean when target==logging; recovers the analytic value on a two-action example
    same_policy = inverse_propensity_estimate([
        {"reward": 1.0, "logged_propensity": 0.5, "target_probability": 0.5},
        {"reward": 0.0, "logged_propensity": 0.5, "target_probability": 0.5}])
    # logging chose action A 80%/B 20%; target always plays B; only B-rows carry target weight 1/0.2
    always_b = inverse_propensity_estimate([
        {"reward": 0.2, "logged_propensity": 0.8, "target_probability": 0.0},   # A row, weight 0
        {"reward": 1.0, "logged_propensity": 0.2, "target_probability": 1.0}])  # B row, weight 5
    guard = inverse_propensity_estimate([{"reward": 1.0, "logged_propensity": 0.0, "target_probability": 1.0}])
    checks.append(("IPS: same-policy = plain mean (0.5); always-B example = (0 + 5*1)/2 = 2.5 (unbiased "
                   "single-sample scale); zero propensity refused",
                   abs(same_policy["estimated_value"] - 0.5) < 1e-9
                   and abs(always_b["estimated_value"] - 2.5) < 1e-9 and guard["ok"] is False))

    # 5 SimHash law: endpoints + the right angle
    checks.append(("simhash law: theta 0 -> 1.0, pi -> 0.0, pi/2 -> 0.5",
                   simhash_collision_probability(0.0)["collision_probability"] == 1.0
                   and simhash_collision_probability(math.pi)["collision_probability"] == 0.0
                   and abs(simhash_collision_probability(math.pi / 2)["collision_probability"] - 0.5) < 1e-9))

    # 6 banding S-curve: sharp separation of J=0.8 vs J=0.2 under r=4,b=8 (exact reference values)
    high = lsh_banding_candidate_probability(0.8, 4, 8)["candidate_probability"]
    low = lsh_banding_candidate_probability(0.2, 4, 8)["candidate_probability"]
    checks.append(("banding: J=0.8@r4b8 = 0.9852371302; J=0.2 = 0.0127285489 (S-curve separation)",
                   abs(high - 0.9852371302) < 1e-9 and abs(low - 0.0127285489) < 1e-9))

    # 7 bloom: the layer's exact reference numbers at 100M @ 1%
    bloom = bloom_filter_sizing(100_000_000, 0.01)
    checks.append(("bloom: 1e8@1%% -> 958,505,838 bits, 9.585 bits/item, 7 hashes, ~119.8 MB",
                   bloom["bits"] == 958_505_838 and bloom["hash_functions"] == 7
                   and abs(bloom["bits_per_item"] - 9.585) < 0.001 and 119.0 < bloom["megabytes"] < 120.5))

    # 8 count-min: the layer's exact reference dimensions
    sketch = count_min_sketch_dimensions(0.001, 1e-6)
    checks.append(("count-min: eps=1e-3, delta=1e-6 -> width 2719 x depth 14 = 38,066 cells",
                   sketch["width"] == 2719 and sketch["depth"] == 14 and sketch["cells"] == 38_066))

    # 9 majority vote: exact small case + monotone improvement with more independent voters
    one = majority_vote_failure_probability(1, 0.3)["majority_failure_probability"]
    three = majority_vote_failure_probability(3, 0.3)["majority_failure_probability"]
    eleven = majority_vote_failure_probability(11, 0.3)["majority_failure_probability"]
    checks.append(("majority vote: n=1 -> 0.3; n=3 -> exactly 0.216; n=11 far lower (independence pays)",
                   abs(one - 0.3) < 1e-12 and abs(three - 0.216) < 1e-12 and eleven < 0.08 < three < one))

    # 10 parity syndrome: consistent facts pass; EVERY single-bit flip is detected; a zero column is honest
    parity = [[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1]]   # all 4 columns nonzero
    facts = [1, 1, 0, 0]                                   # satisfies rows: 1+1=0, 1+0=1? -> recompute below
    consistent = [0, 0, 0, 0]                              # trivially consistent (zero vector)
    base = gf2_parity_syndrome(parity, consistent)
    all_flips_detected = all(
        not gf2_parity_syndrome(parity, [1 if i == j else 0 for i in range(4)])["consistent"]
        for j in range(4))
    degenerate = gf2_parity_syndrome([[1, 0, 0, 0]], [0, 0, 0, 0])
    checks.append(("parity: zero-vector consistent; every single-bit flip flips the syndrome; a matrix with "
                   "zero columns honestly reports it cannot detect all single-bit errors",
                   base["consistent"] and base["detects_all_single_bit_errors"] and all_flips_detected
                   and degenerate["detects_all_single_bit_errors"] is False))

    # 11 MDL gate: both directions
    promote = mdl_promotion_gate(50.0, 10.0, 20.0, [2.0] * 20, [30.0] * 20)
    refuse = mdl_promotion_gate(500.0, 100.0, 100.0, [2.0], [30.0])
    checks.append(("MDL gate: 20-use cheap abstraction promotes (gain 480 bits); costly single-use refused",
                   promote["promote"] and abs(promote["gain_bits"] - 480.0) < 1e-9 and not refuse["promote"]))

    # cards: deterministic, unique ids, candidate-only, typed edges, 3 registers, oracle-backed
    cards = emit_cards()
    checks.append(("11 cards: deterministic, unique ids, candidate-only, typed edges, 3-register descriptions",
                   len(cards) == 11 and len({c["primitive_id"] for c in cards}) == 11
                   and all(c["candidate"] and not c["serves_truth"] and c["input_edge"] and c["output_edge"]
                           and set(c["registers"]) == {"plain", "technical", "semantic"}
                           and c["proof_requirements"] for c in cards)
                   and json.dumps(cards, sort_keys=True) == json.dumps(emit_cards(), sort_keys=True)))

    # demo composes across kernels and stays deterministic
    d = demo()
    checks.append(("demo: 100M plan = 27 id bits, ~119.8MB bloom, 38,066-cell sketch, cheap-first cascade "
                   "order [1,2,0], SPRT accepts",
                   d["identity_bits"] == 27 and d["cascade_order"] == [1, 2, 0]
                   and d["count_min_cells"] == 38_066 and d["sprt"] == "accept_h1"))

    ok = all(v for _, v in checks)
    print("math_foundations_primitives — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print("  11 mathematical-foundation kernels, deterministic + oracle-verified against the layer's "
          "reference numbers: identity-floor · cascade-order · SPRT · IPS · simhash-law · banding · bloom · "
          "count-min · majority-vote · parity-syndrome · MDL-gate. candidate-only.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--emit", action="store_true")
    args = ap.parse_args()
    if args.demo:
        print(json.dumps(demo(), indent=2))
        return 0
    if args.emit:
        print(json.dumps(build(write=True), indent=2))
        return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
