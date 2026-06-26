# Agent Workflow System Reference Intake

OpenHubForAI should study mature agent and workflow ecosystems as reference sources for workflow shapes, skill formats, tool permissioning, memory designs, hub/marketplace patterns, and deployment models.

This should be done as controlled reference intake, not blind global installation. Many of these systems execute code, install plugins, run browser tooling, or connect to external accounts. The default path is:

```text
identify upstream
-> clone or download into _reference or sandbox
-> license and provenance check
-> scan workflow / skill / tool metadata
-> extract primitives
-> entity link
-> label and dimension
-> fuzzy dedupe
-> publish only normalized summaries/manifests
```

Do not republish upstream source files from `_reference/`.

## Priority Systems

### OpenClaw

OpenClaw is useful as a reference for multi-channel agent routing, community skill hubs, sandboxed skills, model-agnostic configuration, and local/self-hosted deployment. Its docs describe 50+ channel integrations, thousands of skills, model-agnostic use across Claude/GPT/Gemini/Llama/Mistral/Ollama, and sandboxed skill permissions.

What to extract:

- channel adapter patterns;
- skill manifest structure;
- sandbox and permission model;
- model-routing configuration;
- memory/wiki patterns;
- marketplace/hub metadata;
- install/runtime shapes.

### Claude Code Skills and Skill Marketplaces

Claude Skills are directly relevant because they package repeatable workflows in Markdown plus optional scripts/resources. Public collections such as office/business skills and security-audit skills show how skills encode tasks, procedures, checklists, tool assumptions, and review workflows.

What to extract:

- `SKILL.md` metadata;
- trigger descriptions;
- task procedures;
- domain categories;
- tool/resource dependencies;
- executable scripts;
- safety and review gates;
- install paths for Claude Code and Codex.

### Hermes Agent

Hermes Agent is useful as a design reference for autonomous self-governance: budget-capped execution loops, security-aware context filtering, platform-adaptive prompts, streaming context management, and persistent cross-agent task boards.

What to extract:

- budget and step-limit policies;
- context filtering;
- prompt-injection defenses;
- task board structure;
- multi-model routing;
- autonomous execution guardrails.

### CrewAI, LangGraph, AutoGen, Dify, Flowise, n8n, ComfyUI

These systems expose workflow graph, agent orchestration, multi-agent role, node, edge, state, retry, human-in-loop, and marketplace patterns.

What to extract:

- workflow graph schemas;
- node types;
- edge and state transition semantics;
- human approval nodes;
- retry/error policies;
- memory/RAG nodes;
- tool calls and credentials;
- marketplace metadata;
- examples and templates.

### Kaggle, Notebook, and Deep-Research Agent Sources

Kaggle and notebook-derived projects are high-value because they expose tasks that require more than a raw model answer: data loading, schema inspection, code execution, intermediate validation, result checking, and trace review. They should be mined as task and evaluation surfaces, not copied wholesale.

What to extract:

- dataset-grounded question types;
- notebook execution traces;
- data-cleaning and schema-inspection steps;
- multi-step research plans;
- exhaustive-answer evaluation rubrics;
- tool-use failure modes;
- cost and runtime priors for code execution.

### Minimal Graph Workflow Frameworks

Small LLM workflow frameworks are useful because they reveal the irreducible primitives behind larger agent stacks: nodes, edges, shared state, batch execution, async execution, retries, and evaluation hooks. PocketFlow-style graph/shared-store designs are especially relevant for turning weak out-of-box LLM behavior into reliable task workflows.

What to extract:

- node contracts;
- shared-store state conventions;
- action-labeled edges;
- batch and parallel execution patterns;
- graph-to-pipeline conversion rules;
- places where deterministic tools replace model guessing.

### Duecare-Style Capability Harnesses

Duecare-style products are a useful pattern even when public details are sparse: they treat an LLM as one component inside a constrained workflow that adds domain context, checks, scoring, and review. The primitive to capture is not the website copy; it is the harness shape that makes a weak general model useful for a narrow, economically valuable task.

What to extract:

- domain-specific decomposition steps;
- deterministic prechecks;
- evidence collection;
- scoring rubrics;
- human approval gates;
- monitoring and regression tests;
- model-swap and cost controls.

## Reference Install Policy

Use three install levels:

- **metadata only**: fetch README, docs index, manifest files, marketplace index, and package metadata;
- **reference clone**: clone into `_reference/<source>` for offline study, never republish;
- **sandbox run**: run in an isolated container or temp workspace only when behavior must be observed.

Never run install scripts such as `curl | bash` as part of routine ingestion. Convert installation instructions into deployable blueprint objects instead.

## Primitive Output

Each scanned system should produce:

- source records;
- canonical entities for projects, skills, tools, adapters, models, workflows, and marketplaces;
- normalized workflow nodes and skill objects;
- labels and dimensions;
- dedupe clusters;
- review tickets for executable or risky skills;
- candidate tools, pipelines, rule packs, and deployment blueprints.

## Security Notes

Treat skills and workflow imports as untrusted code until scanned. Flag:

- shell scripts;
- package installs;
- browser automation;
- credential access;
- network access;
- filesystem writes;
- MCP servers and tool permissions;
- prompt-injection-prone context loading;
- unknown licenses.
