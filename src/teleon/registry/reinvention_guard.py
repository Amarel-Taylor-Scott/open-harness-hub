"""registry.reinvention_guard — the 'you're reinventing a solved problem' guardrail, GROUNDED in the federation.

The regression-to-the-mean guardrail as a product (owner idea 2026-06-23). The hard part everyone identifies is the
GROUNDING — knowing a solution already exists, reliably enough to interrupt. That grounding is the registry
federation (search_all over the component/capability registries). The tiered cascade keeps it cheap + precise:

  Tier 0 (heuristic, ~free):  detect build-intent ("let me write / implement / build a X from scratch") + extract X.
  Tier 1 (cheap gate):         is X in a known SOLVED domain? (deterministic floor now; a cheap/local model later.)
  Tier 2 (GROUNDED, the moat):  search_all(X) over the federation -> if real components/capabilities exist, FIRE.

PRECISION DISCIPLINE: fires ONLY when Tier 2 finds grounded matches (silent on genuinely-novel work — the tails are
where new value lives). This is the descent thesis as a product: don't regenerate what already exists. The economic
win is the avoided rebuild + its debug/retry trajectory, not the monitor's own tokens. serves_truth=false.
"""
from __future__ import annotations

import re

from .search import search_all

# Tier 0: build-intent tells + famously-solved domains (the keyword gate that wakes Tier 2).
_INTENT_TELLS = ("let me write", "let me build", "let me implement", "i'll write", "i'll implement", "i'll build",
                 "build a ", "write a ", "implement a ", "from scratch", "roll my own", "my own", "create a ")
_SOLVED_DOMAINS = ("auth", "oauth", "jwt", "login", "date", "parse", "parser", "csv", "json", "xml", "rate limit",
                   "retry", "backoff", "ocr", "pdf", "email", "validation", "regex", "encryption", "hashing",
                   "logging", "cache", "queue", "scheduler", "geocode", "address", "sanctions", "embedding",
                   "vector", "weather", "license", "search", "extract")
_TOP = 5


def detect_intent(message: str) -> dict:
    """Tier 0 — is this build-intent, and what solved-domain is it about? (no model, near-zero cost)."""
    msg = (message or "").lower()
    intent = any(t in msg for t in _INTENT_TELLS)
    domains = sorted({d for d in _SOLVED_DOMAINS if re.search(rf"\b{re.escape(d)}", msg)})
    return {"build_intent": intent, "candidate_domains": domains}


def check(message: str) -> dict:
    """The cascade. Returns a notice ONLY when a solution is GROUNDED in the federation (else stays quiet)."""
    t0 = detect_intent(message)
    if not t0["build_intent"]:
        return {"fire": False, "tier": 0, "reason": "no build intent"}
    if not t0["candidate_domains"]:
        return {"fire": False, "tier": 1, "reason": "no solved-domain signal — may be genuinely novel, let it build"}
    # Tier 2: ground each candidate against the registries (this is the precision/moat step)
    grounded: dict[str, list[dict]] = {}
    for domain in t0["candidate_domains"]:
        hits = search_all(domain)
        if hits:
            grounded[domain] = [{"registry": h["registry"], "name": h["name"]} for h in hits[:_TOP]]
    if not grounded:
        return {"fire": False, "tier": 2, "reason": "nothing in the federation — likely genuinely novel, build it"}
    return {
        "fire": True, "tier": 2,
        "notice": "This looks like a solved problem — these already exist in the registry federation, "
                  "don't reinvent them:",
        "existing": grounded,
        "grounded_in": "registry.search_all over the component/capability registries",
        "saves": "the whole rebuild + its debug/retry trajectory (the descent thesis: deterministic > probabilistic)",
        "serves_truth": False,
    }
