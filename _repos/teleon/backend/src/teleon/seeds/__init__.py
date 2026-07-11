"""src.teleon.seeds — governed CAPABILITY SEEDS distilled from externally-reviewed repos.

A seed is what we LEARNED from a repo turned into our own clean-room, governed capability: drop-in where the
license permits, technique-borrowed where it does not. Every seed runs real (no placeholder) logic, records the
`lesson` taken from the source, and NEVER serves truth (its output is a candidate). Discovery is not trust —
a seed is a proposal that must still pass the gap/lift + human/eval gates before promotion.
"""
from src.teleon.seeds.capability_seed import CapabilitySeed, SeedResult, all_seeds, register, seeds_for_source

__all__ = ["CapabilitySeed", "SeedResult", "all_seeds", "register", "seeds_for_source"]
