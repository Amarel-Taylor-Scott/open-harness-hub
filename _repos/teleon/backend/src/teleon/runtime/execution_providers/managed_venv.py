"""src.teleon.runtime.execution_providers.managed_venv — run container/image/function-style tasks LOCALLY
without Docker or cloud. The local equivalent for container-image / function execution. Creates a cache
dir under .agent/venvs/<key>/, runs the entrypoint as a bounded subprocess, captures stdout/stderr,
enforces a timeout, returns a structured ExecutionResult (never truth). NEVER global pip / sudo / apt /
brew / docker. The task still requires an atomic claim — the venv runner is given a reference, not ownership.

Canonical TELEON home (runtime layer); imports the port from Teleon (never Baltor). Baltor re-exports this via
a shim at _repos/baltor/backend/src/baltor/workers/execution_providers/managed_venv.py.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from src.teleon.runtime.execution_provider import py_class_src_teleon_runtime_execution_provider__ExecutionResult

py_var_src_teleon_runtime_execution_providers_managed_venv___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[4])
py_var_src_teleon_runtime_execution_providers_managed_venv___VENVS = py_var_src_teleon_runtime_execution_providers_managed_venv___REPO / ".agent" / "venvs"
py_const_src_teleon_runtime_execution_providers_managed_venv__PROVIDER_ID = "execution.managed_venv@v1"


class py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider:
    provider_id = py_const_src_teleon_runtime_execution_providers_managed_venv__PROVIDER_ID

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "kind": "managed_venv", "owns_truth": False,
                "no_docker": True, "no_global_pip": True, "no_sudo": True}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": True, "reason": "local venv runner always available"}

    def ensure_cache(self, py_arg_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_ensure_cache__cache_key: str) -> Path:
        py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_ensure_cache__d = py_var_src_teleon_runtime_execution_providers_managed_venv___VENVS / py_arg_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_ensure_cache__cache_key
        py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_ensure_cache__d.mkdir(parents=True, exist_ok=True)
        return py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_ensure_cache__d

    def run(self, *, cache_key: str, argv: list[str], task_id: str = "venv-task", timeout_s: int = 20,
            env: dict | None = None) -> py_class_src_teleon_runtime_execution_provider__ExecutionResult:
        """Run argv as a bounded local subprocess inside the venv cache dir. Structured failure on error/
        timeout — never raises out, never global-installs."""
        py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__d = self.ensure_cache(cache_key)
        py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__run_env = {**os.environ, **(env or {})}
        try:
            py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__p = subprocess.run(argv, cwd=str(py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__d), env=py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__run_env, capture_output=True, text=True, timeout=timeout_s)
            py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__status = "succeeded" if py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__p.returncode == 0 else "failed"
            return py_class_src_teleon_runtime_execution_provider__ExecutionResult(provider_id=self.provider_id, execution_id="venv-" + task_id, task_id=task_id,
                                   status=py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__status, result_ids=(f"venv-art:{task_id}",) if py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__status == "succeeded" else (),
                                   is_truth=False, detail={"returncode": py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__p.returncode, "stdout": py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__p.stdout[-2000:],
                                                            "stderr": py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__p.stderr[-2000:], "venv": str(py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__d)})
        except subprocess.TimeoutExpired:
            return py_class_src_teleon_runtime_execution_provider__ExecutionResult(provider_id=self.provider_id, execution_id="venv-" + task_id, task_id=task_id,
                                   status="failed", is_truth=False,
                                   detail={"error": f"timeout after {timeout_s}s", "failure_type": "memory_limit_exceeded"})
        except Exception as py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__e:  # never crash the loop
            return py_class_src_teleon_runtime_execution_provider__ExecutionResult(provider_id=self.provider_id, execution_id="venv-" + task_id, task_id=task_id,
                                   status="failed", is_truth=False, detail={"error": f"{type(py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__e).__name__}: {py_local_src_teleon_runtime_execution_providers_managed_venv__py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider_run__e}"})

    def run_python(self, *, cache_key: str, code: str, task_id: str = "venv-task", timeout_s: int = 20) -> py_class_src_teleon_runtime_execution_provider__ExecutionResult:
        """Convenience: run a short python snippet locally (no install)."""
        return self.run(cache_key=cache_key, argv=[sys.executable, "-c", code], task_id=task_id, timeout_s=timeout_s)


__all__ = ["py_class_src_teleon_runtime_execution_providers_managed_venv__ManagedVenvProvider", "py_const_src_teleon_runtime_execution_providers_managed_venv__PROVIDER_ID"]
