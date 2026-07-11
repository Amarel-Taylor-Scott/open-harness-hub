#!/usr/bin/env python3
"""Export canonical vector configuration for DB/search schema renderers.

This is the reviewable bridge between repo seed constants and database-backed
settings rows. Hosted deployments should seed `setting_profile` rows from this
output instead of copying dimensions, model IDs, backend names, or similarity
functions into each backend schema by hand.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from typing import Any

from scripts._config import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_SENTENCE_TRANSFORMERS_EMBEDDING_MODEL,
    DEFAULT_VECTOR_SIMILARITY,
    DEFAULT_VECTOR_STORAGE_BACKEND,
    PGVECTOR_TYPE_SETTING_KEY,
    VECTOR_INDEX_PROFILES,
    VECTOR_STORAGE_BACKENDS,
    pgvector_type,
)


def vector_config_summary() -> dict[str, Any]:
    """Return the canonical vector/index settings used by DB docs and loaders."""
    return {
        "default_embedding_model": DEFAULT_EMBEDDING_MODEL,
        "default_sentence_transformers_embedding_model": DEFAULT_SENTENCE_TRANSFORMERS_EMBEDDING_MODEL,
        "default_embedding_dimensions": DEFAULT_EMBEDDING_DIMENSIONS,
        "default_vector_similarity": DEFAULT_VECTOR_SIMILARITY,
        "default_vector_storage_backend": DEFAULT_VECTOR_STORAGE_BACKEND,
        PGVECTOR_TYPE_SETTING_KEY: pgvector_type(),
        "vector_storage_backends": deepcopy(VECTOR_STORAGE_BACKENDS),
        "vector_index_profiles": deepcopy(VECTOR_INDEX_PROFILES),
        "database_seed_target": {
            "profile_table": "setting_profile",
            "value_table": "setting_value",
            "setting_kind": "vector_index",
            "source_of_truth": "repo_seed",
        },
    }


def setting_profile_seed_rows(*, tenant_id: str = "system") -> list[dict[str, Any]]:
    """Return seed rows shaped for the database settings registry."""
    rows = []
    for profile_id, profile in VECTOR_INDEX_PROFILES.items():
        rows.append(
            {
                "setting_profile_id": f"setting://{tenant_id}/vector_index/{profile_id}",
                "tenant_id": tenant_id,
                "namespace": "vector.index",
                "setting_key": profile_id,
                "setting_kind": "vector_index",
                "value_type": "json",
                "default_value": profile,
                "allowed_values": [],
                "validation": {
                    "required": [
                        "subject_type",
                        "backend",
                        "embedding_model",
                        "dimensions",
                        "similarity",
                    ],
                    "dimensions": {"minimum": 1},
                },
                "source_of_truth": "repo_seed",
                "body": {
                    "owner": "scripts._config.VECTOR_INDEX_PROFILES",
                    PGVECTOR_TYPE_SETTING_KEY: pgvector_type(int(profile["dimensions"])),
                },
            }
        )
    return rows


def render_markdown(summary: dict[str, Any]) -> str:
    """Render a compact human-readable registry view."""
    lines = [
        "# Vector Config Registry",
        "",
        f"- Default model: `{summary['default_sentence_transformers_embedding_model']}`",
        f"- Default dimensions: `{summary['default_embedding_dimensions']}`",
        f"- Default similarity: `{summary['default_vector_similarity']}`",
        f"- Default backend: `{summary['default_vector_storage_backend']}`",
        f"- Postgres type: `{summary[PGVECTOR_TYPE_SETTING_KEY]}`",
        "",
        "## Index Profiles",
        "",
        "| Profile | Subject | Backend | Dimensions | Similarity | Index Names |",
        "|---|---|---|---:|---|---|",
    ]
    for profile_id, profile in summary["vector_index_profiles"].items():
        names = ", ".join(
            f"{backend}:{name}" for backend, name in sorted(profile.get("index_names", {}).items())
        )
        lines.append(
            "| {profile_id} | {subject} | {backend} | {dimensions} | {similarity} | {names} |".format(
                profile_id=profile_id,
                subject=profile["subject_type"],
                backend=profile["backend"],
                dimensions=profile["dimensions"],
                similarity=profile["similarity"],
                names=names,
            )
        )
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
    parser.add_argument("--tenant-id", default="system", help="Tenant id for seed rows.")
    args = parser.parse_args()

    payload: Any
    if args.setting_profile_seeds:
        payload = setting_profile_seed_rows(tenant_id=args.tenant_id)
    else:
        payload = vector_config_summary()

    if args.format == "markdown":
        if args.setting_profile_seeds:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
