"""Open Harness Hub — MCP connector processors (external context intake).

This package holds the implementations behind the `catalog/processors/connectors/`
manifests: permission-aware, READ-ONLY connectors that pull external context
(Confluence prose, GitLab technical docs, Postgres rows) into the governed
corpus as CANDIDATES.

Shared rules:
  * the MCP transport is INJECTED (``call_tool(tool, arguments) -> result``);
    without one the connector refuses — fetched-looking data is never faked;
  * every returned item is marked ``untrusted_external_content: True`` and
    pointed at `processor/prompt-injection-screen` before any model sees it;
  * read-only scope is pinned structurally (the connector exposes no write);
  * results are intake CANDIDATES (``serves_truth: False``) with source
    handles — the verification rail promotes, not the connector.
"""
