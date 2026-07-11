#!/usr/bin/env python3
"""Generate the source-backed enterprise operating-system primitive atlas.

The atlas turns public, high-level enterprise platform and industry workflow
descriptions into independent, generic primitive candidates. It never claims to
reconstruct a vendor implementation. Every generated row is candidate-only and
every benchmark row is a seed until a starter repo and executed oracle receipt
exist.

The canonical lists live in the source YAML. This module only validates,
normalizes, expands, hashes, and renders them.

    PYTHONPATH=. python3 scripts/generate_enterprise_operating_system_primitive_atlas.py --self-test
    PYTHONPATH=. python3 scripts/generate_enterprise_operating_system_primitive_atlas.py --emit
    PYTHONPATH=. python3 scripts/generate_enterprise_operating_system_primitive_atlas.py --stats
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import yaml

_HERE = Path(__file__).resolve()
_SBC = next(
    (parent for parent in _HERE.parents if (parent / "scripts" / "_repo_paths.py").exists()),
    _HERE.parents[1],
)
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))

from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

from src.teleon.experiments.ids import canonical_id, sha256_hex  # noqa: E402


PACK_SLUG = "enterprise-operating-system-primitive-atlas"
PACK_ID = f"knowledge-pack/{PACK_SLUG}"
SOURCE_REL = f"catalog/knowledge-packs/data/{PACK_SLUG}/atlas_source.yaml"
PACK_DIR_REL = f"catalog/knowledge-packs/data/{PACK_SLUG}"
CATALOG_MANIFEST_REL = f"catalog/knowledge-packs/{PACK_SLUG}.yaml"
DOC_REL = f"_repos/shared-backend-components/context/research/{PACK_SLUG}.md"
INDUSTRY_VOCAB_REL = "vocabularies/industries.yaml"

BOUNDARY = {"candidate": True, "serves_truth": False}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_TOKEN_RE = re.compile(r"(?:^|-)(?:v\d+|\d+\.\d+(?:\.\d+)?)(?:-|$)", re.IGNORECASE)
CANONICAL_PRIMITIVES = {"action", "if_statement", "knowledge_corpus", "loop", "output", "stop_end", "input"}
SOURCE_CLASSES = {"A", "B", "C"}

OUTPUT_FILES = {
    "source_records": "source_records.jsonl",
    "source_evidence_locators": "source_evidence_locators.jsonl",
    "tool_classes": "tool_classes.jsonl",
    "system_adapters": "system_adapters.jsonl",
    "primitive_templates": "primitive_templates.jsonl",
    "systems": "systems.jsonl",
    "business_workflows": "business_workflows.jsonl",
    "workflow_primitive_bindings": "workflow_primitive_bindings.jsonl",
    "primitive_proof_plans": "primitive_proof_plans.jsonl",
    "project_archetypes": "project_archetypes.jsonl",
    "benchmark_bindings": "benchmark_bindings.jsonl",
}


class AtlasValidationError(ValueError):
    """Raised when the curated source violates a structural or safety invariant."""


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AtlasValidationError(f"expected YAML object at {path}")
    return data


def load_source() -> dict[str, Any]:
    """Load the single source of truth for atlas lists and mappings."""
    return _read_yaml(resource(SOURCE_REL))


def _industry_ids() -> set[str]:
    data = _read_yaml(resource(INDUSTRY_VOCAB_REL))
    ids: set[str] = set()
    for row in data.get("industries", []):
        ids.add(str(row["id"]))
        ids.update(str(child["id"]) for child in row.get("sub", []))
    return ids


def _unique_map(rows: Iterable[dict[str, Any]], label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = str(row.get("id", ""))
        if not row_id:
            errors.append(f"{label} row missing id")
            continue
        if row_id in result:
            errors.append(f"duplicate {label} id: {row_id}")
        result[row_id] = row
    return result


def _check_slug(value: str, label: str, errors: list[str]) -> None:
    if not SLUG_RE.fullmatch(value):
        errors.append(f"{label} must be a lowercase dash slug: {value}")
    if len(value) > 64:
        errors.append(f"{label} exceeds 64 chars: {value}")
    if VERSION_TOKEN_RE.search(value):
        errors.append(f"{label} must not contain a version token: {value}")


def _expanded_primitive_bindings(
    system: dict[str, Any],
    workflow: dict[str, Any],
    bundles: dict[str, list[str]],
    operation_bindings: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Resolve route membership while separating required steps from cross-cutting support.

    A binding is a dependency/composition edge, never a new primitive identity.
    Workflow bundles, explicit primitives, and operation mappings are required;
    system-default bundles are cross-cutting support unless upgraded by a required source.
    """
    by_template: dict[str, dict[str, Any]] = {}

    def add(template_ids: Iterable[str], role: str, origin: str) -> None:
        for template_id in template_ids:
            template_id = str(template_id)
            current = by_template.setdefault(
                template_id,
                {"primitive_template_id": template_id, "role": "cross_cutting", "origins": []},
            )
            if role == "required":
                current["role"] = "required"
            if origin not in current["origins"]:
                current["origins"].append(origin)

    for bundle_id in system.get("default_bundles", []):
        add(bundles.get(str(bundle_id), []), "cross_cutting", f"system_bundle:{bundle_id}")
    for bundle_id in workflow.get("bundles", []):
        add(bundles.get(str(bundle_id), []), "required", f"workflow_bundle:{bundle_id}")
    add(workflow.get("primitives", []), "required", "workflow_explicit")
    operation = str(workflow.get("operation", ""))
    add(operation_bindings.get(operation, []), "required", f"operation:{operation}")
    return [by_template[key] for key in sorted(by_template)]


def _expanded_primitive_ids(
    system: dict[str, Any],
    workflow: dict[str, Any],
    bundles: dict[str, list[str]],
    operation_bindings: dict[str, list[str]],
) -> list[str]:
    return [
        row["primitive_template_id"]
        for row in _expanded_primitive_bindings(system, workflow, bundles, operation_bindings)
    ]


def validate_source(data: dict[str, Any], *, validate_manifest: bool = False) -> None:
    """Validate references, safety boundaries, vocabulary membership, and floors."""
    errors: list[str] = []
    required = {
        "schema_version",
        "evidence_snapshot_date",
        "scope",
        "quality_floors",
        "adapter_contract",
        "default_error_semantics",
        "workflow_operation_bindings",
        "sources",
        "tool_classes",
        "primitive_templates",
        "bundles",
        "oracle_patterns",
        "primitive_oracle_patterns",
        "project_archetypes",
        "system_families",
    }
    missing = sorted(required - set(data))
    if missing:
        errors.append(f"missing top-level keys: {missing}")

    sources = _unique_map(data.get("sources", []), "source", errors)
    tools = _unique_map(data.get("tool_classes", []), "tool class", errors)
    templates = _unique_map(data.get("primitive_templates", []), "primitive template", errors)
    systems = _unique_map(data.get("system_families", []), "system family", errors)
    bundles = {str(key): [str(item) for item in value] for key, value in data.get("bundles", {}).items()}
    operation_bindings = {
        str(key): [str(item) for item in value]
        for key, value in data.get("workflow_operation_bindings", {}).items()
    }
    oracles = data.get("oracle_patterns", {})
    primitive_oracles = data.get("primitive_oracle_patterns", {})
    projects = set(str(item) for item in data.get("project_archetypes", []))
    industries = _industry_ids()

    for label, mapping in (
        ("source", sources),
        ("tool class", tools),
        ("primitive template", templates),
        ("system family", systems),
        ("bundle", bundles),
    ):
        for row_id in mapping:
            _check_slug(row_id, label, errors)

    for source in sources.values():
        if source.get("source_class") not in SOURCE_CLASSES:
            errors.append(f"source {source['id']} has invalid class {source.get('source_class')}")
        if not str(source.get("url", "")).startswith("https://"):
            errors.append(f"source {source['id']} must use an https URL")

    referenced_sources = {
        str(source_id)
        for system in systems.values()
        for source_id in system.get("source_refs", [])
    }
    unused_sources = sorted(
        source_id
        for source_id, source in sources.items()
        if source_id not in referenced_sources and not source.get("background_only")
    )
    if unused_sources:
        errors.append(f"sources are neither referenced nor marked background_only: {unused_sources}")

    for template in templates.values():
        missing_fields = [
            field
            for field in (
                "layer",
                "operation",
                "object",
                "input",
                "output",
                "invariants",
                "effects",
                "determinism",
                "oracle",
                "primitive",
            )
            if field not in template
        ]
        if missing_fields:
            errors.append(f"primitive template {template['id']} missing {missing_fields}")
        if template.get("primitive") not in CANONICAL_PRIMITIVES:
            errors.append(f"primitive template {template['id']} has invalid canonical primitive")
        if not template.get("invariants"):
            errors.append(f"primitive template {template['id']} must declare invariants")
        if template.get("oracle") not in primitive_oracles:
            errors.append(f"primitive template {template['id']} references unknown atomic oracle")

    for bundle_id, primitive_ids in bundles.items():
        if not primitive_ids:
            errors.append(f"bundle {bundle_id} is empty")
        unknown = sorted(set(primitive_ids) - set(templates))
        if unknown:
            errors.append(f"bundle {bundle_id} references unknown templates {unknown}")

    for operation, primitive_ids in operation_bindings.items():
        unknown = sorted(set(primitive_ids) - set(templates))
        if unknown:
            errors.append(f"operation binding {operation} references unknown templates {unknown}")

    workflow_ids: set[str] = set()
    excluded_domains = {str(item).lower() for item in data.get("scope", {}).get("excluded_domains", [])}
    floors = data.get("quality_floors", {})
    for system in systems.values():
        system_text = json.dumps(system, sort_keys=True).lower()
        if any(domain in system_text for domain in excluded_domains):
            errors.append(f"system {system['id']} violates excluded domain policy")
        unknown_sources = sorted(set(system.get("source_refs", [])) - set(sources))
        if unknown_sources:
            errors.append(f"system {system['id']} references unknown sources {unknown_sources}")
        unknown_tools = sorted(set(system.get("tool_classes", [])) - set(tools))
        if unknown_tools:
            errors.append(f"system {system['id']} references unknown tool classes {unknown_tools}")
        unknown_industries = sorted(set(system.get("industries", [])) - industries)
        if unknown_industries:
            errors.append(f"system {system['id']} uses unknown industries {unknown_industries}")
        unknown_default_bundles = sorted(set(system.get("default_bundles", [])) - set(bundles))
        if unknown_default_bundles:
            errors.append(f"system {system['id']} references unknown bundles {unknown_default_bundles}")
        workflows = system.get("workflows", [])
        if len(workflows) < int(floors.get("min_workflows_per_system", 0)):
            errors.append(f"system {system['id']} is below workflow floor")
        for workflow in workflows:
            workflow_id = str(workflow.get("id", ""))
            _check_slug(workflow_id, "workflow", errors)
            if workflow_id in workflow_ids:
                errors.append(f"duplicate workflow id: {workflow_id}")
            workflow_ids.add(workflow_id)
            if workflow.get("evidence_relation", "inferred_extension") not in {
                "explicit",
                "inferred_extension",
                "synthetic_gap",
            }:
                errors.append(f"workflow {workflow_id} has invalid evidence_relation")
            unknown_workflow_bundles = sorted(set(workflow.get("bundles", [])) - set(bundles))
            if unknown_workflow_bundles:
                errors.append(f"workflow {workflow_id} references unknown bundles {unknown_workflow_bundles}")
            operation = str(workflow.get("operation", ""))
            if operation not in operation_bindings:
                errors.append(f"workflow {workflow_id} operation lacks a binding rule: {operation}")
            bindings = _expanded_primitive_bindings(system, workflow, bundles, operation_bindings)
            expanded = [row["primitive_template_id"] for row in bindings]
            unknown_templates = sorted(set(expanded) - set(templates))
            if unknown_templates:
                errors.append(f"workflow {workflow_id} references unknown templates {unknown_templates}")
            required_count = sum(row["role"] == "required" for row in bindings)
            if required_count < int(floors.get("min_required_bindings_per_workflow", 0)):
                errors.append(f"workflow {workflow_id} is below required-binding floor")
            oracle_id = str(workflow.get("oracle", ""))
            if oracle_id not in oracles:
                errors.append(f"workflow {workflow_id} references unknown oracle {oracle_id}")
            elif int(str(oracles[oracle_id].get("strength", "O0"))[1:]) < 5:
                errors.append(f"workflow {workflow_id} oracle must target O5+")
            if workflow.get("project") not in projects:
                errors.append(f"workflow {workflow_id} references unknown project archetype")

    if len(systems) < int(floors.get("min_system_families", 0)):
        errors.append("system family count is below source-defined floor")
    if len(templates) < int(floors.get("min_primitive_templates", 0)):
        errors.append("primitive template count is below source-defined floor")
    if len({str(source.get("source_class")) for source in sources.values()}) < int(
        floors.get("min_source_classes", 0)
    ):
        errors.append("source-class diversity is below source-defined floor")

    if validate_manifest:
        manifest_path = resource(CATALOG_MANIFEST_REL)
        if not manifest_path.exists():
            errors.append(f"catalog manifest missing: {manifest_path}")
        else:
            manifest = _read_yaml(manifest_path)
            if manifest.get("id") != PACK_ID:
                errors.append("catalog manifest id does not match generator PACK_ID")
            declared = {str(row.get("path")) for row in manifest.get("files", [])}
            expected = {f"catalog/knowledge-packs/data/{PACK_SLUG}/{name}" for name in OUTPUT_FILES.values()}
            if not expected <= declared:
                errors.append(f"catalog manifest is missing generated files: {sorted(expected - declared)}")

    if errors:
        raise AtlasValidationError("\n".join(errors))


def _jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)


def _title(slug: str) -> str:
    return slug.replace("-", " ").title()


def _pascal(value: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[-_]", value) if part)


def _system_and_workflow_rows(data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bundles = {str(key): [str(item) for item in value] for key, value in data["bundles"].items()}
    operation_bindings = {
        str(key): [str(item) for item in value]
        for key, value in data["workflow_operation_bindings"].items()
    }
    system_rows: list[dict[str, Any]] = []
    workflow_rows: list[dict[str, Any]] = []
    for system in sorted(data["system_families"], key=lambda row: row["id"]):
        system_rows.append(
            {
                "record_type": "enterprise_system_family",
                "system_id": system["id"],
                "title": system["title"],
                "industries": system["industries"],
                "tool_classes": system["tool_classes"],
                "business_objects": system["business_objects"],
                "source_refs": system["source_refs"],
                "workflow_ids": sorted(workflow["id"] for workflow in system["workflows"]),
                "safety": system.get("safety"),
                "fact_or_inference": "inferred_generic_system_pattern",
                **BOUNDARY,
            }
        )
        for workflow in sorted(system["workflows"], key=lambda row: row["id"]):
            bindings = _expanded_primitive_bindings(system, workflow, bundles, operation_bindings)
            required_ids = [row["primitive_template_id"] for row in bindings if row["role"] == "required"]
            cross_cutting_ids = [
                row["primitive_template_id"] for row in bindings if row["role"] == "cross_cutting"
            ]
            workflow_rows.append(
                {
                    "record_type": "enterprise_business_workflow",
                    "workflow_id": workflow["id"],
                    "system_id": system["id"],
                    "title": workflow["title"],
                    "operation": workflow["operation"],
                    "business_object": workflow["object"],
                    "risk": workflow["risk"],
                    "human_authority_required": workflow["risk"] == "high" or bool(system.get("safety")),
                    "required_primitive_template_ids": required_ids,
                    "cross_cutting_primitive_template_ids": cross_cutting_ids,
                    "oracle_pattern_id": workflow["oracle"],
                    "project_archetype_id": workflow["project"],
                    "source_refs": system["source_refs"],
                    "evidence_relation": workflow.get("evidence_relation", "inferred_extension"),
                    "source_evidence_status": "family_level_breadth_ref_needs_workflow_span_review",
                    "safety": system.get("safety"),
                    **BOUNDARY,
                }
            )
    return system_rows, workflow_rows


def _workflow_binding_rows(workflow_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Emit dependency placements, not new primitive identities."""
    rows: list[dict[str, Any]] = []
    for workflow in workflow_rows:
        for role, field in (
            ("required", "required_primitive_template_ids"),
            ("cross_cutting", "cross_cutting_primitive_template_ids"),
        ):
            for template_id in workflow[field]:
                rows.append(
                    {
                        "record_type": "enterprise_workflow_primitive_binding",
                        "binding_id": canonical_id(
                            "entbinding", workflow["system_id"], workflow["workflow_id"], template_id
                        ),
                        "workflow_id": workflow["workflow_id"],
                        "system_id": workflow["system_id"],
                        "primitive_template_id": template_id,
                        "binding_role": role,
                        "relationship": "requires" if role == "required" else "uses_cross_cutting_support",
                        "business_object_overlay": workflow["business_object"],
                        "authorization_policy": {
                            "human_authority_required": workflow["human_authority_required"],
                            "risk": workflow["risk"],
                            "safety": workflow.get("safety"),
                        },
                        "source_refs": workflow["source_refs"],
                        "evidence_relation": workflow["evidence_relation"],
                        "fact_or_inference": "candidate_composition_binding_not_new_primitive",
                        **BOUNDARY,
                    }
                )
    return rows


def _primitive_proof_plan_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    """One atomic proof plan per canonical template, using the template's oracle."""
    oracle_patterns = data["primitive_oracle_patterns"]
    rows: list[dict[str, Any]] = []
    for template in sorted(data["primitive_templates"], key=lambda row: row["id"]):
        oracle_kind = template["oracle"]
        oracle = oracle_patterns[oracle_kind]
        rows.append(
            {
                "record_type": "enterprise_primitive_proof_plan",
                "proof_plan_id": canonical_id("entproof", template["id"], oracle_kind),
                "primitive_template_id": template["id"],
                "oracle_kind": oracle_kind,
                "execution": oracle["execution"],
                "mutation_probes": oracle["mutations"],
                "required_results": [
                    "known_good_passes",
                    "known_bad_fails",
                    "mutated_candidate_fails",
                    "deterministic_replay_matches",
                    "receipt_readback_matches",
                ],
                "status": "planned_not_executed",
                "headline_eligible": False,
                **BOUNDARY,
            }
        )
    return rows


def _benchmark_rows(data: dict[str, Any], workflow_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    oracles = data["oracle_patterns"]
    rows: list[dict[str, Any]] = []
    for workflow in workflow_rows:
        oracle = oracles[workflow["oracle_pattern_id"]]
        rows.append(
            {
                "record_type": "enterprise_project_benchmark_binding",
                "benchmark_seed_id": canonical_id("entbench", workflow["system_id"], workflow["workflow_id"]),
                "workflow_id": workflow["workflow_id"],
                "system_id": workflow["system_id"],
                "project_archetype_id": workflow["project_archetype_id"],
                "benchmark_kind": "real_project",
                "task_status": "seed_only_needs_starter_repo_and_oracle_implementation",
                "headline_eligible": False,
                "benchmark_result": False,
                "realism_target": oracle["strength"],
                "execution_profile": oracle["execution"],
                "required_artifacts": [
                    "task_contract",
                    "starter_repo",
                    "hidden_tests",
                    "known_good_solution",
                    "known_bad_solution",
                    "setup_build_run_oracle_cleanup_commands",
                    "project_run_receipt",
                ],
                "required_oracle_mutations": oracle["mutations"],
                "ab_lanes": ["harness_alone", "harness_plus_certified_primitives", "compiled_route_reuse"],
                "source_refs": workflow["source_refs"],
                "no_proxy_gate_required": True,
                **BOUNDARY,
            }
        )
    return rows


def _evidence_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for system in data["system_families"]:
        for workflow in system["workflows"]:
            evidence_relation = workflow.get("evidence_relation", "inferred_extension")
            for source_id in system["source_refs"]:
                rows.append(
                    {
                        "record_type": "enterprise_source_evidence_locator",
                        "evidence_id": canonical_id("entevidence", system["id"], workflow["id"], source_id),
                        "system_id": system["id"],
                        "workflow_id": workflow["id"],
                        "source_id": source_id,
                        "locator_kind": "page_scope",
                        "locator": "family-level public page; exact workflow span not yet stored",
                        "quote_stored": False,
                        "evidence_relation": evidence_relation,
                        "fact_or_inference": "family_breadth_support; workflow_mapping_is_inferred",
                        "needs_manual_span_review_before_promotion": True,
                        **BOUNDARY,
                    }
                )
    for source in data["sources"]:
        if source.get("background_only"):
            rows.append(
                {
                    "record_type": "enterprise_source_evidence_locator",
                    "evidence_id": canonical_id("entevidence", "atlas-breadth", source["id"]),
                    "system_id": None,
                    "source_id": source["id"],
                    "locator_kind": "catalog_scope",
                    "locator": "public offering index used only to establish breadth of the research surface",
                    "quote_stored": False,
                    "fact_or_inference": "background_breadth_signal_not_workflow_proof",
                    "needs_manual_span_review_before_promotion": True,
                    **BOUNDARY,
                }
            )
    return rows


def _render_doc(data: dict[str, Any], rows: dict[str, list[dict[str, Any]]], manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    lines = [
        "# Enterprise operating-system primitive atlas",
        "",
        "> GENERATED from `catalog/knowledge-packs/data/enterprise-operating-system-primitive-atlas/atlas_source.yaml`.",
        "> Public examples establish workflow breadth; primitive decompositions are independent candidate inferences.",
        "",
        "## Honest boundary",
        "",
        "This atlas does **not** claim access to every project performed by Palantir or any other company, and it does not",
        "copy vendor code, UI, schemas, or proprietary implementation details. It normalizes publicly documented patterns",
        "into generic system families, workflows, canonical primitive templates, specialization edges, proof plans, and",
        "project benchmark seeds. All generated rows are `candidate=true` and `serves_truth=false`.",
        "",
        "A benchmark binding is only a seed. It becomes a real result only after the starter repo, runtime, hidden oracle,",
        "known-good/known-bad mutation checks, cleanup, and `project_run_receipt` actually execute.",
        "",
        "## Generated surface",
        "",
        f"- system families: {counts['system_families']}",
        f"- business workflows: {counts['business_workflows']}",
        f"- canonical primitive templates: {counts['primitive_templates']}",
        f"- system-adapter candidates: {counts['system_adapters']}",
        f"- workflow-specific primitive candidates: {counts['primitive_candidates']}",
        f"- source records: {counts['source_records']}",
        f"- project benchmark seeds: {counts['benchmark_bindings']}",
        "",
        "## Normalization model",
        "",
        "```text",
        "canonical operation + typed contract + invariants + side effects + error semantics",
        "  + system adapter + industry/standard overlay + workflow composition + executable oracle",
        "```",
        "",
        "Company and product names are provenance, not primitive identity. A hospital bed, transformer, aircraft, railcar,",
        "factory machine, and vehicle can all specialize the same governed `asset` operations. A quality investigation,",
        "AML case, public-sector case, and incident can all specialize the same evidence-linked case/work-queue machinery.",
        "",
        "## System families and workflows",
        "",
        "| System family | Industries | Workflows | Public evidence refs |",
        "|---|---|---:|---|",
    ]
    workflow_counts = Counter(row["system_id"] for row in rows["business_workflows"])
    for system in rows["systems"]:
        lines.append(
            f"| `{system['system_id']}` | {', '.join(system['industries'])} | "
            f"{workflow_counts[system['system_id']]} | {', '.join(system['source_refs'])} |"
        )
    lines.extend(
        [
            "",
            "## Canonical primitive templates",
            "",
            "| Template | Layer | Operation | Contract | Determinism | Oracle |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in rows["primitive_templates"]:
        lines.append(
            f"| `{row['template_id']}` | {row['layer']} | {row['operation']} | "
            f"`{row['input_type']} -> {row['output_type']}` | {row['determinism']} | {row['oracle_kind']} |"
        )
    lines.extend(
        [
            "",
            "## Project proof path",
            "",
            "Each workflow maps to an O5-or-stronger project seed. The implementation path is:",
            "",
            "```text",
            "public source metadata",
            "  -> generic workflow candidate",
            "  -> canonical primitive composition",
            "  -> starter repo + hidden oracle",
            "  -> known-good / known-bad / mutation validation",
            "  -> harness-alone vs primitive-assisted execution",
            "  -> project_run_receipt",
            "```",
            "",
            "High-risk healthcare, government, finance, defense, energy, and space workflows require explicit human",
            "authority. The source policy excludes insurance expansion and autonomous lethal targeting, unreviewed",
            "clinical decisions, unreviewed public-benefit decisions, and covert-surveillance decisions.",
            "",
            "## Source registry",
            "",
        ]
    )
    for source in rows["source_records"]:
        lines.append(
            f"- [{source['title']}]({source['url']}) — class {source['source_class']}; {source['authority']}."
        )
    return "\n".join(lines) + "\n"


def build_outputs(data: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    """Build every derived artifact in memory with stable ordering."""
    validate_source(data)
    sources = [
        {
            "record_type": "enterprise_public_source_record",
            "source_id": row["id"],
            "title": row["title"],
            "url": row["url"],
            "source_class": row["source_class"],
            "authority": row["authority"],
            "background_only": bool(row.get("background_only")),
            "evidence_snapshot_date": data["evidence_snapshot_date"],
            "content_body_stored": False,
            "use_policy": data["scope"]["source_use_policy"],
            **BOUNDARY,
        }
        for row in sorted(data["sources"], key=lambda item: item["id"])
    ]
    tools = [
        {
            "record_type": "enterprise_tool_class",
            "tool_class_id": row["id"],
            "title": row["title"],
            "canonical_objects": row["objects"],
            "adapter_contract": data["adapter_contract"],
            "vendor_bindings_are_adapters": True,
            **BOUNDARY,
        }
        for row in sorted(data["tool_classes"], key=lambda item: item["id"])
    ]
    adapters = [
        {
            "record_type": "enterprise_system_adapter_candidate",
            "adapter_candidate_id": canonical_id("entadapter", row["id"], operation),
            "tool_class_id": row["id"],
            "operation": operation,
            "canonical_objects": row["objects"],
            "contract": {
                "input_type": f"{_pascal(row['id'])}AdapterIntent",
                "output_type": f"{_pascal(operation)}Receipt",
                "vendor_specific_binding_required": True,
            },
            "proof_requirements": [
                "local_fixture_or_emulator",
                "permission_boundary_test",
                "positive_and_negative_contract_cases",
                "receipt_readback",
            ],
            "fact_or_inference": "generic_adapter_contract_candidate",
            **BOUNDARY,
        }
        for row in sorted(data["tool_classes"], key=lambda item: item["id"])
        for operation in data["adapter_contract"]
    ]
    templates = [
        {
            "record_type": "enterprise_primitive_template",
            "template_id": row["id"],
            "title": _title(row["id"]),
            "layer": row["layer"],
            "operation": row["operation"],
            "business_object_class": row["object"],
            "input_type": row["input"],
            "output_type": row["output"],
            "invariants": row["invariants"],
            "effects": row["effects"],
            "determinism": row["determinism"],
            "oracle_kind": row["oracle"],
            "canonical_primitive": row["primitive"],
            "identity_rule": "operation+input+output+invariants+effects+determinism",
            **BOUNDARY,
        }
        for row in sorted(data["primitive_templates"], key=lambda item: item["id"])
    ]
    systems, workflows = _system_and_workflow_rows(data)
    candidates, edges, proofs = _candidate_rows(data, workflows)
    benchmarks = _benchmark_rows(data, workflows)
    evidence = _evidence_rows(data)
    projects = [
        {
            "record_type": "enterprise_project_archetype",
            "project_archetype_id": project_id,
            "title": _title(project_id),
            "benchmark_status": "template_only_not_executed",
            **BOUNDARY,
        }
        for project_id in sorted(data["project_archetypes"])
    ]
    rows = {
        "source_records": sources,
        "source_evidence_locators": sorted(evidence, key=lambda row: row["evidence_id"]),
        "tool_classes": tools,
        "system_adapters": sorted(adapters, key=lambda row: row["adapter_candidate_id"]),
        "primitive_templates": templates,
        "systems": systems,
        "business_workflows": workflows,
        "primitive_candidates": sorted(candidates, key=lambda row: row["candidate_id"]),
        "primitive_edges": sorted(edges, key=lambda row: row["edge_id"]),
        "proof_plans": sorted(proofs, key=lambda row: row["proof_plan_id"]),
        "project_archetypes": projects,
        "benchmark_bindings": sorted(benchmarks, key=lambda row: row["benchmark_seed_id"]),
    }
    outputs = {OUTPUT_FILES[key]: _jsonl(value) for key, value in rows.items()}
    file_meta = {
        filename: {"record_count": len(rows[key]), "sha256": sha256_hex(outputs[filename])}
        for key, filename in OUTPUT_FILES.items()
    }
    manifest = {
        "record_type": "enterprise_operating_system_primitive_atlas_manifest",
        "pack_id": PACK_SLUG,
        "schema_version": data["schema_version"],
        "evidence_snapshot_date": data["evidence_snapshot_date"],
        "source_hash": sha256_hex(data),
        "description": data["scope"]["statement"],
        "counts": {
            "source_records": len(sources),
            "source_evidence_locators": len(evidence),
            "tool_classes": len(tools),
            "system_adapters": len(adapters),
            "primitive_templates": len(templates),
            "system_families": len(systems),
            "business_workflows": len(workflows),
            "primitive_candidates": len(candidates),
            "primitive_edges": len(edges),
            "proof_plans": len(proofs),
            "project_archetypes": len(projects),
            "benchmark_bindings": len(benchmarks),
        },
        "files": file_meta,
        "excluded_domains": data["scope"]["excluded_domains"],
        "excluded_actions": data["scope"]["excluded_actions"],
        "claim_boundary": {
            "public_sources_prove": "documented platform and workflow breadth only",
            "primitive_decompositions": "independent candidate inferences",
            "benchmark_bindings": "seeds only; not results",
        },
        **BOUNDARY,
    }
    outputs["manifest.json"] = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    outputs["__doc__"] = _render_doc(data, rows, manifest)
    return outputs, manifest


def emit(data: dict[str, Any]) -> dict[str, Any]:
    """Write the deterministic derived layer without changing the raw source."""
    validate_source(data, validate_manifest=True)
    outputs, manifest = build_outputs(data)
    pack_dir = resource(PACK_DIR_REL)
    pack_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in outputs.items():
        if filename == "__doc__":
            continue
        (pack_dir / filename).write_text(content, encoding="utf-8")
    doc_path = resource(DOC_REL)
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(outputs["__doc__"], encoding="utf-8")
    return {"manifest": str(pack_dir / "manifest.json"), "doc": str(doc_path), **manifest["counts"]}


def self_test() -> bool:
    """Verify validation teeth, deterministic bytes, boundaries, and no-proxy status."""
    data = load_source()
    validate_source(data, validate_manifest=True)
    first, first_manifest = build_outputs(data)
    second, second_manifest = build_outputs(copy.deepcopy(data))
    assert first == second, "determinism gate: repeated builds must be byte-identical"
    assert first_manifest == second_manifest

    # Mutation gate 1: an unresolved primitive reference must make the validator red.
    bad_ref = copy.deepcopy(data)
    bad_ref["system_families"][0]["workflows"][0]["primitives"].append("missing-template")
    try:
        validate_source(bad_ref)
    except AtlasValidationError as exc:
        assert "missing-template" in str(exc)
    else:
        raise AssertionError("mutation gate failed: missing primitive reference passed")

    # Mutation gate 2: the repo's excluded industry must stay excluded from new work.
    excluded = copy.deepcopy(data)
    excluded["system_families"][0]["industries"].append("insurance")
    try:
        validate_source(excluded)
    except AtlasValidationError as exc:
        assert "excluded domain" in str(exc)
    else:
        raise AssertionError("mutation gate failed: excluded-domain specialization passed")

    candidates = [json.loads(line) for line in first[OUTPUT_FILES["primitive_candidates"]].splitlines()]
    benchmarks = [json.loads(line) for line in first[OUTPUT_FILES["benchmark_bindings"]].splitlines()]
    assert len({row["candidate_id"] for row in candidates}) == len(candidates)
    assert all(row["candidate"] and not row["serves_truth"] for row in candidates)
    assert all(not row["headline_eligible"] and not row["benchmark_result"] for row in benchmarks)
    assert all(row["no_proxy_gate_required"] for row in benchmarks)
    assert first_manifest["counts"]["system_adapters"] == (
        first_manifest["counts"]["tool_classes"] * len(data["adapter_contract"])
    )
    assert first_manifest["counts"]["primitive_candidates"] > first_manifest["counts"]["business_workflows"]

    print(
        "OK enterprise operating-system primitive atlas self-test: "
        f"{first_manifest['counts']['system_families']} systems, "
        f"{first_manifest['counts']['business_workflows']} workflows, "
        f"{first_manifest['counts']['primitive_templates']} canonical templates, "
        f"{first_manifest['counts']['primitive_candidates']} candidate specializations; "
        "determinism + unresolved-ref mutation + excluded-domain mutation gates pass; "
        "benchmark rows remain seed-only; serves_truth=false"
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()
    data = load_source()
    if args.self_test:
        self_test()
        return 0
    if args.emit:
        print(json.dumps(emit(data), indent=2, sort_keys=True))
        return 0
    outputs, manifest = build_outputs(data)
    if args.stats:
        print(json.dumps(manifest["counts"], indent=2, sort_keys=True))
        return 0
    print(outputs["__doc__"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
