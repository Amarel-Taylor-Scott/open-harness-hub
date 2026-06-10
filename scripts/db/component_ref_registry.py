#!/usr/bin/env python3
"""Export registered component references for database seed/check workflows."""
from __future__ import annotations

import argparse
import json
from typing import Any

from scripts._config import REGISTERED_COMPONENT_REF_IDS


def component_ref_registry_summary() -> dict[str, Any]:
    """Return registered component IDs that should seed/check component_ref rows."""
    return {
        "database_seed_target": {
            "component_table": "component",
            "reference_table": "component_ref",
            "source_of_truth": "repo_seed",
        },
        "registered_component_refs": REGISTERED_COMPONENT_REF_IDS,
    }


def component_ref_seed_rows(*, source_component_id: str | None = None) -> list[dict[str, str]]:
    """Return component_ref-shaped rows when a source component is supplied."""
    if not source_component_id:
        return []
    return [
        {
            "src_id": source_component_id,
            "dst_id": component_id,
            "role": metadata["role"],
        }
        for component_id, metadata in sorted(REGISTERED_COMPONENT_REF_IDS.items())
    ]


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Component Ref Registry",
        "",
        "These component IDs are registered because they are repeated across YAML seed/export manifests.",
        "Hosted deployments should seed/check `component_ref` rows instead of treating raw YAML text as the operational source.",
        "",
        "| Component ID | Type | Role | Owner |",
        "|---|---|---|---|",
    ]
    for component_id, metadata in sorted(summary["registered_component_refs"].items()):
        lines.append(
            "| {component_id} | {component_type} | {role} | {owner} |".format(
                component_id=component_id,
                component_type=metadata["component_type"],
                role=metadata["role"],
                owner=metadata["owner"],
            )
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument(
        "--source-component-id",
        help="Emit component_ref seed rows from this source component to every registered target.",
    )
    args = parser.parse_args()

    payload: Any
    if args.source_component_id:
        payload = component_ref_seed_rows(source_component_id=args.source_component_id)
    else:
        payload = component_ref_registry_summary()

    if args.format == "markdown" and not args.source_component_id:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
