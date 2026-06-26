"""check_observer_agentic — proof wrapper for agentic-loop supervision (src/teleon/observer/agentic.py).

The supervisor lives in the package (relative imports over the router), so it can't run as a bare script path;
this top-level wrapper bootstraps sys.path and delegates to its self-test. Run with --self-test (gate convention).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.observer.agentic import _self_test  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    return _self_test()


if __name__ == "__main__":
    sys.exit(main())
