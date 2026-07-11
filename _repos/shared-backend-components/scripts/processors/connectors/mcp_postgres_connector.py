#!/usr/bin/env python3
"""Backs `processor/mcp-postgres-connector` (process_kind ``connect.mcp_postgres``).

MCP connector to a Postgres / pgvector store: run a READ-ONLY query and pull
operational + vector rows as governed context candidates. The MCP transport
is INJECTED; the connector enforces the read-only law ITSELF (a statement
that is not a single SELECT/WITH is refused before any transport call — the
defense does not rely on the server), caps row counts, and stamps every row
batch with the query hash as its source handle.

Contract: side_effects=external_call; on_error=raise.
Input query → output rows.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/connectors/mcp_postgres_connector.py
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: The MCP tool this connector invokes.
MCP_QUERY_TOOL = "postgres_query"

#: Read-only statement shape: exactly one statement, starting SELECT or WITH.
#: Everything else (INSERT/UPDATE/DELETE/DDL, stacked statements, COPY) is
#: refused HERE, before the transport sees it.
_READONLY_RE = re.compile(r"^\s*(?:select|with)\b", re.IGNORECASE)
_FORBIDDEN_RE = re.compile(
    r"\b(?:insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|vacuum)\b",
    re.IGNORECASE)

MAX_ROWS = 500

HASH_ALGORITHM = "sha256"
QUERY_HANDLE_PREFIX = "pgq:"
QUERY_HANDLE_HEX_LEN = 16


def validate_readonly(query: str) -> None:
    """Raise unless ``query`` is a single read-only SELECT/WITH statement."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty SQL string")
    body = query.strip().rstrip(";")
    if ";" in body:
        raise ValueError("multiple statements are refused — one read-only SELECT only")
    if not _READONLY_RE.match(body):
        raise ValueError("only SELECT/WITH statements are allowed (read-only connector)")
    if _FORBIDDEN_RE.search(body):
        raise ValueError("write/DDL keywords are refused even inside a SELECT-looking text")


def run(*, query: str,
        call_tool: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
        max_rows: int = MAX_ROWS) -> dict[str, Any]:
    """Run the read-only ``query`` via the injected MCP transport."""
    validate_readonly(query)
    if not isinstance(max_rows, int) or not 1 <= max_rows <= MAX_ROWS:
        raise ValueError(f"max_rows must be 1..{MAX_ROWS}, got {max_rows!r}")
    if call_tool is None:
        raise RuntimeError("mcp_postgres_connector requires an injected MCP transport "
                           "(call_tool=(tool, arguments) -> result); rows are never faked")
    result = call_tool(MCP_QUERY_TOOL, {"query": query.strip(), "limit": max_rows})
    raw = result.get("rows") if isinstance(result, dict) else None
    if not isinstance(raw, list):
        raise ValueError("MCP transport returned no rows[] — malformed server response")
    truncated = len(raw) > max_rows
    rows = raw[:max_rows]
    handle = QUERY_HANDLE_PREFIX + hashlib.new(
        HASH_ALGORITHM, query.strip().encode("utf-8")).hexdigest()[:QUERY_HANDLE_HEX_LEN]
    return {"rows": {"rows": rows, "row_count": len(rows), "truncated": truncated,
                     "source_handle": handle, "query": query.strip(),
                     "scope": "read_only", "serves_truth": False}}


def _selftest() -> None:
    calls: list[dict] = []

    def transport(tool: str, arguments: dict) -> dict:
        calls.append({"tool": tool, **arguments})
        return {"rows": [{"id": 1, "component": "processor/cache-exact", "score": 0.97},
                         {"id": 2, "component": "processor/rrf-fusion", "score": 0.94}]}

    out = run(query="SELECT id, component, score FROM object_embedding LIMIT 10",
              call_tool=transport)["rows"]
    assert calls[0]["tool"] == MCP_QUERY_TOOL
    assert out["row_count"] == 2 and out["rows"][0]["component"] == "processor/cache-exact"
    # Source handle is the query hash — stable, citable.
    assert out["source_handle"].startswith(QUERY_HANDLE_PREFIX)
    assert out["source_handle"] == run(query="SELECT id, component, score FROM object_embedding LIMIT 10",
                                       call_tool=transport)["rows"]["source_handle"]
    # Read-only law enforced HERE, before any transport call: every shape refused.
    for evil in ("DELETE FROM object_embedding",
                 "SELECT 1; DROP TABLE object_embedding",
                 "WITH x AS (SELECT 1) UPDATE t SET a=1",
                 "  insert into t values (1)",
                 ""):
        raised = False
        try:
            run(query=evil, call_tool=transport)
        except ValueError:
            raised = True
        assert raised, evil
    assert len(calls) == 2  # the refusals never reached the transport
    # WITH-led reads pass; candidates never truth; scope pinned.
    w = run(query="WITH recent AS (SELECT * FROM runs) SELECT count(*) FROM recent",
            call_tool=transport)["rows"]
    assert w["scope"] == "read_only" and w["serves_truth"] is False
    # Truncation is reported, never silent.
    big = run(query="SELECT 1", call_tool=lambda t, a: {"rows": [{"n": i} for i in range(600)]},
              max_rows=500)["rows"]
    assert big["truncated"] is True and big["row_count"] == 500
    # No transport / malformed response refuse.
    for bad in (lambda: run(query="SELECT 1"),
                lambda: run(query="SELECT 1", call_tool=lambda t, a: {})):
        raised = False
        try:
            bad()
        except (RuntimeError, ValueError):
            raised = True
        assert raised
    print("PASS — mcp_postgres_connector: connector-side read-only law (single "
          "SELECT/WITH, write/DDL refused pre-transport), query-hash source handles, "
          "reported truncation, rows never faked verified")


if __name__ == "__main__":
    _selftest()
