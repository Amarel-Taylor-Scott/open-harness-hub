"""src.teleon.synthesis.variation_store — store a capability's VARIATIONS in git (GitHub/GitLab) + the version log.

The synthesis tree explores many variations of a capability (winners AND losers — lossless). This persists them two ways:
(1) the durable append-only version_history stream (record_store, history tier — SQLite local / Postgres cloud), and
(2) git via the capability_pr layer (src/teleon/storage) — the WINNING variation committed to main, each explored loser as
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

_STREAM = "version_history"


def version_hash(capability: str, decision_path: str) -> str:
    return hashlib.sha256(f"{capability}|{decision_path}".encode()).hexdigest()[:16]


def record_variations(capability: str, variations: list[dict]) -> dict:
    """Append each variation to the durable version_history stream (idempotent by version_hash; winners + losers kept)."""
    st = RS.open_record_store(_STREAM)
    try:
        before = st.count()                          # idempotency is enforced by the store (dedupe on version_hash);
        for v in variations:                         # we report TRUE added via before/after (append's int return is always truthy)
            vh = version_hash(capability, v["decision_path"])
            rec = {"version_hash": vh, "component_id": capability, "capability": capability,
                   "decision_path": v["decision_path"], "status": v.get("status", "explored"),
                   "strategy": v.get("strategy", "base"), "note": v.get("note", ""), "serves_truth": False}
            st.append(rec, idem_key=vh)
        added = st.count() - before
    finally:
        st.close()
    return {"capability": capability, "stored": added, "total": len(variations)}


def list_variations(capability: str) -> list[dict]:
    st = RS.open_record_store(_STREAM)
    try:
        return [r for r in st.all() if r.get("capability") == capability]
    finally:
        st.close()


def _branch(capability: str, v: dict) -> str:
    return f"{capability}/{v.get('status', 'var')}-{version_hash(capability, v['decision_path'])[:8]}"


def commit_to_git(capability: str, variations: list[dict], *, platform: str = "internal", repo: str = "capabilities",
                  now: str, token_present: bool = False) -> dict:
    """Store variations in git: the WINNING variation -> main; each explored loser -> a PR branch (lossless review trail).
    platform 'internal' uses LocalGitBackend (offline, always works); 'github'/'gitlab'/... uses the client backend and
    REQUIRES a git_token (honest plan-only when absent — never a fake push)."""
    if platform not in SUPPORTED_PLATFORMS:
        return {"error": f"unsupported platform {platform!r}; supported: {list(SUPPORTED_PLATFORMS)}"}
    if platform != "internal" and not token_present:
        return {"platform": platform, "pushed": False, "reason": f"needs a git_token for {platform} (add it to the key holder)",
                "plan": [{"ref": _branch(capability, v), "status": v.get("status")} for v in variations]}
    backend = LocalGitBackend() if platform == "internal" else ClientPlatformBackend(platform, repo)
    rk = CapabilityRepo(backend)
    winner = next((v for v in variations if v.get("status") == "working"), None)
    branches = []
    if winner:
        rk.commit_main(capability, json.dumps(winner), message=f"capability {capability}: winning variation", now=now)
    for v in variations:
        if v is winner:
            continue
        br = _branch(capability, v)
        rk.open_pr(capability, branch=br, head_code=json.dumps(v),
                   eval_result={"status": v.get("status"), "note": v.get("note", "")}, title=f"variation {br}")
        branches.append({"ref": br, "status": v.get("status")})
    return {"platform": platform, "pushed": True, "main": bool(winner), "branches": branches, "count": len(variations)}
