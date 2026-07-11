# browser_use_adapter (DESIGN SEAM)

> Status: **design seam** — an **LLM→browser agent** (browser-use, or the self-healing one-websocket
> browser-harness) that takes a natural-language goal and autonomously drives a browser. It is the
> *unknown-workflow* explorer, NOT a trusted executor: its output — including any helper code it writes — is
> **QUARANTINED** until a deterministic gate proves it, then compiled to a stable primitive.

## Adapter shape

- **Class:** `BrowserUseAdapter(BrowserAdapter)` wrapping the agent (`browser-use` is installable; it drives a real
  Chrome via CDP/Playwright underneath — so its *browser* is really our `cdp`/`playwright` backend, with an LLM on
  top choosing the actions).
- **Backs:** a HIGH-LEVEL `explore(goal)` that returns a **proposed** action plan + observations, each still emitted
  as a `browser_action_receipt`. The low-level `navigate`/`snapshot`/`extract_*` delegate to the underlying real
  backend. `click_ref`/`fill_ref` remain **gated** — the agent PROPOSES a side effect; the human confirmation gate
  (write+) still governs execution. It NEVER submits / bypasses a login/captcha autonomously.
- **Output contract:** every agent step → an `llm_browser_task` row (`task_type: browser_action_plan`,
  `untrusted: true`); any helper the agent writes → the security gate (`primitive_security_gate`) before it may run.

## Install + test

```bash
pip install browser-use                 # installable; needs an LLM endpoint + a real browser backend
# Owner rule: LOCAL LLM first — localhost:8000 (OpenAI-compat) / OpenWebUI; cloud only with configured keys.
python3 scripts/primitive_security_gate.py --self-test   # the gate every agent-written helper must pass
```

## When to use

- **Unknown / one-off workflow discovery** — let the agent find the steps, capture them as receipts, then
  **compile the proven path into a deterministic primitive** (the agent is a scout, not the runtime).
- Never for a repeatable production task — once known, route it to `playwright` (regression) or a compiled primitive.

## Risks

- **Output QUARANTINED:** agent action plans and any self-written helper code are untrusted supply-chain artifacts —
  security-gate + human review before trust or promotion; `serves_truth=false` always.
- **browser-harness** self-healing helpers carry the same quarantine.
- Non-determinism + cost (LLM in the loop) → use to DISCOVER, then remove the intelligence from the path (the
  execution-descent filter). Local-LLM-first per owner rule; keep the side-effect confirmation gate on our side.
