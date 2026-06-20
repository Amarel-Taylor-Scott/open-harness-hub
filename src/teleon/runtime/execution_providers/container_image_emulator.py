"""src.teleon.runtime.execution_providers.container_image_emulator — the local equivalent for a
Docker/container-image task. If Docker is approved + available a candidate Docker provider could run; when
it is not (the default offline case), it FALLS BACK to the managed-venv runner so a container-style task is
never blocked. No privileged mounts, no secrets; same ExecutionResult contract.

Canonical TELEON home (runtime layer); imports its sibling from Teleon (never Baltor). Baltor re-exports this
via a shim at src/baltor/workers/execution_providers/container_image_emulator.py.
"""
from __future__ import annotations

from src.teleon.runtime.execution_providers.managed_venv import ManagedVenvProvider

PROVIDER_ID = "execution.container_image_emulator@v1"


class ContainerImageEmulator:
    provider_id = PROVIDER_ID

    def __init__(self, *, docker_available: bool = False, docker_approved: bool = False) -> None:
        self.docker_available = docker_available
        self.docker_approved = docker_approved
        self._venv = ManagedVenvProvider()

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "kind": "container_image", "owns_truth": False,
                "fallback": "execution.managed_venv@v1", "docker": "candidate (approval required)"}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": True, "via": "managed_venv fallback"}

    def run(self, *, image: str, command: list[str], cache_key: str | None = None, task_id: str = "ci-task",
            timeout_s: int = 20) -> dict:
        """Run a container-style command. Docker stays CANDIDATE; offline → managed-venv fallback."""
        used = "managed_venv_fallback"
        if self.docker_available and self.docker_approved:
            # real Docker is a candidate requiring owner approval — not invoked here.
            used = "docker_candidate_skipped_pending_approval"
        res = self._venv.run(cache_key=cache_key or f"ci-{image}", argv=command, task_id=task_id, timeout_s=timeout_s)
        return {"provider_id": self.provider_id, "image": image, "backend_used": used,
                "status": res.status, "is_truth": False, "detail": res.detail}


__all__ = ["ContainerImageEmulator", "PROVIDER_ID"]
