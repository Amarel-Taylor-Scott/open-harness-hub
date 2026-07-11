#!/usr/bin/env python3
"""Runtime setting resolution backed by setting_profile rows.

Use this for deployable settings that still have Python seed definitions. The
resolution order is:

1. explicit environment variable
2. explicit fallback environment variable
3. effective setting_profile/setting_value row
4. Python seed default

That keeps local/static behavior stable while allowing hosted deployments to
move mutable defaults into `setting_value` rows.
"""
from __future__ import annotations

import os
from typing import Any

from scripts.db.setting_profile_rows import setting_profile_rows_by_namespace


def _row_value(row: dict[str, Any]) -> Any:
    default_value = row.get("default_value")
    if isinstance(default_value, dict) and "value" in default_value:
        return default_value.get("value")
    return default_value


def runtime_setting(
    *,
    namespace: str,
    definitions: dict[str, dict[str, Any]],
    name: str,
    scope: dict[str, Any] | None = None,
    prefer_database: bool = True,
    strict_database: bool = False,
) -> str:
    """Resolve a runtime setting through env, registry rows, then seed default."""
    setting = definitions[name]
    env_name = str(setting["env"])
    if env_name in os.environ:
        return os.environ[env_name]

    fallback_env = setting.get("fallback_env")
    if fallback_env and str(fallback_env) in os.environ:
        return os.environ[str(fallback_env)]

    try:
        rows = setting_profile_rows_by_namespace(
            namespace,
            prefer_database=prefer_database,
            strict_database=strict_database,
            scope=scope,
        )
    except (RuntimeError, ValueError):
        rows = []

    for row in rows:
        if row.get("setting_key") != name:
            continue
        value = _row_value(row)
        if value is not None and value != "":
            return str(value)
        fallback_setting = setting.get("fallback_setting")
        if fallback_setting:
            return runtime_setting(
                namespace=namespace,
                definitions=definitions,
                name=str(fallback_setting),
                scope=scope,
                prefer_database=prefer_database,
                strict_database=strict_database,
            )

    fallback_setting = setting.get("fallback_setting")
    if fallback_setting:
        resolved = runtime_setting(
            namespace=namespace,
            definitions=definitions,
            name=str(fallback_setting),
            scope=scope,
            prefer_database=prefer_database,
            strict_database=strict_database,
        )
        if resolved:
            return resolved

    return str(setting["default"])
