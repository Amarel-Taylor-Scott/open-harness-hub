"""src.baltor.workers.execution_providers.managed_venv — RE-EXPORT SHIM (lossless extraction → Teleon).

The managed-venv local execution provider now lives in its canonical Teleon home
``src.teleon.runtime.execution_providers.managed_venv`` (runtime layer; architecture/
portfolio_dependency_law.json migration_status). This shim re-exports it so callers + proofs keep working with NO
duplicate runtime. Baltor → Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.runtime.execution_providers.managed_venv import PROVIDER_ID, ManagedVenvProvider

__all__ = ["ManagedVenvProvider", "PROVIDER_ID"]
