"""src.teleon.training.capability_network — the cross-capability NETWORK GRAPH + per-capability metadata profile.

Each capability already has a per-capability EVOLUTION graph (its non-det -> det distillation lineage). THIS is
the other graph the owner asked for: the relationships BETWEEN capabilities, so models/harnesses learn distillation
from STRUCTURE, not just per-item features:
  * alternative_of — capabilities that serve the same need via different providers (same category + similar
    intent). These ARE the endpoint sets: a dense alternative-cluster means provider-selection matters and a
    deterministic wrapper can front many providers at once.
  * composability — a capability's category has downstream categories it can feed (scraping -> data-extraction ->
    document -> research): the pipeline structure, captured as a per-capability feature (how many downstream
    capabilities exist), not an O(n^2) edge explosion.
  * neighborhood — category size, source family.
The per-capability PROFILE (metadata + graph features) extends the skills-DB feature vector, so the trained policy
learns e.g. 'high-alternative, high-composability deterministic-library capabilities distill cheapest'.

Deterministic (no clock/RNG/LLM); Teleon-layer — never imports src.baltor; a profile/edge is metadata, never truth.
NOTE: alternative clustering is within-category pairwise; at 100k+ scale do it per-category with blocking/LSH.
"""
from __future__ import annotations

import re

EDGE_ALTERNATIVE = "alternative_of"

#: intent stopwords stripped before similarity (generic verbs/nouns that don't identify the need).
_STOP = {"a", "an", "the", "of", "to", "for", "and", "or", "with", "by", "from", "data", "get", "fetch",
         "via", "into", "on", "in", "using", "use", "create", "run", "return", "list", "search", "query", "this"}
_ALT_JACCARD = 0.34  # within-category intent overlap above which two capabilities are alternatives (endpoint peers)

#: category pipeline adjacency (upstream -> downstream categories it can feed) — the composability structure.
_PIPELINE_ADJACENCY = {
    "scraping": ("data-extraction", "document", "research"),
    "data-extraction": ("database", "document", "research", "market-data", "financial-data"),
    "document": ("research", "data-extraction"),
    "database": ("data-extraction", "research"),
    "research": ("document",),
    "media": ("document", "data-extraction"),
    "messaging": ("productivity",),
    "email": ("productivity",),
    "geo-weather": ("research", "data-extraction"),
    "scientific-data": ("research",),
    "financial-data": ("research", "market-data"),
    "market-data": ("research",),
    "identity-compliance": ("regulation",),
}


def _tokens(intent: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", (intent or "").lower()) if w not in _STOP and len(w) > 2}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class CapabilityNetwork:
    """The relationship graph over a capability corpus + per-capability profiles/features for training."""

    def __init__(self) -> None:
        self._cap: dict[str, dict] = {}        # slot -> {category, source_kind, tokens, ...}
        self._alt: dict[str, set] = {}         # slot -> set of alternative slots
        self._by_category: dict[str, list] = {}

    def build(self, candidates: list[dict]) -> "CapabilityNetwork":
        for c in candidates:
            slot = c["capability_slot"]
            src = c.get("source") if isinstance(c.get("source"), dict) else {}
            self._cap[slot] = {"category": c.get("category", "other"),
                               "source_kind": src.get("kind") or c.get("source_kind", "other"),
                               "tokens": _tokens(c.get("intent", "")), "slot": slot}
            self._by_category.setdefault(c.get("category", "other"), []).append(slot)
        # alternative_of: within each category, pairs whose intent overlap clears the threshold (the endpoint sets).
        for slots in self._by_category.values():
            for i in range(len(slots)):
                ti = self._cap[slots[i]]["tokens"]
                for j in range(i + 1, len(slots)):
                    if _jaccard(ti, self._cap[slots[j]]["tokens"]) >= _ALT_JACCARD:
                        self._alt.setdefault(slots[i], set()).add(slots[j])
                        self._alt.setdefault(slots[j], set()).add(slots[i])
        return self

    def alternatives(self, slot: str) -> list[str]:
        """The capability's endpoint-set peers (same need, different provider)."""
        return sorted(self._alt.get(slot, set()))

    def downstream_categories(self, slot: str) -> list[str]:
        return list(_PIPELINE_ADJACENCY.get(self._cap[slot]["category"], ()))

    def _downstream_capability_count(self, slot: str) -> int:
        return sum(len(self._by_category.get(dc, [])) for dc in self.downstream_categories(slot))

    def profile(self, slot: str) -> dict:
        """Per-capability metadata + graph position — the 'map' for one capability (alongside its evolution lineage)."""
        if slot not in self._cap:
            raise KeyError(f"unknown capability {slot!r}")
        c = self._cap[slot]
        alts = self.alternatives(slot)
        return {"capability_slot": slot, "category": c["category"], "source_kind": c["source_kind"],
                "alternatives": alts, "n_alternatives": len(alts),
                "category_size": len(self._by_category.get(c["category"], [])),
                "downstream_categories": self.downstream_categories(slot),
                "downstream_capability_count": self._downstream_capability_count(slot), "serves_truth": False}

    def network_features(self, slot: str) -> dict:
        """Numeric graph features to EXTEND the skills-DB feature vector (what the policy learns structure from)."""
        p = self.profile(slot)
        return {"n_alternatives": p["n_alternatives"], "has_alternatives": 1 if p["n_alternatives"] else 0,
                "category_size": p["category_size"], "downstream_capability_count": p["downstream_capability_count"],
                "is_composable": 1 if p["downstream_capability_count"] else 0}

    def summary(self) -> dict:
        clusters = sum(1 for s in self._cap if self._alt.get(s))
        return {"capabilities": len(self._cap), "with_alternatives": clusters,
                "categories": len(self._by_category), "serves_truth": False}


def enrich_features(candidate: dict, network: CapabilityNetwork) -> dict:
    """The skills-DB feature vector + the capability's network features — the richer training signal. Keeps
    skills_db.feature_vector unchanged; callers opt in to the structural features."""
    from src.teleon.training.skills_db import feature_vector
    base = feature_vector(candidate)
    base.update(network.network_features(candidate["capability_slot"]))
    return base
