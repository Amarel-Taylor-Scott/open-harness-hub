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

from .search import py_function_src_teleon_registry_search__search_all

# Tier 0: build-intent tells + famously-solved domains (the keyword gate that wakes Tier 2).
py_var_src_teleon_registry_reinvention_guard___INTENT_TELLS = ("let me write", "let me build", "let me implement", "i'll write", "i'll implement", "i'll build",
                 "build a ", "write a ", "implement a ", "from scratch", "roll my own", "my own", "create a ")
py_var_src_teleon_registry_reinvention_guard___SOLVED_DOMAINS = ("auth", "oauth", "jwt", "login", "date", "parse", "parser", "csv", "json", "xml", "rate limit",
                   "retry", "backoff", "ocr", "pdf", "email", "validation", "regex", "encryption", "hashing",
                   "logging", "cache", "queue", "scheduler", "geocode", "address", "sanctions", "embedding",
                   "vector", "weather", "license", "search", "extract",
                   # multi-path / routing already built in-house (path_selection_policy + run_path_bakeoff +
                   # parallel_paths + foundry/model_route + OIPS); ChronoRouter/VariantGraph are our OWN thesis
                   # renamed — flag these so agents wrap the existing engine instead of rebuilding it (ADR 0012).
                   "model router", "model routing", "llm router", "path selection", "path selector",
                   "variant graph", "temporal routing", "solution graph", "multi-path", "route selection")
py_var_src_teleon_registry_reinvention_guard___TOP = 5


def py_function_src_teleon_registry_reinvention_guard__detect_intent(py_arg_src_teleon_registry_reinvention_guard__py_function_src_teleon_registry_reinvention_guard__detect_intent__message: str) -> dict:
    """Tier 0 — is this build-intent, and what solved-domain is it about? (no model, near-zero cost)."""
    py_local_src_teleon_registry_reinvention_guard__detect_intent__msg = (py_arg_src_teleon_registry_reinvention_guard__py_function_src_teleon_registry_reinvention_guard__detect_intent__message or "").lower()
    py_local_src_teleon_registry_reinvention_guard__detect_intent__intent = any(t in py_local_src_teleon_registry_reinvention_guard__detect_intent__msg for t in py_var_src_teleon_registry_reinvention_guard___INTENT_TELLS)
    py_local_src_teleon_registry_reinvention_guard__detect_intent__domains = sorted({d for d in py_var_src_teleon_registry_reinvention_guard___SOLVED_DOMAINS if re.search(rf"\b{re.escape(d)}", py_local_src_teleon_registry_reinvention_guard__detect_intent__msg)})
    return {"build_intent": py_local_src_teleon_registry_reinvention_guard__detect_intent__intent, "candidate_domains": py_local_src_teleon_registry_reinvention_guard__detect_intent__domains}


def py_function_src_teleon_registry_reinvention_guard__check(py_arg_src_teleon_registry_reinvention_guard__py_function_src_teleon_registry_reinvention_guard__check__message: str) -> dict:
    """The cascade. Returns a notice ONLY when a solution is GROUNDED in the federation (else stays quiet)."""
    py_local_src_teleon_registry_reinvention_guard__check__t0 = py_function_src_teleon_registry_reinvention_guard__detect_intent(py_arg_src_teleon_registry_reinvention_guard__py_function_src_teleon_registry_reinvention_guard__check__message)
    if not py_local_src_teleon_registry_reinvention_guard__check__t0["build_intent"]:
        return {"fire": False, "tier": 0, "reason": "no build intent"}
    if not py_local_src_teleon_registry_reinvention_guard__check__t0["candidate_domains"]:
        return {"fire": False, "tier": 1, "reason": "no solved-domain signal — may be genuinely novel, let it build"}
    # Tier 2: ground each candidate against the registries (this is the precision/moat step)
    py_local_src_teleon_registry_reinvention_guard__check__grounded: dict[str, list[dict]] = {}
    for py_local_src_teleon_registry_reinvention_guard__check__domain in py_local_src_teleon_registry_reinvention_guard__check__t0["candidate_domains"]:
        py_local_src_teleon_registry_reinvention_guard__check__hits = py_function_src_teleon_registry_search__search_all(py_local_src_teleon_registry_reinvention_guard__check__domain)
        if py_local_src_teleon_registry_reinvention_guard__check__hits:
            py_local_src_teleon_registry_reinvention_guard__check__grounded[py_local_src_teleon_registry_reinvention_guard__check__domain] = [{"registry": h["registry"], "name": h["name"]} for h in py_local_src_teleon_registry_reinvention_guard__check__hits[:py_var_src_teleon_registry_reinvention_guard___TOP]]
    if not py_local_src_teleon_registry_reinvention_guard__check__grounded:
        return {"fire": False, "tier": 2, "reason": "nothing in the federation — likely genuinely novel, build it"}
    return {
        "fire": True, "tier": 2,
        "notice": "This matches known capability in the registry federation. Reuse or compare these before building:",
        "existing": py_local_src_teleon_registry_reinvention_guard__check__grounded,
        "grounded_in": "registry.search_all over the component/capability registries",
        "saves": "the whole rebuild + its debug/retry trajectory (the descent thesis: deterministic > probabilistic)",
        "serves_truth": False,
    }
