"""src.baltor.sales.diagnostics.runner — resolve a configurable engagement mode and gate a diagnostic run.

start_diagnostic returns (DiagnosticRun | None, reasons). A run is refused (None) when the authorization basis
isn't permitted by the active/selected mode, or when a live third-party probe is requested but the mode forbids it
or the basis isn't written_authorization. Pure + deterministic; composes src.baltor.sales.claim_guard.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import hashlib
import json
from pathlib import Path
from typing import Any

from src.baltor.sales import claim_guard as _guard

_A = _resource("architecture")


def load_modes() -> dict:
    return json.loads((_A / "sales_diagnostic_modes.json").read_text(encoding="utf-8"))


def resolve_mode(name: str | None = None) -> tuple[str, dict]:
    cfg = load_modes()
    key = name or cfg.get("active_mode", "safe_default")
    return key, cfg["modes"].get(key, cfg["modes"]["safe_default"])


def _rid(*parts: str) -> str:
    return "dxrun_" + hashlib.blake2b("|".join(parts).encode(), digest_size=10).hexdigest()


def start_diagnostic(*, tool: str, mode: str | None, authorization_basis: str, input_source: str,
                     is_live_probe: bool, company_id: str | None, now: str) -> tuple[dict | None, list[str]]:
    mode_key, m = resolve_mode(mode)
    reasons: list[str] = []
    if authorization_basis not in m.get("allowed_authorization_bases", []):
        reasons.append(f"authorization_basis_not_allowed_in_mode_{mode_key}")
    if is_live_probe:
        if not m.get("allow_live_probe"):
            reasons.append(f"live_probe_not_allowed_in_mode_{mode_key}")
        elif authorization_basis != m.get("live_probe_requires", "written_authorization"):
            reasons.append("live_probe_requires_written_authorization")
    # second, independent gate: the global engagement policy (defense in depth)
    ok_auth, why_auth = _guard.authorization_ok({"is_live_probe": is_live_probe, "authorization_basis": authorization_basis})
    if not ok_auth:
        reasons += why_auth
    if reasons:
        return None, sorted(set(reasons))
    run = {
        "schema_version": "DiagnosticRun",
        "run_id": _rid(tool, mode_key, authorization_basis, input_source, now),
        "tool": tool, "company_id": company_id, "authorization_basis": authorization_basis,
        "input_source": input_source, "is_live_probe": is_live_probe, "mode": mode_key,
        "findings": [], "created_at": now,
    }
    return run, []


__all__ = ["load_modes", "resolve_mode", "start_diagnostic"]
