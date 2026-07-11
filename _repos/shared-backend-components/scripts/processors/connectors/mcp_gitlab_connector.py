#!/usr/bin/env python3
"""Backs `processor/mcp-gitlab-connector` (process_kind ``connect.mcp_gitlab``).

Read-scoped MCP connector to GitLab: pull versioned technical context (repo
docs, README content, merge-request descriptions) into the governed corpus
as CANDIDATES. The MCP transport is INJECTED; the connector pins read-only
scope, requires a ref (branch/SHA) so every doc handle is VERSIONED, and
marks all retrieved content untrusted (the manifest's own warning:
prompt-injection rides in retrieved docs).

Contract: side_effects=external_call; on_error=raise.
Inputs repo, query → output docs.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/connectors/mcp_gitlab_connector.py
"""
from __future__ import annotations

import json
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: The MCP tool this connector invokes.
MCP_SEARCH_TOOL = "gitlab_search_docs"

#: Default ref when the caller pins none — the repo's default branch HEAD is
#: still recorded EXPLICITLY in every handle (no ref, no handle).
DEFAULT_REF = "HEAD"

MAX_DOCS = 25
SCREEN_BEFORE_USE = "processor/prompt-injection-screen"


def run(*, repo: str, query: str, ref: str = DEFAULT_REF,
        call_tool: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
        max_docs: int = MAX_DOCS) -> dict[str, Any]:
    """Search ``repo``@``ref`` for ``query`` via the injected MCP transport."""
    if not isinstance(repo, str) or "/" not in repo:
        raise ValueError(f"repo must be a group/project path, got {repo!r}")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty str")
    if not isinstance(ref, str) or not ref:
        raise ValueError("ref must be a non-empty branch/SHA (versioned handles only)")
    if not isinstance(max_docs, int) or not 1 <= max_docs <= MAX_DOCS:
        raise ValueError(f"max_docs must be 1..{MAX_DOCS}, got {max_docs!r}")
    if call_tool is None:
        raise RuntimeError("mcp_gitlab_connector requires an injected MCP transport "
                           "(call_tool=(tool, arguments) -> result); fetched-looking docs "
                           "are never faked")
    result = call_tool(MCP_SEARCH_TOOL, {"repo": repo, "query": query, "ref": ref,
                                         "limit": max_docs})
    raw = result.get("docs") if isinstance(result, dict) else None
    if not isinstance(raw, list):
        raise ValueError("MCP transport returned no docs[] — malformed server response")
    docs: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for i, d in enumerate(raw[:max_docs]):
        if not isinstance(d, dict) or not d.get("path"):
            skipped.append({"index": i, "reason": "doc without a path — no versioned handle, not intaken"})
            continue
        resolved_ref = str(d.get("ref", ref))
        docs.append({
            "path": str(d["path"]),
            "text": str(d.get("text", "")),
            "source_handle": f"{repo}@{resolved_ref}:{d['path']}",
            "ref": resolved_ref,
            "untrusted_external_content": True,
            "screen_before_use": SCREEN_BEFORE_USE,
            "serves_truth": False,
        })
    return {"docs": {"docs": docs, "skipped": skipped, "repo": repo, "ref": ref,
                     "query": query, "scope": "read_only"}}


def _selftest() -> None:
    calls: list[tuple[str, dict]] = []

    def transport(tool: str, arguments: dict) -> dict:
        calls.append((tool, arguments))
        return {"docs": [
            {"path": "docs/deploy.md", "ref": "a1b2c3d", "text": "Deploys ride the gate."},
            {"path": "README.md", "text": "Project overview."},
            {"text": "orphan content without a path"},
        ]}

    out = run(repo="platform/teleon", query="deploy gate", ref="main", call_tool=transport)["docs"]
    assert calls[0][0] == MCP_SEARCH_TOOL and calls[0][1]["ref"] == "main"
    # Handles are VERSIONED: server-provided SHA wins, else the requested ref.
    assert out["docs"][0]["source_handle"] == "platform/teleon@a1b2c3d:docs/deploy.md"
    assert out["docs"][1]["source_handle"] == "platform/teleon@main:README.md"
    # Untrusted + screen-pointed + candidate-grade on every doc.
    assert all(d["untrusted_external_content"] and d["screen_before_use"] == SCREEN_BEFORE_USE
               and d["serves_truth"] is False for d in out["docs"])
    # Path-less rows are skipped with a reason; scope pinned read-only.
    assert out["skipped"] and "no versioned handle" in out["skipped"][0]["reason"]
    assert out["scope"] == "read_only"
    # Refusals: no transport, malformed response, non-project repo string, empty ref.
    for bad in (
        lambda: run(repo="platform/teleon", query="x"),
        lambda: run(repo="platform/teleon", query="x", call_tool=lambda t, a: {}),
        lambda: run(repo="teleon", query="x", call_tool=transport),
        lambda: run(repo="platform/teleon", query="x", ref="", call_tool=transport),
    ):
        raised = False
        try:
            bad()
        except (RuntimeError, ValueError):
            raised = True
        assert raised
    assert json.dumps(run(repo="g/p", query="q", call_tool=transport), sort_keys=True) == \
           json.dumps(run(repo="g/p", query="q", call_tool=transport), sort_keys=True)
    print("PASS — mcp_gitlab_connector: injected MCP transport, VERSIONED source handles "
          "(repo@ref:path), untrusted + screen-pointed docs, read-only scope, honest "
          "refusals verified")


if __name__ == "__main__":
    _selftest()
