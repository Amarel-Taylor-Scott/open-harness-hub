#!/usr/bin/env python3
"""Generate and load-audit a daily model-ops component candidate batch."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.db.daily_partition_load_audit import build_daily_partition_load_audit
from scripts.factory.model_runtime_training_seeds import DEFAULT_SEEDS, _read_jsonl
from scripts.factory.use_case_seed_rows import export_seed_rows


MODEL_FAMILIES = [
    ("gemma", "Gemma-family local and hosted models"),
    ("llama", "Llama-family local and hosted models"),
    ("qwen", "Qwen-family local and hosted models"),
    ("mistral", "Mistral-family local and hosted models"),
    ("phi", "Phi-family edge and desktop models"),
    ("embedding", "Embedding and rerank model endpoints"),
]

RUNTIME_TARGETS = [
    ("local_python", "Local Python process"),
    ("desktop_ollama", "Desktop Ollama service"),
    ("edge_llama_cpp", "Edge llama.cpp process"),
    ("render_worker", "Render background worker"),
    ("k8s_vllm", "Kubernetes vLLM service"),
    ("cloud_run_container", "Cloud Run container worker"),
    ("airgapped_node", "Air-gapped local node"),
]

COST_PROFILES = [
    ("cheap", "cheap"),
    ("balanced", "balanced"),
    ("quality", "quality"),
    ("local_first", "local-first"),
    ("high_assurance", "high-assurance"),
]

PRIVACY_BOUNDARIES = [
    ("local_only", "raw context stays local"),
    ("reviewed_objects_only", "only reviewed objects leave the node"),
    ("redacted_export", "redacted export with hash receipt"),
    ("tenant_private", "tenant-private hosted runtime"),
]


def _today() -> str:
    return dt.date.today().isoformat()


def _safe_slug(value: str) -> str:
    chars: list[str] = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")[:80] or "unknown"


def _slug_with_hash(value: str, *, max_slug_len: int = 60, hash_len: int = 12) -> str:
    slug = _safe_slug(value)[:max_slug_len].strip("-") or "unknown"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:hash_len]
    return f"{slug}-{digest}"


def _variant_seed(base: dict[str, Any], ordinal: int) -> dict[str, Any]:
    model_family, model_label = MODEL_FAMILIES[ordinal % len(MODEL_FAMILIES)]
    runtime_target, runtime_label = RUNTIME_TARGETS[(ordinal // len(MODEL_FAMILIES)) % len(RUNTIME_TARGETS)]
    cost_profile, cost_label = COST_PROFILES[(ordinal // (len(MODEL_FAMILIES) * len(RUNTIME_TARGETS))) % len(COST_PROFILES)]
    privacy_boundary, privacy_label = PRIVACY_BOUNDARIES[
        (ordinal // (len(MODEL_FAMILIES) * len(RUNTIME_TARGETS) * len(COST_PROFILES))) % len(PRIVACY_BOUNDARIES)
    ]
    base_id = str(base.get("id") or f"model-ops-pattern-{ordinal}")
    variant_key = f"{base_id}-{model_family}-{runtime_target}-{cost_profile}-{privacy_boundary}-{ordinal:05d}"
    variant_id = _slug_with_hash(variant_key)

    seed = dict(base)
    seed["id"] = variant_id
    seed["title"] = f"{base.get('title', base_id)} for {model_label} on {runtime_label}"
    seed["task"] = (
        f"{base.get('task', '')} Configure this candidate for {model_label}, {runtime_label}, "
        f"a {cost_label} cost profile, and a {privacy_label} privacy boundary. Preserve source governance, "
        "model-swap metadata, cost dimensions, runtime constraints, review gates, and index records."
    ).strip()
    seed["domain"] = str(base.get("domain") or "ai_model_ops")
    seed["inputs"] = sorted(set([str(value) for value in base.get("inputs", [])] + ["model_family", "runtime_target", "cost_profile", "privacy_boundary"]))
    seed["outputs"] = sorted(set([str(value) for value in base.get("outputs", [])] + ["model_route_record", "runtime_dimension", "review_ticket"]))
    seed["required_stages"] = sorted(
        set(
            [str(value) for value in base.get("required_stages", [])]
            + [
                "source_governance",
                "normalized_object_schema",
                "entity_linking",
                "fuzzy_dedupe",
                "index_record_emission",
                "review_ticket_routing",
            ]
        )
    )
    seed["label_paths"] = sorted(
        set(
            [str(value) for value in base.get("label_paths", [])]
            + [
                f"model_family.{model_family}",
                f"runtime.{runtime_target}",
                f"cost_profile.{cost_profile}",
                f"privacy_boundary.{privacy_boundary}",
                "factory.model_ops_daily",
            ]
        )
    )
    if cost_profile == "high_assurance" or privacy_boundary in {"reviewed_objects_only", "redacted_export"}:
        seed["risk_tier"] = "high"
    else:
        seed["risk_tier"] = str(base.get("risk_tier") or "medium")
    seed["excluded_scope"] = sorted(set([str(value) for value in base.get("excluded_scope", [])] + ["insurance"]))
    seed["metadata"] = {
        "base_seed_id": base_id,
        "model_family": model_family,
        "runtime_target": runtime_target,
        "cost_profile": cost_profile,
        "privacy_boundary": privacy_boundary,
        "variant_ordinal": ordinal,
    }
    return seed


def build_model_ops_daily_seeds(*, target_count: int, seeds_path: str | Path = DEFAULT_SEEDS) -> list[dict[str, Any]]:
    base_seeds = _read_jsonl(seeds_path)
    if not base_seeds:
        raise ValueError(f"{seeds_path}: no seed patterns found")
    seeds: list[dict[str, Any]] = []
    ordinal = 0
    while len(seeds) < target_count:
        for base in base_seeds:
            if len(seeds) >= target_count:
                break
            seeds.append(_variant_seed(base, ordinal))
            ordinal += 1
    return seeds


def run_model_ops_daily_batch(
    *,
    run_date: str,
    output_dir: str | Path,
    target_count: int = 1000,
    seeds_path: str | Path = DEFAULT_SEEDS,
) -> dict[str, Any]:
    out = Path(output_dir)
    row_dir = out / "rows"
    seed_path = out / "model-ops-component-seeds.jsonl"
    run_id = f"model-ops-daily-{run_date}"

    seeds = build_model_ops_daily_seeds(target_count=target_count, seeds_path=seeds_path)
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text("".join(json.dumps(seed, sort_keys=True, ensure_ascii=False) + "\n" for seed in seeds), encoding="utf-8")
    row_summary = export_seed_rows(seeds, output_dir=row_dir, excluded_scopes=["insurance"])
    load_audit = build_daily_partition_load_audit(
        partitions=[row_dir],
        output_dir=out / "load-audit",
        run_id=run_id,
    )

    summary = {
        "ok": bool(load_audit.get("ok")),
        "version": "0.1.0",
        "run_date": run_date,
        "run_id": run_id,
        "target_count": target_count,
        "base_seed_path": str(seeds_path),
        "seed_path": str(seed_path),
        "output_dir": str(out),
        "row_counts": row_summary["row_counts"],
        "row_family_paths": row_summary["row_family_paths"],
        "load_audit": {
            "audit_status": load_audit.get("audit_status"),
            "raw_total": load_audit.get("merge_report", {}).get("raw_total"),
            "unique_total": load_audit.get("merge_report", {}).get("unique_total"),
            "duplicate_total": load_audit.get("merge_report", {}).get("duplicate_total"),
            "preflight": load_audit.get("preflight"),
            "load_sql": load_audit.get("bulk_manifest", {}).get("load_sql"),
        },
        "notes": [
            "This run stages model/runtime/training/federation candidates and emits a side-effect-free load plan.",
            "It does not download model weights, train models, contact Kubernetes, or apply SQL.",
            "Training, high-assurance, and federated sharing candidates remain review-gated.",
        ],
    }
    (out / "model-ops-daily-run-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        result = run_model_ops_daily_batch(
            run_date="self-test",
            output_dir=tmp,
            target_count=36,
        )
        assert result["ok"] is True
        assert result["row_counts"]["normalized_object"] == 36
        seeds = _read_jsonl(Path(tmp) / "model-ops-component-seeds.jsonl")
        seed_ids = [str(seed["id"]) for seed in seeds]
        assert len(seed_ids) == len(set(seed_ids))
        assert result["load_audit"]["audit_status"] == "staged_only"
        assert result["load_audit"]["preflight"]["ok"] is True
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run-date", default=_today())
    parser.add_argument("--output-dir")
    parser.add_argument("--target-count", type=int, default=1000)
    parser.add_argument("--seeds-path", default=DEFAULT_SEEDS)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    output_dir = args.output_dir or f"dist/model-ops-daily-runs/{args.run_date}"
    result = run_model_ops_daily_batch(
        run_date=args.run_date,
        output_dir=output_dir,
        target_count=args.target_count,
        seeds_path=args.seeds_path,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
