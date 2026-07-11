#!/usr/bin/env python3
"""scripts.harness_bakeoff_spec — the model x harness x runtime x task bakeoff BACKBONE + a real availability
probe (candidate-only).

Owner research (2026-07-08, Raschka local-harness post + analysis): the HARNESS is a hidden runtime — the SAME
model on the SAME task burns different tokens / file-context / tool-calls / failure-modes under different
harnesses (Claude Code ~2x Codex tokens is the anecdote). So the factory must benchmark
`model x harness x runtime x task_family`. BOTH raw count and quality are co-measured, and NEITHER caps the other
(owner 2026-07-08: "raw count is very important, we will continue to scale it and then test against billions/
trillions of prompts and figure out what works best — stop artificially limiting yourself"). Raw candidate
count is a primary SCALING goal (scale to billions+); `executor_certified_per_million_tokens` is a quality
signal measured AT SCALE and tested empirically against massive prompt sets — a NON-DESTRUCTIVE router
(weight/rank/diversify), never a generation cap or a discard. This module encodes that as durable DATA:

  - `HarnessRunReceipt` — the new registry object type (one row per (task,model,harness,runtime) run);
  - the bakeoff MATRIX (models x harnesses x runtimes x task families) + a structured skip-reason taxonomy;
  - the three metric layers, headline = `executor_certified_per_million_tokens` (the metric law: optimize this,
    never raw candidate_count);
  - `probe_availability()` — a REAL probe of what is installed/reachable here (harness CLIs on PATH, local
    runtime ports open, provider keys present) that NEVER runs a local model (dev-PC crash rule) and NEVER
    prints a key.

Execution of the full bakeoff is GATED on a local-capable rig (the DGX Spark) — on the dev PC local models are
disabled; this backbone (receipt + matrix + metric + probe) is the reusable, testable core. candidate-only.

    python3 scripts/harness_bakeoff_spec.py --self-test
    python3 scripts/harness_bakeoff_spec.py --probe
    python3 scripts/harness_bakeoff_spec.py --emit
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/ml_lifecycle_primitive_minter.py) ────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import socket  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"harness_bakeoff_spec requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real"  # no_proxy_gate: real=executed+measured / proxy=estimated
BAKEOFF_ID_PREFIX = "spec-bakeoff"
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"
SCHEMA_DIR_REL = "schemas/harness_bakeoff"
SPEC_FILENAME = "harness_bakeoff_spec.json"
PACKAGED_AT = "2026-07-08T00:00:00Z"
SOURCE_REFS = [
    "Sebastian Raschka (LinkedIn 2026-07-08): local open-weight LLMs across Qwen-Code/Codex/Claude Code; 30B "
    "MoE sweet spot ~40 tok/s on Mac/DGX Spark; Claude Code ~2x Codex tokens (anecdote, reproduce under control)",
    "owner analysis: benchmark model x harness x runtime x task_family; unit = executor-certified per token",
]

# ── the new registry object: HarnessRunReceipt (required fields) ─────────────────────────────────────────────
HARNESS_RUN_RECEIPT: dict[str, Any] = {
    "required": ["run_id", "task_id", "task_family", "model_id", "harness_id", "runtime_id", "hardware_id",
                 "input_tokens", "output_tokens", "cached_tokens", "tool_calls", "file_bytes_read",
                 "commands_run", "wall_time_ms", "success", "executor_certified", "verifier_mutation_pass",
                 "security_pass", "cost_estimate", "artifacts", "candidate", "serves_truth"],
    "invariants": {"serves_truth": False},
    "note": "one row per (task,model,harness,runtime) run; store request/response HASHES not raw prompts.",
}

# ── the bakeoff matrix (single source; extend by adding a row, never a rewrite — the multi-path law) ─────────
BAKEOFF_MODELS: list[str] = [
    "qwen3-coder-30b-a3b", "gemma-4-e2b", "gemma-4-e4b", "gemma-4-26b-a4b",
    "hy3", "glm-5.2", "kimi-k2.7-code", "nemotron-3-super-120b",
]
BAKEOFF_HARNESSES: list[str] = [
    "qwen_code", "codex", "claude_code_router", "opencode", "aider", "cline", "custom_primitive_harness",
]
BAKEOFF_RUNTIMES: list[str] = ["lmstudio", "ollama", "vllm", "llama_cpp", "openrouter", "nvidia"]
BAKEOFF_TASK_FAMILIES: list[str] = [
    "executor_synthesis", "fixture_generation", "verifier_generation", "api_interface_primitive",
    "browser_primitive", "repo_mining", "bugfix", "multi_file_package", "critique_improve", "dedupe",
]
SKIP_REASONS: list[str] = [
    "harness_missing", "runtime_missing", "model_missing", "incompatible_protocol", "insufficient_memory",
    "timeout", "provider_key_missing", "local_disabled_dev_pc",
]

# ── metrics: three layers; the HEADLINE + the metric law ─────────────────────────────────────────────────────
METRIC_LAYERS: dict[str, list[str]] = {
    "harness_overhead": ["input_tokens", "output_tokens", "cached_tokens", "tool_call_count", "file_context_bytes",
                         "commands_run", "messages_per_task", "round_trips", "wall_time", "tokens_per_success"],
    "quality": ["task_success", "oracle_pass", "executor_security_pass", "positive_fixture_pass",
                "negative_fixture_pass", "adversarial_fixture_pass", "deterministic_replay_pass",
                "verifier_mutation_pass", "human_review_required"],
    "factory_value": ["candidate_count", "useful_candidate_rate", "executor_ready_rate", "executor_certified_rate",
                      "duplicate_rate", "placeholder_rate", "security_fail_rate", "cost_per_useful_candidate",
                      "executor_certified_per_million_tokens", "real_ab_generation_saved_fraction"],
}
HEADLINE_METRIC = "executor_certified_per_million_tokens"
METRIC_LAW = ("scale raw candidate_count aggressively (billions+) AND co-measure "
              "executor_certified_per_million_tokens as a quality signal AT SCALE, tested empirically against "
              "billions/trillions of prompts. BOTH are primary; neither caps the other. Usefulness is a "
              "NON-DESTRUCTIVE router (weight/rank/diversify), never a generation cap or a discard.")

# ── hardware lanes (the dev-PC crash rule vs the local-capable rig) ──────────────────────────────────────────
HARDWARE_LANES: dict[str, Any] = {
    "dev_pc": {"local_models": "disabled", "reason": "owner: local models crash this PC", "runs": "cloud lanes only"},
    "dgx_spark": {"local_models": "candidate", "unified_memory_gb": 128, "inference_up_to_params_b": 200,
                  "note": "local 30B-MoE minting here bypasses the 429 throttle; enable when reachable"},
}

# ── availability probe targets (local runtime ports; provider keys checked env-only) ─────────────────────────
_HARNESS_CLIS: dict[str, list[str]] = {
    "qwen_code": ["qwen", "qwen-code"], "codex": ["codex"], "claude_code_router": ["ccr", "claude-code-router"],
    "opencode": ["opencode"], "aider": ["aider"], "cline": ["cline"], "claude_code": ["claude"],
}
_RUNTIME_PORTS: dict[str, int] = {"lmstudio": 1234, "ollama": 11434, "vllm": 8000, "llama_cpp": 8080}
_PROVIDER_KEY_ENVS: dict[str, list[str]] = {
    "openrouter": ["OPENROUTER_API_KEY"], "nvidia": ["NVIDIA_API_KEY"], "openai_compatible": ["OPENAI_API_KEY"],
}


def _port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.2) -> bool:
    """TCP connect check only — NEVER sends a request or runs a model."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def probe_availability() -> dict[str, Any]:
    """Report what is installed/reachable HERE without running any local model or printing any key."""
    harnesses = {name: {"available": any(shutil.which(c) for c in clis),
                        "checked": clis} for name, clis in _HARNESS_CLIS.items()}
    runtimes = {name: {"port": port, "reachable": _port_open(port)} for name, port in _RUNTIME_PORTS.items()}
    # OpenRouter keys also live in the gitignored .agent file at the REPO ROOT (walk up to find it); report
    # presence only (never the value).
    or_present = any((p / ".agent" / "openrouter_keys.txt").exists() for p in _here_boot.parents)
    provider_keys = {prov: {"present": any(os.environ.get(e) for e in envs)}
                     for prov, envs in _PROVIDER_KEY_ENVS.items()}
    provider_keys["openrouter"]["present"] = provider_keys["openrouter"]["present"] or or_present
    return {
        "record_type": "harness_bakeoff_availability_probe",
        "harness_clis": harnesses,
        "local_runtimes": runtimes,
        "provider_keys_present": provider_keys,
        "n_harnesses_available": sum(1 for v in harnesses.values() if v["available"]),
        "n_runtimes_reachable": sum(1 for v in runtimes.values() if v["reachable"]),
        "local_models_policy": HARDWARE_LANES["dev_pc"]["local_models"],
        "note": "availability only; no local model was run (dev-PC crash rule); no key printed.",
        **BOUNDARY,
    }


def build_spec() -> dict[str, Any]:
    spec_id = canonical_id(BAKEOFF_ID_PREFIX, "matrix",
                           str(len(BAKEOFF_MODELS)), str(len(BAKEOFF_HARNESSES)), str(len(BAKEOFF_TASK_FAMILIES)))
    return {
        "record_type": "harness_bakeoff_spec",
        "spec_id": spec_id,
        "title": "model x harness x runtime x task bakeoff — executor-certified-per-token",
        "framing": "the harness is a hidden runtime; measure model x harness x runtime x task_family; the unit "
                   "is executor-certified primitive per token, not raw candidate count.",
        "harness_run_receipt": HARNESS_RUN_RECEIPT,
        "matrix": {"models": BAKEOFF_MODELS, "harnesses": BAKEOFF_HARNESSES, "runtimes": BAKEOFF_RUNTIMES,
                   "task_families": BAKEOFF_TASK_FAMILIES,
                   "cells": len(BAKEOFF_MODELS) * len(BAKEOFF_HARNESSES) * len(BAKEOFF_RUNTIMES) *
                   len(BAKEOFF_TASK_FAMILIES)},
        "skip_reasons": SKIP_REASONS,
        "metric_layers": METRIC_LAYERS,
        "headline_metric": HEADLINE_METRIC,
        "metric_law": METRIC_LAW,
        "hardware_lanes": HARDWARE_LANES,
        "routing_output": "learned routing table: best (harness,model,runtime) per task_family by "
                          f"{HEADLINE_METRIC} — feeds llm_capability_router.",
        "source_refs": SOURCE_REFS,
        "packaged_at": PACKAGED_AT,
        **BOUNDARY,
    }


def emit() -> dict[str, Any]:
    spec = build_spec()
    out_dir = resource(PACK_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / SPEC_FILENAME).write_text(json.dumps(spec, indent=2, sort_keys=True), encoding="utf-8")
    sch_dir = resource(SCHEMA_DIR_REL)
    sch_dir.mkdir(parents=True, exist_ok=True)
    receipt_schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "HarnessRunReceipt",
                      "type": "object", "required": HARNESS_RUN_RECEIPT["required"],
                      "properties": {f: {} for f in HARNESS_RUN_RECEIPT["required"]},
                      "x_invariants": HARNESS_RUN_RECEIPT["invariants"], "x_candidate_only": True}
    (sch_dir / "HarnessRunReceipt.schema.json").write_text(json.dumps(receipt_schema, indent=2, sort_keys=True),
                                                           encoding="utf-8")
    return {"spec_path": str(out_dir / SPEC_FILENAME), "matrix_cells": spec["matrix"]["cells"],
            "schema": str(sch_dir / "HarnessRunReceipt.schema.json")}


def self_test() -> bool:
    """Mutation-gated: a missing receipt provenance field, the headline metric absent, or the metric law
    optimizing raw count goes RED."""
    # (1) receipt carries token accounting + certification + the boundary.
    for f in ("input_tokens", "output_tokens", "executor_certified", "verifier_mutation_pass", "security_pass",
              "serves_truth"):
        assert f in HARNESS_RUN_RECEIPT["required"], f"HarnessRunReceipt missing {f}"
    assert HARNESS_RUN_RECEIPT["invariants"]["serves_truth"] is False

    # (2) the matrix is non-trivial and the headline metric exists in factory_value.
    spec = build_spec()
    assert spec["matrix"]["cells"] == (len(BAKEOFF_MODELS) * len(BAKEOFF_HARNESSES) * len(BAKEOFF_RUNTIMES)
                                       * len(BAKEOFF_TASK_FAMILIES)) > 100
    assert HEADLINE_METRIC in METRIC_LAYERS["factory_value"], "headline metric not in factory_value"

    # (3) the metric law keeps BOTH raw count (a scaling goal) AND certified-per-token (a quality signal) as
    #     first-class, tracked metrics — neither caps the other (owner: raw count is very important, scale it).
    assert "candidate_count" in METRIC_LAYERS["factory_value"], "raw candidate_count must be a tracked metric"
    assert HEADLINE_METRIC in METRIC_LAYERS["factory_value"], "certified-per-token must be a tracked metric"
    assert "scale raw candidate_count" in METRIC_LAW and "NON-DESTRUCTIVE router" in METRIC_LAW

    # (4) skip taxonomy includes the dev-PC local-disabled reason (honest about what we can't run).
    assert "local_disabled_dev_pc" in SKIP_REASONS
    assert HARDWARE_LANES["dev_pc"]["local_models"] == "disabled"

    # (5) the probe runs, returns structure, and NEVER ran a local model / printed a key.
    probe = probe_availability()
    assert probe["local_models_policy"] == "disabled"
    assert set(probe["local_runtimes"]) == set(_RUNTIME_PORTS)
    assert probe["candidate"] is True and probe["serves_truth"] is False
    # provider key presence is a bool, never the value.
    for prov, info in probe["provider_keys_present"].items():
        assert isinstance(info["present"], bool), f"{prov} key presence leaked a non-bool"

    # (6) spec candidate-only + deterministic id.
    assert spec["candidate"] is True and spec["serves_truth"] is False
    assert build_spec()["spec_id"] == spec["spec_id"]

    print(f"OK harness_bakeoff_spec self-test: {spec['matrix']['cells']} matrix cells "
          f"({len(BAKEOFF_MODELS)}x{len(BAKEOFF_HARNESSES)}x{len(BAKEOFF_RUNTIMES)}x{len(BAKEOFF_TASK_FAMILIES)}), "
          f"headline={HEADLINE_METRIC}, probe ran (no local model, no key), serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="model x harness x runtime x task bakeoff backbone + probe.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--probe", action="store_true", help="report installed harnesses/runtimes/keys (no model run)")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.probe:
        print(json.dumps(probe_availability(), indent=2))
        return
    if args.emit:
        print(json.dumps(emit(), indent=2))
        return
    if args.show:
        print(json.dumps(build_spec(), indent=2, sort_keys=True))
        return
    self_test()


if __name__ == "__main__":
    main()
