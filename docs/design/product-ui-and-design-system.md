# Open Harness Hub — Product Pages & Design System

> **What this file is.** A single, self-contained design brief you can paste into
> Claude (design / artifacts) to generate the product UI. It defines every page,
> the landing page (a deliberately bare entry box), the reusable components, and a
> full design-token **system** — the token *names and roles*. The token **values**
> (palette, type, theme) are deliberately left open: explore the *visual direction*
> with the companion prompt **`claude-design-prompt.md`** (it proposes and compares
> several directions against a best-practice rubric), then drop the winning values
> into the CSS scaffold in §5.5. The shipped `scripts/showcase/pages.py` palette
> appears below as the **baseline to beat**, not a mandate.
>
> **How to feed it to Claude.** Give Claude this whole file plus a target:
> *"Design the `/` landing page per §8.1 and §3, in the chosen direction, using the
> token scaffold in §5.5 and the entry-box spec in §7.4."* Work page-by-page; the
> token roles and the seven-primitive legend (§5–§6) are shared across every screen.
>
> **Vocabulary is load-bearing.** Use the canonical product labels everywhere:
> **Knowledge Corpus**, **Conditional** (the IF; formerly "If Statement"),
> **Action** (the THEN), **Loop / Flow**, **Component**, **Capability-request**.
> Never surface the storage names (`knowledge-pack`, `rule-pack`, `manifest`,
> `artifact`) in UI copy. Version is metadata — never shown in a name or ID.

---

## 1. Product in one screen

**Open Harness Hub** is a portable, database-backed **registry of reusable AI-pipeline
components** *and* a **conversational builder**. Its single admission rule: a
component earns a place only if it **measurably lifts capability over a bare LLM**
(`pipeline_score − bare_model_score > 0`) and the lift is *structural* (won't
vanish when the next model ships).

**The headline interaction (the whole product in one move):**

> **Paste a task → get back a working, costed, deployable flow built from existing components.**

Everything in the UI orbits that sentence. The landing page *is* the entry to it.
The catalog, governance, marketplace, and workspace are the supporting structure
that makes the returned flow trustworthy, cheap, swappable, and deployable.

**Three things the UI must always make legible:**

1. **Lift** — *why* this component/flow beats prompting a bare model (a benchmark delta).
2. **Governance** — provenance, license, verified facts, review status, freshness/revocation.
3. **Cost & portability** — what it costs, on which model, and that you can swap models and deploy it in your own environment.

---

## 2. Audience & tone context (for visual decisions)

- **Primary buyer (wedge):** compliance / risk / audit teams in regulated, esoteric
  domains (ESG·CSDDD, GxP, customs & trade, sanctions·AML, food/water safety). They
  value *proof* over flash.
- **Secondary:** AI consultants/agencies, SaaS teams adding AI features, ops teams
  converting procedures to workflows, dev-tool teams running long agentic jobs.
- **Implication for design:** **instrument-grade, not toy-grade.** Calm, precise,
  dense-but-legible. Closer to a developer console / financial terminal / lab
  instrument than a consumer app. Trust is the aesthetic.

---

## 3. Design principles

1. **The box is the product.** The landing page is one entry box. Resist adding
   marketing chrome above the fold. The fastest path from "I have a task" to "here
   is a costed flow" wins every layout argument.
2. **Show the lift, always.** Every component and flow carries a visible
   capability-lift signal. If we can't show why it beats a bare model, we don't
   show it as promotable.
3. **Governance is visible, not buried.** Provenance, license, verified, review,
   and freshness are first-class badges — the moat must be on-screen.
4. **One visual grammar for pipelines.** The seven-primitive legend (§6) is the
   spine of the catalog, the builder canvas, and the run trace. Learn it once, read
   it everywhere.
5. **Restraint over decoration.** Flat surfaces, hairline borders, one accent.
   Color carries *meaning* (primitive type, execution class, state) — never mood.
6. **Dense but breathable.** Information-rich screens (catalog, trace, cost matrix)
   on a strict 4px grid; generous negative space on entry/marketing screens.
7. **Every state is designed.** Empty, loading (skeleton), partial, error, blocked
   (by a gate), and success are all first-class — never an afterthought.
8. **Accessible by construction.** Color is never the only signal: primitive type =
   color **+** glyph **+** label. WCAG AA contrast minimum. Reduced-motion honored.

---

## 4. Brand & voice

- **Wordmark:** "Open Harness Hub" set in the UI sans, weight 700, tight tracking.
  Short form **"OHH"** or **"Hub"** acceptable in compact nav. A mark can use the
  Action-orange as a single accent (e.g. a node/operator glyph), never a gradient.
- **Tagline (hero, optional, ≤1 line):** *"Describe a task. Get a costed,
  deployable AI pipeline built from components that beat a bare model."*
- **Voice:** precise, declarative, quietly confident. Verbs over adjectives. State
  the mechanism ("cites CSDDD articles across 13 languages"), not the vibe ("powerful").
- **Microcopy rules:**
  - Use **Knowledge Corpus / Conditional / Action / Loop / Output**; never
    "manifest", "artifact", "rule pack" in user-facing text.
  - Costs are always qualified until live pricing exists: *"est."* and a tier label.
  - Never imply a placeholder is real: a hash/zero embedding shows a **"staging"**
    chip; a flow built on it shows **"preview retrieval"**, not "semantic".
  - Empty states teach the next action ("No saved flows yet — paste a task to build one").

---

## 5. Design tokens

> **Token *roles* are stable; token *values* come from the chosen visual direction**
> (`claude-design-prompt.md`). The tables below carry the shipped GitHub-dark palette
> as a **baseline fill** — keep the token *names*, swap the hex once a direction is
> picked. Whatever the direction, both themes must render the seven-primitive legend
> identically. §5.5 is a ready-to-fill CSS scaffold.

### 5.1 Color — neutrals & surfaces

| Token | Dark (app) | Light (marketing) | Use |
|---|---|---|---|
| `--bg` | `#0d1117` | `#ffffff` | page background |
| `--bg-subtle` | `#010409` | `#f6f8fa` | recessed areas, code wells |
| `--panel` | `#161b22` | `#ffffff` | cards, panels, menus |
| `--panel-2` | `#11161d` | `#f6f8fa` | nested panels, DAG nodes |
| `--line` | `#30363d` | `#d0d7de` | hairline borders, dividers |
| `--line-strong` | `#444c56` | `#afb8c1` | emphasized borders, focus rings (non-accent) |
| `--fg` | `#e6edf3` | `#1f2328` | primary text |
| `--fg-muted` | `#8b949e` | `#656d76` | secondary text, labels, metadata |
| `--fg-faint` | `#6e7681` | `#8c959f` | disabled, watermark |

### 5.2 Color — brand & semantic

| Token | Dark | Light | Meaning |
|---|---|---|---|
| `--accent` (brand / Action) | `#fb7714` | `#e8590c` | primary buttons, links, brand, the Action primitive |
| `--accent-weak` | `#3a2410` | `#fff1e6` | accent backgrounds, hover wash |
| `--success` / lift-positive | `#3fb950` | `#1a7f37` | positive lift, passed gate, healthy |
| `--warning` / review | `#d29922` | `#9a6700` | needs review, staging, caution (also the Conditional hue) |
| `--danger` / blocked | `#f85149` | `#cf222e` | blocked-by-gate, error, revoked (also Stop/End hue) |
| `--info` | `#58a6ff` | `#0969da` | informational, Output hue, neutral links in dark |
| `--verified` (governance) | `#39c5cf` | `#1b7c83` | verified facts, signed publisher, provenance OK — **the moat color**; distinct from the legend |

> **Note:** `--accent`, `--warning`, `--danger`, `--info` deliberately equal four
> primitive-legend hues (Action, Conditional, Stop/End, Output). That coupling is
> intentional — semantics and primitives share a language. `--verified` and
> `--success` sit *outside* the legend so governance and gate-pass read as their own
> signals. Always pair with a glyph + label so meaning never rests on hue alone.

### 5.3 Typography

| Token | Value | Use |
|---|---|---|
| `--font-sans` | `"Inter", -apple-system, "Segoe UI", system-ui, sans-serif` | all UI text |
| `--font-mono` | `"JetBrains Mono", "IBM Plex Mono", ui-monospace, SFMono-Regular, monospace` | component IDs, code, DAG node refs, costs/tokens, schema |

Component IDs (`pipeline/research-entity`) are **always mono**, often with a copy affordance.

Type scale (px / line-height): `12/16` micro · `13/18` caption/badge · `14/22` **body (base)** ·
`16/24` body-lg · `18/26` h5 · `20/28` h4 · `24/32` h3 · `30/38` h2 · `36/44` h1 ·
`48/56` display (hero only).
Weights: `400` body · `500` medium (labels) · `650` semibold (buttons, emphasis — matches shipped) · `700` headings/wordmark.
Tracking: `-0.01em` on ≥24px; `+0.04em` uppercase micro-labels (primitive labels, eyebrows).

### 5.4 Space, radius, elevation, motion

- **Spacing scale (4px base):** `4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 64`. Default gutter 16; section padding 24–32; marketing sections 64–96.
- **Radius:** `--r-sm 6` (chips, inputs) · `--r-md 9` (buttons, cards — matches shipped) · `--r-lg 12` (panels, modals) · `--r-pill 999` (legend chips, operator nodes). DAG nodes `10`.
- **Borders:** hairline `1px var(--line)`. DAG node: `border-left: 5px solid <primitive>`. Operator node: `border: 2px solid var(--operator)`.
- **Elevation (subtle — dev aesthetic):** `--e1` `0 1px 0 rgba(0,0,0,.2)` (cards) · `--e2` `0 8px 24px rgba(0,0,0,.35)` (menus/popovers) · `--e3` `0 16px 48px rgba(0,0,0,.5)` (modals). Light theme uses softer alpha (`.04 / .12 / .18`).
- **Motion:** durations `120ms` (hover/press) · `200ms` (enter/expand) · `320ms` (route/flow assembly). Easing `cubic-bezier(.2,.8,.2,1)`. Respect `prefers-reduced-motion`.
- **Focus ring:** `2px` accent at `2px` offset; never remove focus visibility.

### 5.5 CSS token scaffold (direction-agnostic — fill the values)

Paste this into the generated app. The **names and roles are fixed**; the **values are
the baseline** (shipped dark). When a direction is chosen (`claude-design-prompt.md`),
overwrite only the hex/type. Dark is `:root`; light overrides under `[data-theme="light"]`.

```css
:root {
  /* surfaces & text — baseline: GitHub-dark */
  --bg:#0d1117; --bg-subtle:#010409; --panel:#161b22; --panel-2:#11161d;
  --line:#30363d; --line-strong:#444c56;
  --fg:#e6edf3; --fg-muted:#8b949e; --fg-faint:#6e7681;

  /* ONE accent (brand + primary action) — the direction fills this */
  --accent:#fb7714; --accent-weak:#3a2410; --on-accent:#1a1300;

  /* semantic state */
  --success:#3fb950; --warning:#d29922; --danger:#f85149; --info:#58a6ff;
  --verified:#39c5cf;                 /* governance/moat — sits OUTSIDE the legend */

  /* the seven primitives + operator — re-tune per direction; keep 7 distinct + glyph + label */
  --p-input:#8b949e; --p-knowledge:#3fb950; --p-conditional:#d29922;
  --p-action:#fb7714; --p-loop:#a371f7; --p-stop:#f85149; --p-output:#58a6ff;
  --operator:#e3b341;

  /* type — direction may swap --font-display to a serif (warm) or grotesk (frontier) */
  --font-sans:"Inter",-apple-system,"Segoe UI",system-ui,sans-serif;
  --font-display:var(--font-sans);
  --font-mono:"JetBrains Mono","IBM Plex Mono",ui-monospace,SFMono-Regular,monospace;

  /* space (4px base) */
  --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:20px; --s6:24px;
  --s8:32px; --s10:40px; --s12:48px; --s16:64px;

  /* radius */
  --r-sm:6px; --r-md:9px; --r-lg:12px; --r-node:10px; --r-pill:999px;

  /* elevation (subtle) */
  --e1:0 1px 0 rgba(0,0,0,.2);
  --e2:0 8px 24px rgba(0,0,0,.35);
  --e3:0 16px 48px rgba(0,0,0,.5);

  /* motion */
  --t-fast:120ms; --t-mid:200ms; --t-slow:320ms; --ease:cubic-bezier(.2,.8,.2,1);

  /* focus */
  --focus:0 0 0 2px var(--bg), 0 0 0 4px var(--accent);
}

[data-theme="light"] {
  --bg:#ffffff; --bg-subtle:#f6f8fa; --panel:#ffffff; --panel-2:#f6f8fa;
  --line:#d0d7de; --line-strong:#afb8c1;
  --fg:#1f2328; --fg-muted:#656d76; --fg-faint:#8c959f;
  --accent:#e8590c; --accent-weak:#fff1e6; --on-accent:#ffffff;
  --success:#1a7f37; --warning:#9a6700; --danger:#cf222e; --info:#0969da;
  --verified:#1b7c83;
  --p-conditional:#9a6700; --p-output:#0969da; --p-stop:#cf222e;  /* legend hues darkened for white */
  --e1:0 1px 0 rgba(31,35,40,.04);
  --e2:0 8px 24px rgba(31,35,40,.12);
  --e3:0 16px 48px rgba(31,35,40,.18);
}

@media (prefers-reduced-motion: reduce){
  :root{ --t-fast:0ms; --t-mid:0ms; --t-slow:0ms; }
}
```

> When a direction swaps `--accent` away from orange, decide whether `--p-action`
> follows it (the shipped design couples them). Keep `--verified` and `--success`
> *outside* the legend so governance and gate-pass read as their own signals.

---

## 6. The seven-primitive visual language (signature system)

This legend is the product's identity. It appears in the DAG canvas, the run trace,
catalog facets, and component cards. These are the **baseline** hues (shipped today); re-tune them per the chosen direction (§5.5) but always preserve **seven distinct, color-blind-distinguishable hues — each with a glyph *and* a label** — in this primitive order, plus the distinct Logical-Operator node.

| Primitive (product label) | Hue token | Hex (dark) | Glyph (anchor) | Node shape | Maps from storage types |
|---|---|---|---|---|---|
| **Input** | `--p-input` | `#8b949e` gray | `⌖` target / `▸` | rounded rect | pipeline `inputs` |
| **Knowledge Corpus** | `--p-knowledge` | `#3fb950` green | `⛁` stack / `▦` | rounded rect | `knowledge-pack`, `dataset` |
| **Conditional** *(the IF)* | `--p-conditional` | `#d29922` amber | `◈` / `?` | rounded rect | `rule-pack`, `logic-pack` |
| **Action** *(the THEN)* | `--p-action` | `#fb7714` orange | `⚡` / `▶` | rounded rect | `persona`,`tool`,`processor`,`harness`,`adapter`,`rubric`,`benchmark` |
| **Loop / Flow** | `--p-loop` | `#a371f7` purple | `↻` | rounded rect | `pattern`, `pipeline` |
| **Stop / End** | `--p-stop` | `#f85149` red | `⊘` / `■` | rounded rect | structural guard |
| **Output** | `--p-output` | `#58a6ff` blue | `⎘` / `✓` | rounded rect | pipeline `outputs` |
| **Logical Operator** *(subtype, combines Conditionals)* | `--operator` | `#e3b341` gold | `◇` diamond | **pill, 2px full border** | OR / AND combiner node |

**DAG node anatomy** (the repeated unit on the canvas and trace):

```
┌─────────────────────────────────────────────┐   ← 5px left border in primitive hue
│ KNOWLEDGE CORPUS                  [rag] [▲]  │   ← uppercase micro-label (hue) + subtype chip + lift
│ CSDDD article corpus                          │   ← component name (sans, 14/22)
│ knowledge-corpus/csddd-articles               │   ← id (mono, faint, copyable)
│ ⛁ rag_vector · static · 13 langs · ✔ sourced  │   ← retrieval/exec/provenance facts
└─────────────────────────────────────────────┘
```

- **Operator node** (OR/AND): pill, centered, gold 2px border, `◇` glyph + role label.
- **Action subtypes** get a small subtype chip: `persona · tool · processor · harness · adapter · rubric · benchmark`.
- **Knowledge Corpus** shows its `retrieval` trigger chip(s): `keyword · regex · rag · exact-id · classifier · graph`, and `static`/`dynamic`.
- **Legend bar** sits above any canvas: one chip per primitive (`swatch + glyph + label`), `cursor:help`, with subtypes on hover.

**Execution-class accent** (orthogonal to primitive — drives safety/cost UI):
`static-information` (read-only, dot `--fg-muted`), `text-operation` (pure, dot `--info`),
`code-executing` (sandboxed/credentialed/cost-gated, dot `--accent`). Surfaced as a
small left-edge dot on cards and as a filter facet.

---

## 7. Core reusable components

These are the atoms Claude should design once and reuse on every page.

### 7.1 Component card (the most-repeated unit)

```
┌───────────────────────────────────────────────┐
│ ● ⚡ ACTION · harness          ▲ +0.41 lift  ⋯ │  exec-dot + primitive + type | lift badge | menu
│ Cite-first ESG counsel                          │  name (16/24, 650)
│ harness/esg-cite-first                          │  id (mono, faint, copy)
│ Holds a deterministic citation gate before…     │  one-line description (2-line clamp)
│ ─────────────────────────────────────────────  │
│ ✔ sourced  ◆ stable  ⛁ rag  $ balanced  MIT     │  badges row (§7.2)
└───────────────────────────────────────────────┘
```

Variants: compact (search row), grid tile (browse), inline chip (inside a flow).

### 7.2 Badges & chips (the trust/meaning layer)

| Badge | Looks like | States |
|---|---|---|
| **Lift** | `▲ +0.41` (success) / `▲ structural` / `— unproven` (muted) | measured delta · structural-class label · unproven (no benchmark) |
| **Provenance** | `✔ sourced` (verified) / `⚠ unsourced` (warning) | has `source_url`+author+license · missing → review |
| **Verified facts / publisher** | `🛡 verified` (verified hue) | signed publisher / verified-fact corpus |
| **Execution class** | dot + `static · text-op · code` | three classes (§6) |
| **Lifecycle** | `◷ abstract · ◐ experimental · ◑ beta · ◆ stable` | maturity ladder; `abstract` = capability-request slot |
| **Cost band** | `$ cheap · $$ balanced · $$$ quality · ⌂ local-first` | qualified "est." until live pricing |
| **Freshness / CDC** | `⟳ fresh · ⟳ stale · ⊘ revoked` (dynamic corpora only) | volatile-fact handling |
| **License** | `MIT · CC-BY-4.0` mono pill | code vs data shaped |

Chips are pill (`--r-pill`), `13/18`, 1px border, hue-tinted background at low alpha.

### 7.3 Buttons & inputs

- **Primary:** `--accent` fill, `#1a1300` text, weight 650, radius 9 (shipped). Hover darken 6%, press scale .98.
- **Secondary:** transparent, `--line` border, `--fg` text. **Ghost:** text + accent on hover. **Danger:** `--danger` outline → fill on confirm.
- **Inputs:** `--panel-2` fill, `--line` border, `--r-sm`, 14/22, focus → accent ring. Mono variant for IDs/paths.
- **Tabs, segmented control** (cheap/balanced/quality), **toggle** (light/dark, simulate/live), **dropdown/command menu** (⌘K global), **slider** (budget/quality target).

### 7.4 The hero entry box (landing centerpiece — design this first)

The single most important component. The landing page is *mostly* this.

```
                       Open Harness Hub
        Describe a task. Get a costed, deployable AI pipeline.

   ╭───────────────────────────────────────────────────────────╮
   │  Describe the task you want an AI pipeline to do…           │   ← large textarea, auto-grow
   │                                                             │     placeholder = real example
   │                                                       Build │   ← accent button, ⌘↵ to submit
   ╰───────────────────────────────────────────────────────────╯
        Try:  ▸ grade suppliers against CSDDD   ▸ triage 311 reports
              ▸ review a contract for renewal risk   ▸ redact a PDF

                 Browse the catalog · Sign in · How it works
```

- **Constraints (progressive, collapsed by default):** a single "Add constraints"
  affordance expands chips for **hosting** (local · cloud · BYO-cloud/air-gap),
  **privacy boundary**, **budget**, **quality target**. Hidden until asked — the bare
  box must dominate.
- **Behavior:** Enter inserts newline; **⌘/Ctrl+Enter or Build** submits → routes to
  `/build` (parse state). Example chips fill the box and submit.
- **Visual:** input is the brightest element on the page; everything else recedes.
  Centered column, max-width ~720px, vertically ~40% from top. No carousel, no
  feature grid above the fold.

### 7.5 Flow canvas (the DAG)

Left-to-right lanes by stage (Input → Input-Formatting → Persona → Knowledge → Conditional → Tools → Model/Harness → Post-process → Evaluate → Output). Nodes per §6. Edges hairline with arrowheads; OR/AND **operator nodes** merge branches; **leaf branches** allowed. Legend bar pinned top. Node click → inspector drawer (right) with full component detail + **swap** action. Empty lanes are visible but dimmed (teaches the shape).

### 7.6 Run / trace (the audit record)

A vertical step log rendered from the `PipelineObject`: per step show stage (primitive
hue), component ref (mono), **model-call flag**, tokens, **cost**, timing (ms), status
(✓ / ⚠ / �—simulated). Header totals: total cost, tokens, wall-time, citations, review
status. A "simulate" banner when steps are echo-stubs. This is the replayable
compliance artifact — make it exportable.

### 7.7 Cost & model-swap matrix

Three columns (**cheap · balanced · quality-first**) + a **local-first** option, each:
route per stage, est. cost (qualified), latency band, risk notes. A model-swap control
re-prices the whole flow. Until live pricing exists, amounts render as bands with an
explicit *"est. — calibrate against real runs"* note (never a fake precise dollar).

### 7.8 Faceted filter rail

Left rail (catalog/search): facets for **primitive** (the seven, color-swatched),
**type**, **industry**, **capability**, **execution class**, **lifecycle**, **trust
boundary**, **cost band**, **license**, **has-benchmark/lift**. Multi-select chips
echo at the top of results; URL-encoded for shareable searches.

### 7.9 System states

Skeleton loaders (cards, canvas, trace) · empty states (teach next action) · partial
(some results) · **blocked-by-gate** (a flow/component stopped by the lift/provenance
gate, with the *reason* and the fix) · error (recoverable, with retry) · toasts
(saved, copied, exported) · confirm dialogs (destructive/outward actions).

---

## 8. Page inventory (the full sitemap)

Grouped into **Marketing** (light theme, marketing shell) and **App** (dark theme,
app shell). Routes are indicative. Pages flagged ★ are the ones to design first.

### Index

| # | Route | Page | Shell | Priority |
|---|---|---|---|---|
| 8.1 | `/` | **Landing — the entry box** | marketing | ★ |
| 8.2 | `/build` | Builder — parse & constraints | app | ★ |
| 8.3 | `/build/results` | Builder — three costed options | app | ★ |
| 8.4 | `/flow/:id` | Flow canvas (DAG) | app | ★ |
| 8.5 | `/flow/:id/cost` | Cost & model-swap matrix | app | |
| 8.6 | `/flow/:id/run` | Run / playground (trace) | app | |
| 8.7 | `/flow/:id/deploy` | Deploy & export | app | |
| 8.8 | `/browse` | Catalog home (faceted) | app | ★ |
| 8.9 | `/search` | Search results (hybrid) | app | ★ |
| 8.10 | `/browse/:primitive` | Browse by primitive | app | |
| 8.11 | `/c/:type/:slug` | Component detail (+ type variants) | app | ★ |
| 8.12 | `/c/:type/:slug/lift` | Lift evidence / benchmark | app | |
| 8.13 | `/compare` | Component compare | app | |
| 8.14 | `/library/by-capability` | Capability map | app | |
| 8.15 | `/requests` | Capability-request board | app | ★ |
| 8.16 | `/requests/new` | Submit a capability-request | app | |
| 8.17 | `/requests/:id` | Capability-request detail | app | |
| 8.18 | `/marketplace` | Premium component marketplace | app | |
| 8.19 | `/contribute` | Community build / earn credits | app | |
| 8.20 | `/publishers` · `/publishers/:id` | Verified publishers | app | |
| 8.21 | `/review` · `/review/:ticket` | Review queue / ticket | app | |
| 8.22 | `/freshness` | CDC / freshness / revocation | app | |
| 8.23 | `/audit` | Audit export / compliance pack | app | |
| 8.24 | `/app` | Workspace dashboard | app | ★ |
| 8.25 | `/registry` | Private registry | app | |
| 8.26 | `/ingest` · `/ingest/:job` | Managed ingestion | app | |
| 8.27 | `/runs` · `/runs/:id` | Runs history / trace explorer | app | |
| 8.28 | `/evals` | Evals & benchmarks | app | |
| 8.29 | `/usage` | Cost / usage analytics | app | |
| 8.30 | `/team` | Team & collaboration | app | |
| 8.31 | `/settings` | Settings (providers, deploy, billing) | app | |
| 8.32 | `/pricing` | Pricing | marketing | ★ |
| 8.33 | `/how-it-works` | How it works | marketing | |
| 8.34 | `/why` | The capability-lift bar (the moat) | marketing | |
| 8.35 | `/use-cases` · `/use-cases/:slug` | Solutions / use cases | marketing | |
| 8.36 | `/compare/:competitor` | Comparison pages | marketing | |
| 8.37 | `/docs/*` | Docs · spec · CLI · API · emitters | marketing | |
| 8.38 | `/changelog` · `/blog` · `/about` · `/trust` | Content & trust | marketing | |
| 8.39 | `/signin` · `/signup` · `/onboarding` | Auth & onboarding | minimal | ★ |
| 8.40 | `/404` · `/500` · `/status` · `/maintenance` | System | minimal | |

---

### 8.1 ★ Landing — the entry box  `/`

- **Purpose:** the single move — paste a task, build a flow. Stays bare.
- **Layout:** marketing shell (slim top bar: wordmark · Browse · Pricing · Docs · Sign in). Centered hero = the entry box (§7.4) and nothing competing above the fold.
- **Below the fold (quiet, optional, scroll-revealed):** a one-row "how it works" (paste → retrieve → assemble → cost → deploy), the capability-lift one-liner, a thin strip of wedge logos/domains, footer. Keep it short; the box is the star.
- **Primary action:** Build (→ `/build`). **Secondary:** Browse the catalog, Sign in.
- **States:** focused (box brightens), submitting (button → spinner, route transition).

### 8.2 ★ Builder — parse & constraints  `/build`

- **Purpose:** confirm the parsed intent and (optionally) constraints before assembling.
- **Elements:** the task text (editable, persists from landing); a parsed-intent summary (detected task kind, domain, modality, privacy hints); the constraints panel (hosting · privacy boundary · budget · quality target); an "Assemble" CTA. A subtle note if retrieval is **preview** (placeholder embeddings) vs **semantic**.
- **Primary action:** Assemble (→ `/build/results`). **Empty/edge:** ambiguous task → ask one clarifying question inline.

### 8.3 ★ Builder — three costed options  `/build/results`

- **Purpose:** present cheap / balanced / quality-first flows for the task.
- **Layout:** three result cards side-by-side (segmented by tier), each: a **mini-DAG preview** (primitive-colored nodes), component count, **est. cost band**, latency band, risk notes, and the headline **lift** vs a bare model. A fourth **local-first** option when feasible.

```
┌─ CHEAP ───────┐  ┌─ BALANCED ★ ──┐  ┌─ QUALITY-FIRST ┐
│ mini-DAG      │  │ mini-DAG      │  │ mini-DAG       │
│ 4 components  │  │ 6 components  │  │ 9 components   │
│ $ est. low    │  │ $$ est. mid   │  │ $$$ est. high  │
│ ▲ +0.21 lift  │  │ ▲ +0.41 lift  │  │ ▲ +0.55 lift   │
│ [Open flow]   │  │ [Open flow]   │  │ [Open flow]    │
└───────────────┘  └───────────────┘  └────────────────┘
```

- **Primary action:** Open flow (→ `/flow/:id`). Balanced pre-selected.

### 8.4 ★ Flow canvas (DAG)  `/flow/:id`

- **Purpose:** read, understand, and edit the assembled pipeline.
- **Elements:** the §7.5 canvas + pinned legend; right **inspector drawer** on node click (full component detail, provenance, **swap component**, alternatives ranked by lift); top toolbar (Run · Cost · Deploy · Save · Share · model-swap select). Validity banner if a hard wiring rule is violated (e.g. a Conditional wired raw to a model without a harness).
- **Primary action:** Run, Deploy, or Save. **Blocked state:** if a node is `abstract`/capability-request, show a "build-on-demand" slot inline.

### 8.5 Cost & model-swap matrix  `/flow/:id/cost`
The §7.7 matrix as a full page; re-prices on model swap; export the cost table.

### 8.6 Run / playground  `/flow/:id/run`
Input form (from the pipeline's `inputs`) → run (simulate or live) → the §7.6 trace. "Simulate" banner when steps echo. Sample scenarios selectable.

### 8.7 Deploy & export  `/flow/:id/deploy`
Tabs for export targets: **runtime bundle · Terraform · MCP server · Docker · CLI** plus emitters (Croissant, HF card, promptfoo, lm-eval, CycloneDX-ML, SPDX, C2PA, EU-AI-Act, JSON-LD, DPV). Each: copy/download + a "what's frozen vs live" note (the pricing boundary: text-op/static = freezable; code-executing/dynamic = recurring).

### 8.8 ★ Catalog home (faceted)  `/browse`
- **Layout:** left facet rail (§7.8) + results grid of component cards (§7.1) + sort (lift · recency · usage · cost). Tabs/segments across the **seven primitives** as the top-level cut.
- **Header:** a search input (→ `/search`), result count (rendered from live data — never hand-typed), active facet chips.

### 8.9 ★ Search results (hybrid)  `/search?q=`
Same shell as browse, ranked by hybrid relevance (keyword + vector + facet). Each row: card + **why-matched** snippet (matched terms / semantic) + lift + provenance. A retrieval-mode indicator (semantic vs preview). Zero-results → suggest a **capability-request** (turn the gap into demand).

### 8.10 Browse by primitive  `/browse/:primitive`
A primer per primitive (what it is, its stage, subtypes) + filtered results. Educational landing that teaches the legend.

### 8.11 ★ Component detail  `/c/:type/:slug`
The reference page for one component. Shared skeleton + type-specific body:

- **Header:** primitive hue bar, name, id (mono+copy), badges row (§7.2), exec-class, lifecycle, version (metadata), **Add to flow** CTA, menu (emit/export, compare, request-update).
- **Body (shared):** description · stage placement diagram · **lift evidence** (delta + how measured, or "unproven") · **provenance panel** (source_url, author, license, last-verified) · dependencies (what it consumes/emits) · used-in pipelines · sample run.
- **Type variants:**
  - **Pipeline** — full DAG, sample runs, benchmark score, deploy CTA.
  - **Knowledge Corpus** — retrieval triggers, static/dynamic, **freshness/CDC/revocation** panel, fact count (live), provenance per source.
  - **Conditional** — rule families, `when → then` table, languages.
  - **Action** (persona/tool/processor/harness/adapter/rubric/benchmark) — subtype-specific: tool shows params/returns/side-effects; harness shows model_targets + trust boundary; adapter shows transport + cost model; rubric shows dimensions/weights; benchmark shows dataset + judge + reproducibility `(commit_sha, dataset_version, run_date)`.
  - **Dataset** — schema, label distribution, provenance.
  - **Pattern** — the reusable flow shape, where it applies.

### 8.12 Lift evidence  `/c/:type/:slug/lift`
The capability-lift detail: the task, `bare_model_score` vs `pipeline_score`, the delta, the durability class (why it won't close), and the decay signal to watch. A bar/delta chart (§12).

### 8.13 Component compare  `/compare?ids=…`
Side-by-side table of 2–4 components: lift, cost, exec-class, provenance, lifecycle, deps. For choosing between alternatives during a swap.

### 8.14 Capability map  `/library/by-capability`
A matrix/heatmap of capability × coverage, surfacing where the catalog is deep vs where gaps exist (gaps link to `/requests/new`). Reinforces the negative-space thesis.

### 8.15 ★ Capability-request board  `/requests`
- **Purpose:** demand capture for what the catalog lacks (build-on-demand funnel).
- **Elements:** list/board of open requests with **demand_count** (votes), `target_type`, status chip (requested → triaged → researching → building → built → verifying → promoted/rejected), and a **"Request this"/upvote** action. Sort by demand. CTA: "Need something missing? Request it."
- **Note:** capability-requests are at `abstract` maturity — render distinctly from real components (dashed border, `◷` glyph), never as tenant-visible components.

### 8.16 Submit a capability-request  `/requests/new`
Form: describe the missing capability, intended `target_type`, the task it should lift, sources you know of. Pre-filled when arriving from a zero-result search. On submit → demand aggregation.

### 8.17 Capability-request detail  `/requests/:id`
Status **timeline** (the promotion path), candidate sources found, the two-axis lift gate it must pass, and two fulfillment paths: **premium agent build** (hosted, paid) and **community build** (contributor earns **credits** when the shared component passes the gate). When promoted, links to the minted component at `experimental`.

### 8.18 Premium component marketplace  `/marketplace`
Browse premium/community-built components; revenue-share indicated; same card grammar with a "premium" treatment. Filter by gate-passed, publisher, lift.

### 8.19 Community build / earn credits  `/contribute`
How to fulfill a capability-request, the credit mechanics (credit only when the shared component passes the lift gate), and contribution status. Links to the request board.

### 8.20 Verified publishers  `/publishers` · `/publishers/:id`
Directory of signed publishers (agencies, standards bodies, governments, domain experts) and their verified components/corpora. Publisher profile shows the `🛡 verified` provenance trail.

### 8.21 Review queue / ticket  `/review` · `/review/:ticket`
Tenant-curator surface: queue of `review_ticket`s (risk-ranked), each with the object, the open question (provenance/signature/volatility), and approve/route/reject actions. The promotion-boundary enforcer — nothing tenant-visible with an open high-risk ticket.

### 8.22 CDC / freshness / revocation  `/freshness`
Dashboard of **dynamic** Knowledge Corpora: freshness status, last fetch, CDC events, revoked facts. The recurring-value surface (decays when the user disconnects → justifies subscription).

### 8.23 Audit export / compliance pack  `/audit`
Generate a compliance bundle: which components ran, what was cited, provenance/licenses, review trail, costs. PDF/CSV/JSON export for the wedge buyer.

### 8.24 ★ Workspace dashboard  `/app`
First screen after sign-in. Cards: **resume/last flows**, **recent runs** (with cost), **usage & credits** (toward plan limits), **suggested gaps** (capability-requests trending in your domain), quick "paste a task" box (the entry box, persistent). Empty state teaches: "Paste a task to build your first flow."

### 8.25 Private registry  `/registry`
The tenant's own components (managed-ingested + saved). Same browse grammar, scoped to the workspace, with visibility/sharing controls.

### 8.26 Managed ingestion  `/ingest` · `/ingest/:job`
Connect a source surface (upload a procedure library, point at an OSS GitHub ecosystem, a standards corpus). Job view: license filter → normalize → dedupe → embed → review-route → **lift gate** → promoted components. Progress per stage; rejects shown with reason (filler/no-lift). This is a billable line — make the value (components produced, gate-passed) legible.

### 8.27 Runs history / trace explorer  `/runs` · `/runs/:id`
The experience database, user-facing: searchable run history; each run opens the §7.6 trace. Filter by flow, cost, status, model. Diff two runs (cost/quality drift).

### 8.28 Evals & benchmarks  `/evals`
Run a rubric/benchmark against a flow; see scores, the bare-vs-pipeline delta, regression over time, and review scaffolding. The "prove the lift" surface.

### 8.29 Cost / usage analytics  `/usage`
Charts: spend by flow/model/day, token volume, cache-savings, embeddings/eval runs, ingestion jobs, build-on-demand spend. Plan limits & credits. (§12 viz.)

### 8.30 Team & collaboration  `/team`
Members, roles/permissions, shared workspaces, component ratings/telemetry, activity. Collaboration is a Team-tier feature.

### 8.31 Settings  `/settings`
Sections: **Model providers / BYO keys** (and the adapter/model-swap defaults), **Deployment targets** (cloud/BYO/air-gap), **Privacy boundaries**, **Billing & plan** (tier, usage add-ons, invoices), **Workspace**, **Profile**, **API tokens**.

### 8.32 ★ Pricing  `/pricing`
The four tiers as columns — **Free/OSS · Pro (~$29–49/seat/mo) · Team (~$199–499/mo) · Enterprise (custom)** — plus a **usage add-ons** row (source scans, embeddings, eval runs, media gen, managed ingestion, build-on-demand). Make the **freezable-vs-live** boundary explicit (export is free; the live/governed layer + build-on-demand is the subscription). Prices marked indicative until validated.

### 8.33 How it works  `/how-it-works`
The headline interaction expanded into five steps with visuals (parse → hybrid-retrieve → assemble → cost/model-swap → deploy), each tied to the on-screen UI. One worked wedge example (ESG/CSDDD).

### 8.34 The capability-lift bar (the moat)  `/why`
The differentiation page: the only-if-it-lifts rule, the anti-fragility-to-model-progress argument, the governance moat, the experience database. The competitive table (vs prompt hubs, visual builders, model registries, provider agent platforms, awesome-lists).

### 8.35 Solutions / use cases  `/use-cases` · `/use-cases/:slug`
Index + per-vertical pages (ESG·CSDDD, GxP, customs, AML, food/water safety; consultants/agencies). Each: the buyer's trigger, the bare-model failure, the composed flow, the lift, a deploy CTA.

### 8.36 Comparison pages  `/compare/:competitor`
One page per competitor category (LangChain Hub/LangSmith, Dify/Flowise/Langflow/n8n, Hugging Face Hub, OpenAI GPTs/Bedrock/Vertex, awesome-lists). Honest "how we differ" framing from the brief.

### 8.37 Docs  `/docs/*`
Developer docs shell (left nav + content + on-page TOC): the spec, **CLI (`oh-hub`)**, **API reference** (search/recommend/pricing/pipeline-generation endpoints), **emitters/export formats**, concepts (the seven primitives, stages, execution classes), and how-tos (run a pipeline, assemble from a task, add a component, deploy).

### 8.38 Content & trust  `/changelog` · `/blog` · `/about` · `/trust`
Changelog (what's new), blog/research notes, about/project (non-goals stated plainly), trust/security/privacy (data handling, no real PII, synthetic/public only, SECURITY policy).

### 8.39 ★ Auth & onboarding  `/signin` · `/signup` · `/onboarding`
Minimal shell. Sign in/up (SSO for Enterprise). Onboarding: paste a first task, connect a model key (or use local/simulate), pick a wedge domain → land in `/app` with a built first flow.

### 8.40 System  `/404` · `/500` · `/status` · `/maintenance`
On-brand minimal pages; 404 offers the entry box and Browse; status shows service/queue health.

---

## 9. Layout system & shells

- **Marketing shell:** slim sticky top bar (wordmark · Browse · Pricing · Docs · How it works · Sign in / Build), full-width sections, footer (product · solutions · docs · company · legal · trust). Light theme default; dark toggle available.
- **App shell:** left icon+label sidebar (Build · Browse · Requests · Runs · Evals · Registry · Usage · Settings), top bar with **global ⌘K search/command**, workspace switcher, credits meter, account menu. Content max-width ~1280; tables/canvas can go wider. Dark theme default; light available.
- **Minimal shell:** centered card, wordmark only (auth, system).
- **Responsive:** breakpoints `sm 640 · md 768 · lg 1024 · xl 1280 · 2xl 1536`. Sidebar collapses to icons < lg, drawer < md. Facet rail → bottom-sheet/modal on mobile. The DAG canvas → vertical stack on mobile (lanes become sections). The entry box is full-width with comfortable padding on mobile. Tables → stacked cards < md.

---

## 10. Motion & interaction

- **Assembly animation (signature):** on `/build/results` → `/flow`, nodes appear stage-by-stage left-to-right (≤320ms total), each fading/sliding in its primitive hue — visualizes "assembled from components." Disabled under reduced-motion (instant).
- **Hover:** cards lift via border-brighten (not large shadow). Legend chips reveal subtypes. Node hover highlights its edges.
- **Press:** scale .98, 120ms. **Copy id:** flash a check + toast.
- **Route transitions:** 200–320ms cross-fade; preserve scroll on back.
- **Live regions:** run trace appends with a subtle highlight; long jobs (ingestion, embedding) stream progress per stage.

---

## 11. Accessibility

- **WCAG 2.1 AA** contrast for text and essential UI. Verify the legend hues against `--panel` in both themes; darken light-theme variants where needed (table §5.2 already does).
- **Never color alone.** Primitive = color + glyph + label. Badges carry text. State (blocked/success/review) carries an icon + label.
- **Keyboard:** full traversal; ⌘K command menu; the entry box submits on ⌘/Ctrl+Enter; canvas nodes are focusable with arrow-key navigation; visible focus ring (§5.4).
- **Screen readers:** semantic landmarks; the DAG exposes a linear text description (stage order + components) as an accessible alternative to the visual graph; the trace is a real list.
- **Reduced motion:** honor `prefers-reduced-motion` (no assembly animation, instant transitions).
- **Color-blind safety:** the seven hues are distinguishable, but glyph + label is the real signal; provide a high-contrast theme option.

---

## 12. Data visualization

- **Lift delta:** a paired/diverging bar — `bare_model_score` vs `pipeline_score`, delta called out in `--success`. Used on `/c/:slug/lift`, result cards, evals.
- **Cost:** stacked area/bar by model/flow/day (`/usage`); cost-band pills elsewhere (no fake precise dollars until live pricing).
- **Coverage/capability map:** heatmap (capability × depth) on `/library/by-capability`; gaps tinted toward `--warning` and linked to requests.
- **Run trace:** the step log is the primary "viz" — keep it tabular and dense.
- **Demand:** capability-request `demand_count` as a simple ranked bar on `/requests`.
- Chart palette: neutrals + one accent per series; reuse primitive hues when a series *is* a primitive. Always labeled; never rely on hue alone.

---

## 13. Handoff notes for Claude (generation order & constraints)

1. **Lock the chosen direction's tokens + the re-tuned seven-primitive legend first** (§5.5–§6). Everything else composes from them. Deliver light + dark in parity.
2. **Then the hero entry box (§7.4) and the landing page (§8.1).** Keep it bare — one box, examples, quiet links. This is the product's first impression; resist feature grids.
3. **Then the builder triplet:** `/build` → `/build/results` (three costed cards) → `/flow/:id` (DAG canvas + inspector). This *is* the headline interaction.
4. **Then the catalog grammar:** component card (§7.1) + badges (§7.2) + `/browse` + `/search` + `/c/:type/:slug`. Get the card right; it repeats hundreds of times.
5. **Then governance & demand:** `/requests` board, provenance/verified treatments, review queue.
6. **Then workspace & pricing:** `/app` dashboard, `/pricing`, `/settings`.
7. Marketing/docs/system pages last.

**Hard constraints to honor in any generated screen:**

- Use the **canonical vocabulary** (Knowledge Corpus · Conditional · Action · Loop · Output · Component · Capability-request). Never "manifest/artifact/rule-pack" in UI copy.
- **One accent, from the chosen direction** (§5.5; explore via `claude-design-prompt.md`). Spend a single accent on the primary action + brand mark; the token *names* (§5) are fixed, the *values* come from the direction. Never introduce a second competing accent.
- **Show lift, governance, and cost** on every component/flow surface (§3, §7.2).
- **Counts are dynamic** — render catalog/result counts from data; never hard-code a number into a design (the project's "no magic values" rule).
- **Don't fake precision** — costs are qualified bands and embeddings show a "staging/preview" state until real; design the honest state, not the aspirational one.
- **Every state designed** (§7.9): empty, loading, partial, blocked-by-gate, error, success.
- **Instrument-grade restraint** (§2–§3): hairline borders, flat surfaces, one accent, color = meaning.

---

## 14. Backend-connected views (lifecycle · monitoring · component-generated data · foundry)

The registry is **not a pile of static definitions** — the backend now has
versioning + CDC, dependency graphs, an evidence-driven generation **foundry**
(`docs/architecture/evidence-driven-component-factory.md`), and, most importantly,
**code-executing components that create data stores and emit their own views.**
These pages connect the front-end to that growing backend. They use the same
shells, tokens, seven-primitive legend, badges, honest-states, and accessibility
rules as §5–§13 — and always show **lift · governance · cost**.

> **The frame (think outside the static card).** A component is not just a
> definition — it is an **operator**. A code-executing Action (tool/harness), a
> **dynamic Knowledge Corpus**, or a Pipeline can *create a data store, write to
> it, and emit views/dashboards/pages over it*. The UI is a **host** for
> component-generated surfaces, not only a browser of cards. This maps onto the
> execution-class model (§6): only `code-executing` + dynamic-corpus components
> create stores/views — which is also the **recurring-revenue boundary** (a static
> export can't keep a live store fresh). Static/text-op components stay freezable.

### 14.1 New reusable components (extend the §7 kit)

| Component | What it is |
|---|---|
| **Version-diff viewer** | side-by-side body diff + retrieval-trigger/rule diff + **lift-delta change** + provenance change |
| **Dependency graph** | consumes/emits, upstream/downstream, impact highlight — reuses the DAG legend grammar (§6) |
| **Pin control** | pin/unpin a version; `📌 pinned@1.2.0` vs `floating(latest)` chip; update-available dot |
| **Customization panel** | typed per-type override editor with reset-to-default + "fork as variant" CTA |
| **Widget kit** | metric tile · time-series · table · status light · distribution — the dashboard atoms |
| **Data-store / query view** | schema header + query builder + results grid + "save as view" |
| **Funnel chart** | the foundry funnel (probed→…→promoted) as a narrowing flow |
| **Lift-over-time / decay chart** | a component's measured lift re-benchmarked across model generations; decay = none/watch/decaying |
| **Alert-rule editor** | condition → channel (in-app/email/webhook) builder |

### 14.2 Component history & audit trail — `/c/:type/:slug/history` *(detail tab)*
Timeline of every change + run + governance event (created · version bumped · re-benchmarked · source refreshed · CDC event · revoked · reviewed · pinned-by-N-tenants). Filter by event type; each entry links to the diff / run trace / review ticket. The replayable record (ties to the `PipelineObject` + CDC). **Connects to:** CDC events, run ledger, review tickets.

### 14.3 Versioning — `/c/:type/:slug/versions` *(detail tab)*
Version list (semver, per-version lifecycle, **per-version lift delta**, created/by). Select two → **diff** (§14.1). Actions: **pin** a version, **roll back** (mints a *new* version equal to the old — never mutate a published one), and compare lift across versions ("did v1.3 actually lift more than v1.2?"). Version is metadata — never in the name/ID. **Connects to:** version store, CDC, the measurement engine.

### 14.4 Pinning & update management — `/pins` *(+ pin control everywhere a component appears)*
Workspace view of pinned components/versions so flows don't drift when a component updates. Pinned vs floating; "3 flows pin `knowledge-corpus/csddd-articles@1.2.0`"; **update-available → diff preview before accepting**; bulk update. In a flow, every node shows `pinned@version` or `floating(latest)`. A pinned **dynamic** corpus still receives freshness/revocation alerts. **Connects to:** version store, CDC, flows.

### 14.5 Customization & forking — `/c/:type/:slug/customize` *(detail tab)*
Typed override panel per type: tool params · corpus retrieval-trigger + chunking · rubric dimensions/weights · harness `model_target` + trust boundary · persona stance · Conditional thresholds. Reset-to-default. **"Save as tenant variant" → fork** with lineage recorded (`forked-from id@version`); forks live in the private registry; a **lineage tree** shows what derived from what. A behavior-changing customization **re-triggers lift measurement** (the delta may differ). **Connects to:** private registry, lineage, the measurement engine.

### 14.6 Dependencies & impact — `/c/:type/:slug/dependencies` *(detail tab)*
Dependency graph (what it consumes/emits; upstream sources/corpora; downstream pipelines/flows). **Impact preview before an edit/deprecate:** "this affects N flows and M pinned tenants" (the codegraph-impact idea, productized). Honors the hard wiring rules (a Conditional reaches a model only through a harness). **Connects to:** the graph/edge store, flows, pins.

### 14.7 Component monitoring — `/c/:type/:slug/monitor` *(detail tab)*
Per-component health: run volume · success/error rate · p50/p95 latency · cost/run · cache-hit · freshness (dynamic corpora) · **lift-over-time** (re-benchmarked as new base models ship → the **decay signal**). Alerts when decay flips to `decaying`, freshness goes stale, or error-rate spikes. This page *is itself* a component-generated data page (§14.9). **Connects to:** run telemetry, the measurement engine, CDC.

### 14.8 Fleet health & decay board — `/monitor`
Cross-registry observability: components by health; the **decay board** (which lifts are eroding as models improve — prune candidates, per the anti-fragile moat); freshness/revocation queue; cost hot-spots; top components by usage/lift. The "keep the registry parked on the moving frontier of what models still can't do" operations view. **Connects to:** the measurement engine, CDC, usage telemetry.

### 14.9 Component-generated views & data pages — view host at `/c/:type/:slug/views/:viewId`
The paradigm. A component may **declare views it produces** (a chart, a table, a dashboard, a data page) and the UI hosts them with product chrome: a telemetry processor emits a metric time-series; a benchmark emits a score trend; a dynamic corpus emits a freshness/coverage page; a monitoring Action emits a status dashboard. The host renders a **typed view spec** (a widget list bound to a data store) and **sandboxes** code-executing components. **Connects to:** data stores (§14.10), the widget kit, the sandbox runtime.

### 14.10 Data stores created by components — `/stores` · `/stores/:id`
Code-executing components and dynamic corpora **create data stores** (a table / collection / index). List: store · owning component · schema · row count (live) · freshness · size/cost. Detail: browse rows, schema, **lineage** (which component writes it), retention/CDC. Stores are first-class backend objects the FE exposes — the substrate the next two pages build on. **Connects to:** Postgres/pgvector/object-store, the owning component, CDC.

### 14.11 Query & view builder — `/stores/:id/query` *(saved views)*
Build a query/view over a store (filter · group · aggregate · join within tenant scope), preview a results grid, **save as a named view** (shareable, embeddable). Materialized vs live. Saved views become dashboard widgets (§14.12) and can **back a component's input**. Honest states — no fake rows; empty/preview/partial designed. **Connects to:** the store engine, saved-view registry.

### 14.12 Dashboard composer — `/dashboards` · `/dashboards/:id`
Compose dashboards from widgets bound to data stores (§14.10), saved views (§14.11), run telemetry, and component monitors. Drag/resize grid, **pin widgets**, set refresh, share/embed. This is how a user turns the growing backend into **monitoring pages and graphs for their components and pipelines** — the "components that generate pages/graphs for monitoring" ask, generalized into a first-class builder. **Connects to:** stores, saved views, telemetry, embed tokens.

### 14.13 Foundry operations console — `/foundry` · `/foundry/runs/:id`
Connects the FE to the **evidence-driven factory** (the backend now being built). Renders the **funnel** as a narrowing flow — `areas_probed → gaps_confirmed → sources_found → drafts_built → standardized → novel → lift_measured → ` **`promoted`** — with live partition/worker-fleet status. Run detail = the funnel ledger + **reject log by reason** + gate decisions + measured lift deltas + cost/budget burn. The headline metric is **promoted, never generated**. Promoted components link to their detail pages. **Connects to:** `scripts/foundry/*` (the `FunnelLedger`, the gate, the measurement engine).

### 14.14 Gap / capability-valley board — `/foundry/gaps`
The **measured** gaps: each with mechanism, `lift_reason` → durability class (transient/structural/mixed), retrievability tier, model-independent score, **failure samples** (the bare-model evidence), and decay signal. Sort by durability + demand. Links to capability-requests (§8.15) and source surfaces (§14.15). The negative-space map, now backed by measurement instead of hand-typed hints. **Connects to:** `gap_screen`/`research_queue`, `reason_codes`.

### 14.15 Source surfaces — `/foundry/sources`
The **veins** being mined: source kind (regulation/dataset/API/repo) · license status · **yield** (components produced + gate-passed) · freshness · last scan · cost. "Rich source = high yield" made legible; license-filter status visible. Managed-ingestion jobs (§8.26) feed this. **Connects to:** the scout/walkers, license filter, ingestion jobs.

### 14.16 Activity feed & notifications/alerts — `/activity` *(+ alert rules)*
Unified event feed: CDC events, revocations, new promotions in your domain, **decay flips**, capability-request status, pinned-component updates, ingestion completion, dashboard alerts. **Alert rules:** notify on freshness-stale · decay→decaying · error-rate spike · gate-blocked · "a new component matches a saved search" · budget threshold. Channels: in-app · email · webhook. **Connects to:** the event bus, saved searches, alert engine.

### 14.17 Integrations — API keys · webhooks · embeds — `/settings/integrations`
API keys (search/recommend/pricing/pipeline-generation/**foundry** endpoints) · webhook subscriptions (the §14.16 events) · **embeddable widgets** (a component lift badge, a dashboard view, a monitor) via tokened iframe/script. The "API access" monetization line, surfaced. **Connects to:** the API gateway, webhook dispatcher, embed-token service.

### 14.18 New routes — index & attachment

| Route | Page | Attaches as | Connects to (backend) |
|---|---|---|---|
| `/c/:t/:s/history` | History & audit | detail tab | CDC · runs · reviews |
| `/c/:t/:s/versions` | Versions + diff | detail tab | version store · measurement |
| `/pins` | Pinning manager | app page | version store · CDC · flows |
| `/c/:t/:s/customize` | Customize & fork | detail tab | private registry · lineage · measurement |
| `/c/:t/:s/dependencies` | Dependencies & impact | detail tab | edge store · flows · pins |
| `/c/:t/:s/monitor` | Component monitor | detail tab | telemetry · measurement · CDC |
| `/monitor` | Fleet health & decay | app page | measurement · CDC · usage |
| `/c/:t/:s/views/:id` | Component view host | detail tab / standalone | data stores · sandbox |
| `/stores` · `/stores/:id` | Data stores | app page | Postgres/pgvector/object-store |
| `/stores/:id/query` | Query & view builder | app page | store engine · saved views |
| `/dashboards` · `/dashboards/:id` | Dashboard composer | app page | stores · views · telemetry |
| `/foundry` · `/foundry/runs/:id` | Foundry console | app page | `scripts/foundry/*` funnel/gate/measure |
| `/foundry/gaps` | Gap / valley board | app page | gap_screen · reason_codes |
| `/foundry/sources` | Source surfaces | app page | scout · license filter · ingestion |
| `/activity` | Activity & alerts | app page | event bus · alert engine |
| `/settings/integrations` | API keys · webhooks · embeds | settings section | API gateway · webhooks · embeds |

**Generation order:** build these *after* the core ★ set (§13). Within §14, the
highest-leverage first: **component detail tabs** (history · versions · dependencies
· monitor — they make the detail page the control center), then **data stores +
dashboard composer** (the outside-the-box capability), then the **foundry console**
(it visualizes the backend that's actively being built), then pins/customize/activity/
integrations.

---

## 15. Browsing at scale (millions of components — and millions of knowledge entries)

The registry's north star is **millions of rows** (`docs/codex/billion-component-goal.md`),
so discovery must assume millions, not hundreds. And there is a level **below the
component** that this requires: a **Knowledge Corpus is not one page** — it holds
many **knowledge entries** (facts, documents, records). "Millions of knowledge
pages" are these entries, each individually browsable, citable, and provenance-
bearing. §15 covers both levels.

### 15.1 Scale principles (non-negotiable for every list here)
- **Never load all.** Cursor pagination + **list virtualization** (render only the visible window). No "fetch everything then filter."
- **Server-driven faceting with live counts**, computed from the index — and **estimated** when huge (`~2.4M`), exact when small. (Counts are data, never hard-coded — the no-magic-values rule.)
- **Hybrid ranking:** keyword + vector + facet + lift + popularity/recency. A retrieval-mode indicator (semantic vs preview) per §8.9.
- **Deep-linkable state** — every filter/sort/cursor in the URL (shareable, restorable).
- **Every state designed** — skeleton, loading-more, end-of-results, and zero-results (→ a **capability-request**, §8.15).
- **Performance budget** — first results render fast; defer heavy facet counts; debounce; prefetch the next page.

### 15.2 Explore hub — `/explore` (the directory to millions)
The entry point when you don't have a query. Browse **axes** as cards/columns: by **primitive** (the 7), by **type** (14), by **industry** (a drill-down tree, `healthcare.radiology`), by **capability**, by **publisher**, by **source surface**, plus **A–Z**, **trending**, **recently added**, **highest-lift**, **most-used**. Each axis opens a scale-list (§15.3). This is "directory + trending + for-you", the human face of millions.

### 15.3 Browse-at-scale list — powers `/browse` and `/search`
Virtualized infinite list of compact component cards (§7.1) + the facet rail (§7.8) with **server counts**; sort menu (relevance · lift · usage · recency · cost); **density toggle** (comfortable / compact / table); a result-count estimate header; active-facet chips; **save-this-search** (→ alerts, §14.16); a recently-viewed rail. Cursor "load more" / infinite scroll, with jump-to-page only for bounded sets.

### 15.4 Axis browses — `/browse/:primitive` · `/browse/type/:t` · `/browse/industry/:slug` · `/browse/capability/:slug` · `/browse/publisher/:id` · `/browse/source/:id`
Each is the §15.3 list pre-scoped to one axis, with a short axis primer header. Industry is a **tree** (drill into sub-industries). Publisher/source tie to §8.20 / §14.15.

### 15.5 The knowledge-entry level — "millions of knowledge pages"
A Knowledge Corpus holds many entries; this is the level below the component card.
- **Browse a corpus's entries** — `/c/:type/:slug/entries`: a scale-list of the corpus's entries (title · snippet · the retrieval **triggers** that fire it · provenance · freshness), with **search-within-corpus**. Million-entry corpora use the §15.1 mechanics.
- **Knowledge entry page** — `/k/:corpus/:entryId`: the individual "knowledge page". Shows the fact/document **content**; **provenance for THIS entry** (source_url · author · license · last-verified); the **triggers** that surface it (`rag` · `exact-id` · `regex` · `keyword` · `classifier` · `graph`); which pipelines/flows **cite** it; **freshness / CDC / revocation** for this entry; the entry's **version history**; and "used in N answers". Individually addressable + SEO-indexed — these are the millions of browsable knowledge pages. Entries live in the corpus's **data store** (§14.10).

### 15.6 Directory & index pages + SEO — `/index/a-z` · `/index/taxonomy` · sitemaps
Crawlable, query-less index pages so millions are navigable by humans and search engines: A–Z, taxonomy tree (industry / capability / primitive), by-publisher, by-source. Paginated + cached. **Segmented sitemaps** (millions of URLs) for component *and* knowledge-entry pages; canonical URLs; **JSON-LD** structured data (via the existing emitter). This is how the long tail gets discovered.

### 15.7 Collections & spaces — `/collections` · `/collections/:id`
Curated or tenant groupings of components/entries ("ESG starter kit", "my pinned set") so millions are navigable by **curation**, not only filtering. Shareable + embeddable (§14.17).

### 15.8 New reusable components (extend the §7 / §14.1 kit)
Virtualized scale-list (windowed rows + cursor) · facet rail with server counts + estimate · result-count estimator (`~2.4M`, exact when small) · directory/index grid + taxonomy-tree navigator + A–Z bar · **knowledge-entry card** + **knowledge-entry page template** · saved-search chip · recently-viewed rail · breadcrumb (`type ▸ industry ▸ corpus ▸ entry`).

### 15.9 New routes — index

| Route | Page | Level | Connects to (backend) |
|---|---|---|---|
| `/explore` | Discovery hub / directory | components | index facets · trending/usage |
| `/browse/:primitive` · `/browse/type/:t` | Axis browse | components | search index |
| `/browse/industry/:slug` · `/browse/capability/:slug` | Axis browse (tree) | components | facet counts |
| `/browse/publisher/:id` · `/browse/source/:id` | Axis browse | components | publishers · source surfaces |
| `/c/:type/:slug/entries` | Browse a corpus's entries | entries | corpus data store (§14.10) |
| `/k/:corpus/:entryId` | **Knowledge entry page** | entry | store row · provenance · CDC · citations |
| `/index/a-z` · `/index/taxonomy` | Directory / SEO index | both | index · sitemaps |
| `/collections` · `/collections/:id` | Collections / spaces | both | collection store |

### 15.10 Backend it rides on
The **hybrid search index** (keyword + vector + facet) over `index_record` rows; **pgvector** for semantic; the corpus **data stores** (§14.10) for entries; the **Foundry** (§14.13) is what fills these at scale — and the funnel keeps "millions" honest (promoted, governed, deduped — not millions of clones). Every count is computed from the index.

---

## 16. Import & Improve — bring your existing pipeline, get a better one

The **builder in reverse** (§8.2–8.4) and one of the strongest **land** motions:
instead of "describe a task → get a flow," it's *"upload the pipeline you already
run → get it critiqued, optimized, and governed."* It demonstrates the value props
(**lift · cost · governance**) on the user's *own* system, with a **measured**
before/after — proof, not a pitch.

### 16.1 The flow
1. **Import** — upload / paste / connect an existing pipeline. Formats: LangChain/LangGraph & LlamaIndex code, Dify/Flowise/Langflow/n8n exports (JSON), OpenAI Assistants / Bedrock / Vertex configs, a raw prompt-chain, a YAML, or a GitHub repo. A format detector + per-source **import adapter** parses it.
2. **Normalize** — map their steps onto the **seven primitives** and render as the DAG canvas (§7.5): "here's your pipeline in our grammar."
3. **Critique** — run analysis passes (lenses below) → prioritized findings.
4. **Rebuild** — assemble an improved flow: swap hand-rolled steps for governed registry components (with their measured lift + provenance), replace model calls with deterministic checks where possible, route to cheaper/local models, add the missing eval/review/citation gates, dedup, fix wiring.
5. **Prove it** — optionally run the original vs the rebuilt flow on sample inputs → a **measured** cost/quality/coverage delta (the same engine, §14.13 / `scripts/foundry/measure`).

### 16.2 Critique lenses (the findings)
| Lens | Looks for |
|---|---|
| **Capability-lift** | steps a bare model already does (removable) vs steps that truly lift |
| **Cost** | model calls replaceable by a deterministic check (Conditional/processor), cheaper/local routes, prompt-cache & batching, redundant calls |
| **Governance** | missing provenance/citations, no review gate, volatile facts without freshness/CDC, PII handling |
| **Reliability** | no output schema/envelope, no verification/eval, missing guardrails/retries |
| **Structure** | duplicate/mergeable steps, missing dedup, **wiring violations** (a Conditional wired raw to a model without a harness) |
| **Reuse** | hand-rolled steps a governed registry component (matched via hybrid search) could replace |

### 16.3 Pages
- **`/improve`** — Import & Improve entry (upload/paste/connect). Offered as a **second entry point on the landing** beside "Describe a task" (§8.1): *"…or improve a pipeline you already have."*
- **`/improve/:id`** — Analysis: your pipeline as a DAG (left) + a **critique panel** (findings by lens · severity · est. impact), each **accept/reject** like a code review.
- **`/improve/:id/diff`** — **Before/after**: your flow vs the improved flow side-by-side, with **cost delta (est.)**, step-count, a **governance-coverage** meter, and projected **lift/quality** (measured when run).
- **`/improve/:id/report`** — a shareable critique report (the artifact a consultant/buyer forwards internally).
- "Open improved flow" → the builder canvas (`/flow/:id`); deploy/export as usual (§8.7).

### 16.4 New reusable components
Importer (format detector + connectors) · **critique-finding card** (lens · severity · rationale · est. impact · accept/reject) · **before/after diff** (twin DAGs + metric deltas) · savings/coverage meters · "apply selected fixes" action bar.

### 16.5 The engine (mostly reuse)
Reuses the builder (assembly), the registry **hybrid search** (reuse-matching), the **gate** signals (`capability_lift_gate.lift_score` for the lift lens + the hard wiring rules), and the **measurement engine** (`scripts/foundry/measure`) for the before/after proof. New backend: **import adapters** (one per source format → seven-primitive normal form) and the **critique passes** (cost/governance/reliability/structure analyzers over the normalized DAG). **Two-way value:** a user's hand-rolled step that clears the lift gate can be offered back as a **component** (credit/marketplace, §8.18–8.19), and unmet needs become **capability-requests** (§8.15) — so Import & Improve *feeds* the registry and the demand signal.

### 16.6 Why it's a wedge (monetization)
Free **critique** is the funnel (meet users on their own pipeline); the **rebuild + governed components + deploy bundle + measured benchmark** are paid (Pro/Team). It lands in exactly the buyer the brief targets — teams already running LLM workflows under cost/compliance pressure — and proves the moat on their own system. Routes: add `/improve*` to the app shell; tie to `docs/strategy/product-market-monetization-brief.md`.

---

*Sources in-repo: `docs/concepts/component-taxonomy-and-stages.md` (primitives, stages,
execution classes, capability-request), `docs/codex/master-goal.md` (headline interaction,
the lift gate), `docs/codex/billion-component-goal.md` (the millions/scale north star §15
serves), `docs/strategy/product-market-monetization-brief.md` (tiers, wedge, moat,
MVP), `docs/architecture/evidence-driven-component-factory.md` (the foundry funnel + gate that
§14.13–14.15 visualize), `scripts/foundry/*` (the live backend: `contracts.FunnelLedger`,
`novelty`, the gate + measurement engine), `scripts/showcase/pages.py` (baseline color tokens +
primitive legend + DAG node anatomy).*
