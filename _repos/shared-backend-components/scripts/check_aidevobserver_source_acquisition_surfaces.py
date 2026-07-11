#!/usr/bin/env python3
"""Check AIDevObserver real-source acquisition surfaces.

This proof keeps the primitive-acquisition map honest for launch work:

* PyPI is split into JSON metadata and index/distribution metadata lanes.
* Public repo scanning includes GitHub and GitLab metadata, not raw source by default.
* Coding textbooks are represented as OER/open-license or metadata-only sources.
* Cloud/Kubernetes/framework docs are official-docs context, not copied prose.
* DeterministicBuilds.io is represented as a demand-signal/request leaderboard.
* Every new lane emits primitive opportunities and explicit license notes.

The check is offline and stdlib-only. It validates the JSONL surface map, not
live network fetching. All downstream candidates remain `serves_truth=false`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
SURFACE_MAP = _resource("catalog") / "knowledge-packs" / "data" / "primitive-source-surface-map" / "surfaces.jsonl"

REQUIRED_SURFACES = {
    "surface-pypi-json-api": {
        "tags": {"pypi", "python", "metadata"},
        "opportunities": {"python_package_metadata_connector", "package_to_reuse_card"},
    },
    "surface-pypi-index-api": {
        "tags": {"pypi", "supply-chain"},
        "opportunities": {"distribution_file_inventory", "hash_digest_source_ref"},
    },
    "surface-python-official-docs": {
        "tags": {"python", "official-docs"},
        "opportunities": {"stdlib_reuse_route", "python_api_contract_reference"},
    },
    "surface-openstax-oer-programming-adjacent": {
        "tags": {"oer", "textbooks"},
        "opportunities": {"open_textbook_concept_map", "licensed_learning_context_pack"},
    },
    "surface-open-textbook-library": {
        "tags": {"oer", "open-license"},
        "opportunities": {"licensed_book_metadata_connector", "topic_to_primitive_gap_map"},
    },
    "surface-github-public-repo-metadata": {
        "tags": {"github", "repos", "licenses"},
        "opportunities": {"public_repo_capability_discovery", "license_aware_source_ref"},
    },
    "surface-gitlab-public-projects": {
        "tags": {"gitlab", "ci"},
        "opportunities": {"public_project_capability_discovery", "gitlab_ci_reuse_card"},
    },
    "surface-github-actions-marketplace": {
        "tags": {"github-actions", "workflow"},
        "opportunities": {"github_action_contract", "workflow_step_reuse_card"},
    },
    "surface-terraform-registry": {
        "tags": {"terraform", "iac"},
        "opportunities": {"terraform_module_contract", "iac_reuse_card"},
    },
    "surface-cloud-native-official-docs": {
        "tags": {"kubernetes", "cloud-functions", "official-docs"},
        "opportunities": {"k8s_workload_checklist", "cloud_function_checklist"},
    },
    "surface-framework-official-docs": {
        "tags": {"frameworks", "developer"},
        "opportunities": {"framework_route_template", "common_setup_reuse_card"},
    },
    "surface-deterministicbuilds-leaderboard": {
        "tags": {"deterministic-builds", "demand-signal", "leaderboard"},
        "opportunities": {"deterministic_build_request", "primitive_bounty", "proof_backlog"},
    },
}


def _rows() -> list[dict]:
    rows: list[dict] = []
    for i, line in enumerate(SURFACE_MAP.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"invalid JSONL at line {i}: {exc}") from exc
        if not isinstance(row, dict):
            raise AssertionError(f"line {i} is not a JSON object")
        rows.append(row)
    return rows


def self_test() -> int:
    rows = _rows()
    by_id = {row.get("id"): row for row in rows}
    assert len(by_id) == len(rows), "surface ids must be unique"

    for sid, expected in REQUIRED_SURFACES.items():
        row = by_id.get(sid)
        assert row, f"missing required source acquisition surface: {sid}"
        assert row.get("version"), f"{sid} must carry version"
        assert row.get("url"), f"{sid} must carry source URL"
        assert row.get("access_method"), f"{sid} must declare access_method"
        assert row.get("scan_cadence"), f"{sid} must declare scan_cadence"
        assert row.get("license_note"), f"{sid} must declare license_note"
        assert row.get("authority"), f"{sid} must declare authority"

        tags = set(row.get("tags") or [])
        missing_tags = expected["tags"] - tags
        assert not missing_tags, f"{sid} missing tags: {sorted(missing_tags)}"

        opportunities = set(row.get("primitive_opportunities") or [])
        missing_opps = expected["opportunities"] - opportunities
        assert not missing_opps, f"{sid} missing primitive opportunities: {sorted(missing_opps)}"

        license_note = str(row.get("license_note") or "").lower()
        assert any(term in license_note for term in ("license", "terms", "attribution", "rights")), (
            f"{sid} license_note must mention license/terms/attribution/rights"
        )
        if "textbook" in sid or "openstax" in sid:
            assert "open" in license_note or "proprietary" in license_note or "commercial" in license_note, (
                f"{sid} must distinguish open/OER from proprietary textbook ingestion"
            )

    print(
        "PASS - aidevobserver source acquisition surfaces: "
        f"{len(REQUIRED_SURFACES)} required PyPI/repo/OER/docs/workflow/IaC lanes validated; "
        "all are license-aware, primitive-oriented, and candidate-only by downstream policy."
    )
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv or not argv:
        return self_test()
    print("usage: python3 scripts/check_aidevobserver_source_acquisition_surfaces.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
