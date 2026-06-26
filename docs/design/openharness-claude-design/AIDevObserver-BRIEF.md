# AIDevObserver build brief (the executable spec for the designer)

> This is the missing piece. The other files give the design system (`DESIGN-BIBLE.md`), the actual source
> (`DESIGN-ASSETS.md`), and the backend contract (`INTEGRATION-BIBLE.md`). This file tells you exactly WHAT to build
> for AIDevObserver: the screens, their states, the data each renders (with REAL payloads from the live backend), and
> the acceptance bar. Build a full app, not a single comp. serves_truth=false. Accent for this surface: `#b25fd6`.

## What you are building (three things, all in the shared kit)

1. **Marketing home** (`/`): already exists at `web/aidevobserver/aidevobserver-main.jsx`; elevate it.
2. **The demo** (`/demo`): a working "paste a session, get a review" page.
3. **THE MAIN BUILD: the logged-in app** using `OhLayout variant="sidebar"` (the left-sidebar shell, which composes
   `OhAppShell`). This is the bulk of the work.

Everything uses the shared kit through `OhLayout` (the one page skeleton): the marketing home and the demo use
`OhLayout variant="no-sidebar"`, and the logged-in app uses `OhLayout variant="sidebar"`; the card/button/pill atoms
and `OhTable` (the standardized data table) come from the same kit. You differ from the other 4 surfaces ONLY by the
accent (`#b25fd6`) and the copy. Do not invent a new CSS system.

## The product in one paragraph (for the copy)

AIDevObserver reviews how a team uses AI coding agents. It reads a session (a transcript of prompts and tool calls),
runs the review engine, and returns a ranked list of findings: reinvention (rebuilding something that already exists),
wasted context (oversized or duplicated), risky commands, and missed cheaper paths. The user triages each finding
(accept, reuse, or dismiss). That accept-or-dismiss signal is what makes the product improve over time. Findings are
suggestions a human reviews, never auto-applied; the tool is read only and stores nothing.

## The logged-in app: `OhLayout variant="sidebar"`, four screens

Use `OhLayout variant="sidebar"` (it composes `OhAppShell`) with the AIDevObserver accent: pass `sidebar` = the nav
(the `[[href, glyph, label], ...]` shape below), plus `brand`, `cta`, `theme`, and `onToggle`. Sidebar nav
(glyph + label):

| Sidebar item | Route | Job |
|---|---|---|
| **Review** (default) | `/` | the ranked findings for the selected session |
| **Sessions** | `/sessions` | the list of reviewed sessions, pick one |
| **Findings** | `/findings` | all findings across sessions, filter by type, see outcomes |
| **Settings** | `/settings` | BYO key, mode, interruption budget, editor integrations |

### Screen: Review (default) and the FINDING CARD (the core component)

- **Data:** `POST /api/observer/review` with the session, returns the report (see the API contract below).
- **Layout:** a page head (session name + a summary strip: total findings, reinventions, waste, the `by_type`
  counts), then the findings list rendered as cards, ordered by `confidence` descending.
- **States:** empty ("Clean session. No findings."), loading (skeleton cards), populated, error (show the message,
  offer retry).
- **The finding card** (render EVERY finding identically, from the real payload fields):
  - a **type chip** (`type`): one of `reinvention`, `stack_reinvention`, `oversized_context`, `duplicate_context`,
    `footgun`, `adversarial`, `shortcut`, `guidance`, `alternative`, `product_reinvention`.
  - a **confidence badge** (`confidence`, 0.00 to 1.00): a small bar or a percentage.
  - the **message** (`message`): the headline.
  - the **evidence** (`evidence`): a short excerpt, monospace. For `footgun` this is `"<redacted match>"`, render it
    muted, never expand it.
  - the **suggestion** (`suggestion`): the recommended action.
  - **source_ref** as chips: `source_ref.existing` (the registry components that already do it) or
    `source_ref.covering` (the package that covers it).
  - three **actions: Accept / Reuse / Dismiss** (this is the `outcome` field, the moat; wire them to set it).

Render note per type (color from the kit, accent for reinvention family, amber for waste, red for footgun, neutral
for adversarial):

| type | meaning | tone |
|---|---|---|
| reinvention / stack_reinvention / product_reinvention | rebuilding something that already exists | accent |
| oversized_context / duplicate_context / shortcut | wasted or repeated context/effort | amber |
| footgun | a risky or destructive or secret pattern | red (evidence redacted) |
| adversarial | a question to answer before building | neutral (a prompt, not an error) |
| guidance / alternative | a convention or a simpler idiom | neutral |

### Screen: Sessions

- **Data:** `GET /api/observer/sessions` returns `{ "sessions": [ {session_id, path, mtime, project} ] }`.
- **Render:** an `OhTable` with `cols` = project, session id (short), time (relative, from `mtime`), and finding
  count (once reviewed). Set `onRow` to open Review for that session (`onRow` makes the rows click-through). Do not
  show the full `path` (it is a local filesystem path); show `project` plus the short id.
- **States:** empty ("No sessions yet. Connect your editor or paste a transcript on the demo."), loading, populated.

### Screen: Findings (cross-session)

- **Job:** one place to filter findings by type and see the accept/dismiss outcomes.
- **Render:** a filterable `OhTable` with `cols` = type, confidence, message, session, outcome. The outcome column is
  the signal the product learns from.

### Screen: Settings

- **Render:** the **mode** selector (`silent_record`, `review_only`, `advisory`, `active`, `enforcing`), the
  **interruption budget** (a small integer, the max live interruptions per session), the **BYO key** field (governed
  copy: "Used only for this request. Never stored or logged."), and the **editor integrations** card with the three
  install lines: the VS Code / Cursor extension, the MCP server (`claude mcp add aidevobserver -- python3
  scripts/aidevobserver_mcp_server.py`), and the CLI (`python3 -m src.teleon.observer.cli review --latest`).

## The API contract (REAL, captured from the live backend at `/api/observer/...`)

**`POST /api/observer/review`** request: `{ "messages": [ {"role":"user|assistant", "content":"..."} ] }`
(or `{ "transcript_path": "..." }`). Response (real shape, abbreviated to 2 findings):

```json
{
  "version": "0.2.0",
  "report": [
    {
      "type": "reinvention",
      "confidence": 0.80,
      "message": "This looks like a solved problem. These already exist in the registry federation, so do not reinvent them.",
      "evidence": "let me write my own pdf text extractor from scratch",
      "suggestion": "Reuse the existing component instead of rebuilding (it saves the rebuild and its debug trajectory).",
      "source_ref": { "existing": { "extract": [ { "registry": "adapter_layers", "name": "ocr_document_parse" } ] } },
      "max_action": "ask", "message_index": 0, "action": "ask", "outcome": null, "candidate": true, "serves_truth": false
    },
    {
      "type": "stack_reinvention",
      "confidence": 0.82,
      "message": "An existing dependency stack already provides this, so do not rebuild it.",
      "evidence": "exponential_backoff, retry",
      "suggestion": "Reuse tenacity (it covers these via its dependency stack).",
      "source_ref": { "covering": [ { "package": "tenacity", "provides": ["exponential_backoff", "retry"] } ] },
      "max_action": "notice", "message_index": 1, "action": "notice", "outcome": null, "candidate": true, "serves_truth": false
    }
  ],
  "summary": { "messages_reviewed": 3, "findings": 4, "reinventions": 2, "waste_signals": 2,
               "by_type": { "reinvention": 2, "stack_reinvention": 1, "adversarial": 1 } },
  "serves_truth": false
}
```

**`POST /api/observer/live`** (intra-session): same request, response
`{ "surfaced": [ ...findings... ], "summary": { "messages", "findings", "by_type", "would_interrupt" }, "mode": "advisory", "serves_truth": false }`.
`surfaced` is the subset the tool would interrupt with live (capped by the interruption budget).

**`GET /api/observer/sessions`** response: `{ "sessions": [ {"session_id":"...", "path":"...", "mtime": 0, "project":"..."} ], "serves_truth": false }`.

(The `message`/`suggestion` strings from the engine currently contain em dashes; render them, but those are on the
backend-copy sweep list, so do not copy that punctuation into your own static copy. Follow the copy rules below.)

## The demo (`/demo`)

A "paste a session (or load the example), get a review" page: a textarea prefilled with an example session, a Review
button that POSTs to `/api/observer/review`, and the result rendered with the SAME finding card component as the app.
Use this example session (it produces the payload above):

```json
{ "messages": [
  {"role":"user","content":"let me write my own pdf text extractor from scratch"},
  {"role":"user","content":"I will implement my own retry with exponential backoff"},
  {"role":"user","content":"building a custom oauth2 login flow by hand"}
] }
```

## Acceptance checklist (this is "done")

- [ ] The `OhAppShell` left-sidebar shell with all 4 screens (Review, Sessions, Findings, Settings), in the shared kit, accent `#b25fd6`.
- [ ] Uses OhLayout (sidebar) for the app and OhTable for the Sessions/Findings lists.
- [ ] The finding card renders the real `/review` payload (every field: type chip, confidence, message, evidence, suggestion, source_ref chips), not placeholder text.
- [ ] Accept / Reuse / Dismiss actions on every finding (the `outcome`).
- [ ] Empty, loading, and error states for Review and Sessions.
- [ ] The demo POSTs to `/api/observer/review` and renders the same finding cards.
- [ ] Settings shows the mode, the interruption budget, the governed BYO-key field, and the three install lines.
- [ ] Copy rules pass (below).
- [ ] Differs from the other 4 surfaces ONLY by accent + copy; reuses the shared kit; no new CSS system.

## Copy rules (hard, enforced)

1. No placeholders. Real names, real words. Write "OpenHubForAI", never "Open*Hubs". No "Lorem", "TODO", "coming soon".
2. No em dashes or en dashes anywhere. Use commas, periods, parentheses, or colons.
3. No strategy leakage in public copy: no "moat", "wedge", "private bench", "win one vertical", pricing or competitive strategy.
4. Real, confident sales and marketing copy: benefit-led headlines, concrete value, clear calls to action.

## Deeper integrations: standardized objects and the registries (design for these)

These are real systems in the codebase. Designing for them is what makes AIDevObserver more than a linter. Each one
gives the UI more to show:

1. **Deep-link a finding to the live registry record.** A `reinvention` finding's `source_ref.existing` names a
   `registry` and a `name` (for example `adapter_layers / ocr_document_parse`). Make that chip a link into the
   OpenHubForAI `/browse` record for it (the federation has 147 catalogs, reached via the `/registry/` seam). The
   user clicks the "already exists" component and sees the real thing. This is the grounding that makes the finding
   trustworthy.
2. **Show dollars and hours saved (the economics registry, `src/teleon/economics`).** A reuse-vs-rebuild finding can
   carry an estimated saving. Design a small "saves ~$X, ~Y hrs" stat on the finding card and a session and team
   total. This is the ROI story: reuse is cheaper than rebuild plus debug.
3. **The cheaper-path ladder (`architecture/capability_ladders.json`).** Each capability has a cost-ordered,
   deterministic-first ladder. A "missed cheaper path" finding can show the rungs (for example for OCR: deterministic
   parser, then a cheap model, then a frontier model). Design a finding that renders the ladder and where the user
   landed on it.
4. **Cheaper model or route (`provider_arbitrage` and the model-routing registries).** A finding: "a frontier model
   was used for a trivial task; a cheaper route does it", with the route and the saving.
5. **Vulnerability-grounded footguns (`vulnerability_sources`).** A footgun finding about a risky dependency or
   pattern can cite the real advisory. Design the footgun card to optionally show the source.
6. **Findings as governed standardized objects (`RegistryObject` + `mint_record`).** Every finding is a governed
   candidate (thin wrapper, version in metadata, `serves_truth=false`, the `outcome` field). The Findings screen is a
   view over these objects; design it to make the governed, candidate, human-triaged nature legible.
7. **AIDevObserver populates the `agent_behavior` and `agent_qa` registries (it closes two known gaps).** These two
   registries exist in the ontology but are underbuilt because they need an agent-telemetry source. AIDevObserver IS
   that source: the team's reviews and accept/dismiss outcomes are the agent-behavior and agent-QA records. Design the
   analytics and Findings screens knowing this data feeds those registries. This is the strongest integration in the
   system: AIDevObserver is the missing telemetry seam.
8. **Bring your own internal registry.** A team connects their OWN internal components to the federation, so "this
   already exists" also covers their private libraries, not just public packages. Design a Settings flow to connect an
   internal registry. (Teams reinvent their OWN code constantly; this is the highest-value catch.)

## Features and product-market fit (design for the buyer)

- **Who buys it:** engineering leads, platform, and developer-experience teams who pay for AI coding agents
  (Copilot, Cursor, Claude Code, Codex) and want that spend to be consistent, cheap, and safe.
- **The wedge:** teams reinvent the wheel constantly with AI; each developer rebuilds what already exists.
  AIDevObserver catches it, grounded in the federation. The value is measurable: dollars saved, review hours saved,
  risky patterns caught.
- **The signal that compounds:** the accept / reuse / dismiss `outcome` on every finding. The more a team uses it, the
  better its suggestions get. Make that loop visible and easy.
- **Features to design for (beyond the four screens):**
  - **Team analytics / savings dashboard:** most-common reinventions, dollars wasted, trend over time, an AI-hygiene
    score. The leader view.
  - **PR / CI check:** run the review on a pull request's session or diff and flag reinvention before merge. Design
    the "PR check" result state.
  - **Live in-editor coaching:** the VS Code and Cursor extension surfaces a finding in the editor (the live mode plus
    the interruption budget). Design the compact in-editor finding.
  - **Multi-tool:** the capture seam normalizes Claude Code, Cursor, Copilot, and Codex sessions; show the source tool
    on the Sessions screen.

## Your deliverable: the app PLUS an integration-handoff README

Deliver two things:

1. **The designed app** (the four screens, the demo, the elevated marketing home), in the shared kit, accent `#b25fd6`.
2. **`INTEGRATION-HANDOFF.md`**: a README that explains how to merge your work into THIS codebase WITHOUT breaking it.
   It must cover, under these constraints:
   - **The app lives at `web/aidevobserver/`** (React 18 rendered in-browser via Babel, no build step, the shared kit
     in `web/aidevobserver/kit/`). Served by the showcase (`OH_PRODUCT=aidevobserver python3 -m scripts.showcase`).
   - **Do not fork the shared kit.** If a component or token needs a change, change it in the kit (it propagates to all
     5 surfaces) and say so explicitly, because that is the one design law.
   - **Backends are reached only through same-origin seams** (`/api/observer/...`); never hardcode a host
     (INTEGRATION-BIBLE section 4). A new endpoint is a service-plane service plus a seam, not a frontend hack.
   - **The proof gate must stay green:** `PYTHONPATH=. python3 scripts/run_proofs.py`. Note which `check_*` proofs
     cover what you touched.
   - **The copy rules and the one design law hold.**
   - The README should list: files added or changed, any kit change (and why it is in the kit, not the app), any new
     seam or service, and a "how to verify" (the gate, Playwright shows rich content with 0 console errors, the demo
     calls the real `/api/observer/review`).

*serves_truth=false. Findings are governed candidate suggestions a human triages; the tool is read only and stores nothing.*
