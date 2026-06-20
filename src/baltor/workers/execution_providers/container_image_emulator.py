"""src.baltor.workers.execution_providers.container_image_emulator — RE-EXPORT SHIM (lossless extraction → Teleon).

The container-image local emulator now lives in its canonical Teleon home
``src.teleon.runtime.execution_providers.container_image_emulator`` (runtime layer; architecture/
portfolio_dependency_law.json migration_status). This shim re-exports it so callers + proofs keep working with NO
duplicate runtime. Baltor → Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.runtime.execution_providers.container_image_emulator import PROVIDER_ID, ContainerImageEmulator

__all__ = ["ContainerImageEmulator", "PROVIDER_ID"]
