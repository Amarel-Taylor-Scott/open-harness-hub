#!/usr/bin/env python3
"""scripts.check_object_shell_conformance_migration — PROOF: object families migrate to the canonical ObjectShell
LOSSLESSLY — the shell conforms, the original is preserved verbatim (rehydratable), and the migration is recorded in
lineage. Distillation is never replacement. Table-driven: ONE sample per conformed family; the proof + the manifest
stay in lock-step (a family marked `conformed` in _repos/shared-backend-components/architecture/object_shell_migration.json MUST have a passing sample
here — "conformed" can never be claimed without a lossless proof).

Per conformed family asserts:
  A. CONFORMS: migrate_to_shell produces an object carrying ALL ObjectShell required sections + the right object_type/id.
  B. LOSSLESS ROUND-TRIP: rehydrate(shell) == the original (byte-identical; original lives in payload, never overwritten).
  C. INTEGRITY + HANDLES: the shell keeps the artifact's content_hash; derived_from -> source_handles + relationships.
  D. LINEAGE: migrated_from + original_preserved=true + original_payload_hash (auditable + reversible).
  E. CANONICAL BUILDER + CANDIDATE: reuses compose_object_shell; status is CANDIDATE (a wrapper asserts no truth).
  G. DETERMINISM: same input + now -> identical shell.
Cross-family:
  F. MANIFEST LOCK-STEP: every family marked `conformed` in the manifest is tested here (none conformed without a
     passing sample), and no family is silently dropped — every manifest family is conformed or honest backlog. An
     empty backlog is the terminal complete state (all families migrated), not a failure.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.io import object_shell_migration as M
from src.teleon.templates import instantiator as TPL

_NOW = "2026-06-05T00:00:00Z"

#: ONE representative sample per CONFORMED family — {object_type: (id_field, source_schema, sample)}.
#: To conform a new family: flip its manifest status to `conformed` AND add a sample row here (the proof enforces both).
_SAMPLES: dict[str, tuple[str, str, dict]] = {
    "ContextArtifact": ("context_artifact_id", "schemas/context-artifact.schema.json", {
        "kind": "context_artifact", "context_artifact_id": "ctxart_demo_001", "artifact_type": "context_pack",
        "derived_from": ["ctx://acme/source/BILL-782", "ctx://acme/decisions/ADR-014"],
        "content_uri": "ctx://acme/packs/ctxart_demo_001", "content_hash": "sha256:deadbeef" + "0" * 56,
        "token_count": 412, "generator": "context_compress@v1", "lineage_event_id": "lev_777",
        "policy": {"visibility": "internal", "retention_class": "standard"}, "created_at": "2026-06-01T00:00:00Z",
    }),
    "SkillArtifact": ("skill_artifact_id", "OpenSkillsHub:SkillArtifact@logical", {
        "kind": "skill_artifact", "skill_artifact_id": "skill_reconcile_dates_001", "skill_name": "reconcile_dates",
        "version": "v1", "derived_from": ["skill://openskillshub/reconcile_dates", "ctx://acme/decisions/ADR-014"],
        "content_hash": "sha256:beadfeed" + "1" * 56, "steps": ["parse", "normalize", "compare", "emit"],
        "inputs_schema": "InputDates", "outputs_schema": "ReconcileResult",
        "policy": {"visibility": "internal", "executable": "gated_through_sandbox"}, "created_at": "2026-06-02T00:00:00Z",
    }),
    "ToolArtifact": ("tool_artifact_id", "OpenToolsHub:ToolArtifact@logical", {
        "kind": "tool_artifact", "tool_artifact_id": "tool_ofac_lookup_001", "tool_name": "ofac_sanctions_lookup",
        "version": "v1", "transport": "mcp", "api_style": "mcp_tool",
        "derived_from": ["tool://opentoolshub/ofac_sanctions_lookup", "ctx://acme/source/SANCTIONS"],
        "content_hash": "sha256:cafef00d" + "2" * 56, "inputs_schema": "LookupQuery", "outputs_schema": "LookupResult",
        "policy": {"visibility": "internal", "executable": "gated_through_sandbox", "side_effects": "read_only"},
        "created_at": "2026-06-03T00:00:00Z",
    }),
    "HarnessArtifact": ("harness_artifact_id", "OpenHubForAI:HarnessArtifact@logical", {
        "kind": "harness_artifact", "harness_artifact_id": "harness_source_handle_preservation_001",
        "harness_name": "source_handle_preservation", "version": "v1",
        "derived_from": ["harness://openhubforai/source_handle_preservation", "rubric://openhubforai/handle_validity"],
        "content_hash": "sha256:f00dface" + "3" * 56, "proves": "source handles survive compression/optimization",
        "rubric_refs": ["handle_validity", "source_recall"], "fixtures": ["cfpb_context_pack.fixture"],
        "result_is_truth": False, "promotion_authority": False,
        "policy": {"visibility": "internal", "executable": "gated_through_sandbox"}, "created_at": "2026-06-04T00:00:00Z",
    }),
    "TemplateArtifact": ("template_artifact_id", "SharedTemplateRegistry:TemplateArtifact@logical", {
        "kind": "template_artifact", "template_artifact_id": "tmpl_purpose_task_shell_001",
        "template_name": "purpose_task_object_shell", "version": "v1", "template_kind": "schema_object_template",
        "derived_from": ["template://shared/canonical_object_shell", "mixin://shared/provenance", "mixin://shared/policy"],
        "content_hash": "sha256:abad1dea" + "4" * 56, "section_count": 14, "mixin_ids": ["provenance", "policy", "security", "receipts"],
        "generates": "a CANDIDATE object shell (never active/truth)",
        "policy": {"visibility": "internal", "instantiates": "candidate_shapes_only"}, "created_at": "2026-06-05T00:00:00Z",
    }),
    "BenchmarkArtifact": ("benchmark_artifact_id", "OpenBenchmarkHub:BenchmarkArtifact@logical", {
        "kind": "benchmark_artifact", "benchmark_artifact_id": "bench_cfpb_context_governance_001",
        "benchmark_name": "cfpb_context_governance", "version": "v1", "benchmark_family": "context_governance",
        "derived_from": ["benchmark://openbenchmarkhub/cfpb_context_governance", "ctx://acme/source/REG-E"],
        "content_hash": "sha256:0ddba11c" + "5" * 56, "metric": "served_answer_correctness + held_out_preserved",
        "expected": {"served": "10 business days", "held_out": "30 days"},
        "result_is_truth": False, "promotion_authority": False,
        "policy": {"visibility": "internal", "note": "benchmark result is EVIDENCE, not promotion authority"},
        "created_at": "2026-06-06T00:00:00Z",
    }),
    "RepoIntelClassifier": ("repo_intel_id", "GitHubSignalFlywheel:RepoIntelClassifier@logical", {
        "kind": "repo_intel_classifier", "repo_intel_id": "repointel_owl_2026w23_001", "repo_ref": "github.com/example/owl",
        "version": "v1", "derived_from": ["repo-snapshot://github/example_owl@2026-06-01", "snapshot://stars_weekly"],
        "content_hash": "sha256:5113dea1" + "6" * 56, "classification": "candidate", "status_code": 200,
        "stars_snapshot": 18400, "discovery_is_trust": False, "stars_are_proof": False, "trend_is_fit": False,
        "proof_to_promote": "must pass eval/redteam/promotion before active",
        "policy": {"visibility": "internal", "intake": "candidate_never_auto_active"}, "created_at": "2026-06-06T00:00:00Z",
    }),
    "PurposeTaskRun": ("purpose_task_run_id", "Teleon:PurposeTaskRun@logical", {
        "kind": "purpose_task_run", "purpose_task_run_id": "ptr_reconcile_dates_2026w23_001",
        "task_id": "ptask_reconcile_dates_001", "capability_slot": "reconcile_dates",
        "runtime_class": "local_function", "backend": "local_emulator", "is_local_fallback": True,
        "candidate_impl_id": "impl_reconcile_dates_v3",
        "derived_from": ["ptask://teleon/ptask_reconcile_dates_001", "impl://teleon/impl_reconcile_dates_v3",
                         "runtimeclass://teleon/local_function"],
        "content_hash": "sha256:7a5e600d" + "7" * 56,
        "evidence_refs": ["evidence://teleon/run/ptr_reconcile_dates_2026w23_001/ledger"],
        "scorecard_refs": ["scorecard://openhubforai/source_handle_preservation@v1"],
        "result_ref": "result://teleon/run/ptr_reconcile_dates_2026w23_001",
        "promotion_status": "candidate", "promoted": False, "result_is_truth": False,
        "safety_class": "bounded", "tenant_scope": "tenant_private",
        "policy": {"visibility": "internal", "promotion": "eval_gated_human_approved"},
        "created_at": "2026-06-07T00:00:00Z",
    }),
    "ModelInvocationReceipt": ("receipt_id", "schemas/inference/ModelInvocationReceipt.schema.json", {
        "schema_version": "ModelInvocationReceipt", "kind": "model_invocation_receipt",
        "receipt_id": "llmrcpt_reconcile_2026w23_001", "request_id": "llmreq_reconcile_2026w23_001",
        "object_id": "ctxart_demo_001", "preference_id": "pref_reconcile_dates_v1", "requested_model_class": "balanced",
        "selected_provider_node_id": "model.local_stub@v1", "selected_model": "local-stub@v1", "selected_region": "local",
        "fallback_used": True, "fallback_reason_codes": ["live_call_not_provisioned_in_this_environment"],
        "rejected_candidates": [{"node_id": "model.hosted_frontier@v1", "reason_code": "requires_network_disabled"}],
        "input_hash": "sha256:" + "a" * 64, "output_hash": "sha256:" + "b" * 64, "prompt_template_hash": "sha256:" + "c" * 64,
        "config_version": "inference_router_config@v1", "tokens": {"input": 41, "output": 12},
        "cost_estimate_usd": 0.0, "latency_ms": 3,
        "policy_checks": {"data_policy_passed": True, "budget_policy_passed": True, "fallback_policy_passed": True,
                          "no_raw_secret": True, "llm_output_is_truth": False},
        "allowed_use": "candidate",
        "derived_from": ["inferencerequest://teleon/llmreq_reconcile_2026w23_001",
                         "resolvedpreference://teleon/pref_reconcile_dates_v1",
                         "providernode://teleon/model.local_stub@v1"],
        "content_hash": "sha256:9c0ffee5" + "9" * 56,
        "policy": {"visibility": "internal", "secrets": "by_reference_only"}, "created_at": "2026-06-07T00:00:00Z",
    }),
    "SandboxRunResult": ("run_id", "schemas/sandbox/SandboxRunResult.schema.json", {
        "schema_version": "SandboxRunResult", "kind": "sandbox_run_result",
        "run_id": "sbxrun_reconcile_dates_2026w23_001", "provider_id": "sandbox.local_golden@v1",
        "status": "ok", "exit_code": 0, "output_contract_valid": True,
        "policy_violations": [], "secrets_leaked": False, "network_events": [], "duration_ms": 42, "cost_estimate": 0.0,
        "stdout_hash": "sha256:" + "d" * 64, "stderr_hash": "sha256:" + "e" * 64,
        "stdout_sample": "reconciled 1 date; 0 conflicts",
        "receipt_id": "sbxrcpt_reconcile_dates_2026w23_001",
        "is_truth": False, "promoted": False, "allowed_use": "candidate",
        "derived_from": ["sandboxrunrequest://teleon/sbxrun_reconcile_dates_2026w23_001",
                         "sandboxpolicy://teleon/default", "provider://teleon/sandbox.local_golden@v1"],
        "content_hash": "sha256:5a4d6033" + "5" * 56,
        "policy": {"visibility": "internal", "secrets": "by_reference_only"}, "created_at": "2026-06-07T00:00:00Z",
    }),
    "EvaluationScorecard": ("eval_id", "OpenHubForAI:EvaluationScorecard@logical", {
        "kind": "evaluation_scorecard", "schema_version": "EvaluationScorecard",
        "eval_id": "eval_source_handle_preservation_2026w23_001",
        "harness_ref": "harness://openhubforai/source_handle_preservation@v1",
        "system_under_test": "ctxpack://acme/packs/ctxart_demo_001 + impl://teleon/impl_reconcile_dates_v3",
        "derived_from": ["harness://openhubforai/source_handle_preservation@v1",
                         "ctxpack://acme/packs/ctxart_demo_001", "impl://teleon/impl_reconcile_dates_v3"],
        "content_hash": "sha256:e7a1c0de" + "e" * 56,
        "scorecard": {"source_recall": 5, "handle_validity": 5, "claim_correctness": 4,
                      "contradiction_detection": 5, "freshness": 4, "token_efficiency": 4},
        "scale": "0-5", "aggregate": 4.5,
        "result_is_truth": False, "promotion_authority": False, "promoted": False, "allowed_use": "candidate",
        "policy": {"visibility": "internal", "note": "a passing eval is EVIDENCE, not promotion authority"},
        "created_at": "2026-06-07T00:00:00Z",
    }),
}


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    shell_schema = json.loads((_resource("schemas") / "shared" / "ObjectShell.schema.json").read_text())
    required = shell_schema["required"]

    for otype, (id_field, source_schema, sample) in _SAMPLES.items():
        shell = M.migrate_to_shell(sample, object_type=otype, id_field=id_field, source_schema=source_schema, now=_NOW)
        missing = [k for k in required if k not in shell]
        check(f"A[{otype}]: shell carries ALL ObjectShell required sections + right type/id",
              not missing and shell["object_type"] == otype and shell["object_id"] == sample[id_field], f"missing {missing}")
        check(f"B[{otype}]: LOSSLESS round-trip — rehydrate(shell) == original (byte-identical)", M.rehydrate(shell) == sample)
        check(f"C[{otype}]: content_hash preserved + derived_from -> source_handles + relationships",
              shell["content_hash"] == sample["content_hash"] and shell["source_handles"] == sample["derived_from"]
              and [r["ref"] for r in shell["relationships"]] == sample["derived_from"])
        lin = shell.get("lineage", {})
        check(f"D[{otype}]: lineage records the migration (migrated_from + original_preserved + payload hash)",
              lin.get("migrated_from") == source_schema and lin.get("original_preserved") is True
              and lin.get("original_payload_hash") == TPL._content_hash(sample))
        check(f"E[{otype}]: reuses canonical builder + CANDIDATE status (wrapper asserts no truth)",
              shell["status_code"] == TPL.CANDIDATE_STATUS and shell["schema_version"] == "v1")
        check(f"G[{otype}]: deterministic (same input+now -> identical shell)",
              json.dumps(M.migrate_to_shell(sample, object_type=otype, id_field=id_field, source_schema=source_schema, now=_NOW), sort_keys=True)
              == json.dumps(shell, sort_keys=True))

    man = json.loads((_resource("architecture") / "object_shell_migration.json").read_text())
    all_families = {f["object_type"] for f in man["families"]}
    conformed = {f["object_type"] for f in man["families"] if f["status"] == "conformed"}
    backlog = {f["object_type"] for f in man["families"] if f["status"] == "backlog"}
    check("F: manifest lock-step — conformed families exactly match the tested samples (none conformed without a passing sample)",
          conformed == set(_SAMPLES), f"manifest conformed={sorted(conformed)} tested={sorted(_SAMPLES)}")
    check("F: no family silently dropped — every manifest family is conformed (with a sample) or honest backlog (empty backlog = migration complete)",
          (conformed | backlog) == all_families and not (set(_SAMPLES) - all_families),
          f"unaccounted={sorted(all_families - (conformed | backlog))} extra_samples={sorted(set(_SAMPLES) - all_families)}")

    print("\n" + (f"PASS — check_object_shell_conformance_migration: {len(_SAMPLES)} families "
                  f"({', '.join(sorted(_SAMPLES))}) migrate to ObjectShell losslessly — all required sections, "
                  "originals preserved verbatim (rehydratable), content_hash + handles carried, migration recorded in "
                  "lineage, canonical builder reused (candidate status); manifest stays lock-step with the proof "
                  f"({len(conformed)} conformed, {len(backlog)} backlog)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_object_shell_conformance_migration.py --self-test")
    raise SystemExit(0)
