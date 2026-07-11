# LLM-Driven Browser Control — Safety

> When a model (or an LLM→browser agent) drives a browser, the browser is a loaded gun: it can spend money, submit
> claims, leak a logged-in session, or run code the model wrote. This is the non-negotiable safety rail for the
> `browser_control` adapters and any LLM lane on top of them. Enforced in code by
> `browser_control/safety.py` (delegating to `scripts/primitive_browser_control_harness.py`) and proven by
> `python3 browser_control/self_test.py --self-test`.

## 1. Read-only by default; side effects are gated

- A session starts **read-only** (`allow_side_effects=False`). An act command (`click_ref`/`fill_ref`) is
  **REFUSED** and receipted `verifier_result=refused_read_only`, `executed=false` — the side effect never happens.
- Even with side effects enabled, the **side-effect calculus** over `SIDE_EFFECT_LEVELS`
  (`read_only < read < write_possible < write < regulated < money_movement`) requires **explicit human
  confirmation** for anything `>= write`: the command returns `requires_confirmation=true, executed=false` and is
  **never auto-executed**. Single source: `safety.side_effect_confirmation_gate(...)`.
- **Dry-run + human gate** for any mutation. The model may PLAN a side effect; a human authorizes it.

## 2. Never bypass a control

- **Never** submit a form autonomously, solve or bypass a **captcha**, defeat a **paywall**, or evade a **login
  wall**. These are **detected and enumerated as candidates** (`captcha_present_detector`, `login_state_detector`,
  `safe_submit_gate`) — detection only, never circumvention.
- **Never act as another user.** A driver that runs in a logged-in browser (extension) or a shared HTTP control
  plane (pinchtab/browserless) hands a live auth session to the caller — treat as **`authenticated_internal`**,
  require an auth gate, capture only on explicit user action, and never promote authenticated/tenant-private
  content to a global corpus.

## 3. Redaction + no raw bodies

- **Secrets are redacted** before ANYTHING is logged or persisted — filled values, tokens, keys — via the harness
  redactor (`safety.redact_fields` / the receipt's own redaction of `fill_ref` values). The self-test seeds a
  secret-shaped token in the fixture and proves it never survives into any receipt/extract/report.
- **No raw page bodies** are stored — digests (`sha256:...`), bounded redacted text, and extracted structured
  units only. Screenshots are hashed, not stored.
- **robots.txt is respected** (`safety.robots_gate`) and per-domain throttling applies before any live fetch.

## 4. The model's output is untrusted

- Every LLM step is an **`llm_browser_task`** with `untrusted=true`: a candidate PROPOSAL a deterministic gate must
  validate (`validation_errors`), never served truth. `serves_truth=false` always.
- **Self-written helpers are QUARANTINED.** Any code an agent (browser-use / browser-harness) writes is an
  untrusted supply-chain artifact — it must pass `scripts/primitive_security_gate.py`
  (`docs/SECURITY_GATE_FOR_PRIMITIVES.md`) and human review before it may run or promote. `quarantine` is not
  waivable without security review.
- Use an LLM/agent to **discover** an unknown workflow, then **compile the proven path into a deterministic
  primitive** and remove the model from the runtime (the execution-descent filter).

## 5. Local LLM first (owner rule)

- **Try a LOCAL endpoint before any cloud lane:** `localhost:8000` (OpenAI-compatible) or a local OpenWebUI /
  OpenWebUI-CDP. Do **not** rely on local Ollama (owner rule), but a local OpenAI-compat server is the default.
- **Cloud only with configured keys.** Cloud keys in this environment are **file-based** (e.g.
  `.agent/openrouter_keys.txt`) — there are no cloud env vars. A lane whose key is absent is **unavailable**
  (degrade, never block); reference keys as `env://`/file handles, never inline. The `model_endpoint.local_first`
  flag on every `llm_browser_task` records that the local lane was tried first.

## 6. What a reviewer checks (not just "it's green")

- Read-only default held; every side effect `>= write` shows `requires_confirmation=true` and a human authorization.
- No secret / raw body / authenticated-content leak in receipts, extracts, or the report.
- No captcha/paywall/login/robots bypass; detections present, circumventions absent.
- Every agent-written helper carries a `security_gate=pass` receipt; every LLM row is `untrusted=true`,
  `serves_truth=false`.
