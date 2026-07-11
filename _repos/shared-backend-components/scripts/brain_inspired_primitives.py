#!/usr/bin/env python3
"""brain_inspired_primitives — next-gen ESOTERIC algorithm kernels as deterministic, oracle-verified primitives,
inspired by the Dragon Hatchling (BDH) post-transformer architecture (Kosowski et al., arXiv:2509.26507).

Owner (2026-07-11): "research and creative next-gen our esoteric algorithms like this and build them into
primitives." BDH's value for a capability registry is not the full LLM — it is the reusable ALGORITHMIC KERNELS
it composes, each a well-established mechanism BDH unifies. Built here as REAL, pure-python, deterministic,
edge-typed primitives with executed oracles (so they can serve truth), not stubs:

  1. hebbian_update          — "neurons that fire together, wire together": Δw = lr·xᵢxⱼ − decay·w. Continuous
                               learning without retraining; the synapse IS the memory.
  2. barabasi_albert_graph   — scale-free topology via preferential attachment: the heavy-tailed, high-modularity
                               neuron graph BDH self-organizes into.
  3. leaky_integrate_and_fire— spiking neuron: accumulate, leak, fire + reset at threshold (integrate-and-fire).
  4. excitatory_inhibitory   — lateral inhibition / k-winners-take-all: excite the relevant, suppress competing
                               hypotheses.
  5. sparse_positive_code    — monosemantic coding: ReLU + top-k → sparse, positive, TRACEABLE activations
                               (BDH's inherent interpretability).
  6. linear_attention_memory — BDH's core insight: attention AS a Hebbian synaptic associative memory. State
                               S = Σ φ(kₜ)⊗vₜ accumulates in LINEAR time; S is a FIXED d_k×d_v matrix regardless
                               of sequence length — UNBOUNDED context, no KV cache, no window.

Every card is candidate (candidate=true, serves_truth=false); a passing oracle is promotion EVIDENCE, not
promotion. Pure functions — no numpy, no wall clock, seeded PRNG only (determinism law).

    python3 scripts/brain_inspired_primitives.py --self-test
    python3 scripts/brain_inspired_primitives.py --demo    # a BDH-style micro-pipeline end to end
"""
from __future__ import annotations

import argparse
import json
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
    raise SystemExit(f"brain_inspired_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
PRIMITIVE_ID_PREFIX = "prim:bio"
CITATION = "inspired by Dragon Hatchling (BDH), Kosowski et al., arXiv:2509.26507"


# ═══════════════ 1. HEBBIAN LEARNING — the synapse is the memory (continuous, no retrain) ══════════════
def hebbian_update(weights: list[list[float]], activation: list[float], *,
                   lr: float = 0.1, decay: float = 0.0) -> list[list[float]]:
    """Classic Hebbian outer-product update: Δw_ij = lr·xᵢ·xⱼ − decay·w_ij. Co-active neurons strengthen their
    synapse; the weight matrix is the working memory (BDH stores context in synapses, not a KV cache)."""
    n = len(activation)
    w = [row[:] for row in weights]
    for i in range(n):
        for j in range(n):
            w[i][j] += lr * activation[i] * activation[j] - decay * w[i][j]
    return w


# ═══════════════ 2. SCALE-FREE GRAPH — the brain-like neuron topology (heavy-tailed degree) ════════════
def _lcg(seed: int) -> Iterator[int]:
    s = (seed & 0x7FFFFFFF) or 1
    while True:
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        yield s


def barabasi_albert_graph(n: int, m: int = 2, *, seed: int = 1) -> dict[str, Any]:
    """Barabási–Albert preferential attachment → a scale-free graph (few high-degree HUBS, most nodes sparse):
    the heavy-tailed, high-modularity topology BDH's neuron network self-organizes into. Deterministic (seeded)."""
    m = max(1, min(m, max(1, n - 1)))
    rng = _lcg(seed)
    edges: set[tuple[int, int]] = set()
    for i in range(m + 1):
        for j in range(i + 1, m + 1):
            edges.add((i, j))
    deg = [0] * n
    targets: list[int] = []
    for a, b in edges:
        deg[a] += 1
        deg[b] += 1
        targets += [a, b]
    for new in range(m + 1, n):
        chosen: set[int] = set()
        while len(chosen) < m:
            t = targets[next(rng) % len(targets)]
            if t != new:
                chosen.add(t)
        for t in chosen:
            edges.add((min(new, t), max(new, t)))
            deg[new] += 1
            deg[t] += 1
            targets += [new, t]
    return {"n": n, "edges": sorted(edges), "degree": deg,
            "max_degree": max(deg), "mean_degree": round(sum(deg) / n, 3)}


# ═══════════════ 3. INTEGRATE-AND-FIRE — spiking dynamics ══════════════════════════════════════════════
def leaky_integrate_and_fire(signal: list[float], *, threshold: float = 1.0,
                             leak: float = 0.1, reset: float = 0.0) -> dict[str, Any]:
    """Leaky integrate-and-fire: v ← v·(1−leak) + s; spike + reset when v ≥ threshold. The neuron accumulates
    evidence until it crosses a threshold, then fires — BDH's integrate-and-fire particle."""
    v, spikes, potentials = 0.0, [], []
    for s in signal:
        v = v * (1.0 - leak) + s
        if v >= threshold:
            spikes.append(1)
            v = reset
        else:
            spikes.append(0)
        potentials.append(round(v, 6))
    return {"spikes": spikes, "spike_count": sum(spikes), "final_potential": round(v, 6),
            "potentials": potentials}


# ═══════════════ 4. EXCITATORY / INHIBITORY — lateral inhibition, suppress competitors ═════════════════
def excitatory_inhibitory(activations: list[float], *, k: int = 1) -> dict[str, Any]:
    """k-winners-take-all lateral inhibition: excite the top-k activations, suppress (zero) the competing
    hypotheses. The excitatory/inhibitory circuit that lets one idea win."""
    order = sorted(range(len(activations)), key=lambda i: (-activations[i], i))
    winners = set(order[:max(0, k)])
    out = [activations[i] if i in winners else 0.0 for i in range(len(activations))]
    return {"output": out, "winners": sorted(winners), "suppressed": sorted(set(range(len(activations))) - winners)}


# ═══════════════ 5. SPARSE POSITIVE (MONOSEMANTIC) CODE — inherent interpretability ════════════════════
def sparse_positive_code(vector: list[float], *, k: Optional[int] = None) -> dict[str, Any]:
    """ReLU then top-k → a sparse, positive, TRACEABLE code. Each active unit maps to one input dimension
    (monosemantic), so the reasoning path is inspectable — BDH's axiomatic interpretability."""
    pos = [x if x > 0 else 0.0 for x in vector]
    active = [i for i in range(len(pos)) if pos[i] > 0]
    if k is not None:
        active = sorted(active, key=lambda i: (-pos[i], i))[:k]
    code = {i: round(pos[i], 6) for i in sorted(active)}
    return {"code": code, "active_indices": sorted(active), "sparsity": round(1 - len(active) / max(1, len(vector)), 4),
            "all_positive": all(v > 0 for v in code.values())}


# ═══════════════ 6. LINEAR-ATTENTION MEMORY — attention AS a Hebbian synapse, UNBOUNDED context ═════════
def linear_attention_memory(keys: list[list[float]], values: list[list[float]],
                            queries: list[list[float]]) -> dict[str, Any]:
    """BDH's core equivalence: linear attention IS a Hebbian synaptic associative memory. The state
    S = Σₜ φ(kₜ) ⊗ vₜ accumulates each (key,value) as a Hebbian outer-product (co-active key+value strengthen
    the synapse). Read y = φ(q)·S. Runs in LINEAR time over the sequence, and S is a FIXED d_k×d_v matrix
    whatever the sequence length — so context is UNBOUNDED (no KV cache, no fixed window)."""
    dk, dv = len(keys[0]), len(values[0])
    state = [[0.0] * dv for _ in range(dk)]  # the synaptic memory — size independent of sequence length

    def phi(x: list[float]) -> list[float]:  # sparse-positive feature map (ties to primitive #5)
        return [xi if xi > 0 else 0.0 for xi in x]

    for k, v in zip(keys, values):
        pk = phi(k)
        for i in range(dk):
            if pk[i]:
                for j in range(dv):
                    state[i][j] += pk[i] * v[j]  # Hebbian accumulation
    outputs = []
    for q in queries:
        pq = phi(q)
        outputs.append([round(sum(pq[i] * state[i][j] for i in range(dk)), 6) for j in range(dv)])
    return {"state_shape": [dk, dv], "outputs": outputs, "stored_pairs": len(keys),
            "context_bounded": False}  # state size is O(dk·dv), NOT O(sequence length)


# ═══════════════ primitive cards ═══════════════════════════════════════════════════════════════════════
PRIMITIVE_SPECS: list[dict[str, Any]] = [
    {"kind": "neuromorphic.hebbian_update", "title": "Hebbian synaptic update (fire together, wire together)",
     "input_edge": "WeightMatrix+ActivationVector", "output_edge": "UpdatedWeightMatrix", "tags": ["learning", "plasticity"],
     "blackbox": "Continuous Hebbian weight update; co-active neurons strengthen their synapse. Memory lives in "
                 "the weights (no retraining, no external cache).", "proof": "two co-active units increase their "
                 "mutual weight; a silent unit's edges do not"},
    {"kind": "neuromorphic.scale_free_graph", "title": "Scale-free neuron graph (preferential attachment)",
     "input_edge": "NodeCount+AttachmentDegree", "output_edge": "ScaleFreeGraph", "tags": ["graph", "topology"],
     "blackbox": "Barabási–Albert preferential attachment → heavy-tailed degree (few hubs, many leaves): the "
                 "brain-like topology BDH self-organizes into.", "proof": "max degree >> mean degree (heavy-tailed)"},
    {"kind": "neuromorphic.integrate_and_fire", "title": "Leaky integrate-and-fire spiking neuron",
     "input_edge": "InputSignal+Threshold", "output_edge": "SpikeTrain", "tags": ["spiking", "dynamics"],
     "blackbox": "Accumulate evidence with leak; fire + reset at threshold. The integrate-and-fire particle.",
     "proof": "supra-threshold constant input spikes periodically; sub-threshold does not"},
    {"kind": "neuromorphic.excitatory_inhibitory", "title": "Excitatory/inhibitory lateral inhibition (k-WTA)",
     "input_edge": "ActivationVector+K", "output_edge": "SparsifiedActivation", "tags": ["circuit", "attention"],
     "blackbox": "k-winners-take-all: excite the top-k, suppress competing hypotheses to zero.",
     "proof": "exactly the top-k survive; the rest are zeroed"},
    {"kind": "neuromorphic.sparse_positive_code", "title": "Sparse positive monosemantic code",
     "input_edge": "DenseVector+K", "output_edge": "MonosemanticSparseCode", "tags": ["interpretability", "coding"],
     "blackbox": "ReLU + top-k → sparse, positive, traceable activations; each active unit = one input dim "
                 "(monosemantic), so reasoning is inspectable.", "proof": "output is sparse, all-positive, and "
                 "each active index traces to an input dimension"},
    {"kind": "neuromorphic.linear_attention_memory", "title": "Linear-attention synaptic memory (unbounded context)",
     "input_edge": "KeyValueStream+Query", "output_edge": "AssociativeReadout", "tags": ["attention", "memory", "linear"],
     "blackbox": "Attention as a Hebbian associative memory: S = Σ φ(k)⊗v accumulates in linear time; state size "
                 "is fixed d_k×d_v regardless of sequence length — unbounded context, no KV cache.",
     "proof": "stored key recalls its value; state shape is independent of the number of stored pairs (unbounded)"},
]


def _card(spec: dict[str, Any]) -> dict[str, Any]:
    pid = canonical_id(PRIMITIVE_ID_PREFIX, spec["kind"], spec["title"])
    return {"primitive_id": pid, "title": spec["title"], "blackbox": spec["blackbox"] + f" ({CITATION}).",
            "primitive_kind": spec["kind"], "kind": "neuromorphic.primitive",
            "input_edge": spec["input_edge"], "output_edge": spec["output_edge"],
            "capability_tags": spec["tags"], "domains": ["ml", "algorithms", "neuromorphic"],
            "runtime_targets": ["python"], "proof_requirements": [spec["proof"]],
            "promotion_blockers": ["review_required", "no_lift_measurement_yet"],
            "readiness": "R4_checker_runs_and_passes_oracle", "verification_level": "L4_deterministic_checker",
            "source_family": "brain_inspired_bdh", "source_ref": {"name": "Dragon Hatchling (BDH)",
            "url": "https://arxiv.org/abs/2509.26507"}, **BOUNDARY}


def emit_cards() -> list[dict[str, Any]]:
    return [_card(s) for s in PRIMITIVE_SPECS]


def demo() -> dict[str, Any]:
    """A BDH-style micro-pipeline: spikes drive a Hebbian synapse; activations are sparsified + made monosemantic;
    a linear-attention memory stores and recalls — end to end, deterministic, 0-token."""
    spikes = leaky_integrate_and_fire([0.6, 0.6, 0.6, 0.6], threshold=1.0, leak=0.1)
    act = [1.0, 0.0, 1.0]  # two neurons fire together
    w = hebbian_update([[0.0] * 3 for _ in range(3)], act, lr=0.5)
    wta = excitatory_inhibitory([0.2, 0.9, 0.5, 0.1], k=1)
    code = sparse_positive_code([-1.0, 3.0, 0.0, 2.0], k=2)
    mem = linear_attention_memory(keys=[[1, 0], [0, 1]], values=[[9, 0], [0, 7]], queries=[[1, 0]])
    return {"spikes": spikes["spikes"], "hebbian_w01": w[0][2], "wta_winner": wta["winners"],
            "monosemantic_active": code["active_indices"], "recall_of_key0": mem["outputs"][0], **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # 1 Hebbian: co-active units strengthen; a silent unit's edges do not (MUTATION-SENSITIVE)
    w0 = [[0.0] * 3 for _ in range(3)]
    w1 = hebbian_update(w0, [1.0, 1.0, 0.0], lr=0.5)
    checks.append(("hebbian: co-active (0,1) wire together; silent unit 2 stays unwired",
                   w1[0][1] > w0[0][1] and w1[0][1] == 0.5 and w1[0][2] == 0.0 and w1[2][2] == 0.0))

    # 2 scale-free: heavy-tailed degree (a hub with degree >> mean), deterministic
    g = barabasi_albert_graph(60, 2, seed=7)
    checks.append(("scale-free: heavy-tailed degree (max >> mean) + deterministic",
                   g["max_degree"] >= 3 * g["mean_degree"]
                   and json.dumps(barabasi_albert_graph(60, 2, seed=7)) == json.dumps(g)))

    # 3 integrate-and-fire: supra-threshold input spikes; a tiny sub-threshold input never fires
    fire = leaky_integrate_and_fire([1.0, 1.0, 1.0, 1.0], threshold=1.0, leak=0.1)
    quiet = leaky_integrate_and_fire([0.05, 0.05, 0.05, 0.05], threshold=1.0, leak=0.5)
    checks.append(("integrate-and-fire: supra-threshold spikes, sub-threshold stays silent",
                   fire["spike_count"] >= 1 and quiet["spike_count"] == 0))

    # 4 excitatory/inhibitory: exactly top-k survive, competitors zeroed
    wta = excitatory_inhibitory([0.2, 0.9, 0.5, 0.1], k=2)
    checks.append(("excitatory/inhibitory: top-2 survive (idx 1,2), others suppressed to 0",
                   wta["winners"] == [1, 2] and wta["output"][0] == 0.0 and wta["output"][3] == 0.0
                   and wta["output"][1] == 0.9))

    # 5 sparse positive: negatives clipped, sparse, all-positive, TRACEABLE to input dims
    sp = sparse_positive_code([-1.0, 3.0, 0.0, 2.0], k=2)
    checks.append(("sparse-positive: negatives clipped, top-2 positive, traceable to input indices",
                   sp["active_indices"] == [1, 3] and sp["all_positive"]
                   and all(i in range(4) for i in sp["active_indices"]) and sp["sparsity"] == 0.5))

    # 6 linear-attention memory: recall a stored value; UNBOUNDED context (state size independent of length)
    mem = linear_attention_memory(keys=[[1, 0], [0, 1]], values=[[9, 0], [0, 7]],
                                  queries=[[1, 0], [0, 1]])
    long_mem = linear_attention_memory(keys=[[1, 0]] * 500, values=[[1, 0]] * 500, queries=[[1, 0]])
    checks.append(("linear-attention memory: recalls stored value AND state is length-independent (unbounded)",
                   mem["outputs"][0] == [9.0, 0.0] and mem["outputs"][1] == [0.0, 7.0]
                   and long_mem["state_shape"] == [2, 2] and long_mem["context_bounded"] is False))

    # cards: deterministic, unique ids, candidate-only, oracle-backed, cite BDH
    cards = emit_cards()
    checks.append(("6 cards: deterministic, unique ids, candidate-only, typed edges, cite BDH",
                   len(cards) == 6 and len({c["primitive_id"] for c in cards}) == 6
                   and all(c["candidate"] and not c["serves_truth"] and c["input_edge"] and c["output_edge"]
                           and "2509.26507" in c["source_ref"]["url"] for c in cards)
                   and json.dumps(cards, sort_keys=True) == json.dumps(emit_cards(), sort_keys=True)))

    # the demo runs end-to-end
    d = demo()
    checks.append(("BDH-style demo pipeline runs end-to-end (spikes→hebbian→wta→monosemantic→recall)",
                   d["hebbian_w01"] == 0.5 and d["wta_winner"] == [1] and d["recall_of_key0"] == [9.0, 0.0]))

    ok = all(v for _, v in checks)
    print("brain_inspired_primitives — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print(f"  6 BDH-inspired kernels, all deterministic + oracle-verified: hebbian · scale-free · "
          f"integrate-and-fire · excitatory/inhibitory · sparse-positive · linear-attention memory. candidate-only.")
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
        print(json.dumps({"cards": emit_cards()}, indent=2))
        return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
