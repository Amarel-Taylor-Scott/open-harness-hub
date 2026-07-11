#!/usr/bin/env python3
"""Persistent AIDevObserver primitive-foundry supervisor.

This is the durable loop runner for the `/goal` workflow. One tick performs
the boring-but-load-bearing work:

1. regenerate source-backed primitive edge cards;
2. refresh context/source/use-case candidate queues;
3. run proof checks;
4. smoke-test registry retrieval across broad developer tasks;
5. append machine-readable and human-readable receipts.

It never promotes a primitive and never turns generated records into served
truth. Every generated row remains candidate-only until an external
proof/promotion path upgrades it.
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# Resolve the SUBSTRATE root (the dir that holds the `scripts` package) via the scripts/_repo_paths.py sentinel —
# NOT `.aidoneright-root`, which sits at the MONOREPO root (no `scripts/` package) and breaks `from scripts.*`/
# `from src.*` on a bare `python3 _repos/shared-backend-components/scripts/<f>.py` launch. install() then
# prepends every code root (repo root + each _repos/*/backend + shared-backend-components) so both resolve.
import sys
from pathlib import Path
_sbc = next((_p for _p in Path(__file__).resolve().parents if (_p / "scripts" / "_repo_paths.py").exists()), Path(__file__).resolve().parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install  # noqa: E402
_install()
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts._config import (  # noqa: E402
    AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY,
    AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC,
)

OUT_DIR = _resource("data") / "dev-intel" / "aidevobserver_primitive_foundry_daemon"
LEDGER = OUT_DIR / "loop_ledger.jsonl"
LATEST = OUT_DIR / "latest_status.json"
HUMAN_LOG = _resource(".agent") / "aidevobserver" / "primitive-foundry-loop-log.md"
EDGE_MANIFEST = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "manifest.json"
CONTEXT_LEDGER = _resource("data") / "dev-intel" / "aidevobserver_context_foundry" / "loop_ledger.jsonl"
LIFECYCLE_MANIFEST = _resource("data") / "dev-intel" / "primitive_source_lifecycle" / "manifest.json"
ROUTE_FIXTURE_MANIFEST = _resource("data") / "dev-intel" / "primitive_route_fixtures" / "manifest.json"
ROUTE_FIXTURE_VERIFICATION_REPORT = _resource("data") / "dev-intel" / "primitive_route_fixtures" / "verification_report.json"
RUNTIME_ADAPTER_COVERAGE_REPORT = _resource("data") / "dev-intel" / "runtime_adapter_coverage" / "runtime_adapter_coverage_report.json"

DEFAULT_EDGE_ROOTS = ("." ,)
DEFAULT_SEARCH_QUERIES = (
    "build api endpoint validate json request persist response",
    "react form validation component submit api",
    "train regression model feature evaluation",
    "kubernetes deployment cloud function runtime",
    "workflow replay ledger debugger",
    "ci workflow test build cache publish",
    "json schema validate input output contract",
    "mcp server tool manifest",
    "notebook train model pandas",
    "browser scrape table csv parquet playwright",
    "openapi operation validate request response",
    "workflow json n8n node",
    "cloud function http handler wrapper",
    "idempotency key persist write receipt",
    "secret ref redaction wrapper",
    "kubernetes job wrapper manifest runtime",
    "pytest vitest test proof receipt",
    "auth login session template primitive route",
    "kaggle tabular baseline schema model submission",
)


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_stable_json(row) + "\n")


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _last_jsonl(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return {}
    if not lines:
        return {}
    try:
        value = json.loads(lines[-1])
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _run(cmd: list[str], *, timeout: int) -> dict[str, Any]:
    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        status = "ok" if proc.returncode == 0 else "failed"
        return {
            "cmd": cmd,
            "status": status,
            "returncode": proc.returncode,
            "seconds": round(time.time() - started, 3),
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "status": "timeout",
            "returncode": None,
            "seconds": round(time.time() - started, 3),
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
        }


def _edge_command(args: argparse.Namespace) -> list[str]:
    cmd = [
        sys.executable,
        str(_resource("scripts/aidevobserver_edge_foundry.py")),
        "--max-files",
        str(args.edge_max_files),
        "--max-records",
        str(args.edge_max_records),
        "--max-structured-rows-per-file",
        str(args.max_structured_rows_per_file),
    ]
    for root in args.edge_root:
        cmd.extend(["--root", root])
    for excluded in args.exclude:
        cmd.extend(["--exclude", excluded])
    if args.no_js:
        cmd.append("--no-js")
    if args.no_structured:
        cmd.append("--no-structured")
    return cmd


def _context_command(args: argparse.Namespace) -> list[str]:
    cmd = [
        sys.executable,
        str(_resource("scripts/aidevobserver_context_foundry_loop.py")),
        "--once",
        "--local-repo-root",
        args.context_local_repo_root,
        "--local-repo-limit",
        str(args.context_local_repo_limit),
        "--surface-limit",
        str(args.surface_limit),
        "--use-case-limit",
        str(args.use_case_limit),
        "--microsurface-limit",
        str(args.microsurface_limit),
        "--search-scope-limit",
        str(args.search_scope_limit),
        "--naics-scope-limit",
        str(args.naics_scope_limit),
        "--business-operation-scope-limit",
        str(args.business_operation_scope_limit),
    ]
    if args.skip_multilingual_search_scopes:
        cmd.append("--skip-multilingual-search-scopes")
    if args.include_local_claude:
        cmd.append("--include-local-claude")
    if args.derive_local_reviews:
        cmd.append("--derive-local-reviews")
    if args.live_github:
        cmd.extend([
            "--live-github",
            "--github-query-limit",
            str(args.github_query_limit),
            "--github-result-limit",
            str(args.github_result_limit),
        ])
    if args.live_kaggle:
        cmd.extend([
            "--live-kaggle",
            "--kaggle-topic-limit",
            str(args.kaggle_topic_limit),
            "--kaggle-result-limit",
            str(args.kaggle_result_limit),
        ])
    if args.live_rss_feeds:
        cmd.extend([
            "--live-rss-feeds",
            "--rss-feed-limit",
            str(args.rss_feed_limit),
            "--rss-item-limit",
            str(args.rss_item_limit),
        ])
    if args.live_markdown_indexes:
        cmd.extend([
            "--live-markdown-indexes",
            "--markdown-index-limit",
            str(args.markdown_index_limit),
            "--markdown-link-limit",
            str(args.markdown_link_limit),
        ])
    return cmd


def _lifecycle_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(_resource("scripts/primitive_source_lifecycle.py")),
        "--limit",
        str(args.lifecycle_limit),
    ]


def _route_fixture_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(_resource("scripts/primitive_route_fixture_foundry.py")),
        "--direct-limit",
        str(args.route_fixture_direct_limit),
        "--mutator-limit",
        str(args.route_fixture_mutator_limit),
        "--chain-limit",
        str(args.route_fixture_chain_limit),
    ]


def _route_fixture_verifier_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(_resource("scripts/primitive_route_fixture_verifier.py")),
        "--search-sample-per-kind",
        str(args.route_fixture_verify_search_sample_per_kind),
        "--min-search-hit-rate",
        str(args.route_fixture_verify_min_search_hit_rate),
    ]


def _runtime_adapter_coverage_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        str(_resource("scripts/runtime_adapter_coverage_report.py")),
        "--low-coverage-count",
        str(args.runtime_adapter_low_coverage_count),
        "--fixtures-per-target",
        str(args.runtime_adapter_fixtures_per_target),
    ]


def _proof_commands(args: argparse.Namespace) -> list[list[str]]:
    cmds = [
        [
            sys.executable,
            "-m",
            "py_compile",
            "scripts/aidevobserver_edge_foundry.py",
            "scripts/aidevobserver_context_foundry_loop.py",
            "scripts/observer_local_service.py",
            "scripts/primitive_source_lifecycle.py",
            "scripts/primitive_route_fixture_foundry.py",
            "scripts/primitive_route_fixture_verifier.py",
            "scripts/runtime_adapter_coverage_report.py",
            "scripts/naics_primitive_scope_generator.py",
            "scripts/business_operation_scope_generator.py",
            "src/teleon/observer/registry_search.py",
            "src/teleon/observer/settings.py",
        ],
        [sys.executable, str(_resource("scripts/aidevobserver_edge_foundry.py")), "--self-test"],
        [sys.executable, str(_resource("scripts/aidevobserver_context_foundry_loop.py")), "--self-test"],
        [sys.executable, str(_resource("scripts/primitive_source_lifecycle.py")), "--self-test"],
        [sys.executable, str(_resource("scripts/primitive_route_fixture_foundry.py")), "--self-test"],
        [sys.executable, str(_resource("scripts/primitive_route_fixture_verifier.py")), "--self-test"],
        [sys.executable, str(_resource("scripts/runtime_adapter_coverage_report.py")), "--self-test"],
        [sys.executable, str(_resource("scripts/naics_primitive_scope_generator.py")), "--self-test"],
        [sys.executable, str(_resource("scripts/business_operation_scope_generator.py")), "--self-test"],
    ]
    if not args.skip_observer_self_test:
        cmds.append([sys.executable, str(_resource("scripts/observer_local_service.py")), "--self-test"])
    return cmds


def _search_smoke() -> list[dict[str, Any]]:
    from src.teleon.observer import registry_search

    registry_search._GLOBAL_PRIMITIVE_CACHE.clear()  # noqa: SLF001 - daemon owns refresh boundary.
    rows: list[dict[str, Any]] = []
    for query in DEFAULT_SEARCH_QUERIES:
        hits = registry_search.search_reusable_primitives(
            query,
            limit=5,
            visibility_scope=AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC,
        )
        private_leaks = [
            hit for hit in hits
            if hit.get("surface_visibility") == AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY
        ]
        rows.append({
            "query": query,
            "visibility_scope": AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC,
            "hit_count": len(hits),
            "private_visibility_leak_count": len(private_leaks),
            "top": [
                {
                    "source_kind": hit.get("source_kind"),
                    "label": hit.get("label"),
                    "domains": hit.get("domains") or [],
                    "score": hit.get("score"),
                    "source_ref": hit.get("source_ref"),
                    "surface_visibility": hit.get("surface_visibility"),
                    "candidate": True,
                    "serves_truth": False,
                }
                for hit in hits[:3]
            ],
            "candidate": True,
            "serves_truth": False,
        })
    return rows


def _append_human_log(row: dict[str, Any]) -> None:
    HUMAN_LOG.parent.mkdir(parents=True, exist_ok=True)
    manifest = row.get("edge_manifest") or {}
    domain_counts = manifest.get("domain_counts") or {}
    family_counts = manifest.get("source_family_counts") or {}
    search_ok = sum(1 for item in row.get("search_smoke") or [] if item.get("hit_count"))
    visibility_leaks = sum(int(item.get("private_visibility_leak_count") or 0) for item in row.get("search_smoke") or [])
    command_status = ", ".join(f"{c['label']}={c['status']}" for c in row.get("commands") or [])
    route_manifest = row.get("route_fixture_manifest") or {}
    route_verification = row.get("route_fixture_verification") or {}
    runtime_coverage = row.get("runtime_adapter_coverage") or {}
    lifecycle_manifest = row.get("lifecycle_manifest") or {}
    section = (
        f"\n## {row['started_at']} · Persistent Primitive Foundry Tick\n\n"
        f"- **Daemon tick:** `{row['tick_id']}`; status `{row['status']}`; "
        f"duration `{row['seconds']}` seconds.\n"
        f"- **Generated corpus:** `{manifest.get('record_count', 0)}` edge cards, "
        "all `candidate=true` and `serves_truth=false`.\n"
        f"- **Source families:** `{family_counts}`.\n"
        f"- **Top domains:** `{dict(sorted(domain_counts.items(), key=lambda item: (-item[1], item[0]))[:10])}`.\n"
        f"- **Context foundry:** `{row.get('context_counts')}`.\n"
        f"- **Lifecycle search/vector rows:** `{lifecycle_manifest.get('search_cards')}` search cards, "
        f"`{lifecycle_manifest.get('vector_rows')}` vector rows.\n"
        f"- **Route fixtures:** `{route_manifest.get('route_fixtures')}` fixtures, "
        f"`{route_manifest.get('candidate_bundles')}` CandidateBundles, "
        f"kinds `{route_manifest.get('fixture_kind_counts')}`.\n"
        f"- **Route fixture verification:** ok=`{route_verification.get('ok')}`, "
        f"checked `{route_verification.get('fixtures_checked')}` fixtures, "
        f"structural errors `{route_verification.get('structural_error_count')}`, "
        f"search hits `{route_verification.get('search_hits')}/{route_verification.get('search_checked')}`.\n"
        f"- **Runtime adapter coverage:** ok=`{runtime_coverage.get('ok')}`, "
        f"fixtures `{runtime_coverage.get('fixture_count')}`, "
        f"blocking gaps `{runtime_coverage.get('blocking_gap_count')}`, "
        f"low-coverage gaps `{runtime_coverage.get('low_coverage_gap_count')}`.\n"
        f"- **Search smoke:** `{search_ok}/{len(row.get('search_smoke') or [])}` query families returned candidates.\n"
        f"- **Public visibility check:** `{visibility_leaks}` private/internal public-search leaks.\n"
        f"- **Commands:** {command_status}.\n"
        "- **Next loop:** continue expanding structured source extractors, proof fixtures, "
        "promotion gates, and live-source connectors without promoting candidates directly.\n"
    )
    with HUMAN_LOG.open("a", encoding="utf-8") as handle:
        handle.write(section)


def run_tick(args: argparse.Namespace, *, tick_index: int) -> dict[str, Any]:
    started_at = _utc()
    started = time.time()
    tick_id = f"foundry_tick_{int(started)}_{tick_index}"
    commands: list[dict[str, Any]] = []

    for label, cmd, timeout in [
        ("edge_foundry", _edge_command(args), args.edge_timeout),
        ("context_foundry", _context_command(args), args.context_timeout),
        ("primitive_lifecycle", _lifecycle_command(args), args.lifecycle_timeout),
        ("route_fixture_foundry", _route_fixture_command(args), args.route_fixture_timeout),
        ("route_fixture_verifier", _route_fixture_verifier_command(args), args.route_fixture_verify_timeout),
        ("runtime_adapter_coverage", _runtime_adapter_coverage_command(args), args.runtime_adapter_timeout),
    ]:
        result = _run(cmd, timeout=timeout)
        result["label"] = label
        commands.append(result)

    if not args.skip_proofs:
        for index, cmd in enumerate(_proof_commands(args), start=1):
            result = _run(cmd, timeout=args.proof_timeout)
            result["label"] = f"proof_{index}"
            commands.append(result)

    edge_manifest = _load_json(EDGE_MANIFEST, {})
    context_last = _last_jsonl(CONTEXT_LEDGER)
    lifecycle_manifest = _load_json(LIFECYCLE_MANIFEST, {})
    route_fixture_manifest = _load_json(ROUTE_FIXTURE_MANIFEST, {})
    route_fixture_verification = _load_json(ROUTE_FIXTURE_VERIFICATION_REPORT, {})
    runtime_adapter_coverage = _load_json(RUNTIME_ADAPTER_COVERAGE_REPORT, {})
    search_smoke = _search_smoke()
    ok = all(command.get("status") == "ok" for command in commands)
    if not all(item.get("hit_count") for item in search_smoke):
        ok = False
    if any(item.get("private_visibility_leak_count") for item in search_smoke):
        ok = False
    if route_fixture_verification and not route_fixture_verification.get("ok"):
        ok = False
    if runtime_adapter_coverage and not runtime_adapter_coverage.get("ok"):
        ok = False

    row = {
        "record_type": "aidevobserver_primitive_foundry_daemon_tick",
        "tick_id": tick_id,
        "started_at": started_at,
        "finished_at": _utc(),
        "seconds": round(time.time() - started, 3),
        "status": "ok" if ok else "needs_attention",
        "edge_manifest": edge_manifest,
        "context_counts": context_last.get("counts") or {},
        "context_ranking": context_last.get("ranking") or {},
        "lifecycle_manifest": {
            "primitive_rows_selected": lifecycle_manifest.get("primitive_rows_selected"),
            "search_cards": lifecycle_manifest.get("search_cards"),
            "vector_rows": lifecycle_manifest.get("vector_rows"),
            "serves_truth": lifecycle_manifest.get("serves_truth", False),
        },
        "route_fixture_manifest": {
            "route_fixtures": route_fixture_manifest.get("route_fixtures"),
            "candidate_bundles": route_fixture_manifest.get("candidate_bundles"),
            "fixture_kind_counts": route_fixture_manifest.get("fixture_kind_counts"),
            "serves_truth": route_fixture_manifest.get("serves_truth", False),
        },
        "route_fixture_verification": {
            "ok": route_fixture_verification.get("ok"),
            "fixtures_checked": route_fixture_verification.get("fixtures_checked"),
            "structural_error_count": route_fixture_verification.get("structural_error_count"),
            "search_checked": route_fixture_verification.get("search_checked"),
            "search_hits": route_fixture_verification.get("search_hits"),
            "search_hit_rate": route_fixture_verification.get("search_hit_rate"),
            "serves_truth": route_fixture_verification.get("serves_truth", False),
        },
        "runtime_adapter_coverage": {
            "ok": runtime_adapter_coverage.get("ok"),
            "edge_cards_read": runtime_adapter_coverage.get("edge_cards_read"),
            "fixture_count": runtime_adapter_coverage.get("fixture_count"),
            "blocking_gap_count": runtime_adapter_coverage.get("blocking_gap_count"),
            "low_coverage_gap_count": runtime_adapter_coverage.get("low_coverage_gap_count"),
            "runtime_target_counts": runtime_adapter_coverage.get("runtime_target_counts"),
            "runtime_mutator_counts": runtime_adapter_coverage.get("runtime_mutator_counts"),
            "serves_truth": runtime_adapter_coverage.get("serves_truth", False),
        },
        "search_smoke": search_smoke,
        "commands": commands,
        "candidate": True,
        "serves_truth": False,
    }
    _append_jsonl(LEDGER, row)
    LATEST.parent.mkdir(parents=True, exist_ok=True)
    LATEST.write_text(json.dumps(row, indent=2, sort_keys=True), encoding="utf-8")
    _append_human_log(row)
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the persistent proof-gated AIDevObserver primitive-foundry loop.")
    parser.add_argument("--once", action="store_true", help="Run one tick and exit.")
    parser.add_argument("--watch", action="store_true", help="Run forever unless --max-ticks is set.")
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between watch ticks.")
    parser.add_argument("--max-ticks", type=int, default=0, help="0 means forever in watch mode.")
    parser.add_argument("--edge-root", action="append", default=list(DEFAULT_EDGE_ROOTS), help="Root to scan for primitive edges. May repeat.")
    parser.add_argument("--exclude", action="append", default=[], help="Additional path part to exclude.")
    parser.add_argument("--edge-max-files", type=int, default=30000)
    parser.add_argument("--edge-max-records", type=int, default=250000)
    parser.add_argument("--max-structured-rows-per-file", type=int, default=80)
    parser.add_argument("--no-js", action="store_true")
    parser.add_argument("--no-structured", action="store_true")
    parser.add_argument("--context-local-repo-root", default=".")
    parser.add_argument("--context-local-repo-limit", type=int, default=500)
    parser.add_argument("--lifecycle-limit", type=int, default=0)
    parser.add_argument("--route-fixture-direct-limit", type=int, default=160)
    parser.add_argument("--route-fixture-mutator-limit", type=int, default=160)
    parser.add_argument("--route-fixture-chain-limit", type=int, default=120)
    parser.add_argument("--route-fixture-verify-search-sample-per-kind", type=int, default=1)
    parser.add_argument("--route-fixture-verify-min-search-hit-rate", type=float, default=0.5)
    parser.add_argument("--runtime-adapter-low-coverage-count", type=int, default=25)
    parser.add_argument("--runtime-adapter-fixtures-per-target", type=int, default=12)
    parser.add_argument("--surface-limit", type=int, default=500)
    parser.add_argument("--use-case-limit", type=int, default=500)
    parser.add_argument("--microsurface-limit", type=int, default=500)
    parser.add_argument("--search-scope-limit", type=int, default=0)
    parser.add_argument("--naics-scope-limit", type=int, default=0)
    parser.add_argument("--business-operation-scope-limit", type=int, default=0)
    parser.add_argument("--skip-multilingual-search-scopes", action="store_true")
    parser.add_argument("--include-local-claude", action="store_true")
    parser.add_argument("--derive-local-reviews", action="store_true")
    parser.add_argument("--live-github", action="store_true")
    parser.add_argument("--github-query-limit", type=int, default=3)
    parser.add_argument("--github-result-limit", type=int, default=5)
    parser.add_argument("--live-kaggle", action="store_true")
    parser.add_argument("--kaggle-topic-limit", type=int, default=3)
    parser.add_argument("--kaggle-result-limit", type=int, default=5)
    parser.add_argument("--live-rss-feeds", action="store_true")
    parser.add_argument("--rss-feed-limit", type=int, default=5)
    parser.add_argument("--rss-item-limit", type=int, default=5)
    parser.add_argument("--live-markdown-indexes", action="store_true")
    parser.add_argument("--markdown-index-limit", type=int, default=3)
    parser.add_argument("--markdown-link-limit", type=int, default=50)
    parser.add_argument("--skip-proofs", action="store_true")
    parser.add_argument("--skip-observer-self-test", action="store_true")
    parser.add_argument("--edge-timeout", type=int, default=900)
    parser.add_argument("--context-timeout", type=int, default=900)
    parser.add_argument("--lifecycle-timeout", type=int, default=900)
    parser.add_argument("--route-fixture-timeout", type=int, default=900)
    parser.add_argument("--route-fixture-verify-timeout", type=int, default=900)
    parser.add_argument("--runtime-adapter-timeout", type=int, default=900)
    parser.add_argument("--proof-timeout", type=int, default=900)
    args = parser.parse_args(argv)

    if not args.once and not args.watch:
        args.once = True

    tick_index = 0
    while True:
        tick_index += 1
        row = run_tick(args, tick_index=tick_index)
        print(json.dumps({
            "tick_id": row["tick_id"],
            "status": row["status"],
            "edge_records": (row.get("edge_manifest") or {}).get("record_count"),
            "search_families": sum(1 for item in row.get("search_smoke") or [] if item.get("hit_count")),
            "serves_truth": False,
        }, sort_keys=True))
        if args.once or not args.watch:
            return 0 if row["status"] == "ok" else 1
        if args.max_ticks and tick_index >= args.max_ticks:
            return 0 if row["status"] == "ok" else 1
        time.sleep(max(1, int(args.interval)))


if __name__ == "__main__":
    raise SystemExit(main())
