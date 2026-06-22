"""equivalence — canonicalization done HONESTLY. Knowing that paddleocr ≈ tesseract ≈ a vision-LLM for `extract_text` is
what makes fallbacks, ladders, dedupe, and learning GENERALIZE across the registry. But general program equivalence is
UNDECIDABLE — so two components/pipelines are equivalent only *to within a benchmark/probe set* (they agree on it). We
treat equivalence classes as **learned, benchmark-relative artifacts, never theorems**: every verdict carries the probe
size + threshold and is flagged `proven=False`. serves_truth=false.
"""
from __future__ import annotations


def agreement(outputs_a: list, outputs_b: list) -> float:
    """Fraction of probe items where two runners produced the SAME output. Empty/length-mismatch → 0.0 (can't claim
    agreement). This is the empirical signal — not a proof."""
    if not outputs_a or len(outputs_a) != len(outputs_b):
        return 0.0
    same = sum(1 for x, y in zip(outputs_a, outputs_b) if x == y)
    return same / len(outputs_a)


def equivalent(outputs_a: list, outputs_b: list, *, threshold: float = 0.95) -> dict:
    """Benchmark-relative equivalence: agreement on the probe set ≥ threshold. NOT a proof. Returns {equivalent,
    agreement, probe_size, threshold, proven:False, benchmark_relative:True}."""
    ag = agreement(outputs_a, outputs_b)
    return {"equivalent": ag >= threshold and bool(outputs_a), "agreement": round(ag, 4),
            "probe_size": len(outputs_a), "threshold": threshold, "proven": False, "benchmark_relative": True,
            "serves_truth": False}


def equivalence_classes(runner_outputs: dict, *, threshold: float = 0.95) -> dict:
    """Cluster runners by pairwise agreement on a SHARED probe set into benchmark-relative equivalence classes.
    runner_outputs: {runner_id: [outputs over the same probe items]}. Returns {classes:[[runner_ids]], threshold,
    probe_size, proven:False}. Transitive-closure clustering (union-find) over the agreement graph."""
    ids = list(runner_outputs)
    parent = {i: i for i in ids}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        parent[find(a)] = find(b)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if agreement(runner_outputs[ids[i]], runner_outputs[ids[j]]) >= threshold:
                union(ids[i], ids[j])
    groups: dict = {}
    for i in ids:
        groups.setdefault(find(i), []).append(i)
    classes = sorted((sorted(g) for g in groups.values()), key=lambda g: (-len(g), g[0]))
    probe = len(next(iter(runner_outputs.values()))) if runner_outputs else 0
    return {"classes": classes, "threshold": threshold, "probe_size": probe, "proven": False,
            "benchmark_relative": True, "serves_truth": False}
