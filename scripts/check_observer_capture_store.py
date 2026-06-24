"""check_observer_capture_store — proof for the capture seam (observer.capture) + the session model / accept-reject
outcome loop (observer.session_store). Delegates to each module's self-test (both relative-import packages, so they
need this top-level wrapper). serves_truth=false.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.observer import capture, session_store  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    rc = capture._self_test() | session_store._self_test()  # 0 only if BOTH return 0
    return rc


if __name__ == "__main__":
    sys.exit(main())
