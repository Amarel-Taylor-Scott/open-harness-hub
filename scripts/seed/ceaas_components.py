#!/usr/bin/env python3
"""Seed the Context-Enrichment-as-a-Service (CEaaS) governed components
(docs/strategy/context-enrichment-service.md): the content TIERS, the four CONSUMPTION SURFACES
agents actually ingest through, and the measured-FIDELITY check that is the moat.

CEaaS refines content into raw -> compressed -> hyper-efficient tiers, hosts/serves them, and feeds
governed corpora + tools into open agent loops (Claude Code / MCP). These are GOVERNED wrappers over
the proven DIY tooling (Repomix structural compression, LLMLingua-2 learned compression, Mem0/Hindsight
distillation, MCP/llms.txt surfaces) — the hosted, measured, freshness-tracked version nobody ships yet.

    python3 -m scripts.seed.ceaas_components
    python3 scripts/validate.py catalog/processors/compression/*.yaml catalog/processors/deliver/*.yaml catalog/processors/verify/*.yaml
"""
from __future__ import annotations

from scripts.seed.component_seed import processor, write_batch

DOC = "docs/strategy/context-enrichment-service.md"
LABEL = "Open Harness Hub — Context Enrichment as a Service (CEaaS)"

# COMPRESSION TIER — structural flavor (the learned flavor is retrieval/llmlingua-compress).
COMPRESSION = [
    ("structural-compress", "Structural compression (Tree-sitter)", "compress.structural", ["summarization"], True, "none",
     ["content"], ["compressed"],
     "Strip function/method bodies, keep signatures + structure (Repomix / Tree-sitter style) — ~70% token "
     "reduction on code, structure-lossless. The 'compressed' tier's structural flavor; pairs with the learned "
     "flavor (retrieval/llmlingua-compress). Ships a measured fidelity delta (verify/compression-fidelity-check)."),
]

# CONSUMPTION SURFACES — meet the agent where it ingests context (the four-surface Repomix pattern).
DELIVER = [
    ("serve-mcp-corpus", "Serve corpus over MCP", "deliver.mcp_serve", ["tool_use", "retrieval"], False, "external_call",
     ["corpus", "tools"], ["mcp_endpoint"],
     "Live-serve a governed corpus + its tools over MCP to Claude Code / Cursor / any agent loop — the default "
     "surface (MCP is the convergence point). Tier-negotiated, CDC-fresh, metered."),
    ("emit-llms-txt", "Emit llms.txt", "deliver.llms_txt", ["format_conversion"], True, "none",
     ["corpus"], ["llms_txt"],
     "Render a governed corpus as llms.txt / llms-full.txt (the emerging doc-tier standard) — download or paste "
     "into any agent, no integration. The freezable consumption surface."),
    ("package-agent-skill", "Package as agent skill/plugin", "deliver.skill_package", ["tool_use"], True, "none",
     ["corpus", "tools"], ["skill_bundle"],
     "Package a governed corpus + tools as one installable Claude Code skill/plugin (the Repomix pattern) — "
     "distribute corpus + tools as a single governed, versioned unit."),
    ("emit-claudemd-fragment", "Emit CLAUDE.md fragment", "deliver.claudemd", ["format_conversion"], True, "none",
     ["distilled"], ["claudemd"],
     "Emit the distilled, always-loaded near-zero-token tier as a CLAUDE.md fragment — stable knowledge that "
     "survives compaction (conventions, glossary)."),
]

# THE MOAT — measured fidelity per tier ("did this tier preserve enough?"), by a separate evaluator.
VERIFY = [
    ("compression-fidelity-check", "Compression fidelity check", "verify.compression_fidelity", ["evaluation", "governance"], False, "none",
     ["raw", "tier"], ["fidelity"],
     "Measure the quality delta per tier so every raw -> compressed -> hyper-efficient artifact ships a published "
     "fidelity score, scored by a SEPARATE evaluator (never self-graded). Aggressive compression destroys "
     "reasoning; this is the measured-fidelity guarantee — the same engine and moat as OHH's lift gate."),
]


def main() -> int:
    def mk(specs, tags, prefix):
        return [processor(*c, tags=tags, source_doc=DOC, source_label=LABEL, impl_prefix=prefix) for c in specs]
    n = 0
    n += len(write_batch("catalog/processors/compression", mk(COMPRESSION, ("ceaas", "compression", "tier"), "scripts.processors.compression")))
    n += len(write_batch("catalog/processors/deliver", mk(DELIVER, ("ceaas", "consumption-surface"), "scripts.processors.deliver")))
    n += len(write_batch("catalog/processors/verify", mk(VERIFY, ("ceaas", "fidelity", "governance"), "scripts.processors.verify")))
    print(f"wrote {n} CEaaS components (compression tier + 4 consumption surfaces + fidelity check)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
