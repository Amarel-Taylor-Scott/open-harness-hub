# Agentic / browser / computer-use tools — candidates for ContextOps (owner research 2026-06-05)

Reference for [[contextops-verification-foundry]]: the BOUNDED agents ContextOps commissions to DISCOVER
sources & methods. **All are CANDIDATES behind ContextOps ports — never imported/executed as the Baltor
runtime, never the orchestrator, never serve truth.** Output = SourceDiscoveryReport / ExtractorSnippet /
GeneratedWorkerSpec *candidate*; Baltor stores/verifies/reconciles/proves/consumes. Verify-first; keep in
`_reference/` or catalog only; high-risk computer-use tools run in a sandbox/VM with human approval for
consequential actions (purchases, account changes, deletes, financial, irreversible).

## OWL (camel-ai/owl) — the repo asked about
Open-source **general task-automation agent framework** (built on CAMEL), NOT just a browser bot:
multi-agent coordination + online search + Playwright browser automation + document parsing + code
execution + multimodal tools + MCP/toolkit integrations + a local Gradio UI. README claims GAIA 69.09 (#1
among open-source frameworks). Baltor fit: a strong `research_agent` candidate for the "research a topic →
find sources → summarize" discovery step. Do NOT adopt its orchestration (Baltor's durable worker framework
stays the runtime).

## Map onto ContextOps ports (catalog as candidates; pick per task)
| ContextOps port / slot | Candidates | Notes |
|---|---|---|
| `ResearchAgentProviderPort` (general autonomous research/discovery) | **OWL**, OpenManus, Microsoft Agent Framework, CrewAI (role teams), MetaGPT (software-spec), Hermes, OpenClaw | output = SourceDiscoveryReport, never a fact |
| `BrowserAutomationProviderPort` (web actions: click/type/extract/forms) | **Browser-use** (open-ended), **Skyvern** (repeatable workflows: act/extract/validate), LaVague (NL→Selenium/Playwright), Airtop (no-code GTM) | best when "AI uses the web" to fetch a source |
| `ComputerUseProviderPort` (desktop GUI — HIGH RISK) | Agent S, Open Interpreter (local code/terminal), OpenAI Computer Use, Claude Computer Use | sandbox/VM + domain allowlist + human approval; never sensitive accounts |
| Hosted browser/desktop infra (scale/auth/observability) | Browserbase (cloud browsers), Scrapybara (remote Ubuntu/browser, CUA/Claude-CU integrations) | swap-in when local Playwright hurts; behind a provider adapter |
| Production orchestration (NOT Baltor's runtime) | LangGraph, Microsoft Agent Framework (AutoGen/SK successor), n8n | reference only — Baltor keeps its durable worker framework; do not adopt a 2nd runtime |

## Baltor stance (the discipline)
- **Separate concerns** (per the research's own production advice): orchestration (Baltor durable workers) ·
  browser/computer runtime (Browser-use/Skyvern/Browserbase/Scrapybara as candidate adapters) · credentials ·
  logging/observability · approvals — never one all-in-one agent owning truth.
- These tools live in ContextOps's M1 rung (agent researches with tools); their discoveries get distilled DOWN
  the cost ladder (M2 SourceRecipe → M3 deterministic extractor → M4 durable worker → M6 canonical cache).
  The whole point is to USE them once to build deterministic machinery, not call them every time.
- Catalog them under a `research_agent` / `browser_automation` / `computer_use` capability slot (each
  active/candidate slot needs a stub adapter) — feeds C-RESEARCH-1 + the deferred ContextOps research_agent
  catalog slot (OPP-contextops-runtime). Never `pip install`/execute in the governed runtime; reference + stub.
- Prompt-injection + sensitive-data + irreversible-action risks are real (OpenAI/Anthropic computer-use docs
  warn explicitly): isolate (container/VM), allowlist domains, require human confirmation for consequential
  actions. ContextOps's sandbox_gate + human-approval hook already encode this posture.

## Suggested next (not auto-applied)
- Add OWL/Browser-use/Skyvern/Agent-S/Open-Interpreter/LangGraph/MS-Agent-Framework to the ContextOps
  research_agent capability catalog as candidates (with a local_stub fallback) under C-RESEARCH-1 /
  OPP-contextops-runtime.
- A 3-prototype eval (per the research): OWL for broad research; Browser-use/Skyvern for a real web workflow;
  LangGraph/MAF for a controlled production flow — but only to produce SourceRecipes/verifiers, behind the
  bounded-agent invariant.
