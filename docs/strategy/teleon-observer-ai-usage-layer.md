# AIDevObserver — a thin layer that watches AI usage and makes it better

> The customer-facing wedge for the Teleon engine. A **thin observer** that monitors how a developer/agent uses AI
> (in VS Code, Claude Code, Codex-in-terminal, …), **saves the session**, lets them **review it for learning**, and
> **pops up intra-session**: *"this already exists,"* an adversarial question, a cheaper path, a suggestion. It is
> NOT a new engine — it's a front-end over the one we have (the **descent** + the **reinvention guardrail** + the
> **federation** as grounding + the **economics** engine). serves_truth=false; local-first; governed.

## 0. The one-line product
**Grammarly / Datadog / a compiler-optimizer — for AI usage.** It watches you use AI, catches waste and reinvention
*grounded in a real index of what exists*, and teaches you (and your agents) to use less unnecessary intelligence.

## 1. Engine vs front-end (the key architecture fact)
There is **one engine**; "VS Code plugin," "server," "terminal wrapper," "gateway," "post-session report" are
**interchangeable front-ends** calling the identical pipeline. Every option below is a choice of wrapper, not a
rewrite. The engine, already in this repo:

| Engine piece | Repo module | Role in the Observer |
|---|---|---|
| Reinvention guardrail | `src/teleon/registry/reinvention_guard.py` | the "this already exists" catch (Tier 0 heuristic → Tier 1 local model → Tier 2 grounded) |
| Grounding (the moat) | the 98-registry federation + `registry.search.search_all` | answers "does it exist?" from a curated index, not LLM guesses |
| Descent | `src/teleon/evolution/descent.py` | the cheaper path: unbounded → observe waste → substitute deterministic → ~95% cheaper |
| Economics | `src/teleon/economics/` (cost_model, provider_arbitrage, simulator) | "$X wasted; here's the cheaper route/model" |
| Optimization memory | `descent_attempt_store` (the brain) | learns winning paths across sessions — the durable moat |
| Local models | Ollama `nomic-embed-text` / `gemma4` (keyless) | Tier-1 judge + embeddings run **on-device**, private |

## 2. The two design axes (pick one from each; they compose)

### Axis A — WHERE it runs
| Topology | Who controls | Best for | Trade-off |
|---|---|---|---|
| Embedded library | app owner | teams building their own agent | no isolation |
| Local sidecar (MCP/localhost) | the dev | privacy-max, offline, per-dev | each machine self-updates |
| Self-hosted server (VPC) | platform team | team policy, shared registry, audit | they operate it |
| Hosted SaaS | us | fastest onboarding, we own the loop | data-residency objections |
| Inline gateway/proxy | platform team | **any** agent, zero client buy-in | messier signal, latency-critical |

The **gateway** is the only one needing no client cooperation (works for Cursor/Codex/homegrown); the cost is it
sees a message stream, not clean tool-call semantics, so Tier 0/1 work harder. **Hooks** (Claude Code) get clean
semantics but need client support.

### Axis B — WHEN it runs (replay and live monitor are the SAME engine on a timeline)
- **Post-session review** *(lead with this)* — ingest the transcript / git diff after a session; run the funnel in
  batch; emit a report: *"6 places you reinvented something solved,"* with confidence scores a human triages. No
  latency budget; no false-positive-interrupts-you problem. The adoption wedge.
- **Intra-session, ambient** — watch the conversation; inject a context note when the dev *says* "I'll build X."
- **Intra-session, post-action** — after a write: "you just wrote X; Y already does this — swap it?" (can't undo).
- **Intra-session, pre-action** *(endgame)* — before the write/tool-call: annotate or **block**. Highest value,
  tightest latency, needs the most trust.
- **Cross-session analytics** — periodic batch over many sessions: *"your team reinvented auth 14× this quarter;
  here are the 3 internal modules people keep missing."* The manager dashboard / cost-savings pitch.

## 3. What the user sees (the features asked for)
- **Monitors AI usage** — captures the session (edits, tool calls, prompts, tokens, model, idle, errors) via the
  client's native channel (Claude Code hooks · a VS Code extension · a terminal wrapper for Codex · the gateway).
- **Saves sessions** — a durable, replayable session record (governed; PII-redacted; local-first storage option).
- **Review for learning** — a scrubbable replay + annotations: where time/tokens were wasted, debugging loops,
  reinventions, missed shortcuts, when to write a test.
- **Intra-session pop-ups** — *"this already exists (PyMuPDF)," an **adversarial question*** ("are you sure a custom
  parser beats the library? what's the failure mode?"), a **suggestion** (cheaper model / deterministic step), an
  **optimization** ("this prompt has 320k unnecessary tokens — summarize first, ~96% cheaper").

The pop-ups are the reinvention guardrail + the descent + economics, surfaced at the chosen timing point.

## 4. Cross-cutting operational logic
- **Latency / critical path** — pre-action *blocking* must be synchronous + fast (Tier 0 free, judge on a tiny
  fraction). Advisory/ambient/post can be async. Post-session has no budget — be exhaustive.
- **Fail-open, always** — if the Observer is slow/down, it degrades to **silence, never obstruction**.
- **Session state + de-dup** — key off the session id; remember what was already surfaced so it doesn't nag.
  Topology decides *where* that state lives (per-session file / sidecar memory / Redis); the dedup logic is identical.
- **Cost** — the funnel discards almost everything for free; you only spend on build-intent survivors. Local Tier-1
  = $0 and private.
- **Data residency (a real deal-lever, local-first)** — Tier-1 runs a **local** model (nothing leaves the machine);
  Tier-2 grounds against a **local** registry; only optional escalation sends *normalized intent + candidate
  metadata*, never the user's code. "Your code physically cannot leave your VPC" wins enterprise deals.

## 5. Sequencing — the trust ladder
**Post-session report → ambient notices → enforced pre-action.** Lead with the non-invasive report (easy yes, no
interruption, human triages false positives) to *earn the precision data + trust* that buys the right to interject
live. Pre-action blocking is the high-value endgame, but leading with it asks people to tolerate interruption from a
tool that hasn't proven it's right yet.

## 6. Three products from one engine
- **Self-hosted server + pre-action hook** → enforced team guardrail, registry in their VPC → the enterprise sale.
- **Hosted SaaS + post-session review** → "paste a session / connect a repo, get a reinvention report" → low-friction.
- **Embedded library + ambient** → for a company building its own agent that wants the check inline.

## 7. The moat (not the front-end)
Anyone can build a hook. The defensible parts are (a) the **grounded index** that makes the "it exists" call precise
(the curated federation, fresh via the population loop), and (b) the **optimization memory** (`descent_attempt_store`)
that learns winning paths from real session telemetry — *"this workflow ran N times; we know what works."*

## 8. Honest hard parts
- **Distribution** (getting devs to install a watcher) and **capture** (clean signal) are harder than the AI.
- **Precision** — a wrong pre-action interrupt gets muted in a day; that's why post-session/report leads.
- **Two products risk** — Teleon **Compiler** (build optimized graphs) and Teleon **Observer** (optimize usage) share
  the engine but are different go-to-markets; resist building both at full depth before one is proven.

## 9. First runnable step
The post-session reviewer is the smallest, highest-adoption artifact: the same descent + guardrail run **in batch**
over a transcript/diff → a confidence-scored reinvention+waste report. It's ~60 lines over the existing engine and
needs no capture infrastructure — the wedge that earns the right to go live.
