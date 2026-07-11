"""src.baltor.ports.execution_provider — RE-EXPORT SHIM (lossless extraction → Teleon).

The EXECUTION BACKEND port now lives in its canonical Teleon home, ``src.teleon.runtime.execution_provider`` —
HOW a CapabilityTask runs is a Teleon runtime concern (_repos/shared-backend-components/architecture/portfolio_dependency_law.json migration_status,
extraction step 1: the runtime layer is the lowest, extracted first). This shim re-exports it so every existing
``from src.baltor.ports.execution_provider import …`` keeps working with NO duplicate runtime and NO broken import.

Baltor → Teleon is the allowed dependency direction (the holding-company law: Baltor → Teleon → OpenHubForAI,
never the reverse); Teleon never imports Baltor. When all callers import from Teleon directly, this shim can retire.
"""
from __future__ import annotations

from src.teleon.runtime.execution_provider import (
    py_class_src_teleon_runtime_execution_provider__ExecutionProviderPort,
    py_class_src_teleon_runtime_execution_provider__ExecutionResult,
    py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult,
)

__all__ = ["py_class_src_teleon_runtime_execution_provider__ExecutionProviderPort", "py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult", "py_class_src_teleon_runtime_execution_provider__ExecutionResult"]
