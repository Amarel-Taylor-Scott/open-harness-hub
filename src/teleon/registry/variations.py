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
AXES: dict[str, list[str]] = {
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


def _base_id(record: dict) -> str:
    return str(record.get("id") or record.get("canonical") or record.get("name") or "record")


def fork_questions(record: dict) -> list[str]:
    """The variation questions to ASK for this record (the discipline, made explicit + per-record)."""
    name = record.get("name") or _base_id(record)
    return [
        f"What variations of '{name}' exist?",
        f"Are there INDUSTRY-specific variations of '{name}' (healthcare / finance / legal / government / …)?",
        f"How would '{name}' vary by region / scale / regulatory regime?",
        f"What alternative APPROACHES implement '{name}' (deterministic / ML / LLM / hybrid)?",
    ]


def variations_of(record: dict, axis: str, values: list[str] | None = None) -> list[dict]:
    """Generate candidate variations of `record` along `axis` (e.g. industry). Each is a governed candidate fork."""
    values = values if values is not None else AXES.get(axis, [])
    base = _base_id(record)
    name = record.get("name") or base
    out = []
    for v in values:
        out.append({
            **record,
            "id": f"{base}::{axis}={v}",
            "name": f"{name} ({v} {axis})",
            "variation_of": base, "variation_axis": axis, "variation_value": v,
            "candidate": True, "serves_truth": False,
        })
    return out


def expand_record(record: dict, axes: list[str] | None = None) -> dict[str, list[dict]]:
    """Generate the full fork set: variations across MULTIPLE axes for one record."""
    return {axis: variations_of(record, axis) for axis in (axes or list(AXES))}


def mutation_space(axes: list[str]) -> int:
    """Variations PER record across the cartesian product of `axes` = product of axis sizes (computed, not typed)."""
    n = 1
    for a in axes:
        n *= max(1, len(AXES.get(a, [])))
    return n


def mutate_stream(records, axes: list[str]):
    """LAZILY yield governed candidate variations across the cartesian product of `axes` for each record — so 1M+
    variations stream to the operational store without holding them in memory. Each carries full lineage
    (variation_of + the axis-combo) and is candidate-only (discovery != trust; the specialization is a candidate to
    verify + populate, never asserted). serves_truth=false."""
    axis_vals = [AXES.get(a, []) for a in axes]
    for rec in records:
        base = _base_id(rec)
        name = rec.get("name") or base
        for combo in itertools.product(*axis_vals):
            tag = "::".join(f"{a}={v}" for a, v in zip(axes, combo))
            yield {
                **rec,
                "id": f"{base}::{tag}",
                "name": f"{name} [" + ", ".join(combo) + "]",
                "variation_of": base, "variation_combo": dict(zip(axes, combo)),
                "candidate": True, "serves_truth": False, "generated": True,
            }


def reachable_count(n_records: int, axes: list[str]) -> int:
    """How many candidate variations `n_records` reach across `axes` (n_records x mutation_space)."""
    return n_records * mutation_space(axes)
