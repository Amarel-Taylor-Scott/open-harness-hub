"""registry.variations — generate FORKS / VARIATIONS of any registry record (the owner's fork-generation discipline
applied to DATA, not just architecture).

For every component — no matter how big or small, down to a single registry row — ask the variation questions:
  - What variations of this exist?
  - Are there INDUSTRY-specific variations? (how would this vary for healthcare / finance / legal / …)
  - How would it vary by REGION / SCALE / regulatory regime?
  - What alternative APPROACHES implement it? (deterministic / ML / LLM / hybrid)

…and emit each as a governed CANDIDATE variation (variation_of + axis + value). discovery != trust: a generated
variation is a candidate to verify + populate, never asserted. serves_truth=false. Pairs with registry.plane
(forks of an ADAPTER, policy-selected) — this is forks of a RECORD.
"""
from __future__ import annotations

import itertools

#: canonical variation axes + example values (extend freely; values can be supplied per call).
py_const_src_teleon_registry_variations__AXES: dict[str, list[str]] = {
    "industry": ["healthcare", "finance", "legal", "government", "retail", "manufacturing", "education",
                 "real_estate", "logistics", "energy"],
    "geography": ["us", "canada", "uk", "germany", "france", "india", "china", "japan", "brazil", "australia",
                  "uae", "singapore"],
    "region": ["us", "eu", "uk", "apac", "latam", "mena"],
    "season": ["spring", "summer", "fall", "winter"],
    "time_period": ["2024", "2025", "2026", "historical", "forecast"],
    "scale": ["individual", "startup", "smb", "enterprise"],
    "approach": ["deterministic", "ml", "llm", "hybrid"],
}


def py_function_src_teleon_registry_variations___base_id(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__base_id__record: dict) -> str:
    return str(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__base_id__record.get("id") or py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__base_id__record.get("canonical") or py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__base_id__record.get("name") or "record")


def py_function_src_teleon_registry_variations__fork_questions(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__fork_questions__record: dict) -> list[str]:
    """The variation questions to ASK for this record (the discipline, made explicit + per-record)."""
    py_local_src_teleon_registry_variations__fork_questions__name = py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__fork_questions__record.get("name") or py_function_src_teleon_registry_variations___base_id(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__fork_questions__record)
    return [
        f"What variations of '{py_local_src_teleon_registry_variations__fork_questions__name}' exist?",
        f"Are there INDUSTRY-specific variations of '{py_local_src_teleon_registry_variations__fork_questions__name}' (healthcare / finance / legal / government / …)?",
        f"How would '{py_local_src_teleon_registry_variations__fork_questions__name}' vary by region / scale / regulatory regime?",
        f"What alternative APPROACHES implement '{py_local_src_teleon_registry_variations__fork_questions__name}' (deterministic / ML / LLM / hybrid)?",
    ]


def py_function_src_teleon_registry_variations__variations_of(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__record: dict, py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__axis: str, py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__values: list[str] | None = None) -> list[dict]:
    """Generate candidate variations of `record` along `axis` (e.g. industry). Each is a governed candidate fork."""
    py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__values = py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__values if py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__values is not None else py_const_src_teleon_registry_variations__AXES.get(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__axis, [])
    py_local_src_teleon_registry_variations__variations_of__base = py_function_src_teleon_registry_variations___base_id(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__record)
    py_local_src_teleon_registry_variations__variations_of__name = py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__record.get("name") or py_local_src_teleon_registry_variations__variations_of__base
    py_local_src_teleon_registry_variations__variations_of__out = []
    for py_local_src_teleon_registry_variations__variations_of__v in py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__values:
        py_local_src_teleon_registry_variations__variations_of__out.append({
            **py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__record,
            "id": f"{py_local_src_teleon_registry_variations__variations_of__base}::{py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__axis}={py_local_src_teleon_registry_variations__variations_of__v}",
            "name": f"{py_local_src_teleon_registry_variations__variations_of__name} ({py_local_src_teleon_registry_variations__variations_of__v} {py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__axis})",
            "variation_of": py_local_src_teleon_registry_variations__variations_of__base, "variation_axis": py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__variations_of__axis, "variation_value": py_local_src_teleon_registry_variations__variations_of__v,
            "candidate": True, "serves_truth": False,
        })
    return py_local_src_teleon_registry_variations__variations_of__out


def py_function_src_teleon_registry_variations__expand_record(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__expand_record__record: dict, py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__expand_record__axes: list[str] | None = None) -> dict[str, list[dict]]:
    """Generate the full fork set: variations across MULTIPLE axes for one record."""
    return {axis: py_function_src_teleon_registry_variations__variations_of(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__expand_record__record, axis) for axis in (py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__expand_record__axes or list(py_const_src_teleon_registry_variations__AXES))}


def py_function_src_teleon_registry_variations__mutation_space(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__mutation_space__axes: list[str]) -> int:
    """Variations PER record across the cartesian product of `axes` = product of axis sizes (computed, not typed)."""
    py_local_src_teleon_registry_variations__mutation_space__n = 1
    for py_local_src_teleon_registry_variations__mutation_space__a in py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__mutation_space__axes:
        py_local_src_teleon_registry_variations__mutation_space__n *= max(1, len(py_const_src_teleon_registry_variations__AXES.get(py_local_src_teleon_registry_variations__mutation_space__a, [])))
    return py_local_src_teleon_registry_variations__mutation_space__n


def py_function_src_teleon_registry_variations__mutate_stream(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__mutate_stream__records, py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__mutate_stream__axes: list[str]):
    """LAZILY yield governed candidate variations across the cartesian product of `axes` for each record — so 1M+
    variations stream to the operational store without holding them in memory. Each carries full lineage
    (variation_of + the axis-combo) and is candidate-only (discovery != trust; the specialization is a candidate to
    verify + populate, never asserted). serves_truth=false."""
    py_local_src_teleon_registry_variations__mutate_stream__axis_vals = [py_const_src_teleon_registry_variations__AXES.get(a, []) for a in py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__mutate_stream__axes]
    for py_local_src_teleon_registry_variations__mutate_stream__rec in py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__mutate_stream__records:
        py_local_src_teleon_registry_variations__mutate_stream__base = py_function_src_teleon_registry_variations___base_id(py_local_src_teleon_registry_variations__mutate_stream__rec)
        py_local_src_teleon_registry_variations__mutate_stream__name = py_local_src_teleon_registry_variations__mutate_stream__rec.get("name") or py_local_src_teleon_registry_variations__mutate_stream__base
        for py_local_src_teleon_registry_variations__mutate_stream__combo in itertools.product(*py_local_src_teleon_registry_variations__mutate_stream__axis_vals):
            py_local_src_teleon_registry_variations__mutate_stream__tag = "::".join(f"{a}={v}" for a, v in zip(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__mutate_stream__axes, py_local_src_teleon_registry_variations__mutate_stream__combo))
            yield {
                **py_local_src_teleon_registry_variations__mutate_stream__rec,
                "id": f"{py_local_src_teleon_registry_variations__mutate_stream__base}::{py_local_src_teleon_registry_variations__mutate_stream__tag}",
                "name": f"{py_local_src_teleon_registry_variations__mutate_stream__name} [" + ", ".join(py_local_src_teleon_registry_variations__mutate_stream__combo) + "]",
                "variation_of": py_local_src_teleon_registry_variations__mutate_stream__base, "variation_combo": dict(zip(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__mutate_stream__axes, py_local_src_teleon_registry_variations__mutate_stream__combo)),
                "candidate": True, "serves_truth": False, "generated": True,
            }


def py_function_src_teleon_registry_variations__reachable_count(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__reachable_count__n_records: int, py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__reachable_count__axes: list[str]) -> int:
    """How many candidate variations `n_records` reach across `axes` (n_records x mutation_space)."""
    return py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__reachable_count__n_records * py_function_src_teleon_registry_variations__mutation_space(py_arg_src_teleon_registry_variations__py_function_src_teleon_registry_variations__reachable_count__axes)
