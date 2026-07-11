#!/usr/bin/env python3
"""Offline, deterministic long-session benchmark for the semantic linker.

This harness compares four ways to solve the *same* repository task:

``agent_only``
    A scripted stand-in for an agent reads a large working set, writes the
    implementation, observes a real hidden-oracle failure, and repairs it.
``text_retrieval``
    The stand-in retrieves a long prose/source reference and still emits the
    complete implementation.
``semantic_compose``
    The stand-in emits a compact capability plan.  A deterministic resolver
    binds and materializes a verified recipe; no residual source is authored.
``partial_gapfill``
    Verified infrastructure is materialized and the stand-in authors only a
    small typed business-rule gap.

The hidden oracles really execute every materialized result.  The agent turns,
however, are deliberately deterministic fixtures and their token counts use a
clearly labelled characters-per-token proxy.  Consequently these rows are
useful for testing benchmark mechanics and the input-token compounding
hypothesis, but they are never live-model evidence and never headline eligible.

The append-only JSONL ledger is resumable by a protocol-fingerprinted run key.
The harness checks at least ``REPORTING_MIN_N`` rows in every underlying exact
model/task/lane cell, but deterministic repeats are explicitly pseudo-replicates
rather than independent evidence, so this offline proxy is never reportable or
headline eligible. Savings diagnostics use matched both-pass pairs only;
both-fail pairs are explicitly inconclusive.

    python3 scripts/semantic_linker_long_session_benchmark.py --self-test
    python3 scripts/semantic_linker_long_session_benchmark.py --demo

serves_truth=false; candidate=true.
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next(
    (q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
    _here_boot.parents[1],
)
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import dataclasses  # noqa: E402
import hashlib  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import statistics  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from collections import defaultdict  # noqa: E402
from typing import Any, Iterable  # noqa: E402

from scripts.reuse_experiment_policy import REPORTING_MIN_N  # noqa: E402


BOUNDARY: dict[str, bool] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "semantic_linker_long_session_offline"
EVIDENCE_SCOPE = "offline_deterministic_simulation"
TOKEN_ACCOUNTING = "chars_per_token_proxy"
TOKEN_PROXY_CHARS = 4
DEFAULT_MODEL = "offline-scripted"
DEFAULT_LEDGER = resource("data/dev-intel/semantic_linker_long_session_benchmark/runs.jsonl")
ORACLE_TIMEOUT_SECONDS = 15
REPEAT_DESIGN = "deterministic_fixture_reexecution_pseudo_replication"
STATISTICAL_INDEPENDENCE_CLAIMED = False

LANE_AGENT_ONLY = "agent_only"
LANE_TEXT_RETRIEVAL = "text_retrieval"
LANE_SEMANTIC_COMPOSE = "semantic_compose"
LANE_PARTIAL_GAPFILL = "partial_gapfill"
LANES = (
    LANE_AGENT_ONLY,
    LANE_TEXT_RETRIEVAL,
    LANE_SEMANTIC_COMPOSE,
    LANE_PARTIAL_GAPFILL,
)
BASELINE_LANE = LANE_AGENT_ONLY
TREATMENT_LANES = tuple(lane for lane in LANES if lane != BASELINE_LANE)

SESSION_SYSTEM = (
    "You are modifying an existing repository. Use one compact tool action per turn, preserve unrelated files, "
    "run the hidden contract tests, and stop only after they pass."
)

_PROTECTED_ORACLE_RUNNER = r'''import contextlib
import io
import json
import os
import sys

oracle_path = sys.argv[1]
receipt_fd = int(sys.argv[2])
expected_checks = tuple(json.loads(sys.argv[3]))
trusted_write = os.write
trusted_fsync = os.fsync
trusted_dumps = json.dumps
sys.path.insert(0, os.getcwd())
scope = {}
captured_stdout = io.StringIO()
captured_stderr = io.StringIO()
with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stderr):
    source = open(oracle_path, encoding="utf-8").read()
    exec(compile(source, oracle_path, "exec"), scope)
payload = scope.get("oracle_payload")
checks = payload.get("checks") if isinstance(payload, dict) else None
observations = payload.get("observations") if isinstance(payload, dict) else None
schema_valid = (
    isinstance(checks, dict)
    and tuple(sorted(checks)) == tuple(sorted(expected_checks))
    and all(isinstance(value, bool) for value in checks.values())
    and isinstance(observations, dict)
    and isinstance(payload.get("oracle_pass"), bool)
    and payload["oracle_pass"] == all(checks.values())
)
if not schema_valid:
    raise SystemExit(70)
encoded = trusted_dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
trusted_write(receipt_fd, encoded)
trusted_fsync(receipt_fd)
raise SystemExit(0 if payload["oracle_pass"] else 3)
'''


@dataclasses.dataclass(frozen=True)
class TaskSpec:
    """One task shared unchanged across all four benchmark lanes."""

    task_id: str
    family: str
    goal: str
    initial_files: dict[str, str]
    faulty_files: dict[str, str]
    full_solution_files: dict[str, str]
    semantic_files: dict[str, str]
    partial_files: dict[str, str]
    partial_residual_files: tuple[str, ...]
    semantic_plan: str
    compact_cards: str
    retrieved_reference: str
    oracle_source: str
    oracle_check_names: tuple[str, ...]
    adapter_counts: dict[str, int]


_EVENT_INITIAL = '''def process_event(secret, body, signature_hex, seen):
    """TODO: authenticate, decode, and deduplicate an event."""
    return {"status": "accepted"}
'''

_EVENT_FAULTY = '''import json


def process_event(secret, body, signature_hex, seen):
    """Faulty first attempt: parses events but does not authenticate them."""
    event = json.loads(body.decode("utf-8"))
    event_id = event.get("event_id")
    if event_id in seen:
        return {"status": "duplicate", "event_id": event_id}
    seen.add(event_id)
    return {"status": "accepted", "event_id": event_id}
'''

_EVENT_FULL = '''import hashlib
import hmac
import json


def process_event(secret, body, signature_hex, seen):
    """Authenticate, decode, validate, and idempotently accept one event."""
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_hex or ""):
        return {"status": "rejected", "reason": "bad_signature"}
    try:
        event = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"status": "rejected", "reason": "invalid_json"}
    event_id = event.get("event_id") if isinstance(event, dict) else None
    if not isinstance(event_id, str) or not event_id:
        return {"status": "rejected", "reason": "missing_event_id"}
    if event_id in seen:
        return {"status": "duplicate", "event_id": event_id}
    seen.add(event_id)
    return {"status": "accepted", "event_id": event_id}
'''

_EVENT_SEMANTIC_BUNDLE = _EVENT_FULL.replace("def process_event", "def signed_idempotent_ingest")
_EVENT_SEMANTIC_APP = '''from verified_recipe import signed_idempotent_ingest


process_event = signed_idempotent_ingest
'''

_EVENT_PARTIAL_CORE = '''import hashlib
import hmac
import json


def verify_and_decode(secret, body, signature_hex):
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_hex or ""):
        return None, "bad_signature"
    try:
        event = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "invalid_json"
    event_id = event.get("event_id") if isinstance(event, dict) else None
    if not isinstance(event_id, str) or not event_id:
        return None, "missing_event_id"
    return event, None
'''

_EVENT_GAP = '''def decide_unique_event(event, seen):
    event_id = event["event_id"]
    if event_id in seen:
        return {"status": "duplicate", "event_id": event_id}
    seen.add(event_id)
    return {"status": "accepted", "event_id": event_id}
'''

_EVENT_PARTIAL_APP = '''from event_gap import decide_unique_event
from verified_event_core import verify_and_decode


def process_event(secret, body, signature_hex, seen):
    event, error = verify_and_decode(secret, body, signature_hex)
    if error:
        return {"status": "rejected", "reason": error}
    return decide_unique_event(event, seen)
'''

_EVENT_ORACLE = r'''import hashlib
import hmac
import json

scope = {}
exec(compile(open("app.py", encoding="utf-8").read(), "app.py", "exec"), scope)
process_event = scope["process_event"]
secret = "oracle-secret"
body = json.dumps({"event_id": "evt-7", "amount": 13}, separators=(",", ":")).encode()
good = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
seen = set()
bad = process_event(secret, body, "deadbeef", seen)
after_bad = sorted(seen)
accepted = process_event(secret, body, good, seen)
duplicate = process_event(secret, body, good, seen)
invalid_body = b"not-json"
invalid_sig = hmac.new(secret.encode(), invalid_body, hashlib.sha256).hexdigest()
invalid = process_event(secret, invalid_body, invalid_sig, seen)
missing_body = json.dumps({"amount": 9}, separators=(",", ":")).encode()
missing_sig = hmac.new(secret.encode(), missing_body, hashlib.sha256).hexdigest()
missing = process_event(secret, missing_body, missing_sig, seen)
checks = {
    "bad_signature_rejected": bad == {"status": "rejected", "reason": "bad_signature"},
    "bad_signature_no_effect": after_bad == [],
    "valid_event_accepted": accepted == {"status": "accepted", "event_id": "evt-7"},
    "duplicate_idempotent": duplicate == {"status": "duplicate", "event_id": "evt-7"},
    "one_event_reserved": seen == {"evt-7"},
    "invalid_json_rejected": invalid == {"status": "rejected", "reason": "invalid_json"},
    "missing_id_rejected": missing == {"status": "rejected", "reason": "missing_event_id"},
}
observations = {"bad": bad, "accepted": accepted, "duplicate": duplicate,
                "invalid": invalid, "missing": missing, "seen": sorted(seen)}
oracle_payload = {"checks": checks, "observations": observations,
                  "oracle_pass": all(checks.values())}
'''


_RETRY_INITIAL = '''def execute(operation, max_attempts=3):
    """TODO: bounded retry with retryable/permanent error semantics."""
    return {"status": "failed", "attempts": 0, "error": "not_implemented"}
'''

_RETRY_FAULTY = '''def execute(operation, max_attempts=3):
    """Faulty first attempt: retries every exception, including permanent ones."""
    for attempt in range(1, max_attempts + 1):
        try:
            return {"status": "ok", "value": operation(), "attempts": attempt}
        except Exception as error:
            if attempt == max_attempts:
                return {"status": "failed", "attempts": attempt, "error": type(error).__name__}
'''

_RETRY_FULL = '''def execute(operation, max_attempts=3):
    """Run an operation with bounded retries for transient failures only."""
    if max_attempts < 1:
        return {"status": "failed", "attempts": 0, "error": "InvalidAttempts"}
    for attempt in range(1, max_attempts + 1):
        try:
            return {"status": "ok", "value": operation(), "attempts": attempt}
        except (TimeoutError, ConnectionError) as error:
            if attempt == max_attempts:
                return {"status": "failed", "attempts": attempt, "error": type(error).__name__}
        except Exception as error:
            return {"status": "failed", "attempts": attempt, "error": type(error).__name__}
    raise AssertionError("unreachable")
'''

_RETRY_SEMANTIC_BUNDLE = _RETRY_FULL.replace("def execute", "def bounded_transient_retry")
_RETRY_SEMANTIC_APP = '''from verified_recipe import bounded_transient_retry


execute = bounded_transient_retry
'''

_RETRY_PARTIAL_CORE = '''def run_with_policy(operation, should_retry, max_attempts):
    if max_attempts < 1:
        return {"status": "failed", "attempts": 0, "error": "InvalidAttempts"}
    for attempt in range(1, max_attempts + 1):
        try:
            return {"status": "ok", "value": operation(), "attempts": attempt}
        except Exception as error:
            if not should_retry(error) or attempt == max_attempts:
                return {"status": "failed", "attempts": attempt, "error": type(error).__name__}
    raise AssertionError("unreachable")
'''

_RETRY_GAP = '''def is_retryable(error):
    return isinstance(error, (TimeoutError, ConnectionError))
'''

_RETRY_PARTIAL_APP = '''from retry_gap import is_retryable
from verified_retry_core import run_with_policy


def execute(operation, max_attempts=3):
    return run_with_policy(operation, is_retryable, max_attempts)
'''

_RETRY_ORACLE = r'''import json

scope = {}
exec(compile(open("app.py", encoding="utf-8").read(), "app.py", "exec"), scope)
execute = scope["execute"]

transient_calls = []
def transient_then_ok():
    transient_calls.append(len(transient_calls) + 1)
    if len(transient_calls) < 3:
        raise TimeoutError("temporary")
    return 17

permanent_calls = []
def permanent():
    permanent_calls.append(len(permanent_calls) + 1)
    raise ValueError("invalid")

exhausted_calls = []
def exhausted():
    exhausted_calls.append(len(exhausted_calls) + 1)
    raise ConnectionError("offline")

success = execute(transient_then_ok, 3)
permanent_result = execute(permanent, 5)
exhausted_result = execute(exhausted, 2)
invalid_result = execute(lambda: 1, 0)
checks = {
    "transient_eventually_succeeds": success == {"status": "ok", "value": 17, "attempts": 3},
    "transient_attempt_count": len(transient_calls) == 3,
    "permanent_not_retried": permanent_result == {"status": "failed", "attempts": 1, "error": "ValueError"}
                             and len(permanent_calls) == 1,
    "retry_limit_enforced": exhausted_result == {"status": "failed", "attempts": 2,
                                                   "error": "ConnectionError"}
                            and len(exhausted_calls) == 2,
    "invalid_limit_rejected": invalid_result == {"status": "failed", "attempts": 0,
                                                  "error": "InvalidAttempts"},
}
observations = {"success": success, "permanent": permanent_result,
                "exhausted": exhausted_result, "invalid": invalid_result}
oracle_payload = {"checks": checks, "observations": observations,
                  "oracle_pass": all(checks.values())}
'''


def _tasks() -> tuple[TaskSpec, ...]:
    """Build the immutable task registry from the source constants above."""

    return (
        TaskSpec(
            task_id="signed-idempotent-event-ingest",
            family="authenticated-event-processing",
            goal=(
                "Implement process_event(secret, body, signature_hex, seen). Verify HMAC-SHA256 with a "
                "constant-time comparison before JSON decoding or mutation; reject malformed/missing IDs; "
                "accept each event_id once and report duplicates without a second mutation."
            ),
            initial_files={"app.py": _EVENT_INITIAL},
            faulty_files={"app.py": _EVENT_FAULTY},
            full_solution_files={"app.py": _EVENT_FULL},
            semantic_files={"verified_recipe.py": _EVENT_SEMANTIC_BUNDLE, "app.py": _EVENT_SEMANTIC_APP},
            partial_files={
                "verified_event_core.py": _EVENT_PARTIAL_CORE,
                "event_gap.py": _EVENT_GAP,
                "app.py": _EVENT_PARTIAL_APP,
            },
            partial_residual_files=("event_gap.py",),
            semantic_plan=(
                "goal process_event\n"
                "bind security.hmac_verify_decode -> events.reserve_once\n"
                "on bad_signature|invalid_json|missing_event_id -> rejected\n"
                "verify signed-idempotent-event-ingest"
            ),
            compact_cards=(
                "p1 security.hmac_verify_decode: Secret + bytes + hex -> Event | AuthOrDecodeError; "
                "effects:none; trust:A\n"
                "p2 events.reserve_once: Event + MutableIdSet -> Accepted | Duplicate; effects:set-write; trust:A"
            ),
            retrieved_reference=(
                "Reference implementation and integration note:\n" + _EVENT_FULL
                + "\nThe caller must preserve byte identity, compare digests in constant time, decode only after "
                "authentication, reject missing IDs, and mutate the idempotency set exactly once.\n"
            ),
            oracle_source=_EVENT_ORACLE,
            oracle_check_names=(
                "bad_signature_rejected",
                "bad_signature_no_effect",
                "valid_event_accepted",
                "duplicate_idempotent",
                "one_event_reserved",
                "invalid_json_rejected",
                "missing_id_rejected",
            ),
            adapter_counts={
                LANE_AGENT_ONLY: 0,
                LANE_TEXT_RETRIEVAL: 0,
                LANE_SEMANTIC_COMPOSE: 1,
                LANE_PARTIAL_GAPFILL: 2,
            },
        ),
        TaskSpec(
            task_id="bounded-transient-retry",
            family="reliable-operation-execution",
            goal=(
                "Implement execute(operation, max_attempts=3). Retry TimeoutError and ConnectionError only, "
                "return permanent failures immediately, enforce the attempt bound, and reject non-positive limits."
            ),
            initial_files={"app.py": _RETRY_INITIAL},
            faulty_files={"app.py": _RETRY_FAULTY},
            full_solution_files={"app.py": _RETRY_FULL},
            semantic_files={"verified_recipe.py": _RETRY_SEMANTIC_BUNDLE, "app.py": _RETRY_SEMANTIC_APP},
            partial_files={
                "verified_retry_core.py": _RETRY_PARTIAL_CORE,
                "retry_gap.py": _RETRY_GAP,
                "app.py": _RETRY_PARTIAL_APP,
            },
            partial_residual_files=("retry_gap.py",),
            semantic_plan=(
                "goal execute\n"
                "bind retry.bounded_loop(policy=errors.transient_only, max=max_attempts)\n"
                "on invalid_attempts -> failed(0)\n"
                "verify bounded-transient-retry"
            ),
            compact_cards=(
                "p1 retry.bounded_loop: Operation + RetryPolicy + PositiveInt -> Result; effects:operation; trust:A\n"
                "p2 errors.transient_only: Exception -> bool; TimeoutError|ConnectionError only; trust:A"
            ),
            retrieved_reference=(
                "Reference implementation and integration note:\n" + _RETRY_FULL
                + "\nRetry only declared transient exception classes. Permanent exceptions terminate on the first "
                "attempt. max_attempts is a total-attempt limit, not a retry count.\n"
            ),
            oracle_source=_RETRY_ORACLE,
            oracle_check_names=(
                "transient_eventually_succeeds",
                "transient_attempt_count",
                "permanent_not_retried",
                "retry_limit_enforced",
                "invalid_limit_rejected",
            ),
            adapter_counts={
                LANE_AGENT_ONLY: 0,
                LANE_TEXT_RETRIEVAL: 0,
                LANE_SEMANTIC_COMPOSE: 1,
                LANE_PARTIAL_GAPFILL: 1,
            },
        ),
    )


TASKS = _tasks()
TASK_BY_ID = {task.task_id: task for task in TASKS}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: Any) -> str:
    text = value if isinstance(value, str) else _canonical_json(value)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _protocol_payload() -> dict[str, Any]:
    return {
        "benchmark_kind": BENCHMARK_KIND,
        "evidence_scope": EVIDENCE_SCOPE,
        "token_accounting": TOKEN_ACCOUNTING,
        "token_proxy_chars": TOKEN_PROXY_CHARS,
        "session_system": SESSION_SYSTEM,
        "repeat_design": REPEAT_DESIGN,
        "statistical_independence_claimed": STATISTICAL_INDEPENDENCE_CLAIMED,
        "protected_oracle_runner_digest": _digest(_PROTECTED_ORACLE_RUNNER),
        "lanes": LANES,
        "tasks": [
            {
                "task_id": task.task_id,
                "family": task.family,
                "goal": task.goal,
                "initial_digest": _digest(task.initial_files),
                "faulty_digest": _digest(task.faulty_files),
                "full_digest": _digest(task.full_solution_files),
                "semantic_digest": _digest(task.semantic_files),
                "partial_digest": _digest(task.partial_files),
                "partial_residual_files": task.partial_residual_files,
                "semantic_plan_digest": _digest(task.semantic_plan),
                "compact_cards_digest": _digest(task.compact_cards),
                "retrieved_reference_digest": _digest(task.retrieved_reference),
                "oracle_digest": _digest(task.oracle_source),
                "oracle_checks": task.oracle_check_names,
                "adapter_counts": task.adapter_counts,
                "generated_repository_context_digest": _digest(_repository_context(task)),
                "generated_workspace_profile_digest": _digest(_compact_workspace_profile(task)),
                "token_bearing_lane_inputs": {
                    lane: _token_bearing_lane_inputs(task, lane)
                    for lane in LANES
                },
            }
            for task in TASKS
        ],
        "token_transcript_generator_digests": {
            function.__name__: _digest(inspect.getsource(function))
            for function in (
                _proxy_tokens,
                _repository_context,
                _compact_workspace_profile,
                _code_write,
                _run_hidden_oracle,
                run_fixture,
            )
        },
        "reporting_min_n": REPORTING_MIN_N,
    }


PROTOCOL_DIGEST: str


def _proxy_tokens(text: str) -> int:
    """Ceiling characters-per-token proxy; never presented as provider usage."""

    return (len(text) + TOKEN_PROXY_CHARS - 1) // TOKEN_PROXY_CHARS


def _source_loc(source: str) -> int:
    return sum(1 for line in source.splitlines() if line.strip() and not line.lstrip().startswith("#"))


def _workspace_text(files: dict[str, str]) -> str:
    return "\n".join(f"===== {name} =====\n{files[name]}" for name in sorted(files))


def _line_edit_distance(before: dict[str, str], after: dict[str, str]) -> int:
    """Line-level insert/delete/replace distance between two workspaces."""

    left = _workspace_text(before).splitlines()
    right = _workspace_text(after).splitlines()
    previous = list(range(len(right) + 1))
    for i, left_line in enumerate(left, start=1):
        current = [i]
        for j, right_line in enumerate(right, start=1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (left_line != right_line),
            ))
        previous = current
    return previous[-1]


def _repository_context(task: TaskSpec) -> str:
    """Deterministic, realistically repetitive context used only by the proxy fixture."""

    sections: list[str] = []
    concerns = (
        "request boundary and validation",
        "domain service and state transition",
        "error translation and observability",
        "repository conventions and tests",
        "security policy and secret handling",
        "deployment configuration and rollback",
        "compatibility aliases and migrations",
        "integration call sites and examples",
    )
    for index, concern in enumerate(concerns):
        lines = [
            f"module_{index:02d}.py — {concern}",
            f"Task family: {task.family}. This module is existing context and must remain behaviorally stable.",
        ]
        lines.extend(
            f"Existing contract {index:02d}.{line:02d}: preserve typed inputs, explicit errors, effects, "
            f"privacy boundary, and deterministic receipt for {concern}."
            for line in range(18)
        )
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def _compact_workspace_profile(task: TaskSpec) -> str:
    return (
        f"language=python; task_family={task.family}; files={','.join(sorted(task.initial_files))}; "
        "stdlib_only=true; tests=hidden_contract; effects=local_memory; policy=no_network,no_secrets_in_logs"
    )


def _token_bearing_lane_inputs(task: TaskSpec, lane: str) -> dict[str, Any]:
    """Inventory every deterministic input/configuration that can affect transcript tokens.

    Oracle receipts are outcome-derived rather than static inputs.  Their generator,
    oracle source, declared check names, and candidate artifacts are all separately
    included in the protocol payload, so changing any receipt-bearing input changes
    the protocol digest.
    """

    common: dict[str, Any] = {
        "initial_conversation": f"SYSTEM: {SESSION_SYSTEM}\nUSER: {task.goal}\n",
        "initial_workspace": _workspace_text(task.initial_files),
        "test_action": "TEST",
        "done_action": "DONE",
        "done_result": "session_complete",
        "oracle_check_names": task.oracle_check_names,
        "oracle_source_digest": _digest(task.oracle_source),
    }
    if lane == LANE_AGENT_ONLY:
        common["turn_inputs"] = (
            ("WORKSPACE_SCAN --include-source", _repository_context(task)),
            ("READ app.py", task.initial_files["app.py"]),
            (_code_write(task.faulty_files), "write_ok"),
            (_code_write(task.full_solution_files), "write_ok"),
        )
    elif lane == LANE_TEXT_RETRIEVAL:
        common["turn_inputs"] = (
            ("WORKSPACE_SCAN --include-source", _repository_context(task)),
            ("TEXT_SEARCH " + task.task_id, task.retrieved_reference),
            (_code_write(task.full_solution_files), "write_ok"),
        )
    elif lane == LANE_SEMANTIC_COMPOSE:
        materialized = dict(task.semantic_files)
        common["turn_inputs"] = (
            ("WORKSPACE_PROFILE", _compact_workspace_profile(task)),
            ("PRIMITIVE_SEARCH " + task.task_id, task.compact_cards),
            ("GRAPH_PLAN\n" + task.semantic_plan, "graph_valid"),
            ("GRAPH_APPLY", _canonical_json({
                "materialized_files": sorted(materialized),
                "artifact_digest": _digest(materialized),
                "residual_files": [],
            })),
        )
    elif lane == LANE_PARTIAL_GAPFILL:
        materialized = dict(task.partial_files)
        residual = _authored_files(task, lane)
        edge_contract = (
            "verified infrastructure already materialized; author only: "
            + ",".join(task.partial_residual_files)
            + "; all other source is read-only"
        )
        common["turn_inputs"] = (
            ("WORKSPACE_PROFILE", _compact_workspace_profile(task)),
            ("PRIMITIVE_SEARCH " + task.task_id, task.compact_cards),
            ("PRIMITIVE_EXPAND --level contract", edge_contract),
            (_code_write(residual), "gap_write_ok"),
            ("GRAPH_APPLY", _canonical_json({
                "materialized_files": sorted(materialized),
                "artifact_digest": _digest(materialized),
                "residual_files": sorted(residual),
            })),
        )
    else:
        raise ValueError(f"unknown lane: {lane}")
    return common


def _run_hidden_oracle(files: dict[str, str], task: TaskSpec) -> dict[str, Any]:
    """Execute an oracle whose evidence channel is isolated from candidate stdout.

    Candidate files live in one temporary directory.  The trusted runner and an
    unlinked receipt file live in a separate evaluator directory.  Candidate
    stdout/stderr is ignored as evidence, and a pass requires both a valid
    protected receipt and a zero subprocess return code.
    """

    with (
        tempfile.TemporaryDirectory(prefix="semantic-linker-candidate-") as workspace,
        tempfile.TemporaryDirectory(prefix="semantic-linker-evaluator-") as evaluator,
    ):
        root = Path(workspace)
        evaluator_root = Path(evaluator)
        for name, source in files.items():
            candidate = Path(name)
            if candidate.is_absolute() or ".." in candidate.parts:
                return {"oracle_pass": False, "checks": {}, "observations": {}, "error": "unsafe_path"}
            target = root / candidate
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding="utf-8")
        oracle_path = evaluator_root / "hidden_oracle.py"
        runner_path = evaluator_root / "protected_runner.py"
        oracle_path.write_text(task.oracle_source, encoding="utf-8")
        runner_path.write_text(_PROTECTED_ORACLE_RUNNER, encoding="utf-8")
        oracle_path.chmod(0o400)
        runner_path.chmod(0o400)
        env = {
            "PATH": os.environ.get("PATH", ""),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        with tempfile.TemporaryFile(mode="w+b", dir=evaluator_root) as protected_receipt:
            try:
                proc = subprocess.run(
                    [
                        sys.executable,
                        "-I",
                        str(runner_path),
                        str(oracle_path),
                        str(protected_receipt.fileno()),
                        _canonical_json(task.oracle_check_names),
                    ],
                    cwd=root,
                    env=env,
                    pass_fds=(protected_receipt.fileno(),),
                    capture_output=True,
                    text=True,
                    timeout=ORACLE_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired:
                return {
                    "oracle_pass": False,
                    "checks": {},
                    "observations": {},
                    "error": "timeout",
                    "receipt_channel": "protected_unlinked_file_descriptor",
                    "subprocess_returncode": None,
                }
            protected_receipt.seek(0)
            raw_receipt = protected_receipt.read().decode("utf-8", errors="strict")
        try:
            receipt = json.loads(raw_receipt) if raw_receipt else {}
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
            receipt = {}
        checks = receipt.get("checks") if isinstance(receipt, dict) else None
        observations = receipt.get("observations") if isinstance(receipt, dict) else None
        schema_valid = (
            isinstance(checks, dict)
            and tuple(sorted(checks)) == tuple(sorted(task.oracle_check_names))
            and all(isinstance(value, bool) for value in checks.values())
            and isinstance(observations, dict)
            and isinstance(receipt.get("oracle_pass"), bool)
            and receipt["oracle_pass"] == all(checks.values())
        )
        if not schema_valid:
            return {
                "oracle_pass": False,
                "checks": {},
                "observations": {},
                "error": "invalid_oracle_receipt",
                "stderr_tail": proc.stderr[-300:],
                "receipt_channel": "protected_unlinked_file_descriptor",
                "subprocess_returncode": proc.returncode,
            }
        process_succeeded = proc.returncode == 0
        oracle_pass = bool(process_succeeded and receipt["oracle_pass"])
        error = None
        if not process_succeeded:
            error = "oracle_checks_failed" if receipt["oracle_pass"] is False else "oracle_subprocess_nonzero"
        return {
            "oracle_pass": oracle_pass,
            "checks": checks,
            "observations": observations,
            "behavior_digest": _digest(observations),
            "error": error,
            "stderr_tail": proc.stderr[-300:] if not oracle_pass else "",
            "receipt_channel": "protected_unlinked_file_descriptor",
            "subprocess_returncode": proc.returncode,
        }


def _final_files(task: TaskSpec, lane: str) -> dict[str, str]:
    if lane in {LANE_AGENT_ONLY, LANE_TEXT_RETRIEVAL}:
        return dict(task.full_solution_files)
    if lane == LANE_SEMANTIC_COMPOSE:
        return dict(task.semantic_files)
    if lane == LANE_PARTIAL_GAPFILL:
        return dict(task.partial_files)
    raise ValueError(f"unknown lane: {lane}")


def _authored_files(task: TaskSpec, lane: str) -> dict[str, str]:
    if lane in {LANE_AGENT_ONLY, LANE_TEXT_RETRIEVAL}:
        return dict(task.full_solution_files)
    if lane == LANE_SEMANTIC_COMPOSE:
        return {}
    if lane == LANE_PARTIAL_GAPFILL:
        return {name: task.partial_files[name] for name in task.partial_residual_files}
    raise ValueError(f"unknown lane: {lane}")


def _code_write(files: dict[str, str]) -> str:
    pieces = []
    for name in sorted(files):
        pieces.append(f"WRITE {name}\n```python\n{files[name]}```")
    return "\n".join(pieces)


def _run_key(model: str, task: TaskSpec, lane: str, repeat: int) -> str:
    return _digest({
        "protocol_digest": PROTOCOL_DIGEST,
        "model": model,
        "task_id": task.task_id,
        "lane": lane,
        "repeat": repeat,
    })


def run_fixture(task: TaskSpec, lane: str, model: str, repeat: int) -> dict[str, Any]:
    """Run one deterministic simulated session and real hidden oracle(s)."""

    if lane not in LANES:
        raise ValueError(f"unknown lane: {lane}")
    if repeat < 0:
        raise ValueError("repeat must be non-negative")

    started = time.perf_counter()
    conversation = f"SYSTEM: {SESSION_SYSTEM}\nUSER: {task.goal}\n"
    turn_log: list[dict[str, Any]] = []
    total_input_tokens = 0
    total_output_tokens = 0
    workspace = dict(task.initial_files)
    oracle_results: list[dict[str, Any]] = []
    failed_test_seen = False
    repair_turns = 0
    time_to_pass_seconds: float | None = None

    def turn(output: str, tool_result: str, *, tool: str) -> None:
        nonlocal conversation, total_input_tokens, total_output_tokens
        input_tokens = _proxy_tokens(conversation)
        output_tokens = _proxy_tokens(output)
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens
        turn_log.append({
            "turn": len(turn_log) + 1,
            "tool": tool,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_chars": len(conversation),
            "output_chars": len(output),
            "input_digest": _digest(conversation),
            "output_digest": _digest(output),
            "tool_result_digest": _digest(tool_result),
            "token_accounting": TOKEN_ACCOUNTING,
        })
        conversation += f"\nASSISTANT: {output}\nTOOL_RESULT: {tool_result}\n"

    def test_turn() -> dict[str, Any]:
        nonlocal failed_test_seen, time_to_pass_seconds
        result = _run_hidden_oracle(workspace, task)
        oracle_results.append(result)
        if result["oracle_pass"] is True and time_to_pass_seconds is None:
            time_to_pass_seconds = time.perf_counter() - started
        if result["oracle_pass"] is False:
            failed_test_seen = True
        compact = {
            "oracle_pass": result["oracle_pass"],
            "checks": result["checks"],
            "behavior_digest": result.get("behavior_digest"),
            "error": result.get("error"),
        }
        turn("TEST", _canonical_json(compact), tool="test")
        return result

    if lane == LANE_AGENT_ONLY:
        turn("WORKSPACE_SCAN --include-source", _repository_context(task), tool="workspace_scan")
        turn("READ app.py", workspace["app.py"], tool="read")
        workspace = dict(task.faulty_files)
        turn(_code_write(task.faulty_files), "write_ok", tool="write")
        first_result = test_turn()
        if first_result["oracle_pass"] is not True:
            repair_turns += 1
            workspace = dict(task.full_solution_files)
            turn(_code_write(task.full_solution_files), "write_ok", tool="write_repair")
            test_turn()
        turn("DONE", "session_complete", tool="done")
    elif lane == LANE_TEXT_RETRIEVAL:
        turn("WORKSPACE_SCAN --include-source", _repository_context(task), tool="workspace_scan")
        turn("TEXT_SEARCH " + task.task_id, task.retrieved_reference, tool="text_search")
        workspace = dict(task.full_solution_files)
        turn(_code_write(task.full_solution_files), "write_ok", tool="write")
        test_turn()
        turn("DONE", "session_complete", tool="done")
    elif lane == LANE_SEMANTIC_COMPOSE:
        turn("WORKSPACE_PROFILE", _compact_workspace_profile(task), tool="workspace_profile")
        turn("PRIMITIVE_SEARCH " + task.task_id, task.compact_cards, tool="primitive_search")
        turn("GRAPH_PLAN\n" + task.semantic_plan, "graph_valid", tool="graph_plan")
        workspace = dict(task.semantic_files)
        binding_receipt = {
            "materialized_files": sorted(workspace),
            "artifact_digest": _digest(workspace),
            "residual_files": [],
        }
        turn("GRAPH_APPLY", _canonical_json(binding_receipt), tool="graph_apply")
        test_turn()
        turn("DONE", "session_complete", tool="done")
    else:
        turn("WORKSPACE_PROFILE", _compact_workspace_profile(task), tool="workspace_profile")
        turn("PRIMITIVE_SEARCH " + task.task_id, task.compact_cards, tool="primitive_search")
        edge_contract = (
            "verified infrastructure already materialized; author only: "
            + ",".join(task.partial_residual_files)
            + "; all other source is read-only"
        )
        turn("PRIMITIVE_EXPAND --level contract", edge_contract, tool="primitive_expand")
        residual = _authored_files(task, lane)
        turn(_code_write(residual), "gap_write_ok", tool="write_gap")
        workspace = dict(task.partial_files)
        turn("GRAPH_APPLY", _canonical_json({
            "materialized_files": sorted(workspace),
            "artifact_digest": _digest(workspace),
            "residual_files": sorted(residual),
        }), tool="graph_apply")
        test_turn()
        turn("DONE", "session_complete", tool="done")

    final_result = oracle_results[-1]
    final_files = _final_files(task, lane)
    if workspace != final_files:
        raise AssertionError("fixture workspace diverged from declared final files")
    authored = _authored_files(task, lane)
    duration_seconds = time.perf_counter() - started
    first_pass = bool(oracle_results and oracle_results[0]["oracle_pass"] is True)
    reproducible_digest = _digest({
        "protocol_digest": PROTOCOL_DIGEST,
        "task_id": task.task_id,
        "lane": lane,
        "final_files": final_files,
        "semantic_plan": task.semantic_plan if lane == LANE_SEMANTIC_COMPOSE else None,
    })
    trajectory_digest = _digest({
        "protocol_digest": PROTOCOL_DIGEST,
        "model": model,
        "task_id": task.task_id,
        "lane": lane,
        "turn_log": [
            {
                key: turn_row[key]
                for key in (
                    "turn",
                    "tool",
                    "input_tokens",
                    "output_tokens",
                    "input_digest",
                    "output_digest",
                    "tool_result_digest",
                )
            }
            for turn_row in turn_log
        ],
        "oracle_behavior_digest": final_result.get("behavior_digest"),
        "final_artifact_digest": _digest(final_files),
    })
    row: dict[str, Any] = {
        "record_type": "semantic_linker_long_session_run",
        "benchmark_kind": BENCHMARK_KIND,
        "protocol_digest": PROTOCOL_DIGEST,
        "run_key": _run_key(model, task, lane, repeat),
        "model": model,
        "task_id": task.task_id,
        "family": task.family,
        "lane": lane,
        "repeat": repeat,
        "oracle_pass": final_result["oracle_pass"],
        "oracle_checks": final_result["checks"],
        "oracle_behavior_digest": final_result.get("behavior_digest"),
        "oracle_error": final_result.get("error"),
        "oracle_receipt_channel": final_result.get("receipt_channel"),
        "oracle_subprocess_returncode": final_result.get("subprocess_returncode"),
        "test_attempts": len(oracle_results),
        "first_pass": first_pass,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "token_accounting": TOKEN_ACCOUNTING,
        "input_token_source": TOKEN_ACCOUNTING,
        "output_token_source": TOKEN_ACCOUNTING,
        "turns": len(turn_log),
        "turn_log": turn_log,
        "duration_seconds": round(duration_seconds, 6),
        "time_to_pass_seconds": round(time_to_pass_seconds, 6) if time_to_pass_seconds is not None else None,
        "residual_loc": sum(_source_loc(source) for source in authored.values()),
        "residual_files": sorted(authored),
        "repair_turns": repair_turns,
        "edit_distance_lines": _line_edit_distance(task.initial_files, final_files),
        "adapter_count": task.adapter_counts[lane],
        "reproducible_digest": reproducible_digest,
        "trajectory_digest": trajectory_digest,
        "repeat_design": REPEAT_DESIGN,
        "statistical_independence_claimed": STATISTICAL_INDEPENDENCE_CLAIMED,
        "evidence_scope": EVIDENCE_SCOPE,
        "simulation": True,
        "proxy_measurement": True,
        "live_model_evidence": False,
        "headline_eligible": False,
        "evidence_note": (
            "Real hidden-oracle execution over deterministic fixture outputs; multi-turn tokens are a "
            "characters-per-token proxy, not provider usage or live-model evidence. Repeats are deterministic "
            "pseudo-replications and are not statistically independent trajectories."
        ),
        **BOUNDARY,
    }
    row["row_digest"] = _digest({
        key: value for key, value in row.items()
        if key not in {"duration_seconds", "time_to_pass_seconds", "row_digest"}
    })
    return row


# Compute only after every transcript-producing function exists.  The payload
# hashes the exact static inputs plus the generators that produce context and
# token-bearing turns, so a fixture/protocol change cannot resume stale rows.
PROTOCOL_DIGEST = _digest(_protocol_payload())


def _load_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(row, dict) or not isinstance(row.get("run_key"), str):
            raise ValueError(f"invalid run row at {path}:{line_number}")
        rows.append(row)
    return rows


def _append_ledger(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_canonical_json(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def run_benchmark(
    ledger: Path,
    *,
    repeats: int = REPORTING_MIN_N,
    models: Iterable[str] = (DEFAULT_MODEL,),
    tasks: Iterable[TaskSpec] = TASKS,
) -> dict[str, Any]:
    """Fill missing logical cells and return exactly the requested protocol slice."""

    if repeats < 1:
        raise ValueError("repeats must be positive")
    model_names = tuple(dict.fromkeys(model.strip() for model in models if model.strip()))
    if not model_names:
        raise ValueError("at least one model label is required")
    task_specs = tuple(tasks)
    if not task_specs:
        raise ValueError("at least one task is required")

    existing_rows = _load_ledger(ledger)
    latest = {row["run_key"]: row for row in existing_rows}
    expected: list[tuple[str, TaskSpec, str, int, str]] = []
    for model in model_names:
        for task in task_specs:
            for repeat in range(repeats):
                for lane in LANES:
                    expected.append((model, task, lane, repeat, _run_key(model, task, lane, repeat)))

    appended = 0
    for model, task, lane, repeat, key in expected:
        previous = latest.get(key)
        if previous and previous.get("protocol_digest") == PROTOCOL_DIGEST:
            continue
        row = run_fixture(task, lane, model, repeat)
        _append_ledger(ledger, row)
        latest[key] = row
        appended += 1

    requested_rows = [latest[key] for *_, key in expected]
    return {
        "rows": requested_rows,
        "appended": appended,
        "resumed": len(expected) - appended,
        "expected": len(expected),
        "ledger": str(ledger),
    }


def _median(rows: list[dict[str, Any]], field: str, digits: int = 1) -> float | None:
    values = [row[field] for row in rows if isinstance(row.get(field), (int, float))]
    return round(statistics.median(values), digits) if values else None


def _underlying_cells(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], int]:
    counts: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in rows:
        counts[(row["lane"], row["model"], row["task_id"])] += 1
    return counts


def _cell_label(cell: tuple[str, str, str]) -> str:
    return "|".join(cell)


def _aggregate_group(
    rows: list[dict[str, Any]],
    *,
    required_cells: Iterable[tuple[str, str, str]],
) -> dict[str, Any]:
    passes = [row for row in rows if row.get("oracle_pass") is True]
    cells = _underlying_cells(rows)
    required = tuple(dict.fromkeys(required_cells))
    required_counts = {cell: cells.get(cell, 0) for cell in required}
    pass_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in passes:
        pass_counts[(row["lane"], row["model"], row["task_id"])] += 1
    min_n_gate_met = bool(required_counts) and all(
        n >= REPORTING_MIN_N for n in required_counts.values()
    )
    missing_cells = [_cell_label(cell) for cell, n in required_counts.items() if n == 0]
    underfilled_cells = [
        _cell_label(cell) for cell, n in required_counts.items() if n < REPORTING_MIN_N
    ]
    zero_success_cells = [
        _cell_label(cell) for cell in required if pass_counts.get(cell, 0) == 0
    ]
    token_total = sum(int(row.get("total_tokens", 0) or 0) for row in rows)
    digest_counts: dict[str, int] = defaultdict(int)
    for row in passes:
        if row.get("reproducible_digest"):
            digest_counts[row["reproducible_digest"]] += 1
    result = {
        "n": len(rows),
        "n_pass": len(passes),
        "pass_rate": round(len(passes) / len(rows), 3) if rows else None,
        "n_required_model_task_lane_cells": len(required),
        "n_observed_model_task_lane_cells": sum(n > 0 for n in required_counts.values()),
        "min_underlying_cell_n": min(required_counts.values()) if required_counts else 0,
        "min_n_gate_met": min_n_gate_met,
        "missing_required_cells": missing_cells,
        "underfilled_required_cells": underfilled_cells,
        "zero_success_required_cells": zero_success_cells,
        "reportable": False,
        "headline_eligible": False,
        "status": (
            "offline deterministic proxy; MIN_N mechanical gate filled but pseudo-repeats are not independent"
            if min_n_gate_met
            else f"offline deterministic proxy with missing/underfilled exact cells (<{REPORTING_MIN_N})"
        ),
        "median_input_tokens": _median(rows, "input_tokens"),
        "median_output_tokens": _median(rows, "output_tokens"),
        "median_total_tokens": _median(rows, "total_tokens"),
        "median_time_to_pass_seconds": _median(passes, "time_to_pass_seconds", 6),
        "median_duration_seconds": _median(rows, "duration_seconds", 6),
        "first_pass_rate": round(sum(bool(row.get("first_pass")) for row in rows) / len(rows), 3) if rows else None,
        "median_residual_loc": _median(rows, "residual_loc"),
        "median_repair_turns": _median(rows, "repair_turns"),
        "median_edit_distance_lines": _median(rows, "edit_distance_lines"),
        "median_adapter_count": _median(rows, "adapter_count"),
        "tokens_per_pass": round(token_total / len(passes), 1) if passes else None,
        "tokens_per_pass_status": (
            "complete_proxy_accounting" if passes
            else "zero_passes_all_attempt_tokens_retained" if rows
            else "missing_required_cell"
        ),
        "input_output_ratio": (
            round(sum(row["input_tokens"] for row in rows) / max(1, sum(row["output_tokens"] for row in rows)), 2)
            if rows else None
        ),
        "n_distinct_reproducible_digests": len(digest_counts),
        "n_unique_trajectory_digests": len({
            row.get("trajectory_digest") for row in rows if row.get("trajectory_digest")
        }),
        "repeat_design": REPEAT_DESIGN,
        "statistical_independence_claimed": STATISTICAL_INDEPENDENCE_CLAIMED,
        "evidence_scope": EVIDENCE_SCOPE,
        "token_accounting": TOKEN_ACCOUNTING,
        "live_model_evidence": False,
    }
    return result


def aggregate(
    rows: list[dict[str, Any]],
    *,
    expected_models: Iterable[str] | None = None,
    expected_tasks: Iterable[TaskSpec] = TASKS,
) -> dict[str, Any]:
    """Emit every required exact cell, including absent and zero-success cells."""

    observed_models = tuple(sorted({str(row["model"]) for row in rows}))
    requested_models = tuple(dict.fromkeys(
        expected_models if expected_models is not None else (observed_models or (DEFAULT_MODEL,))
    ))
    models = tuple(dict.fromkeys((*requested_models, *observed_models)))
    task_specs = tuple(expected_tasks)
    if not models:
        return {"by_lane_model": {}, "by_lane_family": {}, "by_lane_model_task": {}}

    by_lane_model: dict[str, Any] = {}
    for lane in LANES:
        for model in models:
            required = [(lane, model, task.task_id) for task in task_specs]
            group = [row for row in rows if row["lane"] == lane and row["model"] == model]
            by_lane_model[f"{lane}|{model}"] = _aggregate_group(group, required_cells=required)

    by_lane_family: dict[str, Any] = {}
    families = tuple(dict.fromkeys(task.family for task in task_specs))
    for lane in LANES:
        for family in families:
            family_tasks = tuple(task for task in task_specs if task.family == family)
            required = [
                (lane, model, task.task_id)
                for model in models
                for task in family_tasks
            ]
            group = [row for row in rows if row["lane"] == lane and row["family"] == family]
            by_lane_family[f"{lane}|{family}"] = _aggregate_group(group, required_cells=required)

    by_lane_model_task: dict[str, Any] = {}
    for lane in LANES:
        for model in models:
            for task in task_specs:
                cell = (lane, model, task.task_id)
                group = [
                    row for row in rows
                    if (row["lane"], row["model"], row["task_id"]) == cell
                ]
                by_lane_model_task[_cell_label(cell)] = _aggregate_group(group, required_cells=(cell,))

    return {
        "by_lane_model": dict(sorted(by_lane_model.items())),
        "by_lane_family": dict(sorted(by_lane_family.items())),
        "by_lane_model_task": dict(sorted(by_lane_model_task.items())),
    }


def _paired_summary(
    rows: list[dict[str, Any]],
    treatment_lane: str,
    *,
    required_pair_cells: Iterable[tuple[str, str]],
) -> dict[str, Any]:
    slots: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        if row.get("lane") not in {BASELINE_LANE, treatment_lane}:
            continue
        identity = (row["model"], row["task_id"], row["repeat"])
        slots[identity][row["lane"]] = row
    pairs = [
        (arms[BASELINE_LANE], arms[treatment_lane])
        for arms in slots.values()
        if BASELINE_LANE in arms and treatment_lane in arms
    ]
    both_pass = [
        (baseline, treatment) for baseline, treatment in pairs
        if baseline.get("oracle_pass") is True and treatment.get("oracle_pass") is True
    ]
    behavior_matched = [
        (baseline, treatment) for baseline, treatment in both_pass
        if baseline.get("oracle_behavior_digest")
        and baseline.get("oracle_behavior_digest") == treatment.get("oracle_behavior_digest")
    ]
    both_fail = [
        (baseline, treatment) for baseline, treatment in pairs
        if baseline.get("oracle_pass") is False and treatment.get("oracle_pass") is False
    ]
    required = tuple(dict.fromkeys(required_pair_cells))
    total_pair_cells: dict[tuple[str, str], int] = defaultdict(int)
    for baseline, _ in pairs:
        total_pair_cells[(baseline["model"], baseline["task_id"])] += 1
    pair_cells: dict[tuple[str, str], int] = defaultdict(int)
    for baseline, _ in behavior_matched:
        pair_cells[(baseline["model"], baseline["task_id"])] += 1
    total_counts = {cell: total_pair_cells.get(cell, 0) for cell in required}
    both_pass_counts = {cell: pair_cells.get(cell, 0) for cell in required}
    pair_min_n_gate_met = bool(required) and all(
        n >= REPORTING_MIN_N for n in total_counts.values()
    )
    both_pass_min_n_gate_met = bool(required) and all(
        n >= REPORTING_MIN_N for n in both_pass_counts.values()
    )

    def median_saved(field: str, digits: int = 1) -> float | None:
        values = [baseline[field] - treatment[field] for baseline, treatment in behavior_matched]
        return round(statistics.median(values), digits) if values else None

    total_saved = [
        baseline["total_tokens"] - treatment["total_tokens"]
        for baseline, treatment in behavior_matched
    ]
    result = {
        "baseline_lane": BASELINE_LANE,
        "treatment_lane": treatment_lane,
        "n_pairs": len(pairs),
        "n_both_pass": len(both_pass),
        "n_both_pass_behavior_match": len(behavior_matched),
        "n_baseline_only_pass": sum(
            baseline.get("oracle_pass") is True and treatment.get("oracle_pass") is False
            for baseline, treatment in pairs
        ),
        "n_treatment_only_pass": sum(
            baseline.get("oracle_pass") is False and treatment.get("oracle_pass") is True
            for baseline, treatment in pairs
        ),
        "n_both_fail": len(both_fail),
        "n_inconclusive_both_fail": len(both_fail),
        "both_fail_classification": "inconclusive; excluded from all savings deltas",
        "n_required_model_task_pair_cells": len(required),
        "min_model_task_pair_n": min(total_counts.values()) if total_counts else 0,
        "min_model_task_both_pass_n": min(both_pass_counts.values()) if both_pass_counts else 0,
        "pair_min_n_gate_met": pair_min_n_gate_met,
        "both_pass_min_n_gate_met": both_pass_min_n_gate_met,
        "missing_required_pair_cells": [
            "|".join(cell) for cell, n in total_counts.items() if n == 0
        ],
        "underfilled_required_pair_cells": [
            "|".join(cell) for cell, n in total_counts.items() if n < REPORTING_MIN_N
        ],
        "zero_both_pass_required_pair_cells": [
            "|".join(cell) for cell, n in both_pass_counts.items() if n == 0
        ],
        "reportable": False,
        "headline_eligible": False,
        "status": (
            "offline deterministic proxy; both-pass MIN_N filled with non-independent pseudo-repeats"
            if both_pass_min_n_gate_met
            else f"offline deterministic proxy with missing/underfilled both-pass cells (<{REPORTING_MIN_N})"
        ),
        "median_input_tokens_saved": median_saved("input_tokens"),
        "median_output_tokens_saved": median_saved("output_tokens"),
        "median_total_tokens_saved": round(statistics.median(total_saved), 1) if total_saved else None,
        "median_time_to_pass_seconds_saved": median_saved("time_to_pass_seconds", 6),
        "median_residual_loc_reduction": median_saved("residual_loc"),
        "median_repair_turns_reduction": median_saved("repair_turns"),
        "median_edit_distance_lines_reduction": median_saved("edit_distance_lines"),
        "median_adapter_count_reduction": median_saved("adapter_count"),
        "evidence_scope": EVIDENCE_SCOPE,
        "token_accounting": TOKEN_ACCOUNTING,
        "live_model_evidence": False,
        "n_unique_paired_trajectory_digests": len({
            (baseline.get("trajectory_digest"), treatment.get("trajectory_digest"))
            for baseline, treatment in behavior_matched
            if baseline.get("trajectory_digest") and treatment.get("trajectory_digest")
        }),
        "repeat_design": REPEAT_DESIGN,
        "statistical_independence_claimed": STATISTICAL_INDEPENDENCE_CLAIMED,
        "primary_comparison_rule": "matched same-model same-task same-repeat both-pass pairs only",
    }
    return result


def paired_comparisons(
    rows: list[dict[str, Any]],
    *,
    expected_models: Iterable[str] | None = None,
    expected_tasks: Iterable[TaskSpec] = TASKS,
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    observed_models = tuple(sorted({str(row["model"]) for row in rows}))
    requested_models = tuple(
        expected_models if expected_models is not None else (observed_models or (DEFAULT_MODEL,))
    )
    models = tuple(dict.fromkeys((*requested_models, *observed_models)))
    task_specs = tuple(expected_tasks)
    model_tasks = tuple((model, task.task_id) for model in models for task in task_specs)
    for treatment in TREATMENT_LANES:
        overall = _paired_summary(rows, treatment, required_pair_cells=model_tasks)
        overall["scope_note"] = "pooled diagnostic only; use by_model_task for reportability"
        output[treatment] = {
            "overall": overall,
            "by_model": {
                model: _paired_summary(
                    [row for row in rows if row["model"] == model],
                    treatment,
                    required_pair_cells=((model, task.task_id) for task in task_specs),
                )
                for model in models
            },
            "by_model_task": {
                f"{model}|{task_id}": _paired_summary(
                    [row for row in rows if row["model"] == model and row["task_id"] == task_id],
                    treatment,
                    required_pair_cells=((model, task_id),),
                )
                for model, task_id in model_tasks
            },
        }
    return output


def build_report(
    rows: list[dict[str, Any]],
    *,
    ledger: str = "",
    expected_models: Iterable[str] | None = None,
    expected_tasks: Iterable[TaskSpec] = TASKS,
) -> dict[str, Any]:
    observed_models = tuple(sorted({str(row["model"]) for row in rows}))
    requested_models = tuple(
        expected_models if expected_models is not None else (observed_models or (DEFAULT_MODEL,))
    )
    models = tuple(dict.fromkeys((*requested_models, *observed_models)))
    task_specs = tuple(expected_tasks)
    required_cells = tuple(
        (lane, model, task.task_id)
        for lane in LANES
        for model in models
        for task in task_specs
    )
    counts = _underlying_cells(rows)
    pass_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in rows:
        if row.get("oracle_pass") is True:
            pass_counts[(row["lane"], row["model"], row["task_id"])] += 1
    completeness = {
        "n_required_exact_cells": len(required_cells),
        "n_present_exact_cells": sum(counts.get(cell, 0) > 0 for cell in required_cells),
        "all_required_exact_cells_meet_min_n": bool(required_cells) and all(
            counts.get(cell, 0) >= REPORTING_MIN_N for cell in required_cells
        ),
        "missing_required_exact_cells": [
            _cell_label(cell) for cell in required_cells if counts.get(cell, 0) == 0
        ],
        "underfilled_required_exact_cells": [
            _cell_label(cell) for cell in required_cells if counts.get(cell, 0) < REPORTING_MIN_N
        ],
        "zero_success_required_exact_cells": [
            _cell_label(cell) for cell in required_cells if pass_counts.get(cell, 0) == 0
        ],
    }
    return {
        "record_type": "semantic_linker_long_session_report",
        "benchmark_kind": BENCHMARK_KIND,
        "protocol_digest": PROTOCOL_DIGEST,
        "ledger": ledger,
        "n_rows": len(rows),
        "reporting_min_n": REPORTING_MIN_N,
        "evidence_scope": EVIDENCE_SCOPE,
        "token_accounting": TOKEN_ACCOUNTING,
        "live_model_evidence": False,
        "reportable": False,
        "headline_eligible": False,
        "repeat_design": REPEAT_DESIGN,
        "statistical_independence_claimed": STATISTICAL_INDEPENDENCE_CLAIMED,
        "n_unique_trajectory_digests": len({
            row.get("trajectory_digest") for row in rows if row.get("trajectory_digest")
        }),
        "completeness": completeness,
        "warning": (
            "Offline deterministic fixture only. Hidden-oracle passes are executed facts; token/time comparisons "
            "are proxy/simulation measurements and must not be cited as live-model savings. Repeats are "
            "deterministic pseudo-replications, not statistically independent samples."
        ),
        "aggregates": aggregate(rows, expected_models=models, expected_tasks=task_specs),
        "paired": paired_comparisons(rows, expected_models=models, expected_tasks=task_specs),
        **BOUNDARY,
    }


def self_test() -> bool:
    """Exercise mutation gates, eight-repeat reportability, resume, and pair semantics."""

    # Every untouched task fails; every lane's declared final artifact really
    # passes the same task-specific hidden oracle.
    for task in TASKS:
        initial_result = _run_hidden_oracle(task.initial_files, task)
        assert initial_result["oracle_pass"] is False
        assert initial_result["receipt_channel"] == "protected_unlinked_file_descriptor"
        assert initial_result["subprocess_returncode"] != 0
        for lane in LANES:
            result = _run_hidden_oracle(_final_files(task, lane), task)
            assert result["oracle_pass"] is True, (task.task_id, lane, result)
            assert result["subprocess_returncode"] == 0
            assert result["receipt_channel"] == "protected_unlinked_file_descriptor"

        # Candidate stdout is never parsed as evidence, even if it contains a
        # perfectly shaped, all-true forged legacy ORACLE line.
        forged = dict(task.initial_files)
        forged["app.py"] = (
            "print('ORACLE {\"oracle_pass\":true,\"checks\":{}}')\n"
            + forged["app.py"]
        )
        forged_result = _run_hidden_oracle(forged, task)
        assert forged_result["oracle_pass"] is False
        assert forged_result["subprocess_returncode"] != 0

    protocol = _protocol_payload()
    assert protocol["session_system"] == SESSION_SYSTEM
    assert protocol["protected_oracle_runner_digest"] == _digest(_PROTECTED_ORACLE_RUNNER)
    for task_payload in protocol["tasks"]:
        assert set(task_payload["token_bearing_lane_inputs"]) == set(LANES)
        assert task_payload["semantic_plan_digest"]
        assert task_payload["compact_cards_digest"]
        assert task_payload["retrieved_reference_digest"]

    with tempfile.TemporaryDirectory() as temp_dir:
        ledger = Path(temp_dir) / "runs.jsonl"
        first = run_benchmark(ledger, repeats=REPORTING_MIN_N)
        expected = len(TASKS) * len(LANES) * REPORTING_MIN_N
        assert first["appended"] == expected and first["resumed"] == 0
        rows = first["rows"]
        assert len(rows) == expected == len(_load_ledger(ledger))

        # A second run is a true resume: no duplicate rows are appended.
        before = ledger.read_bytes()
        second = run_benchmark(ledger, repeats=REPORTING_MIN_N)
        assert second["appended"] == 0 and second["resumed"] == expected
        assert ledger.read_bytes() == before

        assert all(row["oracle_pass"] is True for row in rows)
        assert all(row["simulation"] and row["proxy_measurement"] for row in rows)
        assert all(not row["live_model_evidence"] and not row["headline_eligible"] for row in rows)
        assert all(row["token_accounting"] == TOKEN_ACCOUNTING for row in rows)
        assert all(row["candidate"] and not row["serves_truth"] for row in rows)
        assert all(row["repeat_design"] == REPEAT_DESIGN for row in rows)
        assert all(row["statistical_independence_claimed"] is False for row in rows)
        assert all(row["oracle_subprocess_returncode"] == 0 for row in rows)

        # Eight repeats exist in each exact model/task/lane cell; no pooled
        # aggregate can hide a smaller cell.
        counts = _underlying_cells(rows)
        assert counts and set(counts.values()) == {REPORTING_MIN_N}
        report = build_report(rows, ledger=str(ledger))
        assert report["reportable"] is False and report["headline_eligible"] is False
        assert report["statistical_independence_claimed"] is False
        assert report["n_unique_trajectory_digests"] == len(TASKS) * len(LANES)
        assert report["completeness"]["all_required_exact_cells_meet_min_n"] is True
        assert report["completeness"]["missing_required_exact_cells"] == []
        assert report["completeness"]["zero_success_required_exact_cells"] == []
        exact = report["aggregates"]["by_lane_model_task"]
        assert exact and all(cell["min_n_gate_met"] for cell in exact.values())
        assert all(not cell["reportable"] for cell in exact.values())
        assert all(not cell["headline_eligible"] for cell in exact.values())
        assert all(cell["tokens_per_pass"] == cell["median_total_tokens"] for cell in exact.values())
        assert all(cell["n_unique_trajectory_digests"] == 1 for cell in exact.values())

        baseline_rows = [row for row in rows if row["lane"] == LANE_AGENT_ONLY]
        semantic_rows = [row for row in rows if row["lane"] == LANE_SEMANTIC_COMPOSE]
        partial_rows = [row for row in rows if row["lane"] == LANE_PARTIAL_GAPFILL]
        assert all(not row["first_pass"] and row["repair_turns"] == 1 for row in baseline_rows)
        assert all(row["first_pass"] and row["residual_loc"] == 0 for row in semantic_rows)
        assert all(row["first_pass"] and row["residual_loc"] > 0 for row in partial_rows)
        assert statistics.median(row["total_tokens"] for row in baseline_rows) > statistics.median(
            row["total_tokens"] for row in semantic_rows
        )

        # Repeated materialization must be byte-identical for a task/lane.
        digests: dict[tuple[str, str], set[str]] = defaultdict(set)
        for row in rows:
            digests[(row["task_id"], row["lane"])].add(row["reproducible_digest"])
        assert all(len(values) == 1 for values in digests.values())

        # Paired savings are based on same-task both-pass outcomes, have n>=8,
        # and remain explicitly ineligible as live evidence.
        for treatment in TREATMENT_LANES:
            comparison = report["paired"][treatment]
            for cell in comparison["by_model_task"].values():
                assert cell["n_both_pass"] == REPORTING_MIN_N
                assert cell["n_both_pass_behavior_match"] == REPORTING_MIN_N
                assert cell["both_pass_min_n_gate_met"] is True
                assert cell["reportable"] is False and cell["headline_eligible"] is False
                assert cell["n_inconclusive_both_fail"] == 0
                assert cell["n_unique_paired_trajectory_digests"] == 1

        # Deleting a complete exact cell cannot disappear from the report.
        missing_cell = (LANE_SEMANTIC_COMPOSE, DEFAULT_MODEL, TASKS[0].task_id)
        incomplete_rows = [
            row for row in rows
            if (row["lane"], row["model"], row["task_id"]) != missing_cell
        ]
        incomplete = build_report(incomplete_rows, expected_models=(DEFAULT_MODEL,))
        missing_key = _cell_label(missing_cell)
        missing_exact = incomplete["aggregates"]["by_lane_model_task"][missing_key]
        assert missing_exact["n"] == 0
        assert missing_exact["min_n_gate_met"] is False
        assert missing_exact["reportable"] is False
        assert missing_key in incomplete["completeness"]["missing_required_exact_cells"]

        # A present MIN_N cell with no successes remains explicit with all
        # failed-attempt tokens retained in its aggregate.
        zero_success_rows: list[dict[str, Any]] = []
        zero_cell = (LANE_TEXT_RETRIEVAL, DEFAULT_MODEL, TASKS[0].task_id)
        for row in rows:
            copy = dict(row)
            if (copy["lane"], copy["model"], copy["task_id"]) == zero_cell:
                copy["oracle_pass"] = False
                copy["oracle_behavior_digest"] = None
            zero_success_rows.append(copy)
        zero_report = build_report(zero_success_rows, expected_models=(DEFAULT_MODEL,))
        zero_key = _cell_label(zero_cell)
        zero_exact = zero_report["aggregates"]["by_lane_model_task"][zero_key]
        assert zero_exact["n"] == REPORTING_MIN_N and zero_exact["n_pass"] == 0
        assert zero_exact["min_n_gate_met"] is True and zero_exact["reportable"] is False
        assert zero_exact["tokens_per_pass"] is None
        assert zero_exact["tokens_per_pass_status"] == "zero_passes_all_attempt_tokens_retained"
        assert zero_key in zero_report["completeness"]["zero_success_required_exact_cells"]

        # A synthetic both-fail sample is not converted into savings evidence.
        synthetic: list[dict[str, Any]] = []
        for repeat in range(REPORTING_MIN_N):
            for lane in (BASELINE_LANE, LANE_SEMANTIC_COMPOSE):
                synthetic.append({
                    "model": DEFAULT_MODEL,
                    "task_id": TASKS[0].task_id,
                    "repeat": repeat,
                    "lane": lane,
                    "oracle_pass": False,
                    "oracle_behavior_digest": None,
                    "input_tokens": 100,
                    "output_tokens": 10,
                    "total_tokens": 110,
                    "time_to_pass_seconds": None,
                    "residual_loc": 0,
                    "repair_turns": 0,
                    "edit_distance_lines": 0,
                    "adapter_count": 0,
                })
        inconclusive = _paired_summary(
            synthetic,
            LANE_SEMANTIC_COMPOSE,
            required_pair_cells=((DEFAULT_MODEL, TASKS[0].task_id),),
        )
        assert inconclusive["n_inconclusive_both_fail"] == REPORTING_MIN_N
        assert inconclusive["median_total_tokens_saved"] is None
        assert inconclusive["reportable"] is False

    print(
        "OK semantic_linker_long_session_benchmark self-test: "
        f"{len(TASKS)} tasks x {len(LANES)} lanes x {REPORTING_MIN_N} repeats = {expected} benchmark rows with "
        "protected hidden-oracle execution(s) recorded in a resumable JSONL ledger; exact model/task/lane cells "
        "meet the mechanical MIN_N "
        "gate but deterministic repeats are labelled non-independent pseudo-replications; matched "
        "both-pass comparisons, proxy token accounting, first-pass/repair/residual/edit/adapter/time metrics, "
        "protected non-stdout oracle receipts, complete missing/zero-success cells, reproducible/unique-trajectory "
        "digests, and both-fail=inconclusive gates verified. All rows remain offline simulation, "
        "candidate=true, serves_truth=false, and never live/headline evidence."
    )
    return True


def _compact_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        key: report[key]
        for key in (
            "record_type",
            "benchmark_kind",
            "protocol_digest",
            "ledger",
            "n_rows",
            "reporting_min_n",
            "evidence_scope",
            "token_accounting",
            "live_model_evidence",
            "reportable",
            "headline_eligible",
            "repeat_design",
            "statistical_independence_claimed",
            "n_unique_trajectory_digests",
            "completeness",
            "warning",
            "aggregates",
            "paired",
            "candidate",
            "serves_truth",
        )
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline paired long-session semantic-linker benchmark (real oracles, simulated token proxy)."
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--repeats", type=int, default=REPORTING_MIN_N)
    parser.add_argument("--model", action="append", dest="models", default=[])
    args = parser.parse_args()

    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    if args.demo:
        run = run_benchmark(
            args.ledger,
            repeats=args.repeats,
            models=tuple(args.models) or (DEFAULT_MODEL,),
        )
        report = build_report(
            run["rows"],
            ledger=str(args.ledger),
            expected_models=tuple(args.models) or (DEFAULT_MODEL,),
        )
        output = _compact_report(report)
        output["ledger_progress"] = {
            "expected": run["expected"],
            "appended": run["appended"],
            "resumed": run["resumed"],
        }
        print(json.dumps(output, indent=2, sort_keys=True))
        return
    parser.print_help()


if __name__ == "__main__":
    main()
