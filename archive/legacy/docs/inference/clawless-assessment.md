# ClawLess assessment — browser runtime, NOT an LLM endpoint

**Verdict:** ClawLess is useful, but it belongs in the **sandbox / browser-agent runtime** bucket, not the LLM
provider bucket. ClawLess is a browser-based runtime for Claw AI agents powered by **WebContainers** — a
sandboxed, in-browser, Node.js-like environment with an editor, terminal, policy engine, and audit logging.

It is therefore **never** an inference provider and **never** a free LLM endpoint. The intelligence engine
classifies it `browser_agent_runtime` (class 700) and `is_inference_provider: false`.

## Portfolio mapping

| Surface | Role |
|---|---|
| OpenToolsHub | tool/runtime candidate metadata |
| OpenHarnessHub | eval harness / sandbox safety tests |
| Teleon | possible `SandboxProvider` / `AgentRuntimeProvider` candidate |
| Shared Sandbox Gateway | browser/WebContainer runtime candidate |
| Shared Inference Gateway | **not a model provider** |

Catalog as `runtime.clawless_webcontainer@candidate` / `sandbox.webcontainer_agent_lab@candidate`.

## Security posture

WebContainers run in the browser and are marketed as a sandboxed in-browser Node.js environment, which is
promising for **disposable demos, skill/tool experiments, and browser-side agent labs**. But WebContainers are
designed for browser-side code execution, not hardened remote-VM compute — useful for local demos, **not** a
replacement for a server-side sandbox.

**Do not** give ClawLess production LLM keys, customer data, or regulated context until we independently test:
key handling, persistence, audit logs, network interception, and dependency-install behavior. Promotion is
capped at phase 2 (dev-only) until that review passes; all real use is **sandbox-gated** through the Shared
Sandbox Gateway, never a direct credentialed call.
