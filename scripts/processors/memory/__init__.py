"""Open Harness Hub — governed memory processors (Baltor context layer).

This package holds the deterministic implementations behind the
`catalog/processors/memory/` manifests — the memory lane of the context layer
(see `docs/strategy/context-layer-pmf.md`). Memory here is GOVERNED: every
write keeps lineage to its raw source, held-out ≠ deleted (the lossless
law, `docs/codex/lossless-distillation.md`), and nothing a processor emits
is served as truth without the verification rail.

Each manifest's `implementations[].path` resolves to a `run(...)` callable here.

Modules:
  memory_recall             — backs processor/memory-recall (memory.recall):
                              semantic + recency ranking over an injected store.
  memory_reflect            — backs processor/memory-reflect (memory.reflect):
                              Hindsight-style reflect() — a coherent synthesis
                              with lineage, not a ranked list.
  memory_distilled_write    — backs processor/memory-distilled-write
                              (memory.write_kb): Mem0-style selective extraction;
                              stores what was LEARNED with quotes + turn lineage.
  memory_agentic_hierarchy  — backs processor/memory-agentic-hierarchy
                              (memory.agentic): Letta/MemGPT-style paging between
                              the context window and the long-term store.
  memory_confidence_track   — backs processor/memory-confidence-track
                              (memory.belief): per-fact belief updated as
                              evidence arrives; fact ≠ opinion.
  memory_temporal_graph     — backs processor/memory-temporal-graph
                              (memory.temporal_graph): Zep/Graphiti-style
                              validity intervals; supersede, never delete.
"""
