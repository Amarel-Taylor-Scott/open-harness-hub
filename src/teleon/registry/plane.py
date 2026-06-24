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
class Candidate:
    """One adapter in a plane + the metadata a policy ranks on."""
    name: str
    factory: Callable[[], object]          # () -> the adapter instance
    locality: str = "local"                # "local" | "cloud"
    keyless: bool = True                   # needs no API key?
    cost: float = 0.0                      # relative est cost (0 = free/local)
    quality: int = 1                       # quality tier (higher = better)
    probe: Callable[[], bool] | None = field(default=None)  # availability check; None = always available


def _local(c: Candidate) -> int:
    return 0 if c.locality == "local" else 1


# POLICIES: name -> sort key (ascending; the smallest key is preferred). Compose freely — adding a preference is
# adding an entry here, never editing select().
POLICIES: dict[str, Callable[[Candidate], tuple]] = {
    "local_first": lambda c: (_local(c), c.cost, -c.quality),
    "keyless_first": lambda c: (0 if c.keyless else 1, _local(c), -c.quality),
    "cheapest": lambda c: (c.cost, _local(c), -c.quality),
    "best_quality": lambda c: (-c.quality, c.cost, _local(c)),
    "fastest_local": lambda c: (_local(c), -c.quality, c.cost),
}
DEFAULT_POLICY = "local_first"


def register_policy(name: str, key: Callable[[Candidate], tuple]) -> None:
    """Add a selection preference; select() never changes."""
    POLICIES[str(name)] = key


def ranked(candidates: list[Candidate], policy: str = DEFAULT_POLICY, *, require_keyless: bool = False) -> list[Candidate]:
    """The candidates ranked by `policy` (filtered to keyless when required) — for selection + introspection."""
    pool = [c for c in candidates if c.keyless or not require_keyless]
    return sorted(pool, key=POLICIES.get(policy, POLICIES[DEFAULT_POLICY]))


def select(candidates: list[Candidate], policy: str = DEFAULT_POLICY, *, require_keyless: bool = False):
    """Rank by policy, then DESCEND to the first AVAILABLE candidate (the fallback chain). Honest: None if none
    available. This is the one selection primitive every plane uses — no per-plane best_X() wrappers."""
    for c in ranked(candidates, policy, require_keyless=require_keyless):
        if c.probe is None or c.probe():
            return c.factory()
    return None
