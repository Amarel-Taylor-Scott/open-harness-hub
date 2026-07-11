"""check_observer_agentic — proof wrapper for agentic-loop supervision (_repos/teleon/backend/src/teleon/observer/agentic.py).

The supervisor lives in the package (relative imports over the router), so it can't run as a bare script path;
this top-level wrapper bootstraps sys.path and delegates to its self-test. Run with --self-test (gate convention).
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# install() prepends every code root so BOTH `scripts.*` and the MOVED `src.teleon.*` resolve on a bare
# `python3 scripts/<f>.py` launch — not only under run_proofs/pytest (which set the full PYTHONPATH for us).
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_here_boot = _Path(__file__).resolve()
_sbc_boot = next((p for p in _here_boot.parents if (p / "scripts" / "_repo_paths.py").exists()), _here_boot.parents[1])
if str(_sbc_boot) not in _sys.path:
    _sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
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
