#!/usr/bin/env python3
"""Durable-gap harness — sort capability gaps into transient vs structural.

The strategy this operationalizes (see docs/concepts/capability-valleys.md):
use humans as the measurement instrument — run a competent human and a frontier
model on the same task — but for every gap, tag *why* it lifts. The `lift_reason`
maps to a `durability_class` that decides the only thing that matters for where
to build:

    transient   → the data flywheel closes it (the demos you collect to find it
                  are the training set that erases it). Revenue today; discount
                  for defensibility, and keep its traces governed.
    structural  → no model/data/tool closes it (body, access, license, verifier,
                  volatile/un-ingestible source). The defensible niche — build.
    mixed       → part structural, part erodes — build but watch decay.

Input: a JSONL of gap trials. Each row:
    {
      "task": "...", "domain": "...",
      "human_won": true,                          # did a competent human beat the model
      "lift_reason": "closed_channel_access",      # WHY it lifts (reason_codes.LIFT_REASONS)
      "mechanism": "channel_inaccessibility",      # optional, why it's hard
      "retrievability_tier": "unaddressable_ephemeral",  # optional, key or 1..5
      "adversarial": true,                         # optional, non-stationary target
      "decay_signal": "none",                      # optional, none|watch|decaying
      "evidence": "...", "public_source": "..."    # optional provenance
    }

Deterministic, stdlib-only. Emits gap classifications, an index record per
structural gap (so it flows into the registry), review tickets for unknowns, and
a summary. No model calls — it scores the *reasons*, not the tasks.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts.eval.reason_codes import (
    DECAY_SIGNALS,
    LIFT_REASONS,
    MECHANISMS,
    TIER_BY_KEY,
    durability_class,
    gap_durability_score,
)

# Defensibility score (0..5) at/above which a structural, human-won gap is worth building.
BUILD_THRESHOLD = 3.5


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug(text: str) -> str:
    return (re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:80] or "gap")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{n}: expected a JSON object")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    path.write_text(body + ("\n" if rows else ""), encoding="utf-8")


def classify_gap(row: dict[str, Any]) -> dict[str, Any]:
    """Classify one gap trial: durability class, defensibility score, decision."""
    lift_reason = row.get("lift_reason") or row.get("reason_code")  # reason_code = back-compat alias
    mechanism = row.get("mechanism")
    tier_in = row.get("retrievability_tier")
    adversarial = bool(row.get("adversarial"))
    human_won = bool(row.get("human_won", True))
    decay = row.get("decay_signal", "none")

    klass = durability_class(lift_reason)
    score = gap_durability_score(
        reason_codes=[lift_reason] if lift_reason else [],
        retrievability_tier=tier_in,
        adversarial=adversarial,
        mechanisms=[mechanism] if mechanism else [],
    )

    notes: list[str] = []
    if lift_reason and lift_reason not in LIFT_REASONS:
        notes.append(f"unknown lift_reason '{lift_reason}' — not in the canonical taxonomy")
    if mechanism and mechanism not in MECHANISMS:
        notes.append(f"unknown mechanism '{mechanism}'")
    if isinstance(tier_in, str) and tier_in not in TIER_BY_KEY:
        notes.append(f"unknown retrievability_tier '{tier_in}'")
    if decay not in DECAY_SIGNALS:
        notes.append(f"unknown decay_signal '{decay}'")

    if not human_won:
        decision = "no_gap"  # model matched/beat the human — nothing to build
    elif klass == "structural" and score >= BUILD_THRESHOLD:
        decision = "build_durable"
    elif klass == "mixed":
        decision = "build_watch"     # build, but re-benchmark for decay
    elif lift_reason == "missing_tool":
        decision = "wire_a_tool"     # tiers 1-3: solvable by tooling, not a model leap
    elif klass == "transient":
        decision = "discount_transient"  # flywheel closes it — no moat
    else:
        decision = "review"  # unknown/untagged — a human must assign a lift_reason

    return {
        "gap_id": f"gap/{_slug(row.get('domain') or 'x')}/{_slug(row.get('task') or 'task')}",
        "task": row.get("task", ""),
        "domain": row.get("domain", ""),
        "human_won": human_won,
        "lift_reason": lift_reason,
        "mechanism": mechanism,
        "retrievability_tier": tier_in,
        "adversarial": adversarial,
        "durability_class": klass,
        "defensibility_score": score,
        "decay_signal": decay,
        "decision": decision,
        "notes": notes,
        "public_source": row.get("public_source", ""),
        "evidence": row.get("evidence", ""),
        "classified_at": _utc_now(),
    }


def _index_record(g: dict[str, Any]) -> dict[str, Any]:
    return {
        "index_record_id": f"idx:{_slug(g['gap_id'])}:durable-gap",
        "index_kind": "capability_gap",
        "subject_id": g["gap_id"],
        "subject_type": "durable_capability_gap",
        "text": " ".join(str(x) for x in (g["domain"], g["task"], g["lift_reason"], g["mechanism"])),
        "metadata": {
            "durability_class": g["durability_class"],
            "defensibility_score": g["defensibility_score"],
            "lift_reason": g["lift_reason"],
            "retrievability_tier": g["retrievability_tier"],
            "decay_signal": g["decay_signal"],
        },
    }


def _review_ticket(g: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_ticket_id": f"review/{_slug(g['gap_id'])}",
        "object_id": g["gap_id"],
        "review_type": "capability_gap_lift_reason",
        "reason": " ".join(g["notes"]) or "Gap is human-won but has no lift_reason — assign one.",
        "status": "open",
        "priority": "medium",
        "created_at": _utc_now(),
    }


def run(*, input_path: str, output_dir: str) -> dict[str, Any]:
    rows = _read_jsonl(Path(input_path))
    classified = [classify_gap(r) for r in rows]
    structural = [g for g in classified if g["decision"] in ("build_durable", "build_watch")]
    index_records = [_index_record(g) for g in structural]
    review_tickets = [_review_ticket(g) for g in classified if g["decision"] == "review"]

    out = Path(output_dir)
    paths = {
        "gap_classifications": out / "gap-classifications.jsonl",
        "durable_index_records": out / "durable-gap-index-records.jsonl",
        "review_tickets": out / "gap-review-tickets.jsonl",
    }
    _write_jsonl(paths["gap_classifications"], classified)
    _write_jsonl(paths["durable_index_records"], index_records)
    _write_jsonl(paths["review_tickets"], review_tickets)

    def _count(decision: str) -> int:
        return sum(1 for g in classified if g["decision"] == decision)

    summary = {
        "ok": True,
        "gaps": len(classified),
        "structural": sum(1 for g in classified if g["durability_class"] == "structural"),
        "transient": sum(1 for g in classified if g["durability_class"] == "transient"),
        "mixed": sum(1 for g in classified if g["durability_class"] == "mixed"),
        "build_durable": _count("build_durable"),
        "build_watch": _count("build_watch"),
        "wire_a_tool": _count("wire_a_tool"),
        "discount_transient": _count("discount_transient"),
        "no_gap": _count("no_gap"),
        "review": _count("review"),
        "build_threshold": BUILD_THRESHOLD,
        "paths": {k: str(v) for k, v in paths.items()},
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def _self_test() -> int:
    trials = [
        {"task": "State which ILO conventions Nigeria ratified and when", "domain": "international labor law",
         "human_won": True, "lift_reason": "long_tail_fact", "mechanism": "sparse_data",
         "retrievability_tier": "structured_no_api"},
        {"task": "Get last night's NYC 311 noise-complaint counts by borough", "domain": "open civic data",
         "human_won": True, "lift_reason": "missing_tool", "mechanism": "coded_vocabulary",
         "retrievability_tier": "clean_api"},
        {"task": "Apply the recruitment-fee ban posted yesterday on the regulator's Facebook page (Pidgin, since edited)",
         "domain": "migrant labor", "human_won": True, "lift_reason": "no_addressable_source",
         "mechanism": "channel_inaccessibility", "retrievability_tier": "unaddressable_ephemeral", "adversarial": True},
        {"task": "Physically verify dormitory conditions at a labor site", "domain": "forced labor",
         "human_won": True, "lift_reason": "embodiment_required", "retrievability_tier": "human_only"},
        {"task": "Sign off on a structural inspection", "domain": "engineering",
         "human_won": True, "lift_reason": "accountability_or_license", "retrievability_tier": "human_only"},
        {"task": "Untagged thing a human did better", "domain": "misc", "human_won": True},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "trials.jsonl"
        _write_jsonl(src, trials)
        result = run(input_path=str(src), output_dir=str(Path(tmp) / "out"))
        assert result["gaps"] == 6, result
        assert result["build_durable"] == 3, result          # FB post, dorm inspect, sign-off
        assert result["wire_a_tool"] == 1, result            # the 311 API
        assert result["discount_transient"] == 1, result     # the long-tail fact
        assert result["review"] == 1, result                 # the untagged one
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Sort capability gaps into transient vs structural by lift reason.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--input")
    p.add_argument("--output-dir")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.input or not args.output_dir:
        p.error("--input and --output-dir are required")
    result = run(input_path=args.input, output_dir=args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
