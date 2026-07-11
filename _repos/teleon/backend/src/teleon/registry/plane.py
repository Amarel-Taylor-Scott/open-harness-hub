"""registry.plane — policy-driven selection over a PLANE of interchangeable adapters (the flexible alternative to
hardcoded best_X() wrappers).

A PLANE is a set of candidate adapters, each carrying metadata (locality / keyless / cost / quality) + an
availability probe. A POLICY ranks the candidates; selection DESCENDS the ranked list to the first AVAILABLE one
(an honest fallback chain). This generalizes the repo's agnostic-port + capability-ladder + PreferenceProfile
thesis to ANY plane (embedding, llm, ocr, vector-store, …):

  - add an adapter   -> append a Candidate (no selection logic changes);
  - add a preference -> register a policy (a ranking key);
  - select           -> select(candidates, policy) -> the best AVAILABLE adapter, or None (honest).

Nothing is hardcoded; local-first is just the DEFAULT policy, not a baked-in branch. serves_truth=false.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class py_class_src_teleon_registry_plane__Candidate:
    """One adapter in a plane + the metadata a policy ranks on."""
    name: str
    factory: Callable[[], object]          # () -> the adapter instance
    locality: str = "local"                # "local" | "cloud"
    keyless: bool = True                   # needs no API key?
    cost: float = 0.0                      # relative est cost (0 = free/local)
    quality: int = 1                       # quality tier (higher = better)
    probe: Callable[[], bool] | None = field(default=None)  # availability check; None = always available


def py_function_src_teleon_registry_plane___local(py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__local__c: py_class_src_teleon_registry_plane__Candidate) -> int:
    return 0 if py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__local__c.locality == "local" else 1


# POLICIES: name -> sort key (ascending; the smallest key is preferred). Compose freely — adding a preference is
# adding an entry here, never editing select().
py_const_src_teleon_registry_plane__POLICIES: dict[str, Callable[[py_class_src_teleon_registry_plane__Candidate], tuple]] = {
    "local_first": lambda py_arg_src_teleon_registry_plane__c: (py_function_src_teleon_registry_plane___local(py_arg_src_teleon_registry_plane__c), py_arg_src_teleon_registry_plane__c.cost, -py_arg_src_teleon_registry_plane__c.quality),
    "keyless_first": lambda py_arg_src_teleon_registry_plane__c: (0 if py_arg_src_teleon_registry_plane__c.keyless else 1, py_function_src_teleon_registry_plane___local(py_arg_src_teleon_registry_plane__c), -py_arg_src_teleon_registry_plane__c.quality),
    "cheapest": lambda py_arg_src_teleon_registry_plane__c: (py_arg_src_teleon_registry_plane__c.cost, py_function_src_teleon_registry_plane___local(py_arg_src_teleon_registry_plane__c), -py_arg_src_teleon_registry_plane__c.quality),
    "best_quality": lambda py_arg_src_teleon_registry_plane__c: (-py_arg_src_teleon_registry_plane__c.quality, py_arg_src_teleon_registry_plane__c.cost, py_function_src_teleon_registry_plane___local(py_arg_src_teleon_registry_plane__c)),
    "fastest_local": lambda py_arg_src_teleon_registry_plane__c: (py_function_src_teleon_registry_plane___local(py_arg_src_teleon_registry_plane__c), -py_arg_src_teleon_registry_plane__c.quality, py_arg_src_teleon_registry_plane__c.cost),
}
py_const_src_teleon_registry_plane__DEFAULT_POLICY = "local_first"


def py_function_src_teleon_registry_plane__register_policy(py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__register_policy__name: str, py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__register_policy__key: Callable[[py_class_src_teleon_registry_plane__Candidate], tuple]) -> None:
    """Add a selection preference; select() never changes."""
    py_const_src_teleon_registry_plane__POLICIES[str(py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__register_policy__name)] = py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__register_policy__key


def py_function_src_teleon_registry_plane__ranked(py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__ranked__candidates: list[py_class_src_teleon_registry_plane__Candidate], py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__ranked__policy: str = py_const_src_teleon_registry_plane__DEFAULT_POLICY, *, require_keyless: bool = False) -> list[py_class_src_teleon_registry_plane__Candidate]:
    """The candidates ranked by `policy` (filtered to keyless when required) — for selection + introspection."""
    py_local_src_teleon_registry_plane__ranked__pool = [py_arg_src_teleon_registry_plane__c for py_arg_src_teleon_registry_plane__c in py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__ranked__candidates if py_arg_src_teleon_registry_plane__c.keyless or not require_keyless]
    return sorted(py_local_src_teleon_registry_plane__ranked__pool, key=py_const_src_teleon_registry_plane__POLICIES.get(py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__ranked__policy, py_const_src_teleon_registry_plane__POLICIES[py_const_src_teleon_registry_plane__DEFAULT_POLICY]))


def py_function_src_teleon_registry_plane__select(py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__select__candidates: list[py_class_src_teleon_registry_plane__Candidate], py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__select__policy: str = py_const_src_teleon_registry_plane__DEFAULT_POLICY, *, require_keyless: bool = False):
    """Rank by policy, then DESCEND to the first AVAILABLE candidate (the fallback chain). Honest: None if none
    available. This is the one selection primitive every plane uses — no per-plane best_X() wrappers."""
    for py_local_src_teleon_registry_plane__select__c in py_function_src_teleon_registry_plane__ranked(py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__select__candidates, py_arg_src_teleon_registry_plane__py_function_src_teleon_registry_plane__select__policy, require_keyless=require_keyless):
        if py_local_src_teleon_registry_plane__select__c.probe is None or py_local_src_teleon_registry_plane__select__c.probe():
            return py_local_src_teleon_registry_plane__select__c.factory()
    return None
