"""src.teleon.runtime — Teleon runtime layer (the LOWEST extraction layer per the dependency law).

HOW a CapabilityTask runs — the execution-backend port + (incrementally) runtime selection and adapters — lives
here, in Teleon. Generic runtime code is being extracted _repos/baltor/backend/src/baltor → src/teleon one module at a time, losslessly,
with _repos/baltor/backend/src/baltor shims re-exporting so callers + proofs stay green and there is no duplicate runtime
(_repos/shared-backend-components/architecture/portfolio_dependency_law.json migration_status). Teleon never imports Baltor.
"""
from src.teleon.runtime.execution_provider import (
    py_class_src_teleon_runtime_execution_provider__ExecutionProviderPort,
    py_class_src_teleon_runtime_execution_provider__ExecutionResult,
    py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult,
)

__all__ = ["py_class_src_teleon_runtime_execution_provider__ExecutionProviderPort", "py_class_src_teleon_runtime_execution_provider__ProviderUnavailableResult", "py_class_src_teleon_runtime_execution_provider__ExecutionResult"]
