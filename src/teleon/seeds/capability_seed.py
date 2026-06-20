"""src.teleon.seeds.capability_seed — the CapabilitySeed framework: turn a lesson learned from an external repo
into a governed, runnable capability candidate.

A seed binds (a) WHAT we learned (`lesson`) from a source repo, (b) whether it is drop-in (clean permissive
license) or technique-only (copyleft/unstated/proprietary → clean-room, never vendor the code), and (c) a real
clean-room `runner` that produces a CANDIDATE result. ``run`` always forces serves_truth=False — a seed proposes,
it never disposes. ``as_purpose_task_candidate`` emits a PurposeTask-spec-shaped dict so the seed plugs into the
normal capability pipeline (gap/lift screen → eval gate → promotion). Pure + deterministic framework.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

#: license tokens that forbid vendoring the source code → a seed must be technique-only (drop_in=False).
#: includes copyleft (GPL family), NonCommercial/NoDerivatives CC (by-nc / nc-nd), and source-available
#: (BSL / Elastic v2 / "source-available") — none are clean-permissive, so none may be vendored.
_NON_VENDORABLE = ("agpl", "gpl", "lgpl", "proprietary", "private", "by-nc", "nc-nd", "bsl", "elv2",
                   "source-available", "unstated", "n/a", "")


def vendorable(license_: str) -> bool:
    """True only for clean permissive licenses (MIT/Apache/BSD/ISC/CC0...). Copyleft/unstated/proprietary → False."""
    lic = (license_ or "").strip().lower()
    return not any(tok and tok in lic or lic == tok for tok in _NON_VENDORABLE)


@dataclass(frozen=True)
class SeedResult:
    output: Any
    provenance: str = ""
    serves_truth: bool = False  # a seed result is a candidate; the framework re-forces this on run()


@dataclass(frozen=True)
class CapabilitySeed:
    slot: str
    intent: str
    learned_from: str            # source repo (owner/name) or service
    source_license: str
    lesson: str                  # the technique/pattern we took (the point of "learn from them")
    runner: Callable[[Any], SeedResult]
    determinism_ceiling: float = 1.0
    adoptable: bool = True        # an adoptable governed candidate (vs foil / commodity / out-of-scope)
    category: str = "other"
    drop_in: bool | None = None   # None → inferred from the license (vendorable). Explicit False = clean-room only.

    def is_drop_in(self) -> bool:
        return vendorable(self.source_license) if self.drop_in is None else bool(self.drop_in)

    def run(self, payload: Any = None) -> dict:
        """Run the clean-room logic. serves_truth is ALWAYS False — the framework refuses to let a seed serve truth."""
        r = self.runner(payload)
        return {"slot": self.slot, "output": r.output, "provenance": r.provenance, "serves_truth": False,
                "learned_from": self.learned_from, "drop_in": self.is_drop_in(), "adoptable": self.adoptable}

    def as_purpose_task_candidate(self) -> dict:
        """A PurposeTask-spec-shaped CANDIDATE dict (round-trips through PurposeTaskSpec) for the normal pipeline."""
        return {
            "task_id": f"seed-{self.slot}", "capability_slot": self.slot, "intent": self.intent,
            "category": self.category, "candidate": True, "serves_truth": False,
            "learned_from": self.learned_from, "source_license": self.source_license,
            "drop_in": self.is_drop_in(), "adoptable": self.adoptable,
            "determinism_ceiling": self.determinism_ceiling, "lesson": self.lesson,
        }


_REGISTRY: list[CapabilitySeed] = []


def register(seed: CapabilitySeed) -> CapabilitySeed:
    """Register a seed (idempotent on slot — a re-registered slot replaces the prior)."""
    global _REGISTRY
    _REGISTRY = [s for s in _REGISTRY if s.slot != seed.slot] + [seed]
    return seed


def all_seeds() -> list[CapabilitySeed]:
    # import the seed packs so registration happens on first access (deterministic order by slot)
    from src.teleon.seeds import api_and_feed_seeds, github_signal_seeds  # noqa: F401
    return sorted(_REGISTRY, key=lambda s: s.slot)


def seeds_for_source(source_substr: str) -> list[CapabilitySeed]:
    return [s for s in all_seeds() if source_substr.lower() in s.learned_from.lower()]
