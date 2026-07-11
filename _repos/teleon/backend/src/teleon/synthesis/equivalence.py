"""equivalence — canonicalization done HONESTLY. Knowing that paddleocr ≈ tesseract ≈ a vision-LLM for `extract_text` is
what makes fallbacks, ladders, dedupe, and learning GENERALIZE across the registry. But general program equivalence is
UNDECIDABLE — so two components/pipelines are equivalent only *to within a benchmark/probe set* (they agree on it). We
treat equivalence classes as **learned, benchmark-relative artifacts, never theorems**: every verdict carries the probe
size + threshold and is flagged `proven=False`. serves_truth=false.
"""
from __future__ import annotations


def py_function_src_teleon_synthesis_equivalence__agreement(py_arg_src_teleon_synthesis_equivalence__agreement__outputs_a: list, py_arg_src_teleon_synthesis_equivalence__agreement__outputs_b: list) -> float:
    """Fraction of probe items where two runners produced the SAME output. Empty/length-mismatch → 0.0 (can't claim
    agreement). This is the empirical signal — not a proof."""
    if not py_arg_src_teleon_synthesis_equivalence__agreement__outputs_a or len(py_arg_src_teleon_synthesis_equivalence__agreement__outputs_a) != len(py_arg_src_teleon_synthesis_equivalence__agreement__outputs_b):
        return 0.0
    py_local_src_teleon_synthesis_equivalence__agreement__same = sum(1 for x, y in zip(py_arg_src_teleon_synthesis_equivalence__agreement__outputs_a, py_arg_src_teleon_synthesis_equivalence__agreement__outputs_b) if x == y)
    return py_local_src_teleon_synthesis_equivalence__agreement__same / len(py_arg_src_teleon_synthesis_equivalence__agreement__outputs_a)


def py_function_src_teleon_synthesis_equivalence__equivalent(py_arg_src_teleon_synthesis_equivalence__equivalent__outputs_a: list, py_arg_src_teleon_synthesis_equivalence__equivalent__outputs_b: list, *, py_arg_src_teleon_synthesis_equivalence__equivalent__threshold: float = 0.95) -> dict:
    """Benchmark-relative equivalence: agreement on the probe set ≥ threshold. NOT a proof. Returns {equivalent,
    agreement, probe_size, threshold, proven:False, benchmark_relative:True}."""
    py_local_src_teleon_synthesis_equivalence__equivalent__ag = py_function_src_teleon_synthesis_equivalence__agreement(py_arg_src_teleon_synthesis_equivalence__equivalent__outputs_a, py_arg_src_teleon_synthesis_equivalence__equivalent__outputs_b)
    return {"equivalent": py_local_src_teleon_synthesis_equivalence__equivalent__ag >= py_arg_src_teleon_synthesis_equivalence__equivalent__threshold and bool(py_arg_src_teleon_synthesis_equivalence__equivalent__outputs_a), "agreement": round(py_local_src_teleon_synthesis_equivalence__equivalent__ag, 4),
            "probe_size": len(py_arg_src_teleon_synthesis_equivalence__equivalent__outputs_a), "threshold": py_arg_src_teleon_synthesis_equivalence__equivalent__threshold, "proven": False, "benchmark_relative": True,
            "serves_truth": False}


def py_function_src_teleon_synthesis_equivalence__equivalence_classes(py_arg_src_teleon_synthesis_equivalence__equivalence_classes__runner_outputs: dict, *, py_arg_src_teleon_synthesis_equivalence__equivalence_classes__threshold: float = 0.95) -> dict:
    """Cluster runners by pairwise agreement on a SHARED probe set into benchmark-relative equivalence classes.
    runner_outputs: {runner_id: [outputs over the same probe items]}. Returns {classes:[[runner_ids]], threshold,
    probe_size, proven:False}. Transitive-closure clustering (union-find) over the agreement graph."""
    py_local_src_teleon_synthesis_equivalence__equivalence_classes__ids = list(py_arg_src_teleon_synthesis_equivalence__equivalence_classes__runner_outputs)
    py_local_src_teleon_synthesis_equivalence__equivalence_classes__parent = {py_local_src_teleon_synthesis_equivalence__equivalence_classes__i: py_local_src_teleon_synthesis_equivalence__equivalence_classes__i for py_local_src_teleon_synthesis_equivalence__equivalence_classes__i in py_local_src_teleon_synthesis_equivalence__equivalence_classes__ids}
    def find(py_arg_src_teleon_synthesis_equivalence__equivalence_classes_find__x):
        while py_local_src_teleon_synthesis_equivalence__equivalence_classes__parent[py_arg_src_teleon_synthesis_equivalence__equivalence_classes_find__x] != py_arg_src_teleon_synthesis_equivalence__equivalence_classes_find__x:
            py_local_src_teleon_synthesis_equivalence__equivalence_classes__parent[py_arg_src_teleon_synthesis_equivalence__equivalence_classes_find__x] = py_local_src_teleon_synthesis_equivalence__equivalence_classes__parent[py_local_src_teleon_synthesis_equivalence__equivalence_classes__parent[py_arg_src_teleon_synthesis_equivalence__equivalence_classes_find__x]]
            py_arg_src_teleon_synthesis_equivalence__equivalence_classes_find__x = py_local_src_teleon_synthesis_equivalence__equivalence_classes__parent[py_arg_src_teleon_synthesis_equivalence__equivalence_classes_find__x]
        return py_arg_src_teleon_synthesis_equivalence__equivalence_classes_find__x
    def union(py_arg_src_teleon_synthesis_equivalence__equivalence_classes_union__a, py_arg_src_teleon_synthesis_equivalence__equivalence_classes_union__b):
        py_local_src_teleon_synthesis_equivalence__equivalence_classes__parent[find(py_arg_src_teleon_synthesis_equivalence__equivalence_classes_union__a)] = find(py_arg_src_teleon_synthesis_equivalence__equivalence_classes_union__b)
    for py_local_src_teleon_synthesis_equivalence__equivalence_classes__i in range(len(py_local_src_teleon_synthesis_equivalence__equivalence_classes__ids)):
        for py_local_src_teleon_synthesis_equivalence__equivalence_classes__j in range(py_local_src_teleon_synthesis_equivalence__equivalence_classes__i + 1, len(py_local_src_teleon_synthesis_equivalence__equivalence_classes__ids)):
            if py_function_src_teleon_synthesis_equivalence__agreement(py_arg_src_teleon_synthesis_equivalence__equivalence_classes__runner_outputs[py_local_src_teleon_synthesis_equivalence__equivalence_classes__ids[py_local_src_teleon_synthesis_equivalence__equivalence_classes__i]], py_arg_src_teleon_synthesis_equivalence__equivalence_classes__runner_outputs[py_local_src_teleon_synthesis_equivalence__equivalence_classes__ids[py_local_src_teleon_synthesis_equivalence__equivalence_classes__j]]) >= py_arg_src_teleon_synthesis_equivalence__equivalence_classes__threshold:
                union(py_local_src_teleon_synthesis_equivalence__equivalence_classes__ids[py_local_src_teleon_synthesis_equivalence__equivalence_classes__i], py_local_src_teleon_synthesis_equivalence__equivalence_classes__ids[py_local_src_teleon_synthesis_equivalence__equivalence_classes__j])
    py_local_src_teleon_synthesis_equivalence__equivalence_classes__groups: dict = {}
    for py_local_src_teleon_synthesis_equivalence__equivalence_classes__i in py_local_src_teleon_synthesis_equivalence__equivalence_classes__ids:
        py_local_src_teleon_synthesis_equivalence__equivalence_classes__groups.setdefault(find(py_local_src_teleon_synthesis_equivalence__equivalence_classes__i), []).append(py_local_src_teleon_synthesis_equivalence__equivalence_classes__i)
    py_local_src_teleon_synthesis_equivalence__equivalence_classes__classes = sorted((sorted(py_arg_src_teleon_synthesis_equivalence__equivalence_classes__g) for py_arg_src_teleon_synthesis_equivalence__equivalence_classes__g in py_local_src_teleon_synthesis_equivalence__equivalence_classes__groups.values()), key=lambda py_arg_src_teleon_synthesis_equivalence__equivalence_classes__g: (-len(py_arg_src_teleon_synthesis_equivalence__equivalence_classes__g), py_arg_src_teleon_synthesis_equivalence__equivalence_classes__g[0]))
    py_local_src_teleon_synthesis_equivalence__equivalence_classes__probe = len(next(iter(py_arg_src_teleon_synthesis_equivalence__equivalence_classes__runner_outputs.values()))) if py_arg_src_teleon_synthesis_equivalence__equivalence_classes__runner_outputs else 0
    return {"classes": py_local_src_teleon_synthesis_equivalence__equivalence_classes__classes, "threshold": py_arg_src_teleon_synthesis_equivalence__equivalence_classes__threshold, "probe_size": py_local_src_teleon_synthesis_equivalence__equivalence_classes__probe, "proven": False,
            "benchmark_relative": True, "serves_truth": False}
