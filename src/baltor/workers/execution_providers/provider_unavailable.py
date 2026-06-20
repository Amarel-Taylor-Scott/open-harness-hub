"""src.baltor.workers.execution_providers.provider_unavailable — RE-EXPORT SHIM (lossless extraction → Teleon).

The unavailable-sentinel provider now lives in its canonical Teleon home
``src.teleon.runtime.execution_providers.provider_unavailable`` (runtime layer; architecture/
portfolio_dependency_law.json migration_status). This shim re-exports it so callers + proofs keep working with NO
duplicate runtime. Baltor → Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.runtime.execution_providers.provider_unavailable import PROVIDER_ID, ProviderUnavailable

__all__ = ["ProviderUnavailable", "PROVIDER_ID"]
