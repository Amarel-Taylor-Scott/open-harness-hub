"""src.teleon.compiler.fixtures — DETERMINISTIC offline fixtures for the compiler CLI/tests.

``fixture_promoted_capability`` / ``fixture_task_spec`` / ``fixture_resolved_preference`` / ``fixture_candidate_
capability`` — a stable, offline promoted-capability + CapabilityTask-spec + OIPS-preference triple (plus a
non-promoted candidate for the refusal test) that the self-test and the ``--compile`` fallback use, so the compiler
is exercisable with no live runtime.

Reading the LIVE runtime state lives in the sibling ``live_capability`` module (a *fixtures* module shouldn't do
production live-state I/O). stdlib only; no ``src.baltor`` / ``src.openharnesshub`` import.
"""
from __future__ import annotations

import json
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
    "schema_version": "ResolvedInferencePreference",
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


__all__ = ["fixture_task_spec", "fixture_promoted_capability", "fixture_candidate_capability",
           "fixture_resolved_preference"]
