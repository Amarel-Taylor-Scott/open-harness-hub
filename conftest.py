"""Root conftest — puts every code root on sys.path for pytest and any tool that loads conftest, so imports
of MOVED packages (src.<x> now under _repos/<x>/backend/) resolve without rewriting a single import.

Single source of the path list: scripts/_repo_paths.py (also used by scripts/run_proofs.py). No magic paths here.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # ensure the repo root is importable first
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()
