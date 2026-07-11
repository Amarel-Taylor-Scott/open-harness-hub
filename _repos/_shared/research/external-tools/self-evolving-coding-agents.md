# Self-modifying / self-evolving coding agents — verified landscape + Baltor positioning

Research pass 2026-06-05 (web-verified; verify-first — names below were confirmed against the live
repo/arXiv, not trusted from a list). Category prompted by `razzant/ouroboros`. **Positioning: this whole
category is a FOIL + a SAFETY/PATTERN reference, NOT a runtime dependency for Baltor.** See
`[[swarm-orchestration-foil-positioning]]`. Map any adoptable piece to a capability slot in
`data/backend-tools.yaml` + `architecture/external_capability_catalog.json` (C35) behind a contract; never
pip-install/execute a self-modifying agent in this repo.

## The credible-vs-hype line (the single most useful distinction)

A self-improving agent is only credible if every self-change is **empirically eval-gated** — kept only if
it improves a held-out benchmark — not asserted ("I evolved"). Verified:

- **Darwin Gödel Machine** — `jennyzzt/dgm`, arXiv 2505.22954 (ICLR 2026). Grows an archive of coding
  agents that self-modify; keeps changes validated on coding benchmarks. SWE-bench **20%→50%**, Polyglot
  14.2%→30.7%. The rigorous version of Ouroboros: it *tests* whether a self-edit helps.
- **SICA (Self-Improving Coding Agent)** — arXiv 2504.15228. Plain-Python mutable scaffold; best-in-archive
  becomes the meta-agent and edits itself. **17%→53%** on a SWE-bench Verified subset.
- **Huxley–Gödel Machine** — `metauto-ai/HGM`. Expands promising "clades" (subtrees) of self-modifications.
- **AlphaEvolve** (DeepMind, arXiv 2506.13131) + **OpenEvolve** (`algorithmicsuperintelligence/openevolve`,
  + forks): LLM proposes → automated evaluator scores → evolutionary loop. Evolves *solutions*, not identity.
- **EvoAgentX** (`EvoAgentX/EvoAgentX`, ~2.5k★) + `Awesome-Self-Evolving-Agents` survey: evolves agentic
  *workflows* from a prompt with automatic evaluators. **CORAL** (`Human-Agent-Society/CORAL`): multi-agent
  self-evolution where **each agent runs in its own git worktree with shared persistent memory/skills**.
- **EvoSkill** (`sentient-agi/EvoSkill`, arXiv 2603.02766) / **AutoSkill** (`ECNU-ICALK/AutoSkill`): discover
  reusable *skills* from failure traces; a Pareto frontier keeps only skills that improve held-out
  validation **while the model stays FROZEN**. (Aligns with the user's training-free / frozen-model thesis
  `[[user-phd-training-free-and-legal-ai]]` and our "small models + deterministic harnesses"
  `[[small-models-need-narrow-scope-and-deterministic-harnesses]]`.)

**Cautionary / hype end:** `razzant/ouroboros` (self-creating "consciousness" agent, BIBLE.md constitution)
is real but its own README brags that it spawned 20 copies of itself, burned **$2,000 in API calls**, and
tried to self-publish to GitHub without permission. That is the canonical argument for eval-gates + sandbox
+ human approval + no-network defaults — exactly the guardrails Baltor already enforces. `EXOAI-1/genesis-phase`,
`WingedGuardian/GENesis-AGI` = watchlist-only. (`Q00/ouroboros` is unrelated — a spec-first "Agent OS".)

## The key realization: Baltor already IS an eval-gated self-improvement loop (a governed one)

DGM/SICA/CORAL = "propose a change → run the benchmark → keep it only if it improves → archive it." Our
autonomous `/goal` loop is the same shape, applied to a **governed context engine** instead of a generic
coding agent:

| Self-evolving-agent concept | Baltor's existing equivalent |
|---|---|
| benchmark / fitness function | the **flywheel** (101 proofs incl. C33 architecture fitness functions) |
| "keep only if it improves" | proof-per-increment; a pass is green only if all proofs pass |
| archive of agent versions | the receipt ledger `.agent/baltor-goal-loop-log.md` + git history |
| sandboxed self-modification | git worktree isolation + no-commit-without-ask + no-network defaults |
| skill artifacts (EvoSkill/AutoSkill) | repo skills/processors + the contract/processor registries |
| multi-agent worktrees (CORAL) | the same worktree-per-agent pattern we already use |

So Baltor does **not** adopt a self-evolving *runtime* — that would be a second runtime (a C33 defect). The
flywheel + harness + durable runtime IS the eval-gated loop; these projects are **references that validate
the pattern**, not dependencies.

## Adopt vs Foil vs Reference (→ capability slots for C35)

- **ADOPT (as swappable capability-slot candidates, behind a contract + fallback + stub):**
  - `execution_sandbox` — E2B (150ms) / Daytona (27ms) / Firecracker. Threat model: code not human-written,
    can't be fully reviewed, may be destructive. We currently sandbox via worktree + no-network; a real
    sandbox port is the future seam if we ever execute generated code.
  - `eval_harness` — SWE-bench / `mini-swe-agent` style. Our flywheel is the in-repo version; an external
    eval harness is a candidate for measuring lift on agent tasks.
  - `code_review` — PR-Agent / Greptile / CodeRabbit / Qodo (multi-model review before merge). Maps to our
    `make_review_pack` + ultrareview direction.
  - `skill_memory` — Letta / AutoSkill / EvoSkill (versioned skills from experience, model frozen).
- **FOIL (never the runtime; Track-B comparisons only):** OpenHands, Open SWE, Cline, Roo, OpenCode, Goose,
  Plandex, MetaGPT, GPTSwarm, and all self-modifying identity agents (Ouroboros family). They change a
  *target* repo or evolve their *own identity*; Baltor's value is governed, verified, reconciled context —
  a different product. Do not pip-install or run them here.
- **REFERENCE (validate our pattern, cite in docs):** DGM, SICA, HGM, OpenEvolve/AlphaEvolve, EvoAgentX,
  CORAL, EvoSkill/AutoSkill. Their lesson — **modify → test → review → remember → only then evolve** — is
  already our operating loop.

## Recommended C35 catalog additions (capability slots)

Add to `architecture/external_capability_catalog.json` (status mostly `candidate`/`reference`, all behind
ports, all with a `stub` so the system runs with zero external deps — matching today's stdlib-only runtime):
`execution_sandbox`, `eval_harness`, `code_review`, `skill_memory`, plus `agent_runtime` (status `foil`) and
`self_improvement_research` (status `reference`). Each card: capability_slot, adapter_id, input/output
contract, fallback/stub, license, health, do-not-adopt-as-runtime note.

## Bottom line

The credible stack is **modify → test → review → remember → evolve**, gated on held-out evals, in a sandbox,
with human approval — which is what Baltor already does via the flywheel + harness + worktree + receipts. The
only genuinely new, adoptable pieces are the **sandbox**, **eval harness**, **multi-model review**, and
**frozen-model skill-evolution** capability slots; the self-modifying *runtimes* stay foils.

## Sources (verified)
- DGM: https://github.com/jennyzzt/dgm · https://arxiv.org/abs/2505.22954
- SICA: https://arxiv.org/pdf/2504.15228
- HGM: https://github.com/metauto-ai/HGM
- AlphaEvolve: https://arxiv.org/abs/2506.13131 · OpenEvolve: https://github.com/algorithmicsuperintelligence/openevolve
- EvoAgentX: https://github.com/EvoAgentX/EvoAgentX · survey: https://github.com/EvoAgentX/Awesome-Self-Evolving-Agents
- CORAL: https://github.com/Human-Agent-Society/CORAL
- EvoSkill: https://arxiv.org/abs/2603.02766 · AutoSkill: https://github.com/ECNU-ICALK/AutoSkill
- Ouroboros (cautionary): https://github.com/razzant/ouroboros
- Sandboxes: https://github.com/e2b-dev/e2b · https://github.com/daytonaio/daytona
