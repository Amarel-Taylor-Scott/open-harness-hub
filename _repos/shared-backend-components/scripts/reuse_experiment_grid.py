#!/usr/bin/env python3
"""scripts.reuse_experiment_grid — the COMPREHENSIVE, REPRESENTATIVE reuse experiment. Built because conclusions
were being drawn from tiny non-representative runs. This runs a model zoo across a base project-buildout track plus
two same-task paired proof tracks, writes every attempt to a journal, and reports aggregate statistics with sample
sizes (a cell below MIN_N is explicitly marked "insufficient n", never headlined).

Base lanes:
  * without           — the model builds the project from scratch (baseline capability + token cost)
  * prompt:<variant>  — the verified molecule is presented to the model 6 different ways (does the RIGHT prompt make
                        it reuse instead of re-implement? measured, not assumed) — reimplementation_rate is recorded
  * compose           — deterministic: the composer emits wiring from config; NO model codegen (0 tokens, always run)

Paired own-task tracks (never mislabeled as the five base families):
  * edge_without ↔ edge_gapfill — full priority-search build vs typed-edge partial composition
  * realistic_session_without ↔ realistic_session — full multi-turn input/output accounting without/with a
    read-only mounted verified primitive

Metrics per cell: oracle_pass · input/output tokens · reimplementation/adoption/coverage. Aggregates include exact
lane/model/family groupings and matched both-pass pairs. Transport failures are retryable attempts, zero-token legacy
rows are quarantined, and pooled-model summaries are diagnostic only. serves_truth=false.

    python3 scripts/reuse_experiment_grid.py --self-test
    python3 scripts/reuse_experiment_grid.py --live --models "mistral:codestral-latest,openrouter:z-ai/glm-4.6" \
        --families "semantic_search_engine__stdlib_http__v0,rag_search_tool__stdlib_http__v0" --repeats 5
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import fcntl  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import statistics  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
from typing import Any, Callable  # noqa: E402

import scripts.run_large_project_ab as rlp  # noqa: E402
import scripts.primitive_reuse_prompt_matrix as prm  # noqa: E402
import scripts.edge_exposed_gapfill as edge_gapfill  # noqa: E402
import scripts.realistic_session_harness as realistic_session  # noqa: E402
from scripts.multi_step_task_ab import COMPOSE_STEPS, PrimitiveSessionManager  # noqa: E402
from scripts.reuse_experiment_policy import (  # noqa: E402
    CODEX_OPENROUTER_KEY_COUNT,
    DEFAULT_LIVE_REPEATS,
    REPORTING_MIN_N,
)
from src.teleon.experiments.ids import canonical_id  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "mixed_reuse_experiment_grid"
ARTIFACT_DIR_REL = "data/dev-intel/reuse_experiment_grid"
GRID_FILENAME = "grid.json"
ATTEMPT_JOURNAL_FILENAME = "attempts.jsonl"
LOCK_FILENAME = "grid.lock"
MIN_N = REPORTING_MIN_N
MAX_CONSECUTIVE_TRANSPORT_ERRORS_PER_MODEL = 3
TRACK_BASE = "project_buildout"
TRACK_EDGE_GAPFILL = "edge_gapfill"
TRACK_REALISTIC_SESSION = "realistic_session"
ALL_TRACKS = (TRACK_BASE, TRACK_EDGE_GAPFILL, TRACK_REALISTIC_SESSION)
EDGE_BASELINE_LANE = "edge_without"
EDGE_TREATMENT_LANE = "edge_gapfill"
SESSION_BASELINE_LANE = "realistic_session_without"
SESSION_TREATMENT_LANE = "realistic_session"
DEFAULT_SESSION_MAX_TURNS = 25
DEFAULT_SESSION_TOKEN_BUDGET = 2_000_000
DEFAULT_BASE_REPAIR_TURNS = 2
BASE_PROTOCOL_LEGACY = "legacy"
BASE_PROTOCOL_CURRENT = "current"
LEGACY_BASE_TRACK_CONFIG_ID = "legacy-unfingerprinted-2026-07-09"

# the model zoo (all reachable via the gitignored key pools) — extend by adding a row
MODEL_ZOO = [
    "openrouter:openai/gpt-oss-120b", "openwebui:gemma-4-coding",
    "openrouter:deepseek/deepseek-chat", "openrouter:meta-llama/llama-3.3-70b-instruct",
    "openrouter:z-ai/glm-4.6", "openrouter:qwen/qwen-2.5-coder-32b-instruct", "mistral:codestral-latest",
]
# clean, fast-booting HTTP task families with strict oracles (the ops-API/ETL are heavier — added later)
FAMILIES = [
    "vendor_crud_macro__stdlib_http__v0", "webhook_ingest_worker__stdlib_http__v0",
    "semantic_search_engine__stdlib_http__v0", "labeling_service__stdlib_http__v0",
    "rag_search_tool__stdlib_http__v0",
]
# genome -> deterministic composition spec (inverted from COMPOSE_STEPS) for the compose lane
_COMPOSE_BY_GENOME = {spec["genome"]: spec for spec in COMPOSE_STEPS.values()}


OPENWEBUI_CODING_SYSTEM = "You are an expert software engineer. Return code in fenced ```python blocks."


def _openwebui_agent(prompt: str, model: str = "gemma-4-coding", *,
                     system: str = OPENWEBUI_CODING_SYSTEM, max_tokens: int = 16000) -> dict[str, Any]:
    """Adapt the browser-context CDP client (Gemma via iamretarded.net) to the experiment's agent interface.
    Returns {code, completion_tokens, input_tokens, error}. Session-dependent (needs the logged-in debug Chrome)."""
    try:
        from scripts.openwebui_cdp_client import cdp_chat  # noqa: PLC0415
        r = cdp_chat(prompt, system=system, model=model, max_tokens=max_tokens, timeout=150)
        u = r.get("usage") or {}
        content = r.get("assistant_content", "") or ""
        if not content.strip():
            raise ValueError("response_missing_content")
        input_tokens = u.get("prompt_tokens")
        output_tokens = u.get("completion_tokens")
        return {"code": content,
                "completion_tokens": output_tokens or 0,
                "input_tokens": input_tokens or 0,
                "input_token_source": ("provider" if isinstance(input_tokens, (int, float))
                                       and input_tokens > 0 else "missing"),
                "output_token_source": ("provider" if isinstance(output_tokens, (int, float))
                                        and output_tokens > 0 else "missing"),
                "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"code": "", "completion_tokens": 0, "input_tokens": 0, "error": f"openwebui:{exc}"[:120]}


def _without_cell(gid: str, agent: Callable[[str], dict], repair: int) -> dict[str, Any]:
    lane = rlp.run_lane(gid, "without", agent, repair, "none")
    return {"oracle_pass": lane.get("oracle_pass"), "input_tokens": lane["input_tokens"],
            "output_tokens": lane["output_tokens"], "reimplemented": None,
            "input_token_source": lane.get("input_token_source"),
            "output_token_source": lane.get("output_token_source"),
            "oracle_checks": lane.get("checks") or {},
            "error": lane.get("error")}


def _compose_cell(gid: str) -> dict[str, Any]:
    """Deterministic composition for one family: emit wiring from config, mount the verified molecule, run oracle."""
    spec = _COMPOSE_BY_GENOME.get(gid)
    if spec is None:
        return {"oracle_pass": None, "input_tokens": 0, "output_tokens": 0, "reimplemented": False,
                "note": "no compose template for this family yet"}
    genome, run_buildout = rlp._registry()[gid]
    entry = genome.get("solution_file", "app.py")
    molecule = {fn: s for fn, s in genome["good"].items() if fn != entry}
    app_src = PrimitiveSessionManager().compose_entry(spec["template"], spec["config"])
    res = run_buildout(gid, {entry: app_src}, lane="compose", extra_files=molecule)
    return {"oracle_pass": bool(res["oracle_pass"]), "input_tokens": 0, "output_tokens": 0,
            "reimplemented": False, "oracle_checks": res.get("oracle_checks") or {}}


def _edge_track_config_id() -> str:
    return canonical_id(
        "trackconfig", TRACK_EDGE_GAPFILL, edge_gapfill.TASK_FAMILY, edge_gapfill.COVERAGE_BASIS,
        str(edge_gapfill.coverage_fraction()), edge_gapfill.SEARCH_SERVICE_SOURCE,
        json.dumps(edge_gapfill.TASK_STAGES, sort_keys=True), edge_gapfill._full_prompt(),  # noqa: SLF001
        edge_gapfill._gapfill_prompt(), edge_gapfill._oracle_source(),  # noqa: SLF001
        hashlib.sha256(Path(edge_gapfill.__file__ or "").read_bytes()).hexdigest(),
    )


def _session_track_config_id(max_turns: int, token_budget: int) -> str:
    return canonical_id(
        "trackconfig", TRACK_REALISTIC_SESSION, realistic_session.TASK_FAMILY, str(max_turns), str(token_budget),
        realistic_session.TASK, json.dumps(realistic_session.WORKING_SET, sort_keys=True),
        realistic_session.SESSION_TRANSPORT_SYSTEM, realistic_session._SYSTEM,  # noqa: SLF001
        realistic_session._PRIMITIVE_TOOL, realistic_session._HIDDEN_TEST,  # noqa: SLF001
        realistic_session.VERIFIED_PRIMITIVE_BUNDLE_DIGEST,
        realistic_session.VERIFIED_PRIMITIVE_CORE_DIGEST,
        "stateless_full_transcript_replay", str(realistic_session._CHARS_PER_TOKEN),  # noqa: SLF001
        hashlib.sha256(Path(realistic_session.__file__ or "").read_bytes()).hexdigest(),
    )


def _base_track_config_id(families: list[str], variants: list[str], repair: int) -> str:
    """Fingerprint task prompts, reference mounts, oracle-owning modules, and repair policy."""
    registry = rlp._registry()
    family_protocol: dict[str, Any] = {}
    for family in sorted(families):
        genome, run_buildout = registry[family]
        oracle_module_path = Path(run_buildout.__code__.co_filename)
        family_protocol[family] = {
            "goal": genome.get("goal"),
            "solution_file": genome.get("solution_file", "app.py"),
            "good": genome.get("good"),
            "oracle_module_sha256": hashlib.sha256(oracle_module_path.read_bytes()).hexdigest(),
            "compose_spec": _COMPOSE_BY_GENOME.get(family),
        }
    prompt_module_path = Path(prm.__file__ or "")
    runner_module_path = Path(rlp.__file__ or "")
    return canonical_id(
        "trackconfig", TRACK_BASE, json.dumps(sorted(variants)), str(repair),
        hashlib.sha256(prompt_module_path.read_bytes()).hexdigest(),
        hashlib.sha256(runner_module_path.read_bytes()).hexdigest(),
        json.dumps(family_protocol, sort_keys=True, separators=(",", ":")),
    )


def _resolve_base_track_config_id(protocol: str, families: list[str], variants: list[str], repair: int) -> str:
    if protocol == BASE_PROTOCOL_LEGACY:
        return LEGACY_BASE_TRACK_CONFIG_ID
    if protocol == BASE_PROTOCOL_CURRENT:
        return _base_track_config_id(families, variants, repair)
    raise ValueError(f"unknown base protocol {protocol!r}")


def _edge_cell(lane: str, agent: Callable[[str], dict]) -> dict[str, Any]:
    if lane not in {EDGE_BASELINE_LANE, EDGE_TREATMENT_LANE}:
        raise ValueError(f"unknown grid edge lane: {lane}")
    standalone_lane = "without" if lane == EDGE_BASELINE_LANE else "edge_gapfill"
    row = edge_gapfill.run_lane(standalone_lane, agent)
    return {"oracle_pass": row.get("oracle_pass"), "input_tokens": row.get("input_tokens", 0) or 0,
            "output_tokens": row.get("output_tokens", 0) or 0,
            "input_token_source": row.get("input_token_source"),
            "output_token_source": row.get("output_token_source"),
            "reimplemented": row.get("reimplemented_covered") if lane == EDGE_TREATMENT_LANE else None,
            "coverage_fraction": row.get("coverage_fraction"), "coverage_basis": row.get("coverage_basis"),
            "checks_passed": row.get("checks_passed"), "oracle_checks": row.get("oracle_checks") or {},
            "oracle_observations": row.get("oracle_observations") or {},
            "response_chars": row.get("app_chars", 0),
            "token_accounting": ("reported" if row.get("input_token_source") == "provider"
                                 and row.get("output_token_source") == "provider" else "incomplete"),
            "error": row.get("error")}


def _session_cell(with_db: bool, agent: Callable[[str], dict], max_turns: int,
                  token_budget: int) -> dict[str, Any]:
    row = realistic_session.run_session(
        agent, with_db=with_db, max_turns=max_turns, token_budget=token_budget,
    )
    return {"oracle_pass": row.get("passed"), "input_tokens": row.get("input_tokens", 0) or 0,
            "output_tokens": row.get("output_tokens", 0) or 0, "reimplemented": None,
            "turns": row.get("turns"), "termination_reason": row.get("termination_reason"),
            "primitive_fetched": row.get("primitive_fetched"),
            "primitive_adopted": row.get("primitive_adopted"),
            "used_verified_primitive": row.get("used_verified_primitive"),
            "token_accounting": row.get("token_accounting"),
            "proxy_input_turns": row.get("proxy_input_turns", 0),
            "proxy_output_turns": row.get("proxy_output_turns", 0),
            "primitive_bundle_digest": row.get("primitive_bundle_digest"),
            "primitive_runtime_calls": row.get("primitive_runtime_calls", 0),
            "primitive_causally_required": row.get("primitive_causally_required", False),
            "oracle_checks": row.get("oracle_checks") or {},
            "oracle_observations": row.get("oracle_observations") or {}, "error": row.get("error")}


def _oracle_behavior_digest(checks: dict[str, Any] | None,
                            observations: dict[str, Any] | None) -> str | None:
    if not checks or not observations:
        return None
    normalized = {
        "checks": {str(name): bool(value) for name, value in sorted(checks.items())},
        "observations": observations,
    }
    return hashlib.sha256(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _timed_cell(call: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    started = time.monotonic()
    try:
        result = call()
    except Exception as exc:  # noqa: BLE001 - normalized retryable attempt
        result = {"oracle_pass": None, "input_tokens": 0, "output_tokens": 0,
                  "reimplemented": None, "error": str(exc)[:120]}
    checks = result.get("oracle_checks") or {}
    observations = result.get("oracle_observations") or {}
    return {**result, "oracle_behavior_digest": _oracle_behavior_digest(checks, observations),
            "duration_seconds": round(time.monotonic() - started, 3)}


def _with_usage_provenance(result: dict[str, Any]) -> dict[str, Any]:
    """Never infer exact provider usage from an unlabeled integer counter."""
    normalized = dict(result)
    if not normalized.get("input_token_source"):
        normalized["input_token_source"] = (
            "provider_unverified" if (normalized.get("input_tokens", 0) or 0) > 0 else "missing"
        )
    if not normalized.get("output_token_source"):
        normalized["output_token_source"] = (
            "provider_unverified" if (normalized.get("completion_tokens", 0) or 0) > 0 else "missing"
        )
    return normalized


def _cell_key(r: dict[str, Any]) -> tuple:
    track_config_id = r.get("track_config_id") or ""
    if not track_config_id and (
        r.get("lane") in {"compose", "without"} or str(r.get("lane", "")).startswith("prompt:")
    ):
        # Historical base rows predate protocol fingerprints.  Give them an
        # explicit legacy identity; never reinterpret them as the current
        # fingerprinted protocol.
        track_config_id = LEGACY_BASE_TRACK_CONFIG_ID
    return (r["lane"], r["model"], r["family"], r["repeat"], track_config_id)


def _normalize_tracks(tracks: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    requested = tuple(ALL_TRACKS if "all" in tracks else tracks)
    unknown = sorted(set(requested) - set(ALL_TRACKS))
    if unknown:
        raise ValueError(f"unknown experiment tracks: {unknown}; expected {list(ALL_TRACKS)} or all")
    return tuple(track for track in ALL_TRACKS if track in requested)


def _expected_cell_keys(
    models: list[str], families: list[str], variants: list[str], repeats: int,
    tracks: list[str] | tuple[str, ...], special_repeats: int, session_max_turns: int,
    session_token_budget: int, base_track_config_id: str = LEGACY_BASE_TRACK_CONFIG_ID,
) -> set[tuple]:
    if repeats < 1 or special_repeats < 1 or session_max_turns < 1 or session_token_budget < 1:
        raise ValueError("repeat counts, session max turns, and session token budget must all be positive")
    normalized_tracks = _normalize_tracks(tracks)
    keys: set[tuple] = set()
    if TRACK_BASE in normalized_tracks:
        for family in families:
            keys.add(("compose", "deterministic", family, 0, base_track_config_id))
        for model in models:
            for family in families:
                for repeat in range(repeats):
                    keys.add(("without", model, family, repeat, base_track_config_id))
                    for variant in variants:
                        keys.add((f"prompt:{variant}", model, family, repeat, base_track_config_id))
    if TRACK_EDGE_GAPFILL in normalized_tracks:
        config_id = _edge_track_config_id()
        for model in models:
            for repeat in range(special_repeats):
                for lane in (EDGE_BASELINE_LANE, EDGE_TREATMENT_LANE):
                    keys.add((lane, model, edge_gapfill.TASK_FAMILY, repeat, config_id))
    if TRACK_REALISTIC_SESSION in normalized_tracks:
        config_id = _session_track_config_id(session_max_turns, session_token_budget)
        for model in models:
            for repeat in range(special_repeats):
                for lane in (SESSION_BASELINE_LANE, SESSION_TREATMENT_LANE):
                    keys.add((lane, model, realistic_session.TASK_FAMILY, repeat, config_id))
    return keys


def _plan_id(expected_keys: set[tuple]) -> str:
    """Fingerprint the exact logical cells, not merely their count."""
    payload = json.dumps([list(key) for key in sorted(expected_keys)], separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def _completion_issue(row: dict[str, Any]) -> str | None:
    if row.get("error"):
        return "recorded_error"
    if not isinstance(row.get("oracle_pass"), bool):
        return "missing_oracle_result"
    if row.get("model") != "deterministic":
        input_tokens = row.get("input_tokens", 0) or 0
        output_tokens = row.get("output_tokens", 0) or 0
        if input_tokens == 0 and output_tokens == 0:
            return "zero_token_model_attempt"
    return None


def _attempt_completed(row: dict[str, Any]) -> bool:
    """Only an actually executed oracle result completes a resumable cell.

    Provider/rate-limit/response-schema errors are attempts, not benchmark
    failures.  They stay in the raw ledger for diagnosis but must be retried and
    excluded from pass-rate denominators.
    """
    return _completion_issue(row) is None


def _completed_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the latest completed attempt per logical cell, in stable order."""
    completed: dict[tuple, dict[str, Any]] = {}
    for row in rows:
        if _attempt_completed(row):
            completed[_cell_key(row)] = row
    return [completed[key] for key in sorted(completed)]


def _attempt_identity(row: dict[str, Any]) -> str:
    if row.get("attempt_id"):
        return str(row["attempt_id"])
    payload = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
    return "legacy-" + hashlib.sha256(payload).hexdigest()


def _load_attempts(incremental_path: Path) -> list[dict[str, Any]]:
    """Losslessly union the materialized snapshot with the append-only journal."""
    rows: list[dict[str, Any]] = []
    if incremental_path.exists():
        try:
            prior = json.loads(incremental_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prior = {}
        rows.extend(row for row in prior.get("rows", []) if isinstance(row, dict))
    journal_path = incremental_path.with_name(ATTEMPT_JOURNAL_FILENAME)
    if journal_path.exists():
        for line in journal_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue  # a partial final line is not an executed receipt
            if isinstance(row, dict):
                rows.append(row)
    unique: dict[str, dict[str, Any]] = {}
    for row in rows:
        unique[_attempt_identity(row)] = row
    return list(unique.values())


def _atomic_write(path: Path, content: str) -> None:
    """Write a complete snapshot atomically; the journal remains the recovery log."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _report_from_attempts(
    rows: list[dict[str, Any]], models: list[str], families: list[str], variants: list[str], repeats: int,
    tracks: list[str] | tuple[str, ...] = (TRACK_BASE,), special_repeats: int = DEFAULT_LIVE_REPEATS,
    session_max_turns: int = DEFAULT_SESSION_MAX_TURNS,
    session_token_budget: int = DEFAULT_SESSION_TOKEN_BUDGET,
    base_protocol: str = BASE_PROTOCOL_LEGACY,
    repair: int = DEFAULT_BASE_REPAIR_TURNS,
) -> dict[str, Any]:
    normalized_tracks = _normalize_tracks(tracks)
    base_track_config_id = _resolve_base_track_config_id(base_protocol, families, variants, repair)
    expected_keys = _expected_cell_keys(
        models, families, variants, repeats, normalized_tracks, special_repeats,
        session_max_turns, session_token_budget, base_track_config_id,
    )
    completed_by_key = {_cell_key(row): row for row in _completed_rows(rows)}
    completed = [{**completed_by_key[key], "track_config_id": key[4]}
                 for key in sorted(expected_keys & set(completed_by_key))]
    missing_keys = sorted(expected_keys - set(completed_by_key))
    scoped_attempts = [row for row in rows if _cell_key(row) in expected_keys]
    incomplete_attempts = [row for row in scoped_attempts if not _attempt_completed(row)]
    retryable_errors = [row for row in incomplete_attempts if row.get("error")]
    quarantined = [row for row in incomplete_attempts if _completion_issue(row) == "zero_token_model_attempt"]
    unexpected_completed = set(completed_by_key) - expected_keys
    return {
        "record_type": "reuse_experiment_grid",
        "benchmark_kind": BENCHMARK_KIND,
        "config": {"models": models, "families": families, "variants": variants, "repeats": repeats,
                   "tracks": list(normalized_tracks), "special_repeats": special_repeats,
                   "session_max_turns": session_max_turns,
                   "session_token_budget": session_token_budget,
                   "base_protocol": base_protocol,
                   "base_repair_turns": repair,
                   "track_config_ids": {
                       TRACK_BASE: base_track_config_id,
                       TRACK_EDGE_GAPFILL: _edge_track_config_id(),
                       TRACK_REALISTIC_SESSION: _session_track_config_id(
                           session_max_turns, session_token_budget,
                       ),
                   }},
        "expected_cells": len(expected_keys),
        "plan_id": _plan_id(expected_keys),
        "n_rows": len(completed),
        "n_completed_cells": len(completed),
        "n_missing_cells": len(missing_keys),
        "expected_complete": not missing_keys,
        "missing_cell_keys": [
            {"lane": key[0], "model": key[1], "family": key[2], "repeat": key[3],
             "track_config_id": key[4] or None}
            for key in missing_keys
        ],
        "n_attempts": len(scoped_attempts),
        "n_attempts_all_tracks": len(rows),
        "n_out_of_scope_attempts": len(rows) - len(scoped_attempts),
        "n_incomplete_attempts": len(incomplete_attempts),
        "n_retryable_error_attempts": len(retryable_errors),
        "n_quarantined_attempts": len(quarantined),
        "n_unexpected_completed_cells": len(unexpected_completed),
        "aggregates": aggregate(completed, scoped_attempts),
        "paired_aggregates": paired_aggregates(completed),
        "rows": rows,
        **BOUNDARY,
    }


def run_grid(models: list[str], families: list[str], variants: list[str], repeats: int,
             incremental_path: Path | None = None, repair: int = DEFAULT_BASE_REPAIR_TURNS,
             tracks: list[str] | tuple[str, ...] = (TRACK_BASE,), special_repeats: int = DEFAULT_LIVE_REPEATS,
             session_max_turns: int = DEFAULT_SESSION_MAX_TURNS,
             session_token_budget: int = DEFAULT_SESSION_TOKEN_BUDGET,
             base_protocol: str = BASE_PROTOCOL_LEGACY) -> dict[str, Any]:
    """Full grid, robust + incremental + RESUMABLE. rows carry (lane, model, family, repeat, metrics). If the
    incremental file already has rows, those cells are skipped so an interrupted run continues instead of restarting."""
    rows: list[dict[str, Any]] = []
    done: set[tuple] = set()
    normalized_tracks = _normalize_tracks(tracks)
    base_track_config_id = _resolve_base_track_config_id(base_protocol, families, variants, repair)
    expected_keys = _expected_cell_keys(
        models, families, variants, repeats, normalized_tracks, special_repeats,
        session_max_turns, session_token_budget, base_track_config_id,
    )
    if incremental_path is not None and (
        incremental_path.exists() or incremental_path.with_name(ATTEMPT_JOURNAL_FILENAME).exists()
    ):
        try:
            rows = _load_attempts(incremental_path)
            done = {_cell_key(r) for r in _completed_rows(rows)} & expected_keys
        except Exception:  # noqa: BLE001  corrupt/partial file -> start fresh
            rows, done = [], set()
    from scripts.primitive_token_savings_ab import live_model  # noqa: PLC0415
    def _flush() -> dict[str, Any]:
        rep = _report_from_attempts(
            rows, models, families, variants, repeats, normalized_tracks, special_repeats,
            session_max_turns, session_token_budget, base_protocol, repair,
        )
        if incremental_path is not None:
            _atomic_write(incremental_path, json.dumps(rep, indent=2, sort_keys=True) + "\n")
        return rep

    def _record(row: dict[str, Any]) -> None:
        key = _cell_key(row)
        attempt_number = 1 + sum(1 for prior in rows if _cell_key(prior) == key)
        stamped = {
            **row,
            "attempt_number": attempt_number,
            "attempted_at": datetime.now(timezone.utc).isoformat(),
        }
        stamped["attempt_id"] = canonical_id(
            "gridattempt", *[str(part) for part in key], attempt_number,
            stamped.get("error"), stamped.get("input_tokens"), stamped.get("output_tokens"),
        )
        rows.append(stamped)
        if incremental_path is not None:
            journal_path = incremental_path.with_name(ATTEMPT_JOURNAL_FILENAME)
            with journal_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(stamped, sort_keys=True, separators=(",", ":")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        _flush()

    # compose lane is model-independent — run once per family
    if TRACK_BASE in normalized_tracks:
        for fam in families:
            if ("compose", "deterministic", fam, 0, base_track_config_id) in done:
                continue
            c = _timed_cell(lambda _family=fam: _compose_cell(_family))
            c["reimplemented"] = False
            _record({"track": TRACK_BASE, "benchmark_kind": "real_project_buildout",
                     "track_config_id": base_track_config_id, "lane": "compose", "model": "deterministic",
                     "family": fam, "repeat": 0, **c})

    for mspec in models:
        consecutive_transport_errors = 0
        model_circuit_open = False
        provider, _, model = mspec.partition(":")
        if provider == "openwebui":  # Gemma via iamretarded.net — browser-context CDP, not OpenAI-over-HTTP
            model = model or "gemma-4-coding"

            def agent(prompt: str, _m=model) -> dict:
                return _openwebui_agent(prompt, _m)

            def session_agent(prompt: str, _m=model) -> dict:
                return _openwebui_agent(
                    prompt, _m, system=realistic_session.SESSION_TRANSPORT_SYSTEM, max_tokens=4000,
                )
        else:
            base_url, keyfile, default_model = rlp._PROVIDERS[provider]
            pool = rlp._load_key_file(keyfile) if keyfile else rlp._load_key_file(f"{provider}_keys.txt")
            if provider == "openrouter":
                pool = pool[:CODEX_OPENROUTER_KEY_COUNT]
            model = model or default_model

            def agent(prompt: str, _b=base_url, _m=model, _p=pool) -> dict:
                return _with_usage_provenance(
                    live_model(prompt, _p, _m, max_tokens=16000, strip=False, base_url=_b),
                )

            def session_agent(prompt: str, _b=base_url, _m=model, _p=pool) -> dict:
                return _with_usage_provenance(
                    live_model(prompt, _p, _m, max_tokens=4000, strip=False, base_url=_b),
                )

        def _record_model_attempt(attempt: dict[str, Any]) -> None:
            nonlocal consecutive_transport_errors, model_circuit_open
            _record(attempt)
            if _attempt_completed(attempt):
                consecutive_transport_errors = 0
            else:
                consecutive_transport_errors += 1
                if consecutive_transport_errors >= MAX_CONSECUTIVE_TRANSPORT_ERRORS_PER_MODEL:
                    model_circuit_open = True

        if TRACK_BASE in normalized_tracks:
            for fam in families:
                if model_circuit_open:
                    break
                for rep_i in range(repeats):
                    if model_circuit_open:
                        break
                    if ("without", mspec, fam, rep_i, base_track_config_id) not in done:
                        w = _timed_cell(
                            lambda _family=fam: _without_cell(_family, agent, repair),
                        )
                        attempt = {"track": TRACK_BASE, "benchmark_kind": "real_project_buildout",
                                   "track_config_id": base_track_config_id, "lane": "without", "model": mspec,
                                   "family": fam, "repeat": rep_i, **w}
                        _record_model_attempt(attempt)
                        if model_circuit_open:
                            break
                    for variant in variants:
                        if model_circuit_open:
                            break
                        if (f"prompt:{variant}", mspec, fam, rep_i, base_track_config_id) in done:
                            continue
                        cell = _timed_cell(
                            lambda _family=fam, _variant=variant: prm.run_cell(_family, _variant, agent),
                        )
                        attempt = {"track": TRACK_BASE, "benchmark_kind": "real_project_buildout",
                                   "track_config_id": base_track_config_id,
                                   "lane": f"prompt:{variant}", "model": mspec, "family": fam,
                                   "repeat": rep_i, "oracle_pass": cell["oracle_pass"],
                                   "input_tokens": cell["input_tokens"],
                                   "output_tokens": cell["output_tokens"],
                                   "input_token_source": cell.get("input_token_source"),
                                   "output_token_source": cell.get("output_token_source"),
                                   "duration_seconds": cell.get("duration_seconds"),
                                   "response_chars": cell.get("entry_chars", 0),
                                   "oracle_checks": cell.get("oracle_checks") or {},
                                   "oracle_behavior_digest": cell.get("oracle_behavior_digest"),
                                   "reimplemented": cell["reimplemented"], "error": cell.get("error")}
                        _record_model_attempt(attempt)

        if TRACK_EDGE_GAPFILL in normalized_tracks and not model_circuit_open:
            config_id = _edge_track_config_id()
            for rep_i in range(special_repeats):
                if model_circuit_open:
                    break
                pair_id = canonical_id(
                    "gridpair", TRACK_EDGE_GAPFILL, mspec, edge_gapfill.TASK_FAMILY, str(rep_i), config_id,
                )
                for lane in (EDGE_BASELINE_LANE, EDGE_TREATMENT_LANE):
                    if model_circuit_open:
                        break
                    if (lane, mspec, edge_gapfill.TASK_FAMILY, rep_i, config_id) in done:
                        continue
                    cell = _timed_cell(lambda _lane=lane: _edge_cell(_lane, agent))
                    attempt = {"track": TRACK_EDGE_GAPFILL, "benchmark_kind": edge_gapfill.BENCHMARK_KIND,
                               "scenario_id": edge_gapfill.TASK_FAMILY, "pair_id": pair_id,
                               "track_config_id": config_id, "lane": lane, "model": mspec,
                               "family": edge_gapfill.TASK_FAMILY, "repeat": rep_i, **cell}
                    _record_model_attempt(attempt)

        if TRACK_REALISTIC_SESSION in normalized_tracks and not model_circuit_open:
            config_id = _session_track_config_id(session_max_turns, session_token_budget)
            for rep_i in range(special_repeats):
                if model_circuit_open:
                    break
                pair_id = canonical_id(
                    "gridpair", TRACK_REALISTIC_SESSION, mspec, realistic_session.TASK_FAMILY,
                    str(rep_i), config_id,
                )
                for lane, with_db in (
                    (SESSION_BASELINE_LANE, False), (SESSION_TREATMENT_LANE, True),
                ):
                    if model_circuit_open:
                        break
                    if (lane, mspec, realistic_session.TASK_FAMILY, rep_i, config_id) in done:
                        continue
                    cell = _timed_cell(
                        lambda _with_db=with_db: _session_cell(
                            _with_db, session_agent, session_max_turns, session_token_budget,
                        ),
                    )
                    attempt = {"track": TRACK_REALISTIC_SESSION,
                               "benchmark_kind": realistic_session.BENCHMARK_KIND,
                               "scenario_id": realistic_session.TASK_FAMILY, "pair_id": pair_id,
                               "track_config_id": config_id, "lane": lane, "model": mspec,
                               "family": realistic_session.TASK_FAMILY, "repeat": rep_i, **cell}
                    _record_model_attempt(attempt)
    return _flush()


def _row_has_complete_token_accounting(row: dict[str, Any]) -> bool:
    if row.get("model") == "deterministic":
        return True
    if row.get("input_token_source") == row.get("output_token_source") == "provider":
        return ((row.get("input_tokens", 0) or 0) > 0
                and (row.get("output_tokens", 0) or 0) > 0)
    accounting = row.get("token_accounting")
    if accounting == "reported":
        return ((row.get("input_tokens", 0) or 0) > 0
                and (row.get("output_tokens", 0) or 0) > 0)
    return False


def _agg(cells: list[dict[str, Any]], attempts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    attempts = cells if attempts is None else attempts
    n = len(cells)
    outs = [c.get("output_tokens", 0) or 0 for c in cells]
    ins = [c.get("input_tokens", 0) or 0 for c in cells]
    reimpls = [c["reimplemented"] for c in cells if isinstance(c.get("reimplemented"), bool)]
    adoptions = [c["primitive_adopted"] for c in cells if isinstance(c.get("primitive_adopted"), bool)]
    coverage = [c["coverage_fraction"] for c in cells if isinstance(c.get("coverage_fraction"), (int, float))]
    durations = [float(c["duration_seconds"]) for c in cells
                 if isinstance(c.get("duration_seconds"), (int, float))]
    n_pass = sum(c.get("oracle_pass") is True for c in cells)
    passing_digests = [str(c["oracle_behavior_digest"]) for c in cells
                       if c.get("oracle_pass") is True and c.get("oracle_behavior_digest")]
    digest_counts: dict[str, int] = {}
    for digest in passing_digests:
        digest_counts[digest] = digest_counts.get(digest, 0) + 1
    check_results: dict[str, list[bool]] = {}
    for cell in cells:
        for name, value in (cell.get("oracle_checks") or {}).items():
            check_results.setdefault(str(name), []).append(bool(value))
    attempt_tokens = sum((c.get("input_tokens", 0) or 0) + (c.get("output_tokens", 0) or 0) for c in attempts)
    incomplete_attempts = [c for c in attempts if not _attempt_completed(c)]
    incomplete_attempt_tokens = sum(
        (c.get("input_tokens", 0) or 0) + (c.get("output_tokens", 0) or 0)
        for c in incomplete_attempts
    )
    attempts_missing_token_accounting = sum(not _row_has_complete_token_accounting(c) for c in attempts)
    proxy_or_unverified_attempts = sum(
        c.get("model") != "deterministic"
        and (c.get("token_accounting") == "proxy_mixed"
             or c.get("input_token_source") not in {None, "provider"}
             or c.get("output_token_source") not in {None, "provider"})
        for c in attempts
    )
    d: dict[str, Any] = {"n": n, "n_attempts": len(attempts), "n_pass": n_pass}
    if n < MIN_N:
        d["status"] = f"insufficient n (<{MIN_N})"
    d["pass_rate"] = round(n_pass / n, 3) if n else None
    d["median_out_tokens"] = round(statistics.median(outs), 1) if outs else None
    d["p95_out_tokens"] = round(sorted(outs)[max(0, int(0.95 * len(outs)) - 1)], 1) if outs else None
    d["median_in_tokens"] = round(statistics.median(ins), 1) if ins else None
    d["median_duration_seconds"] = round(statistics.median(durations), 3) if durations else None
    d["p95_duration_seconds"] = (round(sorted(durations)[max(0, int(0.95 * len(durations)) - 1)], 3)
                                 if durations else None)
    # ideation #22/#44: realistic sessions are input-dominated — always report the split
    d["input_output_ratio"] = round(sum(ins) / max(1, sum(outs)), 2) if outs else None
    # ideation #43: ALL recorded attempt tokens, including retryable/provider
    # attempts and oracle failures, divided by passing logical cells.
    d["tokens_per_pass"] = round(attempt_tokens / n_pass, 1) if n_pass else None
    d["tokens_per_pass_status"] = ("lower_bound_missing_usage" if attempts_missing_token_accounting
                                   else "complete_recorded_usage")
    d["attempt_tokens"] = attempt_tokens
    d["incomplete_attempt_tokens"] = incomplete_attempt_tokens
    d["n_attempts_missing_token_accounting"] = attempts_missing_token_accounting
    d["n_proxy_or_unverified_usage_attempts"] = proxy_or_unverified_attempts
    d["n_complete_token_accounting"] = sum(_row_has_complete_token_accounting(c) for c in cells)
    d["n_zero_input_token_rows"] = sum(
        c.get("model") != "deterministic" and (c.get("input_tokens", 0) or 0) == 0 for c in cells
    )
    d["reimpl_rate"] = round(sum(reimpls) / len(reimpls), 3) if reimpls else None
    d["primitive_adoption_rate"] = round(sum(adoptions) / len(adoptions), 3) if adoptions else None
    d["median_coverage_fraction"] = round(statistics.median(coverage), 3) if coverage else None
    d["n_passing_behavior_digests"] = len(passing_digests)
    d["n_distinct_passing_behavior_digests"] = len(digest_counts)
    d["oracle_behavior_digest_stability"] = (
        round(max(digest_counts.values()) / len(passing_digests), 3) if passing_digests else None
    )
    d["oracle_consistency_status"] = (
        "reportable" if len(passing_digests) >= MIN_N else f"insufficient n (<{MIN_N} passing behavior receipts)"
    )
    d["oracle_check_pass_rates"] = {
        name: {"n": len(values), "pass_rate": round(sum(values) / len(values), 3),
               "status": ("reportable" if len(values) >= MIN_N else f"insufficient n (<{MIN_N})")}
        for name, values in sorted(check_results.items())
    }
    return d


def aggregate(rows: list[dict[str, Any]], attempts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Roll up completed cells while charging every scoped attempt to cost-per-pass."""
    attempts = rows if attempts is None else attempts
    key_functions: dict[str, Callable[[dict[str, Any]], str]] = {
        "by_lane": lambda r: r["lane"],
        "by_lane_model": lambda r: f"{r['lane']}|{r['model']}",
        "by_lane_family": lambda r: f"{r['lane']}|{r['family']}",
        "by_lane_model_family": lambda r: f"{r['lane']}|{r['model']}|{r['family']}",
    }
    output: dict[str, Any] = {}
    for label, key_function in key_functions.items():
        completed_groups: dict[str, list[dict[str, Any]]] = {}
        attempt_groups: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            completed_groups.setdefault(key_function(row), []).append(row)
        for row in attempts:
            attempt_groups.setdefault(key_function(row), []).append(row)
        output[label] = {
            key: _agg(completed_groups.get(key, []), attempt_groups.get(key, []))
            for key in sorted(set(completed_groups) | set(attempt_groups))
        }
    return output


def _paired_summary(rows: list[dict[str, Any]], baseline_lane: str, treatment_lane: str) -> dict[str, Any]:
    slots: dict[tuple, dict[str, dict[str, Any]]] = {}
    for row in rows:
        if row.get("lane") not in {baseline_lane, treatment_lane}:
            continue
        identity = (row["model"], row["family"], row["repeat"], row.get("track_config_id", ""))
        slots.setdefault(identity, {})[row["lane"]] = row
    pairs = [
        (arms[baseline_lane], arms[treatment_lane])
        for arms in slots.values()
        if baseline_lane in arms and treatment_lane in arms
    ]
    both_pass = [(baseline, treatment) for baseline, treatment in pairs
                 if baseline.get("oracle_pass") is True and treatment.get("oracle_pass") is True]
    behavior_both_pass = [
        (baseline, treatment) for baseline, treatment in both_pass
        if baseline.get("oracle_behavior_digest")
        and baseline.get("oracle_behavior_digest") == treatment.get("oracle_behavior_digest")
    ]
    adoption_required = treatment_lane == SESSION_TREATMENT_LANE
    exact_both_pass = [
        (baseline, treatment) for baseline, treatment in behavior_both_pass
        if _row_has_complete_token_accounting(baseline)
        and _row_has_complete_token_accounting(treatment)
        and (not adoption_required or treatment.get("primitive_adopted") is True)
    ]
    timed_both_pass = [
        (baseline, treatment) for baseline, treatment in behavior_both_pass
        if isinstance(baseline.get("duration_seconds"), (int, float))
        and isinstance(treatment.get("duration_seconds"), (int, float))
        and (not adoption_required or treatment.get("primitive_adopted") is True)
    ]

    def median_delta(field: str) -> float | None:
        return (round(statistics.median(
            (baseline.get(field, 0) or 0) - (treatment.get(field, 0) or 0)
            for baseline, treatment in exact_both_pass
        ), 1) if exact_both_pass else None)

    def diagnostic_median_delta(field: str) -> float | None:
        return (round(statistics.median(
            (baseline.get(field, 0) or 0) - (treatment.get(field, 0) or 0)
            for baseline, treatment in both_pass
        ), 1) if both_pass else None)

    total_deltas = [
        (baseline.get("input_tokens", 0) or 0) + (baseline.get("output_tokens", 0) or 0)
        - (treatment.get("input_tokens", 0) or 0) - (treatment.get("output_tokens", 0) or 0)
        for baseline, treatment in exact_both_pass
    ]
    median_total_saved = round(statistics.median(total_deltas), 1) if total_deltas else None
    diagnostic_total_deltas = [
        (baseline.get("input_tokens", 0) or 0) + (baseline.get("output_tokens", 0) or 0)
        - (treatment.get("input_tokens", 0) or 0) - (treatment.get("output_tokens", 0) or 0)
        for baseline, treatment in both_pass
    ]
    duration_deltas = [
        float(baseline["duration_seconds"]) - float(treatment["duration_seconds"])
        for baseline, treatment in timed_both_pass
    ]
    median_duration_saved = round(statistics.median(duration_deltas), 3) if duration_deltas else None
    input_reductions = [
        ((baseline.get("input_tokens", 0) or 0) - (treatment.get("input_tokens", 0) or 0))
        / (baseline.get("input_tokens", 0) or 1)
        for baseline, treatment in exact_both_pass
        if (baseline.get("input_tokens", 0) or 0) > 0
    ]
    adoptions = [treatment.get("primitive_adopted") for _, treatment in pairs
                 if isinstance(treatment.get("primitive_adopted"), bool)]
    protocol_fingerprinted = bool(pairs) and all(
        bool(baseline.get("track_config_id")) and bool(treatment.get("track_config_id"))
        and baseline.get("track_config_id") != LEGACY_BASE_TRACK_CONFIG_ID
        and treatment.get("track_config_id") != LEGACY_BASE_TRACK_CONFIG_ID
        for baseline, treatment in pairs
    )
    result: dict[str, Any] = {
        "baseline_lane": baseline_lane,
        "treatment_lane": treatment_lane,
        "n_pairs": len(pairs),
        "n_orphan_arms": sum(len(arms) for arms in slots.values() if len(arms) == 1),
        "n_both_pass": len(both_pass),
        "n_both_pass_behavior_match": len(behavior_both_pass),
        "n_both_pass_complete_token_accounting": len(exact_both_pass),
        "n_both_pass_timed": len(timed_both_pass),
        "n_baseline_only_pass": sum(b.get("oracle_pass") is True and t.get("oracle_pass") is False
                                    for b, t in pairs),
        "n_treatment_only_pass": sum(b.get("oracle_pass") is False and t.get("oracle_pass") is True
                                     for b, t in pairs),
        "n_both_fail": sum(b.get("oracle_pass") is False and t.get("oracle_pass") is False
                           for b, t in pairs),
        "median_input_tokens_saved": median_delta("input_tokens"),
        "median_output_tokens_saved": median_delta("output_tokens"),
        "median_total_tokens_saved": median_total_saved,
        "diagnostic_unverified_median_input_tokens_saved": diagnostic_median_delta("input_tokens"),
        "diagnostic_unverified_median_output_tokens_saved": diagnostic_median_delta("output_tokens"),
        "diagnostic_unverified_median_total_tokens_saved": (
            round(statistics.median(diagnostic_total_deltas), 1) if diagnostic_total_deltas else None
        ),
        "diagnostic_token_status": "unverified usage provenance; never headline eligible",
        "median_duration_seconds_saved": median_duration_saved,
        "median_input_reduction_fraction": (round(statistics.median(input_reductions), 3)
                                            if input_reductions else None),
        "primitive_adoption_rate": round(sum(adoptions) / len(adoptions), 3) if adoptions else None,
        "oracle_behavior_match_rate": (round(len(behavior_both_pass) / len(both_pass), 3)
                                       if both_pass else None),
        "protocol_fingerprinted": protocol_fingerprinted,
        "consistency_reportable": len(behavior_both_pass) >= MIN_N and protocol_fingerprinted,
        "reportable": len(exact_both_pass) >= MIN_N and protocol_fingerprinted,
        "headline_eligible": (len(exact_both_pass) >= MIN_N and protocol_fingerprinted
                              and median_total_saved is not None and median_total_saved > 0),
        "time_reportable": len(timed_both_pass) >= MIN_N and protocol_fingerprinted,
        "time_headline_eligible": (len(timed_both_pass) >= MIN_N and protocol_fingerprinted
                                   and median_duration_saved is not None and median_duration_saved > 0),
    }
    if len(both_pass) < MIN_N:
        result["status"] = f"insufficient n (<{MIN_N} both-pass pairs)"
    if len(exact_both_pass) < MIN_N:
        result["savings_status"] = (
            f"insufficient n (<{MIN_N} behavior-matched both-pass pairs with complete token accounting"
            + (" and proven primitive adoption" if adoption_required else "") + ")"
        )
    if len(timed_both_pass) < MIN_N:
        result["time_savings_status"] = f"insufficient n (<{MIN_N} behavior-matched timed both-pass pairs)"
    if not protocol_fingerprinted:
        result["protocol_status"] = "legacy/unfingerprinted protocol; diagnostic only, never headline eligible"
    return result


def _paired_comparison(rows: list[dict[str, Any]], baseline_lane: str, treatment_lane: str) -> dict[str, Any]:
    relevant = [row for row in rows if row.get("lane") in {baseline_lane, treatment_lane}]
    models = sorted({row["model"] for row in relevant})
    model_families = sorted({(row["model"], row["family"]) for row in relevant})
    overall = _paired_summary(relevant, baseline_lane, treatment_lane)
    overall["headline_eligible"] = False
    overall["time_headline_eligible"] = False
    overall["scope_note"] = "pooled across models; diagnostic only, never a per-model headline"
    return {
        "overall": overall,
        "by_model": {
            model: _paired_summary([row for row in relevant if row["model"] == model],
                                   baseline_lane, treatment_lane)
            for model in models
        },
        "by_model_family": {
            f"{model}|{family}": _paired_summary(
                [row for row in relevant if row["model"] == model and row["family"] == family],
                baseline_lane, treatment_lane,
            )
            for model, family in model_families
        },
    }


def paired_aggregates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Matched same-task comparisons; only both-pass, complete-accounting pairs can headline savings."""
    return {
        "without_vs_full_source_asis": _paired_comparison(
            rows, "without", "prompt:full_source_asis",
        ),
        "edge_without_vs_edge_gapfill": _paired_comparison(
            rows, EDGE_BASELINE_LANE, EDGE_TREATMENT_LANE,
        ),
        "realistic_session_without_vs_realistic_session": _paired_comparison(
            rows, SESSION_BASELINE_LANE, SESSION_TREATMENT_LANE,
        ),
    }


def self_test() -> bool:
    """Mutation-gated + REAL (mocks, no network): (1) grid runs all lanes with a GOOD mock (writes correct wiring)
    -> every prompt+without+compose cell passes; aggregates carry n + flag insufficient-n; (2) a RE-IMPLEMENTING mock
    -> prompt lanes fail + reimpl_rate=1.0 while compose still passes (model-independent); (3) MIN_N guard fires."""
    fams = ["semantic_search_engine__stdlib_http__v0"]
    variants = ["full_source_asis", "signatures_only"]

    # a GOOD mock: return the FULL reference build (all files) for whatever family is asked. The WITHOUT lane needs
    # every file; the PROMPT lanes keep only the entry (run_cell drops mounted molecule files) — both work from this.
    def good_agent(prompt: str) -> dict:
        for gid in FAMILIES:
            g, _ = rlp._registry()[gid]
            if g["goal"][:40] in prompt:
                total = sum(len(s) for s in g["good"].values())
                return {"code": rlp._fenced(g["good"]), "completion_tokens": max(1, total // 4),
                        "input_tokens": max(1, len(prompt) // 4)}
        return {"code": "", "completion_tokens": 0, "input_tokens": 0}

    # run lanes directly with the good agent (bypass provider resolution)
    rows = []
    for fam in fams:
        rows.append({"lane": "compose", "model": "deterministic", "family": fam, "repeat": 0, **_compose_cell(fam)})
        for rep_i in range(2):
            rows.append({"lane": "without", "model": "mock", "family": fam, "repeat": rep_i,
                         **_without_cell(fam, good_agent, 1)})
            for v in variants:
                c = prm.run_cell(fam, v, good_agent)
                rows.append({"lane": f"prompt:{v}", "model": "mock", "family": fam, "repeat": rep_i,
                             "oracle_pass": c["oracle_pass"], "input_tokens": c["input_tokens"],
                             "output_tokens": c["output_tokens"], "reimplemented": c["reimplemented"]})
    agg = aggregate(rows)
    assert agg["by_lane"]["compose"]["pass_rate"] == 1.0, "compose must pass"
    assert agg["by_lane"]["without"]["pass_rate"] == 1.0, "good mock without must pass"
    assert all(agg["by_lane"][f"prompt:{v}"]["pass_rate"] == 1.0 for v in variants), "good wiring passes prompt lanes"
    assert "insufficient n" in agg["by_lane"]["compose"].get("status", ""), "MIN_N guard must flag small cells"

    # re-implementing mock -> prompt fails + reimpl flagged; compose still passes (model-independent)
    reimpl_rows = []
    ra = prm._mock_reimpl_agent(fams[0])
    for v in variants:
        c = prm.run_cell(fams[0], v, ra)
        reimpl_rows.append({"lane": f"prompt:{v}", "model": "mock", "family": fams[0], "repeat": 0,
                            "oracle_pass": c["oracle_pass"], "input_tokens": c["input_tokens"],
                            "output_tokens": c["output_tokens"], "reimplemented": c["reimplemented"]})
    ra_agg = aggregate(reimpl_rows)
    assert all(ra_agg["by_lane"][f"prompt:{v}"]["pass_rate"] == 0.0 for v in variants), "reimpl must fail prompt lanes"
    assert all(ra_agg["by_lane"][f"prompt:{v}"]["reimpl_rate"] == 1.0 for v in variants), "reimpl must be detected"

    # transport mutation: a provider failure is preserved as an attempt but is
    # neither a failed benchmark result nor a completed resumable cell.
    transport = prm.run_cell(
        fams[0], variants[0],
        lambda _prompt: {"code": "", "completion_tokens": 0, "input_tokens": 0, "error": "http503"},
    )
    assert transport["oracle_pass"] is None and transport["error"] == "http503"
    transport_row = {"lane": f"prompt:{variants[0]}", "model": "mock", "family": fams[0],
                     "repeat": 0, **transport}
    assert not _attempt_completed(transport_row) and not _completed_rows([transport_row])

    # Exact plan accounting: no total-count shortcut can hide missing or
    # unexpected keys. Special tracks floor their own one-scenario cohorts at MIN_N.
    base_keys = _expected_cell_keys(
        ["mock"], fams, variants, 2, [TRACK_BASE], MIN_N,
        DEFAULT_SESSION_MAX_TURNS, DEFAULT_SESSION_TOKEN_BUDGET,
    )
    edge_keys = _expected_cell_keys(
        ["mock"], fams, variants, 2, [TRACK_EDGE_GAPFILL], MIN_N,
        DEFAULT_SESSION_MAX_TURNS, DEFAULT_SESSION_TOKEN_BUDGET,
    )
    session_keys = _expected_cell_keys(
        ["mock"], fams, variants, 2, [TRACK_REALISTIC_SESSION], MIN_N,
        DEFAULT_SESSION_MAX_TURNS, DEFAULT_SESSION_TOKEN_BUDGET,
    )
    assert len(base_keys) == len(rows) == 7
    same_size_other_plan = _expected_cell_keys(
        ["different-model"], fams, variants, 2, [TRACK_BASE], MIN_N,
        DEFAULT_SESSION_MAX_TURNS, DEFAULT_SESSION_TOKEN_BUDGET,
    )
    assert len(same_size_other_plan) == len(base_keys)
    assert _plan_id(same_size_other_plan) != _plan_id(base_keys), "equal-sized plans need distinct identities"
    assert len(edge_keys) == len(session_keys) == 2 * MIN_N
    assert len(_expected_cell_keys(
        ["mock"], fams, variants, 2, ["all"], MIN_N,
        DEFAULT_SESSION_MAX_TURNS, DEFAULT_SESSION_TOKEN_BUDGET,
    )) == len(base_keys) + len(edge_keys) + len(session_keys)

    # Legacy 0/0 model rows are quarantined, not misreported as executed
    # oracle failures. This catches the exact historical lost-error shape.
    suspicious = {"lane": "without", "model": "mock", "family": fams[0], "repeat": 0,
                  "oracle_pass": False, "input_tokens": 0, "output_tokens": 0,
                  "reimplemented": None, "error": None}
    assert _completion_issue(suspicious) == "zero_token_model_attempt"
    report = _report_from_attempts(rows + [suspicious], ["mock"], fams, variants, 2)
    assert report["expected_complete"] is True and report["n_completed_cells"] == len(base_keys)
    assert report["n_quarantined_attempts"] == 1 and report["n_missing_cells"] == 0

    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_path = Path(temp_dir) / GRID_FILENAME
        _atomic_write(snapshot_path, json.dumps({"rows": [rows[0]]}))
        journal_path = snapshot_path.with_name(ATTEMPT_JOURNAL_FILENAME)
        journal_path.write_text(json.dumps(rows[1]) + "\n" + "{partial", encoding="utf-8")
        recovered = _load_attempts(snapshot_path)
        assert len(recovered) == 2, "snapshot+journal union must recover complete rows and ignore a partial tail"
        assert json.loads(snapshot_path.read_text(encoding="utf-8"))["rows"] == [rows[0]]

    paired = report["paired_aggregates"]["without_vs_full_source_asis"]["by_model"]["mock"]
    assert paired["n_both_pass"] == 2 and "insufficient n" in paired["status"]
    synthetic_pairs = []
    for repeat in range(MIN_N):
        synthetic_pairs.extend([
            {"lane": "b", "model": "m", "family": "f", "repeat": repeat,
             "oracle_pass": True, "input_tokens": 100, "output_tokens": 100,
             "token_accounting": "reported", "track_config_id": "fingerprinted-test",
             "oracle_behavior_digest": "same-behavior", "duration_seconds": 2.0},
            {"lane": "t", "model": "m", "family": "f", "repeat": repeat,
             "oracle_pass": True, "input_tokens": 50, "output_tokens": 10,
             "token_accounting": "reported", "track_config_id": "fingerprinted-test",
             "oracle_behavior_digest": "same-behavior", "duration_seconds": 1.0},
        ])
    synthetic_summary = _paired_summary(synthetic_pairs, "b", "t")
    assert synthetic_summary["n_both_pass_complete_token_accounting"] == MIN_N
    assert synthetic_summary["headline_eligible"] is True and synthetic_summary["median_total_tokens_saved"] == 140

    # The treatment adapters retain their distinct task identities and real
    # adoption/coverage evidence instead of pretending to cover all base families.
    edge_cell = _edge_cell(
        EDGE_TREATMENT_LANE,
        lambda prompt: {"code": f"```python\n{edge_gapfill._GOOD_GAP_APP}```",  # noqa: SLF001
                        "completion_tokens": 80, "input_tokens": max(1, len(prompt) // 4)},
    )
    assert edge_cell["oracle_pass"] is True and edge_cell["coverage_fraction"] == 0.75
    session_app = realistic_session._correct_app_using_verified_primitive()  # noqa: SLF001
    session_cell = _session_cell(
        True,
        realistic_session._scripted_agent([  # noqa: SLF001
            "PRIMITIVE verify webhook signature",
            f"WRITE app.py\n```python\n{session_app}```",
            "TEST",
        ]),
        4, DEFAULT_SESSION_TOKEN_BUDGET,
    )
    assert session_cell["oracle_pass"] is True and session_cell["primitive_adopted"] is True

    print(f"OK reuse_experiment_grid self-test: full grid orchestrates {len(rows)} cells across lanes "
          f"(compose + without + {len(variants)} prompt variants); GOOD mock passes every lane; RE-IMPL mock fails "
          f"prompt lanes with reimpl_rate=1.0 while COMPOSE stays 1.0 (model-independent); transport-error mutation "
          f"is preserved but excluded/retried; exact expected-key accounting quarantines legacy 0/0 rows; paired "
          f"both-pass savings stay insufficient below MIN_N={MIN_N}; edge-gapfill and realistic-session adapters "
          f"pass real hidden oracles with coverage/adoption evidence. "
          "Ready to run the representative grid. serves_truth=false")
    return True


def emit_summary(rep: dict[str, Any]) -> dict[str, Any]:
    return {"n_rows": rep["n_rows"], "n_attempts": rep.get("n_attempts", rep["n_rows"]),
            "n_retryable_error_attempts": rep.get("n_retryable_error_attempts", 0),
            "n_quarantined_attempts": rep.get("n_quarantined_attempts", 0),
            "expected_cells": rep.get("expected_cells"), "plan_id": rep.get("plan_id"),
            "n_missing_cells": rep.get("n_missing_cells"),
            "expected_complete": rep.get("expected_complete"), "config": rep["config"],
            "by_lane_model": rep["aggregates"]["by_lane_model"],
            "paired_by_model": {
                comparison: data["by_model"] for comparison, data in rep["paired_aggregates"].items()
            }}


def main() -> None:
    ap = argparse.ArgumentParser(description="Comprehensive resumable reuse grid with paired proof tracks.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--reconcile-only", action="store_true",
                    help="rebuild the atomic snapshot from preserved attempts without calling a model")
    ap.add_argument("--expected-only", action="store_true",
                    help="print the exact expected-cell count for this configuration and exit")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--models", default=",".join(MODEL_ZOO))
    ap.add_argument("--families", default=",".join(FAMILIES))
    ap.add_argument("--variants", default="all")
    ap.add_argument("--repeats", type=int, default=MIN_N)
    ap.add_argument("--tracks", default=TRACK_BASE,
                    help=f"comma-separated tracks ({','.join(ALL_TRACKS)}) or all")
    ap.add_argument("--special-repeats", type=int, default=DEFAULT_LIVE_REPEATS,
                    help="repeat count for each one-scenario paired special track")
    ap.add_argument("--session-max-turns", type=int, default=DEFAULT_SESSION_MAX_TURNS)
    ap.add_argument("--session-token-budget", type=int, default=DEFAULT_SESSION_TOKEN_BUDGET)
    ap.add_argument("--base-protocol", choices=(BASE_PROTOCOL_LEGACY, BASE_PROTOCOL_CURRENT),
                    default=BASE_PROTOCOL_LEGACY,
                    help="legacy finishes the inherited diagnostic grid; current requires content-fingerprinted cells")
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    variants_from_args = list(prm.PROMPT_VARIANTS) if args.variants == "all" else args.variants.split(",")
    tracks_from_args = _normalize_tracks(args.tracks.split(","))
    if args.expected_only:
        base_track_config_id = _resolve_base_track_config_id(
            args.base_protocol, args.families.split(","), variants_from_args, DEFAULT_BASE_REPAIR_TURNS,
        )
        keys = _expected_cell_keys(
            args.models.split(","), args.families.split(","), variants_from_args, args.repeats,
            tracks_from_args, args.special_repeats, args.session_max_turns, args.session_token_budget,
            base_track_config_id,
        )
        print(json.dumps({"expected_cells": len(keys), "plan_id": _plan_id(keys),
                         "tracks": list(tracks_from_args), **BOUNDARY},
                         sort_keys=True))
        return
    if args.reconcile_only:
        out = resource(ARTIFACT_DIR_REL); out.mkdir(parents=True, exist_ok=True)
        snapshot_path = out / GRID_FILENAME
        lock_path = out / LOCK_FILENAME
        with lock_path.open("a+", encoding="utf-8") as lock_handle:
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print(json.dumps({"status": "already_running", "lock_path": str(lock_path), **BOUNDARY}))
                raise SystemExit(75)
            rows = _load_attempts(snapshot_path)
            if snapshot_path.exists():
                try:
                    prior_config = json.loads(snapshot_path.read_text(encoding="utf-8")).get("config", {})
                except json.JSONDecodeError:
                    prior_config = {}
            else:
                prior_config = {}
            models = list(prior_config.get("models") or args.models.split(","))
            families = list(prior_config.get("families") or args.families.split(","))
            variants = list(prior_config.get("variants") or (
                variants_from_args
            ))
            repeats = int(prior_config.get("repeats") or args.repeats)
            tracks = _normalize_tracks(list(prior_config.get("tracks") or tracks_from_args))
            special_repeats = int(prior_config.get("special_repeats") or args.special_repeats)
            session_max_turns = int(prior_config.get("session_max_turns") or args.session_max_turns)
            session_token_budget = int(prior_config.get("session_token_budget") or args.session_token_budget)
            base_protocol = str(prior_config.get("base_protocol") or args.base_protocol)
            repair = int(prior_config.get("base_repair_turns") or DEFAULT_BASE_REPAIR_TURNS)
            rep = _report_from_attempts(
                rows, models, families, variants, repeats, tracks, special_repeats,
                session_max_turns, session_token_budget, base_protocol, repair,
            )
            _atomic_write(snapshot_path, json.dumps(rep, indent=2, sort_keys=True) + "\n")
        print(json.dumps(emit_summary(rep), indent=2, sort_keys=True))
        return
    if args.live:
        out = resource(ARTIFACT_DIR_REL); out.mkdir(parents=True, exist_ok=True)
        lock_path = out / LOCK_FILENAME
        with lock_path.open("a+", encoding="utf-8") as lock_handle:
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print(json.dumps({"status": "already_running", "lock_path": str(lock_path), **BOUNDARY}))
                raise SystemExit(75)
            rep = run_grid(
                args.models.split(","), args.families.split(","), variants_from_args, args.repeats,
                incremental_path=out / GRID_FILENAME, tracks=tracks_from_args,
                special_repeats=args.special_repeats, session_max_turns=args.session_max_turns,
                session_token_budget=args.session_token_budget, base_protocol=args.base_protocol,
            )
        print(json.dumps(emit_summary(rep), indent=2, sort_keys=True))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
