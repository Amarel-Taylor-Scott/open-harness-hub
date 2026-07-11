#!/usr/bin/env python3
"""physics_tracking_primitives — physics-informed TRACKING/ESTIMATION kernels as deterministic, oracle-verified
primitives, mined from the ROGII wellbore-geosteering decomposition (owner-provided Kaggle notebook, seed source
`kaggle-rogii-wellbore-pf-gbm-notebook` in data/research-queue/seed_sources.jsonl).

Owner (2026-07-11): "Continue improving all aspects, building out more primitives, describing primitives,
testing." The notebook's winning shape — *track like a physicist, learn the residual, calibrate per group,
guard every shortcut* — decomposes into classic, general kernels far older and broader than geosteering.
Implemented HERE from scratch (standard algorithms, not copied notebook code): pure python, no numpy, no wall
clock, seeded LCG randomness only, every kernel behind an executed mutation-sensitive oracle:

   1. particle_filter_track     — sequential Monte-Carlo state tracker: propagate a particle swarm (momentum +
                                  process noise), reweight by observation likelihood against a reference curve,
                                  systematic-resample on ESS collapse. THE "track like a physicist" kernel.
   2. systematic_resample       — low-variance resampling: one uniform draw, N evenly-spaced pointers.
   3. effective_sample_size     — 1/Σw²: the particle-degeneracy diagnostic that triggers resampling.
   4. beam_search_grid_path     — bounded-width Viterbi-style decoding over a discrete grid with per-step move
                                  costs + emission costs and backpointer path recovery.
   5. ncc_best_offset           — normalized cross-correlation template match (scale/offset-invariant).
   6. robust_irls_polyfit       — IRLS-reweighted polynomial fit (Cauchy weights on MAD-scaled residuals):
                                  trend fitting that outliers cannot drag.
   7. likelihood_weighted_ensemble — softmax(log-likelihood/scale) weighting of per-seed predictions: trust
                                  runs by how well they explained the observations.
   8. inverse_distance_weighted_impute — IDW spatial interpolation from scattered neighbor observations.
   9. exponential_warmup_blend  — ramp a learned correction in with 1−exp(−d/τ) so it is silent at the anchor
                                  and full-strength far from it.
  10. backtest_gated_override   — "guard every shortcut": adopt a candidate only when it backtests below an
                                  RMSE gate on the visible reference section; otherwise keep the base.
  11. confidence_gated_blend    — per-group calibration: move toward a candidate only when measured gain and
                                  consistency clear thresholds, with a hard clip on the move.
  12. prediction_integrity_audit — id-alignment + finiteness + row-count audit with a canonical SHA-256, so a
                                  quietly wrong artifact cannot win.

Every card is candidate (candidate=true, serves_truth=false); a passing oracle is promotion EVIDENCE, not
promotion. Descriptions ship in THREE registers (plain / technical / semantic) per the enrichment scheme.

    python3 scripts/physics_tracking_primitives.py --self-test
    python3 scripts/physics_tracking_primitives.py --demo    # track a drifting well against a reference curve
    python3 scripts/physics_tracking_primitives.py --emit    # write the candidate card pack (+ stdout)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterator, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
try:
    from src.teleon.experiments.ids import canonical_id
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"physics_tracking_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
#: fixed build date so emitted cards are byte-identical across runs (no live clock — determinism law).
GENERATED_AT = "2026-07-11T00:00:00+00:00"
PRIMITIVE_ID_PREFIX = "prim:trk"
SOURCE_FAMILY = "physics_tracking_rogii_decomposition"
SOURCE_REF = {"name": "ROGII Wellbore Geology Prediction (Kaggle) — PF+GBM geosteering decomposition",
              "url": "https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction",
              "seed_source_id": "kaggle-rogii-wellbore-pf-gbm-notebook"}
OUT_DIR = _SBC / "data" / "dev-intel" / "physics_tracking_primitives"
CARDS_PATH = OUT_DIR / "physics_tracking_candidate_cards.jsonl"


# ═══════════════ seeded randomness (pure, deterministic — the only randomness in this module) ══════════
def _lcg(seed: int) -> Iterator[float]:
    """Uniform(0,1) stream from a 31-bit LCG; deterministic for a given seed."""
    s = (seed & 0x7FFFFFFF) or 1
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s / 0x80000000


def _gauss(uniform_stream: Iterator[float]) -> float:
    """~N(0,1) via Irwin–Hall (sum of 12 uniforms − 6): pure, branch-free, deterministic."""
    return sum(next(uniform_stream) for _ in range(12)) - 6.0


def _interp(x: float, xs: list[float], ys: list[float]) -> float:
    """Piecewise-linear interpolation with edge clamping (xs ascending)."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    lo, hi = 0, len(xs) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if xs[mid] <= x:
            lo = mid
        else:
            hi = mid
    t = (x - xs[lo]) / (xs[hi] - xs[lo])
    return ys[lo] * (1.0 - t) + ys[hi] * t


def _rmse(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / max(1, len(a)))


# ═══════════════ 3. EFFECTIVE SAMPLE SIZE — the degeneracy diagnostic ══════════════════════════════════
def effective_sample_size(weights: list[float]) -> float:
    """ESS = 1/Σwᵢ² over normalized weights: N when uniform, 1 when one particle holds all the mass. The
    trigger for resampling in every particle filter."""
    total = sum(weights)
    if total <= 0:
        return 0.0
    return 1.0 / sum((w / total) ** 2 for w in weights)


# ═══════════════ 2. SYSTEMATIC RESAMPLING — low-variance particle survival ═════════════════════════════
def systematic_resample(weights: list[float], *, seed: int = 1) -> list[int]:
    """Low-variance systematic resampling: ONE uniform draw u₀, then N evenly-spaced pointers u₀+i/N walk the
    cumulative weights. Preserves the weight distribution with far less variance than N independent draws."""
    n = len(weights)
    total = sum(weights)
    norm = [w / total for w in weights] if total > 0 else [1.0 / n] * n
    cumulative = []
    running = 0.0
    for w in norm:
        running += w
        cumulative.append(running)
    u0 = next(_lcg(seed)) / n
    chosen, ci = [], 0
    for i in range(n):
        u = u0 + i / n
        while ci < n - 1 and cumulative[ci] < u:
            ci += 1
        chosen.append(ci)
    return chosen


# ═══════════════ 1. PARTICLE FILTER — track like a physicist ═══════════════════════════════════════════
def particle_filter_track(observations: list[float], reference_x: list[float], reference_y: list[float], *,
                          start_state: float, n_particles: int = 200, seed: int = 42,
                          momentum: float = 0.99, rate_noise: float = 0.01, position_noise: float = 0.02,
                          observation_sigma: float = 1.0, resample_fraction: float = 0.5) -> dict[str, Any]:
    """Sequential Monte-Carlo tracker for a 1-D hidden state observed through a reference curve. A swarm of
    (position, rate) particles propagates with momentum + process noise; each observation reweights particles by
    a Gaussian likelihood of (observation − reference(position)); when ESS collapses below resample_fraction·N,
    systematic resampling survives the fittest. Returns the weighted-mean path, the per-run log-likelihood (how
    well this run explained the data — feeds likelihood_weighted_ensemble), and the final ESS."""
    rng = _lcg(seed)
    positions = [start_state + 0.5 * _gauss(rng) for _ in range(n_particles)]
    rates = [0.01 * _gauss(rng) for _ in range(n_particles)]
    weights = [1.0 / n_particles] * n_particles
    path: list[float] = []
    log_likelihood = 0.0
    for obs in observations:
        for j in range(n_particles):
            rates[j] = momentum * rates[j] + rate_noise * _gauss(rng)
            positions[j] += rates[j] + position_noise * _gauss(rng)
        average_likelihood = 0.0
        for j in range(n_particles):
            expected = _interp(positions[j], reference_x, reference_y)
            d = (obs - expected) / observation_sigma
            likelihood = math.exp(-0.5 * min(d * d, 600.0))
            likelihood = max(likelihood, 1e-300)
            average_likelihood += weights[j] * likelihood
            weights[j] *= likelihood
        log_likelihood += math.log(max(average_likelihood, 1e-300))
        total = sum(weights)
        weights = [w / total for w in weights] if total > 0 else [1.0 / n_particles] * n_particles
        if effective_sample_size(weights) < resample_fraction * n_particles:
            chosen = systematic_resample(weights, seed=int(next(rng) * 0x7FFFFFFF))
            positions = [positions[c] + 0.05 * _gauss(rng) for c in chosen]
            rates = [rates[c] + 0.001 * _gauss(rng) for c in chosen]
            weights = [1.0 / n_particles] * n_particles
        path.append(sum(w * p for w, p in zip(weights, positions)))
    return {"path": [round(p, 6) for p in path], "log_likelihood": round(log_likelihood, 6),
            "final_effective_sample_size": round(effective_sample_size(weights), 3)}


# ═══════════════ 4. BEAM SEARCH — bounded-width path decoding over a grid ══════════════════════════════
def beam_search_grid_path(emissions: list[float], grid_values: list[float], start_index: int, *,
                          beam_size: int = 8, move_cost: float = 1.0, emission_scale: float = 1.0,
                          max_step: int = 2) -> dict[str, Any]:
    """Viterbi-style decoding with a bounded beam: at each step a state (grid index) may move ±max_step; the
    path cost adds move_cost·|Δ| plus (emission − grid_value)²/emission_scale. The best beam_size unique states
    survive each step; backpointers recover the single best path. Move cost is the stiffness knob: high = a
    conservative nearly-flat path, low = follow the emissions closely."""
    n, grid_length = len(emissions), len(grid_values)
    beam: dict[int, tuple[float, int]] = {start_index: (0.0, -1)}   # index -> (cost, backpointer beam slot)
    history: list[list[tuple[int, int]]] = []                        # per step: [(index, parent slot)]
    costs_prev = [0.0]
    slots_prev = [start_index]
    for step in range(n):
        candidates: dict[int, tuple[float, int]] = {}
        for slot, index in enumerate(slots_prev):
            base_cost = costs_prev[slot]
            for delta in range(-max_step, max_step + 1):
                nxt = index + delta
                if nxt < 0 or nxt >= grid_length:
                    continue
                cost = base_cost + move_cost * abs(delta) + \
                    (emissions[step] - grid_values[nxt]) ** 2 / emission_scale
                if nxt not in candidates or cost < candidates[nxt][0]:
                    candidates[nxt] = (cost, slot)
        kept = sorted(candidates.items(), key=lambda kv: (kv[1][0], kv[0]))[:beam_size]
        history.append([(index, parent) for index, (_c, parent) in kept])
        slots_prev = [index for index, _cp in kept]
        costs_prev = [cost for _i, (cost, _p) in kept]
    best_slot = min(range(len(costs_prev)), key=lambda s: costs_prev[s])
    path_indices = [0] * n
    slot = best_slot
    for step in range(n - 1, -1, -1):
        index, parent = history[step][slot]
        path_indices[step] = index
        slot = parent
    return {"path_indices": path_indices, "path_values": [grid_values[i] for i in path_indices],
            "best_cost": round(costs_prev[best_slot], 6)}


# ═══════════════ 5. NCC TEMPLATE MATCH — scale/offset-invariant alignment ══════════════════════════════
def ncc_best_offset(needle: list[float], haystack: list[float]) -> dict[str, Any]:
    """Normalized cross-correlation of a template against every window of a longer series. Because both sides
    are standardized per window, the match is invariant to affine gain/offset — the reason NCC aligns a gamma-ray
    log to a type well regardless of tool calibration. Returns the best offset and its score in [−1, 1]."""
    m, n = len(needle), len(haystack)
    mean_needle = sum(needle) / m
    centered_needle = [x - mean_needle for x in needle]
    needle_norm = math.sqrt(sum(x * x for x in centered_needle)) or 1e-12
    best_offset, best_score, scores = 0, -2.0, []
    for offset in range(n - m + 1):
        window = haystack[offset:offset + m]
        mean_window = sum(window) / m
        centered_window = [x - mean_window for x in window]
        window_norm = math.sqrt(sum(x * x for x in centered_window)) or 1e-12
        score = sum(a * b for a, b in zip(centered_needle, centered_window)) / (needle_norm * window_norm)
        scores.append(round(score, 6))
        if score > best_score:
            best_offset, best_score = offset, score
    return {"best_offset": best_offset, "best_score": round(best_score, 6), "scores": scores}


# ═══════════════ 6. ROBUST IRLS POLYFIT — trends outliers cannot drag ══════════════════════════════════
def _solve_linear_system(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting (small systems only)."""
    n = len(rhs)
    a = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        a[col], a[pivot] = a[pivot], a[col]
        if abs(a[col][col]) < 1e-12:
            a[col][col] = 1e-12
        for row in range(col + 1, n):
            factor = a[row][col] / a[col][col]
            for k in range(col, n + 1):
                a[row][k] -= factor * a[col][k]
    solution = [0.0] * n
    for row in range(n - 1, -1, -1):
        solution[row] = (a[row][n] - sum(a[row][k] * solution[k] for k in range(row + 1, n))) / a[row][row]
    return solution


def _weighted_polyfit(x: list[float], y: list[float], degree: int, weights: list[float]) -> list[float]:
    terms = degree + 1
    normal = [[sum(w * xi ** (i + j) for xi, w in zip(x, weights)) for j in range(terms)] for i in range(terms)]
    rhs = [sum(w * yi * xi ** i for xi, yi, w in zip(x, y, weights)) for i in range(terms)]
    return _solve_linear_system(normal, rhs)   # coefficients low→high degree


def _polyval(coefficients: list[float], x: float) -> float:
    return sum(c * x ** i for i, c in enumerate(coefficients))


def robust_irls_polyfit(x: list[float], y: list[float], *, degree: int = 2,
                        iterations: int = 4) -> dict[str, Any]:
    """Iteratively-reweighted least-squares polynomial fit: after an ordinary fit, residuals are scaled by
    1.4826·MAD and each point reweighted with the Cauchy weight 1/(1+(r/2s)²), then refit. Gross outliers lose
    their vote instead of dragging the trend — the denoiser that keeps a wrong-branch jump from bending the
    whole trajectory."""
    weights = [1.0] * len(x)
    coefficients = _weighted_polyfit(x, y, degree, weights)
    for _ in range(iterations):
        residuals = [yi - _polyval(coefficients, xi) for xi, yi in zip(x, y)]
        med = sorted(residuals)[len(residuals) // 2]
        mad = sorted(abs(r - med) for r in residuals)[len(residuals) // 2]
        scale = 1.4826 * mad + 1e-9
        weights = [1.0 / (1.0 + (r / (2.0 * scale)) ** 2) for r in residuals]
        coefficients = _weighted_polyfit(x, y, degree, weights)
    fitted = [round(_polyval(coefficients, xi), 6) for xi in x]
    return {"coefficients": [round(c, 6) for c in coefficients], "fitted": fitted,
            "final_weights": [round(w, 4) for w in weights]}


# ═══════════════ 7. LIKELIHOOD-WEIGHTED ENSEMBLE — trust runs that explained the data ══════════════════
def likelihood_weighted_ensemble(predictions: list[list[float]], log_likelihoods: list[float], *,
                                 scale: float = 5.0) -> dict[str, Any]:
    """Softmax over per-run log-likelihoods (divided by a temperature-like scale) weights each run's
    prediction: a run that explained the observations well dominates; scale→∞ recovers the plain mean. The
    principled alternative to averaging seeds blindly."""
    top = max(log_likelihoods)
    raw = [math.exp((ll - top) / scale) for ll in log_likelihoods]
    total = sum(raw)
    weights = [r / total for r in raw]
    length = len(predictions[0])
    combined = [round(sum(w * run[i] for w, run in zip(weights, predictions)), 6) for i in range(length)]
    return {"prediction": combined, "weights": [round(w, 6) for w in weights]}


# ═══════════════ 8. IDW SPATIAL IMPUTE — borrow from the neighbors ═════════════════════════════════════
def inverse_distance_weighted_impute(points: list[tuple[float, float, float]],
                                     queries: list[tuple[float, float]], *,
                                     k: int = 4, power: float = 2.0) -> dict[str, Any]:
    """Inverse-distance-weighted interpolation: each query takes the k nearest scattered observations,
    weighted by 1/distance^power (an exact hit returns that point's value). The offset-well imputer: estimate a
    surface where you have no measurement from the wells around you."""
    estimates, nearest_distances = [], []
    for qx, qy in queries:
        ranked = sorted(points, key=lambda p: (p[0] - qx) ** 2 + (p[1] - qy) ** 2)[:max(1, k)]
        exact = next((p for p in ranked if (p[0] - qx) ** 2 + (p[1] - qy) ** 2 == 0.0), None)
        if exact is not None:
            estimates.append(round(exact[2], 6))
            nearest_distances.append(0.0)
            continue
        inverse_weights = [1.0 / (math.sqrt((p[0] - qx) ** 2 + (p[1] - qy) ** 2) ** power) for p in ranked]
        total = sum(inverse_weights)
        estimates.append(round(sum(w * p[2] for w, p in zip(inverse_weights, ranked)) / total, 6))
        nearest_distances.append(round(math.sqrt((ranked[0][0] - qx) ** 2 + (ranked[0][1] - qy) ** 2), 6))
    return {"estimates": estimates, "nearest_distances": nearest_distances}


# ═══════════════ 9. WARM-UP RAMP — corrections earn trust with distance ════════════════════════════════
def exponential_warmup_blend(base: list[float], correction: list[float], distances: list[float], *,
                             tau: float = 120.0, alpha: float = 1.0) -> dict[str, Any]:
    """Blend a learned correction into a physical baseline with a 1−exp(−distance/τ) ramp: zero correction at
    the anchor (where the baseline is trusted), full correction far away (where drift dominates). The seam that
    lets a learned residual model coexist with a physics tracker without fighting it at the boundary."""
    ramps = [1.0 - math.exp(-max(d, 0.0) / tau) if tau > 1e-9 else 1.0 for d in distances]
    blended = [round(b + alpha * r * c, 6) for b, c, r in zip(base, correction, ramps)]
    return {"blended": blended, "ramps": [round(r, 6) for r in ramps]}


# ═══════════════ 10. BACKTEST-GATED OVERRIDE — guard every shortcut ════════════════════════════════════
def backtest_gated_override(base_prediction: list[float], candidate_prediction: list[float],
                            known_reference: list[float], candidate_at_known: list[float], *,
                            rmse_gate: float = 1.0) -> dict[str, Any]:
    """Adopt a tempting shortcut ONLY after it proves itself: the candidate must backtest below rmse_gate
    against the section where truth is visible; otherwise the base prediction is kept unchanged. Turns 'the
    lookup is probably aligned' into a measured decision — a quietly-misaligned shortcut cannot inject error."""
    backtest_rmse = _rmse(candidate_at_known, known_reference)
    adopted = math.isfinite(backtest_rmse) and backtest_rmse <= rmse_gate
    return {"prediction": list(candidate_prediction if adopted else base_prediction),
            "adopted_candidate": adopted, "backtest_rmse": round(backtest_rmse, 6), "rmse_gate": rmse_gate}


# ═══════════════ 11. CONFIDENCE-GATED BLEND — calibrate per group, move only on evidence ═══════════════
def confidence_gated_blend(base: list[float], candidate: list[float], *, gain: float,
                           consistency: float, minimum_gain: float = 0.5,
                           minimum_consistency: float = 0.5, maximum_alpha: float = 0.35,
                           move_clip: float = 10.0) -> dict[str, Any]:
    """Per-group calibration overlay: move from the base toward a candidate only when the measured improvement
    (gain) and its stability across backtest cuts (consistency) BOTH clear thresholds; the blend strength scales
    with gain and every per-point move is hard-clipped. Below threshold the base passes through untouched."""
    qualifies = gain >= minimum_gain and consistency >= minimum_consistency
    alpha = min(maximum_alpha, 0.1 + 0.2 * min(max(gain, 0.0), 5.0) / 5.0) if qualifies else 0.0
    moves = [max(-move_clip, min(move_clip, alpha * (c - b))) for b, c in zip(base, candidate)]
    return {"blended": [round(b + m, 6) for b, m in zip(base, moves)], "alpha": round(alpha, 4),
            "qualified": qualifies, "max_abs_move": round(max((abs(m) for m in moves), default=0.0), 6)}


# ═══════════════ 12. INTEGRITY AUDIT — a quietly wrong artifact cannot win ═════════════════════════════
def prediction_integrity_audit(ids: list[str], values: list[float],
                               expected_ids: list[str]) -> dict[str, Any]:
    """Read-only artifact audit before anything ships: id set + ORDER must match the expected manifest, every
    value must be finite, counts must agree; the canonical SHA-256 fingerprints the exact artifact for the
    receipt trail. Any violation flags ok=false — it never repairs silently."""
    problems = []
    if len(ids) != len(expected_ids):
        problems.append(f"row count {len(ids)} != expected {len(expected_ids)}")
    elif ids != expected_ids:
        problems.append("id order does not match the expected manifest")
    if len(values) != len(ids):
        problems.append(f"value count {len(values)} != id count {len(ids)}")
    if any(not math.isfinite(v) for v in values):
        problems.append("non-finite values present")
    canonical = json.dumps({"ids": ids, "values": [round(v, 9) if math.isfinite(v) else None for v in values]},
                           sort_keys=True).encode("utf-8")
    return {"ok": not problems, "problems": problems, "rows": len(ids),
            "sha256": hashlib.sha256(canonical).hexdigest()}


# ═══════════════ primitive cards (3-register descriptions + typed edges) ═══════════════════════════════
PRIMITIVE_SPECS: list[dict[str, Any]] = [
    {"kind": "tracking.particle_filter_track", "title": "Particle filter state tracker (momentum + likelihood + resample)",
     "input_edge": "ObservationSeries+ReferenceCurve+StartState", "output_edge": "TrackedStatePath+RunLogLikelihood",
     "tags": ["tracking", "state-estimation", "monte-carlo"],
     "registers": {
         "plain": "Follows a hidden quantity through noisy measurements by keeping many guesses alive at once, "
                  "trusting the guesses that match what was measured, and multiplying the survivors.",
         "technical": "Sequential Monte-Carlo (bootstrap particle filter) over a 1-D state with (position, rate) "
                      "particles: momentum+noise propagation, Gaussian observation likelihood against an "
                      "interpolated reference curve, ESS-triggered systematic resampling, weighted-mean estimate; "
                      "returns per-run log-likelihood for downstream ensemble weighting.",
         "semantic": "track a drifting signal / geosteering / keep hypotheses alive under noise / physics prior "
                     "with measurement correction / Bayesian filtering"},
     "proof": "tracks a synthetic drifting state within tolerance while an observation-blind variant drifts off"},
    {"kind": "tracking.systematic_resample", "title": "Systematic (low-variance) particle resampling",
     "input_edge": "ParticleWeights", "output_edge": "SurvivorIndices",
     "tags": ["tracking", "resampling", "monte-carlo"],
     "registers": {
         "plain": "Given how believable each guess is, decides which guesses survive to the next round — heavy "
                  "believers multiply, hopeless ones die — with as little luck involved as possible.",
         "technical": "Low-variance systematic resampling: one uniform draw u0, N evenly-spaced pointers u0+i/N "
                      "walk the cumulative normalized weights; expected copy count is proportional to weight with "
                      "O(N) work and minimal Monte-Carlo variance.",
         "semantic": "particle survival / resampling step / weight degeneracy fix / sequential importance resampling"},
     "proof": "a one-hot weight vector maps every survivor to that index; uniform weights keep diversity"},
    {"kind": "tracking.effective_sample_size", "title": "Effective sample size (particle degeneracy diagnostic)",
     "input_edge": "ParticleWeights", "output_edge": "EffectiveSampleSize",
     "tags": ["tracking", "diagnostic"],
     "registers": {
         "plain": "Measures how many of your guesses still actually matter — if one guess holds all the belief, "
                  "you effectively have one guess left and it is time to reshuffle.",
         "technical": "ESS = 1/Σ(w/Σw)² over particle weights: equals N for uniform weights, 1 for one-hot; the "
                      "canonical trigger (ESS < fraction·N) for the resampling step in sequential Monte-Carlo.",
         "semantic": "weight collapse / degeneracy metric / when to resample / filter health"},
     "proof": "uniform weights give N; a one-hot vector gives 1"},
    {"kind": "tracking.beam_search_grid_path", "title": "Beam-search path decoder over a discrete grid",
     "input_edge": "EmissionSeries+GridValues+StartIndex", "output_edge": "BestGridPath",
     "tags": ["decoding", "search", "dynamic-programming"],
     "registers": {
         "plain": "Finds the best route through a ladder of possible levels to explain a sequence of readings, "
                  "keeping only the few most promising routes alive at each step.",
         "technical": "Bounded-width Viterbi-style decoding: states are grid indices, transitions ±max_step with "
                      "cost move_cost·|Δ| plus squared emission mismatch / emission_scale; per-step candidate "
                      "dedupe keeps the best beam_size states; backpointers recover the optimal surviving path.",
         "semantic": "path decoding / constrained alignment / stiffness-controlled tracking / HMM-like decoding "
                     "without probabilities"},
     "proof": "recovers a planted staircase path; a high move-cost run stays measurably flatter (stiffness knob works)"},
    {"kind": "tracking.ncc_best_offset", "title": "Normalized cross-correlation template match",
     "input_edge": "TemplateSeries+SearchSeries", "output_edge": "BestOffset+MatchScore",
     "tags": ["alignment", "correlation", "signal"],
     "registers": {
         "plain": "Slides a short pattern along a long recording and reports where it lines up best — even when "
                  "one instrument reads systematically higher or is scaled differently.",
         "technical": "Per-window standardized cross-correlation (subtract mean, divide by norm on both sides) — "
                      "invariant to affine gain/offset; returns argmax offset and score in [−1,1] plus the full "
                      "score profile.",
         "semantic": "log correlation / template alignment / gain-invariant matching / find the depth shift"},
     "proof": "finds a planted template under gain+offset distortion at the exact offset with a near-1 score"},
    {"kind": "tracking.robust_irls_polyfit", "title": "Robust IRLS polynomial fit (outlier-resistant trend)",
     "input_edge": "XYSeries+Degree", "output_edge": "RobustTrendFit",
     "tags": ["regression", "robust", "denoising"],
     "registers": {
         "plain": "Draws a smooth trend through data where a few points are wildly wrong, by letting the odd "
                  "ones out lose their vote instead of bending the line.",
         "technical": "Iteratively-reweighted least squares: ordinary polyfit, then Cauchy weights "
                      "1/(1+(r/2s)²) on 1.4826·MAD-scaled residuals, refit for k iterations; normal equations "
                      "solved by partial-pivot Gaussian elimination (pure python).",
         "semantic": "robust regression / outlier-immune smoothing / trajectory projection / M-estimation"},
     "proof": "one gross outlier barely moves the fit (versus ordinary least squares it stays close to the clean curve)"},
    {"kind": "tracking.likelihood_weighted_ensemble", "title": "Likelihood-weighted seed ensemble",
     "input_edge": "PerRunPredictions+PerRunLogLikelihoods", "output_edge": "WeightedEnsemblePrediction",
     "tags": ["ensemble", "weighting", "monte-carlo"],
     "registers": {
         "plain": "Averages many independent runs, but gives the runs that explained the observed data better a "
                  "louder voice instead of counting everyone equally.",
         "technical": "Softmax over per-run log-likelihoods with a temperature-like scale (weights ∝ "
                      "exp((llᵢ−max)/scale)); scale→∞ degrades gracefully to the plain mean; returns weights for "
                      "the receipt trail.",
         "semantic": "seed ensembling / evidence-weighted averaging / Bayesian model averaging (approximate)"},
     "proof": "a much-higher-likelihood run dominates the blend; a huge scale recovers the near-uniform mean"},
    {"kind": "tracking.inverse_distance_weighted_impute", "title": "Inverse-distance-weighted spatial imputation",
     "input_edge": "ScatteredPointValues+QueryLocations", "output_edge": "ImputedValues+NeighborDistances",
     "tags": ["spatial", "imputation", "interpolation"],
     "registers": {
         "plain": "Estimates a value where nothing was measured by asking the nearest measured places and "
                  "trusting closer neighbors more.",
         "technical": "k-nearest IDW: weights 1/d^power over the k nearest scattered points, exact hits "
                      "short-circuit to the observed value; returns nearest-neighbor distance as a confidence "
                      "signal.",
         "semantic": "offset-well borrowing / spatial gap fill / kriging-lite / neighborhood interpolation"},
     "proof": "a query at a data point returns exactly its value; the midpoint of two equal neighbors returns their mean"},
    {"kind": "tracking.exponential_warmup_blend", "title": "Exponential warm-up correction ramp",
     "input_edge": "BaselineSeries+CorrectionSeries+DistanceFromAnchor", "output_edge": "RampBlendedSeries",
     "tags": ["blending", "calibration", "ramp"],
     "registers": {
         "plain": "Lets a learned correction fade in gradually: right where you still trust the anchor it stays "
                  "silent, far away it applies in full.",
         "technical": "blended = base + α·(1−exp(−d/τ))·correction per point; τ sets the trust horizon, α the "
                      "global correction scale; τ→0 applies immediately, d=0 applies nothing.",
         "semantic": "correction warm-up / anchor-respecting blend / residual model on top of physics"},
     "proof": "zero distance leaves the baseline untouched; far distance converges to base+α·correction"},
    {"kind": "tracking.backtest_gated_override", "title": "Backtest-gated override (guard every shortcut)",
     "input_edge": "BasePrediction+CandidatePrediction+VisibleReference", "output_edge": "GuardedPrediction+AdoptionReceipt",
     "tags": ["guard", "validation", "override"],
     "registers": {
         "plain": "Before trusting a tempting shortcut answer, checks it against the part of the truth you can "
                  "already see; only if it nails that part does it replace the default.",
         "technical": "Computes candidate RMSE on the visible reference section; adopts the candidate iff "
                      "rmse ≤ gate, else passes the base through unchanged; emits the measured RMSE and decision "
                      "as a receipt.",
         "semantic": "guarded lookup / shortcut validation / self-check before override / leak-safe exploitation"},
     "proof": "an aligned candidate (backtest 0) is adopted; a misaligned one is rejected and the base survives"},
    {"kind": "tracking.confidence_gated_blend", "title": "Confidence-gated per-group calibration blend",
     "input_edge": "BasePrediction+CandidatePrediction+GainConsistencyEvidence", "output_edge": "CalibratedPrediction+MoveReceipt",
     "tags": ["calibration", "gating", "blending"],
     "registers": {
         "plain": "Only nudges the answer toward an alternative when the evidence says the alternative is both "
                  "better and consistently better — and even then, never by more than a capped amount.",
         "technical": "alpha = 0 unless gain ≥ min_gain AND consistency ≥ min_consistency; qualifying alpha "
                      "scales with gain up to max_alpha; per-point move hard-clipped to ±move_clip; emits alpha "
                      "and max move for the receipt.",
         "semantic": "per-well calibration / evidence-gated adjustment / conservative overlay / bounded correction"},
     "proof": "below-threshold evidence leaves the base byte-identical; qualifying evidence moves it, clipped"},
    {"kind": "tracking.prediction_integrity_audit", "title": "Prediction artifact integrity audit (id order + finite + SHA-256)",
     "input_edge": "PredictionIds+PredictionValues+ExpectedManifest", "output_edge": "AuditVerdict+CanonicalSha256",
     "tags": ["audit", "integrity", "receipt"],
     "registers": {
         "plain": "A final read-only check that the file about to ship has exactly the expected rows in the "
                  "expected order with no broken numbers — plus a fingerprint so you can prove later which file "
                  "it was.",
         "technical": "Validates id sequence equality against the manifest, value/id count agreement, and "
                      "finiteness; computes SHA-256 over canonical sorted-key JSON; never mutates — violations "
                      "return ok=false with named problems.",
         "semantic": "submission audit / artifact fingerprint / ship gate / reproducibility receipt"},
     "proof": "an aligned finite artifact passes with a stable hash; a shuffled id order or NaN flips ok=false"},
]


def _card(spec: dict[str, Any]) -> dict[str, Any]:
    pid = canonical_id(PRIMITIVE_ID_PREFIX, spec["kind"], spec["title"])
    return {"primitive_id": pid, "title": spec["title"], "blackbox": spec["registers"]["technical"],
            "registers": spec["registers"], "primitive_kind": spec["kind"], "kind": "tracking.primitive",
            "input_edge": spec["input_edge"], "output_edge": spec["output_edge"],
            "capability_tags": spec["tags"], "domains": ["algorithms", "ml", "geo/time", "signal"],
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
    """Micro-geosteering end to end: a reference curve + drifting truth → particle-filter track → likelihood
    ensemble over seeds → warm-up blend with a learned correction → backtest-gated shortcut → integrity audit."""
    reference_x = [float(i) for i in range(0, 41, 2)]
    reference_y = [math.sin(x / 4.0) * 10.0 + x for x in reference_x]
    truth = [10.0 + 0.15 * i for i in range(30)]
    observations = [_interp(t, reference_x, reference_y) for t in truth]
    runs = [particle_filter_track(observations, reference_x, reference_y, start_state=10.0, seed=s,
                                  n_particles=120) for s in (1, 2, 3)]
    ensemble = likelihood_weighted_ensemble([r["path"] for r in runs], [r["log_likelihood"] for r in runs])
    audit = prediction_integrity_audit([f"row_{i}" for i in range(30)], ensemble["prediction"],
                                       [f"row_{i}" for i in range(30)])
    return {"tracker_rmse": round(_rmse(ensemble["prediction"], truth), 3),
            "ensemble_weights": ensemble["weights"], "audit_ok": audit["ok"],
            "audit_sha256": audit["sha256"][:16], **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # shared synthetic world: monotone reference curve + drifting hidden state (deterministic)
    reference_x = [float(i) for i in range(0, 41, 2)]
    reference_y = [math.sin(x / 4.0) * 10.0 + x for x in reference_x]
    truth = [10.0 + 0.15 * i for i in range(30)]
    observations = [_interp(t, reference_x, reference_y) for t in truth]

    # 1 particle filter: tracks the drift; an observation-BLIND variant (huge sigma → flat likelihood)
    #   drifts measurably worse (MUTATION-SENSITIVE: the likelihood update is load-bearing)
    tracked = particle_filter_track(observations, reference_x, reference_y, start_state=10.0, seed=42)
    blind = particle_filter_track(observations, reference_x, reference_y, start_state=10.0, seed=42,
                                  observation_sigma=1e9)
    rmse_tracked = _rmse(tracked["path"], truth)
    rmse_blind = _rmse(blind["path"], truth)
    deterministic = particle_filter_track(observations, reference_x, reference_y, start_state=10.0, seed=42)
    checks.append(("particle filter: tracks drift (rmse<1.5), beats the observation-blind run, deterministic",
                   rmse_tracked < 1.5 and rmse_tracked < rmse_blind
                   and json.dumps(deterministic) == json.dumps(tracked)))

    # 2 systematic resample: one-hot → all survivors are that index; uniform keeps diversity; deterministic
    one_hot = systematic_resample([0.0, 0.0, 1.0, 0.0], seed=3)
    uniform = systematic_resample([1.0] * 8, seed=3)
    checks.append(("systematic resample: one-hot collapses to the winner; uniform keeps diversity",
                   set(one_hot) == {2} and len(set(uniform)) >= 6
                   and uniform == systematic_resample([1.0] * 8, seed=3)))

    # 3 ESS: uniform → N; one-hot → 1
    checks.append(("effective sample size: uniform=N, one-hot=1",
                   abs(effective_sample_size([0.25] * 4) - 4.0) < 1e-9
                   and abs(effective_sample_size([0.0, 1.0, 0.0]) - 1.0) < 1e-9))

    # 4 beam search: recovers a planted staircase; a HIGH move-cost path is flatter (stiffness knob works)
    grid = [float(v) for v in range(0, 20)]
    planted = [0, 1, 2, 3, 4, 5, 6, 7]
    emissions = [grid[i] for i in planted]
    loose = beam_search_grid_path(emissions, grid, 0, beam_size=6, move_cost=0.01, emission_scale=1.0)
    stiff = beam_search_grid_path(emissions, grid, 0, beam_size=6, move_cost=500.0, emission_scale=1.0)
    stiff_span = max(stiff["path_indices"]) - min(stiff["path_indices"])
    checks.append(("beam search: recovers the planted staircase; high move-cost stays flatter",
                   loose["path_indices"] == planted and stiff_span < (max(planted) - min(planted))))

    # 5 NCC: finds a gain+offset-distorted template at the planted offset with a ~1 score
    haystack = [math.sin(i / 3.0) * 5.0 for i in range(60)]
    planted_offset = 23
    needle = [3.0 * haystack[planted_offset + i] + 40.0 for i in range(9)]   # affine distortion
    match = ncc_best_offset(needle, haystack)
    checks.append(("ncc: planted template found at the exact offset despite gain+offset distortion",
                   match["best_offset"] == planted_offset and match["best_score"] > 0.999))

    # 6 IRLS: one gross outlier cannot drag the robust fit (vs ordinary LS it stays near the clean curve)
    xs = [float(i) for i in range(12)]
    clean = [2.0 + 0.5 * x + 0.1 * x * x for x in xs]
    dirty = clean[:]
    dirty[6] += 80.0
    robust = robust_irls_polyfit(xs, dirty, degree=2, iterations=5)
    ordinary = _weighted_polyfit(xs, dirty, 2, [1.0] * len(xs))
    robust_error = abs(robust["fitted"][6] - clean[6])
    ordinary_error = abs(_polyval(ordinary, xs[6]) - clean[6])
    checks.append(("robust IRLS: outlier point barely moves the fit (robust error << ordinary LS error)",
                   robust_error < 3.0 and ordinary_error > 3.0 * robust_error
                   and robust["final_weights"][6] < 0.2))

    # 7 likelihood ensemble: the better-likelihood run dominates; huge scale → near-uniform mean
    predictions = [[0.0] * 5, [10.0] * 5]
    sharp = likelihood_weighted_ensemble(predictions, [-100.0, -1.0], scale=5.0)
    flat = likelihood_weighted_ensemble(predictions, [-100.0, -1.0], scale=1e9)
    checks.append(("likelihood ensemble: high-likelihood run dominates; scale→∞ recovers the mean",
                   sharp["weights"][1] > 0.99 and sharp["prediction"][0] > 9.9
                   and abs(flat["prediction"][0] - 5.0) < 0.01))

    # 8 IDW: exact hit returns the observed value; equal-distance midpoint returns the mean
    points = [(0.0, 0.0, 10.0), (2.0, 0.0, 30.0), (50.0, 50.0, 999.0)]
    idw = inverse_distance_weighted_impute(points, [(0.0, 0.0), (1.0, 0.0)], k=2)
    checks.append(("IDW: exact hit returns its value; midpoint of two equal neighbors returns the mean",
                   idw["estimates"][0] == 10.0 and abs(idw["estimates"][1] - 20.0) < 1e-6))

    # 9 warm-up ramp: silent at the anchor, full correction far away
    ramped = exponential_warmup_blend([100.0, 100.0, 100.0], [10.0, 10.0, 10.0],
                                      [0.0, 120.0, 12000.0], tau=120.0, alpha=1.0)
    checks.append(("warm-up ramp: distance 0 leaves the base; far distance converges to base+correction",
                   ramped["blended"][0] == 100.0 and 106.0 < ramped["blended"][1] < 107.0
                   and abs(ramped["blended"][2] - 110.0) < 0.01))

    # 10 backtest gate: aligned candidate adopted; misaligned candidate rejected (base survives)
    base = [1.0, 1.0, 1.0]
    candidate = [5.0, 5.0, 5.0]
    adopted = backtest_gated_override(base, candidate, [7.0, 7.0], [7.0, 7.0], rmse_gate=1.0)
    rejected = backtest_gated_override(base, candidate, [7.0, 7.0], [40.0, 40.0], rmse_gate=1.0)
    checks.append(("backtest gate: proven candidate adopted; misaligned candidate rejected, base kept",
                   adopted["adopted_candidate"] and adopted["prediction"] == candidate
                   and not rejected["adopted_candidate"] and rejected["prediction"] == base))

    # 11 confidence blend: weak evidence → byte-identical base; strong evidence → clipped move
    weak = confidence_gated_blend([0.0] * 3, [100.0] * 3, gain=0.1, consistency=0.9)
    strong = confidence_gated_blend([0.0] * 3, [100.0] * 3, gain=3.0, consistency=0.9, move_clip=5.0)
    checks.append(("confidence blend: below-threshold evidence changes nothing; qualifying move is clipped",
                   weak["blended"] == [0.0, 0.0, 0.0] and weak["alpha"] == 0.0
                   and strong["qualified"] and strong["max_abs_move"] == 5.0))

    # 12 integrity audit: aligned+finite passes with a stable hash; shuffled ids or NaN flip ok=false
    ids = ["a", "b", "c"]
    good = prediction_integrity_audit(ids, [1.0, 2.0, 3.0], ids)
    shuffled = prediction_integrity_audit(["b", "a", "c"], [1.0, 2.0, 3.0], ids)
    broken = prediction_integrity_audit(ids, [1.0, float("nan"), 3.0], ids)
    stable = prediction_integrity_audit(ids, [1.0, 2.0, 3.0], ids)
    checks.append(("integrity audit: pass + stable sha; shuffled id order and NaN both flip ok=false",
                   good["ok"] and good["sha256"] == stable["sha256"]
                   and not shuffled["ok"] and not broken["ok"]))

    # cards: deterministic, unique ids, candidate-only, typed edges, 3 registers, oracle-backed
    cards = emit_cards()
    checks.append(("12 cards: deterministic, unique ids, candidate-only, typed edges, 3-register descriptions",
                   len(cards) == 12 and len({c["primitive_id"] for c in cards}) == 12
                   and all(c["candidate"] and not c["serves_truth"] and c["input_edge"] and c["output_edge"]
                           and set(c["registers"]) == {"plain", "technical", "semantic"}
                           and c["proof_requirements"] for c in cards)
                   and json.dumps(cards, sort_keys=True) == json.dumps(emit_cards(), sort_keys=True)))

    # the demo pipeline runs end to end and its audit passes
    d = demo()
    checks.append(("demo: PF→ensemble→audit end-to-end; tracker rmse < 1.5 and the shipped artifact audits ok",
                   d["tracker_rmse"] < 1.5 and d["audit_ok"]))

    ok = all(v for _, v in checks)
    print("physics_tracking_primitives — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print("  12 tracking/estimation kernels, deterministic + oracle-verified: particle-filter · resample · ESS "
          "· beam-search · NCC · robust-IRLS · lik-ensemble · IDW · warm-up · backtest-gate · confidence-blend "
          "· integrity-audit. candidate-only.")
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
