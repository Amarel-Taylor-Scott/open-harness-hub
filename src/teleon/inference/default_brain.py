"""src.teleon.inference.default_brain — the cheap DEFAULT brain (Ollama: GLM-5.2 / Kimi-k2.7-code) as orchestrator,
reviewer, and distiller-judge, escalating to a frontier model only when a confidence/quality bar fails.

The descent applied to the brain itself: the LLM that DRIVES a capability from unbounded+inefficient toward
most-bounded+most-efficient should itself run cheap by default. Reads architecture/default_brain_policy.json; auth
via OLLAMA_API_KEY (env ref; value in the gitignored .env, never tracked). The brain PROPOSES; gates DISPOSE —
serves_truth False. Teleon-layer; never imports baltor.
"""
from __future__ import annotations

import json
from pathlib import Path

_POLICY = Path(__file__).resolve().parents[3] / "architecture" / "default_brain_policy.json"


def load_policy() -> dict:
    return json.loads(_POLICY.read_text())


def roles() -> list[str]:
    return [r["role"] for r in load_policy()["roles"]]


def _role(role: str) -> dict | None:
    return next((r for r in load_policy()["roles"] if r["role"] == role), None)


def brain_for(role: str, *, available_keys: tuple = (), force_frontier: bool = False) -> dict:
    """Pick the model for a brain role: the cheap Ollama default when OLLAMA_API_KEY is available and no escalation
    is forced; otherwise the frontier escalation. Honest when neither is reachable."""
    r = _role(role)
    if not r:
        return {"role": role, "error": "unknown brain role", "serves_truth": False}
    have = {k.upper() for k in available_keys}
    auth = r["auth_env_ref"]
    default_reachable = auth.upper() in have
    if force_frontier:
        pick, is_default, why = r["escalation_model"], False, f"escalation forced ({r['escalate_when']})"
    elif default_reachable:
        pick, is_default, why = r["default_model"], True, "cheap Ollama default (frontier only on escalation)"
    else:
        pick, is_default, why = r["escalation_model"], False, f"default unavailable ({auth} not set) — using escalation"
    return {
        "role": role, "model": pick, "is_default": is_default, "provider": r["default_provider"] if is_default else "frontier",
        "auth_env_ref": auth, "default_model": r["default_model"], "escalation_model": r["escalation_model"],
        "escalate_when": r["escalate_when"], "default_reachable": default_reachable, "reason": why, "serves_truth": False,
    }
