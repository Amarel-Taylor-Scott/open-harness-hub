#!/usr/bin/env python3
"""Export canonical model runtime routes for DB settings seed rows.

This keeps judge/runtime model defaults out of ad hoc script literals while the
hosted product migrates them into `setting_profile` and `setting_value` rows.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from typing import Any
from urllib.parse import quote

from scripts._config import (
    MODEL_RUNTIME_PROFILES,
    REGISTERED_EXAMPLE_MODEL_VALUES,
    REGISTERED_MODEL_CLASS_VALUES,
    REGISTERED_MODEL_FAMILY_TAGS,
    REGISTERED_TOOL_TAGS,
)


def model_runtime_summary() -> dict[str, Any]:
    """Return the canonical runtime model route registry."""
    return {
        "model_runtime_profiles": deepcopy(MODEL_RUNTIME_PROFILES),
        "model_vocabulary": {
            "example_models": deepcopy(REGISTERED_EXAMPLE_MODEL_VALUES),
            "model_classes": deepcopy(REGISTERED_MODEL_CLASS_VALUES),
            "model_family_tags": deepcopy(REGISTERED_MODEL_FAMILY_TAGS),
            "tool_tags": deepcopy(REGISTERED_TOOL_TAGS),
        },
        "database_seed_target": {
            "profile_table": "setting_profile",
            "value_table": "setting_value",
            "setting_kinds": [
                "model_route",
                "judge_model",
                "rerank_model",
                "custom",
            ],
            "source_of_truth": "repo_seed",
        },
    }


def _runtime_setting_kind(profile_id: str) -> str:
    if "rerank" in profile_id:
        return "rerank_model"
    if "judge" in profile_id:
        return "judge_model"
    return "model_route"


def _setting_profile_row(
    *,
    tenant_id: str,
    namespace: str,
    setting_key: str,
    setting_kind: str,
    default_value: dict[str, Any],
    owner: str,
    validation: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    setting_key_id = quote(setting_key, safe="")
    return {
        "setting_profile_id": f"setting://{tenant_id}/{namespace}/{setting_key_id}",
        "tenant_id": tenant_id,
        "namespace": namespace.replace("/", "."),
        "setting_key": setting_key,
        "setting_kind": setting_kind,
        "value_type": "json",
        "default_value": default_value,
        "allowed_values": [],
        "validation": validation or {},
        "source_of_truth": "repo_seed",
        "body": {
            "owner": owner,
            **(body or {}),
        },
    }


def setting_profile_seed_rows(*, tenant_id: str = "system", include_vocabulary: bool = True) -> list[dict[str, Any]]:
    """Return seed rows shaped for the database settings registry."""
    rows = []
    for profile_id, profile in MODEL_RUNTIME_PROFILES.items():
        rows.append(
            _setting_profile_row(
                tenant_id=tenant_id,
                namespace="model.runtime",
                setting_key=profile_id,
                setting_kind=_runtime_setting_kind(profile_id),
                default_value=profile,
                owner="scripts._config.MODEL_RUNTIME_PROFILES",
                validation={
                    "required": [
                        "provider",
                        "model",
                        "runtime",
                        "trust_boundary",
                    ],
                },
                body={
                    "migration_note": (
                        "Deployment-owned setting_value rows may override env names, "
                        "model IDs, endpoints, and timeouts without changing scripts."
                    ),
                },
            )
        )
    if not include_vocabulary:
        return rows

    vocabulary_groups: list[tuple[str, str, dict[str, dict[str, Any]], str]] = [
        ("model.example", "model_route", REGISTERED_EXAMPLE_MODEL_VALUES, "scripts._config.REGISTERED_EXAMPLE_MODEL_VALUES"),
        ("model.family", "custom", REGISTERED_MODEL_FAMILY_TAGS, "scripts._config.REGISTERED_MODEL_FAMILY_TAGS"),
        ("model.class", "custom", REGISTERED_MODEL_CLASS_VALUES, "scripts._config.REGISTERED_MODEL_CLASS_VALUES"),
        ("tool.tag", "custom", REGISTERED_TOOL_TAGS, "scripts._config.REGISTERED_TOOL_TAGS"),
    ]
    for namespace, setting_kind, registry, owner in vocabulary_groups:
        for setting_key, value in registry.items():
            rows.append(
                _setting_profile_row(
                    tenant_id=tenant_id,
                    namespace=namespace,
                    setting_key=setting_key,
                    setting_kind=setting_kind,
                    default_value={"value": setting_key, **value},
                    owner=owner,
                    validation={"required": ["value"]},
                    body={
                        "migration_note": (
                            "Catalog vocabulary value registered to keep repeated YAML/docs terms "
                            "out of hard-coded-setting migration candidates."
                        ),
                    },
                )
            )
    return rows


def render_markdown(summary: dict[str, Any]) -> str:
    """Render a compact human-readable registry view."""
    lines = [
        "# Model Runtime Registry",
        "",
        "| Profile | Provider | Runtime | Trust Boundary | Default Model | Env Override |",
        "|---|---|---|---|---|---|",
    ]
    for profile_id, profile in summary["model_runtime_profiles"].items():
        env_override = profile.get("model_env") or ""
        lines.append(
            "| {profile_id} | {provider} | {runtime} | {trust_boundary} | {model} | {env_override} |".format(
                profile_id=profile_id,
                provider=profile["provider"],
                runtime=profile["runtime"],
                trust_boundary=profile["trust_boundary"],
                model=profile["model"],
                env_override=env_override,
            )
        )
    vocabulary = summary.get("model_vocabulary") or {}
    if vocabulary:
        lines.extend(["", "## Vocabulary Buckets", ""])
        for label, values in vocabulary.items():
            lines.append(f"- {label}: {len(values)}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    parser.add_argument(
        "--setting-profile-seeds",
        action="store_true",
        help="Emit database setting_profile seed rows instead of the full summary.",
    )
    parser.add_argument(
        "--runtime-only",
        action="store_true",
        help="When emitting setting_profile rows, omit registered vocabulary bucket rows.",
    )
    parser.add_argument("--tenant-id", default="system", help="Tenant id for seed rows.")
    args = parser.parse_args()

    payload: Any
    if args.setting_profile_seeds:
        payload = setting_profile_seed_rows(
            tenant_id=args.tenant_id,
            include_vocabulary=not args.runtime_only,
        )
    else:
        payload = model_runtime_summary()

    if args.format == "markdown":
        if args.setting_profile_seeds:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
