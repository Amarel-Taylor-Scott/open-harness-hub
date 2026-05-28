#!/usr/bin/env python3
"""Back-compat shim — the showcase is now the modular `scripts/showcase/` package.

Kept so `python3 -m scripts.serve_builder` (and serve_showcase.sh) keep working.
New code should import from `scripts.showcase`.
"""
from __future__ import annotations

from scripts.showcase import Index, build_flow, export_flow, main, serve  # noqa: F401

if __name__ == "__main__":
    raise SystemExit(main())
