"""src.teleon.compiler.fixtures — deterministic fixtures + a live-state reader for the compiler CLI/tests.

Two jobs:
  * ``fixture_promoted_capability`` / ``fixture_task_spec`` / ``fixture_resolved_preference`` — a stable, offline
    promoted-capability + CapabilityTask-spec + OIPS-preference triple the self-test and the ``--compile`` fallback
    use, so the compiler is exercisable with no live runtime.
  * ``load_live_capability`` — read the LIVE teleon runtime state (``capabilities.json`` + ``runs.jsonl`` under the
    runtime's STATE_DIR), returning a capability record ENRICHED with the gate evidence + receipt refs from its
    latest PROMOTING run. Honest: fields the live record never carried come back as ``None`` (never fabricated).

No magic values: the live STATE_DIR is imported from ``scripts.teleon_local_runtime`` (its single definition), not
re-typed. stdlib only; no ``src.baltor`` / ``src.openharnesshub`` import.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

#: a deterministic CapabilityTask spec for the fixture / live-compile default — declares the runtime CLASS
#: (vendor-neutral), the resource class (joins worker_resource_classes.json), the SLA policy (joins
#: worker_sla_policies.json), and the gate's retry ceiling. This is the TASK CONTRACT a capability compiles under.
_FIXTURE_TASK_SPEC: dict[str, Any] = {
    "task_id": "task-fixture-deterministic-capability",
    "tenant_id": "teleon-internal",
    "capability_id": "cap-redact",
    "allowed_runtime_classes": ["cloud-function", "kubernetes-job"],
    "required_resource_class": "standard_cpu",
    "sla_policy_id": "interactive_30s",
    "max_attempts": 3,
    "batch_policy_id": "",
    "lifecycle_policy_id": "",
}

#: a fixture promoted-capability record matching the runtime's capability shape (id/name/criteria/version/status/
#: last_score/examples/last_mode) PLUS the gate-evidence fields a promoting run carries (train/holdout/gate_basis).
_FIXTURE_CAPABILITY: dict[str, Any] = {
    "id": "cap-redact",
    "name": "PII redactor",
    "criteria": ["emails masked", "phones masked", "exact otherwise"],
    "version": 2,
    "status": "promoted",
    "last_score": 1.0,
    "last_mode": "deterministic",
    "examples": 4,
    "train_pass_rate": 1.0,
    "holdout_pass_rate": 1.0,
    "gate_basis": "train+holdout",
    "promoted_at": "2026-06-11T00:00:00Z",
}

#: a fixture OIPS resolved-preference whose budget_policy supplies a token ceiling (so budgets.max_tokens is
#: policy-sourced, not the default constant) — proves the budget JOIN, not a magic number.
_FIXTURE_RESOLVED_PREFERENCE: dict[str, Any] = {
    "schema_version": "ResolvedInferencePreference.v1",
    "preference_id": "pref-fixture",
    "effective": {"budget_policy": {"max_output_tokens": 512, "max_model_cost_usd": 0.02}},
}

#: a non-promoted capability (status candidate) for the REFUSAL test — the only-promoted-compiles law.
_FIXTURE_CANDIDATE_CAPABILITY: dict[str, Any] = {
    "id": "cap-json-guard", "name": "JSON schema guard", "criteria": ["parses or repairs once"],
    "version": 1, "status": "candidate", "last_score": None, "examples": 4,
}


def fixture_task_spec() -> dict[str, Any]:
    return json.loads(json.dumps(_FIXTURE_TASK_SPEC))  # deep copy so callers can't mutate the canonical fixture


def fixture_promoted_capability() -> dict[str, Any]:
    return json.loads(json.dumps(_FIXTURE_CAPABILITY))


def fixture_candidate_capability() -> dict[str, Any]:
    return json.loads(json.dumps(_FIXTURE_CANDIDATE_CAPABILITY))


def fixture_resolved_preference() -> dict[str, Any]:
    return json.loads(json.dumps(_FIXTURE_RESOLVED_PREFERENCE))


def _state_dir() -> Path:
    """The live teleon-runtime STATE_DIR — imported from its single definition (no re-typed path)."""
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


__all__ = ["fixture_task_spec", "fixture_promoted_capability", "fixture_candidate_capability",
           "fixture_resolved_preference", "load_live_capability"]
