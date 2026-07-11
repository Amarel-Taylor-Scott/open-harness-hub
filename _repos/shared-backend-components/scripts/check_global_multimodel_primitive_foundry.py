#!/usr/bin/env python3
"""Validate the global multi-model primitive foundry contract.

The check is intentionally offline. It proves the configuration shape and safety
invariants for the source-to-usable-primitive workflow that can use Codex,
Ollama-hosted GLM/Kimi lanes, and browser capture tools without letting model
outputs become registry truth by themselves.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
CONTRACT = _resource("catalog") / "knowledge-packs" / "data" / "global-primitive-foundry" / "multimodel-lanes.json"

REQUIRED_LANES = {
    "lane.codex_orchestrator",
    "lane.glm_5_2_ollama_researcher",
    "lane.kimi_code_2_7_ollama_implementer",
    "lane.browser_capture_source_observer",
    "lane.deterministic_gatekeeper",
}

REQUIRED_STAGE_ORDER = [
    "stage.source_discovery",
    "stage.source_normalization",
    "stage.primitive_opportunity_distillation",
    "stage.cross_model_critique",
    "stage.contract_authoring",
    "stage.implementation_candidate",
    "stage.proof_generation",
    "stage.lifecycle_packaging",
    "stage.promotion_queue",
]

REQUIRED_GATES = {
    "license_and_attribution_gate",
    "privacy_redaction_gate",
    "raw_source_republish_gate",
    "candidate_only_gate",
    "contract_schema_gate",
    "effect_memory_cache_gate",
    "source_ref_gate",
    "no_unlicensed_source_copy_gate",
    "deterministic_replay_gate",
    "contract_proof_gate",
    "vector_staging_not_truth_gate",
    "promotion_gate",
    "serves_truth_flip_gate",
}

MODEL_LANE_TYPES = {"agent_engineer", "model_researcher", "model_code_reviewer"}


def _load() -> dict[str, Any]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    cfg = _load()
    lanes = {lane["lane_id"]: lane for lane in cfg.get("lanes", [])}
    stages = cfg.get("stages", [])
    stage_ids = [stage.get("stage_id") for stage in stages]
    gates = set(cfg.get("required_gates", []))

    check("contract is candidate-only at top level", cfg.get("serves_truth") is False)
    check("all required lanes exist", REQUIRED_LANES.issubset(lanes), str(REQUIRED_LANES - set(lanes)))
    check("stage order covers scrape-to-promotion path", stage_ids == REQUIRED_STAGE_ORDER, str(stage_ids))
    check("all required gates exist", REQUIRED_GATES.issubset(gates), str(REQUIRED_GATES - gates))

    model_resolution = cfg.get("model_resolution_policy", {})
    check("model tags resolve through env/provider registry, not code",
          model_resolution.get("research_model_env") == "OH_PRIMITIVE_RESEARCH_MODEL"
          and model_resolution.get("code_model_env") == "OH_PRIMITIVE_CODE_MODEL"
          and model_resolution.get("default_research_model_id") == "glm-5.2"
          and model_resolution.get("default_code_model_id") == "kimi-k2.7-code"
          and model_resolution.get("default_fallback_chat_model_id") == "glm-5.2"
          and model_resolution.get("raw_secrets_allowed") is False)

    model_lanes = [lane for lane in lanes.values() if lane.get("lane_type") in MODEL_LANE_TYPES]
    check("model lanes are present", len(model_lanes) >= 3)
    check("model lanes cannot promote or serve truth",
          all(lane.get("candidate_only_output") is True
              and lane.get("promotion_allowed") is False
              and lane.get("serves_truth") is False for lane in model_lanes))

    browser = lanes["lane.browser_capture_source_observer"]
    required_provenance = set(browser.get("required_provenance_fields", []))
    check("browser lane captures provenance needed for rights/privacy gates",
          {"url", "captured_at", "content_hash", "license_status", "redaction_status"}.issubset(required_provenance))
    check("browser lane cannot promote", browser.get("promotion_allowed") is False and browser.get("serves_truth") is False)

    gatekeeper = lanes["lane.deterministic_gatekeeper"]
    check("only deterministic gatekeeper may emit promotion candidates",
          gatekeeper.get("promotion_allowed") is True
          and "promotion_candidate" in gatekeeper.get("allowed_outputs", []))
    non_gatekeepers = [lane for lane in lanes.values() if lane["lane_id"] != "lane.deterministic_gatekeeper"]
    check("non-gatekeepers do not emit promotion candidates",
          all("promotion_candidate" not in lane.get("allowed_outputs", []) for lane in non_gatekeepers))

    for stage in stages:
        owner = stage.get("owner_lane")
        check(f"{stage.get('stage_id')} owner exists", owner in lanes, str(owner))
        check(f"{stage.get('stage_id')} gates are declared globally",
              set(stage.get("required_gates", [])).issubset(gates))

    usable = cfg.get("usable_primitive_definition", {})
    check("usable primitive requires proof/source/search/vector/promotion fields",
          {"canonical_identity", "contract", "effects", "source_ref", "proof_bundle", "search_card", "vector_row", "promotion_status"}.issubset(set(usable.get("must_have", []))))
    check("serves_truth flip is gated by proof, privacy, license, and promotion",
          {"proof_bundle_passes", "license_and_attribution_gate_passes", "privacy_redaction_gate_passes", "promotion_record_approved", "serves_truth_flip_gate_passes"}.issubset(set(usable.get("may_serve_truth_only_when", []))))

    print(
        "\n"
        + (
            "PASS - global multimodel primitive foundry contract: Codex, Ollama GLM/Kimi, browser capture, "
            "and deterministic gates are wired as candidate-only lanes from source discovery through primitive "
            "drafting, lifecycle packaging, vectors, and proof-gated promotion."
            if not failures
            else f"{len(failures)} FAILURES: {failures}"
        )
    )
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if "--self-test" in argv:
        return _self_test()
    print("usage: python3 scripts/check_global_multimodel_primitive_foundry.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
