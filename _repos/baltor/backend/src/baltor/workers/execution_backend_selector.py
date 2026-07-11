"""src.baltor.workers.execution_backend_selector — RE-EXPORT SHIM (lossless extraction → Teleon).

Execution-backend SELECTION is a Teleon runtime concern; it now lives in its canonical home
``src.teleon.runtime.execution_backend_selector`` (_repos/shared-backend-components/architecture/portfolio_dependency_law.json migration_status,
extraction step 1 — the runtime layer). This shim re-exports it so every existing
``from src.baltor.workers.execution_backend_selector import …`` keeps working with NO duplicate runtime.

Baltor → Teleon is the allowed dependency direction (Baltor → Teleon → OpenHubForAI, never the reverse);
Teleon never imports Baltor. When all callers import from Teleon directly, this shim can retire.
"""
from __future__ import annotations

from src.teleon.runtime.execution_backend_selector import (
    py_const_src_teleon_runtime_execution_backend_selector__ACTIONS,
    py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS,
    py_function_src_teleon_runtime_execution_backend_selector__generic_functions,
    py_function_src_teleon_runtime_execution_backend_selector__select_backend,
)

__all__ = ["py_function_src_teleon_runtime_execution_backend_selector__select_backend", "py_const_src_teleon_runtime_execution_backend_selector__GENERIC_FUNCTIONS", "py_function_src_teleon_runtime_execution_backend_selector__generic_functions", "py_const_src_teleon_runtime_execution_backend_selector__ACTIONS"]
