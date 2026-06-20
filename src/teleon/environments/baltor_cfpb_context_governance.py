"""src.teleon.environments.baltor_cfpb_context_governance — a Baltor-STYLE governed task, as Teleon INFRA.

Defines the environment ``environment.baltor.cfpb_context_governance.local@v1``: a deterministic, offline
governed-context task that MEASURES whether a candidate answer to a Reg E question is correct AND governed.

The task (synthetic, from ``demo-data/cfpb-sample``): a consumer asks the EFT-error provisional-credit
resolution deadline. The authoritative answer (Reg E §1005.11) is **"10 business days"** (extendable to 45
calendar days with provisional credit). A stale internal FAQ says **"30 days"** — that is the HELD-OUT
CONTRADICTION that must NOT be served. A good answer states the authoritative value, carries a source handle,
and is backed by a receipt; a bad answer that leaks "30 days" FAILS.

The RewardSpec (kind ``deterministic_check``) enforces, deterministically:
  - ``exact_answer`` substring is present ("10 business days") — the authoritative value;
  - ``held_out_absent`` — "30 days" is NOT served (the stale contradiction is held out, never served);
  - ``key_present`` — a ``source_handles`` provenance handle is present on the answer;
  - the run carries a receipt (provenance) and the agent output is never marked truth.

This module is Teleon infra modeling a Baltor-style task — it **does NOT import src.baltor**. The fixture is
read from ``demo-data/cfpb-sample/seed-graph.json`` when present (reusing the planted facts) and falls back to a
deterministic inline fixture otherwise. Stdlib only; deterministic when ``now`` is injected; offline.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.environments.local_environment_provider import (
    LOCAL_ENVIRONMENT_PROVIDER_ID,
    LocalEnvironmentProvider,
)
from src.teleon.environments.reward_runner import RewardRunner

#: the id of this governed-context environment (local-first; serves_truth False).
ENVIRONMENT_ID = "environment.baltor.cfpb_context_governance.local@v1"
#: the reward spec id for this environment's deterministic checks.
REWARD_SPEC_ID = "reward.baltor.cfpb_context_governance.deterministic@v1"
#: default tenant + agent ids for a run (synthetic).
DEFAULT_TENANT_ID = "tenant.cfpb-demo"
DEFAULT_AGENT_ID = "agent.context-answerer.under-test"

#: THE authoritative answer value (Reg E §1005.11). Single source for the exact_answer check + the stub.
AUTHORITATIVE_ANSWER = "10 business days"
#: the held-out, stale, CONTRADICTING value that must never be served.
HELD_OUT_CONTRADICTION = "30 days"
#: the canonical provenance handle for the authoritative source (from the cfpb-sample seed graph).
AUTHORITATIVE_SOURCE_HANDLE = "ctx://cfpb-sample/regs/RegE-error-resolution.md#decision"

#: where the synthetic seed lives, relative to the repo root (parents[3] = repo root from this file).
_REPO = Path(__file__).resolve().parents[3]
_SEED_PATH = _REPO / "demo-data" / "cfpb-sample" / "seed-graph.json"


def load_fixture(*, seed_path: Path | None = None) -> dict:
    """Return the deterministic task fixture: the question, the authoritative answer + source handle, and the
    held-out contradiction. Reads ``demo-data/cfpb-sample/seed-graph.json`` (the planted Reg E decision object)
    when available; otherwise falls back to an equivalent inline fixture. Never imports Baltor.

    The returned fixture is synthetic + deterministic; it is the GROUND for the reward spec, not served truth.
    """
    question = (
        "A consumer reports an unauthorized EFT. Under Reg E (Regulation E, EFT Act §1005.11), within how many "
        "business days must the institution investigate and resolve the error if it does not provisionally "
        "credit the account?"
    )
    authoritative = AUTHORITATIVE_ANSWER
    source_handle = AUTHORITATIVE_SOURCE_HANDLE
    held_out = HELD_OUT_CONTRADICTION

    path = seed_path if seed_path is not None else _SEED_PATH
    if path.exists():
        try:
            graph = json.loads(path.read_text())
            for obj in graph.get("objects", []):
                if obj.get("context_object_id") == "obj-rege":
                    handles = obj.get("source_handles") or [source_handle]
                    source_handle = handles[0]
                    # The seed's claim is "error_resolution_days = 10 business days"; keep the value substring.
                    if AUTHORITATIVE_ANSWER in str(obj.get("claim", "")):
                        authoritative = AUTHORITATIVE_ANSWER
                    break
        except (json.JSONDecodeError, OSError):
            pass  # fall back to the inline fixture (deterministic; offline-safe).

    return {
        "question": question,
        "authoritative_answer": authoritative,
        "source_handle": source_handle,
        "held_out_contradiction": held_out,
    }


def build_reward_spec(fixture: dict | None = None) -> dict:
    """The deterministic RewardSpec for this environment (kind=deterministic_check). One check per governance
    requirement: authoritative value present, held-out contradiction absent, and a source handle present."""
    fx = fixture if fixture is not None else load_fixture()
    checks = [
        {"check_id": "authoritative_value_present", "type": "substring_present",
         "needle": fx["authoritative_answer"], "weight": 1.0},
        {"check_id": "held_out_contradiction_absent", "type": "held_out_absent",
         "needle": fx["held_out_contradiction"], "weight": 1.0},
        {"check_id": "source_handle_present", "type": "key_present", "key": "source_handles", "weight": 1.0},
    ]
    return {
        "reward_spec_id": REWARD_SPEC_ID,
        "kind": "deterministic_check",
        "checks": checks,
        "max_score": float(len(checks)),
        "requires_execution": False,
    }


def build_request(run_id: str, *, candidate_answer: str, source_handles: list[str] | None = None,
                  fixture: dict | None = None) -> tuple[dict, dict]:
    """Build the ``(EnvironmentRunRequest, candidate_output)`` for a CANDIDATE answer to the Reg E question.

    ``candidate_answer`` is the answer text under measurement; ``source_handles`` is its claimed provenance
    (defaults to the authoritative handle so a well-formed good answer can pass the source-handle check). The
    candidate output is a CANDIDATE proposal (never truth) that the reward spec measures."""
    fx = fixture if fixture is not None else load_fixture()
    handles = source_handles if source_handles is not None else [fx["source_handle"]]
    request = {
        "schema_version": "v1",
        "run_id": run_id,
        "environment_id": ENVIRONMENT_ID,
        "agent_id": DEFAULT_AGENT_ID,
        "tenant_id": DEFAULT_TENANT_ID,
        "input_ref": None,
        "input": {"question": fx["question"]},
        "max_steps": 4,
        "timeout_ms": 30000,
        "reward_spec_id": REWARD_SPEC_ID,
        "require_receipt": True,
    }
    candidate_output = {"answer": candidate_answer, "source_handles": list(handles)}
    return request, candidate_output


def run_candidate(run_id: str, *, candidate_answer: str, now: str,
                  source_handles: list[str] | None = None,
                  provider: LocalEnvironmentProvider | None = None,
                  scorer: RewardRunner | None = None,
                  fixture: dict | None = None) -> dict:
    """Run a CANDIDATE answer through the LOCAL environment + the deterministic RewardRunner.

    Returns ``{"result": <EnvironmentRunResult>, "reward": <RewardResult>, "receipt": <EnvironmentRunReceipt>}``.
    The result's ``serves_truth`` and the reward's ``is_truth`` are both False — the candidate answer is
    MEASURED, never served — and a leaked held-out "30 days" fails the ``held_out_absent`` check. The receipt's
    ``reward_result_id`` is back-filled with the score's id (provenance links the measurement to the run).

    Deterministic for fixed (run_id, candidate_answer, now, source_handles). Offline; never imports Baltor.
    """
    env = provider if provider is not None else LocalEnvironmentProvider()
    rew = scorer if scorer is not None else RewardRunner()
    fx = fixture if fixture is not None else load_fixture()

    request, candidate_output = build_request(run_id, candidate_answer=candidate_answer,
                                              source_handles=source_handles, fixture=fx)
    run = env.run(request, now=now, candidate_output=candidate_output)
    result = run["result"]
    receipt = run["receipt"]

    reward_spec = build_reward_spec(fx)
    reward = rew.score(result, reward_spec, now=now)

    # Link the measurement back into the run result + receipt (lineage; no truth assertion).
    result["reward_result_id"] = reward["reward_result_id"]
    receipt["reward_result_id"] = reward["reward_result_id"]

    return {"result": result, "reward": reward, "receipt": receipt}


def describe() -> dict:
    """EnvironmentProviderNode-style card for this governed-context environment (local-first; serves_truth False)."""
    return {
        "provider_id": ENVIRONMENT_ID,
        "name": "baltor-cfpb-context-governance (local)",
        "status": "active",
        "requires_docker": False,
        "requires_network": False,
        "local_equivalent": LOCAL_ENVIRONMENT_PROVIDER_ID,
        "serves_truth": False,
        "reward_spec_id": REWARD_SPEC_ID,
        "models": "a Baltor-style governed-context task as Teleon infra; does not import src.baltor",
    }


__all__ = [
    "ENVIRONMENT_ID", "REWARD_SPEC_ID", "AUTHORITATIVE_ANSWER", "HELD_OUT_CONTRADICTION",
    "AUTHORITATIVE_SOURCE_HANDLE", "DEFAULT_TENANT_ID", "DEFAULT_AGENT_ID",
    "load_fixture", "build_reward_spec", "build_request", "run_candidate", "describe",
]
