"""src.teleon.compiler.live_capability — read the LIVE teleon runtime state for the compiler CLI.

Split out of ``compiler/fixtures.py`` (organization: a module named *fixtures* should hold deterministic offline
fixtures, not production live-state I/O). ``load_live_capability`` reads the live capability record
(``capabilities.json`` + ``runs.jsonl`` under the runtime's STATE_DIR) and ENRICHES it with the gate evidence +
receipt refs from its latest PROMOTING run. Honest: fields the live record never carried come back as ``None``
(never fabricated).

No magic values: the live STATE_DIR is imported (LAZILY, inside ``_state_dir``) from ``scripts.teleon_local_runtime``
— its single definition, not re-typed. Keeping that import lazy means this product module carries NO top-level
dev-tool dependency (plane separation stays green). stdlib only; no ``src.baltor`` / ``src.openharnesshub`` import.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _state_dir() -> Path:
    """The live teleon-runtime STATE_DIR — imported (lazily) from its single definition (no re-typed path)."""
    from scripts.teleon_local_runtime import STATE_DIR  # one source of the state path
    return STATE_DIR


def _latest_promoting_run(runs_path: Path, capability_id: str) -> dict[str, Any] | None:
    """The most recent run that PROMOTED this capability (latest-line-wins fold over the append-only event log)."""
    if not runs_path.is_file():
        return None
    latest: dict[str, Any] | None = None
    for line in runs_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if rec.get("capability_id") == capability_id and rec.get("status") == "promoted":
            latest = rec  # keep walking → the LAST promoting run wins
    return latest


def load_live_capability(capability_id: str, *, state_dir: Path | None = None) -> tuple[dict[str, Any], list[str]]:
    """Read the LIVE capability record for ``capability_id`` and ENRICH it with the gate evidence + receipt refs
    from its latest promoting run. Returns (capability_record, receipt_refs).

    Raises ``FileNotFoundError`` when there is no live capabilities.json, and ``KeyError`` when the capability is
    absent — the CLI falls back to the fixture on either. Honest: train/holdout/gate_basis come from the promoting
    run when present, else ``None`` (never fabricated). receipt_refs = the run_id(s) of the promoting run (the
    receipt correlation handle the runtime persists)."""
    sdir = state_dir or _state_dir()
    caps_path = sdir / "capabilities.json"
    runs_path = sdir / "runs.jsonl"
    if not caps_path.is_file():
        raise FileNotFoundError(f"no live capabilities.json at {caps_path}")
    caps = json.loads(caps_path.read_text(encoding="utf-8"))
    if capability_id not in caps:
        raise KeyError(capability_id)
    cap = dict(caps[capability_id])
    receipt_refs: list[str] = []
    run = _latest_promoting_run(runs_path, capability_id)
    if run is not None:
        # enrich (never overwrite a value the record already carries) — gate evidence from the promoting run
        cap.setdefault("train_pass_rate", run.get("train_pass_rate"))
        cap.setdefault("holdout_pass_rate", run.get("holdout_pass_rate"))
        cap.setdefault("gate_basis", run.get("gate_basis"))
        # promoted_at: the run's epoch 'at' as an honest provenance handle (string); None when absent
        if run.get("at") is not None and cap.get("promoted_at") is None:
            cap["promoted_at"] = f"epoch:{run['at']}"
        if run.get("run_id"):
            receipt_refs = [str(run["run_id"])]
    return cap, receipt_refs


__all__ = ["load_live_capability"]
