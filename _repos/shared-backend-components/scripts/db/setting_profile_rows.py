#!/usr/bin/env python3
"""Shared read helpers for setting_profile registry rows.

These helpers are the runtime/static bridge for database-backed settings.
Runtime consumers should call this module instead of hand-reading
`db/seeds/settings-registry/setting_profile.jsonl`. Hosted deployments can pass
or expose a database URL to read `setting_profile` rows directly; local/static
consumers keep using the generated JSONL seed.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
from pathlib import Path
from typing import Any

from scripts._config import DEFAULT_DATABASE_URL_ENV, REPO_ROOT


DEFAULT_SETTING_PROFILE_PATH = _resource("db") / "seeds" / "settings-registry" / "setting_profile.jsonl"
DEFAULT_SETTING_TENANT_ID = "system"


def resolve_setting_profile_path(path: Path | str | None = None) -> Path:
    """Resolve a setting_profile JSONL path.

    Absolute paths are returned as-is. Relative paths are interpreted relative
    to the repository root so hosted/generated row paths can be supplied without
    depending on the current working directory.
    """
    if path is None:
        return DEFAULT_SETTING_PROFILE_PATH
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return _resource(candidate)


def read_setting_profile_seed_rows(path: Path | str | None = None) -> list[dict[str, Any]]:
    """Read setting_profile JSONL seed rows from a path.

    Missing files return an empty list so callers can use explicit fallbacks.
    Malformed files raise ValueError; callers that want soft fallback can catch
    it and return their local seed literals.
    """
    resolved = resolve_setting_profile_path(path)
    if not resolved.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(resolved.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{resolved}:{line_no}: invalid JSONL row: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{resolved}:{line_no}: expected JSON object row")
        rows.append(row)
    return rows


def read_setting_profile_rows_from_database(
    *,
    database_url: str,
    tenant_id: str = DEFAULT_SETTING_TENANT_ID,
    namespace: str | None = None,
    scope: dict[str, Any] | None = None,
    apply_effective_values: bool = True,
) -> list[dict[str, Any]]:
    """Read active setting_profile rows from Postgres.

    The `psycopg` dependency is optional for static builds. Callers decide
    whether a database read failure should be fatal or should fall back to seed
    rows by catching RuntimeError.

    When `apply_effective_values` is true, the row's `default_value` is replaced
    with the currently effective `setting_value.value` for the requested scope.
    The original default remains in `profile_default_value`.
    """
    if not database_url:
        return []
    try:
        import psycopg  # type: ignore[import-not-found]
        from psycopg.rows import dict_row  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required to read setting_profile rows from Postgres") from exc

    sql = """
        SELECT
          sp.setting_profile_id,
          sp.tenant_id,
          sp.namespace,
          sp.setting_key,
          sp.setting_kind,
          sp.value_type,
          sp.default_value,
          sp.allowed_values,
          sp.validation,
          sp.source_of_truth,
          sp.body,
          sp.owner_team,
          sv.setting_value_id,
          sv.value AS effective_value,
          sv.scope AS effective_scope,
          sv.version AS effective_version,
          sv.effective_from AS effective_from,
          sv.lineage_event_id AS effective_lineage_event_id
        FROM setting_profile sp
        LEFT JOIN LATERAL (
          SELECT
            setting_value_id,
            value,
            scope,
            version,
            effective_from,
            lineage_event_id
          FROM setting_value
          WHERE setting_profile_id = sp.setting_profile_id
            AND tenant_id = %s
            AND effective_from <= now()
            AND (effective_to IS NULL OR effective_to > now())
            AND (scope = '{}'::jsonb OR %s::jsonb @> scope)
          ORDER BY jsonb_object_length(scope) DESC, effective_from DESC, created_at DESC
          LIMIT 1
        ) sv ON TRUE
        WHERE sp.tenant_id = %s
          AND sp.lifecycle <> 'archived'
    """
    scope_json = json.dumps(scope or {}, sort_keys=True)
    params: list[Any] = [tenant_id, scope_json, tenant_id]
    if namespace:
        sql += " AND sp.namespace = %s"
        params.append(namespace)
    sql += " ORDER BY sp.namespace, sp.setting_key"

    try:
        with psycopg.connect(database_url, connect_timeout=3, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = [dict(row) for row in cur.fetchall()]
    except Exception as exc:  # pragma: no cover - depends on local Postgres availability
        raise RuntimeError(f"failed to read setting_profile rows from Postgres: {exc}") from exc

    normalized: list[dict[str, Any]] = []
    for row in rows:
        body = row.get("body")
        if not isinstance(body, dict):
            body = {}
        if row.get("owner_team") and "owner" not in body:
            body = {**body, "owner": row["owner_team"]}
        effective_value = row.get("effective_value")
        default_value = row["default_value"]
        normalized_row = {
            "setting_profile_id": row["setting_profile_id"],
            "tenant_id": row["tenant_id"],
            "namespace": row["namespace"],
            "setting_key": row["setting_key"],
            "setting_kind": row["setting_kind"],
            "value_type": row["value_type"],
            "default_value": effective_value if apply_effective_values and effective_value is not None else default_value,
            "profile_default_value": default_value,
            "allowed_values": row.get("allowed_values") or [],
            "validation": row.get("validation") or {},
            "source_of_truth": row["source_of_truth"],
            "body": body,
        }
        if row.get("setting_value_id"):
            normalized_row["effective_setting_value"] = {
                "setting_value_id": row["setting_value_id"],
                "scope": row.get("effective_scope") or {},
                "version": row.get("effective_version"),
                "effective_from": str(row["effective_from"]) if row.get("effective_from") is not None else None,
                "lineage_event_id": row.get("effective_lineage_event_id"),
            }
        normalized.append(normalized_row)
    return normalized


def read_setting_profile_rows(
    path: Path | str | None = None,
    *,
    database_url: str | None = None,
    tenant_id: str = DEFAULT_SETTING_TENANT_ID,
    scope: dict[str, Any] | None = None,
    prefer_database: bool = False,
    strict_database: bool = False,
) -> list[dict[str, Any]]:
    """Read setting_profile rows from Postgres when requested, else seed JSONL.

    `prefer_database=True` checks `database_url` first, then `$DATABASE_URL`.
    If the database cannot be read and `strict_database` is false, the helper
    falls back to the JSONL seed so static docs and local validation continue to
    work without a live database.
    """
    effective_database_url = database_url
    if prefer_database and effective_database_url is None:
        effective_database_url = os.environ.get(DEFAULT_DATABASE_URL_ENV, "")
    if prefer_database and effective_database_url:
        try:
            rows = read_setting_profile_rows_from_database(
                database_url=effective_database_url,
                tenant_id=tenant_id,
                scope=scope,
            )
        except RuntimeError:
            if strict_database:
                raise
        else:
            if rows:
                return rows
    return read_setting_profile_seed_rows(path)


def setting_profile_rows_by_namespace(
    namespace: str,
    path: Path | str | None = None,
    *,
    database_url: str | None = None,
    tenant_id: str = DEFAULT_SETTING_TENANT_ID,
    scope: dict[str, Any] | None = None,
    prefer_database: bool = False,
    strict_database: bool = False,
) -> list[dict[str, Any]]:
    """Return setting_profile rows for a namespace from DB or JSONL seed."""
    if prefer_database:
        effective_database_url = database_url if database_url is not None else os.environ.get(DEFAULT_DATABASE_URL_ENV, "")
        if effective_database_url:
            try:
                rows = read_setting_profile_rows_from_database(
                    database_url=effective_database_url,
                    tenant_id=tenant_id,
                    namespace=namespace,
                    scope=scope,
                )
            except RuntimeError:
                if strict_database:
                    raise
            else:
                if rows:
                    return rows
    return [row for row in read_setting_profile_seed_rows(path) if row.get("namespace") == namespace]
