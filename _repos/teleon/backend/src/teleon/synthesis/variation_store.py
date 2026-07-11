"""src.teleon.synthesis.variation_store — store a capability's VARIATIONS in git (GitHub/GitLab) + the version log.

The synthesis tree explores many variations of a capability (winners AND losers — lossless). This persists them two ways:
(1) the durable append-only version_history stream (record_store, history tier — SQLite local / Postgres cloud), and
(2) git via the capability_pr layer (_repos/teleon/backend/src/teleon/storage) — the WINNING variation committed to main, each explored loser as
a PR branch — backed by INTERNAL git (offline) OR the CLIENT's GitHub/GitLab/Bitbucket (via a git_token from the key
holder). So variations are versioned, diffable, restorable, and reviewable in a GitHub-familiar way. serves_truth=false.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.teleon.storage import record_store as RS
from src.teleon.storage.capability_pr import CapabilityRepo
from src.teleon.storage.git_backend_port import SUPPORTED_PLATFORMS, ClientPlatformBackend, LocalGitBackend

py_var_src_teleon_synthesis_variation_store___STREAM = "version_history"


def py_function_src_teleon_synthesis_variation_store__version_hash(py_arg_src_teleon_synthesis_variation_store__version_hash__capability: str, py_arg_src_teleon_synthesis_variation_store__version_hash__decision_path: str) -> str:
    return hashlib.sha256(f"{py_arg_src_teleon_synthesis_variation_store__version_hash__capability}|{py_arg_src_teleon_synthesis_variation_store__version_hash__decision_path}".encode()).hexdigest()[:16]


def py_function_src_teleon_synthesis_variation_store__record_variations(py_arg_src_teleon_synthesis_variation_store__record_variations__capability: str, py_arg_src_teleon_synthesis_variation_store__record_variations__variations: list[dict]) -> dict:
    """Append each variation to the durable version_history stream (idempotent by version_hash; winners + losers kept)."""
    py_local_src_teleon_synthesis_variation_store__record_variations__st = RS.open_record_store(py_var_src_teleon_synthesis_variation_store___STREAM)
    try:
        py_local_src_teleon_synthesis_variation_store__record_variations__before = py_local_src_teleon_synthesis_variation_store__record_variations__st.count()                          # idempotency is enforced by the store (dedupe on version_hash);
        for py_local_src_teleon_synthesis_variation_store__record_variations__v in py_arg_src_teleon_synthesis_variation_store__record_variations__variations:                         # we report TRUE added via before/after (append's int return is always truthy)
            py_local_src_teleon_synthesis_variation_store__record_variations__vh = py_function_src_teleon_synthesis_variation_store__version_hash(py_arg_src_teleon_synthesis_variation_store__record_variations__capability, py_local_src_teleon_synthesis_variation_store__record_variations__v["decision_path"])
            py_local_src_teleon_synthesis_variation_store__record_variations__rec = {"version_hash": py_local_src_teleon_synthesis_variation_store__record_variations__vh, "component_id": py_arg_src_teleon_synthesis_variation_store__record_variations__capability, "capability": py_arg_src_teleon_synthesis_variation_store__record_variations__capability,
                   "decision_path": py_local_src_teleon_synthesis_variation_store__record_variations__v["decision_path"], "status": py_local_src_teleon_synthesis_variation_store__record_variations__v.get("status", "explored"),
                   "strategy": py_local_src_teleon_synthesis_variation_store__record_variations__v.get("strategy", "base"), "note": py_local_src_teleon_synthesis_variation_store__record_variations__v.get("note", ""), "serves_truth": False}
            py_local_src_teleon_synthesis_variation_store__record_variations__st.append(py_local_src_teleon_synthesis_variation_store__record_variations__rec, idem_key=py_local_src_teleon_synthesis_variation_store__record_variations__vh)
        py_local_src_teleon_synthesis_variation_store__record_variations__added = py_local_src_teleon_synthesis_variation_store__record_variations__st.count() - py_local_src_teleon_synthesis_variation_store__record_variations__before
    finally:
        py_local_src_teleon_synthesis_variation_store__record_variations__st.close()
    return {"capability": py_arg_src_teleon_synthesis_variation_store__record_variations__capability, "stored": py_local_src_teleon_synthesis_variation_store__record_variations__added, "total": len(py_arg_src_teleon_synthesis_variation_store__record_variations__variations)}


def py_function_src_teleon_synthesis_variation_store__list_variations(py_arg_src_teleon_synthesis_variation_store__list_variations__capability: str) -> list[dict]:
    py_local_src_teleon_synthesis_variation_store__list_variations__st = RS.open_record_store(py_var_src_teleon_synthesis_variation_store___STREAM)
    try:
        return [r for r in py_local_src_teleon_synthesis_variation_store__list_variations__st.all() if r.get("capability") == py_arg_src_teleon_synthesis_variation_store__list_variations__capability]
    finally:
        py_local_src_teleon_synthesis_variation_store__list_variations__st.close()


def py_function_src_teleon_synthesis_variation_store___branch(py_arg_src_teleon_synthesis_variation_store__branch__capability: str, py_arg_src_teleon_synthesis_variation_store__branch__v: dict) -> str:
    return f"{py_arg_src_teleon_synthesis_variation_store__branch__capability}/{py_arg_src_teleon_synthesis_variation_store__branch__v.get('status', 'var')}-{py_function_src_teleon_synthesis_variation_store__version_hash(py_arg_src_teleon_synthesis_variation_store__branch__capability, py_arg_src_teleon_synthesis_variation_store__branch__v['decision_path'])[:8]}"


def py_function_src_teleon_synthesis_variation_store__commit_to_git(py_arg_src_teleon_synthesis_variation_store__commit_to_git__capability: str, py_arg_src_teleon_synthesis_variation_store__commit_to_git__variations: list[dict], *, platform: str = "internal", py_arg_src_teleon_synthesis_variation_store__commit_to_git__repo: str = "capabilities",
                  now: str, token_present: bool = False) -> dict:
    """Store variations in git: the WINNING variation -> main; each explored loser -> a PR branch (lossless review trail).
    platform 'internal' uses LocalGitBackend (offline, always works); 'github'/'gitlab'/... uses the client backend and
    REQUIRES a git_token (honest plan-only when absent — never a fake push)."""
    if platform not in SUPPORTED_PLATFORMS:
        return {"error": f"unsupported platform {platform!r}; supported: {list(SUPPORTED_PLATFORMS)}"}
    if platform != "internal" and not token_present:
        return {"platform": platform, "pushed": False, "reason": f"needs a git_token for {platform} (add it to the key holder)",
                "plan": [{"ref": py_function_src_teleon_synthesis_variation_store___branch(py_arg_src_teleon_synthesis_variation_store__commit_to_git__capability, py_local_src_teleon_synthesis_variation_store__commit_to_git__v), "status": py_local_src_teleon_synthesis_variation_store__commit_to_git__v.get("status")} for py_local_src_teleon_synthesis_variation_store__commit_to_git__v in py_arg_src_teleon_synthesis_variation_store__commit_to_git__variations]}
    py_local_src_teleon_synthesis_variation_store__commit_to_git__backend = LocalGitBackend() if platform == "internal" else ClientPlatformBackend(platform, py_arg_src_teleon_synthesis_variation_store__commit_to_git__repo)
    rk = CapabilityRepo(py_local_src_teleon_synthesis_variation_store__commit_to_git__backend)
    py_local_src_teleon_synthesis_variation_store__commit_to_git__winner = next((py_local_src_teleon_synthesis_variation_store__commit_to_git__v for py_local_src_teleon_synthesis_variation_store__commit_to_git__v in py_arg_src_teleon_synthesis_variation_store__commit_to_git__variations if py_local_src_teleon_synthesis_variation_store__commit_to_git__v.get("status") == "working"), None)
    py_local_src_teleon_synthesis_variation_store__commit_to_git__branches = []
    if py_local_src_teleon_synthesis_variation_store__commit_to_git__winner:
        rk.commit_main(py_arg_src_teleon_synthesis_variation_store__commit_to_git__capability, json.dumps(py_local_src_teleon_synthesis_variation_store__commit_to_git__winner), message=f"capability {py_arg_src_teleon_synthesis_variation_store__commit_to_git__capability}: winning variation", now=now)
    for py_local_src_teleon_synthesis_variation_store__commit_to_git__v in py_arg_src_teleon_synthesis_variation_store__commit_to_git__variations:
        if py_local_src_teleon_synthesis_variation_store__commit_to_git__v is py_local_src_teleon_synthesis_variation_store__commit_to_git__winner:
            continue
        py_local_src_teleon_synthesis_variation_store__commit_to_git__br = py_function_src_teleon_synthesis_variation_store___branch(py_arg_src_teleon_synthesis_variation_store__commit_to_git__capability, py_local_src_teleon_synthesis_variation_store__commit_to_git__v)
        rk.open_pr(py_arg_src_teleon_synthesis_variation_store__commit_to_git__capability, branch=py_local_src_teleon_synthesis_variation_store__commit_to_git__br, head_code=json.dumps(py_local_src_teleon_synthesis_variation_store__commit_to_git__v),
                   eval_result={"status": py_local_src_teleon_synthesis_variation_store__commit_to_git__v.get("status"), "note": py_local_src_teleon_synthesis_variation_store__commit_to_git__v.get("note", "")}, title=f"variation {py_local_src_teleon_synthesis_variation_store__commit_to_git__br}")
        py_local_src_teleon_synthesis_variation_store__commit_to_git__branches.append({"ref": py_local_src_teleon_synthesis_variation_store__commit_to_git__br, "status": py_local_src_teleon_synthesis_variation_store__commit_to_git__v.get("status")})
    return {"platform": platform, "pushed": True, "main": bool(py_local_src_teleon_synthesis_variation_store__commit_to_git__winner), "branches": py_local_src_teleon_synthesis_variation_store__commit_to_git__branches, "count": len(py_arg_src_teleon_synthesis_variation_store__commit_to_git__variations)}
