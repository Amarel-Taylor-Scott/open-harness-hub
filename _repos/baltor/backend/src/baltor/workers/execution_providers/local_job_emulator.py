"""_repos/baltor/backend/src/baltor/workers/execution_providers/local_job_emulator.py — RE-EXPORT SHIM (lossless extraction → Teleon, 2026-06-08). Canonical home: src.teleon.workers.*. Baltor → Teleon allowed; Teleon never imports Baltor."""
from __future__ import annotations

from src.teleon.workers.execution_providers.local_job_emulator import (  # noqa: F401
    CLOUD_RUN_JOB_ALIAS, PROVIDER_ID, LocalCloudRunJobEmulator, LocalJobEmulator)
__all__ = ["LocalJobEmulator", "LocalCloudRunJobEmulator", "PROVIDER_ID", "CLOUD_RUN_JOB_ALIAS"]
