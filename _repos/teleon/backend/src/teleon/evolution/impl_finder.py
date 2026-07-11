"""src.teleon.evolution.impl_finder — when a capability is entered, find a MORE-DETERMINISTIC / more-efficient
implementation of it, searching internally (the corpus) and externally (a governed seam).

The distiller turns a capability toward determinism; THIS grounds that in a REAL implementation rather than a
plan. Given a capability, it searches:
  * INTERNALLY — the existing corpus for capabilities serving the same NEED (intent overlap, cross-category) that
    are MORE deterministic or cheaper. e.g. an LLM-based "parse dates from text" (ceiling 0.3) is matched to a
    deterministic `dateparser` library (ceiling 1.0) already in the corpus -> replace the model with the library.
  * EXTERNALLY — a governed seam (off by default). External search IS the discovery/bulk-ingest pipeline (it
    finds new implementations from registries/the web); enable with allow_external + a configured
    ExternalImplSearchPort. Never a silent live call.

It PROPOSES implementations ranked by determinism; the distiller + gates DISPOSE. Pure + deterministic; reads no
disk; Teleon-layer — never imports src.baltor; a found implementation is a candidate, never truth.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.teleon.training.capability_network import _jaccard, _tokens

_EPS = 1e-9
_DEFAULT_MIN_OVERLAP = 0.25  # intent-token Jaccard above which a corpus capability serves the same need
_MAXIMAL_DETERMINISM = 0.99  # at/above this the capability is already ~fully deterministic


@runtime_checkable
class ExternalImplSearchPort(Protocol):
    """The seam for external search (web/registries). A real impl returns candidate implementations for a
    capability; output is a candidate, never truth. Off unless allow_external + a configured port."""

    def search(self, capability: dict) -> list[dict]:
        ...


def find_implementations(capability: dict, corpus: list[dict], *, allow_external: bool = False,
                         external_search: ExternalImplSearchPort | None = None,
                         min_overlap: float = _DEFAULT_MIN_OVERLAP) -> dict:
    """Find more-deterministic / more-efficient implementations of ``capability``. Searches the corpus by intent
    overlap (cross-category — a deterministic library can implement an LLM task), ranks by determinism then
    coverage then overlap, and flags the ones MORE deterministic than the input (the distillation wins). External
    search is a governed seam (off by default; routes through the discovery pipeline)."""
    tslot = capability["capability_slot"]
    target = _tokens(capability.get("intent", ""))
    tdet = float(capability.get("determinism_ceiling", 0.0))

    matches = []
    for c in corpus:
        if c.get("capability_slot") == tslot:
            continue
        overlap = _jaccard(target, _tokens(c.get("intent", "")))
        if overlap >= min_overlap:
            cdet = float(c.get("determinism_ceiling", 0.0))
            matches.append({
                "capability_slot": c["capability_slot"], "category": c.get("category", "other"),
                "determinism_ceiling": cdet,
                "deterministic_coverage_estimate": float(c.get("deterministic_coverage_estimate", 0.0)),
                "intent_overlap": round(overlap, 4), "more_deterministic": cdet > tdet + _EPS,
            })
    matches.sort(key=lambda m: (-m["determinism_ceiling"], -m["deterministic_coverage_estimate"],
                                -m["intent_overlap"], m["capability_slot"]))
    more_det = [m for m in matches if m["more_deterministic"]]
    best = more_det[0] if more_det else None

    external = {"searched": False,
                "reason": ("external search is a governed seam — it routes through the discovery runner / bulk "
                           "ingester; enable with allow_external + a configured ExternalImplSearchPort")}
    if allow_external:
        if external_search is None:
            external = {"searched": False, "reason": "allow_external set but no ExternalImplSearchPort configured"}
        else:
            external = {"searched": True, "results": list(external_search.search(capability))}

    if best is not None:
        rec = (f"replace with the more-deterministic internal implementation '{best['capability_slot']}' "
               f"(determinism {best['determinism_ceiling']} vs {tdet}) — distill toward it")
    elif tdet >= _MAXIMAL_DETERMINISM:
        rec = f"already ~maximally deterministic (ceiling {tdet}); no more-deterministic internal implementation needed"
    else:
        rec = "no more-deterministic internal implementation found; route to external search (the discovery pipeline)"

    return {"capability_slot": tslot, "target_determinism": tdet, "internal_matches": matches,
            "more_deterministic_count": len(more_det), "best_deterministic_impl": best,
            "external": external, "recommendation": rec, "serves_truth": False}
