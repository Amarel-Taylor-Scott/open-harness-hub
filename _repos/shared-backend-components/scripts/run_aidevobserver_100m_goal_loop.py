#!/usr/bin/env python3
"""Bounded, resumable AIDevObserver primitive-corpus goal loop.

This is an ORCHESTRATOR over existing proof-producing stages.  It does not mint a
target-sized count, promote candidates merely because a command returned zero,
or turn a declared target into measured inventory.  Every persisted receipt is
``candidate=true / serves_truth=false``.

Default invocation is a read-only dry run.  ``--once`` executes one bounded
offline tick.  Network scraping and LLM calls remain disabled unless separately
enabled; ToS-sensitive live sources remain blocked even when live scraping is
enabled.

    PYTHONPATH=. python3 scripts/run_aidevobserver_100m_goal_loop.py
    PYTHONPATH=. python3 scripts/run_aidevobserver_100m_goal_loop.py --once
    PYTHONPATH=. python3 scripts/run_aidevobserver_100m_goal_loop.py --watch --max-ticks 3
    PYTHONPATH=. python3 scripts/run_aidevobserver_100m_goal_loop.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next(
    (parent for parent in _here_boot.parents if (parent / "scripts" / "_repo_paths.py").exists()),
    _here_boot.parents[1],
)
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import copy  # noqa: E402
import fcntl  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from contextlib import contextmanager  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from typing import Any, Callable, Mapping, Sequence  # noqa: E402

from scripts.primitive_description_backfill_loop import DEFAULT_MANIFEST as DESCRIPTION_MANIFEST  # noqa: E402
from scripts.primitive_description_embedding_loop import (  # noqa: E402
    DEFAULT_STATE_DIR as DESCRIPTION_EMBEDDING_STATE_DIR,
    STATE_FILENAME as DESCRIPTION_EMBEDDING_STATE_FILENAME,
)


BOUNDARY: dict[str, bool] = {"candidate": True, "serves_truth": False}
DECLARED_TARGET = 100_000_000
SCHEMA_VERSION = 1
STATE_SCHEMA = "aidevobserver_primitive_goal_loop_state"
TICK_RECORD_TYPE = "aidevobserver_primitive_goal_tick_receipt"
DRY_RUN_RECORD_TYPE = "aidevobserver_primitive_goal_dry_run"

DEFAULT_STATE_DIR = resource("data") / "dev-intel" / "aidevobserver_100m_goal_loop"
STATE_FILENAME = "state.json"
LEDGER_FILENAME = "ledger.jsonl"
LOCK_FILENAME = ".writer.lock"
PENDING_TICK_FILENAME = ".pending_tick.json"

# Named bounds keep --once safe on a developer machine.  Operators may raise
# them explicitly; an omitted bound never expands to the whole corpus.
DEFAULT_SOURCE_LIMIT = 10
DEFAULT_QUESTION_COUNT = 24
DEFAULT_USEFULNESS_CAP = 2_000
DEFAULT_DESCRIPTION_LIMIT = 20_000
DEFAULT_SYNTHESIS_LIMIT = 2_000
DEFAULT_SEARCH_LIMIT = 25_000
DEFAULT_SEARCH_QUERY_SAMPLE = 24
DEFAULT_EMBEDDING_LIMIT = 25_000
DEFAULT_STAGE_TIMEOUT_SECONDS = 900
DEFAULT_INVENTORY_TIMEOUT_SECONDS = 300
DEFAULT_WATCH_INTERVAL_SECONDS = 3_600
MAX_RECEIPT_OUTPUT_CHARS = 4_000

_SCRIPTS = {
    "source_intake": "continuous_primitive_scrape_loop.py",
    "ingest_research_candidates": "ingest_continuous_scrape_candidates.py",
    "ingest_registered_source_union": "ingest_primitive_source_union.py",
    "description_backfill": "primitive_description_backfill_loop.py",
    "usefulness_description_gate": "primitive_usefulness_gate.py",
    "deterministic_synthesis_oracle": "primitive_synthesis_loop.py",
    "verified_recipe_receipts": "verified_recipe_receipt_store.py",
    "federated_search_overlay_sync": "primitive_search_federation.py",
    "description_embedding_sync": "primitive_description_embedding_loop.py",
    "embedding_shard_sync": "primitive_embedding_shard_loop.py",
    "inventory_receipt": "primitive_inventory.py",
}

# Coverage manifests are read, never inferred from the target.  The full-corpus
# search tier is a candidate federation and remains separate from promotion.
_COVERAGE_MANIFESTS: dict[str, tuple[Path, str]] = {
    "federated_search_docs": (
        resource("dist") / "primitive_search_federation_overlay.fast.manifest.json",
        "unique_searchable_docs",
    ),
    "description_complete_docs": (
        resource("dist") / "primitive_search_federation_overlay.manifest.json",
        "description_complete_docs",
    ),
    "description_sidecar_accepted_current": (DESCRIPTION_MANIFEST, "accepted_current_descriptions"),
    "description_sidecar_usefulness_pass": (DESCRIPTION_MANIFEST, "usefulness_pass"),
    "description_embedding_revisions": (
        DESCRIPTION_EMBEDDING_STATE_DIR / DESCRIPTION_EMBEDDING_STATE_FILENAME,
        "distinct_primitive_revisions",
    ),
    "description_embedding_primitives": (
        DESCRIPTION_EMBEDDING_STATE_DIR / DESCRIPTION_EMBEDDING_STATE_FILENAME,
        "distinct_primitives",
    ),
    "trusted_recipe_receipts": (
        resource("dist") / "verified_recipe_receipts.manifest.json",
        "trusted_receipts",
    ),
    "embedding_docs": (
        resource("dist") / "primitive-embedding-shards" / "manifest.json", "coverage_rows"
    ),
    "register_embedding_docs": (
        resource("dist") / "primitive-embedding-shards" / "manifest.json", "coverage_rows"
    ),
    "usefulness_full_corpus_docs": (
        resource("data") / "dev-intel" / "primitive_usefulness_gate" / "full_corpus_manifest.json",
        "passing_unique_docs",
    ),
}


Runner = Callable[[Sequence[str], int], Mapping[str, Any]]
InventoryProvider = Callable[[bool, int], Mapping[str, Any]]
CoverageProvider = Callable[[], Mapping[str, Any]]
Sleep = Callable[[float], None]


@dataclass(frozen=True)
class LoopConfig:
    state_dir: Path = DEFAULT_STATE_DIR
    source_limit: int = DEFAULT_SOURCE_LIMIT
    question_count: int = DEFAULT_QUESTION_COUNT
    usefulness_cap: int = DEFAULT_USEFULNESS_CAP
    description_limit: int = DEFAULT_DESCRIPTION_LIMIT
    synthesis_limit: int = DEFAULT_SYNTHESIS_LIMIT
    search_limit: int = DEFAULT_SEARCH_LIMIT
    search_query_sample: int = DEFAULT_SEARCH_QUERY_SAMPLE
    embedding_limit: int = DEFAULT_EMBEDDING_LIMIT
    stage_timeout_seconds: int = DEFAULT_STAGE_TIMEOUT_SECONDS
    inventory_timeout_seconds: int = DEFAULT_INVENTORY_TIMEOUT_SECONDS
    allow_live_scrape: bool = False
    allow_llm: bool = False
    initial_synthesis_offset: int | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _script(name: str) -> str:
    return str(_sbc_boot / "scripts" / _SCRIPTS[name])


def _new_state() -> dict[str, Any]:
    now = _utc_now()
    return {
        "schema": STATE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "declared_target": DECLARED_TARGET,
        "tick": 0,
        "synthesis_offset": 0,
        "last_tick_ok": None,
        "last_inventory": {},
        "created_at": now,
        "updated_at": now,
        **BOUNDARY,
    }


def _bootstrap_synthesis_offset() -> int:
    """Resume after the last actually scanned descriptor, never a requested batch limit."""

    path = resource("data") / "dev-intel" / "primitive_synthesis" / "latest_batch.json"
    if not path.exists():
        return 0
    try:
        row = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    return _positive_int(row.get("offset", 0)) + _positive_int(row.get("scanned", 0))


def _load_state(state_dir: Path, initial_synthesis_offset: int | None = None) -> dict[str, Any]:
    path = state_dir / STATE_FILENAME
    if not path.exists():
        state = _new_state()
        state["synthesis_offset"] = (
            _bootstrap_synthesis_offset()
            if initial_synthesis_offset is None else _positive_int(initial_synthesis_offset)
        )
        return state
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("schema") != STATE_SCHEMA:
        raise ValueError(f"unexpected state schema in {path}: {state.get('schema')!r}")
    if state.get("declared_target") != DECLARED_TARGET:
        raise ValueError(
            f"declared target mismatch in {path}: {state.get('declared_target')!r} != {DECLARED_TARGET}"
        )
    for key in ("tick", "synthesis_offset"):
        value = state.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"invalid {key} in {path}: {value!r}")
    return state


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
        tmp = Path(handle.name)
    os.replace(tmp, path)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


@contextmanager
def _writer_lock(state_dir: Path):
    state_dir.mkdir(parents=True, exist_ok=True)
    with (state_dir / LOCK_FILENAME).open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _file_digest_or_none(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tick_transaction_id(receipt: Mapping[str, Any], state: Mapping[str, Any]) -> str:
    payload = json.dumps(
        {
            "tick": receipt.get("tick"),
            "generated_at": receipt.get("generated_at"),
            "synthesis_offset": state.get("synthesis_offset"),
            "state_tick": state.get("tick"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _ledger_has_transaction(path: Path, transaction_id: str) -> bool:
    if not path.is_file():
        return False
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, Mapping) and row.get("tick_transaction_id") == transaction_id:
                return True
    return False


def _recover_pending_tick(config: LoopConfig) -> None:
    """Finish an interrupted ledger/state two-file commit while holding the writer lock."""

    pending_path = config.state_dir / PENDING_TICK_FILENAME
    if not pending_path.is_file():
        return
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    receipt = pending.get("receipt")
    state = pending.get("state")
    transaction_id = pending.get("tick_transaction_id")
    if not isinstance(receipt, Mapping) or not isinstance(state, Mapping) or not isinstance(transaction_id, str):
        raise ValueError(f"invalid pending tick transaction: {pending_path}")
    if receipt.get("candidate") is not True or receipt.get("serves_truth") is not False:
        raise ValueError(f"pending receipt lost candidate boundary: {pending_path}")
    ledger_path = config.state_dir / LEDGER_FILENAME
    if not _ledger_has_transaction(ledger_path, transaction_id):
        _append_jsonl(ledger_path, receipt)
    state_path = config.state_dir / STATE_FILENAME
    publish_pending_state = True
    if state_path.is_file():
        current = _load_state(config.state_dir)
        current_tick = _positive_int(current.get("tick", 0))
        pending_tick = _positive_int(state.get("tick", 0))
        if current_tick > pending_tick:
            publish_pending_state = False
        elif current_tick == pending_tick and dict(current) != dict(state):
            raise RuntimeError("pending transaction conflicts with the durable state at the same tick")
    if publish_pending_state:
        _atomic_write_json(state_path, state)
    pending_path.unlink()
    _fsync_directory(config.state_dir)


def _run_subprocess(command: Sequence[str], timeout_seconds: int) -> Mapping[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(command),
            cwd=_sbc_boot,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "ok": False,
            "returncode": None,
            "timed_out": True,
            "stdout": stdout,
            "stderr": stderr,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    except OSError as exc:
        return {
            "ok": False,
            "returncode": None,
            "error": f"{type(exc).__name__}: {exc}",
            "stdout": "",
            "stderr": "",
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }


def _trimmed_stage_result(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(result.get("ok")),
        "returncode": result.get("returncode"),
        "timed_out": bool(result.get("timed_out", False)),
        "elapsed_seconds": result.get("elapsed_seconds"),
        "error": result.get("error"),
        "stdout_tail": str(result.get("stdout", ""))[-MAX_RECEIPT_OUTPUT_CHARS:],
        "stderr_tail": str(result.get("stderr", ""))[-MAX_RECEIPT_OUTPUT_CHARS:],
    }


def _real_inventory_provider(emit: bool, timeout_seconds: int) -> Mapping[str, Any]:
    command = [sys.executable, _script("inventory_receipt")]
    if emit:
        command.append("--emit")
    command.append("--json")
    result = dict(_run_subprocess(command, timeout_seconds))
    if not result.get("ok"):
        return {"ok": False, "command": command, "result": _trimmed_stage_result(result)}
    try:
        inventory = json.loads(str(result.get("stdout", "")))
    except json.JSONDecodeError as exc:
        result["error"] = f"inventory JSON decode failed: {exc}"
        result["ok"] = False
        return {"ok": False, "command": command, "result": _trimmed_stage_result(result)}
    return {
        "ok": True,
        "command": command,
        "inventory": inventory,
        "result": _trimmed_stage_result(result),
    }


def _read_coverage_manifests() -> Mapping[str, Any]:
    measured: dict[str, Any] = {}
    for label, (path, field) in _COVERAGE_MANIFESTS.items():
        entry: dict[str, Any] = {
            "path": str(path.relative_to(_sbc_boot)),
            "field": field,
            "exists": path.exists(),
            "count": 0,
        }
        if path.exists():
            try:
                manifest = json.loads(path.read_text(encoding="utf-8"))
                value = manifest.get(field, 0)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    entry["count"] = value
                else:
                    entry["error"] = f"field {field!r} is not a non-negative integer"
            except (OSError, json.JSONDecodeError) as exc:
                entry["error"] = f"{type(exc).__name__}: {exc}"
        measured[label] = entry
    return measured


def _positive_int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _target_gate_receipt(
    inventory: Mapping[str, Any], coverage: Mapping[str, Any]
) -> dict[str, Any]:
    ladder = inventory.get("status_ladder", {})
    if not isinstance(ladder, Mapping):
        ladder = {}

    def coverage_count(label: str) -> int:
        entry = coverage.get(label, {})
        return _positive_int(entry.get("count", 0)) if isinstance(entry, Mapping) else 0

    ladder_detail = inventory.get("ladder_detail", {})
    if not isinstance(ladder_detail, Mapping):
        ladder_detail = {}

    def detail_group(tier: str, group: str) -> int:
        entry = ladder_detail.get(tier, {})
        by_group = entry.get("by_group", {}) if isinstance(entry, Mapping) else {}
        return _positive_int(by_group.get(group, 0)) if isinstance(by_group, Mapping) else 0

    measured_counts = {
        # The synthesized group proves a generic family template, not each broad descriptor contract. Only the
        # independently execution-verified group is eligible for the 100M fully-working/verified gates.
        "descriptor_specific_working": detail_group("working", "executed"),
        "descriptor_specific_verified": detail_group("verified", "executed"),
        "family_template_execution": detail_group("working", "synthesized"),
        "federated_search_docs": coverage_count("federated_search_docs"),
        # Legacy field-completeness remains diagnostic; it is not accepted descriptor coverage.
        "description_complete_docs": coverage_count("description_complete_docs"),
        "description_sidecar_accepted_current": coverage_count("description_sidecar_accepted_current"),
        "description_sidecar_usefulness_pass": coverage_count("description_sidecar_usefulness_pass"),
        # Normalize profile fan-out to distinct immutable revisions and distinct primitive identities.
        "description_embedding_revisions": coverage_count("description_embedding_revisions"),
        "description_embedding_primitives": coverage_count("description_embedding_primitives"),
        "trusted_recipe_receipts": coverage_count("trusted_recipe_receipts"),
        "usefulness_full_corpus_docs": coverage_count("usefulness_full_corpus_docs"),
        "embedding_docs": coverage_count("embedding_docs"),
        "register_embedding_docs": coverage_count("register_embedding_docs"),
    }
    gate_sources = {
        "working": ("descriptor_specific_working",),
        "verification": ("descriptor_specific_verified",),
        "search_coverage": ("federated_search_docs",),
        "description_coverage": ("description_sidecar_accepted_current",),
        "usefulness_coverage": (
            "usefulness_full_corpus_docs",
            "description_sidecar_usefulness_pass",
        ),
        "embedding_coverage": ("embedding_docs",),
        "description_embedding_coverage": ("description_embedding_primitives",),
        "description_embedding_revision_evidence": ("description_embedding_revisions",),
        "register_embedding_coverage": ("register_embedding_docs",),
    }
    gates: dict[str, Any] = {}
    for gate, source_names in gate_sources.items():
        source_counts = {name: measured_counts[name] for name in source_names}
        measured = min(source_counts.values()) if source_counts else 0
        gates[gate] = {
            "pass": measured >= DECLARED_TARGET,
            "measured_count": measured,
            "source_counts": source_counts,
            "gap": max(0, DECLARED_TARGET - measured),
        }
    all_pass = all(gate["pass"] for gate in gates.values())
    return {
        "declared_target": DECLARED_TARGET,
        "measured_counts": measured_counts,
        "gates": gates,
        "all_coverage_gates_passed": all_pass,
        "count_gates_ready_for_independent_review": all_pass,
        "status": "coverage_gates_passed" if all_pass else "not_ready",
        "note": (
            "Passing these candidate-only count gates permits independent review of the underlying receipts; "
            "counts never authorize an external truth claim or upgrade execution evidence."
        ),
        **BOUNDARY,
    }


def _stage_plan(config: LoopConfig, state: Mapping[str, Any]) -> list[dict[str, Any]]:
    source_command = [
        sys.executable,
        _script("source_intake"),
        "--once",
        "--source-limit",
        str(config.source_limit),
        "--question-count",
        str(config.question_count),
    ]
    if config.allow_live_scrape:
        source_command.append("--live")
    if config.allow_llm:
        source_command.append("--use-llm")

    # Deliberately absent: --allow-tos-sensitive-live.  This loop never opts
    # ToS-sensitive sources into live access.
    return [
        {
            "name": "source_intake",
            "command": source_command,
            "timeout_seconds": config.stage_timeout_seconds,
            "policy": {
                "network_enabled": config.allow_live_scrape,
                "llm_enabled": config.allow_llm,
                "tos_sensitive_live_allowed": False,
            },
        },
        {
            "name": "ingest_research_candidates",
            "command": [sys.executable, _script("ingest_research_candidates"), "--sync"],
            "timeout_seconds": config.stage_timeout_seconds,
            "policy": {"candidate_only": True, "dedupe_by_immutable_id": True, "promotion": False},
        },
        {
            "name": "ingest_registered_source_union",
            "command": [sys.executable, _script("ingest_registered_source_union"), "--sync"],
            "timeout_seconds": config.stage_timeout_seconds,
            "policy": {
                "candidate_only_search_projection": True,
                "origin_truth_boundary_preserved": True,
                "dedupe_by_immutable_id": True,
                "promotion": False,
            },
        },
        {
            "name": "description_backfill",
            "command": [
                sys.executable,
                _script("description_backfill"),
                "--once",
                "--batch-size",
                str(config.description_limit),
            ],
            "timeout_seconds": config.stage_timeout_seconds,
            "policy": {
                "source_grounded_first": True,
                "versioned_sidecar": True,
                "description_quality_does_not_upgrade_execution_proof": True,
                "candidate_only": True,
            },
        },
        {
            "name": "usefulness_description_gate",
            "command": [
                sys.executable,
                _script("usefulness_description_gate"),
                "--run",
                "--cap",
                str(config.usefulness_cap),
            ],
            "timeout_seconds": config.stage_timeout_seconds,
            "policy": {
                "candidate_signal_only": True,
                "zero_exit_means_measured_not_promoted": True,
            },
        },
        {
            "name": "deterministic_synthesis_oracle",
            "command": [
                sys.executable,
                _script("deterministic_synthesis_oracle"),
                "--run",
                "--limit",
                str(config.synthesis_limit),
                "--offset",
                str(_positive_int(state.get("synthesis_offset", 0))),
            ],
            "timeout_seconds": config.stage_timeout_seconds,
            "policy": {"deterministic": True, "behavioral_oracle_required": True},
        },
        {
            "name": "verified_recipe_receipts",
            "command": [
                sys.executable,
                _script("verified_recipe_receipts"),
                "--run",
            ],
            "timeout_seconds": config.stage_timeout_seconds,
            "policy": {
                "separate_receipt_store": True,
                "all_hidden_oracles_must_pass": True,
                "source_labels_do_not_authorize_execution": True,
                "revocation_checked_on_read": True,
            },
        },
        {
            "name": "federated_search_overlay_sync",
            "command": [
                sys.executable,
                _script("federated_search_overlay_sync"),
                "--sync",
                "--fast-coverage",
            ],
            "timeout_seconds": config.stage_timeout_seconds,
            "policy": {
                "separate_candidate_overlay": True,
                "governed_default_untouched": True,
                "fast_tick_coverage": True,
                "exact_description_gap_join_runs_as_a_separate_audit": True,
            },
        },
        {
            "name": "embedding_shard_sync",
            "command": [
                sys.executable,
                _script("embedding_shard_sync"),
                "--once",
                "--batch-size",
                str(config.embedding_limit),
            ],
            "timeout_seconds": config.stage_timeout_seconds,
            "policy": {"columns": ["blackbox", "plain", "technical", "semantic", "features"],
                       "rowid_cursor_resumable": True},
        },
        {
            "name": "description_embedding_sync",
            "command": [
                sys.executable,
                _script("description_embedding_sync"),
                "--once",
                "--batch-size",
                str(config.embedding_limit),
            ],
            "timeout_seconds": config.stage_timeout_seconds,
            "policy": {
                "immutable_key": [
                    "primitive_id",
                    "description_digest",
                    "embedding_profile",
                    "model",
                    "dimension",
                ],
                "revisions_reembed": True,
                "offline_only": True,
                "embedding_does_not_prove_semantics_or_execution": True,
            },
        },
    ]


def _run_tick(
    config: LoopConfig,
    state: Mapping[str, Any],
    *,
    runner: Runner = _run_subprocess,
    inventory_provider: InventoryProvider = _real_inventory_provider,
    coverage_provider: CoverageProvider = _read_coverage_manifests,
) -> tuple[dict[str, Any], dict[str, Any]]:
    tick = _positive_int(state.get("tick", 0)) + 1
    stages: list[dict[str, Any]] = []
    blocked_by: str | None = None
    synthesis_succeeded = False
    synthesis_rows_scanned = 0

    for planned in _stage_plan(config, state):
        name = str(planned["name"])
        if blocked_by:
            stages.append(
                {
                    "name": name,
                    "status": "skipped",
                    "blocked_by": blocked_by,
                    "command": planned["command"],
                    "policy": planned["policy"],
                }
            )
            continue
        raw_result = runner(planned["command"], int(planned["timeout_seconds"]))
        result = _trimmed_stage_result(raw_result)
        status = "passed" if result["ok"] else "failed"
        stage = {
            "name": name,
            "status": status,
            "command": planned["command"],
            "timeout_seconds": planned["timeout_seconds"],
            "policy": planned["policy"],
            "result": result,
        }
        stages.append(stage)
        if not result["ok"]:
            blocked_by = name
        elif name == "deterministic_synthesis_oracle":
            synthesis_succeeded = True
            try:
                synthesis_report = json.loads(str(raw_result.get("stdout") or ""))
            except json.JSONDecodeError:
                synthesis_report = {}
            synthesis_rows_scanned = (
                _positive_int(synthesis_report.get("scanned", 0))
                if isinstance(synthesis_report, Mapping) else 0
            )
            stage["progress"] = {"rows_scanned": synthesis_rows_scanned}

    # Inventory is observational and therefore runs even after a pipeline
    # failure.  This preserves a measured receipt without allowing downstream
    # search/embedding stages to proceed after a failed gate.
    inventory_result = dict(inventory_provider(True, config.inventory_timeout_seconds))
    inventory_ok = bool(inventory_result.get("ok"))
    inventory = inventory_result.get("inventory", {}) if inventory_ok else {}
    if not isinstance(inventory, Mapping):
        inventory = {}
        inventory_ok = False
    coverage = dict(coverage_provider())
    target_gates = _target_gate_receipt(inventory, coverage)

    tick_ok = blocked_by is None and inventory_ok
    receipt = {
        "record_type": TICK_RECORD_TYPE,
        "schema_version": SCHEMA_VERSION,
        "tick": tick,
        "generated_at": _utc_now(),
        "mode": "bounded_execution",
        "declared_target": DECLARED_TARGET,
        "stages": stages,
        "pipeline_blocked_by": blocked_by,
        "inventory_stage": inventory_result,
        "inventory": inventory,
        "coverage_manifests": coverage,
        "target_gates": target_gates,
        "tick_ok": tick_ok,
        "policy": {
            "live_scrape_enabled": config.allow_live_scrape,
            "llm_enabled": config.allow_llm,
            "tos_sensitive_live_allowed": False,
            "subprocess_timeouts_enforced": True,
            "target_is_declared_not_measured": True,
        },
        **BOUNDARY,
    }

    next_state = copy.deepcopy(dict(state))
    next_state.update(
        {
            "tick": tick,
            "last_tick_ok": tick_ok,
            "last_blocked_by": blocked_by,
            "last_inventory": dict(inventory),
            "last_target_gates": target_gates,
            "updated_at": receipt["generated_at"],
            **BOUNDARY,
        }
    )
    if synthesis_succeeded:
        next_state["synthesis_offset"] = (
            _positive_int(state.get("synthesis_offset", 0)) + synthesis_rows_scanned
        )
    return receipt, next_state


def _persist_tick(
    config: LoopConfig,
    receipt: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    expected_state_digest: str | None,
) -> dict[str, Any]:
    """Commit a receipt plus resume state with an fsynced recovery record.

    Two ordinary files cannot be renamed atomically as a pair.  The pending transaction makes either crash
    point recoverable and the caller's writer lock prevents duplicate ticks.  The digest check also refuses to
    overwrite a cursor changed by a legacy/non-cooperating writer.
    """

    state_path = config.state_dir / STATE_FILENAME
    if _file_digest_or_none(state_path) != expected_state_digest:
        raise RuntimeError("goal-loop state changed during tick; refusing to overwrite or regress the cursor")
    transaction_id = _tick_transaction_id(receipt, state)
    persisted_receipt = {**dict(receipt), "tick_transaction_id": transaction_id}
    pending = {
        "schema": "aidevobserver_goal_loop_pending_tick",
        "schema_version": SCHEMA_VERSION,
        "tick_transaction_id": transaction_id,
        "receipt": persisted_receipt,
        "state": dict(state),
        **BOUNDARY,
    }
    pending_path = config.state_dir / PENDING_TICK_FILENAME
    _atomic_write_json(pending_path, pending)
    _fsync_directory(config.state_dir)
    ledger_path = config.state_dir / LEDGER_FILENAME
    if not _ledger_has_transaction(ledger_path, transaction_id):
        _append_jsonl(ledger_path, persisted_receipt)
    _atomic_write_json(state_path, state)
    pending_path.unlink()
    _fsync_directory(config.state_dir)
    return persisted_receipt


def _dry_run(
    config: LoopConfig,
    *,
    inventory_provider: InventoryProvider = _real_inventory_provider,
    coverage_provider: CoverageProvider = _read_coverage_manifests,
) -> dict[str, Any]:
    state = _load_state(config.state_dir, config.initial_synthesis_offset)
    inventory_result = dict(inventory_provider(False, config.inventory_timeout_seconds))
    inventory = inventory_result.get("inventory", {}) if inventory_result.get("ok") else {}
    if not isinstance(inventory, Mapping):
        inventory = {}
    coverage = dict(coverage_provider())
    return {
        "record_type": DRY_RUN_RECORD_TYPE,
        "schema_version": SCHEMA_VERSION,
        "mode": "dry_run",
        "declared_target": DECLARED_TARGET,
        "would_run_tick": _positive_int(state.get("tick", 0)) + 1,
        "resume_synthesis_offset": _positive_int(state.get("synthesis_offset", 0)),
        "planned_stages": _stage_plan(config, state),
        "inventory_stage": inventory_result,
        "inventory": inventory,
        "coverage_manifests": coverage,
        "target_gates": _target_gate_receipt(inventory, coverage),
        "writes_performed": False,
        "policy": {
            "live_scrape_enabled": config.allow_live_scrape,
            "llm_enabled": config.allow_llm,
            "tos_sensitive_live_allowed": False,
        },
        **BOUNDARY,
    }


def _execute_ticks(
    config: LoopConfig,
    ticks: int,
    interval_seconds: int,
    *,
    runner: Runner = _run_subprocess,
    inventory_provider: InventoryProvider = _real_inventory_provider,
    coverage_provider: CoverageProvider = _read_coverage_manifests,
    sleep: Sleep = time.sleep,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if ticks < 1:
        raise ValueError("ticks must be at least one")
    receipts: list[dict[str, Any]] = []
    state: dict[str, Any] = {}
    for index in range(ticks):
        with _writer_lock(config.state_dir):
            _recover_pending_tick(config)
            state_path = config.state_dir / STATE_FILENAME
            expected_state_digest = _file_digest_or_none(state_path)
            prior_state = _load_state(config.state_dir, config.initial_synthesis_offset)
            receipt, state = _run_tick(
                config,
                prior_state,
                runner=runner,
                inventory_provider=inventory_provider,
                coverage_provider=coverage_provider,
            )
            persisted_receipt = _persist_tick(
                config,
                receipt,
                state,
                expected_state_digest=expected_state_digest,
            )
            receipts.append(persisted_receipt)
        if index + 1 < ticks:
            sleep(float(interval_seconds))
    return receipts, state


def _fake_coverage(counts: Mapping[str, int] | None = None) -> Mapping[str, Any]:
    values = counts or {
        "federated_search_docs": 17,
        "description_complete_docs": 16,
        "description_sidecar_accepted_current": 8,
        "description_sidecar_usefulness_pass": 8,
        "description_embedding_revisions": 12,
        "description_embedding_primitives": 10,
        "trusted_recipe_receipts": 5,
        "usefulness_full_corpus_docs": 9,
        "embedding_docs": 13,
        "register_embedding_docs": 11,
    }
    return {
        name: {"path": f"fixture/{name}.json", "field": "count", "exists": True, "count": count}
        for name, count in values.items()
    }


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    fake_ladder = {
        "raw_records": 31,
        "candidate": 29,
        "indexed": 23,
        "searchable": 19,
        "composition_ready": 7,
        "valid_syntax": 5,
        "working": 5,
        "verified": 3,
        "promotion_ready": 2,
        "customer_proof": 1,
    }

    def fake_inventory(emit: bool, timeout_seconds: int) -> Mapping[str, Any]:
        del timeout_seconds
        return {
            "ok": True,
            "command": ["fake-inventory", "--emit" if emit else "--read-only"],
            "inventory": {"status_ladder": dict(fake_ladder),
                          "ladder_detail": {
                              "working": {"by_group": {"executed": 5, "synthesized": 2}},
                              "verified": {"by_group": {"executed": 3, "synthesized": 2}},
                          }, **BOUNDARY},
            "result": {"ok": True, "returncode": 0},
        }

    with tempfile.TemporaryDirectory(prefix="aidevobserver-goal-loop-test-") as tmp:
        config = LoopConfig(
            state_dir=Path(tmp),
            source_limit=2,
            question_count=3,
            usefulness_cap=4,
            description_limit=8,
            synthesis_limit=5,
            search_limit=6,
            search_query_sample=2,
            embedding_limit=7,
            stage_timeout_seconds=8,
            inventory_timeout_seconds=9,
            initial_synthesis_offset=0,
        )

        # Default/dry plan is deterministic, read-only, and never opts into
        # network, LLM, or ToS-sensitive live access.
        dry_a = _dry_run(config, inventory_provider=fake_inventory, coverage_provider=_fake_coverage)
        dry_b = _dry_run(config, inventory_provider=fake_inventory, coverage_provider=_fake_coverage)
        checks.append(("dry run is deterministic apart from no volatile fields", dry_a == dry_b))
        checks.append(("dry run writes neither state nor ledger", not any(Path(tmp).iterdir())))
        source_plan = dry_a["planned_stages"][0]
        checks.append(
            (
                "network, LLM, and ToS-sensitive live intake are off by default",
                "--live" not in source_plan["command"]
                and "--use-llm" not in source_plan["command"]
                and "--allow-tos-sensitive-live" not in source_plan["command"],
            )
        )

        # Mutation gate: a failed usefulness/description stage blocks synthesis,
        # search, and both embedding writers, while inventory still runs.
        invoked: list[str] = []

        def failing_runner(command: Sequence[str], timeout_seconds: int) -> Mapping[str, Any]:
            del timeout_seconds
            script_name = Path(command[1]).name
            invoked.append(script_name)
            fail = script_name == _SCRIPTS["usefulness_description_gate"]
            return {
                "ok": not fail,
                "returncode": 1 if fail else 0,
                "stdout": "",
                "stderr": "mutated failure" if fail else "",
            }

        failed_receipt, failed_state = _run_tick(
            config,
            _new_state(),
            runner=failing_runner,
            inventory_provider=fake_inventory,
            coverage_provider=_fake_coverage,
        )
        stage_status = {row["name"]: row["status"] for row in failed_receipt["stages"]}
        checks.append(
            (
                "stage failure halts every downstream writer",
                stage_status["usefulness_description_gate"] == "failed"
                and all(
                    stage_status[name] == "skipped"
                    for name in (
                        "deterministic_synthesis_oracle",
                        "verified_recipe_receipts",
                        "federated_search_overlay_sync",
                        "embedding_shard_sync",
                        "description_embedding_sync",
                    )
                )
                and _SCRIPTS["deterministic_synthesis_oracle"] not in invoked,
            )
        )
        checks.append(
            (
                "inventory still records the real ladder after a blocked tick",
                failed_receipt["inventory"]["status_ladder"] == fake_ladder
                and failed_state["synthesis_offset"] == 0,
            )
        )

        # Target-leak proof: declared target is metadata/gate threshold only;
        # every measured count is exactly the injected inventory/manifest value.
        measured = failed_receipt["target_gates"]["measured_counts"]
        checks.append(
            (
                "declared target never leaks into measured counts",
                measured
                == {
                    "descriptor_specific_working": 5,
                    "descriptor_specific_verified": 3,
                    "family_template_execution": 2,
                    "federated_search_docs": 17,
                    "description_complete_docs": 16,
                    "description_sidecar_accepted_current": 8,
                    "description_sidecar_usefulness_pass": 8,
                    "description_embedding_revisions": 12,
                    "description_embedding_primitives": 10,
                    "trusted_recipe_receipts": 5,
                    "usefulness_full_corpus_docs": 9,
                    "embedding_docs": 13,
                    "register_embedding_docs": 11,
                }
                and DECLARED_TARGET not in measured.values()
                and failed_receipt["target_gates"]["status"] == "not_ready",
            )
        )
        checks.append(
            (
                "description gates require accepted sidecar rows and profile-normalized embeddings",
                failed_receipt["target_gates"]["gates"]["description_coverage"]["source_counts"]
                == {"description_sidecar_accepted_current": 8}
                and failed_receipt["target_gates"]["gates"]["description_embedding_coverage"][
                    "source_counts"
                ]
                == {"description_embedding_primitives": 10}
                and failed_receipt["target_gates"]["count_gates_ready_for_independent_review"] is False,
            )
        )

        # Resume/watch proof with an injected runner and no-op sleeper: two
        # ticks advance both the durable cursor and ledger exactly twice.
        calls: list[tuple[str, int]] = []

        def passing_runner(command: Sequence[str], timeout_seconds: int) -> Mapping[str, Any]:
            calls.append((Path(command[1]).name, timeout_seconds))
            stdout = (
                json.dumps({"scanned": config.synthesis_limit})
                if Path(command[1]).name == _SCRIPTS["deterministic_synthesis_oracle"]
                else "fixture ok"
            )
            return {"ok": True, "returncode": 0, "stdout": stdout,
                    "stderr": "", "elapsed_seconds": 0.0}

        sleeps: list[float] = []
        receipts, state = _execute_ticks(
            config,
            2,
            1,
            runner=passing_runner,
            inventory_provider=fake_inventory,
            coverage_provider=_fake_coverage,
            sleep=sleeps.append,
        )
        resumed = _load_state(Path(tmp))
        ledger_rows = [
            json.loads(line)
            for line in (Path(tmp) / LEDGER_FILENAME).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        checks.append(
            (
                "watch ticks persist and resume the synthesis cursor",
                [row["tick"] for row in receipts] == [1, 2]
                and state["tick"] == resumed["tick"] == 2
                and state["synthesis_offset"] == resumed["synthesis_offset"] == 10
                and len(ledger_rows) == 2
                and sleeps == [1.0],
            )
        )
        checks.append(
            (
                "every executed subprocess receives the configured timeout",
                bool(calls) and all(timeout == config.stage_timeout_seconds for _name, timeout in calls),
            )
        )

        # Replaying an fsynced pending transaction is idempotent: it neither duplicates the ledger row nor
        # regresses state.
        pending = {
            "schema": "aidevobserver_goal_loop_pending_tick",
            "schema_version": SCHEMA_VERSION,
            "tick_transaction_id": receipts[-1]["tick_transaction_id"],
            "receipt": receipts[-1],
            "state": state,
            **BOUNDARY,
        }
        _atomic_write_json(Path(tmp) / PENDING_TICK_FILENAME, pending)
        with _writer_lock(Path(tmp)):
            _recover_pending_tick(config)
        recovered_ledger = [
            json.loads(line)
            for line in (Path(tmp) / LEDGER_FILENAME).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        checks.append(
            (
                "pending tick recovery is idempotent and leaves one durable state cursor",
                len(recovered_ledger) == 2
                and not (Path(tmp) / PENDING_TICK_FILENAME).exists()
                and _load_state(Path(tmp))["tick"] == 2,
            )
        )

        cas_config = LoopConfig(state_dir=Path(tmp) / "cas", initial_synthesis_offset=0)
        cas_state_path = cas_config.state_dir / STATE_FILENAME
        initial_cas_state = _new_state()
        _atomic_write_json(cas_state_path, initial_cas_state)
        stale_digest = _file_digest_or_none(cas_state_path)
        advanced_cas_state = {**initial_cas_state, "tick": 1, "updated_at": _utc_now()}
        _atomic_write_json(cas_state_path, advanced_cas_state)
        try:
            _persist_tick(
                cas_config,
                {"tick": 1, "generated_at": _utc_now(), **BOUNDARY},
                advanced_cas_state,
                expected_state_digest=stale_digest,
            )
        except RuntimeError:
            stale_writer_rejected = True
        else:
            stale_writer_rejected = False
        checks.append(("stale state writers cannot overwrite a newer cursor", stale_writer_rejected))

        # Enabling live/LLM is explicit, but the ToS override remains absent.
        opt_in = LoopConfig(state_dir=Path(tmp), allow_live_scrape=True, allow_llm=True)
        opt_in_command = _stage_plan(opt_in, resumed)[0]["command"]
        checks.append(
            (
                "explicit live and LLM opt-ins never enable ToS-sensitive live sources",
                "--live" in opt_in_command
                and "--use-llm" in opt_in_command
                and "--allow-tos-sensitive-live" not in opt_in_command,
            )
        )

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} failures: {failed}")
        return 1
    print(
        "\nPASS - run_aidevobserver_100m_goal_loop: dry-by-default, bounded and timeout-enforced; "
        "failure blocks downstream writers; inventory remains observational; declared target never becomes a "
        "measured count; state/ledger resume across ticks; network/LLM require opt-in and ToS-sensitive live "
        "sources stay blocked. candidate=true / serves_truth=false."
    )
    return 0


def _positive_cli_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _config_from_args(args: argparse.Namespace) -> LoopConfig:
    return LoopConfig(
        state_dir=Path(args.state_dir).expanduser().resolve(),
        source_limit=args.source_limit,
        question_count=args.question_count,
        usefulness_cap=args.usefulness_cap,
        description_limit=args.description_limit,
        synthesis_limit=args.synthesis_limit,
        search_limit=args.search_limit,
        search_query_sample=args.search_query_sample,
        embedding_limit=args.embedding_limit,
        stage_timeout_seconds=args.stage_timeout,
        inventory_timeout_seconds=args.inventory_timeout,
        allow_live_scrape=args.allow_live_scrape,
        allow_llm=args.allow_llm,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="execute one bounded tick (offline by default)")
    mode.add_argument("--watch", action="store_true", help="execute repeated bounded ticks")
    parser.add_argument("--self-test", action="store_true", help="run a hermetic injected-runner proof")
    parser.add_argument("--interval", type=_positive_cli_int, default=DEFAULT_WATCH_INTERVAL_SECONDS)
    parser.add_argument(
        "--max-ticks",
        type=_positive_cli_int,
        default=1,
        help="ticks in this watch invocation; finite by design (default: 1)",
    )
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--source-limit", type=_positive_cli_int, default=DEFAULT_SOURCE_LIMIT)
    parser.add_argument("--question-count", type=_positive_cli_int, default=DEFAULT_QUESTION_COUNT)
    parser.add_argument("--usefulness-cap", type=_positive_cli_int, default=DEFAULT_USEFULNESS_CAP)
    parser.add_argument("--description-limit", type=_positive_cli_int, default=DEFAULT_DESCRIPTION_LIMIT)
    parser.add_argument("--synthesis-limit", type=_positive_cli_int, default=DEFAULT_SYNTHESIS_LIMIT)
    parser.add_argument("--search-limit", type=_positive_cli_int, default=DEFAULT_SEARCH_LIMIT)
    parser.add_argument("--search-query-sample", type=_positive_cli_int, default=DEFAULT_SEARCH_QUERY_SAMPLE)
    parser.add_argument("--embedding-limit", type=_positive_cli_int, default=DEFAULT_EMBEDDING_LIMIT)
    parser.add_argument("--stage-timeout", type=_positive_cli_int, default=DEFAULT_STAGE_TIMEOUT_SECONDS)
    parser.add_argument("--inventory-timeout", type=_positive_cli_int, default=DEFAULT_INVENTORY_TIMEOUT_SECONDS)
    parser.add_argument(
        "--allow-live-scrape",
        action="store_true",
        help="explicitly allow ordinary live sources; ToS-sensitive live sources remain blocked",
    )
    parser.add_argument("--allow-llm", action="store_true", help="explicitly allow the intake stage to call an LLM")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    config = _config_from_args(args)
    if not args.once and not args.watch:
        print(json.dumps(_dry_run(config), indent=2, sort_keys=True))
        return 0

    ticks = args.max_ticks if args.watch else 1
    receipts, state = _execute_ticks(config, ticks, args.interval)
    print(
        json.dumps(
            {
                "record_type": "aidevobserver_primitive_goal_loop_run_summary",
                "declared_target": DECLARED_TARGET,
                "ticks_executed": len(receipts),
                "last_tick": state["tick"],
                "synthesis_offset": state["synthesis_offset"],
                "all_ticks_ok": all(receipt["tick_ok"] for receipt in receipts),
                "last_target_gates": receipts[-1]["target_gates"],
                "state_path": str(config.state_dir / STATE_FILENAME),
                "ledger_path": str(config.state_dir / LEDGER_FILENAME),
                **BOUNDARY,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all(receipt["tick_ok"] for receipt in receipts) else 1


if __name__ == "__main__":
    raise SystemExit(main())
