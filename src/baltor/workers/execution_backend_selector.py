"""src.baltor.workers.execution_backend_selector — RE-EXPORT SHIM (lossless extraction → Teleon).

Execution-backend SELECTION is a Teleon runtime concern; it now lives in its canonical home
``src.teleon.runtime.execution_backend_selector`` (architecture/portfolio_dependency_law.json migration_status,
extraction step 1 — the runtime layer). This shim re-exports it so every existing
``from src.baltor.workers.execution_backend_selector import …`` keeps working with NO duplicate runtime.

Baltor → Teleon is the allowed dependency direction (Baltor → Teleon → OpenHarnessHub, never the reverse);
Teleon never imports Baltor. When all callers import from Teleon directly, this shim can retire.
"""
from __future__ import annotations

from src.teleon.runtime.execution_backend_selector import (
    ACTIONS,
    GENERIC_FUNCTIONS,
    generic_functions,
    select_backend,
)

__all__ = ["select_backend", "GENERIC_FUNCTIONS", "generic_functions", "ACTIONS"]
