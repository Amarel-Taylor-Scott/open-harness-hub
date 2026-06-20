"""src.teleon.runtime — Teleon runtime layer (the LOWEST extraction layer per the dependency law).

HOW a CapabilityTask runs — the execution-backend port + (incrementally) runtime selection and adapters — lives
here, in Teleon. Generic runtime code is being extracted src/baltor → src/teleon one module at a time, losslessly,
with src/baltor shims re-exporting so callers + proofs stay green and there is no duplicate runtime
(architecture/portfolio_dependency_law.json migration_status). Teleon never imports Baltor.
"""
from src.teleon.runtime.execution_provider import (
    ExecutionProviderPort,
    ExecutionResult,
    ProviderUnavailableResult,
)

__all__ = ["ExecutionProviderPort", "ProviderUnavailableResult", "ExecutionResult"]
