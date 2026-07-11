#!/usr/bin/env python3
"""Deterministic JSON hook for primitive-loop actions.

This is the narrow "tool call" surface an LLM can call instead of shelling out.
It accepts one JSON object, validates the requested action against an allowlist,
clamps action arguments, executes fixed argv templates with ``shell=False``, and
writes append-only receipts.

No hook output serves truth. Live model generations, benchmark rows, and system
plans are candidate artifacts until promoted through the normal review gates.

Example:

    python3 scripts/primitive_loop_json_hook.py \
      --request-json '{"action":"gemma_long.once","dry_run":true,"args":{"limit":1}}'
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

_SBC = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "scripts" / "_repo_paths.py").exists()),
    Path(__file__).resolve().parents[1],
)
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))

from scripts._repo_paths import install as _install  # noqa: E402

_install()

from scripts._repo_paths import pythonpath as _pythonpath  # noqa: E402
from scripts._repo_paths import repo_root as _repo_root  # noqa: E402
from scripts._repo_paths import resource as _resource  # noqa: E402


RECORD_TYPE = "primitive_loop_json_hook"
HOOK_SCHEMA = _resource("schemas") / "primitive_loop_hook_request.schema.json"
DEFAULT_OUT_ROOT = _resource("data") / "dev-intel" / "primitive_loop_json_hook"
KNOWN_STATUS_FILES = {
    "billion_primitive_system": _resource("data") / "dev-intel" / "billion_primitive_system" / "latest_status.json",
    "gemma_long_multistep_lane_ledger": (
        _resource("data") / "dev-intel" / "gemma_primitive_lane" / "long_multistep_loop_ledger.jsonl"
    ),
    "primitive_deconstruction_plane_pipeline": (
        _resource("data") / "dev-intel" / "primitive_deconstruction_plane_pipeline" / "latest_status.json"
    ),
    "continuous_primitive_scrape_loop": (
        _resource("data") / "dev-intel" / "continuous_primitive_scrape_loop" / "latest_status.json"
    ),
    "token_savings_experiments": _resource("data") / "dev-intel" / "token_savings_experiments" / "summary.json",
    "realistic_session_benchmarks": (
        _resource("data") / "dev-intel" / "realistic_session_benchmarks" / "latest_status.json"
    ),
    "twenty_million_goal": _resource("data") / "dev-intel" / "primitive_factory" / "20m_goal" / "latest_status.json",
    "twenty_million_supervised_cycle": (
        _resource("data") / "dev-intel" / "primitive_factory" / "20m_goal" / "supervised_latest_status.json"
    ),
}
KNOWN_SERVICE_UNITS = (
    "openwebui-cdp-chromium.service",
    "primitive-live-source-collector.service",
    "primitive-deconstruction-live-loop.service",
    "primitive-gemma-long-multistep-loop.service",
)
SAFE_MODEL_RE = re.compile(r"^[A-Za-z0-9_.:/@+~-]{1,96}$")
DEFAULT_GEMMA_MODEL = "gemma-4-coding"
GEMMA_LIMIT_MAX = 5
GEMMA_MAX_TOKENS_MIN = 512
GEMMA_MAX_TOKENS_FLOOR = 8_192
GEMMA_MAX_TOKENS_DEFAULT = GEMMA_MAX_TOKENS_HARD_CAP = 65_536
GEMMA_TIMEOUT_DEFAULT = 600
GEMMA_TIMEOUT_MAX = 3_600
GEMMA_SLEEP_BETWEEN_CALLS_MIN = 55.0
GEMMA_MIN_HIDDEN_EDGES_DEFAULT = 10
GEMMA_MIN_HIDDEN_EDGES_MAX = 24
GEMMA_MIN_EXAMPLES_DEFAULT = 4
GEMMA_MIN_EXAMPLES_MAX = 12
GEMMA_TOKEN_BUDGET_TIERS = {
    "compact": 12_288,
    "standard": 24_576,
    "advanced": 32_768,
    "frontier": 49_152,
    "exhaustive": 65_536,
}
MAX_INPUT_CONTEXT_TOKENS = 262_144
FLYWHEEL_MAX_ITERATIONS = 10
FLYWHEEL_MAX_CHILD_ACTIONS = 30
COMMAND_OUTPUT_TAIL_CHARS = 16_000
MAX_SOURCE_LIMIT = 500
MAX_QUESTION_COUNT = 5_000
MAX_COMPONENTS_PER_SOURCE = 50
MAX_SOURCES_PER_PARTITION = 500
MAX_DECONSTRUCTION_ATLAS_ROWS = 10_000
MAX_OVERLAYS_PER_PRIMITIVE = 24
MAX_BASE_PRIMITIVES = 20_000
MAX_LLM_CONTEXT_CHARS = 1_000_000


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha(value: Any, *, n: int = 12) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:n]


def _slug(value: str, *, limit: int = 64) -> str:
    chars: list[str] = []
    for char in str(value).lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")[:limit] or "action"


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_stable_json(row) + "\n")
        handle.flush()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"path": str(path), "read_error": str(exc), "exists": True}
    return value if isinstance(value, dict) else {"path": str(path), "non_object_json": True, "exists": True}


def _tail_jsonl_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError as exc:
        return {"path": str(path), "read_error": str(exc), "exists": True}
    for line in reversed(lines[-50:]):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return {"path": str(path), "exists": True, "object_found": False}


def _clamp_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def _clamp_float(value: Any, *, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def _bool(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.lower() in {"1", "true", "yes", "on"})


def _round_up_to(value: int, multiple: int) -> int:
    if multiple <= 1:
        return value
    return ((value + multiple - 1) // multiple) * multiple


def _token_budget_tier(value: Any, *, default: str = "advanced") -> str:
    tier = str(value or default).strip().lower()
    return tier if tier in GEMMA_TOKEN_BUDGET_TIERS else default


def _dynamic_gemma_max_tokens(
    args: dict[str, Any],
    *,
    limit: int,
    min_hidden_edges: int,
    min_examples: int,
    default_tier: str = "advanced",
) -> tuple[int, dict[str, Any]]:
    """Resolve a deterministic completion-token budget for large primitive groups.

    Policy: start at the maximum allowed budget by default. Smaller tiers remain
    available for explicit degraded/retry paths after an issue is observed.
    """
    tier = _token_budget_tier(
        args.get("token_budget_tier") or args.get("primitive_complexity"),
        default=default_tier,
    )
    ceiling = _clamp_int(
        args.get("max_token_ceiling"),
        default=GEMMA_MAX_TOKENS_HARD_CAP,
        minimum=GEMMA_MAX_TOKENS_FLOOR,
        maximum=GEMMA_MAX_TOKENS_HARD_CAP,
    )
    explicit = args.get("max_tokens")
    if explicit is not None:
        resolved = _clamp_int(
            explicit,
            default=GEMMA_TOKEN_BUDGET_TIERS[tier],
            minimum=GEMMA_MAX_TOKENS_MIN,
            maximum=ceiling,
        )
        mode = "explicit"
    else:
        complexity_budget = (
            GEMMA_MAX_TOKENS_FLOOR
            + (max(0, min_hidden_edges) * 960)
            + (max(0, min_examples) * 1_536)
            + (max(0, limit - 1) * 6_144)
        )
        resolved = ceiling
        mode = "maximum_then_adapt_lower_on_issue"
    return resolved, {
        "mode": mode,
        "tier": tier,
        "ceiling": ceiling,
        "hard_cap": GEMMA_MAX_TOKENS_HARD_CAP,
        "floor": GEMMA_MAX_TOKENS_FLOOR,
        "complexity_budget_if_reduced": _round_up_to(complexity_budget, 1_024) if explicit is None else None,
        "min_hidden_edges": min_hidden_edges,
        "min_examples": min_examples,
        "limit": limit,
    }


def _repo_path(value: Any, *, field: str, must_exist: bool = False) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty path string")
    root = _repo_root().resolve()
    raw = Path(value.strip())
    path = raw if raw.is_absolute() else root / raw
    resolved = path.resolve(strict=False)
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"{field} must resolve under repo root: {value}")
    if must_exist and not resolved.exists():
        raise ValueError(f"{field} does not exist: {resolved}")
    return resolved


def _script(name: str) -> Path:
    path = _resource("scripts") / name
    if not path.exists():
        raise ValueError(f"required script is missing: {path}")
    return path


@dataclass(frozen=True)
class CommandPlan:
    action: str
    argv: list[str]
    timeout_seconds: int
    sanitized_args: dict[str, Any]
    side_effects: str
    description: str


def _python_cmd(script_name: str, *args: str) -> list[str]:
    return [sys.executable, str(_script(script_name)), *args]


def _safe_provider(value: Any, *, default: str = "openwebui") -> str:
    provider = str(value or default)
    if provider not in {"openwebui", "ollama", "openrouter"}:
        return default
    return provider


def _safe_mode(value: Any, *, default: str = "cdp") -> str:
    mode = str(value or default)
    return mode if mode in {"direct", "cdp"} else default


def _append_optional_model(argv: list[str], args: dict[str, Any], sanitized: dict[str, Any]) -> None:
    model = args.get("model")
    if model:
        model_text = str(model)
        if not SAFE_MODEL_RE.match(model_text):
            raise ValueError("model contains unsupported characters")
        argv.extend(["--model", model_text])
        sanitized["model"] = model_text


def _build_source_collect_once(action: str, args: dict[str, Any]) -> CommandPlan:
    source_limit = _clamp_int(args.get("source_limit"), default=36, minimum=1, maximum=MAX_SOURCE_LIMIT)
    question_count = _clamp_int(args.get("question_count"), default=720, minimum=120, maximum=MAX_QUESTION_COUNT)
    max_components = _clamp_int(
        args.get("max_components"),
        default=10,
        minimum=1,
        maximum=MAX_COMPONENTS_PER_SOURCE,
    )
    max_sources_per_partition = _clamp_int(
        args.get("max_sources_per_partition"),
        default=50,
        minimum=1,
        maximum=MAX_SOURCES_PER_PARTITION,
    )
    llm_batch_size = _clamp_int(args.get("llm_batch_size"), default=4, minimum=1, maximum=32)
    llm_max_tokens = _clamp_int(
        args.get("llm_max_tokens"),
        default=GEMMA_MAX_TOKENS_HARD_CAP,
        minimum=GEMMA_MAX_TOKENS_MIN,
        maximum=GEMMA_MAX_TOKENS_HARD_CAP,
    )
    llm_timeout = _clamp_int(args.get("llm_timeout"), default=GEMMA_TIMEOUT_DEFAULT, minimum=30, maximum=GEMMA_TIMEOUT_MAX)
    max_llm_context_chars = _clamp_int(
        args.get("max_llm_context_chars"),
        default=MAX_LLM_CONTEXT_CHARS,
        minimum=4_096,
        maximum=MAX_LLM_CONTEXT_CHARS,
    )
    http_timeout = _clamp_int(args.get("http_timeout"), default=30, minimum=3, maximum=120)
    provider = _safe_provider(args.get("provider"), default="openwebui")
    argv = _python_cmd(
        "continuous_primitive_scrape_loop.py",
        "--once",
        "--source-limit",
        str(source_limit),
        "--question-count",
        str(question_count),
        "--max-components",
        str(max_components),
        "--max-sources-per-partition",
        str(max_sources_per_partition),
        "--provider",
        provider,
        "--llm-batch-size",
        str(llm_batch_size),
        "--llm-max-tokens",
        str(llm_max_tokens),
        "--llm-timeout",
        str(llm_timeout),
        "--max-llm-context-chars",
        str(max_llm_context_chars),
        "--http-timeout",
        str(http_timeout),
    )
    sanitized: dict[str, Any] = {
        "source_limit": source_limit,
        "question_count": question_count,
        "max_components": max_components,
        "max_sources_per_partition": max_sources_per_partition,
        "provider": provider,
        "llm_batch_size": llm_batch_size,
        "llm_max_tokens": llm_max_tokens,
        "llm_timeout": llm_timeout,
        "max_llm_context_chars": max_llm_context_chars,
        "http_timeout": http_timeout,
    }
    source_path = args.get("from_jsonl")
    if source_path:
        path = _repo_path(source_path, field="args.from_jsonl", must_exist=True)
        argv.extend(["--from-jsonl", str(path)])
        sanitized["from_jsonl"] = str(path)
    _append_optional_model(argv, args, sanitized)
    if _bool(args.get("live")):
        argv.append("--live")
        sanitized["live"] = True
    if _bool(args.get("allow_tos_sensitive_live")):
        argv.append("--allow-tos-sensitive-live")
        sanitized["allow_tos_sensitive_live"] = True
    if _bool(args.get("store_short_excerpts")):
        argv.append("--store-short-excerpts")
        sanitized["store_short_excerpts"] = True
    if _bool(args.get("use_llm")):
        argv.append("--use-llm")
        sanitized["use_llm"] = True
    return CommandPlan(
        action=action,
        argv=argv,
        timeout_seconds=max(180, min(3_600, 120 + source_limit * 12 + question_count // 10)),
        sanitized_args=sanitized,
        side_effects="write:source-snapshots;write:primitive-candidate-feed;optional-external_call:live-fetch-or-llm",
        description="Run one governed source collection and primitive candidate mining pass.",
    )


def _build_source_collect_self_test(action: str, args: dict[str, Any]) -> CommandPlan:
    return CommandPlan(
        action=action,
        argv=_python_cmd("continuous_primitive_scrape_loop.py", "--self-test"),
        timeout_seconds=180,
        sanitized_args={},
        side_effects="write:temporary-self-test-artifacts",
        description="Run the governed source collection self-test.",
    )


def _build_deconstruction_once(action: str, args: dict[str, Any]) -> CommandPlan:
    question_count = _clamp_int(args.get("question_count"), default=1_315, minimum=120, maximum=MAX_QUESTION_COUNT)
    source_limit = _clamp_int(args.get("source_limit"), default=72, minimum=1, maximum=MAX_SOURCE_LIMIT)
    max_atlas_rows = _clamp_int(
        args.get("max_atlas_rows"),
        default=1_000,
        minimum=0,
        maximum=MAX_DECONSTRUCTION_ATLAS_ROWS,
    )
    overlays_per_primitive = _clamp_int(
        args.get("overlays_per_primitive"),
        default=8,
        minimum=1,
        maximum=MAX_OVERLAYS_PER_PRIMITIVE,
    )
    max_base_primitives = _clamp_int(
        args.get("max_base_primitives"),
        default=0,
        minimum=0,
        maximum=MAX_BASE_PRIMITIVES,
    )
    llm_refine_limit = _clamp_int(args.get("llm_refine_limit"), default=0, minimum=0, maximum=MAX_BASE_PRIMITIVES)
    llm_max_tokens = _clamp_int(
        args.get("llm_max_tokens"),
        default=GEMMA_MAX_TOKENS_HARD_CAP,
        minimum=GEMMA_MAX_TOKENS_MIN,
        maximum=GEMMA_MAX_TOKENS_HARD_CAP,
    )
    llm_timeout = _clamp_int(args.get("llm_timeout"), default=GEMMA_TIMEOUT_DEFAULT, minimum=30, maximum=GEMMA_TIMEOUT_MAX)
    provider = _safe_provider(args.get("provider"), default="openwebui")
    mode = _safe_mode(args.get("mode"), default="cdp")
    argv = _python_cmd(
        "primitive_deconstruction_plane_pipeline.py",
        "--run",
        "--source-limit",
        str(source_limit),
        "--question-count",
        str(question_count),
        "--max-atlas-rows",
        str(max_atlas_rows),
        "--overlays-per-primitive",
        str(overlays_per_primitive),
        "--max-base-primitives",
        str(max_base_primitives),
        "--provider",
        provider,
        "--mode",
        mode,
        "--llm-refine-limit",
        str(llm_refine_limit),
        "--llm-max-tokens",
        str(llm_max_tokens),
        "--llm-timeout",
        str(llm_timeout),
    )
    sanitized: dict[str, Any] = {
        "source_limit": source_limit,
        "question_count": question_count,
        "max_atlas_rows": max_atlas_rows,
        "overlays_per_primitive": overlays_per_primitive,
        "max_base_primitives": max_base_primitives,
        "provider": provider,
        "mode": mode,
        "llm_refine_limit": llm_refine_limit,
        "llm_max_tokens": llm_max_tokens,
        "llm_timeout": llm_timeout,
    }
    from_run_dir = args.get("from_run_dir")
    if from_run_dir:
        path = _repo_path(from_run_dir, field="args.from_run_dir", must_exist=True)
        argv.extend(["--from-run-dir", str(path)])
        sanitized["from_run_dir"] = str(path)
    cdp_url = args.get("cdp_url")
    if cdp_url:
        cdp_text = str(cdp_url)
        if not cdp_text.startswith("http://127.0.0.1:"):
            raise ValueError("cdp_url must be a local 127.0.0.1 HTTP URL")
        argv.extend(["--cdp-url", cdp_text])
        sanitized["cdp_url"] = cdp_text
    _append_optional_model(argv, args, sanitized)
    if _bool(args.get("run_continuous_first")):
        argv.append("--run-continuous-first")
        sanitized["run_continuous_first"] = True
    if _bool(args.get("use_llm")):
        argv.append("--use-llm")
        sanitized["use_llm"] = True
    return CommandPlan(
        action=action,
        argv=argv,
        timeout_seconds=max(180, min(3_600, 120 + question_count // 5 + max_base_primitives // 10)),
        sanitized_args=sanitized,
        side_effects="write:deconstruction-plane-db;write:fully-defined-primitive-feed;optional-external_call:llm",
        description="Run one deconstruction-plane pass to materialize fully-defined primitive candidates.",
    )


def _build_deconstruction_self_test(action: str, args: dict[str, Any]) -> CommandPlan:
    return CommandPlan(
        action=action,
        argv=_python_cmd("primitive_deconstruction_plane_pipeline.py", "--self-test"),
        timeout_seconds=180,
        sanitized_args={},
        side_effects="write:temporary-self-test-artifacts",
        description="Run the deconstruction-plane self-test.",
    )


def _build_gemma_long_once(action: str, args: dict[str, Any]) -> CommandPlan:
    limit = _clamp_int(args.get("limit"), default=1, minimum=1, maximum=GEMMA_LIMIT_MAX)
    offset = _clamp_int(args.get("offset"), default=0, minimum=0, maximum=100_000)
    model_timeout = _clamp_int(
        args.get("timeout"),
        default=GEMMA_TIMEOUT_DEFAULT,
        minimum=30,
        maximum=GEMMA_TIMEOUT_MAX,
    )
    sleep_between_calls = _clamp_float(
        args.get("sleep_between_calls"),
        default=GEMMA_SLEEP_BETWEEN_CALLS_MIN,
        minimum=GEMMA_SLEEP_BETWEEN_CALLS_MIN,
        maximum=900.0,
    )
    min_hidden_edges = _clamp_int(
        args.get("min_hidden_edges"),
        default=GEMMA_MIN_HIDDEN_EDGES_DEFAULT,
        minimum=3,
        maximum=GEMMA_MIN_HIDDEN_EDGES_MAX,
    )
    min_examples = _clamp_int(
        args.get("min_examples"),
        default=GEMMA_MIN_EXAMPLES_DEFAULT,
        minimum=1,
        maximum=GEMMA_MIN_EXAMPLES_MAX,
    )
    max_tokens, token_budget_policy = _dynamic_gemma_max_tokens(
        args,
        limit=limit,
        min_hidden_edges=min_hidden_edges,
        min_examples=min_examples,
        default_tier="exhaustive",
    )
    model = str(args.get("model") or DEFAULT_GEMMA_MODEL)
    if not SAFE_MODEL_RE.match(model):
        raise ValueError("model contains unsupported characters")
    argv = _python_cmd(
        "run_gemma_long_multistep_primitive_lane.py",
        "--once",
        "--limit",
        str(limit),
        "--offset",
        str(offset),
        "--max-tokens",
        str(max_tokens),
        "--timeout",
        str(model_timeout),
        "--sleep-between-calls",
        str(sleep_between_calls),
        "--min-hidden-edges",
        str(min_hidden_edges),
        "--min-examples",
        str(min_examples),
        "--model",
        model,
    )
    source_run_dir = args.get("source_run_dir")
    sanitized: dict[str, Any] = {
        "limit": limit,
        "offset": offset,
        "max_tokens": max_tokens,
        "timeout": model_timeout,
        "sleep_between_calls": sleep_between_calls,
        "min_hidden_edges": min_hidden_edges,
        "min_examples": min_examples,
        "model": model,
        "token_budget_policy": token_budget_policy,
    }
    if source_run_dir:
        path = _repo_path(source_run_dir, field="args.source_run_dir", must_exist=True)
        argv.extend(["--source-run-dir", str(path)])
        sanitized["source_run_dir"] = str(path)
    if _bool(args.get("lane_dry_run")):
        argv.append("--dry-run")
        sanitized["lane_dry_run"] = True
    if _bool(args.get("no_skip_processed")):
        argv.append("--no-skip-processed")
        sanitized["no_skip_processed"] = True
    hook_timeout = model_timeout + int(limit * sleep_between_calls) + 180
    return CommandPlan(
        action=action,
        argv=argv,
        timeout_seconds=max(120, min(2400, hook_timeout)),
        sanitized_args=sanitized,
        side_effects="write:candidate-run-dir;external_call:openwebui-cdp-unless-lane_dry_run",
        description="Generate one bounded batch of long multistep primitive-group candidates through the Gemma lane.",
    )


def _build_gemma_long_self_test(action: str, args: dict[str, Any]) -> CommandPlan:
    return CommandPlan(
        action=action,
        argv=_python_cmd("run_gemma_long_multistep_primitive_lane.py", "--self-test"),
        timeout_seconds=120,
        sanitized_args={},
        side_effects="write:temporary-self-test-artifacts",
        description="Run the bounded self-test for the Gemma long multistep primitive lane.",
    )


def _build_billion_plan_run(action: str, args: dict[str, Any]) -> CommandPlan:
    return CommandPlan(
        action=action,
        argv=_python_cmd("build_billion_primitive_system_plan.py", "--run"),
        timeout_seconds=120,
        sanitized_args={},
        side_effects="write:candidate-plan-run-dir",
        description="Materialize a candidate billion-primitive system plan bundle.",
    )


def _build_billion_plan_self_test(action: str, args: dict[str, Any]) -> CommandPlan:
    return CommandPlan(
        action=action,
        argv=_python_cmd("build_billion_primitive_system_plan.py", "--self-test"),
        timeout_seconds=120,
        sanitized_args={},
        side_effects="write:append-only-self-test-plan-run-dir",
        description="Run the billion primitive system plan self-test.",
    )


def _build_twenty_million_goal_run(action: str, args: dict[str, Any]) -> CommandPlan:
    target = _clamp_int(args.get("target"), default=20_000_000, minimum=1_000_000, maximum=200_000_000)
    rows_per_shard = _clamp_int(args.get("rows_per_shard"), default=10_000, minimum=1_000, maximum=100_000)
    daily_working_target = _clamp_int(
        args.get("daily_working_target"),
        default=100_000,
        minimum=1_000,
        maximum=5_000_000,
    )
    daily_candidate_target = _clamp_int(
        args.get("daily_candidate_target"),
        default=400_000,
        minimum=daily_working_target,
        maximum=20_000_000,
    )
    horizon_days = _clamp_int(args.get("horizon_days"), default=60, minimum=1, maximum=365)
    start_date = str(args.get("start_date") or dt.datetime.now(dt.timezone.utc).date().isoformat())
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", start_date):
        start_date = dt.datetime.now(dt.timezone.utc).date().isoformat()
    argv = _python_cmd(
        "build_twenty_million_primitive_goal.py",
        "--run",
        "--target",
        str(target),
        "--rows-per-shard",
        str(rows_per_shard),
        "--daily-working-target",
        str(daily_working_target),
        "--daily-candidate-target",
        str(daily_candidate_target),
        "--horizon-days",
        str(horizon_days),
        "--start-date",
        start_date,
    )
    return CommandPlan(
        action=action,
        argv=argv,
        timeout_seconds=240,
        sanitized_args={
            "target": target,
            "rows_per_shard": rows_per_shard,
            "daily_working_target": daily_working_target,
            "daily_candidate_target": daily_candidate_target,
            "horizon_days": horizon_days,
            "start_date": start_date,
        },
        side_effects="write:20m-goal-control-plane",
        description="Materialize the 20M primitive goal plan across deterministic, nondeterministic, hybrid, research, remix, benchmark, proof, and negative-memory generators.",
    )


def _build_twenty_million_goal_self_test(action: str, args: dict[str, Any]) -> CommandPlan:
    return CommandPlan(
        action=action,
        argv=_python_cmd("build_twenty_million_primitive_goal.py", "--self-test"),
        timeout_seconds=120,
        sanitized_args={},
        side_effects="none-or-self-test-only",
        description="Run the 20M primitive goal planner self-test.",
    )


def _build_twenty_million_cycle_run(action: str, args: dict[str, Any]) -> CommandPlan:
    seed_rows = _clamp_int(args.get("seed_rows"), default=100_000, minimum=10_000, maximum=2_000_000)
    rows_per_shard = _clamp_int(args.get("rows_per_shard"), default=10_000, minimum=1_000, maximum=100_000)
    compile_shards = _clamp_int(args.get("compile_shards"), default=2, minimum=1, maximum=20)
    start_shard = _clamp_int(args.get("start_shard"), default=-1, minimum=-1, maximum=10_000)
    limit_per_shard = _clamp_int(args.get("limit_per_shard"), default=0, minimum=0, maximum=rows_per_shard)
    package_limit_per_shard = _clamp_int(
        args.get("package_limit_per_shard"),
        default=0,
        minimum=0,
        maximum=rows_per_shard,
    )
    benchmark_n = _clamp_int(args.get("benchmark_n"), default=300, minimum=25, maximum=5_000)
    benchmark_k = _clamp_int(args.get("benchmark_k"), default=5, minimum=1, maximum=20)
    benchmark_seed = _clamp_int(args.get("benchmark_seed"), default=23, minimum=0, maximum=1_000_000)
    argv = _python_cmd(
        "run_twenty_million_supervised_cycle.py",
        "--run",
        "--seed-rows",
        str(seed_rows),
        "--rows-per-shard",
        str(rows_per_shard),
        "--compile-shards",
        str(compile_shards),
        "--start-shard",
        str(start_shard),
        "--limit-per-shard",
        str(limit_per_shard),
        "--package-limit-per-shard",
        str(package_limit_per_shard),
        "--benchmark-n",
        str(benchmark_n),
        "--benchmark-k",
        str(benchmark_k),
        "--benchmark-seed",
        str(benchmark_seed),
    )
    if not (args.get("paraphrase") is False):
        argv.append("--paraphrase")
    else:
        argv.append("--no-paraphrase")
    return CommandPlan(
        action=action,
        argv=argv,
        timeout_seconds=max(900, min(7_200, 300 + seed_rows // 1_000 + compile_shards * 180 + benchmark_n)),
        sanitized_args={
            "seed_rows": seed_rows,
            "rows_per_shard": rows_per_shard,
            "compile_shards": compile_shards,
            "start_shard": start_shard,
            "limit_per_shard": limit_per_shard,
            "package_limit_per_shard": package_limit_per_shard,
            "benchmark_n": benchmark_n,
            "benchmark_k": benchmark_k,
            "benchmark_seed": benchmark_seed,
            "paraphrase": not (args.get("paraphrase") is False),
        },
        side_effects="write:20m-supervised-cycle;write:seed-slice;write:verified-candidates;write:linkable-cards;write:benchmarks",
        description="Run one supervised 20M primitive generation, packaging, and benchmark cycle.",
    )


def _build_twenty_million_cycle_self_test(action: str, args: dict[str, Any]) -> CommandPlan:
    return CommandPlan(
        action=action,
        argv=_python_cmd("run_twenty_million_supervised_cycle.py", "--self-test"),
        timeout_seconds=120,
        sanitized_args={},
        side_effects="none-or-self-test-only",
        description="Run the 20M supervised cycle self-test.",
    )


def _build_token_savings_self_test(action: str, args: dict[str, Any]) -> CommandPlan:
    return CommandPlan(
        action=action,
        argv=_python_cmd("run_token_savings_experiments.py", "--self-test"),
        timeout_seconds=180,
        sanitized_args={},
        side_effects="none-or-self-test-only",
        description="Run the bounded token-savings verifier self-test.",
    )


def _build_token_savings_small_run(action: str, args: dict[str, Any]) -> CommandPlan:
    n = _clamp_int(args.get("n"), default=100, minimum=1, maximum=5_000)
    k = _clamp_int(args.get("k"), default=5, minimum=1, maximum=20)
    seed = _clamp_int(args.get("seed"), default=7, minimum=0, maximum=1_000_000)
    corpus = _clamp_int(args.get("corpus"), default=20_000, minimum=0, maximum=200_000)
    intent_mode = str(args.get("intent_mode") or "paraphrase")
    if intent_mode not in {"descriptive", "paraphrase", "external"}:
        intent_mode = "paraphrase"
    argv = _python_cmd(
        "run_token_savings_experiments.py",
        "--run",
        "--n",
        str(n),
        "--k",
        str(k),
        "--seed",
        str(seed),
        "--corpus",
        str(corpus),
        "--intent-mode",
        intent_mode,
    )
    sanitized = {"n": n, "k": k, "seed": seed, "corpus": corpus, "intent_mode": intent_mode}
    if _bool(args.get("emit_gaps")):
        argv.append("--emit-gaps")
        sanitized["emit_gaps"] = True
    return CommandPlan(
        action=action,
        argv=argv,
        timeout_seconds=max(180, min(1800, 90 + n // 2)),
        sanitized_args=sanitized,
        side_effects="write:token-savings-summary;optional-write:research-queue-gaps",
        description="Run a bounded reuse-vs-rebuild token-savings experiment over the real primitive search index.",
    )


def _build_session_benchmarks_self_test(action: str, args: dict[str, Any]) -> CommandPlan:
    return CommandPlan(
        action=action,
        argv=_python_cmd("run_realistic_session_benchmarks.py", "--self-test"),
        timeout_seconds=180,
        sanitized_args={},
        side_effects="none-or-self-test-only",
        description="Run the realistic multi-prompt session benchmark self-test.",
    )


def _build_session_benchmarks_run(action: str, args: dict[str, Any]) -> CommandPlan:
    sessions = _clamp_int(args.get("sessions"), default=12, minimum=1, maximum=500)
    turns_per_session = _clamp_int(args.get("turns_per_session"), default=0, minimum=0, maximum=20)
    k = _clamp_int(args.get("k"), default=8, minimum=1, maximum=20)
    components_per_turn = _clamp_int(args.get("components_per_turn"), default=4, minimum=1, maximum=12)
    seed = _clamp_int(args.get("seed"), default=41, minimum=0, maximum=1_000_000)
    base_limit = _clamp_int(args.get("base_limit"), default=30_000, minimum=0, maximum=300_000)
    supervised_limit = _clamp_int(args.get("supervised_limit"), default=80_000, minimum=0, maximum=500_000)
    max_cycles = _clamp_int(args.get("max_cycles"), default=5, minimum=0, maximum=100)
    context_window = _clamp_int(
        args.get("context_window"),
        default=MAX_INPUT_CONTEXT_TOKENS,
        minimum=4_096,
        maximum=MAX_INPUT_CONTEXT_TOKENS,
    )
    scenario_mode = str(args.get("scenario_mode") or "mixed")
    if scenario_mode not in {"mixed", "warehouse", "app", "regulated", "platform", "ml_lifecycle", "large_org", "kaggle"}:
        scenario_mode = "mixed"
    include_supervised = args.get("include_supervised") is not False
    compare_base = args.get("compare_base") is not False
    argv = _python_cmd(
        "run_realistic_session_benchmarks.py",
        "--run",
        "--sessions",
        str(sessions),
        "--turns-per-session",
        str(turns_per_session),
        "--k",
        str(k),
        "--components-per-turn",
        str(components_per_turn),
        "--seed",
        str(seed),
        "--base-limit",
        str(base_limit),
        "--supervised-limit",
        str(supervised_limit),
        "--max-cycles",
        str(max_cycles),
        "--scenario-mode",
        scenario_mode,
        "--context-window",
        str(context_window),
    )
    argv.append("--include-supervised" if include_supervised else "--no-include-supervised")
    argv.append("--compare-base" if compare_base else "--no-compare-base")
    return CommandPlan(
        action=action,
        argv=argv,
        timeout_seconds=max(300, min(7_200, 180 + sessions * max(8, turns_per_session or 8) * 8)),
        sanitized_args={
            "sessions": sessions,
            "turns_per_session": turns_per_session,
            "k": k,
            "components_per_turn": components_per_turn,
            "seed": seed,
            "base_limit": base_limit,
            "supervised_limit": supervised_limit,
            "max_cycles": max_cycles,
            "scenario_mode": scenario_mode,
            "context_window": context_window,
            "include_supervised": include_supervised,
            "compare_base": compare_base,
        },
        side_effects="write:realistic-session-benchmark;write:scenario-catalog;write:turn-and-session-receipts",
        description="Run realistic multi-prompt app, agent, warehouse, compliance, platform, ML lifecycle, and large-organization build benchmarks.",
    )



def _build_executor_synth_run(action: str, args: dict[str, Any]) -> CommandPlan:
    limit = _clamp_int(args.get("limit"), default=20, minimum=1, maximum=1000)
    argv = _python_cmd("spec_to_executor_synthesizer.py", "--run", "--limit", str(limit))
    sanitized: dict[str, Any] = {"limit": limit}
    specs = args.get("specs")
    if specs:
        path = _repo_path(specs, field="args.specs", must_exist=True)
        argv.extend(["--specs", str(path)]); sanitized["specs"] = str(path)
    return CommandPlan(action=action, argv=argv, timeout_seconds=max(300, min(3600, 60 + limit * 30)),
                       sanitized_args=sanitized, side_effects="write:synthesis-receipts;external_call:hy3-llm",
                       description="Hy3-draft executors+fixtures for needs_executor specs -> security gate -> sandbox -> promote.")


def _build_executor_synth_self_test(action: str, args: dict[str, Any]) -> CommandPlan:
    return CommandPlan(action=action, argv=_python_cmd("spec_to_executor_synthesizer.py", "--self-test"),
                       timeout_seconds=180, sanitized_args={}, side_effects="write:none",
                       description="Offline mutation-gated self-test of the executor synthesizer.")


def _build_weak_capability_run(action: str, args: dict[str, Any]) -> CommandPlan:
    argv = _python_cmd("weak_capability_primitive_closer.py", "--run")
    sanitized: dict[str, Any] = {}
    cap = args.get("capability")
    if isinstance(cap, str) and cap.replace("_", "").isalnum():
        argv.extend(["--capability", cap]); sanitized["capability"] = cap
    return CommandPlan(action=action, argv=argv, timeout_seconds=3600, sanitized_args=sanitized,
                       side_effects="write:closed-gap-receipts;external_call:hy3-llm",
                       description="Hy3 synthesizer over the measured-weak-capability specs -> fixture-proven primitives.")


def _build_weak_capability_self_test(action: str, args: dict[str, Any]) -> CommandPlan:
    return CommandPlan(action=action, argv=_python_cmd("weak_capability_primitive_closer.py", "--self-test"),
                       timeout_seconds=180, sanitized_args={}, side_effects="write:none",
                       description="Offline self-test of the weak-capability closer.")


def _build_autonomous_factory_once(action: str, args: dict[str, Any]) -> CommandPlan:
    cycles = _clamp_int(args.get("max_cycles"), default=1, minimum=1, maximum=5)
    cyc_min = _clamp_int(args.get("cycle_minutes"), default=10, minimum=1, maximum=60)
    argv = _python_cmd("autonomous_primitive_factory_loop.py", "--run", "--max-cycles", str(cycles),
                       "--cycle-minutes", str(cyc_min))
    return CommandPlan(action=action, argv=argv, timeout_seconds=max(600, min(7200, cycles * cyc_min * 60 + 300)),
                       sanitized_args={"max_cycles": cycles, "cycle_minutes": cyc_min},
                       side_effects="write:cycle-receipts;write:candidate-feeds;external_call:hy3-llm",
                       description="Run N bounded autonomous cycles: scrape->deconstruct->Hy3 manufacture->Hy3 synth.")


def _build_autonomous_factory_self_test(action: str, args: dict[str, Any]) -> CommandPlan:
    return CommandPlan(action=action, argv=_python_cmd("autonomous_primitive_factory_loop.py", "--self-test"),
                       timeout_seconds=180, sanitized_args={}, side_effects="write:none",
                       description="Offline self-test of the autonomous factory loop.")


COMMAND_BUILDERS: dict[str, Callable[[str, dict[str, Any]], CommandPlan]] = {
    "source_collect.once": _build_source_collect_once,
    "source_collect.self_test": _build_source_collect_self_test,
    "deconstruction.once": _build_deconstruction_once,
    "deconstruction.self_test": _build_deconstruction_self_test,
    "gemma_long.once": _build_gemma_long_once,
    "gemma_long.self_test": _build_gemma_long_self_test,
    "billion_plan.run": _build_billion_plan_run,
    "billion_plan.self_test": _build_billion_plan_self_test,
    "twenty_million_goal.run": _build_twenty_million_goal_run,
    "twenty_million_goal.self_test": _build_twenty_million_goal_self_test,
    "twenty_million_cycle.run": _build_twenty_million_cycle_run,
    "twenty_million_cycle.self_test": _build_twenty_million_cycle_self_test,
    "token_savings.self_test": _build_token_savings_self_test,
    "token_savings.run_small": _build_token_savings_small_run,
    "session_benchmarks.self_test": _build_session_benchmarks_self_test,
    "session_benchmarks.run": _build_session_benchmarks_run,
    "executor_synth.run": _build_executor_synth_run,
    "executor_synth.self_test": _build_executor_synth_self_test,
    "weak_capability.run": _build_weak_capability_run,
    "weak_capability.self_test": _build_weak_capability_self_test,
    "autonomous_factory.once": _build_autonomous_factory_once,
    "autonomous_factory.self_test": _build_autonomous_factory_self_test,
}
NON_COMMAND_ACTIONS = ("actions.list", "status.snapshot", "loop.services.status")


def action_specs() -> dict[str, Any]:
    return {
        "record_type": "primitive_loop_hook_action_specs",
        "schema": str(HOOK_SCHEMA),
        "candidate": True,
        "serves_truth": False,
        "actions": {
            "actions.list": {
                "description": "Return this allowlist and example request shapes.",
                "side_effects": "write:hook-receipt-only",
                "args": {},
            },
            "status.snapshot": {
                "description": "Read latest append-only loop status files; include service status only on request.",
                "side_effects": "read:status-files;optional-read:systemd-user-services",
                "args": {"include_services": "bool default false"},
            },
            "loop.services.status": {
                "description": "Check known user-level loop service units with systemctl --user is-active.",
                "side_effects": "read:systemd-user-services",
                "args": {},
            },
            "flywheel.run": {
                "description": "Run a bounded supervisor pass that snapshots status, benchmarks reuse, plans scale work, and schedules Gemma generation through child hook calls.",
                "side_effects": "write:hook-receipts;optional-write:candidate-runs;optional-external_call:openwebui-cdp",
                "args": {
                    "iterations": f"int clamped 1..{FLYWHEEL_MAX_ITERATIONS}",
                    "max_child_actions": f"int clamped 1..{FLYWHEEL_MAX_CHILD_ACTIONS}",
                    "mode": "balanced|generate|benchmark|supervise|full",
                    "include_services": "bool default false",
                    "execute_live_model": "bool default false",
                    "force_live_gemma": "bool default false",
                    "avoid_duplicate_gemma": "bool default true",
                    "run_token_benchmark": "bool default true except supervise mode",
                    "run_source_collect": "bool default false; run upstream governed source collection in this pass",
                    "run_deconstruction": "bool default false; run deconstruction-plane materialization in this pass",
                    "run_full_chain": "bool default false; equivalent to mode=full for upstream source+deconstruction",
                    "source_question_count": f"int clamped 120..{MAX_QUESTION_COUNT}",
                    "source_limit": f"int clamped 1..{MAX_SOURCE_LIMIT}",
                    "source_max_components": f"int clamped 1..{MAX_COMPONENTS_PER_SOURCE}",
                    "deconstruction_question_count": f"int clamped 120..{MAX_QUESTION_COUNT}",
                    "deconstruction_overlays_per_primitive": f"int clamped 1..{MAX_OVERLAYS_PER_PRIMITIVE}",
                    "deconstruction_max_base_primitives": f"int clamped 0..{MAX_BASE_PRIMITIVES}",
                    "refresh_plan": "bool default false",
                    "gemma_max_tokens": f"int clamped 512..{GEMMA_MAX_TOKENS_HARD_CAP}; defaults to maximum",
                    "max_token_ceiling": f"int clamped 8192..{GEMMA_MAX_TOKENS_HARD_CAP}",
                    "token_budget_tier": "compact|standard|advanced|frontier|exhaustive; used only after explicit downshift",
                    "gemma_limit": f"int clamped 1..{GEMMA_LIMIT_MAX}",
                    "input_context_tokens": f"metadata budget clamped 4096..{MAX_INPUT_CONTEXT_TOKENS}; defaults to maximum",
                    "output_context_tokens": f"metadata budget clamped 512..{GEMMA_MAX_TOKENS_HARD_CAP}; defaults to maximum",
                    "auto_reduce_on_issue": "bool default true; retry live Gemma once at half budget if max budget fails",
                },
            },
            "source_collect.once": {
                "description": "Run one governed source queue to primitive-candidate mining pass.",
                "side_effects": "write:source-snapshots;write:primitive-candidate-feed;optional-external_call:live-fetch-or-llm",
                "args": {
                    "from_jsonl": "optional repo-contained JSONL source queue",
                    "source_limit": f"int clamped 1..{MAX_SOURCE_LIMIT}",
                    "question_count": f"int clamped 120..{MAX_QUESTION_COUNT}",
                    "max_components": f"int clamped 1..{MAX_COMPONENTS_PER_SOURCE}",
                    "max_sources_per_partition": f"int clamped 1..{MAX_SOURCES_PER_PARTITION}",
                    "live": "bool default false",
                    "use_llm": "bool default false",
                    "llm_max_tokens": f"int clamped 512..{GEMMA_MAX_TOKENS_HARD_CAP}",
                    "max_llm_context_chars": f"int clamped 4096..{MAX_LLM_CONTEXT_CHARS}",
                },
            },
            "source_collect.self_test": {
                "description": "Run the governed source collection self-test.",
                "side_effects": "write:temporary-self-test-artifacts",
                "args": {},
            },
            "deconstruction.once": {
                "description": "Run one deconstruction-plane pass to produce fully-defined primitive candidates.",
                "side_effects": "write:deconstruction-plane-db;write:fully-defined-primitive-feed;optional-external_call:llm",
                "args": {
                    "from_run_dir": "optional repo-contained continuous source run",
                    "question_count": f"int clamped 120..{MAX_QUESTION_COUNT}",
                    "source_limit": f"int clamped 1..{MAX_SOURCE_LIMIT}",
                    "max_atlas_rows": f"int clamped 0..{MAX_DECONSTRUCTION_ATLAS_ROWS}",
                    "overlays_per_primitive": f"int clamped 1..{MAX_OVERLAYS_PER_PRIMITIVE}",
                    "max_base_primitives": f"int clamped 0..{MAX_BASE_PRIMITIVES}",
                    "use_llm": "bool default false",
                    "llm_refine_limit": f"int clamped 0..{MAX_BASE_PRIMITIVES}",
                    "llm_max_tokens": f"int clamped 512..{GEMMA_MAX_TOKENS_HARD_CAP}",
                },
            },
            "deconstruction.self_test": {
                "description": "Run the deconstruction-plane self-test.",
                "side_effects": "write:temporary-self-test-artifacts",
                "args": {},
            },
            "gemma_long.once": {
                "description": "Run one bounded Gemma long multistep primitive generation batch.",
                "side_effects": "write:candidate-run-dir;external_call:openwebui-cdp-unless-lane_dry_run",
                "args": {
                    "source_run_dir": "optional repo-contained path",
                    "limit": f"int clamped 1..{GEMMA_LIMIT_MAX}",
                    "offset": "int clamped 0..100000",
                    "max_tokens": f"int clamped 512..{GEMMA_MAX_TOKENS_HARD_CAP}; omitted means maximum",
                    "max_token_ceiling": f"int clamped 8192..{GEMMA_MAX_TOKENS_HARD_CAP}",
                    "token_budget_tier": "compact|standard|advanced|frontier|exhaustive; used only for reduced explicit budgets",
                    "timeout": f"int clamped 30..{GEMMA_TIMEOUT_MAX}",
                    "sleep_between_calls": "float clamped 55..900",
                    "min_hidden_edges": f"int clamped 3..{GEMMA_MIN_HIDDEN_EDGES_MAX}",
                    "min_examples": f"int clamped 1..{GEMMA_MIN_EXAMPLES_MAX}",
                    "lane_dry_run": "bool; execute underlying lane without live model calls",
                    "no_skip_processed": "bool",
                },
            },
            "gemma_long.self_test": {
                "description": "Run the Gemma lane offline self-test.",
                "side_effects": "write:temporary-self-test-artifacts",
                "args": {},
            },
            "billion_plan.run": {
                "description": "Materialize the candidate agents/tools/shards/gates plan bundle.",
                "side_effects": "write:candidate-plan-run-dir",
                "args": {},
            },
            "billion_plan.self_test": {
                "description": "Run the billion-plan self-test.",
                "side_effects": "write:append-only-self-test-plan-run-dir",
                "args": {},
            },
            "twenty_million_goal.run": {
                "description": "Materialize the 20M primitive goal control plane across deterministic, nondeterministic, hybrid, research, remix, benchmark, proof, and negative-memory generators.",
                "side_effects": "write:20m-goal-control-plane",
                "args": {
                    "target": "int clamped 1000000..200000000; default 20000000",
                    "rows_per_shard": "int clamped 1000..100000; default 10000",
                    "daily_working_target": "int clamped 1000..5000000; default 100000",
                    "daily_candidate_target": "int clamped daily_working_target..20000000; default 400000",
                    "horizon_days": "int clamped 1..365; default 60",
                    "start_date": "YYYY-MM-DD; default today UTC",
                },
            },
            "twenty_million_goal.self_test": {
                "description": "Run the 20M primitive goal planner self-test.",
                "side_effects": "none-or-self-test-only",
                "args": {},
            },
            "twenty_million_cycle.run": {
                "description": "Run one supervised 20M generation cycle: seed slice, compile, verify, package, benchmark before/after, refresh counts.",
                "side_effects": "write:20m-supervised-cycle;write:seed-slice;write:verified-candidates;write:linkable-cards;write:benchmarks",
                "args": {
                    "seed_rows": "int clamped 10000..2000000; default 100000",
                    "rows_per_shard": "int clamped 1000..100000; default 10000",
                    "compile_shards": "int clamped 1..20; default 2",
                    "start_shard": "int clamped -1..10000; -1 means next unused shard window",
                    "limit_per_shard": "int clamped 0..rows_per_shard; 0 means full shard",
                    "package_limit_per_shard": "int clamped 0..rows_per_shard; 0 means full shard",
                    "benchmark_n": "int clamped 25..5000; default 300",
                    "benchmark_k": "int clamped 1..20; default 5",
                    "benchmark_seed": "int clamped 0..1000000; default 23",
                    "paraphrase": "bool default true",
                },
            },
            "twenty_million_cycle.self_test": {
                "description": "Run the 20M supervised cycle self-test.",
                "side_effects": "none-or-self-test-only",
                "args": {},
            },
            "token_savings.self_test": {
                "description": "Run the deterministic token-savings verifier self-test.",
                "side_effects": "none-or-self-test-only",
                "args": {},
            },
            "token_savings.run_small": {
                "description": "Run bounded real-card reuse-vs-rebuild token-savings experiments.",
                "side_effects": "write:token-savings-summary;optional-write:research-queue-gaps",
                "args": {
                    "n": "int clamped 1..5000",
                    "k": "int clamped 1..20",
                    "seed": "int clamped 0..1000000",
                    "corpus": "int clamped 0..200000",
                    "intent_mode": "descriptive|paraphrase|external",
                    "emit_gaps": "bool default false",
                },
            },
            "session_benchmarks.self_test": {
                "description": "Run the realistic multi-prompt app/warehouse/session benchmark self-test.",
                "side_effects": "none-or-self-test-only",
                "args": {},
            },
            "session_benchmarks.run": {
                "description": "Run realistic multi-prompt sessions for full app builds, data warehouse builds, agent platforms, compliance workflows, and platform migrations.",
                "side_effects": "write:realistic-session-benchmark;write:scenario-catalog;write:turn-and-session-receipts",
                "args": {
                    "sessions": "int clamped 1..500; default 12",
                    "turns_per_session": "int clamped 0..20; 0 means all template turns",
                    "k": "int clamped 1..20; default 8",
                    "components_per_turn": "int clamped 1..12; default 4",
                    "seed": "int clamped 0..1000000; default 41",
                    "base_limit": "int clamped 0..300000; default 30000",
                    "supervised_limit": "int clamped 0..500000; default 80000",
                    "max_cycles": "int clamped 0..100; default 5",
                    "scenario_mode": "mixed|warehouse|app|regulated|platform|ml_lifecycle|large_org",
                    "context_window": f"int clamped 4096..{MAX_INPUT_CONTEXT_TOKENS}; default maximum",
                    "include_supervised": "bool default true",
                    "compare_base": "bool default true",
                },
            },
        },
        "examples": [
            {
                "action": "gemma_long.once",
                "dry_run": True,
                "args": {"limit": 1, "lane_dry_run": True},
            },
            {
                "action": "token_savings.run_small",
                "args": {"n": 100, "k": 5, "seed": 7, "intent_mode": "paraphrase"},
            },
            {
                "action": "session_benchmarks.run",
                "args": {"sessions": 12, "k": 8, "components_per_turn": 4, "scenario_mode": "mixed"},
            },
            {"action": "billion_plan.run"},
            {"action": "twenty_million_goal.run", "args": {"target": 20_000_000, "horizon_days": 60}},
            {
                "action": "twenty_million_cycle.run",
                "args": {"seed_rows": 100_000, "compile_shards": 2, "benchmark_n": 300},
            },
            {
                "action": "flywheel.run",
                "args": {
                    "iterations": 1,
                    "mode": "full",
                    "execute_live_model": False,
                    "input_context_tokens": MAX_INPUT_CONTEXT_TOKENS,
                    "output_context_tokens": GEMMA_MAX_TOKENS_HARD_CAP,
                    "max_token_ceiling": GEMMA_MAX_TOKENS_HARD_CAP,
                },
            },
        ],
    }


class PrimitiveLoopHook:
    def __init__(self, out_root: Path = DEFAULT_OUT_ROOT):
        self.out_root = out_root

    def _new_run_dir(self, action: str, request: dict[str, Any]) -> tuple[str, Path]:
        run_id = f"primitive-loop-hook-{_stamp()}-{_slug(action)}-{_sha({'request': request, 'ns': time.time_ns()})}"
        run_dir = self.out_root / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        return run_id, run_dir

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(request, dict):
            raise ValueError("request must be a JSON object")
        action = str(request.get("action") or "")
        if not action:
            raise ValueError("request.action is required")
        run_id, run_dir = self._new_run_dir(action, request)
        receipt_base = {
            "record_type": RECORD_TYPE,
            "run_id": run_id,
            "run_dir": str(run_dir),
            "created_at": _utc(),
            "action": action,
            "request_id": request.get("request_id"),
            "candidate": True,
            "serves_truth": False,
        }
        _write_json(run_dir / "request.json", {"received_at": _utc(), "request": request})
        try:
            response = self._dispatch(request, run_dir, receipt_base)
        except Exception as exc:  # noqa: BLE001 - hook errors must still be receipt-backed.
            response = {
                **receipt_base,
                "ok": False,
                "accepted": False,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }
        _write_json(run_dir / "response.json", response)
        _append_jsonl(self.out_root / "hook_ledger.jsonl", response)
        return response

    def _dispatch(self, request: dict[str, Any], run_dir: Path, base: dict[str, Any]) -> dict[str, Any]:
        action = str(request.get("action") or "")
        args = request.get("args") or {}
        if not isinstance(args, dict):
            raise ValueError("request.args must be an object when present")
        dry_run = _bool(request.get("dry_run"))
        if action == "actions.list":
            return {
                **base,
                "ok": True,
                "accepted": True,
                "dry_run": dry_run,
                "result": action_specs(),
            }
        if action == "status.snapshot":
            include_services = _bool(args.get("include_services"))
            return {
                **base,
                "ok": True,
                "accepted": True,
                "dry_run": dry_run,
                "result": status_snapshot(include_services=include_services),
            }
        if action == "loop.services.status":
            return {
                **base,
                "ok": True,
                "accepted": True,
                "dry_run": dry_run,
                "result": service_statuses(),
            }
        if action == "flywheel.run":
            return {
                **base,
                "ok": True,
                "accepted": True,
                "dry_run": dry_run,
                "result": flywheel_run(self, run_dir=run_dir, args=args, parent_dry_run=dry_run),
            }
        builder = COMMAND_BUILDERS.get(action)
        if builder is None:
            raise ValueError(f"unsupported action: {action}")
        plan = builder(action, args)
        _write_json(
            run_dir / "planned_command.json",
            {
                "action": plan.action,
                "argv": plan.argv,
                "timeout_seconds": plan.timeout_seconds,
                "sanitized_args": plan.sanitized_args,
                "side_effects": plan.side_effects,
                "description": plan.description,
                "shell": False,
            },
        )
        if dry_run:
            return {
                **base,
                "ok": True,
                "accepted": True,
                "dry_run": True,
                "executed": False,
                "plan": {
                    "argv": plan.argv,
                    "timeout_seconds": plan.timeout_seconds,
                    "sanitized_args": plan.sanitized_args,
                    "side_effects": plan.side_effects,
                    "description": plan.description,
                    "shell": False,
                },
            }
        completed = run_command(plan, run_dir)
        return {
            **base,
            "ok": completed["returncode"] == 0,
            "accepted": True,
            "dry_run": False,
            "executed": True,
            "plan": {
                "argv": plan.argv,
                "timeout_seconds": plan.timeout_seconds,
                "sanitized_args": plan.sanitized_args,
                "side_effects": plan.side_effects,
                "description": plan.description,
                "shell": False,
            },
            "command": completed,
        }


def run_command(plan: CommandPlan, run_dir: Path) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = _pythonpath()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = _utc()
    try:
        result = subprocess.run(
            plan.argv,
            cwd=str(_repo_root()),
            env=env,
            text=True,
            capture_output=True,
            timeout=plan.timeout_seconds,
            shell=False,
            check=False,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        (run_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
        (run_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
        return {
            "started_at": started,
            "finished_at": _utc(),
            "returncode": result.returncode,
            "stdout_path": str(run_dir / "stdout.txt"),
            "stderr_path": str(run_dir / "stderr.txt"),
            "stdout_tail": stdout[-COMMAND_OUTPUT_TAIL_CHARS:],
            "stderr_tail": stderr[-COMMAND_OUTPUT_TAIL_CHARS:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        (run_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
        (run_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
        return {
            "started_at": started,
            "finished_at": _utc(),
            "returncode": 124,
            "stdout_path": str(run_dir / "stdout.txt"),
            "stderr_path": str(run_dir / "stderr.txt"),
            "stdout_tail": stdout[-COMMAND_OUTPUT_TAIL_CHARS:],
            "stderr_tail": stderr[-COMMAND_OUTPUT_TAIL_CHARS:],
            "timed_out": True,
            "timeout_seconds": plan.timeout_seconds,
        }


def status_snapshot(*, include_services: bool = False) -> dict[str, Any]:
    statuses: dict[str, Any] = {}
    for name, path in KNOWN_STATUS_FILES.items():
        if path.suffix == ".jsonl":
            status = _tail_jsonl_object(path)
        else:
            status = _read_json(path)
        statuses[name] = {
            "path": str(path),
            "exists": path.exists(),
            "latest": status,
        }
    result = {
        "record_type": "primitive_loop_status_snapshot",
        "created_at": _utc(),
        "statuses": statuses,
        "candidate": True,
        "serves_truth": False,
    }
    if include_services:
        result["services"] = service_statuses()
    return result


def service_statuses() -> dict[str, Any]:
    services: dict[str, Any] = {}
    for unit in KNOWN_SERVICE_UNITS:
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", unit],
                cwd=str(_repo_root()),
                text=True,
                capture_output=True,
                timeout=8,
                shell=False,
                check=False,
            )
            services[unit] = {
                "returncode": result.returncode,
                "active_state": (result.stdout or "").strip(),
                "stderr": (result.stderr or "").strip()[-1000:],
            }
        except Exception as exc:  # noqa: BLE001
            services[unit] = {"error": str(exc), "error_type": type(exc).__name__}
    return {
        "record_type": "primitive_loop_service_statuses",
        "created_at": _utc(),
        "services": services,
        "candidate": True,
        "serves_truth": False,
    }


def _latest_status(snapshot: dict[str, Any], key: str) -> dict[str, Any]:
    statuses = snapshot.get("statuses") if isinstance(snapshot, dict) else {}
    item = statuses.get(key) if isinstance(statuses, dict) else {}
    latest = item.get("latest") if isinstance(item, dict) else {}
    return latest if isinstance(latest, dict) else {}


def _latest_deconstruction_run_dir(snapshot: dict[str, Any]) -> str:
    latest = _latest_status(snapshot, "primitive_deconstruction_plane_pipeline")
    outputs = latest.get("outputs") if isinstance(latest.get("outputs"), dict) else {}
    run_dir = str(outputs.get("run_dir") or latest.get("run_dir") or "")
    return run_dir


def _service_state(service_result: dict[str, Any], unit: str) -> str:
    services = service_result.get("services") if isinstance(service_result, dict) else {}
    item = services.get(unit) if isinstance(services, dict) else {}
    return str(item.get("active_state") or "unknown") if isinstance(item, dict) else "unknown"


def flywheel_run(
    hook: PrimitiveLoopHook,
    *,
    run_dir: Path,
    args: dict[str, Any],
    parent_dry_run: bool,
) -> dict[str, Any]:
    """Run a bounded supervisor pass through child hook calls.

    The flywheel deliberately composes the same allowlisted JSON actions rather
    than reaching around the hook. This gives every child action its own receipt
    and keeps live model calls opt-in.
    """
    mode = str(args.get("mode") or "balanced")
    if mode not in {"balanced", "generate", "benchmark", "supervise", "full"}:
        mode = "balanced"
    iterations = _clamp_int(args.get("iterations"), default=1, minimum=1, maximum=FLYWHEEL_MAX_ITERATIONS)
    max_child_actions = _clamp_int(
        args.get("max_child_actions"),
        default=8,
        minimum=1,
        maximum=FLYWHEEL_MAX_CHILD_ACTIONS,
    )
    include_services = _bool(args.get("include_services"))
    execute_live_model = _bool(args.get("execute_live_model"))
    force_live_gemma = _bool(args.get("force_live_gemma"))
    avoid_duplicate_gemma = not (args.get("avoid_duplicate_gemma") is False)
    auto_reduce_on_issue = not (args.get("auto_reduce_on_issue") is False)
    run_token_benchmark = _bool(args.get("run_token_benchmark")) or mode in {"balanced", "benchmark"}
    if mode == "supervise" and args.get("run_token_benchmark") is None:
        run_token_benchmark = False
    refresh_plan = _bool(args.get("refresh_plan"))
    run_full_chain = _bool(args.get("run_full_chain")) or mode == "full"
    run_source_collect = run_full_chain or _bool(args.get("run_source_collect"))
    run_deconstruction = run_full_chain or _bool(args.get("run_deconstruction"))
    run_gemma = mode in {"balanced", "generate", "full"} and not _bool(args.get("skip_gemma"))
    token_n = _clamp_int(args.get("token_n"), default=100, minimum=1, maximum=5_000)
    token_k = _clamp_int(args.get("token_k"), default=5, minimum=1, maximum=20)
    token_corpus = _clamp_int(args.get("token_corpus"), default=20_000, minimum=0, maximum=200_000)
    token_seed = _clamp_int(args.get("token_seed"), default=7, minimum=0, maximum=1_000_000)
    token_intent_mode = str(args.get("token_intent_mode") or "paraphrase")
    if token_intent_mode not in {"descriptive", "paraphrase", "external"}:
        token_intent_mode = "paraphrase"
    gemma_limit = _clamp_int(args.get("gemma_limit"), default=1, minimum=1, maximum=GEMMA_LIMIT_MAX)
    gemma_output_ceiling = _clamp_int(
        args.get("max_token_ceiling"),
        default=GEMMA_MAX_TOKENS_HARD_CAP,
        minimum=GEMMA_MAX_TOKENS_FLOOR,
        maximum=GEMMA_MAX_TOKENS_HARD_CAP,
    )
    gemma_max_tokens = _clamp_int(
        args.get("gemma_max_tokens"),
        default=gemma_output_ceiling,
        minimum=GEMMA_MAX_TOKENS_MIN,
        maximum=gemma_output_ceiling,
    )
    gemma_timeout = _clamp_int(
        args.get("gemma_timeout"),
        default=max(GEMMA_TIMEOUT_DEFAULT, 420),
        minimum=30,
        maximum=GEMMA_TIMEOUT_MAX,
    )
    gemma_min_hidden_edges = _clamp_int(
        args.get("gemma_min_hidden_edges"),
        default=GEMMA_MIN_HIDDEN_EDGES_DEFAULT,
        minimum=3,
        maximum=GEMMA_MIN_HIDDEN_EDGES_MAX,
    )
    gemma_min_examples = _clamp_int(
        args.get("gemma_min_examples"),
        default=GEMMA_MIN_EXAMPLES_DEFAULT,
        minimum=1,
        maximum=GEMMA_MIN_EXAMPLES_MAX,
    )
    source_limit = _clamp_int(args.get("source_limit"), default=36, minimum=1, maximum=MAX_SOURCE_LIMIT)
    source_question_count = _clamp_int(
        args.get("source_question_count"),
        default=720,
        minimum=120,
        maximum=MAX_QUESTION_COUNT,
    )
    source_max_components = _clamp_int(
        args.get("source_max_components"),
        default=10,
        minimum=1,
        maximum=MAX_COMPONENTS_PER_SOURCE,
    )
    deconstruction_question_count = _clamp_int(
        args.get("deconstruction_question_count"),
        default=1_315,
        minimum=120,
        maximum=MAX_QUESTION_COUNT,
    )
    deconstruction_overlays_per_primitive = _clamp_int(
        args.get("deconstruction_overlays_per_primitive"),
        default=8,
        minimum=1,
        maximum=MAX_OVERLAYS_PER_PRIMITIVE,
    )
    deconstruction_max_base_primitives = _clamp_int(
        args.get("deconstruction_max_base_primitives"),
        default=0,
        minimum=0,
        maximum=MAX_BASE_PRIMITIVES,
    )
    input_context_tokens = _clamp_int(
        args.get("input_context_tokens"),
        default=MAX_INPUT_CONTEXT_TOKENS,
        minimum=4_096,
        maximum=MAX_INPUT_CONTEXT_TOKENS,
    )
    output_context_tokens = _clamp_int(
        args.get("output_context_tokens"),
        default=gemma_output_ceiling,
        minimum=GEMMA_MAX_TOKENS_MIN,
        maximum=gemma_output_ceiling,
    )
    children: list[dict[str, Any]] = []
    child_index = 0

    policy = {
        "mode": mode,
        "iterations": iterations,
        "max_child_actions": max_child_actions,
        "include_services": include_services,
        "execute_live_model": execute_live_model,
        "force_live_gemma": force_live_gemma,
        "avoid_duplicate_gemma": avoid_duplicate_gemma,
        "auto_reduce_on_issue": auto_reduce_on_issue,
        "run_token_benchmark": run_token_benchmark,
        "run_full_chain": run_full_chain,
        "run_source_collect": run_source_collect,
        "run_deconstruction": run_deconstruction,
        "refresh_plan": refresh_plan,
        "context_budget": {
            "input_context_tokens": input_context_tokens,
            "output_context_tokens": output_context_tokens,
            "gemma_output_ceiling": gemma_output_ceiling,
            "command_output_tail_chars": COMMAND_OUTPUT_TAIL_CHARS,
        },
        "source_collect_policy": {
            "source_limit": source_limit,
            "question_count": source_question_count,
            "max_components": source_max_components,
            "live": _bool(args.get("source_live")),
            "use_llm": _bool(args.get("source_use_llm")),
        },
        "deconstruction_policy": {
            "question_count": deconstruction_question_count,
            "overlays_per_primitive": deconstruction_overlays_per_primitive,
            "max_base_primitives": deconstruction_max_base_primitives,
            "use_llm": _bool(args.get("deconstruction_use_llm")),
        },
        "candidate": True,
        "serves_truth": False,
    }
    _write_json(run_dir / "flywheel_policy.json", policy)

    def child(request: dict[str, Any], *, reason: str) -> dict[str, Any]:
        nonlocal child_index
        if len(children) >= max_child_actions:
            row = {
                "record_type": "primitive_loop_flywheel_decision",
                "decision": "skipped_child_action_cap_reached",
                "reason": reason,
                "request": request,
                "child_action_count": len(children),
                "candidate": True,
                "serves_truth": False,
            }
            _append_jsonl(run_dir / "flywheel_decisions.jsonl", row)
            return {"ok": False, "accepted": False, "skipped": True, "reason": "child_action_cap_reached"}
        child_index += 1
        child_request = dict(request)
        child_request.setdefault("request_id", f"flywheel-child-{child_index:03d}-{_slug(str(request.get('action')))}")
        if parent_dry_run:
            child_request["dry_run"] = True
        response = hook.run(child_request)
        child_row = {
            "record_type": "primitive_loop_flywheel_child_action",
            "index": child_index,
            "reason": reason,
            "request": child_request,
            "response_ref": {
                "run_id": response.get("run_id"),
                "run_dir": response.get("run_dir"),
                "ok": response.get("ok"),
                "accepted": response.get("accepted"),
                "action": response.get("action"),
            },
            "candidate": True,
            "serves_truth": False,
        }
        children.append(child_row)
        _append_jsonl(run_dir / "flywheel_decisions.jsonl", child_row)
        return response

    def skipped_child(action: str, *, reason: str, decision: str, details: dict[str, Any]) -> dict[str, Any]:
        nonlocal child_index
        if len(children) >= max_child_actions:
            row = {
                "record_type": "primitive_loop_flywheel_decision",
                "decision": "skipped_child_action_cap_reached",
                "reason": reason,
                "request": {"action": action, "details": details},
                "child_action_count": len(children),
                "candidate": True,
                "serves_truth": False,
            }
            _append_jsonl(run_dir / "flywheel_decisions.jsonl", row)
            return {"ok": False, "accepted": False, "skipped": True, "reason": "child_action_cap_reached"}
        child_index += 1
        child_row = {
            "record_type": "primitive_loop_flywheel_child_action",
            "index": child_index,
            "reason": reason,
            "request": {"action": action, "details": details},
            "response_ref": {
                "action": action,
                "accepted": True,
                "decision": decision,
                "ok": True,
                "skipped": True,
            },
            "candidate": True,
            "serves_truth": False,
        }
        children.append(child_row)
        _append_jsonl(run_dir / "flywheel_decisions.jsonl", child_row)
        return {
            "ok": True,
            "accepted": True,
            "action": action,
            "decision": decision,
            "skipped": True,
            "details": details,
        }

    latest_snapshot: dict[str, Any] = {}
    latest_service_result: dict[str, Any] = {}
    for iteration in range(1, iterations + 1):
        snapshot_response = child(
            {
                "action": "status.snapshot",
                "args": {"include_services": False},
                "request_id": f"flywheel-iteration-{iteration:02d}-status-before",
            },
            reason=f"iteration {iteration}: read current candidate loop state",
        )
        latest_snapshot = snapshot_response.get("result") if isinstance(snapshot_response.get("result"), dict) else {}
        _write_json(run_dir / f"iteration_{iteration:02d}_status_before.json", latest_snapshot)

        if include_services or (run_gemma and avoid_duplicate_gemma):
            services_response = child(
                {
                    "action": "loop.services.status",
                    "request_id": f"flywheel-iteration-{iteration:02d}-services",
                },
                reason=f"iteration {iteration}: supervise known background loop services",
            )
            latest_service_result = (
                services_response.get("result") if isinstance(services_response.get("result"), dict) else {}
            )

        if refresh_plan or not _latest_status(latest_snapshot, "billion_primitive_system"):
            child(
                {
                    "action": "billion_plan.run",
                    "request_id": f"flywheel-iteration-{iteration:02d}-billion-plan",
                },
                reason=f"iteration {iteration}: materialize or refresh scale plan",
            )

        if refresh_plan or not _latest_status(latest_snapshot, "twenty_million_goal"):
            child(
                {
                    "action": "twenty_million_goal.run",
                    "request_id": f"flywheel-iteration-{iteration:02d}-twenty-million-goal",
                    "args": {
                        "target": 20_000_000,
                        "daily_working_target": 100_000,
                        "daily_candidate_target": 400_000,
                        "horizon_days": 60,
                    },
                },
                reason=f"iteration {iteration}: materialize or refresh 20M generator goal plan",
            )

        if run_source_collect:
            source_args: dict[str, Any] = {
                "source_limit": source_limit,
                "question_count": source_question_count,
                "max_components": source_max_components,
                "max_sources_per_partition": _clamp_int(
                    args.get("source_max_sources_per_partition"),
                    default=50,
                    minimum=1,
                    maximum=MAX_SOURCES_PER_PARTITION,
                ),
                "live": _bool(args.get("source_live")),
                "use_llm": _bool(args.get("source_use_llm")),
                "llm_max_tokens": GEMMA_MAX_TOKENS_HARD_CAP,
                "max_llm_context_chars": MAX_LLM_CONTEXT_CHARS,
            }
            if args.get("source_from_jsonl"):
                source_args["from_jsonl"] = args.get("source_from_jsonl")
            child(
                {
                    "action": "source_collect.once",
                    "request_id": f"flywheel-iteration-{iteration:02d}-source-collect",
                    "args": source_args,
                },
                reason=f"iteration {iteration}: mine source surfaces into primitive candidate feed",
            )

        if run_deconstruction:
            deconstruction_args: dict[str, Any] = {
                "question_count": deconstruction_question_count,
                "source_limit": source_limit,
                "max_atlas_rows": _clamp_int(
                    args.get("deconstruction_max_atlas_rows"),
                    default=1_000,
                    minimum=0,
                    maximum=MAX_DECONSTRUCTION_ATLAS_ROWS,
                ),
                "overlays_per_primitive": deconstruction_overlays_per_primitive,
                "max_base_primitives": deconstruction_max_base_primitives,
                "use_llm": _bool(args.get("deconstruction_use_llm")),
                "llm_refine_limit": _clamp_int(
                    args.get("deconstruction_llm_refine_limit"),
                    default=0,
                    minimum=0,
                    maximum=MAX_BASE_PRIMITIVES,
                ),
                "llm_max_tokens": GEMMA_MAX_TOKENS_HARD_CAP,
            }
            if args.get("deconstruction_from_run_dir"):
                deconstruction_args["from_run_dir"] = args.get("deconstruction_from_run_dir")
            child(
                {
                    "action": "deconstruction.once",
                    "request_id": f"flywheel-iteration-{iteration:02d}-deconstruction",
                    "args": deconstruction_args,
                },
                reason=f"iteration {iteration}: materialize fully-defined primitive candidates",
            )
            post_deconstruction_status = child(
                {
                    "action": "status.snapshot",
                    "args": {"include_services": False},
                    "request_id": f"flywheel-iteration-{iteration:02d}-status-after-deconstruction",
                },
                reason=f"iteration {iteration}: refresh status after deconstruction",
            )
            latest_snapshot = (
                post_deconstruction_status.get("result")
                if isinstance(post_deconstruction_status.get("result"), dict)
                else latest_snapshot
            )

        if run_token_benchmark:
            child(
                {
                    "action": "token_savings.run_small",
                    "request_id": f"flywheel-iteration-{iteration:02d}-token-savings",
                    "args": {
                        "n": token_n,
                        "k": token_k,
                        "seed": token_seed + iteration - 1,
                        "corpus": token_corpus,
                        "intent_mode": token_intent_mode,
                        "emit_gaps": _bool(args.get("emit_gaps")),
                    },
                },
                reason=f"iteration {iteration}: measure reuse-vs-rebuild token savings",
            )

        if run_gemma:
            gemma_service_state = _service_state(latest_service_result, "primitive-gemma-long-multistep-loop.service")
            service_blocks_live = avoid_duplicate_gemma and gemma_service_state in {"active", "activating", "unknown", ""}
            live_allowed = execute_live_model and (force_live_gemma or not service_blocks_live)
            source_run_dir = str(args.get("source_run_dir") or _latest_deconstruction_run_dir(latest_snapshot))
            gemma_args: dict[str, Any] = {
                "source_run_dir": source_run_dir,
                "limit": gemma_limit,
                "max_tokens": min(gemma_max_tokens, output_context_tokens),
                "max_token_ceiling": gemma_output_ceiling,
                "token_budget_tier": "exhaustive",
                "timeout": gemma_timeout,
                "sleep_between_calls": GEMMA_SLEEP_BETWEEN_CALLS_MIN,
                "min_hidden_edges": gemma_min_hidden_edges,
                "min_examples": gemma_min_examples,
                "lane_dry_run": not live_allowed,
            }
            if service_blocks_live and not force_live_gemma:
                gemma_response = skipped_child(
                    "gemma_long.once",
                    reason=f"iteration {iteration}: Gemma lane already supervised by background service",
                    decision="skipped_duplicate_gemma_service",
                    details={
                        "gemma_service_state": gemma_service_state,
                        "planned_args": gemma_args,
                    },
                )
            else:
                gemma_response = child(
                    {
                        "action": "gemma_long.once",
                        "request_id": f"flywheel-iteration-{iteration:02d}-gemma-long",
                        "dry_run": False,
                        "args": gemma_args,
                    },
                    reason=(
                        f"iteration {iteration}: "
                        + ("live Gemma generation" if live_allowed else "Gemma lane dry-run because live generation is disabled")
                    ),
                )
            if (
                live_allowed
                and auto_reduce_on_issue
                and not gemma_response.get("ok")
                and gemma_args["max_tokens"] > GEMMA_MAX_TOKENS_FLOOR
            ):
                reduced_tokens = max(GEMMA_MAX_TOKENS_FLOOR, int(gemma_args["max_tokens"] // 2))
                reduced_args = dict(gemma_args)
                reduced_args["max_tokens"] = reduced_tokens
                reduced_args["max_token_ceiling"] = reduced_tokens
                reduced_args["token_budget_tier"] = "frontier" if reduced_tokens >= 49_152 else "advanced"
                child(
                    {
                        "action": "gemma_long.once",
                        "request_id": f"flywheel-iteration-{iteration:02d}-gemma-long-reduced",
                        "dry_run": False,
                        "args": reduced_args,
                    },
                    reason=(
                        f"iteration {iteration}: retry live Gemma after issue with reduced "
                        f"{reduced_tokens} token output budget"
                    ),
                )

    final_snapshot_response = child(
        {
            "action": "status.snapshot",
            "args": {"include_services": False},
            "request_id": "flywheel-final-status",
        },
        reason="final state readback",
    )
    final_snapshot = final_snapshot_response.get("result") if isinstance(final_snapshot_response.get("result"), dict) else {}
    _write_json(run_dir / "final_status_snapshot.json", final_snapshot)

    result = {
        "record_type": "primitive_loop_flywheel_result",
        "created_at": _utc(),
        "policy": policy,
        "child_action_count": len(children),
        "children": [
            {
                "index": child_row["index"],
                "reason": child_row["reason"],
                "action": child_row["request"].get("action"),
                "ok": child_row["response_ref"].get("ok"),
                "run_id": child_row["response_ref"].get("run_id"),
                "run_dir": child_row["response_ref"].get("run_dir"),
            }
            for child_row in children
        ],
        "outputs": {
            "policy": str(run_dir / "flywheel_policy.json"),
            "decisions": str(run_dir / "flywheel_decisions.jsonl"),
            "final_status_snapshot": str(run_dir / "final_status_snapshot.json"),
        },
        "candidate": True,
        "serves_truth": False,
    }
    _write_json(run_dir / "flywheel_result.json", result)
    return result


def load_request(args: argparse.Namespace) -> dict[str, Any]:
    sources = [bool(args.request_json), bool(args.request_file)]
    if sum(sources) > 1:
        raise ValueError("pass only one of --request-json or --request-file")
    if args.request_json:
        value = json.loads(args.request_json)
    elif args.request_file:
        value = json.loads(Path(args.request_file).read_text(encoding="utf-8"))
    else:
        value = json.loads(sys.stdin.read())
    if not isinstance(value, dict):
        raise ValueError("request must decode to a JSON object")
    return value


def _self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="primitive-loop-json-hook-") as temp:
        hook = PrimitiveLoopHook(out_root=Path(temp) / "hook")
        listed = hook.run({"action": "actions.list", "request_id": "test-list"})
        assert listed["ok"] is True
        assert "gemma_long.once" in listed["result"]["actions"]
        dry = hook.run(
            {
                "action": "gemma_long.once",
                "request_id": "test-gemma-dry",
                "dry_run": True,
                "args": {
                    "limit": 99,
                    "max_tokens": 99_999,
                    "sleep_between_calls": 1,
                    "timeout": 999,
                    "min_hidden_edges": 99,
                    "min_examples": 99,
                    "lane_dry_run": True,
                },
            }
        )
        assert dry["ok"] is True and dry["executed"] is False
        argv = dry["plan"]["argv"]
        assert "--limit" in argv and argv[argv.index("--limit") + 1] == str(GEMMA_LIMIT_MAX)
        assert "--max-tokens" in argv and argv[argv.index("--max-tokens") + 1] == str(GEMMA_MAX_TOKENS_HARD_CAP)
        assert "--sleep-between-calls" in argv and argv[argv.index("--sleep-between-calls") + 1] == "55.0"
        assert "--dry-run" in argv
        status = hook.run({"action": "status.snapshot"})
        assert status["ok"] is True
        flywheel = hook.run(
            {
                "action": "flywheel.run",
                "dry_run": True,
                "args": {
                    "iterations": 2,
                    "mode": "balanced",
                    "max_child_actions": 8,
                    "execute_live_model": True,
                    "gemma_max_tokens": 99_999,
                    "output_context_tokens": 99_999,
                },
            }
        )
        assert flywheel["ok"] is True
        assert flywheel["result"]["policy"]["context_budget"]["output_context_tokens"] == GEMMA_MAX_TOKENS_HARD_CAP
        assert flywheel["result"]["child_action_count"] <= 8
        token = hook.run({"action": "token_savings.run_small", "dry_run": True, "args": {"n": 10, "intent_mode": "bad"}})
        assert token["plan"]["sanitized_args"]["intent_mode"] == "paraphrase"
        session_bench = hook.run(
            {
                "action": "session_benchmarks.run",
                "dry_run": True,
                "args": {
                    "sessions": 999,
                    "turns_per_session": 999,
                    "k": 99,
                    "components_per_turn": 99,
                    "scenario_mode": "bad",
                    "context_window": 999_999_999,
                },
            }
        )
        assert session_bench["ok"] is True and session_bench["executed"] is False
        assert session_bench["plan"]["sanitized_args"]["sessions"] == 500
        assert session_bench["plan"]["sanitized_args"]["turns_per_session"] == 20
        assert session_bench["plan"]["sanitized_args"]["scenario_mode"] == "mixed"
        assert session_bench["plan"]["sanitized_args"]["context_window"] == MAX_INPUT_CONTEXT_TOKENS
        bad = hook.run({"action": "gemma_long.once", "dry_run": True, "args": {"source_run_dir": "../outside"}})
        assert bad["ok"] is False and bad["accepted"] is False
        unknown = hook.run({"action": "does.not.exist"})
        assert unknown["ok"] is False and unknown["accepted"] is False
        ledger = hook.out_root / "hook_ledger.jsonl"
        rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert rows and all(row["candidate"] is True and row["serves_truth"] is False for row in rows)
    print("PASS - primitive_loop_json_hook allowlists actions, clamps args, rejects path escape, and writes receipts.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-json", help="JSON object request")
    parser.add_argument("--request-file", help="path to a JSON request file")
    parser.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT), help="hook receipt root")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    try:
        request = load_request(args)
        hook = PrimitiveLoopHook(out_root=_repo_path(args.out_root, field="--out-root") if args.out_root else DEFAULT_OUT_ROOT)
        response = hook.run(request)
    except Exception as exc:  # noqa: BLE001
        response = {
            "record_type": RECORD_TYPE,
            "created_at": _utc(),
            "ok": False,
            "accepted": False,
            "error": str(exc),
            "error_type": type(exc).__name__,
            "candidate": True,
            "serves_truth": False,
        }
    print(json.dumps(response, indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if response.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
