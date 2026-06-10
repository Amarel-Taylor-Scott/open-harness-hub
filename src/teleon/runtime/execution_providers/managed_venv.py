"""src.teleon.runtime.execution_providers.managed_venv — run container/image/function-style tasks LOCALLY
without Docker or cloud. The local equivalent for container-image / function execution. Creates a cache
dir under .agent/venvs/<key>/, runs the entrypoint as a bounded subprocess, captures stdout/stderr,
enforces a timeout, returns a structured ExecutionResult (never truth). NEVER global pip / sudo / apt /
brew / docker. The task still requires an atomic claim — the venv runner is given a reference, not ownership.

Canonical TELEON home (runtime layer); imports the port from Teleon (never Baltor). Baltor re-exports this via
a shim at src/baltor/workers/execution_providers/managed_venv.py.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from src.teleon.runtime.execution_provider import ExecutionResult

_REPO = Path(__file__).resolve().parents[4]
_VENVS = _REPO / ".agent" / "venvs"
PROVIDER_ID = "execution.managed_venv@v1"


class ManagedVenvProvider:
    provider_id = PROVIDER_ID

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "kind": "managed_venv", "owns_truth": False,
                "no_docker": True, "no_global_pip": True, "no_sudo": True}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": True, "reason": "local venv runner always available"}

    def ensure_cache(self, cache_key: str) -> Path:
        d = _VENVS / cache_key
        d.mkdir(parents=True, exist_ok=True)
        return d

    def run(self, *, cache_key: str, argv: list[str], task_id: str = "venv-task", timeout_s: int = 20,
            env: dict | None = None) -> ExecutionResult:
        """Run argv as a bounded local subprocess inside the venv cache dir. Structured failure on error/
        timeout — never raises out, never global-installs."""
        d = self.ensure_cache(cache_key)
        run_env = {**os.environ, **(env or {})}
        try:
            p = subprocess.run(argv, cwd=str(d), env=run_env, capture_output=True, text=True, timeout=timeout_s)
            status = "succeeded" if p.returncode == 0 else "failed"
            return ExecutionResult(provider_id=self.provider_id, execution_id="venv-" + task_id, task_id=task_id,
                                   status=status, result_ids=(f"venv-art:{task_id}",) if status == "succeeded" else (),
                                   is_truth=False, detail={"returncode": p.returncode, "stdout": p.stdout[-2000:],
                                                            "stderr": p.stderr[-2000:], "venv": str(d)})
        except subprocess.TimeoutExpired:
            return ExecutionResult(provider_id=self.provider_id, execution_id="venv-" + task_id, task_id=task_id,
                                   status="failed", is_truth=False,
                                   detail={"error": f"timeout after {timeout_s}s", "failure_type": "memory_limit_exceeded"})
        except Exception as e:  # never crash the loop
            return ExecutionResult(provider_id=self.provider_id, execution_id="venv-" + task_id, task_id=task_id,
                                   status="failed", is_truth=False, detail={"error": f"{type(e).__name__}: {e}"})

    def run_python(self, *, cache_key: str, code: str, task_id: str = "venv-task", timeout_s: int = 20) -> ExecutionResult:
        """Convenience: run a short python snippet locally (no install)."""
        return self.run(cache_key=cache_key, argv=[sys.executable, "-c", code], task_id=task_id, timeout_s=timeout_s)


__all__ = ["ManagedVenvProvider", "PROVIDER_ID"]
