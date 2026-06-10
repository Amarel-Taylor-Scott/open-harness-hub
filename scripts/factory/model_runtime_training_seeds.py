#!/usr/bin/env python3
"""Export model runtime, training, and federation component seeds to row families."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from scripts.factory.use_case_seed_rows import export_seed_rows


DEFAULT_SEEDS = "catalog/knowledge-packs/data/model-runtime-training-component-patterns/patterns.jsonl"


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def export_model_runtime_training_rows(
    *,
    seeds_path: str | Path = DEFAULT_SEEDS,
    output_dir: str | Path,
    excluded_scopes: list[str] | None = None,
) -> dict[str, Any]:
    seeds = _read_jsonl(seeds_path)
    rows = export_seed_rows(seeds, output_dir=output_dir, excluded_scopes=excluded_scopes or ["insurance"])
    summary = {
        "ok": True,
        "version": "0.1.0",
        "seed_path": str(seeds_path),
        "seed_count": len(seeds),
        "output_dir": rows["output_dir"],
        "row_counts": rows["row_counts"],
        "row_family_paths": rows["row_family_paths"],
        "warnings": rows.get("warnings", []),
        "notes": [
            "Rows are staged candidates for model/runtime/training/federation components.",
            "Training and federated sharing rows are review-gated before promotion.",
            "The exporter does not download models, train weights, apply SQL, or contact Kubernetes.",
        ],
    }
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir, "model-runtime-training-seed-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return summary


def _self_test() -> int:
    sample = [
        {
            "id": "local-runtime-self-test",
            "title": "Local runtime self test",
            "domain": "ai_local_runtime",
            "task": "Create a local runtime component candidate.",
            "inputs": ["model"],
            "outputs": ["runtime_component"],
            "risk_tier": "medium",
            "required_stages": ["privacy_boundary_check", "audit_trace_emission"],
            "label_paths": ["runtime.local", "model.test"],
            "excluded_scope": ["insurance"],
        },
        {
            "id": "training-gate-self-test",
            "title": "Training gate self test",
            "domain": "ai_training_governance",
            "task": "Create a training data review gate component candidate.",
            "inputs": ["candidate_training_rows"],
            "outputs": ["review_ticket"],
            "risk_tier": "high",
            "required_stages": ["pii_screening", "human_review_route"],
            "label_paths": ["training.governance", "review.required"],
            "excluded_scope": ["insurance"],
        },
    ]
    with tempfile.TemporaryDirectory() as tmp:
        seed_path = Path(tmp) / "seeds.jsonl"
        seed_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in sample), encoding="utf-8")
        result = export_model_runtime_training_rows(seeds_path=seed_path, output_dir=Path(tmp) / "rows")
        assert result["ok"] is True
        assert result["seed_count"] == 2
        assert result["row_counts"]["normalized_object"] == 2
        assert result["row_counts"]["review_ticket"] >= 1
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--seeds-path", default=DEFAULT_SEEDS)
    parser.add_argument("--output-dir")
    parser.add_argument("--excluded-scopes", nargs="*", default=["insurance"])
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.output_dir:
        parser.error("--output-dir is required unless --self-test is used")
    result = export_model_runtime_training_rows(
        seeds_path=args.seeds_path,
        output_dir=args.output_dir,
        excluded_scopes=args.excluded_scopes,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
