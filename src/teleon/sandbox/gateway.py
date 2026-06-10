"""src.teleon.sandbox.gateway — SandboxProviderPort + a local deterministic provider + governed run.

Deny-by-default: the local provider runs a candidate's command in a scoped tempdir with a SANITIZED env (no
inherited secrets), no shell, and a timeout. True OS-level network isolation is a CANDIDATE-provider capability
(documented in the catalog) — the local provider declares network=none and refuses to pass any secret/network
env. Sandbox output is NOT truth. Pure-ish + deterministic (injected `now`; commands are caller-provided).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Protocol

_REPO = Path(__file__).resolve().parents[3]
_CATALOG = _REPO / "architecture" / "sandbox_provider_catalog.json"
OFFLINE_DEFAULT_PROVIDER = "sandbox.local_tempdir@v1"
_SECRET_RE = re.compile(r"(AKIA[0-9A-Z]{12}|sk-[a-zA-Z0-9]{16}|ghp_[A-Za-z0-9]{20})")
#: env keys never passed into a sandbox
_SECRET_ENV_HINTS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "AWS_", "OPENAI", "ANTHROPIC")


class SandboxProviderPort(Protocol):
    provider_id: str

    def describe(self) -> dict: ...
    def health(self) -> dict: ...
    def run(self, request: dict, *, now: str) -> dict: ...


def load_catalog() -> dict:
    return json.loads(_CATALOG.read_text(encoding="utf-8"))


def _sanitized_env() -> dict:
    """A minimal env with ALL secret-ish keys stripped (deny-by-default)."""
    return {k: v for k, v in os.environ.items()
            if k in ("PATH", "LANG", "LC_ALL", "HOME", "TMPDIR") and not any(h in k.upper() for h in _SECRET_ENV_HINTS)}


def _receipt(run_id: str, provider_id: str, now: str, **extra) -> dict:
    rid = "sbxrcpt_" + hashlib.blake2b(f"{run_id}|{provider_id}|{now}".encode(), digest_size=10).hexdigest()
    return {"schema_version": "SandboxReceipt.v1", "receipt_id": rid, "run_id": run_id, "provider_id": provider_id,
            "created_at": now, "is_truth": False, **extra}


class LocalTempdirProvider:
    """Offline golden-path sandbox: scoped tempdir + sanitized env + timeout + no shell. Network = none."""
    provider_id = OFFLINE_DEFAULT_PROVIDER

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "kind": "local_tempdir", "external": False, "network": "none"}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": True}

    def run(self, request: dict, *, now: str) -> dict:
        cmd = request.get("command") or []
        timeout = int(request.get("timeout_seconds", 15))
        tmp = Path(tempfile.mkdtemp(prefix="sbx-"))
        violations: list[str] = []
        # policy: deny network + secrets by default
        if (request.get("network_policy") or "none") not in ("none", "deny", "egress_deny"):
            violations.append("network_requested_but_denied_by_default")
        out, err, code = "", "", None
        try:
            if cmd and isinstance(cmd, list):
                p = subprocess.run(cmd, cwd=str(tmp), env=_sanitized_env(), capture_output=True,
                                   text=True, timeout=timeout)  # no shell=True
                out, err, code = p.stdout[:8192], p.stderr[:4096], p.returncode
            else:
                code = 0  # no-op candidate (e.g. metadata-only parse)
        except subprocess.TimeoutExpired:
            violations.append("timeout"); code = None
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}"; code = None
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        secrets_leaked = bool(_SECRET_RE.search(out) or _SECRET_RE.search(err))
        if secrets_leaked:
            violations.append("secret_in_output")
        expected = request.get("expected_outputs") or []
        contract_ok = (code == 0) and all(e in out for e in expected)
        status = "ok" if (code == 0 and not violations) else ("policy_violation" if violations else "failed")
        return {"schema_version": "SandboxRunResult.v1", "run_id": request["run_id"], "provider_id": self.provider_id,
                "status": status, "exit_code": code, "output_contract_valid": contract_ok,
                "policy_violations": violations, "secrets_leaked": secrets_leaked, "network_events": [],
                "duration_ms": None, "cost_estimate": 0.0, "stdout_sample": out[:512],
                "receipt_id": _receipt(request["run_id"], self.provider_id, now)["receipt_id"], "is_truth": False}


class _CandidateSeam:
    """A candidate external provider (docker/e2b/daytona/cubesandbox/...) — NOT available offline; never runs on
    the host. Returns ProviderUnavailable so the caller falls back to the local provider or fails closed."""

    def __init__(self, provider_id: str):
        self.provider_id = provider_id

    def describe(self) -> dict:
        return {"provider_id": self.provider_id, "external": True, "available": False}

    def health(self) -> dict:
        return {"provider_id": self.provider_id, "available": False, "reason": "candidate — needs creds/host/infra"}

    def run(self, request: dict, *, now: str) -> dict:
        return {"schema_version": "SandboxRunResult.v1", "run_id": request["run_id"], "provider_id": self.provider_id,
                "status": "provider_unavailable", "exit_code": None, "output_contract_valid": False,
                "policy_violations": [], "secrets_leaked": False,
                "receipt_id": _receipt(request["run_id"], self.provider_id, now, unavailable=True)["receipt_id"], "is_truth": False}


def select_provider(provider_id: str | None = None) -> SandboxProviderPort:
    """Return a provider. Default = the local golden path. Any external/candidate id → a labelled seam (never the
    host) so missing infra cannot silently execute on the machine."""
    if provider_id in (None, OFFLINE_DEFAULT_PROVIDER):
        return LocalTempdirProvider()
    cat = {p["provider_id"]: p for p in load_catalog()["providers"]}
    node = cat.get(provider_id)
    if node and not node.get("external"):
        return LocalTempdirProvider()  # other local providers share the local impl for now
    return _CandidateSeam(provider_id)


def run_in_sandbox(request: dict, *, provider_id: str | None = None, now: str) -> dict:
    """Run a candidate in a sandbox (default local). The result is EVIDENCE for the promotion gate — never truth."""
    return select_provider(provider_id).run(request, now=now)


__all__ = ["SandboxProviderPort", "LocalTempdirProvider", "select_provider", "run_in_sandbox", "load_catalog",
           "OFFLINE_DEFAULT_PROVIDER"]
