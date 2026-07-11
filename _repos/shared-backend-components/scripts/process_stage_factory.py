#!/usr/bin/env python3
"""scripts.process_stage_factory — the PROCESS is a primitive factory (2026-07-08). Most enterprise data/ML
work follows a standard ~18-stage lifecycle (research -> source -> access -> ingest -> profile -> validate ->
standardize -> ETL -> label -> split -> feature -> train -> evaluate -> package -> deploy -> monitor -> drift/
retrain -> audit; CRISP-DM / TDSP / TFX all agree on the skeleton). The SCAFFOLD is highly standardizable; the
VARIABLE part is local policy + domain semantics — the canonical -> variant -> delta split. This factory mints
a governed ProcessStep primitive per stage (executor + validator + verifier + RECEIPT + lineage event, typed by
input/output ARTIFACT), the first-class process ARTIFACT types, and reusable process TEMPLATES (pipeline DAGs).

Answers "how much follows standard steps": each stage carries a `standardization_potential` (very_high..low) —
artifact movement + pipeline control-flow + validation + evaluation + deployment are very-high/high; research
judgment + business thresholds are the low/variable part. Every ProcessStep is candidate/serves_truth=false,
needs_executor (a governed SPEC), with the determinism budget honest per stage (profile/validate/evaluate D0;
deploy D2 external; research/label D3-D4 judgment). Data seam: a new stage/artifact/template = one row.

    python3 scripts/process_stage_factory.py --self-test
    python3 scripts/process_stage_factory.py --report   # the standardizability answer, computed
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"process_stage_factory requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-proc"
FACTORY_VERSION = "process-stage-factory-v1"
#: every ProcessStep emits these receipts (the evidence trail — owner §3)
STEP_RECEIPTS = ("run_receipt", "quality_receipt", "lineage_receipt")

# ── the standard lifecycle: (stage, family, in_artifacts, out_artifacts, determinism, standardization) ────────
#: standardization potential: very_high | high | high_medium | medium | low_medium | low (owner §2 table)
PIPELINE_STAGES: tuple[tuple[str, str, list[str], list[str], str, str], ...] = (
    ("research", "problem_framing", ["BusinessObjective"],
     ["ResearchQuestion", "MetricDefinition", "AcceptanceCriteria"], "D4_stochastic", "low_medium"),
    ("source_discovery", "acquisition", ["ResearchQuestion"], ["SourceManifest", "DataContract"],
     "D1_seeded", "high"),
    ("access", "acquisition", ["SourceManifest"], ["AccessGrant"], "D1_seeded", "high"),
    ("ingest", "loading", ["AccessGrant", "SourceManifest"], ["RawDataset", "IngestionManifest",
     "SchemaFingerprint"], "D0_pure", "very_high"),
    ("profile", "data_understanding", ["RawDataset"], ["DataProfileReport", "ColumnProfile"], "D0_pure",
     "high"),
    ("quality_validate", "validation", ["RawDataset", "DataProfileReport"], ["ExpectationSuite",
     "ValidationResult", "QualityGateDecision"], "D0_pure", "high"),
    ("standardize", "standardization", ["ValidationResult", "RawDataset"], ["StandardizedDataset",
     "StandardizationMap", "MatchKey"], "D0_pure", "high"),
    ("transform_etl", "transformation", ["StandardizedDataset"], ["CuratedDataset", "TransformGraph",
     "LineageGraph"], "D1_seeded", "high_medium"),
    ("label", "labeling", ["CuratedDataset"], ["LabelDefinition", "LabelSet", "LabelQualityReport"],
     "D3_hybrid", "medium"),
    ("split", "splitting", ["CuratedDataset", "LabelSet"], ["SplitPlan", "CrossValidationPlan",
     "LeakageRiskReport"], "D1_seeded", "high"),
    ("feature", "feature_engineering", ["CuratedDataset", "SplitPlan"], ["FeatureDefinition", "FeatureSet",
     "FeatureLineage"], "D1_seeded", "medium"),
    ("train", "training", ["FeatureSet", "SplitPlan"], ["TrainingRun", "ModelCandidate", "TrainingReceipt"],
     "D1_seeded", "medium"),
    ("evaluate", "evaluation", ["ModelCandidate", "SplitPlan"], ["EvaluationReport", "SliceReport",
     "ModelBlessing"], "D0_pure", "high"),
    ("package", "packaging", ["ModelBlessing", "ModelCandidate"], ["ModelArtifact", "ModelCard", "SBOM",
     "ProvenanceReceipt"], "D0_pure", "high"),
    ("deploy", "serving", ["ModelArtifact", "ServingContract"], ["DeploymentPlan", "CanaryReport",
     "EndpointHealthReport"], "D2_bounded_external", "high"),
    ("monitor", "operations", ["EndpointHealthReport"], ["MonitoringSignal", "DriftReport"], "D1_seeded",
     "high"),
    ("drift_retrain", "operations", ["DriftReport"], ["RetrainingDecision", "IncidentRecord"], "D1_seeded",
     "medium"),
    ("audit", "governance", ["ProvenanceReceipt", "EvaluationReport"], ["AuditPacket"], "D0_pure", "high"),
)
#: reusable process TEMPLATES (pipeline DAGs over stages) — owner §7
PROCESS_TEMPLATES: dict[str, list[str]] = {
    "tabular_classification_pipeline": ["ingest", "profile", "quality_validate", "standardize", "transform_etl",
                                        "label", "split", "feature", "train", "evaluate", "package", "deploy",
                                        "monitor"],
    "time_series_forecasting_pipeline": ["ingest", "profile", "quality_validate", "standardize", "feature",
                                         "split", "train", "evaluate", "package", "deploy", "monitor"],
    "entity_resolution_pipeline": ["ingest", "profile", "standardize", "transform_etl", "feature", "evaluate",
                                   "audit"],
    "reconciliation_pipeline": ["ingest", "quality_validate", "standardize", "transform_etl", "evaluate",
                                "audit"],
    "document_extraction_pipeline": ["ingest", "profile", "standardize", "label", "evaluate", "package",
                                     "deploy", "monitor"],
    "rag_pipeline": ["ingest", "standardize", "feature", "evaluate", "deploy", "monitor"],
}
_SENSITIVE_STAGES = frozenset({"label", "deploy", "audit"})


def _step_card(stage: str, family: str, ins: list[str], outs: list[str], determinism: str,
               standardization: str) -> dict[str, Any]:
    return {
        "primitive_id": canonical_id(CARD_PREFIX, f"stage.{stage}", family),
        "impl_name": f"process_step.{stage}", "record_type": "process_step_primitive",
        "kind": "primitive_spec", "title": f"ProcessStep: {stage}", "process_stage": stage,
        "step_family": family, "input_edge": ins[0] if ins else "None", "output_edge": outs[0] if outs else "None",
        "input_artifacts": ins, "output_artifacts": outs,
        # the ProcessStep shape (owner §3): executor + validator + verifier + receipt + lineage
        "executor": f"{stage}_executor", "validator": f"{stage}_validator", "verifier": f"{stage}_verifier",
        "receipts": list(STEP_RECEIPTS), "lineage_event": f"openlineage_{stage}_event",
        "standardization_potential": standardization,
        # governance (candidate spec awaiting executor; determinism honest per stage)
        "execution_model": "compiled_workflow", "determinism_level": determinism,
        "lifecycle_stage": "candidate", "needs_executor": True,
        "permission_manifest": {"permission_class": "network egress" if determinism == "D2_bounded_external"
                                else "pure", "side_effect_free": determinism.startswith("D0"),
                                "network_access": determinism == "D2_bounded_external", "security_flags": []},
        "risk_tier": "review required" if (stage in _SENSITIVE_STAGES or determinism in ("D3_hybrid",
                     "D4_stochastic", "D2_bounded_external")) else "safe",
        "verifier_id": "process_stage_factory::_self_test", "verifier_kind": "spec + receipt",
        "marginal_utility_evidence": {"status": "unmeasured", "lift": None},
        "artifact_hash": canonical_id("artifact", f"stage.{stage}", FACTORY_VERSION),
        "provenance": {"contract_version": FACTORY_VERSION, "reference_models": ["CRISP-DM", "TDSP", "TFX"]},
        "promotion_receipts": {}, "retrieval_tags": sorted({"process_step", family, stage, determinism,
                               standardization, "candidate", *ins, *outs}),
        "never_final_adverse_decision": stage in ("label", "audit"),
        "blackbox": f"ProcessStep '{stage}' ({family}): {ins} -> {outs}. Executor+validator+verifier+receipts"
                    f"{list(STEP_RECEIPTS)}+lineage. Determinism {determinism}; standardization potential "
                    f"{standardization}. Candidate spec awaiting executor.", "tier": "process", **BOUNDARY}


def _artifact_card(name: str) -> dict[str, Any]:
    return {"primitive_id": canonical_id(CARD_PREFIX, f"artifact.{name}", FACTORY_VERSION),
            "impl_name": f"process_artifact.{name}", "record_type": "process_artifact_type",
            "kind": "artifact_type", "title": f"Artifact: {name}", "artifact_name": name,
            "provenance": {"contract_version": FACTORY_VERSION}, "retrieval_tags": ["process_artifact", name],
            "tier": "process", **BOUNDARY}


def _template_card(name: str, stages: list[str]) -> dict[str, Any]:
    return {"primitive_id": canonical_id(CARD_PREFIX, f"template.{name}", FACTORY_VERSION),
            "impl_name": f"process_template.{name}", "record_type": "process_template",
            "kind": "primitive_group", "title": f"Process template: {name}", "stages": stages,
            "plan_steps": [f"process_step.{s}" for s in stages], "execution_model": "compiled_workflow",
            "lifecycle_stage": "candidate", "needs_executor": True,
            "provenance": {"contract_version": FACTORY_VERSION}, "retrieval_tags": sorted({"process_template",
                           name, *stages}), "tier": "process", **BOUNDARY}


def all_cards() -> list[dict[str, Any]]:
    steps = [_step_card(*s) for s in PIPELINE_STAGES]
    artifacts = sorted({a for s in PIPELINE_STAGES for a in (s[2] + s[3])})
    return steps + [_artifact_card(a) for a in artifacts] + [_template_card(n, st)
                                                             for n, st in PROCESS_TEMPLATES.items()]


def standardization_report() -> dict[str, Any]:
    """The computed answer to 'how much follows standard steps'."""
    dist: dict[str, int] = {}
    for s in PIPELINE_STAGES:
        dist[s[5]] = dist.get(s[5], 0) + 1
    high = sum(dist.get(k, 0) for k in ("very_high", "high"))
    return {"record_type": "process_standardizability_report", "n_stages": len(PIPELINE_STAGES),
            "standardization_distribution": dict(sorted(dist.items())),
            "high_or_very_high_stages": high, "of_total": len(PIPELINE_STAGES),
            "n_artifact_types": len({a for s in PIPELINE_STAGES for a in (s[2] + s[3])}),
            "n_templates": len(PROCESS_TEMPLATES),
            "conclusion": f"{high}/{len(PIPELINE_STAGES)} lifecycle stages are high/very-high standardizable "
                          "SCAFFOLD; research judgment + labeling + thresholds are the variable POLICY part — "
                          "the canonical->variant->delta split. The scaffold is the reusable primitive; the "
                          "policy/domain/geography/system/tenant is the delta.", **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = all_cards()
    steps = [c for c in cards if c["record_type"] == "process_step_primitive"]
    by_stage = {c["process_stage"]: c for c in steps}
    checks.append((f"the standard lifecycle: {len(steps)} ProcessStep primitives (research->...->audit)",
                   len(steps) == 18 and by_stage["research"]["step_family"] == "problem_framing"
                   and "audit" in by_stage))
    checks.append(("every ProcessStep has the executor+validator+verifier+receipts+lineage shape + typed "
                   "input/output artifacts",
                   all(c["executor"] and c["validator"] and c["verifier"] and c["receipts"] == list(STEP_RECEIPTS)
                       and c["lineage_event"] and c["input_artifacts"] and c["output_artifacts"] for c in steps)))
    checks.append(("determinism honest per stage: profile/validate/evaluate D0; deploy D2; research D4; label D3",
                   by_stage["profile"]["determinism_level"] == "D0_pure"
                   and by_stage["deploy"]["determinism_level"] == "D2_bounded_external"
                   and by_stage["research"]["determinism_level"] == "D4_stochastic"
                   and by_stage["label"]["determinism_level"] == "D3_hybrid"))
    checks.append(("artifact TYPES minted as first-class primitives (DatasetSnapshot-style records)",
                   any(c["record_type"] == "process_artifact_type" and c["artifact_name"] == "ModelArtifact"
                       for c in cards)
                   and any(c["artifact_name"] == "EvaluationReport" for c in cards
                           if c["record_type"] == "process_artifact_type")))
    tmpl = next(c for c in cards if c["record_type"] == "process_template"
                and c["impl_name"] == "process_template.tabular_classification_pipeline")
    checks.append(("process TEMPLATES are DAGs over stages (plan_steps reference process_steps)",
                   tmpl["plan_steps"][0] == "process_step.ingest" and "process_step.train" in tmpl["plan_steps"]))
    rep = standardization_report()
    checks.append(("standardizability report computed: >=12/18 stages high/very-high; conclusion present",
                   rep["high_or_very_high_stages"] >= 12 and rep["n_stages"] == 18
                   and "canonical->variant->delta" in rep["conclusion"]))
    checks.append(("all candidate/serves_truth=false; ids canonical + unique",
                   all(c["serves_truth"] is False for c in cards)
                   and len({c["primitive_id"] for c in cards}) == len(cards)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    rep = standardization_report()
    print(f"\nPASS - process_stage_factory: {len(steps)} ProcessStep primitives + "
          f"{rep['n_artifact_types']} artifact types + {rep['n_templates']} templates. "
          f"{rep['high_or_very_high_stages']}/{rep['n_stages']} stages high/very-high standardizable scaffold; "
          f"policy/domain is the delta. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--cards", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.report:
        print(json.dumps(standardization_report(), indent=2, sort_keys=True))
        return 0
    if args.cards:
        for c in all_cards():
            print(json.dumps(c, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
