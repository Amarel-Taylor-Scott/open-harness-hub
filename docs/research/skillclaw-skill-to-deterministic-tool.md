# SkillClaw -> the GOVERNED "skill -> deterministic tool" compiler (research infra)

> **Status: research_candidate. Not production infra.** SkillClaw is MIT-licensed and presented as
> work-in-progress; we treat it as a CANDIDATE source of *skill drafts only*, never as runtime that
> serves truth. The interesting move is the **fork direction**: compile a repeatedly-reused, held-out-validated
> skill into a deterministic, schema-bounded, sandboxed, signed internal **tool** — i.e. the
> [Determinism Factory](../../prompts/baltor-determinism-factory.md) applied to *skills*, gated like the
> agent-gateway and governed by the [Lossless Distillation law](../codex/lossless-distillation.md).
>
> **LOSSLESS DISTILLATION CLAUSE:** Any distillation, decomposition, compression, optimization,
> reconciliation, promotion, or LLM-to-rule conversion must be lossless at the system level. Never overwrite
> or delete raw/source/intermediate artifacts. Every derived artifact preserves source handles, lineage,
> transform config, version, receipts, held-out items, rejected candidates, and a rollback target. Run
> side-by-side before promotion, run shadow mode for new rules, monitor after promotion, prove rehydration.
> Omitted means held out, never erased.

Machine-readable companion: [`architecture/skill_to_tool_promotion_catalog.json`](../../architecture/skill_to_tool_promotion_catalog.json).
Proof: `scripts/check_skill_to_tool_promotion.py --self-test`.

---

## 1. What SkillClaw is (verified)

SkillClaw (`AMAP-ML/SkillClaw`, from Alibaba's AMAP-ML team) is an open-source framework that makes an
agent's skills improve continuously from real interaction traces ("collective skill evolution"). Two
components share one storage layer and one skill format (`SKILL.md`):

- **Client Proxy** — a local, OpenAI-compatible API proxy (`/v1/chat/completions`, `/v1/messages`) that sits
  in front of the agent's model calls. It **records session artifacts** and **manages a local skill library**.
- **Evolve Server (optional)** — a backend service that reads session data from shared storage, **detects
  repeated gaps / failure patterns, and generates or evolves `SKILL.md` skills**, then writes them back. Two
  engines: a `workflow` engine (a fixed 3-stage LLM pipeline: **Summarize -> Aggregate -> Execute**) and an
  `agent` engine (an OpenClaw-driven workspace that edits skills directly). You add the Evolve Server only when
  you want automatic evolution or team-wide sharing.

Other verified facts:

- **Skill loop:** observe conversations -> detect where the agent fails to give a useful response ->
  generate modular reusable skills -> **validate against a set before deployment** (a skill that makes things
  worse is rejected) -> integrate back. Described as "data-driven, not prompt-engineered."
- **Shared storage:** Alibaba OSS / AWS S3 / local filesystem (optional Nacos for skill assets). The default
  workflow uploads accepted outputs to `{group_id}/skills/<name>/SKILL.md`.
- **Ecosystem:** integrates with **Hermes, Codex, Claude Code, OpenClaw, QwenPaw** (and other OpenAI-compatible
  agents; the repo also lists IronClaw/PicoClaw/ZeroClaw/NanoClaw/NemoClaw).
- **License:** **MIT**.

**Confidence.** *High* on architecture (Client Proxy / Evolve Server / two engines), the SKILL.md loop,
OpenAI-compatible endpoints, shared-storage options, the ecosystem list, and MIT license — these corroborate
across the project post and the repo. *Medium / conflicted* on maturity: the
[opensourceprojects.dev post](https://opensourceprojects.dev/post/skillclaw) frames it as **work in progress**,
while the [GitHub README](https://github.com/AMAP-ML/SkillClaw) reads more feature-complete. **We adopt the
safer reading and record it as WIP / `research_candidate`** until independently re-verified. We did not run or
install it (guardrails: no pip / install / live-LLM).

---

## 2. Why a fork is needed (the gap)

SkillClaw's loop is exactly the kind of self-improvement we want to *capture*, but as shipped it does two
things our governance cannot accept unchanged:

1. **It re-injects an evolved `SKILL.md` back into the probabilistic agent loop.** A better prompt is still a
   prompt — the result is still non-deterministic and still not truth. Our thesis is the opposite: where a
   skill is *repeatedly* used and *verified*, **compile it down to a deterministic tool** so cheap models can
   call it reliably (the [small-models + deterministic-harnesses](../../prompts/baltor-determinism-factory.md)
   thesis).
2. **It can auto-publish to shared/collective storage on a threshold**, and collective cross-user evolution can
   carry one tenant's data into a shared skill. Defaults include Alibaba OSS (a low-cost / foreign processing
   lane). For a governance product this is disqualifying for any non-public trace.

**Fork direction — the "skill -> tool compiler."** Keep SkillClaw's *observe -> detect-gap -> generate-skill ->
validate* loop as a CANDIDATE source of **skill drafts only**. Then add a compiler stage that promotes a
validated, repeatedly-reused skill through a governed ladder into a deterministic, schema-bounded, sandboxed,
secret-scanned, SBOM'd, **human-approved, signed, versioned** internal tool — with the source skill kept as the
documented fallback. Self-improvement happens **out of band** and is promoted only through the gate.

A key clarification carried throughout: **"deterministic tool" != "deterministic agent."** The agent still
plans probabilistically and decides *when* to call the tool. A promoted tool is deterministic **given the same
input + declared state**; its output is still a candidate the consumption gate must verify, never auto-served
truth.

---

## 3. The promotion ladder (0 -> 6)

Each rung is a **versioned derived layer** over the one below; promotion deletes nothing (lossless). No rung
auto-advances, and **no rung serves truth**.

| Rung | Name | Produces | Gate to enter |
|---|---|---|---|
| **0** | Observation | `session_trace` (public / synthetic / redacted-internal-non-sensitive only) | gap detector finds a *repeated* failure or manual workaround |
| **1** | Draft skill (`SKILL.md`) | a candidate `SKILL.md` in a quarantine library | never auto-published to shared/global storage |
| **2** | Verified skill | `SkillValidationReport` | capability **lift on a HELD-OUT eval set** (not the mined traces) + no regression; reuse counted |
| **3** | Tool candidate | `tool.yaml` + input/output **JSON Schema** + `src` + unit/golden/property tests + **security_manifest** | the skill->tool compiler emits the deterministic core; source skill retained as fallback |
| **4** | Deterministic tool | `DeterminismProofReport` | passes the **deterministic-tool standard** (see §4): repeatability + schema + sandbox + side-effect checks |
| **5** | Certified internal tool | **signed** `ToolPromotionReceipt` + registry entry | secret-scan + static-analysis + dependency-lock + SBOM pass **AND** human/policy approval -> signed, versioned, rollback target set |
| **6** | Retired / merged | `RetirementRecord` (lineage preserved) | superseded / merged / gap closed; active pointer moves, but tool + skill + held-out eval + losing candidates are **preserved** |

Rung 0->1 is SkillClaw-shaped. Rung 1->2 is the **held-out** validation bar (stronger than "tested against a
set" — it must lift on data it was *not* mined from). Rungs 3->5 are the new compiler + governance gate. Rung 6
is the lossless-retirement rule: **retired/merged != deleted.**

---

## 4. The deterministic-tool standard

A tool may be **certified (rung 5)** only if all of the following hold. Single source of truth:
`deterministic_tool_standard` in
[`architecture/skill_to_tool_promotion_catalog.json`](../../architecture/skill_to_tool_promotion_catalog.json).

**Determinism**
- `no_llm_calls` — the tool never calls a model at runtime.
- `no_random_without_seed` — no unseeded randomness.
- `no_wall_clock_dependency` — time is injected, not read from the clock.
- `repeat_runs: N` (N >= 2) with `same_output_hash: true` — N repeat runs on the same input produce the same
  output hash. **Deterministic GIVEN same input + declared state** — not "deterministic agent."

**Sandbox caps**
- `fs: read_only` (`allowed_paths_only`), `network: blocked`, `subprocess: blocked`.

**Declared side-effects**
- required, must match observed behavior; default `none`.

**Tests**
- `unit` + `golden` + `property`; `min_tool_test_pass = 1.0`.

**Promotion gates**
- `min_reuse = 3`, `min_skill_validation = 1`, `min_tool_test_pass = 1.0`, `min_repeatability = 1.0`,
  `human_approval_required = true`.

**Security**
- `secret_scan`, `static_analysis`, `dependency_lock`, `sbom`, `signed` — all required.

**Lineage (lossless)**
- preserve the **source skill**, the **held-out eval set**, the **losing candidate tools**, and a
  **rollback target**.

`agent_is_deterministic: false` is asserted in the standard so the distinction can never be lost.

---

## 5. How this ties to existing repo laws (connect, don't duplicate)

- **Determinism Factory** (`prompts/baltor-determinism-factory.md`). This IS that factory's M0->M8 ladder
  applied to *skills* instead of reconciliation/classification decisions. The mapping: M0–M2 (raw/structured/
  multi-candidate LLM behavior) ~ rungs 0–1; M3–M4 (deterministic validation + verified label) ~ rung 2's
  held-out validation; M5 (mine a rule candidate) ~ rung 3 (compile a tool candidate); M6 (shadow) and M7
  (deterministic-first with fallback) ~ rungs 4–5 (the tool runs deterministic-first via the agent-gateway with
  the skill/LLM path as OOD fallback); M8 (retire the LLM path) ~ rung 6 (retire/merge). Same invariant:
  **LLMs propose, the gate disposes; consensus/validation != truth.** This catalog is a *meta ledger* over that
  factory — it does not create a second rule engine, optimizer, or authority.
- **Agent-gateway / deterministic-first token ladder.** A certified tool becomes a cheap deterministic rung the
  gateway prefers before spending tokens on the skill/LLM path; the skill is the fallback for
  out-of-distribution inputs. This is the gateway's "deterministic-first, model-last" ordering — now fed by
  promoted tools.
- **Lossless Distillation law** (`docs/codex/lossless-distillation.md`). Every rung is a new versioned layer;
  the compiler keeps the **source skill + held-out eval + losing candidate tools + rollback target**. A
  certified tool that *replaced* its skill, or a retirement that *deleted* a tool, would violate the law. Run
  side-by-side (skill vs tool) before promotion; shadow the tool; monitor after; prove rehydration.
- **Skill Digestion Lab** (`docs/research/` + `scripts/check_skill_digestion.py`,
  `src/teleon/digestion/`). That lab already digests an *expensive* skill into a cheaper deterministic runtime
  CANDIDATE keeping the original as fallback, parses `SKILL.md` **without executing it**, and quarantines unsafe
  skills behind a sandbox+eval+redteam ladder. This catalog is the **governed promotion contract** that such a
  digester targets: it names the rungs, the deterministic-tool standard, and the data policy the digester must
  satisfy. (Connect, don't rebuild — the digester is the engine; this is the rulebook.)

---

## 6. Governance summary (the non-negotiables)

- **SkillClaw = `research_candidate` (MIT, WIP).** Never run unchanged as production infra; if ever vendored,
  pin a reviewed commit.
- **Skill output != truth; tool output != truth.** Both are candidates the consumption/verification gate must
  check.
- **No generated tool is auto-published.** Promotion requires sandbox + secret-scan + static-analysis +
  dependency-lock + SBOM + human/policy approval, and ships signed + versioned with a rollback target.
- **Data policy.** Mine skills/tools **only** from `public` / `synthetic` / `redacted_internal_non_sensitive`
  traces. **Never** `customer` / `secrets` / `regulated` / `confidential`, and never via a low-cost / foreign
  processing lane. Tenant-private lineage never becomes global.
- **Distillation is lossless.** The source skill, held-out eval, and losing candidates survive every promotion
  and every retirement.

## Sources

- [GitHub — AMAP-ML/SkillClaw](https://github.com/AMAP-ML/SkillClaw) (license, components, ecosystem)
- [opensourceprojects.dev — SkillClaw](https://opensourceprojects.dev/post/skillclaw) (loop, work-in-progress framing)
- Repo laws: [`prompts/baltor-determinism-factory.md`](../../prompts/baltor-determinism-factory.md),
  [`docs/codex/lossless-distillation.md`](../codex/lossless-distillation.md),
  [`scripts/check_skill_digestion.py`](../../scripts/check_skill_digestion.py)
