"""src.baltor.workers.execution_providers.container_image_emulator — RE-EXPORT SHIM (lossless extraction → Teleon).

The container-image local emulator now lives in its canonical Teleon home
``src.teleon.runtime.execution_providers.container_image_emulator`` (runtime layer; _repos/shared-backend-components/architecture/
portfolio_dependency_law.json migration_status). This shim re-exports it so callers + proofs keep working with NO
duplicate runtime. Baltor → Teleon is the allowed direction; Teleon never imports Baltor.
"""
from __future__ import annotations

from src.teleon.runtime.execution_providers.container_image_emulator import py_const_src_teleon_runtime_execution_providers_container_image_emulator__PROVIDER_ID, py_class_src_teleon_runtime_execution_providers_container_image_emulator__ContainerImageEmulator

__all__ = ["py_class_src_teleon_runtime_execution_providers_container_image_emulator__ContainerImageEmulator", "py_const_src_teleon_runtime_execution_providers_container_image_emulator__PROVIDER_ID"]
