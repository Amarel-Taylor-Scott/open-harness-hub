#!/usr/bin/env python3
"""Proof for Teleon's outbound-traffic evidence graph.

The owner asked for a new layer that captures outgoing worker traffic/searches
and puts it in a searchable graph per query. This check proves the local
correctness slice: every outbound observation is redacted, append-only,
tenant-scoped, graph-projected, searchable by query/worker/destination, and
truth-free.
"""
from __future__ import annotations

import json
from src.teleon.runtime.tenancy import INTERNAL_TENANT_ID
import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from src.teleon.egress.traffic_graph import (
    EGRESS_SERVES_TRUTH,
    GRAPH_SCHEMA_VERSION,
    LocalEgressGraph,
    SCHEMA_VERSION,
    TeleonEgressGraphRejected,
    make_egress_observation,
)


def _obs(**overrides):
    base = {
        "tenant_id": INTERNAL_TENANT_ID,
        "run_id": "run-ph-license-2026-06-14",
        "worker_id": "worker-ph-license-watchtower",
        "worker_kind": "official-source-fetcher",
        "query_text": "Island Recruiters licensed employment agency Philippines",
        "operation": "http_fetch",
        "destination_url": "https://onlineservices.dmw.gov.ph/OnlineServices/POEAOnline.aspx?api_key=fixture-secret-value&q=Island+Recruiters",
        "started_at": "2026-06-14T02:10:00Z",
        "completed_at": "2026-06-14T02:10:01Z",
        "tool_name": "source.fetch.official_registry_with_receipt",
        "request": {
            "method": "GET",
            "headers": {"Authorization": "Bearer abcdef0123456789abcdef", "Accept": "text/html"},
            "url": "https://onlineservices.dmw.gov.ph/OnlineServices/POEAOnline.aspx?token=fixture-token-value&q=Island+Recruiters",
        },
        "response": {"status_code": 200, "content_type": "text/html", "bytes": 42117,
                     "body_hash": "sha256:dmw-fixture"},
        "status": "ok",
        "trace_id": "trace-ph-license",
    }
    base.update(overrides)
    return make_egress_observation(**base)


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    store = LocalEgressGraph(":memory:")
    first = _obs()
    second = _obs(
        worker_id="worker-dole-advisory-search",
        worker_kind="search-worker",
        operation="web_search",
        destination_url="https://www.dole.gov.ph/search?s=Island+Recruiters&client_secret=fixture-client-secret",
        tool_name="source.search.official_advisory_candidates",
        response={"status_code": 403, "content_type": "text/html", "bytes": 8200,
                  "body_hash": "sha256:dole-cloudflare-challenge"},
        status="source_unavailable_requires_browser",
        started_at="2026-06-14T02:10:02Z",
        completed_at="2026-06-14T02:10:03Z",
    )
    third = _obs(
        tenant_id="other-tenant",
        run_id="run-other",
        worker_id="worker-other",
        destination_url="https://vendor.example.com/search?q=Island+Recruiters",
        tool_name="vendor.search",
        started_at="2026-06-14T02:11:00Z",
        completed_at="2026-06-14T02:11:01Z",
    )

    out1 = store.append(first)
    store.append(second)
    store.append(third)
    store.append(first)  # idempotent retry

    check("observations use the Teleon egress schema", out1["schema_version"] == SCHEMA_VERSION)
    check("egress evidence never serves truth", out1["serves_truth"] is False and EGRESS_SERVES_TRUTH is False)
    blob = json.dumps(store.graph_for_query(tenant_id=INTERNAL_TENANT_ID, text="Island Recruiters"), sort_keys=True)
    check("URL query credentials and authorization headers are redacted",
          "fixture-secret-value" not in blob and "Bearer abcdef" not in blob
          and "fixture-client-secret" not in blob, blob)
    check("redacted destination preserves the authoritative host for graph search",
          "onlineservices.dmw.gov.ph" in blob and "www.dole.gov.ph" in blob, blob)

    by_query = store.search_events(tenant_id=INTERNAL_TENANT_ID, text="Island Recruiters")
    check("tenant-scoped query search returns both Baltor egress events only",
          len(by_query) == 2 and {e["worker_id"] for e in by_query} == {
              "worker-ph-license-watchtower", "worker-dole-advisory-search"}, str(by_query))
    check("destination-host search works",
          len(store.search_events(tenant_id=INTERNAL_TENANT_ID, destination_host="onlineservices.dmw.gov.ph")) == 1)
    check("worker search works",
          store.search_events(tenant_id=INTERNAL_TENANT_ID, worker_id="worker-dole-advisory-search")[0]["status"]
          == "source_unavailable_requires_browser")

    graph = store.graph_for_query(tenant_id=INTERNAL_TENANT_ID, text="Island Recruiters")
    node_types = {n["node_type"] for n in graph["nodes"]}
    edge_types = {e["edge_type"] for e in graph["edges"]}
    check("graph projection includes query/worker/tool/destination/response nodes",
          {"query", "worker", "tool", "destination", "response_digest", "egress_event"} <= node_types,
          str(node_types))
    check("graph projection includes event lineage edges",
          {"for_query", "performed_by", "used_tool", "to_destination", "returned_digest"} <= edge_types,
          str(edge_types))
    check("graph envelope is truth-free", graph["schema_version"] == GRAPH_SCHEMA_VERSION and graph["serves_truth"] is False)

    tampered = dict(first)
    tampered["status"] = "tampered"
    check("append-only guard rejects same event_id with different content",
          _raises(lambda: store.append(tampered)))
    check("tenant isolation keeps other tenant out of Baltor query graph",
          "vendor.example.com" not in blob and len(store.search_events(tenant_id="other-tenant", text="Island Recruiters")) == 1)
    check("missing tenant/query/worker/destination fields are rejected",
          _raises(lambda: make_egress_observation(**{**{
              "tenant_id": "", "run_id": "r", "worker_id": "w", "worker_kind": "k",
              "query_text": "q", "operation": "fetch", "destination_url": "https://example.com",
              "started_at": "t1", "completed_at": "t2"}, })))

    print("\n" + ("PASS - check_teleon_egress_graph: Teleon outbound fetch/search/tool calls are captured as "
                  "redacted append-only evidence, projected into a query-scoped graph, searchable by tenant/query/"
                  "worker/destination, and never marked as truth." if not failures
                  else f"{len(failures)} FAILURES: {failures}"))
    return 0 if not failures else 1


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except TeleonEgressGraphRejected:
        return True


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
