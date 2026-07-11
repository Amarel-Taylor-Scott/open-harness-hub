# Harness Engineering — landscape, our-system map, and honest gaps (2026-07-08)

> **Warrant:** owner shared a cluster of harness-engineering writeups ("Research these") — Anthony Maio's
> *Build Your First Agent Harness in 90 Minutes*, Effective AI's multi-agent insurance runtime (Suman Swaroop),
> GitHub Copilot's published harness-efficiency benchmark, and Lin et al.'s *Agentic Harness Engineering*. This
> doc synthesizes them, maps each load-bearing pattern to **what this substrate already has** (reuse-first), and
> lists the honest gaps + a prioritized adopt list. It is analysis, not a design change; `serves_truth=false`.

## 0. The load-bearing reframe (the owner's highlight — internalize this)

> "Often people think it's about token cost, but it's more than that. Being paranoid about every token that goes
> into their context directly translates to the level of complexity they can own."

**Token discipline is not a cost lever — it is a CAPABILITY lever.** A tighter, higher-signal context window
raises the *complexity ceiling* an agent can reliably own, and lowers silent failure. This is strongest in
**out-of-distribution domains** (heavy in-context learning), where context quality dominates model choice.

This upgrades our value proposition. Our primitive-injection thesis (retrieve verified capability instead of
re-deriving it; inject verified code at ~0 tokens) is usually pitched as **cost savings** (4.96–7.54× in our
session benchmarks). The stronger, truer pitch is: **it raises the reliability ceiling** — the same context
budget now buys a harder task done correctly. Fold this into the briefing and measure it with the
**context-re-fed-per-turn** axis (see the Databricks benchmark memo) — not just $/task, but *tasks-completable
per context budget*.

## 1. The external landscape (harness engineering is now a named discipline)

- **Anthony Maio — *Build Your First Agent Harness in 90 Minutes*** ([blog], repo
  `github.com/anthony-maio/agent-harness-90m`). A minimal harness = a `while` loop with guardrails, no
  frameworks. **"The model is a dependency you can swap. The harness is the product."** The **six jobs**:
  1. **Task intake** — a *contract*, not a prompt (what to do · allowed tools · forbidden · **Done-means**).
     "Done-means" is load-bearing: without explicit completion criteria the agent declares done the moment the
     task gets hard.
  2. **Tool registry** — name · schema · `execute()` · **risk level** (low = fire, medium = policy decides,
     high = always ask). "A tool the agent doesn't know about doesn't exist." The tool list is an attack surface.
  3. **Policy gate** — approval-required / blocked-outright / workspace-boundary. One enforcement point, not
     scattered in each tool.
  4. **Budget layer** — max LLM calls · max tool calls · max wall-seconds; **hard kill at 100%, no negotiation.**
     Motivated by a real Producer/Critic loop that ate **215,000 tokens** against a 200K limit because the Critic
     out-ranked the Coordinator and **nobody had a kill switch**.
  5. **Logging** — every tool + LLM call as append-only JSONL. "If you can't replay the run, you have a story
     about an agent, not an agent."
  6. **Report** — one Markdown receipt per run (what happened, budget used, tools, files, failures, what to
     remember). Plus **memory** (append-only, human-gated; *surprisal-gated write-back* as the v2 — persist only
     info above a surprise threshold), and **model routing** (60–80% of turns on a cheaper tier via a
     *lightweight dispatch heuristic, not a second model*).
  Three time-wasters he names: starting with multi-agent orchestration ("one agent with good logs beats five
  agents improvising"), giving the model every tool, and skipping approval gates because "it's just local."

- **Effective AI (Suman Swaroop) — production multi-agent runtime.** 10–20 specialized agents per user request:
  **typed task contracts, cooperative yielding, promise-based orchestration, and shared-or-isolated compute via
  E2B sandboxes.** Speed-to-market in days not weeks. ⚠️ **Their vertical is INSURANCE — ours is not** (§4).

- **GitHub Copilot harness benchmark (Meagan Cojocar et al.).** Published, reproducible data showing the Copilot
  agent harness is **on par or ahead on task completion AND cost-per-task** — token efficiency *without*
  sacrificing completion. Validates (a) our token-savings-with-quality thesis and (b) publishing **transparent,
  reproducible** benchmarks (our verify-the-verifier + receipt discipline).

- **Lin et al. — *Agentic Harness Engineering* (AHE / NexAU-AHE)** (`china-qijizhifeng/agentic-harness-engineering`).
  **Observability-driven AUTOMATIC evolution of the harness** around a frozen model: lifts GPT-5.4 **69.7 → 77.0%**
  over 10 iterations *while using ~12% fewer tokens*, reaches **84.7% ± 2.1 pass@1 on Terminal-Bench 2** (GPT-5.5),
  beats Codex/ACE/Training-Free GRPO, and the **frozen harness transfers to SWE-bench-Verified**. Part of a 2026
  arXiv cluster: *HarnessX* (2606.14249), *The Interplay of Harness Design and Post-Training in LLM Agents*
  (2606.25447), and an `awesome-harness-engineering` catalog. **The differentiation is the scaffolding, not the
  model** — exactly our "LLM proposes, deterministic system disposes" stance.

## 2. Map to OUR harness — reuse-first (we already implement all six jobs)

| Harness job (Maio) | Where it already lives here | Status |
|---|---|---|
| **Task intake / contract** | typed `edge_contract` · `input_edge`/`output_edge` · `route_signature` on every card; `request_intake.py` (canonical brief) | ✅ typed contracts; ⚠️ no explicit **Done-means** field |
| **Tool registry + risk** | `primitive_loop_json_hook.py` action **allowlist**; card `proofs_to_run_before_linking`; the **security gate** on generated executor code | ✅ |
| **Policy gate** | JSON hook validates action against allowlist, **clamps args**, runs fixed argv `shell=False`, keeps output **candidate-only** (`serves_truth=false`) | ✅ |
| **Budget layer + kill switch** | `_clamp_int` / `_token_budget_tier` ceilings; **6 STOP-file kill switches** (`STOP_HY3_FLYWHEEL`, `STOP_AUTONOMOUS_FACTORY`, `STOP_LLM_GENERATION`, `STOP_RESOURCE`, …); per-lane backoff/breaker | ✅ (this is exactly the 215K-runaway fix) |
| **Logging (replayable JSONL)** | append-only **receipts** under `data/dev-intel/**` (request/response, synthesis, benchmark) | ✅ |
| **Report** | `latest_status.json` + per-run receipts | ⚠️ no single human-facing per-run **Markdown report** |
| **Model routing (cheaper tier)** | `llm_capability_router.route(job_type)` → `_CHEAP_FAST` for labeling/triage/dedupe/taxonomy; Hy3-first for long ideation; strong-code lane for executors — a **heuristic classifier, not a second model** | ✅ (matches the 60–80%-cheaper-tier pattern) |
| **Auto-evolving harness (Lin et al.)** | `graph_autotune.py` races + persists the champion **retrieval** config and self-heals | ◻️ retrieval only — not yet the loop/harness config |
| **Sandbox placement (Effective AI / E2B)** | executor sandbox = `python -I -S` isolated subprocess; determinism check before promote | ✅ local; ◻️ E2B/cloud isolation is a config swap, not built |

**Conclusion:** the harness-engineering canon *validates our architecture* — we are not missing the discipline,
we implement it. The gaps are refinements, not foundations.

## 3. Honest gaps → prioritized adopt list

1. **Reframe the metric (highest ROI, no new code).** State "complexity ceiling, not just cost" in the
   end-to-end briefing; add **tasks-completable-per-context-budget** / **context-re-fed-per-turn** alongside
   $/task in `real_buildout_ab_harness`. (Ties to the Databricks context-per-turn finding.)
2. **Explicit `done_means` completion criteria** on task contracts (Maio: load-bearing). Add an optional
   `completion_criteria` field to the request brief / spec card and check it before a run is marked complete.
3. **Unified per-run Markdown report** (Maio's job #6). One receipt: task, budget used, tools/lanes, files
   changed, failures, "remember-next". Cheap wrapper over the receipts we already write.
4. **Observability-driven harness auto-evolution** (Lin et al.). Generalize the `graph_autotune` pattern from
   retrieval to the **loop config** (budgets, routing table, tool-set) — iterate on receipts, keep the champion,
   self-heal. This is the frontier and the strongest differentiator.
5. **Surprisal-gated memory write-back** (Maio v2). Score how surprising a candidate memory is; persist above a
   threshold instead of writing everything. Our memory is human-gated today — surprisal-gating is a real upgrade.
6. **E2B / cloud sandbox seam** as a drop-in behind the executor's local `python -I -S` sandbox — local-first
   now, cloud isolation when we scale (config swap, per our local→cloud law).

## 4. Guardrail — adopt the ARCHITECTURE, not the vertical

Effective AI's showcase domain is **insurance**. This repo has a **hard rule against insurance pipelines**
(CLAUDE.md / repo laws): do **not** build or expand insurance work. We adopt the harness *architecture*
(domain-neutral: contracts, gates, budgets, kill switches, routing, receipts) and target our own verticals —
**sanctions / OFAC SDN screening** first, then **healthcare-admin provider directory** (claims-*shape* adjacent,
never insurance). The insurance framing in these writeups is illustrative only.

## 5. Field observations (owner hands-on, 2026-07-08 — write-up forthcoming)

Owner test-drove local open-weight LLMs across **Qwen-Code, Codex, and Claude Code** harnesses. Preliminary
(a fuller write-up with data + methodology lands ~2026-07-09 — supersede this section then):

- **30B Mixture-of-Expert models are the sweet spot** — solve challenging problems, ~**40 tok/sec** on a Mac or
  **DGX Spark**, comparable throughput to a GPT-5.5 Pro subscription; usable for everyday work.
- **Harness choice is a first-order variable:** **Claude Code used ~2× the tokens of Codex** for equivalent (or
  better) task completion. This is a **third independent confirmation** of the harness-dominates-cost axis
  (Databricks: Pi fed ~3× less context/turn at equal quality; GitHub Copilot's published efficiency benchmark).
- **Gemma 4 E2B (effective-2B) is the floor/control** — included to show the tasks are **non-trivial** (small
  models can't solve them), so the 30B-MoE tier is where the real capability sweet spot begins. (Gemma **4** only,
  never Gemma 3 — repo rule.)

**Implications for us:**
1. **Finish the token-efficiency benchmark honestly** (`real_buildout_ab_harness`, task #8): report
   **tokens-per-task** and **context-re-fed-per-turn** for equivalent completion, since our primitive injection is
   the extreme case of "less context re-fed per turn." The axis is now triply-confirmed — measure it, don't assume.
2. **A local 30B-MoE lane would bypass the 429 throttle entirely** (free, private, no shared-key rpm ceiling — our
   current #1 generation blocker). Our `ollama_local` lane is **disabled, not deleted** (dev-PC crash rule); it
   re-enables via a one-line config `status` flip **iff** a local-capable rig (the DGX Spark / Mac) is reachable
   from the factory. Guardrail unchanged: **no local models on the dev PC that crashes** — the DGX Spark is
   separate hardware and an opportunity, not a reversal of that rule.

## Sources

- Anthony Maio, *Build Your First Agent Harness in 90 Minutes* — repo
  [`anthony-maio/agent-harness-90m`](https://github.com/anthony-maio/agent-harness-90m).
- Effective AI (Suman Swaroop) — multi-agent insurance runtime (typed task contracts, promise orchestration,
  E2B sandboxes).
- GitHub Copilot agent-harness efficiency benchmark (Meagan Cojocar et al.) — published cost-per-task + completion data.
- Lin et al., *Agentic Harness Engineering* —
  [`china-qijizhifeng/agentic-harness-engineering`](https://github.com/china-qijizhifeng/agentic-harness-engineering);
  cluster: [HarnessX (arXiv 2606.14249)](https://arxiv.org/pdf/2606.14249),
  [Interplay of Harness Design and Post-Training (arXiv 2606.25447)](https://arxiv.org/pdf/2606.25447),
  [awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering).
