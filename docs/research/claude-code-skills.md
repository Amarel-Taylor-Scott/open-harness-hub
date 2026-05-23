# Overlap with Claude Code skills (and the Agent Skills open standard)

> The short answer: **yes, there's overlap, but the hub is a superset and
> Claude Code skills are now one of its emit targets.** A larger truth:
> Claude Code skills follow the **Agent Skills** open standard
> ([agentskills.io](https://agentskills.io)) adopted by 40+ tools, so
> emitting skills covers far more than just Claude Code.

## What Claude Code skills are

A **Claude Code skill** is a folder containing `SKILL.md` plus optional
supporting files (`scripts/`, `references/`, `assets/`). `SKILL.md` has
YAML frontmatter (`name`, `description`, optional `allowed-tools`,
`disable-model-invocation`, `user-invocable`, `paths`, `argument-hint`,
`when_to_use`, etc.) followed by markdown instructions. Skills load via
**progressive disclosure**: agents see only `name` + `description` at
startup and load the full body when relevant.

Locations:

- Personal: `~/.claude/skills/<name>/SKILL.md`
- Project:  `.claude/skills/<name>/SKILL.md`
- Plugin:   `<plugin>/skills/<name>/SKILL.md`
- Enterprise: managed settings

**Distribution**: a `.claude-plugin/marketplace.json` in a git repo turns
that repo into a Claude Code plugin marketplace; users add it with
`/plugin marketplace add <url>`.

## What Agent Skills (the open standard) is

[agentskills.io](https://agentskills.io) is the open Anthropic-originated
standard the Claude Code skills format conforms to. It's adopted by
**40+ AI agent tools**, including:

> Claude Code · Claude (claude.ai) · OpenAI Codex · GitHub Copilot ·
> VS Code · Gemini CLI · Cursor · OpenHands · Roo Code · Goose · Letta ·
> Amp · Junie · Workshop · Tabnine · OpenCode · Factory · fast-agent ·
> Spring AI · Kiro · Mux · Firebender · Databricks Genie Code ·
> Snowflake Cortex Code · Mistral Vibe · Trae · Qodo · Ona · Piebald ·
> Emdash · Laravel Boost · Google AI Edge Gallery · nanobot · pi ·
> VT Code · Command Code · Vita · Agentman · Autohand Code CLI · …

That makes Agent Skills the **largest cross-tool catalog format** in the
agent ecosystem today.

Minimum required: `SKILL.md` with `name` + `description` plus body. Same
progressive-disclosure mechanic everywhere.

## The overlap (and where the hub is a superset)

| Concept | Claude Code skills | Agent Skills standard | Open Harness Hub |
|---|---|---|---|
| Atomic catalog unit | Skill folder | Skill folder | Harness, Pipeline, RulePack, KnowledgePack, LogicPack, Tool, Persona, Adapter, Rubric, Dataset, Processor, Schema (**12 types**) |
| Format | YAML frontmatter + markdown | YAML frontmatter + markdown | YAML manifest with JSON-Schema validation |
| Composition | Single MD body | Single MD body | Pipelines as DAGs of harnesses + rule packs + tools + processors |
| Evaluation | Not first-class | Not first-class | First-class `benchmark` + `rubric` + judge + dataset arms |
| Lifecycle position (pre/api/post) | Implicit | Implicit | Explicit `lifecycle_position` field |
| Cross-cutting axes | `paths` only | `paths` only | industry, capability, modality, trust_boundary, lifecycle, freshness, EU AI Act risk, NIST controls, DPV categories |
| Provenance | Implicit | Implicit | First-class `attribution`, `provenance`, PROV-O context |
| Distribution | Git repo + marketplace.json | Git repo | Git repo + multiple emit targets (Pages, HF Space, Vercel, Netlify, Cloudflare) |
| Cross-tool reach | One tool (Claude Code) | 40+ tools | All of the above PLUS MCP, Croissant, HF model/dataset/Space cards, lm-eval-harness, promptfoo, CycloneDX-ML, OpenLineage, C2PA, EU AI Act dossiers |

The hub is not a competitor to Agent Skills - it's a **higher-level
catalog** that emits down to Agent Skills (plus the other 13 targets in
SPEC §18.2).

## How they interop (and what the hub does about it)

The hub now ships `scripts/emit/agent_skill.py` (built in this session).
For every `harness/*` and `pipeline/*` in the catalog it emits:

```
dist/agent-skills/
├── INDEX.md
├── .claude-plugin/
│   └── marketplace.json          # makes the bundle a Claude Code plugin marketplace
├── <slug>/
│   ├── SKILL.md                  # Agent Skills compliant
│   └── references/
│       └── manifest.yaml         # the hub manifest, preserved
```

Three usage modes for the same output:

1. **Drop into Claude Code**: `cp -r dist/agent-skills/<slug> ~/.claude/skills/`.
2. **Publish as a Claude Code marketplace**: push `dist/agent-skills/` to a git repo; users run `/plugin marketplace add <git-url>`.
3. **Use in any Agent Skills-compatible tool** (Cursor, OpenHands, Gemini CLI, Roo Code, Goose, Letta, etc.): drop the same folder into their skills directory.

The hub catalog stays the source of truth. Agent Skills, MCP, Croissant,
HF cards, lm-eval-harness, and the rest are all leaves derived from the
same YAML.

## What the hub does that Agent Skills can't

These are the hub features that have no place in a SKILL.md folder and
that justify keeping the hub catalog as the primary artifact:

- **Composition**: a `pipeline/research-entity` is a DAG of 6 steps
  across multiple harnesses, rule packs, tools, and knowledge packs. A
  skill body would either flatten this (losing modularity) or reference
  external skills (no standard way to do so cross-tool).
- **Benchmarks**: a `benchmark/` ties a pipeline to a dataset + rubric +
  judge + model arms. There's no Agent Skills concept for "run X
  reproducibly against Y and report a comparable score."
- **Multi-target emit**: a single hub `dataset/` manifest emits to
  Croissant (HF/Kaggle/Google indexes it), HF dataset card (HF Hub
  renders it), and lm-eval-harness YAML (academic eval frameworks
  consume it). A skill is one target.
- **Provenance and compliance**: hub manifests carry
  `data_protection.hipaa_safe_harbor_categories`, `eu_ai_act_risk`,
  `nist_ai_rmf_controls`, attribution chains, etc. Skills carry none of
  that machine-readably.

## What we'd lose if we stopped at Agent Skills

If we just published SKILL.md folders directly (no hub layer above
them):

- No benchmarks across model arms.
- No DAG composition; every multi-step workflow lives inline.
- No machine-readable industry / capability / modality classification.
- No compliance metadata.
- No cross-emit to MCP, Croissant, HF cards, lm-eval-harness,
  CycloneDX-ML.
- No catalog browser / vector index / faceted search across artifact
  types beyond skills.

What we'd gain: a smaller mental model and zero translation step. The
hub keeps both - Agent Skills as the *emit target* for harnesses and
pipelines, hub YAML as the *source of truth*.

## Bottom line

| Question | Answer |
|---|---|
| Is there overlap with Claude Code skills directories? | Yes. The hub catalog IS a plugin marketplace once `dist/agent-skills/` is published. |
| Should the hub abandon its own format and just be skills? | No - Agent Skills can't express composition, benchmarks, multi-target emit, or compliance metadata. |
| What's the right relationship? | Hub is the **upstream**; Agent Skills (+ MCP, Croissant, HF cards, …) are **leaf emit targets**. |
| Effort to integrate? | Already done - `scripts/emit/agent_skill.py` produces 9 skills + a plugin marketplace manifest from the current catalog. |
| Cross-tool reach? | Agent Skills works in 40+ tools (Claude Code, Claude.ai, OpenAI Codex, GitHub Copilot, Cursor, Gemini CLI, OpenHands, Roo Code, Goose, Letta, VS Code, Junie, Workshop, Tabnine, …). |
