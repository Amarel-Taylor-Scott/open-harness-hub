#!/usr/bin/env python3
"""associative_memory_primitives — fast-weight / associative-memory kernels as deterministic, oracle-verified
primitives, mined from the owner-forwarded BDH research verdict and its mathematical pass (seed
`owner-bdh-research-verdict-2026-07-11` in data/research-queue/seed_sources.jsonl).

Owner (2026-07-11): "Continue generating and populating more primitives." The forwarded verdict's HARD
THEOREMS about synaptic/linear memory become executable kernels whose oracles are the theorems themselves —
implemented from scratch, pure python, no randomness, every claim executed:

   1. hebbian_write / associative_read — the additive outer-product memory (attention-as-synapse baseline).
   2. associative_crosstalk          — retrieval interference: readout = v_j + sum_i v_i<k_i,k_j>; orthogonal
                                       keys recall exactly, overlapping keys pay a computable crosstalk bill.
   3. delta_rule_write               — the error-correcting write M += beta(v - Mk)k^T: exact overwrite at
                                       beta=1 on a unit key, and provably non-expansive for 0<=beta<=2.
   4. erase_then_write               — independently-addressed erase before write: the erased address reads
                                       back ~zero while untouched orthogonal associations survive exactly.
   5. decayed_write_norm_bound       — with decay, state norm is UNIFORMLY bounded by (1-l)^t*M0 + nR/l;
                                       without decay the additive memory has no comparable bound.
   6. positive_sparse_overlap_bias   — positive sparse keys have E<k_i,k_j> = s/D (a coherent bias), while
                                       centered keys average zero — the exact diagnosis of positivity crosstalk.
   7. contraction_forgetting_bound   — a rho-contractive recurrence forgets old distinctions like rho^k:
                                       stability and long memory are in mathematical tension.
   8. multi_timescale_decay_mixture  — a log-spaced bank of exponentials imitates power-law forgetting: the
                                       mixture's decay RATIO stays stable across horizons where any single
                                       exponential collapses.
   9. persistent_occupancy_fraction  — instantaneous sparsity is not persistent sparsity: rows touched at
                                       least once after T writes = 1-(1-p)^T (5% activity -> 99.4% at T=100).
  10. exact_recall_state_floor       — exact recall of n independent values from vocabulary V needs at least
                                       n*log2(V) state bits: "unlimited context" with fixed state cannot mean
                                       unlimited exact recall.
  11. linear_memory_rank_limit      — a d-dimensional linear key memory cannot store more than d independent
                                       associations exactly: with N=d+1 the least-squares residual is provably
                                       nonzero; at N<=d orthogonal keys store exactly.

Every card is candidate (candidate=true, serves_truth=false); a passing oracle is promotion EVIDENCE, not
promotion. Descriptions ship in THREE registers (plain / technical / semantic). The verdict's empirical claims
about any specific architecture remain UNVERIFIED here — only the mathematics that executes is evidence.

    python3 scripts/associative_memory_primitives.py --self-test
    python3 scripts/associative_memory_primitives.py --demo    # hebbian vs delta vs erase-then-write, measured
    python3 scripts/associative_memory_primitives.py --emit    # write the candidate card pack (+ stdout)
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
    raise SystemExit(f"associative_memory_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
GENERATED_AT = "2026-07-11T00:00:00+00:00"   # fixed build date — emitted cards byte-identical across runs
PRIMITIVE_ID_PREFIX = "prim:mem"
SOURCE_FAMILY = "associative_memory_bdh_verdict"
SOURCE_REF = {"name": "BDH research verdict + mathematical pass (owner-forwarded; architecture claims unverified in-repo)",
              "seed_source_id": "owner-bdh-research-verdict-2026-07-11"}
OUT_DIR = _SBC / "data" / "dev-intel" / "associative_memory_primitives"
CARDS_PATH = OUT_DIR / "associative_memory_candidate_cards.jsonl"


# ═══════════════ small pure linear algebra (lists only; no numpy — determinism law) ═══════════════════
def _outer(key: list[float], value: list[float]) -> list[list[float]]:
    return [[k * v for v in value] for k in key]


def _matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Readout y = M^T k for a key-rows-by-value-columns memory matrix."""
    return [sum(matrix[i][j] * vector[i] for i in range(len(vector))) for j in range(len(matrix[0]))]


def _mat_add(a: list[list[float]], b: list[list[float]], scale: float = 1.0) -> list[list[float]]:
    return [[a[i][j] + scale * b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _frobenius_norm(matrix: list[list[float]]) -> float:
    return math.sqrt(sum(x * x for row in matrix for x in row))


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _zeros(rows: int, cols: int) -> list[list[float]]:
    return [[0.0] * cols for _ in range(rows)]


# ═══════════════ 1. HEBBIAN ADDITIVE MEMORY ════════════════════════════════════════════════════════════
def hebbian_write(memory: list[list[float]], key: list[float], value: list[float]) -> dict[str, Any]:
    """Additive outer-product (Hebbian / linear-attention) write: M += k (outer) v. The baseline synaptic
    memory — accumulates every association forever; interference is whatever the key geometry allows."""
    updated = _mat_add(memory, _outer(key, value))
    return {"memory": updated, "memory_norm": round(_frobenius_norm(updated), 9)}


def associative_read(memory: list[list[float]], key: list[float]) -> dict[str, Any]:
    """Read the association at a key: y = M^T k (the linear-attention readout)."""
    readout = _matvec(memory, key)
    return {"readout": [round(x, 9) for x in readout]}


# ═══════════════ 2. CROSSTALK — the interference bill, computed exactly ════════════════════════════════
def associative_crosstalk(keys: list[list[float]], values: list[list[float]],
                          query_index: int) -> dict[str, Any]:
    """Store every (key, value) additively, then read back key[query_index]: the readout equals the true
    value PLUS sum_i value_i * <key_i, key_query> over the other pairs — interference is not noise, it is a
    computable bill determined by key geometry (zero for orthogonal keys)."""
    dimension_k, dimension_v = len(keys[0]), len(values[0])
    memory = _zeros(dimension_k, dimension_v)
    for key, value in zip(keys, values):
        memory = _mat_add(memory, _outer(key, value))
    readout = _matvec(memory, keys[query_index])
    true_value = values[query_index]
    scale = _dot(keys[query_index], keys[query_index])
    crosstalk = math.sqrt(sum((r - scale * t) ** 2 for r, t in zip(readout, true_value)))
    return {"readout": [round(x, 9) for x in readout], "self_scale": round(scale, 9),
            "crosstalk_norm": round(crosstalk, 9)}


# ═══════════════ 3. DELTA-RULE WRITE — error-correcting, non-expansive ═════════════════════════════════
def delta_rule_write(memory: list[list[float]], key: list[float], value: list[float], *,
                     beta: float = 1.0) -> dict[str, Any]:
    """DeltaNet-style write: M += beta * k (outer) (v - M^T k). One gradient step on ||M^T k - v||^2 —
    at beta=1 with a unit key the address is EXACTLY overwritten (M^T k == v afterward), and for
    0 <= beta <= 2 the update is non-expansive in the state (perturbations never grow)."""
    prediction = _matvec(memory, key)
    error = [v - p for v, p in zip(value, prediction)]
    updated = _mat_add(memory, _outer(key, error), scale=beta)
    after = _matvec(updated, key)
    return {"memory": updated, "readout_after": [round(x, 9) for x in after],
            "write_error_norm_before": round(math.sqrt(sum(e * e for e in error)), 9)}


# ═══════════════ 4. ERASE-THEN-WRITE — independently addressed deletion ════════════════════════════════
def erase_then_write(memory: list[list[float]], erase_key: list[float], write_key: list[float],
                     value: list[float], *, beta: float = 1.0) -> dict[str, Any]:
    """Erase one address (a delta write toward zero at erase_key), then write a new association elsewhere.
    Decouples where the memory FORGETS from where it LEARNS — the erased address reads back ~zero while
    orthogonal associations survive untouched."""
    zero_value = [0.0] * len(value)
    erased = delta_rule_write(memory, erase_key, zero_value, beta=beta)["memory"]
    written = delta_rule_write(erased, write_key, value, beta=beta)["memory"]
    return {"memory": written,
            "erased_readout": associative_read(written, erase_key)["readout"],
            "written_readout": associative_read(written, write_key)["readout"]}


# ═══════════════ 5. DECAY BOUNDS THE STATE — forgetting buys stability ═════════════════════════════════
def decayed_write_norm_bound(initial_norm: float, decay: float, update_norm_limit: float,
                             steps: int) -> dict[str, Any]:
    """With per-step decay l and bounded updates ||G|| <= R: ||M_t|| <= (1-l)^t ||M_0|| + R/l — a UNIFORM
    bound however long the stream runs. Verified against the exact worst-case recursion; decay=0 grows
    without bound (the additive memory's failure mode)."""
    if decay <= 0.0:
        worst = initial_norm + steps * update_norm_limit
        return {"bounded": False, "worst_case_norm": round(worst, 9),
                "note": "no decay -> norm grows linearly with the stream; no uniform bound exists"}
    bound = (1.0 - decay) ** steps * initial_norm + update_norm_limit / decay
    worst = initial_norm
    for _ in range(steps):
        worst = (1.0 - decay) * worst + update_norm_limit
    return {"bounded": True, "uniform_bound": round(bound, 9), "worst_case_norm": round(worst, 9),
            "bound_holds": worst <= bound + 1e-9}


# ═══════════════ 6. POSITIVE SPARSE KEYS HAVE A COHERENT OVERLAP BIAS ══════════════════════════════════
def positive_sparse_overlap_bias(dimension: int, active_count: int) -> dict[str, Any]:
    """For keys with `active_count` uniformly-placed positive coordinates (each 1/sqrt(s)), the EXPECTED
    overlap of two independent keys is s/D — a coherent, same-sign interference bias. Centered keys (mean
    subtracted) average zero instead. Computed by EXACT enumeration over all support pairs, so the law is
    executed, not asserted."""
    supports = list(itertools.combinations(range(dimension), active_count))
    total_overlap, total_centered, pairs = 0.0, 0.0, 0
    mean_coordinate = active_count / dimension / math.sqrt(active_count)
    for support_a in supports:
        key_a = [1.0 / math.sqrt(active_count) if i in support_a else 0.0 for i in range(dimension)]
        centered_a = [x - mean_coordinate for x in key_a]
        for support_b in supports:
            key_b = [1.0 / math.sqrt(active_count) if i in support_b else 0.0 for i in range(dimension)]
            centered_b = [x - mean_coordinate for x in key_b]
            total_overlap += _dot(key_a, key_b)
            total_centered += _dot(centered_a, centered_b)
            pairs += 1
    return {"expected_overlap": round(total_overlap / pairs, 9),
            "theory_s_over_d": round(active_count / dimension, 9),
            "expected_centered_overlap": round(total_centered / pairs, 9)}


# ═══════════════ 7. CONTRACTION FORGETS — stability vs memory ══════════════════════════════════════════
def contraction_forgetting_bound(contraction_factor: float, steps: int,
                                 initial_gap: float) -> dict[str, Any]:
    """A rho-contractive recurrence shrinks any old distinction by rho^k after k shared steps: distant past
    vanishes exponentially. Verified on the exact linear recurrence; rho -> 1 keeps memory longer but the
    same math accumulates noise (variance sigma^2/(1-rho^2))."""
    bound = contraction_factor ** steps * initial_gap
    gap = initial_gap
    for _ in range(steps):
        gap = contraction_factor * gap
    noise_variance_amplification = 1.0 / (1.0 - contraction_factor ** 2) if contraction_factor < 1 else None
    relative_gap = abs(gap - bound) / max(abs(bound), 1e-300)
    return {"gap_after_steps": gap, "bound": bound,
            "bound_is_exact_for_linear": relative_gap < 1e-12,
            "stationary_noise_amplification": (round(noise_variance_amplification, 6)
                                               if noise_variance_amplification is not None else None)}


# ═══════════════ 8. MULTI-TIMESCALE MIXTURE — power-law forgetting from exponentials ═══════════════════
def multi_timescale_decay_mixture(decay_rates: list[float], weights: list[float],
                                  horizons: list[int]) -> dict[str, Any]:
    """K(t) = sum_j w_j (1-l_j)^t: a log-spaced bank of exponential traces imitates power-law retention.
    Diagnostic: the retention RATIO K(4t)/K(t) stays comparatively stable across horizons for the mixture
    (power-law behavior) while any single exponential's ratio collapses toward zero."""
    total_weight = sum(weights)
    normalized = [w / total_weight for w in weights]

    def kernel(t: int) -> float:
        return sum(w * (1.0 - rate) ** t for w, rate in zip(normalized, decay_rates))

    retention = {str(t): round(kernel(t), 9) for t in horizons}
    # scale stability lives in LOG space: a power law K(t)=t^-a has CONSTANT log K(4t)/K(t) = -a*log 4,
    # while a single exponential's log-ratio is -3t*l and diverges linearly with the horizon.
    log_ratios = [math.log(kernel(4 * t) / kernel(t)) for t in horizons if kernel(t) > 0]
    fastest = max(decay_rates)
    single_log_ratios = [3 * t * math.log(1.0 - fastest) for t in horizons]
    spread = (max(log_ratios) - min(log_ratios)) if log_ratios else float("inf")
    single_spread = (max(single_log_ratios) - min(single_log_ratios)) if single_log_ratios else 0.0
    return {"retention": retention, "log_ratio_spread_mixture": round(spread, 6),
            "log_ratio_spread_single_fastest": round(single_spread, 6),
            "mixture_more_scale_stable": spread < single_spread}


# ═══════════════ 9. PERSISTENT OCCUPANCY — instantaneous sparsity is not persistent sparsity ═══════════
def persistent_occupancy_fraction(activation_probability: float, steps: int) -> dict[str, Any]:
    """Fraction of memory rows touched at least once after T independent writes with per-step activity p:
    1 - (1-p)^T. At p=0.05 and T=100 that is ~99.4% — 5% instantaneous sparsity still populates nearly the
    whole persistent state unless supports are stable or rows are physically skipped/erased."""
    fraction = 1.0 - (1.0 - activation_probability) ** steps
    return {"activation_probability": activation_probability, "steps": steps,
            "occupied_fraction": round(fraction, 9)}


# ═══════════════ 10. EXACT-RECALL STATE FLOOR ══════════════════════════════════════════════════════════
def exact_recall_state_floor(items: int, vocabulary_size: int) -> dict[str, Any]:
    """Exactly recalling any of n independent values drawn from a vocabulary of V requires at least
    n*log2(V) bits of state — whatever the architecture calls that state. Fixed finite state therefore
    cannot deliver unlimited exact recall; something must grow, forget, or fall back to external memory."""
    bits = items * math.log2(vocabulary_size)
    return {"items": items, "vocabulary_size": vocabulary_size,
            "state_floor_bits": round(bits, 6), "state_floor_bytes": math.ceil(bits / 8)}


# ═══════════════ 11. RANK LIMIT — d dimensions store at most d exact associations ═════════════════════
def _least_squares_residual(keys: list[list[float]], values: list[list[float]]) -> float:
    """Best linear memory M (per value column, via normal equations) and the residual max_i ||M^T k_i - v_i||.
    Small pure-python solve with partial pivoting; keys as rows of K (n x d)."""
    n, d = len(keys), len(keys[0])
    dimension_v = len(values[0])
    gram = [[sum(keys[a][i] * keys[a][j] for a in range(n)) + (1e-12 if i == j else 0.0)
             for j in range(d)] for i in range(d)]
    memory = _zeros(d, dimension_v)
    for column in range(dimension_v):
        rhs = [sum(keys[a][i] * values[a][column] for a in range(n)) for i in range(d)]
        solution = _solve(gram, rhs)
        for i in range(d):
            memory[i][column] = solution[i]
    worst = 0.0
    for a in range(n):
        prediction = _matvec(memory, keys[a])
        worst = max(worst, math.sqrt(sum((p - v) ** 2 for p, v in zip(prediction, values[a]))))
    return worst


def _solve(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    n = len(rhs)
    a = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        a[col], a[pivot] = a[pivot], a[col]
        for row in range(col + 1, n):
            factor = a[row][col] / a[col][col]
            for k in range(col, n + 1):
                a[row][k] -= factor * a[col][k]
    out = [0.0] * n
    for row in range(n - 1, -1, -1):
        out[row] = (a[row][n] - sum(a[row][k] * out[k] for k in range(row + 1, n))) / a[row][row]
    return out


def linear_memory_rank_limit(dimension: int) -> dict[str, Any]:
    """Executable form of the rank boundary: d orthogonal keys store d arbitrary associations EXACTLY
    (residual ~0), but d+1 keys in d dimensions admit value assignments NO linear memory can store (the
    best least-squares memory keeps a strictly positive residual). Delta rules improve overwriting; they
    do not remove this limit."""
    orthogonal = [[1.0 if i == j else 0.0 for j in range(dimension)] for i in range(dimension)]
    values_ok = [[float(i + 1), float(-(i + 1))] for i in range(dimension)]
    residual_within = _least_squares_residual(orthogonal, values_ok)
    over = orthogonal + [[1.0 / math.sqrt(dimension)] * dimension]
    values_over = values_ok + [[100.0, 100.0]]   # deliberately violates the null-space constraint
    residual_over = _least_squares_residual(over, values_over)
    return {"dimension": dimension, "residual_at_capacity": round(residual_within, 9),
            "residual_over_capacity": round(residual_over, 9),
            "exact_within_capacity": residual_within < 1e-6,
            "impossible_over_capacity": residual_over > 1e-3}


# ═══════════════ primitive cards (3-register descriptions + typed edges) ═══════════════════════════════
PRIMITIVE_SPECS: list[dict[str, Any]] = [
    {"kind": "associative_memory.hebbian_write", "title": "Hebbian additive associative write + read",
     "input_edge": "MemoryMatrix+KeyVector+ValueVector", "output_edge": "UpdatedMemory+Readout",
     "tags": ["memory", "fast-weights", "attention"],
     "registers": {
         "plain": "Stores a pair of things together by strengthening their connection, and recalls one from "
                  "the other — the simplest kind of machine memory, which never forgets and never overwrites.",
         "technical": "Additive outer-product memory M += k(outer)v with linear readout y = M^T k — the "
                      "linear-attention/fast-weight baseline; capacity and interference are set entirely by "
                      "key geometry.",
         "semantic": "synaptic memory / linear attention state / key-value accumulation / fire-together"},
     "proof": "storing one pair on a unit key reads back exactly; the memory norm grows with every write"},
    {"kind": "associative_memory.associative_crosstalk", "title": "Associative interference (crosstalk) computed exactly",
     "input_edge": "KeySet+ValueSet+QueryIndex", "output_edge": "Readout+CrosstalkNorm",
     "tags": ["memory", "interference", "diagnostic"],
     "registers": {
         "plain": "Measures exactly how much stored memories bleed into each other when their keys are "
                  "similar — recall is perfect only when the keys don't overlap.",
         "technical": "Readout at k_j equals scale*v_j + sum_{i!=j} v_i <k_i,k_j>: interference is a computable "
                      "bill from key inner products, zero for orthogonal keys — not random noise.",
         "semantic": "memory bleed / retrieval interference / key collision cost / capacity diagnostic"},
     "proof": "orthogonal keys give zero crosstalk; overlapping keys give exactly the predicted nonzero bill"},
    {"kind": "associative_memory.delta_rule_write", "title": "Delta-rule error-correcting memory write",
     "input_edge": "MemoryMatrix+KeyVector+TargetValue+StepSize", "output_edge": "UpdatedMemory+ReadoutAfter",
     "tags": ["memory", "delta-rule", "overwrite"],
     "registers": {
         "plain": "Updates a memory by first checking what it currently recalls and only writing the "
                  "difference — so the same slot can be corrected or overwritten instead of piling up.",
         "technical": "M += beta*k(outer)(v - M^T k): one gradient step on ||M^T k - v||^2; exact overwrite at "
                      "beta=1 on a unit key; the state map is non-expansive for 0<=beta<=2 (perturbations "
                      "never amplify).",
         "semantic": "DeltaNet write / targeted overwrite / online least squares / interference-reducing update"},
     "proof": "beta=1 on a unit key reads back the new value exactly; a perturbation's norm does not grow"},
    {"kind": "associative_memory.erase_then_write", "title": "Independently addressed erase-then-write",
     "input_edge": "MemoryMatrix+EraseKey+WriteKey+ValueVector", "output_edge": "UpdatedMemory+EraseReceipt",
     "tags": ["memory", "forgetting", "addressing"],
     "registers": {
         "plain": "Deletes what one address remembers before storing something new at another — forgetting "
                  "and learning become separate, controllable acts.",
         "technical": "A delta write toward zero at erase_key, then a delta write of v at write_key: the erased "
                      "address reads ~0, orthogonal associations are untouched — the erase/write decoupling of "
                      "the newest linear-memory architectures.",
         "semantic": "targeted forgetting / stale-entry deletion / erase gate / memory hygiene"},
     "proof": "after erase the erased key reads ~zero while an orthogonal stored pair still reads exactly"},
    {"kind": "associative_memory.decayed_write_norm_bound", "title": "Decay-bounded memory norm (forgetting buys stability)",
     "input_edge": "InitialNorm+DecayRate+UpdateLimit+Steps", "output_edge": "UniformBound+WorstCaseNorm",
     "tags": ["memory", "stability", "bounds"],
     "registers": {
         "plain": "Shows that a memory which fades a little each step can run forever without blowing up, "
                  "and computes exactly how large it can ever get; without fading there is no such ceiling.",
         "technical": "||M_t|| <= (1-l)^t ||M_0|| + R/l for decay l and bounded updates R, verified against the "
                      "exact worst-case recursion; decay=0 grows linearly with the stream (no uniform bound).",
         "semantic": "bounded state / leak rate / stability-plasticity ceiling / unbounded-growth diagnosis"},
     "proof": "the simulated worst case never exceeds the closed-form bound; zero decay is flagged unbounded"},
    {"kind": "associative_memory.positive_sparse_overlap_bias", "title": "Positive sparse-key overlap bias (s over D)",
     "input_edge": "Dimension+ActiveCount", "output_edge": "ExpectedOverlap+CenteredComparison",
     "tags": ["memory", "sparsity", "coding"],
     "registers": {
         "plain": "Proves by exhaustive counting that memories using only positive sparse patterns always "
                  "lean on each other by a predictable amount — and that centering the patterns removes the "
                  "lean.",
         "technical": "Exact enumeration over all support pairs: E<k_i,k_j> = s/D for positive sparse keys "
                      "(coherent same-sign crosstalk), ~0 for centered keys — positivity plus sparsity is not "
                      "automatically a good associative code.",
         "semantic": "positive key bias / crosstalk expectation / centering fix / sparse coding diagnostic"},
     "proof": "enumerated expected overlap equals s/D exactly; the centered variant averages zero"},
    {"kind": "associative_memory.contraction_forgetting_bound", "title": "Contraction forgetting bound (rho^k)",
     "input_edge": "ContractionFactor+Steps+InitialGap", "output_edge": "GapBound+NoiseAmplification",
     "tags": ["memory", "dynamics", "forgetting"],
     "registers": {
         "plain": "Shows that any stable recurring process must gradually forget old differences — and that "
                  "trying to remember longer makes it accumulate more noise instead.",
         "technical": "A rho-contractive state map shrinks old state differences by rho^k (exact for linear "
                      "maps); stationary noise variance amplifies as 1/(1-rho^2) as rho->1 — the memory/"
                      "stability trade made numeric.",
         "semantic": "vanishing gradients cousin / stability vs memory / exponential forgetting / leaky state"},
     "proof": "the simulated gap equals rho^k times the initial gap to machine precision"},
    {"kind": "associative_memory.multi_timescale_decay_mixture", "title": "Multi-timescale decay mixture (power-law retention)",
     "input_edge": "DecayRateBank+Weights+Horizons", "output_edge": "RetentionCurve+ScaleStability",
     "tags": ["memory", "timescales", "consolidation"],
     "registers": {
         "plain": "Combines several memories that fade at different speeds so the whole remembers the way "
                  "people do — a lot at first, then a slowly thinning long tail.",
         "technical": "K(t)=sum w_j (1-l_j)^t over a log-spaced decay bank; the LOG retention ratio "
                      "log[K(4t)/K(t)] stays comparatively stable across horizons (constant for a true power "
                      "law) while a single exponential's diverges linearly — working/episodic/semantic tiers "
                      "from one mechanism.",
         "semantic": "power-law forgetting / memory tiers / spaced decay bank / consolidation timescales"},
     "proof": "the mixture's retention-ratio spread across horizons is strictly smaller than a single exponential's"},
    {"kind": "associative_memory.persistent_occupancy_fraction", "title": "Persistent occupancy of sparse writes",
     "input_edge": "ActivationProbability+Steps", "output_edge": "OccupiedFraction",
     "tags": ["memory", "sparsity", "capacity"],
     "registers": {
         "plain": "Shows that touching only a few memory slots at a time still fills nearly all of them over "
                  "time — momentary sparsity is not long-run sparsity.",
         "technical": "Rows touched at least once after T independent writes with per-step probability p: "
                      "1-(1-p)^T; at p=0.05, T=100 the persistent state is ~99.4% populated.",
         "semantic": "sparse writes dense state / occupancy law / physical sparsity planning"},
     "proof": "p=0.05, T=100 gives 0.994079471 exactly; one step gives exactly p"},
    {"kind": "associative_memory.exact_recall_state_floor", "title": "Exact-recall state floor (n log2 V bits)",
     "input_edge": "ItemCount+VocabularySize", "output_edge": "StateFloorBits",
     "tags": ["memory", "information-theory", "context"],
     "registers": {
         "plain": "Computes the minimum amount of memory any system needs to recall n independent things "
                  "perfectly — no architecture escapes it, so 'unlimited context' with fixed memory cannot "
                  "mean unlimited perfect recall.",
         "technical": "B >= n*log2(V) bits for exact recall of n independent values from vocabulary V "
                      "(Fano/communication-complexity floor); fixed state must grow, forget, approximate, or "
                      "escape to external memory.",
         "semantic": "recall lower bound / context-length reality check / state budget / recall-throughput trade"},
     "proof": "1000 items over a 1024-word vocabulary need exactly 10,000 bits (1,250 bytes)"},
    {"kind": "associative_memory.linear_memory_rank_limit", "title": "Linear memory rank limit (d associations in d dimensions)",
     "input_edge": "KeyDimension", "output_edge": "CapacityVerdict+Residuals",
     "tags": ["memory", "capacity", "linear-algebra"],
     "registers": {
         "plain": "Demonstrates, by actually trying, that a memory built on d-dimensional keys can store d "
                  "arbitrary facts perfectly but never d+1 — a hard ceiling no clever update rule removes.",
         "technical": "d orthogonal keys store arbitrary values with ~0 least-squares residual; d+1 keys admit "
                      "value assignments violating the null-space constraint Vc=0, leaving a provably positive "
                      "residual for EVERY linear memory — delta rules fix overwriting, not rank.",
         "semantic": "capacity ceiling / rank boundary / why exact attention persists / fast-weight limit"},
     "proof": "residual ~0 at capacity; residual > 1e-3 one association over capacity"},
]


def _card(spec: dict[str, Any]) -> dict[str, Any]:
    pid = canonical_id(PRIMITIVE_ID_PREFIX, spec["kind"], spec["title"])
    return {"primitive_id": pid, "title": spec["title"], "blackbox": spec["registers"]["technical"],
            "registers": spec["registers"], "primitive_kind": spec["kind"],
            "kind": "associative_memory.primitive",
            "input_edge": spec["input_edge"], "output_edge": spec["output_edge"],
            "capability_tags": spec["tags"], "domains": ["ml", "algorithms", "memory", "general"],
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
    """Hebbian vs delta vs erase-then-write on the SAME colliding-key workload, interference measured."""
    key_a = [1.0, 0.0, 0.0]
    key_b = [0.8, 0.6, 0.0]     # deliberately overlaps key_a
    value_a, value_b = [5.0, 0.0], [0.0, 7.0]
    hebbian = hebbian_write(hebbian_write(_zeros(3, 2), key_a, value_a)["memory"], key_b, value_b)["memory"]
    hebbian_recall_a = associative_read(hebbian, key_a)["readout"]
    delta = delta_rule_write(delta_rule_write(_zeros(3, 2), key_a, value_a)["memory"], key_b, value_b)["memory"]
    delta_recall_b = associative_read(delta, key_b)["readout"]
    cleaned = erase_then_write(delta, key_a, [0.0, 0.0, 1.0], [9.0, 9.0])
    return {"hebbian_recall_a_interfered": hebbian_recall_a,
            "delta_recall_b_exact": [round(x, 6) for x in delta_recall_b],
            "erased_a_reads": [round(x, 6) for x in cleaned["erased_readout"]],
            "new_slot_reads": [round(x, 6) for x in cleaned["written_readout"]], **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # 1 hebbian: unit-key store reads back exactly; norm grows monotonically (never forgets)
    m1 = hebbian_write(_zeros(2, 2), [1.0, 0.0], [3.0, 4.0])
    read1 = associative_read(m1["memory"], [1.0, 0.0])["readout"]
    m2 = hebbian_write(m1["memory"], [0.0, 1.0], [1.0, 1.0])
    checks.append(("hebbian: unit-key pair reads back exactly; norm grows with every write",
                   read1 == [3.0, 4.0] and m2["memory_norm"] > m1["memory_norm"]))

    # 2 crosstalk: orthogonal keys -> zero bill; overlapping keys -> exactly the predicted bill
    orth = associative_crosstalk([[1.0, 0.0], [0.0, 1.0]], [[5.0], [7.0]], 0)
    keys = [[1.0, 0.0], [0.8, 0.6]]
    overlap = associative_crosstalk(keys, [[5.0], [7.0]], 0)
    predicted = abs(7.0 * _dot(keys[0], keys[1]))   # v_b * <k_a,k_b>
    checks.append(("crosstalk: zero for orthogonal keys; equals the predicted v*<k_i,k_j> bill for overlap",
                   orth["crosstalk_norm"] == 0.0 and abs(overlap["crosstalk_norm"] - predicted) < 1e-9))

    # 3 delta rule: exact overwrite at beta=1; non-expansive perturbation (MUTATION-SENSITIVE)
    stale = hebbian_write(_zeros(2, 2), [1.0, 0.0], [9.0, 9.0])["memory"]
    fixed = delta_rule_write(stale, [1.0, 0.0], [1.0, 2.0], beta=1.0)
    perturbation = [[0.3, -0.2], [0.1, 0.4]]
    base = delta_rule_write(_zeros(2, 2), [1.0, 0.0], [1.0, 2.0])["memory"]
    shifted = delta_rule_write(perturbation, [1.0, 0.0], [1.0, 2.0])["memory"]
    gap_after = _frobenius_norm(_mat_add(shifted, base, scale=-1.0))
    checks.append(("delta rule: beta=1 exactly overwrites a stale slot; perturbations never amplify",
                   fixed["readout_after"] == [1.0, 2.0]
                   and gap_after <= _frobenius_norm(perturbation) + 1e-12))

    # 4 erase-then-write: erased address ~0; an orthogonal stored pair survives exactly
    memory = delta_rule_write(_zeros(3, 2), [1.0, 0.0, 0.0], [5.0, 5.0])["memory"]
    memory = delta_rule_write(memory, [0.0, 1.0, 0.0], [2.0, 3.0])["memory"]
    result = erase_then_write(memory, [1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [8.0, 8.0])
    survivor = associative_read(result["memory"], [0.0, 1.0, 0.0])["readout"]
    checks.append(("erase-then-write: erased key reads ~0; orthogonal association survives; new slot exact",
                   max(abs(x) for x in result["erased_readout"]) < 1e-9
                   and survivor == [2.0, 3.0] and result["written_readout"] == [8.0, 8.0]))

    # 5 decay bound: simulation never exceeds the closed form; zero decay flagged unbounded
    bounded = decayed_write_norm_bound(10.0, 0.02, 1.0, 500)
    unbounded = decayed_write_norm_bound(10.0, 0.0, 1.0, 500)
    checks.append(("decay bound: worst case <= closed-form uniform bound; zero decay honestly unbounded",
                   bounded["bounded"] and bounded["bound_holds"]
                   and not unbounded["bounded"] and unbounded["worst_case_norm"] == 510.0))

    # 6 overlap bias: exact enumeration equals s/D; centering kills the bias (D=6, s=2 -> 1/3)
    bias = positive_sparse_overlap_bias(6, 2)
    checks.append(("overlap bias: enumerated expectation == s/D exactly (1/3); centered version ~0",
                   abs(bias["expected_overlap"] - bias["theory_s_over_d"]) < 1e-9
                   and abs(bias["theory_s_over_d"] - 2.0 / 6.0) < 1e-9
                   and abs(bias["expected_centered_overlap"]) < 1e-9))

    # 7 contraction: gap == rho^k exactly for the linear map; noise amplification reported
    contraction = contraction_forgetting_bound(0.9, 50, 1.0)
    checks.append(("contraction: 0.9^50 gap to machine precision; stationary noise amplification computed",
                   contraction["bound_is_exact_for_linear"]
                   and abs(contraction["gap_after_steps"] - 0.9 ** 50) < 1e-15
                   and contraction["stationary_noise_amplification"] is not None))

    # 8 timescale mixture: mixture's retention-ratio spread beats the fastest single exponential
    mixture = multi_timescale_decay_mixture([0.5, 0.1, 0.02, 0.004], [1.0, 1.0, 1.0, 1.0],
                                            [1, 5, 25, 125])
    checks.append(("timescale mixture: retention-ratio spread strictly smaller than a single exponential",
                   mixture["mixture_more_scale_stable"]))

    # 9 occupancy: the verdict's reference number (5% activity, 100 steps -> 99.4%)
    occupancy = persistent_occupancy_fraction(0.05, 100)
    one_step = persistent_occupancy_fraction(0.3, 1)
    checks.append(("occupancy: p=0.05,T=100 -> 0.994079471; one step -> exactly p",
                   abs(occupancy["occupied_fraction"] - 0.994079471) < 1e-9
                   and abs(one_step["occupied_fraction"] - 0.3) < 1e-12))

    # 10 state floor: 1000 items x 1024 vocab = exactly 10,000 bits
    floor = exact_recall_state_floor(1000, 1024)
    checks.append(("state floor: 1000 items over 1024 vocabulary = exactly 10,000 bits (1,250 bytes)",
                   floor["state_floor_bits"] == 10000.0 and floor["state_floor_bytes"] == 1250))

    # 11 rank limit: exact at capacity, provably impossible one over (MUTATION-SENSITIVE both ways)
    rank = linear_memory_rank_limit(4)
    checks.append(("rank limit: d orthogonal keys store exactly; d+1 keys leave a positive residual",
                   rank["exact_within_capacity"] and rank["impossible_over_capacity"]))

    # cards: deterministic, unique ids, candidate-only, typed edges, 3 registers, oracle-backed
    cards = emit_cards()
    checks.append(("11 cards: deterministic, unique ids, candidate-only, typed edges, 3-register descriptions",
                   len(cards) == 11 and len({c["primitive_id"] for c in cards}) == 11
                   and all(c["candidate"] and not c["serves_truth"] and c["input_edge"] and c["output_edge"]
                           and set(c["registers"]) == {"plain", "technical", "semantic"}
                           and c["proof_requirements"] for c in cards)
                   and json.dumps(cards, sort_keys=True) == json.dumps(emit_cards(), sort_keys=True)))

    # demo: delta beats hebbian on the colliding workload; erase works end to end
    d = demo()
    checks.append(("demo: hebbian recall interfered, delta recall exact, erase leaves ~0, new slot exact",
                   d["hebbian_recall_a_interfered"] != [5.0, 0.0]
                   and d["delta_recall_b_exact"] == [0.0, 7.0]
                   and max(abs(x) for x in d["erased_a_reads"]) < 1e-6
                   and d["new_slot_reads"] == [9.0, 9.0]))

    ok = all(v for _, v in checks)
    print("associative_memory_primitives — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print("  11 associative-memory kernels, deterministic + oracle-verified from the forwarded verdict's "
          "theorems: hebbian · crosstalk · delta-rule · erase-then-write · decay-bound · overlap-bias · "
          "contraction · timescale-mixture · occupancy · state-floor · rank-limit. candidate-only.")
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
