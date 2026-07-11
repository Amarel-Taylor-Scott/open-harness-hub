# Agent tooling & document-parsing batch — research (2026-06)

**Date:** 2026-06-06. **Owner-supplied, verify-first** (sources cited; "changes everything / greatest minds"
marketing language treated as marketing, not evidence). Four repos, split into **two infrastructure pieces**
(PaddleOCR, DESIGN.md) and **two agent-context/skill-layer pieces** (OpenAgent, Nuwa-Skill).

> **Baltor stance (how each maps to the governed substrate):** none of these is adopted as a runtime. Each is
> a **candidate behind a capability port**, slotted by **numeric priority** (see
> `_repos/teleon/context/architecture/numeric-preference-graph.md`) so a new tool drops in *between* existing ones without a
> code change. Agents/skills **PROPOSE**; Baltor **DISPOSES** (memory/agent/LLM output is never truth).
> Sandboxed, never auto-installed/executed. Real adapters stay candidate until a local equivalent + contract
> test + fallback exist (CLOUD-DEFER-ONLY-AFTER-LOCAL-EQUIVALENT).

| Repo | Layer | Baltor slot | Verdict |
|---|---|---|---|
| **PaddleOCR** | OCR / document-AI / RAG ingestion | `parser_manager` | **Highest practical value.** Strong parser candidate before decomposition/RAG; Apache-2.0; has MCP server + Agent Skills. |
| **OpenAgent** | self-hosted personal AI agent platform | `research_agent` (bounded, sandboxed) | **Promising, active, high-risk** (shell/browser). Candidate that PROPOSES evidence; **never the runtime**, never serves truth. |
| **DESIGN.md** | design-context spec for coding agents | context-file standard (like AGENTS.md/CLAUDE.md) | **Useful, low-friction standard — adopt.** Persistent visual identity for coding agents. No execution surface. |
| **Nuwa-Skill** | persona / thinking-style skill generator | `skills_manager` / personas (creative lens) | **Interesting but hype-heavy.** Perspective generator, **not** truth or real cognition transfer; audit before installing. |

---

## 1. PaddleOCR → `parser_manager` (highest practical value)

OCR + document-AI toolkit (PaddlePaddle): PDFs/images/forms/tables/formulas/charts → structured JSON/Markdown
for LLMs/RAG. Stack: **PP-OCRv5** (text), **PP-StructureV3** (layout/tables/formulas/reading-order),
**PaddleOCR-VL** (0.9B vision-language doc parser, claims 96.3% OmniDocBench v1.6), a **PaddleOCR MCP server**,
and official **Agent Skills** (`paddleocr-text-recognition`, `paddleocr-doc-parsing`). Apache-2.0.
([PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR))

**Why it matters to Baltor:** RAG/decomposition quality fails *before* retrieval — a parser that mangles
tables, reading order, math, or figure captions cannot be recovered downstream. PaddleOCR is a strong
candidate for the **Source/intake → decomposition** layer, ahead of the existing `parser.unstructured`
fallback. It already speaks MCP + Skills, so it fits our provider-port model directly.

**Comparison set to benchmark on our nastiest docs** (scanned PDFs, multi-column papers, tables, charts,
sealed/handwritten, slide decks): **Docling** (MIT, clean GenAI conversion — already our intended primary),
**MinerU** (VLM+OCR dual engine, 109 langs, MCP; custom-Apache license), **Marker** (fast PDF→MD/JSON; watch
GPL/commercial model-license), **Surya** (650M OCR, 91 langs; code Apache-2.0 but **model weights have
OpenRAIL-style restrictions** — license caveat), **Unstructured** (enterprise ingestion/chunking).

**Action:** cataloged as a `parser_manager` candidate with a high numeric priority (see catalog). License is
clean (Apache-2.0); benchmark before promoting above Docling.

## 2. OpenAgent → `research_agent` (bounded, sandboxed candidate — never the runtime)

Self-hosted single-binary personal AI assistant: LLM orchestration + RAG + MCP + tool-calling + computer/
browser/shell + 30+ providers + vector backends (Qdrant/Pinecone/Milvus/pgvector) + RBAC/SSO/audit. ~5.2k★,
very active. ([OpenAgent](https://github.com/the-open-agent/openagent) ·
[docs](https://www.openagentai.org/docs))

**Security caveat (load-bearing):** its own docs warn that **Shell and Browser tools act on the host** and
must run only in trusted/sandboxed environments. Any platform that can browse, run shell, call MCP, read/write
files, and connect to chat channels is a **high-trust admin surface**.

**Baltor stance:** this is exactly an **agentic-tools-landscape candidate** — a bounded agent behind a
ContextOps/research port that **PROPOSES evidence**, never serves truth, never becomes the runtime. Treat like
OWL/Browser-use/Skyvern (already cataloged). If evaluated: throwaway VM/container, no real secrets, test
channel accounts, explicit tool allow/deny lists, human approval for shell/browser/file-write/credential
actions, no public exposure. **We do not pip-install or execute it.** Cataloged with a `do_not_adopt_as_runtime`
note + sandbox requirement.

## 3. DESIGN.md → adopt as a context-file standard

Google-Labs spec: a plain-text file giving coding agents persistent **visual-identity** context (YAML
frontmatter tokens + Markdown intent/examples/anti-patterns). CLI lints, checks WCAG contrast, diffs versions.
"AGENTS.md, but for visual identity." ([design.md](https://github.com/google-labs-code/design.md) ·
[AGENTS.md](https://agents.md/))

**Why it matters to Baltor:** we already keep `AGENTS.md` + `CLAUDE.md`; a `DESIGN.md` would give coding
agents our **locked brand** as persistent, reviewable visual context — directly serving the design-quality
goal (acquired-AI-tool-grade UI, not dev-dark+orange). Low-risk: a text file, no execution surface.

**Action (recommended, low-risk):** adopt a `DESIGN.md` (or `_repos/baltor/frontend/DESIGN.md`) seeded from
`_repos/aidoneright/context/strategy/brand-architecture.md` (thesis, pillars Verified·Current·Efficient·Provable, lexicon,
never-say list). **Design tokens (colors/typography/spacing) are owner input** — author them with the owner;
do not fabricate a visual system. Pairs with a `web-design-engineer`-style skill.

## 4. Nuwa-Skill → skills/persona layer (creative lens, NOT truth)

Agent Skill that generates persona/"thinking-style" skills from a person's public traces (expression DNA,
mental models, decision heuristics, anti-patterns, honest boundaries). ~23k★. Works in Agent-Skills runtimes.
Its own README is careful: **not cloning a person**, cannot capture true intuition, a snapshot of *public*
expression. ([Nuwa-Skill](https://github.com/alchaincyf/nuwa-skill))

**Baltor stance:** useful as a **structured-brainstorming / perspective lens** (e.g. "stress-test this via a
Munger-style incentives lens"), mapping to our **personas** (an Action) — but it is **not a factual authority
and not real cognition transfer**, consistent with our "memory/agent output is not truth" law.
**Security:** Agent Skills can carry scripts/prompt-injections; GitHub explicitly warns skills are unverified —
**audit before installing**, never bulk-install into a privileged agent profile.
**Legal/ethical:** for living/public figures — false-attribution, right-of-publicity, impersonation risk.
Label any output **"inspired by public writings, not endorsement/impersonation."** Catalog as a
`skills_manager` candidate flagged hype-heavy + audit-required; not adopted.

---

## Cross-comparison & priority

| Need | Best from this batch |
|---|---|
| Parse PDFs/images/tables for decomposition/RAG | **PaddleOCR** (benchmark vs Docling/MinerU/Marker/Surya) |
| Self-hosted assistant w/ RAG/MCP/tools (sandboxed) | **OpenAgent** (candidate, never runtime) |
| Keep AI-generated UI on-brand | **DESIGN.md** |
| Reusable creative/strategic viewpoints | **Nuwa-Skill** (lens, not truth) |

**Priority:** (1) **PaddleOCR — benchmark seriously** (slot by number above `unstructured`); (2) **DESIGN.md —
adopt early** (low-risk); (3) **OpenAgent — sandbox-prototype only**; (4) **Nuwa-Skill — creative lens, audit
first**.

**Weekend evaluation plan:** run PaddleOCR on ~20 representative docs vs Docling/MinerU/Marker; install
OpenAgent in a VM, test RAG/MCP/web/browser/shell **separately**; add `DESIGN.md` to one frontend repo and
diff agent UI output before/after; run Nuwa-Skill only in a disposable project, review every generated file.

## How this connects to the Baltor stack

| Layer | Tools/repos |
|---|---|
| Agent runtime / assistant | OpenAgent · OWL · OpenHands · Claude Code (candidates/foils — never the canonical runtime) |
| Skill layer | Nuwa-Skill · PaddleOCR Skills · Anthropic Skills (behind `skills_manager`) |
| Context files | AGENTS.md · CLAUDE.md · **DESIGN.md** (adopt) |
| Document parsing / OCR | **PaddleOCR** · Docling · MinerU · Marker · Surya · Unstructured (behind `parser_manager`) |
| Context compression / memory | Headroom · LLMLingua (behind `compression`) · Supermemory/Mem0/Letta (behind `memory_provider`) |

*Warrant: owner-supplied research + cited sources (verify-first). No tool installed or executed. Catalog
additions are candidates behind ports, slotted by numeric priority; agents/skills propose, never serve truth.
Sources inline above.*
