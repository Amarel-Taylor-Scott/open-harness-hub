# Peer registries - what already exists, what this hub adds

A side-by-side of the LLM-ecosystem registries Hassan mentioned
("Hugging Face, vector DBs") plus the others Taylor references, and
which gaps Open Harness Hub fills.

## The landscape

| Registry | What it indexes | What it does NOT index | Gap |
|---|---|---|---|
| **HuggingFace Hub** | models, datasets, spaces | step-by-step pipelines, rule packs, retrieval rules, personas, evaluation rubrics | no notion of "this is how you chain steps around the model" |
| **LangChain Hub** | prompt templates | rule packs, GREP heuristics, post-LLM verification, multi-vertical reuse | prompts only; the rest of the harness is left to the developer |
| **OpenAI Evals registry** | evaluation suites for OpenAI models | non-evaluation primitives (personas, rule packs, knowledge packs) | only the right-hand side of the chain |
| **EleutherAI lm-eval-harness** | evaluation tasks for any HF-compatible LLM | persona libraries, GREP rule packs, RAG content, redaction processors | only the right-hand side, deeper than OpenAI Evals but still eval-only |
| **promptfoo** | configs for comparing prompts/models | not a registry - config files travel with each project; no central catalog | per-project tool, not a public registry |
| **MCP server marketplace** | MCP server definitions (tools the model can call) | personas, rule packs, eval rubrics, full pipelines | tools-only |
| **Anthropic Agent Skills** | self-contained agentic skills | atomic primitives below the skill level (a persona, a GREP pack) | top-level skill bundles only |
| **Pinecone / Weaviate / Chroma** | vector DBs | the rules + personas + rubrics around the retrieval | infrastructure layer, no semantic content |
| **Docker Hub** | container images | not the operational workflows - just the binaries inside the container | infrastructure layer, no logic |

## What Open Harness Hub adds

**Full coverage of the 6-step canonical chain** that real production
pipelines follow:

```
structured-to-prose  →  PII/PHI redact  →  GREP red-flags  →  RAG  →  LLM judge  →  audit trace
       │                      │                  │              │            │              │
   processor             rule-pack + processor   rule-pack    knowledge-pack  processor    processor
```

**Each step has its own first-class artifact type** in the registry.
No other peer indexes ALL of:

1. The persona library (12 personas including ESG-auditor /
   radiologist / contract-reviewer / security-engineer)
2. The GREP rule packs that catch problems BEFORE the LLM call (21
   rule packs across PHI/PII/forced-labor/environmental/governance/
   contract/code-vulnerabilities/prompt-injection)
3. The hierarchical RAG anchors (20 knowledge packs with real JSONL
   data covering CSDDD + 12 national laws / 11 ILO indicators /
   ACR Appropriateness Criteria + Fleischner + 18 RADS scores /
   10 contract clause families / OWASP / MITRE ATT&CK)
4. The post-LLM verification (10 verify-* processors + 7 composable
   success-criteria kinds with AND/OR/NOT logic)
5. The audit trace emitter (CSDDD-Art.26 / HIPAA / board-oversight
   compliance trace)

**Plus** the 22 design patterns (Self-RAG / ReAct / ToT / SoT /
Reflexion / Self-Refine / Plan-Execute / Orchestrator-Workers /
Evaluator-Optimizer / Multi-Agent-Debate / Routing / Prompt-Chaining
/ Naive/Corrective/Fusion RAG / HyDE / Step-Back / Two-Stage-Retrieve
/ K-Anonymity-Aggregation / Composable-Success-Criteria) - each with
paper citation, reference implementations, when-to-use, tradeoffs,
counter-patterns, and implementing pipelines.

## Why not extend Hugging Face / LangChain Hub?

They could each absorb part of this scope. But:

- **HuggingFace** is model-centric: hosts the BERT / Llama / Mistral
  weights. Adding "this is the regex you run BEFORE the model" needs
  a different artifact type with different lifecycle properties
  (volatile vs stable, local-only trust boundary, etc.). The Open
  Harness Hub schemas formalize that.
- **LangChain Hub** is prompt-centric and locked to LangChain's
  Python class hierarchy. The harness here is framework-neutral
  YAML; it emits to LangChain, but is not LangChain.
- **MCP marketplace** is tool-centric. A tool is _one_ kind of
  primitive in the harness; this hub indexes all 14.
- The emitters in `scripts/emit/` actually publish to all of these
  peer registries from one source - the hub becomes a fan-out point,
  not a competitor.

## Layered architecture

```
   ┌───────────────────────────────────────────────────────────┐
   │  Open Harness Hub catalog (200 YAML manifests, 14 types)  │
   └────────────────────────────┬──────────────────────────────┘
                                ▼
         ┌──────────────────────────────────────────┐
         │  Emitters (13 standards-format outputs)  │
         └─┬────┬────┬────┬────┬────┬────┬────┬────┘
           ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼
       HF      MCP  Agent CycloneDX OL  C2PA  EU-AI lm-eval
     model/   server Skills  -ML        Annex IV harness
     dataset                                       promptfoo
     cards                                          ...
```

Each downstream registry gets a clean publication artifact in its
native format from one source. No double-bookkeeping; no drift.

## What forks should look like

Hassan's CSDDD example fits naturally as a **vertical fork** of this
hub - same schemas, same vocabularies, different catalog content
focused on compliance. The hub publishes the spec; vendors and
domain consortiums publish their own catalogs against the same spec.

A pharmaceutical-compliance hub, a defense-acquisition hub, a
climate-finance hub - all are healthy forks that consume the same
schemas/vocabularies/emitters and share interoperable artifacts.

## Status (May 2026)

- **200 manifests**, all validating
- **4 working verticals** with live end-to-end demos
- **13 emitters** producing clean output
- **CLI** with 9 subcommands
- **Real LLM integration** (Ollama / Anthropic / OpenAI / Gemini)
- **MIT license**
- **No platform lock-in** - plain YAML in git

The reference implementation is the existence proof. The spec
(`docs/spec/HARNESS_HUB_SPEC.md`) is the portable layer. Forks and
co-authors welcome.
