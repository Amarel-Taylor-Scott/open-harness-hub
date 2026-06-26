#!/usr/bin/env python3
"""Seed the context-layer GAP families the PMF analysis surfaced (docs/strategy/context-layer-pmf.md):
MEMORY (Mem0/Hindsight/Zep/Letta-style) · CACHING (prompt/semantic/KV) · retrieval additions
(graph-RAG · LLMLingua compression · agentic-grep) · MCP connectors (Confluence/GitLab/Postgres).

These are GOVERNED component wrappers — OHH doesn't replace Mem0/Qdrant/LLMLingua, it makes them
swappable, measured-lift, provenance-carrying components under one contract. Shared standardized
builder; spec-level (lifecycle=experimental).

    python3 -m scripts.seed.context_layer_components
    python3 scripts/validate.py catalog/processors/memory/*.yaml catalog/processors/cache/*.yaml catalog/processors/connectors/*.yaml
"""
from __future__ import annotations

from scripts.seed.component_seed import processor, write_batch

DOC = "docs/strategy/context-layer-pmf.md"
LABEL = "OpenHubForAI context-layer taxonomy"

# MEMORY — persist what was LEARNED across sessions (not raw history). (catalog/processors/memory/)
MEMORY = [
    ("memory-distilled-write", "Distilled memory write", "memory.write_kb", ["memory"], False, "write",
     ["turns"], ["facts"],
     "Distill a conversation/run into durable facts (Mem0-style selective extraction — ~1.8k tokens/convo) "
     "and write them to the memory store: stores what was LEARNED, not raw history."),
    ("memory-temporal-graph", "Temporal-graph memory", "memory.temporal_graph", ["memory", "governance"], False, "write",
     ["event"], ["graph_delta"],
     "Write facts into a TEMPORAL knowledge graph (Zep/Graphiti-style) with validity intervals — answers "
     "'what was true when' and supersedes facts as they change."),
    ("memory-agentic-hierarchy", "Agentic memory hierarchy", "memory.agentic", ["memory", "agent_loop"], True, "write",
     ["context", "store"], ["paged"],
     "Agent-controlled working / long-term memory hierarchy (Letta/MemGPT-style): the agent pages facts "
     "between the context window and long-term store to stay within budget on long-running tasks."),
    ("memory-recall", "Memory recall", "memory.recall", ["memory", "retrieval"], False, "read",
     ["query", "store"], ["memories"],
     "Recall the memories relevant to the current turn (semantic + recency over the memory store)."),
    ("memory-reflect", "Memory reflect", "memory.reflect", ["memory", "reasoning"], False, "read",
     ["query", "memories"], ["synthesis"],
     "Reflect across recalled memories to produce a coherent synthesis (Hindsight-style reflect()), not a "
     "ranked list of facts — distilled knowledge for the prompt."),
    ("memory-confidence-track", "Memory confidence tracking", "memory.belief", ["memory", "governance"], True, "write",
     ["claim", "evidence"], ["belief"],
     "Track confidence / belief per fact, updating as evidence arrives, and separate fact from opinion "
     "(Hindsight opinion-network style) — governed memory, not blind retention."),
]

# CACHING — don't pay twice for the same tokens. (catalog/processors/cache/)
CACHE = [
    ("cache-prompt-prefix", "Prompt-prefix cache", "cache.prompt_prefix", ["memory"], True, "read",
     ["prompt"], ["cache_hint"],
     "Mark the stable prompt prefix (persona + system + tool schemas) for provider prompt caching "
     "(~90% read discount on Anthropic, automatic >1,024 tokens on OpenAI). Turn on first — free."),
    ("cache-semantic", "Semantic response cache", "cache.semantic", ["memory", "retrieval"], False, "read",
     ["query", "threshold"], ["hit"],
     "Semantic response cache (GPTCache-style): a paraphrase of a prior query hits the same entry "
     "(~61-69% hit rate). NEVER cache personalized/user-specific responses (wrong-user risk)."),
    ("cache-exact", "Exact response cache", "cache.exact_hash", ["memory"], True, "read",
     ["key"], ["hit"],
     "Exact-hash response cache keyed by (task, components, inputs) — identical runs return instantly at "
     "zero model cost. Deterministic; freezable."),
    ("cache-kv-reuse", "KV-cache reuse", "cache.kv_reuse", ["memory", "serving"], True, "read",
     ["prefix"], ["kv"],
     "KV-cache reuse across calls (LMCache-style) for self-hosted inference — up to ~7x faster "
     "time-to-first-token on shared prefixes."),
]

# RETRIEVAL additions — round out the retrieval layer. (catalog/processors/retrieval/)
RETRIEVAL = [
    ("graphrag-retrieve", "GraphRAG retrieve", "retrieve.graph", ["retrieval", "reasoning"], False, "read",
     ["query", "graph"], ["subgraph"],
     "Knowledge-graph (GraphRAG) retrieval: follow explicit relationship chains for multi-hop + corpus-wide "
     "sensemaking that naive vector RAG misses (wins ~70-80% of complex sensemaking). Add only when the "
     "retriever genuinely can't follow a relationship — heavier build/compute."),
    ("llmlingua-compress", "LLMLingua compress", "summarize.llmlingua", ["summarization"], False, "none",
     ["context", "ratio"], ["compressed"],
     "LLMLingua prompt compression: a small model drops low-information tokens (up to ~20x); LongLLMLingua "
     "mitigates 'lost in the middle'. MEASURE the breakeven — gains only when length/ratio/hardware match."),
    ("grep-agentic-retrieve", "Agentic grep retrieve", "retrieve.grep_agentic", ["retrieval"], True, "read",
     ["pattern", "corpus"], ["matches"],
     "Agentic regex/grep retrieval (ripgrep-style, as Claude Code does): exact, no index, private; ~90% of "
     "RAG quality on well-named corpora (Amazon 'Keyword Search Is All You Need'). Costs more turns; pair "
     "with a vector leg for the mature hybrid."),
]

# MCP CONNECTORS — bring the team's doc sources in as governed corpora. (catalog/processors/connectors/)
CONNECTORS = [
    ("mcp-confluence-connector", "MCP connector — Confluence", "connect.mcp_confluence", ["retrieval", "tool_use"], False, "external_call",
     ["space", "query"], ["pages"],
     "MCP connector to Confluence (human-readable docs): permission-aware retrieval that pulls prose context "
     "on demand into a governed corpus. Cloud = official Atlassian MCP; Data Center = community server."),
    ("mcp-gitlab-connector", "MCP connector — GitLab", "connect.mcp_gitlab", ["retrieval", "tool_use"], False, "external_call",
     ["repo", "query"], ["docs"],
     "MCP connector to GitLab (technical docs / repos / MRs): read-scoped; pulls versioned technical context. "
     "Treat retrieved content as untrusted input (prompt-injection); prefer read-only mode."),
    ("mcp-postgres-connector", "MCP connector — Postgres/pgvector", "connect.mcp_postgres", ["retrieval", "tool_use"], False, "external_call",
     ["query"], ["rows"],
     "MCP connector to a Postgres / pgvector store: query operational + vector data as governed context, "
     "co-located with the platform's own stores."),
]


def main() -> int:
    def mk(specs, tags, prefix):
        return [processor(*c, tags=tags, source_doc=DOC, source_label=LABEL, impl_prefix=prefix) for c in specs]
    n = 0
    n += len(write_batch("catalog/processors/memory", mk(MEMORY, ("context-layer", "memory"), "scripts.processors.memory")))
    n += len(write_batch("catalog/processors/cache", mk(CACHE, ("context-layer", "cache"), "scripts.processors.cache")))
    n += len(write_batch("catalog/processors/retrieval", mk(RETRIEVAL, ("context-layer", "retrieval"), "scripts.processors.retrieval")))
    n += len(write_batch("catalog/processors/connectors", mk(CONNECTORS, ("context-layer", "connector", "mcp"), "scripts.processors.connectors")))
    print(f"wrote {n} context-layer components (memory + cache + retrieval + connectors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
