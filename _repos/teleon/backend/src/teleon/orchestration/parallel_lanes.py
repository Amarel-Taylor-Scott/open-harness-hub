"""src.teleon.orchestration.parallel_lanes — coordinate a PARALLEL dev fleet (Claude Code + Ollama agents) that never
edits the same file at once.

The guarantee has two layers (see _repos/shared-backend-components/architecture/parallel_dev_lanes.json):
  1. WORKTREE ISOLATION — each lane runs in its own git worktree (separate working dir + branch), so two agents
     physically cannot write the same file in the same tree.
  2. DISJOINT OWNERSHIP — lanes own non-overlapping file globs, so their diffs don't collide at merge; and the
     files EVERY increment touches (the proof registry + the computed count token) are SERIALIZED (owned by no lane,
     applied by the coordinator at merge, one lane at a time).

Brains are assigned by the unbounded->bounded policy: cheap Ollama (GLM-5.2 / Kimi) for narrow/deterministic/templated
lanes, Claude Code for ambiguous/design lanes. This module is pure planning/validation (no spawning, no network);
the launcher script run_parallel_dev_fleet.sh does the worktree creation + agent spawning (owner-gated). serves_truth
False; Teleon-layer (never imports baltor).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
_MANIFEST = _resource("architecture") / "parallel_dev_lanes.json"
_WORKTREE_ROOT = ".agent/worktrees"   # repo-relative; one worktree dir per lane


def load_manifest() -> dict:
    with open(_MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def lanes() -> list[dict]:
    return load_manifest().get("lanes", [])


def shared_files() -> list[str]:
    return load_manifest().get("shared_serialized", {}).get("files", [])


def _expand(globs: list[str]) -> set[str]:
    """Expand a lane's owns globs to the set of repo-relative FILE paths they match (supports literal paths, '*',
    and recursive '**'). A trailing '/**' is normalized to '/**/*' because pathlib's bare '**' matches only
    directories, not the files under them. Non-matching globs simply contribute nothing."""
    out: set[str] = set()
    for g in globs:
        pattern = (g + "/*") if g.endswith("/**") else g
        for p in _REPO.glob(pattern):
            if p.is_file():
                out.add(str(p.relative_to(_REPO)))
    return out


def owned_files(lane: dict) -> set[str]:
    return _expand(lane.get("owns", []))


def validate_disjoint() -> dict:
    """Prove the no-same-file-edit guarantee at the ownership layer: lanes' owned file sets are pairwise disjoint, and
    no lane owns a shared-serialized file. Returns {ok, overlaps, shared_violations, per_lane_counts}."""
    ls = lanes()
    files_by_lane = {ln["id"]: owned_files(ln) for ln in ls}
    overlaps: dict[str, list[str]] = {}
    ids = list(files_by_lane)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            common = sorted(files_by_lane[ids[i]] & files_by_lane[ids[j]])
            if common:
                overlaps[f"{ids[i]} & {ids[j]}"] = common
    shared = set(shared_files())
    shared_violations = {ln_id: sorted(fs & shared) for ln_id, fs in files_by_lane.items() if fs & shared}
    return {
        "ok": not overlaps and not shared_violations,
        "overlaps": overlaps,
        "shared_violations": shared_violations,
        "per_lane_counts": {k: len(v) for k, v in files_by_lane.items()},
    }


def brain_command(brain: str) -> str:
    """Resolve the command that drives a brain's agent: claude -> CLAUDE_CODE_CMD (default 'claude -p'); ollama ->
    OLLAMA_AGENT_CMD (an OpenAI-compatible agent pointed at the local Ollama endpoint; no hardcoded default so it must
    be supplied for live ollama lanes). Empty string means 'not configured' — the launcher dry-runs / skips it."""
    spec = load_manifest().get("brains", {}).get(brain, {})
    env_name = spec.get("command_env", "")
    return os.environ.get(env_name, spec.get("default_command", "")) if env_name else spec.get("default_command", "")


def worktree_path(lane: dict) -> str:
    return f"{_WORKTREE_ROOT}/{lane['id']}"


def lane_prompt(lane: dict) -> str:
    """The scoped self-prompt for a lane's agent: it OWNS only its files, must not touch others or the shared files,
    runs its own check, and leaves its worktree green for the coordinator to merge."""
    owns = ", ".join(lane.get("owns", []))
    return (f"You are the '{lane['id']}' lane agent ({lane['surface']}). You work in an ISOLATED git worktree on your "
            f"own branch. You OWN ONLY these paths: {owns}. Do NOT edit any file outside them, and NEVER edit the "
            f"shared-serialized files ({', '.join(shared_files())}) — the coordinator applies proof registration + the "
            f"count token at merge. Ship one proof-backed increment on your surface, run your lane's check + leave the "
            f"worktree green. serves_truth=false; candidate!=active.")


def plan() -> list[dict]:
    """Dry-run plan: what each lane agent would do. No worktrees created, no agents spawned."""
    out = []
    for ln in lanes():
        cmd = brain_command(ln["brain"])
        out.append({
            "lane": ln["id"], "surface": ln["surface"], "brain": ln["brain"],
            "owned_file_count": len(owned_files(ln)),
            "worktree": worktree_path(ln),
            "branch": f"fleet/{ln['id']}",
            "command_configured": bool(cmd),
            "command_preview": (cmd or f"<set ${load_manifest()['brains'][ln['brain']]['command_env']}>"),
        })
    return out
