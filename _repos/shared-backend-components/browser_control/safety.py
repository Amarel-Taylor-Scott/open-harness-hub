#!/usr/bin/env python3
"""browser_control.safety — the read-only-by-default safety rail for driver-neutral browser control.

Thin, single-source policy layer over the shipped harness (scripts.primitive_browser_control_harness). It
adds NO new secret patterns, robots logic, or a second side-effect ladder — it DELEGATES:

    * redact_fields             -> harness.redact_secrets              (the one secret-shape redactor)
    * robots_gate               -> harness.browser_respect_robots_policy (robots.txt permission, injectable fetch)
    * side_effect_*_gate        -> harness.SIDE_EFFECT_LEVELS           (the one side-effect calculus ladder)

The rules (owner spec 2026-07-08): READ-ONLY by default; an act command is REFUSED unless side effects are
explicitly enabled; even when enabled, any level >= 'write' needs explicit HUMAN confirmation (never
auto-executed); NEVER submit a form, solve/bypass a captcha, defeat a paywall, or use another user's auth
session; secrets are redacted before anything is logged or persisted.
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install  # noqa: E402

_install()

from typing import Any, Callable, Optional  # noqa: E402

from scripts.primitive_browser_control_harness import (  # noqa: E402  single source — never re-implement
    SIDE_EFFECT_LEVELS,
    browser_respect_robots_policy,
    redact_secrets,
)

#: read-only unless an operator flips it; >= this ladder index needs human confirmation even when permitted
READ_ONLY_DEFAULT = True
WRITE_THRESHOLD = "write"


def redact_fields(obj: Any, *, fields: Optional[set[str]] = None) -> tuple[Any, int]:
    """Recursively redact secret-shaped substrings in every string value (or only the named ``fields``) via the
    harness redactor. Returns ``(clean_copy, n_redacted)``; never mutates the input. Apply before ANY log/persist."""
    total = 0

    def _walk(value: Any, key: Optional[str]) -> Any:
        nonlocal total
        if isinstance(value, str):
            if fields is None or (key is not None and key in fields):
                clean, n = redact_secrets(value)
                total += n
                return clean
            return value
        if isinstance(value, dict):
            return {k: _walk(v, k) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [_walk(v, key) for v in value]
        return value

    return _walk(obj, None), total


def robots_gate(url: str, *, fetch: Optional[Callable[[str], Optional[str]]] = None,
                ua: Optional[str] = None) -> bool:
    """True iff robots.txt permits fetching ``url`` — delegates to the harness policy. ``fetch`` is injectable for
    offline tests; absent/unreadable robots ⇒ allowed (standard crawler convention)."""
    kw: dict[str, Any] = {}
    if ua:
        kw["ua"] = ua
    return browser_respect_robots_policy(url, fetch=fetch, **kw)


def side_effect_confirmation_gate(level: str, *, allow_side_effects: bool = False,
                                  confirmed: bool = False) -> dict[str, Any]:
    """The side-effect calculus over SIDE_EFFECT_LEVELS (single source). Returns a DECISION dict — it never executes
    anything. read-only by default; >= 'write' needs explicit human confirmation even when side effects are allowed.

        {execute: bool, requires_confirmation: bool, verdict: str, level: str, reason: str}
    """
    if level not in SIDE_EFFECT_LEVELS:
        return {"execute": False, "requires_confirmation": True, "verdict": "invalid_level", "level": level,
                "reason": f"unknown side_effect_level {level!r}; expected one of {list(SIDE_EFFECT_LEVELS)}"}
    if not allow_side_effects:
        return {"execute": False, "requires_confirmation": True, "verdict": "refused_read_only", "level": level,
                "reason": "read-only policy: side effects are disabled for this session"}
    needs = SIDE_EFFECT_LEVELS.index(level) >= SIDE_EFFECT_LEVELS.index(WRITE_THRESHOLD)
    if needs and not confirmed:
        return {"execute": False, "requires_confirmation": True, "verdict": "gated_pending_confirmation",
                "level": level, "reason": f"{level} >= {WRITE_THRESHOLD}: explicit human confirmation required"}
    return {"execute": True, "requires_confirmation": needs, "level": level,
            "verdict": "gated_confirmed_execute" if needs else "gated_executed", "reason": ""}


class ReadOnlyPolicy:
    """A read-only-by-default policy object an adapter consults before any act command. ``confirm(level, input)``
    is the human-in-the-loop hook — it is only ever called when side effects are enabled, and a falsy return keeps
    a write gated. The default policy is fully read-only and confirms nothing."""

    def __init__(self, *, allow_side_effects: bool = not READ_ONLY_DEFAULT,
                 confirm: Optional[Callable[[str, dict], bool]] = None) -> None:
        self.allow_side_effects = bool(allow_side_effects)
        self._confirm = confirm or (lambda level, inp: False)

    def evaluate(self, level: str, inp: Optional[dict] = None) -> dict[str, Any]:
        confirmed = bool(self._confirm(level, inp or {})) if self.allow_side_effects else False
        return side_effect_confirmation_gate(level, allow_side_effects=self.allow_side_effects, confirmed=confirmed)


__all__ = ["READ_ONLY_DEFAULT", "WRITE_THRESHOLD", "SIDE_EFFECT_LEVELS", "redact_fields", "robots_gate",
           "side_effect_confirmation_gate", "ReadOnlyPolicy"]
