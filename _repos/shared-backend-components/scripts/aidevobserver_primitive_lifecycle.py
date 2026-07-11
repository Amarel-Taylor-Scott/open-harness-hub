#!/usr/bin/env python3
"""Compatibility wrapper for the global primitive source lifecycle.

AIDevObserver contributes source candidates and review signals, but primitive
digesting, implementation backlog creation, summaries, and vector rows are
ecosystem-wide concerns. Use `_repos/shared-backend-components/scripts/primitive_source_lifecycle.py` directly
for new automation.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.primitive_source_lifecycle import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
