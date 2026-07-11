#!/usr/bin/env python3
"""Run one supervised 20M primitive generation and benchmark cycle.

The cycle is bounded, receipt-backed, and candidate-only:

1. refresh the 20M goal plan
2. generate a deterministic seed slice
3. compile and verify a shard window
4. package verified rows into linkable cards
5. benchmark reuse-vs-rebuild before and after the new cards are added
6. write a cycle manifest plus latest status
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import random
import sys
import time
from pathlib import Path
from typing import Any

_SBC = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "scripts" / "_repo_paths.py").exists()),
    Path(__file__).resolve().parents[1],
)
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))

from scripts._repo_paths import install as _install  # noqa: E402

_install()

from scripts._repo_paths import repo_root as _repo_root  # noqa: E402
from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts.build_twenty_million_primitive_goal import run as refresh_goal_plan  # noqa: E402
from scripts.generate_million_primitive_seed_bundle import generate_bundle  # noqa: E402
from scripts.package_linkable_primitive_cards import package_cards  # noqa: E402
from scripts.run_million_seed_bundle_compiler import run as compile_seed_bundle  # noqa: E402
from scripts.run_token_savings_experiments import aggregate, run_experiments  # noqa: E402


OUT_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "20m_goal" / "supervised_cycles"
LATEST_STATUS = _resource("data") / "dev-intel" / "primitive_factory" / "20m_goal" / "supervised_latest_status.json"
BASE_LINKABLE_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "linkable_cards"
GOAL_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "20m_goal"
DEFAULT_ROWS_PER_SHARD = 10_000
DEFAULT_SEED_ROWS = 100_000
DEFAULT_COMPILE_SHARDS = 2
DEFAULT_BENCHMARK_N = 300


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha(value: Any, *, n: int = 12) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:n]


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _read_jsonl(path: Path, *, limit: int = 0) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if limit and len(rows) >= limit:
            break
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _existing_cycle_manifests() -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for path in sorted(OUT_ROOT.glob("*/cycle_manifest.json")):
        data = _read_json(path)
        if data.get("record_type") == "twenty_million_supervised_cycle_manifest":
            manifests.append(data)
    return manifests


def _used_shard_indexes() -> set[int]:
    used: set[int] = set()
    for manifest in _existing_cycle_manifests():
        compiler = manifest.get("compiler_manifest") if isinstance(manifest.get("compiler_manifest"), dict) else {}
        try:
            start = int(compiler.get("start_shard") or 0)
            count = int(compiler.get("shard_count") or 0)
        except (TypeError, ValueError):
            continue
        for shard_index in range(start, max(start, start + count)):
            used.add(shard_index)
    return used


def _auto_start_shard(*, seed_manifest: dict[str, Any], compile_shards: int) -> int:
    try:
        shard_count = int(seed_manifest.get("shard_count") or 0)
    except (TypeError, ValueError):
        shard_count = 0
    if shard_count <= 0:
        return 0
    window = max(1, min(compile_shards, shard_count))
    used = _used_shard_indexes()
    for start in range(0, shard_count, window):
        candidate = set(range(start, min(shard_count, start + window)))
        if not candidate.issubset(used):
            return start
    return 0


def _rel(path: Path) -> str:
    root = _repo_root()
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _resource_rel(path: Path) -> str:
    try:
        return str(path.relative_to(_resource(".")))
    except ValueError:
        return _rel(path)


def _latest_base_linkable_manifest() -> dict[str, Any]:
    manifests = sorted(BASE_LINKABLE_ROOT.glob("*/manifest.json"), key=lambda p: p.stat().st_mtime)
    return _read_json(manifests[-1]) if manifests else {}


def _load_linkable_cards_from_manifest(manifest: dict[str, Any], *, limit: int = 0) -> list[dict[str, Any]]:
    cards_path = manifest.get("cards_path")
    if not isinstance(cards_path, str) or not cards_path:
        return []
    return _read_jsonl(_resource(cards_path), limit=limit)


def _bench_card(card: dict[str, Any]) -> dict[str, Any]:
    visible = card.get("visible_edge") if isinstance(card.get("visible_edge"), dict) else {}
    leverage = card.get("leverage_profile") if isinstance(card.get("leverage_profile"), dict) else {}
    return {
        "primitive_id": card.get("primitive_id") or card.get("card_id"),
        "title": card.get("title") or card.get("primitive_id"),
        "kind": card.get("kind") or "primitive",
        "input_edge": card.get("input_edge") or visible.get("input"),
        "output_edge": card.get("output_edge") or visible.get("output"),
        "contract": card.get("contract") or card.get("edge_contract") or {},
        "edge_contract": card.get("edge_contract") or {},
        "blackbox": card.get("blackbox") or "",
        "effects": card.get("effects") or [],
        "mutations": card.get("mutators") or [],
        "proof_requirements": card.get("proof_requirements") or [],
        "source_family": leverage.get("reuse_class") or "linkable_card",
        "domains": [leverage.get("reuse_class") or "twenty_million"],
        "candidate": True,
        "serves_truth": False,
    }


def _bench(
    cards: list[dict[str, Any]],
    *,
    n: int,
    k: int,
    seed: int,
    paraphrase: bool,
    out_dir: Path,
    label: str,
) -> dict[str, Any]:
    bench_cards = [_bench_card(card) for card in cards if card.get("primitive_id") or card.get("card_id")]
    if not bench_cards:
        summary = {"record_type": "token_savings_summary", "experiments": 0, "net_positive": False, "candidate": True, "serves_truth": False}
        _write_json(out_dir / f"{label}_summary.json", summary)
        return summary
    rows = run_experiments(bench_cards, n=min(n, len(bench_cards)), k=k, seed=seed, paraphrase=paraphrase)
    summary = aggregate(rows)
    summary.update({
        "label": label,
        "card_corpus_count": len(bench_cards),
        "candidate": True,
        "serves_truth": False,
    })
    _write_jsonl(out_dir / f"{label}_experiments.jsonl", rows)
    _write_json(out_dir / f"{label}_summary.json", summary)
    return summary


def _package_compiled_shards(*, compiler_manifest: dict[str, Any], cycle_dir: Path, limit_per_package: int) -> list[dict[str, Any]]:
    package_manifests: list[dict[str, Any]] = []
    for index, manifest_ref in enumerate(compiler_manifest.get("shard_manifests") or []):
        shard_manifest_path = _resource(str(manifest_ref))
        shard_manifest = _read_json(shard_manifest_path)
        verified_manifest = shard_manifest.get("verification_manifest") if isinstance(shard_manifest.get("verification_manifest"), dict) else {}
        verified_dir = _resource(str(verified_manifest.get("out_dir") or ""))
        if not verified_dir.exists():
            continue
        out_dir = cycle_dir / "linkable_cards" / f"shard_{index:03d}"
        packaged = package_cards(
            prefix="",
            run_date=_resource_rel(verified_dir),
            out_dir=out_dir,
            limit=limit_per_package,
            include_weak_source_refs=False,
        )
        package_manifests.append(packaged)
    return package_manifests


def _load_new_cards(package_manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for manifest in package_manifests:
        cards.extend(_load_linkable_cards_from_manifest(manifest))
    return cards


def run_cycle(
    *,
    seed_rows: int,
    rows_per_shard: int,
    compile_shards: int,
    start_shard: int | None,
    limit_per_shard: int,
    package_limit_per_shard: int,
    benchmark_n: int,
    benchmark_k: int,
    benchmark_seed: int,
    paraphrase: bool,
) -> dict[str, Any]:
    started = time.time()
    run_id = f"20m-supervised-cycle-{_stamp()}-{_sha({'seed_rows': seed_rows, 'compile_shards': compile_shards, 't': time.time_ns()})}"
    cycle_dir = OUT_ROOT / run_id
    cycle_dir.mkdir(parents=True, exist_ok=False)
    before_goal = refresh_goal_plan(
        out_root=GOAL_ROOT,
        target=20_000_000,
        rows_per_shard=10_000,
        daily_working_target=100_000,
        daily_candidate_target=400_000,
        horizon_days=60,
        start_date=dt.datetime.now(dt.timezone.utc).date(),
    )

    base_manifest = _latest_base_linkable_manifest()
    base_cards = _load_linkable_cards_from_manifest(base_manifest)
    benchmark_dir = cycle_dir / "benchmarks"
    before_benchmark = _bench(
        base_cards,
        n=benchmark_n,
        k=benchmark_k,
        seed=benchmark_seed,
        paraphrase=paraphrase,
        out_dir=benchmark_dir,
        label="before",
    )

    seed_dir = cycle_dir / "seed_bundle"
    seed_manifest = generate_bundle(
        bundle_dir=seed_dir,
        zip_path=cycle_dir / "seed_bundle.zip",
        total_rows=seed_rows,
        rows_per_shard=rows_per_shard,
        force=True,
    )
    resolved_start_shard = (
        _auto_start_shard(seed_manifest=seed_manifest, compile_shards=compile_shards)
        if start_shard is None or start_shard < 0
        else start_shard
    )
    compiler_manifest = compile_seed_bundle(
        bundle_root=seed_dir,
        out_root=cycle_dir / "compiler_runs",
        start_shard=resolved_start_shard,
        shard_count=compile_shards,
        limit_per_shard=limit_per_shard,
        verify=True,
    )
    package_manifests = _package_compiled_shards(
        compiler_manifest=compiler_manifest,
        cycle_dir=cycle_dir,
        limit_per_package=package_limit_per_shard,
    )
    new_cards = _load_new_cards(package_manifests)
    combined_cards = base_cards + new_cards
    after_benchmark = _bench(
        combined_cards,
        n=benchmark_n,
        k=benchmark_k,
        seed=benchmark_seed,
        paraphrase=paraphrase,
        out_dir=benchmark_dir,
        label="after",
    )

    new_card_count = sum(int(manifest.get("card_count") or 0) for manifest in package_manifests)
    new_high_leverage_count = sum(int(manifest.get("high_leverage_card_count") or 0) for manifest in package_manifests)
    new_saved_tokens = sum(int(manifest.get("estimated_saved_output_tokens_total") or 0) for manifest in package_manifests)
    before_saved = float(before_benchmark.get("avg_net_saved_tokens") or 0)
    after_saved = float(after_benchmark.get("avg_net_saved_tokens") or 0)
    improvement = {
        "card_count_delta": new_card_count,
        "high_leverage_card_delta": new_high_leverage_count,
        "estimated_saved_output_tokens_delta": new_saved_tokens,
        "avg_net_saved_tokens_before": before_saved,
        "avg_net_saved_tokens_after": after_saved,
        "avg_net_saved_tokens_delta": round(after_saved - before_saved, 3),
        "after_net_positive": bool(after_benchmark.get("net_positive")),
        "positive_improvement": new_card_count > 0 and new_saved_tokens > 0 and bool(after_benchmark.get("net_positive")),
        "candidate": True,
        "serves_truth": False,
    }
    manifest = {
        "record_type": "twenty_million_supervised_cycle_manifest",
        "run_id": run_id,
        "run_dir": str(cycle_dir),
        "created_at": _utc(),
        "duration_seconds": round(time.time() - started, 3),
        "parameters": {
            "seed_rows": seed_rows,
            "rows_per_shard": rows_per_shard,
            "compile_shards": compile_shards,
            "start_shard": resolved_start_shard,
            "start_shard_mode": "auto_next_unused" if start_shard is None or start_shard < 0 else "explicit",
            "limit_per_shard": limit_per_shard,
            "package_limit_per_shard": package_limit_per_shard,
            "benchmark_n": benchmark_n,
            "benchmark_k": benchmark_k,
            "benchmark_seed": benchmark_seed,
            "paraphrase": paraphrase,
        },
        "before_goal_run_id": before_goal.get("run_id"),
        "after_goal_run_id": "",
        "seed_manifest": seed_manifest,
        "compiler_manifest": compiler_manifest,
        "package_manifests": package_manifests,
        "before_benchmark": before_benchmark,
        "after_benchmark": after_benchmark,
        "improvement": improvement,
        "status_paths": {
            "cycle_manifest": _rel(cycle_dir / "cycle_manifest.json"),
            "supervised_latest_status": _rel(LATEST_STATUS),
            "goal_latest_status": _rel(GOAL_ROOT / "latest_status.json"),
        },
        "candidate": True,
        "serves_truth": False,
    }
    _write_json(cycle_dir / "cycle_manifest.json", manifest)
    after_goal = refresh_goal_plan(
        out_root=GOAL_ROOT,
        target=20_000_000,
        rows_per_shard=10_000,
        daily_working_target=100_000,
        daily_candidate_target=400_000,
        horizon_days=60,
        start_date=dt.datetime.now(dt.timezone.utc).date(),
    )
    manifest["after_goal_run_id"] = after_goal.get("run_id")
    _write_json(LATEST_STATUS, manifest)
    _write_json(cycle_dir / "cycle_manifest.json", manifest)
    return manifest


def _self_test() -> int:
    fake_card = {
        "card_id": "lpc:test",
        "primitive_id": "prim:test",
        "title": "Parse JSON response",
        "kind": "primitive",
        "visible_edge": {"input": "JsonText", "output": "RecordObject"},
        "edge_contract": {"summary": "parse"},
        "candidate": True,
        "serves_truth": False,
    }
    bench = _bench_card(fake_card)
    ok = (
        bench["candidate"] is True
        and bench["serves_truth"] is False
        and bench["input_edge"] == "JsonText"
        and bench["output_edge"] == "RecordObject"
    )
    print("PASS - 20M supervised cycle wiring is candidate-only." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--seed-rows", type=int, default=DEFAULT_SEED_ROWS)
    parser.add_argument("--rows-per-shard", type=int, default=DEFAULT_ROWS_PER_SHARD)
    parser.add_argument("--compile-shards", type=int, default=DEFAULT_COMPILE_SHARDS)
    parser.add_argument("--start-shard", type=int, default=-1, help="-1 = next unused shard window")
    parser.add_argument("--limit-per-shard", type=int, default=0)
    parser.add_argument("--package-limit-per-shard", type=int, default=0)
    parser.add_argument("--benchmark-n", type=int, default=DEFAULT_BENCHMARK_N)
    parser.add_argument("--benchmark-k", type=int, default=5)
    parser.add_argument("--benchmark-seed", type=int, default=23)
    parser.add_argument("--paraphrase", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.run:
        parser.error("--run is required unless --self-test is used")
    if args.seed_rows <= 0 or args.rows_per_shard <= 0 or args.compile_shards <= 0:
        parser.error("seed rows, rows per shard, and compile shards must be positive")
    manifest = run_cycle(
        seed_rows=args.seed_rows,
        rows_per_shard=args.rows_per_shard,
        compile_shards=args.compile_shards,
        start_shard=args.start_shard,
        limit_per_shard=max(0, args.limit_per_shard),
        package_limit_per_shard=max(0, args.package_limit_per_shard),
        benchmark_n=max(1, args.benchmark_n),
        benchmark_k=max(1, args.benchmark_k),
        benchmark_seed=max(0, args.benchmark_seed),
        paraphrase=args.paraphrase,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
