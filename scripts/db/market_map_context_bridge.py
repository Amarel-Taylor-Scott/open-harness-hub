#!/usr/bin/env python3
"""Emit database-shaped context rows from the Baltor adjacent-market map.

The market map is a strategy/review artifact. This bridge keeps it from
becoming an unstructured side channel by emitting reviewable JSONL rows for
provider contracts and market-watchlist context objects. It does not connect to
Postgres and it does not mutate source documents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parent.parent.parent
DEFAULT_SOURCE = REPO / "docs" / "strategy" / "baltor-adjacent-market-map.md"
DEFAULT_OUT = REPO / "dist" / "market-map-context-bridge"
TENANT_ID = "baltor"
ACL_ID = "acl://baltor/strategy/internal"
CLASSIFICATION = "internal"


MARKET_CATEGORIES: list[dict[str, Any]] = [
    {
        "category_id": "agent-memory-context-layers",
        "title": "Agent memory and context layers",
        "summary": "Persistent memory across agents, apps, and conversations.",
        "relationship": "adjacent_competitor_or_provider",
    },
    {
        "category_id": "codebase-context-repo-intelligence",
        "title": "Codebase context and repo intelligence",
        "summary": "Repo maps, generated docs, semantic code search, and PR context.",
        "relationship": "engineering_pack_provider_or_competitor",
    },
    {
        "category_id": "enterprise-search-work-graphs",
        "title": "Enterprise search and work graphs",
        "summary": "Permission-aware broad company search over docs and apps.",
        "relationship": "broad_retrieval_provider_or_substitute",
    },
    {
        "category_id": "mcp-gateways-tool-infrastructure",
        "title": "MCP gateways and tool infrastructure",
        "summary": "Agent tool access, auth, action governance, and deployment.",
        "relationship": "complementary_gateway_layer",
    },
    {
        "category_id": "rag-retrieval-platforms",
        "title": "RAG and retrieval platforms",
        "summary": "Ingestion, chunking, embeddings, hybrid retrieval, and reranking.",
        "relationship": "retrieval_backend_provider",
    },
    {
        "category_id": "graph-vector-context-databases",
        "title": "Graph, vector, and context databases",
        "summary": "Relationship-rich storage and vector/graph traversal.",
        "relationship": "infrastructure_backend",
    },
    {
        "category_id": "architecture-service-catalogs",
        "title": "Architecture and service catalogs",
        "summary": "Services, owners, dependencies, diagrams, flows, and APIs.",
        "relationship": "high_authority_context_provider",
    },
    {
        "category_id": "data-agent-semantic-layers",
        "title": "Data-agent semantic layers",
        "summary": "Warehouse, BI, metric, and data-document context.",
        "relationship": "domain_specific_context_layer",
    },
    {
        "category_id": "docs-generation-docs-repair",
        "title": "Docs generation and docs repair",
        "summary": "AI-optimized docs, repo wikis, and knowledge-base gap detection.",
        "relationship": "derived_artifact_provider",
    },
    {
        "category_id": "agent-observability-evals",
        "title": "Agent observability and evals",
        "summary": "Traces, tool calls, cost, failures, and quality monitoring.",
        "relationship": "feedback_and_evaluation_provider",
    },
    {
        "category_id": "agent-validation-review",
        "title": "Agent validation and review",
        "summary": "PR review, test generation, QA, and infrastructure review.",
        "relationship": "context_pack_consumer_and_artifact_producer",
    },
    {
        "category_id": "local-first-encrypted-knowledge",
        "title": "Local-first encrypted knowledge",
        "summary": "Markdown, local databases, encrypted sync, and private memory.",
        "relationship": "private_developer_memory_substrate",
    },
]


WATCHLIST: list[tuple[str, str, str, str]] = [
    ("Hyperspell", "Agent memory/context layer", "local_memory", "memory_context_layer"),
    ("Nessie", "AI conversation memory", "local_memory", "conversation_memory_source"),
    ("Memory Store", "Shared agent memory", "local_memory", "shared_agent_memory"),
    ("Mem0", "Agent memory API", "local_memory", "memory_api_backend"),
    ("Zep / Graphiti", "Temporal context graph", "graph_store", "temporal_context_graph"),
    ("Airweave", "Open-source context retrieval", "federated_search", "connector_retrieval_layer"),
    ("Driver", "Codebase context layer", "code_intelligence", "repo_context_competitor"),
    ("Swimm", "Agentic codebase context", "code_intelligence", "repo_knowledge_provider"),
    ("Sourcebot", "Code understanding/search", "code_intelligence", "code_search_provider"),
    ("Greptile", "Codebase AI / PR review", "code_intelligence", "review_pack_competitor"),
    ("Nozomio / Nia", "MCP code/docs context", "code_intelligence", "mcp_code_context"),
    ("Kaelio", "Data-agent context layer", "industry_system", "data_context_layer"),
    ("Airbyte Context Store", "Business entity context", "source_connector", "entity_context_store"),
    ("HelixDB", "Graph-vector database", "graph_store", "graph_vector_backend"),
    ("Compresr", "Context compression", "custom", "compression_provider"),
    ("Manufact / mcp-use", "MCP infrastructure", "mcp_gateway", "mcp_infrastructure"),
    ("Clawvisor", "Agent authorization", "policy_engine", "agent_authorization"),
    ("HumanLayer", "Human approval layer", "policy_engine", "human_approval"),
    ("The Context Company", "Agent observability", "custom", "observability_provider"),
    ("RefineTrain", "Docs optimization", "repo_wiki", "docs_optimization_provider"),
    ("Outlit", "Customer context profile", "industry_system", "customer_context_layer"),
]


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def slug(value: str) -> str:
    out = []
    for char in value.lower():
        out.append(char if char.isalnum() else "-")
    return "-".join(part for part in "".join(out).split("-") if part)


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
            count += 1
    return count


def source_fingerprint(path: Path) -> str:
    return sha256_text(path.read_text(encoding="utf-8"))


def provider_row(item: tuple[str, str, str, str], *, now: str, source: Path, fingerprint: str) -> dict[str, Any]:
    name, segment, provider_type, relationship = item
    provider_id = f"market-provider/{slug(name)}"
    return {
        "kind": "baltor.context-provider",
        "provider_id": provider_id,
        "name": name,
        "provider_type": provider_type,
        "source_systems": ["market_watchlist"],
        "capabilities": {
            "discover": True,
            "fetch": provider_type in {"source_connector", "enterprise_search", "repo_wiki", "code_intelligence"},
            "search": provider_type in {"federated_search", "enterprise_search", "code_intelligence", "repo_wiki", "graph_store"},
            "relationships": provider_type in {"graph_store", "architecture_context", "code_intelligence", "industry_system"},
            "permissions": provider_type in {"enterprise_search", "policy_engine", "mcp_gateway"},
            "subscribe": False,
            "actions": provider_type in {"mcp_gateway", "policy_engine"},
            "embeddings": provider_type in {"vector_index", "graph_store", "federated_search"},
            "artifact_generation": provider_type in {"repo_wiki", "code_intelligence", "custom"},
        },
        "connector_modes": ["link_only"],
        "supported_triggers": ["manual", "scheduled_poll"],
        "object_types": ["market_watchlist_provider", "market_intelligence_claim"],
        "auth": {"mode": "none", "delegates_source_permissions": False},
        "policy": {
            "acl_filter_before_model": True,
            "raw_source_access": "exact_handle_only",
            "writes_require_approval": True,
            "derived_context": True,
        },
        "interfaces": [{"kind": "custom", "uri": str(source.relative_to(REPO))}],
        "facets": {
            "segment": segment,
            "relationship": relationship,
            "source_fingerprint": fingerprint,
            "review_status": "strategy_watchlist",
        },
        "created_at": now,
        "updated_at": now,
    }


def context_object_row(
    object_id: str,
    *,
    object_type: str,
    subkind: str,
    title: str,
    summary: str,
    native_id: str,
    source: Path,
    source_hash: str,
    facets: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    source_path = str(source.relative_to(REPO))
    return {
        "context_object_id": object_id,
        "tenant_id": TENANT_ID,
        "object_type": object_type,
        "subkind": subkind,
        "title": title,
        "summary": summary,
        "source_system": "baltor_strategy_market_map",
        "native_id": native_id,
        "source_url": source_path,
        "current_version_id": f"{object_id}@{source_hash}",
        "acl_id": ACL_ID,
        "classification": CLASSIFICATION,
        "source_handles": [
            f"ctx://baltor/strategy/adjacent-market-map#{native_id}",
            source_path,
        ],
        "facets": facets,
        "five_w_one_h": {
            "what": object_type,
            "why": "Track adjacent market intelligence as database-addressable context.",
            "where": source_path,
            "when": now,
            "who": "baltor.strategy",
            "how": "Generated from the adjacent market map bridge.",
        },
        "dimension_summary": {
            "freshness": "review_before_external_use",
            "source_quality": "strategy_review_artifact",
            "operational_truth": "database_row_after_load",
        },
        "document": {
            "source_hash": source_hash,
            "review_note": "Vendor claims and funding status are volatile and must be refreshed before publication or sales use.",
        },
        "created_at": now,
        "updated_at": now,
    }


def build_rows(source: Path = DEFAULT_SOURCE) -> dict[str, list[dict[str, Any]]]:
    now = utc_now()
    fingerprint = source_fingerprint(source)
    providers = [provider_row(item, now=now, source=source, fingerprint=fingerprint) for item in WATCHLIST]
    provider_objects = [
        context_object_row(
            f"ctx://baltor/market/provider/{slug(item[0])}",
            object_type="market_watchlist_provider",
            subkind=item[2],
            title=item[0],
            summary=f"{item[0]} is tracked as {item[1]} for Baltor positioning and provider strategy.",
            native_id=f"provider-{slug(item[0])}",
            source=source,
            source_hash=fingerprint,
            facets={"segment": item[1], "provider_type": item[2], "relationship": item[3]},
            now=now,
        )
        for item in WATCHLIST
    ]
    category_objects = [
        context_object_row(
            f"ctx://baltor/market/category/{item['category_id']}",
            object_type="market_category",
            subkind=item["relationship"],
            title=item["title"],
            summary=item["summary"],
            native_id=f"category-{item['category_id']}",
            source=source,
            source_hash=fingerprint,
            facets={"relationship": item["relationship"]},
            now=now,
        )
        for item in MARKET_CATEGORIES
    ]
    return {
        "context_providers": providers,
        "context_objects": [*provider_objects, *category_objects],
    }


def write_bridge(output_dir: Path = DEFAULT_OUT, source: Path = DEFAULT_SOURCE) -> dict[str, Any]:
    rows = build_rows(source)
    counts = {
        "context_providers": write_jsonl(output_dir / "context_providers.jsonl", rows["context_providers"]),
        "context_objects": write_jsonl(output_dir / "context_objects.jsonl", rows["context_objects"]),
    }
    plan = {
        "ok": True,
        "generated_at": utc_now(),
        "source": str(source.relative_to(REPO)),
        "source_hash": source_fingerprint(source),
        "output_dir": str(output_dir),
        "counts": counts,
        "files": {
            "context_providers": str(output_dir / "context_providers.jsonl"),
            "context_objects": str(output_dir / "context_objects.jsonl"),
        },
        "safety_notes": [
            "This bridge does not connect to Postgres.",
            "It does not mutate strategy documents or catalog manifests.",
            "Generated market rows are internal strategy context; refresh volatile vendor claims before external use.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "market-map-context-bridge-plan.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return plan


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        plan = write_bridge(output_dir=Path(tmp), source=DEFAULT_SOURCE)
        assert plan["counts"]["context_providers"] == len(WATCHLIST), plan
        assert plan["counts"]["context_objects"] == len(WATCHLIST) + len(MARKET_CATEGORIES), plan
        provider = json.loads((Path(tmp) / "context_providers.jsonl").read_text(encoding="utf-8").splitlines()[0])
        assert provider["kind"] == "baltor.context-provider", provider
        assert provider["policy"]["acl_filter_before_model"] is True, provider
        context_object = json.loads((Path(tmp) / "context_objects.jsonl").read_text(encoding="utf-8").splitlines()[0])
        assert context_object["object_type"] == "market_watchlist_provider", context_object
        assert context_object["classification"] == CLASSIFICATION, context_object
    print(json.dumps({"ok": True, "providers": len(WATCHLIST), "categories": len(MARKET_CATEGORIES)}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit market-map context provider and context-object rows.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    source = args.source if args.source.is_absolute() else REPO / args.source
    output_dir = args.output_dir if args.output_dir.is_absolute() else REPO / args.output_dir
    plan = write_bridge(output_dir=output_dir, source=source)
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
