#!/usr/bin/env python3
"""Probe catalog bridge operational views.

This is a side-effect-free readiness probe. Without a database URL it verifies
that the canonical schema declares the expected catalog bridge views. With
DATABASE_URL or --database-url it also checks live Postgres view presence and
row counts.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._config import CATALOG_OPERATIONAL_VIEWS, DEFAULT_DATABASE_URL_ENV

DEFAULT_SCHEMA_SQL = ROOT / "db" / "postgres" / "schema.sql"
VALID_VIEW_NAME_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _schema_view_presence(schema_sql: str | Path) -> list[dict[str, Any]]:
    path = Path(schema_sql)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    lowered = text.lower()
    return [
        {
            "name": view,
            "present": f"create or replace view {view.lower()}" in lowered,
        }
        for view in CATALOG_OPERATIONAL_VIEWS
    ]


def _database_view_probe(database_url: str, views: tuple[str, ...]) -> dict[str, Any]:
    try:
        import psycopg  # type: ignore[import-not-found]
    except Exception as exc:
        return {
            "mode": "driver_unavailable",
            "configured": True,
            "driver_available": False,
            "views": [],
            "counts": {},
            "error": f"{type(exc).__name__}: {exc}",
        }

    probe: dict[str, Any] = {
        "mode": "database",
        "configured": True,
        "driver_available": True,
        "views": [],
        "counts": {},
        "error": None,
    }
    try:
        with psycopg.connect(database_url, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.views
                    WHERE table_schema = current_schema()
                      AND table_name = ANY(%s)
                    """,
                    (list(views),),
                )
                present = {str(row[0]) for row in cur.fetchall()}
                probe["views"] = [
                    {"name": view, "present": view in present}
                    for view in views
                ]
                for view in views:
                    if view not in present:
                        continue
                    if not VALID_VIEW_NAME_RE.fullmatch(view):
                        raise ValueError(f"invalid view name from registry: {view!r}")
                    cur.execute(f"SELECT count(*) FROM {view}")
                    row = cur.fetchone()
                    probe["counts"][view] = int(row[0]) if row else 0
    except Exception as exc:
        probe["mode"] = "database_error"
        probe["error"] = f"{type(exc).__name__}: {exc}"
    return probe


def probe_catalog_operational_views(
    *,
    schema_sql: str | Path = DEFAULT_SCHEMA_SQL,
    database_url: str = "",
    require_database: bool = False,
    require_views: bool = False,
) -> dict[str, Any]:
    schema_views = _schema_view_presence(schema_sql)
    database_probe = (
        _database_view_probe(database_url, CATALOG_OPERATIONAL_VIEWS)
        if database_url
        else {
            "mode": "not_configured",
            "configured": False,
            "driver_available": False,
            "views": [],
            "counts": {},
            "error": None,
        }
    )
    schema_ready = all(view["present"] for view in schema_views)
    database_ready = (
        database_probe.get("mode") == "database"
        and all(view.get("present") for view in database_probe.get("views") or [])
    )
    ok = schema_ready and (database_ready if require_database else True)
    if require_views and database_probe.get("mode") == "database":
        ok = ok and all(int(count) > 0 for count in (database_probe.get("counts") or {}).values())
    return {
        "ok": bool(ok),
        "generated_at": _utc_now(),
        "schema_sql": str(Path(schema_sql)),
        "expected_views": list(CATALOG_OPERATIONAL_VIEWS),
        "schema_views": schema_views,
        "schema_ready": schema_ready,
        "database_probe": database_probe,
        "database_ready": database_ready,
        "requirements": {
            "require_database": require_database,
            "require_views": require_views,
        },
        "readiness_status": "ready" if ok else "not_ready",
        "safety_notes": [
            "The probe is read-only.",
            "Without a database URL it verifies canonical schema declarations only.",
            "With a database URL it checks view presence and row counts.",
        ],
    }


def _self_test() -> int:
    result = probe_catalog_operational_views()
    assert result["ok"] is True
    assert result["schema_ready"] is True
    assert result["database_probe"]["mode"] == "not_configured"
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe catalog bridge operational views.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--schema-sql", default=str(DEFAULT_SCHEMA_SQL))
    parser.add_argument("--database-url", default=os.environ.get(DEFAULT_DATABASE_URL_ENV, ""))
    parser.add_argument("--require-database", action="store_true")
    parser.add_argument("--require-views", action="store_true", help="Require live database view counts to be non-zero.")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    result = probe_catalog_operational_views(
        schema_sql=args.schema_sql,
        database_url=args.database_url,
        require_database=args.require_database,
        require_views=args.require_views,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
