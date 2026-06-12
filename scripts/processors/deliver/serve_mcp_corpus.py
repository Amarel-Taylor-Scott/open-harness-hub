#!/usr/bin/env python3
"""Backs `processor/serve-mcp-corpus` (process_kind ``deliver.mcp_serve``).

Live-serve a governed corpus + its tools over MCP — the default consumption
surface. This processor builds the complete, validated SERVER DESCRIPTOR
(server name, resource list from the corpus, tool list, tier policy) and
hands it to an INJECTED server runtime (``start_server(descriptor) ->
{"endpoint": ...}``). Without a runtime the call returns the descriptor with
an honest ``started: False`` — a descriptor is real output (it is what the
runtime consumes), but an ENDPOINT is never faked.

Only ``status: published`` documents become MCP resources; tools are
metadata passed through verbatim; every exclusion is reported.

Contract: side_effects=external_call (runtime lane); on_error=raise.
Inputs corpus, tools → output mcp_endpoint.

CLI / self-test: python3 scripts/processors/deliver/serve_mcp_corpus.py
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

PUBLISHABLE_STATUS = "published"
HELD_OUT_NOT_PUBLISHED = "status is not 'published' — candidates are never served over MCP"

#: MCP server names: kebab-case (matches the client config convention).
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

#: Resource URI scheme for corpus documents.
RESOURCE_SCHEME = "corpus://"

HASH_ALGORITHM = "sha256"
DESCRIPTOR_HASH_PREFIX = "mcpd:"


def build_descriptor(corpus: dict[str, Any], tools: list[dict[str, Any]]) -> dict[str, Any]:
    """The deterministic half: corpus + tools → a validated MCP server descriptor."""
    if not isinstance(corpus, dict):
        raise TypeError("corpus must be a dict")
    name = corpus.get("server_name", "")
    if not isinstance(name, str) or not _NAME_RE.match(name):
        raise ValueError(f"server_name must be kebab-case, got {name!r}")
    docs = corpus.get("documents")
    if not isinstance(docs, list):
        raise TypeError("corpus.documents must be a list")
    resources: list[dict[str, Any]] = []
    held_out: list[dict[str, Any]] = []
    for i, d in enumerate(docs):
        if not isinstance(d, dict) or "id" not in d:
            raise ValueError(f"documents[{i}] needs id")
        if d.get("status") != PUBLISHABLE_STATUS:
            held_out.append({"id": d["id"], "reason": HELD_OUT_NOT_PUBLISHED})
            continue
        resources.append({"uri": f"{RESOURCE_SCHEME}{name}/{d['id']}",
                          "name": str(d.get("title", d["id"])),
                          "mimeType": "text/markdown",
                          "source_handle": d.get("source_handle")})
    for i, t in enumerate(tools):
        if not isinstance(t, dict) or "name" not in t:
            raise ValueError(f"tools[{i}] needs name")
    descriptor = {
        "server_name": name,
        "resources": resources,
        "tools": tools,
        "policy": {"tier_negotiated": True, "cdc_fresh": bool(corpus.get("cdc_enabled", False)),
                   "metered": True, "serves_truth_via": "verification rail (resources carry source handles)"},
        "held_out": held_out,
    }
    digest = hashlib.new(HASH_ALGORITHM,
                         json.dumps(descriptor, sort_keys=True).encode("utf-8")).hexdigest()
    descriptor["descriptor_hash"] = DESCRIPTOR_HASH_PREFIX + digest[:24]
    return descriptor


def run(*, corpus: dict[str, Any], tools: list[dict[str, Any]] | None = None,
        start_server: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build the descriptor; start it via the injected runtime when given."""
    descriptor = build_descriptor(corpus, tools or [])
    if start_server is None:
        return {"mcp_endpoint": {"endpoint": None, "started": False,
                                 "descriptor": descriptor,
                                 "note": "no server runtime injected — descriptor is real, an endpoint is never faked"}}
    receipt = start_server(descriptor)
    endpoint = receipt.get("endpoint") if isinstance(receipt, dict) else None
    if not endpoint:
        raise ValueError("runtime returned no endpoint — serving unconfirmed, not faked")
    return {"mcp_endpoint": {"endpoint": str(endpoint), "started": True,
                             "descriptor": descriptor}}


def _selftest() -> None:
    corpus = {
        "server_name": "reg-e-corpus", "cdc_enabled": True,
        "documents": [
            {"id": "rule", "title": "The 10-day rule", "status": "published",
             "source_handle": "ctx://reg-e/1005.11"},
            {"id": "draft", "status": "candidate"},
        ],
    }
    tools = [{"name": "lookup_rule", "description": "Exact statute lookup"}]
    # Descriptor lane (no runtime): complete + honest about not serving.
    pv = run(corpus=corpus, tools=tools)["mcp_endpoint"]
    assert pv["started"] is False and pv["endpoint"] is None
    d = pv["descriptor"]
    assert d["resources"][0]["uri"] == "corpus://reg-e-corpus/rule"
    assert d["resources"][0]["source_handle"] == "ctx://reg-e/1005.11"
    assert d["policy"]["cdc_fresh"] is True and d["tools"] == tools
    # Governance: the candidate is not a resource and the exclusion is recorded.
    assert len(d["resources"]) == 1
    assert d["held_out"] == [{"id": "draft", "reason": HELD_OUT_NOT_PUBLISHED}]
    # Runtime lane: endpoint comes from the runtime, never invented.
    started: list[dict] = []
    def runtime(desc: dict) -> dict:
        started.append(desc)
        return {"endpoint": "http://127.0.0.1:9424/mcp/reg-e-corpus"}
    live = run(corpus=corpus, tools=tools, start_server=runtime)["mcp_endpoint"]
    assert live["started"] is True and live["endpoint"].endswith("/mcp/reg-e-corpus")
    assert started[0]["descriptor_hash"] == d["descriptor_hash"]  # same deterministic descriptor
    # Endpoint-less runtime raises; bad names/docs raise.
    for bad in (
        lambda: run(corpus=corpus, tools=tools, start_server=lambda d: {}),
        lambda: run(corpus={"server_name": "Bad Name", "documents": []}),
        lambda: run(corpus={"server_name": "ok", "documents": [{}]}),
    ):
        raised = False
        try:
            bad()
        except ValueError:
            raised = True
        assert raised
    # Deterministic descriptor hash.
    assert run(corpus=corpus, tools=tools)["mcp_endpoint"]["descriptor"]["descriptor_hash"] == d["descriptor_hash"]
    print("PASS — serve_mcp_corpus: validated MCP descriptor (published-only resources "
          "with source handles, verbatim tools, tier/CDC policy), injected runtime for "
          "the real endpoint, honest not-started preview verified")


if __name__ == "__main__":
    _selftest()
