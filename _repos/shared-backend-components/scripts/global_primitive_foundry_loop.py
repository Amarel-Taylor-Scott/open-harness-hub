#!/usr/bin/env python3
"""Global primitive foundry loop.

Runs the shared source-to-primitive candidate pipeline across public metadata
sources, model-assisted review lanes, and deterministic lifecycle packaging.

This is intentionally global, not AIDevObserver-specific. AIDevObserver is one
source and consumer of signals; OpenHubForAI/Teleon own the shared primitive
lifecycle.

Every generated row remains candidate evidence with ``serves_truth=false``.
Proof and promotion are separate gates.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from scripts._config import (  # noqa: E402
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH,
    LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS,
    OPENWEBUI_DEFAULT_MODEL,
    PRIMITIVE_FACTORY_DEFAULT_SHARD_USEFUL_TARGET,
    PRIMITIVE_FACTORY_FAST_SHARD_USEFUL_TARGET,
)

DEFAULT_INTERVAL_SECONDS = 60 * 60
DEFAULT_DAEMON_LOG = _resource("data") / "dev-intel" / "global_primitive_foundry" / "daemon.log"
DEFAULT_DAEMON_PID = _resource("data") / "dev-intel" / "global_primitive_foundry" / "daemon.pid"
AIDEVEXPLORER_TASK_CORPUS = _resource(AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH)
ROUTE_FIXTURE_VERIFICATION_REPORT = _resource("data") / "dev-intel" / "primitive_route_fixtures" / "verification_report.json"
RUNTIME_ADAPTER_COVERAGE_REPORT = _resource("data") / "dev-intel" / "runtime_adapter_coverage" / "runtime_adapter_coverage_report.json"


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_dotenv(env: dict[str, str]) -> dict[str, str]:
    path = REPO / ".env"
    initial_keys = set(env)
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and not env.get(key):
            env[key] = value
    if "OLLAMA_API_KEY" in initial_keys and "OH_LLM_API_KEY" not in initial_keys and env.get("OLLAMA_API_KEY"):
        env["OH_LLM_API_KEY"] = env["OLLAMA_API_KEY"]
    elif env.get("OLLAMA_API_KEY") and not env.get("OH_LLM_API_KEY"):
        env["OH_LLM_API_KEY"] = env["OLLAMA_API_KEY"]
    if env.get("OH_LLM_API_KEY") and not env.get("OLLAMA_API_KEY"):
        env["OLLAMA_API_KEY"] = env["OH_LLM_API_KEY"]
    env.setdefault("OH_LLM_BASE_URL", "https://ollama.com/v1")
    env.setdefault("OH_CHAT_MODEL", "glm-5.2")
    env.setdefault("OH_PRIMITIVE_RESEARCH_MODEL", "glm-5.2")
    env.setdefault("OH_PRIMITIVE_CODE_MODEL", "kimi-k2.7-code")
    return env


def _git_credential_token() -> str:
    """Return a GitHub token from ~/.git-credentials when available.

    Never logs or writes the value. The token may be in the username or
    password slot depending on how credential.helper stored it.
    """
    path = Path.home() / ".git-credentials"
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "github.com" not in line:
            continue
        parsed = urllib.parse.urlparse(line)
        token = urllib.parse.unquote(parsed.password or parsed.username or "")
        if token:
            return token
    return ""


def _run(label: str, cmd: list[str], *, env: dict[str, str]) -> dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        cmd,
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "label": label,
        "cmd": cmd[:2] + ["..."] if len(cmd) > 2 else cmd,
        "returncode": proc.returncode,
        "duration_seconds": round(time.time() - started, 3),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "serves_truth": False,
    }


def _skip(label: str, reason: str) -> dict[str, Any]:
    return {
        "label": label,
        "reason": reason,
        "returncode": None,
        "serves_truth": False,
        "skipped": True,
    }


def _enabled_this_tick(every: int, *, tick_index: int) -> bool:
    if every <= 0:
        return False
    return (tick_index - 1) % every == 0


def _apply_fast_candidate_mode(args: argparse.Namespace) -> None:
    if not args.fast_candidate_mode:
        return
    args.build_5k_shards = True
    args.build_aidevexplorer_task_corpus = True
    args.use_aidevexplorer_task_corpus = True
    args.skip_lifecycle = True
    args.skip_route_fixtures = True
    args.skip_route_verifier = True
    args.skip_runtime_coverage = True
    if args.shard_useful_target == PRIMITIVE_FACTORY_DEFAULT_SHARD_USEFUL_TARGET:
        args.shard_useful_target = PRIMITIVE_FACTORY_FAST_SHARD_USEFUL_TARGET


def _tick(args: argparse.Namespace, *, tick_index: int) -> dict[str, Any]:
    env = _load_dotenv(dict(os.environ))
    if args.live_public:
        token = env.get("GITHUB_TOKEN") or env.get("GH_TOKEN") or _git_credential_token()
        if token:
            env["GITHUB_TOKEN"] = token

    steps: list[dict[str, Any]] = []
    skipped_steps: list[dict[str, Any]] = []

    if args.scan_pypi:
        steps.append(
            _run(
                "pypi_metadata_scan",
                ["python3", str(_resource("scripts/aidevobserver_pypi_source_scan.py")), "--seed-common-python", "--write"],
                env=env,
            )
        )

    if args.build_5k_shards:
        steps.append(
            _run(
                "primitive_factory_5k_lane_check",
                ["python3", str(_resource("scripts/check_primitive_factory_5k_lanes.py"))],
                env=env,
            )
        )
        steps.append(
            _run(
                "primitive_factory_5k_shard_plan",
                [
                    "python3",
                    str(_resource("scripts/build_primitive_factory_5k_shards.py")),
                    "--shard-useful-target",
                    str(args.shard_useful_target),
                ],
                env=env,
            )
        )
        steps.append(
            _run(
                "primitive_factory_5k_shard_check",
                ["python3", str(_resource("scripts/check_primitive_factory_5k_shards.py"))],
                env=env,
            )
        )

    if args.run_gemma_shard_worker:
        gemma_cmd = [
            "python3",
            str(_resource("scripts/run_primitive_factory_model_worker.py")),
            "--provider",
            "openwebui",
            "--model",
            args.gemma_model,
            "--workers",
            str(args.gemma_workers),
            "--mode",
            args.gemma_mode,
            "--limit",
            str(args.gemma_shard_limit),
            "--max-tokens",
            str(args.gemma_max_tokens),
            "--timeout",
            str(args.gemma_timeout),
        ]
        if args.gemma_cdp_url:
            gemma_cmd += ["--cdp-url", args.gemma_cdp_url]
        if args.gemma_worker_dry_run:
            gemma_cmd.append("--dry-run")
        steps.append(_run("openwebui_gemma_shard_worker", gemma_cmd, env=env))

    if args.build_aidevexplorer_task_corpus:
        steps.append(
            _run(
                "aidevexplorer_task_corpus_generate",
                ["python3", str(_resource("scripts/generate_aidevexplorer_real_world_task_corpus.py"))],
                env=env,
            )
        )
        steps.append(
            _run(
                "aidevexplorer_task_corpus_check",
                ["python3", str(_resource("scripts/check_aidevexplorer_real_world_task_corpus.py"))],
                env=env,
            )
        )
        steps.append(
            _run(
                "aidevexplorer_task_benchmark_suites_build",
                ["python3", str(_resource("scripts/build_aidevexplorer_task_benchmark_suites.py"))],
                env=env,
            )
        )
        steps.append(
            _run(
                "aidevexplorer_task_benchmark_suites_check",
                ["python3", str(_resource("scripts/check_aidevexplorer_task_benchmark_suites.py"))],
                env=env,
            )
        )

    public_use_case_seeds = AIDEVEXPLORER_TASK_CORPUS if args.use_aidevexplorer_task_corpus else None
    foundry_cmd = [
        "python3",
        str(_resource("scripts/aidevobserver_context_foundry_loop.py")),
        "--once",
    ]
    if public_use_case_seeds is not None:
        foundry_cmd += ["--public-use-case-seeds", str(public_use_case_seeds)]
    foundry_cmd += [
        "--surface-limit",
        str(args.surface_limit),
        "--use-case-limit",
        str(args.use_case_limit),
        "--microsurface-limit",
        str(args.microsurface_limit),
        "--local-repo-limit",
        str(args.local_repo_limit),
        "--search-scope-limit",
        str(args.search_scope_limit),
        "--naics-scope-limit",
        str(args.naics_scope_limit),
        "--business-operation-scope-limit",
        str(args.business_operation_scope_limit),
    ]
    if args.skip_multilingual_search_scopes:
        foundry_cmd.append("--skip-multilingual-search-scopes")
    if args.live_public:
        foundry_cmd += [
            "--live-github",
            "--github-query-limit",
            str(args.github_query_limit),
            "--github-result-limit",
            str(args.github_result_limit),
            "--live-kaggle",
            "--kaggle-topic-limit",
            str(args.kaggle_topic_limit),
            "--kaggle-result-limit",
            str(args.kaggle_result_limit),
            "--live-rss-feeds",
            "--rss-feed-limit",
            str(args.rss_feed_limit),
            "--rss-item-limit",
            str(args.rss_item_limit),
            "--live-markdown-indexes",
            "--markdown-index-limit",
            str(args.markdown_index_limit),
            "--markdown-link-limit",
            str(args.markdown_link_limit),
        ]
    steps.append(_run("source_context_foundry", foundry_cmd, env=env))

    if args.live_model:
        steps.append(
            _run(
                "kaggle_kernel_distillation",
                ["python3", str(_resource("scripts/distill_kaggle_kernels.py")), "--live", "--llm-limit", str(args.kaggle_distill_limit)],
                env=env,
            )
        )
        sweep_cmd = [
            "python3",
            str(_resource("scripts/multi_model_improvement_loop.py")),
            "--kinds",
            args.model_sweep_kinds,
            "--target-workers",
            str(args.model_target_workers),
        ]
        if args.model_sweep_limit > 0:
            sweep_cmd += ["--run", "--limit", str(args.model_sweep_limit)]
        else:
            sweep_cmd += ["--all"]
        steps.append(
            _run(
                "glm_kimi_improvement_sweep",
                sweep_cmd,
                env=env,
            )
        )

    if args.skip_lifecycle:
        skipped_steps.append(_skip("primitive_lifecycle_package", "skip_lifecycle"))
    elif not _enabled_this_tick(args.lifecycle_every, tick_index=tick_index):
        skipped_steps.append(_skip("primitive_lifecycle_package", f"lifecycle_every={args.lifecycle_every}"))
    else:
        steps.append(
            _run(
                "primitive_lifecycle_package",
                ["python3", str(_resource("scripts/primitive_source_lifecycle.py")), "--limit", str(args.lifecycle_limit)],
                env=env,
            )
        )

    if args.skip_route_fixtures:
        skipped_steps.append(_skip("primitive_route_fixture_foundry", "skip_route_fixtures"))
    elif not _enabled_this_tick(args.route_fixture_every, tick_index=tick_index):
        skipped_steps.append(_skip("primitive_route_fixture_foundry", f"route_fixture_every={args.route_fixture_every}"))
    else:
        steps.append(
            _run(
                "primitive_route_fixture_foundry",
                [
                    "python3",
                    str(_resource("scripts/primitive_route_fixture_foundry.py")),
                    "--direct-limit",
                    str(args.route_fixture_direct_limit),
                    "--mutator-limit",
                    str(args.route_fixture_mutator_limit),
                    "--chain-limit",
                    str(args.route_fixture_chain_limit),
                ],
                env=env,
            )
        )

    if args.skip_route_verifier:
        skipped_steps.append(_skip("primitive_route_fixture_verifier", "skip_route_verifier"))
    elif not _enabled_this_tick(args.route_verifier_every, tick_index=tick_index):
        skipped_steps.append(_skip("primitive_route_fixture_verifier", f"route_verifier_every={args.route_verifier_every}"))
    else:
        steps.append(
            _run(
                "primitive_route_fixture_verifier",
                [
                    "python3",
                    str(_resource("scripts/primitive_route_fixture_verifier.py")),
                    "--search-sample-per-kind",
                    str(args.route_fixture_verify_search_sample_per_kind),
                    "--min-search-hit-rate",
                    str(args.route_fixture_verify_min_search_hit_rate),
                ],
                env=env,
            )
        )

    if args.skip_runtime_coverage:
        skipped_steps.append(_skip("runtime_adapter_coverage", "skip_runtime_coverage"))
    elif not _enabled_this_tick(args.runtime_coverage_every, tick_index=tick_index):
        skipped_steps.append(_skip("runtime_adapter_coverage", f"runtime_coverage_every={args.runtime_coverage_every}"))
    else:
        steps.append(
            _run(
                "runtime_adapter_coverage",
                [
                    "python3",
                    str(_resource("scripts/runtime_adapter_coverage_report.py")),
                    "--low-coverage-count",
                    str(args.runtime_adapter_low_coverage_count),
                    "--fixtures-per-target",
                    str(args.runtime_adapter_fixtures_per_target),
                ],
                env=env,
            )
        )

    manifest_path = _resource("data") / "dev-intel" / "primitive_source_lifecycle" / "manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
    route_fixture_path = _resource("data") / "dev-intel" / "primitive_route_fixtures" / "manifest.json"
    route_manifest: dict[str, Any] = {}
    if route_fixture_path.exists():
        try:
            route_manifest = json.loads(route_fixture_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            route_manifest = {}
    route_verification: dict[str, Any] = {}
    if ROUTE_FIXTURE_VERIFICATION_REPORT.exists():
        try:
            route_verification = json.loads(ROUTE_FIXTURE_VERIFICATION_REPORT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            route_verification = {}
    runtime_coverage: dict[str, Any] = {}
    if RUNTIME_ADAPTER_COVERAGE_REPORT.exists():
        try:
            runtime_coverage = json.loads(RUNTIME_ADAPTER_COVERAGE_REPORT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            runtime_coverage = {}

    return {
        "record_type": "global_primitive_foundry_tick",
        "tick_index": tick_index,
        "created_at": _utc(),
        "live_public": bool(args.live_public),
        "live_model": bool(args.live_model),
        "candidate": True,
        "serves_truth": False,
        "steps": steps,
        "skipped_steps": skipped_steps,
        "fast_candidate_mode": bool(args.fast_candidate_mode),
        "shard_useful_target": args.shard_useful_target,
        "lifecycle_manifest": {
            "source_candidates": manifest.get("source_candidates"),
            "primitive_rows_available": manifest.get("primitive_rows_available"),
            "primitive_rows_selected": manifest.get("primitive_rows_selected"),
            "implementation_backlog_rows": manifest.get("implementation_backlog_rows"),
            "search_cards": manifest.get("search_cards"),
            "vector_rows": manifest.get("vector_rows"),
            "serves_truth": manifest.get("serves_truth", False),
        },
        "route_fixture_manifest": {
            "route_fixtures": route_manifest.get("route_fixtures"),
            "candidate_bundles": route_manifest.get("candidate_bundles"),
            "fixture_kind_counts": route_manifest.get("fixture_kind_counts"),
            "serves_truth": route_manifest.get("serves_truth", False),
        },
        "route_fixture_verification": {
            "ok": route_verification.get("ok"),
            "fixtures_checked": route_verification.get("fixtures_checked"),
            "structural_error_count": route_verification.get("structural_error_count"),
            "search_checked": route_verification.get("search_checked"),
            "search_hits": route_verification.get("search_hits"),
            "search_hit_rate": route_verification.get("search_hit_rate"),
            "serves_truth": route_verification.get("serves_truth", False),
        },
        "runtime_adapter_coverage": {
            "ok": runtime_coverage.get("ok"),
            "edge_cards_read": runtime_coverage.get("edge_cards_read"),
            "fixture_count": runtime_coverage.get("fixture_count"),
            "blocking_gap_count": runtime_coverage.get("blocking_gap_count"),
            "low_coverage_gap_count": runtime_coverage.get("low_coverage_gap_count"),
            "runtime_target_counts": runtime_coverage.get("runtime_target_counts"),
            "runtime_mutator_counts": runtime_coverage.get("runtime_mutator_counts"),
            "serves_truth": runtime_coverage.get("serves_truth", False),
        },
    }


def _write_ledger(row: dict[str, Any]) -> None:
    path = _resource("data") / "dev-intel" / "global_primitive_foundry" / "loop_ledger.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    env = _load_dotenv({})
    check("dotenv defaults set GLM research model", env["OH_PRIMITIVE_RESEARCH_MODEL"] == "glm-5.2")
    check("dotenv defaults set Kimi code model", env["OH_PRIMITIVE_CODE_MODEL"] == "kimi-k2.7-code")
    check("Ollama key aliases synchronize when present",
          _load_dotenv({"OLLAMA_API_KEY": "x"}).get("OH_LLM_API_KEY") == "x")
    p = argparse.Namespace(
        live_public=False,
        live_model=False,
        scan_pypi=False,
        surface_limit=1,
        use_case_limit=1,
        microsurface_limit=1,
        local_repo_limit=1,
        search_scope_limit=1,
        naics_scope_limit=1,
        business_operation_scope_limit=1,
        skip_multilingual_search_scopes=False,
        github_query_limit=1,
        github_result_limit=1,
        kaggle_topic_limit=1,
        kaggle_result_limit=1,
        rss_feed_limit=1,
        rss_item_limit=1,
        markdown_index_limit=1,
        markdown_link_limit=1,
        kaggle_distill_limit=1,
        model_sweep_limit=1,
        model_sweep_kinds="research",
        model_target_workers=1,
        lifecycle_limit=5,
        route_fixture_direct_limit=5,
        route_fixture_mutator_limit=5,
        route_fixture_chain_limit=5,
        route_fixture_verify_search_sample_per_kind=1,
        route_fixture_verify_min_search_hit_rate=0.5,
        runtime_adapter_low_coverage_count=25,
        runtime_adapter_fixtures_per_target=12,
        build_5k_shards=False,
        shard_useful_target=PRIMITIVE_FACTORY_DEFAULT_SHARD_USEFUL_TARGET,
        build_aidevexplorer_task_corpus=False,
        use_aidevexplorer_task_corpus=False,
        run_gemma_shard_worker=False,
        gemma_model=OPENWEBUI_DEFAULT_MODEL,
        gemma_workers=2,
        gemma_mode="direct",
        gemma_cdp_url="",
        gemma_shard_limit=1,
        gemma_max_tokens=LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS,
        gemma_timeout=30,
        gemma_worker_dry_run=True,
        fast_candidate_mode=False,
        skip_lifecycle=False,
        skip_route_fixtures=False,
        skip_route_verifier=False,
        skip_runtime_coverage=False,
        lifecycle_every=1,
        route_fixture_every=1,
        route_verifier_every=1,
        runtime_coverage_every=1,
    )
    _apply_fast_candidate_mode(p)
    check("tick args carry candidate-only defaults", p.live_model is False and p.live_public is False)
    check("route fixture verifier defaults sample retrieval", p.route_fixture_verify_search_sample_per_kind == 1)
    p.fast_candidate_mode = True
    _apply_fast_candidate_mode(p)
    check("fast candidate mode turns on shard and corpus generation", p.build_5k_shards and p.use_aidevexplorer_task_corpus)
    check("fast candidate mode skips heavyweight refresh", p.skip_lifecycle and p.skip_route_verifier and p.skip_runtime_coverage)
    check("fast candidate mode uses smaller shards", p.shard_useful_target == PRIMITIVE_FACTORY_FAST_SHARD_USEFUL_TARGET)
    p.run_gemma_shard_worker = True
    check("Gemma shard worker is explicit opt-in", p.run_gemma_shard_worker and p.gemma_model == OPENWEBUI_DEFAULT_MODEL)
    print(
        "\n"
        + (
            "PASS - global primitive foundry loop: env lanes, candidate-only defaults, and batch orchestration are configured."
            if not failures
            else f"{len(failures)} FAILURES: {failures}"
        )
    )
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the global primitive source-to-lifecycle foundry loop.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--daemon", action="store_true", help="start the loop detached and return the child pid")
    parser.add_argument("--daemon-log", default=str(DEFAULT_DAEMON_LOG))
    parser.add_argument("--daemon-pid", default=str(DEFAULT_DAEMON_PID))
    parser.add_argument("--watch", action="store_true", help="run repeatedly")
    parser.add_argument("--max-ticks", type=int, default=1, help="0 means forever in --watch mode")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS)
    parser.add_argument("--live-public", action="store_true", help="enable live GitHub/Kaggle metadata discovery")
    parser.add_argument("--live-model", action="store_true", help="enable GLM/Kimi model-assisted candidate passes")
    parser.add_argument("--fast-candidate-mode", action="store_true", help="favor high-volume candidate generation over heavyweight packaging/verification refresh")
    parser.add_argument("--build-5k-shards", action="store_true", help="build 5k/day primitive factory work shards this tick")
    parser.add_argument("--shard-useful-target", type=int, default=PRIMITIVE_FACTORY_DEFAULT_SHARD_USEFUL_TARGET, help="use smaller values to create more parallel primitive-generation shards")
    parser.add_argument("--run-gemma-shard-worker", action="store_true", help="run Open WebUI Gemma over primitive factory shards")
    parser.add_argument("--gemma-model", default=OPENWEBUI_DEFAULT_MODEL)
    parser.add_argument("--gemma-workers", type=int, default=8)
    parser.add_argument("--gemma-mode", choices=["direct", "cdp"], default="direct")
    parser.add_argument("--gemma-cdp-url", default="")
    parser.add_argument("--gemma-shard-limit", type=int, default=25, help="0 means all available shards")
    parser.add_argument("--gemma-max-tokens", type=int, default=LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS)
    parser.add_argument("--gemma-timeout", type=int, default=120)
    parser.add_argument("--gemma-worker-dry-run", action="store_true", help="plan Gemma shard work without live model calls")
    parser.add_argument("--build-aidevexplorer-task-corpus", action="store_true", help="generate/check the 10k AIDevExplorer task corpus and benchmark suites")
    parser.add_argument("--use-aidevexplorer-task-corpus", action="store_true", help="use the 10k AIDevExplorer task corpus as public use-case seeds")
    parser.add_argument("--scan-pypi", action="store_true", help="scan common PyPI metadata each tick")
    parser.add_argument("--surface-limit", type=int, default=0, help="0 means all configured source surfaces")
    parser.add_argument("--use-case-limit", type=int, default=0, help="0 means all public use-case seeds")
    parser.add_argument("--microsurface-limit", type=int, default=0, help="0 means all microsurface seeds")
    parser.add_argument("--local-repo-limit", type=int, default=0, help="0 means all eligible local primitive candidates")
    parser.add_argument("--search-scope-limit", type=int, default=0, help="0 means all multilingual search-scope seeds")
    parser.add_argument("--naics-scope-limit", type=int, default=0, help="0 means all generated NAICS search-scope seeds")
    parser.add_argument("--business-operation-scope-limit", type=int, default=0, help="0 means all generated first-principles business-operation scopes")
    parser.add_argument("--skip-multilingual-search-scopes", action="store_true")
    parser.add_argument("--github-query-limit", type=int, default=100)
    parser.add_argument("--github-result-limit", type=int, default=100)
    parser.add_argument("--kaggle-topic-limit", type=int, default=100)
    parser.add_argument("--kaggle-result-limit", type=int, default=100)
    parser.add_argument("--rss-feed-limit", type=int, default=100)
    parser.add_argument("--rss-item-limit", type=int, default=25)
    parser.add_argument("--markdown-index-limit", type=int, default=25)
    parser.add_argument("--markdown-link-limit", type=int, default=100)
    parser.add_argument("--kaggle-distill-limit", type=int, default=0, help="0 means all mined kernels")
    parser.add_argument("--model-sweep-limit", type=int, default=0, help="0 means all remaining targets once")
    parser.add_argument("--model-sweep-kinds", default="research,module,architecture")
    parser.add_argument("--model-target-workers", type=int, default=2, help="parallel Kimi/GLM target reviews during live model sweep")
    parser.add_argument("--lifecycle-limit", type=int, default=0, help="0 means all lifecycle rows")
    parser.add_argument("--skip-lifecycle", action="store_true", help="skip primitive lifecycle packaging this tick")
    parser.add_argument("--lifecycle-every", type=int, default=1, help="run lifecycle packaging every N ticks; 0 disables it")
    parser.add_argument("--route-fixture-direct-limit", type=int, default=160)
    parser.add_argument("--route-fixture-mutator-limit", type=int, default=160)
    parser.add_argument("--route-fixture-chain-limit", type=int, default=120)
    parser.add_argument("--skip-route-fixtures", action="store_true", help="skip route fixture generation this tick")
    parser.add_argument("--route-fixture-every", type=int, default=1, help="run route fixture generation every N ticks; 0 disables it")
    parser.add_argument("--skip-route-verifier", action="store_true", help="skip route fixture verification this tick")
    parser.add_argument("--route-verifier-every", type=int, default=1, help="run route fixture verification every N ticks; 0 disables it")
    parser.add_argument("--route-fixture-verify-search-sample-per-kind", type=int, default=1)
    parser.add_argument("--route-fixture-verify-min-search-hit-rate", type=float, default=0.5)
    parser.add_argument("--runtime-adapter-low-coverage-count", type=int, default=25)
    parser.add_argument("--runtime-adapter-fixtures-per-target", type=int, default=12)
    parser.add_argument("--skip-runtime-coverage", action="store_true", help="skip runtime adapter coverage refresh this tick")
    parser.add_argument("--runtime-coverage-every", type=int, default=1, help="run runtime adapter coverage every N ticks; 0 disables it")
    args = parser.parse_args(argv)
    _apply_fast_candidate_mode(args)

    if args.self_test:
        return _self_test()

    if args.daemon:
        daemon_args = [arg for arg in (argv if argv is not None else sys.argv[1:]) if arg != "--daemon"]
        log_path = Path(args.daemon_log)
        pid_path = Path(args.daemon_pid)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        out = log_path.open("ab")
        proc = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), *daemon_args],
            cwd=REPO,
            stdout=out,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        pid_path.write_text(str(proc.pid) + "\n", encoding="utf-8")
        print(json.dumps({
            "record_type": "global_primitive_foundry_daemon_started",
            "pid": proc.pid,
            "log": str(log_path),
            "pid_file": str(pid_path),
            "serves_truth": False,
        }, sort_keys=True))
        return 0

    tick = 0
    while True:
        tick += 1
        row = _tick(args, tick_index=tick)
        _write_ledger(row)
        print(json.dumps(row, indent=2, sort_keys=True))
        failed = [step for step in row["steps"] if step.get("returncode") != 0]
        if failed:
            print(f"global primitive foundry tick completed with {len(failed)} failed step(s)", file=sys.stderr)
        if not args.watch:
            return 0 if not failed else 1
        if args.max_ticks and tick >= args.max_ticks:
            return 0 if not failed else 1
        time.sleep(max(1, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
