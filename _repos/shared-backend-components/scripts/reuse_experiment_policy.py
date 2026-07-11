#!/usr/bin/env python3
"""Single-source policy constants for the candidate reuse experiments.

This module deliberately contains no experiment implementation imports, so the
standalone harnesses and the grid can share reporting/coordination policy
without creating circular dependencies.
"""
from __future__ import annotations


REPORTING_MIN_N = 8
DEFAULT_LIVE_REPEATS = REPORTING_MIN_N + 2

# The owner-coordination protocol reserves OpenRouter key indices 24-28 for
# Claude/Fable while agents run concurrently.  Codex uses the leading slice.
CODEX_OPENROUTER_KEY_COUNT = 24
