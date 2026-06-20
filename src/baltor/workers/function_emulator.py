"""src/baltor/workers/function_emulator.py — RE-EXPORT SHIM (lossless extraction → Teleon, 2026-06-08). Canonical home: src.teleon.workers.*. Baltor → Teleon allowed; Teleon never imports Baltor."""
from __future__ import annotations

from src.teleon.workers.function_emulator import LocalFunctionEmulator, _echo_handler  # noqa: F401
__all__ = ["LocalFunctionEmulator"]
